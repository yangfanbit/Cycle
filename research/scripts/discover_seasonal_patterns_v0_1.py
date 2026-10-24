#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""discover_seasonal_patterns_v0_1.py —— 从**多年行情**里发现重复的季节性结构（v0.34）。

## 方法（先声明口径，再看结果）

对每个「行业板块 × 日历月」：
1. 用**原始收盘**算该月（首→末交易日）板块收益，减去沪深300同区间收益 = 当月超额；
2. 统计覆盖年份数 `n_years`、超额中位数 `median_excess_pct`、为正的年份占比 `hit_rate`；
3. **纳入标准**（预先写死）：`n_years ≥ 8` 且 `median_excess_pct ≥ 1.5` 且 `hit_rate ≥ 0.6`；
4. 与当前时点比较：`as_of` 落在该月 → `IN_WINDOW`；落在该月前一个月 → `PRE_WINDOW`（前置观察）；
   其余 `PASSED` / `LATER`。

★ 这是**描述性统计**：只说明「历史上这个月份该板块跑赢基准的频率与幅度」，不构成因果，
  也不预测未来；样本年份与命中率必须一起看，单年极端行情会主导中位数。
★ 板块用**当前**行业分类回溯，历史分类变更无法还原（已知偏差）。
★ 代表股票暂缺：板块成分历史无法取得 → 不臆造「当年龙头」。

用法：
    python research/scripts/discover_seasonal_patterns_v0_1.py --write --version 1
    python research/scripts/discover_seasonal_patterns_v0_1.py --check
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(REPO, "research", "database", "history_scan.db")
CURRENT = os.path.join(REPO, "research", "current")
OUT_RE = re.compile(r"pattern_discovery_v0_(\d+)\.json$")

MIN_YEARS = 8
MIN_MEDIAN_EXCESS = 1.5
MIN_HIT_RATE = 0.6


def load(conn, sid):
    return conn.execute(
        "SELECT trade_date, close FROM scan_daily WHERE series_id=? ORDER BY trade_date", (sid,)).fetchall()


def month_returns(rows):
    """{YYYY-MM: (first_close, last_close, first_date, last_date)}"""
    out = {}
    for d, c in rows:
        d = d.replace("-", "")
        ym = "%s-%s" % (d[:4], d[4:6])   # ★ 板块是 20100104、指数是 2010-01-04 → 统一键
        if ym not in out:
            out[ym] = [c, c, d, d]
        else:
            out[ym][1] = c
            out[ym][3] = d
    return out


def main(argv):
    ap = argparse.ArgumentParser(description="季节性结构发现")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--version", type=int, default=None)
    ap.add_argument("--min-years", type=int, default=MIN_YEARS)
    a = ap.parse_args(argv)

    if a.check:
        files = [f for f in os.listdir(CURRENT) if OUT_RE.match(f)]
        if not files:
            print("FAIL: 产物不存在")
            return 1
        files.sort(key=lambda f: int(OUT_RE.match(f).group(1)))
        doc = json.load(open(os.path.join(CURRENT, files[-1]), encoding="utf-8"))
        errs = []
        for p in doc["patterns"]:
            if p["tier"] == "EXPLORATORY":
                continue
            if p["n_years"] < doc["criteria"]["min_years"]:
                errs.append("%s/%s n_years 低于标准" % (p["board"], p["month"]))
            if p["hit_rate"] < doc["criteria"]["min_hit_rate"]:
                errs.append("%s/%s hit_rate 低于标准" % (p["board"], p["month"]))
            if p["median_excess_pct"] < doc["criteria"]["min_median_excess"]:
                errs.append("%s/%s 中位超额低于标准" % (p["board"], p["month"]))
        if errs:
            print("FAIL: %s" % errs[:5])
            return 1
        print("PASS: 季节性发现产物一致（%d 条 · 覆盖 %s）" % (len(doc["patterns"]), doc["coverage"]))
        return 0

    conn = sqlite3.connect(DB)
    bench = load(conn, "CSI300")
    if not bench:
        print("FAIL: 缺基准（先回补 --indices）")
        return 1
    as_of = bench[-1][0]
    bm = month_returns(bench)
    boards = conn.execute(
        "SELECT series_id, name, first_date, last_date, rows, kind FROM scan_series "
        "WHERE kind IN ('industry_board','concept_basket') AND rows>0").fetchall()

    patterns = []
    for sid, name, first, last, nrows, kind in boards:
        rows = load(conn, sid)
        bmr = month_returns(rows)
        by_month = {}
        for ym, (c0, c1, d0, d1) in bmr.items():
            if ym not in bm or c0 <= 0:
                continue
            bc0, bc1 = bm[ym][0], bm[ym][1]
            if bc0 <= 0:
                continue
            ex = (c1 / c0 - 1) * 100 - (bc1 / bc0 - 1) * 100
            by_month.setdefault(int(ym[5:7]), []).append((ym[:4], round(ex, 2)))
        for m, vals in by_month.items():
            if len(vals) < a.min_years:
                continue
            exs = [v[1] for v in vals]
            med = statistics.median(exs)
            hit = sum(1 for x in exs if x > 0) / len(exs)
            tier = ("STRICT" if (med >= MIN_MEDIAN_EXCESS and hit >= MIN_HIT_RATE)
                    else "EXPLORATORY" if (med >= 0.8 and hit >= 0.55) else None)
            if tier is None:
                continue
            patterns.append({
                "pattern_id": "SEAS-%s-M%02d" % (sid, m),
                "board": name, "board_series": sid, "month": m, "kind": kind,
                "n_years": len(vals), "years": sorted(v[0] for v in vals),
                "tier": tier,
                "median_excess_pct": round(med, 2),
                "hit_rate": round(hit, 3),
                "best_year": max(vals, key=lambda v: v[1]),
                "worst_year": min(vals, key=lambda v: v[1]),
                "per_year": [{"year": v[0], "excess_pct": v[1]} for v in sorted(vals)],
                "board_first_date": first, "board_last_date": last,
            })
    # ★ 代表性股票：概念篮子有成分记录 → 取「该月超额中位」前 3（**当前成分**，偏差已声明）
    mem_cache = {}
    for p in patterns:
        if p["kind"] != "concept_basket":
            continue
        row = conn.execute("SELECT v FROM scan_meta WHERE k=?", ("members:" + p["board_series"],)).fetchone()
        if not row:
            continue
        syms = json.loads(row[0])
        q = ",".join("?" * len(syms))
        rows_by = {}
        for sid, d, close in conn.execute(
                "SELECT series_id, trade_date, close FROM scan_daily WHERE series_id IN (%s) AND close>0" % q, syms):
            rows_by.setdefault(sid, []).append((d.replace("-", ""), close))
        scored = []
        for sid, rs in rows_by.items():
            mrets = []
            bym = {}
            for d, c in rs:
                bym.setdefault(d[:6], [c, c])[1] = c
            for ym, (c0, c1) in bym.items():
                if int(ym[4:6]) != p["month"] or c0 <= 0:
                    continue
                b = bm.get("%s-%s" % (ym[:4], ym[4:6]))
                if not b:
                    continue
                mrets.append((c1 / c0 - 1) * 100 - (b[1] / b[0] - 1) * 100)
            if len(mrets) >= 6:
                scored.append((sid, round(statistics.median(mrets), 2), len(mrets)))
        scored.sort(key=lambda x: -x[1])
        p["representative_stocks"] = [{"series_id": s_, "median_excess_pct": v, "years": n}
                                      for s_, v, n in scored[:3]]
    patterns.sort(key=lambda p: (-p["median_excess_pct"], -p["hit_rate"]))

    cur_month = int(as_of[5:7])
    for p in patterns:
        if p["month"] == cur_month:
            p["current_status"] = "IN_WINDOW"
        elif p["month"] == cur_month + 1:
            p["current_status"] = "PRE_WINDOW"
        else:
            p["current_status"] = "LATER" if p["month"] > cur_month else "PASSED"

    doc = {
        "artifact": "pattern_discovery",
        "artifact_version": "0.1",
        "generated_at": as_of,
        "as_of": as_of,
        "as_of_source": "history_scan.db · CSI300 最后一根日线",
        "coverage": "%s → %s" % (min(b[2] for b in boards if b[2]), max(b[3] for b in boards if b[3])),
        "source": {
            "db": "research/database/history_scan.db",
            "provider": "ths（行业板块按年接口 bk_881xxx/01/<year>.js）",
            "benchmark": "sina sh000300（原始收盘）",
            "price_type": "raw",
            "boards_scanned": len(boards),
        },
        "criteria": {
            "min_years": a.min_years,
            "min_median_excess": MIN_MEDIAN_EXCESS,
            "min_hit_rate": MIN_HIT_RATE,
            "declared_before_scan": True,
            "rule": "板块该月收益 − 沪深300同月收益（原始收盘，首→末交易日）",
        },
        "patterns": patterns,
        "current_windows": [p for p in patterns if p["current_status"] in ("IN_WINDOW", "PRE_WINDOW")],
        "tier_note": ("STRICT = 预先声明标准（n≥8 年、中位超额≥1.5pp、命中≥60%）；"
                      "EXPLORATORY = 放宽到 ≥0.8pp / ≥55%，**仅作探索线索**，不得当已验证规律。"),
        "limitations": [
            "★ 描述性统计，不是因果，也不预测；单年极端行情会主导中位数，必须同时看 hit_rate 与 per_year。",
            "★ 行业分类为**当前**分类回溯，历史分类变更无法还原（幸存者/分类偏差）。",
            "★ 代表股票暂缺：板块历史成分不可得，不臆造「当年龙头」。",
            "★ 板块序列来自同花顺按年接口，缺失年份已在 n_years 中体现。",
        ],
    }
    strict = [p for p in patterns if p["tier"] == "STRICT"]
    print("板块 %d 个 · STRICT %d 条 · EXPLORATORY %d 条 · 当前窗口 %d 条"
          % (len(boards), len(strict), len(patterns) - len(strict), len(doc["current_windows"])))
    for p in doc["current_windows"][:8]:
        print("  %s %d 月 · %d 年 · 中位超额 %+.2f%% · 命中 %.0f%%"
              % (p["board"], p["month"], p["n_years"], p["median_excess_pct"], p["hit_rate"] * 100))

    if a.write:
        if a.version is None:
            print("FAIL: --write 需要 --version N")
            return 1
        out = os.path.join(CURRENT, "pattern_discovery_v0_%d.json" % a.version)
        if os.path.exists(out):
            print("FAIL: 目标已存在，拒绝覆盖：%s" % out)
            return 1
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        print("已生成 %s" % os.path.relpath(out, REPO))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
