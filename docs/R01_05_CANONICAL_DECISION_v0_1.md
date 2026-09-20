# R01-05 Canonical Decision & Import v0.1 — 金融 / 房地产

> **性质**：R01-05 的 Canonical Decision + DB Import 落地记录。
> **前置**：`docs/R01_05_INTAKE_REVIEW_v0_1.md` + `docs/R01_05_INTAKE_REVIEW_ADDENDUM_v0_1.md`（均 PASS）。
> **正式 Package**：`research/intake/packages/R01-05/`（**v2**，`source_commit 2153f6d`；v1 结论不适用）。
> **边界**：**未修改** schema / Research Model v1.0 / Export Contract v1.0 / CMTR v1 / taxonomy /
> Structural Analogy / Time Observation。**未启动 R01-06。**
> **未回头修改 R01-01 / R01-02 / R01-03 / R01-04**（已用「导入前备份 vs 导入后」逐表集合比对验证，见 §11）。

---

## 1. 12 个 Candidate 最终状态

| # | intake | 年份 | 最终处置 | canonical_id / 说明 |
|---|---|---:|---|---|
| 1 | `001` 地产融资「三支箭」+ 保交楼 | 2022 | **PROMOTE** | `C-2022-RE-POLICY-THREE` |
| 2 | **`002` 2024-05-17「5·17」地产新政** | 2024 | **RESEARCH_ONLY** | `RC-2024-RE-POLICY-517`（**市场层强反向证伪**） |
| 3 | **`003` 2018–2019 地产边际放松** | 2019 | **RESEARCH_ONLY** | `RC-2019-RE-EASING`（INSUFFICIENT + 市场层证伪） |
| 4 | `004` 房企债务风险暴露（**下行结构**） | 2020 | **PROMOTE**（`result = weak`） | `C-2020-RE-DEBT-RISK` |
| 5 | `005` 2024-09 政策组合拳 / 券商·非银 | 2024 | **PROMOTE**（`dc = low`） | `C-2024-FIN-BROKER-POLICY` |
| 6 | `006` 2023-04/05「中特估」银行·保险 | 2023 | **PROMOTE**（`dc = low`） | `C-2023-FIN-SOE-VALUATION` |
| 7 | `007` 2023–2025 银行高股息 | 2024 | **PROMOTE**（`dc = low`；**peak/end = NULL**） | `C-2024-FIN-BANK-DIVIDEND` |
| 8 | `008` 2020-11—2021-03 银行顺周期 | 2020 | **PROMOTE**（`dc = low`） | `C-2020-FIN-BANK-CREDIT` |
| 9 | **`009` 2020-06/07 券商** | 2020 | **RESEARCH_ONLY** | `RC-2020-FIN-BROKER-VOLUME`（**无 lifecycle → Q4 不成立**） |
| 10 | `010` 2025 保险 | 2025 | **PROMOTE**（`dc = low`；**peak/end = NULL**） | `C-2025-FIN-INSURANCE` |
| 11 | **`011` 2015–2017 棚改去库存** | 2016 | **RESEARCH_ONLY** | `RC-2016-RE-SHANTY`（Priority B；市场响应层空白） |
| 12 | **`012` 2015 杠杆牛金融股** | 2015 | **RESEARCH_ONLY** | `RC-2015-FIN-LEVERAGE`（`PIT = 0`；纯 Beta） |

**7 PROMOTE · 5 RESEARCH_ONLY** · 无 `MERGE` · 无 `EXCLUDE` · **无候选级拆分**。

> `002 / 003 / 009 / 011 / 012` 全部为 **RESEARCH_ONLY**，且**每一条都有独立的、可复核的否决理由**
> （不是"证据少"这一笼统理由）—— 详见 §4。

---

## 2. 13 条 Conflict 的逐项裁决

| conflict | 原状态 | **本轮裁决** |
|---|---|---|
| **`CF013`** 股息口径差（P0） | UNRESOLVED | **保留 UNRESOLVED —— 转为「结论约束」而非「数据修正」**。个股**前复权（含股息再投）** vs 沪深300 **价格指数（不含股息）**；按银行股息率约 5%/年估算，3 年窗口口径差约 **+15pct**，**银行类候选超额被系统性高估**。→ **所有引用沪深300 相对基准的金融 Campaign 的 `research_notes` 均写入统一 caveat**：**不得把相对收益直接解释为行业 Alpha**；**未做 Beta 调整、未剥离风格因子**；**Beta 中性验证未完成**。**原始 Evidence（E130–E141）与原始区间收益保持不变，未伪造任何调整后收益**（详见 §3） |
| **`CF001`** 三支箭：独立 Campaign vs 大周期反弹（P0） | UNRESOLVED | **裁决：判为独立 Campaign**。Q1 注意力中心与 004 **方向相反**（融资供给端转向 vs 融资收紧）；Q3 持续；**Q4 独立生命周期**（2022-11-08→11-29 脉冲，与 004 的 2020-08→2022-07 下行段**不重叠**）；Q5 双向成立；**独立启动锚点**（2022-11-08 第二支箭，一手）。★ **Q2 代表标的不成立**（与 004 完全重叠）→ 由「**同一批资产在两轮方向相反的政策周期中重演**」解释，同属 Theme Cycle `realestate_policy_cycle_2020_2023`（**Sequential**） |
| **`CF003`** 2024-09 券商：行业结构 vs 全市场 Beta（P0） | UNRESOLVED | **保留 UNRESOLVED —— 未因代表股跑赢就排除 Beta**。P2 极强：2024-10-08 成交额 **3.5 万亿元创历史新高**（全市场级流动性/风险偏好）。★ **东方财富相对幅度 +102.1pct 本身即「成交量 Beta 代理」信号，不是行业 Alpha 信号**。→ 独立 Campaign 的判据**不基于相对强度**，而基于①独立一手政策锚点 ②可测 A 股响应 ③`classification = mixed`；并**降级**：生命周期仅 11 个交易日 → `date_confidence = low`、`strength = medium`（**未升 strong**） |
| **`CF004`** 银行上涨：行业重估 vs 红利风格因子（P0） | UNRESOLVED | **保留 UNRESOLVED —— 未把「银行上涨」本身当作独立机制**。P2（红利/低估值/防御风格因子抱团，银行 Alpha 与红利因子**是否可分未做验证**）完整保留在 006/007 notes。→ 006 与 007 **判为两个独立 Campaign**（同属 `bank_valuation_2023_2025`，**Parallel**）：006 = 「中特估」**叙事**驱动、007 = **资金配置**驱动 |
| **`CF007`** 地产下行结构是否进入 canonical（P0） | UNRESOLVED | **裁决：允许进入 Canonical Campaign**。沿用既有先例：R01-01 `C-2018-HIEQ-ROBOT-DOWN`、R01-03 `C-2022-SEMI-DOWNTURN` 均已进入 canonical。**现有 Independence Gate 是结构独立性判据，不排除负向产业结构**。★ `result = weak` **语义 = 市场/行业方向为负，不表示证据质量弱**（本 Campaign 8 ev / 8 IG，质量同级）。★ **命名中性化**：`C-2020-RE-DEBT-RISK`（**不使用带方向判断的措辞**） |
| **`CF005`** 中特估：银行与保险是否拆分（P1） | UNRESOLVED | **裁决：判为一个 Campaign，保留 Conflict**。Q1 注意力中心 = 「中国特色估值体系」（**横跨银行/保险/低估值央国企的统一叙事**）✓；Q4 银行与保险**同一窗口同步** ✓。**未机械合并** —— 本 Campaign 与 007 机制不同、**分属不同 Theme Cycle** |
| **`CF006`** 房地产与金融是否同一 Theme Cycle（P1） | UNRESOLVED | **保留 UNRESOLVED**。地产 → 银行风险传导（`Q005`）仅作**机制联系**保留（制度联结：房地产贷款集中度管理制度），**未合并任何 Campaign**、**未新增 Cycle** |
| **`CF008`** 2020-07 券商：改革驱动 vs 成交量驱动（P1） | UNRESOLVED | **保留 UNRESOLVED**，并**作为 009 不 Promote 的核心理由之一**：核心反证就在证据本身（E081「银行、保险、互联网金融等大金融**全线走高**」= 典型市场 Beta 形态） |
| **`CF011`** 三支箭窗口内两龙头方向相反（P1） | UNRESOLVED | **保留 UNRESOLVED**。保利发展 **-3.3pct** vs 万科A **+18.7pct** → **「地产板块」是否上涨无法判定**。★ 本包明确**不允许取平均充当板块表现** → 001 的 `strength` **定为 medium（不升 strong）** |
| **`CF012`** 2025 保险：板块叙事 vs 代表标的跑输（P1） | UNRESOLVED | **保留 UNRESOLVED —— 未消解**。P1 板块年度叙事（保险指数涨超 30%）；P2 登记代表标的**中国平安相对 -5.8pct** → **代表标的与板块叙事方向冲突**，本轮**无法判定板块内部是否显著分化**（`Q012`）。写入 010 notes |
| `CF002` 2024-05-17 是否构成周期反转起点（P2） | UNRESOLVED | **保留**。作为 002 不 Promote 的**直接依据**：单日脉冲、4 个月内全部回吐（**市场层证伪**） |
| `CF009` 2018–2019 地方放松是否代表中央政策转向（P2） | KEEP_BOTH | **保留 KEEP_BOTH**（影响启动锚点认定）。写入 001 与 003 的 notes |
| `CF010` 2015–2016 去库存：政策基本面 vs 杠杆牛 Beta（P2） | UNRESOLVED | **保留**。作为 011 不 Promote 的依据之一 |

> **13 条全部处理：4 条给出明确裁决（`CF001` / `CF007` / `CF005` / `CF013` 的处理方式），9 条明确保留。**
> **未为「解决 Conflict」而强行得出确定结论。**
> **P0 五项（CF013 / CF001 / CF003 / CF004 / CF007）全部先行裁决，再进入 DB Import。**

---

## 3. `CF013` 口径差的处理（本轮最关键的一项）

**问题**：intake 的一级行情证据（E130–E141）以「**个股前复权（含股息再投）**」对比「**沪深300 价格指数（不含股息）**」。
对高股息行业（银行）而言，**股息部分被计入个股收益但未计入基准** → 相对超额被**系统性高估**。

**本轮的三个处理原则**：

1. **不修改任何原始数据。** E130–E141 的数值、区间、口径**全部保持不变**；
   数据库中的 `evidences` 记录、`campaign_date_observations` 的 `candidate_date` 均**未做任何"调整后"改写**。
2. **不伪造调整后收益。** **没有**任何地方出现"剥离股息后的相对收益""Beta 调整后超额"这类**未被证据支撑**的数字。
3. **把口径差转化为「结论约束」。** 在**全部 7 个**引用沪深300 相对基准的金融 Campaign 的 `research_notes` 中写入**统一 caveat**（常量 `CF013`，见 `research/scripts/import_r01_05_canonical_v0_1.py`）：
   - 明确标注口径为「**个股前复权（含股息再投）vs 沪深300 价格指数（不含股息）**」；
   - 明确 3 年窗口口径差约 **+15pct**、**银行类候选超额被系统性高估**；
   - 明确「**不得把该相对收益直接解释为行业 Alpha**」；
   - 明确「**未做 Beta 调整、未剥离风格因子，Beta 中性验证未完成**」；
   - 给出**后续解决路径**：以**中证红利全收益指数 / 银行行业指数（全收益）**重算（`Q013`）。

**在 Export 层的落地**：
- `rule_fin_realestate` 的 `observation_window` 中写入「★ CF013 口径差 **UNRESOLVED**」；
- 相关 Campaign 的 `market_data` 状态为 `unavailable`（本地无金融/地产行情序列），`note` 中再次指向 CF013；
- 因此 **CF013 未被"升级为 Alpha"**，也**未被静默删除**。

> **结论**：CF013 保持 **UNRESOLVED**，但其影响被**显式约束**在「幅度解释」层面；
> **任何基于本批数据得出的"银行/保险跑赢 = 行业 Alpha"结论都是不成立的**。

---

## 4. 5 个 RESEARCH_ONLY 的独立否决理由

| intake | canonical | **否决理由（每一条独立成立）** |
|---|---|---|
| `002` 5·17 新政 | `RC-2024-RE-POLICY-517` | **市场层强反向证伪**：2024-05-17 当日保利 +10.66%、万科 +10.02%，但至 2024-09-13 保利 **-31.3%**、万科 **-29.8%**（相对 **-17.2pct / -15.7pct**），同期工商银行相对 **+22.8pct**。→ **政策的市场反应是单日脉冲，4 个月内全部回吐**。本候选价值已明确定位为「**市场层证伪的教（样本）**」 |
| `003` 2018–2019 地产 | `RC-2019-RE-EASING` | ① `INSUFFICIENT` / `low`；② **市场层证伪** —— 保利相对 **-18.2pct**、万科 **-0.4pct**，**两龙头均未跑赢基准**（E130），而同期中信证券 **+52.3%**；③ 同期卖方明确认为地方放松**不代表中央政策转向**；④ `exclusion X012` 已记录 `NOT_A_CAMPAIGN` |
| `009` 2020-06/07 券商 | `RC-2020-FIN-BROKER-VOLUME` | **Gate 不成立**：① **`lifecycle` = `UNKNOWN`（无任何阶段）→ Q4 独立生命周期不成立**；② `start` 为 low 且包内自述「**不确认为真正起点**」，`peak`/`end` 为 PHASE_WINDOW 且无具体日期 → **Q3 持续性不成立**；③ **Q5 残差检验不成立**（E081 明写「大金融全线走高」= 市场 Beta 形态）；④ `CF008` 保留。★ **相对强度（+21.6pct）不作为 Promote 依据** |
| `011` 2015–2017 棚改去库存 | `RC-2016-RE-SHANTY` | ① `INSUFFICIENT` / `low`；② **仅 2 ev / 2 IG**；③ **市场响应层完全空白** —— 2015—2016 前复权序列存在**复权因子异常**（保利发展 2016-12-30 = 4.7254 与 2017-12-29 = 10.0604 隐含复权因子相差约 57%，无法用分红解释）→ Worker **不采用量化证据** → 三层链条第三层缺失；④ 同期处于 2015 杠杆牛/股灾极端 Beta 环境。★ **未因存在政策 / 历史叙述而提升状态** ✓ |
| `012` 2015 杠杆牛金融股 | `RC-2015-FIN-LEVERAGE` | ① `INSUFFICIENT` / `low`；② **仅 2 ev / 2 IG**；③ **`PIT = 0`** —— 全部为 retrospective 复盘，**无一条同期证据**；④ **无任何行情数据**；⑤ 机制本身即「杠杆资金驱动的市场 Beta」，按 `historical_campaign_validation_v1.md §4.3`，**无法排除 Beta 污染时必须保持低置信度**。★ `exclusion X001` 已建议**不作为独立金融 Campaign** |

---

## 5. 新增 7 个 Canonical Campaign

| canonical_id | 年 | start | peak | end | class | strength | result | dc | Theme Cycle |
|---|---:|---|---|---|---|---|---|---|---|
| `C-2022-RE-POLICY-THREE` | 2022 | 2022-11-08 | 2022-11-29 | 2023-02-28 | `event_driven` | medium | positive | **medium** | `realestate_policy_cycle_2020_2023` |
| `C-2020-RE-DEBT-RISK` | 2020 | 2020-08-20 | 2021-12-03 | 2022-07-31 | `industry_trend` | medium | **weak** | medium | `realestate_policy_cycle_2020_2023` |
| `C-2024-FIN-BROKER-POLICY` | 2024 | 2024-09-24 | 2024-10-08 | 2024-10-31 | `mixed` | medium | positive | **low** | `broker_risk_appetite_2024` |
| `C-2023-FIN-SOE-VALUATION` | 2023 | 2023-04-01 | 2023-05-11 | 2023-06-30 | `theme_campaign` | medium | positive | **low** | `bank_valuation_2023_2025` |
| `C-2024-FIN-BANK-DIVIDEND` | 2024 | 2024-01-01 | **NULL** | **NULL** | `industry_trend` | medium | positive | **low** | `bank_valuation_2023_2025` |
| `C-2020-FIN-BANK-CREDIT` | 2020 | 2020-10-30 | 2021-03-03 | 2021-03-31 | `industry_trend` | medium | positive | **low** | `bank_credit_cycle_2020_2021` |
| `C-2025-FIN-INSURANCE` | 2025 | 2025-01-01 | **NULL** | **NULL** | `industry_trend` | medium | positive | **low** | `insurance_asset_liability_2025` |

**关键点**：
- **7 个 Campaign 全部 `strength = medium`**（**无一个升 strong**）—— 与 §3 的 CF013 约束、以及各候选的已知弱点一致；
- **`peak_date` / `end_date` 为 NULL 的有 2 个**（007 / 010）：**不制造完整日线生命周期**、**不把观察窗口结束当作 Peak/End**；
- **`date_confidence` 仅 001 / 004 为 `medium`**，其余 **5 个为 `low`**（无启动锚点 / 生命周期未闭合）；
- **`result = weak` 仅 004 一个**，语义为**方向为负**（非证据质量弱）。

---

## 6. Theme Cycle（新增 5 个）

| Theme Cycle | Campaigns | Pattern |
|---|---|---|
| `realestate_policy_cycle_2020_2023` | `C-2020-RE-DEBT-RISK`（下行）→ `C-2022-RE-POLICY-THREE`（政策修复） | **Sequential** |
| `bank_valuation_2023_2025` | `C-2023-FIN-SOE-VALUATION` / `C-2024-FIN-BANK-DIVIDEND` | **Parallel**（同属银行/估值重估，但机制不同） |
| `broker_risk_appetite_2024` | `C-2024-FIN-BROKER-POLICY` | 单一 |
| `bank_credit_cycle_2020_2021` | `C-2020-FIN-BANK-CREDIT` | 单一（**与 `bank_valuation_2023_2025` 分属不同 Cycle** —— 机制相反） |
| `insurance_asset_liability_2025` | `C-2025-FIN-INSURANCE` | 单一 |

> **`bank_valuation_2023_2025` 与 `bank_credit_cycle_2020_2021` 刻意分开**：前者 = **资金配置驱动**（低利率 + 资产荒 + 高股息），
> 后者 = **信用周期驱动**（经济复苏 + 信用成本改善）。**未因同属"银行"而合并**。
> 行情支持该区分：2020-11~2021-03 银行跑赢时券商跑输 **-24.9pct**。

---

## 7. 金融内部「不机械合并」与地产内部「不机械合并」

| 边界 | 裁决 | 依据 |
|---|---|---|
| **006 中特估（银行+保险）** vs **007 银行高股息** | **拆为两个 Campaign** | Q1 注意力中心不同（「中特估」叙事 vs 资金配置）；机制不同；**分属同一 Cycle 但不同 Campaign** |
| **005 券商 2024-09** vs **009 券商 2020-07** | **未合并**（005 Promote / 009 Research Only） | **分属不同 Theme Cycle**；005 有 lifecycle + 一手政策锚点，009 两者皆无 |
| **007 银行高股息** vs **008 银行顺周期** | **拆为两个 Campaign，且分属不同 Theme Cycle** | **机制相反**（资金配置 vs 信用扩张）；行情支持（2020-11~2021-03 银行跑赢时券商跑输 -24.9pct） |
| **001 三支箭** vs **004 地产债务风险** | **拆为两个 Campaign，同一 Cycle（Sequential）** | **方向相反**（政策修复 vs 风险暴露）；独立生命周期不重叠；Q2 标的完全重叠由 Sequential 解释 |
| **地产 → 银行风险传导** | **仅作机制联系保留，未合并** | `CF006` 保留 UNRESOLVED；`Q005` 未升级为独立机制轴 |

> **原则**：**同一子行业 ≠ 同一 Campaign**；**同一叙事 ≠ 同一机制**。所有合并/拆分均由 Q1–Q5 支持，**未按行业名称机械处理**。

---

## 8. Shared Evidence 处理（1 evidence : 1 campaign）

`validate_batch_research` 强制 **1 evidence : 1 campaign**。本轮共享证据归属如下：

| evidence | 被哪些候选引用 | **唯一归属** | 理由 |
|---|---|---|---|
| `E141`（沪深300 基准） | 被 10 个候选共享 | **不绑定任何 Campaign**（`evidence_role = context`） | **全局基准**，保留在研究层；context 孤儿不触发 `validate_db` 告警 |
| `E132` | 004 / 008 | → **008** | 008 的核心证据 |
| `E137` | 007 / 010 | → **010** | 010 的代表标的证据 |
| `E140` | 006 / 007 | → **006** | 006 的核心证据 |

> **未为了消除共享而强行合并 Campaign**；**未把全局基准硬挂到某个 Campaign**。
> 相关归属在 `research/scripts/import_r01_05_canonical_v0_1.py` 中以 `EVIDENCE_OWNER` / `GLOBAL_BENCHMARK_EV` 显式登记。

---

## 9. Market Evidence 口径（跨任务一致性）

- **「市场关注必须有 A 股侧证据」** —— 该原则自 R01-03 起作为**决策因子**使用，**本轮继续使用**；
- **本轮再次确认：该原则未写入 Protocol、未回溯修改 R01-01 / R01-02**；
- 本轮所有 7 个 Campaign 均有 A 股侧证据（E130–E141 一级行情 / 行业指数 / 媒体），
  且**均显式标注口径与局限**（CF003 Beta / CF004 风格因子 / CF013 口径差 / CF012 代表标的冲突）；
- **相对强度一律不作为 Promote 的唯一依据**（009 即为例证：+21.6pct 但 Q4/Q5 不成立）。

---

## 10. `008` 的特别处理

`008`（`C-2020-FIN-BANK-CREDIT`）是**根据正式 Gate 判为独立 Campaign**（**不基于相对强度**）：

- Q1 独立注意力中心 =「**经济复苏 + 信用成本改善**」（**信用周期驱动**），与 007「低利率 + 资产荒 + 高股息」（**资金配置驱动**）**机制相反** ✓；
- Q2 代表标的（招商银行 / 工商银行）与 007 部分重叠 → 由「**同一子行业的不同机制周期**」解释；
- Q3 / Q4 / Q5 均成立。

**如实记录的降级项**（**未美化**）：
① 仅 **4 ev / 4 IG**（门槛下限）；② **仅 1 条同期市场证据**（E070，2021-03-03）；
③ **无可靠启动 / 结束锚点**（start/end 均为 PHASE_WINDOW，`dc = low`）；
④ **单一代表标的**（工商银行）—— **缺行业指数广度与多标的验证**；
→ `strength = medium`、`date_confidence = low`；**建议后续补证**。

---

## 11. DB / Export 变化

### 11.1 DB（`research/database/cycle_research.db`）

逐表集合比对（导入前备份 vs 导入后，`set` 差集）：

| table | before | after | Δ | 说明 |
|---|---:|---:|---:|---|
| `themes` | 52 | 52 | **+0** | **taxonomy 未变** |
| `research_rules` | 8 | 9 | +1 | `rule_fin_realestate` |
| `annual_reviews` | 51 | 56 | +5 | `AR-FINRE-2020/2022/2023/2024/2025` |
| `campaigns` | 43 | 50 | +7 | 见 §5 |
| `sources` | 285 | 345 | +60 | |
| `evidences` | 287 | 331 | +44 | 63 intake evidence − 19 RC-only |
| `events` | 111 | 123 | +12 | 15 定义 − 3 RC-only |
| `securities` | 143 | 158 | +15 | 全部新建（无 mnemonic / ticker 冲突） |
| `campaign_themes` | 89 | 103 | +14 | |
| `campaign_evidences` | 269 | 309 | +40 | |
| `campaign_events` | 104 | 116 | +12 | |
| `campaign_securities` | 161 | 185 | +24 | |
| `campaign_phases` | 99 | 108 | +9 | |
| `campaign_date_observations` | 109 | 126 | +17 | |

- **全部差异均为 `+N / −0`（纯新增）**，**无任何既有行被修改或删除**；
- `themes` / `market_series` / `market_daily` / `trading_calendar` **完全未变**（taxonomy 与行情库零改动）；
- **每个 `campaign_year` 均有 `annual_review`**（**未重现 R01-04 的 `AR-CONS-2018` 问题**，已逐条 JOIN 验证 7/7 OK）。

### 11.2 Export（`exports/timeline_export_v1.json`，Contract v1.0 不变）

| 数组 | before | after | Δ |
|---|---:|---:|---:|
| `rules` | 8 | 9 | +1 |
| `campaigns` | 43 | 50 | +7 |
| `research_candidates` | 17 | 22 | +5 |
| `events` | 118 | 130 | +12 |
| `signals` | 22 | 22 | **+0** |
| `securities` | 207 | 241 | +34 |

- 顶层结构（`contract` / `timeline_export_version` / `project`）**完全一致**；仅 `generated_at` / `source_commit` 例行更新；
- **既有 43 个 Campaign 逐条深比对：0 修改 / 0 删除**（`added=7, removed=0, modified=0`）；
- `research_candidates`：`added=5, removed=0, modified=0`；既有 17 个 RC 未动；
- **`conflicts.json` 的 `conflicts` 数组逐字节一致**（仅 `generated_at` / `source_commit` 变化）；
- **manifest 的既有 43 Campaign 逐条深比对：0 修改**。

### 11.3 本轮修复的一处 Export 生成端缺陷（跨 Rule 污染）

`build_2018()`（汽车 Rule 的 2018 反例年份）原本以 `date LIKE '2018%'` 吸收「未绑定任何 Campaign 的 2018 证据」。
R01-05 引入了**未被任何候选引用的孤儿证据** `E-FINRE-51`（**2018-04-27 资管新规**，`context`），
导致其被**误并入汽车反例年份**的 `evidence_ids`。

**修复**：将过滤条件限定为 `evidence_id LIKE 'E-2018-%'`（与同一行的 `source_ids` 使用 `S-2018-%` **同构**）。
**对既有各 Rule 数据行为完全一致**（既有 unbound 2018 证据仅 `E-2018-01..04`，修复后 `Y2018-NO-CLEAR.evidence_ids` 与导入前**逐元素相同**）。
**性质**：Export **生成脚本**的缺陷修复，**未修改 Export Contract、未修改任何已导出的既有 Campaign 数据**。

> 同类修复在更早的 Wave 已做过一次（`year == 2018` 的 Campaign 跳过逻辑加上 `rule_id == AUTO_RULE` 限定）。
> 本轮为**同一类跨 Rule 污染**在 `evidence_ids` 上的残留。

---

## 12. 全部验证结果 → **全部 PASS**

| 检查 | 结果 |
|---|---|
| `validate_db.py` | **PASS**（3 条警告 —— 均为 R01-02 **已记录为 unresolved** 的 `E-SEMI-29/47/48` temporal 标注，**非本轮引入**） |
| `validate_timeline_export.py`（Contract v1.0） | **PASS**（0 警告；50 campaigns / 22 RC / 130 events / 241 securities） |
| `validate_batch_research.py` | **PASS**（0 警告；51 条目；`{PROVISIONAL: 50, CONFLICT: 1}`） |
| `validate_promotion_manifest.py` | **PASS** |
| `check_doc_schema_consistency.py` | **PASS**（0 FAIL；Contract 17 表 / 125 字段 / Schema-only 字段 0） |
| `validate_current_research.py` | **PASS**（5 通过 / 0 警告 / 0 失败） |
| `validate_monorepo_integrity.py` | **PASS**（25 项通过 / 0 警告） |
| `refresh_current_research.py --check` | **PASS** |
| `validate_historical_research_intake.py --check` | **PASS**（25 checks，FAIL 0，WARN 0） |
| Intake Validator × 5（R01-01 ~ R01-05） | **PASS**（每个 `checks: 25  FAIL: 0  WARN: 0`，含 **C25 Strict Draft-07**） |
| Intake Validator 单元测试 | **PASS**（**44 tests, 0 failed**） |
| 幂等性（import `--verify`） | **PASS**（`计划写入 0 行`） |
| Export 幂等性 / 深比对 | **PASS**（既有 43 Campaign 0 修改） |

---

## 13. 尚未解决的问题（明确保留）

| # | 问题 | 状态 |
|---|---|---|
| 1 | **`CF013` 股息口径差** | **UNRESOLVED**（已转为结论约束；**未伪造调整后收益**；需以全收益指数重算） |
| 2 | `CF001` 的 **Q2 代表标的重叠** | 由 Sequential 解释，**未消解** |
| 3 | `CF003` 券商 **全市场 Beta 不可分离** | **UNRESOLVED** |
| 4 | `CF004` 银行 **红利风格因子不可分离** | **UNRESOLVED** |
| 5 | `CF005` 中特估 **银行/保险边界** | **UNRESOLVED**（已判为一个 Campaign） |
| 6 | `CF006` **房地产 vs 金融 Theme Cycle 归属** | **UNRESOLVED** |
| 7 | `CF008` 2020-07 券商 **驱动归属** | **UNRESOLVED** |
| 8 | `CF009` **地方放松是否代表中央转向** | **KEEP_BOTH** |
| 9 | `CF011` 三支箭 **两龙头方向相反** | **UNRESOLVED**（不允许取平均） |
| 10 | `CF012` 2025 保险 **代表标的 vs 板块叙事** | **UNRESOLVED** |
| 11 | `006` / `007` / `010` **生命周期未闭合** | `peak/end = NULL` 或推断值；`dc = low` |
| 12 | **`008` 证据广度不足**（4 ev / 4 IG、单一标的） | 已如实记录，**建议后续补证** |
| 13 | **本地无金融/地产行情序列** | Export `market_data = unavailable`；相对表现仅引自 intake 一级行情证据 |
| 14 | `E-SEMI-29/47/48` temporal 标注（**R01-02 遗留**） | 保留现状（非本轮引入） |
| 15 | 孤儿证据 `E-FINRE-49/50/51/63`（intake 中未被任何候选引用） | **按既有惯例导入**（R01-01 有 2 条、R01-04 有 9 条同类孤儿）；`E-FINRE-63` = E141 全局基准 |

---

## 14. 本轮严格未做

- ❌ 未修改 **Schema** / **Research Model v1.0** / **Export Contract v1.0** / **CMTR v1** / **taxonomy**；
- ❌ 未修改 `themes`（52 → 52）、`market_series` / `market_daily` / `trading_calendar`（零改动）；
- ❌ 未修改 **Structural Analogy** / **Time Observation**；
- ❌ 未回头修改 **R01-01 / R01-02 / R01-03 / R01-04** 的任何 Campaign、Evidence、Source 或 Export 数据；
- ❌ 未修改任何 **Intake Package**（R01-01 ~ R01-05 的 11 文件与 checksums 均未动）；
- ❌ 未启动 **R01-06**、未开始下一项 Canonicalization；
- ❌ 未把任何 Conflict 强行"解决"为确定结论；
- ❌ 未伪造任何调整后收益、未用"板块平均"代替两个方向相反的龙头。

---

## 15. 交付物

| 文件 | 说明 |
|---|---|
| `research/scripts/import_r01_05_canonical_v0_1.py` | 本轮 Canonical Import 脚本（幂等；`--dry-run` / `--verify`） |
| `research/scripts/batch_auto_research.py` | 扩展 R01-05 的 `FINRE_RULE` / THEME_CYCLE / LIFECYCLE / DRIVERS / RULE_META / PROXY_NOTE / scope；修复 `build_2018()` 跨 Rule 污染 |
| `research/database/cycle_research.db` | 新增 7 Campaign 及其关系（**纯新增**） |
| `exports/timeline_export_v1.json` | Contract v1.0（**纯新增**） |
| `research/research/batch/auto_2018_2025_batch_manifest.json` | 44 → 51 条目 |
| `research/research/batch/conflicts.json` | `conflicts` 数组未变 |
| `docs/R01_05_CANONICAL_DECISION_v0_1.md` | 本文件 |
| `docs/PROJECT_STATE.md` | 同步更新 |
