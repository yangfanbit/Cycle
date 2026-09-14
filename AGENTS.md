# AGENTS.md — ThreeC 接班入口（项目宪法）

> **任何 AI 模型 / Agent / 协作者接手本仓库时，先读本文件，再读 `docs/PROJECT_STATE.md`。**
> 只有在具体任务需要时，才进一步深入 `research/AGENTS.md` 或产品侧文档。
> **不要为了"了解项目"而通读全部文档** —— 本文件 + PROJECT_STATE 已覆盖 90% 的接手上下文。

---

## 1. 项目初心（最高优先级）

**ThreeC = A股历史机会时间轴 / 历史机会地图。**

这个项目最终**不是**：

- 学术型历史数据库
- 炒股预测软件
- 自动荐股 / 选股工具
- 买卖信号系统
- AI 预测系统

**真正目标**——帮助用户回答：

1. 今天处于一年中的哪个时间位置？
2. 历史上这个时间附近发生过什么主题 / 行情？
3. 这些主题通常如何形成、发展、转折、结束？
4. 有没有提前信号？
5. 为什么启动 / 加速 / 转折 / 结束？
6. 通过历史规律，发现当前值得继续研究的方向。

**用户自己负责**：基本面、技术面、个股选择、入场时机。ThreeC 不做这些。

> **核心价值 = 机会发现，不是交易决策。**
> 每个任务开始前先自问：「这个工作是否提高了历史对比与机会发现能力？」
> 如果只是工程复杂化 —— **不要做**。

---

## 2. 当前阶段

**Phase 5.2.1：V1.8.2.1 Pre-observation Semantic Fix（Formation Anchor）（IMPLEMENTED / READY FOR USER VISUAL REVIEW）。**

- Phase 4 Monorepo Integration 已完成：Cycle（产品 / PWA / Timeline 前端）与
  Cycle-Research（研究 / 数据生产）已合并为**单一仓库 `ThreeC`**，单一 Git，保留双方完整历史。
- Phase 5 Current Time Lens v0 已实现（后降级为③补充摘要）。
- Phase 5.1 V1.8.1 已完成：页面 IA 重排为
  **① Timeline（第一视觉）→ ② 历史同周期主题（主题级）→ ③ 当前时间上下文**；
  「历史同期」由「一行一个 Campaign」升级为「**一行一个主主题**」。
- Phase 5.2 V1.8.2 已完成：**两级详情**（Level 1 就地 Inline Summary，点击主题行触发
  `onToggle`，不离开主页面；Level 2 仅「查看完整历史案例」触发 `onSelect` 打开既有
  `CampaignDetail`）；Timeline 恒为第一视觉，不新增大型 modal / 永久右侧大面板；
  移动端详情退化为 Bottom Sheet。新增 **「提前观察参考区」**（`historicalPreObservationDays = 30`，
  UI / Research browsing buffer，代码注释注明「不代表历史平均领先期」）。
- Phase 5.2.1 V1.8.2.1 已完成：修正 Formation Anchor——
  `themeFormationDate()` 按 `THEME_FORMING → BROAD_CONFIRMATION → Campaign.start → null` 取锚点，
  **禁止**取 lifecycle 最早 stage（原实现会把 EARLY_SIGNAL 误认为形成）；
  Early Signal 与 Formation 为**两个独立边界**（Early Signal 沿用导出既有字段，不重新推导）；
  文案「历史提前观察区」→「**提前观察参考区**」；
  视觉层级 `Campaign > Early Signal > 参考区`（opacity / z-index 双降序）。
  **不做**预测 / 荐股 / 交易信号。
- 当前处于 **等待真实用户视觉 Review** 状态。**不继续加功能。**

阶段全景见 `docs/ROADMAP.md`。下一个唯一目标见 `docs/PROJECT_STATE.md`「Next Single Goal」。

---

## 3. 产品 / Research 边界

| | Product（Cycle） | Research（Cycle-Research） |
|---|---|---|
| 位置 | 仓库根（`src/`、`public/`、`package.json`） | `research/` |
| 职责 | Timeline UI、PWA、历史对比、机会发现呈现 | 数据收集、Source、Evidence、Market Data、Campaign、Lifecycle、Drivers、Research Export |
| 不做 | 数据生产、改 Research Model | UI、Timeline 排版、PWA、前端交互 |
| 语言 | TypeScript / React / Vite | Python（标准库 sqlite3） |

**两个逻辑模块，一个项目目标。** 边界必须清晰：Research 只产出数据，Product 只消费数据。

---

## 4. 目录结构

```
ThreeC/
├─ .git/                       ← 唯一 Git
├─ .gitignore
├─ AGENTS.md                   ← 本文件（接班入口）
├─ README.md
├─ package.json / tsconfig.json / vite.config.ts
│
├─ src/                        ← Product：前端源码
│   ├─ components/             ← Timeline（第一视觉）/ SamePeriodView（主题级历史同周期 + 两级详情）/ CurrentTimeLens（③当前时间上下文）/ CampaignDetail（Level 2 完整历史案例）/ OpportunityRadar（未引用，待清理）…
│   ├─ data/
│   │   └─ timeline/           ← Timeline Adapter（消费 exports/）+ preObservation.ts（提前观察区，纯 UI 层）
│   ├─ models/                 ← 核心数据模型（禁擅改）
│   └─ utils/
├─ public/
├─ index.html
│
├─ docs/                       ← 项目级文档
│   ├─ PROJECT_STATE.md        ← 接班必读②
│   ├─ PRODUCT_PURPOSE.md
│   ├─ ROADMAP.md
│   ├─ CHANGELOG.md            ← 统一变更记录
│   ├─ THEME_CAMPAIGN_MODEL_AUDIT.md ← Theme/Campaign 分层模型审计（Macro Theme→Theme Cycle→Campaign→Sub-theme）
│   └─ (Cycle 原有) PRODUCT.md / DATA_MODEL.md / DATA_GOVERNANCE.md /
│        HISTORICAL_VALIDATION.md / ARCHITECTURE.md / UI_SPEC.md
│
├─ exports/                    ← ★ Research → Product 唯一交换目录
│   └─ timeline_export_v1.json ← ★ 唯一 canonical export
├─ contracts/
│   └─ timeline_export_v1.md   ← 跨模块接口契约
│
├─ research/                   ← Research 子系统（原 Cycle-Research 仓库）
│   ├─ AGENTS.md               ← Research 职责书
│   ├─ README.md               ← 原 Cycle-Research README
│   ├─ database/cycle_research.db  ← 研究数据库（提交 Git，见 §11）
│   ├─ schema/schema.sql       ← 冻结（禁改）
│   ├─ data/market/            ← raw / normalized 行情 CSV
│   ├─ exports/cycle_verified_candidates.json
│   ├─ scripts/                ← Python 流水线
│   └─ research/               ← 研究产物：annual / batch / c2 / methodology / promotion / summary / templates
│
├─ data/                       ← Product 侧核验数据（raw / candidate / verified / validation）
└─ tests/
```

> 注：`research/research/` 是历史既有嵌套（Research 仓库内原本就有 `research/` 产物目录），
> 迁移时**刻意保留**该相对结构以维持零语义漂移与历史可追溯，不是冗余。

---

## 5. 数据流（单向，禁止手工 Copy）

```
research/                      Python 研究流水线
    ↓  Research scripts
exports/timeline_export_v1.json   ← ★ 唯一 canonical
    ↓  Cycle Timeline Adapter（src/data/timeline/timelinePreview.ts → timelineAdapter.ts）
Timeline UI
```

**禁止**：Research → 手工 Copy → Cycle 内 JSON。
**禁止**：在仓库内长期存在两个 canonical JSON 副本。

---

## 6. Export Contract

- 唯一版本：`timeline_export_version = "1.0"`。
- 契约正文：`contracts/timeline_export_v1.md`。
- 顶层 11 字段白名单：`contract / timeline_export_version / generated_at / source_commit / project / rules / signals / campaigns / research_candidates / events / securities`。
- 守门人：`research/scripts/validate_timeline_export.py`。
- **Schema 变更必须同时更新三处**：`contracts/` + Research exporter + Cycle adapter。
  任何一侧不得单方面改变。

---

## 7. 数据状态（严格分层，禁止越级）

```
Source ≠ Evidence ≠ Rule ≠ Historical Fact ≠ Verification ≠ Prediction
```

**Research 研究状态**（大写）：`RAW / PROVISIONAL / CONFLICT / INSUFFICIENT / VERIFIED`
**生产状态**（小写，Cycle 消费）：`verified / provisional / conflict / preview`

- `PROVISIONAL ≠ VERIFIED`。PROVISIONAL 可用于预览，**不得**自动进入 verified。
- Research Candidate（`RC-` 前缀）**永不**映射为 verified；与正式 Campaign 是**并列**来源，非升级关系。
- 生产 `verified` 数据位于 `data/verified/`；前端 `?preview=1` 消费 `exports/`，默认生产模式消费 `data/verified/`。

---

## 8. 禁止事项（红线）

**数据与模型**

- 修改 Research Model v1.0
- 新增 ThemeCycle / CampaignRelation schema 或数据库实体
- 修改 `research/schema/schema.sql`
- 修改 2018–2025 已有历史研究结论（Campaign / Theme / Evidence / Market Data / Lifecycle / Drivers）
- 让 PROVISIONAL 自动进入 verified；把 Candidate 当 confirmed
- 丢 Git 历史 / 丢 Research 数据

**产品**

- 实时行情 / 资金流 / 异动监控
- AI 预测、确定性未来预测、"必涨 / 必跌"
- 买入 / 卖出 / 建仓 / 清仓建议；股票推荐；自动交易信号
- 伪造胜率 / 季节性评分等量化结论
- 用户登录 / 权限系统 / 后端 / 自动爬虫

UI 文案中「买入 / 卖出 / 建仓 / 清仓 / 推荐」只允许出现在**否定性免责声明**中。

---

## 9. 测试策略

**Product（Node）**

```bash
npm test          # Vitest，当前 220 项
npx tsc -b        # 类型检查
npm run build     # 生产构建
```

**Research（Python，标准库 sqlite3）**

```bash
cd research
python scripts/validate_db.py
python scripts/validate_timeline_export.py
python scripts/validate_batch_research.py
python scripts/validate_promotion_manifest.py
python scripts/check_doc_schema_consistency.py
```

**Integrity**

```bash
python scripts/validate_monorepo_integrity.py   # 仓库结构 / canonical 唯一性 / 数据流
```

改动后必须运行相关测试；不得删除现有测试。

---

## 10. 修改规则

1. 先搜索是否已有实现；**优先修改已有实现**，不重复造轮子。
2. 最小修改原则：不做「为了更优雅」的重构；不做「未来可能需要」的预留。
   "未来可能需要" 记入 `docs/ROADMAP.md`，不写进代码。
3. 不擅自重构核心数据模型（`src/models/`）或改变产品定位（§1）。
4. 若任务与本文件冲突：**优先遵守本文件**，在最终报告中明确指出冲突点，等待确认。
5. 每轮修改必须说明：改了什么、为什么改、为什么属于必要修改。

---

## 11. Git 规则

- **唯一 Git**：仓库根 `.git`。`research/` 内**不再**有独立 `.git`。
- **唯一远程**：`origin` → `https://github.com/yangfanbit/Cycle.git`。不新建第三个仓库。
- `research/database/cycle_research.db` **继续提交 Git**（Research 明确依赖可回查数据库）；
  不因通用最佳实践自动忽略 SQLite。
- 禁止 `force push`。若遇无法解决的问题，先停止并报告。
- 默认普通 fast-forward push。
- 提交前确认：工作树干净、`origin` 正确、`main` 正确、历史完整。

**Research 历史追溯**：`git log -- research/` 可回溯原 Cycle-Research 全部历史提交
（经 `git subtree` 并入，原始 author / date / message 保留）。

---

## 12. 当前唯一下一目标

> 见 `docs/PROJECT_STATE.md`。

**真实用户视觉 Review。** Phase 5.2.1 V1.8.2.1 实现完成后已**停止**：
不新增行业、不新增 Rule、不新增统计、不新增 Radar、不新增预测、不新增 UI。

请用户在真实使用中依次判断 4 个产品目的问题：

1. Early Signal 与 Theme Formation 是否真正分开？（参考区 → 早期信号 → 主题形成，不再同日）
2. 提前观察参考区是否只是浏览参考，而不是历史事实？
3. Campaign 是否仍然最突出？（视觉层级 Campaign > Early Signal > 参考区）
4. 用户是否仍能理解「先观察 → 出现早期信号 → 主题形成」？
