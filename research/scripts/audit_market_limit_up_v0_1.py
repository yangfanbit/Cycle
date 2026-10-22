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
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

REPO = db.REPO_ROOT
CURRENT = os.path.join(REPO, "research", "current")
MARKET_DB = os.path.join(REPO, "research", "database", "market_data.db")
ROLES_PATH = os.path.join(CURRENT, "historical_market_roles_v0_3.json")
OUT_PATH = os.path.join(REPO, "research", "research", "reports", "limit_up_audit_v0_1.json")
GENERATED_AT = "2026-10-22"

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


def audit():
    index = json.load(open(os.path.join(CURRENT, "historical_event_maps_index.json"),
                           encoding="utf-8"))
    tickers = load_tickers(index)
    roles = json.load(open(ROLES_PATH, encoding="utf-8"))
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
        "artifact_version": "0.1",
        "generated_at": GENERATED_AT,
        "generated_by": "research/scripts/audit_market_limit_up_v0_1.py",
        "supersedes": None,
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
                               "ST 涨跌停为 5%，落在 10%/20% 带之外 ⇒ 天然不被识别（漏报，可接受方向）；"
                               "qfq 噪声把价格拉到带内时可能误报 → 由双口径核验兜底。"),
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
            "★ ST / 退市整理 / 新股上市首日等特殊状态无法从库内判定 → 不检测（漏报方向）。",
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
    a = ap.parse_args(argv)
    doc = audit()
    v = doc["verdict"]
    print("审计信号日: %d（%s）" % (v["signal_days_audited"], v["by_board"]))
    print("  与产物计算基础一致: %d | 不一致: %d | 按最终规则不算信号: %d"
          % (v["basis_agree_with_artifact"], v["basis_mismatch"],
             v["not_a_signal_under_final_rule"]))
    print("  raw 与复权差 >0.5pp 的交易日: %d | 缺行: %d"
          % (v["raw_adj_differ_gt_0_5pp"], v["missing_rows"]))
    if a.check:
        if not os.path.exists(OUT_PATH):
            print("FAIL: 审计产物不存在：%s" % os.path.relpath(OUT_PATH, REPO))
            return 1
        cur = json.load(open(OUT_PATH, encoding="utf-8"))
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
        os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
        if os.path.exists(OUT_PATH):
            print("FAIL: 目标已存在，拒绝覆盖：%s" % os.path.relpath(OUT_PATH, REPO))
            return 1
        with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        print("已生成 %s" % os.path.relpath(OUT_PATH, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
