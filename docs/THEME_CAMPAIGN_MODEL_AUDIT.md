# THEME / CAMPAIGN MODEL AUDIT（分层模型统一审计）

> **性质**：只读审计 + 方法论统一。**不是**功能开发，**不是**历史重标。
> **日期**：2026-09-14
> **审计对象**：ThreeC（`yangfanbit/Cycle`）在汽车案例中已部分体现、但尚未完全抽象成通用规则的
> 「一个 Macro Theme 可包含多个 Campaign；Sub-theme ≠ Campaign」方法。
> **结论优先级**：`规范统一 > 结构清晰 > 数据修正`。
> **本轮未修改任何历史研究结论 / schema / DB 数据 / export 数据 / Timeline 行为。**

---

## 1. Current Model（现状）

### 1.1 研究层（research）

| 文档 | 已有内容 |
|---|---|
| `research/research/methodology/research_model_v1_0.md` | §3 **ThemeCycle**：「同一主题家族下的研究归组，**可包含多个 Campaign**」；§5 Campaign 判定标准；§13 三层语义（Fact / Interpretation / **Grouping=ThemeCycle/Theme Drift/Campaign Relation**）；§17 案例（含 Theme Drift + Campaign Overlap）；**§18 声明模型 v1.0 冻结（不扩展新概念）** |
| `research/research/methodology/theme_lifecycle_v0_2.md` | §3 Theme Cycle 结构图（1 Cycle → N Campaign）；§4 **Theme Drift**；§5 **Campaign Overlap**（明确「**不强迫 `A.end < B.start`**」）；§6 Campaign End 判定（含 **Theme Cycle End** 独立于 Campaign End） |
| `research/research/methodology/theme_lifecycle_schema_v0_1.md` | 设计方案 + 红队；目标层级 `SeasonalRule → ThemeCycle → Campaign → Phase`；**结论：不建表，保持 research-level**（当前未被采纳为 schema） |
| `research/research/methodology/rule_candidates_v1.md` | 候选规则清单；`rule_pharma_year` 风险栏写明「**主题分散，需按子赛道拆窗口**」 |

**研究层已有**：Rule、ThemeCycle（研究级归组）、Campaign、Campaign Phase、Research Signal、
Theme Drift、Campaign Overlap、Event / Evidence / Security、Point-in-Time / Retrospective。

**研究层缺失**：**Macro Theme** 与 **Sub-theme** 两个术语从未出现（全仓 0 次命中）；
**Campaign Independence Gate** 从未形式化。

### 1.2 数据层（SQLite，`research/schema/schema.sql`）

```
research_rules ──1..*── annual_reviews ──1..*── campaigns ──1..*── campaign_phases
                                                  │
                                       campaign_themes (M..N, role: main/related/secondary)
                                                  │
                                              themes ──┐
                                                  │    └─ parent_theme_id（自引用！）
                                                  └── campaigns
```

**关键发现：`themes` 表已内建层级。**

```sql
CREATE TABLE themes (
    theme_id        TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    theme_type      TEXT NOT NULL CHECK (theme_type IN ('sector','industry','concept')),
    parent_theme_id TEXT REFERENCES themes(theme_id),   -- ★ 父子层级
    description     TEXT
);
```

实际数据（7 行）已形成两级结构：

```
TH-AUTO 汽车 (industry, root)
├── TH-AD                智能驾驶/无人驾驶 (concept)
├── TH-CAR-CONSUMPTION   汽车消费/购置税刺激 (concept)
├── TH-NEV               新能源汽车/电池 (industry)
│   └── TH-TESLA-CHAIN   特斯拉产业链 (concept)
├── TH-ROBOTAXI          Robotaxi/无人驾驶/智能网约车 (concept)
└── TH-V2X               车路云一体化/车路协同 (concept)
```

`campaign_themes` 中 **「汽车」对 8 个 Campaign 全部以 `role='related'` 出现** —— 这正是
「一个 Macro Theme 关联多个 Campaign」的既有表达。

### 1.3 导出层（`exports/timeline_export_v1.json` + `contracts/timeline_export_v1.md`）

- 契约 §5 已定义 `themes: [{ name, theme_type, role }]`。
- 契约 §11 已把 **`theme_cycle_id`** 列为研究层元数据（「Research-only metadata」）。
- 实际导出中 **8 个 campaign + 2 个 research_candidate 全部带 `theme_cycle_id`**：

| theme_cycle_id | 成员 |
|---|---|
| `auto_ad_2019` | C-2019-AD |
| `auto_nev_2020` | C-2020-NEV |
| `auto_nev_2021` | C-2021-NEV |
| `auto_policy_2022` | C-2022-POLICY |
| `auto_intelligence_2023` | **C-2023-AD + RC-2023-HUAWEI**（1 Cycle → 2 实体）|
| `auto_v2x_2024` | C-2024-V2X |
| `robotaxi_2024` | **C-2024-ROBOTAXI + RC-2024-SECONDARY**（1 Cycle → 2 实体）|
| `robotaxi_2025` | C-2025-ROBOTAXI |

### 1.4 产品层（`src/` 与 `data/`）

- **产品侧候选层 `data/candidate/themes.ts` 已实现父子主题树 + 辅助函数**
  （`parent_theme_id` + `childrenOf()`），并注册了 8 个 sector 级主题：
  `th_auto 汽车` / `th_pharma 医药` / `th_consumption 大消费` / `th_power 电力` /
  `th_mining 矿产` / `th_infra 基建` / `th_media 广电·传媒` / `th_education 教育`。
- `data/candidate/rules.ts` 的 `rule_auto_summer` 描述**已写明层级原则**：
  > 「底层行业（汽车）与每年的具体题材（如 2023 年减速器、2024 年自动驾驶）**是两个层级，不可混为一谈**。」
- 但 **Timeline 视图未使用该层级**：`themeRows.ts` 的 `primaryThemeName()` 取 `role='main'`，
  而 `role='main'` 在导出中指向 **concept（子题材）**。实测 9 月视图 5 行分别是
  「智能驾驶/无人驾驶」「新能源汽车/电池」「汽车消费/购置税刺激」「华为汽车」「Robotaxi/…」——
  **全部是「汽车」的子题材，Macro Theme「汽车」从未作为一行出现。**
- **adapter 丢弃了两个已存在的字段**：`timelineAdapter.ts` 只映射 `{ name, role }`，
  把导出已提供的 `theme_type` 与 `theme_cycle_id` 丢掉（`timelineTypes.ts` 已声明这两个可选字段）。

### 1.5 现状判定

| 目标能力 | 研究层 | 数据层(DB) | 导出层 | 产品数据层 | 产品视图层 |
|---|---|---|---|---|---|
| Macro Theme → 多 Campaign | ⚠ 概念未命名 | ✅ `parent_theme_id` | ⚠ 仅靠 `theme_type` 推断 | ✅ 父子树 + `childrenOf` | ❌ 未使用 |
| Theme Cycle → 多 Campaign | ✅ 已定义 | — 不入库（设计决定）| ✅ `theme_cycle_id` | — | ❌ 被 adapter 丢弃 |
| Sub-theme ≠ Campaign | ⚠ 概念未命名 | ✅ `themes` 可复用 | ✅ `theme_type='concept'` | ✅ | ⚠ 反而被当作行标题 |
| Campaign Overlap 允许 | ✅ 明写 | — | ✅ 2023 实例 | — | — |
| Catalyst ≠ Campaign | ✅ 2022 实例 | — | — | — | — |
| Campaign Independence Gate | ❌ 未形式化 | — | — | — | — |

---

## 2. Proposed Unified Model（统一后的分层）

```text
Macro Theme           产品级长期稳定分类（汽车 / 医药健康 / 大消费 / 电力 / …）
    ↓                 现存映射：themes(parent_theme_id IS NULL, theme_type ∈ sector/industry)
Theme Cycle           研究层周期归组（auto_intelligence_2023 / robotaxi_2024 / …）
    ↓                 现存映射：export 的 theme_cycle_id（不入库，保持 research-level）
Campaign              独立历史行情阶段（C-2023-AD / RC-2023-HUAWEI / …）
    ↓                 现存映射：campaigns 表 + campaign_themes
Sub-theme / Narrative 解释层（智能驾驶 / Robotaxi / 华为汽车 / 创新药 / CRO / 中药 …）
    ↓                 现存映射：themes(theme_type='concept', parent_theme_id=<Macro Theme>)
Phase / Signal        生命周期阶段与早期信号
                      现存映射：export lifecycle[] / signals[]；DB campaign_phases（旧枚举）

旁挂（不属于上述主链）：
Catalyst              事件/催化剂（events 表 / export events[]）—— 不等于 Campaign
Research Signal       研究信号（EARLY_SIGNAL / THEME_FORMING / CONFIRMATION_CANDIDATE）—— 不等于 Campaign Phase
```

### 层次职责（必须固定）

| 层 | 回答的问题 | 是否入库 | 是否作为 Timeline 一行 |
|---|---|---|---|
| Macro Theme | 这是哪一大类方向？ | ✅ `themes`（root） | ✅ **产品主视图主要单位** |
| Theme Cycle | 这段时期属于同一主题家族的哪一轮？ | ❌ research-level 标签 | ❌ 不强制成行 |
| Campaign | 历史上是否发生一轮有持续性的独立行情？ | ✅ `campaigns` | Detail 层细节 |
| Sub-theme | 这轮行情的叙事主导结构是什么？ | ✅ `themes`（child） | ❌ **不得自动升级为一行/Campaign** |
| Catalyst | 什么事件触发/强化/解释？ | ✅ `events` | ❌ |
| Phase / Signal | 行情走到哪一步 / 有无提前信号？ | ✅ `campaign_phases` / export | ❌ |

> **判据**：Sub-theme 是「解释维度」，Campaign 是「独立行情阶段」。**解释维度不产生新行。**

---

## 3. Campaign Independence Gate（通用判定框架）

用于回答：*某个 Sub-theme 应当停留在解释层，还是升级为独立 Campaign？*

### 五项核心判据

| # | 判据 | 要问的问题 | 反例信号（倾向 Sub-theme） |
|---|---|---|---|
| **Q1** | Independent Attention Center | 是否形成**相对独立的市场注意力中心**？ | 注意力仍集中在原主线；仅局部个股活跃 |
| **Q2** | Independent Representative Stocks | 是否出现**相对独立的一组**代表性公司/股票？ | 代表性标的与原 Campaign 高度重合 |
| **Q3** | Independent Persistence | 叙事/行情是否有**足够独立的持续时间**？ | 2–3 日内回吐、无持续（如 2024-09-05 次级段） |
| **Q4** | Independent Lifecycle | 能否**独立描述** Formation → Rise → Peak/Turn → Decline/End？ | 只有一次脉冲，无法给出独立生命周期 |
| **Q5** | **Residual Test**（最关键） | 把该 Sub-theme 从原 Theme Cycle 去掉后，**剩余行情是否仍能作为完整、合理的 Campaign 解释**？ | 去掉后主线残缺 → 说明它本来就是主线的一部分 |

> **Q5 为什么最关键**：它防止「因为出现了新催化/新龙头，就把一段连续行情切碎」。
> 只有当**整体**去掉后剩余部分仍自洽，才说明这两段是可以共存的两个独立解释。

### 判定结果

| Case | 条件 | 判定 | 处理 |
|---|---|---|---|
| **A** | 多数答案为**否** | `Sub-theme` | 归入解释层；**不单独建立 Campaign**、**不新增 Timeline 行** |
| **B** | 多数答案为**是**，但生命周期/证据未闭合 | `Campaign Candidate` | 进入进一步研究（对应 `RC-` / research candidate） |
| **C** | 证据充分**且**生命周期独立 | `Historical Campaign` | 进入正式 Campaign（`C-`） |

Case A 的典型形态：同一主线下的一个细分方向、一个行业分支、单个政策刺激、单个公司事件、单次新闻催化。

### 六条禁止规则

1. **Catalyst ≠ Campaign** —— 多个催化剂不代表多个 Campaign。
2. **Sub-theme ≠ Campaign** —— 一个 Macro Theme 内部可有多个 Sub-theme，**不必拆 Timeline 行**。
3. **不同时间 ≠ 不同 Campaign** —— 时间前后相邻不自动意味着独立。
4. **同一时间 ≠ 同一个 Campaign** —— 时间重叠也可能是两个独立 Campaign。
5. **Campaign Overlap is allowed** —— `A.end < B.start` **不是**必要条件。
6. **不得为了「整齐」人为切 Campaign** —— 禁止为迎合模型而重写历史边界。

> **兼容性声明**：以上是**判据与禁令**，不新增持久化实体、不新增表、不新增必填字段；
> 因此与 `research_model_v1_0.md` §18「不扩展新的模型概念」**不冲突**（详见 §6 与
> `theme_campaign_separation_v1.md`）。

---

## 4. Automotive Audit（逐年）

**判定基准**：`themes.parent_theme_id`（汽车 = Macro Theme）+ `theme_cycle_id` + Campaign Independence Gate。

| 年 | Campaign | theme_cycle_id | 判定 | 依据 | 动作 |
|---|---|---|---|---|---|
| **2019** | C-2019-AD | `auto_ad_2019` | ✅ 保持 | 独立注意力中心（智驾概念）+ 独立龙头 + 独立生命周期（08-15 → 09-24 Peak → 09-30 End）；`event_driven`/weak 已如实标注 | 无 |
| **2020** | C-2020-NEV | `auto_nev_2020` | ✅ 保持 | 独立龙头组（宁德/比亚迪/特斯拉链）+ 独立生命周期（06-01 → 07-13 Peak → 08-21 Secondary → 09-30） | 无 |
| **2021** | C-2021-NEV | `auto_nev_2021` | ✅ 保持 | 同 Macro Theme 下**下一年度的独立重演**；与 2020 时间不重叠、龙头/叙事可独立描述 → 满足 Q1–Q5 | 无 |
| **2022** | C-2022-POLICY | `auto_policy_2022` | ✅ **保持单一 Campaign** | 04-27 Setup → 05-23 Theme Formation → 05-23~06-28 Main → 07 Retracement → 08 Decay，**是同一 Campaign 的内部 Phase**；`05-23`（国常会 600 亿）与 `05-31`（财政部细则）被明确判为「**同一事件簇的两个步骤**」，**未拆分** ✓ | **无（这正是正确做法）** |
| **2022** | 中通客车 | — | ✅ 保持独立 | 「核酸检测车」与汽车政策/新能源主线**不同源** → `classification=event_driven`，不并入主 Campaign 强度 ✓ | 无 |
| **2023** | C-2023-AD + RC-2023-HUAWEI | `auto_intelligence_2023`（**共享**） | ✅ **保持「1 Cycle → 2 Campaign」** | 由 `2023_theme_timeline.md` 判定为 **Theme Drift**（核心叙事 + 核心股票 + 催化类型三者同时迁移），**不是两个无关 Campaign**，也未合并为一个 ✓；`§5` Campaign Overlap 08-29~09-12 已显式记录且未强改日期 ✓ | 无 |
| **2024** | C-2024-V2X | `auto_v2x_2024` | ✅ 保持独立 | 独立注意力中心（车路云政策线）+ 独立龙头 + 独立短生命周期（06-11 → 06-18 Peak → 06-25 End）；与 Robotaxi **时间不重叠**、叙事不同源 | 无 |
| **2024** | C-2024-ROBOTAXI | `robotaxi_2024` | ✅ 保持独立 | 独立注意力中心（萝卜快跑出圈）+ 独立龙头（大众/锦江/金龙…）+ 独立生命周期（07-08 → 08-05 Peak → 08-23 End）；**其独立性与 V2X 无关**，不是「因为时间不同」→ 满足 Q1–Q5 | 无 |
| **2024** | RC-2024-SECONDARY | `robotaxi_2024`（**共享**） | ✅ 保持 Candidate（**未升级**）| `2024_robotaxi_continuity_review.md` 已用「原主题是否消失/冷却期、新催化是否不同、是否再同步、持续性」四问判定为 `secondary_campaign_same_theme_cycle`（3/5 核心同步、2 日即回吐）→ 按 Gate 属 **Case B**，**正确地未升级为 Campaign** ✓ | 无（可选：补 `relation_type=secondary` 记录）|
| **2025** | C-2025-ROBOTAXI | `robotaxi_2025` | ✅ **保持单一 Campaign** | 06-22 → 06-24 Peak → 08-31；同 Macro Theme 下独立年度轮次。**后续催化剂未被错误拆成新 Campaign**（无独立注意力中心/独立龙头组/独立生命周期）→ 符合 Gate 的 Case A（保持解释层） | 无 |

### 4.1 关键结论

- **2022 的处理方向完全正确**：多政策/多催化 → 仍是**一个** Campaign，靠 Phase 承载内部结构。
- **2023 的处理方向完全正确**：`auto_intelligence_2023` 是「1 Theme Cycle → 2 Campaign」的**最佳现有范例**，
  且 Theme Drift 与 Campaign Overlap 都已显式记录。
- **2024 V2X vs Robotaxi 的独立性成立**：两者的独立依据是**注意力中心 + 龙头组 + 生命周期 + 叙事来源**，
  **不是**「时间不同」。这一点现有研究是站得住的。
- **2025 未过度拆分**：符合「不得为整齐而切 Campaign」。
- **没有任何一处需要重标历史**。汽车案例本身已是新规则的**正例集合**。

---

## 5. Medical Pilot Audit（医药健康）

### 5.1 现状：结构就绪，数据为空

| 层 | 医药健康现状 |
|---|---|
| Macro Theme | ✅ `data/candidate/themes.ts` 已注册 `th_pharma 医药`（`theme_type='sector'`，root） |
| Rule | ✅ `rule_pharma_post_interim`（中报后医药关注窗口 08-15~09-30，candidate）；`rule_candidates_v1.md` 的 `rule_pharma_year`（candidate #2，风险栏：「**主题分散，需按子赛道拆窗口**」）|
| Theme Cycle | ❌ 无（无任何 `*_pharma_*` cycle 标签） |
| Campaign | ❌ 无（DB 中 0 条医药 campaign；`data/candidate/campaigns.ts` 为空数组） |
| Sub-theme | ❌ 无（`themes` 表无医药子题材） |
| Evidence / 行情 | ❌ 无（无医药 evidence / market_series） |

> 全仓 `医疗` / `CRO` / `CXO` / `疫苗` / `医疗器械` / `GLP-1` / `生物医药` **命中 0 次**。

### 5.2 模型层验证（不预设答案）

用 Gate 对 2019–2021 医药做**假设性**推演。注意：**以下为方法论推演，不是研究结论**，
在真实数据录入前不得当作历史事实。

| 候选 Sub-theme | Q1 注意力 | Q2 龙头组 | Q3 持续 | Q4 独立生命周期 | Q5 残差检验 | 假设判定 |
|---|---|---|---|---|---|---|
| 创新药 / CRO 结构性重估 | 待验证 | 待验证 | 待验证 | 待验证 | 待验证 | 若 Q5「是」→ **Campaign Candidate** |
| 疫情医疗（口罩/检测/疫苗） | 待验证 | 待验证 | 待验证 | 待验证 | 待验证 | 若 Q5「是」→ **Campaign Candidate** |
| 后续独立创新药 / 出海 | 待验证 | 待验证 | 待验证 | 待验证 | 待验证 | 若 Q5「是」→ **Campaign Candidate** |
| 中药 / 器械 / 医药服务 | 待验证 | 待验证 | 待验证 | 待验证 | 倾向「否」 | 倾向 **Sub-theme（解释层）** |

**模型层结论（可以确定的）**：

1. **`2019–2021` 作为一个 Theme Cycle 比「一年一个 Campaign」更自然** ——
   医药的结构性重估（创新药/CRO）与疫情医疗在时间上**交织**（2020 疫情医疗与创新药重估同年并存），
   而 Theme Cycle 的定义（§1.1）明确允许**多年**且允许**多个 Campaign 时间重叠**（§5）。
   用「Theme Cycle 2019–2021 + 多个 Campaign」表达，能避免把交织的叙事切成「2020 医药」「2021 医药」
   这种**以日历年为界的伪切分**。
2. **不应强行拆**：若某方向的 Q5 残差检验为「否」（去掉后剩余行情仍完整），
   它就该留在解释层，**不新增行**。
3. **不应强行合**：若 Q5 为「是」且 Q3/Q4 成立（独立持续 + 独立生命周期），
   它就应升级为 Campaign，而不是因为「都是医药」而被压平成同一个。

> **回答 §九的问题**：「Theme Cycle 2019–2021 + Campaign 1/2/3」在**方法论上成立且更自然**；
> 但**是否真的成立，必须由真实数据经 Q1–Q5 判定后才能确认**。本轮**不做**该判定，
> 也**不**录入医药历史数据（见 §7 与 DECISION）。

### 5.3 分轨道（Sub-track）说明

`rule_candidates_v1.md` 已预判医药需要「按子赛道拆窗口」。在新分层下，
这在模型上是**天然可表达**的：子赛道 = `themes(theme_type='concept', parent_theme_id='th_pharma')`，
即 **Sub-theme**；是否为独立 Campaign 仍由 Gate 决定。
**不要**把每一个子赛道自动变成 Timeline 的一行。

---

## 6. Data / Schema Impact

| 层 | 是否需要修改 | 说明 |
|---|---|---|
| **research methodology** | ✅ **建议最小增补**（见 §7） | 缺「统一原则」：Macro Theme / Sub-theme / Independence Gate 未成文。**不重写 Research Model**，只增补一节独立文档 + 指针 |
| **research DB schema** | ❌ **不需要** | `themes.parent_theme_id` 已可表达 Macro Theme → Sub-theme；`campaign_themes(role)` 已可表达多 Campaign 共享；`theme_cycle_id` 按设计保持 research-level **不入库**。**无新增表 / 无新增必填字段** |
| **contracts** | ❌ **不需要** | §5 已定义 `themes{name,theme_type,role}`；§11 已把 `theme_cycle_id` 列为研究层元数据 |
| **exports 数据** | ❌ **不需要** | 已含 `themes[]` 与 `theme_cycle_id`，8+2 条齐备 |
| **product 数据层** | ❌ **不需要** | `data/candidate/themes.ts` 已有父子树 + `childrenOf()` |
| **product 视图层** | ⚠ **可选（本轮不做）** | ① adapter 丢弃 `theme_type` / `theme_cycle_id`；② Timeline 以 Sub-theme 为行。**改动会改变 Timeline 行为**，违反本轮「不破坏 Timeline」要求 → 列为 DEFER 并单独立项 |

### 6.1 关于 §十二 的四项能力核对

| 需要表达 | 现有能力 | 结论 |
|---|---|---|
| `macro_theme_id` | `themes.theme_id`（`parent_theme_id IS NULL` 即 Macro Theme）；产品侧 `th_*` | ✅ 可表达（无需新字段） |
| `theme_cycle_id` | export 字段（研究层标签） | ✅ 已存在 |
| `campaign_id` | `campaigns.campaign_id` / `C-` / `RC-` | ✅ 已存在 |
| `sub_theme` | `themes`（`theme_type='concept'` + `parent_theme_id`） | ✅ 可表达（无需新字段） |
| `campaign overlap` | 无字段依赖：两个 Campaign 各带时间区间 + `notes`/research 记录关系 | ✅ 已可表达（2023 实例） |

> **结论：Schema / Contract / Export 均不需要改动** —— 只补文档与最小字段说明即可。

---

## 7. Recommended Next Step

> **唯一一件**：把本文的 §2 / §3 沉淀为方法论文档
> `research/research/methodology/theme_campaign_separation_v1.md`（**已在本轮完成**），
> 并在**现有两份方法论文档中各加一条指针**（不改变其语义）。
>
> 然后停下，等人工确认。**不要**顺势去做 Timeline 重分组、adapter 补字段、医药数据录入。

---

## 8. Audit Findings（缺陷清单）

| # | 级别 | 发现 | 为什么 | 应怎么改 | 影响文件 | 是否必要 |
|---|---|---|---|---|---|---|
| **F1** | 文档 | 全仓无 **Macro Theme** / **Sub-theme** 术语 | 概念只存在于实现（`parent_theme_id`、`theme_type`）与注释中，未成文 → 无法作为可交接的通用规则 | 新增 `theme_campaign_separation_v1.md` | 新文件 | ✅ 本轮已做 |
| **F2** | 文档 | **Campaign Independence Gate** 未形式化 | `2024_robotaxi_continuity_review.md` §8 实际已在用它（4 问），但是**一次性、隐式**的 | 在 F1 文档中形式化为 Q1–Q5 + Case A/B/C + 6 禁令 | 新文件 | ✅ 本轮已做 |
| **F3** | 文档 | `theme_lifecycle_v0_2.md` §9 存在**乱码**「先敌view下」 | 疑似「Point-in-Time 视角下」被打坏，影响可读性 | 修正为「Point-in-Time 视角下」 | `theme_lifecycle_v0_2.md` | ✅ 本轮已做（最小且可控）|
| **F4** | 代码 | adapter 丢弃 `theme_type` / `theme_cycle_id` | 导出已提供、`timelineTypes.ts` 已声明，但 `timelineAdapter.ts` 只映射 `{name, role}` → 产品永远看不到 Macro Theme / Theme Cycle | 在 adapter 补两个字段透传（**不改 Timeline 行为**） | `timelineAdapter.ts` | ⏸ **DEFER**（本轮不改视图层） |
| **F5** | 产品 | Timeline 以 **Sub-theme** 为行，Macro Theme 从不出现 | 与「Timeline 应主要看到 Macro Theme」不一致；但现行为**可用且不错误**（子题材行更细） | 需先定义「Macro Theme 优先 / 可下钻」的交互，再改 `themeRows` | `themeRows.ts` / `SamePeriodView` | ⏸ **DEFER**（改 UI 超出本轮） |
| **F6** | 数据一致性 | DB `campaign_phases.phase_type` 枚举（`startup/acceleration/main_rise/diffusion/retracement/secondary_rally/decline/unclear`）与导出的 `lifecycle[].stage`（`EARLY_SIGNAL/THEME_FORMING/BROAD_CONFIRMATION/MAIN_RISE/PEAK/…`）**不一致** | 两套 Phase 词汇并存；DB 那套 17 行且缺 2019/2024-V2X | 记录在案；**导出的 `lifecycle` 为权威研究视图**，DB 表为历史遗留 | `schema.sql` / export 生成脚本 | ⏸ **DEFER**（改 schema 属破坏性变更） |
| **F7** | 数据完整性 | `RC-2023-HUAWEI` 的题材「华为汽车」**不在 `themes` 表中** | 研究候选的题材绕过 `parent_theme_id` → 无法挂到 `汽车` 之下 | 若该 RC 未来正式化，再新增 `TH-HUAWEI-AUTO`（`parent_theme_id=TH-AUTO`） | `themes` 表 / research c2 | ⏸ **DEFER**（无实际错误，候选期不建正式题材）|

**无 F 项属于「明显且必须立即修复的历史数据错误」。** 本轮仅实际修改 F1/F2/F3。

---

## 9. DECISION

### KEEP（必须保留）

- **`campaigns` 现有 8 条 + 2 个 research candidate 的边界与日期** —— 全部经 Gate 复核，**无需重标**。
- **2022 = 单一 Campaign + 内部 Phase**（多催化不拆）—— 正确范例。
- **2023 = `auto_intelligence_2023` 一个 Theme Cycle 含 2 个 Campaign（Theme Drift + Overlap）** —— 最佳范例。
- **2024 V2X 与 Robotaxi 两个独立 Campaign**，独立性依据是注意力/龙头/生命周期，而非时间。
- **2024 RC-2024-SECONDARY 保持 Candidate**（不升级）。
- **`themes.parent_theme_id` + `theme_type`、`campaign_themes.role`、export `theme_cycle_id`** 现有结构。
- **`research_model_v1_0.md` v1.0 冻结** 与 **ThemeCycle 保持 research-level 不入库** 的既有决定。
- 产品侧 `data/candidate/themes.ts` 的父子树与 `childrenOf()`。

### CHANGE（必须修改 —— 本轮已做的最小项）

- **新增** `research/research/methodology/theme_campaign_separation_v1.md`：
  Theme / Campaign Separation Rules + Campaign Independence Gate（研究层判据，不含新实体）。
- **新增** `docs/THEME_CAMPAIGN_MODEL_AUDIT.md`（本文）。
- **在两份既有方法论文档各加一条指针**（`research_model_v1_0.md` §3、`theme_lifecycle_v0_2.md` §3），
  并**修正 `theme_lifecycle_v0_2.md` §9 的乱码**。
- **不**修改任何 schema / DB 数据 / export 数据 / 历史结论。

### DEFER（暂时不要做）

- ❌ Timeline 从「Sub-theme 一行」改为「Macro Theme 一行」（F5）—— 需先设计下钻交互。
- ❌ adapter 透传 `theme_type` / `theme_cycle_id`（F4）—— 与 F5 一并做才有意义。
- ❌ 医药健康历史数据录入 / 医药 Campaign 生产（本轮只做模型验证）。
- ❌ `theme_cycles` / `campaign_relations` 建表（维持 research-level）。
- ❌ 统一 DB `phase_type` 与 export `lifecycle` 枚举（F6）—— 破坏性变更。
- ❌ 一切 §十六 所列禁区（实时行情 / 资金流 / 技术指标 / 荐股 / 买卖信号 / 胜率 /
  seasonality / prediction / radar / notification / backend / 大规模重标 / 大规模补数据）。

---

## 10. 八问结论（Final Summary）

| # | 问题 | 结论 |
|---|---|---|
| 1 | 当前 ThreeC 是否已基本支持「一个 Macro Theme → 多 Campaign」？ | ✅ **是**。DB `themes.parent_theme_id`（TH-AUTO 挂 8 个 Campaign）+ 产品 `data/candidate/themes.ts` 父子树 + `childrenOf()` 均已支持；但「Macro Theme / Sub-theme」**术语与研究判据未成文**（本轮补齐） |
| 2 | 汽车现有模型哪些地方已经正确？ | 2019/2020/2021 独立年度 Campaign；**2022 单 Campaign + 内部 Phase**（多催化不拆）；**2023 一 Cycle 两 Campaign**（Drift + Overlap）；2024 V2X/Robotaxi 双独立；2024 次级段保持 Candidate；2025 未过度拆分 |
| 3 | 汽车哪些地方需要修正？ | **历史数据不需要修正**。需修正的是**文档层**：术语缺失（F1）、Gate 未形式化（F2）、乱码（F3）。可选代码层 F4/F5 属 DEFER |
| 4 | 医药健康是否可以作为第二个 Macro Theme？ | ✅ **可以**，且**结构上已就绪**：`th_pharma 医药` 已在产品主题树注册（sector 级），`rule_pharma_post_interim` 与 `rule_pharma_year` 已是候选规则。**但没有任何行情/证据数据** |
| 5 | 医药 2019–2021 是否适合用「Theme Cycle + Multiple Campaigns」表达？ | ⚠ **方法论上更自然（成立）**：2019–2021 结构性重估与疫情医疗**时间交织**，Cycle 允许多年+重叠，可避免按日历年的伪切分。**但是否真成立，必须由真实数据经 Q1–Q5 判定** —— 本轮不判定、不录数据 |
| 6 | 当前 Schema 是否足以支撑该模型？ | ✅ **足够**。`themes.parent_theme_id` = Macro/Sub 层级；`campaign_themes.role` = 多对多；`theme_cycle_id` = 研究层 cycle（contract §11 已定义）；overlap 用时间区间 + research 记录表达。**无需新表/新必填字段** |
| 7 | 是否必须修改产品 UI？ | ❌ **不必须**。现状（Sub-theme 成行）不错误、可用。把它改为「Macro Theme 成行 + 下钻」是**增强**，属 DEFER |
| 8 | 下一步最值得做的唯一一件事？ | **把本轮新增的 `theme_campaign_separation_v1.md` 作为方法论基线，交人工确认**；确认后再单独立项做「Timeline 以 Macro Theme 为主单位 + Sub-theme 下钻」（F4+F5 一起） |

### 最终判断

> **ThreeC 已经形成一个可以持续扩展到汽车、医药健康以及未来其他 Macro Theme 的统一历史机会建模框架。**
>
> 支撑它的是三层现成结构：**研究层的 ThemeCycle + Drift + Overlap 规则**、
> **数据层的 `themes.parent_theme_id` + `campaign_themes`**、
> **产品层的 `data/candidate/themes.ts` 父子树**。
> 本轮补齐的是**唯一缺失的一块 —— 把「Macro Theme / Sub-theme / Campaign」的边界与
> 「Campaign Independence Gate」写成可交接的成文规则**。
>
> 需要人工决策的是**产品表达**（Timeline 是否从 Sub-theme 行升到 Macro Theme 行），
> 而不是**研究方法** —— 研究方法已经自洽。

---

*本审计为只读 + 文档级变更；未修改 schema / DB 数据 / export 数据 / 历史研究结论 / Timeline 行为。
配套方法论见 `research/research/methodology/theme_campaign_separation_v1.md`。*
