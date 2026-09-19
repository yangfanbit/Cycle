# Structural Analogy Rule Set v0.2（冻结）

> | 项目 | 值 |
> |---|---|
> | 文件性质 | **Research Layer 判定规则冻结件**（不是 Product schema / export contract） |
> | Rule Set | **`Structural Analogy Rule Set v0.2`** |
> | Protocol version | `structural-analogy-ruleset-v0.2` |
> | **Effective date** | **2026-09-19** |
> | **Source artifact** | `research/research/reports/structural_analogy_rule_calibration_v0_2.json`（Rule Calibration v0.2，7/7 Gate PASS） |
> | 依据报告 | `Structural_Analogy_Rule_Calibration_v0_2.md` · `Structural_Analogy_Robustness_v0_1.md` · `Structural_Analogy_Research_v0_1.md` · `Structural_Analogy_Feasibility_v0_3.md` · `Historical_Driver_Canonicalization_v0_1` |
> | **不修改** | 任何**旧研究报告**（Research v0.1 · Robustness v0.1 · Calibration v0.2 · Feasibility v0.1–v0.3 · Data Readiness v0.1 · Driver Canonicalization v0.1 · Time Observation v0.2–v0.5） |
> | 不改变 | `schema/schema.sql` · `contracts/` · `exports/` · Research Model v1.0 · 历史原始数据 · Product |
>
> 本文档**只定义研究侧判定规则**，不新增数据库实体、不新增字段、不修改原始 driver。

---

## 0. 为什么需要冻结

`Structural Analogy Rule Calibration v0.2` 修正了 v0.1 的三处规则表达问题并**通过 7/7 Decision Gate**：

| # | v0.1 问题 | v0.2 修正 |
|---|---|---|
| **A** | **Theme precedence bug** —— `elif same_theme: THEME_ONLY` 先于结构性判定 → 同族会「压低」等级 | 结构性判定置于主题判定**之前**；Theme 仅用于 `THEME_ONLY` 的**事后**派生 |
| **B** | **Event 低筛选力** —— `event_structure PARTIAL = 74/85`；Robustness 中 `R2 ≡ R3` | `overlap == 1` **不再算 PARTIAL**（→ `MISMATCH`）；`PARTIAL` 需 ≥2 类型真实对应 + 可比 chronology |
| **C** | **Driver PARTIAL 过宽** —— `PARTIAL = 50/85` | 引入 `primary_mechanism`；`overlap == 1 且非历史 primary` → **`PERIPHERAL_OVERLAP`（不计为支持）** |

冻结的目的：**后续 Research 轮次只执行规则，不再调规则。**

---

## 1. Structural Status 与 Theme Relation 解耦（强制）

### 1.1 Structural Status

**只允许**由以下四个正式维度决定：

| 维度 | 标识 |
|---|---|
| Lifecycle | `D1` |
| Driver（机制轴） | `D2` |
| Evidence Sequence | `D3` |
| Event Structure | `D4` |

### 1.2 Theme Relation（独立 metadata）

单独记录，取值：

`SAME_MACRO_THEME` · `CROSS_MACRO_THEME` · `SAME_INDUSTRY` · `CROSS_INDUSTRY` · `UNKNOWN`

> **本轮实现只使用前两个**（`SAME_MACRO_THEME` / `CROSS_MACRO_THEME`）；
> `SAME_INDUSTRY` / `CROSS_INDUSTRY` / `UNKNOWN` 为保留取值，待 industry 层级数据可用时启用。

### 1.3 禁止（**硬约束**）

- ❌ 因 `SAME_THEME` **降级**
- ❌ 因 `CROSS_THEME` **升级**
- ❌ 因 industry 相同**升级**
- ❌ 因 industry 不同**降级**

`Theme Relation` **不得**参与 `Structural Status` 的判定；
它**只**在结构评估**之后**用于派生 `THEME_ONLY`。

---

## 2. Lifecycle 比较语义（强制）

```
candidate.current_phase  ↔  historical.stage_at_comparable_point
```

`historical.stage_at_comparable_point`（`historical_comparison_point`）为
**Research-layer 派生观测点**，**不是**新的生命周期阶段：

```
target = PHASE_TO_STAGE(candidate.current_phase)
历史 lifecycle[] 含 target     → MATCH   （锚点日期明确）
历史含相邻阶段                 → PARTIAL
否则                           → MISMATCH（回落到最早阶段，仅作记录）
历史无 lifecycle               → COMPARISON_POINT_UNKNOWN
```

### 禁止

- ❌ `candidate.current_phase ↔ historical.terminalPhaseOf`

`terminalPhaseOf` **仅保留为历史 cycle 的 background 信息**，**不得**用于 current-phase analogy。

**状态词表**：`MATCH` · `PARTIAL` · `MISMATCH` · `UNKNOWN` · `NOT_AVAILABLE`

---

## 3. Driver（机制轴，强制）

### 3.1 词表来源

**必须**使用 `Historical Driver Canonicalization v0.1`：

- Canonical vocabulary = `research/current/schema.json` 的 `narrativeType` 枚举
  （`POLICY_DRIVEN` / `INDUSTRY_UPGRADE` / `TECH_BREAKTHROUGH` / `DEMAND_SURGE` /
  `SUPPLY_CONTRACTION` / `VALUATION_RESET` / `CYCLE_REVERSAL` / `EVENT_CATALYST` / `UNKNOWN`）
- **禁止新增** driver vocabulary
- **禁止**从 `event_type` / 价格 / 行业标签反推 driver

### 3.2 状态词表

`MATCH` · `PARTIAL` · `PERIPHERAL_OVERLAP` · `MISMATCH` · `UNKNOWN` · `NOT_AVAILABLE`

| 状态 | 判据 |
|---|---|
| **`MATCH`** | 集合相等 **且 ≥2 项** **且** 历史侧对共有机制均有 **DIRECT provenance**（`CORE_EQUIVALENT`）。**要求机制语义真正对应 + evidence provenance 明确。** |
| **`PARTIAL`** | 交集 **≥2**（`MULTI_MECHANISM`）；或 交集 =1 且该机制 = 历史 `primary_mechanism`（`PRIMARY_MECHANISM_OVERLAP`）。**必须存在明确机制交集，但核心机制不能完全相同。** |
| **`PERIPHERAL_OVERLAP`** | 交集 =1 且 **非**历史 primary（`PERIPHERAL_ONLY`）。**仅存在外围 / 非主要机制交集。** |
| **`MISMATCH`** | 交集 = 0 |
| **`NOT_AVAILABLE`** | 任一侧无 canonical driver |

### 3.3 硬约束

> **`PERIPHERAL_OVERLAP` 不属于 structural support。**
> **不得仅凭 driver 名称相同判定 `MATCH`。**

---

## 4. Primary Mechanism（强制）

`primary_mechanism` 为 **Research-layer 派生**，**不修改原始 driver**。

### 确定规则（deterministic）

1. 取该历史 cycle 在 **driving 相位**（`start` + `accelerator`）中
   **DIRECT 证据计数最高**的 canonical driver
2. 平手 → **确定性 tie-break**：canonical 名称**升序**
3. **无 DIRECT → `UNKNOWN`**
4. **禁止猜测**

> **实测**（当前样本）：15/16 cycle 可推导；`UNKNOWN` 仅 2 个
> （`C-2024-V2X` 仅有 DERIVED、`RC-2024-SECONDARY` 无 driving driver）。
> `UNKNOWN` 是**诚实结果**，**不得**为消除它而补造证据。

---

## 5. Evidence Sequence（强制）

### 状态词表

`SEQUENCE_MATCH` · `SEQUENCE_PARTIAL` · `SET_ONLY` · `SEQUENCE_MISMATCH` · `UNKNOWN` · `NOT_AVAILABLE`

| subtype | 判据 |
|---|---|
| `SEQUENCE_MATCH` | LCS ≥2 **且** 首项相同 |
| `SEQUENCE_PARTIAL` | LCS ≥2 **但** 首项不同 |
| `SET_ONLY` | LCS =1 **且** 类型交集 ≥2 |
| `SEQUENCE_MISMATCH` | LCS ≤1 **且** 类型交集 <2 |
| `NOT_AVAILABLE` | 任一侧 <2 条带日期事件 |

### 硬约束

> **`same evidence types ≠ sequence match`**
> **`SET_ONLY` 不得当作 `SEQUENCE_MATCH`。**

---

## 6. Event Structure（强制）

### 状态词表

`MATCH` · `PARTIAL` · `MISMATCH` · `NOT_AVAILABLE`

| 状态 | 判据 |
|---|---|
| **`MATCH`** | 类型集合相等 **且** 双方 ≥2 事件 **且** 首项相同（`TYPE_AND_CHRONOLOGY`）—— 即至少真实 event correspondence + 可比较 event type + chronology / phase relationship 有支持 |
| **`PARTIAL`** | 类型交集 **≥2** **且** 双方 ≥2 事件（`MULTI_TYPE_WITH_CHRONOLOGY`）；或交集 ≥2 但 chronology 不完整 |
| **`MISMATCH`** | 交集 **≤1**（**`SINGLE_TYPE_ONLY` 不得作为 `PARTIAL`**，应进入非支持状态） |
| **`NOT_AVAILABLE`** | 任一侧无事件实体 |

### 硬约束

> **继续禁止 `event_type → driver`。**
> Event 只能证明「什么事件出现了」，**不能**证明「周期由什么机制驱动」。

---

## 7. Structural Supported（冻结）

**必须同时满足**：

1. `Lifecycle = MATCH`
2. `Driver = MATCH`，或 `PARTIAL` **且 quality = `MULTI_MECHANISM`**（= sufficiently evidenced PARTIAL）
3. `Evidence Sequence ∈ {MATCH, PARTIAL}` 且 subtype ∈ {`SEQUENCE_MATCH`, `SEQUENCE_PARTIAL`}
4. `Event Structure ∈ {MATCH, PARTIAL}`
5. **≥2 个非 Lifecycle 维度**具有 evidence-backed support
6. 不存在核心 `MISMATCH`（lifecycle / driver / event）
7. **`Theme Relation` 不参与判定**

> **以 `Rule Calibration v0.2` 已通过的 deterministic implementation 为准** ——
> **不要重新发明规则。** 实现位于
> `research/scripts/build_structural_analogy_rule_calibration_v0_2.py::level_v2()`。

### `STRICT_STRUCTURAL_SUPPORTED`

同 `STRUCTURAL_SUPPORTED`，但 **`Driver = MATCH`**（**单独计数，不得把 PARTIAL 包装成 supported**）。

---

## 8. Structural Partial（冻结）

**至少两个维度存在真实结构对应**，**且**：

- `Driver ∈ {MATCH, PARTIAL}`（`PERIPHERAL_OVERLAP` 不算）
- `Evidence Sequence ∈ {MATCH, PARTIAL}`
- 维度支持数 ≥ 2

允许存在的数据限制：`driver partial` · `sequence partial` · `event partial`。

### 硬约束

> **不能仅 `Lifecycle MATCH + weak driver overlap` 自动升级。**

---

## 9. Theme Only（冻结）

> **Theme / Industry / Name 等表层关系存在，但正式 Structural Dimensions 不足以形成结构对应。**

**必须在 structural evaluation 之后派生**：

```
结构支持不足  且  Theme Relation = SAME_MACRO_THEME   →  THEME_ONLY
结构支持不足  且  Theme Relation = CROSS_MACRO_THEME  →  NO_VALID_CORRESPONDENCE
```

---

## 10. 负控制规则（强制）

### 三条不可违反的命题

> **`name similarity != structural correspondence`**
> **`same theme != structural correspondence`**
> **`cross theme != structural correspondence`**

### 必留测试案例

| 用途 | 案例 |
|---|---|
| **name-similarity negative control** | `CC-2026-EMBODIED-AI × C-2024-ROBOTAXI`（**必须保持 `NO_VALID_CORRESPONDENCE`**） |
| same-theme negative control | `CC-2026-OPTICAL-LINK × C-2019-COMM-5G`（`THEME_ONLY`） |
| cross-theme negative control | 68 条跨族组合中非 SUPPORTED 者 |

> 若上述案例在**数据未真实变化**的情况下发生升级 → **必须停止并解释，而不是自动接受。**

---

## 11. 数据不确定性语义（强制）

> **`UNKNOWN` ≠ `NO_PATTERN`**
> **`NOT_AVAILABLE` ≠ `NO_PATTERN`**
> **missing evidence ≠ absence of phenomenon**
> **incomplete chronology ≠ sequence mismatch**

具体：`NOT_AVAILABLE` 表示**当前资料不足以编码**，**不是**「该现象不存在」。

---

## 12. Market / Temporal Boundary（强制）

| 类别 | 维度 | 参与 v0.2 Structural Status？ |
|---|---|---|
| **正式维度** | Lifecycle · Driver · Evidence Sequence · Event Structure | ✅ **是** |
| **非正式维度** | Market · Temporal | ❌ **否** |

Market / Temporal 可以进入 **supplementary context**，但

> **不参与 v0.2 Structural Status。**

理由：`Market Structure = PARTIALLY_RESOLVED`（候选侧 2026 行情不可得，**单向**）；
`Temporal Structure = candidate-side one-way`。

---

## 13. Rule Sensitivity Matrix 的方法学披露（强制）

Calibration v0.2 的 Sensitivity Matrix 中间三行（`theme-decoupled` / `event-calibrated` / `driver-calibrated`）
是用 **v0.2 规则 + 对应维度是否校准** 计算的。

> ⚠️ 当 `driver_calibrated = False` 时**缺少 `driver_quality` 字段**，
> 因此 `drv_strong` **只能由 `MATCH` 满足** → 计数被系统性压低。

**因此：**

> **baseline 与 calibrated intermediate rows 不是严格同口径。**
> **以后不得把中间三行直接解释为独立的性能变化。**

它们的**唯一用途**是**定位变化的来源方向**，而非给出中间态计数。

---

## 14. 版本标识与生效范围

| 项 | 值 |
|---|---|
| Rule Set | `Structural Analogy Rule Set v0.2` |
| Protocol version | `structural-analogy-ruleset-v0.2` |
| Effective date | **2026-09-19** |
| Source artifact | `research/research/reports/structural_analogy_rule_calibration_v0_2.json` |
| 适用范围 | 所有后续 Structural Analogy Research 轮次 |
| 旧研究报告 | **不修改、不覆盖**（逐字节保留） |
| 后续变更 | **必须新建 v0.3 规则集**，不得就地修改本文件 |

### 与旧规则集的关系

| 规则集 | 状态 |
|---|---|
| v0.1（隐式，见 `Structural_Analogy_Research_v0_1.md`） | **已被本规则集取代**（其报告保留） |
| **v0.2（本文件）** | **当前生效** |

---

## 15. 禁止事项（汇总）

- ❌ similarity score · weighted score · confidence score · probability · similarity percentage
- ❌ ranking · top N · best analogue · winner · most similar
- ❌ 从 `event_type` 推 driver
- ❌ 从价格 / 涨跌结果推 driver 或 lifecycle
- ❌ 把 Market / Temporal 计入 Structural Status
- ❌ 把 `SET_ONLY` 当作 `SEQUENCE_MATCH`
- ❌ 把 `SINGLE_TYPE_ONLY` 当作 Event `PARTIAL`
- ❌ 把 `PERIPHERAL_OVERLAP` 计入 structural support
- ❌ 因同族而升级 / 因跨族而降级
- ❌ 新增 driver vocabulary / taxonomy / mapping
- ❌ 修改历史原始数据 / candidate driver / schema / export contract / Product

---

*Protocol Freeze 结束 · Structural Analogy Rule Set v0.2 · effective 2026-09-19*
