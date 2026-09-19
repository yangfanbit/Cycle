# Structural Analogy Robustness Audit v0.1

> | 项目 | 值 |
> |---|---|
> | 性质 | **Research-only Robustness Audit** —— 不是 Product / 不是新算法 |
> | 完成日期 | 2026-09-19 |
> | 起始状态 | `HEAD = origin/main = 1c6f570`，ahead/behind `0/0`，工作树 clean（**自行核对**） |
> | 审计对象 | `Structural Analogy Research v0.1`（**未修改，逐字节保留**） |
> | 未修改 | `src/**` · schema.sql · export contract · 历史原始数据 · candidate 数据 · Time Observation v0.2–v0.5 · Feasibility v0.1–v0.3 · Driver Canonicalization v0.1 · Research v0.1 |

**核心问题**：当前 Structural Correspondence 是**真实的结构关系**，还是**部分规则叠加造成的假阳性**？

---

## 0. 顶部结果

### Baseline（冻结自 v0.1）

| 项 | 值 |
|---|---:|
| `STRICT_STRUCTURAL_SUPPORTED` | **1** |
| `STRUCTURAL_SUPPORTED` | **4** |
| `STRUCTURAL_PARTIAL` | **46** |
| `THEME_ONLY` | **3** |
| `NO_VALID_CORRESPONDENCE` | **27** |
| （`INSUFFICIENT_EVIDENCE`） | 5 |

### Robustness

| 状态 | 数量 |
|---|---:|
| **`ROBUST`** | **4** |
| `SENSITIVE` | 0 |
| `EVIDENCE_FRAGILE` | 0 |
| `UNSTABLE` | 0 |

### Name Blind / Theme Blind

| 测试 | retained | changed |
|---|---:|---:|
| **Name-Blind** | **85 / 85** | **0** |
| **Theme-Blind** | **82 / 85** | **3** |

---

## 1. Executive Summary

**结论**：**当前 4 个 `STRUCTURAL_SUPPORTED` 是真实的结构关系，不是规则叠加造成的假阳性。**

**四项决定 Gate 全部 PASS** → **`ROBUST ENOUGH FOR RESEARCH v0.2`**

| Gate | 判据 | 结果 |
|---|---|---|
| **Gate 1** | 至少 1 个 STRICT case 在主要 ablation 下仍成立 | ✅ **PASS** |
| **Gate 2** | 至少 1 个跨族 case 在 name-blind / theme-blind 下仍成立 | ✅ **PASS** |
| **Gate 3** | THEME_ONLY 负控制仍被结构规则排除 | ✅ **PASS** |
| **Gate 4** | 最重要的 SUPPORTED 案例不由单一维度决定 | ✅ **PASS** |

### ★ 三个最重要的发现

1. **★ 四个维度全部承重（load-bearing）** —— 把任一维度置为最差，`SUPPORTED` 从 **4 → 0**。
   → **不存在「只靠一个维度」的 SUPPORTED**。
2. **★ 无名称泄漏、无主题泄漏** —— Name-Blind **85/85 完全一致**；
   Theme-Blind 仅 3 处变化，**全部是 `THEME_ONLY` 类**，4 个 `SUPPORTED` 全部保持。
3. **★ Event Structure 无区分力** —— 最小规则比较中 **R2（Lifecycle+Driver+Evidence）≡ R3（+Event）**，
   两者产出完全相同（strict 1 / sup 4 / TO 3 / NOV 27）。
   → Event 维度当前**未提供额外筛选力**（`D4 MATCH = 0/85`，`PARTIAL 74/85`）。

---

## 2. Baseline Freeze（§三）

| 项 | 值 |
|---|---|
| candidate count | 5 |
| historical cycle count | 17 |
| comparison pairs | **85** |
| lifecycle | `MATCH 58` · `PARTIAL 24` · `MISMATCH 3` |
| driver | `MATCH 1` · `PARTIAL 50` · `MISMATCH 29` · `NA 5` |
| evidence sequence | `MATCH 12` · `PARTIAL 29` · `MISMATCH 14` · `NA 30` |
| event structure | `MATCH 0` · `PARTIAL 74` · `MISMATCH 6` · `NA 5` |
| **final status** | **strict 1 / sup 4 / part 46 / TO 3 / INSUF 5 / NOV 27** |

**自检**：审计脚本用**纯函数**重新实现 v0.1 规则，并断言其结果与 v0.1 产物**逐项一致** → `self_check_reproduced = True`。
**未修改 v0.1 任何内容。**

---

## 3. Robustness Method

**两类消融**（区别关键，§四 的「拿掉维度」有两种读法）：

| 类型 | 做法 | 回答的问题 |
|---|---|---|
| **Requirement ablation**（A1–A4） | 把该维度置为**中性通过** | 该维度是否为**必要条件**？（`SUPPORTED` 上升越多 → 越有约束力） |
| **Necessity ablation**（N1–N4） | 把该维度置为**最差** | 该维度是否**承重**？（`SUPPORTED` 下降越多 → 越承重） |

**禁用**：`similarity score` · `confidence %` · `probability` · `top N` · `best analogue` · `ranking`。
**全部输出为离散状态**：`PASS` / `FAIL` / `ROBUST` / `SENSITIVE` / `EVIDENCE_FRAGILE` / `UNSTABLE`。

---

## 4. Dimension Ablation（§四）

### 4.1 Requirement ablation（置为中性通过 → `SUPPORTED` 数）

| case | strict | **supported** | partial | theme_only | no_valid |
|---|---:|---:|---:|---:|---:|
| **baseline** | 1 | **4** | 46 | 3 | 27 |
| A1 Lifecycle removed | 1 | **4** | 48 | 3 | 25 |
| **A2 Driver removed** | **1** | **33** | 27 | 0 | 0 |
| A3 Evidence Sequence removed | 1 | **5** | 45 | 3 | 27 |
| A4 Event Structure removed | 1 | **4** | 46 | 3 | 27 |

**解读**：
- **A2（Driver）→ 33** —— Driver 是**最强约束**（去掉后大量 `PARTIAL/NO_VALID` 涌入 `SUPPORTED`）。
- **A1（Lifecycle）→ 4**、**A4（Event）→ 4** —— 去掉这两个「要求」后 `SUPPORTED` **不变**
  → 对当前这 4 个案例而言，它们**不是必要条件**（但见 §4.2 的承重性）。
- **A3（Sequence）→ 5** —— 去掉顺序要求后多出 1 个。

### 4.2 ★ Necessity ablation（置为最差 → `SUPPORTED` 数）

| case | dimension | supported retained | **load-bearing** |
|---|---|---:|---|
| **N1** | Lifecycle | **0** | ✅ |
| **N2** | Driver | **0** | ✅ |
| **N3** | Evidence Sequence | **0** | ✅ |
| **N4** | Event Structure | **0** | ✅ |

> **★ 四个维度全部承重** —— 把任一维度置为最差，`SUPPORTED` 从 4 降到 **0**。
> → **不存在依赖单一维度的 SUPPORTED 案例。**（Gate 4 的实证基础）

---

## 5. Evidence Ablation（§五）

对每个 `SUPPORTED` 做 leave-one-evidence-out（移除 1 条 DIRECT driver 证据）：

| candidate | historical cycle | DIRECT driver 证据数 | 移除后 status | verdict |
|---|---|---:|---|---|
| `CC-2026-BCI-MEDTECH` | `C-2023-AD` | 3 | `STRUCTURAL_SUPPORTED` | **`ROBUST`** |
| `CC-2026-EMBODIED-AI` | `C-2023-AD` | 3 | `STRUCTURAL_SUPPORTED` | **`ROBUST`** |
| `CC-2026-OPTICAL-LINK` | `C-2025-ROBOTAXI` | 2 | `STRUCTURAL_SUPPORTED` | **`ROBUST`** |
| `CC-2026-OPTICAL-LINK` | `C-2023-COMM-OPTICAL` | 2 | `STRUCTURAL_SUPPORTED` | **`ROBUST`** |

**无 `EVIDENCE_FRAGILE`、无 `COMPLETELY_DEPENDENT`** —— 每个案例都有 ≥2 条 DIRECT driver 证据支撑。

---

## 6. Driver Ablation（§六 —— 本轮最重要测试之一）

| 变体 | strict | **supported** | 说明 |
|---|---:|---:|---|
| **C3 Driver = MATCH\|PARTIAL**（v0.1 baseline） | 1 | **4** | 当前规则 |
| **C1 Driver = MATCH only** | **1** | **1** | 只剩唯一 STRICT |
| **C2 Driver ignored** | 1 | **33** | 去掉 Driver 后暴增 |

**★ 回答「SUPPORTED 是否实际上主要依赖 Lifecycle + Event，而 Driver 只是 PARTIAL」**：

- **否。** 若 Driver 仅为「可有可无」，则 **C2（ignored）应与 baseline 接近** ——
  实际从 **4 → 33**（+29），说明 **Driver 承担了主要筛选**。
- 反之，若把 Driver 收紧为 **MATCH only**，`SUPPORTED` 从 **4 → 1** ——
  说明 3 个案例依赖 `PARTIAL`（机制交集 ≥2）。
- **→ 当前结构类比不是「Lifecycle + Evidence/Event」的伪装，Driver 是核心约束。**

**同时必须诚实记录**：3 个 `SUPPORTED` 的 Driver 状态为 **`PARTIAL`**（交集 2 项），
**仅 1 个为 `MATCH`**。机制交集规模仍小。

---

## 7. Event Ablation（§七）

| 变体 | strict | **supported** |
|---|---:|---:|
| baseline | 1 | **4** |
| **D1 Event Structure ignored** | 1 | **4** |

**→ 去掉 Event 要求后 `SUPPORTED` 不变（4）。**
**但**：见 §4.2 —— 把 Event 置为**最差**则 `SUPPORTED → 0`（Event 承重）。

**两者不矛盾**：
- Event **不作为必要条件**时可以被移除（说明当前 4 例的 Event 都是 `PARTIAL`，从未成为瓶颈）；
- 但 Event **一旦被破坏**则案例失效（说明它是**必要条件**而非**充分条件**）。

**诚实结论**：`event_structure PARTIAL = 74/85` 意味着该维度**几乎总是通过** →
**当前结构类比对该维度并不过度敏感，但该维度也几乎不提供筛选力。**

---

## 8. Sequence Ablation（§八）

| 变体 | strict | **supported** | 说明 |
|---|---:|---:|---|
| **E1 完整 sequence**（baseline） | 1 | **4** | 要求 subtype ∈ {SEQUENCE_MATCH, SEQUENCE_PARTIAL} |
| **E2 只保留 set**（强制 `SET_ONLY`） | **0** | **0** | **全部 SUPPORTED 失效** |
| **E3 完全移除 sequence** | 1 | **5** | 多出 1 个 |

**★ 关键区分（§八 要求）**：
- **「有同样证据」（SET_ONLY）≠「证据以相似顺序出现」** ——
  强制 `SET_ONLY` 后 **`SUPPORTED` 归零**，证明当前 4 个案例**确实依赖顺序**（`SEQUENCE_MATCH` / `SEQUENCE_PARTIAL`）。
- 这直接回应 §八 的要求：**未把 SET_ONLY 当作 MATCH**，且**顺序信息是实质性的**。

---

## 9. Name-Blind Test（§九）

| 项 | 值 |
|---|---:|
| retained | **85 / 85** |
| changed | **0** |
| 引擎使用的名称字段 | **无** |

**结论**：v0.1 引擎的四个正式维度**不读取任何名称字段**（candidate 名称 / cycle 名称 / 公司名 / 行业名）。
名称仅用于展示。→ **Structural Analogy 可以完全脱离名称运行。** ✅

---

## 10. Theme-Blind Test（§十）

| 项 | 值 |
|---|---:|
| retained | **82 / 85** |
| changed | **3** |

**3 处变化（全部为 `THEME_ONLY` 类）**：

| candidate | historical cycle | from | to |
|---|---|---|---|
| `CC-2026-BCI-MEDTECH` | `C-2019-PHARMA-INNOV` | `THEME_ONLY` | `NO_VALID_CORRESPONDENCE` |
| `CC-2026-OPTICAL-LINK` | `C-2019-COMM-5G` | `THEME_ONLY` | `NO_VALID_CORRESPONDENCE` |
| `CC-2026-OFFSHORE-WIND` | `C-2020-POWER-NE` | `THEME_ONLY` | **`STRUCTURAL_PARTIAL`** |

**★ 三个跨族 `STRUCTURAL_SUPPORTED` 全部保持**（`BCI-MEDTECH × C-2023-AD` ·
`EMBODIED-AI × C-2023-AD` · `OPTICAL-LINK × C-2025-ROBOTAXI`）
→ **跨族结构对应确实来自结构，不是主题字段泄漏。** ✅

### ★ 附带发现（须披露）：同族会**压低**等级

第 3 处变化暴露一个**规则次序效应**：`OFFSHORE-WIND × C-2020-POWER-NE`
在**带主题**时判 `THEME_ONLY`，在**去主题**时判 `STRUCTURAL_PARTIAL`。

原因：v0.1 规则中 `elif same_theme: THEME_ONLY` **先于** `elif driver ∈ GOOD: STRUCTURAL_PARTIAL`。
→ **同族标签会把一个本可判 PARTIAL 的配对降为 THEME_ONLY。**

- 这**不是**「同族自动升级」（该风险不存在），而是**反向**的次序效应。
- **不影响 4 个 `SUPPORTED`**（它们不经过该分支）。
- **建议 v0.2 修正**：把「结构性判定」放在「主题表层判定」之前，或让同族不参与降级。

---

## 11. Negative Controls（§十一）

以 3 个 `THEME_ONLY` 为负控制：

| candidate | historical cycle | same_macro_theme | lifecycle | driver | evidence_sequence | 排除原因 |
|---|---|---|---|---|---|---|
| `CC-2026-BCI-MEDTECH` | `C-2019-PHARMA-INNOV` | **True** | `MATCH` | **`MISMATCH`** | `PARTIAL` | driver MISMATCH |
| `CC-2026-OPTICAL-LINK` | `C-2019-COMM-5G` | **True** | `MATCH` | **`MISMATCH`** | **`MISMATCH`** | driver + sequence MISMATCH |
| `CC-2026-OFFSHORE-WIND` | `C-2020-POWER-NE` | **True** | `MATCH` | `PARTIAL` | **`MISMATCH`** | sequence MISMATCH |

**→ 3/3 稳定保持「非结构」**，且**全部为同族** —— 同族**未**使其升级。✅
**Gate 3 PASS。**

---

## 12. 最像名字的反例（§十二）

`CC-2026-EMBODIED-AI × C-2024-ROBOTAXI`：

| 条件 | status |
|---|---|
| Name visible | `NO_VALID_CORRESPONDENCE` |
| **Name blind** | `NO_VALID_CORRESPONDENCE` |
| Theme visible | `NO_VALID_CORRESPONDENCE` |
| **Theme blind** | `NO_VALID_CORRESPONDENCE` |

**四种情况下完全一致** → 该判定**不是**由任何名称字段造成。✅
（原因：`driver = MISMATCH`，`evidence_sequence = NOT_AVAILABLE`）

---

## 13. Comparison Pool Expansion（§十三）

| 项 | 值 |
|---|---:|
| comparison pairs | **85** |
| 期望（笛卡尔积 5 × 17） | **85** |
| **pool 是否已穷尽** | ✅ **是** |
| same-family pairs | 17 |
| cross-family pairs | 68 |
| **expansion delta** | **0** |
| 新关系 | **无** |

**结论：`NO_THEME_FILTERING_APPLIED`** —— v0.1 的 comparison pool **本就是无过滤的全笛卡尔积**，
**未使用 same-theme filtering**。因此不存在「被主题分区过早限制」的关系。✅

---

## 14. Candidate Order Determinism（§十四）

| 排序 | 签名 |
|---|---|
| alphabetical | 一致 |
| reverse alphabetical | 一致 |
| macro-theme order | 一致 |
| dataset order | 一致 |

**`byte_identical = True`**（输出按 `(candidate_id, historical_cycle)` 归一化后比较）→ **顺序不影响任何状态。** ✅

---

## 15. Four Supported Case Cards（§十六）

### Card 1 · `CC-2026-BCI-MEDTECH × C-2023-AD`（汽车）· **跨族** · **唯一 STRICT**

| 维度 | Baseline | Ablation（置为最差） | Robustness |
|---|---|---|---|
| **Lifecycle** | `MATCH` | `0` supported 保留 | **承重** |
| **Driver** | **`MATCH`**（`POLICY_DRIVEN` + `TECH_BREAKTHROUGH`，provenance 均 `DIRECT`） | 承重 | **承重** |
| **Evidence Sequence** | `PARTIAL` / `SEQUENCE_PARTIAL` | 承重 | **承重** |
| **Event Structure** | `PARTIAL` | 承重 | **承重** |

- **Name-blind**：`STRUCTURAL_SUPPORTED`（不变） · **Theme-blind**：`STRUCTURAL_SUPPORTED`（不变）
- **Overall Robustness**：**`ROBUST`** · **Main dependency**：四维共同（无单一依赖）
- **Main contradiction**：无（driver `MATCH` + `DIRECT` provenance）
- **为什么它成立**：四维同时达标；机制集合**完全相等**（全库唯一）；历史侧有 3 条 DIRECT driver 证据。
- **为什么它仍然不能被称为强预测类比**：① 样本仅 1 例，**无统计意义**；
  ② `D4 event_structure` 仅 `PARTIAL`（历史 event_type 集合从未完全相等）；
  ③ 无 market / temporal 上下文；④ 本审计是**规则内部一致性检验**，**不是外部验证**。

### Card 2 · `CC-2026-EMBODIED-AI × C-2023-AD`（汽车）· **跨族**

| 维度 | Baseline | Robustness |
|---|---|---|
| Lifecycle | `MATCH` | 承重 |
| Driver | `PARTIAL`（`POLICY_DRIVEN` + `TECH_BREAKTHROUGH`） | 承重 |
| Evidence Sequence | **`MATCH`** / `SEQUENCE_MATCH` | 承重 |
| Event Structure | `PARTIAL` | 承重 |

- Name-blind / Theme-blind：均 `STRUCTURAL_SUPPORTED`（不变） · **`ROBUST`**
- **Main dependency**：四维共同 · **Main contradiction**：Driver 仅 `PARTIAL`（交集 2 项）
- **为什么它仍然不能被称为强预测类比**：① Driver 非 `MATCH`；② 无同族历史支撑（跨族）；
  ③ 高端装备族在历史侧不存在；④ 无 market / temporal。

### Card 3 · `CC-2026-OPTICAL-LINK × C-2025-ROBOTAXI`（汽车）· **跨族**

| 维度 | Baseline | Robustness |
|---|---|---|
| Lifecycle | `MATCH` | 承重 |
| Driver | `PARTIAL`（`DEMAND_SURGE` + `INDUSTRY_UPGRADE`） | 承重 |
| Evidence Sequence | **`MATCH`** / `SEQUENCE_MATCH` | 承重 |
| Event Structure | `PARTIAL` | 承重 |

- Name-blind / Theme-blind：均 `STRUCTURAL_SUPPORTED` · **`ROBUST`**
- **Main dependency**：四维共同 · **Main contradiction**：Driver 仅 `PARTIAL`
- **为什么它仍然不能被称为强预测类比**：① Driver 非 `MATCH`；② 跨族且两族在历史上无共同背景；
  ③ 历史 cycle 的 `terminal_phase` 与候选阶段无直接关系；④ 无 market / temporal。

### Card 4 · `CC-2026-OPTICAL-LINK × C-2023-COMM-OPTICAL`（信息通信）· **同族**

| 维度 | Baseline | Robustness |
|---|---|---|
| Lifecycle | `MATCH` | 承重 |
| Driver | `PARTIAL`（`DEMAND_SURGE` + `TECH_BREAKTHROUGH`） | 承重 |
| Evidence Sequence | `PARTIAL` / `SEQUENCE_PARTIAL` | 承重 |
| Event Structure | `PARTIAL` | 承重 |

- Name-blind / Theme-blind：均 `STRUCTURAL_SUPPORTED` · **`ROBUST`**
- **Main dependency**：四维共同 · **Main contradiction**：Driver 仅 `PARTIAL`
- **为什么它仍然不能被称为强预测类比**：① 同族 → 存在**主题上下文混杂**可能；
  ② Driver 非 `MATCH`；③ 同族另一 cycle `C-2019-COMM-5G` 判 `THEME_ONLY`（同族内也不一致）；
  ④ 无 market / temporal。

> **四个案例均须保留 `why_not_strong_prediction`**（§十六 要求）。

---

## 16. Strict Case Audit（§十七）

| 项 | 值 |
|---|---|
| candidate | **`CC-2026-BCI-MEDTECH`** |
| historical cycle | **`C-2023-AD`**（汽车） |
| Lifecycle | `MATCH` |
| Driver | **`MATCH`** —— 交集 `['POLICY_DRIVEN', 'TECH_BREAKTHROUGH']` |
| Evidence Sequence | `PARTIAL` / `SEQUENCE_PARTIAL` |
| Event Structure | `PARTIAL` |
| **driver provenance** | `POLICY_DRIVEN: [DIRECT]` · `TECH_BREAKTHROUGH: [DIRECT]` |
| ablation | 四维全部承重（`['lifecycle','driver','sequence','event']`） |
| **overall robustness** | **`ROBUST`** |
| **strict robustness** | ✅ **`PASS`** |

**→ 唯一 STRICT 经得起 robustness 检验。**（**未为维持 1 而放宽规则**）

---

## 17. False Positive Audit（§十八）

| Type | 内容 | 结果 |
|---|---|---|
| **A** | `THEME_ONLY` 不应升级 | ✅ **PASS** —— 3/3 保持 `THEME_ONLY` |
| **B** | 高名称相似但应 `NO_VALID` | ✅ **PASS** —— `EMBODIED-AI × C-2024-ROBOTAXI` 在四种条件下均 `NO_VALID` |
| **C** | `Driver PARTIAL + Lifecycle MATCH` 不应自动升级 | ✅ **PASS** —— 该类配对均停在 `STRUCTURAL_PARTIAL` |
| **D** | `Event PARTIAL + sequence weak` 不应自动升级 | ✅ **PASS** —— `SET_ONLY` 不参与 SUPPORTED 判定（强制后 `SUPPORTED → 0`） |
| **E** | 同族 ≠ structural | ✅ **PASS** —— 3 例同族被降为 `THEME_ONLY` |
| **F** | 跨族 ≠ 自动 structural | ✅ **PASS** —— 68 条跨族中仅 **3** 条 `SUPPORTED` |

**★ 当前最主要的 false-positive 来源（诚实记录）**：

1. **`event_structure = PARTIAL` 的普遍性（74/85）** —— 它几乎总是通过，**不提供筛选力**；
   若某规则误把「event PARTIAL」当作证据，会产生大量假阳性。**当前 v0.1 未这样做**（D4 只是必要条件之一）。
2. **`driver = PARTIAL` 的宽泛性（50/85）** —— 只要交集 ≥1 即 PARTIAL；
   当前靠 `PARTIAL 且交集 ≥2` 才允许 `SUPPORTED`，否则会产生 33 个 SUPPORTED（见 A2/C2）。
3. **同族次序效应**（§10 附带发现）—— 会把 `PARTIAL` 压成 `THEME_ONLY`（**假阴性**方向，非假阳性）。

---

## 18. Minimal Rule Comparison（§十九）

| 规则 | strict | supported | partial | theme_only | no_valid | 跨族 supported |
|---|---:|---:|---:|---:|---:|---:|
| **R0** Lifecycle only | 56 | 56 | 29 | 0 | 0 | 49 |
| **R1** Lifecycle + Driver | **1** | **5** | 46 | **2** | 27 | **4** |
| **R2** Lifecycle + Driver + Evidence | **1** | **4** | 46 | **3** | 27 | **3** |
| **R3** Lifecycle + Driver + Evidence + Event（= v0.1） | **1** | **4** | 46 | **3** | 27 | **3** |
| **R4** Evidence + Event only | 35 | 35 | 43 | 2 | 0 | 30 |

**关键观察**：
- **R0 / R4 完全无区分力**（`SUPPORTED` 56 / 35）→ 缺 Driver 的规则不可用。
- **R2 ≡ R3** → **Event 维度当前不提供任何筛选力**（与 §7 一致）。
- **R1 → R2**：加入 Evidence Sequence 后 `SUPPORTED 5 → 4`、`THEME_ONLY 2 → 3`
  → 顺序要求**排除了 1 个原本会被误判的案例**。

**不追求数量最大**。按 §十九 的四项优先观察：

| 优先项 | R1 | R2 | R3 |
|---|---|---|---|
| 保留 1 个 STRICT | ✅ | ✅ | ✅ |
| 保留跨族案例 | ✅ 4 | ✅ 3 | ✅ 3 |
| 排除 THEME_ONLY | ⚠️ 2 | ✅ 3 | ✅ 3 |
| 排除 name-only 假阳性 | ✅ | ✅ | ✅ |

→ **R2 是最小充分规则**（Event 维度可移除而不损失任何结果）。
**本轮不冻结新算法**（§十九），仅记录该观察供 v0.2 决策。

---

## 19. Robustness Decision（§二十七）

| Gate | 结果 |
|---|---|
| **Gate 1** 至少 1 个 STRICT case 在主要 ablation 下仍成立 | ✅ **PASS** |
| **Gate 2** 至少 1 个跨族 case 在 name-blind / theme-blind 下仍成立 | ✅ **PASS** |
| **Gate 3** `THEME_ONLY` 负控制仍被结构规则排除 | ✅ **PASS** |
| **Gate 4** 最重要的 SUPPORTED 案例不由单一维度决定 | ✅ **PASS** |

> ## **`ROBUST ENOUGH FOR RESEARCH v0.2`**（4/4 Gate PASS）

---

## 20. 三个结论（§二十一）

| 结论 | 回答 |
|---|---|
| **A** 当前 Structural Supported 是否具有足够 robustness？ | ✅ **是** —— 4/4 `ROBUST`；无 `SENSITIVE` / `EVIDENCE_FRAGILE` / `UNSTABLE`；唯一 STRICT `PASS` |
| **B** Structural Analogy 是否依赖名称 / Macro Theme？ | ❌ **否** —— Name-Blind **85/85 一致**；Theme-Blind 仅 3 处变化且全为 `THEME_ONLY` 类；4 个 `SUPPORTED` 全保持 |
| **C** Structural Analogy 是否主要依赖某一个维度？ | ❌ **否** —— 四维**全部承重**（任一置最差 → `SUPPORTED = 0`）；去掉 Driver 则 `4 → 33`，说明 Driver 承担主要筛选 |

**★ 特别检查 §二十一 的告警条件**（「如果 Driver 被移除，大部分 SUPPORTED 仍存在」）：
- 移除 Driver 后 `SUPPORTED` **4 → 33**（**大幅上升**，而非「仍存在」）→ 该告警条件**不成立**。
- **→ 无需把当前结构类比重新定义为「Lifecycle + Evidence/Event correspondence」。**

---

## 21. Research Boundary（§二十二）

| 项 | 状态 |
|---|---|
| **Research robustness** | **`ROBUST ENOUGH FOR RESEARCH v0.2`** |
| **Product readiness** | **NO**（§二十二 明确：即便 robustness 良好也不评估为 Yes） |

**Product 仍需单独处理**：user-facing semantics · explanation format · uncertainty ·
missing data · market context · temporal context · interaction · performance。

---

## 22. Wave 1C（§二十三）

> **`NOT REQUIRED`**

robustness audit **未发现**因历史 coverage 缺失而无法判断的核心 structural relation。
`EMBODIED-AI` 无同族历史的问题已由跨族对应覆盖（`× C-2023-AD` → `STRUCTURAL_SUPPORTED`，`ROBUST`）。

---

## 23. Next Phase

**建议：可进入 `Structural Analogy Research v0.2`**，优先处理三项：

1. **Event Structure 的筛选力**（`PARTIAL 74/85`，R2 ≡ R3）—— 当前**不提供区分度**；
   考虑是否改为「事件时序对齐」而非「类型集合重叠」。
2. **同族次序效应**（§10 附带发现）—— 把结构性判定置于主题表层判定之前。
3. **`driver = PARTIAL` 的宽泛性** —— 考虑要求机制交集 ≥2 作为默认门槛（当前仅在 SUPPORTED 中要求）。

**未自动进入**：Product Integration · UI · AI matcher · scoring · ranking ·
market matching · temporal matching · Wave 1C。

---

## 24. Reproducibility

- 生成器：`research/scripts/build_structural_analogy_robustness_v0_1.py`
  （**deterministic**：无随机 / 无时间依赖 / 无网络 / 无 LLM；消融规则显式可审计）。
- 支持 `--check`：产物与重算结果**逐字节一致**（已执行 `run → check → run → check`）。
- **内置自检**：纯函数实现必须复现 v0.1 baseline（`assert` 强制）。
- **未修改** v0.1 引擎与任何旧产物。

---

*报告结束 · Structural Analogy Robustness Audit v0.1 · 2026-09-19*
