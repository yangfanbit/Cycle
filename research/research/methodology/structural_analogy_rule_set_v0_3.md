# Structural Analogy Rule Set v0.3（冻结）

> | 项目 | 值 |
> |---|---|
> | 文件性质 | **Research Layer 判定规则冻结件**（不是 Product schema / export contract） |
> | Rule Set | **`Structural Analogy Rule Set v0.3`** |
> | Protocol version | `structural-analogy-ruleset-v0.3` |
> | **Effective date** | **2026-09-22** |
> | **Source artifact** | `research/research/reports/structural_analogy_rule_calibration_v0_3.json` |
> | **取代** | `Structural Analogy Rule Set v0.2`（`structural-analogy-ruleset-v0.2`）—— 其文档与 Calibration v0.2 **逐字节保留**，仅状态由「当前生效」改为「已被 v0.3 取代」 |
> | **依据** | `docs/STRUCTURAL_ANALOGY_V0_3_REFRESH_REPORT.md` §5（E.1 / E.2） |
> | **不修改** | Rule Set v0.2 文本 · Rule Calibration v0.2 · Research v0.1/v0.2/v0.3 · Explanations v0.1/v0.2/v0.3 · Driver Canonicalization v0.1/v0.2 · Ledger v0.1/v0.2 · `schema.sql` · `contracts/` · `exports/` · Research Model v1.0 · 历史原始数据 · Product |
>
> 本文档**只定义研究侧判定规则**，不新增数据库实体、不新增字段、不修改原始 driver。

---

## 0. 为什么需要 v0.3

`Structural Analogy v0.3`（R01 扩展 universe，79 cycle / 395 pairs）暴露了 Rule Set v0.2 的**一处真实缺陷**：

> **§8 文本**要求 `STRUCTURAL_PARTIAL` 的 `Driver ∈ {MATCH, PARTIAL}`，
> 但 **§7 指定实现**（`build_structural_analogy_rule_calibration_v0_2.py::level_v2()`）
> 的末段存在 fallback `if n_support >= 2: return "STRUCTURAL_PARTIAL"` —— **不检查 driver**。

**实测影响**：

| | STRUCTURAL_PARTIAL 总数 | 其中 `driver = MISMATCH` | 占比 |
|---|---:|---:|---:|
| v0.2（17 cycle） | 36 | 10 | **27.8%** |
| **v0.3（79 cycle）** | **89** | **50** | **56.2%** |

→ 即「**核心机制完全不对应**（driver = MISMATCH）的组合，仅因其它维度支持数 ≥2 就被判为 `STRUCTURAL_PARTIAL`」。
这与 Structural Analogy 的目标（寻找**机制 + 生命周期 + 证据结构**真正对应的历史案例）相悖。

### v0.3 的裁决

> **以 §8 文字语义为准：`Driver = MISMATCH` 不得进入 `STRUCTURAL_PARTIAL`。**

理由：当**核心机制**完全 MISMATCH 时，其它维度的重叠**不足以**单独构成 Structural Partial ——
否则「同族 / 同类行情形状」会被误读为「机制结构对应」，正是 Rule Set §10 三条负控制命题要防的失效模式。

**v0.3 只做这一处语义修正**（+ 使 §7/§8/§9/§11 的判定顺序与优先级**显式化、无歧义**）；
**其余维度判据（Lifecycle / Driver / Evidence Sequence / Event Structure 的取值规则）全部沿用 v0.2，未改**。

---

## 1. 判定顺序（**强制**，自上而下，命中即返回）

> **R1 → R2 → R3 → R4**。**顺序不可调换**；每行**恰好命中一条**。

| 序 | 结果 | 条件 |
|---|---|---|
| **R1** | `INSUFFICIENT_EVIDENCE` | `NOT_AVAILABLE` 维度数 **≥ 2**，**或** `Driver = NOT_AVAILABLE` |
| **R2** | `STRUCTURAL_SUPPORTED` | `strict` 或 `supported`（见 §3） |
| **R3** | `STRUCTURAL_PARTIAL` | **`Driver ∈ {MATCH, PARTIAL}`** **且** `Evidence Sequence ∈ {MATCH, PARTIAL}` **且** 维度支持数 ≥ 2 |
| **R4** | `THEME_ONLY` / `NO_VALID_CORRESPONDENCE` | 其余全部情形 → 按 `Theme Relation` **事后派生**（§5） |

**★ R3 是 v0.3 的核心修正**：`Driver ∈ {MATCH, PARTIAL}` 是 **硬前提**；
`Driver ∈ {PERIPHERAL_OVERLAP, MISMATCH, NOT_AVAILABLE}` **一律不得**进入 `STRUCTURAL_PARTIAL`。
**不存在**任何「因其它维度支持数 ≥2 而升级为 PARTIAL」的 fallback。

---

## 2. 维度取值规则（**沿用 v0.2，未改**）

### 2.1 Lifecycle（D1）

```
candidate.current_phase ↔ historical.stage_at_comparable_point
target = PHASE_TO_STAGE(candidate.current_phase)
历史 lifecycle 含 target     → MATCH   （锚点日期明确）
历史含相邻阶段                 → PARTIAL
否则                           → MISMATCH
历史无 lifecycle               → COMPARISON_POINT_UNKNOWN
```

**禁止**：`candidate.current_phase ↔ historical.terminalPhaseOf`。
**状态词表**：`MATCH` · `PARTIAL` · `MISMATCH` · `UNKNOWN` · `NOT_AVAILABLE` · `COMPARISON_POINT_UNKNOWN`

### 2.2 Driver（D2，机制轴）

**词表来源**：`Historical Driver Canonicalization`（v0.1 / v0.2 / **v0.3**，三者 **canonical vocabulary 相同**）——
即 `research/current/schema.json` 的 `narrativeType` 枚举。**禁止新增 driver vocabulary**。

| 状态 | 判据 |
|---|---|
| **`MATCH`** | 集合相等 **且 ≥2 项** **且** 历史侧对共有机制均有 **DIRECT provenance**（`CORE_EQUIVALENT`） |
| **`PARTIAL`** | 交集 **≥2**（`MULTI_MECHANISM`）；或 交集 =1 且该机制 = 历史 `primary_mechanism`（`PRIMARY_MECHANISM_OVERLAP`） |
| **`PERIPHERAL_OVERLAP`** | 交集 =1 且 **非**历史 primary（`PERIPHERAL_ONLY`） |
| **`MISMATCH`** | 交集 = 0 |
| **`NOT_AVAILABLE`** | 任一侧无 canonical driver |

**硬约束**：`PERIPHERAL_OVERLAP` **不属于** structural support；**不得**仅凭 driver 名称相同判定 `MATCH`；
**不得**从 `event_type` / 价格 / 涨跌结果反推 driver。

### 2.3 Evidence Sequence（D3）

| subtype | 判据 |
|---|---|
| `SEQUENCE_MATCH` | LCS ≥2 **且** 首项相同 |
| `SEQUENCE_PARTIAL` | LCS ≥2 **但** 首项不同 |
| `SET_ONLY` | LCS =1 **且** 类型交集 ≥2 |
| `SEQUENCE_MISMATCH` | LCS ≤1 **且** 类型交集 <2 |
| `NOT_AVAILABLE` | 任一侧 <2 条带日期事件 |

**维度状态** ∈ `{MATCH, PARTIAL, MISMATCH, UNKNOWN, NOT_AVAILABLE}`（与 subtype 是**两套词表**）。
**硬约束**：`same evidence types ≠ sequence match`；**`SET_ONLY` 不得当作 `SEQUENCE_MATCH`**。

### 2.4 Event Structure（D4）

| 状态 | 判据 |
|---|---|
| **`MATCH`** | 类型集合相等 **且** 双方 ≥2 事件 **且** 首项相同 |
| **`PARTIAL`** | 类型交集 **≥2** **且** 双方 ≥2 事件；或交集 ≥2 但 chronology 不完整 |
| **`MISMATCH`** | 交集 **≤1**（**`SINGLE_TYPE_ONLY` 不得作为 `PARTIAL`**） |
| **`NOT_AVAILABLE`** | 任一侧无事件实体 |

**硬约束**：**继续禁止 `event_type → driver`**。

---

## 3. `STRUCTURAL_SUPPORTED` / `STRICT_STRUCTURAL_SUPPORTED`（**沿用 v0.2 §7，未改**）

`supported` **必须同时满足**：

1. `Lifecycle = MATCH`
2. `Driver = MATCH`，或 `Driver = PARTIAL` **且** `driver_quality = MULTI_MECHANISM`
3. `Evidence Sequence ∈ {MATCH, PARTIAL}` 且 `subtype ∈ {SEQUENCE_MATCH, SEQUENCE_PARTIAL}`
4. `Event Structure ∈ {MATCH, PARTIAL}`
5. **非 Lifecycle 维度中 ≥2 个**有 evidence-backed support
6. 不存在核心 `MISMATCH`（`lifecycle` / `driver` / `event_structure`）
7. **`Theme Relation` 不参与判定**
8. 历史侧存在 ≥1 个 **DIRECT** driver 证据（`has_direct`）

`strict` = 同 `supported`，但 **`Driver = MATCH`**（**单独计数，不得把 PARTIAL 包装成 supported**）。

> **`PRIMARY_MECHANISM_OVERLAP`（单一机制交集）不足以**支撑 `STRUCTURAL_SUPPORTED`
> —— 必须 `MULTI_MECHANISM`（≥2 机制交集）。

---

## 4. `STRUCTURAL_PARTIAL`（**v0.3 修正**）

**必须同时满足**：

1. **`Driver ∈ {MATCH, PARTIAL}`** ← ★ **v0.3 硬前提**（`PERIPHERAL_OVERLAP` / `MISMATCH` / `NOT_AVAILABLE` **均不得**）
2. **`Evidence Sequence ∈ {MATCH, PARTIAL}`**
3. **维度支持数 ≥ 2**
4. **不存在**任何形式的 fallback 升级

### 硬约束

> **`Driver = MISMATCH` 时，无论其它维度支持数多高，一律不得判为 `STRUCTURAL_PARTIAL`。**
> **不能仅 `Lifecycle MATCH + weak driver overlap` 自动升级。**
> **`PERIPHERAL_OVERLAP` 不计入 structural support。**

> ⚠️ **与 v0.2 的差异**：v0.2 实现存在末段 fallback
> `if n_support >= 2: return "STRUCTURAL_PARTIAL"`，会放行 `Driver = MISMATCH`。
> **v0.3 移除该 fallback**，使实现与 §8 文本一致。

---

## 5. `THEME_ONLY` / `NO_VALID_CORRESPONDENCE`（**沿用 v0.2 §9，未改**）

> **Theme / Industry / Name 等表层关系存在，但正式 Structural Dimensions 不足以形成结构对应。**

**必须在 structural evaluation 之后派生**（即 R1–R3 全部未命中时）：

```
结构支持不足  且  Theme Relation = SAME_MACRO_THEME   →  THEME_ONLY
结构支持不足  且  Theme Relation = CROSS_MACRO_THEME  →  NO_VALID_CORRESPONDENCE
```

---

## 6. `INSUFFICIENT_EVIDENCE`（**沿用 v0.2 §11，未改**）

**最高优先级**（R1）：`NOT_AVAILABLE` 维度 ≥2，或 `Driver = NOT_AVAILABLE`。

> **`UNKNOWN` ≠ `NO_PATTERN`**；**`NOT_AVAILABLE` ≠ `NO_PATTERN`**；
> **missing evidence ≠ absence of phenomenon**；**incomplete chronology ≠ sequence mismatch**。
>
> `NOT_AVAILABLE` 表示**当前资料不足以编码**，**不是**「该现象不存在」。
> **不得**为降低 `INSUFFICIENT_EVIDENCE` 数量而猜测 driver 或补造证据。

---

## 7. 负控制规则（**强制，沿用 v0.2 §10**）

> **`name similarity != structural correspondence`**
> **`same theme != structural correspondence`**
> **`cross theme != structural correspondence`**

| 用途 | 案例 | 必须保持 |
|---|---|---|
| name-similarity negative control | `CC-2026-EMBODIED-AI × C-2024-ROBOTAXI` | **`NO_VALID_CORRESPONDENCE`** |
| same-theme negative control | `CC-2026-OPTICAL-LINK × C-2019-COMM-5G` | **`THEME_ONLY`** |

> 若上述案例在**数据未真实变化**的情况下发生升级 → **必须停止并解释，而不是自动接受。**

---

## 8. Theme Relation 与 Structural Status 解耦（**强制，沿用 v0.2 §1**）

`Theme Relation`（`SAME_MACRO_THEME` / `CROSS_MACRO_THEME`）**不参与** `Structural Status` 判定，
**只在**结构评估**之后**用于派生 `THEME_ONLY`。

**禁止**：因同族而降级 · 因跨族而升级 · 因 industry 相同升级 · 因 industry 不同降级。

---

## 9. Market / Temporal / Governance Boundary（**强制，沿用 v0.2 §12**）

| 类别 | 维度 | 参与 Structural Status？ |
|---|---|---|
| **正式维度** | Lifecycle · Driver · Evidence Sequence · Event Structure | ✅ **是** |
| **非正式维度** | Market · Temporal · **Governance（`governance-gates-v0.1`）** | ❌ **否** |

Governance 元数据（`market_evidence_state` / `beta_level` / `peak|end` 四态 / `result`）
**只可进入 supplementary context**：
- **`beta_level = 1` ≠ Alpha**；
- **`market_evidence_state = A_SHARE_MARKET` ≠ 独立 Campaign**；
- **`result = weak` = 方向为负**，**不降低**该 cycle 参与结构类比的资格。

---

## 10. 版本标识与生效范围

| 项 | 值 |
|---|---|
| Rule Set | `Structural Analogy Rule Set v0.3` |
| Protocol version | `structural-analogy-ruleset-v0.3` |
| Effective date | **2026-09-22** |
| Source artifact | `research/research/reports/structural_analogy_rule_calibration_v0_3.json` |
| 权威实现 | `research/scripts/build_structural_analogy_rule_calibration_v0_3.py::level_v3()` |
| 语义一致性校验 | `research/scripts/validate_structural_analogy_semantics.py` |
| 适用范围 | 所有后续 Structural Analogy Research 轮次（含 SA v0.4） |
| 旧规则集 | **不修改、不覆盖**（逐字节保留） |
| 后续变更 | **必须新建 v0.4 规则集**，不得就地修改本文件 |

### 与旧规则集的关系

| 规则集 | 状态 |
|---|---|
| v0.1（隐式） | 已被 v0.2 取代（其报告保留） |
| v0.2 | **已被本规则集取代**（其文档与 Calibration **逐字节保留**） |
| **v0.3（本文件）** | **当前生效** |

### v0.2 → v0.3 变更清单（**仅 1 项语义修正**）

| # | 变更 | 性质 |
|---|---|---|
| **1** | `STRUCTURAL_PARTIAL` 的 `Driver ∈ {MATCH, PARTIAL}` 由「文本要求」提升为「实现硬前提」；**移除** `if n_support >= 2 → STRUCTURAL_PARTIAL` fallback | **语义修正**（消除文本-实现不一致） |
| 2 | 判定顺序 R1→R2→R3→R4 显式化（v0.2 隐含） | 表达澄清（**不改变**任何已正确判定的结果） |
| 3 | 其余全部判据（Lifecycle / Driver / Sequence / Event / Theme 解耦 / 负控制 / 边界） | **未改** |

---

## 11. 禁止事项（汇总）

- ❌ similarity score · weighted score · confidence score · probability · similarity percentage
- ❌ ranking · top N · best analogue · winner · most similar
- ❌ 从 `event_type` 推 driver
- ❌ 从价格 / 涨跌结果推 driver 或 lifecycle
- ❌ 把 Market / Temporal / Governance 计入 Structural Status
- ❌ 把 `SET_ONLY` 当作 `SEQUENCE_MATCH`
- ❌ 把 `SINGLE_TYPE_ONLY` 当作 Event `PARTIAL`
- ❌ 把 `PERIPHERAL_OVERLAP` 计入 structural support
- ❌ **把 `Driver = MISMATCH` 判为 `STRUCTURAL_PARTIAL`**（★ v0.3 新增禁止项）
- ❌ 因同族而升级 / 因跨族而降级
- ❌ 新增 driver vocabulary / taxonomy / mapping
- ❌ 为降低 `INSUFFICIENT_EVIDENCE` 而猜测 driver 或补造证据
- ❌ 修改历史原始数据 / candidate driver / schema / export contract / Product
- ❌ 修改 Rule Set v0.2 及其 Calibration v0.2、Research/Explanations v0.1–v0.3

---

*Protocol Freeze 结束 · Structural Analogy Rule Set v0.3 · effective 2026-09-22*
