# CHANGELOG.md — ThreeC 变更记录

> 本文件为 ThreeC 统一变更记录（Monorepo Integration 后）。
> 原 `Cycle/docs/CHANGELOG.md` 的 V1–V1.7 全部历史**完整保留在下方**。
> 原 Cycle-Research 的历史记录保留在 `research/` 内的报告文件中
> （`RESEARCH_MODEL_V1_FREEZE_REPORT.md`、`HISTORICAL_DATA_PRODUCTION_V1_REPORT.md` 等）。

---

## 2026-09-13 · Phase 5.2.1 V1.8.2.1 Pre-observation Semantic Fix（Formation Anchor）

### 目标

修正提前观察区的**语义锚点错误**，并把文案统一为「提前观察参考区」。
本轮**不改 Research / Schema / Database / Export Contract / TimelineExportV1 / Research Model**，
不新增主题，不增加资金 / 筹码 / 情绪，不改 Theme Row 逻辑，不改 CampaignDetail UX。

### 原语义问题

`themeFormationDate()` 原实现为「取 lifecycle 中最早阶段 start」。但 lifecycle 通常以
`EARLY_SIGNAL` 开头，导致把**早期信号误当成主题形成**。

真实案例 `RC-2023-HUAWEI`：

| | 修正前（错误） | 修正后（正确） |
|---|---|---|
| Formation | 2023-08-29（= EARLY_SIGNAL）✗ | **2023-09-04**（THEME_FORMING）✓ |
| 参考区 | 07-30 ~ 08-28 | **08-05 ~ 09-03** |
| Early Signal | 08-29（与 Formation 同日） | **08-29**（独立锚点，不等于 Formation） |

### 新 Formation Anchor 规则

```
1. lifecycle.stage === 'THEME_FORMING'      → 该 stage.start
2. 否则 'BROAD_CONFIRMATION'                → 该 stage.start
3. 否则 Campaign.start                      → campaign_start
4. 都没有                                    → null（不编造）
```

**禁止**直接取 lifecycle 最早 stage。新增 `formationAnchorOf()` 暴露锚点来源，
`PreObservationWindow` 新增 `formationAnchor` 字段（`THEME_FORMING` / `BROAD_CONFIRMATION` / `campaign_start`）。

### Early Signal 与 Formation 的关系

- Early Signal **继续使用** `TimelineCampaign.early_signal` 与 Research Export 既有数据，**不重新推导**。
- 二者是**两个独立边界**：`参考区 → 早期信号 → 主题形成 → 主升`。
- 顺序保证：`preObservation.end < formation`，且 `earlySignal.start !== formation`。

### 30 天的真实含义（不变）

`historicalPreObservationDays = 30` 保持不变，含义为 **UI / Research browsing buffer**：
不是历史统计领先期、不是预测、不是买入时间。

### 文案变化

| 位置 | 旧 | 新 |
|---|---|---|
| `PRE_OBSERVATION_LABEL` | 历史提前观察区 | **提前观察参考区** |
| `PRE_OBSERVATION_HINT` | 仅为研究浏览缓冲，不代表历史平均领先期，也不是买入建议。 | **仅用于研究浏览参考**，不代表历史平均领先期，也不是买入建议。 |

### 视觉层级（Section 八）

`Campaign > Early Signal > 提前观察参考区`，opacity 与 z-index 双降序：

| 元素 | opacity | z-index |
|---|---|---|
| `.bar.cmp-main_rise`（Campaign） | 0.95 | — |
| `.bar.early-signal` | 0.5 | **1**（新增） |
| `.bar.pre-obs` | **0.4**（原 0.62） | 0 |

参考区继续：点线边框 + 斜纹 + 低 z-index，不抢 Campaign / Peak / Early Signal。

### 修改文件

| 文件 | 变化 |
|---|---|
| `src/data/timeline/preObservation.ts` | 重写 `themeFormationDate()`（锚点优先级）；新增 `formationAnchorOf()`；`PreObservationWindow.formationAnchor`；`PreObservationChain.formationAnchor`；标签与 hint 文案更新 |
| `src/components/Timeline/Timeline.tsx` | tooltip 文案改「提前观察参考区」+「主升」层级；注释更新 |
| `src/components/CurrentTimeLens/CurrentTimeLens.tsx` | 移除脆弱的 `.replace('历史','')`；文案改「研究浏览参考」 |
| `src/components/SamePeriodView/SamePeriodView.tsx` | 仅注释更新（标签走常量） |
| `src/data/timeline/themeRows.ts` | 仅注释更新 |
| `src/styles.css` | `.bar.pre-obs` opacity 0.62→0.4；`.bar.early-signal` 加 `z-index:1`；注释更新 |
| `src/data/timeline/__tests__/preObservation.test.tsx` | 重写 Section 5/6（锚点规则 + Early Signal 独立性）；新增视觉层级测试 |

### 验证

- `npm test` **191 项通过**（182 → 191，+9）；`tsc -b` 通过；`build` 通过（58 modules）。
- **未运行** Python 校验脚本（本轮零 Research / Schema / Export 变更）。
- diff 零触及 `schema.sql` / `research/**` / `exports/**` / `src/models/` / `contracts/`。

---

## 2026-09-13 · Phase 5.2 V1.8.2 Timeline Detail UX + Historical Pre-observation Window

### 目标

详情不再打断时间轴阅读（两级详情）；新增「历史提前观察区」帮助用户提前开始研究。
本轮**不新增主题 / Research / 资金流 / 筹码 / 情绪 / 预测 / Radar / Statistics / Dashboard / Notification**。

### 新增文件

| 文件 | 说明 |
|---|---|
| `src/data/timeline/preObservation.ts` | `historicalPreObservationDays = 30`；`preObservationWindowOf` / `preObservationChainOf` / `isInPreObservation` / `themeFormationDate`；`PRE_OBSERVATION_LABEL` / `PRE_OBSERVATION_HINT` |
| `src/data/timeline/__tests__/preObservation.test.tsx` | 25 项测试（10 场景 + 附加） |

### 修改文件

| 文件 | 变化 |
|---|---|
| `src/components/SamePeriodView/SamePeriodView.tsx` | 两级详情：Level 1 Inline Summary（就地展开，`sp-inline-*`）；「查看完整历史案例」为唯一 Level 2 入口 |
| `src/components/Timeline/Timeline.tsx` | 新增提前观察区条形（`bar cmp pre-obs`），位于 Campaign 主体之前 |
| `src/components/CampaignDetail/CampaignDetail.tsx` | 增加 `role="dialog"` / `aria-label`（Level 2 语义） |
| `src/components/CurrentTimeLens/CurrentTimeLens.tsx` | 新增「今天处于某历史主题的提前观察区」提示 + 「不代表本年度预测」限定 |
| `src/data/timeline/themeRows.ts` | `ThemeCampaignEntry` 新增 `preObservation`（三层链） |
| `src/styles.css` | 新增 `.sp-inline-*` / `.pre-*` / `.ctl-pre-obs` / `.bar.pre-obs`；详情面板移动端改为 Bottom Sheet；清理 V1.8.1 废弃 `.sp-item-line` / `.sp-campaigns` 等样式 |
| `docs/PROJECT_STATE.md` / `docs/ROADMAP.md` / `AGENTS.md` / `docs/CHANGELOG.md` | 阶段 / 状态 / 阶段规划更新 |

### 设计要点（严格遵守约束）

- **Timeline 永远第一视觉**：点击主题行调用 `onToggle`（就地展开），**不**调用 `onSelect`；
  仅「查看完整历史案例」调用 `onSelect`（测试断言源码中 `onSelect?.(` 仅 1 处）。
- **提前观察区语义**：`historicalPreObservationDays = 30` 为 **UI research buffer**，
  代码注释明确「仅为研究浏览缓冲，不代表历史平均领先期」。
- **层级**：`Pre-observation → Early Signal? → Theme Formation`（无 Early Signal 退化为两段式，不编造）。
- **窗口口径**：`[formation-30, formation-1]`（不含形成日，避免与 Campaign 主体重叠）；
  `formation` 取 lifecycle 最早阶段起点，否则 `Campaign.start`。
- **禁止文案**：买入区 / 布局区 / 信号区 / 30天后大概率上涨 / 建议提前布局 / 最佳埋伏。
- **一行一个主题**保持不变；同主题多条独立行情不合并；RC 保留 badge；仅重大冲突显示 ⚠。
- **未实现**：资金 / 筹码 / 情绪 / 广度 —— 仅在 Roadmap Phase 5.3 **记录**。

### 验证

- `npm test` **182 项通过**（157 → 182，+25）；`tsc -b` 通过；`build` 通过（58 modules）。
- 真实导出复核：提前观察区逐条 30 天；`RC-2023-HUAWEI` 三层链完整
  （观察区 07-30 ~ 08-28 → 早期信号 08-29 → 形成 08-29）。
- **未运行** Python 校验脚本（本轮无 Research / Schema / Export 变更）。
- diff 零触及 `schema.sql` / `research/**` / `exports/**` / `src/models/` / `contracts/`。

---

## 2026-09-13 · Phase 5.1 V1.8.1 主题级历史机会视图

### 目标

把「历史同期」从「一行一个 Campaign / 个股」升级为「**一行一个主主题**」，
并重排页面 IA，恢复 **Timeline 为第一视觉**。本轮**不增加新数据 / 新主题 /
新 Schema / Export Contract 变更 / Research 语义变更**。

### 页面 IA（重排）

```
① Timeline（第一视觉）
② 历史同周期主题（主题级：一行 = 一个主主题，展开见独立行情）
③ 当前时间上下文（原 Current Time Lens，降级为补充摘要）
```

### 新增文件

| 文件 | 说明 |
|---|---|
| `src/data/timeline/themeRows.ts` | `themeRowsOf(source, month)` → `ThemeRowsResult`；导出 `TimelineThemeRow` / `ThemeCampaignEntry` / `primaryThemeName` |
| `src/data/timeline/__tests__/themeRows.test.tsx` | 18 项测试（主题分组 1–8 / IA 9 / 产品 10–11） |

### 修改文件

| 文件 | 变化 |
|---|---|
| `src/components/SamePeriodView/SamePeriodView.tsx` | 重构为主题级：主题行（`sp-theme-*`）+ 展开明细（`sp-item-line`）；标题「历史同周期主题」；新增 `selection` / `onSelect` props |
| `src/App.tsx` | IA 重排：`<Timeline>` → `<SamePeriodView>` → `<CurrentTimeLens>` |
| `src/components/CurrentTimeLens/CurrentTimeLens.tsx` | 标题改「当前时间上下文」+「补充查看 · 非主视图」标签；「可能驱动 / 相关因素」→「**可能相关因素**」（仅 UI 文案） |
| `src/styles.css` | 新增 `.sp-theme-*` / `.sp-item-line` / `.sp-related-chip` / `.sp-conflict-flag` 样式 |
| `src/data/timeline/__tests__/currentTimeLens.test.tsx` | D 块断言随标签改名更新（仍断言旧标签**不出现**） |
| `docs/PROJECT_STATE.md` | Phase 5.1；Completed 表 / Product Status / Next Single Goal / Explicitly Not Doing 更新 |
| `docs/ROADMAP.md` | 新增 Phase 5.1（已完成）+ Phase 5.2（仅记录） |
| `docs/CHANGELOG.md` | 本条目 |

### 设计要点（严格遵守约束）

- **`TimelineThemeRow` = 纯 UI / Adapter 视图概念**，**不是** DB 实体：
  无 `theme_cycles` / `theme_relations`，不改 `src/models/`、不改 `schema.sql`。
- **日期口径完全复用** `samePeriodCampaigns()`（内部即 `samePeriodWindow()`）；
  阶段口径复用 `currentTimeLens.historicalPhasesInWindow()`，不另造第二套逻辑。
- **同主题多条独立行情不合并**：分组只决定"行归属"，行内仍是各自 Campaign；
  RC 保留 badge、状态不升级（`candidate` 永不 verified）。
- **主题信息完全来自导出既有 `themes` 字段**：`primaryThemeName` = `role='main'` 优先，
  否则第一个；无 theme → 归入「未标注主题」占位组（不编造）。
- **仅重大冲突显示 ⚠**：`>10 天` 计为 major；轻微分歧不升级告警视觉。
- **「可能相关因素」不由 Event 自动生成**：沿用 `campaignDrivers()` 研究层归因口径；
  改名仅 UI 文案，Research 数据与 API 未变。
- **不删除 `SamePeriodView` / `currentTimeLens.ts`**：组件名与能力保留，仅内部重构 / 降级。
- **未实现**：资金 / 筹码 / 情绪 / 广度维度——仅在 Roadmap Phase 5.2 **记录**。

### 验证

- `npm test` **157 项通过**（139 → 157，+18）；`tsc -b` 通过；`build` 通过。
- 真实导出 SSR 复核（9 月）：5 个主题行 / 7 条独立行情，RC 2023–2024 保留 badge。
- **未运行** Python 校验脚本（本轮无 Research / Schema / Export 变更）。

---

## 2026-09-13 · Phase 5 Current Time Lens v0（现已被 Phase 5.1 降级为③补充摘要）

### 目标

把「今天」变成产品入口 —— 打开即回答
**「今天这个时间点，历史上附近发生过什么？」**
**不做**预测 / 荐股 / 交易信号 / 概率统计。本轮**不扩大功能**、不改 Research Model、
不改历史研究结论、不改 Schema / Export Contract、不新增数据。

### 新增文件

| 文件 | 说明 |
|---|---|
| `src/data/timeline/currentTimeLens.ts` | `currentTimeLens(source, today)` 纯函数；导出 `historicalPhasesInWindow` / `possibleDriversOf` / `stageLabel` 及类型 |
| `src/components/CurrentTimeLens/CurrentTimeLens.tsx` | 页面顶部入口组件（A–D 四块） |
| `src/data/timeline/__tests__/currentTimeLens.test.tsx` | 28 项测试（数据逻辑 1–8 / 联动 9–10 / 产品 11–13 + SSR 渲染 3 项） |

### 修改文件

| 文件 | 变化 |
|---|---|
| `src/App.tsx` | `<CurrentTimeLens>` 置于 `<Timeline>` 之上，复用现有 `selection` / `setSelection`；移除 `<OpportunityRadar>` 渲染与其 import（组件文件保留） |
| `src/styles.css` | 新增 `.ctl-*` 样式块（Lens 面板 / 年份行 / 条目 grid / 驱动 chip） |
| `docs/PROJECT_STATE.md` | Phase 4 → Phase 5；Completed 表 / Product Status / Next Single Goal / Blockers 更新 |
| `docs/ROADMAP.md` | Phase 5 改为 Current Time Lens v0（已完成）；原机会地图深化顺延为 Phase 5.1 |
| `AGENTS.md` | §2 当前阶段、§4 目录、§9 测试数、§12 下一目标 |
| `docs/CHANGELOG.md` | 本条目 |

### 设计要点（严格遵守约束）

- **复用 `samePeriodWindow()` / `samePeriodCampaigns()`**：不发明第二套日期逻辑（9 月 → 08-15 ~ 10-15）。
- **只消费 canonical `TimelineDataSource`**（= `exports/timeline_export_v1.json`）：零新数据 / 新 Schema / 新 Export 字段。
- **「当时处于」语义**：`historicalPhasesInWindow()` 返回 Campaign 在**历史那个窗口内**命中的
  lifecycle 阶段（历史事实），**绝不写成「当前处于」** —— 技术上防止「历史相似 = 今年重演」的误读。
- **不做「N 次」**：结果对象无 probability / frequency / score 字段；仅以「覆盖 N 个年份」提示覆盖度。
- **未覆盖措辞**：无数据 → 「当前研究数据未覆盖（不是「历史没有机会」）」。
- **不编造**：无 `lifecycle` → 「历史阶段未标注」；Research 原始归因标签（含 `unknown（…）`）原样展示。

### 验证结果（全绿）

- Node：`npm test` **139 项通过**（lens 28 + adapter 59 + utils 52）；`tsc -b` 通过；`build` 通过
  （56 modules，229.50 kB JS / 16.52 kB CSS）。
- Python：`validate_db.py` / `validate_timeline_export.py` / `validate_batch_research.py` 全部 PASS。
- SSR 实测（2026-09-13，preview）：2019 智能驾驶「主升」/ 2020 新能源「次级行情」/ 2021「退潮」/
  2022 购置税「退潮」/ 2023 RC-华为「主升」(09-20~10-15) / 2024 RC-次级「早期信号」/ 2025「主段结束」。
- 生产 verified 空 → Lens 正确落「当前研究数据未覆盖」空态。

### 未做（明确）

未新增 Rule / 主题 / 数据 / Schema / Export 字段 / Statistics / Similarity / Probability /
Prediction / Recommendation / Realtime / Radar Upgrade / Dashboard；未删 `OpportunityRadar.tsx`；
未改 `schema.sql` / `database/cycle_research.db` / Research 研究语义。

---

### 目标

把 `Cycle`（产品）与 `Cycle-Research`（研究）合并为**单一仓库 `ThreeC`**：
一个项目、一个 Git、一个 canonical export、两个逻辑模块、一个项目目标。
**本轮不扩大功能**；不改 Research Model、不改历史研究结论、不新增 UI。

### 迁移事实

| 项 | 值 |
|---|---|
| 原 Cycle HEAD | `d37950027380037970447c163c8159f14f64d5f8`（11 commits） |
| 原 Cycle-Research HEAD | `eadf06a1555b2c46817c543c3e8454d4326a5efb`（28 commits） |
| 迁移方式 | Cycle 为根仓库；Cycle-Research 经 `git subtree add --prefix=research` 并入 |
| 结果 | 40 commits（11 + 28 + 1 join）；双方原始 author / date / message 保留 |
| 唯一远程 | `origin` → `https://github.com/yangfanbit/Cycle.git` |

`git log -- research/` 可完整追溯原 Cycle-Research 历史。

### 结构变化

- `Cycle/` 内容提升为仓库根（`src/`、`package.json`、`vite.config.ts`、`data/`、`tests/`、`docs/`）。
  **未**新建 `apps/cycle/`。
- `Cycle-Research/` 内容并入 `research/`（`database/`、`schema/`、`scripts/`、`data/`、`research/`）。
- 删除内层 `.git`（`Cycle/.git`、`Cycle-Research/.git`）——**在历史安全迁移且内容确认无丢失之后**。

### Canonical Export 唯一化

- **唯一源**：`exports/timeline_export_v1.json`
  （SHA256 `BF36FF7B419F4BFA982527B15F5853E3BB67F7CA4D8941D2932B358574EFD01E`，内容零变化）。
- **移除**前端手工副本 `src/data/timeline/data/timeline_export_v1.json`（原为逐字节拷贝）。
- 前端消费路径：`src/data/timeline/timelinePreview.ts` → `@exports/timeline_export_v1.json`。
  - `vite.config.ts`：新增 `resolve.alias['@exports']` → `./exports`
  - `tsconfig.json`：新增 `paths["@exports/*"]`、`include` 加入 `exports`、
    `types` 加入 `node`（新增 devDependency `@types/node`）
- 数据流统一为：

```
research/ → Research scripts → exports/timeline_export_v1.json
  → Cycle Timeline Adapter → Timeline UI
```

不再存在 `Research → 手工 Copy → Cycle JSON` 路径；仓库内**只有一个** canonical JSON。

### Research 脚本路径适配（3 个文件，仅路径语义）

| 文件 | 变化 |
|---|---|
| `research/scripts/db.py` | 新增 `REPO_ROOT` / `EXPORTS_DIR` / `TIMELINE_EXPORT_PATH`（canonical 在 `research/` 上一级）；`ROOT` 语义 = `research/` |
| `research/scripts/batch_auto_research.py` | `EXPORT = db.TIMELINE_EXPORT_PATH` |
| `research/scripts/validate_timeline_export.py` | `ROOT = db.ROOT`；`EXPORT = db.TIMELINE_EXPORT_PATH` |

**未改动**任何研究数据内容、Model、schema、历史结论。

### 新增接班文档

- `AGENTS.md`（根，重写为 12 节接班入口：初心 / 阶段 / 边界 / 目录 / 数据流 / Contract /
  数据状态 / 禁止事项 / 测试 / 修改规则 / Git 规则 / 下一目标）
- `research/AGENTS.md`（Research 职责书：Model v1.0 Frozen、负责 / 不负责、工作流、红线）
- `docs/PROJECT_STATE.md`（一至两页：Purpose / Phase / Completed / Architecture / Status /
  Contract / Limitations / Blockers / Next Goal / Not Doing）
- `docs/PRODUCT_PURPOSE.md`（基于历史时间轴的 A 股机会地图；核心 / 非核心 / 边界声明）
- `README.md`（根，重写：ThreeC = Research + Cycle Product）
- `docs/ROADMAP.md`（Phase 1–8 重新整理，非拼接）
- `contracts/timeline_export_v1.md`（契约副本，跨模块接口单一出处）
- `research/scripts/validate_monorepo_integrity.py`（15 项完整性校验）

### 验证结果

| 项 | 结果 |
|---|---|
| Cycle `npm test` | **111 / 111 通过**（迁移前后一致） |
| `npx tsc -b` | 通过 |
| `npm run build` | 通过（55 modules，225.82 kB） |
| Research `validate_db.py` | PASS |
| Research `validate_timeline_export.py` | PASS（8 Campaigns / 2 Candidates / 26 Events / 39 Securities） |
| Research `validate_batch_research.py` | PASS（PROVISIONAL 8 / CONFLICT 1） |
| Research `validate_promotion_manifest.py` | PASS（5/5） |
| Research `check_doc_schema_consistency.py` | PASS（17 表 / 125 字段） |
| 历史研究 semantic diff | **未修改文件 zero diff**；仅 3 个脚本路径调整 |
| canonical export 哈希 | 迁移前后**完全一致** |

### 明确未做

- 未修改 Research Model v1.0 / `schema.sql` / 历史研究结论
- 未新增数据库实体 / ThemeCycle / CampaignRelation schema
- 未新增 UI 功能 / Dashboard / Statistics / Prediction / Radar / Notification / Backend
- 未重新生产 Research 数据
- 未删除任何测试
- 未 force push

---

# 以下为原 `Cycle/docs/CHANGELOG.md` 历史（完整保留）

## 2026-09-13 · V1.7 Historical Opportunity Map UX（第十一轮）

### 目标

用户打开页面 5 秒内回答"现在这个时间点，历史上通常发生什么"，
并进一步理解"这些行情为什么开始 / 加速 / 转折 / 结束"。
**精确日期不再作为主要视觉信息**（窗口优先于日期）。
未修改核心数据模型与 TimelineExportV1 Contract。

### 1. Phase Window（窗口优先于精确日期）

- **Adapter**：`peakWindowOf(campaign)` →
  - 正常峰值：peak ± 7 天（`PEAK_WINDOW_HALF_DAYS`）；
  - 轻微峰值分歧（≤ 阈值）：候选 A → B 构成窗口（`disputed: true`）；
  - 严重峰值分歧：返回 null（交由双候选标记 ▲ᴬ / ▲ᴮ 表达，V1.6.2 视觉保留）。
- **Timeline**：Campaign 行上方渲染 Peak Window 窄条（悬停显示完整窗口日期）；
  分歧窗口用斜纹 + 虚线边框区分；Detail 抽屉仍显示 Exact Dates 与候选 A / B。

### 2. Date Conflict 分级（轻微不喧宾夺主）

- **Adapter**：`conflictSeverity(conflict)` → minor（候选间隔 ≤ 10 天，
  `MINOR_CONFLICT_THRESHOLD_DAYS`）/ major（> 10 天，跨月份或影响生命周期判断）。
- **Timeline**：只有 major 冲突使用 V1.6.2 大型 Conflict 视觉
  （主体斜纹 + Start/End 分歧信封）；minor 冲突显示 Peak Window 并在
  tooltip / Detail 保留 Candidate A / B 双方口径，不画大型 Conflict。
- 测试断言：2024 peak（07-29 vs 08-05，7 天）= minor；2022 start
  （04-27 vs 05-23，26 天）= major；边界 10 天 = minor、11 天 = major。

### 3. 驱动因素四问（Campaign Detail）

- **Adapter**：`campaignDrivers(campaign)` 从 Campaign 关联研究事件按时间归组：
  - 启动 [start-30, start+15] / 加速 (start+15, peak-7] / 转折 [peak-10, peak+10] /
    结束 [end-25, end+7]（openEnded 候选不归组结束，end 为年末近似）；
  - 每组最多 3 个标签，trigger / catalyst 角色优先；无 peak 时以区间中点近似转折位置。
- **CampaignDetail**：新增「驱动因素（为什么）」区块——为什么启动 / 加速 / 转折 / 结束；
  无事件落入的组显示「暂无可靠归因」（不编造）；标注"时间归组线索，非因果结论"。
- Timeline 主轴不显示 Drivers（保持简洁，详情才展开）。

### 4. 历史同周期查看（轻量 Year Comparison）

- **Adapter**：`samePeriodWindow(year, month)`（选中月份 → [m-1 月 15 日, m+1 月 15 日]
  两个月宽窗口，跨年自动处理）+ `samePeriodCampaigns(source, month)`
  （各年份与窗口相交的 Campaign 列表，仅日期相交匹配，**不是统计模型 / 相似度评分**）。
- **新组件 SamePeriodView**：月份选择（默认当前月）+ 历史各年同期 Campaign 列表；
  RC 候选带徽章、非 verified 状态虚线淡化；空年份显示「无同期行情」；
  文案明确"仅历史列表，不构成任何预测"。
- **App**：接入 Timeline 下方（单一页面流，不加新仪表盘）。

### 边界（不变量）

- Production（verified 空态）/ Preview（Research 导出）隔离不变：同周期查询
  在生产数据源下不消费 preview 数据（测试断言）；
- TODAY 仅表示日期位置，≠ 当前市场状态；
- 不实现实时资金流 / AI 预测 / 股票推荐 / 胜率 / 相似度评分 / 自动埋伏建议 / 通知 / 后端；
- 未修改 src/models/ 核心模型、TimelineExportV1 Contract、RC 并列语义。

### 测试

- 93 → 108 项：新增 15 项（Peak Window 3 / 冲突分级 4 / 驱动因素四问 4 /
  历史同周期 4，含 preview/production 隔离与空态 fallback）。
- `npm test` 108/108 通过；`npx tsc -b` 通过；`npm run build` 通过。

## 2026-09-13 · V1.6.2 附：Conflict Campaign Timeline Visualization（第十轮）

### 问题

C-2024-ROBOTAXI 等冲突行情的时间轴主体使用 Candidate A 日期（07-08 → 07-31），
仅附 ⚠ 警示——视觉上暗示 07-31 = 已确定 End。研究分歧被弱化为"警告"而非"未定"。

### 修复：conflict 视觉语义 = "日期尚未确定"

- **Adapter**：新增 `getConflictBoundaryCandidates(campaign)`（视图辅助函数，从
  conflicts 推导 start / peak / end 的 A/B 候选日期，升序去重，不做任何取舍）；
  **未修改 TimelineCampaign 核心模型**。
- **Timeline**（仅 status = conflict 启用新视觉；verified / provisional / preview 不变）：
  - 主体条：低透明度 + 白色斜纹（`st-conflict-visual`），表达"非确定状态"；
  - **Start 分歧**：A → B 区间渲染"起点研究分歧区间"信封（虚线边框 + 斜纹），
    两端 A / B 候选 marker（竖线 + 字母）；
  - **Peak 分歧**：渲染 ▲ᴬ / ▲ᴮ 两个峰值候选标记（tooltip：Peak Candidate A/B）；
  - **End 分歧**：从 Candidate A 到 B 渲染"End 候选区间"dotted 延伸（非正式延续），
    两端 A / B 候选 marker；不再让 07-31 视觉上成为绝对 End。
- **CampaignDetail**：完整日期标注"日期存在研究分歧，A / B 候选见下方；
  本区间为 DB Candidate 口径"；研究分歧按 起点 / 峰值 / 终点 字段排序显示。
- **labels**：`CONFLICT_FIELD_LABEL`（start_date→起点 等）；
  `conflictLine` 显示中文字段标签。
- 均不依赖颜色（形状 / 线型 / 字母 / 斜纹区分）。

### 边界（不变量）

- 不自动选择 Candidate A 或 B（测试断言正式字段 = A 且候选集含双方）；
- 未修改 Research Export / TimelineExportV1 / 核心模型 / RC 逻辑；
- RC Candidate 不因 conflict 升级为 verified。

### 测试

- 83 → 93 项：新增 `getConflictBoundaryCandidates` 10 项
  （start 2 候选 / peak 2 marker / end 2 候选 / 非 conflict 全 null /
  2022 start 保留 / 2024 peak 保留 / 2024 end 保留 / 不自动选择 /
  保持 conflict 状态 / verified·provisional·preview 不受影响）。

## 2026-09-13 · V1.6.1 Real Research Export Integration（第九轮）

### 目标

Cycle-Research 2018—2025 历史研究数据（timeline_export_v1，canonical Contract v1.0）
真正进入 Cycle Timeline MVP。**未修改核心数据模型**（src/models/ 零改动），
全部经 Timeline Adapter 层解决。

### Canonical Contract v1.0 接入

- `timelineTypes.ts`：`TimelineExportV1` 与 Research 冻结 Contract（Research commit
  4bbe257）11 字段白名单对齐；新增 `ExportCampaignV1` / `ExportCandidateV1` /
  `ExportSignalV1` / `ExportEventV1` / `ExportSecurityV1` / `ExportConflictV1`。
  旧字段（export_version / source_project / purpose）不再兼容，Cycle 内不维护第二套 v1 格式。
- `timelineAdapter.ts` `validateTimelineExportV1`：只验证 Cycle 实际消费的部分——
  顶层白名单（未知字段拒绝）、version / contract、campaigns（必填字段 +
  status ⇔ research_status 一致性 + CONFLICT ⇔ conflicts）、research_candidates
  （无生产 status + ID 不与 formal campaigns 冲突）、events（唯一 ID + 归属回指）、
  signals（campaign_id XOR research_candidate_id）、securities（恰好一个 owner）、
  event_ids / security_ids 引用完整性。非法数据抛错并携带问题清单。
- 修复：顶层校验只在「缺少必填字段」时提前返回（未知字段不阻断后续 version 检查）。

### 真实导出替换手工 fixture

- `src/data/timeline/data/timeline_export_v1.json`：Cycle-Research 导出的逐字节拷贝
  （source_commit 49797cc；8 条正式 Campaign + 2 条 Research Candidate +
  26 事件 + 9 信号 + 39 证券）。**Cycle 只消费、不修改**；业务结构变更回 Research 项目。
- `timelinePreview.ts`：静态 import JSON（tsconfig 开启 resolveJsonModule），
  无运行时网络请求，静态 PWA 不变。

### Adapter 映射（Research Export → Timeline）

- 正式 Campaign：research_status → 状态（PROVISIONAL→provisional / CONFLICT→conflict /
  VERIFIED→verified）；first_decline_date 作回撤起点（缺省 peak→end 中点近似）。
- Research Candidate（RC-2023-HUAWEI / RC-2024-SECONDARY）：kind = candidate，
  status 只为 preview / conflict（永不 verified）；与正式 Campaign 并列展示，
  非升级关系；end_date 缺省时 openEnded = true（end 为年末近似，仅渲染）。
- Signals：EARLY_SIGNAL 且早于正式起点 → TimelineEarlySignal（淡显 / 虚线）；
  全部研究信号进入详情（类型 + 置信度）。研究信号是"值得观察"，不是交易信号。
- Events / Securities：顶层扁平数组 + owner 引用；Adapter 建 lookup
  （eventById / securitiesByOwner / signalsByCampaign / signalsByCandidate）解析，
  不要求嵌套在 Campaign 内。
- 年份自动推导：campaigns + research_candidates + events → 连续区间 2018—2025
  （2018 反例年份可见、无 Campaign、空态合法，不编造行情）。

### UI

- Timeline：研究事件行（.evt-chip.res 虚线暖色区分日历事件；tooltip 含归属 +
  「非正式历史事实」）；Candidate RC 徽章；conflict tooltip 用 `conflictLine`
  结构化显示（修复对象数组误拼 [object Object]）；空态文案
  「该年份当前无正式 Historical Campaign 数据」。
- CampaignDetail：结构化研究分歧（⚠ field：A date（label） vs B date（label），
  保留双方不自行取舍）；关联事件（日期 + 类型 + 角色）；研究信号（类型 +
  置信度 + "不是交易信号"注明）；Research Candidate 徽章与说明；openEnded 文案；
  证券显示 ticker。
- App：researchEvents 透传；预览横幅带 Research 源 commit；初始年份回退
  （preview 源 2018—2025、当前 2026 → 打开即显示 2025，而不是空白年）。
- `labels.ts`：SIGNAL_TYPE_LABEL / SIGNAL_CONFIDENCE_LABEL / EVENT_TYPE_LABEL +
  `conflictLine`（A/B 双方口径单行文本）。

### 数据边界（不变量）

- timeline_export_v1.json 只存在于 src/data/timeline/data/，不写入 data/ 任何目录；
- Research Candidate / preview 数据不进入 allCampaigns / verifiedCampaigns /
  campaignById（测试断言保证）；
- 核心数据模型（HistoricalCampaign / Rule / Theme / Security 等）零修改。

### 测试

- 66 → 81 项：重写 timelineAdapter 测试，覆盖 Contract 校验（真实导出通过 /
  export_version 拒绝 / source_project 拒绝 / version 必须 1.0 / 未知字段拒绝 /
  status 一致性 / candidate 无生产 status / signals XOR / 引用缺失）、
  年份推导（2018—2025 全可见 / 2018 空态 / 2019—2025 有数据）、
  Conflict（2022 start 分歧 04-27 vs 05-23 / 2024 peak+end 双分歧）、
  Candidate（kind=candidate / 不进生产 / 与 Campaign 并列共存）、
  徽章（preview 来源标注 / conflict 携带分歧）、引用解析（events / securities /
  signals 挂正确主体）、verified 隔离与跨年回归、生命周期分段推导。

## 2026-09-13 · V1.6 Cycle Timeline MVP：时间轴 + 历史对比 + 提前观察（第八轮）

### 目标

Timeline MVP：365 天全年时间轴（真实日期比例）、Campaign 生命周期视觉主体、
Preview / Production 数据源分离。**未修改核心数据模型**（无 ThemeCycle /
CampaignRelation / CampaignPhase，HistoricalCampaign 未动），全部经 Timeline
Adapter 层解决。

### 新增：Timeline Data Adapter（src/data/timeline/）

- `timelineTypes.ts`：`TimelineDataSource` 接口（kind: verified | preview）、
  `TimelineCampaign` 视图模型、生命周期分段（early_signal / main_rise / peak /
  retracement / declining / ended）、数据状态（verified / provisional / preview /
  conflict）、`TimelineExportV1` 导入格式。
- `timelineAdapter.ts`：
  - `verifiedTimelineDataSource`：生产数据（data/verified/ 的 allCampaigns /
    themes / securities + data/candidate/events.ts）→ 视图模型；
  - `previewTimelineDataSource`：Research 预览 fixture → 视图模型；
  - `fromTimelineExportV1`：timeline_export_v1.json 本地导入 Adapter（不 fetch
    GitHub，静态 PWA 不变）；
  - `derivePhases`：由 start / peak / end / retracement_start 推导生命周期分段
    （retracement 缺省以 peak→end 中点近似，仅渲染用）。
- `timelinePreview.ts`：2022 Auto Policy / 2023 Smart Driving（Huawei Auto
  Research Candidate）/ 2024 Robotaxi 三个已研究案例的 preview fixture，
  `status = preview`（2023 华为案例标 conflict 供分歧视觉验证）。
  **不进入 data/verified、不污染 allCampaigns**（测试断言保证）。

### UI：Campaign 生命周期 + Preview 模式

- Timeline 第三层（Campaign）成为视觉主体：
  - 生命周期分段渲染：主升实色 → 高位回撤条纹 → 退潮虚线纹理；
  - Peak 三角标记 + Peak Cluster；Early Signal 淡显于 Campaign 前方
    （虚线边框 + 降低透明度，标注「前置观察，非正式行情起点」）；
  - provisional / preview 虚线淡化；conflict ⚠ 警示标记；
  - 跨年延续箭头（◂ ▸）沿用现有逻辑。
- App：`?preview=1` 启用 Preview（默认生产数据）；预览横幅「开发预览数据，
  非正式历史事实」+ 返回生产数据链接；生产层为空时显示空态 +
  「开发预览：查看 Research Preview」入口；年份切换接入数据源（不硬编码年份）。
- CampaignDetail：归一化生产 / 预览两种输入；预览数据明确标注
  「Research Preview · 非正式 Verified 数据」；conflict 展示研究分歧描述。
- 提前观察中性表达：OpportunityRadar 改为「历史观察窗口将在约 N 天后进入」
  等中性文案（无买卖建议用语）。
- 样式：形状 / 线型 / 透明度 / 标签区分生命周期（不单靠颜色，避免色盲不可分辨）。

### 数据边界（不变量）

- Preview fixture 只存在于 src/data/timeline/，不写入 data/ 任何目录；
- allCampaigns = verifiedCampaigns（生产聚合不含 preview，测试断言）；
- 核心数据模型（HistoricalCampaign / Rule / Theme 等）零修改。

### 测试

- 52 → 66 项：新增 Timeline adapter 测试 14 项，覆盖：
  preview 数据不进入 allCampaigns / verifiedCampaigns / campaignById、
  verified 数据源空态、年份推导、日期比例定位（非 12 等分）、跨年分段、
  preview 徽标、conflict 徽标、TODAY 定位、生命周期分段推导（含 retracement
  中点近似与无 peak 回退）、timeline_export_v1 导入兼容。
- 既有 Timeline 渲染测试更新为新 props 签名（campaigns + sourceKind）。
- 验证：`npm test` 66/66 通过；`npx tsc -b` 通过；`npm run build` 成功。

---

## 2026-09-12 · Pilot 1 录入入口准备：verified 层数据录入路径（第七轮）

### 目标

为人工核验「6—8月汽车」提供干净、可追溯的 verified 录入路径。**本轮未录入任何
真实历史数据**（无 2023/2024 汽车 Campaign、无真实龙头 / 涨幅 / 日期），
verified 层保持空状态。

### 新增：Verified Campaign 录入流程（HISTORICAL_VALIDATION.md 12B）

标准流程：先登记 Evidence → 人工确认事实 → 创建 HistoricalCampaign →
写入 `data/verified/campaigns.ts`（含配套 themes / securities 关联）→
Campaign 必须至少被一条 Evidence 追溯（evidencesOfCampaign）→ 新增 campaign 级
ValidationRecord（scope = 'campaign'、L2）→ Rule 保持 not_tested / under_review。
明确「某一年 Campaign 被核验 ≠ 整条 Rule 已经验证成立」。

### 补齐：verified 层龙头关联落脚点

- `data/verified/campaigns.ts` 新增 `verifiedCampaignSecurities`（空表）：
  人工核验后的真实龙头（CampaignSecurity）有明确归宿，不落入 candidate 层。
- barrel 新增聚合导出 `allCampaignSecurities`（candidate 恒空 + verified），
  CampaignDetail 改用聚合导出——verified 数据录入后 UI 自动可见，当前无视觉变化。

### 修复：validationByRuleId 键冲突隐患

- 该索引以 rule_id 为键；campaign 级记录与所属 Rule 的 rule_id 相同，
  直接全量建 Map 会在追加 campaign 级记录后覆盖 rule 级记录。
  改为只索引 `validation_scope = 'rule'` 的记录（1 行防御性修复，当前无生产消费方）。

### 三层关联链确认

Evidence（campaign_id 反向指向）→ HistoricalCampaign（verifiedCampaigns）→
ValidationRecord（scope = 'campaign' + L2）已可闭环，模型未做任何修改。

### 测试

- 49 → 52 项：新增「Pilot 1 录入入口准备」3 项（verified 三张表与聚合层全空、
  validationByRuleId 只索引 rule 级记录、录入链路演练——fixture 验证
  campaign + evidence(campaign_id) + campaign 级记录的关联约束，不入生产层）。
- 验证：`npm test` 52/52 通过；`npx tsc -b` 通过；`npm run build` 成功。

---

## 2026-09-12 · V1.5 Final Preparation：进入历史核验前的最后语义准备（第六轮）

### 修正：Source URL

- `src_exp_001` URL 由知乎问题页（question/464198498）修正为核对后的原始来源
  `https://www.zhihu.com/question/663265687/answer/3583512483`；
  title / author 等其他字段不变，未新建 source_id。

### 修正：「国庆后→春节前」复合时间窗口的近似表达

- `rule_consumption_year_end` / `rule_education_year_end` / `rule_textile_year_end`
  的窗口（10-08 → 01-31，empirical）实为复合窗口：固定起点 + 相对春节终点。
  **不扩展 TimeWindow Schema**，采取最小近似表达：
  - TimeWindow 新增 `approximate?: boolean` 字段（src/models/timeWindow.ts）；
  - 三条窗口标记 `approximate: true`，note 说明终点随春节浮动；
  - 新增共享 `windowRangeLabel()`（src/components/labels.ts）：approximate 窗口
    一律渲染为「约 … → …（近似）」，RuleDetail / Timeline tooltip / OpportunityRadar
    三处统一接入，**UI 不再把 01-31 显示为精确结束日**。
- 决策记录写入 DATA_MODEL.md（第 3 节）与 HISTORICAL_VALIDATION.md（12A）：
  国庆后→春节前属于复合时间窗口，V1.5 暂采用近似表达，后续统一支持
  mixed anchor window。

### 新增：ValidationRecord.validation_scope（Rule ≠ Campaign）

- 模型新增 `validation_scope: 'rule' | 'campaign'`：
  - `'rule'`：验证整条 Rule，campaign_id 省略；
  - `'campaign'`：验证具体 HistoricalCampaign 的历史事实，campaign_id 必填。
- data/validation/records.ts 三条 Pilot 记录均置 `validation_scope: 'rule'`。
- 语义写入 AGENTS.md（核验范围章节）、DATA_MODEL.md（第 12 节）、
  HISTORICAL_VALIDATION.md（第 10 节），并强调 L2 ≠ statistically_supported。

### 新增：Evidence → Campaign 查询

- `evidencesOfCampaign(campaignId)`（data/validation/evidence.ts，经 barrel 导出），
  与既有 `evidencesOfRule` 并列；UI 统一从 src/data/index.ts 使用。
- 明确不变式：未来 verified Campaign 必须能追溯到至少一条 Evidence
  （已入防回归测试，verified 层有数据后自动生效）。

### 新增：Campaign 判定方法论与失败年份原则

- HISTORICAL_VALIDATION.md 新增「1A. Campaign 判定原则 V1」：
  不能仅因行业上涨建 Campaign（持续性 / 可识别主题 / 市场关注 / 可解释起止
  四项齐备）；Theme Campaign 与 Industry Trend 区分（当前只研究前者）；
  启动 / 结束 / 强度 / 结果的判定字段；第一阶段人工核验、不设数学阈值。
- 第 4 节新增「失败年份原则」：核验必须主动寻找成功 / 弱 / 失败 / 无行情
  四类年份，防 survivorship bias 与 confirmation bias。

### 测试

- 43 → 49 项：新增「V1.5 Final Preparation」6 项（scope 约束不变式、当前全为
  rule scope、evidencesOfCampaign 注入查询、verified Campaign 证据可追溯不变式、
  approximate 窗口 + windowRangeLabel 文本、三层行情全空）；Source URL 测试
  收紧为精确 URL + title/author 不变断言。
- 验证：`npm test` 49/49 通过；`npx tsc -b` 通过；`npm run build` 成功。

### 未做（按任务边界停止）

- 未查询行情、未新增 2023/2024 汽车真实 Campaign、未加真实龙头 / 涨幅 /
  胜率 / 季节性分数；未开始实际历史核验。
- 下一轮正式进入：Pilot 1「6—8月汽车」历史事实核验（先核验事实，不是证明规律成立）。

---

## 2026-09-12 · V1.5 第零阶段：Preflight 数据语义清理（第五轮）

### 修复：示例数据进入生产历史行情层

- `cmp_media_2026_2027`（需求文档跨年结构示例 2026-11-01 → 2027-01-15）从
  `data/candidate/campaigns.ts` 移至 `tests/fixtures/campaignFixtures.ts`。
  生产层不再展示结构示例；跨年渲染测试改用 fixture，测试语义不变。
  禁止测试数据回归 `data/` 目录。

### 修复：未核验 Candidate Campaign 伪装"历史行情"（方案 A）

- `cmp_auto_2023` / `cmp_auto_2024` 从生产层移除：材料提及的年度题材
  （2023 汽车=减速器、2024 汽车=自动驾驶）仅保留在 data/validation/evidence.ts
  的 Evidence 记录中，避免 inferred/low 日期被误读为历史事实。
- `data/candidate/campaigns.ts` 置空：candidate 层不再承载未核验 HistoricalCampaign；
  人工核验完成的真实行情直接写入 `data/verified/campaigns.ts`（L2）。
- `src/data/index.ts`：生产层聚合改为 `allCampaigns = [...verifiedCampaigns]`。

### 修复：Timeline 第三层语义

- 层标题「历史题材 / 历史行情」→「已核验历史行情」；
  数据源由 candidate `campaigns` 改为 `allCampaigns`（verified）。
- 空态文案：「暂无已核验历史行情（历史核验尚未开始）」。

### 修复：ValidationRecord 审计字段语义

- 模型（src/models/validation.ts）：新增 `created_at`（记录建立日期）；
  `reviewed_at` 改为 `string | null`（人工核验完成日期）。
- 未审核状态：`reviewer = 'pending'` 且 `reviewed_at = null`——
  没有核验人就不得有核验完成日期。data/validation/records.ts 同步更新。

### 新增：A 股市场日期基准 Asia/Shanghai

- `marketTodayISO()`（src/utils/date/dateUtils.ts）：A 股"今天"固定基于
  Asia/Shanghai（原生 Intl，零新依赖），不随用户机器时区漂移；
  App 的 TODAY / Pre-heat / OpportunityRadar 统一接入。
- 纯日期运算（diffDays / addDaysISO 等）保持 UTC，与市场日期基准分离。

### 补充：Source URL

- `src_exp_001` 补登记原始来源 URL（知乎问题页），title 保持不变（不编造）。
  来源追溯规则写入 DATA_GOVERNANCE.md。

### 审计：Event 日期精度（仅记录，未改数据）

- 逐事件审计结论记入 ROADMAP.md「Event 日期精度治理」：
  两会会期为近似日期被当成确定事实（待改 variable / approximate），
  其余事件（春节 / 披露期 / 法定节假日）建模基本准确。

### 文档修订

- DATA_MODEL.md：ValidationRecord 字段更新（created_at / reviewed_at 语义）、
  差异记录补市场日期基准。
- HISTORICAL_VALIDATION.md：新增 12A「Preflight 数据语义决策」（方案 A 全文）、
  第 10 节审计字段语义、Pilot 表状态更新。
- DATA_GOVERNANCE.md：Source URL 追溯规则、市场日期基准章节、
  种子数据诚信边界更新为 Preflight 后基线。
- ROADMAP.md：V1.5 第零阶段记录 + Event 日期精度治理待办。

### 测试

- 33 → 43 项：新增「V1.5 Preflight：生产层数据语义」7 项
  （示例不属生产层、候选不进 allCampaigns、聚合=verified、广电零 Campaign、
  Source URL、reviewer/reviewed_at 不变式、Timeline 空态渲染）
  与「测试 fixture 语义」8 项（fixture 存在性、跨年双视图延续、日期约束、
  unknown/null 合法、引用完整、Base/Annual 并存、一 Base 多 Theme、failed 标签）；
  新增 marketTodayISO Asia/Shanghai 确定性测试 4 项（含中国午夜边界）。
- 验证：`npm test` 43/43 通过；`npx tsc -b` 通过；`npm run build` 成功。

### 未做（按任务边界停止）

- 未接行情 / AkShare / Tushare；未做回测、季节性评分、胜率、SQLite、
  实时数据、AI、历史相似度、新页面、消息推送；未开始批量历史核验。
- 下一轮等待人工启动：「Pilot 1：夏季汽车历史事实核验」。

---

## 2026-09-12 · V1.5 第一阶段：历史规律核验基础建设（第四轮）

### 新增：核验规范与数据结构

- `docs/HISTORICAL_VALIDATION.md`（新）：Historical Campaign 定义（含 peak_date）、
  启动/结束日期判定（observed / inferred / official_event / unknown + confidence）、
  结果分类（允许失败年份）、Base Pattern ≠ Annual Theme、Cross-Year 规则、
  Evidence 概念、人工优先原则、统计预留（本轮不计算）。
- 模型新增：`Evidence`（src/models/evidence.ts）、`ValidationRecord` / `PilotPlan`
  （src/models/validation.ts）、`RawExcerpt`（src/models/source.ts）。
- `HistoricalCampaign` 扩展可选字段：peak_date、start_date_basis、end_date_basis、date_confidence。
  既有种子数据回填真实判定：cmp_auto_2023/2024 = inferred/low，cmp_media_2026_2027 = unknown/low。

### 新增：data/ 四层数据目录（自 src/data 迁入）

```
data/raw/        sources.ts（来源注册表）、excerpts.ts（材料原文摘录，13 条）
data/candidate/  rules.ts、campaigns.ts、themes.ts、events.ts（V1 种子整体迁入）
data/verified/   campaigns.ts（L2 已核验事实，当前 0 条）
data/validation/ evidence.ts（6 条证据）、records.ts（3 条核验记录）、pilot.ts（3 条 Pilot）
```

- `src/data/index.ts` 改为纯 re-export barrel，所有应用代码 import 路径不变，零 UI 改动。
- 诚信处理：材料"提及广电 2021/2022/2023"但无任何细节 → 仅登记 L1 证据线索，
  **不创建 Campaign**（防编造最小事实原则）。

### 3 条 Pilot 核验数据骨架

| Pilot | evidence_status | verification_status | 说明 |
|-------|-----------------|---------------------|------|
| 夏季汽车 | L1 | not_tested | 材料：2023减速器 / 2024自动驾驶；候选 Campaign 日期 inferred/low |
| 年底广电 | L1 | not_tested | 材料：2021—2023 年份提及，无细节，未建 Campaign |
| 国庆后大消费 | L0 | not_tested | 仅经验窗口，无年份案例证据 |

### 文档修订

- AGENTS.md：概念链加入 Evidence；阅读顺序加入 HISTORICAL_VALIDATION.md；
  data/ 修改留痕义务。
- DATA_MODEL.md：新增第 11/12 节（Evidence / ValidationRecord / PilotPlan）、
  Campaign 字段更新、数据位置说明。
- DATA_GOVERNANCE.md：Evidence 原则、数据目录治理、V1.5 核验数据基线。
- ARCHITECTURE.md：数据层目录结构、测试覆盖更新。
- ROADMAP.md：V1.5 拆分为三阶段，第一阶段标记完成。

### 测试

- 23 → 33 项（新增「V1.5 核验数据完整性」10 项：证据引用、跨年日期约束、
  unknown/null 合法性、L2 ≠ statistically_supported 不变式、失败年份不过滤、
  Base Pattern 与 Annual Theme 并存、一 Base 多 Theme、Pilot 骨架、verified 层为空、
  仅年份提及不产生 Campaign）。
- 验证：`npx tsc -b` 通过；`npm test` 33/33 通过；`npm run build` 成功。

### 未做（按阶段边界停止）

- 未做历史行情数据接入 / 全市场回测 / 自动识别 Campaign / UI 改造 / SQLite 迁移。
- 3 条 Pilot 的历史事实核验等待人工 Review 后启动。

---

## 2026-09-12 · 规范微调（第三轮）

规范微调：区分 Evidence Status 与 Verification Status；重新定义前瞻性分析与确定性预测的边界。

### 文档修改（仅文档，未改业务代码）

- `AGENTS.md`
  - 第 2 节新增「两个独立维度：证据 ≠ 验证」（Evidence L0–L4 / Verification 五态，强调 L2 ≠ 规律成立）。
  - 「永不输出预测」改写为「前瞻性分析 ≠ 确定性预测」：禁止确定性预测/保证收益/买卖建议/必涨必跌/自动交易信号；
    允许历史统计、情景分析、前瞻性观察窗口。
  - 第 6 节红线同步补充。
- `docs/DATA_GOVERNANCE.md` — 数据等级重构为 Evidence Status + Verification Status 双维度，
  增加与当前 `Rule.status` 字段的映射表（字段拆分列入 ROADMAP，本轮不改代码）。
- `docs/DATA_MODEL.md` — Rule 章节与差异记录补充双维度说明。
- `docs/PRODUCT.md` — 新增「前瞻性分析 ≠ 确定性预测」章节（禁止项 / 允许项 / UI 文案边界）。
- `docs/ROADMAP.md` — V1.5 补充双字段评估与"历史统计特征"表述约束；V3 改为情景分析框架表述。

### 业务代码

- 无修改。现有 `Rule.status` 字段与新双维度语义无冲突（映射表已记录，拆分留待 V1.5）。

### 验证

- `npm test`：23/23 通过。
- `npx tsc -b`：通过。

---

## 2026-09-12 · 规范补救与架构一致性检查（第二轮）

### 新增（治理文档体系）

- `AGENTS.md` — 项目宪法：定位、数据认知边界（Source ≠ Rule ≠ Historical Fact ≠ Verification ≠ Prediction）、
  Agent 开发原则、冲突处理、最小修改原则、产品红线。
- `docs/PRODUCT.md` — 产品定义：核心价值、核心对象、四层时间轴、跨年原则、V1 不做清单。
- `docs/DATA_MODEL.md` — 10 个实体的当前实际字段 + 差异记录。
- `docs/DATA_GOVERNANCE.md` — 数据等级 L0–L4、Source 原则、禁止行为、「缺少数据是合法状态」、种子数据诚信边界。
- `docs/ARCHITECTURE.md` — 当前实际架构（非理想状态）：技术栈、组件结构、跨年/Pre-heat 实现方式、测试方式。
- `docs/UI_SPEC.md` — UI 原则：时间轴为视觉中心、四层视觉、跨年延续表达、文案红线。
- `docs/ROADMAP.md` — V1 / V1.5 / V2 / V3 / V4 阶段划分。

### 边界明确

- Source / Rule / Historical Fact / Verification / Prediction 的语义边界写入 AGENTS.md 第 2 节。
- 跨年规则（自然年只是显示容器、Campaign 不得拆条）写入 PRODUCT.md 与 DATA_MODEL.md。

### 代码修改（最小修复）

- `src/components/RuleDetail/RuleDetail.tsx`
  - 修复：相对事件窗口的详情文案原样显示内部 ID（`evt_spring_festival`），
    现通过 `eventById` 解析为事件名（「春节」）。属于数据语义/可用性 Bug 的最小修复。

### 测试

- 扩展 `src/utils/__tests__/timeline.test.ts`：18 → 23 个用例，新增「数据治理规范」分组：
  种子数据零 verified、缺失案例返回空数组、CampaignTheme 引用完整、缺失关联不抛异常、
  跨年种子行情双视图年延续分段。
- 未引入第二套测试框架。

### 未做的事

- 未重构任何业务模块；未改变产品定位；未接入实时行情/资金流/AI；未新增功能。

---

## 2026-09-12 · V1 第一阶段开发（第一轮）

- 初始化 Vite + React 18 + TypeScript 项目。
- 建立 10 个实体数据模型（`src/models/`）。
- 录入种子数据：2 来源 / 16 题材 / 7 事件 / 10 候选规律 + 窗口 / 3 历史行情。
- 实现四层时间轴、TODAY、跨年延续渲染、Pre-heat 四态、详情抽屉、未来关注窗口。
- 建立 18 个 Vitest 单元测试。
