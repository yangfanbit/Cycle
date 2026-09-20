# R01-04 Canonical Decision & Import v0.1 — 消费

> **性质**：R01-04 的 Canonical Decision + DB Import 落地记录。
> **前置**：`docs/R01_04_INTAKE_REVIEW_v0_1.md`（Intake PASS）。
> **边界**：**未修改** schema / Research Model v1.0 / Export Contract v1.0 / CMTR v1 / taxonomy /
> Structural Analogy v0.2 / Time Observation。**未启动 R01-05 / R01-06。**
> **未回头修改 R01-01 / R01-02 / R01-03。**

---

## 1. 13 个 Candidate 最终状态

| # | intake | 年份 | 最终处置 | canonical_id / 说明 |
|---|---|---:|---|---|
| 1 | `001` 白酒/消费升级 2016–2018 | 2016 | **PROMOTE** | `C-2016-CONS-BAIJIU-UPGRADE` |
| 2 | `002` 白酒核心资产 2019–2021 | 2019 | **PROMOTE** | `C-2019-CONS-BAIJIU-CORE` |
| 3 | `003` 海南离岛免税 | 2020 | **PROMOTE** | `C-2020-CONS-DUTYFREE` |
| 4 | `004` 疫后服务消费修复 | 2022 | **PROMOTE** | `C-2022-CONS-SERVICE-REBOUND` |
| 5 | `005` 非洲猪瘟超级猪周期 | 2018 | **PROMOTE** | `C-2018-CONS-HOG-AFRICAN` |
| 6 | `006` 猪周期反转 | 2021 | **PROMOTE** | `C-2021-CONS-HOG-REVERSAL` |
| 7 | **`007` 小家电/清洁电器** | 2020 | **RESEARCH_ONLY**（补证后再评估） | `RC-2020-CONS-SMALL-APPLIANCE` |
| 8 | `008` 白电 | 2020 | **PROMOTE** | `C-2020-CONS-WHITE-GOODS` |
| 9 | `009` 医美/颜值经济 | 2019 | **PROMOTE** | `C-2019-CONS-AESTHETICS` |
| 10 | `010` 国货美妆 | 2020 | **PROMOTE** | `C-2020-CONS-BEAUTY-CN` |
| 11 | `011` 消费品以旧换新 | 2024 | **PROMOTE** | `C-2024-CONS-TRADE-IN` |
| 12 | `012` 量贩零食/折扣零售 | 2023 | **PROMOTE**（`dc = low`） | `C-2023-CONS-VALUE-RETAIL` |
| 13 | **`013` 宠物食品** | 2024 | **RESEARCH_ONLY**（INSUFFICIENT） | `RC-2024-CONS-PET-FOOD` |

**11 PROMOTE · 2 RESEARCH_ONLY** · 无 `MERGE` · 无 `EXCLUDE` · **无拆分**（候选级）。

---

## 2. 12 条 Conflict 的逐项裁决

| conflict | 原状态 | **本轮裁决** |
|---|---|---|
| **`CF002`** 白酒两段 | UNRESOLVED | **裁决：两个独立 Campaign + 同一 Theme Cycle（Sequential）**。Gate 4/5 支持拆分（Q1 注意力中心不同：漂亮50/龙头集中 vs 核心资产/外资定价；Q4 **独立生命周期** —— 中间存在 **2018 年 -27% 级别回撤** 与 **2018-10-29 茅台上市以来首个一字跌停**；Q5 双向成立）；**唯一反对项 Q2（代表标的完全重叠）** 由「同一 Cycle 内的 Sequential Campaign」解释。**未按年份机械切割，也未默认合并。** |
| **`CF006`** 猪周期 | UNRESOLVED | **裁决（两层）**：① **允许进入 Campaign Universe** —— 判据**不基于「猪周期」这一名称**，而基于现有 Gate 五要素与 Q1–Q5（可观测先行指标 + 官方逆周期调控框架 + A 股提前定价）；且 R01-01 的 `C-2018-HIEQ-ROBOT-DOWN` 与 R01-03 的 `C-2022-SEMI-DOWNTURN` 已确立「非主题叙事型结构亦可进入 canonical」先例。② **两轮拆为两个独立 Campaign**（Q1 注意力中心不同：疫病外生冲击 vs 去化+调控；**独立产能拐点** 2021-07 结束 21 个月增长；独立政策框架事件），同属 Theme Cycle `hog_cycle_2018_2022`（Sequential）。★ **机制性质已在 `classification` 与 notes 中显式区分为「供给端自然周期」。** |
| **`CF005`** 白电驱动归因 | UNRESOLVED | **保留 UNRESOLVED —— 不强行选一个**。P2（出口替代）数据更支持（2020 出口 +24.2% vs 内销 -9.2%）；**P3 给出地产传导的反证**（2020 竣工 -4.9% 而板块上行；2021 竣工 +11.2% 而板块已下行）。★ **命名确定性已下调**：**不使用「地产后周期」**，改用中性 ID `C-2020-CONS-WHITE-GOODS`，两侧证据与 P3 反证完整保留在 notes。 |
| **`CF008`** 小家电 vs 白电 | UNRESOLVED | **裁决：008 独立进入 canonical；007 保持待补证**。Q2 代表标的**完全不重叠**（科沃斯/石头科技/小熊 vs 美的/格力/海尔/老板）、Q4 见顶错位 5 个月至 1 年 → **支持独立结构**。★ **共享 evidence `E047`/`E048`/`E049` 因 007 未进入 canonical，按 1:1 规则全部归属 008** —— **未为了处理共享证据而强行合并两个候选** ✓ |
| `CF001` 白酒 classification | UNRESOLVED | **保留**。两段均按 `industry_trend` 提案；P2（2021 社零 +12.5%、基本面未恶化而价格大幅回落）已在 notes 记录，最终 classification 待后续复核 |
| `CF003` 白酒行业增速口径 | KEEP_BOTH | **保留**。统计局 6033.48 亿元/+3.38% vs 茅台年报引述 +18.6% —— **两者均未用于支撑行业景气强度结论** |
| `CF004` 宏观 ≠ 行业启动 | KEEP_BOTH | **保留**（本任务最核心方法论冲突）。Worker 已用「**宏观数据（社零/CPI/旅游人次）一律 `context` 角色**」处理 → 本裁决**确认该处理方式**并写入 004 的 notes |
| `CF007` 医美归属 | UNRESOLVED | **保留**。CMTR v1 解析 → `消费` 根；「消费 vs 医药健康」边界**未裁决**；**未自行新增 Macro Theme、未扩展 taxonomy** |
| `CF009` 医美 vs 国货美妆 | UNRESOLVED | **裁决：两个独立 Campaign + 同一 Theme Cycle（Parallel）**。Q1 产业环节不同、**Q2 代表标的不重叠**、Q4 生命周期独立（peak 2021-07-05 vs 2021-10-29）。★ **P3 医美监管双重性质**（清退非法供给 = accelerator；压制扩张预期 = turning）**已分别归入 drivers，未单向归类** ✓ |
| `CF010` 以旧换新 补贴 vs 真实需求 | UNRESOLVED | **保留 UNRESOLVED**。Worker 按「一个 Campaign、双驱动叠加」提交（两者时间完全重叠、代表标的相同，拆分违反 Q5）→ **本裁决确认不拆分**。★ **`+11%` vs `-4.3%` 口径冲突完整保留** —— **不选任何一个作为唯一事实** |
| `CF011` 免税 vs 疫后修复 | UNRESOLVED | **裁决：两个独立 Campaign + 同一 Theme Cycle（Sequential）**。Q1 启动锚点/政策主体/验证数据**三者均不同**；Q4 独立生命周期；Q5 双向成立。Q2 部分重叠（中国中免）由 Sequential 解释 |
| `CF012` 2025 政策 vs 板块下跌 | KEEP_BOTH | **保留**。作为「**政策发布 ≠ 主题形成**」的对照样本写入 011 的 notes（与 `exclusion X001` 一致） |

> **12 条全部处理：6 条给出明确裁决（CF002 / CF006 / CF008 / CF009 / CF011 / CF004 确认处理方式），6 条明确保留（CF001 / CF003 / CF005 / CF007 / CF010 / CF012）。**
> **未为「解决 Conflict」而强行得出确定结论。**

---

## 3. 重点研究结构的独立性裁决

| 机制 | 是否形成独立 Campaign | 依据 |
|---|---|---|
| **消费升级**（001） | ✅ 独立 | Q1 注意力中心（漂亮50/龙头集中）+ Q4 独立生命周期（2018 -27% 回撤分隔） |
| **白酒核心资产**（002） | ✅ 独立 | Q1（MSCI 扩容 + 外资增量）；与 001 同 Cycle Sequential |
| **免税 / 出境替代**（003） | ✅ 独立 | Q1 启动锚点（财政部 33 号公告）+ 验证数据（海口海关销售额）均不同于 004 |
| **疫后补偿需求**（004） | ✅ 独立（`strength = medium`） | Q1 事件驱动；**主升仅 1–2 个月 → 持续性最弱环节，已降 strength** |
| **生猪自然周期**（005 / 006） | ✅ 各自独立 | 独立产能拐点 + 独立政策框架事件；机制性质已显式区分为「供给端自然周期」 |
| **家电出口 / 地产传导**（008） | ✅ 独立（`strength = medium`） | 驱动归因 UNRESOLVED，**命名中性化**；**PIT = 0** |
| **医美渗透率**（009） | ✅ 独立 | Q2 标的不重叠；跨族边界保留 |
| **国货美妆渗透率**（010） | ✅ 独立 | Q2 标的不重叠；与 009 同 Cycle Parallel |
| **财政补贴 → 官方销量**（011） | ✅ 独立 | **五级链条完整**（政策 → 资金 → 细则 → 官方销量/零售 → A 股响应）；`strength = medium`（Beta 未排除） |
| **渠道效率 / 性价比消费**（012） | ✅ 独立（`dc = low`） | 机制与消费升级**方向相反**；start 年度级、end 未确立 |

> ★ **未因「都属于消费」而合并任何两个候选** ✓

---

## 4. 新增 11 个 Canonical Campaign

| canonical_id | year | start | peak | end | class | strength | result | dc | themes |
|---|---:|---|---|---|---|---|---|---|---|
| `C-2016-CONS-BAIJIU-UPGRADE` | 2016 | 2016-06-01 | 2018-01-31 | 2018-12-31 | industry_trend | medium | positive | medium | 消费 + 食品饮料 |
| `C-2019-CONS-BAIJIU-CORE` | 2019 | 2019-03-01 | 2021-02-18 | 2021-12-31 | industry_trend | strong | positive | medium | 消费 + 食品饮料 |
| `C-2020-CONS-DUTYFREE` | 2020 | 2020-06-01 | 2021-02-18 | 2022-12-31 | mixed | strong | positive | medium | 消费 + 社会服务 |
| `C-2022-CONS-SERVICE-REBOUND` | 2022 | 2022-12-07 | 2023-01-31 | 2023-06-30 | event_driven | medium | positive | medium | 消费 + 社会服务 |
| `C-2018-CONS-HOG-AFRICAN` | 2018 | 2018-08-03 | 2020-03-09 | 2021-12-31 | industry_trend | strong | positive | medium | 消费 + 农林牧渔 |
| `C-2021-CONS-HOG-REVERSAL` | 2021 | 2021-08-17 | 2022-10-15 | 2022-12-31 | industry_trend | medium | positive | medium | 消费 + 农林牧渔 |
| `C-2020-CONS-WHITE-GOODS` | 2020 | 2020-06-01 | 2021-02-18 | 2021-12-31 | industry_trend | medium | positive | medium | 消费 + 家用电器 |
| `C-2019-CONS-AESTHETICS` | 2019 | 2019-11-06 | 2021-07-05 | 2022-12-31 | theme_campaign | medium | positive | medium | **消费（root，无子主题）** |
| `C-2020-CONS-BEAUTY-CN` | 2020 | 2020-06-29 | 2021-10-29 | 2022-12-31 | industry_trend | medium | positive | medium | **消费（root，无子主题）** |
| `C-2024-CONS-TRADE-IN` | 2024 | 2024-03-13 | 2024-10-08 | 2025-12-31 | mixed | medium | positive | medium | 消费 + 家用电器 |
| `C-2023-CONS-VALUE-RETAIL` | 2023 | 2023-01-01 | 2025-08-29 | **NULL** | industry_trend | medium | positive | **low** | **消费（root，无子主题）** |

**机制覆盖（对应 Historical Universe 缺失轴）**：消费升级/核心资产 · 政策放开+需求替代 · 事件驱动补偿需求 ·
**供给端自然周期** · 出口替代+成本推动 · 渗透率+产品创新+合规化 · 国货替代+渠道红利 · **财政补贴→官方销量** · **渠道效率/性价比消费**

**被合并 / 被拆分**：**均无**（候选级）。`CF002`/`CF006`/`CF011` 的「合并读法」由 **Theme Cycle（Sequential）** 承载，而非 Campaign 合并。

---

## 5. 2 个 RESEARCH_ONLY 的保存方式

> **均不进入 `campaigns` 表**（Research Model v1.0 §4）。仅在导出层 `research_candidates` 承载；
> 其**专属 evidence（4 条：`E050` / `E080` / `E081` / `E082`）不入 DB** —— 与 R01-01/02/03 同口径。

| canonical_id | 理由 | 补证要求 |
|---|---|---|
| **`RC-2020-CONS-SMALL-APPLIANCE`**（007） | **证据薄**（4 ev / 3 IG）+ **PIT = 0**（4 条全为 subsequent/retrospective）+ 渗透率核心机制**缺一手量化数据** | 补「清洁电器/小家电渗透率一手数据」+「2020–2021 同期证据」后重新评估 |
| **`RC-2024-CONS-PET-FOOD`**（013） | `INSUFFICIENT` / `low` · 3 ev / 3 IG · **PIT = 0** · **无任何一手官方证据**（均为媒体转述）· 板块广度不足（2 标的）· 持续仅 2–3 季度 | 补「海关总署出口原文」+「行业规模官方口径」后重新评估 |

> ★ **007 仍需补证** —— 本轮的 `CF008` 裁决支持其**独立结构**（标的与生命周期均错位），
> 但**证据强度不足**，**未因机制独特性或数量目标而提升** ✓

---

## 6. Theme Cycle（新增 7 个）

| theme_cycle_id | 成员 | Pattern |
|---|---|---|
| `baijiu_premium_2016_2021` | `C-2016-CONS-BAIJIU-UPGRADE` · `C-2019-CONS-BAIJIU-CORE` | **Sequential** |
| `service_consumption_2020_2023` | `C-2020-CONS-DUTYFREE` · `C-2022-CONS-SERVICE-REBOUND` | **Sequential** |
| `hog_cycle_2018_2022` | `C-2018-CONS-HOG-AFRICAN` · `C-2021-CONS-HOG-REVERSAL` | **Sequential** |
| `beauty_aesthetics_2019_2022` | `C-2019-CONS-AESTHETICS` · `C-2020-CONS-BEAUTY-CN` | **Parallel** |
| `appliance_export_2020_2021` | `C-2020-CONS-WHITE-GOODS` | 单一 |
| `trade_in_2024_2025` | `C-2024-CONS-TRADE-IN` | 单一 |
| `value_retail_2023_2025` | `C-2023-CONS-VALUE-RETAIL` | 单一 |

> **未新增 DB 实体** —— `theme_cycle_id` 沿用既有「研究级标签」做法（写入 `season_id` 与 `research_notes`）。

---

## 7. 医美 Macro Theme 归属（`CF007`）

- **CMTR v1 结果**：`R01-CONSUMER-MT006`（美容护理 / 消费医疗）以 `kind = CROSS_FAMILY` 提交 →
  **`UNRESOLVED_NAME`** —— **这是协议期望的正确结果**（跨族问题不由 CMTR 裁决）
- **候选级**：`009` / `010` 均经名称 `消费` **成功解析 → root `TH-CONSUMER`** ✓
- **本轮处置**：**保留边界 Conflict / note**（「医美属消费 vs 医药健康」未裁决）；
  **未自行新增 Macro Theme**；**未扩展 taxonomy** ✓
- **附带记录**：`美容护理` / `商贸零售` **未被 T01 的 `消费` 根覆盖**（T01 只设 食品饮料 / 家用电器 / 农林牧渔 / 社会服务）
  → `009` / `010` / `012` 以 **root `TH-CONSUMER` 为 main 主题**（无子主题），与 R01-02 的 `C-2019-CONSUMER-TWS` 同口径。
  该 taxonomy 缺口（`MT006` / `MT007` 提案级）**已记录，本轮不扩展**。

---

## 8. 以旧换新（`011`）的独立生命周期裁决

**五级链条**（**政策定调未被当作完整 Campaign 启动**）：

```
① 政策定调 2024-03-13（国发〔2024〕7 号公开）
② 资金落地 2024-07-25（发改环资〔2024〕1104 号，约 1500 亿元超长期特别国债）
③ 补贴细则 2024-08-24（商务部等 4 部门，8 类家电补 15%/20%）
④ 官方销量/零售验证 2024-09~12（零售额同比 +20.5%/+39.2%/+22.2%/+39.3%，连续 4 个月双位数）
   + 全年 10307 亿元、+12.3% 创历史新高 + 商务部口径超 6000 万台、超 2600 亿元
⑤ A 股响应 2024-10-08（美的/格力/海尔/海信家电/华帝/老板电器同时出现区间最高价）
→ 降温 2025 年（奥维云网推总口径 8931 亿元、-4.3%，Q3 起明显回落）
```

**裁决**：**构成独立 Campaign**（`start = 2024-03-13`，`peak = 2024-10-08`，`end = 2025-12-31`）。
★ **`+11%` vs `-4.3%` 口径冲突完整保留** —— **未选任何一个作为唯一事实** ✓
★ **Beta 风险**：峰值日与全市场「9·24 行情」重合 → **无法排除 Beta Contamination** → `strength = medium`；
**未声称完成 Beta 中性验证** ✓

---

## 9. 市场侧证据与 Beta（跨任务口径说明）

- **本轮未把「市场关注必须有 A 股市场侧证据」固化为新 Protocol** ✓（符合指示）
- **实际做法**：把市场侧证据作为 **Canonical Decision 的重要判断因素** ——
  - 有 A 股侧证据 → 正常进入（001/002/003/004/005/006/008/009/010/011/012 **均有**）
  - **PIT = 0 且证据薄** → Research Only（007）；**PIT = 0 但证据达标** → 降 `strength` 并记录（008）
  - 政策/消费数据与市场表现**明显脱节** → 降 `strength` / 保留 Conflict（004 / 008 / 011）
- **未回头修改 R01-01 / R01-02 / R01-03** ✓
- ★ **跨任务治理问题仍开放**：R01-03 起采用的更严口径（「市场关注」需 A 股市场侧证据）与
  R01-01 / R01-02 的口径差异**仍未统一** → 待 R01 完成后统一（**本轮不处理**）

---

## 10. 003 / 004 的独立性命中检查

| 检查 | 003 离岛免税 | 004 疫后修复 |
|---|---|---|
| 启动锚点 | ✅ 财政部公告 33 号（2020-06-29）**一手政策** | ✅「新十条」（2022-12-07） |
| 验证数据 | ✅ 海口海关离岛免税销售额（两个独立官方口径） | ✅ 官方旅游人次（春节 + 五一） |
| 独立生命周期 | ✅ 2020-06 → 2022-12 | ✅ 2022-12 → 2023-06 |
| 代表标的 | ⚠️ **仅 1 个**（中国中免）—— **A 股广度严重不足** | ✅ 4 个（中免/锦江/首旅/宋城） |
| 是否属「疫后消费修复的一部分」 | ❌ **否** —— 政策主体（财政部 vs 联防联控）、验证数据（免税销售额 vs 旅游人次）均不同；且 003 的启动（2020-06）**早于**疫后修复（2022-12）**2.5 年** | — |
| 是否满足独立生命周期 | ✅ 满足 | ✅ 满足，**但主升仅 1–2 个月** → `strength = medium`，**已记录为最弱环节** |

→ **裁决：两者均为独立 Campaign，同属 Theme Cycle `service_consumption_2020_2023`（Sequential）** ✓

---

## 11. DB / Export 变化

| 表 | 前 | 后 | Δ |
|---|---:|---:|---:|
| `research_rules` | 7 | **8** | +1（`rule_consumer`） |
| `annual_reviews` | 43 | **51** | +8（`AR-CONS-{2016,2018,2019,2020,2021,2022,2023,2024}`） |
| `campaigns` | 32 | **43** | **+11** |
| `sources` | 203 | **285** | +82 |
| `evidences` | 196 | **287** | +91 |
| `events` | 93 | **111** | +18 |
| `securities` | 112 | **143** | +31 |
| `campaign_themes` | 70 | **89** | +19 |
| `campaign_evidences` | 187 | **269** | +82 |
| `campaign_events` | 86 | **104** | +18 |
| `campaign_securities` | 126 | **161** | +35 |
| `campaign_phases` | 78 | **99** | +21 |
| `campaign_date_observations` | 77 | **109** | +32 |
| `themes` | 52 | 52 | **0（未改 taxonomy）** |

**既有数据零改动**：既有 32 campaigns / 52 themes / 43 annual_reviews / 7 rules / 196 evidences /
203 sources / 112 securities / 93 events 及全部桥表 → **逐行比对「被改动：无」** ✓

★ **共享 evidence 唯一归属**（`validate_batch_research` 强制 1 evidence : 1 campaign）：
`E047` / `E048` / `E049`（家电行业整体口径，原为 007 与 008 共享）→ **因 007 未进入 canonical，全部归属 008** ✓

**Export**：campaigns 32 → **43** · research_candidates 15 → **17** · rules 7 → **8** ·
events 100 → **118** · securities 167 → **207** · **`timeline_export_version = "1.0"` 未变** ✓

---

## 12. 全部验证结果 → **全部 PASS**

| 检查 | 结果 |
|---|---|
| `validate_db` | **PASS**（**3 条 WARNING —— 与 R01-04 导入前完全相同，无新增**） |
| `validate_timeline_export` · `validate_batch_research` · `validate_promotion_manifest` · `check_doc_schema_consistency` · `validate_current_research` | **PASS** |
| `validate_monorepo_integrity` · `refresh --check` | **PASS** |
| `intake --check` | **PASS（0 FAIL / 0 WARN）** |
| Intake Validator C01–C25（R01-01/02/03/04） | **PASS × 4** |
| `test_validate_historical_research_intake.py` | **PASS（44 / 44）** |

★ `research/schema` · `contracts` · `src` · Structural Analogy v0.2 · Time Observation → **零改动** ✓

**Historical Universe 当前实测**：root **11** · **有 Campaign 的 root 8**（新增 `消费`）·
Historical Campaign **43** · Research Candidate **17** · 跨族 Campaign 对 `C(8,2)` = **28**。

---

## 13. 尚未解决的问题

| # | 项 | 说明 |
|---|---|---|
| 1 | **`CF007` 医美归属未裁决** | 「消费 vs 医药健康」边界保留；`美容护理` 未被 T01 覆盖（`MT006` 提案级 gap） |
| 2 | **`CF005` 白电驱动归因保留 UNRESOLVED** | 命名已中性化（不使用「地产后周期」），两侧证据与 P3 反证完整保留 |
| 3 | **`CF010` 保留 UNRESOLVED** | 补贴 vs 真实需求不拆分；**`+11%` vs `-4.3%` 口径冲突完整保留** |
| 4 | **`CF001` 白酒 classification 保留** | 两段均按 `industry_trend`；资金面权重高的反证已记录 |
| 5 | **`007` 仍需补证** | 渗透率一手数据 + 2020–2021 同期证据；`CF008` 已支持其独立结构，但证据强度不足 |
| 6 | **`013` 保持 Research Only** | 无任何一手官方证据 |
| 7 | **`C-2020-CONS-DUTYFREE` 的 A 股广度不足** | `security_ids` 仅 1 个（中国中免） |
| 8 | **`C-2023-CONS-VALUE-RETAIL` 的 start 为年度级、end 未确立** | `date_confidence = low`、`end_date = NULL` |
| 9 | **`C-2024-CONS-TRADE-IN` 的 Beta 风险未排除** | 峰值日与「9·24 行情」重合 |
| 10 | **跨任务「市场关注」口径差异未统一** | R01-03 起更严 vs R01-01/02；**本轮未固化新 Protocol、未回改历史** |
| 11 | **`美容护理` / `商贸零售` taxonomy 缺口** | `MT006` / `MT007` 提案级未解析；**本轮不扩展** |
| 12 | **`C-2016-CONS-BAIJIU-UPGRADE` 的 Priority B 证据薄** | 月度批价/动销一手数据缺失 |
| 13 | **Structural Analogy / Time Observation 未刷新** | 待 R01 全部完成后以新 artifact 版本统一刷新 |
| 14 | **Validator C08 vs Research Model v1.0 §15 的 `research_report` tier 冲突** | 与 R01-04 无关；仍待独立工程处理 |

---

## 14. 本轮严格未做

- ❌ 未启动 R01-05 / R01-06（其 Worker 可继续独立并行 Research，不受本轮影响）
- ❌ 未修改 Research Model v1.0 / Schema / Protocol / Export Contract / CMTR v1 / taxonomy
- ❌ 未刷新 Structural Analogy / Time Observation
- ❌ 未回头修改 R01-01 / R01-02 / R01-03 的任何数据（既有 32 campaigns 逐行零改动）
- ❌ 未把「市场关注需 A 股市场侧证据」固化为新 Protocol
- ❌ 未为「解决 Conflict」而强行得出确定结论
- ❌ 未为了增加 Campaign 数量而提升 007 / 013
