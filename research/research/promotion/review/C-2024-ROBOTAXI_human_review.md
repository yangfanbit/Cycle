# Human Final Review Dossier — C-2024-ROBOTAXI

> **性质**：本文件为 Human Final Review Pack（人工最终核验材料包）。**本轮最重要的 Review**。
> **范围**：只整理现有 Research Evidence / Market Data / 研究报告；不新增研究、不改 DB、不改日期。
> **状态**：所有日期均为 **候选（Candidate）**；**Verified Date 尚不存在**。人工 Decision 栏统一留空。
> **术语**：`Historical Leader Equal-Weight Index`（EW）= 事后选定的 5 只核心股票（大众交通/锦江在线/金龙汽车/星网宇达/天迈科技）等权归一化指数，base 2024-07-08=100，raw close 信号口径。**这是历史复盘指数，不是板块指数、也不是投资者当时可获得的收益。**

---

## 1. Current DB Candidate

| 字段 | 值 |
|---|---|
| campaign_id | C-2024-ROBOTAXI |
| start_date | 2024-07-08 |
| peak_date | 2024-07-29 |
| end_date | 2024-07-31 |
| strength | strong |
| result | positive |
| classification | theme_campaign |
| source_id | S-2024-05 |
| date_confidence | medium |

**明确**：以上为 **DB Candidate**（campaigns 表当前记录的研究候选值），**不是 Verified Fact**。start/peak/end 在 `campaign_date_observations` 中 verified 均为 NULL、confidence=low、method=market_data。

---

## 2. Research Review Candidates（DB Candidate 与 Market Data Research Candidate 并排）

### 并排总表

| 字段 | DB Candidate | Market Data Research Candidate |
|---|---|---|
| Start | 2024-07-08 | **2024-07-08**（起势日）；首个 Index 大日（Retrospective Confirmation）07-09；**Broad Theme Confirmation（PIT 可辩护）07-10** |
| Peak | 2024-07-29 | **2024-08-05**（EW raw 峰值 234.8；07-30 为中途高 230.3） |
| First Decline | （无此字段） | **2024-08-06**（EW 234.8→214.1，单日 -8.8%） |
| Main End | 2024-07-31 | **2024-08-23**（Main Campaign End / Major Breakpoint） |

> **严格区分**：`Candidate`（候选日期）与 `First Decline`（首次显著回撤）是两个不同概念。**First Decline ≠ End**。07-31 是中途回撤、08-06 是 First Decline、08-23 是 Main End Candidate——**不得混成一个 "End"**。

### Start
| 候选 | 语义 | 来源 |
|---|---|---|
| **2024-07-08** | 起势日（EW 基准 100；大众交通 +6.12% 启动） | DB Candidate；`2024_robotaxi_point_in_time.md` §3 |
| 2024-07-09 | 首个 Index 大日（EW 单日 +10.1%）——**Retrospective Confirmation / 事后增强**，当时 PIT 可确认的仅大众（低置信） | `2024_robotaxi_point_in_time.md` §3；`2024_robotaxi_continuity_review.md` §10 |
| **2024-07-10** | Broad Confirmation（PIT 可辩护）：天迈获当日证券时报点名（E-2024-05），板块 +4%，萝卜快跑媒体全面发酵 | `2024_robotaxi_continuity_review.md` §10；E-2024-05 |

### Peak
| 候选 | 语义 | 来源 |
|---|---|---|
| **2024-07-29** | DB Candidate（财联社焦点复盘"大众交通 16 日涨 233%"报道日；EW 当日 210.8） | DB Candidate；E-2024-06 |
| **2024-08-05** | EW raw 峰值 234.8（大众 08-05 见顶 11.22 拉高指数） | `2024_robotaxi_market_validation.md` Peak 节；`2024_robotaxi_point_in_time.md` §4 |

### First Decline（独立概念，非 End）
| 候选 | 语义 | 来源 |
|---|---|---|
| **2024-08-06** | 首个显著回撤（EW 234.8→214.1，-8.8%）；07-31 只是中途回撤（230.3→218.2），被 08-05 新高覆盖，不构成 First Decline | `2024_robotaxi_point_in_time.md` §5；`2024_robotaxi_market_validation.md` First Decline 节 |

### Main End
| 候选 | 语义 | 来源 |
|---|---|---|
| **2024-07-31** | DB Candidate（大众交通 9 连板终结 -2.65%、大众公用天地板港股暴跌 22.75%） | DB Candidate；E-2024-07 |
| **2024-08-23** | Main Campaign End / Major Breakpoint：08-21/08-22 重新活跃（EW 207.6/207.3）被 08-23 单日 -4.6% 跳水（197.8）打断；其后 08-26→08-30 持续走弱、无集体回升、个股不再同步 → 主题失去持续主导地位 | `2024_robotaxi_point_in_time.md` §7；`2024_robotaxi_continuity_review.md` §9 |

---

## 3. 证据按日期组织

绑定 Evidence 共 4 条，independence_group 共 4 个（orig_robotaxi_momentum / orig_robotaxi_leader / orig_robotaxi_retreat / orig_robotaxi_thirdwave）。

### 2024-07-08（Start 候选：起势日）

| 字段 | 值 |
|---|---|
| Evidence ID | N/A（无 evidence_date=2024-07-08 的绑定证据行） |
| Source ID | N/A |
| Source Title | N/A |
| Published Date | N/A |
| Evidence Date | N/A |
| Evidence Role | N/A |
| Temporal Relation | N/A |
| Confidence | N/A |
| Independence Group | N/A |

关联（非直接绑定该日）：
- E-2024-05（group=orig_robotaxi_momentum，published 2024-07-10）内容提及"7 月上中旬萝卜快跑武汉跑出圈订单暴涨"；DB start_date_basis 记"7/8 大众交通启动"。
- 行情观测：大众交通 07-08 放量 +6.12%；EW 基准 100。

### 2024-07-09（首个 Index 大日）

| 字段 | 值 |
|---|---|
| Evidence ID | N/A |
| Source ID | N/A |
| Source Title | N/A |
| Published Date | N/A |
| Evidence Date | N/A |
| Evidence Role | N/A |
| Temporal Relation | N/A |
| Confidence | N/A |
| Independence Group | N/A |

- 仅行情观测：EW 单日 +10.1%（110.1）；大众交通一字板；锦江/星网当日一字连板（媒体盘后归因）。

### 2024-07-10（Broad Confirmation）

| Evidence ID | Source ID | Source Title | Published Date | Evidence Date | Evidence Role | Temporal Relation | Confidence | Independence Group |
|---|---|---|---|---|---|---|---|---|
| E-2024-05 | S-2024-04 | 无人驾驶+车路云共涨：板块指数大涨超4%，天迈/经纬恒润20cm涨停，德赛西威涨停 | 2024-07-10 | 2024-07-10 | supporting | contemporaneous | high | orig_robotaxi_momentum |

- 事件表：EV-2024-03（2024-07-10，market，role=trigger）"萝卜快跑武汉跑出圈，无人驾驶板块大涨 4%"。

### 2024-07-29（Peak 候选：DB Candidate）

| Evidence ID | Source ID | Source Title | Published Date | Evidence Date | Evidence Role | Temporal Relation | Confidence | Independence Group |
|---|---|---|---|---|---|---|---|---|
| E-2024-06 | S-2024-05 | 焦点复盘：大众交通16日涨233%，锦江15天9板、金龙12天7板 | 2024-07-29 | 2024-07-29 | supporting | contemporaneous | high | orig_robotaxi_leader |

- 行情观测：EW 07-29 = 210.8（非窗口峰值）。

### 2024-07-31（End 候选：DB Candidate / 中途回撤）

| Evidence ID | Source ID | Source Title | Published Date | Evidence Date | Evidence Role | Temporal Relation | Confidence | Independence Group |
|---|---|---|---|---|---|---|---|---|
| E-2024-07 | S-2024-06 | 大众交通终结9连板神话，大众公用A股"天地板" | 2024-08-01 | 2024-07-31 | contradicting | contemporaneous | high | orig_robotaxi_retreat |

- 注：E-2024-07 的 evidence_date=2024-07-31（事件日），source published_at=2024-08-01（次日报道）。
- 行情观测：EW 07-31 = 218.2（自 07-30 中途高 230.3 回撤）。

### 2024-08-05（Peak 候选：EW 峰值）

| 字段 | 值 |
|---|---|
| Evidence ID | N/A |
| Source ID | N/A |
| Source Title | N/A |
| Published Date | N/A |
| Evidence Date | N/A |
| Evidence Role | N/A |
| Temporal Relation | N/A |
| Confidence | N/A |
| Independence Group | N/A |

- 仅行情观测：EW raw = 234.8（窗口峰值）；大众 08-05 见顶 11.22。

### 2024-08-06（First Decline）

| 字段 | 值 |
|---|---|
| Evidence ID | N/A |
| Source ID | N/A |
| Source Title | N/A |
| Published Date | N/A |
| Evidence Date | N/A |
| Evidence Role | N/A |
| Temporal Relation | N/A |
| Confidence | N/A |
| Independence Group | N/A |

- 仅行情观测：EW 234.8 → 214.1，单日 -8.8%。

### 2024-08-23（End 候选：Major Breakpoint）

| 字段 | 值 |
|---|---|
| Evidence ID | N/A |
| Source ID | N/A |
| Source Title | N/A |
| Published Date | N/A |
| Evidence Date | N/A |
| Evidence Role | N/A |
| Temporal Relation | N/A |
| Confidence | N/A |
| Independence Group | N/A |

- 仅行情观测：EW 08-22 207.3 → 08-23 197.8（单日 -4.6% 跳水）；其后 08-26 191.8 → 08-30 188.6 持续走弱。

### 上下文（Context，非日期候选）

| Evidence ID | Source ID | Source Title | Published Date | Evidence Date | Evidence Role | Temporal Relation | Confidence | Independence Group |
|---|---|---|---|---|---|---|---|---|
| E-2024-08 | S-2024-06 | 大众交通终结9连板神话，大众公用A股"天地板" | 2024-08-01 | 2024-10-11 | context | subsequent | medium | orig_robotaxi_thirdwave |

- 10/10-11 特斯拉 Robotaxi 发布会仅一日脉冲后回落，不构成独立 Campaign。

---

## 4. 关键日期"为什么"

### 4.1 Start：2024-07-08（与 07-09 / 07-10 的关系）

#### 2024-07-08（起势日）

**Supporting Evidence**
- 行情观测：大众交通 07-08 放量 +6.12% 启动；EW 基准日起点。
- E-2024-05 内容提及"7 月上中旬萝卜快跑武汉跑出圈订单暴涨"。

**Contradicting Evidence**
- 07-08 当日**无可靠"当时公开主题识别"**：仅大众单只低置信异动（market_breadth），不足以认定广泛主题启动；直接绑定证据行无（N/A）。
- PIT 切片：**07-08 时点 point_in_time_basket = unavailable**。

**Interpretation**
- 研究解释：07-08 = **起势日 / 指数起点**，事实成立，但"不足以独立证明广泛启动"。

**Point-in-Time**
- 当时能知道：大众交通放量异动（低置信主题归因）；**不能**确认无人驾驶主题 basket。

**Retrospective**
- "07-08 = Campaign Start"依赖后续 07-09/07-10 的主题确认，属 retrospective 增强。

#### 2024-07-09 vs 07-10（Broad Confirmation 归谁）

- **07-09** = 首个 Index 大日（EW +10.1%）：但当时 PIT 能可靠识别的仅大众（market_breadth）+ 锦江/星网盘后媒体初归因；"广泛"若用完整 5 只 Historical Leader Set 证明则属 **look-ahead** → **Retrospective Confirmation**。
- **07-10** = 天迈获当日证券时报点名（E-2024-05，high）、板块 +4%、萝卜快跑媒体全面发酵 → **Broad Theme Confirmation（PIT 可辩护）**。
- 建议措辞（研究已封存）：**Start 起势 07-08 → 首个 Index 大日(R) 07-09 → Broad Theme Confirmation(PIT) 07-10**。

### 4.2 Peak：2024-07-29 vs 2024-08-05

#### 2024-07-29（DB Candidate）

**Supporting Evidence**
- E-2024-06（orig_robotaxi_leader，high，contemporaneous）：07-29 焦点复盘"大众交通 16 日涨 233%、锦江 15 天 9 板、金龙 12 天 7 板"——**叙事/龙头梯队确认的高峰报道日**。

**Contradicting Evidence**
- 行情观测：EW 07-29 = 210.8，**低于** 07-30（230.3）与 08-05（234.8）→ 07-29 **不是价格峰值**。
- 龙头个股峰值亦不在 07-29（大众 08-05、锦江 07-30、金龙 08-15、星网 08-02、天迈 07-18）。

**Interpretation**
- 研究解释：07-29 = 媒体叙事高峰/复盘日，不是等权指数价格峰值。

**Point-in-Time**
- 当时能知道：07-29 复盘报道为当日公开（PIT）。

**Retrospective**
- 将 07-29 标为 "peak" 只有在事后对照 EW 序列才发现偏早。

#### 2024-08-05（EW 峰值）

**Supporting Evidence**
- 行情观测：EW raw 234.8 = 窗口峰值（大众 08-05 11.22 拉高指数）；raw/adjusted 双口径峰值日一致。
- 等权方法学校正（`2024_robotaxi_market_validation.md`）：修正前"平均股价"口径曾误导峰值在 07-30；修正后真正等权峰值 = 08-05。

**Contradicting Evidence**
- 无绑定证据行（N/A）：08-05 无任何当日新闻/政策证据支撑其为"事件峰值"。
- 个股层面仅大众 08-05 见顶；锦江（07-30）、星网（08-02）已先于 08-05 见顶 → 08-05 峰值由大众单只拉高，**同步性弱**。

**Interpretation**
- 研究解释：08-05 = Historical Leader EW Index 的真正峰值（retrospective 判定）；记录为 Research Candidate，`campaign_date_observations` notes 明确"observed，未人工确认"。

**Point-in-Time**
- 当时能知道：08-05 当日行情公开；但"这是峰值"当时不可知。

**Retrospective**
- 峰值判定本身是 retrospective。

### 4.3 First Decline：2024-08-06（独立概念，非 End）

**Supporting Evidence**
- 行情观测：EW 234.8 → 214.1，单日 -8.8%，为峰值后首次显著连续下跌。

**Contradicting Evidence**
- 无绑定证据行（N/A）。
- 07-31 也曾回撤（230.3→218.2），但随后 08-05 创新高覆盖 → 07-31 是**中途回撤**，不是 First Decline。

**Interpretation**
- 研究解释：**First Decline = 08-06**，保留为独立概念；**它不是最终 End**（此后还有 08-15、08-21/22 的部分个股二次活跃）。

**Point-in-Time / Retrospective**
- 当日行情公开；"First Decline"判定为 retrospective。

### 4.4 Main Campaign End：2024-07-31 vs 2024-08-23

#### 2024-07-31（DB Candidate）

**Supporting Evidence**
- E-2024-07（orig_robotaxi_retreat，high，contradicting）：07-31 大众交通 9 连板终结（-2.65%）、大众公用天地板港股暴跌 22.75%；7/24 高位亏钱效应放大（锦江/金溢跌停）。
- **当时公开**：07-31 事件 + 08-01 报道，PIT 可辩护。

**Contradicting Evidence**
- 行情观测：EW 07-31（218.2）后 **08-01~08-05 再度上攻并创真正峰值 234.8** → 若 End=07-31，则把 08-05 峰值及 08-06 First Decline 排除在 Campaign 外，与研究封存的 Main Campaign 结构（07-08→08-23）矛盾。

**Interpretation**
- 研究解释：07-31 = **第一次回撤（中途回撤）**，不是 Main Campaign End。

**Point-in-Time**
- 当时能知道：龙头断板退潮信号（PIT 可辩护）。

**Retrospective**
- 作为"End"则 retrospective（且被 08-05 新高证伪）。

#### 2024-08-23（Main Campaign End Candidate）

**Supporting Evidence**
- 行情观测：08-21/08-22 重新活跃（EW 207.6/207.3）被 08-23 单日 -4.6% 跳水（197.8）打断；08-26→08-30 持续走弱（191.8→188.6）、**无任何集体回升/新高**、个股不再同步（锦江回落、金龙下行、大众横盘）。
- 判定逻辑（非"单日跌 X%"）：①核心样本走弱 ②无新高 ③无新集体催化 ④个股不再同步 → 主题失去持续主导地位。

**Contradicting Evidence**
- 无绑定证据行（N/A）：08-23 无当日新闻/政策证据。
- 09-05/09-06 出现同主题次级再启动（secondary_campaign_same_theme_cycle，weak）→ 08-23 **不是 Final Theme Cycle End**，主题 Cycle 延续至 9 月次级段。

**Interpretation**
- 研究解释：08-23 = **Main Campaign End / Major Breakpoint**；08-06 仅是 First Decline；09-05/06 为同主题次级段（另作 RC-2024-SECONDARY，不进入正式 Campaign）。

**Point-in-Time**
- 当时能知道：08-23 跳水当日公开；但"Main End"需观察其后持续走弱才可确认。

**Retrospective**
- 属 retrospective 判定。

---

## 5. Historical Leader vs Point-in-Time

| | Historical Leader Set | Point-in-Time Basket |
|---|---|---|
| 定义 | 行情结束后回看确认的核心样本（5 只：大众/锦江/金龙/星网/天迈） | 截至某日已有公开证据识别的主题样本 |
| 07-08 切片 | — | **unavailable**（仅大众低置信异动，不足以建立主题篮子） |
| 07-10 切片 | — | {大众、锦江、星网、天迈}（4 只） |
| 07-15 切片 | — | {大众、锦江、星网、天迈、金龙}（5 只，金龙 07-12 识别纳入） |

- 禁止倒推：不用完整 5 只 Historical Leader Set 去证明 07-09 的"广泛启动"（look-ahead）。

---

## 6. Industry vs Theme vs Benchmark

| 层 | 代理 | 07-08→07-31 累计（adjusted） |
|---|---|---|
| Industry layer | AUTO_ETF_516110（2024 汽车行业代理；AUTO_SW 801880 unavailable） | +3.6% |
| Theme layer | Robotaxi Historical Leader EW（5 只历史核心等权，事后工具） | **+122.4%** |
| Benchmark layer | HS300 | +1.2% |

- 判定：EW 相对汽车 ETF +118.8pp、相对 HS300 +121.2pp；汽车行业整体仅温和上冲（07-16 见顶后回落，08-05 破前低）→ 这是**"汽车行业里的 Robotaxi 题材行情"（theme_campaign）**，非全面汽车行情。
- 注意：**+122.4% 的语义 = 历史核心样本五股等权累计收益**，不是 Robotaxi 板块平均收益，更不是普通投资者当时可获得的收益。

---

## 7. Evidence 门槛（Promotion Gate）

| 最终候选日期 | 直接绑定 Evidence 数 | independence_group 数 | 是否满足 >=2 independent groups |
|---|---|---|---|
| Start 07-08 | 0 | 0 | **不满足**（仅行情观测 + E-2024-05 跨日内容提及） |
| Broad Confirmation 07-10 | 1（E-2024-05） | 1（orig_robotaxi_momentum） | **不满足**（单组） |
| Peak 07-29 | 1（E-2024-06） | 1（orig_robotaxi_leader） | **不满足**（单组） |
| Peak 08-05 | 0 | 0 | **不满足**（仅行情观测） |
| First Decline 08-06 | 0 | 0 | **不满足**（仅行情观测） |
| End 07-31 | 1（E-2024-07，contradicting） | 1（orig_robotaxi_retreat） | **不满足**（单组） |
| End 08-23 | 0 | 0 | **不满足**（仅行情观测） |
| **Campaign 整体** | **4** | **4** | **满足** |

> 提示：单日证据门槛（>=2 independent groups）在各候选日期上**均不满足**；Campaign 级门槛满足。2024 的 Peak/End 研究候选（08-05 / 08-06 / 08-23）**全部只有行情观测、无任何绑定证据行**，人工裁决时需知悉这一证据结构。

---

## 8. Review Decision 表

| Field | Current Candidate | Research Candidate(s) | Human Decision |
|---|---|---|---|
| Start | 2024-07-08 | 2024-07-08（起势）/ 07-09（首个 Index 大日，R）/ 07-10（Broad Confirmation，PIT） | |
| Peak | 2024-07-29 | 2024-07-29（叙事高峰）/ 2024-08-05（EW 峰值 234.8） | |
| End | 2024-07-31 | 2024-07-31（第一次回撤）/ 2024-08-23（Main End / Major Breakpoint）；First Decline=2024-08-06（独立概念） | |
| Strength | strong | strong（研究未提出降档） | |
| Result | positive | positive | |
| Classification | theme_campaign | theme_campaign | |
| Date Confidence | medium | 日期观测 confidence=low（market-data observation，未人工确认） | |

---

*本文件只整理现有证据供人工最终核验；未新增研究、未修改 DB/schema/Cycle。*
