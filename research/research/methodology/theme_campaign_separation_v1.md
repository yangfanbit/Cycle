# Theme / Campaign Separation Rules v1.1（主题—战役分层判据）

> **性质**：研究层**判据与禁令**，不是新数据模型。
> **定位**：补齐 `research_model_v1_0.md`（§3 ThemeCycle）与 `theme_lifecycle_v0_2.md`（§3 / §5）
> 的**统一原则**：*一个 Macro Theme 可以包含多个 Campaign；Sub-theme 不等于 Campaign。*
> **兼容性**：本文件**不新增持久化实体 / 不新增表 / 不新增必填字段 / 不改 schema / 不改历史结论**，
> 因此与 `research_model_v1_0.md` §18「不扩展新的模型概念，保持 v1.0 冻结」**不冲突**。
> **不含**任何预测 / 概率 / 胜率 / seasonality / 交易信号。
> 版本：**v1.1** · 状态：ACTIVE（判据层）

**本文件即 Research Model v1.1 的方法论澄清层。** v1.1 相对 v1.0 只做**判据补强**，
不新增实体、不改既有结论；`research_model_v1_0.md` 的 v1.0 冻结保持有效。

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

#### Q1 Anti-example（**v1.1 新增**）

> **不同名称 ≠ 不同 Campaign。**

如果两个候选：

- **资金来源高度重叠**（同一资金池 / 同一持仓逻辑 / 同一批机构）
- **核心代表资产高度重叠**
- **市场交易逻辑一致**（同一套买卖理由）

则**优先**认为：

```text
Same Campaign  +  Different Sub-theme
```

而**不是**：

```text
New Campaign
```

**典型反例**：不能因为「创新药」「CXO」「医疗服务」都有上涨，就自动创建三个 Campaign ——
若它们**同属"医药核心资产"资金池、共享同一"政策免疫 + 高景气"交易逻辑**，
则应视为**同一 Campaign 内部的三个 Sub-theme**（除非其余 Q2–Q5 另有强证据）。

> **判据作用**：防止把「同一资金池的分支」误判为多个独立 Campaign。

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

### 3.1 Campaign vs Sub-theme 边界示例（**v1.1 新增**）

#### 应作为 `Sub-theme`（不升级）

需**同时**满足：

| 条件 | 说明 |
|---|---|
| **同一资金逻辑** | 资金来源、持仓机构、交易理由一致 |
| **同一市场叙事** | 讲述的是同一个故事，只是细分方向不同 |
| **生命周期高度一致** | Formation / Peak / Decline 与主线基本同步，无独立节奏 |

→ 归入**解释层**。**不新增 Timeline 行**，**不建立 Campaign**。

#### 应升级为 `Campaign`

需满足 Gate **Q1–Q5 多数成立**：

- 独立 **Attention Center**
- 独立 **Representative Assets**
- 独立 **Persistence**
- 独立 **Lifecycle**（可单独描述 Formation → Rise → Peak/Turn → Decline/End）
- **Residual Test 成立**（去掉后剩余部分仍自洽）

→ 进入 **Case B（Candidate）**；证据充分且生命周期独立 → **Case C（Historical Campaign）**。

> **对照表（决策速查）**

| 观察到的现象 | 判定 |
|---|---|
| 不同名称，但同一资金池 + 同一叙事 + 同步生命周期 | **Sub-theme** |
| 不同名称，独立注意力 + 独立龙头组 + 独立生命周期 + Residual 成立 | **Campaign** |
| 不同名称，独立性存疑（如共享资金池但节奏略不同） | **暂留 Sub-theme**，标记待验证 |

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

## 5. Theme Cycle Pattern（**v1.1 新增**）

用于描述**一个 Theme Cycle 内部 Campaign 的组织方式**。这是**描述层分类**，
不新增实体、不改变分层结构；同一 Macro Theme 在不同时期可以呈现不同 Pattern。

### Pattern A：Sequential Cycle（顺序型）

> **定义**：Campaign 按时间顺序演进，后续 Campaign 通常**继承、替代或迁移**前一 Campaign 的市场关注。

```
Theme Cycle
   │
Campaign A
   ↓
Campaign B
   ↓
Campaign C
```

**识别特征**
- Narrative migration（叙事迁移）
- Attention shift（关注中心转移）
- **Overlap possible**（允许时间重叠）
- 后续 Campaign 可能**吸收**前一 Campaign 的资金与关注

**典型：汽车智能化（`auto_intelligence_2023`）**

```
Smart Driving（C-2023-AD）
      ↓  Theme Drift
Huawei Auto（RC-2023-HUAWEI）
```

> 该案例已记录 Theme Drift + Campaign Overlap（08-29 ~ 09-12）。

### Pattern B：Parallel Cycle（并行型）

> **定义**：同一 Theme Cycle 内多个 Campaign **并行展开**，各自具有**独立生命周期**。

```
        Campaign A
           ‖
Theme Cycle ‖  Campaign B
           ‖
        Campaign C
```

**识别特征**
- 多个叙事**同时存在**
- **Peak 时间可能不同**（不同 Campaign 可在不同时间见顶）
- **不要求** Campaign 相互替代

**典型：医药结构升级（`medical_structural_upgrade_2019_2022`，候选）**

```
Medical Structural Upgrade
   ├── Innovation Drug / CXO（主线）
   ├── Pandemic Medical（M1，Candidate）
   └── TCM 中药（M3，Candidate）
```

> 医药案例显示：同一 Cycle 内**多叙事并存**，且**分批见顶**
> （板块口径 2021-07-01 / 成长赛道口径 2022-01-04）。

### Pattern C：Hybrid Cycle（混合型）

> **定义**：同时存在**时间迁移**与**横向并存**两种组织方式。

若未来发现某 Theme Cycle 内部既有时序接续（A → B），又有并行分支（B ‖ C），
允许将其判定为 **Hybrid**，并**分别记录**每段的 Pattern。

```
Theme Cycle（Hybrid）
   │
Campaign A
   ↓（sequential）
Campaign B  ‖  Campaign C   （parallel）
```

**约束**
- 不得为了「凑成某一种 Pattern」而改写 Campaign 边界。
- Pattern 是**研究描述**，不是市场客观结论；判定需标注依据与置信度。
- 一个 Cycle 的 Pattern 可在不同时期变化（A → Hybrid 是允许的）。

---

## 6. Campaign Lifecycle Measurement Rule（**v1.1 新增**）

用于**避免未来误判 Peak / End**。这是**测量口径规则**，不新增字段。

### 6.1 Campaign Peak Definition

**Campaign Peak ≠ Macro Theme 指数最高点**

**Campaign Peak ≠ 行业指数最高点**

**Campaign Peak ≠ 单一股票最高点**

Campaign Peak **应优先依据以下三者综合判断**：

```
Campaign Core Narrative
        +
Representative Assets
        +
Market Attention
```

**推论（必须遵守）**

- Peak 的判定口径应**以该 Campaign 自己的代表标的 / 子指数为准**，
  **不得**用上位板块指数（Macro Theme 指数 / 行业指数）代替。
- 若同一 Cycle 内多个 Campaign 存在，**各自的 Peak 应分列记录**，不强行取同一日期。
- 允许 **Peak cluster**（多日期候选）。

### 6.2 Campaign End Definition

**Campaign End ≠ 行业指数下跌**

**Campaign End ≠ 某只股票见顶**

**Campaign End ≠ 新闻减少**

判断 Campaign End，需要判断是否发生：

| 判据 | 含义 |
|---|---|
| **市场注意力消失** | 注意力中心不再停留于该叙事 |
| **Narrative 失效** | 核心叙事不再被市场采信 |
| **资金中心迁移** | 资金系统性转向其他方向 |
| **新 Campaign 替代** | 出现独立的新 Campaign 接替（见 Pattern A） |

### 6.3 错误 vs 正确（示例）

**❌ 错误**
```
医药指数 2021-07 下跌
        ↓
认为医药 Campaign End
```

**✅ 正确**
```
Macro Theme Peak（板块口径）
        ↓
某 Sub-theme Peak（各自口径）
        ↓
另一个 Campaign 延续
```

> **概括**：**Macro Theme 的顶 ≠ 某个 Campaign 的 End。**
> 板块指数回落可能只是某个 Sub-theme / 某个 Campaign 见顶，
> 同期另一个 Campaign 可能仍在延续（Pattern B 的常态）。

### 6.4 与既有做法的一致性

汽车案例 `2022_auto_boundary_review.md` 已实际采用同类处理：
**「龙头（比亚迪/长安）峰值 06-23/24；行业代理（AUTO）峰值 06-28 —— 两者分列记录」**。
本规则把该做法**上升为通用判据**，适用于所有 Macro Theme。

---

## 7. 与既有方法论的对应（不改语义）

| 本文件 | 既有出处 | 关系 |
|---|---|---|
| Theme Cycle 可含多个 Campaign | `research_model_v1_0.md` §3；`theme_lifecycle_v0_2.md` §3 | **复述 + 命名统一** |
| Theme Drift | `research_model_v1_0.md` §13；`theme_lifecycle_v0_2.md` §4 | 沿用 |
| Campaign Overlap（规则 5） | `theme_lifecycle_v0_2.md` §5 | 沿用 |
| Campaign End vs Theme Cycle End | `theme_lifecycle_v0_2.md` §6 | 沿用 |
| Campaign 判定标准（5 条） | `research_model_v1_0.md` §5 / §14 | 沿用（本文件 Case C 引用之） |
| Catalyst ≠ Campaign（规则 1） | `theme_lifecycle_v0_2.md` §7 特殊处理 | **明确化** |
| Sub-theme 层 | `themes.theme_type='concept'` + `parent_theme_id`；`data/candidate/rules.ts` 注释 | **仅命名与成文，无实现变化** |
| Macro Theme 层 | `themes.parent_theme_id IS NULL`；`data/candidate/themes.ts` | **仅命名与成文，无实现变化** |
| Independence Gate | `2024_robotaxi_continuity_review.md` §8（隐式四问） | **形式化** |
| **Theme Cycle Pattern（§5）** | 汽车（Sequential）与医药（Parallel）的实证对比（v1.1） | **新增描述层分类，无新实体** |
| **Lifecycle Measurement Rule（§6）** | `2022_auto_boundary_review.md` §3「峰值分列」做法（v1.1） | **上升为通用判据** |
| **Q1 Anti-example（§2）** | 医药 M2 消费医疗「共享资金池」问题（v1.1） | **补充反例** |

---

## 8. 应用示例（现有案例复核，均为既有结论）

| 案例 | Gate 判定 | 结果 |
|---|---|---|
| 2022 汽车：05-23（国常会 600 亿）vs 05-31（财政部细则） | Q5 = 否（与 05-23 同属一个事件簇） | **同一 Campaign 内部结构**，不拆 ✅ 既有做法 |
| 2023 智能驾驶 → 华为汽车 | Q1/Q2/Q3/Q4 均为「是」（注意力中心、龙头组、催化类型同时迁移） | **两个独立 Campaign**（同属 `auto_intelligence_2023`），Pattern = **Sequential**，并记录 Theme Drift + Overlap ✅ 既有做法 |
| 2024-09-05 次级回流（Robotaxi） | Q3 = 否（2 日即回吐）、Q5 = 否；仅 3/5 核心同步 | **停留 `secondary_campaign_same_theme_cycle`**，不升级为 Campaign ✅ 既有做法 |
| 2022 中通客车 | 与主线不同源（核酸检测车） | `event_driven` 独立记录，不并入主 Campaign ✅ 既有做法 |
| 医药「创新药 / CXO / 医疗服务」同时上涨 | **Q1 Anti-example**：同属医药核心资产资金池 + 同一「政策免疫」交易逻辑 | **倾向 Sub-theme（同一 Campaign 内部）**，不自动建三个 Campaign ⚠️ 候选待验证 |
| 医药 M1 疫情医疗（2020–2021） | Q1/Q2/Q5 成立；Q3/Q4 待行情数据 | **Campaign Candidate**（medium），Pattern = **Parallel** ⚠️ 待验证 |

---

## 9. 纪律

- 本文件为**研究描述与判据**，非交易信号。
- 宁可 `unknown` / `candidate` / `no_clear_campaign`，也不伪装 `verified`。
- 真实历史事实优先，**不为支持模型而修改研究结果**。
- Sub-theme / Macro Theme / **Theme Cycle Pattern** 均为**归组与描述**，属第 3 层（Grouping），
  不得当作市场客观结论。
- 不计算 `seasonality_score` / `win_rate` / `probability` / `predictive_model`。
- 新增 Macro Theme（如医药健康）时，**必须先有真实行情与证据**，不得为「补齐结构」而编造。

---

## 修订记录

| 版本 | 变更 | 性质 |
|---|---|---|
| **v1.0** | 五层定义 + Independence Gate（Q1–Q5）+ Case A/B/C + 六条禁止规则 | 判据层建立 |
| **v1.1** | ① 新增 **Theme Cycle Pattern**（§5：Sequential / Parallel / Hybrid）<br>② 新增 **Campaign Lifecycle Measurement Rule**（§6：Peak/End 口径）<br>③ 新增 **Q1 Anti-example**（§2：不同名称 ≠ 不同 Campaign）<br>④ 新增 **Campaign vs Sub-theme 边界示例**（§3.1） | 判据补强，**无新实体 / 无新字段 / 不改既有结论** |

---

*本文件为方法论判据，不改 schema / DB / 数据 / export / 历史结论。*
*配套审计见 `docs/THEME_CAMPAIGN_MODEL_AUDIT.md`。*
