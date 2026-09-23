# ROADMAP.md — ThreeC 当前路线

> 路线图只描述当前之后的工作；历史实施细节见 `docs/CHANGELOG.md`。

## 1. 已完成基座

### Research
- Research Model v1.0 Frozen
- Historical Data Production
- Theme / Campaign / Sub-theme model
- CMTR v1
- Current Research Discovery
- Time Observation v0.5
- Driver Canonicalization
- Structural Analogy Feasibility / Robustness / Calibration
- **Structural Analogy Rule Set v0.3**（Frozen）
- **Structural Analogy Research v0.4**
- **Structural Analogy Explanation Artifact v0.4**
- **Driver Canonicalization v0.4**
- **Time Observation v0.2**（内部 `artifact_version` 0.3）

### ★★ Research Core Release v0.4 —— **COMPLETE / FROZEN**（2026-09-23）

| 项 | 正式基线 |
|---|---|
| Historical Objects | **79**（52 Campaign + 27 Research Candidate） |
| Macro Theme roots | 11 |
| Driver Canonicalization | **v0.4** |
| Structural Analogy | **v0.5**（395 pairs · lifecycle 输入修复后） |
| Time Observation | **v0.2**（内部 0.3） |
| Product 消费 | **已消费最新 SA / TO artifact** |

> **Research Core 后续只允许由「真实 Product Usage 暴露的问题」触发新研究轮次。**
> 不再主动：扩展 Historical Universe · 新增 Driver vocabulary · 微调 SA rule · 为增加 Pattern 挖数据。

### Product
- Timeline
- Current Time Lens
- Calendar Lens
- Lifecycle Lens
- Current Candidate
- Preview / Production isolation
- Static PWA runtime

## 2. ★ 当前主线：**Product / Real Usage Iteration**（2026-09-23 起）

> Research Core 已 Release（见 §1）。主线由「Research → Product」切换为
> **Product Stabilization + Real Usage Validation**。
>
> **最高原则**：目标从 `Research correctness` 切换为 `Real Research Usability` ——
> 一个用户能否从「今天」出发，顺畅完成一次完整历史研究，并得到**可理解、可追溯、不误导**的结果。

### 主流程（Product 必须逐段可用）

```
Today
 ↓  Current Candidate
 ↓  Time / Calendar（Current Time Lens · Time Observation）
 ↓  Lifecycle（生命周期位置）
 ↓  Structural Analogy（结构对应与不对应）
 ↓  Historical Case（历史对象详情）
 ↓  Evidence（证据 / 时间轴）
 ↓  New Research Question（「这里为什么不一样？」「还缺什么证据？」）
```

**★ Product 不重新实现 Research Logic** —— 只消费 Research artifact，保留 provenance 与不确定性。

### 本轮（v0.1）已完成
- 阶段 A–C：Product 测试 **21 failed → 0 failed**（622 passed）· `tsc -b` PASS · `vite build` PASS
- 阶段 D–F：SA v0.4 / TO v0.2 消费验收 · **P0 修复**（见 `docs/PRODUCT_REAL_USAGE_BASELINE_v0_1.md`）
- 阶段 G：移动端静态审计 + TO 详情网格 3 列 → 2 列（P1）
- 详见 `docs/PRODUCT_REAL_USAGE_BASELINE_v0_1.md`

### 本轮（Lifecycle Repair v0.1）已完成 —— **已闭环上一轮 Next Single Goal**
- 根因：export lifecycle 来自**手写静态字典**（与 intake 解耦）→ `CANDIDATE_LIFECYCLE` 仅 11/27，且丢 `UNKNOWN` / open-ended 段
- 修复：**从 intake 派生**（单一真源）`build_lifecycle_from_intake_v0_1.py` + `batch_auto_research.py` **intake 优先**
- 结果：RC lifecycle **11/27 → 23/27** · 段 **187 → 243** · **PEAK 22 → 46** · UNKNOWN **未被伪装**
- SA **v0.4 → v0.5**（60 条变化**全部仅 lifecycle 维度**；structural_status 变化 **0**）
- **Driver v0.4 不变**（输入未变）· **TO v0.2 不变**（输出未变）· 新增 `validate_lifecycle_coverage_v0_1.py` 防回归

### 下一步
**唯一目标**：**重新由真实使用判断**（本轮已闭环上一目标；不自动开始下一项开发）。

---

## 2b. 历史主线：Research → Product（已归档）

> **同步说明（2026-09-19）**：Step 1–4 已全部完成（Gate PASS · Adapter · UI Integration · UX Review PASS）。
> 其后追加完成：**Historical Case Experience v0.1（PASS）** ·
> **Historical Cycle Map v0.1（PASS）** · **Current Research Refresh Loop v0.1（PASS）** ·
> **First Real Observation Cycle v0.1（PASS）** ·
> **Historical Case Evidence View Rework v0.1（PASS）** ·
> **Second Real Observation Cycle v0.1（PASS · 0 code change）**。
> 核心路径 `Current Candidate → Cycle Map → Lifecycle Position → Cross-family SA →
> Evidence Timeline → New Research Question` 已在真实使用中自然发生。
> 下一步由**用户**决定，**不在 roadmap 内预设**。

### Step 1 · Product Similarity Architecture Gate v0.1

**已完成：PASS。**

不是 UI 开发，而是 Product 语义和模块职责定稿。

必须正式决定：

1. Calendar / Lifecycle / Structural Analogy 三者边界
2. `currentSimilarity.ts`：兼容层 / 重构 / 废弃
3. `historicalSimilarPhase.ts` 长期定位
4. Structural Analogy 的唯一 Current → Historical Structural Correspondence 入口
5. Evidence Category vs Mechanism Driver
6. Structural Status / dimension status 的产品表达
7. WHY SIMILAR / WHY NOT / UNKNOWN 如何表达
8. Explanation Artifact 的最终接口
9. OpportunityRadar 的最终 legacy 处置

**已输出：**
- Architecture Gate / Decision document
- Explanation Artifact v0.2
- Product-facing Artifact 最小契约

本阶段结束，不再重复执行。

### Step 2 · Product Adapter v0.1

**已完成：PASS。**（后续由 Research Core Release 升级为 v0.4 artifact 输入）

`structural_analogy_explanations_v0_2.json → Product View Model`

前置条件：Step 1 Gate = PASS。

要求：
- Product 只消费 Research 结果
- 不重新实现 Structural Analogy
- 不做 score / ranking / probability
- 保留 provenance
- 保留 UNKNOWN / NOT_AVAILABLE
- 稳定导航到 historical cycle / campaign
- 不破坏 Calendar / Lifecycle

### Step 3 · Product UI Integration

优先进入：

**Current Time Lens / Current Candidate**

目标：

`Current Candidate → Structural Analogy → Historical Case`

不是新增一个孤立 Dashboard。

### Step 4 · UX Review

验证：
- 5 秒理解“今天在哪里”
- 30 秒找到研究入口
- 2 分钟完成一次历史结构比较
- 不把历史对应误读成预测
- 移动端可读
- 信息密度合理

## 3. 非主线 Quality Backlog

> **★ 状态说明（2026-09-23）**：以下全部为 **KNOWN LIMITATION**，
> **不再标记为 BLOCKING**，也不再阻塞任何 Product / Real Usage 推进。
> 只有当真实使用暴露「影响核心判断的错误」时才升级处理。

### ★ Known Limitations 清单（2026-09-24 更新）

| # | 限制 | 影响 | 状态 |
|---|---|---|---|
| **L1** | 剩余 **7 项**跨 canonical 子串冲突（含 v0.1 既有遗留如 `结构迁移`、`倍/翻倍`、`利润/净利润`、`出清/出清完成`、`标准体系/标准体系（2026 版）`） | 相关文本无法成为 `DIRECT`；**不改变任何 driver 集合** | `KNOWN LIMITATION` |
| **L2** | `driver = MATCH` 仅 **1** 条 / `event MATCH` 仅 **1** 条 | 数据粒度限制（**不得**通过放宽规则解决） | `KNOWN LIMITATION` |
| **L3** | **2** 个 cycle 因**映射逻辑**无 canonical driver（`RC-2015-FIN-LEVERAGE` 多命中 · `RC-2024-SECONDARY` 研究自述强度不足） | 非数据缺口 | `KNOWN LIMITATION` |
| **L4** | TO `observation.year`（研究对象研究年份）与 `date`（锚点日期）在「锚点退化为 `campaign.start_date` 且落在上一日历年度」时相差 1 年（5 例，全部 R01） | 年度归属口径问题；改则属规则变更，需独立轮次 | `KNOWN LIMITATION` |
| ~~L5~~ | ~~Research export `lifecycle` 映射缺口~~ → **✅ 已修复（Lifecycle Repair v0.1）**：改为**从 intake 派生**（单一真源）；RC lifecycle **11/27 → 23/27**、PEAK **22 → 46**；剩 4 个仅含 intake `UNKNOWN` 的 RC **保持空**（**不虚构**，语义由 `research_status = INSUFFICIENT` 承载） | **已解除** |

### Driver Evidence Depth

当前最大 Research 质量债：
- Driver MATCH = 1/79（Historical Objects 扩容后）
- MULTI_MECHANISM = 4

后续如补证据，必须围绕真实缺口，不得以提高 SUPPORTED 数量为目标。

### Historical Date Verification

`campaign_date_observations = 24`，当前 verified = 0/24。

不阻塞 Architecture / Adapter；作为可信度债继续记录。

### Market / Temporal Context

继续：

**SUPPLEMENTARY_ONLY**

除非新的 Research question 明确要求，不进入 Structural Status。

### Coverage Expansion

**Wave 1C 暂停。**

仅在新研究问题证明必须扩容时重新开启。

> **同步（2026-09-19）**：第二次真实使用已确认瓶颈是 **Historical Universe 太窄**
> （4 个 Macro Theme · 85 条比较中仅 1 条 STRICT 结构对应）→ **触发条件成立**。
> Coverage Expansion 以 **R01 独立研究轮次**形式重新开启；
> **R00（Historical Universe Expansion / Research Intake Protocol v0.1）已完成基础设施**：
> - `research/intake/HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md`（协议）
> - `research/intake/HISTORICAL_UNIVERSE_COVERAGE_PLAN_v0_1.md`（覆盖方向）
> - `research/intake/historical_research_intake.schema.json`（交付结构）
> - `research/intake/HISTORICAL_UNIVERSE_R01_TASK_MANIFEST_v0_1.json`（R01-01 ~ R01-06）
> - `research/scripts/validate_historical_research_intake.py`（机器校验器）
>
> **同步（2026-09-23）**：**R01-01 ~ R01-06 已全部完成并入库**（52 Campaign + 27 Research Candidate），
> Historical Universe 由 17 → **79** objects。**Coverage Expansion 现已回到 `FROZEN / DEFERRED`。**
>
> 重新开启的**唯一条件**：新的 Research Question 证明「Historical Universe 不足」。

## 4. 当前明确不做

- 不继续扩 Time Observation Pattern
- 不继续调 Structural Analogy v0.2 规则
- 不为了提高 SUPPORTED 数量放宽规则
- 不新增 schema entity
- 不做 similarity score / percentage / probability / ranking
- 不做实时行情 / 资金流 / 通知 / 后台
- 不做新的 Radar / Dashboard
- 不在 Adapter 前重写 Product

## 5. 产品最终工作流

```
今天
  ↓
历史同期
  ↓
历史周期阶段
  ↓
当前研究对象
  ↓
历史结构对应
  ↓
为什么对应 / 哪里不同
  ↓
继续研究
```
