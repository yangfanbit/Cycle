# -*- coding: utf-8 -*-
"""
TEMPORARY RESEARCH SCRIPT — Seasonal Observation Pattern Discovery v0.1
========================================================================
STATUS: 临时研究脚本。**不是产品代码。**

核心任务：**选择偏差 / 基准率检验**（研究任务 §18 + §11-C）

问题：ThreeC 只记录了「成功 / 有关注」的主题。那么"6 月集中"到底是
      (a) 主题启动时间的真实季节性，还是
      (b) 记录样本本身（研究时人工挑选的年份 × 事件窗口）造成的？

做法（不引入新数据源，全部用仓库内既有行情）：
  T1. 「事件驱动点火日」基准分布
      用 DB 中既有 events 的日期（33 条，横跨 2018-2025，含 policy/company/market），
      计算其 day-of-year 分布，检验「政策/公司/市场事件本身是否集中在 6 月」。
      如果事件本身也集中在 6 月 → 说明「6 月集中」可能来自事件日历，而非主题选择。
  T2. 「指数级 30 日涨幅前列」基准分布
      用 AUTO_SW / AUTO_ETF_516110 / PHARMA_ETF / NEV 等既有指数，
      逐年逐日滚动 30 交易日收益，取每年「最大 30 日涨幅的起点日」，
      看起点日分布。这是「不限主题、让市场自己说话」的中性基准
      ——检验「A 股本来就容易在 6 月启动行情」这一竞争假设。
  T3. 全年均匀基准（解析 + permutation，已有）
纪律：只读 DB。不做收益预测；涨幅仅用于**基准分布**，不用于定义启动。
"""

import csv
import json
import math
import os
import random
import sqlite3
from collections import Counter, defaultdict
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
DB = os.path.join(REPO, "research", "database", "cycle_research.db")
random.seed(20260916)
PERIOD = 365


def doy_norm(dd):
    n = dd.timetuple().tm_yday
    if dd.month >= 3 and (dd.year % 4 == 0 and (dd.year % 100 != 0 or dd.year % 400 == 0)):
        n -= 1
    return n


def month_of(n):
    return date.fromordinal(date(2025, 1, 1).toordinal() + ((int(round(n)) - 1) % PERIOD)).month


def md(n):
    return date.fromordinal(date(2025, 1, 1).toordinal() + ((int(round(n)) - 1) % PERIOD)).strftime("%m-%d")


def circ_min_max(xs):
    s = sorted(x % PERIOD for x in xs)
    n = len(s)
    bg, bi = -1, 0
    for i in range(n):
        g = (s[(i + 1) % n] - s[i]) % PERIOD
        if g > bg:
            bg, bi = g, i
    return s[(bi + 1) % n], s[bi], (s[bi] - s[(bi + 1) % n]) % PERIOD


def chi2_uniform_month(months_count, n_months=12):
    """月份均匀性卡方（探索性）。"""
    n = sum(months_count)
    if n == 0:
        return None
    exp = n / n_months
    chi2 = sum((c - exp) ** 2 / exp for c in months_count)
    # 粗略 p（df=11，用 Wilson-Hilferty 近似）
    df = n_months - 1
    z = ((chi2 / df) ** (1 / 3) - (1 - 2 / (9 * df))) / math.sqrt(2 / (9 * df))
    p = 0.5 * (1 - math.erf(z / math.sqrt(2)))  # 上尾近似
    return {"chi2": chi2, "df": df, "p_approx_one_sided": p, "note": "近似 p，探索性"}


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    out = {}

    # ================================================== T1 事件基准
    cur.execute("SELECT event_id,date,name,event_type FROM events ORDER BY date")
    evs = cur.fetchall()
    ev_rows = []
    for r in evs:
        dd = datetime.strptime(r["date"][:10], "%Y-%m-%d").date()
        ev_rows.append({"event_id": r["event_id"], "date": r["date"], "type": r["event_type"],
                        "doy": doy_norm(dd), "month": dd.month, "md": dd.strftime("%m-%d")})
    mc = Counter(e["month"] for e in ev_rows)
    months_count = [mc.get(m, 0) for m in range(1, 13)]
    out["T1_event_baseline"] = {
        "n_events": len(ev_rows),
        "month_distribution": {f"{m:02d}": mc.get(m, 0) for m in range(1, 13)},
        "june_share": mc.get(6, 0) / len(ev_rows),
        "uniform_june_share": 1 / 12,
        "chi2_uniform_month": chi2_uniform_month(months_count),
        "by_type_month": {},
        "note": "事件日历基准：ThreeC 记录的 33 个事件本身是否集中在某月",
    }
    btm = defaultdict(Counter)
    for e in ev_rows:
        btm[e["type"]][e["month"]] += 1
    out["T1_event_baseline"]["by_type_month"] = {k: dict(sorted(v.items())) for k, v in btm.items()}

    # ================================================== T2 指数滚动 30 日涨幅起点基准
    cur.execute("SELECT DISTINCT series_id, series_type FROM market_series")
    series = [dict(r) for r in cur.fetchall()]
    index_series = [s for s in series if s["series_type"] in ("industry_index", "concept_index", "benchmark")]

    t2 = {}
    for s in index_series:
        sid = s["series_id"]
        cur.execute(
            "SELECT trade_date, close FROM market_daily WHERE series_id=? AND close IS NOT NULL ORDER BY trade_date",
            (sid,),
        )
        data = [(datetime.strptime(r["trade_date"][:10], "%Y-%m-%d").date(), r["close"]) for r in cur.fetchall()]
        if len(data) < 40:
            continue
        by_year_best = {}
        W = 30
        for i in range(len(data) - W):
            p0 = data[i][1]
            p1 = data[i + W][1]
            if not p0:
                continue
            ret = p1 / p0 - 1
            y = data[i][0].year
            if y not in by_year_best or ret > by_year_best[y][0]:
                by_year_best[y] = (ret, data[i][0], data[i + W][0])
        # 只统计该序列覆盖的年份中「有完整 30 日窗」的
        year_days = defaultdict(int)
        for dd, _ in data:
            year_days[dd.year] += 1
        usable = {y: v for y, v in by_year_best.items() if year_days[y] >= 200}
        if len(usable) < 3:
            continue
        doys = [doy_norm(v[1]) for v in usable.values()]
        mds = [v[1].strftime("%m-%d") for v in usable.values()]
        mc2 = Counter(month_of(x) for x in doys)
        t2[sid] = {
            "series_name": s.get("name") or sid,
            "years": sorted(usable),
            "best_window_start_md": mds,
            "best_window_start_doy": doys,
            "returns": [round(v[0], 4) for v in usable.values()],
            "month_distribution": {f"{m:02d}": mc2.get(m, 0) for m in range(1, 13)},
            "june_count": mc2.get(6, 0),
            "n_years": len(usable),
        }
        lo, hi, span = circ_min_max(doys) if len(doys) >= 2 else (None, None, None)
        t2[sid]["span_days"] = span
        t2[sid]["earliest_md"], t2[sid]["latest_md"] = (md(lo), md(hi)) if lo else (None, None)

    out["T2_index_best_30d_window_baseline"] = t2

    # 汇总：所有指数的最强 30 日窗口起点月份分布
    allmonths = Counter()
    allmd = []
    for sid, v in t2.items():
        for m, c in v["month_distribution"].items():
            allmonths[int(m)] += c
        allmd += v["best_window_start_md"]
    total = sum(allmonths.values())
    out["T2_aggregate"] = {
        "n_series": len(t2),
        "n_observations": total,
        "month_distribution": {f"{m:02d}": allmonths.get(m, 0) for m in range(1, 13)},
        "june_share": allmonths.get(6, 0) / total if total else None,
        "uniform_june_share": 1 / 12,
        "chi2": chi2_uniform_month([allmonths.get(m, 0) for m in range(1, 13)]),
        "note": (
            "中性基准：不限主题，直接看 A 股主要指数「年内最强 30 个交易日」的起点落在哪个月。"
            "若该基准本身 6 月占比高 → 说明「6 月集中」可能是市场层面现象，而非汽车主题独有。"
        ),
    }

    # ================================================== T3 主题族 vs 基准对照
    fam_path = os.path.join(HERE, "family_analysis.json")
    if os.path.exists(fam_path):
        with open(fam_path, "r", encoding="utf-8") as f:
            fam = json.load(f)
        comp = {}
        for label, a in fam.get("families", {}).items():
            june = a["month_distribution"].get("06", 0)
            n = a["n_years"]
            comp[label] = {
                "n_years": n,
                "june_count": june,
                "june_share": june / n,
                "baseline_june_share_T1": out["T1_event_baseline"]["june_share"],
                "baseline_june_share_T2": out["T2_aggregate"]["june_share"],
                "lift_vs_T1": (june / n) / out["T1_event_baseline"]["june_share"] if out["T1_event_baseline"]["june_share"] else None,
                "lift_vs_T2": (june / n) / out["T2_aggregate"]["june_share"] if out["T2_aggregate"]["june_share"] else None,
            }
        out["T3_family_vs_baseline"] = comp

    with open(os.path.join(HERE, "baseline_analysis.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)

    # ---------------- 打印
    print("=" * 78)
    print("T1 — 事件日历基准（33 个事件）")
    print(f"  月份分布: {out['T1_event_baseline']['month_distribution']}")
    print(f"  6月占比: {out['T1_event_baseline']['june_share']:.3f}  (均匀基准 {1/12:.3f})")
    print(f"  卡方: {out['T1_event_baseline']['chi2_uniform_month']}")
    print(f"  按类型月份: {json.dumps(out['T1_event_baseline']['by_type_month'], ensure_ascii=False)}")

    print("=" * 78)
    print("T2 — 指数「年内最强 30 交易日」起点月份分布（中性基准）")
    for sid, v in t2.items():
        print(f"  {sid:20s} n={v['n_years']:2d} months={v['month_distribution']} starts={v['best_window_start_md']}")
    print(f"\n  汇总: {out['T2_aggregate']['month_distribution']}")
    print(f"  6月占比: {out['T2_aggregate']['june_share']:.3f} (均匀 {1/12:.3f})")
    print(f"  卡方: {out['T2_aggregate']['chi2']}")

    if "T3_family_vs_baseline" in out:
        print("=" * 78)
        print("T3 — 主题族 6 月占比 vs 两个基准")
        for k, v in out["T3_family_vs_baseline"].items():
            print(f"  {k:34s} n={v['n_years']}  6月占比={v['june_share']:.2f}  "
                  f"lift_vs_event={v['lift_vs_T1']:.2f}x  lift_vs_index={v['lift_vs_T2']:.2f}x")


if __name__ == "__main__":
    main()
