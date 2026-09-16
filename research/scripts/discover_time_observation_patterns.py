#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""discover_time_observation_patterns.py —— Time Observation Discovery v0.3（全量历史扫描）。

## 这个脚本是什么

对 ThreeC **全部** 2018–2025 历史研究数据做一次**统一、可复现、可审计**的时间结构扫描，
产出一个 **Research Candidate Pool**（研究候选池），供后续 Product Review / Promotion 消费。

     exports/timeline_export_v1.json  +  research/database/cycle_research.db   （只读输入）
                          ↓  本脚本（discover 模式，只读）
     research/research/reports/time_observation_candidate_pool_v0_3.json       （候选池）
     research/research/reports/time_observation_candidate_pool_v0_3.csv        （人工浏览）

**这不是产品集成**：结果不进入 `src/`、不进入 Timeline、不进入 DB / schema.sql / canonical export / contracts。
`RESEARCH_ONLY` 与 `REJECTED` 一律不得进入 Timeline。

## v0.3 相对 v0.2 的唯一变化：canonical Macro Theme Resolution

v0.2 用 `direct` 口径（Macro Theme 名称是否**字面出现**在 `themes[]` 中）判定对象所属主题族；
v0.3 改用 canonical `resolved` 口径（`themes[]` 名称 → DB `themes` 表归一化 →
沿 `parent_theme_id` 上溯至根），实现见 `research/scripts/theme_taxonomy.py`。

- **动机**：`Historical_Coverage_Audit_v0_1.md` §2.2(d) 确认两种口径不等价，
  影响 4 个对象（`C-2019-AD` / `RC-2024-SECONDARY` / `RC-2020-PANDEMIC` / `RC-2021-TCM`），
  并指出这正是 v0.2 中 3 条候选被判「口径脆弱」的根本原因。
- **影响面**：仅 `theme_family_id` / `theme_family_count` / `theme_cycle_count` 等**归属与独立性指标**。
  锚点定义、窗口、集中度、复现率等**统计量一律不变**；TOP-01 走 `RULE` scope，不受影响。
- **未解析名称**不静默丢弃：`theme_resolution.unmatched_theme_names` 显式上报
  （当前唯一缺口 = `华为汽车`，即 `MEMORY.md` 已登记的 DEFER 项 `F7`）。
- **历史轮次可复现**：`--round 0.2` 可重新生成 v0.2 产物用于逐字节回归比对。

## 与 v0.1 / Phase 7.2 的关系

- 上游：`Seasonal_Observation_Pattern_Discovery_v0_1.md`（确立锚点口径与拒绝规则）、
  `Time_Observation_Pattern_Integration_v0_1.md` + `time_observation_patterns_v0_1.json`（canonical Artifact，TOP-01..04）。
- 本脚本是**发现层（discovery）**：不替换 canonical Artifact，而是把扫描面从「4 个主题族」扩到
  **全部 scope × 全部 lifecycle stage × 全部 transition × 全部 event type**，并补齐
  Phase-Transition / Holiday-relative / 主题族独立性 / 负对照 / 多重比较等 v0.1 未覆盖的维度。
- **TOP-01 回归**：本脚本必须复现 TOP-01 的核心数字（N=7 / 中心 06-11 / 窗口 05-27 ~ 06-26 / 复现 5/7），
  不一致即 FAIL（见 `--check`）。

## 扫描维度（六个 Pattern 类型）

1. `SEASONAL`               —— 绝对日历月份 / 季度聚集
2. `CALENDAR_DRIVEN`        —— 制度性固定节奏（财报窗口、政策会议、年度周期）
3. `INDUSTRY_EVENT_DRIVEN`  —— 行业固定事件（车展 / 发布会 / 行业大会）
4. `DATA_RELEASE_DRIVEN`    —— 产销 / 价格 / 出口 / 景气等数据披露节奏
5. `HOLIDAY_RELATIVE`       —— 相对春节 / 国庆 / 五一的偏移
6. `PHASE_TRANSITION`       —— **阶段迁移**（如 EARLY_SIGNAL→THEME_FORMING）的时间聚集

## 绝对 vs 相对（v0.2 关键升级）

每个候选同时计算两套特征并判定谁更有解释力：

- Absolute：`day_of_year`（闰年归一）→ 判定 `ABSOLUTE_CALENDAR`
- Relative：相对春节 / 国庆 / 五一的 `offset_days` → 判定 `EVENT_RELATIVE`

避免把「其实跟着春节 / 政策会议走」的规律误判成「六月季节性」。

## 统计口径（与 v0.1 保持连续，全部为描述统计）

- 日序 + 闰年归一；**环形（circular）跨度**用于跨年簇（12 月下旬 ~ 1 月上旬）
- 中心 = 中位数；窗口 = `median ± 1×MAD×1.4826`；并列保留 P25–P75 与月降级
- 集中度比率 = 观测跨度 ÷ 均匀期望跨度 `(N-1)/(N+1)×365`
- 集中度精确 p（**解析式，非随机**）：`P(range ≤ s) = N·r^(N-1) − (N-1)·r^N`，`r = s/365`
- 历史复现 = 落入窗口年数 ÷ 有效年数（**只描述过去**）
- 稳定性：年份前后两半中位位移（<21d STABLE / 21–44d MILD_DRIFT / ≥45d STRONG_DRIFT）
- 留一法（LOO）：逐点剔除后中心位移；`max_center_shift_days` / `median_center_shift_days`
- 主题族独立性：`theme_family_count` / `theme_cycle_count` / `campaign_count`

## 样本量与 Promotion Gate（宁少不多）

    N < 3            → INSUFFICIENT_DATA
    N = 3–4          → EXPLORATORY / RESEARCH_ONLY（不得进 Timeline）
    N >= 5           → 才允许进入候选统计池（≠ 自动进 Timeline）
    TIMELINE_CANDIDATE: N>=5 且 窗口可构建 且 集中度<=0.45 且 STABLE 且 无单年主导
                        且 theme_cycle_count>=3 且 机制>=MEDIUM
    REJECTED          : 单年主导 / 窗口不可构建（IQR>90d）/ N<3 之外的结构性伪规律

## 确定性（deterministic rerun）

不使用任何随机数：集中度 p 用解析式，负对照用全量枚举。
同输入 → 同输出，逐字节一致。

用法:
    python research/scripts/discover_time_observation_patterns.py            # 生成
    python research/scripts/discover_time_observation_patterns.py --check     # 校验逐字节一致
    python research/scripts/discover_time_observation_patterns.py --print     # 生成并打印摘要
    python research/scripts/discover_time_observation_patterns.py --round 0.2 # 复现历史轮次（回归比对）

退出码: 0 = 通过；1 = 自检 / TOP-01 回归失败（**不写文件**）。
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import sqlite3
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT_PATH = os.path.join(ROOT, "exports", "timeline_export_v1.json")
DB_PATH = os.path.join(ROOT, "research", "database", "cycle_research.db")
REPORTS_DIR = os.path.join(ROOT, "research", "research", "reports")
DEFAULT_ROUND = "0.3"


def _artifact_paths(round_):
    tag = "v" + round_.replace(".", "_")
    return (
        os.path.join(REPORTS_DIR, "time_observation_candidate_pool_%s.json" % tag),
        os.path.join(REPORTS_DIR, "time_observation_candidate_pool_%s.csv" % tag),
    )


OUT_JSON, OUT_CSV = _artifact_paths(DEFAULT_ROUND)

SNAPSHOT_DATE = "2026-09-16"
ARTIFACT_VERSION = DEFAULT_ROUND
RULESET_VERSION = "time-observation-discovery-" + DEFAULT_ROUND


def set_round(round_):
    """切换产物轮次（`--round 0.2` 可复现历史轮次，用于回归比对）。"""
    global ARTIFACT_VERSION, RULESET_VERSION, OUT_JSON, OUT_CSV
    ARTIFACT_VERSION = round_
    RULESET_VERSION = "time-observation-discovery-" + round_
    OUT_JSON, OUT_CSV = _artifact_paths(round_)


# v0.2 的 `direct` 口径开关：**仅供历史轮次逐字节回归比对**，不得用于新研究。
LEGACY_DIRECT_RESOLUTION = False


def set_legacy_direct_resolution(flag):
    global LEGACY_DIRECT_RESOLUTION
    LEGACY_DIRECT_RESOLUTION = bool(flag)


# canonical Macro Theme 解析（单一事实来源；见 research/scripts/theme_taxonomy.py）
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
import theme_taxonomy  # noqa: E402

# ---------------------------------------------------------------- 枚举（有限集）

PATTERN_TYPES = [
    "SEASONAL",
    "CALENDAR_DRIVEN",
    "INDUSTRY_EVENT_DRIVEN",
    "DATA_RELEASE_DRIVEN",
    "HOLIDAY_RELATIVE",
    "PHASE_TRANSITION",
    "UNKNOWN",
]

MECHANISMS = [
    "SEASONAL_DEMAND",
    "CALENDAR_DRIVEN",
    "POLICY_CADENCE",
    "REPORTING_CADENCE",
    "INDUSTRY_EVENT_CADENCE",
    "DATA_RELEASE_CADENCE",
    "HOLIDAY_RELATIVE",
    "PHASE_TRANSITION",
    "UNKNOWN",
]

MECHANISM_CONFIDENCE = ["HIGH", "MEDIUM", "LOW"]

PROMOTION_STATUSES = [
    "TIMELINE_CANDIDATE",
    "EXPLORATORY",
    "RESEARCH_ONLY",
    "REJECTED",
    "INSUFFICIENT_DATA",
]

SCOPE_TYPES = ["THEME_FAMILY", "RULE", "THEME", "ALL", "EVENT_TYPE"]

FORBIDDEN_FIELDS = [
    "future_probability",
    "confidence_percent",
    "expected_return",
    "win_rate",
    "buy_signal",
    "sell_signal",
    "target_price",
    "seasonality_score",
    "rating",
    "score",
]

# 面向用户文本中禁止出现的非否定语义
BANNED_PHRASES = ["买入", "卖出", "布局窗口", "最佳买点", "预测", "概率", "胜率", "涨幅预测"]

# ---------------------------------------------------------------- 生命周期枚举

# 导出 lifecycle 的阶段（ThreeC 真实定义，见 contracts/timeline_export_v1.md）
LC_STAGES = [
    "EARLY_SIGNAL",
    "THEME_FORMING",
    "BROAD_CONFIRMATION",
    "MAIN_RISE",
    "PEAK",
    "RETRACEMENT",
    "SECONDARY",
    "DECLINING",
    "FIRST_DECLINE",
    "MAIN_END",
]

# DB campaign_phases 的阶段（研究子系统自有口径）
DB_PHASES = ["startup", "acceleration", "main_rise", "diffusion", "retracement", "secondary_rally", "decline"]

# 阶段迁移（导出 lifecycle 口径）—— PHASE_TRANSITION 扫描对象
LC_TRANSITIONS = [
    ("EARLY_SIGNAL", "THEME_FORMING"),
    ("EARLY_SIGNAL", "BROAD_CONFIRMATION"),
    ("THEME_FORMING", "BROAD_CONFIRMATION"),
    ("THEME_FORMING", "PEAK"),
    ("BROAD_CONFIRMATION", "MAIN_RISE"),
    ("BROAD_CONFIRMATION", "PEAK"),
    ("MAIN_RISE", "PEAK"),
    ("PEAK", "MAIN_END"),
]

# 阶段迁移（DB campaign_phases 口径）
DB_TRANSITIONS = [
    ("startup", "main_rise"),
    ("main_rise", "retracement"),
    ("main_rise", "decline"),
]

# ---------------------------------------------------------------- 节假日表（公历日期，可审计）

SPRING_FESTIVAL = {
    2018: "2018-02-16",
    2019: "2019-02-05",
    2020: "2020-01-25",
    2021: "2021-02-12",
    2022: "2022-02-01",
    2023: "2023-01-22",
    2024: "2024-02-10",
    2025: "2025-01-29",
}
FIXED_HOLIDAYS = {
    "national_day": (10, 1),
    "may_day": (5, 1),
}

# ---------------------------------------------------------------- 主题族（复用既有 taxonomy，不新建）

THEME_FAMILY_BY_SCOPE = {
    "汽车": {"theme_family_id": "TH-AUTO", "display_name": "汽车"},
    "医药健康": {"theme_family_id": "TH-PHARMA", "display_name": "医药健康"},
}

# ---------------------------------------------------------------- 机制推断（声明式，可审计）

# 主题族 → 该族「研究观察起点」的机制画像。仅为**归类规则**，不是因果断言。
MECHANISM_PROFILE = {
    "TH-AUTO": {
        "mechanisms": ["CALENDAR_DRIVEN", "POLICY_CADENCE", "REPORTING_CADENCE", "DATA_RELEASE_CADENCE"],
        "confidence": "MEDIUM",
        "note": (
            "汽车主题族多机制叠加：年中稳增长政策节奏（国常会 / 财政部细则偏 5–6 月）+ "
            "A 股中报业绩预告披露日历（6 月中下旬密集）+ 月度产销与渗透率数据发布日历"
            "（次月中旬）+ 国际产业事件（特斯拉 Robotaxi / FSD 偏北半球夏季）。"
            "属 CALENDAR_DRIVEN 为主，**不是** SEASONAL_DEMAND。"
        ),
        "data_supported": [
            "2022-05-23 国常会阶段性减征乘用车购置税 600 亿元（仓库内 EV-2022-01）",
            "2022-05-31 财政部 / 税务总局购置税减半细则（EV-2022-02）",
            "A 股中报预告披露窗口为公开制度性日历",
        ],
        "post_hoc": ["「政策预期窗口」而非「政策发布日」的解读为事后假设"],
    },
    "TH-PHARMA": {
        "mechanisms": ["CALENDAR_DRIVEN", "POLICY_CADENCE"],
        "confidence": "LOW",
        "note": (
            "医药主题族的政策日期本身分散（集采 2018-12-17、科创板 2019-07-22、"
            "医保谈判 2019-11-28、中医药 2021-12-31），**不支持**任何单一月份的集中解释。"
        ),
        "data_supported": ["仓库内 EV-MED-01 / EV-MED-02 / EV-MED-03 / EV-MED-05 的政策日期分布"],
        "post_hoc": ["无"],
    },
}

# 事件类型 → 机制归类
EVENT_TYPE_MECHANISM = {
    "policy": (["POLICY_CADENCE", "CALENDAR_DRIVEN"], "MEDIUM"),
    "company": (["INDUSTRY_EVENT_CADENCE"], "LOW"),
    "market": (["UNKNOWN"], "LOW"),
    "macro": (["UNKNOWN"], "LOW"),
}


# ================================================================ 日期工具


def parse_iso(s):
    """严格解析 YYYY-MM-DD；失败返回 None。"""
    if not isinstance(s, str) or len(s) < 10:
        return None
    try:
        y, m, d = int(s[0:4]), int(s[5:7]), int(s[8:10])
    except ValueError:
        return None
    if not (1 <= m <= 12 and 1 <= d <= 31):
        return None
    return (y, m, d)


def is_leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


_PER_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_MD_TABLE = None


def md_table():
    """非闰年 365 天日序 → MM-DD 表（窗口边界统一按非闰年基准呈现）。"""
    global _MD_TABLE
    if _MD_TABLE is None:
        _MD_TABLE = []
        for m, n in enumerate(_PER_MONTH, start=1):
            for d in range(1, n + 1):
                _MD_TABLE.append("%02d-%02d" % (m, d))
    return _MD_TABLE


def doy_norm(ymd):
    """闰年归一日序（1–365）：3 月 1 日起 −1，使 06-18 在任何年份得到同一序数。"""
    y, m, d = ymd
    per = list(_PER_MONTH)
    if is_leap(y):
        per[1] = 29
    n = sum(per[: m - 1]) + d
    if m >= 3 and is_leap(y):
        n -= 1
    return n


def md_of_doy(n, L=365):
    """日序（1-based，与 doy_norm / doy_of_md 同口径）→ MM-DD（环形包裹）。"""
    return md_table()[(int(round(n)) - 1) % L]


def doy_of_md(md):
    m, d = int(md[0:2]), int(md[3:5])
    return sum(_PER_MONTH[: m - 1]) + d


def days_between(a, b):
    """两个 YYYY-MM-DD 之间的自然日差（b − a），用序数近似（不含时区）。"""
    ya, ma, da = parse_iso(a)
    yb, mb, db = parse_iso(b)
    return _ordinal(yb, mb, db) - _ordinal(ya, ma, da)


def _ordinal(y, m, d):
    """公历序数（days since 0000-03-01 近似），只用于差值比较。"""
    days = 0
    for yy in range(1, y):
        days += 366 if is_leap(yy) else 365
    per = list(_PER_MONTH)
    if is_leap(y):
        per[1] = 29
    days += sum(per[: m - 1]) + d
    return days


def circ_span(doys, L=365):
    """环形最小跨度 = L − 最大间隙。"""
    if len(doys) < 2:
        return 0.0
    s = sorted(doys)
    gaps = [((s[(i + 1) % len(s)] - s[i]) % L) for i in range(len(s))]
    return float(L - max(gaps))


def circ_center(doys, L=365):
    """环形簇中心 = 补弧中点（先找最大间隙，弧从其后续点起算）。"""
    if not doys:
        return None
    if len(doys) == 1:
        return float(doys[0])
    s = sorted(doys)
    gaps = [((s[(i + 1) % len(s)] - s[i]) % L) for i in range(len(s))]
    gi = gaps.index(max(gaps))
    start = s[(gi + 1) % len(s)]
    span = L - max(gaps)
    return (start + span / 2.0) % L


def analytic_span_p(span, n, L=365.0):
    """解析式：N 个均匀点落在长 L 上的跨度 ≤ span 的概率。

        P(range ≤ s) = N·r^(N-1) − (N−1)·r^N,  r = s/L

    这是**解析式**（非随机模拟），保证确定性。仅作发现阶段诊断，不是确认性检验。
    """
    if n < 2:
        return None
    r = max(0.0, min(1.0, float(span) / L))
    return n * (r ** (n - 1)) - (n - 1) * (r ** n)


# ================================================================ 统计引擎


def median_f(xs):
    return statistics.median(sorted(xs))


def mad_f(xs, center):
    return statistics.median([abs(x - center) for x in xs])


def quantiles(xs, n=4):
    s = sorted(xs)
    if len(s) >= 4:
        q = statistics.quantiles(s, n=n, method="inclusive")
        return q[0], q[2]
    return float(s[0]), float(s[-1])


def compute_core(doys):
    """核心描述统计（线性 + 环形双口径）。"""
    n = len(doys)
    s = sorted(doys)
    med = median_f(s)
    center = int(round(med))
    m = mad_f(s, center)
    p25, p75 = quantiles(s)
    iqr = p75 - p25
    lin_span = float(s[-1] - s[0])
    cspan = circ_span(s)
    ccenter = circ_center(s)

    # 环形跨度显著更小时，采用环形口径（跨年簇）
    circular_used = cspan < lin_span - 30.0 and n >= 2
    span = cspan if circular_used else lin_span
    center_used = int(round(ccenter)) if circular_used else center

    uniform_span = (n - 1) / (n + 1) * 365.0 if n >= 2 else 0.0
    ratio = (span / uniform_span) if uniform_span else None

    return {
        "n": n,
        "doys": s,
        "median_doy": med,
        "center_doy": center_used,
        "center_md": md_of_doy(center_used),
        "linear_center_md": md_of_doy(center),
        "mad": m,
        "mad_days": int(round(m)),
        "p25_md": md_of_doy(p25),
        "p75_md": md_of_doy(p75),
        "iqr_days": round(iqr, 2),
        "linear_span_days": lin_span,
        "circular_span_days": cspan,
        "span_days": round(span, 2),
        "circular_window_used": bool(circular_used),
        "uniform_expected_span_days": round(uniform_span, 2),
        "concentration_ratio": round(ratio, 4) if ratio is not None else None,
        "span_p_analytic": round(analytic_span_p(span, n), 6) if n >= 2 else None,
        "earliest_md": md_of_doy(s[0]),
        "latest_md": md_of_doy(s[-1]),
        "month_distribution": _month_dist(s),
        "quarter_distribution": _quarter_dist(s),
    }


def _month_dist(doys):
    out = {}
    for x in doys:
        m = md_of_doy(x)[0:2]
        out[m] = out.get(m, 0) + 1
    return dict(sorted(out.items()))


def _quarter_dist(doys):
    out = {}
    for x in doys:
        q = "Q%d" % ((int(md_of_doy(x)[0:2]) - 1) // 3 + 1)
        out[q] = out.get(q, 0) + 1
    return dict(sorted(out.items()))


def build_window(center_doy, mad, k=1.0, L=365):
    """窗口半径 = round(1.4826 × MAD × k)；MAD 用浮点（不先取整，避免人为放宽）。"""
    half = int(round(1.4826 * mad * k))
    return (center_doy - half) % L, (center_doy + half) % L, half


def window_recurrence(doys, center, mad, L=365):
    """窗口命中情况。跨年窗口按环形判定。"""
    ws, we, half = build_window(center, mad, L=L)
    hits, miss = [], []
    for i, d in enumerate(doys):
        if _in_circ_window(d, ws, we, L):
            hits.append(i)
        else:
            miss.append(i)
    return {
        "start": md_of_doy(ws, L),
        "end": md_of_doy(we, L),
        "radius_days": half,
        "width_days": 2 * half + 1,
        "hit_indices": hits,
        "miss_indices": miss,
        "hits": len(hits),
        "n": len(doys),
    }


def _in_circ_window(d, ws, we, L=365):
    if ws <= we:
        return ws <= d <= we
    return d >= ws or d <= we  # 跨年


def stability_split(records, L=365):
    """前后半段中位位移（N<4 不做：位移对单点过于敏感）。"""
    n = len(records)
    if n < 4:
        return {
            "status": "INSUFFICIENT_N",
            "note": "N<4，不做前后半段检验（位移对单点过于敏感）。",
        }
    half = n // 2
    first, second = records[:half], records[half:]
    f1 = median_f([r["doy"] for r in first])
    f2 = median_f([r["doy"] for r in second])
    shift = f2 - f1
    if abs(shift) >= 45:
        flag = "STRONG_DRIFT"
    elif abs(shift) >= 21:
        flag = "MILD_DRIFT"
    else:
        flag = "STABLE"
    return {
        "status": "SPLIT",
        "front_back": flag,
        "drift_flag": flag,
        "first_years": [r["year"] for r in first],
        "second_years": [r["year"] for r in second],
        "front_center_md": md_of_doy(int(round(f1)), L),
        "back_center_md": md_of_doy(int(round(f2)), L),
        "median_shift_days": round(shift, 1),
        "note": "|位移| ≥ 45d → STRONG_DRIFT；21–44d → MILD_DRIFT；< 21d → STABLE。",
    }


def loo_stats(records, L=365):
    """留一法：逐点剔除重算中心，判断是否由单一年份主导。

    判据：`max_center_shift_days >= 45` → single_year_dominance。
    （命中数变化只作参考 —— 窗口宽度随样本重算变化，边缘年份会跳动 1–2 个，属边缘效应。）
    """
    n = len(records)
    if n < 3:
        return {
            "status": "INSUFFICIENT_N",
            "loo_max_shift_days": None,
            "loo_median_shift_days": None,
            "single_year_dominance": None,
            "note": "N<3，留一法无意义。",
        }
    base = compute_core([r["doy"] for r in records])
    shifts = []
    for i in range(n):
        rest = [r for j, r in enumerate(records) if j != i]
        if len(rest) < 2:
            continue
        c = compute_core([r["doy"] for r in rest])
        shifts.append(abs(c["center_doy"] - base["center_doy"]))
    max_shift = max(shifts) if shifts else 0.0
    med_shift = median_f(shifts) if shifts else 0.0
    return {
        "status": "OK",
        "loo_max_shift_days": round(float(max_shift), 1),
        "loo_median_shift_days": round(float(med_shift), 1),
        "single_year_dominance": bool(max_shift >= 45),
        "note": "判据：剔除任一年后中心位移 ≥ 45 天 → 结果由单一年份主导（不构成时间规律）。",
    }


def holiday_offsets(records):
    """相对节假日偏移（春节 / 国庆 / 五一）。"""
    out = {"spring_festival": [], "national_day": [], "may_day": []}
    for r in records:
        y = r["date"][0:4]
        yi = int(y)
        sf = SPRING_FESTIVAL.get(yi)
        if sf:
            out["spring_festival"].append({"year": r["year"], "offset_days": days_between(sf, r["date"])})
        for key, (m, d) in FIXED_HOLIDAYS.items():
            ref = "%04d-%02d-%02d" % (yi, m, d)
            out[key].append({"year": r["year"], "offset_days": days_between(ref, r["date"])})
    return out


def relative_vs_absolute(records, offsets, L=365):
    """§八：判定 ABSOLUTE_CALENDAR vs EVENT_RELATIVE 谁更有解释力。"""
    if len(records) < 3:
        return {"feature_winner": None, "note": "N<3，不做绝对 / 相对比较。"}
    abs_span = circ_span([r["doy"] for r in records], L)
    n = len(records)
    uniform_span = (n - 1) / (n + 1) * 365.0

    best = None
    for key in ("spring_festival", "national_day", "may_day"):
        offs = [o["offset_days"] for o in offsets.get(key) or []]
        if len(offs) < 3:
            continue
        span = float(max(offs) - min(offs))
        ratio = span / uniform_span if uniform_span else None
        if best is None or (ratio is not None and ratio < best["ratio"]):
            best = {"holiday": key, "span_days": round(span, 2), "ratio": round(ratio, 4)}

    abs_ratio = abs_span / uniform_span if uniform_span else None
    MARGIN = 0.8  # 相对 / 绝对须有 ≥20% 的比率优势才算「更有解释力」，避免技术性胜出
    if best is None:
        winner = "ABSOLUTE_CALENDAR"
        note = "无可用节假日偏移样本 → 以绝对日历口径为准。"
    elif abs_ratio is not None and best["ratio"] is not None and best["ratio"] <= MARGIN * abs_ratio:
        winner = "EVENT_RELATIVE"
        note = (
            "节假日偏移比率 %.4f（%s）≤ 绝对日序比率 %.4f 的 80%% → **相对事件日期更有解释力**，"
            "不应表述为绝对月份季节性。" % (best["ratio"], best["holiday"], abs_ratio)
        )
    elif abs_ratio is not None and best["ratio"] is not None and abs_ratio <= MARGIN * best["ratio"]:
        winner = "ABSOLUTE_CALENDAR"
        note = (
            "绝对日序跨度比率 %.4f ≤ 最优节假日偏移比率 %.4f（%s）的 80%% → 绝对日历更有解释力。"
            % (abs_ratio, best["ratio"], best["holiday"])
        )
    else:
        winner = "INCONCLUSIVE_SIMILAR"
        note = (
            "绝对日序比率 %s 与最优节假日偏移比率 %s（%s）差异不足 20%% → **两者都不构成集中**，"
            "不应声称任何一方更有解释力。" % (abs_ratio, best["ratio"] if best else None, best["holiday"] if best else None)
        )
    return {
        "feature_winner": winner,
        "absolute_span_ratio": round(abs_ratio, 4) if abs_ratio is not None else None,
        "best_relative": best,
        "margin_threshold": MARGIN,
        "note": note,
    }


# ================================================================ 数据装载


def load_export():
    with io.open(EXPORT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def db_phases(conn):
    cur = conn.cursor()
    cur.execute("SELECT campaign_id, phase_type, start_date, end_date FROM campaign_phases ORDER BY campaign_id, start_date")
    out = {}
    for r in cur.fetchall():
        out.setdefault(r[0], []).append({"phase_type": r[1], "start_date": r[2], "end_date": r[3]})
    return out


def db_events(conn):
    cur = conn.cursor()
    cur.execute("SELECT event_id, date, name, event_type FROM events ORDER BY date")
    return [
        {"event_id": r[0], "date": r[1], "name": r[2], "event_type": r[3]} for r in cur.fetchall()
    ]


def db_annual(conn):
    cur = conn.cursor()
    cur.execute("SELECT rule_id, year, status FROM annual_reviews ORDER BY year")
    return [{"rule_id": r[0], "year": r[1], "status": r[2]} for r in cur.fetchall()]


def db_macro_themes(conn):
    cur = conn.cursor()
    cur.execute("SELECT theme_id, name FROM themes WHERE parent_theme_id IS NULL")
    return {r[0]: r[1] for r in cur.fetchall()}


def db_all_themes(conn):
    cur = conn.cursor()
    cur.execute("SELECT theme_id, name, theme_type, parent_theme_id FROM themes ORDER BY theme_id")
    return [
        {"theme_id": r[0], "name": r[1], "theme_type": r[2], "parent_theme_id": r[3]}
        for r in cur.fetchall()
    ]


def macro_theme_of(obj, tax):
    """对象所属 Macro Theme —— **canonical 解析**（CMTR v1，见 `theme_taxonomy.py`）。

    口径：`themes[]` 名称 → DB `themes` 表归一化为 theme_id → 沿 `parent_theme_id` 上溯至根。

    **不再**使用 `direct`（Macro Theme 名称字面出现在 `themes[]` 中）口径 ——
    该口径会把「只登记子主题」的对象误判为「无 Macro Theme」。
    实测受影响对象 4 个：`C-2019-AD` / `RC-2024-SECONDARY` / `RC-2020-PANDEMIC` / `RC-2021-TCM`
    （见 `Historical_Coverage_Audit_v0_1.md` §2.2(d)）。

    `CONFLICT`（跨 Macro Theme）返回 None —— 不可归属，不得任选其一。
    """
    if LEGACY_DIRECT_RESOLUTION:
        return _legacy_direct_macro_theme_of(obj)
    return tax.macro_theme_id_of(obj)


def _legacy_direct_macro_theme_of(obj):
    """v0.2 的 `direct` 口径（**已废弃**，仅保留用于历史轮次回归比对）。

    判定方式：Macro Theme 名称是否**字面出现**在对象的 `themes[]` 中。
    该口径会把只登记子主题的对象误判为「无 Macro Theme」。
    """
    names = {t.get("name") for t in (obj.get("themes") or [])}
    for disp, meta in THEME_FAMILY_BY_SCOPE.items():
        if meta["display_name"] in names:
            return meta["theme_family_id"]
    return None


def sub_theme_names(obj):
    return [t.get("name") for t in (obj.get("themes") or [])]


# ================================================================ 数据集构建


def build_objects(export, tax):
    """全量对象（Campaign + Research Candidate）。"""
    objs = []
    for kind, key in (("campaign", "campaigns"), ("research_candidate", "research_candidates")):
        for o in export.get(key) or []:
            cid = o.get("campaign_id")
            if not cid:
                continue
            res = tax.resolve_object(o)
            if LEGACY_DIRECT_RESOLUTION:
                _m = _legacy_direct_macro_theme_of(o)
                fam_ids = [_m] if _m else []
                fam_status = "LEGACY_DIRECT"
            else:
                fam_ids = res["macro_theme_ids"]
                fam_status = res["status"]
            objs.append(
                {
                    "kind": kind,
                    "campaign_id": cid,
                    "title": o.get("title") or cid,
                    "year": o.get("year"),
                    "rule_id": o.get("rule_id"),
                    "theme_cycle_id": o.get("theme_cycle_id"),
                    "theme_family_id": fam_ids[0] if len(fam_ids) == 1 else None,
                    "theme_family_ids": fam_ids,
                    "theme_resolution": fam_status,
                    "theme_names": sub_theme_names(o),
                    "research_status": o.get("research_status"),
                    "lifecycle": o.get("lifecycle") or [],
                    "start_date": o.get("start_date"),
                    "peak_date": o.get("peak_date"),
                    "end_date": o.get("end_date"),
                    "classification": o.get("classification"),
                    "strength": o.get("strength"),
                    "raw": o,
                }
            )
    return objs


def build_anchor_records(objs):
    """(scope-agnostic) 全量锚点记录：每个对象 × 每个 lifecycle 阶段一条。"""
    recs = []
    for o in objs:
        for l in o["lifecycle"]:
            st = l.get("stage")
            sd = l.get("start")
            if not st or not sd or parse_iso(sd) is None:
                continue
            recs.append(
                {
                    "object": o,
                    "campaign_id": o["campaign_id"],
                    "theme_cycle_id": o["theme_cycle_id"],
                    "theme_family_id": o["theme_family_id"],
                    "rule_id": o["rule_id"],
                    "theme_names": o["theme_names"],
                    "kind": o["kind"],
                    "stage": st,
                    "anchor_type": st,
                    "date": sd,
                    "calendar_year": int(sd[0:4]),
                    "year": int(sd[0:4]),
                    "doy": doy_norm(parse_iso(sd)),
                    "precision": l.get("precision"),
                    "source": "export.lifecycle[%s].start" % st,
                }
            )
        # Campaign start（仅当 lifecycle 无同名阶段时补充，避免重复）
        if o["start_date"] and parse_iso(o["start_date"]):
            if not any(l.get("stage") == "EARLY_SIGNAL" and l.get("start") == o["start_date"] for l in o["lifecycle"]):
                recs.append(
                    {
                        "object": o,
                        "campaign_id": o["campaign_id"],
                        "theme_cycle_id": o["theme_cycle_id"],
                        "theme_family_id": o["theme_family_id"],
                        "rule_id": o["rule_id"],
                        "theme_names": o["theme_names"],
                        "kind": o["kind"],
                        "stage": "CAMPAIGN_START",
                        "anchor_type": "CAMPAIGN_START",
                        "date": o["start_date"],
                        "calendar_year": int(o["start_date"][0:4]),
                        "year": int(o["start_date"][0:4]),
                        "doy": doy_norm(parse_iso(o["start_date"])),
                        "precision": "EXACT_DATE",
                        "source": "export.campaigns[].start_date",
                    }
                )
    return recs


def build_transition_records(objs):
    """生命周期阶段迁移记录（PHASE_TRANSITION）。transition_date = to_stage.start。"""
    recs = []
    for o in objs:
        stages = {}
        for l in o["lifecycle"]:
            if l.get("stage") and l.get("start") and parse_iso(l["start"]):
                stages.setdefault(l["stage"], l["start"])
        for a, b in LC_TRANSITIONS:
            if a in stages and b in stages:
                da, db = stages[a], stages[b]
                if db < da:
                    continue
                recs.append(
                    {
                        "object": o,
                        "campaign_id": o["campaign_id"],
                        "theme_cycle_id": o["theme_cycle_id"],
                        "theme_family_id": o["theme_family_id"],
                        "rule_id": o["rule_id"],
                        "theme_names": o["theme_names"],
                        "kind": o["kind"],
                        "stage": "%s->%s" % (a, b),
                        "from_stage": a,
                        "to_stage": b,
                        "date": db,
                        "duration_days": days_between(da, db),
                        "year": int(db[0:4]),
                        "doy": doy_norm(parse_iso(db)),
                        "source": "export.lifecycle[%s].start − [%s].start" % (b, a),
                    }
                )
    return recs


def build_db_phase_records(objs, phases):
    """DB campaign_phases 口径的阶段起点与迁移（补充口径，独立记录）。"""
    starts, trans = [], []
    by_id = {o["campaign_id"]: o for o in objs}
    for cid, rows in phases.items():
        o = by_id.get(cid)
        if not o:
            continue
        first = {}
        for r in rows:
            pt, sd = r["phase_type"], r["start_date"]
            if not sd or parse_iso(sd) is None:
                continue
            first.setdefault(pt, sd)
            starts.append(
                {
                    "object": o,
                    "campaign_id": cid,
                    "theme_cycle_id": o["theme_cycle_id"],
                    "theme_family_id": o["theme_family_id"],
                    "rule_id": o["rule_id"],
                    "theme_names": o["theme_names"],
                    "kind": o["kind"],
                    "stage": "PHASE_" + pt.upper(),
                    "date": sd,
                    "year": int(sd[0:4]),
                    "doy": doy_norm(parse_iso(sd)),
                    "source": "cycle_research.db:campaign_phases(%s)" % pt,
                }
            )
        for a, b in DB_TRANSITIONS:
            if a in first and b in first and first[b] >= first[a]:
                db = first[b]
                trans.append(
                    {
                        "object": o,
                        "campaign_id": cid,
                        "theme_cycle_id": o["theme_cycle_id"],
                        "theme_family_id": o["theme_family_id"],
                        "rule_id": o["rule_id"],
                        "theme_names": o["theme_names"],
                        "kind": o["kind"],
                        "stage": "%s->%s" % (a, b),
                        "from_stage": a,
                        "to_stage": b,
                        "date": db,
                        "duration_days": days_between(first[a], db),
                        "year": int(db[0:4]),
                        "doy": doy_norm(parse_iso(db)),
                        "source": "cycle_research.db:campaign_phases(%s→%s)" % (a, b),
                    }
                )
    return starts, trans


def build_event_records(export, db_ev):
    """事件记录（export 33 + DB 30，以 export 为准，DB 补充 event_type）。"""
    type_by_id = {e["event_id"]: e["event_type"] for e in db_ev}
    out = []
    for e in export.get("events") or []:
        d = e.get("date")
        if not d or parse_iso(d) is None:
            continue
        out.append(
            {
                "event_id": e.get("event_id"),
                "date": d,
                "name": e.get("name") or "",
                "event_type": e.get("event_type") or type_by_id.get(e.get("event_id")) or "unknown",
                "year": int(d[0:4]),
                "doy": doy_norm(parse_iso(d)),
                "source": "export.events",
            }
        )
    return out


# ================================================================ 扫描范围


def build_scopes(export, objs, themes):
    """扫描范围定义（全部 scope，不挑主题）。"""
    scopes = []
    # 1) Theme Family（Macro Theme）
    for disp, meta in THEME_FAMILY_BY_SCOPE.items():
        scopes.append(
            {
                "scope_type": "THEME_FAMILY",
                "scope_id": meta["theme_family_id"],
                "scope_name": meta["display_name"],
                "predicate": lambda o, fid=meta["theme_family_id"]: o["theme_family_id"] == fid,
                "stages": LC_STAGES,
                "transitions": LC_TRANSITIONS,
            }
        )
    # 2) Rule
    for r in export.get("rules") or []:
        rid = r.get("rule_id")
        scopes.append(
            {
                "scope_type": "RULE",
                "scope_id": rid,
                "scope_name": r.get("name") or rid,
                "predicate": lambda o, rr=rid: o["rule_id"] == rr,
                "stages": LC_STAGES,
                "transitions": LC_TRANSITIONS,
            }
        )
    # 3) ALL（跨族，用于检查「是否只有单族驱动」）
    scopes.append(
        {
            "scope_type": "ALL",
            "scope_id": "ALL",
            "scope_name": "全部历史对象",
            "predicate": lambda o: True,
            "stages": LC_STAGES,
            "transitions": LC_TRANSITIONS,
        }
    )
    # 4) Theme（子主题级；只扫主要阶段，避免组合爆炸）
    #    跳过已被 THEME_FAMILY 覆盖的 Macro Theme，避免同一集合被两个 scope 重复统计。
    family_ids = {meta["theme_family_id"] for meta in THEME_FAMILY_BY_SCOPE.values()}
    primary = ["EARLY_SIGNAL", "THEME_FORMING", "PEAK"]
    for t in themes:
        if t["theme_id"] in family_ids:
            continue
        scopes.append(
            {
                "scope_type": "THEME",
                "scope_id": t["theme_id"],
                "scope_name": t["name"],
                "predicate": lambda o, nm=t["name"]: nm in o["theme_names"],
                "stages": primary,
                "transitions": [],
            }
        )
    return scopes


def select_records(records, scope):
    """按 scope 过滤锚点记录。"""
    return [r for r in records if scope["predicate"](r["object"])]


def _scope_by_id(scopes, scope_id):
    for s in scopes:
        if s["scope_id"] == scope_id:
            return s
    raise SystemExit("FAIL —— 未找到 scope：%s" % scope_id)


# ================================================================ 候选构建


def dedup_by_year(records):
    """年度去重：同一日历年只取**最早**锚点（防止同年多对象人为放大 N）。"""
    by_year = {}
    for r in records:
        y = r["year"]
        cur = by_year.get(y)
        if cur is None or r["date"] < cur["date"]:
            by_year[y] = r
    return [by_year[y] for y in sorted(by_year)]


def mechanism_of(scope, stage, records):
    """机制归类（多选）+ 置信度；区分 data-supported 与 post-hoc。"""
    fam_ids = {r["theme_family_id"] for r in records if r["theme_family_id"]}
    mechs, conf, notes, supported, posthoc = [], "LOW", [], [], []

    for fid in sorted(fam_ids):
        prof = MECHANISM_PROFILE.get(fid)
        if not prof:
            continue
        for m in prof["mechanisms"]:
            if m not in mechs:
                mechs.append(m)
        supported.extend(prof["data_supported"])
        posthoc.extend(prof["post_hoc"])
        if prof["confidence"] == "MEDIUM" and conf == "LOW":
            conf = "MEDIUM"
        if prof["confidence"] == "HIGH":
            conf = "HIGH"
        notes.append("[%s] %s" % (fid, prof["note"]))

    if "->" in str(stage):
        if "PHASE_TRANSITION" not in mechs:
            mechs.append("PHASE_TRANSITION")
        conf = "MEDIUM" if conf == "LOW" else conf
        notes.append("阶段迁移本身的时间聚集 —— 与制度性 / 产业节奏耦合。")

    if not mechs:
        mechs = ["UNKNOWN"]
    return {
        "mechanisms": mechs,
        "mechanism_confidence": conf,
        "mechanism_note": " ".join(notes) if notes else "无可用机制画像，暂归 UNKNOWN。",
        "data_supported": supported,
        "post_hoc_hypothesis": posthoc,
    }


def classify_pattern_type(scope, stage, core, rel, mech):
    """六类 Pattern 分类。

    优先级：阶段迁移 → 相对节假日（需 N≥4 且优势明显）→ 机制画像 → 绝对日历。
    注意：本数据集中**没有**任何候选被归为 SEASONAL_DEMAND —— 找到的是日历规律，不是季节规律。
    """
    if "->" in str(stage) or "PHASE_" in str(stage):
        return "PHASE_TRANSITION"

    n = core["n"]
    # 相对节假日仅在「样本足够 + 优势 ≥20%」时才作为主分类（优势判定见 relative_vs_absolute）
    if rel.get("feature_winner") == "EVENT_RELATIVE" and n >= 4:
        return "HOLIDAY_RELATIVE"

    mset = set(mech["mechanisms"])
    if "POLICY_CADENCE" in mset or "REPORTING_CADENCE" in mset or "CALENDAR_DRIVEN" in mset:
        return "CALENDAR_DRIVEN"
    if "DATA_RELEASE_CADENCE" in mset:
        return "DATA_RELEASE_DRIVEN"
    if "INDUSTRY_EVENT_CADENCE" in mset:
        return "INDUSTRY_EVENT_DRIVEN"
    if core.get("concentration_ratio") is not None and core["concentration_ratio"] <= 0.6:
        return "SEASONAL"
    return "UNKNOWN"


def member_signature(records):
    """样本身份签名：同一签名 = 完全相同的底层观测集合（跨 scope 的重复口径）。"""
    key = "|".join(sorted("%s@%s" % (r.get("campaign_id") or r.get("event_id"), r["date"]) for r in records))
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def promotion_gate(core, stab, loo, independence, mech, rel):
    """Promotion Gate（§十八）。"""
    n = core["n"]
    ratio = core["concentration_ratio"]
    drift = stab.get("front_back")
    dominated = loo.get("single_year_dominance")
    window_buildable = n >= 3 and core["iqr_days"] <= 90.0
    cycle_count = independence["theme_cycle_count"]

    if n < 3:
        return {
            "promotion_status": "INSUFFICIENT_DATA",
            "reason": "N=%d < 3：样本不足以判断是否存在时间结构。" % n,
            "window_buildable": window_buildable,
        }

    if dominated is True:
        return {
            "promotion_status": "REJECTED",
            "reason": (
                "留一法显示结果由单一年份主导（最大中心位移 %s 天）→ 不构成时间规律。"
                % loo.get("loo_max_shift_days")
            ),
            "window_buildable": window_buildable,
        }

    if not window_buildable:
        return {
            "promotion_status": "REJECTED",
            "reason": (
                "IQR=%s 天 → 锚点跨三个以上季节，无法构建有意义的观察窗口（不得人为造窗口）。"
                % core["iqr_days"]
            ),
            "window_buildable": window_buildable,
        }

    if n < 5:
        status = "EXPLORATORY" if (ratio is not None and ratio <= 0.60) else "RESEARCH_ONLY"
        return {
            "promotion_status": status,
            "reason": (
                "N=%d 落在 3–4 区间 → 只允许 RESEARCH_ONLY / EXPLORATORY，不得进入 Timeline%s。"
                % (n, "（集中度尚可，标记为探索性）" if status == "EXPLORATORY" else "")
            ),
            "window_buildable": window_buildable,
        }

    # N >= 5
    if (
        ratio is not None
        and ratio <= 0.45
        and drift == "STABLE"
        and not dominated
        and cycle_count >= 3
        and mech["mechanism_confidence"] in ("MEDIUM", "HIGH")
    ):
        return {
            "promotion_status": "TIMELINE_CANDIDATE",
            "reason": (
                "N=%d ≥ 5；集中度比率 %s ≤ 0.45；前后半段 %s；留一法无单年主导；"
                "独立 Theme Cycle 数 %d ≥ 3；机制置信度 %s → 满足 Timeline 候选门槛。"
                % (n, ratio, drift, cycle_count, mech["mechanism_confidence"])
            ),
            "window_buildable": window_buildable,
        }

    if ratio is not None and ratio <= 0.60:
        return {
            "promotion_status": "EXPLORATORY",
            "reason": (
                "N=%d ≥ 5 且窗口可构建，但未全部满足门槛（集中度 %s / 漂移 %s / 独立 Cycle %d / 机制 %s）"
                "→ 探索性，暂不进 Timeline。" % (n, ratio, drift, cycle_count, mech["mechanism_confidence"])
            ),
            "window_buildable": window_buildable,
        }

    return {
        "promotion_status": "RESEARCH_ONLY",
        "reason": (
            "N=%d ≥ 5 但集中度比率 %s 不足（> 0.60）→ 时间分散，仅留研究层。"
            % (n, ratio)
        ),
        "window_buildable": window_buildable,
    }


def build_candidate(pid, scope, stage, records, pattern_kind):
    """构造一个候选（完整统计 + 判定 + 来源记录）。"""
    agg = dedup_by_year(records)
    doys = [r["doy"] for r in agg]
    core = compute_core(doys)
    stab = stability_split(agg)
    loo = loo_stats(agg)
    offsets = holiday_offsets(agg)
    rel = relative_vs_absolute(agg, offsets)
    mech = mechanism_of(scope, stage, agg)
    ptype = classify_pattern_type(scope, stage, core, rel, mech)

    fam_ids = sorted({r["theme_family_id"] for r in agg if r["theme_family_id"]})
    cycle_ids = sorted({r["theme_cycle_id"] for r in agg if r["theme_cycle_id"]})
    camp_ids = sorted({r["campaign_id"] for r in agg})
    independence = {
        "theme_family_count": len(fam_ids),
        "theme_family_names": fam_ids,
        "theme_cycle_count": len(cycle_ids),
        "theme_cycle_names": cycle_ids,
        "campaign_count": len(camp_ids),
        "single_family": len(fam_ids) <= 1,
        "single_cycle": len(cycle_ids) <= 1,
        "note": (
            "theme_family_count = 独立 Macro Theme 数；theme_cycle_count = 独立 Theme Cycle 数。"
            "N 相同但二者不同时，统计意义完全不同（N=8 全来自同一 Cycle ≠ N=8 来自 4 个独立族）。"
        ),
    }

    gate = promotion_gate(core, stab, loo, independence, mech, rel)
    win = None
    if gate["window_buildable"]:
        w = window_recurrence(doys, core["center_doy"], core["mad"])
        win = {
            "start": w["start"],
            "end": w["end"],
            "radius_days": w["radius_days"],
            "width_days": w["width_days"],
        }
        rec_count = w["hits"]
        rec_years = [agg[i]["year"] for i in w["hit_indices"]]
        miss_years = [agg[i]["year"] for i in w["miss_indices"]]
    else:
        rec_count, rec_years, miss_years = None, [], [r["year"] for r in agg]

    limitations = []
    if core["n"] < 5:
        limitations.append("N=%d < 5：样本不足，不得进入 Timeline。" % core["n"])
    if independence["single_family"]:
        limitations.append(
            "仅由 1 个 Macro Theme 族驱动（%s）→ 主题族独立性不足，无法排除「该族自身研究偏好」解释。"
            % (fam_ids[0] if fam_ids else "N/A")
        )
    if core["n"] >= 2 and core["circular_window_used"]:
        limitations.append("存在跨年簇 → 已用环形口径（跨年窗口需按两段渲染）。")
    if stab.get("front_back") in ("MILD_DRIFT", "STRONG_DRIFT"):
        limitations.append("前后半段存在 %s（位移 %s 天）→ 时间位置在漂移。" % (stab["front_back"], stab["median_shift_days"]))
    if mech["mechanism_confidence"] == "LOW":
        limitations.append("机制置信度 LOW：仅有事后假设，缺少仓库内数据支撑。")
    if rel.get("feature_winner") == "EVENT_RELATIVE":
        limitations.append("相对事件日期比绝对日历更有解释力 → 不得表述为绝对月份季节性。")
    limitations.append("全部锚点为研究候选日期，未经行情人工最终核验（verification_method 多为 unknown）。")
    limitations.append("ThreeC 只记录「形成 Campaign 的主题」→ 存在幸存者偏差（见 negative_control）。")

    source_records = [
        {
            "year": r["year"],
            "theme_cycle_id": r["theme_cycle_id"],
            "campaign_id": r["campaign_id"],
            "theme_family_id": r["theme_family_id"],
            "anchor_type": r.get("anchor_type") or r["stage"],
            "anchor_date": r["date"],
            "doy": r["doy"],
            "source": r.get("source"),
        }
        for r in agg
    ]

    return {
        "pattern_id": pid,
        "pattern_type": ptype,
        "pattern_kind": pattern_kind,
        "member_signature": member_signature(agg),
        "scope_type": scope["scope_type"],
        "scope_id": scope["scope_id"],
        "scope_name": scope["scope_name"],
        "name": "%s · %s" % (scope["scope_name"], stage),
        "lifecycle_stage": stage,
        "sample_size": core["n"],
        "years": [r["year"] for r in agg],
        "center_day_of_year": core["center_doy"],
        "center_date_label": core["center_md"],
        "window": win,
        "concentration_ratio": core["concentration_ratio"],
        "concentration_p_analytic": core["span_p_analytic"],
        "recurrence_count": rec_count,
        "recurrence_ratio": (
            round(rec_count / core["n"], 4) if rec_count is not None and core["n"] else None
        ),
        "recurrence_label": "历史样本中的窗口复现情况（不是未来概率）",
        "recurrence_years": rec_years,
        "missed_years": miss_years,
        "dispersion": {
            "iqr_days": core["iqr_days"],
            "mad_days": core["mad_days"],
            "linear_span_days": core["linear_span_days"],
            "circular_span_days": core["circular_span_days"],
            "span_days": core["span_days"],
            "circular_window_used": core["circular_window_used"],
            "earliest_md": core["earliest_md"],
            "latest_md": core["latest_md"],
            "month_distribution": core["month_distribution"],
            "quarter_distribution": core["quarter_distribution"],
        },
        "stability": {
            "front_back": stab.get("front_back"),
            "status": stab.get("status"),
            "front_center_md": stab.get("front_center_md"),
            "back_center_md": stab.get("back_center_md"),
            "median_shift_days": stab.get("median_shift_days"),
            "loo_max_shift_days": loo.get("loo_max_shift_days"),
            "loo_median_shift_days": loo.get("loo_median_shift_days"),
            "single_year_dominance": loo.get("single_year_dominance"),
        },
        "theme_family_count": independence["theme_family_count"],
        "theme_family_names": independence["theme_family_names"],
        "theme_cycle_count": independence["theme_cycle_count"],
        "campaign_count": independence["campaign_count"],
        "theme_family_independence": independence,
        "mechanisms": mech["mechanisms"],
        "mechanism_confidence": mech["mechanism_confidence"],
        "mechanism_note": mech["mechanism_note"],
        "mechanism_data_supported": mech["data_supported"],
        "mechanism_post_hoc": mech["post_hoc_hypothesis"],
        "absolute_vs_relative": rel,
        "holiday_offsets": offsets,
        "promotion_status": gate["promotion_status"],
        "promotion_reason": gate["reason"],
        "window_buildable": gate["window_buildable"],
        "limitations": limitations,
        "source_records": source_records,
    }


# ================================================================ 全量扫描


def run_scan(export, objs, anchors, transitions, db_starts, db_trans, events, themes):
    scopes = build_scopes(export, objs, themes)
    candidates = []
    counter = 0

    def next_id():
        nonlocal counter
        counter += 1
        return "TOPC-%03d" % counter

    # A) 锚点扫描：scope × lifecycle stage
    for scope in scopes:
        sel = select_records(anchors, scope)
        for stage in scope["stages"]:
            recs = [r for r in sel if r["stage"] == stage]
            if not recs:
                continue
            candidates.append(build_candidate(next_id(), scope, stage, recs, "LIFECYCLE_STAGE"))

    # B) 阶段迁移扫描：scope × transition
    for scope in scopes:
        if not scope["transitions"]:
            continue
        sel = select_records(transitions, scope)
        for a, b in scope["transitions"]:
            key = "%s->%s" % (a, b)
            recs = [r for r in sel if r["stage"] == key]
            if not recs:
                continue
            candidates.append(build_candidate(next_id(), scope, key, recs, "PHASE_TRANSITION"))

    # C) DB campaign_phases 口径（补充口径）
    for scope in scopes:
        sel = select_records(db_starts, scope)
        for pt in DB_PHASES:
            recs = [r for r in sel if r["stage"] == "PHASE_" + pt.upper()]
            if not recs:
                continue
            candidates.append(build_candidate(next_id(), scope, "PHASE_" + pt.upper(), recs, "DB_PHASE_START"))
        if scope["scope_type"] in ("THEME_FAMILY", "RULE", "ALL"):
            sel2 = select_records(db_trans, scope)
            for a, b in DB_TRANSITIONS:
                key = "%s->%s" % (a, b)
                recs = [r for r in sel2 if r["stage"] == key]
                if not recs:
                    continue
                candidates.append(build_candidate(next_id(), scope, "DB_" + key, recs, "DB_PHASE_TRANSITION"))

    # D) 事件类型扫描（EVENT_TYPE scope）
    etypes = sorted({e["event_type"] for e in events})
    for et in etypes:
        recs = [e for e in events if e["event_type"] == et]
        if not recs:
            continue
        scope = {
            "scope_type": "EVENT_TYPE",
            "scope_id": "EVT-" + et.upper(),
            "scope_name": "事件类型：%s" % et,
        }
        cand = build_event_candidate(next_id(), scope, et, recs)
        candidates.append(cand)

    # E) 全量事件（不分类型）
    if events:
        scope = {"scope_type": "EVENT_TYPE", "scope_id": "EVT-ALL", "scope_name": "全部事件"}
        candidates.append(build_event_candidate(next_id(), scope, "ALL_EVENTS", events))

    return scopes, candidates


def build_event_candidate(pid, scope, et, events):
    """事件候选：把事件日期当作「时点」做同一套统计（年度去重按事件年）。"""
    agg = dedup_by_year(events)
    doys = [r["doy"] for r in agg]
    core = compute_core(doys)
    stab = stability_split(agg)
    loo = loo_stats(agg)
    offsets = holiday_offsets(agg)
    rel = relative_vs_absolute(agg, offsets)
    mechs, conf = EVENT_TYPE_MECHANISM.get(et, (["UNKNOWN"], "LOW"))
    mech = {
        "mechanisms": list(mechs),
        "mechanism_confidence": conf,
        "mechanism_note": "事件台账的时间分布；仅描述仓库内已登记事件的月份集中情况。",
        "data_supported": ["cycle_research.db:events + export.events"],
        "post_hoc_hypothesis": [],
    }
    ptype = "CALENDAR_DRIVEN" if "POLICY_CADENCE" in mechs else "UNKNOWN"
    independence = {
        "theme_family_count": 0,
        "theme_family_names": [],
        "theme_cycle_count": 0,
        "theme_cycle_names": [],
        "campaign_count": 0,
        "single_family": True,
        "single_cycle": True,
        "note": "事件类型不隶属主题族；theme-family 独立性不适用。",
    }
    gate = promotion_gate(core, stab, loo, independence, mech, rel)
    # 事件类型不是「主题观察规律」，无论统计多强都不得进入 Timeline
    if gate["promotion_status"] == "TIMELINE_CANDIDATE":
        gate = {
            "promotion_status": "RESEARCH_ONLY",
            "reason": "事件台账本身是研究样本的一部分（存在选择偏差），不得作为主题观察规律进入 Timeline。",
            "window_buildable": gate["window_buildable"],
        }
    win = None
    if gate["window_buildable"]:
        w = window_recurrence(doys, core["center_doy"], core["mad"])
        win = {"start": w["start"], "end": w["end"], "radius_days": w["radius_days"], "width_days": w["width_days"]}
        rec_count = w["hits"]
        rec_years = [agg[i]["year"] for i in w["hit_indices"]]
        miss_years = [agg[i]["year"] for i in w["miss_indices"]]
    else:
        rec_count, rec_years, miss_years = None, [], [r["year"] for r in agg]

    return {
        "pattern_id": pid,
        "pattern_type": ptype,
        "pattern_kind": "EVENT_TYPE",
        "member_signature": member_signature(agg),
        "scope_type": "EVENT_TYPE",
        "scope_id": scope["scope_id"],
        "scope_name": scope["scope_name"],
        "name": scope["scope_name"],
        "lifecycle_stage": None,
        "sample_size": core["n"],
        "years": [r["year"] for r in agg],
        "center_day_of_year": core["center_doy"],
        "center_date_label": core["center_md"],
        "window": win,
        "concentration_ratio": core["concentration_ratio"],
        "concentration_p_analytic": core["span_p_analytic"],
        "recurrence_count": rec_count,
        "recurrence_ratio": round(rec_count / core["n"], 4) if rec_count is not None and core["n"] else None,
        "recurrence_label": "历史样本中的窗口复现情况（不是未来概率）",
        "recurrence_years": rec_years,
        "missed_years": miss_years,
        "dispersion": {
            "iqr_days": core["iqr_days"],
            "mad_days": core["mad_days"],
            "linear_span_days": core["linear_span_days"],
            "circular_span_days": core["circular_span_days"],
            "span_days": core["span_days"],
            "circular_window_used": core["circular_window_used"],
            "earliest_md": core["earliest_md"],
            "latest_md": core["latest_md"],
            "month_distribution": core["month_distribution"],
            "quarter_distribution": core["quarter_distribution"],
        },
        "stability": {
            "front_back": stab.get("front_back"),
            "status": stab.get("status"),
            "front_center_md": stab.get("front_center_md"),
            "back_center_md": stab.get("back_center_md"),
            "median_shift_days": stab.get("median_shift_days"),
            "loo_max_shift_days": loo.get("loo_max_shift_days"),
            "loo_median_shift_days": loo.get("loo_median_shift_days"),
            "single_year_dominance": loo.get("single_year_dominance"),
        },
        "theme_family_count": 0,
        "theme_family_names": [],
        "theme_cycle_count": 0,
        "campaign_count": 0,
        "theme_family_independence": independence,
        "mechanisms": mech["mechanisms"],
        "mechanism_confidence": mech["mechanism_confidence"],
        "mechanism_note": mech["mechanism_note"],
        "mechanism_data_supported": mech["data_supported"],
        "mechanism_post_hoc": mech["post_hoc_hypothesis"],
        "absolute_vs_relative": rel,
        "holiday_offsets": offsets,
        "promotion_status": gate["promotion_status"],
        "promotion_reason": gate["reason"],
        "window_buildable": gate["window_buildable"],
        "limitations": [
            "事件台账是研究样本的一部分，其月份分布本身存在选择偏差（6 月占比 33%）。",
            "事件类型不构成「主题观察规律」，不得进入 Timeline。",
        ],
        "source_records": [
            {
                "year": r["year"],
                "event_id": r.get("event_id"),
                "anchor_type": "EVENT_DATE",
                "anchor_date": r["date"],
                "doy": r["doy"],
                "source": r.get("source"),
            }
            for r in agg
        ],
    }


# ================================================================ 负对照 / 多重比较


def negative_control(annual, export):
    """幸存者偏差 / 负对照检查。"""
    negatives = [a for a in annual if a["status"] in ("no_clear_campaign", "weak")]
    total_years = sorted({a["year"] for a in annual})
    by_rule = {}
    for a in annual:
        by_rule.setdefault(a["rule_id"], []).append(a)
    detail = []
    for rid, rows in sorted(by_rule.items()):
        neg = [r for r in rows if r["status"] in ("no_clear_campaign", "weak")]
        detail.append(
            {
                "rule_id": rid,
                "years_reviewed": len(rows),
                "negative_years": [r["year"] for r in neg],
                "negative_statuses": {str(r["year"]): r["status"] for r in neg},
                "coverage_ratio": round(len(neg) / len(rows), 4) if rows else None,
            }
        )
    return {
        "available": True,
        "method": (
            "以 `annual_reviews.status ∈ {no_clear_campaign, weak}` 作为「窗口经过但未成势」的**年度级弱反例**；"
            "仓库内不存在「主题级未成势」记录。"
        ),
        "negative_records": negatives,
        "by_rule": detail,
        "coverage": "WEAK — 仅有年度级状态，没有主题级负样本",
        "coverage_note": (
            "negative-control coverage insufficient：无法观测「同样在某时间窗口出现、但最终未形成 Campaign」的主题。"
            "因此**不能**把「没有反例」当作「不存在反例」。"
        ),
    }


def multiple_testing(candidates):
    """多重比较 / 数据挖掘偏差意识（§十七）。"""
    n_total = len(candidates)
    n_ge5 = [c for c in candidates if c["sample_size"] >= 5]
    n_ge3 = [c for c in candidates if c["sample_size"] >= 3]
    concentrated = [c for c in candidates if c["concentration_ratio"] is not None and c["concentration_ratio"] <= 0.45]
    p_le_005 = [
        c for c in candidates
        if c["concentration_p_analytic"] is not None and c["concentration_p_analytic"] <= 0.05
    ]
    return {
        "scan_space_size": n_total,
        "candidates_N_ge_3": len(n_ge3),
        "candidates_N_ge_5": len(n_ge5),
        "candidates_concentration_le_0_45": len(concentrated),
        "candidates_p_le_0_05": len(p_le_005),
        "expected_false_positives_at_0_05": round(0.05 * len(n_ge5), 2),
        "bonferroni_threshold": round(0.05 / n_total, 6) if n_total else None,
        "candidates_passing_bonferroni": [
            c["pattern_id"] for c in p_le_005 if c["concentration_p_analytic"] <= (0.05 / n_total if n_total else 1)
        ],
        "note": (
            "本轮为**发现性研究（discovery）**，不是验证性统计检验（confirmatory）。"
            "扫描空间 %d 个候选，因此「某个 p 值很漂亮」本身不构成证据；"
            "必须同时通过样本量、集中度、稳定性、留一法、主题族独立性、负对照与机制七项检查。"
            % n_total
        ),
    }


# ================================================================ TOP-01 回归


def top01_regression(candidates):
    """TOP-01（rule_auto_summer · EARLY_SIGNAL）核心数字回归检查。"""
    target = None
    for c in candidates:
        if c["scope_type"] == "RULE" and c["scope_id"] == "rule_auto_summer" and c["lifecycle_stage"] == "EARLY_SIGNAL":
            target = c
            break
    expected = {"N": 7, "center": "06-11", "window": ("05-27", "06-26"), "recurrence": "5/7"}
    if target is None:
        return {
            "status": "FAIL",
            "reason": "未在候选池中找到 rule_auto_summer · EARLY_SIGNAL（TOP-01 对应候选）。",
            "expected": expected,
            "actual": None,
        }
    actual = {
        "N": target["sample_size"],
        "center": target["center_date_label"],
        "window": (
            target["window"]["start"] if target["window"] else None,
            target["window"]["end"] if target["window"] else None,
        ),
        "recurrence": "%s/%s" % (target["recurrence_count"], target["sample_size"]),
    }
    ok = (
        actual["N"] == expected["N"]
        and actual["center"] == expected["center"]
        and actual["window"] == expected["window"]
        and actual["recurrence"] == expected["recurrence"]
    )
    return {
        "status": "PASS" if ok else "FAIL",
        "pattern_id": target["pattern_id"],
        "expected": {
            "N": expected["N"],
            "center": expected["center"],
            "window": "%s ~ %s" % expected["window"],
            "recurrence": expected["recurrence"],
        },
        "actual": {
            "N": actual["N"],
            "center": actual["center"],
            "window": "%s ~ %s" % actual["window"],
            "recurrence": actual["recurrence"],
        },
        "promotion_status_v0_2": target["promotion_status"],
        "note": (
            "核心数字回归：N / center / window / recurrence 四项必须与 Phase 7.2 canonical Artifact 一致。"
            "promotion_status 属规则集演进维度，允许变化但必须在报告中解释（不得静默改变）。"
        ),
    }


# ================================================================ 组装 Artifact


def build_artifact():
    export = load_export()
    conn = sqlite3.connect(DB_PATH)
    try:
        phases = db_phases(conn)
        db_ev = db_events(conn)
        annual = db_annual(conn)
        macro_themes = db_macro_themes(conn)
        themes = db_all_themes(conn)
        tax = theme_taxonomy.load(conn)
    finally:
        conn.close()

    # 主题族校验（复用既有 taxonomy）
    for disp, meta in THEME_FAMILY_BY_SCOPE.items():
        if macro_themes.get(meta["theme_family_id"]) != meta["display_name"]:
            raise SystemExit(
                "FAIL —— 主题族 %s（%s）在 themes 表中不存在或名称不一致（现有：%s）"
                % (meta["theme_family_id"], meta["display_name"], macro_themes)
            )

    # canonical Macro Theme 解析报告（CMTR v1）
    _objs_for_res = []
    for kind, key in (("campaign", "campaigns"), ("research_candidate", "research_candidates")):
        for o in export.get(key) or []:
            if o.get("campaign_id"):
                _objs_for_res.append(dict(o, kind=kind))
    theme_resolution = theme_taxonomy.resolution_report(tax, _objs_for_res)

    objs = build_objects(export, tax)
    anchors = build_anchor_records(objs)
    transitions = build_transition_records(objs)
    db_starts, db_trans = build_db_phase_records(objs, phases)
    events = build_event_records(export, db_ev)

    scopes, candidates = run_scan(export, objs, anchors, transitions, db_starts, db_trans, events, themes)
    candidates = mark_duplicates(candidates)

    # 排序：先按 promotion 优先级，再按 N，再按集中度（稳定、可复现）
    prio = {"TIMELINE_CANDIDATE": 0, "EXPLORATORY": 1, "RESEARCH_ONLY": 2, "REJECTED": 3, "INSUFFICIENT_DATA": 4}
    candidates.sort(
        key=lambda c: (
            prio.get(c["promotion_status"], 9),
            c["is_duplicate_scope"],
            -(c["sample_size"] or 0),
            c["concentration_ratio"] if c["concentration_ratio"] is not None else 9,
            c["pattern_id"],
        )
    )

    neg = negative_control(annual, export)
    mt = multiple_testing(candidates)
    reg = top01_regression(candidates)
    overlap = overlap_groups(candidates)
    sr = scope_robustness(candidates)
    tcr = timeline_candidate_robustness(candidates, sr)
    candidates = annotate_effective_status(candidates, tcr)

    eff_counts = {}
    for c in candidates:
        eff_counts[c["effective_promotion_status"]] = eff_counts.get(c["effective_promotion_status"], 0) + 1
    robust_timeline = [
        c["pattern_id"] for c in candidates
        if c["effective_promotion_status"] == "TIMELINE_CANDIDATE"
    ]
    # 有效候选的「结构数」按样本重叠连通分量计（同一结构的多个 scope 切面算 1 个）
    eff_set = set(robust_timeline)
    parent = {i: i for i in robust_timeline}

    def _find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for p in overlap["pairs"]:
        if p["a"] in eff_set and p["b"] in eff_set:
            ra, rb = _find(p["a"]), _find(p["b"])
            if ra != rb:
                parent[rb] = ra
    eff_structures = len({_find(i) for i in robust_timeline})

    by_status = {}
    for c in candidates:
        by_status.setdefault(c["promotion_status"], []).append(c["pattern_id"])
    by_type = {}
    for c in candidates:
        by_type.setdefault(c["pattern_type"], []).append(c["pattern_id"])
    by_scope = {}
    for c in candidates:
        by_scope.setdefault(c["scope_type"], []).append(c["pattern_id"])

    sigs = {}
    for c in candidates:
        sigs.setdefault(c["member_signature"], []).append(c["pattern_id"])
    distinct_sigs = {s: ids for s, ids in sigs.items() if True}
    timeline_ids = [c["pattern_id"] for c in candidates if c["promotion_status"] == "TIMELINE_CANDIDATE"]
    timeline_distinct = sorted({c["member_signature"] for c in candidates if c["promotion_status"] == "TIMELINE_CANDIDATE"})

    artifact = {
        "artifact": "time_observation_candidate_pool",
        "artifact_version": ARTIFACT_VERSION,
        "ruleset_version": RULESET_VERSION,
        "generated_at": SNAPSHOT_DATE,
        "snapshot_date": SNAPSHOT_DATE,
        "generated_by": "research/scripts/discover_time_observation_patterns.py",
        "research_round": "time-observation-discovery-v%s" % ARTIFACT_VERSION,
        "contract_note": (
            "Research Candidate Pool —— **不是** Timeline Database，**不是**产品 schema。"
            "不进入 src/ / DB / schema.sql / timeline_export_v1.json / contracts。"
            "TIMELINE_CANDIDATE 亦仅为「候选」，需经 Product Review 后才可成为 Product Artifact。"
        ),
        "pipeline": [
            "历史数据（export + research DB，只读）",
            "统一时间事件层（Anchor / Lifecycle Transition / Event）",
            "Time Observation Discovery（本脚本）",
            "Candidate Pool（本 Artifact）",
            "Promotion Gate（脚本内置，可复核）",
            "Product Artifact（**本轮不做**）",
            "Timeline（**本轮不改**）",
        ],
        "question": (
            "在 2018–2025 的 ThreeC 历史数据中，哪些主题、主题族或事件类型，其启动 / 形成 / 确认 / "
            "强化 / 转折等关键时间，在一年内呈现可重复的聚集、节奏或日历关联？"
        ),
        "not_a": [
            "这不是预测器，也不做任何形式的未来推断",
            "这不给出买入或卖出时间",
            "这不指示最佳埋伏点",
            "这不做涨幅预测",
            "这不计算胜率",
            "这不输出未来概率",
            "这不做收益预测",
        ],
        "input_snapshot": {
            "canonical_export": "exports/timeline_export_v1.json",
            "export_version": export.get("timeline_export_version"),
            "export_generated_at": export.get("generated_at"),
            "export_source_commit": export.get("source_commit"),
            "research_db": "research/database/cycle_research.db",
        },
        "theme_resolution": theme_resolution,
        "scan_scope": {
            "years": "2018-01-01 ~ 2025-12-31",
            "years_observed": sorted({o["year"] for o in objs if o["year"]}),
            "excluded_years": [
                {"year": a["year"], "reason": a["status"], "rule_id": a["rule_id"]}
                for a in annual
                if a["status"] == "no_clear_campaign"
            ],
            "theme_cycles_scanned": sorted({o["theme_cycle_id"] for o in objs if o["theme_cycle_id"]}),
            "campaigns_scanned": sum(1 for o in objs if o["kind"] == "campaign"),
            "research_candidates_scanned": sum(1 for o in objs if o["kind"] == "research_candidate"),
            "anchor_records": len(anchors),
            "transition_records": len(transitions),
            "db_phase_records": len(db_starts) + len(db_trans),
            "event_records": len(events),
            "scopes": [
                {"scope_type": s["scope_type"], "scope_id": s["scope_id"], "scope_name": s["scope_name"],
                 "stages": s["stages"], "transitions": ["%s->%s" % t for t in s["transitions"]]}
                for s in scopes
            ],
            "lifecycle_stages_scanned": LC_STAGES,
            "db_phases_scanned": DB_PHASES,
            "transitions_scanned": ["%s->%s" % t for t in LC_TRANSITIONS],
            "db_transitions_scanned": ["%s->%s" % t for t in DB_TRANSITIONS],
            "event_types_scanned": sorted({e["event_type"] for e in events}),
        },
        "method": {
            "anchor_priority": [
                "EARLY_SIGNAL.start（首选）",
                "THEME_FORMING.start",
                "BROAD_CONFIRMATION.start",
                "Campaign.start（末选）",
            ],
            "anchor_note": (
                "本脚本对**每个 lifecycle 阶段**分别扫描（不只看启动），因此同时覆盖 start / formation / "
                "broad confirmation / expansion / peak / weakening / decline 与阶段迁移。"
                "锚点优先级与 `src/data/timeline/preObservation.ts` 同口径，不另立标准。"
            ),
            "day_of_year": "日序 + 闰年归一（3 月 1 日起 −1）；环形距离支持跨年簇（12 月下旬 ~ 1 月上旬）。",
            "window": "典型窗口 = Median ± 1×MAD×1.4826（抗离群）；并列保留 P25–P75 与月降级口径。",
            "concentration": "集中度比率 = 观测跨度 ÷ 均匀期望跨度 (N-1)/(N+1)×365。",
            "concentration_p": "解析式 P(range ≤ s) = N·r^(N-1) − (N-1)·r^N（r = s/365），**非随机**，保证确定性。",
            "recurrence": "落入窗口年数 ÷ 有效观测年数（只描述过去，不是未来概率）。",
            "stability": "年份前后两半中位位移：<21d STABLE / 21–44d MILD_DRIFT / ≥45d STRONG_DRIFT。",
            "leave_one_out": "逐点剔除后中心位移；max ≥ 45d → single_year_dominance = true。",
            "theme_family_independence": (
                "同时记录 theme_family_count（Macro Theme 数）、theme_cycle_count（独立 Theme Cycle 数）"
                "与 campaign_count（独立 Campaign 数）。"
            ),
            "macro_theme_resolution": (
                "canonical CMTR v1（research/scripts/theme_taxonomy.py）：对象 Macro Theme = "
                "themes[] 名称 → DB themes 表归一化 → 沿 parent_theme_id 上溯至根。"
                "**不使用** direct（Macro Theme 名称字面匹配）口径 —— 该口径会把只登记子主题的对象"
                "（C-2019-AD / RC-2024-SECONDARY / RC-2020-PANDEMIC / RC-2021-TCM）误判为无 Macro Theme。"
                "未解析名称一律显式上报（见 theme_resolution.unmatched_theme_names），不静默丢弃。"
            ),
            "absolute_vs_relative": (
                "同时计算绝对日序与相对春节 / 国庆 / 五一的偏移，判定 ABSOLUTE_CALENDAR vs EVENT_RELATIVE 谁更有解释力。"
            ),
        },
        "pattern_type_vocabulary": PATTERN_TYPES,
        "mechanism_vocabulary": MECHANISMS,
        "mechanism_confidence_vocabulary": MECHANISM_CONFIDENCE,
        "promotion_status_vocabulary": PROMOTION_STATUSES,
        "promotion_gate": {
            "INSUFFICIENT_DATA": "N < 3：样本不足以判断。",
            "REJECTED": "留一法单年主导，或 IQR > 90 天（窗口不可构建）。",
            "RESEARCH_ONLY": "N ≥ 5 但集中度 > 0.60（时间分散）；或 3–4 且集中度不足。",
            "EXPLORATORY": "窗口可构建且集中度尚可，但样本 / 稳定性 / 独立性 / 机制未全部达门槛。",
            "TIMELINE_CANDIDATE": (
                "N ≥ 5 且 窗口可构建 且 集中度 ≤ 0.45 且 STABLE 且 无单年主导 "
                "且 theme_cycle_count ≥ 3 且 机制置信度 ≥ MEDIUM。"
            ),
            "note": (
                "**N ≥ 5 ≠ 自动进入 Timeline。** 门槛保持与 v0.1 连续，不为了增加 TIMELINE_CANDIDATE 数量而放宽。"
                "事件类型候选一律不得成为 TIMELINE_CANDIDATE。"
            ),
        },
        "forbidden_fields": FORBIDDEN_FIELDS,
        "background_baseline": {
            "note": (
                "时间聚集不能只靠「某月事件多」证明：ThreeC 自建事件台账本身 6 月占比 33%（10/30），"
                "远高于均匀基准 8.3%；即使只看指数「最优 30 日窗口」，6 月占比也达 18.75%。"
                "因此任何 6 月偏好都**部分来自研究样本选择偏差**。"
            ),
            "event_calendar_june_share": 0.3333,
            "index_best_30d_window_june_share": 0.1875,
            "uniform_june_share": 0.0833,
        },
        "negative_control": neg,
        "multiple_testing": mt,
        "top01_regression": reg,
        "lifecycle_rhythm": {
            "rule_auto_summer": lifecycle_rhythm_analysis(anchors, _scope_by_id(scopes, "rule_auto_summer"), LC_STAGES),
            "TH-AUTO": lifecycle_rhythm_analysis(anchors, _scope_by_id(scopes, "TH-AUTO"), LC_STAGES),
        },
        "candidate_overlap": overlap,
        "scope_robustness": sr,
        "timeline_candidate_robustness": tcr,
        "scan_map": {
            "total_candidates": len(candidates),
            "distinct_samples": len(distinct_sigs),
            "duplicate_scope_candidates": sum(1 for c in candidates if c["is_duplicate_scope"]),
            "by_promotion_status": {k: len(v) for k, v in sorted(by_status.items())},
            "by_pattern_type": {k: len(v) for k, v in sorted(by_type.items())},
            "by_scope_type": {k: len(v) for k, v in sorted(by_scope.items())},
            "promotion_ids": {k: v for k, v in sorted(by_status.items())},
            "timeline_candidate_distinct_samples": len(timeline_distinct),
            "timeline_candidate_distinct_structures": overlap["distinct_structures"],
            "timeline_candidate_ids": timeline_ids,
            "effective_by_promotion_status": dict(sorted(eff_counts.items())),
            "effective_timeline_candidate_ids": sorted(robust_timeline),
            "effective_timeline_candidate_count": len(robust_timeline),
            "effective_timeline_candidate_distinct_structures": eff_structures,
            "pattern_type_x_status": _cross(candidates, "pattern_type", "promotion_status"),
            "scope_type_x_status": _cross(candidates, "scope_type", "promotion_status"),
            "member_signature_groups": {
                s: ids for s, ids in sorted(sigs.items()) if len(ids) > 1
            },
        },
        "candidates": candidates,
    }
    if LEGACY_DIRECT_RESOLUTION:
        # v0.2 产物不含这两处；删除以保证历史轮次逐字节可复现
        artifact.pop("theme_resolution", None)
        artifact["method"].pop("macro_theme_resolution", None)
    return artifact


def mark_duplicates(candidates):
    """标记「同一底层观测集合被多个 scope 重复统计」的候选（跨 scope 重复口径）。

    同一 `member_signature` 的候选共享完全相同的年份与锚点，统计结果必然相同；
    它们不是「多个独立规律」，只是同一规律在不同 scope 定义下的两次呈现。
    为可审计，保留全部候选，但显式标注 `exact_duplicate_of` 与 `is_duplicate_scope`。
    """
    first = {}
    for c in candidates:
        sig = c["member_signature"]
        if sig in first:
            c["exact_duplicate_of"] = first[sig]["pattern_id"]
            c["is_duplicate_scope"] = True
        else:
            first[sig] = c
            c["exact_duplicate_of"] = None
            c["is_duplicate_scope"] = False
    return candidates


def lifecycle_rhythm_analysis(anchors, scope, stages):
    """生命周期节奏分析：各阶段相对 EARLY_SIGNAL 的中位滞后。

    **关键方法学点**：如果某阶段的中心 ≈ EARLY_SIGNAL 中心 + 典型 Campaign 时长，
    那么该阶段的「时间聚集」是 EARLY_SIGNAL 聚集的**派生结果**，不是独立证据。
    本函数显式标记 `derived_from_early_signal`，避免把同一事实重复计为多个规律。
    """
    sel = select_records(anchors, scope)
    base = dedup_by_year([r for r in sel if r["stage"] == "EARLY_SIGNAL"])
    if len(base) < 3:
        return {"status": "INSUFFICIENT_DATA", "note": "EARLY_SIGNAL 样本 < 3，无法做节奏基线。"}
    base_by_year = {r["year"]: r for r in base}

    out = {
        "status": "OK",
        "baseline_stage": "EARLY_SIGNAL",
        "baseline_center_md": compute_core([r["doy"] for r in base])["center_md"],
        "baseline_n": len(base),
        "stages": [],
        "note": (
            "滞后 = 同一对象内「该阶段起点 − EARLY_SIGNAL 起点」的天数中位数。"
            "若某阶段中心 ≈ 基线中心 + 滞后，则其时间聚集为派生结果，**不得**计为独立规律。"
        ),
    }
    for st in stages:
        if st == "EARLY_SIGNAL":
            continue
        rows = dedup_by_year([r for r in sel if r["stage"] == st])
        if len(rows) < 3:
            continue
        lags = []
        for r in rows:
            b = base_by_year.get(r["year"])
            if b:
                lags.append(days_between(b["date"], r["date"]))
        if not lags:
            continue
        core = compute_core([r["doy"] for r in rows])
        med_lag = median_f(lags)
        expected_center = (compute_core([r["doy"] for r in base])["center_doy"] + med_lag) % 365
        gap = abs(((core["center_doy"] - expected_center + 182) % 365) - 182)
        out["stages"].append(
            {
                "stage": st,
                "n": core["n"],
                "center_md": core["center_md"],
                "median_lag_from_early_signal_days": round(med_lag, 1),
                "predicted_center_md": md_of_doy(expected_center),
                "center_residual_days": round(gap, 1),
                "derived_from_early_signal": bool(gap <= 21.0),
                "concentration_ratio": core["concentration_ratio"],
                "interpretation": (
                    "派生：中心可由「EARLY_SIGNAL 中心 + 中位滞后」解释（残差 ≤ 21 天）→ 非独立证据。"
                    if gap <= 21.0
                    else "残差 > 21 天 → 该阶段时间位置含 EARLY_SIGNAL 之外的额外信息（仍需独立检验）。"
                ),
            }
        )
    return out


def overlap_groups(candidates, threshold=0.5):
    """TIMELINE_CANDIDATE 之间的样本重叠（Jaccard）—— 判断是否为「同一结构的多个切面」。"""
    tl = [c for c in candidates if c["promotion_status"] == "TIMELINE_CANDIDATE"]
    sets = {}
    for c in tl:
        sets[c["pattern_id"]] = {(r.get("campaign_id") or r.get("event_id"), r["anchor_date"]) for r in c["source_records"]}
    groups = []
    for i, a in enumerate(tl):
        for b in tl[i + 1:]:
            sa, sb = sets[a["pattern_id"]], sets[b["pattern_id"]]
            if not sa or not sb:
                continue
            j = len(sa & sb) / float(len(sa | sb))
            if j >= threshold:
                groups.append(
                    {
                        "a": a["pattern_id"],
                        "a_name": a["name"],
                        "b": b["pattern_id"],
                        "b_name": b["name"],
                        "jaccard": round(j, 3),
                    }
                )
    # 连通分量 = 结构分组（同一结构的不同切面归为一组）
    ids = [c["pattern_id"] for c in tl]
    parent = {i: i for i in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for g in groups:
        ra, rb = find(g["a"]), find(g["b"])
        if ra != rb:
            parent[rb] = ra
    comps = {}
    for i in ids:
        comps.setdefault(find(i), []).append(i)

    return {
        "threshold": threshold,
        "timeline_candidate_count": len(tl),
        "distinct_structures": len(comps),
        "structures": {k: sorted(v) for k, v in sorted(comps.items())},
        "pairs": groups,
        "note": (
            "Jaccard ≥ 0.5 表示两条候选的底层观测高度重叠 → 更可能是**同一结构的不同生命周期切面**，"
            "而非多个独立规律。报告与产品接入时须按「结构」而非「候选条数」计数。"
        ),
    }


# scope 变体对：**同一主题族**在两种 scope 定义下的呈现。
# v0.3 起 Macro Theme 归属改用 canonical CMTR v1（theme_taxonomy.py）→ 两侧成员集合应当一致。
SCOPE_VARIANT_PAIRS = [
    ("rule_auto_summer", "TH-AUTO"),
    ("rule_pharma_upgrade", "TH-PHARMA"),
]


def scope_robustness(candidates):
    """口径稳健性：**同一主题族的两种 scope 定义**是否给出一致结论。

    只比较 `SCOPE_VARIANT_PAIRS`（rule ↔ 对应 Macro Theme），不比较跨族或 ALL ——
    跨族样本本来就不同，比较它们会把「天然不同」误判为「不一致」。

    v0.2 历史背景：当时 Macro Theme 归属用 `direct`（字面名称匹配）口径，
    `C-2019-AD` 因未挂接 Macro Theme 被 TH-AUTO 排除 → 两侧成员不同（rule 含 2019、TH-AUTO 不含），
    导致 5 对判定不一致。v0.3 改用 canonical `resolved` 口径后该缺口消失。

    因此本检验在 v0.3 的语义变为**回归检验**：
    - `fragile_pairs == 0` → 两种 scope 定义对同一主题族给出一致结论（期望结果）
    - 若再次出现不一致 → 说明又引入了新的口径分歧，**必须**记录并降级，不得静默通过
    """
    sets = {
        c["pattern_id"]: {(r.get("campaign_id") or r.get("event_id"), r["anchor_date"]) for r in c["source_records"]}
        for c in candidates
    }
    index = {}
    for c in candidates:
        index.setdefault((c["pattern_kind"], c["lifecycle_stage"], c["scope_id"]), c)

    out = []
    for sa, sb in SCOPE_VARIANT_PAIRS:
        keys = {(k[0], k[1]) for k in index if k[2] in (sa, sb)}
        for kind, stage in sorted(keys):
            a = index.get((kind, stage, sa))
            b = index.get((kind, stage, sb))
            if not a or not b:
                continue
            m_a, m_b = sets[a["pattern_id"]], sets[b["pattern_id"]]
            j = len(m_a & m_b) / float(len(m_a | m_b)) if (m_a and m_b) else 0.0
            same_status = a["promotion_status"] == b["promotion_status"]
            same_drift = a["stability"].get("front_back") == b["stability"].get("front_back")
            out.append(
                {
                    "pattern_kind": kind,
                    "lifecycle_stage": stage,
                    "a": a["pattern_id"],
                    "a_scope": sa,
                    "b": b["pattern_id"],
                    "b_scope": sb,
                    "jaccard": round(j, 3),
                    "sample_sizes": {sa: a["sample_size"], sb: b["sample_size"]},
                    "statuses": {sa: a["promotion_status"], sb: b["promotion_status"]},
                    "drift_flags": {sa: a["stability"].get("front_back"), sb: b["stability"].get("front_back")},
                    "concentration_ratios": {sa: a["concentration_ratio"], sb: b["concentration_ratio"]},
                    "verdict_consistent": bool(same_status and same_drift),
                    "note": (
                        "⚠️ 口径不一致：同一主题族的两种 scope 定义给出不同判定 → 结论依赖单一年份（2019）"
                        "是否入样，而该入样由 taxonomy 缺口决定，不是有原则的筛选规则 → 判定脆弱。"
                        if not (same_status and same_drift)
                        else "同一主题族的两种 scope 定义判定一致。"
                    ),
                }
            )
    n_robust = sum(1 for r in out if r["verdict_consistent"])
    return {
        "pairs_compared": len(out),
        "robust_pairs": n_robust,
        "fragile_pairs": len(out) - n_robust,
        "detail": out,
        # legacy 口径下必须输出 v0.2 的原文，否则历史轮次无法逐字节复现
        "note": (
            (
                "只比较 `SCOPE_VARIANT_PAIRS`（rule ↔ 对应 Macro Theme）。"
                "`rule_auto_summer` 与 Macro Theme「汽车」的唯一差别是 C-2019-AD 的 taxonomy 挂接缺口；"
                "两者结论不一致 = 判定由「2019 年是否入样」决定，而这不是有原则的筛选规则。"
            )
            if LEGACY_DIRECT_RESOLUTION
            else (
                "只比较 `SCOPE_VARIANT_PAIRS`（rule ↔ 对应 Macro Theme）。"
                "v0.3 起 Macro Theme 归属改用 canonical CMTR v1（theme_taxonomy.py）→ 两侧成员集合一致，"
                "本检验语义为**回归检验**：`fragile_pairs == 0` 为期望结果；"
                "若再次出现不一致，说明引入了新的口径分歧，必须记录并降级。"
                "（v0.2 曾因 C-2019-AD 的 taxonomy 挂接缺口产生 5 对脆弱，v0.3 已消除。）"
            )
        ),
    }


def timeline_candidate_robustness(candidates, sr):
    """对每个 TIMELINE_CANDIDATE 判定：其结论是否对 scope 定义稳健。

    稳健 = 所有 Jaccard ≥ 阈值的同阶段伙伴给出相同 status 与相同 drift 判定。
    若存在任何脆弱配对，则该候选**不得**被当作稳定规律（即使它自己通过了数值门槛）。
    """
    fragile_ids = set()
    for d in sr["detail"]:
        if not d["verdict_consistent"]:
            fragile_ids.add(d["a"])
            fragile_ids.add(d["b"])
    partners = {}
    for d in sr["detail"]:
        partners.setdefault(d["a"], []).append(d["b"])
        partners.setdefault(d["b"], []).append(d["a"])

    out = []
    for c in candidates:
        if c["promotion_status"] != "TIMELINE_CANDIDATE":
            continue
        pid = c["pattern_id"]
        ps = partners.get(pid, [])
        if not ps:
            verdict = "UNTESTED_NO_SCOPE_VARIANT"
        elif pid in fragile_ids:
            verdict = "FRAGILE_SCOPE_DEPENDENT"
        else:
            verdict = "ROBUST"
        out.append(
            {
                "pattern_id": pid,
                "name": c["name"],
                "sample_size": c["sample_size"],
                "center_date_label": c["center_date_label"],
                "scope_id": c["scope_id"],
                "theme_family_count": c["theme_family_count"],
                "theme_cycle_count": c["theme_cycle_count"],
                "scope_variant_partners": sorted(ps),
                "robustness_verdict": verdict,
                "note": (
                    "稳健：在所有可比 scope 变体下给出相同判定。"
                    if verdict == "ROBUST"
                    else (
                        "⚠️ 脆弱：结论依赖单一年份是否入样（scope 变体给出不同判定）→ 不得当作稳定规律。"
                        if verdict == "FRAGILE_SCOPE_DEPENDENT"
                        else "无可比 scope 变体，未能检验稳健性。"
                    )
                ),
            }
        )
    n_robust = sum(1 for r in out if r["robustness_verdict"] == "ROBUST")
    return {
        "timeline_candidate_count": len(out),
        "robust_count": n_robust,
        "fragile_count": sum(1 for r in out if r["robustness_verdict"] == "FRAGILE_SCOPE_DEPENDENT"),
        "untested_count": sum(1 for r in out if r["robustness_verdict"] == "UNTESTED_NO_SCOPE_VARIANT"),
        "detail": out,
        "note": (
            "**这是本轮最关键的筛选**：通过数值门槛（N / 集中度 / 稳定性 / LOO）的候选，"
            "若其结论随 scope 定义翻转，则说明它依赖「某一年是否入样」这一非原则性条件。"
        ),
    }


def annotate_effective_status(candidates, tcr):
    """把口径稳健性结果回写到候选：脆弱者降级为 EXPLORATORY。

    保留原始 `promotion_status`（可审计「数值门槛结论」），另加
    `effective_promotion_status`（经稳健性检验后的**最终**结论）。
    两者不一致时必须记录原因，不得静默覆盖。
    """
    verdict = {d["pattern_id"]: d for d in tcr["detail"]}
    for c in candidates:
        v = verdict.get(c["pattern_id"])
        c["robustness_verdict"] = v["robustness_verdict"] if v else None
        if c["promotion_status"] == "TIMELINE_CANDIDATE" and v and v["robustness_verdict"] == "FRAGILE_SCOPE_DEPENDENT":
            c["effective_promotion_status"] = "EXPLORATORY"
            c["effective_status_reason"] = (
                "通过数值门槛，但同一主题族的两种 scope 定义给出不同判定 → 结论依赖 2019 年是否入样"
                "（该入样由 taxonomy 缺口决定，非有原则的筛选）→ 降级为 EXPLORATORY，不得进入 Timeline。"
            )
        else:
            c["effective_promotion_status"] = c["promotion_status"]
            c["effective_status_reason"] = None
    return candidates


def _cross(candidates, ka, kb):
    out = {}
    for c in candidates:
        a, b = c.get(ka), c.get(kb)
        out.setdefault(a, {}).setdefault(b, 0)
        out[a][b] += 1
    return {k: dict(sorted(v.items())) for k, v in sorted(out.items())}


# ================================================================ 自检


def _iter_strings(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _iter_strings(v, "%s.%s" % (path, k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _iter_strings(v, "%s[%d]" % (path, i))
    elif isinstance(obj, str):
        yield path, obj


def validate_artifact(art):
    issues = []
    ids = [c["pattern_id"] for c in art["candidates"]]
    if len(set(ids)) != len(ids):
        issues.append("pattern_id 重复")
    for c in art["candidates"]:
        pid = c["pattern_id"]
        for f in FORBIDDEN_FIELDS:
            if f in c:
                issues.append("%s: 出现禁用字段 %s" % (pid, f))
        if c["pattern_type"] not in PATTERN_TYPES:
            issues.append("%s: pattern_type %s 不在枚举内" % (pid, c["pattern_type"]))
        if c["promotion_status"] not in PROMOTION_STATUSES:
            issues.append("%s: promotion_status %s 不在枚举内" % (pid, c["promotion_status"]))
        for m in c["mechanisms"]:
            if m not in MECHANISMS:
                issues.append("%s: mechanism %s 不在枚举内" % (pid, m))
        if c["mechanism_confidence"] not in MECHANISM_CONFIDENCE:
            issues.append("%s: mechanism_confidence 不在枚举内" % pid)
        if c["sample_size"] != len(c["source_records"]) and c["pattern_kind"] != "EVENT_TYPE":
            issues.append("%s: sample_size 与 source_records 数量不一致" % pid)
        if c["promotion_status"] == "TIMELINE_CANDIDATE":
            if c["sample_size"] < 5:
                issues.append("%s: TIMELINE_CANDIDATE 但 N<5" % pid)
            if not c["window"]:
                issues.append("%s: TIMELINE_CANDIDATE 但无窗口" % pid)
            if c["theme_cycle_count"] < 3:
                issues.append("%s: TIMELINE_CANDIDATE 但独立 Cycle < 3" % pid)
            if c["mechanism_confidence"] == "LOW":
                issues.append("%s: TIMELINE_CANDIDATE 但机制置信度 LOW" % pid)
            if not c["limitations"]:
                issues.append("%s: TIMELINE_CANDIDATE 但无 limitations" % pid)
        if c["promotion_status"] in ("RESEARCH_ONLY", "REJECTED", "INSUFFICIENT_DATA"):
            if c.get("promotion_status") == "TIMELINE_CANDIDATE":
                issues.append("%s: 状态冲突" % pid)
        if c["effective_promotion_status"] not in PROMOTION_STATUSES:
            issues.append("%s: effective_promotion_status 不在枚举内" % pid)
        if (
            c["effective_promotion_status"] == "TIMELINE_CANDIDATE"
            and c["robustness_verdict"] != "ROBUST"
        ):
            issues.append("%s: effective TIMELINE_CANDIDATE 但稳健性判定非 ROBUST" % pid)
        if (
            c["effective_promotion_status"] != c["promotion_status"]
            and not c.get("effective_status_reason")
        ):
            issues.append("%s: effective 状态与原始状态不一致但未记录原因" % pid)
        if c["pattern_kind"] == "EVENT_TYPE" and c["promotion_status"] == "TIMELINE_CANDIDATE":
            issues.append("%s: 事件类型候选不得成为 TIMELINE_CANDIDATE" % pid)
        for r in c["source_records"]:
            if r.get("anchor_date") and parse_iso(r["anchor_date"]) is None:
                issues.append("%s: 来源记录日期非法 %s" % (pid, r["anchor_date"]))

    # canonical Macro Theme 解析自检（CMTR v1）；legacy 口径下不适用
    tr = art.get("theme_resolution")
    if LEGACY_DIRECT_RESOLUTION and tr is not None:
        issues.append("legacy 口径下不应输出 theme_resolution")
    elif not LEGACY_DIRECT_RESOLUTION and not tr:
        issues.append("缺少 theme_resolution（canonical Macro Theme 解析报告）")
    elif tr:
        if tr.get("ruleset") != theme_taxonomy.RULESET:
            issues.append("theme_resolution.ruleset 与 theme_taxonomy 不一致")
        if sum(tr["counts_by_status"].values()) != len(tr["objects_resolved"]):
            issues.append("theme_resolution.counts_by_status 与 objects_resolved 数量不一致")
        declared = {m["theme_id"] for m in tr["macro_themes"]}
        for r in tr["objects_resolved"]:
            cid = r["campaign_id"]
            if r["status"] not in theme_taxonomy.STATUSES:
                issues.append("%s: theme_resolution.status 不在枚举内" % cid)
            if r["status"] == "RESOLVED" and len(r["macro_theme_ids"]) != 1:
                issues.append("%s: RESOLVED 但 Macro Theme 数 != 1" % cid)
            if r["status"] == "CONFLICT" and len(r["macro_theme_ids"]) < 2:
                issues.append("%s: CONFLICT 但 Macro Theme 数 < 2" % cid)
            if r["status"] == "UNRESOLVED_NAME" and r["macro_theme_ids"]:
                issues.append("%s: UNRESOLVED_NAME 但已解析出 Macro Theme" % cid)
            for m in r["macro_theme_ids"]:
                if m not in declared:
                    issues.append("%s: 解析出未声明的 Macro Theme %s" % (cid, m))
        # 未解析名称不得静默丢弃：报告索引必须覆盖所有对象级 unmatched_names
        idx = tr["unmatched_theme_names"]
        for r in tr["objects_resolved"]:
            for nm in r["unmatched_names"]:
                if r["campaign_id"] not in idx.get(nm, []):
                    issues.append("%s: 未解析名称 %s 未进入 unmatched_theme_names 索引" % (r["campaign_id"], nm))

    if art["top01_regression"]["status"] != "PASS":
        issues.append("TOP-01 回归检查未通过：%s" % art["top01_regression"])

    # 语义红线（否定语境除外）
    negations = ("不", "非", "无", "禁止", "未")
    for path, s in _iter_strings(art):
        for phrase in BANNED_PHRASES:
            idx = s.find(phrase)
            while idx >= 0:
                window = s[max(0, idx - 12): idx]
                if not any(n in window for n in negations):
                    issues.append("%s: 文本出现非否定语境的「%s」→ 语义红线" % (path, phrase))
                idx = s.find(phrase, idx + 1)
    return issues


# ================================================================ CSV


CSV_COLUMNS = [
    "pattern_id", "pattern_type", "pattern_kind", "scope_type", "scope_id", "scope_name",
    "lifecycle_stage", "name", "sample_size", "years", "center_date_label", "window_start",
    "window_end", "window_radius_days", "concentration_ratio", "concentration_p_analytic",
    "recurrence_count", "recurrence_ratio", "front_back", "loo_max_shift_days",
    "single_year_dominance", "theme_family_count", "theme_cycle_count", "campaign_count",
    "mechanisms", "mechanism_confidence", "feature_winner", "promotion_status",
    "robustness_verdict", "effective_promotion_status", "promotion_reason",
]


def write_csv(art):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n")
    w.writeheader()
    for c in art["candidates"]:
        win = c["window"] or {}
        w.writerow(
            {
                "pattern_id": c["pattern_id"],
                "pattern_type": c["pattern_type"],
                "pattern_kind": c["pattern_kind"],
                "scope_type": c["scope_type"],
                "scope_id": c["scope_id"],
                "scope_name": c["scope_name"],
                "lifecycle_stage": c["lifecycle_stage"] or "",
                "name": c["name"],
                "sample_size": c["sample_size"],
                "years": "|".join(str(y) for y in c["years"]),
                "center_date_label": c["center_date_label"],
                "window_start": win.get("start", ""),
                "window_end": win.get("end", ""),
                "window_radius_days": win.get("radius_days", ""),
                "concentration_ratio": c["concentration_ratio"] if c["concentration_ratio"] is not None else "",
                "concentration_p_analytic": c["concentration_p_analytic"] if c["concentration_p_analytic"] is not None else "",
                "recurrence_count": c["recurrence_count"] if c["recurrence_count"] is not None else "",
                "recurrence_ratio": c["recurrence_ratio"] if c["recurrence_ratio"] is not None else "",
                "front_back": c["stability"].get("front_back") or c["stability"].get("status") or "",
                "loo_max_shift_days": c["stability"].get("loo_max_shift_days")
                if c["stability"].get("loo_max_shift_days") is not None else "",
                "single_year_dominance": c["stability"].get("single_year_dominance")
                if c["stability"].get("single_year_dominance") is not None else "",
                "theme_family_count": c["theme_family_count"],
                "theme_cycle_count": c["theme_cycle_count"],
                "campaign_count": c["campaign_count"],
                "mechanisms": "|".join(c["mechanisms"]),
                "mechanism_confidence": c["mechanism_confidence"],
                "feature_winner": (c["absolute_vs_relative"] or {}).get("feature_winner") or "",
                "promotion_status": c["promotion_status"],
                "robustness_verdict": c.get("robustness_verdict") or "",
                "effective_promotion_status": c["effective_promotion_status"],
                "promotion_reason": c["promotion_reason"],
            }
        )
    return "\ufeff" + buf.getvalue()


# ================================================================ main


def main(argv):
    check_only = "--check" in argv
    do_print = "--print" in argv

    if "--legacy-direct-resolution" in argv:
        set_legacy_direct_resolution(True)

    if "--round" in argv:
        i = argv.index("--round")
        if i + 1 >= len(argv):
            print("FAIL —— --round 需要参数，例如：--round 0.2")
            return 1
        set_round(argv[i + 1])

    art = build_artifact()
    issues = validate_artifact(art)
    if issues:
        print("FAIL —— 自检未通过，不写文件：")
        for i in issues[:40]:
            print("  -", i)
        return 1

    text = json.dumps(art, ensure_ascii=False, indent=2) + "\n"
    csv_text = write_csv(art)

    if check_only:
        ok = True
        for path, expected in ((OUT_JSON, text), (OUT_CSV, csv_text)):
            if not os.path.exists(path):
                print("FAIL —— 磁盘上不存在产物：", os.path.relpath(path, ROOT))
                ok = False
                continue
            with io.open(path, "r", encoding="utf-8", newline="") as f:
                cur = f.read()
            if cur != expected:
                print("FAIL —— 磁盘产物与重算结果不一致：", os.path.relpath(path, ROOT))
                ok = False
        if ok:
            print("PASS —— 磁盘产物与重算结果逐字节一致（deterministic）。")
            print("PASS —— TOP-01 回归：", art["top01_regression"]["actual"])
            return 0
        return 1

    with io.open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    with io.open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        f.write(csv_text)

    if do_print:
        _print_summary(art)
    return 0


def _print_summary(art):
    ss = art["scan_scope"]
    sm = art["scan_map"]
    print("=" * 78)
    print("Time Observation Discovery v%s —— 全量历史扫描完成" % ARTIFACT_VERSION)
    print("=" * 78)
    print("Dataset")
    print("  Theme Cycles :", len(ss["theme_cycles_scanned"]))
    print("  Campaigns    :", ss["campaigns_scanned"], "+ Research Candidates:", ss["research_candidates_scanned"])
    print("  Anchor recs  :", ss["anchor_records"], "| Transition recs:", ss["transition_records"],
          "| DB phase recs:", ss["db_phase_records"])
    print("  Events       :", ss["event_records"])
    print("  Years        :", ss["years_observed"])
    print("-" * 78)
    print("Discovery（effective = 经口径稳健性检验后的最终结论）")
    print("  Raw candidates      :", sm["total_candidates"])
    print("  distinct samples    :", sm["distinct_samples"])
    for k in PROMOTION_STATUSES:
        print("  %-19s : %s（effective %s）" % (k, sm["by_promotion_status"].get(k, 0),
                                                sm["effective_by_promotion_status"].get(k, 0)))
    print("-" * 78)
    print("Pattern Type × Count")
    for k, v in sorted(sm["by_pattern_type"].items(), key=lambda x: -x[1]):
        print("  %-24s %d" % (k, v))
    print("-" * 78)
    print("Top candidates（effective TIMELINE_CANDIDATE）")
    for c in art["candidates"]:
        if c["effective_promotion_status"] != "TIMELINE_CANDIDATE":
            continue
        w = c["window"] or {}
        print("  %s  %s  N=%d  中心 %s  窗口 %s~%s  复现 %s/%s  族=%d Cycle=%d  %s"
              % (c["pattern_id"], c["name"], c["sample_size"], c["center_date_label"],
                 w.get("start"), w.get("end"), c["recurrence_count"], c["sample_size"],
                 c["theme_family_count"], c["theme_cycle_count"], c["robustness_verdict"]))
    print("  → 有效候选 %d 条，归并为 %d 个独立结构（按样本重叠）"
          % (sm["effective_timeline_candidate_count"], sm["effective_timeline_candidate_distinct_structures"]))
    print("-" * 78)
    reg = art["top01_regression"]
    print("TOP-01 Regression :", reg["status"], reg.get("actual"))
    print("Determinism       : PASS（无随机数；集中度 p 用解析式）")
    print("Negative control  :", art["negative_control"]["coverage"])
    print("Multiple testing  : scan space =", art["multiple_testing"]["scan_space_size"],
          "| N>=5 =", art["multiple_testing"]["candidates_N_ge_5"],
          "| p<=0.05 =", art["multiple_testing"]["candidates_p_le_0_05"])
    print("=" * 78)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
