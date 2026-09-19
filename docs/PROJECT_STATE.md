# PROJECT_STATE.md — ThreeC 当前真实状态

> 动态接班文档：只回答“现在是什么状态、哪里有问题、下一步做什么”。
> 长期规则见 `AGENTS.md`；未来路线见 `docs/ROADMAP.md`；历史细节见 `docs/CHANGELOG.md`。

- 更新日期：2026-09-19
- branch：`main`
- ahead / behind：`0 / 0`
- working tree：clean
- HEAD：`e4ec504`（`docs(research): second real observation cycle v0.1`；本文件随 Snapshot Freshness Polish 提交入库）
- 最近完成：**Snapshot Freshness Polish v0.1**（PASS；`stale` 阈值 `> 0` → `> 14`）

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

# 由真实研究产生的新 Research Question 决定（无已确认 P1）

**已完成（全部 PASS）**：Product Similarity Architecture Gate v0.1 · Product Adapter v0.1 ·
Product UI Integration v0.1 · **UX Review + Performance Gate v0.1** ·
**Historical Case Experience v0.1** · **Historical Cycle Map v0.1** ·
**Current Research Refresh Loop v0.1** · **First Real Observation Cycle v0.1** ·
**Historical Case Evidence View Rework v0.1** · **Second Real Observation Cycle v0.1** ·
**Snapshot Freshness Polish v0.1**（`stale` 阈值 `> 0` → `> 14`）。

**当前无已确认 P1。** 下一步由**真实研究产生的新 Research Question**决定，不由 Agent 预设。

### 待 Research 验证的研究问题（**只记录，不排期，不做 Product 功能**）

> **历史案例从「政策触发」到「产业 / 公司催化」的时间间隔，是否存在可重复的结构？**

第二次真实研究观察到的样本（**4 个样本，尚不足以称为规律**）：

| 历史案例 | 政策/产业触发 | 公司/产业催化 | 间隔 |
|---|---|---|---:|
| `C-2023-AD`（汽车 · 智能驾驶） | 2023-06-21 `policy.trigger` | 2023-07-03 `company.catalyst` | **12 天** |
| `C-2023-COMM-OPTICAL`（信息通信 · 光模块） | 2023-03-21 `industry.trigger` | 2023-05-24 `company.catalyst` | **64 天** |
| `C-2019-PHARMA-INNOV`（医药健康 · 创新药） | 2019-07-22 `policy.trigger` | 2019-11-28 `policy.catalyst` | **129 天** |
| `C-2019-COMM-5G`（信息通信 · 5G） | 2019-06-06 `policy.trigger` | 2019-10-31 `policy.catalyst` | **147 天** |

**必须由 Research 单独验证**（本轮不展开）：是否存在更多同类案例 · 是否跨 Macro Theme ·
是否处于不同生命周期阶段 · 是否存在明显机制差异 · 间隔是否稳定到足以成为**可观察结构**。

> ⚠️ **不得**把上述 4 个样本解释为已形成规律。

### 已记录的候选后续项（**未排期**）

| 类型 | 项 |
|---|---|
| POLISH | `themeCycleId` 内部 id 可读性（如 `auto_intelligence_2023`）· 归因自由文本内嵌 Research id（`EV-*` / `S-*` / `E-*`） |
| POLISH | `event_type`（`company`）与证据类别标签（「产业（INDUSTRY）」）的行内对应关系未呈现 |
| DEFER | SA 默认折叠使唯一 STRICT 对应位于第 9 位（**修复需引入排序 = 禁止**） |
| DEFER | `event_structure` 区分度低 · Driver `MATCH = 1/85`（Research Quality Backlog） |
| DEFER | `campaign_date_observations verified = 0/24`（Future Data Precision Debt） |

### 已确认无风险

- `stale` 阈值 = **14 天**（`SNAPSHOT_STALE_THRESHOLD_DAYS`）；0–14 天属正常研究节奏，不提示滞后
- `historicalEvidenceTimelineOf()` 的 `date|name` 稳定键：**32 campaigns / 106 events / 0 冲突** → 无需升级为 `event_id`

### 边界

- 不新增 Product 功能 / 不新增 Dashboard
- 不改 Research 规则（Rule Set v0.2）· 不改 Artifact · 不改 schema / export / 历史数据
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
