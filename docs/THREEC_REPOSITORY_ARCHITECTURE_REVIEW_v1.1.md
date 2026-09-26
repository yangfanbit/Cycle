# THREEC_REPOSITORY_ARCHITECTURE_REVIEW_v1.1.md

> | 项目 | 值 |
> |---|---|
> | 性质 | **Phase 1.1 仓库架构只读审查报告**（Read-only Review） |
> | 轮次 | ThreeC 1.1 Phase 1.1 |
> | 日期 | 2026-09-26 |
> | 基线 | `main` @ `738638d`（= `origin/main`）· tag `v1.0.0` → `064d39c` · worktree clean |
> | Canonical Repository | https://github.com/yangfanbit/Cycle |
> | 本轮改动 | **零代码、零数据**（仅新增本报告） |
> | 结论 | **PASS WITH FINDINGS** —— 无阻断性违规；发现 **4 项架构债**，其中 **F-1 须在 Phase 1.2 前处置** |
>
> 上游：`docs/THREEC_1_1_MARKET_SNAPSHOT_ARCHITECTURE.md` ·
> `docs/MARKET_SNAPSHOT_CONTRACT_v0.2.md` · `docs/MARKET_SNAPSHOT_GOVERNANCE.md`

---

## 0. 审查目标

用户指定的三项检查：

| # | 检查项 |
|---|---|
| 1 | **数据流** —— 确认 `Research → Generator → Export Artifact → Product`；避免 Frontend 直接读取 Research 原始数据 |
| 2 | **Product 消费边界** —— 确认 Product 只消费 artifact |
| 3 | **Market Snapshot 落点** —— 确认新增位置 |

---

## 1. 检查项 1 · 数据流

### 1.1 理想形态

```
Research（DB / intake / scripts）
        ↓  Generator（research/scripts/*.py）
Export / Product-facing Artifact
        ↓  静态 import（Vite alias，只读）
Product（src/）
```

### 1.2 实测入口（4 个，不是 1 个）

`vite.config.ts:74-78`：

| Alias | 指向 | 性质 |
|---|---|---|
| `@exports` | `exports/` | **Canonical Export**（Contract v1.0） |
| `@current` | `research/current/` | Current Research Discovery artifact |
| `@observation` | `research/research/reports/` | SA / TO / Driver artifact 目录 |
| *(无 alias)* | `data/`（仓库根） | Legacy 核验数据层 —— **实测无任何消费者**（见 F-3 修正），当前为死代码 |

被 `src/` 直接 import 的研究产物（实测）：

| 文件 | 消费点 | 产物 |
|---|---|---|
| `@exports/timeline_export_v1.json` | `buildProvenance.ts:38` · `timelineAdapter.ts` | Export v1.0 |
| `@observation/structural_analogy_explanations_v0_5.json` | `buildProvenance.ts:39` | SA v0.5 |
| `@observation/time_observation_patterns_v0_2.json` | `buildProvenance.ts:40` | TO v0.2 |
| `@observation/historical_driver_canonicalization_v0_1.json` | `historicalCase.ts:98`（动态 import） | Driver canon v0.1 |
| `@current/current_candidates.json` | `currentCandidate.ts:23` | Current Candidate v1.0 |
| `@current/fixtures/example_candidates.json` | `App.tsx:24` | **示例 fixture**（文档化，`?candidates=example`） |

生成器（Research → Artifact）实测存在：
`batch_auto_research.py` · `export.py` · `build_structural_analogy_*` · `build_time_observation_patterns*` ·
`build_lifecycle_from_intake_v0_1.py` · `build_governance_classification_v0_1.py`。

### 1.3 判定

| 判定 | 结论 |
|---|---|
| **Frontend 是否直接读取 Research 原始数据？** | ✅ **否**。实测 `src/` 未 import 任何 `research/database` · `research/intake` · `research/scripts` · 中间产物（`_seasonal_analysis/` · `structural_analogy_research_*` · `*_candidate_events`）。 |
| **是否只消费 artifact？** | ✅ 是 —— 消费对象全部是**版本化 Product-facing artifact**。 |
| **入口是否收敛为 1 个？** | ⚠️ **否** —— 有 **4 个入口**（3 个 alias + 1 个手维护数据集）。 |

### 1.4 建议（Phase 1.2 决定）

1. **不必强行收敛为单一 export** —— SA / TO / Driver 从设计上就是「Product-facing Artifact · READ_ONLY」（见 Architecture Gate §D），直接消费**是既定设计**，不是缺陷。
2. **但要明文形式化边界**（写入 AGENTS.md / 本报告的硬约束章节）：
   > Product 可消费「**版本化只读研究产物** + **canonical export**」；
   > **永远不得**触碰 `research/scripts` · `research/database` · `research/intake` · 任何中间结果。
3. **`data/`（仓库根）为死代码，非活跃双源** —— 见 F-3（含**初判修正**）。

---

## 2. 检查项 2 · Product 消费边界

### 2.1 硬约束（既有，已被本轮确认）

- Product 不重新实现 SA 规则
- Product 不产生新的研究结论
- 不生成 score / ranking / probability / prediction
- 不联网 / 不调 LLM

### 2.2 实测：2 处 Product 侧「自造逻辑」

#### ★ F-1（最高优先级）：`currentSimilarity.ts` 评分引擎**仍在线并渲染到 UI**

实测：

| 位置 | 内容 |
|---|---|
| `currentSimilarity.ts:151` | `export const SIMILARITY_WEIGHTS = {…}` |
| `currentSimilarity.ts:207` | `tier: SimilarTier` |
| `currentSimilarity.ts:210` | `score: number` |
| `currentSimilarity.ts:308` | `export function similarPhaseForCandidate(...)` |
| `currentCandidateAdapter.ts:59-61` | 从 `./currentSimilarity` 导入并组装 `similarity: CurrentSimilarityView` |
| `CurrentCandidateSection.tsx:191-192` | `results.filter(r => r.tier === 'HIGH' / 'MEDIUM')` |
| `CurrentCandidateSection.tsx:423-428` | **渲染 `{TIER_LABEL[r.tier]}` + `{r.stars}`** |

**判定**：

> Product 中存在一个**内部的评分 / 分档 / 星级**相似度引擎，且**已渲染进生产 UI**。
> 该引擎与冻结的 SA v0.5 **不是同一套判定体系** —— 即：UI 上「历史相似」列表的强弱次序，
> **并非 Research 的正式结构结论**，而是 Product 自算结果。
>
> 这与 `AGENTS.md` §5 / Architecture Gate §D 的
> 「Product 不重新计算 Structural Analogy」「不生成 score / ranking」**直接冲突**。

**状态**：Architecture Gate 已将其标记为 **`LEGACY / FREEZE`**（不删除、不扩展），当时因 UI 依赖而未动。
**本轮判定**：该状态**不可带入 Phase 1.2** —— 因为 1.2 的核心正是建立「正式结构匹配」，
若 Product 同时保留一套自算星级，用户会看到**两套互相矛盾的「相似」**。

**建议**：Phase 1.2 准入条件（见 §5）—— 退役或降级该引擎。

#### ★ F-2：`derivePhases()` —— Product 侧再派生生命周期

| 位置 | 内容 |
|---|---|
| `timelineAdapter.ts:49` | `export function derivePhases(...)` |
| `timelineAdapter.ts:126 / 716 / 787` | 三处调用，产出 `phases` |
| `researchAttention.ts:115` | 明令：**不得**回退到视图分段 `campaign.phases` |
| `historicalCase.ts:168 / 252` | 注释：`phases` 是 adapter 派生的**视图分段**（Timeline 视觉用） |

**判定**：1.0 P0 修复轮已把「研究结论」与「视觉分段」分离（`lifecycle` 读 Research，`phases` 仅视觉），
`derivePhases()` **被有意保留**。→ **不是违规**，但属于**命名与语义双轨**债：
Product 侧存在「研究 lifecycle」与「派生 phases」两套阶段表示，未来易被误用。

**建议**：保留，但在 `AGENTS.md` 中固化其**唯一合法用途 = Timeline 视觉分段**，禁止进入任何研究语义。

#### ✅ 已确认的正确做法

| 位置 | 内容 |
|---|---|
| `structuralAnalogy.ts:28` | 明确声明**不复用** `currentSimilarity.ts` 的任何判定逻辑 |
| `HistoricalCycleMapSection.tsx:12` | 明确「**不排序**：无 similarity score / ranking / probability / Top-N」 |

### 2.3 判定

| 项 | 结论 |
|---|---|
| Product 是否读取了非法数据 | ✅ 否 |
| Product 是否重算研究结论 | ⚠️ **是（F-1）** —— 评分相似度引擎在线并已渲染 |
| Product 是否越界派生 | ⚠️ 存在（F-2）但已被约束在视觉用途 |

---

## 3. 检查项 3 · Market Snapshot 落点（已批准）

### 3.1 决策

```
research/current/
├── README.md
├── schema.json                    （既有）
├── current_candidates.json        （既有）
├── narrative_annotations.json     （既有）
├── fixtures/                      （既有）
├── snapshots/                     （既有）
└── market_snapshots/              ★ 新增
```

### 3.2 理由

1. **`research/` 整体在冻结范围内** —— 不可重排既有目录。
2. `research/current/` 已是「**当前研究 Artifact**」的既有语义归属（Current Candidate 协议在此）。
   Market Snapshot 与 Correction Record 属同类「**当前研究过程**」，与「历史事实」分离（架构 §4）。
3. **新增子目录 = 纯增量**，不触碰任何既有文件 → 满足「不修改冻结 artifact」。

### 3.3 与纠错的落点（建议，Phase 1.2 确认）

| Artifact | 建议位置 |
|---|---|
| Market Snapshot（`MS-*`） | `research/current/market_snapshots/` |
| Research Request（`RR-*`） | 同上或 `research/current/requests/` |
| Correction Record（`CR-*`） | `research/corrections/`（**新增顶层目录**；纠错面向历史 artifact，不应混入 current） |
| Import Record（`IR-*`） | `research/current/import_records/`（Phase 1.4） |

### 3.4 Vite alias（Phase 1.2 决定）

若 Product 需消费 Market Snapshot，建议新增 alias：

```ts
'@market': fileURLToPath(new URL('./research/current/market_snapshots', import.meta.url)),
```

**硬约束**：只能指向 `market_snapshots/` **目录**，不得开放到 `research/current/` 更上层（否则 `fixtures` 等会进入可达范围）。

---

## 4. 架构债清单（按优先级）

| ID | 债 | 级别 | 建议处置 |
|---|---|---|---|
| **F-1** | `currentSimilarity.ts` 评分/tier/stars 引擎在线且已渲染 UI，与冻结 SA 双轨 | **P0（阻塞 Phase 1.2）** | Phase 1.2 前退役或降级（见 §5） |
| **F-2** | `derivePhases()` 与研究 `lifecycle` 双轨表示 | P1 | 固化用途为「仅 Timeline 视觉分段」 |
| **F-3** | 仓库根 `data/`（raw/candidate/verified/validation，759 行 TS）+ `src/data/index.ts` barrel | **P2**（**初判 P1「活跃双源」有误，已修正**） | ✅ **已处置：保留 + 标注**（人工核验为后续计划）。`data/README.md` 已加入当前状态说明。修正依据见下方「F-3 修正」 |

### F-3 修正（2026-09-26 复核）

初判 writing 时据 `src/data/index.ts` 的 import 语句推断其为「活跃双源」。**实测复核推翻该判断**：

| 实测项 | 结果 |
|---|---|
| `src/` 或 `tests/` 中引用 `data/candidate` · `data/raw` · `data/validation` · `data/verified` | **0 处** |
| `src/data/index.ts`（barrel）被 import | **0 处** |
| `data/verified/campaigns.ts` 内容 | **空数组**（`verifiedCampaigns: HistoricalCampaign[] = []`，注释明写「当前：0 条」） |
| `TimelineDataSource.kind = 'verified'` 的实例化 | **仅 1 处，且是测试 mock**（`historicalCycleMap.test.tsx:192`）；生产无实例化 |

→ **结论**：`data/` 与 canonical export **并不构成运行时双源**。它是一条**从未接通的备用核验管线**（V1.5 遗留），
生产 Timeline 的默认与唯一数据源仍是 `exports/timeline_export_v1.json`。
**降级为 P2：无正确性风险，仅是可维护性问题（759 行无人引用）。**
| **F-4** | 数据入口 4 个（3 alias + data/），无统一清单 | P2 | 在 `AGENTS.md` 固化「允许/禁止消费清单」 |

---

## 5. Phase 1.2 准入条件（Definition of Entry）

进入 Phase 1.2（Research Runtime）**前**必须闭环：

| # | 条件 |
|---|---|
| **G-1** | **F-1 处置完毕**：UI 中不得再出现非 Research 结论的星级 / tier 排序「历史相似」列表。可接受方案：① 退役 `currentSimilarity.ts`，该区块改由冻结 SA 解释驱动；② 保留但**显式标注为 LEGACY 且不再展示强弱次序** |
| **G-2** | `AGENTS.md` 新增「Product 允许消费清单」（4 入口白名单）+「禁止触碰清单」 |
| **G-3** | Market Snapshot 目录 `research/current/market_snapshots/` 建立（可为空 + `.gitkeep` + README） |
| **G-4** | 确认 Phase 1.2 **只复用冻结 SA v0.3**，不新造匹配算法（架构 §8 硬约束） |

---

## 6. 本轮明确未做

- ❌ 未修改任何代码（`src/` 零改动）
- ❌ 未修改任何 Research 数据 / export / contract / schema
- ❌ 未新建 Market Snapshot 目录（待 Phase 1.2 与 G-3 一并执行）
- ❌ 未新增 Vite alias
- ❌ 未 commit / 未 push

---

*审查报告结束 · ThreeC Repository Architecture Review v1.1 · 2026-09-26 · 只读审查，零代码改动*
