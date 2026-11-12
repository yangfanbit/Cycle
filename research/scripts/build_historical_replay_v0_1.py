#!/usr/bin/env python3
"""build_historical_replay_v0_1.py —— 历史冻结重放（v0.84，PIT / expanding window）。

## 为什么存在
使用者指出：回测不必等未来行情，可以把过去某段时间**封住**，只用 T 之前可得的数据
做预测，再用 T 之后的历史结算。本脚本把这条路线做成可复算的只读研究产物。

## 纪律（写脚本前已冻结在 docs/HISTORICAL_REPLAY_DESIGN_v0_1.md）
- 阈值沿用已发布的 `theme_discovery_v0_1.json:rules.market_gate`，**本轮不调参**；
  否则就是「先按全样本筛选再 walk-forward」的选择偏差。
- 每条预测只用**严格早于 T** 的已结算观察训练（expanding window）；结算窗口严格晚于 T。
- 观察单位按**冻结日聚簇**（同日几百个板块共享市场冲击，不是独立样本）。
- 二元比例给 95% Wilson，n=0 → null；只把 `comparable === true` 计入分母。
- 与简单历史基准比较，报 Brier / Log Loss / 校准 / 样本量；不做显著性检验。
- 三层口径分开：① 历史统计 ② 探索性经验基准概率（**未校准**）③ 无验证模型。
- 产物只给聚合统计，不给板块/个股清单；不与买卖措辞共现。

## 边界
- 只用库内 `history_scan.db` 的 raw 收盘与 `CSI300`，**不取官方指数**、不联网、不调 LLM；
  因此不触发官方指数取数的授权闸门。
- 无大库（CI）时 `--check` 显式 SKIP 行情复算并打印范围，形状/语义/禁用词照常校验。
- 不新增 CI Job；不修改任何既有产物（独立新文件）。

用法：--write / --check
"""
import argparse
import collections
import hashlib
import json
import math
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(ROOT, "research", "current")
DB = os.path.join(ROOT, "research", "database", "history_scan.db")
OUT = os.path.join(CURRENT, "historical_replay_v0_1.json")
SEM = os.path.join(CURRENT, "board_semantics_v0_1.json")
TD = os.path.join(CURRENT, "theme_discovery_v0_1.json")
DESIGN = os.path.join(ROOT, "docs", "HISTORICAL_REPLAY_DESIGN_v0_1.md")

PRE_DAYS = 60          # 事前特征窗口（共同交易日）
STEP = 60              # 冻结点步长（基准交易日），> HORIZON 保证窗口不重叠
HORIZON = 20           # 结算窗口（基准交易日）
MIN_TRAIN = 20         # 训练不足则该预测器 p=null
Z95 = 1.959963984540054

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
    """95% Wilson 区间；n=0 → (None, None, None)。"""
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


def load_market(con):
    """返回 (基准日历, 基准收盘, 序列收盘, 成交额代理, 序列名/类别)。
    ★ 日期一律归一；同一 (series_id, 归一日期) 若出现重复，记入 dup 并拒绝。
    """
    bench = {}
    for d, c in con.execute("select trade_date,close from scan_daily where series_id='CSI300'"):
        if c and c > 0:
            bench[norm_date(d)] = float(c)
    cal = sorted(bench)
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
    return cal, bench, series, amount, meta, dup


def features_at(sid, T, cal, idx, bench, series, amount):
    """只用 ≤T 的数据算两个事前特征。返回 (excess20, amt_ratio) 或 None。"""
    cl = series[sid]
    window = [d for d in cal[idx - PRE_DAYS:idx + 1] if d in cl and d in bench]
    if len(window) < PRE_DAYS:
        return None
    # 近 20 日 / 前 20 日
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
    return round(exc, 4), (round(ratio, 4) if ratio is not None else None)


def settle_at(sid, T, cal, idx, bench, series):
    """T+1..T+20 的累计相对超额（严格晚于 T）。返回 (ok, outcome, reason)。"""
    cl = series[sid]
    if T not in cl or T not in bench:
        return False, None, "NO_CLOSE_AT_T"
    post = cal[idx + 1:idx + 1 + HORIZON]
    if len(post) < HORIZON or post[-1] not in bench:
        return False, None, "INCOMPLETE_BENCH_WINDOW"
    end = post[-1]
    if end not in cl:
        return False, None, "NO_SERIES_AT_HORIZON"
    miss = [d for d in post if d not in cl]
    if miss:
        return False, None, "INCOMPLETE_SERIES_WINDOW"
    exc = ((cl[end] / cl[T] - 1) - (bench[end] / bench[T] - 1)) * 100
    return True, int(exc > 0), None


def build():
    if not os.path.exists(DB) or os.path.getsize(DB) == 0:
        raise RuntimeError("缺 history_scan.db（1.3 GB 未入库）→ 无法重放行情")
    td = _load(TD)
    gate = td["rules"]["market_gate"]
    abs_thr = float(gate["abs_excess20_pp_gt"])
    amt_thr = float(gate["amount_ratio_20_over_prev20_gt"])
    sem = _load(SEM)
    fuzzy = {e["series_id"] for e in (sem.get("entries") or []) if not e.get("interpretable")}

    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        cal, bench, series, amount, meta, dup = load_market(con)
    finally:
        con.close()

    freeze_idx = list(range(PRE_DAYS, len(cal) - HORIZON, STEP))
    freezes = [cal[i] for i in freeze_idx]

    # ★ 训练池按「结算完成日」严格早于当前冻结点：expanding window，PIT
    #   每条观察含 (gate_hit, outcome)，按完成日归档，供后续冻结点训练。
    train_pool = []            # [(settle_day_index, gate_hit, outcome)]
    clusters = []
    excluded = collections.Counter()
    all_obs_n = 0
    baseline_scored = 0
    gate_scored = 0
    fallback_count = 0
    score_rows = []            # (cluster, predictor, brier, logloss, p, o, bin)
    for i, T in zip(freeze_idx, freezes):
        # 只用「结算窗口完成日 < i」的历史观察训练（严格早于 T，无未来信息）
        hist = [x for x in train_pool if x[0] < i]
        all_hist = [x for x in hist]
        gate_hist = [x for x in hist if x[1]]
        nongate_hist = [x for x in hist if not x[1]]

        def freq(rows):
            if len(rows) < MIN_TRAIN:
                return None
            return sum(1 for x in rows if x[2] == 1) / len(rows)

        p_base = freq(all_hist)
        p_gate = freq(gate_hist)
        p_nongate = freq(nongate_hist)

        cluster_obs = []
        for sid in sorted(series):
            if sid in fuzzy:
                excluded["NOT_INTERPRETABLE"] += 1
                continue
            ok, outcome, reason = settle_at(sid, T, cal, i, bench, series)
            if not ok:
                excluded[reason] += 1
                continue
            feat = features_at(sid, T, cal, i, bench, series, amount)
            if feat is None:
                excluded["INSUFFICIENT_PRE_WINDOW"] += 1
                continue
            exc20, ratio = feat
            hit = (exc20 is not None and abs(exc20) > abs_thr) or \
                  (ratio is not None and ratio > amt_thr)
            cluster_obs.append({
                "series_id": sid, "gate_hit": bool(hit), "outcome": outcome,
                "features_ex_ante": {"excess_20_pp": exc20,
                                     "amount_ratio_20_over_prev20": ratio},
            })
        all_obs_n += len(cluster_obs)

        # 评分：两个预测器各自给概率（训练不足 → p=null，不计入评分）
        for o in cluster_obs:
            pg = p_gate if o["gate_hit"] else p_nongate
            used_fallback = False
            if pg is None and p_base is not None:
                pg, used_fallback = p_base, True
            if pg is not None:
                gate_scored += 1
                fallback_count += int(used_fallback)
                score_rows.append((T, "EX_ANTE_GATE", _brier(pg, o["outcome"]),
                                   _logloss(pg, o["outcome"]), pg, o["outcome"]))
            if p_base is not None:
                baseline_scored += 1
                score_rows.append((T, "BASELINE", _brier(p_base, o["outcome"]),
                                   _logloss(p_base, o["outcome"]), p_base, o["outcome"]))

        # 更新训练池：本簇的结算完成日 = i + HORIZON
        for o in cluster_obs:
            train_pool.append((i + HORIZON, o["gate_hit"], o["outcome"]))

        n = len(cluster_obs)
        gate_n = sum(1 for o in cluster_obs if o["gate_hit"])
        gate_k = sum(1 for o in cluster_obs if o["gate_hit"] and o["outcome"] == 1)
        all_k = sum(1 for o in cluster_obs if o["outcome"] == 1)
        clusters.append({
            "freeze_date": T,
            "comparable_observations": n,
            "gate_hit_observations": gate_n,
            "historical_frequency": {
                "all": {"k": all_k, "n": n,
                        "point": wilson(all_k, n)[0], "wilson95": wilson(all_k, n)[1:]},
                "gate_hit": {"k": gate_k, "n": gate_n,
                             "point": wilson(gate_k, gate_n)[0],
                             "wilson95": wilson(gate_k, gate_n)[1:]},
            },
            "train_pool_size": len(hist),
            "predictors": {"BASELINE": p_base,
                           "EX_ANTE_GATE_HIT": p_gate,
                           "EX_ANTE_GATE_MISS": p_nongate},
        })

    # ── 聚合（按冻结日聚簇，逐观察数只报规模） ──
    by_pred = collections.defaultdict(list)
    for row in score_rows:
        by_pred[row[1]].append(row)

    def cluster_scores(name):
        rows = by_pred.get(name, [])
        per = collections.defaultdict(list)
        for r in rows:
            per[r[0]].append(r)
        return {
            "scored_observations": len(rows),          # 规模，非独立样本
            "independent_clusters": len(per),          # 冻结日数
            "brier_mean_by_cluster": (round(sum(
                sum(r[2] for r in rs) / len(rs) for rs in per.values()) / len(per), 6)
                if per else None),
            "logloss_mean_by_cluster": (round(sum(
                sum(r[3] for r in rs) / len(rs) for rs in per.values()) / len(per), 6)
                if per else None),
        }

    scores = {name: cluster_scores(name) for name in ("BASELINE", "EX_ANTE_GATE")}

    # 簇级「gate 是否更优」：同一冻结日两预测器的簇均 Brier 对比
    per_cluster = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in score_rows:
        per_cluster[r[0]][r[1]].append(r[2])
    better = 0
    compared = 0
    for c, d in per_cluster.items():
        if "BASELINE" in d and "EX_ANTE_GATE" in d and d["BASELINE"] and d["EX_ANTE_GATE"]:
            compared += 1
            if sum(d["EX_ANTE_GATE"]) / len(d["EX_ANTE_GATE"]) < \
               sum(d["BASELINE"]) / len(d["BASELINE"]):
                better += 1
    k, n = better, compared
    pw, lo, hi = wilson(k, n)

    # 校准分箱（逐观察描述，明确非独立）
    bins = collections.defaultdict(lambda: {"n": 0, "sum_p": 0.0, "sum_o": 0})
    for r in score_rows:
        b = min(4, int(r[4] * 5))
        bins[b]["n"] += 1
        bins[b]["sum_p"] += r[4]
        bins[b]["sum_o"] += r[5]
    calibration = [{
        "bin": "%d/5" % b, "n": v["n"],
        "mean_predicted": round(v["sum_p"] / v["n"], 4),
        "observed_frequency": round(v["sum_o"] / v["n"], 4),
    } for b, v in sorted(bins.items())]

    # ── ② 层：探索性经验基准概率（未校准）──
    total_k = sum(c["historical_frequency"]["all"]["k"] for c in clusters)
    total_n = sum(c["historical_frequency"]["all"]["n"] for c in clusters)
    gate_total_k = sum(c["historical_frequency"]["gate_hit"]["k"] for c in clusters)
    gate_total_n = sum(c["historical_frequency"]["gate_hit"]["n"] for c in clusters)
    # ★★ 逐观察 Wilson 是**伪精度**（同日几百个板块共享市场冲击）。
    #    保留只为描述规模，明确标 non_independent / pseudo_precision，不作②层主口径。
    p2, lo2, hi2 = wilson(total_k, total_n)
    pg2, glo2, ghi2 = wilson(gate_total_k, gate_total_n)
    k3, n3 = better, compared
    p3, lo3, hi3 = wilson(k3, n3)
    # ② 层主口径：以「冻结日」为独立观察单位，统计 gate 组横截面命中率 > 全体的簇数
    gate_above = 0
    comparable_clusters = 0
    for c in clusters:
        ga = c["historical_frequency"]["gate_hit"]
        aa = c["historical_frequency"]["all"]
        if ga["n"] >= 10 and aa["n"] >= 10:
            comparable_clusters += 1
            if ga["point"] > aa["point"]:
                gate_above += 1
    pc, l_c, h_c = wilson(gate_above, comparable_clusters)
    # β 污染诊断：横截面命中率的簇间离散度
    cs = [c["historical_frequency"]["all"]["point"] for c in clusters
          if c["comparable_observations"] >= 10]
    beta_diag = {
        "cross_sectional_hit_rate_min": round(min(cs), 4) if cs else None,
        "cross_sectional_hit_rate_max": round(max(cs), 4) if cs else None,
        "cross_sectional_hit_rate_mean": round(sum(cs) / len(cs), 4) if cs else None,
        "interpretation": "横截面命中率簇间剧烈摆动 → 目标几乎由市场整体状态决定，"
                          "不是板块选择能力；逐观察比例不可当独立样本。",
    }

    doc = {
        "artifact": "historical_replay",
        "artifact_version": "0.1",
        "purpose": "历史冻结重放：验证事前特征规则在 PIT expanding-window 下的可核区分度；"
                   "不建立验证过的预测模型、不参与有效性验收",
        "design": "docs/HISTORICAL_REPLAY_DESIGN_v0_1.md",
        "as_of": cal[-1],
        "benchmark": {"series_id": "CSI300", "price_type": "raw",
                      "first_date": cal[0], "last_date": cal[-1],
                      "trading_days": len(cal)},
        "freeze_schedule": {"pre_days": PRE_DAYS, "step_trading_days": STEP,
                            "horizon_trading_days": HORIZON,
                            "min_training_observations": MIN_TRAIN,
                            "freeze_points": len(freezes),
                            "first": freezes[0], "last": freezes[-1]},
        "predictors": {
            "BASELINE": "严格早于 T 的已结算观察中 FORWARD_EXCESS_POSITIVE 的频率（climatology）",
            "EX_ANTE_GATE": "只用 ≤T 的两个事前特征分组的历史频率；分组训练不足回退 BASELINE",
        },
        "caliber_seven": {
            "target": "FORWARD_EXCESS_POSITIVE：T+20 相对 CSI300 累计超额 > 0（沿用既有 test_hit=ex>0）",
            "sample_scope": "history_scan.db 的 241 行业板块 + 173 概念篮子，"
                            "冻结点从基准第 61 个交易日起、步长 60、窗口 20",
            "observation_window": "事前 T-60..T；结算 T+1..T+20（严格晚于 T）",
            "denominator": "comparable===true；主统计按冻结日聚簇，逐观察数只报规模",
            "exclusions": dict(sorted(excluded.items())),
            "source": "scan_daily.close raw（provider=sina）+ CSI300 + board_semantics_v0_1.json；"
                      "不取官方指数、不联网",
            "uncertainty": "二元比例一律 95% Wilson；n=0→null；样本相关，不做显著性检验",
        },
        "historical_statistics": {
            "comparable_observations": total_n,
            "independent_clusters": len(clusters),
            "all": {"k": total_k, "n": total_n, "point": p2,
                    "wilson95": [lo2, hi2],
                    "unit": "逐观察（非独立）", "non_independent": True,
                    "pseudo_precision": True,
                    "note": "同日板块共享市场冲击；此区间仅供描述规模，不作②层分母"},
            "gate_hit": {"k": gate_total_k, "n": gate_total_n, "point": pg2,
                         "wilson95": [glo2, ghi2],
                         "unit": "逐观察（非独立）", "non_independent": True,
                         "pseudo_precision": True},
            "by_cluster": {
                "unit": "冻结日（独立观察单位）",
                "comparable_clusters": len(clusters),
                "cross_sectional_hit_rate": beta_diag,
            },
            "description": "① 层历史统计描述；逐观察数只报规模，主统计按冻结日聚簇",
        },
        "exploratory_baseline_probability": {
            "layer": "②",
            "calibrated": False,
            "not_future_probability": True,
            "not_a_model": True,
            "primary_unit": "冻结日（独立观察单位）",
            "primary": {
                "name": "gate 组横截面命中率高于全体的冻结日占比",
                "k": gate_above, "n": comparable_clusters,
                "point": pc, "wilson95": [l_c, h_c],
            },
            "secondary_by_observation": {
                "all": {"k": total_k, "n": total_n, "point": p2, "wilson95": [lo2, hi2]},
                "gate_hit": {"k": gate_total_k, "n": gate_total_n, "point": pg2,
                             "wilson95": [glo2, ghi2]},
                "non_independent": True, "pseudo_precision": True,
                "note": "逐观察比例仅作规模描述，不作②层分母",
            },
            "gate_better_than_baseline_clusters": {"k": k3, "n": n3, "point": p3,
                                                   "wilson95": [lo3, hi3],
                                                   "unit": "Brier 逐簇比较（冻结日）"},
            "note": "探索性经验基准概率，未校准；仅限②层表述，不得外推或作结论性宣称",
        },
        "scores": scores,
        "calibration_bins": calibration,
        "scoring_coverage": {
            "baseline_scored_observations": baseline_scored,
            "gate_scored_observations": gate_scored,
            "gate_fallback_to_baseline": fallback_count,
            "note": "评分逐观察计算但按冻结日聚簇取均值；逐观察数非独立样本",
        },
        "excluded_observations": dict(sorted(excluded.items())),
        "denominator_reconciliation": {
            "universe_series": len(series),
            "freeze_points": len(freezes),
            "gross_observations": len(series) * len(freezes),
            "comparable": total_n,
            "excluded": sum(excluded.values()),
            "identity": "gross = comparable + excluded（杂项桶按每个冻结点重复排除，"
                        "不是一次性排除）",
        }, 
        "duplicate_dates": dup[:10],
        "duplicate_date_count": len(dup),
        "validated_model": False,
        "layer3_gate": {
            "required_walk_forward_steps": 30,
            "actual_steps": len(clusters),
            "required_ex_ante_features": 3,
            "actual_ex_ante_features": 2,
            "meets_threshold": len(clusters) >= 30 and 2 >= 3,
            "reason": "步数达标但事前特征仅 2 个，且未做样本外校准与多重检验修正 → ③ 层仍不成立",
        },
        "limits": [
            "★ 行情描述统计，不参与「研究增量」验收；有效性仍需真实使用记录。",
            "★ 同一冻结日的板块共享市场冲击，不是独立样本；② 层主口径按冻结日聚簇，"
            "逐观察 Wilson 明确标为伪精度，只作规模描述。",
            "★ 横截面命中率簇间剧烈摆动，说明目标几乎由市场整体状态决定（β 污染），"
            "不是板块选择能力；本轮未做板块中性化，结论不得外推。",
            "★ 阈值沿用已发布规则、本轮未调参；未做多重检验修正（DSR/PBO）。",
            "★ 探索性经验基准概率**未校准**，仅限②层表述，不构成任何买卖信号或标的清单。",
            "★ 板块宇宙随时间扩张，早期冻结点可比序列少是数据边界，不补造。",
            "★ 相对超额已减 β，但价格规则测出的延续不等于定性「成势」判据。",
        ],
        "clusters": clusters,
        "source_sha256_16": {os.path.basename(p): _sha16(p)
                             for p in (TD, SEM, DESIGN)},
    }
    return doc


def check():
    errs, skips = [], []
    if not os.path.exists(OUT):
        print("FAIL 产物不存在：%s" % OUT)
        return 1
    doc = _load(OUT)

    db_ok = os.path.exists(DB) and os.path.getsize(DB) > 0
    if db_ok:
        rebuilt = build()
        if json.dumps(rebuilt, ensure_ascii=False, sort_keys=True) != \
           json.dumps(doc, ensure_ascii=False, sort_keys=True):
            errs.append("产物与上游重算不一致（行情推进后需 --write）")
    else:
        skips.append("行情复算（缺 1.3 GB history_scan.db，CI 环境）")

    # 形状 / 语义不变量（不依赖大库）
    for p in (TD, SEM, DESIGN):
        k = os.path.basename(p)
        if doc["source_sha256_16"].get(k) != _sha16(p):
            errs.append("上游指纹漂移：%s" % k)
    h = doc["historical_statistics"]
    e = doc["exploratory_baseline_probability"]
    c = doc["caliber_seven"]
    if len(c) != 7:
        errs.append("口径七要素数量 != 7")
    if h["comparable_observations"] <= 0 or h["independent_clusters"] <= 0:
        errs.append("可比观察或独立簇为 0（不能静默通过）")
    if h["independent_clusters"] != len(doc["clusters"]):
        errs.append("independent_clusters 与 clusters 长度不一致")
    # ★★ 逐簇加总守恒（外部复核过，必须固化进 --check，防下次漂移）
    if sum(x["comparable_observations"] for x in doc["clusters"]) != \
       h["comparable_observations"]:
        errs.append("逐簇 n 之和 != comparable_observations")
    if sum(x["historical_frequency"]["all"]["k"] for x in doc["clusters"]) != \
       h["all"]["k"]:
        errs.append("逐簇 k 之和 != historical_statistics.all.k")
    if sum(doc["excluded_observations"].values()) != \
       sum(doc["caliber_seven"]["exclusions"].values()):
        errs.append("七要素里的排除计数与顶层排除计数不一致")
    if any(not isinstance(v, int) or v < 0
           for v in doc["excluded_observations"].values()):
        errs.append("排除计数含非整数或负值")
    dr = doc.get("denominator_reconciliation") or {}
    if dr.get("gross_observations") != dr.get("comparable", 0) + dr.get("excluded", 0):
        errs.append("分母守恒不成立：gross != comparable + excluded")
    if dr.get("comparable") != h["comparable_observations"] or \
       dr.get("freeze_points") != h["independent_clusters"]:
        errs.append("分母守恒里的 comparable / freeze_points 与统计层不一致")
    if e["calibrated"] is not False or e["not_future_probability"] is not True:
        errs.append("② 层未正确声明「未校准 / 非未来概率」")
    if e.get("primary_unit") != "冻结日（独立观察单位）":
        errs.append("② 层主口径必须是簇级（冻结日），不得用逐观察当分母")
    if e.get("primary", {}).get("n") is None or e["primary"]["n"] <= 0:
        errs.append("② 层主口径缺有效分母")
    if e.get("secondary_by_observation", {}).get("pseudo_precision") is not True:
        errs.append("逐观察 Wilson 未标注伪精度")
    if h["all"].get("non_independent") is not True or h["all"].get("pseudo_precision") is not True:
        errs.append("① 层逐观察统计未标注非独立 / 伪精度")
    if h["by_cluster"]["cross_sectional_hit_rate"]["cross_sectional_hit_rate_min"] is None:
        errs.append("缺 β 污染诊断（簇间横截面命中率）")
    if doc["validated_model"] is not False:
        errs.append("不得声称存在已验证预测模型")
    if doc["layer3_gate"]["meets_threshold"] is not False:
        errs.append("③ 层门槛判定错误（事前特征仅 2 个）")
    if doc["duplicate_date_count"] != 0:
        errs.append("归一后日期存在重复：%d" % doc["duplicate_date_count"])

    # Wilson 与 n=0→null
    for name, obj in (("all", h["all"]), ("gate_hit", h["gate_hit"])):
        p, lo, hi = wilson(obj["k"], obj["n"])
        if obj["point"] != p or obj["wilson95"] != [lo, hi]:
            errs.append("Wilson 区间不一致：%s" % name)
        if obj["n"] == 0 and obj["point"] is not None:
            errs.append("n=0 时 point 必须为 null：%s" % name)
    for pt in doc["clusters"]:
        a = pt["historical_frequency"]["all"]
        if a["n"] != pt["comparable_observations"]:
            errs.append("冻结日 %s 计数不自洽" % pt["freeze_date"])
        g = pt["historical_frequency"]["gate_hit"]
        if g["n"] != pt["gate_hit_observations"] or g["k"] > g["n"]:
            errs.append("冻结日 %s gate 计数不自洽" % pt["freeze_date"])
        # ★ PIT 不变量：训练池只能来自严格早于该冻结点的已结算观察
        if pt["freeze_date"] == doc["freeze_schedule"]["first"] and \
           pt["train_pool_size"] != 0:
            errs.append("首个冻结点不应有训练数据（未来信息泄漏）")
    if any(x["train_pool_size"] < 0 for x in doc["clusters"]):
        errs.append("训练池大小异常")
    # ★★ PIT 不变量：训练集严格早于冻结点 → train_pool_size 单调递增且等于此前簇观察之和
    pools = [x["train_pool_size"] for x in doc["clusters"]]
    if any(b < a for a, b in zip(pools, pools[1:])):
        errs.append("训练池非单调（可能有未来信息泄漏）")
    expected = 0
    for i, pt in enumerate(doc["clusters"]):
        if pt["train_pool_size"] != expected:
            errs.append("训练池与「严格早于 T 的已结算观察之和」不符：%s"
                        % pt["freeze_date"])
            break
        expected += pt["comparable_observations"]

    # 互斥：逐观察数 = BASELINE/gate 评分覆盖不得大于可比观察
    if doc["scoring_coverage"]["baseline_scored_observations"] > h["comparable_observations"]:
        errs.append("评分覆盖大于可比观察数")

    # 禁用措辞（说明性否定句除外：逐条检查，不允许出现任何命中）
    blob = json.dumps(doc, ensure_ascii=False)
    for w in BANNED:
        if w in blob:
            errs.append("出现禁止措辞或占位符：%s" % w)

    if errs:
        for x in errs:
            print("FAIL " + x)
        print("--check：%d 项 FAIL" % len(errs))
        return 1
    scope = "上游指纹 / 口径七要素 / Wilson / 互斥计数 / PIT 不变量 / 三层口径 / 禁用措辞"
    if skips:
        scope += "（SKIP：%s）" % "；".join(skips)
    print("--check PASS · 范围：%s · %d 冻结点 / %d 可比观察"
          % (scope, h["independent_clusters"], h["comparable_observations"]))
    return 0


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        d = build()
        _dump(OUT, d)
        print("--write OK · %d 冻结点 / %d 可比观察 · ③ 层门槛 %s"
              % (d["historical_statistics"]["independent_clusters"],
                 d["historical_statistics"]["comparable_observations"],
                 "达" if d["layer3_gate"]["meets_threshold"] else "未达"))
        return 0
    return check()


if __name__ == "__main__":
    sys.exit(main())
