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

**Phase 4：Monorepo Integration + Project Handoff Infrastructure —— 已完成。**

单一仓库 `ThreeC`、单一 Git、单一 canonical export、两个逻辑模块（Research + Product）、
一个项目目标。当前**等待下一轮 Review**。

---

## Completed

| Phase | 内容 | 状态 |
|---|---|---|
| Phase 1 | Research Model v1.0（冻结） | ✅ |
| Phase 2 | Historical Data Production v1（2018–2025 批量研究） | ✅ |
| Phase 3 | Timeline MVP（+ Conflict Visual / Phase Window / Drivers / SamePeriod / Research Export Adapter / Preview-Production 隔离） | ✅ |
| Phase 4 | Monorepo Integration + Handoff Infrastructure | ✅ |

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

- Timeline MVP 可用：365 天全年时间轴、Campaign 生命周期视觉、
  Peak Window、Conflict 分级视觉、Drivers 四问、SamePeriodView、OpportunityRadar。
- **生产模式**：消费 `data/verified/`（当前为空 → 显示空态 + 预览入口）。
- **预览模式**：`?preview=1` 消费 `exports/timeline_export_v1.json`（2018–2025）。
- 测试：`npm test` **111 项通过**；`tsc -b` 通过；`build` 通过。

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

**无硬性阻塞。** 处于等待 Review 状态。

---

## Next Single Goal

> **等待下一轮 Review。**
>
> Monorepo Integration 完成后**立即停止**。未经明确授权，不启动任何新功能。

Review 后可能的方向（**仅供参考，须经授权**）：
Phase 5 Historical Opportunity Map 深化 → Phase 6 Multi-theme → Phase 7 Current Market Mapping
→ Phase 8 Opportunity Discovery / Radar（**Radar 不是交易信号**）。

---

## Explicitly Not Doing

本轮及默认状态下**明确不做**：

- 新行业 / 新 Rule / 新统计 / 新 Radar / 新预测 / 新 UI
- Timeline 新功能、UI redesign、Dashboard、Statistics、Notification、Backend
- 修改 Research Model v1.0 / `schema.sql` / 已有历史研究结论
- 新增数据库实体
- 自动升级 verified；把 Research Candidate 当 confirmed
- 重新生产 Research 数据
- force push
- 为迁移引入无必要的新框架
- 删除现有测试
