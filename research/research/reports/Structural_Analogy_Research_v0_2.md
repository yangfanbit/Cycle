# Structural Analogy Research v0.2

> | 项目 | 值 |
> |---|---|
> | 性质 | **Research-only Structural Analogy baseline**（执行**已冻结**规则，不调规则） |
> | 完成日期 | 2026-09-19 |
> | 起始状态 | `HEAD = origin/main = 724e44f`，ahead/behind `0/0`，工作树 clean（**自行核对**） |
> | 前置 | Step A `research: freeze structural analogy rule set v0.2`（commit `5fdc5ec`） |
> | 未修改 | `src/**` · schema.sql · export contract · 历史原始数据 · candidate driver · **全部旧产物**（Research v0.1 · Robustness v0.1 · Calibration v0.2 · Feasibility v0.1–v0.3 · Data Readiness v0.1 · Driver Canonicalization v0.1 · Time Observation v0.2–v0.5） |

---

## Protocol

| 项 | 值 |
|---|---|
| **Rule Set** | **`Structural Analogy Rule Set v0.2`** |
| **Protocol version** | `structural-analogy-ruleset-v0.2` |
| **Protocol document** | `research/research/methodology/structural_analogy_rule_set_v0_2.md` |
| **Effective date** | **2026-09-19** |
| **Source calibration artifact** | `research/research/reports/structural_analogy_rule_calibration_v0_2.json` |
| **Frozen** | **YES** |
| 规则实现一致性 | 与 `build_structural_analogy_rule_calibration_v0_2.py::level_v2()` **逐条一致**（实测计数完全相同） |

---

## Core Result

| 项 | 值 |
|---|---:|
| Current candidates | **5** |
| Historical cycles | **17**（13 Campaign + 4 Research Candidate） |
| Comparison pairs | **85** |
| **STRICT_STRUCTURAL_SUPPORTED** | **1** |
| **STRUCTURAL_SUPPORTED** | **4** |
| **STRUCTURAL_PARTIAL** | **36** |
| **THEME_ONLY** | **3** |
| **INSUFFICIENT_EVIDENCE** | **5** |
| **NO_VALID_CORRESPONDENCE** | **37** |

---

## v0.1 → v0.2

| 分类 | 对数 |
|---|---:|
| **added**（v0.1 中不存在该等级 → v0.2 新出现） | 0（等级集合不变） |
| **removed** | 0 |
| **upgraded**（等级序下降 = 更结构） | **11** |
| **downgraded**（等级序上升 = 更弱） | **21** |
| **unchanged** | **53** |
| 合计变化 | **32 / 85** |

### 状态迁移矩阵

| v0.1 → v0.2 | 对数 |
|---|---:|
| `STRUCTURAL_SUPPORTED` → `STRUCTURAL_SUPPORTED` | **4** |
| `STRUCTURAL_PARTIAL` → `STRUCTURAL_PARTIAL` | 25 |
| `STRUCTURAL_PARTIAL` → `NO_VALID_CORRESPONDENCE` | 19 |
| `NO_VALID_CORRESPONDENCE` → `NO_VALID_CORRESPONDENCE` | 18 |
| `NO_VALID_CORRESPONDENCE` → `STRUCTURAL_PARTIAL` | 9 |
| `INSUFFICIENT_EVIDENCE` → `INSUFFICIENT_EVIDENCE` | 5 |
| **`THEME_ONLY` → `STRUCTURAL_PARTIAL`** | **2** |
| `STRUCTURAL_PARTIAL` → `THEME_ONLY` | 2 |
| `THEME_ONLY` → `THEME_ONLY` | 1 |

### 归因（**不混合解释**）

| 归因 | 对数 |
|---|---:|
| Driver calibration | 10 |
| Driver + Event calibration | 11 |
| Event calibration | 3 |
| Theme decoupling / Structural support threshold | 8 |
| **合计** | **32** |

> **未使用**模糊的「rule improvement」表述 —— 每条变化均归因到**具体规则**。

---

## Cross-family

| 项 | 跨族（68 组合） | 同族（17 组合） |
|---|---:|---:|
| `STRUCTURAL_SUPPORTED` | **3** | **1** |
| `STRUCTURAL_PARTIAL` | 33 | 3 |

**3 个跨族 `STRUCTURAL_SUPPORTED`**：`BCI-MEDTECH × C-2023-AD`（医药健康↔汽车）·
`EMBODIED-AI × C-2023-AD`（高端装备↔汽车）· `OPTICAL-LINK × C-2025-ROBOTAXI`（信息通信↔汽车）。

---

## Controls

### Name-Blind（regression control）
| 项 | 值 |
|---|---:|
| changed | **0** |

Rule Set v0.2 的四个正式维度**不读取任何名称字段**；名称仅用于展示。✅

### Theme-Blind（regression control）
| 项 | 值 |
|---|---:|
| changed（全部等级） | 3 |
| **Structural Status changed** | **0** ✅ |
| theme_relation changed | **7** ✅（预期行为：metadata 变化） |

3 处变化全部为 `THEME_ONLY` → `NO_VALID_CORRESPONDENCE`（**按定义**，`THEME_ONLY` 依赖 Theme Relation）。
**关键指标 `Structural Status changed = 0` → Theme 不再决定结构等级。** ✅

### Negative Controls（B-12）

| 案例类型 | candidate × cycle | v0.1 | **v0.2** | not upgraded |
|---|---|---|---|---|
| **name-similarity negative control** | `EMBODIED-AI × C-2024-ROBOTAXI` | `NO_VALID` | **`NO_VALID`** | ✅ |
| **same-theme negative control** | `OPTICAL-LINK × C-2019-COMM-5G` | `THEME_ONLY` | **`THEME_ONLY`** | ✅ |
| same-theme（v0.1 曾误判为 THEME_ONLY） | `BCI-MEDTECH × C-2019-PHARMA-INNOV` | `THEME_ONLY` | **`STRUCTURAL_PARTIAL`** | ⚠️ 见下 |
| **theme-decoupling fix case** | `OFFSHORE-WIND × C-2020-POWER-NE` | `THEME_ONLY` | **`STRUCTURAL_PARTIAL`** | ⚠️ 见下 |

> **后两例的「升级」是预期的修复结果，不是错误升级**：
> 它们在 v0.1 中被 `same_theme` 分支**错误压制**为 `THEME_ONLY`；
> v0.2 解耦后，其真实结构支持（`driver ∈ GOOD` 且 `evidence_sequence ∈ GOOD` 且 ≥2 维支持）得以体现。
> **数据未发生任何变化**，变化**完全**来自 Theme 解耦（已在归因中记录为 `Theme decoupling`）。

---

## Research Loop（B-14）

| 环节 | 判定 |
|---|---|
| **Current → Historical search** | **PASS** |
| **Lifecycle** | **PASS**（`MATCH` 58/85） |
| **Driver** | **PARTIAL**（机制级 `MATCH` 极少；`SUPPORTED` 依赖 `MULTI_MECHANISM`） |
| **Evidence Sequence** | **PARTIAL**（`NOT_AVAILABLE` 30/85） |
| **Event Structure** | **PARTIAL**（`NOT_AVAILABLE` 5/85；`MISMATCH` 53/85） |
| **综合** | **PARTIAL** |

---

## Critical Findings

### 1. v0.2 是否保持 v0.1 的四个 SUPPORTED？
✅ **是。** 四个案例**完全保留**（零损失、零新增）：
`BCI-MEDTECH × C-2023-AD` · `EMBODIED-AI × C-2023-AD` · `OPTICAL-LINK × C-2025-ROBOTAXI` ·
`OPTICAL-LINK × C-2023-COMM-OPTICAL`。

### 2. STRICT 是否保持？
✅ **是。** `CC-2026-BCI-MEDTECH × C-2023-AD` 仍为**唯一** `STRICT_STRUCTURAL_SUPPORTED`，
`driver = MATCH / CORE_EQUIVALENT`。

### 3. Theme 是否完全不再决定 Structural Status？
✅ **是。** Theme-Blind 下 **Structural Status changed = 0**；
`theme_relation` 变化 7 处（metadata，预期）。
`THEME_ONLY` 现在**只在结构评估之后**派生，且 3 例全部为 `SAME_MACRO_THEME`。

### 4. Event calibration 是否保持可解释？
✅ **是。** 判据显式且可审计：`overlap == 1` → `MISMATCH`（`SINGLE_TYPE_ONLY`）；
`PARTIAL` 需 ≥2 类型 + 可比 chronology；`MATCH` 需集合相等 + 首项相同。
`event_structure = PARTIAL` 从 v0.1 的 **74/85 → 27/85**。

### 5. Driver PARTIAL 是否继续避免类别轴虚高？
✅ **是。** `PERIPHERAL_OVERLAP`（仅外围机制交集）**不计为结构支持**；
`SUPPORTED` 要求 `MATCH` 或 `PARTIAL/MULTI_MECHANISM`。
3 个 `THEME_ONLY` 中 **2 例**的 driver 正是 `PERIPHERAL_OVERLAP`。

### 6. 是否仍然存在跨族结构对应？
✅ **是。** **3 个跨族 `STRUCTURAL_SUPPORTED`**（占 4 个的 75%）。

### 7. 是否仍然存在主题相同但结构不成立的案例？
✅ **是。** **3 例 `THEME_ONLY`，全部同族**：
`COMPUTE-POWER × C-2022-POWER-GRID`（`PERIPHERAL_OVERLAP`）·
`OPTICAL-LINK × C-2019-COMM-5G`（`MISMATCH`）·
`OFFSHORE-WIND × C-2022-POWER-GRID`（`PERIPHERAL_OVERLAP`）。

### 8. 是否仍然存在名字很像但结构不成立的反例？
✅ **是。** `EMBODIED-AI × C-2024-ROBOTAXI` → **`NO_VALID_CORRESPONDENCE`**（未变化，未升级）。

### 9. 当前最大研究瓶颈是什么？
**机制级 Driver 证据深度**：
- `driver = MATCH` 仅 **1/85**；`MULTI_MECHANISM` 仅 **4**；
- 多数 `STRUCTURAL_PARTIAL`（36 条）依赖 `PRIMARY_MECHANISM_OVERLAP`（单机制交集）；
- `Evidence Sequence` 有 **30/85 `NOT_AVAILABLE`**（历史对象 <2 带日期事件）。

→ **不是 vocabulary 问题，而是证据深度问题。**

---

## Boundary

| 项 | 状态 |
|---|---|
| **Research status** | **`Structural Analogy Research v0.2 baseline` 已建立（可引用、可复现）** |
| **Product readiness** | **NO** |
| **Wave 1C** | **`NOT REQUIRED`** |
| **Market / Temporal status** | **`SUPPLEMENTARY_ONLY`**（不参与 Structural Status） |
| **Next research question** | 机制级 Driver 证据深度是否可通过补充 **历史 driving 相位的 DIRECT 证据** 提升？ |

**Product 仍为 NO 的原因**（继续保留）：market context · temporal context · explanation design ·
uncertainty presentation · user interaction · performance · product language。

---

## 明确回答

| 问题 | 回答 |
|---|---|
| schema changed | **NO** |
| export contract changed | **NO** |
| 历史原始数据 changed | **NO** |
| candidate driver changed | **NO** |
| 全部旧产物 changed | **NO**（逐字节保留） |
| `src/**` / Product changed | **NO** |
| 是否新增 score / ranking / probability | **NO** |
| 是否进入 Wave 1C | **NO**（`NOT REQUIRED`） |
| breaking change | **NO** |

---

## Reproducibility

- 生成器：`research/scripts/build_structural_analogy_research_v0_2.py`
  （**deterministic**：无随机 / 无时间依赖 / 无网络 / 无 LLM；规则实现与 Calibration v0.2 一致）。
- 支持 `--check`：产物与重算结果**逐字节一致**（已执行 `run → check → run → check`）。
- 输入：`structural_analogy_research_v0_1.json`（含全部维度状态）·
  `historical_driver_evidence_ledger_v0_1.json`（`primary_mechanism` 推导）。
- **未写** DB / schema / export / `src/**`。

---

*报告结束 · Structural Analogy Research v0.2 · 2026-09-19*
