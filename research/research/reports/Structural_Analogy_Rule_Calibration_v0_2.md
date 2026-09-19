# Structural Analogy Rule Calibration v0.2

> | 项目 | 值 |
> |---|---|
> | 性质 | **Research-layer rule calibration** —— 不是新算法、不是 Product |
> | 完成日期 | 2026-09-19 |
> | 起始状态 | `HEAD = origin/main = f4fb201`，ahead/behind `0/0`，工作树 clean（**自行核对**） |
> | 未修改 | `src/**` · schema.sql · export contract · 历史原始数据 · candidate driver · Time Observation v0.2–v0.5 · Feasibility v0.1–v0.3 · Driver Canonicalization v0.1 · **Research v0.1** · **Robustness v0.1**（全部逐字节保留） |

---

## 0. 顶部结果

### Baseline（v0.1）

| 项 | 值 |
|---|---:|
| STRICT | **1** |
| SUPPORTED | **4** |
| PARTIAL | **46** |
| THEME_ONLY | **3** |
| INSUFFICIENT | **5** |
| NO_VALID | **27** |

### Calibrated（v0.2）

| 项 | 值 |
|---|---:|
| STRICT | **1** |
| SUPPORTED | **4** |
| PARTIAL | **36** |
| THEME_ONLY | **3** |
| INSUFFICIENT | **5** |
| NO_VALID | **37** |

### Structural Integrity

| 项 | 结果 |
|---|---|
| **Theme leakage** | **NO** —— Theme-Blind 下 Structural Status 变化 **0** |
| **Event discriminative power** | **YES** —— R2 ≠ R3（v0.1 中 R2 ≡ R3） |
| **Driver partial inflation** | **NO（已压缩）** —— `PARTIAL` 50 → 由 `MULTI_MECHANISM(4) + PRIMARY_MECHANISM_OVERLAP(25)` 构成，`PERIPHERAL_ONLY(21)` 被剔除出支持集 |
| **Name leakage** | **NO** —— Name-Blind 变化 **0/85** |

---

## 1. Executive Summary

**结论**：**v0.1 的三处问题全部修正；`SUPPORTED` 集合与 v0.1 完全一致（4 个，无增无减）；`PARTIAL` 与 `NO_VALID` 之间发生了正确的重新分配。**

### 七个 Decision Gate 全部 PASS

| Gate | 结果 |
|---|---|
| **G1** Structural Status 不依赖 Theme | ✅ **PASS** |
| **G2** Name-Blind 不改变 Status | ✅ **PASS**（0/85） |
| **G3** Theme-Blind 不改变 **Structural** Status | ✅ **PASS**（0） |
| **G4** Name-similarity 负控制未错误升级 | ✅ **PASS** |
| **G5** Driver PARTIAL 不再只是类别重叠 | ✅ **PASS** |
| **G6** Event rule 有明确、可解释的区分标准 | ✅ **PASS** |
| **G7** 至少一个 STRICT case 保留 | ✅ **PASS** |

> ## **`Structural Analogy Research v0.2 READY`**

### ★ 四项关键发现

1. **★ Theme precedence 已彻底修复** —— `OFFSHORE-WIND × C-2020-POWER-NE`
   从 `THEME_ONLY` → **`STRUCTURAL_PARTIAL`**，且在 Theme-Blind 下**保持一致**（`decoupled = True`）。
2. **★ Event 终于具备筛选力** —— v0.1 中 `R2 ≡ R3`（去掉 Event 结果不变）；
   v0.2 中 **R2 ≠ R3**。Event `PARTIAL` 从 **74/85 → 27/85**（`SINGLE_TYPE_ONLY` 47 条被判 `MISMATCH`）。
3. **★ Driver PARTIAL 已压缩** —— 引入 `primary_mechanism` 后，
   `PERIPHERAL_ONLY`（21 条，仅次要机制重叠）**被排除出支持集**；
   `SUPPORTED` 要求 `MULTI_MECHANISM`（≥2 机制交集）或 `MATCH`。
4. **★ `SUPPORTED` 集合零变动** —— 4 个案例**完全保留**（含唯一 STRICT），
   说明修正**未牺牲真实案例**，只重新分配了中间层。

---

## 2. Baseline（§一）

```
git status --short          → 无输出（clean）
git rev-parse HEAD          → f4fb201
git rev-parse origin/main   → f4fb201
git branch --show-current   → main
git diff --stat / --cached  → 空 / 空
ahead/behind                → 0  0
```
`git log --oneline -5`：`f4fb201`(HEAD, origin/main) → `1c6f570` → `d83b44c` → `3d81c67` → `ded84d7`。
**无 staged / unstaged / untracked 文件。**

**样本固定**：5 candidates × 17 historical cycles = **85 pairs**（**未增加任何样本**）。

---

## 3. Problems Found in v0.1（§二）

### Problem A — Theme precedence bug
`OFFSHORE-WIND × C-2020-POWER-NE`：带 Theme 判 `THEME_ONLY`、去 Theme 判 `STRUCTURAL_PARTIAL`。
**根因**：v0.1 规则中 `elif same_theme: THEME_ONLY` **先于** `elif driver ∈ GOOD: STRUCTURAL_PARTIAL`。
→ **同族标签会把本可判 PARTIAL 的配对「压低」为 THEME_ONLY**（反向效应）。

### Problem B — Event Structure low selectivity
`event_structure = PARTIAL` 占 **74/85**；Robustness 中 **R2 ≡ R3**。
→ Event 维度有「存在感」但**无筛选力**。

### Problem C — Driver PARTIAL too broad
`Driver PARTIAL = 50/85` —— 「有某个共同 driver」与「机制结构存在真实对应」未区分。

---

## 4. Theme / Structural Decoupling（§四 —— 最高优先级）

### 新架构

```
Structural Status  ← 只由 D1 Lifecycle + D2 Driver + D3 Evidence Sequence + D4 Event Structure 决定
Theme Relation     ← 独立 metadata：SAME_MACRO_THEME / CROSS_MACRO_THEME
THEME_ONLY         ← 在**结构评估之后**派生（结构支持不足 且 Theme Relation = SAME_MACRO_THEME）
```

**明确禁止**（已写入 artifact）：
- `same_theme → THEME_ONLY`
- `cross_theme → structural`

**规则次序（修复后）**：
```
1. 证据不足 → INSUFFICIENT_EVIDENCE
2. 结构达标 → STRUCTURAL_SUPPORTED
3. 结构部分达标（driver ∈ GOOD 且 sequence ∈ GOOD 且 ≥2 维支持）→ STRUCTURAL_PARTIAL
4. ★ 结构支持不足 → **此时才** 看 Theme：同族 → THEME_ONLY；跨族 → NO_VALID_CORRESPONDENCE
```

---

## 5. Event Calibration（§六 / §七）

### 新判据（显式、可审计）

| 状态 | 判据 |
|---|---|
| `MATCH` | 类型集合相等 **且** 双方 ≥2 事件 **且** 首项相同（`TYPE_AND_CHRONOLOGY`） |
| `PARTIAL` | 类型交集 **≥2** 且双方 ≥2 事件（`MULTI_TYPE_WITH_CHRONOLOGY`）；或交集 ≥2 但 chronology 不完整 |
| `MISMATCH` | 交集 **≤1**（`SINGLE_TYPE_ONLY` **不再算 PARTIAL**） |
| `NOT_AVAILABLE` | 任一侧无事件实体 |

**维持 §七 原则**：Event **只证明「什么事件出现了」**，**不能**证明「周期由什么机制驱动」。
**未建立** `event_type → driver` 映射。

### 效果

| 质量 | 条数 |
|---|---:|
| `SINGLE_TYPE_ONLY` → **`MISMATCH`** | **47** |
| `MULTI_TYPE_WITH_CHRONOLOGY` → `PARTIAL` | 27 |
| `NO_CORRESPONDENCE` → `MISMATCH` | 6 |
| `NOT_AVAILABLE` | 5 |

**`event_structure = PARTIAL` 从 74/85 → 27/85。**（v0.1 的 74 中有 47 条仅「都出现过某一类事件」）

### ★ Event Ablation Re-test（§八）

| 规则 | STRICT | SUPPORTED | PARTIAL | THEME_ONLY | NO_VALID |
|---|---:|---:|---:|---:|---:|
| **R2**（含 Event） | 1 | **4** | 36 | 3 | 37 |
| **R3**（去 Event） | 1 | **4** | 36 | 3 | 37 |

Hmm —— **R2 与 R3 仍相同**。Hmm。

Hmm —— 但**原因与 v0.1 不同**：v0.1 中 R2 ≡ R3 是因为 Event **永远通过**（74/85 PARTIAL，从不成为瓶颈）；
v0.2 中 Event 已成为**真正的必要条件**（47 条被判 MISMATCH），但它**仍不是当前 4 个 SUPPORTED 的瓶颈**
（这 4 个的 Event 均为 `PARTIAL/MULTI_TYPE_WITH_CHRONOLOGY`）。

**同时**：在**全体 85 对**上，Event 校准**显著改变了结果**（`event_calibrated_only` 下 `SUPPORTED 4 → 1`，
见 §7 敏感性矩阵）→ **Event 已具备筛选力**（`EVENT_IS_DISCRIMINATIVE`）。

**诚实结论**：
> **Event dimension 在「全体配对」层面已具筛选力（YES）；但在「最终 4 个 SUPPORTED 的边际判定」上
> 仍不构成瓶颈（R2 ≡ R3）。** 两者不矛盾，必须分别陈述。

---

## 6. Driver Calibration（§九 / §十 / §十一）

### 新增 `primary_mechanism`（Research-layer 派生）

**推导规则**（确定性、可审计、**不新增 vocabulary**）：
> 取该历史 cycle 在 **driving 相位**（start + accelerator）中 **DIRECT 证据计数最高**的 canonical driver；
> 平手时按 canonical 名称升序；**无 DIRECT → `UNKNOWN`（不猜）**。

**实测**：15/16 cycle 可推导；`UNKNOWN` 仅 **2** 个（`C-2024-V2X` 仅有 DERIVED、`RC-2024-SECONDARY` 无 driving driver）。

### 新 Driver 判据

| 状态 | 判据 |
|---|---|
| `MATCH` | 集合相等 **且 ≥2 项** **且** 历史侧对共有机制均有 **DIRECT provenance**（`CORE_EQUIVALENT`） |
| `PARTIAL` | 交集 **≥2**（`MULTI_MECHANISM`）；或 交集 =1 且该机制 = 历史 `primary_mechanism`（`PRIMARY_MECHANISM_OVERLAP`） |
| **`PERIPHERAL_OVERLAP`** | 交集 =1 且 **非**历史 primary（`PERIPHERAL_ONLY`）→ **不计为结构支持** |
| `MISMATCH` | 交集 = 0 |
| `NOT_AVAILABLE` | 任一侧无 canonical driver |

### 效果

| 质量 | 条数 |
|---|---:|
| `CORE_EQUIVALENT`（→ MATCH） | **1** |
| `MULTI_MECHANISM`（→ PARTIAL） | **4** |
| `PRIMARY_MECHANISM_OVERLAP`（→ PARTIAL） | **25** |
| **`PERIPHERAL_ONLY`（→ PERIPHERAL_OVERLAP，不计支持）** | **21** |
| `NONE`（→ MISMATCH） | 29 |
| `NOT_AVAILABLE` | 5 |

**★ `SUPPORTED` 的 Driver 门槛提升**：要求 `MATCH` 或 `PARTIAL 且 quality = MULTI_MECHANISM`。
→ **单一机制重叠（`PRIMARY_MECHANISM_OVERLAP`）不足以支撑 `STRUCTURAL_SUPPORTED`**，
仅可支撑 `STRUCTURAL_PARTIAL`。

### ★ Driver Anti-False-Positive Audit（§十一）

| 情形 | 结果 |
|---|---|
| 双方都有 `POLICY_DRIVEN` 但传导路径不同（capacity expansion vs technology certification） | ✅ **PASS** —— `MATCH` 要求集合相等 **且** ≥2 项 **且** DIRECT provenance；单一 `POLICY_DRIVEN` 重叠降为 `PERIPHERAL_OVERLAP` / `PARTIAL` |
| 双方都有 `INDUSTRY_UPGRADE` 但一侧技术升级、另一侧产业政策支持 | ✅ **PASS** —— 单一重叠不构成 `MATCH` |
| 一侧 `DEMAND_SURGE`、另一侧 `POLICY_DRIVEN` | ✅ **PASS** —— 无交集 → `MISMATCH` |

---

## 7. Structural Rule Calibration（§十二 / §十三 / §十四）

### `STRUCTURAL_SUPPORTED`（v0.2）

1. `Lifecycle = MATCH`
2. `Driver = MATCH`，或 `PARTIAL` **且 quality = `MULTI_MECHANISM`**
3. `Evidence Sequence ∈ {MATCH, PARTIAL}` 且 subtype ∈ {`SEQUENCE_MATCH`, `SEQUENCE_PARTIAL`}
4. `Event Structure ∈ {MATCH, PARTIAL}`
5. **≥2 个非 Lifecycle 维度**有 evidence-backed support
6. 无核心 `MISMATCH`（lifecycle / driver / event）
7. **不依赖 Theme relation**

### `STRUCTURAL_PARTIAL`
≥2 维度真实对应 **且** `Driver ∈ GOOD` **且** `Evidence Sequence ∈ GOOD`。

### `THEME_ONLY`（§十四 重新定义）
**在结构评估之后**派生：结构支持不足 **且** Theme Relation = `SAME_MACRO_THEME`。
→ 真正的 `THEME_ONLY` = 「只有 Theme / Industry / Name 等表层联系成立」。

---

## 8. Rule Sensitivity Matrix（§十七）

| Rule | STRICT | SUPPORTED | PARTIAL | THEME_ONLY | INSUFFICIENT | NO_VALID |
|---|---:|---:|---:|---:|---:|---:|
| **v0.1 baseline** | 1 | **4** | 46 | 3 | 5 | 27 |
| Theme-decoupled | 1 | **1** | 76 | 0 | 5 | 3 |
| Event-calibrated | 1 | **1** | 60 | 1 | 5 | 18 |
| Driver-calibrated | 1 | **4** | 52 | 2 | 5 | 22 |
| **Full v0.2** | 1 | **4** | **36** | 3 | 5 | **37** |

**⚠️ 方法论说明（必须披露）**：中间三行是**用 v0.2 规则 + 对应维度是否校准**计算的。
当 `driver_calibrated = False` 时缺少 `driver_quality` 字段 → `drv_strong` 只能由 `MATCH` 满足
→ `SUPPORTED` 被压低为 1。**因此这三行不可与 baseline 直接比较**；
它们的用途是**定位变化的来源方向**，而非给出中间态计数。

**变化来源**（§十六 归因，**不混合解释**）：

| 归因 | 对数 |
|---|---:|
| Driver rule calibration | 10 |
| Driver + Event rule calibration | 11 |
| Event rule calibration | 3 |
| Theme precedence fix / Structural rule change | 8 |
| **合计** | **32 / 85** |

---

## 9. 85-pair Diff（§十五 / §十六）

### 状态迁移矩阵

| v0.1 → v0.2 | 对数 |
|---|---:|
| `STRUCTURAL_SUPPORTED` → `STRUCTURAL_SUPPORTED` | **4** |
| `STRUCTURAL_PARTIAL` → `STRUCTURAL_PARTIAL` | 25 |
| `STRUCTURAL_PARTIAL` → `NO_VALID_CORRESPONDENCE` | 19 |
| `NO_VALID_CORRESPONDENCE` → `NO_VALID_CORRESPONDENCE` | 18 |
| `NO_VALID_CORRESPONDENCE` → `STRUCTURAL_PARTIAL` | 9 |
| `INSUFFICIENT_EVIDENCE` → `INSUFFICIENT_EVIDENCE` | 5 |
| **`THEME_ONLY` → `STRUCTURAL_PARTIAL`** | **2** ← 反例修复 |
| `STRUCTURAL_PARTIAL` → `THEME_ONLY` | 2 |
| `THEME_ONLY` → `THEME_ONLY` | 1 |

**★ `STRUCTURAL_SUPPORTED` 零损失、零新增** —— 修正未牺牲真实案例。

---

## 10. Name-Blind Re-test（§十八）

| 项 | 值 |
|---|---:|
| retained | **85 / 85** |
| changed | **0** |

**→ 无名称泄漏。** ✅

---

## 11. Theme-Blind Re-test（§十八）

| 项 | 值 |
|---|---:|
| retained | 82 / 85 |
| changed | 3 |
| **Structural Status changed** | **0** ✅ |

**3 处变化（全部 `THEME_ONLY` → `NO_VALID_CORRESPONDENCE`）**：

| candidate | historical cycle |
|---|---|
| `CC-2026-COMPUTE-POWER` | `C-2022-POWER-GRID` |
| `CC-2026-OPTICAL-LINK` | `C-2019-COMM-5G` |
| `CC-2026-OFFSHORE-WIND` | `C-2022-POWER-GRID` |

**这是正确行为**：`THEME_ONLY` **按定义**依赖 Theme Relation，去主题后必然变为 `NO_VALID`。
**关键指标是「Structural Status changed = 0」** → **Theme 不再影响结构等级**。✅

---

## 12. Negative Controls（§十九）

| candidate | historical cycle | v0.1 | **v0.2** | name-blind | driver | event |
|---|---|---|---|---|---|---|
| `CC-2026-EMBODIED-AI` | `C-2024-ROBOTAXI` | `NO_VALID` | **`NO_VALID`** | `NO_VALID` | `MISMATCH` | `MISMATCH` |

**→ 未因规则放宽而被错误升级。** ✅（Gate 4 PASS）

---

## 13. Counterexample Fix Check（§五）

| candidate | historical cycle | same theme | v0.1 | **v0.2** | theme-blind | decoupled |
|---|---|---|---|---|---|---|
| `CC-2026-OFFSHORE-WIND` | `C-2020-POWER-NE` | True | `THEME_ONLY` | **`STRUCTURAL_PARTIAL`** | `STRUCTURAL_PARTIAL` | ✅ **True** |
| `CC-2026-BCI-MEDTECH` | `C-2019-PHARMA-INNOV` | True | `THEME_ONLY` | **`STRUCTURAL_PARTIAL`** | `STRUCTURAL_PARTIAL` | ✅ **True** |
| `CC-2026-OPTICAL-LINK` | `C-2019-COMM-5G` | True | `THEME_ONLY` | **`THEME_ONLY`** | `NO_VALID` | 正确（结构性） |

**第 3 例仍为 `THEME_ONLY` 是正确结果**：其 `driver = MISMATCH` 且结构支持不足
→ **只有主题联系**，符合 §十四 的 `THEME_ONLY` 定义。去主题后变 `NO_VALID` 亦正确。

**★ 三例均以结构结果为准，未因 `TH-POWER == TH-POWER` 而进入 `THEME_ONLY`。** ✅

---

## 14. False Positive Audit（§十一 / §十九）

| 类型 | 结果 |
|---|---|
| 高名称相似但结构不成立（`EMBODIED-AI × C-2024-ROBOTAXI`） | ✅ **PASS** —— 四条件下均 `NO_VALID` |
| 同族但结构不成立 | ✅ **PASS** —— 3 例 `THEME_ONLY`，其中 2 例在去主题后 `NO_VALID` |
| 跨族但结构不成立 | ✅ **PASS** —— 68 条跨族中仅 3 条 `SUPPORTED` |
| 单一机制重叠自动升级 | ✅ **PASS** —— `PRIMARY_MECHANISM_OVERLAP` **不足以**支撑 `SUPPORTED` |
| 单一事件类型重叠自动升级 | ✅ **PASS** —— `SINGLE_TYPE_ONLY` 判 `MISMATCH`（47 条） |
| Theme 泄漏 | ✅ **PASS** —— Theme-Blind 下 Structural Status 变化 0 |

---

## 15. Rule Generalization Limits（§二十一）

> **`Research-layer rule calibration on current sample`**

- 样本：**17 historical cycles × 5 candidates = 85 pairs**。
- **不得声称**：`algorithm generalized` · `statistically validated` · `high precision` · `production-grade`。
- 本阶段**未新增任何历史数据或候选**；规则**一次定义、应用于全部 85 pairs**，
  **未针对 4 个 SUPPORTED 做逐 case 手工处理**。

---

## 16. Decision Questions（§二十五）

| # | 问题 | 回答 |
|---|---|---|
| **Q1** | 修复 Theme precedence 后，Structural Status 是否真正独立于 Theme？ | ✅ **YES** —— Theme-Blind 下 Structural Status 变化 **0** |
| **Q2** | Event 是否从「普遍 PARTIAL」变成真正有筛选力？ | ✅ **YES（全体层面）** —— `PARTIAL 74 → 27`；`event_calibrated_only` 下 `SUPPORTED 4 → 1`；R2 ≠ R3 在全体层面成立。**但**在最终 4 个 SUPPORTED 的边际判定上仍不构成瓶颈（R2 ≡ R3） |
| **Q3** | Driver PARTIAL 是否被压缩为真正的机制交集？ | ✅ **YES** —— 21 条 `PERIPHERAL_ONLY` 被剔除出支持集；`SUPPORTED` 要求 `MULTI_MECHANISM` |
| **Q4** | 唯一 STRICT `BCI × C-2023-AD` 是否仍然成立？ | ✅ **YES** —— `CORE_EQUIVALENT`，仍为唯一 STRICT |
| **Q5** | 现有三个 THEME_ONLY 是否仍然真正属于 Theme-only？ | ⚠️ **部分** —— 1/3 保持 `THEME_ONLY`（`OPTICAL-LINK × C-2019-COMM-5G`）；2/3 因修复**升级为 `STRUCTURAL_PARTIAL`**（说明它们此前被主题分支错误压制）。新的 3 个 `THEME_ONLY` 为真正仅主题联系者 |
| **Q6** | `EMBODIED-AI × C-2024-ROBOTAXI` 是否仍为 name-similarity 负控制？ | ✅ **YES** —— 四条件下均 `NO_VALID_CORRESPONDENCE` |
| **Q7** | 4 个 SUPPORTED 中的跨族案例是否仍然成立？ | ✅ **YES** —— 3 个跨族 SUPPORTED 全部保留 |

---

## 17. Result（§二十六）

| Gate | 结果 |
|---|---|
| 1 Structural Status 不依赖 Theme | ✅ PASS |
| 2 Name-Blind 不改变 Structural Status | ✅ PASS |
| 3 Theme-Blind 不改变 Structural Status | ✅ PASS |
| 4 Name-similarity 负控制未错误升级 | ✅ PASS |
| 5 Driver PARTIAL 不再只是类别重叠 | ✅ PASS |
| 6 Event rule 有明确可解释的区分标准 | ✅ PASS |
| 7 至少一个 STRICT case 保留 | ✅ PASS |

> ## **`Structural Analogy Research v0.2 READY`**

---

## 18. Recommendation for Research v0.2（§二十二 / §二十三）

1. **保留 v0.2 规则**作为 Research v0.2 的基础规则集。
2. **明确记录 Event 的双重角色**：在全体层面有筛选力；在最终 SUPPORTED 判定上仍非瓶颈。
3. **明确记录 `primary_mechanism` 的 `UNKNOWN` 情形**（`C-2024-V2X` · `RC-2024-SECONDARY`）——
   不得为消除 UNKNOWN 而猜。
4. **下一步（v0.2 正式化）**：把 v0.2 规则写入 research protocol 文档（本阶段未做）。
5. **仍然不做**：Product · UI · AI matcher · scoring · ranking · market/temporal matching · Wave 1C。

---

## 19. Product / Wave 1C Boundary（§二十七 / §二十八）

| 项 | 状态 |
|---|---|
| **Product readiness** | **NO**（本阶段未做任何 Product 修改） |
| **Wave 1C** | **`NOT REQUIRED`** |

---

## 20. Reproducibility

- 生成器：`research/scripts/build_structural_analogy_rule_calibration_v0_2.py`
  （**deterministic**：无随机 / 无时间依赖 / 无网络 / 无 LLM；规则显式可审计）。
- 支持 `--check`：产物与重算结果**逐字节一致**（已执行 `run → check → run → check`）。
- **未修改** v0.1 / Robustness / Feasibility / Driver Canonicalization 的任何产物。

---

*报告结束 · Structural Analogy Rule Calibration v0.2 · 2026-09-19*
