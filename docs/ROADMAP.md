# ROADMAP.md — ThreeC 阶段规划（合并版）

> 本文件整合原 `Cycle/docs/ROADMAP.md` 与 Cycle-Research 的阶段规划，
> **按项目阶段重新整理**，不是两份文件的拼接。
> 历史细项（V1.5 / V1.6.x / V1.7 的逐条实现）保留在 `docs/CHANGELOG.md`。
> 规则：未来功能记录在这里，而不是提前实现在代码里。

---

## Phase 1 · Research Model（已完成）

**目标**：建立历史研究的认知框架与数据模型。

- 概念链：`Source ≠ Evidence ≠ Rule ≠ Historical Fact ≠ Verification ≠ Prediction`
- 证据双维度：**Evidence Status**（L0–L4） ≠ **Verification Status**（not_tested → statistically_supported）
- Campaign 判定原则 V1：不能仅因行业上涨建 Campaign
  （持续性 / 可识别主题 / 市场关注 / 可解释起止，四项齐备）
- SQLite 研究数据库 + `schema.sql`
- **Research Model v1.0 Frozen**（`research/research/methodology/research_model_v1_0.md`）

---

## Phase 2 · Historical Data Production（已完成）

**目标**：批量生产可回查的历史研究数据。

- 行情核验基础设施：`market_series / market_daily / trading_calendar / campaign_date_observations`
- Price Policy：raw close 判日期，adjusted close 算收益；不混用口径
- Trading Day vs Calendar Day 分离
- **2018–2025 八年度批量研究**：`research/scripts/batch_auto_research.py`
- 研究状态层：`PROVISIONAL / CONFLICT / INSUFFICIENT`（不改 SQLite schema）
- 产出：`research/batch/` manifest + conflicts、`research/summary/`、`research/annual/`
- 结论：**"6–8 月汽车" = 历史观察窗口，Partially Supported**

---

## Phase 3 · Timeline MVP（已完成）

**目标**：让历史数据可见。

- **V1.6**：Timeline Data Adapter 层（`TimelineDataSource` 统一接口）；
  365 天真实比例时间轴；Campaign 生命周期视觉主体；Preview / Production 隔离（`?preview=1`）
- **V1.6.1**：Real Research Export Integration —— 接入 canonical Contract v1.0
- **V1.6.2**：Conflict Campaign Timeline Visualization（保留 Candidate A / B 双方）
- **V1.7**：Historical Opportunity Map UX ——
  Phase Window 优先于精确日期、Date Conflict 分级（minor / major）、
  驱动因素四问、历史同周期查看（SamePeriodView）、OpportunityRadar

---

## Phase 4 · Monorepo Integration（已完成）

**目标**：一个项目、一个 Git、一个 canonical export、两个逻辑模块。

- Cycle 为根仓库，Cycle-Research 经 `git subtree` 并入 `research/`（历史保留）
- 唯一 `.git` / 唯一 `origin`（`yangfanbit/Cycle`）
- canonical export 唯一化 → `exports/timeline_export_v1.json`
  （移除 `src/data/timeline/data/` 手工副本）
- 数据流：`research/` → `exports/` → Cycle Adapter → Timeline UI（无手工 Copy）
- 新增接班文档：根 `AGENTS.md`、`research/AGENTS.md`、
  `docs/PROJECT_STATE.md`、`docs/PRODUCT_PURPOSE.md`、本 ROADMAP、`docs/CHANGELOG.md`
- 新增 `scripts/validate_monorepo_integrity.py`

---

## Phase 5 · Current Time Lens v0（已完成 · IMPLEMENTED）

**目标**：把「今天」变成产品入口 —— 打开即回答「今天这个时间点，历史上附近发生过什么？」
**不做**预测 / 荐股 / 交易信号。

- 新增 `src/data/timeline/currentTimeLens.ts`：`currentTimeLens(source, today)`
  - 复用 `samePeriodWindow()` / `samePeriodCampaigns()`，不发明第二套日期逻辑
  - 输出：A 时间定位 / B 历史同期（按年份）/ C 历史阶段映射（**当时处于**）/ D 可能驱动
- 新增 `src/components/CurrentTimeLens/CurrentTimeLens.tsx`：点击经现有
  `selection` 打开 Campaign Detail
- 新增测试 `src/data/timeline/__tests__/currentTimeLens.test.tsx`（28 项）
- 数据源仍为唯一 canonical `exports/timeline_export_v1.json`，**零**新数据 / 新 Schema / 新 Export 字段

> 注：Phase 5 原将 Lens 置于页面顶部；**Phase 5.1（V1.8.1）已将其降级为③补充摘要**，
> 恢复 Timeline 为第一视觉。

---

## Phase 5.1 · V1.8.1 主题级历史机会视图（已完成 · IMPLEMENTED / READY FOR USER VISUAL REVIEW）

**目标**：把「历史同期」从「一行一个 Campaign」升级为「**一行一个主主题**」，
并重排页面 IA，恢复 Timeline 为第一视觉。

- 页面 IA 重排：**① Timeline → ② 历史同周期主题 → ③ 当前时间上下文**
- 新增 `src/data/timeline/themeRows.ts`：`themeRowsOf(source, month)` → `ThemeRowsResult`
  - **`TimelineThemeRow` 为纯 UI / Adapter 视图概念**（无 `theme_cycles` / `theme_relations` / schema 变更）
  - 步骤：`samePeriodCampaigns` → Theme Grouping（按主主题）→ Theme Rows
  - 行字段：`themeKey / title / years / campaigns / primaryPhase / phaseSummary /
    relatedConcepts / statuses`
  - 同主题多条**独立行情不合并**；RC 保留 badge、状态不升级；仅**重大冲突**显示 ⚠
- `SamePeriodView` 重构为主题级（组件名与能力保留）：主题行 + 展开明细
- `CurrentTimeLens` 降级为③；标签「可能驱动 / 相关因素」→「**可能相关因素**」（仅 UI 文案）
- 新增测试 `src/data/timeline/__tests__/themeRows.test.tsx`（18 项，含 11 场景）
- **明确不做**：新数据 / 新 Schema / 新主题 / Export Contract 变更 / Research 语义变更 /
  由 Event 自动生成「相关因素」

**验收**：2026-09-13 打开页面，Timeline 为第一视觉；历史同周期以主题行呈现。
下一步：**真实用户界面 Review**。

---

## Phase 5.2 · V1.8.2 Timeline Detail UX + Historical Pre-observation Window（已完成 · IMPLEMENTED / READY FOR USER EXPERIENCE REVIEW）

**目标**：详情不再打断 Timeline 阅读；新增「提前观察区」帮助用户提前开始研究。

- **两级详情**：
  - **Level 1 Inline Summary**：点击主题行 → 就地展开摘要（主题 / 年份 / 阶段 / 关键阶段 /
    提前观察区 / 可能相关因素 / 数据状态 / RC / Conflict），不离开主页面、不遮挡 Timeline。
  - **Level 2**：仅点「查看完整历史案例」才打开完整 `CampaignDetail`（保留全部字段）。
- **Timeline 永远第一视觉**：点击主题 / Campaign 不遮挡 Timeline；无大型 modal、无永久右侧大面板压缩。
- **移动端**：详情为 **Bottom Sheet**（非固定 Side Drawer）。
- **历史提前观察区**（新增 `src/data/timeline/preObservation.ts`）：
  - `historicalPreObservationDays = 30`（**UI research buffer**，注明「不代表历史平均领先期」）
  - 层级：`Pre-observation → Early Signal? → Theme Formation`
  - Timeline 视觉：极淡点划线 + 斜纹 + 低透明度，不抢 Campaign 主体与 Peak
  - 文案统一「历史提前观察区」；**禁止**「买入区 / 布局区 / 信号区」
- 新增测试 `src/data/timeline/__tests__/preObservation.test.tsx`（25 项）
- **明确不做**：新主题 / 新 Research / 资金流 / 筹码 / 情绪 / 预测 / Radar / Statistics / Dashboard / Notification

**验收**：Timeline 保持第一视觉；点击主题就地展开摘要；提前观察区不被误认为预测。
下一步：**真实用户体验 Review**。

---

## Phase 5.2.1 · V1.8.2.1 Pre-observation Semantic Fix（已完成 · IMPLEMENTED / READY FOR USER VISUAL REVIEW）

**目标**：修正提前观察区的语义锚点错误，统一文案为「提前观察参考区」。

- **Formation Anchor 规则**（`themeFormationDate()` 重写）：
  `THEME_FORMING.start → BROAD_CONFIRMATION.start → Campaign.start → null`
  **禁止**取 lifecycle 最早 stage（原实现会把 `EARLY_SIGNAL` 误认为 `THEME_FORMING`）。
  新增 `formationAnchorOf()` 与 `formationAnchor` 字段暴露锚点来源。
- **Early Signal 与 Formation 分离**：Early Signal 继续用导出既有 `early_signal`，**不重新推导**；
  层级 `提前观察参考区 → Early Signal? → Theme Formation → Main Rise`，二者为独立边界。
- **30 天含义不变**：`historicalPreObservationDays = 30` = **UI / Research browsing buffer**，
  不是历史统计领先期 / 预测 / 买入时间。
- **文案**：「历史提前观察区」→「**提前观察参考区**」；
  hint →「仅用于研究浏览参考，不代表历史平均领先期，也不是买入建议。」
- **视觉层级**：`Campaign > Early Signal > 提前观察参考区`
  （`.bar.cmp-main_rise` 0.95 > `.bar.early-signal` 0.5 / z-1 > `.bar.pre-obs` 0.4 / z-0）。
- 更新测试 `preObservation.test.tsx`（+9 项：锚点规则 ①②③④⑤ / Early Signal 独立性 ④⑤⑥ / 视觉层级）
- **明确不做**：Research / Schema / Database / Export Contract / TimelineExportV1 / Research Model /
  新主题 / 资金 / 筹码 / 情绪 / Theme Row 逻辑 / CampaignDetail UX

**验收**：`RC-2023-HUAWEI` 参考区 08-05 ~ 09-03 → 早期信号 08-29 → 形成 09-04（三者不再同日）。

---

## Phase 5.3 · 资金 / 筹码 / 情绪 / 广度维度（仅记录 · 未实现）

**目标**：为「机会地图」补充量的维度。
> ⚠️ V1.8.2 仅**记录**本方向，**未实现**任何代码 / 数据 / 字段（只保留未来扩展接口）。

- 资金流（北向 / 主力）、筹码分布、情绪指标、市场广度
- 数据来源与合规性需届时单独评估授权

---

## Phase 5.4–5.8 · 分层模型统一与多主题接入（已完成 · IMPLEMENTED）

- **Theme / Campaign / Sub-theme 分层统一审计** + Campaign Independence Gate Q1–Q5
  （`docs/THEME_CAMPAIGN_MODEL_AUDIT.md`）
- **Research Model v1.1 方法论补丁**：Theme Cycle Pattern（Sequential / Parallel / Hybrid）·
  Campaign Lifecycle Measurement Rule · Gate Q1 Anti-example
- **医药健康 Pilot**：首个非汽车 Macro Theme（1 正式 Campaign + 2 Research Candidate，真实行情）
- F-MED-1 跨年年份语义（V1.8.4）· Timeline Entry Identity（V1.9.0）· Year Coverage Rule（V1.9.1）

---

## Phase 6 · Product Core v2（已完成 · IMPLEMENTED）

把 Timeline + Historical Same Period + Current Time Lens 升级为**当前研究导航层**。

- **F-MED-6**：Selection 区分展示实例（`entryId`）与完整历史案例（`campaign_id`）
- **Current Time Lens v2 三层**：A. A股整体环境 = `Unknown`（**绝不**由行业反推大盘）·
  B. 当前 Theme / Theme Cycle（无当前年份数据 → 诚实空态）· C. Research Attention 状态分类
- **Historical Similar Phase v1（Lifecycle Lens）**：阶段 → Pattern → Drivers；Top 3、无百分比、无证据 → 空态
- **Macro Theme 聚合接口**（仅 View / Adapter；不改 Timeline 视觉）
- IA：`① Timeline → ② 当前时间研究导航 → ③ 历史相似阶段 → ④ 历史同期（日历）`

---

## Phase 7 · Current Research Discovery v0.1（已完成 · IMPLEMENTED）

让产品能回答**「今天这个时间点，我应该去历史资料里研究什么？」**
架构原则：网络与 AI 只出现在**离线研究数据生成端**，不进入运行时。

- **数据协议层** `research/current/`：canonical 数据集 + JSON Schema + README + 示例 fixture + 叙事标注
- **验证器** `research/scripts/validate_current_research.py`（Data / Temporal / Evidence / Phase /
  Similarity / Theme Boundary 六组校验）
- **产品层 5 个纯 View 模块**：`currentCandidate` · `currentEvidence`（Evidence Ledger +
  Temporal Firewall + 相位证据矩阵 + 冲突 + 状态门）· `currentPhaseInference`（R0–R8 规则引擎）·
  `currentSimilarity`（Similarity v2）· `currentCandidateAdapter`
- **UI**：Current Lens 内「当前研究候选」区（概览 + 就地展开 + 诚实空态）
- 四条红线：Temporal Firewall · 禁用单一指标推阶段 · 状态门**只降不升** · 相似度**无百分比**

---

## Phase 7.1 · First Real Current Research（已完成 · IMPLEMENTED）

- `snapshot_date = 2026-09-15`：5 个 `CC-*` 真实候选 / 39 条证据 / **0 条 AFTER_SNAPSHOT**
- 拒绝候选池 5 条 + 本轮架构问题 4 条（`research/current/README.md` §8 / §9）
- 跨会话并行轮次的裁决与交叉记录（`research/current/README.md` §11）

---

## Phase 7.2 · Time-based Observation Layer（已完成 · IMPLEMENTED）

把「**什么时候值得看**」做成产品能力 —— 回答：

> 「历史上，一年中的这个时间位置附近，**反复出现过**值得研究的主题启动 / 观察现象吗？」

- **Research**：`research/research/reports/time_observation_patterns_v0_1.json`
  （4 条模式：1 条进入 Timeline / 2 条留在研究层 / 1 条拒绝）+ 整合报告
  `Time_Observation_Pattern_Integration_v0_1.md` + canonical 生成器
  `research/scripts/build_time_observation_patterns.py`（可复现，`--check` 逐字节校验）
- **Product**：`src/data/timeline/timeObservationPatterns.ts`（宽容解析 + **跨年环形窗口** +
  邻近关系 + View Model 排序）+ `src/components/TimeObservation/TimeObservationLayer.tsx`
  （Timeline 内**极轻一层**：窗口带 + 该年观察起点标记 + Level 2 摘要）
- **三层信息结构**：Timeline 窗口带 → 就地 Pattern 摘要 → **既有** Campaign Detail（不新建第四套详情）
- **语义纪律**：只讲「历史观察窗口 / 历史复现」；不出现概率 / 胜率 / 买卖信号；无窗口时**不渲染本层**
- **未改**：DB / `schema.sql` / canonical export / `contracts/` / Campaign 定义 / Research Model /
  Timeline 主视觉

**验收**：打开 Timeline 即看到「时间型观察层」；今天落在窗口内时提示「当前位于历史观察窗口」；
点击某一年 → 进入既有 Campaign Detail。

---

## Phase 7.3 · Structural Historical Analogy（推迟 · 未实现）

> ⚠️ **本轮（Phase 7.2）明确未实现。** 记录在此，避免提前实现。

- `Current State → Structural Signature → Historical Phase`
- 与 Time Observation Pattern 的分层关系：
  Time Pattern 回答「**什么时候值得看**」，Structural Analogy 回答「**这个方向像哪段历史**」。
- 前置条件：Time Observation Layer 的样本量与日期核验先改善（见 Phase 7.2 报告的 P0 / P1）。

---

## Phase 8 · Opportunity Discovery / Radar（推迟 · 未实现）

> ⚠️ 由 Phase 7.2 重新排序 —— 「Radar」不再紧接 Phase 5，而是排在 Structural Historical Analogy 之后。

- 历史相似阶段检索、当前状态与历史条件的分布对比、观察窗口的规则化呈现

> **Radar 不是交易信号。**
> 输出的是「值得研究的方向」，不是「买入 / 卖出」。
> 用户自己负责入场判断（见 `docs/PRODUCT_PURPOSE.md`）。

---

## 长期待治理（非阶段目标）

- **Event 日期精度**：两会会期目前是"近似被当作确定"，应改 `variable` 或加 `approximate`
- **Rule.status 双字段拆分**：`evidence_status` / `verification_status`
- **数据源迁移**：TS 模块 → SQLite（待业务模型稳定后）

---

## 未来可能加入（均需届时单独评估授权）

- 实时行情 / 资金流 / 市场异动
- 个性化观察池
- 通知
- 组件级测试与 E2E 框架

> 以上均**未授权**。默认状态下不得实现。
