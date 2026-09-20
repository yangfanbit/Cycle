# R01-05 Intake Review v0.1 — 金融 / 房地产

> **性质**：ThreeC Agent 对 `research/intake/packages/R01-05/`（**Worker v2**）的 **Intake 层**审查。
> **本轮范围**：只做 Intake Review。**未创建 Canonical Campaign · 未导入 DB · 未修改既有 Campaign ·
> 未修改 taxonomy · 未修改 Schema / Protocol · 未刷新 Structural Analogy / Time Observation ·
> 未启动 R01-06 的 ThreeC Intake · 未修改 Package。**
> **13 条 Conflict 一条未消解**；Campaign 的合并 / 拆分**未提前决定**。

---

## 0. 结论摘要

| 项 | 结果 |
|---|---|
| **A. Package 是否通过 Intake** | ❌ **未通过** —— **1 项 C20 FAIL**（`checksums.sha256` 引用不存在的 `README.md`） |
| **B. C25 Strict Draft-07** | ✅ **0 违规**（独立 `jsonschema` 4.26.0 复核确认） |
| **J. 是否建议进入 Canonicalization** | ✅ **建议** —— 但须先修复 §2 的 2 项 Package 侧问题（或由 ThreeC 侧豁免说明） |

> ★ **本轮以 v2 Package 为正式版本**（Worker v2 已补入一级行情证据 E130–E141 与来源 S057–S061）。
> ★ **v2 已上调 4 个候选的置信度**（008 INSUFFICIENT→PROVISIONAL；009/005/008 low→medium），
> **但本包仍然没有 high confidence 候选** —— 原因已在 `quality_summary` 中明确：
> ① 只有锚点日端点口径、无连续日线；② **前复权含股息 vs 沪深300 价格指数不含股息（CF013）**；③ **Beta 中性验证未做**。

---

## 1. Package 验收

### 1.1 规模与 checksum

| 项 | 数量 |
|---|---:|
| Candidates | **12** |
| Evidence | **63**（含 v2 新增 E130–E141，共 12 条） |
| Sources | **60**（含 v2 新增 S057–S061，共 5 条） |
| Securities | **15** |
| Exclusions | **12**（v2 新增 X012） |
| **Conflicts** | **13**（v1 为 10；v2 新增 CF011/CF012/CF013） |
| **Research Questions** | **13**（v1 为 11） |
| Macro Theme Proposals | **7** |
| Cross-task Notes | **6** |

> ★ 用户任务书提到「10 个 Conflict」，那是 **v1** 的口径；**v2 实际为 13 条**。本轮按 v2 审查。

**置信度分布**：`high 0 / medium 8 / low 4`（v1 为 `high 0 / medium 5 / low 7`）。

### 1.2 ★ checksum 核对 → **发现 1 项 FAIL**

| 检查 | 结果 |
|---|---|
| `checksums.sha256` 条目数 | **11**（其它 4 个包均为 **10**） |
| 目录中非-checksum 文件数 | **10** |
| **checksum 引用但文件不存在** | ❌ **`README.md`** |
| 已引用文件的哈希 | 全部一致 ✓ |

**Validator 结果**：

```
validate_historical_research_intake.py research/intake/packages/R01-05
  → FAIL  C20   checksums 引用的文件不存在: README.md
  → INFO  C25   Strict JSON Schema (Draft-07) 校验通过（0 违规）
  → checks: 25   FAIL: 1   WARN: 0   RESULT: FAIL
```

`--check`：**FAIL（1）· packages found: 5** —— 该 FAIL **由 R01-05 引起**。

**根因**：Worker 的 `05_OUTPUT/checksums.sha256` 包含其工作区模板文件 `README.md` 的哈希
（`ffaf8b9c…`），但**复制到 ThreeC 时未包含该文件**（R01-01/02 曾有此文件、R01-03/04 从未有）。
→ **属 Package 侧一致性缺口**（非 Validator 缺陷、非 Schema 问题）。

### 1.3 ★ C25 Strict Draft-07

| Package | Draft-07 违规数 |
|---|---:|
| **R01-05** | **0** ✓ |
| R01-01 / R01-02 / R01-03 / R01-04（对照） | 0 / 0 / 0 / 0 |

独立复核（`jsonschema` 4.26.0 / `Draft7Validator` / `FormatChecker`，按 Validator 的装配规则组装完整对象）→ **0 违规** ✓

---

## 2. 必须修复的问题（Package 侧，**本轮只报告不修**）

| # | 问题 | 影响 | 建议修复 |
|---|---|---|---|
| **B1** | **`checksums.sha256` 含 `README.md` 条目但文件不存在** | **C20 FAIL** → `intake --check` 红 | 二选一：① 从 `checksums.sha256` 删除该行（与 R01-03/04 一致，10 条）；② 补入 `README.md` 并重算 |
| **B2** | **`manifest.task_scope.excluded_scope` 为 v1 残留文本，与 v2 内容矛盾** | 描述性字段误导 | 该字段仍写「**工作区内富途行情接口不可用，未取得任何一级行情数据**…**全部市场幅度证据来自二级来源**」，而 v2 已取得 E130–E141 一级行情证据。★ 其中「**未做 Beta 中性验证**」一句**仍属实**，须保留 |

> ★ **两项均为 Package 侧问题，不涉及 Protocol / Schema / Validator**。

---

## 3. 结构与引用关系

### 3.1 引用完整性

| 检查 | 结果 |
|---|---|
| candidate → evidence 悬空 | **无** ✓ |
| candidate → security 悬空 | **无** ✓ |
| evidence → source 悬空 | **无** ✓ |
| date_candidates → source 悬空 | **无** ✓ |
| **conflict.positions → source / evidence 悬空** | **无** ✓ |

### 3.2 孤儿检查

| 类型 | 结果 |
|---|---|
| 孤儿 Evidence | **0** ✓ |
| **孤儿 Source** | ⚠️ **6 个**：`S005` `S012` `S013` `S019` `S024` `S029` |
| 孤儿 Security | **0** ✓ |

> ★ `S005`/`S019`/`S024` 属 Worker 在 `coverage.md §9` 明确说明的「**同源转述不计为独立证据**」组
> —— 它们被定义以记录 **retelling 关系**，但**未绑定为任何 evidence 的 source**。
> `S012`/`S013`/`S029` 亦未被引用。**不阻塞**（Schema 不要求反向引用；C01–C25 无孤儿检查）。
> **建议**：绑定至相关 evidence，或在 `sources.description` 中显式标注「仅用于同源性说明」。

### 3.3 Research Model v1.0 §5 证据门槛

**12 / 12 候选全部满足「≥2 Evidence 且 ≥2 independence_group」** ✓

| candidate | ev | IG | sec | **PIT 证据** |
|---|---:|---:|---:|---:|
| `001` 三支箭地产 | **11** | **10** | 4 | **6** |
| `002` 5·17 地产 | 8 | 8 | 2 | 5 |
| `003` 2018–2019 地产 | 6 | 6 | 2 | 4 |
| `004` 地产下行 | 8 | 8 | 4 | 3 |
| `005` 2024-09 券商 | 8 | 7 | 3 | 2 |
| `006` 2023 中特估 | 5 | 4 | 4 | 1 |
| `007` 2023–2025 银行高股息 | **10** | 8 | 4 | 2 |
| `008` 2020–2021 银行顺周期 | **4** | 4 | 2 | 1 |
| `009` 2020-07 券商 | **4** | 4 | 3 | 2 |
| `010` 2025 保险 | **4** | 4 | 3 | 1 |
| `011` 棚改去库存 | **2** | 2 | 1 | 1 |
| `012` 2015 杠杆牛金融股 | **2** | 2 | 2 | **0** |

### 3.4 ★ 共享 evidence（跨候选）

**4 条**：

| evidence | 被引候选数 | 引用者 | 判定 |
|---|---:|---|---|
| **`E141`**（沪深300 基准序列） | **10** | 001–010 | ★ **设计上正确** —— 它是本包**统一基准**；但 **canonical 化时会违反 `validate_batch_research` 的 1 evidence : 1 campaign** → **须在 Canonical Decision 中决定处理方式**（建议：作为全局基准不绑定 `campaign_evidences`，或按候选拆分） |
| `E132`（工商银行 2020-10-30→2021-03-31） | 2 | 004, 008 | 须 1:1 消歧 |
| `E137`（2024-12-31→2025-09-19 相对表现） | 2 | 007, 010 | 须 1:1 消歧 |
| `E140`（工商银行 2023-01-31→2023-12-29） | 2 | 006, 007 | 须 1:1 消歧 |

> ★ **不存在「同一行情证据被错误复用」** —— `E141` 的共享是**基准性质**，其余 3 条是**跨候选真实相关**
> （同一银行标的在两个不同窗口/候选中被引用）。**但 canonical 化须按 1:1 规则处理** ✓

### 3.5 evidence / source / security 治理

| 维度 | 分布 |
|---|---|
| `temporal_relation` | contemporaneous 30 · **retrospective 19** · subsequent 14 |
| `evidence_role` | supporting 45 · **contradicting 8** · context 10 |
| `support_kind` | historical_fact_support 63 · point_in_time_support 29 · **retrospective_context 19** |
| subsequent / retrospective **缺 `point_in_time_note`** | **无** ✓ |
| `source_type` | media_tier2 20 · media_tier3 14 · research_report 10 · regulator 8 · **`other` 5** · industry_association 2 · website 1 |
| `tier` | tier 2 = 36 · tier 3 = 15 · tier 1 = 9 |
| `research_report` 的 tier | **10 / 10 全部 tier 2** ✓（C08 满足） |
| 无 `url` 且无 `no_url_reason` | **无** ✓ |
| securities | 15 条，**全部有 ticker** ✓ · **全部 `survivorship_aware = True`** ✓ |

---

## 4. ★ 重点检查 1：新增一级行情证据（E130–E141 / S057–S061）

### 4.1 结构与引用

| 检查 | 结果 |
|---|---|
| E130–E141 **全部存在** | ✅ 12 条齐备 |
| S057–S061 **全部存在** | ✅ 5 条齐备 |
| evidence → source 悬空 | ✅ **无** |
| **E130–E141 是否全部被候选引用** | ✅ **全部被引用**（E130→003 · E131→009 · E132→004,008 · E133→001 · E134→002 · E135→005 · E136→007 · E137→007,010 · E138→007 · E139→005 · E140→006,007 · E141→001–010） |
| 是否有 orphan evidence | ✅ **0** |

### 4.2 日期 / 证券 / 区间一致性

| evidence | event_date | 区间 / 标的 | 一致性 |
|---|---|---|---|
| `E130` | 2019-04-19 | 2018-11-30→2019-04-19 · 保利 +11.7% / 万科 +29.5% / 沪深300 +29.9% | ✅ 与 `candidates[003]` 窗口一致 |
| `E131` | 2020-07-15 | 2020-06-30→2020-07-15 · 中信 +35.6% / 东方财富 +39.9% | ✅ 与 `candidates[009]` 一致 |
| `E132` | 2021-03-31 | 2020-10-30→2021-03-31 · 工商银行 +19.8% | ✅ 与 `candidates[008]` lifecycle `MAIN_RISE 2020-10-30→2021-03-31` **完全一致** ✓ |
| `E133` | 2023-01-31 | 2022-10-31→2023-01-31（三支箭窗口） | ✅ 与 `candidates[001]` 一致 |
| `E134` | 2024-09-13 | 2024-05-17→2024-09-13 · 保利 -31.3% / 万科 -29.8% | ✅ 与 `candidates[002]` 一致 |
| `E135` | 2024-10-08 | 2024-09-13→2024-10-08 | ✅ 与 `candidates[005]` peak 2024-10-08 一致 |
| `E136` | 2025-09-19 | 2023-12-29→2025-09-19 · 工商银行 +78.7% | ✅ 与 `candidates[007]` SECONDARY 2025-01-01→2025-09-19 一致 |
| `E137` | 2025-09-19 | 2024-12-31→2025-09-19 · 工商银行 / 中国平安 | ✅ 与 `candidates[010]` 一致 |
| `E138` | 2025-09-19 | 2022-10-31→2025-09-19 · 工商银行 +135.8% / 保利 -38.0% | ✅ |
| `E139` | 2024-12-31 | 2024-09-13→2024-12-31 · 中信 +59.3% | ✅ 与 `candidates[005]` 一致 |
| `E140` | 2023-12-29 | 2023-01-31→2023-12-29 · 工商银行 +24.7% | ✅ 与 `candidates[006]` 一致 |
| `E141` | 2025-09-19 | 沪深300 **15 个锚点日**收盘点位 | ✅ 与各候选窗口一致 |

★ **日期 / 证券 / 区间一致** ✓ —— 且 `E132` 的区间与 `candidates[008]` 的 lifecycle 端点**精确对应**，
说明行情证据是按候选生命周期锚点**定向取数**的 ✓

### 4.3 ★ 是否把「相对沪深300」写成 Alpha

| 检查 | 结果 |
|---|---|
| `coverage.md §4.1` | ✅ 明确「本包取得的是**相对沪深300 的区间超额**，这是**相对表现证据，不等于 Beta 中性**…**不声称已完成 Beta 分离**」 |
| `coverage.md §4.2` | ✅ 明确「因此上表银行超额**被系统性高估**，**不得直接表述为行业 Alpha**」 |
| `quality_summary.known_gaps[2]` | ✅ 「★ Beta 中性验证完全未做…**不得据此声称已完成 Beta 分离**」 |
| `candidates[005].why_not` | ✅ 「**Beta 与行业结构不可分离**…券商上涨**高度可能完全是市场 Beta 的放大**」 |
| `candidates[007].why_not` | ✅ 「银行 Alpha 与红利风格因子**是否可分，未做验证**」 |
| `candidates[009].why_not` | ✅ 「**Beta 中性验证未完成**」 |

> ## ✅ **未把相对收益写成 Alpha** —— 该 caveat 在 **coverage / quality_summary / candidate.why_not** 三层均已保留 ✓

### 4.4 ★ 是否把端点价格数据解释成完整生命周期

| 检查 | 结果 |
|---|---|
| `coverage.md §4.3` | ✅ 「15 个锚点日之间**只有两个端点，没有连续日线**…峰值**精确日期**仍不可判定（只能给窗口）· 无法计算波动率、最大回撤、回撤持续期」 |
| `quality_summary.known_gaps[1]` | ✅ 「仅为**锚点日的端点口径**…**不是连续日线序列**」 |
| `known_gaps[6]` | ✅ 「2024-05「5·17」窗口**仍缺连续日线**…**中途路径与峰值精确日期未闭合**」 |
| 候选 `peak` 精度 | ✅ 各候选的 peak 仍为 `DATE_WINDOW` / `PHASE_WINDOW` / 推断值（**未被端点数据升格为精确日期**） |

> ## ✅ **未把端点数据解释成完整生命周期** ✓

---

## 5. 重点检查 2：Candidate 处置资格

### 5.1 `001` / `002` / `003` 三类地产政策结构

| candidate | 政策存在 | **市场响应** | 判定 |
|---|---|---|---|
| `001` 三支箭（2022-11） | ✅ 一手政策（银发〔2022〕254 号等） | ⚠️ **E133**：保利 +15.1%、万科 +37.1%、工商银行 +5.8%，沪深300 +18.5% → **保利相对 -3.3pct、万科 +18.7pct**（**CF011：两龙头方向相反**） | **有条件进入** —— 但 **CF011 须由 Canonical Decision 裁决**（`已知_gaps[5]` 明确「不允许取平均充当板块表现」） |
| `002` 5·17（2024-05） | ✅ 一手政策 | ❌ **E134 强反向**：保利 -31.3%、万科 -29.8%，相对 -17.2pct / -15.7pct（4 个月**全部回吐**） | **建议 Research Only** —— Worker 自述其价值已变为「**市场层证伪的教**（样本）」 |
| `003` 2018–2019 | ✅ 地方调控放松 | ❌ **E130 反向**：保利相对 -18.2pct、万科 -0.4pct，**两龙头均未跑赢基准**；同期中信证券 +52.3%（相对 +22.4pct） | **Research Only** —— `INSUFFICIENT` / `low`，且 `exclusion X012` 已明确记录其 **NOT_A_CAMPAIGN** |

> ## ✅ **未让「政策存在」替代 Campaign 成立证据** —— 三条均有**市场层实证**，其中两条为**证伪** ✓

### 5.2 `004` 地产下行 / 风险暴露

- `classification = industry_trend`，lifecycle `DECLINING 2020-08-20→2021-12-31` + `ENDED 2022-01-01→2022-07-31`
- Worker 的 `why_not`：「★ 它是**下行结构**，不是『历史机会』结构…**不因它不是机会型而删除**」
- **`result` 字段**：⚠️ 候选未在 `why_not` 中显式给出 `result` 口径 —— hmm，`candidates[004]` 的 `classification_proposal = industry_trend`，`research_status = PROVISIONAL`。
  Hmm — **本包 12 个候选的 JSON 中均无 `result` 字段**（Schema 的 `campaign_candidate` 不含 `result`）→ `result` 属 **canonical 层字段**，由 ThreeC Agent 在 Canonical Decision 中赋值 ✓
- **与既有体系的一致性**：R01-01 的 `C-2018-HIEQ-ROBOT-DOWN` 与 R01-03 的 `C-2022-SEMI-DOWNTURN` 已确立
  「**下行结构亦可进入 canonical，以 `result = weak` 表达**」的先例 ✓
- **判定**：**有条件进入** —— **`CF007` 须裁决「下行结构是否进入 canonical」**（本包不自行裁决）✓

### 5.3 `005` / `009` 两个券商候选（均 `CONFLICT`）

| | `005`（2024-09） | `009`（2020-07） |
|---|---|---|
| 相对强度实证 | ✅ 中信 +59.3%（相对 **+34.7pct**）；东方财富 2024-09-13→10-08 相对 **+102.1pct** | ✅ 中信 +35.6%、东方财富 +39.9%（相对 **+21.6pct / +26.0pct**） |
| 政策组合拳 | ✅ 同日三大金融管理部门同场发布（货币 + 资本市场 + 地产） | ⚠️ 资本市场改革预期 |
| 成交量 / 风险偏好 | ⚠️ 10-08 成交额 **3.5 万亿元**创历史新高 | ⚠️ 成交量放大 |
| **是否只是 Market Beta** | ⚠️ **无法排除** —— 同日三部门同场 + 全市场级别成交额 → **Beta 与行业结构不可分离** | ⚠️ **证据本身即反证**：「银行、保险、互联网金融等大金融**全线走高**」= 典型 Beta 形态 |
| 独立生命周期 | ⚠️ `MAIN_RISE 2024-09-24→2024-10-08`（**仅 11 个交易日**） | ❌ `UNKNOWN`（**无 lifecycle**） |

> ## ✅ **未因一级行情显示超额就直接 Promote** —— 两者的 `research_status` **均为 `CONFLICT`** ✓
> ★ Worker 的关键论证：东方财富 +102.1pct 的**数量级本身就是「成交量 Beta 代理」的信号，不是行业 Alpha 的信号** ✓
> **判定**：`005` **有条件进入**（`CF003` 须裁）· `009` **有条件进入**（`CF008` 须裁）—— 但 **`009` 无 lifecycle、仅 4 ev**，倾向**补证**

### 5.4 `006` / `007` / `008` / `010` 金融内部不同机制

| candidate | 机制 | 关键证据 | 判定 |
|---|---|---|---|
| `006` 2023 中特估 | **估值体系叙事 + 低估值修复** | 工商银行 2023-01-31→2023-12-29 相对 **+42.2pct**（沪深300 **-17.5%**） | **有条件进入** —— 生命周期未闭合（peak/end 推断）、仅 1 条同期证据 |
| `007` 2023–2025 银行高股息 | **低利率 + 资产荒 + 高股息（资金配置驱动）** | 工商银行 2023-12-29→2025-09-19 相对 **+47.5pct**；2022-10-31→2025-09-19 相对 **+107.5pct** | **有条件进入** —— **无启动锚点** + **CF004 红利风格因子** + **CF013 口径差** |
| `008` 2020–2021 银行顺周期 | **经济复苏 + 信用成本改善（信用周期驱动）** | 工商银行 2020-10-30→2021-03-31 相对 **+12.3pct** | **建议补证** —— **仅 4 ev**、无启动锚点、无结束证据、单一代表标的 |
| `010` 2025 保险 | **资产端 + 负债端共振** | ⚠️ **CF012**：登记代表标的中国平安**跑输基准**，而保险指数涨超 30% | **有条件进入** —— 但 **CF012 须裁**（代表标的与板块叙事冲突） |

> ## ✅ **未因都属于金融而合并** —— 7 个金融候选各自独立 ✓
> ★ **`007` 与 `008` 同属银行但机制相反**（资金配置驱动 vs 信用周期驱动），
> `coverage.md §8` 明确「本包**未合并**」，且行情支持该区分（2020-11~2021-03 银行跑赢时券商跑输 -24.9pct）✓

---

## 6. 重点检查 3：金融 vs 房地产边界

| 检查 | 结果 |
|---|---|
| **是否偷偷把「金融地产」作为单一 Campaign** | ✅ **否** —— `coverage.md §7` 明确「本包**未建立任何**『金融地产 Campaign』」；`MT002` 的 `金融地产` 名称 **CMTR 未解析为根**（`unmatched`）✓ |
| 是否分别评价四类机制 | ✅ 房地产周期（001/002/003/004/011）· 银行信用周期（008）· 券商风险偏好（005/009）· 保险资产/负债（010）· 银行资金配置（007）· 估值叙事（006） |
| 行情层证据 | ✅ `coverage.md §3.3` 给出**三个窗口**证明银行/地产/券商**从未同向**；2022-10-31→2025-09-19 工商银行相对 **+107.5pct** 而保利发展相对 **-66.3pct**（**相差约 174pct**）✓ |
| 地产 → 银行风险传导 | ✅ 仅作为 **可能的 Theme Cycle / 机制联系**保留：`CF006`（UNRESOLVED，房地产与金融是否同一 Theme Cycle）· `Q005`（传导是否构成独立机制轴）—— **未提前合并** ✓ |

> ## ✅ **边界清晰** ✓

---

## 7. 重点检查 4：Beta 与市场系统性因素

| caveat | 是否保留 | 位置 |
|---|---|---|
| **未进行 Beta 调整** | ✅ | `coverage.md §4.1` · `known_gaps[2]` |
| **只有端点数据（无连续日线）** | ✅ | `coverage.md §4.3` · `known_gaps[1]` |
| **沪深300 为价格指数，个股前复权含股息** | ✅ | `coverage.md §4.2` · **`CF013`（UNRESOLVED）** · `known_gaps[3]` |
| **部分超额可能受风格 / 成交量 / Beta 影响** | ✅ | `CF003`（券商 Beta）· `CF004`（红利风格因子）· `candidates[005/007/009/010].why_not` |
| **不得声称已完成 Beta / Alpha 验证** | ✅ | `coverage.md §4.1/4.2` · `known_gaps[2]` |

> ## ✅ **caveat 在 Candidate / Evidence / Conflict / quality_summary 四层均正确保留** ✓
> ★ 本 Review **不**将其表述为「已证明行业 Alpha」；亦**不**将其表述为「已完成 Beta 中性验证」。

---

## 8. 重点检查 5：2015–2017 Priority B（`011` / `012`）

| candidate | ev / IG | PIT | status / conf | 市场层 | 判定 |
|---|---:|---:|---|---|---|
| `011` 棚改去库存 | 2 / 2 | 1 | **INSUFFICIENT** / low | ❌ **空白** | **Research Only** ✓ |
| `012` 2015 杠杆牛金融股 | 2 / 2 | **0** | **INSUFFICIENT** / low | ❌ **空白** | **Research Only** ✓ |

- **Worker 的处理**：`coverage.md §2` 说明保利发展 2016-12-30（4.7254）与 2017-12-29（10.0604）的
  **隐含复权因子相差约 57%**，无法用分红解释 → **2015–2016 锚点不用于任何量化结论**，
  Priority B 市场层**继续留空** ✓
- **`012` 的三条硬伤**（Worker 自述）：全部 retrospective、无任何行情数据、机制本身即 Beta → 建议 **Observation**
- **`X010`**（2016–2017 地产板块行情 · 复权因子异常）· **`X009`**（2025 地产 Campaign 第三层证据缺位）✓

> ## ✅ **仍被正确标记为证据不足，未因存在政策 / 历史叙述而提升状态** ✓
> ★ **Priority B 的数据缺口属客观限制，不是 Package 质量缺陷** ✓

---

## 9. 重点检查 6：Worker 报告的两个「规则问题」

### 9.1 A. C19 比 Schema 严 —— **核实结果**

**C19 实际实现**（`research/scripts/validate_historical_research_intake.py`）：

```python
if tr == "retrospective" and "retrospective_context" not in sk:
    rep.fail("C19", "evidence %s retrospective 必须含 support_kind=retrospective_context" % eid)
if tr in ("subsequent", "retrospective") and not e.get("point_in_time_note"):
    rep.fail("C19", "evidence %s temporal_relation=%s 必须填写 point_in_time_note" % (eid, tr))
```

**当前 Schema 定义**（`definitions.evidence`）：

- `support_kind`：`{"type":"array","minItems":1,"items":{"$ref":"#/definitions/support_kind"}}` —— **仅枚举 + 非空**
- **`evidence` 定义中没有任何 `if` / `then` / `allOf` 条件约束**（已逐字段确认）
- `point_in_time_note` 的「必填」**只写在 `description` 里**，**未被任何 `if/then` 强制**

| 结论 | 判定 |
|---|---|
| **C19 是否比 Schema 严** | ✅ **属实** —— C19 强制 `retrospective → 必须含 retrospective_context`，Schema 不强制 |
| **R01-05 是否存在「Validator PASS 但 Schema 不一致」** | ❌ **不存在** —— 本包 **C19 PASS 且 Strict Draft-07 PASS**（两者同时通过）；不存在「C19 通过但 Schema 违规」或反之的实例 |
| **是否构成真实 Validator ↔ Schema 冲突** | ❌ **不构成** —— 属「**Validator 业务规则严于 Schema**」的正常分层设计（Validator 可在 Schema 之上追加业务规则）；Schema 未禁止更严规则 |
| ★ **附带发现** | ⚠️ Schema 的 `point_in_time_note.description` 写「必填」但**无 `if/then` 强制** → **描述承诺了强制而实现未落实**（实际由 C19 兜底）。属 **Schema 表达 / 文档层小瑕疵**，**不影响校验结果** → 记录为独立工程观察项（§12 K3） |

> ★ **未修改 ThreeC Schema / Protocol** ✓（符合用户指示）

### 9.2 B. 富途 MCP 参数问题 —— **核实结果**

- **是否影响 R01-05 已交付 Package**：❌ **不影响** —— v2 已成功取得 **E130–E141（12 条）** 与 **S057–S061（5 条）**，
  且做了两道可信性校验（口径一致性交叉验证 + 实盘交叉核对）✓
- **是否造成数据缺失**：⚠️ **造成了两项限制，但已被显式记录**：
  ① 因 `ktype` / `autype` 枚举校验不可用，只能按锚点日取数 → **无连续日线**（`known_gaps[1]`）
  ② 2015–2016 前复权序列异常 → **Priority B 市场层留空**（`known_gaps[4]`）
- **判定**：**属外部数据工具层限制**，**不影响 Package 的接收** → **记录即可，不做工程修改** ✓

---

## 10. CMTR v1 检查（**未修改 taxonomy**）

**唯一实现**：`research/scripts/theme_taxonomy.py`（`canonical-macro-theme-resolution-1`）
现有根节点（**11**）：… · **房地产** · **金融** · …

| proposal | 名称 | kind | CMTR status | root |
|---|---|---|---|---|
| `MT001` | 房地产 | NEW_MACRO_CANDIDATE | **RESOLVED** | **房地产** |
| `MT002` | 金融 | NEW_MACRO_CANDIDATE | **RESOLVED** | **金融**（`金融地产` **unmatched** ✓） |
| `MT003` | 银行 | SUB_THEME | **RESOLVED** | **金融** |
| `MT004` | 非银金融 | SUB_THEME | **RESOLVED** | **金融** |
| `MT005` | 建筑材料 | SUB_THEME | **RESOLVED** | **房地产** |
| `MT006` | 流动性 / 政策周期 | MECHANISM | **UNRESOLVED_NAME** | — ✅ **正确** |
| `MT007` | 地产融资 / 信贷周期 | MECHANISM | **UNRESOLVED_NAME** | — ✅ **正确** |

**候选级**：**12 / 12 全部 `RESOLVED`** —— `001`/`002`/`003`/`004`/`011` → **房地产**；
`005`/`006`/`007`/`008`/`009`/`010`/`012` → **金融** ✓

> ★ **无阻塞性 taxonomy gap** ✓
> ★ **跨族边界已按协议处理**：`MT002` 的 `金融地产` **未被解析**（无该根），
> `MT006`/`MT007`（MECHANISM）的 `UNRESOLVED_NAME` 是**协议期望的正确结果** ✓
> ★ **未自行增加 canonical theme** ✓
> ★ 别名缺口（只记录，不扩展）：中特估 / 保险 / 券商 / 证券 / 因城施策 / 地产融资政策 / 地产风险暴露 /
> 房地产信贷政策 / 棚改货币化 / 高股息·红利资产

---

## 11. Candidate 处置

### D. 具备 Canonicalization 条件（**有条件，7**）

| candidate | 条件 / 必须一并裁决的 Conflict |
|---|---|
| `001` 三支箭地产 | **`CF001`**（独立 Campaign vs 大周期反弹）· **`CF011`**（两龙头方向不一致）· End 推断（low） |
| `004` 地产下行 | **`CF007`**（**下行结构是否进入 canonical**）—— 既有先例：R01-01 `C-2018-HIEQ-ROBOT-DOWN`、R01-03 `C-2022-SEMI-DOWNTURN`（`result = weak`） |
| `005` 2024-09 券商 | **`CF003`**（行业结构 vs 全市场 Beta）· **`CF013`**（口径差） |
| `006` 2023 中特估 | **`CF005`**（银行/保险是否拆分）· 生命周期未闭合 |
| `007` 2023–2025 银行高股息 | **`CF004`**（红利风格因子）· **`CF013`**（口径差）· 无启动锚点 |
| `009` 2020-07 券商 | **`CF008`**（改革驱动 vs 成交量 Beta） |
| `010` 2025 保险 | **`CF012`**（代表标的 vs 板块叙事） |

### E. 应 Research Only（**4**）

| candidate | 理由 |
|---|---|
| **`002` 5·17 地产** | **市场层强反向证伪**（保利 -31.3% / 万科 -29.8%，相对 -17.2pct / -15.7pct，4 个月全部回吐）· `confidence = low` —— Worker 自述其价值已变为「**市场层证伪样本**」 |
| **`003` 2018–2019 地产** | `INSUFFICIENT` / low · **市场层证伪**（保利 -18.2pct、万科 -0.4pct，均未跑赢）· `exclusion X012` 已明确 **NOT_A_CAMPAIGN** |
| **`011` 棚改去库存** | `INSUFFICIENT` / low · **2 ev / 2 IG** · **Priority B 市场层空白**（复权因子异常） |
| **`012` 2015 杠杆牛金融股** | `INSUFFICIENT` / low · **2 ev / 2 IG** · **PIT = 0** · 无任何行情数据 · 机制本身即 Beta → 建议 **Observation** |

### E2. 需要补证（**1**）

| candidate | 补证要求 |
|---|---|
| **`008` 2020–2021 银行顺周期** | **仅 4 ev / 4 IG** · 仅 **1 条同期市场证据** · 无启动锚点 · 无结束证据 · **单一代表标的**（工商银行）→ 补「多标的 / 行业指数广度」+「启动与结束证据」 |

> ★ **7 有条件 + 1 补证 + 4 Research Only** —— **未直接决定 Campaign 数量** ✓
> ★ **当前无 high confidence 候选，不代表 Package 质量差** —— 三道口径问题（端点口径 / 口径差 / Beta 未做）
> 已由 Worker **如实记录**，属**证据边界**而非**研究缺陷** ✓

### F. 13 条 Conflict 的优先级

| 优先级 | Conflict | 须 Canonical Decision 裁决的事项 |
|---|---|---|
| **P0** | **`CF013`** | **口径差**：个股前复权（含股息再投）vs 沪深300 价格指数（不含股息）—— **系统性高估银行超额约 +9~15pct**，**影响所有银行候选的幅度结论** |
| **P0** | **`CF003`** | 2024-09/10 券商/非银：**资本市场政策驱动的行业结构 vs 全市场 Beta 的放大** |
| **P0** | **`CF004`** | 2023–2025 银行上涨：**行业重估（高股息/资产荒）vs 红利风格因子抱团** |
| **P0** | **`CF001`** | 2022-11 三支箭：**独立政策驱动 Campaign vs 地产下行大周期中的一次政策反弹** |
| **P0** | **`CF007`** | **2021–2022 地产下行结构是否应作为 Campaign 进入 canonical**（含 `result` 口径） |
| P1 | `CF011` | 三支箭窗口内**两龙头相对方向不一致**（保利 -3.3pct vs 万科 +18.7pct）→ 无法判定「地产板块」涨没涨 |
| P1 | `CF008` | 2020-07 券商：**资本市场改革驱动 vs 成交量驱动的 Beta 放大** |
| P1 | `CF005` | 2023 中特估：**银行/保险一个 Campaign vs 拆分为两个** |
| P1 | `CF006` | **房地产与金融是否属同一 Theme Cycle**（制度联结：房地产贷款集中度管理制度） |
| P1 | `CF012` | 2025 保险：**板块年度叙事 vs 登记代表标的跑输** |
| P2 | `CF002` | 2024-05-17 新政：**是否构成地产周期反转的起点** |
| P2 | `CF009` | 2018–2019 地产：**地方调控放松是否代表中央政策转向**（影响启动锚点认定） |
| P2 | `CF010` | 2015–2016 去库存：**政策驱动的基本面周期 vs 杠杆牛市 Beta 的一部分** |

> **13 条全部移交，本轮一条未消解。**
> ★ **`CF013` 被列为 P0** —— 因为它**系统性影响所有银行候选的幅度结论**（不是单个候选的边界问题）。

---

## 12. K. 需要独立工程 / Protocol 处理的问题

| # | 问题 | 归属 | 是否阻塞 R01-05 | 处置 |
|---|---|---|---|---|
| **K1** | **`checksums.sha256` 引用不存在的 `README.md`** → C20 FAIL | **Package 侧**（非 Validator / Schema 缺陷） | ✅ **阻塞**（`intake --check` 红） | 从 checksums 删除该行（与 R01-03/04 一致）或补入文件。**本轮未执行** |
| **K2** | **`manifest.excluded_scope` 的 v1 残留文本**与 v2 矛盾 | **Package 侧** | ❌ 不阻塞（描述性字段） | 更新为 v2 口径；**「未做 Beta 中性验证」一句须保留** |
| **K3** | **Schema 的 `point_in_time_note.description` 写「必填」但无 `if/then` 强制** | **Schema 表达 / 文档层** | ❌ 不阻塞（由 C19 兜底） | 记录；若后续统一，应作为独立 Schema 轮次处理 |
| **K4** | **C19 严于 Schema** | **Validator 业务规则分层** | ❌ 不阻塞 | **不构成真实冲突** —— Validator 可在 Schema 之上追加业务规则；**本轮不修改** |
| **K5** | **`source_type` 缺「指数编制机构 / 行情数据商」类型** | **Schema 表达损耗** | ❌ 不阻塞 | 本包 `S057`–`S061`（中证指数 / 交易所 / 富途行情接口）均用 **`other`**。★ 与 R01-04 的 I1 **同一问题再次实证** → 记录；**不修改 Schema** |
| **K6** | **6 个孤儿 source**（`S005`/`S012`/`S013`/`S019`/`S024`/`S029`） | Package 侧（非阻塞） | ❌ 不阻塞 | 建议绑定或在 `description` 中标注「仅用于同源性说明」 |
| **K7** | **`E141`（沪深300 基准）被 10 个候选共享** | **Canonical 化设计问题** | ❌ 不阻塞 | `validate_batch_research` 强制 1 evidence : 1 campaign → **须在 Canonical Decision 中决定**（建议作为全局基准不绑定 `campaign_evidences`） |
| **K8** | **富途 MCP 参数限制**（`ktype`/`autype` 枚举校验不可用） | **外部工具层** | ❌ 不影响已交付 Package | 记录即可，**不做工程修改** ✓ |
| **K9** | **跨任务「市场关注」口径差异**（R01-03 起更严 vs R01-01/02） | **跨任务治理问题** | ❌ 不阻塞 | **仍未统一**；本轮不固化新 Protocol、不回改历史 |

---

## 13. 本轮严格未做

- ❌ 未创建 Canonical Campaign · 未导入 DB · 未修改既有 Campaign
- ❌ 未修改 taxonomy（CMTR v1 只读）· 未修改 Schema / Protocol / Validator
- ❌ 未修改 R01-05 Package 的任何字节（§2 的两项问题**只报告不修**）
- ❌ 未刷新 Structural Analogy / Time Observation
- ❌ 未启动 R01-06 的 ThreeC Intake
- ❌ 未消解任何 Conflict · 未提前决定任何 Campaign 的合并 / 拆分
- ❌ **未把相对收益表述为 Alpha / Beta 中性验证** ✓
