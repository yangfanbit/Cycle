# `扩产` / `扩产周期` 语义裁决报告（v0.3-r2）

> | 项目 | 值 |
> |---|---|
> | **性质** | **`扩产` / `扩产周期` 专项语义裁决 + 最小影响修复** |
> | **基线** | HEAD `0ce4344` · a/b `0/0` · worktree clean |
> | **裁决** | **`扩产` → A（保留在 `DEMAND_SURGE`）** · **`扩产周期` → D（从 canonical keyword mapping 删除）** |
> | **实施** | 删除 `扩产周期`（保留 `扩产`）—— revision **`v0.3-r2`** |
> | **未做** | 未处理其余 5 项 substring collision · 未生成 SA v0.4 · 未刷新 Time Observation · 未改 Rule Set v0.3 · 未改 taxonomy · 未改 DB schema · 未重新研究 R01 · 未改 v0.1/v0.2 · 未为改善 SA 数量而放宽标准 |

---

## 一、审计（**先不改词表**）

### 1.1 两个词的基本事实

| 项 | `扩产` | `扩产周期` |
|---|---|---|
| 当前 canonical | **`DEMAND_SURGE`** | **`SUPPLY_CONTRACTION`** |
| 来源版本 | **v0.3 新增**（v0.1 **无**此词） | **v0.3 新增**（v0.1 **无**此词） |
| 声明覆盖理由（原 `coverage_note`） | `C-2020-SEMI-EQUIPMENT：晶圆厂扩产` | `C-2020-SEMI-EQUIPMENT：晶圆厂扩产（供给端产能扩张，方向相反，单列以利审计）` |

### 1.2 全部真实命中文本（541 条 ledger 中）

**`扩产` 命中 2 条**：

| # | cycle | bucket | raw_driver | matched_rules | mapping_status | canon |
|---|---|---|---|---|---|---|
| 1 | `C-2020-SEMI-EQUIPMENT` | start#3 | **国内晶圆厂进入扩产周期** | `[DEMAND_SURGE, SUPPLY_CONTRACTION]` | `DERIVED` | `None` |
| 2 | `C-2020-PANEL-CYCLE` | start#2 | **2018-2019 年过度扩产后的产能出清，行业集中度提升** | `[POLICY_DRIVEN, DEMAND_SURGE, SUPPLY_CONTRACTION]` | `DERIVED` | `None` |

**`扩产周期` 命中 1 条**：

| # | cycle | bucket | raw_driver | matched_rules | mapping_status | canon |
|---|---|---|---|---|---|---|
| 1 | `C-2020-SEMI-EQUIPMENT` | start#3 | **国内晶圆厂进入扩产周期** ← **与 `扩产` 命中文本 #1 完全同一文本** | `[DEMAND_SURGE, SUPPLY_CONTRACTION]` | `DERIVED` | `None` |

> **★ 关键事实 1**：`扩产周期` 的命中集合是 `扩产` 命中集合的**严格子集** —— **`扩产周期` 贡献 0 条独有覆盖**。

### 1.3 是否造成现有 Campaign / RC 的机制误判

| cycle | 现状 `canonical_drivers` | 是否受影响 |
|---|---|---|
| `C-2020-SEMI-EQUIPMENT` | **`['POLICY_DRIVEN']`**（仅 1 个） | ⚠️ **是** —— 其需求机制**不可见** |
| `C-2020-PANEL-CYCLE` | `['DEMAND_SURGE', 'SUPPLY_CONTRACTION']`（完整） | ❌ 否（误命中不改变结果） |
| 其余 50 个 Campaign / 27 个 RC | — | ❌ 否（无命中） |

**`C-2020-SEMI-EQUIPMENT` 的机制问题**：该 Campaign 的 `start` 相位共 3 条驱动，其中
- 「中芯国际回 A 并把募资投向 12 英寸产线」→ `UNKNOWN`（无命中）
- 「大基金二期聚焦设备/材料」→ `DERIVED` / **`POLICY_DRIVEN`** ✓
- 「**国内晶圆厂进入扩产周期**」→ `DERIVED` / **`None`** ← 被 `[DEMAND_SURGE, SUPPLY_CONTRACTION]` 双命中卡住

→ 结果：该 Campaign 的 `canonical_drivers` **只有 `POLICY_DRIVEN`**，
**其真实需求机制（晶圆厂扩产 → 设备需求）完全不可见**。

### 1.4 ★ 决定性证据：研究自身的机制表述

`research/intake/packages/R01-02/candidates.json`：

| candidate | **title（研究自身的机制框架）** |
|---|---|
| `R01-SEMICONDUCTOR-002` | 「2020–2021 半导体设备与材料国产替代（**晶圆厂扩产 → 「卡脖子」上游**）」 |
| `R01-SEMICONDUCTOR-003` | 「2020–2022 面板（LCD）价格上行周期：**韩国产能退出 + 宅经济需求**」 |

→ **研究自身**把「晶圆厂扩产」明确定位为**上游（设备/材料）的需求来源**；
把面板周期的机制定位为「**产能退出**（供给收缩）+ 宅经济需求」，
即「2018-2019 年过度扩产」在面板语境中是**时序前提**，机制是「**产能出清**」。

---

## 二、语义裁决

### 2.1 `扩产` → **A：可作为 `DEMAND_SURGE` 的有效机制词**（保留）

**逐项排除其他选项**：

| 选项 | 结论 |
|---|---|
| **A**（有效 `DEMAND_SURGE` 机制词） | ✅ **成立**（依据见下） |
| **B**（应属其他已有 canonical） | ❌ 不成立 —— 「产能扩张」在机制上与 `SUPPLY_CONTRACTION`（供给收缩）**方向相反**；与 `INDUSTRY_UPGRADE` / `TECH_BREAKTHROUGH` / `VALUATION_RESET` / `CYCLE_REVERSAL` / `EVENT_CATALYST` 均无机制对应。**9 项 canonical 中没有「产能扩张」这一机制轴** |
| **C**（只能作上下文/结果，不能单独作为 canonical driver） | ❌ 不采纳 —— 会使 `C-2020-SEMI-EQUIPMENT` 的需求机制**永久不可见**，**与其研究标题直接矛盾**；且该文本会退化为 `UNKNOWN`（**负面变化**） |
| **D**（从 mapping 删除） | ❌ 同 C |

**A 的三条依据**：

1. **研究自身表述**（最强证据）：`R01-SEMICONDUCTOR-002` 标题即
   「半导体设备与材料国产替代（**晶圆厂扩产 → 「卡脖子」上游**）」→ 扩产 = 上游需求。
2. **v0.1 既有惯例**：`DEMAND_SURGE` 已含「**装机 / 并网 / 招标 / 采购**」——
   这些同为**观察者相对的客户侧动作**（**他人动作 → 本行业需求**）。「扩产」性质完全相同。
3. **决定性数据证据**：删除 `扩产周期` 后，「国内晶圆厂进入扩产周期」变为 **1 命中** →
   `DERIVED` / **`canonical_driver = DEMAND_SURGE`** → `C-2020-SEMI-EQUIPMENT` 获得
   **`['DEMAND_SURGE', 'POLICY_DRIVEN']`**，**与研究标题一致**，且**无任何数据损失**。

**★ 已知误命中（如实记录，不隐藏）**：
命中文本 #2（`C-2020-PANEL-CYCLE`「2018-2019 年**过度扩产**后的产能出清」）中，
「扩产」是**时序前提**而非驱动机制 → 属**误命中**。
但该文本同时命中 `POLICY_DRIVEN`（「集中度」）+ `SUPPLY_CONTRACTION`（「产能」「出清」）→ **2 命中** →
**无论是否保留「扩产」，结果均为 `DERIVED` / `None`** → **误命中零数据影响**。

> ⚠️ **风险披露**：`扩产` 作为关键词存在**系统性误命中风险**（例如未来的「硅料扩产」文本会被赋予
> `DEMAND_SURGE`，而硅料扩产实为供给增加）。该风险与 v0.1 既有的「装机/招标/采购」同类，
> **不在本轮处理范围**（属 multi-hit disambiguation / 词表细化）。**已记录为后续观测项。**

### 2.2 `扩产周期` → **D：从 canonical keyword mapping 中删除**

**四条依据**：

| # | 依据 |
|---|---|
| **① 零增量覆盖** | 其唯一命中文本「国内晶圆厂进入扩产周期」**已被 `扩产` 完全覆盖** → 贡献 **0 条独有覆盖** |
| **② 方向错误** | 它被归入 **`SUPPLY_CONTRACTION`**，而「**产能扩张**」在机制上与「**供给收缩**」**方向相反** —— 原 `coverage_note` 自述「供给端产能扩张，方向相反，单列以利审计」，**该推理不成立**：产能扩张不属于供给收缩 |
| **③ 实际损害** | 它使该文本额外命中 `SUPPLY_CONTRACTION` → 把**本应得到 `DEMAND_SURGE`** 的文本推入 2-命中 `DERIVED`（canon=None），**直接导致 `C-2020-SEMI-EQUIPMENT` 的需求机制不可见** |
| **④ 无替代必要性** | `扩产` 已覆盖该语境；「**周期**」不携带机制（v0.1/v0.3 词表中「周期」单独均非关键词） |

**逐项排除其他选项**：

| 选项 | 结论 |
|---|---|
| A（有效 `DEMAND_SURGE` 词） | ❌ 与 `扩产` 重复（零独有覆盖），保留只会**加重多命中** |
| B（迁到其他 canonical） | ❌ 迁移到 `DEMAND_SURGE` 会与 `扩产` 形成**同 canonical 内重复**，仍是零增量覆盖 |
| C（只能作上下文） | ⚠️ 等价于 D（不作 keyword） |
| **D（删除）** | ✅ **采纳** —— 且符合用户 §三「**优先考虑删词而不是迁移**」 |

> **★ 明确：不是「为消除 collision 而机械让两个词归到同一个 canonical」。**
> 本裁决是 **`扩产` 保留在原 canonical（A）· `扩产周期` 删除（D）** —— **一留一删**，
> 且删除理由是**零增量覆盖 + 方向错误 + 实际损害**，由**真实命中文本**证明。

---

## 三、最小影响分析（S0 → S1）

**场景定义**（`research/scripts/decide_kuochan_semantics.py`，**显式重建三场景、可重复运行**）：
- **S0** = 修改前（`扩产`→DEMAND_SURGE，`扩产周期`→SUPPLY_CONTRACTION）
- **S1** = **已实施**（删除 `扩产周期`）
- **S2** = 对照（`扩产` + `扩产周期` 都删）

### 3.1 逐条差异（S0 → S1，**全部 1 条**）

| cycle_id | bucket | raw_driver | 旧 matched_rules | 新 matched_rules | 旧 status | 新 status | 旧 canon | 新 canon | primary 变化 | 影响 SA |
|---|---|---|---|---|---|---|---|---|---|---|
| `C-2020-SEMI-EQUIPMENT` | start#3 | 国内晶圆厂进入扩产周期 | `[DEMAND_SURGE, SUPPLY_CONTRACTION]` | **`[DEMAND_SURGE]`** | `DERIVED` | `DERIVED`（**未变**） | `None` | **`DEMAND_SURGE`** ✅ | **无** | **有**（+1 PARTIAL） |

**`DIRECT → DERIVED` / `DERIVED → DIRECT` / `AMBIGUOUS` / `UNKNOWN` / `NOT_AVAILABLE` 变化**：
**全部为 0** —— 本条差异**不涉及**任何 status 变化，只涉及 `canonical_driver` 由 `None` 变为 `DEMAND_SURGE`。

### 3.2 canonical_drivers 变化

| cycle | S0 | S1 |
|---|---|---|
| **`C-2020-SEMI-EQUIPMENT`** | `['POLICY_DRIVEN']` | **`['DEMAND_SURGE', 'POLICY_DRIVEN']`** ✅ |

**其余 78 个 cycle 的 driver 集合：0 变化。**

### 3.3 primary_mechanism 变化

**0 个 cycle 变化**（`C-2020-SEMI-EQUIPMENT` 的 `direct_count` 仍为 0 → `primary = UNKNOWN`，未变）。

### 3.4 ★ 负面变化披露

**S1（已实施方案）：无任何负面变化** —— 无 status 降级、无 driver 丢失、无 `UNKNOWN` 增加。

**对照 S2（未采纳）**：会产生 **1 条负面变化** ——
`C-2020-SEMI-EQUIPMENT` start#3 `DERIVED → UNKNOWN`（`UNKNOWN 86 → 87`、`DERIVED 454 → 453`），
且 `canonical_drivers` **0 改善**。→ **S2 劣于 S1**，故不采纳。

---

## 四、Before / After 汇总（用户 §六）

| 指标 | **Before（S0）** | **After（S1）** |
|---|---:|---:|
| **keyword count**（新增 / 总） | 134 / 289 | **133 / 288** |
| **collision count**（跨 canonical 重复 / 新增词跨重复 / **子串冲突**） | 1 / 0 / **11** | 1 / 0 / **10** ✅ |
| `DIRECT` | 55 | **55**（未变） |
| `DERIVED` | 454 | **454**（未变） |
| `AMBIGUOUS` | 2 | **2**（未变） |
| `UNKNOWN` | 86 | **86**（未变） |
| `NOT_AVAILABLE` | 98 | **98**（未变） |
| **有 canonical driver 的 cycle 数** | **77 / 79** | **77 / 79**（未变） |
| **52 个 Canonical Campaign driver coverage** | **52 / 52** | **52 / 52**（未变） |
| `DEMAND_SURGE` 计数 | 62 | **63**（+1） |
| `SUPPLY_CONTRACTION` 计数 | 69 | 69（未变） |
| **SA Calibration 五态**（对已发布 SA v0.3 基线） | `SUPPORTED 4 / STRICT 1 / PARTIAL 40 / THEME_ONLY 10 / INSUFFICIENT 115 / NO_VALID 226` | `SUPPORTED 4 / STRICT 1 / **PARTIAL 41** / THEME_ONLY 10 / INSUFFICIENT 115 / **NO_VALID 225**` |
| **`STRUCTURAL_SUPPORTED` / `STRICT`** | **4 / 1** | **4 / 1（未变）** ✅ |
| **`driver=MISMATCH → PARTIAL`** | **0** | **0** ✅ **继续保持 = 0** |
| 无 driving 文本的 cycle | 0 | **0** |
| 仍无 canonical driver 的 cycle | 2 | **2**（均非数据缺口） |

> **★ 唯一实质变化**：`C-2020-SEMI-EQUIPMENT` 的 `canonical_drivers` 由 `['POLICY_DRIVEN']`
> 变为 **`['DEMAND_SURGE', 'POLICY_DRIVEN']`**；连带 1 条 SA 组合由 `NO_VALID` → `STRUCTURAL_PARTIAL`。
> **五态分布完全不变**、**SUPPORTED / STRICT 完全不变**、**campaign coverage 完全不变**。

---

## 五、验证结果（全 PASS）

| 检查 | 结果 |
|---|---|
| **Driver Canonicalization v0.3 `--check` ×3** | **PASS ×3**（deterministic） |
| **Rule Calibration v0.3 `--check` ×3** | **PASS ×3**（deterministic） |
| `validate_structural_analogy_v0_3` | **PASS** |
| **`validate_structural_analogy_semantics`** | **PASS**（1580/1580；S1–S14 全绿；**S14 = 0**） |
| `validate_db` | **PASS**（3 条 warning 未新增） |
| `validate_timeline_export` | **PASS** |
| `validate_batch_research` / `validate_promotion_manifest` / `check_doc_schema_consistency` / `validate_current_research` | **PASS** |
| `validate_monorepo_integrity` / `refresh --check` / `intake --check` | **PASS** |
| validator tests | **PASS**（44/44） |
| `validate_governance_gates` | **PASS** |
| **v0.1 / v0.2 byte-identical** | **PASS** —— `historical_driver_canonicalization_v0_1/v0_2` · `ledger_v0_1/v0_2` 全部 `git diff --quiet` **UNCHANGED** |
| **未改动**：Rule Set v0.2/v0.3 · Calibration v0.2 · **SA research v0.3** · **SA explanations v0.3** | **PASS**（全部 UNCHANGED） |

---

## 六、最终结论（用户 §七）

> ## **`扩产` 保留在 `DEMAND_SURGE`（方案 A）；`扩产周期` 从 canonical keyword mapping 中删除（方案 D）。**

**为什么**：

1. **`扩产周期` 贡献 0 条独有覆盖** —— 其唯一命中文本已被 `扩产` 完全覆盖（严格子集）。
2. **`扩产周期` 的 canonical 归属方向错误** —— 「产能扩张」与「供给收缩」机制相反；
   它把一条本应得到 `DEMAND_SURGE` 的文本推入多命中 `DERIVED`，**直接造成
   `C-2020-SEMI-EQUIPMENT` 的需求机制不可见**。
3. **`扩产` 有决定性证据支持其 `DEMAND_SURGE` 归属** ——
   ① 研究自身标题「晶圆厂扩产 → 「卡脖子」上游」；② v0.1 既有惯例（装机/并网/招标/采购 同为观察者相对的客户侧动作）；
   ③ 删除 `扩产周期` 后该词使 `C-2020-SEMI-EQUIPMENT` 获得与研究标题一致的 `DEMAND_SURGE`，且**无数据损失**。
4. **一留一删，不是「机械归到同一 canonical」** —— 删除理由由**真实命中文本**证明。
5. **最小影响**：仅 1 条 ledger 条目变化；**五态分布、SUPPORTED/STRICT、campaign coverage 全部不变**；
   **无任何负面变化**；`driver=MISMATCH → PARTIAL` **继续保持 = 0**。

**已记录、未处理**：
- ⚠️ `扩产` 的**系统性误命中风险**（未来「硅料扩产」类文本）—— 与 v0.1 既有「装机/招标/采购」同类，
  属 multi-hit disambiguation / 词表细化范围，**留待后续**。
- ⚠️ 其余 **5 项 substring collision**（`增长/负增长` · `整治/整治提升` · `出口/出口管制` ·
  `采购/装备采购` · `储备/黄金储备`）—— **本轮未处理**（用户 §五 明确禁止）。
- ⚠️ **SA v0.3 产物仍相对当前 driver 链过期**（`structural_analogy_research_v0_3.json` /
  `..._explanations_v0_3.json` 未重新生成）—— 须由 **SA v0.4** 消费。

---

## 七、本轮严格未做

- ❌ 未处理其余 5 项 substring collision；❌ 未进入 6 项 multi-hit disambiguation；
- ❌ 未生成 **SA v0.4**；❌ 未刷新 **Time Observation**；
- ❌ 未修改 **Rule Set v0.3**；❌ 未修改 **taxonomy**；❌ 未修改 **DB schema**；
- ❌ 未重新研究 **R01**；❌ 未修改 **v0.1 / v0.2**；
- ❌ 未为改善 SA 数量而放宽标准（本次唯一实质变化由**删除方向错误的关键词**产生，属**收紧**而非放宽）；
- ❌ 未改动 canonical vocabulary（仍 9 项）。

---

*`扩产` / `扩产周期` 语义裁决 · revision `v0.3-r2` · 2026-09-23 · 未生成 SA v0.4 · 未刷新 Time Observation*
