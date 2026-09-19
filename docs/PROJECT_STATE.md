# PROJECT_STATE.md — ThreeC 当前真实状态

> 动态接班文档：只回答“现在是什么状态、哪里有问题、下一步做什么”。
> 长期规则见 `AGENTS.md`；未来路线见 `docs/ROADMAP.md`；历史细节见 `docs/CHANGELOG.md`。

- 更新日期：2026-09-19
- branch：`main`
- ahead / behind：`0 / 0`
- working tree：clean
- HEAD：`c246b94`（`fix(research): normalize R01-01 intake conflict schema`；本文件随 R01-02 Canonical Import 提交入库）
- 最近完成：**R01-02 Canonical Decision & Import v0.1**（PASS；**8 个 PROMOTE 入 Canonical DB，4 个 RESEARCH_ONLY 保留**）

## 1. 项目当前定位

**ThreeC = A股历史机会时间轴 / 历史机会地图。**

核心价值：

> 从历史周期里找结构，而不是从历史数据里找同名主题。

主链路：

`今天 → 历史同期 → 历史周期阶段 → 当前研究对象 → 历史结构对应 → 为什么对应 / 哪里不同 → 继续研究`

不是交易决策、预测、买卖信号、概率或推荐系统。

## 2. 当前总阶段

### Research Core：第一版闭环完成

`Historical Model → Historical Data → Time Observation → Current Research → Structural Analogy`

当前已完成：
- Structural Analogy Rule Set v0.2 冻结
- Structural Analogy Research v0.2 baseline
- Structural Analogy Explanation Artifact v0.2
- Product Similarity Architecture Gate v0.1 — PASS
- Product Adapter v0.1（Structural Analogy Artifact → Product View Model）
- Time Observation v0.5
- CMTR v1
- Historical Driver Canonicalization
- Robustness / Feasibility / Readiness

### Product Core：闭环已成立，并已具备可重复的研究更新循环

```
Current Time → Current Candidate → Structural Analogy → Historical Case
             → Historical Cycle Map → Current Research Refresh Loop
```

**已完成**：Product Similarity Architecture Gate v0.1（PASS）· Product Adapter v0.1 ·
Product UI Integration v0.1 · UX Review + Performance Gate v0.1（PASS）·
Historical Case Experience v0.1（PASS）· Historical Cycle Map v0.1（PASS）·
**Current Research Refresh Loop v0.1（PASS）**。

当前 Product 主线：

`Timeline → Current Time Lens → Lifecycle Lens → Calendar Lens`

Current Candidate 已进入 Current Time Lens。

Structural Analogy 已通过 Adapter 接入 Current Candidate / Current Time Lens。UI Integration v0.1 已完成。

## 3. Structural Analogy 当前基线

Research v0.2：
- 5 Current Candidates
- 17 Historical Cycles
- 85 comparison pairs
- STRICT_STRUCTURAL_SUPPORTED = 1
- STRUCTURAL_SUPPORTED = 4
- STRUCTURAL_PARTIAL = 36
- THEME_ONLY = 3
- INSUFFICIENT_EVIDENCE = 5
- NO_VALID_CORRESPONDENCE = 37

规则版本：

`structural-analogy-ruleset-v0.2`

最大瓶颈仍是机制级 Driver 证据深度，不是规则或 vocabulary。

## 4. Product-facing Artifact 与 Adapter

已新增：
- `docs/STRUCTURAL_ANALOGY_EXPLANATION_ARTIFACT_v0_1.md`
- `research/research/reports/structural_analogy_explanations_v0_1.json`
- `research/scripts/build_structural_analogy_explanation_v0_1.py`
- `research/research/reports/structural_analogy_explanations_v0_2.json`
- `research/scripts/build_structural_analogy_explanation_v0_2.py`
- `src/data/timeline/structuralAnalogy.ts`
- `src/data/timeline/__tests__/structuralAnalogy.test.ts`
- `src/components/CurrentTimeLens/StructuralAnalogySection.tsx`
- `src/components/CurrentTimeLens/__tests__/structuralAnalogySection.test.tsx`

Artifact 覆盖 85 explanations，且：
- 来源唯一 = Structural Analogy Research v0.2
- 规则唯一 = Rule Set v0.2
- Product READ_ONLY
- 无 score / ranking / probability
- `--check` 可逐字节复现

**v0.2 已通过 Architecture Gate；Adapter v0.1 已消费该契约。**
1. `why_not_similar` 不应把 CROSS_MACRO_THEME 当成“为什么不相似”。
2. explanations 当前按 structural status 再按 cycle id 排列；虽然不是研究 ranking，但 Product 很容易把数组顺序误读为排名，应去除这种暗示。
3. `historical_campaign_id` 同时承载 historical campaign 与 Research Candidate，需要在 Adapter 前明确 cycle / campaign identity。
4. provenance 需要明确哪些证据支撑哪个维度，避免 Product 误把候选全部证据理解为每个维度的直接依据。

因此：

> **Explanation Artifact v0.2 是当前 Product Adapter 的 Research-facing 输入；v0.1 只作为历史保留。**

## 5. 当前 Product Architecture Debt

### 三套比较体系

1. `currentSimilarity.ts`
   - Current Candidate × Historical
   - 内部 score / tier
   - 当前 UI 已使用

2. `historicalSimilarPhase.ts`
   - Historical × Historical
   - Lifecycle Lens
   - 内部 score / tier

3. Structural Analogy
   - Current Candidate × Historical Cycle
   - Lifecycle / Mechanism Driver / Evidence Sequence / Event Structure
   - 正式 Research Correspondence
   - 离散状态，不以 score 定义

长期目标：

- Calendar = 时间邻近浏览
- Lifecycle = 生命周期浏览
- Structural Analogy = 正式结构对应

不能长期维护三套“历史相似算法”。

### Driver 双层语义

Product Current Candidate：
- 证据类别：POLICY / INDUSTRY / CAPITAL / SENTIMENT / EXTERNAL

Structural Analogy：
- 驱动机制：POLICY_DRIVEN / INDUSTRY_UPGRADE / TECH_BREAKTHROUGH / …

以后必须明确区分“证据类别”与“驱动机制”。

### OpportunityRadar

`src/components/OpportunityRadar/` 当前不在 `App.tsx` 主流程。

状态：

**LEGACY / DEFER**

不在 Architecture Gate 前删除。

## 6. Time Observation

Time Observation v0.5 已完成并暂时冻结：

- raw candidates = 315
- distinct samples = 139
- independent robust structures = 1
- TOP-01 = N7 / center 06-11 / window 05-27~06-26 / recurrence 5/7
- cross-family robust = 0

不再为了增加 Pattern 数量继续扩容或放宽标准。

## 7. 当前唯一下一目标

# R01-03：资源 / 有色 / 化工（**未启动**）

**已完成（全部 PASS）**：… Product 侧全部轮次 · **R00**（Intake Protocol）· **T01**（taxonomy gap）·
**R01-01 Canonical Import** · **Intake Validator C25**（严格 Draft-07）· **R01-02 Canonical Import**。

**当前无已确认 P1（Product 侧）。**

### R01 进度

| task_id | scope | status |
|---|---|---|
| `R01-01` | 高端装备 / 机器人 | ✅ **已导入 Canonical**（+5 campaigns） |
| `R01-02` | 半导体 / 电子 | ✅ **已导入 Canonical**（+8 campaigns / +4 RESEARCH_ONLY） |
| `R01-03` | 资源 / 有色 / 化工 | `PLANNED_NOT_STARTED` |
| `R01-04` | 消费 | `PLANNED_NOT_STARTED` |
| `R01-05` | 金融 / 地产 | `PLANNED_NOT_STARTED` |
| `R01-06` | 军工 | `PLANNED_NOT_STARTED` |

### Historical Universe 当前实测

| 项 | 值 |
|---|---:|
| Macro Theme 根节点 | **11** |
| **有 Campaign 的根节点** | **6**（汽车 · 医药健康 · 信息通信 · 电力设备 · 高端装备 · **电子**） |
| Historical Campaign | **26** |
| Research Candidate（导出层） | 10 |
| 跨族 Campaign 对 | `C(6,2)` = **15** |

**R01-02 新增 8 个 Canonical**：`C-2019-SEMI-LOCALIZATION` · `C-2020-SEMI-EQUIPMENT` ·
`C-2020-PANEL-CYCLE` · `C-2019-CONSUMER-TWS` · `C-2023-AI-COMPUTE-SEMI` ·
`C-2024-SEMI-MEMORY` · `C-2022-SEMI-DOWNTURN` · `C-2016-PANEL-CYCLE`。
详见 `docs/R01_02_CANONICAL_DECISION_v0_1.md`。

**新增机制轴覆盖**：供给收缩 / 价格周期 · 纯需求端驱动 · 库存周期型下行。

### Structural Analogy

**未刷新**（`structural_analogy_explanations_v0_2.json` 字节不变）。Rule Set v0.2 与 Research v0.2
均 FROZEN，AGENTS.md §4 禁止覆盖旧轮次产物。**建议 R01 全部完成后以新 artifact 版本统一刷新。**

### 未决与待办（**未排期**）

| 类型 | 项 |
|---|---|
| OPEN | `CF006`（2024-09-24 后市场 Beta）**保留 UNRESOLVED**；`C-2024-SEMI-MEMORY` 以 medium 置信度进入并保留限定 |
| OPEN | `CF008`（2017 显卡/矿机归属）保留未裁决 |
| OPEN | R01-02 的 3 条 `evidence-temporal-mislabel` 警告（Package 自身 `temporal_relation` 与 lifecycle 端点不一致） |
| OPEN | `E056`（2024-05-24）被包内绑定至 `C-2020-SEMI-EQUIPMENT`（2020–2021），日期不符 |
| OPEN | **5 个 root 仍无 Campaign**：资源 · 消费 · 金融 · 房地产 · 国防军工 |
| OPEN | R01-01 / R01-02 的别名 taxonomy 缺口（芯片 / 集成电路 / 面板 / 存储 / HBM / GPU / 消费电子 等） |
| POLISH | `themeCycleId` 可读性 · `event_type` ↔ 证据类别标签对应 |
| DEFER | `event_structure` 区分度 · `campaign_date_observations verified = 0/N` |

### 边界

- 不新增 Product 功能 / 不新增 Dashboard
- 不改 Research Model v1.0 / schema / CMTR v1 / Export Contract v1.0 /
  Structural Analogy Rule Set v0.2 / Time Observation v0.5
- 不引入实时网络 / LLM · 不建立 ranking / score / probability / prediction

## 8. 当前质量债务

非主线 blocker：
- campaign_date_observations verified = 0/24
- Driver DIRECT evidence depth
- market / temporal = SUPPLEMENTARY_ONLY
- historical coverage imbalance

这些问题暂不阻塞本阶段 Review，但性能问题必须在 Product polish 前闭环。

## 9. 验证基线

最近已报告全绿：
- Structural Analogy Explanation `--check` PASS
- Research validators 全 PASS
- npm test 476/476
- tsc -b PASS
- vite build PASS

下一轮任何实现先核对真实 HEAD，再执行验证。
