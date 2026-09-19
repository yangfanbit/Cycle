# Historical Universe Coverage Plan v0.1

> **性质**：第一轮 Historical Universe Expansion 的**覆盖方向**（R00 基础设施）。
> **不是**产出目标，**不是** KPI，**不是**「必须完成」清单。
> 配套协议：`HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md`

---

## 1. 当前真实基线（实测）

来源：`research/database/cycle_research.db`（HEAD `2ba94bd`）

| 项 | 值 |
|---|---:|
| Macro Theme 根节点 | **4** |
| themes 行 | 19 |
| Campaign | 13 |
| Structural Analogy 历史对象 | 17 |
| 比较对数 | 85 |
| `STRUCTURAL_SUPPORTED` | 4（其中 **STRICT 1**） |
| `STRUCTURAL_PARTIAL` | 36 |
| `NO_VALID_CORRESPONDENCE` | 37 |

### 1.1 四个已有 Macro Theme

| # | Macro Theme | 已有 Campaign（示例） |
|---|---|---|
| 1 | **汽车** | `C-2019-AD` · `C-2021-NEV` · `C-2023-AD` · `C-2024-V2X` · `C-2024-ROBOTAXI` · `C-2025-ROBOTAXI` |
| 2 | **医药健康** | `C-2019-PHARMA-INNOV` · `RC-2020-PANDEMIC` · `RC-2021-TCM` |
| 3 | **信息通信** | `C-2019-COMM-5G` · `C-2023-COMM-OPTICAL` |
| 4 | **电力设备** | `C-2020-POWER-NE` · `C-2021-NEV` · `C-2022-POWER-GRID` |

### 1.2 瓶颈诊断

> **85 条比较中只有 1 条 STRICT 结构对应 —— 根因不是规则太严，是候选池太窄。**

只有 4 个 Macro Theme 时，「跨 Macro Theme 结构对应」在**结构上**只能落在
`C(4,2) = 6` 个族对组合上。**扩大宇宙的族数，比放宽规则更能提高结构对应的可发现性。**

**明确**：本计划**不为**提高 `STRUCTURAL_SUPPORTED` 数量而扩容（那是被禁止的动机）。
扩容的目的是让**跨族结构对应有足够多的真实候选可比较**，
从而让「**没有对应**」这个结论也更有信息量。

---

## 2. 第一轮覆盖方向

### 2.1 已有（继续补强，不视为已覆盖）

| # | Macro Theme | 补强方向 |
|---|---|---|
| 1 | 汽车 | 已有 6 个 Campaign，**结构覆盖相对最好**；本轮不作为新增重点 |
| 2 | 医药健康 | 仅 1 个 Campaign + 2 个 Research Candidate → **需补强** |
| 3 | 信息通信 | 仅 2 个 Campaign → **需补强** |
| 4 | 电力设备 | 3 个 Campaign → 中等 |

> 一个 Macro Theme「出现过」**不代表**已经形成充分历史覆盖（协议 §1.3 原则 7）。

### 2.2 第一轮新增重点（6 个 family 方向）

| # | Family 方向 | 为什么值得作为独立族 |
|---|---|---|
| 5 | **高端装备 / 机器人** | 与「汽车」「电力设备」机制不同（制造升级 / 产业政策），且已有 `C-2024-ROBOTAXI` 等相邻案例可交叉验证 |
| 6 | **半导体 / 电子** | A 股历史上有多次独立政策 + 国产替代驱动的周期，机制与「信息通信」可分离 |
| 7 | **资源 / 有色 / 化工** | **供给收缩 / 涨价**型机制 —— 当前 4 族**完全没有**此类机制 |
| 8 | **消费** | **需求端**驱动机制 —— 当前 4 族**完全没有** |
| 9 | **金融 / 地产** | **流动性与政策周期**驱动 —— 当前 4 族**完全没有** |
| 10 | **军工** | **订单 / 事件驱动**机制 —— 当前 4 族**完全没有** |

### 2.3 关键判据：**机制多样性**，不是族名数量

当前 4 族的机制集中在：**政策驱动 · 技术突破 · 产业升级 · 需求爆发**。

**完全缺失的机制轴**：

```text
供给收缩（SUPPLY_CONTRACTION）      ← 资源 / 化工
纯需求端驱动（消费）                 ← 消费
流动性 / 政策周期（金融地产）        ← 金融 / 地产
订单 / 事件驱动（军工）              ← 军工
```

> **这四条缺失机制轴，才是本轮扩容真正的目标。**
> 只要新族仍然只产出「政策驱动 + 技术突破」，**结构覆盖没有真正扩大**。

---

## 3. AI / 算力 / 半导体 / 机器人 交叉处理原则

### 3.1 明确警告

以下名称之间存在**明显交叉**：

```text
AI · 算力 · 大模型 · 半导体 · 计算机 · 通信 · 机器人 · 高端装备
```

**严禁**未经判断就把它们**全部**设成新的 Macro Theme。

### 3.2 允许的表达层级

这些名称可以作为：

| 层级 | 示例 |
|---|---|
| **Theme**（子主题） | 「智能驾驶/无人驾驶」挂 `汽车` 下 |
| **子主题** | 「光模块/高速光互联」挂 `信息通信` 下 |
| **Cross-family research candidate** | 一个 Campaign 的 `theme_name_candidates` 跨越两个族 → 交由 CMTR 判定 |
| **Mechanism**（机制轴） | `TECH_BREAKTHROUGH` 是**机制**，不是 Macro Theme |

### 3.3 Macro Theme 必须走 CMTR v1

> **最终 Macro Theme 必须经过 `research/scripts/theme_taxonomy.py`（CMTR v1）。**
> **不得自行发明第二套 Macro Theme Resolution。**

- 唯一事实来源：DB `themes` 表
- 规则集：`canonical-macro-theme-resolution-1`
- 无法解析的名称 → 显式报告（`UNRESOLVED_NAME` / `unmatched_names`），**不静默丢弃**
- 若某新族在 DB `themes` 中**不存在对应根节点** → 这是**数据决策**，
  必须**单独轮次**处理，**不在 R01 内自动新增 taxonomy 行**

### 3.4 交叉情形的处理顺序

```text
1. Research Agent 提交 macro_theme_proposals + theme_name_candidates（原始名称）
        ↓
2. ThreeC Agent 用 CMTR v1 解析
        ↓
3. 若 RESOLVED      → 归入已有根节点
   若 CONFLICT      → 跨族，必须人工判定归属或拆分
   若 UNRESOLVED_NAME → 记录 taxonomy gap（不自动新增）
   若 NO_THEME      → 候选未登记任何主题 → 退回研究侧补主题
```

---

## 4. 时间范围与优先级

| 层级 | 年份 | 性质 | 要求 |
|---|---|---|---|
| **Priority A** | **2018–2025** | 当前主宇宙直接扩容区 | **必须独立可交付** |
| **Priority B** | **2015–2017** | 历史回填区 | 允许大面积 `INSUFFICIENT` |

**硬约束**：

- Research Agent **可以**一次性研究 2015–2025
- **不得**因 2015–2017 资料较难而**阻塞** 2018–2025 的产出
- Priority A 的 package **不得**因为 Priority B 未完成而延后提交

**不建议**在未验证资料质量前扩张到 2015 年之前（当时的概念板块口径、
公开信息可得性、行情数据可得性与 2018 年后**不可比**）。

---

## 5. 什么算「充分覆盖」（判定原则）

**不看数量，看结构多样性。** 一个 family 方向在下列维度上**出现分化**时，
才算开始形成覆盖：

| 维度 | 分化示例 |
|---|---|
| **Mechanism** | 政策驱动 **vs** 供给收缩 **vs** 需求端 |
| **Lifecycle** | 完整走完（形成→主升→转折→衰减）**vs** 中途失败 |
| **Event Structure** | 单一事件类型主导 **vs** 多类型带时序 |
| **Result** | `positive` **vs** `weak` / `failed` / `no_clear_campaign` |

> ⚠️ **失败案例同样是覆盖。**
> 「该方向历史上**没有**形成 Campaign」是一个**有价值的结论**，
> 必须以 `no_clear_campaign` / `exclusions` 显式记录，**不得**为了填满而升级边缘事件。

---

## 6. 明确不做

- ❌ 不设「每个 family 至少 N 个 Campaign」
- ❌ 不设「必须覆盖全部 10 个方向」
- ❌ 不为提高 `STRUCTURAL_SUPPORTED` 数量而扩容
- ❌ 不把热门主题自动升格为 Macro Theme
- ❌ 不在 R01 内新增 DB `themes` 行（taxonomy 变更属独立轮次）
- ❌ 不修改 Research Model v1.0 / schema / export / Product

---

## 7. 与 ROADMAP 的关系

`docs/ROADMAP.md` §3「Coverage Expansion」原文：

> **Wave 1C 暂停。仅在新研究问题证明必须扩容时重新开启。**

**本轮即该条件的触发**：第二次真实使用确认了瓶颈是
**Historical Universe 太窄**（4 个 Macro Theme / 1 条 STRICT 对应），
因此 Coverage Expansion 以 **R01 独立研究轮次**的形式重新开启。

**但 R00 只建立基础设施 —— 不启动任何 family 的研究。**

---

## 8. 版本

| 版本 | 内容 |
|---|---|
| **v0.1** | 首版：当前基线 · 4 已有族补强方向 · 6 新增 family 方向 · 缺失机制轴诊断 · AI/算力交叉处理原则 · Priority A/B · 充分覆盖判定原则 |
