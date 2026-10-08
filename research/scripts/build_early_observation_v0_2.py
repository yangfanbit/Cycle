#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_early_observation_v0_2.py —— 「提前观察」：**L1 市场层**（历史 + 当前）+ L2 标的层（仅历史）。

设计依据：`docs/DESIGN_EARLY_OBSERVATION_v0_2.md`

## 分层（按**选择偏差的性质**分，不是按内容分）

| 层 | 对象 | 选择偏差 | 可否与当前并列 |
|---|---|---|---|
| **L1 市场层** | 基准指数 `SH000300` | **无**（指数不是选出来的） | ✅ 可以 |
| **L2 标的层（历史）** | campaign 已登记标的 | **有**（**事后选定**） | ❌ 不可 |
| **L3 当前对象→标的** | — | — | **不做**（会事实上成为个股清单） |

## ★★ 三条硬约束

1. **不做「像不像」** —— 本产物**只有事实**，没有相似度 / 匹配 / 命中 / 概率 / 评分 / 排序。
2. **全部 ex-ante** —— 每个检查点只用它**当日及之前**的数据。
3. **L2 不得与当前并列** —— 其标的是事后选定的；与当下并列会把结果混进输入。

## v0_1 → v0_2

- 新增 **L1 市场层**（历史 53 段 + **当前**），基准固定 `SH000300`
- 新增**多检查点** T-60 / T-40 / T-20 / T-10 / T-5 / T-1（单一窗口看不出演变）
- L2 沿用 v0_1，**补上偏差标注**
- 基准层**不输出相对强度**（相对自身恒为 0，无意义）

## 用法

    python research/scripts/build_early_observation_v0_2.py
"""

from __future__ import annotations

import io
import json
import math
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

REP = os.path.join(db.ROOT, "research", "reports")
OUT = os.path.join(REP, "early_observation_v0_2.json")

BENCH = "SH000300"
CHECKPOINTS = (60, 40, 20, 10, 5, 1)
LOOKBACK = 20
MIN_HISTORY = 60


def load(conn, sid):
    return conn.execute(
        "SELECT trade_date, close, volume FROM market_daily "
        "WHERE series_id=? AND price_type='raw' AND close IS NOT NULL ORDER BY trade_date",
        (sid,)).fetchall()


def bench_ret20(rows, i):
    return (rows[i][1] / rows[i - 20][1] - 1) * 100 if i >= 20 else None


def obs_at(rows, i, bench_ret20_pct=None, with_rel=True):
    """只用 rows[≤i] 计算（**ex-ante**）。"""
    if i + 1 < MIN_HISTORY:
        return None
    close = [r[1] for r in rows]
    vol = [r[2] for r in rows]
    win = [v for v in vol[i - 59:i + 1] if v is not None]
    vp = round(sum(1 for v in win if v <= vol[i]) / len(win), 3) if (len(win) >= 30 and vol[i] is not None) else None

    def sd(a):
        rs = [math.log(a[k] / a[k - 1]) for k in range(1, len(a)) if a[k] and a[k - 1]]
        return statistics.pstdev(rs) if len(rs) >= 5 else None
    s20, s60 = sd(close[i - 20:i + 1]), sd(close[i - 60:i + 1])
    out = {
        "date": rows[i][0],
        "close": round(close[i], 3),
        "vol_pct60": vp,
        "ret_20_pct": round((close[i] / close[i - 20] - 1) * 100, 2),
        "vol_ratio": round(s20 / s60, 3) if (s20 and s60) else None,
        "above_ma20": close[i] > sum(close[i - 19:i + 1]) / 20,
        "above_ma60": close[i] > sum(close[i - 59:i + 1]) / 60,
    }
    if with_rel:
        r = out["ret_20_pct"]
        out["rel_strength_20"] = round(r - bench_ret20_pct, 2) if bench_ret20_pct is not None else None
    return out


def median_of(items, key):
    vals = [x[key] for x in items if x.get(key) is not None]
    return round(statistics.median(vals), 3) if vals else None


def main():
    conn = db.connect()
    bench = load(conn, BENCH)
    if not bench:
        raise SystemExit("缺少基准 %s" % BENCH)

    # ---------- L1 · 当前市场状态（取最新可得交易日） ----------
    cur_i = len(bench) - 1
    current_market = obs_at(bench, cur_i, with_rel=False)
    current_market_series = [x for x in (obs_at(bench, i, with_rel=False) for i in range(max(0, cur_i - 19), cur_i + 1)) if x]

    bench_by_date = {r[0]: i for i, r in enumerate(bench)}

    rows = conn.execute("SELECT campaign_id, campaign_year, start_date, peak_date, end_date FROM campaigns ORDER BY campaign_year, campaign_id").fetchall()
    out, cache = {}, {}
    tally = {"OK": 0, "PARTIAL": 0, "NO_DATA": 0}

    for cid, yr, s, p, e in rows:
        if not s:
            out[cid] = {"campaign_id": cid, "status": "NO_START"}
            tally["NO_DATA"] += 1
            continue
        # ---------- L1 · 该 campaign 启动前的市场状态 ----------
        bidx = [i for i, r in enumerate(bench) if r[0] < s]
        market_layer = None
        if len(bidx) >= MIN_HISTORY:
            cps = []
            for t in CHECKPOINTS:
                if len(bidx) < t:
                    continue
                o = obs_at(bench, bidx[-t], with_rel=False)
                if o:
                    o = dict(o, t_minus=t)
                    cps.append(o)
            series = [x for x in (obs_at(bench, i, with_rel=False) for i in bidx[-LOOKBACK:]) if x]
            market_layer = {
                "series_id": BENCH,
                "checkpoints": list(reversed(cps)),
                "series": series,
                "at_last_day": cps[-1] if cps else None,
                "note": "基准指数**不是选出来的** → 本层**可与当前并列**",
            }

        # ---------- L2 · 该 campaign 已登记标的（★ 事后选定，不得与当前并列） ----------
        secs = [x[0] for x in conn.execute("SELECT security_id FROM campaign_securities WHERE campaign_id=?", (cid,))]
        per = []
        for sid in secs:
            if sid not in cache:
                cache[sid] = load(conn, sid)
            rs = cache[sid]
            idx = [i for i, r in enumerate(rs) if r[0] < s]
            if len(idx) < MIN_HISTORY:
                per.append({"security_id": sid, "status": "NO_DATA", "rows_before_start": len(idx)})
                continue
            pts = idx[-LOOKBACK:]
            series = []
            for i in pts:
                bi = bench_by_date.get(rs[i][0])          # 同一交易日的基准位次
                br = bench_ret20(bench, bi) if bi is not None else None
                o = obs_at(rs, i, br)
                if o:
                    series.append(o)
            if not series:
                per.append({"security_id": sid, "status": "NO_DATA", "rows_before_start": len(idx)})
                continue
            per.append({"security_id": sid, "status": "OK",
                        "lookback_from": series[0]["date"], "lookback_to": series[-1]["date"],
                        "series": series, "at_last_day": series[-1]})
        ok = [x for x in per if x["status"] == "OK"]
        security_layer = None
        if ok:
            n = max(len(x["series"]) for x in ok)
            med = []
            for k in range(-n, 0):
                items = [x["series"][k] for x in ok if len(x["series"]) >= -k]
                if not items:
                    continue
                med.append({"date": items[-1]["date"],
                            "vol_pct60": median_of(items, "vol_pct60"),
                            "ret_20_pct": median_of(items, "ret_20_pct"),
                            "rel_strength_20": median_of(items, "rel_strength_20"),
                            "vol_ratio": median_of(items, "vol_ratio")})
            security_layer = {
                "per_security": per, "median_series": med,
                "bias_note": ("★ 本层标的为**事后选定**（记录自己声明为回顾性识别）——"
                              "**不得与当前并列**：那会把「已经涨过」混进输入，"
                              "使任何形态比较系统性偏高。"),
            }

        status = "OK" if (market_layer and security_layer and len(ok) == len(secs)) else ("NO_DATA" if not market_layer else "PARTIAL")
        tally[status if status in tally else "PARTIAL"] += 1
        out[cid] = {
            "campaign_id": cid, "campaign_year": yr, "start": s, "peak": p, "end": e,
            "status": status,
            "market_layer": market_layer,
            "security_layer": security_layer,
        }

    res = {
        "artifact": "early_observation",
        "artifact_version": "0.2",
        "generated_by": "research/scripts/build_early_observation_v0_2.py",
        "supersedes": "research/research/reports/early_observation_v0_1.json",
        "design": "docs/DESIGN_EARLY_OBSERVATION_v0_2.md",
        "position": ("Research-only 描述性产物 —— **只提供事实**：历史启动前的市场状态 + 当前市场状态。"
                     "**不含**相似度 / 匹配 / 命中 / 概率 / 评分 / 排序 / 预测。"),
        "layers": {
            "L1_market": {"object": "基准指数 %s（不是选出来的）" % BENCH,
                          "selection_bias": "无", "comparable_with_current": True},
            "L2_security": {"object": "campaign 已登记标的", "selection_bias": "有（**事后选定**）",
                            "comparable_with_current": False,
                            "reason": "与当下并列会把「已经涨过」混进输入，使形态比较系统性偏高"},
            "L3_current_to_security": {"built": False,
                                       "why": ("① 当前对象无标的字段且行情原止于 2025-12-31；"
                                               "② 映射不可审计；"
                                               "③ 一个「当前主题 + 代表个股 + 现量价」的区块**事实上就是个股清单**，"
                                               "与 AGENTS.md §1「禁荐股」只隔一层措辞。"
                                               "替代方案是用概念指数（非个股），但 concept_index 目前 0 行数据。")},
        },
        "rules": {
            "checkpoints_t_minus": list(CHECKPOINTS),
            "ex_ante": "每个检查点只用**它当日及之前**的数据（滚动窗口），不引入未来信息",
            "observables": {
                "vol_pct60": "当日成交量在过去 60 个交易日中的分位（0–1）",
                "ret_20_pct": "过去 20 个交易日收益率（%）",
                "rel_strength_20": "ret_20 − 基准同期收益（百分点）—— ★ **L1 不输出**（相对自身恒为 0，无意义）",
                "vol_ratio": "20 日已实现波动率 / 60 日已实现波动率",
                "above_ma20": "收盘价是否站上 20 日均线",
                "above_ma60": "收盘价是否站上 60 日均线",
            },
            "all_dimensionless": "四个量均无量纲 → 跨标的、跨时期可比（**价格水平本身不可比，故不呈现**）",
            "benchmark_fixed": "基准固定 `%s`，**不按 campaign 更换**（换基准会变结论，按 campaign 换等于事后择优）" % BENCH,
            "no_matching": "★ 本产物**不做**「现在像不像历史」的判定；并列呈现，判断留给读者",
        },
        "current_market": {
            "series_id": BENCH,
            "as_of": current_market["date"] if current_market else None,
            "observables": current_market,
            "series": current_market_series,
            "note": ("取**最新可得交易日**。当前快照日为 2026-09-15；"
                     "行情已补至 2026-09-30（国庆假期后无新交易日）。"),
        },
        "summary": tally,
        "by_campaign": out,
    }
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    print("written", OUT)
    print("summary:", json.dumps(tally, ensure_ascii=False))
    print()
    print("=== L1 · 当前市场状态（%s）===" % res["current_market"]["as_of"])
    c = current_market
    print("  vol_pct60=%s ret_20=%s%% vol_ratio=%s ma20=%s ma60=%s" % (
        c["vol_pct60"], c["ret_20_pct"], c["vol_ratio"], c["above_ma20"], c["above_ma60"]))
    print()
    print("=== 样例：C-2023-AD 启动前基准检查点 ===")
    ml = (out.get("C-2023-AD") or {}).get("market_layer")
    if ml:
        for x in ml["checkpoints"]:
            print("  T-%-3s %s  vol_pct60=%-5s ret20=%-6s vol_ratio=%-5s ma20=%s ma60=%s" % (
                x["t_minus"], x["date"], x["vol_pct60"], x["ret_20_pct"], x["vol_ratio"], x["above_ma20"], x["above_ma60"]))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
