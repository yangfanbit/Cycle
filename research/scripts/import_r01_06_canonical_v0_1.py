#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""import_r01_06_canonical_v0_1.py —— R01-06（国防军工）Canonical Import。

依据：`docs/R01_06_INTAKE_REVIEW_v0_1.md` + 本轮 Canonical Decision（Independence Gate Q1–Q5）。

结果（**2 PROMOTE + 5 RESEARCH_ONLY**）：
  PROMOTE → campaigns 表
    001 2020–2021 装备放量 / 主机厂订单与预付款 → C-2020-MIL-EQUIP-ORDER
    002 2019「南北船」合并 / 集团战略重组        → C-2019-MIL-GROUP-RESTRUCTURE
  RESEARCH_ONLY → **不入 campaigns 表**（仅导出层 research_candidates）
    003 2019 国庆 70 周年阅兵（全 retrospective）      → RC-2019-MIL-PARADE-70
    004 2025 抗战 80 周年阅兵 / 军贸 / 十五五（复合机制） → RC-2025-MIL-PARADE-80
    005 2017 军民融合 / 军工混改（生命周期未闭合）        → RC-2017-MIL-MIXED-REFORM
    006 2015 改革牛 / 资产证券化（Beta 不可分离）        → RC-2015-MIL-REFORM-BULL
    007 2024–2025 商业航天 / 卫星互联网（族属未定）       → RC-2024-MIL-COMMERCIAL-SPACE

★ E042 特别处理：2022 国防预算 +7.1% vs 军工板块 -23.6%（反向证据）
  → **入 DB 但不绑定任何 Campaign**（`evidence_role = context`，research-level）。
  理由：原绑定对象 006（2015）判为 RESEARCH_ONLY；且 2022-03-10 的 contemporaneous
  证据若绑定到 2015 Campaign 会触发 `validate_db` 的 evidence-temporal-mislabel。
  不进入任何 canonical Campaign → 不破坏 temporal consistency（与 R01-05 的 E141 同口径）。

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
PKG = os.path.join(ROOT, "research", "intake", "packages", "R01-06")

RULE_ID = "rule_defense_military"
PROV = "R01-06 Intake Package（source_commit 2153f6d）｜Canonical Decision docs/R01_06_INTAKE_REVIEW_v0_1.md"

# ★ CF008 裁决：军费 → 订单传导的时滞 caveat（写入 001）
CF008 = (
    "★ **CF008 裁决（军费 → 订单传导时滞）**：传导**存在但不稳定**，且**军费层不得作为 Campaign start 锚点**。"
    "实测链条（2021）：国防预算公布 **2021-03-08**（国防部，T1）→ 主机厂订单/预付款披露 **2021-03-30**（中航沈飞公告，T1 一手）"
    "→ 五大主机厂集中披露 **2021-04-01** → 市场主升启动 **2021-05-11**（**距预算公布约 9 周**）"
    "→ 合同负债体现（2021H1 末 2021-06-30，半年报 8–9 月披露）→ 区间高点 **2021-12-01**（**距预算公布约 9 个月**）。"
    "★ **反向对照**：2022 年国防预算 **+7.1%**（阶段新高）而军工板块全年 **-23.63%** → **传导非稳定**。"
    "★ **2020H2 启动（2020-06-25 窗口）早于 2021 预算公布约 8 个月** → 2020H2 不可能由 2021 预算驱动，"
    "其驱动为 2020-07 媒体「装备采购加速」叙事 + 券商「十四五」叙事（**非政策文件**）。"
    "→ **军费层只能作 `context`**；本 Campaign 的 `start` 取 2020H2 启动窗口，**非军费公布日**。"
)

# ★ CF001 裁决：不拆分
CF001 = (
    "★ **CF001 裁决（2020H2 与 2021 是否同一 Campaign）：判为一个 Campaign，不拆分**。"
    "Gate：**Q2 = 否**（代表标的完全重叠：中航沈飞/航发动力/中直股份/洪都航空/中航西飞）、"
    "**Q1 倾向否**（同一资金池；Q1 Anti-example）、**Q3 / Q4 无法判定**（2020-08 中旬~12 月区间数据缺失，"
    "无法证明两段之间存在明确阶段边界）、**Q5 单向成立**（去掉 2020H2，2021 的「预算→订单→合同负债→市场」链条仍完整；"
    "去掉 2021，2020H2 仅剩约 1.5 个月预期段 + 5 个月空白，**不能独立构成 Campaign**）。"
    "→ 多数项为「否 / 无法判定」→ **按 Gate 不拆分**。"
    "★ 本包 `date_candidates.start` 给出两个锚点（2020-06-25~07-05 与 2021-03-29~03-31）；"
    "**本裁决取第一个（2020-06-25）为 Campaign start**，第二个作为「订单兑现段起点」记录在 `drivers.accelerator`。"
    "★ **保留重新评估条件**：若后续补齐 2020-08~12 连续行情数据并证明存在明确阶段边界，可重新评估拆分为两个 Campaign。"
)

# ★ CF003 裁决：军工电子为 Sub-theme
CF003 = (
    "★ **CF003 裁决（军工电子 Sub-theme vs 独立 Campaign）：判为 Sub-theme，不单独建 Campaign**。"
    "与 T01 的既定 taxonomy 一致（T01 已将 `军工电子` 设为 `国防军工` 下的 `concept`：买方为军方，"
    "与「电子」的国产替代机制不同）。军工电子与航空装备、新材料共享资金池、生命周期高度一致（2022 年同步大幅回调），"
    "符合 Q1 Anti-example。★ 与 R01-02（半导体/电子）的 cross-task dedupe 仍待办（`N002` / `Q006`）。"
)

# ★ CF011 类 caveat：市场层证据等级
MKT_CAVEAT = (
    "★ **市场层证据等级**：本 Campaign 的 A 股市场侧证据（中证军工指数区间涨跌、申万国防军工行业比较、"
    "公募基金持仓比例）**全部为 Tier 3 二手整理**（同花顺 / 东方财富转载研报），"
    "**未取得指数公司官方历史点位原文**（`known_gaps[11]`）。"
    "★ **2020-07 启动段与 A 股整体放量上涨（Beta）重叠，本包不宣称已分离**（`Q002` 未决）。"
)

CAMPAIGNS = [
    dict(
        k="001", cid="C-2020-MIL-EQUIP-ORDER", year=2020,
        start="2020-06-25", peak="2021-12-01", end="2022-12-31",
        cls="mixed", strength="medium", result="positive", dc="medium",
        cycle="military_equipment_order_cycle_2020_2022",
        themes=[("TH-DEFENSE", "related"), ("TH-DEFENSE-AIR", "main")],
        notes=(
            "★ **本包唯一具备「军费 → 订单 → 基本面 → A 股市场」四层可复核链条的 Campaign**（17 ev / 14 IG）。"
            "① **军费层**：`E004`（2021 国防预算 13795.44 亿元 / +6.8%，**国防部官网 T1**）—— "
            "该 evidence 自述「**不是订单本身，不单独构成订单兑现证据**」；"
            "② **订单层**：`E001` 中航沈飞 2021 年度**日常关联交易预计公告**（**巨潮资讯网 = 证监会指定披露平台，T1 一手 PDF**）"
            "—— ★ 该 evidence 明确写「**公告具体金额本文不引用，以避免依赖二级转述**」→ **未把代理变量写成精确订单总额**；"
            "补强 `E002`（截至 2021-04-01 五大主机厂均已披露，天风证券研报 T3，自述「独立性弱于公告原文」）；"
            "③ **基本面层**：`E003` 中航沈飞 2021H1 末**合同负债 377.37 亿元** —— ★ **明确标注为会计口径代理变量**，"
            "且自述「未取得公告原文，经券商研报引用」；`E015` 2021Q3 公募军工持仓 2.10%（主动配置创 2014 年来最高）；"
            "④ **市场层**：`E008`/`E009`（中证军工指数 2021 +8.97%、2021-12-01 高点 14748 点）、"
            "`E010`/`E012`（申万军工 2021 +8.6%）、`E016`（2022 细分板块普遍下跌）。"
            "★ **strength 定为 medium（不升 strong）** —— 尽管四层链条完整，但：市场层全为 T3 二手、"
            "2020-07 启动段 Beta 未分离、`peak` 存在 2 个口径（2021-08-24 与 2021-12-01）、`end` 存在 2 个口径、"
            "2020-08 中旬~12 月数据缺失。**四层证据完整 ≠ 强度 strong**。" + CF001 + CF008 + CF003 + MKT_CAVEAT +
            "★ `peak` 取 **2021-12-01**（中证军工指数 14748 点，EXACT_DATE）；alternative = 2021-08-24"
            "（中证军工指数 5/11–8/24 上涨 43% 的区间高点）→ **peak cluster，不强行取单一日期**。"
            "★ `end` 取 **2022-12-31**（「主题持续性与资金关注显著下降」口径，与 lifecycle 的 DECLINING 段一致）；"
            "alternative = 2022-01-31（「最后一次有效催化」口径）→ **两口径并存，已在 notes 保留**。"
            "★ 生命周期含 **2021-01-08 → 2021-05-10 的 -32% 内部回撤**（RETRACEMENT）。"
            "｜theme_cycle_id=military_equipment_order_cycle_2020_2022｜provenance: " + PROV
        ),
    ),
    dict(
        k="002", cid="C-2019-MIL-GROUP-RESTRUCTURE", year=2019,
        start="2019-07-01", peak=None, end="2019-11-26",
        cls="event_driven", strength="medium", result="positive", dc="medium",
        cycle="military_group_restructure_2019",
        themes=[("TH-DEFENSE", "related"), ("TH-DEFENSE-SHIP", "main")],
        notes=(
            "★ **CF002 裁决（2019 南北船重组 vs 2019 国庆阅兵 是否合并）：不合并**。"
            "机制不同 —— 本 Campaign = **集团层面组织与资产重组**（不由军费、订单或业绩驱动）；"
            "003（阅兵）= 事件注意力驱动。**未因同属 2019 年军工而合并**。"
            "★ Gate：**Q1 = 是**（独立注意力中心 = 军工集团战略性重组）；"
            "**Q2 = 是**（独立代表标的组：中国船舶 / 中国重工 / 中船防务，与主机厂完全不重叠）；"
            "**Q3 = 是**（2019-07-01 → 2019-11-26，约 5 个月，事件链有层级跃迁：筹划公告 → 国务院批准 → 集团揭牌）；"
            "**Q4 = 独立但未完全闭合**（`peak` 缺失：无 2019-07~08 中船系行情数据）；"
            "**Q5 = 是**（去掉本 Campaign，军工主线（001）仍完整）。→ 多数成立 → **Case C**。"
            "★ **`peak_date = NULL`** —— 本包未取得 2019 年 7–8 月中船系个股/板块峰值的可靠日期证据，"
            "**不制造精确日期**（`date_candidates.peak` 为 PHASE_WINDOW，无具体日期）。"
            "★ `start = 2019-07-01`（两船集团旗下 **9 家上市公司同步发布筹划战略性重组公告**，"
            "E018 / 国际船舶网 T3；取**公告日**，非市场反应日 2019-07-02）；"
            "`end = 2019-11-26`（中国船舶集团有限公司**揭牌成立**，重组事项执行完成，E020 / 央企官网 T2）；"
            "alternative end = 2019-10-25（经国务院批准联合重组，E019 / 人民网转国资委 T2）→ **两口径并存**。"
            "★ **已知弱点（如实记录，未美化）**：① **仅 3 ev / 3 IG**（门槛下限）；"
            "② **市场侧行情证据完全缺失**（涨幅 / 峰值 / 持续时间均不可考）→ **无行情核验**；"
            "③ 个股名单来自「9 家上市公司」的**推断**（来源未逐一点名，已在 securities.basis 标注）；"
            "④ `SEC010`（中船防务）同时出现在 2019（重组）与 2020（装备放量）两轮结构中 —— "
            "**不得据以认定两轮属同一 Campaign**。"
            "★ **`classification = event_driven`**（driver 为离散重组事件，有明确执行完成日；非广泛主题趋势）。"
            "★ **CF005（船舶：民船周期 vs 军品订单）保留 UNRESOLVED** —— 本 Campaign **仅承载「集团重组」机制**，"
            "2021–2024 民船订单/船价周期未建候选（`X005` HANDOFF）。"
            "★ **与 T01 的张力已记录**：T01 将 `船舶制造`（含民用造船周期）归 `国防军工`；"
            "本包的机制切分（民船周期不并入）需在 R01 收口的 Governance Review 中对齐。"
            "｜theme_cycle_id=military_group_restructure_2019｜provenance: " + PROV
        ),
    ),
]

RESEARCH_ONLY = [
    dict(
        k="003", cid="RC-2019-MIL-PARADE-70", year=2019,
        start="2019-08-07", peak="2019-09-03", end=None,
        cls="event_driven", cycle="military_parade_event_2019",
        themes=[("TH-DEFENSE", "related"), ("TH-DEFENSE-AIR", "main")],
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。**Gate 不成立**："
            "① **Q2 = 否** —— `security_ids` 仅 1 个宽基指数（申万国防军工指数），**无独立代表标的组**；"
            "② **Q3 = 否** —— 持续性仅约 4 周（2019-08-07 → 2019-09-03），事件驱动型持续性不足；"
            "③ **Q4 = 否** —— **全部 3 条证据均为 2025 年发布的 retrospective 复盘材料，无任何同期一手证据**"
            "（`support_kind` 含 `retrospective_context`，已逐条填 `point_in_time_note`）；"
            "④ 与 002 的 Q1 Anti-example（同一资金池）无法排除。"
            "★ 本包自述「**不应作为已成立的历史 Campaign 使用**」→ 本裁决一致。"
            "★ **未因「国庆 70 周年阅兵」事件重大而默认形成 Campaign**（用户明确要求）。"
        ),
    ),
    dict(
        k="004", cid="RC-2025-MIL-PARADE-80", year=2025,
        start="2025-06-24", peak=None, end=None,
        cls="event_driven", cycle="military_parade_event_2025",
        themes=[("TH-DEFENSE", "related"), ("TH-DEFENSE-AIR", "main")],
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。**CF007 裁决：不通过 Gate → 无需在 `theme_campaign` vs "
            "`event_driven` 之间选择（两者皆不成立）**。"
            "① **Q2 = 否** —— `security_ids` 仅 2 个宽基指数（中证军工指数 / 申万国防军工指数），**无独立代表标的组**；"
            "② **Q3 = 弱** —— 窗口约 2.5 个月（2025-06-24 → 2025-09-03）；"
            "③ **Q4 = 否** —— **生命周期未闭合**：`peak` 不可考（`date_candidates.peak` 为 PHASE_WINDOW 无日期）、"
            "阅兵后走向无任何可复核材料（`known_gaps[6]`）；"
            "④ **Q5 = 否** —— 去掉阅兵事件，「军贸」（无订单数据，`Q010`）与「十五五」（无落地证据）**均无法独立构成 Campaign**。"
            "★ **机制复合（阅兵事件 + 军贸外需 + 十五五政策预期）无法形成统一生命周期** → "
            "**按用户要求：不强行合并、也不为保持 Candidate 结构而机械 Promote**；"
            "本包 `why_not` 亦自述「若严格按机制必须明确的要求，可能应拆分为不同结构或降级为 OBSERVATION_ONLY」。"
            "★ **未因「2025 新结构」而机械 Promote**。"
            "★ 阅兵事件本身有 **Tier 1 官方锚点**（2025-06-24 国新办官宣 E024、2025-08-20 阅兵准备发布会 E025），"
            "但**市场响应证据仅 Tier 3 相对强弱描述**（无绝对涨幅、无指数点位）。"
        ),
    ),
    dict(
        k="005", cid="RC-2017-MIL-MIXED-REFORM", year=2017,
        start="2017-01-04", peak=None, end=None,
        cls="theme_campaign", cycle="military_mixed_reform_2017",
        themes=[("TH-DEFENSE", "main")],
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。**需补证后重新评估**。Gate："
            "① **Q1 = 是**（政策文本驱动：2017-01-04 兵器工业集团混改指导意见 → 2017-01-22 中央军民融合发展委员会设立）；"
            "② **Q2 = 否** —— `security_ids` 仅 1 个宽基指数（申万国防军工指数），**无独立代表标的组**；"
            "③ **Q3 = 无法判定**（2017 年 2 月之后走势不可考）；"
            "④ **Q4 = 否** —— **生命周期无法闭合**：`peak` / `end` 均不可考，`known_gaps[4]` 明确记录；"
            "⑤ **Q5 = 无法执行**（生命周期不完整）。→ **多数否 / 无法判定 → 不成立**。"
            "★ **只能证明「政策存在」**（同期政策原文 + 1 月市场响应：1-09 板块集体启动、近 10 只涨停、"
            "1-20 行业排名第 2），**不能证明市场结构**（2017 年全年军工涨跌数据缺失）→ "
            "**按用户要求保持 Research Only**。"
            "★ 本包自述「**没有任何证据显示 2017 年混改已转化为订单或业绩**」→ 政策发布 ≠ 执行 ≠ 订单兑现。"
            "★ **CF009（军民融合 vs 混改 是否同一机制）保留 UNRESOLVED** —— 不影响本候选的存废判定。"
            "★ 补证方向：2017 年军工板块全年 / 分月行情序列 + 混改落地公告（`Q008`）。"
        ),
    ),
    dict(
        k="006", cid="RC-2015-MIL-REFORM-BULL", year=2015,
        start=None, peak="2015-06-04", end=None,
        cls="mixed", cycle="military_reform_bull_2015",
        themes=[("TH-DEFENSE", "related")],
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。**CF006 裁决：Beta 无法排除 → 保持 Research Only**。"
            "① **Q2 = 否** —— `security_ids` 仅 1 个指数（国证军工指数，且 `ticker` 缺失），**无独立代表标的组**；"
            "② **Q3 = 否**（启动与结束日期均不可考）；"
            "③ **Q4 = 否** —— `start` 不可考（本包未取得 2015 年军工行情的可靠启动日期）、"
            "`end` 不可考（无法把军工的结束与全市场 Beta 的结束分离）；"
            "④ **Q5 = 无法执行** —— 无法把军工自身机制贡献从 2015 年 A 股杠杆牛市中分离。"
            "★ 本包自述「**无法证明这是军工 Campaign 而不是市场 Beta 在军工板块的投射**」、"
            "「**没有任何证据可以把 2015 年军工涨幅与市场 Beta 分离**」、"
            "「**若 ThreeC Agent 判定 Beta 无法排除，应降级为 OBSERVATION_ONLY**」→ **本裁决采纳降级**。"
            "★ **未因 2015 是历史回填空缺年份而降低标准**（用户明确要求）；"
            "按 `historical_campaign_validation_v1.md §4.3`，**无法排除 Beta 污染时必须保持低置信度**。"
            "★ `peak = 2015-06-04`（国证军工指数年初至该日累计 **+117.36%**，中国新闻网 T2）—— "
            "★ 这是**报道口径的区间终点**，**不是严格意义的行情峰值日**，且含大量 Beta。"
        ),
    ),
    dict(
        k="007", cid="RC-2024-MIL-COMMERCIAL-SPACE", year=2024,
        start="2024-08-06", peak=None, end=None,
        cls="industry_trend", cycle="commercial_space_2024_2025",
        themes=[("TH-DEFENSE-SPACE", "related")],
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。**CF004 裁决：族属 UNRESOLVED → 不进入任何族的 canonical**。"
            "① **族属未定**：CMTR v1 对 `商业航天` / `卫星互联网` / `卫星导航` 均为 **UNRESOLVED_NAME**"
            "（taxonomy 中不存在）；只有 `航天装备` 解析到 `国防军工`。"
            "② **机制不是国防采购**（本包自述「驱动来自产业规划与商业需求，不是军费或军品订单」）；"
            "核心催化的**主管部门为工信部 / 国家航天局**，主题是**商业航天 / 卫星通信产业发展**"
            "（E037 国家航天局行动计划 + 商业航天司设立；E038 工信部卫星通信政策）。"
            "③ **`X008` 已将「卫星互联网的通信属性」列为 OUT_OF_SCOPE**（任务书 `excluded_scope` 同）→ **继续遵守**。"
            "④ **Q4 = 否** —— 生命周期未闭合：`peak` / `end` 均不可考，2025 年末仍活跃。"
            "⑤ **Q2 = 是**（独立代表标的组：中国卫星 / 中天火箭 / 宏达电子）；**Q1 = 是**；**Q3 = 是**（约 17 个月、多次催化）。"
            "→ 3/5 成立 + 族属未定 + 生命周期未闭合 → **不进入 canonical**。"
            "★ **未因当前 root 是「国防军工」就默认纳入**（用户明确要求）；"
            "**未扩展 taxonomy**（不新增 root / 子主题）—— taxonomy 变更属独立轮次。"
            "★ 与信息通信族 / R01-02 的 cross-task dedupe 仍待办（`N004` POSSIBLE_DUPLICATE）。"
        ),
    ),
]

ANNUAL = {
    2019: ("medium", "军工集团战略性重组（「南北船」合并）：筹划公告（07-01）→ 国务院批准（10-25）→ 集团揭牌（11-26）；**市场侧行情证据缺失，peak 不可考。**"),
    2020: ("medium", "「十四五」装备放量建设启幕：2020H2 装备采购加速叙事驱动的军工行情启动；**启动段与市场 Beta 重叠，未分离。**"),
}

SEC_CANON = {
    "R01-MIL-SEC001": ("CSIMIL", "399967.SZ", "中证军工指数", "深圳证券交易所"),
    "R01-MIL-SEC002": ("SWMIL", "801740.SI", "申万国防军工指数", "申万宏源（指数编制）"),
    "R01-MIL-SEC003": ("CNIMIL", None, "国证军工指数（深圳证券信息有限公司编制，50只成分股）", "深圳证券信息有限公司"),
    "R01-MIL-SEC004": ("SHENFEI", "600760.SH", "中航沈飞", "上海证券交易所"),
    "R01-MIL-SEC005": ("AECPOWER", "600893.SH", "航发动力", "上海证券交易所"),
    "R01-MIL-SEC006": ("XIFEI", "000768.SZ", "中航西飞", "深圳证券交易所"),
    "R01-MIL-SEC007": ("HONGDU", "600316.SH", "洪都航空", "上海证券交易所"),
    "R01-MIL-SEC008": ("CSSC", "600150.SH", "中国船舶", "上海证券交易所"),
    "R01-MIL-SEC009": ("CSIC", "601989.SH", "中国重工", "上海证券交易所"),
    "R01-MIL-SEC010": ("CSSCDEF", "600685.SH", "中船防务", "上海证券交易所"),
    "R01-MIL-SEC011": ("CHINASAT", "600118.SH", "中国卫星", "上海证券交易所"),
    "R01-MIL-SEC012": ("ZTROCKET", "003009.SZ", "中天火箭", "深圳证券交易所"),
    "R01-MIL-SEC013": ("HONGDA", "300726.SZ", "宏达电子", "深圳证券交易所"),
}

EVENTS = [
    ("EV-MIL-01", "2021-03-08", "国防部公布 2021 年全国财政国防支出预算 13795.44 亿元、比上年预算执行数增长 6.8%", "policy", "R01-MIL-E004"),
    ("EV-MIL-02", "2021-03-30", "中航沈飞披露 2021 年度日常关联交易预计公告（军方大额预付/订单叙事的最早一手可验证锚点）", "company", "R01-MIL-E001"),
    ("EV-MIL-03", "2021-04-06", "五大主机厂（沈飞/航发动力/中直股份/洪都航空/中航西飞）均已披露 2021 年度关联交易预计及甲方大额预付安排", "company", "R01-MIL-E002"),
    ("EV-MIL-04", "2021-12-01", "中证军工指数（399967.SZ）收于 14748 点，为 2021 年区间高点", "market", "R01-MIL-E009"),
    ("EV-MIL-05", "2022-12-31", "2022 年军工细分板块普遍下跌：地面兵装 -2.48%、航海装备 -8.64%，航空装备/航天装备/军工电子跌幅更大", "market", "R01-MIL-E016"),
    ("EV-MIL-06", "2019-07-01", "中船工业集团与中船重工集团旗下合计 9 家上市公司同步发布筹划战略性重组公告", "company", "R01-MIL-E018"),
    ("EV-MIL-07", "2019-10-25", "经国务院批准，中国船舶工业集团与中国船舶重工集团实施联合重组（国资委消息）", "policy", "R01-MIL-E019"),
    ("EV-MIL-08", "2019-11-26", "中国船舶集团有限公司揭牌成立，重组事项执行完成", "company", "R01-MIL-E020"),
]

CAMPAIGN_EVENTS = [
    ("C-2020-MIL-EQUIP-ORDER", "EV-MIL-01", "context"),
    ("C-2020-MIL-EQUIP-ORDER", "EV-MIL-02", "catalyst"),
    ("C-2020-MIL-EQUIP-ORDER", "EV-MIL-03", "catalyst"),
    ("C-2020-MIL-EQUIP-ORDER", "EV-MIL-04", "follow_up"),
    ("C-2020-MIL-EQUIP-ORDER", "EV-MIL-05", "follow_up"),
    ("C-2019-MIL-GROUP-RESTRUCTURE", "EV-MIL-06", "trigger"),
    ("C-2019-MIL-GROUP-RESTRUCTURE", "EV-MIL-07", "catalyst"),
    ("C-2019-MIL-GROUP-RESTRUCTURE", "EV-MIL-08", "follow_up"),
]

PHASES = [
    # 001（与 intake lifecycle 一致；ENDED/UNKNOWN 段不入 DB）
    ("C-2020-MIL-EQUIP-ORDER", "main_rise", "2020-06-25", "2020-08-10", "MAIN_RISE（intake lifecycle）★与2020年7月A股整体Beta重叠，未分离"),
    ("C-2020-MIL-EQUIP-ORDER", "retracement", "2021-01-08", "2021-05-10", "RETRACEMENT（intake lifecycle）中证军工指数区间下跌32%；2020-08中旬~12月数据缺失，未填充"),
    ("C-2020-MIL-EQUIP-ORDER", "main_rise", "2021-05-11", "2021-08-24", "MAIN_RISE（intake lifecycle）中证军工指数区间上涨43%；「订单→业绩」链条最完整的一段"),
    ("C-2020-MIL-EQUIP-ORDER", "retracement", "2021-08-25", "2021-10-13", "RETRACEMENT（intake lifecycle）中证军工指数区间下跌13.8%；中航工业集团集中减持"),
    ("C-2020-MIL-EQUIP-ORDER", "secondary_rally", "2021-10-14", "2021-11-30", "SECONDARY（intake lifecycle）中证军工指数区间上涨22.5%"),
    ("C-2020-MIL-EQUIP-ORDER", "decline", "2021-12-02", "2022-12-31", "DECLINING（intake lifecycle）2022年业绩预告不及预期；2022全年申万国防军工-23.63%；2023年「十四五」中期调整致订单放缓"),
    # 002（peak 缺失；ENDED 段无对应 phase_type，不入 DB）
    ("C-2019-MIL-GROUP-RESTRUCTURE", "main_rise", "2019-07-02", None, "MAIN_RISE（intake lifecycle）重组公告后的市场反应窗口；★结束日期不可考，留空，不强行取值"),
    ("C-2019-MIL-GROUP-RESTRUCTURE", "secondary_rally", "2019-10-25", "2019-10-28", "SECONDARY（intake lifecycle）国资委10-25消息：经国务院批准实施联合重组"),
]

# ★ research-level evidence：入 DB 但不绑定任何 Campaign（见文件头说明）
RESEARCH_LEVEL_EV = {"R01-MIL-E042"}


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
    existing_tickers = {r[0]: r[1] for r in cur.execute("SELECT ticker, security_id FROM securities WHERE ticker IS NOT NULL")}
    reuse_sec = set()
    for _iid, (sid, ticker, nm, _e) in SEC_CANON.items():
        if sid in existing_sec:
            if existing_sec[sid] != nm:
                raise SystemExit("FAIL 证券助记符冲突: %s 既有=%s 新=%s" % (sid, existing_sec[sid], nm))
            reuse_sec.add(sid)
        if ticker and ticker in existing_tickers and existing_tickers[ticker] != sid:
            raise SystemExit("FAIL ticker 冲突: %s 已被 %s 占用" % (ticker, existing_tickers[ticker]))
    if reuse_sec:
        print("  复用既有证券: %s" % sorted(reuse_sec))

    if not have("research_rules", "rule_id", RULE_ID):
        add("research_rules", RULE_ID,
            "INSERT INTO research_rules (rule_id,name,base_pattern,description,status) VALUES (?,?,?,?,?)",
            (RULE_ID, "国防军工历史周期观察", "国防军工",
             "R01-06（国防军工）历史周期观察窗口：订单 / 事件驱动机制（T01 已确立 TH-DEFENSE 根）。" + PROV, "under_review"))

    # ★ 为每个 campaign_year 建 annual_review（避免重现 AR-CONS-2018 问题）
    for yr in sorted(ANNUAL):
        arid = "AR-MIL-%d" % yr
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
                (c["cid"], "AR-MIL-%d" % c["year"], RULE_ID, c["cycle"], c["year"], c["start"], c["end"], c["peak"],
                 c["strength"], c["result"], c["cls"],
                 "研究候选日期（intake date_candidates）；未经行情核验",
                 "研究候选日期（intake date_candidates）；未经行情核验",
                 c["dc"],
                 "%s［intake R01-MIL-%s］" % (cand_by_k[c["k"]]["title"], c["k"]),
                 c["notes"]))

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
        sid = "S-MIL-%02d" % i
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
    # 入 DB = promoted ∪ research-level；RC-only（未被任何 promote 候选引用且非 research-level）跳过
    rc_only_ev = (rc_ev - promoted_ev) - RESEARCH_LEVEL_EV
    print("  RESEARCH_ONLY 专属 evidence（不入 DB）: %d 条" % len(rc_only_ev))
    print("  research-level evidence（入 DB 但不绑定 Campaign）: %d 条 %s"
          % (len(RESEARCH_LEVEL_EV), sorted(RESEARCH_LEVEL_EV)))

    ev_map = {}
    for i, e in enumerate(pkg["evidence"], start=1):
        if e["evidence_id"] in rc_only_ev:
            continue
        eid = "E-MIL-%02d" % i
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
        if intake_ev in rc_only_ev:
            continue
        if not have("events", "event_id", eid):
            add("events", eid,
                "INSERT INTO events (event_id,date,name,event_type,description,source_id) VALUES (?,?,?,?,?,?)",
                (eid, date, name, etype, "%s｜provenance: %s" % (intake_ev, PROV), src_map[ev_src[intake_ev]]))

    for c in CAMPAIGNS:
        for ieid in cand_by_k[c["k"]]["evidence_ids"]:
            if ieid in RESEARCH_LEVEL_EV:
                continue  # research-level 不绑定 Campaign（见文件头说明）
            eid = ev_map[ieid]
            if not cur.execute("SELECT 1 FROM campaign_evidences WHERE campaign_id=? AND evidence_id=?",
                               (c["cid"], eid)).fetchone():
                add("campaign_evidences", "%s/%s" % (c["cid"], eid),
                    "INSERT INTO campaign_evidences (campaign_id,evidence_id,role) VALUES (?,?,?)",
                    (c["cid"], eid, ev_by_id[ieid]["evidence_role"]))

    rc_event_ids = {eid for eid, _d, _n, _t, ie in EVENTS if ie in rc_only_ev}
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

    # phases（002 的 main_rise 允许 end_date = NULL：结束日期不可考，不制造精确日期）
    ph_n = 0
    for cid, ptype, sdate, edate, desc in PHASES:
        ph_n += 1
        pid = "PH-MIL-%02d" % ph_n
        if not have("campaign_phases", "phase_id", pid):
            add("campaign_phases", pid,
                "INSERT INTO campaign_phases (phase_id,campaign_id,phase_type,start_date,end_date,description)"
                " VALUES (?,?,?,?,?,?)",
                (pid, cid, ptype, sdate, edate, "%s｜%s" % (desc, PROV)))

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
                     "candidate 快照自 R01-06 intake date_candidates；未经行情核验。｜%s" % PROV))

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
