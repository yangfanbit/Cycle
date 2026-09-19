# PRODUCT_SIMILARITY_ARCHITECTURE_GATE_v0_1

> | 项目 | 值 |
> |---|---|
> | 性质 | **Adapter 前的最终架构闸门**（不是 UI 开发，不是 Adapter 实现） |
> | 完成日期 | 2026-09-19 |
> | 起始状态 | `HEAD = origin/main = 1a1f74c`，ahead/behind `0/0`，工作树 clean（**自行核对**，已先 `git merge --ff-only` 同步远程 3 个 doc commit） |
> | 依据 | `AGENTS.md` · `docs/ARCHITECTURE.md` · `docs/PRODUCT_SIMILARITY_ARCHITECTURE_REVIEW.md` · `docs/STRUCTURAL_ANALOGY_EXPLANATION_ARTIFACT_v0_1.md` · `docs/ROADMAP.md` · `docs/PROJECT_STATE.md` |
> | **Gate 结论** | **`PASS`**（含 1 项 artifact 修正，已落地为 v0.2） |

---

## 0. Executive Summary

**闸门问题**：三个「比较视角」职责是否清晰？`currentSimilarity.ts` 去留？Artifact 能否被 Product 安全消费？

**结论**：

| 项 | 结论 |
|---|---|
| 三个比较视角 | ✅ **正式冻结**（Calendar / Lifecycle / Structural Analogy，职责互斥且可共存） |
| `currentSimilarity.ts` | ⚠️ **`LEGACY / FREEZE`** —— **停止扩展、不删除、不改写**；待 UI 需求验证后处置 |
| `historicalSimilarPhase.ts` | ✅ **正式确认为 Lifecycle Lens 长期组件** |
| Artifact v0.1 → **v0.2** | ⚠️ **需修正 4 项 Product-facing 契约语义** —— 已生成 `structural_analogy_explanations_v0_2.json`（**v0.1 逐字节保留**） |
| `Evidence Category` ≠ `Mechanism Driver` | ✅ **正式确定** |
| OpportunityRadar | ✅ **`LEGACY / DEPRECATED FOR NEW USE`**（本轮不删除） |
| **Gate** | ✅ **`PASS`** |

**★ 关键事实**：`src/**` **零改动**（build bundle 382.27 kB 未变）；schema / export / 历史数据 **零改动**；旧研究产物**逐字节保留**。

---

## A. 三个比较视角的最终职责

| 视角 | 核心问题 | 性质 | 输入 | 输出性质 | 是否允许 score/tier |
|---|---|---|---|---|---|
| **Calendar Lens** | 这个时间附近历史上发生过什么？ | **时间邻近浏览** | `timeline_export_v1` | 同期案例列表 | ❌ 不允许 |
| **Lifecycle Lens** | 历史上谁处于类似生命周期阶段？ | **历史阶段浏览** | `timeline_export_v1` | 阶段相近案例（分档） | ⚠️ 允许**离散档位**（高/中/参考），**不允许连续分数与排序榜单** |
| **Structural Analogy** | 当前结构与历史结构在哪些维度对应？ | **正式 Current → Historical Structural Correspondence** | `structural_analogy_explanations_v0_2.json` | 结构等级 + 逐维解释 | ❌ 不允许（**离散状态 + 逐维理由**） |

### 冻结条款

1. 三者**可共存**，但**不得共用「相似度」作为产品名称**。
2. **Structural Analogy 是 Product 唯一正式的 Current → Historical Structural Correspondence 能力。**
3. Product **不得**重新计算 Structural Analogy 的四个维度。
4. Lifecycle Lens 是 Structural Analogy 的**一个子维度视角**，但**不等价于**完整结构对应。
5. Calendar Lens 与另外两者**正交**（时间邻近 ≠ 结构相似）。

---

## B. `currentSimilarity.ts` 最终处置建议

### 现状（实测）

| 项 | 事实 |
|---|---|
| 位置 / 规模 | `src/data/timeline/currentSimilarity.ts`，**485 行** |
| 问题 | **Current Candidate × Historical**（与 Structural Analogy **同一问题**） |
| 判定体系 | 内部 `SIMILARITY_WEIGHTS` · **`score: number`** · `tier: SimilarTier` · `stars` · **`scored.sort()` + `slice(0, 3)`** |
| 主要导出 | `similarPhaseForCandidate` · `CurrentSimilarCase` · `CurrentSimilarityView` · `SIMILARITY_WEIGHTS` · `narrativeTypesOfCampaign` · `narrativeProvenanceOf` · `candidatePatternOf` · `phasePositionOf` |
| 引用方 | `src/components/CurrentTimeLens/CurrentCandidateSection.tsx` · `currentCandidateAdapter.ts` · 2 个测试文件 |

### 处置：**`LEGACY / FREEZE`（兼容保留，不删除、不扩展、不改写）**

**理由**：

1. **与 Structural Analogy 目标问题重叠**，但**判定体系不同** → 同时维护会造成「两套 Current → Historical 算法」。
2. 其 **`score` + `tier` + Top-3 排序** 与 Rule Set v0.2 的「离散状态、无分数、无排名」原则**直接冲突** ——
   若长期共存，Product 会同时出现两种「相似」语义（review §2 明确反对）。
3. **但**：`currentCandidateAdapter.ts` 与 `CurrentCandidateSection.tsx` **当前正在使用它**；
   在本 Gate 不做 Adapter / UI 改动的前提下，**删除会破坏现有 Product 行为** → **无必要风险**。
4. 其部分**非重叠**能力（`narrativeTypesOfCampaign` / `narrativeProvenanceOf` /
   `candidatePatternOf` / `phasePositionOf`）可能被 Adapter 复用 → **不宜整文件删除**。

### 后续处置路径（**不在本 Gate 执行**）

```
Step 3（Adapter 设计）→ 判定哪些导出被 Adapter 复用
        ↓
Step 4（UI 集成）→ 用真实 UI 需求验证重叠程度
        ↓
Step 5（UX Review）→ 三选一：
  ① 兼容保留（仅旧路径使用）
  ② 改造成 thin adapter（剥离 score/tier，改为消费 Explanation Artifact）
  ③ 废弃（迁移完成且无引用后删除）
```

> **本 Gate 硬约束遵守**：**未删除** `currentSimilarity.ts`；**未修改** 其任何代码。

---

## C. `historicalSimilarPhase.ts` 最终定位

### 现状（实测）

| 项 | 事实 |
|---|---|
| 位置 / 规模 | `src/data/timeline/historicalSimilarPhase.ts`，**253 行** |
| 问题 | **Historical × Historical**（与 Structural Analogy **不同问题**） |
| 判定 | Lifecycle / Pattern / Driver 分类；`SimilarTier = HIGH / MEDIUM / REFERENCE` + `TIER_STARS` |
| 引用方 | `src/components/HistoricalSimilarPhase/HistoricalSimilarPhase.tsx`（已在 `App.tsx` 挂载） |

### 定位：✅ **正式确认为 Lifecycle Lens 长期组件**

**理由**：

1. 它回答的是「**历史上谁处于类似生命周期阶段**」—— 这是**浏览工具**，
   与 Structural Analogy 的「**当前 → 历史结构对应**」是**不同问题**。
2. 其输入是 `timeline_export_v1`（历史侧），**不依赖** Current Candidate，与 Structural Analogy **输入不重叠**。
3. 已在 `App.tsx` 主流程挂载，是**稳定产品能力**。

### 边界（须长期遵守）

- 其 `SimilarTier` 是**离散档位**（高/中/参考），**不得**演化为连续分数或榜单。
- **不得**把它当作 Structural Analogy 的替代品；两者**并列不可互替**。
- 其 API 与 UI 边界在 **Step 3/4** 正式固化；本 Gate 不改动其代码。

---

## D. Structural Analogy Product Contract

### D.1 消费契约

```
Consumer      : Product（View / Adapter 层）
Mode          : READ_ONLY —— **Product 不得重新实现 Structural Analogy 规则**
Rule source   : Structural Analogy Rule Set v0.2（唯一规则来源）
Source        : research/research/reports/structural_analogy_explanations_v0_2.json
Snapshot      : 2026-09-15
Coverage      : 5 candidates × 17 historical objects = 85 explanations
```

### D.2 Product 必须遵守（**红线**）

| # | 红线 |
|---|---|
| 1 | 不把 `UNKNOWN` / `NOT_AVAILABLE` 当成 `NO`（**缺失证据 ≠ 现象不存在**） |
| 2 | 不把 `PARTIAL` 当成 `MATCH` |
| 3 | 不把 `Theme Relation` 变成等级因素（**不得**据此升降级） |
| 4 | 不重新计算四个维度 |
| 5 | 不生成 score / ranking / probability / prediction |
| 6 | 不联网 |
| 7 | 不把 `explanations[]` 的数组顺序当作强弱排名 |
| 8 | 不把 `Market` / `Temporal` 当作结构判定依据 |

### D.3 最小契约（正式确定）

见 §E / §F / §G。**字段名与语义以 `structural_analogy_explanations_v0_2.json` 为准。**

---

## E. Artifact identity 规范（★ 本轮修正项 5.3）

### 问题（实测确认）

v0.1 把 `RC-*` 对象标为 `historical_campaign_id` —— **语义错误**。

**根因**：`exports/timeline_export_v1.json` 的 `research_candidates[]` **复用了 `campaign_id` 字段名**
（值为 `RC-*`），因此无法按字段名区分 Campaign 与 Research Candidate。

> **不得修改 export**（frozen）。→ 修正落在 **artifact 层**：按**来源数组**判定 kind。

### 正式规范

```jsonc
"identity": {
  "historical_object_kind": "campaign" | "research_candidate",
  "historical_cycle_id": "...",              // 统一稳定 id（始终非空）
  "historical_campaign_id": "C-..." | null,  // **仅真实 Campaign 非空**
  "historical_research_candidate_id": "RC-..." | null,  // **仅 Research Candidate 非空**
  "historical_theme_cycle_id": "...",
  "identity_note": "..."
}
```

**硬约束**：

> **不得**把 `historical_campaign_id` 当作「所有历史对象」的总身份。
> 需要「任一历史对象」的稳定引用时，**必须**使用 `historical_cycle_id`。

**实测分布**（v0.2）：`campaign 65` · `research_candidate 20`（= 5 candidates × 13 / × 4）。✅

---

## F. Provenance 规范（★ 本轮修正项 5.4）

### 正式分层

| 层 | 字段 | 含义 | Product 用法 |
|---|---|---|---|
| **直接依据** | `dimension_evidence.{lifecycle \| mechanism_driver \| evidence_sequence \| event_structure}` | 该**维度判定**的直接证据 | ✅ 可作为「为什么这个维度是这个状态」的依据 |
| **背景来源** | `background_sources[]`（每项带 `role: "BACKGROUND_ONLY..."`） | 背景上下文 | ⚠️ **仅作背景展示**，**不得**作为维度判定依据 |

**硬约束**：

> **Product 不得对同一组 provenance 做因果推断。**
> 只有 `dimension_evidence` 是该维度的**直接依据**；`background_sources` **不是**。

**`background_sources` 包含**（全部标 `BACKGROUND_ONLY`）：
`historical_macro_theme` · `historical_terminal_phase`（**不得用于 current-phase analogy**）·
`historical_driver_provenance_summary` · `candidate_source_summary`。

---

## G. status / uncertainty 规范

### G.1 五级结构状态（离散，**无分数**）

`STRUCTURAL_SUPPORTED` · `STRUCTURAL_PARTIAL` · `THEME_ONLY` ·
`INSUFFICIENT_EVIDENCE` · `NO_VALID_CORRESPONDENCE`

> `STRICT_STRUCTURAL_SUPPORTED` 为**独立布尔标记**（Driver 必须 = `MATCH`），
> **不得**把 `PARTIAL` 包装成 supported。

### G.2 四维状态词表

| 维度 | 词表 |
|---|---|
| `lifecycle` | `MATCH` · `PARTIAL` · `MISMATCH` · `UNKNOWN` · `NOT_AVAILABLE` |
| `mechanism_driver` | `MATCH` · `PARTIAL` · **`PERIPHERAL_OVERLAP`** · `MISMATCH` · `UNKNOWN` · `NOT_AVAILABLE` |
| `evidence_sequence` | `MATCH` · `PARTIAL` · `MISMATCH` · `UNKNOWN` · `NOT_AVAILABLE` |
| `event_structure` | `MATCH` · `PARTIAL` · `MISMATCH` · `NOT_AVAILABLE` |

### G.3 不确定性语义（**强制**）

| 命题 | 含义 |
|---|---|
| `UNKNOWN` ≠ `NO_PATTERN` | 有资料但不足以判断 |
| `NOT_AVAILABLE` ≠ `NO_PATTERN` | **当前资料不足以编码** |
| **missing evidence ≠ absence of phenomenon** | 缺证据不等于现象不存在 |
| incomplete chronology ≠ sequence mismatch | 顺序资料不全 ≠ 顺序冲突 |
| `PERIPHERAL_OVERLAP` | **不属于** structural support |

### G.4 排序语义（★ 本轮修正项 5.2）

> `explanations[]` 按 **`historical_cycle_id` 升序** 排列 ——
> **这是稳定 identity 顺序，不是强弱排名。**
> **已移除** v0.1 的 `structural_status → cycle_id` 排序（易被读成「从强到弱」）。

### G.5 Theme Relation 语义（★ 本轮修正项 5.1）

`theme_relation` 改为**对象**：

```jsonc
"theme_relation": {
  "value": "SAME_MACRO_THEME" | "CROSS_MACRO_THEME",
  "role": "METADATA_ONLY —— 不参与 Structural Status 判定，不得据此升降级",
  "note": "跨 Macro Theme **不是**「不相似」的依据；同族 **也不是**「相似」的依据。"
}
```

**已移除**：v0.1 中 `CROSS_MACRO_THEME` 出现在 `why_not_similar` 的写法。
生成器内置自检：`why_not_similar` 中出现 theme 相关内容即 `FAIL`。✅

---

## H. OpportunityRadar 处置

### 现状（实测）

| 项 | 事实 |
|---|---|
| 位置 | `src/components/OpportunityRadar/OpportunityRadar.tsx` |
| **`App.tsx` 引用数** | **0**（**未接入主流程**） |
| 逻辑性质 | 经验规则日历提醒（**非** Research-derived） |

### 处置：**`LEGACY / DEPRECATED FOR NEW USE`**（**本轮不删除**）

- **不得**继续扩展。
- **不得**作为 Structural Analogy 的入口。
- **不得**成为新的 Product 能力。
- 若未来重新设计，**必须**由 Research-derived historical context 驱动，**不得**沿用旧经验规则日历。

**后续**：在 Step 4 / Step 5 确认无引用后删除（**不在本 Gate 执行**）。

---

## I. Research → Artifact → Adapter → UI 最终数据流

```
【Research 层 · 已冻结】
research/current/current_candidates.json
        +
Research DB  →  timeline_export_v1.json
        ↓
Structural Analogy Research v0.2           （Rule Set v0.2 执行结果）
        ↓
structural_analogy_explanations_v0_2.json （★ Product-facing Artifact · READ_ONLY 契约）
        ↓
【Product 层 · 尚未实现】
Product Adapter                            （Step 3：Artifact → View Model，无 score/ranking）
        ↓
Current Time Lens / Current Candidate      （Step 4：UI 集成）
        ↓
User Experience Review                     （Step 5）

【并列存在，互不替代】
Calendar Lens      ← timeline_export_v1（时间邻近）
Lifecycle Lens     ← timeline_export_v1（生命周期阶段，historicalSimilarPhase.ts）
```

### 数据流硬约束

| # | 约束 |
|---|---|
| 1 | **Product 不重新实现** Structural Analogy 规则 |
| 2 | Product **不产生**新的研究结论 |
| 3 | Adapter **只做** `Artifact → View Model` 映射（不判定、不重算、不排序） |
| 4 | UI **不消费** Research 原始产物（只消费 Adapter 输出） |
| 5 | `timeline_export_v1` 与 Explanation Artifact **互不修改** |
| 6 | 三个视角**并列**，Calendar / Lifecycle 的入口**不得**被 Structural Analogy 取代 |

---

## J. Gate 结论

> ## ✅ **`PASS`**

### 判定依据

| 检查项 | 结果 |
|---|---|
| 三个比较视角职责冻结 | ✅ 完成（§A） |
| `currentSimilarity.ts` 处置决定 | ✅ `LEGACY / FREEZE`（§B，**未删除、未修改**） |
| `historicalSimilarPhase.ts` 定位 | ✅ 确认为 Lifecycle Lens（§C） |
| Artifact Product-facing QA | ⚠️ **发现 4 项需修正** → 已生成 **v0.2**（§E/§F/§G） |
| Artifact 修正是否改变研究结论 | ❌ **未改变**（生成器内置一致性自检：状态计数与 Research v0.2 **完全一致**） |
| Product-facing Artifact 最小契约 | ✅ 确定（§D/§E/§F/§G） |
| `Evidence Category` ≠ `Mechanism Driver` | ✅ 正式确定（§D + artifact `dimension_naming`） |
| OpportunityRadar 处置 | ✅ `LEGACY / DEPRECATED FOR NEW USE`（§H） |
| 数据流最终形态 | ✅ 确定（§I） |

### 为什么是 `PASS` 而非 `CONDITIONAL PASS`

Artifact 的 4 项修正**已在 Gate 内完成**（v0.2 已生成并通过全部自检），
**不存在**遗留的阻塞项；且修正**未改变任何研究结论**（一致性自检 PASS）。
`currentSimilarity.ts` 与 `OpportunityRadar` 的最终删除**不属于本 Gate 范围**（需 Step 3–5 输入），
已在 §B / §H 明确标注为**延后决定**，**不构成 Gate 阻塞**。

### 本轮明确未做

- ❌ 未实现 Product Adapter
- ❌ 未改 UI
- ❌ 未改 schema / `timeline_export_v1` / 历史数据
- ❌ 未改 `Structural Analogy Rule Set v0.2`
- ❌ 未重新运行 Structural Analogy Research
- ❌ 未做 Wave 1C
- ❌ 未新增 score / ranking / probability / prediction
- ❌ 未把 Research 规则重新实现到 Product
- ❌ 未删除 `currentSimilarity.ts` / `OpportunityRadar`

---

## 附：Artifact v0.1 → v0.2 修正清单

| # | 问题 | 修正 | 自检 |
|---|---|---|---|
| **5.1** | `CROSS_MACRO_THEME` 出现在 `why_not_similar` | 移出；`theme_relation` 改为对象（`value` + `role` + `note`），显式 `METADATA_ONLY` | ✅ `why_not_similar` 无 theme 内容 |
| **5.2** | `explanations[]` 按 `structural_status` 排序 | 改为**稳定 identity 顺序**（`historical_cycle_id` 升序） | ✅ 实测 `C-2019-AD … RC-2024-SECONDARY` |
| **5.3** | `historical_campaign_id` 被当作总身份（`RC-*` 实为 Research Candidate） | 新增 `identity` 对象，按**来源数组**判定 kind | ✅ `campaign 65` / `research_candidate 20` |
| **5.4** | `provenance` 混层 | 拆为 `dimension_evidence`（直接依据）与 `background_sources`（背景） | ✅ 4 维直接依据 + 全部 `BACKGROUND_ONLY` |

**版本与保留**：
- 新版本号 = **`0.2`**，产物 `structural_analogy_explanations_v0_2.json`
- **v0.1 逐字节保留**（`structural_analogy_explanations_v0_1.json`，实测 `git diff` 为空）
- **未修改** `Structural Analogy Research v0.2` / Rule Set v0.2 / 任何原始数据
- **修正未改变既有研究结论**（一致性自检：状态计数与 Research v0.2 完全一致）

---

## 附：验证结果

| 项 | 结果 |
|---|---|
| `build_structural_analogy_explanation_v0_2.py --check` | ✅ **PASS**（run→check→run→check 逐字节） |
| `build_structural_analogy_explanation_v0_1.py --check` | ✅ PASS（v0.1 未受影响） |
| Research v0.2 / Calibration v0.2 / Research v0.1 / Robustness v0.1 | ✅ PASS |
| Feasibility v0.3 / v0.1 · Readiness v0.2 · Driver Canonicalization | ✅ PASS |
| Time Observation build · Discovery v0.5 `--check` | ✅ PASS |
| 7 个 research validators | ✅ 全 PASS |
| `npm test` / `tsc -b` / `npm run build` | ✅ 395/395 · exit 0 · PASS |
| **`src/**` 修改** | ✅ **零修改**（bundle 382.27 kB 未变） |
| schema / export / 历史数据修改 | ✅ **零修改** |
| 旧研究产物逐字节 | ✅ **保持不变** |

---

*Gate 文档结束 · Product Similarity Architecture Gate v0.1 · 2026-09-19*
