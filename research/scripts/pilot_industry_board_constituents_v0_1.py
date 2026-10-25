#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pilot_industry_board_constituents_v0_1.py —— 行业板块「历史成分」映射试点（v0.51）。

## 为什么只做**一个**试点

`pattern_discovery_v0_10` 的 204 条当前窗口里，**75 条行业板块窗口全部未绑定个股**
（`representative_stocks = null`，`rep_stock_gap` 写着「行业板块无历史成分 → 不绑个股」）。
在批量补 75 条之前，先用**一个**板块验证：到底能不能补？补出来的东西可不可信？

## 试点对象的选取（不是挑好看的结果）

在 61 个未绑定板块里，只有 3 个在**名称层面**能对上某个自建概念篮子
（互联网电商→电商概念、游戏→网络游戏、电池→BC/钒/钠/固态电池）。
其中 **游戏（BK881275）↔ 网络游戏（CPT_wlyx）** 语义最接近、双方历史都够长、
且该窗口是 STRICT（12 年 2014–2025）→ 选它。另外两个是**子集关系**
（固态电池 ⊂ 电池），拿子集代理全集在口径上更不成立。

## ★★ 预先声明的判据（**先写死，再看结果**）

| 指标 | 阈值 | 含义 |
|---|---|---|
| `median_abs_diff_pp` | ≤ **2.0** | 逐年代理超额与板块超额的绝对差中位数 |
| `hit_agreement` | ≥ **0.80** | 逐年代理与板块「同向」的比例 |
| `survivor_share` | ≤ **0.20** | 当前成分中「在首个检验年 1 月之后才上市」的占比 |

三条**全部**满足 → `PROXY_ACCEPTABLE_WITH_LABEL`（可以带标签代理）；
任一不满足 → `PROXY_NOT_ACCEPTABLE`（**保留缺口**，不绑个股）。

## 这个试点**不能**证明什么

- 代理用的是**当前**成分 → 它测的是「当前成分回溯到过去」的误差，**不是**历史成分的误差；
- 即使误差小，也**不等于**「当时的板块成分就是这样」；
- 本试点不给任何选股结论，只回答「要不要批量补 75 条」。

## 用法

    python research/scripts/pilot_industry_board_constituents_v0_1.py            # 打印
    python research/scripts/pilot_industry_board_constituents_v0_1.py --write    # 落盘
    python research/scripts/pilot_industry_board_constituents_v0_1.py --check    # 逐字节比对
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sqlite3
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import discover_seasonal_patterns_v0_5 as D  # noqa: E402  ★ 复用同一 month_bounds/month_returns 口径

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
DB = os.path.join(REPO, "research", "database", "history_scan.db")
OUT_NAME = "industry_board_constituent_pilot_v0_1.json"
BENCH = "CSI300"

# ★★ 预先声明（不得看结果后调整）
MAX_MEDIAN_ABS_DIFF_PP = 2.0
MIN_HIT_AGREEMENT = 0.80
MAX_SURVIVOR_SHARE = 0.20
TOP_N_FOR_NAIVE_BINDING = 3      # 与概念篮子同一口径：按历史中位超额取前 3


def _dump(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def _latest_pd():
    import re
    rx = re.compile(r"pattern_discovery_v0_(\d+)\.json$")
    hits = [(int(rx.match(f).group(1)), f) for f in os.listdir(CURRENT) if rx.match(f)]
    return os.path.join(CURRENT, sorted(hits)[-1][1])


def _series(con, sid):
    return D.load(con, sid)


def _excess_by_year(series, bounds, bench_ret, month):
    mr = D.month_returns(series, bounds)
    out = {}
    for ym, ret in mr.items():
        if int(ym[4:6]) == month and ym in bench_ret:
            out[int(ym[:4])] = round(ret - bench_ret[ym], 2)
    return out


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs) ** 0.5
    syy = sum((y - my) ** 2 for y in ys) ** 0.5
    return round(sxy / (sxx * syy), 3) if sxx and syy else None


def build(board_sid, proxy_sid, month=None):
    pd_path = _latest_pd()
    pd = json.loads(io.open(pd_path, encoding="utf-8").read())
    win = next((w for w in pd["current_windows"]
                if w["board_series"] == board_sid and (month is None or w["month"] == month)), None)
    if win is None:
        raise SystemExit("FAIL: %s 不在当前窗口里（先用 --month 指定）" % board_sid)
    month = win["month"]

    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        bench = _series(con, BENCH)
        bounds = D.month_bounds(bench)
        cur_ym = pd["as_of"][:4] + pd["as_of"][4:6] if "-" not in pd["as_of"] else \
            pd["as_of"][:4] + pd["as_of"][5:7]
        bounds_hist = {ym: v for ym, v in bounds.items() if ym < cur_ym}
        bench_ret = D.month_returns(bench, bounds_hist)

        board_ex = _excess_by_year(_series(con, board_sid), bounds_hist, bench_ret, month)
        proxy_ex = _excess_by_year(_series(con, proxy_sid), bounds_hist, bench_ret, month)
        years = sorted(set(board_ex) & set(proxy_ex))

        members = json.loads((con.execute("SELECT v FROM scan_meta WHERE k=?",
                                         ("members:" + proxy_sid,)).fetchone() or ["[]"])[0])
        mrows = []
        for m in members:
            r = con.execute("SELECT name, first_date, last_date FROM scan_series WHERE series_id=?",
                            (m,)).fetchone()
            if r:
                mrows.append({"series_id": m, "name": r[0],
                              "first_date": r[1] if "-" in r[1] else
                              "%s-%s-%s" % (r[1][:4], r[1][4:6], r[1][6:]),
                              "last_date": r[2] if "-" in r[2] else
                              "%s-%s-%s" % (r[2][:4], r[2][4:6], r[2][6:])})
        mrows.sort(key=lambda x: x["series_id"])

        # 逐月覆盖：检验月的首末交易日该成员是否都有数据
        # ★★ 不能直接拿 bounds 的日期去 SQL 里比：`D.load` 已把日期归一成**紧凑** YYYYMMDD，
        #    而库里个股存的是 dashed（"2014-11-03"）→ 直接 IN (紧凑) 会**全查不到**，
        #    然后被读成「覆盖 0 只」= 把「取到空」当成「没有」。这里统一用归一化后的集合比。
        dset = {}
        for m in mrows:
            dset[m["series_id"]] = {D.norm(r[0]) for r in con.execute(
                "SELECT trade_date FROM scan_daily WHERE series_id=?", (m["series_id"],))}
        cover = []
        for y in years:
            ym = "%d%02d" % (y, month)
            if ym not in bounds_hist:
                continue
            d0, d1 = bounds_hist[ym]
            cover.append({"year": y,
                          "members_covered": sum(1 for m in mrows
                                                 if d0 in dset[m["series_id"]]
                                                 and d1 in dset[m["series_id"]])})

        # 天真绑定会选谁：按历史中位超额取前 N（与概念篮子同口径）
        naive = []
        for m in mrows:
            mr = D.month_returns(_series(con, m["series_id"]), bounds_hist)
            vals = [mr["%d%02d" % (y, month)] - bench_ret["%d%02d" % (y, month)]
                    for y in years
                    if "%d%02d" % (y, month) in mr and "%d%02d" % (y, month) in bench_ret]
            if len(vals) >= max(3, len(years) // 2):
                naive.append({"series_id": m["series_id"], "name": m["name"],
                              "first_date": m["first_date"], "n_years": len(vals),
                              "median_excess_pct": round(statistics.median(vals), 2),
                              "existed_in_first_year":
                                  bool(years) and m["first_date"] <= "%d-12-31" % years[0]})
        naive.sort(key=lambda x: -x["median_excess_pct"])
        naive = naive[:TOP_N_FOR_NAIVE_BINDING]
    finally:
        con.close()

    # ── 指标 ──
    diffs = [proxy_ex[y] - board_ex[y] for y in years]
    median_abs = round(statistics.median(abs(d) for d in diffs), 2) if diffs else None
    max_abs = round(max((abs(d) for d in diffs), default=0), 2) if diffs else None
    hit_agree = round(sum(1 for y in years
                          if (board_ex[y] > 0) == (proxy_ex[y] > 0)) / len(years), 3) if years else None
    corr = _pearson([board_ex[y] for y in years], [proxy_ex[y] for y in years]) if years else None
    first_year = years[0] if years else None
    survivors = [m for m in mrows if first_year and m["first_date"] > "%d-01-01" % first_year]
    survivor_share = round(len(survivors) / len(mrows), 3) if mrows else None

    reasons = []
    if median_abs is None or median_abs > MAX_MEDIAN_ABS_DIFF_PP:
        reasons.append("median_abs_diff_pp=%s > %.1f" % (median_abs, MAX_MEDIAN_ABS_DIFF_PP))
    if hit_agree is None or hit_agree < MIN_HIT_AGREEMENT:
        reasons.append("hit_agreement=%s < %.2f" % (hit_agree, MIN_HIT_AGREEMENT))
    if survivor_share is None or survivor_share > MAX_SURVIVOR_SHARE:
        reasons.append("survivor_share=%s > %.2f（%d/%d 只在 %s 之后才上市）"
                       % (survivor_share, MAX_SURVIVOR_SHARE, len(survivors), len(mrows), first_year))
    verdict = "PROXY_NOT_ACCEPTABLE" if reasons else "PROXY_ACCEPTABLE_WITH_LABEL"

    return {
        "artifact": "industry_board_constituent_pilot",
        "artifact_version": "0.1",
        "generated_by": "research/scripts/pilot_industry_board_constituents_v0_1.py",
        "question": ("行业板块窗口能否绑定个股？—— 用**一个**板块验证「当前概念成分回溯」"
                     "这条唯一可行路径的误差与幸存者偏差，据此决定要不要批量补 75 条。"),
        "source": {"pattern_discovery": {"file": os.path.basename(pd_path),
                                         "sha256": hashlib.sha256(
                                             io.open(pd_path, "rb").read()).hexdigest(),
                                         "as_of": pd["as_of"]},
                   "db": "research/database/history_scan.db", "benchmark": BENCH},
        "subject": {"board": win["board"], "board_series": board_sid,
                    "month": month, "tier": win.get("tier"),
                    "n_years": win.get("n_years"),
                    "median_excess_pct": win.get("median_excess_pct"),
                    "hit_rate": win.get("hit_rate"),
                    "proxy_concept": proxy_sid, "proxy_members": len(mrows)},
        "caliber": {
            "month_return": "close[月内最后交易日] / close[月内首个交易日] − 1（与季节性发现同一函数）",
            "excess": "该月收益 − 沪深300 同月收益（pp）",
            "proxy": "自建概念篮子的**当前**成分等权序列（不是历史成分）",
            "test_years": years,
        },
        "thresholds_declared_before_run": {
            "max_median_abs_diff_pp": MAX_MEDIAN_ABS_DIFF_PP,
            "min_hit_agreement": MIN_HIT_AGREEMENT,
            "max_survivor_share": MAX_SURVIVOR_SHARE,
        },
        "per_year": [{"year": y, "board_excess_pct": board_ex[y], "proxy_excess_pct": proxy_ex[y],
                      "diff_pp": round(proxy_ex[y] - board_ex[y], 2)} for y in years],
        "metrics": {
            "n_years": len(years),
            "median_abs_diff_pp": median_abs,
            "max_abs_diff_pp": max_abs,
            "level_bias_pp": round(statistics.median(diffs), 2) if diffs else None,
            "hit_agreement": hit_agree,
            "pearson_r": corr,
            "survivor_share": survivor_share,
            "survivors": [{"series_id": m["series_id"], "name": m["name"],
                           "first_date": m["first_date"]} for m in survivors],
            "member_coverage": cover,
            "median_members_covered": (statistics.median([c["members_covered"] for c in cover])
                                       if cover else None),
        },
        "naive_binding_would_pick": naive,
        "verdict": verdict,
        "verdict_reasons": reasons,
        "conclusion": (
            "行业板块**没有历史成分**（`scan_meta` 只有 173 个概念篮子的 `members:`，"
            "零个 `BK*` 板块）；唯一可行的替代是「当前概念成分回溯」，"
            "而它在本题上" + ("未通过" if reasons else "通过了") + "预先声明的三项判据。"
            + ("→ **保留缺口**，不批量补 75 条；`rep_stock_gap` 继续如实写「无历史成分」。"
               if reasons else
               "→ 可以按 `PROXY_CURRENT_CONCEPT` 标签批量补，但必须在 UI 上写明代理关系。")),
        "limits": [
            "代理用**当前**成分 → 测的是「当前成分回溯」的误差，不是历史成分的误差。",
            "即使误差小，也不等于「当时的板块成分就是这样」。",
            "本试点只回答「要不要批量补」，不含任何选股结论。",
            "单板块结论**不能**外推到其余 60 个板块（语义接近度不同）。",
        ],
    }


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", default="BK881275", help="行业板块 series_id（默认 游戏）")
    ap.add_argument("--proxy", default="CPT_wlyx", help="代理概念篮子 series_id（默认 网络游戏）")
    ap.add_argument("--month", type=int, default=None)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)

    if not os.path.exists(DB):
        print("SKIP: history_scan.db 不存在（CI 不携带 1.3GB 库）")
        return 0
    doc = build(a.board, a.proxy, a.month)
    body = _dump(doc)
    out = os.path.join(CURRENT, OUT_NAME)

    if a.check:
        if not os.path.exists(out):
            print("FAIL: 试点产物不存在，请先 --write")
            return 1
        if io.open(out, encoding="utf-8").read() != body:
            print("FAIL: 试点产物与当前数据不一致（需 --write 重建）")
            return 1
        print("PASS: 试点产物一致（%s）" % doc["verdict"])
        return 0

    m = doc["metrics"]
    print("试点：%s（%s）· %d 月 · 代理 %s（%d 只当前成分）"
          % (doc["subject"]["board"], doc["subject"]["board_series"], doc["subject"]["month"],
             doc["subject"]["proxy_concept"], doc["subject"]["proxy_members"]))
    print("  检验年 %d 个（%s–%s）" % (m["n_years"], doc["caliber"]["test_years"][0],
                                   doc["caliber"]["test_years"][-1]))
    print("  median|Δ超额| = %s pp（阈值 ≤ %.1f）" % (m["median_abs_diff_pp"], MAX_MEDIAN_ABS_DIFF_PP))
    print("  最大|Δ超额|   = %s pp" % m["max_abs_diff_pp"])
    print("  水平偏差(中位)= %s pp · Pearson r = %s" % (m["level_bias_pp"], m["pearson_r"]))
    print("  同向率        = %s（阈值 ≥ %.2f）" % (m["hit_agreement"], MIN_HIT_AGREEMENT))
    print("  幸存者占比    = %s（%d 只在首个检验年之后上市；阈值 ≤ %.2f）"
          % (m["survivor_share"], len(m["survivors"]), MAX_SURVIVOR_SHARE))
    print("  成员覆盖中位  = %s 只/月" % m["median_members_covered"])
    print("  ★ 结论：%s" % doc["verdict"])
    for r in doc["verdict_reasons"]:
        print("     - %s" % r)
    if a.write:
        io.open(out, "w", encoding="utf-8", newline="\n").write(body)
        print("  已写 %s" % os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
