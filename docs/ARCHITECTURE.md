# ARCHITECTURE.md — ThreeC 当前实际架构

> 描述当前真实结构与已知架构债务；未来路线见 `docs/ROADMAP.md`。

## 1. System Boundary

```
ThreeC
├─ Product（src/）
│  ├─ Timeline
│  ├─ Current Time Lens
│  │  └─ Current Candidate
│  ├─ Lifecycle Lens
│  └─ Calendar Lens
│
├─ Research（research/）
│  ├─ Historical DB
│  ├─ Current Candidate Dataset
│  ├─ Time Observation artifacts
│  ├─ Structural Analogy Research
│  └─ Structural Analogy Explanation Artifact
│
├─ exports/
│  └─ timeline_export_v1.json
│
└─ contracts/
   └─ timeline_export_v1.md
```

## 2. Data Flow

### Historical Product

```
Research DB
  ↓
timeline_export_v1.json
  ↓
timelineAdapter
  ↓
Timeline / Calendar / Lifecycle
```

### Current Candidate

```
research/current/current_candidates.json
  ↓
currentCandidate
  ↓
currentEvidence
  ↓
currentPhaseInference
  ↓
currentSimilarity
  ↓
CurrentCandidateView
  ↓
Current Time Lens
```

### Structural Analogy

```
current_candidates
  +
historical research
  ↓
Structural Analogy Research v0.2
  ↓
Explanation Artifact v0.1
  ↓
[下一步：Architecture Gate]
  ↓
Product Adapter
  ↓
Current Candidate / Current Time Lens
```

## 3. Product Comparison Taxonomy

| 视角 | 核心问题 | 性质 |
|---|---|---|
| Calendar Lens | 这个时间附近历史上发生过什么？ | 时间邻近浏览 |
| Lifecycle Lens | 历史上谁处于类似生命周期阶段？ | 历史阶段浏览 |
| Structural Analogy | 当前结构与历史结构在哪些维度对应？ | 正式结构对应 |

这三个视角可以共存，但不应都叫“相似度”。

## 4. Existing Comparison Implementations

### A. currentSimilarity.ts

当前是：

**Current Candidate × Historical**

使用：
- Lifecycle
- Theme Cycle Pattern
- Evidence Category / Driver Profile
- Narrative Structure
- 内部 score / tier
- 最多 3 个结果

问题：

> 它与 Structural Analogy 的输入关系和目标问题高度重叠，但判定体系不同。

当前政策：

**停止继续扩展，等待 Architecture Gate 决定长期去留。**

### B. historicalSimilarPhase.ts

当前是：

**Historical × Historical**

使用 Lifecycle / Pattern / Driver 分类。

长期建议：

**保留为 Lifecycle Lens**，但 Gate 需要正式确认其 API / UI 边界。

### C. Structural Analogy

当前是：

**Current Candidate × Historical Cycle**

Research 正式规则：
- D1 Lifecycle
- D2 Mechanism Driver
- D3 Evidence Sequence
- D4 Event Structure
- Theme Relation = metadata

它是未来 Product 唯一正式的：

**Current → Historical Structural Correspondence**

Product 不重新实现其规则。

## 5. Step 2 Artifact 的接口风险

当前 `structural_analogy_explanations_v0_1.json` 可复现，但在 Adapter 前需要 QA：

### 5.1 WHY NOT

`CROSS_MACRO_THEME` 被写入 `why_not_similar` 的当前实现容易造成错误语义。

正确原则：

> 跨主题不是“不相似”的依据；它只能作为背景 metadata。

### 5.2 Ordering

当前 explanations 按 structural status → cycle id 排列。

虽然实现声明“不是 ranking”，但 Product 很容易把数组顺序理解成“从强到弱”。

Adapter 前建议改为：

> **不按 structural status 排序；只保留稳定 identity 顺序。**

### 5.3 Identity

当前同时存在：
- `historical_cycle_id`
- `historical_campaign_id`
- `historical_kind`

而 17 个历史对象中包含 Research Candidate。

因此 Adapter 前应正式区分：
- historical cycle identity
- campaign identity（可为空）
- research candidate identity（如适用）

不得让 `historical_campaign_id` 成为“所有历史对象”的总身份。

### 5.4 Provenance

当前 provenance 有三类来源：

- candidate evidence
- historical driver evidence
- historical events

Adapter 前应明确：

> 哪些 provenance 是某个维度的直接依据；哪些只是背景来源。

不要让 Product 对同一组 provenance 做因果推断。

## 6. Driver 层级

必须长期区分：

**证据类别 / Evidence Category**

与

**驱动机制 / Mechanism Driver**

不要在 Product 文案中都叫 Driver。

## 7. Product Layer 约束

Product：
- 不重新计算 Structural Analogy
- 不产生新的研究结论
- 不把 UNKNOWN 当成 NO
- 不把 PARTIAL 当成 MATCH
- 不把 Theme Relation 变成等级因素
- 不生成 score / ranking / probability
- 不联网

## 8. OpportunityRadar

当前未接入 App 主流程。

状态：

**LEGACY / DEFER**

Architecture Gate 后决定删除或保留为历史代码；本轮不删除。
