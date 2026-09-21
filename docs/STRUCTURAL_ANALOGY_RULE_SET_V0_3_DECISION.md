# Structural Analogy Rule Set v0.3 — 决策与 Calibration 报告

> | 项目 | 值 |
> |---|---|
> | **性质** | **Rule Set v0.3 决策 + Driver Canonicalization v0.3 + Rule Calibration v0.3 + 语义一致性校验** |
> | **新规则集** | **`Structural Analogy Rule Set v0.3`**（`structural-analogy-ruleset-v0.3`，effective 2026-09-22） |
> | **依据** | `docs/STRUCTURAL_ANALOGY_V0_3_REFRESH_REPORT.md` §5（E.1 / E.2） |
> | **未修改** | Rule Set v0.2 文本 · Calibration v0.2 · Research v0.1/v0.2/**v0.3** · Explanations v0.1/v0.2/**v0.3** · Driver Canonicalization v0.1/v0.2 · Ledger v0.1/v0.2（**逐字节保留，已 `git diff --quiet` 逐文件确认**） |
> | **未修改** | canonical DB · `exports/timeline_export_v1.json` · Export Contract v1.0 · Research Model v1.0 · Schema · Protocol · taxonomy · CMTR v1 |
> | **未做** | **不生成 SA v0.4** · 不覆盖 SA v0.3 · **不刷新 Time Observation** · 不回改 R01 Campaign |

---

## 1. Rule Set v0.3 最终规则

完整文本：`research/research/methodology/structural_analogy_rule_set_v0_3.md`
权威实现：`research/scripts/build_structural_analogy_rule_calibration_v0_3.py::level_v3()`

### 1.1 判定顺序（**强制**，自上而下，命中即返回，每行恰好命中一条）

| 序 | 结果 | 条件 |
|---|---|---|
| **R1** | `INSUFFICIENT_EVIDENCE` | `NOT_AVAILABLE` 维度数 ≥ 2，**或** `Driver = NOT_AVAILABLE` |
| **R2** | `STRUCTURAL_SUPPORTED` | `strict` 或 `supported`（见 §1.3） |
| **R3** | `STRUCTURAL_PARTIAL` | **`Driver ∈ {MATCH, PARTIAL}`** **且** `Evidence Sequence ∈ {MATCH, PARTIAL}` **且** 维度支持数 ≥ 2 |
| **R4** | `THEME_ONLY` / `NO_VALID_CORRESPONDENCE` | 其余 → `SAME_MACRO_THEME → THEME_ONLY`；`CROSS_MACRO_THEME → NO_VALID_CORRESPONDENCE` |

### 1.2 各状态定义（无歧义）

| 状态 | 定义 |
|---|---|
| **`STRUCTURAL_SUPPORTED`** | `Lifecycle = MATCH` **且** （`Driver = MATCH` 或 `Driver = PARTIAL` 且 `quality = MULTI_MECHANISM`）**且** `Evidence Sequence ∈ {MATCH,PARTIAL}` 且 `subtype ∈ {SEQUENCE_MATCH, SEQUENCE_PARTIAL}` **且** `Event Structure ∈ {MATCH,PARTIAL}` **且** 非 Lifecycle 维度 ≥2 有支持 **且** 无核心 `MISMATCH`（lifecycle/driver/event）**且** `has_direct` |
| **`STRICT_STRUCTURAL_SUPPORTED`** | 同 `STRUCTURAL_SUPPORTED`，但 **`Driver = MATCH`**（单独计数） |
| **`STRUCTURAL_PARTIAL`** | **`Driver ∈ {MATCH, PARTIAL}`** **且** **`Evidence Sequence ∈ {MATCH, PARTIAL}`** **且** **维度支持数 ≥ 2**；**不存在任何 fallback 升级** |
| **`THEME_ONLY`** | 结构支持不足 **且** `Theme Relation = SAME_MACRO_THEME`（**事后**派生） |
| **`NO_VALID_CORRESPONDENCE`** | 结构支持不足 **且** `Theme Relation = CROSS_MACRO_THEME`（**事后**派生） |
| **`INSUFFICIENT_EVIDENCE`** | `NOT_AVAILABLE` 维度 ≥2，或 `Driver = NOT_AVAILABLE`（**最高优先级**） |

### 1.3 硬约束（v0.3 明确列出）

1. **`Driver = MISMATCH` 不得进入 `STRUCTURAL_PARTIAL`** ← ★ v0.3 核心
2. **`PERIPHERAL_OVERLAP` 不计入 structural support**
3. **核心 `MISMATCH` 不得被任何 fallback 升级**
4. `SET_ONLY` **不得**当作 `SEQUENCE_MATCH`
5. `SINGLE_TYPE_ONLY` **不得**作为 Event `PARTIAL`
6. `Theme Relation` **不参与** Structural Status（只在 R4 事后派生）
7. `Market` / `Temporal` / **`Governance`** **不参与** Structural Status
8. `UNKNOWN` / `NOT_AVAILABLE` **≠** 现象不存在；**不得**为降低 `INSUFFICIENT_EVIDENCE` 而猜测 driver

---

## 2. E.1 最终处理方式

### 2.1 裁决

> **以 §8 文字语义为准：`Driver = MISMATCH` 不得进入 `STRUCTURAL_PARTIAL`。**

**理由**：Structural Analogy 的目标是寻找「**机制 + 生命周期 + 证据结构**」真正具有结构对应关系的历史案例。
当**核心机制完全 MISMATCH** 时，其它维度的重叠**不足以**单独构成 Structural Partial ——
否则「同族 / 同类行情形状」会被误读为「机制结构对应」，正是 Rule Set §10 三条负控制命题要防的失效模式。

### 2.2 实现变更（**仅此一处语义修正**）

```
# v0.2 实现（含 fallback，放行 driver=MISMATCH）
    if d_dr in GOOD and d_sq in GOOD and n_support >= 2:  return "STRUCTURAL_PARTIAL"
    if d_dr == "PERIPHERAL_OVERLAP" or (d_lc in GOOD and n_support <= 1): return THEME_ONLY / NO_VALID
    if n_support >= 2:                                    return "STRUCTURAL_PARTIAL"   ← ★ 移除
    return "NO_VALID_CORRESPONDENCE"

# v0.3 实现（R3 以 Driver ∈ {MATCH, PARTIAL} 为硬前提）
    if d_dr in GOOD and d_sq in GOOD and n_support >= 2:  return "STRUCTURAL_PARTIAL"
    return THEME_ONLY if theme_rel == "SAME_MACRO_THEME" else "NO_VALID_CORRESPONDENCE"
```

**v0.3 相对 v0.2 的变更清单 = 1 项语义修正 + 2 项表达澄清**（判定顺序显式化；其余判据全部未改）。

---

## 3. Driver Canonicalization v0.3 变化

`research/scripts/canonicalize_historical_drivers_v0_3.py` → `historical_driver_canonicalization_v0_3.json` + `historical_driver_evidence_ledger_v0_3.json`

### 3.1 变更边界（**严格**）

| 项 | 状态 |
|---|---|
| canonical vocabulary（9 项 `narrativeType`） | **完全不变** |
| `mapping_status` 语义（DIRECT/DERIVED/AMBIGUOUS/UNKNOWN/NOT_AVAILABLE） | **完全不变** |
| 映射逻辑（命中数 → 状态；价格/行情结果 → NOT_AVAILABLE） | **完全不变** |
| `PRICE_ACTION` 排除逻辑（§15：价格结果不得作为 driver） | **完全不变** |
| v0.1 原有关键词 | **一个未删** |
| **新增** | **关键词表扩展**（逐条注明覆盖来源） |

**关键词扩展规模**：v0.1 基础 **128** 词 → 新增 **142** 词 → 合计 **270** 词（8 个 canonical driver 维度）。

### 3.2 重点覆盖的 R01 词汇（用户点名 + 实测缺口）

| 机制 | 新增关键词（部分） | 覆盖的实测缺口 |
|---|---|---|
| `POLICY_DRIVEN` | **三道红线** · 审慎管理 · **集中度** · 保交楼 · 因城施策 · 三支箭 · 第二支箭 · 交易商协会 · **疫情防控** · 新十条 · 措施优化 · 收储 · 储备 · 特别国债 · 条例 · 规范 · 纲要 · 行动计划 · 方案 · 整治 · 核查 · 环保 · 指标 · 配额 · 军民融合 · 混改 · 战略性重组 · 资产证券化 · 军品 · 装备采购 · 国防预算 · **阅兵** · 纪念大会 · 实体清单 · 出口管制 · 大基金 · 投资计划 | `C-2020-RE-DEBT-RISK` · `C-2020-CONS-BEAUTY-CN` · `C-2022-CONS-SERVICE-REBOUND` · `RC-2019-MIL-PARADE-70` · `C-2022-POWER-GRID` · `C-2019-SEMI-LOCALIZATION` 等 |
| `SUPPLY_CONTRACTION` | **停产** · 停工 · **关闭** · 关停 · **压减** · 削减 · 整治提升 · 惜售 · 锁货 · 现货稀少 · 供应受限 · 供需缺口 · 口岸关闭 · 进口量 · 能耗双控 · 双控 · 限电 · 去化 | `C-2019-RES-DYE-SHOCK` · `C-2020-RES-RAREEARTH` · `C-2020-RES-LITHIUM` · `C-2021-RES-CHEM-DUALCTRL` |
| `DEMAND_SURGE` | **关联交易** · 预付款 · 预付 · **合同负债** · 出游 · 人次 · 客流 · 门店 · 铺开 · 渠道 · GMV · 月活 · 用户 · 资本开支 · 扩产 · 固定资产投资 · 基站 · 持仓 | `C-2020-MIL-EQUIP-ORDER` · `C-2022-CONS-SERVICE-REBOUND` · `C-2023-CONS-VALUE-RETAIL` · `C-2019-COMM-5G` |
| `VALUATION_RESET` | **高股息** · 红利 · 资产荒 · 低利率 · 配置 · 增量资金 · 外资 · 去美元化 · 央行购金 · 黄金储备 · ETF · 实际利率 · 零利率 · 宽松 · 资产端 · 负债端 | `C-2024-FIN-BANK-DIVIDEND` · `C-2025-FIN-INSURANCE` · `C-2024-RES-GOLD-CB` |
| `TECH_BREAKTHROUGH` | 组网 · 入轨 · 首飞 · 可重复使用 · 大模型 · ChatGPT · GPT · Copilot | `RC-2024-MIL-COMMERCIAL-SPACE` · `C-2023-AI-COMPUTE-SEMI` |
| `CYCLE_REVERSAL` | 更新周期 · 替换窗口 · 更新替换 · 逆周期 · 周期底部 · 下行周期 · 增速放缓 · 增速转负 · 负增长 · 收缩 · 退坡 | `C-2016-HIEQ-CONSTR` · `C-2018-HIEQ-ROBOT-DOWN` · `C-2022-SEMI-DOWNTURN` |
| `EVENT_CATALYST` | **事故** · 爆炸 · 四中全会 · 十五五 · 成立 · 揭牌 | `C-2019-RES-DYE-SHOCK` · `C-2024-MIL-GROUP-RESTRUCTURE` · `RC-2024-MIL-COMMERCIAL-SPACE` |
| `INDUSTRY_UPGRADE` | 自主可控 · 业态 · 定价权 · 纳入因子 · MSCI · 确定性溢价 | `C-2016-CONS-BAIJIU-UPGRADE` · `C-2019-CONS-BAIJIU-CORE` · `C-2023-CONS-VALUE-RETAIL` |

### 3.3 ★ 关于 4 个 Canonical Campaign 的专项评估（用户要求）

用户要求单独评估：**这些已有 Canonical Campaign 的 driving driver 缺失，是否应由 Canonical / Export 数据补全，而不是由词表猜测。**

| Campaign | v0.2 状态 | 缺口性质 | **v0.3 结果** |
|---|---|---|---|
| `C-2020-CONS-BEAUTY-CN` | 无 canonical driver | **纯词表缺口**（`drivers` 文本齐全：条例 / 规范 / 渠道红利） | ✅ **已覆盖**（`POLICY_DRIVEN`） |
| `C-2022-CONS-SERVICE-REBOUND` | 无 canonical driver | **纯词表缺口**（疫情防控优化 / 出游人次） | ✅ **已覆盖**（`POLICY_DRIVEN`） |
| `C-2020-RE-DEBT-RISK` | 无 canonical driver | **纯词表缺口**（三道红线 / 贷款集中度 / 信用债违约） | ✅ **已覆盖**（`POLICY_DRIVEN`） |
| `C-2019-RES-DYE-SHOCK` | 无 canonical driver | **纯词表缺口**（爆炸事故 / 关闭园区 / 压减产能） | ✅ **已覆盖**（`SUPPLY_CONTRACTION`） |

> **★ 结论：这 4 个 Campaign 的缺口是「词表覆盖不足」，不是「export 数据缺失」** ——
> 其 `drivers.start` / `drivers.accelerator` 文本**齐全且为机制表述**，v0.3 词表扩展后**全部得到 canonical driver**。
> **无需 Canonical / Export 层补数据**。

**★ 真正属于 export 数据缺口的是 18 个 Research Candidate**（见 §4.4）—— 其 `drivers` 四个 bucket **全为空**，
**不应由词表猜测**，应由 Canonical / Export 层补全（**本轮不做**）。

---

## 4. Calibration v0.3 结果

`research/scripts/build_structural_analogy_rule_calibration_v0_3.py` → `structural_analogy_rule_calibration_v0_3.json` + `..._pairs_v0_3.csv`

### 4.1 校准设计（因子化，唯一差异可控）

| 组 | 规则 | driver 数据 |
|---|---|---|
| **A** | v0.2 实现（含 fallback） | Canonicalization **v0.2** ← **= SA v0.3 已发布基线** |
| **B** | v0.2 实现 | Canonicalization **v0.3** |
| **C** | **v0.3 实现** | Canonicalization v0.2 |
| **D** | **v0.3 实现** | Canonicalization **v0.3** ← **最终结果** |

→ `E1 = B→D`（**规则效应**）· `E2 = A→B`（**词表效应**）· `combined = A→D`

### 4.2 ★ E.1 修复前后（**证明 MISMATCH→PARTIAL 已彻底消除**）

| 指标 | before（v0.2 规则） | **after（v0.3 规则）** |
|---|---:|---:|
| `STRUCTURAL_PARTIAL` | 105 | **39** |
| **其中 `driver = MISMATCH`** | **48** | **0** ✅ |
| 其中 `driver = MISMATCH` **且跨族** | 47 | **0** ✅ |
| `STRUCTURAL_SUPPORTED` | 4 | **4（未变）** |
| `STRICT_STRUCTURAL_SUPPORTED` | 1 | **1（未变）** |
| 变化组合 | — | **67**（`PARTIAL→NO_VALID` 64 · `PARTIAL→THEME_ONLY` 2 · `NO_VALID→THEME_ONLY` 1） |

**★ 对照「已发布 SA v0.3」基线（A → C，同 v0.2 driver 数据）**：

| 指标 | 已发布 SA v0.3（v0.2 规则） | v0.3 规则 |
|---|---:|---:|
| `STRUCTURAL_PARTIAL` | **89** | **24** |
| **其中 `driver = MISMATCH`** | **50（56.2%）** | **0** ✅ |
| 其中跨族 | 49 | **0** |

> **结论**：**`driver = MISMATCH → STRUCTURAL_PARTIAL` 已彻底消除（50 → 0）**，
> 且 **`STRUCTURAL_SUPPORTED` / `STRICT` 完全未受影响（4 / 1）** —— 修复只作用于 `PARTIAL` 层，**未误伤任何强结构对应**。

### 4.3 E.2 修复前后（**词表覆盖**）

| 指标 | before（Canonicalization v0.2） | after（v0.3） |
|---|---:|---:|
| 有 canonical driver 的 cycle | 55 / 79 | **59 / 79** |
| 无 canonical driver 的 cycle | 24 | **20** |
| driving `UNKNOWN` | 85 | **23**（−62） |
| driving `DERIVED` | 140 | **200**（+60） |
| driving `DIRECT` | 42 | **45**（+3） |
| driving `NOT_AVAILABLE` | 31 | **29** |
| driving `AMBIGUOUS` | 0 | **1** |
| `INSUFFICIENT_EVIDENCE`（同 v0.2 规则下） | 145 | **125**（−20） |

**新增覆盖的 5 个 cycle**：`C-2019-RES-DYE-SHOCK` · `C-2020-CONS-BEAUTY-CN` · `C-2020-RE-DEBT-RISK` ·
`C-2022-CONS-SERVICE-REBOUND` · `RC-2019-MIL-PARADE-70`

> **★ 不以「让 INSUFFICIENT 越少越好」为目标** —— 减少的 20 条全部来自**真实词表缺口被补全**（原文本即为机制表述），
> **未**通过猜测 driver 或补造证据达成；剩余 **20 个 cycle 仍为 `INSUFFICIENT_EVIDENCE`**，**如实保留**。

### 4.4 ★ 仍无 canonical driver 的 20 个 cycle（**全部为 Research Candidate**）

| 子因 | 数量 | 说明 |
|---|---:|---|
| **A. export `drivers` 四个 bucket 全为空** | **18** | 属 **export 数据缺口** —— 应由 Canonical / Export 层补全，**不得由词表猜测** |
| **B. 有 driving 文本但多规则命中（`DERIVED` 无 canonical）或 `AMBIGUOUS`** | 2 | `RC-2025-MIL-PARADE-80` · `RC-2024-SECONDARY` |

**★ 关键：`by_kind` 全部为 `research_candidate`（18 / 20）—— 无一个 Canonical Campaign 缺 driver** ✅

### 4.5 其他校准检查

| 检查 | 结果 |
|---|---|
| **Theme 解耦**（§8） | ✅ theme-blind **0 个 Structural Status 变化**（`theme_relation_changed` 如实记录） |
| **负控制**（§7） | ✅ `CC-2026-EMBODIED-AI × C-2024-ROBOTAXI` = `NO_VALID_CORRESPONDENCE`；`CC-2026-OPTICAL-LINK × C-2019-COMM-5G` = `THEME_ONLY` |
| **Name-blind** | ✅ 0 变化（四个正式维度不读取名称） |
| **Event 规则**（§2.4） | ✅ `SINGLE_TYPE_ONLY` 均未作为 `PARTIAL`（校验器 S9） |
| **Sequence 规则**（§2.3） | ✅ `SET_ONLY` 均未当作 `SEQUENCE_MATCH`（校验器 S6） |
| **Driver 规则**（§2.2） | ✅ `PERIPHERAL_OVERLAP` 均未计入结构支持（校验器 S5） |
| **Supported / Strict / Partial 分布** | 见 §4.2（`SUPPORTED` / `STRICT` **未变**） |
| **Rule Sensitivity** | 见 `rule_sensitivity`（仅用于定位变化来源方向，**不得解释为性能变化**） |

### 4.6 维度分布（D 组，395 组合）

| 维度 | 分布 |
|---|---|
| `lifecycle` | `MATCH 142` · `PARTIAL 66` · `MISMATCH 107` · `COMPARISON_POINT_UNKNOWN 80` |
| `driver` | `MATCH 1` · `PARTIAL 66` · `PERIPHERAL_OVERLAP 124` · `MISMATCH 104` · `NOT_AVAILABLE 100` |
| `evidence_sequence` | `SEQUENCE_MATCH 40` · `SEQUENCE_PARTIAL 112` · `SET_ONLY 19` · `SEQUENCE_MISMATCH 34` · `NOT_AVAILABLE 190` |
| `event_structure` | `MATCH 1` · `PARTIAL 123` · `MISMATCH 156` · `NOT_AVAILABLE 115` |

---

## 5. v0.2 → v0.3 关键统计变化（汇总）

| 指标 | 已发布 SA v0.3（v0.2 规则 + v0.2 driver） | **新 v0.3（v0.3 规则 + v0.3 driver）** |
|---|---:|---:|
| `STRUCTURAL_SUPPORTED` | 4 | **4**（未变） |
| `STRICT_STRUCTURAL_SUPPORTED` | 1 | **1**（未变） |
| `STRUCTURAL_PARTIAL` | **89** | **39**（−50） |
| **其中 `driver = MISMATCH`** | **50** | **0** ✅ |
| `THEME_ONLY` | 6 | **9**（+3） |
| `INSUFFICIENT_EVIDENCE` | 145 | **125**（−20） |
| `NO_VALID_CORRESPONDENCE` | 151 | **218**（+67） |
| 变化组合总数 | — | **99** |

**变化归因**（99 条）：
- `STRUCTURAL_PARTIAL→NO_VALID_CORRESPONDENCE` **64** ← 主要为 **E.1 规则修正**（MISMATCH-PARTIAL 被正确降级）
- `INSUFFICIENT_EVIDENCE→NO_VALID_CORRESPONDENCE` **16** ← **E.2 词表扩展**（新获得 driver 后进入结构判定，但未达支持）
- `NO_VALID_CORRESPONDENCE→STRUCTURAL_PARTIAL` **12** ← **E.2 词表扩展**（新获得 driver 且满足 R3）
- `INSUFFICIENT_EVIDENCE→STRUCTURAL_PARTIAL` **4** ← **E.2 词表扩展**
- `STRUCTURAL_PARTIAL→THEME_ONLY` **2** · `NO_VALID_CORRESPONDENCE→THEME_ONLY` **1** ← E.1

---

## 6. `driver=MISMATCH → STRUCTURAL_PARTIAL` 是否彻底消除

> ### ✅ **已彻底消除。**

| 组 | 规则 | driver 数据 | MISMATCH-PARTIAL |
|---|---|---|---:|
| **A** | v0.2 | v0.2 | **50**（= SA v0.3 已发布基线） |
| **C** | **v0.3** | v0.2 | **0** |
| **D** | **v0.3** | v0.3 | **0** |

**三重确认**：
1. **因子化对照**：C 组（仅换规则、driver 数据不变）即为 0 → 证明**由规则修正直接消除**，与词表扩展无关；
2. **语义不变量 S14**（`validate_structural_analogy_semantics.py`）：全表扫描 `Driver = MISMATCH` 的 `STRUCTURAL_PARTIAL` 计数 = **0**；
3. **不变量 S1**：所有 `STRUCTURAL_PARTIAL` 均满足 `Driver ∈ {MATCH, PARTIAL}`。

---

## 7. Semantic Conformance Validator 结果

`research/scripts/validate_structural_analogy_semantics.py` —— **补齐 SA v0.3 Validator（A1–A16）未重算规则语义的缺口**。

### 7.1 方法（两层，互相独立）

**第 1 层 — 独立重算（Independent Recompute）**
本校验器**从 Rule Set v0.3 文本独立重新实现** `level_v3()`（**不 import** builder 的实现），
并对 **A / B / C / D 四组全部 1580 行**（395 组合 × 4 组）逐行重算，要求**与产物完全一致**。

**第 2 层 — 语义不变量（Semantic Invariants，直接由规则文本派生，不依赖任何实现）**

| ID | 不变量 | 结果 |
|---|---|---|
| **S1** | `PARTIAL ⇒ Driver ∈ {MATCH, PARTIAL}` | ✅ 0 违规 |
| **S2** | `PARTIAL ⇒ Evidence Sequence ∈ {MATCH, PARTIAL}` | ✅ 0 违规 |
| **S3** | `PARTIAL ⇒ 维度支持数 ≥ 2` | ✅ 0 违规 |
| **S4** | **`Driver = MISMATCH` ⇒ 状态 ∉ STRUCTURAL_*** | ✅ 0 违规 |
| **S5** | `Driver = PERIPHERAL_OVERLAP` ⇒ 状态 ∉ STRUCTURAL_* | ✅ 0 违规 |
| **S6** | `SUPPORTED ⇒ sequence_subtype ∈ {SEQUENCE_MATCH, SEQUENCE_PARTIAL}` | ✅ 0 违规 |
| **S7** | `SUPPORTED ⇒ lifecycle = MATCH` 且无核心 MISMATCH 且 `has_direct` | ✅ 0 违规 |
| **S8** | `SUPPORTED ⇒ Driver = MATCH` 或（`PARTIAL` 且 `MULTI_MECHANISM`） | ✅ 0 违规 |
| **S9** | `event_quality = SINGLE_TYPE_ONLY ⇒ event_structure ≠ PARTIAL` | ✅ 0 违规 |
| **S10** | `INSUFFICIENT_EVIDENCE ⇔ (n_av ≥ 2 或 Driver = NOT_AVAILABLE)` | ✅ 0 违规 |
| **S11** | 结构支持不足 ⇒ SAME→`THEME_ONLY` / CROSS→`NO_VALID_CORRESPONDENCE` | ✅ 0 违规 |
| **S12** | Theme-Blind 不改变 Structural Status | ✅ 0 变化 |
| **S13** | 负控制保持非结构状态 | ✅ 2/2 |
| **S14** | **全表 `Driver = MISMATCH` 的 `PARTIAL` 计数 = 0** | ✅ **0**（A 组对照 50） |
| **P1** | Rule Set v0.3 文档与 Calibration `protocol_version` 一致 | ✅ |
| **P2** | v0.1 / v0.2 / SA v0.3 旧产物存在（未被删除） | ✅ 12/12 |

### 7.2 结果

```
=== validate_structural_analogy_semantics.py（structural-analogy-ruleset-v0.3）===
独立重算行数: 1580 / 1580
★ S14：driver=MISMATCH → STRUCTURAL_PARTIAL
     D 组（v0.3 规则 + v0.3 driver）: 0 条  ← 必须为 0
     C 组（v0.3 规则 + v0.2 driver）: 0 条
     A 组（v0.2 规则 + v0.2 driver）: 50 条  ← SA v0.3 已发布基线
------------------------------------------------------------------
结果: PASS（FAIL 0 / WARN 0）
```

> **★ 该校验器在开发过程中真实捕获了 2 处不一致**（最终确认为校验器自身的 CSV 布尔解析缺陷 `bool("False") == True`，
> 以及 calibration CSV 的**宽表混用不同 run 的 driver/status** 问题）。
> 二者均已修正为 **long-format CSV（pair × run）** + 显式布尔解析 → 现 **1580/1580 逐行一致**。
> 这证明该层校验**确实能发现「Validator PASS 但语义不一致」的问题**。

---

## 8. 本轮新增 / 未改动清单

### 8.1 新增（8 个文件）

| 文件 | 性质 |
|---|---|
| `research/research/methodology/structural_analogy_rule_set_v0_3.md` | **Rule Set v0.3**（冻结） |
| `research/research/reports/structural_analogy_rule_calibration_v0_3.json` | **Rule Calibration v0.3** |
| `research/research/reports/structural_analogy_rule_calibration_pairs_v0_3.csv` | 逐行校准数据（**long format：395 × 4 = 1580 行**） |
| `research/research/reports/historical_driver_canonicalization_v0_3.json` | **Driver Canonicalization v0.3** |
| `research/research/reports/historical_driver_evidence_ledger_v0_3.json` | Ledger v0.3（541 entries） |
| `research/scripts/build_structural_analogy_rule_calibration_v0_3.py` | 校准生成器（含 `level_v2()` / `level_v3()`，`--check`） |
| `research/scripts/canonicalize_historical_drivers_v0_3.py` | 规范化生成器（`--check`） |
| `research/scripts/validate_structural_analogy_semantics.py` | **语义一致性校验器**（独立重算 + S1–S14） |

### 8.2 未改动（**已 `git diff --quiet` 逐文件确认 UNCHANGED**）

`structural_analogy_rule_set_v0_2.md` · `structural_analogy_rule_calibration_v0_2.json` ·
`structural_analogy_research_v0_1/v0_2/v0_3.json` · `structural_analogy_explanations_v0_1/v0_2/v0_3.json` ·
`historical_driver_canonicalization_v0_1/v0_2.json` · `historical_driver_evidence_ledger_v0_1/v0_2.json` ·
canonical DB · `exports/timeline_export_v1.json` · Export Contract v1.0 · Research Model v1.0 ·
Schema · Protocol · taxonomy · CMTR v1

---

## 9. 验证结果

| 检查 | 结果 |
|---|---|
| `validate_db` | **PASS**（3 条 warning 与之前完全相同，**未新增**） |
| `validate_timeline_export` | **PASS** |
| `validate_batch_research` | **PASS** |
| `validate_promotion_manifest` | **PASS** |
| `check_doc_schema_consistency` | **PASS** |
| `validate_current_research` | **PASS** |
| `validate_monorepo_integrity` | **PASS** |
| `refresh --check` | **PASS** |
| `intake --check` | **PASS** |
| validator tests | **PASS**（44/44） |
| `validate_governance_gates` | **PASS** |
| `validate_structural_analogy_v0_3`（A1–A16） | **PASS** |
| **`validate_structural_analogy_semantics`**（独立重算 + S1–S14） | **PASS**（FAIL 0 / WARN 0；1580/1580 一致） |
| `canonicalize_historical_drivers_v0_3.py --check` | **PASS**（deterministic） |
| `build_structural_analogy_rule_calibration_v0_3.py --check` | **PASS**（deterministic） |
| **v0.1 / v0.2 / SA v0.3 全部保持不变** | **PASS**（12 个文件 `git diff --quiet` 全部 UNCHANGED） |

---

## 10. 仍需在 SA v0.4 前处理的问题

| # | 问题 | 级别 | 说明 |
|---|---|---|---|
| 1 | **18 个 Research Candidate 的 `drivers` 全为空** | **数据补全** | 属 **export 数据缺口** → 应由 Canonical / Export 层补全（**不得由词表猜测**）；补全后这 18 个 cycle 才能参与结构判定 |
| 2 | **2 个 RC 有 driving 文本但仍无 canonical driver**（`RC-2025-MIL-PARADE-80` · `RC-2024-SECONDARY`） | 映射逻辑 | 因多规则命中落入 `DERIVED`（无 canonical）或 `AMBIGUOUS`。**多命中消歧属映射逻辑变更**（非关键词变更），需在 v0.4 评估 |
| 3 | **E.3：`historical_kind` metadata 缺陷** | **元数据** | SA **research** artifact 的 `historical_profiles[].kind` / `matrix[].historical_kind` 把**全部 cycle 标为 `campaign`**（含 RC-*）。根因：export 的 `research_candidates[]` 复用 `campaign_id` 字段名。**无规则影响**（explanations 侧已正确）。建议 SA v0.4 一并修正 |
| 4 | **E.4：关键词扩展的已知副作用** | 轻微 | 8 条文本由 `DIRECT` → `DERIVED`；其中 `C-2025-FIN-INSURANCE` **失去唯一 DIRECT**（`has_direct` True→False）。**不改变任何 SUPPORTED 结论**（该 cycle 本就不达 SUPPORTED）；`primary_mechanism` 变为 `UNKNOWN` |
| 5 | **`driver = MATCH` 仅 1 条 / `event MATCH` 仅 1 条** | 观测 | `MATCH` 极稀缺是**数据粒度**问题（历史 driver 证据与事件覆盖不足），**不得**通过放宽规则解决 |
| 6 | **`evidence_sequence NOT_AVAILABLE` 190/395** | 观测 | 任一侧 <2 条带日期事件即 `NOT_AVAILABLE`；属数据覆盖限制 |

> **建议 SA v0.4 的顺序**：① 先完成问题 1（export 数据补全）② 再评估问题 2（多命中消歧）③ 修正问题 3（kind metadata）
> ④ 用 **Rule Set v0.3 + Canonicalization v0.3** 生成 **SA v0.4**（Research + Explanations）⑤ 之后才考虑 Time Observation 刷新。

---

## 11. 本轮严格未做

- ❌ **未生成 SA v0.4**；**未覆盖 SA v0.3**；
- ❌ **未刷新 Time Observation**；
- ❌ 未修改 **canonical DB** / **Export Contract v1.0** / `exports/timeline_export_v1.json`；
- ❌ 未修改 **Research Model v1.0** / **Schema** / **Protocol** / **taxonomy** / **CMTR v1**；
- ❌ 未修改 **Rule Set v0.2** 及其 Calibration v0.2；
- ❌ 未修改 **Research v0.1/v0.2/v0.3** · **Explanations v0.1/v0.2/v0.3**；
- ❌ 未修改 **Driver Canonicalization v0.1/v0.2** · **Ledger v0.1/v0.2**；
- ❌ 未新增 driver vocabulary；未使用 `event_type` 反推 driver；未使用价格结果反推 driver；
- ❌ 未回改 R01 Campaign；
- ❌ 未为降低 `INSUFFICIENT_EVIDENCE` 而猜测 driver 或补造证据。

---

*Structural Analogy Rule Set v0.3 · effective 2026-09-22 · 未刷新 Time Observation*
