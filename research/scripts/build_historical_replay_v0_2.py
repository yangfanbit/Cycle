#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""历史冻结重放 v0.2：横截面中性化目标 + 第 3 个信息侧特征 + purge/embargo
+ cluster bootstrap + Holm 多重检验 + 2010 起绝对收益敏感性对照。

★ 口径在 docs/HISTORICAL_REPLAY_DESIGN_v0_2.md 中**先于本脚本**冻结；
  设计文档全文 sha256_16 锁在 LOCKED_DESIGN_SHA16，改口径必须升版并留痕。
★ v0.1 的设计 / 脚本 / 产物逐字节保留；本脚本 --check 会核对三份基线指纹。

用法：
  python research/scripts/build_historical_replay_v0_2.py --write
  python research/scripts/build_historical_replay_v0_2.py --check

边界：
- 不读官方指数接口、不联网；只用 research/database/history_scan.db 的 raw 收盘。
- 缺 1.3 GB 大库时 --check 显式 SKIP 行情复算并打印范围，形状/语义/禁用词照常。
- 不产生板块或个股明细清单，不进默认页；产物只给聚合统计。
"""

import argparse
import collections
import datetime
import hashlib
import importlib.util
import json
import math
import os
import random
import sqlite3
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(ROOT, "research", "current")
DOCS = os.path.join(ROOT, "docs")
SCRIPTS = os.path.join(ROOT, "research", "scripts")
DB = os.path.join(ROOT, "research", "database", "history_scan.db")

OUT = os.path.join(CURRENT, "historical_replay_v0_2.json")
SEM = os.path.join(CURRENT, "board_semantics_v0_1.json")
TD = os.path.join(CURRENT, "theme_discovery_v0_1.json")
TD_SCRIPT = os.path.join(SCRIPTS, "build_theme_discovery_v0_1.py")
RADAR = os.path.join(CURRENT, "new_theme_radar_v0_10_view.json")
ROLES = os.path.join(CURRENT, "historical_market_roles_v0_13.json")
DESIGN = os.path.join(DOCS, "HISTORICAL_REPLAY_DESIGN_v0_2.md")

V01_DESIGN = os.path.join(DOCS, "HISTORICAL_REPLAY_DESIGN_v0_1.md")
V01_OUT = os.path.join(CURRENT, "historical_replay_v0_1.json")
V01_SCRIPT = os.path.join(SCRIPTS, "build_historical_replay_v0_1.py")

# ── 设计 §0 记录的 v0.1 基线（冻结时实测；--check 断言旧文件未被覆盖） ──
V01_BASELINE_SHA16 = {
    "HISTORICAL_REPLAY_DESIGN_v0_1.md": "73858f2633d787eb",
    "historical_replay_v0_1.json": "6297e9be8c8a3226",
    "build_historical_replay_v0_1.py": "9e30d8cb0ef3ac0d",
}
LOCKED_DESIGN_SHA16 = "32ad700f0e0a2692"

# ── 设计 §1/§2/§4/§5/§6 冻结的常量，一律不因结果调整 ──
PRE_DAYS = 60
STEP = 60
HORIZON = 20
EMBARGO = 20
MIN_TRAIN = 20
MIN_CROSS_SECTION = 30
INFO_LOOKBACK_DAYS = 365
SENS_START = "2010-01-01"   # 设计 §6：敏感性对照轨的声明起点
BOOTSTRAP_B = 2000
BOOTSTRAP_SEED = 20261113
TRIAL_COUNT = 2
ALPHA = 0.05
CALIB_MONOTONE_TOL = 0.05
CALIB_MAX_GAP = 0.20
Z95 = 1.959963984540054

# 设计 §3.2：theme_id → (board_series, relation)；只登记同轴或显式代理
ROLE_MAP = {
    "SEMICONDUCTOR_AI": ("BK881121", "DIRECT"),
    "ROBOTICS": ("CPT_zjqrgn", "DIRECT"),
    "MEDIA": ("BK881164", "PROXY"),
    "AUTO_INTELLIGENCE": ("BK881126", "PROXY"),
    "POWER_SUMMER": ("BK881145", "PROXY"),
}
NO_EXACT_MAPPING_THEMES = ("FLU", "CONSUMER_SEASON", "RESOURCE_METAL")

BANNED = ("买入", "卖出", "目标价", "仓位", "胜率", "准确性", "荐股", "选股清单",
          "龙头", "弹性", "大概率", "未来概率", "TODO", "TBD", "PLACEHOLDER")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def _dump(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, sort_keys=True, indent=1)
        f.write("\n")


def norm_date(d):
    s = str(d).replace("-", "")
    return "%s-%s-%s" % (s[:4], s[4:6], s[6:8])


def wilson(k, n, z=Z95):
    if n <= 0:
        return None, None, None
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = (z / den) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return round(p, 4), round(max(0.0, center - half), 4), round(min(1.0, center + half), 4)


def _clamp(p):
    return min(1 - 1e-6, max(1e-6, p))


def _brier(p, o):
    return (p - o) ** 2


def _logloss(p, o):
    p = _clamp(p)
    return -(o * math.log(p) + (1 - o) * math.log(1 - p))


def _pct(values, q):
    """线性插值百分位；values 非空。"""
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    pos = q * (len(s) - 1)
    lo = int(math.floor(pos))
    hi = min(len(s) - 1, lo + 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def _date(s):
    return datetime.date.fromisoformat(s)


# ────────────────────────── 数据加载 ──────────────────────────

def load_market(con):
    """返回 (CSI300 日历, 全库归一日历, 基准收盘, 序列收盘, 成交额代理, 元数据, 重复日期)。"""
    bench = {}
    for d, c in con.execute("select trade_date,close from scan_daily where series_id='CSI300'"):
        if c and c > 0:
            bench[norm_date(d)] = float(c)
    cal = sorted(bench)
    all_cal = sorted({norm_date(r[0]) for r in con.execute("select distinct trade_date from scan_daily")})
    series = collections.defaultdict(dict)
    amount = collections.defaultdict(dict)
    meta = {}
    for sid, name, kind in con.execute(
            "select series_id,name,kind from scan_series "
            "where kind in ('industry_board','concept_basket')"):
        meta[sid] = {"name": name, "kind": kind}
    dup = []
    for sid, d, c, v in con.execute(
            "select d.series_id,d.trade_date,d.close,d.volume from scan_daily d "
            "join scan_series s on d.series_id=s.series_id "
            "where s.kind in ('industry_board','concept_basket')"):
        nd = norm_date(d)
        if nd in series[sid]:
            dup.append({"series_id": sid, "trade_date": nd})
            continue
        if c and float(c) > 0:
            series[sid][nd] = float(c)
            amount[sid][nd] = float(c) * (float(v or 0))
    return cal, all_cal, bench, series, amount, meta, dup


def load_info_events():
    """设计 §3：雷达标题精确匹配 + 历史角色显式映射，全部带 date<=T 截断。"""
    spec = importlib.util.spec_from_file_location("td_v082_keywords", TD_SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    kw = dict(m.KEYWORD_MAP)

    by_series = collections.defaultdict(set)
    radar = _load(RADAR)
    radar_pairs = set()
    for e in radar.get("events") or []:
        title = e.get("title") or ""
        d = e.get("event_date")
        if not d:
            continue
        for word, v in kw.items():
            if word in title:
                radar_pairs.add((d, v[1]))
    for d, sid in radar_pairs:
        by_series[sid].add(d)

    roles = _load(ROLES)
    role_pairs = set()
    no_exact = collections.Counter()
    for _eid, v in (roles.get("events") or {}).items():
        tid = v.get("theme_id")
        w = v.get("window") or []
        if tid in NO_EXACT_MAPPING_THEMES:
            no_exact[tid] += 1
            continue
        if tid not in ROLE_MAP or not w:
            continue
        role_pairs.add((w[0], ROLE_MAP[tid][0]))
    for d, sid in role_pairs:
        by_series[sid].add(d)

    kw_series = {v[1] for v in kw.values()}
    role_series = {v[0] for v in ROLE_MAP.values()}
    mapped = kw_series | role_series
    report = {
        "keyword_count": len(kw),
        "radar_event_count": len(radar.get("events") or []),
        "radar_matched_pairs": len(radar_pairs),
        "role_event_count": len(roles.get("events") or {}),
        "role_mapped_pairs": len(role_pairs),
        "no_exact_mapping_themes": dict(sorted(no_exact.items())),
        "mapped_series_count": len(mapped),
        "mapped_series": sorted(mapped),
        "total_info_events": len(radar_pairs) + len(role_pairs),
        "event_date_min": min([d for d, _ in radar_pairs | role_pairs]) if (radar_pairs | role_pairs) else None,
        "event_date_max": max([d for d, _ in radar_pairs | role_pairs]) if (radar_pairs | role_pairs) else None,
        "rule": "只用标题关键词精确匹配；正文不建关联；NO_EXACT_MAPPING 逐族写原因",
    }
    return {sid: sorted(ds) for sid, ds in by_series.items()}, mapped, report


def features_at(sid, T, cal, idx, bench, series, amount):
    """设计 §2：F1 门槛输入 + F2，全部只用 ≤T。返回 (exc20, ratio, sign) 或 None。"""
    cl = series[sid]
    window = [d for d in cal[idx - PRE_DAYS:idx + 1] if d in cl and d in bench]
    if len(window) < PRE_DAYS:
        return None
    recent = window[-21:]
    if len(recent) < 21 or recent[0] not in cl or recent[-1] not in bench:
        return None
    exc = ((cl[recent[-1]] / cl[recent[0]] - 1) -
           (bench[recent[-1]] / bench[recent[0]] - 1)) * 100
    am = amount[sid]
    a_recent = [am[d] for d in window[-20:] if d in am]
    a_prev = [am[d] for d in window[-40:-20] if d in am]
    ratio = None
    if len(a_recent) >= 20 and len(a_prev) >= 20 and sum(a_prev) > 0:
        ratio = (sum(a_recent) / len(a_recent)) / (sum(a_prev) / len(a_prev))
    return round(exc, 4), (round(ratio, 4) if ratio is not None else None), int(exc > 0)


def info_at(sid, T, events_by_series, mapped):
    """设计 §2：三态 F3。NO_COVERAGE 单独返回，不当 0。"""
    if sid not in mapped:
        return "NO_COVERAGE"
    t = _date(T)
    lo = t - datetime.timedelta(days=INFO_LOOKBACK_DAYS)
    for d in events_by_series.get(sid, ()):
        if lo <= _date(d) <= t:
            return 1
    return 0


def settle_row(sid, T, post, bench, series):
    """返回 (ok, r20, excess_pp, reason)。要求 T 与窗口内全部日期都有收盘。"""
    cl = series[sid]
    if T not in cl or T not in bench:
        return False, None, None, "NO_CLOSE_AT_T"
    end = post[-1]
    if end not in bench or end not in cl:
        return False, None, None, "NO_SERIES_AT_HORIZON"
    if any(d not in cl for d in post):
        return False, None, None, "INCOMPLETE_SERIES_WINDOW"
    r20 = cl[end] / cl[T] - 1
    exc = (r20 - (bench[end] / bench[T] - 1)) * 100
    return True, round(r20, 8), round(exc, 4), None


def _freq(rows):
    if len(rows) < MIN_TRAIN:
        return None
    return sum(1 for x in rows if x[-1] == 1) / len(rows)


def _build_main(cal, bench, series, amount, fuzzy, gate, events_by_series, mapped):
    """主轨：横截面中性化目标。返回 (clusters, excluded, score_rows, coverage, meta)。"""
    abs_thr = float(gate["abs_excess20_pp_gt"])
    amt_thr = float(gate["amount_ratio_20_over_prev20_gt"])
    freeze_idx = list(range(PRE_DAYS, len(cal) - HORIZON, STEP))
    freezes = [cal[i] for i in freeze_idx]

    train_pool = []   # (settle_idx, f1, f2, f3, outcome) —— f3 可为 "NO_COVERAGE"
    clusters = []
    excluded = collections.Counter()
    score_rows = []   # (T, predictor, brier, logloss, p, o)
    cov = collections.Counter()
    series_with_info = set()
    clusters_with_both = 0

    for i, T in zip(freeze_idx, freezes):
        # ★ 设计 §4：purge/embargo，训练观察完成日 ≤ T_idx − EMBARGO
        hist = [x for x in train_pool if x[0] <= i - EMBARGO]
        p_base = _freq(hist)
        p_gate = {1: _freq([x for x in hist if x[1] == 1]),
                  0: _freq([x for x in hist if x[1] == 0])}
        groups = {}
        for f1 in (0, 1):
            for f2 in (0, 1):
                for f3 in (0, 1):
                    groups[(f1, f2, f3)] = _freq(
                        [x for x in hist if x[1] == f1 and x[2] == f2 and x[3] == f3])

        post = cal[i + 1:i + 1 + HORIZON]
        cand = []
        for sid in sorted(series):
            if sid in fuzzy:
                excluded["NOT_INTERPRETABLE"] += 1
                continue
            ok, r20, _exc, reason = settle_row(sid, T, post, bench, series)
            if not ok:
                excluded[reason] += 1
                continue
            feat = features_at(sid, T, cal, i, bench, series, amount)
            if feat is None:
                excluded["INSUFFICIENT_PRE_WINDOW"] += 1
                continue
            exc20, ratio, sign = feat
            f1 = int((exc20 is not None and abs(exc20) > abs_thr) or
                     (ratio is not None and ratio > amt_thr))
            f3 = info_at(sid, T, events_by_series, mapped)
            cand.append({"sid": sid, "r20": r20, "f1": f1, "f2": sign, "f3": f3})

        if len(cand) < MIN_CROSS_SECTION:
            excluded["CLUSTER_BELOW_MIN_CROSS_SECTION"] += len(cand)
            clusters.append({"freeze_date": T, "comparable_observations": 0,
                             "cluster_excluded": True,
                             "reason": "MIN_CROSS_SECTION_INSUFFICIENT",
                             "train_pool_size": len(hist),
                             "embargo_trading_days": EMBARGO})
            continue

        med = statistics.median(x["r20"] for x in cand)
        for x in cand:
            x["outcome"] = int(x["r20"] > med)

        f3_vals = collections.Counter(x["f3"] for x in cand)
        cov["F3_ONE"] += f3_vals[1]
        cov["F3_ZERO"] += f3_vals[0]
        cov["F3_NO_COVERAGE"] += f3_vals["NO_COVERAGE"]
        if f3_vals[0] > 0 and f3_vals[1] > 0:
            clusters_with_both += 1
        for x in cand:
            if x["f3"] == 1:
                series_with_info.add(x["sid"])
        cov["OBSERVATIONS"] += len(cand)

        for x in cand:
            o = x["outcome"]
            pg = p_gate.get(x["f1"])
            if pg is None and p_base is not None:
                pg, fb = p_base, True
            else:
                fb = False
            if pg is None:
                continue
            cov["GATE_FALLBACK"] += int(fb)
            score_rows.append((T, "EX_ANTE_GATE", _brier(pg, o), _logloss(pg, o), pg, o))

            p3 = groups.get((x["f1"], x["f2"], x["f3"])) if x["f3"] != "NO_COVERAGE" else None
            if p3 is None and p_base is not None:
                p3 = p_base
                cov["F3_FALLBACK"] += 1
                if x["f3"] == "NO_COVERAGE":
                    cov["F3_NO_COVERAGE_FALLBACK"] += 1
            if p3 is not None:
                score_rows.append((T, "EX_ANTE_3F", _brier(p3, o), _logloss(p3, o), p3, o))
            if p_base is not None:
                score_rows.append((T, "BASELINE", _brier(p_base, o), _logloss(p_base, o), p_base, o))

        for x in cand:
            train_pool.append((i + HORIZON, x["f1"], x["f2"], x["f3"], x["outcome"]))

        k = sum(x["outcome"] for x in cand)
        n = len(cand)
        clusters.append({
            "freeze_date": T,
            "comparable_observations": n,
            "cluster_excluded": False,
            "cross_sectional_hit_rate": wilson(k, n)[0],
            "outcome_k": k,
            "f3_one": f3_vals[1],
            "f3_zero": f3_vals[0],
            "f3_no_coverage": f3_vals["NO_COVERAGE"],
            "train_pool_size": len(hist),
            "embargo_trading_days": EMBARGO,
            "predictors": {"BASELINE": p_base,
                           "EX_ANTE_GATE_HIT": p_gate[1],
                           "EX_ANTE_GATE_MISS": p_gate[0]},
        })

    meta = {"freezes": freezes, "freeze_idx": freeze_idx,
            "clusters_with_both_f3": clusters_with_both,
            "series_with_f3_one": sorted(series_with_info),
            "coverage": dict(sorted(cov.items()))}
    return clusters, excluded, score_rows, meta


def _build_sensitivity(all_cal, series, amount, fuzzy, gate):
    """设计 §6：2010 起绝对收益，只作 β 更重的敏感性对照，不参与推断。"""
    abs_thr = float(gate["abs_excess20_pp_gt"])
    amt_thr = float(gate["amount_ratio_20_over_prev20_gt"])
    idxs = list(range(PRE_DAYS, len(all_cal) - HORIZON, STEP))
    train_pool = []
    rates = []
    score_rows = []
    skipped = 0
    used = 0
    for i in idxs:
        T = all_cal[i]
        post = all_cal[i + 1:i + 1 + HORIZON]
        hist = [x for x in train_pool if x[0] <= i - EMBARGO]
        p_base = _freq(hist)
        p_g = {1: _freq([x for x in hist if x[1] == 1]),
               0: _freq([x for x in hist if x[1] == 0])}
        cand = []
        for sid in sorted(series):
            if sid in fuzzy:
                continue
            cl = series[sid]
            if T not in cl or post[-1] not in cl or any(d not in cl for d in post):
                continue
            r20 = cl[post[-1]] / cl[T] - 1
            pre = all_cal[i - 20:i + 1]
            if any(d not in cl for d in pre):
                continue
            r_pre = (cl[pre[-1]] / cl[pre[0]] - 1) * 100 if cl[pre[0]] > 0 else 0.0
            am = amount[sid]
            a_recent = [am[d] for d in pre[-20:] if d in am]
            a_prev = [am[d] for d in all_cal[i - 40:i - 20] if d in am]
            ratio = None
            if len(a_recent) >= 20 and len(a_prev) >= 20 and sum(a_prev) > 0:
                ratio = (sum(a_recent) / len(a_recent)) / (sum(a_prev) / len(a_prev))
            f1 = int(abs(r_pre) > abs_thr or (ratio is not None and ratio > amt_thr))
            cand.append((f1, int(r20 > 0)))
        if len(cand) < MIN_CROSS_SECTION:
            skipped += 1
            continue
        used += 1
        k = sum(o for _, o in cand)
        rates.append(wilson(k, len(cand))[0])
        for f1, o in cand:
            pg = p_g.get(f1)
            if pg is None and p_base is not None:
                pg = p_base
            if pg is not None:
                score_rows.append((T, "EX_ANTE_GATE", _brier(pg, o), _logloss(pg, o), pg, o))
            if p_base is not None:
                score_rows.append((T, "BASELINE", _brier(p_base, o), _logloss(p_base, o), p_base, o))
        for f1, o in cand:
            train_pool.append((i + HORIZON, f1, o))
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in score_rows:
        per[r[0]][r[1]].append(r[2])
    scores = {}
    for name in ("BASELINE", "EX_ANTE_GATE"):
        vals = [sum(v[name]) / len(v[name]) for v in per.values() if v.get(name)]
        scores[name] = round(sum(vals) / len(vals), 6) if vals else None
    return {
        "label": "SENSITIVITY_ONLY",
        "target": "FORWARD_ABSOLUTE_POSITIVE（板块绝对收益 > 0，不减基准、不减横截面中位数）",
        "calendar": "全库归一交易日（不依赖 CSI300），按设计 §6 截断到声明起点",
        "calendar_start_declared": SENS_START,
        "calendar_first": all_cal[0] if all_cal else None,
        "calendar_last": all_cal[-1] if all_cal else None,
        "calendar_days": len(all_cal),
        "freeze_points_total": len(idxs),
        "freeze_points_used": used,
        "freeze_points_skipped_below_min_cross_section": skipped,
        "cross_sectional_hit_rate_min": min(rates) if rates else None,
        "cross_sectional_hit_rate_max": max(rates) if rates else None,
        "cross_sectional_hit_rate_range": round(max(rates) - min(rates), 4) if rates else None,
        "brier_mean_by_cluster": scores,
        "note": "β 更重、样本更长更脏；只用于对照横截面中性化是否压掉市场共同因子，"
                "不参与 bootstrap / Holm / ③ 层判定，不作推断",
    }


def _cluster_scores(score_rows, name):
    rows = [r for r in score_rows if r[1] == name]
    per = collections.defaultdict(list)
    for r in rows:
        per[r[0]].append(r)
    return {
        "scored_observations": len(rows),
        "independent_clusters": len(per),
        "brier_mean_by_cluster": (round(sum(
            sum(r[2] for r in rs) / len(rs) for rs in per.values()) / len(per), 6)
            if per else None),
        "logloss_mean_by_cluster": (round(sum(
            sum(r[3] for r in rs) / len(rs) for rs in per.values()) / len(per), 6)
            if per else None),
    }


def _bootstrap(score_rows):
    """设计 §5.3：按冻结日整簇有放回重抽，B/seed 固定 → 逐字节确定性。"""
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in score_rows:
        per[r[0]][r[1]].append(r[2])
    triples = []
    for T in sorted(per):
        d = per[T]
        if all(d.get(n) for n in ("BASELINE", "EX_ANTE_GATE", "EX_ANTE_3F")):
            triples.append((sum(d["EX_ANTE_3F"]) / len(d["EX_ANTE_3F"]),
                            sum(d["BASELINE"]) / len(d["BASELINE"]),
                            sum(d["EX_ANTE_GATE"]) / len(d["EX_ANTE_GATE"])))
    if not triples:
        return {"scored_clusters": 0, "B": BOOTSTRAP_B, "seed": BOOTSTRAP_SEED,
                "tests": [], "note": "无可评分簇，bootstrap 不执行"}
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(triples)
    d1, d2 = [], []
    for _ in range(BOOTSTRAP_B):
        s = [triples[rng.randrange(n)] for _ in range(n)]
        a = sum(x[0] for x in s) / n
        b = sum(x[1] for x in s) / n
        g = sum(x[2] for x in s) / n
        d1.append(a - b)
        d2.append(a - g)

    def summarize(name, delta, ref):
        point = round(sum(a - b for a, b in zip(
            (x[0] for x in triples), (x[1] if ref == "BASELINE" else x[2] for x in triples))) / n, 6)
        ci95 = [round(_pct(delta, 0.025), 6), round(_pct(delta, 0.975), 6)]
        ci975 = [round(_pct(delta, 0.0125), 6), round(_pct(delta, 0.9875), 6)]
        p_le = sum(1 for x in delta if x <= 0) / len(delta)
        p_ge = sum(1 for x in delta if x >= 0) / len(delta)
        p = min(1.0, 2 * min(p_le, p_ge))
        return {"name": name, "reference": ref, "delta_brier_point": point,
                "ci95": ci95, "ci975_holm": ci975,
                "p_empirical": round(p, 6)}

    t1 = summarize("H1_3F_VS_BASELINE", d1, "BASELINE")
    t2 = summarize("H2_3F_VS_GATE", d2, "EX_ANTE_GATE")
    # Holm：p 升序，依次对 alpha/2、alpha
    order = sorted([t1, t2], key=lambda x: x["p_empirical"])
    for j, t in enumerate(order):
        t["holm_alpha"] = ALPHA / (TRIAL_COUNT - j)
        t["holm_reject"] = bool(t["p_empirical"] < t["holm_alpha"])
    for t in (t1, t2):
        t["holm_upper_lt_zero"] = bool(t["ci975_holm"][1] < 0)
        t["passes"] = bool(t["holm_reject"] and t["holm_upper_lt_zero"])
        t["conclusion"] = ("区间上界 < 0 且 Holm 拒绝 → 有可分辨改善"
                           if t["passes"] else
                           "未通过：区间跨 0 或 Holm 未拒绝 → 无可分辨改善")
    return {"scored_clusters": n, "B": BOOTSTRAP_B, "seed": BOOTSTRAP_SEED,
            "resample_unit": "冻结日整簇（簇内观察不独立）",
            "trial_count": TRIAL_COUNT, "alpha": ALPHA,
            "holm_procedure": "p 升序，依次对 alpha/2 与 alpha 判定；通过还需 97.5% 区间上界 < 0",
            "pbo": "NOT_ESTIMABLE",
            "pbo_reason": "PBO/CSCV 需多个候选配置的排名分布；本轮只预先注册 2 个检验、3 个预测器，"
                          "试验次数不足以估计，显式不计算",
            "dsr": "NOT_APPLICABLE",
            "dsr_reason": "DSR 修正策略收益 Sharpe 的多重试验膨胀；本产物是概率评分、无收益序列与 Sharpe",
            "tests": [t1, t2]}


def _calibration(score_rows):
    bins = collections.defaultdict(lambda: {"n": 0, "sum_p": 0.0, "sum_o": 0})
    for r in score_rows:
        if r[1] != "EX_ANTE_3F":
            continue
        b = min(4, int(r[4] * 5))
        bins[b]["n"] += 1
        bins[b]["sum_p"] += r[4]
        bins[b]["sum_o"] += r[5]
    out = []
    for b in range(5):
        v = bins.get(b) or {"n": 0, "sum_p": 0.0, "sum_o": 0}
        out.append({"bin": "%d/5" % b, "n": v["n"],
                    "mean_predicted": round(v["sum_p"] / v["n"], 4) if v["n"] else None,
                    "observed_frequency": round(v["sum_o"] / v["n"], 4) if v["n"] else None})
    nonempty = [x for x in out if x["n"] > 0 and x["observed_frequency"] is not None]
    monotone = all(nonempty[j + 1]["observed_frequency"] >=
                   nonempty[j]["observed_frequency"] - CALIB_MONOTONE_TOL
                   for j in range(len(nonempty) - 1)) if len(nonempty) > 1 else False
    gaps = [abs(x["observed_frequency"] - x["mean_predicted"]) for x in nonempty]
    ok = bool(monotone and gaps and max(gaps) <= CALIB_MAX_GAP)
    return {"bins": out, "monotone_with_tolerance": monotone,
            "max_abs_gap": round(max(gaps), 4) if gaps else None,
            "tolerance": {"monotone": CALIB_MONOTONE_TOL, "max_abs_gap": CALIB_MAX_GAP},
            "passes": ok, "note": "描述性；按设计 §8.1 的固定容差判定，不按结果调整"}


def build():
    if not os.path.exists(DB) or os.path.getsize(DB) == 0:
        raise RuntimeError("缺 history_scan.db（1.3 GB 未入库）→ 无法重放行情")
    td = _load(TD)
    gate = td["rules"]["market_gate"]
    sem = _load(SEM)
    fuzzy = {e["series_id"] for e in (sem.get("entries") or []) if not e.get("interpretable")}

    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        cal, all_cal, bench, series, amount, meta, dup = load_market(con)
    finally:
        con.close()

    events_by_series, mapped, info_report = load_info_events()
    clusters, excluded, score_rows, mmeta = _build_main(
        cal, bench, series, amount, fuzzy, gate, events_by_series, mapped)
    # ★ 设计 §6 声明「2010 起」；全库实际更早（2004-11-04），必须按声明截断
    #   并把「声明 vs 落地」写进产物、由 --check 对账，不让两份真相并存。
    sens_cal = [d for d in all_cal if d >= SENS_START]
    sens = _build_sensitivity(sens_cal, series, amount, fuzzy, gate)

    scores = {name: _cluster_scores(score_rows, name)
              for name in ("BASELINE", "EX_ANTE_GATE", "EX_ANTE_3F")}
    boot = _bootstrap(score_rows)
    calib = _calibration(score_rows)

    live = [c for c in clusters if not c.get("cluster_excluded")]
    rates = [c["cross_sectional_hit_rate"] for c in live
             if c["cross_sectional_hit_rate"] is not None]
    main_range = round(max(rates) - min(rates), 4) if rates else None
    sens_range = sens["cross_sectional_hit_rate_range"]
    beta = {
        "main_track_range": main_range,
        "sensitivity_track_range": sens_range,
        "criterion": "主轨极差 <= 0.02 且敏感性轨极差更大",
        "effective": bool(main_range is not None and main_range <= 0.02
                          and sens_range is not None and sens_range > main_range),
        "note": "结构性判据：只说明目标定义是否去掉市场共同因子，不代表规则有选择能力",
    }

    cov = mmeta["coverage"]
    total_obs = cov.get("OBSERVATIONS", 0)
    f3_one = cov.get("F3_ONE", 0)
    c1 = bool(total_obs > 0 and f3_one / total_obs >= 0.05)
    c2 = bool(mmeta["clusters_with_both_f3"] >= 20)
    c3 = bool(len(mmeta["series_with_f3_one"]) >= 5)
    effective_features = 3 if (c1 and c2 and c3) else 2

    h1 = next((t for t in boot["tests"] if t["name"] == "H1_3F_VS_BASELINE"), None)
    h2 = next((t for t in boot["tests"] if t["name"] == "H2_3F_VS_GATE"), None)
    gates = {
        "1_steps_ge_30": len(live) >= 30,
        "2_effective_features_ge_3": effective_features >= 3,
        "3_h1_passes": bool(h1 and h1["passes"]),
        "4_h2_passes": bool(h2 and h2["passes"]),
        "5_calibration_ok": calib["passes"],
        "6_trial_count_consistent": boot.get("trial_count") == TRIAL_COUNT,
    }
    all_pass = all(gates.values())

    comparable = sum(c["comparable_observations"] for c in clusters)
    gross = len(series) * len(mmeta["freezes"])
    excluded_total = sum(excluded.values())

    design_sha = _sha16(DESIGN)
    sources = [TD, SEM, RADAR, ROLES, TD_SCRIPT, DESIGN]

    doc = {
        "artifact": "historical_replay",
        "artifact_version": "0.2",
        "supersedes": "historical_replay_v0_1.json（逐字节保留，未覆盖）",
        "purpose": "历史冻结重放 v0.2：横截面中性化目标 + 第 3 信息侧特征 + "
                   "purge/embargo + cluster bootstrap + Holm + 早期敏感性对照；不建立验证过的预测模型",
        "design": "docs/HISTORICAL_REPLAY_DESIGN_v0_2.md",
        "design_sha256_16_locked": LOCKED_DESIGN_SHA16,
        "as_of": cal[-1],
        "benchmark": {"series_id": "CSI300", "price_type": "raw",
                      "first_date": cal[0], "last_date": cal[-1],
                      "trading_days": len(cal)},
        "freeze_schedule": {"pre_days": PRE_DAYS, "step_trading_days": STEP,
                            "horizon_trading_days": HORIZON,
                            "embargo_trading_days": EMBARGO,
                            "min_training_observations": MIN_TRAIN,
                            "min_cross_section": MIN_CROSS_SECTION,
                            "info_lookback_days": INFO_LOOKBACK_DAYS,
                            "freeze_points": len(mmeta["freezes"]),
                            "first": mmeta["freezes"][0], "last": mmeta["freezes"][-1]},
        "caliber_seven": {
            "target": "CROSS_SECTIONAL_OUTPERFORM：T+20 板块收益减去同簇全可比板块收益中位数 > 0",
            "sample_scope": "history_scan.db 的 241 行业板块 + 173 概念篮子；CSI300 日历；"
                            "冻结点从基准第 61 个交易日起、步长 60、窗口 20",
            "observation_window": "事前 T-60..T；结算 T+1..T+20；信息侧另回看 365 自然日",
            "denominator": "comparable===true；主统计按冻结日聚簇，逐观察数只报规模",
            "exclusions": dict(sorted(excluded.items())),
            "source": "scan_daily.close raw + CSI300 + board_semantics + theme_discovery 门槛 + "
                      "雷达与历史角色事件表；不取官方指数、不联网",
            "uncertainty": "比例给 95% Wilson（n=0→null）；主检验给 cluster bootstrap "
                           "95% / 97.5% 区间并做 Holm 修正",
        },
        "predictors": {
            "BASELINE": "purge 后全体可比观察的历史频率（climatology）",
            "EX_ANTE_GATE": "仅 F1 分组频率，分组训练不足回退 BASELINE",
            "EX_ANTE_3F": "F1×F2×F3 共 8 分组频率；NO_COVERAGE 或训练不足回退 BASELINE",
        },
        "ex_ante_features": {
            "F1_GATE_HIT": "价格侧：沿用已发布 market_gate 门槛",
            "F2_EXCESS20_SIGN": "价格侧：近 20 日相对 CSI300 超额 > 0",
            "F3_INFO_EVENT_365D": "信息侧：T 前 365 自然日内该板块是否有已登记可核事件；三态 0/1/NO_COVERAGE",
            "declared_count": 3,
            "effective_count": effective_features,
            "necessary_conditions": {
                "C1_coverage_ge_5pct": {"value": round(f3_one / total_obs, 6) if total_obs else None,
                                        "required": 0.05, "passes": c1},
                "C2_clusters_with_both_ge_20": {"value": mmeta["clusters_with_both_f3"],
                                                "required": 20, "passes": c2},
                "C3_distinct_series_ge_5": {"value": len(mmeta["series_with_f3_one"]),
                                            "required": 5, "passes": c3},
            },
            "verdict": "EFFECTIVE" if effective_features == 3 else "INSUFFICIENT_VARIATION",
            "note": "判定只由覆盖率与分布计算，不看任何收益结果；不足时有效特征数仍按 2 计",
        },
        "information_side": info_report,
        "information_coverage": {
            "observations_total": total_obs,
            "f3_one": f3_one,
            "f3_zero": cov.get("F3_ZERO", 0),
            "f3_no_coverage": cov.get("F3_NO_COVERAGE", 0),
            "identity": "OBSERVATIONS = F3_ONE + F3_ZERO + F3_NO_COVERAGE",
            "clusters_with_both_f3_values": mmeta["clusters_with_both_f3"],
            "distinct_series_with_f3_one": len(mmeta["series_with_f3_one"]),
            "f3_fallback_to_baseline": cov.get("F3_FALLBACK", 0),
            "f3_no_coverage_fallback": cov.get("F3_NO_COVERAGE_FALLBACK", 0),
            "gate_fallback_to_baseline": cov.get("GATE_FALLBACK", 0),
        },
        "historical_statistics": {
            "comparable_observations": comparable,
            "independent_clusters": len(live),
            "excluded_observations": excluded_total,
            "cross_sectional_hit_rate_by_cluster": {
                "min": min(rates) if rates else None,
                "max": max(rates) if rates else None,
                "mean": round(sum(rates) / len(rates), 4) if rates else None,
            },
            "description": "① 层历史统计描述；主统计按冻结日聚簇",
        },
        "scores": scores,
        "cluster_bootstrap": boot,
        "calibration": calib,
        "beta_neutralization": beta,
        "sensitivity_track": sens,
        "denominator_reconciliation": {
            "universe_series": len(series),
            "freeze_points": len(mmeta["freezes"]),
            "gross_observations": gross,
            "comparable": comparable,
            "excluded": excluded_total,
            "identity": "gross = comparable + excluded（杂项桶按每冻结点重复排除）",
        },
        "duplicate_dates": dup[:10],
        "duplicate_date_count": len(dup),
        "validated_model": False,
        "layer3_gate": {
            "required_walk_forward_steps": 30,
            "actual_steps": len(live),
            "required_ex_ante_features": 3,
            "actual_effective_ex_ante_features": effective_features,
            "conditions": gates,
            "meets_threshold": all_pass,
            "reason": "按设计 §8 六条逐项判定；任一不满足即维持③层不成立",
        },
        "limits": [
            "★ 行情描述统计，不参与「研究增量」验收；有效性仍需真实使用记录。",
            "★ 同一冻结日的板块共享市场冲击，不是独立样本；bootstrap 以整簇为重抽样单位。",
            "★ 横截面中性化只去掉市场共同因子，不等于规则具备板块选择能力。",
            "★ 阈值沿用已发布规则、本轮未调参；检验族与容差在跑 outcome 之前写死。",
            "★ ② 层经验基准概率**未校准**，仅限描述，不构成任何交易信号或标的清单。",
            "★ 信息侧事件覆盖有限且集中在后期；NO_COVERAGE 单独三态，不当作「无事件」。",
            "★ 敏感性对照轨 β 更重、样本更脏，只作摆动幅度对照，不作推断。",
            "★ 板块宇宙随时间扩张，早期冻结点可比序列少是数据边界，不补造。",
            "★ PBO 与 DSR 未估算 / 不适用，原因写在 cluster_bootstrap，不以其他指标冒充。",
        ],
        "clusters": clusters,
        "v0_1_baseline_sha256_16": {os.path.basename(p): _sha16(p)
                                    for p in (V01_DESIGN, V01_OUT, V01_SCRIPT)},
        "source_sha256_16": {os.path.basename(p): _sha16(p) for p in sources},
    }
    return doc


def _resolve_source(name):
    for base in (CURRENT, DOCS, SCRIPTS):
        p = os.path.join(base, name)
        if os.path.exists(p):
            return p
    return None


def check():
    """范围：设计指纹锁定 / v0.1 基线 / 上游对账 / PIT+embargo / 三态与分母守恒 /
    bootstrap 确定性 / Wilson / 禁用措辞。无大库时显式 SKIP 行情复算。"""
    errs, skips = [], []
    if not os.path.exists(OUT):
        print("FAIL 产物不存在：%s" % OUT)
        return 1
    doc = _load(OUT)

    # 1 · 设计文档指纹锁定（防事后改口径）
    if not os.path.exists(DESIGN):
        errs.append("设计文档缺失")
    else:
        actual = _sha16(DESIGN)
        if actual != LOCKED_DESIGN_SHA16:
            errs.append("设计文档已被改动（实际 %s / 锁定 %s）→ 改口径必须升版"
                        % (actual, LOCKED_DESIGN_SHA16))
        if doc.get("design_sha256_16_locked") != LOCKED_DESIGN_SHA16:
            errs.append("产物里的设计指纹与脚本锁定值不一致")
        decl = doc.get("source_sha256_16") or {}
        if decl.get("HISTORICAL_REPLAY_DESIGN_v0_2.md") != actual:
            errs.append("产物声明的设计文档指纹与实际不一致")

    # 2 · v0.1 基线逐字保留
    base = doc.get("v0_1_baseline_sha256_16") or {}
    for name, want in V01_BASELINE_SHA16.items():
        if base.get(name) != want:
            errs.append("产物记录的 v0.1 基线指纹异常：%s" % name)
        p = _resolve_source(name)
        if not p:
            errs.append("v0.1 基线文件缺失：%s" % name)
        elif _sha16(p) != want:
            errs.append("v0.1 基线文件已被覆盖：%s" % name)

    # 3 · 上游 sha256 声明 vs 实际
    for name, want in (doc.get("source_sha256_16") or {}).items():
        p = _resolve_source(name)
        if not p:
            skips.append("上游文件不在干净 checkout：%s" % name)
            continue
        if _sha16(p) != want:
            errs.append("上游指纹漂移：%s" % name)

    # 4 · 有库时逐字节重算（无库显式 SKIP）
    db_ok = os.path.exists(DB) and os.path.getsize(DB) > 0
    if db_ok:
        rebuilt = build()
        if json.dumps(rebuilt, ensure_ascii=False, sort_keys=True) != \
           json.dumps(doc, ensure_ascii=False, sort_keys=True):
            errs.append("产物与上游重算不一致（行情推进后需 --write）")
    else:
        skips.append("行情逐字节复算（缺 1.3 GB history_scan.db，CI 环境）")

    # 5 · PIT + embargo 不变量
    cl = doc.get("clusters") or []
    if not cl:
        errs.append("clusters 为空")
    else:
        dates = [c["freeze_date"] for c in cl]
        if dates != sorted(dates):
            errs.append("冻结点未严格递增")
        pools = [c["train_pool_size"] for c in cl]
        if pools[0] != 0:
            errs.append("首个冻结点训练池非空 → 未来信息泄漏")
        if pools != sorted(pools):
            errs.append("训练池大小非单调不减")
        if any(c.get("embargo_trading_days") != EMBARGO for c in cl):
            errs.append("embargo 声明与冻结值不一致")
        for c in cl:
            if c["train_pool_size"] > 0 and c["freeze_date"] == dates[0]:
                errs.append("首簇出现训练观察")

    # 6 · 三态 / 分母 / 逐簇守恒
    ic = doc.get("information_coverage") or {}
    if ic.get("observations_total") != (ic.get("f3_one", 0) + ic.get("f3_zero", 0)
                                        + ic.get("f3_no_coverage", 0)):
        errs.append("F3 三态计数不守恒")
    rec = doc.get("denominator_reconciliation") or {}
    if rec.get("gross_observations") != rec.get("comparable", 0) + rec.get("excluded", 0):
        errs.append("分母守恒不成立：gross != comparable + excluded")
    hs = doc.get("historical_statistics") or {}
    if hs.get("comparable_observations") != sum(c["comparable_observations"] for c in cl):
        errs.append("逐簇可比观察数之和与顶层不一致")
    for c in cl:
        if c.get("cluster_excluded"):
            continue
        if c["f3_one"] + c["f3_zero"] + c["f3_no_coverage"] != c["comparable_observations"]:
            errs.append("簇内 F3 三态不守恒：%s" % c["freeze_date"])
        if c["outcome_k"] > c["comparable_observations"]:
            errs.append("簇内 outcome_k 越界：%s" % c["freeze_date"])

    # 7 · bootstrap 确定性 / 检验族 / n=0 → null
    boot = doc.get("cluster_bootstrap") or {}
    if boot.get("B") != BOOTSTRAP_B or boot.get("seed") != BOOTSTRAP_SEED:
        errs.append("bootstrap B / seed 与冻结值不一致")
    if boot.get("trial_count") != TRIAL_COUNT:
        errs.append("trial_count 与预先注册不一致")
    if len(boot.get("tests") or []) != TRIAL_COUNT:
        errs.append("实际检验数不等于 trial_count（疑似事后加配置）")
    for t in boot.get("tests") or []:
        if t["ci95"][0] > t["ci95"][1] or t["ci975_holm"][0] > t["ci975_holm"][1]:
            errs.append("bootstrap 区间下界大于上界：%s" % t["name"])
        if t["passes"] != (t["holm_reject"] and t["holm_upper_lt_zero"]):
            errs.append("检验通过标记与 Holm / 区间判定不一致：%s" % t["name"])
    calib = doc.get("calibration") or {}
    for b in calib.get("bins") or []:
        if b["n"] == 0 and (b["mean_predicted"] is not None or b["observed_frequency"] is not None):
            errs.append("空箱未写 null：%s" % b["bin"])

    # 7.1 · 敏感性轨「声明起点 vs 落地日历」必须对账（全库实际早于 2010）
    st = doc.get("sensitivity_track") or {}
    if st.get("calendar_start_declared") != SENS_START:
        errs.append("敏感性轨未声明设计 §6 的起点 %s" % SENS_START)
    if st.get("calendar_first") and st["calendar_first"] < SENS_START:
        errs.append("敏感性轨落地日历早于声明起点：%s" % st["calendar_first"])
    if st.get("label") != "SENSITIVITY_ONLY":
        errs.append("敏感性轨未标注 SENSITIVITY_ONLY")

    # 8 · 三层口径与③层判定
    g3 = doc.get("layer3_gate") or {}
    if doc.get("validated_model") is not False:
        errs.append("validated_model 必须为 false")
    if g3.get("meets_threshold") != all(g3.get("conditions", {}).values()):
        errs.append("③ 层汇总判定与逐条条件不一致")
    if g3.get("meets_threshold") is True and doc.get("validated_model") is not False:
        errs.append("即使门槛全过，本产物也不得自动宣称模型已验证（须另行声明）")
    ef = (doc.get("ex_ante_features") or {}).get("effective_count")
    if g3.get("actual_effective_ex_ante_features") != ef:
        errs.append("③ 层有效特征数与特征判定不一致")

    # 9 · 禁用措辞与占位符
    blob = json.dumps(doc, ensure_ascii=False)
    for w in BANNED:
        if w in blob:
            errs.append("产物出现禁止措辞或占位符：%s" % w)

    if errs:
        for e in errs:
            print("FAIL " + e)
    for s in skips:
        print("SKIP " + s)
    if errs:
        print("--check：%d 项 FAIL · 范围：设计指纹 / v0.1 基线 / 上游对账 / "
              "PIT+embargo / 三态与分母守恒 / bootstrap / 三层口径 / 禁用措辞" % len(errs))
        return 1
    print("--check PASS · 范围：设计指纹锁定 %s / v0.1 基线 3 份 / 上游 %d 项 / "
          "PIT+embargo / 三态与分母守恒 / bootstrap B=%d / 三层口径 / 禁用措辞 · "
          "簇 %d · 可比观察 %d · SKIP %d 项"
          % (LOCKED_DESIGN_SHA16, len(doc.get("source_sha256_16") or {}),
             BOOTSTRAP_B, len(cl), hs.get("comparable_observations", 0), len(skips)))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="重算并写产物")
    ap.add_argument("--check", action="store_true", help="只读校验")
    a = ap.parse_args()
    if a.write:
        doc = build()
        _dump(OUT, doc)
        print("--write OK: %s · 簇 %d · 可比观察 %d"
              % (os.path.basename(OUT),
                 len([c for c in doc["clusters"] if not c.get("cluster_excluded")]),
                 doc["historical_statistics"]["comparable_observations"]))
        return 0
    return check()


if __name__ == "__main__":
    sys.exit(main())
