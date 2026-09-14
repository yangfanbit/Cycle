"""Medical Health 最小数据集：入库（Research 侧）。

背景（Medical Health Minimum Dataset v0.1）：
- 首次把非汽车 Macro Theme（医药健康）接入 ThreeC 数据链路，验证 Research → DB → Export → Timeline。
- 这是**最小验证数据集**，不是完整医药数据库：
  1 个正式 Campaign（创新药产业链升级）+ 2 个 Research Candidate（疫情医疗 / 中医药）。
- **日期来自真实行情复核**（research/data/market/normalized/*.csv，腾讯 GTIMG 2019-01-02~2022-12-30）。

纪律（严格遵守）：
- 不修改 schema.sql / contracts / export contract / Timeline UI / Research Model。
- Peak 口径按 Theme/Campaign Separation v1.1 §6：**使用 Campaign 自身的代表标的**，
  不得使用上位医药指数（PHARMA_ETF_512010 仅作参照，不参与 Peak 判定）。
- 不伪造：取不到的日期留 NULL / 写 unknown；不计算 seasonality / win_rate / probability。
- 幂等：全部 db.insert（INSERT OR REPLACE），可重复运行。

用法: python scripts/seed_medical_min.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

conn = db.connect()
db.migrate(conn)

RULE = "rule_pharma_upgrade"
CAMPAIGN = "C-2019-PHARMA-INNOV"

# ------------------------------------------------------------------ 1) Rule
RULES = [
    dict(rule_id=RULE, name="医药健康结构性升级观察窗口", base_pattern="医药健康",
         description=("历史观察窗口：医药产业从「仿制药/销售驱动」向「创新驱动 + 产业链专业化 + 国际化」"
                      "迁移所形成的结构性行情。非固定买入窗口，不构成交易建议。"),
         source_id=None, status="under_review"),
]

# ------------------------------------------------------- 2) Annual Reviews
ANNUAL = [
    dict(annual_review_id="AR-MED-2019", rule_id=RULE, year=2019, status="medium",
         summary="医药结构性重估起步：科创板开板 + 医保谈判释放「鼓励创新」信号；子行业显著分化。"),
    dict(annual_review_id="AR-MED-2020", rule_id=RULE, year=2020, status="strong",
         summary="疫情 + 流动性双驱动扩张；疫情医疗与创新药/CXO/消费医疗两条叙事并行。"),
    dict(annual_review_id="AR-MED-2021", rule_id=RULE, year=2021, status="strong",
         summary="分批见顶：恒瑞医药 2020-12-25、药明康德/泰格医药 2021-07-01；下半年集采扩围 + 风格切换。"),
    dict(annual_review_id="AR-MED-2022", rule_id=RULE, year=2022, status="weak",
         summary="估值出清延续；中医药与抗疫相关逆势活跃。Cycle End 未确认。"),
]

# ------------------------------------------------------------- 3) Themes
THEMES = [
    dict(theme_id="TH-PHARMA", name="医药健康", theme_type="industry", parent_theme_id=None,
         description="Macro Theme（产品级长期稳定分类）。"),
    dict(theme_id="TH-PHARMA-INNOV", name="创新药", theme_type="concept", parent_theme_id="TH-PHARMA",
         description="Sub-theme：创新药结构性重估。"),
    dict(theme_id="TH-PHARMA-CXO", name="CXO(研发外包)", theme_type="concept", parent_theme_id="TH-PHARMA",
         description="Sub-theme：CRO/CDMO 产业链专业化（经 Gate Q1 Anti-example 判定为 Sub-theme，非独立 Campaign）。"),
    dict(theme_id="TH-PHARMA-PANDEMIC", name="疫情医疗", theme_type="concept", parent_theme_id="TH-PHARMA",
         description="Sub-theme / Candidate：防护耗材 · 检测 · 疫苗。"),
    dict(theme_id="TH-PHARMA-TCM", name="中医药", theme_type="concept", parent_theme_id="TH-PHARMA",
         description="Sub-theme / Candidate：品牌中药 · 中药创新 · 抗疫中药。"),
]

# ---------------------------------------------------------- 4) Campaigns
# 日期全部来自本地真实行情复核（数据见 market_daily / normalized CSV）。
CAMPAIGNS = [dict(
    campaign_id=CAMPAIGN,
    annual_review_id="AR-MED-2019",
    rule_id=RULE,
    season_id="pharma_2019_2021",
    campaign_year=2019,
    start_date="2019-01-02",
    end_date="2022-10-31",
    peak_date="2021-07-01",
    strength="strong",
    result="positive",
    classification="theme_campaign",
    start_date_basis="market_data",
    end_date_basis="market_data",
    date_confidence="medium",
    description=("创新药产业链升级：医药产业从仿制药/销售驱动转向创新驱动 + 产业链专业化。"
                 "代表标的：恒瑞医药（创新药）、药明康德 / 泰格医药（CXO）。"),
    research_notes=("跨年 Campaign（2019-01-02 ~ 2022-10-31，约 3.8 年）。"
                    "Peak 口径按 v1.1 §6 使用 Campaign 自身代表标的：恒瑞医药 2020-12-25、"
                    "药明康德/泰格医药 2021-07-01 → Peak Window 2020-12-25~2021-07-01（DATE_WINDOW）。"
                    "end_date 为各自代表标的 2022-09/10 低点；2022Q4 出现修复迹象，"
                    "Theme Cycle End 未确认。start_date 等于本地数据窗口起点（2019-01-02），"
                    "2018Q4 的 4+7 集采 Setup 不在本地数据范围内（仅作 context 证据）。"),
)]

CAMPAIGN_THEMES = [
    dict(campaign_id=CAMPAIGN, theme_id="TH-PHARMA", role="related"),
    # 主主题唯一：创新药（避免 role='main' 多条导致产品端主题行键不确定）
    dict(campaign_id=CAMPAIGN, theme_id="TH-PHARMA-INNOV", role="main"),
    # CXO 是本 Campaign 内的产业链环节（Sub-theme），不是独立 Campaign → role=related
    dict(campaign_id=CAMPAIGN, theme_id="TH-PHARMA-CXO", role="related"),
]

# campaign_phases 沿用既有 DB 枚举（startup/acceleration/main_rise/diffusion/retracement/secondary_rally/decline/unclear）
# 注意：export 的 lifecycle[] 使用研究层枚举，两者并存（见 THEME_CAMPAIGN_MODEL_AUDIT F6）。
PHASES = [
    dict(phase_id="PH-MED-01", campaign_id=CAMPAIGN, phase_type="startup",
         start_date="2019-01-02", end_date="2019-07-21",
         description="Setup：4+7 集采（2018-12-17）后市场开始区分「创新 vs 仿制」，结构性重估起步。"),
    dict(phase_id="PH-MED-02", campaign_id=CAMPAIGN, phase_type="acceleration",
         start_date="2019-07-22", end_date="2019-11-27",
         description="加速：科创板开板（2019-07-22）打开未盈利生物科技融资通道；药明康德 2019-08 明显跳升。"),
    dict(phase_id="PH-MED-03", campaign_id=CAMPAIGN, phase_type="main_rise",
         start_date="2020-01-01", end_date="2020-12-24",
         description="主升：疫情 + 全球流动性宽松 + CXO 景气；恒瑞医药 2020 年内 +53.9%（adj）。"),
    dict(phase_id="PH-MED-04", campaign_id=CAMPAIGN, phase_type="diffusion",
         start_date="2020-12-25", end_date="2021-07-01",
         description="Peak Window（分批见顶）：恒瑞医药 2020-12-25 → 药明康德/泰格医药 2021-07-01。"),
    dict(phase_id="PH-MED-05", campaign_id=CAMPAIGN, phase_type="retracement",
         start_date="2021-07-02", end_date="2021-12-31",
         description="回撤：集采扩围（器械/耗材/IVD）超预期 + 高估值消化 + 资金切向新能源。"),
    dict(phase_id="PH-MED-06", campaign_id=CAMPAIGN, phase_type="decline",
         start_date="2022-01-03", end_date="2022-10-31",
         description="衰减：创新药估值出清至近 10 年低位区间；2022Q4 出现修复迹象（Cycle End 未确认）。"),
]

# --------------------------------------------------------- 5) Securities
SECURITIES = [
    dict(security_id="HENGRUI", ticker="600276", name="恒瑞医药", exchange="SH"),
    dict(security_id="WUXIAPPTEC", ticker="603259", name="药明康德", exchange="SH"),
    dict(security_id="TIGERMED", ticker="300347", name="泰格医药", exchange="SZ"),
    dict(security_id="INTCO", ticker="300677", name="英科医疗", exchange="SZ"),
    dict(security_id="ZHIFEI", ticker="300122", name="智飞生物", exchange="SZ"),
    dict(security_id="PIANZAIHUANG", ticker="600436", name="片仔癀", exchange="SH"),
    dict(security_id="YILING", ticker="002603", name="以岭药业", exchange="SZ"),
]
# 正式 Campaign 的代表标的（RC 的代表标的记录在 batch 脚本的 RESEARCH_CANDIDATES，
# 因候选不进入 campaigns 表，无法经 campaign_securities 绑定 —— 见审计报告结构性发现）
CAMPAIGN_SECURITIES = [
    dict(campaign_id=CAMPAIGN, security_id="HENGRUI", role="leader"),
    dict(campaign_id=CAMPAIGN, security_id="WUXIAPPTEC", role="leader"),
    dict(campaign_id=CAMPAIGN, security_id="TIGERMED", role="second_leader"),
]

# ------------------------------------------------------------ 6) Sources
SOURCES = [
    dict(source_id="S-MED-01", source_type="regulator", tier=1,
         title="国家医保局 2019 年国家医保谈判准入药品名单新闻发布会（150 谈成 97；PD-1 首次纳入医保）",
         publisher="国家医疗保障局", published_at="2019-11-28",
         url="https://www.nhsa.gov.cn/", description="官方发布：新增 70 个平均降幅 60.7%；12 个国产重大创新药谈成 8 个。"),
    dict(source_id="S-MED-02", source_type="exchange", tier=1,
         title="上海证券交易所科创板开板（允许未盈利生物科技企业上市）",
         publisher="上海证券交易所", published_at="2019-07-22",
         url=None, description="为创新药企业提供独立融资与估值体系。"),
    dict(source_id="S-MED-03", source_type="regulator", tier=1,
         title="CDE《以临床价值为导向的抗肿瘤药物临床研发指导原则（征求意见稿）》",
         publisher="国家药品监督管理局药品审评中心", published_at="2021-07-02",
         url=None, description="引发市场对 CXO 景气度的质疑，为 2021-07 板块见顶后的政策扰动之一。"),
    dict(source_id="S-MED-04", source_type="media_tier2", tier=2,
         title="4+7 城市药品集中采购中选结果公布（25 品种，平均降幅 52%）",
         publisher="人民网 / 中国新闻网", published_at="2018-12-17",
         url="https://society.people.com.cn/n1/2018/1209/c1008-30451518.html",
         description="Setup 背景：摧毁仿制药「带金销售」旧叙事，市场开始区分创新与仿制。"),
    dict(source_id="S-MED-05", source_type="regulator", tier=1,
         title="国家医保局、国家中医药管理局《关于医保支持中医药传承创新发展的指导意见》",
         publisher="国家医疗保障局 / 国家中医药管理局", published_at="2021-12-31",
         url=None, description="中医药专属政策体系（与创新药/集采主线不同源）。"),
    dict(source_id="S-MED-06", source_type="website", tier=3,
         title="腾讯财经 GTIMG 日线（raw + 前复权 qfq），2019-01-02 ~ 2022-12-30",
         publisher="腾讯财经", published_at=None,
         url="https://gu.qq.com/", description="行情数据来源；本地复核见 research/data/market/normalized/。"),
]

# ---------------------------------------------------------- 7) Evidences
EVIDENCES = [
    dict(evidence_id="E-MED-01", source_id="S-MED-06", date="2021-07-01",
         evidence_type="market_data",
         description=("创新药产业链代表标的行情复核：药明康德 / 泰格医药 前复权价于 2021-07-01 达区间最高"
                      "（161.83 / 202.49），此前 2019-01-02→2021-07-01 分别 +103.5% / +159.7%。"
                      "恒瑞医药同期于 2020-12-25 见顶（94.76）→ Peak 分批。"),
         evidence_role="supporting", confidence="high",
         independence_group="med_market_innov", temporal_relation="contemporaneous"),
    dict(evidence_id="E-MED-02", source_id="S-MED-01", date="2019-11-28",
         evidence_type="official_document",
         description=("2019 年国家医保谈判结果：150 谈成 97，新增 70 个平均降幅 60.7%；PD-1 首次纳入医保；"
                      "12 个国产重大创新药谈成 8 个 → 官方定价机制明确「鼓励创新」导向。"),
         evidence_role="supporting", confidence="high",
         independence_group="med_policy_insurance", temporal_relation="contemporaneous"),
    dict(evidence_id="E-MED-03", source_id="S-MED-02", date="2019-07-22",
         evidence_type="official_document",
         description="科创板开板，允许未盈利生物科技企业上市，创新药获得独立融资与估值通道。",
         evidence_role="supporting", confidence="high",
         independence_group="med_policy_ipo", temporal_relation="contemporaneous"),
    dict(evidence_id="E-MED-04", source_id="S-MED-03", date="2021-07-02",
         evidence_type="official_document",
         description=("CDE 发布《以临床价值为导向的抗肿瘤药物临床研发指导原则（征求意见稿）》，"
                      "引发市场对 CXO 景气度的质疑 → 与 2021-07 见顶后的回撤相互印证。"),
         evidence_role="context", confidence="medium",
         independence_group="med_policy_cde", temporal_relation="contemporaneous"),
    dict(evidence_id="E-MED-05", source_id="S-MED-04", date="2018-12-17",
         evidence_type="media",
         description=("4+7 城市药品集中采购中选结果：25 品种平均降幅 52%、最高 96%。"
                      "构成 Theme Cycle 的 Setup 背景（旧叙事被摧毁），早于本地行情数据窗口。"),
         evidence_role="context", confidence="high",
         independence_group="med_policy_vbp", temporal_relation="prior"),
]
CAMPAIGN_EVIDENCES = [
    dict(campaign_id=CAMPAIGN, evidence_id="E-MED-01", role="supporting"),
    dict(campaign_id=CAMPAIGN, evidence_id="E-MED-02", role="supporting"),
    dict(campaign_id=CAMPAIGN, evidence_id="E-MED-03", role="supporting"),
    dict(campaign_id=CAMPAIGN, evidence_id="E-MED-04", role="context"),
    dict(campaign_id=CAMPAIGN, evidence_id="E-MED-05", role="context"),
]

# ------------------------------------------------------------- 8) Events
EVENTS = [
    dict(event_id="EV-MED-01", date="2018-12-17", event_type="policy", source_id="S-MED-04",
         name="4+7 城市药品集中采购中选结果公布（25 品种，平均降幅 52%）",
         description="摧毁仿制药销售驱动旧叙事，形成创新药结构性重估的 Setup 背景。"),
    dict(event_id="EV-MED-02", date="2019-07-22", event_type="policy", source_id="S-MED-02",
         name="科创板开板（允许未盈利生物科技企业上市）",
         description="创新药独立融资与估值通道打开。"),
    dict(event_id="EV-MED-03", date="2019-11-28", event_type="policy", source_id="S-MED-01",
         name="2019 年国家医保药品目录谈判结果公布（PD-1 首次纳入医保）",
         description="官方明确「鼓励创新」导向，构成 Theme Cycle 的 Broad Confirmation。"),
    dict(event_id="EV-MED-04", date="2021-07-02", event_type="policy", source_id="S-MED-03",
         name="CDE《以临床价值为导向的抗肿瘤药物临床研发指导原则（征求意见稿）》",
         description="引发对 CXO 景气度的质疑。"),
    dict(event_id="EV-MED-05", date="2021-12-31", event_type="policy", source_id="S-MED-05",
         name="医保局、中医药局《关于医保支持中医药传承创新发展的指导意见》",
         description="中医药专属政策（与创新药/集采主线不同源）；作为全局事件记录（不绑定正式 Campaign）。"),
]
CAMPAIGN_EVENTS = [
    dict(campaign_id=CAMPAIGN, event_id="EV-MED-01", role="context"),
    dict(campaign_id=CAMPAIGN, event_id="EV-MED-02", role="trigger"),
    dict(campaign_id=CAMPAIGN, event_id="EV-MED-03", role="catalyst"),
    dict(campaign_id=CAMPAIGN, event_id="EV-MED-04", role="context"),
]


def ins(table, rows):
    for r in rows:
        db.insert(conn, table, r)
    print(f"  {table:24s} +{len(rows)}")


def main():
    print("=== seed_medical_min.py（医药健康最小数据集）===")
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
