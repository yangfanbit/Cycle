# Macro Theme 归属规则：单一 Primary + Related（v0.1）

> | 项目 | 值 |
> |---|---|
> | 文件性质 | **Research Layer 数据判定规则**（不是 Product schema / export contract） |
> | 轮次 | `macro-theme-primary-related-v0.1` |
> | 确立日期 | 2026-09-17（Wave 1A — 电力设备历史 Cycle） |
> | 适用范围 | 任何**新补录**的历史 Theme Cycle / Campaign / Research Candidate |
> | 不改变 | `schema/schema.sql` · `contracts/` · Research Model v1.0 · export contract · Product |
>
> 本文档只定义**研究侧判定规则**，不新增数据库实体，不新增字段。

---

## 0. 为什么需要这条规则

`Historical Coverage Audit v0.1`（2026-09-16）指出：历史侧只有 2 个 Macro Theme，
而 Current Candidate 侧已声明 4 个 → 3 个主题存在**结构性断裂**。

补录新主题时出现的第一个风险是：**同一轮历史行情同时覆盖多个产业**
（最典型的是 2020–2021「新能源」同时触及**光伏/风电/储能**与**车用动力电池/整车**）。

若不约束，同一轮行情会被同时计入「电力设备」与「汽车」两个 Macro Theme，
从而**虚增独立样本数**，直接污染：

- `theme_family_count`（Time Observation 的跨族稳健性）
- Time Observation 的 `N`（独立观察对象计数）
- Structural Analogy 的跨族独立性判断

---

## 1. 规则

### R1 — 每个 Theme Cycle 有且只有一个 Primary Macro Theme

Primary 用于：

- Theme Family 统计
- `theme_family_count`
- Time Observation 的独立样本计数（`N`）
- Structural Analogy 的跨族独立性判断

### R2 — Related Macro Theme 可以存在，但不增加独立样本数

一个 Cycle 可表达多个 `related macro themes`（用于记录产业交叉），
但 Related **不**贡献 `theme_family_count`，**不**贡献 `N`。

### R3 — Primary 的判定依据（按优先级）

**不按**股价涨幅、新闻数量或概念标签决定。依据：

1. **核心研究对象** —— 该 Cycle 讲的是哪个产业环节
2. **生命周期主体** —— 代表标的与 Peak 由谁决定
3. **主要政策 / 产业驱动** —— 驱动变量属于哪条产业链
4. **当时 Theme Cycle 的叙事中心** —— 市场当时在讨论什么

### R4 — 无法判断时不强行归类

若证据不足以判断 Primary → 标记 `AMBIGUOUS` / `UNKNOWN`，并说明原因。
**禁止**为了归类而选择"看起来更合适"的一侧。

### R5 — 时间重叠 ≠ 必须合并，但必须证明独立性

两个时间上重叠的 Cycle 可以同时存在，但必须**分别证明**：

- 独立的形成锚点
- 独立的核心驱动
- 独立的生命周期（Peak / 区间不同）

**不能**只是同一轮行情的不同子行业切片。

### R6 — `N` 按独立 Theme Cycle 计，不按 Theme 标签数计

一个 Cycle 即使同时拥有 AUTO + POWER 两个关联标签，仍然只贡献 `N = 1`。

### R7 — `theme_family_count` 只统计 Primary Macro Theme

Related Macro Theme **不**计入。

---

## 2. 实现约束（实测，2026-09-17）

规则 R1 / R2 在本仓库中**不需要也不允许**改 schema —— 现有 `campaign_themes`
已经可以表达 Primary，但**不能**表达第二个 Related Macro Theme 而不污染 CMTR。
原因如下（三处实测证据）：

### 2.1 CMTR v1 对对象 `themes[]` **全量**解析根节点

`research/scripts/theme_taxonomy.py`：

```python
def resolve_object(self, obj):
    names = [t.get("name") for t in (obj.get("themes") or [])]
    return self.resolve_names(names)      # ← 不看 role，全部参与解析
```

→ 一个 Campaign 若挂接 **≥2 个** Macro root（如「电力设备」+「汽车」），
CMTR 判为 **`CONFLICT`**，`macro_theme_id_of()` 返回 `None`（**不可归属，不得任选其一**）。

### 2.2 `theme_family_id` 在多根时为 `None`

`research/scripts/discover_time_observation_patterns.py`：

```python
"theme_family_id": fam_ids[0] if len(fam_ids) == 1 else None,
```

→ CONFLICT 对象**不进入任何主题族**，既不贡献 `theme_family_count`，
也不参与跨族独立性判断。**这不是"少算一个"，而是"整个对象被排除"**。

### 2.3 Product 侧的 Macro Theme 读取约定

`src/data/timeline/researchAttention.ts`：

```ts
const macro = (campaign.themes ?? []).find(
  (t) => t.role === 'related' && (t.theme_type === 'industry' || t.theme_type === 'sector'),
);
```

→ Product 侧把 **`role='related'` 且 `theme_type ∈ {industry, sector}`** 的那一行
当作 Macro Theme。**沿用既有约定，无需新增字段。**

### 2.4 因此的落地方式

| 表达对象 | 落地位置 |
|---|---|
| **Primary Macro Theme** | `campaign_themes` 一行：`role='related'` + `theme_type='industry'`（既有约定） |
| Cycle 的 `main` 主题 | `campaign_themes` 一行：`role='main'` + 子主题（`concept`） |
| **Related Macro Theme** | **不写入 `campaign_themes`**；记录在研究层文档：`campaigns.research_notes` + export `drivers` + 本轮报告 |

**结论**：`campaign_themes` **能**表达 Primary（复用既有 `role='related'` + industry 约定），
**不能**表达 Related Macro Theme 而不破坏 CMTR → Related 走研究层文档，**未改 schema**。

---

## 3. 已裁决案例

### 3.1 Wave 1A — 电力设备（2026-09-17）

| Cycle | Primary | Related | 裁决依据 |
|---|---|---|---|
| `power_ne_equipment_2020_2022`（清洁能源发电设备） | `TH-POWER` 电力设备 | **无** | 核心研究对象 = 光伏硅片/组件、逆变器、风电整机；驱动 = 双碳目标 / 平价上网 / 整县推进；代表标的 = 隆基绿能 / 阳光电源 / 金风科技 |
| `power_grid_uhv_2022_2025`（电网投资与特高压） | `TH-POWER` 电力设备 | **无** | 核心研究对象 = 特高压 / 直流输电 / 高压开关 / 电网自动化；驱动 = 电网工程投资与特高压建设节奏；代表标的 = 国电南瑞 / 许继电气 / 平高电气 |

### 3.2 ★ 2020–2021「新能源」重叠裁决（本规则的关键应用）

2020–2021 的「新能源」大行情同时触及发电设备与车用动力电池。
按 R3 / R5 逐项裁决：

| 维度 | `C-2020-NEV` / `C-2021-NEV`（既有） | `C-2020-POWER-NE`（本轮新增） |
|---|---|---|
| **核心研究对象** | 特斯拉国产化、整车、动力电池（车用） | 光伏硅片/组件、逆变器、风电整机（发电设备） |
| **代表标的** | 比亚迪、宁德时代、江淮、旭升 | 隆基绿能、阳光电源、金风科技 |
| **主要政策/产业驱动** | 新能源车补贴、双积分、特斯拉国产化 | 双碳目标、平价上网、整县推进分布式光伏 |
| **叙事中心** | 「车」的电动化与智能化 | 「电」的生产与装机 |
| **生命周期（Peak）** | `C-2020-NEV` **2020-07-13**；`C-2021-NEV` **2021-08-06** | **2021-10-27 ~ 2021-11-04** |
| **结论** | Primary = `TH-AUTO` | Primary = `TH-POWER` |

**裁决：两者 Primary 不同，且 Peak 不同 → 生命周期独立 → 允许并存，互不贡献对方的 `N`。**
它们**不是**同一轮行情的两个子行业切片：Peak 相差 3~4 个月，
且驱动变量（车用补贴 vs 发电装机政策）分属两条政策链。

### 3.3 明确**不**另立 Cycle 的情形（同 Cycle 内的环节错位）

| 现象 | 处理 | 依据 |
|---|---|---|
| 硅料环节（特变电工-新特能源）延后至 **2022-07-05** 见顶，中下游 2021-11 见顶 | 记入 `C-2020-POWER-NE` 的 `research_notes` / `drivers`，**不另立 Cycle** | 核心研究对象、驱动、叙事中心均相同，仅产业链环节节奏不同 → 不满足 R5 的「独立核心驱动」 |
| 出海环节（思源电气 2025-12-26、特变电工 2025-11-07）延后见顶，特高压国内标的 2024-10 见顶 | 记入 `C-2022-POWER-GRID` 的 `research_notes` / `drivers`，**不另立 Cycle** | 驱动同为「电网投资」，属结构分化而非独立周期 |

### 3.4 未出现 `AMBIGUOUS` 的说明

本轮 2 个 Cycle 的 Primary 判定均有**代表标的 + 驱动变量 + Peak** 三重独立证据，
不存在需要标记 `AMBIGUOUS` / `UNKNOWN` 的情形。

---

## 4. 诚实限制

1. 本文档定义的是**研究侧判定规则**；它**不改变** `schema.sql` / export contract / Product。
2. Related Macro Theme 目前**只存在于研究层文档**，产品侧不可见 ——
   这是 R1 与 CMTR 现状共同决定的，**不是遗漏**。
3. 若未来需要让 Related Macro Theme 在产品侧可见，
   必须先解决 §2.1 的 CMTR 全量解析问题（属模型层决策，须走独立轮次）。
4. `AMBIGUOUS` / `UNKNOWN` 是**允许的结论**，不是失败。

---

*Macro Theme Primary/Related Rule v0.1 · 2026-09-17 · Wave 1A*
