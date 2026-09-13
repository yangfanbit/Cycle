# ThreeC

**A股历史机会时间轴 / 历史机会地图**

> 看今天处于一年中的哪个时间位置 → 看历史上这个时间附近发生过什么主题 / 行情 →
> 看这些主题通常如何形成、发展、转折、结束 → 看有没有提前信号 → 看为什么启动 / 加速 / 转折 / 结束
> → 通过历史规律发现当前值得继续研究的方向。

**ThreeC = Research + Cycle Product**

- **Research**：历史研究 / 数据生产 / Research Export（`research/`，Python + SQLite）
- **Cycle Product**：Timeline 前端 / PWA / 机会发现呈现（仓库根 `src/`，React + TypeScript + Vite）

> **核心价值 = 机会发现，不是交易决策。**
> 用户自己负责基本面、技术面、个股选择与入场时机。ThreeC 不做这些。
>
> ⚠️ 本项目**不是**：学术型历史数据库 / 炒股预测软件 / 自动荐股 / 买卖信号系统 / AI 预测系统。

---

## 快速开始

> 需要 **Node.js**（≥18）与 **Python 3**（含标准库 `sqlite3`）。
> Node 与 Python 是**两个独立子系统**：根 `package.json` 只服务 Cycle/Vite；
> Research 保持 Python 脚本，**不是** npm package。

### Product（前端）

```bash
npm install
npm run dev        # http://localhost:5173        ← 生产数据模式
                   # http://localhost:5173/?preview=1  ← Research 预览模式
npm test           # Vitest（111 项）
npx tsc -b         # 类型检查
npm run build      # 生产构建
```

**Preview 与 Production 的差别**

| 模式 | URL | 数据源 |
|---|---|---|
| Production（默认） | `/` | `data/verified/`（已人工核验历史行情；当前为空 → 显示空态） |
| Preview | `/?preview=1` | `exports/timeline_export_v1.json`（Research 导出，2018–2025） |

> Preview 数据**不是**生产数据出口：不写入 `data/verified/`、不混入 `allCampaigns`。
> 顶部会显示「开发预览数据」横幅。**PROVISIONAL 不会自动进入 verified。**

### Research（研究流水线）

```bash
cd research

python scripts/fetch_market_batch.py        # 补齐缺失行情（幂等，腾讯免费接口）
python scripts/batch_auto_research.py       # 生成 batch manifest / conflicts / timeline_export_v1
python scripts/validate_db.py
python scripts/validate_timeline_export.py
python scripts/validate_batch_research.py
```

> ⚠️ 运行 `batch_auto_research.py` 会重写 `exports/timeline_export_v1.json`。
> `generated_at` / `source_commit` 会变化，**业务内容必须保持 zero semantic diff**。

### 完整性校验

```bash
python scripts/validate_monorepo_integrity.py
```

---

## 目录说明

```
ThreeC/
├─ AGENTS.md              ← ★ 接班入口（先读这个）
├─ README.md              ← 本文件
├─ package.json           ← Product（Node/Vite）
├─ tsconfig.json / vite.config.ts
│
├─ src/                   ← Product：React 源码
│   ├─ components/        Timeline / CampaignDetail / SamePeriodView / OpportunityRadar / RuleDetail
│   ├─ data/
│   │   └─ timeline/      ← Timeline Adapter（消费 @exports）
│   ├─ models/            ← 核心数据模型
│   └─ utils/
├─ public/  index.html
├─ data/                  ← Product 侧核验数据（raw / candidate / verified / validation）
├─ tests/
│
├─ docs/                  ← 项目级 + 产品级文档
│   ├─ PROJECT_STATE.md   ← ★ 接班必读②
│   ├─ PRODUCT_PURPOSE.md
│   ├─ ROADMAP.md         ← Phase 1–8
│   ├─ CHANGELOG.md       ← 统一变更记录
│   └─ PRODUCT.md / DATA_MODEL.md / DATA_GOVERNANCE.md /
│      HISTORICAL_VALIDATION.md / ARCHITECTURE.md / UI_SPEC.md
│
├─ exports/               ← ★ Research → Product 唯一交换目录
│   └─ timeline_export_v1.json   ← ★ 唯一 canonical export
├─ contracts/
│   └─ timeline_export_v1.md     ← 接口契约
│
└─ research/              ← Research 子系统（Python + SQLite）
    ├─ AGENTS.md          ← Research 职责书
    ├─ README.md          ← 原 Cycle-Research README
    ├─ database/          ← cycle_research.db（提交 Git，可回查）
    ├─ schema/schema.sql  ← 冻结
    ├─ data/market/       ← raw / normalized 行情 CSV
    ├─ scripts/           ← Python 流水线
    └─ research/          ← 研究产物：annual / batch / c2 / methodology / promotion / summary / templates
```

---

## Research Workflow

```
source（Tier 1–4）
  → Evidence（supporting / contradicting / context）
  → Campaign（主题可识别 + 持续性 + 市场关注 + 可解释起止 + 有 Evidence）
  → Lifecycle（周期阶段）+ Drivers（归因四问）
  → Research Export
```

研究状态（大写）：`RAW / PROVISIONAL / CONFLICT / INSUFFICIENT / VERIFIED`
生产状态（小写）：`verified / provisional / conflict / preview`

- `PROVISIONAL ≠ VERIFIED`
- Research Candidate（`RC-` 前缀）**永不**映射为 verified，与正式 Campaign 并列
- Confirmed 门槛：≥2 条 Evidence 且 ≥2 个 `independence_group`

**Research Model v1.0 处于 Frozen 状态**（`schema.sql` 冻结，禁改）。

---

## Export Workflow

```
research/（Python 研究流水线）
    ↓  生成
exports/timeline_export_v1.json      ← ★ 唯一 canonical
    ↓  Cycle Timeline Adapter 消费
Timeline UI
```

- 唯一版本：`timeline_export_version = "1.0"`
- 契约：`contracts/timeline_export_v1.md`
- 守门人：`research/scripts/validate_timeline_export.py`
- **禁止**：手工 Copy JSON；仓库内长期存在第二份 canonical 副本。
- **Schema 变更必须同时更新**：`contracts/` + Research exporter + Cycle adapter。

---

## 接手阅读顺序

1. `AGENTS.md`（根）—— 12 节，覆盖初心 / 边界 / 目录 / 数据流 / 规则
2. `docs/PROJECT_STATE.md` —— 当前状态、数据状态、下一目标
3. 按任务需要再读：`research/AGENTS.md`（Research 任务）或 `docs/PRODUCT_PURPOSE.md`（产品任务）

**不要通读全部文档。**

---

## 当前状态

**Phase 4 Monorepo Integration 已完成** —— 一个项目、一个 Git、一个 canonical export、
两个逻辑模块、一个项目目标。

- Timeline MVP 已可用（2018–2025 数据可见，`?preview=1`）
- Research 已产出 8 个正式 Campaign + 2 个 Research Candidate（2018 反例年份保留）
- **等待下一轮 Review**；不新增行业 / Rule / 统计 / Radar / 预测 / UI

详见 `docs/PROJECT_STATE.md`。
