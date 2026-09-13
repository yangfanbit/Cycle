# Human Final Review Dossier — C-2022-POLICY

> **性质**：本文件为 Human Final Review Pack（人工最终核验材料包）。
> **范围**：只整理现有 Research Evidence / Market Data / 研究报告；不新增研究、不改 DB、不改日期。
> **状态**：所有日期均为 **候选（Candidate）**；**Verified Date 尚不存在**。人工 Decision 栏统一留空。

---

## 1. Current DB Candidate

| 字段 | 值 |
|---|---|
| campaign_id | C-2022-POLICY |
| start_date | 2022-04-27 |
| peak_date | 2022-06-10 |
| end_date | 2022-08-31 |
| strength | strong |
| result | positive |
| classification | theme_campaign |
| source_id | S-2022-01 |
| date_confidence | medium |

**明确**：以上为 **DB Candidate**（campaigns 表当前记录的研究候选值），**不是 Verified Fact**。start/peak/end 在 `campaign_date_observations` 中 verified 均为 NULL、confidence=low、method=market_data。

---

## 2. Research Review Candidates

研究阶段发现的候选日期（**不自动选择**）：

### Start
| 候选 | 语义 | 来源 |
|---|---|---|
| **2022-04-27** | Industry Recovery / Setup 起点（AUTO 行业代理 04-26 低点 0.828 → 04-27 0.85 转上；全市场超跌反弹+复工复产预期） | DB Candidate；`2022_auto_boundary_review.md` §2 |
| **2022-05-23** | Theme Formation / Policy Catalyst（国常会宣布阶段性减征购置税 600 亿，首个 Point-in-Time 主题催化） | `2022_auto_boundary_review.md` §2 |

### Peak
| 候选 | 语义 | 来源 |
|---|---|---|
| **2022-06-10** | DB Candidate（比亚迪 A 股市值首破万亿） | DB Candidate；E-2022-03 |
| **2022-06-23** | 龙头峰值（比亚迪 353.5 / 长安 06-23~24 峰值；6/23 整车板块 +5.8% 多股涨停） | `2022_auto_boundary_review.md` §3；E-2022-04 |
| **2022-06-28** | 行业代理峰值（AUTO_ETF_516110 = 1.312，相对 04-26 低点 +56%） | `2022_auto_boundary_review.md` §3；`campaign_date_observations` notes |

### End
| 候选 | 语义 | 来源 |
|---|---|---|
| **2022-08-01** | 行业代理最后一个有效"二高点"（AUTO 1.298），但非新高、龙头（比亚迪 330.5，远低于 06-23 峰 353.5）不确认 → "未同步的二高点" | `2022_auto_boundary_review.md` §4 |
| **2022-08 月 decline cluster** | 08-01 之后持续衰减段（比亚迪 07-07 后持续走弱至 08-31 288；HS300 06-30 4485→08-31 4078） | `2022_auto_boundary_review.md` §4 |
| **2022-08-31** | DB Candidate（窗口暂记；研究明确"不因数据窗到 8/31 就机械定 End=8/31"） | DB Candidate；`2022_auto_boundary_review.md` §4 |

---

## 3. 证据按日期组织

绑定 Evidence 共 5 条，independence_group 共 4 个（orig_policy_tax_catalyst / orig_nev_stock_price / orig_sector_momentum / orig_counter_single_stock）。

### 2022-04-27（Start 候选 A：Industry Setup）

| 字段 | 值 |
|---|---|
| Evidence ID | N/A（无 evidence_date=2022-04-27 的绑定证据行） |
| Source ID | N/A |
| Source Title | N/A |
| Published Date | N/A |
| Evidence Date | N/A |
| Evidence Role | N/A |
| Temporal Relation | N/A |
| Confidence | N/A |
| Independence Group | N/A |

关联（非直接绑定该日）：
- E-2022-04（group=orig_sector_momentum，published 2022-06-26）内容提及"Wind 汽车指数自 4 月以来不到两个月累计涨超 60%（4 月底已启动）"——属**事后追述**，非 04-27 当日证据。
- 行情观测（market-data observation，非 evidence 行）：AUTO 04-26 低点 0.828 → 04-27 0.85 转上。

### 2022-05-23（Start 候选 B：Theme Formation）

| Evidence ID | Source ID | Source Title | Published Date | Evidence Date | Evidence Role | Temporal Relation | Confidence | Independence Group |
|---|---|---|---|---|---|---|---|---|
| E-2022-02 | S-2022-02 | 政策东风频吹 多家车企自掏腰包补贴消费者 | 2022-06-02 | 2022-06-02 | supporting | contemporaneous | high | orig_policy_tax_catalyst |

- 注：E-2022-02 的 evidence_date 为 2022-06-02（报道日），其**内容**描述 05-23 国常会 600 亿；DB 中 temporal_relation=contemporaneous（相对所描述事件簇）。
- 事件表：EV-2022-01（2022-05-23，policy，role=trigger）"国常会：阶段性减征乘用车购置税 600 亿元"。

### 2022-06-10（Peak 候选：DB Candidate）

| Evidence ID | Source ID | Source Title | Published Date | Evidence Date | Evidence Role | Temporal Relation | Confidence | Independence Group |
|---|---|---|---|---|---|---|---|---|
| E-2022-03 | S-2022-04 | 涨疯了！超越大众后，比亚迪市值突破万亿大关 | 2022-06-10 | 2022-06-10 | supporting | contemporaneous | high | orig_nev_stock_price |

### 2022-06-23（Peak 候选：龙头峰值）

| Evidence ID | Source ID | Source Title | Published Date | Evidence Date | Evidence Role | Temporal Relation | Confidence | Independence Group |
|---|---|---|---|---|---|---|---|---|
| E-2022-04 | S-2022-03 | 国常会促进汽车消费举措提振市场 数十家汽车企业股价触及涨停 | 2022-06-26 | 2022-06-26 | supporting | contemporaneous | medium | orig_sector_momentum |

- 注：E-2022-04 内容描述 06-22 国常会再促消费 → 06-23 整车板块 +5.8% 多股涨停；evidence_date 为报道日 06-26。
- 龙头行情观测：比亚迪 06-23 收盘 353.5（峰值）、长安 06-23~24 峰值 22.35（market-data observation）。

### 2022-06-28（Peak 候选：行业代理峰值）

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

- 仅行情观测：AUTO_ETF_516110 06-28 收盘 1.312（窗口内峰值）。

### 2022-08-01 / 2022-08 月 decline cluster / 2022-08-31（End 候选）

| 字段 | 值 |
|---|---|
| Evidence ID | N/A（三个 End 候选日均无绑定证据行） |
| Source ID | N/A |
| Source Title | N/A |
| Published Date | N/A |
| Evidence Date | N/A |
| Evidence Role | N/A |
| Temporal Relation | N/A |
| Confidence | N/A |
| Independence Group | N/A |

- 仅行情观测：AUTO 08-01 二高点 1.298（未同步）→ 08-31 走弱至约 1.10；比亚迪 07-07（349.38）后持续走弱至 08-31 288；HS300 06-30 4485 → 08-31 4078。

### 反例（Contradicting，个股事件，不计入主线）

| Evidence ID | Source ID | Source Title | Published Date | Evidence Date | Evidence Role | Temporal Relation | Confidence | Independence Group |
|---|---|---|---|---|---|---|---|---|
| E-2022-05 | S-2022-05 | 中通客车"12天12板" 监管发函质问是否存内幕交易？ | 2022-05-30 | 2022-05-30 | contradicting | contemporaneous | high | orig_counter_single_stock |

- 中通客车 5/13–5/30 十二连板（+214.52%）系"核酸检测车"个股事件，深交所发关注函；**不计入 Campaign 主线**（event_driven，独立核算）。

### 2022-06-01（政策落地买盘，辅助）

| Evidence ID | Source ID | Source Title | Published Date | Evidence Date | Evidence Role | Temporal Relation | Confidence | Independence Group |
|---|---|---|---|---|---|---|---|---|
| E-2022-01 | S-2022-01 | 车企加码送福利，助力政策"大礼包"，汽车股继续狂欢！ | 2022-06-02 | 2022-06-02 | supporting | contemporaneous | high | orig_policy_tax_catalyst |

- 内容：5/31 购置税减半细则 → 6/1 次日整车指数盘中涨逾 4%，安凯/东风/海马/小康涨停，板块居申万一级涨幅第一。

---

## 4. 关键日期"为什么"

### 4.1 Start：2022-04-27 vs 2022-05-23（本 Campaign 核心冲突）

#### 2022-04-27（Industry Recovery / Setup）

**Supporting Evidence**
- 行情观测：AUTO 行业代理 04-26 低点 0.828 → 04-27 0.85 转上；此后持续走强（05-13 0.998）。
- E-2022-04 事后追述"Wind 汽车指数自 4 月以来不到两个月累计涨超 60%（4 月底已启动）"。
- 当时宏观背景：全市场超跌反弹 + 复工复产/政策预期。

**Contradicting Evidence**
- 04-27 当日**无任何可确认的主题催化**（无政策、无主题定名）；05-13 前仍属 Industry Recovery。
- 直接绑定证据行：无（N/A）。

**Interpretation**
- 研究解释（`2022_auto_boundary_review.md` §2）：04-27 = **Setup / Industry Recovery 起点**，非 Theme Start；主题未确认。

**Point-in-Time**
- 当时能知道：全市场超跌反弹 + 复工复产预期；**不能**凭比亚迪"后来破万亿"倒推主题已启动。

**Retrospective**
- "04-27 启动"的表述依赖 06-26 报道（E-2022-04）与事后行情回看，属 retrospective 增强。

#### 2022-05-23（Theme Formation / Policy Catalyst）

**Supporting Evidence**
- EV-2022-01：05-23 国常会宣布阶段性减征购置税 600 亿（trigger）。
- E-2022-02（orig_policy_tax_catalyst，high）：政策组合拳（05-23 国常会 → 05-31 细则 → 超 20 家车企加码补贴）。
- 行情观测：05-23 AUTO 1.047 连日走强；05-25 政策后加速 1.073；06-01 细则落地买盘 1.099。

**Contradicting Evidence**
- 05-24 现货回踩（AUTO 1.037、比亚迪 281.0）：政策日波动，启动并非单边。
- 若 Campaign 定义含"行业修复段"，05-23 会**遗漏 04-27→05-22 的 Setup 段**（约 17 个交易日、AUTO +23%）。

**Interpretation**
- 研究解释：05-23 = **首个明确 Point-in-Time 政策催化**，Theme Confirmation Candidate；05-23 与 05-31 为同一事件簇的两个步骤（05-23 定方向、05-31 给细则）。

**Point-in-Time**
- 当时能知道：国常会 600 亿为**当时公开**信息 → 主题催化可确认（PIT 可辩护）。

**Retrospective**
- 不依赖事后信息；但"05-23 即 Campaign Start"的判定本身需人工对 Campaign 定义（含不含 Setup 段）作出裁决。

#### 人工需要回答
> "Campaign Start" 应为：
> - **A. 2022-04-27**（Industry Setup 起点，含行业修复段）
> - **B. 2022-05-23**（Theme Formation / 政策催化日）
> - **C. 其他日期**
>
> 本材料包**不替人工做决定**。

### 4.2 Peak：2022-06-10 vs 2022-06-23 vs 2022-06-28

#### 2022-06-10（DB Candidate）

**Supporting Evidence**
- E-2022-03（orig_nev_stock_price，high，contemporaneous）：06-10 比亚迪 A 股市值首破万亿（348.80 元 +8.19%），自主品牌首家；5 月新能源乘用车零售 36 万辆同比 +91.2%。

**Contradicting Evidence**
- 行情观测：比亚迪 06-10 后仍创新高（06-23 353.5）；AUTO 06-28 才见顶 1.312 → 06-10 **不是行情峰值**，是标志性事件日。

**Interpretation**
- 研究解释：06-10 = 主升段的**标志事件（比亚迪破万亿）**，不是价格峰值；真正峰值在 06-23~06-28 cluster。

**Point-in-Time**
- 当时能知道：06-10 比亚迪破万亿为当日公开事实。

**Retrospective**
- 将 06-10 标为 "peak" 只有在事后对照 06-23/06-28 才发现偏早。

#### 2022-06-23（龙头峰值）

**Supporting Evidence**
- 行情观测：比亚迪 06-23 峰值 353.5（相对 04-27 +51%）、长安 06-23~24 峰值 22.35（约 +137%）。
- E-2022-04（orig_sector_momentum，medium）：06-22 国常会再促消费 → 06-23 整车板块 +5.8% 多股涨停（二次催化）。

**Contradicting Evidence**
- 行业代理 AUTO 峰值在 06-28（1.312），晚于龙头 5 天 → 单日 06-23 不能代表板块峰值。

**Interpretation**
- 研究解释：peak_cluster = 06-23~06-28；**龙头峰 06-23/24，行业代理峰 06-28**，分列记录、不强行取单日。

**Point-in-Time**
- 当时能知道：06-23 板块大涨为当日公开；但"这就是峰值"当时不可知。

**Retrospective**
- 峰值判定本身是 retrospective。

#### 2022-06-28（行业代理峰值）

**Supporting Evidence**
- 行情观测：AUTO_ETF_516110 06-28 收盘 1.312 = 窗口内行业代理峰值（相对 04-26 低点 +56%）。

**Contradicting Evidence**
- 龙头（比亚迪/长安）峰值在 06-23/24，06-28 龙头已过峰 → 行业代理峰值与龙头峰值**不同步**。
- 无绑定证据行（N/A）。

**Interpretation**
- 研究解释：行业代理峰值滞后于龙头，peak_cluster 06-23~06-28 更诚实。

**Point-in-Time / Retrospective**
- 06-28 为当时公开行情；峰值属性为 retrospective。

### 4.3 End：2022-08-01 vs 2022-08 decline cluster vs 2022-08-31（不机械使用 08-31）

#### 2022-08-01（未同步的二高点）

**Supporting Evidence**
- 行情观测：AUTO 08-01 二高点 1.298，为 07 月回落后最后一次有效高点。

**Contradicting Evidence**
- 1.298 低于 06-28 主峰 1.312（非新高）；比亚迪 08-01 仅 330.5，远低于 06-23 峰 353.5 → **龙头不确认**，08-01 不是板块同步新高。

**Interpretation**
- 研究解释：08-01 = "未同步的二高点"，其后进入 decline cluster。

**Point-in-Time / Retrospective**
- 当日行情公开；"二高点"性质为 retrospective。

#### 2022-08 月 decline cluster（08-01 → 08-31）

**Supporting Evidence**
- 行情观测：比亚迪 07-07（349.38）后持续走弱至 08-31 288；AUTO 08-01 1.298 → 08-31 约 1.10；HS300 06-30 4485 → 08-31 4078（大盘同步走弱）。

**Contradicting Evidence**
- 无明确单日"结束事件"；decline 是渐变过程，难取单日。

**Interpretation**
- 研究解释：最后一次板块同步 = 06-23~06-28 主峰；7 月 retracement、8 月为 decline_cluster（持续衰减、龙头与代理不同步）。

**Point-in-Time / Retrospective**
- 衰减过程当时可观察；"cluster 边界"判定为 retrospective。

#### 2022-08-31（DB Candidate）

**Supporting Evidence**
- DB end_date_basis：7 月中后板块分化/回调；8 月后政策边际减弱；窗口暂记至 8/31。

**Contradicting Evidence**
- 研究明确："**不因数据窗到 8/31 就机械定 End=8/31**"；08-31 只是数据窗口边界，非行情事件。

**Interpretation**
- 08-31 = 窗口暂记值（decline cluster 的右端点），其"结束"语义弱于 08-01 后进入衰减的判断。

**Point-in-Time / Retrospective**
- 当日行情公开；作为 End 的判读为 retrospective。

---

## 5. Historical Leader vs Point-in-Time

| | Historical Leader Set | Point-in-Time Basket |
|---|---|---|
| 定义 | 事后确认的核心/高表现样本 | 截至某日已有公开证据可识别的主题样本 |
| 本 Campaign | 比亚迪、长安、长城、广汽（+安凯代表） | 04-27 时点：**unavailable**（无确认主题）；05-23 时点：可由政策催化建立（政策受益整车股），但研究未产出逐股 PIT 篮子表 → **unavailable（未建表）** |

- 禁止倒推：不因比亚迪事后破万亿，把 04-27 的比亚迪当作"当时可识别龙头"。

---

## 6. Industry vs Theme vs Benchmark

| 层 | 代理 | 本 Campaign 表现 |
|---|---|---|
| Industry layer | AUTO_ETF_516110（2022 汽车行业代理；AUTO_SW 801880 unavailable） | 04-27 0.85 → 06-28 1.312（+56% 相对 04-26 低点）→ 08-31 约 1.10 |
| Theme layer | 政策主题（购置税+新能源）龙头：比亚迪/长安 | 比亚迪 04-27 235.0 → 06-23 353.5（+51%）；长安约 +137% |
| Benchmark layer | HS300 | 04-27 3895 → 06-28 约 4400+（06-30 4485）→ 08-31 4078 |

- 判定：行业与主题同向、主题有明确政策催化与龙头 → **theme_campaign（政策驱动）**，非纯 industry_trend（行业 β 之外有清晰题材+龙头+一致上行段）。

---

## 7. Evidence 门槛（Promotion Gate）

| 最终候选日期 | 直接绑定 Evidence 数 | independence_group 数 | 是否满足 >=2 independent groups |
|---|---|---|---|
| Start 04-27 | 0 | 0 | **不满足**（仅行情观测 + 事后追述） |
| Start 05-23 | 1（E-2022-02）+ 事件 EV-2022-01 | 1（orig_policy_tax_catalyst） | **不满足**（单组；E-2022-01 亦属同组） |
| Peak 06-10 | 1（E-2022-03） | 1（orig_nev_stock_price） | **不满足**（单组） |
| Peak 06-23 | 1（E-2022-04） | 1（orig_sector_momentum） | **不满足**（单组） |
| Peak 06-28 | 0 | 0 | **不满足**（仅行情观测） |
| End 08-01 / 08 月 cluster / 08-31 | 0 | 0 | **不满足**（仅行情观测） |
| **Campaign 整体** | **5** | **4** | **满足** |

> 提示：单日证据门槛（>=2 independent groups）在各候选日期上**均不满足**；Campaign 级门槛满足。人工裁决日期时需知悉：日期判定主要依赖行情观测 + 少量单组证据。

---

## 8. Review Decision 表

| Field | Current Candidate | Research Candidate(s) | Human Decision |
|---|---|---|---|
| Start | 2022-04-27 | 2022-04-27（Setup）/ 2022-05-23（Theme Formation） | |
| Peak | 2022-06-10 | 2022-06-10 / 2022-06-23（龙头）/ 2022-06-28（行业代理） | |
| End | 2022-08-31 | 2022-08-01（二高点）/ 2022-08 decline cluster / 2022-08-31 | |
| Strength | strong | strong（研究未提出降档） | |
| Result | positive | positive | |
| Classification | theme_campaign | theme_campaign | |
| Date Confidence | medium | 日期观测 confidence=low（`campaign_date_observations`） | |

---

*本文件只整理现有证据供人工最终核验；未新增研究、未修改 DB/schema/Cycle。*
