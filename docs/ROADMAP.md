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

## Phase 5.2 · 资金 / 筹码 / 情绪 / 广度维度（仅记录 · 未实现）

**目标**：为「机会地图」补充量的维度。
> ⚠️ V1.8.1 仅**记录**本方向，**未实现**任何代码 / 数据 / 字段。

- 资金流（北向 / 主力）、筹码分布、情绪指标、市场广度
- 数据来源与合规性需届时单独评估授权

---

## Phase 6 · Multi-theme（待 Review 后启动）

**目标**：从单条 Rule（`rule_auto_summer`）扩展到多主题。

- 新增行业 / 主题的 Research Campaign 生产
- 多 Rule 并行的时间轴呈现
- Export Contract 保持 v1.0 兼容（新增可选字段，不破坏）

---

## Phase 7 · Current Market Mapping（待 Review 后启动）

**目标**：把"今天"映射到历史时间轴。

- 当前日期 → 历史同周期对照（已有 SamePeriodView 的深化）
- 当年实际走势与历史窗口的偏离度对比
- 「今年是否重演」的**情景分析框架**（前瞻性分析，不是确定性预测）

---

## Phase 8 · Opportunity Discovery / Radar（待 Review 后启动）

**目标**：机会发现能力的系统化。

- 历史相似阶段检索、当前状态与历史条件的分布对比
- 观察窗口的规则化呈现

> ⚠️ **Radar 不是交易信号。**
> 输出的是"值得研究的方向"，不是"买入 / 卖出"。
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
