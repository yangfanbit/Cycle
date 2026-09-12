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
    # ---- 2021 ----
    dict(source_id="S-2021-01", source_type="regulator", title="2021年6月汽车工业经济运行情况", author="装备工业一司", url="https://wap.miit.gov.cn/jgsj/zbys/gzdt/art/2021/art_064b511ebcb340fb9952570930e06e85.html", published_at="2021-07-09", publisher="工信部", tier=1, description="工信部装备工业一司(据中汽协)：6月汽车销量201.5万辆同比-12.4%(芯片短缺、原材料上涨)；新能源汽车产销24.8/25.6万辆同比+1.3/1.4倍，渗透率超12%。"),
    dict(source_id="S-2021-02", source_type="media_tier2", title="淡季不淡 新能源前7月累计销量已超历年全年", author="张懿", url="http://auto.ce.cn/auto/gundong/202108/13/t20210813_36803370.shtml", published_at="2021-08-13", publisher="中国经济网/中汽协", tier=2, description="中汽协7月数据：整体汽车销量同比-11.9%(缺芯)；新能源产销28.4/27.1万辆同比+1.7/1.6倍创新高，前7月累计超历年全年，渗透率10%。”淡季不淡”。"),
    dict(source_id="S-2021-03", source_type="media_tier2", title="新能源车板块爆发 长安汽车等多股涨停", author="上证报", url="https://news.cnstock.com/news,bwkx-202106-4718320.htm", published_at="2021-06-18", publisher="上海证券报/中国证券网", tier=2, description="6/18新能源车板块爆发，蓝海华腾/金银河/精达/长安/华友钴业/天赐材料/小康等十余股涨停，长城、比亚迪涨幅均超8%。"),
    dict(source_id="S-2021-04", source_type="media_tier2", title="宁德时代盘中站上500元 持续布局产能扩张", author="经济参考报", url="http://finance.ce.cn/stock/gsgdbd/202106/29/t20210629_36677047.shtml", published_at="2021-06-29", publisher="经济参考报", tier=2, description="6/28新能源板块全线走强，宁德时代盘中最高502.98元创历史新高，总市值约1.15万亿；5/31市值已破万亿，近一年涨188%。6月动力电池产量+165.8%。"),
    dict(source_id="S-2021-05", source_type="media_tier2", title="比亚迪盘中大涨逾5%再创新高 总市值一度超9000亿元", author="吴永芳", url="https://www.stcn.com/stock/djjd/202108/t20210806_3516040.html", published_at="2021-08-06", publisher="证券时报网", tier=2, description="8/6比亚迪大涨逾5%创历史新高，总市值一度超9000亿；7月新能源销量5.05万辆再创新高同比+234.38%。"),
    dict(source_id="S-2021-06", source_type="media_tier3", title="“芯”常态下看车企 几家欢喜几家愁", author="北京青年报", url="http://epaper.ynet.com/images/2021-08/18/C03/bjqnb20210818C03.pdf", published_at="2021-08-18", publisher="北京青年报(北青网)", tier=3, description="受芯片短缺加剧，截至7月汽车产销同比连续三个月下滑(4-7月乘用车产量同比转负)；自主新能源高增长但整体车市承压。"),
    dict(source_id="S-2021-07", source_type="media_tier3", title="个股市值增长千亿 新能源车市场淡季不淡", author="智通财经", url="https://finance.sina.com.cn/stock/hkstock/hkstocknews/2021-08-21/doc-ikqciyzm2723001.shtml", published_at="2021-08-21", publisher="智通财经/新浪财经", tier=3, description="7月新能源汽车市场淡季不淡：7月国内新能源乘用车零售22.2万辆同比+169.4%，渗透率升至14.8%；长城7月市值增长超千亿、江淮7月股价+42.8%。"),
    # ---- 2022 ----
    dict(source_id="S-2022-01", source_type="media_tier2", title="车企加码送福利，助力政策“大礼包”，汽车股继续狂欢！", author="裴健如", url="http://finance.ce.cn/stock//gsgdbd/202206/02/t20220602_37702442.shtml", published_at="2022-06-02", publisher="每日经济新闻", tier=2, description="5/31财政部/税务总局发布购置税减半细则(6/1-12/31, 30万内2.0L以下)；6/1次日汽车整车指数盘中拉涨逾4%，安凯/东风/海马/小康涨停，中通/广汽涨超6%，板块居申万一级涨幅第一。"),
    dict(source_id="S-2022-02", source_type="media_tier2", title="政策东风频吹 多家车企自掏腰包补贴消费者", author="韩忠楠", url="https://www.cs.com.cn/qc/202206/t20220602_6274329.html", published_at="2022-06-02", publisher="证券时报", tier=2, description="5/23国常会部署稳经济一揽子措施：阶段性减征购置税600亿；5/31国务院《扎实稳住经济一揽子政策措施》+财政部购置税细则+工信部等新能源下乡；超20家车企响应加码补贴。"),
    dict(source_id="S-2022-03", source_type="media_tier3", title="国常会促进汽车消费举措提振市场 数十家汽车企业股价触及涨停", author="周菊", url="http://www.zqrb.cn/finance/hangyedongtai/2022-06-26/A1656238702392.html", published_at="2022-06-26", publisher="经济观察网", tier=3, description="6/22国常会再促汽车消费(取消二手车限迁等)；6/23汽车整车板块涨5.8%多股涨停；Wind汽车指数自4月以来不到两个月累计涨超60%。"),
    dict(source_id="S-2022-04", source_type="media_tier2", title="涨疯了！超越大众后，比亚迪市值突破万亿大关", author="每日经济新闻", url="http://finance.ce.cn/stock/gsgdbd/202206/10/t20220610_37743414.shtml", published_at="2022-06-10", publisher="每日经济新闻", tier=2, description="6/10比亚迪A股市值首破万亿(报348.80元+8.19%)，自主品牌首家；5月新能源乘用车零售36万辆同比+91.2%；上海6月初解封，供给大幅好转+购置税6/1起实施。"),
    dict(source_id="S-2022-05", source_type="media_tier2", title="中通客车“12天12板” 监管发函质问是否存内幕交易？", author="龚梦泽", url="http://m.zqrb.cn/gscy/gongsi/2022-05-30/A1653910621458.html", published_at="2022-05-30", publisher="证券日报", tier=2, description="中通客车5/13-5/30收12个涨停累计涨214.52%，系核酸检测车概念个股事件；深交所发关注函质疑内幕交易；公司2021年净利-2.2亿持续恶化。非汽车行业Campaign主线。"),
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
    # 2021
    dict(evidence_id="E-2021-01", source_id="S-2021-01", date="2021-07-09", evidence_type="行业月度产销数据", description="工信部/中汽协：6月整体汽车销量201.5万辆同比-12.4%(芯片短缺、原材料涨)；但新能源汽车产销24.8/25.6万辆同比+1.3/1.4倍，6月新能源渗透率超12%，刷新历史。", evidence_role="supporting", confidence="high", independence_group="orig_nev_sales_data"),
    dict(evidence_id="E-2021-02", source_id="S-2021-02", date="2021-08-13", evidence_type="行业月度产销数据", description="中汽协7月数据：整体汽车销量同比-11.9%(缺芯)；新能源产销28.4/27.1万辆同比+1.7/1.6倍创新高，前7月累计已超历年全年，渗透率10%。新能源“淡季不淡”。", evidence_role="supporting", confidence="high", independence_group="orig_nev_sales_data"),
    dict(evidence_id="E-2021-03", source_id="S-2021-03", date="2021-06-18", evidence_type="行情数据", description="6/18新能源车板块爆发，蓝海华腾/金银河/精达/长安/华友钴业/天赐材料/小康等十余股涨停，长城、比亚迪涨幅均超8%。板块级主升信号。", evidence_role="supporting", confidence="high", independence_group="orig_sector_momentum"),
    dict(evidence_id="E-2021-04", source_id="S-2021-04", date="2021-06-29", evidence_type="行情数据", description="6/28新能源板块全线走强，宁德时代盘中最高502.98元创历史新高，总市值约1.15万亿；5/31市值已破万亿，一年涨188%。动力电池6月产量同比+165.8%。", evidence_role="supporting", confidence="high", independence_group="orig_nev_stock_price"),
    dict(evidence_id="E-2021-05", source_id="S-2021-05", date="2021-08-06", evidence_type="行情数据", description="8/6比亚迪大涨逾5%创历史新高，总市值一度超9000亿；7月新能源销量5.05万辆再创新高同比+234.38%。龙头持续创新高，主线延续至8月。", evidence_role="supporting", confidence="high", independence_group="orig_nev_stock_price"),
    dict(evidence_id="E-2021-06", source_id="S-2021-06", date="2021-08-01", evidence_type="行业数据", description="反例视角：受芯片短缺加剧，4-7月乘用车产销同比连续三个月下滑(7月乘用车产量同比-10.7%)；整体汽车产销总量负增长，传统车承压。Campaign集中于新能源/电池，非全面汽车行情。", evidence_role="contradicting", confidence="high", independence_group="orig_counter_chip"),
    dict(evidence_id="E-2021-07", source_id="S-2021-07", date="2021-07-01", evidence_type="行业数据", description="7月新能源乘用车零售22.2万辆同比+169.4%，渗透率升至14.8%；长城7月市值增长超千亿、江淮7月股价+42.8%。新能源Beta外溢至整车个股。", evidence_role="context", confidence="medium", independence_group="orig_nev_retail_sales"),
    # 2022
    dict(evidence_id="E-2022-01", source_id="S-2022-01", date="2022-06-02", evidence_type="行情数据", description="5/31财政部/税务总局发布购置税减半细则(6/1-12/31, 30万内2.0L以下)；6/1次日汽车整车指数盘中拉涨逾4%，安凯/东风/海马/小康涨停，中通/广汽涨超6%，板块居申万一级涨幅第一。", evidence_role="supporting", confidence="high", independence_group="orig_policy_tax_catalyst"),
    dict(evidence_id="E-2022-02", source_id="S-2022-02", date="2022-06-02", evidence_type="政策文件", description="5/23国常会部署稳经济一揽子措施：阶段性减征购置税600亿；5/31国务院《扎实稳住经济一揽子措施》+财政部购置税细则+工信部新能源下乡启动；超20家车企响应加码补贴。政策组合拳。", evidence_role="supporting", confidence="high", independence_group="orig_policy_tax_catalyst"),
    dict(evidence_id="E-2022-03", source_id="S-2022-04", date="2022-06-10", evidence_type="行情数据", description="6/10比亚迪A股市值首破万亿(报348.80元+8.19%)，自主品牌首家；5月新能源乘用车零售36万辆同比+91.2%；上海6月初解封+购置税6/1实施，供给与需求双击。", evidence_role="supporting", confidence="high", independence_group="orig_nev_stock_price"),
    dict(evidence_id="E-2022-04", source_id="S-2022-03", date="2022-06-26", evidence_type="行情数据", description="6/22国常会再促汽车消费(取消二手车限迁/新能源购置税延期研究)；6/23汽车整车板块涨5.8%多股涨停(二次催化)；Wind汽车指数自4月以来不到两个月累计涨超60%，证明启动早于经验窗口。", evidence_role="supporting", confidence="medium", independence_group="orig_sector_momentum"),
    dict(evidence_id="E-2022-05", source_id="S-2022-05", date="2022-05-30", evidence_type="行情数据", description="反例视角：中通客车5/13-5/30收12连板累计+214.52%，系“核酸检测车”概念个股事件(1-4月仅售20台)，深交所发关注函；非汽车行业Campaign主线，属单只个股事件驱动。", evidence_role="contradicting", confidence="high", independence_group="orig_counter_single_stock"),
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
    dict(annual_review_id="AR-2021", rule_id="rule_auto_summer", year=2021, status="strong",
         summary="2021年6-8月为清晰的新能源/电池主题 Campaign：整体汽车销量受芯片短缺拖累同比转负，但新能源汽车产销持续翻倍高增(渗透率升至12%+)，资金集中炒作新能源+电池主线(比亚迪/宁德时代/长城/长安)。6月中旬板块爆发、7月主线延续、8月龙头仍创新高。判定 strong，classification=theme_campaign(新能源主题为主)，但非全面汽车行情(见反例)。",
         review_notes="重要区分：Campaign集中于新能源/电池，整体整车销量因缺芯负增长，故主线非‘全面汽车’，而是‘新能源渗透+电池高景气’。Bloomberg口径需以日线核验精确峰/终点。"),
    dict(annual_review_id="AR-2022", rule_id="rule_auto_summer", year=2022, status="strong",
         summary="2022年汽车板块为清晰的政策驱动主题 Campaign：23国常会购置税600亿→5/31细则→6/1落地次日整车集体涨停，叠加复工复产/新能源下乡，5月指数已启动(自4月不到两月涨超60%)，6/10比亚迪破万亿，6/23二次催化再涨停。判定 strong，theme_campaign。注意实际启动早于经验窗口(4月底/5月初)，不强行限定6-8月。",
         review_notes="启动明显提前：Wind汽车指数自4月以来涨超60%(4月底已启动)。中通客车13连板为‘核酸检测车’个股事件，不计入Campaign主线。7月后板块分化，需日线核验精确终点。"),
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
    dict(theme_id="TH-CAR-CONSUMPTION", name="汽车消费/购置税刺激", theme_type="concept", parent_theme_id="TH-AUTO", description="购置税减半、汽车下乡、汽车消费政策刺激 (2022主升)"),
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
    # 2021
    dict(event_id="EV-2021-01", date="2021-05-31", name="宁德时代市值突破万亿", event_type="market", description="5/31宁德时代总市值首破万亿，动力电池龙头走强", source_id="S-2021-04"),
    dict(event_id="EV-2021-02", date="2021-08-05", name="比亚迪7月产销快报：新能源销量5.05万辆创新高", event_type="company", description="7月新能源销量5.05万辆同比+234.38%再创新高", source_id="S-2021-05"),
    dict(event_id="EV-2021-03", date="2021-06-17", name="宁德时代四川宜宾产能一期投运", event_type="company", description="四川时代动力电池一期在宜宾投运，累计六期投资超300亿", source_id="S-2021-04"),
    # 2022
    dict(event_id="EV-2022-01", date="2022-05-23", name="国常会：阶段性减征乘用车购置税600亿元", event_type="policy", description="国务院常务会议部署稳经济一揽子措施，明确减征部分乘用车购置税600亿", source_id="S-2022-02"),
    dict(event_id="EV-2022-02", date="2022-05-31", name="财政部/税务总局发布购置税减半细则+新能源下乡启动", event_type="policy", description="6/1-12/31对30万内2.0L及以下乘用车减半征收购置税；工信部等四部门启动新能源下乡", source_id="S-2022-02"),
    dict(event_id="EV-2022-03", date="2022-06-22", name="国常会再促汽车消费(取消二手车限迁等)", event_type="policy", description="活跃二手车市场、取消非营运小汽车迁入限制、研究新能源购置税减免延期", source_id="S-2022-03"),
    dict(event_id="EV-2022-04", date="2022-06-10", name="比亚迪A股市值首破万亿", event_type="market", description="6/10比亚迪报348.8元+8.19%，A股市值破万亿，自主品牌首家", source_id="S-2022-04"),
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
    dict(security_id="ZHONGTONG", ticker="000957", name="中通客车", exchange="SZ"),
    dict(security_id="GAC", ticker="601238", name="广汽集团", exchange="SH"),
    dict(security_id="ANKA", ticker="000868", name="安凯客车", exchange="SZ"),
    dict(security_id="DONGFENG", ticker="600006", name="东风汽车", exchange="SH"),
    dict(security_id="XIAOKANG", ticker="601127", name="小康股份", exchange="SH"),
    dict(security_id="GANFENG", ticker="002460", name="赣锋锂业", exchange="SZ"),
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
    # 2021: 新能源/电池主题 Campaign（整体车市因缺芯负增长，主线集中在新能源）
    dict(campaign_id="C-2021-NEV", annual_review_id="AR-2021", rule_id="rule_auto_summer",
         season_id="summer_2021", campaign_year=2021,
         start_date="2021-06-01", end_date="2021-09-30", peak_date="2021-08-06",
         strength="strong", result="positive", classification="theme_campaign",
         start_date_basis="趋势自5月底启动(5/31宁德市值破万亿)，6/18新能源板块爆发涨停潮(据S-2021-03)，6/28宁德创历史新高(据S-2021-04)",
         end_date_basis="8/6比亚迪新高9000亿后高位震荡，9月后主线衰减；精确终点需日线核验。窗口暂记至9/30", date_confidence="medium",
         drift_vs_jun01=0, drift_vs_jul01=-30, drift_vs_aug01=-61,
         description="新能源汽车/电池主题 Campaign。整体汽车销量受芯片短缺拖累同比转负，但新能源汽车产销翻倍高增(渗透率12%+)，资金集中炒作新能源+电池主线。6/18板块爆发、7月延续、8/6龙头比亚迪创新高。龙头比亚迪、宁德时代、长城、长安。",
         research_notes="classification=theme_campaign(新能源主线)，但非全面汽车行情；整体车市缺芯负增长为反例约束。需以新能源指数日线核验精确峰/终点。存在个股层面二次催化。"),
    # 2022: 政策驱动主题 Campaign（早于经验窗口）
    dict(campaign_id="C-2022-POLICY", annual_review_id="AR-2022", rule_id="rule_auto_summer",
         season_id="season_2022", campaign_year=2022,
         start_date="2022-04-27", end_date="2022-08-31", peak_date="2022-06-10",
         strength="strong", result="positive", classification="theme_campaign",
         start_date_basis="Wind汽车指数自4月以来不到两个月累计涨超60%，4月底已启动(据S-2022-03)；5/23国常会购置税600亿为政策信号(据S-2022-02)",
         end_date_basis="7月中后板块分化/回调(需日线核验)；8月后政策边际减弱。窗口暂记至8/31", date_confidence="medium",
         drift_vs_jun01=-35, drift_vs_jul01=-65, drift_vs_aug01=-96,
         description="汽车消费刺激政策主题 Campaign。5/23国常会购置税600亿→5/31细则→6/1落地次日整车集体涨停；叠加复工复产、新能源下乡。6/10比亚迪破万亿，6/22国常会再刺激触发二次上攻。龙头比亚迪、长城、长安、广汽。启动早于6-8月经验窗口(4月底/5月初)。",
         research_notes="启动明显提前(4月底)，不强行限定6-8月。中通客车13连板系‘核酸检测车’个股事件，不计入Campaign主线。7月后分化，需日线核验精确终点。"),
]
for c in campaigns:
    ins("campaigns", c)

# campaign_themes
campaign_themes = [
    dict(campaign_id="C-2019-AD", theme_id="TH-AD", role="main"),
    dict(campaign_id="C-2020-NEV", theme_id="TH-TESLA-CHAIN", role="main"),
    dict(campaign_id="C-2020-NEV", theme_id="TH-NEV", role="main"),
    dict(campaign_id="C-2020-NEV", theme_id="TH-AUTO", role="related"),
    dict(campaign_id="C-2021-NEV", theme_id="TH-NEV", role="main"),
    dict(campaign_id="C-2021-NEV", theme_id="TH-AUTO", role="related"),
    dict(campaign_id="C-2022-POLICY", theme_id="TH-CAR-CONSUMPTION", role="main"),
    dict(campaign_id="C-2022-POLICY", theme_id="TH-NEV", role="related"),
    dict(campaign_id="C-2022-POLICY", theme_id="TH-AUTO", role="related"),
]
for ct in campaign_themes:
    ins("campaign_themes", ct)

# campaign_events
campaign_events = [
    dict(campaign_id="C-2019-AD", event_id="EV-2019-03", role="trigger"),
    dict(campaign_id="C-2020-NEV", event_id="EV-2020-01", role="trigger"),
    dict(campaign_id="C-2020-NEV", event_id="EV-2020-02", role="catalyst"),
    dict(campaign_id="C-2020-NEV", event_id="EV-2020-03", role="follow_up"),
    dict(campaign_id="C-2021-NEV", event_id="EV-2021-01", role="catalyst"),
    dict(campaign_id="C-2021-NEV", event_id="EV-2021-03", role="catalyst"),
    dict(campaign_id="C-2021-NEV", event_id="EV-2021-02", role="follow_up"),
    dict(campaign_id="C-2022-POLICY", event_id="EV-2022-01", role="trigger"),
    dict(campaign_id="C-2022-POLICY", event_id="EV-2022-02", role="catalyst"),
    dict(campaign_id="C-2022-POLICY", event_id="EV-2022-04", role="follow_up"),
    dict(campaign_id="C-2022-POLICY", event_id="EV-2022-03", role="follow_up"),
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
    # C-2021-NEV（新能源/电池主题）
    dict(campaign_id="C-2021-NEV", evidence_id="E-2021-01", role="supporting"),
    dict(campaign_id="C-2021-NEV", evidence_id="E-2021-02", role="supporting"),
    dict(campaign_id="C-2021-NEV", evidence_id="E-2021-03", role="supporting"),
    dict(campaign_id="C-2021-NEV", evidence_id="E-2021-04", role="supporting"),
    dict(campaign_id="C-2021-NEV", evidence_id="E-2021-05", role="supporting"),
    dict(campaign_id="C-2021-NEV", evidence_id="E-2021-07", role="context"),
    dict(campaign_id="C-2021-NEV", evidence_id="E-2021-06", role="contradicting"),
    # C-2022-POLICY（汽车消费刺激主题）
    dict(campaign_id="C-2022-POLICY", evidence_id="E-2022-01", role="supporting"),
    dict(campaign_id="C-2022-POLICY", evidence_id="E-2022-02", role="supporting"),
    dict(campaign_id="C-2022-POLICY", evidence_id="E-2022-03", role="supporting"),
    dict(campaign_id="C-2022-POLICY", evidence_id="E-2022-04", role="supporting"),
    dict(campaign_id="C-2022-POLICY", evidence_id="E-2022-05", role="contradicting"),
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
    # 2021: 比亚迪/宁德时代/长城/长安为龙头
    dict(campaign_id="C-2021-NEV", security_id="BIDI", role="leader"),
    dict(campaign_id="C-2021-NEV", security_id="CATL", role="leader"),
    dict(campaign_id="C-2021-NEV", security_id="GWM", role="second_leader"),
    dict(campaign_id="C-2021-NEV", security_id="CHANGAN", role="second_leader"),
    dict(campaign_id="C-2021-NEV", security_id="XIAOKANG", role="representative"),
    # 2022: 比亚迪/长城/长安/广汽为龙头；中通客车系个股事件不计 leader
    dict(campaign_id="C-2022-POLICY", security_id="BIDI", role="leader"),
    dict(campaign_id="C-2022-POLICY", security_id="GWM", role="leader"),
    dict(campaign_id="C-2022-POLICY", security_id="CHANGAN", role="second_leader"),
    dict(campaign_id="C-2022-POLICY", security_id="GAC", role="second_leader"),
    dict(campaign_id="C-2022-POLICY", security_id="ANKA", role="representative"),
]
for cs in campaign_securities:
    ins("campaign_securities", cs)

# campaign_phases (2020 Wave，证据为线索低confidence，仅记录)
phases = [
    dict(phase_id="PH-2020-01", campaign_id="C-2020-NEV", phase_type="startup", start_date="2020-06-01", end_date="2020-06-10", description="特斯拉破千美元前，板块蓄势/启动"),
    dict(phase_id="PH-2020-02", campaign_id="C-2020-NEV", phase_type="main_rise", start_date="2020-06-11", end_date="2020-07-13", description="特斯拉涨停潮驱动主升；7/13比亚迪涨停、宁德逼近5000亿"),
    dict(phase_id="PH-2020-03", campaign_id="C-2020-NEV", phase_type="retracement", start_date="2020-07-14", end_date="2020-08-20", description="7/14特斯拉过山车带动A股调整，比亚迪回调后横盘"),
    dict(phase_id="PH-2020-04", campaign_id="C-2020-NEV", phase_type="secondary_rally", start_date="2020-08-21", end_date="2020-09-30", description="8/21比亚迪二次启动破100(线索S-2020-03)，是否再加速需核验"),
    # 2021（线索为主，仅记录便于核验）
    dict(phase_id="PH-2021-01", campaign_id="C-2021-NEV", phase_type="main_rise", start_date="2021-06-01", end_date="2021-08-06", description="新能源板块6月中加速，6/28宁德创历史新高(1.15万亿)，8/6比亚迪新高9000亿；主线延续"),
    dict(phase_id="PH-2021-02", campaign_id="C-2021-NEV", phase_type="decline", start_date="2021-08-07", end_date="2021-09-30", description="8/6峰值后高位震荡/分化，9月主线衰减(需日线核验)"),
    # 2022（政策驱动两段式）
    dict(phase_id="PH-2022-01", campaign_id="C-2022-POLICY", phase_type="startup", start_date="2022-04-27", end_date="2022-05-22", description="复工复产预期+地方补贴，Wind汽车指数自4月底启动"),
    dict(phase_id="PH-2022-02", campaign_id="C-2022-POLICY", phase_type="main_rise", start_date="2022-05-23", end_date="2022-06-10", description="5/23国常会购置税600亿→6/1细则落地整车涨停潮→6/10比亚迪破万亿"),
    dict(phase_id="PH-2022-03", campaign_id="C-2022-POLICY", phase_type="secondary_rally", start_date="2022-06-22", end_date="2022-06-30", description="6/22国常会再促消费(取消二手车限迁)，6/23整车板块+5.8%多股涨停二次上攻"),
    dict(phase_id="PH-2022-04", campaign_id="C-2022-POLICY", phase_type="decline", start_date="2022-07-01", end_date="2022-08-31", description="7月后板块分化/回调，政策边际减弱(需日线核验)"),
]
for p in phases:
    ins("campaign_phases", p)

# ============================================================
# Pilot 1-B：2023—2025 汽车夏季研究扩展
# ============================================================

# ---- 2023 Sources ----
sources_2023_25 = [
    # ---- 2023 ----
    dict(source_id="S-2023-01", source_type="regulator", title="国新办吹风会：支持L3级及以上自动驾驶商业化应用、启动智能网联汽车准入和上路通行试点", author="工信部", url="https://www.gov.cn/zhengce/202306/content_6887704.htm", published_at="2023-06-21", publisher="国务院新闻办/工信部", tier=1, description="6/21工信部副部长辛国斌吹风会明确表态'支持L3级及更高级别自动驾驶商业化应用、启动准入和上路通行试点'，属政策预期信号，非文件落地。"),
    dict(source_id="S-2023-02", source_type="media_tier2", title="25只汽车股携手涨停！汽车产业链成新主线", author="邬龙", url="http://m.zqrb.cn/stock/bankuaijujiao/2023-07-04/A1688467267535.html", published_at="2023-07-04", publisher="证券日报", tier=2, description="7/4 25只汽车股集体涨停、申万汽车行业涨幅居首+2.67%，整车板块指数创4月新高；机构称汽车产业链'替代AI成为A股新投资主线'。"),
    dict(source_id="S-2023-03", source_type="media_tier2", title="焦点复盘：智能驾驶再度引爆汽车产业链，主线地位就此确认？", author="财联社", url="https://m.cls.cn/detail/1401009", published_at="2023-07-11", publisher="财联社", tier=2, description="7/11智能驾驶涨势加速带动汽车产业链全面爆发；浙江世宝8天6板、瑞玛精密6天5板、众泰7天4板、万安科技2连板；主线地位确认问句。"),
    dict(source_id="S-2023-04", source_type="media_tier2", title="揭秘涨停：无人驾驶掀起涨停潮，机构买入龙头超亿元", author="证券时报", url="https://www.stcn.com/article/detail/909932.html", published_at="2023-07-04", publisher="证券时报", tier=2, description="7/4无人驾驶涨停：德赛西威、路畅、得润、永新光学等9股涨停，浙江世宝3连板，德赛西威龙虎榜净买超亿元；催化=7/3比亚迪首发'天神之眼'高阶智驾。"),
    dict(source_id="S-2023-05", source_type="media_tier2", title="浙江世宝股价翻倍、万安科技等多股涨停，谁是真正智能驾驶概念股？", author="界面新闻", url="https://www.stcn.com/article/detail/919083.html", published_at="2023-07-13", publisher="界面新闻/证券时报", tier=2, description="浙江世宝近一月<8元拉至近18元涨超100%；万安科技8.5→14.31涨近70%；德赛西威5月中<百元→7/11最高179.5元约+80%；赛力斯6/8触24.75低点后一月近翻倍。"),
    dict(source_id="S-2023-06", source_type="media_tier2", title="产销数据亮眼 汽车股狂欢", author="韩忠楠", url="https://www.stcn.com/article/detail/907975.html", published_at="2023-07-03", publisher="证券时报", tier=2, description="7/3汽车板块指数放量涨逾2%创近4月新高；小鹏港股6月来累计涨近80%、理想年内+88%；比亚迪6月销25.3万辆(+88.79%)；政策+出口+销量回暖共振。"),
    dict(source_id="S-2023-07", source_type="regulator", title="《关于开展智能网联汽车准入和上路通行试点工作的通知》", author="工信部等四部门", url="https://www.gov.cn/zhengce/zhengceku/202311/content_6915788.htm", published_at="2023-11-17", publisher="工信部/公安部/住建部/交通部", tier=1, description="11/17四部委(工信部联通装〔2023〕217号)正式遴选L3/L4量产产品开展准入和上路通行试点。关键反证：正式L3文件成文于11月、不在夏季；夏季行情系政策预期驱动。"),
    dict(source_id="S-2023-08", source_type="media_tier2", title="减速器热门股五连板 中马传动澄清『不涉及机器人』", author="证券时报", url="https://www.stcn.com/article/detail/969247.html", published_at="2023-09-04", publisher="证券时报", tier=2, description="做汽车变速器/新能源减速器的中马传动被当机器人概念炒5连板、年内+200%，公司被迫澄清'生产不涉及机器人概念'。证明减速器板市场主逻辑是机器人题材而非汽车。"),
    dict(source_id="S-2023-09", source_type="media_tier2", title="马斯克人形机器人Optimus进展点燃A股机器人/减速器", author="证券时报", url="https://www.stcn.com/article/detail/870171.html", published_at="2023-05-22", publisher="证券时报", tier=2, description="5/17马斯克股东会展示Optimus进展+黄仁勋'具身智能'，5/18-5/22丰立智能3个20cm涨停、5/15-22累计+86.73%，深交所发关注函。减速器5月中-7月初大涨主逻辑系人形机器人。"),
    # ---- 2024 ----
    dict(source_id="S-2024-01", source_type="regulator", title="五部门公布'车路云一体化'应用试点城市名单（20城）", author="工信部等五部门", url="https://www.gov.cn/zhengce/zhengceku/202407/content_6965771.htm", published_at="2024-07-03", publisher="工信部/公安部/住建部/交通部/应急管理部", tier=1, description="7/1成文、7/3公开（工信部联通装函〔2024〕181号）公布20个车路云一体化应用试点城市：北京/上海/重庆/沈阳/南京/武汉/长沙/广州/深圳等。政策顶层信号。"),
    dict(source_id="S-2024-02", source_type="media_tier2", title="车路云概念全线爆发 华铭智能等10余股涨停", author="财联社", url="https://m.cls.cn/detail/1707526", published_at="2024-06-18", publisher="财联社", tier=2, description="6/18车路云概念全线爆发，华铭智能、中海达、鸿泉物联、索菱、金溢、长江通信等10余股涨停，华铭/金溢/索菱2连板——行情高峰。"),
    dict(source_id="S-2024-03", source_type="media_tier2", title="车路云持续分化退潮：索菱断板跌停，金溢逼近跌停", author="财联社/经济参考报", url="https://www.cls.cn/detail/1712879", published_at="2024-06-24", publisher="财联社", tier=2, description="6/24车路云分化退潮，索菱5连板断板跌停，光庭/高新兴/万集高位补跌；6/25金溢逼近跌停、华铭跌近15%。快涨快退、约2周脉冲。"),
    dict(source_id="S-2024-04", source_type="media_tier2", title="无人驾驶+车路云共涨：板块指数大涨超4%，天迈/经纬恒润20cm涨停，德赛西威涨停", author="证券时报", url="http://www.stcn.com/article/detail/1254813.html", published_at="2024-07-10", publisher="证券时报", tier=2, description="7/10无人驾驶+车路云共涨，板块指数大涨超4%，天迈科技/经纬恒润20cm涨停，中海达涨16%、德赛西威涨停，港股百度涨超12%。催化=萝卜快跑武汉出圈。"),
    dict(source_id="S-2024-05", source_type="media_tier2", title="焦点复盘：大众交通16日涨233%，锦江15天9板、金龙12天7板", author="财联社", url="https://m.cls.cn/detail/1747242", published_at="2024-07-29", publisher="财联社", tier=2, description="7/29大众交通16个交易日涨233%、锦江在线15天9板、金龙汽车12天7板——Robotaxi主线最高峰。"),
    dict(source_id="S-2024-06", source_type="media_tier2", title="大众交通终结9连板神话，大众公用A股'天地板'", author="华夏时报", url="https://finance.sina.cn/2024-08-01/detail-inchecpv7805389.d.html", published_at="2024-08-01", publisher="华夏时报", tier=2, description="7/31大众交通终止9连板（-2.65%创新高11.22后回落），大众公用A股天地板（涨停到收跌9.11%）、港股暴跌22.75%——Robotaxi主线见顶退潮。"),
    dict(source_id="S-2024-07", source_type="media_tier2", title="高位题材亏钱效应放大，锦江/金溢跌停，天迈/万集跌超10%", author="财联社", url="https://www.cls.cn/detail/1742498", published_at="2024-07-24", publisher="财联社", tier=2, description="7/24财联社：'无论6月车路云一体化概念还是7月智能网约车，智能驾驶主题炒作已贯穿2个月'；同日高位题材亏钱效应放大，锦江/金溢跌停、天迈/万集跌超10%。"),
    dict(source_id="S-2024-08", source_type="media_tier2", title="武汉车路云一体化重大示范项目备案170.84亿", author="宁波证券/头条财经", url="http://m.toutiao.com/group/7381289421716324864/", published_at="2024-06-14", publisher="头条财经/国泰君安点评", tier=2, description="6/14武汉车路云一体化示范项目获发改委批复、备案170.84亿，紧随北京99亿招标后更重大项目。车路云启动导火索之一。"),
    # ---- 2025 ----
    dict(source_id="S-2025-01", source_type="media_tier2", title="A股无人驾驶概念全线爆发：板块大涨逾3%，多股涨停", author="证券时报", url="https://www.stcn.com/article/detail/2223200.html", published_at="2025-06-24", publisher="证券时报", tier=2, description="6/24无人驾驶板块金飞首涨停潮：三友30%涨停、万马科技/恒帅股份/星源卓镁20%封板，海马汽车/浙江世宝等批量涨停。板块级启动点火。"),
    dict(source_id="S-2025-02", source_type="media_tier2", title="特斯拉在美奥斯汀启动首批Robotaxi有偿试运营", author="深圳商报", url="https://www.stcn.com/article/detail/2242282.html", published_at="2025-06-22", publisher="深圳商报/证券时报", tier=2, description="6/22特斯拉在美国得州奥斯汀启动首批约10辆Model Y Robotaxi有偿试运营(4.2美元/趟)，为特斯拉首次Robotaxi收费试点。点火事件。"),
    dict(source_id="S-2025-03", source_type="media_tier3", title="8月行业月报：CS汽车+11.72%，CS汽车零部件+16.04%", author="国信证券", url="https://finance.sina.com.cn/stock/stockzmt/2025-09-13/", published_at="2025-09-13", publisher="国信证券", tier=3, description="8月CS汽车+11.72%、CS汽车零部件+16.04%(最猛)、乘用车+8.01%，跑赢沪深300 1.39pct。汽零8月独立走强。"),
    dict(source_id="S-2025-04", source_type="media_tier3", title="6/25沪指涨1%创年内新高 汽车产业链为多热点之一", author="新浪财经", url="https://finance.sina.com.cn/roll/2025-06-25/", published_at="2025-06-25", publisher="新浪财经", tier=3, description="6/25大盘氛围：沪指+1%创年内新高、创业板+3.11%，汽车产业链等多方向共振上攻。汽车为多热点之一、非唯一主线。"),
    dict(source_id="S-2025-05", source_type="media_tier2", title="渤海汽车重组获批涨停，10月累计+30%", author="证券时报", url="https://www.stcn.com/article/detail/3382998.html", published_at="2025-10-15", publisher="证券时报", tier=2, description="渤海汽车(活塞/汽零)10/15重组获批(收购海纳川汽车部件资产27.28亿)涨停、10月累计+30%。属个股重组/capital运作事件，不能算行业Campaign。"),
    dict(source_id="S-2025-06", source_type="media_tier2", title="特斯拉FSD正式入华宣布为2026年5月21日，2025年仅预期", author="澎湃新闻", url="https://www.thepaper.cn/newsDetail_forward_32566555", published_at="2025-06-01", publisher="澎湃新闻", tier=2, description="反证：特斯拉'监督版FSD'正式宣布中国可用为2026-05-21；2024年曾称2025Q3获批但未实现，2025年全程仅'部分批准/待批'预期。FSD五一未落地，是2025年夏季题材的关键反例。"),
    dict(source_id="S-2025-07", source_type="media_tier2", title="8月A股整体大牛：沪指+8%、创业板+24%、科创50+28%", author="国际金融报", url="https://www.stcn.com/article/detail/3308400.html", published_at="2025-08-29", publisher="国际金融报/证券时报", tier=2, description="8月A股整体大牛，汽车为其中强势板块之一。夏季汽车涨幅部分来自系统性牛市β，需排除后衡量汽车独立Campaign强度。"),
]
for s in sources_2023_25:
    ins("sources", s)

# ---- 2023—2025 Evidences ----
evidences_2023_25 = [
    # 2023
    dict(evidence_id="E-2023-01", source_id="S-2023-01", date="2023-06-21", evidence_type="政策文件", description="6/21工信部吹风会明确支持L3及以上自动驾驶商业化、启动准入和上路通行试点，属政策预期信号。是7月智能驾驶行情的起点。", evidence_role="supporting", confidence="high", independence_group="orig_l3_policy_expectation"),
    dict(evidence_id="E-2023-02", source_id="S-2023-02", date="2023-07-04", evidence_type="行情数据", description="7/4 25只汽车股集体涨停、申万汽车涨幅居首+2.67%，整车指数创4月新高，机构称汽车产业链替代AI成新主线。板块级主升信号。", evidence_role="supporting", confidence="high", independence_group="orig_sector_momentum"),
    dict(evidence_id="E-2023-03", source_id="S-2023-03", date="2023-07-11", evidence_type="行情数据", description="7/11智能驾驶涨势加速带动汽车产业链爆发，浙江世宝8天6板、瑞玛精密6天5板、万安科技2连板，'主线地位确认'。", evidence_role="supporting", confidence="high", independence_group="orig_ad_momentum"),
    dict(evidence_id="E-2023-04", source_id="S-2023-05", date="2023-07-13", evidence_type="行情数据", description="龙头区间涨幅：浙江世宝近一月翻倍(8→18)、德赛西威+80%、万安+70%、赛力斯6/8见底后一月近翻倍。启动早于6/1(6/12预热、赛力斯6/8见底)。", evidence_role="supporting", confidence="high", independence_group="orig_ad_stock_price"),
    dict(evidence_id="E-2023-05", source_id="S-2023-06", date="2023-07-03", evidence_type="行业数据", description="6月底-7月初汽车销量回暖+出口高增(上半年214万辆+75.7%)+小鹏港股+80%、理想+88%、比亚迪6月+88.79%。政策(6/21吹风+7/21发改委十三部门)+销量+出口共振。", evidence_role="supporting", confidence="medium", independence_group="orig_sales_trend"),
    dict(evidence_id="E-2023-06", source_id="S-2023-07", date="2023-11-17", evidence_type="政策文件", description="反证：正式L3准入文件成文2023-11-17、非夏季；2023年FSD未在华落地(2024-01财报仅员工Beta)。夏季行情系'政策预期'而非'落地'驱动，需降档强度。", evidence_role="contradicting", confidence="high", independence_group="orig_policy_schedule"),
    dict(evidence_id="E-2023-07", source_id="S-2023-03", date="2023-07-19", evidence_type="行情数据", description="反例：7月中下汽车让位地产/顺周期，市场快速轮动/存量资金博弈(财联社7/12'主题频繁高切低')；汽车非贯穿夏季单极主线，呈波段/脉冲式。", evidence_role="contradicting", confidence="medium", independence_group="orig_structure_pulse"),
    dict(evidence_id="E-2023-08", source_id="S-2023-08", date="2023-09-04", evidence_type="行业数据", description="减速器5月中-7月初大涨主逻辑系人形机器人(特斯拉Optimus/具身智能)，中马传动(车辆零部股)被当机器人炒被迫澄清；中大力德产品机器人/自动化各占约50%。归机器人Base Pattern，不计汽车。", evidence_role="context", confidence="high", independence_group="orig_robot_reducer"),
    # 2024
    dict(evidence_id="E-2024-01", source_id="S-2024-01", date="2024-07-03", evidence_type="政策文件", description="7/3五部门公布20个车路云一体化试点城市；叠加6/14武汉170.84亿备案、5/31北京99.39亿招标。顶层政策+大单驱动。", evidence_role="supporting", confidence="high", independence_group="orig_v2x_policy"),
    dict(evidence_id="E-2024-02", source_id="S-2024-02", date="2024-06-18", evidence_type="行情数据", description="6/18车路云全线爆发，华铭/金溢/索菱/长江通信等10余股涨停、多股2连板——行情高峰。", evidence_role="supporting", confidence="high", independence_group="orig_v2x_momentum"),
    dict(evidence_id="E-2024-03", source_id="S-2024-02", date="2024-06-21", evidence_type="行情数据", description="车联网(车路协同)概念指数6/11-6/21涨超9%，229家概念股近八成上涨；6/21索菱5连板后巨量分歧。", evidence_role="supporting", confidence="medium", independence_group="orig_v2x_momentum"),
    dict(evidence_id="E-2024-04", source_id="S-2024-03", date="2024-06-24", evidence_type="行情数据", description="反例/退潮：6/24-25车路云分化退潮，索菱断板跌停、金溢逼近跌停、华铭跌近15%；公司多公告'未参与'仍连板。约2周脉冲炒作、快涨快退、缺持续主线。", evidence_role="contradicting", confidence="high", independence_group="orig_v2x_retreat"),
    dict(evidence_id="E-2024-05", source_id="S-2024-04", date="2024-07-10", evidence_type="行情数据", description="7月上中旬萝卜快跑武汉跑出圈订单暴涨；7/10无人驾驶板块+4%，天迈/经纬恒润20cm涨停、德赛西威涨停、港股百度+12%。", evidence_role="supporting", confidence="high", independence_group="orig_robotaxi_momentum"),
    dict(evidence_id="E-2024-06", source_id="S-2024-05", date="2024-07-29", evidence_type="行情数据", description="7月下旬高峰：大众交通16日涨233%、锦江15天9板、金龙12天7板、7/23大众交通12日+142%。龙头梯队明确。", evidence_role="supporting", confidence="high", independence_group="orig_robotaxi_leader"),
    dict(evidence_id="E-2024-07", source_id="S-2024-06", date="2024-07-31", evidence_type="行情数据", description="反例/退潮：7/31大众交通9连板终结(-2.65%)、大众公用天地板港股暴跌22.75%；7/24高位亏钱效应放大(锦江/金溢跌停)。约3周脉冲、快涨快退。", evidence_role="contradicting", confidence="high", independence_group="orig_robotaxi_retreat"),
    dict(evidence_id="E-2024-08", source_id="S-2024-06", date="2024-10-11", evidence_type="行情数据", description="10/10-11特斯拉Robotaxi发布会(无方向盘Cybercab)仅带来一日A股脉冲后回落，强度弱、不构成独立Campaign。", evidence_role="context", confidence="medium", independence_group="orig_robotaxi_thirdwave"),
    # 2025
    dict(evidence_id="E-2025-01", source_id="S-2025-02", date="2025-06-24", evidence_type="行情数据", description="6/22特斯拉奥斯汀Robotaxi收费试点(点火)→6/24 A股无人驾驶板块全线爆发涨3%三友30%、万马/恒帅/星源卓镁20%、海马/浙江世宝涨停。板块级启动。", evidence_role="supporting", confidence="high", independence_group="orig_robotaxi_2025"),
    dict(evidence_id="E-2025-02", source_id="S-2025-03", date="2025-08-31", evidence_type="行业数据", description="8月CS汽车+11.72%、CS汽车零部件+16.04%、乘用车+8.01%，跑赢沪深300；小马智行8/11第7代Robotaxi量产超200辆。汽零8月独立走强。", evidence_role="supporting", confidence="medium", independence_group="orig_sector_momentum"),
    dict(evidence_id="E-2025-03", source_id="S-2025-07", date="2025-08-29", evidence_type="行情数据", description="反例：8月A股整体大牛(沪指+8%、创业板+24%、科创50+28%)，汽车为强势板块之一非唯一主线；夏季涨幅部分来自系统性牛市β，需降档汽车独立Campaign强度。", evidence_role="contradicting", confidence="medium", independence_group="orig_beta_mask"),
    dict(evidence_id="E-2025-04", source_id="S-2025-06", date="2025-08-31", evidence_type="行业数据", description="反例：特斯拉FSD 2025年未正式在华落地(2026-05-21才宣布监督版可用)；智驾行业分化出清(毫末停摆/纵目破产)，一级投资降至<120亿。点火源是'Robotaxi试点'而非'FSD入华'。", evidence_role="contradicting", confidence="high", independence_group="orig_fsd_not_landed"),
    dict(evidence_id="E-2025-05", source_id="S-2025-05", date="2025-10-15", evidence_type="行情数据", description="反例/剥离：渤海汽车重组获批、众泰阿尔及利亚订单、中通客车同业竞争重组、天汽模/天迈控股权变更等个股资本运作单独暴涨，均不能算汽车行业Campaign。", evidence_role="contradicting", confidence="high", independence_group="orig_single_stock_events"),
]
for e in evidences_2023_25:
    ins("evidences", e)

# ---- 2023—2025 Annual Reviews ----
annual_2023_25 = [
    dict(annual_review_id="AR-2023", rule_id="rule_auto_summer", year=2023, status="medium",
         summary="2023年6-8月存在一段真实可识别的市场主题：智能驾驶/无人驾驶(L3政策预期+7/3比亚迪天神之眼智驾)+汽车产业链(销量回暖+出口高增+智驾催化)。6/12预热、6/21工信部L3吹风表态、7/3-4整车/智驾全面爆发(25股涨停、整车指数创4月新高)、7/11主线确认、7月中下退潮。判定 theme_campaign、strength=medium。关键反例：正式L3准入文件成文于11/17、非夏季；2023年FSD未在华落地，故夏季系'政策预期+销量回暖'驱动的波段/脉冲行情，非贯穿夏季单极主线。减速器(5月-7月初)主逻辑系人形机器人、归其他Base Pattern，不计入。",
         review_notes="classification=theme_campaign，但降档为medium：结构性/脉冲式、7月中下让位地产/顺周期。8月-9月后汽车再随顺周期轮动。需以智驾/整车指数日线核验精确峰与终点(7/11-7/19)。"),
    dict(annual_review_id="AR-2024", rule_id="rule_auto_summer", year=2024, status="medium",
         summary="2024年6-8月存在两个时间错开、同属'智能驾驶大主线'的脉冲型 Campaign：A)车路云一体化(车路协同/V2X)6月中-6月下旬(6/18高峰、6/24-25退潮)；B)Robotaxi/无人驾驶(智能网约车)7月(7/8启动、7/29高峰、7/31退潮)。两波核心标的不重叠(车路云=华铭/金溢/索菱/万集等设备股；Robotaxi=大众交通/锦江/金龙/江铃等运营+整车)，时间无缝衔接。判定 theme_campaign×2，但均系快涨快退的脉冲炒作、缺持续主线，故 annual status=medium。",
         review_notes="财联社7/24明确：智能驾驶主题炒作已贯穿2个月(6月车路云+7月智能网约车)。10/10特斯拉Robotaxi发布会仅一日脉冲后回落，不作为独立Campaign。两Campaign核心标的时间均明确、证据充分。"),
    dict(annual_review_id="AR-2025", rule_id="rule_auto_summer", year=2025, status="medium",
         summary="2025年夏季存在一段Robotaxi/L4商业化主题 Campaign(6/24 A股无人驾驶涨停潮启动，伴随萝卜快跑/小马智行Robotaxi规模化、汽零8月独立走强)。但强度需降档：a)特斯拉FSD 2025年未正式落地(2026-05-21才宣布监督版入华)，点火源是'Robotaxi试点'而非'FSD入华'；b)夏季涨幅部分来自8月大盘牛市β(沪指+8%/创业板+24%)，汽车非唯一主线；c)渤海汽车重组/众泰订单/中通客车重组等系个股事件、剥离。判定 theme_campaign、strength=medium，9月(Robotaxi龙头)/12月(L3准入)另有两轮催化、超夏季窗口。",
         review_notes="重要：classification=theme_campaign但受大盘β与FSD未落地双重约束，勿高估。8月汽零+16.04%更多由'机器人跨界+AI液冷'第二曲线与技术牛市β驱动。个股资本运作不计入行业Campaign。"),
]
for a in annual_2023_25:
    ins("annual_reviews", a)

# ---- 2023—2025 Themes ----
themes_2023_25 = [
    dict(theme_id="TH-V2X", name="车路云一体化/车路协同", theme_type="concept", parent_theme_id="TH-AUTO", description="V2X/车路协同设备与试点(2024主升)"),
    dict(theme_id="TH-ROBOTAXI", name="Robotaxi/无人驾驶/智能网约车", theme_type="concept", parent_theme_id="TH-AUTO", description="无人驾驶商业化运营、网约车(2024/2025主升)"),
]
for t in themes_2023_25:
    ins("themes", t)

# ---- 2023—2025 Events ----
events_2023_25 = [
    dict(event_id="EV-2023-01", date="2023-06-21", name="工信部吹风会：支持L3及以上自动驾驶商业化、启动准入和上路通行试点", event_type="policy", description="政策预期信号(非落地)；7月智能驾驶行情的起点", source_id="S-2023-01"),
    dict(event_id="EV-2023-02", date="2023-07-03", name="比亚迪首发'天神之眼'高阶智驾(腾势N7)", event_type="company", description="智能驾驶高端化催化，7/4无人驾驶涨停潮导火索", source_id="S-2023-04"),
    dict(event_id="EV-2023-03", date="2023-11-17", name="四部委《智能网联汽车准入和上路通行试点》通知", event_type="policy", description="正式L3文件成文、非夏季；作为夏季行情'未落地'反证", source_id="S-2023-07"),
    dict(event_id="EV-2023-04", date="2023-05-17", name="马斯克股东会展示人形机器人Optimus进展", event_type="company", description="点燃减速器/机器人题材(非汽车)，归其他Base Pattern", source_id="S-2023-09"),
    dict(event_id="EV-2024-01", date="2024-06-14", name="武汉车路云一体化示范项目备案170.84亿", event_type="policy", description="紧随北京99亿招标，车路云启动导火索", source_id="S-2024-08"),
    dict(event_id="EV-2024-02", date="2024-07-03", name="五部门公布20个车路云一体化试点城市", event_type="policy", description="顶层政策信号", source_id="S-2024-01"),
    dict(event_id="EV-2024-03", date="2024-07-10", name="萝卜快跑武汉跑出圈，无人驾驶板块大涨4%", event_type="market", description="Robotaxi主线点火(订单暴涨+百度港股+12%)", source_id="S-2024-04"),
    dict(event_id="EV-2024-04", date="2024-10-10", name="特斯拉Robotaxi发布会(无方向盘Cybercab)", event_type="company", description="美西10/10、北京时间10/11；仅一日脉冲后回落，不作为独立Campaign", source_id="S-2024-06"),
    dict(event_id="EV-2025-01", date="2025-06-22", name="特斯拉奥斯汀启动Robotaxi有偿试运营", event_type="company", description="2025年夏季板块启动点火", source_id="S-2025-02"),
    dict(event_id="EV-2025-02", date="2025-06-24", name="A股无人驾驶板块全线爆发涨停潮", event_type="market", description="板块级启动确认", source_id="S-2025-01"),
    dict(event_id="EV-2025-03", date="2025-10-15", name="渤海汽车重组获批涨停(个股事件)", event_type="company", description="个股资本运作，剥离不计入行业Campaign", source_id="S-2025-05"),
]
for ev in events_2023_25:
    ins("events", ev)

# ---- 2023—2025 Securities ----
securities_2023_25 = [
    dict(security_id="ZHEJIANGSHISHI", ticker="002703", name="浙江世宝", exchange="SZ"),
    dict(security_id="DESAYSV", ticker="002920", name="德赛西威", exchange="SZ"),
    dict(security_id="ZTELEVISION", ticker="000980", name="众泰汽车", exchange="SZ"),
    dict(security_id="SUOLING", ticker="002766", name="索菱股份", exchange="SZ"),
    dict(security_id="JINYI", ticker="002869", name="金溢科技", exchange="SZ"),
    dict(security_id="VANJI", ticker="300552", name="万集科技", exchange="SZ"),
    dict(security_id="HUAMING", ticker="300462", name="华铭智能", exchange="SZ"),
    dict(security_id="DADONGTRAFFIC", ticker="600611", name="大众交通", exchange="SH"),
    dict(security_id="JINJIANGONLINE", ticker="600650", name="锦江在线", exchange="SH"),
    dict(security_id="JINLONG", ticker="600686", name="金龙汽车", exchange="SH"),
    dict(security_id="JIANGLING", ticker="000550", name="江铃汽车", exchange="SZ"),
]
for s in securities_2023_25:
    ins("securities", s)

# ---- 2023—2025 Campaigns ----
campaigns_2023_25 = [
    dict(campaign_id="C-2023-AD", annual_review_id="AR-2023", rule_id="rule_auto_summer",
         season_id="summer_2023", campaign_year=2023,
         start_date="2023-06-12", end_date="2023-07-19", peak_date="2023-07-11",
         strength="medium", result="positive", classification="theme_campaign",
         start_date_basis="6/12汽车产业链爆发展开预热(赛力斯等10余股涨停)；6/21工信部吹风表态支持L3及以上商业化(据S-2023-01)；赛力斯6/8见底",
         end_date_basis="7/11主线确认后，7月中下汽车让位地产/顺周期、存量资金快速轮动(据E-2023-07)；窗口暂记至7/19，需日线核验精确终点", date_confidence="medium",
         drift_vs_jun01=11, drift_vs_jul01=-19, drift_vs_aug01=-50,
         description="智能驾驶/无人驾驶+汽车产业链 波段题材 Campaign。6月政策预期(工信部L3吹风)+销量回暖预热，7/3-4整车/智驾全面爆发(25股涨停、整车指数创4月新高、申万汽车涨幅居首)，7/11主线确认后7月中下退潮。龙头：浙江世宝(总龙/翻倍)、德赛西威(+80%)、万安科技(+70%)、众泰、赛力斯。减速器(5月-7月初)系人形机器人题材不计入。",
         research_notes="关键反例：正式L3准入文件成文2023-11-17、非夏季；2023年FSD未在华落地。夏季系'政策预期+销量回暖'驱动、结构性/脉冲式、非贯穿夏季单极主线，故strength=medium。classification=theme_campaign。"),
    dict(campaign_id="C-2024-V2X", annual_review_id="AR-2024", rule_id="rule_auto_summer",
         season_id="summer_2024", campaign_year=2024,
         start_date="2024-06-11", end_date="2024-06-25", peak_date="2024-06-18",
         strength="medium", result="positive", classification="theme_campaign",
         start_date_basis="6/11车联网概念指数起涨；6/14武汉车路云170.84亿备案、6/18车路云全线爆发10余股涨停(据S-2024-02/S-2024-08)",
         end_date_basis="6/24-25退潮：索菱断板跌停、金溢逼近跌停、华铭跌近15%(据E-2024-04)", date_confidence="medium",
         drift_vs_jun01=10, drift_vs_jul01=-20, drift_vs_aug01=-51,
         description="车路云一体化(V2X/车路协同)主题 Campaign。政策+大单驱动(5/31北京99亿招标、6/14武汉170亿、7/3五部门20城试点)。6/18高峰10余股涨停，核心股华铭/金溢/索菱/万集。约2周脉冲、6/24-25退潮。",
         research_notes="属性=政策驱动题材，但快涨快退(约2周)、公司多公告'未参与'实为题材炒作；与Robotaxi为先后衔接两波、资金同源但不同时段。"),
    dict(campaign_id="C-2024-ROBOTAXI", annual_review_id="AR-2024", rule_id="rule_auto_summer",
         season_id="summer_2024", campaign_year=2024,
         start_date="2024-07-08", end_date="2024-07-31", peak_date="2024-07-29",
         strength="strong", result="positive", classification="theme_campaign",
         start_date_basis="7月上旬萝卜快跑武汉出圈订单暴涨；7/8大众交通启动、7/10无人驾驶板块大涨4%天迈/经纬恒润20cm涨停(据S-2024-04)",
         end_date_basis="7/31大众交通9连板终结、大众公用天地板、港股暴跌22.75%；7/24高位亏钱效应放大(据E-2024-07)", date_confidence="medium",
         drift_vs_jun01=37, drift_vs_jul01=7, drift_vs_aug01=-24,
         description="Robotaxi/无人驾驶主题 Campaign。催化：萝卜快跑武汉跑出圈(订单暴涨)+7/10板块+4%。龙头：大众交通(16日涨233%)、锦江在线(15天9板)、金龙汽车(12天7板)、江铃。约3周脉冲、7月下旬高峰、7/31退潮。",
         research_notes="与车路云同属'智能驾驶大主线'但时间错开、核心标的不重叠，拆为独立Campaign。10/10特斯拉Robotaxi发布会仅一日脉冲后回落，不作为独立Campaign。"),
    dict(campaign_id="C-2025-ROBOTAXI", annual_review_id="AR-2025", rule_id="rule_auto_summer",
         season_id="summer_2025", campaign_year=2025,
         start_date="2025-06-22", end_date="2025-08-31", peak_date="2025-06-24",
         strength="medium", result="positive", classification="theme_campaign",
         start_date_basis="6/22特斯拉奥斯汀Robotaxi收费试点；6/24 A股无人驾驶板块涨停潮(据S-2025-01/02)",
         end_date_basis="8月板块随大盘牛β放量但缺乏独立主线；9月/12月另有两轮L3/智驾催化超出夏季窗口；窗口暂记至8/31", date_confidence="medium",
         drift_vs_jun01=21, drift_vs_jul01=-9, drift_vs_aug01=-40,
         description="Robotaxi/L4商业化主题 Campaign。6/24 A股无人驾驶涨停潮，叠加萝卜快跑/小马智行Robotaxi规模化、汽零8月独立走强(+16.04%)。龙头浙江世宝、德赛西威。但夏季涨幅部分来自8月大盘牛市β、特斯拉FSD 2025年未落地，且渤海汽车重组/众泰订单/中通客车重组等个股事件需剥离。",
         research_notes="classification=theme_campaign但强度medium；FSD 2025未正式落地系重要反例(2026-05-21才宣布监督版入华)，点火源为'Robotaxi试点'而非'FSD入华'；个股资本运作不算行业Campaign。"),
]
for c in campaigns_2023_25:
    ins("campaigns", c)

# ---- 2023—2025 campaign_themes ----
campaign_themes_2023_25 = [
    dict(campaign_id="C-2023-AD", theme_id="TH-AD", role="main"),
    dict(campaign_id="C-2023-AD", theme_id="TH-AUTO", role="related"),
    dict(campaign_id="C-2024-V2X", theme_id="TH-V2X", role="main"),
    dict(campaign_id="C-2024-V2X", theme_id="TH-AUTO", role="related"),
    dict(campaign_id="C-2024-ROBOTAXI", theme_id="TH-ROBOTAXI", role="main"),
    dict(campaign_id="C-2024-ROBOTAXI", theme_id="TH-AUTO", role="related"),
    dict(campaign_id="C-2025-ROBOTAXI", theme_id="TH-ROBOTAXI", role="main"),
    dict(campaign_id="C-2025-ROBOTAXI", theme_id="TH-AD", role="secondary"),
    dict(campaign_id="C-2025-ROBOTAXI", theme_id="TH-AUTO", role="related"),
]
for ct in campaign_themes_2023_25:
    ins("campaign_themes", ct)

# ---- 2023—2025 campaign_events ----
campaign_events_2023_25 = [
    dict(campaign_id="C-2023-AD", event_id="EV-2023-01", role="trigger"),
    dict(campaign_id="C-2023-AD", event_id="EV-2023-02", role="catalyst"),
    dict(campaign_id="C-2023-AD", event_id="EV-2023-03", role="context"),
    dict(campaign_id="C-2024-V2X", event_id="EV-2024-01", role="trigger"),
    dict(campaign_id="C-2024-V2X", event_id="EV-2024-02", role="catalyst"),
    dict(campaign_id="C-2024-ROBOTAXI", event_id="EV-2024-03", role="trigger"),
    dict(campaign_id="C-2025-ROBOTAXI", event_id="EV-2025-01", role="trigger"),
    dict(campaign_id="C-2025-ROBOTAXI", event_id="EV-2025-02", role="catalyst"),
]
for ce in campaign_events_2023_25:
    ins("campaign_events", ce)

# ---- 2023—2025 campaign_securities ----
campaign_securities_2023_25 = [
    dict(campaign_id="C-2023-AD", security_id="ZHEJIANGSHISHI", role="leader"),
    dict(campaign_id="C-2023-AD", security_id="DESAYSV", role="second_leader"),
    dict(campaign_id="C-2023-AD", security_id="WANAN", role="second_leader"),
    dict(campaign_id="C-2023-AD", security_id="ZTELEVISION", role="representative"),
    dict(campaign_id="C-2024-V2X", security_id="SUOLING", role="leader"),
    dict(campaign_id="C-2024-V2X", security_id="JINYI", role="second_leader"),
    dict(campaign_id="C-2024-V2X", security_id="VANJI", role="second_leader"),
    dict(campaign_id="C-2024-V2X", security_id="HUAMING", role="representative"),
    dict(campaign_id="C-2024-ROBOTAXI", security_id="DADONGTRAFFIC", role="leader"),
    dict(campaign_id="C-2024-ROBOTAXI", security_id="JINJIANGONLINE", role="second_leader"),
    dict(campaign_id="C-2024-ROBOTAXI", security_id="JINLONG", role="second_leader"),
    dict(campaign_id="C-2024-ROBOTAXI", security_id="JIANGLING", role="representative"),
    dict(campaign_id="C-2025-ROBOTAXI", security_id="ZHEJIANGSHISHI", role="leader"),
    dict(campaign_id="C-2025-ROBOTAXI", security_id="DESAYSV", role="second_leader"),
]
for cs in campaign_securities_2023_25:
    ins("campaign_securities", cs)

# ---- 2023—2025 campaign_evidences（v1.5 显式绑定） ----
campaign_evidences_2023_25 = [
    # C-2023-AD（减速器 E-2023-08 属机器人、保持 unbound，年报复例段展示）
    dict(campaign_id="C-2023-AD", evidence_id="E-2023-01", role="supporting"),
    dict(campaign_id="C-2023-AD", evidence_id="E-2023-02", role="supporting"),
    dict(campaign_id="C-2023-AD", evidence_id="E-2023-03", role="supporting"),
    dict(campaign_id="C-2023-AD", evidence_id="E-2023-04", role="supporting"),
    dict(campaign_id="C-2023-AD", evidence_id="E-2023-05", role="supporting"),
    dict(campaign_id="C-2023-AD", evidence_id="E-2023-06", role="contradicting"),
    dict(campaign_id="C-2023-AD", evidence_id="E-2023-07", role="contradicting"),
    # C-2024-V2X
    dict(campaign_id="C-2024-V2X", evidence_id="E-2024-01", role="supporting"),
    dict(campaign_id="C-2024-V2X", evidence_id="E-2024-02", role="supporting"),
    dict(campaign_id="C-2024-V2X", evidence_id="E-2024-03", role="supporting"),
    dict(campaign_id="C-2024-V2X", evidence_id="E-2024-04", role="contradicting"),
    # C-2024-ROBOTAXI
    dict(campaign_id="C-2024-ROBOTAXI", evidence_id="E-2024-05", role="supporting"),
    dict(campaign_id="C-2024-ROBOTAXI", evidence_id="E-2024-06", role="supporting"),
    dict(campaign_id="C-2024-ROBOTAXI", evidence_id="E-2024-07", role="contradicting"),
    dict(campaign_id="C-2024-ROBOTAXI", evidence_id="E-2024-08", role="context"),
    # C-2025-ROBOTAXI
    dict(campaign_id="C-2025-ROBOTAXI", evidence_id="E-2025-01", role="supporting"),
    dict(campaign_id="C-2025-ROBOTAXI", evidence_id="E-2025-02", role="supporting"),
    dict(campaign_id="C-2025-ROBOTAXI", evidence_id="E-2025-03", role="contradicting"),
    dict(campaign_id="C-2025-ROBOTAXI", evidence_id="E-2025-04", role="contradicting"),
    dict(campaign_id="C-2025-ROBOTAXI", evidence_id="E-2025-05", role="contradicting"),
]
for cew in campaign_evidences_2023_25:
    ins("campaign_evidences", cew)

# ---- 2023—2025 campaign_phases（仅证据充分时记录） ----
phases_2023_25 = [
    dict(phase_id="PH-2023-01", campaign_id="C-2023-AD", phase_type="startup", start_date="2023-06-12", end_date="2023-07-02", description="6月政策预期(L3吹风)+销量回暖预热，赛力斯6/8见底后启动"),
    dict(phase_id="PH-2023-02", campaign_id="C-2023-AD", phase_type="main_rise", start_date="2023-07-03", end_date="2023-07-11", description="7/3-4全面爆发(25股涨停)，7/11智驾主线确认(浙江世宝8天6板)"),
    dict(phase_id="PH-2023-03", campaign_id="C-2023-AD", phase_type="decline", start_date="2023-07-11", end_date="2023-07-19", description="7/11峰值后板块让位地产/顺周期、快速轮动退潮(需日线核验)"),
    dict(phase_id="PH-2024-01", campaign_id="C-2024-ROBOTAXI", phase_type="startup", start_date="2024-07-08", end_date="2024-07-10", description="萝卜快跑出圈点火，大众交通启动、7/10板块+4%"),
    dict(phase_id="PH-2024-02", campaign_id="C-2024-ROBOTAXI", phase_type="main_rise", start_date="2024-07-11", end_date="2024-07-29", description="主升，大众交通16日涨233%、锦江15天9板、金龙12天7板"),
    dict(phase_id="PH-2024-03", campaign_id="C-2024-ROBOTAXI", phase_type="decline", start_date="2024-07-30", end_date="2024-07-31", description="7/31大众交通9连板终结、大众公用天地板退潮"),
    dict(phase_id="PH-2025-01", campaign_id="C-2025-ROBOTAXI", phase_type="main_rise", start_date="2025-06-22", end_date="2025-06-24", description="特斯拉奥斯汀试点→6/24 A股无人驾驶涨停潮；后续受大盘β驱动较杂、不单独记Wave"),
]
for p in phases_2023_25:
    ins("campaign_phases", p)

conn.commit()
conn.close()
print("Seeded OK. DB rows:")
conn = db.connect()
for t in ["sources","evidences","research_rules","annual_reviews","campaigns","themes","campaign_themes","events","campaign_events","securities","campaign_securities","campaign_phases"]:
    print(f"  {t}: {conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]}")
conn.close()