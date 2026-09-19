# STRUCTURAL_ANALOGY_CONTEXT.md

> **只读说明文件。** 说明 Research 结果**未来**会如何被使用。
> 目的：让 Research Worker 知道自己的产出**下游去哪**，从而**不越界**。

- **source_threec_commit**: `2153f6d83b7481300696ab73d792e9e53aa31a07`

---

## 1. Research 结果未来会用于 Structural Analogy

ThreeC 的最终产品链路中，历史研究会进入 **Structural Analogy**：

```text
Research 产出（本 Workspace）
        ↓
Canonical SQLite（ThreeC Agent 写入）
        ↓
Export（exports/timeline_export_v1.json）
        ↓
Structural Analogy
        ↓
Product（Current Time Lens）
```

**Structural Analogy 回答的问题是**：

> 「**当前**结构与**历史**结构存在哪些**可解释的对应**与**不对应**？为什么？」

它比较的维度是：

| 维度 | 说明 |
|---|---|
| **Lifecycle** | 当前阶段 vs 历史在可比观测点的阶段 |
| **Mechanism Driver** | 驱动机制是否**核心等价**（如 `POLICY_DRIVEN` + `TECH_BREAKTHROUGH`） |
| **Evidence Sequence** | 证据顺序是否可比 |
| **Event Structure** | 事件结构是否对应（单一类型主导 vs 多类型带时序） |

---

## 2. ★ Research Worker **不执行** Structural Analogy

| 禁止 | 说明 |
|---|---|
| ❌ 不执行 Structural Analogy | 那是 Research 侧**下游**的独立步骤，有冻结的 Rule Set |
| ❌ 不调整 Structural Analogy Rule Set | 当前冻结版本 = **v0.2**，本 Workspace **无权**修改 |
| ❌ 不生成 Structural Analogy status | 不要产出 `STRUCTURAL_SUPPORTED` / `NO_VALID_CORRESPONDENCE` 一类结论 |
| ❌ **不为了提高 `STRUCTURAL_SUPPORTED` 数量而研究** | 这是**被明确禁止的动机** |

> **结构对应是「被发现」的，不是「被制造」的。**

---

## 3. 为什么不禁止「提高数量」

因为那会**反向扭曲研究**：Worker 会倾向于只提交「看起来能对上」的案例，
从而破坏 `exclusions` 的诚实性，并让「**没有对应**」这个同样有价值的结论消失。

### 当前基线（供参考，**不是目标**）

| 项 | 值 |
|---|---:|
| 历史对象 | 17 |
| 比较对数 | 85 |
| `STRUCTURAL_SUPPORTED` | 4 |
| └ 其中 STRICT | **1** |
| `STRUCTURAL_PARTIAL` | 36 |
| `THEME_ONLY` | 3 |
| `INSUFFICIENT_EVIDENCE` | 5 |
| `NO_VALID_CORRESPONDENCE` | 37 |

> `NO_VALID_CORRESPONDENCE` 占 43.5% —— 这是**正常且必要**的。
> 一个「**哪里都不像**」的诚实结论，比一个勉强的对应更有价值。

---

## 4. Research Worker 该做什么

**只做一件事**：把「历史上真实发生过什么」研究清楚，并**如实记录**：

- 真实的 Campaign（以及**真实的非 Campaign**，写入 `exclusions`）
- 真实的 Evidence（区分 `supporting` / `contradicting` / `context`）
- 真实的 Lifecycle 与 Drivers
- 真实的冲突（**保留双方，不自动取舍**）

**下游如何使用，由 ThreeC Agent 与 Structural Analogy 决定。**

---

## 5. 冻结版本说明

Structural Analogy 当前冻结基线（**本 Workspace 不得修改**）：

- Rule Set：`structural-analogy-ruleset-v0.2`
  （`research/research/methodology/structural_analogy_rule_set_v0_2.md`）
- Research baseline：`Structural Analogy Research v0.2`
- Explanation Artifact：`v0.2`

> 这些是 ThreeC 侧资产。本 Workspace 中**没有**它们的副本 ——
> Worker **不需要**、也**不应该**接触它们。
