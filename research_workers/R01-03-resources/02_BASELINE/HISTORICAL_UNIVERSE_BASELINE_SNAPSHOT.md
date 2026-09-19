# HISTORICAL_UNIVERSE_BASELINE_SNAPSHOT.md

> ## ⚠️ READ_ONLY BASELINE SNAPSHOT
>
> 本文件是**只读基线快照**，描述 ThreeC 在 `2153f6d83b7481300696ab73d792e9e53aa31a07` 时的**已有状态**。
> **它不是 DB**，**不是 DB dump**，**不包含完整数据库内容**。
> 它**只用于**让 Research Worker 理解「现在已经有什么」，从而判断哪些方向是**真正的空缺**。
>
> **不得**据此推断任何研究结论。**不得**把它当作 Evidence。

- **source_threec_commit**: `2153f6d83b7481300696ab73d792e9e53aa31a07`
- **snapshot_kind**: `READ_ONLY_BASELINE_SNAPSHOT`
- **本任务**: `R01-03`

---

## A. 当前 canonical Macro Theme

当前 DB `themes` 表中的**根节点**（`parent_theme_id IS NULL`）共 **4** 个：

| # | Macro Theme |
|---|---|
| 1 | 汽车 |
| 2 | 医药健康 |
| 3 | 信息通信 |
| 4 | 电力设备 |

> ⚠️ **一个 Macro Theme 只出现一次，不代表已经形成充分历史覆盖。**
> 覆盖面 = 该族内**机制 / 生命周期 / 事件结构**的多样性，不是「族名出现过」。

**唯一事实来源**：DB `themes` 表。
Macro Theme 的 canonical 解析只能由 ThreeC Agent 用 **CMTR v1**（`theme_taxonomy.py`，规则集
`canonical-macro-theme-resolution-1`）完成。**不接受任何硬编码的「主题族名称表」。**

---

## B. 当前历史对象

### B.1 Historical Campaign（13 个）

| campaign_id | year | title / themes | Macro Theme | 状态 |
|---|---:|---|---|---|
| `C-2019-AD` | 2019 | 汽车 · 智能驾驶/无人驾驶 | 汽车 | campaign · event_driven · weak |
| `C-2019-COMM-5G` | 2019 | 信息通信 · 5G网络建设/通信设备 | 信息通信 | campaign · theme_campaign · strong |
| `C-2019-PHARMA-INNOV` | 2019 | 医药健康 · 创新药 / CXO | 医药健康 | campaign · theme_campaign · strong |
| `C-2020-NEV` | 2020 | 汽车 · 新能源汽车/电池 / 特斯拉产业链 | 汽车 | campaign · theme_campaign · strong |
| `C-2020-POWER-NE` | 2020 | 电力设备 · 光伏/新能源发电设备 / 风电设备 | 电力设备 | campaign · theme_campaign · strong |
| `C-2021-NEV` | 2021 | 汽车 · 新能源汽车/电池 | 汽车 | campaign · theme_campaign · strong |
| `C-2022-POLICY` | 2022 | 汽车 · 汽车消费/购置税刺激 / 新能源汽车 | 汽车 | campaign · theme_campaign · strong |
| `C-2022-POWER-GRID` | 2022 | 电力设备 · 电网/输变电设备 | 电力设备 | campaign · industry_trend · strong |
| `C-2023-AD` | 2023 | 汽车 · 智能驾驶/无人驾驶 | 汽车 | campaign · theme_campaign · medium |
| `C-2023-COMM-OPTICAL` | 2023 | 信息通信 · 光模块/高速光互联 | 信息通信 | campaign · theme_campaign · strong |
| `C-2024-ROBOTAXI` | 2024 | 汽车 · Robotaxi/无人驾驶/智能网约车 | 汽车 | campaign · theme_campaign · strong |
| `C-2024-V2X` | 2024 | 汽车 · 车路云一体化/车路协同 | 汽车 | campaign · theme_campaign · medium |
| `C-2025-ROBOTAXI` | 2025 | 汽车 · Robotaxi / 智能驾驶 | 汽车 | campaign · theme_campaign · medium |

### B.2 Research Candidate（4 个，**不是** Confirmed Campaign）

| research_candidate_id | year | title | Macro Theme | 状态 |
|---|---:|---|---|---|
| `RC-2020-PANDEMIC` | 2020 | 2020 疫情医疗（防护耗材 / 体外诊断 / 疫苗） | 医药健康 | research_candidate · PROVISIONAL |
| `RC-2021-TCM` | 2021 | 2021–2022 中医药（品牌中药 / 中药创新 / 抗疫中药） | 医药健康 | research_candidate · PROVISIONAL |
| `RC-2023-HUAWEI` | 2023 | Huawei Auto 2023（华为汽车 / AITO M7 / ADS2.0） | 汽车 | research_candidate · PROVISIONAL（taxonomy gap F7） |
| `RC-2024-SECONDARY` | 2024 | 2024 Robotaxi Secondary（弱次级行情候选） | 汽车 | research_candidate · PROVISIONAL |

> `RC-*` 是**研究候选**，永远不是 Confirmed Historical Campaign。
> `RC-2023-HUAWEI` 存在已知 taxonomy gap（题材「华为汽车」不在 DB `themes` 表中）。

**Historical Object 合计 = 17**（13 Campaign + 4 Research Candidate）

### B.3 当前 taxonomy（DB `themes`，19 行）

| theme_id | name | theme_type | parent |
|---|---|---|---|
| `TH-AUTO` | 汽车 | industry | —（根） |
| `TH-NEV` | 新能源汽车/电池 | industry | 汽车 |
| `TH-AD` | 智能驾驶/无人驾驶 | concept | 汽车 |
| `TH-ROBOTAXI` | Robotaxi/无人驾驶/智能网约车 | concept | 汽车 |
| `TH-V2X` | 车路云一体化/车路协同 | concept | 汽车 |
| `TH-CAR-CONSUMPTION` | 汽车消费/购置税刺激 | concept | 汽车 |
| `TH-TESLA-CHAIN` | 特斯拉产业链 | concept | 新能源汽车/电池 |
| `TH-PHARMA` | 医药健康 | industry | —（根） |
| `TH-PHARMA-INNOV` | 创新药 | concept | 医药健康 |
| `TH-PHARMA-CXO` | CXO(研发外包) | concept | 医药健康 |
| `TH-PHARMA-PANDEMIC` | 疫情医疗 | concept | 医药健康 |
| `TH-PHARMA-TCM` | 中医药 | concept | 医药健康 |
| `TH-COMM` | 信息通信 | industry | —（根） |
| `TH-COMM-5G` | 5G网络建设/通信设备 | concept | 信息通信 |
| `TH-COMM-OPTICAL` | 光模块/高速光互联 | concept | 信息通信 |
| `TH-POWER` | 电力设备 | industry | —（根） |
| `TH-POWER-PV` | 光伏/新能源发电设备 | concept | 电力设备 |
| `TH-POWER-WIND` | 风电设备 | concept | 电力设备 |
| `TH-POWER-GRID` | 电网/输变电设备 | concept | 电力设备 |

---

## C. 当前历史覆盖概况

| 项 | 值 |
|---|---:|
| Macro Theme（根节点） | **4** |
| Historical Campaign | **13** |
| Research Candidate | **4** |
| Historical Object（合计） | **17** |
| DB `themes` 行 | **19** |
| DB `events` 行 | **49** |
| DB `evidences` 行 | **83** |
| DB `sources` 行 | **85** |
| DB `securities` 行 | **48** |
| `campaign_date_observations` | **24**（其中 `verified` = **0**） |
| Structural Analogy 历史对象 | **17** |
| Structural Analogy 比较对数 | **85** |

### 当前主要缺口

| 缺口 | 说明 |
|---|---|
| **Macro Theme 数量过少** | 仅 **4** 个族 → 跨族结构对应在结构上只能落在 `C(4,2) = 6` 个族对组合上 |
| **机制轴缺失** | 当前 4 族的机制集中在：政策驱动 · 技术突破 · 产业升级 · 需求爆发。**四条机制轴完全缺失**（见下表） |
| **SA STRICT 极稀** | 85 条比较中 `STRUCTURAL_SUPPORTED` 仅 4 条，**STRICT 仅 1 条** |
| **日期核验未完成** | `campaign_date_observations` verified = **0 / 24**（Future Data Precision Debt） |

### 当前机制轴分布

| 机制轴 | 当前是否存在 | 主要来源族 |
|---|---|---|
| 政策驱动 POLICY_DRIVEN | 有 | 汽车 / 医药健康 / 信息通信 / 电力设备 |
| 技术突破 TECH_BREAKTHROUGH | 有 | 汽车 / 信息通信 |
| 产业升级 INDUSTRY_UPGRADE | 有 | 汽车 / 电力设备 |
| 需求爆发 DEMAND_SURGE | 有 | 电力设备 / 信息通信 |
| 供给收缩 SUPPLY_CONTRACTION | ★ 缺失 | （本任务可能是主要来源） |
| 纯需求端驱动（消费） | ★ 缺失 | （本任务可能是主要来源） |
| 流动性 / 政策周期 | ★ 缺失 | （本任务可能是主要来源） |
| 订单 / 事件驱动 | ★ 缺失 | （本任务可能是主要来源） |

### 时间范围

| 层级 | 年份 | 性质 |
|---|---|---|
| **Priority A** | **2018–2025** | **当前 ThreeC 历史主宇宙**。必须独立可交付，不得被 Priority B 阻塞 |
| **Priority B** | **2015–2017** | **本轮回填区**。允许大面积 `INSUFFICIENT` |

---

## D. 已知缺口（本轮的扩容方向）

| # | family 方向 | 为什么目前属于扩容方向 |
|---|---|---|
| 5 | **高端装备 / 机器人** | 当前 DB `themes` 中**不存在**该方向根节点；机制（制造升级 / 产业政策）与已有族不同 |
| 6 | **半导体 / 电子** | A 股历史上有多次**独立**政策 + 国产替代驱动的周期，机制与「信息通信」可分离 |
| 7 | **资源 / 有色 / 化工** | 当前 4 族**完全没有「供给收缩 / 涨价」**型机制 |
| 8 | **消费** | 当前 4 族**完全没有「需求端」**驱动机制 |
| 9 | **金融 / 地产** | 当前 4 族**完全没有「流动性与政策周期」**驱动 |
| 10 | **军工** | 当前 4 族**完全没有「订单 / 事件驱动」**机制 |

### 本任务（`R01-03`）相关提示

本任务对应新增方向「资源 / 有色 / 化工」。当前 4 族**完全缺失「供给收缩 / 涨价」机制轴** —— 本任务是该机制的主要来源。

> ⚠️ **扩容的目的不是提高 `STRUCTURAL_SUPPORTED` 数量**（那是被禁止的动机）。
> 目的是让**跨族结构对应有足够多的真实候选可比较** ——
> 从而让「**没有对应**」这个结论也更有信息量。

---

## E. 明确声明

> 本文件是 **`READ_ONLY BASELINE SNAPSHOT`**。
>
> - **不是** DB
> - **不是** DB dump
> - **不包含**完整数据库内容
> - **不是** Evidence
> - **不得**被用作任何研究结论的依据
>
> 它只描述「ThreeC 在 `2153f6d83b7481300696ab73d792e9e53aa31a07` 时已经有什么」。
> Research Worker 的任务是**补充它没有的**，而不是复述它已有的。
