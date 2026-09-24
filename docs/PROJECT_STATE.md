# PROJECT_STATE.md — ThreeC 当前真实状态

> 动态接班文档：只回答“现在是什么状态、哪里有问题、下一步做什么”。
> 长期规则见 `AGENTS.md`；未来路线见 `docs/ROADMAP.md`；历史细节见 `docs/CHANGELOG.md`。

- 更新日期：2026-09-24
- branch：`main`
- ahead / behind：`0 / 0`
- working tree：clean
- HEAD：见 `git log -1`（本文件随 **ThreeC 1.0 P0 修复轮** 提交入库）
- **★ 当前阶段：Product / Real Usage Iteration v0.1 → 已通过 Gate T8，待进入 1.0 Deployment**（详见 `docs/ROADMAP.md` §2）
- 最近完成：**Product Stabilization + Real Usage Validation v0.1**（详见 `docs/PRODUCT_REAL_USAGE_BASELINE_v0_1.md`）
  · **阶段 A–C**：**21 项 Product Test Failures → 0**（逐项验证分类：A 旧 universe fixture 18 · C 契约更新 1 · **B 真实缺陷 2**）；
    `npm test` **0 failed / 622 passed（16 files）** · `tsc -b` **PASS** · `vite build` **PASS**
  · **阶段 D/F · P0 修复**：① **Attention Gate 把已结束历史 Campaign 标为「当前值得研究」**（14 个，含 `C-2016-PANEL-CYCLE`）
    → 已修（已记录 `end` ⇒ `HISTORICAL_REFERENCE`），14 → **5**；② **null `start`/`end` 导致 93 处运行时崩溃** → 已修（类型 + null 安全 + `openEnded`）
  · **阶段 G · P1 修复**：Time Observation 移动端详情网格 **3 列 → 2 列**（375px 可读性）
  · **阶段 E**：新增**可重复研究闭环验收夹具** `researchWorkflow.test.tsx`（43 用例）——
    **5 个 Current Candidate 全部走通完整闭环**（今天 → 候选 → 时间/日历 → 生命周期 → 结构对应 → 历史案例 → 证据 → 新研究问题）
  · **阶段 H**：`ROADMAP.md` 主线切换为 **Product / Real Usage Iteration**；Research 标记 **COMPLETE / FROZEN**；
    Coverage Expansion 回到 **FROZEN / DEFERRED**；Backlog 全部降级为 **KNOWN LIMITATION**
- **★ Research Core 基线（FROZEN）**：79 Historical Objects（52 Campaign + 27 RC）· Driver Canonicalization **v0.4** ·
  SA **v0.5**（395 pairs）· TO **v0.2**（内部 0.3）· Driver **v0.4** · Product **已消费最新 SA / TO artifact**
- **Known Limitations（不阻塞推进，详见 ROADMAP §3）**：
  **L5（★ Next Single Goal）** Research export `lifecycle` 映射缺口（**16 / 27 RC 的 export `lifecycle` 为空**，
  而 **intake 全部有**；R01 importers 过滤 `PEAK` 阶段）· L1 剩余 7 项子串冲突（不改变 driver 集合）·
  L2 `driver=MATCH` 仅 1 条 · L3 2 个 cycle 因映射逻辑无 driver · L4 TO `year`/`date` 相差 1 年（5 例）
- 最近完成（续）：**Research Lifecycle Mapping Repair v0.1**（**已闭环上一轮 Next Single Goal**）
  · **根因**：export 的 lifecycle 原来自 `batch_auto_research.py` 中**手写的静态字典**
    `CAMPAIGN_LIFECYCLE` / `CANDIDATE_LIFECYCLE`，**与 intake 解耦** → `CANDIDATE_LIFECYCLE` 只登记 **11/27**；
    已登记条目**丢掉 `UNKNOWN` 段与 open-ended 段**。（DB `campaign_phases` 过滤 `PEAK` 属 **schema 合法约束**，
    但 **DB 不是 export 的来源** → 真正的缺口在 **export 装配层**）
  · **修复**：新增 `research/scripts/build_lifecycle_from_intake_v0_1.py`，**从 R01 intake 包派生** export lifecycle
    （**单一真源**），并在 `batch_auto_research.py` 中 **intake 优先**（静态字典仅作 pre-R01 回退）
  · **数据前后**：RC lifecycle **11/27 → 23/27**；lifecycle 段 **187 → 243**；**PEAK 22 → 46**；
    **UNKNOWN 未被伪装**（4 个仅含 UNKNOWN 的 RC 保持空，语义由 `research_status = INSUFFICIENT` 承载）
  · **SA**：**v0.4 → v0.5**（60 条变化，**全部仅 lifecycle 维度**：`COMPARISON_POINT_UNKNOWN → MATCH/PARTIAL/MISMATCH`；
    **structural_status 变化 0**；SUPPORTED 4 / STRICT 1 不变；`driver=MISMATCH → PARTIAL` 仍为 0）
  · **Driver v0.4 保持不变**（输入未变，`--check` PASS）· **TO v0.2 保持不变**（输出未变，`--check` PASS）
  · 新增 **lifecycle 覆盖恒等校验器** `validate_lifecycle_coverage_v0_1.py`（L1–L8，**防回归**）
- 最近完成（续）：**ThreeC 1.0 Release Definition + Release Gap Audit**（详见 `docs/THREEC_1_0_RELEASE_DEFINITION.md`）
  · 正式建立 **1.0 定义**（8 个硬 Gate：R / P / T / Q / U / M / D / G）与 **Blocker 分级（P0/P1/P2）**
  · **Gap**：Research / Product / Quality / Documentation **PASS**；Mobile **PASS（静态）**；
    Real Usage **PASS（含 1 项已知缺口）**；**Trust ★ FAIL（P0-1）**；**Deployment ★ P1-1**
  · **P0-1**：无 research lifecycle 的对象在 Product 中被推导出 `main_rise`（`historicalCase.ts:243` 读 adapter 派生的
    `c.phases`；`derivePhases` 在 `peak == null` 时**无条件**返回 `main_rise`）→ 违反 Gate T8 `UNKNOWN ≠ 自动推导具体阶段`
  · **P1-1**：**无任何部署配置 / 无 git tag / 无访问入口 / 无回滚定义**（`package.json` 仍为 `0.1.0`）；
    最小静态部署方案已设计（见定义文档 §2），**未引入后端**
  · **4 个仅 UNKNOWN lifecycle 的 RC 判定为 `KNOWN DATA LIMITATION`，不是 1.0 Blocker**（来源明确 · 无伪造 ·
    Product 可显示信息不足 · validator L4 防静默丢失）
- **Next Single Goal**：**进入 ThreeC 1.0 Deployment / Release Engineering** —— 处理 **P1-1**
  （最小静态部署 + 重建流程 + 回滚定义 + 访问入口）。**本轮不设 `1.0.0`、不打 tag、不部署。**

### 最近完成：**ThreeC 1.0 P0 修复轮 —— Gate T8 / P0-1（含审计新发现 P0-1c / P0-1d）**

> **结果：Gate T 由 ★ FAIL → PASS；P0 清单清零（0 项）；**全 8 个 Gate 中 T/Q/U 已 PASS**。
> 本轮为**纯 Product 语义修复**，`research/` · `exports/` · `contracts/` · `schema.sql` **零改动**。

- **P0-1（原判 P0）**：`historicalCase.ts` 的 `lifecycle` 改为读 **Research `c.lifecycle`**（空则 `[]`），
  **不再回退** adapter 派生的 `c.phases`；`researchAttention.ts::terminalPhaseOf` **删除 `c.phases` 回退**
  → 无 Research lifecycle 时返回 `UNKNOWN`。**P0-1b** 伴生误导注释同步改写。
  · **实证**：4 个仅 UNKNOWN 的 RC（`RC-2019-RE-EASING` / `RC-2020-FIN-BROKER-VOLUME` /
    `RC-2016-RE-SHANTY` / `RC-2015-FIN-LEVERAGE`）修复前一律显示「主升 `main_rise`」/ `EXPANSION`，
    修复后 **`lifecycle = []` / `UNKNOWN`**；虚构计数 **4 → 0**（两个函数各自 4 → 0）。
  · **`derivePhases()` 与 `c.phases` 完整保留**（Timeline 视觉分段仍依赖；4 个 RC 的 `phases` 均在）。
- **P0-1c（★ 本轮审计新发现，同属 Gate T8 家族）**：`STAGE_TO_PHASE` **漏映射 `ENDED`**
  —— `ENDED` 是 Contract `VALID_LIFECYCLE_STAGE` 成员且在当前 export 中出现 **2 次**，
  漏映射使 `phaseOfStage('ENDED')` **静默退化为 `UNKNOWN`**（`UNKNOWN ≠ 未映射`：前者是研究未判定，
  后者是 Product 没接上 → **低估研究结论**）。受影响对象 `C-2019-MIL-GROUP-RESTRUCTURE` /
  `C-2020-RE-DEBT-RISK` 由 `UNKNOWN` **纠正为 `END`**。已补映射，并新增
  `CONTRACT_LIFECYCLE_STAGES`（11 项全量）与 F7/F8/F9 覆盖度不变量。
- **P0-1d（★ 本轮审计新发现）**：`ExportLifecycleStageV1.start/end` 类型曾写死为 `string`，
  但 Contract 明确 `start`/`end` **可为 null**（开放区间；`is_iso_date(None) == True`）
  → 5 个消费点存在 `null` 运行时风险（`terminalPhaseOf` 排序、`peakWindowOf`、`stageSegmentOf`、
  `historicalPhasesInWindow`、`CampaignDetail` 旧字段区）。**全部显式处理开放区间，不猜测端点。**
  `tsc -b` 由 **12 error → 0 error**。
- **P0-1e（本轮 UI 审计新发现）**：`CampaignDetail` 存在 **第二处独立 `m.phases` 渲染路径**
  （旧 `历史行情` 字段区），与 `historicalCaseOf` 无关但同样虚构「主升」→ 已改读 Research `lifecycle`，
  空则**整区不渲染**。
- **Gate U 正式化**：D3 由 `it.fails`（KNOWN GAP）**正式化为 `it(...)` 正常断言**；
  新增 **D3b**（UI「生命周期」字段区不得出现具体阶段名）与 **Scenario F1–F9**（Gate T8 全局不变量，
  含 **F3 反向非空断言** —— 证明修复不是靠「一律返回空」蒙过、**F5** 证明 `phases` 未被删除）。
- **验证链**：`npm test` **654 passed / 0 failed（17 files）**（643 → 654）· `tsc -b` **0 error** ·
  `vite build` **PASS** · `researchWorkflow.test.tsx` 5/5 Candidate 闭环仍全通 · 无 runtime crash。
- **本轮未做**：未改 `research/` / `exports/` / `contracts/` / `schema.sql` / SA v0.5 / Driver v0.4 / TO v0.2 /
  lifecycle 映射规则 / Historical Universe；未设 `1.0.0`、未打 tag、未部署、未引入托管。

## 1. 项目当前定位

**ThreeC = A股历史机会时间轴 / 历史机会地图。**

核心价值：

> 从历史周期里找结构，而不是从历史数据里找同名主题。

主链路：

`今天 → 历史同期 → 历史周期阶段 → 当前研究对象 → 历史结构对应 → 为什么对应 / 哪里不同 → 继续研究`

不是交易决策、预测、买卖信号、概率或推荐系统。

## 2. 当前总阶段

### Research Core：第一版闭环完成

`Historical Model → Historical Data → Time Observation → Current Research → Structural Analogy`

当前已完成：
- Structural Analogy Rule Set v0.2 冻结
- Structural Analogy Research v0.2 baseline
- Structural Analogy Explanation Artifact v0.2
- Product Similarity Architecture Gate v0.1 — PASS
- Product Adapter v0.1（Structural Analogy Artifact → Product View Model）
- Time Observation v0.5
- CMTR v1
- Historical Driver Canonicalization
- Robustness / Feasibility / Readiness

### Product Core：闭环已成立，并已具备可重复的研究更新循环

```
Current Time → Current Candidate → Structural Analogy → Historical Case
             → Historical Cycle Map → Current Research Refresh Loop
```

**已完成**：Product Similarity Architecture Gate v0.1（PASS）· Product Adapter v0.1 ·
Product UI Integration v0.1 · UX Review + Performance Gate v0.1（PASS）·
Historical Case Experience v0.1（PASS）· Historical Cycle Map v0.1（PASS）·
**Current Research Refresh Loop v0.1（PASS）**。

当前 Product 主线：

`Timeline → Current Time Lens → Lifecycle Lens → Calendar Lens`

Current Candidate 已进入 Current Time Lens。

Structural Analogy 已通过 Adapter 接入 Current Candidate / Current Time Lens。UI Integration v0.1 已完成。

## 3. Structural Analogy 当前基线

Research v0.2：
- 5 Current Candidates
- 17 Historical Cycles
- 85 comparison pairs
- STRICT_STRUCTURAL_SUPPORTED = 1
- STRUCTURAL_SUPPORTED = 4
- STRUCTURAL_PARTIAL = 36
- THEME_ONLY = 3
- INSUFFICIENT_EVIDENCE = 5
- NO_VALID_CORRESPONDENCE = 37

规则版本：

`structural-analogy-ruleset-v0.2`

最大瓶颈仍是机制级 Driver 证据深度，不是规则或 vocabulary。

## 4. Product-facing Artifact 与 Adapter

已新增：
- `docs/STRUCTURAL_ANALOGY_EXPLANATION_ARTIFACT_v0_1.md`
- `research/research/reports/structural_analogy_explanations_v0_1.json`
- `research/scripts/build_structural_analogy_explanation_v0_1.py`
- `research/research/reports/structural_analogy_explanations_v0_2.json`
- `research/scripts/build_structural_analogy_explanation_v0_2.py`
- `src/data/timeline/structuralAnalogy.ts`
- `src/data/timeline/__tests__/structuralAnalogy.test.ts`
- `src/components/CurrentTimeLens/StructuralAnalogySection.tsx`
- `src/components/CurrentTimeLens/__tests__/structuralAnalogySection.test.tsx`

Artifact 覆盖 85 explanations，且：
- 来源唯一 = Structural Analogy Research v0.2
- 规则唯一 = Rule Set v0.2
- Product READ_ONLY
- 无 score / ranking / probability
- `--check` 可逐字节复现

**v0.2 已通过 Architecture Gate；Adapter v0.1 已消费该契约。**
1. `why_not_similar` 不应把 CROSS_MACRO_THEME 当成“为什么不相似”。
2. explanations 当前按 structural status 再按 cycle id 排列；虽然不是研究 ranking，但 Product 很容易把数组顺序误读为排名，应去除这种暗示。
3. `historical_campaign_id` 同时承载 historical campaign 与 Research Candidate，需要在 Adapter 前明确 cycle / campaign identity。
4. provenance 需要明确哪些证据支撑哪个维度，避免 Product 误把候选全部证据理解为每个维度的直接依据。

因此：

> **Explanation Artifact v0.2 是当前 Product Adapter 的 Research-facing 输入；v0.1 只作为历史保留。**

## 5. 当前 Product Architecture Debt

### 三套比较体系

1. `currentSimilarity.ts`
   - Current Candidate × Historical
   - 内部 score / tier
   - 当前 UI 已使用

2. `historicalSimilarPhase.ts`
   - Historical × Historical
   - Lifecycle Lens
   - 内部 score / tier

3. Structural Analogy
   - Current Candidate × Historical Cycle
   - Lifecycle / Mechanism Driver / Evidence Sequence / Event Structure
   - 正式 Research Correspondence
   - 离散状态，不以 score 定义

长期目标：

- Calendar = 时间邻近浏览
- Lifecycle = 生命周期浏览
- Structural Analogy = 正式结构对应

不能长期维护三套“历史相似算法”。

### Driver 双层语义

Product Current Candidate：
- 证据类别：POLICY / INDUSTRY / CAPITAL / SENTIMENT / EXTERNAL

Structural Analogy：
- 驱动机制：POLICY_DRIVEN / INDUSTRY_UPGRADE / TECH_BREAKTHROUGH / …

以后必须明确区分“证据类别”与“驱动机制”。

### OpportunityRadar

`src/components/OpportunityRadar/` 当前不在 `App.tsx` 主流程。

状态：

**LEGACY / DEFER**

不在 Architecture Gate 前删除。

## 6. Time Observation

Time Observation v0.5 已完成并暂时冻结：

- raw candidates = 315
- distinct samples = 139
- independent robust structures = 1
- TOP-01 = N7 / center 06-11 / window 05-27~06-26 / recurrence 5/7
- cross-family robust = 0

不再为了增加 Pattern 数量继续扩容或放宽标准。

## 7. 当前唯一下一目标

# R01 收口 → **SA / TO 刷新**（第一批治理修复已完成，待决定是否刷新）

**已完成（全部 PASS）**：… Product 侧全部轮次 · **R00**（Intake Protocol）· **T01**（taxonomy gap）·
**R01-01 / R01-02 / R01-03 / R01-04 / R01-05 / R01-06 Canonical Import** · **Intake Validator C25**（严格 Draft-07）。

### R01 进度

| task_id | scope | status |
|---|---|---|
| `R01-01` | 高端装备 / 机器人 | ✅ 已导入（+5 campaigns / 2 RC） |
| `R01-02` | 半导体 / 电子 | ✅ 已导入（+8 campaigns / 4 RC） |
| `R01-03` | 资源 / 有色 / 化工 | ✅ 已导入（+6 campaigns / 5 RC） |
| `R01-04` | 消费 | ✅ 已导入（+11 campaigns / 2 RC） |
| `R01-05` | 金融 / 地产 | ✅ 已导入（+7 campaigns / 5 RC） |
| `R01-06` | 军工 | ✅ 已导入（**+2 campaigns / 5 RC**） |

### ★ `governance-gates-v0.1` 已落地（第一批：SA / TO 前置 4 项）

| Gate | 结论 |
|---|---|
| **G1-1 市场侧证据** | **软门槛**（影响 `strength` / `date_confidence`），**非** Campaign 存废硬门槛；**不回溯**。三态：`A_SHARE_MARKET` **48** / `INDUSTRY_COMPANY_ONLY` **4** / `NONE` **0**。4 个仅行业公司证据：`C-2019-MIL-GROUP-RESTRUCTURE` · `C-2018-HIEQ-ROBOT-DOWN` · `C-2016-PANEL-CYCLE`（面板价格属商品）· `C-2020-RES-RAREEARTH`。★ **商品价格 ≠ A 股市场侧证据** |
| **G1-3 Beta Level 0–3** | **L0 = 43 · L1 = 9 · L2 = 0 · L3 = 0**（**未虚构 L2/L3**）。L1 共 9 个：R01-05 的 7 个 + `C-2023-HIEQ-ROBOT-PLUS` + `C-2025-ROBOTAXI`。★ **修正 Review 预估**：`C-2020-MIL-EQUIP-ORDER` 实为 **L0**（只有中证军工指数绝对涨跌，无宽基对比）；已排除伪 L1：`C-2024-SEMI-MEMORY`（绝对指数涨跌）· `C-2020-SEMI-EQUIPMENT`（「超额配售」为发行术语）· `C-2020-RES-LITHIUM`（「同期」对比对象是商品锂价） |
| **G1-5 `result=weak`** | 正式定义 = **行业 / 市场方向为负**（≠ 证据弱 / confidence 低 / 不成立）。`strength` **不得**为 `weak`。全库 `result=weak` **4** 个；**`strength=weak` 违例 1 个 = `C-2019-AD`**（legacy 残留）→ **本轮不修**，由校验器 **V8 持续 WARN**，提出独立修复（→ `strength: medium`，保留 `result: weak`） |
| **G2-1 Peak / End 四态** | EXACT / WINDOW / ALTERNATIVE（非空 `alternative` 表示）/ NULL。实测 peak：EXACT 22 / WINDOW 26 / NULL 4；end：EXACT 16 / WINDOW 30 / NULL 6；带 alternative 13 / 3。**未回填任何新日期**。★ 保留「商品 peak ≠ A 股 peak」（`C-2020-RES-LITHIUM` A股 2021-09-13 vs 商品 2022-11-11） |

**交付**：`docs/R01_GOVERNANCE_GATES_v0_1.md`（规则集，不覆盖冻结基座）·
`research/research/reports/governance_classification_v0_1.json`（机器可读，研究级）·
`research/scripts/build_governance_classification_v0_1.py` · `research/scripts/validate_governance_gates.py`

**★ 重要约束（实测）**：本轮**曾尝试**把 `governance` 加入 `exports/timeline_export_v1.json`，
触发 `validate_timeline_export` 的 **`CAMPAIGN_FIELDS` 严格白名单 FAIL（52 处）** →
在 Export 加字段 **= 事实上的 Contract 变更** → 依「不修改 Export Contract v1.0」**已回退**。
治理分类改由 **SA / TO 直接读取研究级 JSON**（与 `time_observation_patterns_v0_1.json` 同类）。
若确需进 Export，须**独立轮次**加入白名单并升 Contract v1.1。

**未改动（已核验 diff 为空）**：`batch_auto_research.py` · `validate_timeline_export.py` · DB Schema ·
DB 业务数据（campaigns 52 / themes 52 不变）· Intake Packages · Research Model v1.0 · Protocol · CMTR v1 · taxonomy。
**DB warning 仍为 3 条**（未新增）。

> **★ R01 六个任务已全部完成 Canonicalization**（Intake → Canonical Decision → DB Import → Export）。
> **★ Governance Review + 第一批治理修复已完成**。
> **下一步（待决策）**：① 是否执行第二批治理修复（G1-2 / G1-4 / G2-2 / G2-3 / G2-5 / G2-6）
> ② 是否刷新 SA / TO ③ `C-2019-AD` 的 `strength=weak` 独立修复。
> **下一步（待决策）**：是否按 G1 / G2 清单执行治理修复；修复完成后再刷新 SA / TO。
> **★ 建议顺序**：① G1-1 / G1-3 / G1-5 落地「约定」（改数据）→ 解 SA 阻塞 ② G2-1 Peak/End 四态规范 → 解 TO 阻塞
> ③ 刷新 SA ④ 刷新 TO ⑤ G1-2 / G1-4 / G2-3 / G2-4 / G2-6 按独立轮次处理。

### Governance Issue 分级（R01 Governance Review v0.1）

| 级别 | 数量 | 项 |
|---|---:|---|
| **G0 必须修复** | **0** | 无机械性错误 / 数据损坏 / 契约违规 |
| **G1 应统一** | **5** | G1-1 市场侧证据门槛（软门槛，非硬门槛）· G1-2 `research_report` Tier 向 Research Model §15 对齐 · G1-3 Beta / 相对收益 Level 0–3 分级 · G1-4 Validator 缺 orphan 检查 · G1-5 `result=weak` 语义（残留 `C-2019-AD` 的 `strength=weak`） |
| **G2 建议统一** | **6** | G2-1 Peak/End 四态规范 · G2-2 Theme Cycle Pattern 标注（4 个存疑）· G2-3 `campaign_date_observations` 缺失（5 个 pre-R01）· G2-4 孤儿 source / evidence 处置规范 · G2-5 3 条 temporal warning 定性 · G2-6 taxonomy aliases / Mechanism 登记 |
| **G3 可保持差异** | **4** | promote 率差异（29%~85%）· `campaign_themes.role` 未用 `catalyst` · 8 个未使用 theme · `classification` 分布差异 |

**实测关键数据**：DB↔Export **0 字段不一致** · 共享 evidence **0**（1:1 全库零违规）· rule↔campaign_year↔annual_review **零缺失** ·
taxonomy 未被任何 R01 修改（52 行 / 11 root，**11/11 均有 Campaign**）·
**Beta caveat 覆盖率 pre-R01 0/13 → R01-01 1/5 → R01-02 1/8 → R01-03 1/6 → R01-04 1/11 → R01-05 7/7 → R01-06 2/2**（标准随时间演进，非随机差异）·
`research_report` DB 内 **23 条全 tier=2**（R01-01 7 / R01-02 2 / R01-03 2 / R01-04 2 / R01-05 10 / **R01-06 0**；R01-06 改用 `media_tier3`+T3）·
孤儿 evidence **25**（R01-04 9 / R01-05 4 / R01-06 3 / R01-01 2 / legacy 7）· 孤儿 source **84**（R01-05 22 / R01-03 18 / R01-06 16 / R01-02 11 / R01-01 5 / R01-04 5 / legacy 7）·
**无任何 Campaign 达到 Beta Level 2 / 3**（L1 仅 R01-05 的 7 个 + R01-06 的 `C-2020-MIL-EQUIP-ORDER`）·
**3 条 DB warning 全部来自 R01-02**，属「期末/年度总结类证据」的内容期 vs 发布期口径差，**非数据错误**。

### Historical Universe 当前实测

| 项 | 值 |
|---|---:|
| Macro Theme 根节点 | **11** |
| **有 Campaign 的根节点** | **11 / 11**（汽车 · 医药健康 · 信息通信 · 电力设备 · 高端装备 · 电子 · 资源 · 消费 · 金融 · 房地产 · **国防军工**）★ **全覆盖，无空缺 root** |
| Historical Campaign | **52** |
| Research Candidate（导出层） | 27 |
| 跨族 Campaign 对 | `C(11,2)` = **55** |

**R01-06 新增 2 个 Canonical**：`C-2020-MIL-EQUIP-ORDER`（2020–2022 装备采购/订单景气；17 ev / 14 IG；
唯一具备「军费→订单→基本面→市场」四层可复核链条）· `C-2019-MIL-GROUP-RESTRUCTURE`（2019「南北船」集团战略重组；
**peak = NULL**，市场侧行情证据缺失）。
**5 个 RESEARCH_ONLY**：`RC-2019-MIL-PARADE-70` · `RC-2025-MIL-PARADE-80` · `RC-2017-MIL-MIXED-REFORM` ·
`RC-2015-MIL-REFORM-BULL` · `RC-2024-MIL-COMMERCIAL-SPACE`。
详见 `docs/R01_06_CANONICAL_DECISION_v0_1.md`。

**R01-06 关键裁决**：**`CF008`** 军费→订单传导**存在但不稳定**（2021 时滞约 9 周；**2022 预算 +7.1% 而板块 -23.63%** 为反证）→
**军费层只能作 `context`，不得作为 start 锚点** · **`CF001`** 2020H2 与 2021 **判为一个 Campaign（不拆分）** ·
**`CF004`** 商业航天**族属 UNRESOLVED** → 007 不进入任何族 · **`CF006`** 2015 Beta 不可分离 → 006 Research Only ·
**`E042`** 入 DB 但**不绑定任何 Campaign**（research-level，避免 temporal-mislabel）。

**R01-05 新增 7 个 Canonical**：`C-2022-RE-POLICY-THREE` · `C-2020-RE-DEBT-RISK`（`result = weak`）·
`C-2024-FIN-BROKER-POLICY` · `C-2023-FIN-SOE-VALUATION` · `C-2024-FIN-BANK-DIVIDEND`（peak/end = NULL）·
`C-2020-FIN-BANK-CREDIT` · `C-2025-FIN-INSURANCE`（peak/end = NULL）。
**5 个 RESEARCH_ONLY**：`RC-2024-RE-POLICY-517` · `RC-2019-RE-EASING` · `RC-2020-FIN-BROKER-VOLUME` ·
`RC-2016-RE-SHANTY` · `RC-2015-FIN-LEVERAGE`。
详见 `docs/R01_05_CANONICAL_DECISION_v0_1.md`。

**新增机制轴覆盖**：地产政策周期（融资收紧→风险暴露→政策修复）· **信用周期驱动**（银行顺周期）·
**估值重估/资金配置**（中特估 · 高股息）· **市场风险偏好/流动性**（券商 · 保险资产端）·
**装备采购/订单释放**（含甲方预付款 / 合同负债代理）· **军工集团改革/资产重组**。

**新增 Theme Cycle（7）**：`realestate_policy_cycle_2020_2023`(Sequential) · `bank_valuation_2023_2025`(Parallel) ·
`broker_risk_appetite_2024` · `bank_credit_cycle_2020_2021` · `insurance_asset_liability_2025` ·
`military_equipment_order_cycle_2020_2022` · `military_group_restructure_2019`。

### Structural Analogy / Time Observation

**★★ SA 已至 v0.4 · Time Observation 已至 v0.2（内部 0.3）—— Research Core Release 完成**（2026-09-23）。

**规则集状态**：**`Structural Analogy Rule Set v0.3`（`structural-analogy-ruleset-v0.3`）当前生效**；
v0.2 已被取代（其文本与 Calibration **逐字节保留**）。

**★ E.1 修复效果（`Driver = MISMATCH` 不得进入 `STRUCTURAL_PARTIAL`）**

| 组 | 规则 | driver 数据 | `STRUCTURAL_PARTIAL` | **其中 driver=MISMATCH** |
|---|---|---|---:|---:|
| A | v0.2 | v0.2 | 89 | **50**（= 已发布 SA v0.3 基线） |
| C | **v0.3** | v0.2 | 24 | **0** ✅ |
| D | **v0.3** | v0.3 | **39** | **0** ✅ |

→ **已彻底消除（50 → 0）**，且 **`STRUCTURAL_SUPPORTED` / `STRICT` 完全未变（4 / 1）** —— 未误伤强结构对应。

**★ E.2 词表扩展效果**：有 canonical driver 的 cycle **55 → 60**（**再经 RC driver 缺口修复 → 77 / 79**）· driving `UNKNOWN` **85 → 23**（修复后 86）·
新增覆盖 `C-2019-RES-DYE-SHOCK` / `C-2020-CONS-BEAUTY-CN` / `C-2020-RE-DEBT-RISK` / `C-2022-CONS-SERVICE-REBOUND` / `RC-2019-MIL-PARADE-70` / `RC-2025-MIL-PARADE-80`；
**4 个被点名的 Canonical Campaign 的缺口确认为「纯词表缺口」→ 无需 export 数据补全** ✅

**★ v0.3-r1 修订（2026-09-23，收口审计）**：「**阅兵**」「**纪念大会**」由 `POLICY_DRIVEN` **移至 `EVENT_CATALYST`** ——
原归属为**语义错误**（阅兵是一次性重大纪念活动 = 事件，不改变任何产业规则；且 v0.1 `EVENT_CATALYST` 已含「大会」等同类型活动）。
影响：`RC-2019-MIL-PARADE-70` `['POLICY_DRIVEN']`→`['EVENT_CATALYST']`；`RC-2025-MIL-PARADE-80` `[]`→`['EVENT_CATALYST']`；
`by_canonical_driver`：`POLICY_DRIVEN 58→56` · `EVENT_CATALYST 14→18`；`AMBIGUOUS 2→1`；**有 driver 的 cycle 59→60**。
★ **SA 层结构状态 0 变化**（两 cycle 各有 ≥2 个 `NOT_AVAILABLE` 维度 → 均落 `INSUFFICIENT_EVIDENCE`），
但 **driver 语义已由「资料不足」纠正为「机制不对应」**。

**★ 收口审计发现（`docs/DRIVER_KEYWORD_COLLISION_AUDIT_v0_3.md`）**：
新增词 **133**（声明 134，净新增 131；v0.1 基础 158 → 合并后 289）·
**新增词跨 canonical 重复 = 0** ✅ · 既有遗留跨 canonical 重复 **1**（`结构迁移`，v0.1 起，**不修**）·
**宽关键词风险 37** · **跨 canonical 子串冲突 6 → 5**（~~`扩产/扩产周期`~~ **✅ 已由 v0.3-r2 消除**；剩余 `增长/负增长` · `整治/整治提升` · `出口/出口管制` · `采购/装备采购` · `储备/黄金储备`）·
新增 `AMBIGUOUS` **0** · `DIRECT→DERIVED` **8**（受影响 Campaign 失去唯一 DIRECT 的仅 `C-2025-FIN-INSURANCE`，**不改变任何 SUPPORTED 结论**）·
**52 个 Canonical Campaign 100% 有 canonical driver** ✅ · 19 个无 driver 的 cycle **全部为 RC，未猜测** ✅

**★ v0.2 → v0.3 汇总（99 条变化）**：`PARTIAL 89→39` · `THEME_ONLY 6→9` · `INSUFFICIENT 145→125` · `NO_VALID 151→218` · `SUPPORTED 4→4` · `STRICT 1→1`

**★ 新增语义一致性校验器** `validate_structural_analogy_semantics.py`：**独立重算**（不 import builder 实现）
A/B/C/D **四组 1580 行逐行复核** + 语义不变量 **S1–S14**（含 **S14：`driver=MISMATCH` 的 `PARTIAL` 必须为 0**）。
**结果 PASS（FAIL 0 / WARN 0；1580/1580 一致）**。补齐了 A1–A16 未重算规则语义的缺口。

**★ 新增产物（8 个）**：`structural_analogy_rule_set_v0_3.md` · `structural_analogy_rule_calibration_v0_3.json` ·
`..._calibration_pairs_v0_3.csv`（**long format：395 × 4 = 1580 行**）· `historical_driver_canonicalization_v0_3.json` ·
`historical_driver_evidence_ledger_v0_3.json` · 3 个脚本（含 2 个生成器 + 语义校验器）

**★ SA v0.4 前处理项（全部已闭环）**：
| # | 问题 | 级别 |
|---|---|---|
| ~~1~~ | ~~18 个 Research Candidate 的 export `drivers` 全为空~~ → **✅ 本轮已修复**（18/18 为 `CANDIDATE_DRIVERS` 映射遗漏；9 → 27 条；RC 空 drivers **18 → 0**；有 driver 的 cycle **60 → 77 / 79**）。详见 `docs/RC_EXPORT_DRIVER_GAP_AUDIT_v0_3.md` | **已解除** |
| ~~2~~ | ~~`扩产` vs `扩产周期` 语义自相矛盾~~ → **✅ 本轮已裁决并修复（v0.3-r2）**：`扩产` → **A 保留在 `DEMAND_SURGE`**；`扩产周期` → **D 删除**（零增量覆盖 + 方向错误 + 实际损害）。详见 `docs/KUOCHAN_SEMANTICS_DECISION_v0_3.md` | **已解除** |
| ~~3~~ | ~~剩余 5 项跨 canonical 子串冲突~~ → **✅ 已完成（v0.4）**：3 项删词（`整治提升` / `装备采购` / `黄金储备`）+ 2 项最小上下文消歧（`增长` 否定语境 · `出口` 限制语境）。子串冲突 **10 → 7**；**`E2` driver 效应 = 0 条 Structural Status 变化**。详见 `docs/RESEARCH_CORE_RELEASE_v0_4.md` | **已解除** |
| ~~4~~ | ~~SA v0.3 产物过期~~ → **✅ 已由 SA v0.4 消费**（`structural_analogy_research_v0_4.json` / `..._explanations_v0_4.json`）；v0.3 产物**逐字节保留**作为历史版本 | **已解除** |
| ~~5~~ | ~~E.3 identity 缺陷~~ → **✅ v0.4 已修正**（按来源数组判定：**52 campaign / 27 research_candidate**，identity 错误 = 0） | **已解除** |
| 6 | **E.4**：关键词扩展副作用 —— 8 条 `DIRECT→DERIVED`；`C-2025-FIN-INSURANCE` 失去唯一 DIRECT（**不改变任何 SUPPORTED 结论**） | 轻微 |
| 7 | （观测）2 个 cycle 因**映射逻辑**仍无 canonical driver（`RC-2015-FIN-LEVERAGE` 多命中无消歧 · `RC-2024-SECONDARY` 研究自述强度不足）—— **非数据缺口** | 观测 |

> **★★ Research Core Release 已完成** —— 上表 1~5 全部闭环；SA v0.4 已生成并通过两层独立校验（含 S15 driver 版本一致性）。
> 剩余项见「Known Limitations」，**不再阻塞推进**。
> ★ 数据层（原问题 1）与 `扩产/扩产周期`（原问题 2）**均已不再是阻塞**。

**★ Governance 元数据接入**：`governance-gates-v0.1` 的 `market_evidence_state` / `beta_level` / `peak|end` / `result`
仅进入 `supplementary` / `governance_context`，**不参与 Structural Status**（Rule Set §9）。

**★ SA / TO 输入字段来源（因 Export Contract v1.0 未改）**：治理字段**不在**
`exports/timeline_export_v1.json` 中（加入会触发 `CAMPAIGN_FIELDS` 白名单 FAIL），
SA / TO 须**直接读取** `research/research/reports/governance_classification_v0_1.json`。

**下一步（待决策）**：① export 数据补全（18 RC 的 drivers）② 多命中消歧评估 ③ 修正 E.3（kind metadata）
④ **生成 SA v0.4**（用 Rule Set v0.3 + Canonicalization v0.3）⑤ **Time Observation 刷新**（建议在 SA v0.4 之后）
⑥ 第二批治理修复 ⑦ `C-2019-AD` 的 `strength=weak` 修复。

### 未决与待办（**未排期**）

| 类型 | 项 |
|---|---|
| OPEN | **`CF013` 股息口径差**（个股前复权含股息 vs 沪深300 价格指数不含股息）—— **UNRESOLVED**；已转为**结论约束**（**不得解释为行业 Alpha**、未伪造调整后收益）；需以**中证红利全收益 / 银行行业全收益指数**重算 |
| OPEN | R01-05 保留未决：`CF001`(Q2 标的重叠) · `CF003`(券商全市场 Beta) · `CF004`(红利风格因子) · `CF005`(中特估银行/保险边界) · `CF006`(房地产 vs 金融 Cycle 归属) · `CF008`(2020-07 券商驱动) · `CF009`(KEEP_BOTH) · `CF011`(两龙头方向相反，不允许取平均) · `CF012`(保险代表标的 vs 板块叙事) |
| OPEN | R01-05 生命周期未闭合：`C-2024-FIN-BANK-DIVIDEND` / `C-2025-FIN-INSURANCE` **peak/end = NULL** · `C-2023-FIN-SOE-VALUATION` peak/end 为推断值；`C-2020-FIN-BANK-CREDIT` 仅 4 ev / 4 IG + 单一标的 → **建议后续补证** |
| OPEN | **本地无金融/地产行情序列** → R01-05 的 Export `market_data = unavailable`（相对表现仅引自 intake 一级行情证据） |
| OPEN | **`CF007`**（医美归属：消费 vs 医药健康）保留未裁决 · **`CF005`**（白电驱动归因）保留 · **`CF010`**（补贴 vs 真实需求；**`+11%` vs `-4.3%` 口径冲突完整保留**）· **`CF001`**（白酒 classification）保留 |
| OPEN | **`RC-2020-CONS-SMALL-APPLIANCE`（007）仍需补证**（渗透率一手数据 + 同期证据）· **`RC-2024-CONS-PET-FOOD`（013）保持 Research Only** |
| OPEN | `C-2020-CONS-DUTYFREE` **A 股广度不足**（sec=1）· `C-2023-CONS-VALUE-RETAIL` **start 年度级 + end NULL** · `C-2024-CONS-TRADE-IN` **Beta 未排除** |
| OPEN | **跨任务「市场关注」口径差异未统一**（R01-03 起更严 vs R01-01/02）—— **本轮未固化新 Protocol、未回改历史**；**R01-06 `N007` 另提出「R01-05 与 R01-06 的 Beta 判据应保持一致，否则跨族结构比较不可比」** |
| OPEN | **`美容护理` / `商贸零售` taxonomy 缺口**（`MT006`/`MT007` 提案级未解析）—— 不扩展 |
| OPEN | R01-03 的 `CF003`（锂跨族）· `CF009`（黄金背离）保留未决 |
| OPEN | R01-02 的 3 条 `evidence-temporal-mislabel` 警告（已收口为 caveat） |
| OPEN | **仅剩 1 个 root 无 Campaign：国防军工** —— **R01-06 已导入 2 个 Campaign**（`C-2020-MIL-EQUIP-ORDER` / `C-2019-MIL-GROUP-RESTRUCTURE`）→ **11 个 root 中已有 11 个具备 Campaign**（原「无 Campaign 的 root」问题**已解决**） |
| OPEN | **R01-06 保留未决**：`CF005`（船舶：民船周期 vs 军品订单；**与 T01 的归属张力**待对齐）· `CF009`（2017 军民融合 vs 混改）· `CF004`（商业航天族属 UNRESOLVED）· `CF001`（2020H2/2021 阶段边界，**保留重新评估条件**） |
| OPEN | **R01-06 待处理项**：`E042` 的 `role = context`（全包 `contradicting = 0` → 建议 R01 Governance Review 统一）；4 条 evidence 缺 `event_date`（E008/E017/E037/E038）；`SEC003`（国证军工指数）`ticker = null`；`CF004.note` 笔误「TwoC Agent」；`002.why_not` 交叉引用错误（引 CF004 讨论 classification） |
| OPEN | **R01-06 的 `001` Beta 污染未分离**（2020-07 启动段）· **`002` 市场侧行情证据完全缺失**（`peak = NULL`）· `003/004/005/007` 生命周期未闭合 · `005` 需补证（2017 分月行情 + 混改落地公告） |
| OPEN | **本地无军工行情序列** → R01-06 的 Export `market_data = unavailable`（市场数据仅引自 intake 二手整理，全 T3） |
| OPEN | Validator C08 vs Research Model v1.0 §15 的 `research_report` tier 冲突（**R01-03 `H1` / R01-05 `K` / R01-06 第三次复现** → **Cross-task governance issue，待 R01 Governance Review 统一处理**） |
| OPEN | **✅ 第一批治理修复已完成**（`governance-gates-v0.1`）：G1-1 市场侧证据软门槛 · G1-3 Beta Level 0–3 · G1-5 `result=weak` 语义 · G2-1 Peak/End 四态。**规则 + 机器可读清单 + 校验器已交付，未改任何 Campaign / Schema / Contract / taxonomy** |
| OPEN | **✅ Rule Set v0.2 的 E.1 / E.2 已修复（2026-09-22）**：新建 **Rule Set v0.3**（`Driver=MISMATCH` 不得进入 `STRUCTURAL_PARTIAL`，**50 → 0 彻底消除**）+ **Driver Canonicalization v0.3**（词表扩展，有 driver 的 cycle **55 → 59**）+ **Rule Calibration v0.3** + **语义一致性校验器**（S1–S14，1580/1580 一致）。**未生成 SA v0.4 · 未覆盖 SA v0.3 · 未刷新 TO** |
| CLOSED | **SA v0.4 前置待办 —— ✅ 全部闭环（Research Core Release）**：① 18 个 RC export driver 缺口 ✅ · ② `扩产/扩产周期` ✅ · ③ 剩余 5 项 collision ✅（v0.4：3 删词 + 2 上下文抑制）· ④ SA v0.3 过期 ✅（由 SA v0.4 消费）· ⑤ E.3 identity ✅（52/27）· ⑥ E.4 轻微（保留为已知限制）· ⑦ 2 个 cycle 映射逻辑（保留为已知限制） |
| OPEN | **Time Observation 仍未刷新**（SA 已至 v0.3；建议在 SA v0.4 之后统一刷新） |
| OPEN | **第二批治理修复待决策（本轮未做，仅 issue register）**：G1-2 `research_report` Tier（**须逐条确认是否真属 Research Model §15 的券商研报，不得把 23 条 tier=2 一律改成 tier=3**）· G1-4 Validator 加 C26 orphan report · G2-2 Theme Cycle Pattern · G2-3 5 个 pre-R01 缺 date_observations · G2-5 3 条 temporal warning · G2-6 taxonomy alias 表 + Mechanism 登记表（**不扩展 taxonomy**） |
| OPEN | **历史数据修复需求（唯一 1 项，待独立评审）**：`C-2019-AD` 的 `strength='weak'` → 建议改 `medium`（保留 `result='weak'`）。属 legacy 语义残留，非本轮规则引入；由 `validate_governance_gates.py` **V8 持续 WARN**。影响：DB 1 行 / Export 1 条 / SA 轻微 |
| OPEN | **Worker ↔ ThreeC 规则统一待办**：Worker 报 `24 checks` vs ThreeC `C01–C25` · Worker 无 Strict Draft-07 · Worker `--check` 目录假设差异 · **Worker 无 orphan 检查** · **须向 Worker 提供 T01 后的 taxonomy 快照（11 root / 52 行）**（R01-06 manifest 曾误称 root 仅 4 个） · 建议后续为 Worker 增加 C26 并统一 `--check` 行为（**本轮不重建 Worker**） |
| OPEN | R01-05 孤儿证据 `E-FINRE-49/50/51/63`（intake 中未被任何候选引用）按既有惯例导入；`E-FINRE-63` = 全局基准 E141 · R01-06 孤儿证据 `E-MIL-40/41/42`（`E-MIL-42` = E042 反向证据，research-level 不绑定） |
| POLISH | `themeCycleId` 可读性 · `event_type` ↔ 证据类别标签对应 |

### 边界

- 不新增 Product 功能 / 不新增 Dashboard
- 不改 Research Model v1.0 / schema / CMTR v1 / Export Contract v1.0 /
  Structural Analogy Rule Set v0.2 / Time Observation v0.5
- 不引入实时网络 / LLM · 不建立 ranking / score / probability / prediction

| DONE | **★★ Research Core Release 完成（2026-09-23）**：Driver Canonicalization **v0.4** · **SA v0.4**（395 pairs · identity 52/27 · 两层独立校验 PASS · `driver=MISMATCH→PARTIAL` = 0）· **Time Observation v0.2**（79 objects · 12 patterns · **Timeline 仍仅 TOP-01**）· **Product 已消费最新 artifact**（`tsc -b` / `vite build` PASS）· 旧版本 18 个文件逐字节 UNCHANGED。详见 `docs/RESEARCH_CORE_RELEASE_v0_4.md` |

## 8. 当前质量债务

非主线 blocker：
- campaign_date_observations verified = 0/131
- Driver DIRECT evidence depth
- market / temporal = SUPPLEMENTARY_ONLY
- historical coverage imbalance

这些问题暂不阻塞本阶段 Review，但性能问题必须在 Product polish 前闭环。

## 9. 验证基线

最近已报告全绿：
- Structural Analogy Explanation `--check` PASS
- Research validators 全 PASS（`validate_db` / `validate_timeline_export` / `validate_batch_research` /
  `validate_promotion_manifest` / `check_doc_schema_consistency` / `validate_current_research` /
  `validate_monorepo_integrity` / `refresh --check`）
- **Intake Validator `--check` PASS（25 checks，FAIL 0，WARN 0；含 C25 严格 Draft-07；packages found 6）**
- **Intake Package R01-01 ~ R01-06 各 PASS（C01–C25）** · **Validator 单元测试 44/44 PASS**
- **R01-06 Canonical Import**：`validate_db` PASS（**3 条 WARNING 与导入前完全相同，无新增 temporal warning**）·
  既有 50 Campaign 逐条深比对 0 修改 · taxonomy `themes` 52→52 未变 · `import --verify` 幂等 · LF 不变式全 CRLF=0
- **R01 Governance Review（审计，未改数据）**：DB↔Export **0 字段不一致**（52↔52）· 共享 evidence **0**（1:1 全库零违规）·
  孤儿 evidence 25 / 孤儿 source 84 已人工复核 · 6 个新 rule 的 `campaign_year` ⊇ `annual_review` **零缺失** ·
  **3 条 DB warning 全部来自 R01-02**（总结类证据内容期 vs 发布期口径差，非数据错误）· **G0 = 0**
- npm test 476/476
- tsc -b PASS
- vite build PASS

下一轮任何实现先核对真实 HEAD，再执行验证。
