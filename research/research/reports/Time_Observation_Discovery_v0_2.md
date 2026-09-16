# Time Observation Discovery v0.2

> **全量历史数据扫描 · 时间影响 / 时间节奏 / 日历驱动结构**
>
> | 项目 | 值 |
> |---|---|
> | 文件性质 | **Research Layer Deliverable**（研究层交付物） |
> | 轮次 | `time-observation-discovery-v0.2` |
> | 规则集 | `time-observation-discovery-0.2` |
> | 快照日期 | 2026-09-16 |
> | 生成器 | `research/scripts/discover_time_observation_patterns.py` |
> | 输入（只读） | `exports/timeline_export_v1.json` + `research/database/cycle_research.db` |
> | 产物 | `time_observation_candidate_pool_v0_2.json` / `.csv` |
>
> **本阶段未修改** `src/` / Timeline UI / `timeline_export_v1.json` / Research Model schema / DB schema / contracts。
> **未接入产品运行时**。`RESEARCH_ONLY` 与 `REJECTED` 一律不得进入 Timeline。

---

## 1. Executive Summary

### 1.1 核心结论

对 ThreeC 全部 2018–2025 历史数据做统一扫描（**191 个候选、94 个独立样本**），结论是：

> **全量扫描确认：数据集中只有 1 个可复现的时间结构 —— 汽车主题族「研究观察起点」集中在每年 5 月下旬 ~ 6 月下旬（TOP-01）。**
> **除此之外，没有任何其他结构在通过数值门槛之后，还能通过「口径稳健性」检验。**

关键数据：

| 层级 | 数量 |
|---|---|
| 扫描候选（scan space） | **191** |
| 独立样本（distinct member sets） | **94** |
| 通过数值门槛 → `TIMELINE_CANDIDATE` | **5** |
| 通过口径稳健性检验 → `effective TIMELINE_CANDIDATE` | **2** |
| 归并后**独立结构数** | **1** |

### 1.2 三个最重要的发现

**发现一：TOP-01 是唯一稳健的结构，且它的稳健性恰好来自"它只依赖汽车族"。**

EARLY_SIGNAL 在两种 scope 定义下判定一致（均 `TIMELINE_CANDIDATE`、均 `STABLE`）：

| scope | N | 中心 | 窗口 | 复现 | 集中度 | 漂移 | LOO |
|---|---|---|---|---|---|---|---|
| `rule_auto_summer` | 7 | 06-11 | 05-27 ~ 06-26 | 5/7 | 0.4018 | STABLE | 5d |
| Macro Theme「汽车」 | 6 | 06-06 | 05-29 ~ 06-14 | 4/6 | 0.2148 | STABLE | 5d |

**发现二：另外 3 个"通过门槛"的候选，其结论随 scope 定义翻转 → 判定脆弱，必须降级。**

| 候选 | rule 口径 | Macro Theme 口径 | 结论 |
|---|---|---|---|
| MAIN_RISE | `TIMELINE_CANDIDATE` / STABLE | `EXPLORATORY` / MILD_DRIFT | ⚠️ FRAGILE |
| PEAK | `EXPLORATORY` / STRONG_DRIFT | `TIMELINE_CANDIDATE` / STABLE | ⚠️ FRAGILE |
| MAIN_RISE→PEAK | `EXPLORATORY` / MILD_DRIFT | `TIMELINE_CANDIDATE` / STABLE | ⚠️ FRAGILE |

两种口径的**唯一差别**是：`C-2019-AD` 未挂接 Macro Theme（taxonomy 缺口），因此被 Macro Theme scope 排除。
**换句话说，这三个候选的判定由"2019 年是否入样"决定 —— 而入样与否来自一个数据挂接缺口，不是有原则的筛选规则。** 这种判定不能当作稳定规律。

**发现三：所谓"生命周期节奏"是派生的，不是独立证据。**

扫描了全部阶段迁移（`EARLY_SIGNAL→THEME_FORMING`、`MAIN_RISE→PEAK` 等 8 类 + DB 口径 3 类），发现：

| 阶段 | 中心 | 相对 EARLY_SIGNAL 中位滞后 | 预测中心 | 残差 | 是否派生 |
|---|---|---|---|---|---|
| THEME_FORMING | 06-14 | +9 d | 06-20 | 6 d | **派生** |
| BROAD_CONFIRMATION | 06-29 | +25 d | 07-06 | 7 d | **派生** |
| MAIN_RISE | 06-22 | +10 d | 06-21 | 1 d | **派生** |
| PEAK | 07-11 | +40 d | 07-21 | 10 d | **派生** |
| SECONDARY | 08-12 | +68.5 d | 08-18 | 6.5 d | **派生** |
| DECLINING | 08-04 | +61.5 d | 08-12 | 7.5 d | **派生** |
| MAIN_END | 08-31 | +70 d | 08-20 | 11 d | **派生** |

**7/7 全部为派生**（残差 ≤ 11 天）。也就是说：阶段迁移的"时间节奏"完全等于「EARLY_SIGNAL 的聚集 + 典型 Campaign 时长」，
**不构成独立的时间规律**。这一点必须写进任何后续产品文案 —— 否则会把同一事实重复计数成多个"规律"。

### 1.3 必须同时说明的否定性结论

1. **全市场层面不成立**：`全部历史对象 · EARLY_SIGNAL`（N=7）→ **REJECTED**（集中度 0.6247、IQR 92.5 天）。
   6 月集中**不是** A 股主题的普遍规律，只是汽车族的现象。
2. **医药族不成立**：医药是数据集中**唯一**跨年重复的 Theme Cycle，但其全部候选为 `INSUFFICIENT_DATA` / `REJECTED`
   （LOO 位移 334–352 天 → 完全由单一年份决定）。**主题重复 ≠ 时间规律**。
3. **不是农历规律**：春节相对偏移跨度 85–191 天（106 天）。绝对日序比率 0.4018 vs 春节偏移比率 0.3872，
   差异不足 20% → 判定 `INCONCLUSIVE_SIMILAR`：**两者都不构成集中**。
4. **不是季节需求**：全部候选**没有一条**被归为 `SEASONAL_DEMAND`。找到的是日历规律，不是季节规律。
5. **"最显著的 p"不是"最稳健的候选"**：唯一通过 Bonferroni 校正（阈值 0.000262）的独立样本是 `MAIN_RISE`（N=6），
   但它 `MILD_DRIFT` → `EXPLORATORY`。这正好证明**p 值不能单独作为晋级依据**。

---

## 2. Dataset Scope

### 2.1 数据面（实测）

| 项目 | 值 |
|---|---|
| 时间范围 | 2018-01-01 ~ 2025-12-31 |
| 有观测的年份 | 2019, 2020, 2021, 2022, 2023, 2024, 2025（**7 年**） |
| 排除年 | 2018（`no_clear_campaign`，无 Campaign） |
| Theme Cycles | **9** |
| Campaigns | **9** |
| Research Candidates | **4** |
| 研究对象合计 | **13** |
| Anchor 记录（对象 × lifecycle 阶段） | **72** |
| 阶段迁移记录（export 口径） | **49** |
| DB campaign_phases 记录 | **35** |
| 事件记录 | **33** |
| 事件类型 | `policy` / `company` / `market` / `macro` |
| Macro Theme（主题族） | **2**（汽车 / 医药健康） |
| 子主题 | 10 |

### 2.2 三个分析层次（Layer A / B / C）

**Layer A — Theme / Theme Family**

- 沿用仓库既有 taxonomy（`themes` 表 + `research_rules` 表），**未新建 taxonomy**。
- 扫描 scope 共 4 类：`THEME_FAMILY`（2）、`RULE`（2）、`THEME`（10，已排除与 Macro Theme 重叠者）、`ALL`（1）。
- 主题族映射：`TH-AUTO` =「汽车」、`TH-PHARMA` =「医药健康」（均为 `parent_theme_id IS NULL`）。

**Layer B — Lifecycle**

仓库真实 lifecycle 阶段（`contracts/timeline_export_v1.md` 定义，实测覆盖率）：

| 阶段 | 出现对象数 |
|---|---|
| `EARLY_SIGNAL` | **13 / 13**（全覆盖） |
| `MAIN_RISE` | 10 |
| `PEAK` | 11 |
| `MAIN_END` | 11 |
| `DECLINING` | 7 |
| `THEME_FORMING` | 6 |
| `BROAD_CONFIRMATION` | 6 |
| `SECONDARY` | 4 |
| `RETRACEMENT` | 2 |
| `FIRST_DECLINE` | 1 |

> ⚠️ 注意：任务书列出的 `EXPANSION` / `WEAKENING` 在仓库中**不存在**。仓库使用的是
> `MAIN_RISE` / `DECLINING` / `RETRACEMENT` / `SECONDARY`。本报告**以仓库真实定义为准**。

DB 侧另有独立口径 `campaign_phases.phase_type`：`startup` / `acceleration` / `main_rise` / `diffusion` /
`retracement` / `secondary_rally` / `decline`（共 23 行，9 个 Campaign）。两套口径**分别独立扫描**，未混用。

**Layer C — Event / Evidence Dates**

- 事件 33 条（`export.events`），按 `event_type` 分 4 类扫描。
- 时间防火墙：仅使用事件自身的 `date`，**不引入任何事件之后的未来信息**；机制解释全部标注为「事后可查公开记录」。

### 2.3 样本量现实（必须先讲清楚）

> **本数据集的根本限制：只有 2 个 Macro Theme。**
>
> 这意味着 `theme_family_count` 的最大可能值是 2。任何单族规律都无法获得真正的"跨主题族独立性"。
> 这是本报告所有结论的天花板，也是 §18 要求诚实标注的部分。

---

## 3. Methodology

### 3.1 统一 Anchor 体系

严格优先级（与 `src/data/timeline/preObservation.ts` 同口径，不另立标准）：

```
EARLY_SIGNAL.start  →  THEME_FORMING.start  →  BROAD_CONFIRMATION.start  →  Campaign.start
```

**关键设计：本脚本对每个 lifecycle 阶段分别扫描**，因此同时覆盖：

```
A. start / formation      → EARLY_SIGNAL / THEME_FORMING
B. broad confirmation     → BROAD_CONFIRMATION
C. expansion              → MAIN_RISE
D. peak                   → PEAK
E. weakening / decline    → DECLINING / RETRACEMENT / SECONDARY / MAIN_END
F. 阶段迁移               → 8 类 export transition + 3 类 DB transition
```

### 3.2 Day-of-Year 与环形处理

- 所有日期 → `day_of_year`（**闰年归一**：3 月 1 日起 −1），使 06-18 跨年可比。
- **环形（circular）跨度**：`span = 365 − 最大间隙`。当环形跨度比线性跨度小 30 天以上时，改用环形口径。
  → 支持识别跨年簇（如 12 月下旬 ~ 1 月上旬），**不会错误拆成两个无关窗口**。

### 3.3 绝对 vs 相对（v0.2 关键升级）

每个候选同时计算两套特征并判定谁更有解释力：

| 特征 | 定义 |
|---|---|
| **Absolute** | `day_of_year` → `ABSOLUTE_CALENDAR` |
| **Relative** | 相对**春节 / 国庆 / 五一**的 `offset_days` → `EVENT_RELATIVE` |

**判定规则（含 20% 优势门槛，避免技术性胜出）**：

```
best_relative_ratio ≤ 0.8 × absolute_ratio   → EVENT_RELATIVE
absolute_ratio     ≤ 0.8 × best_relative_ratio → ABSOLUTE_CALENDAR
否则                                          → INCONCLUSIVE_SIMILAR（两者都不集中）
```

全量结果分布：`INCONCLUSIVE_SIMILAR` 61、`EVENT_RELATIVE` 7、`ABSOLUTE_CALENDAR` 2、其余 121（N<3 不判定）。
**TOP-01 落于 `INCONCLUSIVE_SIMILAR`** —— 这是"既不是强日历规律、也不是农历规律"的量化表述。

### 3.4 统计量（延续 v0.1 口径）

| 统计量 | 定义 |
|---|---|
| `center` | 中位数日序（抗离群） |
| `window` | `Median ± 1×MAD×1.4826`（浮点 MAD，不先取整） |
| `concentration_ratio` | 观测跨度 ÷ 均匀期望跨度 `(N-1)/(N+1)×365` |
| `concentration_p_analytic` | **解析式** `P(range ≤ s) = N·r^(N-1) − (N-1)·r^N`，`r = s/365` |
| `recurrence` | 落入窗口年数 ÷ 有效年数（**只描述过去**） |
| `stability.front_back` | 前后半段中位位移：<21d STABLE / 21–44d MILD_DRIFT / ≥45d STRONG_DRIFT |
| `loo_max_shift_days` | 逐点剔除后中心最大位移；≥45d → `single_year_dominance` |
| `theme_family_count` / `theme_cycle_count` / `campaign_count` | 独立性三重计数 |

> **p 值用解析式而非随机模拟**，因此无随机数、可逐字节复现。p 仅作发现阶段诊断，**不是确认性检验**。

### 3.5 年度去重（防伪重复）

同一日历年、同一 scope 内**只取最早锚点**。例如 2024 年汽车族有 3 个对象
（`C-2024-V2X` 06-11 / `C-2024-ROBOTAXI` 07-08 / `RC-2024-SECONDARY` 09-05）→ 只计 06-11 一次。
**不这样做会把 N 从 7 抬到 9，人为放大样本。**

---

## 4. Pattern Types

六类 Pattern 的扫描结果：

| Pattern 类型 | 候选数 | 说明 |
|---|---|---|
| `PHASE_TRANSITION` | **115** | 阶段起点与阶段迁移（数量最多，因每个 scope × 每个阶段组合都扫） |
| `CALENDAR_DRIVEN` | **64** | 制度性 / 政策 / 财报日历驱动 |
| `UNKNOWN` | 9 | 机制无法归类（多为 N<3） |
| `HOLIDAY_RELATIVE` | **2** | 相对节假日优势 ≥20% 且 N≥4 |
| `SEASONAL` | **1** | 仅 1 条（`TOPC-033` 医药·`DECLINING`，N=2）→ 实为 `INSUFFICIENT_DATA`，不构成证据 |
| `INDUSTRY_EVENT_DRIVEN` | **0** | ⚠️ 见下 |
| `DATA_RELEASE_DRIVEN` | **0** | ⚠️ 见下 |

### 4.1 两类"零结果"是有效研究结果

**`INDUSTRY_EVENT_DRIVEN` = 0**：仓库内**没有结构化的行业事件日历**（车展 / CES / MWC / 发布会季）。
33 条事件中 `company` 类 15 条，但都是单次公司事件，不构成"年度固定行业事件"。
→ **数据不足，无法研究**。按 §三十 记录为 `INSUFFICIENT_DATA`，**不硬造**。

**`DATA_RELEASE_DRIVEN` = 0**：仓库内**没有产销 / 库存 / 价格 / 出口 / PMI / 景气数据的发布日期字段**。
`market_daily` 是行情数据，不是"数据发布日历"。
→ **数据不足，无法研究**。机制上只能作为"假设"（见 §13），不能作为 `data-supported mechanism`。

### 4.2 机制词汇表使用情况

| 机制 | 使用 |
|---|---|
| `CALENDAR_DRIVEN` | ✅ 汽车族主力 |
| `POLICY_CADENCE` | ✅ 汽车族（政策节奏） |
| `REPORTING_CADENCE` | ✅ 汽车族（中报预告日历） |
| `DATA_RELEASE_CADENCE` | ✅ 仅作为假设 |
| `PHASE_TRANSITION` | ✅ 迁移类候选 |
| `HOLIDAY_RELATIVE` | ⚠️ 仅 2 条（DECLINING，N=4） |
| `INDUSTRY_EVENT_CADENCE` | ⚠️ 仅作为假设 |
| `SEASONAL_DEMAND` | ❌ **零使用** |
| `UNKNOWN` | ✅ 9 条 |

---

## 5. Candidate Discovery

### 5.1 扫描漏斗

```
全部历史数据（9 Cycle / 13 对象 / 72 anchor / 49 transition / 33 event）
        ↓  统一 Anchor + Lifecycle + Event 数据集
   扫描空间 191 个候选（94 个独立样本）
        ↓  样本量门槛 N ≥ 3
      70 个候选
        ↓  窗口可构建 + LOO + 稳定性 + 集中度
   数值门槛通过 → 5 个 TIMELINE_CANDIDATE
        ↓  口径稳健性检验（rule ↔ Macro Theme）
   有效候选 → 2 条（TOPC-018 / TOPC-001）
        ↓  样本重叠归并
   独立结构 → 1 个
```

### 5.2 状态分布

| promotion_status | 数值门槛 | **effective（最终）** |
|---|---|---|
| `TIMELINE_CANDIDATE` | 5 | **2** |
| `EXPLORATORY` | 43 | **46** |
| `RESEARCH_ONLY` | 12 | 12 |
| `REJECTED` | 10 | 10 |
| `INSUFFICIENT_DATA` | 121 | 121 |
| **合计** | **191** | **191** |

### 5.3 扫描地图（§二十七）

**Pattern Type × Status**

| Pattern Type | TIMELINE | EXPLORATORY | RESEARCH_ONLY | REJECTED | INSUFFICIENT | 合计 |
|---|---|---|---|---|---|---|
| `PHASE_TRANSITION` | 1 | 23 | 7 | 5 | 79 | **115** |
| `CALENDAR_DRIVEN` | 4 | 15 | 5 | 5 | 35 | **64** |
| `UNKNOWN` | 0 | 3 | 0 | 0 | 6 | **9** |
| `HOLIDAY_RELATIVE` | 0 | 2 | 0 | 0 | 0 | **2** |
| `SEASONAL` | 0 | 0 | 0 | 0 | 1 | **1** |
| **合计** | **5** | **43** | **12** | **10** | **121** | **191** |

**Scope Type × Status**

| Scope Type | 候选数 | TIMELINE | EXPLORATORY | RESEARCH_ONLY | REJECTED | INSUFFICIENT |
|---|---|---|---|---|---|---|
| `THEME` | 58 | 0 | 4 | 0 | 1 | 53 |
| `RULE` | 50 | 2 | 17 | 0 | 2 | 29 |
| `THEME_FAMILY` | 50 | 3 | 16 | 0 | 0 | 31 |
| `ALL` | 28 | 0 | 3 | 11 | 7 | 7 |
| `EVENT_TYPE` | 5 | 0 | 3 | 1 | 0 | 1 |

> 注意 `ALL` scope 的 28 条候选**没有一条**通过 —— 这正是"跨族后规律消失"的体现。

**主题族 × 候选数**：`TH-AUTO` 家族占绝大多数候选；`TH-PHARMA` 家族候选几乎全部为 `INSUFFICIENT_DATA`（N≤3）。

---

## 6. Promotion Gate

### 6.1 门槛定义（与 v0.1 连续，未放宽）

```
INSUFFICIENT_DATA : N < 3
REJECTED          : 单年主导（LOO 中心位移 ≥ 45d）或 IQR > 90d（窗口不可构建）
RESEARCH_ONLY     : N ≥ 5 但集中度 > 0.60；或 3–4 且集中度不足
EXPLORATORY       : 窗口可构建且集中度尚可，但样本 / 稳定性 / 独立性 / 机制未全部达门槛
TIMELINE_CANDIDATE: N ≥ 5 且 窗口可构建 且 集中度 ≤ 0.45 且 STABLE
                    且 无单年主导 且 theme_cycle_count ≥ 3 且 机制置信度 ≥ MEDIUM
```

**附加规则**：
1. **事件类型候选一律不得成为 `TIMELINE_CANDIDATE`** —— 事件台账本身是研究样本的一部分，存在选择偏差。
2. **`N ≥ 5` ≠ 自动进入 Timeline。**
3. **v0.2 新增：口径稳健性检验。** 数值门槛通过后，还必须通过与"同一主题族另一种 scope 定义"的一致性检验（见 §6.2）。

### 6.2 v0.2 新增的关键筛选：口径稳健性

这是本轮**最重要的方法学增量**。

**问题**：数据集中 `rule_auto_summer` 与 Macro Theme「汽车」在语义上是同一主题族，但成员不同 ——
`C-2019-AD` 的 `themes` 只有「智能驾驶/无人驾驶」，**没有挂接 Macro Theme「汽车」**（taxonomy 缺口），
因此 Macro Theme scope 排除了 2019 年。

**后果**：同一现象在两种口径下得到**不同判定**。这说明判定依赖"2019 年是否入样"，
而这个入样由**数据挂接缺口**决定，不是有原则的筛选规则。

**检验结果**：

| 指标 | 值 |
|---|---|
| 比较的 scope 变体对 | 50 |
| 判定一致（稳健） | 45 |
| **判定不一致（脆弱）** | **5** |
| 其中涉及 TIMELINE_CANDIDATE 的 | **3** |

**脆弱配对明细**：

| 阶段 | 指标 | rule 口径 | Macro Theme 口径 |
|---|---|---|---|
| `MAIN_RISE` | status / drift | TIMELINE_CANDIDATE / STABLE | EXPLORATORY / MILD_DRIFT |
| `PEAK` | status / drift | EXPLORATORY / STRONG_DRIFT | TIMELINE_CANDIDATE / STABLE |
| `MAIN_RISE→PEAK` | status / drift | EXPLORATORY / MILD_DRIFT | TIMELINE_CANDIDATE / STABLE |

**处理**：这 3 条从 `TIMELINE_CANDIDATE` **降级为 `EXPLORATORY`**（记入 `effective_promotion_status`，
并保留原始 `promotion_status` 与降级原因，**不静默覆盖**）。

**这暴露了一个真实的架构问题**（记录，未修改产品代码）：Macro Theme 与 Theme Cycle 之间缺少稳定映射键，
导致"同一主题族"有两种不等价的成员集合。**要解决它，需要一个显式的「主题族 ↔ rule / theme」定义表**（模型层决策）。

---

## 7. Strong Candidates

### 7.1 TOP-01（有效 · 稳健）★

| 字段 | 值 |
|---|---|
| **pattern_id** | `TOPC-018` |
| scope | `RULE` / `rule_auto_summer` |
| lifecycle_stage | `EARLY_SIGNAL` |
| N | **7**（2019–2025） |
| 中心 | **06-11** |
| 窗口 | **05-27 ~ 06-26**（31 天，宽窗口） |
| 集中度比率 | 0.4018 |
| 解析 p | 0.00389 |
| 复现 | **5 / 7**（命中 2020/2021/2023/2024/2025；未命中 2019/2022） |
| 前后半段 | **STABLE**（位移 +10.5 d） |
| LOO | 最大位移 **5 d** → 无单年主导 |
| 主题族 / Cycle 数 | **1 / 7** |
| 机制 | `CALENDAR_DRIVEN` + `POLICY_CADENCE` + `REPORTING_CADENCE` + `DATA_RELEASE_CADENCE`（置信度 MEDIUM） |
| 绝对 vs 相对 | `INCONCLUSIVE_SIMILAR` |
| 口径稳健性 | **ROBUST** |
| **有效状态** | **`TIMELINE_CANDIDATE`** |

**来源记录（可回溯到 Campaign）**：

| 年 | Campaign | Anchor | 日期 |
|---|---|---|---|
| 2019 | `C-2019-AD` | EARLY_SIGNAL | 2019-08-15 |
| 2020 | `C-2020-NEV` | EARLY_SIGNAL | 2020-06-01 |
| 2021 | `C-2021-NEV` | EARLY_SIGNAL | 2021-06-01 |
| 2022 | `C-2022-POLICY` | EARLY_SIGNAL | 2022-04-27 |
| 2023 | `C-2023-AD` | EARLY_SIGNAL | 2023-06-12 |
| 2024 | `C-2024-V2X` | EARLY_SIGNAL | 2024-06-11 |
| 2025 | `C-2025-ROBOTAXI` | EARLY_SIGNAL | 2025-06-22 |

**限制（必须随结论一起呈现）**：

1. **仅 1 个 Macro Theme 驱动** → `theme_family_count = 1`。**不能表述为"A 股主题的普遍规律"**，只能说"汽车主题族"。
2. 全部锚点为研究候选日期，`verification_method = unknown`（未经行情人工核验）→ 数据质量上限 MEDIUM。
3. **存在研究样本选择偏差**：ThreeC 自建事件台账 6 月占比 33%（均匀 8.3%）→ 任何 6 月偏好都部分来自研究样本本身。
4. 绝对与相对特征**都不构成集中**（跨度约 106 天）→ 不得表述为"6 月季节性"，也不得表述为"春节后第 N 天"。
5. 幸存者偏差无法消除（见 §12）。

### 7.2 TOP-01 的口径变体（有效 · 稳健）

| 字段 | 值 |
|---|---|
| **pattern_id** | `TOPC-001` |
| scope | `THEME_FAMILY` / `TH-AUTO` |
| N | 6（2020–2025，**不含 2019**） |
| 中心 | 06-06 |
| 窗口 | 05-29 ~ 06-14（17 天） |
| 集中度比率 | **0.2148** |
| 复现 | 4 / 6 |
| 前后半段 / LOO | STABLE / 5 d |
| 绝对 vs 相对 | `ABSOLUTE_CALENDAR` |
| 口径稳健性 | **ROBUST** |
| **有效状态** | **`TIMELINE_CANDIDATE`** |

> ⚠️ **重要提醒**：`TOPC-001` 的集中度比率（0.2148）明显优于 `TOPC-018`（0.4018），
> 但这**不是**因为它更强 —— 而是因为它排除了 2019 年（唯一的 8 月离群锚点）。
> 而排除 2019 的原因是 **taxonomy 挂接缺口**，不是有原则的日期筛选。
> **因此不得用"剔掉 2019 后集中度更高"作为 TOP-01 更强的证据。** 两者互为口径变体，本质是同一结构。

### 7.3 归并结论

`TOPC-018` 与 `TOPC-001` 的样本 Jaccard = **0.857** → 归并为 **1 个独立结构**。

> **全量扫描的最终结论：1 个稳健时间结构。**

---

## 8. Exploratory Candidates

以下候选在**某一种** scope 口径下通过数值门槛，但经口径稳健性检验后降级，或本身样本 / 稳定性不足。

### 8.1 因口径脆弱而降级（3 条）

| pattern_id | 阶段 | 通过时的口径 | N | 中心 | 窗口 | 降级原因 |
|---|---|---|---|---|---|---|
| `TOPC-021` | `MAIN_RISE` | rule_auto_summer | 7 | 06-22 | 05-25 ~ 07-20 | 变体口径为 MILD_DRIFT |
| `TOPC-005` | `PEAK` | TH-AUTO | 6 | 07-03 | 06-14 ~ 07-22 | 变体口径为 STRONG_DRIFT |
| `TOPC-078` | `MAIN_RISE→PEAK` | TH-AUTO | 6 | 07-12 | 06-16 ~ 08-07 | 变体口径为 MILD_DRIFT |

**且如 §1.2 发现三 所述，这三者全部是 EARLY_SIGNAL 的派生结果**（残差 ≤ 10 天），
即使口径稳健，也不构成独立规律。

### 8.2 有结构但漂移（值得关注）

| pattern_id | 阶段 | N | 中心 | 集中度 | 问题 |
|---|---|---|---|---|---|
| `TOPC-004` | 汽车 · `MAIN_RISE` | 6 | 06-17 | **0.1879** | MILD_DRIFT（唯一通过 Bonferroni 的独立样本） |
| `TOPC-022` | rule · `PEAK` | 7 | 07-11 | 0.3872 | **STRONG_DRIFT** |
| `TOPC-027` | rule · `MAIN_END` | 7 | 08-31 | 0.3543 | **STRONG_DRIFT** |
| `TOPC-094` | rule · `MAIN_RISE→PEAK` | 7 | 07-13 | 0.3872 | MILD_DRIFT |
| `TOPC-010` | 汽车 · `MAIN_END` | 6 | 08-31 | 0.3721 | **STRONG_DRIFT** |
| `TOPC-003` | 汽车 · `BROAD_CONFIRMATION` | 4 | 06-29 | 0.1781 | N=4，STABLE |
| `TOPC-008` | 汽车 · `DECLINING` | 4 | 08-04 | **0.0868** | N=4；且为派生（滞后 61.5 d） |
| `TOPC-116` | 汽车 · `PHASE_DECLINE` | 4 | 07-21 | 0.1689 | N=4，STABLE |
| `TOPC-007` | 汽车 · `SECONDARY` | 4 | 08-12 | 0.3425 | MILD_DRIFT |
| `TOPC-112` | 汽车 · `PHASE_STARTUP` | 4 | 06-07 | 0.3288 | MILD_DRIFT |
| `TOPC-117` | 汽车 · `DB_startup→main_rise` | 4 | 06-22 | 0.2237 | MILD_DRIFT |

### 8.3 事件类型候选（2 条，结构上不得进 Timeline）

| pattern_id | 事件类型 | N | 中心 | 集中度 | 状态 |
|---|---|---|---|---|---|
| `TOPC-191` | 全部事件 | 8 | 06-03 | 0.5918 | EXPLORATORY |
| `TOPC-187` | `company` | 6 | 06-19 | 0.5600 | EXPLORATORY |
| `TOPC-189` | `market` | 4 | 06-17 | 0.1826 | EXPLORATORY |

> **这三条恰恰是"研究样本选择偏差"的直接证据**：ThreeC 自己登记的事件在 6 月高度集中。
> 它们**不能**作为主题观察规律，只能作为**偏差度量**使用。

### 8.4 两条 `HOLIDAY_RELATIVE`

| pattern_id | 阶段 | N | 绝对比率 | 春节偏移比率 | 偏移值 |
|---|---|---|---|---|---|
| `TOPC-008` / `TOPC-025` | 汽车 · `DECLINING` | 4 | 0.0868 | **0.0228** | 176 / 181 / 178 / 178 天 |

4 个 DECLINING 日期落在春节后 **176–181 天**（5 天跨度）。
但 N=4、且为派生结果（滞后 61.5 天）→ `EXPLORATORY`，不构成规律。

---

## 9. Research-only Candidates

12 条 `RESEARCH_ONLY`。典型特征：**N ≥ 5 但集中度 > 0.60（时间分散）**，或 N=3–4 且集中度不足。
注意其中相当一部分来自 `ALL` scope —— 即"把两族合并后时间立刻分散"。

| 代表 | scope | 阶段 | N | 集中度 | 原因 |
|---|---|---|---|---|---|
| `TOPC-038` | ALL | `MAIN_RISE` | 7 | 0.8256 | 时间高度分散 |
| `TOPC-039` | ALL | `PEAK` | 7 | 0.8840 | 时间高度分散 |
| `TOPC-110` | ALL | `MAIN_RISE→PEAK` | 7 | 0.8840 | 时间高度分散 |
| `TOPC-037` | ALL | `BROAD_CONFIRMATION` | 5 | 0.7397 | 时间分散 |
| `TOPC-148` | ALL | `PHASE_MAIN_RISE` | 6 | 0.7326 | 时间分散 |
| `TOPC-190` | 事件类型：`policy` | — | 6 | 0.7978 | 政策日期本身分散（跨 5 个月） |

`RESEARCH_ONLY` 保留在候选池中**仅供扩样后复查**，不得进入 Timeline。

---

## 10. Rejected Patterns

10 条 `REJECTED`，两类原因：

### 10.1 窗口不可构建（IQR > 90 天 = 跨三个以上季节）

| pattern_id | scope | 阶段 | N | IQR |
|---|---|---|---|---|
| `TOPC-035` | **全部历史对象** | `EARLY_SIGNAL` | 7 | **92.5 d** |
| `TOPC-047` | 智能驾驶/无人驾驶 | `PEAK` | 3 | 92.0 d |

> **`TOPC-035` 是本轮最重要的否定性结果之一**：把两个主题族合并后，EARLY_SIGNAL 立刻失去集中性
> （比率 0.6247、IQR 92.5 天）→ **6 月集中不是全市场现象**。

### 10.2 单年主导（LOO 中心位移 ≥ 45 天）

| pattern_id | scope | 阶段 | N | LOO 位移 |
|---|---|---|---|---|
| `TOPC-036` | ALL | `THEME_FORMING` | 5 | 86.0 d |
| `TOPC-104` | ALL | `EARLY_SIGNAL→THEME_FORMING` | 5 | 86.0 d |
| `TOPC-152` | ALL | `PHASE_DECLINE` | 4 | 69.0 d |
| `TOPC-155` | ALL | `DB_main_rise→decline` | 4 | 69.0 d |
| `TOPC-108` | ALL | `BROAD_CONFIRMATION→MAIN_RISE` | 3 | 92.0 d |
| `TOPC-106` | ALL | `THEME_FORMING→BROAD_CONFIRMATION` | 3 | 74.0 d |
| **`TOPC-028`** | **rule_pharma_upgrade** | `EARLY_SIGNAL` | 3 | **334.0 d** |
| **`TOPC-032`** | **rule_pharma_upgrade** | `PEAK` | 3 | **352.0 d** |

> **医药族的两条 LOO 位移 334 / 352 天** —— 意味着剔除任一年后中心几乎完全翻转。
> 这是"主题重复 ≠ 时间规律"最直接的量化证据。

---

## 11. Small-sample False Positives

### 11.1 N=2 完全重合（v0.1 已识别，v0.2 继续拦截）

`TOPC-003`/`TOPC-020` 系列：汽车电动化 2020-06-01 与 2021-06-01 **完全重合** → 集中度比率 0.000、p≈0.003。

**这是"样本量幻觉"的教科书案例**：两点重合使任何集中度指标与检验都出现假显著，但毫无统计意义。
v0.2 的 `N < 3 → INSUFFICIENT_DATA` 规则把它拦在候选统计池之外。

### 11.2 本轮新识别的假阳性类型

| 类型 | 案例 | 特征 |
|---|---|---|
| **派生假阳性** | `MAIN_RISE` / `PEAK` / `MAIN_END` / `SECONDARY` 全部阶段 | 中心 = EARLY_SIGNAL 中心 + 典型时长（残差 ≤ 11 d）→ 与 EARLY_SIGNAL 是同一事实 |
| **口径依赖假阳性** | `MAIN_RISE` / `PEAK` / `MAIN_RISE→PEAK` | 判定随 scope 定义翻转 → 依赖 2019 是否入样 |
| **事件台账假阳性** | `TOPC-191` / `TOPC-187`（N=8 / 6，p≈0.02–0.04） | 由研究样本自身的 6 月偏好造成 |
| **p 值假阳性** | `TOPC-004`（唯一过 Bonferroni） | p 最小但 MILD_DRIFT → 不能晋级 |
| **N=2 重合假阳性** | `TOPC-003` 系列 | 两点重合造成假显著 |

### 11.3 假阳性拦截统计

| 拦截机制 | 拦截数 |
|---|---|
| `N < 3` → INSUFFICIENT_DATA | 121 |
| LOO 单年主导 → REJECTED | 8 |
| IQR > 90d → REJECTED | 2 |
| 口径稳健性 → 降级 | 3 |
| 派生判定（标注，不单独拦截） | 7 个阶段 |
| **合计被拦截 / 降级** | **134 / 191（70%）** |

---

## 12. Survivorship / Negative-control Limitations

### 12.1 负对照可得性

| 项目 | 结果 |
|---|---|
| `coverage` | **WEAK** |
| 可用负样本 | 仅 `annual_reviews.status ∈ {no_clear_campaign, weak}` 的**年度级**状态 |
| `rule_auto_summer` | 8 年审查，负例 2 个（2018 `no_clear_campaign`、2019 `weak`）→ 覆盖率 25% |
| `rule_pharma_upgrade` | 4 年审查，负例 1 个（2022 `weak`）→ 覆盖率 25% |

### 12.2 明确结论

> **`negative-control coverage insufficient`。**
>
> 仓库内**不存在"主题级未成势"记录**。我们无法观测：
> 「同样在 5–6 月出现、但最终没有形成 Campaign 的主题」。
>
> **因此不能把"没有反例"当作"不存在反例"。**

### 12.3 三重偏差（叠加）

| 偏差 | 度量 |
|---|---|
| **幸存者偏差** | 只记录"形成 Campaign 的主题" |
| **研究事件选择偏差** | 事件台账 6 月占比 **33.3%**（均匀 8.3%）；指数最优 30 日窗口 6 月占比 **18.75%** |
| **口径漂移** | 2019–2022 与 2023–2024 立项标准不同；2019-01-02 实为本地数据窗口起点 |

**对 TOP-01 的影响**：即使扣掉 18.75% 的指数基准，汽车族 71% 的 6 月占比仍有剩余解释力；
但**无法排除**"汽车族是研究者重点跟踪对象，因此其 6 月事件被更完整地记录"这一可能性。

---

## 13. Mechanism Analysis

### 13.1 机制归类（区分 data-supported 与 post-hoc）

**汽车主题族（`TH-AUTO`）**

| 机制 | 置信度 | 依据类型 |
|---|---|---|
| `CALENDAR_DRIVEN` | MEDIUM | 制度性日历 |
| `POLICY_CADENCE` | MEDIUM | **data-supported**：仓库内 `EV-2022-01`（2022-05-23 国常会减征购置税 600 亿）、`EV-2022-02`（2022-05-31 财政部细则） |
| `REPORTING_CADENCE` | MEDIUM | **公开制度日历**：A 股中报预告披露窗口（6 月中下旬密集） |
| `DATA_RELEASE_CADENCE` | LOW | **post-hoc**：月度产销 / 渗透率数据次月中旬公布（仓库内无发布日期字段） |
| `INDUSTRY_EVENT_CADENCE` | LOW | **post-hoc**：国际产业事件（特斯拉 Robotaxi / FSD）偏北半球夏季 |

**医药健康主题族（`TH-PHARMA`）**

| 机制 | 置信度 | 依据 |
|---|---|---|
| `CALENDAR_DRIVEN` | **LOW** | **data-supported 的反证**：政策日期本身分散（集采 2018-12-17、科创板 2019-07-22、医保谈判 2019-11-28、中医药 2021-12-31）→ **不支持任何单月集中** |

### 13.2 关键区分：政策"预期窗口" vs "发布日"

必须明确指出：

> 智能网联汽车相关政策的**发布时点并不在 6 月** ——
> 四部委《智能网联汽车准入和上路通行试点》成文 **2023-11-17**；
> 五部门车路云 20 城试点名单公布 **2024-07-01**。

因此机制更接近**"政策预期窗口 + 国际产业事件 + 财报日历"的叠加**，
**不是**"政策发布日期本身"。这一解读属 **post-hoc hypothesis**，置信度 LOW。

### 13.3 为什么这是 `CALENDAR_DRIVEN` 而非 `SEASONAL_DEMAND`

- 无任何终端需求季节性证据（无销量季节性、无库存季节性数据）；
- 6 月集中的时间位置与**制度性日历**（政策节奏、财报预告窗口）重合度更高；
- 春节相对位置检验失败（跨度 106 天）→ 排除农历驱动。

> **产品文案不得写成"夏季汽车旺季"。** 正确表述是"日历驱动的研究观察窗口"。

---

## 14. Multiple-testing Limitations

### 14.1 扫描规模与假阳性期望

| 指标 | 值 |
|---|---|
| 扫描空间 | **191** |
| N ≥ 3 的候选 | 70 |
| N ≥ 5 的候选 | 30 |
| 集中度 ≤ 0.45 的候选 | 65 |
| **p ≤ 0.05 的候选** | **49** |
| α=0.05 下的期望假阳性（仅按 N≥5 计） | 1.5 |
| Bonferroni 阈值 | **0.000262** |
| 通过 Bonferroni 的候选 | 3 条（`TOPC-004` / `TOPC-113` / `TOPC-130`） |
| 其中**独立样本** | **1 个**（`TOPC-004`） |

### 14.2 关键解读

> **191 个候选中有 49 个 p ≤ 0.05。** 如果只看 p 值，会得到"49 个规律"的荒谬结论。
> 这正是 §十七 要求处理的多重比较 / 数据挖掘偏差。

**"扫得越多，总有几个 p 值很漂亮"** —— 本轮的直接证据：
唯一通过 Bonferroni 校正的独立样本 `TOPC-004`（汽车 `MAIN_RISE`，N=6，集中度 0.1879，p=0.000232）
**同时是 MILD_DRIFT**，且是 EARLY_SIGNAL 的派生结果 → `EXPLORATORY`。

### 14.3 立场声明

> **本轮是发现性研究（discovery），不是验证性统计检验（confirmatory）。**
>
> 因此：
> 1. 不因为单个 p 值晋级；
> 2. 大量弱候选归为 `RESEARCH_ONLY`；
> 3. p 值仅作描述性诊断，**不承载"显著性断言"**；
> 4. 晋级必须同时通过七项检查：样本量 / 集中度 / 稳定性 / LOO / 主题族独立性 / 负对照 / 机制。

---

## 15. Data Gaps

| # | 缺口 | 影响 | 需要什么 |
|---|---|---|---|
| 1 | **只有 2 个 Macro Theme** | `theme_family_count` 上限 = 2 → 无法获得真正跨族独立性 | 补录非汽车 / 非医药主题族（电力、军工、消费、TMT、纺织等） |
| 2 | **无"主题级未成势"负样本** | 幸存者偏差无法量化 | 记录"观察到但未形成 Campaign"的主题 |
| 3 | **无行业事件日历** | `INDUSTRY_EVENT_DRIVEN` 无法研究（= 0 条） | 结构化车展 / CES / MWC / 发布会日期 |
| 4 | **无数据发布日历** | `DATA_RELEASE_DRIVEN` 无法研究（= 0 条） | 产销 / 库存 / 价格 / 出口 / PMI 发布日期字段 |
| 5 | **锚点未经人工核验** | 数据质量上限 MEDIUM，结论永远带"探索性" | 人工核验 TOP-01 的 7 个锚点日期 |
| 6 | **Macro Theme ↔ Theme Cycle 无稳定映射键** | 同一主题族有两种不等价成员集合（本轮 3 条脆弱候选的直接原因） | 显式「主题族 ↔ rule / theme」定义表 |
| 7 | **2019-01-02 实为数据窗口起点** | 医药 2019 锚点失真 | 补录真实主题起点 |
| 8 | **交易日历仅覆盖 2022-03 ~ 2024-09** | 无法用交易日口径 | 补全 2018–2025 交易日历 |
| 9 | **只有 7 个有效年度观测** | 所有 N ≤ 7，`N ≥ 8` 的"稳定规律"档位无法达到 | 扩样到 2018 之前或 2026+ |

---

## 16. Recommended Next Research

### P0（最高优先级，唯一一件事）

**人工核验 TOP-01 的 7 个锚点日期**（尤其 `2019-08-15` 弱事件锚点与 `2022-04-27` 政策锚点）。
这是当前提升可信度**性价比最高**的一步，直接决定能否去掉"探索性"标签。

### P1

1. **补录"未成势主题"** → 建立主题级负样本，量化幸存者偏差。**这是最有价值的一步。**
2. **修复 `C-2019-AD` 的 Macro Theme 挂接**，消除本轮 3 条脆弱候选的根源。
3. **建立显式「主题族 ↔ rule / theme」定义表**（模型层决策，需 Review）。

### P2

4. **补录非汽车主题族历史数据**，把 `theme_family_count` 从 2 提到 ≥ 4 —— 这是唯一能让"跨族独立性"检查真正生效的路径。
5. 结构化**行业事件日历**与**数据发布日历**，使两类"零结果"的 Pattern 变为可研究。
6. 补全 2018–2025 **交易日历**。

### P3

7. **扩样到 2018 之前 / 2026+**，把 N 从 7 提到 ≥ 8，解锁"稳定规律"档位。
8. 当 `theme_family_count ≥ 4` 且 N ≥ 8 时，重新运行本 Discovery（**无需重写研究逻辑**，见 §18）。

### 关于增量更新

本 Artifact 已支持增量复算：每个候选含 `years` / `sample_size` / `ruleset_version` / `input_snapshot`，
顶层含 `input_snapshot.export_source_commit`。新增一年数据后只需：

```bash
python research/scripts/discover_time_observation_patterns.py            # 重新生成
python research/scripts/discover_time_observation_patterns.py --check    # 校验确定性
```

**无需人工重写研究逻辑。**

---

## 17. 必须回答的十个研究问题（§二十八）

### Q1 · 除 TOP-01 外，还有哪些可能具有时间重复性的结构？

**答：没有稳健的。** 数值门槛下另有 4 条（`MAIN_RISE` / `PEAK` / `MAIN_RISE→PEAK` / `EARLY_SIGNAL`@TH-AUTO），
但它们要么是 TOP-01 的口径变体（`TOPC-001`），要么口径脆弱（3 条），要么是派生结果（全部）。
归并后**独立结构 = 1**。

### Q2 · 这些结构属于哪类？

| 类型 | 结果 |
|---|---|
| `CALENDAR_DRIVEN` | **主类**（汽车族，64 条） |
| `PHASE_TRANSITION` | 数量最多（115），但**全部为派生**，不构成独立规律 |
| `SEASONAL` | 1 条（`TOPC-033`，N=2 → `INSUFFICIENT_DATA`），不构成证据 |
| `HOLIDAY_RELATIVE` | 2 条（N=4，探索性） |
| `INDUSTRY_EVENT_DRIVEN` / `DATA_RELEASE_DRIVEN` | **0（数据不足）** |

### Q3 · 哪些只是小样本幻觉？

- **N=2 完全重合**：`TOPC-003` 系列（2020/2021 均 06-01）→ 集中度 0.000、p≈0.003 的假显著。
- **事件台账**：`TOPC-191`（N=8）/ `TOPC-187`（N=6）→ 由研究样本 6 月偏好造成。
- **派生阶段**：全部阶段迁移与后续阶段 —— 与 EARLY_SIGNAL 是同一事实。

### Q4 · 哪些规律只由单一 Theme Family 驱动？

**TOP-01 本身。** `theme_family_count = 1`（仅汽车）。
这是它最强的限制 —— 不能表述为"A 股主题普遍规律"。

### Q5 · 哪些规律跨多个 Theme Family 依然存在？

**没有。** `全部历史对象 · EARLY_SIGNAL`（N=7，跨两族）→ **REJECTED**（集中度 0.6247、IQR 92.5 天）。
**跨族之后规律消失**，这从反面证明 TOP-01 是汽车族特有现象。

### Q6 · 哪些规律在前半时期和后半时期都成立？

`STABLE` 且有效的：**仅 TOP-01 的两个口径变体**（`TOPC-018` 位移 +10.5 d；`TOPC-001` STABLE）。

### Q7 · 哪些规律存在明显年代漂移？

| 候选 | 漂移 |
|---|---|
| `TOPC-022` rule·`PEAK` | STRONG_DRIFT |
| `TOPC-027` rule·`MAIN_END` | STRONG_DRIFT |
| `TOPC-010` 汽车·`MAIN_END` | STRONG_DRIFT |
| `TOPC-004` 汽车·`MAIN_RISE` | MILD_DRIFT |
| `TOPC-094` rule·`MAIN_RISE→PEAK` | MILD_DRIFT |
| `TOPC-007` 汽车·`SECONDARY` | MILD_DRIFT |
| `TOPC-112` 汽车·`PHASE_STARTUP` | MILD_DRIFT |
| `TOPC-117` 汽车·`DB_startup→main_rise` | MILD_DRIFT |

### Q8 · 哪些可能是制度性日历造成，而非自然季节性？

**全部。** 零候选被归为 `SEASONAL_DEMAND`。
汽车族的机制画像为 `CALENDAR_DRIVEN` + `POLICY_CADENCE` + `REPORTING_CADENCE`。

### Q9 · 哪些目前值得 Product 层继续保留？

**只有 TOP-01（汽车主题族 EARLY_SIGNAL 上半年末观察窗口）**，
且必须以「宽窗口 + 明确机制类别 + 非预测文案 + 限制说明」方式呈现。

**建议维持 Phase 7.2 的现状不变**：本轮未发现需要新增或移除的产品模式。
新增的 3 个"通过门槛"候选经稳健性检验后应**不进** Timeline。

### Q10 · 未来新增 2026 / 2027 数据时，哪些 Candidate 最值得自动增量复算？

| 优先级 | Candidate | 理由 |
|---|---|---|
| **1** | `TOPC-018`（rule·`EARLY_SIGNAL`） | 唯一有效结构；每年新增 1 个观测即可验证 |
| **2** | `TOPC-001`（TH-AUTO·`EARLY_SIGNAL`） | 口径变体，需同步复算以检查稳健性是否保持 |
| **3** | `TOPC-021` / `TOPC-005` / `TOPC-078` | 降级候选；若新增年份后口径一致性恢复，可重新评估 |
| 4 | `TOPC-004`（汽车·`MAIN_RISE`） | p 最小；若漂移消失可升级 |
| 5 | 医药族全部候选 | 当前 `INSUFFICIENT_DATA`；N 增加后复查 |

**复算方式**：直接重跑生成器 + `--check`，无需人工介入。

---

## 18. 全量扫描地图（§二十七）

```text
Dataset
  Theme Cycles : 9
  Campaigns    : 9
  Research Candidates : 4
  Anchors      : 72 条（13 对象 × 平均 5.5 个 lifecycle 阶段）
  Transitions  : 49 条（export 口径）+ 35 条（DB campaign_phases 口径）
  Events       : 33 条（policy / company / market / macro）
  Years        : 2019–2025（有效 7 年；2018 为 no_clear_campaign 反例年）

Discovery
  Raw candidates      : 191
  distinct samples    : 94
  TIMELINE_CANDIDATE  : 5   → effective 2
  EXPLORATORY         : 43  → effective 46
  RESEARCH_ONLY       : 12  → effective 12
  REJECTED            : 10  → effective 10
  INSUFFICIENT_DATA   : 121 → effective 121
  独立结构            : 1

Pattern Type × Count
  PHASE_TRANSITION        115
  CALENDAR_DRIVEN          64
  UNKNOWN                   9
  HOLIDAY_RELATIVE          2
  SEASONAL                  1
  INDUSTRY_EVENT_DRIVEN     0  ← 数据不足
  DATA_RELEASE_DRIVEN       0  ← 数据不足

Scope Type × Count
  THEME                    58
  RULE                     50
  THEME_FAMILY             50
  ALL                      28
  EVENT_TYPE                5

Theme Family × Count
  汽车（TH-AUTO）          绝大多数候选
  医药健康（TH-PHARMA）    几乎全部 INSUFFICIENT_DATA
```

---

## 19. TOP-01 Regression

**结果：`PASS`**

| 项目 | 期望（Phase 7.2 canonical） | 实测（v0.2） | 判定 |
|---|---|---|---|
| N | 7 | **7** | ✅ |
| center | 06-11 | **06-11** | ✅ |
| window | 05-27 ~ 06-26 | **05-27 ~ 06-26** | ✅ |
| recurrence | 5/7 | **5/7** | ✅ |

**核心数字未被破坏。**

**但必须显式说明的一处差异**（不得静默改变）：

| 项目 | Phase 7.2 canonical | v0.2 discovery | 说明 |
|---|---|---|---|
| `promotion_status` | `TIMELINE_ELIGIBLE` | 数值门槛 `TIMELINE_CANDIDATE`；**effective 仍为 `TIMELINE_CANDIDATE`** | ✅ **一致** |
| 新增判定维度 | 无 | **口径稳健性 = ROBUST** | v0.2 新增检验，TOP-01 **通过** |

**结论**：TOP-01 在 v0.2 中**结论不变**，且**新增通过了更严格的口径稳健性检验**。
`research/scripts/build_time_observation_patterns.py` 与 canonical Artifact **未被修改**。

---

## 20. Determinism

**结果：`PASS`**

```bash
python research/scripts/discover_time_observation_patterns.py           # 生成
python research/scripts/discover_time_observation_patterns.py --check   # 校验
```

```
PASS —— 磁盘产物与重算结果逐字节一致（deterministic）。
PASS —— TOP-01 回归： {'N': 7, 'center': '06-11', 'window': '05-27 ~ 06-26', 'recurrence': '5/7'}
```

**实现要点**：

| 机制 | 做法 |
|---|---|
| 无随机数 | 集中度 p 使用**解析式** `N·r^(N-1) − (N-1)·r^N`，非蒙特卡洛 |
| 无时间戳漂移 | `generated_at` 固定为 `SNAPSHOT_DATE` |
| 排序稳定 | 候选按 `(promotion 优先级, is_duplicate, -N, concentration, pattern_id)` 全序排序 |
| 浮点一致 | MAD 用浮点（不先取整），`round()` 统一位数 |
| 自检先行 | 自检 / TOP-01 回归不通过 → **不写文件**，退出码 1 |

**自检覆盖**：pattern_id 唯一性、禁用字段、枚举合法性、`sample_size` 与 `source_records` 一致、
`TIMELINE_CANDIDATE` 门槛复核、事件类型不得晋级、日期合法性、effective 状态需有降级原因、语义红线。

---

## 21. 交付物与管线位置

### 21.1 本轮产物

| 文件 | 性质 |
|---|---|
| `research/scripts/discover_time_observation_patterns.py` | **研究脚本**（discovery 模式，只读输入，可复现） |
| `research/research/reports/time_observation_candidate_pool_v0_2.json` | **Research Candidate Pool**（机器可读，191 候选，含来源记录） |
| `research/research/reports/time_observation_candidate_pool_v0_2.csv` | 人工浏览用（30 列） |
| `research/research/reports/Time_Observation_Discovery_v0_2.md` | 本报告 |

### 21.2 管线位置

```text
历史数据（export + research DB，只读）
   ↓
统一时间事件层（Anchor / Lifecycle Transition / Event）
   ↓
Time Observation Discovery（本脚本）
   ↓
Candidate Pool（本 Artifact）          ← 本轮终点
   ↓
Promotion Gate（脚本内置，可复核）
   ↓
Product Artifact                        ← 本轮不做
   ↓
Timeline                                ← 本轮不改
```

> **`Research Candidate Pool` 不是 `Timeline Database`。**
> `RESEARCH_ONLY` / `REJECTED` / `INSUFFICIENT_DATA` 一律不得进入 Timeline。

### 21.3 与既有研究的关系

| 上游 | 关系 |
|---|---|
| `Seasonal_Observation_Pattern_Discovery_v0_1.md` | 继承锚点口径与拒绝规则；v0.2 把扫描面从 4 个主题族扩到全部 scope × 全部阶段 × 全部迁移 × 全部事件类型 |
| `time_observation_patterns_v0_1.json`（Phase 7.2 canonical） | **未修改**；v0.2 复现其 TOP-01 核心数字 |
| `research/scripts/build_time_observation_patterns.py` | **未修改**；v0.2 是独立 discovery 脚本 |
| `src/data/timeline/timeObservationPatterns.ts` | **未修改** |

---

## 22. 诚实限制清单

1. 有效观测仅 **7 年**（2018 为反例年）→ 所有 N ≤ 7，无法达到"稳定规律"档位（N ≥ 8）。
2. **只有 2 个 Macro Theme** → 主题族独立性检查的天花板为 2，本报告所有结论均受此限制。
3. 全部锚点为研究候选日期，`verification_method` 多为 `unknown`。
4. ThreeC 只记录"形成 Campaign 的主题" → **幸存者偏差无法消除**。
5. 事件台账 6 月占比 33%（均匀 8.3%）→ 时间聚集含**研究样本选择偏差**成分。
6. `C-2019-AD` 的 Macro Theme 挂接缺口造成 3 条候选判定脆弱（已降级并记录）。
7. `INDUSTRY_EVENT_DRIVEN` 与 `DATA_RELEASE_DRIVEN` 因**数据不足**无法研究（= 0 条），这是有效研究结果，不是失败。
8. 农历换算为近似（春节日期表），非精确农历算法。
9. 机制解释中的"政策预期窗口""国际产业事件"为 **post-hoc hypothesis**，置信度 LOW。
10. 本轮为**发现性研究**，p 值仅作描述性诊断，**不是确认性统计检验**。

---

## 23. 最终工作原则声明

> **本阶段的目标不是给 ThreeC 制造更多"看起来有规律"的内容，**
> **而是建立一条可长期复用的研究流水线：**
>
> **从全部历史数据中自动发现时间结构 → 统计筛选 → 稳定性检验 → 机制分类 → Promotion Gate → Product Candidate Pool。**
>
> 本轮最重要的评价标准不是"发现了多少"，而是：
> **扫描是否完整、筛选是否一致、假阳性是否被控制、结果是否可复现。**

**本轮的自我检验结果**：

| 标准 | 结果 |
|---|---|
| 扫描是否完整 | ✅ 191 候选覆盖全部 scope × 阶段 × 迁移 × 事件类型 |
| 筛选是否一致 | ✅ 门槛与 v0.1 连续，未为增加数量而放宽 |
| 假阳性是否被控制 | ✅ 191 → 5 → 2 → **1**（拦截/降级率 70%） |
| 结果是否可复现 | ✅ `--check` 逐字节一致 |
| TOP-01 是否被破坏 | ✅ 未破坏（`PASS`） |
| 产品是否被改动 | ✅ **零改动** |

**最终答案**：全量扫描后，**只有 TOP-01（汽车主题族上半年末启动观察窗口）值得继续产品化** ——
这与 §三十一 允许的"最终只有 TOP-01 也完全可以接受"一致。

---

*报告结束 · Time Observation Discovery v0.2 · 2026-09-16*
