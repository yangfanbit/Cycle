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
- **Structural Analogy Rule Set v0.2**
- **Structural Analogy Research v0.2**
- **Structural Analogy Explanation Artifact v0.1**

### Product
- Timeline
- Current Time Lens
- Calendar Lens
- Lifecycle Lens
- Current Candidate
- Preview / Production isolation
- Static PWA runtime

## 2. 当前主线：Research → Product

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

**当前进行中。**

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

### Driver Evidence Depth

当前最大 Research 质量债：
- Driver MATCH = 1/85
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
