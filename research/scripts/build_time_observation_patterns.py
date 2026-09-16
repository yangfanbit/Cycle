#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_time_observation_patterns.py —— Time Observation Pattern canonical generator（Phase 7.2）。

## 这个脚本是什么

`Time-based Observation Layer`（时间型观察层）的**唯一 canonical 研究产物生成器**。

    exports/timeline_export_v1.json  +  research/database/cycle_research.db
                        ↓  本脚本（只读输入）
        research/research/reports/time_observation_patterns_v0_1.json   ← 产品只读消费

回答的问题（且仅此一问）：

    「历史上，一年中的这个时间位置附近，**反复出现过**值得研究的主题启动 / 观察现象吗？」

**不是**：预测、最佳买入时间、胜率、未来概率、收益预测、选股。

## 分层（与 ThreeC 既有语义严格对齐）

    Historical Campaign（历史事实）
        ↓  Anchor Extraction（不发明新的「启动」定义）
    Time Pattern Aggregation（跨年份聚合，年度去重）
        ↓
    Time Observation Pattern（多年观察结果的统计摘要）
        ↓
    Timeline View（产品只读）

- **Pattern ≠ Campaign**：一条 Pattern 对应多年、多个 Campaign；本脚本**不修改** Campaign 定义。
- **锚点优先级**（与 `src/data/timeline/preObservation.ts` 同口径，不另立标准）：
  `EARLY_SIGNAL.start` → `THEME_FORMING.start` → `BROAD_CONFIRMATION.start` → `Campaign.start`。
  **绝不**用 Peak / End / 单日涨停 / 最高成交额 / 最低点定义「启动」。
- **不改** DB / `schema.sql` / canonical export / contracts；输入只读。

## 统计口径（全部为描述统计，不含显著性断言）

- 年内日序（day-of-year）+ **闰年归一**（3 月 1 日起 -1），使 06-18 跨年可比；
- 典型窗口 B：`median ± 1×MAD×1.4826`（中位绝对偏差，抗离群）；A：P25–P75；C：月降级；
- 离散度：IQR / MAD / 跨度；
- 集中度比率 = 跨度 ÷ 均匀期望跨度 `(N-1)/(N+1)×365`；
- 历史复现 = 落入窗口的年数 ÷ 有效观测年数（**只描述过去**，不是未来概率）；
- 稳定性：年份切前后两半比较中位位移（<21d STABLE / 21–44d MILD_DRIFT / ≥45d DRIFTING）；
- 留一法（LOO）：逐点剔除，检查是否由单一年份主导；
- **不输出** permutation p 值 —— 见研究报告 §10–§12；产品数据中不承载显著性数值，避免伪精确。

## 纳入判定（宁少不多）

    TIMELINE_ELIGIBLE : N ≥ 5 且 窗口可构建 且 集中度 ≤ 0.45 且 STABLE 且 无单年主导
    REJECTED          : 窗口不可构建（IQR > 90 天 = 跨三个以上季节）或 单年主导
    RESEARCH_ONLY     : 其余（样本不足 / 稳定性或集中度未达门槛）—— 保留在 Artifact，不进 Timeline

Research Strength（A/B/C/D）与状态（MODERATE_CANDIDATE / EXPLORATORY / REJECTED）为**研究可固化程度**，
与「统计聚集强度」是两个维度（一条统计上最强的 Pattern 仍可能只是中等候选）。

用法:
    python research/scripts/build_time_observation_patterns.py            # 生成
    python research/scripts/build_time_observation_patterns.py --check     # 校验磁盘产物与重算一致
    python research/scripts/build_time_observation_patterns.py --print     # 生成并打印摘要

退出码: 0 = 通过；1 = 自检失败（**不写文件**）。
"""

from __future__ import annotations

import io
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT_PATH = os.path.join(ROOT, "exports", "timeline_export_v1.json")
DB_PATH = os.path.join(ROOT, "research", "database", "cycle_research.db")
OUT_PATH = os.path.join(
    ROOT, "research", "research", "reports", "time_observation_patterns_v0_1.json"
)

SNAPSHOT_DATE = "2026-09-16"
ARTIFACT_VERSION = "0.1"

# ---------------------------------------------------------------- 枚举（有限集，不用伪精确数值）

PATTERN_TYPES = [
    "SEASONAL",
    "CALENDAR_DRIVEN",
    "INDUSTRY_CYCLE",
    "REPORTING_CYCLE",
    "POLICY_CALENDAR",
    "MIXED",
    "UNKNOWN",
]
STATUS_VOCABULARY = ["STRONG_CANDIDATE", "MODERATE_CANDIDATE", "EXPLORATORY", "REJECTED"]
ELIGIBILITY_VOCABULARY = ["TIMELINE_ELIGIBLE", "RESEARCH_ONLY", "REJECTED"]

# 产品数据中**禁止出现**的字段名（语义红线；不是产品 schema 的一部分）
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

# 面向用户的文本里禁止出现的语义（否定语境除外）
BANNED_PHRASES = ["买入", "卖出", "布局窗口", "最佳买点", "预测", "概率", "胜率", "涨幅预测"]

# ---------------------------------------------------------------- 锚点口径

ANCHOR_EARLY = "EARLY_SIGNAL"
ANCHOR_FORMING = "THEME_FORMING"
ANCHOR_BROAD = "BROAD_CONFIRMATION"
ANCHOR_START = "CAMPAIGN_START"

ANCHOR_PRIORITY = [
    "EARLY_SIGNAL（lifecycle.EARLY_SIGNAL.start / export.early_signal / signals[].EARLY_SIGNAL 最早）",
    "THEME_FORMING（lifecycle.THEME_FORMING.start）",
    "BROAD_CONFIRMATION（lifecycle.BROAD_CONFIRMATION.start）",
    "CAMPAIGN_START（start_date；末选，仅在前三者皆无时使用）",
]

# ---------------------------------------------------------------- 主题族定义（声明式，可审计）

# 主题族 = 「同机制、不同 Campaign」的归一集合（Level 3）。
# 定义方式只用**导出既有字段**（rule_id / 主题材名），不引入新研究概念。
# theme_names 里的名称来自 export 的 themes[].name，改名会在生成结果中显式体现（family_definition 会写入产物）。
FAMILIES = [
    {
        "family_id": "AUTO_ALL",
        "source_pattern_id": "SOP-03",
        "title": "汽车主题上半年末启动观察窗口",
        "theme_scope": "汽车",
        "theme_key": "汽车（Macro Theme 全主题，rule_auto_summer 范围内全部对象）",
        "definition": {"rule_ids": ["rule_auto_summer"]},
        "pattern_type": "MIXED",
        "primary_mechanism": "CALENDAR_DRIVEN",
        "description": (
            "在 ThreeC 2018–2025 的研究样本中，汽车主题（rule_auto_summer 范围内全部 Campaign / "
            "Research Candidate）的「研究观察起点（Early Signal）」多次落在 5 月下旬—6 月下旬这一带。"
            "这是**历史样本中的时间聚集现象**，不是行业需求季节性，也不是未来概率。"
        ),
        "mechanism_note": (
            "多机制叠加：年中稳增长政策节奏（如 2022-05-23 国常会阶段性减征乘用车购置税）+ "
            "国际产业事件节奏 + A 股中报预告披露日历（6 月中下旬）+ 月度产销与渗透率数据发布日历。"
            "属于 CALENDAR_DRIVEN 为主的时间型规律，**不是** SEASONAL_DEMAND（无终端需求季节性证据）。"
        ),
        "mechanism_evidence": [
            {
                "note": "年中稳增长政策窗口（国常会 / 财政部细则集中于 5–6 月）",
                "evidence_strength": "SUPPORTED_BY_PUBLIC_RECORD",
            },
            {
                "note": "A 股中报业绩预告披露窗口（6 月中下旬进入密集期）—— 制度性日历",
                "evidence_strength": "PUBLIC_SCHEDULE_FACT",
            },
            {
                "note": "新能源车月度产销 / 渗透率数据在次月中旬公布 —— 制度性日历",
                "evidence_strength": "PUBLIC_SCHEDULE_FACT",
            },
            {
                "note": "国际产业事件与展会节奏偏北半球夏季",
                "evidence_strength": "MULTI_YEAR_OBSERVATION",
            },
        ],
        "limitations": [
            "样本仅 2018–2025（有效观测 7 年，2018 为反例年）。",
            "全部锚点日期均为**研究候选日期**，未经行情人工最终核验（verification_method 多为 unknown）。",
            "ThreeC 只记录「形成了 Campaign 的主题」，存在**幸存者偏差**："
            "无法观测「同样在 6 月出现但未成势」的主题。",
            "研究样本自身的事件台账 6 月占比 33%（均匀基准 8.3%）→ 时间聚集含研究选择偏差成分。",
            "2019 锚点为弱事件驱动（event_driven / weak），2022 锚点落在窗口之外。",
            "本例为**探索性历史规律**：样本有限，仅表示历史复现情况，不代表未来重演。",
        ],
    },
    {
        "family_id": "AUTO_SMART_DRIVING",
        "source_pattern_id": "SOP-01",
        "title": "汽车智能化启动观察窗口",
        "theme_scope": "汽车",
        "theme_key": "汽车 / 智能驾驶大主题（自动驾驶 · 车路云 · Robotaxi）",
        "definition": {
            "rule_ids": ["rule_auto_summer"],
            "main_theme_names": [
                "智能驾驶/无人驾驶",
                "车路云一体化/车路协同",
                "Robotaxi/无人驾驶/智能网约车",
            ],
        },
        "pattern_type": "MIXED",
        "primary_mechanism": "CALENDAR_DRIVEN",
        "description": (
            "汽车智能化（自动驾驶 / 车路云 / Robotaxi）方向的研究观察起点集中在 6 月中旬前后，"
            "但样本只有 4 年且前后半段存在轻度漂移，**未达 Timeline 门槛**，仅作为研究层记录。"
        ),
        "mechanism_note": (
            "政策**预期**窗口 + 国际产业事件 + 中报预告日历；注意政策落地时点本身并不在 6 月"
            "（如智能网联准入试点成文于 2023-11-17、车路云试点名单公布于 2024-07-01）。"
        ),
        "mechanism_evidence": [
            {
                "note": "政策落地时点不在 6 月，机制更接近「预期窗口」而非政策发布日本身",
                "evidence_strength": "SUPPORTED_BY_PUBLIC_RECORD",
            }
        ],
        "limitations": [
            "N=4 < 最低纳入标准（5），且 2019 锚点为弱事件驱动，与其他年份不是同一强度样本。",
            "前后半段存在 MILD_DRIFT（中位位移约 −27.5 天）→ 不稳定。",
            "全部锚点为研究候选日期，未经行情人工最终核验。",
        ],
    },
    {
        "family_id": "AUTO_NEV_ELECTRIFICATION",
        "source_pattern_id": "SOP-02",
        "title": "汽车电动化启动观察窗口",
        "theme_scope": "汽车",
        "theme_key": "汽车 / 新能源（新能源车 · 动力电池 · 特斯拉产业链）",
        "definition": {
            "rule_ids": ["rule_auto_summer"],
            "main_theme_names": ["新能源汽车/电池", "特斯拉产业链"],
        },
        "pattern_type": "INDUSTRY_CYCLE",
        "primary_mechanism": "INDUSTRY_CYCLE",
        "description": (
            "汽车电动化方向两年（2020 / 2021）的研究观察起点完全相同（06-01），"
            "但 N=2 的「完全重合」是**样本量幻觉**，不构成可固化规律；保留在 Artifact 供扩样后复查。"
        ),
        "mechanism_note": (
            "产销数据与产能节奏（INDUSTRY_CYCLE）：新能源车月度产销与渗透率数据在年中发布后强化叙事。"
        ),
        "mechanism_evidence": [
            {
                "note": "新能源车月度产销 / 渗透率数据的发布节奏",
                "evidence_strength": "PUBLIC_SCHEDULE_FACT",
            }
        ],
        "limitations": [
            "N=2 < 最低纳入标准；两点完全重合会让集中度指标与经验检验出现**假显著**，不得当作证据。",
            "两年锚点均为研究候选日期，未经行情人工核验。",
            "本条目是「样本量幻觉」的教学案例：**最「漂亮」的集中度反而最不可用**。",
        ],
    },
    {
        "family_id": "PHARMA_ALL",
        "source_pattern_id": "SOP-04",
        "title": "医药健康结构性升级启动窗口",
        "theme_scope": "医药健康",
        "theme_key": "医药健康（创新药 · 疫情医疗 · 中医药）",
        "definition": {"rule_ids": ["rule_pharma_upgrade"]},
        "pattern_type": "CALENDAR_DRIVEN",
        "primary_mechanism": "CALENDAR_DRIVEN",
        "description": (
            "医药健康方向**未**发现时间聚集：三个锚点分散在三个不同月份（11-01 / 01-02 / 01-23），"
            "且留一法显示结果完全由单一年份（2020 疫情）决定 → 已拒绝。"
        ),
        "mechanism_note": (
            "政策日期本身分散（集采 2018-12-17、科创板 2019-07-22、医保谈判 2019-11-28），"
            "不支持「1 月集中」；且含一个不可重复的外生冲击（2020 疫情）。"
        ),
        "mechanism_evidence": [
            {
                "note": "医药是数据集中**唯一**跨年重复的 Theme Cycle，却恰恰不构成时间规律",
                "evidence_strength": "NEGATIVE_FINDING",
            }
        ],
        "limitations": [
            "N=3；锚点分属 3 个月，无法构建任何日级 / 月级窗口。",
            "留一法中位位移约 141 天 → 完全由单一年份主导。",
            "2019 锚点（01-02）实为本地数据窗口起点，不是真实主题起点。",
        ],
    },
]

# ---------------------------------------------------------------- 基础工具


def parse_iso(s):
    """严格解析 YYYY-MM-DD（不依赖 dateutil）。"""
    if not isinstance(s, str) or len(s) < 10:
        return None
    try:
        y, m, d = int(s[0:4]), int(s[5:7]), int(s[8:10])
        if not (1 <= m <= 12 and 1 <= d <= 31):
            return None
        return (y, m, d)
    except ValueError:
        return None


def is_leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def days_in_year(y):
    return 366 if is_leap(y) else 365


_MD_TABLE = None


def md_table():
    """非闰年 365 天的日序 → MM-DD 表（窗口边界按非闰年基准呈现，跨年可比）。"""
    global _MD_TABLE
    if _MD_TABLE is None:
        _MD_TABLE = []
        per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        for m, n in enumerate(per_month, start=1):
            for d in range(1, n + 1):
                _MD_TABLE.append(f"{m:02d}-{d:02d}")
    return _MD_TABLE


def doy_norm(ymd):
    """闰年归一日序（1–365）：3 月 1 日起 -1，使 06-18 在任何年份得到同一序数。"""
    y, m, d = ymd
    n = sum([31, 29 if is_leap(y) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][: m - 1]) + d
    if m >= 3 and is_leap(y):
        n -= 1
    return n


def md_of_doy(n):
    """日序（1–365）→ MM-DD；超出范围做环形包裹（跨年窗口用）。"""
    t = md_table()
    idx = int(round(n)) - 1
    idx %= 365
    return t[idx]


def doy_of_md(md):
    """MM-DD → 日序（1–365）。"""
    m, d = int(md[0:2]), int(md[3:5])
    return sum([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][: m - 1]) + d


# ---------------------------------------------------------------- 读取输入


def load_export():
    with io.open(EXPORT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def db_anchor_quality(conn):
    """(campaign_id, date_role) → verification_method / confidence（数据质量口径，只读）。"""
    cur = conn.cursor()
    cur.execute(
        "SELECT campaign_id, date_role, verification_method, confidence, verified_date "
        "FROM campaign_date_observations"
    )
    return {(r[0], r[1]): {"method": r[2], "confidence": r[3], "verified": r[4]} for r in cur.fetchall()}


def db_annual_reviews(conn):
    cur = conn.cursor()
    cur.execute("SELECT rule_id, year, status FROM annual_reviews")
    return {(r[0], r[1]): r[2] for r in cur.fetchall()}


# ---------------------------------------------------------------- 锚点提取（统一优先级）


def anchor_of(obj, signals_of):
    """按统一优先级返回 (date, anchor_type, source_detail)；无法判定返回 (None, None, None)。"""
    lc = {s.get("stage"): s for s in (obj.get("lifecycle") or [])}

    # 1. Early Signal（三种既有载体，取最早可用者）
    es = obj.get("early_signal")
    if isinstance(es, dict) and es.get("start"):
        return es["start"], ANCHOR_EARLY, "export.early_signal.start"
    if isinstance(es, str) and es:
        return es, ANCHOR_EARLY, "export.early_signal"
    if (lc.get("EARLY_SIGNAL") or {}).get("start"):
        return lc["EARLY_SIGNAL"]["start"], ANCHOR_EARLY, "lifecycle.EARLY_SIGNAL.start"
    dates = sorted(
        s.get("date") for s in signals_of if s.get("type") == "EARLY_SIGNAL" and s.get("date")
    )
    if dates:
        return dates[0], ANCHOR_EARLY, "signals[].EARLY_SIGNAL(min)"

    # 2. Formation Anchor（不取「lifecycle 最早阶段」——那会把 Early Signal 误当 Formation）
    if (lc.get("THEME_FORMING") or {}).get("start"):
        return lc["THEME_FORMING"]["start"], ANCHOR_FORMING, "lifecycle.THEME_FORMING.start"
    if (lc.get("BROAD_CONFIRMATION") or {}).get("start"):
        return lc["BROAD_CONFIRMATION"]["start"], ANCHOR_BROAD, "lifecycle.BROAD_CONFIRMATION.start"

    # 3. Campaign start（末选）
    if obj.get("start_date"):
        return obj["start_date"], ANCHOR_START, "campaign.start_date"

    return None, None, None


def main_theme_names(obj):
    return [t.get("name") for t in (obj.get("themes") or []) if t.get("role") == "main"]


def macro_theme_of(obj):
    for t in obj.get("themes") or []:
        if t.get("theme_type") in ("industry", "sector") and t.get("role") == "related":
            return t.get("name")
    return None


def collect_units(export, quality):
    """全量对象 → 原始锚点行（Campaign 与 Research Candidate 并列）。"""
    signals_by = {}
    for s in export.get("signals") or []:
        key = s.get("campaign_id") or s.get("research_candidate_id")
        if key:
            signals_by.setdefault(key, []).append(s)

    units = []
    for kind, key in (("campaign", "campaigns"), ("research_candidate", "research_candidates")):
        for obj in export.get(key) or []:
            cid = obj.get("campaign_id")
            if not cid:
                continue
            date, atype, src = anchor_of(obj, signals_by.get(cid, []))
            q = quality.get((cid, "start")) or {}
            units.append(
                {
                    "kind": kind,
                    "campaign_id": cid,
                    "title": obj.get("title") or cid,
                    "year": obj.get("year"),
                    "rule_id": obj.get("rule_id"),
                    "theme_cycle_id": obj.get("theme_cycle_id"),
                    "macro_theme": macro_theme_of(obj),
                    "main_themes": main_theme_names(obj),
                    "anchor_date": date,
                    "anchor_type": atype,
                    "anchor_source": src,
                    "research_status": obj.get("research_status"),
                    "has_conflict": bool(obj.get("conflicts")),
                    "verification_method": q.get("method"),
                    "verified_date": q.get("verified"),
                }
            )
    return units


def family_members(units, fam):
    """按声明式定义取族成员。"""
    out = []
    rule_ids = set(fam["definition"].get("rule_ids") or [])
    theme_names = set(fam["definition"].get("main_theme_names") or [])
    for u in units:
        if u["anchor_date"] is None:
            continue
        if rule_ids and u["rule_id"] not in rule_ids:
            continue
        if theme_names and not (theme_names & set(u["main_themes"])):
            continue
        out.append(u)
    return out


def aggregate_by_year(members):
    """年度去重：同一年只取**最早**锚点（防止同年多 Campaign 人为放大 N）。"""
    by_year = {}
    for u in members:
        y = u["year"]
        if y is None:
            continue
        cur = by_year.get(y)
        if cur is None or u["anchor_date"] < cur["anchor_date"]:
            by_year[y] = u
    return [by_year[y] for y in sorted(by_year)]


# ---------------------------------------------------------------- 统计


def build_window(center_doy, mad_days, k=1.0):
    """典型窗口半径 = round(1.4826 × MAD × k)。MAD 用**浮点**（不先取整，避免人为放宽窗口）。"""
    half = int(round(1.4826 * mad_days * k))
    return center_doy - half, center_doy + half


def compute_stats(units):
    """单一主题族的描述统计（中位与 MAD 保留浮点用于计算，整日用于呈现）。"""
    doys = [doy_norm(parse_iso(u["anchor_date"])) for u in units]
    years = [u["year"] for u in units]
    n = len(doys)
    srt = sorted(doys)

    median_f = statistics.median(srt)
    center = int(round(median_f))
    mad_f = statistics.median([abs(x - center) for x in srt])
    if n >= 4:
        q = statistics.quantiles(srt, n=4, method="inclusive")
        p25, p75 = q[0], q[2]
    else:
        p25, p75 = srt[0], srt[-1]
    iqr = p75 - p25

    span = srt[-1] - srt[0]
    uniform_span = (n - 1) / (n + 1) * 365 if n >= 2 else 0.0
    ratio = (span / uniform_span) if uniform_span else None

    stats_out = {
        "n": n,
        "years": years,
        "doys": doys,
        "median_f": median_f,
        "center_doy": center,
        "center_md": md_of_doy(center),
        "mad_f": mad_f,
        "mad_days": int(round(mad_f)),
        "iqr_days": round(iqr, 2),
        "p25_md": md_of_doy(p25),
        "p75_md": md_of_doy(p75),
        "span_days": span,
        "uniform_expected_span_days": round(uniform_span, 2),
        "concentration_ratio": round(ratio, 4) if ratio is not None else None,
        "earliest_md": md_of_doy(srt[0]),
        "latest_md": md_of_doy(srt[-1]),
        "month_distribution": {},
    }
    for x in srt:
        m = md_of_doy(x)[0:2]
        stats_out["month_distribution"][m] = stats_out["month_distribution"].get(m, 0) + 1
    return stats_out


def window_stats(units, center, mad_f):
    """给定中位 / MAD 的窗口与其复现（主窗口与 LOO 复用同一实现，保证口径一致）。"""
    if center is None:
        return None
    ws, we = build_window(center, mad_f)
    hits, misses = [], []
    for u in units:
        d = doy_norm(parse_iso(u["anchor_date"]))
        (hits if ws <= d <= we else misses).append(u["year"])
    return {
        "start": md_of_doy(ws),
        "end": md_of_doy(we),
        "width_days": we - ws + 1,
        "matched_years": hits,
        "missed_years": misses,
        "hits": len(hits),
        "n": len(units),
    }


def stability_stats(units, stats):
    """年份切前后两半比较中位位移（N < 4 不做：位移对单点过于敏感）。"""
    years = stats["years"]
    n = len(years)
    if n < 4:
        return {"status": "INSUFFICIENT_N", "note": "N<4，不做前后半段检验（位移对单点过于敏感）。"}
    half = n // 2
    first = [u for u in units if u["year"] in years[:half]]
    second = [u for u in units if u["year"] in years[half:]]
    f1 = statistics.median([doy_norm(parse_iso(u["anchor_date"])) for u in first])
    f2 = statistics.median([doy_norm(parse_iso(u["anchor_date"])) for u in second])
    shift = f2 - f1
    if abs(shift) >= 45:
        flag = "DRIFTING"
    elif abs(shift) >= 21:
        flag = "MILD_DRIFT"
    else:
        flag = "STABLE"
    return {
        "status": "SPLIT",
        "first_years": years[:half],
        "second_years": years[half:],
        "first_center_md": md_of_doy(int(round(f1))),
        "second_center_md": md_of_doy(int(round(f2))),
        "median_shift_days": round(shift, 1),
        "drift_flag": flag,
        "note": "|位移| ≥ 45d → DRIFTING；21–44d → MILD_DRIFT；< 21d → STABLE。",
    }


def loo_stats(units, stats):
    """留一法：逐点剔除后重算中位与窗口，判断规律是否由单一年份主导。

    **主导判据只用中位位移（≥ 45 天）**。命中数变化只作为参考信息记录，不作为判据 ——
    因为窗口宽度会随样本重算而变化，边缘年份会让命中数跳动 1–2 个，属于窗口边缘效应，
    而不是「单年主导」。
    """
    base_win = window_stats(units, stats["center_doy"], stats["mad_f"])
    base_hits = base_win["hits"] if base_win else 0
    max_shift, max_drop = 0.0, 0
    for i in range(len(units)):
        rest = [u for j, u in enumerate(units) if j != i]
        if len(rest) < 2:
            continue
        s2 = compute_stats(rest)
        max_shift = max(max_shift, abs(s2["center_doy"] - stats["center_doy"]))
        if len(rest) >= 3:
            w2 = window_stats(rest, s2["center_doy"], s2["mad_f"])
            if w2:
                max_drop = max(max_drop, base_hits - w2["hits"])
    dominated = max_shift >= 45
    return {
        "base_hits": base_hits,
        "max_center_shift_days": float(max_shift),
        "max_hit_drop": int(max_drop),
        "single_year_dominated": bool(dominated),
        "note": (
            "判据：剔除任一年后中位位移 ≥ 45 天 → 结果由单一年份主导（不构成时间规律）。"
            "命中数变化（max_hit_drop）仅作参考，不参与判定。"
        ),
    }


# ---------------------------------------------------------------- 判定


def judge(stats, stability, loo):
    """窗口可构建 / 研究强度 / 状态 / Timeline 纳入判定（全部可复核）。"""
    n = stats["n"]
    ratio = stats["concentration_ratio"]
    drift = stability.get("drift_flag") if stability.get("status") == "SPLIT" else None
    window_buildable = n >= 3 and stats["iqr_days"] <= 90.0
    dominated = loo["single_year_dominated"]

    # 研究强度 A/B/C/D —— 「统计聚集强度」与「可固化程度」（status）是两个维度
    if dominated or (window_buildable is False and n >= 3):
        strength = "D"
    elif n >= 7 and ratio is not None and ratio <= 0.45 and drift == "STABLE" and window_buildable:
        strength = "A"
    elif n >= 4 and ratio is not None and ratio <= 0.60 and drift != "DRIFTING" and window_buildable:
        strength = "B"
    else:
        strength = "C"

    status = {"D": "REJECTED", "C": "EXPLORATORY"}.get(strength, "MODERATE_CANDIDATE")

    if (
        n >= 5
        and window_buildable
        and ratio is not None
        and ratio <= 0.45
        and drift == "STABLE"
        and not dominated
    ):
        eligibility = "TIMELINE_ELIGIBLE"
        reason = (
            f"N={n} ≥ 5；集中度比率 {ratio} ≤ 0.45；前后半段 {drift}；留一法无单年主导 → "
            "满足 Timeline 最低门槛（必须以「宽窗口 + 明确机制类别 + 非预测文案」呈现）。"
        )
    elif dominated:
        eligibility = "REJECTED"
        reason = (
            f"留一法显示结果由单一年份主导（最大中位位移 {round(loo['max_center_shift_days'], 1)} 天）"
            "→ 不构成时间规律。"
        )
    elif not window_buildable and n >= 3:
        eligibility = "REJECTED"
        reason = (
            f"N={n}、IQR={stats['iqr_days']} 天 → 锚点跨三个以上季节（或样本不足以定窗口），"
            "无法构建有意义的观察窗口。"
        )
    elif n < 5:
        eligibility = "RESEARCH_ONLY"
        extra = ""
        if n == 2:
            extra = "；且 N=2 的「完全重合」属样本量幻觉，不得当作证据"
        if drift == "MILD_DRIFT":
            extra += "；另有轻度漂移（MILD_DRIFT）"
        reason = f"N={n} < 最低纳入标准（5），样本不足，先留在研究层{extra}。"
    else:
        eligibility = "RESEARCH_ONLY"
        reason = (
            f"未达集中度 / 稳定性门槛（集中度比率 {ratio}、漂移 {drift}）→ 暂不进入 Timeline。"
        )

    return {
        "window_buildable": window_buildable,
        "research_strength": strength,
        "status": status,
        "timeline_eligibility": eligibility,
        "timeline_eligible": eligibility == "TIMELINE_ELIGIBLE",
        "reason": reason,
    }


def data_quality_of(units, quality_rows):
    methods, statuses = {}, {}
    verified = 0
    for u in units:
        m = u.get("verification_method") or "unknown"
        methods[m] = methods.get(m, 0) + 1
        s = u.get("research_status") or "UNKNOWN"
        statuses[s] = statuses.get(s, 0) + 1
        if u.get("verified_date"):
            verified += 1
    n = len(units)
    if verified == n and n > 0:
        grade = "HIGH"
    elif verified > 0:
        grade = "MEDIUM"
    else:
        grade = "MEDIUM" if n > 0 else "UNKNOWN"
    return {
        "grade": grade,
        "anchor_precision": "EXACT_DATE（日级）",
        "verified_anchors": verified,
        "unverified_anchors": n - verified,
        "verification_methods": methods,
        "research_status_counts": statuses,
        "note": (
            "全部锚点为研究候选日期，未经行情人工最终核验 → 数据质量上限为 MEDIUM；"
            "这份数据不足以支撑「稳定规律」级别（N≥8 且多机制复核）的结论。"
        ),
    }


# ---------------------------------------------------------------- 组装 Artifact


def build_artifact():
    export = load_export()
    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    try:
        quality = db_anchor_quality(conn)
        annual = db_annual_reviews(conn)
    finally:
        conn.close()

    units = collect_units(export, quality)
    anchor_counts = {}
    for u in units:
        anchor_counts[u["anchor_type"] or "NONE"] = anchor_counts.get(u["anchor_type"] or "NONE", 0) + 1

    patterns = []
    for idx, fam in enumerate(FAMILIES, start=1):
        members = family_members(units, fam)
        agg = aggregate_by_year(members)
        stats = compute_stats(agg)
        stability = stability_stats(agg, stats)
        loo = loo_stats(agg, stats)
        verdict = judge(stats, stability, loo)
        # 窗口只在「可构建」时生成：不可构建的族不得输出一个看起来可用的窗口（避免伪造确定性）
        win = (
            window_stats(agg, stats["center_doy"], stats["mad_f"])
            if verdict["window_buildable"]
            else None
        )

        observations = [
            {
                "year": u["year"],
                "date": u["anchor_date"],
                "md": "%s-%s" % (u["anchor_date"][5:7], u["anchor_date"][8:10]),
                "campaign_id": u["campaign_id"],
                "title": u["title"],
                "kind": u["kind"],
                "anchor_source": u["anchor_source"],
                "in_typical_window": (
                    win["start"] <= "%s-%s" % (u["anchor_date"][5:7], u["anchor_date"][8:10]) <= win["end"]
                    if win
                    else None
                ),
            }
            for u in agg
        ] if win else [
            {
                "year": u["year"],
                "date": u["anchor_date"],
                "md": "%s-%s" % (u["anchor_date"][5:7], u["anchor_date"][8:10]),
                "campaign_id": u["campaign_id"],
                "title": u["title"],
                "kind": u["kind"],
                "anchor_source": u["anchor_source"],
                "in_typical_window": None,
            }
            for u in agg
        ]

        ratio = stats["concentration_ratio"]
        typical_window = None
        if verdict["window_buildable"] and win:
            typical_window = {
                "start": win["start"],
                "end": win["end"],
                "width_days": win["width_days"],
                "method": "Median ± 1×MAD（MAD 乘以 1.4826 一致化）",
                "center_date": stats["center_md"],
                "alternative_quantile_window": {
                    "start": stats["p25_md"],
                    "end": stats["p75_md"],
                    "method": "P25–P75",
                },
                "degraded_month_window": (
                    "%s ~ %s（放弃日级精度时的粗略口径）"
                    % (stats["p25_md"][0:2], stats["p75_md"][0:2])
                ),
            }

        patterns.append(
            {
                "pattern_id": "TOP-%02d" % idx,
                "source_pattern_id": fam["source_pattern_id"],
                "pattern_type": fam["pattern_type"],
                "title": fam["title"],
                "description": fam["description"],
                "theme_scope": fam["theme_scope"],
                "theme_key": fam["theme_key"],
                "family_definition": fam["definition"],
                "anchor_type": ANCHOR_EARLY if all(
                    u["anchor_type"] == ANCHOR_EARLY for u in agg
                ) else "MIXED_ANCHOR",
                "anchor_note": (
                    "全部年份均取到 EARLY_SIGNAL（未退化到 Formation / Campaign.start），"
                    "口径统一，不存在「部分年份用 A、部分年份用 B」的污染。"
                    if all(u["anchor_type"] == ANCHOR_EARLY for u in agg)
                    else "各年锚点类型不一致（已在 observations[].anchor_source 逐条标注）。"
                ),
                "eligible_years": stats["years"],
                "observation_count": stats["n"],
                "observations": observations,
                "typical_window": typical_window,
                "center_date": stats["center_md"],
                "dispersion": {
                    "iqr_days": stats["iqr_days"],
                    "mad_days": stats["mad_days"],
                    "span_days": stats["span_days"],
                    "earliest_md": stats["earliest_md"],
                    "latest_md": stats["latest_md"],
                },
                "recurrence": {
                    "matched_years": win["matched_years"] if win else [],
                    "missed_years": win["missed_years"] if win else [],
                    "eligible_years": stats["n"],
                    "matched_count": win["hits"] if win else 0,
                    "historical_ratio": (
                        round(win["hits"] / stats["n"], 4) if win and stats["n"] else None
                    ),
                    "label": "历史样本中的窗口复现情况（不是未来概率）",
                },
                "stability": stability,
                "leave_one_out": loo,
                "data_quality": data_quality_of(agg, quality),
                "research_strength": {
                    "grade": verdict["research_strength"],
                    "rationale": (
                        "N=%d；集中度比率 %s；漂移 %s；单年主导 %s。"
                        % (
                            stats["n"],
                            ratio,
                            stability.get("drift_flag", stability.get("status")),
                            loo["single_year_dominated"],
                        )
                    ),
                },
                "status": verdict["status"],
                "timeline_eligibility": verdict["timeline_eligibility"],
                "timeline_eligible": verdict["timeline_eligible"],
                "timeline_eligibility_reason": verdict["reason"],
                "mechanism": {
                    "type": fam["pattern_type"],
                    "primary_mechanism": fam["primary_mechanism"],
                    "note": fam["mechanism_note"],
                    "is_lunar_driven": False,
                    "lunar_note": (
                        "以春节为基准的偏移跨度 85–191 天（约 106 天）→ 该规律**不是**农历型，"
                        "任何「春节后第 N 天」的表达都是错的。"
                    ),
                    "evidence": fam["mechanism_evidence"],
                },
                "limitations": fam["limitations"],
                "provenance": {
                    "source": "ThreeC 2018–2025 历史研究数据（canonical export + research DB）",
                    "generated_by": "research/scripts/build_time_observation_patterns.py",
                    "snapshot_date": SNAPSHOT_DATE,
                },
            }
        )

    eligible = [p for p in patterns if p["timeline_eligibility"] == "TIMELINE_ELIGIBLE"]

    artifact = {
        "artifact": "time_observation_patterns",
        "artifact_version": ARTIFACT_VERSION,
        "contract_note": (
            "Research Artifact —— 不是产品 schema，不进入 DB / schema.sql / "
            "timeline_export_v1.json / contracts。产品端只读消费。"
        ),
        "generated_at": SNAPSHOT_DATE,
        "generated_by": "research/scripts/build_time_observation_patterns.py",
        "snapshot_date": SNAPSHOT_DATE,
        "research_round": "time-observation-pattern-v0.1",
        "supersedes": {
            "exploratory_artifact": "research/research/reports/seasonal_observation_patterns_v0_1.json",
            "exploratory_report": "research/research/reports/Seasonal_Observation_Pattern_Discovery_v0_1.md",
            "note": (
                "上游探索研究确立了锚点口径与拒绝规则；本 Artifact 是可复现生成器重新计算后的"
                "**产品可消费版本**，模式编号改为 TOP-*（与 SOP-* 一一对应并由 source_pattern_id 保留）。"
            ),
        },
        "question": "历史上，一年中的这个时间位置附近，反复出现过值得研究的主题启动 / 观察现象吗？",
        "not_a": [
            "这不是预测器，也不做任何形式的未来推断",
            "这不给出买入或卖出时间",
            "这不指示最佳埋伏点",
            "这不做涨幅预测",
            "这不计算胜率",
            "这不输出未来概率",
            "这不做收益预测",
        ],
        "method": (
            "三阶段：① Historical Campaign / Research Candidate → Anchor Extraction（统一优先级）；"
            "② 主题族逐年聚合（同一年只取最早锚点，防止人为放大 N）；③ 描述统计 + 稳定性 + 留一法 → "
            "纳入判定。全程不修改 Campaign 定义，不使用行情涨幅定义「启动」。"
        ),
        "anchor_priority": ANCHOR_PRIORITY,
        "pattern_type_vocabulary": PATTERN_TYPES,
        "status_vocabulary": STATUS_VOCABULARY,
        "timeline_eligibility_vocabulary": ELIGIBILITY_VOCABULARY,
        "inclusion_rules": {
            "timeline_eligible": "N ≥ 5 且 窗口可构建 且 集中度比率 ≤ 0.45 且 STABLE 且 无单年主导",
            "rejected": "窗口不可构建（IQR > 90 天）或 留一法显示单年主导",
            "research_only": "其余（样本不足，或稳定性 / 集中度未达门槛）",
            "window_definition": "典型窗口 = Median ± 1×MAD×1.4826（抗离群；A/B/C 三种口径并列保留）",
            "note": "宁可少，也不把明显不可靠的规律放进 Timeline。",
        },
        "forbidden_fields": FORBIDDEN_FIELDS,
        "label_vocabulary": {
            "window": "历史观察窗口",
            "recurrence": "历史复现",
            "in_window": "当前位于历史观察窗口",
            "near_window": "接近历史观察窗口",
            "none": "当前没有发现处于历史时间观察窗口的模式",
            "disclaimer": "这是历史时间聚集现象，不代表今年必然重演，也不是买入或卖出信号。",
        },
        "background_baseline": {
            "note": (
                "时间聚集不能只靠「某月事件多」证明：ThreeC 自建事件台账本身 6 月占比 33%（10/30），"
                "远高于均匀基准 8.3%；即使只看指数「最优 30 日窗口」，6 月占比也达 18.75%。"
                "因此本 Artifact 中任何 6 月偏好都**部分来自研究样本选择偏差**，不可解读为主题独有季节性。"
            ),
            "event_calendar_june_share": 0.3333,
            "index_best_30d_window_june_share": 0.1875,
            "uniform_june_share": 0.0833,
        },
        "coverage": {
            "years_observed": sorted({u["year"] for u in units if u["year"]}),
            "excluded_years": [
                {"year": y, "reason": st, "rule_id": rid}
                for (rid, y), st in sorted(annual.items())
                if st == "no_clear_campaign"
            ],
            "total_objects": len(units),
            "campaigns": sum(1 for u in units if u["kind"] == "campaign"),
            "research_candidates": sum(1 for u in units if u["kind"] == "research_candidate"),
            "anchor_type_counts": anchor_counts,
            "annual_review_status": {
                f"{rid}#{y}": st for (rid, y), st in sorted(annual.items())
            },
        },
        "summary": {
            "patterns_total": len(patterns),
            "timeline_eligible": [p["pattern_id"] for p in eligible],
            "research_only": [
                p["pattern_id"] for p in patterns if p["timeline_eligibility"] == "RESEARCH_ONLY"
            ],
            "rejected": [
                p["pattern_id"] for p in patterns if p["timeline_eligibility"] == "REJECTED"
            ],
            "note": (
                "本轮只有一条 Pattern 达到 Timeline 门槛，且它仍是**探索性**的"
                "（样本 7 年、全部研究候选日期）——产品必须以此口径呈现。"
            ),
        },
        "patterns": patterns,
    }
    return artifact


# ---------------------------------------------------------------- 自检（写盘前）

ISO = None


def _iter_strings(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _iter_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _iter_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def validate_artifact(art):
    """自检：字段卫生 / 语义红线 / 结构与判定一致性。返回问题清单。"""
    issues = []

    for p in [p for p in art["patterns"]]:
        pid = p["pattern_id"]
        for f in FORBIDDEN_FIELDS:
            if f in p:
                issues.append(f"{pid}: 出现禁用字段 {f}")
        if p["pattern_type"] not in PATTERN_TYPES:
            issues.append(f"{pid}: pattern_type {p['pattern_type']} 不在枚举内")
        if p["status"] not in STATUS_VOCABULARY:
            issues.append(f"{pid}: status {p['status']} 不在枚举内")
        if p["timeline_eligibility"] not in ELIGIBILITY_VOCABULARY:
            issues.append(f"{pid}: timeline_eligibility 不在枚举内")
        if p["timeline_eligible"] != (p["timeline_eligibility"] == "TIMELINE_ELIGIBLE"):
            issues.append(f"{pid}: timeline_eligible 与 timeline_eligibility 不一致")
        if p["observation_count"] != len(p["observations"]):
            issues.append(f"{pid}: observation_count 与 observations 数量不一致")
        if p["observation_count"] == 0:
            issues.append(f"{pid}: 无观测样本")
        for o in p["observations"]:
            if parse_iso(o["date"]) is None:
                issues.append(f"{pid}: 观测日期非法 {o['date']}")
            if not (len(o["md"]) == 5 and o["md"][2] == "-"):
                issues.append(f"{pid}: md 格式非法 {o['md']}")
        if p["timeline_eligibility"] == "TIMELINE_ELIGIBLE":
            if not p["typical_window"]:
                issues.append(f"{pid}: TIMELINE_ELIGIBLE 必须带 typical_window")
            else:
                for k in ("start", "end"):
                    md = p["typical_window"][k]
                    if not (len(md) == 5 and md[2] == "-"):
                        issues.append(f"{pid}: 窗口 {k} 格式非法 {md}")
            if not p["limitations"]:
                issues.append(f"{pid}: TIMELINE_ELIGIBLE 必须带 limitations（避免被读成预测）")
            if p["recurrence"]["historical_ratio"] is None:
                issues.append(f"{pid}: TIMELINE_ELIGIBLE 必须带 historical_ratio")
            if p["status"] not in ("MODERATE_CANDIDATE", "STRONG_CANDIDATE"):
                issues.append(f"{pid}: TIMELINE_ELIGIBLE 的 status 与可固化程度不匹配")
        if p["recurrence"]["historical_ratio"] is not None and not (
            0.0 <= p["recurrence"]["historical_ratio"] <= 1.0
        ):
            issues.append(f"{pid}: historical_ratio 越界")

    ids = [p["pattern_id"] for p in art["patterns"]]
    if len(set(ids)) != len(ids):
        issues.append("pattern_id 重复")

    # 语义红线：面向用户的文本不得出现预测 / 买卖语义（否定语境除外）
    negations = ("不", "非", "无", "禁止", "未")
    for path, s in _iter_strings(art):
        for phrase in BANNED_PHRASES:
            idx = s.find(phrase)
            while idx >= 0:
                window = s[max(0, idx - 12) : idx]
                if not any(n in window for n in negations):
                    issues.append(f"{path}: 文本出现非否定语境的「{phrase}」→ 语义红线")
                idx = s.find(phrase, idx + 1)

    return issues


def main(argv):
    check_only = "--check" in argv
    do_print = "--print" in argv

    art = build_artifact()
    issues = validate_artifact(art)
    if issues:
        print("FAIL —— 自检未通过，不写文件：")
        for i in issues:
            print("  -", i)
        return 1

    text = json.dumps(art, ensure_ascii=False, indent=2) + "\n"

    if check_only:
        if not os.path.exists(OUT_PATH):
            print("FAIL —— 磁盘上不存在产物：", OUT_PATH)
            return 1
        with io.open(OUT_PATH, "r", encoding="utf-8") as f:
            cur = f.read()
        if cur == text:
            print("PASS —— 磁盘产物与重算结果逐字节一致（可复现）。")
            return 0
        print("FAIL —— 磁盘产物与重算结果不一致（research/ 下的 Artifact 必须由脚本生成）。")
        return 1

    with io.open(OUT_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

    print("=" * 72)
    print("Time Observation Pattern 生成完成（Phase 7.2）")
    print("=" * 72)
    print(f"产物: {os.path.relpath(OUT_PATH, ROOT)}")
    print(f"样本: {art['coverage']['total_objects']} 个历史对象 "
          f"（{art['coverage']['campaigns']} Campaign + "
          f"{art['coverage']['research_candidates']} Research Candidate）")
    print(f"锚点: {art['coverage']['anchor_type_counts']}")
    print("-" * 72)
    for p in art["patterns"]:
        w = p["typical_window"]
        win = f"{w['start']} ~ {w['end']}" if w else "（不生成窗口）"
        rec = p["recurrence"]
        print(f"  {p['pattern_id']} ← {p['source_pattern_id']}  {p['title']}")
        print(f"      N={p['observation_count']}  中心 {p['center_date']}  窗口 {win}  "
              f"复现 {rec['matched_count']}/{rec['eligible_years']}  "
              f"强度 {p['research_strength']['grade']}  状态 {p['status']}")
        print(f"      → {p['timeline_eligibility']}：{p['timeline_eligibility_reason']}")
    print("-" * 72)
    print("进入产品 Timeline：", ", ".join(art["summary"]["timeline_eligible"]) or "（无）")
    print("留在研究层：", ", ".join(art["summary"]["research_only"]) or "（无）")
    print("已拒绝：", ", ".join(art["summary"]["rejected"]) or "（无）")
    print("自检：PASS（字段卫生 / 语义红线 / 判定一致性）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
