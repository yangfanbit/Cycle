# PROJECT_STATE.md — ThreeC

> 接班必读②（读完根 `AGENTS.md` 后读本文件）。
> 一页到两页，覆盖接手所需的全部状态。**不要**为理解项目而通读其他文档。

---

## Project Purpose

**ThreeC = A股历史机会时间轴 / 历史机会地图。**

让用户回答：今天在一年中的什么位置 → 历史上这个时间发生过什么 → 主题如何形成 / 发展 /
转折 / 结束 → 有没有提前信号 → 为什么启动 / 加速 / 转折 / 结束 → 哪些方向值得继续研究。

**核心价值 = 机会发现，不是交易决策。** 用户自己负责基本面 / 技术面 / 选股 / 入场时机。
详见 `docs/PRODUCT_PURPOSE.md`。

---

## Current Phase

**Phase 6：Product Core v2（IMPLEMENTED）。**
把 Timeline + Historical Same Period + Current Time Lens 升级为**当前研究导航层**，
并首次具备「生命周期相似」检索能力。

IA（视觉优先级 `Timeline > Current Lens > Similar Phase`）：
1. **① Timeline**（第一视觉，未改动）
2. **② 当前时间研究导航（Current Time Lens v2）** 三层：
   - **A. A股整体环境** → `A股整体周期：Unknown`（ThreeC 没有整体市场周期模型，
     **绝不**从行业 Campaign 反推大盘牛熊）
   - **B. 当前 Theme / Theme Cycle** → 无当前年份数据时**诚实空态**
     （「暂无 2026 当前 Theme Cycle 研究数据；历史研究覆盖至 2025」），
     并列出研究覆盖内的 Theme Cycle（Parallel-aware，历史参考，不冒充当前状态）
   - **C. Research Attention（研究关注）** → 状态分类（**不是评分 / 概率 / 信号**）：
     `当前值得研究` / `保持观察` / `历史参考`
3. **③ 历史相似阶段（Historical Similar Phase v1）** —— **Lifecycle Lens**：
   按「阶段 → Theme Cycle Pattern → Drivers 重叠」检索历史结构相似案例，最多 Top 3，
   用「高相似 / 中相似 / 参考」（**无百分比**），必须给出「为什么类似」；
   找不到足够证据 → 空态，**不强行凑数**
4. **④ 历史同期（Calendar Lens）** —— 既有 `SamePeriodView` 保留并重新定位（日历同期搜索，
   与 ③ 生命周期相似**并存、不可互相替代**）

同时完成 **F-MED-6**：Selection 区分「展示实例」（`entryId`，用于条目高亮 / focus）与
「完整历史案例」（`campaign_id`，用于 Campaign Detail）—— 跨年 Campaign 不再多行同时高亮。

**不做**预测 / 荐股 / 交易信号 / 评分 / 概率 / 实时数据。

---

## Completed

| Phase | 内容 | 状态 |
|---|---|---|
| Phase 1 | Research Model v1.0（冻结） | ✅ |
| Phase 2 | Historical Data Production v1（2018–2025 批量研究） | ✅ |
| Phase 3 | Timeline MVP（+ Conflict Visual / Phase Window / Drivers / SamePeriod / Research Export Adapter / Preview-Production 隔离） | ✅ |
| Phase 4 | Monorepo Integration + Handoff Infrastructure | ✅ |
| Phase 5 | **Current Time Lens v0**（今天入口：时间定位 → 历史同期 → 历史阶段映射 → 可能驱动） | ✅ IMPLEMENTED |
| Phase 5.1 | **V1.8.1 主题级历史机会视图**（IA 重排：Timeline 第一视觉 + 历史同周期主题行 + Lens 降级） | ✅ IMPLEMENTED |
| Phase 5.2 | **V1.8.2 Timeline Detail UX + 提前观察区**（两级详情 / Inline Summary / Bottom Sheet / Pre-observation Window） | ✅ IMPLEMENTED |
| Phase 5.2.1 | **V1.8.2.1 Pre-observation Semantic Fix**（Formation Anchor 优先级 / Early Signal 与 Formation 分离 / 文案改「提前观察参考区」/ 视觉层级降序） | ✅ IMPLEMENTED |
| Phase 5.3 | **Theme / Campaign 分层模型统一审计**（Macro Theme → Theme Cycle → Campaign → Sub-theme；Campaign Independence Gate Q1–Q5；`docs/THEME_CAMPAIGN_MODEL_AUDIT.md`） | ✅ IMPLEMENTED |
| Phase 5.4 | **Research Model v1.1 方法论补丁**（Theme Cycle Pattern A/B/C · Campaign Lifecycle Measurement Rule · Gate Q1 Anti-example） | ✅ IMPLEMENTED |
| Phase 5.5 | **医药健康 Pilot**（Theme Cycle Discovery v0.1 → Campaign Boundary Decision v0.1 → 最小数据集接入：1 正式 Campaign + 2 Research Candidate + 8 行情序列） | ✅ IMPLEMENTED |
| Phase 5.6 | **V1.8.4 F-MED-1** 跨年 Campaign 年份语义修复（明细 `year` = 所属展示年份） | ✅ IMPLEMENTED |
| Phase 5.7 | **V1.9.0 Timeline Entry Identity**（`entryId = campaign_id@display_year`；展示实例 ≠ Campaign 选择） | ✅ IMPLEMENTED |
| Phase 5.8 | **V1.9.1 Timeline Year Coverage Rule**（两源 `years()` 统一为 start→end 连续） | ✅ IMPLEMENTED |
| Phase 6 | **V2.0 Product Core v2**（F-MED-6 Selection 身份分离 · Current Time Lens v2 三层 · Research Attention Gate v1 · Historical Similar Phase v1 · Macro Theme 聚合接口 · IA 重排） | ✅ IMPLEMENTED |

---

## Current Architecture

```
ThreeC/  (单一 Git, origin = yangfanbit/Cycle)
├─ src/                Product：React + TS + Vite (Timeline UI / Adapter / models)
├─ data/               Product 侧核验数据（verified 层当前为空）
├─ exports/            ★ canonical timeline_export_v1.json
├─ contracts/          timeline_export_v1.md（接口契约）
├─ research/           Research 子系统（Python + SQLite）
│   ├─ database/cycle_research.db   （提交 Git）
│   ├─ schema/schema.sql            （冻结）
│   ├─ scripts/                     （Python 流水线）
│   └─ research/                    （研究产物）
├─ docs/               项目级 + 产品级文档
└─ tests/
```

- **History migration**：Cycle 为根（原 11 commits），Cycle-Research 经
  `git subtree add --prefix=research` 并入（原 28 commits）。共 40 commits，
  双方原始 author / date / message 保留。
- **前端消费路径**：`src/data/timeline/timelinePreview.ts` → `@exports/timeline_export_v1.json`
  （Vite alias + tsconfig `paths`）。**不再有** `src/data/timeline/data/timeline_export_v1.json` 副本。

---

## Research Status

- Research Model **v1.0 Frozen**；`schema.sql` 冻结（17 表 / 125 字段）。
- 2018–2025 八年度研究完成：**8 个正式 Campaign + 1 个 2018 反例年份**。
- 研究状态分布：`PROVISIONAL 8 / CONFLICT 1`。
- Research Candidates：`RC-2023-HUAWEI`、`RC-2024-SECONDARY`（永不 verified）。
- 结论：**"6–8 月汽车" = 历史观察窗口（Historical Observation Window），
  Partially Supported，非固定买入窗口**。
  （见 `research/research/summary/auto_2018_2025_final_review.md`）

---

## Product Status

- **页面 IA（V1.8.1 起）**：① **Timeline（第一视觉）** → ② **历史同周期主题** → ③ **当前时间上下文**。
- **Timeline 永远保持第一视觉（V1.8.2 硬约束）**：点击主题 / Campaign **不遮挡** Timeline；
  无大型 modal 覆盖、无永久右侧大面板压缩。
- **两级详情（V1.8.2）**：
  - **Level 1 Inline Summary**：点击主题行 → **就地**展开摘要（主题 / 年份 / 阶段 / 关键阶段 /
    提前观察区 / 可能相关因素 / 数据状态 / RC / Conflict），**不离开主页面**。
  - **Level 2 Full CampaignDetail**：仅点「查看完整历史案例」才打开；保留 lifecycle / 精确日期 /
    日期候选 / conflict / securities / events / evidence / source。桌面为右侧浮层；**移动端为 Bottom Sheet**。
- **提前观察参考区（V1.8.2 / V1.8.2.1）**：`historicalPreObservationDays = 30`
  （**UI / Research browsing buffer**）。
  语义 = 「主题正式形成前可开始关注的时间缓冲区」；**不是**预测 / 买入建议 / 未来信号 / 历史统计事实。
  层级：`Pre-observation Reference → Early Signal? → Theme Formation → Main Rise`。
  - **Formation Anchor（V1.8.2.1 修正）**：`THEME_FORMING.start → BROAD_CONFIRMATION.start →
    Campaign.start → null`；**禁止**取 lifecycle 最早 stage（会把 EARLY_SIGNAL 误认为形成）。
    锚点来源由 `formationAnchorOf()` / `formationAnchor` 暴露。
  - Early Signal 继续使用导出既有 `early_signal` 字段，**不重新推导**，与 Formation 相互独立
    （`earlySignal.start !== formation`，`preObservation.end < formation`）。
  - Timeline 中以**极淡**点划线 + 斜纹 + `opacity 0.4` + `z-index 0` 呈现，
    视觉层级 `Campaign(0.95) > Early Signal(0.5/z-1) > 参考区(0.4/z-0)`，
    不抢 Campaign 主体 / Peak / Early Signal。
  - 文案统一「**提前观察参考区**」，说明「仅用于研究浏览参考，不代表历史平均领先期，也不是买入建议。」
    （禁止「买入区 / 布局区 / 信号区」）。
- **历史同周期主题**（`SamePeriodView`，主题级）：一行 = 一个主主题（`themeRows.ts` 的 `TimelineThemeRow`，
  **纯 UI/Adapter 视图概念，非 DB 实体**）；同主题多条独立行情**不合并**，RC 保留 badge、状态不升级；
  仅**重大冲突**（>10 天）显示 ⚠。
- **当前时间上下文**（`CurrentTimeLens`，③补充摘要）：可提示「今天处于某历史主题的提前观察区」，
  必须附「历史研究位置，不代表本年度预测」。相关因素统一称「**可能相关因素**」。
- Timeline MVP 可用：365 天全年时间轴、Campaign 生命周期视觉、
  Peak Window、Conflict 分级视觉、Drivers 四问。
- **生产模式**：消费 `data/verified/`（当前为空 → 显示「当前研究数据未覆盖」空态 + 预览入口）。
- **预览模式**：`?preview=1` 消费 `exports/timeline_export_v1.json`（2018–2025）。
- `OpportunityRadar` 已**不再被 App 引用**（保留文件，后续统一清理；本轮不删）。
- 测试：`npm test` **282 项通过**（Product Core v2 后 244 → 282，+38）；`tsc -b` 通过；`build` 通过。
- **Current Time Lens v2（V2.0）**：三层 A（A股整体环境 = `Unknown`）/ B（当前 Theme · Theme Cycle，
  无当前年份数据 → 诚实空态）/ C（Research Attention 状态分类）。数据层 `researchAttention.ts`
  （纯 View/Research Navigation，不写 DB/schema/export/contracts）。
- **Historical Similar Phase v1（V2.0）**：`historicalSimilarPhase.ts` —— Phase + Theme Cycle Pattern +
  Drivers 三维度，Top 3 上限、「高/中/参考」分级（无百分比）、必给「为什么类似」、无证据 → 空态。
  与 ④ 历史同期（Calendar Lens）并存。
- **Macro Theme 聚合接口（V2.0）**：`macroTheme.ts` —— 从既有 `theme_type` / `role=related` /
  `parent_theme_id` 推导「Macro Theme → Theme Cycle → Campaigns」；**本轮不改 Timeline 视觉**。
- **F4 已修复（V2.0）**：`theme_type` / `theme_cycle_id` 经 Adapter 透传进视图模型（契约 §11 既有字段，
  未改 export / contract）。
- **Timeline Year Coverage Rule（V1.9.1）**：Campaign / 候选覆盖年份 = `start` 年 **连续到** `end` 年
  （`src/data/timeline/yearCoverage.ts` 的 `timelineYears()`）。`verified` 与 `preview` 两源**同一规则、同一 helper**
  —— 修复生产模式下跨年 Campaign 中间年份行缺失（F-MED-5）。单年度 Campaign 覆盖年份不变。
- **Timeline Entry Identity（V1.9.0）**：明细唯一身份 `entryId = `${campaign_id}@${展示年份}``
  （`src/data/timeline/entryIdentity.ts`，**纯 UI / ViewModel**）。跨年 Campaign 在多年度各成一条明细，
  React key / `focusEntryId` / 年份页签一律用 `entryId`；**打开 Campaign Detail 仍以 `campaign_id` 为准**。
  汽车（单年度）`entryId` 与 `campaign_id` 一一对应 → 视觉与行为不变。
- **F-MED-1 已修复（V1.8.4）**：主题行明细 `year` 取**所属展示年份**（`row.year`），非 Campaign 起始年；
  同步修复同源缺陷 `currentTimeLens.ts` 条目 `year`。跨年 Campaign（医药）行级 `primaryPhase` 恢复正确；
  汽车各行零变化（单年度 `row.year === campaign.year`，恒等）。

---

## Data Status

| 数据 | 位置 | 状态 |
|---|---|---|
| Canonical Export | `exports/timeline_export_v1.json` | **唯一**（SHA256 `BF36FF7B…D01E`） |
| Research DB | `research/database/cycle_research.db` | 3.4 MB，提交 Git |
| Schema | `research/schema/schema.sql` | 冻结（未改） |
| 历史研究产物 | `research/research/**` | **zero semantic diff** |
| 行情 CSV | `research/data/market/**` | 原样保留 |
| Product verified | `data/verified/` | 空（历史核验尚未开始） |

---

## Export Contract

- 唯一版本：`timeline_export_version = "1.0"`
- 契约：`contracts/timeline_export_v1.md`
- 顶层 11 字段白名单；未知字段拒绝。
- Research **生成**，Cycle **消费**。
- Schema 变更必须同时更新 `contracts/` + Research exporter + Cycle adapter。

---

## Known Limitations

- Product 生产层（`data/verified/`）为空：真实历史核验（L0/L1 → L2）尚未开始，
  生产首页目前只能显示空态；实际内容需经 `?preview=1` 查看。
- 所有历史日期为**研究候选日期**，未全部完成人工最终核验 → 标注 provisional / conflict。
- `research/research/` 嵌套目录名为历史遗留，迁移时刻意保留。
- Research 脚本依赖腾讯免费行情接口（仅 `fetch_market_*` 需要网络）。
- `npm audit` 报告 5 项漏洞（构建工具链传递依赖，本轮未处理）。

---

## Current Blockers

**无硬性阻塞。** Phase 6 Product Core v2 已实现并通过全部门禁。

**真实数据限制（不是缺陷，是项目定位的一部分）：**
- A股整体环境（Layer A）为 `Unknown`：ThreeC 没有指数 / 成交量 / 资金 / 情绪数据源，
  也不应由此推导大盘状态。
- 当前年份（2026）无研究数据 → Layer B 为**诚实空态**（研究覆盖至 2025）。
- Research Attention 的 `当前值得研究` 目前为空：现有正式 Campaign 均已记录到结束阶段
  （这不是错误，已在 UI 中明确说明）。
- Drivers 分类只用到 `policy/company/market/macro` → `Sentiment` 在研究数据中**没有来源**，
  因此永不出现（不编造）。

---

## Next Single Goal

> **用户视觉 / 交互 Review（Phase 6 V2.0）。**
>
> 请在真实使用中判断（Product Purpose Check）：
> 1. **Timeline 是否仍是第一视觉？**（Lens 是研究导航层，但不能压过 Timeline）
> 2. **Lens 三层是否读得懂？** A 层 `Unknown` 是否被理解为「诚实的不知道」而不是「系统没做完」？
> 3. **B 层的 2026 空态是否清楚表达了「不用 2025 冒充 2026」？**
> 4. **Research Attention 的三种状态是否不被误读为「推荐度 / 评分」？**
> 5. **历史相似阶段的结果是否让你想去研究某个方向？**（研究入口是否有效）
> 6. **「日历同期」与「生命周期相似」两个视角是否清楚可区分、且都需要保留？**

Review 后可能的方向（**仅供参考，须经授权**）：
- Layer A 若要脱离 Unknown，需先有 A股整体市场周期数据源（**当前明确不做**）。
- Macro Theme 聚合接口已就绪 → 未来可把 Timeline 主单位从 Sub-theme 切到 Macro Theme。
- 更多 Macro Theme（消费 / 电力 / 资源…）的数据生产。

---

## Explicitly Not Doing

本轮及默认状态下**明确不做**：

- 新行业 / 新 Rule / 新统计 / 新 Radar / 新预测 / 新 UI
- Timeline 新功能、UI redesign、Dashboard、Statistics、Notification、Backend
- 修改 Research Model v1.0 / `schema.sql` / 已有历史研究结论
- 新增数据库实体（含 `theme_cycles` / `theme_relations`；`TimelineThemeRow` **仅为视图概念**）
- 新建主题 / 修改 Export Contract / 重新生产 Research 数据
- 新增资金 / 筹码 / 情绪数据（仅保留未来扩展接口）
- 自动升级 verified；把 Research Candidate 当 confirmed
- 改动 `src/models/` 与 Research 侧语义
- 把提前观察区做成「预测 / 买入建议 / 历史统计事实」
- force push
- 删除现有测试
