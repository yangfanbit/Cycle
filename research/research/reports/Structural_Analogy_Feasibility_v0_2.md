# Structural Analogy Data Readiness & Semantic Repair v0.1

> | 项目 | 值 |
> |---|---|
> | 性质 | **Data Readiness / Semantic Repair（不是 Structural Analogy 实现）** |
> | 完成日期 | 2026-09-19 |
> | 起始状态 | `HEAD = origin/main = ded84d7`，ahead/behind `0/0`，工作树 clean（**自行核对**） |
> | 对照基线 | `Structural_Analogy_Feasibility_v0_1`（**保留不覆盖**） |
> | 未修改 | `src/**` · Product IA / UI · schema.sql · frozen export contract · Research Model v1.0 · 历史数据 · Time Observation v0.2–v0.5 全部产物 |

---

## 1. Executive Summary

**目标**：修复 v0.1 暴露的 4 项缺陷（1 语义 + 3 数据），再重新评估 Research feasibility。

### 修复结果

| Blocker | v0.1 | v0.2 | Resolution |
|---|---|---|---|
| **lifecycle semantic break** | BLOCKER | ✅ **RESOLVED** | 新增 `historical_stage_at_comparable_point`（可比观测点口径） |
| **candidate event entity** | BLOCKER | ✅ **RESOLVED** | 从 evidence 派生最小事件实体（36/39 条可派生） |
| **candidate market mapping** | BLOCKER | ⚠️ **PARTIALLY_RESOLVED** | 同产品段序列代理（**非候选自身证券**） |
| **phase_window.end** | HIGH | ❌ **UNRESOLVED** | 证据不足 → 保持 `null`，语义记 `unknown`（**不猜日期**） |

### 维度可用性（85 组合 = 5 候选 × 17 历史对象）

| 维度 | v0.1 | v0.2 |
|---|---|---|
| `lifecycle` | MATCH 58 / **MISMATCH 27** | **MATCH 58 / PARTIAL 24 / MISMATCH 3** |
| `lifecycle_terminal_legacy`（旧口径，保留对照） | MISMATCH 80 / PARTIAL 3 / MATCH 2 | 同（**未变**，证明修复只改语义不改数据） |
| `drivers` | PARTIAL 71 / MATCH 3 / MISMATCH 6 / NA 5 | 同（**未变**，本轮未改 driver taxonomy） |
| `evidence_sequence` | NA 30 / PARTIAL 27 / MISMATCH 22 / MATCH 6 | NA 30 / PARTIAL 23 / MISMATCH 24 / **MATCH 8** |
| **`event_structure`** | **NA 85** | **PARTIAL 74 / MISMATCH 6 / NA 5** |
| `temporal_structure` | NA 40 / PARTIAL 45 | **PARTIAL 85** |
| **`market_structure`** | **NA 85** | **PARTIAL 68 / NA 17** |

### ★ 最重要结论：三项修复**未改变**顶层可用性

| 三关键数字 | v0.1 | v0.2 |
|---|---:|---:|
| 有结构可用历史类比（`STRICT_B`） | **1 / 5** | **1 / 5** |
| 仅有主题/名称级类比 | 4 / 5 | 4 / 5 |
| 无任何可用历史类比 | 0 / 5 | 0 / 5 |

**原因**：修复后**约束瓶颈转移**了 —— v0.1 卡在 lifecycle / event / market，
**v0.2 卡在 `drivers`**（仅 3/85 为 `MATCH`，71/85 为弱 `PARTIAL`）。
→ **`drivers` 是新的单一瓶颈**，且它是**历史侧数据粒度问题**，不是候选侧缺陷。

---

## 2. Repo Baseline

```
git status --short          → 无输出（clean）
git rev-parse HEAD          → ded84d72e33b14206b21052350410319c7c42d3c
git rev-parse origin/main   → ded84d72e33b14206b21052350410319c7c42d3c
git branch --show-current   → main
git diff --stat             → 空      git diff --cached --stat → 空
ahead/behind                → 0  0
```
`git log --oneline -10`：`ded84d7`(HEAD, origin/main) → `fd5914f` → `d3fa89f` → `2c16058` → `707224b` → `052b79b` → `cc4c2d4` → `f446cb8` → `ff8b6eb` → `e85fb42`。
**无 staged / unstaged / untracked 文件。** 与任务书描述相符（**已自行核对**）。

---

## 3. P0-A：Lifecycle Semantic Break 修复

### 问题
`terminalPhaseOf` 对历史对象几乎恒为 `END`（**12/17**，因历史 Campaign 均已结束）。
用它作比较基准 → **80/85 MISMATCH**。**这是比较语义错误，不是历史数据缺失。**

### 修复（research-only 派生层）
新增字段 **`historical_stage_at_comparable_point`**：

```
candidate.attention_state  ──PHASE_TO_STAGE──▶  目标阶段 T
历史 lifecycle[]：
  T ∈ stages            → MATCH    （该阶段有明确锚点日期）
  ∃ 相邻阶段 ∈ stages    → PARTIAL  （阶段次序相邻）
  否则                   → MISMATCH （回落到 terminal_stage，仅作记录）
  无 lifecycle           → UNKNOWN
```

- **`terminalPhaseOf` 保留、语义未改**；旧口径以 `lifecycle_terminal_legacy` **保留作对照**。
- **未改** frozen schema · 历史原始 lifecycle 数据 · Timeline export。仅在 Structural Analogy research layer 生成。

### 效果
`MISMATCH 27 → 3`（剩余 3 条全部为 `RC-2024-SECONDARY` —— 该 Research Candidate 的阶段与候选当前阶段既不相邻也不相同，属**真实数据差异**，非语义错误）。
`lifecycle_terminal_legacy` **完全未变**（80/3/2）→ 证明修复**只改语义、未动数据**。

---

## 4. P0-B：Candidate-side Event Entity

### 问题
候选侧**无事件实体**（只有 `evidence`）→ `event_structure` **85/85 NOT_AVAILABLE**。

### 修复
从 candidate `evidence[]` 派生**最小事件实体**，写入
`structural_analogy_candidate_events_v0_1.json`：

| 字段 | 来源 |
|---|---|
| `event_id` | `CEV-<candidate>-<nn>` |
| `candidate_id` | candidate |
| `date` | `evidence.event_date`（优先）→ `evidence.source_date`（**降级依据**） |
| `date_basis` | `event_date` \| `source_date`（**显式标注依据强度**） |
| `date_confidence` | `high`（event_date）\| `medium`（source_date） |
| `event_type` | `evidence.source_type` → **复用历史 `events.event_type` 枚举** |
| `source_evidence_id` / `source_type` / `description` / `evidence_strength` / `direction` | evidence |

**词表复用（未新建 taxonomy）**：`POLICY→policy` · `INDUSTRY→industry` · `COMPANY→company` ·
`MARKET→market` · `MACRO→macro` · **`CAPITAL→market`**（历史枚举无 `capital`；
与既有 `EVENT_TYPE_TO_DRIVER` 的 market→CAPITAL 方向一致）。

### 覆盖（39 条 evidence）

| 项 | 值 |
|---|---:|
| evidence 总数 | 39 |
| **可派生事件** | **36** |
| ├ `date_basis = event_date`（强） | 28 |
| └ `date_basis = source_date`（弱） | 8 |
| **无任何日期 → 不派生** | **3** |

按候选：BCI **7** · COMPUTE-POWER **9** · EMBODIED-AI **7** · OPTICAL-LINK **7** · OFFSHORE-WIND **6**。
按类型：`policy 12` · `industry 10` · `market 8` · `company 5` · `macro 1`。

**★ 「无证据 ≠ 无事件」语义**：无可追溯日期者**不派生**，并记 `NOT_AVAILABLE`；
**未**出现 `NO_EVENT` / `NO_PATTERN` 表述。`CC-2026-EMBODIED-AI` 的 8 条 evidence
**全部** `event_date = null` → 改用 `source_date`（7 条可派生，1 条无任何日期）。

### 效果
`event_structure`：**NA 85 → PARTIAL 74 / MISMATCH 6 / NA 5**（剩余 5 = EMBODIED-AI 对无事件的历史对象）。

---

## 5. P0-C：Candidate-side Market Mapping

### 问题
候选侧**无可映射行情序列** → `market_structure` **85/85 NOT_AVAILABLE**。

### 修复原则
**不因 candidate 属于某行业就假设 market series 可用** —— 按**产品段**逐项判定，
并显式记录覆盖限制。**未联网抓取任何数据**（保持 offline / deterministic）。

写入 `structural_analogy_candidate_market_map_v0_1.json`：

| candidate | 段 | 代理序列 | 状态 | 覆盖限制 |
|---|---|---|---|---|
| `CC-2026-OPTICAL-LINK` | 光模块/光器件 | INNOLIGHT · EOPTOLINK · TFC · ACCELINK | **PARTIAL** | 同产品段，非候选自身证券；2018–2025 连续 |
| `CC-2026-OFFSHORE-WIND` | 风电整机 | GOLDWIND | **PARTIAL** | **覆盖止于 2022-12-30** |
| `CC-2026-COMPUTE-POWER` | 电网设备 | NARI · PINGGAO · SIEYUAN · TBEA · XUJI | **PARTIAL** | 相关段；「算电协同」本身无序列 |
| `CC-2026-BCI-MEDTECH` | 医药（**非医疗器械**） | HENGRUI · TIGERMED · WUXIAPPTEC · ZHIFEI · YILING · INTCO · PIANZAIHUANG · PHARMA_ETF_512010 | **PARTIAL** | **非同产品段**；个股止于 2022 |
| `CC-2026-EMBODIED-AI` | 具身智能/人形机器人 | — | **NOT_AVAILABLE** | 仓库无机器人序列；`ROBOTAXI` 为空占位 |

### ★ 仍未解决的本质限制
**候选自身 2026 行情不可得**（无证券记录、不联网）→ 市场比较**仍为单向**（历史侧有、候选侧无）。
→ 因此状态最高只能到 **`PARTIAL`**，**不能**判 `MATCH`。

### 效果
`market_structure`：**NA 85 → PARTIAL 68 / NA 17**（17 = EMBODIED-AI 的 17 个组合）。

---

## 6. P1：`phase_window.end`

**决定：保持 `null`，语义记 `unknown`。不猜日期。**

理由：仓库内**无**候选当前阶段结束的证据（无阶段终止事件、无 next-phase 证据）。
新增显式语义字段 `phase_window_end_semantics ∈ {declared, derived, unknown}`，
本轮 5 个候选**全部为 `unknown`**。

**影响**：`temporal_structure` 只能单向（候选 `phase_window.start` + 已历时 vs 历史阶段锚点）。
**已部分缓解**：v0.2 引入 `phase_elapsed_days_at_snapshot`（候选在当前阶段已停留天数）：
BCI 77 · COMPUTE-POWER 130 · EMBODIED-AI 199 · OPTICAL-LINK 106 · OFFSHORE-WIND 5。
→ `temporal_structure` 从 `NA 40 / PARTIAL 45` 变为 **`PARTIAL 85`**（单向但**全覆盖**）。

---

## 7. 重建后的 Comparison Matrix

85 行见 `structural_analogy_feasibility_candidates_v0_2.csv`。
**Tier 分布**：`TIER_1` **21** · `TIER_2` 34 · `TIER_3` 1 · `TIER_4` 29。
**TIER_1 同族/跨族**：**3 / 18**。

**敏感性分析（必须同时披露）**：

| 口径 | 组合数 | 覆盖候选 |
|---|---:|---:|
| `STRICT_A`（lifecycle+drivers+seq+event 全 MATCH） | **0** | **0 / 5** |
| `STRICT_B`（lifecycle + drivers MATCH） | **3** | **1 / 5** |
| `TIER_1`（stage + driver 强匹配 + seq + event） | 21 | 5 / 5 |

> `drivers = PARTIAL` 仍占 **71/85** → 宽口径结果主要由弱 driver 匹配贡献。

---

## 8. 五个 Current Candidates（仅记录支持/缺口，**无排名/评分/最佳匹配**）

| candidate | lifecycle | event | market | temporal | 结构支持 | 主要缺口 |
|---|---|---|---|---|---|---|
| `CC-2026-BCI-MEDTECH` | MATCH | 7 事件（4 类） | PARTIAL（**非同段**） | PARTIAL | **唯一达 STRICT_B** | 同族 `C-2019-PHARMA-INNOV` 未达 TIER_1；driver 仅弱匹配 |
| `CC-2026-COMPUTE-POWER` | MATCH | 9 事件（3 类） | PARTIAL（相关段） | PARTIAL | TIER_1 覆盖 5 个历史对象 | 无可比段的精确代理；`phase_elapsed` 最长（130 天）无对照 |
| `CC-2026-EMBODIED-AI` | MATCH | **7 事件（全 `source_date` 降级）** | **NOT_AVAILABLE** | PARTIAL | TIER_1 全为跨族 | ① 高端装备族历史侧不存在 ② 无行情序列 ③ `event_date` 全缺 |
| `CC-2026-OPTICAL-LINK` | MATCH | 7 事件（4 类） | PARTIAL（**同产品段**） | PARTIAL | TIER_1 含**同族** `C-2023-COMM-OPTICAL` | 同族另一 Cycle `C-2019-COMM-5G` 未达 TIER_1 |
| `CC-2026-OFFSHORE-WIND` | MATCH | 6 事件（5 类，**类型最全**） | PARTIAL（覆盖止 2022） | PARTIAL | TIER_1 含同族 `C-2022-POWER-GRID` | 行情代理无法覆盖 2023–2025 |

**禁止项（本轮未产出）**：best analogue · ranking · score · winner · prediction。

---

## 9. Name vs Structural 对照实验（§十三）

| | v0.1 | v0.2 |
|---|---:|---:|
| Method A（名称/主题）覆盖 | 9 | **9** |
| Method B（结构 TIER_1）覆盖 | 6 | **6** |
| 交集 | 5 | **5** |
| **仅 A**（名称相似但结构未达 TIER_1） | 4 | **4** |
| **仅 B**（名称不同但结构达 TIER_1） | 1 | **1** |

- **仅 A**：`C-2019-COMM-5G` · `C-2019-PHARMA-INNOV` · `C-2020-POWER-NE` · `C-2024-ROBOTAXI`
- **仅 B**：`C-2025-ROBOTAXI`
- Method B 命中按族：**汽车 4** · 信息通信 1 · 电力设备 1（候选分属 4 个不同族）

**结论**：修复 lifecycle / event / market 后，**结构匹配与名称匹配的差异仍然存在**（仅 A 4 / 仅 B 1）。
**不声称 Method B 更准确** —— 只确认该差异未被修复动作抹平。

---

## 10. Blocker Resolution Matrix（§十五）

| Blocker | v0.1 | v0.2 | Resolution | Remaining impact |
|---|---|---|---|---|
| **lifecycle semantic break** | BLOCKER | ✅ **RESOLVED** | 新增 `historical_stage_at_comparable_point` | 历史不含候选阶段时仍 MISMATCH（真实数据差异，3/85） |
| **candidate event entity** | BLOCKER | ✅ **RESOLVED** | 从 evidence 派生最小事件实体 | 3/39 evidence 无任何日期 → 不派生；EMBODIED-AI 的 7 条为 `source_date` 降级依据 |
| **candidate market mapping** | BLOCKER | ⚠️ **PARTIALLY_RESOLVED** | 同产品段序列代理 | **候选侧 2026 行情不可得** → 市场比较**单向**；`GOLDWIND` 覆盖止 2022；BCI **非同段** |
| **phase_window.end** | HIGH | ❌ **UNRESOLVED** | 语义记 `unknown`，**不猜** | temporal 仍单向（已用 `phase_elapsed_days` 部分缓解） |

### 无法解决项的性质
- `phase_window.end`：**数据问题**（无阶段终止证据）→ 需**未来证据**，非本轮可解。
- 市场单向：**数据问题**（候选自身无证券/行情）→ 需 2026 行情数据源。
- `drivers` 弱匹配（71/85 PARTIAL）：**历史侧数据粒度问题** ——
  历史 `drivers` 字段是自由文本，只能由 `event_type` 反推，且 `industry` event_type **未映射** driver。

---

## 11. Wave 1C 判定（§十六）

> **`Wave 1C = NOT REQUIRED`**（对 Structural Analogy 而言）

**推导**：修复后**不再存在**必须依靠新增历史 Theme Family 才能解决的 BLOCKER。
`EMBODIED-AI` 无同族历史的问题，**已由跨族结构类比覆盖** ——
其 TIER_1 命中 **6 个对象（全部跨族）**，证明跨族类比**已可支撑它**。
→ **不建立 `TH-HIGH-END`。**

（`高端装备` 族缺失仍是 Coverage Audit 的已知项，但**不构成 Structural Analogy 的 blocker**。）

---

## 12. Feasibility Decision

| Dimension | v0.1 | v0.2 |
|---|---|---|
| Historical cycle coverage | PARTIAL | PARTIAL（未变） |
| Lifecycle | PARTIAL | **PARTIAL（MISMATCH 27→3）** |
| Drivers | PARTIAL | PARTIAL（**未变 —— 新瓶颈**） |
| Evidence sequence | PARTIAL | PARTIAL（MATCH 6→8） |
| **Event structure** | **NOT_AVAILABLE** | **PARTIAL** |
| Temporal structure | PARTIAL（NA 40） | **PARTIAL（全覆盖）** |
| **Market structure** | **NOT_AVAILABLE** | **PARTIAL（单向）** |
| Cross-family analogy | PARTIAL | **PARTIAL（TIER_1 跨族 18 / 同族 3）** |

### Overall Status

> ## **`PARTIALLY_FEASIBLE`（与 v0.1 同级，但**瓶颈已转移**）**

- **Research feasibility**：**改善** —— 4 项缺陷中 2 项 RESOLVED、1 项 PARTIALLY_RESOLVED；
  维度层 2 个 `NOT_AVAILABLE` 全部消除。
- **Product readiness**：**仍为 NO** —— 三关键数字**未变**（1/4/0），
  且市场比较**单向**、`drivers` 弱匹配为主。

> ★ **Research feasibility ≠ Product readiness。本轮只回答前者。**

---

## 13. Minimum Viable Scope

> **Option C（Research-only exploration），上限 Option B。**

可做：`Lifecycle(可比观测点)` + `Driver` + `Evidence Sequence` + `Event Structure` **四维**；
不可做：候选侧 2026 market state · 双向 temporal · 任何 similarity score / ranking。

---

## 14. Limitations

- 维度判定阈值（`STAGE_NEIGHBOURS` / `TIER_*`）为本轮 v0.1/v0.2 **工作定义**，非既有标准。
- `CAPITAL → market` 映射为**人工判定**，有损（历史枚举无 `capital`）。
- `source_date` 派生的 8 条事件，其日期是**来源发布日而非事件发生日**（已用 `date_basis` 显式标注）。
- 行情代理为**段级**，非候选自身证券；`GOLDWIND` 覆盖止 2022、BCI 代理**非同段**。
- 样本量小（85 组合），**任何比例数字都不具统计意义**。
- 未做多重比较校正（本轮不产出 p 值）。

---

## 15. Reproducibility

- 生成器：`research/scripts/build_structural_analogy_readiness_v0_2.py`（**deterministic**：
  无随机 / 无时间依赖 / 无网络 / 无 LLM）。
- `--check`：**三份产物**与重算结果**逐字节一致**；已执行 `run → check → run → check`。
- 输入：`exports/timeline_export_v1.json` · `research/current/current_candidates.json` ·
  `research/database/cycle_research.db`（只读）。
- **v0.1 产物保留不覆盖**；**未写** DB / schema / export / `src/**`。

---

## 16. 明确回答

| 问题 | 回答 |
|---|---|
| schema changed | **NO** |
| export contract changed | **NO** |
| 历史数据 changed | **NO** |
| Time Observation v0.2–v0.5 changed | **NO**（逐字节保留） |
| `src/**` / Product changed | **NO** |
| 是否实现 Structural Analogy | **NO** |
| 是否进入 Wave 1C | **NO**（判定为 `NOT REQUIRED`） |
| breaking change | **NO** |

---

*报告结束 · Structural Analogy Data Readiness v0.1 · 2026-09-19*
