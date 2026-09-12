"""seeds 2018-2020 汽车夏季窗口研究数据（试点）。

严格区分 Source / Evidence / Campaign / Rule。
媒体描述只作为 evidence，不直接等于 market fact。
只有 Evidence 足够时 Campaign 才被创建；否则 annual status = no_clear_campaign / weak。

用法: python scripts/seed.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

conn = db.connect()
db.init_db(conn)
db.migrate(conn)   # v1.5：对已存在数据库增量建表/加列（幂等）


def ins(table, row):
    db.insert(conn, table, row)


# ------------------------------------------------------------
# Rule
# ------------------------------------------------------------
ins("research_rules", {
    "rule_id": "rule_auto_summer",
    "name": "6-8月汽车季节性观察窗口",
    "base_pattern": "汽车",
    "description": "检验历史上 6-8 月是否更容易出现汽车相关机会；记录窗口漂移、年度主题、Campaign 持续性与反例。不预设结论为有效。",
    "source_id": None,
    "status": "under_review",
})

# ------------------------------------------------------------
# Sources (Tier 标记)
# ------------------------------------------------------------
sources = [
    # ---- 2018 ----
    dict(source_id="S-2018-01", source_type="media_tier2", title="7月份传统汽车产销双降 新能源车逆势增长", author="刘瑾", url="http://www.ce.cn/cysc/newmain/yc/jsxw/201808/21/t20180821_30080840.shtml", published_at="2018-08-21", publisher="中国经济网/经济日报", tier=2, description="中汽协7月数据：汽车产销量同比双降，进入负增长；新能源汽车逆势高增。含6月销量同比下滑、7月转负的表述。"),
    dict(source_id="S-2018-02", source_type="media_tier2", title="汽车股半年盘点：一汽东风比亚迪跌20% 上汽小幅上涨", author="新浪财经", url="https://finance.sina.com.cn/stock/marketresearch/2018-07-02/doc-ihespqry6410552.shtml", published_at="2018-07-02", publisher="新浪财经", tier=2, description="上半年汽车板块整体跌22.59%，26只汽车股仅上汽上涨。汽车板块持续走弱。"),
    dict(source_id="S-2018-03", source_type="media_tier2", title="国内建厂利好提振特斯拉相关概念走势活跃", author="中国证券报", url="https://www.cs.com.cn/gppd/gsyj/201807/t20180712_5840061.html", published_at="2018-07-12", publisher="中国证券报", tier=2, description="7/10特斯拉与临港签署协议，7/11特斯拉/锂电概念逆势走强，宁德时代涨6.44%创新高。短期事件驱动。"),
    dict(source_id="S-2018-04", source_type="media_tier2", title="汽车行业估值见底 龙头公司投资价值凸显", author="杨苏", url="https://news.cnstock.com/industry,rdjj-201807-4244790.htm", published_at="2018-07-11", publisher="证券时报", tier=2, description="2018H1股价跌幅超30%的汽车公司50多家。板块整体下跌，估值回落。"),
    # ---- 2019 ----
    dict(source_id="S-2019-01", source_type="media_tier2", title="6月份乘用车销量环比增长10.7% 汽车市场迎来“促销式”回暖", author="刘瑾", url="http://paper.ce.cn/jjrb/html/2019-07/11/content_395466.htm", published_at="2019-07-11", publisher="经济日报·中国经济网", tier=2, description="6月汽车销量205.6万辆环比+7.5%同比-9.6%；乘用车环比+10.7%。国五/国六切换+促销导致回暖，非真实需求改善。6/26补贴退坡过渡期结束。"),
    dict(source_id="S-2019-02", source_type="media_tier2", title="新能源汽车再现负增长 市场情绪有望9月回升", author="崔小粟", url="http://www.ce.cn/cysc/ny/gdxw/201908/13/t20190813_32888607.shtml", published_at="2019-08-13", publisher="中国证券报/中经网", tier=2, description="7月新能源销量同比-4.7%近三年首次负增长；汽车销量连续13个月同比下降。补贴退坡致7月后新能源汽车降温。"),
    dict(source_id="S-2019-03", source_type="media_tier3", title="上半年汽车相关政策盘点", author="综合", url="http://m.toutiao.com/group/6715160839256539659/", published_at="2019-07", publisher="头条/综合", tier=3, description="6/6发改委等印发《推动重点消费品更新升级方案2019-2020》，汽车限购解禁为关键词，但未推实质补贴。6/26新能源补贴退坡近70%。"),
    dict(source_id="S-2019-04", source_type="media_tier2", title="快讯：智能汽车概念股午后走强", author="财联社", url="https://www.cls.cn/detail/381973", published_at="2019-08-27", publisher="财联社", tier=2, description="8/27智能汽车概念午后走强，万安科技封板，亚太股份/浙江世宝/路畅科技跟涨。交通运输部研究自动驾驶法规及指导意见。"),
    dict(source_id="S-2019-05", source_type="media_tier3", title="无人驾驶板块", author="张枕河", url="http://m.toutiao.com/group/6748910614548054542/", published_at="2019-10-17", publisher="中国证券报", tier=3, description="无人驾驶指数8/15(2210.96)涨至9/24(2733.92)累计+23.65%。《交通强国建设纲要》、自动驾驶商用牌照催化。8月中下旬起走强。"),
    # ---- 2020 ----
    dict(source_id="S-2020-01", source_type="media_tier2", title="'全球车王'狂掀涨停潮 3400亿巨头暴涨8%", author="莫飞", url="https://www.stcn.com/article/detail/185209.html", published_at="2020-06-11", publisher="中国基金报/证券时报", tier=2, description="6/10特斯拉破千美元超丰田成全球市值最大车企；6/11 A股特斯拉板块涨近4%，旭升/亚玛顿/秀强/模塑涨停，宁德时代涨超8%。"),
    dict(source_id="S-2020-02", source_type="media_tier2", title="汽车股集体走强：比亚迪涨停，宁德时代市值逼近五千亿", author="21世纪经济报道", url="http://static.nfapp.southcn.com/content/202007/13/c3761026.html", published_at="2020-07-13", publisher="南方+/21世纪经济报道", tier=2, description="7/13比亚迪涨停，江淮两连板，宁德时代涨9.91%市值逼近5000亿。6月汽车产销同比+11.6%回暖。7/12比亚迪汉(刀片电池)上市。"),
    dict(source_id="S-2020-03", source_type="media_tier4", title="比亚迪2020年6月来的走势复盘", author="轻舟已过万重山186", url="https://xueqiu.com/3795379662/269009043", published_at="2023-11-30", publisher="雪球（经验帖，Tier4线索）", tier=4, description="口径为线索：比亚迪2020/6/1爆发突破40-50平台，7/13阶段高点96.44，随后回调，8/21二次启动突破100，11/6涨到197.46。含二次启动/Wave。仅作线索，需行情数据核验。"),
    dict(source_id="S-2020-04", source_type="media_tier4", title="2017-2025年汽车整车板块炒作周期分析", author="跃渊SH", url="https://xueqiu.com/5184598984/398548787", published_at="2026-07-06", publisher="雪球（经验帖，Tier4线索）", tier=4, description="2020年汽车整车板块从4月底启动到年底涨幅82.66%，特斯拉国产化图腾。口径为线索，需独立数据核验。"),
]
for s in sources:
    ins("sources", s)

# ------------------------------------------------------------
# Evidences (evidence 与 source 相对应)
# ------------------------------------------------------------
evidences = [
    # 2018
    dict(evidence_id="E-2018-01", source_id="S-2018-01", date="2018-07-01", evidence_type="行业月度产销数据", description="中汽协：2018年7月汽车销量188.9万辆，同比-4%，为年内第二个同比下降月份；6月乘用车销量已同比下滑。高房价/贸易摩擦/消费贷收紧导致需求走弱。", evidence_role="contradicting", confidence="high", independence_group="orig_cn_sales_data"),
    dict(evidence_id="E-2018-02", source_id="S-2018-02", date="2018-07-02", evidence_type="行情数据", description="申万汽车/同花顺汽车板块2018上半年整体跌约22.59%，26只汽车股仅上汽上涨，余25只普跌。板块整体走弱，无夏季上攻。", evidence_role="contradicting", confidence="high", independence_group="orig_sector_price"),
    dict(evidence_id="E-2018-03", source_id="S-2018-03", date="2018-07-11", evidence_type="行情数据", description="7/10特斯拉临港建厂消息，7/11特斯拉/锂电概念逆势走强，宁德时代涨6.44%收于创新高，成交37亿居A股首位。系事件驱动脉冲，非板块级持续行情。", evidence_role="context", confidence="high", independence_group="orig_tesla_sh"),
    dict(evidence_id="E-2018-04", source_id="S-2018-04", date="2018-07-11", evidence_type="行情数据", description="2018上半年涨幅>40%的汽车公司20多家、>30%的50多家；汽车零部件PE降至19倍历史底部。板块整体估值系统性下移。", evidence_role="contradicting", confidence="high", independence_group="orig_sector_valuation"),
    # 2019
    dict(evidence_id="E-2019-01", source_id="S-2019-01", date="2019-06-01", evidence_type="行业月度产销数据", description="6月汽车销量205.6万辆环比+7.5%同比-9.6%，乘用车环比+10.7%。此回暖主要来自国五/国六切换与经销商清仓促销、补贴过渡期前抢装，非真实需求增长。", evidence_role="context", confidence="high", independence_group="orig_cn_sales_data"),
    dict(evidence_id="E-2019-02", source_id="S-2019-02", date="2019-07-01", evidence_type="行业月度产销数据", description="7月汽车销量连续13个月同比下降；7月新能源销量8万辆同比-4.7%，近三年首次负增长。6/26补贴退坡近70%致7月后新能源汽车降温。", evidence_role="contradicting", confidence="high", independence_group="orig_cn_sales_data"),
    dict(evidence_id="E-2019-03", source_id="S-2019-03", date="2019-06-06", evidence_type="政策文件", description="6/6发改委等印发《推动重点消费品更新升级方案2019-2020》，汽车限购解禁关键词，鼓励促进汽车消费；但未含实质补贴，属温和信号。", evidence_role="context", confidence="high", independence_group="orig_policy"),
    dict(evidence_id="E-2019-04", source_id="S-2019-04", date="2019-08-27", evidence_type="行情数据", description="8/27智能汽车概念午后走强，万安科技封板，亚太/浙江世宝/路畅跟涨；交通部研究自动驾驶法规与指导意见。属8月底事件驱动脉冲。", evidence_role="supporting", confidence="medium", independence_group="orig_ad_momentum"),
    dict(evidence_id="E-2019-05", source_id="S-2019-05", date="2019-08-15", evidence_type="行情数据", description="无人驾驶指数自8/15(2210.96)涨至9/24(2733.92)，累计+23.65%。《交通强国建设纲要》+自动驾驶商用牌照+华为5G方案催化。窗口偏8月中下旬起，近9月。", evidence_role="supporting", confidence="medium", independence_group="orig_ad_momentum"),
    # 2020
    dict(evidence_id="E-2020-01", source_id="S-2020-01", date="2020-06-11", evidence_type="行情数据", description="6/10特斯拉破千美元超丰田成全球市值最大车企；6/11 A股特斯拉板块大涨近4%，旭升/亚玛顿/秀强/模塑涨停，宁德时代涨超8%。板块半日市值增450亿。", evidence_role="supporting", confidence="high", independence_group="orig_tesla_momentum"),
    dict(evidence_id="E-2020-02", source_id="S-2020-02", date="2020-07-13", evidence_type="行情数据", description="7/13汽车整车走强，比亚迪首板涨停、江淮两连板，宁德时代涨9.91%市值逼近5000亿。6月汽车产销同比+11.6%持续回暖。7/12比亚迪汉(刀片电池)上市。", evidence_role="supporting", confidence="high", independence_group="orig_tesla_momentum"),
    dict(evidence_id="E-2020-03", source_id="S-2020-03", date="2020-06-01", evidence_type="行情数据", description="线索(Tier4)：比亚迪2020/6/1突破40-50平台启动，6月+25%，7/13阶段高点96.44，7月中回调后8/21二次启动破100，11/6至197.46。反映Wave/二次启动，需行情数据二次核验确认。", evidence_role="supporting", confidence="low", independence_group="same_origin_xueqiu_byd"),
    dict(evidence_id="E-2020-04", source_id="S-2020-04", date="2020-04-28", evidence_type="行情数据", description="线索(Tier4)：汽车整车板块2020年自4月底启动至年底涨幅82.66%，特斯拉国产化为核心驱动。全年视角可能早于6/1启动，窗口漂移需核验。", evidence_role="context", confidence="low", independence_group="same_origin_xueqiu_byd"),
]
for e in evidences:
    ins("evidences", e)

# ------------------------------------------------------------
# Annual Reviews (母记录)
# ------------------------------------------------------------
annual = [
    dict(annual_review_id="AR-2018", rule_id="rule_auto_summer", year=2018, status="no_clear_campaign",
         summary="2018年6-8月窗口内汽车板块整体下行，无持续性主题 Campaign。处于行业下行+贸易摩擦+购置税退坡背景，销量7月起转负。仅特斯拉临港建厂造成短暂事件脉冲，不构成 Campaign。判定为 no_clear_campaign（反例年份）。",
         review_notes="强反例：板块整体下跌，6-8月无上攻。证明'6-8月汽车'并非每年有效。"),
    dict(annual_review_id="AR-2019", rule_id="rule_auto_summer", year=2019, status="weak",
         summary="2019年6-8月整车板块无明确主题 Campaign。6月系国五/六切换促销式回暖（非行情主线）；新能源汽车7月起负增长。仅8月中下旬-9月无人驾驶/智能汽车出现事件驱动行情，启动偏窗口尾部（近9月），属 weak/event 性质。",
         review_notes="窗口尾端出现智能汽车题材；整车无持续上攻；判定 lean weak。"),
    dict(annual_review_id="AR-2020", rule_id="rule_auto_summer", year=2020, status="strong",
         summary="2020年6-8月为清晰的主题 Campaign：特斯拉国产化+新能源(比亚迪刀片电池、宁德时代)。6月初启动、7/13高位、龙头比亚迪/宁德时代明确。且存在 Wave（8/21二次启动）。判定 strong，是当前已知最强证据窗口。",
         review_notes="注意线索提示全年或自4月底启动，需行数据核验窗口真实起点。存在 Wave。"),
]
for a in annual:
    ins("annual_reviews", a)

# ------------------------------------------------------------
# Themes（Base Pattern: 汽车 → Annual Theme）
# ------------------------------------------------------------
themes = [
    dict(theme_id="TH-AUTO", name="汽车", theme_type="industry", parent_theme_id=None, description="Base Pattern 汽车"),
    dict(theme_id="TH-NEV", name="新能源汽车/电池", theme_type="industry", parent_theme_id="TH-AUTO", description="电动化产业链"),
    dict(theme_id="TH-TESLA-CHAIN", name="特斯拉产业链", theme_type="concept", parent_theme_id="TH-NEV", description="特斯拉国产化受益标的"),
    dict(theme_id="TH-AD", name="智能驾驶/无人驾驶", theme_type="concept", parent_theme_id="TH-AUTO", description="自动驾驶、车联网（2023年后主升）"),
]
for t in themes:
    ins("themes", t)

# ------------------------------------------------------------
# Events
# ------------------------------------------------------------
events = [
    dict(event_id="EV-2018-01", date="2018-07-10", name="特斯拉与上海临港签署建厂协议", event_type="company", description="特斯拉将在临港独资建设纯电动车超级工厂", source_id="S-2018-03"),
    dict(event_id="EV-2019-01", date="2019-06-06", name="《推动重点消费品更新升级方案2019-2020》印发", event_type="policy", description="汽车限购解禁关键词，促进汽车消费但无实质补贴", source_id="S-2019-03"),
    dict(event_id="EV-2019-02", date="2019-06-26", name="2019年新能源汽车补贴退坡新政实施", event_type="policy", description="国补降幅近50%，地补退出，总退坡近70%", source_id="S-2019-03"),
    dict(event_id="EV-2019-03", date="2019-08-27", name="交通部研究自动驾驶法规与指导意见", event_type="policy", description="围绕自动驾驶法律/法规开展专项研究", source_id="S-2019-04"),
    dict(event_id="EV-2020-01", date="2020-06-10", name="特斯拉股价破千美元、市值超丰田居全球车企第一", event_type="company", description="特斯拉市值破1900亿美元成全球市值最大车企；5月华销量11095辆环比+205%", source_id="S-2020-01"),
    dict(event_id="EV-2020-02", date="2020-07-12", name="比亚迪汉上市（首搭刀片电池）", event_type="company", description="对标特斯拉Model 3的旗舰新能源车型上市", source_id="S-2020-02"),
    dict(event_id="EV-2020-03", date="2020-07-10", name="宁德时代与本田战略合作+为特斯拉供货", event_type="company", description="本田认购宁德时代1%股权；本月起为特斯拉上海工厂供电池", source_id="S-2020-02"),
]
for ev in events:
    ins("events", ev)

# ------------------------------------------------------------
# Securities
# ------------------------------------------------------------
securities = [
    dict(security_id="BIDI", ticker="002594", name="比亚迪", exchange="SZ"),
    dict(security_id="CATL", ticker="300750", name="宁德时代", exchange="SZ"),
    dict(security_id="JAC", ticker="600418", name="江淮汽车", exchange="SH"),
    dict(security_id="GWM", ticker="601633", name="长城汽车", exchange="SH"),
    dict(security_id="CHANGAN", ticker="000625", name="长安汽车", exchange="SZ"),
    dict(security_id="XUSHENG", ticker="603305", name="旭升股份", exchange="SH"),
    dict(security_id="SAIC", ticker="600104", name="上汽集团", exchange="SH"),
    dict(security_id="WANAN", ticker="002590", name="万安科技", exchange="SZ"),
    dict(security_id="YATAI", ticker="002284", name="亚太股份", exchange="SZ"),
    dict(security_id="ROUTE", ticker="002813", name="路畅科技", exchange="SZ"),
]
for s in securities:
    ins("securities", s)

# ------------------------------------------------------------
# Campaigns
# ------------------------------------------------------------
campaigns = [
    # 2018: no campaign (反例年份，不创建 theme_campaign)
    # 2019: 智能汽车事件驱动（8月底，窗口尾部）
    dict(campaign_id="C-2019-AD", annual_review_id="AR-2019", rule_id="rule_auto_summer",
         season_id="summer_2019", campaign_year=2019,
         start_date="2019-08-15", end_date="2019-09-30", peak_date="2019-09-24",
         strength="weak", result="weak", classification="event_driven",
         start_date_basis="无人驾驶指数自8/15起持续走强(据S-2019-05)；8/27智能汽车脉冲(据S-2019-04)",
         end_date_basis="9/24指数高点后回落(据S-2019-05)", date_confidence="medium",
         drift_vs_jun01=75, drift_vs_jul01=45, drift_vs_aug01=14,
         description="8月中下旬启动的智能驾驶/无人驾驶事件驱动行情，起点落在6-8月窗口尾部（近9月），非整车主线，强度弱。",
         research_notes="classification=event_driven 而非 theme_campaign，因持续时间与强度不足；且主题更偏智能网联而非整车。"),
    # 2020: 特斯拉/新能源主题 Campaign
    dict(campaign_id="C-2020-NEV", annual_review_id="AR-2020", rule_id="rule_auto_summer",
         season_id="summer_2020", campaign_year=2020,
         start_date="2020-06-01", end_date="2020-09-30", peak_date="2020-07-13",
         strength="strong", result="positive", classification="theme_campaign",
         start_date_basis="6/10特斯拉破千美元+6/11 A股特斯拉板块涨停潮(据S-2020-01)；比亚迪6/1启动(线索S-2020-03)",
         end_date_basis="9月末后进入震荡；注意全年或延续至年底(线索S-2020-04)。窗口暂记至9/30", date_confidence="medium",
         drift_vs_jun01=0, drift_vs_jul01=-30, drift_vs_aug01=-61,
         description="特斯拉国产化+新能源主题 Campaign。主线：特斯拉链+比亚迪刀片电池+宁德时代。6/11特斯拉板块涨停潮为明确信号。龙头比亚迪、宁德时代。存在 Wave（8/21二次启动）。",
         research_notes="全年视角可能4月底提前启动(线索)；日线行情数据需二次核验精确起点与终点。wave 已用 campaign_phases 记录。"),
]
for c in campaigns:
    ins("campaigns", c)

# campaign_themes
campaign_themes = [
    dict(campaign_id="C-2019-AD", theme_id="TH-AD", role="main"),
    dict(campaign_id="C-2020-NEV", theme_id="TH-TESLA-CHAIN", role="main"),
    dict(campaign_id="C-2020-NEV", theme_id="TH-NEV", role="main"),
    dict(campaign_id="C-2020-NEV", theme_id="TH-AUTO", role="related"),
]
for ct in campaign_themes:
    ins("campaign_themes", ct)

# campaign_events
campaign_events = [
    dict(campaign_id="C-2019-AD", event_id="EV-2019-03", role="trigger"),
    dict(campaign_id="C-2020-NEV", event_id="EV-2020-01", role="trigger"),
    dict(campaign_id="C-2020-NEV", event_id="EV-2020-02", role="catalyst"),
    dict(campaign_id="C-2020-NEV", event_id="EV-2020-03", role="follow_up"),
]
for ce in campaign_events:
    ins("campaign_events", ce)

# campaign_evidences（v1.5：显式关联，禁止混入全库证据）
campaign_evidences = [
    # C-2019-AD（智能驾驶事件驱动）
    dict(campaign_id="C-2019-AD", evidence_id="E-2019-04", role="supporting"),
    dict(campaign_id="C-2019-AD", evidence_id="E-2019-05", role="supporting"),
    dict(campaign_id="C-2019-AD", evidence_id="E-2019-03", role="context"),
    # C-2020-NEV（特斯拉/新能源主题）
    dict(campaign_id="C-2020-NEV", evidence_id="E-2020-01", role="supporting"),
    dict(campaign_id="C-2020-NEV", evidence_id="E-2020-02", role="supporting"),
    dict(campaign_id="C-2020-NEV", evidence_id="E-2020-03", role="supporting"),
    dict(campaign_id="C-2020-NEV", evidence_id="E-2020-04", role="context"),
]
for cew in campaign_evidences:
    ins("campaign_evidences", cew)

# campaign_securities（leader 需证据支撑）
campaign_securities = [
    dict(campaign_id="C-2019-AD", security_id="WANAN", role="leader"),
    dict(campaign_id="C-2019-AD", security_id="YATAI", role="representative"),
    dict(campaign_id="C-2019-AD", security_id="ROUTE", role="representative"),
    dict(campaign_id="C-2020-NEV", security_id="BIDI", role="leader"),
    dict(campaign_id="C-2020-NEV", security_id="CATL", role="leader"),
    dict(campaign_id="C-2020-NEV", security_id="XUSHENG", role="representative"),
    dict(campaign_id="C-2020-NEV", security_id="JAC", role="second_leader"),
]
for cs in campaign_securities:
    ins("campaign_securities", cs)

# campaign_phases (2020 Wave，证据为线索低confidence，仅记录)
phases = [
    dict(phase_id="PH-2020-01", campaign_id="C-2020-NEV", phase_type="startup", start_date="2020-06-01", end_date="2020-06-10", description="特斯拉破千美元前，板块蓄势/启动"),
    dict(phase_id="PH-2020-02", campaign_id="C-2020-NEV", phase_type="main_rise", start_date="2020-06-11", end_date="2020-07-13", description="特斯拉涨停潮驱动主升；7/13比亚迪涨停、宁德逼近5000亿"),
    dict(phase_id="PH-2020-03", campaign_id="C-2020-NEV", phase_type="retracement", start_date="2020-07-14", end_date="2020-08-20", description="7/14特斯拉过山车带动A股调整，比亚迪回调后横盘"),
    dict(phase_id="PH-2020-04", campaign_id="C-2020-NEV", phase_type="secondary_rally", start_date="2020-08-21", end_date="2020-09-30", description="8/21比亚迪二次启动破100(线索S-2020-03)，是否再加速需核验"),
]
for p in phases:
    ins("campaign_phases", p)

conn.commit()
conn.close()
print("Seeded OK. DB rows:")
conn = db.connect()
for t in ["sources","evidences","research_rules","annual_reviews","campaigns","themes","campaign_themes","events","campaign_events","securities","campaign_securities","campaign_phases"]:
    print(f"  {t}: {conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]}")
conn.close()