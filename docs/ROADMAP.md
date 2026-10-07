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

## ★★ 当前主线（下一步）：**ThreeC 1.2 —— 接通工作流（Usage-Driven）**（2026-10-06 起）

> 置于此处是刻意的：**这是现在唯一要做的事**。下方 §2 起为状态与历史存档。

> **规划依据**：用 §5「产品最终工作流」逐段对照现状。
> **结论：七段都存在，但没连成一条能走通的路。**

### 逐段对照（2026-10-06 实测）

| 段 | 现状 | 判定 |
|---|---|---|
| 今天 | 首页 Today 线 | ✅ |
| 历史同期 | Calendar Lens | ✅ |
| 历史周期阶段 | Lifecycle Lens | ✅ |
| **当前研究对象** | 本期快照列出 5 个对象 | ⚠️ **列了但点不进去** |
| 历史结构对应 | `StructuralAnalogySection` 四维 | ✅ 但入口在**另一个钻取区** |
| 为什么对应 / 哪里不同 | SA 的 `why_similar` / `why_not_similar` | ✅ 同上 |
| **继续研究** | `research_questions` | ⚠️ 在 CurrentTimeLens 里，**不在快照页** |

**★ 实测证据**：`src/components/CurrentSnapshot/CurrentSnapshotSection.tsx` 中
**没有任何 `onClick` / `onSelect` / `href` / `<button>`** —— 它是一个**死胡同**：
用户看到「79 条比对 · 有结构对应 1 条 · 无有效对应 47 条」，
**既看不到是哪些历史对象，也无法跳去详情**。
（对照：`StructuralAnalogySection.tsx` 有 11 处交互。）

### 主线目标

> **不加新能力，先让已有的七段连成一条能走通的路。**

| 优先级 | 做什么 | 实用理由 |
|---|---|---|
| **P0** | **接通**：快照页的研究对象 → SA 详情；候选计数 → **具体历史对象**（含「为什么不对应」） | 现在页面**给了数字不给内容**，用户无法据此做研究 |
| **P1** | **用户声明研究方向**（`URO-*` 入口 + Research Request） | 5 个对象是研究侧选的；用户关心的方向可能不在其中 —— **无法自己问** |
| **P2** | 当前对象 **vs 历史生命周期**对照 | 「理解主题生命周期」目标的落点 |
| **P3** | 补 **T1/T2 一手来源** | 现有观察**全为 T3**（媒体转述），可信度上限受限 |

### ★★ 2026-10-07 实测修正：**瓶颈是「覆盖」，不是「连接」**

拿用户提的真实方向 **「文化传媒」** 一试，立刻暴露更根本的问题：

| 检查项 | 结果 |
|---|---|
| 52 个 Campaign 中含「传媒 / 文化 / 游戏 / 影视 / 短剧 / 出版 / 元宇宙」 | **0 条** |
| 44 个主题名中含传媒 / 文化类 | **0 个** |
| 5 个当前研究对象中含传媒 | **0 个** |
| 而该方向**当下正在动** | **2026-09-29 文化传媒板块领涨**（新浪财经当日复盘） |

**历史覆盖集中度（实测）**：汽车 · 消费 · 电子/半导体 · 资源 · 金融 · 高端装备 · 电力设备 ·
信息通信 · 医药健康 · 国防军工 · 房地产 —— **硬科技 + 高端制造 + 消费 + 资源 + 金融**。
**不含**传媒 / 文化 / 娱乐 / 教育 等方向。

**结论**：

1. **P0（接通）解决不了「文化传媒」** —— 数据里根本没有对应对象，接什么都接不上。
2. **已做的最小改动**：把**覆盖边界**做成首页可见的声明（`App.tsx` `.seasonal-scope`），
   用户一问就知道「在不在覆盖内」，而不是查半天查不到。
   ★ 该声明是**人工维护**的（canonical export 已冻结，不得改其 provenance）。
3. **待定**：是否**扩边**（把传媒 / 文化等纳入历史研究）？
   - ROADMAP §2 现行政策是 **`Research expansion: DEFERRED`**。
   - 扩边 = **新研究轮次**，工程量大，且必须遵守 Research 的规则（不得为凑数放宽）。

> ★ 这次实测印证了规划里那句话：**ThreeC 至今没有被真实使用过一次** ——
> 一用就撞到了最根本的边界问题。

### ★★ 2026-10-07 两次真实使用测试 → **覆盖地图**

| 方向 | 历史 | 当前对象 | 实测能做什么 |
|---|---|---|---|
| **医药健康** | 1 Campaign | **1** | ✅ **完整工作流** —— 给出**跨主题**结构洞察（报告见 `USAGE_TEST_2026-10-07_PHARMA.md`） |
| **汽车** | **7 Campaign** | **0** | ⚠️ **历史可用，问不了「现在」**（报告见 `USAGE_TEST_2026-10-07_AUTO.md`） |
| **文化传媒** | 0 | 0 | ❌ **完全覆盖不到** |

**三种缺口性质完全不同**：文化传媒 = 双向都无（需扩边）· 汽车 = 历史厚但当前空（需补当前对象）·
医药健康 = 两侧都有（只是没出口）。

> ★ **最重要的结论：缺的不是历史深度，是「当前侧」的覆盖面。**
> 全库 **5 个当前对象** vs **52 个 Campaign / 44 个主题名** ——
> 用户想研究的方向**大概率不在这 5 个里**。**这是入口太窄，不是数据不足。**

→ **P1（用户声明研究方向）应上调**：让用户能声明一个方向并得到明确回答
（有当前对象 → 完整工作流；只有历史 → 历史侧；都没有 → 诚实说覆盖不到）。

### 为什么 P0 排在「加功能」之前

1. **零新增能力** —— SA v0.5 的 395 条解释**已经在包里**，只是**没有出口**。
2. **不加这段，后面每加一个功能都会变成又一个死胡同。**
3. 它直接决定「这个工具到底帮不帮得上」—— 而 ThreeC **至今没有被真实使用过一次**。

### 与「使用测试」的关系

**P0 完成后立即做一次真实使用**：拿一个真正关心的方向，走完整条工作流，记录卡点。
**流程只有真跑过一次才算成立**（1.1 的月度流程演练已经证明了这一点 —— 5 个缺陷全是「真用」才暴露的）。

---

## 2. ★ 当前状态：**ThreeC 1.1 — RELEASED**（1.0 已冻结）

**目标（已达成）**：把已通过 Research / Product / Trust / Quality / Real Usage / Gate M 的 ThreeC，
变成**可稳定访问、可重复构建、可追溯、可回滚**的静态产品，并**正式发布 1.0**。

| 项 | 值 |
|---|---|
| **Version** | **`1.0.0`** |
| **Tag** | **`v1.0.0`**（annotated） |
| **Release commit** | **`064d39c`**（`release: ThreeC 1.0.0`） |
| **Production URL** | **https://yangfanbit.github.io/Cycle/** |
| **Gate R / P / T / Q / U / M / D / G** | **全部 PASS** |
| **P0 / P1** | **0 / 0** |

当前冻结 / 发布状态：

> Research Core：**FROZEN**
> Product **1.1.0：RELEASED**（tag `v1.1.0`）· 1.0 已冻结（tag `v1.0.0`）
> Deployment：**PRODUCTION**
> Historical Universe：**79**（52 Campaign + 27 Research Candidate）
> Research expansion：**DEFERRED**
> SA / TO：**FROZEN**

**1.1 新增（已上线）**：Market Snapshot 运行时 · 本期研究快照页面 · 快照 diff（月度变化）·
两个纯投影器 · 东方财富 EOD 取数 · Lifecycle Tracking · 首页大主题分类配色 ·
旧「历史相似阶段」视图退役。详见 `docs/CHANGELOG.md` 1.1.0 条目。

**1.1+ 只允许由真实 Product Usage 或明确 Research Question 触发。不预设大量新功能。**

**发布主流程（已落地并已执行）**：

```text
push main
    ↓  GitHub Actions（.github/workflows/deploy.yml）
npm ci → tsc -b → npm test → npm run build（base=/Cycle/）→ 上传 dist/ → deploy-pages
    ↓
https://yangfanbit.github.io/Cycle/
    ↓  操作手册
docs/DEPLOYMENT_RUNBOOK.md
```

| 技术决策 | 结论 |
|---|---|
| 部署平台 | **GitHub Pages**（唯一）；不使用 Vercel / Netlify / Docker / 云服务器 / CDN 产品化 |
| 访问入口 | `https://yangfanbit.github.io/Cycle/` |
| Vite `base` | `THREEC_BASE` > `GITHUB_ACTIONS === 'true'` → `/Cycle/` > `/`（本地 dev / preview 不受影响） |
| provenance（D7） | `src/data/buildProvenance.ts` 在 Product 内展示 version / commit / export `source_commit` / SA / TO |
| 回滚（D6） | 基于 commit SHA + revert（**不伪造 `v1.0.0`**） |
| 重建（D8） | `DEPLOYMENT_RUNBOOK.md` §1–§3 |
| SPA fallback | **不需要**（无 client-side router，仅 query param） |
| `.nojekyll` | **不需要**（产物无 `_` 前缀文件） |

**已执行（Deployment / Release Engineering + 1.0 Release）**：

- `.github/workflows/deploy.yml`（`npm test` 为硬门禁，绝不跳过；只上传 `dist/`；权限最小化）
- `vite.config.ts` base 解析 + `vite define` 注入 provenance
- `src/data/buildProvenance.ts` + `<BuildProvenanceFooter />`
- `src/data/__tests__/deployment.test.ts`（24 用例，workflow 契约由测试锁死）
- `docs/DEPLOYMENT_RUNBOOK.md`
- **1.0 Release 执行**：`package.json → 1.0.0` → release commit `064d39c` →
  annotated tag `v1.0.0` → `git push origin main` + `git push origin v1.0.0` →
  Actions build + deploy PASS → 线上入口 **200 OK** → smoke / 语义 smoke 全通过
- **实测**：`npm test` 678 passed / 0 failed · `tsc -b` 0 error · `vite build` PASS ·
  Actions `build` PASS + `deploy` PASS · 线上 provenance = `1.0.0` / commit `064d39c`

**★ 明确不重开**（除非真实使用产生新的 P0 证据或明确 Research Question）：
R01 / Research 扩容 / SA 扩容 / TO 扩容 / Driver vocabulary / Dashboard / Radar / backend。

---


## 2a. 上一主线（已闭环）：**Product / Real Usage Iteration**（2026-09-23 起）

> Research Core 已 Release（见 §1）。主线曾由「Research → Product」切换为
> **Product Stabilization + Real Usage Validation**。
> **该主线已于 2026-09-24 闭环：P0 清零（Gate T8 PASS）。**

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

### 已完成
- 阶段 A–C：Product 测试 **21 failed → 0 failed** · `tsc -b` PASS · `vite build` PASS
- 阶段 D–F：SA / TO 消费验收 · **P0 修复**（见 `docs/PRODUCT_REAL_USAGE_BASELINE_v0_1.md`）
- 阶段 G：移动端静态审计 + TO 详情网格 3 列 → 2 列（P1）

### 已完成（Lifecycle Repair v0.1）—— 已闭环上一轮 Next Single Goal
- 根因：export lifecycle 来自**手写静态字典**（与 intake 解耦）→ `CANDIDATE_LIFECYCLE` 仅 11/27，且丢 `UNKNOWN` / open-ended 段
- 修复：**从 intake 派生**（单一真源）`build_lifecycle_from_intake_v0_1.py` + `batch_auto_research.py` **intake 优先**
- 结果：RC lifecycle **11/27 → 23/27** · 段 **187 → 243** · **PEAK 22 → 46** · UNKNOWN **未被伪装**
- SA **v0.4 → v0.5**（60 条变化**全部仅 lifecycle 维度**；structural_status 变化 **0**）
- **Driver v0.4 不变**（输入未变）· **TO v0.2 不变**（输出未变）· 新增 `validate_lifecycle_coverage_v0_1.py` 防回归

### 已完成（1.0 P0 修复轮）—— **Gate T8 由 FAIL → PASS，P0 = 0**

> 完整定义见 `docs/THREEC_1_0_RELEASE_DEFINITION.md`。

- **P0-1**：`historicalCase.ts` 改读 Research `c.lifecycle`（空则 `[]`）；
  `researchAttention.ts::terminalPhaseOf` 删除 `c.phases` 回退 → `UNKNOWN`。
  **实证：4 个 UNKNOWN-only RC 的虚构阶段 4 → 0。**
- **P0-1c（审计新发现）**：`STAGE_TO_PHASE` 漏 `ENDED`（Contract 成员）→ 静默退化为 `UNKNOWN`
  → 已补；2 个已结束 Campaign 由 `UNKNOWN` 纠正为 `END`。
- **P0-1d**：`ExportLifecycleStageV1.start/end` 类型改为 `string | null`（Contract 允许开放区间）；
  5 个消费点显式处理，`tsc -b` **12 error → 0**。
- **P0-1e**：`CampaignDetail` 第二处独立 `m.phases` 渲染路径同样虚构「主升」→ 已改读 Research `lifecycle`。
- **D3 由 `it.fails` 正式化**；新增 **Scenario F1–F9** Gate T8 全局不变量（含反向非空断言）。
- `derivePhases()` / `c.phases` **完整保留**（Timeline 视觉分段仍依赖）。

### 1.0 八 Gate 现状

| Gate | 状态 |
|---|---|
| Research · Product · Trust · Quality · Real Usage · Documentation | **PASS** |
| Mobile | PASS（静态；真机复核为 **P2**） |
| **Deployment** | **★ 本轮目标**（P1-1 处理中；访问入口验证待线上执行） |
| P0 | **0** |
| P1 | 见 `docs/THREEC_1_0_RELEASE_DEFINITION.md` §8 |

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
