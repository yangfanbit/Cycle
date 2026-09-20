#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""import_r01_04_canonical_v0_1.py —— R01-04（消费）Canonical Import。

依据：`docs/R01_04_INTAKE_REVIEW_v0_1.md` + 本轮 Canonical Decision（Independence Gate Q1–Q5）。

结果（**11 PROMOTE + 2 RESEARCH_ONLY**）：
  PROMOTE → campaigns 表
    001 白酒/消费升级 2016–2018   → C-2016-CONS-BAIJIU-UPGRADE
    002 白酒核心资产 2019–2021    → C-2019-CONS-BAIJIU-CORE
    003 海南离岛免税 2019–2021    → C-2020-CONS-DUTYFREE
    004 疫后服务消费修复 2022–2023 → C-2022-CONS-SERVICE-REBOUND
    005 非洲猪瘟超级猪周期         → C-2018-CONS-HOG-AFRICAN
    006 猪周期反转 2021–2022      → C-2021-CONS-HOG-REVERSAL
    008 白电/出口共振 2020–2021    → C-2020-CONS-WHITE-GOODS
    009 医美/颜值经济 2019–2021    → C-2019-CONS-AESTHETICS
    010 国货美妆 2020–2022        → C-2020-CONS-BEAUTY-CN
    011 消费品以旧换新 2024–2025   → C-2024-CONS-TRADE-IN
    012 量贩零食/折扣零售 2023–2025 → C-2023-CONS-VALUE-RETAIL
  RESEARCH_ONLY → **不入 campaigns 表**（仅导出层 research_candidates）
    007 小家电/清洁电器（证据薄 4ev/3IG + PIT=0）→ RC-2020-CONS-SMALL-APPLIANCE
    013 宠物食品（INSUFFICIENT / low）→ RC-2024-CONS-PET-FOOD

边界：不改 schema · 不改 Research Model v1.0 · 不改 Export Contract · 不改 CMTR v1 · 不改 taxonomy。
幂等：已存在则跳过。用法：--dry-run | (apply) | --verify
"""

from __future__ import annotations

import io
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(ROOT, "research", "database", "cycle_research.db")
PKG = os.path.join(ROOT, "research", "intake", "packages", "R01-04")

RULE_ID = "rule_consumer"
PROV = "R01-04 Intake Package（source_commit 2153f6d）｜Canonical Decision docs/R01_04_INTAKE_REVIEW_v0_1.md"

CAMPAIGNS = [
    dict(
        k="001", cid="C-2016-CONS-BAIJIU-UPGRADE", year=2016,
        start="2016-06-01", peak="2018-01-31", end="2018-12-31",
        cls="industry_trend", strength="medium", result="positive", dc="medium",
        cycle="baijiu_premium_2016_2021",
        themes=[("TH-CONSUMER", "related"), ("TH-CONSUMER-FOOD", "main")],
        notes=(
            "★ CF002 裁决：**判为独立 Campaign**（非「同一白酒长周期」的一段）。"
            "Gate：Q1 注意力中心 =「漂亮50 / 白马蓝筹 + 消费升级 + 龙头集中」（国内资金主导），"
            "与 002 的「核心资产 + 外资增量定价（MSCI 扩容）」不同；Q3 持续性成立（约 2.5 年）；"
            "**Q4 独立生命周期成立** —— 中间存在 **2018 年全年 -27% 级别回撤**（中证白酒指数，E007）"
            "与 **2018-10-29 贵州茅台上市以来首个「一」字跌停**（E005/E006），资金逻辑明确重置；"
            "Q5 Residual Test 双向成立。★ **Q2 代表标的不成立**（与 002 完全重叠：茅台/五粮液/泸州老窖）—— "
            "这是唯一反对拆分的 Gate 项；其重叠由「**同一 Theme Cycle 内的 Sequential Campaign**」解释："
            "同一批核心资产在两轮独立周期中重演。"
            "★ 与 002 同属 Theme Cycle `baijiu_premium_2016_2021`（Pattern = **Sequential**）。"
            "★ CF001（classification 歧义）**保留**：本段按 industry_trend 提案，"
            "但 2021 年社零 +12.5%、基本面未恶化而价格大幅回落（E015 统计局口径 vs E013 媒体口径）"
            "说明 002 段资金面权重高 —— 最终 classification 由后续复核裁定。"
            "★ **Priority B 段**：月度批价/动销一手数据缺失，`date_confidence = medium`。"
        ),
    ),
    dict(
        k="002", cid="C-2019-CONS-BAIJIU-CORE", year=2019,
        start="2019-03-01", peak="2021-02-18", end="2021-12-31",
        cls="industry_trend", strength="strong", result="positive", dc="medium",
        cycle="baijiu_premium_2016_2021",
        themes=[("TH-CONSUMER", "related"), ("TH-CONSUMER-FOOD", "main")],
        notes=(
            "★ CF002 裁决：**与 001 为同一 Theme Cycle 下的 Sequential Campaign**（非合并、非拆分）。"
            "启动锚点为 **2019-03-01 MSCI 宣布纳入因子由 5% 提高至 20%**（E009，contemporaneous 一手事件）；"
            "2019 年北向资金净流入 3517.43 亿元创历史新高（E010）。"
            "★ **peak = 2021-02-18**（中证白酒指数 399997 盘中最高 21663.85 点；贵州茅台 2627.88 元、"
            "五粮液 357.19 元、泸州老窖 327.66 元，均不复权，E012）—— **采用 A 股板块指数口径**。"
            "★ CF001（classification）**保留**：P2 指出「2021 年社零 +12.5%、行业需求未恶化，"
            "而板块自 2021-02-18 起大幅回落」（E013 经济参考报 2021-03-29 报道）→ 主导力量为资金抱团与确定性溢价；"
            "本段仍按 industry_trend 提案，**最终 classification 保留待裁**。"
            "★ CF003（2021 年规上白酒收入/利润增速口径）**保留 KEEP_BOTH**："
            "国家统计局口径 6033.48 亿元 / +3.38%（E015）vs 贵州茅台年报引述 +18.6% —— **两者均未用于支撑行业景气强度结论**。"
        ),
    ),
    dict(
        k="003", cid="C-2020-CONS-DUTYFREE", year=2020,
        start="2020-06-01", peak="2021-02-18", end="2022-12-31",
        cls="mixed", strength="strong", result="positive", dc="medium",
        cycle="service_consumption_2020_2023",
        themes=[("TH-CONSUMER", "related"), ("TH-CONSUMER-SERVICE", "main")],
        notes=(
            "★ CF011 裁决：**判为独立 Campaign**（与 004 疫后修复分列）。"
            "Gate：Q1 启动锚点/政策主体/验证数据**三者均不同**（本 Campaign = 财政部公告 33 号 + 海南自贸港方案，"
            "验证 = 海口海关离岛免税销售额；004 = 新十条 + 补偿性需求，验证 = 旅游人次与社零）；"
            "Q4 独立生命周期成立；Q5 双向成立。★ Q2 代表标的部分重叠（中国中免）→ "
            "由「**同一 Theme Cycle 内的 Sequential Campaign**」解释。"
            "★ 链条完整：E017（2020-06-01 海南自贸港总体方案）→ E016/E094（2020-06-29 财政部公告 33 号，"
            "额度 3 万→10 万元/年、不限次数、品类 38→45 类）→ E018（海口海关 2020-07-01~10-31 销售 120.1 亿元、+214.1%）"
            "→ E091（2020 全年 274.8 亿元、+103.7%）→ E019（2021 全年 601.73 亿元、+84%）→ "
            "E020（2021-02-18 中国中免盘中最高 403.78 元，历史最高）→ E022（2022 约 487.1 亿元、-19%）。"
            "★ **已知结构弱点**：`security_ids` 仅 **1 个**（中国中免），**A 股可交易标的广度严重不足** —— "
            "若按 Gate Q2「独立代表资产组」严格衡量，其独立性弱于白酒候选；**不得声称已完成板块广度验证**。"
            "★ 2022 年降温数据仅取得媒体转述（`known_gaps[5]`），`date_confidence = medium`。"
            "★ 与 004 同属 Theme Cycle `service_consumption_2020_2023`（Pattern = **Sequential**）。"
        ),
    ),
    dict(
        k="004", cid="C-2022-CONS-SERVICE-REBOUND", year=2022,
        start="2022-12-07", peak="2023-01-31", end="2023-06-30",
        cls="event_driven", strength="medium", result="positive", dc="medium",
        cycle="service_consumption_2020_2023",
        themes=[("TH-CONSUMER", "related"), ("TH-CONSUMER-SERVICE", "main")],
        notes=(
            "★ CF011 裁决：**与 003 为同一 Theme Cycle 下的 Sequential Campaign**。"
            "机制 = **事件驱动的补偿性需求释放**（与 003 的政策额度放开 + 出境回流替代不同）。"
            "★ 链条：E026（2022-12-07「新十条」）→ E027（2023 春节 3.08 亿人次、+23.1%，恢复至 2019 年 88.6%）"
            "→ E028（2023 五一 2.74 亿人次、+70.83%，恢复至 2019 年 119.09%）→ "
            "E032（2023-01-31 中国中免月内最高 239.99 元）→ E031（2023-04-28~05-31 中免 160.98→123.10 元等回落）。"
            "★ **峰值取 A 股口径 2023-01-31**（中国中免月内最高价，E032）。"
            "★ **持续性为本 Campaign 最脆弱环节**：主升段仅约 **1–2 个月** → `strength` 定为 **medium**"
            "（而非 strong）；保留依据为「需求端有连续两个假期的官方数据验证 + 降温有明确的宏观数据证伪事件 + "
            "代表标的组回落同步」。**不得据此宣称已满足长周期持续性标准。**"
            "★ CF004（**宏观消费数据改善 ≠ 具体消费行业启动**）**保留 KEEP_BOTH**："
            "P1 2023-04 社零 +18.4%、5 月 +12.7%；P2 同期服务消费标的**已在回落**；"
            "P3 权威媒体确认复苏不及预期（E029/E030 `contradicting`）→ "
            "本包**所有宏观数据（社零/CPI/旅游人次）证据角色均为 `context`**，不作启动或加速证据。"
        ),
    ),
    dict(
        k="005", cid="C-2018-CONS-HOG-AFRICAN", year=2018,
        start="2018-08-03", peak="2020-03-09", end="2021-12-31",
        cls="industry_trend", strength="strong", result="positive", dc="medium",
        cycle="hog_cycle_2018_2022",
        themes=[("TH-CONSUMER", "related"), ("TH-CONSUMER-AGRI", "main")],
        notes=(
            "★ CF006 裁决（含 Q001「自然周期是否允许进入 Campaign Universe」）：**判为独立 Campaign，并允许进入**。"
            "判据**不基于「猪周期」这一名称**，而基于现有 Independence Gate 五要素与 Q1–Q5："
            "① 主题明确（非洲猪瘟外生供给冲击）；② 持续性成立（2018-08 至 2021-12）；"
            "③ **市场关注有 A 股侧证据**（E038 牧原股份 2020-03-09 盘中历史最高 139.92 元；"
            "温氏股份 2019-03-13 盘中 45.55 元）；④ start/end 可解释；⑤ ≥2 独立证据（7 ev / 6 IG）。"
            "★ **关于 Q001 的判据立场**：现有 Independence Gate 是**结构独立性**判据，**不排除自然周期**；"
            "且 R01-01 的 `C-2018-HIEQ-ROBOT-DOWN`（下行周期）与 R01-03 的 `C-2022-SEMI-DOWNTURN`（下行周期）"
            "已确立「非主题叙事型结构亦可进入 canonical」的先例。本 Campaign 具备"
            "「**可观测先行指标（能繁母猪存栏，传导约 10 个月）+ 官方逆周期调控框架 + A 股提前定价**」三要素。"
            "**但须明确**：其机制性质为「**供给端自然周期**」，与「政策/技术/叙事驱动」型 Campaign 不同 —— "
            "已在 `classification = industry_trend` 与本注记中显式区分。"
            "★ 链条：E033（2018-08-03 首例非洲猪瘟）→ E093（22 省市猪肉均价 16→56 元/千克、+250%）"
            "→ E034（2019 年第 40 周官方周度收购价 29.96 元/公斤）→ E035（猪肉 +42.5%，拉动 CPI 约 62.4%）"
            "→ E036（2019-10 能繁母猪环比 +0.6%，2018-04 以来首次回升）→ E037（2021-10 官方周度 13.40 元/公斤、-57.7%）。"
            "★ 与 006 同属 Theme Cycle `hog_cycle_2018_2022`（Pattern = **Sequential**）。"
        ),
    ),
    dict(
        k="006", cid="C-2021-CONS-HOG-REVERSAL", year=2021,
        start="2021-08-17", peak="2022-10-15", end="2022-12-31",
        cls="industry_trend", strength="medium", result="positive", dc="medium",
        cycle="hog_cycle_2018_2022",
        themes=[("TH-CONSUMER", "related"), ("TH-CONSUMER-AGRI", "main")],
        notes=(
            "★ CF006 裁决：**与 005 为同一 Theme Cycle 下的 Sequential Campaign**（两轮拆为两个独立 Campaign）。"
            "Gate：Q1 注意力中心 =「能繁母猪去化 + 官方逆周期调控」（与 005 的疫病外生冲击不同）；"
            "**Q4 独立生命周期成立** —— 存在**独立产能拐点**（E039：2021-07 能繁母猪环比 -0.5%，"
            "**结束连续 21 个月增长**）与**独立政策框架事件**（E040：2021-09-19《生猪产能调控实施方案（暂行）》，"
            "明确正常保有量约 4100 万头；E041：2022-02-28 中央冻猪肉收储 4 万吨；E043：2022-09-08 开始投放储备）；"
            "Q5 双向成立。★ Q2 代表标的部分重叠（牧原股份）→ 由 Sequential 解释；"
            "006 另有 005 未出现的弹性标的（巨星农牧、傲农生物，E046）。"
            "★ **PIT 证据 = 6（本包最高）** —— 官方周度价格与政策文件均为同期口径。"
            "★ 价格高点（E044，2022-10 中旬约 28 元/公斤，**媒体转述**）与结束段（E045，"
            "「**行业信息站复盘称**」，来源 `S074` 猪易网 tier 3）**均为非官方口径，已明确标记**；"
            "官方周度监测对应期数未逐期补齐（`known_gaps[6]`）→ `date_confidence = medium`。"
        ),
    ),
    dict(
        k="008", cid="C-2020-CONS-WHITE-GOODS", year=2020,
        start="2020-06-01", peak="2021-02-18", end="2021-12-31",
        cls="industry_trend", strength="medium", result="positive", dc="medium",
        cycle="appliance_export_2020_2021",
        themes=[("TH-CONSUMER", "related"), ("TH-CONSUMER-APPLIANCE", "main")],
        notes=(
            "★ CF005 裁决（驱动归因）：**保留 UNRESOLVED —— 不强行选一个**。"
            "P1 地产后周期（传统解释）；P2 **出口替代**（数据更支持：2020 年家电出口 4582 亿元、+24.2%，"
            "而内销 7297 亿元、-9.2%，E047/E048）；P3 **反证地产传导的时间关系**"
            "（2020 年房屋竣工 -4.9% 而板块上行；2021 年竣工 +11.2% 而板块已下行 —— E051/E052 `contradicting`）。"
            "★ **命名确定性已下调**：本 Campaign **不使用「地产后周期」这一命名**，改用中性 ID `C-2020-CONS-WHITE-GOODS`"
            "（白电），并在本注记中完整保留两侧证据与 P3 反证。**未强行选定单一驱动。**"
            "★ **peak = 2021-02-18**（海尔智家盘中最高 35.95 元；美的集团 2021-02-10 盘中 108.00 元；"
            "格力电器 2021-01-06，E054）—— 采用 A 股个股高点口径。"
            "★ **CF008 裁决（小家电 vs 白电）**：本 Campaign 与 `RC-2020-CONS-SMALL-APPLIANCE`（007）"
            "**代表标的完全不重叠**（科沃斯/石头科技/小熊电器 vs 美的/格力/海尔/老板电器）、"
            "**见顶时间错位 5 个月至 1 年**（2020-07 / 2021-06–07 vs 2021-01–02）→ **支持独立结构**；"
            "但 007 因证据薄（4 ev / 3 IG）与 **PIT = 0** 本轮**未进入 canonical**，保持待补证。"
            "★ **共享 evidence 处理**：`E047`/`E048`/`E049`（家电行业整体口径）原为 007 与 008 共享；"
            "因 007 未进入 canonical，按 **1 evidence : 1 campaign** 规则**全部归属本 Campaign** ✓ "
            "（**未为了处理共享证据而强行合并两个候选**）。"
            "★ **PIT = 0**：本 Campaign 全部证据为 subsequent / retrospective 口径（无同期证据）→ "
            "`strength = medium`；**不得声称已完成同期市场响应验证**。"
        ),
    ),
    dict(
        k="009", cid="C-2019-CONS-AESTHETICS", year=2019,
        start="2019-11-06", peak="2021-07-05", end="2022-12-31",
        cls="theme_campaign", strength="medium", result="positive", dc="medium",
        cycle="beauty_aesthetics_2019_2022",
        themes=[("TH-CONSUMER", "main")],
        notes=(
            "★ CF007 裁决（Macro Theme 归属）：**按 CMTR v1 解析结果归 `消费` 根**"
            "（`R01-CONSUMER-MT006` 以 `kind = CROSS_FAMILY` 提交，CMTR 返回 `UNRESOLVED_NAME` —— "
            "**这是协议期望的正确结果**，跨族问题不由 CMTR 裁决）。"
            "★ **边界 Conflict 保留**：「医美属消费 vs 医药健康」未裁决 —— "
            "P1 属消费（自费/可选/受收入与消费意愿驱动，与白酒/美妆同属「悦己消费」叙事）；"
            "P2 属医药健康（医美耗材按**医疗器械**监管、服务机构受**卫健委**监管，产业链与医疗器械重叠）。"
            "**未自行新增 Macro Theme、未扩展 taxonomy**（符合协议）。"
            "★ CF009 裁决（医美 vs 国货美妆）：**判为两个独立 Campaign，同属 Theme Cycle `beauty_aesthetics_2019_2022`"
            "（Pattern = Parallel）**。Gate：Q1 产业环节不同（医疗耗材/服务 vs 化妆品零售）；"
            "**Q2 代表标的不重叠**（爱美客/华熙生物/朗姿股份 vs 珀莱雅/贝泰妮）；"
            "Q4 生命周期独立（peak 2021-07-05 vs 010 的 2021-10-29）。"
            "★ **P3 医美监管的双重性质已分别归入 drivers**：八部门打击非法医美（E064）"
            "既清退非法供给（accelerator）又压制扩张预期（turning）—— **未单向归类**。"
            "★ 渗透率机制**无权威统一口径**（E067 为「券商研究经媒体转述」3.6%）→ "
            "**未把估算值当作官方统计**；`strength = medium`。"
        ),
    ),
    dict(
        k="010", cid="C-2020-CONS-BEAUTY-CN", year=2020,
        start="2020-06-29", peak="2021-10-29", end="2022-12-31",
        cls="industry_trend", strength="medium", result="positive", dc="medium",
        cycle="beauty_aesthetics_2019_2022",
        themes=[("TH-CONSUMER", "main")],
        notes=(
            "★ CF009 裁决：**与 009 为同一 Theme Cycle 下的 Parallel Campaign**（非合并）。"
            "机制 =「**国货替代 + 线上渠道红利 + 监管规范化**」，与 009 的「渗透率 + 产品创新 + 合规化」不同；"
            "验证数据亦不同（本 Campaign 有**国家统计局化妆品零售额**：2021 年 4026 亿元、+14.0%；"
            "2022 年 3936 亿元、-4.5% 为十年首次负增长，E070）。"
            "★ 监管链条：E068（2020-06-29《化妆品监督管理条例》）→ E069（2021-04-08《化妆品功效宣称评价规范》）"
            "→ E071（2021-03-25 贝泰妮创业板上市）→ E072（2021-10-29 珀莱雅盘中最高 224.43 元，历史最高；"
            "贝泰妮 2021-07-08 盘中最高 289.35 元）→ E070（2022 零售额转负）。"
            "★ **peak = 2021-10-29**（珀莱雅历史最高，A 股个股口径）。"
            "★ **已知弱点**：① 渠道红利这一核心机制仅有事后转述证据；② A 股可交易标的仅 2 个"
            "（珀莱雅/贝泰妮），**板块广度有限**，且珀莱雅滞后见顶使「板块峰值」难以定义；"
            "③ 2019 年化妆品零售额未取得官方直链 → `strength = medium`、`date_confidence = medium`。"
            "★ **Macro Theme 归属**：`美容护理` 未被 T01 的 `消费` 根覆盖（`MT006` 未解析）→ "
            "本 Campaign 以 **root `TH-CONSUMER` 为 main 主题**（无子主题），与 R01-02 的 `C-2019-CONSUMER-TWS` 同口径。"
        ),
    ),
    dict(
        k="011", cid="C-2024-CONS-TRADE-IN", year=2024,
        start="2024-03-13", peak="2024-10-08", end="2025-12-31",
        cls="mixed", strength="medium", result="positive", dc="medium",
        cycle="trade_in_2024_2025",
        themes=[("TH-CONSUMER", "related"), ("TH-CONSUMER-APPLIANCE", "main")],
        notes=(
            "★ 独立生命周期裁决：**构成独立 Campaign** —— 政策定调**不**被当作完整启动。"
            "完整链条（**五级验证**）：① 政策定调 E055（2024-03-13 国发〔2024〕7 号公开）→ "
            "② 资金落地 E056（2024-07-25 发改环资〔2024〕1104 号，约 1500 亿元超长期特别国债）→ "
            "③ 补贴细则 E057（2024-08-24 商务部等 4 部门，8 类家电补 15%/20%）→ "
            "④ **官方销量/零售验证** E058（2024-09~12 零售额同比 +20.5%/+39.2%/+22.2%/+39.3%，连续 4 个月双位数）"
            "+ E059（全年 10307 亿元、+12.3% 创历史新高）+ E060（商务部口径 3600 万消费者、超 6000 万台、超 2600 亿元）"
            "→ ⑤ **A 股响应** E061（2024-10-08 美的/格力/海尔/海信家电/华帝/老板电器**同时**出现区间最高价）"
            "→ 降温 E062（2025 年奥维云网推总口径 8931 亿元、-4.3%，Q3 起明显回落）。"
            "**start 取 2024-03-13（政策定调），peak 取 2024-10-08（A 股区间高点）** —— "
            "**未把政策出台日期当成完整 Campaign 启动**。"
            "★ CF010（补贴驱动 vs 真实需求）**保留 UNRESOLVED**：P1 需求前置（2025 推总口径 -4.3%）；"
            "P2 存在真实成分（全年零售额创历史新高、1 级能效占比高）；**P3 口径冲突完整保留** —— "
            "**2025 年家电零售增速：国家统计局口径 +11% vs 奥维云网推总口径 -4.3%，方向相反**"
            "（`CF010.positions[2]`，来源 `S076`）—— **本注记不选任何一个作为唯一事实**。"
            "Worker 按「一个 Campaign、双驱动叠加」提交，理由：两者**时间完全重叠、代表标的相同**，拆分将违反 Q5。"
            "★ **Beta 风险**：峰值日 2024-10-08 与全市场「9·24 行情」重合 → **存在 Beta Contamination，"
            "无法排除** → `strength = medium`（而非 strong），峰值置信度仅 medium；"
            "**不得把涨幅单独归因于补贴逻辑，不得声称完成 Beta 中性验证**。"
            "★ **反面对照**：2025 年消费政策密集但**无 Campaign**（`exclusion X001` / `CF012`）："
            "社零 +3.7%、中证白酒 -16.2%、中证食品饮料 -12.0%，年内高点恰在政策公开前后 —— "
            "**政策发布 ≠ 主题形成**。"
        ),
    ),
    dict(
        k="012", cid="C-2023-CONS-VALUE-RETAIL", year=2023,
        start="2023-01-01", peak="2025-08-29", end=None,
        cls="industry_trend", strength="medium", result="positive", dc="low",
        cycle="value_retail_2023_2025",
        themes=[("TH-CONSUMER", "main")],
        notes=(
            "★ 启动精度裁决：**start 采用包内 DATE_WINDOW 左沿 2023-01-01，`date_confidence = low`** —— "
            "**不虚构更精确的日期**。已知缺口：门店总数**缺乏官方统计口径**，启动窗口只能定为**年度级**"
            "（`known_gaps[8]`）；首个有确切日期的证据为 E075（2024-06-12 零食很忙集团门店总数突破 10000 家）。"
            "★ **`end_date = NULL`** —— **结束尚未确立**：渠道龙头万辰集团 2025-08-29 收 210.81 元（区间最高），"
            "lifecycle 末段为 `UNKNOWN`（`Q011`）。"
            "★ 机制 =「**渠道效率变革 + 性价比消费**」，与收入驱动的消费升级**方向相反**，"
            "为当前 Historical Universe **完全缺失**的机制样本。"
            "★ 链条：E075（2024-06-12 门店破万）→ E076（万辰并表门店 4726→14196 家）→ "
            "E077（万辰 2024 营收 323.29 亿元、+247.86%）→ E078（盐津铺子营收 +28.89%）→ "
            "E079（万辰 2024-12-11 收 80.21 元 → 2025-08-29 收 210.81 元，区间最高）。"
            "★ **已知弱点**：① A 股可交易标的仅 2 个（万辰集团/盐津铺子），**板块广度有限**；"
            "② 三只松鼠、良品铺子等品牌商走势与渠道龙头分化 → 「量贩零食」作为单一叙事的完整性存疑；"
            "③ 港股/一级市场同类业态不在本任务范围 → `strength = medium`。"
            "★ **Macro Theme 归属**：`商贸零售` 未被 T01 的 `消费` 根覆盖"
            "（`MT007` 以 `NEW_MACRO_CANDIDATE` 提交但 CMTR 返回 `UNRESOLVED_NAME`）→ "
            "本 Campaign 以 **root `TH-CONSUMER` 为 main 主题**（无子主题）。"
            "**未扩展 taxonomy**；该提案级 gap 已记录，待后续 taxonomy 轮次处理。"
        ),
    ),
]

RESEARCH_ONLY = [
    dict(
        k="007", cid="RC-2020-CONS-SMALL-APPLIANCE", year=2020,
        start="2020-02-01", peak="2021-07-15", end="2021-12-31",
        cls="industry_trend", cycle="small_appliance_2020_2021",
        themes=[("TH-CONSUMER", "related"), ("TH-CONSUMER-APPLIANCE", "main")],
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）—— **补证后再评估**。理由："
            "① **证据薄**：仅 4 evidence / 3 independence_group（本包最少之一）；"
            "② **PIT 证据 = 0** —— 4 条证据全部为 subsequent / retrospective，**无任何同期证据**；"
            "③ **渗透率提升这一核心机制缺一手量化数据**（`known_gaps[3]`）。"
            "★ **CF008 裁决**：本候选与 `C-2020-CONS-WHITE-GOODS`（008）**代表标的完全不重叠**"
            "（科沃斯/石头科技/小熊电器 vs 美的/格力/海尔/老板电器）、**见顶时间错位 5 个月至 1 年**"
            "（2020-07 / 2021-06–07 vs 2021-01–02）→ **支持独立结构**；"
            "但因上述证据缺口**本轮未进入 canonical**。**未因共享证据而强行与白电合并**。"
            "★ 共享 evidence `E047`/`E048`/`E049`（家电行业整体口径）因本候选未进入 canonical，"
            "已按 **1 evidence : 1 campaign** 规则归属 008 ✓。"
            "→ 建议补「清洁电器/小家电渗透率一手数据」与「同期（2020–2021）证据」后重新评估。"
        ),
    ),
    dict(
        k="013", cid="RC-2024-CONS-PET-FOOD", year=2024,
        start="2024-10-01", peak="2025-06-30", end=None,
        cls="industry_trend", cycle="pet_food_2024_2025",
        themes=[("TH-CONSUMER", "related"), ("TH-CONSUMER-AGRI", "main")],
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）—— **保持 INSUFFICIENT / low**。理由："
            "① 仅 **3 evidence / 3 independence_group**；② **PIT 证据 = 0**；"
            "③ **无任何一手官方证据** —— 行业规模与出口数据**均为媒体转述**"
            "（E080 城镇犬猫消费市场规模；E081「**媒体转述海关数据称**」宠物食品出口 105.29 亿元、+22.07%）；"
            "④ 无明确的启动事件锚点（start 只能以 PHASE_WINDOW 表达）；"
            "⑤ A 股可交易标的仅 2–3 只，**板块广度严重不足**；⑥ 持续仅约 2–3 个季度，**接近 OBSERVATION_ONLY 边界**。"
            "★ 机制独特性（**情感消费 / 它经济**，既不依赖收入周期也不依赖政策刺激）**保留记录**，"
            "但**不得为了机制独特性而提升为 Campaign**。"
            "→ 建议补「海关总署出口原文」与「行业规模官方口径」后重新评估。"
        ),
    ),
]

ANNUAL = {
    2018: ("medium", "非洲猪瘟驱动的超级猪周期启幕（供给端外生冲击）。"),
    2016: ("medium", "白酒/消费升级与白马蓝筹行情启幕；**Priority B 段，月度批价/动销一手数据缺失。**"),
    2019: ("strong", "白酒核心资产主升（MSCI 扩容 + 外资增量）与医美/颜值经济并行。"),
    2020: ("strong", "离岛免税额度放开、白电出口共振、国货美妆三条结构并行。"),
    2021: ("medium", "猪周期反转（能繁母猪去化 + 官方逆周期调控）。"),
    2022: ("medium", "疫后服务消费修复脉冲与「弱复苏」证伪；**主升仅 1–2 个月。**"),
    2023: ("medium", "量贩零食/折扣零售（渠道效率变革 + 性价比消费）；**start 为年度级、end 未确立。**"),
    2024: ("medium", "消费品以旧换新（财政补贴 → 官方销量 → A 股响应）；**Beta 风险未排除。**"),
}

SEC_CANON = {
    "R01-CONSUMER-SEC001": ("MOUTAI", "600519", "贵州茅台", "SH"),
    "R01-CONSUMER-SEC002": ("WULIANGYE", "000858", "五粮液", "SZ"),
    "R01-CONSUMER-SEC003": ("LUZHOULAOJIAO", "000568", "泸州老窖", "SZ"),
    "R01-CONSUMER-SEC004": ("FENJIU", "600809", "山西汾酒", "SH"),
    "R01-CONSUMER-SEC005": ("HAITIAN", "603288", "海天味业", "SH"),
    "R01-CONSUMER-SEC006": ("YILI", "600887", "伊利股份", "SH"),
    "R01-CONSUMER-SEC007": ("CTGDF", "601888", "中国中免", "SH"),
    "R01-CONSUMER-SEC008": ("JINJIANG", "600754", "锦江酒店", "SH"),
    "R01-CONSUMER-SEC009": ("BTG", "600258", "首旅酒店", "SH"),
    "R01-CONSUMER-SEC010": ("SONGCHENG", "300144", "宋城演艺", "SZ"),
    "R01-CONSUMER-SEC011": ("MUYUAN", "002714", "牧原股份", "SZ"),
    "R01-CONSUMER-SEC012": ("WENS", "300498", "温氏股份", "SZ"),
    "R01-CONSUMER-SEC013": ("NEWHOPE", "000876", "新希望", "SZ"),
    "R01-CONSUMER-SEC014": ("JUXING", "603477", "巨星农牧", "SH"),
    "R01-CONSUMER-SEC015": ("AONONG", "603363", "傲农生物", "SH"),
    "R01-CONSUMER-SEC016": ("MIDEA", "000333", "美的集团", "SZ"),
    "R01-CONSUMER-SEC017": ("GREE", "000651", "格力电器", "SZ"),
    "R01-CONSUMER-SEC018": ("HAIER", "600690", "海尔智家", "SH"),
    "R01-CONSUMER-SEC019": ("ROBAM", "002508", "老板电器", "SZ"),
    "R01-CONSUMER-SEC020": ("AIMEIKE", "300896", "爱美客", "SZ"),
    "R01-CONSUMER-SEC021": ("BLOOMAGE", "688363", "华熙生物", "SH"),
    "R01-CONSUMER-SEC022": ("LANCY", "002612", "朗姿股份", "SZ"),
    "R01-CONSUMER-SEC023": ("PROYA", "603605", "珀莱雅", "SH"),
    "R01-CONSUMER-SEC024": ("BETTENI", "300957", "贝泰妮", "SZ"),
    "R01-CONSUMER-SEC025": ("WANCHEN", "300972", "万辰集团", "SZ"),
    "R01-CONSUMER-SEC026": ("YANJIN", "002847", "盐津铺子", "SZ"),
    "R01-CONSUMER-SEC027": ("GAMBO", "301498", "乖宝宠物", "SZ"),
    "R01-CONSUMER-SEC028": ("CHINAPET", "002891", "中宠股份", "SZ"),
    "R01-CONSUMER-SEC029": ("ECOVACS", "603486", "科沃斯", "SH"),
    "R01-CONSUMER-SEC030": ("ROBOROCK", "688169", "石头科技", "SH"),
    "R01-CONSUMER-SEC031": ("BEAR", "002959", "小熊电器", "SZ"),
}

EVENTS = [
    ("EV-CONS-01", "2017-06-21", "MSCI 宣布自 2018 年 6 月起将中国 A 股纳入 MSCI 新兴市场指数", "policy", "R01-CONSUMER-E003"),
    ("EV-CONS-02", "2018-10-29", "贵州茅台出现上市以来首个「一」字跌停（Q3 收入 +3.8%、利润 +2.7% 低于预期）", "market", "R01-CONSUMER-E005"),
    ("EV-CONS-03", "2019-03-01", "MSCI 宣布将中国 A 股纳入因子由 5% 提高至 20%（5/8/11 月三步实施）", "policy", "R01-CONSUMER-E009"),
    ("EV-CONS-04", "2021-02-18", "中证白酒指数（399997）盘中最高 21663.85 点；贵州茅台盘中最高 2627.88 元", "market", "R01-CONSUMER-E012"),
    ("EV-CONS-05", "2020-06-29", "财政部等三部门公告 2020 年第 33 号：离岛免税额度由 3 万元提高至 10 万元/年、不限次数", "policy", "R01-CONSUMER-E016"),
    ("EV-CONS-06", "2021-12-31", "2021 年海南 10 家离岛免税店总销售额 601.73 亿元、同比增长 84%", "industry", "R01-CONSUMER-E019"),
    ("EV-CONS-07", "2022-12-07", "国务院联防联控机制综合组印发《关于进一步优化落实新冠肺炎疫情防控措施的通知》（新十条）", "policy", "R01-CONSUMER-E026"),
    ("EV-CONS-08", "2023-01-27", "2023 年春节假期全国国内旅游出游 3.08 亿人次、同比增长 23.1%（恢复至 2019 年同期 88.6%）", "industry", "R01-CONSUMER-E027"),
    ("EV-CONS-09", "2018-08-03", "农业农村部确认辽宁省沈阳市沈北新区发生我国首例非洲猪瘟疫情", "industry", "R01-CONSUMER-E033"),
    ("EV-CONS-10", "2020-03-09", "牧原股份盘中触及历史最高价 139.92 元（不复权）", "market", "R01-CONSUMER-E038"),
    ("EV-CONS-11", "2021-08-17", "农业农村部公布 7 月全国能繁母猪存栏环比下降 0.5%，结束连续 21 个月增长", "industry", "R01-CONSUMER-E039"),
    ("EV-CONS-12", "2022-02-28", "国家发展改革委启动中央冻猪肉储备收储工作，首批收储 4 万吨", "policy", "R01-CONSUMER-E041"),
    ("EV-CONS-13", "2021-02-18", "白电龙头区间高点：海尔智家盘中最高 35.95 元、美的集团 2021-02-10 盘中 108.00 元", "market", "R01-CONSUMER-E054"),
    ("EV-CONS-14", "2021-07-05", "爱美客/华熙生物盘中历史最高价（爱美客 2021-02-18 1331.02 元；华熙生物 314.99 元）", "market", "R01-CONSUMER-E066"),
    ("EV-CONS-15", "2021-04-08", "国家药品监督管理局发布《化妆品功效宣称评价规范》（2021 年第 50 号）", "policy", "R01-CONSUMER-E069"),
    ("EV-CONS-16", "2024-08-24", "商务部等 4 部门发布《关于进一步做好家电以旧换新工作的通知》（8 类家电补 15%/20%）", "policy", "R01-CONSUMER-E057"),
    ("EV-CONS-17", "2024-10-08", "美的/格力/海尔/海信家电/华帝/老板电器同时出现区间最高价", "market", "R01-CONSUMER-E061"),
    ("EV-CONS-18", "2025-08-29", "万辰集团收于 210.81 元（区间最高）；同期三只松鼠 2025 年初见顶后全年收跌", "market", "R01-CONSUMER-E079"),
]

CAMPAIGN_EVENTS = [
    ("C-2016-CONS-BAIJIU-UPGRADE", "EV-CONS-01", "catalyst"),
    ("C-2016-CONS-BAIJIU-UPGRADE", "EV-CONS-02", "follow_up"),
    ("C-2019-CONS-BAIJIU-CORE", "EV-CONS-03", "trigger"),
    ("C-2019-CONS-BAIJIU-CORE", "EV-CONS-04", "follow_up"),
    ("C-2020-CONS-DUTYFREE", "EV-CONS-05", "trigger"),
    ("C-2020-CONS-DUTYFREE", "EV-CONS-06", "follow_up"),
    ("C-2022-CONS-SERVICE-REBOUND", "EV-CONS-07", "trigger"),
    ("C-2022-CONS-SERVICE-REBOUND", "EV-CONS-08", "catalyst"),
    ("C-2018-CONS-HOG-AFRICAN", "EV-CONS-09", "trigger"),
    ("C-2018-CONS-HOG-AFRICAN", "EV-CONS-10", "follow_up"),
    ("C-2021-CONS-HOG-REVERSAL", "EV-CONS-11", "trigger"),
    ("C-2021-CONS-HOG-REVERSAL", "EV-CONS-12", "catalyst"),
    ("C-2020-CONS-WHITE-GOODS", "EV-CONS-13", "follow_up"),
    ("C-2019-CONS-AESTHETICS", "EV-CONS-14", "follow_up"),
    ("C-2020-CONS-BEAUTY-CN", "EV-CONS-15", "trigger"),
    ("C-2024-CONS-TRADE-IN", "EV-CONS-16", "trigger"),
    ("C-2024-CONS-TRADE-IN", "EV-CONS-17", "follow_up"),
    ("C-2023-CONS-VALUE-RETAIL", "EV-CONS-18", "follow_up"),
]

# 共享 evidence 唯一归属：E047/E048/E049 原为 007 与 008 共享；
# 007 未进入 canonical → 全部归属 008（按 1 evidence : 1 campaign 规则）
EVIDENCE_OWNER = {
    "R01-CONSUMER-E047": "008",
    "R01-CONSUMER-E048": "008",
    "R01-CONSUMER-E049": "008",
}


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

    existing_sec = {r[0]: r[1] for r in cur.execute("SELECT security_id, name FROM securities")}
    reuse_sec = set()
    for _iid, (sid, _t, nm, _e) in SEC_CANON.items():
        if sid in existing_sec:
            if existing_sec[sid] != nm:
                raise SystemExit("FAIL 证券助记符冲突（名称不一致）: %s 既有=%s 新=%s" % (sid, existing_sec[sid], nm))
            reuse_sec.add(sid)
    if reuse_sec:
        print("  复用既有证券: %s" % sorted(reuse_sec))

    if not have("research_rules", "rule_id", RULE_ID):
        add("research_rules", RULE_ID,
            "INSERT INTO research_rules (rule_id,name,base_pattern,description,status) VALUES (?,?,?,?,?)",
            (RULE_ID, "消费历史周期观察", "消费", "R01-04（消费）历史周期观察窗口。" + PROV, "under_review"))

    for yr in sorted(ANNUAL):
        arid = "AR-CONS-%d" % yr
        if not have("annual_reviews", "annual_review_id", arid):
            st, summary = ANNUAL[yr]
            add("annual_reviews", arid,
                "INSERT INTO annual_reviews (annual_review_id,rule_id,year,status,summary,review_notes) VALUES (?,?,?,?,?,?)",
                (arid, RULE_ID, yr, st, summary, PROV))

    for c in CAMPAIGNS:
        if not have("campaigns", "campaign_id", c["cid"]):
            add("campaigns", c["cid"],
                "INSERT INTO campaigns (campaign_id,annual_review_id,rule_id,season_id,campaign_year,start_date,end_date,peak_date,"
                "strength,result,classification,start_date_basis,end_date_basis,"
                "date_confidence,description,research_notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (c["cid"], "AR-CONS-%d" % c["year"], RULE_ID, c["cycle"], c["year"], c["start"], c["end"], c["peak"],
                 c["strength"], c["result"], c["cls"],
                 "研究候选日期（intake date_candidates）；未经行情核验",
                 "研究候选日期（intake date_candidates）；未经行情核验",
                 c["dc"],
                 "%s［intake R01-CONSUMER-%s］" % (cand_by_k[c["k"]]["title"], c["k"]),
                 c["notes"] + "｜theme_cycle_id=%s｜provenance: %s" % (c["cycle"], PROV)))

    for c in CAMPAIGNS:
        for tid, role in c["themes"]:
            if not cur.execute("SELECT 1 FROM campaign_themes WHERE campaign_id=? AND theme_id=?",
                               (c["cid"], tid)).fetchone():
                add("campaign_themes", "%s/%s" % (c["cid"], tid),
                    "INSERT INTO campaign_themes (campaign_id,theme_id,role) VALUES (?,?,?)", (c["cid"], tid, role))

    for _iid, (sid, ticker, name, exch) in SEC_CANON.items():
        if sid in reuse_sec:
            continue
        if not have("securities", "security_id", sid):
            add("securities", sid,
                "INSERT INTO securities (security_id,ticker,name,exchange) VALUES (?,?,?,?)", (sid, ticker, name, exch))

    src_map = {}
    for i, s in enumerate(pkg["sources"], start=1):
        sid = "S-CONS-%02d" % i
        src_map[s["source_id"]] = sid
        if not have("sources", "source_id", sid):
            add("sources", sid,
                "INSERT INTO sources (source_id,source_type,title,author,url,published_at,captured_at,publisher,description,tier)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (sid, s["source_type"], s["title"], s.get("author"), s.get("url"), s.get("published_at"), None,
                 s["publisher"], "%s［intake %s］" % (s.get("description") or "", s["source_id"]), s["tier"]))

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
        eid = "E-CONS-%02d" % i
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

    ev_src = {e["evidence_id"]: e["source_id"] for e in pkg["evidence"]}
    for eid, date, name, etype, intake_ev in EVENTS:
        if intake_ev in RC_ONLY_EV:
            continue
        if not have("events", "event_id", eid):
            add("events", eid,
                "INSERT INTO events (event_id,date,name,event_type,description,source_id) VALUES (?,?,?,?,?,?)",
                (eid, date, name, etype, "%s｜provenance: %s" % (intake_ev, PROV), src_map[ev_src[intake_ev]]))

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

    rc_event_ids = {eid for eid, _d, _n, _t, ie in EVENTS if ie in RC_ONLY_EV}
    for cid, eid, role in CAMPAIGN_EVENTS:
        if eid in rc_event_ids:
            continue
        if not cur.execute("SELECT 1 FROM campaign_events WHERE campaign_id=? AND event_id=?", (cid, eid)).fetchone():
            add("campaign_events", "%s/%s" % (cid, eid),
                "INSERT INTO campaign_events (campaign_id,event_id,role) VALUES (?,?,?)", (cid, eid, role))

    for c in CAMPAIGNS:
        for intake_sec in cand_by_k[c["k"]]["security_ids"]:
            sid = SEC_CANON[intake_sec][0]
            if not cur.execute("SELECT 1 FROM campaign_securities WHERE campaign_id=? AND security_id=?",
                               (c["cid"], sid)).fetchone():
                add("campaign_securities", "%s/%s" % (c["cid"], sid),
                    "INSERT INTO campaign_securities (campaign_id,security_id,role) VALUES (?,?,?)",
                    (c["cid"], sid, "representative"))

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
            pid = "PH-CONS-%02d" % ph_n
            if not have("campaign_phases", "phase_id", pid):
                add("campaign_phases", pid,
                    "INSERT INTO campaign_phases (phase_id,campaign_id,phase_type,start_date,end_date,description)"
                    " VALUES (?,?,?,?,?,?)",
                    (pid, c["cid"], STAGE[stage], l["start"], end, "%s（intake lifecycle）｜%s" % (stage, PROV)))

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
                     "candidate 快照自 R01-04 intake date_candidates；未经行情核验。｜%s" % PROV))

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
