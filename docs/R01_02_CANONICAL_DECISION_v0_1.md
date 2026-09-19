# R01-02 Canonical Decision & Import v0.1 — 半导体 / 电子

> **性质**：R01-02 的 Canonical Decision + DB Import 落地记录。
> **前置**：`docs/R01_02_INTAKE_REVIEW_v0_1.md`（Intake PASS）。
> **边界**：**未修改** schema / Research Model v1.0 / Export Contract v1.0 / CMTR v1 / taxonomy /
> Structural Analogy v0.2 / Time Observation。**未启动 R01-03。**

---

## 1. 12 个 Candidate 最终逐项状态

| # | intake | 年份 | 最终处置 | canonical_id / 说明 |
|---|---|---:|---|---|
| 1 | `001` 半导体自主可控（实体清单） | 2019 | **PROMOTE** | `C-2019-SEMI-LOCALIZATION` |
| 2 | `002` 设备/材料国产替代（扩产） | 2020 | **PROMOTE** | `C-2020-SEMI-EQUIPMENT` |
| 3 | `003` 面板 LCD 价格上行（2020–22） | 2020 | **PROMOTE** | `C-2020-PANEL-CYCLE` |
| 4 | `004` 全球缺芯 / 全链涨价 | 2020 | **RESEARCH_ONLY** | `RC-2022-SEMI-CHIPSHORTAGE` |
| 5 | `005` TWS / 可穿戴消费电子 | 2019 | **PROMOTE** | `C-2019-CONSUMER-TWS` |
| 6 | `006` AI 算力半导体 | 2023 | **PROMOTE** | `C-2023-AI-COMPUTE-SEMI` |
| 7 | `007` 存储超级周期 | 2024 | **PROMOTE**（附 CF006 限定） | `C-2024-SEMI-MEMORY` |
| 8 | `008` 大基金三期 + 自主可控 | 2024 | **RESEARCH_ONLY** | `RC-2024-SEMI-FUND3` |
| 9 | `009` 半导体下行 / 去库存 | 2022 | **PROMOTE** | `C-2022-SEMI-DOWNTURN` |
| 10 | `010` 2015 杠杆牛 | 2015 | **RESEARCH_ONLY**（INSUFFICIENT） | `RC-2015-SEMI-LEVERAGE` |
| 11 | `011` 面板价格上行（2016–17） | 2016 | **PROMOTE**（date_confidence low） | `C-2016-PANEL-CYCLE` |
| 12 | `012` 2017 显卡 / 矿机 | 2017 | **RESEARCH_ONLY**（INSUFFICIENT） | `RC-2017-GPU-MINING` |

**8 PROMOTE · 4 RESEARCH_ONLY** · 无 `MERGE` · 无 `EXCLUDE`。

---

## 2. 10 个 Conflict 的最终处理

| conflict | 状态 | 本轮处理 |
|---|---|---|
| **`CF001`** 2019–2021 一周期 vs 多段 | **裁决为两个独立 Campaign**（Sequential，同一 Theme Cycle） | 见 §3 |
| **`CF010`** 峰值三口径（2020-02 / 2020-07-14 / 2021-07-30） | **保留全部三口径**，不预设任何一个是 canonical | 001 peak = **2020-07-14**；002 peak = **2021-07-30**；2020-02 底（研报口径）**仅记录为 alternative，未采用** |
| **`CF003`** 半导体 vs 电子是否合并 | **由 CMTR v1 回答** | 两者均解析至根 **`电子`**；`半导体` 为其子主题。**未修改 taxonomy** |
| **`CF004`** 面板/显示是否拆分 | **按独立机制族处理** | 面板 = `TH-ELEC-PANEL`（子主题）；机制（产能+库存价格周期）与半导体设计/设备不同步 |
| **`CF006`** 2024-09-24 后 Beta | **保留 UNRESOLVED** | 007 以 medium 置信度进入 canonical 并**保留 Beta 限定**；008 → RESEARCH_ONLY |
| `CF002` 国产替代阶段边界 | **倾向两个不同结构**（附结论） | 2019–20 与 2024–25 中间有 2022-01—2024-01 近两年独立下行；但 008 因 Beta + 与 007 重叠 → RESEARCH_ONLY |
| `CF005` 面板涨价 vs 缺芯 | **判为两个独立结构**（Q5 成立） | 003 与 004 供给曲线不同；但 004 因 start 为 PHASE_WINDOW 且自述难以独立切分 → RESEARCH_ONLY |
| `CF007` 面板 2016–17 vs 2020–22 | **判为两个独立 Campaign**（同一机制族两轮） | 003 与 011 均 PROMOTE，同属 `panel_price_cycle_2016_2022` |
| `CF008` 2017 显卡/矿机归属 | **保留未裁决** | 012 → RESEARCH_ONLY |
| `CF009` 纯下行是否进 canonical | **裁决进入** | 009 → PROMOTE，`result = weak`（与 R01-01 `C-2018-HIEQ-ROBOT-DOWN` 同口径） |

> **未为「消除 Conflict」而强行做单一结论**：`CF006`、`CF008` 明确保留；`CF010` 三口径全部保留。

---

## 3. P0 裁决依据 —— 关键实测数据

**申万半导体板块指数（01801081）实测点位**：

```
2019-01-04  1316.17（年内低点）
2019-12-25  3173.11
2020-07-14  5869.83   ← 001 的 canonical peak
2021-07-30  7642.58   ← 002 的 canonical peak（2019–2021 全周期最高）
2022-10-12  3605.80   ← 009 下行低点
2025-10-31  7964.33   ← 007 期间，超过 2021-07 创指数新高
```

**CF001 裁决为两个 Campaign 的 Gate 依据**：

| Gate | 001 | 002 | 判定 |
|---|---|---|---|
| **Q1 独立注意力中心** | 华为实体清单 → 国产替代认知（设计/制造/封测） | 中芯国际回A + 晶圆厂扩产 → 设备材料 | ✅ 不同 |
| **Q2 独立代表标的** | 设计+封测+设备（8 只） | 设备+材料集中（4 只） | ✅ 不同 |
| **Q3 独立持续性** | 主升 14 个月 | 主升 4 个月 + 下行 14 个月 | ✅ 均成立 |
| **Q4 独立生命周期** | 主升→回撤（2020-07→09） | 主升→下行（2021-08→2022-10） | ✅ 独立 |
| **Q5 残差检验** | 剔除 002 后 001 自洽 | 剔除 001 后 002 自洽 | ✅ 通过 |

> ★ **不采用**「2020-07-14 是全周期峰值」的读法 —— 2021-07-30（7642.58）高于它 30%，
> 故 2020-07-14 只能是 001 的**局部高点**；反之亦不能因 2021-07 更高而把 001 并入 002。
> 两者**允许时间重叠**（`theme_campaign_separation_v1.md` 规则 5）。

---

## 4. 新增 8 个 Canonical Campaign

| canonical_id | year | start | peak | end | class | strength | result | dc | themes |
|---|---:|---|---|---|---|---|---|---|---|
| `C-2019-SEMI-LOCALIZATION` | 2019 | 2019-05-16 | **2020-07-14** | 2020-09-30 | theme_campaign | strong | positive | medium | 电子(related) + 半导体(main) |
| `C-2020-SEMI-EQUIPMENT` | 2020 | 2020-07-16 | **2021-07-30** | 2021-09-30 | theme_campaign | strong | positive | medium | 电子(related) + 半导体(secondary) + 半导体设备(main) |
| `C-2020-PANEL-CYCLE` | 2020 | 2020-06-01 | 2021-07-31 | 2021-08-31 | industry_trend | strong | positive | medium | 电子(related) + 面板/显示(main) |
| `C-2019-CONSUMER-TWS` | 2019 | 2019-01-04 | 2020-10-13 | 2021-03-31 | theme_campaign | strong | positive | medium | 电子(main) |
| `C-2023-AI-COMPUTE-SEMI` | 2023 | 2023-01-30 | 2023-04-10 | 2023-08-25 | theme_campaign | medium | positive | medium | 电子(related) + 半导体(main) |
| `C-2024-SEMI-MEMORY` | 2024 | 2024-09-24 | 2025-10-31 | **NULL** | theme_campaign | medium | positive | medium | 电子(related) + 半导体(main) |
| `C-2022-SEMI-DOWNTURN` | 2022 | 2022-01-04 | 2022-08-31 | 2022-10-12 | industry_trend | medium | **weak** | medium | 电子(related) + 半导体(main) |
| `C-2016-PANEL-CYCLE` | 2016 | 2016-02-01 | 2017-06-30 | 2017-06-30 | industry_trend | medium | positive | **low** | 电子(related) + 面板/显示(main) |

**机制覆盖（对应 Historical Universe 缺失轴）**：
- **供给收缩 / 价格周期**：`C-2020-PANEL-CYCLE` · `C-2016-PANEL-CYCLE` · `C-2024-SEMI-MEMORY`
- **纯需求端驱动**：`C-2019-CONSUMER-TWS`（终端产品创新 + 大客户订单）
- **库存周期 / 需求收缩型下行**：`C-2022-SEMI-DOWNTURN`（`result=weak`）
- **国产替代 / 资本开支**：`C-2019-SEMI-LOCALIZATION` · `C-2020-SEMI-EQUIPMENT`

**被合并 / 被拆分**：
- **无 MERGE**（无候选被合并进另一候选）
- **无拆分**（无候选被拆成多个 Campaign）—— CF001 的「多段」读法**未**被采纳为把 001 拆成 3 段
- 002 与 001 的关系判为**同一 Theme Cycle 下的 Sequential Campaign**，非合并、非拆分

---

## 5. 4 个 RESEARCH_ONLY 的保存方式

> **均不进入 `campaigns` 表**（Research Model v1.0 §4：Campaign Candidate「不能进入 `campaigns` 表」）。

| canonical_id | 原因 |
|---|---|
| `RC-2022-SEMI-CHIPSHORTAGE`（004 缺芯） | start/peak 均为 PHASE_WINDOW（无日期锚点）；包内自述 A 股映射与 001/002 高度重合、**难以独立切分** → Q4 不成立 |
| `RC-2024-SEMI-FUND3`（008 大基金三期） | confidence **low**；与 007 市场区间高度重叠；无独立结束点 |
| `RC-2015-SEMI-LEVERAGE`（010） | INSUFFICIENT：**0 securities**、2 ev/2 IG 恰在门槛、Beta 无法排除、Priority B 资料不足 |
| `RC-2017-GPU-MINING`（012） | INSUFFICIENT：**0 securities**、归属争议（`CF008`）保留、缺行业数据支撑 |

**与既有设计一致**：仅在导出层 `research_candidates` 承载（与既有 4 个 `RC-*` 同）。
其**专属** evidence（12 条）**不入 DB** —— 避免 `orphan-supporting-evidence` 告警
（与 R01-01 同一口径）。研究内容完整保留在 intake Package 中。

---

## 6. Theme Cycle（新增 6 个）

| theme_cycle_id | 成员 | Pattern |
|---|---|---|
| `semi_localization_2019_2021` | `C-2019-SEMI-LOCALIZATION` · `C-2020-SEMI-EQUIPMENT` | **Sequential** |
| `panel_price_cycle_2016_2022` | `C-2016-PANEL-CYCLE` · `C-2020-PANEL-CYCLE` | **同一机制族的两轮实例** |
| `electronics_tws_2019_2020` | `C-2019-CONSUMER-TWS` | 单一 |
| `ai_compute_semi_2023` | `C-2023-AI-COMPUTE-SEMI` | 单一 |
| `memory_supercycle_2024_2025` | `C-2024-SEMI-MEMORY` | 单一 |
| `semi_inventory_downturn_2022` | `C-2022-SEMI-DOWNTURN` | 单一 |

> **未新增 DB 实体** —— `theme_cycle_id` 沿用既有「研究级标签」做法，写入
> `campaigns.research_notes` 与 `season_id`，**不创建 `theme_cycles` 表**（Research Model §3）。

---

## 7. DB 变化

| 表 | R01-02 前 | 后 | 增量 |
|---|---:|---:|---:|
| `research_rules` | 5 | **6** | +1（`rule_semiconductor`） |
| `annual_reviews` | 33 | **39** | +6（`AR-SEMI-{2016,2019,2020,2022,2023,2024}`） |
| `campaigns` | 18 | **26** | **+8** |
| `sources` | 115 | **155** | +40 |
| `evidences` | 116 | **160** | +44 |
| `events` | 64 | **79** | +15 |
| `securities` | 64 | **83** | +19 |
| `campaign_themes` | 42 | **58** | +16 |
| `campaign_evidences` | 107 | **151** | +44 |
| `campaign_events` | 57 | **72** | +15 |
| `campaign_securities` | 72 | **100** | +28 |
| `campaign_phases` | 57 | **72** | +15 |
| `campaign_date_observations` | 38 | **61** | +23 |
| `themes` | 52 | 52 | **0（未改 taxonomy）** |

**既有数据零改动**：既有 18 campaigns / 52 themes / 33 annual_reviews / 5 rules /
116 evidences / 115 sources / 64 securities / 64 events —— **逐行比对「被改动：无」** ✓

**跨 Campaign 证据唯一归属**（`validate_batch_research` 强制 1 : 1）：
`E035` → 007（008 为 RESEARCH_ONLY）· `E056` → 002（008 为 RESEARCH_ONLY）。

---

## 8. Export 变化

**沿用现有流程**（`research/scripts/batch_auto_research.py`），**Contract v1.0 未改**。
最小必要扩展：`SEMI_RULE`/`RULES` · `THEME_CYCLE`(+8) · `CAMPAIGN_LIFECYCLE`(+8) ·
`CAMPAIGN_DRIVERS`(+8) · `RESEARCH_CANDIDATES`(+4) · `RULE_META`/`scope`。

| 项 | 前 | 后 |
|---|---:|---:|
| `campaigns` | 18 | **26** |
| `research_candidates` | 6 | **10** |
| `rules` | 5 | **6** |
| `events` | 71 | **86** |
| `securities` | 94 | **129** |

`timeline_export_version = "1.0"`（未变）· 无 score / rank / probability / prediction。

---

## 9. 所有 Validator 结果 → **全部 PASS**

| 检查 | 结果 |
|---|---|
| `validate_db` | **PASS**（3 条 WARNING，见 §10） |
| `validate_timeline_export` | **PASS**（0 警告） |
| `validate_batch_research` | **PASS**（0 警告） |
| `validate_promotion_manifest` | **PASS** |
| `check_doc_schema_consistency` | **PASS** |
| `validate_current_research` | **PASS** |
| `validate_monorepo_integrity` | **PASS** |
| `validate_historical_research_intake --check` | **PASS** |
| `test_validate_historical_research_intake.py` | **PASS（44 / 44）** |
| `refresh_current_research --check` | **PASS** |
| R01-01 / R01-02 Intake Validator | **PASS / PASS** |

---

## 10. 需要单独处理但未在本轮处理的问题

1. **`CF006`（2024-09-24 后市场 Beta）保留 UNRESOLVED** —— 007 已以 medium 置信度进入 canonical
   并**保留 Beta 限定**；**不得**据此宣称已与 Beta 分离。分离口径（等权 / 相对收益）属
   R01-05 与 ThreeC Agent 的统一口径问题（intake `Q005` / `CT006`）。
2. **`CF008`（2017 显卡/矿机归属）保留未裁决** —— 012 保持 RESEARCH_ONLY。
3. **3 条 `evidence-temporal-mislabel` 警告**（`validate_db`）：
   `E-SEMI-29`（2020-12-28 标 contemporaneous，但 001 end = 2020-09-30）·
   `E-SEMI-47`（2022-12-29）· `E-SEMI-48`（2022-10-31，均 bound to 009，end = 2022-10-12）。
   → 这是 **intake Package 自身的 `temporal_relation` 标注与其 lifecycle 端点不一致**。
   **本轮不改研究内容**（改 `temporal_relation` 属研究结论修改），**建议由 R01-02 后续复核轮次处理**。
4. **`E056`（2024-05-24 大基金三期）被包内绑定至 002（2020–2021）** —— 日期与 Campaign 区间不符。
   已按「不改研究内容」原样导入并在 `research_notes` 标注。
5. **别名 taxonomy 缺口**（非阻塞，本轮不扩展）：`芯片` / `集成电路` / `面板` / `存储` / `DRAM` /
   `HBM` / `GPU` / `消费电子` / `苹果产业链` / `TWS耳机` / `缺芯` / `自主可控` / `国产替代` / `算力` 等。
6. **`C-2016-PANEL-CYCLE` 证据偏薄**（3 ev / 2 IG，peak 仅半年窗口）—— 建议优先补齐面板价格月度序列。
7. **Structural Analogy 未刷新**（Rule Set v0.2 与 Research v0.2 均 FROZEN；
   AGENTS.md §4 禁止覆盖旧轮次产物）—— 建议 R01 全部完成后以**新 artifact 版本**统一刷新。
8. **Time Observation 未刷新**（本轮边界）。

---

## 11. 本轮严格未做

- ❌ 未修改 Research Model v1.0 / schema / Export Contract v1.0 / CMTR v1 / taxonomy
- ❌ 未修改任何无关历史 Campaign（既有 18 campaigns 逐行零改动）
- ❌ 未刷新 Structural Analogy v0.2 · 未刷新 Time Observation
- ❌ 未启动 R01-03
- ❌ 未创建 ranking / score / probability / prediction
- ❌ 未为导入数量降低标准（004 / 008 / 010 / 012 保持 RESEARCH_ONLY）
