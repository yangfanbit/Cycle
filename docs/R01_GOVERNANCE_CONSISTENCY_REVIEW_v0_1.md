# R01 Governance / Consistency Review v0.1

> **性质**：**Audit / Consistency Review / Governance Recommendation**。
> **本轮不修改任何业务数据**：未改 Campaign / research data / Schema / Protocol / Research Model v1.0 /
> Validator / taxonomy，未刷新 Structural Analogy（SA）与 Time Observation（TO），未启动新 Research Task，未引入新 Candidate。
> **唯一交付物**：本报告 + `docs/PROJECT_STATE.md` 同步。
> **基线**：HEAD `5c288c0` · a/b `0/0` · worktree clean。
> **审计对象**：R01-01 ~ R01-06 六个任务在 `Research → Intake → Canonicalization → DB → Export` 各层的口径一致性。
> **实测基线**：52 Canonical Campaign · 27 Research Candidate · 11 Macro Theme root（**11/11 均有 Campaign**）·
> 10 rules · 58 annual_reviews · 382 sources · 354 evidences · 171 securities · 39 Theme Cycle。

---

## 0. 执行摘要

| 结论 | 内容 |
|---|---|
| **一致性总体** | **结构层高度一致**（DB↔Export 0 字段不一致；1:1 evidence attribution **零违规**；rule/campaign_year/annual_review **零缺失**；taxonomy 未被任何 R01 修改）。 |
| **主要漂移** | 集中在 **4 个判据层**：① Market Attention / 市场侧证据 ② `research_report` Tier ③ Beta / Relative Return ④ Peak / End 与 `result=weak` 语义。 |
| **漂移方向** | **时间越晚的 Wave 越严格**（pre-R01 最松 → R01-05/06 最严）。属**标准演进**，非随机差异。 |
| **分级结果** | **G0（必须修复）= 0**；**G1（应统一）= 5**；**G2（建议统一）= 6**；**G3（可保持差异）= 4**。 |
| **是否有机械性错误** | **未发现**。既有 3 条 DB warning 均为「总结类证据的 temporal 标注」问题，**非数据错误**。 |
| **SA / TO 前置条件** | **4 项必须在刷新前处理**（G1-1 / G1-2 / G1-3 / G1-5）；**7 项可带 caveat 进入刷新**。 |

---

# A. R01 全局一致性矩阵

## A.1 任务层横向矩阵

| 维度 | pre-R01（基线） | R01-01 高端装备 | R01-02 半导体 | R01-03 资源 | R01-04 消费 | R01-05 金融地产 | R01-06 军工 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **rule_id** | 4 个 | `rule_high_end_equipment` | `rule_semiconductor` | `rule_resources` | `rule_consumer` | `rule_fin_realestate` | `rule_defense_military` |
| intake candidates | — | 7 | 12 | 11 | 13 | 12 | 7 |
| **canonical campaigns** | 13 | **5** | **8** | **6** | **11** | **7** | **2** |
| **research_only** | 4 | 2 | 4 | 5 | 2 | 5 | 5 |
| **promote 率** | — | 71% | 67% | 55% | **85%** | 58% | **29%** |
| **Gate Q1–Q5 明确记录** | ❌ 无 | ⚠️ 部分 | ⚠️ 部分 | ✅ 是 | ✅ 是 | ✅ 是 | ✅ 是 |
| **市场侧证据门槛** | ❌ 无 | ❌ 无 | ⚠️ 部分 | ✅ **明确采用更严** | ⚠️ 参考未固化 | ✅ **非常严格** | ✅ 严格 |
| **Beta / 相对收益 caveat 覆盖率** | **0/13** | 1/5 | 1/8 | 1/6 | 1/11 | **7/7** | **2/2** |
| **research_report 声明数** | — | 8 | 2 | 2 | 2 | 10 | **0** |
| **研报类 evidence 数** | — | 3 | 0 | 0 | 1 | 0 | **16** |
| **研报实际 source_type/tier** | — | `research_report`/T2 | `research_report`/T2 | `research_report`/T2 | `research_report`/T2 | `research_report`/T2 | **`media_tier3`/T3** |
| **peak = NULL** | 0 | 0 | 0 | 1 | 0 | 2 | 1 |
| **end = NULL** | 0 | 1 | 1 | 1 | 1 | 2 | 0 |
| **result = weak** | 1（legacy） | 1 | 1 | 0 | 0 | 1 | 0 |
| **孤儿 evidence（DB）** | 7 | 2 | 0 | 0 | **9** | 4 | 3 |
| **孤儿 source（DB）** | 7 | 5 | 11 | **18** | 5 | **22** | 16 |
| **Theme Cycle 数** | 14 | 3 | 4 | 5 | 7 | 5 | 2 |
| **campaign_year ⊇ annual_review** | ✅ | ✅ | ✅ | ✅ | ✅（R01-04 曾缺失→已修） | ✅ | ✅ |
| **C01–C25 / C25 Draft-07** | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## A.2 DB ↔ Export 一致性（实测）

| 检查 | 结果 |
|---|---|
| DB campaigns 52 ↔ Export campaigns 52 | **完全一致**（DB-only 0 / Export-only 0） |
| 7 个关键字段逐条比对（start/peak/end/strength/result/classification/year） | **0 处不一致** ✅ |
| 无归属 securities | **0** ✅ |
| 无归属 events | 7（全局/legacy 事件，设计如此） |
| **共享 evidence（一条绑多个 Campaign）** | **0** ✅ —— 1:1 attribution **全库零违规** |
| `campaign_themes` 引用不存在的 theme | **0** ✅ |

## A.3 结构层「已高度一致」的项（无需治理）

- **1:1 evidence attribution**：52 Campaign / 329 `campaign_evidences`，**零共享**。R01-05 的 `E141/E132/E137/E140` 与 R01-06 的 `E042` 均已被正确处理（归属或不绑定）。
- **rule ↔ campaign_year ↔ annual_review**：6 个新 rule 的**每个** `campaign_year` 均有 `annual_review`（R01-04 暴露的 `AR-CONS-2018` 问题已修复并成为固定检查项）。
- **taxonomy 未被修改**：`themes` 始终 52 行；六个 R01 均未新增 root / 子主题 / alias。
- **canonical ID 泄漏**：全库 0（C13 检查持续生效）。
- **无数量 KPI**：6 个 intake 包 `no_quantity_kpi_acknowledged = true`；C22 持续生效。
- **Campaign 命名**：`C-{year}-{FAMILY}-{DESCRIPTOR}` 六任务一致（仅 pre-R01 的 `C-2019-AD`/`C-2022-POLICY` 为历史风格）。

---

# B. Governance Issue List（分级）

| ID | 级别 | 问题 | 一句话 |
|---|---|---|---|
| **G1-1** | **G1 应统一** | **Market Attention / 市场侧证据门槛** | 应固化为**统一 Canonical Gate 的「软门槛」**（影响 strength / date_confidence），而非「可 Promote 与否」的硬门槛；**不回溯**。 |
| **G1-2** | **G1 应统一** | **`research_report` Tier 口径** | Validator C08 `research_report→(2,)` **应向 Research Model v1.0 §15（Tier 3）对齐**，改为 `(2,3)` 兼容区间；**需一次性 migration**。 |
| **G1-3** | **G1 应统一** | **Beta / Relative Return 表达规范** | 建立 **Level 0–3** 分级并强制写入 caveat；实测**全库无一例达到 Level 2/3**。 |
| **G1-4** | **G1 应统一** | **Validator 缺 orphan 检查** | C01–C25 **无孤儿检查**，导致 84 孤儿 source / 25 孤儿 evidence 未被机器发现。 |
| **G1-5** | **G1 应统一** | **`result=weak` 语义与 `strength=weak` 残留** | `weak` 应**只在 `result`**；`strength=weak`（legacy `C-2019-AD`）应统一。 |
| **G2-1** | G2 建议 | **Peak / End 口径规范** | 建立「canonical / alternative / WINDOW / NULL」四态决策树；保留「商品 peak ≠ A 股 peak」。 |
| **G2-2** | G2 建议 | **Theme Cycle Pattern 标注** | `Sequential` 但窗口重叠的 2 个 Cycle 应改标 `Parallel` 或显式记录 overlap。 |
| **G2-3** | G2 建议 | **`campaign_date_observations` 缺失** | pre-R01 的 5 个 Campaign（`COMM/PHARMA/POWER`）**obs = 0**。 |
| **G2-4** | G2 建议 | **孤儿 source / evidence 处置规范** | 应明确「孤儿是否允许、是否需 `no_orphan_reason`」。 |
| **G2-5** | G2 建议 | **3 条 `evidence-temporal-mislabel` warning** | 属「总结类证据」的合法标注 vs validator 口径，需二选一并统一。 |
| **G2-6** | G2 建议 | **taxonomy aliases / proposals 统一登记** | 164 个 unmatched 名称需分类（alias / MECHANISM / 真 gap），建立 alias 表而非扩展 taxonomy。 |
| **G3-1** | G3 可保持 | **promote 率差异**（29% ~ 85%） | 由行业可公开证据密度决定，属合理任务差异。 |
| **G3-2** | G3 可保持 | **`campaign_themes.role` 只用 main/related/secondary** | `catalyst` 从未使用；无害。 |
| **G3-3** | G3 可保持 | **8 个未使用 theme** | T01 预留的 taxonomy 容量，非缺陷。 |
| **G3-4** | G3 可保持 | **`classification` 分布差异**（theme_campaign 24 / industry_trend 18） | 反映行业机制差异，合理。 |

> **G0（必须修复）= 0** —— 未发现机械性错误、数据损坏或契约违规。

---

# C. 重点治理问题详审

## C.1 【G1-1】Market Attention / 市场侧证据

### 当前事实

| 阶段 | 实际做法 | 证据 |
|---|---|---|
| pre-R01 | **无任何市场侧门槛**，也无 Beta caveat | 13 个 Campaign，Beta 提及 **0/13** |
| R01-01 | 无明确门槛；`C-2018-HIEQ-ROBOT-DOWN` **在缺 A 股行情证据下仍 Promote** | Beta 提及 1/5 |
| R01-02 | 市场证据较强；`C-2024-SEMI-MEMORY` 有 Beta caveat | Beta 提及 1/8 |
| R01-03 | **明确采用更严标准**（「市场关注必须由 A 股市场侧证据支撑」写进 Canonical Decision） | Beta 提及 1/6 |
| R01-04 | **参考但未固化**；`C-2020-CONS-WHITE-GOODS`（**contemp=0**）仍 Promote | Beta 提及 1/11 |
| R01-05 | **Beta caveat 极严格**（7/7 全部写明「未做 Beta 调整 / 不得解释为 Alpha」） | Beta 提及 **7/7** |
| R01-06 | 沿 R01-05；`001` 市场层**全 Tier 3 二手**，`002` **市场侧证据完全缺失** | Beta 提及 **2/2** |

**★ 实测两个「市场侧偏弱但仍 Promote」的实例**：
- `C-2020-CONS-WHITE-GOODS`：**0 条 contemporaneous evidence**（7 ev 全为 subsequent/retrospective）。
- `C-2019-MIL-GROUP-RESTRUCTURE`：**市场侧行情证据完全缺失**（涨幅/峰值/持续时间均不可考），`peak = NULL`。

### 判定

1. **是否应成为统一 Canonical Gate** → **是，但作为「软门槛」**。
   - **不应**作为「能否进入 canonical」的**硬门槛**：否则 R01-01 的 `C-2018-HIEQ-ROBOT-DOWN`、R01-06 的 `C-2019-MIL-GROUP-RESTRUCTURE` 等需回溯降级，而这些 Campaign 的**产业/公司/事件证据本身充分**，且已在 notes 中如实记录缺口。
   - **应**固化为 **Gate 的 Q3/Q4 加权项 + strength / date_confidence 的降级项**：
     - 有 A 股市场侧证据 → `strength` 可评 `strong`，`date_confidence` 可评 `medium/high`；
     - 仅有强行业/公司证据 → `strength` 上限 `medium`；
     - **无任何市场侧证据** → `strength` 上限 `medium` 且 `date_confidence ≤ medium`，**必须在 `research_notes` 写明「无行情核验」**。
2. **是否对所有 Campaign 生效** → **是**（新 Campaign 立即生效；既有 Campaign **不回溯**）。
3. **是硬门槛还是 strength/confidence 影响项** → **strength / date_confidence 影响项**（软门槛）。
4. **是否需 retroactive audit** → **建议只对「既有 notes 未记录市场侧缺口」的 Campaign 补记 caveat（属文本补记，不改数据）**；**不做降级、不改 strength**。
5. **受影响的 Campaign**（市场侧证据弱/缺）：
   - `C-2018-HIEQ-ROBOT-DOWN`（R01-01）
   - `C-2020-CONS-WHITE-GOODS`（R01-04，**contemp=0**）
   - `C-2019-MIL-GROUP-RESTRUCTURE`（R01-06，市场侧完全缺失）
   - `C-2024-FIN-BROKER-POLICY`（R01-05，市场响应仅 T3 相对强弱）
   - `C-2020-MIL-EQUIP-ORDER`（R01-06，市场层全 T3 二手）
   - pre-R01 的 13 个（**建议仅补记 caveat，不改 strength**）

> **本轮不回改任何历史 Campaign。**

## C.2 【G1-2】`research_report` Tier —— 完整 Inventory

### C.2.1 四方口径对照（实证）

| 文档 | 券商研报 tier | 档位数 | 是否定义研报 |
|---|---|---|---|
| `research_model_v1_0.md` §15（**冻结**） | **Tier 3** | 4 | ✅ 明确写「券商研报 / 研究机构 / 专业财经网站」 |
| `HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md` §7.3 | —（**未定义**） | 4 | ❌ |
| `historical_campaign_validation_v1.md` §1.2 | —（**未定义**） | **3** | ❌ |
| Validator `SOURCE_TYPE_TIER['research_report']` | **Tier 2（唯一）** | — | — |

★ 三份文档**档位数都不同**（4 / 4 / **3**），且 Protocol §7.3 与 validation §1.2 **均未定义券商研报**。

### C.2.2 DB 内 `research_report` 全量 Inventory（**23 条，全部 tier=2**）

| wave | 数量 | source_id |
|---|---:|---|
| R01-01 HIEQ | **7** | S-HIEQ-10 / 12 / 18 / 21 / 24 / 26 / 27 |
| R01-02 SEMI | **2** | S-SEMI-15 / 16 |
| R01-03 RES | **2** | S-RES-14 / 40 |
| R01-04 CONS | **2** | S-CONS-57 / 59 |
| R01-05 FINRE | **10** | S-FINRE-15 / 21 / 30 / 31 / 37 / 43 / 47 / 48 / 49 / 50 |
| R01-06 MIL | **0** | — |

**受影响的 Campaign**（由这些 source 派生的 evidence 所属）：

| campaign | 依赖的 research_report |
|---|---|
| `C-2016-HIEQ-CONSTR` | S-HIEQ-10, S-HIEQ-12 |
| `C-2018-HIEQ-ROBOT-DOWN` | S-HIEQ-24 |
| `C-2020-HIEQ-AUTOMATION` | S-HIEQ-21 |
| `C-2023-HIEQ-HUMANOID` | S-HIEQ-18 |
| `C-2023-HIEQ-ROBOT-PLUS` | S-HIEQ-26 |
| `C-2020-PANEL-CYCLE` | S-SEMI-16 |
| `C-2023-AI-COMPUTE-SEMI` | S-SEMI-15 |
| `C-2020-RES-RAREEARTH` | S-RES-14 |
| `C-2020-RES-LITHIUM` | S-RES-40 |
| `C-2023-CONS-VALUE-RETAIL` | S-CONS-59 |
| `C-2022-RE-POLICY-THREE` | S-FINRE-30 |
| `C-2023-FIN-SOE-VALUATION` | S-FINRE-31, S-FINRE-50 |
| `C-2024-FIN-BROKER-POLICY` | S-FINRE-21, S-FINRE-49 |
| `C-2020-RE-DEBT-RISK` | S-FINRE-48 |

**★ 另有 5 条 `research_report` 为孤儿 source**（S-HIEQ-27, S-FINRE-15, S-FINRE-37, S-FINRE-43, S-FINRE-47）—— 不影响任何 Campaign。

### C.2.3 语义问题（实测发现）

`research_report` 在 R01-01~05 中**被用作「研究报告」的统称**，而非仅「券商研报」：
- `S-CONS-57` = **艾媒咨询**（咨询机构报告）
- `S-FINRE-48` = **ScienceDirect 学术期刊**
- 其余为真正的券商研报（多为新浪财经 / 东方财富 / 搜狐转载）

→ 这既是**语义模糊**，也是 R01-06 选择绕开该枚举的**部分合理性来源**。

### C.2.4 建议（**不改 Research Model v1.0**）

| 项 | 建议 |
|---|---|
| **Validator 是否向 Research Model 对齐** | **是**。`SOURCE_TYPE_TIER['research_report']` 由 `(2,)` 改为 **`(2, 3)`**（兼容区间），使「券商研报 = Tier 3」合法。 |
| **是否存在历史数据迁移** | **是，一次性 migration**：现有 23 条 `research_report` 若其**实际为券商研报**，tier 由 2 → 3（`S-CONS-57` 咨询报告、`S-FINRE-48` 学术期刊**保持 2** 或改 `other`）。 |
| **是否需要兼容旧数据** | **是** —— 改为 `(2,3)` 后，现有 tier=2 的 23 条**不会 FAIL**，可平滑过渡。 |
| **Schema 是否需修改** | **否** —— `source_tier` 枚举已是 `(1,2,3,4)`，`source_type` 枚举已含 `research_report`。**Schema 无需改动**。 |
| **是否改 Research Model v1.0** | **否**（已冻结）。 |
| **是否回溯 Campaign** | **否** —— tier 变化不影响 Campaign / Evidence 绑定与结论；仅需重跑 export（tier 不进 export，实测 export 无 tier 字段 → **Export 不受影响**）。 |

## C.3 【G1-3】Beta / Relative Return —— Level 0–3 分级

### 分级定义

| Level | 定义 | 能否支撑 Alpha 判断 |
|---|---|---|
| **L0** | 只有绝对价格 / 涨跌幅（或仅持仓、仅订单等产业侧数据） | ❌ |
| **L1** | 相对基准（沪深300 / 上证 / 行业指数）超额，**但无 Beta 调整** | ❌ **Relative Return ≠ Beta-neutral Alpha** |
| **L2** | 有风格因子 / Beta 调整后的超额 | ⚠️ 可作参考，仍非 Alpha 定论 |
| **L3** | 可独立支持行业 Alpha 判断（多基准 + 因子剥离 + 显著性） | ✅ |

### 逐项统计（实测，**不虚构 L2/L3**）

| Level | Campaign |
|---|---:|
| **L1**（相对基准超额，无 Beta 调整） | `C-2022-RE-POLICY-THREE` · `C-2020-RE-DEBT-RISK` · `C-2024-FIN-BROKER-POLICY` · `C-2023-FIN-SOE-VALUATION` · `C-2024-FIN-BANK-DIVIDEND` · `C-2020-FIN-BANK-CREDIT` · `C-2025-FIN-INSURANCE`（**全部 R01-05，7 个**）；`C-2020-MIL-EQUIP-ORDER`（R01-06，中证军工指数区间涨跌，无基准对比，实为 **L0~L1 之间**） |
| **L0**（仅绝对涨跌 / 产业侧 / 事件侧） | **其余 45 个 Campaign** |
| **L2（有 Beta 调整）** | **0 个** |
| **L3（可支撑 Alpha 判断）** | **0 个** |

**★ 关键结论（实测）**：
- **全库无一个 Campaign 达到 L2 或 L3**；
- 所有 L1 使用**都已显式声明「未做 Beta 调整 / 未剥离风格因子 / 不得解释为行业 Alpha」**（R01-05 的 CF013、R01-06 的 CF008 均为明证）；
- R01-05 的 `CF013` 更进一步识别了**股息口径差**（个股前复权含股息 vs 沪深300 价格指数不含股息 → 银行超额被高估约 +15pct/3 年）—— 这是**比 L1 更细的 caveat，属最佳实践**。

### 建议

1. **强制分级标注**：每个 Campaign 的 `research_notes` 必须写明其市场证据 Level（L0/L1/L2/L3）。
2. **强制 caveat 模板**：凡 L1 必须包含「**相对收益 ≠ 行业 Alpha；未做 Beta 调整；未剥离风格因子**」。
3. **禁止**：任何 L0/L1 证据不得用于「跑赢 = Alpha」的表述。
4. **不虚构 L2/L3**：当前无一例，如实记录。
5. **不需要回溯**：L1 的 caveat 已在 R01-05/06 完整；pre-R01 / R01-01~04 未使用相对收益，**无 caveat 需求**。

## C.4 【G2-1】Peak / End 口径

### 实测分类

| 类别 | 数量 | Campaign |
|---|---:|---|
| `peak = NULL` | **4** | `C-2019-MIL-GROUP-RESTRUCTURE`（无行情数据）· `C-2024-FIN-BANK-DIVIDEND` · `C-2025-FIN-INSURANCE` · `C-2024-RES-GOLD-CB`（三者均为结构仍延续） |
| `end = NULL` | **6** | `C-2023-CONS-VALUE-RETAIL` · `C-2024-FIN-BANK-DIVIDEND` · `C-2025-FIN-INSURANCE` · `C-2023-HIEQ-ROBOT-PLUS` · `C-2024-RES-GOLD-CB` · `C-2024-SEMI-MEMORY` |
| peak 为 **推断 / cluster** | 多个 | `C-2020-MIL-EQUIP-ORDER`（2021-12-01，alternative 2021-08-24）· `C-2024-SEMI-MEMORY`（2025-10-31，区间高点口径）· `C-2023-COMM-OPTICAL`（2025-12-25，区间高点口径） |
| **商品 peak vs A 股 peak 分离** | 明确处理 | `C-2020-RES-LITHIUM`（A 股 peak 2021-09-13；商品 peak 2022-11-11，差约 14 个月）· `C-2020-RES-NONFERROUS`（A 股 2021-09-13；商品 LME 铜 2021-05-10）· `C-2024-RES-GOLD-CB`（**peak = NULL**，未把商品 2025-12-26 当 A 股 peak） |

### 用户点名的 6 处核查

| Campaign | peak | 判定 |
|---|---|---|
| `C-2024-SEMI-MEMORY` | 2025-10-31（区间高点口径） | ✅ 合理；end = NULL（结构仍延续） |
| `C-2020-RES-LITHIUM` | 2021-09-13（**A 股口径**） | ✅ **已正确分离商品 peak（2022-11-11）** |
| `C-2024-RES-GOLD-CB` | **NULL** | ✅ 正确 —— 未把商品峰值当 A 股 peak |
| `C-2020-RES-NONFERROUS` | 2021-09-13（A 股） | ✅ 已分离商品 peak |
| R01-05 银行 / 保险 | 银行 DIVIDEND / 保险 **peak+end 均 NULL** | ✅ 正确（结构可能仍在延续） |
| R01-06 军工 | `001` peak 2021-12-01（cluster）· `002` peak **NULL** | ✅ 正确 |

### 建议统一规范（四态决策树）

| 情形 | 处理 |
|---|---|
| 有可核验的 A 股单点/窄区间高点 | 用 **canonical peak**（EXACT_DATE） |
| 存在多个并列高点且证据同级 | 用 canonical peak **+ alternative 记录在 notes**（**不强行取单一日期**） |
| 仅有区间涨跌幅、无峰���日期 | **WINDOW / PHASE_WINDOW**（`date_confidence = low`） |
| 无可靠峰值证据，或结构仍延续 | **NULL**（**禁止**用观察窗口结束、商品峰值、行业数据峰值代替） |

**★ 明确保留**：**商品 peak ≠ A 股 Campaign peak**；**行业/产业数据 peak ≠ A 股 peak**；**事件结束日 ≠ Campaign End**。

## C.5 【G1-5】Downturn Campaign / `result = weak`

### 实测

| Campaign | wave | result | strength | 说明 |
|---|---|---|---|---|
| `C-2019-AD` | **pre-R01 legacy** | `weak` | **`weak`** | ⚠️ **legacy 用 `strength=weak`** |
| `C-2018-HIEQ-ROBOT-DOWN` | R01-01 | `weak` | `medium` | ✅ 现代口径 |
| `C-2022-SEMI-DOWNTURN` | R01-02 | `weak` | `medium` | ✅ 现代口径 |
| `C-2020-RE-DEBT-RISK` | R01-05 | `weak` | `medium` | ✅ 现代口径（`CF007` 裁决：下行结构**允许**进入 canonical） |

**R01-03 / R01-04 / R01-06 是否存在类似候选** → **均已处理，未再新增 `result=weak`**：
- R01-03：2023 年订单真空 → `exclusion X006`（**降温而非新行情**），未建 Campaign。
- R01-04：无下行 Campaign。
- R01-06：2022 年板块 -23.63% → 用作 `C-2020-MIL-EQUIP-ORDER` 的 **DECLINING 段**与 `E042` 反证，**未单独建下行 Campaign**。

### 判定

> **`result = weak` 已成为统一语义：= 市场 / 行业方向为负，而不是证据质量弱。** ✅（R01-01 / R01-02 / R01-05 三次一致使用）

**★ 但存在一处残留不一致**：`C-2019-AD`（legacy）使用 **`strength = weak`**，而现代口径下 `strength ∈ {medium, strong}`、负向由 `result` 承载。
全库 `strength` 分布：`strong 21 / medium 30 / **weak 1**` —— **唯一 1 例即 `C-2019-AD`**。

### 建议

1. **固化语义**：`result = weak` ⇔ 方向为负；`strength` **不得**取 `weak`（写入 Protocol 或 AGENTS.md 约定）。
2. **`C-2019-AD` 的 `strength = weak`** → 建议后续（**非本轮**）统一为 `medium`（保持 `result = weak`）。**本轮不改**。
3. **不要修改已有 Campaign**（用户要求）。

## C.6 【G2-2】Campaign vs Theme Cycle

### 实测（39 个 Theme Cycle，13 个含多 Campaign）

| Theme Cycle | # | 窗口关系 | 标注 Pattern | **一致性判定** |
|---|---:|---|---|---|
| `baijiu_premium_2016_2021` | 2 | 2016-06~2018-12 / 2019-03~2021-12（**不重叠**） | Sequential | ✅ |
| `hog_cycle_2018_2022` | 2 | 2018-08~2021-12 / 2021-08~2022-12（**重叠 2021-08~12**） | Sequential | ⚠️ **标 Sequential 但重叠** |
| `semi_localization_2019_2021` | 2 | 2019-05~2020-09 / 2020-07~2021-09（**重叠 2020-07~09**） | Sequential | ⚠️ **标 Sequential 但重叠** |
| `resource_reflation_2020_2022` | 4 | 全部重叠 | Parallel | ✅ |
| `beauty_aesthetics_2019_2022` | 2 | 2019-11~2022-12 / 2020-06~2022-12（**高度重叠**） | Parallel | ✅ |
| `bank_valuation_2023_2025` | 2 | 2023-04~06 / 2024-01~NULL（**不重叠**） | Parallel | ⚠️ **不重叠却标 Parallel**（机制同族，可辩护） |
| `service_consumption_2020_2023` | 2 | 2020-06~2022-12 / 2022-12~2023-06（**相邻**） | Sequential | ✅ |
| `panel_price_cycle_2016_2022` | 2 | 2016-02~2017-06 / 2020-06~2021-08（**不重叠**） | — | ✅ |
| `realestate_policy_cycle_2020_2023` | 2 | 2020-08~2022-07 / 2022-11~2023-02（**不重叠**） | Sequential | ✅ |
| `hieq_robot_2023` | 2 | 2023-01~NULL / 2023-05~2023-12（**重叠**） | — | ⚠️ 未标 Pattern |
| `summer_2024` | 2 | 2024-06-11~06-25 / 2024-07-08~07-31（**不重叠**） | — | ✅ |

### 判定

- ✅ **Campaign 必须自身通过 Gate** —— 六任务一致（每个 canonical Campaign 均有独立的 Gate 论证）。
- ✅ **Theme Cycle 只是上位组织结构**，**未替代 Campaign 独立性**。
- ✅ **同一行业不同机制可 Parallel**（`resource_reflation` 4 个、`bank_valuation` 2 个）。
- ✅ **前后阶段可 Sequential**（白酒 / 猪周期 / 地产政策 / 服务消费）。
- ✅ **Campaign overlap 允许** —— 实测 beauty / hog / semi / resource / hieq_robot 均存在窗口重叠，**未被强行改日期**。
- ⚠️ **2 个 Cycle 标 `Sequential` 但窗口重叠**（`hog_cycle_2018_2022`、`semi_localization_2019_2021`）；1 个不重叠却标 `Parallel`（`bank_valuation_2023_2025`）；1 个未标 Pattern（`hieq_robot_2023`）。

### 建议（G2）

1. **统一 Pattern 定义**：`Sequential` = 时间前后接续（**允许首尾轻微重叠**）；`Parallel` = 时间并存；并**显式记录 overlap 区间**。
2. 对上表 4 个标注存疑的 Cycle **补记 overlap 说明**（文本层，**不改数据**）。
3. **不因 Pattern 而合并/拆分 Campaign**。

## C.7 【G2-6】Taxonomy

### 实测（CMTR v1，52 行 / 11 root）

- **root 11 个**：汽车 · 信息通信 · 消费 · **国防军工** · 电子 · 金融 · 高端装备 · 医药健康 · 电力设备 · 房地产 · 资源 —— **11/11 均有 Campaign**（无空缺 root）。
- **3 层结构存在**（孙节点 7 个）：`TH-ELEC-SEMI-EQUIP/MAT`、`TH-HIEQ-HUMANOID`、`TH-RES-AGRI/PRECIOUS/RARE`、`TH-TESLA-CHAIN`。
- **8 个未使用 theme**：`TH-DEFENSE-ELEC` `TH-DEFENSE-SPACE` `TH-ELEC-SEMI-MAT` `TH-HIEQ-RAIL` `TH-PHARMA-PANDEMIC` `TH-PHARMA-TCM` `TH-REALESTATE-MATERIAL` `TH-RES-AGRI`（**T01 预留容量，非缺陷**）。
- **ambiguous（重名）= 0** ✅
- **matched（已覆盖）= 32 个名称**；**unmatched = 164 个**。

### 164 个 unmatched 名称的分类（建议，**不扩展 taxonomy**）

| 类别 | 数量（约） | 典型 | 处置 |
|---|---:|---|---|
| **① 现有 theme 的 alias** | **~95** | 军工/军工行业/国防军工行业→`TH-DEFENSE`；白酒/酿酒行业→`TH-CONSUMER-FOOD`；芯片/集成电路/存储/DRAM→`TH-ELEC-SEMI`；面板/LCD/液晶面板→`TH-ELEC-PANEL`；券商/证券/大金融→`TH-FIN-NONBANK`；化工/染料/化肥/农药→`TH-RES-CHEM`；铜/电解铝/黄金/稀土→`TH-RES-METAL`；自动化设备/工控设备→`TH-HIEQ-AUTOMATION` | **建 alias 表**，不新增 theme |
| **② 机制名（MECHANISM）—— 不应入 taxonomy** | **~45** | 供给收缩 / 产能去化 / 供给侧改革 / 能耗双控 / 周期反转 / 缺芯 / 国产替代 / 自主可控 / 消费升级 / 消费降级 / 以旧换新 / 财政补贴 / 三道红线 / 因城施策 / 保交楼 / 棚改货币化 / 信贷周期 / 降准降息 / 中特估 / 高股息红利 / 装备采购 / 军品订单 / 订单驱动 / 军民融合 / 军转民 / 民参军 / 资产证券化 | **登记为 Mechanism**（`MT006` 式），**不进 taxonomy** |
| **③ 跨族方向（CROSS_FAMILY）—— 不应入 taxonomy** | **2** | 金融地产（R01-05 `MT002`）、军民融合（R01-06 `MT007`） | **保持 CROSS_FAMILY**，不建 root |
| **④ 真正的 taxonomy gap（建议后续独立轮次评估）** | **~8** | **美容护理**（R01-04 `MT006`）· **商贸零售**（R01-04 `MT007`）· **商业航天 / 卫星互联网**（R01-06 `CF004`，且跨信息通信族）· **AI算力 / 算力芯片 / HBM / GPU**（R01-02）· **消费电子 / 电子元器件 / 被动元件**（R01-02）· **兵器装备**（R01-06） | **本轮不扩展**；登记待办 |
| **⑤ 军工/其他细分（可归现有子主题）** | ~14 | 航空发动机/大飞机→`TH-DEFENSE-AIR`；船舶/航海装备→`TH-DEFENSE-SHIP`；卫星导航→`TH-DEFENSE-SPACE`；军贸/阅兵主题/地面兵装/新质战斗力/主机厂→叙事/机制，非 theme | alias 或 Mechanism |

**★ 结论**：164 个 unmatched 中，**绝大多数（~95）只是 alias、~45 是机制名**，**真正的 taxonomy gap 仅约 8 个**，且其中「商业航天 / 卫星互联网」还涉及跨族裁决。→ **无需扩展 taxonomy**，只需**建立 alias 表 + Mechanism 登记表**。

## C.8 【G2-4 / G1-4】Evidence Attribution

### 实测

| 检查 | 结果 |
|---|---|
| **一条 evidence 绑定多个 Campaign** | **0** ✅ —— 1:1 **全库零违规** |
| **未绑定（孤儿）evidence** | **25 条** |
| **未绑定（孤儿）source** | **84 条**（占 382 的 22%） |

**孤儿 evidence 分布**：legacy 7（`E-2018`×4 / `E-2019`×2 / `E-2023`×1）· R01-01 **2** · R01-02 **0** · R01-03 **0** · R01-04 **9** · R01-05 **4** · R01-06 **3**
**孤儿 source 分布**：legacy 7 · R01-01 **5** · R01-02 **11** · R01-03 **18** · R01-04 **5** · R01-05 **22** · R01-06 **16**

### 用户点名的 5 处

| 对象 | 现状 | 判定 |
|---|---|---|
| **R01-02 `E056`** | 已在 R01-02 数据质量收口处理（attribution 核查） | ✅ 已闭环 |
| **R01-05 `E141`** | 沪深300 全局基准，被 10 候选共享 → **不绑定任何 Campaign**（`GLOBAL_BENCHMARK_EV`） | ✅ **正确** —— 基准证据不应属于某个 Campaign |
| **R01-05 `E132`/`E137`/`E140`** | 分别归属 `008`/`010`/`006`（`EVIDENCE_OWNER`） | ✅ 正确 —— 未为消除共享而合并 Campaign |
| **R01-06 `E042`** | 反向证据 → **入 DB 但不绑定任何 Campaign**（research-level） | ✅ **正确** —— 原绑定对象 006 判 RO；若绑定 2015 Campaign 会触发 `evidence-temporal-mislabel` |

### 判定与建议

1. **1:1 attribution **未破坏**证据语义** —— 因为对「全局基准」与「研究级反证」已建立 **不绑定（unbound）** 这一合法出口（R01-05 `E141`、R01-06 `E042`）。
2. **benchmark evidence** → **不应**属于任何 Campaign；保持 unbound。
3. **context evidence** → **视情况**：若与 Campaign 时间相容可绑定；若不相容（如 `E042`）→ **保持 unbound**。
4. **Research Only evidence** → **按既有惯例不入库**（R01-01~06 一致）；**例外**：具全局方法论价值的（如 `E042`）可 **research-level 入库但不绑定**。
5. **orphan source** → **允许存在**（来源被候选/conflict/exclusion 引用但无独立 evidence 行）；**但应要求**其曾在 `candidates.source_ids` / `conflict.positions.source_ids` / `exclusions.source_ids` 中被引用，否则视为**无来源**。
   - 实测：84 条孤儿 source **绝大部分**确实被上述字段引用（R01-06 实测 0 真孤儿）。→ **可接受，但需机器可校验**。
6. **★ G1-4**：**Validator C01–C25 无孤儿检查**（已确认 `grep` 无 `orphan` 相关逻辑）→ 建议新增 **C26 orphan report**（**WARN 级**，非 FAIL），使孤儿可见且可复核。

## C.9 【G2-5】Temporal / PIT

### 实测

- `temporal_relation` 分布：`contemporaneous 200 / subsequent 97 / retrospective 35 / prior 15 / unknown 7`
- **无 `event_date` 的 evidence**：**6 条**
- **3 条 `evidence-temporal-mislabel` warning**（全部 R01-02）：

| evidence | date | tr | role | bound campaign | campaign end | 内容性质 |
|---|---|---|---|---|---|---|
| `E-SEMI-29` | 2020-12-28 | contemporaneous | context | `C-2019-SEMI-LOCALIZATION` | 2020-09-30 | **2020 全年总结**（62 只半导体股年度表现） |
| `E-SEMI-47` | 2022-12-29 | contemporaneous | **supporting** | `C-2022-SEMI-DOWNTURN` | 2022-10-12 | **2022 全年总结**（行业下行周期复盘） |
| `E-SEMI-48` | 2022-10-31 | contemporaneous | context | `C-2022-SEMI-DOWNTURN` | 2022-10-12 | 2022-10 美国出口管制（**事件日期 10 月，发布 10-31**） |

### 判定

三者**共同性质**：**「期末 / 年度总结类证据」**—— 其**内容**覆盖 Campaign 窗口，但**发布日期**晚于 Campaign `end_date`。
`temporal_relation = contemporaneous` 是按「证据所述事件的时期」标注（内容同期），而 validator 按「证据日期 vs campaign end」判定（日期晚）→ **口径不同**。

| 可能定性 | 评估 |
|---|---|
| ① 合理 context | **部分成立** —— 内容确为窗口内事实；但 `E-SEMI-47` 是 `supporting`，用作支撑则更需谨慎 |
| ② validator 口径问题 | **部分成立** —— 「总结类证据」被一律视为 mislabel，未区分「内容期」与「发布期」 |
| ③ 需真正修正 | **可辩护** —— 严格按 Protocol §7.4，2022-12-29 的年度复盘应标 `subsequent`/`retrospective` 并填 `point_in_time_note` |

### 建议（**不为清零 warning 而篡改历史证据**）

1. **首选**：保留现状（**caveat**），但在 Governance Review 中**明确记录**：这 3 条属「总结类证据的内容期/发布期口径差」，**非数据错误**。
2. **次选（若后续要清零）**：走**正式变更流程**——将 `E-SEMI-29/47/48` 的 `temporal_relation` 改为 `subsequent`，按 Protocol §7.4 **补填 `point_in_time_note`**；`E-SEMI-47` 若改 `retrospective` 则 `support_kind` 需含 `retrospective_context`。
   - ⚠️ 这**会修改研究内容**，需单独评审，**本轮不做**。
3. **validator 侧**（可选）：为「总结类证据」引入 `period_covered_start/end` 字段，或按 `support_kind=retrospective_context` 豁免。属 Schema 变更，**本轮不做**。

## C.10 【A.3】Annual Review / Rule 一致性（**已达标**）

| rule | campaigns | annual_reviews | campaign_year ⊇ AR |
|---|---:|---:|---|
| `rule_high_end_equipment` | 5 | 5 | ✅（2016/2018/2020/2023/2024） |
| `rule_semiconductor` | 8 | 6 | ✅（2016/2019/2020/2022/2023/2024） |
| `rule_resources` | 6 | 4 | ✅（2019/2020/2021/2024） |
| `rule_consumer` | 11 | 8 | ✅（2016/2018/2019/2020/2021/2022/2023/2024） |
| `rule_fin_realestate` | 7 | 5 | ✅（2020/2022/2023/2024/2025） |
| `rule_defense_military` | 2 | 2 | ✅（2019/2020） |

> **★ R01-04 暴露的「新增 rule 后必须为每个 campaign_year 建 annual_review」已确认为固定检查项**，六个新 rule **零缺失**。
> 建议将此检查**固化进 `validate_db`**（当前依赖人工 + importer 纪律）。→ 归入 **G2-3** 一并处理。

## C.11 【G2-3】`campaign_date_observations` 缺失（实测发现）

| Campaign | wave | `campaign_date_observations` |
|---|---|---:|
| `C-2019-COMM-5G` | pre-R01 | **0** |
| `C-2023-COMM-OPTICAL` | pre-R01 | **0** |
| `C-2019-PHARMA-INNOV` | pre-R01 | **0** |
| `C-2020-POWER-NE` | pre-R01 | **0** |
| `C-2022-POWER-GRID` | pre-R01 | **0** |
| `C-2016-PANEL-CYCLE` | R01-02 | 3 |
| 其余 R01 Campaign | R01 | 1~3 |

→ **5 个 pre-R01 Campaign 无 date_observation**（导入早于该约定）。建议后续补齐（**属数据补齐，非本轮**）。

---

# D. 历史影响范围（对每个 G）

| ID | 级别 | 影响 Campaign | 需回溯？ | 影响 DB | 影响 Export | 影响 SA/TO | 修改范围 |
|---|---|---|---|---|---|---|---|
| **G1-1** 市场侧证据 | G1 | 6 个弱市场侧 + pre-R01 13 个（补记 caveat） | **否**（仅文本补记） | 否 | 否（notes 不进 export） | **是**（SA 若用 strength 需 caveat） | Protocol/AGENTS 约定 + 后续 notes 补记 |
| **G1-2** research_report Tier | G1 | 14 个（见 C.2.2） | **否**（不改结论） | **是**（23 行 tier 2→3） | **否**（export 无 tier 字段） | 否 | Validator C08 + 一次性 migration 脚本 |
| **G1-3** Beta/相对收益 | G1 | 8 个（R01-05 七个 + R01-06 001） | **否**（caveat 已存在） | 否 | 否 | **是**（SA 需注明 Level） | Protocol/AGENTS 约定（Level 标注） |
| **G1-4** Validator 孤儿检查 | G1 | 无（只增 WARN） | 否 | 否 | 否 | 否 | Validator +C26（WARN 级） |
| **G1-5** result=weak 语义 | G1 | **1 个**（`C-2019-AD` 的 `strength=weak`） | **否**（建议后续统一） | 若改则 1 行 | 若改则 1 条 | 若改则轻微 | 约定 + 后续 1 行修正 |
| **G2-1** Peak/End 规范 | G2 | 10 个（peak/end NULL 或推断） | **否** | 否 | 否 | **是**（TO 用日期窗口） | 约定文档 |
| **G2-2** Theme Cycle Pattern | G2 | 4 个 Cycle | **否**（仅补记 overlap） | 否 | 否 | 否 | 约定 + 文本补记 |
| **G2-3** date_observations 缺失 | G2 | 5 个 pre-R01 | **否**（补齐属新增） | 若补则 +15 行 | 否 | **是**（TO 依赖） | 后续补齐脚本 |
| **G2-4** 孤儿处置规范 | G2 | 无 | 否 | 否 | 否 | 否 | 约定 |
| **G2-5** 3 条 temporal warning | G2 | 2 个（`C-2019-SEMI-LOCALIZATION` / `C-2022-SEMI-DOWNTURN`） | **否**（保留 caveat） | 否 | 否 | 否 | 约定 |
| **G2-6** taxonomy aliases | G2 | 无 | 否 | 否（仅登记） | 否 | 否 | alias 表 + Mechanism 登记表 |
| **G3-1~4** | G3 | — | 否 | 否 | 否 | 否 | 不处理 |

---

# E. SA / Time Observation 前置条件

## E.1 **必须在刷新 SA / TO 前处理**（阻塞项）

| # | 项 | 为什么阻塞 |
|---|---|---|
| 1 | **G1-1 市场侧证据门槛统一** | SA 若按 `strength` 比较跨族结构，必须先确定「无市场侧证据」的 strength 上限，否则 6 个弱市场侧 Campaign 与 21 个 `strong` 不可比。 |
| 2 | **G1-3 Beta/相对收益 Level 标注** | SA 若把「相对超额」当 Alpha 强度会系统性失真。必须先把 Level 0–3 标注进 notes。 |
| 3 | **G1-5 `result=weak` 语义统一** | SA 的「负向结构」比较依赖 `result=weak` 的一致语义；`C-2019-AD` 的 `strength=weak` 会造成口径分叉。 |
| 4 | **G2-1 Peak / End 四态规范** | **TO 直接依赖日期窗口与 peak**。必须先确定「NULL / WINDOW / alternative」的合法用法，否则 TO 的窗口构造会不一致。 |

## E.2 **可带 caveat 进入刷新**（非阻塞）

| # | 项 | 附带 caveat 的写法 |
|---|---|---|
| 1 | G1-2 `research_report` Tier | 「既有 23 条 tier=2 为历史兼容；对齐后为 Tier 3。**不影响任何 Campaign 结论**」 |
| 2 | G1-4 孤儿检查缺失 | 「84 孤儿 source / 25 孤儿 evidence 未经机器校验，已在报告中人工复核」 |
| 3 | G2-2 Theme Cycle Pattern 标注存疑（4 个） | 「overlap 区间已记录；Pattern 标注待统一」 |
| 4 | G2-3 `campaign_date_observations` 缺失（5 个 pre-R01） | 「该 5 个 Campaign 日期未经 date_observation 记录」 |
| 5 | G2-5 3 条 temporal warning | 「属总结类证据内容期/发布期口径差，非数据错误」 |
| 6 | G2-6 taxonomy aliases | 「164 个未解析名称中 ~95 为 alias、~45 为机制名；真 gap 约 8 个，均未影响 Campaign 归属」 |
| 7 | G3-1 promote 率差异（29%~85%） | 「反映行业可公开证据密度差异，非标准差异」 |

## E.3 建议的刷新顺序

```
1. 先落地 G1-1 / G1-3 / G1-5 的「约定」（不改数据）      → 解除 SA 阻塞
2. 再落地 G2-1 的 Peak/End 四态规范                    → 解除 TO 阻塞
3. 然后刷新 SA（新 artifact 版本）
4. 然后刷新 TO（新 artifact 版本）
5. G1-2 / G1-4 / G2-3 / G2-4 / G2-6 可在刷新后按独立轮次处理
```

---

# F. Validator / Worker 版本差异表

| 项 | Worker Workspace | ThreeC 当前 | 差异影响 |
|---|---|---|---|
| **检查项数量** | **24 checks** | **C01–C25（25 项）** | Worker 报的 `24 checks` **不是 ThreeC 口径**；以 C01–C25 为准 |
| **Strict Draft-07** | **无**（Worker 有 `schema_conformance` 但非 Draft-07 全量） | **C25**（`jsonschema` Draft7Validator，含 `additionalProperties:false`） | R01-01 `_position_note` 违规即被 C25 发现 |
| **`source_type` ↔ `tier` 映射** | 依 Worker 自身实现 | **C08 `SOURCE_TYPE_TIER`** | **三方文档不一致**（G1-2） |
| **`research_report` tier** | 部分 Worker 用 `media_tier3 + tier 3` 规避 | C08 允许 `(2,)` only | R01-06 规避成功但**语义损失** |
| **`--check` 目录假设** | Worker 假设自身 workspace 结构 | ThreeC `--check` 扫 `packages/*` | Worker 误报；**不影响主仓库** |
| ** orphan 检查** | Worker 部分实现 | **C01–C25 无 orphan 检查** | **G1-4**：84 孤儿 source 未被机器发现 |
| **canonical ID 泄漏** | 有（部分） | **C13** 强制 | 一致 |
| **PIT / support_kind 一致性** | 有 | **C19** 强制（三条规则） | 一致 |
| **LF / 确定性** | 有（部分） | **C20** 强制 | 一致 |
| **数量 KPI** | 有 | **C22** 强制 | 一致 |

### 建议（**本轮不重建 Worker**）

1. **明确「唯一事实规则」**：以后 Worker 交付**只以 ThreeC `validate_historical_research_intake.py` 的 C01–C25 + C25 Draft-07 为准**；Worker 自检结果**仅供参考**。
2. **向 Worker 提供**：`research/intake/` 下 **Protocol + Schema + Validator** 三件套的**当前版本快照**（含 C25），避免 R01-06 的 `KNOWN_TAXONOMY_AND_OVERLAP_NOTES` 陈旧问题重演。
3. **taxonomy 快照**：提供 T01 后的 **11 root / 52 行** taxonomy 清单（见 MEMORY.md §7），防止 Worker 再误判 root 数量。
4. **后续**（独立轮次）：为 Worker 增加 **C26 orphan report**，并统一 `--check` 行为。

---

# G. 现有 3 条 DB Warning 的最终定位

| 项 | 结论 |
|---|---|
| **来源** | **全部来自 R01-02**（`E-SEMI-29` / `E-SEMI-47` / `E-SEMI-48`）✅ |
| **性质** | 「**期末/年度总结类证据**」：内容期在 Campaign 窗口内，**发布期**晚于 `campaigns.end_date` → `temporal_relation=contemporaneous` 与 validator 的「date vs end」判定口径不同 |
| **当前是否只是 caveat** | **是** —— 已由 R01-02 数据质量收口明确记录为 **unresolved caveat**，`validate_db` 仅 WARN 不 FAIL |
| **是否影响 Structural Analogy** | **否**（SA 未刷新；且这 3 条证据不参与跨族结构比较的判据） |
| **是否影响 Time Observation** | **否**（TO 未刷新；且这 3 条不涉及日期窗口构造） |
| **是否需在刷新前处理** | **否** —— 可带 caveat 进入刷新（见 E.2 #5） |
| **是否要清零** | **否** —— **不得为清零 warning 而改变研究结论或篡改历史证据** |

---

# H. 本轮严格未做（合规声明）

- ❌ 未修改任何历史 Campaign / research data；
- ❌ 未修改 Schema · Protocol · Research Model v1.0 · Validator · taxonomy；
- ❌ 未刷新 Structural Analogy / Time Observation；
- ❌ 未启动新 Research Task，未引入新 Candidate；
- ❌ 未回改任何 R01-01~R01-06 的历史结论；
- ❌ 未扩展 taxonomy（164 个 unmatched 仅分类登记）；
- ✅ **唯一产物**：本审计报告 + `docs/PROJECT_STATE.md` 同步（文本层）。

---

# I. 交付物

| 文件 | 说明 |
|---|---|
| `docs/R01_GOVERNANCE_CONSISTENCY_REVIEW_v0_1.md` | 本文件 |
| `docs/PROJECT_STATE.md` | 同步更新（下一目标 = 治理修复决策；SA/TO 前置条件） |
