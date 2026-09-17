"""电力设备（Power Equipment）历史 Cycle 入库（Research 侧）— Wave 1A。

背景（Historical Coverage Audit v0.1 §12 Wave 1 P0）：
- 历史侧此前只有 `TH-AUTO` / `TH-PHARMA` 两个 Macro Theme，而 Current Candidate
  侧已声明 4 个（医药健康 / 电力设备 / 信息通信 / 高端装备）→ 3 个主题**无历史 Cycle 可类比**。
- 本脚本把「电力设备」接入 ThreeC 数据链路（Research → DB → Export → Timeline），
  使 `CC-2026-OFFSHORE-WIND` / `CC-2026-COMPUTE-POWER` 首次具备历史比较对象。

本轮纳入的 Historical Theme Cycle（**数量由证据决定，不为凑数制造 Cycle**）：

  1. `power_ne_equipment_2020_2022` — 双碳驱动的清洁能源发电设备重估
     （平价上网 Setup → 双碳 → 气候雄心 → 整县推进；Peak 2021-10-27~2021-11-04）
  2. `power_grid_uhv_2022_2025` — 电网投资与特高压第四轮建设
     （国网投资由降转升 → 利好兑现回撤 → 特高压密集开工 → 电网投资持续高增）

**Primary / Related 规则（本轮确立，用户 2026-09-17 决策）**：
- 每个 Theme Cycle 有且只有一个 Primary Macro Theme，用于 Theme Family 统计 /
  `theme_family_count` / Time Observation 独立样本计数 / Structural Analogy 跨族独立性。
- 一个 Cycle 可有多个 related macro themes，但 **Related 不增加独立样本数**。
- **实现约束（实测）**：CMTR v1 对对象 `themes[]` **全量**解析根节点，
  且 `discover_time_observation_patterns.py` 取 `theme_family_id = fam_ids[0] if len(fam_ids)==1 else None`
  → **一个 Campaign 若挂接 ≥2 个 Macro root，将被判 CONFLICT 且 `theme_family_id=None`（不计入任何族）**。
  因此 Related Macro Theme **不写进 `campaign_themes`**，改在研究层文档（drivers / research_notes /
  本轮报告）中记录。**未修改 schema / export contract / Product。**

纪律：
- 不修改 `schema/schema.sql` / `contracts/` / export contract / `src/` / Timeline UI / Research Model。
- 不新增数据库实体 / 新表 / 新列（仅新增数据行）。
- 日期：Campaign `start_date` = `EARLY_SIGNAL`（与既有 9 个 Campaign 一致）；
  Peak / 区间来自本地真实行情复核（`research/data/market/normalized/*.csv`，腾讯 GTIMG 前复权）。
- 不伪造：取不到的日期留 NULL / 写 unknown；不计算 seasonality / win_rate / probability。
- `evidence_type` 沿用仓库既有可归一化取值（`政策文件`/`行业数据`/`行情数据`/`media`），
  对应 `audit_historical_coverage.py` 的 canonical 类别 policy/industry/market/information。
- 幂等：全部 `db.insert`（INSERT OR REPLACE），可重复运行。

用法: python scripts/seed_power_equipment.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

conn = db.connect()
db.migrate(conn)

RULE = "rule_power_equipment"
C_NE = "C-2020-POWER-NE"        # 清洁能源发电设备（光伏/风电）
C_GRID = "C-2022-POWER-GRID"    # 电网投资与特高压

# ------------------------------------------------------------------ 1) Rule
RULES = [
    dict(rule_id=RULE, name="电力设备历史周期观察", base_pattern="电力设备",
         description=("历史观察窗口：电力设备（新能源发电设备 / 电网输配电设备）"
                      "在政策与投资周期驱动下形成的结构性行情。"
                      "非固定买入窗口，不构成交易建议。"),
         source_id=None, status="under_review"),
]

# ------------------------------------------------------- 2) Annual Reviews
ANNUAL = [
    dict(annual_review_id="AR-PWR-2018", rule_id=RULE, year=2018, status="weak",
         summary=("531 新政（发改能源〔2018〕823 号）补贴急刹 → 光伏板块深度出清："
                  "隆基绿能 -33.6%、阳光电源 -73.9%、金风科技 -49.0%。无正向 Campaign。")),
    dict(annual_review_id="AR-PWR-2019", rule_id=RULE, year=2019, status="medium",
         summary=("平价上网元年（发改能源〔2019〕19 号）→ 板块自 2019-01 低点修复："
                  "隆基绿能 +85.7%。属 Cycle 1 的 Setup 段，未独立成 Campaign。")),
    dict(annual_review_id="AR-PWR-2020", rule_id=RULE, year=2020, status="strong",
         summary=("双碳目标宣布（2020-09-22）+ 气候雄心峰会（12 亿千瓦，2020-12-12）"
                  "→ 清洁能源发电设备重估：隆基绿能 +270.5%、阳光电源 +1034.6%。")),
    dict(annual_review_id="AR-PWR-2021", rule_id=RULE, year=2021, status="strong",
         summary=("整县推进分布式光伏（2021-06 / 09 名单 676 县）+ 硅料价格暴涨挤压中下游利润；"
                  "10 月末~11 月初批量见顶（阳光电源 10-27 / 隆基 11-01 / 金风 11-04）。")),
    dict(annual_review_id="AR-PWR-2022", rule_id=RULE, year=2022, status="weak",
         summary=("光伏出清（隆基 -30.4% / 金风 -32.3%）；电网侧虽投资计划创新高，"
                  "但 1 月利好兑现后回撤（国电南瑞 -25.5% / 许继电气 -20.7%）。")),
    dict(annual_review_id="AR-PWR-2023", rule_id=RULE, year=2023, status="medium",
         summary=("电网投资完成 5275 亿元（+5.4%）；特高压进入密集开工期（首个沙戈荒外送"
                  "特高压 06-11 开工）。平高电气 +62.8%，电网设备显著强于发电设备。")),
    dict(annual_review_id="AR-PWR-2024", rule_id=RULE, year=2024, status="strong",
         summary=("电网工程投资完成 6083 亿元（+15.3%），国家电网投资首超 6000 亿元、"
                  "累计建成「22 交 16 直」38 项特高压。平高电气 +57.7% / 许继电气 +28.4% / "
                  "国电南瑞 +18.6%，2024-07~10 批量见顶。")),
    dict(annual_review_id="AR-PWR-2025", rule_id=RULE, year=2025, status="medium",
         summary=("分化：特变电工 +86.0%（输变电出海），而平高电气 -2.8% / 国电南瑞 -5.0% "
                  "高位震荡。Theme Cycle End 未确认（本地行情窗口止于 2025-12-31）。")),
]

# ------------------------------------------------------------- 3) Themes
# 用户 2026-09-17 决策：本轮**新建 Macro Theme root「电力设备」**；
# 只建立 root + **被实际引用所必需**的最小 Sub-theme 集（不做完整子主题树）。
THEMES = [
    dict(theme_id="TH-POWER", name="电力设备", theme_type="industry", parent_theme_id=None,
         description=("Macro Theme（Wave 1A 新建）。与 Current Candidate 侧 "
                      "`CC-2026-OFFSHORE-WIND` / `CC-2026-COMPUTE-POWER` 声明的 "
                      "macro_theme=\"电力设备\" 精确对齐（Similarity 的 Pattern 层按名称精确匹配）。")),
    dict(theme_id="TH-POWER-PV", name="光伏/新能源发电设备", theme_type="concept",
         parent_theme_id="TH-POWER",
         description="Sub-theme：光伏产业链（硅料/硅片/电池/组件/逆变器）与平价上网后的发电设备重估。"),
    dict(theme_id="TH-POWER-WIND", name="风电设备", theme_type="concept",
         parent_theme_id="TH-POWER",
         description="Sub-theme：风电整机与零部件（气候雄心峰会 12 亿千瓦目标同时覆盖风电与太阳能）。"),
    dict(theme_id="TH-POWER-GRID", name="电网/输变电设备", theme_type="concept",
         parent_theme_id="TH-POWER",
         description=("Sub-theme：特高压 / 直流输电 / 高压开关 / 电网自动化与配网设备，"
                      "驱动为电网工程投资与特高压建设节奏。")),
]

# ---------------------------------------------------------- 4) Campaigns
CAMPAIGNS = [
    dict(
        campaign_id=C_NE,
        annual_review_id="AR-PWR-2020",
        rule_id=RULE,
        season_id="power_ne_2020_2022",
        campaign_year=2020,
        start_date="2020-09-22",      # = EARLY_SIGNAL（双碳目标宣布）
        end_date="2022-12-30",        # 本地行情窗口末端（Cycle End 未确认）
        peak_date="2021-11-01",       # 隆基绿能自身区间高点；Peak Window 见 research_notes
        strength="strong",
        result="positive",
        classification="theme_campaign",
        start_date_basis="official_event",
        end_date_basis="market_data",
        date_confidence="medium",
        description=("双碳驱动的清洁能源发电设备重估：政策路径为"
                     "「平价上网（2019 Setup）→ 双碳目标（2020-09-22）→ 气候雄心峰会 12 亿千瓦"
                     "（2020-12-12）→ 整县推进分布式光伏（2021-06 / 09 名单 676 县）」。"
                     "代表标的：隆基绿能（硅片/组件）、阳光电源（逆变器）、金风科技（风电整机）。"),
        research_notes=("跨年 Campaign（2020-09-22 ~ 2022-12-30，约 2.3 年）。"
                        "Peak 口径按 Theme/Campaign Separation v1.1 §6 使用 Campaign 自身代表标的："
                        "阳光电源 2021-10-27（119.98）、隆基绿能 2021-11-01（70.82）、"
                        "金风科技 2021-11-04（19.75）→ Peak Window 2021-10-27~2021-11-04（DATE_WINDOW）。"
                        "主跌段结束于 2022-04-26（隆基 39.68 / 阳光 37.65 / 金风 9.45 同步低点，"
                        "与大盘 4 月底同步，含显著 β）；2022-04-27~2022-08-23 阳光电源出现次级反弹"
                        "（2022-08-23 100.12）→ 记 SECONDARY。"
                        "★ 上游分化：硅料环节延后至 2022-07-05 见顶（特变电工自身区间高点 21.97，"
                        "由其控股子公司新特能源多晶硅驱动），与中下游 2021-11 见顶不同步，"
                        "属同一 Cycle 内的环节错位，不另立 Cycle。"
                        "（通威股份 sh600438 因腾讯前复权序列在 2018 年返回非正价格，"
                        "按「不写入已知损坏数据」纪律未登记，见 fetch_market_power.py 注释。）"
                        "★ Related Macro Theme：无（本 Cycle 核心为发电设备，非汽车族）。"),
    ),
    dict(
        campaign_id=C_GRID,
        annual_review_id="AR-PWR-2022",
        rule_id=RULE,
        season_id="power_grid_2022_2025",
        campaign_year=2022,
        start_date="2022-01-10",      # = EARLY_SIGNAL（特高压核准提速）
        end_date="2025-12-31",        # 本地行情窗口末端（Cycle End 未确认）
        peak_date="2024-10-08",       # 国电南瑞自身区间高点；Peak Window 见 research_notes
        strength="strong",
        result="positive",
        classification="industry_trend",
        start_date_basis="official_event",
        end_date_basis="market_data",
        date_confidence="medium",
        description=("电网投资与特高压第四轮建设：政策路径为"
                     "「特高压核准提速（2022-01-10）→ 国网年度工作会议 5012 亿元投资计划"
                     "（2022-01-16）→ 再开工 8 项特高压、在建项目投资破万亿（2022-08-03）→ "
                     "电网投资连续高增（2023 年 5275 亿 / 2024 年 6083 亿，+15.3%）」。"
                     "代表标的：国电南瑞（电网自动化）、许继电气（直流输电）、平高电气（高压开关）。"),
        research_notes=("跨年 Campaign（2022-01-10 ~ 2025-12-31，约 4.0 年）。"
                        "★ 2022-01 利好兑现回撤：政策信号披露后三大代表标的同步见顶回落"
                        "（国电南瑞 2022-01-19 / 许继电气 2022-01-19 / 平高电气 2022-01-18），"
                        "至 2022-04-25~26 同步见底 → 记 RETRACEMENT，未隐藏。"
                        "★ Peak Window 2024-07-09~2024-10-14（许继电气 07-09 34.17、"
                        "国电南瑞 10-08 26.71、平高电气 10-14 20.54）。"
                        "★ 环节错位（不另立 Cycle）：出海暴露较高的思源电气（2025-12-26 160.30）与"
                        "特变电工（2025-11-07 26.14）延后至 2025 年见顶，而特高压国内标的 2024-10 即见顶；"
                        "同属「电网投资」驱动下的结构分化，本轮按单一 Cycle 处理并显式记录。"
                        "★ 特变电工（600089）作为代表标的时**存在混淆**：其 2022-07-05 高点由"
                        "控股子公司新特能源（多晶硅）驱动，与纯电网设备节奏不同；"
                        "本轮保留为 representative 并显式标注该混淆，未据此判定 Peak。"
                        "★ Related Macro Theme：无。本 Cycle 驱动为电网投资，与汽车族无交叉。"),
    ),
]

CAMPAIGN_THEMES = [
    # ---- Cycle 1：清洁能源发电设备 ----
    # Macro Theme 行沿用既有约定 role='related' + theme_type='industry'
    # （Product 侧 macroThemeOf() 正是按 role='related' && theme_type∈{industry,sector} 读取）
    dict(campaign_id=C_NE, theme_id="TH-POWER", role="related"),
    dict(campaign_id=C_NE, theme_id="TH-POWER-PV", role="main"),
    dict(campaign_id=C_NE, theme_id="TH-POWER-WIND", role="related"),
    # ---- Cycle 2：电网/输变电设备 ----
    dict(campaign_id=C_GRID, theme_id="TH-POWER", role="related"),
    dict(campaign_id=C_GRID, theme_id="TH-POWER-GRID", role="main"),
]

# campaign_phases 沿用既有 DB 枚举（startup/acceleration/main_rise/diffusion/
# retracement/secondary_rally/decline/unclear）；export 的 lifecycle[] 用研究层枚举，两者并存（F6）。
PHASES = [
    # ---- Cycle 1 ----
    dict(phase_id="PH-PWR-NE-01", campaign_id=C_NE, phase_type="startup",
         start_date="2020-09-22", end_date="2020-12-11",
         description="启动：第 75 届联大宣布 2030 碳达峰 / 2060 碳中和（2020-09-22）。"),
    dict(phase_id="PH-PWR-NE-02", campaign_id=C_NE, phase_type="acceleration",
         start_date="2020-12-12", end_date="2021-06-19",
         description="加速：气候雄心峰会明确 2030 年风电、太阳能发电总装机 12 亿千瓦以上（2020-12-12）。"),
    dict(phase_id="PH-PWR-NE-03", campaign_id=C_NE, phase_type="main_rise",
         start_date="2021-06-20", end_date="2021-10-26",
         description="主升：整县（市、区）屋顶分布式光伏试点推进（2021-06 通知 / 09-08 名单 676 县）。"),
    dict(phase_id="PH-PWR-NE-04", campaign_id=C_NE, phase_type="diffusion",
         start_date="2021-10-27", end_date="2021-11-04",
         description="Peak Window（批量见顶）：阳光电源 10-27 / 隆基绿能 11-01 / 金风科技 11-04。"),
    dict(phase_id="PH-PWR-NE-05", campaign_id=C_NE, phase_type="retracement",
         start_date="2021-11-05", end_date="2022-04-26",
         description="回撤：硅料价格暴涨挤压中下游利润 + 高估值消化 + 大盘 β（2022-04-25/26 同步见底）。"),
    dict(phase_id="PH-PWR-NE-06", campaign_id=C_NE, phase_type="secondary_rally",
         start_date="2022-04-27", end_date="2022-08-23",
         description="次级反弹：阳光电源自 2022-04-26 低点反弹至 2022-08-23（100.12）；隆基未同步。"),
    dict(phase_id="PH-PWR-NE-07", campaign_id=C_NE, phase_type="decline",
         start_date="2022-08-24", end_date="2022-12-30",
         description="衰减：板块整体下行至本地行情窗口末端；Theme Cycle End 未确认。"),
    # ---- Cycle 2 ----
    dict(phase_id="PH-PWR-GRID-01", campaign_id=C_GRID, phase_type="startup",
         start_date="2022-01-10", end_date="2022-01-19",
         description="启动：特高压核准提速（2022-01-10 报道）+ 国网 2022 年度工作会议 5012 亿元电网投资计划（2022-01-16）。"),
    dict(phase_id="PH-PWR-GRID-02", campaign_id=C_GRID, phase_type="retracement",
         start_date="2022-01-20", end_date="2022-04-26",
         description="利好兑现回撤：三大代表标的同步回落（国电南瑞/许继电气 01-19、平高电气 01-18 见顶）至 2022-04-25/26。"),
    dict(phase_id="PH-PWR-GRID-03", campaign_id=C_GRID, phase_type="acceleration",
         start_date="2022-04-27", end_date="2022-12-31",
         description="加速：国网披露年内再开工 8 项特高压、在建项目投资突破万亿（2022-08-03）。"),
    dict(phase_id="PH-PWR-GRID-04", campaign_id=C_GRID, phase_type="main_rise",
         start_date="2023-01-01", end_date="2024-07-08",
         description="主升：电网投资连续高增（2023 年 5275 亿 +5.4%；2024 年 6083 亿 +15.3%），特高压密集开工。"),
    dict(phase_id="PH-PWR-GRID-05", campaign_id=C_GRID, phase_type="diffusion",
         start_date="2024-07-09", end_date="2024-10-14",
         description="Peak Window：许继电气 2024-07-09 / 国电南瑞 2024-10-08 / 平高电气 2024-10-14。"),
    dict(phase_id="PH-PWR-GRID-06", campaign_id=C_GRID, phase_type="decline",
         start_date="2024-10-15", end_date="2025-12-31",
         description="衰减：高位震荡回落至本地行情窗口末端；Theme Cycle End 未确认。"),
]

# --------------------------------------------------------- 5) Securities
SECURITIES = [
    dict(security_id="LONGI",    ticker="601012", name="隆基绿能",   exchange="SH"),
    dict(security_id="SUNGROW",  ticker="300274", name="阳光电源",   exchange="SZ"),
    dict(security_id="GOLDWIND", ticker="002202", name="金风科技",   exchange="SZ"),
    dict(security_id="NARI",     ticker="600406", name="国电南瑞",   exchange="SH"),
    dict(security_id="XUJI",     ticker="000400", name="许继电气",   exchange="SZ"),
    dict(security_id="PINGGAO",  ticker="600312", name="平高电气",   exchange="SH"),
    dict(security_id="SIEYUAN",  ticker="002028", name="思源电气",   exchange="SZ"),
    dict(security_id="TBEA",     ticker="600089", name="特变电工",   exchange="SH"),
]
CAMPAIGN_SECURITIES = [
    dict(campaign_id=C_NE, security_id="LONGI", role="leader"),
    dict(campaign_id=C_NE, security_id="SUNGROW", role="leader"),
    dict(campaign_id=C_NE, security_id="GOLDWIND", role="second_leader"),
    dict(campaign_id=C_GRID, security_id="NARI", role="leader"),
    dict(campaign_id=C_GRID, security_id="XUJI", role="leader"),
    dict(campaign_id=C_GRID, security_id="PINGGAO", role="second_leader"),
    dict(campaign_id=C_GRID, security_id="SIEYUAN", role="representative"),
    # 保留并显式标注混淆：特变电工 2022-07-05 高点由多晶硅（新特能源）驱动
    dict(campaign_id=C_GRID, security_id="TBEA", role="representative"),
]

# ------------------------------------------------------------ 6) Sources
SOURCES = [
    # ---- Cycle 1（清洁能源发电设备）----
    dict(source_id="S-PWR-01", source_type="regulator", tier=1,
         title="国家主席习近平在第七十五届联合国大会一般性辩论上的讲话（宣布 2030 碳达峰 / 2060 碳中和）",
         publisher="新华社（国家主席讲话）", published_at="2020-09-22",
         url="https://world.huanqiu.com/article/3zzx6TNlCFN",
         description="官方宣布：中国将提高国家自主贡献力度，力争 2030 年前二氧化碳排放达到峰值，努力争取 2060 年前实现碳中和。"),
    dict(source_id="S-PWR-02", source_type="regulator", tier=1,
         title="国家主席习近平在气候雄心峰会上的讲话（风电、太阳能发电总装机容量将达到 12 亿千瓦以上）",
         publisher="新华社（求是网全文）", published_at="2020-12-12",
         url="https://www.qstheory.cn/yaowen/2020-12/13/c_1126854050.htm",
         description="进一步宣布：到 2030 年单位 GDP 二氧化碳排放比 2005 年下降 65% 以上，非化石能源占一次能源消费比重达 25% 左右，风电、太阳能发电总装机容量达 12 亿千瓦以上。"),
    dict(source_id="S-PWR-03", source_type="regulator", tier=1,
         title="国家能源局综合司关于公布整县（市、区）屋顶分布式光伏开发试点名单的通知（国能综通新能〔2021〕84 号）",
         publisher="国家能源局综合司", published_at="2021-09-08",
         url="https://www.gov.cn/zhengce/zhengceku/2021-09/15/content_5637323.htm",
         description="共报送试点县（市、区）676 个全部列为整县屋顶分布式光伏开发试点；2023 年底前达标者列为示范县。正文载明 2021 年 6 月已印发《关于报送整县（市、区）屋顶分布式光伏开发试点方案的通知》。"),
    dict(source_id="S-PWR-04", source_type="regulator", tier=1,
         title="国家发展改革委 国家能源局关于积极推进风电、光伏发电无补贴平价上网有关工作的通知（发改能源〔2019〕19 号）",
         publisher="国家发展改革委 / 国家能源局", published_at="2019-01-07",
         url="https://www.nea.gov.cn/2019-01/10/c_137731320.htm",
         description="推进无补贴平价上网试点，不受年度建设规模限制；省级电网企业承担收购责任并按项目核准时煤电标杆上网电价签订不少于 20 年长期固定电价购售电合同。"),
    dict(source_id="S-PWR-05", source_type="regulator", tier=1,
         title="国家发展改革委 财政部 国家能源局关于 2018 年光伏发电有关事项的通知（发改能源〔2018〕823 号，531 新政）",
         publisher="国家发展改革委 / 财政部 / 国家能源局", published_at="2018-05-31",
         url="https://www.gov.cn/zhengce/zhengceku/2018-12/31/content_5433580.htm",
         description="加快补贴退坡、合理把握发展节奏；构成 2018 年光伏板块深度出清的 Setup 背景（早于本轮行情窗口，仅作 context）。"),
    dict(source_id="S-PWR-06", source_type="regulator", tier=1,
         title="国家能源局：2021 年光伏发电并网装机 5300 万千瓦，分布式占比首次过半",
         publisher="国家能源局", published_at="2022-01-20",
         url="https://m.thepaper.cn/newsDetail_forward_16373085",
         description="2021 年新增光伏发电并网装机约 5300 万千瓦，连续 9 年居世界首位；分布式约 2900 万千瓦、占新增 55%，历史上首次突破 50%；累计并网装机达 3.06 亿千瓦。"),
    dict(source_id="S-PWR-07", source_type="website", tier=3,
         title="腾讯财经 GTIMG 日线（raw + 前复权 qfq），电力设备代表标的 2018-01-02 ~ 2025-12-31",
         publisher="腾讯财经", published_at=None,
         url="https://gu.qq.com/",
         description="行情数据来源；本地复核见 research/data/market/normalized/（LONGI / SUNGROW / GOLDWIND / NARI / XUJI / PINGGAO / SIEYUAN / TBEA）。"),
    # ---- Cycle 2（电网投资与特高压）----
    dict(source_id="S-PWR-08", source_type="media_tier2", tier=2,
         title="特高压建设迎来新一轮提速期（2022 年特高压项目核准提速）",
         publisher="中国能源报（人民日报社）", published_at="2022-01-10",
         url="https://paper.people.com.cn/zgnybwap/html/2022-01/10/content_25898336.htm",
         description="报道称 2022 年特高压项目核准提速、规划项目有望全部核准，未来四年特高压建设规模空前。"),
    dict(source_id="S-PWR-09", source_type="media_tier2", tier=2,
         title="国家电网：2022 年计划电网投资金额达 5012 亿元（2022 年度工作会议）",
         publisher="中国证券报", published_at="2022-01-16",
         url="https://www.cs.com.cn/sylm/jsbd/202201/t20220116_6235739.html",
         description="国网董事长辛保安在 2022 年度工作会议指出：2022 年计划发展总投入 5795 亿元，其中电网投资 5012 亿元。"),
    dict(source_id="S-PWR-10", source_type="media_tier2", tier=2,
         title="国家电网将再开工 8 项特高压工程，年内在建项目投资突破万亿",
         publisher="澎湃新闻（中新网转载）", published_at="2022-08-03",
         url="https://www.chinanews.com.cn/cj/2022/08-03/9819005.shtml",
         description="2022 年 1-7 月完成电网投资 2364 亿元（+19%），在建项目总投资 8832 亿元；年内计划陆续开工「四交四直」8 项特高压工程，总投资超 1500 亿元；全年电网投资将达约 5300 亿元，创历史最高。"),
    dict(source_id="S-PWR-11", source_type="regulator", tier=1,
         title="国家能源局发布 2022 年全国电力工业统计数据",
         publisher="国家能源局", published_at="2023-01-18",
         url="https://www.nea.gov.cn/2023-01/18/c_1310691509.htm",
         description="截至 2022 年 12 月底全国累计发电装机约 25.6 亿千瓦（+7.8%），其中风电 3.7 亿千瓦（+11.2%）、太阳能 3.9 亿千瓦（+28.1%）；电网工程建设投资完成 5012 亿元（+2.0%）。"),
    dict(source_id="S-PWR-12", source_type="regulator", tier=1,
         title="国家能源局发布 2023 年全国电力工业统计数据",
         publisher="国家能源局", published_at="2024-01-26",
         url="https://www.nea.gov.cn/2024-01/26/c_1310762246.htm",
         description="截至 2023 年 12 月底全国累计发电装机约 29.2 亿千瓦（+13.9%），其中太阳能 6.1 亿千瓦（+55.2%）、风电 4.4 亿千瓦（+20.7%）；电网工程建设投资完成 5275 亿元（+5.4%）。"),
    dict(source_id="S-PWR-13", source_type="regulator", tier=1,
         title="国家能源局发布 2024 年全国电力工业统计数据",
         publisher="国家能源局", published_at="2025-01-21",
         url="https://www.nea.gov.cn/20250121/097bfd7c1cd3498897639857d86d5dac/c.html",
         description="截至 2024 年 12 月底全国累计发电装机约 33.5 亿千瓦（+14.6%），其中太阳能 8.9 亿千瓦（+45.2%）、风电 5.2 亿千瓦（+18.0%）；电网工程投资完成 6083 亿元（+15.3%）。"),
    dict(source_id="S-PWR-14", source_type="media_tier2", tier=2,
         title="2024 年国家电网投资首超 6000 亿元，累计建成「22 交 16 直」38 项特高压工程",
         publisher="人民日报", published_at="2025-02-12",
         url="http://www.nc.sgcc.com.cn/zxzx/mtjj/2025/03/469533.shtml",
         description="2024 年国家电网投资首次超过 6000 亿元，建成投运 3 项特高压工程，累计建成「22 交 16 直」38 项特高压工程。"),
    dict(source_id="S-PWR-15", source_type="media_tier2", tier=2,
         title="2023 年特高压工程核准、开工、投运年终盘点（首个「沙戈荒」外送特高压 2023-06-11 开工）",
         publisher="北极星电力网 / 中国智能电网", published_at="2023-12-27",
         url="https://news.bjx.com.cn/html/20231227/1352575.shtml",
         description="2023 年 6 月 11 日，我国首个「沙戈荒」风光电基地外送电特高压工程——宁夏—湖南 ±800 千伏特高压直流输电工程开工。"),
]

# ---------------------------------------------------------- 7) Evidences
EVIDENCES = [
    # ---- Cycle 1 ----
    dict(evidence_id="E-PWR-01", source_id="S-PWR-01", date="2020-09-22",
         evidence_type="政策文件",
         description=("第 75 届联大一般性辩论：中国宣布力争 2030 年前二氧化碳排放达峰、2060 年前实现碳中和。"
                      "构成清洁能源发电设备重估的政策起点（双碳目标）。"),
         evidence_role="supporting", confidence="high",
         independence_group="pwr_policy_double_carbon", temporal_relation="contemporaneous"),
    dict(evidence_id="E-PWR-02", source_id="S-PWR-02", date="2020-12-12",
         evidence_type="政策文件",
         description=("气候雄心峰会：到 2030 年风电、太阳能发电总装机容量将达到 12 亿千瓦以上；"
                      "非化石能源占一次能源消费比重达 25% 左右。首次给出可量化的装机目标。"),
         evidence_role="supporting", confidence="high",
         independence_group="pwr_policy_capacity_target", temporal_relation="contemporaneous"),
    dict(evidence_id="E-PWR-03", source_id="S-PWR-03", date="2021-09-08",
         evidence_type="政策文件",
         description=("整县（市、区）屋顶分布式光伏开发试点名单公布：676 个县（市、区）全部列为试点，"
                      "2023 年底前达标者列为示范县。分布式光伏由地方试点上升为全国性推进机制。"),
         evidence_role="supporting", confidence="high",
         independence_group="pwr_policy_county_pv", temporal_relation="contemporaneous"),
    dict(evidence_id="E-PWR-04", source_id="S-PWR-06", date="2022-01-20",
         evidence_type="行业数据",
         description=("2021 年新增光伏并网装机约 5300 万千瓦（连续 9 年世界首位），分布式约 2900 万千瓦、"
                      "占新增 55%（首次过半）；累计并网 3.06 亿千瓦。装机侧验证政策已传导至实际建设。"),
         evidence_role="supporting", confidence="high",
         independence_group="pwr_industry_install", temporal_relation="subsequent"),
    dict(evidence_id="E-PWR-05", source_id="S-PWR-07", date="2021-11-01",
         evidence_type="行情数据",
         description=("代表标的行情复核（前复权）：阳光电源 2021-10-27 达区间高点 119.98；"
                      "隆基绿能 2021-11-01 达 70.82；金风科技 2021-11-04 达 19.75 → Peak Window "
                      "2021-10-27~2021-11-04。此前 2019-01-02（隆基 6.24）为本轮起点低点。"),
         evidence_role="supporting", confidence="high",
         independence_group="pwr_market_cycle1", temporal_relation="contemporaneous"),
    dict(evidence_id="E-PWR-06", source_id="S-PWR-04", date="2019-01-07",
         evidence_type="政策文件",
         description=("风电、光伏无补贴平价上网试点通知（发改能源〔2019〕19 号）：平价项目不受年度建设规模限制，"
                      "并签订不少于 20 年固定电价购售电合同。构成 Theme Cycle 的 Setup 背景（早于行情窗口）。"),
         evidence_role="context", confidence="high",
         independence_group="pwr_policy_parity", temporal_relation="prior"),
    dict(evidence_id="E-PWR-07", source_id="S-PWR-05", date="2018-05-31",
         evidence_type="政策文件",
         description=("531 新政（发改能源〔2018〕823 号）加快补贴退坡 → 2018 年光伏板块深度出清"
                      "（隆基绿能当年 -33.6%、阳光电源 -73.9%、金风科技 -49.0%）。"
                      "构成后续重估的低基数起点，本身不是正向驱动。"),
         evidence_role="context", confidence="high",
         independence_group="pwr_policy_531", temporal_relation="prior"),
    # ---- Cycle 2 ----
    dict(evidence_id="E-PWR-08", source_id="S-PWR-08", date="2022-01-10",
         evidence_type="media",
         description=("报道：2022 年特高压项目核准提速、规划项目有望全部核准，未来四年特高压建设规模空前。"
                      "为电网投资周期转向上行的最早公开信号。"),
         evidence_role="supporting", confidence="medium",
         independence_group="pwr_policy_uhv_speedup", temporal_relation="contemporaneous"),
    dict(evidence_id="E-PWR-09", source_id="S-PWR-09", date="2022-01-16",
         evidence_type="行业数据",
         description=("国家电网 2022 年度工作会议：2022 年计划发展总投入 5795 亿元，其中电网投资 5012 亿元。"
                      "电网投资由 2019 年 4473 亿 / 2021 年 4882 亿转为上行。"),
         evidence_role="supporting", confidence="high",
         independence_group="pwr_grid_plan_2022", temporal_relation="contemporaneous"),
    dict(evidence_id="E-PWR-10", source_id="S-PWR-10", date="2022-08-03",
         evidence_type="行业数据",
         description=("国网披露：2022 年 1-7 月完成电网投资 2364 亿元（+19%），在建项目总投资 8832 亿元；"
                      "年内计划陆续开工「四交四直」8 项特高压工程（总投资超 1500 亿元），"
                      "全年电网投资将达约 5300 亿元创历史最高。"),
         evidence_role="supporting", confidence="high",
         independence_group="pwr_grid_uhv_8", temporal_relation="contemporaneous"),
    dict(evidence_id="E-PWR-11", source_id="S-PWR-11", date="2023-01-18",
         evidence_type="行业数据",
         description=("2022 年全国电网工程建设投资完成 5012 亿元（+2.0%）；风电装机 3.7 亿千瓦（+11.2%）、"
                      "太阳能 3.9 亿千瓦（+28.1%）。官方口径确认投资计划落地。"),
         evidence_role="supporting", confidence="high",
         independence_group="pwr_grid_stats_2022", temporal_relation="subsequent"),
    dict(evidence_id="E-PWR-12", source_id="S-PWR-12", date="2024-01-26",
         evidence_type="行业数据",
         description=("2023 年全国电网工程建设投资完成 5275 亿元（+5.4%）；太阳能装机 6.1 亿千瓦（+55.2%）。"
                      "电网投资连续第二年增长。"),
         evidence_role="supporting", confidence="high",
         independence_group="pwr_grid_stats_2023", temporal_relation="subsequent"),
    dict(evidence_id="E-PWR-13", source_id="S-PWR-13", date="2025-01-21",
         evidence_type="行业数据",
         description=("2024 年全国电网工程投资完成 6083 亿元（+15.3%）；太阳能装机 8.9 亿千瓦（+45.2%）、"
                      "风电 5.2 亿千瓦（+18.0%）。电网投资增速显著抬升，与 2024 年板块主升相互印证。"),
         evidence_role="supporting", confidence="high",
         independence_group="pwr_grid_stats_2024", temporal_relation="subsequent"),
    dict(evidence_id="E-PWR-14", source_id="S-PWR-15", date="2023-06-11",
         evidence_type="行业数据",
         description=("我国首个「沙戈荒」风光电基地外送电特高压工程——宁夏—湖南 ±800 千伏特高压直流输电工程开工，"
                      "标志特高压进入密集开工期。"),
         evidence_role="supporting", confidence="high",
         independence_group="pwr_grid_uhv_start", temporal_relation="contemporaneous"),
    dict(evidence_id="E-PWR-15", source_id="S-PWR-07", date="2024-10-08",
         evidence_type="行情数据",
         description=("代表标的行情复核（前复权）：许继电气 2024-07-09 达区间高点 34.17；"
                      "国电南瑞 2024-10-08 达 26.71；平高电气 2024-10-14 达 20.54 → Peak Window "
                      "2024-07-09~2024-10-14。另 2022-01-18/19 三大标的同步见顶（利好兑现回撤起点）。"),
         evidence_role="supporting", confidence="high",
         independence_group="pwr_market_cycle2", temporal_relation="contemporaneous"),
    dict(evidence_id="E-PWR-16", source_id="S-PWR-14", date="2025-02-12",
         evidence_type="media",
         description=("2024 年国家电网投资首次超过 6000 亿元，建成投运 3 项特高压工程，"
                      "累计建成「22 交 16 直」38 项特高压工程。"),
         evidence_role="supporting", confidence="high",
         independence_group="pwr_grid_sgcc_2024", temporal_relation="subsequent"),
]
CAMPAIGN_EVIDENCES = [
    dict(campaign_id=C_NE, evidence_id="E-PWR-01", role="supporting"),
    dict(campaign_id=C_NE, evidence_id="E-PWR-02", role="supporting"),
    dict(campaign_id=C_NE, evidence_id="E-PWR-03", role="supporting"),
    dict(campaign_id=C_NE, evidence_id="E-PWR-04", role="supporting"),
    dict(campaign_id=C_NE, evidence_id="E-PWR-05", role="supporting"),
    dict(campaign_id=C_NE, evidence_id="E-PWR-06", role="context"),
    dict(campaign_id=C_NE, evidence_id="E-PWR-07", role="context"),
    dict(campaign_id=C_GRID, evidence_id="E-PWR-08", role="supporting"),
    dict(campaign_id=C_GRID, evidence_id="E-PWR-09", role="supporting"),
    dict(campaign_id=C_GRID, evidence_id="E-PWR-10", role="supporting"),
    dict(campaign_id=C_GRID, evidence_id="E-PWR-11", role="supporting"),
    dict(campaign_id=C_GRID, evidence_id="E-PWR-12", role="supporting"),
    dict(campaign_id=C_GRID, evidence_id="E-PWR-13", role="supporting"),
    dict(campaign_id=C_GRID, evidence_id="E-PWR-14", role="supporting"),
    dict(campaign_id=C_GRID, evidence_id="E-PWR-15", role="supporting"),
    dict(campaign_id=C_GRID, evidence_id="E-PWR-16", role="supporting"),
]

# ------------------------------------------------------------- 8) Events
EVENTS = [
    dict(event_id="EV-PWR-01", date="2018-05-31", event_type="policy", source_id="S-PWR-05",
         name="光伏「531 新政」：关于 2018 年光伏发电有关事项的通知（发改能源〔2018〕823 号）",
         description="加快补贴退坡、控制发展节奏，构成 2018 年光伏板块深度出清的 Setup。"),
    dict(event_id="EV-PWR-02", date="2019-01-07", event_type="policy", source_id="S-PWR-04",
         name="风电、光伏发电无补贴平价上网试点通知（发改能源〔2019〕19 号）",
         description="平价上网元年；平价项目不受年度建设规模限制。"),
    dict(event_id="EV-PWR-03", date="2020-09-22", event_type="policy", source_id="S-PWR-01",
         name="第 75 届联大：宣布 2030 碳达峰 / 2060 碳中和（双碳目标）",
         description="清洁能源发电设备重估的政策起点。"),
    dict(event_id="EV-PWR-04", date="2020-12-12", event_type="policy", source_id="S-PWR-02",
         name="气候雄心峰会：2030 年风电、太阳能发电总装机容量 12 亿千瓦以上",
         description="首个可量化的装机目标，构成本轮 Cycle 的加速催化。"),
    dict(event_id="EV-PWR-05", date="2021-09-08", event_type="policy", source_id="S-PWR-03",
         name="整县（市、区）屋顶分布式光伏开发试点名单公布（676 个县）",
         description="分布式光伏全国性推进机制落地，构成广泛确认。"),
    dict(event_id="EV-PWR-06", date="2022-01-16", event_type="policy", source_id="S-PWR-09",
         name="国家电网 2022 年度工作会议：电网投资计划 5012 亿元",
         description="电网投资由降转升的转折点；但市场当日前后即「利好兑现」回落。"),
    dict(event_id="EV-PWR-07", date="2022-08-03", event_type="policy", source_id="S-PWR-10",
         name="国家电网披露年内再开工 8 项特高压工程、在建项目投资突破万亿",
         description="特高压第四轮建设进入实施阶段的官方确认。"),
    dict(event_id="EV-PWR-08", date="2023-06-11", event_type="industry", source_id="S-PWR-15",
         name="首个「沙戈荒」风光电基地外送特高压工程开工（宁夏—湖南 ±800 千伏）",
         description="特高压进入密集开工期；行业事件（非政策发布）。"),
    dict(event_id="EV-PWR-09", date="2025-02-12", event_type="company", source_id="S-PWR-14",
         name="国家电网 2024 年投资首超 6000 亿元，累计建成「22 交 16 直」38 项特高压",
         description="电网投资高增的年度确认。"),
]
CAMPAIGN_EVENTS = [
    dict(campaign_id=C_NE, event_id="EV-PWR-01", role="context"),
    dict(campaign_id=C_NE, event_id="EV-PWR-02", role="context"),
    dict(campaign_id=C_NE, event_id="EV-PWR-03", role="trigger"),
    dict(campaign_id=C_NE, event_id="EV-PWR-04", role="catalyst"),
    dict(campaign_id=C_NE, event_id="EV-PWR-05", role="catalyst"),
    dict(campaign_id=C_GRID, event_id="EV-PWR-06", role="trigger"),
    dict(campaign_id=C_GRID, event_id="EV-PWR-07", role="catalyst"),
    dict(campaign_id=C_GRID, event_id="EV-PWR-08", role="follow_up"),
    dict(campaign_id=C_GRID, event_id="EV-PWR-09", role="follow_up"),
]


def ins(table, rows):
    for r in rows:
        db.insert(conn, table, r)
    print(f"  {table:24s} +{len(rows)}")


def main():
    print("=== seed_power_equipment.py（电力设备历史 Cycle — Wave 1A）===")
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
