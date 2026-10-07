#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""import_r02_01_canonical_v0_1.py —— 将 R02-01 Intake Package 导入 ThreeC Canonical DB。

## 依据

- Intake Package：`research/intake/packages/R02-01/`（validator **PASS**，25 checks / 0 FAIL）
- 审查结论（ThreeC Agent 角色，2026-10-07）：
  · `R02-PHARMA-001` 减重（GLP-1）概念 → **`ACCEPT_WITH_CHANGES`** → 入库
  · `R02-PHARMA-002` 创新药 BD 出海 → **`DEFER`** → **不入库**（留在 intake 层）
- Taxonomy：`apply_taxonomy_t02_v0_1.py`（新增 `TH-PHARMA-GLP1`）
- 模型：Research Model v1.0 · schema：`research/schema/schema.sql`（**未修改**）

## 边界

- 严格遵守 `schema.sql`；**不新增表 / 列**。
- **不修改**既有 52 个 Campaign / 既有 Evidence / 既有 Source / 既有 Theme / 既有 Rule。
- canonical ID 沿用 ThreeC 既有规则：`C-<YYYY>-<SLUG>` / `AR-MED-<YYYY>` /
  `S-MED-NN` / `E-MED-NN` / `EV-MED-NN` / `PH-MED-NN`（接续既有最大编号）。
- **不使用** `R02-PHARMA-*` 作为 canonical ID；通过 `research_notes` 保留 intake provenance。
- 幂等：已存在则跳过；重复运行结果一致。

## 用法

    python research/scripts/import_r02_01_canonical_v0_1.py --dry-run
    python research/scripts/import_r02_01_canonical_v0_1.py
    python research/scripts/import_r02_01_canonical_v0_1.py --verify
"""

from __future__ import annotations

import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(ROOT, "research", "database", "cycle_research.db")

PROV = (
    "R02-01 Intake Package（2026-10-07）｜审查：ThreeC Agent 角色，"
    "R02-PHARMA-001 = ACCEPT_WITH_CHANGES（来源改级 2 条、日期锚点证据基础调整，日期数值未改）"
)

# ★ intake → canonical 映射（供 build_lifecycle_from_intake_v0_2.py 解析；
#   与 R01 importers 的 `intake="R01-XXX-NNN"` 等价，只是用显式表表达）
INTAKE_MAP = [("C-2023-PHARMA-GLP1", "R02-PHARMA-001")]

CAMPAIGN = dict(
    campaign_id="C-2023-PHARMA-GLP1",
    annual_review_id="AR-MED-2023",
    rule_id="rule_pharma_upgrade",
    season_id="pharma_glp1_2023",
    campaign_year=2023,
    start_date="2023-09-08",
    end_date="2023-10-19",
    peak_date="2023-10-16",
    strength="medium",
    result="positive",
    classification="mixed",
    start_date_basis="9/8 A股减肥药概念集体上涨（据 S-MED-07，tier2）；9/19 翰宇药业披露 3000 万美元 GLP-1 多肽原料药海外合同（据 S-MED-08，tier3 转述公司公告）",
    end_date_basis="10/17、10/18 指数分别收跌 1.24%/1.75%，10/18 逾八成成分股下跌；10/16~17 康惠制药、百花医药、博瑞医药董事长先后收警示函或致歉（据 S-MED-07，tier2）",
    date_confidence="medium",
    description=(
        "减重（GLP-1）概念行情：由美股 GLP-1 双寡头（诺和诺德司美格鲁肽、礼来替尔泊肽）"
        "销售与临床数据超预期外溢驱动。上行段内可验证事实含多肽原料药海外订单（翰宇药业 3000 万美元）；"
        "★ 降温由**监管警示函**触发，而非业绩不达预期。"
        "代表标的：常山药业、翰宇药业、博瑞医药（★ 常山药业自身未开展减肥药研发，属叙事驱动标的）。"
    ),
)

THEMES = [("TH-PHARMA", "related"), ("TH-PHARMA-GLP1", "main")]

PHASES = [
    ("main_rise", "2023-09-08", "2023-10-16", "上行段：指数 21 个交易日 +26.43%；相关 27 只股票市值增 1261 亿元。"),
    ("retracement", "2023-10-17", "2023-10-19", "降温：指数连续收跌；监管警示函/致歉为触发事件。★ 本段**不**声称终局。"),
]

SOURCES = [
    ("S-MED-07", "media_tier2", "蹭热点公司被警示成分股逾8成收跌 A股减肥药概念行情显著降温（央广网）",
     None, "https://www.toutiao.com/article/7291488283455062587/", "2023-10-19", "2026-10-07", "央广网（央广资本眼）",
     "记载 2023-09-08 起涨、10-16 顶点、10-17/18 降温；转述 Wind 指数与公司公告。★ 审查改级：Tier 3 → Tier 2（权威媒体）。", 2),
    ("S-MED-08", "media_tier3", "5家药企借减肥药概念跻身百亿市值俱乐部（第一财经）",
     None, "https://www.toutiao.com/article/7289467522674639418/", "2023-10-13", "2026-10-07", "第一财经",
     "记载 9/1-10/13 相关 27 只股票市值增 1261 亿元；翰宇药业 9-19 海外合同；常山药业市值 41.7→155.5 亿元。", 3),
    ("S-MED-09", "media_tier3", "吃药减肥火遍A股 医药基金强势回血（新浪财经）",
     None, "https://finance.sina.cn/tech/2023-10-20/detail-imzrsiza1156885.d.html", "2023-10-20", "2026-10-07", "新浪财经",
     "记载减肥药概念 9 月以来平均涨幅超 30% 及三条催化。★ 本包**未**以本来源单独承担结论（未被任何 evidence 引用）。", 3),
]

# evidence_id, source_id, date, evidence_type, description, role, confidence, independence_group, temporal_relation
EVIDENCES = [
    ("E-MED-06", "S-MED-07", "2023-09-08", "market_data", "A股减肥药概念自 2023-09-08 起集体上涨，至 2023-10-16 达顶点。", "supporting", "medium", "IG-MEDIA-2023GLP1-COOLDOWN", "subsequent"),
    ("E-MED-07", "S-MED-07", "2023-10-16", "market_data", "Wind 减肥药指数 2023-09-08 至 10-16 共 21 个交易日上涨 26.43%，25 只成分股中 23 只上涨。", "supporting", "medium", "IG-MEDIA-2023GLP1-COOLDOWN", "subsequent"),
    ("E-MED-08", "S-MED-07", "2023-10-18", "market_data", "2023-10-17/10-18 指数分别收跌 1.24%/1.75%；10-18 25 家成分股中 21 家收跌。", "supporting", "medium", "IG-MEDIA-2023GLP1-COOLDOWN", "subsequent"),
    ("E-MED-09", "S-MED-07", "2023-10-17", "regulatory", "2023-10-16~17 康惠制药、百花医药、博瑞医药董事长先后收到证监局警示函或致歉，涉『蹭减肥药热点』。", "supporting", "high", "IG-REG-2023GLP1-WARNING", "subsequent"),
    ("E-MED-10", "S-MED-08", "2023-10-13", "market_data", "2023-09-01 至 10-13 与减肥药概念相关的 27 只股票市值合计增加 1261 亿元。", "supporting", "medium", "IG-MEDIA-2023GLP1-MKTCAP", "contemporaneous"),
    ("E-MED-11", "S-MED-08", "2023-09-19", "company_announcement", "2023-09-19 翰宇药业披露与海外客户签订 3000 万美元 GLP-1 多肽原料药合同；9-20 收获 20cm 涨停。", "supporting", "medium", "IG-CO-2023GLP1-HANYU", "contemporaneous"),
    ("E-MED-12", "S-MED-08", "2023-10-13", "market_data", "2023-09-01 以来常山药业总市值由 41.7 亿元升至 155.5 亿元，涨幅 272.87%（★ 该公司自身未开展减肥药研发）。", "context", "medium", "IG-MEDIA-2023GLP1-MKTCAP", "contemporaneous"),
]

SECURITIES = [
    ("CHANGSHAN", "300255", "常山药业", "SZ"),
    ("HANYU", "300199", "翰宇药业", "SZ"),
    ("BORUI", "688166", "博瑞医药", "SH"),
]

# security_id, role
CAMPAIGN_SECURITIES = [("CHANGSHAN", "leader"), ("HANYU", "representative"), ("BORUI", "representative")]

# evidence_id → role（★ 从 evidence_role 派生，不硬编码 —— 否则桥表与 evidences 表会不一致）
CAMPAIGN_EVIDENCES = [(e[0], e[5]) for e in EVIDENCES]

# event_id, date, name, event_type, description, source_id
EVENTS = [
    ("EV-MED-06", "2023-09-08", "A股减肥药概念集体上涨（上行段起点）", "market", "由美股 GLP-1 双寡头市值创新高外溢触发。", "S-MED-07"),
    ("EV-MED-07", "2023-09-19", "翰宇药业披露 3000 万美元 GLP-1 多肽原料药海外合同", "company", "产业侧可验证订单。", "S-MED-08"),
    ("EV-MED-08", "2023-10-10", "司美格鲁肽三期临床提前终止（疗效达标）", "company", "二次催化。", "S-MED-09"),
    ("EV-MED-09", "2023-10-16", "减肥药概念达顶点（Wind 指数 21 个交易日 +26.43%）", "market", "上行段顶点。", "S-MED-07"),
    ("EV-MED-10", "2023-10-17", "康惠制药、百花医药、博瑞医药董事长收警示函或致歉", "policy", "降温的直接触发事件。", "S-MED-07"),
]

OBSERVATIONS = [
    ("start", "2023-09-08", "2023-09-08", "manual", "medium", "E-MED-06", "起点锚。指数口径非一手，见 E-MED-06 说明。"),
    ("peak", "2023-10-16", "2023-10-16", "manual", "medium", "E-MED-07", "顶点锚（单日）。未取得指数逐日收盘序列以进一步收敛。"),
    ("end", "2023-10-19", "2023-10-19", "manual", "medium", "E-MED-08", "★ 仅界定**降温起点窗口**（10-17~19），不声称终局日期。"),
]


def _next_num(cur, col, tbl, pat):
    import re
    rows = [r[0] for r in cur.execute("SELECT %s FROM %s WHERE %s LIKE ?" % (col, tbl, col), (pat,))]
    nums = sorted(int(re.sub(r"\D", "", x.split("-")[-1])) for x in rows if x.split("-")[-1].isdigit())
    return (nums[-1] + 1) if nums else 1


def main(argv):
    dry = "--dry-run" in argv
    verify = "--verify" in argv
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    print("ThreeC · R02-01 Canonical Import —— 医药健康（减重 / GLP-1）")
    print("-" * 62)

    if verify:
        cid = CAMPAIGN["campaign_id"]
        row = cur.execute("SELECT campaign_id,campaign_year,start_date,peak_date,end_date,classification FROM campaigns WHERE campaign_id=?", (cid,)).fetchone()
        print("campaign      :", row if row else "✗ 缺失")
        for t in ("campaign_themes", "campaign_phases", "campaign_evidences", "campaign_securities", "campaign_events", "campaign_date_observations"):
            n = cur.execute("SELECT COUNT(*) FROM %s WHERE campaign_id=?" % t, (cid,)).fetchone()[0]
            print("%-14s: %d 行" % (t, n))
        print("themes 表 TH-PHARMA-GLP1:", cur.execute("SELECT 1 FROM themes WHERE theme_id='TH-PHARMA-GLP1'").fetchone() and "存在" or "✗ 缺失")
        print("campaigns 总数:", cur.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0])
        conn.close()
        return 0

    cid = CAMPAIGN["campaign_id"]
    if cur.execute("SELECT 1 FROM campaigns WHERE campaign_id=?", (cid,)).fetchone():
        print("SKIP  %s 已存在（幂等）" % cid)
        conn.close()
        return 0

    # 前置检查：taxonomy 必须先建
    if not cur.execute("SELECT 1 FROM themes WHERE theme_id='TH-PHARMA-GLP1'").fetchone():
        print("FAIL  taxonomy 未就绪：TH-PHARMA-GLP1 不存在 → 先运行 apply_taxonomy_t02_v0_1.py")
        conn.close()
        return 1
    for tid, _r in THEMES:
        if not cur.execute("SELECT 1 FROM themes WHERE theme_id=?", (tid,)).fetchone():
            print("FAIL  theme %s 不存在" % tid)
            conn.close()
            return 1
    if not cur.execute("SELECT 1 FROM research_rules WHERE rule_id=?", (CAMPAIGN["rule_id"],)).fetchone():
        print("FAIL  rule %s 不存在" % CAMPAIGN["rule_id"])
        conn.close()
        return 1

    if dry:
        print("DRY   annual_reviews  +1  %s" % CAMPAIGN["annual_review_id"])
        print("DRY   campaigns       +1  %s (%s ~ %s, peak %s)" % (cid, CAMPAIGN["start_date"], CAMPAIGN["end_date"], CAMPAIGN["peak_date"]))
        print("DRY   campaign_themes +%d  %s" % (len(THEMES), ", ".join("%s=%s" % t for t in THEMES)))
        print("DRY   campaign_phases +%d  %s" % (len(PHASES), ", ".join(p[0] for p in PHASES)))
        print("DRY   sources         +%d  %s" % (len(SOURCES), ", ".join(s[0] for s in SOURCES)))
        print("DRY   evidences       +%d  %s" % (len(EVIDENCES), ", ".join(e[0] for e in EVIDENCES)))
        print("DRY   events          +%d  %s" % (len(EVENTS), ", ".join(e[0] for e in EVENTS)))
        print("DRY   securities      +%d  %s" % (len(SECURITIES), ", ".join(s[0] for s in SECURITIES)))
        print("DRY   campaign_evidences +%d / campaign_securities +%d / campaign_events +%d / campaign_date_observations +%d"
              % (len(CAMPAIGN_EVIDENCES), len(CAMPAIGN_SECURITIES), len(EVENTS), len(OBSERVATIONS)))
        print("-" * 62)
        print("[dry-run] 未写入任何行")
        conn.close()
        return 0

    cur.execute("INSERT INTO annual_reviews (annual_review_id,rule_id,year,status,summary,review_notes) VALUES (?,?,?,?,?,?)",
                (CAMPAIGN["annual_review_id"], CAMPAIGN["rule_id"], CAMPAIGN["campaign_year"], "medium",
                 "医药健康 %d：减重（GLP-1）概念行情。" % CAMPAIGN["campaign_year"], PROV))
    cur.execute(
        "INSERT INTO campaigns (campaign_id,annual_review_id,rule_id,season_id,campaign_year,start_date,end_date,peak_date,"
        "strength,result,classification,start_date_basis,end_date_basis,date_confidence,description,research_notes) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (cid, CAMPAIGN["annual_review_id"], CAMPAIGN["rule_id"], CAMPAIGN["season_id"], CAMPAIGN["campaign_year"],
         CAMPAIGN["start_date"], CAMPAIGN["end_date"], CAMPAIGN["peak_date"], CAMPAIGN["strength"], CAMPAIGN["result"],
         CAMPAIGN["classification"], CAMPAIGN["start_date_basis"], CAMPAIGN["end_date_basis"],
         CAMPAIGN["date_confidence"], CAMPAIGN["description"], PROV))
    print("ADD   campaigns       %s" % cid)

    for tid, role in THEMES:
        cur.execute("INSERT INTO campaign_themes (campaign_id,theme_id,role) VALUES (?,?,?)", (cid, tid, role))
    print("ADD   campaign_themes %d" % len(THEMES))

    ph = _next_num(cur, "phase_id", "campaign_phases", "PH-MED-%")
    for i, (ptype, s, e, desc) in enumerate(PHASES):
        cur.execute("INSERT INTO campaign_phases (phase_id,campaign_id,phase_type,start_date,end_date,description) VALUES (?,?,?,?,?,?)",
                    ("PH-MED-%02d" % (ph + i), cid, ptype, s, e, desc))
    print("ADD   campaign_phases %d（PH-MED-%02d..%02d）" % (len(PHASES), ph, ph + len(PHASES) - 1))

    for s in SOURCES:
        cur.execute("INSERT INTO sources (source_id,source_type,title,author,url,published_at,captured_at,publisher,description,tier) VALUES (?,?,?,?,?,?,?,?,?,?)", s)
    print("ADD   sources         %d" % len(SOURCES))

    for e in EVIDENCES:
        cur.execute("INSERT INTO evidences (evidence_id,source_id,date,evidence_type,description,evidence_role,confidence,independence_group,temporal_relation) VALUES (?,?,?,?,?,?,?,?,?)", e)
    print("ADD   evidences       %d" % len(EVIDENCES))

    for ev in EVENTS:
        cur.execute("INSERT INTO events (event_id,date,name,event_type,description,source_id) VALUES (?,?,?,?,?,?)", ev)
    print("ADD   events          %d" % len(EVENTS))

    for s in SECURITIES:
        if cur.execute("SELECT 1 FROM securities WHERE security_id=?", (s[0],)).fetchone():
            print("SKIP  securities %s 已存在" % s[0]); continue
        cur.execute("INSERT INTO securities (security_id,ticker,name,exchange) VALUES (?,?,?,?)", s)
    print("ADD   securities      ≤%d" % len(SECURITIES))

    for eid, role in CAMPAIGN_EVIDENCES:
        cur.execute("INSERT INTO campaign_evidences (campaign_id,evidence_id,role) VALUES (?,?,?)", (cid, eid, role))
    for sid, role in CAMPAIGN_SECURITIES:
        cur.execute("INSERT INTO campaign_securities (campaign_id,security_id,role) VALUES (?,?,?)", (cid, sid, role))
    for ev in EVENTS:
        cur.execute("INSERT INTO campaign_events (campaign_id,event_id,role) VALUES (?,?,?)", (cid, ev[0], "catalyst"))
    print("ADD   campaign_evidences %d / campaign_securities %d / campaign_events %d" % (len(CAMPAIGN_EVIDENCES), len(CAMPAIGN_SECURITIES), len(EVENTS)))

    ob = _next_num(cur, "observation_id", "campaign_date_observations", "CDO-MED-%")
    for i, (role, cand, ver, method, conf, eid, notes) in enumerate(OBSERVATIONS):
        cur.execute("INSERT INTO campaign_date_observations (observation_id,campaign_id,date_role,candidate_date,verified_date,verification_method,confidence,evidence_id,notes) VALUES (?,?,?,?,?,?,?,?,?)",
                    ("CDO-MED-%02d" % (ob + i), cid, role, cand, ver, method, conf, eid, notes))
    print("ADD   campaign_date_observations %d" % len(OBSERVATIONS))

    conn.commit()
    print("-" * 62)
    print("campaigns 总数：%d" % cur.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0])
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
