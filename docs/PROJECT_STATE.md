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

**Phase 5.2：V1.8.2 Timeline Detail UX + Historical Pre-observation Window —— IMPLEMENTED / READY FOR USER EXPERIENCE REVIEW。**

详情改为**两级**：Level 1 就地 Inline Summary（不离开主页面、不遮挡 Timeline）→
Level 2 显式点「查看完整历史案例」才打开完整 CampaignDetail（移动端 Bottom Sheet）。
新增**历史提前观察区**（主题形成前 30 个自然日的**研究浏览缓冲**，非预测 / 非建议 / 非历史统计事实）。
**不做**预测 / 荐股 / 交易信号。

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
| Phase 5.2 | **V1.8.2 Timeline Detail UX + 提前观察区**（两级详情 / Inline Summary / Bottom Sheet / Pre-observation Window） | ✅ IMPLEMENTED / READY FOR USER EXPERIENCE REVIEW |

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
- **历史提前观察区（V1.8.2）**：`historicalPreObservationDays = 30`（**UI research buffer**）。
  语义 = 「主题正式形成前可开始关注的时间缓冲区」；**不是**预测 / 买入建议 / 未来信号 / 历史统计事实。
  层级：`Pre-observation → Early Signal? → Theme Formation`。Timeline 中以**极淡**点划线 + 斜纹 + 低透明度呈现，
  不抢 Campaign 主体与 Peak。文案统一「历史提前观察区」（禁止「买入区 / 布局区 / 信号区」）。
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
- 测试：`npm test` **182 项通过**；`tsc -b` 通过；`build` 通过。

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

**无硬性阻塞。** Phase 5.2 V1.8.2 Timeline Detail UX + 提前观察区已实现，处于
**等待真实用户体验 Review**状态。

---

## Next Single Goal

> **真实用户体验 Review（V1.8.2）。**
>
> 请在真实使用中回答（Product Purpose Check）：
> 1. Timeline 是否仍然是第一视觉？
> 2. 详情是否不再打断时间轴阅读？
> 3. 用户能否先快速理解主题，再决定是否深入？
> 4. 提前观察区是否帮助「提前开始研究」？
> 5. 是否避免把提前观察区误认为预测？
> 6. 是否仍保持「一行一个主题」？
> 7. 是否保持页面简单？

Review 后可能的方向（**仅供参考，须经授权**）：
Phase 5.3 资金 / 筹码 / 情绪 / 广度维度（**仅记录，未实现**）
→ Phase 6 Multi-theme → Phase 7 Current Market Mapping
→ Phase 8 Opportunity Discovery / Radar（**Radar 不是交易信号**）。

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
