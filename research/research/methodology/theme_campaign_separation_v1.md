# Theme / Campaign Separation Rules v1（主题—战役分层判据）

> **性质**：研究层**判据与禁令**，不是新数据模型。
> **定位**：补齐 `research_model_v1_0.md`（§3 ThemeCycle）与 `theme_lifecycle_v0_2.md`（§3 / §5）
> 的**统一原则**：*一个 Macro Theme 可以包含多个 Campaign；Sub-theme 不等于 Campaign。*
> **兼容性**：本文件**不新增持久化实体 / 不新增表 / 不新增必填字段 / 不改 schema / 不改历史结论**，
> 因此与 `research_model_v1_0.md` §18「不扩展新的模型概念，保持 v1.0 冻结」**不冲突**。
> **不含**任何预测 / 概率 / 胜率 / seasonality / 交易信号。
> 版本：v1.0 · 状态：ACTIVE（判据层）

---

## 1. 分层定义（固定职责）

```text
Macro Theme           产品级长期稳定分类
    ↓
Theme Cycle           研究层周期归组（可多年、可含多个 Campaign）
    ↓
Campaign              独立历史行情/机会阶段
    ↓
Sub-theme / Narrative 解释层（叙事主导结构）
    ↓
Phase / Signal        生命周期阶段 / 研究信号

旁挂：
Catalyst              事件 / 催化剂（不等于 Campaign）
```

| 层 | 定义 | 持久化 | Timeline 一行？ |
|---|---|---|---|
| **Macro Theme** | 产品级长期稳定分类（汽车 / 医药健康 / 大消费 / 电力 / 资源 …） | `themes` 中 `parent_theme_id IS NULL`（`theme_type ∈ sector/industry`） | ✅ **产品主视图的主要主题单位** |
| **Theme Cycle** | 一段时期内、同属主题家族、**可能含多 Campaign** 的研究归组 | ❌ research-level 标签（`theme_cycle_id`），不入库 | ❌ 不强制成为一行 |
| **Campaign** | 独立历史行情阶段，有明确主题 / 持续性 / 市场关注 / 可解释 start-end / ≥2 独立 Evidence | `campaigns` + `campaign_themes` | Detail 层细节 |
| **Sub-theme** | Campaign **内部**的解释维度（叙事 / 主导结构 / 行业分支） | `themes` 中 `parent_theme_id = <Macro Theme>`（`theme_type='concept'`） | ❌ **不得自动升级为 Campaign / 不得自动成行** |
| **Catalyst** | 事件 / 催化剂 | `events` | ❌ |
| **Phase** | Campaign 生命周期阶段 | `campaign_phases` / export `lifecycle[]` | ❌ |
| **Research Signal** | EARLY_SIGNAL / THEME_FORMING / CONFIRMATION_CANDIDATE | export `signals[]` | ❌ |

> **记忆点**：**Sub-theme 是解释维度，Campaign 是独立行情阶段。解释维度不产生新行。**

---

## 2. Campaign Independence Gate（五问判据）

用于回答：*某个 Sub-theme 应停留在解释层，还是升级为独立 Campaign？*

### Q1. Independent Attention Center
是否形成了**相对独立的市场注意力中心**？

### Q2. Independent Representative Stocks
是否出现**相对独立的一组**代表性公司 / 股票？

### Q3. Independent Persistence
这种叙事 / 行情是否具有**足够独立的持续时间**？

### Q4. Independent Lifecycle
是否可以**单独描述**：
```
Formation → Rise → Peak / Turn → Decline / End
```

### Q5. Residual Test（**最关键**）
如果把该 Sub-theme 从原 Theme Cycle 中去掉：

> **剩余的行情是否仍然能够作为一个完整、合理的 Campaign 解释？**

- 若「**能**」→ 说明两者可各自独立解释 → 倾向独立 Campaign。
- 若「**不能**」（去掉后主线残缺）→ 说明它本来就是主线的一部分 → 停留 Sub-theme。

> **Q5 的作用**：防止「因为出现新催化 / 新龙头，就把一段连续行情切碎」。

---

## 3. 判定结果（Case A / B / C）

| Case | 条件 | 判定 | 处理 |
|---|---|---|---|
| **A** | **大多数问题答案为「否」** | `Sub-theme` | 归入**解释层**；不单独建立 Campaign、不新增 Timeline 行 |
| **B** | **大多数问题答案为「是」**，但证据 / 生命周期尚未闭合 | `Campaign Candidate` | 进入进一步研究（对应 `RC-` research candidate） |
| **C** | **证据充分 且 生命周期独立** | `Historical Campaign` | 进入正式 Campaign（`C-`） |

**Case A 的典型形态**（不要单独建立 Campaign）：
- 同一主线下的一个细分方向
- 一个行业分支
- 单个政策刺激
- 单个公司事件
- 单次新闻催化

---

## 4. 禁止规则（六条）

### 规则 1 —— `Catalyst ≠ Campaign`
多个催化剂**不代表**多个 Campaign。同一事件簇的多个步骤（如「政策方向宣布 → 细则公告」）
应作为一个 Campaign 的内部结构记录，不拆分为两个 Campaign。

### 规则 2 —— `Sub-theme ≠ Campaign`
一个 Macro Theme 可以内部存在多个 Sub-theme，而**不必拆 Timeline 行**。

### 规则 3 —— `不同时间 ≠ 不同 Campaign`
时间前后相邻，**不自动**意味着独立。

### 规则 4 —— `同一时间 ≠ 同一个 Campaign`
两个叙事**即使时间重叠**，也可能是两个独立 Campaign。

### 规则 5 —— `Campaign overlap is allowed`
两个 Campaign **可以**有时间重叠。
> **不要求** `Campaign A.end < Campaign B.start`。
> 不得为了让时间轴「看起来整齐」而修改 Campaign 日期。

### 规则 6 —— 不得为「整齐」人为切 Campaign
不要为了得到整齐的时间轴而人为切分 Campaign；也不得为了迎合模型而重写历史边界。

---

## 5. 与既有方法论的对应（不改语义）

| 本文件 | 既有出处 | 关系 |
|---|---|---|
| Theme Cycle 可含多个 Campaign | `research_model_v1_0.md` §3；`theme_lifecycle_v0_2.md` §3 | **复述 + 命名统一** |
| Theme Drift | `research_model_v1_0.md` §13；`theme_lifecycle_v0_2.md` §4 | 沿用 |
| Campaign Overlap（规则 5） | `theme_lifecycle_v0_2.md` §5 | 沿用 |
| Campaign End vs Theme Cycle End | `theme_lifecycle_v0_2.md` §6 | 沿用 |
| Campaign 判定标准（5 条） | `research_model_v1_0.md` §5 / §14 | 沿用（本文件 Case C 引用之） |
| Catalyst ≠ Campaign（规则 1） | `theme_lifecycle_v0_2.md` §7 特殊处理 | **明确化** |
| Sub-theme 层（新增命名） | `themes.theme_type='concept'` + `parent_theme_id`；`data/candidate/rules.ts` 注释 | **仅命名与成文，无实现变化** |
| Macro Theme 层（新增命名） | `themes.parent_theme_id IS NULL`；`data/candidate/themes.ts` | **仅命名与成文，无实现变化** |
| Independence Gate | `2024_robotaxi_continuity_review.md` §8（隐式四问） | **形式化** |

---

## 6. 应用示例（现有案例复核，均为既有结论）

| 案例 | Gate 判定 | 结果 |
|---|---|---|
| 2022 汽车：05-23（国常会 600 亿）vs 05-31（财政部细则） | Q5 = 否（与 05-23 同属一个事件簇） | **同一 Campaign 内部结构**，不拆 ✅ 既有做法 |
| 2023 智能驾驶 → 华为汽车 | Q1/Q2/Q3/Q4 均为「是」（注意力中心、龙头组、催化类型同时迁移） | **两个独立 Campaign**（同属 `auto_intelligence_2023`），并记录 Theme Drift + Overlap ✅ 既有做法 |
| 2024-09-05 次级回流（Robotaxi） | Q3 = 否（2 日即回吐）、Q5 = 否；仅 3/5 核心同步 | **停留 `secondary_campaign_same_theme_cycle`**，不升级为 Campaign ✅ 既有做法 |
| 2022 中通客车 | 与主线不同源（核酸检测车） | `event_driven` 独立记录，不并入主 Campaign ✅ 既有做法 |

---

## 7. 纪律

- 本文件为**研究描述与判据**，非交易信号。
- 宁可 `unknown` / `candidate` / `no_clear_campaign`，也不伪装 `verified`。
- 真实历史事实优先，**不为支持模型而修改研究结果**。
- Sub-theme / Macro Theme 为**归组与命名**，属第 3 层（Grouping），不得当作市场客观结论。
- 不计算 `seasonality_score` / `win_rate` / `probability` / `predictive_model`。
- 新增 Macro Theme（如医药健康）时，**必须先有真实行情与证据**，不得为「补齐结构」而编造。

---

*本文件为方法论判据，不改 schema / DB / 数据 / export / 历史结论。*
*配套审计见 `docs/THEME_CAMPAIGN_MODEL_AUDIT.md`。*
