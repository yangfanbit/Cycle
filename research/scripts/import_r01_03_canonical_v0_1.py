#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""import_r01_03_canonical_v0_1.py —— R01-03（资源 / 有色 / 化工）Canonical Import。

依据：`docs/R01_03_INTAKE_REVIEW_v0_1.md` + `docs/R01_03_INTAKE_REVIEW_ADDENDUM_v0_1.md`
     + 本轮 Canonical Decision（Campaign Independence Gate Q1–Q5）。

结果（**6 PROMOTE + 5 RESEARCH_ONLY**）：
  PROMOTE → campaigns 表
    001 工业金属（铜/铝）        → C-2020-RES-NONFERROUS
    002 能源金属（锂）           → C-2020-RES-LITHIUM
    003 稀土                     → C-2020-RES-RAREEARTH
    004 基础化工（能耗双控）     → C-2021-RES-CHEM-DUALCTRL
    005 染料/中间体（响水）      → C-2019-RES-DYE-SHOCK
    007 黄金（2024–2025 央行购金）→ C-2024-RES-GOLD-CB
  RESEARCH_ONLY → **不入 campaigns 表**（仅导出层 research_candidates）
    006 黄金（2019–2020 实际利率）→ RC-2020-RES-GOLD-RATES
    008 农化（化肥）              → RC-2022-RES-FERTILIZER
    009 铜（2024–2025 矿端缺口）  → RC-2025-RES-COPPER
    010 电解铝（2017 行政去产能） → RC-2017-RES-ALUMINUM
    011 化工（2016 环保约束）     → RC-2016-RES-CHEM-ENV

边界：不改 schema · 不改 Research Model v1.0 · 不改 Export Contract · 不改 CMTR v1 · 不改 taxonomy。
幂等：已存在则跳过。
用法：--dry-run | (apply) | --verify
"""

from __future__ import annotations

import io
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(ROOT, "research", "database", "cycle_research.db")
PKG = os.path.join(ROOT, "research", "intake", "packages", "R01-03")

RULE_ID = "rule_resources"
PROV = "R01-03 Intake Package（source_commit 2153f6d）｜Canonical Decision docs/R01_03_INTAKE_REVIEW_v0_1.md + ADDENDUM_v0_1.md"

# ---------------------------------------------------------------- Campaign 决策表
CAMPAIGNS = [
    dict(
        k="001", cid="C-2020-RES-NONFERROUS", year=2020,
        start="2020-03-23", peak="2021-09-13", end="2021-12-31",
        cls="theme_campaign", strength="strong", result="positive", dc="medium",
        cycle="resource_reflation_2020_2022",
        themes=[("TH-RES", "related"), ("TH-RES-METAL", "main")],
        notes=(
            "★ CF001 裁决：**判为独立 Campaign**（非「2021 大宗商品超级周期」的组成部分）。"
            "Gate：Q1 注意力中心 = 全球流动性宽松 + 需求复苏 + 矿产供给约束（与 003 的配额型、004 的行政限产不同）；"
            "Q2 代表标的（江西铜业/云南铜业/紫金矿业/中国铝业/云铝股份）与 003/004 **不重叠**；"
            "Q4 生命周期独立（peak 2021-09-13，与 003 的 2021-11 及 004 的 2021-10 不同步）。"
            "四个 2021 并行结构由**上位 Theme Cycle** `resource_reflation_2020_2022`（Pattern = Parallel）承载 —— "
            "即 CF001 的 P1（多 Campaign）在 Campaign 层成立，P2（同一大周期）在 Theme Cycle 层成立。"
            "★ **peak = 2021-09-13**（中证有色金属指数 000819.SH 区间最高 8603.88 点，E007）—— "
            "**采用 A 股板块指数口径**，与既有 canonical 惯例一致；**商品口径峰值 2021-05-10**（LME 铜 10747.5 美元/吨，E001）"
            "**作为 alternative 保留**，**不强行同步**（CF006 同源问题）。"
            "★ CF005（2021 年涨幅口径）**保留**：申万一级 40.47%（E005/E006）vs 中证有色金属 31.31%（E007），引用时必须说明口径。"
            "★ CF012：中国铝业/云铝股份 同时属本 Campaign 与 004/010 —— 多主业为合法历史事实，**不构成合并理由**。"
        ),
    ),
    dict(
        k="002", cid="C-2020-RES-LITHIUM", year=2020,
        start="2020-10-27", peak="2021-09-13", end="2022-11-11",
        cls="theme_campaign", strength="strong", result="positive", dc="medium",
        cycle="resource_reflation_2020_2022",
        themes=[("TH-RES", "related"), ("TH-RES-METAL", "main")],
        notes=(
            "★ CF006 裁决（**商品 peak ≠ A 股 peak**）：**canonical peak = 2021-09-13**"
            "（能源金属指数 399366.SZ 区间最高点；天齐锂业 +451.88%、赣锋锂业 +180.74%，E015）—— 采用 **A 股口径**；"
            "**商品口径峰值 2022-11-11**（电池级碳酸锂 59 万元/吨，E012/E013）**作为 alternative 保留**，"
            "**不强行同步**（两者相差约 14 个月）。"
            "★ CF003（跨族归属）**保留为未决**：本 Campaign 的 Macro Theme 归属按 **CMTR v1 解析结果**置于 `资源` 根下 `有色金属` 子主题；"
            "「是否应归 电力设备 / 汽车」属跨族问题，CMTR v1 **不回答**，**保留 Conflict**，**不新增 canonical theme**。"
            "★ end = 2022-11-11（商品周期见顶日，为本结构最后一个有证据的上行锚点）；"
            "**A 股自 2021-09-16 起即转跌**（CF006 P2），领先商品约 14 个月。"
        ),
    ),
    dict(
        k="003", cid="C-2020-RES-RAREEARTH", year=2020,
        start="2020-05-01", peak="2021-11-09", end="2021-12-31",
        cls="theme_campaign", strength="medium", result="positive", dc="medium",
        cycle="resource_reflation_2020_2022",
        themes=[("TH-RES", "related"), ("TH-RES-RARE", "main")],
        notes=(
            "★ CF004（机制归类：资源属性 vs 政策属性）**保留 KEEP_BOTH**："
            "两侧均有证据 —— P1 资源属性（缅甸矿进口下降、分离企业减停产、现货稀少，E023）；"
            "P2 政策属性（开采/冶炼分离总量控制指标 16.8/16.2 万吨、央企整合、出口管制，E022/E026）。"
            "两者真实并存，**不机械归并**。"
            "★ **已知证据缺口（本轮降级 strength 至 medium 的原因）**："
            "本候选 7 条 evidence **全部为商品价格 / 行业指标 / 公司业绩口径**（E021–E027），"
            "**没有任何 A 股板块指数或个股行情证据** —— 即「商品/行业机制 → A 股市场响应」这一环"
            "**未被证据直接支持**。因此：① `strength` 由 strong 降为 **medium**；"
            "② **不得声称已完成 A 股市场响应验证**；③ 建议后续轮次补齐稀土永磁板块指数序列。"
            "（公司级证据 E027「北方稀土 2021 年归母净利润 +462.32%」仅能证明行业景气，"
            "**不等同于**市场关注。）"
            "★ peak = 2021-11-09（北方稀土挂牌价氧化镨钕 76.26 万元/吨，E026）。"
        ),
    ),
    dict(
        k="004", cid="C-2021-RES-CHEM-DUALCTRL", year=2021,
        start="2021-08-12", peak="2021-10-31", end="2021-12-31",
        cls="theme_campaign", strength="strong", result="positive", dc="medium",
        cycle="resource_reflation_2020_2022",
        themes=[("TH-RES", "related"), ("TH-RES-CHEM", "main")],
        notes=(
            "★ CF002（2021 电解铝机制归属）**保留 KEEP_BOTH**：电解铝同时受「工业金属再通胀」（001）与"
            "「能耗双控行政限产」（本 Campaign）两套机制影响（E092/E095 云南限电致云铝减少 77 万吨产能；"
            "E002 有色协会将铝与铜并列归因）。两机制真实并存，**不机械归并**。"
            "★ 行政限产链条：E033（2021-03-10 内蒙古）→ E031（2021-08-12 发改委晴雨表）→ E032（2021-09-11 云南）→ E034（2021-09 江浙）。"
            "★ peak = 2021-10-31（多地化工企业停车减产、纯碱/黄磷等价格飙升，E036）。"
            "★ CF011（双控方案印发日期 2021-09-11 / 2021-09-16）**保留 KEEP_BOTH**，本 Campaign 的 start 采用 **2021-08-12**（E031，一手文件），不依赖该争议日期。"
        ),
    ),
    dict(
        k="005", cid="C-2019-RES-DYE-SHOCK", year=2019,
        start="2019-03-21", peak="2019-04-04", end="2019-07-30",
        cls="event_driven", strength="medium", result="positive", dc="medium",
        cycle="dye_shock_2019",
        themes=[("TH-RES", "related"), ("TH-RES-CHEM", "main")],
        notes=(
            "机制 = **安全事故型供给冲击**（区别于 004 的行政限产、011 的环保约束、010 的行政去产能、003 的配额约束）——"
            "本包「供给收缩」五子类型之一。"
            "★ 链条：E041（2019-03-21 响水爆炸）→ E042（间苯二胺三大核心工厂之一 → 供应短缺）→ "
            "E044（2019-03-22 分散染料板块集体高开、浙江龙盛一字板）→ E043（2019-04-04 关闭响水化工园区）。"
            "★ peak = 2019-04-04（园区彻底关闭决定，政策冲击高点）。"
            "★ **已知缺口**：缺退潮段证据（无可引用的染料价格序列与板块指数序列），`end = 2019-07-30`（E045，最后有证据的日期），"
            "**不主张该 Campaign 已在某确定日期结束**。"
            "★ CF008（响水事故伤亡人数通报口径 44 / 78 人）**保留 KEEP_BOTH** —— 滚动通报，不同统计时点，"
            "**不得把后一数字当作事发当日已知信息**。"
        ),
    ),
    dict(
        k="007", cid="C-2024-RES-GOLD-CB", year=2024,
        start="2024-02-01", peak=None, end=None,
        cls="theme_campaign", strength="medium", result="positive", dc="low",
        cycle="gold_cb_demand_2024_2025",
        themes=[("TH-RES", "related"), ("TH-RES-PRECIOUS", "main")],
        notes=(
            "★ CF009（2025-12「现货热、股价冷」背离）**保留 UNRESOLVED** —— **不消解**。"
            "P1 金价与基本面同向（E063：2024 年全球央行购金 1045 吨、占比 21%；2025 前三季度净购金 634 吨；"
            "E061：2025-02-11 现货金一度 2942.7 美元/盎司创历史新高）；"
            "P2 A 股股价未同步（2025-12 金价创 4526 美元/盎司新高时，山东黄金/招金矿业等仍低于 10 月初高点）。"
            "★ **`peak_date = NULL`** —— **A 股口径峰值未被证据支持**。"
            "E064（2025-09-30）仅能证明「2025 年以来 A 股黄金股指数整体上涨超一倍」，**未给出峰值日期**；"
            "商品口径峰值 2025-12-26（4526 美元/盎司）**不得直接用作 A 股 Campaign 的 peak**"
            "（CF006 同类问题：商品 peak ≠ A 股 peak）→ **不人为强行同步**，保留 NULL 并在本注记记录。"
            "★ **`end_date = NULL`** —— 结构在研究窗口结束时仍在延续，生命周期未闭合。"
            "★ `date_confidence = low`（start 为包内 DATE_WINDOW 左沿 2024-02-01，缺该时点的直接证据）。"
            "★ **未声称完成 Beta 中性验证**：本 Campaign 的 A 股响应证据（E064）为**绝对涨幅**口径，"
            "**不能排除整体市场 Beta**，故 `strength = medium` 而非 strong。"
        ),
    ),
]

RESEARCH_ONLY = [
    dict(
        k="006", cid="RC-2020-RES-GOLD-RATES", year=2020,
        start="2019-05-01", peak="2020-08-07", end="2020-12-31",
        cls="theme_campaign", cycle="gold_rates_2019_2020",
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。理由：**4 条 evidence 全部为商品端**"
            "（E051 金价 / E052 美联储资产负债表 / E053 COMEX 期货 / E054 2019 金价），"
            "**A 股板块证据为零** —— 而「市场关注」为 Campaign 五要素之一，"
            "`why_campaign` 断言「市场关注充分」**无证据支撑**。"
            "本候选代表标的（山东黄金/中金黄金/湖南黄金）虽在 securities 中列出，但**无任何行情证据**。"
            "★ CF007（2020 金价峰值三口径：伦敦现货盘中 2075.14 / COMEX 期货盘中 2089.20 / 期货结算 2069.40）"
            "**保留 KEEP_BOTH** —— 本 RC 的 peak 仅记录商品口径 2020-08-07，供后续复核。"
            "→ 建议补 A 股黄金板块指数序列后重新评估。"
        ),
    ),
    dict(
        k="008", cid="RC-2022-RES-FERTILIZER", year=2022,
        start="2021-01-01", peak="2022-03-31", end="2022-11-30",
        cls="mixed", cycle="fertilizer_cost_2021_2022",
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。理由（**采用 Addendum 修正后的真实表述**）："
            "① **PIT 证据 = 0** —— 5 条 evidence 中 4 条为 `subsequent`（E071 FAO 2022-12-05、E072 USDA 2022-04-06、"
            "E073/E074 商务部 2023-01-13），唯一的 A 股证据 `E075` 虽为 **`contemporaneous`**"
            "（化肥概念板块 2021-01-04~2021-12-31 **+24.24%**，区间最高 1048.07 点 @2021-09-28），"
            "但其 `support_kind` **不含 `point_in_time_support`** —— 故「无同期可观察证据可直接锁定 A 股主题启动」。"
            "② **传导无法确认**：E075 的峰值（2021-09-28）早于本候选观测到的商品 peak 窗口（2022-03—2022-04）"
            "**约半年**，包内证据**无法判定二者是否属同一结构或存在领先滞后关系**。"
            "★ **明确不作反例结论**：上一轮 Intake Review 已判定原 `why_not` 的"
            "「商品上涨期 A 股板块未同步」定性**不成立**（其 -12.05% 窗口起点 2022-03-15 ≈ 本候选自身峰值，"
            "度量的是峰值后下跌段，且与 E075 的 +24.24% 直接矛盾）；Worker 已**显式撤回**该定性。"
            "**本 RC 的核心缺口是「无法确认传导」，不是「存在反例」。**"
            "★ 附带：Worker 修正稿中「全部 evidence 均为 subsequent」的表述**与数据不符**（E075 为 contemporaneous）—— "
            "本条注记采用**修正后的真实表述**（E075 为 contemporaneous 但无 PIT 标注）。"
            "→ 建议补 2022 年逐月板块序列与同期政策/价格锚点后重新评估。"
        ),
    ),
    dict(
        k="009", cid="RC-2025-RES-COPPER", year=2025,
        start="2024-03-01", peak="2025-12-31", end=None,
        cls="industry_trend", cycle="copper_mine_gap_2024_2025",
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。理由：**5 条 evidence 全部为商品端**"
            "（E081 LME 铜 11104.5 / E082 矿端扰动 / E083 LME 铜 11000 / E084 2025 铜价 +30% / E085 加工费降至 21.3 美元），"
            "**无任何 A 股铜板块指数或个股行情证据** —— 包内 `why_not ②` 自述"
            "「商品与 A 股铜板块的传导证据不足（本任务未收集到足够的板块行情证据）」✓ **Worker 自身已承认该缺口**。"
            "★ 与 001 的边界：CF001 裁决 001 为独立 Campaign；本候选与 001 同属铜价周期，"
            "「一个铜长周期 vs 两个独立阶段」的争议**保留**，因本候选未进入 canonical 层，本轮**不裁决**。"
        ),
    ),
    dict(
        k="010", cid="RC-2017-RES-ALUMINUM", year=2017,
        start="2017-04-12", peak="2017-08-09", end="2017-12-31",
        cls="theme_campaign", cycle="aluminum_capacity_cut_2017",
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。理由：**无任何 A 股权益行情证据** —— "
            "6 条 evidence 为政策文件（E091 四部委通知）+ 关停产能（E092/E096）+ **沪铝期货**（E093/E095）"
            "+ 产量（E094）。E093「沪铝 1710 合约 9 个交易日飙升至 16215 元/吨」属**商品期货**口径，"
            "**不是 A 股权益**。包内 `why_not` 自述「缺少可引用的电解铝板块指数与个股行情序列，"
            "A 股市场扩散证据弱于商品端」✓ **Worker 自身已承认该缺口**。"
            "★ 本候选的 **PIT 覆盖为全包最优（5/6）**，机制链条（行政去产能）清晰且为一手文件 —— "
            "**若补齐 A 股板块指数序列，应优先重新评估**。"
        ),
    ),
    dict(
        k="011", cid="RC-2016-RES-CHEM-ENV", year=2016,
        start="2016-01-04", peak=None, end=None,
        cls="unclear", cycle="chem_env_constraint_2016",
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。理由：① `research_status = INSUFFICIENT` · `confidence = low` · **0 securities**；"
            "② **同窗口反例有效**：E101（2016 化工商品指数 618→833，均涨跌幅 +29.84%）vs "
            "E105（**申万基础化工板块 2016-01-04 至 2016-12-30 = -7.13%**，`contradicting`）—— "
            "**两者为同一完整年度窗口**，商品上行未伴随 A 股板块行情；"
            "③ 缺板块内部结构证据（不知哪些子行业/标的上涨）；④ 无可识别的启动锚点与扩散过程。"
            "★ CF010 **保留 KEEP_BOTH**：这是本包最重要的反例 —— 「商品价格上涨**不构成** A 股主题启动的充分条件」。"
            "★ 与 008 的区别：011 的反例**同窗口有效**；008 的反例**窗口错位、已被撤回**。"
        ),
    ),
]

ANNUAL = {
    2019: ("medium", "染料/中间体安全事故型供给冲击（响水 3·21）；事件驱动，退潮段证据不足。"),
    2020: ("strong", "资源/有色再通胀周期启幕：工业金属（铜/铝）、能源金属（锂）、稀土三条并行结构。"),
    2021: ("strong", "能耗双控行政限产（基础化工）；同期工业金属与锂达到峰值。"),
    2024: ("medium", "黄金：官方部门结构性购金驱动的新一轮上行；**CF009 商品与 A 股背离未决，peak 未确认。**"),
}

# 证券助记符（大写助记符，沿用既有惯例）
SEC_CANON = {
    "R01-RESOURCES-SEC001": ("JXCOPPER", "600362", "江西铜业", "SH"),
    "R01-RESOURCES-SEC002": ("YNCOPPER", "000878", "云南铜业", "SZ"),
    "R01-RESOURCES-SEC003": ("ZIJIN", "601899", "紫金矿业", "SH"),
    "R01-RESOURCES-SEC004": ("TONGLING", "000630", "铜陵有色", "SZ"),
    "R01-RESOURCES-SEC005": ("CHALCO", "601600", "中国铝业", "SH"),
    "R01-RESOURCES-SEC006": ("YUNAL", "000807", "云铝股份", "SZ"),
    "R01-RESOURCES-SEC007": ("SHENHUO", "000933", "神火股份", "SZ"),
    "R01-RESOURCES-SEC008": ("TIANQI", "002466", "天齐锂业", "SZ"),
    "R01-RESOURCES-SEC009": ("GANFENG", "002460", "赣锋锂业", "SZ"),
    "R01-RESOURCES-SEC010": ("SINOMINE", "002738", "中矿资源", "SZ"),
    "R01-RESOURCES-SEC011": ("YONGXING", "002756", "永兴材料", "SZ"),
    "R01-RESOURCES-SEC012": ("SALTLIAKE", "000792", "盐湖股份", "SZ"),
    "R01-RESOURCES-SEC013": ("NPRARE", "600111", "北方稀土", "SH"),
    "R01-RESOURCES-SEC014": ("SHENGHE", "600392", "盛和资源", "SH"),
    "R01-RESOURCES-SEC015": ("CNRAREEARTH", "000831", "中国稀土", "SZ"),
    "R01-RESOURCES-SEC016": ("GUANGSHENG", "600259", "广晟有色", "SH"),
    "R01-RESOURCES-SEC017": ("HUBEIYIHUA", "000422", "湖北宜化", "SZ"),
    "R01-RESOURCES-SEC018": ("YUNTIANHUA", "600096", "云天化", "SH"),
    "R01-RESOURCES-SEC019": ("XINGFA", "600141", "兴发集团", "SH"),
    "R01-RESOURCES-SEC020": ("HOSHINE", "603260", "合盛硅业", "SH"),
    "R01-RESOURCES-SEC021": ("LONGSHENG", "600352", "浙江龙盛", "SH"),
    "R01-RESOURCES-SEC022": ("RUNTE", "002440", "闰土股份", "SZ"),
    "R01-RESOURCES-SEC023": ("SDGOLD", "600547", "山东黄金", "SH"),
    "R01-RESOURCES-SEC024": ("ZJGOLD", "600489", "中金黄金", "SH"),
    "R01-RESOURCES-SEC025": ("CFGOLD", "600988", "赤峰黄金", "SH"),
    "R01-RESOURCES-SEC026": ("HNGOLD", "002155", "湖南黄金", "SZ"),
    "R01-RESOURCES-SEC027": ("ASIAPOTASH", "000893", "亚钾国际", "SZ"),
    "R01-RESOURCES-SEC028": ("XINYANGFENG", "000902", "新洋丰", "SZ"),
    "R01-RESOURCES-SEC029": ("WANHUA", "600309", "万华化学", "SH"),
    "R01-RESOURCES-SEC030": ("CMOC", "603993", "洛阳钼业", "SH"),
}

EVENTS = [
    ("EV-RES-01", "2021-05-10", "LME 铜期货 10747.5 美元/吨创历史新高（较 2020 年低点涨幅超一倍）", "market", "R01-RESOURCES-E001"),
    ("EV-RES-02", "2020-10-27", "澳洲锂精矿企业 Altura 进入破产管理（锂精矿供给出清延续）", "industry", "R01-RESOURCES-E011"),
    ("EV-RES-03", "2022-11-11", "电池级碳酸锂价格达 59 万元/吨 历史高点", "industry", "R01-RESOURCES-E012"),
    ("EV-RES-04", "2021-03-10", "内蒙古印发《关于确保完成「十四五」能耗双控目标若干保障措施》", "policy", "R01-RESOURCES-E033"),
    ("EV-RES-05", "2021-08-12", "国家发改委印发《2021 年上半年各地区能耗双控目标完成情况晴雨表》(发改办环资〔2021〕629 号)", "policy", "R01-RESOURCES-E031"),
    ("EV-RES-06", "2021-09-11", "云南省发布《关于坚决做好能耗双控有关工作的通知》（工业硅月均产量不得超过 8 月产量 10%）", "policy", "R01-RESOURCES-E032"),
    ("EV-RES-07", "2021-10-31", "江苏/云南/陕西等多地化工企业停车减产，纯碱、黄磷等原料价格飙升", "industry", "R01-RESOURCES-E036"),
    ("EV-RES-08", "2019-03-21", "江苏响水天嘉宜化工有限公司发生特别重大爆炸事故（间苯二胺核心产能受损）", "industry", "R01-RESOURCES-E041"),
    ("EV-RES-09", "2019-03-22", "分散染料板块集体高开大涨，浙江龙盛一字板涨停（封单超 28 万手）", "market", "R01-RESOURCES-E044"),
    ("EV-RES-10", "2019-04-04", "江苏盐城市委常委会决定彻底关闭响水化工园区", "policy", "R01-RESOURCES-E043"),
    ("EV-RES-11", "2020-08-17", "美联储资产负债表自约 4.3 万亿美元扩至 7.1 万亿美元，金价自 1450 升至 2075 美元/盎司附近", "macro", "R01-RESOURCES-E052"),
    ("EV-RES-12", "2021-10-28", "氧化镨钕价格自 10 月初 59.8 万元/吨涨至 73.5 万元/吨", "industry", "R01-RESOURCES-E024"),
    ("EV-RES-13", "2021-11-09", "北方稀土更新挂牌价，氧化镨钕升至 76.26 万元/吨", "industry", "R01-RESOURCES-E026"),
    ("EV-RES-14", "2025-02-11", "国际现货黄金一度涨至 2942.7 美元/盎司，创历史新高", "market", "R01-RESOURCES-E061"),
    ("EV-RES-15", "2025-09-30", "2025 年以来 A 股黄金股指数整体上涨超一倍（紫金矿业、山东黄金等）", "market", "R01-RESOURCES-E064"),
]

CAMPAIGN_EVENTS = [
    ("C-2020-RES-NONFERROUS", "EV-RES-01", "follow_up"),
    ("C-2020-RES-LITHIUM", "EV-RES-02", "context"),
    ("C-2020-RES-LITHIUM", "EV-RES-03", "follow_up"),
    ("C-2020-RES-RAREEARTH", "EV-RES-12", "catalyst"),
    ("C-2020-RES-RAREEARTH", "EV-RES-13", "follow_up"),
    ("C-2021-RES-CHEM-DUALCTRL", "EV-RES-04", "context"),
    ("C-2021-RES-CHEM-DUALCTRL", "EV-RES-05", "trigger"),
    ("C-2021-RES-CHEM-DUALCTRL", "EV-RES-06", "catalyst"),
    ("C-2021-RES-CHEM-DUALCTRL", "EV-RES-07", "follow_up"),
    ("C-2019-RES-DYE-SHOCK", "EV-RES-08", "trigger"),
    ("C-2019-RES-DYE-SHOCK", "EV-RES-09", "catalyst"),
    ("C-2019-RES-DYE-SHOCK", "EV-RES-10", "follow_up"),
    ("C-2024-RES-GOLD-CB", "EV-RES-11", "context"),
    ("C-2024-RES-GOLD-CB", "EV-RES-14", "catalyst"),
    ("C-2024-RES-GOLD-CB", "EV-RES-15", "follow_up"),
]

# 共享 evidence 的唯一归属（本包共享 = 0，此表为空；保留以备将来）
EVIDENCE_OWNER = {}


def load():
    out = {}
    for name in ("candidates", "evidence", "sources", "securities"):
        with io.open(os.path.join(PKG, name + ".json"), encoding="utf-8") as fh:
            out[name] = json.load(fh)
    return out


def main(argv):
    dry = "--dry-run" in argv
    verify_only = "--verify" in argv
    pkg = load()
    cand_by_k = {c["candidate_id"].split("-")[-1]: c for c in pkg["candidates"]}
    ev_by_id = {e["evidence_id"]: e for e in pkg["evidence"]}

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    def have(table, col, val):
        return cur.execute("SELECT 1 FROM %s WHERE %s=?" % (table, col), (val,)).fetchone() is not None

    plan = []

    def add(table, key, sql, params):
        plan.append((table, key, lambda s=sql, p=params: cur.execute(s, p)))

    # 既有证券复用规则：若助记符已存在且名称一致 → **复用**（同一证券不得重复建行）；
    # 名称不一致 → FAIL（助记符冲突）。
    existing_sec = {r[0]: r[1] for r in cur.execute("SELECT security_id, name FROM securities")}
    reuse_sec = set()
    for intake_id, (sid, _t, nm, _e) in SEC_CANON.items():
        if sid in existing_sec:
            if existing_sec[sid] != nm:
                raise SystemExit("FAIL 证券助记符冲突（名称不一致）: %s 既有=%s 新=%s" % (sid, existing_sec[sid], nm))
            reuse_sec.add(sid)
    if reuse_sec:
        print("  复用既有证券（不重复建行）: %s" % sorted(reuse_sec))

    # ---- rule ----
    if not have("research_rules", "rule_id", RULE_ID):
        add("research_rules", RULE_ID,
            "INSERT INTO research_rules (rule_id,name,base_pattern,description,status) VALUES (?,?,?,?,?)",
            (RULE_ID, "资源 / 有色 / 化工历史周期观察", "资源",
             "R01-03（资源 / 有色 / 化工）历史周期观察窗口。" + PROV, "under_review"))

    # ---- annual_reviews ----
    for yr in sorted(ANNUAL):
        arid = "AR-RES-%d" % yr
        if not have("annual_reviews", "annual_review_id", arid):
            st, summary = ANNUAL[yr]
            add("annual_reviews", arid,
                "INSERT INTO annual_reviews (annual_review_id,rule_id,year,status,summary,review_notes) VALUES (?,?,?,?,?,?)",
                (arid, RULE_ID, yr, st, summary, PROV))

    # ---- campaigns（6 PROMOTE）----
    for c in CAMPAIGNS:
        if not have("campaigns", "campaign_id", c["cid"]):
            add("campaigns", c["cid"],
                "INSERT INTO campaigns (campaign_id,annual_review_id,rule_id,season_id,campaign_year,start_date,end_date,peak_date,"
                "strength,result,classification,start_date_basis,end_date_basis,"
                "date_confidence,description,research_notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (c["cid"], "AR-RES-%d" % c["year"], RULE_ID, c["cycle"], c["year"], c["start"], c["end"], c["peak"],
                 c["strength"], c["result"], c["cls"],
                 "研究候选日期（intake date_candidates）；未经行情核验",
                 "研究候选日期（intake date_candidates）；未经行情核验",
                 c["dc"],
                 "%s［intake R01-RESOURCES-%s］" % (cand_by_k[c["k"]]["title"], c["k"]),
                 c["notes"] + "｜theme_cycle_id=%s｜provenance: %s" % (c["cycle"], PROV)))

    # ---- campaign_themes ----
    for c in CAMPAIGNS:
        for tid, role in c["themes"]:
            if not cur.execute("SELECT 1 FROM campaign_themes WHERE campaign_id=? AND theme_id=?",
                               (c["cid"], tid)).fetchone():
                add("campaign_themes", "%s/%s" % (c["cid"], tid),
                    "INSERT INTO campaign_themes (campaign_id,theme_id,role) VALUES (?,?,?)", (c["cid"], tid, role))

    # ---- securities ----
    for intake_id, (sid, ticker, name, exch) in SEC_CANON.items():
        if sid in reuse_sec:
            continue  # 复用既有行
        if not have("securities", "security_id", sid):
            add("securities", sid,
                "INSERT INTO securities (security_id,ticker,name,exchange) VALUES (?,?,?,?)", (sid, ticker, name, exch))

    # ---- sources ----
    src_map = {}
    for i, s in enumerate(pkg["sources"], start=1):
        sid = "S-RES-%02d" % i
        src_map[s["source_id"]] = sid
        if not have("sources", "source_id", sid):
            add("sources", sid,
                "INSERT INTO sources (source_id,source_type,title,author,url,published_at,captured_at,publisher,description,tier)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (sid, s["source_type"], s["title"], s.get("author"), s.get("url"), s.get("published_at"), None,
                 s["publisher"], "%s［intake %s］" % (s.get("description") or "", s["source_id"]), s["tier"]))

    # ---- evidences（RESEARCH_ONLY 专属不入 DB，与 R01-01/02 同口径）----
    promoted_ev, rc_ev = set(), set()
    for c in CAMPAIGNS:
        promoted_ev |= set(cand_by_k[c["k"]]["evidence_ids"])
    for r in RESEARCH_ONLY:
        rc_ev |= set(cand_by_k[r["k"]]["evidence_ids"])
    RC_ONLY_EV = rc_ev - promoted_ev
    print("  RESEARCH_ONLY 专属 evidence（不入 DB）: %d 条" % len(RC_ONLY_EV))

    ev_map = {}
    for i, e in enumerate(pkg["evidence"], start=1):
        if e["evidence_id"] in RC_ONLY_EV:
            continue
        eid = "E-RES-%02d" % i
        ev_map[e["evidence_id"]] = eid
        if not have("evidences", "evidence_id", eid):
            desc = "%s［intake %s｜role=%s｜independence=%s］" % (
                e["claim"], e["evidence_id"], e["evidence_role"], e["independence_group"])
            if e.get("point_in_time_note"):
                desc += "｜PIT: " + e["point_in_time_note"]
            add("evidences", eid,
                "INSERT INTO evidences (evidence_id,source_id,date,evidence_type,description,evidence_role,confidence,"
                "independence_group,temporal_relation) VALUES (?,?,?,?,?,?,?,?,?)",
                (eid, src_map[e["source_id"]], e.get("event_date"), e["evidence_type"], desc, e["evidence_role"],
                 e["confidence"], e["independence_group"], e["temporal_relation"]))

    # ---- events ----
    ev_src = {e["evidence_id"]: e["source_id"] for e in pkg["evidence"]}
    rc_ev_set = {e for e in RC_ONLY_EV}
    for eid, date, name, etype, intake_ev in EVENTS:
        if intake_ev in rc_ev_set:
            continue
        if not have("events", "event_id", eid):
            add("events", eid,
                "INSERT INTO events (event_id,date,name,event_type,description,source_id) VALUES (?,?,?,?,?,?)",
                (eid, date, name, etype, "%s｜provenance: %s" % (intake_ev, PROV), src_map[ev_src[intake_ev]]))

    # ---- campaign_evidences ----
    for c in CAMPAIGNS:
        for ieid in cand_by_k[c["k"]]["evidence_ids"]:
            owner = EVIDENCE_OWNER.get(ieid)
            if owner is not None and owner != c["k"]:
                continue
            eid = ev_map[ieid]
            if not cur.execute("SELECT 1 FROM campaign_evidences WHERE campaign_id=? AND evidence_id=?",
                               (c["cid"], eid)).fetchone():
                add("campaign_evidences", "%s/%s" % (c["cid"], eid),
                    "INSERT INTO campaign_evidences (campaign_id,evidence_id,role) VALUES (?,?,?)",
                    (c["cid"], eid, ev_by_id[ieid]["evidence_role"]))

    # ---- campaign_events ----
    rc_event_ids = {eid for eid, _d, _n, _t, ie in EVENTS if ie in rc_ev_set}
    for cid, eid, role in CAMPAIGN_EVENTS:
        if eid in rc_event_ids:
            continue
        if not cur.execute("SELECT 1 FROM campaign_events WHERE campaign_id=? AND event_id=?", (cid, eid)).fetchone():
            add("campaign_events", "%s/%s" % (cid, eid),
                "INSERT INTO campaign_events (campaign_id,event_id,role) VALUES (?,?,?)", (cid, eid, role))

    # ---- campaign_securities ----
    for c in CAMPAIGNS:
        for intake_sec in cand_by_k[c["k"]]["security_ids"]:
            sid = SEC_CANON[intake_sec][0]
            if not cur.execute("SELECT 1 FROM campaign_securities WHERE campaign_id=? AND security_id=?",
                               (c["cid"], sid)).fetchone():
                add("campaign_securities", "%s/%s" % (c["cid"], sid),
                    "INSERT INTO campaign_securities (campaign_id,security_id,role) VALUES (?,?,?)",
                    (c["cid"], sid, "representative"))

    # ---- campaign_phases ----
    ph_n = 0
    STAGE = {"MAIN_RISE": "main_rise", "RETRACEMENT": "retracement", "DECLINING": "decline",
             "SECONDARY": "secondary_rally", "PEAK": None, "UNKNOWN": None}
    for c in CAMPAIGNS:
        cand = cand_by_k[c["k"]]
        for l in cand["lifecycle"]:
            stage = l["stage_proposal"]
            if stage not in STAGE or STAGE[stage] is None or not l["start"] or not l["end"]:
                continue
            if l["start"] < c["start"]:
                continue
            end = l["end"]
            if c["end"] and end > c["end"]:
                end = c["end"]
            if end < l["start"]:
                continue
            ph_n += 1
            pid = "PH-RES-%02d" % ph_n
            if not have("campaign_phases", "phase_id", pid):
                add("campaign_phases", pid,
                    "INSERT INTO campaign_phases (phase_id,campaign_id,phase_type,start_date,end_date,description)"
                    " VALUES (?,?,?,?,?,?)",
                    (pid, c["cid"], STAGE[stage], l["start"], end, "%s（intake lifecycle）｜%s" % (stage, PROV)))

    # ---- campaign_date_observations ----
    for c in CAMPAIGNS:
        for role, val in (("start", c["start"]), ("peak", c["peak"]), ("end", c["end"])):
            if not val:
                continue
            oid = "OBS-%s-%s" % (c["cid"], role)
            if not have("campaign_date_observations", "observation_id", oid):
                add("campaign_date_observations", oid,
                    "INSERT INTO campaign_date_observations (observation_id,campaign_id,date_role,candidate_date,verified_date,"
                    "verification_method,confidence,evidence_id,notes) VALUES (?,?,?,?,?,?,?,?,?)",
                    (oid, c["cid"], role, val, None, "unknown", c["dc"], None,
                     "candidate 快照自 R01-03 intake date_candidates；未经行情核验。｜%s" % PROV))

    print("=== 计划写入 %d 行 ===" % len(plan))
    from collections import Counter
    for t, n in sorted(Counter(p[0] for p in plan).items()):
        print("  %-30s %d" % (t, n))
    for t, k, _ in plan:
        print("    + %-30s %s" % (t, k))

    if verify_only:
        print("verify: %s" % ("PASS（全部已存在）" if not plan else "FAIL（仍有 %d 行待写入）" % len(plan)))
        conn.close()
        return 0 if not plan else 1

    if dry:
        print("--dry-run：未写入。")
        conn.close()
        return 0

    for _t, _k, fn in plan:
        fn()
    conn.commit()
    print("=== 写入完成 ===")
    for t in ("themes", "research_rules", "annual_reviews", "campaigns", "sources", "evidences", "events", "securities",
              "campaign_themes", "campaign_evidences", "campaign_events", "campaign_securities", "campaign_phases",
              "campaign_date_observations"):
        print("  %-30s %d" % (t, cur.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]))
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
