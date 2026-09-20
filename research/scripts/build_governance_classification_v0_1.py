#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_governance_classification_v0_1.py —— 生成 R01 治理分类清单（**只读 DB + intake，不改 canonical 数据**）。

对应治理规则集：`governance-gates-v0.1`（`docs/R01_GOVERNANCE_GATES_v0_1.md`）。

产出：`research/research/reports/governance_classification_v0_1.json`

分类内容（每个 canonical Campaign）：
  1. `market_evidence_state`  —— G1-1：A_SHARE_MARKET / INDUSTRY_COMPANY_ONLY / NONE
  2. `beta_level`             —— G1-3：0 / 1 / 2 / 3（**不虚构 L2/L3**）
  3. `peak` / `end`           —— G2-1：EXACT / WINDOW / NULL（+ `alternative` 保留另一口径）
  4. `result_semantics_ok`    —— G1-5：`result=weak` 语义 + `strength` 不得为 weak
  5. `needs_historical_fix`   —— 是否产生历史数据修复需求（本轮**只标注、不修复**）

**边界**：
  - 不写 canonical DB 的 campaigns / evidences / sources / themes 任何一行；
  - 不修改任何 Intake Package；
  - 不修改 Schema / Protocol / Research Model v1.0 / Export Contract v1.0 / CMTR v1；
  - 不因本规则上线而回填新的 peak / end。

用法：python research/scripts/build_governance_classification_v0_1.py [--check]
"""

from __future__ import annotations

import io
import json
import os
import re
import sqlite3
import sys
import glob
from collections import Counter, OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(ROOT, "research", "database", "cycle_research.db")
PKG_DIR = os.path.join(ROOT, "research", "intake", "packages")
OUT_PATH = os.path.join(ROOT, "research", "research", "reports", "governance_classification_v0_1.json")

RULESET = "governance-gates-v0.1"

# ---------------------------------------------------------------- G1-1 人工复核结论
# 判定依据：逐条阅读 campaign_evidences 的 description，区分
#   (a) A 股市场侧证据：个股行情（涨停/收于/盘中最高 X 元）、A 股板块/行业指数涨跌、持仓、成交额、市值、跑赢/跑输宽基
#   (b) 行业 / 公司证据：产量、销量、订单、商品价格（元/吨、美元/吨、元/公斤）、营收、政策文件
#   (c) 无市场侧证据
# 以下 4 个 Campaign 的**全部** evidence 均为 (b)，无一条 A 股市场侧证据 → INDUSTRY_COMPANY_ONLY
INDUSTRY_COMPANY_ONLY = {
    "C-2019-MIL-GROUP-RESTRUCTURE":
        "3/3 evidence 均为集团重组事件（筹划公告 / 国务院批准 / 集团揭牌），"
        "无 A 股行情证据（`R01-06 Intake` 已记录「市场反应侧行情数据缺失」）",
    "C-2018-HIEQ-ROBOT-DOWN":
        "5/5 evidence 均为行业产量 / 销量 / 上市公司业绩，无 A 股行情证据"
        "（`R01-03 Intake Review` 已记录该先例：无 A 股行情证据下被 PROMOTE）",
    "C-2016-PANEL-CYCLE":
        "3/3 evidence 均为面板价格与供给（40 英寸面板涨幅、三星转产、大陆新增产能），"
        "属**商品价格**，非 A 股市场侧证据",
    "C-2020-RES-RAREEARTH":
        "7/7 evidence 均为稀土价格 / 开采配额 / 公司营收，无 A 股行情证据",
}

# ---------------------------------------------------------------- G1-3 Beta Level 1
# 判定依据：evidence description 中存在**相对宽基基准**（沪深300 / 上证指数）的超额收益表述。
# 仅「跑赢/跑输 + 宽基」或「相对 ±Xpct（对比宽基）」计入 L1；
# 商品价格的「同期」、行业间排名、「超额配售」（证券发行术语）**均不计入**。
BENCH_RE = re.compile(
    r"沪深\s?300|上证指数|上证综指|中证全指|万得全A|跑赢沪深|跑输沪深|跑赢\s?沪深300|跑输\s?沪深300"
)
# 「相对 / 跑赢 / 跑输 / 超额」任一出现，且与宽基基准同句 → 判为相对基准超额
EXCESS_RE = re.compile(r"相对|跑赢|跑输|超额")


def canonical_intake_map():
    """从 6 个 canonical importer 脚本中提取 canonical_id -> (package, candidate_no)。"""
    m = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "research", "scripts", "import_r01_0*_canonical_v0_1.py"))):
        txt = io.open(f, encoding="utf-8").read()
        mm = re.search(r"import_r01_(\d{2})_canonical", f)
        if not mm:
            continue
        pkg = "R01-" + mm.group(1)
        for k, cid in re.findall(r'k="(\d{3})",\s*cid="(C-[A-Z0-9\-]+)"', txt):
            m[cid] = (pkg, k)
        for cid, intk in re.findall(r'cid="(C-[A-Z0-9\-]+)",\s*intake="R01-[A-Z]+-(\d{3})"', txt):
            m[cid] = (pkg, intk)
    return m


PREFIX = {
    "R01-01": "R01-HIEQ-",
    "R01-02": "R01-SEMICONDUCTOR-",
    "R01-03": "R01-RESOURCES-",
    "R01-04": "R01-CONSUMER-",
    "R01-05": "R01-FINRE-",
    "R01-06": "R01-MIL-",
}


def precision_state(prec, date_value):
    if date_value is None:
        return "NULL"
    prec = (prec or "").upper()
    if prec in ("DATE_WINDOW", "PHASE_WINDOW", "UNKNOWN"):
        return "WINDOW"
    if prec == "EXACT_DATE":
        return "EXACT"
    return "WINDOW"


def main(argv):
    check_only = "--check" in argv
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cmap = canonical_intake_map()

    # 预载 intake candidates
    pkg_cand = {}
    for pkg, pre in PREFIX.items():
        try:
            arr = json.load(io.open(os.path.join(PKG_DIR, pkg, "candidates.json"), encoding="utf-8"))
        except Exception:
            arr = []
        pkg_cand[pkg] = {c["candidate_id"]: c for c in arr}

    rows = cur.execute(
        "SELECT campaign_id, rule_id, campaign_year, start_date, peak_date, end_date, strength, result, "
        "classification, date_confidence, season_id, research_notes FROM campaigns ORDER BY rule_id, campaign_year"
    ).fetchall()

    items = []
    for r in rows:
        cid = r["campaign_id"]
        ev = [x[0] or "" for x in cur.execute(
            """SELECT e.description FROM campaign_evidences ce JOIN evidences e ON e.evidence_id=ce.evidence_id
               WHERE ce.campaign_id=?""", (cid,))]

        # ---- G1-1 ----
        if cid in INDUSTRY_COMPANY_ONLY:
            mes, mes_basis = "INDUSTRY_COMPANY_ONLY", INDUSTRY_COMPANY_ONLY[cid]
        elif not ev:
            mes, mes_basis = "NONE", "无绑定 evidence"
        else:
            mes, mes_basis = "A_SHARE_MARKET", (
                "存在 A 股市场侧证据（个股行情 / A 股板块或行业指数涨跌 / 持仓 / 成交额 / 市值 / 宽基对比）")

        # ---- G1-3 ----
        bench_hits = [s for s in ev if BENCH_RE.search(s)]
        has_excess = any(EXCESS_RE.search(s) for s in bench_hits)
        if bench_hits and has_excess:
            bl, bl_basis = 1, "存在相对宽基基准（沪深300 / 上证）的超额收益，但**未做 Beta 调整、未剥离风格因子**"
        else:
            bl, bl_basis = 0, "仅有绝对涨跌 / 价格或产业侧证据，无相对宽基基准超额收益"

        # ---- G2-1 ----
        peak_alt = end_alt = None
        peak_state = end_state = None
        if cid in cmap:
            pkg, k = cmap[cid]
            cand = pkg_cand.get(pkg, {}).get(PREFIX[pkg] + k)
            if cand:
                dc = cand.get("date_candidates") or {}

                def one(role):
                    d0 = (dc.get(role) or [{}])[0]
                    return d0.get("date_precision"), d0.get("date")
                pp, _pd = one("peak")
                ep, _ed = one("end")
                peak_state = precision_state(pp, r["peak_date"])
                end_state = precision_state(ep, r["end_date"])
                alts_p = [a for d in (dc.get("peak") or []) for a in (d.get("alternative_dates") or [])]
                alts_e = [a for d in (dc.get("end") or []) for a in (d.get("alternative_dates") or [])]
                if alts_p:
                    peak_alt = {"date": alts_p[0].get("date"), "basis": (alts_p[0].get("basis") or "")[:200]}
                if alts_e:
                    end_alt = {"date": alts_e[0].get("date"), "basis": (alts_e[0].get("basis") or "")[:200]}
        if peak_state is None:  # pre-R01（无 canonical importer 映射）
            txt = " ".join(ev) + " " + (r["research_notes"] or "")
            windowish = bool(re.search(r"Peak Window|区间高点|最高点", txt))
            peak_state = "NULL" if r["peak_date"] is None else ("WINDOW" if windowish else "EXACT")
            end_state = "NULL" if r["end_date"] is None else "EXACT"

        # ---- G1-5 ----
        result_ok = r["result"] == "weak"
        strength_weak = (r["strength"] == "weak")
        needs_fix = strength_weak
        fix_note = None
        if strength_weak:
            fix_note = ("legacy 残留：`strength='weak'`。按 governance-gates-v0.1，`weak` 只能出现在 `result`；"
                        "建议后续独立修复为 `strength='medium'`（保留 `result='weak'`）。**本轮不修改。**")

        items.append(OrderedDict([
            ("campaign_id", cid),
            ("rule_id", r["rule_id"]),
            ("campaign_year", r["campaign_year"]),
            ("theme_cycle_id", r["season_id"]),
            ("classification", r["classification"]),
            ("strength", r["strength"]),
            ("result", r["result"]),
            ("date_confidence", r["date_confidence"]),
            ("market_evidence_state", mes),
            ("market_evidence_basis", mes_basis),
            ("beta_level", bl),
            ("beta_level_basis", bl_basis),
            ("peak", OrderedDict([("state", peak_state), ("date", r["peak_date"]), ("alternative", peak_alt)])),
            ("end", OrderedDict([("state", end_state), ("date", r["end_date"]), ("alternative", end_alt)])),
            ("result_weak_semantics", OrderedDict([
                ("result_is_weak", result_ok),
                ("strength_is_weak", strength_weak),
                ("conforms_to_gate", not strength_weak),
                ("note", fix_note),
            ])),
            ("needs_historical_fix", needs_fix),
        ]))

    doc = OrderedDict([
        ("ruleset", RULESET),
        ("rule_doc", "docs/R01_GOVERNANCE_GATES_v0_1.md"),
        ("generated_from", OrderedDict([
            ("db", "research/database/cycle_research.db（只读）"),
            ("intake_packages", "research/intake/packages/R01-01..R01-06（只读）"),
        ])),
        ("scope_note", [
            "本清单为**治理 / 审计层**产物，不是 canonical Campaign 数据",
            "未修改 campaigns / evidences / sources / themes 的任何一行",
            "未因本规则上线而回填新的 peak / end；ALTERNATIVE 仅记录，不改变 canonical 取值",
            "Beta Level 2 / 3 在 R01-01~06 中**实测为 0**，未虚构",
        ]),
        ("counts", OrderedDict([
            ("campaigns", len(items)),
            ("market_evidence_state", dict(Counter(i["market_evidence_state"] for i in items))),
            ("beta_level", dict(Counter(str(i["beta_level"]) for i in items))),
            ("peak_state", dict(Counter(i["peak"]["state"] for i in items))),
            ("end_state", dict(Counter(i["end"]["state"] for i in items))),
            ("with_peak_alternative", sum(1 for i in items if i["peak"]["alternative"])),
            ("with_end_alternative", sum(1 for i in items if i["end"]["alternative"])),
            ("result_weak", sum(1 for i in items if i["result_weak_semantics"]["result_is_weak"])),
            ("strength_weak_violations", sum(1 for i in items if i["result_weak_semantics"]["strength_is_weak"])),
            ("needs_historical_fix", sum(1 for i in items if i["needs_historical_fix"])),
        ])),
        ("campaigns", items),
    ])

    if check_only:
        print("check-only：已构建 %d 条，未写盘" % len(items))
        print(json.dumps(doc["counts"], ensure_ascii=False, indent=2))
        conn.close()
        return 0

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print("written: %s" % OUT_PATH)
    print(json.dumps(doc["counts"], ensure_ascii=False, indent=2))
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
