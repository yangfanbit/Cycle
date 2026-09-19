# ROADMAP.md — ThreeC 当前路线

> **路线图只描述未来，不重复历史实施细节。**
> 历史版本与每次 commit 的细节见 `docs/CHANGELOG.md`。

## A. 已经完成的基础

### Research Foundation
- Research Model v1.0 Frozen
- Historical Data Production
- Theme / Campaign / Sub-theme 分层
- CMTR v1
- Evidence / Lifecycle / Driver 基础设施

### Product Foundation
- Timeline MVP
- Current Time Lens
- Calendar Lens
- Lifecycle Lens
- Current Candidate
- Preview / Production 隔离
- PWA / static runtime

### Research Core
- Current Research Discovery
- Time Observation v0.5
- Structural Analogy Feasibility
- Driver Canonicalization
- Structural Analogy Robustness
- Structural Analogy Rule Calibration v0.2
- **Structural Analogy Research v0.2 baseline**

---

# B. 当前阶段：Research → Product Architecture

## Step 1 · Product Similarity Architecture Review v0.1

**目标：** 统一三个比较系统的职责，避免产品出现三套“相似度”。

必须回答：

- Calendar vs Lifecycle vs Structural Analogy 的边界
- `currentSimilarity.ts` 的去留
- `historicalSimilarPhase.ts` 的长期定位
- Structural Analogy 的产品入口
- Driver 层级语义
- uncertainty / evidence / explanation 展示方式
- OpportunityRadar legacy 处理

**输出：** 一份稳定的产品比较架构，而不是代码。

---

## Step 2 · Structural Analogy Explanation Artifact

把 Research v0.2 的结果转成**产品可消费、但仍然 research-derived** 的 Artifact。

建议最小信息：

- candidate
- historical cycle
- structural status
- theme relation（metadata）
- D1 Lifecycle
- D2 Driver
- D3 Evidence Sequence
- D4 Event Structure
- supported dimensions
- unsupported / unknown dimensions
- why similar
- why not similar
- provenance
- snapshot / rule-set version

原则：

> Product 不重新实现 Structural Analogy 规则，只消费 Research 结果。

---

## Step 3 · Product Adapter

建立：

`Research Structural Analogy Artifact → Product View Model`

要求：

- 无 ranking / score
- 不猜测 UNKNOWN / NOT_AVAILABLE
- 保留 evidence provenance
- 能稳定导航至历史 Campaign
- 不破坏现有 Timeline / Calendar / Lifecycle

---

## Step 4 · Product UI Integration

优先进入：

**Current Time Lens / Current Candidate**

而不是新建一个孤立“大页面”。

产品层次建议：

`Current Candidate → Structural Analogy → Historical Case`

用户看到：

> 当前研究对象  
> → 历史结构对应  
> → 为什么类似  
> → 哪里不同 / 哪些未知  
> → 查看完整历史案例

---

## Step 5 · User Experience Review

真实使用 Review：

- 5 秒是否理解今天在哪里
- 30 秒是否找到研究入口
- 2 分钟是否完成一次历史结构比较
- 信息密度是否过高
- 是否把“历史对应”误读成预测
- 移动端是否仍然可读

---

# C. Parallel Quality Backlog

这些事情重要，但当前不是主线 blocker：

### Historical Fact Verification
`campaign_date_observations 24 行，当前 verified 0/24`

### Driver Evidence Depth
当前 Structural Analogy 最大瓶颈：

- Driver MATCH 1/85
- MULTI_MECHANISM 4

后续可围绕 driving phase 补 DIRECT evidence，但**不得为了提高 supported 数量而补证据**。

### Market / Temporal Context
目前仍：

**SUPPLEMENTARY_ONLY**

不进入 Structural Status。

### Coverage Expansion
Wave 1C：

**暂停。**

只有新的研究问题明确证明需要，才重新开启。

---

# D. 明确不走的路线

- 不继续为了 Pattern 数量扩 Time Observation
- 不为了提高 Structural SUPPORTED 数量放松规则
- 不新增 Theme Cycle / schema 实体
- 不做分数榜 / 相似度百分比 / 概率 / 胜率
- 不把 Structural Analogy 变成预测器
- 不做实时行情、资金流、通知、后台
- 不做新的 Dashboard / Radar，除非新的 Product Review 证明必要

---

# E. 产品最终目标

ThreeC 最终不是“多功能投资工具”。

它应该收敛成一个非常清晰的工作流：

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

核心问题始终只有一个：

> **今天看到一个方向时，能不能快速找到真正值得对照的历史结构，并且知道为什么。**
