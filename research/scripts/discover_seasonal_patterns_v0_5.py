#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""discover_seasonal_patterns_v0_5.py —— 季节性发现：双层时点资格 + 扫描口径自洽 + 校验补齐（v0.42）。

## 相对 v0_4 的修正（校验与审计口径）
- ★ A1：`--check` 补 `criteria.exploratory.min_hit_rate`；结构检查覆盖 STRICT / EXPLORATORY /
  INSUFFICIENT_HISTORY / OOS 不足四类；`oos_by_train_tier` 分项加总必须等于 `oos_tests`；
  `pit_only_patterns` 也要做 OOS 状态与检验次数检查（不只是字段存在）。
- ★ A2：`scan_audit` 改为**互斥分组**（<6 / 6–7 / ≥8 年；有资格 / 无资格；有资格内 <8 / ≥8），
  并新增 `records` 与 `reconcile` 自洽断言（分组加总 == 记录数 == 产物数）。
  旧字段 `pairs_history_lt_8` 实际只含 6–7 年，名字误导，已废弃。
- ★ A3：`--check` 的源数据核对范围**明确写清**：这是「窗口指标核对」（n_years / 中位 / 命中 /
  tier / 时点资格 / OOS 次数与分层），不是完整产物逐字节复现；无库时显式 SKIP。
- 新增跨块对账：`bias_audit.new_method.tests` == 产物检验数合计 == `oos_summary.combined.tests`
  == `by_year` 合计 == 两层分项之和。


## 相对 v0_3 的修正（口径审计后）
1. ★★ **资格规则是双层的，v0_3 的声明写错了**：v0_2 与 v0_3 的 `walk_forward` 都用
   `tier_of(train) is not None` 判定资格，而 `tier_of` 会返回 STRICT **或** EXPLORATORY
   → 实际是**两层都算通过**。v0_3 的 `criteria.training_rule` 只写了 STRICT 阈值（≥1.5pp/60%），
   属**声明与行为不符**。本版以可核验代码行为为准：**保留双层**，并把声明、逐年记录、汇总一起改对。
2. ★★ **历史门槛与检验门槛分离**：v0_3 在 `len(vals) < 8` 时**直接跳过滚动检验**，
   导致只有 6–7 年、但曾在 5 年训练后取得资格的序列被漏掉（实测新增 190 个）。
   本版：只要有 ≥5 年训练 + ≥1 个后续检验年就做时点检验；<8 年**不计算**历史等级，
   记 `INSUFFICIENT_HISTORY` 并单独留存。
3. ★★ **综合统计必须可解释**：同时给出 `oos_by_train_tier`（STRICT / EXPLORATORY 分项），
   顶层 `oos_*` 是**两层合并**并显式声明包含哪些层级。
4. ★ **措辞**：`pit_eligible_years` 只表示「按当前可用序列、只用过去数据取得的**统计**资格」，
   **不等于**当时的分类/成分/研究机会都在当时可得 → 用户可见文案改为「历史序列时点资格」。

## 时点检验协议（先声明，再看结果；阈值不随结果调整）
- 历史描述（L1）：全样本 ≥8 年才给 STRICT / EXPLORATORY；不足 8 年 → `INSUFFICIENT_HISTORY`。
- 滚动资格（L2）：每个检验年 Y 只用 **Y 之前**的年份；训练年数 ≥5；
  训练集 **STRICT**（中位≥1.5pp 且命中≥60%）或 **EXPLORATORY**（中位≥0.8pp 且命中≥55%）→ 该年具资格。
- 时点结论（L3）：`oos_tests ≥5` 才 REPORTED，否则 INSUFFICIENT_OOS；不补造、不用样本内替代。

## 三层口径（不得混用）
① 历史统计 `in_sample` ② 滚动检验 `walk_forward_detail` / `walk_forward_audit`
③ 时点结论 `oos_*` / `evidence_grade`。**历史命中率不是未来成功概率。**

## 仍无法消除的偏差（写入产物 limitations）
概念篮子是**当前成分**合成、分类为**当前**回溯、退市股缺失 → walk-forward 只能约束「用没用未来数据」，
**不能**把这些偏差消掉。
"""
from __future__ import annotations

import argparse, json, os, re, sqlite3, statistics, sys, time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(REPO, "research", "database", "history_scan.db")
CURRENT = os.path.join(REPO, "research", "current")
OUT_RE = re.compile(r"pattern_discovery_v0_(\d+)\.json$")

MIN_YEARS, MIN_MEDIAN, MIN_HIT = 8, 1.5, 0.6          # 历史描述门槛（L1）
EXP_MEDIAN, EXP_HIT = 0.8, 0.55                        # EXPLORATORY 阈值
MIN_TRAIN_YEARS, MIN_OOS_TESTS, MIN_STOCK_YEARS = 5, 5, 6
MIN_TOTAL_YEARS_FOR_TEST = MIN_TRAIN_YEARS + 1          # ≥5 训练 + ≥1 检验
PROTOCOL = "seasonal_walk_forward_pit_v2"  # 方法未变；本版只改校验与审计口径
TIER_INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"


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


def tier_of(vals, min_years):
    """双层判定：STRICT / EXPLORATORY / None。阈值**预先声明**，不随结果调整。"""
    if len(vals) < min_years:
        return None
    exs = [v for _, v in vals]
    med, hit = statistics.median(exs), sum(1 for x in exs if x > 0) / len(exs)
    if med >= MIN_MEDIAN and hit >= MIN_HIT:
        return "STRICT"
    if med >= EXP_MEDIAN and hit >= EXP_HIT:
        return "EXPLORATORY"
    return None


def walk_forward(vals):
    """逐年滚动：资格只用该年之前的年份。返回 (records, eligible_tests)。

    每条记录含：训练年数 / 训练区间 / 训练层级 / 是否具资格 / 测试结果 / 未通过原因。
    """
    vals = sorted(vals)
    recs, elig = [], []
    for i, (y, ex) in enumerate(vals):
        train = vals[:i]
        r = {"year": str(y), "n_train": len(train)}
        if len(train) < MIN_TRAIN_YEARS:
            r.update(testable=False, eligible=False, reason="TRAIN_YEARS_TOO_FEW")
        else:
            tr_tier = tier_of(train, MIN_TRAIN_YEARS)
            r.update(testable=True, eligible=tr_tier is not None, train_tier=tr_tier,
                     train_window=("%s~%s" % (train[0][0], train[-1][0])) if train else None,
                     reason="ELIGIBLE" if tr_tier else "TRAIN_CRITERIA_NOT_MET")
            if tr_tier:
                r.update(test_excess_pct=round(ex, 2), test_hit=ex > 0)
                elig.append({"year": y, "excess_pct": round(ex, 2), "hit": ex > 0,
                             "train_tier": tr_tier})
        recs.append(r)
    return recs, elig


def _stat(tests):
    if not tests:
        return {"tests": 0, "hit_rate": None, "median_excess_pct": None}
    return {"tests": len(tests),
            "hit_rate": round(sum(1 for t in tests if t["hit"]) / len(tests), 3),
            "median_excess_pct": round(statistics.median([t["excess_pct"] for t in tests]), 2)}


def summarise(elig):
    """顶层 oos_* = **两层合并**；分项见 oos_by_train_tier（避免把两类混成无法解释的一个数）。"""
    if not elig:
        return {"oos_tests": 0, "oos_status": "INSUFFICIENT_OOS",
                "oos_note": "没有任何年份在「仅用之前年份」的条件下取得检验资格",
                "oos_by_train_tier": {"STRICT": _stat([]), "EXPLORATORY": _stat([])}}
    allst = _stat(elig)
    by = {}
    for t in ("STRICT", "EXPLORATORY"):
        sub = [e for e in elig if e["train_tier"] == t]
        by[t] = _stat(sub)
        by[t]["status"] = ("REPORTED" if len(sub) >= MIN_OOS_TESTS
                           else "INSUFFICIENT_OOS" if sub else "NO_TEST")
    return {
        "oos_tests": allst["tests"],
        "oos_hit_rate": allst["hit_rate"],
        "oos_median_excess_pct": allst["median_excess_pct"],
        "oos_years": [str(t["year"]) for t in elig],
        "oos_status": "REPORTED" if allst["tests"] >= MIN_OOS_TESTS else "INSUFFICIENT_OOS",
        "oos_note": (None if allst["tests"] >= MIN_OOS_TESTS
                     else "检验年数 < %d，不作结论" % MIN_OOS_TESTS),
        "oos_by_train_tier": by,
        "oos_scope": "COMBINED_STRICT_AND_EXPLORATORY",
    }


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--version", type=int, default=None)
    a = ap.parse_args(argv)

    # ★ CI 不携带 history_scan.db（1.3GB、不入库）→ --check 只能做结构校验，
    #   源数据核对显式 SKIP（不静默假装核对过）。
    if a.check and not os.path.exists(DB):
        return check(None, None, None, None)

    conn = sqlite3.connect(DB)
    bench = load(conn, "CSI300")
    if not bench:
        print("FAIL: 缺基准"); return 1
    as_of = bench[-1][0]
    bounds = month_bounds(bench)
    cur_ym = as_of[:6]
    bounds_hist = {ym: v for ym, v in bounds.items() if ym < cur_ym}
    bench_ret = month_returns(bench, bounds_hist)

    if a.check:
        return check(conn, as_of, bounds_hist, bench_ret)
    series_rows = conn.execute(
        "SELECT series_id, name, kind, first_date, last_date, rows FROM scan_series "
        "WHERE kind IN ('industry_board','concept_basket') AND rows>0 AND status='OK'").fetchall()

    patterns, pit_only, raw_vals = [], [], {}
    audit = {}
    old_tests, new_tests, hidden_tests = [], [], []
    # ★ 扫描口径：**互斥分组**，每组可加总复核（旧版 pairs_history_lt_8 实际只含 6–7 年，名字误导）
    scan = {"series": len(series_rows), "pairs_scanned": 0, "pairs_with_data": 0,
            "years_group": {"lt_6": 0, "6_to_7": 0, "ge_8": 0},
            "eligibility_group": {"pit_eligible": 0, "never_eligible": 0},
            "pit_eligible_detail": {"history_lt_8": 0, "history_ge_8": 0},
            "history_group": {"strict": 0, "exploratory": 0, "below_threshold": 0}}

    for sid, name, kind, first, last, nrows in series_rows:
        mr = month_returns(load(conn, sid), bounds_hist)
        by_month = {}
        for ym, ret in mr.items():
            if ym in bench_ret:
                by_month.setdefault(int(ym[4:6]), []).append((int(ym[:4]), ret - bench_ret[ym]))
        scan["pairs_scanned"] += 12
        for m, vals in by_month.items():
            scan["pairs_with_data"] += 1
            n = len(vals)
            if n < MIN_TOTAL_YEARS_FOR_TEST:
                # 连「5 年训练 + 1 个检验年」都凑不出 → 不做时点检验
                scan["years_group"]["lt_6"] += 1
                continue
            scan["years_group"]["6_to_7" if n < MIN_YEARS else "ge_8"] += 1
            hist_tier = tier_of(vals, MIN_YEARS) if n >= MIN_YEARS else None
            if hist_tier == "STRICT":
                scan["history_group"]["strict"] += 1
            elif hist_tier == "EXPLORATORY":
                scan["history_group"]["exploratory"] += 1
            elif n >= MIN_YEARS:
                scan["history_group"]["below_threshold"] += 1

            recs, elig = walk_forward(vals)
            pit_years = [t["year"] for t in elig]
            if pit_years:
                scan["eligibility_group"]["pit_eligible"] += 1
                scan["pit_eligible_detail"]["history_lt_8" if n < MIN_YEARS else "history_ge_8"] += 1
            else:
                scan["eligibility_group"]["never_eligible"] += 1

            pid = "SEAS-%s-M%02d" % (sid, m)
            raw_vals[pid] = list(vals)
            oos = summarise(elig)
            exs = [v for _, v in vals]
            failures = {k: sum(1 for r in recs if r.get("reason") == k)
                        for k in ("TRAIN_YEARS_TOO_FEW", "TRAIN_CRITERIA_NOT_MET")}

            def audit_add():
                for r in recs:
                    b = audit.setdefault(r["year"], {"year": r["year"], "testable": 0, "eligible": 0,
                                                     "tested": 0, "hits": 0, "excess": [],
                                                     "by_train_tier": {"STRICT": 0, "EXPLORATORY": 0}})
                    if r.get("testable"):
                        b["testable"] += 1
                    if r.get("eligible"):
                        b["eligible"] += 1
                        b["tested"] += 1
                        b["hits"] += 1 if r.get("test_hit") else 0
                        b["excess"].append(r["test_excess_pct"])
                        b["by_train_tier"][r["train_tier"]] += 1

            if hist_tier is None:
                # 历史等级缺失：区分「样本不足 8 年」与「≥8 年但未达阈值」
                if not pit_years:
                    # 既无历史等级、也从未取得时点资格 → 不入库（只在 scan_audit 计数）
                    audit_add()
                    continue
                pit_only.append({
                    "pattern_id": pid, "board": name, "board_series": sid, "kind": kind, "month": m,
                    "n_years": n,
                    "median_excess_pct": round(statistics.median(exs), 2),
                    "hit_rate": round(sum(1 for x in exs if x > 0) / len(exs), 3),
                    "history_tier": TIER_INSUFFICIENT_HISTORY if n < MIN_YEARS else "BELOW_THRESHOLD",
                    "history_note": ("样本仅 %d 年（<8）→ 不计算历史等级" % n if n < MIN_YEARS
                                     else "样本 %d 年但未达 STRICT/EXPLORATORY 阈值" % n),
                    "pit_eligible_years": len(pit_years),
                    "pit_first_year": pit_years[0] if pit_years else None,
                    "pit_last_year": pit_years[-1] if pit_years else None,
                    "walk_forward_failures": failures,
                    **oos,
                    "note": ("历史样本不足，仅在「只用之前年份」的条件下曾具统计资格；"
                             "不代表当时分类/成分/研究机会可得"),
                })
                audit_add()
                new_tests.extend(elig)
                hidden_tests.extend(elig)
                continue

            basis = "POINT_IN_TIME" if pit_years else "FULL_SAMPLE_ONLY"
            grade = ("NOT_DISCOVERABLE_IN_TIME" if not pit_years
                     else "OOS_REPORTED" if oos["oos_status"] == "REPORTED" else "OOS_INSUFFICIENT")
            patterns.append({
                "pattern_id": pid, "board": name, "board_series": sid, "kind": kind, "month": m,
                "tier": hist_tier, "n_years": n,
                "years": sorted(str(y) for y, _ in vals),
                "median_excess_pct": round(statistics.median(exs), 2),
                "hit_rate": round(sum(1 for x in exs if x > 0) / len(exs), 3),
                "best_year": {"year": str(max(vals, key=lambda v: v[1])[0]),
                              "excess_pct": round(max(vals, key=lambda v: v[1])[1], 2)},
                "worst_year": {"year": str(min(vals, key=lambda v: v[1])[0]),
                               "excess_pct": round(min(vals, key=lambda v: v[1])[1], 2)},
                "per_year": [{"year": str(y), "excess_pct": round(e, 2)} for y, e in sorted(vals)],
                "pit_eligible_years": len(pit_years),
                "pit_first_year": pit_years[0] if pit_years else None,
                "pit_last_year": pit_years[-1] if pit_years else None,
                "pit_basis": "STATISTICAL_ON_CURRENT_SERIES",
                "discovery_basis": basis,
                "walk_forward_failures": failures,
                **oos,
                "evidence_grade": grade,
            })
            audit_add()
            new_tests.extend(elig)
            old_tests.extend(elig)      # 旧方法口径：历史等级达标者才进检验（本分支即达标者）

    # 代表股票：只对「历史等级达标」的概念模式计算（与 v0_2 口径一致）
    for p in patterns:
        if p["kind"] != "concept_basket":
            continue
        row = conn.execute("SELECT v FROM scan_meta WHERE k=?", ("members:" + p["board_series"],)).fetchone()
        if not row:
            continue
        syms = json.loads(row[0])
        q = ",".join("?" * len(syms))
        by_sym = {}
        for sid_, d, close in conn.execute(
                "SELECT series_id, trade_date, close FROM scan_daily WHERE series_id IN (%s) AND close>0" % q, syms):
            by_sym.setdefault(sid_, []).append((norm(d), close))
        scored = []
        for sid_, rs in by_sym.items():
            mr2 = month_returns(rs, bounds_hist)
            exs2 = [ret - bench_ret[ym] for ym, ret in mr2.items()
                    if ym in bench_ret and int(ym[4:6]) == p["month"]]
            if len(exs2) >= MIN_STOCK_YEARS:
                scored.append((sid_, round(statistics.median(exs2), 2), len(exs2)))
        scored.sort(key=lambda x: -x[1])
        name_map = {}
        for s_, _v, _n in scored[:3]:
            row_n = conn.execute("SELECT name FROM scan_series WHERE series_id=?", (s_,)).fetchone()
            name_map[s_] = (row_n[0] if row_n and row_n[0] else None)
        p["representative_stocks"] = [
            {"series_id": s_, "name": name_map.get(s_),
             "name_status": "RESOLVED" if name_map.get(s_) else "MISSING",
             "median_excess_pct": v, "years": n_, "source": "当前概念成分 + 基准日历对齐"}
            for s_, v, n_ in scored[:3]]
        if not scored:
            p["rep_stock_gap"] = "成分内没有 ≥%d 年可比样本的个股" % MIN_STOCK_YEARS

    patterns.sort(key=lambda p: (-p["median_excess_pct"], -p["hit_rate"]))
    cur = int(as_of[4:6])
    for p in patterns:
        p["current_status"] = ("IN_WINDOW" if p["month"] == cur
                               else "PRE_WINDOW" if p["month"] == cur + 1
                               else "LATER" if p["month"] > cur else "PASSED")

    windows = [p for p in patterns if p["current_status"] in ("IN_WINDOW", "PRE_WINDOW")]
    for p in windows:
        p["walk_forward_detail"] = walk_forward(raw_vals[p["pattern_id"]])[0]

    def cov(kind):
        n_, rows_, f, l = conn.execute(
            "SELECT COUNT(*), SUM(rows), MIN(first_date), MAX(last_date) FROM scan_series "
            "WHERE kind=? AND rows>0", (kind,)).fetchone()
        return {"series": n_ or 0, "rows": rows_ or 0,
                "first_date": norm(f) if f else None, "last_date": norm(l) if l else None}

    by_year = []
    for y in sorted(audit):
        b = audit[y]
        by_year.append({
            "year": y, "patterns_testable": b["testable"], "patterns_eligible": b["eligible"],
            "tests_run": b["tested"], "hits": b["hits"],
            "hit_rate": round(b["hits"] / b["tested"], 3) if b["tested"] else None,
            "median_excess_pct": round(statistics.median(b["excess"]), 2) if b["excess"] else None,
            "by_train_tier": b["by_train_tier"],
        })

    def agg(tests, label):
        s = _stat(tests)
        s["scope"] = label
        return s

    # ★ B3：pit_only 的规模与质量分层（决定「是否值得开独立探索入口」，不直接塞首页）
    def _hist_tier(k):
        return sum(1 for p in pit_only if p["history_tier"] == k)
    rep_pit = [p for p in pit_only if p.get("oos_status") == "REPORTED"]
    pit_summary = {
        "total": len(pit_only),
        "by_history_tier": {
            "INSUFFICIENT_HISTORY": _hist_tier(TIER_INSUFFICIENT_HISTORY),
            "BELOW_THRESHOLD": _hist_tier("BELOW_THRESHOLD"),
        },
        "oos_reportable": len(rep_pit),
        "oos_reportable_hit_rate": (round(sum(1 for p in rep_pit if (p.get("oos_hit_rate") or 0) >= 0.5)
                                          / len(rep_pit), 3) if rep_pit else None),
        "median_positive": sum(1 for p in pit_only if (p.get("median_excess_pct") or 0) > 0),
        "note": ("这些模式**只在时点上曾具资格**（全样本不达标或历史样本 <8 年），本轮**不进入首页**；"
                 "若要开独立探索入口，建议以 oos_reportable 且 median_positive 为最低门槛。"),
    }

    # ★ 扫描口径自洽：分组互斥、可加总，且与产物记录数对得上（--check 会逐条断言）
    scan["records"] = {
        "patterns": len(patterns),
        "patterns_point_in_time": sum(1 for p in patterns if p.get("pit_eligible_years")),
        "patterns_full_sample_only": sum(1 for p in patterns if not p.get("pit_eligible_years")),
        "pit_only": len(pit_only),
        "pit_only_insufficient_history": _hist_tier(TIER_INSUFFICIENT_HISTORY),
        "pit_only_below_threshold": _hist_tier("BELOW_THRESHOLD"),
    }
    yg, eg, pdet, hg, rc = (scan["years_group"], scan["eligibility_group"],
                            scan["pit_eligible_detail"], scan["history_group"], scan["records"])
    scan["reconcile"] = {
        "years_group_sums_to_with_data": yg["lt_6"] + yg["6_to_7"] + yg["ge_8"] == scan["pairs_with_data"],
        "eligibility_sums_to_testable": (eg["pit_eligible"] + eg["never_eligible"]
                                         == scan["pairs_with_data"] - yg["lt_6"]),
        "pit_detail_sums_to_eligible": pdet["history_lt_8"] + pdet["history_ge_8"] == eg["pit_eligible"],
        "history_group_sums_to_ge_8": (hg["strict"] + hg["exploratory"] + hg["below_threshold"] == yg["ge_8"]),
        "patterns_equal_history_qualified": rc["patterns"] == hg["strict"] + hg["exploratory"],
        "pit_only_equal_eligible_minus_history_qualified": (
            rc["pit_only"] == eg["pit_eligible"] - rc["patterns_point_in_time"]),
        "total_pit_eligible_equal": rc["patterns_point_in_time"] + rc["pit_only"] == eg["pit_eligible"],
        "pit_only_splits": (rc["pit_only"] == rc["pit_only_insufficient_history"]
                            + rc["pit_only_below_threshold"]),
    }

    doc = {
        "artifact": "pattern_discovery", "artifact_version": "0.8",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "as_of": as_of,
        "protocol": PROTOCOL,
        "history_excludes_incomplete_month": True,
        "as_of_source": "history_scan.db · CSI300 最后一根日线（原始收盘）",
        "coverage_detail": {"stocks": cov("stock"), "industry_boards": cov("industry_board"),
                            "concept_baskets": cov("concept_basket"), "indices": cov("index")},
        "criteria": {
            "min_years": MIN_YEARS, "min_median_excess": MIN_MEDIAN, "min_hit_rate": MIN_HIT,
            "exploratory": {"min_median_excess": EXP_MEDIAN, "min_hit_rate": EXP_HIT},
            "min_train_years": MIN_TRAIN_YEARS, "min_oos_tests": MIN_OOS_TESTS,
            "min_total_years_for_test": MIN_TOTAL_YEARS_FOR_TEST,
            "in_sample_min_years": MIN_YEARS,
            "training_rule": ("每年资格只用该年之前的年份；训练年数 ≥5；训练集满足 "
                              "STRICT（中位≥1.5pp 且命中≥60%）**或** EXPLORATORY（中位≥0.8pp 且命中≥55%）"
                              "→ 该年具资格（双层，预先声明，不随结果调整）"),
            "history_rule": "历史等级（STRICT/EXPLORATORY）需要全样本 ≥8 年；不足 8 年记 INSUFFICIENT_HISTORY，不计算等级",
            "completed_months_only": True,
            "month_boundary": "基准（沪深300）当月首/末交易日；序列两端都要有收盘",
            "rule": "月度持有收益 = 末收/首收−1；超额 = 序列 − 基准同区间",
            "selection_rule": "模式是否进入产物 = 曾有时点资格 OR 历史等级达标；历史等级**不**决定谁被检验",
        },
        "reporting_layers": {
            "L1_historical_statistics": "in_sample（tier / n_years / median_excess_pct / hit_rate）：全样本历史描述，**不是**未来概率",
            "L2_rolling_tests": "walk_forward_detail / walk_forward_audit：逐年训练区间、训练层级、资格、测试结果与失败原因",
            "L3_point_in_time_conclusion": "oos_* + oos_by_train_tier + evidence_grade：仅在 oos_tests ≥ min_oos_tests 时给结论",
            "note": "三层不得混用；顶层 oos_* 为 STRICT 与 EXPLORATORY 两层训练的合并统计，分项见 oos_by_train_tier。",
        },
        "pit_semantics": {
            "field": "pit_eligible_years",
            "means": "按**当前可用序列**、只用该年之前的数据，训练集取得的**统计**检验资格年数",
            "does_not_mean": [
                "不等于当时的分类、成分、概念成员资格在研究时点已可得（分类为当前回溯）",
                "不等于当时存在可执行的研究机会或可交易标的",
                "不等于历史会重演，也不是未来成功概率",
            ],
            "ui_wording": "历史序列时点资格",
        },
        "scan_audit": scan,
        "bias_audit": {
            "what": "旧方法（v0_2）先按全样本判等级，只有达标者进入滚动检验 → 选择偏差（偏差在「谁进入检验」）。",
            "old_method": agg(old_tests, "ONLY_HISTORY_QUALIFIED"),
            "new_method": agg(new_tests, "ALL_PIT_ELIGIBLE"),
            "hidden_by_old_method": agg(hidden_tests, "HIDDEN_BY_OLD_METHOD"),
            "inflation": {
                "hit_rate_pp": (round((_stat(old_tests)["hit_rate"] or 0) * 100
                                      - (_stat(new_tests)["hit_rate"] or 0) * 100, 1)
                                if old_tests and new_tests else None),
                "median_excess_pp": (round(_stat(old_tests)["median_excess_pct"]
                                           - _stat(new_tests)["median_excess_pct"], 2)
                                     if old_tests and new_tests else None),
            },
            "note": "旧方法逐年训练逻辑本身没有泄漏；偏差只在「谁进入检验」这一层。数字随口径修正会变化，旧值仅作对照。",
        },
        "oos_summary": {
            "combined": agg(new_tests, "COMBINED_STRICT_AND_EXPLORATORY"),
            "by_train_tier": {
                "STRICT": agg([t for t in new_tests if t["train_tier"] == "STRICT"], "STRICT_TRAINED"),
                "EXPLORATORY": agg([t for t in new_tests if t["train_tier"] == "EXPLORATORY"],
                                   "EXPLORATORY_TRAINED"),
            },
            "note": ("combined 是**两层合并**（含 STRICT 训练与 EXPLORATORY 训练取得的资格年）；"
                     "两层表现差异见 by_train_tier —— 不得把合并值当成单一口径。"),
        },
        "walk_forward_audit": {
            "by_year": by_year,
            "note": ("patterns_testable = 该年有训练数据且训练年数达标的模式数；patterns_eligible = 训练集通过"
                     "STRICT 或 EXPLORATORY 的模式数；tests_run = 实际进入检验数（= eligible）；"
                     "by_train_tier = 该年具资格模式中训练层级为 STRICT / EXPLORATORY 的条数。"),
        },
        "source": {
            "db": "research/database/history_scan.db",
            "industry_boards": "同花顺 bk_881xxx / bk_884xxx 按年接口（原始收盘）",
            "concept_baskets": "自建等权：新浪**当前**概念成分 + 全市场个股日线合成（成交量字段恒 0）",
            "benchmark": "新浪 sh000300（原始收盘）", "price_type": "raw",
        },
        "patterns": patterns,
        "pit_only_patterns": pit_only,
        "pit_only_count": len(pit_only),
        "pit_only_summary": pit_summary,
        "current_windows": windows,
        "tier_note": ("STRICT/EXPLORATORY = 全样本历史描述（预先声明阈值）；"
                      "INSUFFICIENT_HISTORY = 历史样本 <8 年但曾在时点上具资格。"
                      "**样本内通过 ≠ 已验证规律**；请同时看 evidence_grade / oos_by_train_tier / pit_eligible_years。"),
        "limitations": [
            "★ 自建概念指数是**合成研究序列**（当前成分等权、成交量无意义），不等于官方概念指数。",
            "★ 概念成员与板块分类均为**当前**口径回溯，历史成分/分类变更无法还原 → walk-forward **不能**消除该偏差。",
            "★ 行业板块**没有历史成分** → 不绑定个股；概念代表股票来自**当前成分**，不是当年龙头。",
            "★ 退市股不在库内 → 早期年份存在幸存者偏差。",
            "★ 样本外检验按年份滚动；检验年数 <5 标 INSUFFICIENT_OOS，不作结论。",
            "★ pit_eligible_years 是**统计资格**，不等于当时可得的研究机会；discovery_basis = FULL_SAMPLE_ONLY 的模式在当年无法被发现。",
        ],
    }

    strict = [p for p in patterns if p["tier"] == "STRICT"]
    expl = [p for p in patterns if p["tier"] == "EXPLORATORY"]
    rep = [p for p in patterns if p.get("oos_status") == "REPORTED"]
    print("扫描 %d 组合 · 有数据 %d · 年限分组 <6=%d / 6–7=%d / ≥8=%d（合计 %d）"
          % (scan["pairs_scanned"], scan["pairs_with_data"],
             scan["years_group"]["lt_6"], scan["years_group"]["6_to_7"], scan["years_group"]["ge_8"],
             scan["years_group"]["lt_6"] + scan["years_group"]["6_to_7"] + scan["years_group"]["ge_8"]))
    print("资格分组 有资格 %d / 无资格 %d（合计 %d）· 有资格中 <8 年 %d"
          % (scan["eligibility_group"]["pit_eligible"], scan["eligibility_group"]["never_eligible"],
             scan["eligibility_group"]["pit_eligible"] + scan["eligibility_group"]["never_eligible"],
             scan["pit_eligible_detail"]["history_lt_8"]))
    print("自洽校验：%s" % ("全部通过" if all(scan["reconcile"].values())
                        else "FAIL %s" % [k for k, v in scan["reconcile"].items() if not v]))
    print("样本内达标 %d（STRICT %d / 探索 %d）· 仅时点资格 %d · 窗口 %d · OOS 可报告 %d"
          % (len(patterns), len(strict), len(expl), len(pit_only), len(windows), len(rep)))
    print("偏差对照：旧 %s vs 新 %s（被旧方法挡掉 %s）"
          % (agg(old_tests, "old"), agg(new_tests, "new"), agg(hidden_tests, "hidden")))

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


def _recompute_reconcile(sa, n_patterns, n_pit_only):
    """★ A1：按产物内的分组计数与**实际数组长度**重算全部 8 条自洽关系。

    返回 (relations, detail)：relations 与 `scan_audit.reconcile` 的键一一对应；
    detail 给出每条关系的实算数字，便于报错时定位（不是只给一个 false）。
    """
    yg = sa.get("years_group") or {}
    eg = sa.get("eligibility_group") or {}
    pd = sa.get("pit_eligible_detail") or {}
    hg = sa.get("history_group") or {}
    rec = sa.get("records") or {}
    with_data = sa.get("pairs_with_data")

    lt6 = yg.get("lt_6", 0)
    testable = (with_data - lt6) if isinstance(with_data, int) else None
    rel = {
        "years_group_sums_to_with_data":
            lt6 + yg.get("6_to_7", 0) + yg.get("ge_8", 0) == with_data,
        "eligibility_sums_to_testable":
            (eg.get("pit_eligible", 0) + eg.get("never_eligible", 0) == testable
             if testable is not None else False),
        "pit_detail_sums_to_eligible":
            pd.get("history_lt_8", 0) + pd.get("history_ge_8", 0) == eg.get("pit_eligible", 0),
        "history_group_sums_to_ge_8":
            (hg.get("strict", 0) + hg.get("exploratory", 0) + hg.get("below_threshold", 0)
             == yg.get("ge_8", 0)),
        "patterns_equal_history_qualified":
            n_patterns == hg.get("strict", 0) + hg.get("exploratory", 0),
        "pit_only_equal_eligible_minus_history_qualified":
            n_pit_only == eg.get("pit_eligible", 0) - rec.get("patterns_point_in_time", 0),
        "total_pit_eligible_equal":
            rec.get("patterns_point_in_time", 0) + n_pit_only == eg.get("pit_eligible", 0),
        "pit_only_splits":
            n_pit_only == (rec.get("pit_only_insufficient_history", 0)
                           + rec.get("pit_only_below_threshold", 0)),
    }
    detail = {
        "years_group_sums_to_with_data":
            "lt6+6to7+ge8=%d vs with_data=%r" % (lt6 + yg.get("6_to_7", 0) + yg.get("ge_8", 0), with_data),
        "eligibility_sums_to_testable":
            "eligible+never=%d vs testable=%r" % (eg.get("pit_eligible", 0) + eg.get("never_eligible", 0), testable),
        "pit_detail_sums_to_eligible":
            "lt8+ge8=%d vs eligible=%r" % (pd.get("history_lt_8", 0) + pd.get("history_ge_8", 0),
                                           eg.get("pit_eligible")),
        "history_group_sums_to_ge_8":
            "strict+expl+below=%d vs ge8=%r" % (hg.get("strict", 0) + hg.get("exploratory", 0)
                                                + hg.get("below_threshold", 0), yg.get("ge_8")),
        "patterns_equal_history_qualified":
            "patterns=%d vs strict+expl=%d" % (n_patterns, hg.get("strict", 0) + hg.get("exploratory", 0)),
        "pit_only_equal_eligible_minus_history_qualified":
            "pit_only=%d vs eligible-pit=%d" % (n_pit_only, eg.get("pit_eligible", 0)
                                                - rec.get("patterns_point_in_time", 0)),
        "total_pit_eligible_equal":
            "pit+pitonly=%d vs eligible=%r" % (rec.get("patterns_point_in_time", 0) + n_pit_only,
                                               eg.get("pit_eligible")),
        "pit_only_splits":
            "pit_only=%d vs lt8+below=%d" % (n_pit_only, rec.get("pit_only_insufficient_history", 0)
                                             + rec.get("pit_only_below_threshold", 0)),
    }
    return rel, detail


def check(conn, as_of, bounds_hist, bench_ret):
    """--check：结构不变量 + **源数据一致性**（重算当前窗口并与产物逐字段比对）。

    ★ conn 为 None 表示源库不可用（CI 场景）→ 只做结构校验，并**显式打印 SKIP**，
      不得把「没核对」说成「核对通过」。
    """
    files = sorted([f for f in os.listdir(CURRENT) if OUT_RE.match(f)],
                   key=lambda f: int(OUT_RE.match(f).group(1)))
    if not files:
        print("FAIL: 产物不存在"); return 1
    path = os.path.join(CURRENT, files[-1])
    with open(path, encoding="utf-8") as fh:      # ★ 显式关闭句柄（避免 ResourceWarning）
        doc = json.load(fh)
    errs = []
    src_checked = conn is not None
    c = doc.get("criteria") or {}

    # ① 协议版本
    if doc.get("protocol") != PROTOCOL:
        errs.append("protocol 期望 %s，实际 %r" % (PROTOCOL, doc.get("protocol")))
    # ② 阈值与脚本常量一致（防止「产物写着 A、脚本跑的是 B」）
    for key, val in (("min_years", MIN_YEARS), ("min_median_excess", MIN_MEDIAN),
                     ("min_hit_rate", MIN_HIT), ("min_train_years", MIN_TRAIN_YEARS),
                     ("min_oos_tests", MIN_OOS_TESTS),
                     ("min_total_years_for_test", MIN_TOTAL_YEARS_FOR_TEST)):
        if c.get(key) != val:
            errs.append("criteria.%s 期望 %r，实际 %r" % (key, val, c.get(key)))
    if (c.get("exploratory") or {}).get("min_median_excess") != EXP_MEDIAN:
        errs.append("criteria.exploratory.min_median_excess 与脚本不一致")
    # ★ A1：命中率阈值也要校验（此前只查了 median，改 EXP_HIT 也能通过）
    if (c.get("exploratory") or {}).get("min_hit_rate") != EXP_HIT:
        errs.append("criteria.exploratory.min_hit_rate 期望 %r，实际 %r"
                    % (EXP_HIT, (c.get("exploratory") or {}).get("min_hit_rate")))
    # ③ 产物 as_of == 当前基准序列最后一个完整交易日（源库不可用时跳过）
    if src_checked and doc.get("as_of") != as_of:
        errs.append("as_of 期望 %s（基准最后交易日），实际 %r —— 产物已过期或基准变了"
                    % (as_of, doc.get("as_of")))

    # ④ 结构不变量（★ A1：STRICT / EXPLORATORY / 历史不足 / OOS 不足 四类都覆盖）
    OOS_STATES = {"REPORTED", "INSUFFICIENT_OOS"}

    def _tier_stat_ok(by, label, pid):
        """两层统计必须齐备，且 STRICT+EXPLORATORY 的检验数加总 == oos_tests。"""
        if not isinstance(by, dict) or "STRICT" not in by or "EXPLORATORY" not in by:
            errs.append("%s 的 oos_by_train_tier 缺 STRICT/EXPLORATORY 分项" % pid); return
        s, e = by["STRICT"].get("tests", 0), by["EXPLORATORY"].get("tests", 0)
        if s + e != label:
            errs.append("%s oos_by_train_tier 检验数 %d+%d ≠ oos_tests %d" % (pid, s, e, label))

    for p in doc["patterns"]:
        pid = p["pattern_id"]
        tier = p.get("tier")
        if tier not in ("STRICT", "EXPLORATORY"):
            errs.append("%s 的 tier 非法: %r" % (pid, tier)); continue
        if p["n_years"] < c["min_years"]:
            errs.append("%s tier=%s 但历史样本 %d < %d 年" % (pid, tier, p["n_years"], c["min_years"]))
        if tier == "STRICT" and (p["median_excess_pct"] < c["min_median_excess"]
                                 or p["hit_rate"] < c["min_hit_rate"]):
            errs.append("%s 标 STRICT 但未达 STRICT 阈值" % pid)
        if tier == "EXPLORATORY":
            ex = c.get("exploratory") or {}
            if (p["median_excess_pct"] < ex.get("min_median_excess", EXP_MEDIAN)
                    or p["hit_rate"] < ex.get("min_hit_rate", EXP_HIT)):
                errs.append("%s 标 EXPLORATORY 但未达探索阈值" % pid)
            if (p["median_excess_pct"] >= c["min_median_excess"] and p["hit_rate"] >= c["min_hit_rate"]):
                errs.append("%s 已达 STRICT 却标成 EXPLORATORY" % pid)
        st = p.get("oos_status")
        if st not in OOS_STATES:
            errs.append("%s OOS 状态非法: %r" % (pid, st))
        elif st == "REPORTED" and p.get("oos_tests", 0) < c["min_oos_tests"]:
            errs.append("%s OOS 年数不足却报告" % pid)
        elif st == "INSUFFICIENT_OOS" and p.get("oos_tests", 0) >= c["min_oos_tests"]:
            errs.append("%s 检验 %d 年已达标却标 INSUFFICIENT_OOS（疑似用历史统计替代）"
                        % (pid, p.get("oos_tests", 0)))
        if "pit_eligible_years" not in p:
            errs.append("%s 缺 pit_eligible_years" % pid)
        if p.get("discovery_basis") == "FULL_SAMPLE_ONLY" and p["pit_eligible_years"] != 0:
            errs.append("%s 标 FULL_SAMPLE_ONLY 却有资格年" % pid)
        if p.get("discovery_basis") == "POINT_IN_TIME" and p["pit_eligible_years"] < 1:
            errs.append("%s 标 POINT_IN_TIME 却无资格年" % pid)
        if "oos_by_train_tier" not in p:
            errs.append("%s 缺 oos_by_train_tier（两层统计未分开）" % pid)
        else:
            _tier_stat_ok(p["oos_by_train_tier"], p.get("oos_tests", 0), pid)

    for p in doc.get("pit_only_patterns") or []:
        pid = p.get("pattern_id")
        if p.get("pit_eligible_years", 0) < 1:
            errs.append("%s 在 pit_only 里却没有资格年" % pid)
        ht = p.get("history_tier")
        if ht not in (TIER_INSUFFICIENT_HISTORY, "BELOW_THRESHOLD"):
            errs.append("%s 的 history_tier 非法: %r" % (pid, ht))
        elif ht == TIER_INSUFFICIENT_HISTORY and p.get("n_years", 0) >= c["min_years"]:
            errs.append("%s 标 INSUFFICIENT_HISTORY 但样本 %d ≥ %d 年"
                        % (pid, p.get("n_years", 0), c["min_years"]))
        elif ht == "BELOW_THRESHOLD" and p.get("n_years", 0) < c["min_years"]:
            errs.append("%s 标 BELOW_THRESHOLD 但样本 %d < %d 年"
                        % (pid, p.get("n_years", 0), c["min_years"]))
        st = p.get("oos_status")
        if st not in OOS_STATES:
            errs.append("%s（pit_only）OOS 状态非法: %r" % (pid, st))
        elif st == "REPORTED" and p.get("oos_tests", 0) < c["min_oos_tests"]:
            errs.append("%s（pit_only）OOS 年数不足却报告" % pid)
        elif st == "INSUFFICIENT_OOS" and p.get("oos_tests", 0) >= c["min_oos_tests"]:
            errs.append("%s（pit_only）检验数已达标却标 INSUFFICIENT_OOS" % pid)
        if "oos_by_train_tier" not in p:
            errs.append("%s（pit_only）缺 oos_by_train_tier" % pid)
        else:
            _tier_stat_ok(p["oos_by_train_tier"], p.get("oos_tests", 0), pid)
    for key in ("stocks", "industry_boards", "concept_baskets"):
        if key not in (doc.get("coverage_detail") or {}):
            errs.append("缺 %s 覆盖" % key)
    if not (doc.get("bias_audit") or {}).get("old_method"):
        errs.append("缺 bias_audit.old_method")
    if not (doc.get("oos_summary") or {}).get("by_train_tier"):
        errs.append("缺 oos_summary.by_train_tier（两层样本外统计未分开）")
    if not (doc.get("walk_forward_audit") or {}).get("by_year"):
        errs.append("缺 walk_forward_audit.by_year")
    if not (doc.get("scan_audit") or {}).get("pairs_scanned"):
        errs.append("缺 scan_audit（候选扫描量未交代）")

    # ④b ★ A1：跨块对账 —— **在检查时重算**，不信任产物里的布尔值
    sa = doc.get("scan_audit") or {}
    rec = sa.get("records") or {}
    rc_stored = sa.get("reconcile") or {}
    n_patterns, n_pit_only = len(doc["patterns"]), len(doc.get("pit_only_patterns") or [])
    rc_calc, rc_detail = _recompute_reconcile(sa, n_patterns, n_pit_only)
    if not rc_stored:
        errs.append("缺 scan_audit.reconcile（扫描口径未自洽校验）")
    else:
        missing = sorted(set(rc_calc) - set(rc_stored))
        extra = sorted(set(rc_stored) - set(rc_calc))
        if missing or extra:
            errs.append("reconcile 键集合与实现不一致 —— 缺 %s / 多 %s" % (missing or "-", extra or "-"))
        broken = [k for k, v in rc_calc.items() if not v]
        if broken:
            errs.append("分组计数不自洽: %s（实算 %s）"
                        % (broken, {k: rc_detail[k] for k in broken}))
        forged = [k for k in rc_calc if rc_stored.get(k) is not rc_calc[k]]
        if forged:
            errs.append("reconcile 记录与重算不一致（疑似留旧 true）: %s" % forged)
    if rec.get("patterns") != n_patterns:
        errs.append("scan_audit.records.patterns %r ≠ 实际 patterns %d" % (rec.get("patterns"), n_patterns))
    if rec.get("pit_only") != n_pit_only:
        errs.append("scan_audit.records.pit_only %r ≠ 实际 pit_only %d" % (rec.get("pit_only"), n_pit_only))
    bias = doc.get("bias_audit") or {}
    newm = (bias.get("new_method") or {}).get("tests")
    all_tests = sum(p.get("oos_tests", 0) for p in doc["patterns"]) + \
        sum(p.get("oos_tests", 0) for p in (doc.get("pit_only_patterns") or []))
    if newm != all_tests:
        errs.append("bias_audit.new_method.tests %r ≠ 产物中检验数合计 %d" % (newm, all_tests))
    osum = doc.get("oos_summary") or {}
    comb = (osum.get("combined") or {}).get("tests")
    bt = osum.get("by_train_tier") or {}
    if comb != all_tests:
        errs.append("oos_summary.combined.tests %r ≠ 检验数合计 %d" % (comb, all_tests))
    if (bt.get("STRICT", {}).get("tests", 0) + bt.get("EXPLORATORY", {}).get("tests", 0)) != comb:
        errs.append("oos_summary.by_train_tier 两层检验数之和 ≠ combined")
    by_year_sum = sum(r.get("tests_run", 0) for r in (doc.get("walk_forward_audit") or {}).get("by_year", []))
    if by_year_sum != all_tests:
        errs.append("walk_forward_audit.by_year 检验数合计 %d ≠ 产物合计 %d" % (by_year_sum, all_tests))

    # ⑤ ★★ 源数据一致性：重算每个当前窗口的**关键指标**并逐字段比对
    #    ★ 范围声明：这是「窗口指标核对」（n_years / 中位 / 命中 / 层级 / 时点资格 /
    #      OOS 次数与分层），**不是**完整产物逐字节复现（不重算 representative_stocks、
    #      per_year 明细与 pit_only 全量记录）。
    drift = []
    if src_checked:
        for p in doc.get("current_windows") or []:
            sid, m = p["board_series"], p["month"]
            mr = month_returns(load(conn, sid), bounds_hist)
            vals = sorted((int(ym[:4]), ret - bench_ret[ym]) for ym, ret in mr.items()
                          if ym in bench_ret and int(ym[4:6]) == m)
            if not vals:
                drift.append("%s 源数据为空" % p["pattern_id"]); continue
            exs = [v for _, v in vals]
            recs, elig = walk_forward(vals)
            hist = tier_of(vals, MIN_YEARS) if len(vals) >= MIN_YEARS else None
            oos = summarise(elig)          # 与生成器同一函数：OOS 次数/状态/命中/中位/年份/分层
            got = {
                "n_years": len(vals),
                "median_excess_pct": round(statistics.median(exs), 2),
                "hit_rate": round(sum(1 for x in exs if x > 0) / len(exs), 3),
                "tier": hist,
                "pit_eligible_years": len(elig),
                "discovery_basis": "POINT_IN_TIME" if elig else "FULL_SAMPLE_ONLY",
                # ★ A2：页面可见的样本外统计全部纳入核对
                "oos_tests": oos["oos_tests"],
                "oos_status": oos["oos_status"],
                "oos_hit_rate": oos.get("oos_hit_rate"),
                "oos_median_excess_pct": oos.get("oos_median_excess_pct"),
                "oos_years": oos.get("oos_years"),
            }
            for k, v in got.items():
                if p.get(k) != v:
                    drift.append("%s.%s 产物 %r ≠ 重算 %r" % (p["pattern_id"], k, p.get(k), v))
            # 分层统计：次数 / 命中 / 中位 / 状态，逐项比对
            obt = p.get("oos_by_train_tier") or {}
            for t in ("STRICT", "EXPLORATORY"):
                exp = oos["oos_by_train_tier"][t]
                got_t = obt.get(t) or {}
                for f in ("tests", "hit_rate", "median_excess_pct", "status"):
                    if got_t.get(f) != exp.get(f):
                        drift.append("%s.oos_by_train_tier.%s.%s 产物 %r ≠ 重算 %r"
                                     % (p["pattern_id"], t, f, got_t.get(f), exp.get(f)))
            # 分层与合并的计数关系（重算侧再确认一次）
            if (obt.get("STRICT", {}).get("tests", 0)
                    + obt.get("EXPLORATORY", {}).get("tests", 0)) != p.get("oos_tests", 0):
                drift.append("%s 分层检验数之和 ≠ oos_tests（产物侧）" % p["pattern_id"])
    if drift:
        errs.extend(drift[:6])
        if len(drift) > 6:
            errs.append("…另有 %d 处漂移" % (len(drift) - 6))

    if errs:
        print("FAIL: %s" % errs[:6]); return 1
    if src_checked:
        print("PASS: 结构不变量 + **窗口指标核对**（%s · as_of %s · 样本内达标 %d · 仅时点资格 %d · "
              "窗口 %d 已重算关键指标）—— 这是窗口指标核对，**不是**完整产物逐字节复现"
              % (os.path.basename(path), as_of, len(doc["patterns"]),
                 len(doc.get("pit_only_patterns") or []), len(doc.get("current_windows") or [])))
    else:
        print("PASS（仅结构）· SKIP 源数据核对：history_scan.db 不存在（CI 不携带该库，1.3GB 未入库）"
              " —— 已校验 protocol/criteria/计数对账/结构不变量，**未**重算任何源数据（%s · 窗口 %d）"
              % (os.path.basename(path), len(doc.get("current_windows") or [])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
