# ARCHITECTURE.md — ThreeC 当前实际架构

> 本文只描述当前真实架构与已知架构债务。未来路线见 `docs/ROADMAP.md`。

## 1. 系统边界

```
ThreeC
├─ Product（src/）
│   ├─ Timeline
│   ├─ Current Time Lens
│   ├─ Calendar Lens
│   ├─ Lifecycle Lens
│   └─ Current Candidate View
│
├─ Research（research/）
│   ├─ SQLite / Evidence / Lifecycle / Drivers
│   ├─ Current Candidate dataset
│   ├─ Time Observation artifacts
│   └─ Structural Analogy research artifacts
│
├─ exports/
│   └─ timeline_export_v1.json   ← canonical v1.0
│
└─ contracts/
    └─ timeline_export_v1.md
```

Research 和 Product 是**两个逻辑层、一个项目**。

Product runtime：
- 无后端
- 无运行时网络
- 无 LLM
- 静态数据消费

---

## 2. Product 数据流

### Historical

```
Research DB
   ↓
timeline_export_v1.json
   ↓
timelineAdapter
   ↓
TimelineDataSource
   ↓
Timeline / Calendar / Lifecycle
```

### Current Candidate

```
research/current/current_candidates.json
   ↓
currentCandidate parser
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

当前已经存在：

```
Current Candidate
   +
Historical Cycle
   ↓
Structural Analogy Research v0.2
```

但目前仍属于 **Research-only**：

> **尚无 Product Artifact / Product Adapter。**

这是下一阶段要解决的核心架构缺口。

---

## 3. 当前 Product 比较视角

### Timeline
历史主体。第一视觉。

### Calendar Lens
回答：

> 这个时间附近，历史上发生过什么？

数据入口主要来自 `timeline_export_v1.json`。

### Lifecycle Lens
回答：

> 历史上处于类似生命周期位置的案例有哪些？

对应：
`historicalSimilarPhase.ts`

### Current Candidate Similarity
对应：
`currentSimilarity.ts`

当前回答：

> 当前候选可以参考哪些历史案例？

它使用内部 score / tier，但数字不直接展示。

### Structural Analogy
Research 正式回答：

> 当前结构与历史结构在哪些维度上存在对应？哪里没有？

规则：
- Lifecycle
- Driver / Mechanism
- Evidence Sequence
- Event Structure

这一层是未来产品中**唯一正式的 Current → Historical Structural Correspondence**能力。

---

## 4. 当前已知架构债务

### Debt 1 · 三套相似体系

`currentSimilarity.ts`、`historicalSimilarPhase.ts`、Structural Analogy Research v0.2

三者不能长期并列为三个“相似度”。

目标是：

- Calendar = 时间邻近
- Lifecycle = 生命周期浏览
- Structural Analogy = 正式结构对应

`currentSimilarity.ts` 最终需要决定保留为兼容层、重构或废弃。

### Debt 2 · Driver 双层语义

Product：

`POLICY / INDUSTRY / CAPITAL / SENTIMENT / EXTERNAL`

Research：

`POLICY_DRIVEN / INDUSTRY_UPGRADE / TECH_BREAKTHROUGH / DEMAND_SURGE / ...`

必须命名区分：

> **Evidence Category ≠ Mechanism Driver**

### Debt 3 · OpportunityRadar

`src/components/OpportunityRadar/` 仍存在，但当前 `App.tsx` 不接入。

它的原始逻辑是经验规则日历提醒，不属于当前 Research Core。

状态：

**LEGACY / DEFER REMOVAL**

等待 Product Similarity Architecture Review 后统一决定删除或彻底转型。

### Debt 4 · 文档与代码漂移风险

动态状态不再写在 AGENTS。

固定规则 → AGENTS  
当前状态 → PROJECT_STATE  
未来计划 → ROADMAP  
历史记录 → CHANGELOG

这是新的文档职责划分。

---

## 5. Structural Analogy 的未来 Product 边界

推荐数据流：

```
Structural Analogy Research
        ↓
Product-facing Research Artifact
        ↓
Product Adapter
        ↓
Current Candidate / Current Time Lens
        ↓
Historical Campaign Detail
```

Product 不重新实现：
- level_v2()
- Theme Relation 判定
- Driver matching
- Evidence Sequence matching
- Event Structure matching

Product 只消费 Research 的结果，并负责：
- 表达
- 导航
- uncertainty
- provenance
- interaction

---

## 6. 当前原则

不要为了“统一代码结构”做大重构。

优先顺序：

1. 先统一语义
2. 再统一 Artifact
3. 再统一 Adapter
4. 最后处理旧模块与 UI

这样可以避免一次大规模 Product Rewrite。

