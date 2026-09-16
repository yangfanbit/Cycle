# Historical Coverage Audit v0.1

> **ThreeC 历史研究数据覆盖度审计**
>
> | 项目 | 值 |
> |---|---|
> | 文件性质 | **Research Layer Deliverable**（研究层交付物） |
> | 轮次 | `historical-coverage-audit-v0.1` |
> | 规则集 | `historical-coverage-audit-0.1` |
> | 快照日期 | 2026-09-16 |
> | 生成器 | `research/scripts/audit_historical_coverage.py`（deterministic，`--check` 逐字节一致） |
> | 输入（只读） | `exports/timeline_export_v1.json` + `research/database/cycle_research.db` + `research/current/current_candidates.json` |
> | 产物 | `historical_coverage_matrix_v0_1.json` / `.csv` |
>
> **本阶段未修改** `src/` / Timeline / `exports/` / `contracts/` / `schema.sql` / Product Artifact。
> 不进入 Structural Historical Analogy。

---

## 0. 一句话结论

> **当前历史数据的瓶颈不是 Pattern Discovery 算法，而是数据覆盖：只有 2 个 Macro Theme、9 个 Theme Cycle、有效观测 7 年、0 个日期完成核验。**
> **最值得补的第一批数据不是"更多行业"，而是——当前侧已经声明、历史侧却完全空白的那 3 个 Macro Theme（电力设备 / 信息通信 / 高端装备）。**

**理由**：这 3 个主题是**已经存在的断裂**（Current Candidate 已产出候选，但历史侧无任何 Cycle 可供类比），补录它们的边际收益远高于补录"当前侧完全没提到"的行业。

---

## 1. Dataset

### 1.1 总量

| 项目 | 数量 |
|---|---|
| Campaigns | **9**（DB 与 export 一致） |
| Research Candidates | **4**（`RC-*`，永不 verified） |
| Theme Cycles | **9** |
| Macro Themes（历史侧） | **2** |
| Themes（全部） | 12（2 宏观 + 10 子主题） |
| 孤立 theme（无 campaign 关联） | **2** |
| Lifecycle records | **72** 条锚点记录（export lifecycle） / **23** 行（DB `campaign_phases`） |
| Evidence | **51** |
| Events | **30**（DB） / **33**（export） |
| Years | **2019–2025**（有效 7 年；2018 为 `no_clear_campaign` 反例年） |
| **已完成核验的日期** | **0 / 24** |
| Market series | 40（其中连续 1 / 窗口采样 22 / 部分跨度 11 / **空占位 6**） |
| trading_calendar | 371 行（**仅 2022-03-01 ~ 2024-09-30**） |

### 1.2 分布（不只总量）

**Campaign 年度分布**

| 年 | Campaigns |
|---|---|
| 2019 | 2 |
| 2020 | 1 |
| 2021 | 1 |
| 2022 | 1 |
| 2023 | 1 |
| 2024 | **2** |
| 2025 | 1 |
| 2018 | **0**（`no_clear_campaign`） |

**classification**：`theme_campaign` **8** / `event_driven` **1**
**strength**：`strong` **5** / `medium` **3** / `weak` **1**
**result**：`positive` **8** / `weak` **1**
**theme_type**：`concept` **9** / `industry` **3**
**campaign_themes.role**：`main` 10 / `related` 10 / `secondary` 1 / **`catalyst` 0**
**annual_reviews.status**：`strong` 5 / `medium` 4 / `weak` 2 / `no_clear_campaign` 1（共 12 条）

**Research 状态**：`PROVISIONAL` 12 / `CONFLICT` 1

### 1.3 关键结构性事实

> **9 个 Campaign 中，8 个属于汽车族，1 个属于医药族。**
>
> 这不是"汽车研究做得好"，而是**行业覆盖的极度不均衡** —— 汽车族占了全部历史数据的 **89%**。

---

## 2. Macro Theme Coverage

| Macro Theme | Theme Cycles | Campaigns | RC | Years Covered | Lifecycle Coverage | Evidence Coverage | Event Coverage | Securities |
|---|---:|---:|---:|---|---|---|---|---:|
| `TH-AUTO` 汽车 | **8** | **8** | 1 | 2019–2025（7 年） | 10 / 10 阶段 | 39（8 个 Campaign，均 4.88/个） | 19（8 个 Campaign 全部有关联事件） | 23 |
| `TH-PHARMA` 医药健康 | **1** | **1** | 2 | 2019–2021（3 年） | 7 / 10 阶段 | 5（1 个 Campaign，5.00/个） | 4（1 个 Campaign 有关联事件） | 3 |

### 2.1 覆盖矩阵读法

- **`TH-AUTO`**：Theme Cycle 数 8（`auto_ad_2019` / `auto_nev_2020` / `auto_nev_2021` / `auto_policy_2022` / `auto_intelligence_2023` / `auto_v2x_2024` / `robotaxi_2024` / `robotaxi_2025`），跨 7 年连续覆盖 —— 这是**目前唯一具备跨年统计条件**的主题族。
- **`TH-PHARMA`**：Theme Cycle 仅 1（`medical_structural_upgrade_2019_2022`），实际只有 1 个正式 Campaign（`C-2019-PHARMA-INNOV`）+ 2 个 Research Candidate（`RC-2020-PANDEMIC` / `RC-2021-TCM`）。**跨年样本不足以做任何时间统计。**

### 2.2 必须识别的四类异常

**（a）孤立 theme（有主题、无 Campaign）—— 2 个**

| theme_id | 名称 | 说明 |
|---|---|---|
| `TH-PHARMA-PANDEMIC` | 疫情医疗 | 仅被 `RC-2020-PANDEMIC` 引用；`campaign_themes` 无关联 |
| `TH-PHARMA-TCM` | 中医药 | 仅被 `RC-2021-TCM` 引用；`campaign_themes` 无关联 |

**（b）export 独有 theme（不在 DB `themes` 表）—— 1 个**

| 名称 | 出现在 | 说明 |
|---|---|---|
| **华为汽车** | `RC-2023-HUAWEI` | **DB `themes` 表中不存在该主题** → taxonomy 断裂 |

**（c）Campaign 未挂接 Macro Theme —— 1 个**

`C-2019-AD`（2019）：其 `themes` 只有「智能驾驶/无人驾驶」，**列表中没有「汽车」**。

**（d）★ 同一对象的 Macro Theme 有两种解析口径 —— 4 个对象**

| 对象 | themes | `resolved`（沿 parent 链） | `direct`（按名称匹配） |
|---|---|---|---|
| `C-2019-AD` | 智能驾驶/无人驾驶 | `TH-AUTO` | **（空）** |
| `RC-2024-SECONDARY` | Robotaxi/无人驾驶/智能网约车 | `TH-AUTO` | **（空）** |
| `RC-2020-PANDEMIC` | 疫情医疗 | `TH-PHARMA` | **（空）** |
| `RC-2021-TCM` | 中医药 | `TH-PHARMA` | **（空）** |

> **这是本轮审计最重要的技术发现之一。**
>
> `Time Observation Discovery v0.2` 用的是 **`direct`（按名称匹配）** 口径，因此把上述 4 个对象**排除在主题族之外**；
> 而本审计用 **`resolved`（沿 parent 链）** 口径，把它们**包含进来**。
>
> → **同一个"汽车主题族"存在两种不等价的成员集合。** 这正是 v0.2 中 3 条候选（`MAIN_RISE` / `PEAK` / `MAIN_RISE→PEAK`）被判为「口径脆弱」的**根本原因** —— 它们的判定依赖"2019 年是否入样"，而入样与否由这个解析口径差异决定。
>
> **修复成本极低（1 行关联 + 1 个 taxonomy 定义），但直接提升已有 Pattern 的稳健性。**

---

## 3. Lifecycle Coverage

### 3.1 逐对象评级（**只评级，未补齐**）

| 对象 | 年 | 阶段数 | 评级 | 缺失阶段（任务书 7 阶段视角） |
|---|---|---:|---|---|
| `C-2019-PHARMA-INNOV` | 2019 | 7 | **COMPLETE** | — |
| `C-2022-POLICY` | 2022 | 9 | **COMPLETE** | — |
| `C-2023-AD` | 2023 | 8 | **COMPLETE** | — |
| `C-2019-AD` | 2019 | 4 | PARTIAL | THEME_FORMING, BROAD_CONFIRMATION, WEAKENING |
| `C-2020-NEV` | 2020 | 6 | PARTIAL | THEME_FORMING, BROAD_CONFIRMATION |
| `C-2021-NEV` | 2021 | 5 | PARTIAL | THEME_FORMING, BROAD_CONFIRMATION |
| `C-2024-ROBOTAXI` | 2024 | 8 | PARTIAL | THEME_FORMING |
| `C-2024-V2X` | 2024 | 4 | PARTIAL | BROAD_CONFIRMATION, EXPANSION, WEAKENING |
| `C-2025-ROBOTAXI` | 2025 | 5 | PARTIAL | THEME_FORMING, WEAKENING |
| `RC-2020-PANDEMIC` | 2020 | 5 | PARTIAL | THEME_FORMING, BROAD_CONFIRMATION |
| `RC-2021-TCM` | 2021 | 4 | PARTIAL | BROAD_CONFIRMATION, EXPANSION, DECLINE |
| `RC-2023-HUAWEI` | 2023 | 4 | PARTIAL | PEAK, WEAKENING, DECLINE |
| `RC-2024-SECONDARY` | 2024 | 2 | **SPARSE** | 除 EARLY_SIGNAL / MAIN_END 外全部缺失 |

**汇总：COMPLETE 3 / PARTIAL 9 / SPARSE 1 / UNKNOWN 0**

### 3.2 阶段覆盖率（13 个对象）

| 阶段 | 覆盖 | 覆盖率 |
|---|---|---|
| `EARLY_SIGNAL` | 13 | **100%** |
| `PEAK` | 11 | 85% |
| `MAIN_END` | 11 | 85% |
| `MAIN_RISE` | 10 | 77% |
| `DECLINING` | 7 | 54% |
| `THEME_FORMING` | 6 | **46%** |
| `BROAD_CONFIRMATION` | 6 | **46%** |
| `SECONDARY` | 4 | 31% |
| `RETRACEMENT` | 2 | 15% |
| `FIRST_DECLINE` | 1 | 8% |

### 3.3 关键结论

> **只有 3 / 13（23%）的对象具有可读的完整生命周期。**
>
> 且缺失集中在 **`THEME_FORMING`（46%）与 `BROAD_CONFIRMATION`（46%）** —— 这恰恰是
> **Formation Anchor** 所依赖的两个阶段（见 `src/data/timeline/preObservation.ts`）。
>
> → **超过一半的对象无法确定「主题形成」的时点**，只能退化到 `EARLY_SIGNAL` 或 `Campaign.start`。
> 这直接限制了 Phase Transition 研究：v0.2 发现「7/7 阶段全部为派生」，
> 部分原因就是**形成 / 确认阶段本身缺失**，无法提供独立的时间信息。

### 3.4 阶段命名口径

任务书 §八 列出的 `EXPANSION` / `WEAKENING` / `DECLINE` 在仓库中**不存在**。本审计按**显式别名映射**对齐，**不发明新阶段**：

| 任务书阶段 | 仓库真实阶段 |
|---|---|
| `EXPANSION` | `MAIN_RISE` |
| `WEAKENING` | `DECLINING` / `RETRACEMENT` / `SECONDARY` |
| `DECLINE` | `MAIN_END` / `FIRST_DECLINE` |

---

## 4. Evidence Coverage

### 4.1 ⚠️ 先修数据质量问题

> **`evidences.evidence_type` 在 schema 中是自由文本（无 CHECK 约束），DB 内中英文混用：**

| 原始 `evidence_type` | 条数 |
|---|---:|
| 行情数据 | 30 |
| 行业数据 | 6 |
| 政策文件 | 5 |
| 行业月度产销数据 | 5 |
| `official_document` | 3 |
| `market_data` | 1 |
| `media` | 1 |

`行情数据` 与 `market_data` 是同一语义、`政策文件` 与 `official_document` 是同一语义。
**统计前必须先归一化** —— 这是纯数据清理，无研究成本。

### 4.2 归一化后的规范覆盖

| 规范类别 | 条数 | 状态 |
|---|---:|---|
| `market`（行情） | 31 | ✅ |
| `industry`（行业） | 11 | ✅ |
| `policy`（政策） | 8 | ✅ |
| `information`（信息/媒体） | 1 | ⚠️ 极弱 |
| **`company`（公司）** | **0** | ❌ **缺失** |
| **`capital`（资金）** | **0** | ❌ **缺失** |

> **`company` 与 `capital` 两类证据完全缺失。**
>
> 这直接对应 Phase Evidence Matrix 的 8 个维度中的**公司维度**与**资金维度** ——
> 两个维度在当前历史数据下**永远无法派生**，只能由研究手工声明。

### 4.3 证据角色与时间关系

| `evidence_role` | 条数 |
|---|---:|
| supporting | 29 |
| contradicting | 13 |
| context | 9 |

| `temporal_relation` | 条数 |
|---|---:|
| contemporaneous | 35 |
| subsequent | 4 |
| retrospective | 3 |
| prior | 2 |
| **unknown** | **7** |

> `unknown` 7 条意味着 **7 条证据的时间语义未定** —— 无法判断它属于"当时信息"还是"事后回顾"，
> 这在 Temporal Firewall 下必须按不可用处理。

### 4.4 来源层级

| `source_type` | 条数 | | `tier` | 条数 |
|---|---:|---|---|---:|
| `media_tier2` | 37 | | 1 | 8 |
| `regulator` | 7 | | 2 | 37 |
| `media_tier3` | 7 | | 3 | 8 |
| `media_tier4` | 2 | | 4 | 2 |
| `exchange` | 1 | | | |
| `website` | 1 | | | |

**Schema 允许但完全未使用的来源类型**：`company_announcement`（公司公告）、`industry_association`（行业协会）、`research_report`（研究报告）。

> **一手来源严重不足**：tier 1 仅 8 条（15.7%），其中 `exchange` 只有 1 条、**`company_announcement` 为 0**。
> 证据链高度依赖媒体（tier 2+ 共 46 条 = 90%），这削弱了"独立证据"的强度。

### 4.5 逐 Campaign 证据数

| Campaign | total | supporting | contradicting | context |
|---|---:|---:|---:|---:|
| `C-2021-NEV` | 7 | 5 | 1 | 1 |
| `C-2023-AD` | 7 | 5 | 2 | 0 |
| `C-2019-PHARMA-INNOV` | 5 | 3 | 0 | 2 |
| `C-2022-POLICY` | 5 | 4 | 1 | 0 |
| `C-2025-ROBOTAXI` | 5 | 2 | 3 | 0 |
| `C-2020-NEV` | 4 | 3 | 0 | 1 |
| `C-2024-ROBOTAXI` | 4 | 2 | 1 | 1 |
| `C-2024-V2X` | 4 | 3 | 1 | 0 |
| `C-2019-AD` | 3 | 2 | 0 | 1 |

> 平均 **4.9 条 / Campaign**，最少 3 条。
> 对"可用于结构比较的历史对象"而言，**证据密度偏低** —— 尤其是反证（contradicting）分布极不均：
> `C-2019-PHARMA-INNOV` / `C-2020-NEV` / `C-2019-AD` 各 **0 条反证**，而 `C-2025-ROBOTAXI` 有 3 条。
> **无反证不等于没有分歧，可能只是没有记录。**

---

## 5. Event Coverage

### 5.1 现有事件类型

| `event_type` | DB | export |
|---|---:|---:|
| `policy` | 15 | 16 |
| `company` | 11 | 12 |
| `market` | 4 | 4 |
| `macro` | **0** | 1 |

**年度分布**：2018:2 / 2019:5 / 2020:3 / 2021:5 / 2022:4 / 2023:4 / 2024:4 / 2025:3

### 5.2 能力相关类别的可用性（§十）

| 能力类别 | 状态 | 条数 | schema 允许？ |
|---|---|---:|---|
| `policy` 政策事件 | ✅ AVAILABLE | 15 | ✅ |
| `company` 公司事件 | ✅ AVAILABLE | 11 | ✅ |
| `market` 市场事件 | ✅ AVAILABLE | 4 | ✅ |
| `macro` 宏观事件 | ⚠️ DECLARED_UNUSED | 0（export 有 1） | ✅ |
| **`industry` 产业事件** | ❌ **NOT_AVAILABLE** | 0 | ✅（允许但未用） |
| **`holiday` 节假日 / 日历** | ❌ **NOT_AVAILABLE** | 0 | ✅（允许但未用） |
| **`data_release` 数据发布** | ❌ **NOT_AVAILABLE** | 0 | ❌ schema 无此类型 |
| **`reporting` 财报披露日** | ❌ **NOT_AVAILABLE** | 0 | ❌ schema 无此类型 |
| **`meeting` 重大会议** | ❌ **NOT_AVAILABLE** | 0 | ❌ schema 无此类型 |
| **`trade_fair` 展会** | ❌ **NOT_AVAILABLE** | 0 | ❌ schema 无此类型 |
| **`product` 产品发布** | ❌ **NOT_AVAILABLE** | 0 | ❌ schema 无此类型 |

**NOT_AVAILABLE 共 7 类。**

### 5.3 ★ 认识论纪律：absence of evidence ≠ evidence of absence

> **以下类别在数据库中"不存在记录"，只说明 ThreeC 尚未登记该类事件，**
> **不能推断该机制在 A 股历史中不存在。**
>
> 特别地：
> - `industry` 与 `holiday` **schema 明确允许**，只是从未使用 → 这是**登记缺口**，不是能力缺口
> - `data_release` / `reporting` / `meeting` / `trade_fair` / `product` **schema 根本没有对应类型** → 这是**结构缺口**，需要 schema 层决策（但本阶段不改 schema）

### 5.4 这直接解释了 v0.2 的两类"零结果"

`Time Observation Discovery v0.2` 中：

| Pattern 类型 | 候选数 | 原因 |
|---|---:|---|
| `INDUSTRY_EVENT_DRIVEN` | **0** | 无行业事件日历（车展 / CES / MWC / 发布会季） |
| `DATA_RELEASE_DRIVEN` | **0** | 无数据发布日历（产销 / 库存 / 价格 / 出口 / PMI） |

**这两类不是"研究了但没发现规律"，而是"根本没有数据可研究"。** 补录后即可解锁。

---

## 6. Market Data Coverage

### 6.1 ★ 核心发现：行情数据是「窗口采样」而非连续序列

40 条 series 的采样分类：

| 采样分类 | 条数 | 定义 |
|---|---:|---|
| `CONTINUOUS`（连续） | **1** | 覆盖 ≥ 6 个年度 |
| `PARTIAL_SPAN`（部分跨度） | 11 | 跨度 ≥ 3 年但年度不足 6 |
| `WINDOW_SAMPLED`（窗口采样） | **22** | 跨度 < 3 年（围绕特定 Campaign） |
| `EMPTY_PLACEHOLDER`（空占位） | **6** | 仅 1 行数据 |

**唯一连续 series：`SH000300`（沪深300，2018-01-02 ~ 2025-12-31，3884 行）**

### 6.2 空占位 series（有登记、无数据）

`AD_AUTO` / `NEV` / `ROBOTAXI` / `V2X` / `AUTO_PARTS` / `AUTO_SW`

> 这 6 条是**概念指数 / 行业指数**，恰恰是"主题级"分析最需要的序列 —— **全部为空**。

### 6.3 年度活跃 series 数（覆盖逐年衰减）

| 年 | 活跃 series | 行数 |
|---|---:|---:|
| 2018 | 1 | 486 |
| 2019 | 12 | 5,382 |
| 2020 | 13 | 6,318 |
| 2021 | 14 | 6,802 |
| 2022 | **15** | 6,350 |
| 2023 | 11 | 2,536 |
| 2024 | 7 | 1,998 |
| 2025 | **4** | 1,944 |

> **越靠近当前，行情覆盖越薄** —— 2025 年仅 4 条 series 活跃（`SH000300` / `AUTO_ETF_516110` / `DESAYSV` / `ZHEJIANGSHISHI`）。
> 这对"最新年度的行情核验"与"当前候选的历史对照"都是直接限制。

### 6.4 交易日历

`2022-03-01 ~ 2024-09-30`，371 行 —— **仅覆盖 8 年中的 2.6 年**。
→ 所有时间统计只能退化为**自然日**口径，无法与交易日对齐。

### 6.5 三个后果

1. **无法为所有年份构造「中性市场基准」** → Time Observation 的背景基准只能部分可用（v0.2 的 T2 指数基准即受此限）
2. **无法做跨主题的相位对比** → Structural Analogy 缺少共同的可比时间轴
3. **最新年度核验能力最弱** → 2025 仅 4 条 series

---

## 7. Verification Coverage

| 项目 | 值 |
|---|---|
| `campaign_date_observations` 总数 | 24 |
| `verified_date` 非空 | **0** |
| 核验比例 | **0%** |
| `confidence = low` | **24 / 24（100%）** |

**`verification_method` 分布**：

| method | 条数 |
|---|---:|
| `unknown` | 18 |
| `market_data` | 6 |

### ★ 关键结论

> **全部 24 条日期观测的 `verified_date` 均为 NULL** ——
> **即使 `verification_method` 已标为 `market_data` 的 6 条，也没有写回核验日期。**
>
> 且**全部 `confidence = low`**。
>
> → **当前没有任何一个历史日期完成最终核验。** 这是数据可信度的**硬天花板**，
> 也是产品必须永远带「探索性」标记的直接原因。
>
> `PROJECT_STATE.md` 已把「人工核验 TOP-01 的 7 个锚点」列为 **Next Single Goal** ——
> 本审计从数据侧确认了这一步的紧迫性：**它不是一个优化项，而是唯一的可信度解锁项。**

---

## 8. Domain Coverage（§六 领域清单）

| 领域 | 状态 | Campaigns | Theme Cycles | Years |
|---|---|---:|---:|---|
| **汽车** | ✅ `COVERED_WITH_CYCLES` | 8 | 8 | 2019–2025 |
| **新能源（车用电池）** | ✅ `COVERED_WITH_CYCLES` | 3 | 3 | 2020–2022 |
| **医药** | ⚠️ `COVERED_SINGLE_CYCLE` | 1 | 1 | 2019 |
| 消费 | ⚠️ `SCATTERED_ONLY` | 0 | 0 | — |
| 电力设备 | ❌ `ABSENT` | 0 | 0 | — |
| 信息通信 | ❌ `ABSENT` | 0 | 0 | — |
| 高端装备 | ❌ `ABSENT` | 0 | 0 | — |
| 半导体 | ❌ `ABSENT` | 0 | 0 | — |
| 电子 | ❌ `ABSENT` | 0 | 0 | — |
| 通信 | ❌ `ABSENT` | 0 | 0 | — |
| 计算机 | ❌ `ABSENT` | 0 | 0 | — |
| AI / 算力 | ❌ `ABSENT` | 0 | 0 | — |
| 机器人 | ❌ `ABSENT` | 0 | 0 | — |
| 军工 | ❌ `ABSENT` | 0 | 0 | — |
| 有色 / 资源 | ❌ `ABSENT` | 0 | 0 | — |
| 化工 | ❌ `ABSENT` | 0 | 0 | — |
| 金融 | ❌ `ABSENT` | 0 | 0 | — |
| 地产 | ❌ `ABSENT` | 0 | 0 | — |
| TMT | ❌ `ABSENT` | 0 | 0 | — |

### 8.1 按「历史周期」而非「行业名称」检查（§七）

> **本审计不回答"有没有半导体"，而回答"有没有可以形成完整 Historical Theme Cycle 的半导体历史周期"。**

| 领域 | 是否有完整 Cycle | 说明 |
|---|---|---|
| 汽车 | ✅ 有（8 个 Cycle） | 唯一具备跨年统计条件的族 |
| 新能源（车用电池） | ⚠️ 部分（3 个 Cycle，2020–2022） | Cycle 连续但年份窗口短 |
| 医药 | ❌ 无 | 1 个 Cycle + 2 个 RC，无法构成周期序列 |
| 消费 | ❌ 无 | **仅 theme 名称匹配（"汽车消费/购置税刺激"含"消费"二字），无独立 Cycle** |
| 其余 15 个领域 | ❌ 无 | 数据库完全无记录 |

**判定口径**：`COVERED_WITH_CYCLES` 要求 ≥ 2 个独立 Theme Cycle。
仅 1 个 Cycle 只能算 `COVERED_SINGLE_CYCLE` —— **单 Cycle 不构成"周期重复"**。
仅有零散事件或名称匹配 → `SCATTERED_ONLY`（**不算成熟 Historical Cycle**）。

> ⚠️ **重要澄清**：「新能源（车用电池）」的 3 个 Cycle
> （`auto_nev_2020` / `auto_nev_2021` / `auto_policy_2022`）**是汽车族 Cycle 的子集**，
> 并非独立主题族。因此它**不能**为 `theme_family_count` 贡献增量 ——
> **真正的独立主题族仍然只有 2 个。**

---

## 9. Research Capability Matrix（§十一）

| 能力 | 当前能力 | 主要限制 | 加什么数据能解锁 |
|---|---|---|---|
| **Time Observation** | `PARTIAL` | `theme_family_count` 上限 = 2；有效观测仅 7 年（N ≤ 7，达不到 N ≥ 8） | 补 ≥ 2 个独立 Macro Theme + 扩样至 N ≥ 8 |
| **Seasonal** | `BLOCKED` | 无终端需求季节性数据（销量 / 库存 / 价格）；无连续行情序列做中性基准 | 需求侧数据 + 连续行业指数 |
| **Calendar-driven** | `PARTIAL` | 无制度性日历结构化数据；机制解释多为 post-hoc（LOW） | 「制度性日历」表（财报窗口 / 国常会 / 五年规划 / 预算） |
| **Event-driven** | `BLOCKED` | 无行业事件日历；`event_type` 从未使用 `industry` | 行业事件日历（展会 / 发布会 / 行业大会） |
| **Phase Transition** | `LIMITED` | 阶段迁移节奏 = EARLY_SIGNAL 聚集 + 典型时长（v0.2 实测 7/7 全为派生）；且 `THEME_FORMING` / `BROAD_CONFIRMATION` 仅覆盖 46% | 补录「有完整 lifecycle」的历史对象（当前仅 3/13 COMPLETE） |
| **Structural Analogy** | `BLOCKED` | 历史侧仅 2 个 Macro Theme，当前侧已声明 4 个 → 3 个主题无历史可类比；Similarity Pattern 层恒 0 | **补录当前侧已声明的 3 个主题的历史 Cycle** |

### 9.1 这张表的读法

> **它告诉我们：增加什么数据，能够解锁什么研究能力。**
>
> 三条最清晰的解锁路径：
> 1. **补当前侧已声明的 3 个主题** → 解锁 Structural Analogy（从 `BLOCKED` 到 `PARTIAL`）
> 2. **补 2 个独立 Macro Theme** → 让 Time Observation 的「跨族稳健性」第一次**成为可检验命题**
> 3. **建行业事件日历 + 数据发布日历** → 解锁 Event-driven 与 Data-release 两类 Pattern（当前各 0 条候选）

---

## 10. Coverage Ceiling（§十三）

```
theme_family_count 上限 = 2
```

### 10.1 三重后果

| # | 后果 | 说明 |
|---|---|---|
| 1 | **单主题规律不能证明跨主题规律** | v0.2 唯一稳健结构（汽车族 EARLY_SIGNAL）为**单族**，无法证明普适性 |
| 2 | **Structural Analogy 当前受限** | 当前侧声明 4 个 Macro Theme，历史侧仅 2 个 → **至少 3 个主题无历史可类比**；Similarity Pattern 层恒 0 |
| 3 | **Time Observation 跨族稳健性受限** | 跨族稳健性检查在当前数据下**不可能通过** —— 这不是算法问题，是数据问题 |

### 10.2 附加天花板

| 天花板 | 当前值 | 需要达到 |
|---|---|---|
| `theme_family_count` | **2** | ≥ 4 |
| 有效观测年数 | **7**（2019–2025） | ≥ 8 |
| 完成核验的日期 | **0 / 24** | ≥ TOP-01 的 7 个锚点 |
| 连续行情 series | **1** | 每个 Macro Theme ≥ 1 条连续行业指数 |
| 交易日历覆盖 | **2.6 / 8 年** | 8 / 8 年 |

### 10.3 当前侧 vs 历史侧的结构性不对称

| 侧 | 声明的 Macro Theme | 数量 |
|---|---|---:|
| **Current Candidate**（`research/current/`） | 医药健康 · **电力设备** · **信息通信** · **高端装备** | **4** |
| **历史研究**（DB + export） | 汽车 · 医药健康 | **2** |
| **交集** | 医药健康 | 1 |
| **★ 断裂** | **电力设备 / 信息通信 / 高端装备** | **3** |

> **这 3 个主题是「已经存在的断裂」，而不是"可以以后再做的扩展"。**
> 当前侧已经产出候选（`CC-2026-COMPUTE-POWER` / `CC-2026-OFFSHORE-WIND` / `CC-2026-OPTICAL-LINK` / `CC-2026-EMBODIED-AI`），
> 但历史侧一条 Cycle 都没有 → **相似度只能退化为"无历史可比"**。

---

## 11. Priority Framework（§五）

> ⚠️ **这是数据建设优先级，不是投资价值排名。**
> 本审计**不推荐研究哪只股票或哪个行业**。
>
> 每个维度的 `basis` 显式标注：`DATA_DERIVED`（可从数据算出）/ `JUDGMENT`（研究判断）。

### 11.1 八个维度

| key | 维度 | basis |
|---|---|---|
| `a_share_historical_significance` | A股历史重要性 | JUDGMENT |
| `cycle_recurrence_potential` | 历史周期重复潜力 | JUDGMENT |
| `cross_year_coverage_ability` | 跨年份覆盖能力 | DATA_DERIVED |
| `independent_theme_cycle_ability` | 可形成独立 Theme Cycle 的能力 | JUDGMENT |
| `structural_difference_vs_auto_pharma` | 与现有 AUTO / PHARMA 的结构差异 | JUDGMENT |
| `increment_for_structural_analogy` | 对 Structural Analogy 的增量价值 | JUDGMENT |
| `increment_for_time_observation` | 对 Time Observation 的增量价值 | JUDGMENT |
| `current_data_gap_size` | 当前 ThreeC 数据缺口大小 | DATA_DERIVED |

**8 个维度中 6 个是 JUDGMENT** —— 必须诚实标注：这个排序**不是纯数据推导**，其中包含研究判断成分。

### 11.2 排序结果

**排序规则**：先「当前侧已有候选需求」（`has_current_candidate_demand`），再总分，再名称。

| 排名 | 领域 | 总分 | 当前侧需求 | Wave |
|---:|---|---:|---|---|
| 1 | **电力设备** | **24 / 24** | `CC-2026-COMPUTE-POWER` · `CC-2026-OFFSHORE-WIND` | **Wave 1** |
| 2 | **信息通信** | **23 / 24** | `CC-2026-OPTICAL-LINK` | **Wave 1** |
| 3 | **高端装备 / 机器人** | 20 / 24 | `CC-2026-EMBODIED-AI` | Wave 2（历史周期短） |
| 4 | 半导体 / 电子 | 24 / 24 | —（无当前侧候选） | Wave 2 |
| 5 | 金融 / 地产 | 21 / 24 | — | Wave 2 |
| 6 | 有色 / 资源 / 化工 | 20 / 24 | — | Wave 2 |
| 7 | 消费 | 20 / 24 | — | Wave 2 |
| 8 | 军工 | 19 / 24 | — | Wave 2 |

> **注意排名 3 与 4 的取舍**：半导体总分同为 24 但**无当前侧候选**，因此排在「高端装备」之后进入 Wave 2。
> 理由：**先修复已存在的断裂，再做净新增** —— 前者的边际收益（解锁一个已存在的功能）高于后者（解锁一个尚未使用的功能）。

---

## 12. Data Build Waves

### Wave 1 —— 最少补录，最大能力提升

> **目标：修复「当前侧有候选、历史侧无 Cycle」的断裂。**

| 优先级 | 动作 | 解锁什么 | 为什么排第一 |
|---|---|---|---|
| **P0** | 补录「**电力设备**」Macro Theme 的历史 Cycle（≥ 2 个 Campaign，覆盖 ≥ 3 年） | Structural Analogy Pattern 层（当前恒 0）；同时服务 2 个已存在的当前候选 | 当前侧已有 2 个候选，历史侧完全空白 → **边际收益最高** |
| **P0** | 补录「**信息通信**」Macro Theme 的历史 Cycle（≥ 1–2 个 Campaign） | Structural Analogy；并给 Time Observation 提供**第 3 个独立主题族** | 当前侧已有 1 个候选；光通信有多轮清晰历史周期 |
| **P1** | 修复 taxonomy 缺口：为 `C-2019-AD` 挂接 Macro Theme「汽车」 | 消除 v0.2 中 3 条候选「口径脆弱」的根源 | **改动量极小（1 行关联），直接提升已有 Pattern 的稳健性** |
| **P1** | 统一 `evidences.evidence_type` 口径（中英文混用 → 单一枚举） | Evidence Coverage 可统计；Phase Evidence Matrix 的 5 个派生维度可靠 | 纯数据清理，无新研究成本 |
| **P1** | 补录 2018–2025 完整交易日历（当前仅 2022-03 ~ 2024-09） | 所有时间统计可切换到交易日口径（与行情对齐） | 一次性、可自动获取、无研究判断成本 |

**预期能力变化**

| 能力 | 从 | 到 |
|---|---|---|
| Structural Analogy | `BLOCKED` | `PARTIAL`（Pattern 层可匹配） |
| Time Observation | `PARTIAL` | `PARTIAL+`（`theme_family_count` 2 → 4，**跨族稳健性检查首次可用**） |

### Wave 2 —— 扩展跨行业覆盖

> **目标：让「跨主题族规律」第一次成为可检验命题。**

| 优先级 | 动作 | 解锁什么 |
|---|---|---|
| P2 | 补录「**高端装备 / 机器人**」历史 Cycle | 当前侧 `CC-2026-EMBODIED-AI` 可类比；但历史周期短（2023 起），跨年样本有限 |
| P2 | 补录「**半导体 / 电子**」历史 Cycle（2019–2025 多轮周期） | 纯历史补录；提供第 5 个独立族，**显著提升 Time Observation 统计功效** |
| P2 | 补录「**消费**」历史 Cycle | **Calendar-driven / Holiday-relative 能力的天然样本**（春节 / 双十一 / 中报） |
| P3 | 补录「有色 / 资源 / 化工」历史 Cycle | 供给端 + 商品价格机制 —— 与汽车 / 医药**结构差异最大**，类比价值高 |
| P3 | 补录「军工」「金融 / 地产」历史 Cycle | 政策周期样本；但更接近宏观，需先明确 Theme / Macro 边界 |

**预期能力变化**：Time Observation `PARTIAL+` → `USABLE`（`theme_family_count` ≥ 5）；Seasonal `BLOCKED` → `LIMITED`。

### Wave 3 —— 事件 / 日历类深度补录

> **目标：解锁 Event-driven 与真正的 Calendar-driven。**

| 优先级 | 动作 | 解锁什么 |
|---|---|---|
| P2 | 建立结构化「**行业事件日历**」表（车展 / CES / MWC / 开发者大会 / 发布会季） | `INDUSTRY_EVENT_DRIVEN` 从 **0 条** → 可研究 |
| P2 | 建立结构化「**数据发布日历**」表（产销 / 库存 / 价格 / 出口 / PMI） | `DATA_RELEASE_DRIVEN` 从 **0 条** → 可研究；把 LOW 置信度的 post-hoc 机制变为 data-supported |
| P3 | 建立结构化「**制度性日历**」表（财报窗口 / 国常会节奏 / 五年规划 / 预算节奏） | Calendar-driven `PARTIAL` → `USABLE` |
| P3 | 为每个 Macro Theme 补齐**连续行业指数行情** | 中性市场基准可全年份构造；相位对比有共同时间轴 |
| P3 | 补录「**未成势主题**」负样本（观察到但未形成 Campaign） | **唯一能真正量化幸存者偏差的路径**（当前 negative-control coverage = WEAK） |

**预期能力变化**：Event-driven `BLOCKED` → `PARTIAL`；Calendar-driven `PARTIAL` → `USABLE`；Seasonal `LIMITED` → `PARTIAL`。

---

## 13. Data Risks

| # | 风险 | 严重度 | 详情 | 缓解 |
|---|---|---|---|---|
| 1 | **样本量不足（有效观测仅 7 年）** | HIGH | 2019–2025；2018 为反例年 → 所有 N ≤ 7，达不到「稳定规律」档位（N ≥ 8） | 补 2018 之前或 2026+ |
| 2 | **主题族上限 = 2** | HIGH | 跨族稳健性检查在当前数据下**不可能通过** | Wave 1/2 补 ≥ 2 个独立 Macro Theme |
| 3 | **日期核验为 0** | HIGH | 全部 `verified_date` = NULL，全部 `confidence = low` | 人工核验 TOP-01 的 7 个锚点（`PROJECT_STATE` 已列为 Next Single Goal） |
| 4 | **幸存者偏差无法消除** | HIGH | 只记录「形成 Campaign 的主题」；无「未成势」负样本 | Wave 3：补录未成势主题 |
| 5 | **当前侧声明 4 个 Macro Theme，历史侧仅 2 个** | HIGH | 结构性不对称 → 3 个主题无历史可类比 | **Wave 1 P0：优先补录这 3 个主题** |
| 6 | **行情为「窗口采样」而非连续序列** | MEDIUM | 仅 1 条连续；6 条空占位；年度活跃 series 从 15（2022）降到 4（2025） | Wave 3：补连续行业指数 |
| 7 | **Event Calendar 缺 7 类能力关键事件** | MEDIUM | `industry` / `data_release` / `holiday` 等 → 两类 Pattern 无法研究 | Wave 3：建立事件日历表 |
| 8 | **Evidence 口径不统一** | MEDIUM | 中英文混用，schema 无 CHECK 约束 | Wave 1：统一 `evidence_type` 枚举 |
| 9 | **taxonomy 缺口造成判定脆弱** | MEDIUM | 1 个 Campaign 未挂接 Macro Theme；2 个孤立 theme；1 个 export 独有 theme（华为汽车） | Wave 1：修复挂接 + 建立「主题族 ↔ theme」定义表 |
| 10 | **生命周期普遍不完整** | MEDIUM | 13 个对象仅 3 个 COMPLETE；`THEME_FORMING` / `BROAD_CONFIRMATION` 仅 46% | 补录时强制要求完整 lifecycle |
| 11 | **一手来源严重不足** | MEDIUM | tier 1 仅 8 条（15.7%）；`company_announcement` 为 0 | 补录时优先登记公司公告 / 交易所 / 行业协会 |
| 12 | **`company` / `capital` 两类证据完全缺失** | MEDIUM | Phase Evidence Matrix 的公司维度与资金维度**永远无法派生** | 补录这两类证据 |
| 13 | **交易日历仅覆盖 2.6 / 8 年** | LOW | 所有时间统计只能退化为自然日口径 | Wave 1：补全 |

---

## 14. 必须回答的十个问题（§十六）

### Q1 · 当前 ThreeC 有多少独立 Macro Theme？

**2 个**：`TH-AUTO`（汽车）、`TH-PHARMA`（医药健康）。
另注：**Current Candidate 侧已声明 4 个**（多了电力设备 / 信息通信 / 高端装备）。

### Q2 · 每个 Macro Theme 有多少历史 Cycle？

| Macro Theme | Theme Cycles |
|---|---:|
| `TH-AUTO` 汽车 | **8** |
| `TH-PHARMA` 医药健康 | **1** |
| **合计** | **9** |

### Q3 · 哪些主题真正具有跨年份历史周期？

**只有汽车族。** 8 个 Theme Cycle 跨 2019–2025 连续 7 年 —— 这是**唯一具备跨年统计条件**的主题族。
新能源（车用电池）有 3 个 Cycle 但集中在 2020–2022，跨年窗口偏短。

### Q4 · 哪些只有零散事件，不能形成 Cycle？

- **医药健康**：1 个正式 Campaign + 2 个 Research Candidate + 1 个 Cycle → **不构成周期序列**
- **消费**：仅 theme 名称匹配（"汽车消费/购置税刺激"），**无独立 Cycle**
- 其余 **15 个领域**：数据库完全无记录

### Q5 · Lifecycle 哪些完整，哪些残缺？

**完整（COMPLETE）3 个**：`C-2019-PHARMA-INNOV` / `C-2022-POLICY` / `C-2023-AD`
**部分（PARTIAL）9 个**、**稀疏（SPARSE）1 个**（`RC-2024-SECONDARY`）
**残缺集中在**：`THEME_FORMING`（46%）与 `BROAD_CONFIRMATION`（46%）—— 恰是 Formation Anchor 所依赖的两个阶段。

### Q6 · Evidence 哪些类型覆盖最弱？

| 类型 | 条数 | 状态 |
|---|---:|---|
| `company`（公司） | **0** | ❌ 完全缺失 |
| `capital`（资金） | **0** | ❌ 完全缺失 |
| `information`（信息） | 1 | ⚠️ 极弱 |
| `policy`（政策） | 8 | 弱 |
| `industry`（行业） | 11 | 中 |
| `market`（行情） | 31 | 强 |

**另注**：来源层级 tier 1 仅 8 条（15.7%），`company_announcement` 来源类型完全未使用。

### Q7 · Event Calendar 哪些完全缺失？

**NOT_AVAILABLE 共 7 类**：`industry`（产业事件）、`holiday`（节假日 / 日历）、`data_release`（数据发布）、`reporting`（财报披露日）、`meeting`（重大会议）、`trade_fair`（展会）、`product`（产品发布）。

其中 `industry` 与 `holiday` **schema 允许但从未使用**（登记缺口）；其余 5 类 **schema 无对应类型**（结构缺口）。

### Q8 · 未来 Time Observation 最缺什么数据？

1. **独立 Macro Theme**（当前上限 2）→ 跨族稳健性无法检验
2. **连续行情序列**（当前仅 1 条）→ 中性基准无法全年份构造
3. **更多有效观测年**（当前 7 年）→ 达不到 N ≥ 8 的「稳定规律」档位

### Q9 · 未来 Structural Historical Analogy 最缺什么数据？

**最缺「当前侧已声明、历史侧空白」的 3 个 Macro Theme 的历史 Cycle**：
**电力设备 / 信息通信 / 高端装备**。

这是**唯一一个"补了就能立刻解锁一个已存在功能"**的缺口 —— 因为当前侧已经产出候选，
而 Similarity 的 Pattern 层因缺少同名历史 cycle 而**恒为 0**。

### Q10 · 如果只补第一批数据，最合理的 Wave 1 是什么？

**五件事，按此顺序：**

1. **P0** 补录「电力设备」历史 Cycle（≥ 2 Campaign，≥ 3 年）
2. **P0** 补录「信息通信」历史 Cycle（≥ 1–2 Campaign）
3. **P1** 修复 `C-2019-AD` 的 Macro Theme 挂接（**1 行关联**）
4. **P1** 统一 `evidences.evidence_type` 口径
5. **P1** 补全 2018–2025 交易日历

**预期**：Structural Analogy `BLOCKED` → `PARTIAL`；Time Observation `theme_family_count` 2 → 4。

---

## 15. 最终输出格式（§十七）

```text
Historical Coverage Audit v0.1

Dataset
- Campaigns      : 9  (8 汽车族 + 1 医药族)
- Theme Cycles   : 9  (8 auto + 1 pharma)
- Macro Themes   : 2  (TH-AUTO / TH-PHARMA)
- Lifecycle recs : 72 条锚点记录 / 23 行 DB phases
- Evidence       : 51  (market 31 / industry 11 / policy 8 / information 1 / company 0 / capital 0)
- Events         : 30 DB / 33 export  (policy 15 / company 11 / market 4 / macro 0)
- Years          : 2019–2025（有效 7 年；2018 为反例年）

Macro Theme Coverage
- TH-AUTO   : 8 cycles / 8 campaigns / 1 RC / 2019–2025 / lifecycle 10-10 / ev 39
- TH-PHARMA : 1 cycle  / 1 campaign  / 2 RC / 2019–2021 / lifecycle 7-10  / ev 5
- 异常：2 孤立 theme · 1 export-only theme(华为汽车) · 1 Campaign 未挂接 Macro Theme
        · ★ 4 对象存在「resolved vs direct」Macro Theme 解析口径差异

Lifecycle Coverage
- COMPLETE 3 / PARTIAL 9 / SPARSE 1 / UNKNOWN 0
- 最弱：THEME_FORMING 46% · BROAD_CONFIRMATION 46% · FIRST_DECLINE 8%

Evidence Coverage
- company 0 · capital 0 · information 1   ← 两类完全缺失
- tier 1 仅 8/51（15.7%）· company_announcement 来源类型未使用
- temporal_relation unknown 7 条

Event Coverage
- NOT_AVAILABLE 7 类：industry / holiday / data_release / reporting / meeting / trade_fair / product
- DECLARED_UNUSED 1 类：macro

Research Capability Matrix
- Time Observation   PARTIAL
- Seasonal           BLOCKED
- Calendar-driven    PARTIAL
- Event-driven       BLOCKED
- Phase Transition   LIMITED
- Structural Analogy BLOCKED

Coverage Ceiling
- theme_family_count 上限 = 2
- 当前侧声明 4 个 Macro Theme，历史侧 2 个 → 3 个主题无历史可类比
- 有效观测 7 年（需 ≥ 8）· 连续行情 1 条 · 核验日期 0/24

Wave 1  P0 电力设备 Cycle · P0 信息通信 Cycle · P1 修 C-2019-AD 挂接 · P1 统一 evidence_type · P1 补交易日历
Wave 2  高端装备/机器人 · 半导体/电子 · 消费 · 有色/资源/化工 · 军工 · 金融/地产
Wave 3  行业事件日历 · 数据发布日历 · 制度性日历 · 连续行业指数 · 未成势主题负样本

Data Risks  HIGH×5 / MEDIUM×7 / LOW×1（共 13 项）

Recommended Next Action
- 优先补录「电力设备」与「信息通信」的历史 Cycle
  （理由：修复"当前侧有候选、历史侧无 Cycle"的已存在断裂，边际收益最高）
- 同时执行 3 项 P1 低成本清理（挂接修复 / evidence_type 统一 / 交易日历补全）
```

---

## 16. 诚实限制清单

1. **优先级框架含 JUDGMENT 成分**：8 个维度中 6 个是研究判断，不是数据计算结果。**这不是纯数据推导的排序。**
2. **`macro_theme_matrix` 用的是 `resolved` 口径**（沿 parent 链），而 v0.2 Discovery 用的是 `direct` 口径（按名称匹配）→ 两者的 `theme_family_count` 成员集合不同。本审计已把差异**显式列出**（4 个对象），未静默选择其一。
3. **`theme_cycles` 使用 export 的 `theme_cycle_id`**，不是 `rule_id`（rule 是观察规则，不是主题周期）。
4. **Event Coverage 的 `NOT_AVAILABLE` 只表示"数据库无记录"**，不表示机制不存在（§5.3）。
5. **Lifecycle 评级是启发式规则**（COMPLETE / PARTIAL / SPARSE），**未补齐任何缺失阶段**。
6. **`evidence_type` 归一化映射是人工定义的**；若未来统一口径，映射表应同步更新。
7. **行情 `sampling_class` 判据为「年度跨度」**，不评价数据质量或复权正确性。
8. 本审计**只读**，未修改任何 DB / schema / export / 产品代码。

---

## 17. 最终原则声明

> **本审计不回答"应该研究什么股票 / 行业"。**
>
> 只回答：
> **ThreeC 的历史研究数据还缺什么，以及优先补什么数据最能提高整个系统的研究能力。**
>
> **结论**：
> 1. 瓶颈是**数据覆盖**，不是 Pattern Discovery 算法。
> 2. 最值得补的第一批数据是**当前侧已声明、历史侧空白的 3 个 Macro Theme**（电力设备 / 信息通信 / 高端装备）—— 这是**已经存在的断裂**。
> 3. 同时有 3 项**低成本高收益**的清理动作（挂接修复 / evidence_type 统一 / 交易日历补全），可在同一轮完成。
> 4. 数据建设的**正确顺序**是：先修复已存在的断裂 → 再扩展净新增覆盖 → 最后做事件 / 日历深度补录。
>
> **不要一次把整个 A 股历史全部录完。**

---

*报告结束 · Historical Coverage Audit v0.1 · 2026-09-16*
