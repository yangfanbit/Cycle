# PRODUCT_SIMILARITY_ARCHITECTURE_REVIEW.md — v0.1 Baseline

> 日期：2026-09-19
> 性质：Product architecture review。**不改代码、不改 schema、不改 export。**

## 1. Review 问题

ThreeC 现在已经有三个“相似 / 对照”实现：

1. `currentSimilarity.ts`
2. `historicalSimilarPhase.ts`
3. Structural Analogy Research v0.2

如果直接把第三套接入 Product，就会出现三个模块同时回答“历史上有什么类似”，用户无法理解差异。

---

## 2. 三者应承担的不同问题

| 能力 | 应回答的问题 | 建议定位 |
|---|---|---|
| Calendar Lens | 这个时间附近历史上发生过什么？ | 时间邻近浏览 |
| Lifecycle Lens | 历史上谁处于类似生命周期阶段？ | 历史阶段浏览 |
| Structural Analogy | 当前结构与历史结构在哪些维度对应？ | **正式结构对应** |

这三个概念应当并列存在，但**不应共用“相似度”作为产品名称**。

---

## 3. Structural Analogy 应成为正式 Current → Historical Correspondence

未来 Product 中：

```
Current Candidate
   ↓
Structural Analogy
   ↓
Historical Cases
```

Research 是唯一规则来源：

- D1 Lifecycle
- D2 Mechanism Driver
- D3 Evidence Sequence
- D4 Event Structure
- Theme Relation 仅 metadata

Product 不再次计算上述规则。

---

## 4. currentSimilarity.ts 的建议

当前实现有自己的内部权重、score、tier。

这与 Research Structural Analogy v0.2 的离散状态体系存在概念重叠。

**建议：暂不删除，但停止继续扩展。**

后续处理顺序：

1. Product Architecture Review 完成
2. 建立 Structural Analogy Product Artifact
3. 用真实 UI 需要验证两者重叠程度
4. 再决定：
   - 兼容保留
   - 改造成 thin adapter
   - 废弃

目前**不要同时维护两套新的 Current → Historical 算法**。

---

## 5. historicalSimilarPhase.ts 的建议

建议长期保留为 **Lifecycle Lens**。

它回答的是：

> “历史上处于类似生命周期位置的案例有哪些？”

这是 Structural Analogy 的一个子维度，但并不等价于完整结构对应。

因此：

- Lifecycle Lens = 浏览工具
- Structural Analogy = 研究对应工具

两者可以共存。

---

## 6. Driver 必须分层命名

当前存在：

### Evidence Category

`POLICY / INDUSTRY / CAPITAL / SENTIMENT / EXTERNAL`

### Mechanism Driver

`POLICY_DRIVEN / INDUSTRY_UPGRADE / TECH_BREAKTHROUGH / DEMAND_SURGE / ...`

以后产品文案不要都简称 “Driver”。

建议使用：

- **证据类别**
- **驱动机制**

这样用户才能理解：

> “公司公告”是一类证据来源；
> “产业升级”是一个机制判断。

两者不是同一维。

---

## 7. Structural Analogy Product Artifact

建议后续新增一个 **research-derived、Product-facing** Artifact。

最小字段：

```
candidate_id
historical_campaign_id
snapshot_date
rule_set_version
structural_status
theme_relation
dimensions:
  lifecycle
  mechanism_driver
  evidence_sequence
  event_structure
supported_dimensions[]
unknown_dimensions[]
unsupported_dimensions[]
why_similar[]
why_not_similar[]
provenance[]
```

禁止：

- score
- percentage
- probability
- winner
- ranking

Artifact 由 Research 生成，Product 只读。

---

## 8. UI 建议

不要新增一个巨大的“结构相似度 Dashboard”。

优先放进现有 Current Time Lens：

```
当前研究对象
   ↓
历史结构对应
   ↓
为什么对应
   ↓
哪里不同 / 哪些未知
   ↓
查看历史案例
```

这样符合现有产品主线，不破坏 Timeline 第一视觉。

---

## 9. OpportunityRadar

当前 `OpportunityRadar` 没有接入 `App.tsx`，且逻辑仍是经验规则日历提醒。

建议状态：

**LEGACY / DEPRECATED FOR NEW USE**

暂不立即删除，避免在架构决策未完成时产生无意义的大清理。

最终方向：

- 删除旧 Radar；或
- 若未来重新设计，也必须由 Research-derived historical context 驱动，而不是旧经验规则日历。

---

## 10. 未决事项

下一轮 Product Architecture Review / Artifact Design 必须正式决定：

1. Structural Analogy Artifact 的精确结构
2. currentSimilarity 的最终去留
3. Lifecycle Lens 的导航关系
4. Driver 的中文/英文产品词汇
5. unknown / not_available 的 UI 表达
6. 多个历史对应案例如何展示
7. performance 与移动端交互

---

## 11. 本轮结论

**现在不应该继续增加“相似度算法”。**

应该做的是：

> **把已经完成的 Structural Analogy Research v0.2 变成 Product 唯一正式的 Current → Historical Structural Correspondence 能力，同时保留 Calendar 与 Lifecycle 作为两个不同的浏览视角。**

这就是当前 Research → Product 的最短路径。
