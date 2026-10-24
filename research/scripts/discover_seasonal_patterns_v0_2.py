#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""discover_seasonal_patterns_v0_2.py —— 季节性结构发现 + 样本外检验（v0.35）。

口径（先声明再计算）：
- 交易日边界统一取**基准**（沪深300）当月首/末交易日；序列两端都要有收盘，否则该月跳过；
- 月度持有收益 = 末收/首收 − 1；超额 = 序列月收益 − 基准同区间；
- 样本内：n≥8 年、中位超额≥1.5pp、命中≥60% → STRICT；放宽 ≥0.8/55% → EXPLORATORY；
- 样本外：对每个检验年 Y，只用 Y 之前的年份（≥5）判断是否达标，再看 Y 实际超额；
  检验年数 <5 标 INSUFFICIENT_OOS；
- 自建概念指数是**合成序列**（当前成分等权，成交量恒 0）；行业板块无历史成分 → 不绑个股。
"""
from __future__ import annotations

import argparse, json, os, re, sqlite3, statistics, sys, time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(REPO, "research", "database", "history_scan.db")
CURRENT = os.path.join(REPO, "research", "current")
OUT_RE = re.compile(r"pattern_discovery_v0_(\d+)\.json$")

MIN_YEARS, MIN_MEDIAN, MIN_HIT = 8, 1.5, 0.6
EXP_MEDIAN, EXP_HIT = 0.8, 0.55
MIN_TRAIN_YEARS, MIN_OOS_TESTS, MIN_STOCK_YEARS = 5, 5, 6


def norm(d):
    return str(d).replace("-", "")


def load(conn, sid):
    return [(norm(d), c) for d, c in conn.execute(
        "SELECT trade_date, close FROM scan_daily WHERE series_id=? ORDER BY trade_date", (sid,)) if c and c > 0]


def month_bounds(bench):
    out = {}
    for d, _ in bench:
        ym = d[:6]
        if ym not in out:
            out[ym] = [d, d]
        else:
            out[ym][1] = d
    return out


def month_returns(series, bounds):
    m = dict(series)
    out = {}
    for ym, (d0, d1) in bounds.items():
        if d0 in m and d1 in m and d0 != d1:
            out[ym] = (m[d1] / m[d0] - 1) * 100
    return out


def judge(vals):
    if len(vals) < MIN_YEARS:
        return None
    exs = [v for _, v in vals]
    med, hit = statistics.median(exs), sum(1 for x in exs if x > 0) / len(exs)
    if med >= MIN_MEDIAN and hit >= MIN_HIT:
        tier = "STRICT"
    elif med >= EXP_MEDIAN and hit >= EXP_HIT:
        tier = "EXPLORATORY"
    else:
        return None
    return {"tier": tier, "n_years": len(vals), "median": med, "hit": hit}


def walk_forward(vals):
    vals = sorted(vals)
    tests = []
    for i, (y, ex) in enumerate(vals):
        train = vals[:i]
        if len(train) < MIN_TRAIN_YEARS or judge(train) is None:
            continue
        tests.append({"year": y, "excess_pct": round(ex, 2), "hit": ex > 0})
    if not tests:
        return {"oos_tests": 0, "oos_status": "INSUFFICIENT_OOS", "oos_note": "没有可检验年份"}
    hit = sum(1 for t in tests if t["hit"]) / len(tests)
    med = statistics.median([t["excess_pct"] for t in tests])
    return {"oos_tests": len(tests), "oos_hit_rate": round(hit, 3),
            "oos_median_excess_pct": round(med, 2),
            "oos_years": [str(t["year"]) for t in tests],
            "oos_status": "REPORTED" if len(tests) >= MIN_OOS_TESTS else "INSUFFICIENT_OOS",
            "oos_note": None if len(tests) >= MIN_OOS_TESTS else "检验年数 < %d，不作结论" % MIN_OOS_TESTS}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--version", type=int, default=None)
    a = ap.parse_args(argv)

    if a.check:
        files = sorted([f for f in os.listdir(CURRENT) if OUT_RE.match(f)],
                       key=lambda f: int(OUT_RE.match(f).group(1)))
        if not files:
            print("FAIL: 产物不存在"); return 1
        path = os.path.join(CURRENT, files[-1])
        doc = json.load(open(path, encoding="utf-8"))
        errs, c = [], doc.get("criteria") or {}
        for p in doc["patterns"]:
            if p["tier"] == "STRICT" and (p["n_years"] < c["min_years"]
                                          or p["median_excess_pct"] < c["min_median_excess"]
                                          or p["hit_rate"] < c["min_hit_rate"]):
                errs.append("%s 不满足 STRICT" % p["pattern_id"])
            if "oos_status" not in p:
                errs.append("%s 缺 OOS 状态" % p["pattern_id"])
            if p.get("oos_status") == "REPORTED" and p["oos_tests"] < c["min_oos_tests"]:
                errs.append("%s OOS 年数不足却报告" % p["pattern_id"])
        for key in ("stocks", "industry_boards", "concept_baskets"):
            if key not in (doc.get("coverage_detail") or {}):
                errs.append("缺 %s 覆盖" % key)
        if errs:
            print("FAIL: %s" % errs[:5]); return 1
        print("PASS: 季节性产物一致（%s · %d 条 · OOS 报告 %d 条）"
              % (os.path.basename(path), len(doc["patterns"]),
                 sum(1 for p in doc["patterns"] if p.get("oos_status") == "REPORTED")))
        return 0

    conn = sqlite3.connect(DB)
    bench = load(conn, "CSI300")
    if not bench:
        print("FAIL: 缺基准"); return 1
    as_of = bench[-1][0]
    bounds = month_bounds(bench)
    bench_ret = month_returns(bench, bounds)
    series_rows = conn.execute(
        "SELECT series_id, name, kind, first_date, last_date, rows FROM scan_series "
        "WHERE kind IN ('industry_board','concept_basket') AND rows>0").fetchall()

    patterns = []
    for sid, name, kind, first, last, nrows in series_rows:
        mr = month_returns(load(conn, sid), bounds)
        by_month = {}
        for ym, ret in mr.items():
            if ym in bench_ret:
                by_month.setdefault(int(ym[4:6]), []).append((int(ym[:4]), ret - bench_ret[ym]))
        for m, vals in by_month.items():
            j = judge(vals)
            if not j:
                continue
            patterns.append({
                "pattern_id": "SEAS-%s-M%02d" % (sid, m), "board": name, "board_series": sid,
                "kind": kind, "month": m, "tier": j["tier"], "n_years": j["n_years"],
                "years": sorted(str(y) for y, _ in vals),
                "median_excess_pct": round(j["median"], 2), "hit_rate": round(j["hit"], 3),
                "best_year": {"year": str(max(vals, key=lambda v: v[1])[0]),
                              "excess_pct": round(max(vals, key=lambda v: v[1])[1], 2)},
                "worst_year": {"year": str(min(vals, key=lambda v: v[1])[0]),
                               "excess_pct": round(min(vals, key=lambda v: v[1])[1], 2)},
                "per_year": [{"year": str(y), "excess_pct": round(e, 2)} for y, e in sorted(vals)],
                **walk_forward(vals),
            })

    for p in patterns:
        if p["kind"] != "concept_basket":
            continue
        row = conn.execute("SELECT v FROM scan_meta WHERE k=?", ("members:" + p["board_series"],)).fetchone()
        if not row:
            continue
        syms = json.loads(row[0])
        q = ",".join("?" * len(syms))
        by_sym = {}
        for sid, d, close in conn.execute(
                "SELECT series_id, trade_date, close FROM scan_daily WHERE series_id IN (%s) AND close>0" % q, syms):
            by_sym.setdefault(sid, []).append((norm(d), close))
        scored = []
        for sid, rs in by_sym.items():
            mr = month_returns(rs, bounds)
            exs = [ret - bench_ret[ym] for ym, ret in mr.items()
                   if ym in bench_ret and int(ym[4:6]) == p["month"]]
            if len(exs) >= MIN_STOCK_YEARS:
                scored.append((sid, round(statistics.median(exs), 2), len(exs)))
        scored.sort(key=lambda x: -x[1])
        p["representative_stocks"] = [
            {"series_id": s_, "median_excess_pct": v, "years": n,
             "source": "当前概念成分 + 基准日历对齐"} for s_, v, n in scored[:3]]
        if not scored:
            p["rep_stock_gap"] = "成分内没有 ≥%d 年可比样本的个股" % MIN_STOCK_YEARS

    patterns.sort(key=lambda p: (-p["median_excess_pct"], -p["hit_rate"]))
    cur = int(as_of[4:6])
    for p in patterns:
        p["current_status"] = ("IN_WINDOW" if p["month"] == cur
                               else "PRE_WINDOW" if p["month"] == cur + 1
                               else "LATER" if p["month"] > cur else "PASSED")

    def cov(kind):
        n, rows, f, l = conn.execute(
            "SELECT COUNT(*), SUM(rows), MIN(first_date), MAX(last_date) FROM scan_series "
            "WHERE kind=? AND rows>0", (kind,)).fetchone()
        return {"series": n or 0, "rows": rows or 0,
                "first_date": norm(f) if f else None, "last_date": norm(l) if l else None}

    doc = {
        "artifact": "pattern_discovery", "artifact_version": "0.5",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "as_of": as_of,
        "as_of_source": "history_scan.db · CSI300 最后一根日线（原始收盘）",
        "coverage_detail": {"stocks": cov("stock"), "industry_boards": cov("industry_board"),
                            "concept_baskets": cov("concept_basket"), "indices": cov("index")},
        "criteria": {
            "min_years": MIN_YEARS, "min_median_excess": MIN_MEDIAN, "min_hit_rate": MIN_HIT,
            "exploratory": {"min_median_excess": EXP_MEDIAN, "min_hit_rate": EXP_HIT},
            "min_train_years": MIN_TRAIN_YEARS, "min_oos_tests": MIN_OOS_TESTS,
            "month_boundary": "基准（沪深300）当月首/末交易日；序列两端都要有收盘",
            "rule": "月度持有收益 = 末收/首收−1；超额 = 序列 − 基准同区间",
        },
        "source": {
            "db": "research/database/history_scan.db",
            "industry_boards": "同花顺 bk_881xxx / bk_884xxx 按年接口（原始收盘）",
            "concept_baskets": "自建等权：新浪**当前**概念成分 + 全市场个股日线合成（成交量字段恒 0）",
            "benchmark": "新浪 sh000300（原始收盘）", "price_type": "raw",
        },
        "patterns": patterns,
        "current_windows": [p for p in patterns if p["current_status"] in ("IN_WINDOW", "PRE_WINDOW")],
        "tier_note": ("STRICT = 预先声明标准（n≥8 年、中位≥1.5pp、命中≥60%）；EXPLORATORY = 放宽 ≥0.8/55%。"
                      "**样本内通过 ≠ 已验证规律**，请看 oos_* 字段。"),
        "limitations": [
            "★ 自建概念指数是**合成研究序列**（当前成分等权、成交量无意义），不等于官方概念指数。",
            "★ 行业板块**没有历史成分** → 不绑定个股；概念代表股票来自**当前成分**，不是当年龙头。",
            "★ 板块/概念均为**当前**分类回溯，历史变更无法还原。",
            "★ 样本外检验按年份滚动；检验年数 <5 标 INSUFFICIENT_OOS，不作结论。",
            "★ 退市股不在库内 → 早期年份存在幸存者偏差。",
        ],
    }

    strict = [p for p in patterns if p["tier"] == "STRICT"]
    oos_rep = [p for p in patterns if p.get("oos_status") == "REPORTED"]
    print("序列 %d · STRICT %d · 探索 %d · 窗口 %d · OOS 可报告 %d"
          % (len(series_rows), len(strict), len(patterns) - len(strict),
             len(doc["current_windows"]), len(oos_rep)))
    for p in [x for x in doc["current_windows"] if x["tier"] == "STRICT"][:6]:
        print("  %s %d月 · %d年 · 中位%+.2f%% · 命中%.0f%% · OOS %s(%s)"
              % (p["board"], p["month"], p["n_years"], p["median_excess_pct"],
                 p["hit_rate"] * 100, p.get("oos_hit_rate"), p.get("oos_status")))

    if a.write:
        if a.version is None:
            print("FAIL: --write 需要 --version N"); return 1
        out = os.path.join(CURRENT, "pattern_discovery_v0_%d.json" % a.version)
        if os.path.exists(out):
            print("FAIL: 目标已存在：%s" % out); return 1
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        print("已生成 %s" % os.path.relpath(out, REPO))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
