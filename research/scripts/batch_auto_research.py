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
POWER_RULE = "rule_power_equipment"   # 电力设备（Wave 1A — 电力设备历史 Cycle）
COMM_RULE = "rule_infocomm"           # 信息通信（Wave 1B — 信息通信历史 Cycle）
HIEQ_RULE = "rule_high_end_equipment"  # 高端装备 / 机器人（Wave R01-01 — Historical Universe Expansion）
SEMI_RULE = "rule_semiconductor"        # 半导体 / 电子（Wave R01-02 — Historical Universe Expansion）
RES_RULE = "rule_resources"             # 资源 / 有色 / 化工（Wave R01-03 — Historical Universe Expansion）
CONS_RULE = "rule_consumer"              # 消费（Wave R01-04 — Historical Universe Expansion）
FINRE_RULE = "rule_fin_realestate"       # 金融 / 房地产（Wave R01-05 — Historical Universe Expansion）
MIL_RULE = "rule_defense_military"       # 国防军工（Wave R01-06 — Historical Universe Expansion）
# 批量研究覆盖的 Rule（按顺序生成；新增 Macro Theme 在此登记）
RULES = [AUTO_RULE, PHARMA_RULE, POWER_RULE, COMM_RULE, HIEQ_RULE, SEMI_RULE, RES_RULE, CONS_RULE, FINRE_RULE, MIL_RULE]
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
    # ---- 电力设备（Wave 1A，Primary Macro Theme = TH-POWER）----
    # 两个 Cycle 的 Primary 均为 TH-POWER；互为独立 Cycle（形成锚点 / 核心驱动 / Peak 均不同）。
    "C-2020-POWER-NE": "power_ne_equipment_2020_2022",
    "C-2022-POWER-GRID": "power_grid_uhv_2022_2025",
    # ---- 信息通信（Wave 1B，Primary Macro Theme = TH-COMM）----
    # 两个 Cycle 的 Primary 均为 TH-COMM；独立性见 seed_comm_cycles.py 的 research_notes。
    "C-2019-COMM-5G": "comm_5g_infrastructure_2019_2022",
    "C-2023-COMM-OPTICAL": "comm_ai_optical_2023_2025",
    # ---- 高端装备（Wave R01-01，Primary Macro Theme = TH-HIEQ）----
    # 002 与 003 同属 hieq_robot_2018_2022（Sequential）；004 与 005 同属 hieq_robot_2023（Sequential）。
    "C-2016-HIEQ-CONSTR": "hieq_constr_2016_2021",
    "C-2018-HIEQ-ROBOT-DOWN": "hieq_robot_2018_2019",
    "C-2020-HIEQ-AUTOMATION": "hieq_automation_2020_2022",
    "C-2023-HIEQ-ROBOT-PLUS": "hieq_robot_2023",
    "C-2023-HIEQ-HUMANOID": "hieq_robot_2023",

    # ---- 半导体 / 电子（Wave R01-02，Primary Macro Theme = TH-ELEC）----
    # 001 与 002 同属 semi_localization_2019_2021（Sequential）；003 与 011 同属 panel_price_cycle_2016_2022（同一机制族的两轮实例）。
    "C-2019-SEMI-LOCALIZATION": "semi_localization_2019_2021",
    "C-2020-SEMI-EQUIPMENT": "semi_localization_2019_2021",
    "C-2020-PANEL-CYCLE": "panel_price_cycle_2016_2022",
    "C-2019-CONSUMER-TWS": "electronics_tws_2019_2020",
    "C-2023-AI-COMPUTE-SEMI": "ai_compute_semi_2023",
    "C-2024-SEMI-MEMORY": "memory_supercycle_2024_2025",
    "C-2022-SEMI-DOWNTURN": "semi_inventory_downturn_2022",
    "C-2016-PANEL-CYCLE": "panel_price_cycle_2016_2022",

    # ---- 资源 / 有色 / 化工（Wave R01-03，Primary Macro Theme = TH-RES）----
    # 001/002/003/004 同属 resource_reflation_2020_2022（Pattern = Parallel，四个机制各异的独立 Campaign）
    "C-2020-RES-NONFERROUS": "resource_reflation_2020_2022",
    "C-2020-RES-LITHIUM": "resource_reflation_2020_2022",
    "C-2020-RES-RAREEARTH": "resource_reflation_2020_2022",
    "C-2021-RES-CHEM-DUALCTRL": "resource_reflation_2020_2022",
    "C-2019-RES-DYE-SHOCK": "dye_shock_2019",
    "C-2024-RES-GOLD-CB": "gold_cb_demand_2024_2025",

    # ---- 消费（Wave R01-04，Primary Macro Theme = TH-CONSUMER）----
    # 001+002（白酒 Sequential）· 003+004（服务消费 Sequential）· 005+006（猪周期 Sequential）
    # 009+010（颜值经济 Parallel）· 008 / 011 / 012 各自独立
    "C-2016-CONS-BAIJIU-UPGRADE": "baijiu_premium_2016_2021",
    "C-2019-CONS-BAIJIU-CORE": "baijiu_premium_2016_2021",
    "C-2020-CONS-DUTYFREE": "service_consumption_2020_2023",
    "C-2022-CONS-SERVICE-REBOUND": "service_consumption_2020_2023",
    "C-2018-CONS-HOG-AFRICAN": "hog_cycle_2018_2022",
    "C-2021-CONS-HOG-REVERSAL": "hog_cycle_2018_2022",
    "C-2020-CONS-WHITE-GOODS": "appliance_export_2020_2021",
    "C-2019-CONS-AESTHETICS": "beauty_aesthetics_2019_2022",
    "C-2020-CONS-BEAUTY-CN": "beauty_aesthetics_2019_2022",
    "C-2024-CONS-TRADE-IN": "trade_in_2024_2025",
    "C-2023-CONS-VALUE-RETAIL": "value_retail_2023_2025",

    # ---- 金融 / 房地产（Wave R01-05，Primary Macro Theme = TH-FIN / TH-REALESTATE）----
    # 004+001（地产政策周期 Sequential：004 下行 → 001 政策修复）· 006+007（银行估值/资金配置 Parallel）
    # 005（券商 2024-09）· 008（银行信用周期 2020-2021）· 010（保险 2025）各自独立 Cycle
    "C-2020-RE-DEBT-RISK": "realestate_policy_cycle_2020_2023",
    "C-2022-RE-POLICY-THREE": "realestate_policy_cycle_2020_2023",
    "C-2023-FIN-SOE-VALUATION": "bank_valuation_2023_2025",
    "C-2024-FIN-BANK-DIVIDEND": "bank_valuation_2023_2025",
    "C-2024-FIN-BROKER-POLICY": "broker_risk_appetite_2024",
    "C-2020-FIN-BANK-CREDIT": "bank_credit_cycle_2020_2021",
    "C-2025-FIN-INSURANCE": "insurance_asset_liability_2025",

    # ---- 国防军工（Wave R01-06，Primary Macro Theme = TH-DEFENSE）----
    # 001 装备订单景气（2020-2022）与 002 集团战略重组（2019）**机制不同、窗口不重叠** → 各自独立 Cycle
    "C-2020-MIL-EQUIP-ORDER": "military_equipment_order_cycle_2020_2022",
    "C-2019-MIL-GROUP-RESTRUCTURE": "military_group_restructure_2019",
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
    # ---- 电力设备（Wave 1A）----
    # Cycle 1：EARLY_SIGNAL = 双碳目标宣布（2020-09-22，官方讲话）；
    #          THEME_FORMING = 气候雄心峰会明确 12 亿千瓦装机目标（2020-12-12，首次可量化）。
    "C-2020-POWER-NE": [
        {"type": "EARLY_SIGNAL", "date": "2020-09-22", "confidence": "high"},
        {"type": "THEME_FORMING", "date": "2020-12-12", "confidence": "high"},
    ],
    # Cycle 2：EARLY_SIGNAL = 特高压核准提速（2022-01-10，行业媒体）；
    #          THEME_FORMING = 国网年度工作会议 5012 亿元电网投资计划（2022-01-16，官方口径）。
    # 注：市场在 2022-01-18/19 即「利好兑现」见顶回落，该回撤记入 lifecycle RETRACEMENT，未隐藏。
    "C-2022-POWER-GRID": [
        {"type": "EARLY_SIGNAL", "date": "2022-01-10", "confidence": "medium"},
        {"type": "THEME_FORMING", "date": "2022-01-16", "confidence": "high"},
    ],
    # ---- 信息通信（Wave 1B）----
    # Cycle 1：EARLY_SIGNAL = 工信部发放 5G 商用牌照（2019-06-06）；
    #          THEME_FORMING = 5G 商用启动仪式（2019-10-31，三大运营商发布 5G 套餐）。
    "C-2019-COMM-5G": [
        {"type": "EARLY_SIGNAL", "date": "2019-06-06", "confidence": "high"},
        {"type": "THEME_FORMING", "date": "2019-10-31", "confidence": "high"},
    ],
    # Cycle 2：EARLY_SIGNAL = NVIDIA GTC 2023 主题演讲（2023-03-21，AI 算力叙事）；
    #          THEME_FORMING = NVIDIA Q1 FY2024 财报 Q2 指引 110 亿美元（2023-05-24，需求财务确认）。
    "C-2023-COMM-OPTICAL": [
        {"type": "EARLY_SIGNAL", "date": "2023-03-21", "confidence": "high"},
        {"type": "THEME_FORMING", "date": "2023-05-24", "confidence": "high"},
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
    # ---- 电力设备（Wave 1A）----
    # Cycle 1：BROAD_CONFIRMATION = 整县屋顶分布式光伏试点名单公布 676 县（2021-09-08）。
    "C-2020-POWER-NE": {"broad_confirmation_date": "2021-09-08"},
    # Cycle 2：BROAD_CONFIRMATION = 国网披露再开工 8 项特高压、在建项目投资破万亿（2022-08-03）。
    "C-2022-POWER-GRID": {"broad_confirmation_date": "2022-08-03"},
    # ---- 信息通信（Wave 1B）----
    # Cycle 1：BROAD_CONFIRMATION = 中央政治局常委会「加快 5G 网络、数据中心等新型基础设施建设进度」（2020-03-04）。
    "C-2019-COMM-5G": {"broad_confirmation_date": "2020-03-04"},
    # Cycle 2：BROAD_CONFIRMATION = 中际旭创 2023 半年报「下半年 800G 出货量明显增长」（2023-08-28）。
    "C-2023-COMM-OPTICAL": {"broad_confirmation_date": "2023-08-28"},
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
    # ==== 消费（Wave R01-04）：RESEARCH_ONLY，**不进入 campaigns 表** ====
    {
        "campaign_id": "RC-2020-CONS-SMALL-APPLIANCE",
        "rule_id": "rule_consumer",
        "year": 2020,
        "title": "2020–2021 小家电与清洁电器（疫情居家需求 + 产品创新 + 渗透率提升 + 出口）",
        "start_date": "2020-02-01",
        "peak_date": "2021-07-15",
        "end_date": "2021-12-31",
        "themes": [
            {
                "name": "消费",
                "theme_type": "industry",
                "role": "related"
            },
            {
                "name": "家用电器",
                "theme_type": "industry",
                "role": "main"
            }
        ],
        "securities": [
            {
                "security_id": "MIDEA",
                "name": "美的集团",
                "ticker": "000333",
                "exchange": "SZ",
                "role": "representative"
            },
            {
                "security_id": "GREE",
                "name": "格力电器",
                "ticker": "000651",
                "exchange": "SZ",
                "role": "representative"
            },
            {
                "security_id": "HAIER",
                "name": "海尔智家",
                "ticker": "600690",
                "exchange": "SH",
                "role": "representative"
            }
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "small_appliance_2020_2021",
        "conflicts": [],
        "notes": "与白电候选（R01-CONSUMER-008）同属家电大类，存在\"同一资金池的不同分支\"风险（Q1 Anti-example）。本包按代表标的组与生命周期错位拆分为两个候选，但是否应判为同一 Campaign 下的两个 sub-theme 保留为 Conflict CF008。此外，渗透率提升这一核心机制缺少一手量化数据，证据强度弱于其他候选。"
    },
    {
        "campaign_id": "RC-2024-CONS-PET-FOOD",
        "rule_id": "rule_consumer",
        "year": 2024,
        "title": "2024–2025 宠物食品（情感消费 + 出口增长）",
        "start_date": "2024-10-01",
        "peak_date": "2025-06-30",
        "end_date": None,
        "themes": [
            {
                "name": "消费",
                "theme_type": "industry",
                "role": "related"
            },
            {
                "name": "农林牧渔",
                "theme_type": "industry",
                "role": "main"
            }
        ],
        "securities": [
            {
                "security_id": "ROBOROCK",
                "name": "石头科技",
                "ticker": "688169",
                "exchange": "SH",
                "role": "representative"
            },
            {
                "security_id": "BEAR",
                "name": "小熊电器",
                "ticker": "002959",
                "exchange": "SZ",
                "role": "representative"
            }
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "pet_food_2024_2025",
        "conflicts": [],
        "notes": "★ 证据明显不足：① 无一手官方数据（行业规模、出口数据均为媒体转述）；② 无明确的启动事件锚点，启动阶段只能以 PHASE_WINDOW 表达；③ A 股可交易标的仅 2–3 只，板块广度严重不足，难以满足\"市场关注/扩散\"标准；④ 持续时间仅约 2–3 个季度，接近 OBSERVATION_ONLY 边界。故研究状态为 INSUFFICIENT，置信度 low，建议后续轮次补齐海关总署出口原文与行业协会官方数据后再评估。"
    },
    # ==== 资源 / 有色 / 化工（Wave R01-03）：RESEARCH_ONLY，**不进入 campaigns 表** ====
    {
        "campaign_id": "RC-2020-RES-GOLD-RATES",
        "rule_id": "rule_resources",
        "year": 2020,
        "title": "2019–2020 黄金：实际利率下行与避险驱动行情",
        "start_date": "2019-05-01",
        "peak_date": "2020-08-07",
        "end_date": "2020-12-31",
        "themes": [
            {
                "name": "资源",
                "theme_type": "industry",
                "role": "related"
            },
            {
                "name": "贵金属",
                "theme_type": "industry",
                "role": "main"
            }
        ],
        "securities": [
            {
                "security_id": "SDGOLD",
                "name": "山东黄金",
                "ticker": "600547",
                "exchange": "SH",
                "role": "representative"
            },
            {
                "security_id": "ZJGOLD",
                "name": "中金黄金",
                "ticker": "600489",
                "exchange": "SH",
                "role": "representative"
            },
            {
                "security_id": "HNGOLD",
                "name": "湖南黄金",
                "ticker": "002155",
                "exchange": "SZ",
                "role": "representative"
            }
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "gold_rates_2019_2020",
        "conflicts": [],
        "notes": "① A 股黄金板块（山东黄金、中金黄金等）在该窗口的市场响应证据弱于商品端，本任务未收集到足够的板块口径行情证据；② 2019 年与 2020 年两段上行是否属同一 Campaign，需 Independence Gate 判定（存在 2020-03 流动性冲击隔断）。"
    },
    {
        "campaign_id": "RC-2022-RES-FERTILIZER",
        "rule_id": "rule_resources",
        "year": 2022,
        "title": "2021–2022 农化（化肥）成本冲击与出口限制驱动行情",
        "start_date": "2021-01-01",
        "peak_date": "2022-03-31",
        "end_date": "2022-11-30",
        "themes": [
            {
                "name": "资源",
                "theme_type": "industry",
                "role": "related"
            },
            {
                "name": "农化",
                "theme_type": "industry",
                "role": "main"
            }
        ],
        "securities": [
            {
                "security_id": "YUNTIANHUA",
                "name": "云天化",
                "ticker": "600096",
                "exchange": "SH",
                "role": "representative"
            },
            {
                "security_id": "ASIAPOTASH",
                "name": "亚钾国际",
                "ticker": "000893",
                "exchange": "SZ",
                "role": "representative"
            },
            {
                "security_id": "XINYANGFENG",
                "name": "新洋丰",
                "ticker": "000902",
                "exchange": "SZ",
                "role": "representative"
            }
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "fertilizer_cost_2021_2022",
        "conflicts": [],
        "notes": "① 无法确立商品与 A 股主题的完整因果证据链（结论降级为「证据不足 / 无法确认」）：E075 显示 A 股「化肥」概念板块 2021-01-04 至 2021-12-31 区间涨跌幅 +24.24%（区间最高 1048.07 点，2021-09-28），板块级响应确实存在，故不能据此断定「商品上行期板块未同步走强」；但 E075 的 +24.24% 与其峰值（2021-09-28）仅覆盖 2021 年，与本候选观测到的商品 peak 窗口（2022-03—2022-04，E071）存在约半年的领先滞后错位，包内现有证据无法判定二者是否属同一结构或存在领先滞后关系。② 本候选现有全部 evidence 均为 subsequent 口径（E071 FAO 2022-12-05、E072 USDA 2022-04-06、E073/E074 商务部 2023-01-13），无一条同期可观察证据可直接锁定 A 股主题启动；S047 的市场响应数据为 2026-09-19 采集、published_at 为空，作为「同期催化」的效力亦有限。③ 因此本候选的核心缺口不是「存在反例」，而是「无法确认传导」，需 Intake Review 或后续轮次补齐 2022 年逐月板块序列与同期政策/价格锚点后方可判定。④ 是否属「农业/粮食安全」主题（R01-04）而非本任务的资源/化工机制，仍需边界裁定。"
    },
    {
        "campaign_id": "RC-2025-RES-COPPER",
        "rule_id": "rule_resources",
        "year": 2025,
        "title": "2024–2025 铜：矿端结构性供给缺口与电网/新能源需求",
        "start_date": "2024-03-01",
        "peak_date": "2025-12-31",
        "end_date": None,
        "themes": [
            {
                "name": "资源",
                "theme_type": "industry",
                "role": "related"
            },
            {
                "name": "有色金属",
                "theme_type": "industry",
                "role": "main"
            }
        ],
        "securities": [
            {
                "security_id": "JXCOPPER",
                "name": "江西铜业",
                "ticker": "600362",
                "exchange": "SH",
                "role": "representative"
            },
            {
                "security_id": "ZIJIN",
                "name": "紫金矿业",
                "ticker": "601899",
                "exchange": "SH",
                "role": "representative"
            },
            {
                "security_id": "CMOC",
                "name": "洛阳钼业",
                "ticker": "603993",
                "exchange": "SH",
                "role": "representative"
            }
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "copper_mine_gap_2024_2025",
        "conflicts": [],
        "notes": "① 与 C1 同属铜价周期，存在「一个铜长周期 vs 两个独立阶段」的边界争议；② 商品与 A 股铜板块的传导证据不足（本任务未收集到足够的板块行情证据）；③ classification 在 theme_campaign 与 industry_trend 之间存在歧义。"
    },
    {
        "campaign_id": "RC-2017-RES-ALUMINUM",
        "rule_id": "rule_resources",
        "year": 2017,
        "title": "2017 电解铝清理违规产能（有色·行政去产能）",
        "start_date": "2017-04-12",
        "peak_date": "2017-08-09",
        "end_date": "2017-12-31",
        "themes": [
            {
                "name": "资源",
                "theme_type": "industry",
                "role": "related"
            },
            {
                "name": "有色金属",
                "theme_type": "industry",
                "role": "main"
            }
        ],
        "securities": [
            {
                "security_id": "CHALCO",
                "name": "中国铝业",
                "ticker": "601600",
                "exchange": "SH",
                "role": "representative"
            },
            {
                "security_id": "YUNAL",
                "name": "云铝股份",
                "ticker": "000807",
                "exchange": "SZ",
                "role": "representative"
            },
            {
                "security_id": "SHENHUO",
                "name": "神火股份",
                "ticker": "000933",
                "exchange": "SZ",
                "role": "representative"
            }
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "aluminum_capacity_cut_2017",
        "conflicts": [],
        "notes": "Priority B 资料密度低于 Priority A：缺少可引用的电解铝板块指数与个股行情序列，A 股市场扩散证据弱于商品端；且与 2016 年煤炭/钢铁供给侧改革行情存在机制同源性但 scope 不同（煤炭/钢铁不在本任务 scope）。"
    },
    {
        "campaign_id": "RC-2016-RES-CHEM-ENV",
        "rule_id": "rule_resources",
        "year": 2016,
        "title": "2016 化工：环保约束下的商品涨价与 A 股板块背离（待定）",
        "start_date": "2016-01-04",
        "peak_date": None,
        "end_date": None,
        "themes": [
            {
                "name": "资源",
                "theme_type": "industry",
                "role": "related"
            },
            {
                "name": "基础化工",
                "theme_type": "industry",
                "role": "main"
            }
        ],
        "securities": [],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "chem_env_constraint_2016",
        "conflicts": [],
        "notes": "A 股主题成立的证据不足：同期申万基础化工板块区间涨跌幅为 -7.13%，商品价格上行未伴随 A 股板块行情；缺少板块内部结构（哪些子行业/标的上涨）的证据，也缺少可识别的启动锚点与扩散过程。按协议 §4.2，「资料不足」不等于「不成立」，故用 INSUFFICIENT 而非 REJECT。"
    },
    # ==== 半导体 / 电子（Wave R01-02）：RESEARCH_ONLY，**不进入 campaigns 表** ====
    {
        "campaign_id": "RC-2022-SEMI-CHIPSHORTAGE",
        "rule_id": "rule_semiconductor",
        "year": 2022,
        "title": "2020–2022 全球「缺芯」与半导体全产业链涨价（供给约束 + 重复下单）",
        "start_date": None,
        "peak_date": None,
        "end_date": "2022-12-31",
        "themes": [
            {
                "name": "电子",
                "theme_type": "industry",
                "role": "related"
            },
            {
                "name": "半导体",
                "theme_type": "concept",
                "role": "main"
            }
        ],
        "securities": [
            {
                "security_id": "MAXSCEND",
                "name": "卓胜微",
                "ticker": "300782",
                "exchange": "SZ",
                "role": "representative"
            },
            {
                "security_id": "JCET",
                "name": "长电科技",
                "ticker": "600584",
                "exchange": "SH",
                "role": "representative"
            },
            {
                "security_id": "TFME",
                "name": "通富微电",
                "ticker": "002156",
                "exchange": "SZ",
                "role": "representative"
            }
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "supply_constraint_2020_2022",
        "conflicts": [],
        "notes": "A 股侧的市场映射与 001/002 的行情高度重合，难以独立切分出属于「缺芯」本身的行情区间；机制属行业景气而非主题叙事，故 proposal 为 industry_trend。"
    },
    {
        "campaign_id": "RC-2024-SEMI-FUND3",
        "rule_id": "rule_semiconductor",
        "year": 2024,
        "title": "2024 半导体自主可控「破局」：大基金三期 + 出口管制升级（设备/材料/先进制程）",
        "start_date": "2024-05-24",
        "peak_date": "2024-12-31",
        "end_date": None,
        "themes": [
            {
                "name": "电子",
                "theme_type": "industry",
                "role": "related"
            },
            {
                "name": "半导体",
                "theme_type": "concept",
                "role": "main"
            }
        ],
        "securities": [
            {
                "security_id": "SMIC",
                "name": "中芯国际",
                "ticker": "688981",
                "exchange": "SH",
                "role": "representative"
            },
            {
                "security_id": "AMEC",
                "name": "中微公司",
                "ticker": "688012",
                "exchange": "SH",
                "role": "representative"
            },
            {
                "security_id": "PIOTECH",
                "name": "拓荆科技",
                "ticker": "688072",
                "exchange": "SH",
                "role": "representative"
            },
            {
                "security_id": "HYGON",
                "name": "海光信息",
                "ticker": "688041",
                "exchange": "SH",
                "role": "representative"
            }
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "semi_localization_2019_2021",
        "conflicts": [],
        "notes": "无法排除 Beta Contamination：2024-09-24 起为全市场普涨，半导体只是其中之一；本候选的市场区间与 007 高度重叠，独立性存疑。按 historical_campaign_validation_v1.md §4.3，无法排除时保持低置信度。"
    },
    {
        "campaign_id": "RC-2015-SEMI-LEVERAGE",
        "rule_id": "rule_semiconductor",
        "year": 2015,
        "title": "2015 半导体杠杆牛：大基金一期 + 全面牛市流动性",
        "start_date": "2015-01-05",
        "peak_date": "2015-06-03",
        "end_date": "2015-12-31",
        "themes": [
            {
                "name": "电子",
                "theme_type": "industry",
                "role": "related"
            },
            {
                "name": "半导体",
                "theme_type": "concept",
                "role": "main"
            }
        ],
        "securities": [],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "liquidity_cycle_2015",
        "conflicts": [],
        "notes": "无法排除 Beta Contamination——2015 年为全面杠杆牛市，半导体板块的上涨难以与市场整体 Beta 分离；且缺少半导体行业自身的基本面证据（产能、出货、价格）。"
    },
    {
        "campaign_id": "RC-2017-GPU-MINING",
        "rule_id": "rule_semiconductor",
        "year": 2017,
        "title": "2017 显卡与矿机芯片需求：比特币价格周期外溢至半导体",
        "start_date": "2017-06-01",
        "peak_date": "2017-11-14",
        "end_date": "2018-06-30",
        "themes": [
            {
                "name": "电子",
                "theme_type": "industry",
                "role": "related"
            },
            {
                "name": "半导体",
                "theme_type": "concept",
                "role": "main"
            }
        ],
        "securities": [],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "crypto_spillover_2017",
        "conflicts": [],
        "notes": "主题边界不清：2017 年 A 股的主要映射是「区块链/数字货币」概念，而区块链概念不属本任务 scope；本包只保留与半导体（GPU、显存、芯片设计）直接相关的部分，但证据不足以支撑其作为独立半导体 Campaign。"
    },
    # ==== 高端装备（Wave R01-01）：RESEARCH_ONLY，**不进入 campaigns 表** ====
    {
        "campaign_id": "RC-2024-HIEQ-EQUIP-UPDATE",
        "rule_id": "rule_high_end_equipment",
        "year": 2024,
        "title": "大规模设备更新政策驱动的装备需求（2024-03 行动方案至 2024-07 资金加码）",
        "start_date": "2024-03-07",
        "peak_date": "2024-07-24",
        "end_date": None,
        "themes": [
            {
                "name": "高端装备",
                "theme_type": "industry",
                "role": "main"
            }
        ],
        "securities": [
            {
                "security_id": "SANY",
                "name": "三一重工",
                "ticker": "600031",
                "exchange": "上海证券交易所",
                "role": "leader"
            },
            {
                "security_id": "ZOOMLION",
                "name": "中联重科",
                "ticker": "000157",
                "exchange": "深圳证券交易所",
                "role": "second_leader"
            },
            {
                "security_id": "XCMG",
                "name": "徐工机械",
                "ticker": "000425",
                "exchange": "深圳证券交易所",
                "role": "representative"
            },
            {
                "security_id": "HENGLI",
                "name": "恒立液压",
                "ticker": "601100",
                "exchange": "上海证券交易所",
                "role": "representative"
            }
        ],
        "events": [
            {
                "event_id": "EV-RC-2024-HIEQ-EQUIP-01",
                "name": "国务院印发《推动大规模设备更新和消费品以旧换新行动方案》（国发〔2024〕7号）",
                "date": "2024-03-07",
                "event_type": "policy",
                "role": "trigger"
            },
            {
                "event_id": "EV-RC-2024-HIEQ-EQUIP-02",
                "name": "发改委、财政部印发《关于加力支持大规模设备更新和消费品以旧换新的若干措施》",
                "date": "2024-07-24",
                "event_type": "policy",
                "role": "catalyst"
            }
        ],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "hieq_equip_update_2024",
        "conflicts": [],
        "notes": "RESEARCH_ONLY（INSUFFICIENT）：市场侧证据 0 条 → Campaign Independence Gate Q1 无法验证；行业口径过宽（11 个重点行业）与 R01-03 / 电力设备重叠；政策与需求间缺少可验证传导证据；标的与 C-2016-HIEQ-CONSTR 完全重合。**不进入 campaigns**。｜R01-01 intake"
    },
    {
        "campaign_id": "RC-2024-HIEQ-HUMANOID-MASS",
        "rule_id": "rule_high_end_equipment",
        "year": 2024,
        "title": "人形机器人量产预期与国产产业链加速段（2024-09 至 2025）",
        "start_date": "2024-09-01",
        "peak_date": "2025-07-01",
        "end_date": None,
        "themes": [
            {
                "name": "高端装备",
                "theme_type": "industry",
                "role": "related"
            },
            {
                "name": "人形机器人",
                "theme_type": "concept",
                "role": "main"
            }
        ],
        "securities": [
            {
                "security_id": "LEADERDRIVE",
                "name": "绿的谐波",
                "ticker": "688017",
                "exchange": "上海证券交易所科创板",
                "role": "representative"
            },
            {
                "security_id": "KINCO",
                "name": "步科股份",
                "ticker": "688160",
                "exchange": "上海证券交易所科创板",
                "role": "representative"
            },
            {
                "security_id": "LEADSHINE",
                "name": "雷赛智能",
                "ticker": "002979",
                "exchange": "深圳证券交易所",
                "role": "follow"
            },
            {
                "security_id": "ZHAOWEI",
                "name": "兆威机电",
                "ticker": None,
                "exchange": "深圳证券交易所",
                "role": "representative"
            },
            {
                "security_id": "EFORT",
                "name": "埃夫特",
                "ticker": None,
                "exchange": "上海证券交易所科创板",
                "role": "representative"
            },
            {
                "security_id": "TOPSTAR",
                "name": "拓斯达",
                "ticker": "300607",
                "exchange": "深圳证券交易所",
                "role": "follow"
            }
        ],
        "events": [
            {
                "event_id": "EV-RC-2024-HIEQ-HUMANOID-01",
                "name": "华为具身智能创新中心运营，与 16 家企业签约",
                "date": "2024-11-15",
                "event_type": "company",
                "role": "catalyst"
            },
            {
                "event_id": "EV-RC-2024-HIEQ-HUMANOID-02",
                "name": "智元、宇树中标中国移动人形双足机器人代工服务采购项目（合计 1.24 亿元）",
                "date": "2025-07-31",
                "event_type": "company",
                "role": "trigger"
            }
        ],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "hieq_humanoid_mass_2024_2025",
        "conflicts": [],
        "notes": "RESEARCH_ONLY（INSUFFICIENT）：市场侧证据 0 条 → Q1 无法验证；E033 与 E034 实为同源（仅 1 个有效 independence_group）；start/end 均依赖回顾性来源；与 C-2023-HIEQ-HUMANOID 边界未切分（CONFLICT CF008 UNRESOLVED）。**不进入 campaigns**。｜R01-01 intake"
    },
    # ==== 金融 / 房地产（Wave R01-05）：RESEARCH_ONLY，**不进入 campaigns 表** ====
    {
        "campaign_id": "RC-2024-RE-POLICY-517",
        "rule_id": "rule_fin_realestate",
        "year": 2024,
        "title": "2024-05-17「5·17」地产新政驱动的 A 股地产脉冲行情（政策发布 ≠ 周期反转）",
        "start_date": "2024-05-17",
        "peak_date": "2024-05-17",
        "end_date": "2024-09-13",
        "themes": [
            {"name": "房地产", "theme_type": "industry", "role": "related"},
            {"name": "房地产开发", "theme_type": "industry", "role": "main"},
        ],
        "securities": [
            {"security_id": "POLY", "name": "保利发展", "ticker": "600048", "exchange": "SH", "role": "representative"},
            {"security_id": "VANKE", "name": "万科A", "ticker": "000002", "exchange": "SZ", "role": "representative"},
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "realestate_policy_cycle_2020_2023",
        "conflicts": [],
        "notes": "RESEARCH_ONLY（不进 campaigns 表）。**市场层强反向证伪**：2024-05-17「5·17」新政当日保利发展单日 +10.66%、万科A +10.02%，但至 2024-09-13 保利发展 -31.3%、万科A -29.8%，同期沪深300 -14.1%，**相对 -17.2pct / -15.7pct**（E134）；同期工商银行 +8.7%（相对 +22.8pct）。→ **政策的市场反应是一个单日脉冲，4 个月内全部回吐**。本候选的研究价值已由 Worker 定位为「**市场层证伪的教（样本）**」——「政策放松 ≠ 地产周期反转」此前只有行业数据层证据，v2 补行情后**市场层也闭合**。confidence = low 维持。｜R01-05 intake"
    },
    {
        "campaign_id": "RC-2019-RE-EASING",
        "rule_id": "rule_fin_realestate",
        "year": 2019,
        "title": "2018-10—2019-04 地产调控边际放松与信用扩张预期驱动的地产修复行情（Beta 不可分离）",
        "start_date": "2018-12-18",
        "peak_date": None,
        "end_date": "2019-04-19",
        "themes": [
            {"name": "房地产", "theme_type": "industry", "role": "related"},
            {"name": "房地产开发", "theme_type": "industry", "role": "main"},
        ],
        "securities": [
            {"security_id": "POLY", "name": "保利发展", "ticker": "600048", "exchange": "SH", "role": "representative"},
            {"security_id": "VANKE", "name": "万科A", "ticker": "000002", "exchange": "SZ", "role": "representative"},
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "realestate_policy_cycle_2020_2023",
        "conflicts": [],
        "notes": "RESEARCH_ONLY（不进 campaigns 表）。① `research_status = INSUFFICIENT` · `confidence = low`；② **市场层证伪** —— 2018-11-30 至 2019-04-19 保利发展相对沪深300 **-18.2pct**、万科A **-0.4pct**，**两个地产龙头均未跑赢基准**（E130）；而同期中信证券 **+52.3%**（相对 +22.4pct）；③ 同期卖方明确认为地方放松**不代表中央政策转向**（直接反证）；④ `exclusion X012` 已明确记录其 **NOT_A_CAMPAIGN**。★ CF009（地方调控放松是否代表中央政策转向）**保留 KEEP_BOTH**。｜R01-05 intake"
    },
    {
        "campaign_id": "RC-2020-FIN-BROKER-VOLUME",
        "rule_id": "rule_fin_realestate",
        "year": 2020,
        "title": "2020-06—07 成交量放大与资本市场改革预期驱动的券商行情（Beta 代理风险）",
        "start_date": "2020-07-02",
        "peak_date": None,
        "end_date": None,
        "themes": [
            {"name": "金融", "theme_type": "industry", "role": "related"},
            {"name": "非银金融", "theme_type": "industry", "role": "main"},
        ],
        "securities": [
            {"security_id": "CITICS", "name": "中信证券", "ticker": "600030", "exchange": "SH", "role": "representative"},
            {"security_id": "EBSEC", "name": "光大证券", "ticker": "601788", "exchange": "SH", "role": "representative"},
            {"security_id": "ZSSEC", "name": "浙商证券", "ticker": "601878", "exchange": "SH", "role": "representative"},
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "CONFLICT",
        "theme_cycle_id": "broker_risk_appetite_2020",
        "conflicts": [],
        "notes": "RESEARCH_ONLY（不进 campaigns 表）。理由（**Gate 不成立**）：① **`lifecycle` 为 `UNKNOWN`（无任何阶段）** —— **Q4 独立生命周期不成立**；② `start = 2020-07-02` 为 confidence low，包内自述「**本包仅能确认该日，不确认为真正起点**」；`peak` / `end` 均为 PHASE_WINDOW 且**无具体日期** → **Q3 持续性不成立**；③ **Q5 残差检验不成立** —— **核心反证就在证据本身**：同期报道明确写出「银行、保险、互联网金融等大金融**全线走高**」（E081），这是**典型的市场 Beta 形态**，券商只是高弹性代理；④ CF008（资本市场改革驱动 vs 成交量驱动）**保留 UNRESOLVED**。★ 与 005（2024-09）**未因都叫「券商行情」而合并** —— 两者分属不同 Theme Cycle，且 005 有 lifecycle 与一手政策锚点、009 两者皆无。★ **相对强度（+21.6pct，E131）不作为 Promote 依据** —— Beta 无法排除。｜R01-05 intake"
    },
    {
        "campaign_id": "RC-2016-RE-SHANTY",
        "rule_id": "rule_fin_realestate",
        "year": 2016,
        "title": "2015—2017 去库存与棚改货币化驱动的房地产基本面周期（Priority B 回填，A 股响应受杠杆牛污染）",
        "start_date": "2015-12-21",
        "peak_date": None,
        "end_date": None,
        "themes": [
            {"name": "房地产", "theme_type": "industry", "role": "related"},
            {"name": "房地产开发", "theme_type": "industry", "role": "main"},
        ],
        "securities": [
            {"security_id": "POLY", "name": "保利发展", "ticker": "600048", "exchange": "SH", "role": "representative"},
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "realestate_policy_cycle_2020_2023",
        "conflicts": [],
        "notes": "RESEARCH_ONLY（不进 campaigns 表）。① `INSUFFICIENT` / `low`；② **仅 2 ev / 2 IG**；③ **市场响应层完全空白** —— 2015—2016 年前复权序列存在**复权因子异常**（保利发展 2016-12-30 = 4.7254 与 2017-12-29 = 10.0604 的隐含复权因子相差约 57%，无法用分红解释），Worker 据此**不采用量化证据** → 无法建立「政策 → 行业数据 → 市场响应」三层链条的第三层；④ 同期 A 股处于 2015 年杠杆牛与股灾的极端 Beta 环境，地产板块响应与全市场不可分离。★ **未因存在政策 / 历史叙述而提升状态** ✓。｜R01-05 intake"
    },
    {
        "campaign_id": "RC-2015-FIN-LEVERAGE",
        "rule_id": "rule_fin_realestate",
        "year": 2015,
        "title": "2015 年杠杆牛市中的金融股（券商/银行）启动段（Beta 主导，建议 Observation）",
        "start_date": None,
        "peak_date": None,
        "end_date": None,
        "themes": [
            {"name": "金融", "theme_type": "industry", "role": "main"},
        ],
        "securities": [
            {"security_id": "CITICS", "name": "中信证券", "ticker": "600030", "exchange": "SH", "role": "representative"},
            {"security_id": "ICBC", "name": "工商银行", "ticker": "601398", "exchange": "SH", "role": "representative"},
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "finance_beta_2015",
        "conflicts": [],
        "notes": "RESEARCH_ONLY（不进 campaigns 表）。① `INSUFFICIENT` / `low`；② **仅 2 ev / 2 IG**；③ **`PIT = 0`** —— 全部证据为 retrospective 复盘，**无一条同期证据**；④ **无任何行情数据**（起止、峰值、板块口径全缺）；⑤ 机制本身就是「**杠杆资金驱动的市场 Beta**」，按 `historical_campaign_validation_v1.md §4.3`，**无法排除 Beta 污染时必须保持低置信度**。★ `exclusion X001` 已明确建议：**不作为独立金融 Campaign**（建议 Observation）。｜R01-05 intake"
    },
    # ==== 国防军工（Wave R01-06）：RESEARCH_ONLY，**不进入 campaigns 表** ====
    {
        "campaign_id": "RC-2019-MIL-PARADE-70",
        "rule_id": "rule_defense_military",
        "year": 2019,
        "title": "2019 年国庆 70 周年阅兵行情（事件驱动候选，资料不足）",
        "start_date": "2019-08-07",
        "peak_date": "2019-09-03",
        "end_date": None,
        "themes": [
            {"name": "国防军工", "theme_type": "industry", "role": "related"},
            {"name": "航空装备", "theme_type": "industry", "role": "main"},
        ],
        "securities": [
            {"security_id": "SWMIL", "name": "申万国防军工指数", "ticker": "801740.SI", "exchange": "申万宏源（指数编制）", "role": "representative"},
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "INSUFFICIENT",
        "theme_cycle_id": "military_parade_event_2019",
        "conflicts": [],
        "notes": "RESEARCH_ONLY（不进 campaigns 表）。**Gate 不成立**：① **Q2 = 否** —— 仅 1 个宽基指数（申万国防军工指数），**无独立代表标的组**；② **Q3 = 否** —— 持续性仅约 4 周（2019-08-07 → 2019-09-03），事件驱动型持续性不足；③ **Q4 = 否** —— **全部 3 条证据均为 2025 年发布的 retrospective 复盘材料，无任何同期一手证据**（`support_kind` 含 `retrospective_context`，已逐条填 `point_in_time_note`）；④ 与 002 的 Q1 Anti-example（同一资金池）无法排除。★ 本包自述「**不应作为已成立的历史 Campaign 使用**」→ 本裁决一致。★ **未因「国庆 70 周年阅兵」事件重大而默认形成 Campaign**。｜R01-06 intake"
    },
    {
        "campaign_id": "RC-2025-MIL-PARADE-80",
        "rule_id": "rule_defense_military",
        "year": 2025,
        "title": "2025 年抗战胜利 80 周年阅兵 / 军贸与新质战斗力主题（复合机制候选）",
        "start_date": "2025-06-24",
        "peak_date": None,
        "end_date": None,
        "themes": [
            {"name": "国防军工", "theme_type": "industry", "role": "related"},
            {"name": "航空装备", "theme_type": "industry", "role": "main"},
        ],
        "securities": [
            {"security_id": "CSIMIL", "name": "中证军工指数", "ticker": "399967.SZ", "exchange": "深圳证券交易所", "role": "representative"},
            {"security_id": "SWMIL", "name": "申万国防军工指数", "ticker": "801740.SI", "exchange": "申万宏源（指数编制）", "role": "representative"},
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "PROVISIONAL",
        "theme_cycle_id": "military_parade_event_2025",
        "conflicts": [],
        "notes": "RESEARCH_ONLY（不进 campaigns 表）。**CF007 裁决：不通过 Gate → 无需在 `theme_campaign` vs `event_driven` 之间选择（两者皆不成立）**。① **Q2 = 否** —— 仅 2 个宽基指数，**无独立代表标的组**；② **Q3 = 弱** —— 窗口约 2.5 个月；③ **Q4 = 否** —— **生命周期未闭合**：`peak` 不可考、阅兵后走向无任何可复核材料；④ **Q5 = 否** —— 去掉阅兵事件，「军贸」（无订单数据）与「十五五」（无落地证据）**均无法独立构成 Campaign**。★ **机制复合（阅兵事件 + 军贸外需 + 十五五政策预期）无法形成统一生命周期** → **不强行合并、也不为保持 Candidate 结构而机械 Promote**；本包 `why_not` 亦自述「若严格按机制必须明确的要求，可能应拆分为不同结构或降级为 OBSERVATION_ONLY」。★ **未因「2025 新结构」而机械 Promote**。★ 阅兵事件有 Tier 1 官方锚点（2025-06-24 国新办官宣、2025-08-20 阅兵准备发布会），但**市场响应证据仅 Tier 3 相对强弱描述**。｜R01-06 intake"
    },
    {
        "campaign_id": "RC-2017-MIL-MIXED-REFORM",
        "rule_id": "rule_defense_military",
        "year": 2017,
        "title": "2017 年军民融合 / 军工混改结构（Priority B 回填，生命周期未闭合）",
        "start_date": "2017-01-04",
        "peak_date": None,
        "end_date": None,
        "themes": [
            {"name": "国防军工", "theme_type": "industry", "role": "main"},
        ],
        "securities": [
            {"security_id": "SWMIL", "name": "申万国防军工指数", "ticker": "801740.SI", "exchange": "申万宏源（指数编制）", "role": "representative"},
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "PROVISIONAL",
        "theme_cycle_id": "military_mixed_reform_2017",
        "conflicts": [],
        "notes": "RESEARCH_ONLY（不进 campaigns 表）。**需补证后重新评估**。Gate：① **Q1 = 是**（政策文本驱动：2017-01-04 兵器工业集团混改指导意见 → 2017-01-22 中央军民融合发展委员会设立）；② **Q2 = 否** —— 仅 1 个宽基指数，**无独立代表标的组**；③ **Q3 = 无法判定**（2017 年 2 月之后走势不可考）；④ **Q4 = 否** —— **生命周期无法闭合**：`peak` / `end` 均不可考；⑤ **Q5 = 无法执行**。→ **多数否 / 无法判定 → 不成立**。★ **只能证明「政策存在」**（同期政策原文 + 1 月市场响应：1-09 板块集体启动、近 10 只涨停、1-20 行业排名第 2），**不能证明市场结构**（2017 年全年军工涨跌数据缺失）→ **保持 Research Only**。★ 本包自述「**没有任何证据显示 2017 年混改已转化为订单或业绩**」。★ **CF009（军民融合 vs 混改 是否同一机制）保留 UNRESOLVED**，不影响存废判定。★ 补证方向：2017 年军工板块全年 / 分月行情序列 + 混改落地公告。｜R01-06 intake"
    },
    {
        "campaign_id": "RC-2015-MIL-REFORM-BULL",
        "rule_id": "rule_defense_military",
        "year": 2015,
        "title": "2015 年军工改革 / 资产证券化行情（改革牛，Beta 不可分离）",
        "start_date": None,
        "peak_date": "2015-06-04",
        "end_date": None,
        "themes": [
            {"name": "国防军工", "theme_type": "industry", "role": "related"},
        ],
        "securities": [
            {"security_id": "CNIMIL", "name": "国证军工指数（深圳证券信息有限公司编制，50只成分股）", "ticker": None, "exchange": "深圳证券信息有限公司", "role": "representative"},
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "PROVISIONAL",
        "theme_cycle_id": "military_reform_bull_2015",
        "conflicts": [],
        "notes": "RESEARCH_ONLY（不进 campaigns 表）。**CF006 裁决：Beta 无法排除 → 保持 Research Only**。① **Q2 = 否** —— 仅 1 个指数（国证军工指数，且 `ticker` 缺失），**无独立代表标的组**；② **Q3 = 否**（启动与结束日期均不可考）；③ **Q4 = 否** —— `start` / `end` 均不可考（无法把军工的结束与全市场 Beta 的结束分离）；④ **Q5 = 无法执行**。★ 本包自述「**无法证明这是军工 Campaign 而不是市场 Beta 在军工板块的投射**」、「**没有任何证据可以把 2015 年军工涨幅与市场 Beta 分离**」、「**若 ThreeC Agent 判定 Beta 无法排除，应降级为 OBSERVATION_ONLY**」→ **本裁决采纳降级**。★ **未因 2015 是历史回填空缺年份而降低标准**；按 `historical_campaign_validation_v1.md §4.3`，无法排除 Beta 污染时必须保持低置信度。★ `peak = 2015-06-04`（国证军工指数年初至该日累计 **+117.36%**，中国新闻网 T2）—— **是报道口径的区间终点，不是严格意义的行情峰值日**，且含大量 Beta。｜R01-06 intake"
    },
    {
        "campaign_id": "RC-2024-MIL-COMMERCIAL-SPACE",
        "rule_id": "rule_defense_military",
        "year": 2024,
        "title": "2024–2025 商业航天 / 卫星互联网（跨族边界候选，族属未定）",
        "start_date": "2024-08-06",
        "peak_date": None,
        "end_date": None,
        "themes": [
            {"name": "航天装备", "theme_type": "industry", "role": "related"},
        ],
        "securities": [
            {"security_id": "CHINASAT", "name": "中国卫星", "ticker": "600118.SH", "exchange": "上海证券交易所", "role": "representative"},
            {"security_id": "ZTROCKET", "name": "中天火箭", "ticker": "003009.SZ", "exchange": "深圳证券交易所", "role": "follow"},
            {"security_id": "HONGDA", "name": "宏达电子", "ticker": "300726.SZ", "exchange": "深圳证券交易所", "role": "follow"},
        ],
        "events": [],
        "signals": [],
        "early_signal": None,
        "theme_formation": None,
        "broad_confirmation": None,
        "research_status": "PROVISIONAL",
        "theme_cycle_id": "commercial_space_2024_2025",
        "conflicts": [],
        "notes": "RESEARCH_ONLY（不进 campaigns 表）。**CF004 裁决：族属 UNRESOLVED → 不进入任何族的 canonical**。① **族属未定**：CMTR v1 对 `商业航天` / `卫星互联网` / `卫星导航` 均为 **UNRESOLVED_NAME**（taxonomy 中不存在）；只有 `航天装备` 解析到 `国防军工`。② **机制不是国防采购**（本包自述「驱动来自产业规划与商业需求，不是军费或军品订单」）；核心催化主管部门为**工信部 / 国家航天局**，主题是商业航天 / 卫星通信产业发展。③ **`X008` 已将「卫星互联网的通信属性」列为 OUT_OF_SCOPE**（任务书 `excluded_scope` 同）→ **继续遵守**。④ **Q4 = 否** —— 生命周期未闭合：`peak` / `end` 均不可考，2025 年末仍活跃。⑤ **Q2 = 是**（独立代表标的组）、**Q1 = 是**、**Q3 = 是**（约 17 个月、多次催化）→ 3/5 成立 + 族属未定 + 生命周期未闭合 → **不进入 canonical**。★ **未因当前 root 是「国防军工」就默认纳入**；**未扩展 taxonomy**。★ 与信息通信族 / R01-02 的 cross-task dedupe 仍待办（`N004` POSSIBLE_DUPLICATE）。｜R01-06 intake"
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
    # ---- 电力设备（Wave 1A；Peak 口径同 v1.1 §6，使用 Campaign 自身代表标的）----
    # Peak Window 由三个代表标的自身高点界定：
    #   阳光电源 2021-10-27 / 隆基绿能 2021-11-01 / 金风科技 2021-11-04。
    "C-2020-POWER-NE": [
        {"stage": "EARLY_SIGNAL", "start": "2020-09-22", "end": "2020-09-22", "precision": "EXACT_DATE"},
        {"stage": "THEME_FORMING", "start": "2020-12-12", "end": "2020-12-12", "precision": "EXACT_DATE"},
        {"stage": "BROAD_CONFIRMATION", "start": "2021-09-08", "end": "2021-09-08", "precision": "EXACT_DATE"},
        {"stage": "MAIN_RISE", "start": "2020-12-12", "end": "2021-10-26", "precision": "PHASE_WINDOW"},
        {"stage": "PEAK", "start": "2021-10-27", "end": "2021-11-04", "precision": "DATE_WINDOW"},
        {"stage": "RETRACEMENT", "start": "2021-11-05", "end": "2022-04-26", "precision": "PHASE_WINDOW"},
        {"stage": "SECONDARY", "start": "2022-04-27", "end": "2022-08-23", "precision": "PHASE_WINDOW"},
        {"stage": "DECLINING", "start": "2022-08-24", "end": "2022-12-30", "precision": "PHASE_WINDOW"},
        {"stage": "MAIN_END", "start": "2022-12-30", "end": "2022-12-30", "precision": "EXACT_DATE"},
    ],
    # Peak Window 由三个代表标的自身高点界定：
    #   许继电气 2024-07-09 / 国电南瑞 2024-10-08 / 平高电气 2024-10-14。
    # RETRACEMENT = 2022-01 政策信号披露后的「利好兑现」回撤（三标的 2022-01-18/19 同步见顶）。
    "C-2022-POWER-GRID": [
        {"stage": "EARLY_SIGNAL", "start": "2022-01-10", "end": "2022-01-10", "precision": "EXACT_DATE"},
        {"stage": "THEME_FORMING", "start": "2022-01-16", "end": "2022-01-16", "precision": "EXACT_DATE"},
        {"stage": "RETRACEMENT", "start": "2022-01-20", "end": "2022-04-26", "precision": "PHASE_WINDOW"},
        {"stage": "BROAD_CONFIRMATION", "start": "2022-08-03", "end": "2022-08-03", "precision": "EXACT_DATE"},
        {"stage": "MAIN_RISE", "start": "2023-01-01", "end": "2024-07-08", "precision": "PHASE_WINDOW"},
        {"stage": "PEAK", "start": "2024-07-09", "end": "2024-10-14", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2024-10-15", "end": "2025-12-31", "precision": "PHASE_WINDOW"},
        {"stage": "MAIN_END", "start": "2025-12-31", "end": "2025-12-31", "precision": "EXACT_DATE"},
    ],
    # ---- 信息通信（Wave 1B；Peak 口径同 v1.1 §6，使用 Campaign 自身代表标的）----
    # Peak Window 由代表标的自身高点界定（分批见顶）：
    #   中际旭创 2020-02-24 / 中兴通讯 2020-02-25 / 烽火通信 2020-03-12 /
    #   新易盛 2020-07-14 / 天孚通信 2020-08-04。
    # 环节错位记入 research_notes，不另立 Cycle。
    "C-2019-COMM-5G": [
        {"stage": "EARLY_SIGNAL", "start": "2019-06-06", "end": "2019-06-06", "precision": "EXACT_DATE"},
        {"stage": "THEME_FORMING", "start": "2019-10-31", "end": "2019-10-31", "precision": "EXACT_DATE"},
        {"stage": "BROAD_CONFIRMATION", "start": "2020-03-04", "end": "2020-03-04", "precision": "EXACT_DATE"},
        {"stage": "MAIN_RISE", "start": "2019-10-31", "end": "2020-02-23", "precision": "PHASE_WINDOW"},
        {"stage": "PEAK", "start": "2020-02-24", "end": "2020-08-04", "precision": "DATE_WINDOW"},
        {"stage": "RETRACEMENT", "start": "2020-08-05", "end": "2021-03-18", "precision": "PHASE_WINDOW"},
        {"stage": "SECONDARY", "start": "2021-03-19", "end": "2021-12-31", "precision": "PHASE_WINDOW"},
        {"stage": "DECLINING", "start": "2022-01-01", "end": "2022-10-11", "precision": "PHASE_WINDOW"},
        {"stage": "MAIN_END", "start": "2022-10-11", "end": "2022-10-11", "precision": "EXACT_DATE"},
    ],
    # Peak 未确认（至行情窗口末端仍在上行）：PEAK 取代表标的 2025-12-22~12-25 的区间高点。
    # 2024-10-08 → 2025-04-08 为一次显著回撤（中际旭创 -62%），故 MAIN_RISE 出现两段
    # （已验证：所有消费端均用 .find()/取最早一段，重复阶段不破坏语义）。
    "C-2023-COMM-OPTICAL": [
        {"stage": "EARLY_SIGNAL", "start": "2023-03-21", "end": "2023-03-21", "precision": "EXACT_DATE"},
        {"stage": "THEME_FORMING", "start": "2023-05-24", "end": "2023-05-24", "precision": "EXACT_DATE"},
        {"stage": "BROAD_CONFIRMATION", "start": "2023-08-28", "end": "2023-08-28", "precision": "EXACT_DATE"},
        {"stage": "MAIN_RISE", "start": "2023-08-28", "end": "2024-10-07", "precision": "PHASE_WINDOW"},
        {"stage": "RETRACEMENT", "start": "2024-10-08", "end": "2025-04-08", "precision": "PHASE_WINDOW"},
        {"stage": "MAIN_RISE", "start": "2025-04-09", "end": "2025-12-18", "precision": "PHASE_WINDOW"},
        {"stage": "PEAK", "start": "2025-12-22", "end": "2025-12-25", "precision": "DATE_WINDOW"},
    ],
    # ---- 高端装备（Wave R01-01）----
    # UNKNOWN 阶段不入 export lifecycle（无起止边界）；PEAK 由 campaigns.peak_date 承载。
    "C-2016-HIEQ-CONSTR": [
        {"stage": "MAIN_RISE", "start": "2016-08-01", "end": "2021-03-31", "precision": "DATE_WINDOW"},
        {"stage": "PEAK", "start": "2021-03-01", "end": "2021-04-30", "precision": "DATE_WINDOW"},
        {"stage": "RETRACEMENT", "start": "2021-05-01", "end": "2021-12-31", "precision": "PHASE_WINDOW"},
    ],
    "C-2018-HIEQ-ROBOT-DOWN": [
        {"stage": "DECLINING", "start": "2018-09-30", "end": "2019-09-30", "precision": "PHASE_WINDOW"},
        {"stage": "SECONDARY", "start": "2019-10-01", "end": "2019-12-31", "precision": "PHASE_WINDOW"},
    ],
    "C-2020-HIEQ-AUTOMATION": [
        {"stage": "MAIN_RISE", "start": "2020-04-01", "end": "2021-06-30", "precision": "PHASE_WINDOW"},
        {"stage": "PEAK", "start": "2021-07-01", "end": "2021-09-30", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2021-10-01", "end": "2022-12-31", "precision": "PHASE_WINDOW"},
    ],
    "C-2023-HIEQ-ROBOT-PLUS": [
        {"stage": "MAIN_RISE", "start": "2023-01-19", "end": "2023-02-03", "precision": "DATE_WINDOW"},
    ],
    "C-2023-HIEQ-HUMANOID": [
        {"stage": "MAIN_RISE", "start": "2023-08-29", "end": "2023-10-31", "precision": "PHASE_WINDOW"},
        {"stage": "PEAK", "start": "2023-11-01", "end": "2023-12-31", "precision": "DATE_WINDOW"},
    ],

    # ---- 半导体 / 电子（Wave R01-02）：lifecycle 与 canonical `campaign_phases` 一致 ----
    "C-2019-SEMI-LOCALIZATION": [
        {"stage": "MAIN_RISE", "start": "2019-05-16", "end": "2020-07-14", "precision": "DATE_WINDOW"},
        {"stage": "RETRACEMENT", "start": "2020-07-15", "end": "2020-09-30", "precision": "DATE_WINDOW"},
    ],
    "C-2020-SEMI-EQUIPMENT": [
        {"stage": "MAIN_RISE", "start": "2021-04-01", "end": "2021-07-30", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2021-08-02", "end": "2021-09-30", "precision": "DATE_WINDOW"},
    ],
    "C-2020-PANEL-CYCLE": [
        {"stage": "MAIN_RISE", "start": "2020-06-01", "end": "2021-07-31", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2021-08-01", "end": "2021-08-31", "precision": "DATE_WINDOW"},
    ],
    "C-2019-CONSUMER-TWS": [
        {"stage": "MAIN_RISE", "start": "2019-01-04", "end": "2020-07-14", "precision": "DATE_WINDOW"},
        {"stage": "SECONDARY", "start": "2020-07-15", "end": "2020-11-09", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2020-11-10", "end": "2021-03-31", "precision": "DATE_WINDOW"},
    ],
    "C-2023-AI-COMPUTE-SEMI": [
        {"stage": "MAIN_RISE", "start": "2023-01-30", "end": "2023-04-10", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2023-06-21", "end": "2023-08-25", "precision": "DATE_WINDOW"},
    ],
    "C-2024-SEMI-MEMORY": [
        {"stage": "MAIN_RISE", "start": "2025-07-01", "end": "2025-10-31", "precision": "DATE_WINDOW"},
    ],
    "C-2022-SEMI-DOWNTURN": [
        {"stage": "DECLINING", "start": "2022-01-04", "end": "2022-10-12", "precision": "DATE_WINDOW"},
        {"stage": "SECONDARY", "start": "2022-06-01", "end": "2022-08-31", "precision": "DATE_WINDOW"},
    ],
    "C-2016-PANEL-CYCLE": [
        {"stage": "MAIN_RISE", "start": "2016-02-01", "end": "2017-01-31", "precision": "DATE_WINDOW"},
    ],

    # ---- 资源 / 有色 / 化工（Wave R01-03）：lifecycle 与 canonical `campaign_phases` 一致 ----
    "C-2020-RES-NONFERROUS": [
        {"stage": "MAIN_RISE", "start": "2020-04-01", "end": "2021-05-10", "precision": "DATE_WINDOW"},
    ],
    "C-2020-RES-LITHIUM": [
        {"stage": "MAIN_RISE", "start": "2020-10-30", "end": "2021-09-13", "precision": "DATE_WINDOW"},
    ],
    "C-2020-RES-RAREEARTH": [
        {"stage": "MAIN_RISE", "start": "2020-05-01", "end": "2021-10-01", "precision": "DATE_WINDOW"},
    ],
    "C-2021-RES-CHEM-DUALCTRL": [
        {"stage": "MAIN_RISE", "start": "2021-08-12", "end": "2021-09-30", "precision": "DATE_WINDOW"},
    ],
    "C-2019-RES-DYE-SHOCK": [
        {"stage": "MAIN_RISE", "start": "2019-03-21", "end": "2019-04-03", "precision": "DATE_WINDOW"},
    ],
    "C-2024-RES-GOLD-CB": [
        {"stage": "MAIN_RISE", "start": "2024-02-01", "end": "2025-12-26", "precision": "DATE_WINDOW"},
    ],

    # ---- 消费（Wave R01-04）：lifecycle 与 canonical `campaign_phases` 一致 ----
    "C-2016-CONS-BAIJIU-UPGRADE": [
        {"stage": "MAIN_RISE", "start": "2016-06-01", "end": "2017-12-31", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2018-09-01", "end": "2018-12-31", "precision": "DATE_WINDOW"},
    ],
    "C-2019-CONS-BAIJIU-CORE": [
        {"stage": "MAIN_RISE", "start": "2019-03-01", "end": "2020-12-31", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2021-02-18", "end": "2021-12-31", "precision": "DATE_WINDOW"},
    ],
    "C-2020-CONS-DUTYFREE": [
        {"stage": "MAIN_RISE", "start": "2020-06-01", "end": "2021-02-18", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2021-07-01", "end": "2022-12-31", "precision": "DATE_WINDOW"},
    ],
    "C-2022-CONS-SERVICE-REBOUND": [
        {"stage": "MAIN_RISE", "start": "2022-12-07", "end": "2023-01-31", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2023-05-01", "end": "2023-06-30", "precision": "DATE_WINDOW"},
    ],
    "C-2018-CONS-HOG-AFRICAN": [
        {"stage": "MAIN_RISE", "start": "2019-01-01", "end": "2019-12-31", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2021-01-01", "end": "2021-12-31", "precision": "DATE_WINDOW"},
    ],
    "C-2021-CONS-HOG-REVERSAL": [
        {"stage": "MAIN_RISE", "start": "2022-04-01", "end": "2022-07-31", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2022-09-08", "end": "2022-12-31", "precision": "DATE_WINDOW"},
    ],
    "C-2020-CONS-WHITE-GOODS": [
        {"stage": "MAIN_RISE", "start": "2020-06-01", "end": "2021-02-28", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2021-07-01", "end": "2021-12-31", "precision": "DATE_WINDOW"},
    ],
    "C-2019-CONS-AESTHETICS": [
        {"stage": "MAIN_RISE", "start": "2020-01-01", "end": "2021-06-30", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2021-07-26", "end": "2022-12-31", "precision": "DATE_WINDOW"},
    ],
    "C-2020-CONS-BEAUTY-CN": [
        {"stage": "MAIN_RISE", "start": "2020-06-29", "end": "2021-06-30", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2022-01-01", "end": "2022-12-31", "precision": "DATE_WINDOW"},
    ],
    "C-2024-CONS-TRADE-IN": [
        {"stage": "MAIN_RISE", "start": "2024-08-24", "end": "2024-10-08", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2025-07-01", "end": "2025-12-31", "precision": "DATE_WINDOW"},
    ],
    "C-2023-CONS-VALUE-RETAIL": [
        {"stage": "MAIN_RISE", "start": "2023-01-01", "end": "2024-12-31", "precision": "DATE_WINDOW"},
    ],

    # ---- 金融 / 房地产（Wave R01-05）：lifecycle 与 canonical `campaign_phases` 一致 ----
    # ★ 007 / 010 无 peak / end（结构可能仍在延续）→ 不制造完整日线生命周期；
    #   006 的 PEAK / END 段为 UNKNOWN（未闭合）→ 不写入。
    "C-2022-RE-POLICY-THREE": [
        {"stage": "MAIN_RISE", "start": "2022-11-08", "end": "2022-11-29", "precision": "DATE_WINDOW"},
        {"stage": "DECLINING", "start": "2023-01-01", "end": "2023-02-28", "precision": "PHASE_WINDOW"},
    ],
    "C-2020-RE-DEBT-RISK": [
        {"stage": "DECLINING", "start": "2020-08-20", "end": "2021-12-31", "precision": "DATE_WINDOW"},
    ],
    "C-2024-FIN-BROKER-POLICY": [
        {"stage": "MAIN_RISE", "start": "2024-09-24", "end": "2024-10-08", "precision": "DATE_WINDOW"},
    ],
    "C-2023-FIN-SOE-VALUATION": [
        {"stage": "MAIN_RISE", "start": "2023-04-01", "end": "2023-05-11", "precision": "PHASE_WINDOW"},
    ],
    "C-2024-FIN-BANK-DIVIDEND": [
        {"stage": "MAIN_RISE", "start": "2024-01-01", "end": "2024-12-31", "precision": "PHASE_WINDOW"},
        {"stage": "SECONDARY", "start": "2025-01-01", "end": "2025-09-19", "precision": "PHASE_WINDOW"},
    ],
    "C-2020-FIN-BANK-CREDIT": [
        {"stage": "MAIN_RISE", "start": "2020-10-30", "end": "2021-03-31", "precision": "PHASE_WINDOW"},
    ],
    "C-2025-FIN-INSURANCE": [
        {"stage": "MAIN_RISE", "start": "2025-01-01", "end": "2025-12-31", "precision": "PHASE_WINDOW"},
    ],

    # ---- 国防军工（Wave R01-06）：lifecycle 与 canonical `campaign_phases` 一致 ----
    # ★ 001 含 2021-01-08→2021-05-10 的 -32% 内部回撤（RETRACEMENT）；2020-08 中旬~12 月数据缺失，未填充。
    # ★ 002 的 MAIN_RISE 结束日期不可考（end = null，不强行取值）；`peak` 缺失 → 无 PEAK 段。
    "C-2020-MIL-EQUIP-ORDER": [
        {"stage": "MAIN_RISE", "start": "2020-06-25", "end": "2020-08-10", "precision": "DATE_WINDOW"},
        {"stage": "RETRACEMENT", "start": "2021-01-08", "end": "2021-05-10", "precision": "DATE_WINDOW"},
        {"stage": "MAIN_RISE", "start": "2021-05-11", "end": "2021-08-24", "precision": "DATE_WINDOW"},
        {"stage": "RETRACEMENT", "start": "2021-08-25", "end": "2021-10-13", "precision": "DATE_WINDOW"},
        {"stage": "SECONDARY", "start": "2021-10-14", "end": "2021-11-30", "precision": "DATE_WINDOW"},
        {"stage": "PEAK", "start": "2021-12-01", "end": "2021-12-01", "precision": "EXACT_DATE"},
        {"stage": "DECLINING", "start": "2021-12-02", "end": "2022-12-31", "precision": "PHASE_WINDOW"},
    ],
    "C-2019-MIL-GROUP-RESTRUCTURE": [
        {"stage": "MAIN_RISE", "start": "2019-07-02", "end": None, "precision": "PHASE_WINDOW"},
        {"stage": "SECONDARY", "start": "2019-10-25", "end": "2019-10-28", "precision": "EXACT_DATE"},
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
    # ---- 高端装备（Wave R01-01，Research Candidate）----
    "RC-2024-HIEQ-EQUIP-UPDATE": [
        {"stage": "MAIN_RISE", "start": "2024-03-07", "end": "2024-07-23", "precision": "PHASE_WINDOW"},
        {"stage": "PEAK", "start": "2024-07-24", "end": "2024-07-26", "precision": "PHASE_WINDOW"},
    ],
    "RC-2024-HIEQ-HUMANOID-MASS": [
        {"stage": "MAIN_RISE", "start": "2025-01-01", "end": "2025-06-30", "precision": "PHASE_WINDOW"},
        {"stage": "PEAK", "start": "2025-07-01", "end": "2025-09-05", "precision": "PHASE_WINDOW"},
    ],
    # ---- 国防军工（Wave R01-06，Research Candidate）----
    # ★ 结束日期不可考处一律 end=null，不制造精确日期（用户明确要求）。
    "RC-2019-MIL-PARADE-70": [
        {"stage": "MAIN_RISE", "start": "2019-08-07", "end": "2019-09-03", "precision": "EXACT_DATE"},
        {"stage": "PEAK", "start": "2019-09-03", "end": "2019-09-03", "precision": "EXACT_DATE"},
        {"stage": "DECLINING", "start": "2019-09-04", "end": None, "precision": "PHASE_WINDOW"},
    ],
    "RC-2025-MIL-PARADE-80": [
        {"stage": "MAIN_RISE", "start": "2025-06-24", "end": None, "precision": "PHASE_WINDOW"},
    ],
    "RC-2017-MIL-MIXED-REFORM": [
        {"stage": "MAIN_RISE", "start": "2017-01-09", "end": None, "precision": "PHASE_WINDOW"},
    ],
    "RC-2015-MIL-REFORM-BULL": [
        {"stage": "MAIN_RISE", "start": None, "end": "2015-06-04", "precision": "PHASE_WINDOW"},
        {"stage": "DECLINING", "start": "2015-06-05", "end": None, "precision": "PHASE_WINDOW"},
    ],
    "RC-2024-MIL-COMMERCIAL-SPACE": [
        {"stage": "MAIN_RISE", "start": "2024-08-06", "end": None, "precision": "PHASE_WINDOW"},
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
    # ---- 电力设备（Wave 1A）----
    "C-2020-POWER-NE": {
        "start": ["双碳目标宣布：力争 2030 年前碳达峰、2060 年前碳中和（EV-PWR-03, 2020-09-22）",
                  "平价上网 Setup：2018 年 531 新政出清后，2019-01-07 平价上网通知（发改能源〔2019〕19 号）"
                  "确立无补贴发展路径（EV-PWR-02，prior）"],
        "accelerator": ["气候雄心峰会：2030 年风电、太阳能发电总装机 12 亿千瓦以上（EV-PWR-04, 2020-12-12）"
                        "→ 首个可量化装机目标",
                        "整县屋顶分布式光伏试点名单 676 县公布（EV-PWR-05, 2021-09-08）",
                        "2021 年新增光伏并网装机约 5300 万千瓦、分布式占比首次过半（E-PWR-04）"],
        "turning": ["硅料价格暴涨挤压中下游利润（2021 年硅料价格年内涨超 2 倍）",
                    "高估值抱团瓦解 + 产能过剩预期",
                    "代表标的分批见顶：阳光电源 2021-10-27 / 隆基绿能 2021-11-01 / 金风科技 2021-11-04"],
        "ending": ["2021-11 见顶后主跌至 2022-04-26（隆基 39.68 / 阳光 37.65 / 金风 9.45 同步低点，含大盘 β）",
                   "2022-04-27~2022-08-23 阳光电源次级反弹（2022-08-23 100.12），隆基未同步",
                   "上游硅料环节延后至 2022-07-05 见顶（特变电工-新特能源），属同 Cycle 内环节错位",
                   "2022-12-30 为本地行情窗口末端，Theme Cycle End 未确认"],
    },
    "C-2022-POWER-GRID": {
        "start": ["特高压核准提速：2022 年规划项目有望全部核准（EV 相关，2022-01-10 报道）",
                  "国家电网 2022 年度工作会议：电网投资计划 5012 亿元（EV-PWR-06, 2022-01-16）"
                  "→ 电网投资由 2019 年 4473 亿 / 2021 年 4882 亿转为上行"],
        "accelerator": ["国网披露年内再开工「四交四直」8 项特高压、在建项目投资破万亿、"
                        "全年电网投资约 5300 亿元创历史最高（EV-PWR-07, 2022-08-03）",
                        "首个「沙戈荒」外送特高压（宁夏—湖南 ±800 千伏）开工（EV-PWR-08, 2023-06-11）",
                        "电网工程投资连续高增：2023 年 5275 亿元（+5.4%）、2024 年 6083 亿元（+15.3%）",
                        "国网 2024 年投资首超 6000 亿元，累计建成「22 交 16 直」38 项特高压（EV-PWR-09, 2025-02-12）"],
        "turning": ["2022-01 政策信号披露后即「利好兑现」：三标的同步见顶（国电南瑞/许继电气 01-19、"
                    "平高电气 01-18）→ 至 2022-04-25/26 同步见底",
                    "2024-07~10 批量见顶：许继电气 07-09 / 国电南瑞 10-08 / 平高电气 10-14"],
        "ending": ["2024-10 后特高压国内标的回落（2025 年：国电南瑞 -5.0%、平高电气 -2.8%、许继电气 +1.7%）",
                   "★ 环节错位：出海暴露较高的思源电气（2025-12-26 160.30，+115.0%）与"
                   "特变电工（2025-11-07 26.14，+86.0%）延后至 2025 年见顶，未另立 Cycle",
                   "★ 特变电工 2022-07-05 高点（21.97）由子公司新特能源（多晶硅）驱动，存在混淆，未据此判定 Peak",
                   "2025-12-31 为本地行情窗口末端，Theme Cycle End 未确认"],
    },
    # ---- 信息通信（Wave 1B）----
    "C-2019-COMM-5G": {
        "start": ["5G 商用牌照发放（EV-COMM-02, 2019-06-06）→ 中国进入 5G 商用元年",
                  "5G 商用启动仪式、三大运营商发布 5G 套餐（EV-COMM-03, 2019-10-31）",
                  "Setup：2018-04-16 美国商务部对中兴通讯激活拒绝令（EV-COMM-01，prior）"
                  "→ 2018 年板块深跌形成低基数（中兴 -49.0%）"],
        "accelerator": ["中央政治局会议（2020-02-21）提出推动 5G 网络等加快发展；"
                        "工信部加快推进 5G 发展会议（2020-02-22）（EV-COMM-04）",
                        "中国联通宣布力争三季度完成全国 25 万基站建设、较原计划提前一个季度（2020-02-23）",
                        "中央政治局常务委员会：加快 5G 网络、数据中心等新型基础设施建设进度（EV-COMM-05, 2020-03-04）",
                        "2020 年固定资产投资 4072 亿元（+11%），新建 5G 基站超 60 万个（E-COMM-07）"],
        "turning": ["代表标的分批见顶：中际旭创 2020-02-24 / 中兴通讯 2020-02-25 / 烽火通信 2020-03-12（Peak Window）",
                    "2021 年上半年三大运营商 5G 资本开支均下滑（中国联通 -45%）（E-COMM-09）",
                    "2021 年电信固定资产投资 4058 亿元，与上年基本持平 → 资本开支见顶（E-COMM-08）"],
        "ending": ["2021-2022 板块持续走弱：中兴 -23.4%（2022）、烽火 -28.2%、中际旭创 -38.2%",
                   "代表标的 2022-10-10/11 同步见底（中兴 18.41 / 烽火 11.65 / 中际旭创 15.88 / 新易盛 6.33）"
                   "→ 本轮 Cycle 出清完成",
                   "★ 环节错位：新易盛（数通光模块）延后至 2020-07-14 见顶，"
                   "主因海外云厂商资本开支与 400G 放量节奏滞后于国内 5G 建设，未另立 Cycle"],
    },
    "C-2023-COMM-OPTICAL": {
        "start": ["NVIDIA GTC 2023 主题演讲（EV-COMM-07, 2023-03-21）→ AI 算力叙事启动；"
                  "A 股光模块次日爆发（中际旭创 2023-03-22 +21.97%）",
                  "context：「东数西算」全面启动（EV-COMM-06, 2022-02-17，prior）"],
        "accelerator": ["NVIDIA FY2024 Q1 财报：数据中心营收创纪录 42.8 亿美元，Q2 指引 110 亿美元"
                        "（较分析师预期高 53.2%）（EV-COMM-08, 2023-05-24）→ 全球 AI 算力资本开支财务确认",
                        "中际旭创 2023 半年报：下半年 800G 光模块出货量明显增长（EV-COMM-09, 2023-08-28）",
                        "中际旭创 2023 年报：营收 107.18 亿元（+11.16%），2024Q1 净利润超 10 亿元"
                        "（EV-COMM-10, 2024-04-21）→ 800G 放量在报表端确认",
                        "2025 年 1.6T 与 NPO/CPO 结构迁移预期（速率代际升级延续）"],
        "turning": ["2024-10-08 代表标的同步出现阶段高点后回撤（中际旭创 183.93 → 2025-04-08 70.09，约 -62%）",
                    "★ 该回撤后板块于 2025-04-09 起重启上行并创新高 → 属同一 Cycle 内的回撤，非 Cycle 结束"],
        "ending": ["unknown（至本地行情窗口末端仍在上行：中际旭创 2025-12-25 达 638.80、"
                   "新易盛 2025-12-22 达 329.99）",
                   "★ 通信设备（中兴通讯 / 烽火通信）2023-2025 亦受益于算力网络建设"
                   "（中兴 2024 +64.8%、烽火 2025 +79.9%），但主驱动仍含运营商侧因素，"
                   "本轮不作为本 Cycle 代表标的"],
    },
    # ---- 高端装备（Wave R01-01）：drivers 原样来自 R01-01 intake（四问），未改写 ----
    "C-2016-HIEQ-CONSTR": {
        "start": [
            "设备更新周期：2009-2012 年间销售的工程机械进入更新替换窗口（一手机制表述见券商研报）",
            "「十三五」基建项目开工带来的新增需求",
            "北方环保核查推进，排放不达标的「国二」挖掘机面临施工限制与强制淘汰",
            "房地产与基建投资增长、海外需求复苏",
        ],
        "accelerator": [
            "国产替代加速：三一挖机市占率由 2009 年 6.5% 提升至 2017 年 22.4%，超越卡特、小松、日立、神钢、斗山等外资品牌",
            "2021Q1 代表公司业绩翻倍（三一、中联、恒立净利润同比增长），形成业绩与股价的正反馈",
            "出口放量：2021 年出口 6.84 万台、同比 +97%，对冲内需下滑并延缓总量数据的拐点显现",
        ],
        "turning": [
            "内需端先行见顶：2021 年国内销量 27.44 万台、同比 -6.32%（总量 +4.63% 由出口贡献），说明转折点先出现在内需而非总量",
            "需求端前置透支：基建与地产投资增速前高后低、专项债发行不及预期",
            "成本端两头承压：原材料与运费上涨压缩盈利",
            "代表资产股价领先基本面见顶：三一与恒立股价 2021 年 1 月下旬已露疲态，早于 3 月的产业销量峰值",
        ],
        "ending": [
            "销量增速连续三季负增长（Q2 -4.8% → Q3 -16% → Q4 -30.4%），2021 年 12 月创下年内国内销量「九连降」",
            "业绩兑现转负：三一重工 2021Q2/Q3 归母净利润分别同比 -28.56%、-35.31%",
            "股价大幅回撤：三一至 2021-11-19 较年内高点下跌近 60%",
            "本包未能确认该周期的 ENDED 时点，出口对冲使总量数据迟迟未出现断崖，故 ending 一栏仅记录「上行段终止的确认信号」，不主张周期已结束",
        ],
    },
    "C-2018-HIEQ-ROBOT-DOWN": {
        "start": [
            "下游需求端收缩：汽车行业增速放缓是中国机器人行业增速放缓的主要原因（业内公开表述，2019 年世界机器人大会）；2019 年中国汽车产量与销量同比分别 -7.5%、-8.2%，降幅较 2018 年分别扩大 4.2 和 5.4 个百分点",
            "制造业固定资产投资增速由 2018 年 9.5% 下滑至 2019 年 1-4 月的 2.5%",
            "工业机器人市场本身的高基数：2018 年销量 154032 台、占全球 36.5%，但同比已 -1.4%，为 2010 年以来首次负增长",
        ],
        "accelerator": [
            "负增长持续时长本身强化了悲观预期：连续 13 个月负增长使「周期性调整」的叙事在 2019 年持续",
            "业绩传导：新松机器人、埃斯顿、华中数控等上市公司业绩不乐观，产业下行进入财务验证阶段",
            "进口同步收缩：2019 年中国机器人进口数量 60701 台、比上年减少 39401 台",
            "日本工业机器人出口（按金额）2019 年占比 69.2%，可交叉印证全球需求（含中国）走弱",
        ],
        "turning": [
            "2019 年 10 月单月产量同比转正（+1.7%）、11 月 +4.3%，连续 13 个月的负增长序列被打破",
            "制造业固定资产投资在 2019 年下半年边际企稳（本包未取得该指标 2019 年下半年的逐月序列，此项为待验证的机制线索）",
        ],
        "ending": [
            "2019 全年累计产量同比 -6.1%、完成 199050 台，作为该下行周期的完整年度记录收尾",
            "2020 年产量转为 237068 台、同比 +19.1%（近三年最高增速），确认下行段已结束",
            "2020 年 2 月疫情低点（累计同比 -19.4%）→ 3 月单月转正 → 4 月累计转正 → 全年 +19.1%，形成 V 型结构",
        ],
    },
    "C-2020-HIEQ-AUTOMATION": {
        "start": [
            "疫情后制造业资本开支回补：2020 年 2 月产量累计同比 -19.4% 为疫情低点，3 月单月转正 +12.9%、4 月累计转正 +4%，形成 V 型反弹",
            "自动化渗透率提升（机器换人）：2015-2019 年六轴机器人国产销量由不到 8000 台提升至近 2.4 万台、CAGR 33.8%，国产市占率由 16.4% 升至 24.1%",
            "制造业固定资产投资回升（券商月报明确以此为自动化设备复苏的前置条件）",
            "出口需求在 2020 年下半年走强，带动制造业整体开工与设备投资",
        ],
        "accelerator": [
            "单月产量增速连续突破：5 月 +16.9% → 6 月 +29.2% → 7 月 +19.4%，增速中枢抬升形成正反馈",
            "市场关注度快速聚集：2020 年 7 月机械设备指数上涨 12.56%，机器人板块月涨幅 18.2%、年初至今 48.1%，位居行业前三",
            "代表资产创新高：汇川技术股价 2020-07-16 创历史新高；埃斯顿月涨幅 35.0%、年初至今 43.4%",
            "国产替代叙事：国产六轴机器人销量与市占率双升，形成「进口替代 + 渗透率提升」的双重成长逻辑",
        ],
        "turning": [
            "上游通胀与出口新增订单下滑（一手公司披露的转折归因）",
            "制造业需求疲软导致通用自动化景气持续下行，2021 年 7 月为下行起点",
            "2022 年 3-4 月经济下行加速行业下滑并进入筑底阶段",
            "盈利质量隐忧在行业内已现：2020 年规上工业机器人制造企业营业收入 +6.0% 而利润总额同比 -26.9%，呈量增价跌",
        ],
        "ending": [
            "2022 年上半年国内产量 20.2 万台、同比 -11% 以上；全年 44.3 万套、同比 -4.8%",
            "公司业绩转亏：新松机器人、哈工智能、新时达、埃夫特等 2022 年上半亏损（疫情封控与原材料涨价为主要原因）",
            "2023 年 1-2 月产量 6.2 万套、同比 -19.2%，负增长延续至政策介入前夜",
            "本包不主张该 Campaign 已 ENDED，故 ending 一栏记录「上行段终止的确认信号」而非周期终结点",
        ],
    },
    "C-2023-HIEQ-ROBOT-PLUS": {
        "start": [
            "产业政策（一手）：工信部等十七部门《「机器人+」应用行动实施方案》于 2023-01-18 成文、2023-01-19 发布，属十七部门联合发文的系统性产业推进文件",
            "政策量化目标提供了可交易的锚：到 2025 年制造业机器人密度较 2020 年翻番（10 大应用领域、100 种以上创新应用技术、200 个以上典型应用场景）",
            "政策介入时点处于行业低位：政策发布时行业产量同比为负（2022 年 -4.8%、2023 年 1-2 月 -19.2%），构成「政策底 vs 基本面底」的错位结构",
        ],
        "accelerator": [
            "二级市场快速定价：发布次日板块放量跳空、多股一字涨停（信邦智能 20%、达意隆、科远智慧等），形成强关注度",
            "卖方系统性解读：多家券商发布事件点评，预期未来 3-5 年机器人产业迎来新一轮景气周期、本轮工业机器人需求拐点或在 2023 年上半年显现",
            "相对强弱可观测：2023-01-14 至 2023-02-03 机器人三级子行业上涨 13.48%，显著跑赢机械设备行业（+6.47%）与沪深 300（+1.65pct 之差）",
            "估值快速抬升：至 2023-02-03 机器人板块估值达 75.45 倍，反映市场对政策目标的前置定价",
        ],
        "turning": [
            "基本面与政策目标之间存在时滞：政策发布时行业产量仍处同比负增长区间（2023 年 1-2 月 -19.2%），若基本面未在政策预期的时间窗内兑现，则存在预期修正风险",
            "2023 年 5 月起叙事重心向「具身智能/人形机器人」迁移，本政策驱动段的注意力中心被稀释（迁移本身的时间边界本包无法切分）",
        ],
        "ending": [
            "本包未能确定该政策驱动段的具体结束机制与时点，故 ending 一栏仅记录风险因素而非结束事件",
            "明确的不确定性：该候选与 R01-HIEQ-005（2023-05 起的人形机器人叙事形成）之间的边界未被切分，二者是否应视为同一 Campaign 的不同阶段，须由 ThreeC Agent 判定",
        ],
    },
    "C-2023-HIEQ-HUMANOID": {
        "start": [
            "AI 大模型技术突破的外溢：2022-11 ChatGPT 发布后 AI 大模型能力跃升，2023-05 黄仁勋公开表述「人工智能下一个浪潮将是具身智能」，将 AI 能力与物理载体相连",
            "产品技术催化：2023-05 特斯拉股东大会发布 Optimus Gen1 最新视频，展示运动控制、环境感知与动作捕捉进展",
            "产业活动聚集：2023-08-16 至 08-22 世界机器人大会在北京举行，达闼、宇树、优必选、追觅等人形机器人集中亮相",
            "地方产业基金与资本入场：北京市设立 100 亿机器人产业基金；比亚迪入股智元机器人",
            "政策预期前置：工信部副部长在 2023 世界机器人大会分论坛表示将推动出台人形机器人创新发展指导意见",
        ],
        "accelerator": [
            "国家级顶层设计落地：2023-11-02 工信部印发《人形机器人创新发展指导意见》，为该领域首个国家级文件，设定 2025 年批量生产、2027 年形成安全可靠产业链供应链体系的目标",
            "产品代际跃升：2023-12-13 特斯拉 Optimus Gen2 亮相，采用自研执行器与传感器、2 自由度驱动颈部、11 自由度灵巧手、足部力/扭矩传感器，性能提升明显，为「量产可行性」提供了叙事支撑",
            "资本化里程碑：2023-12 优必选登陆港交所成为人形机器人领域首家上市企业；傅利叶智能 GR-1 开启预售并实现小批量交付",
            "叙事可交易化：市场形成以减速器、丝杠、无框力矩电机、传感器、视觉为核心的产业链映射，使主题可被板块化交易",
        ],
        "turning": [
            "本包未在该候选段内识别到明确的转折催化，即 2023-12 之后叙事重心直接迁移至「量产预期 + 国产加速」（R01-HIEQ-007），而非转折下行",
            "潜在风险（未在本包证据中证实）：Optimus Gen2 属展示品而非量产产品，产品发布与商业化之间存在时间差",
        ],
        "ending": [
            "本包不主张该叙事段已结束；其后续形态被记录为 R01-HIEQ-007，二者边界未切分",
            "ending 一栏在此仅记录「叙事重心迁移」这一可观察现象，不主张生命周期终止",
        ],
    },

    # ---- 半导体 / 电子（Wave R01-02）：drivers 原样来自 R01-02 intake（四问），未改写
    "C-2019-SEMI-LOCALIZATION": {
        "start": [
            "美国对中兴通讯的出口禁令（2018-04-16）触发「卡脖子」认知",
            "华为及关联公司被列入实体清单（2019-05-16）",
            "国家集成电路产业投资基金（大基金）持续注资",
        ],
        "accelerator": [
            "科创板 2019-07-22 开市，为未盈利半导体企业提供上市与再融资通道",
            "韦尔股份并购豪威、闻泰科技并购安世等资产注入带来业绩与估值共振",
            "5G 商用带来的终端芯片需求预期",
        ],
        "turning": [
            "大基金一期 2019-12-20 公告减持兆易创新、汇顶科技、国科微",
            "板块估值升至历史高位（部分个股 PE 达数千倍）",
            "2020 年 3 月全球疫情冲击",
        ],
        "ending": [
            "2020-07 后指数转入高位震荡与回撤",
            "资金风格切换至新能源/光伏等顺周期方向",
        ],
    },
    "C-2020-SEMI-EQUIPMENT": {
        "start": [
            "中芯国际回 A 并把募资投向 12 英寸产线",
            "大基金二期聚焦设备/材料（刻蚀、薄膜、测试、清洗、大硅片、光刻胶、掩模版、电子特气）",
            "国内晶圆厂进入扩产周期",
        ],
        "accelerator": [
            "设备国产化率从个位数向两位数突破",
            "全球缺芯推动晶圆厂加快资本开支",
            "出口管制预期强化替代紧迫性",
        ],
        "turning": [
            "2021Q3 起终端需求转弱、渠道库存累积",
            "板块估值透支 2022 年业绩",
        ],
        "ending": [
            "2022 年全球半导体增速降至 4.4%，除日本外亚太地区增速转负",
            "A 股半导体进入去库存下行周期",
        ],
    },
    "C-2020-PANEL-CYCLE": {
        "start": [
            "三星、LG Display 宣布逐步退出 LCD，韩厂产能关停",
            "2018-2019 年过度扩产后的产能出清，行业集中度提升",
            "疫情催生「宅经济」，电视/笔记本/平板需求激增",
        ],
        "accelerator": [
            "显示驱动 IC、偏光片、玻璃等上游元器件缺货",
            "整机厂备货意愿强烈，渠道库存低位",
            "产能向京东方、TCL 华星集中后具备调控产能能力",
        ],
        "turning": [
            "2021 年 1—6 月价格持续上涨至 236 美元后动能衰减",
            "终端需求透支，整机厂采购转弱",
        ],
        "ending": [
            "2021-08 起价格进入下行通道",
            "2022 年上半年地缘政治、通胀与需求透支叠加，价格跌回 2020 年上半年水平",
        ],
    },
    "C-2019-CONSUMER-TWS": {
        "start": [
            "AirPods 带动 TWS 渗透率快速提升（2017—2019 出货增速 118%/130%/183%）",
            "安卓阵营跟进，华为/三星/OPPO/vivo/小米入局",
            "2019-01 起市场整体估值修复",
        ],
        "accelerator": [
            "AirPods Pro 需求增加，订单向大厂集中",
            "TWS 相关标的 2019 年涨幅达 4—5 倍，形成赚钱效应",
            "上游模拟芯片与存储配套需求同步放大",
        ],
        "turning": [
            "2020-11 两大龙头披露存货大幅上升",
            "TWS 普通款产能利用率降至约 80%",
            "2020-10-30 苹果 iPhone 收入同比 -20.7%",
        ],
        "ending": [
            "2020-11 后连续回调，估值中枢下移",
            "市场注意力转向新能源与半导体自主可控",
        ],
    },
    "C-2023-AI-COMPUTE-SEMI": {
        "start": [
            "ChatGPT 月活快速破亿引发大模型关注（2023 年 1 月末—2 月初）",
            "微软 2023-03-16 发布植入 GPT-4 的 Copilot",
            "英伟达 2023-03-21 GTC 大会",
        ],
        "accelerator": [
            "海外算力资本开支预期上修",
            "国产算力芯片与存储的国产替代叙事叠加",
            "光模块加单信息带动整条 AI 产业链情绪",
        ],
        "turning": [
            "2023-04 中下旬财报与估值偏离压制情绪",
            "加单信息对市场反应的边际效力下降",
        ],
        "ending": [
            "2023-06-21 起 AI 板块整体回调",
            "资金向算力租赁、华为产业链等分支迁移",
        ],
    },
    "C-2024-SEMI-MEMORY": {
        "start": [
            "2023 年存储价格深度下跌 60%—70% 后的低基数",
            "2024Q2 起库存改善、价格反弹",
            "2024-09-24 一揽子金融政策改善流动性与风险偏好",
        ],
        "accelerator": [
            "AI 服务器对 DRAM 需求为普通服务器的 8 倍，OpenAI 等企业对 DRAM 晶圆需求规模巨大",
            "三星、SK 海力士、铠侠、美光削减 NAND 供应并把产能转向 QLC/HBM",
            "云服务商追加大容量 QLC SSD 订单",
        ],
        "turning": [
            "2025Q4 DRAM 合约价季增 45%—50% 创历史最大季度涨幅后，价格涨幅成为后续需求的最大变量",
            "下游（PC/手机）成本压力显性化",
        ],
        "ending": [
            "尚未出现明确结束信号（截至 2025-12-31）",
        ],
    },
    "C-2022-SEMI-DOWNTURN": {
        "start": [
            "2021 年供需错配与重复下单造成的渠道库存需要消化",
            "消费电子终端需求萎缩",
            "美国 2022-10 进一步收紧对华半导体限制",
        ],
        "accelerator": [
            "全球半导体市场增速由 2021 年的 26% 降至 2022 年的 4.4%",
            "除日本外亚太地区市场增速转负（-2%）",
        ],
        "turning": [
            "2022Q3 起部分细分领域库存降幅明显",
            "2023-10 DRAM 与 NAND Flash 均价全面上涨",
        ],
        "ending": [
            "2023Q4 智能手机与 PC 市场分别结束连续 7、8 个季度的同比下滑",
        ],
    },
    "C-2016-PANEL-CYCLE": {
        "start": [
            "三星显示关闭部分 G7 产线转产 OLED",
            "鸿海收购夏普后减少对三星电视面板出货",
            "2016 年新增产能较少",
        ],
        "accelerator": [
            "电视面板平均尺寸由 16Q4 的 44.6 寸提升至 17Q4 的 46 寸，大尺寸化消耗产能",
            "2016Q3 起面板厂利润明显改善（京东方单季营业利润 6.78 亿元）",
        ],
        "turning": [
            "2017 年新增产能集中在下半年释放",
            "涨价压缩整机厂盈利空间，影响旺季促销",
        ],
        "ending": [
            "2017H2 起价格进入长期下行周期",
            "2019Q4 行业指标触底",
        ],
    },

    # ---- 资源 / 有色 / 化工（Wave R01-03）：drivers 原样来自 R01-03 intake（四问），未改写
    "C-2020-RES-NONFERROUS": {
        "start": [
            "新冠疫情后全球需求复苏",
            "美联储零利率 + 无限量宽松，美元实际利率下行、美元走弱",
            "疫情冲击下铜矿等矿产产量恢复缓慢，供给跟不上需求",
        ],
        "accelerator": [
            "LME 与国内铜库存持续下滑",
            "2021 年前三季度中国新能源汽车产销量同比均增长 185%，带动铜等有色金属需求",
            "海外铜需求较上年提高约 7%，叠加跨市套利窗口，2021 年中国铜出口量同比 +25% 创历史新高",
        ],
        "turning": [
            "铜价快速上涨抑制下游消费，采购意愿下降",
            "2021 年 5 月后进入宽幅震荡，商品价格不再创新高",
            "2022 年美联储进入加息周期、美元走强",
        ],
        "ending": [
            "全球流动性转向收紧",
            "高价抑制需求叠加供给恢复",
            "板块资金转向新能源等结构性方向",
        ],
    },
    "C-2020-RES-LITHIUM": {
        "start": [
            "锂精矿供给出清：2020-10-27 澳洲 Altura 进入破产管理，延续 2019 年下半年的出清",
            "《新能源汽车产业发展规划(2021-2035 年)》等政策利好 + 新能源车热销带动需求预期",
            "上游锂价处于历史周期底部（2020 年 8 月碳酸锂约 4 万元/吨）",
        ],
        "accelerator": [
            "2020-11 至 2021 年 1 月，磷酸铁锂需求推动国内锂价上涨 40% 至 18 个月高点",
            "2021 年夏季起锂价加速，2021-10 至 2022-06 锂矿供应受限、供需缺口扩大",
            "锂资源自主可控叙事驱动上市公司大额布局海内外锂矿",
        ],
        "turning": [
            "2022-11-11 碳酸锂价格达 59 万元/吨 历史高点后转为下跌",
            "2022-06 至 2022-11 需求快速拉升后转为需求快速缩减",
            "下游电池厂在价格下行期转为长单交易、去库存",
        ],
        "ending": [
            "供给放量（南美盐湖、非洲矿）使供需由偏紧转为过剩",
            "2022-11 至 2023-04 价格大幅下行，板块资金流失",
            "宁德时代锂矿返利等事件加速价格下滑与叙事失效",
        ],
    },
    "C-2020-RES-RAREEARTH": {
        "start": [
            "供给端：稀土矿产品与冶炼分离总量控制指标机制，中重稀土继续严控",
            "2020-05 起供需基本面改善，价格进入景气上升周期",
            "持货端锁货惜售、现货稀少",
        ],
        "accelerator": [
            "缅甸政局与疫情导致中缅口岸关闭近 6 个月，2021 年前 11 个月缅甸矿进口量约 2.5 万吨（-23%）",
            "2021-10-29 工信部与市场监管总局印发《电机能效提升计划(2021-2023 年)》，加大稀土永磁电机应用",
            "2021 年开采指标 16.8 万吨、冶炼分离指标 16.2 万吨，同比均增 20%，但增量全部为轻稀土指标，中重稀土指标连续四年不变",
            "北方稀土多次专场竞价推高金属镨钕成交价",
        ],
        "turning": [
            "2021-10 至 11 月价格急涨后出现冲高回调",
            "下游（中低端钕铁硼）因高价缩减用量",
            "磁材企业采购周期结束后需求边际转弱",
        ],
        "ending": [
            "配额有序释放、供给偏紧程度缓解",
            "行业整合（2021-12-23 中国稀土集团成立）改变供给主体结构",
            "价格回落至高位震荡",
        ],
    },
    "C-2021-RES-CHEM-DUALCTRL": {
        "start": [
            "2021-08-12 发改委发布能耗双控目标完成情况晴雨表，9 省(区)能耗强度不降反升被一级预警",
            "2021-09-11 发改委印发《完善能源消费强度和总量双控制度方案》，明确指标分解落实机制",
            "2020-09 中国提出碳达峰碳中和目标，双碳政策预期自 2021 年起密集落地",
        ],
        "accelerator": [
            "云南要求工业硅、黄磷月均产量不超过 8 月 10%（削减约 90%）",
            "江苏对年综合能耗 5 万吨标煤以上企业开展专项节能监察，部分纯碱企业开工率降幅约 20%",
            "内蒙古自 2021 年起不再审批焦炭、电石、PVC、合成氨(尿素)、甲醇、乙二醇、烧碱、纯碱、磷铵、黄磷等新增产能",
            "陕西榆林要求已投产「两高」项目限产 60%、9 月减产 50%",
        ],
        "turning": [
            "化工品价格急涨后出现有价无市，厂家暂停报价",
            "下游（印染、化纤、纺织）成本压力剧增并公开抵制原料涨价",
            "政策转向保供稳价，限电措施边际放松",
        ],
        "ending": [
            "能耗双控阶段性目标完成后限产放松",
            "下游需求走弱、库存回补完成",
            "价格向成本线回归",
        ],
    },
    "C-2019-RES-DYE-SHOCK": {
        "start": [
            "2019-03-21 天嘉宜化工特别重大爆炸事故（同期通报死亡 44 人，后更新为 78 人遇难）",
            "天嘉宜是染料中间体间苯二胺的三大核心生产工厂之一",
            "苏北地区染料中间体产量约占全国三分之一",
        ],
        "accelerator": [
            "2019-04-04 盐城市委决定彻底关闭响水化工园区",
            "江苏省下发《化工行业整治提升方案(征求意见稿)》，拟大幅压减化工生产企业数量",
            "2018 年苏北化工园区整治已使部分企业停产，事故进一步延迟复工",
        ],
        "turning": [
            "染料价格与印染加工费急涨，下游印染行业公开抵制",
            "绍兴市柯桥区印染工业协会倡议抵制染化料价格不正常上涨",
            "园区关停后替代产能与库存逐步补充",
        ],
        "ending": [
            "江苏省化工整治方案落地，供给侧长期收缩但价格冲击消退",
            "染料价格回落",
            "市场注意力转向新主题",
        ],
    },
    "C-2024-RES-GOLD-CB": {
        "start": [
            "2022 年美国冻结俄罗斯外汇储备后，新兴市场央行调整外汇资产结构，减持美债、增持黄金",
            "2024 年全球央行购金 1045 吨，占全球黄金总需求（4974 吨）21%",
            "实际利率之外新增「去美元化 / 国际货币体系重构」定价维度",
        ],
        "accelerator": [
            "2024 年伦敦现货黄金全年均价同比上涨 22.97% 至 2386.2 美元/盎司",
            "黄金 ETF 持仓快速扩张（2024 年底中国国内黄金 ETF 持有量同比增超八成）",
            "2025 年美联储降息预期与地缘紧张共同推动，2025 年全球央行购金延续（前三季度 634 吨）",
            "中国黄金储备 2025 年连续第 11 个月上升，至 9 月底 2303 吨",
        ],
        "turning": [
            "2025 年 12 月金价加速上行后，A 股金矿龙头股价未同步创新高，出现「现货热、股价冷」背离",
            "头部矿企采金综合成本同比上升 12%–18%，利润增速不及金价涨幅",
            "部分矿企股价在 2025 年 Q3 已提前大幅上涨，资金阶段性获利了结",
        ],
        "ending": [
            "窗口结束时结构未结束（unknown）",
        ],
    },

    # ---- 消费（Wave R01-04）：drivers 原样来自 R01-04 intake（四问），未改写
    "C-2016-CONS-BAIJIU-UPGRADE": {
        "start": [
            "高端白酒价格上行：飞天茅台一批价与零售价 2016 年持续走高（S001）",
            "行业量价齐升：2016 年全国规上白酒产量 1358.36 万千升为历史峰值（S002）",
        ],
        "accelerator": [
            "外资定价权提升：2017-06-21 MSCI 宣布自 2018 年 6 月起纳入 A 股（S003）",
            "龙头集中与业绩兑现：贵州茅台 2017 年营收 582.18 亿元、归母净利 270.79 亿元（S009）",
        ],
        "turning": [
            "2018-10-29 贵州茅台首个一字跌停，白酒股集体下跌，市场同步注意到业绩增速不及预期（S004、S005）",
        ],
        "ending": [
            "板块估值与景气同步回落（S065 计算值：2018 年全年约 -26.9%）",
            "2018 年社零增速降至 9.0%，宏观消费环境转弱（S006，仅作背景）",
        ],
    },
    "C-2019-CONS-BAIJIU-CORE": {
        "start": [
            "外资增量资金制度性启动：2019-03-01 MSCI 提高 A 股纳入因子至 20%（S007）",
            "2019 年北向资金净流入 3517.43 亿元创历史新高（S008）",
        ],
        "accelerator": [
            "2020 年疫情下\"确定性溢价\"叙事强化（本包未为该项单独建立一手证据，属解释性判断）",
            "龙头业绩持续兑现：贵州茅台 2021 年营收 1094.64 亿元、归母净利 524.60 亿元（S010）",
        ],
        "turning": [
            "2021-02-18 后核心资产集体下跌，抱团结构瓦解（S011）",
        ],
        "ending": [
            "2021 年 7 月指数单月约 -21%，全年约 -3.4%（S065 计算值）",
            "宏观消费 2021 年社零 +12.5%（S012），基本面并未同步恶化——说明结束主要由估值与资金结构驱动，而非需求端反转",
        ],
    },
    "C-2020-CONS-DUTYFREE": {
        "start": [
            "公司战略重塑：聚焦免税、变更证券简称（S069）",
            "政策方向确立：2020-06-01 海南自贸港总体方案提出放宽离岛免税额度至 10 万元（S068）",
        ],
        "accelerator": [
            "2020-06-29 财政部、海关总署、税务总局 33 号公告：额度 3 万→10 万元、不限次数、品类增至 45 类、取消单件 8000 元限额，2020-07-01 施行（S013、S014）",
            "需求验证：2020-07-01 至 10-31 离岛免税销售 120.1 亿元、同比 +214.1%（S015）；2020 年全年 274.8 亿元、+103.7%（S016）",
        ],
        "turning": [
            "2021 年后疫情反复导致客流波动，离岛免税经营主体增加、竞争加剧（本项为解释性判断，本包未取得一手竞争数据）",
        ],
        "ending": [
            "2022 年海南离岛免税店销售额约 487.1 亿元、同比约 -19%（S070，媒体转述，置信度低）",
            "2023 年 5 月股价回落至 123.10 元（S066）",
        ],
    },
    "C-2022-CONS-SERVICE-REBOUND": {
        "start": [
            "2022-12-07 疫情防控措施优化（新十条）（S021）",
            "低基数背景：2020 年国内旅游 28.79 亿人次、-52.1%，餐饮收入 -16.6%（S018、S071，context）",
        ],
        "accelerator": [
            "2023 年春节旅游出游 3.08 亿人次，恢复至 2019 年同期 88.6%（S019）",
            "2023 年五一旅游出游 2.74 亿人次，可比口径恢复至 2019 年同期 119.09%（S020）",
        ],
        "turning": [
            "2023 年 5 月社零 +12.7% 低于市场预期（S024）；6 月降至 +3.1%（S023）——人次恢复但消费力未同步修复",
        ],
        "ending": [
            "2023 年 4–5 月服务消费标的普遍回落（S066）",
            "叙事失效：\"强复苏\"预期被数据证伪，资金转向其他方向",
        ],
    },
    "C-2018-CONS-HOG-AFRICAN": {
        "start": [
            "外生供给冲击：2018-08-03 我国首例非洲猪瘟疫情确认（S026）",
        ],
        "accelerator": [
            "产能去化：生猪与能繁母猪存栏大幅下降（官方数据经媒体转述，E036，置信度低）",
            "价格与宏观传导：2019 年猪肉价格 +42.5%，拉动 CPI 约 1.81 个百分点（S031）",
        ],
        "turning": [
            "产能见底回升：2019 年 10 月能繁母猪存栏环比 +0.6%，为 2018 年 4 月以来首次回升（E036，弱证据）",
        ],
        "ending": [
            "2021 年猪价大幅回落，10 月集贸市场活猪 13.40 元/公斤、同比 -57.7%（S030）",
        ],
    },
    "C-2021-CONS-HOG-REVERSAL": {
        "start": [
            "产能去化信号：2021-08-17 公布 7 月能繁母猪存栏环比 -0.5%，结束 21 个月增长（S033）",
        ],
        "accelerator": [
            "制度框架确立：2021-09-19《生猪产能调控实施方案（暂行）》明确 4100 万头正常保有量（S027）",
            "逆周期收储：2022-02-28 启动中央冻猪肉储备收储，首批 4 万吨（S034）",
            "价格验证：2022-07-04 至 07-10 生猪平均收购价 22.26 元/公斤、同比 +30.6%（S029）",
        ],
        "turning": [
            "2022-09-08 起投放中央猪肉储备，调控方向反转（S035）",
        ],
        "ending": [
            "2022 年末猪价快速回落（S074，非官方口径，置信度低）",
            "2023 年养殖行业普遍亏损（媒体转述，本包未建立一手证据）",
        ],
    },
    "C-2020-CONS-WHITE-GOODS": {
        "start": [
            "出口替代：2020 年家电出口 4582 亿元、+24.2%，出口自 6 月起强劲反弹（S036、S037）",
        ],
        "accelerator": [
            "原材料涨价推动产品均价上升（S037）",
            "2021 年行业主营收入 1.73 万亿元、+15.5%（S038）",
        ],
        "turning": [
            "2021 年 7 月商品房销售面积与销售额单月同比首次下降（S075，媒体转述）",
        ],
        "ending": [
            "2021 年 12 月家电零售额同比 -10.4%；利润增速 +4.5% 远低于收入增速 +15.5%（S038）",
        ],
    },
    "C-2019-CONS-AESTHETICS": {
        "start": [
            "标的可得性：华熙生物 2019-11-06 科创板上市（S051）",
        ],
        "accelerator": [
            "渗透率提升与国产品牌替代（E067，二手转述，置信度低）",
            "合规化清退非法供给，份额向合规龙头集中（S047，双重性质）",
        ],
        "turning": [
            "2021-05-28 八部门印发打击非法医美专项整治工作方案，2021-06-11 公开，整治期 2021 年 6–12 月（S047）",
        ],
        "ending": [
            "2021-11-01 市场监管总局发布《医疗美容广告执法指南》（S048）",
            "2022 年市场监管总局等 11 部门开展医美行业突出问题专项治理（本包未建立一手证据链接，仅叙述性提及）",
        ],
    },
    "C-2020-CONS-BEAUTY-CN": {
        "start": [
            "制度框架：《化妆品监督管理条例》2020-06-29 公布、2021-01-01 施行（S049）",
        ],
        "accelerator": [
            "功效宣称规范化：《化妆品功效宣称评价规范》2021-04-08 发布、2021-05-01 施行（S050）",
            "标的扩容与需求验证：贝泰妮 2021-03-25 创业板上市（S052）；2021 年限额以上化妆品类零售额 4026 亿元、+14.0%（S012）",
            "线上渠道红利：抖音美妆头部品牌 GMV 由 2021 年 10 亿级升至 2022 年 20 亿级（E073，二手转述）",
        ],
        "turning": [
            "2022 年化妆品类零售额转为 -4.5%，行业需求自高增长切至负增长（S077）",
        ],
        "ending": [
            "行业需求负增长与板块估值回落（S077）",
        ],
    },
    "C-2024-CONS-TRADE-IN": {
        "start": [
            "政策定调：国发〔2024〕7 号《推动大规模设备更新和消费品以旧换新行动方案》（S041）",
        ],
        "accelerator": [
            "资金落地：发改环资〔2024〕1104 号安排约 1500 亿元超长期特别国债支持消费品以旧换新（S042）",
            "补贴细则：2024-08-24 明确 8 类家电按能效补 15%/20%（S043）",
            "需求验证：2024 年 9–12 月限额以上家电和音像器材类零售额同比 +20.5%/+39.2%/+22.2%/+39.3%（S044）；全年 10307 亿元、+12.3%（S044）",
        ],
        "turning": [
            "2025 年高基数效应显现，补贴力度边际减弱（S076）",
        ],
        "ending": [
            "2025 年推总口径家电零售 8931 亿元、-4.3%，Q3 起明显回落（S076）",
        ],
    },
    "C-2023-CONS-VALUE-RETAIL": {
        "start": [
            "渠道业态扩张：量贩零食门店快速铺开（E074/E075，第三方测算与公司数据，置信度不一）",
        ],
        "accelerator": [
            "渠道商规模化：万辰集团并表门店由 2023 年末 4726 家增至 2024 年末 14196 家（S059）；2024 年营收 323.29 亿元、+247.86%（S082）",
            "上游品牌业绩兑现：盐津铺子 2024 年营收 53.04 亿元、+28.89%，归母净利 6.40 亿元、+26.53%（S058）",
            "头部整合：2024-06 零食很忙集团（含赵一鸣）门店总数突破 10000 家（S060）",
        ],
        "turning": [
            "2025 年品牌商标（三只松鼠、良品铺子）见顶后全年收跌，板块内部出现分化",
        ],
        "ending": [
            "尚无明确结束证据（见 lifecycle 的 UNKNOWN 段）",
        ],
    },
    # ---- 金融 / 房地产（Wave R01-05）：drivers 引用 canonical evidence 编号 ----
    "C-2022-RE-POLICY-THREE": {
        "start": [
            "交易商协会「第二支箭」（民营企业债券融资支持工具）延期扩容（E-FINRE-01, 2022-11-08，T1 一手）",
            "央行、银保监《关于做好当前金融支持房地产市场平稳健康发展工作的通知》金融十六条（E-FINRE-02, 2022-11-11，T1 一手）",
        ],
        "accelerator": [
            "证监会「第三支箭」恢复涉房上市公司并购重组及配套融资（E-FINRE-03, 2022-11-28，T1）",
            "2022-11-29 板块暴涨，万科A 等近 40 只个股涨停（E-FINRE-06）",
            "2022-11-01→11-25 房地产行业指数 +20.9%，居申万一级行业涨幅前列（E-FINRE-05）",
        ],
        "turning": [
            "★ 2022 全年商品房销售面积 -24.3%、开发投资 -10.0%（E-FINRE-07，contradicting，T1）→ 政策脉冲与基本面背离",
            "★ 三支箭窗口内两个地产龙头相对沪深300 方向相反（保利发展 -3.3pct vs 万科A +18.7pct，E-FINRE-55）→ CF011 保留 UNRESOLVED，不取平均",
        ],
        "ending": [
            "2023-02-28 降温窗口（**推断值**，confidence low，无同期结束证据）",
        ],
    },
    "C-2020-RE-DEBT-RISK": {
        "start": [
            "住建部、人民银行联合召开重点房地产企业座谈会，实施房地产金融审慎管理制度（「三道红线」，E-FINRE-20, 2020-08-20，T2）",
        ],
        "accelerator": [
            "房地产贷款集中度管理制度分档设定房贷占比上限（E-FINRE-21, 2020-12-31，T1）",
            "信用债市场地产开发商违约 52 起、逾期余额约 630.28 亿元（E-FINRE-22, 2021-12-03，T3）",
            "中国恒大未能偿付 2.6 亿美元担保义务，构成违约（E-FINRE-24, 2021-12-03）",
        ],
        "turning": [
            "2021 年 A 股房地产板块全年 -7.57%，跑输沪深300（E-FINRE-23，T3）",
            "上市房企股价普遍大幅下跌：恒大 -88%、新力控股 -87%、佳兆业 -76%（E-FINRE-25）",
        ],
        "ending": [
            "2022-07 停工停贷事件后转入「保交楼」政策阶段（**阶段边界** 2022-07-31，confidence low）",
            "★ 本条为**下行结构**（result=weak = 市场/行业方向为负，**非证据质量弱**），主升阶段不存在",
        ],
    },
    "C-2024-FIN-BROKER-POLICY": {
        "start": [
            "央行行长宣布降准 0.5 个百分点、降低政策利率 20 个基点（E-FINRE-26, 2024-09-24，T1 一手）",
            "央行、金融监管总局、证监会三大金融管理部门同场出席发布会（E-FINRE-27, 2024-09-24，T3）",
        ],
        "accelerator": [
            "2024 年 9 月券商指数（证券Ⅱ）创 2015 年以来最大月度涨幅（E-FINRE-28）",
            "2024-09-13→10-08 东方财富 +136.8%（相对 +102.1pct）、中信证券 +62.1%（相对 +27.4pct）（E-FINRE-57）",
        ],
        "turning": [
            "2024-10-08 国庆后复市大幅高开但回落明显（E-FINRE-29）",
            "★ 同日成交额 3.5 万亿元创历史新高 → **全市场 Beta 不可分离**（E-FINRE-30，contradicting）→ CF003 保留 UNRESOLVED",
        ],
        "ending": [
            "2024-10-31 降温（**推断值**，无同期结束证据）；生命周期仅 11 个交易日 → date_confidence = low",
        ],
    },
    "C-2023-FIN-SOE-VALUATION": {
        "start": [
            "证监会主席提出「中国特色估值体系」（E-FINRE-31, 2022-11-21，context，叙事起点）",
            "2023 年 4 月随一季报窗口、风险偏好回落，「中特估」重新领涨（E-FINRE-32, 2023-04-30）",
        ],
        "accelerator": [
            "非银中期策略：保险明显领涨，一季报 NBV 及净利润同比超预期，「中特估」成为重要定价因素（E-FINRE-33, 2023-05-11）",
            "2023-01-31→12-29 工商银行 +24.7%，同期沪深300 -17.5%，银行相对 +42.2pct（E-FINRE-62，T2）",
        ],
        "turning": [
            "★ CF004 保留 UNRESOLVED：银行上涨属行业重估 vs 红利风格因子抱团，**未做验证**",
        ],
        "ending": [
            "无明确结束证据（peak/end 均为**推断**，confidence low；生命周期未闭合）",
        ],
    },
    "C-2024-FIN-BANK-DIVIDEND": {
        "start": [
            "2023 年内低利率 + 资产荒环境下高股息配置逐步形成（**无单一启动事件**，start 为 PHASE_WINDOW）",
        ],
        "accelerator": [
            "2024 年 A 股银行板块全年涨幅超 37%，所有行业中排名第一（E-FINRE-34）",
            "42 只银行股中 40 只涨超 10%、11 只涨超 50%，四大行股价屡创新高（E-FINRE-35）",
            "2025 上半年七家上市险企合计增配高息股约 3200 亿元（E-FINRE-37）",
        ],
        "turning": [
            "2025 年以来银行板块累计涨幅收敛至约 14%（E-FINRE-36）",
            "2024-12-31→2025-09-19 工商银行相对沪深300 转弱（相对 -5.1pct）（E-FINRE-58 / E-FINRE-59）",
            "★ CF004 保留：红利风格因子抱团与银行 Alpha 是否可分**未做验证**；CF013 口径差使超额被高估",
        ],
        "ending": [
            "**不判定 End** —— peak_date / end_date 为 NULL，结构可能仍在延续（不得把观察窗口结束当作 End）",
        ],
    },
    "C-2020-FIN-BANK-CREDIT": {
        "start": [
            "经济复苏 + 信用成本改善预期（**无精确启动锚点**，start 为 PHASE_WINDOW，confidence low）",
        ],
        "accelerator": [
            "2020-10-30→2021-03-31 工商银行 +19.8%，同期沪深300 +7.5%，银行相对 +12.3pct（E-FINRE-54，T2）",
        ],
        "turning": [
            "2021-03-03 A 股银行股全线大涨（**本包唯一同期市场证据日**，E-FINRE-39）",
        ],
        "ending": [
            "2021-03-31 窗口末（**无可靠结束锚点**）；净利润 +12.6% 部分源于 2020 年低基数，机制解释存在争议（E-FINRE-40）",
            "★ 已知弱点：仅 4 ev / 4 IG、单一代表标的（工商银行），缺行业指数广度与多标的验证",
        ],
    },
    "C-2025-FIN-INSURANCE": {
        "start": [
            "保险资产端（权益 / 高股息）+ 负债端（长期资金入市）共振（**无启动锚点**，start 为年度趋势型）",
        ],
        "accelerator": [
            "2025 年 A 股保险股指数涨幅超 30%，新华保险表现居首（E-FINRE-43）",
            "险资举牌上市公司次数增加，高股息资产配置力度更强（E-FINRE-44）",
        ],
        "turning": [
            "★ 2024-12-31→2025-09-19 中国平安相对沪深300 **-5.8pct**、工商银行 -5.1pct（E-FINRE-59，contradicting）→ CF012 代表标的与板块叙事方向冲突，**未消解**",
            "★ 保险资产端与权益市场高度耦合，存在「市场 Beta 经资产端传导」的特殊污染路径，**无法分离**",
        ],
        "ending": [
            "2025 年内**未确认峰值**（peak_date / end_date 为 NULL）；年度盘点口径下**不判定 End**",
        ],
    },
    # ---- 国防军工（Wave R01-06）：drivers 引用 canonical evidence 编号（E-MIL-*）----
    "C-2020-MIL-EQUIP-ORDER": {
        "start": [
            "2020-07-10 同期媒体：装备采购与更新换代加速、训练强度提高导致装备损耗加快（E-MIL-05）",
            "2020-07-27 同期媒体：国防军工板块「一个月大涨近30%」并逆市上涨（E-MIL-07）→ 倒推启动窗口 2020-06-25~07-05",
            "★ 2020-07 与 A 股整体放量上涨（Beta）重叠，**未分离**",
        ],
        "accelerator": [
            "2021-03-08 国防部：2021 年全国财政国防支出预算 13795.44 亿元、+6.8%（E-MIL-04，T1；**军费层 context，非订单**）",
            "2021-03-30 中航沈飞 2021 年度日常关联交易预计公告（E-MIL-01，巨潮资讯网 T1 一手；★ 公告金额未引用）",
            "2021-04-06 五大主机厂均已披露关联交易预计及甲方大额预付（E-MIL-02，研报 T3）",
            "2021H1 末中航沈飞合同负债 377.37 亿元（E-MIL-03，**会计口径代理变量**）",
            "2021Q3 公募基金军工持仓 2.10%、主动配置创 2014 年来最高（E-MIL-15）",
        ],
        "turning": [
            "2021-08-25→10-13 中证军工指数 -13.8%，中航工业集团集中减持（E-MIL-08）",
            "2021-12-01 见顶后业绩真空期 + 市场风格切换（E-MIL-09）",
            "2022-01~02 年报/一季报预告不及预期（E-MIL-11，subsequent 复盘）",
        ],
        "ending": [
            "2022 全年申万国防军工 -23.63%，居 31 个申万一级行业第 28（E-MIL-16，subsequent）",
            "2023 年「十四五」中期调整致部分装备采购与订单下达放缓（E-MIL-13，subsequent，产业侧机制）",
            "★ 对照：2022 年国防预算 +7.1% 创阶段新高但板块下跌 → **军费增长不是行情充分条件**（E042，research-level，不绑定 Campaign）",
        ],
    },
    "C-2019-MIL-GROUP-RESTRUCTURE": {
        "start": [
            "2019-07-01 中船工业集团与中船重工集团旗下合计 **9 家上市公司同步发布筹划战略性重组公告**（E-MIL-18）",
        ],
        "accelerator": [
            "2019-10-25 经国务院批准，两集团实施联合重组（国资委消息，E-MIL-19，人民网 T2）",
        ],
        "turning": [
            "重组由「筹划」进入「批准」阶段，事件不确定性下降，题材属性随之减弱",
        ],
        "ending": [
            "2019-11-26 中国船舶集团有限公司**揭牌成立**，重组事项执行完成（E-MIL-20，央企官网 T2）",
            "★ **市场侧行情证据完全缺失**（涨幅 / 峰值 / 持续时间均不可考）→ **无行情核验**",
        ],
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
    # ---- 国防军工（Wave R01-06，Research Candidate）----
    "RC-2019-MIL-PARADE-70": {
        "start": ["国庆 70 周年阅兵预期（重大纪念事件的注意力驱动）"],
        "accelerator": ["阅兵准备期的官方信息与装备展示预期"],
        "turning": ["阅兵事件兑现（2019-10-01），事件驱动型叙事的注意力衰减"],
        "ending": ["阅兵结束后注意力迁移（复盘口径，日期不可考）",
                   "★ 全部证据为 2025 年 retrospective 复盘，**无同期一手证据**"],
    },
    "RC-2025-MIL-PARADE-80": {
        "start": ["2025-06-24 国新办官宣 9 月 3 日纪念大会（含阅兵）（Tier 1 官方发布）"],
        "accelerator": ["2025-08-20 国新办阅兵准备发布会（Tier 1）",
                        "券商归纳的复合叙事：阅兵 + 军贸 + 景气反转 +「十五五」",
                        "「参阅装备突出智能化」等新型作战力量叙事"],
        "turning": ["未知：本包未取得阅兵后的行情转折证据"],
        "ending": ["未知；★ **不得把阅兵事件结束直接等同于 Campaign 结束**",
                   "★ 市场响应证据仅 Tier 3 相对强弱描述，无绝对涨幅 / 无指数点位"],
    },
    "RC-2017-MIL-MIXED-REFORM": {
        "start": ["2017-01-04 中国兵器工业集团《关于发展混合所有制经济的指导意见（试行）》（26 条、4 家试点）",
                  "军工被列为 2017 年中央经济工作会议确定的七大重点改革行业之一"],
        "accelerator": ["2017-01-22 中共中央政治局决定设立中央军民融合发展委员会（最高层面统一领导）"],
        "turning": ["未知"],
        "ending": ["未知；2017 年 2 月之后走势、峰值与结束完全不可考 → **生命周期无法闭合**",
                   "★ **无任何证据显示 2017 年混改已转化为订单或业绩**"],
    },
    "RC-2015-MIL-REFORM-BULL": {
        "start": ["军工改革与资产证券化预期（券商事后复盘：改革预期 + 低估值标的涨幅居前）",
                  "2015-03 军民融合发展上升为国家战略",
                  "★ 2013–2014 年以来军工板块已持续跑赢沪深300（行情延续而非 2015 年新起）"],
        "accelerator": ["★ 2015 年 A 股杠杆资金推动的全面牛市（**市场 Beta，无法分离**）"],
        "turning": ["2015 年 6 月中旬起 A 股系统性去杠杆"],
        "ending": ["★ 与 A 股系统性调整同步，**军工自身机制层面的结束点不可考**",
                   "★ 无法把军工的结束与全市场 Beta 的结束分离"],
    },
    "RC-2024-MIL-COMMERCIAL-SPACE": {
        "start": ["2024-08-06 千帆星座首批 18 星入轨（低轨星座进入批量组网阶段）",
                  "2024、2025 年国务院政府工作报告两次提出推动商业航天产业加快发展"],
        "accelerator": ["2025-10-24 二十届四中全会与「十五五」建议提出加快建设航天强国、发展航空航天战略性新兴产业集群",
                        "2025-11 国家航天局《推进商业航天高质量安全发展行动计划（2025—2027年）》+ 商业航天司设立",
                        "2025-12 朱雀三号首飞入轨（可重复使用火箭技术验证）"],
        "turning": ["未知"],
        "ending": ["无结束证据（2025 年末仍活跃）→ **生命周期未闭合**",
                   "★ 政策催化主管部门为**工信部 / 国家航天局**，主题是商业航天 / 卫星通信产业发展，**不是国防采购订单**"],
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
    # ---- 电力设备（Wave 1A）：行业代理指数不可得（电力设备 ETF 均晚于 2022 成立），
    #      按 v1.1 §6 使用 Campaign 自身代表标的 ----
    "C-2020-POWER-NE": "LONGI",
    "C-2022-POWER-GRID": "NARI",
    # ---- 信息通信（Wave 1B）：行业指数代理不可得，按 v1.1 §6 使用 Campaign 自身代表标的 ----
    "C-2019-COMM-5G": "ZTE",
    "C-2023-COMM-OPTICAL": "INNOLIGHT",
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
    "C-2020-POWER-NE": ("Campaign 自身代表标的 隆基绿能（单晶硅片/组件龙头）raw/adj close；"
                        "同 Campaign 另含 阳光电源（2021-10-27 见顶）与 金风科技（2021-11-04 见顶）→ Peak 分批。"
                        "电力设备行业指数代理不可得（相关 ETF 均晚于本轮窗口成立），不参与 Peak 判定（v1.1 §6）"),
    "C-2022-POWER-GRID": ("Campaign 自身代表标的 国电南瑞（电网自动化龙头）raw/adj close；"
                          "同 Campaign 另含 许继电气（2024-07-09 见顶）与 平高电气（2024-10-14 见顶）→ Peak 分批。"
                          "★ 思源电气（2025-12-26 见顶）与 特变电工（2025-11-07 见顶）延后，属出海环节错位；"
                          "特变电工另有 多晶硅（新特能源）混淆，均不参与 Peak 判定（v1.1 §6）"),
    "C-2019-COMM-5G": ("Campaign 自身代表标的 中兴通讯（通信主设备）raw/adj close；"
                       "同 Campaign 另含 烽火通信（2020-03-12 见顶）、中际旭创（2020-02-24 见顶）与 "
                       "新易盛（延后至 2020-07-14 见顶，环节错位）→ Peak 分批。"
                       "信息通信行业指数代理不可得，不参与 Peak 判定（v1.1 §6）"),
    "C-2023-COMM-OPTICAL": ("Campaign 自身代表标的 中际旭创（光模块龙头）raw/adj close；"
                            "同 Campaign 另含 新易盛（2025-12-22 达区间高点）、天孚通信与光迅科技。"
                            "★ 至本地行情窗口末端（2025-12-31）代表标的仍在上行，"
                            "Peak 未确认，peak_date 取中际旭创自身区间高点（v1.1 §6）"),
    # ---- 金融 / 房地产（Wave R01-05）：本地 market_series 无任何 A 股金融/地产序列，
    #      行业指数代理与代表标的行情**均不可得** → 如实 unavailable，不制造行情快照 ----
    "C-2022-RE-POLICY-THREE": ("本地 market_series 无地产板块指数 / 代表标的前复权序列 → 行情快照 unavailable。"
                               "区间相对表现引自 intake 一级行情证据 E-FINRE-55（保利发展 -3.3pct / 万科A +18.7pct，"
                               "**两个龙头方向相反**）→ CF011 保留，不取平均"),
    "C-2020-RE-DEBT-RISK": ("本地 market_series 无地产板块指数 / 代表标的前复权序列 → 行情快照 unavailable。"
                            "下行段方向证据引自 intake（2021 年板块 -7.57% 跑输大盘；恒大 -88% / 新力 -87% / 佳兆业 -76%）"),
    "C-2024-FIN-BROKER-POLICY": ("本地 market_series 无券商指数 / 代表标的前复权序列 → 行情快照 unavailable。"
                                 "区间相对表现引自 intake E-FINRE-57（东方财富相对 +102.1pct、中信证券相对 +27.4pct）；"
                                 "★ 该数量级为「成交量 Beta 代理」信号，**非行业 Alpha**"),
    "C-2023-FIN-SOE-VALUATION": ("本地 market_series 无银行 / 保险指数与代表标的前复权序列 → 行情快照 unavailable。"
                                 "区间相对表现引自 intake E-FINRE-62（工商银行相对 +42.2pct）；"
                                 "★ CF004 红利风格因子是否可分**未做验证**"),
    "C-2024-FIN-BANK-DIVIDEND": ("本地 market_series 无银行指数与代表标的前复权序列 → 行情快照 unavailable。"
                                 "★ peak_date / end_date 为 NULL（结构可能仍在延续）；"
                                 "★ CF013 口径差使相对超额被系统性高估（约 +15pct/3 年），**不得解释为行业 Alpha**"),
    "C-2020-FIN-BANK-CREDIT": ("本地 market_series 无银行指数 / 代表标的前复权序列 → 行情快照 unavailable。"
                               "区间相对表现引自 intake E-FINRE-54（工商银行相对 +12.3pct）；"
                               "★ 仅 4 ev / 4 IG、单一代表标的，缺行业指数广度与多标的验证"),
    "C-2025-FIN-INSURANCE": ("本地 market_series 无保险指数与代表标的前复权序列 → 行情快照 unavailable。"
                             "★ peak_date / end_date 为 NULL；CF012 代表标的（中国平安相对 -5.8pct）与板块叙事（指数 +30%）"
                             "方向冲突，**未消解**"),
    # ---- 国防军工（Wave R01-06）：本地 market_series 无任何军工指数 / 军工标的前复权序列 → 如实 unavailable ----
    "C-2020-MIL-EQUIP-ORDER": ("本地 market_series 无军工指数 / 军工标的前复权序列 → 行情快照 unavailable。"
                               "区间涨跌引自 intake 一级/二级整理证据：中证军工指数 2021 全年 +8.97%"
                               "（1/8–5/10 -32%、5/11–8/24 +43%）、2021-12-01 高点 14748 点；申万国防军工 2022 全年 -23.63%。"
                               "★ 市场层**全部为 Tier 3 二手整理**（未取得指数公司官方历史点位原文）；"
                               "★ 2020-07 启动段与 A 股整体放量上涨（Beta）**重叠，未分离**"),
    "C-2019-MIL-GROUP-RESTRUCTURE": ("本地 market_series 无军工指数 / 船舶系标的前复权序列 → 行情快照 unavailable。"
                                     "★ **市场侧行情证据完全缺失**（涨幅 / 峰值 / 持续时间均不可考）→ **无行情核验**；"
                                     "★ peak_date 为 NULL（不制造精确日期）"),
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
        # 2018 为汽车 Rule 的反例年份：只吸收**汽车 Rule 自己的、未显式绑定任何 Campaign** 的 2018 年证据。
        # （否则其他 Rule 的 2018 年证据会被误并入汽车反例年份 → evidence-cross-campaign）
        # ★ 与下方 source_ids 的 `S-2018-%` 同构：用 `E-2018-%` 把范围限定到汽车 Rule 自身的 2018 年证据。
        #   原实现仅按 `date LIKE '2018%'` 过滤，会把**其它 Rule 的 2018 年孤儿证据**（如 R01-05 的
        #   E-FINRE-51 资管新规 2018-04-27）误并入汽车反例年份。对既有各 Rule 数据行为完全一致
        #   （既有 unbound 2018 证据仅 E-2018-01..04）。
        "evidence_ids": [e["evidence_id"] for e in q(
            "SELECT evidence_id FROM evidences WHERE evidence_id LIKE 'E-2018-%' "
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
                  " + rule_pharma_upgrade（医药健康 2019–2022，结构性升级）"
                  " + rule_power_equipment（电力设备 2018–2025，发电设备 / 电网输配电）"
                  " + rule_infocomm（信息通信 2018–2025，5G 建设 / AI 算力光模块）"
                  " + rule_high_end_equipment（高端装备 / 机器人 2016–2022，工程机械 / 工业自动化 / 机器人）"
                  " + rule_semiconductor（半导体 / 电子 2016–2025，国产替代 / 面板价格周期 / AI 算力 / 存储超级周期）"
                  " + rule_resources（资源 / 有色 / 化工 2016–2025，供给收缩五子类型 / 新能源需求 / 黄金资产属性）"
                  " + rule_consumer（消费 2016–2025，消费升级 / 政策替代 / 自然周期 / 财政补贴 / 渠道变革）"
                  " + rule_fin_realestate（金融 / 房地产 2015–2025，地产政策周期 / 信用周期 / 估值重估 / 风险偏好；含 CF013 口径差约束）"
                  " + rule_defense_military（国防军工 2019–2022，装备采购订单景气 / 军工集团战略重组；含 CF008 军费传导时滞约束）"),
        "status_vocabulary": {
            "PROVISIONAL": "研究预览可用：主题可识别+行情/媒体证据+≥1可靠来源+主要日期有依据+无跨时间因果错误；未人工复核，非 VERIFIED",
            "CONFLICT": "存在研究日期口径冲突（candidate_a vs candidate_b），保留双方证据，不强行解决",
            "INSUFFICIENT": "来源不足/无法判断 Campaign 或时间范围/行情数据缺失，不编造",
        },
        "note": "本 manifest 为研究批次输出，不是新的正式 Schema；PROVISIONAL 不等于 VERIFIED，不得进入 Cycle verified",
        "campaigns": entries,
    }
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
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
    with open(CONFLICTS, "w", encoding="utf-8", newline="\n") as f:
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
        POWER_RULE: {
            "definition": ("Historical Observation Window（历史观察窗口）：电力设备（新能源发电设备 / "
                           "电网输配电设备）在政策与电网投资周期驱动下形成的结构性行情；"
                           "非固定买入窗口，不构成交易建议"),
            "observation_window": ("结构性（非季节性）：2018–2025。两个独立 Theme Cycle："
                                   "① 清洁能源发电设备 2020-09-22~2022-12-30（Peak 2021-10-27~2021-11-04）；"
                                   "② 电网投资与特高压 2022-01-10~2025-12-31（Peak 2024-07-09~2024-10-14）"),
        },
        COMM_RULE: {
            "definition": ("Historical Observation Window（历史观察窗口）：信息通信（通信设备 / "
                           "光模块光器件 / 光纤光缆 / 数据中心与算力基础设施）在政策、运营商资本开支"
                           "与云/AI 资本开支驱动下形成的结构性行情；非固定买入窗口，不构成交易建议"),
            "observation_window": ("结构性（非季节性）：2018–2025。两个独立 Theme Cycle："
                                   "① 5G 网络建设与光通信基础设施 2019-06-06~2022-10-11"
                                   "（Peak 2020-02-24~2020-03-12）；"
                                   "② AI 算力驱动的光模块 2023-03-21~2025-12-31"
                                   "（Peak 未确认，2025-12-22~12-25 为区间高点）"),
        },
        CONS_RULE: {
            "definition": ("Historical Observation Window（历史观察窗口）：消费（食品饮料 / 家用电器 / 农林牧渔 / 社会服务 / "
                           "商贸零售 / 美容护理）在消费升级、核心资产定价、政策放开与需求替代、事件驱动补偿需求、"
                           "供给端自然周期、出口替代、渗透率提升、财政补贴与渠道效率变革驱动下形成的结构性行情；"
                           "非固定买入窗口，不构成交易建议"),
            "observation_window": ("结构性（非季节性）：2016–2025。五条机制主线："
                                   "① 消费升级 / 核心资产（白酒 2016-06-01~2018-12-31 与 2019-03-01~2021-12-31，Sequential）；"
                                   "② 政策放开 + 需求替代（离岛免税 2020-06-01~2022-12-31）；"
                                   "③ 事件驱动补偿需求（疫后修复 2022-12-07~2023-06-30）；"
                                   "④ 供给端自然周期（猪周期 2018-08-03~2021-12-31 与 2021-08-17~2022-12-31，Sequential）；"
                                   "⑤ 财政补贴 → 官方销量 → A 股响应（以旧换新 2024-03-13~2025-12-31）"),
        },
        RES_RULE: {
            "definition": ("Historical Observation Window（历史观察窗口）：资源 / 有色 / 化工（工业金属 / 贵金属 / 稀有金属·稀土 / "
                           "能源金属 / 基础化工 / 农化）在供给收缩、行政限产、环保约束、安全事故冲击、成本与地缘冲击、"
                           "新能源需求、以及黄金资产属性驱动下形成的结构性行情；非固定买入窗口，不构成交易建议"),
            "observation_window": ("结构性（非季节性）：2016–2025。四条机制主线："
                                   "① 再通胀 / 需求复苏（工业金属 2020-03-23~2021-12-31，Peak 2021-09-13 = 8603.88）；"
                                   "② 新能源需求拉动（锂 2020-10-27~2022-11-11，A 股 Peak 2021-09-13 / 商品 Peak 2022-11-11）；"
                                   "③ 供给收缩五子类型（行政去产能 / 能耗双控 / 环保约束 / 配额控制 / 安全事故冲击）；"
                                   "④ 黄金资产属性（2024-02-01 起，Peak 未确认 —— CF009 商品与 A 股背离未决）"),
        },
        SEMI_RULE: {
            "definition": ("Historical Observation Window（历史观察窗口）：半导体 / 电子产业链（设计 / 制造 / 封测 / 设备 / 材料 / 被动元件 / 面板）在国产替代、资本开支、供给约束与下游需求周期驱动下形成的结构性行情；非固定买入窗口，不构成交易建议"),
            "observation_window": ("结构性（非季节性）：2016–2025。四条机制主线："
                                   "① 国产替代 / 自主可控：2019-05-16~2020-09-30（Peak 2020-07-14 = 5869.83）与 2020-07-16~2021-09-30（Peak 2021-07-30 = 7642.58）"
                                   "② 面板价格周期：2016-02-01~2017-06-30 与 2020-06-01~2021-08-31"
                                   "③ 需求与库存：2019 TWS 与 2022 下行去库存（Peak 2022-08-31）"
                                   "④ AI 算力（2023）与存储超级周期（2024-09-24 起，Peak 2025-10-31 = 7964.33，指数新高）")
        },
        HIEQ_RULE: {
            "definition": ("Historical Observation Window（历史观察窗口）：高端装备 / 机器人（工程机械 / "
                           "工业自动化 / 机器人本体与核心零部件 / 轨道交通装备）在设备更新、制造业资本开支、"
                           "产业政策与产业叙事驱动下形成的结构性行情；非固定买入窗口，不构成交易建议"),
            "observation_window": ("结构性（非季节性）：2016–2022。两个 Sequential Theme Cycle："
                                   "① 工程机械更新+基建+环保 2016-08-01~2021-12-31"
                                   "（Peak 2021-01-25 资产价格 / 2021-03-31 产业销量）；"
                                   "② 工业机器人与自动化 2018-09-30~2022-12-31"
                                   "（含 2018-2019 下行段与 2020-2021 复苏段）。"
                                   "另：2023 机器人政策段与人形机器人叙事段（hieq_robot_2023）"),
        },
        FINRE_RULE: {
            "definition": ("Historical Observation Window（历史观察窗口）：金融 / 房地产（房地产开发 / 银行 / 非银金融 / 保险）"
                           "在地产政策周期、信用周期、估值重估（「中特估」/ 高股息红利）、"
                           "市场风险偏好与流动性驱动下形成的结构性行情；"
                           "非固定买入窗口，不构成交易建议"),
            "observation_window": ("结构性（非季节性）：2015–2025。四条机制主线："
                                   "① 地产政策周期（Sequential：2020-08-20~2022-07-31 融资收紧→债务风险暴露（下行）"
                                   " → 2022-11-08~2023-02-28 三支箭政策修复）；"
                                   "② 银行估值 / 资金配置（2023-04-01~2023-06-30 中特估 与 2024-01-01 起 高股息，Parallel）；"
                                   "③ 信用周期（2020-10-30~2021-03-31 银行顺周期）；"
                                   "④ 风险偏好 / 流动性（2024-09-24~2024-10-31 券商；2025 保险资产端共振）。"
                                   "★ CF013 口径差（个股前复权含股息 vs 沪深300 价格指数不含股息）**UNRESOLVED** —— "
                                   "相对收益**不得直接解释为行业 Alpha**，Beta 中性验证未完成"),
        },
        MIL_RULE: {
            "definition": ("Historical Observation Window（历史观察窗口）：国防军工（航空装备 / 航天装备 / 船舶制造 / 军工电子）"
                           "在装备采购与订单释放（含甲方预付款 / 合同负债）、军工集团改革与资产重组、"
                           "重大纪念事件注意力驱动下形成的结构性行情；"
                           "非固定买入窗口，不构成交易建议"),
            "observation_window": ("结构性（非季节性）：2019–2022。两条机制主线（**机制不同、窗口不重叠**）："
                                   "① 装备采购订单景气 2020-06-25~2022-12-31（「十四五」装备放量；"
                                   "2021-03-30 主机厂关联交易预计公告为订单层可验证锚点；Peak 2021-12-01 = 14748 点）；"
                                   "② 军工集团战略重组 2019-07-01~2019-11-26（「南北船」合并：筹划→批准→揭牌；**peak 不可考**）。"
                                   "★ **CF008 军费传导时滞**：国防预算（2021-03-08）→ 订单披露（2021-03-30）→ 市场主升（2021-05-11，"
                                   "**距预算公布约 9 周**）→ 区间高点（2021-12-01，**约 9 个月**）；"
                                   "★ **反向对照 E042**：2022 年国防预算 +7.1%（阶段新高）而军工板块全年 -23.63% → "
                                   "**传导非稳定**；**军费层只能作 `context`，不得作为 Campaign start 锚点**"),
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
        # ★ 「2018 = 反例年份（no_clear_campaign）」是 **rule_auto_summer（汽车）专属**的年度约定，
        #   不是全局规则。原实现按 year==2018 全局跳过，会把其它 Rule 的 2018 年真实 Campaign
        #   （如 C-2018-HIEQ-ROBOT-DOWN）误删。此处按 rule 限定，对既有数据行为完全一致
        #   （既有各 Rule 均无 2018 年 Campaign）。
        if e["year"] == 2018 and e["rule_id"] == AUTO_RULE:
            continue  # 汽车反例年份，不出现在 campaign 列表（反例由 rule 级注释承载）
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
    with open(EXPORT, "w", encoding="utf-8", newline="\n") as f:
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
