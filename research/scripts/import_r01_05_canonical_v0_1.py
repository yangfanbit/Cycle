#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""import_r01_05_canonical_v0_1.py —— R01-05（金融 / 房地产）Canonical Import。

依据：`docs/R01_05_INTAKE_REVIEW_v0_1.md` + `docs/R01_05_INTAKE_REVIEW_ADDENDUM_v0_1.md`
     + 本轮 Canonical Decision（Independence Gate Q1–Q5）。

结果（**7 PROMOTE + 5 RESEARCH_ONLY**）：
  PROMOTE → campaigns 表
    001 三支箭地产              → C-2022-RE-POLICY-THREE
    004 地产债务风险暴露（下行）→ C-2020-RE-DEBT-RISK
    005 2024-09 券商/非银       → C-2024-FIN-BROKER-POLICY
    006 2023 中特估金融         → C-2023-FIN-SOE-VALUATION
    007 2023–2025 银行高股息    → C-2024-FIN-BANK-DIVIDEND
    008 2020–2021 银行顺周期    → C-2020-FIN-BANK-CREDIT
    010 2025 保险               → C-2025-FIN-INSURANCE
  RESEARCH_ONLY → **不入 campaigns 表**（仅导出层 research_candidates）
    002 5·17 地产（市场层强反向证伪）→ RC-2024-RE-POLICY-517
    003 2018–2019 地产（INSUFFICIENT + 市场层证伪）→ RC-2019-RE-EASING
    009 2020-07 券商（CONFLICT + **无 lifecycle**）→ RC-2020-FIN-BROKER-VOLUME
    011 棚改去库存（Priority B 市场层空白）→ RC-2016-RE-SHANTY
    012 2015 杠杆牛金融股（Beta 主导）→ RC-2015-FIN-LEVERAGE

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
PKG = os.path.join(ROOT, "research", "intake", "packages", "R01-05")

RULE_ID = "rule_fin_realestate"
PROV = "R01-05 Intake Package（v2，source_commit 2153f6d）｜Canonical Decision docs/R01_05_INTAKE_REVIEW_v0_1.md + ADDENDUM_v0_1.md"

# ★ CF013 口径差统一 caveat（写入所有引用沪深300 相对基准的 Campaign）
CF013 = (
    "★ **CF013 口径差（UNRESOLVED）—— 结论约束，非数据修正**：本 Campaign 引用的相对收益为"
    "「**个股前复权（含股息再投）vs 沪深300 价格指数（不含股息）**」口径。按银行股息率约 5%/年估算，"
    "3 年窗口的口径差约 **+15pct**，银行类候选的超额被**系统性高估**。"
    "**因此不得把该相对收益直接解释为行业 Alpha**；**未做 Beta 调整、未剥离风格因子**，"
    "**Beta 中性验证未完成**。原始 Evidence（E130–E141）与原始区间收益**保持不变**，"
    "**未伪造任何调整后收益**；如需分离股息贡献，须以中证红利全收益指数 / 银行行业指数（全收益）重算（Q013）。"
)

CAMPAIGNS = [
    dict(
        k="001", cid="C-2022-RE-POLICY-THREE", year=2022,
        start="2022-11-08", peak="2022-11-29", end="2023-02-28",
        cls="event_driven", strength="medium", result="positive", dc="medium",
        cycle="realestate_policy_cycle_2020_2023",
        themes=[("TH-REALESTATE", "related"), ("TH-REALESTATE-DEV", "main")],
        notes=(
            "★ CF001 裁决：**判为独立 Campaign**（非「地产下行大周期中的一次政策反弹」）。"
            "Gate：Q1 独立注意力中心 =「房企融资供给端政策转向（信贷/债券/股权三支箭）+ 保交楼风险出清预期」，"
            "与 004 的「融资收紧 → 信用风险暴露」**方向相反**；Q3 持续性成立（2022-11 至 2023-02）；"
            "**Q4 独立生命周期成立**（政策脉冲：MAIN_RISE 2022-11-08→11-29 → PEAK → 2023Q1 降温，"
            "与 004 的 2020-08→2022-07 下行段**不重叠**）；Q5 Residual Test 双向成立；"
            "**独立启动锚点**（2022-11-08 交易商协会「第二支箭」公告，一手）与 004 的 2020-08-20 座谈会不同。"
            "★ **Q2 代表标的不成立**（与 004 完全重叠：保利/万科/招商蛇口/金地）—— 由"
            "「**同一批资产在两轮方向相反的政策周期中重演**」解释，二者同属 Theme Cycle "
            "`realestate_policy_cycle_2020_2023`（Pattern = **Sequential**：004 下行 → 001 政策修复）。"
            "★ **CF011 保留 UNRESOLVED**：三支箭窗口内两个地产龙头相对沪深300 **方向相反**"
            "（保利发展 -3.3pct vs 万科A +18.7pct，E133）→ **「地产板块」是否上涨无法判定**；"
            "本包明确**不允许取平均充当板块表现** → **strength 定为 medium（不升 strong）**。"
            "★ **CF009 保留 KEEP_BOTH**：2018–2019 地方调控放松是否代表中央政策转向（影响启动锚点认定）。"
            "★ peak = 2022-11-29（「第三支箭」次日近 40 股涨停，E008）；end 为**推断值**（confidence low）。"
            + CF013
        ),
    ),
    dict(
        k="004", cid="C-2020-RE-DEBT-RISK", year=2020,
        start="2020-08-20", peak="2021-12-03", end="2022-07-31",
        cls="industry_trend", strength="medium", result="weak", dc="medium",
        cycle="realestate_policy_cycle_2020_2023",
        themes=[("TH-REALESTATE", "related"), ("TH-REALESTATE-DEV", "main")],
        notes=(
            "★ CF007 裁决：**允许进入 Canonical Campaign** —— 沿用既有先例：R01-01 的 `C-2018-HIEQ-ROBOT-DOWN`"
            "（下行周期）与 R01-03 的 `C-2022-SEMI-DOWNTURN`（下行周期）均已进入 canonical。"
            "现有 Independence Gate 是**结构独立性**判据，**不排除负向产业结构**。"
            "★ **`result = weak` 语义（沿用既有口径）**：表示**市场 / 行业方向为负**，"
            "**不表示证据质量弱** —— 本 Campaign 的证据为 8 ev / 8 IG，质量与其它 Campaign 同级。"
            "★ 命名中性化：使用 `C-2020-RE-DEBT-RISK`（地产债务风险暴露），**不使用带方向判断的措辞**。"
            "★ 启动锚点 = 2020-08-20 住建部、人民银行联合召开重点房地产企业座谈会（房地产金融审慎管理制度，"
            "「三道红线」，一手事件）；peak = 2021-12-03（恒大违约，标志性风险高点）；"
            "end = 2022-07-31（2022-07 停工停贷事件后转入「保交楼」政策阶段，阶段边界）。"
            "★ CF006（房地产与金融是否属同一 Theme Cycle）**保留 UNRESOLVED**；"
            "地产 → 银行风险传导（Q005）仅作**机制联系**保留，**未合并任何 Campaign**。"
            + CF013
        ),
    ),
    dict(
        k="005", cid="C-2024-FIN-BROKER-POLICY", year=2024,
        start="2024-09-24", peak="2024-10-08", end="2024-10-31",
        cls="mixed", strength="medium", result="positive", dc="low",
        cycle="broker_risk_appetite_2024",
        themes=[("TH-FIN", "related"), ("TH-FIN-NONBANK", "main")],
        notes=(
            "★ CF003 裁决：**保留 UNRESOLVED —— 未因代表股跑赢就排除 Beta**。"
            "两侧证据：P1 政策组合拳（2024-09-24 央行宣布降准 0.5pct、降政策利率 20bp，**一手**；"
            "同日三大金融管理部门同场发布货币/资本市场/地产政策）；P2 **全市场 Beta 不可分离**"
            "（2024-10-08 成交额 **3.5 万亿元创历史新高**，属全市场级别流动性/风险偏好行情；"
            "券商为 Beta 的高弹性代理）。"
            "★ **东方财富在 2024-09-13→10-08 的相对幅度达 +102.1pct（E135）—— 该数量级本身即"
            "「成交量 Beta 代理」的信号，不是行业 Alpha 的信号**（Worker 原话）。"
            "★ 判为独立 Campaign 的依据（**不基于相对强度**）：① 有**独立启动锚点**（2024-09-24 央行政策，一手）；"
            "② 有可测的 A 股响应（中信证券 +59.3%、相对 +34.7pct，E139）；③ `classification = mixed`（政策+流动性）。"
            "★ **降级项**：生命周期仅 **11 个交易日**（2024-09-24→10-08）→ `date_confidence = low`；"
            "`strength = medium`（**未升 strong**）；`end = 2024-10-31` 为**推断值**（无同期结束证据）。"
            "★ **CF013 / Beta caveat**：" + CF013
        ),
    ),
    dict(
        k="006", cid="C-2023-FIN-SOE-VALUATION", year=2023,
        start="2023-04-01", peak="2023-05-11", end="2023-06-30",
        cls="theme_campaign", strength="medium", result="positive", dc="low",
        cycle="bank_valuation_2023_2025",
        themes=[("TH-FIN", "related"), ("TH-FIN-BANK", "main")],
        notes=(
            "★ CF005 裁决（「中特估」银行与保险是否应拆分）：**判为一个 Campaign，保留 Conflict**。"
            "Gate：Q1 注意力中心 =「**中国特色估值体系**」叙事（**横跨银行/保险/低估值央国企的统一叙事**）✓；"
            "Q4 生命周期 = 银行与保险**同一窗口**（2023-04 → 2023-06）**同步** ✓；"
            "Q2 代表标的跨两个子行业（工商银行/中信银行/中国平安/中国人寿）—— 由「**同一叙事**」解释。"
            "**未机械合并**：本 Campaign 与 007（银行高股息，资金配置驱动）机制不同，**分属不同 Theme Cycle**。"
            "★ **CF004 保留 UNRESOLVED**（银行上涨：行业重估 vs 红利风格因子抱团）。"
            "★ **已知弱点**：① 生命周期未闭合（peak/end 均为推断，confidence low）；"
            "② 仅 1 条同期证据（E052）；③ `start` 为 DATE_WINDOW（2023-04 月内区间，不给精确到日）。"
            "★ peak = 2023-05-11（同期研报仍描述保险「明显…」的最后一日，E051/E052 窗口右沿）。"
            + CF013
        ),
    ),
    dict(
        k="007", cid="C-2024-FIN-BANK-DIVIDEND", year=2024,
        start="2024-01-01", peak=None, end=None,
        cls="industry_trend", strength="medium", result="positive", dc="low",
        cycle="bank_valuation_2023_2025",
        themes=[("TH-FIN", "related"), ("TH-FIN-BANK", "main")],
        notes=(
            "★ CF004 裁决：**保留 UNRESOLVED —— 未把「银行上涨」本身当作独立机制**。"
            "两侧证据：P1 行业重估（低利率 + 资产荒 + 高股息 + 长期资金配置）；"
            "P2 **红利风格因子抱团**（与跨行业「红利/低估值/防御」风格因子高度耦合，"
            "银行 Alpha 与红利因子是否可分**未做验证**）。"
            "★ **与 008 的机制区分（本包明确未合并）**：本 Campaign = **资金配置驱动**（非信用扩张）；"
            "008 = **信用周期驱动**（经济复苏 + 信用成本改善）—— 两者同属银行但**机制相反**；"
            "行情支持该区分（2020-11~2021-03 银行跑赢时券商跑输 -24.9pct）。二者同属 Theme Cycle "
            "`bank_valuation_2023_2025` / `bank_credit_cycle_2020_2021`（**分属不同 Cycle**）。"
            "★ **`peak_date = NULL` / `end_date = NULL`** —— **结构可能仍在延续**；"
            "Worker 明确「**不得把观察窗口结束当作 Peak/End**」→ **不制造完整日线生命周期**、"
            "**不把端点数据当作精确 peak**。`start = 2024-01-01`（lifecycle MAIN_RISE 起点，"
            "原包 start 为 PHASE_WINDOW「2023 年内逐步形成」，无单一启动事件）。"
            "★ `date_confidence = low`（**无启动锚点**）；`strength = medium`（**因子不可分离**）。"
            + CF013
        ),
    ),
    dict(
        k="008", cid="C-2020-FIN-BANK-CREDIT", year=2020,
        start="2020-10-30", peak="2021-03-03", end="2021-03-31",
        cls="industry_trend", strength="medium", result="positive", dc="low",
        cycle="bank_credit_cycle_2020_2021",
        themes=[("TH-FIN", "related"), ("TH-FIN-BANK", "main")],
        notes=(
            "★ §10 裁决（根据正式 Gate，**不基于相对强度**）：**判为独立 Campaign**。"
            "Gate：Q1 独立注意力中心 =「**经济复苏 + 信用成本改善**」（**信用周期驱动**），"
            "与 007 的「低利率 + 资产荒 + 高股息」（**资金配置驱动**）**机制相反** ✓；"
            "Q2 代表标的（招商银行/工商银行）与 007 部分重叠 —— 由「同一子行业的不同机制周期」解释；"
            "Q3 持续性成立（2020-10-30 → 2021-03-31，约 5 个月）；Q4 独立生命周期成立；Q5 双向成立。"
            "★ **降级项（本包如实记录）**：① 仅 **4 ev / 4 IG**（门槛下限）；② **仅 1 条同期市场证据**"
            "（E070，2021-03-03 单日大涨报道）；③ **无可靠启动 / 结束锚点**（start/end 均为 PHASE_WINDOW，"
            "confidence low）；④ **单一代表标的**（工商银行）—— 缺行业指数广度与多标的验证。"
            "→ `strength = medium`、`date_confidence = low`；**建议后续补证**（多标的 / 行业指数广度 + 启动与结束证据）。"
            "★ 净利润 +12.6% 部分源于 2020 年低基数，机制解释存在争议。"
            + CF013
        ),
    ),
    dict(
        k="010", cid="C-2025-FIN-INSURANCE", year=2025,
        start="2025-01-01", peak=None, end=None,
        cls="industry_trend", strength="medium", result="positive", dc="low",
        cycle="insurance_asset_liability_2025",
        themes=[("TH-FIN", "related"), ("TH-FIN-NONBANK", "main")],
        notes=(
            "★ CF012 裁决：**保留 UNRESOLVED —— 未消解**。"
            "P1 板块年度叙事（2025 年保险指数涨超 30%）；"
            "P2 **登记代表标的（中国平安）相对沪深300 跑输约 -5.8pct**（E137）→ "
            "**代表标的与板块叙事方向冲突**，本包**无法在本轮内判定板块内部是否显著分化**（Q012）。"
            "★ **与 005 的区分**：本 Campaign 有 lifecycle（MAIN_RISE 2025-01-01→2025-12-31）；"
            "机制为**保险资产端（权益/高股息）+ 负债端（长期资金入市）共振**，与券商（成交量/风险偏好）不同 ✓。"
            "★ **`peak_date = NULL` / `end_date = NULL`** —— 2025 年内未确认峰值，年度盘点口径下不判定 End ✓。"
            "★ 已知弱点：① 仅 4 ev / 4 IG；② **无启动锚点**（start 为年度趋势型）→ `date_confidence = low`；"
            "③ 保险资产端与权益市场高度耦合，存在「**市场 Beta 经资产端传导**」的特殊污染路径，**无法分离**。"
            + CF013
        ),
    ),
]

RESEARCH_ONLY = [
    dict(
        k="002", cid="RC-2024-RE-POLICY-517", year=2024,
        start="2024-05-17", peak="2024-05-17", end="2024-09-13",
        cls="event_driven", cycle="realestate_policy_cycle_2020_2023",
        themes=[("TH-REALESTATE", "related"), ("TH-REALESTATE-DEV", "main")],
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。理由：**市场层强反向证伪** —— "
            "2024-05-17「5·17」新政当日保利发展单日 +10.66%、万科A +10.02%，"
            "但至 2024-09-13 保利发展 **-31.3%**、万科A **-29.8%**，同期沪深300 -14.1%，"
            "**相对 -17.2pct / -15.7pct**（E134）；同期工商银行 +8.7%（相对 +22.8pct）。"
            "→ **政策的市场反应是一个单日脉冲，4 个月内全部回吐**。"
            "★ 本候选的价值已由 Worker 明确定位为「**市场层证伪的教（样本）**」——"
            "「**政策放松 ≠ 地产周期反转**」此前只有行业数据层证据，v2 补行情后**市场层也闭合**。"
            "★ `confidence = low` 维持不变。"
        ),
    ),
    dict(
        k="003", cid="RC-2019-RE-EASING", year=2019,
        start="2018-12-18", peak=None, end="2019-04-19",
        cls="unclear", cycle="realestate_policy_cycle_2020_2023",
        themes=[("TH-REALESTATE", "related"), ("TH-REALESTATE-DEV", "main")],
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。理由：① `research_status = INSUFFICIENT` · `confidence = low`；"
            "② **市场层证伪** —— 2018-11-30 至 2019-04-19 保利发展相对沪深300 **-18.2pct**、万科A **-0.4pct**，"
            "**两个地产龙头均未跑赢基准**（E130）；而同期中信证券 **+52.3%**（相对 +22.4pct）；"
            "③ 同期卖方明确认为地方放松**不代表中央政策转向**（直接反证）；"
            "④ `exclusion X012` 已明确记录其 **NOT_A_CAMPAIGN**。"
            "★ CF009（地方调控放松是否代表中央政策转向）**保留 KEEP_BOTH**。"
        ),
    ),
    dict(
        k="009", cid="RC-2020-FIN-BROKER-VOLUME", year=2020,
        start="2020-07-02", peak=None, end=None,
        cls="mixed", cycle="broker_risk_appetite_2020",
        themes=[("TH-FIN", "related"), ("TH-FIN-NONBANK", "main")],
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。理由（**Gate 不成立**）："
            "① **`lifecycle` 为 `UNKNOWN`（无任何阶段）** —— **Q4 独立生命周期不成立**；"
            "② `start = 2020-07-02` 为 **confidence low**，包内自述「**本包仅能确认该日，不确认为真正起点**」；"
            "`peak` / `end` 均为 PHASE_WINDOW 且**无具体日期** → **Q3 持续性不成立**（约 1 个月，无生命周期）；"
            "③ **Q5 残差检验不成立** —— **核心反证就在证据本身**：同期报道明确写出"
            "「银行、保险、互联网金融等大金融**全线走高**」（E081），这是**典型的市场 Beta 形态**，"
            "券商只是高弹性代理；④ CF008（资本市场改革驱动 vs 成交量驱动）**保留 UNRESOLVED**。"
            "★ 与 005（2024-09）**未因都叫「券商行情」而合并** —— 两者分属不同 Theme Cycle，"
            "且 005 有 lifecycle 与一手政策锚点、009 两者皆无。"
            "★ **相对强度（+21.6pct，E131）不作为 Promote 依据** —— Beta 无法排除。"
        ),
    ),
    dict(
        k="011", cid="RC-2016-RE-SHANTY", year=2016,
        start="2015-12-21", peak=None, end=None,
        cls="unclear", cycle="realestate_policy_cycle_2020_2023",
        themes=[("TH-REALESTATE", "related"), ("TH-REALESTATE-DEV", "main")],
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。理由：① `INSUFFICIENT` / `low`；② **仅 2 ev / 2 IG**；"
            "③ **市场响应层完全空白** —— 2015—2016 年前复权序列存在**复权因子异常**"
            "（保利发展 2016-12-30 = 4.7254 与 2017-12-29 = 10.0604 的隐含复权因子相差约 57%，无法用分红解释），"
            "Worker 据此**不采用量化证据** → 无法建立「政策 → 行业数据 → 市场响应」三层链条的第三层；"
            "④ 同期 A 股处于 2015 年杠杆牛与股灾的极端 Beta 环境，地产板块响应与全市场不可分离。"
            "★ **未因存在政策 / 历史叙述而提升状态** ✓"
        ),
    ),
    dict(
        k="012", cid="RC-2015-FIN-LEVERAGE", year=2015,
        start=None, peak=None, end=None,
        cls="unclear", cycle="finance_beta_2015",
        themes=[("TH-FIN", "main")],
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。理由：① `INSUFFICIENT` / `low`；② **仅 2 ev / 2 IG**；"
            "③ **`PIT = 0`** —— 全部证据为 retrospective 复盘，**无一条同期证据**；"
            "④ **无任何行情数据**（起止、峰值、板块口径全缺）；"
            "⑤ 机制本身就是「**杠杆资金驱动的市场 Beta**」，按 `historical_campaign_validation_v1.md §4.3`，"
            "**无法排除 Beta 污染时必须保持低置信度**。"
            "★ `exclusion X001` 已明确建议：**不作为独立金融 Campaign**（建议 Observation）。"
        ),
    ),
]

ANNUAL = {
    2020: ("medium", "地产融资审慎管理制度（三道红线）落地与银行信用周期；**地产债务风险暴露段启幕。**"),
    2022: ("medium", "地产融资「三支箭」+ 保交楼政策驱动的 A 股地产修复行情（政策脉冲）。"),
    2023: ("medium", "「中国特色估值体系」驱动的银行/保险重估行情；**生命周期未闭合。**"),
    2024: ("medium", "银行高股息重估（资金配置驱动）与 2024-09 政策组合拳下的券商/非银行情；**均含 Beta 未排除项。**"),
    2025: ("medium", "保险资产端与负债端共振行情；**CF012 代表标的与板块叙事冲突未决，peak/end 未确认。**"),
}

SEC_CANON = {
    "R01-FINRE-SEC001": ("POLY", "600048", "保利发展", "SH"),
    "R01-FINRE-SEC002": ("VANKE", "000002", "万科A", "SZ"),
    "R01-FINRE-SEC003": ("CMSK", "001979", "招商蛇口", "SZ"),
    "R01-FINRE-SEC004": ("GEMDALE", "600383", "金地集团", "SH"),
    "R01-FINRE-SEC005": ("ICBC", "601398", "工商银行", "SH"),
    "R01-FINRE-SEC006": ("ABC", "601288", "农业银行", "SH"),
    "R01-FINRE-SEC007": ("CMB", "600036", "招商银行", "SH"),
    "R01-FINRE-SEC008": ("CNCB", "601998", "中信银行", "SH"),
    "R01-FINRE-SEC009": ("CITICS", "600030", "中信证券", "SH"),
    "R01-FINRE-SEC010": ("EASTMONEY", "300059", "东方财富", "SZ"),
    "R01-FINRE-SEC011": ("PINGAN", "601318", "中国平安", "SH"),
    "R01-FINRE-SEC012": ("CHINALIFE", "601628", "中国人寿", "SH"),
    "R01-FINRE-SEC013": ("NCI", "601336", "新华保险", "SH"),
    "R01-FINRE-SEC014": ("EBSEC", "601788", "光大证券", "SH"),
    "R01-FINRE-SEC015": ("ZSSEC", "601878", "浙商证券", "SH"),
}

EVENTS = [
    ("EV-FINRE-01", "2022-11-08", "交易商协会公告「第二支箭」延期并扩容（民营企业债券融资支持工具）", "policy", "R01-FINRE-E001"),
    ("EV-FINRE-02", "2022-11-29", "证监会「第三支箭」恢复涉房上市公司并购重组及配套融资；次日地产股近 40 只涨停", "policy", "R01-FINRE-E008"),
    ("EV-FINRE-03", "2020-08-20", "住建部、人民银行联合召开重点房地产企业座谈会，实施房地产金融审慎管理制度（三道红线）", "policy", "R01-FINRE-E030"),
    ("EV-FINRE-04", "2021-12-03", "中国恒大公告无法履行 2.6 亿美元担保义务（标志性债务违约）", "company", "R01-FINRE-E035"),
    ("EV-FINRE-05", "2024-09-24", "央行行长宣布降准 0.5 个百分点、降低政策利率 20 个基点；三大金融管理部门同场发布政策组合", "policy", "R01-FINRE-E040"),
    ("EV-FINRE-06", "2024-10-08", "A 股复市大幅高开后回落，同日成交额 3.5 万亿元创历史新高", "market", "R01-FINRE-E044"),
    ("EV-FINRE-07", "2023-04-01", "「中国特色估值体系」叙事重新领涨（券商策略复盘口径，月内区间起点）", "market", "R01-FINRE-E050"),
    ("EV-FINRE-08", "2023-05-11", "同期研报仍描述保险板块「明显…」（中特估窗口右沿）", "market", "R01-FINRE-E051"),
    ("EV-FINRE-09", "2021-03-03", "银行股全线大涨（本包唯一同期市场证据日）", "market", "R01-FINRE-E070"),
    ("EV-FINRE-10", "2021-03-31", "2020 年商业银行净利润同比 +12.6%（公布于 2022-02，属后续确认）", "industry", "R01-FINRE-E071"),
    ("EV-FINRE-11", "2025-09-19", "2024-12-31 至 2025-09-19 相对表现锚点：工商银行相对 -5.1pct、中国平安相对 -5.8pct", "market", "R01-FINRE-E137"),
    ("EV-FINRE-12", "2023-12-29", "2023-01-31 至 2023-12-29 工商银行 +24.7%，同期沪深300 -17.5%，相对 +42.2pct", "market", "R01-FINRE-E140"),
    ("EV-FINRE-13", "2024-05-17", "央行、金融监管总局发布通知：首付降至 15%/25%、取消全国层面房贷利率下限；同日设立 3000 亿元保障性住房再贷款", "policy", "R01-FINRE-E011"),
    ("EV-FINRE-14", "2019-04-19", "2018-11-30 至 2019-04-19 相对表现锚点：保利发展相对 -18.2pct、万科A -0.4pct（地产未跑赢）", "market", "R01-FINRE-E130"),
    ("EV-FINRE-15", "2020-07-15", "2020-06-30 至 2020-07-15 中信证券 +35.6%、东方财富 +39.9%（相对 +21.6pct / +26.0pct）", "market", "R01-FINRE-E131"),
]

CAMPAIGN_EVENTS = [
    ("C-2022-RE-POLICY-THREE", "EV-FINRE-01", "trigger"),
    ("C-2022-RE-POLICY-THREE", "EV-FINRE-02", "catalyst"),
    ("C-2020-RE-DEBT-RISK", "EV-FINRE-03", "trigger"),
    ("C-2020-RE-DEBT-RISK", "EV-FINRE-04", "follow_up"),
    ("C-2024-FIN-BROKER-POLICY", "EV-FINRE-05", "trigger"),
    ("C-2024-FIN-BROKER-POLICY", "EV-FINRE-06", "follow_up"),
    ("C-2023-FIN-SOE-VALUATION", "EV-FINRE-07", "trigger"),
    ("C-2023-FIN-SOE-VALUATION", "EV-FINRE-08", "follow_up"),
    ("C-2020-FIN-BANK-CREDIT", "EV-FINRE-09", "follow_up"),
    ("C-2020-FIN-BANK-CREDIT", "EV-FINRE-10", "catalyst"),
    ("C-2024-FIN-BANK-DIVIDEND", "EV-FINRE-12", "follow_up"),
    ("C-2025-FIN-INSURANCE", "EV-FINRE-11", "follow_up"),
]

# ★ Shared Evidence 的唯一归属（1 evidence : 1 campaign）
#   E141（沪深300 基准，被 10 候选共享）：**不绑定任何 Campaign** —— 其 evidence_role = `context`
#     （全局基准，保留在研究层；context 孤儿不触发 validate_db 告警）
#   E132（004 / 008）→ 008（其核心证据）· E137（007 / 010）→ 010 · E140（006 / 007）→ 006
EVIDENCE_OWNER = {
    "R01-FINRE-E132": "008",
    "R01-FINRE-E137": "010",
    "R01-FINRE-E140": "006",
}
# 全局基准 evidence：不写入 campaign_evidences
GLOBAL_BENCHMARK_EV = {"R01-FINRE-E141"}


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
                raise SystemExit("FAIL 证券助记符冲突: %s 既有=%s 新=%s" % (sid, existing_sec[sid], nm))
            reuse_sec.add(sid)
    if reuse_sec:
        print("  复用既有证券: %s" % sorted(reuse_sec))

    if not have("research_rules", "rule_id", RULE_ID):
        add("research_rules", RULE_ID,
            "INSERT INTO research_rules (rule_id,name,base_pattern,description,status) VALUES (?,?,?,?,?)",
            (RULE_ID, "金融 / 房地产历史周期观察", "金融", "R01-05（金融 / 房地产）历史周期观察窗口。" + PROV, "under_review"))

    # ★ §13：为每个 campaign_year 建 annual_review（避免重现 R01-04 的 AR-CONS-2018 问题）
    for yr in sorted(ANNUAL):
        arid = "AR-FINRE-%d" % yr
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
                (c["cid"], "AR-FINRE-%d" % c["year"], RULE_ID, c["cycle"], c["year"], c["start"], c["end"], c["peak"],
                 c["strength"], c["result"], c["cls"],
                 "研究候选日期（intake date_candidates）；未经行情核验",
                 "研究候选日期（intake date_candidates）；未经行情核验",
                 c["dc"],
                 "%s［intake R01-FINRE-%s］" % (cand_by_k[c["k"]]["title"], c["k"]),
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
        sid = "S-FINRE-%02d" % i
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
        eid = "E-FINRE-%02d" % i
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
            if ieid in GLOBAL_BENCHMARK_EV:
                continue  # 全局基准不绑定 Campaign（见 EVIDENCE_OWNER 注释）
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
             "SECONDARY": "secondary_rally", "PEAK": None, "UNKNOWN": None, "ENDED": None}
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
            pid = "PH-FINRE-%02d" % ph_n
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
                     "candidate 快照自 R01-05 intake date_candidates；未经行情核验。｜%s" % PROV))

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
