# USAGE_TEST_2026-10-07_PHARMA.md

> | 项目 | 值 |
> |---|---|
> | 性质 | **真实使用测试报告**（ThreeC 1.2 · Usage-Driven） |
> | 日期 | 2026-10-07 |
> | 测试方向 | **医药健康**（用户指定） |
> | 测试问题 | 「**脑机接口医疗器械现在处于什么阶段？历史上有没有结构类似的？**」 |
> | 结论 | ✅ **工具确实能产出有价值的研究结论** —— 但 ❌ **路径断了，用户看不到** |

---

## 1. 逐段走一遍「最终工作流」（ROADMAP §5）

| 段 | 实测结果 | 判定 |
|---|---|---|
| 今天 | 首页 Today 线；`market_regime` 显示宽基 `DOWN` / 流动性 `STABLE` | ✅ |
| 历史同期 | Calendar Lens 可用 | ✅ |
| 历史周期阶段 | Lifecycle Lens 可用 | ✅ |
| **当前研究对象** | `CC-2026-BCI-MEDTECH`，阶段 `THEME_FORMING`，大主题 医药健康 | ✅ |
| **历史结构对应** | 数据里有 **9 条有效对应**（1 SUPPORTED + 7 PARTIAL + 1 THEME_ONLY） | ⚠️ **只在 SA 区块可见** |
| **为什么对应 / 哪里不同** | SA 给出逐维度的 `why_similar` / `why_not_similar`，**内容非常具体** | ⚠️ **同上，快照页没有出口** |
| **继续研究** | `research_questions` 在 CurrentTimeLens 里 | ⚠️ **不在快照页** |

## 2. ★★ 工具实际给出的结论（这才是价值所在）

**问：脑机接口医疗器械历史上有结构类似的吗？**

| 历史对象 | 结构状态 | 大主题关系 | 机制轴 |
|---|---|---|---|
| **`C-2023-AD`（智能驾驶/无人驾驶）** | **`STRUCTURAL_SUPPORTED`** | **跨大主题** | **`MATCH` · `CORE_EQUIVALENT`** |
| `C-2019-COMM-5G`（5G 网络建设） | `STRUCTURAL_PARTIAL` | 跨大主题 | PARTIAL |
| `C-2019-MIL-GROUP-RESTRUCTURE`（军工重组） | `STRUCTURAL_PARTIAL` | 跨大主题 | PARTIAL |
| `C-2020-POWER-NE`（光伏/新能源发电） | `STRUCTURAL_PARTIAL` | 跨大主题 | PARTIAL |
| `C-2020-RE-DEBT-RISK`（地产债务） | `STRUCTURAL_PARTIAL` | 跨大主题 | PARTIAL |
| `C-2022-POLICY`（购置税刺激） | `STRUCTURAL_PARTIAL` | 跨大主题 | PARTIAL |
| `C-2022-RE-POLICY-THREE`（地产三支箭） | `STRUCTURAL_PARTIAL` | 跨大主题 | PARTIAL |
| `C-2023-HIEQ-HUMANOID`（人形机器人） | `STRUCTURAL_PARTIAL` | 跨大主题 | PARTIAL |
| **`C-2019-PHARMA-INNOV`（创新药/CXO）** | **`THEME_ONLY`** | **同大主题** | **`MISMATCH`（无交集）** |

### ★ 这张表本身就是「研究结论」

1. **唯一的结构支持来自「智能驾驶」** —— 一个**完全不同的大主题**。
   两者共享 `POLICY_DRIVEN + TECH_BREAKTHROUGH`（`CORE_EQUIVALENT`），且生命周期阶段相同（均 `THEME_FORMING`）。
2. **同大主题的「创新药」反而只是「仅主题相同」** —— 生命周期阶段相同，但**机制轴完全无交集**。
3. 即：**「名字像」的不像，「看起来不像」的才像。**

> ★★ 这**正是 ThreeC 的立身之论在真实数据上的验证**：
> `Theme / Name 相似 ≠ Structural Correspondence`。
> 一个只做主题名匹配的工具，会给出**完全相反**的答案。

### 工具同时诚实标注了不知道的部分

- `structural_gaps`：`candidate_side_2026_market_state_not_available`、`phase_window_end_unknown`
- `market_status` / `temporal_status`：`SUPPLEMENTARY_ONLY`（**不参与**结构判定）
- 每条的 `why_not_similar` 都写明限制（如「受历史驱动证据粒度与事件覆盖限制」）

## 3. ★ 卡在哪（这才是本轮测试的真正产出）

**数据层完全够用，产品层没接通。**

- 快照页对 `CC-2026-BCI-MEDTECH` 显示的是：
  > 「共 79 条比对 · 有结构对应 **8** 条 · 无有效对应 **47** 条」

  **然后就没有了** —— 用户看不到是哪 8 条、为什么、哪条最强。
- 而上述那张表的内容，**全部已经在包里**（冻结 SA v0.5 的 `explanations[]`），
  只是**没有任何出口**（`CurrentSnapshotSection.tsx` 实测：0 个 `onClick` / `href` / `<button>`）。
- 用户若想看到它，必须**自己知道**去另一个钻取区（Current Time Lens）→ 选中该对象 → 找到 SA 区块。
  **一个不知道产品结构的人不可能走通。**

**这不是「缺功能」，是「已有的东西没连上」。**

## 4. 结论与下一步

| # | 结论 |
|---|---|
| 1 | **工具能产出有价值的研究结论** —— 且是**非显然、跨主题**的那种。**值得继续投入。** |
| 2 | **最大的实用缺口是「接通」** —— 数据在、解释在、没有出口。**P0 判断被实测证实。** |
| 3 | 「无有效对应」（47 条）也应可查 —— 现在同样只是一个数字。**「为什么不对应」与「为什么对应」同等重要。** |
| 4 | 覆盖边界问题（传媒/文化不在覆盖内）是**另一个维度**的问题，不冲突。 |

**建议**：立即做 P0 —— **把快照页的历史候选从「计数」变成「可看的明细」**
（对象 → SA 详情；候选 → 具体历史对象 + 为什么对应/不对应）。

---

*使用测试报告 · 2026-10-07 · 测试方向由用户指定（医药健康）*
