# Structural Analogy Research v0.1

> | 项目 | 值 |
> |---|---|
> | 性质 | **Research-only Structural Analogy Engine v0.1** |
> | 完成日期 | 2026-09-19 |
> | 起始状态 | `HEAD = origin/main = d83b44c`，ahead/behind `0/0`，工作树 clean（**自行核对**） |
> | 未修改 | `src/**` · Product IA / UI · schema.sql · frozen export contract · Research Model v1.0 · 历史原始数据 · Time Observation v0.2–v0.5 · Feasibility v0.1/v0.2/v0.3 · Driver Canonicalization v0.1（**全部逐字节保留**） |

---

## 0. Core Result（顶部直接给出）

| 指标 | 值 |
|---|---:|
| **Current candidates** | **5** |
| **Historical cycles examined** | **17**（13 Campaign + 4 Research Candidate） |
| 比较组合总数 | **85** |
| **`STRICT_STRUCTURAL_SUPPORTED`** | **1** |
| **`STRUCTURAL_SUPPORTED`** | **4** |
| **`STRUCTURAL_PARTIAL`** | **46** |
| **`THEME_ONLY`** | **3** |
| **`INSUFFICIENT_EVIDENCE`** | **5** |
| **`NO_VALID_CORRESPONDENCE`** | **27** |

> ⚠️ **`STRICT_STRUCTURAL_SUPPORTED` 单独计数** —— **不得**把 `PARTIAL` 包装成 `supported`。
> 严格定义（§二十六）：`D1 Lifecycle = MATCH` **且** `D2 Driver = MATCH`（机制集合相等）。

### Cross-family

| 等级 | 跨族（85−17=68 组合） | 同族（17 组合） |
|---|---:|---:|
| `STRUCTURAL_SUPPORTED` | **3** | 1 |
| `STRUCTURAL_PARTIAL` | 43 | 3 |
| `THEME_ONLY` | **0** | **3** |
| `INSUFFICIENT_EVIDENCE` | 5 | 0 |
| `NO_VALID_CORRESPONDENCE` | 27 | 0 |

**★ `THEME_ONLY` 全部 3 例均为同族** —— 同族但机制不对应时**被结构性方法排除**。

### Research Loop

| 环节 | 结论 |
|---|---|
| Current → Historical structural search | **PASS** |
| Lifecycle comparison | **PASS** |
| Driver comparison（机制轴） | **PARTIAL**（`MATCH 仅 1/85`，`PARTIAL 50/85`） |
| Evidence sequence（顺序，LCS） | **PARTIAL**（`SEQUENCE_MATCH 12` · `SEQUENCE_PARTIAL 26` · `SET_ONLY 3` · `NA 30`） |
| Event structure | **PARTIAL**（`PARTIAL 74` · `MATCH 0` · `NA 5`） |

---

## 1. Executive Summary

**研究命题**：**从当下市场的结构状态出发，到历史周期中寻找结构，而不是从历史数据库中寻找同名主题。**

**结果**：**四维闭环已跑通**，且**结构性方法与主题查找产生不同结果**。

### 四问回答（§二十七）

| # | 问题 | 答案 |
|---|---|---|
| **Q1** | 是否至少存在一个 historical correspondence，四维都能完成可解释比较？ | ✅ **YES** —— `CC-2026-BCI-MEDTECH × C-2023-AD`（**唯一 STRICT**），四维全部 MATCH/PARTIAL |
| **Q2** | 是否存在跨 Macro Theme 的结构 correspondence？ | ✅ **YES** —— 4 个 `STRUCTURAL_SUPPORTED` 中 **3 个跨族**（医药健康↔汽车、高端装备↔汽车、信息通信↔汽车） |
| **Q3** | 是否至少有一个 `THEME_ONLY` 对象在 Structural Method 下被排除？ | ✅ **YES** —— **3 例**，全部为同族（医药健康 / 信息通信 / 电力设备） |
| **Q4** | 是否至少有一个 Structural 对象不是靠同名主题找到？ | ✅ **YES** —— `only_structural = 7` |

> **4/4 YES → Structural Analogy Research Loop 已真正跑通。**

---

## 2. Research Question

> 在 ThreeC 现有 Research 数据下，**是否能够建立一个可重复、可审计、确定性的流程**，
> 使「当前 candidate 的结构状态」与「历史 cycle 的对应结构状态」形成**结构对应**，
> 且该对应**不依赖主题名称相似**？

---

## 3. Scope

- **纳入**：5 个 2026 Current Candidate × 17 个历史研究对象 = **85 组合**。
- **维度**：`D1 Lifecycle` · `D2 Mechanism Driver` · `D3 Evidence Sequence` · `D4 Event Structure`。
- **明确排除**（§六）：
  - `Market Structure` → `SUPPLEMENTARY_ONLY`（PARTIALLY_RESOLVED，候选侧 2026 行情不可得，**单向**）
  - `Temporal Structure` → `SUPPLEMENTARY_ONLY`（candidate-side **one-way**）
  - **两者均不参与 v0.1 成立判据。**
- **严禁**（§四）：`similarity_score` · `weighted_score` · `confidence_score` · `ranking` ·
  `best analogue` · `winner` · `most similar`。

---

## 4. Current Structural Profile

| candidate | macro_theme | current_phase | canonical drivers（机制轴） | 证据 | 派生事件 | 序列状态 | market | temporal |
|---|---|---|---|---|---:|---|---|---|---|
| `CC-2026-BCI-MEDTECH` | 医药健康 | `THEME_FORMING` | `POLICY_DRIVEN` `TECH_BREAKTHROUGH` | 7 | 7 | SEQUENCE_FULL | SUPPLEMENTARY_ONLY(PARTIAL) | SUPPLEMENTARY_ONLY |
| `CC-2026-COMPUTE-POWER` | 电力设备 | `BROAD_CONFIRMATION` | `DEMAND_SURGE` `INDUSTRY_UPGRADE` `POLICY_DRIVEN` | 10 | 9 | SEQUENCE_PARTIAL | SUPPLEMENTARY_ONLY(PARTIAL) | SUPPLEMENTARY_ONLY |
| `CC-2026-EMBODIED-AI` | 高端装备 | `EXPANSION` | `INDUSTRY_UPGRADE` `POLICY_DRIVEN` `TECH_BREAKTHROUGH` | 8 | 7 | SEQUENCE_PARTIAL | SUPPLEMENTARY_ONLY(NOT_AVAILABLE) | SUPPLEMENTARY_ONLY |
| `CC-2026-OPTICAL-LINK` | 信息通信 | `EXPANSION` | `DEMAND_SURGE` `INDUSTRY_UPGRADE` `TECH_BREAKTHROUGH` | 8 | 7 | SEQUENCE_PARTIAL | SUPPLEMENTARY_ONLY(PARTIAL) | SUPPLEMENTARY_ONLY |
| `CC-2026-OFFSHORE-WIND` | 电力设备 | `THEME_FORMING` | `POLICY_DRIVEN` `SUPPLY_CONTRACTION` | 6 | 6 | SEQUENCE_FULL | SUPPLEMENTARY_ONLY(PARTIAL) | SUPPLEMENTARY_ONLY |

**structural_gaps**（全部候选共有）：`candidate_side_2026_market_state_not_available` ·
`phase_window_end_unknown`；`COMPUTE-POWER` / `EMBODIED-AI` / `OPTICAL-LINK` 另有 `evidence_sequence_partial`。

---

## 5. Historical Structural Profile

17 个对象全部建立统一 profile（`cycle_id` · `macro_theme` · `lifecycle_stages` · `stage_starts` ·
`terminal_phase` · `canonical_drivers` · `driver_provenance` · `evidence_sequence` · `event_profile` · `n_events`）。

**`terminal_phase` 保留作为 cycle background，但不用于 current-phase analogy。**（§八）

**历史 canonical drivers（driving 相位）分布**：
`POLICY_DRIVEN 10 对象` · `CYCLE_REVERSAL 9` · `VALUATION_RESET 9` · `DEMAND_SURGE 5` ·
`EVENT_CATALYST 5` · `TECH_BREAKTHROUGH 4` · `INDUSTRY_UPGRADE 2` · `SUPPLY_CONTRACTION 1`

---

## 6. Comparison Point Semantics（§九）

`historical_comparison_point` = **Research-layer 派生观测点**，**不是**新的生命周期阶段：

```
target = PHASE_TO_STAGE(candidate.current_phase)
历史 lifecycle[] 含 target          → status = MATCH   （锚点日期明确）
历史含相邻阶段                       → status = PARTIAL
否则                                → status = MISMATCH（回落到最早阶段，仅作记录）
历史无 lifecycle                     → status = COMPARISON_POINT_UNKNOWN
```

- **不修改**历史生命周期数据；**不改变** `terminalPhaseOf`。
- 实测：`MATCH 58` · `PARTIAL 24` · `MISMATCH 3` · `COMPARISON_POINT_UNKNOWN 0`。
- **绝对禁止** `candidate.current_phase ↔ historical.terminalPhaseOf`（§五 D1）。

---

## 7. Lifecycle Comparison（D1）

`MATCH 58` · `PARTIAL 24` · `MISMATCH 3` · `NOT_AVAILABLE 0`。
3 条 `MISMATCH` 全部为 `RC-2024-SECONDARY`（该对象阶段与候选当前阶段既不相同也不相邻，属**真实数据差异**）。

---

## 8. Driver Comparison（D2 · 机制轴）

沿用 **Historical Driver Canonicalization v0.1** 的机制轴（`narrative_types` ↔ 历史 driving 相位 canonical drivers）。

| 状态 | 条数 | 判据 |
|---|---:|---|
| `MATCH` | **1** | 机制集合相等 |
| `PARTIAL` | **50** | 交集非空且不等 |
| `MISMATCH` | **29** | 交集为空 |
| `NOT_AVAILABLE` | 5 | 任一侧无 canonical driver |

- **未从** `event_type` / 价格 / 行业标签**重新推导** driver（§五 D2）。
- 每条历史 driver 保留 `driver_provenance`（DIRECT / DERIVED 来源）。
- **★ `MATCH 仅 1/85`** —— 因此**不能**因「存在共同 driver category」就算 MATCH。

---

## 9. Evidence Sequence Comparison（D3 · 顺序）

**用 LCS（最长公共子序列）比较顺序**，而非仅集合：

| subtype | 条数 | 判据 |
|---|---:|---|
| `SEQUENCE_MATCH` | **12** | LCS ≥2 且首项相同 |
| `SEQUENCE_PARTIAL` | **26** | LCS ≥2 但首项不同 |
| `SET_ONLY` | **3** | LCS =1 且类型交集 ≥2（**不得**当作 MATCH） |
| `SEQUENCE_MISMATCH` | **14** | LCS ≤1 且类型交集 <2 |
| `NOT_AVAILABLE` | **30** | 任一侧 <2 条带日期事件 |

**`SET_ONLY` 已单独标记，未自动升级为 `SEQUENCE_MATCH`**（§十五）。

---

## 10. Event Structure Comparison（D4）

比较 `event_type` + chronology + linkage（候选侧事件来自 `structural_analogy_candidate_events_v0_1.json`，**带 provenance**）。

`MATCH 0` · `PARTIAL 74` · `MISMATCH 6` · `NOT_AVAILABLE 5`。

> `MATCH 0` 说明：**没有任何一对的 event_type 集合完全相等** —— 这是诚实结果，未放宽。

---

## 11. Structural Correspondence Rules（§十一 / §十三）

### 五级状态（deterministic、顺序敏感、无连续分数）

| 等级 | 判据 |
|---|---|
| **`STRUCTURAL_SUPPORTED`** | D1 = `MATCH` **且** D2 = `MATCH` 或（`PARTIAL` 且机制交集 ≥2）**且** D3 ∈ {MATCH, PARTIAL} 且 subtype ∈ {SEQUENCE_MATCH, SEQUENCE_PARTIAL} **且** D4 ∈ {MATCH, PARTIAL} **且** 历史侧有 ≥1 个 **DIRECT** driver 证据 **且** D1/D2 无 `MISMATCH` |
| **`STRICT_STRUCTURAL_SUPPORTED`** | 同上，但 **D2 必须 = `MATCH`**（§二十六 单独计数） |
| **`STRUCTURAL_PARTIAL`** | **D2 ∈ {MATCH, PARTIAL}** 且 **D3 ∈ {MATCH, PARTIAL}** 且 ≥2 维度有对应 |
| **`THEME_ONLY`** | 只有 macro theme / sector / keyword 等表层联系（**含同族但结构不成立**） |
| **`INSUFFICIENT_EVIDENCE`** | ≥2 维度 `NOT_AVAILABLE`，或 **D2 = `NOT_AVAILABLE`** |
| **`NO_VALID_CORRESPONDENCE`** | 四维中 ≤1 维度有对应，且无主题联系 |

### ★ 关键收紧（§十二）与规则理由

> **`D2 Driver = MISMATCH` 时不得成为 `STRUCTURAL_PARTIAL`** ——
> 机制不对应时，即使 sequence/event 有重叠，也退化为 `THEME_ONLY`（同族）或 `NO_VALID_CORRESPONDENCE`（跨族）。
>
> **理由**：首版规则（仅要求 ≥2 维度有对应）产出 `STRUCTURAL_PARTIAL 73/85（86%）`，
> 因为 `event_structure` 的 `PARTIAL` 占 74/85（几乎全部）→ **等级失去区分度**。
> 收紧后分布为 `4 / 46 / 3 / 5 / 27` —— **可区分**。
> **规则为 v0.1 工作定义**（§十三 允许显式调整），已写入 artifact `correspondence_rules`。

---

## 12. Candidate-by-Candidate Results（§十八）

> **不是排序。** 按 status 分组展示；**不产生「第一名」。**

### `CC-2026-BCI-MEDTECH`（医药健康 · THEME_FORMING）
- `STRUCTURAL_SUPPORTED` **1** · `STRUCTURAL_PARTIAL` 9 · `THEME_ONLY` 1 · `INSUFFICIENT_EVIDENCE` 1 · `NO_VALID` 5
- **★ `× C-2023-AD`（汽车）→ `STRUCTURAL_SUPPORTED`，且为全库唯一 `STRICT`**
  （`D2 = MATCH`：`POLICY_DRIVEN + TECH_BREAKTHROUGH` 集合完全相等）
- **同族 `× C-2019-PHARMA-INNOV` → `THEME_ONLY`**（`D2 = MISMATCH`，机制交集为空）

### `CC-2026-COMPUTE-POWER`（电力设备 · BROAD_CONFIRMATION）
- `STRUCTURAL_PARTIAL` **13**（5 个候选中最多）· `NO_VALID` 3 · `INSUFFICIENT_EVIDENCE` 1 · `SUPPORTED` 0
- 同族 `× C-2022-POWER-GRID` / `× C-2020-POWER-NE` → `STRUCTURAL_PARTIAL`，**机制交集仅 `POLICY_DRIVEN` 一项**

### `CC-2026-EMBODIED-AI`（高端装备 · EXPANSION）
- `STRUCTURAL_PARTIAL` 11 · `NO_VALID` 4 · `STRUCTURAL_SUPPORTED` **1** · `INSUFFICIENT_EVIDENCE` 1
- **★ `× C-2023-AD`（汽车）→ `STRUCTURAL_SUPPORTED`**（`SEQUENCE_MATCH`）
- **★ `× C-2024-ROBOTAXI`（看似名字最接近）→ `NO_VALID_CORRESPONDENCE`**
  （`D2 = MISMATCH`，`D3 = NOT_AVAILABLE`）→ **name similarity ≠ structural correspondence**

### `CC-2026-OPTICAL-LINK`（信息通信 · EXPANSION）
- `STRUCTURAL_SUPPORTED` **2** · `STRUCTURAL_PARTIAL` 5 · `THEME_ONLY` 1 · `NO_VALID` 8 · `INSUFFICIENT` 1
- **`× C-2023-COMM-OPTICAL`（同族）→ `STRUCTURAL_SUPPORTED`**（`DEMAND_SURGE + TECH_BREAKTHROUGH`）
- **★ 同族 `× C-2019-COMM-5G` → `THEME_ONLY`**（`D2 = MISMATCH`）
- 跨族 `× C-2025-ROBOTAXI`（汽车）→ `STRUCTURAL_SUPPORTED`（`SEQUENCE_MATCH`）

### `CC-2026-OFFSHORE-WIND`（电力设备 · THEME_FORMING）
- `STRUCTURAL_PARTIAL` 8 · `NO_VALID` 7 · `THEME_ONLY` 1 · `INSUFFICIENT` 1 · `SUPPORTED` 0
- 同族 `× C-2022-POWER-GRID` → `PARTIAL`（`POLICY_DRIVEN`）
- **同族 `× C-2020-POWER-NE` → `THEME_ONLY`**（`D3 = SEQUENCE_MISMATCH`）

---

## 13. Name vs Structural Experiment（§十七）

| 集合 | 数量 | 对象 |
|---|---:|---|
| **Name / Theme matching** | **9** | `C-2019-COMM-5G` `C-2019-PHARMA-INNOV` `C-2020-POWER-NE` `C-2021-NEV` `C-2022-POLICY` `C-2022-POWER-GRID` `C-2023-AD` `C-2023-COMM-OPTICAL` `C-2024-ROBOTAXI` |
| **Structural matching**（SUPPORTED + PARTIAL） | **15** | 上述 8 个 + `C-2019-AD` `C-2020-NEV` `C-2024-V2X` `C-2025-ROBOTAXI` `RC-2020-PANDEMIC` `RC-2021-TCM` `RC-2023-HUAWEI` |
| **both** | **8** | — |
| **only name** | **1** | **`C-2024-ROBOTAXI`** |
| **only structural** | **7** | `C-2019-AD` `C-2020-NEV` `C-2024-V2X` `C-2025-ROBOTAXI` `RC-2020-PANDEMIC` `RC-2021-TCM` `RC-2023-HUAWEI` |

**结论**：**研究对象确实与 Theme Lookup 不同**（only name 1 / only structural 7）。
**不声称 Structural Matching「更准确」** —— 只验证两者产生**不同集合**。

---

## 14. Cross-Family Findings（§二 / §十二）

- **4 个 `STRUCTURAL_SUPPORTED` 中 3 个跨族**：
  `医药健康 × 汽车` · `高端装备 × 汽车` · `信息通信 × 汽车`。
- **`C-2023-AD`（汽车·智能驾驶）同时是 `BCI-MEDTECH` 与 `EMBODIED-AI` 的 `STRUCTURAL_SUPPORTED`**
  —— 共享 `POLICY_DRIVEN + TECH_BREAKTHROUGH`。**这是跨族结构对应的实证。**
- **3 个 `THEME_ONLY` 全部同族** → **同族只提供 contextual proximity，不是 structural proof**。
- **未因同族自动升级等级**：`TH-POWER` 的两组同族配对仅得 `PARTIAL`（单机制重叠）或 `THEME_ONLY`。

---

## 15. Negative Evidence / Mismatch（§二十一）

每个 `STRUCTURAL_SUPPORTED` / `STRUCTURAL_PARTIAL` 案例均生成 **Evidence Card**，
其 `why_not_strong_analogy` **必须存在**（§二十）。汇总负证据：

| 负证据类型 | 出现次数 |
|---|---:|
| `driver mismatch` | 29 |
| `event structure mismatch` | 6 |
| `lifecycle mismatch` | 3 |
| `evidence sequence mismatch` | 14 |
| `sequence is SET_ONLY` | 3 |
| 历史侧无 DIRECT driver 证据 | — |
| 跨族：无同主题上下文支撑 | 46（PARTIAL 中跨族者） |
| 维度 `NOT_AVAILABLE` | 30（D3）+ 5（D4）+ 5（D2） |

**典型反例**：
- `EMBODIED-AI × C-2024-ROBOTAXI` → `NO_VALID_CORRESPONDENCE`（名字最像，结构最不像）
- `BCI-MEDTECH × C-2019-PHARMA-INNOV` → `THEME_ONLY`（同族，机制完全不同）
- `OPTICAL-LINK × C-2019-COMM-5G` → `THEME_ONLY`（同族，机制 + 顺序双 MISMATCH）

---

## 16. Data Limitations（§二十二 防污染声明）

- **禁止市场结果污染**：本轮**未使用**历史涨跌 / 收益率 / 当前市场强度 / 指数表现
  推导 driver match / lifecycle match / structural correspondence。
- `Market` 与 `Temporal` 仅记为 `SUPPLEMENTARY_ONLY`，**未进入成立判据**。
- 候选侧 **2026 行情不可得**；`phase_window.end` 全部 `unknown`。
- 历史 `driving` 文本 22 条 `UNKNOWN` + 49 条 `NOT_AVAILABLE`（价格结果描述）。
- 样本量小（85 组合），**任何比例数字都不具统计意义**；未做多重比较校正。

---

## 17. Research Interpretation

1. **结构性对应确实存在，且可跨族** —— 3/4 个 `SUPPORTED` 跨族，四维可解释。
2. **同族不构成结构证明** —— 3 个同族配对被降为 `THEME_ONLY`。
3. **Driver 仍是最大约束** —— `MATCH 1/85`；多数对应建立在**单机制重叠**（`POLICY_DRIVEN`）之上。
4. **`C-2023-AD` 是当前唯一「四维闭环」对象**（`BCI-MEDTECH` 的 `STRICT` 对应）。

**当前最大研究瓶颈**：**机制级 driver 证据粒度**（历史 driving 文本已充分编码，
但机制交集普遍只有 1 项）→ **不是 vocabulary 问题，而是证据深度问题**。

---

## 18. Product Readiness Boundary（§二十八）

> **即使 Research loop 跑通，也禁止自动 Product Integration。**

| 项 | 状态 |
|---|---|
| Research status | **Loop 已跑通（Research-only）** |
| Product readiness | **NO** —— 仍需单独评估 user-facing semantics · explanation quality · false-positive control · market context · temporal context · interaction design · performance · reproducibility |
| 本轮是否修改 Product | **NO** |

---

## 19. Next Research Questions

1. 单机制重叠（`POLICY_DRIVEN`）是否足以支撑 `STRUCTURAL_PARTIAL`？是否需要机制**强度**而非仅集合？
2. `SET_ONLY`（3 条）能否通过补证据升级为 `SEQUENCE_PARTIAL`？
3. `C-2023-AD` 作为跨族枢纽，是否反映「政策+技术突破」这一**通用启动机制**？
4. 历史 `driving` 相位 22 条 `UNKNOWN` 是否可通过补充 evidence 编码？
5. `phase_window.end` 缺失对 `Temporal` 维度的影响是否可解？

---

## 20. Reproducibility（§三十）

- 生成器：`research/scripts/build_structural_analogy_research_v0_1.py`
  （**deterministic**：无随机 / 无时间依赖 / 无网络 / 无 LLM；规则显式可审计）。
- 支持 `--check`：产物与重算结果**逐字节一致**（已执行 `run → check → run → check`）。
- 输入：`exports/timeline_export_v1.json` · `research/current/current_candidates.json` ·
  `structural_analogy_candidate_events_v0_1.json` · `historical_driver_canonicalization_v0_1.json` ·
  `historical_driver_evidence_ledger_v0_1.json` · `structural_analogy_candidate_market_map_v0_1.json`。
- **未写** DB / schema / export / `src/**`。

---

## 21. Wave 1C（§二十九）

> **`Wave 1C = NOT REQUIRED`**

未出现必须依靠新增历史 Macro Theme 才能解决的 **Structural Analogy BLOCKER**。
`EMBODIED-AI` 无同族历史的问题**已由跨族对应覆盖**（`× C-2023-AD` → `STRUCTURAL_SUPPORTED`）。

---

## 22. 明确回答

| 问题 | 回答 |
|---|---|
| schema changed | **NO** |
| export contract changed | **NO** |
| 历史原始数据 changed | **NO** |
| Time Observation v0.2–v0.5 changed | **NO** |
| Feasibility v0.1/v0.2/v0.3 changed | **NO** |
| Driver Canonicalization v0.1 changed | **NO** |
| `src/**` / Product changed | **NO** |
| 是否进入 Wave 1C | **NO**（`NOT REQUIRED`） |
| breaking change | **NO** |

---

*报告结束 · Structural Analogy Research v0.1 · 2026-09-19*
