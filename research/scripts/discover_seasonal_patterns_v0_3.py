#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""discover_seasonal_patterns_v0_3.py —— 季节性发现：**时点候选发现 + 时点资格样本外检验**（v0.40）。

## 为什么有 v0_3（相对 v0_2 的实质改动）
v0_2 的**逐年后验逻辑本身没有泄漏**（每个检验年只用该年之前的年份训练），
但它先按**全样本**判 STRICT / EXPLORATORY，只有通过的模式才进入 `walk_forward`。
→ 这是**选择偏差**：哪些模式被检验，取决于包含未来信息的全样本结果。
实测（2026-10-23 数据）：被全样本挡掉的 1,891 次「模式-年」检验命中率仅 **24.9%**，
而旧方法报告的样本外命中率 **67.7%** —— 高估 **9.8pp**；中位超额 +2.07pp → 真实 +0.96pp。

## 新流程（协议先声明，再看结果）
1. 对每个 (序列, 月份)，把年度超额按年份排序；
2. 对每个年份 Y：训练集 = **严格早于 Y** 的年份；训练年数 < `min_train_years` → 不可检验；
   训练集不满足**预先声明**的 STRICT 阈值 → 该年不具资格（不进入检验）；
   满足 → 该年进入检验，记录实际超额与是否为正；
3. 样本外结论只由**具资格年份**汇总；`oos_tests < min_oos_tests` → `INSUFFICIENT_OOS`（不补造、不用样本内替代）；
4. **模式是否进入产物**由「是否曾有时点资格」**或**「全样本是否达标」决定 —— 全样本**不**决定谁被检验；
5. 全样本统计仅作**历史描述**（`in_sample`），不参与资格判定。

## 三层口径（不得混用）
- ① 历史统计：`in_sample`（全样本中位超额 / 命中率）——「过去发生了什么」
- ② 滚动检验：`walk_forward_detail`（逐年的训练窗口、资格、测试结果、失败原因）——「按时间顺序能不能做出来」
- ③ 时点验证结论：`oos_*` + `evidence_grade` —— 只在 `oos_tests >= min_oos_tests` 时给出
★ 任何一层都**不是**未来成功概率；`hit_rate` 不得写成「大概率上涨」。

## 口径（沿用 v0_2，不调整）
- 交易日边界取基准（沪深300）当月首/末交易日；两端都要有收盘；
- 月度持有收益 = 末收/首收 − 1；超额 = 序列 − 基准同区间；
- STRICT：n≥8、中位≥1.5pp、命中≥60%；EXPLORATORY：≥0.8pp / 55%；训练≥5 年；检验≥5 年。
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
PROTOCOL = "seasonal_walk_forward_pit_v1"
TIER_NOT_QUALIFIED = "NOT_QUALIFIED_IN_SAMPLE"


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
    """全样本 / 训练集通用的阈值判定。**阈值先声明**，不随结果调整。"""
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
    """逐年滚动：资格判定**只用该年之前**的年份。

    返回 (records, eligible_tests)：
      records —— 每个年份一条（含训练年数、训练集是否达标、是否具资格、测试结果、失败原因）
      eligible_tests —— 仅具资格年份的测试记录
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
                elig.append({"year": y, "excess_pct": round(ex, 2), "hit": ex > 0})
        recs.append(r)
    return recs, elig


def summarise(elig):
    if not elig:
        return {"oos_tests": 0, "oos_status": "INSUFFICIENT_OOS",
                "oos_note": "没有任何年份在「仅用之前年份」的条件下取得检验资格"}
    hit = sum(1 for t in elig if t["hit"]) / len(elig)
    med = statistics.median([t["excess_pct"] for t in elig])
    return {
        "oos_tests": len(elig),
        "oos_hit_rate": round(hit, 3),
        "oos_median_excess_pct": round(med, 2),
        "oos_years": [str(t["year"]) for t in elig],
        "oos_status": "REPORTED" if len(elig) >= MIN_OOS_TESTS else "INSUFFICIENT_OOS",
        "oos_note": None if len(elig) >= MIN_OOS_TESTS else "检验年数 < %d，不作结论" % MIN_OOS_TESTS,
    }


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
        if doc.get("protocol") != PROTOCOL:
            errs.append("protocol 缺失或不是 %s" % PROTOCOL)
        for p in doc["patterns"]:
            if p["tier"] == "STRICT" and (p["n_years"] < c["min_years"]
                                          or p["median_excess_pct"] < c["min_median_excess"]
                                          or p["hit_rate"] < c["min_hit_rate"]):
                errs.append("%s 不满足 STRICT" % p["pattern_id"])
            if "oos_status" not in p:
                errs.append("%s 缺 OOS 状态" % p["pattern_id"])
            if p.get("oos_status") == "REPORTED" and p["oos_tests"] < c["min_oos_tests"]:
                errs.append("%s OOS 年数不足却报告" % p["pattern_id"])
            if "pit_eligible_years" not in p:
                errs.append("%s 缺 pit_eligible_years（时点资格未记录）" % p["pattern_id"])
            if p.get("discovery_basis") == "FULL_SAMPLE_ONLY" and p["pit_eligible_years"] != 0:
                errs.append("%s 标 FULL_SAMPLE_ONLY 却有资格年" % p["pattern_id"])
            if p.get("discovery_basis") == "POINT_IN_TIME" and p["pit_eligible_years"] < 1:
                errs.append("%s 标 POINT_IN_TIME 却无资格年" % p["pattern_id"])
        for p in doc.get("pit_only_patterns") or []:
            if p.get("pit_eligible_years", 0) < 1:
                errs.append("%s 在 pit_only 里却没有资格年" % p.get("pattern_id"))
            if p.get("oos_status") == "REPORTED" and p.get("oos_tests", 0) < c["min_oos_tests"]:
                errs.append("%s（pit_only）OOS 年数不足却报告" % p.get("pattern_id"))
        for key in ("stocks", "industry_boards", "concept_baskets"):
            if key not in (doc.get("coverage_detail") or {}):
                errs.append("缺 %s 覆盖" % key)
        if not (doc.get("bias_audit") or {}).get("old_method"):
            errs.append("缺 bias_audit.old_method（偏差对照未记录）")
        if not (doc.get("walk_forward_audit") or {}).get("by_year"):
            errs.append("缺 walk_forward_audit.by_year（逐年审计未记录）")
        if errs:
            print("FAIL: %s" % errs[:5]); return 1
        print("PASS: 季节性产物一致（%s · 样本内达标 %d 条 · 仅时点达标 %d 条 · OOS 报告 %d 条 · 时点可发现 %d 条）"
              % (os.path.basename(path), len(doc["patterns"]),
                 len(doc.get("pit_only_patterns") or []),
                 sum(1 for p in doc["patterns"] if p.get("oos_status") == "REPORTED"),
                 sum(1 for p in doc["patterns"] if p.get("pit_eligible_years"))
                 + len(doc.get("pit_only_patterns") or [])))
        return 0

    conn = sqlite3.connect(DB)
    bench = load(conn, "CSI300")
    if not bench:
        print("FAIL: 缺基准"); return 1
    as_of = bench[-1][0]
    bounds = month_bounds(bench)
    cur_ym = as_of[:6]
    bounds_hist = {ym: v for ym, v in bounds.items() if ym < cur_ym}
    bench_ret = month_returns(bench, bounds_hist)
    series_rows = conn.execute(
        "SELECT series_id, name, kind, first_date, last_date, rows FROM scan_series "
        "WHERE kind IN ('industry_board','concept_basket') AND rows>0 AND status='OK'").fetchall()

    patterns = []
    pit_only = []          # 样本内不达标、但曾有时点资格（旧方法看不到）
    raw_vals = {}          # pattern_id -> 原始 (year, excess)，供逐年明细重算
    # 逐年审计桶：year -> 统计
    audit = {}
    # 偏差对照：旧方法 = 只有全样本达标的模式进入检验
    old_tests, new_tests, hidden_tests = [], [], []

    for sid, name, kind, first, last, nrows in series_rows:
        mr = month_returns(load(conn, sid), bounds_hist)
        by_month = {}
        for ym, ret in mr.items():
            if ym in bench_ret:
                by_month.setdefault(int(ym[4:6]), []).append((int(ym[:4]), ret - bench_ret[ym]))
        for m, vals in by_month.items():
            if len(vals) < MIN_YEARS:
                continue
            full_tier = tier_of(vals, MIN_YEARS)          # 仅历史描述，不决定资格
            recs, elig = walk_forward(vals)               # 时点资格
            if full_tier is None and not elig:
                continue                                  # 既无历史达标、也从无时点资格 → 不入库
            pid = "SEAS-%s-M%02d" % (sid, m)
            raw_vals[pid] = list(vals)
            oos = summarise(elig)
            pit_years = [t["year"] for t in elig]
            exs = [v for _, v in vals]
            failures = {k: sum(1 for r in recs if r.get("reason") == k)
                        for k in ("TRAIN_YEARS_TOO_FEW", "TRAIN_CRITERIA_NOT_MET")}

            if full_tier is None:
                # ★ 样本内不达标、但曾在时点上取得检验资格 → 旧方法**完全看不到**的模式。
                #   放在独立数组里（紧凑记录），既留证又不改变 `patterns` 的形状。
                pit_only.append({
                    "pattern_id": pid, "board": name, "board_series": sid, "kind": kind, "month": m,
                    "n_years": len(vals),
                    "median_excess_pct": round(statistics.median(exs), 2),
                    "hit_rate": round(sum(1 for x in exs if x > 0) / len(exs), 3),
                    "pit_eligible_years": len(pit_years),
                    "pit_first_year": pit_years[0] if pit_years else None,
                    "pit_last_year": pit_years[-1] if pit_years else None,
                    "walk_forward_failures": failures,
                    **oos,
                    "in_sample_tier": TIER_NOT_QUALIFIED,
                    "note": "全样本未达标；仅在「只用之前年份」的条件下曾具资格 → 旧方法（全样本先筛）看不到",
                })
                for r in recs:
                    b = audit.setdefault(r["year"], {"year": r["year"], "testable": 0, "eligible": 0,
                                                     "tested": 0, "hits": 0, "excess": []})
                    if r.get("testable"):
                        b["testable"] += 1
                    if r.get("eligible"):
                        b["eligible"] += 1
                        b["tested"] += 1
                        b["hits"] += 1 if r.get("test_hit") else 0
                        b["excess"].append(r["test_excess_pct"])
                new_tests.extend(elig)
                hidden_tests.extend(elig)
                continue

            basis = "POINT_IN_TIME" if pit_years else "FULL_SAMPLE_ONLY"
            grade = ("NOT_DISCOVERABLE_IN_TIME" if not pit_years
                     else "OOS_REPORTED" if oos["oos_status"] == "REPORTED" else "OOS_INSUFFICIENT")

            patterns.append({
                "pattern_id": pid, "board": name, "board_series": sid, "kind": kind, "month": m,
                # ① 历史统计（全样本 · 仅描述）
                "tier": full_tier,
                "n_years": len(vals),
                "years": sorted(str(y) for y, _ in vals),
                "median_excess_pct": round(statistics.median(exs), 2),
                "hit_rate": round(sum(1 for x in exs if x > 0) / len(exs), 3),
                "best_year": {"year": str(max(vals, key=lambda v: v[1])[0]),
                              "excess_pct": round(max(vals, key=lambda v: v[1])[1], 2)},
                "worst_year": {"year": str(min(vals, key=lambda v: v[1])[0]),
                               "excess_pct": round(min(vals, key=lambda v: v[1])[1], 2)},
                "per_year": [{"year": str(y), "excess_pct": round(e, 2)} for y, e in sorted(vals)],
                # ② 滚动检验（逐年记录）
                "pit_eligible_years": len(pit_years),
                "pit_first_year": pit_years[0] if pit_years else None,
                "pit_last_year": pit_years[-1] if pit_years else None,
                "discovery_basis": basis,
                "walk_forward_failures": failures,
                # ③ 时点验证结论
                **oos,
                "evidence_grade": grade,
            })

            # ---- 审计聚合 ----
            for r in recs:
                b = audit.setdefault(r["year"], {"year": r["year"], "testable": 0, "eligible": 0,
                                                 "tested": 0, "hits": 0, "excess": []})
                if r.get("testable"):
                    b["testable"] += 1
                if r.get("eligible"):
                    b["eligible"] += 1
                    b["tested"] += 1
                    b["hits"] += 1 if r.get("test_hit") else 0
                    b["excess"].append(r["test_excess_pct"])
            new_tests.extend(elig)
            old_tests.extend(elig)          # 旧方法口径：全样本达标者才进检验（本分支即达标者）

    # 代表股票：只对「样本内达标」的概念模式计算（与 v0_2 口径一致，避免无谓开销）
    for p in patterns:
        if p["kind"] != "concept_basket" or p["tier"] == TIER_NOT_QUALIFIED:
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
             "median_excess_pct": v, "years": n, "source": "当前概念成分 + 基准日历对齐"}
            for s_, v, n in scored[:3]]
        if not scored:
            p["rep_stock_gap"] = "成分内没有 ≥%d 年可比样本的个股" % MIN_STOCK_YEARS

    patterns.sort(key=lambda p: (-p["median_excess_pct"], -p["hit_rate"]))
    cur = int(as_of[4:6])
    for p in patterns:
        p["current_status"] = ("IN_WINDOW" if p["month"] == cur
                               else "PRE_WINDOW" if p["month"] == cur + 1
                               else "LATER" if p["month"] > cur else "PASSED")

    # ★ 产品窗口：仍以「样本内达标」为准（不把样本内不达标的模式塞进产品），
    #   但每个窗口都带时点可发现性标记，分组据此降级。
    windows = [p for p in patterns
               if p["current_status"] in ("IN_WINDOW", "PRE_WINDOW")
               and p["tier"] != TIER_NOT_QUALIFIED]
    for p in windows:
        # ★ 用**未取整**的原始超额重算逐年记录，避免四舍五入把阈值判定推到另一边
        p["walk_forward_detail"] = walk_forward(raw_vals[p["pattern_id"]])[0]

    def cov(kind):
        n, rows, f, l = conn.execute(
            "SELECT COUNT(*), SUM(rows), MIN(first_date), MAX(last_date) FROM scan_series "
            "WHERE kind=? AND rows>0", (kind,)).fetchone()
        return {"series": n or 0, "rows": rows or 0,
                "first_date": norm(f) if f else None, "last_date": norm(l) if l else None}

    def agg(tests):
        if not tests:
            return {"tests": 0}
        return {"tests": len(tests),
                "hit_rate": round(sum(1 for t in tests if t["hit"]) / len(tests), 3),
                "median_excess_pct": round(statistics.median([t["excess_pct"] for t in tests]), 2)}

    by_year = []
    for y in sorted(audit):
        b = audit[y]
        by_year.append({
            "year": y, "patterns_testable": b["testable"], "patterns_eligible": b["eligible"],
            "tests_run": b["tested"], "hits": b["hits"],
            "hit_rate": round(b["hits"] / b["tested"], 3) if b["tested"] else None,
            "median_excess_pct": round(statistics.median(b["excess"]), 2) if b["excess"] else None,
        })

    doc = {
        "artifact": "pattern_discovery", "artifact_version": "0.6",
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
            "in_sample_min_years": MIN_YEARS,
            "training_rule": "每年资格判定只用该年之前的年份：训练年数 ≥5 且训练集中位≥1.5pp、命中≥60%（预先声明，不随结果调整）",
            "completed_months_only": True,
            "month_boundary": "基准（沪深300）当月首/末交易日；序列两端都要有收盘",
            "rule": "月度持有收益 = 末收/首收−1；超额 = 序列 − 基准同区间",
            "selection_rule": "模式是否进入产物 = 曾有时点资格 OR 全样本达标；全样本**不**决定谁被检验",
        },
        "reporting_layers": {
            "L1_historical_statistics": "in_sample（tier / n_years / median_excess_pct / hit_rate）：全样本的历史描述，**不是**未来概率",
            "L2_rolling_tests": "walk_forward_detail / walk_forward_audit：逐年训练窗口、资格、测试结果与失败原因",
            "L3_point_in_time_conclusion": "oos_* + evidence_grade：仅在 oos_tests ≥ min_oos_tests 时给出结论，否则 INSUFFICIENT_OOS",
            "note": "三层不得混用；历史命中率不得写成「未来成功概率」。",
        },
        "bias_audit": {
            "what": "旧方法（v0_2）先按全样本判 STRICT/EXPLORATORY，只有通过者进入滚动检验 → 选择偏差。",
            "old_method": {"tests": len(old_tests), **{k: v for k, v in agg(old_tests).items() if k != "tests"}},
            "new_method": {"tests": len(new_tests), **{k: v for k, v in agg(new_tests).items() if k != "tests"}},
            "hidden_by_old_method": {"tests": len(hidden_tests),
                                     **{k: v for k, v in agg(hidden_tests).items() if k != "tests"}},
            "inflation": {
                "hit_rate_pp": round((agg(old_tests).get("hit_rate", 0)
                                      - agg(new_tests).get("hit_rate", 0)) * 100, 1),
                "median_excess_pp": round(agg(old_tests).get("median_excess_pct", 0)
                                          - agg(new_tests).get("median_excess_pct", 0), 2),
            },
            "note": "旧方法的逐年训练逻辑本身没有泄漏；偏差在「谁进入检验」这一层。",
        },
        "walk_forward_audit": {
            "by_year": by_year,
            "note": ("patterns_testable = 该年有训练数据且训练年数达标的模式数；patterns_eligible = 训练集通过阈值的模式数；"
                     "tests_run = 实际进入检验的模式数（= eligible）；失败原因见各模式的 walk_forward_failures。"),
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
        "current_windows": windows,
        "tier_note": ("STRICT/EXPLORATORY = 全样本历史描述（预先声明阈值）；NOT_QUALIFIED_IN_SAMPLE = 全样本未达标但曾有时点资格。"
                      "**样本内通过 ≠ 已验证规律**；请同时看 evidence_grade / oos_* / pit_eligible_years。"),
        "limitations": [
            "★ 自建概念指数是**合成研究序列**（当前成分等权、成交量无意义），不等于官方概念指数。",
            "★ 行业板块**没有历史成分** → 不绑定个股；概念代表股票来自**当前成分**，不是当年龙头。",
            "★ 板块/概念均为**当前**分类回溯，历史变更无法还原。",
            "★ 样本外检验按年份滚动；检验年数 <5 标 INSUFFICIENT_OOS，不作结论。",
            "★ 退市股不在库内 → 早期年份存在幸存者偏差。",
            "★ discovery_basis = FULL_SAMPLE_ONLY 的模式**在当年无法被发现**（只有回看才成立），不得作为「当时可预判」的证据。",
        ],
    }

    strict = [p for p in patterns if p["tier"] == "STRICT"]
    expl = [p for p in patterns if p["tier"] == "EXPLORATORY"]
    oos_rep = [p for p in patterns if p.get("oos_status") == "REPORTED"]
    pit = [p for p in patterns if p.get("pit_eligible_years")]
    print("序列 %d · 样本内达标 %d（STRICT %d / 探索 %d）· 仅时点达标 %d · 窗口 %d · OOS 可报告 %d · 时点可发现 %d"
          % (len(series_rows), len(patterns), len(strict), len(expl), len(pit_only),
             len(windows), len(oos_rep), len(pit) + len(pit_only)))
    print("偏差对照：旧 %s vs 新 %s（被旧方法挡掉 %s）"
          % (agg(old_tests), agg(new_tests), agg(hidden_tests)))
    for p in [x for x in windows if x["tier"] == "STRICT"][:5]:
        print("  %s %d月 · %d年 · 中位%+.2f%% · 命中%.0f%% · 时点资格%d次 · %s"
              % (p["board"], p["month"], p["n_years"], p["median_excess_pct"],
                 p["hit_rate"] * 100, p["pit_eligible_years"], p["evidence_grade"]))

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
