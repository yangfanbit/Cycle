# Research Model v1.0（研究模型冻结版）

> 本文档定义 **A股历史规律研究模型 v1.0**，用于统一研究方法论，确保长期可扩展性。
> **本模型是研究状态，不是交易信号；不做预测/概率/seasonality。**
> 冻结日期：2026-09-13

---

## 1. Rule（研究规则）

### 定义
研究假设 / 历史观察窗口，用于探索 A股行业/题材/时间规律。

### 属性
- `rule_id`：规则标识（如 `rule_auto_summer`）
- `rule_type`：规则类型（seasonal / thematic / event-driven）
- `status`：candidate / under_review / confirmed / weak / rejected
- **属于 Research Prior / Hypothesis**，不是市场事实

### 示例
- `rule_auto_summer`：汽车夏季历史观察窗口（6-8月）

---

## 2. Research Signal（研究信号）

### 定义
尚未形成正式 Campaign，但已值得开始观察的信号。

### 状态枚举
| Signal State | 含义 | 约束 |
|---|---|---|
| **EARLY_SIGNAL** | 最早值得观察的异动/关注 | 可早于正式催化 |
| **THEME_FORMING** | 主题初具雏形，龙头/叙事确立 | 尚未广泛识别 |
| **CONFIRMATION_CANDIDATE** | 可能升级为正式 Campaign 的候选 | 待验证 |

### 关键约束
- **不属于 Campaign Phase**，不得写入 `campaign_phases` 表
- 用 Point-in-Time 信息判断，不事后倒推
- 非交易信号，仅为研究描述

---

## 3. ThemeCycle（主题周期）

### 定义
同一主题家族下的研究归组，可包含多个 Campaign。

### 属性
- `theme_cycle_id`：研究级标签（如 `auto_policy_2022`）
- **Research-level grouping**，不是 Market Fact
- 不创建正式 `theme_cycles` 表

### 示例
- `auto_intelligence_2023`：包含 Smart Driving + Huawei Auto 两个 Campaign

---

## 4. Campaign Candidate（战役候选）

### 定义
研究级候选，尚未达到正式 Campaign 门槛。

### 属性
- `research_campaign_id`：研究级标识（如 `RC-2023-HUAWEI`）
- 保留在 `research/c2/` 文件中
- **不能进入** `campaigns` 表，除非人工确认

### 示例
- `RC-2023-HUAWEI`：Huawei Auto 2023（研究候选）

---

## 5. Historical Campaign（历史战役）

### 定义
已确认的历史市场行情，具有明确主题、持续性、市场关注。

### 属性
- `campaign_id`：正式标识（如 `C-2022-POLICY`）
- `campaign_year`：年份
- `start_date` / `end_date` / `peak_date`：正式事实层
- `classification`：theme_campaign / industry_trend / event_driven / mixed / unclear
- `strength`：strong / medium / weak
- `result`：positive / neutral / weak / failed / unknown

### 判定标准（Campaign vs Observation）
**Campaign 至少需要**：
1. 明确 Theme
2. 持续性
3. 市场关注
4. 可解释 start/end
5. ≥2 独立 Evidence

**Observation**：
- 只能证明个股异动/单日脉冲/零散新闻/证据不足
- **不得升级为 Campaign**

---

## 6. Campaign Status（战役状态）

### 状态枚举
| Status | 含义 |
|---|---|
| **candidate** | 候选，待验证 |
| **confirmed** | 已确认 |
| **weak** | 弱，证据不足 |
| **rejected** | 已拒绝 |

**注意**：`confirmed` 是 Campaign status，不是 Campaign Phase。

---

## 7. Campaign Phase（战役阶段）

### 定义
Historical Campaign 的正式阶段，记录已确认的市场行情结构。

### 状态枚举
| Phase State | 含义 | 关键区分 |
|---|---|---|
| **MAIN_RISE** | 主升：板块/核心样本持续一致上行 | — |
| **PEAK** | 主升顶点（允许 cluster） | — |
| **RETRACEMENT** | 正常回撤，主题可能恢复 | 幅度/时间未破坏主升结构 |
| **DECLINING** | 主题持续性明显下降 | 资金持续流出，难以恢复 |
| **SECONDARY** | 次级活跃/二次新高 | 可能仅部分个股 |
| **ENDED** | 主题失去持续主导 | 进入冷却或结束 |

### 关键约束
- **Campaign start 后才能产生 Campaign Phase**
- Research Signal（EARLY_SIGNAL/THEME_FORMING）**不属于** Campaign Phase
- `CONFIRMED` **不属于** Phase，是 Campaign status

---

## 8. Event（事件）

### 定义
市场催化事件，如政策发布、产品发布、行业数据等。

### 属性
- `event_id`：事件标识
- `event_type`：policy / industry / macro / company / market / news / holiday / other
- `date`：事件日期
- **Layer 1 Fact**：客观数据

---

## 9. Evidence（证据）

### 定义
支持或反驳 Campaign 的证据，必须显式绑定。

### 属性
- `evidence_id`：证据标识
- `evidence_role`：supporting / contradicting / context
- `temporal_relation`：contemporaneous / prior / subsequent / retrospective / unknown
- `independence_group`：独立性分组（用于判断独立证据数量）
- **Layer 1 Fact**：客观数据

### 绑定规则
- **必须**通过 `campaign_evidences` 桥表显式绑定
- **允许 unbound**：支持整个 Rule 的证据 / 无法属于某个 Campaign 的反例
- **禁止**全库 Evidence 挂到一个 Campaign

### 证据数量要求
- **Research Confirmed**：≥2 Evidence + ≥2 independence_group
- **禁止**：同一原文转载算作两个独立来源

---

## 10. Security（证券）

### 定义
Campaign 相关的股票 / 指数 / ETF。

### 属性
- `security_id`：证券标识
- `security_type`：stock / index / etf
- `role`：leader / second_leader / representative / follow
- **Layer 1 Fact**：客观数据

---

## 11. Point-in-Time（当时视角）

### 定义
站在当时，仅能使用当时已公开的信息。

### 约束
- **不得**用后来信息证明当时已知道某股票是 Leader
- **属于 Research Observation**，不是 Fact 本身
- 是"当时可观察的信息集合"

### Leader 命名
- **Historical Leader Set**：完整行情结束后回看确认（复盘）
- **Point-in-Time Basket**：截至具体日期当时可识别（提前观察）
- **禁止混用**

---

## 12. Retrospective（回顾视角）

### 定义
站在今天回看过去，可以使用后来发生的结果/公告/最终价格。

### 用途
- 复盘
- 验证 Campaign 边界
- 确认 Historical Leader

---

## 13. Three Layers（三层语义）

### Layer 1 — Fact（事实层）
- **Market Data**：价格、成交量
- **Event**：政策、公告
- **Evidence**：证据
- **Security**：股票、指数
- **Source**：来源

### Layer 2 — Interpretation（解释层）
- **Campaign**：历史战役
- **Campaign Phase**：战役阶段
- **Annual Review**：年度评审

### Layer 3 — Grouping（归组层）
- **ThemeCycle**：主题周期
- **Theme Drift**：主题漂移
- **Campaign Relation**：战役关系

**约束**：三层不能混淆。

---

## 14. Campaign vs Observation（战役 vs 观察）

### Campaign 判定标准
**至少需要**：
1. 明确 Theme
2. 持续性
3. 市场关注
4. 可解释 start/end
5. ≥2 独立 Evidence

### Observation 判定标准
**只能证明**：
- 个股异动
- 单日脉冲
- 零散新闻
- 证据不足

**约束**：Observation 不得升级为 Campaign。

### 示例
- **2022 中通客车**：12连板（+214.52%）但系"核酸检测车"概念个股事件 → **Observation**
- **2023 Huawei Auto**：有明确主题但尚未达到正式 Campaign 门槛 → **Research Candidate**

---

## 15. Evidence Governance（证据治理）

### 来源分级（Source Tier）
| Tier | 定义 | 示例 |
|---|---|---|
| **Tier 1** | 交易所 / 监管机构 / 政府 / 公司正式公告 / 财报 | 证监会、国务院、公司公告 |
| **Tier 2** | 中国证券报 / 证券时报 / 第一财经 / 财联社 / 界面 / 新华社 / 权威行业协会 | 中证报、证券时报、财联社 |
| **Tier 3** | 券商研报 / 研究机构 / 专业财经网站 | 券商研报、Wind、同花顺 |
| **Tier 4** | 雪球 / 自媒体 / 论坛 / 博客 / 社交媒体 | 雪球、微博、知乎 |

### 约束
- **Tier 4 只能作为线索**，不能单独使 Campaign 成为 Research Confirmed
- `source_type` 与 `tier` 不得矛盾

---

## 16. Bias Controls（偏差控制）

### Survivorship Bias
- Leader Basket 标记 `survivorship-aware / retrospective`
- 明确说明基于事后确认的幸存者

### Look-Ahead Bias
- PIT 研究仅用当时已公开信息
- Retrospective 研究明确标注使用 hindsight

### Beta Contamination
- 识别市场整体 β 对主题表现的影响
- 无法排除 contamination 时，保持低置信度

---

## 17. 2022/2023/2024 Examples（案例）

### 2022 Auto Policy（theme_cycle_id = auto_policy_2022）

**Research Signals**：
- 04-27 EARLY_SIGNAL：行业修复/Setup
- 05-23 THEME_FORMING：国常会购置税600亿政策

**Campaign Phases**：
- Campaign Start: 05-23
- Broad Confirmation: 06-01
- Main Rise: 05-23 → 06-28
- Peak: cluster {06-23, 06-28}
- Retracement: 07月
- Declining: 08月
- End: 08月后续

**特殊处理**：
- 中通客车 = Observation（核酸检测车概念，非汽车主题）

### 2023 Auto Intelligence（theme_cycle_id = auto_intelligence_2023）

**Campaign 1: Smart Driving**
- Research Signals: 06-12 (EARLY_SIGNAL), 06-21 (THEME_FORMING)
- Campaign Start: 06-21
- Main Rise: 07-03 ~ 07-19
- End: ≈09-12

**Campaign 2: Huawei Auto**
- Research Signals: 08-29 (EARLY_SIGNAL Candidate), 09-04 (THEME_FORMING)
- Campaign Start Candidate: 09-12
- Broad Confirmation: 09-18
- Main Rise: 09下~10

**Theme Drift**：Smart Driving → Huawei Auto
**Campaign Overlap**：08-29~09-12 重叠

### 2024 Robotaxi（theme_cycle_id = robotaxi_2024）

**Research Signals**：
- 07-08 EARLY_SIGNAL：萝卜快跑武汉跑出圈

**Campaign Phases**：
- Broad Confirmation: 07-10
- Main Rise: 07→
- Peak: 08-05
- First Decline: 08-06
- Main Campaign End: 08-23
- Secondary: 09-05~06（Weak Candidate）

---

## 18. 纪律

- 真实历史事实优先，不为证明 Rule 而修改研究结果
- 宁可 unknown / candidate / no_clear_campaign，也不伪装 verified
- 所有关键定义明确标注来源/研究者解释/暂定假设
- 禁止"大家都知道" / "显然" / "通常" / "经验上" 而无依据
- 不计算 seasonality_score / win_rate / probability / predictive_model
- 不扩展新的模型概念，保持 v1.0 冻结

---

## 19. 导出层

### 正式导出
- `formal_campaigns`：仅包含 `campaigns` 表中的正式 Campaign
- `research_candidates`：保留在 `research/c2/` 文件中，不自动混入正式导出

### JSON Meta
必须明确说明：研究候选不会自动混入正式 Campaign。

---

## 20. Rule 最终评价

### "6—8月汽车" 定义
**历史观察窗口**（Historical Observation Window）

### 最终评价
**Partially Supported**（部分支持）

### 约束
- 这是 **research conclusion**，不是预测
- 需结合 Research Signal 触发
- 需排除市场 β contamination
- 强度需根据具体年份评估
