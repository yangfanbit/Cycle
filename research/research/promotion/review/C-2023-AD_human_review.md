# Human Final Review Dossier — C-2023-AD

> **性质**：本文件为 Human Final Review Pack（人工最终核验材料包）。
> **范围**：只整理现有 Research Evidence / Market Data / 研究报告；不新增研究、不改 DB、不改日期。
> **状态**：所有日期均为 **候选（Candidate）**；**Verified Date 尚不存在**。人工 Decision 栏统一留空。

---

## 1. Current DB Candidate

| 字段 | 值 |
|---|---|
| campaign_id | C-2023-AD |
| start_date | 2023-06-12 |
| peak_date | 2023-07-11 |
| end_date | 2023-07-19 |
| strength | medium |
| result | positive |
| classification | theme_campaign |
| source_id | S-2023-01 |
| date_confidence | medium |

**明确**：以上为 **DB Candidate**（campaigns 表当前记录的研究候选值），**不是 Verified Fact**。start/peak/end 在 `campaign_date_observations` 中 verified 均为 NULL、confidence=low、method=unknown（快照自 campaigns，未经行情核验）。

---

## 2. Research Review Candidates

研究阶段发现的候选日期（**不自动选择**）：

### Start
| 候选 | 语义 | 来源 |
|---|---|---|
| **2023-06-12** | DB Candidate：汽车产业链爆发预热（赛力斯等 10 余股涨停；AUTO 转上；德赛西威 06-09→06-12 三日内 +10%） | DB Candidate；`2023_smart_driving_research.md` §4 |
| **2023-06-21** | "智能驾驶"被市场明确识别的起点（工信部 L3 吹风表态；SDIdx 首次明显加速 111.3） | `2023_smart_driving_research.md` §4/§6；E-2023-01 |
| **2023-07-03 / 07-05** | 智能驾驶主升确认（07-03 比亚迪"天神之眼"发布；07-05 SDIdx 129.3 进入主升） | `2023_smart_driving_research.md` §4/§6 |

### Peak
| 候选 | 语义 | 来源 |
|---|---|---|
| **2023-07-11** | DB Candidate（智驾"主线地位确认"复盘日；SDIdx 149.0） | DB Candidate；E-2023-03 |
| **2023-07-12** | SDIdx 窗口内峰值 157.8（浙江世宝 17.87 峰值） | `2023_smart_driving_research.md` §1/§5 |
| **peak_cluster 07-12 ~ 07-19** | 智驾主升峰值簇（SDIdx 157.8 / 156.8） | `2023_smart_driving_research.md` §5 |

### End
| 候选 | 语义 | 来源 |
|---|---|---|
| **2023-07-19** | DB Candidate（主线确认后板块让位地产/顺周期、快速轮动退潮） | DB Candidate；E-2023-07 |
| **2023-08-04** | 8 月次级活跃高点（SDIdx 159.1，集中于浙江世宝/众泰题材妖股；德赛已回落） | `2023_smart_driving_research.md` §5 |
| **2023-08 月下旬** | SDIdx 回落至 132 偏弱（08-25），08-31 反弹 141.7；**End 不清晰**（研究原话） | `2023_smart_driving_research.md` §5/§10 |

---

## 3. 证据按日期组织

绑定 Evidence 共 7 条，independence_group 共 7 个（orig_l3_policy_expectation / orig_sales_trend / orig_sector_momentum / orig_ad_momentum / orig_ad_stock_price / orig_structure_pulse / orig_policy_schedule）。

### 2023-06-12（Start 候选：DB Candidate）

| 字段 | 值 |
|---|---|
| Evidence ID | N/A（无 evidence_date=2023-06-12 的绑定证据行） |
| Source ID | N/A |
| Source Title | N/A |
| Published Date | N/A |
| Evidence Date | N/A |
| Evidence Role | N/A |
| Temporal Relation | N/A |
| Confidence | N/A |
| Independence Group | N/A |

关联（非直接绑定该日）：
- E-2023-04（group=orig_ad_stock_price，published 2023-07-13）内容提及"启动早于 6/1（6/12 预热、赛力斯 6/8 见底）"——属**事后追述**。
- 行情观测：06-12 AUTO 转上；德赛西威 06-09（114.2）→ 06-12（125.6）三日 +10%；赛力斯等 10 余股涨停（DB start_date_basis）。

**06-12 是否已有 Theme Evidence（用户重点检查项）**：
- 06-12 当日**无"智能驾驶"主题证据**：无政策、无主题定名报道；可观察的是**汽车产业链个股异动**（德赛+10%、赛力斯涨停），属 Industry Recovery / 产业链预热性质。
- 第一个"智能驾驶"主题级证据是 **06-21 工信部 L3 吹风**（E-2023-01）。
- 研究结论（§4）：先"汽车/产业链异动"（06-12），后"智能驾驶主题被定名+主升"（06-21 起识别、07-03 确认），两组时点相差约 2 周。

### 2023-06-21（Start 候选：Theme 识别起点）

| Evidence ID | Source ID | Source Title | Published Date | Evidence Date | Evidence Role | Temporal Relation | Confidence | Independence Group |
|---|---|---|---|---|---|---|---|---|
| E-2023-01 | S-2023-01 | 国新办吹风会：支持L3级及以上自动驾驶商业化应用、启动智能网联汽车准入和上路通行试点 | 2023-06-21 | 2023-06-21 | supporting | contemporaneous | high | orig_l3_policy_expectation |

- 事件表：EV-2023-01（2023-06-21，policy，role=trigger）。

### 2023-07-03（主升确认辅助）

| Evidence ID | Source ID | Source Title | Published Date | Evidence Date | Evidence Role | Temporal Relation | Confidence | Independence Group |
|---|---|---|---|---|---|---|---|---|
| E-2023-05 | S-2023-06 | 产销数据亮眼 汽车股狂欢 | 2023-07-03 | 2023-07-03 | supporting | contemporaneous | medium | orig_sales_trend |

- 事件表：EV-2023-02（2023-07-03，company，role=catalyst）"比亚迪首发'天神之眼'高阶智驾（腾势 N7）"。

### 2023-07-04（板块级主升信号）

| Evidence ID | Source ID | Source Title | Published Date | Evidence Date | Evidence Role | Temporal Relation | Confidence | Independence Group |
|---|---|---|---|---|---|---|---|---|
| E-2023-02 | S-2023-02 | 25只汽车股携手涨停！汽车产业链成新主线 | 2023-07-04 | 2023-07-04 | supporting | contemporaneous | high | orig_sector_momentum |

### 2023-07-11（Peak 候选：DB Candidate）

| Evidence ID | Source ID | Source Title | Published Date | Evidence Date | Evidence Role | Temporal Relation | Confidence | Independence Group |
|---|---|---|---|---|---|---|---|---|
| E-2023-03 | S-2023-03 | 焦点复盘：智能驾驶再度引爆汽车产业链，主线地位就此确认？ | 2023-07-11 | 2023-07-11 | supporting | contemporaneous | high | orig_ad_momentum |

- 行情观测：SDIdx 07-11 = 149.0（浙江世宝 8 天 6 板、瑞玛精密 6 天 5 板、万安 2 连板）。

### 2023-07-12（Peak 候选：SDIdx 峰值）

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

- 仅行情观测：SDIdx 07-12 = 157.8（窗口内峰值）；浙江世宝 17.87 峰值。

### 2023-07-13（龙头区间涨幅证据，辅助）

| Evidence ID | Source ID | Source Title | Published Date | Evidence Date | Evidence Role | Temporal Relation | Confidence | Independence Group |
|---|---|---|---|---|---|---|---|---|
| E-2023-04 | S-2023-05 | 浙江世宝股价翻倍、万安科技等多股涨停，谁是真正智能驾驶概念股？ | 2023-07-13 | 2023-07-13 | supporting | contemporaneous | high | orig_ad_stock_price |

### 2023-07-19（End 候选：DB Candidate）

| Evidence ID | Source ID | Source Title | Published Date | Evidence Date | Evidence Role | Temporal Relation | Confidence | Independence Group |
|---|---|---|---|---|---|---|---|---|
| E-2023-07 | S-2023-03 | 焦点复盘：智能驾驶再度引爆汽车产业链，主线地位就此确认？ | 2023-07-11 | 2023-07-19 | contradicting | contemporaneous | medium | orig_structure_pulse |

- 注：E-2023-07 与 E-2023-03 **同源**（S-2023-03），但角色为 contradicting（内容：7 月中下汽车让位地产/顺周期、存量资金快速轮动）。

### 2023-08-04 / 2023-08 月下旬（End 备选观察）

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

- 仅行情观测：08-04 SDIdx 159.1（浙江 18.07、众泰 4.52 驱动，德赛已回落至 160.1 vs 峰值 172.5）；08-25 SDIdx 132.4 偏弱；08-31 反弹 141.7。

### 反证（降档依据，非日期候选）

| Evidence ID | Source ID | Source Title | Published Date | Evidence Date | Evidence Role | Temporal Relation | Confidence | Independence Group |
|---|---|---|---|---|---|---|---|---|
| E-2023-06 | S-2023-07 | 《关于开展智能网联汽车准入和上路通行试点工作的通知》 | 2023-11-17 | 2023-11-17 | contradicting | subsequent | high | orig_policy_schedule |

- 正式 L3 准入文件成文 2023-11-17、非夏季；2023 年 FSD 未在华落地 → 夏季系"政策预期"而非"落地"驱动 → strength 降档 medium。

---

## 4. 关键日期"为什么"

### 4.1 Start：2023-06-12 vs 2023-06-21（Theme Evidence 检查）

#### 2023-06-12（DB Candidate）

**Supporting Evidence**
- 行情观测：06-12 AUTO 转上；德赛西威三日 +10%（114.2→125.6）；赛力斯等 10 余股涨停；赛力斯 6/8 见底。
- E-2023-04 事后追述"6/12 预热"。

**Contradicting Evidence**
- 06-12 当日**无 Theme Evidence**（无政策、无"智能驾驶"主题定名）；仅是汽车产业链个股异动/预热。
- 直接绑定证据行：无（N/A）。

**Interpretation**
- 研究解释：06-12 = 产业链/智驾**预热**（Phase1），主题尚未被市场定名；与 07 月主升为**同一 Campaign 的多 Phase**（无冷却、同一催化主线、龙头持续抬升）。

**Point-in-Time**
- 当时能知道：汽车产业链异动；**不能**知道这是"智能驾驶 Campaign"的起点（主题 06-21 才有政策信号）。

**Retrospective**
- "06-12 = Campaign Start"含 retrospective 成分（用后来的主题归属回贴 06-12 的异动）。

#### 2023-06-21（Theme 识别起点）

**Supporting Evidence**
- E-2023-01（Tier1 监管源，high，contemporaneous）：工信部吹风会明确支持 L3 及以上商业化、启动准入试点。
- 行情观测：SDIdx 06-21 首次明显加速（111.3）。

**Contradicting Evidence**
- 06-21 后 SDIdx 并未立即主升（06-30 111.1 横盘），主升确认在 07-03~07-05 → 06-21 是**信号日**而非启动日。

**Interpretation**
- 研究解释：06-21 = "智能驾驶"被市场明确识别的起点（政策预期信号），是 7 月行情的起点。

**Point-in-Time**
- 当时能知道：吹风会为当日公开（PIT 可辩护）。

**Retrospective**
- 非 retrospective。

### 4.2 Peak：2023-07-11 vs 2023-07-12（peak_cluster 07-12~07-19）

#### 2023-07-11（DB Candidate）

**Supporting Evidence**
- E-2023-03（orig_ad_momentum，high，contemporaneous）：07-11 智驾涨势加速带动产业链爆发，"主线地位确认"。
- 行情观测：SDIdx 07-11 = 149.0。

**Contradicting Evidence**
- SDIdx 窗口内峰值在 **07-12（157.8）**，非 07-11；个股峰值亦分散（德赛 07-04、浙江 07-12、万安 07-13）。

**Interpretation**
- 研究解释：07-11 = "主线确认"的**叙事峰值日**；价格峰值簇为 07-12~07-19。

**Point-in-Time / Retrospective**
- 07-11 复盘报道为当日公开（PIT）；"峰值"属性为 retrospective。

#### 2023-07-12（SDIdx 峰值）

**Supporting Evidence**
- 行情观测：SDIdx 157.8 = 窗口内最高；浙江世宝 17.87 峰值。

**Contradicting Evidence**
- 无绑定证据行（N/A）；单日峰值与 07-19（156.8）差距小，peak_cluster 更诚实。

**Interpretation**
- peak_cluster = 07-12~07-19，不强行取单日。

**Point-in-Time / Retrospective**
- 当日行情公开；峰值属性 retrospective。

### 4.3 End：2023-07-19（及 8 月备选观察）

#### 2023-07-19（DB Candidate）

**Supporting Evidence**
- E-2023-07（orig_structure_pulse，contradicting，medium）：7 月中下汽车让位地产/顺周期、市场快速轮动（财联社 7/12"主题频繁高切低"）。
- 行情观测：SDIdx 07-19（156.8）后 07-21 回落至 144.9。

**Contradicting Evidence**
- **08-04 SDIdx 159.1 再创窗口内新高**（浙江 18.07、众泰 4.52）→ 若 End=07-19，则 8 月次级活跃被排除在 Campaign 外。
- 研究原话："**没有简单'7/19=end'**：8 月再度活跃（08-04）……End 不清晰"。

**Interpretation**
- 研究解释：07-19 = 智驾**主升段**（第二波/加速段）结束；8 月为反复活跃/次级（多 Wave），集中于题材妖股（浙江/众泰），德赛已回落 → 属**同一 Campaign 的尾段**而非新 Campaign。

**Point-in-Time**
- 当时能知道：7 月中下板块轮动退潮（E-2023-07 为当时公开信息）。

**Retrospective**
- "07-19 后只剩次级/尾段"的判定需 8 月数据，属 retrospective。

#### 后续是否存在有效 Smart Driving Campaign（用户重点检查项）

- **07-19 之后至 09-30 窗口内**：无新的独立 Smart Driving Campaign。8 月活跃（08-04 等）被研究判定为**同一 Campaign 的次级/多 Wave**（题材妖股驱动，龙头德赛已回落；无新催化、无冷却期）。
- **RC-2023-HUAWEI**（Huawei Auto，08-29 Early Signal / 09-04 Theme Formation / 09-12 Start Candidate）为**独立 Research Candidate**，promotion_status=RESEARCH_CANDIDATE，**未达到正式 Campaign 门槛，不得混入本 Campaign**。
- 因此：若人工接受"8 月=同一 Campaign 尾段"，则 End=07-19（主升结束）或 8 月下旬（尾段结束）二选一；若人工认为 8 月次级活跃应计入，则 End 应后移。**本材料包不替人工决定**。

---

## 5. Historical Leader vs Point-in-Time

| | Historical Leader Set | Point-in-Time Basket |
|---|---|---|
| 定义 | 事后确认的核心/高表现样本 | 截至某日已有公开证据可识别的主题样本 |
| 本 Campaign | 浙江世宝（总龙/翻倍）、德赛西威（+80%）、万安科技（+70%）、众泰、赛力斯（SDIdx = 德赛/浙江/万安/众泰 4 股等权，事后工具） | 07-05 起可建立相对可辩护的 PIT 篮子：{德赛、浙江、万安}（众泰偏题材后补）；07-12 才是清晰主升确认 |

- 禁止倒推：不因浙江世宝/众泰事后涨最多，把 06-12 的它们当作"当时可识别龙头"——06-12 只有德赛异动可视。

---

## 6. Industry vs Theme vs Benchmark

| 层 | 代理 | 本 Campaign 表现 |
|---|---|---|
| Industry layer | AUTO_ETF_516110（2023 汽车行业代理；AUTO_SW 801880 unavailable） | 06-12→07-11 +10.5%；07-03→07-19（题材主升段）仅 **+1.3%** |
| Theme layer | SDIdx（4 只智驾龙头等权，事后工具） | 06-12→07-11 **+49.0%**；07-03→07-19 **+33.5%** |
| Benchmark layer | HS300 | 06-12→07-11 +0.7%；07-03→07-19 -1.1% |

- 判定：7 月 SDIdx +33.5% 而 AUTO 仅 +1.3% → **题材主升几乎不依赖行业 β**（行业几乎不动，题材暴涨）→ 是**主题行情**（theme_campaign），非行业行情。

---

## 7. Evidence 门槛（Promotion Gate）

| 最终候选日期 | 直接绑定 Evidence 数 | independence_group 数 | 是否满足 >=2 independent groups |
|---|---|---|---|
| Start 06-12 | 0 | 0 | **不满足**（仅行情观测 + 事后追述） |
| Start 06-21 | 1（E-2023-01） | 1（orig_l3_policy_expectation） | **不满足**（单组） |
| Peak 07-11 | 1（E-2023-03） | 1（orig_ad_momentum） | **不满足**（单组） |
| Peak 07-12 | 0 | 0 | **不满足**（仅行情观测） |
| End 07-19 | 1（E-2023-07，contradicting） | 1（orig_structure_pulse） | **不满足**（单组） |
| End 08-04 / 08 月下旬 | 0 | 0 | **不满足**（仅行情观测） |
| **Campaign 整体** | **7** | **7** | **满足** |

> 提示：单日证据门槛（>=2 independent groups）在各候选日期上**均不满足**；Campaign 级门槛满足。日期判定主要依赖行情观测 + 单组证据。

---

## 8. Huawei Auto 隔离声明

- **RC-2023-HUAWEI** 在 promotion_manifest 中 promotion_status = **RESEARCH_CANDIDATE**（证据不足、未达正式 Campaign 门槛）。
- 本 Dossier 中 Huawei Auto **只作为 RC-2023-HUAWEI 被提及**，其日期（08-29 / 09-04 / 09-12）**不混入** C-2023-AD 的任何 Start/Peak/End 候选。

---

## 9. Review Decision 表

| Field | Current Candidate | Research Candidate(s) | Human Decision |
|---|---|---|---|
| Start | 2023-06-12 | 2023-06-12（产业链预热）/ 2023-06-21（Theme 识别）/ 2023-07-03（主升确认） | |
| Peak | 2023-07-11 | 2023-07-11 / 2023-07-12（SDIdx 峰值）/ peak_cluster 07-12~07-19 | |
| End | 2023-07-19 | 2023-07-19 / 2023-08-04（次级高点）/ 2023-08 月下旬（偏弱） | |
| Strength | medium | medium（E-2023-06 反证降档：政策预期非落地） | |
| Result | positive | positive | |
| Classification | theme_campaign | theme_campaign | |
| Date Confidence | medium | 日期观测 confidence=low（快照自 campaigns，未经行情核验） | |

---

*本文件只整理现有证据供人工最终核验；未新增研究、未修改 DB/schema/Cycle。*
