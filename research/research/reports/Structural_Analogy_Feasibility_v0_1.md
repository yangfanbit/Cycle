# Structural Analogy Feasibility v0.1

> | 项目 | 值 |
> |---|---|
> | 性质 | **Feasibility Check（可行性审计）—— 不是 Structural Analogy 实现** |
> | 完成日期 | 2026-09-18 |
> | 起始状态 | `HEAD = origin/main = fd5914f`，ahead/behind `0/0`，工作树 clean（**自行核对**） |
> | 产物 | `structural_analogy_feasibility_v0_1.json` · `structural_analogy_feasibility_candidates_v0_1.csv` · 本报告 |
> | 未修改 | `src/**` · Product IA / Timeline / UI · Research Model v1.0 · frozen export contract · 历史数据 |

---

## 1. Executive Summary

**核心问题**：ThreeC 当前是否已具备「从当下状态出发，在历史周期中寻找**结构**相似阶段」的最小可用研究基础？

**结论**：**`PARTIALLY_FEASIBLE`** —— 机制上可算，但**不足以进入 Product**。

### 三个关键数字

| # | 指标 | 数量 | 候选 |
|---|---|---:|---|
| 1 | **有结构可用历史类比**（严格口径） | **1 / 5** | `CC-2026-BCI-MEDTECH` |
| 2 | **仅有主题/名称级类比** | **4 / 5** | `CC-2026-COMPUTE-POWER` · `CC-2026-EMBODIED-AI` · `CC-2026-OPTICAL-LINK` · `CC-2026-OFFSHORE-WIND` |
| 3 | **无任何可用历史类比** | **0 / 5** | — |

> **`usable structural analogue ≠ same-theme match`**
> 「严格口径」= `lifecycle stage MATCH` **且** `drivers MATCH`（阶段对齐 + driver 集合完全一致）。

**若放宽到 TIER_1**（stage MATCH + driver 弱匹配 + evidence_sequence 可比较）→ **5/5 候选均有**。
但 `drivers = PARTIAL` 占 **71/85** 行（只要共享 1 个 driver 即为 PARTIAL）→ **TIER_1 的 5/5 主要由弱匹配贡献，不得据此宣称结构类比已可用**。

### 三项决定性发现

1. **★ 语义断层**：历史对象的 `terminalPhaseOf` **12/17 = `END`**（历史 Campaign 均已结束）。
   用「候选**当前**阶段 vs 历史**终态**」比较 → 80/85 行直接 `MISMATCH`。
   → 结构类比**必须**改用 **stage-aligned** 口径（历史 `lifecycle[]` 是否包含该阶段）：58/85 行转为 `MATCH`。
2. **★ 两个维度双侧 NOT_AVAILABLE**：`event_structure` **85/85 NOT_AVAILABLE**（候选侧无事件台账实体）、
   `market_structure` **85/85 NOT_AVAILABLE**（候选侧无可映射行情序列）。
   `temporal_structure` 只能**单向**比较（候选只有 1 个 phase_window 起点，`end` 全为 null）。
3. **★ 跨族结构相似性确实存在**：TIER_1 的 23 条组合中 **20 条为跨族**（同族仅 3 条）。
   → 结构匹配**不等于**名称匹配，核心产品理念**部分可被实现**。

---

## 2. Repo Baseline

```
git status --short                          → 无输出（clean）
git rev-parse HEAD                          → fd5914f6e2441f6ca632d410c4afc11b90519a69
git branch --show-current                   → main
git log --oneline -10                       → fd5914f (HEAD -> main, origin/main) research: run time observation discovery v0.5
                                              d3fa89f fix(research): clean unsupported historical date claims
                                              2c16058 research: verify time observation anchors
                                              707224b research: add historical information communication cycles
                                              052b79b research: add coverage audit v0.2 (post Wave 1A)
                                              cc4c2d4 research: add historical power equipment cycles
                                              f446cb8 docs(state): rebuild PROJECT_STATE from verified repo state; record recovery
                                              ff8b6eb docs(repo): record Repository Recovery Report 2026-09-17
                                              e85fb42 chore(repo): reconcile research workspace and restore canonical state
                                              c968097 fix(research): exclude derived time structures from promotion
git rev-parse origin/main                   → fd5914f6e2441f6ca632d410c4afc11b90519a69
git diff --stat                             → 空
git diff --cached --stat                    → 空
ahead/behind                                → 0  0
```
**未提交 / 未追踪 / staged 文件：无。** HEAD 与 origin/main 一致，与任务书描述相符（**已自行核对，未采信**）。

---

## 3. Dataset Baseline

| 项 | 值 |
|---|---|
| Years（观测） | **2019–2025**（2018 = `no_clear_campaign`，保留既有语义） |
| Macro Themes（CMTR v1） | **4**：`TH-AUTO` 汽车 · `TH-PHARMA` 医药健康 · `TH-POWER` 电力设备 · `TH-COMM` 信息通信 |
| Theme Cycles / Campaigns | **13 / 13**（+4 Research Candidate = **17 个研究对象**） |
| Evidence | **83** |
| Events | **49 DB / 52 export** |
| market_series | **56**（benchmark 1 · concept_index 4 · industry_index 4 · stock 47） |
| Current Candidates | **5**（`current_candidates_version = 1.0`，snapshot `2026-09-15`） |

**研究对象规模（按 export 的 industry 级主题统计）**：汽车 **7** · 电力设备 **2** · 信息通信 **2** · 医药健康 **1** · 新能源汽车/电池 **1**。

---

## 4. Structural Analogy Definition（v0.1 工作定义）

> **Structural Analogy** = 从**当前候选的结构特征**出发，在历史周期中寻找**结构维度上对应**的阶段，
> 而**不是**寻找同名 / 同行业 / 同关键词的历史对象。

**明确排除**作为主要依据：名称相似 · 关键词重合 · 行业名称重合 · 公司名称重合 · 「都是机器人/光模块/新能源」式表面相似。

**采用的六个结构维度**（全部取自仓库既有字段，**未新造 taxonomy**）：

| 维度 | 数据来源 | 可比性 |
|---|---|---|
| **1 Lifecycle** | `candidate.attention_state` vs `STAGE_TO_PHASE(历史 lifecycle)` | ✅ 同枚举（`ResearchPhase`） |
| **2 Driver** | `candidate.drivers[].category` vs `EVENT_TYPE_TO_DRIVER(历史 events[].event_type)` | ✅ 同枚举（POLICY/INDUSTRY/CAPITAL/SENTIMENT/EXTERNAL） |
| **3 Evidence Sequence** | `candidate.evidence[].source_type` 顺序 vs 历史 `events[].event_type` 顺序 | ⚠️ 词表不同，需人工映射 |
| **4 Market Structure** | 候选可映射行情序列 / 历史窗口采样行情 | ❌ 候选侧无 |
| **5 Event Structure** | 历史 `events` 台账 / 候选事件实体 | ❌ 候选侧无 |
| **6 Temporal Structure** | 阶段间距 / evidence 间距 | ⚠️ 只能单向 |

**状态取值**：`MATCH` · `PARTIAL` · `UNKNOWN` · `NOT_AVAILABLE` · `MISMATCH`（**不伪造二元真值**）。
**明确不产出**：similarity score · ranking · winner · best analogue · prediction · future outcome inference。

---

## 5. Feasibility Criteria（A–G 实测）

### Criterion A — Historical coverage → **PARTIAL**
13 Campaign / 13 Theme Cycle / 4 Macro Theme。但**每族仅 1–7 个**（汽车 7 · 电力设备 2 · 信息通信 2 · 医药健康 1）。
> `theme_family_count = 4` **只是覆盖条件，不等于样本充足**。
> Time Observation v0.5 已实测：`TH-POWER` / `TH-COMM` 因各仅 2 个 Cycle（< N≥3）→ **产出 0 个 family 级候选**。

### Criterion B — Lifecycle coverage → **PARTIAL**

| stage | 覆盖（/17） | 比例 |
|---|---:|---:|
| `EARLY_SIGNAL` | 17 | 100.0% |
| `MAIN_RISE` | 14 | 82.4% |
| `MAIN_END` | 14 | 82.4% |
| `PEAK` | 15 | 88.2% |
| `THEME_FORMING` | 10 | 58.8% |
| `BROAD_CONFIRMATION` | 10 | 58.8% |
| `DECLINING` | 10 | 58.8% |
| `RETRACEMENT` | 6 | 35.3% |
| `SECONDARY` | 6 | 35.3% |
| **`FIRST_DECLINE`** | **1** | **5.9%** ← 仍然大量 unknown |

**★ 关键**：历史 `terminal_phase` 分布 = `END` **12** · `DECLINE` 3 · `EXPANSION` 1 · `PEAK` 1。
**没有任何历史对象的终态是 `THEME_FORMING` 或 `BROAD_CONFIRMATION`。**

### Criterion C — Driver coverage → **PARTIAL**

| driver | 历史出现次数（对象数） | 当前候选出现次数 |
|---|---:|---:|
| `POLICY` | 10 | 5 |
| `INDUSTRY` | 7 | 5 |
| `CAPITAL` | 4 | 3 |
| `SENTIMENT` | **0（恒不可派生）** | 0 |
| `EXTERNAL` | 1 | 1 |

- 历史侧 **16/17** 对象有 ≥1 driver（由 `events[].event_type` 反推）。
- **缺口**：① 历史 `drivers` 字段本身是**自由文本**（start/accelerator/turning/ending），未结构化；
  ② `industry` event_type **未映射**到 driver → 丢失；③ `SENTIMENT` 历史侧**恒不可派生**。

### Criterion D — Evidence sequence coverage → **PARTIAL**

| 事件数 | 对象数 |
|---|---:|
| 0 | 1 |
| 1 | 5 |
| ≥2 | **11** |
| ≥3 | **9** |

→ 11/17 可做 `A → B` 顺序比较、9/17 可做 `A → B → C`。
**缺口**：候选侧只有 `evidence`（无事件台账），两侧**实体类型不同**；且 5/17 历史对象仅 0–1 事件。

### Criterion E — Event coverage → **NOT_AVAILABLE（候选侧）**

| event_type | DB 条数 | 可映射 driver |
|---|---:|---|
| `policy` | 28 | ✅ POLICY |
| `company` | 15 | ✅ INDUSTRY |
| `market` | 4 | ✅ CAPITAL |
| `industry` | 2 | ❌ **未映射** |
| `macro` | 0 | ✅ EXTERNAL（映射存在但无数据） |

**★ 必须明确**：Time Observation v0.5 已判定 `INDUSTRY_EVENT_DRIVEN` / `DATA_RELEASE_DRIVEN` 为 **`NOT_AVAILABLE`**。
Structural Analogy **受到完全相同的数据缺口限制**：
- 候选侧**无事件实体** → `event_structure` 维度 85/85 `NOT_AVAILABLE`；
- 缺行业事件日历 / 制度性数据发布日历 → 无法做事件驱动的结构对齐。
**`NOT_AVAILABLE` ≠ `NO_PATTERN`。**

### Criterion F — Market data coverage → **NOT_AVAILABLE（候选侧）**

| 类型 | 条数 | 非空 |
|---|---:|---:|
| `benchmark` | 1 | 1 |
| `concept_index` | 4 | **0（全为空占位）** |
| `industry_index` | 4 | 2（AUTO_ETF_516110 · PHARMA_ETF_512010） |
| `stock` | 47 | 大部分非空 |
| **合计** | **56** | **6 条空占位** |

**真实结论**：
- 历史侧行情是**「按 Campaign 窗口采样」**，不是连续序列 → 无法做 breadth / 相对走势 / 波动比较。
- **候选侧 5 个 2026 candidate 全部没有可映射的行情序列**（2026 无证券数据）。
→ **`market structure` 不可用**，不得以「存在 `market_series` 表」当作可用。

### Criterion G — Cross-family evidence → **PARTIAL（但正向）**

TIER_1 的 23 条组合中：**同族 3 · 跨族 20**。
Method B（结构匹配）命中的 6 个历史对象按族分布：**汽车 4** · 信息通信 1 · 电力设备 1
—— 而候选分属医药健康 / 电力设备 / 高端装备 / 信息通信。

→ **跨 Macro Theme 的结构相似性证据确实存在**，不是只能同族。
**但**：样本量小、driver 匹配多为 `PARTIAL`（1 个重叠）→ 只能判 **PARTIAL**。

---

## 6. Current Candidate Structural Profiles

| candidate | macro_theme | phase | phase_window.start | drivers | evidence | 首条证据 | 窗口→首证据 |
|---|---|---|---|---|---:|---|---:|
| `CC-2026-BCI-MEDTECH` | 医药健康 | `THEME_FORMING` | 2026-06-30 | POLICY, INDUSTRY | 7 | 2026-01-06 | −175 天 |
| `CC-2026-COMPUTE-POWER` | 电力设备 | `BROAD_CONFIRMATION` | 2026-05-08 | POLICY, INDUSTRY, CAPITAL | 10 | 2026-04-22 | −16 天 |
| `CC-2026-EMBODIED-AI` | 高端装备 | `EXPANSION` | 2026-02-28 | POLICY, INDUSTRY, CAPITAL | 8 | 2026-04-23 | +54 天 |
| `CC-2026-OPTICAL-LINK` | 信息通信 | `EXPANSION` | 2026-06-01 | INDUSTRY, CAPITAL, POLICY | 8 | 2026-04-27 | −35 天 |
| `CC-2026-OFFSHORE-WIND` | 电力设备 | `THEME_FORMING` | 2026-09-10 | POLICY, INDUSTRY, EXTERNAL | 6 | 2026-09-10 | 0 天 |

**结构性缺口（全部 5 个候选共有）**：`phase_window.end` **全为 `null`** → 无法计算候选侧阶段间距；
`event` 实体缺失；无可映射行情序列。

---

## 7. Historical Comparison Pool

**纳入规则**（机械、可复核）：全部 17 个研究对象（13 Campaign + 4 Research Candidate）均进入 comparison pool。
**Macro Theme 只用作 `context` 与 `same_macro_theme` 标记，不作为纳入理由。**

> 明确拒绝的做法：**不因为 `TH-POWER == TH-POWER` 就自动视为 comparable。**

---

## 8. Candidate-by-Candidate Analysis

### 8.1 `CC-2026-OFFSHORE-WIND`（海上风电与整机价格修复）
- **终态口径**：usable **0**（所有历史对象终态均为 END/DECLINE/EXPANSION/PEAK，与其 THEME_FORMING 不符）
- **stage-aligned 口径**：usable **10**（同族 2）；**TIER_1 = 3** → `C-2023-AD` · `C-2023-COMM-OPTICAL` · `C-2022-POWER-GRID`
- **同族**：`C-2020-POWER-NE`（发电设备）· `C-2022-POWER-GRID`（电网）—— 但 `C-2020-POWER-NE` 未达 TIER_1
- **判断**：**有结构上有意义的历史对象**（`C-2022-POWER-GRID` 为同族 stage+driver+seq 匹配）。
  政策→产业→公司的顺序在 `C-2022-POWER-GRID` 有对应。**不因行业不同而排除，也不因同行业而自动采纳。**
- **缺口**：`EXTERNAL` driver 在历史侧仅 1 个对象具备 → 该维度基本无对应。

### 8.2 `CC-2026-COMPUTE-POWER`（算电协同）
- **终态口径**：usable **1**（`RC-2023-HUAWEI`）
- **stage-aligned**：usable **10**（同族 2）；**TIER_1 = 5** → `C-2022-POLICY` · `C-2023-AD` · `C-2025-ROBOTAXI` · `C-2023-COMM-OPTICAL` · `C-2022-POWER-GRID`
- **判断**：**有可用历史对象**，其中 `C-2022-POWER-GRID`（同族）与 `C-2022-POLICY`（跨族）为 infra/capex 型结构。
- **缺口**：`BROAD_CONFIRMATION` 阶段的历史样本仅 10/17，且候选的 `phase_window.end = null` → 无法判断其在该阶段已停留多久。

### 8.3 `CC-2026-EMBODIED-AI`（具身智能与人形机器人）
- **终态口径**：usable **2**；**stage-aligned**：usable **13（同族 0）**；**TIER_1 = 6（同族 0）**
- **为什么"没有历史 comparable"必须被拆开**：
  - **不是**「历史上没有类似」（结构上有 6 个 TIER_1 对象，且**全部跨族**）；
  - **而是**：① **historical coverage insufficient** —— 其 Macro Theme **`高端装备` 在历史侧完全不存在**
    （Coverage Audit v0.3 的 `declared_but_no_history` 唯一剩余项）；
    ② **data missing** —— 无可映射行情序列、无事件实体；
    ③ **lifecycle not sufficiently documented** —— 其 `phase_window.end` 缺失。
- **判断**：**跨族结构类比可用，同族类比根本不存在（因为该族无历史）。**

### 8.4 `CC-2026-OPTICAL-LINK`（高速光互联）
- **终态口径**：usable **2**（`C-2023-COMM-OPTICAL` · `RC-2023-HUAWEI`）
- **stage-aligned**：usable **13（同族 2）**；**TIER_1 = 6（同族 1）** → `C-2021-NEV` · `C-2022-POLICY` · `C-2023-AD` · `C-2025-ROBOTAXI` · **`C-2023-COMM-OPTICAL`** · `C-2022-POWER-GRID`
- **`TH-COMM` 历史 cycles 提供的是**：
  - **structural analogue**：`C-2023-COMM-OPTICAL`（同族、stage `MAIN_RISE` 存在、driver 匹配）✅
  - **不是**仅有 theme/industry analogue —— 该对象在 lifecycle + driver + evidence_sequence 三维均可比较
- **判断**：**这是 5 个候选中结构支撑最强的**（唯一同时具备同族 + 跨族 TIER_1）。
- **缺口**：`C-2019-COMM-5G`（同族另一 Cycle）**未达 TIER_1** → 同族类比只有 1 个可用对象。

### 8.5 `CC-2026-BCI-MEDTECH`（脑机接口医疗器械）
- **终态口径**：usable **0**；**stage-aligned**：usable **10（同族 1）**；**TIER_1 = 3（同族 0）**
- **★ 唯一达到严格口径（STRICT_B：stage MATCH + drivers MATCH）的候选** → 3 个对象：
  `C-2023-AD` · `C-2023-COMM-OPTICAL` · `C-2022-POWER-GRID`
- **PHARMA 历史数据能支持到什么程度**：
  - `C-2019-PHARMA-INNOV`（唯一同族对象）**未达 TIER_1**（其 stage 存在但 driver 仅 1 个重叠）
  - → **PHARMA 只有 1 个历史 Cycle，不足以支撑族内结构类比**
- **判断**：**明确不因 PHARMA 样本少而强行类比**；其可用对象**全部来自跨族**。

---

## 9. Structural Match / Mismatch Matrix

完整 85 行（5 候选 × 17 历史对象）见 `structural_analogy_feasibility_candidates_v0_1.csv`。
**维度状态分布（85 行）**：

| 维度 | 分布 |
|---|---|
| `lifecycle_terminal` | MISMATCH **80** · PARTIAL 3 · MATCH 2 |
| `lifecycle_stage_presence` | MATCH **58** · MISMATCH 27 |
| `drivers` | **PARTIAL 71** · MISMATCH 6 · NOT_AVAILABLE 5 · MATCH 3 |
| `evidence_sequence` | NOT_AVAILABLE 30 · PARTIAL 27 · MISMATCH 22 · MATCH 6 |
| `event_structure` | **NOT_AVAILABLE 85** |
| `temporal_structure` | NOT_AVAILABLE 40 · PARTIAL 45 |
| `market_structure` | **NOT_AVAILABLE 85** |

**★ 敏感性分析（必须同时披露，不得只报最宽口径）**

| 口径 | 组合数 | 覆盖候选 |
|---|---:|---:|
| `STRICT_A`：stage + drivers + seq 全 MATCH | **0** | **0 / 5** |
| `STRICT_B`：stage + drivers MATCH | **3** | **1 / 5** |
| `TIER_1`：stage + driver 弱匹配 + seq 可比较 | 23 | 5 / 5 |

> `TIER_1` 之所以宽松，是因为 `drivers = PARTIAL` 占 71/85 行 —— **只要两边共享 1 个 driver 即为 PARTIAL**。

---

## 10. Name Matching vs Structural Matching Experiment（§九）

**Method A** = Name / Theme matching（同 Macro Theme + 人工 `reference_cases`）
**Method B** = Structural matching（TIER_1 多维结构匹配）

| candidate | A（名称/主题） | B（结构） | A∩B | 仅 A | 仅 B |
|---|---|---|---|---|---|
| `CC-2026-BCI-MEDTECH` | 2 | 3 | 1 | 1 | 2 |
| `CC-2026-COMPUTE-POWER` | 3 | 5 | 1 | 2 | 4 |
| `CC-2026-EMBODIED-AI` | 3 | 6 | 1 | 2 | 5 |
| `CC-2026-OPTICAL-LINK` | 3 | 6 | 2 | 1 | 4 |
| `CC-2026-OFFSHORE-WIND` | 3 | 3 | 1 | 2 | 2 |

**并集对比**：

| | 数量 | 对象 |
|---|---:|---|
| Method A 覆盖 | 9 | C-2019-COMM-5G · C-2019-PHARMA-INNOV · C-2020-POWER-NE · C-2021-NEV · C-2022-POLICY · C-2022-POWER-GRID · C-2023-AD · C-2023-COMM-OPTICAL · C-2024-ROBOTAXI |
| Method B 覆盖 | 6 | C-2021-NEV · C-2022-POLICY · C-2022-POWER-GRID · C-2023-AD · C-2023-COMM-OPTICAL · C-2025-ROBOTAXI |
| **交集** | **5** | C-2021-NEV · C-2022-POLICY · C-2022-POWER-GRID · C-2023-AD · C-2023-COMM-OPTICAL |
| **仅 A**（名称相似但结构未达 TIER_1） | **4** | **C-2019-COMM-5G** · **C-2019-PHARMA-INNOV** · **C-2020-POWER-NE** · **C-2024-ROBOTAXI** |
| **仅 B**（名称不同但结构达 TIER_1） | **1** | **C-2025-ROBOTAXI** |

**结论（不声称 B 更好）**：
- 两套方法的结果**确实不同** —— 仅 A 有 4 个、仅 B 有 1 个。
- **仅 A 的对象全部是「同族但结构不匹配」**（如 `C-2019-PHARMA-INNOV` 对 BCI-MEDTECH、
  `C-2020-POWER-NE` 对 OFFSHORE-WIND）→ 正是「只因名字相似而进入」的对象。
- **仅 B 的对象 `C-2025-ROBOTAXI`** 与 EMBODIED-AI / OPTICAL-LINK 名称毫不相关，
  但因 stage + driver + seq 可比而进入。
- → **ThreeC 的核心产品理念在数据层面部分可被实现**，但受 §9 的维度缺口限制（尤其 market / event 两侧）。

---

## 11. Data Availability Audit

见 §5 Criteria A–G 与 JSON 的 `sensitivity_analysis.dimension_status_distribution`。
**一句话总结**：**数据侧有 3 个维度可用（lifecycle stage-aligned / driver / evidence sequence）、
2 个维度双侧不可用（market / event）、1 个维度只能单向（temporal）。**

---

## 12. Cross-Family Analysis

| 项 | 结果 |
|---|---|
| 历史 Macro Theme 数 | **4**（`TH-AUTO` / `TH-PHARMA` / `TH-POWER` / `TH-COMM`） |
| 产出 family 级稳健候选的族 | **1**（`TH-AUTO`，Time Observation v0.5 实测） |
| TIER_1 组合：同族 / 跨族 | **3 / 20** |
| Method B 命中的历史对象按族 | 汽车 **4** · 信息通信 **1** · 电力设备 **1** |
| 同族类比可用性 | `CC-2026-OPTICAL-LINK` ✅（1 个）· `CC-2026-OFFSHORE-WIND` ✅（1 个）· 其余 3 个候选 ❌ |
| 跨族类比可用性 | **5 / 5 候选均有** |
| 无有效类比 | **0 / 5** |

**区分**：
- **same-family analogy**：存在但样本极少（每族 1–2 个可用对象）。
- **cross-family analogy**：**存在且是当前主要来源**（20/23）。
- **no-valid-analogy**：**不存在**。

> **跨族 analogy 不是可行性的必要条件** —— 但本轮实测显示它恰恰是当前**唯一较充分的**来源。

---

## 13. Blocking Gaps

| # | 缺口 | 严重度 | 影响 |
|---|---|---|---|
| 1 | **候选侧无事件台账实体** | **BLOCKER** | `event_structure` 维度 85/85 NOT_AVAILABLE |
| 2 | **候选侧无可映射行情序列** | **BLOCKER** | `market_structure` 维度 85/85 NOT_AVAILABLE；无法做 breadth / 相对走势 |
| 3 | **`terminalPhaseOf` 语义断层** | HIGH | 历史终态 12/17 = END → 现口径 80/85 MISMATCH |
| 4 | **候选 `phase_window.end` 全为 null** | HIGH | `temporal_structure` 只能单向 |
| 5 | **`高端装备` 无历史 Cycle** | HIGH | EMBODIED-AI 无同族类比（跨族可用） |
| 6 | **每族样本量 1–2** | HIGH | 族内结构类比不可靠 |
| 7 | **`FIRST_DECLINE` 覆盖 5.9%** | MEDIUM | 衰退段结构无法比较 |
| 8 | **`industry` event_type 未映射 driver** | MEDIUM | driver 维度丢失一个来源 |
| 9 | **`SENTIMENT` 历史侧恒不可派生** | MEDIUM | 5 类 driver 实际只有 4 类可用 |
| 10 | **`industry_index` / `concept_index` 多为空占位** | MEDIUM | 6/56 空；概念指数 4/4 全空 |
| 11 | **`INDUSTRY_EVENT_DRIVEN` / `DATA_RELEASE_DRIVEN` NOT_AVAILABLE** | MEDIUM | 与 Time Observation v0.5 同一缺口 |
| 12 | 历史 `drivers` 字段为自由文本 | LOW | 需从 event_type 反推（粒度粗） |

---

## 14. Feasibility Decision

### Decision Table

| Dimension | Status | Evidence | Main Gap |
|---|---|---|---|
| Historical cycle coverage | **PARTIAL** | 13 Campaign / 13 Cycle / 4 Macro Theme | 每族 1–7 个；POWER/COMM 各 2 个 → 0 个 family 级候选 |
| Lifecycle | **PARTIAL** | stage-aligned 58/85 MATCH；5/5 候选有可用对象 | terminal 口径 80/85 MISMATCH；`FIRST_DECLINE` 5.9% |
| Drivers | **PARTIAL** | 同枚举可比；16/17 历史对象有 driver | 仅 3/85 MATCH；71/85 为弱 PARTIAL；SENTIMENT 恒缺 |
| Evidence sequence | **PARTIAL** | 11/17 有 ≥2 事件、9/17 有 ≥3 | 候选侧无事件实体；两侧词表不同；0/85 三维全 MATCH |
| Event structure | **NOT_AVAILABLE** | 历史有 52 条事件台账 | **候选侧无事件实体** |
| Temporal structure | **PARTIAL** | 历史阶段有精确日期 | **候选只有 1 个起点，只能单向** |
| Market structure | **NOT_AVAILABLE** | 56 series（6 空） | **候选侧无可映射序列**；历史为窗口采样 |
| Cross-family analogy | **PARTIAL** | TIER_1 跨族 20 / 同族 3 | 样本小；driver 多为弱匹配 |

### Overall Status

> ## **`PARTIALLY_FEASIBLE`**

**推导（非主观）**：
- 有 3 个维度达 `PARTIAL` 以上且**机制上可算** → 不是 `INSUFFICIENT_DATA`、也不是 `BLOCKED`；
- 但有 **2 个维度双侧 `NOT_AVAILABLE`**、1 个只能单向，
  且**严格口径下三维同时 MATCH = 0、二维 = 1/5** → 不是 `FEASIBLE`。

---

## 15. Minimum Viable Scope（§十五）

> ## **Option C（Research-only exploration），上限为 Option B**

- **可以做**：`Lifecycle(stage-aligned)` + `Driver` + `Evidence Sequence` **三维结构类比**，
  且结果**确实不同于名称匹配**（§10 已验证）。
- **不可以做**：`Market Structure`、`Event Structure`、双向 `Temporal`。
- **因此**：**只能停留在 Research-only**，**不足以支撑 Product 端「相似度」呈现**
  （Product 侧需要 market context 才能解释「当时市场环境如何」）。

---

## 16. Wave 1C Dependency（§十二）

**Wave 1C 状态：`OPTIONAL / BLOCKER-DEPENDENT` —— 本轮不实施。**

| 缺口 | Wave 1C（高端装备）能否解决 |
|---|---|
| `高端装备` 无历史 Cycle | ✅ 能（唯一直接相关项） |
| 候选侧无事件台账 | ❌ 不能 |
| 候选侧无行情序列 | ❌ 不能 |
| `terminalPhaseOf` 语义断层 | ❌ 不能（属 Product/语义层，非数据） |
| 每族样本量 1–2 | ⚠️ 部分（只增一族，不增已有族的深度） |

→ **Wave 1C 只解决 1 个 HIGH 缺口（#5），不解决 2 个 BLOCKER（#1 / #2）。**
→ **不足以成为 Structural Analogy 的前置条件。**

---

## 17. Recommendation for Phase 8

**建议：先修 2 个 BLOCKER，再谈 Structural Analogy 实现。**

优先级（按对可行性的边际影响）：

1. **BLOCKER #2（候选侧行情序列）** —— 若能建立 2026 候选的可映射行情/指数序列，
   `market_structure` 可从 `NOT_AVAILABLE` 变为可比较 → 直接决定 Product 可行性。
2. **BLOCKER #1（候选侧事件实体）** —— 让候选具备与历史同构的 `events` 台账，
   `event_structure` 维度即可对齐。
3. **HIGH #3（`terminalPhaseOf` 语义）** —— 属**语义/契约**问题：结构类比需要
   「历史对象**在该阶段时**的结构」，而现实现只给终态。**这是 Product 侧的设计问题，不是数据问题。**
4. **HIGH #4（`phase_window.end`）** —— 补候选侧阶段区间。
5. `OPTIONAL`：Wave 1C（高端装备）。

**不建议**：现在进入 Structural Analogy Implementation / Product Integration / UI。

---

## 18. Limitations

- 本轮为 **Feasibility Check**，**未实现** Structural Analogy，**未产出**相似度排名。
- 维度判定规则（`PHASE_ADJ` / `TIER_*` 阈值）由本轮**首次定义**，属 v0.1 工作定义，**非既有标准**。
- 候选侧 `evidence[].source_type` → 历史 `event_type` 的映射（`CAND_EV_TO_EVENT`）为**人工映射**，有损。
- `drivers` 维度的历史侧由 `event_type` 反推，**粒度粗于**候选侧的显式 `drivers[].category`。
- 样本量小（5 候选 × 17 历史对象 = 85 组合），**任何比例数字都不具统计意义**。
- 未做**多重比较校正**（本轮不产出 p 值，故不适用）。
- 未评估 `research_candidates` 与 `campaigns` 混用是否引入偏差。

---

## 19. Reproducibility

- 产物由 `research/scripts/build_structural_analogy_feasibility.py` 生成（**deterministic**：
  无随机、无时间依赖、无网络、无 LLM）。
- 支持 `--check`：重算结果与磁盘产物**逐字节一致**。
- 输入：`exports/timeline_export_v1.json` · `research/current/current_candidates.json`。
- **不写入** DB / schema / export / `src/**`。

---

## 20. 明确回答（任务书要求）

| 问题 | 回答 |
|---|---|
| schema changed | **NO** |
| timeline export contract changed | **NO** |
| 历史数据 changed | **NO** |
| `src/**` / Product changed | **NO** |
| 是否实现 Structural Analogy | **NO**（本轮为 Feasibility Check） |
| 是否进入 Wave 1C | **NO**（标记为 `OPTIONAL / BLOCKER-DEPENDENT`） |
| breaking change | **NO** |

---

*报告结束 · Structural Analogy Feasibility v0.1 · 2026-09-18*
