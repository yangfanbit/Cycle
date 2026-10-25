#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""audit_market_limit_up_v0_1.py —— 盘面涨停识别方法的**可验证性审计**（v0.31）。

## 审计什么

`PIT_MARKET_OBSERVED` 角色由「单日涨跌幅落在板块涨跌停带内 + 连板」推导。
本脚本用**同一批真实样本**独立回答五个问题：

1. `market_daily` 到底有什么字段？日涨幅只能怎么算？
   - `open/high/low/close`（原始价）+ `adj_close`（前复权）+ `price_type`；
     **没有** `pre_close`（交易所参考前收）→ 官方「当日涨跌幅」无法直接取到。
2. 前复权序列与原始价是什么关系？
   - **实测发现是仿射变换**：`adj_close ≈ k·raw_close − c`（k/c 只在公司行为日变化）。
     茅台 2016 段 k=1、c=−297.755（纯加法，故出现负价）；兆易创新 k≈0.51、c≈3.36。
   - 推论：直接用 `adj_close` 比值算涨跌幅会**系统性偏离**原始价环比，偏移越大越明显。
3. 识别出的每个「信号日」能否被**原始价**独立佐证？
   - 逐日独立计算 `raw_pct` 与 `adj_pct`，按最终采用的双口径规则分类：
     `both_series_agree` / `adjusted_ratio_ex_dividend` / `adjusted_ratio_action_day`。
4. ST 等特殊状态怎么处理？
   - `securities` 表**只有** security_id/ticker/name/exchange，**没有 ST 标记**
     → ST 状态无法从库内判定；ST 涨跌停 5% 落在 10%/20% 带外 ⇒ 天然不被识别
     （漏报方向）；反向的误报由双口径核验兜底。
5. 曾被考虑但**已否决**的口径（留证，避免后来者重复踩）：
   - 「offset 跳变量 = 当日派息 → pre_close = raw_{t-1} − Δoffset」：
     只在**纯加法**复权（k=1）时成立；k≠1 时会算错（实测兆易创新 2020-05-06
     被算成 +4.86%，真实是 +10.0%）。

产物：`research/research/reports/limit_up_audit_v0_1.json`（`--write`，拒绝覆盖）。
门禁：`--check` 与已发布产物逐字段比对。

用法：
    python research/scripts/audit_market_limit_up_v0_1.py            # 打印摘要
    python research/scripts/audit_market_limit_up_v0_1.py --check    # CI 门禁
    python research/scripts/audit_market_limit_up_v0_1.py --write    # 写产物
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

REPO = db.REPO_ROOT
CURRENT = os.path.join(REPO, "research", "current")
MARKET_DB = os.path.join(REPO, "research", "database", "market_data.db")
OUT_DIR = os.path.join(REPO, "research", "research", "reports")
GENERATED_AT = "2026-10-23"
AUDIT_RE = re.compile(r"limit_up_audit_v0_(\d+)\.json$")


def latest_roles_path():
    """★ v0.32：角色产物按版本号取**最新**，不再硬编码 v0_3。"""
    files = [f for f in os.listdir(CURRENT)
             if re.match(r"historical_market_roles_v0_(\d+)\.json$", f)]
    if not files:
        raise SystemExit("FAIL: 找不到历史市场角色产物")
    files.sort(key=lambda f: int(re.search(r"v0_(\d+)", f).group(1)))
    return os.path.join(CURRENT, files[-1])


def audit_out_path(version=None):
    if version is None:
        files = [f for f in os.listdir(OUT_DIR) if AUDIT_RE.match(f)]
        if not files:
            return os.path.join(OUT_DIR, "limit_up_audit_v0_1.json")
        files.sort(key=lambda f: int(AUDIT_RE.match(f).group(1)))
        return os.path.join(OUT_DIR, files[-1])
    return os.path.join(OUT_DIR, "limit_up_audit_v0_%d.json" % version)

# 与角色层同一规则（公司行为日阈值 / 板块带）
ACTION_DAY_PCT = 21.6


def limit_band(ticker, date):
    t = ticker or ""
    if t.startswith("688"):
        return (19.5, 21.2)
    if t.startswith("300"):
        return (19.5, 21.2) if date >= "2020-08-24" else (9.8, 10.6)
    return (9.8, 10.6)


def board_of(ticker):
    t = ticker or ""
    if t.startswith("688"):
        return "STAR"
    if t.startswith("300"):
        return "GEM"
    return "MAIN"


def load_tickers(index):
    out = {}
    for entry in index.get("maps") or []:
        path = os.path.join(CURRENT, entry["file"])
        if not os.path.exists(path):
            continue
        doc = json.load(open(path, encoding="utf-8"))
        for e in doc.get("events") or []:
            for p in e.get("participants") or []:
                if p.get("ticker"):
                    out[p["security_id"]] = p["ticker"]
    return out


def both_pcts(con, sid, dt):
    """独立计算 `raw_pct` 与 `adj_pct`（不复用生成器代码，保证审计独立性）。"""
    cur = con.execute(
        "SELECT a.trade_date td, r.close raw_close, a.adj_close adj_close "
        "FROM market_daily a JOIN market_daily r "
        "  ON r.series_id=a.series_id AND r.trade_date=a.trade_date AND r.price_type='raw' "
        "WHERE a.series_id=? AND a.price_type='adjusted' AND a.trade_date=?",
        (sid, dt)).fetchone()
    prv = con.execute(
        "SELECT a.trade_date td, r.close raw_close, a.adj_close adj_close "
        "FROM market_daily a JOIN market_daily r "
        "  ON r.series_id=a.series_id AND r.trade_date=a.trade_date AND r.price_type='raw' "
        "WHERE a.series_id=? AND a.price_type='adjusted' AND a.trade_date<? "
        "ORDER BY a.trade_date DESC LIMIT 1", (sid, dt)).fetchone()
    if not (cur and prv):
        return None
    raw_pct = adj_pct = None
    if cur["raw_close"] and prv["raw_close"]:
        raw_pct = (cur["raw_close"] / prv["raw_close"] - 1.0) * 100.0
    if cur["adj_close"] and prv["adj_close"]:
        adj_pct = (cur["adj_close"] / prv["adj_close"] - 1.0) * 100.0
    if raw_pct is None and adj_pct is None:
        return None
    return {"raw_pct": raw_pct, "adj_pct": adj_pct, "prev_date": prv["td"],
            "raw_close": cur["raw_close"], "adj_close": cur["adj_close"]}


def classify(raw_pct, adj_pct, lo, hi):
    """与角色层一致的双口径分类。"""
    if raw_pct is not None and abs(raw_pct) > ACTION_DAY_PCT:
        if adj_pct is None:
            return None, None
        return "adjusted_ratio_action_day", adj_pct
    in_raw = raw_pct is not None and lo <= raw_pct <= hi
    in_adj = adj_pct is not None and lo <= adj_pct <= hi
    if in_raw and in_adj:
        return "both_series_agree", raw_pct
    if in_adj and not in_raw:
        return "adjusted_ratio_ex_dividend", adj_pct
    return None, None


# ---------------------------------------------------------------- ST 规则（按板块 × 时期）
# ★★ v0.32：原文「ST 一律 5% → 天然不被识别」是**错的**，按板块与时期拆开：
#   · 主板风险警示股票：5%（≤ 2026-07-05）→ 2026-07-06 起放宽至 **10%**；
#   · 创业板风险警示股票：5%（改革前）→ 2020-08-24 起 **20%**；
#   · 科创板风险警示股票：**20%**（与普通股一致，无 5% 档）。
#   ⇒ 只有「主板 2026-07-06 之前」与「创业板 2020-08-24 之前」的 ST 才落在带外（漏报）；
#     创业板/科创板 ST 与主板新规后的 ST 都**落在现有带内**，不会被漏掉。
ST_RULES = {
    "detectable_from_db": False,
    "why": ("`securities` 只有 security_id / ticker / name / exchange，**没有** ST/*ST 标记 → "
            "无法逐日判定某只股票在某个交易日是否处于风险警示状态。"),
    "bands_by_board_and_period": {
        "MAIN": [
            {"period": "<= 2026-07-05", "limit_pct": 5,
             "consequence": "落在 9.8–10.6% 带**之外** → 不被识别（**漏报方向**）"},
            {"period": ">= 2026-07-06", "limit_pct": 10,
             "consequence": "与主板普通股同带（9.8–10.6%）→ **不漏报**（规则已放宽）"},
        ],
        "GEM": [
            {"period": "<= 2020-08-23", "limit_pct": 5,
             "consequence": "落在 9.8–10.6% 带外 → 漏报"},
            {"period": ">= 2020-08-24", "limit_pct": 20,
             "consequence": "与创业板普通股同带（19.5–21.2%）→ 不漏报"},
        ],
        "STAR": [
            {"period": "全部", "limit_pct": 20,
             "consequence": "与科创板普通股同带（19.5–21.2%）→ 不漏报"},
        ],
    },
    "sources": [
        {"title": "关于创业板风险警示股票和退市整理期股票交易制度安排的通知（深证上〔2020〕620 号）",
         "url": "https://www.szse.cn/disclosure/notice/general/t20200710_579459.html",
         "date": "2020-07-10",
         "quote": ("《特别规定》实施前，创业板风险警示股票 …… 价格涨跌幅限制比例为 5%；"
                   "《特别规定》正式实施后，创业板风险警示股票涨跌幅限制比例为 20%。")},
        {"title": "深交所投教：风险警示股票价格涨跌幅限制比例是多少？",
         "url": "https://www.szse.cn/www/investor/knowledge/stock/deal/t20210127_584469.html",
         "date": "2021-01-27",
         "quote": ("深交所对风险警示股票实行价格涨跌幅限制，主板、中小企业板风险警示股票"
                   "价格涨跌幅限制比例为 5%，创业板风险警示股票价格涨跌幅限制比例为 20%。")},
        {"title": "A股交易新规 7 月 6 日起施行（证监会上海监管局转载证券日报）",
         "url": "https://www.csrc.gov.cn/shanghai/c105566/c7643909/content.shtml",
         "date": "2026-07-06",
         "quote": ("沪深交易所将主板风险警示股票的涨跌幅限制由 5% 放宽至 10%，"
                   "创业板和科创板的风险警示股票涨跌幅限制此前已统一为 20%，"
                   "北交所风险警示股票为 30%，均维持不变。")},
    ],
    "impact_on_current_universe": (
        "本产物涉及的事件行情窗口最晚到 **2025-12-26**（< 2026-07-06）→ "
        "主板 ST 的 5% 档在本库历史窗口内仍然适用；创业板 2020-08-24 前后已按日期分带处理。"),
    "not_verified": [
        "《特别规定》的正式实施日未在该通知原文中给出；本库按首批注册制股票上市日 "
        "2020-08-24 近似，未逐日核对交易所公告。",
        "科创板风险警示股票的 20% 未取得交易所原文（本轮只核到证监会转载与投教材料），"
        "按「与科创板普通股同带」处理。",
        "退市整理期股票（主板 / 创业板 / 科创板）的涨跌幅与风险警示股票不同，"
        "本轮未独立核实，且库内无退市整理期标记 → 未纳入检测。",
        "北交所（8/4 开头）风险警示股票为 30%，本库 `board_of()` 会误判为主板；"
        "当前事件参与者里**没有**北交所代码（实测前缀仅 600/601/603/000/001/002/003/300/301/688），"
        "故不影响既有结论，但属已知限制。",
    ],
}


def audit(version=2):
    index = json.load(open(os.path.join(CURRENT, "historical_event_maps_index.json"),
                           encoding="utf-8"))
    tickers = load_tickers(index)
    roles_path = latest_roles_path()
    roles = json.load(open(roles_path, encoding="utf-8"))
    con = sqlite3.connect("file:%s?mode=ro" % MARKET_DB, uri=True)
    con.row_factory = sqlite3.Row
    stats = collections.Counter()
    by_board = collections.Counter()
    mismatches = []
    affine_samples = []
    for eid, ev in roles["events"].items():
        for r in ev.get("roles") or []:
            if r.get("role") != "PIT_MARKET_OBSERVED":
                continue
            sid = r.get("security_id")
            if not sid:
                continue
            tk = tickers.get(sid)
            board = board_of(tk)
            # ★ 同时审计**支持性证据**与**事后观察**两个集合（方法对两者都适用）
            evd = r.get("evidence") or {}
            all_signals = list(evd.get("limit_up_days_as_of") or []) \
                + list(evd.get("retrospective_limit_up_days") or [])
            for x in all_signals:
                dt = x["date"]
                lo, hi = limit_band(tk, dt)
                both = both_pcts(con, sid, dt)
                if both is None:
                    stats["missing_rows"] += 1
                    continue
                basis, pct = classify(both["raw_pct"], both["adj_pct"], lo, hi)
                stats["total"] += 1
                by_board[board] += 1
                if basis is None:
                    stats["not_a_signal_under_final_rule"] += 1
                    mismatches.append({"event_id": eid, "security_id": sid, "date": dt,
                                       "raw_pct": round(both["raw_pct"], 3),
                                       "adjusted_pct": round(both["adj_pct"], 3)})
                    continue
                if basis != x.get("basis"):
                    stats["basis_mismatch"] += 1
                    mismatches.append({"event_id": eid, "security_id": sid, "date": dt,
                                       "artifact_basis": x.get("basis"), "audit_basis": basis})
                else:
                    stats["basis_agree"] += 1
                if abs((both["adj_pct"] or 0) - (both["raw_pct"] or 0)) > 0.5:
                    stats["raw_adj_differ_gt_0_5pp"] += 1
    # 仿射关系抽样（茅台 2016 纯加法 / 兆易创新 k≠1）
    for sid, rng in (("MOUTAI", ("2016-06-20", "2016-06-30")),
                     ("GIGADEVICE", ("2020-04-28", "2020-05-06"))):
        rows = con.execute(
            "SELECT a.trade_date td, r.close raw_close, a.adj_close adj_close "
            "FROM market_daily a JOIN market_daily r "
            "  ON r.series_id=a.series_id AND r.trade_date=a.trade_date AND r.price_type='raw' "
            "WHERE a.series_id=? AND a.price_type='adjusted' "
            "AND a.trade_date BETWEEN ? AND ? ORDER BY a.trade_date",
            (sid, rng[0], rng[1])).fetchall()
        if len(rows) >= 2:
            a, b = rows[0], rows[-1]
            if (b["raw_close"] - a["raw_close"]) != 0:
                k = ((b["adj_close"] - a["adj_close"]) / (b["raw_close"] - a["raw_close"]))
                c = a["adj_close"] - k * a["raw_close"]
                affine_samples.append({
                    "security_id": sid, "range": list(rng),
                    "k": round(k, 6), "c": round(c, 4),
                    "note": ("k=1 → 纯加法复权（c=累计分红调整，故早年高分红段出现负价）"
                             if abs(k - 1) < 1e-6 else
                             "k≠1 → 仿射复权；adj_close 比值会偏离原始价环比"),
                })
    con.close()

    total = stats["total"]
    verdict = {
        "signal_days_audited": total,
        "by_board": dict(by_board),
        "basis_agree_with_artifact": stats["basis_agree"],
        "basis_mismatch": stats["basis_mismatch"],
        "not_a_signal_under_final_rule": stats["not_a_signal_under_final_rule"],
        "raw_adj_differ_gt_0_5pp": stats["raw_adj_differ_gt_0_5pp"],
        "missing_rows": stats["missing_rows"],
        "mismatch_samples": mismatches[:8],
    }
    doc = {
        "artifact": "limit_up_audit",
        "artifact_version": "0.%d" % version,
        "generated_at": GENERATED_AT,
        "generated_by": "research/scripts/audit_market_limit_up_v0_1.py",
        "supersedes": ("research/research/reports/limit_up_audit_v0_%d.json" % (version - 1)
                       if version > 1 else None),
        # ★ v0.32：审计对象可追溯（读的是哪个版本的角色产物）
        "audited_roles_artifact": os.path.relpath(roles_path, REPO).replace(os.sep, "/"),
        "st_rules": ST_RULES,
        "schema_facts": {
            "market_daily_columns": ["series_id", "trade_date", "open", "high", "low", "close",
                                     "adj_close", "price_type", "volume", "amount",
                                     "data_source", "retrieved_at"],
            "price_types": ["raw", "adjusted"],
            "has_pre_close": False,
            "pre_close_consequence": ("★ 库内**没有** `pre_close`（交易所参考前收）→ "
                                      "官方「当日涨跌幅」无法直接取到，只能用相邻交易日比值近似。"),
            "securities_columns": ["security_id", "ticker", "name", "exchange"],
            "has_st_flag": False,
            "st_consequence": ("★ `securities` 无 ST 标记 → ST 状态**无法从库内判定**。"
                               "但「ST 一律 5%、一律漏报」的说法**不成立**（v0.32 按板块与时期更正）："
                               "主板 ST 5%（≤2026-07-05）/ 10%（≥2026-07-06）、"
                               "创业板 ST 5%（≤2020-08-23）/ 20%（≥2020-08-24）、科创板 ST 20%。"
                               "⇒ 只有主板新规前与创业板改革前的 ST 落在带外（漏报）；"
                               "其余与普通股同带，**不会被漏掉**。详见 `st_rules`。"),
        },
        "adjustment_relation": {
            "finding": ("★★ 该 provider 的前复权与原始价是**仿射**关系："
                        "`adj_close ≈ k·raw_close − c`（k/c 只在公司行为日变化）。"),
            "samples": affine_samples,
            "consequence": ("★ 因此 `adj_close` 比值**不能**等同于官方涨跌幅：偏移（c）越大，"
                            "比值偏离越大；茅台 2016 段 c=−297.755 已使 adj_close 变负"
                            "（`non_positive_adj_close`）。"),
        },
        "final_rule": {
            "primary": "非公司行为日取**原始价收盘环比**（= 官方涨跌幅）",
            "action_day": "|raw 环比| > 21.6%（拆股/送转/大额除权）→ 取复权环比",
            "cross_check": ("同时用复权环比核验：两者都在带内 → `both_series_agree`；"
                            "仅复权在带内 → `adjusted_ratio_ex_dividend`（当日除息，官方以复权为准）；"
                            "**仅原始价在带内 → 不确认**"),
            "bands": {"MAIN": "9.8–10.6%", "GEM_before_2020-08-24": "9.8–10.6%",
                      "GEM_after_2020-08-24": "19.5–21.2%", "STAR": "19.5–21.2%"},
            "why_band": "用「带」而非「≥阈值」：复权噪声会产生 13%/16% 这类非涨停跳变",
        },
        "rejected_approach": {
            "formula": "pre_close_t = raw_{t-1} − (offset_t − offset_{t-1})，offset = adj − raw",
            "why_rejected": ("★ 该公式假设复权是**纯加法**（k=1）。实测存在 k≠1 的序列"
                             "（兆易创新 k≈0.51）→ 会把 2020-05-06 的真实 +10.0% 算成 +4.86%，"
                             "从而漏判涨停。已改用双口径规则，此处留证避免重复踩。"),
        },
        "verdict": verdict,
        "limits": [
            "★ 识别结果是「价格区间信号」，不是交易所官方涨停认定；没有 pre_close 字段，"
            "除权除息日的官方涨跌幅无法逐日复算。",
            "★ ST 状态无法从库内判定；漏报范围**按板块与时期**不同（见 `st_rules`）—— "
            "只有主板 2026-07-06 之前、创业板 2020-08-24 之前的 ST 落在带外；"
            "创业板/科创板 ST 与主板新规后的 ST 与普通股同带。",
            "★ 退市整理期 / 新股上市首日等特殊状态同样无法从库内判定 → 不检测；"
            "相关规则本轮未独立核实（见 `st_rules.not_verified`）。",
            "★ 板块规则按 ticker 前缀与日期近似；规则生效日（科创板 2019-07-22、"
            "创业板 2020-08-24）边界日未逐日核对交易所公告。",
            "★ 小额除息日（原始价跳变在日涨跌停范围内）无法与普通交易日区分 → "
            "此类日子原始价环比会略低于官方涨跌幅，可能漏报（方向可接受）。",
            "★ 盘面异动只能证明「当时观察到某种市场行为」，**不能**证明该股是题材核心、"
            "当时公认的龙头或题材上涨的驱动者。",
        ],
    }
    return doc


def main(argv):
    ap = argparse.ArgumentParser(description="盘面涨停识别可验证性审计")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--version", type=int, default=None,
                    help="写产物时的版本号（--check 恒用最新版本）")
    a = ap.parse_args(argv)
    doc = audit(a.version or 2)
    v = doc["verdict"]
    print("审计信号日: %d（%s）" % (v["signal_days_audited"], v["by_board"]))
    print("  与产物计算基础一致: %d | 不一致: %d | 按最终规则不算信号: %d"
          % (v["basis_agree_with_artifact"], v["basis_mismatch"],
             v["not_a_signal_under_final_rule"]))
    print("  raw 与复权差 >0.5pp 的交易日: %d | 缺行: %d"
          % (v["raw_adj_differ_gt_0_5pp"], v["missing_rows"]))
    if a.check:
        out_path = audit_out_path()
        if not os.path.exists(out_path):
            print("FAIL: 审计产物不存在：%s" % os.path.relpath(out_path, REPO))
            return 1
        with open(out_path, encoding="utf-8") as fh:
            cur = json.load(fh)
        # ★ v0.32：审计必须对齐**当前最新角色产物**，否则「审的是旧角色」
        if cur.get("audited_roles_artifact") != doc["audited_roles_artifact"]:
            print("FAIL: 审计产物审计的角色版本不是最新：%s vs %s"
                  % (cur.get("audited_roles_artifact"), doc["audited_roles_artifact"]))
            return 1
        if cur.get("st_rules") != doc["st_rules"]:
            print("FAIL: 审计产物的 ST 规则说明与脚本不一致（规则改了就升版重写）")
            return 1
        if cur.get("verdict") != doc["verdict"]:
            print("FAIL: 审计产物与重新推导不一致")
            return 1
        if v["basis_mismatch"] or v["not_a_signal_under_final_rule"]:
            print("FAIL: 有信号日与最终规则不符")
            return 1
        print("PASS: 涨停识别审计产物一致（%d 个信号日全部与最终规则相符）"
              % v["signal_days_audited"])
        return 0
    if a.write:
        if a.version is None:
            print("FAIL: --write 必须显式给 --version N（产物只增不改）")
            return 1
        out_path = audit_out_path(a.version)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        if os.path.exists(out_path):
            print("FAIL: 目标已存在，拒绝覆盖：%s" % os.path.relpath(out_path, REPO))
            return 1
        with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        print("已生成 %s" % os.path.relpath(out_path, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
