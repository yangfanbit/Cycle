# R01-03 Canonical Decision & Import v0.1 — 资源 / 有色 / 化工

> **性质**：R01-03 的 Canonical Decision + DB Import 落地记录。
> **前置**：`docs/R01_03_INTAKE_REVIEW_v0_1.md` + `docs/R01_03_INTAKE_REVIEW_ADDENDUM_v0_1.md`。
> **边界**：**未修改** schema / Research Model v1.0 / Export Contract v1.0 / CMTR v1 / taxonomy /
> Structural Analogy v0.2 / Time Observation。**未启动 R01-04 / R01-05 / R01-06。**

---

## 1. 11 个 Candidate 最终状态

| # | intake | 年份 | 最终处置 | canonical_id / 说明 |
|---|---|---:|---|---|
| 1 | `001` 工业金属（铜/铝） | 2020 | **PROMOTE** | `C-2020-RES-NONFERROUS` |
| 2 | `002` 能源金属（锂） | 2020 | **PROMOTE** | `C-2020-RES-LITHIUM` |
| 3 | `003` 稀土 | 2020 | **PROMOTE**（strength 降为 medium） | `C-2020-RES-RAREEARTH` |
| 4 | `004` 基础化工（能耗双控） | 2021 | **PROMOTE** | `C-2021-RES-CHEM-DUALCTRL` |
| 5 | `005` 染料 / 中间体 | 2019 | **PROMOTE** | `C-2019-RES-DYE-SHOCK` |
| 6 | `006` 黄金（2019–2020 实际利率） | 2020 | **RESEARCH_ONLY** | `RC-2020-RES-GOLD-RATES` |
| 7 | `007` 黄金（2024–2025 央行购金） | 2024 | **PROMOTE** | `C-2024-RES-GOLD-CB` |
| 8 | `008` 农化（化肥） | 2022 | **RESEARCH_ONLY** | `RC-2022-RES-FERTILIZER` |
| 9 | `009` 铜（2024–2025 矿端缺口） | 2025 | **RESEARCH_ONLY** | `RC-2025-RES-COPPER` |
| 10 | `010` 电解铝（2017 行政去产能） | 2017 | **RESEARCH_ONLY** | `RC-2017-RES-ALUMINUM` |
| 11 | `011` 化工（2016 环保约束） | 2016 | **RESEARCH_ONLY** | `RC-2016-RES-CHEM-ENV` |

**6 PROMOTE · 5 RESEARCH_ONLY** · 无 `MERGE` · 无 `EXCLUDE` · **无拆分**。

### 1.1 本轮确立的裁决规则（明示）

> **「市场关注」必须由 A 股市场侧证据支撑，或由强行业/公司证据支撑；仅有商品价格者不足以确立。**

| candidate | A 股市场侧证据 | 判定 |
|---|---|---|
| `001` | ✅ E005/E006（2021 申万有色金属 +40.47%，全行业第二）· E007（中证有色指数 +31.31%，高点 8603.88 @2021-09-13） | PROMOTE |
| `002` | ✅ E015（能源金属指数 399366.SZ；天齐 +451.88% / 赣锋 +180.74%） | PROMOTE |
| `003` | ⚠️ **无板块指数**；仅公司业绩 E027（北方稀土归母净利 +462.32%） | PROMOTE 但 **strength 降为 medium** |
| `004` | ✅ E035（2021 申万基础化工 +37.19%，全行业第四） | PROMOTE |
| `005` | ✅ E044（2019-03-22 分散染料板块集体高开、浙江龙盛一字板） | PROMOTE |
| `006` | ❌ **零**（4 条全为商品端） | RESEARCH_ONLY |
| `007` | ✅ E064（2025 以来 A 股黄金股指数整体上涨超一倍） | PROMOTE |
| `008` | ✅ E075（化肥概念板块 2021 +24.24%）但 **PIT = 0** | RESEARCH_ONLY |
| `009` | ❌ **零**（5 条全为商品端）· Worker 自认传导证据不足 | RESEARCH_ONLY |
| `010` | ❌ **零权益证据**（E093/E095 为**沪铝期货**，非 A 股）· Worker 自认扩散证据弱 | RESEARCH_ONLY |
| `011` | ✅ E105（申万基础化工 2016 **-7.13%**，`contradicting`，**同窗口反例**） | RESEARCH_ONLY |

> ★ **`003` 的处理**：7 ev / 5 IG 为本包最强证据基础，且 E027 证明行业景气（净利 +462.32%）；
> 但**无任何板块指数或个股行情证据** → **`strength` 由 strong 降为 `medium`**，
> 并在 `research_notes` 中记录「**不得声称已完成 A 股市场响应验证**」，
> 建议后续轮次补齐稀土永磁板块指数序列。
>
> ★ **与 R01-01 的一致性说明（诚实记录）**：R01-01 的 `C-2018-HIEQ-ROBOT-DOWN` 在**无 A 股行情证据**的情况下被 PROMOTE。
> 本轮规则更严。该差异**保留为已知不一致**（见 §8 未决问题），**本轮不回改 R01-01**。

---

## 2. 12 条 Conflict 的最终裁决

| conflict | 原状态 | **本轮裁决** |
|---|---|---|
| **`CF001`** 2021 大类周期 vs 多个独立 Campaign | UNRESOLVED | **裁决：多个独立 Campaign**（001 / 003 / 004 各自独立）+ **上位 Theme Cycle** `resource_reflation_2020_2022`（Pattern = Parallel）。Gate Q1（注意力中心不同）· Q2（代表标的不重叠）· Q4（peak 不同步：001 = 2021-09-13 / 003 = 2021-11-09 / 004 = 2021-10-31）→ **不合并**。★ 即 P1（多 Campaign）在 **Campaign 层**成立，P2（同一大周期）在 **Theme Cycle 层**成立 —— 两者并不矛盾。 |
| **`CF003`** 锂的跨族归属 | UNRESOLVED | **保留为未决**。Macro Theme 归属**按 CMTR v1 解析结果**置于 `资源` 根下 `有色金属` 子主题；「是否应归 电力设备 / 汽车」属跨族问题，**CMTR v1 不回答**，**不新增 canonical theme**。 |
| **`CF006`** 锂 商品 peak vs A 股 peak（差 ~14 个月） | KEEP_BOTH | **裁决：canonical peak = A 股口径 2021-09-13**（能源金属指数区间最高点，E015）；**商品口径峰值 2022-11-11**（碳酸锂 59 万元/吨，E012/E013）**作为 alternative 保留**。**不强行同步**。`end = 2022-11-11`（商品周期见顶日）。 |
| **`CF009`** 2025-12 金价新高但 A 股金矿未同步 | UNRESOLVED | **保留 UNRESOLVED（不消解）**。**`C-2024-RES-GOLD-CB` 的 `peak_date = NULL`** —— A 股口径峰值未被证据支持（E064 仅证明「2025 年以来涨超一倍」，**未给峰值日期**）；商品峰值 2025-12-26 **不得直接用作 A 股 peak**。`end_date = NULL`（结构仍在延续）。 |
| `CF002` 2021 电解铝机制归属 | KEEP_BOTH | **保留**。电解铝同时受 001（再通胀）与 004（能耗双控）两套机制影响，真实并存，**不机械归并**。 |
| `CF004` 稀土机制归类（资源 vs 政策） | KEEP_BOTH | **保留**。两侧证据均在（E023 供给面 vs E022/E026 配额与整合）。 |
| `CF005` 2021 有色涨幅口径（申万 40.47% vs 中证 31.31%） | KEEP_BOTH | **保留**。引用时必须说明口径，**不得混用**。 |
| `CF007` 2020 金价峰值三口径 | KEEP_BOTH | **保留**（该候选为 RESEARCH_ONLY，peak 仅记录商品口径）。 |
| `CF008` 响水伤亡人数通报口径（44 / 78 人） | KEEP_BOTH | **保留**。滚动通报不同时点；**不得把后一数字当作事发当日已知信息**。 |
| `CF010` 2016 化工：商品上行 vs A 股下行 | KEEP_BOTH | **保留**（本包最重要反例：「商品上涨**不构成** A 股主题启动的充分条件」）。 |
| `CF011` 双控方案印发日期（09-11 / 09-16） | KEEP_BOTH | **保留**。004 的 start 采用 **2021-08-12**（E031 一手文件），**不依赖该争议日期**。 |
| `CF012` 同一证券跨候选归属 | KEEP_BOTH | **保留**。紫金矿业（001/007/009）· 云天化（004/008）· 中国铝业/云铝股份（001/004/010）—— 多主业为合法历史事实，**不构成合并理由**，但提示边界需后续复核。 |

> **12 条全部处理：4 条裁决（CF001 / CF006 明确裁决，CF003 / CF009 明确保留未决），8 条 KEEP_BOTH 保留。**
> **未为「消除 Conflict」而强行合并或拆分。**

---

## 3. P0 关键数据（裁决依据）

```
2021 申万一级行业涨幅（E005/E006）：电力设备 +47.86% · 有色金属 +40.47% · 煤炭 +39.6% · 基础化工 +37.19%
中证有色金属指数 000819.SH（E007）：2021 区间最高 8603.88 点 @2021-09-13
LME 铜（E001）：2021-05-10 = 10747.5 美元/吨 历史新高          ← 商品 peak
能源金属指数 399366.SZ（E015）：区间最高点 2021-09-13           ← A 股 peak
电池级碳酸锂（E012/E013）：2022-11-11 = 59 万元/吨 历史高点      ← 商品 peak（滞后 14 个月）
氧化镨钕（E026）：2021-11-09 = 76.26 万元/吨（北方稀土挂牌价）
国际现货黄金（E063）：2025-12-26 = 4526 美元/盎司（历史新高）
```

★ **商品价格 peak ≠ A 股 Campaign peak**：本轮的 canonical peak **一律采用 A 股口径**（与既有 26 个 Campaign 的惯例一致）；
商品口径峰值**全部作为 alternative 保留**，**未人为强行同步**。

---

## 4. 新增 6 个 Canonical Campaign

| canonical_id | year | start | peak | end | class | strength | result | dc | themes |
|---|---:|---|---|---|---|---|---|---|---|
| `C-2020-RES-NONFERROUS` | 2020 | 2020-03-23 | **2021-09-13** | 2021-12-31 | theme_campaign | strong | positive | medium | 资源(related) + 有色金属(main) |
| `C-2020-RES-LITHIUM` | 2020 | 2020-10-27 | **2021-09-13** | 2022-11-11 | theme_campaign | strong | positive | medium | 资源(related) + 有色金属(main) |
| `C-2020-RES-RAREEARTH` | 2020 | 2020-05-01 | 2021-11-09 | 2021-12-31 | theme_campaign | **medium** | positive | medium | 资源(related) + 稀有金属/稀土(main) |
| `C-2021-RES-CHEM-DUALCTRL` | 2021 | 2021-08-12 | 2021-10-31 | 2021-12-31 | theme_campaign | strong | positive | medium | 资源(related) + 基础化工(main) |
| `C-2019-RES-DYE-SHOCK` | 2019 | 2019-03-21 | 2019-04-04 | 2019-07-30 | event_driven | medium | positive | medium | 资源(related) + 基础化工(main) |
| `C-2024-RES-GOLD-CB` | 2024 | 2024-02-01 | **NULL** | **NULL** | theme_campaign | medium | positive | **low** | 资源(related) + 贵金属(main) |

**机制覆盖（对应 Historical Universe 缺失轴）**：
- **供给收缩五子类型**：行政去产能（`RC-2017-RES-ALUMINUM`）· 能耗双控行政限产（`C-2021-RES-CHEM-DUALCTRL`）·
  环保约束（`RC-2016-RES-CHEM-ENV`）· 配额型供给约束（`C-2020-RES-RAREEARTH`）· **安全事故冲击**（`C-2019-RES-DYE-SHOCK`）
- **全球流动性 + 需求复苏**：`C-2020-RES-NONFERROUS`
- **新能源需求拉动**：`C-2020-RES-LITHIUM`
- **黄金资产属性**：`C-2024-RES-GOLD-CB`

**被合并 / 被拆分**：**无**（CF001 的「多段」读法未被采纳为拆分；001/003/004 未被合并）。

---

## 5. 5 个 RESEARCH_ONLY 的保存方式

> **均不进入 `campaigns` 表**（Research Model v1.0 §4）。仅在导出层 `research_candidates` 承载；
> 其**专属 evidence（25 条）不入 DB** —— 避免 `orphan-supporting-evidence` 告警（与 R01-01/02 同口径）。

| canonical_id | 理由 |
|---|---|
| `RC-2020-RES-GOLD-RATES`（006） | 4 条证据**全为商品端**，**A 股板块证据为零** → 「市场关注」无证据支撑 |
| `RC-2022-RES-FERTILIZER`（008） | **PIT 证据 = 0** + 传导无法确认（E075 峰值 2021-09-28 早于商品 peak 2022-03~04 **约半年**）。★ **明确不作反例结论**（原错误定性已撤回）；★ 采用 **Addendum 修正后的真实表述**（E075 为 `contemporaneous`，非 subsequent） |
| `RC-2025-RES-COPPER`（009） | 5 条证据**全为商品端**，**无 A 股铜板块证据** · Worker 自认传导证据不足 |
| `RC-2017-RES-ALUMINUM`（010） | **无任何 A 股权益证据**（E093/E095 为**沪铝期货**）· Worker 自认扩散证据弱。★ **PIT 覆盖全包最优（5/6）**，补齐板块序列后应**优先重新评估** |
| `RC-2016-RES-CHEM-ENV`（011） | `INSUFFICIENT` · `low` · **0 securities** · **同窗口反例有效**（商品 +29.84% vs 申万基础化工 **-7.13%**，E101 vs E105） |

---

## 6. Theme Cycle（新增 3 个）

| theme_cycle_id | 成员 | Pattern |
|---|---|---|
| `resource_reflation_2020_2022` | `C-2020-RES-NONFERROUS` · `C-2020-RES-LITHIUM` · `C-2020-RES-RAREEARTH` · `C-2021-RES-CHEM-DUALCTRL` | **Parallel**（同一「供给约束 / 再通胀」上位主题下的四个机制各异的独立 Campaign） |
| `dye_shock_2019` | `C-2019-RES-DYE-SHOCK` | 单一 |
| `gold_cb_demand_2024_2025` | `C-2024-RES-GOLD-CB` | 单一 |

> **未新增 DB 实体** —— `theme_cycle_id` 沿用既有「研究级标签」做法（写入 `season_id` 与 `research_notes`）。

---

## 7. DB / Export 变化

| 表 | R01-03 前 | 后 | Δ |
|---|---:|---:|---:|
| `research_rules` | 6 | **7** | +1（`rule_resources`） |
| `annual_reviews` | 39 | **43** | +4（`AR-RES-{2019,2020,2021,2024}`） |
| `campaigns` | 26 | **32** | **+6** |
| `sources` | 155 | **203** | +48 |
| `evidences` | 160 | **196** | +36 |
| `events` | 79 | **93** | +14 |
| `securities` | 83 | **112** | +29（30 − 1 复用既有 `GANFENG`） |
| `campaign_themes` | 58 | **70** | +12 |
| `campaign_evidences` | 151 | **187** | +36 |
| `campaign_events` | 72 | **86** | +14 |
| `campaign_securities` | 100 | **126** | +26 |
| `campaign_phases` | 72 | **78** | +6 |
| `campaign_date_observations` | 61 | **77** | +16 |
| `themes` | 52 | 52 | **0（未改 taxonomy）** |

**既有数据零改动**：既有 26 campaigns / 52 themes / 39 annual_reviews / 6 rules / 160 evidences /
155 sources / 83 securities / 79 events 及全部桥表 → **逐行比对「被改动：无」** ✓

★ **证券复用**：`GANFENG`（赣锋锂业 002460）**已存在于 DB**（既有族）→ **复用既有行，未重复建行** ✓

**Export**：campaigns 26 → **32** · research_candidates 10 → **15** · rules 6 → **7** ·
events 86 → **100** · securities 129 → **167** · **`timeline_export_version = "1.0"` 未变** ✓

---

## 8. 所有验证结果 → **全部 PASS**

| 检查 | 结果 |
|---|---|
| `validate_db` | **PASS**（**3 条 WARNING —— 与 R01-03 导入前完全相同，无新增**） |
| `validate_timeline_export` · `validate_batch_research` · `validate_promotion_manifest` · `check_doc_schema_consistency` · `validate_current_research` | **PASS** |
| `validate_monorepo_integrity` · `refresh --check` | **PASS** |
| `intake --check` | **PASS（0 FAIL / 0 WARN）** |
| Intake Validator C01–C25（R01-01 / R01-02 / R01-03） | **PASS / PASS / PASS** |
| `test_validate_historical_research_intake.py` | **PASS（44 / 44）** |

★ `research/schema` · `contracts` · `src` · Structural Analogy v0.2 · Time Observation → **零改动** ✓

**Historical Universe 当前实测**：root **11** · **有 Campaign 的 root 7**（新增 `资源`）·
Historical Campaign **32** · Research Candidate **15** · 跨族 Campaign 对 `C(7,2)` = **21**。

---

## 9. 尚未解决的问题

| # | 项 | 说明 |
|---|---|---|
| 1 | **`CF003`（锂跨族归属）保留未决** | CMTR v1 解析至 `资源`，但「资源 vs 电力设备/汽车」的跨族争议未裁决；**不新增 canonical theme** |
| 2 | **`CF009`（2025-12 黄金商品与 A 股背离）保留 UNRESOLVED** | `C-2024-RES-GOLD-CB` 的 `peak_date = NULL`、`end_date = NULL` |
| 3 | **`003` 缺 A 股板块指数证据** | 已降 `strength` 至 medium；**不得声称已完成市场响应验证**；建议补齐稀土永磁板块序列 |
| 4 | **与 R01-01 的规则不一致（诚实记录）** | R01-01 的 `C-2018-HIEQ-ROBOT-DOWN` 在无 A 股行情证据下被 PROMOTE；本轮规则更严。**本轮不回改 R01-01**，差异保留待后续统一 |
| 5 | **5 个 RESEARCH_ONLY 待补证** | 006（A 股板块序列）· 008（2022 逐月板块序列 + PIT 标注）· 009（A 股铜板块序列）· 010（电解铝板块序列，**PIT 覆盖最优，优先**）· 011（板块内部结构） |
| 6 | **`CF012` 边界提示** | 紫金矿业/云天化/中国铝业等跨候选，提示 001/004/007/008/009/010 的边界可能需复核 |
| 7 | **`C-2020-RES-NONFERROUS` 的 phase 与 peak 口径分歧** | 其 `campaign_phases.MAIN_RISE` 来自 intake lifecycle（终于**商品**峰值 2021-05-10），而 canonical `peak_date` 采用 **A 股**口径 2021-09-13 —— 已在 `research_notes` 记录，**未改 phase**（属研究结论） |
| 8 | **别名 taxonomy 缺口** | 工业金属/铜/电解铝/锂/锂矿/能源金属/稀土/稀土永磁/化工/染料/化肥/黄金 —— **只记录，未扩展** |
| 9 | **Structural Analogy / Time Observation 未刷新** | 仍待 R01 全部完成后以新 artifact 版本统一刷新 |
| 10 | **Validator C08 vs Research Model v1.0 §15 的 `research_report` tier 冲突** | 与 R01-03 无关（本包 2 个 research_report 均 tier 2，符合 C08）；仍待独立工程处理 |

---

## 10. 本轮严格未做

- ❌ 未启动 R01-04 的 ThreeC Intake（不影响 R01-04 Worker 独立 Research）· 未启动 R01-05 / R01-06
- ❌ 未刷新 Structural Analogy / Time Observation
- ❌ 未修改 Research Model v1.0 / Schema / Protocol / Export Contract / CMTR v1 / taxonomy
- ❌ 未回改 R01-01 / R01-02 的任何数据（既有 26 campaigns 逐行零改动）
- ❌ 未为「消除 Conflict」而强行合并或拆分
