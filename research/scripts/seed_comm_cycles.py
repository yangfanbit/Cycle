"""信息通信（Information & Communication）历史 Cycle 入库（Research 侧）— Wave 1B。

背景（Historical Coverage Audit v0.2 §J / Wave 1 P0）：
- 历史侧此前只有 `TH-AUTO` / `TH-PHARMA` / `TH-POWER`；Current Candidate 侧
  `CC-2026-OPTICAL-LINK`（高速光互联 1.6T / NPO / CPO）声明 `macro_theme = "信息通信"`，
  但历史侧无同名 Macro Theme / Theme Cycle → Similarity 的 Pattern 层恒 `UNKNOWN`。
- 本脚本把「信息通信」接入 ThreeC 数据链路（Research → DB → Export → Timeline）。

本轮纳入的 Historical Theme Cycle（**数量由证据决定，不为凑数制造 Cycle**）：

  1. `comm_5g_infrastructure_2019_2022` — 5G 网络建设与光通信基础设施
     （5G 牌照 → 5G 正式商用 → 新基建加速 → Peak 2020-02/03 → 2022-10 出清）
  2. `comm_ai_optical_2023_2025` — AI 算力驱动的光模块（800G / 1.6T）
     （NVIDIA GTC 2023 → Q1 FY2024 财报 → 中际旭创 800G 业绩兑现；2025 仍在上行）

**Primary / Related 规则（继承 Wave 1A，用户 2026-09-17 决策）**：
- 每个 Theme Cycle 有且只有一个 Primary Macro Theme（用于 Theme Family 统计 /
  `theme_family_count` / Time Observation 独立样本计数 / Structural Analogy 跨族独立性）。
- Related 不增加独立样本数。
- **实现约束（实测）**：CMTR v1 对对象 `themes[]` **全量**解析根节点，且
  `theme_family_id = fam_ids[0] if len(fam_ids)==1 else None`
  → 一个 Campaign 挂 ≥2 个 Macro root 会被判 CONFLICT 并**被排除出所有族**。
  因此 Related Macro Theme **不写进 `campaign_themes`**，改记研究层文档。**未改 schema。**

纪律：
- 不修改 `schema/schema.sql` / `contracts/` / export contract / `src/` / Timeline UI / Research Model。
- 不新增数据库实体 / 新表 / 新列（仅新增数据行）。
- 日期：Campaign `start_date` = `EARLY_SIGNAL`（与既有 11 个 Campaign 一致）；
  Peak / 区间来自本地真实行情复核（`research/data/market/normalized/*.csv`，腾讯 GTIMG 前复权）。
- 不伪造：取不到的日期留 NULL / 写 unknown；不计算 seasonality / win_rate / probability。
- `evidence_type` 沿用仓库既有可归一化取值（`政策文件`/`行业数据`/`行情数据`/`media`）；
  公司财报类证据使用 `source_type='company_announcement'`（schema 允许、此前未使用），
  但 `evidence_type` 仍落在既有可归一化取值内 —— **不新增未映射取值**。
- 幂等：全部 `db.insert`（INSERT OR REPLACE），可重复运行。

用法: python scripts/seed_comm_cycles.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

conn = db.connect()
db.migrate(conn)

RULE = "rule_infocomm"
C_5G = "C-2019-COMM-5G"           # 5G 网络建设与光通信基础设施
C_AI = "C-2023-COMM-OPTICAL"      # AI 算力驱动的光模块

# ------------------------------------------------------------------ 1) Rule
RULES = [
    dict(rule_id=RULE, name="信息通信历史周期观察", base_pattern="信息通信",
         description=("历史观察窗口：信息通信（通信设备 / 光模块光器件 / 光纤光缆 / "
                      "数据中心与算力基础设施）在政策、运营商资本开支与云/AI 资本开支"
                      "驱动下形成的结构性行情。非固定买入窗口，不构成交易建议。"),
         source_id=None, status="under_review"),
]

# ------------------------------------------------------- 2) Annual Reviews
ANNUAL = [
    dict(annual_review_id="AR-COMM-2018", rule_id=RULE, year=2018, status="weak",
         summary=("Setup 年：美国商务部 4 月激活对中兴通讯的拒绝令（7 年禁运）→ "
                  "中兴通讯 -49.0%、中际旭创 -33.8%、新易盛 -40.0%。"
                  "通信板块整体下行，无正向 Campaign。")),
    dict(annual_review_id="AR-COMM-2019", rule_id=RULE, year=2019, status="strong",
         summary=("5G 商用牌照（06-06）与 5G 正式商用启动（10-31）→ 板块自 2019-01 低点大幅修复："
                  "中兴通讯 +94.5%、中际旭创 +93.9%、新易盛 +163.6%。"
                  "运营商固定资产投资 +4.7%（5G 相关投资快速增长）。")),
    dict(annual_review_id="AR-COMM-2020", rule_id=RULE, year=2020, status="strong",
         summary=("新基建加速（02-21 政治局会议、02-22 工信部会议、03-04 政治局常委会）→ "
                  "代表标的 02-24~03-12 批量见顶（中兴 52.30 / 中际旭创 49.41 / 烽火 40.34）；"
                  "运营商固定资产投资 4072 亿元（+11%）。新易盛延后至 07-14 见顶。")),
    dict(annual_review_id="AR-COMM-2021", rule_id=RULE, year=2021, status="weak",
         summary=("5G 资本开支见顶：上半年三大运营商 5G 资本开支均下滑；"
                  "全年电信固定资产投资 4058 亿元（与上年基本持平）。"
                  "板块普跌（中兴 -2.0%、烽火 -27.3%、中际旭创 -19.4%）。")),
    dict(annual_review_id="AR-COMM-2022", rule_id=RULE, year=2022, status="weak",
         summary=("5G 投资稳步下降 + 板块出清：中兴 -23.4%、烽火 -28.2%、中际旭创 -38.2%；"
                  "代表标的 2022-10-10/11 同步见底（本轮 Cycle 出清完成）。"
                  "「东数西算」02-17 全面启动（新驱动萌芽，尚未形成行情）。")),
    dict(annual_review_id="AR-COMM-2023", rule_id=RULE, year=2023, status="strong",
         summary=("AI 算力叙事启动：NVIDIA GTC 2023（03-21）→ A 股光模块 03-22 爆发；"
                  "NVIDIA Q1 FY2024 财报（05-24，Q2 指引 110 亿美元）确认算力需求；"
                  "中际旭创 2023 半年报显示下半年 800G 出货明显增长。"
                  "中际旭创 +339.0%、新易盛 +204.3%。")),
    dict(annual_review_id="AR-COMM-2024", rule_id=RULE, year=2024, status="strong",
         summary=("业绩兑现：中际旭创 2023 年报营收 107.18 亿元（+11.16%）、2024Q1 净利润超 10 亿元；"
                  "中际旭创 +57.4%、新易盛 +147.4%。板块于 2024-10-08 出现阶段高点后震荡。")),
    dict(annual_review_id="AR-COMM-2025", rule_id=RULE, year=2025, status="strong",
         summary=("高速率迭代延续：1.6T 与 NPO/CPO 结构迁移预期推动；"
                  "中际旭创 +406.6%（区间高点 638.80 @2025-12-25）、新易盛 +439.2%"
                  "（329.99 @2025-12-22）。Cycle End 未确认（本地行情窗口止于 2025-12-31）。")),
]

# ------------------------------------------------------------- 3) Themes
# 只建立 root + **被实际引用所必需**的最小 Sub-theme 集（不做完整子主题树）。
THEMES = [
    dict(theme_id="TH-COMM", name="信息通信", theme_type="industry", parent_theme_id=None,
         description=("Macro Theme（Wave 1B 新建）。与 Current Candidate 侧 "
                      "`CC-2026-OPTICAL-LINK` 声明的 macro_theme=\"信息通信\" 精确对齐"
                      "（Similarity 的 Pattern 层按名称精确匹配）。")),
    dict(theme_id="TH-COMM-5G", name="5G网络建设/通信设备", theme_type="concept",
         parent_theme_id="TH-COMM",
         description=("Sub-theme：5G 主设备、传输设备与运营商网络建设（"
                      "驱动 = 运营商资本开支与 5G 建设节奏）。")),
    dict(theme_id="TH-COMM-OPTICAL", name="光模块/高速光互联", theme_type="concept",
         parent_theme_id="TH-COMM",
         description=("Sub-theme：光模块、光器件与高速光互联（"
                      "驱动 = 数据中心 / 云 / AI 资本开支与速率代际升级 100G→400G→800G→1.6T）。")),
]

# ---------------------------------------------------------- 4) Campaigns
CAMPAIGNS = [
    dict(
        campaign_id=C_5G,
        annual_review_id="AR-COMM-2019",
        rule_id=RULE,
        season_id="comm_5g_2019_2022",
        campaign_year=2019,
        start_date="2019-06-06",      # = EARLY_SIGNAL（5G 商用牌照）
        end_date="2022-10-11",        # 代表标的同步低点（出清完成）
        peak_date="2020-02-25",       # 中兴通讯自身区间高点；Peak Window 见 research_notes
        strength="strong",
        result="positive",
        classification="theme_campaign",
        start_date_basis="official_event",
        end_date_basis="market_data",
        date_confidence="medium",
        description=("5G 网络建设与光通信基础设施：政策路径为「5G 商用牌照（2019-06-06）→ "
                     "5G 正式商用启动（2019-10-31）→ 新基建加速（2020-02-21 政治局会议 / "
                     "2020-02-22 工信部会议 / 2020-03-04 政治局常委会）」。"
                     "代表标的：中兴通讯（主设备）、烽火通信（光通信/主设备）、"
                     "中际旭创与新易盛（光模块）。"),
        research_notes=("跨年 Campaign（2019-06-06 ~ 2022-10-11，约 3.4 年）。"
                        "Peak 口径按 Theme/Campaign Separation v1.1 §6 使用 Campaign 自身代表标的："
                        "中际旭创 2020-02-24（49.41）、中兴通讯 2020-02-25（52.30）、"
                        "烽火通信 2020-03-12（40.34）、新易盛 2020-07-14（20.01）、"
                        "天孚通信 2020-08-04（12.42）→ Peak Window 2020-02-24~2020-08-04（DATE_WINDOW，"
                        "**分批见顶**，与医药 Campaign 的 Peak Window 口径一致）。"
                        "★ 环节错位（不另立 Cycle）：通信主设备与中际旭创于 2020-02/03 见顶"
                        "（国内 5G 建设加速预期驱动），而数通光器件（新易盛 / 天孚通信）延后至 "
                        "2020-07/08 见顶（海外云厂商资本开支与 400G 放量节奏滞后）；"
                        "两者核心研究对象与叙事中心同属信息通信，**不拆分为两个 Cycle**。"
                        "★ 出清：代表标的于 2022-10-10/11 同步见底（中兴 18.41 / 烽火 11.65 / "
                        "中际旭创 15.88 / 新易盛 6.33）→ 本轮 Cycle 出清完成。"
                        "★ Setup：2018-04-16 美国商务部对中兴通讯激活拒绝令（7 年禁运）"
                        "→ 2018 年板块深跌（中兴 -49.0%），构成低基数起点，本身不是正向驱动。"
                        "★ Related Macro Theme：无（核心为信息通信本体）。"),
    ),
    dict(
        campaign_id=C_AI,
        annual_review_id="AR-COMM-2023",
        rule_id=RULE,
        season_id="comm_ai_optical_2023_2025",
        campaign_year=2023,
        start_date="2023-03-21",      # = EARLY_SIGNAL（NVIDIA GTC 2023 主题演讲）
        end_date="2025-12-31",        # 本地行情窗口末端（Cycle End 未确认）
        peak_date="2025-12-25",       # 中际旭创自身区间高点；仍在上行，未确认见顶
        strength="strong",
        result="positive",
        classification="theme_campaign",
        start_date_basis="official_event",
        end_date_basis="market_data",
        date_confidence="medium",
        description=("AI 算力驱动的光模块（800G / 1.6T）：政策与产业路径为"
                     "「NVIDIA GTC 2023 主题演讲（2023-03-21，AI 算力叙事）→ "
                     "NVIDIA Q1 FY2024 财报（2023-05-24，Q2 指引 110 亿美元，算力需求财务确认）→ "
                     "中际旭创 2023 半年报（2023-08-28，下半年 800G 出货明显增长）→ "
                     "2024 年报/一季报业绩兑现」。"
                     "代表标的：中际旭创、新易盛（光模块）、天孚通信（光器件）。"),
        research_notes=("跨年 Campaign（2023-03-21 ~ 2025-12-31，约 2.8 年，**尚未结束**）。"
                        "★ 与 Cycle 1 的独立性：核心研究对象（AI 数据中心互连 vs 运营商 5G 网络）、"
                        "驱动变量（海外云与 AI 资本开支 vs 运营商资本开支）、"
                        "生命周期（2023-2025 上行 vs 2019-2020 见顶后出清）三者均不同 → 独立 Cycle。"
                        "★ Peak 口径：中际旭创 2025-12-25（638.80）、新易盛 2025-12-22（329.99）"
                        "→ 至本地行情窗口末端**仍在上行**，Theme Cycle End 未确认。"
                        "★ 通信设备（中兴通讯 / 烽火通信）在 2023-2025 亦受益于算力网络建设"
                        "（中兴 2024 +64.8%、烽火 2025 +79.9%），但其主驱动仍含运营商侧因素，"
                        "本轮不作为本 Cycle 代表标的。"
                        "★ Related Macro Theme：无（核心为信息通信本体；与「电力设备」的"
                        "算电协同属产业关联，非本 Cycle 的 Primary 归属）。"),
    ),
]

CAMPAIGN_THEMES = [
    # ---- Cycle 1：5G 网络建设与光通信基础设施 ----
    # Macro Theme 行沿用既有约定 role='related' + theme_type='industry'
    dict(campaign_id=C_5G, theme_id="TH-COMM", role="related"),
    dict(campaign_id=C_5G, theme_id="TH-COMM-5G", role="main"),
    dict(campaign_id=C_5G, theme_id="TH-COMM-OPTICAL", role="related"),
    # ---- Cycle 2：AI 算力驱动的光模块 ----
    dict(campaign_id=C_AI, theme_id="TH-COMM", role="related"),
    dict(campaign_id=C_AI, theme_id="TH-COMM-OPTICAL", role="main"),
]

# campaign_phases 沿用既有 DB 枚举（startup/acceleration/main_rise/diffusion/
# retracement/secondary_rally/decline/unclear）；export 的 lifecycle[] 用研究层枚举，两者并存（F6）。
PHASES = [
    # ---- Cycle 1 ----
    dict(phase_id="PH-COMM-5G-01", campaign_id=C_5G, phase_type="startup",
         start_date="2019-06-06", end_date="2019-10-30",
         description="启动：工信部发放 5G 商用牌照（2019-06-06），5G 由试验转入商用。"),
    dict(phase_id="PH-COMM-5G-02", campaign_id=C_5G, phase_type="acceleration",
         start_date="2019-10-31", end_date="2020-02-20",
         description="加速：5G 商用正式启动（2019-10-31，三大运营商发布 5G 套餐）。"),
    dict(phase_id="PH-COMM-5G-03", campaign_id=C_5G, phase_type="main_rise",
         start_date="2020-02-21", end_date="2020-02-23",
         description="主升：中央政治局会议（02-21）与工信部会议（02-22）要求加快 5G 网络建设；"
                     "中国联通宣布提前一个季度完成全年基站目标（02-23）。"),
    dict(phase_id="PH-COMM-5G-04", campaign_id=C_5G, phase_type="diffusion",
         start_date="2020-02-24", end_date="2020-08-04",
         description="Peak Window（分批见顶）：中际旭创 02-24 / 中兴通讯 02-25 / 烽火通信 03-12 / "
                     "新易盛 07-14 / 天孚通信 08-04（通信主设备与中际旭创先见顶，数通光器件延后）。"),
    dict(phase_id="PH-COMM-5G-05", campaign_id=C_5G, phase_type="retracement",
         start_date="2020-08-05", end_date="2021-03-18",
         description="回撤：5G 资本开支预期兑现后回落；2021 上半年三大运营商 5G 资本开支均下滑。"),
    dict(phase_id="PH-COMM-5G-06", campaign_id=C_5G, phase_type="secondary_rally",
         start_date="2021-03-19", end_date="2021-12-31",
         description="次级反弹：中兴通讯 2021-08-04 反弹至 38.45（未创新高）；同期资本开支已见顶。"),
    dict(phase_id="PH-COMM-5G-07", campaign_id=C_5G, phase_type="decline",
         start_date="2022-01-01", end_date="2022-10-11",
         description="衰减与出清：5G 投资稳步下降（2021 年电信固定资产投资与上年基本持平），"
                     "代表标的至 2022-10-10/11 同步见底。"),
    # ---- Cycle 2 ----
    dict(phase_id="PH-COMM-AI-01", campaign_id=C_AI, phase_type="startup",
         start_date="2023-03-21", end_date="2023-05-23",
         description="启动：NVIDIA GTC 2023 主题演讲（2023-03-21，AI 算力叙事）；"
                     "A 股光模块次日（03-22）爆发（中际旭创 +21.97%）。"),
    dict(phase_id="PH-COMM-AI-02", campaign_id=C_AI, phase_type="acceleration",
         start_date="2023-05-24", end_date="2023-08-27",
         description="加速：NVIDIA Q1 FY2024 财报（2023-05-24），Q2 指引 110 亿美元，"
                     "较分析师预期高 53.2%，全球 AI 算力需求获财务确认。"),
    dict(phase_id="PH-COMM-AI-03", campaign_id=C_AI, phase_type="main_rise",
         start_date="2023-08-28", end_date="2024-10-07",
         description="主升：中际旭创 2023 半年报（08-28）确认下半年 800G 出货明显增长；"
                     "2024 年报/一季报业绩兑现（2023 年营收 107.18 亿元，+11.16%；2024Q1 净利润超 10 亿元）。"),
    dict(phase_id="PH-COMM-AI-04", campaign_id=C_AI, phase_type="diffusion",
         start_date="2024-10-08", end_date="2025-04-08",
         description="阶段高点后震荡：2024-10-08 代表标的同步出现阶段高点，随后回撤至 2025-04-08。"),
    dict(phase_id="PH-COMM-AI-05", campaign_id=C_AI, phase_type="main_rise",
         start_date="2025-04-09", end_date="2025-12-31",
         description="二次上行：1.6T 与 NPO/CPO 结构迁移预期推动，"
                     "中际旭创 2025-12-25 达 638.80、新易盛 2025-12-22 达 329.99；"
                     "至本地行情窗口末端仍在上行，Cycle End 未确认。"),
]

# --------------------------------------------------------- 5) Securities
SECURITIES = [
    dict(security_id="ZTE",        ticker="000063", name="中兴通讯",   exchange="SZ"),
    dict(security_id="FIBERHOME",  ticker="600498", name="烽火通信",   exchange="SH"),
    dict(security_id="INNOLIGHT",  ticker="300308", name="中际旭创",   exchange="SZ"),
    dict(security_id="EOPTOLINK",  ticker="300502", name="新易盛",     exchange="SZ"),
    dict(security_id="TFC",        ticker="300394", name="天孚通信",   exchange="SZ"),
    dict(security_id="ACCELINK",   ticker="002281", name="光迅科技",   exchange="SZ"),
]
CAMPAIGN_SECURITIES = [
    dict(campaign_id=C_5G, security_id="ZTE", role="leader"),
    dict(campaign_id=C_5G, security_id="FIBERHOME", role="leader"),
    dict(campaign_id=C_5G, security_id="INNOLIGHT", role="second_leader"),
    dict(campaign_id=C_5G, security_id="EOPTOLINK", role="second_leader"),
    dict(campaign_id=C_5G, security_id="TFC", role="representative"),
    dict(campaign_id=C_AI, security_id="INNOLIGHT", role="leader"),
    dict(campaign_id=C_AI, security_id="EOPTOLINK", role="leader"),
    dict(campaign_id=C_AI, security_id="TFC", role="second_leader"),
    dict(campaign_id=C_AI, security_id="ACCELINK", role="representative"),
]

# ------------------------------------------------------------ 6) Sources
SOURCES = [
    # ---- Setup（Cycle 1 之前）----
    dict(source_id="S-COMM-01", source_type="media_tier2", tier=2,
         title="美商务部禁止美企业向中兴通讯出口产品（激活拒绝令，7 年）",
         publisher="新华网", published_at="2018-04-17",
         url="https://www.xinhuanet.com/world/2018-04/17/c_1122694444.htm",
         description="2018-04-16 美国商务部发布声明，禁止美国企业在 7 年内向中兴通讯出口敏感产品；"
                     "构成 2018 年通信板块深跌的 Setup（早于本轮行情窗口，仅作 context）。"),
    # ---- Cycle 1 ----
    dict(source_id="S-COMM-02", source_type="regulator", tier=1,
         title="我国正式发放 5G 商用牌照（工信部向中国电信、中国移动、中国联通、中国广电发放）",
         publisher="新华社 / 中央网络安全和信息化委员会办公室", published_at="2019-06-06",
         url="https://www.cac.gov.cn/2019-06/06/c_1124591450.htm",
         description="工信部 2019-06-06 正式发放 5G 商用牌照，中国正式进入 5G 商用元年。"),
    dict(source_id="S-COMM-03", source_type="media_tier2", tier=2,
         title="5G 商用服务正式启动：工信部与三大运营商举行 5G 商用启动仪式并发布 5G 套餐",
         publisher="央视网", published_at="2019-10-31",
         url="https://news.cctv.com/2019/10/31/ARTIKAepIQmAJT4yIZhXjnNi191031.shtml",
         description="2019-10-31 工信部与三大运营商在 2019 年中国国际信息通信展览会上举行 5G 商用启动仪式，"
                     "5G 套餐 11-01 正式上线。"),
    dict(source_id="S-COMM-04", source_type="media_tier2", tier=2,
         title="中央政治局会议（02-21）与工信部加快推进 5G 发展会议（02-22）；中国联通宣布提前一季度完成全年基站目标",
         publisher="观察者网 / 中新经纬 / 中国经济网", published_at="2020-02-24",
         url="https://finance.ce.cn/stock/gsgdbd/202003/07/t20200307_34433827.shtml",
         description="2020-02-21 中央政治局会议提出推动 5G 网络等加快发展；02-22 工信部召开加快推进 5G 发展、"
                     "做好信息通信业复工复产工作会议；02-23 中国联通宣布三季度力争完成全国 25 万基站建设，"
                     "较原计划提前一个季度。02-24/25 中兴通讯连续涨停。"),
    dict(source_id="S-COMM-05", source_type="regulator", tier=1,
         title="中共中央政治局常务委员会会议：加快 5G 网络、数据中心等新型基础设施建设进度",
         publisher="中共中央政治局常务委员会", published_at="2020-03-04",
         url="https://www.cls.cn/detail/452051",
         description="2020-03-04 中央政治局常务委员会会议指出，要加快 5G 网络、数据中心等新型基础设施建设进度。"),
    dict(source_id="S-COMM-06", source_type="regulator", tier=1,
         title="2019 年通信业统计公报（工信部）",
         publisher="工业和信息化部 运行监测协调局", published_at="2020-02-27",
         url="https://www.miit.gov.cn/gxsj/tjfx/txy/art/2020/art_2d61a3d279ba4d53aa944359d20b8d7f.html",
         description="2019 年电信业务收入 1.31 万亿元（+0.8%）；三家基础电信企业和中国铁塔完成固定资产投资"
                     "比上年增长 4.7%（5G 相关投资快速增长推动），移动通信投资占比 47.3%；"
                     "新建光缆线路 434 万公里，总长 4750 万公里；净增移动电话基站 174 万个。"),
    dict(source_id="S-COMM-07", source_type="regulator", tier=1,
         title="2020 年通信业统计公报（工信部）",
         publisher="工业和信息化部 运行监测协调局", published_at="2021-01-22",
         url="https://www.miit.gov.cn/gxsj/tjfx/txy/art/2021/art_057a331667154aaaa6767018dfd79a4f.html",
         description="2020 年电信业务收入 1.36 万亿元（+3.6%）；固定资产投资 4072 亿元（+11%），"
                     "移动通信投资 2154 亿元（占 52.9%）；新建 5G 基站超 60 万个、累计开通超 71.8 万个；"
                     "数据中心业务收入 +22.2%、云计算 +85.8%。"),
    dict(source_id="S-COMM-08", source_type="regulator", tier=1,
         title="2021 年通信业统计公报（工信部）",
         publisher="工业和信息化部 运行监测协调局", published_at="2022-01-25",
         url="https://wap.miit.gov.cn/gxsj/tjfx/txy/art/2022/art_e8b64ba8f29d4ce18a1003c4f4d88234.html",
         description="2021 年电信业务收入 1.47 万亿元（+8.0%）；电信固定资产投资 4058 亿元，"
                     "**与上年基本持平**；5G 投资 1849 亿元（占 45.6%）；5G 基站 142.5 万个。"
                     "→ 运营商资本开支见顶的信号。"),
    dict(source_id="S-COMM-09", source_type="media_tier2", tier=2,
         title="三大运营商上半年 5G 资本开支均下滑",
         publisher="新浪财经", published_at="2021-08-25",
         url="https://finance.sina.com.cn/tech/2021-08-25/doc-ikqciyzm3520350.shtml",
         description="2021 年上半年三大运营商 5G 资本开支均下滑（中国联通资本开支 142.8 亿元，同比 -45%）。"),
    dict(source_id="S-COMM-10", source_type="regulator", tier=1,
         title="「东数西算」工程正式全面启动（国家发改委等四部门，八大算力枢纽）",
         publisher="国家发展改革委 / 中央网信办 / 工业和信息化部 / 国家能源局", published_at="2022-02-17",
         url="https://www.xiongan.gov.cn/2022-02/18/c_1211577024.htm",
         description="2022-02-17 四部门联合印发通知，同意在京津冀、长三角、粤港澳大湾区、成渝、内蒙古、"
                     "贵州、甘肃、宁夏 8 地启动建设国家算力枢纽节点，全国一体化大数据中心体系完成总体布局设计。"),
    # ---- Cycle 2 ----
    dict(source_id="S-COMM-11", source_type="media_tier2", tier=2,
         title="NVIDIA GTC 2023 主题演讲（黄仁勋发布 AI 推理芯片，称「人工智能的 iPhone 时刻」）",
         publisher="36氪 / 智源社区", published_at="2023-03-21",
         url="https://m.36kr.com/p/2181878738188803",
         description="北京时间 2023-03-21 23:00 NVIDIA GTC 2023 主题演讲，发布四款 AI 推理芯片及加速计算产品；"
                     "A 股光模块板块次日（2023-03-22）爆发（中际旭创 +21.97%）。"),
    dict(source_id="S-COMM-12", source_type="company_announcement", tier=1,
         title="NVIDIA Announces Financial Results for First Quarter Fiscal 2024（Q2 指引 110 亿美元）",
         publisher="NVIDIA Corporation（投资者关系官方新闻稿）", published_at="2023-05-24",
         url="https://investor.nvidia.com/news/press-release-details/2023/NVIDIA-Announces-Financial-Results-for-First-Quarter-Fiscal-2024/default.aspx",
         description="2023-05-24 NVIDIA 公布 FY2024 Q1（截至 2023-04-30）业绩：营收 71.92 亿美元，"
                     "数据中心营收创纪录 42.8 亿美元；Q2 营收指引 110 亿美元（±2%），"
                     "较分析师预期高 53.2%。黄仁勋称万亿美元规模数据中心将从通用计算转向加速计算。"),
    dict(source_id="S-COMM-13", source_type="company_announcement", tier=1,
         title="中际旭创 2023 年半年度报告（下半年 800G 光模块出货量明显增长）",
         publisher="中际旭创股份有限公司", published_at="2023-08-28",
         url="https://www.c114.com.cn/4app/3542/a1241253.html",
         description="2023 年半年报：报告期内营业收入约 40.04 亿元（同比 -5.37%），归母净利润约 6.14 亿元；"
                     "公司表示下半年 800G 光模块出货量明显增长。"),
    dict(source_id="S-COMM-14", source_type="company_announcement", tier=1,
         title="中际旭创 2023 年年度报告（营收 107.18 亿元，同比 +11.16%）",
         publisher="中际旭创股份有限公司", published_at="2024-04-21",
         url="https://baijiahao.baidu.com/s?id=1796984569138751490",
         description="2023 年实现营收 107.18 亿元（+11.16%），净利润大幅增长；2024Q1 净利润超 10 亿元。"
                     "800G、400G 等高端光模块产品出货增长驱动。"),
    dict(source_id="S-COMM-15", source_type="website", tier=3,
         title="腾讯财经 GTIMG 日线（raw + 前复权 qfq），信息通信代表标的 2018-01-02 ~ 2025-12-31",
         publisher="腾讯财经", published_at=None,
         url="https://gu.qq.com/",
         description="行情数据来源；本地复核见 research/data/market/normalized/"
                     "（ZTE / FIBERHOME / INNOLIGHT / EOPTOLINK / TFC / ACCELINK）。"),
]

# ---------------------------------------------------------- 7) Evidences
EVIDENCES = [
    # ---- Setup ----
    dict(evidence_id="E-COMM-01", source_id="S-COMM-01", date="2018-04-16",
         evidence_type="media",
         description=("美国商务部对中兴通讯激活拒绝令（7 年内禁止美国企业向其出口敏感产品）→ "
                      "2018 年中兴通讯 -49.0%、中际旭创 -33.8%、新易盛 -40.0%。"
                      "构成后续重估的低基数起点，本身不是正向驱动。"),
         evidence_role="context", confidence="high",
         independence_group="comm_geopolitics_zte_ban", temporal_relation="prior"),
    # ---- Cycle 1 ----
    dict(evidence_id="E-COMM-02", source_id="S-COMM-02", date="2019-06-06",
         evidence_type="政策文件",
         description=("工信部正式向中国电信、中国移动、中国联通、中国广电发放 5G 商用牌照，"
                      "中国进入 5G 商用元年 → 通信设备产业链进入建设周期。"),
         evidence_role="supporting", confidence="high",
         independence_group="comm_policy_5g_license", temporal_relation="contemporaneous"),
    dict(evidence_id="E-COMM-03", source_id="S-COMM-03", date="2019-10-31",
         evidence_type="media",
         description=("工信部与三大运营商举行 5G 商用启动仪式并发布 5G 套餐（11-01 正式上线）→ "
                      "5G 由「发牌」进入「面向用户商用」。"),
         evidence_role="supporting", confidence="high",
         independence_group="comm_policy_5g_commercial", temporal_relation="contemporaneous"),
    dict(evidence_id="E-COMM-04", source_id="S-COMM-06", date="2020-02-27",
         evidence_type="行业数据",
         description=("2019 年电信业务收入 1.31 万亿元（+0.8%）；三家基础电信企业和中国铁塔完成固定资产投资"
                      "比上年增长 4.7%（5G 相关投资快速增长推动）；新建光缆线路 434 万公里。"
                      "→ 投资侧验证 5G 建设已启动，但增速仍温和。"),
         evidence_role="supporting", confidence="high",
         independence_group="comm_industry_capex_2019", temporal_relation="subsequent"),
    dict(evidence_id="E-COMM-05", source_id="S-COMM-04", date="2020-02-22",
         evidence_type="media",
         description=("2020-02-21 中央政治局会议提出推动 5G 网络等加快发展；02-22 工信部召开加快推进 5G 发展"
                      "会议；02-23 中国联通宣布力争三季度完成全国 25 万基站建设（提前一个季度）。"
                      "→ 02-24/25 中兴通讯连续涨停，板块进入主升。"),
         evidence_role="supporting", confidence="high",
         independence_group="comm_policy_5g_speedup", temporal_relation="contemporaneous"),
    dict(evidence_id="E-COMM-06", source_id="S-COMM-05", date="2020-03-04",
         evidence_type="政策文件",
         description=("中央政治局常务委员会会议：加快 5G 网络、数据中心等新型基础设施建设进度。"
                      "→ 政策定调达到最高层级（但市场已在 02-24~03-12 批量见顶，属利好兑现）。"),
         evidence_role="supporting", confidence="high",
         independence_group="comm_policy_new_infra", temporal_relation="contemporaneous"),
    dict(evidence_id="E-COMM-07", source_id="S-COMM-07", date="2021-01-22",
         evidence_type="行业数据",
         description=("2020 年固定资产投资 4072 亿元（+11%），移动通信投资 2154 亿元（占 52.9%）；"
                      "新建 5G 基站超 60 万个、累计开通超 71.8 万个；数据中心业务 +22.2%、云计算 +85.8%。"
                      "→ 资本开支加速的年度确认。"),
         evidence_role="supporting", confidence="high",
         independence_group="comm_industry_capex_2020", temporal_relation="subsequent"),
    dict(evidence_id="E-COMM-08", source_id="S-COMM-08", date="2022-01-25",
         evidence_type="行业数据",
         description=("2021 年电信固定资产投资 4058 亿元，**与上年基本持平**；5G 投资 1849 亿元（占 45.6%）。"
                      "→ 运营商资本开支见顶，与板块 2021-2022 的持续走弱相互印证。"),
         evidence_role="contradicting", confidence="high",
         independence_group="comm_industry_capex_2021", temporal_relation="subsequent"),
    dict(evidence_id="E-COMM-09", source_id="S-COMM-09", date="2021-08-25",
         evidence_type="media",
         description=("2021 年上半年三大运营商 5G 资本开支均下滑（中国联通同比 -45%）→ "
                      "直接削弱 5G 设备需求预期。"),
         evidence_role="contradicting", confidence="high",
         independence_group="comm_industry_capex_cut", temporal_relation="contemporaneous"),
    dict(evidence_id="E-COMM-10", source_id="S-COMM-15", date="2020-02-25",
         evidence_type="行情数据",
         description=("代表标的行情复核（前复权）：中际旭创 2020-02-24 达区间高点 49.41；"
                      "中兴通讯 2020-02-25 达 52.30；烽火通信 2020-03-12 达 40.34；"
                      "新易盛 2020-07-14 达 20.01；天孚通信 2020-08-04 达 12.42 → "
                      "Peak Window 2020-02-24~2020-08-04（分批见顶）。"
                      "另：四者于 2022-10-10/11 同步见底（中兴 18.41 / 烽火 11.65 / "
                      "中际旭创 15.88 / 新易盛 6.33）。"),
         evidence_role="supporting", confidence="high",
         independence_group="comm_market_cycle1", temporal_relation="contemporaneous"),
    # ---- Cycle 2 ----
    dict(evidence_id="E-COMM-11", source_id="S-COMM-10", date="2022-02-17",
         evidence_type="政策文件",
         description=("「东数西算」工程正式全面启动，8 地建设国家算力枢纽节点 → "
                      "国内算力基础设施投资的新驱动萌芽（早于 Cycle 2 形成，记 context）。"),
         evidence_role="context", confidence="high",
         independence_group="comm_policy_east_data_west", temporal_relation="prior"),
    dict(evidence_id="E-COMM-12", source_id="S-COMM-11", date="2023-03-21",
         evidence_type="media",
         description=("NVIDIA GTC 2023 主题演讲发布 AI 推理芯片并称「人工智能的 iPhone 时刻」；"
                      "A 股光模块板块次日爆发（中际旭创 2023-03-22 +21.97%）→ "
                      "AI 算力叙事首次传导至光互联环节。"),
         evidence_role="supporting", confidence="high",
         independence_group="comm_ai_gtc2023", temporal_relation="contemporaneous"),
    dict(evidence_id="E-COMM-13", source_id="S-COMM-12", date="2023-05-24",
         evidence_type="行业数据",
         description=("NVIDIA FY2024 Q1 数据中心营收创纪录 42.8 亿美元，Q2 营收指引 110 亿美元"
                      "（较分析师预期高 53.2%）→ 全球 AI 算力资本开支获**财务确认**，"
                      "为光模块需求提供可验证的上游依据。"),
         evidence_role="supporting", confidence="high",
         independence_group="comm_ai_nvidia_guide", temporal_relation="contemporaneous"),
    dict(evidence_id="E-COMM-14", source_id="S-COMM-13", date="2023-08-28",
         evidence_type="行业数据",
         description=("中际旭创 2023 年半年报：营业收入约 40.04 亿元（-5.37%）、归母净利润约 6.14 亿元；"
                      "公司表示下半年 800G 光模块出货量明显增长 → 光模块环节的业绩兑现开始。"),
         evidence_role="supporting", confidence="high",
         independence_group="comm_company_innolight_h1", temporal_relation="contemporaneous"),
    dict(evidence_id="E-COMM-15", source_id="S-COMM-14", date="2024-04-21",
         evidence_type="行业数据",
         description=("中际旭创 2023 年年报：营收 107.18 亿元（+11.16%），净利润大幅增长；"
                      "2024Q1 净利润超 10 亿元 → 800G 放量在报表端确认。"),
         evidence_role="supporting", confidence="high",
         independence_group="comm_company_innolight_2023fy", temporal_relation="subsequent"),
    dict(evidence_id="E-COMM-16", source_id="S-COMM-15", date="2025-12-25",
         evidence_type="行情数据",
         description=("代表标的行情复核（前复权）：中际旭创 2025-12-25 达 638.80、"
                      "新易盛 2025-12-22 达 329.99 → 至本地行情窗口末端仍在上行，"
                      "Theme Cycle End 未确认。"),
         evidence_role="supporting", confidence="high",
         independence_group="comm_market_cycle2", temporal_relation="contemporaneous"),
]
CAMPAIGN_EVIDENCES = [
    dict(campaign_id=C_5G, evidence_id="E-COMM-01", role="context"),
    dict(campaign_id=C_5G, evidence_id="E-COMM-02", role="supporting"),
    dict(campaign_id=C_5G, evidence_id="E-COMM-03", role="supporting"),
    dict(campaign_id=C_5G, evidence_id="E-COMM-04", role="supporting"),
    dict(campaign_id=C_5G, evidence_id="E-COMM-05", role="supporting"),
    dict(campaign_id=C_5G, evidence_id="E-COMM-06", role="supporting"),
    dict(campaign_id=C_5G, evidence_id="E-COMM-07", role="supporting"),
    dict(campaign_id=C_5G, evidence_id="E-COMM-08", role="contradicting"),
    dict(campaign_id=C_5G, evidence_id="E-COMM-09", role="contradicting"),
    dict(campaign_id=C_5G, evidence_id="E-COMM-10", role="supporting"),
    dict(campaign_id=C_AI, evidence_id="E-COMM-11", role="context"),
    dict(campaign_id=C_AI, evidence_id="E-COMM-12", role="supporting"),
    dict(campaign_id=C_AI, evidence_id="E-COMM-13", role="supporting"),
    dict(campaign_id=C_AI, evidence_id="E-COMM-14", role="supporting"),
    dict(campaign_id=C_AI, evidence_id="E-COMM-15", role="supporting"),
    dict(campaign_id=C_AI, evidence_id="E-COMM-16", role="supporting"),
]

# ------------------------------------------------------------- 8) Events
EVENTS = [
    dict(event_id="EV-COMM-01", date="2018-04-16", event_type="policy", source_id="S-COMM-01",
         name="美国商务部对中兴通讯激活拒绝令（7 年出口禁运）",
         description="构成 2018 年通信板块深跌的 Setup 背景。"),
    dict(event_id="EV-COMM-02", date="2019-06-06", event_type="policy", source_id="S-COMM-02",
         name="工信部发放 5G 商用牌照（中国电信 / 中国移动 / 中国联通 / 中国广电）",
         description="中国进入 5G 商用元年。"),
    dict(event_id="EV-COMM-03", date="2019-10-31", event_type="policy", source_id="S-COMM-03",
         name="5G 商用启动仪式：三大运营商发布 5G 套餐",
         description="5G 由发牌进入面向用户的正式商用。"),
    dict(event_id="EV-COMM-04", date="2020-02-22", event_type="policy", source_id="S-COMM-04",
         name="工信部加快推进 5G 发展、做好信息通信业复工复产工作会议",
         description="要求加快 5G 商用步伐；02-23 中国联通宣布提前一季度完成全年基站目标。"),
    dict(event_id="EV-COMM-05", date="2020-03-04", event_type="policy", source_id="S-COMM-05",
         name="中央政治局常务委员会会议：加快 5G 网络、数据中心等新型基础设施建设进度",
         description="新基建政策定调达到最高层级。"),
    dict(event_id="EV-COMM-06", date="2022-02-17", event_type="policy", source_id="S-COMM-10",
         name="「东数西算」工程正式全面启动（8 地国家算力枢纽节点）",
         description="国内算力基础设施投资的新驱动。"),
    dict(event_id="EV-COMM-07", date="2023-03-21", event_type="industry", source_id="S-COMM-11",
         name="NVIDIA GTC 2023 主题演讲（AI 推理芯片 / 「人工智能的 iPhone 时刻」）",
         description="AI 算力叙事启动；A 股光模块次日爆发。"),
    dict(event_id="EV-COMM-08", date="2023-05-24", event_type="company", source_id="S-COMM-12",
         name="NVIDIA FY2024 Q1 财报：数据中心营收创纪录 42.8 亿美元，Q2 指引 110 亿美元",
         description="全球 AI 算力资本开支获财务确认。"),
    dict(event_id="EV-COMM-09", date="2023-08-28", event_type="company", source_id="S-COMM-13",
         name="中际旭创 2023 年半年报：下半年 800G 光模块出货量明显增长",
         description="光模块环节业绩兑现开始。"),
    dict(event_id="EV-COMM-10", date="2024-04-21", event_type="company", source_id="S-COMM-14",
         name="中际旭创 2023 年年报：营收 107.18 亿元（+11.16%），2024Q1 净利润超 10 亿元",
         description="800G 放量在报表端确认。"),
]
CAMPAIGN_EVENTS = [
    dict(campaign_id=C_5G, event_id="EV-COMM-01", role="context"),
    dict(campaign_id=C_5G, event_id="EV-COMM-02", role="trigger"),
    dict(campaign_id=C_5G, event_id="EV-COMM-03", role="catalyst"),
    dict(campaign_id=C_5G, event_id="EV-COMM-04", role="catalyst"),
    dict(campaign_id=C_5G, event_id="EV-COMM-05", role="catalyst"),
    dict(campaign_id=C_AI, event_id="EV-COMM-06", role="context"),
    dict(campaign_id=C_AI, event_id="EV-COMM-07", role="trigger"),
    dict(campaign_id=C_AI, event_id="EV-COMM-08", role="catalyst"),
    dict(campaign_id=C_AI, event_id="EV-COMM-09", role="catalyst"),
    dict(campaign_id=C_AI, event_id="EV-COMM-10", role="follow_up"),
]


def ins(table, rows):
    for r in rows:
        db.insert(conn, table, r)
    print(f"  {table:24s} +{len(rows)}")


def main():
    print("=== seed_comm_cycles.py（信息通信历史 Cycle — Wave 1B）===")
    ins("research_rules", RULES)
    ins("annual_reviews", ANNUAL)
    ins("themes", THEMES)
    ins("campaigns", CAMPAIGNS)
    ins("campaign_themes", CAMPAIGN_THEMES)
    ins("campaign_phases", PHASES)
    ins("securities", SECURITIES)
    ins("campaign_securities", CAMPAIGN_SECURITIES)
    ins("sources", SOURCES)
    ins("evidences", EVIDENCES)
    ins("campaign_evidences", CAMPAIGN_EVIDENCES)
    ins("events", EVENTS)
    ins("campaign_events", CAMPAIGN_EVENTS)
    conn.close()
    print("DONE")


if __name__ == "__main__":
    main()
