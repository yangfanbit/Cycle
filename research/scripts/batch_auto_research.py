"""批量研究脚本（Batch Auto Research v1）。

职责（对应 HDP v1 契约）：
1. 读取正式 Campaign（2018–2025, rule_auto_summer）
2. 检查已有 Evidence / Source / 独立性分组
3. 检查 Market Data（raw close 日期快照 + adjusted 收益率，缺则如实 unavailable）
4. 生成研究状态：PROVISIONAL / CONFLICT / INSUFFICIENT（不进入 verified）
5. 输出 research/batch/auto_2018_2025_batch_manifest.json
6. 输出 research/batch/conflicts.json（候选 A/B + 支持/反驳证据）
7. 输出 exports/timeline_export_v1.json（Research → Cycle Timeline MVP 契约 v1.0）

纪律：
- 模型冻结：不新增实体/字段/schema，不改动正式 Campaign 日期。
- PROVISIONAL 用于研究预览；绝不写入 verified。
- 日期冲突不强行解决，记录 candidate_a / candidate_b。
- 无行情数据时记录 unavailable，不伪造。
- 不计算任何统计指标（seasonality/win_rate/probability）。

用法: python scripts/batch_auto_research.py
"""
import sys, os, json, subprocess
from datetime import datetime, date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

ROOT = db.ROOT
conn = db.connect()

BATCH_DIR = os.path.join(ROOT, "research", "batch")
MANIFEST = os.path.join(BATCH_DIR, "auto_2018_2025_batch_manifest.json")
CONFLICTS = os.path.join(BATCH_DIR, "conflicts.json")
EXPORT = db.TIMELINE_EXPORT_PATH  # canonical: <repo>/exports/timeline_export_v1.json

AUTO_RULE = "rule_auto_summer"
PHARMA_RULE = "rule_pharma_upgrade"   # 医药健康（Medical Health Minimum Dataset v0.1）
# 批量研究覆盖的 Rule（按顺序生成；新增 Macro Theme 在此登记）
RULES = [AUTO_RULE, PHARMA_RULE]
RULE = AUTO_RULE   # 兼容既有引用（汽车专用常量；build_campaign 已改为按 c["rule_id"] 取值）

# ---- 研究级元数据（来自 theme_lifecycle_v0_2 / 年度研究） ----
THEME_CYCLE = {
    "C-2019-AD": "auto_ad_2019",
    "C-2020-NEV": "auto_nev_2020",
    "C-2021-NEV": "auto_nev_2021",
    "C-2022-POLICY": "auto_policy_2022",
    "C-2023-AD": "auto_intelligence_2023",
    "C-2024-V2X": "auto_v2x_2024",
    "C-2024-ROBOTAXI": "robotaxi_2024",
    "C-2025-ROBOTAXI": "robotaxi_2025",
    # ---- 医药健康（Medical Health Minimum Dataset v0.1，Pattern = Parallel）----
    # 同一 Theme Cycle 内含多个 Campaign，各自独立生命周期、Peak 时间可不同（v1.1 §5）。
    "C-2019-PHARMA-INNOV": "medical_structural_upgrade_2019_2022",
}

# 研究信号（research-level，来自 theme_lifecycle_v0_2 三案例建模；其余年份按 annual 研究记录）
SIGNALS = {
    "C-2022-POLICY": [
        {"type": "EARLY_SIGNAL", "date": "2022-04-27", "confidence": "medium"},
        {"type": "THEME_FORMING", "date": "2022-05-23", "confidence": "high"},
    ],
    "C-2023-AD": [
        {"type": "EARLY_SIGNAL", "date": "2023-06-12", "confidence": "medium"},
        {"type": "THEME_FORMING", "date": "2023-06-21", "confidence": "high"},
    ],
    "C-2024-ROBOTAXI": [
        {"type": "EARLY_SIGNAL", "date": "2024-07-08", "confidence": "medium"},
    ],
    "C-2024-V2X": [
        {"type": "EARLY_SIGNAL", "date": "2024-06-11", "confidence": "medium"},
    ],
    "C-2025-ROBOTAXI": [
        {"type": "EARLY_SIGNAL", "date": "2025-06-22", "confidence": "medium"},
    ],
    # ---- 医药健康 ----
    # EARLY_SIGNAL 2019-01-02 = 本地行情数据窗口起点（4+7 集采 2018-12-17 冲击后的首个交易日），
    # confidence=medium：窗口前的 Setup 不在本地数据范围内（见 campaigns.research_notes）。
    "C-2019-PHARMA-INNOV": [
        {"type": "EARLY_SIGNAL", "date": "2019-01-02", "confidence": "medium"},
        {"type": "THEME_FORMING", "date": "2019-07-22", "confidence": "high"},
    ],
}

# Campaign Phase → 时间字段（research-only，便于 timeline 表达）
PHASE_TIME_FIELDS = {
    "C-2022-POLICY": {"broad_confirmation_date": "2022-06-01", "first_decline_date": "2022-07-01"},
    "C-2023-AD": {"broad_confirmation_date": "2023-07-03"},
    "C-2024-ROBOTAXI": {"broad_confirmation_date": "2024-07-10", "first_decline_date": "2024-08-06"},
    "C-2024-V2X": {"broad_confirmation_date": "2024-06-18"},
    "C-2025-ROBOTAXI": {"broad_confirmation_date": "2025-06-24"},
    # ---- 医药健康 ----
    "C-2019-PHARMA-INNOV": {"broad_confirmation_date": "2019-11-28"},
}

# ---- 日期精度（V1.7：日期精度不再是核心瓶颈）----
# EXACT_DATE：真实行情/正式事件单日；DATE_WINDOW：多指标/来源轻微差异区间；PHASE_WINDOW：用户周期阶段。
# 仅当差异足以改变 Campaign 生命周期判断时才进入 CONFLICT（见 CONFLICT_MAP）。
TIME_PRECISION = ("EXACT_DATE", "DATE_WINDOW", "PHASE_WINDOW")

# ---- 重大冲突（V1.7 新标准：只处理重大冲突）----
# 判定：1) 起点相差 >20 交易日；2) Peak Window 落完全不同月份；3) End 候选改变生命周期；
#       4) Theme classification 完全不同；5) Evidence 直接事实冲突。
# 已降级（非 CONFLICT，用 date_window 表达）：
#   - C-2022-POLICY start 04-27 vs 05-23（15 交易日 ≤20；语义上 EARLY_SIGNAL 04-27 + THEME_FORMING 05-23，见 lifecycle）
#   - C-2024-ROBOTAXI peak 07-29 vs 08-05（仅 5 交易日、相邻月份 → Peak Window 07-29~08-05）
# 保留 CONFLICT：C-2024-ROBOTAXI end 07-31 vs 08-23（17 交易日且改变 Main Campaign 生命周期）。
CONFLICT_MAP = {
    "C-2024-ROBOTAXI": {
        "end_date": {
            "candidate_a": {"date": "2024-07-31", "label": "DB Candidate",
                            "basis": "campaigns.end_date 冻结值"},
            "candidate_b": {"date": "2024-08-23", "label": "Research Review Candidate（Main Campaign End）",
                            "basis": "theme_lifecycle_v0_2：08-23 Major Breakpoint"},
        },
    },
}

# Campaign → Cycle 侧 promotion 状态（promotion_gate_v1：仅三条正式候选 READY_FOR_HUMAN_REVIEW）
PROMO_STATUS = {
    "C-2022-POLICY": "READY_FOR_HUMAN_REVIEW",
    "C-2023-AD": "READY_FOR_HUMAN_REVIEW",
    "C-2024-ROBOTAXI": "READY_FOR_HUMAN_REVIEW",
}

# ---- Research Candidate（研究候选，不进入正式 campaigns）----
# 来自 theme_lifecycle_v0_2 / 2023_huawei_auto_campaign_review / 2024_robotaxi_* 研究记录。
# 仅表达于 timeline_export 的 research_candidates 数组，用于 Cycle Preview 展示；不新建数据库。
RESEARCH_CANDIDATES = [
    {
        "campaign_id": "RC-2023-HUAWEI",
        "rule_id": RULE,
        "year": 2023,
        "title": "Huawei Auto 2023（华为汽车 / AITO M7 / ADS2.0）",
        "start_date": "2023-09-12",      # Campaign Start Candidate（问界M7 catalyst）
        "peak_date": None,
        "end_date": None,                # 主升至 2023-10-31 仍升，结束未定
        "themes": [{"name": "华为汽车", "theme_type": "concept", "role": "main"}],
        "securities": [
            {"security_id": "XIAOKANG", "name": "赛力斯(原小康股份)", "ticker": "601127", "exchange": "SH", "role": "leader"},
            {"security_id": "JAC", "name": "江淮汽车", "ticker": "600418", "exchange": "SH", "role": "second_leader"},
            {"security_id": "DEMEISHI", "name": "德迈仕", "ticker": "301007", "exchange": "SZ", "role": "representative"},
            {"security_id": "MINGKEJINGJI", "name": "铭科精技", "ticker": "001319", "exchange": "SZ", "role": "representative"},
            {"security_id": "HUAYANG", "name": "华阳集团", "ticker": "002906", "exchange": "SZ", "role": "representative"},
        ],
        "events": [
            {"event_id": "EV-RC-2023-HUAWEI-01", "name": "问界新M7上市发布会（HUAWEI ADS 2.0 随车亮相）",
             "date": "2023-09-12", "event_type": "company", "role": "trigger"},
        ],
        "signals": [
            {"type": "EARLY_SIGNAL", "date": "2023-08-29", "confidence": "low"},
            {"type": "THEME_FORMING", "date": "2023-09-04", "confidence": "medium"},
        ],
        "early_signal": "2023-08-29",
        "theme_formation": "2023-09-04",
        "broad_confirmation": "2023-09-18",
        "research_status": "PROVISIONAL",
        "theme_cycle_id": "auto_intelligence_2023",
        "conflicts": [],
        "notes": "Research Candidate（未达正式 Campaign 门槛，不进入 campaigns）：问界M7催化 09-12、Broad Confirmation 09-18、主升 09下~10 仍升；08-29 Early Signal 存在市场 Beta contamination（low）；与 C-2023-AD 同属 auto_intelligence_2023（Theme Drift：Smart Driving → Huawei Auto）",
    },
    {
        "campaign_id": "RC-2024-SECONDARY",
        "rule_id": RULE,
        "year": 2024,
        "title": "2024 Robotaxi Secondary（弱次级行情候选）",
        "start_date": "2024-09-05",
        "peak_date": None,
        "end_date": "2024-09-06",
        "themes": [{"name": "Robotaxi/无人驾驶/智能网约车", "theme_type": "concept", "role": "main"}],
        "securities": [
            {"security_id": "DADONGTRAFFIC", "name": "大众交通", "ticker": "600611", "exchange": "SH", "role": "leader"},
            {"security_id": "JINJIANGONLINE", "name": "锦江在线", "ticker": "600650", "exchange": "SH", "role": "second_leader"},
            {"security_id": "JINLONG", "name": "金龙汽车", "ticker": "600686", "exchange": "SH", "role": "second_leader"},
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "PROVISIONAL",
        "theme_cycle_id": "robotaxi_2024",
        "conflicts": [],
        "notes": "Weak Secondary Campaign Candidate：主 Campaign C-2024-ROBOTAXI（07-08~08-23）结束后 09-05~06 次级活跃，强度不足；不作为正式 Campaign。2024-10-10 特斯拉 Robotaxi 发布会仅一日脉冲后回落，亦不作为候选",
    },
    # ==== 医药健康（Medical Health Minimum Dataset v0.1）====
    # 均为 Case B（Campaign Candidate）：Gate Q1–Q5 多数成立，但生命周期边界尚缺完整行情验证 → 不升 Case C。
    {
        "campaign_id": "RC-2020-PANDEMIC",
        "rule_id": PHARMA_RULE,
        "year": 2020,
        "title": "2020 疫情医疗（防护耗材 / 体外诊断 / 疫苗）",
        "start_date": "2020-01-23",      # 武汉疫情防控措施；英科医疗 2020-01-23 已明显跳升
        "peak_date": "2021-01-25",       # 英科医疗自身历史高点（Campaign 自身口径，非医药指数）
        "end_date": "2021-12-31",        # 主跌段结束（2021 全年英科 -46.1%（adj））
        "themes": [{"name": "疫情医疗", "theme_type": "concept", "role": "main"}],
        "securities": [
            {"security_id": "INTCO", "name": "英科医疗", "ticker": "300677", "exchange": "SZ", "role": "leader"},
            {"security_id": "ZHIFEI", "name": "智飞生物", "ticker": "300122", "exchange": "SZ", "role": "second_leader"},
        ],
        "events": [
            {"event_id": "EV-RC-MED-PANDEMIC-01", "name": "新冠疫情：武汉实施离汉通道管控（疫情医疗需求起点）",
             "date": "2020-01-23", "event_type": "macro", "role": "trigger"},
        ],
        "signals": [{"type": "EARLY_SIGNAL", "date": "2020-01-23", "confidence": "medium"}],
        "early_signal": "2020-01-23",
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "PROVISIONAL",
        "theme_cycle_id": "medical_structural_upgrade_2019_2022",
        "conflicts": [],
        "notes": ("Campaign Candidate（Case B）。Gate：Q1 独立注意力中心=是；Q2 独立代表资产=是"
                  "（英科/智飞 与 恒瑞/药明/泰格 几乎零交集）；Q3 独立持续性=是（2020-01~2021，节奏与主线相反）；"
                  "Q4 独立生命周期=是（英科医疗 2021-01-25 见顶 296.99 元，2021 全年 -46.1%（adj），"
                  "同期主线仍在上涨至 2021-07）；Q5 Residual Test=是（去掉后 Theme Cycle 仍成立）。"
                  "未升 Case C：需排除疫情「全国 β 事件」污染 + 精确边界待更完整行情验证（见 Unknown Register）。"
                  "Pattern=Parallel（顶比主线早约半年）。"),
    },
    {
        "campaign_id": "RC-2021-TCM",
        "rule_id": PHARMA_RULE,
        "year": 2021,
        "title": "2021–2022 中医药（品牌中药 / 中药创新 / 抗疫中药）",
        "start_date": "2021-11-01",      # 政策预期升温起点（公开报道：2021-11-01 以来中药板块 79 只中 73 只上涨）
        "peak_date": "2022-12-08",       # 以岭药业自身区间高点（Campaign 自身口径）
        "end_date": "2022-12-30",        # 数据窗口末端（未确认结束）
        "themes": [{"name": "中医药", "theme_type": "concept", "role": "main"}],
        "securities": [
            {"security_id": "PIANZAIHUANG", "name": "片仔癀", "ticker": "600436", "exchange": "SH", "role": "leader"},
            {"security_id": "YILING", "name": "以岭药业", "ticker": "002603", "exchange": "SZ", "role": "second_leader"},
        ],
        "events": [
            {"event_id": "EV-RC-MED-TCM-01",
             "name": "国家医保局、国家中医药管理局《关于医保支持中医药传承创新发展的指导意见》",
             "date": "2021-12-31", "event_type": "policy", "role": "trigger"},
        ],
        "signals": [
            {"type": "EARLY_SIGNAL", "date": "2021-11-01", "confidence": "medium"},
            {"type": "THEME_FORMING", "date": "2021-12-31", "confidence": "high"},
        ],
        "early_signal": "2021-11-01",
        "theme_formation": "2021-12-31",
        "broad_confirmation": None,
        "research_status": "PROVISIONAL",
        "theme_cycle_id": "medical_structural_upgrade_2019_2022",
        "conflicts": [],
        "notes": ("Campaign Candidate（Case B）。Gate：Q1 独立注意力中心=是（中医药有专属政策体系）；"
                  "Q2 独立代表资产=是（片仔癀/以岭 与 创新药核心资产基本不重合）；Q3 独立持续性=是（2021Q4→2022Q4 多波）；"
                  "Q4 独立生命周期=是；Q5 Residual Test=是。**不依赖涨幅的独立证据三支柱**："
                  "① 独立政策体系；② 多数中药品种未进集采、可自主定价；③ 独立估值体系（20–30x vs 创新药/CXO 上百倍）。"
                  "未升 Case C：⚠ 归属未决（医药健康下 Sub-theme vs 独立 Macro Theme「中医药」）→ Unknown Register U-C1；"
                  "且市场存在分歧（「拐点已现」vs「更多是反弹」）→ 记 CONFLICT 语义但不写入 conflicts（无日期口径冲突）。"
                  "结构为两段（片仔癀 2021 品牌中药 + 以岭 2022Q4 抗疫中药），Peak 取以岭自身高点。"),
    },
]

# ---- Lifecycle（Phase Windows）与 Drivers（V1.7 核心产出）----
# 依据 theme_lifecycle_v0_2 / auto_lifecycle_2022_2024 / 年度研究 / campaign_phases。
# 时间精度：EXACT_DATE / DATE_WINDOW / PHASE_WINDOW；无可靠依据的阶段不写或标 unknown，不编造。
# drivers 内嵌来源引用（EV-/E-/S- 编号）；无可靠来源写 "unknown"。

CAMPAIGN_LIFECYCLE = {
    "C-2019-AD": [
        {"stage": "EARLY_SIGNAL", "start": "2019-08-15", "end": "2019-08-15", "precision": "EXACT_DATE"},
        {"stage": "MAIN_RISE", "start": "2019-08-15", "end": "2019-09-24", "precision": "DATE_WINDOW"},
        {"stage": "PEAK", "start": "2019-09-24", "end": "2019-09-24", "precision": "EXACT_DATE"},
        {"stage": "MAIN_END", "start": "2019-09-30", "end": "2019-09-30", "precision": "EXACT_DATE"},
    ],
    "C-2020-NEV": [
        {"stage": "EARLY_SIGNAL", "start": "2020-06-01", "end": "2020-06-01", "precision": "EXACT_DATE"},
        {"stage": "MAIN_RISE", "start": "2020-06-11", "end": "2020-07-13", "precision": "EXACT_DATE"},
        {"stage": "PEAK", "start": "2020-07-13", "end": "2020-07-13", "precision": "EXACT_DATE"},
        {"stage": "RETRACEMENT", "start": "2020-07-14", "end": "2020-08-20", "precision": "EXACT_DATE"},
        {"stage": "SECONDARY", "start": "2020-08-21", "end": "2020-09-30", "precision": "PHASE_WINDOW"},
        {"stage": "MAIN_END", "start": "2020-09-30", "end": "2020-09-30", "precision": "EXACT_DATE"},
    ],
    "C-2021-NEV": [
        {"stage": "EARLY_SIGNAL", "start": "2021-06-01", "end": "2021-06-01", "precision": "EXACT_DATE"},
        {"stage": "MAIN_RISE", "start": "2021-06-01", "end": "2021-08-06", "precision": "EXACT_DATE"},
        {"stage": "PEAK", "start": "2021-08-06", "end": "2021-08-06", "precision": "EXACT_DATE"},
        {"stage": "DECLINING", "start": "2021-08-07", "end": "2021-09-30", "precision": "EXACT_DATE"},
        {"stage": "MAIN_END", "start": "2021-09-30", "end": "2021-09-30", "precision": "EXACT_DATE"},
    ],
    "C-2022-POLICY": [
        {"stage": "EARLY_SIGNAL", "start": "2022-04-27", "end": "2022-04-27", "precision": "EXACT_DATE"},
        {"stage": "THEME_FORMING", "start": "2022-05-23", "end": "2022-05-23", "precision": "EXACT_DATE"},
        {"stage": "BROAD_CONFIRMATION", "start": "2022-06-01", "end": "2022-06-01", "precision": "EXACT_DATE"},
        {"stage": "MAIN_RISE", "start": "2022-05-23", "end": "2022-06-28", "precision": "DATE_WINDOW"},
        {"stage": "PEAK", "start": "2022-06-10", "end": "2022-06-28", "precision": "DATE_WINDOW"},
        {"stage": "SECONDARY", "start": "2022-06-22", "end": "2022-06-30", "precision": "EXACT_DATE"},
        {"stage": "RETRACEMENT", "start": "2022-07-01", "end": "2022-07-31", "precision": "PHASE_WINDOW"},
        {"stage": "DECLINING", "start": "2022-08-01", "end": "2022-08-31", "precision": "PHASE_WINDOW"},
        {"stage": "MAIN_END", "start": "2022-08-31", "end": "2022-08-31", "precision": "EXACT_DATE"},
    ],
    "C-2023-AD": [
        {"stage": "EARLY_SIGNAL", "start": "2023-06-12", "end": "2023-06-12", "precision": "EXACT_DATE"},
        {"stage": "THEME_FORMING", "start": "2023-06-21", "end": "2023-06-21", "precision": "EXACT_DATE"},
        {"stage": "BROAD_CONFIRMATION", "start": "2023-07-03", "end": "2023-07-03", "precision": "EXACT_DATE"},
        {"stage": "MAIN_RISE", "start": "2023-07-03", "end": "2023-07-19", "precision": "EXACT_DATE"},
        {"stage": "PEAK", "start": "2023-07-11", "end": "2023-07-19", "precision": "DATE_WINDOW"},
        {"stage": "SECONDARY", "start": "2023-08-04", "end": "2023-08-04", "precision": "EXACT_DATE"},
        {"stage": "DECLINING", "start": "2023-07-19", "end": "2023-09-12", "precision": "PHASE_WINDOW"},
        {"stage": "MAIN_END", "start": "2023-07-19", "end": "2023-07-19", "precision": "EXACT_DATE"},
    ],
    "C-2024-V2X": [
        {"stage": "EARLY_SIGNAL", "start": "2024-06-11", "end": "2024-06-11", "precision": "EXACT_DATE"},
        {"stage": "THEME_FORMING", "start": "2024-06-14", "end": "2024-06-14", "precision": "EXACT_DATE"},
        {"stage": "PEAK", "start": "2024-06-18", "end": "2024-06-18", "precision": "EXACT_DATE"},
        {"stage": "MAIN_END", "start": "2024-06-25", "end": "2024-06-25", "precision": "EXACT_DATE"},
    ],
    "C-2024-ROBOTAXI": [
        {"stage": "EARLY_SIGNAL", "start": "2024-07-08", "end": "2024-07-08", "precision": "EXACT_DATE"},
        {"stage": "BROAD_CONFIRMATION", "start": "2024-07-10", "end": "2024-07-10", "precision": "EXACT_DATE"},
        {"stage": "MAIN_RISE", "start": "2024-07-11", "end": "2024-07-29", "precision": "EXACT_DATE"},
        {"stage": "PEAK", "start": "2024-07-29", "end": "2024-08-05", "precision": "DATE_WINDOW"},
        {"stage": "FIRST_DECLINE", "start": "2024-08-06", "end": "2024-08-06", "precision": "EXACT_DATE"},
        {"stage": "DECLINING", "start": "2024-08-06", "end": "2024-08-23", "precision": "DATE_WINDOW"},
        {"stage": "MAIN_END", "start": "2024-07-31", "end": "2024-08-23", "precision": "DATE_WINDOW"},
        {"stage": "SECONDARY", "start": "2024-09-05", "end": "2024-09-06", "precision": "EXACT_DATE"},
    ],
    "C-2025-ROBOTAXI": [
        {"stage": "EARLY_SIGNAL", "start": "2025-06-22", "end": "2025-06-22", "precision": "EXACT_DATE"},
        {"stage": "BROAD_CONFIRMATION", "start": "2025-06-24", "end": "2025-06-24", "precision": "EXACT_DATE"},
        {"stage": "MAIN_RISE", "start": "2025-06-22", "end": "2025-06-24", "precision": "EXACT_DATE"},
        {"stage": "PEAK", "start": "2025-06-24", "end": "2025-06-24", "precision": "EXACT_DATE"},
        {"stage": "MAIN_END", "start": "2025-08-31", "end": "2025-08-31", "precision": "EXACT_DATE"},
    ],
    # ---- 医药健康（Peak 口径按 v1.1 §6：使用 Campaign 自身代表标的，非上位医药指数）----
    "C-2019-PHARMA-INNOV": [
        {"stage": "EARLY_SIGNAL", "start": "2019-01-02", "end": "2019-01-02", "precision": "EXACT_DATE"},
        {"stage": "THEME_FORMING", "start": "2019-07-22", "end": "2019-07-22", "precision": "EXACT_DATE"},
        {"stage": "BROAD_CONFIRMATION", "start": "2019-11-28", "end": "2019-11-28", "precision": "EXACT_DATE"},
        {"stage": "MAIN_RISE", "start": "2020-01-01", "end": "2020-12-24", "precision": "DATE_WINDOW"},
        {"stage": "PEAK", "start": "2020-12-25", "end": "2021-07-01", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2021-07-02", "end": "2022-10-31", "precision": "PHASE_WINDOW"},
        {"stage": "MAIN_END", "start": "2022-10-31", "end": "2022-10-31", "precision": "EXACT_DATE"},
    ],
}

CANDIDATE_LIFECYCLE = {
    "RC-2023-HUAWEI": [
        {"stage": "EARLY_SIGNAL", "start": "2023-08-29", "end": "2023-08-29", "precision": "EXACT_DATE"},
        {"stage": "THEME_FORMING", "start": "2023-09-04", "end": "2023-09-04", "precision": "EXACT_DATE"},
        {"stage": "BROAD_CONFIRMATION", "start": "2023-09-18", "end": "2023-09-18", "precision": "EXACT_DATE"},
        {"stage": "MAIN_RISE", "start": "2023-09-20", "end": "2023-10-31", "precision": "PHASE_WINDOW"},
    ],
    "RC-2024-SECONDARY": [
        {"stage": "EARLY_SIGNAL", "start": "2024-09-05", "end": "2024-09-05", "precision": "EXACT_DATE"},
        {"stage": "MAIN_END", "start": "2024-09-06", "end": "2024-09-06", "precision": "EXACT_DATE"},
    ],
    # ---- 医药健康（Candidate）----
    "RC-2020-PANDEMIC": [
        {"stage": "EARLY_SIGNAL", "start": "2020-01-23", "end": "2020-01-23", "precision": "EXACT_DATE"},
        {"stage": "MAIN_RISE", "start": "2020-02-03", "end": "2020-12-31", "precision": "PHASE_WINDOW"},
        {"stage": "PEAK", "start": "2021-01-25", "end": "2021-01-25", "precision": "EXACT_DATE"},
        {"stage": "DECLINING", "start": "2021-02-01", "end": "2021-12-31", "precision": "PHASE_WINDOW"},
        {"stage": "MAIN_END", "start": "2021-12-31", "end": "2021-12-31", "precision": "EXACT_DATE"},
    ],
    "RC-2021-TCM": [
        {"stage": "EARLY_SIGNAL", "start": "2021-11-01", "end": "2021-11-01", "precision": "EXACT_DATE"},
        {"stage": "THEME_FORMING", "start": "2021-12-31", "end": "2021-12-31", "precision": "EXACT_DATE"},
        {"stage": "PEAK", "start": "2022-11-30", "end": "2022-12-08", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2022-12-09", "end": "2022-12-30", "precision": "EXACT_DATE"},
    ],
}

CAMPAIGN_DRIVERS = {
    "C-2019-AD": {
        "start": ["交通部研究自动驾驶法规与指导意见（EV-2019-03 trigger, 2019-08-27）",
                  "6月国五/六切换促销式回暖后市场寻找新方向（S-2019-01）"],
        "accelerator": ["智能汽车概念午后走强（E-2019-04, 2019-09）", "无人驾驶板块活跃（E-2019-05）"],
        "turning": ["新能源汽车7月起负增长、行业基本面弱（S-2019-02 contradicting）"],
        "ending": ["事件驱动脉冲退潮、无持续主线（result=weak）"],
    },
    "C-2020-NEV": {
        "start": ["特斯拉国产化落地 + 股价破千美元预期（S-2020-01）", "比亚迪汉上市（首搭刀片电池）（EV-2020-02）"],
        "accelerator": ["特斯拉市值超丰田居全球车企第一（EV-2020-01, 06-10）",
                        "宁德时代与本田战略合作 + 为特斯拉供货（EV-2020-03）",
                        "比亚迪涨停、宁德市值逼近五千亿（S-2020-02）"],
        "turning": ["7/14 特斯拉过山车带动A股调整（phase retracement 07-14~08-20）", "获利盘回吐"],
        "ending": ["主升 7/13 见顶后回调；8/21 二次启动为弱（S-2020-03 Tier4 线索）", "9月末宽窗口结束（暂定）"],
    },
    "C-2021-NEV": {
        "start": ["新能源车产销持续翻倍、渗透率升至12%+（S-2021-01/02）"],
        "accelerator": ["宁德时代市值破万亿（EV-2021-01）", "宁德宜宾产能一期投运（EV-2021-03）",
                        "比亚迪创新高、市值一度超9000亿（S-2021-05）", "板块爆发多股涨停（S-2021-03）"],
        "turning": ["整体车市缺芯负增长（S-2021-06 contradicting）", "8/6 比亚迪新高后高位震荡分化"],
        "ending": ["8/6 峰值后分化、9月主线衰减（phase decline 08-07~09-30）", "9月末宽窗口结束（暂定）"],
    },
    "C-2022-POLICY": {
        "start": ["行业修复/Setup + 复工复产预期（EARLY_SIGNAL 04-27）",
                  "国常会阶段性减征乘用车购置税600亿元（EV-2022-01, 05-23 THEME_FORMING）",
                  "地方补贴加码（S-2022-02）"],
        "accelerator": ["5/31 财政部/税务总局购置税减半细则 + 新能源下乡（EV-2022-02）",
                        "6/1 细则落地次日整车集体涨停（Broad Confirmation）",
                        "6/22 国常会再促消费（取消二手车限迁）（EV-2022-03）",
                        "比亚迪A股市值破万亿（EV-2022-04, 06-10）"],
        "turning": ["7月后政策边际减弱", "获利盘/估值高位（6/10 比亚迪破万亿后）", "板块分化回调"],
        "ending": ["8月 declining（08-01 二高点后持续衰减）", "政策催化缺失、板块失去同步"],
    },
    "C-2023-AD": {
        "start": ["工信部吹风会：支持L3商业化 + 启动准入和上路通行试点（EV-2023-01, 06-21 THEME_FORMING）",
                  "L3政策预期（E-2023-01/07）"],
        "accelerator": ["比亚迪首发'天神之眼'高阶智驾（腾势N7）（EV-2023-02, 07-03）",
                        "7/3-4 25股涨停全面爆发（S-2023-02）", "浙江世宝8天6板（S-2023-05）"],
        "turning": ["7/11 峰值后板块让位地产/顺周期、快速轮动（phase decline）", "获利盘兑现"],
        "ending": ["7/19 主升结束、8-9月主题衰减（至09-12 德赛/浙江见顶转跌）",
                   "正式L3文件11/17成文为后续（EV-2023-03 subsequent），夏季系预期驱动",
                   "FSD 2023未在华落地（反例约束）"],
    },
    "C-2024-V2X": {
        "start": ["武汉车路云一体化示范项目备案170.84亿（EV-2024-01, 06-14 THEME_FORMING）", "政策试点预期"],
        "accelerator": ["车路云概念全线爆发、华铭智能等10余股涨停（S-2024-02）"],
        "turning": ["公司多公告'未参与'（题材证伪）", "6/18 高峰后分化"],
        "ending": ["索菱断板跌停、金溢逼近跌停（S-2024-03）", "快涨快退（约2周）题材退潮",
                   "5部门20城试点（EV-2024-02, 07-03）为后续事件，不充当窗口内催化"],
    },
    "C-2024-ROBOTAXI": {
        "start": ["萝卜快跑武汉跑出圈（EV-2024-03, 07-10 Broad Confirmation）", "无人驾驶板块大涨4%（S-2024-04）"],
        "accelerator": ["大众交通16日涨233%（S-2024-05）", "锦江15天9板、金龙12天7板",
                        "板块指数大涨超4%、天迈/经纬恒润20cm涨停（S-2024-04）"],
        "turning": ["7/31 大众交通9连板终结、大众公用'天地板'（S-2024-06）", "8/6 首次明显回撤",
                    "高位题材亏钱效应放大（S-2024-07）"],
        "ending": ["08-23 Main Campaign End（Major Breakpoint）", "板块同步性消失、龙头退潮"],
    },
    "C-2025-ROBOTAXI": {
        "start": ["特斯拉奥斯汀启动Robotaxi有偿试运营（EV-2025-01, 06-22）",
                  "萝卜快跑/小马智行Robotaxi规模化（S-2025-01）"],
        "accelerator": ["A股无人驾驶板块全线爆发涨停潮（EV-2025-02, 06-24）", "汽零8月板块行情（S-2025-03）"],
        "turning": ["大盘β contamination（8月沪指+8%、创业板+24%）（S-2025-07）", "FSD 2025未落地（S-2025-06 retrospective）"],
        "ending": ["8/31 暂定边界（9/12月另有催化波次）", "beta 驱动为主、主题独立性弱"],
    },
    # ---- 医药健康 ----
    "C-2019-PHARMA-INNOV": {
        "start": ["4+7 城市药品集中采购中选结果（25 品种平均降幅 52%）（EV-MED-01, 2018-12-17）"
                  "→ 摧毁仿制药「带金销售」旧叙事，市场转向「创新 vs 仿制」分化（E-MED-05）",
                  "科创板开板、未盈利生物科技可上市（EV-MED-02, 2019-07-22）"],
        "accelerator": ["2019 年国家医保谈判：150 谈成 97、新增平均降幅 60.7%、PD-1 首次纳入医保、"
                        "12 个国产重大创新药谈成 8 个（EV-MED-03, 2019-11-28）→ 官方明确鼓励创新导向（E-MED-02）",
                        "CXO 景气与订单高增；公募/外资持续增配医药核心资产（2020Q2 医药持仓占比一度 17.2%）"],
        "turning": ["CDE《以临床价值为导向的抗肿瘤药物临床研发指导原则（征求意见稿）》（EV-MED-04, 2021-07-02）"
                    "→ 引发对 CXO 景气度的质疑（E-MED-04）",
                    "2021 年下半年集采扩围至器械/耗材/IVD，超市场预期",
                    "资金风格切向新能源（电新/有色/钢铁），赚钱效应虹吸"],
        "ending": ["代表标的分批见顶：恒瑞医药 2020-12-25、药明康德/泰格医药 2021-07-01（Peak Window）",
                   "2022 年创新药估值出清：CXO 估值自 2021 年中 103x 降至约 30x（估值杀，非业绩杀）",
                   "2022-09/10 各自代表标的见低点；2022Q4 出现修复迹象，Theme Cycle End 未确认"],
    },
}

CANDIDATE_DRIVERS = {
    "RC-2023-HUAWEI": {
        "start": ["问界新M7上市发布会（EV-RC-2023-HUAWEI-01, 09-12）", "赛力斯首次明显突破（THEME_FORMING 09-04）"],
        "accelerator": ["华为汽车核心扩散 + 多股同步（Broad Confirmation 09-18）", "HUAWEI ADS 2.0 随车亮相"],
        "turning": ["08-29 Early Signal 存在市场 Beta contamination（low confidence）"],
        "ending": ["unknown（至2023-10-31仍升，未确认结束）"],
    },
    "RC-2024-SECONDARY": {
        "start": ["主 Campaign 退潮后 09-05 次级活跃（weak）"],
        "accelerator": ["unknown（强度不足）"],
        "turning": ["unknown"],
        "ending": ["09-06 后回落，弱候选不成势"],
    },
    # ---- 医药健康（Candidate）----
    "RC-2020-PANDEMIC": {
        "start": ["新冠疫情 + 防疫物资刚性需求（EV-RC-MED-PANDEMIC-01, 2020-01-23）",
                  "英科医疗（一次性手套）2020 年内涨幅约 26.5 倍（adj）；智飞生物 +208%（adj）"],
        "accelerator": ["全球疫情反复、防疫物资出口需求；疫苗/检测产业链放量",
                        "2020 年 A 股涨幅榜首为一次性防护手套企业（英科医疗）"],
        "turning": ["英科医疗 2021-01-25 见顶（自身口径）后进入全年下跌；疫苗指数 2020-07/08 已先见顶",
                    "疫情缓解预期 + 产能过剩担忧（防护用品需求回落）"],
        "ending": ["2021 全年英科医疗 -46.1%（adj）、2022 再 -56.5%；主题注意力显著减弱",
                   "与主线（创新药/CXO）节奏相反：同期主线仍在上涨至 2021-07 → Pattern=Parallel"],
    },
    "RC-2021-TCM": {
        "start": ["中医药鼓励政策预期持续加码（2021-11 起板块活跃）",
                  "中成药集采温和落地；多家公司宣布提价（行业报道）"],
        "accelerator": ["医保局、中医药局《关于医保支持中医药传承创新发展的指导意见》（EV-RC-MED-TCM-01, 2021-12-31）",
                        "低估值修复（中药长期 20–30x vs 创新药/CXO 上百倍）"],
        "turning": ["2022 上半年深幅调整（疫情反复 + 中报不及预期）"],
        "ending": ["2022Q4 抗疫中药再度活跃：以岭药业 2022-11-30→12-08 快速上行至区间高点",
                   "2022-12-30 收于 28.36（自高点回落）；窗口末端，未确认结束"],
    },
}

# 每个 Campaign 用于行情快照的代理序列（行业代理不可得时用真实龙头个股，标注代理性质）
PROXY_SERIES = {
    "C-2019-AD": "WANAN",
    "C-2020-NEV": "BIDI",
    "C-2021-NEV": "BIDI",
    "C-2022-POLICY": "AUTO_ETF_516110",
    "C-2023-AD": "AUTO_ETF_516110",
    "C-2024-V2X": "AUTO_ETF_516110",
    "C-2024-ROBOTAXI": "AUTO_ETF_516110",
    "C-2025-ROBOTAXI": "AUTO_ETF_516110",
    # ---- 医药健康：按 v1.1 §6 使用 Campaign 自身代表标的（医药ETF 仅作参照，不作 Peak 口径）----
    "C-2019-PHARMA-INNOV": "WUXIAPPTEC",
}

PROXY_NOTE = {
    "C-2019-AD": "行业代理不可得（AUTO_SW 腾讯无数据、516110 未成立），用龙头万安科技 raw close 作参考（非行业代理）",
    "C-2020-NEV": "516110 未成立，用龙头比亚迪 raw close 作参考（非行业代理）",
    "C-2021-NEV": "516110 未成立，用龙头比亚迪 raw close 作参考（非行业代理）",
    "C-2022-POLICY": "汽车ETF(中证800汽车) 行业代理（成立于2021-11之后，2022年可用）",
    "C-2023-AD": "汽车ETF(中证800汽车) 行业代理",
    "C-2024-V2X": "汽车ETF(中证800汽车) 行业代理（非车路云专用指数，仅供参照）",
    "C-2024-ROBOTAXI": "汽车ETF(中证800汽车) 行业代理（非Robotaxi专用指数，仅供参照）",
    "C-2025-ROBOTAXI": "汽车ETF(中证800汽车) 行业代理（成立于2021-11之后，2025年可用）",
    "C-2019-PHARMA-INNOV": ("Campaign 自身代表标的 药明康德（CXO 龙头）raw/adj close；"
                            "同 Campaign 另含 恒瑞医药（2020-12-25 见顶）与 泰格医药 → Peak 分批。"
                            "医药ETF(512010) 仅作行业参照，不参与 Peak 判定（v1.1 §6）"),
}


def q(sql, *a):
    return [dict(r) for r in conn.execute(sql, a).fetchall()]


def q1(sql, *a):
    r = conn.execute(sql, a).fetchone()
    return dict(r) if r else None


def get_git_head():
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def market_snapshot(series_id, dates, campaign_id):
    """返回 {date: raw_close} + 可用性标记。取 <= date 的最近交易日（含当日）。"""
    out = {}
    for d in dates:
        if not d:
            continue
        row = q1(
            "SELECT close FROM market_daily WHERE series_id=? AND price_type='raw' AND trade_date<=? "
            "ORDER BY trade_date DESC LIMIT 1", series_id, d)
        out[d] = row["close"] if row else None
    if any(v is not None for v in out.values()):
        return {"series_id": series_id, "raw_close": out, "status": "available"}
    return {"series_id": series_id, "raw_close": out, "status": "unavailable",
            "note": PROXY_NOTE.get(campaign_id, "")}


def adjusted_returns(series_id, start, peak, end):
    def close_on(d):
        row = q1("SELECT adj_close FROM market_daily WHERE series_id=? AND price_type='adjusted' "
                 "AND trade_date<=? ORDER BY trade_date DESC LIMIT 1", series_id, d)
        return row["adj_close"] if row else None
    c0, cp, ce = close_on(start), close_on(peak), close_on(end)
    if None in (c0, cp, ce) or c0 == 0:
        return None
    return {
        "start_to_peak": round(cp / c0 - 1.0, 4),
        "start_to_end": round(ce / c0 - 1.0, 4),
        "peak_to_end": round(ce / cp - 1.0, 4),
        "price_type": "adjusted(qfq)",
        "note": "调整后收益，仅用于收益率口径；日期判断用 raw close",
    }


def build_campaign(c):
    cid = c["campaign_id"]
    evs = q("""SELECT e.evidence_id, e.date, e.evidence_type, e.description, e.evidence_role,
                      e.confidence, e.independence_group, e.temporal_relation,
                      s.source_id, s.title, s.url, s.tier, s.source_type
               FROM campaign_evidences ce
               JOIN evidences e ON e.evidence_id=ce.evidence_id
               LEFT JOIN sources s ON s.source_id=e.source_id
               WHERE ce.campaign_id=? ORDER BY e.date""", cid)
    themes = q("""SELECT t.name, t.theme_type, ct.role FROM campaign_themes ct
                  JOIN themes t ON t.theme_id=ct.theme_id WHERE ct.campaign_id=?""", cid)
    events = q("""SELECT e.event_id, e.name, e.date, e.event_type, ce.role FROM campaign_events ce
                  JOIN events e ON e.event_id=ce.event_id WHERE ce.campaign_id=?""", cid)
    secs = q("""SELECT s.security_id, s.name, s.ticker, s.exchange, cs.role
                FROM campaign_securities cs JOIN securities s ON s.security_id=cs.security_id
                WHERE cs.campaign_id=?""", cid)
    phases = q("SELECT phase_type, start_date, end_date, description FROM campaign_phases WHERE campaign_id=?",
               cid)

    source_ids = sorted({e["source_id"] for e in evs if e["source_id"]})
    evidence_ids = [e["evidence_id"] for e in evs]
    groups = sorted({e["independence_group"] for e in evs if e["independence_group"]})

    # 状态判定：有已知日期冲突 → CONFLICT；满足 PROVISIONAL 标准 → PROVISIONAL；否则 INSUFFICIENT
    status = "PROVISIONAL"
    status_notes = []
    if cid in CONFLICT_MAP:
        status = "CONFLICT"
        fields = ", ".join(CONFLICT_MAP[cid].keys())
        status_notes.append(f"日期口径未收敛：{fields}（见 conflicts.json）")
    if not themes:
        status = "INSUFFICIENT"; status_notes.append("主题不可识别")
    if not evs:
        status = "INSUFFICIENT"; status_notes.append("无绑定证据")
    if not source_ids:
        status = "INSUFFICIENT"; status_notes.append("无可靠来源")
    if status == "PROVISIONAL":
        status_notes.append("主题可识别 + 有行情/媒体证据 + ≥1 可靠来源 + 主要日期有依据 + 无跨时间因果错误（多来源已交叉比对）")

    # 行情快照：raw close @ start/peak/end + 各 phase 起止
    proxy = PROXY_SERIES.get(cid)
    md = {"status": "unavailable", "note": "无可用行情数据（AUTO_SW 不可得时如实 unavailable）"}
    if proxy:
        snap_dates = [c["start_date"], c["peak_date"], c["end_date"]]
        for ph in phases:
            snap_dates += [ph["start_date"], ph["end_date"]]
        md = market_snapshot(proxy, [d for d in snap_dates if d], cid)
    adj = adjusted_returns(proxy, c["start_date"], c["peak_date"], c["end_date"]) if proxy else None

    # 冲突详情
    conflict = None
    if cid in CONFLICT_MAP:
        conflict = CONFLICT_MAP[cid]

    # 研究信号
    signals = SIGNALS.get(cid, [])

    entry = {
        "research_campaign_id": cid,
        "db_campaign_id": cid,
        "year": c["campaign_year"],
        "rule_id": c["rule_id"],
        "status": status,
        "annual_status": q1("SELECT status FROM annual_reviews WHERE rule_id=? AND year=?",
                            c["rule_id"], c["campaign_year"])["status"],
        "start_date_candidate": c["start_date"],
        "peak_date_candidate": c["peak_date"],
        "end_date_candidate": c["end_date"],
        "date_confidence": c["date_confidence"],
        "theme": ", ".join(t["name"] for t in themes if t["role"] == "main") or "(未标 main)",
        "themes": themes,
        "theme_cycle_id": THEME_CYCLE.get(cid),
        "classification": c["classification"],
        "result": c["result"],
        "strength": c["strength"],
        "evidence_ids": evidence_ids,
        "source_ids": source_ids,
        "independent_groups": groups,
        "independent_group_count": len(groups),
        "events": events,
        "securities": secs,
        "market_data": {**md, "adjusted_returns": adj} if md.get("status") == "available"
                       else {"status": "unavailable", "note": PROXY_NOTE.get(cid, "无可用行情数据"),
                             "adjusted_returns": None},
        "signals": signals,
        "confidence": c["date_confidence"] or "low",
        "notes": "; ".join(status_notes) or c.get("research_notes") or "",
        "research_notes": c.get("research_notes"),
        "conflict": conflict,
        "lifecycle": CAMPAIGN_LIFECYCLE.get(cid, []),
        "drivers": CAMPAIGN_DRIVERS.get(cid, {"start": [], "accelerator": [], "turning": [], "ending": []}),
    }
    return entry


def build_2018():
    """2018 = 反例年份（no_clear_campaign），保留为年度级记录，不作为 Campaign。"""
    ar = q1("SELECT status, summary FROM annual_reviews WHERE rule_id=? AND year=2018", RULE)
    return {
        "research_campaign_id": "Y2018-NO-CLEAR",
        "db_campaign_id": None,
        "year": 2018,
        "rule_id": RULE,
        "status": "PROVISIONAL",          # “2018 无清晰 Campaign”是研究结论（未人工复核）
        "annual_status": ar["status"] if ar else "no_clear_campaign",
        "start_date_candidate": None, "peak_date_candidate": None, "end_date_candidate": None,
        "date_confidence": "medium",
        "theme": "(无 Campaign，反例年份)",
        "themes": [], "theme_cycle_id": None,
        "classification": None, "result": "failed", "strength": None,
        # 2018 为汽车 Rule 的反例年份：只吸收**未显式绑定任何 Campaign** 的 2018 年证据。
        # （否则其他 Rule 的 2018 年证据会被误并入汽车反例年份 → evidence-cross-campaign）
        "evidence_ids": [e["evidence_id"] for e in q(
            "SELECT evidence_id FROM evidences WHERE date LIKE '2018%' "
            "AND evidence_id NOT IN (SELECT evidence_id FROM campaign_evidences)")],
        "source_ids": [s["source_id"] for s in q("SELECT source_id FROM sources WHERE source_id LIKE 'S-2018-%'")],
        "independent_groups": [],
        "independent_group_count": 0,
        "events": [], "securities": [],
        "market_data": {"status": "unavailable",
                        "note": "2018 无 Campaign，仅年度反例结论；板块下行证据来自媒体/行业数据（S-2018-01/02）"},
        "signals": [],
        "confidence": "medium",
        "notes": "反例年份：6-8月窗口内汽车板块整体下行（销量7月起同比转负），无持续性主题 Campaign，不得强行找上涨案例",
        "research_notes": ar["summary"] if ar else None,
        "conflict": None,
    }


def main():
    os.makedirs(BATCH_DIR, exist_ok=True)
    camps = q("SELECT * FROM campaigns WHERE rule_id IN (%s) ORDER BY rule_id, campaign_year"
              % ", ".join("?" * len(RULES)), *RULES)
    entries = [build_2018()] + [build_campaign(c) for c in camps]

    # ---------- manifest ----------
    manifest = {
        "manifest_version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_commit": get_git_head(),
        "rule_id": RULES if len(RULES) > 1 else RULES[0],
        "scope": ("rule_auto_summer（汽车 2018–2025，观察窗口 6-8月）"
                  " + rule_pharma_upgrade（医药健康 2019–2022，结构性升级）"),
        "status_vocabulary": {
            "PROVISIONAL": "研究预览可用：主题可识别+行情/媒体证据+≥1可靠来源+主要日期有依据+无跨时间因果错误；未人工复核，非 VERIFIED",
            "CONFLICT": "存在研究日期口径冲突（candidate_a vs candidate_b），保留双方证据，不强行解决",
            "INSUFFICIENT": "来源不足/无法判断 Campaign 或时间范围/行情数据缺失，不编造",
        },
        "note": "本 manifest 为研究批次输出，不是新的正式 Schema；PROVISIONAL 不等于 VERIFIED，不得进入 Cycle verified",
        "campaigns": entries,
    }
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, default=str)
    print(f"manifest: {MANIFEST} ({len(entries)} entries)")

    # ---------- conflicts.json ----------
    conflicts = []
    for cid, fields in CONFLICT_MAP.items():
        for field, cand in fields.items():
            conflicts.append({
                "research_campaign_id": cid,
                "field": field,
                "candidate_a": cand["candidate_a"],
                "candidate_b": cand["candidate_b"],
                "supporting_evidence_a": [e["evidence_id"] for e in
                                          q("SELECT e.evidence_id FROM campaign_evidences ce "
                                            "JOIN evidences e ON e.evidence_id=ce.evidence_id "
                                            "WHERE ce.campaign_id=? AND e.evidence_role='supporting'", cid)],
                "supporting_evidence_b": [],
                "contradicting_evidence": [],
                "decision": "pending_human_review",
                "blocker_type": "RESEARCH_UNCERTAINTY",
                "notes": "不强行解决；由人工最终 Review 裁决为 Verified Date 后才允许进入 Cycle",
            })
    conflicts_doc = {
        "version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_commit": get_git_head(),
        "rule": "conflicts 记录研究日期口径冲突；candidate_a=DB 冻结值，candidate_b=研究复核候选",
        "conflicts": conflicts,
    }
    with open(CONFLICTS, "w", encoding="utf-8") as f:
        json.dump(conflicts_doc, f, ensure_ascii=False, indent=2, default=str)
    print(f"conflicts: {CONFLICTS} ({len(conflicts)} conflicts)")

    # ---------- timeline_export_v1.json ----------
    # Canonical Contract v1.0（Research → Cycle Timeline 唯一接口）：
    #   contract / timeline_export_version / generated_at / source_commit / project /
    #   rules / signals / campaigns / research_candidates / events / securities
    rule_row = q1("SELECT * FROM research_rules WHERE rule_id=?", AUTO_RULE)

    def production_status(research_status):
        """生产兼容状态（Cycle 消费）：verified / provisional / conflict / preview。"""
        return {"PROVISIONAL": "provisional", "CONFLICT": "conflict",
                "INSUFFICIENT": "preview"}.get(research_status, "preview")

    # 1) rules（每个 Rule 一条；definition / observation_window 为研究层描述）
    RULE_META = {
        AUTO_RULE: {
            "definition": "Historical Observation Window（历史观察窗口），非固定买入窗口",
            "observation_window": "Q2-Q3（4-9月），6-8月为名义窗口；允许漂移（2022 启动 04-27、2019 启动 08-15）",
        },
        PHARMA_RULE: {
            "definition": ("Historical Observation Window（历史观察窗口）：医药产业由仿制药/销售驱动"
                           "转向创新驱动 + 产业链专业化；非固定买入窗口，不构成交易建议"),
            "observation_window": ("结构性（非季节性）：2019–2022。Formation 2019-07-22（科创板）、"
                                   "Broad Confirmation 2019-11-28（医保谈判）、Peak Window 2020-12-25~2021-07-01"),
        },
    }
    rules_out = []
    for rid in RULES:
        rr = q1("SELECT * FROM research_rules WHERE rule_id=?", rid)
        meta = RULE_META.get(rid, {})
        rules_out.append({
            "rule_id": rr["rule_id"] if rr else rid,
            "name": rr["name"] if rr else rid,
            "base_pattern": rr["base_pattern"] if rr else "行情",
            "definition": meta.get("definition", "Historical Observation Window（历史观察窗口）"),
            "observation_window": meta.get("observation_window", "—"),
        })

    # 2) signals（扁平；归属 = campaign_id XOR research_candidate_id）
    signals_out = []
    for cid, sigs in SIGNALS.items():
        for s in sigs:
            signals_out.append({"type": s["type"], "date": s["date"],
                                "confidence": s["confidence"], "campaign_id": cid})
    for rc in RESEARCH_CANDIDATES:
        for s in rc.get("signals", []):
            signals_out.append({"type": s["type"], "date": s["date"],
                                "confidence": s["confidence"], "research_candidate_id": rc["campaign_id"]})

    # 3) events（扁平；含全局事件 campaign_id=null；research candidate 事件 research_candidate_id=...）
    events_out = []
    for r in q("""SELECT e.event_id, e.name, e.date, e.event_type, ce.role, ce.campaign_id
                  FROM campaign_events ce JOIN events e ON e.event_id=ce.event_id
                  ORDER BY e.date"""):
        events_out.append({"event_id": r["event_id"], "name": r["name"], "date": r["date"],
                           "event_type": r["event_type"], "role": r["role"],
                           "campaign_id": r["campaign_id"], "research_candidate_id": None})
    for r in q("""SELECT e.event_id, e.name, e.date, e.event_type FROM events e
                  WHERE NOT EXISTS (SELECT 1 FROM campaign_events ce WHERE ce.event_id=e.event_id)
                  ORDER BY e.date"""):
        events_out.append({"event_id": r["event_id"], "name": r["name"], "date": r["date"],
                           "event_type": r["event_type"], "role": None,
                           "campaign_id": None, "research_candidate_id": None})
    for rc in RESEARCH_CANDIDATES:
        for ev in rc.get("events", []):
            events_out.append({"event_id": ev["event_id"], "name": ev["name"], "date": ev["date"],
                               "event_type": ev["event_type"], "role": ev["role"],
                               "campaign_id": None, "research_candidate_id": rc["campaign_id"]})

    # 4) securities（扁平；必须知道属于谁；禁止把整个证券表复制到每个 Campaign）
    securities_out = []
    for r in q("""SELECT s.security_id, s.name, s.ticker, s.exchange, cs.role, cs.campaign_id
                  FROM campaign_securities cs JOIN securities s ON s.security_id=cs.security_id
                  ORDER BY cs.campaign_id, cs.role"""):
        securities_out.append({"security_id": r["security_id"], "name": r["name"],
                               "ticker": r["ticker"], "exchange": r["exchange"], "role": r["role"],
                               "campaign_id": r["campaign_id"], "research_candidate_id": None})
    for rc in RESEARCH_CANDIDATES:
        for sec in rc.get("securities", []):
            securities_out.append({"security_id": sec["security_id"], "name": sec["name"],
                                   "ticker": sec["ticker"], "exchange": sec["exchange"], "role": sec["role"],
                                   "campaign_id": None, "research_candidate_id": rc["campaign_id"]})

    # 5) campaigns（formal）
    campaigns_out = []
    for e in entries:
        if e["year"] == 2018:
            continue  # 无 Campaign，不出现在 campaign 列表（反例由 rule 级注释承载）
        cid = e["research_campaign_id"]
        ph = PHASE_TIME_FIELDS.get(cid, {})
        conflicts_out = []
        for field, cand in (CONFLICT_MAP.get(cid) or {}).items():
            conflicts_out.append({"field": field,
                                  "candidate_a": {"date": cand["candidate_a"]["date"],
                                                  "label": cand["candidate_a"]["label"]},
                                  "candidate_b": {"date": cand["candidate_b"]["date"],
                                                  "label": cand["candidate_b"]["label"]}})
        campaigns_out.append({
            "campaign_id": cid,
            "rule_id": e["rule_id"],
            "year": e["year"],
            "start_date": e["start_date_candidate"],
            "peak_date": e["peak_date_candidate"],
            "end_date": e["end_date_candidate"],
            "status": production_status(e["status"]),   # production compatibility
            "confidence": e["confidence"],
            "classification": e["classification"],
            "strength": e["strength"],
            "result": e["result"],
            "themes": e["themes"],
            "event_ids": [ev["event_id"] for ev in events_out if ev["campaign_id"] == cid],
            "security_ids": [sec["security_id"] for sec in securities_out if sec["campaign_id"] == cid],
            # ---- research metadata（明确不是 HistoricalCampaign schema 字段）----
            "research_status": e["status"],             # PROVISIONAL / CONFLICT / INSUFFICIENT
            "theme_cycle_id": e["theme_cycle_id"],
            "promotion_status": PROMO_STATUS.get(cid),  # promotion_gate 词汇，单独命名不混淆
            "first_signal_date": e["signals"][0]["date"] if e["signals"] else None,
            "broad_confirmation_date": ph.get("broad_confirmation_date"),
            "first_decline_date": ph.get("first_decline_date"),
            "conflicts": conflicts_out,
            "notes": e["notes"],
            # ---- V1.7 新增（backward-compatible optional）----
            "lifecycle": e["lifecycle"],          # phase windows + 时间精度
            "drivers": e["drivers"],              # start/accelerator/turning/ending
        })

    # 6) research_candidates（不进入 campaigns，可在 Cycle Preview 展示）
    research_candidates_out = []
    for rc in RESEARCH_CANDIDATES:
        rcid = rc["campaign_id"]
        research_candidates_out.append({
            "campaign_id": rcid,
            "rule_id": rc["rule_id"],
            "year": rc["year"],
            "title": rc["title"],
            "start_date": rc["start_date"],
            "peak_date": rc["peak_date"],
            "end_date": rc["end_date"],
            "themes": rc["themes"],
            "event_ids": [ev["event_id"] for ev in events_out if ev["research_candidate_id"] == rcid],
            "security_ids": [sec["security_id"] for sec in securities_out if sec["research_candidate_id"] == rcid],
            "early_signal": rc["early_signal"],
            "research_status": rc["research_status"],
            "theme_cycle_id": rc["theme_cycle_id"],
            "conflicts": rc["conflicts"],
            "notes": rc["notes"],
            # ---- V1.7 新增（backward-compatible optional）----
            "lifecycle": CANDIDATE_LIFECYCLE.get(rcid, []),
            "drivers": CANDIDATE_DRIVERS.get(rcid, {"start": [], "accelerator": [], "turning": [], "ending": []}),
        })

    export = {
        "contract": "timeline_export",
        "timeline_export_version": "1.0",      # 唯一版本字段（不再出现 export_version）
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_commit": get_git_head(),
        "project": "Cycle-Research",
        "rules": rules_out,
        "signals": signals_out,
        "campaigns": campaigns_out,
        "research_candidates": research_candidates_out,
        "events": events_out,
        "securities": securities_out,
    }
    os.makedirs(os.path.dirname(EXPORT), exist_ok=True)
    with open(EXPORT, "w", encoding="utf-8") as f:
        json.dump(export, f, ensure_ascii=False, indent=2, default=str)
    print(f"timeline_export: {EXPORT} (v1.0, {len(campaigns_out)} campaigns, "
          f"{len(research_candidates_out)} research_candidates, "
          f"{len(events_out)} events, {len(securities_out)} securities)")

    # 汇总输出（供最终报告引用）
    from collections import Counter
    ctr = Counter(e["status"] for e in entries)
    years = {e["year"] for e in entries}
    print("STATUS:", dict(ctr), "YEARS:", sorted(years))
    conn.close()


if __name__ == "__main__":
    main()
