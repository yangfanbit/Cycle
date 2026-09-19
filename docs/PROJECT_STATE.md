# PROJECT_STATE.md — ThreeC 当前真实状态

> **动态接班文档。** 本文件只回答“现在是什么状态、哪里有问题、下一步做什么”。
> 历史细节进入 CHANGELOG；长期规则进入 AGENTS。

- **更新日期**：2026-09-19
- **HEAD**：`0e19cff`
- **branch**：`main`
- **ahead / behind**：`0 / 0`
- **working tree**：clean
- **最近完成**：Structural Analogy Research v0.2

---

## 1. 项目一句话

**ThreeC = A股历史机会时间轴 / 历史机会地图。**

核心价值不是预测，而是：

> **从历史周期里找结构，而不是去历史数据里找同名主题。**

---

## 2. 当前总阶段

### Research Core：已完成第一版闭环

`Historical Model → Historical Data → Time Observation → Current Research → Structural Analogy`

现在已经完成：

- Structural Analogy Rule Set v0.2 冻结
- Structural Analogy Research v0.2 baseline
- Time Observation Discovery v0.5
- Macro Theme Canonicalization
- Driver Canonicalization
- Robustness / Feasibility / Readiness

### Product Core：已有骨架，但没有消费最新 Structural Analogy

当前 Product 已有：

`Timeline → Current Time Lens → Lifecycle Lens → Calendar Lens`

另有 Current Candidate UI。

**Structural Analogy 尚未进入 Product。**

---

## 3. Research 当前基线

### Historical Data

当前 DB 实测：

| 表 | 行数 |
|---|---:|
| campaigns | 13 |
| themes | 19 |
| campaign_themes | 31 |
| campaign_phases | 48 |
| campaign_date_observations | 24 |
| evidences | 83 |
| events | 49 |
| market_series | 56 |
| market_daily | 79,466 |
| trading_calendar | 371 |
| sources | 85 |

Macro Theme roots：

- TH-AUTO · 汽车
- TH-PHARMA · 医药健康
- TH-POWER · 电力设备
- TH-COMM · 信息通信

历史主题族样本目前仍然不均衡：

- AUTO = 9
- PHARMA = 3
- POWER = 2
- COMM = 2

日期核验：

- `campaign_date_observations = 24`
- `verified_date = 0 / 24`

这属于可信度债务，不再作为当前 Structural Analogy 的阻塞条件。

---

## 4. Time Observation v0.5

四族数据首次完整重跑：

- Raw candidates = **315**
- distinct samples = **139**
- `N ≥ 5` = **34**
- independent robust structures = **1**
- TOP-01：`N=7` · center=`06-11` · window=`05-27~06-26` · recurrence=`5/7`
- cross-family robust structures = **0**

结论：

> **Time Observation 暂时冻结。**

不再为了增加 Pattern 数量继续扩容或放宽标准。

---

## 5. Structural Analogy v0.2

Protocol：

`structural-analogy-ruleset-v0.2`

规则已冻结，研究执行基线已建立。

### Core Result

| 状态 | 数量 |
|---|---:|
| STRICT_STRUCTURAL_SUPPORTED | 1 |
| STRUCTURAL_SUPPORTED | 4 |
| STRUCTURAL_PARTIAL | 36 |
| THEME_ONLY | 3 |
| INSUFFICIENT_EVIDENCE | 5 |
| NO_VALID_CORRESPONDENCE | 37 |

比较规模：

- Current candidates = **5**
- Historical cycles = **17**
- Pairs = **85**

Cross-family：

- SUPPORTED = **3**
- same-family SUPPORTED = **1**

Controls：

- Name-blind changed = **0**
- Theme-blind structural status changed = **0**
- name-similarity negative control = PASS
- same-theme negative control = PASS

最大研究瓶颈：

> **机制级 Driver 证据深度**，不是 vocabulary。

当前：
- Driver MATCH = 1 / 85
- MULTI_MECHANISM = 4
- Evidence Sequence NOT_AVAILABLE = 30 / 85

因此后续不应再优先“调算法”，而应把注意力转向**证据深度与产品解释**。

---

## 6. 当前真正存在的 Product Architecture Debt

### A. 有三套“相似”体系

1. `currentSimilarity.ts`
   - Current Candidate × Historical
   - 内部 score / tier
   - 当前 Product 用于候选历史参照

2. `historicalSimilarPhase.ts`
   - Historical × Historical
   - Lifecycle Lens
   - 按阶段 / Pattern / Driver 找历史相似阶段

3. Structural Analogy Research v0.2
   - Current Candidate × Historical Cycle
   - Lifecycle / Driver / Evidence Sequence / Event Structure
   - **研究正式规则**
   - 不以 score / ranking 定义结果

**不能直接把三套并列放进产品。**
必须重新划清职责。

### B. Driver 语义有两层

Product 当前 Candidate Driver：

`POLICY / INDUSTRY / CAPITAL / SENTIMENT / EXTERNAL`

Structural Analogy Driver：

`POLICY_DRIVEN / INDUSTRY_UPGRADE / TECH_BREAKTHROUGH / DEMAND_SURGE / ...`

前者更接近“证据类别”，后者是“机制类别”。

以后不能继续都叫同一个 Driver 而不解释层级。

### C. OpportunityRadar 已不属于当前 App 主流程

`src/components/OpportunityRadar/` 仍存在，但当前 `App.tsx` 已不接入。

其逻辑仍主要是“经验规则日历提醒”，与当前 Research Core 不一致。

**暂不删除，标记为 legacy，待 Product Architecture Review 后统一处理。**

### D. 文档曾明显滞后

本轮已同步：

- AGENTS
- PROJECT_STATE
- ROADMAP
- ARCHITECTURE
- README

以后不再把动态状态重复塞进 AGENTS。

---

## 7. 当前产品真实架构

```
Research
  │
  ├─ Historical DB / Evidence / Lifecycle / Drivers
  ├─ Current Candidate Dataset
  ├─ Time Observation Artifacts
  └─ Structural Analogy Research
          │
          └──（目前尚未进入 Product Artifact）

Canonical Export v1
          │
          ▼
Product Adapter
          │
          ├─ Timeline
          ├─ Current Time Lens
          ├─ Calendar Lens
          └─ Lifecycle Lens
```

### Product 侧原则

- Timeline 是第一视觉。
- Calendar / Lifecycle / Structural 三种“比较视角”必须正交。
- Research 结论应通过 Artifact + Adapter 进入 Product，而不是在 React 里重新实现研究规则。
- Product runtime 不联网。

---

## 8. 当前唯一下一目标

# Product Similarity Architecture Review v0.1

目标不是写 UI，而是回答：

1. `currentSimilarity.ts` 是否保留、降级还是最终废弃？
2. `historicalSimilarPhase.ts` 是否作为独立 Lifecycle Lens 长期保留？
3. Structural Analogy 如何成为**唯一正式的 Current → Historical Structural Correspondence**能力？
4. Product 应消费什么 Research Artifact？
5. Driver “证据类别”与“机制类别”如何命名和分层？
6. 如何展示 MATCH / PARTIAL / MISMATCH / UNKNOWN / NOT_AVAILABLE，而不变成分数榜？
7. 如何把“为什么类似”和“哪里不类似”放入产品？
8. OpportunityRadar 是否正式 deprecated / 删除？
9. Product Performance / interaction / uncertainty 怎么处理？

### 本目标的边界

- **先设计，不实现 UI。**
- 不改 schema。
- 不改 export contract v1.0。
- 不把 Structural Analogy 直接写入现有 TimelineCampaign。
- 不新增 score / probability / ranking。
- 不做 Wave 1C。
- 不继续调 Structural Analogy v0.2 规则。

---

## 9. 之后的路线

```
[现在]
Structural Analogy v0.2 baseline
        ↓
[Next]
Product Similarity Architecture Review
        ↓
Structural Analogy Explanation Contract / Artifact
        ↓
Product Adapter
        ↓
Product UI Integration
        ↓
真实用户体验 Review
        ↓
再决定是否补 Driver Evidence / Date Verification
```

Wave 1C 暂停；Time Observation 暂停。

---

## 10. 当前验证基线

已知最近一次全绿：

- Structural Analogy v0.2 `--check` PASS
- Calibration v0.2 PASS
- Robustness PASS
- Feasibility / Readiness PASS
- Time Observation v0.5 PASS
- Research validators 全 PASS
- `npm test` = **395 / 395**
- `tsc -b` = PASS
- `vite build` = PASS

任何下一轮实现都必须先核对实际 HEAD，再执行验证。

