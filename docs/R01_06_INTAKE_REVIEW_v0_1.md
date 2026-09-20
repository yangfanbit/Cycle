# R01-06 Intake Review v0.1 — 国防军工

> **性质**：**只做 Intake Review**。**未创建 Campaign / 未导 DB / 未改既有 Campaign / 未改 taxonomy /
> 未改 Schema · Protocol · Validator · Research Model v1.0 / 未刷新 SA · Time Observation /
> 未修改 Package / 未启动 R01-06 Canonicalization。**
> **Package**：`research/intake/packages/R01-06/`（11 文件 · `source_commit 2153f6d` · `generated_at 2026-09-20T21:00:00+08:00`）
> **基线**：HEAD `e305fe3` · a/b `0/0` · worktree clean（R01-06 为新增未跟踪目录）
> **ThreeC 当前有效规则**：Intake Protocol v0.1 · `historical_research_intake.schema.json` · Validator **C01–C25**（含 C25 Strict Draft-07）· CMTR v1（`canonical-macro-theme-resolution-1`）
> **Worker 报告的 `24 checks` 属其 Workspace 口径 → 本 Review 一律以 ThreeC C01–C25 为准。**

---

## A. Package 是否通过 Intake → **PASS**

| 检查 | 结果 |
|---|---|
| **C01–C25（ThreeC 当前版本）** | **PASS · FAIL 0 · WARN 0** |
| **C25 Strict JSON Schema（Draft-07）** | **PASS · 0 违规** |
| `checksums.sha256` | **10 / 10 ALL OK**（独立复算；10 条声明 = 10 个正式文件；`checksums.sha256` 自身不计） |
| 正式文件数 | **11**（10 声明 + checksums）→ 与 R01-01~05 一致 |
| 数量自洽（vs `quality_summary.counts`） | **7 / 42 / 37 / 13 / 12 / 9 —— 逐项精确一致** |
| **悬空引用** | **0**（candidate.evidence_ids / evidence.source_id / conflict.positions.source_ids / exclusion.* 全通） |
| **孤儿 Evidence / Source / Security** | **0 / 0 / 0**（含 exclusions 与 research_questions 引用；**优于 R01-03 的 1 个孤儿 source**） |
| **跨候选共享 Evidence** | **0** → **无 1:1 归属冲突**（优于 R01-04 的 3 条 / R01-05 的 4 条） |
| **canonical ID 泄漏**（禁止创造 `C-* / RC-* / CC-* / TH-* / rule_* / summer_*`） | **0** ✓ |
| 顶层 ID 前缀 | 全部 `R01-MIL-` ✓ |
| Protocol §7.4 PIT 三条一致性规则 | **R1 = 0 / R2 = 0 / R3 = 0 违规** ✓ |
| `intake --check` | **PASS · packages found 6 · FAIL 0 · WARN 0** |
| Validator 单元测试 | **44 / 44 PASS** |

**结论**：Package **通过 Intake**，可直接进入 Canonical Decision 流程。

### 包规模

7 candidates · 42 evidence · 37 sources · 13 securities · 12 exclusions · 9 conflicts · 10 research_questions ·
7 macro_theme_proposals · 7 cross_task_notes

**分布**：
- `research_status`：PROVISIONAL 6 / INSUFFICIENT 1
- `confidence`：high **0** / medium 2 / low 5
- `classification_proposal`：event_driven 3 / mixed 2 / theme_campaign 1 / industry_trend 1
- `evidence_role`：supporting 32 / context 10 / **contradicting 0**
- `temporal_relation`：contemporaneous 33 / subsequent 5 / retrospective 4
- `source.tier`：T1 5 / T2 12 / T3 20（**Tier 4 = 0** ✓）
- `source_type`：media_tier3 19 / media_tier2 10 / regulator 4 / website 3 / company_announcement 1
- **`research_report` = 0**（见 §I）

---

## B. C25 Strict Draft-07 → **PASS（0 违规）**

- `jsonschema 4.26.0` 独立复核：`Draft7Validator.iter_errors()` = 0；
- `additionalProperties: false` 在 candidate / evidence / source / security / conflict / exclusion 上**全部生效**；
- 验证点：**candidate 无 `source_ids` 字段是**正确的**** —— Schema 的 `campaign_candidate.properties` **不含 `source_ids`**，且 `additionalProperties: false`；R01-06 的 7 个候选均未写入该字段 ✓；
- `conflict.positions.items` 的 Schema **只允许 `position` + `source_ids`**（无 `evidence_ids`）—— R01-06 的 19 个 position 全部只填 `source_ids`，与 R01-03/04/05 一致 ✓；
- `security.ticker` **非必填** → `R01-MIL-SEC003` 的 `ticker: null` 合法（见 §C-附注）。

---

## C. 7 个 Candidate 是否具备 Canonicalization 条件

### C.1 汇总表

| # | candidate | 年 | status / conf | ev(IG) | 市场侧证据 | **本轮判定** |
|---|---|---:|---|---:|---|---|
| 001 | 2020–2021 装备放量 / 主机厂订单与预付款 | 2020 | PROVISIONAL · medium | **17(14)** | T3 指数 + 基金持仓 | **D · 可进入（最强）** |
| 002 | 2019「南北船」合并 / 集团战略重组 | 2019 | PROVISIONAL · medium | 3(3) | **无行情证据**（有强公司/集团证据） | **D · 有条件进入** |
| 003 | 2019 国庆 70 周年阅兵 | 2019 | **INSUFFICIENT** · low | 3(2) | **全 retrospective** | **E2 · Research Only** |
| 004 | 2025 抗战 80 周年阅兵 / 军贸 / 十五五 | 2025 | PROVISIONAL · low | 4(4) | T3 相对强弱（无绝对涨幅） | **D · 有条件进入** |
| 005 | 2017 军民融合 / 军工混改 | 2017 | PROVISIONAL · low | 4(3) | 同期有（1 月启动） | **E1 · 需补证** |
| 006 | 2015 军工改革 / 资产证券化（改革牛） | 2015 | PROVISIONAL · low | 4(3) | 有，但 **Beta 不可分离** | **E2 · Research Only（倾向）** |
| 007 | 2024–2025 商业航天 / 卫星互联网 | 2024 | PROVISIONAL · low | 5(5) | 有（2025-10-24 / 12-04） | **D · 有条件进入（须先裁族属）** |

> **D = 4 · E1（需补证）= 1 · E2（Research Only）= 2** · 无 `MERGE` / 无 `EXCLUDE` 建议。
> **最终 Campaign 数量不在本轮决定** —— 由 Canonical Decision 走 Research Model v1.0 §5 + Independence Gate Q1–Q5 判定。

### C.2 `R01-MIL-001`（本包最完整候选）—— 五层链条核查

用户要求核实：**国防预算 → 装备采购/订单 → 公司经营 → A 股市场响应**。逐层核查结果：

| 层 | 承载证据 | tier | 判定 |
|---|---|---|---|
| ① 军费预算（政策层） | `E004` 2021 国防预算 13795.44 亿元 / +6.8%（**国防部官网**） | **T1** | ✅ 成立，且 evidence 自述「**不是订单本身，不单独构成订单兑现证据**」 |
| ② 订单 / 预付款（订单层） | `E001` 中航沈飞 2021 年度**日常关联交易预计**公告（**巨潮资讯网 = 证监会指定披露平台**，一手 PDF） | **T1** | ✅ 成立；**★ 关键：该 evidence 明确写「公告具体金额本文不引用，以避免依赖二级转述」** —— **未把代理变量写成精确订单总额** ✓ |
| ② 补强 | `E002` 截至 2021-04-01 **五大主机厂**均已披露关联交易预计与甲方大额预付（天风证券研报） | T3 | ✅ 行业级而非单股级；evidence 自述「研报统计基于公告，**独立性弱于公告原文**」 |
| ③ 公司经营（基本面层） | `E003` 中航沈飞 2021H1 末**合同负债 377.37 亿元** | T3 | ⚠️ 成立但**明确标注为会计口径代理变量**，且自述「**未取得公告原文**，经券商研报引用」 |
| ④ A 股市场响应（市场层） | `E008/E009`（同花顺，中证军工指数 2021 +8.97%、2021-12-01 高点 14748 点）、`E010/E012`（券商复盘）、`E015`（2021Q3 公募军工持仓 2.10%，主动配置创 2014 年来最高） | **全 T3** | ✅ 成立，但**市场层全部为二手整理**（`known_gaps[11]` 已如实记录「未取得指数公司官方历史点位原文」） |

**判定**：
- **五层链条成立**，且**每一层都标注了其证据等级与局限**；
- **订单层未越界**：一手证据（E001）刻意不引用金额，代理变量（E003 合同负债）显式标注为会计口径；
- **市场层为最弱环节**（全 T3 二手），已在 `known_gaps` 与 `why_not` 中如实记录；
- **`why_campaign` 中「17 条 Evidence、≥8 个 independence_group」表述** —— 实际为 **17 ev / 14 IG**，`≥8` **保守正确**，无夸大 ✓。

### C.3 逐候选条件（Canonicalization 前必须解决）

| # | 进入条件（**须在 Canonical Decision 中裁决**） |
|---|---|
| **001** | ① **`CF001`**：2020H2 与 2021 是否拆为两个 Campaign（若拆，各自持续性须重新论证）；② 2020-07 启动段的 **Beta 污染**（`CF006`-类问题，本包已声明「不宣称已分离」）；③ `peak` 为 **peak cluster**（2021-08-24 与 2021-12-01 并存，不得强行取单日）；④ `end` 有**两个口径并存**（2021-12-01~2022-01-31 vs 2022 年内） |
| **002** | ① **`CF002`**：与 003 是否合并（缺少 2019-07~09 连续行情数据，**关键阻塞项**）；② **`CF004`**：`event_driven` vs `theme_campaign` 的 classification 歧义；③ **市场侧行情证据完全缺失**（涨幅/峰值/持续性均不可考）→ 须用 Gate Q3 严格判定「持续性」；④ `peak` 留空、`MAIN_RISE.end` 留空 |
| **004** | ① **`CF007`**：`theme_campaign` vs `event_driven` / 是否降级 `OBSERVATION_ONLY`；② **机制复合**（阅兵 + 军贸 + 景气反转 + 十五五）**是否应拆分或降级**（不得为保持 Candidate 结构而强行合并）；③ 市场响应仅 T3 相对强弱描述，**无绝对涨幅 / 无峰值 / 阅兵后走向缺失** |
| **007** | ① **`CF004` 必须先裁族属**（国防军工 vs 信息通信 vs 跨族）—— **族属未定前不应进入 canonical**；② 生命周期未闭合（2025 年末仍活跃，peak/end 不可考）；③ 2025-12 催化集中年末，**须防止把「观察窗口结束」当作「行情结束」** |
| **005** | **需补证**：2017 年 2 月之后的走势、峰值与结束**完全不可考**，`lifecycle` 无法闭合；且**政策文本驱动，无任何订单/业绩兑现证据**（本包自述）。补证方向：2017 年军工板块全年/分月行情序列 + 混改落地公告 |
| **003** | **Research Only**：**全部 3 条证据均为 2025 年 retrospective 复盘**，无任何同期一手证据；持续性仅约 4 周；与 002 的 Q1 Anti-example（同一资金池）无法排除。**本包自述「不应作为已成立的历史 Campaign 使用」** |
| **006** | **Research Only（倾向）**：**Beta Contamination 无法排除**（本包自述「无法证明这是军工 Campaign 而不是市场 Beta 的投射」）；**无订单/业绩证据**；启动与结束日期均不可考。本包已声明「**若 ThreeC Agent 判定 Beta 无法排除，应降级为 OBSERVATION_ONLY**」 |

---

## D. 重点反向证据 `E042` —— 核查结论

**用户要求**：确认 E042（2022 国防预算 +7.1% vs 军工板块全年 -23.6%）被正确保留、不被后续叙述弱化。

### D.1 保留状态 → **未被弱化** ✓

```json
{
  "evidence_id": "R01-MIL-E042",
  "claim": "2022年全国财政安排国防支出预算约1.45万亿元，同比增长7.1%，为2019年以来首次突破7%。",
  "evidence_role": "context",
  "evidence_type": "官方发布（国防部）",
  "event_date": "2022-03-10",
  "source_id": "R01-MIL-S002",          // 国防部官网
  "confidence": "high",
  "independence_group": "IG-MOD-2022",
  "primary_source": true,
  "temporal_relation": "contemporaneous",
  "description": "★反向/对照证据：2022年国防预算增速创阶段新高，但2022年军工板块全年下跌约23.6%。这直接说明“军费增长≠军工行情”，用于防止把预算增速直接当作Campaign依据。"
}
```

**核查结果（5 项全部通过）**：
1. **`confidence = high`**、**`primary_source = true`**（国防部官网，Tier 1）—— 未被降级 ✓
2. **`description` 中显式保留反向结论**（「军费增长≠军工行情」）✓
3. **被 `CF008` 直接引用**为 position[1] 的核心依据 ✓
4. **`coverage.md §7` 方法学声明中再次重申**该反证 ✓
5. **`001.drivers.ending` 中再次引用**（「★对照：2022年国防预算增速7.1%创阶段新高但板块下跌 —— 说明军费增长本身不是行情充分条件」）✓

> **结论**：反证在 **evidence / conflict / coverage / drivers 四处**被一致保留，**未被任何后续叙述弱化** ✓

### D.2 但有两处**需在 Canonicalization 处理**的问题

**① `evidence_role = context`，而全包 `contradicting` 证据数 = 0**

- E042 的**字面 claim**（预算 +7.1%）是中性事实，标 `context` 在字面上可自洽；反向含义由 `description` + `CF008` 承载；
- 但**全包 42 条 evidence 中 `contradicting` = 0**，而本包的核心方法论主张恰是「军费增长 ≠ 军工行情」→ **反证在 role 维度上是「未标注」的**；
- **本轮判定**：**不构成 Schema / Protocol 违规**（`evidence_role` 由 Worker 自行判断），但属**语义标注偏保守**。**建议 Canonicalization 时评估是否将 E042 的 role 调整为 `contradicting`**，或在 `research_notes` 中显式注明「本证据为反向/对照证据」。

**② E042 被绑定到 `006`（2015），存在两个隐患**

- **语义错配**：E042（2022-03-10）绑定到 **2015 年**候选，而其描述用途是**军费传导边界**（主要针对 001 / CF008）；
- **DB 层 temporal-mislabel 风险**：`validate_db` 的 `evidence-temporal-mislabel` 规则为
  「`temporal_relation='contemporaneous'` 且 `evidences.date > campaigns.end_date` → WARNING」。
  若按声明导入，E042 的 `contemporaneous` 标注 + 006 的 2015 窗口 → **必然触发 WARNING**（与 R01-02 的 `E-SEMI-29/47/48` 同类）。
- **同类风险**：`E034`（2015-06-08，contemporaneous）也晚于 006 的 peak（2015-06-04），但落在 DECLINING 段内，**是否触发取决于 006 的 canonical `end_date`**（当前 lifecycle 的 DECLINING `end` 为空）。
- **本轮判定**：**属 Canonicalization 的归属/口径问题，非 Intake 阻塞项**。**建议**：E042 或改为不绑定候选（仅 `context` 保留在研究层），或调整绑定对象，或在绑定后重标 `temporal_relation`。

---

## E. Beta / 市场侧证据 caveat —— 完整性核查

**跨任务口径（沿用 R01-03 起的新观察，未固化为 Protocol）**：
> **市场关注最好有 A 股市场侧或强行业/公司证据支撑。**
> **本轮再次确认：该原则未被写入 Protocol、未回溯修改 R01-01/02。**

| 候选 | 市场侧证据 | Beta / caveat 处理 | 判定 |
|---|---|---|---|
| **001** | T3 指数 + 基金持仓 | ★ 明确标注「2020-07 启动段与 A 股整体 Beta 高度重叠，**本包不宣称已分离**」（`why_not①` + `drivers.start③` + `Q002`） | ✅ **完整** |
| **002** | **无行情证据** | 如实记录「市场反应侧行情数据缺失，若要求持续性必须有行情证据，本候选可能降级」（`why_not①`） | ✅ **完整（如实空白）** |
| **003** | 全 retrospective | 3 条证据**逐条**填 PIT note；候选级 PIT note 明写「**没有任何证据可以证明 2019 年 8 月投资者当时已知**」 | ✅ **完整** |
| **004** | T3 相对强弱 | 如实记录「仅 Tier 3 研报相对强弱，**无绝对涨幅、无峰值、无结束后行情**」 | ✅ **完整** |
| **005** | 同期有（2017-01） | 3 条 contemporaneous + 1 条 subsequent（已填 PIT note） | ✅ **完整** |
| **006** | 有，但 Beta 主导 | ★★ 「**无法证明这是军工 Campaign 而不是市场 Beta 的投射**」；`drivers.accelerator` 仅 1 条且标注「**市场 Beta，无法分离**」；`CF006` UNRESOLVED | ✅ **完整（最强警告）** |
| **007** | 有（2025-10-24 / 12-04） | 候选级 PIT note 明写「政策催化主管部门为**工信部/国家航天局**，主题是卫星通信/商业航天产业发展，**不是国防采购订单**；**不得把这些产业政策直接当作军工订单证据**」 | ✅ **完整** |

**结论**：**7/7 候选的 Beta / 市场侧 caveat 完整**，且 **`N007` 显式提出「R01-05 与 R01-06 的 Beta 判据应保持一致」**（跨任务治理项，见 §K）。

**明确区分**（用户要求）：
> **本包未把「市场上涨」等同于「军工独立结构已成立」。** 证据：
> - 001 有上涨但明确标注 Beta 未分离；
> - 006 有巨大上涨（+117.36%）但被本包自己标为 **Beta 投射嫌疑**；
> - 002 有事件链但**无市场上涨证据**，本包仍如实提交并标注缺口；
> - 2022 年预算增长 + 板块下跌（E042）作为**反向对照**贯穿全包。

---

## F. 时间结构（启动 → 主题形成 → 扩散/加速 → 高确认 → 降温/结束）

### F.1 Worker 已声明的缺口 —— 逐条核对（**全部属实**）

| Worker 声明 | 核对结果 |
|---|---|
| 2020-08 中旬 ~ 12 月区间数据缺失 | ✅ `lifecycle` 中 RETRACEMENT 直接从 2021-01-08 起，2020-08-10~2021-01-07 **确实留空**，未填充 |
| 2019 南北船行情涨幅/峰值缺失 | ✅ `002.date_candidates.peak` = `PHASE_WINDOW`（无具体日期），`MAIN_RISE.end` = `null` |
| 2017 年 2 月后走势不可考 | ✅ `005` 的 `UNKNOWN` 段 `start=null, end=null`，`date_candidates.end` = `UNKNOWN` |
| 2015 起止日期不可考 | ✅ `006` 的 `MAIN_RISE.start` = `null`；`end` = `PHASE_WINDOW` |
| 2025 阅兵后走势缺失 | ✅ `004` 的 `UNKNOWN` 段自 2025-09-03 起、`end=null`；`date_candidates.end` = `PHASE_WINDOW` |
| 商业航天是否结束未知 | ✅ `007` 的 `end` = `UNKNOWN`；`UNKNOWN` 段自 2025-12-31 起 |
| 2016 完全空缺 | ✅ `exclusion X009`（`INSUFFICIENT_EVIDENCE`），无任何 2016 证据 |

**`lifecycle` 覆盖年份**：2015 / 2017 / 2019 / 2020 / 2021 / 2022 / 2024 / 2025 ——
**2016 / 2018 / 2023 无 lifecycle**，均已在 `exclusions` 中逐条说明理由（X009 / X002 / X006）✓

### F.2 精度纪律核查

- **`date_precision` 使用**：`EXACT_DATE` / `DATE_WINDOW` / `PHASE_WINDOW` / `UNKNOWN` —— **无一处把缺失日期伪造成精确日期** ✓
- **`alternative_dates` 使用**：001（peak cluster 2 个口径）、002（10-25 vs 11-26）、005（1-04 vs 1-09）、007（10-24 vs 11-30）—— **保留双口径，不自动取舍** ✓
- **`conflict_note`**：几乎每条 `date_candidate` 都写明口径分歧，含 `★` 级警告（如 001 的 Beta、004 的「**不得以阅兵结束直接推断 Campaign 结束**」）✓
- **4 条 evidence 缺 `event_date`**（`E008 / E017 / E037 / E038`）但标 `contemporaneous` —— Schema **允许** `event_date` 缺省；导入 DB 后 `evidences.date = NULL`。**属轻微时间信息损失，已记录，非阻塞**。

**结论**：**时间结构处理符合「资料不足时保持 UNKNOWN / PHASE_WINDOW，不制造精确日期」的要求** ✓

---

## G. 9 个 Conflict 的优先级（**全部保留，未消解**）

**resolution 分布**：`UNRESOLVED` 6 · `KEEP_BOTH` 2 · `RESOLVED_PREFERRED` 1（`CF003` 倾向 Sub-theme，**但仍保留第二种立场**）
**position 数**：2 / 2 / 2 / 3 / 2 / 2 / 2 / 2 / 2 —— **全部 ≥ 2**（Schema `minItems: 2`）✓

| 优先级 | conflict | 主题 | 为什么是这个优先级 |
|---|---|---|---|
| **P0** | **`CF008`** | **军费/国防预算增长 → 装备订单兑现的传导与时滞** | **决定整条「军费→订单→业绩→市场」证据链是否合法**。本包已用 `E042` 作反向对照；若不裁决，001 的政策层证据无法定性 |
| **P0** | **`CF001`** | **2020H2 与 2021 是否为同一 Campaign** | 直接决定 **001 是否拆分**，进而决定生命周期、`peak`、`end` 与持续性。**本包已显式声明「若采信拆分立场，001 应拆为两个候选，各自持续性需重新论证」** |
| **P0** | **`CF004`** | **商业航天/卫星互联网的族属（军工 vs 信息通信 vs 跨族）** | 决定 **007 是否留在军工族** —— **族属未定前 007 不应进入 canonical**；且涉及与 R01-02 / 信息通信的 cross-task dedupe |
| **P0** | **`CF006`** | **2015 军工是独立 Campaign 还是杠杆牛 Beta 投射** | 决定 **006 的存废**。本包已按 `historical_campaign_validation_v1.md §4.3` 自降为 low 并声明「若 Beta 无法排除应降级 OBSERVATION_ONLY」 |
| **P1** | `CF002` | 2019 南北船（002）与 2019 阅兵（003）是否同一 Campaign | 决定 002/003 是否合并（MERGE）；**关键阻塞是 2019-07~09 连续行情数据缺失** |
| **P1** | `CF007` | 2025 阅兵行情是 `theme_campaign` 还是 `event_driven`（持续性） | 决定 **004 的 classification 与是否降级**；也影响 003 的同类判据 |
| **P1** | `CF003` | 军工电子在 2020–2021 是 Sub-theme 还是独立 Campaign | 影响 001 的内部结构（本包倾向 Sub-theme，已记 `X004`）；涉及与 R01-02 的 dedupe |
| **P2** | `CF005` | 船舶制造：民船周期 vs 军品订单 | **已由 `X005` + `N005`（HANDOFF）处理** —— 本包未建民船周期候选，**低风险**。但**与 T01 的既定归属存在张力**（见 §H） |
| **P2** | `CF009` | 2017「军民融合」与「军工混改」是否同一机制 | 影响 005 的内部结构，**不影响 005 的存废**；本包已合并提交并显式记录分歧 |

> **9 条全部保留、一条未消解** ✓ · **未为「解决 Conflict」而强行做确定结论** ✓

---

## H. `Commercial Space` / `军工电子` 等边界是否清晰

| 边界 | 处理 | 判定 |
|---|---|---|
| **军工电子 ↔ 半导体** | `X004`（判为 001 内部 Sub-theme，**未单独建 Campaign**）+ `CF003` + `N002`（BOUNDARY → R01-02）+ `Q006` | ✅ **清晰**（判据 + 跨任务移交 + 研究问题三层齐备）。**与 T01 一致**：T01 已将 `军工电子` 设为 `国防军工` 下的 `concept` |
| **商业航天 ↔ 信息通信** | `X008`（OUT_OF_SCOPE 通信属性）+ `CF004`（3 position）+ `N004`（POSSIBLE_DUPLICATE）+ `Q007` | ⚠️ **刻意不清晰（保留）** —— 本包明写「**不预设全部归入国防军工**」「**提交本候选的主要目的是把边界争议显式化**」。**这是正确的做法**，但意味着 **007 的族属必须由 Canonical Decision 裁决** |
| **船舶制造：民船周期 ↔ 军品订单** | `X005`（机制切分）+ `CF005` + `N005`（HANDOFF）+ `Q` 相关 | ✅ **清晰**（机制切分明确：民船周期机制属周期族，本包不重复建候选） |
| **军民两用装备 ↔ 高端装备** | `N001`（BOUNDARY → R01-01）+ 按「驱动来自军费与军品采购」为归属判据 | ✅ **清晰** |
| **军工新材料 ↔ 化工** | `X007`（OUT_OF_SCOPE → R01-03）+ `N003` | ✅ **清晰** |
| **地缘事件 ↔ 军工产业周期** | `X001`（2022 佩洛西 → OBSERVATION_ONLY）+ `N006` + `E041` | ✅ **清晰**，且给出了边界判据：「**地缘事件本身不构成 Campaign，只有当事件转化为可观察的采购/订单/产能变化时，才考虑纳入军工机制链条**」 |
| **军民融合（作为 root？）** | `X012`（NOT_INDEPENDENT_MACRO_THEME）+ `MT007`（CROSS_FAMILY） | ✅ **清晰**（不升格为 Macro Theme，作为 CROSS_FAMILY / Mechanism 表达） |

### H.1 与 T01 的一处**张力**（需在 Canonicalization 注意）

- **T01 §E 已明确**：「`船舶制造` 归 `国防军工`（军民两用，**含民用造船周期**），**不归「高端装备」**」；
- **R01-06 的 `X005`**：把「民船订单 / 船价周期（2021–2024）」判为**机制不同**并 **HANDOFF 给 R01-03 / R01-01 评估**；
- **性质**：**不构成直接冲突** —— T01 规定的是 **theme 归属**（`船舶制造` 主题仍在 `国防军工` 下），R01-06 处理的是 **mechanism 切分**（民船周期不并入 002）。但**同一主题下「哪些结构算军工」**的判据需要在 Canonicalization 显式对齐，否则会出现「主题属军工、结构属周期族」的口径分叉。
- **本轮判定**：**记录，不裁决**（属 Canonical Decision 职责）。

---

## I. `research_report` Tier 冲突 —— **实证核查**

### I.1 用户要求核查的 5 项 —— 逐项结论

**① Research Model v1.0 §15 的实际定义**
```text
Tier 1 | 交易所 / 监管机构 / 政府 / 公司正式公告 / 财报
Tier 2 | 中国证券报 / 证券时报 / 第一财经 / 财联社 / 界面 / 新华社 / 权威行业协会
Tier 3 | 券商研报 / 研究机构 / 专业财经网站      ← ★ 券商研报 = Tier 3
Tier 4 | 雪球 / 自媒体 / 论坛 / 博客 / 社交媒体
约束：`source_type` 与 `tier` 不得矛盾
```
→ **券商研报 = Tier 3**（`research/research/methodology/research_model_v1_0.md` 第 283 行）✓

**② 当前 Validator C08 的实际映射**
```python
SOURCE_TYPE_TIER = {
    "exchange": (1,), "regulator": (1,), "company_announcement": (1,),
    "industry_association": (1, 2),
    "research_report": (2,),        ← ★ 只允许 Tier 2
    "media_tier2": (2,), "media_tier3": (3,), "media_tier4": (4,),
    "website": (2, 3, 4), "forum_blog": (4,), "social_media": (4,),
    "other": (1, 2, 3, 4),
}
```
→ **`research_report` → Tier 2 only** ✓ · C08 在 `tier not in SOURCE_TYPE_TIER[st]` 时 `rep.fail("C08", ...)`

**③ 当前 Protocol / Schema 是否存在相关约束**
- **Protocol §7.3**（来源分级，4 档）：Tier 1 官方 / Tier 2 **权威媒体 / 行业协会 / 产业原始数据** / Tier 3 **财经媒体转述 / 一般报道** / Tier 4 论坛博客 —— **★ 完全没有提及「券商研报」**；并规定「`source_type` 与 `tier` 不得矛盾（沿用 `historical_campaign_validation_v1.md` §1.2）」
- **`historical_campaign_validation_v1.md` §1.2**（**只有 3 档**）：Tier 1 官方公告/政府文件/财报 · Tier 2 权威媒体/行业协会数据 · **Tier 3 市场传闻/社交媒体/自媒体** —— **★ 同样未提及券商研报**，且 Tier 3 的定义与另两份**语义完全不同**
- **Schema**：`source_type` 枚举为 **tier 内嵌式**（`media_tier2` / `media_tier3` / `media_tier4` + `research_report` / `website` / `other` 等），**未定义 `source_type ↔ tier` 的映射表** → 映射只存在于 Validator C08

**④ R01-06 Package 是否真正符合当前有效规则**
- **符合** ✓：全包 `source_type × tier` 组合经 C08 校验**全部通过**（`regulator→1` ×4、`company_announcement→1` ×1、`media_tier2→2` ×10、`website→2/3` ×3、`media_tier3→3` ×19）；
- **但方式值得注意**：**全包 `source_type = research_report` 的数量 = 0** —— 9 条 `evidence_type = 券商研报` 全部映射为 **`media_tier3` + `tier 3`**。

**⑤ `media_tier3 + tier 3` 是否会产生其他语义问题 → 会产生两类**

| 类型 | 具体 | 影响 |
|---|---|---|
| **① 语义损失（真实存在）** | `R01-MIL-S027`（**国盛证券（研报PDF）**）与 `R01-MIL-S033`（**国盛证券（研报PDF）**）是**券商研报原文 PDF**，被标为 `media_tier3` —— 而 `research_report` 枚举值**正是为它们设计的**。把它们称作「媒体（Tier 3）」是**字段语义错位** | **可追溯性未受损**（`title` / `url` / `publisher` 完整记录了「国盛证券（研报PDF）」）；但**按 `source_type` 做统计/筛选时会失真** |
| **② 规避而非解决** | 因 `research_report` 被 C08 锁定为 Tier 2，而 Research Model 要求 Tier 3 → **Worker 选择绕开该枚举值**。结果：**R01-06 的 C08 校验从未行使 `research_report` 分支**，冲突被**隐藏**而非**解决** | 若后续某包**诚实使用** `research_report + tier 3`，**C08 会 FAIL** —— 冲突依然存在 |

### I.2 冲突定性 → **是真实的口径冲突，不是 Worker 对字段映射的误读**

**判定依据（三方不一致，且与 Worker 描述吻合）**：

| 文档 | 券商研报的 tier | 档位数 |
|---|---|---|
| `research_model_v1_0.md` §15 | **Tier 3** | 4 |
| `HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md` §7.3 | **未定义** | 4 |
| `historical_campaign_validation_v1.md` §1.2 | **未定义** | **3** |
| Validator `SOURCE_TYPE_TIER` | **Tier 2（唯一）** | — |

→ **Worker 的表述（「Validator → Tier 2 / Research Model §15 → Tier 3 / 两者不得矛盾」）经实证核查成立** ✓
→ **不是误读** ✓

**与既有记录的关系**：
- 这是 **R01-03 的 `H1`** 与 **R01-05 的 `K` 系列**同一问题的**第三次复现**；
- **同一系统性问题** → **标记为 `Cross-task governance issue`，待所有 R01 任务完成后统一处理**（见 §K）✓
- **本轮未修改 Research Model v1.0 / Protocol / Schema / Validator** ✓

---

## J. 是否建议进入 R01-06 Canonicalization → **建议进入，但须先完成 4 项 P0 裁决**

**建议**：
1. **Package 可以正式进入 R01-06 Canonicalization**（Intake PASS，C25 PASS，结构完整）；
2. **但 Canonical Decision 必须先裁决 `CF008` / `CF001` / `CF004` / `CF006` 四项 P0**，再进入 DB Import；
3. **`004` 与 `007` 的处置取决于 P0 裁决结果** —— 若 `CF004` 判为跨族或属信息通信，007 不应进入军工 canonical；若 `CF007` 判为 event_driven 且持续性不足，004 应降级；
4. **`003` / `006` 建议保持 Research Only**（详见 §C.3）；
5. **`005` 建议先补证**（生命周期未闭合）；
6. **`E042` 的绑定与 `temporal_relation` 须在 Canonicalization 处理**（避免 DB 层 `evidence-temporal-mislabel`，见 §D.2）。

**预计可进入 canonical 的候选数**：**2–4 个**（001 最稳；002 / 004 / 007 取决于 P0 裁决）。
**★ 本轮不决定最终 Campaign 数量** —— 由 Canonical Decision 走 Research Model v1.0 §5 + Independence Gate Q1–Q5 判定。

---

## K. CMTR v1（**未修改 taxonomy**）

### K.1 解析结果

**DB 当前 11 个 Macro Theme root**（**含 `TH-DEFENSE` 国防军工**）：
`汽车 · 信息通信 · 消费 · 国防军工 · 电子 · 金融 · 高端装备 · 医药健康 · 电力设备 · 房地产 · 资源`

| 对象 | status | 解析根 |
|---|---|---|
| **7/7 候选**（`theme_name_candidates`） | **全部 RESOLVED** | **`国防军工`** |
| `MT001` 国防军工 | RESOLVED | `国防军工` |
| `MT002` 航空装备 | RESOLVED | `国防军工` |
| `MT003` 航天装备 | RESOLVED | `国防军工` |
| `MT004` 船舶制造 | RESOLVED | `国防军工` |
| `MT005` 军工电子 | RESOLVED | `国防军工` |
| `MT006` 装备采购与订单驱动机制（MECHANISM） | **UNRESOLVED_NAME** | — （**正确**，机制轴不是主题） |
| `MT007` 军民融合（CROSS_FAMILY） | **UNRESOLVED_NAME** | — （**正确**，跨族方向不是主题） |

**汇总**：37 个去重名称 → `status = RESOLVED` → **根 = `国防军工`**；`has_taxonomy_gap = True`（因存在未解析的机制/跨族名称，**属预期**）。

**未解析名称（32 个，全部为别名或机制词，非阻塞）**：
`主机厂 · 兵器装备 · 军品订单 · 军工 · 军工元器件 · 军工改革 · 军工混改 · 军工行业 · 军工集团改革 · 军民融合 · 军用电子 · 军贸 · 军转民 · 卫星互联网 · 卫星导航 · 商业航天 · 国防军工行业 · 地面兵装 · 大飞机 · 央企重组 · 新质战斗力 · 武器装备列装 · 武器装备采购 · 民参军 · 火箭制造 · 航海装备 · 航空发动机 · 船舶 · 装备采购 · 订单驱动 · 资产证券化 · 阅兵主题`

### K.2 ★ 重要发现：**`国防军工` 及 4 个子主题「已经存在」，Package 的 taxonomy 前提是陈旧的**

**T01（commit `92299e7`，早于 R01-01）已确立**：
- DB `themes` 表 **19 → 52 行**，**Macro Theme root 4 → 11**；
- **新增 `TH-DEFENSE` = 国防军工**，rationale 明确写「**订单 / 事件驱动（原 4 族完全缺失）**」；
- 子树：**`TH-DEFENSE-AIR` 航空装备（industry）· `TH-DEFENSE-SPACE` 航天装备（industry）· `TH-DEFENSE-SHIP` 船舶制造（industry）· `TH-DEFENSE-ELEC` 军工电子（concept）**；
- T01 §E 并已裁定：**航空装备 / 航天装备 / 船舶制造 / 军工电子 不建 root**，归 `国防军工`。

**但 R01-06 Package 的两处表述与事实不符**：

| 位置 | 原文 | 事实 |
|---|---|---|
| `manifest.macro_theme_proposals[MT001].rationale` | 「当前 canonical DB themes 的根节点**仅 4 个**（汽车 / 医药健康 / 信息通信 / 电力设备），**不含军工**」 | **实际 11 个根**，且**已含 `国防军工`** |
| `exclusions[X011].rationale` | 「DB themes 当前**仅有 4 个根节点**：汽车/医药健康/信息通信/电力设备」 | 同上 |

**根因推断**：Worker 的 `manifest` 引用了 `KNOWN_TAXONOMY_AND_OVERLAP_NOTES §2` —— 该文件**不在本仓库中**（`grep` 全仓仅命中 R01-06 自身的 manifest / exclusions 与本会话记忆文件），**属 Worker Workspace 材料**，其内容**早于 T01**。

**影响评估**：
- **不阻塞**：`MT001~MT005` 全部解析为**已存在的根**，**结论正确**；7/7 候选的 `macro_theme_proposal = 国防军工` 解析正确；Worker **未创建任何 `TH-*` ID**、**未修改 taxonomy** ✓（符合 `forbidden_actions`）；
- **但须记录**：若 Canonicalization 机械采信 `NEW_MACRO_CANDIDATE`，**会造成重复根节点**；
- **处置建议**：`MT001~MT005` **视为「已满足，无需新增」**；`MT006`（MECHANISM）/ `MT007`（CROSS_FAMILY）**维持不升格为 root**（与 T01 一致）。

### K.3 taxonomy gap 结论

**无阻塞性 taxonomy gap** ✓ —— 7/7 候选全部解析到既有根 `国防军工`；
`MT006` / `MT007` 的 UNRESOLVED 是**正确**的（机制轴 / 跨族方向本就不应成为 Macro Theme）；
32 个未解析名称均为**别名或机制词**（`军工` / `船舶` / `阅兵主题` / `订单驱动` 等），**属别名缺口，非结构性 gap**。

---

## L. 最终结论 A–K

| | 项 | 结论 |
|---|---|---|
| **A** | **Package 是否通过 Intake** | ✅ **PASS**（C01–C25 = 0 FAIL / 0 WARN；checksums 10/10；0 悬空；0 孤儿；0 共享；0 canonical ID 泄漏；§7.4 三条规则 0 违规） |
| **B** | **C25 Strict Draft-07** | ✅ **PASS · 0 违规**（`additionalProperties:false` 全面生效；candidate 无 `source_ids` 属正确） |
| **C** | **7 个 Candidate 是否具备 Canonicalization 条件** | **D 可进入 = 4**（`001` 最强 / `002` / `004` / `007` 各有前置条件）· **E1 需补证 = 1**（`005`）· **E2 Research Only = 2**（`003` / `006`） |
| **D** | **Research Only / 补证** | `003`（全 retrospective + 4 周持续性）· `006`（Beta 不可分离 + 无订单/业绩证据）→ **Research Only**；`005`（生命周期未闭合 + 政策文本驱动无兑现证据）→ **需补证** |
| **E** | **9 个 Conflict 优先级** | **P0 = `CF008` `CF001` `CF004` `CF006`** · **P1 = `CF002` `CF007` `CF003`** · **P2 = `CF005` `CF009`** —— **全部保留，一条未消解** |
| **F** | **`E042` 等关键反向证据是否正确保留** | ✅ **是**（`high` + `primary_source` + `description` 显式反证 + `CF008` + `coverage §7` + `001.drivers.ending` 四处一致保留，**未被弱化**）。**但两处待 Canonicalization 处理**：`role = context`（全包 `contradicting = 0`）；绑定到 `006`（2015）会触发 DB 层 `evidence-temporal-mislabel` |
| **G** | **Beta / 市场侧证据 caveat 是否完整** | ✅ **7/7 完整**（001 明写「不宣称已分离」；006 明写「无法证明不是 Beta 投射」；002 如实空白；004 如实薄弱；007 明写「不得当作军工订单证据」）。**明确未把「市场上涨」等同于「军工独立结构成立」** |
| **H** | **Commercial Space / 军工电子等边界是否清晰** | **军工电子 ✅ 清晰**（`X004`+`CF003`+`N002`+`Q006`，与 T01 一致）· **商业航天 ⚠️ 刻意保留不清晰**（`CF004` 3 position + `X008` + `N004`，**族属必须由 Canonical Decision 裁决**）· **船舶 ✅ 清晰**（`X005`+`CF005`+`N005`，但与 T01 的归属存在**张力**，需对齐）· **军民融合 ✅ 清晰**（`X012`+`MT007`，不升 root） |
| **I** | **`research_report` Tier 冲突是否真实存在** | ✅ **真实存在**（**不是误读**）：Research Model §15 = Tier 3 / Protocol §7.3 **未定义** / `historical_campaign_validation_v1.md` §1.2 **未定义且只有 3 档** / Validator C08 = **Tier 2 only**。Worker 的 `media_tier3 + tier 3` **通过校验但造成语义损失**（2 条国盛证券研报 PDF 被标为媒体）且**规避而非解决**。**与 R01-03 `H1` / R01-05 `K` 系列同源** → **Cross-task governance issue** |
| **J** | **是否建议进入 R01-06 Canonicalization** | ✅ **建议进入**，但**必须先裁决 4 项 P0**；`004`/`007` 的处置取决于 P0 结果；`003`/`006` 建议 Research Only；`005` 建议先补证。**本轮不决定最终 Campaign 数量** |
| **K** | **是否存在需统一治理的跨任务问题** | ✅ **存在 4 项**（见下） |

### K-1. 需要统一治理的跨任务问题（**待所有 R01 任务完成后统一处理**）

| # | 问题 | 证据 / 来源 | 处置 |
|---|---|---|---|
| **1** | **Source Tier 口径三方不一致** | `research_model_v1_0.md` §15（4 档，研报=T3）· `INTAKE_PROTOCOL_v0_1.md` §7.3（4 档，**未定义研报**）· `historical_campaign_validation_v1.md` §1.2（**3 档**，T3=市场传闻/自媒体）· Validator `SOURCE_TYPE_TIER['research_report'] = (2,)` | **Cross-task governance issue** —— 与 R01-03 `H1`、R01-05 `K` 系列**同一问题第三次复现**。**本轮只确认与记录，未改 Research Model / Protocol / Schema / Validator** |
| **2** | **Worker 侧 taxonomy 快照陈旧** | R01-06 manifest / `X011` 认为 root 仅 4 个；实际 T01 后为 11 个且已含 `国防军工` | **需向后续 Worker 提供 T01 之后的 taxonomy 快照**（`KNOWN_TAXONOMY_AND_OVERLAP_NOTES` 不在本仓库，无法核验其版本） |
| **3** | **跨任务「市场关注」口径差异未统一** | R01-03 起更严（必须有 A 股市场侧或强行业/公司证据）vs R01-01/02 较宽 | **仍开放** —— 本轮**未固化为新 Protocol、未回改历史** |
| **4** | **Beta 判据跨任务一致性** | R01-06 `N007` 显式提出「R01-05（金融/地产）与本包的 Beta 判据应保持一致，否则跨族结构比较将不可比」 | **需在 R01 收口时统一** |

### K-2. 其他已记录项（非阻塞）

| # | 项 |
|---|---|
| 1 | `R01-MIL-SEC003`（国证军工指数）**`ticker = null`**（`basis` 已说明「未取得指数代码」）；`SEC002`/`SEC003` 的 `exchange` 填的是**指数编制机构**（申万宏源 / 深圳证券信息有限公司），非交易所 —— **Schema 允许（free string），属字段语义偏松** |
| 2 | **4 条 evidence 缺 `event_date`**（`E008` / `E017` / `E037` / `E038`）但标 `contemporaneous` → DB 导入后 `evidences.date = NULL`（Schema 允许） |
| 3 | `conflicts[CF004].note` 有笔误：**「★TwoC Agent 应走 CMTR v1 解析」** → 应为 **ThreeC Agent** |
| 4 | **全包 `evidence_role = contradicting` 数量为 0**，而本包核心方法论主张即「军费增长 ≠ 军工行情」→ 建议 Canonicalization 时评估 `E042` 的 role |
| 5 | `001.why_campaign` 表述「≥8 个 independence_group」—— 实际 **14**，**保守正确**（无夸大） |
| 6 | `source.captured_at` / `author` **全部为空**（均为可选字段；与 R01-01~05 一致） |
| 7 | `CF003` 为 `RESOLVED_PREFERRED`（倾向 Sub-theme）但**同时完整保留第二种立场** —— **符合「不得自动取舍」** ✓ |

---

## M. 本轮严格未做

- ❌ 未创建 Canonical Campaign · 未导入 DB · 未修改已有 Campaign / Evidence / Source / Theme / Rule；
- ❌ 未修改 **taxonomy**（`themes` 表 52 行未动）· 未创建任何 `TH-*` / `C-*` / `RC-*` ID；
- ❌ 未修改 **Schema**（`historical_research_intake.schema.json`）· **Protocol**（`HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md`）· **Validator**（`validate_historical_research_intake.py`）· **Research Model v1.0**；
- ❌ 未修改 **R01-06 Package** 的任何文件（含 `checksums.sha256`）；
- ❌ 未刷新 **Structural Analogy** · **Time Observation**；
- ❌ 未启动 **R01-06 Canonicalization**；
- ❌ 未为「解决 Conflict」强行做确定结论；
- ❌ 未把「市场上涨」当作「军工独立结构已成立」；
- ❌ 未因事件重大（2019/2025 阅兵）而默认形成 Campaign。

---

## N. 交付物

| 文件 | 说明 |
|---|---|
| `docs/R01_06_INTAKE_REVIEW_v0_1.md` | 本文件 |
| `docs/PROJECT_STATE.md` | 同步更新（R01 进度 / 实测 / 未决项） |
