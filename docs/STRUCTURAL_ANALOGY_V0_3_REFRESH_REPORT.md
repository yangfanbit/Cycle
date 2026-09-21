# Structural Analogy v0.3 — R01 扩展 Universe 刷新报告

> | 项目 | 值 |
> |---|---|
> | **性质** | **Research Layer 刷新**（不是 Product schema / export contract） |
> | **规则集** | **`Structural Analogy Rule Set v0.2`（冻结，未修改）** · `structural-analogy-ruleset-v0.2` |
> | **新版本** | **Structural Analogy v0.3**（Research + Explanations） |
> | **依据** | `docs/R01_GOVERNANCE_CONSISTENCY_REVIEW_v0_1.md` · `docs/R01_GOVERNANCE_GATES_v0_1.md` |
> | **唯一变化** | **Historical Universe 由 17 cycle 扩容至 79 cycle**（R01-01~R01-06 全部纳入） |
> | **未修改** | Rule Set v0.2 · Research v0.1/v0.2 · Explanations v0.1/v0.2 · Rule Calibration v0.2 · Driver Canonicalization v0.1 / Ledger v0.1 · **canonical DB** · **Timeline Export Contract v1.0** · Research Model v1.0 · Schema · Protocol · taxonomy · CMTR v1 |
> | **未刷新** | **Time Observation**（按要求未动） |
> | **禁止** | similarity score · ranking · probability · 预测 · 胜率 · 涨跌判断 · 推荐 · 买卖信号 |

---

## 0. 执行摘要

| 项 | v0.2 | **v0.3** |
|---|---:|---:|
| Historical cycles | 17 | **79**（52 campaigns + 27 research_candidates） |
| Current candidates | 5 | 5 |
| **Pairs** | 85 | **395** |
| STRUCTURAL_SUPPORTED | 4 | **4** |
| STRICT_STRUCTURAL_SUPPORTED | 1 | **1** |
| STRUCTURAL_PARTIAL | 36 | **89** |
| THEME_ONLY | 3 | **6** |
| INSUFFICIENT_EVIDENCE | 5 | **145** |
| NO_VALID_CORRESPONDENCE | 37 | **151** |
| 跨 Macro Theme 结构对应 | 3 | **88** |
| 旧关系变化 | — | **0（85/85 逐条一致）** |

**三个最重要结论**：
1. **非回归 100% 通过** —— v0.2 已覆盖的 85 个组合在 v0.3 中**逐条状态相同**（规则与数据均未变）。
2. **跨族结构对应从 3 增至 88** —— R01 扩容**显著提升**了跨 Macro Theme 的机制型类比空间。
3. **发现 Rule Set v0.2 一处真实缺陷**（§8 文本 vs §7 指定实现不一致），**只记录、未修改**（见 §5）。

---

## A. 新增 / 删除 / 保留的 Analog 关系数量

| 类别 | 数量 | 说明 |
|---|---:|---|
| **保留（不变）** | **85** | v0.2 的 17 cycle × 5 candidate —— **状态逐条相同**（0 变化） |
| **新增（R01 带来）** | **310** | 62 个新 cycle × 5 candidate |
| **删除** | **0** | 无任何旧关系被移除 |
| **合计** | **395** | |

**新增部分的分布**（310 pairs）：

| status | 数量 |
|---|---:|
| STRUCTURAL_SUPPORTED | 0 |
| STRUCTURAL_PARTIAL | **53** |
| THEME_ONLY | 3 |
| INSUFFICIENT_EVIDENCE | **140** |
| NO_VALID_CORRESPONDENCE | 114 |

**结构对应总量**（SUPPORTED + PARTIAL）= **93**，其中 **53（57%）由 R01 新增 cycle 贡献**。

---

## B. 跨 Macro Theme Analog（ThreeC 核心价值）

**跨族结构对应 = 88 条**（v0.2 仅 3 条）。

| candidate | 跨族结构对应数 |
|---|---:|
| `CC-2026-COMPUTE-POWER` | 20 |
| `CC-2026-EMBODIED-AI` | 18 |
| `CC-2026-OPTICAL-LINK` | 18 |
| `CC-2026-BCI-MEDTECH` | 17 |
| `CC-2026-OFFSHORE-WIND` | 15 |

**历史侧 Macro Theme 分布**（跨族对应的另一端）：
`汽车 16 · 消费 15 · 高端装备 9 · 金融 7 · 电子 7 · 资源 7 · 国防军工 6 · 信息通信 6 · 电力设备 3 · 医药健康 1 ·（RC 无 root 11）`

### B.1 机制型 Analog 分类（按 driver 交集）

| 机制 | 结构对应数 | 其中跨族 | 说明 |
|---|---:|---:|---|
| **`POLICY_DRIVEN`** | **30** | **28** | 最强跨族机制轴 —— 政策驱动的结构跨 汽车/消费/资源/军工/金融 等族反复出现 |
| **`DEMAND_SURGE`** | **15** | **14** | 需求放量型结构（含 `C-2020-MIL-EQUIP-ORDER` 的军品订单） |
| **`INDUSTRY_UPGRADE`** | 6 | 5 | 产业升级 / 国产替代 |
| **`TECH_BREAKTHROUGH`** | 6 | 4 | 技术突破 |
| **`SUPPLY_CONTRACTION`** | 2 | 2 | 供给收缩（R01 新增资源/化工 cycle 的贡献） |

> **同机制交集 ≠ 结构对应** —— 上表**只统计**已同时通过 Rule Set v0.2 §7/§8 的组合。
> **未出现** `CYCLE_REVERSAL` / `VALUATION_RESET` / `EVENT_CATALYST` 的跨族结构对应（其交集均为 `PERIPHERAL_OVERLAP`，按 §3.3 **不计为结构支持**）。

### B.2 四个 STRUCTURAL_SUPPORTED（含唯一 STRICT）

| candidate | historical cycle | theme relation | driver | seq | event |
|---|---|---|---|---|---|
| `CC-2026-BCI-MEDTECH` | `C-2023-AD` | **跨族** | **MATCH / CORE_EQUIVALENT** ★STRICT | PARTIAL | PARTIAL |
| `CC-2026-EMBODIED-AI` | `C-2023-AD` | **跨族** | PARTIAL / MULTI_MECHANISM | MATCH | PARTIAL |
| `CC-2026-OPTICAL-LINK` | `C-2025-ROBOTAXI` | **跨族** | PARTIAL / MULTI_MECHANISM | MATCH | PARTIAL |
| `CC-2026-OPTICAL-LINK` | `C-2023-COMM-OPTICAL` | 同族 | PARTIAL / MULTI_MECHANISM | PARTIAL | PARTIAL |

> **3/4 的 STRUCTURAL_SUPPORTED 是跨族** —— 与 ThreeC「从历史周期里找结构，而不是找同名主题」的定位一致。
> 唯一 STRICT 是 `CC-2026-BCI-MEDTECH × C-2023-AD`（**脑机接口 × 智能驾驶**，机制集合完全相等且均有 DIRECT provenance）—— **跨族**。

---

## C. 哪些新增 R01 Campaign 最明显改变了结构空间

**按「新增结构对应数」排序**：

| # | historical cycle | family | 新增结构对应 | 关键机制 |
|---:|---|---|---:|---|
| 1 | **`C-2020-MIL-EQUIP-ORDER`** | 国防军工（R01-06） | **5（全部 5 个 candidate）** | `DEMAND_SURGE`（军品订单放量）—— **唯一对全部 5 个 current candidate 都形成结构对应**的新增 cycle |
| 2 | `C-2018-CONS-HOG-AFRICAN` | 消费（R01-04） | 4 | 供给端自然周期（猪周期） |
| 3 | `C-2021-CONS-HOG-REVERSAL` | 消费（R01-04） | 4 | 供给端自然周期（反转段） |
| 4 | `C-2020-FIN-BANK-CREDIT` | 金融（R01-05） | 4 | 信用周期 |
| 5 | `C-2016-HIEQ-CONSTR` | 高端装备（R01-01） | 4 | 更新周期 + 出口替代 |
| 6–15 | `C-2019-CONS-BAIJIU-CORE` · `C-2019-SEMI-LOCALIZATION` · `C-2020-RES-LITHIUM` · `C-2023-HIEQ-HUMANOID`（各 3）· `C-2016-CONS-BAIJIU-UPGRADE` · `C-2020-SEMI-EQUIPMENT` · `C-2023-FIN-SOE-VALUATION` · `C-2020-HIEQ-AUTOMATION` · `C-2020-RES-RAREEARTH` · `C-2021-RES-CHEM-DUALCTRL`（各 2） | — | 2–3 | — |

**按 rule family 汇总（新增结构对应）**：
`消费 16 · 高端装备 10 · 金融 7 · 资源 7 · 国防军工 6 · 半导体 6 · 面板 1`

### C.1 最显著的结构空间变化：`C-2020-MIL-EQUIP-ORDER`

- 对 **全部 5 个 current candidate** 均形成 `STRUCTURAL_PARTIAL`；
- 其中 `CC-2026-COMPUTE-POWER` 与 `CC-2026-OPTICAL-LINK` 的 driver 交集为 **`DEMAND_SURGE`（历史 primary mechanism）→ `PARTIAL / PRIMARY_MECHANISM_OVERLAP`**；
- 另 3 个 candidate 的 driver 为 `MISMATCH`，但因 lifecycle/sequence/event 维度支持数 ≥2 仍被判 `STRUCTURAL_PARTIAL`
  → ★ **这正是 §5 记录的规则缺陷的典型实例**（见下）。

### C.2 新增的 3 个 `THEME_ONLY`

v0.3 的 6 个 `THEME_ONLY` 中，3 个来自新增 cycle —— 均为**同族但结构不成立**，符合 §9 的事后派生语义（同族 ≠ 相似）。

---

## D. 旧 Analog 因 R01 扩充的解释变化

### D.1 状态层：**0 变化**

v0.2 已覆盖的 **85 个组合逐条状态相同**（含 4 个 SUPPORTED、36 个 PARTIAL、3 个 THEME_ONLY、5 个 INSUFFICIENT、37 个 NO_VALID）。
**没有任何旧 analog 被升级或降级** —— 因为规则未变、那些 cycle 的数据未变。

### D.2 解释空间层：**显著扩大**

| v0.2 的 STRUCTURAL_SUPPORTED | v0.3 同候选结构对应总数 | 其中 v0.2 时代 | **R01 新增** |
|---|---:|---:|---:|
| `CC-2026-BCI-MEDTECH × C-2023-AD` | 18 | 9 | **+9** |
| `CC-2026-EMBODIED-AI × C-2023-AD` | 19 | 8 | **+11** |
| `CC-2026-OPTICAL-LINK × C-2025-ROBOTAXI` | 19 | 6 | **+13** |
| `CC-2026-OPTICAL-LINK × C-2023-COMM-OPTICAL` | 19 | 6 | **+13** |

> **结论**：旧 analog 的**绝对结论未变**，但其**相对解释力被稀释** —— 同一 candidate 的结构对应集合从 6–9 个扩展到 18–19 个。
> 这**不是**「旧 analog 变弱」，而是**历史结构空间变丰富**。**不得**据此对旧 analog 重新排序或降级（Rule Set §15 禁止 ranking）。

---

## E. 发现的 Rule Set v0.2 缺陷（**只记录，未修改**）

### E.1 缺陷 1：§8 文本与 §7 指定实现不一致（**真实缺陷**）

| 项 | 内容 |
|---|---|
| **§8 文本** | `Structural Partial` 要求 **`Driver ∈ {MATCH, PARTIAL}`**（`PERIPHERAL_OVERLAP` 不算） |
| **§7 指定实现** | `build_structural_analogy_rule_calibration_v0_2.py::level_v2()`（**被 §7 声明为权威**） |
| **实现末段** | `if n_support >= 2: return "STRUCTURAL_PARTIAL"` —— **不检查 driver** |
| **后果** | **`driver = MISMATCH` 仍可被判 `STRUCTURAL_PARTIAL`**（只要 lifecycle/sequence/event 支持数 ≥2） |

**量化影响**：

| | STRUCTURAL_PARTIAL 总数 | 其中 `driver=MISMATCH` | 占比 |
|---|---:|---:|---:|
| v0.2 | 36 | 10 | **27.8%** |
| **v0.3** | **89** | **50** | **56.2%** |

→ **缺陷在 R01 扩容后被放大 2 倍**（27.8% → 56.2%），因为新 cycle 的 driver 词表覆盖更差，`MISMATCH` 更多。

**典型实例**：`CC-2026-BCI-MEDTECH × C-2020-MIL-EQUIP-ORDER`（`lifecycle=MISMATCH`、`driver=MISMATCH`、`seq=PARTIAL`、`ev=PARTIAL`）→ 被判 `STRUCTURAL_PARTIAL`。

**建议（本轮不做）**：
- 二选一并**新建 Rule Set v0.3**（**不得就地改 v0.2**）：
  - (a) **以文本为准**：实现补上 `and d_dr in DRIVER_GOOD` 前置条件 → 预计大量 `PARTIAL` 降为 `THEME_ONLY` / `NO_VALID_CORRESPONDENCE`；
  - (b) **以实现为准**：修订 §8 文本，显式允许「driver MISMATCH 但其余 ≥2 维支持」的 `PARTIAL`，并说明其语义。
- **在 v0.3 决定前，v0.3 产物沿用冻结实现**（保持与 v0.2 可比）。

### E.2 缺陷 2：Driver Canonicalization 词表覆盖不足（**覆盖缺陷，非逻辑缺陷**）

| 项 | 内容 |
|---|---|
| **现象** | **24 / 79 cycle（30.4%）无任何 canonical driver** → 该 cycle × 5 candidate = **120 组合被迫 `INSUFFICIENT_EVIDENCE`** |
| **子因 A：driving 相位文本缺失**（18 cycle） | 这些 cycle 在 export 中 `drivers.start` + `drivers.accelerator` **均为空** → 无文本可映射 |
| **子因 B：关键词词表未覆盖 R01 词汇**（6 cycle） | 有 driving 文本，但全部落入 `UNKNOWN` |

**子因 B 的具体词汇缺口**（v0.1 关键词表**未包含**）：

| cycle | 未被识别的词汇 | 应属机制（**未写入，仅建议**） |
|---|---|---|
| `C-2020-RE-DEBT-RISK` | 「三道红线」「房地产金融审慎管理」「贷款集中度管理」「信用债违约」 | `POLICY_DRIVEN` / `CYCLE_REVERSAL` |
| `C-2019-RES-DYE-SHOCK` | 「爆炸事故」「关闭化工园区」「整治提升方案」 | `SUPPLY_CONTRACTION` / `EVENT_CATALYST` |
| `C-2020-CONS-BEAUTY-CN` | 「条例」「规范」「上市」「渠道红利」 | `POLICY_DRIVEN` / `INDUSTRY_UPGRADE` |
| `C-2022-CONS-SERVICE-REBOUND` | 「疫情防控措施优化」「旅游出游人次」「低基数」 | `POLICY_DRIVEN` / `CYCLE_REVERSAL` |
| `RC-2019-MIL-PARADE-70` | 「阅兵」「纪念大会」「装备展示」 | `EVENT_CATALYST` |
| `RC-2024-SECONDARY` | （driving 文本为 `NOT_AVAILABLE` 语义） | — |

**性质判定**：**不是逻辑缺陷** —— Rule Set §11 明确规定 `NOT_AVAILABLE ≠ NO_PATTERN`，实现**正确地**返回 `INSUFFICIENT_EVIDENCE` 而非猜测。
**是覆盖缺陷**：驱动词表（`Historical Driver Canonicalization v0.1`）在 **17-cycle 时代**校准，**未随 R01 扩表**。

**建议（本轮不做）**：
- 新建 `Historical Driver Canonicalization v0.3`（**扩展关键词 + 保持词表不变**），并**重新做 Rule Calibration** 以验证等级分布是否稳定；
- **不得**在 v0.2 上就地改关键词（会使 v0.1/v0.2 产物不可复现）；
- 同时评估「18 个 cycle 的 driving 相位 drivers 为空」是否属于 **export 数据补全**需求（属 Canonical/Export 层，非 SA 层）。

### E.3 未发现的缺陷（**通过**）

| 检查 | 结果 |
|---|---|
| §1 Theme Relation 与 Structural Status 解耦 | ✅ theme-blind 运行 **0 个 Structural Status 变化** |
| §3.3 `PERIPHERAL_OVERLAP` 不计入结构支持 | ✅ 0 违规 |
| §5 `SET_ONLY` 不得当作 `SEQUENCE_MATCH` | ✅ 0 违规 |
| §6 `SINGLE_TYPE_ONLY` 不得作为 event `PARTIAL` | ✅ 0 违规 |
| §7 `STRUCTURAL_SUPPORTED` 全部条件 | ✅ 4/4 满足（含 `not key_mismatch`、`drv_strong`、`has_direct`） |
| §10 负控制 | ✅ 2/2 保持非结构状态（`NO_VALID_CORRESPONDENCE` / `THEME_ONLY`） |
| §12 Market/Temporal 不参与 | ✅ governance 元数据仅出现在 `supplementary` / `governance_context` |
| §15 禁止事项 | ✅ 无 score / ranking / probability 字段 |

---

## F. Governance 元数据的接入方式（`governance-gates-v0.1`）

**接入位置**：`matrix[].supplementary.governance_gates` 与 `explanations[].governance_context`。

| 字段 | 来源 | 角色 |
|---|---|---|
| `market_evidence_state` | G1-1（`A_SHARE_MARKET` / `INDUSTRY_COMPANY_ONLY` / `NONE`） | **SUPPLEMENTARY_ONLY** |
| `beta_level` | G1-3（`0`–`3`） | **SUPPLEMENTARY_ONLY** |
| `peak_state` / `end_state` | G2-1（`EXACT` / `WINDOW` / `NULL`） | **SUPPLEMENTARY_ONLY** |
| `result` | G1-5（`result=weak` = 方向为负） | **SUPPLEMENTARY_ONLY** |

**三条硬约束（已写入产物 `note`，并由校验器 A16 检查）**：
1. **不参与 Structural Status**（Rule Set v0.2 §12：Market / Temporal 为非正式维度）；
2. **`beta_level = 1` ≠ Alpha**（未做 Beta 调整、未剥离风格因子）；
3. **`result = weak` 不降低参与结构类比的资格** —— 上行与下行 cycle **同等参与**（本版中 `C-2020-RE-DEBT-RISK` 与 `C-2022-SEMI-DOWNTURN` 均正常参与并产生结构对应）。

**★ 注意**：`governance` 字段**未进入** `exports/timeline_export_v1.json`（会触发 `CAMPAIGN_FIELDS` 白名单 FAIL，属 Export Contract 变更）→ SA / TO **直接读取研究级 JSON**（与 `time_observation_patterns_v0_1.json` 同类做法）。

---

## G. 产物与版本管理

| 文件 | 性质 | 状态 |
|---|---|---|
| `research/research/reports/structural_analogy_research_v0_3.json` | **新** | 395 组合，含 mechanism_analogs / cross_macro_theme_analogs / per_candidate / regression_controls / evidence_cards |
| `research/research/reports/structural_analogy_research_candidates_v0_3.csv` | **新** | 395 行（含 governance 列） |
| `research/research/reports/structural_analogy_explanations_v0_3.json` | **新** | Product-facing，395 explanations |
| `research/research/reports/historical_driver_canonicalization_v0_2.json` | **新** | 79 cycle（**同规则、全 universe**） |
| `research/research/reports/historical_driver_evidence_ledger_v0_2.json` | **新** | 541 entries |
| `research/scripts/build_structural_analogy_research_v0_3.py` | **新** | 生成器（`--check` 支持） |
| `research/scripts/build_structural_analogy_explanation_v0_3.py` | **新** | 生成器（`--check` 支持） |
| `research/scripts/canonicalize_historical_drivers_v0_2.py` | **新** | 生成器（`--check` 支持） |
| `research/scripts/validate_structural_analogy_v0_3.py` | **新** | 校验器 A1–A16 |

**逐字节保留（未改动）**：`structural_analogy_rule_set_v0_2.md` · `structural_analogy_rule_calibration_v0_2.json` ·
`structural_analogy_research_v0_1/v0_2.json` · `structural_analogy_explanations_v0_1/v0_2.json` ·
`historical_driver_canonicalization_v0_1.json` · `historical_driver_evidence_ledger_v0_1.json`
（已用 `git diff --quiet` **逐文件确认 UNCHANGED**）。

---

## H. 验证结果

| 检查 | 结果 |
|---|---|
| `validate_db` | **PASS**（3 条 warning 与治理修复后完全相同，**未新增**） |
| `validate_timeline_export` | **PASS** |
| `validate_batch_research` | **PASS** |
| `validate_promotion_manifest` | **PASS** |
| `check_doc_schema_consistency` | **PASS** |
| `validate_current_research` | **PASS** |
| `validate_monorepo_integrity` | **PASS** |
| `intake --check` | **PASS** |
| validator tests | **PASS**（44/44） |
| `refresh --check` | **PASS** |
| `validate_governance_gates` | **PASS**（WARN 1 = `C-2019-AD` 历史残留） |
| **`validate_structural_analogy_v0_3`** | **PASS**（FAIL 0 / WARN 0）· A1–A16 全通过 |
| SA v0.3 生成器 `--check` | **PASS**（逐字节 deterministic） |
| Explanations v0.3 `--check` | **PASS** |
| Driver Canonicalization v0.2 `--check` | **PASS** |
| **v0.1 / v0.2 逐字节保留** | **PASS**（`git diff --quiet` 全部 UNCHANGED） |
| **canonical DB 未改动** | **PASS**（`git status` 无 DB 变更） |
| **Export Contract 未改动** | **PASS**（`exports/` 无变更） |
| **Research Model / Schema / Protocol / taxonomy 未改动** | **PASS** |

**关键确认**：
- ✅ 52 Campaign **全部纳入**（`historical_profiles` 与 export universe 集合相等，校验器 A3）；
- ✅ **非回归**：v0.2 已覆盖的 85 组合 **逐条状态相同**（校验器 A12）；
- ✅ **负控制保持**（校验器 A11）；
- ✅ **Time Observation 未刷新**。

---

## I. 本轮严格未做

- ❌ 未修改 **Rule Set v0.2**（含其文本与 calibration 实现）；
- ❌ 未修改 **Research v0.1/v0.2** · **Explanations v0.1/v0.2** · **Driver Canonicalization v0.1** · **Ledger v0.1**；
- ❌ 未修改 **canonical DB**（`campaigns` / `evidences` / `sources` / `themes` 零改动）；
- ❌ 未修改 **Timeline Export Contract v1.0** / `exports/timeline_export_v1.json`；
- ❌ 未修改 **Research Model v1.0** / **Schema** / **Protocol** / **taxonomy** / **CMTR v1**；
- ❌ **未刷新 Time Observation**；
- ❌ 未新增 driver vocabulary / taxonomy / mapping；
- ❌ 未输出预测 / 概率 / 胜率 / 涨跌判断 / 推荐 / 买卖信号 / 相似度评分 / 排名；
- ❌ 未因发现缺陷而修改 v0.2（**只记录**）。

---

## J. 下一步建议（供决策，本轮不执行）

1. **Rule Set v0.3 决策**：解决 §E.1 的 §8 文本 vs 实现不一致（二选一），并**新建** v0.3 规则集 + 重新 Calibration。
2. **Driver Canonicalization v0.3**：扩展关键词覆盖 R01 词汇（§E.2 子因 B），并评估 18 个 cycle 的 driving drivers 空缺是否属 export 数据补全。
3. **SA v0.4**：在 (1)(2) 完成后重跑，预期 `INSUFFICIENT_EVIDENCE` 显著下降、`STRUCTURAL_PARTIAL` 结构更纯净。
4. **Product 侧**：v0.3 已可消费（契约语义与 v0.2 一致，仅 universe 扩大 + 新增 supplementary `governance_context`）。
5. **Time Observation**：如需刷新，建议在 SA v0.4 之后统一进行。

---

*Structural Analogy v0.3 · 规则集沿用冻结的 `structural-analogy-ruleset-v0.2` · 未刷新 Time Observation*
