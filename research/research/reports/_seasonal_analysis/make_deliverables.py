# -*- coding: utf-8 -*-
"""
TEMPORARY RESEARCH SCRIPT — Seasonal Observation Pattern Discovery v0.1
========================================================================
STATUS: 临时研究脚本。**不是产品代码 / 不是正式 schema。**
用途：把 pattern_validation.json + baseline_analysis.json + data_fitness.json
      合成为两个交付物：
        seasonal_observation_patterns_v0_1.json
        seasonal_observation_candidates_v0_1.csv
纪律：不含预测 / 未来概率 / 收益 / 胜率 / 买卖信号字段。
"""

import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
REPORT_DIR = os.path.join(REPO, "research", "research", "reports")

with open(os.path.join(HERE, "pattern_validation.json"), encoding="utf-8") as f:
    PV = json.load(f)
with open(os.path.join(HERE, "baseline_analysis.json"), encoding="utf-8") as f:
    BL = json.load(f)
with open(os.path.join(HERE, "data_fitness.json"), encoding="utf-8") as f:
    FIT = json.load(f)
with open(os.path.join(HERE, "family_analysis.json"), encoding="utf-8") as f:
    FA = json.load(f)

BASE_EVENT_JUNE = BL["T1_event_baseline"]["june_share"]
BASE_INDEX_JUNE = BL["T2_aggregate"]["june_share"]


def grade(n, span_ratio, p, rec_ratio, drift, loo_dominated, mech):
    """
    研究方法内部分级（不是投资评分）。输入全部是研究方法量。
    A = 数据支持较强的历史时间聚集现象
    B = 存在一定历史聚集，但样本 / 稳定性有限
    C = 探索性迹象，不能固化
    D = 没有发现足够证据
    """
    if n < 2:
        return "D", "样本不足以评估"
    if n == 2:
        return "C", "N=2，即使时间完全重合也不能视作稳定规律（样本量幻觉）"
    if n == 3:
        if span_ratio < 0.2 and p < 0.05 and not loo_dominated:
            return "B", "N=3 且集中度显著、无单年主导，但仍需扩样"
        return "C", "N=3 且集中度或稳健性不足"

    # N>=4
    score = 0
    why = []
    if span_ratio < 0.25:
        score += 2
        why.append(f"跨度仅为均匀基准的 {span_ratio:.2f}")
    elif span_ratio < 0.4:
        score += 1
        why.append(f"跨度约均匀基准的 {span_ratio:.2f}")
    if p is not None and p < 0.01:
        score += 2
        why.append(f"经验 p={p:.4f}")
    elif p is not None and p < 0.05:
        score += 1
        why.append(f"经验 p={p:.4f}")
    if rec_ratio >= 0.7:
        score += 1
        why.append(f"窗口复现 {rec_ratio:.0%}")
    if drift == "STABLE":
        score += 1
        why.append("前后半段无漂移")
    if not loo_dominated:
        score += 1
        why.append("无单一年份主导")
    if mech:
        score += 1
        why.append(f"有机制假设（{mech}）")

    if score >= 6:
        return "A", "；".join(why)
    if score >= 4:
        return "B", "；".join(why)
    if score >= 2:
        return "C", "；".join(why)
    return "D", "；".join(why) or "未发现足够证据"


PATTERNS = []

# ---------------------------------------------------------------- SOP-01
p1 = PV["SOP-01"]
ws = p1["windows"]["B_mad_k1.0"]
ws15 = p1["windows"]["B_mad_k1.5"]
rec = p1["historical_recurrence"]["B_mad_k1.0"]
g1, why1 = grade(p1["n_years"], p1["spread_ratio_vs_uniform"], p1["empirical_span_p_one_sided"],
                 rec["ratio"], p1["stability"].get("drift_flag", "INSUFFICIENT_N"),
                 p1["leave_one_out"].get("single_year_dominated", False), 1)
PATTERNS.append({
    "pattern_id": "SOP-01",
    "pattern_type": "MIXED",
    "theme_key": "汽车 / 智能驾驶大主题（自动驾驶 · 车路云 · Robotaxi）",
    "title": "汽车智能化启动观察窗口",
    "anchor_type": "EARLY_SIGNAL",
    "anchor_definition": "Anchor A —— lifecycle.EARLY_SIGNAL.start（四年全部可用，无需退化到 Formation / Campaign.start）",
    "level": "LEVEL_3 同机制不同 Campaign 主题族（跨 Theme Cycle 归一）",
    "eligible_years": p1["years"],
    "observed_years": p1["years"],
    "observations": [{"year": y, "campaign": c, "anchor_date": d}
                     for y, c, d in zip(p1["years"], p1["campaigns"], p1["anchor_dates"])],
    "typical_window": {
        "start": ws["start_md"], "end": ws["end_md"],
        "method": "Median ± 1×MAD（1.4826 σ 一致化）",
        "alternative_quantile_window": {"start": p1["windows"]["A_quantile_P25_P75"]["start_md"],
                                        "end": p1["windows"]["A_quantile_P25_P75"]["end_md"],
                                        "method": "P25–P75"},
        "alternative_wider_window": {"start": ws15["start_md"], "end": ws15["end_md"],
                                     "method": "Median ± 1.5×MAD"},
        "degraded_month_window": "06 月中旬 ~ 07 月上旬（若放弃日级精度）",
    },
    "center_date": p1["median_md"],
    "dispersion": {
        "iqr_days": p1["iqr_days"], "mad_days": p1["mad_days"],
        "span_days": p1["span_days"], "earliest": p1["earliest_md"], "latest": p1["latest_md"],
    },
    "time_concentration": {
        "spread_ratio_vs_uniform": p1["spread_ratio_vs_uniform"],
        "empirical_span_p_one_sided": p1["empirical_span_p_one_sided"],
        "month_distribution": p1["month_distribution"],
        "uniform_expected_span_days": 365 * (p1["n_years"] - 1) / (p1["n_years"] + 1),
        "note": "探索性描述统计。样本仅 4 年，p 值不作为显著性断言。",
    },
    "historical_recurrence": {
        "hits": rec["hits"], "n_years": rec["n_years"], "ratio": rec["ratio"],
        "hits_years": rec["hits_years"], "miss_years": rec["miss_years"],
        "label": "历史样本中的窗口复现情况（不是未来概率）",
    },
    "outside_window_contrast": {
        "window_width_days": 17,
        "window_share_of_year": 17 / 365,
        "hit_share": rec["ratio"],
        "density_ratio": rec["ratio"] / (17 / 365),
        "june_share": p1["month_distribution"].get("06", 0) / p1["n_years"],
        "baseline_june_share_event_calendar": BASE_EVENT_JUNE,
        "baseline_june_share_index_best30d": BASE_INDEX_JUNE,
        "lift_vs_event_baseline": (p1["month_distribution"].get("06", 0) / p1["n_years"]) / BASE_EVENT_JUNE,
        "lift_vs_index_baseline": (p1["month_distribution"].get("06", 0) / p1["n_years"]) / BASE_INDEX_JUNE,
    },
    "stability": p1["stability"],
    "drift": p1["stability"].get("drift_flag", "INSUFFICIENT_N"),
    "leave_one_out": {k: v for k, v in p1["leave_one_out"].items() if k != "per_removal"},
    "sample_size_sensitivity": {
        "n2_n3_n4_available": "N=4；若剔除 2019（唯一的 8 月锚点）→ N=3，跨度降至 12 天、集中度上升（更集中而非更分散）",
        "note": "结论对剔单年不敏感（max median shift 5d、max hit drop 1）。",
    },
    "evidence_basis": [
        "exports/timeline_export_v1.json campaigns[]: C-2019-AD / C-2023-AD / C-2024-V2X / C-2025-ROBOTAXI",
        "research/database/cycle_research.db campaign_phases + campaign_events",
        "research/research/annual/2019.md, 2023.md, 2024.md, 2025.md",
    ],
    "mechanism_hypotheses": [
        {"hypothesis": "工信部/部委智能网联政策与技术标准的发布节奏偏上半年末",
         "evidence_strength": "SUPPORTED_BY_PUBLIC_RECORD",
         "detail": "四部委《智能网联汽车准入和上路通行试点》成文 2023-11-17；五部门车路云 20 城试点名单公布 2024-07-01 — 即**政策落地时点并不在 6 月**。故机制更接近「政策**预期**窗口 + 国际产业事件」而非「政策发布日期本身」。",
         "temporal_note": "以上均为事后可查的公开记录，仅用于机制解释，不用于定义当时已知信息。"},
        {"hypothesis": "北京/武汉等地车路云大额招标与项目备案集中在上半年末（2024-06-14 武汉 170.84 亿）",
         "evidence_strength": "SINGLE_YEAR_OBSERVATION"},
        {"hypothesis": "特斯拉 Robotaxi / FSD 相关国际产业事件落在北半球夏季（2025-06-22 奥斯汀试点）",
         "evidence_strength": "SINGLE_YEAR_OBSERVATION"},
        {"hypothesis": "A 股半年报业绩预告密集披露窗口（6 月中旬起）提升成长主题的关注度",
         "evidence_strength": "PUBLIC_SCHEDULE_FACT",
         "detail": "A 股中报预告披露窗口期历来在 6 月中下旬进入密集期 — 属制度性日历，非行业季节性。"},
    ],
    "mechanism_class": "MIXED（政策/标准日历 + 国际产业事件 + 招标节奏 + 财报日历，多个机制叠加）",
    "calendar_vs_seasonal": "CALENDAR_DRIVEN 成分较高；不建议归类为 SEASONAL_DEMAND（无需求季节性证据）",
    "lunar_holiday_check": {
        "spring_festival_offset_days": [
            {"year": 2019, "anchor": "08-15", "days_after_spring_festival": 191},
            {"year": 2023, "anchor": "06-12", "days_after_spring_festival": 141},
            {"year": 2024, "anchor": "06-11", "days_after_spring_festival": 121},
            {"year": 2025, "anchor": "06-22", "days_after_spring_festival": 144},
        ],
        "finding": "距春节 121–191 天，跨度 70 天；农历相对位置**不集中**。→ 该规律是公历型（或事件型），不是农历型。",
        "nearest_fixed_anchors": ["618（4–7 天）", "中报预告窗口（6 月中）"],
    },
    "data_quality": {
        "anchor_precision": "EXACT_DATE（日级）",
        "verification": "campaign_date_observations.verification_method 多为 `unknown`（未经行情人工核验）",
        "research_status": "全部 PROVISIONAL（无 CONFLICT，无 VERIFIED）",
        "provisional_ratio": 1.0,
        "grade": "MEDIUM（日期有依据、主题可识别，但未经人工最终核验）",
    },
    "research_strength": {"grade": g1, "rationale": why1},
    "status": "MODERATE_CANDIDATE",
    "timeline_eligible": False,
    "timeline_ineligible_reason": "N=4 且 2019 锚点为弱事件驱动（event_driven / strength=weak），并非同一强度样本；建议先扩样至 N≥5 或完成日期人工核验。",
    "provenance": {
        "source": "ThreeC 2018–2025 历史研究数据（canonical export + research DB）",
        "generated_by": "offline research script（临时脚本，非产品代码）",
        "snapshot_date": "2026-09-16",
        "research_round": "seasonal-observation-pattern-v0.1",
    },
})

# ---------------------------------------------------------------- SOP-02
p2 = PV["SOP-02"]
PATTERNS.append({
    "pattern_id": "SOP-02",
    "pattern_type": "INDUSTRY_CYCLE",
    "theme_key": "汽车 / 新能源（新能源车 · 动力电池 · 特斯拉产业链）",
    "title": "汽车电动化启动观察窗口",
    "anchor_type": "EARLY_SIGNAL",
    "anchor_definition": "Anchor A —— lifecycle.EARLY_SIGNAL.start",
    "level": "LEVEL_2 同一 Macro Theme 下跨年重复出现的机制族",
    "eligible_years": [2020, 2021],
    "observed_years": [2020, 2021],
    "observations": [{"year": 2020, "campaign": "C-2020-NEV", "anchor_date": "2020-06-01"},
                     {"year": 2021, "campaign": "C-2021-NEV", "anchor_date": "2021-06-01"}],
    "typical_window": {"start": "06-01", "end": "06-01",
                       "method": "N=2 且两点完全重合 → **不生成日级窗口**（样本量幻觉风险）",
                       "degraded_month_window": "6 月上旬（唯一可接受的口径）"},
    "center_date": "06-01",
    "dispersion": {"iqr_days": 0.0, "mad_days": 0.0, "span_days": 0,
                   "earliest": "06-01", "latest": "06-01"},
    "time_concentration": {
        "spread_ratio_vs_uniform": 0.0, "empirical_span_p_one_sided": p2["empirical_span_p_one_sided"],
        "month_distribution": {"06": 2},
        "note": "两点完全重合会产生 ratio=0、p≈0.003 的**假象级显著性**。这正是 N=2 的样本量幻觉，**不得**当作证据。",
    },
    "historical_recurrence": {"hits": 2, "n_years": 2, "ratio": 1.0,
                              "hits_years": [2020, 2021], "miss_years": [],
                              "label": "历史样本中的窗口复现情况（不是未来概率）"},
    "outside_window_contrast": {
        "note": "N=2 无法做有效窗口外对照（全年只有一个可用子集）。",
        "baseline_june_share_event_calendar": BASE_EVENT_JUNE,
    },
    "stability": {"status": "INSUFFICIENT_N", "note": "N=2<4，不做前后半段检验"},
    "drift": "UNKNOWN",
    "sample_size_sensitivity": {"note": "N=2 → 按拒绝规则默认 Exploratory，不纳入正式 Pattern"},
    "evidence_basis": ["exports/timeline_export_v1.json campaigns[]: C-2020-NEV / C-2021-NEV",
                       "research/research/annual/2020.md, 2021.md"],
    "mechanism_hypotheses": [
        {"hypothesis": "新能源车月度产销数据在年中公布后强化「渗透率跃升」叙事",
         "evidence_strength": "PUBLIC_RECORD（2021 年 6 月新能源渗透率升至 12%+，见 AR-2021）"},
        {"hypothesis": "特斯拉/电池龙头的市值里程碑事件（2020-06 特斯拉破千美元；2021-05-31 宁德破万亿）集中于上半年末",
         "evidence_strength": "SINGLE_YEAR_EACH"},
    ],
    "mechanism_class": "INDUSTRY_CYCLE",
    "calendar_vs_seasonal": "INDUSTRY_CYCLE（产销数据与产能节奏），非自然季节性",
    "lunar_holiday_check": {
        "spring_festival_offset_days": [
            {"year": 2020, "anchor": "06-01", "days_after_spring_festival": 127},
            {"year": 2021, "anchor": "06-01", "days_after_spring_festival": 109},
        ],
        "finding": "2020 与 2021 春节相差 18 天，但锚点同为 06-01 → 说明该锚点是**公历/公司数据驱动**，与春节无关。",
    },
    "data_quality": {"anchor_precision": "EXACT_DATE", "verification": "verification_method=unknown",
                     "research_status": "PROVISIONAL", "grade": "MEDIUM"},
    "research_strength": {"grade": "C",
                          "rationale": "N=2；两点完全重合但不足以构成稳定规律；且 2020/2021 的锚点日期均为研究候选日期（未人工核验）"},
    "status": "EXPLORATORY",
    "timeline_eligible": False,
    "timeline_ineligible_reason": "N=2 < 最低纳入标准；触发「样本量幻觉」拒绝规则情况 1。",
    "provenance": {"source": "ThreeC 2018–2025 历史研究数据", "generated_by": "offline research script",
                   "snapshot_date": "2026-09-16", "research_round": "seasonal-observation-pattern-v0.1"},
})

# ---------------------------------------------------------------- SOP-03
p3 = PV["SOP-03"]
w3 = p3["windows"]["B_mad_k1.0"]
w315 = p3["windows"]["B_mad_k1.5"]
w32 = p3["windows"]["B_mad_k2.0"]
r3 = p3["historical_recurrence"]["B_mad_k1.0"]
r3q = p3["historical_recurrence"]["A_quantile_P25_P75"]
g3, why3 = grade(p3["n_years"], p3["spread_ratio_vs_uniform"], p3["empirical_span_p_one_sided"],
                 r3["ratio"], p3["stability"].get("drift_flag", "INSUFFICIENT_N"),
                 p3["leave_one_out"].get("single_year_dominated", False), 1)
PATTERNS.append({
    "pattern_id": "SOP-03",
    "pattern_type": "MIXED",
    "theme_key": "汽车（Macro Theme 全主题）",
    "title": "汽车主题夏季 / 上半年末启动观察窗口",
    "anchor_type": "EARLY_SIGNAL",
    "anchor_definition": "Anchor A（7 年全部可用 EARLY_SIGNAL）",
    "level": "LEVEL_3 Macro Theme 级（合并多条不同机制的 Theme Cycle）",
    "eligible_years": p3["years"],
    "observed_years": p3["years"],
    "observations": [{"year": y, "campaign": c, "anchor_date": d}
                     for y, c, d in zip(p3["years"], p3["campaigns"], p3["anchor_dates"])],
    "typical_window": {
        "start": w3["start_md"], "end": w3["end_md"], "method": "Median ± 1×MAD",
        "alternative_quantile_window": {"start": p3["windows"]["A_quantile_P25_P75"]["start_md"],
                                        "end": p3["windows"]["A_quantile_P25_P75"]["end_md"]},
        "alternative_wider_window": {"start": w315["start_md"], "end": w315["end_md"],
                                     "method": "Median ± 1.5×MAD"},
        "widest_window": {"start": w32["start_md"], "end": w32["end_md"], "method": "Median ± 2×MAD"},
        "degraded_month_window": "5 月下旬 ~ 7 月上旬（含 4 月末离群年则为 4 月下旬 ~ 8 月中旬）",
    },
    "center_date": p3["median_md"],
    "dispersion": {"iqr_days": p3["iqr_days"], "mad_days": p3["mad_days"],
                   "span_days": p3["span_days"], "earliest": p3["earliest_md"], "latest": p3["latest_md"]},
    "time_concentration": {
        "spread_ratio_vs_uniform": p3["spread_ratio_vs_uniform"],
        "empirical_span_p_one_sided": p3["empirical_span_p_one_sided"],
        "month_distribution": p3["month_distribution"],
        "uniform_expected_span_days": 365 * (p3["n_years"] - 1) / (p3["n_years"] + 1),
        "note": "N=7 是本轮唯一达到「可做探索性统计」规模的族；仍为描述统计。",
    },
    "historical_recurrence": {
        "hits": r3["hits"], "n_years": r3["n_years"], "ratio": r3["ratio"],
        "hits_years": r3["hits_years"], "miss_years": r3["miss_years"],
        "quantile_window_variant": {"hits": r3q["hits"], "ratio": r3q["ratio"],
                                    "hits_years": r3q["hits_years"], "miss_years": r3q["miss_years"]},
        "label": "历史样本中的窗口复现情况（不是未来概率）",
    },
    "outside_window_contrast": {
        "window_width_days": 31, "window_share_of_year": 31 / 365,
        "hit_share": r3["ratio"], "density_ratio": r3["ratio"] / (31 / 365),
        "june_share": p3["month_distribution"].get("06", 0) / p3["n_years"],
        "baseline_june_share_event_calendar": BASE_EVENT_JUNE,
        "baseline_june_share_index_best30d": BASE_INDEX_JUNE,
        "lift_vs_event_baseline": (p3["month_distribution"].get("06", 0) / p3["n_years"]) / BASE_EVENT_JUNE,
        "lift_vs_index_baseline": (p3["month_distribution"].get("06", 0) / p3["n_years"]) / BASE_INDEX_JUNE,
        "warning": "ThreeC 事件台账本身 6 月占比 33%（10/30），远高于均匀 8.3% → 存在**研究事件选择偏差**，lift 值不可解读为主题独有季节性。",
    },
    "stability": p3["stability"],
    "drift": p3["stability"].get("drift_flag", "UNKNOWN"),
    "leave_one_out": {k: v for k, v in p3["leave_one_out"].items() if k != "per_removal"},
    "sample_size_sensitivity": {
        "N2": "不足（单机制族多为 N=1–2）",
        "N3": "2019/2023/2024 智能化子族 → 跨度 21 天、ratio 0.115",
        "N4": "智能化子族 N=4 → 跨度 65 天、ratio 0.297、p≈0.024",
        "N5plus": "汽车全主题 N=7 → 跨度 110 天、ratio 0.402、p≈0.005（但被 2019-08-15 与 2022-04-27 两个离群年拉宽）",
        "note": "样本量从 3→7 时「集中度」指标先急剧下降再因离群年抬升；说明该指标对单点极敏感。",
    },
    "evidence_basis": ["exports/timeline_export_v1.json campaigns[]（9 个正式 Campaign 中 8 个属汽车）",
                       "research/database/cycle_research.db campaigns / campaign_phases",
                       "research/research/summary/auto_2018_2025_final_review.md",
                       "research/research/batch/auto_2018_2025_batch_manifest.json"],
    "mechanism_hypotheses": [
        {"hypothesis": "政策/制度日历：年中稳增长政策窗口（国常会 5–6 月部署汽车消费）",
         "evidence_strength": "SUPPORTED_BY_PUBLIC_RECORD",
         "detail": "2022-05-23 国常会阶段性减征乘用车购置税 600 亿；2022-05-31 财政部细则 — 属年中稳增长节奏。"},
        {"hypothesis": "国际产业事件与行业展会/发布会节奏偏北半球夏季",
         "evidence_strength": "MULTI_YEAR_OBSERVATION"},
        {"hypothesis": "A 股中报预告窗口（6 月中下旬密集）与汽车产业链景气验证叠加",
         "evidence_strength": "PUBLIC_SCHEDULE_FACT"},
        {"hypothesis": "新能源车月度产销与渗透率数据发布节奏（月度数据在次月中旬公布）",
         "evidence_strength": "PUBLIC_SCHEDULE_FACT"},
    ],
    "mechanism_class": "MIXED（CALENDAR_DRIVEN 政策日历 + INDUSTRY_CYCLE 产销节奏 + 事件驱动）",
    "calendar_vs_seasonal": "以 CALENDAR_DRIVEN / INDUSTRY_CYCLE 为主；**不**支持 SEASONAL_DEMAND（无证据表明汽车终端需求在 6 月出现季节性峰值）",
    "lunar_holiday_check": {
        "spring_festival_offset_days": [
            {"year": 2019, "anchor": "08-15", "days_after_spring_festival": 191},
            {"year": 2020, "anchor": "06-01", "days_after_spring_festival": 127},
            {"year": 2021, "anchor": "06-01", "days_after_spring_festival": 109},
            {"year": 2022, "anchor": "04-27", "days_after_spring_festival": 85},
            {"year": 2023, "anchor": "06-12", "days_after_spring_festival": 141},
            {"year": 2024, "anchor": "06-11", "days_after_spring_festival": 121},
            {"year": 2025, "anchor": "06-22", "days_after_spring_festival": 144},
        ],
        "finding": "春节相对位置跨度 85–191 天（106 天跨度）→ **不是农历型规律**。公历 6 月的集中度显著高于春节相对位置的集中度。",
        "nearest_fixed_anchors": ["618（约 4–17 天）", "五一（2022 年 4 天）", "中报预告窗口"],
    },
    "data_quality": {
        "anchor_precision": "EXACT_DATE", "verification": "verbatim: 2019/2020/2021/2023/2024/2025 verification_method=unknown；2022/2024-ROBOTAXI=market_data",
        "research_status": "全部 PROVISIONAL（C-2024-ROBOTAXI 为 CONFLICT）",
        "provisional_ratio": 1.0, "grade": "MEDIUM",
        "inconsistency": "2019 锚点为 event_driven/weak，与其他年份的 theme_campaign 不同强度；2018 为 no_clear_campaign 反例年",
    },
    "research_strength": {"grade": g3, "rationale": why3},
    "status": "MODERATE_CANDIDATE",
    "timeline_eligible": True,
    "timeline_eligible_notes": "满足 Timeline 最低门槛（N=7、集中度比率 0.40、p≈0.005、无单年主导、有无漂移的前后半段）；但必须以「宽窗口 + 明确机制类别 + 非预测文案」方式呈现，且需先完成日期人工核验。",
    "provenance": {"source": "ThreeC 2018–2025 历史研究数据", "generated_by": "offline research script",
                   "snapshot_date": "2026-09-16", "research_round": "seasonal-observation-pattern-v0.1"},
})

# ---------------------------------------------------------------- SOP-04
p4 = PV["SOP-04"]
PATTERNS.append({
    "pattern_id": "SOP-04",
    "pattern_type": "CALENDAR_DRIVEN",
    "theme_key": "医药健康（创新药 · 疫情医疗 · 中医药）",
    "title": "医药健康结构性升级启动窗口",
    "anchor_type": "EARLY_SIGNAL",
    "anchor_definition": "Anchor A（其中 RC-2020-PANDEMIC / RC-2021-TCM 来自 export.early_signal 字符串字段）",
    "level": "LEVEL_2 同一 Theme Cycle（medical_structural_upgrade_2019_2022）内多叙事并行",
    "eligible_years": [2019, 2020, 2021],
    "observed_years": [2019, 2020, 2021],
    "observations": [{"year": 2019, "campaign": "C-2019-PHARMA-INNOV", "anchor_date": "2019-01-02"},
                     {"year": 2020, "campaign": "RC-2020-PANDEMIC", "anchor_date": "2020-01-23"},
                     {"year": 2021, "campaign": "RC-2021-TCM", "anchor_date": "2021-11-01"}],
    "typical_window": {
        "start": None, "end": None,
        "method": "**不生成窗口** —— 跨度 83 天（11-01 ~ 01-23），IQR 151.5 天，三个锚点分属 3 个不同月份",
        "minimal_statement": "仅能说「分布在年末—年初区段」，且其中 2 个观测为 1 月、1 个为 11 月，**不足以形成任何日级或月级窗口**",
    },
    "center_date": p4["median_md"],
    "dispersion": {"iqr_days": p4["iqr_days"], "mad_days": p4["mad_days"],
                   "span_days": p4["span_days"], "earliest": p4["earliest_md"], "latest": p4["latest_md"]},
    "time_concentration": {
        "spread_ratio_vs_uniform": p4["spread_ratio_vs_uniform"],
        "empirical_span_p_one_sided": p4["empirical_span_p_one_sided"],
        "month_distribution": p4["month_distribution"],
        "note": "ratio 0.455、p≈0.156 → 与全年均匀分布**无显著差异**。",
    },
    "historical_recurrence": {"note": "窗口无法构建 → 不计算复现率（避免人为造一个窗口再去数命中）"},
    "outside_window_contrast": {
        "note": "无窗口可对照。三个锚点分散在 3 个月 → 分类为「年内分散」，不构成时间聚集。",
    },
    "stability": {"status": "INSUFFICIENT_N", "note": "N=3<4；且留一法显示 max median shift 141 天 → 完全由单点决定"},
    "drift": "UNDEFINED",
    "leave_one_out": {k: v for k, v in p4["leave_one_out"].items() if k != "per_removal"},
    "sample_size_sensitivity": {"note": "N=3；三点的中位数在剔除任一点后位移最大 141 天 → 统计量无意义"},
    "evidence_basis": ["exports/timeline_export_v1.json campaigns[]: C-2019-PHARMA-INNOV / research_candidates[]: RC-2020-PANDEMIC, RC-2021-TCM",
                       "research/research/reportts/Medical_Health_*", "research/research/annual/2019.md, 2020.md, 2021.md"],
    "mechanism_hypotheses": [
        {"hypothesis": "政策/制度日历驱动（集采 4+7 结果 2018-12-17、科创板 2019-07-22、医保谈判 2019-11-28）",
         "evidence_strength": "SUPPORTED_BY_PUBLIC_RECORD",
         "detail": "但政策日期本身分散在 12 月 / 7 月 / 11 月，**并不支持「1 月集中」**。"},
        {"hypothesis": "疫情为外生冲击，不可重复（2020-01-23 武汉封城）",
         "evidence_strength": "SINGLE_EVENT"},
        {"hypothesis": "中医药政策在年末发布（2021-12-31 医保局/中医药局指导意见）→ 板块 11 月提前反应",
         "evidence_strength": "SINGLE_YEAR"},
    ],
    "mechanism_class": "CALENDAR_DRIVEN（政策/制度日历）为主，含 1 个外生冲击（疫情）",
    "calendar_vs_seasonal": "CALENDAR_DRIVEN；**无 SEASONAL_DEMAND 证据**",
    "lunar_holiday_check": {
        "spring_festival_offset_days": [
            {"year": 2019, "anchor": "01-02", "days_after_spring_festival": -34},
            {"year": 2020, "anchor": "01-23", "days_after_spring_festival": -2},
            {"year": 2021, "anchor": "11-01", "days_after_spring_festival": 262},
        ],
        "finding": "偏离春节 -34 / -2 / +262 天 → 同样不集中。与公历亦不集中（分散 3 个月）。",
    },
    "data_quality": {"anchor_precision": "EXACT_DATE；2019 锚点为本地数据窗口起点（2019-01-02）而非真实主题起点",
                     "verification": "verification_method=unknown", "research_status": "PROVISIONAL", "grade": "LOW-MEDIUM"},
    "research_strength": {"grade": "D", "rationale": "N=3、跨度 83 天、与均匀分布无差异、留一法显示完全由单点决定 → 未发现时间聚集证据"},
    "status": "REJECTED",
    "reject_reason": "拒绝规则情况 2（窗口内外差异极小 / 无集中）+ 情况 4（实际含单一致命外生事件：2020 疫情）+ 情况 6（规律由单一年份主导，LOO 位移 141 天）",
    "timeline_eligible": False,
    "provenance": {"source": "ThreeC 2018–2025 历史研究数据", "generated_by": "offline research script",
                   "snapshot_date": "2026-09-16", "research_round": "seasonal-observation-pattern-v0.1"},
})

DOC = {
    "artifact": "seasonal_observation_patterns",
    "artifact_version": "0.1",
    "status": "RESEARCH_ARTIFACT — 不是产品 schema，不进入 DB / export / contracts",
    "generated_at": "2026-09-16",
    "generated_by": "offline research script（临时脚本；非产品代码）",
    "research_round": "seasonal-observation-pattern-v0.1",
    "snapshot_date": "2026-09-16",
    "data_source": {
        "canonical_export": "exports/timeline_export_v1.json",
        "research_db": "research/database/cycle_research.db",
        "export_version": "1.0",
        "coverage_years": "2018–2025（研究覆盖至 2025-08）",
    },
    "anchor_priority_used": ["ANCHOR_A_EARLY_SIGNAL", "ANCHOR_B_FORMATION（THEME_FORMING → BROAD_CONFIRMATION）", "ANCHOR_C_CAMPAIGN_START"],
    "forbidden_fields_policy": [
        "future_probability", "confidence_percent", "expected_return", "win_rate",
        "buy_signal", "target_price", "seasonality_score", "评级：买入/卖出",
    ],
    "research_strength_grading": {
        "A": "数据支持较强的历史时间聚集现象",
        "B": "存在一定历史聚集，但样本 / 稳定性有限",
        "C": "探索性迹象，不能固化",
        "D": "没有发现足够证据",
    },
    "status_vocabulary": ["STRONG_CANDIDATE", "MODERATE_CANDIDATE", "EXPLORATORY", "REJECTED"],
    "baselines": {
        "event_calendar_june_share": BASE_EVENT_JUNE,
        "index_best_30d_window_june_share": BASE_INDEX_JUNE,
        "uniform_june_share": 1 / 12,
        "note": "两个基准均显示 6 月占比高于均匀 → 「6 月集中」存在研究样本选择偏差成分，不可直接归因于主题季节性",
    },
    "patterns": PATTERNS,
    "dataset_level_findings": {
        "total_objects": FIT["n_total_export_objects"],
        "total_campaigns": FIT["n_campaigns_export"],
        "total_research_candidates": FIT["n_research_candidates_export"],
        "level2_cross_year_repeat_themes": 1,
        "level2_detail": "仅 medical_structural_upgrade_2019_2022 一个 Theme Cycle 跨年重复；其余 8 个 Cycle 均为单年",
        "level3_explored_families": list(FA["families"].keys()),
        "final_answer": "B/ C —— 存在迹象但样本不足，仅 1 个 Pattern 达到 Timeline 最低门槛且需先补数据",
    },
    "known_limitations": [
        "2018–2025 仅 8 个年度观测，且 2018 为反例年（no_clear_campaign）→ 有效年度 7 个。",
        "所有锚点日期均为研究候选日期，verification_method 多为 unknown（未经行情人工核验）。",
        "ThreeC 只记录「形成 Campaign 的主题」→ 存在 survivorship bias；无法观测「当年同样在 6 月启动但未成势」的主题。",
        "研究规则在 2019–2022 与 2023–2024 之间存在口径差异（见方法学一致性审计）。",
        "农历换算为近似（基于春节日期表），非精确农历算法。",
        "permutation 经验 p 仅作探索性描述，N<5 时不作为显著性断言。",
    ],
}

out_json = os.path.join(REPORT_DIR, "seasonal_observation_patterns_v0_1.json")
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(DOC, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------- CSV
csv_rows = []
raw_map = {
    "SOP-01": (2019, "C-2019-AD"), "SOP-02": (2020, "C-2020-NEV"),
}
for pid, p in PV.items():
    for y, c, d, m in zip(p["years"], p["campaigns"], p["anchor_dates"], p["anchor_md"]):
        # phase at anchor
        phase = "EARLY_SIGNAL"
        status = {"SOP-01": "MODERATE_CANDIDATE", "SOP-02": "EXPLORATORY",
                  "SOP-03": "MODERATE_CANDIDATE", "SOP-04": "REJECTED"}[pid]
        csv_rows.append({
            "theme": p["name"],
            "pattern_id": pid,
            "year": y,
            "campaign_id": c,
            "anchor_type": "EARLY_SIGNAL",
            "anchor_date": d,
            "day_of_year": p["anchor_doy_norm"][p["years"].index(y)],
            "phase": phase,
            "status": status,
        })

out_csv = os.path.join(HERE, "seasonal_observation_candidates_v0_1.csv")
with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["theme", "pattern_id", "year", "campaign_id",
                                      "anchor_type", "anchor_date", "day_of_year", "phase", "status"])
    w.writeheader()
    for r in sorted(csv_rows, key=lambda x: (x["pattern_id"], x["year"])):
        w.writerow(r)

print("WROTE:", out_json)
print("WROTE:", out_csv)
print()
print("=== 分级汇总 ===")
for p in PATTERNS:
    print(f"  {p['pattern_id']}  {p['title'][:30]:32s} N={len(p['observed_years'])}  "
          f"grade={p['research_strength']['grade']}  status={p['status']}  timeline={p['timeline_eligible']}")
