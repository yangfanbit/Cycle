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

**Phase 6：Product Core v2（IMPLEMENTED）。**

把 Timeline + Historical Same Period + Current Time Lens 升级为**当前研究导航层**
（Current Time Lens v2 + Historical Similar Phase v1 + Macro Theme 聚合接口）。

- Phase 4 Monorepo Integration 已完成：单一仓库 `ThreeC`，单一 Git，保留双方完整历史。
- Phase 5.x 已完成：Current Time Lens v0 → V1.8.1 主题级历史机会视图（IA 重排）→
  V1.8.2 两级详情 + 提前观察参考区 → V1.8.2.1 Formation Anchor 语义修正。
- Phase 5.3–5.5 已完成：**Theme / Campaign 分层模型统一审计**（Macro Theme → Theme Cycle →
  Campaign → Sub-theme + Campaign Independence Gate Q1–Q5）· **Research Model v1.1 方法论补丁**
  （Theme Cycle Pattern A/B/C · Lifecycle Measurement Rule · Gate Q1 Anti-example）·
  **医药健康 Pilot**（首个非汽车 Macro Theme，1 正式 Campaign + 2 Research Candidate）。
- Phase 5.6–5.8 已完成：F-MED-1 跨年年份语义 · **Timeline Entry Identity**
  （`entryId = campaign_id@display_year`）· **Year Coverage Rule**（两源 `years()` 统一）。
- **Phase 6 V2.0 已完成**：
  - **F-MED-6**：Selection 区分展示实例（`entryId`，条目高亮 / focus）与完整历史案例
    （`campaign_id`，Campaign Detail）—— 跨年 Campaign 不再多行同时高亮。
  - **Current Time Lens v2 三层**：A. A股整体环境 = `Unknown`（无整体市场周期模型，
    **绝不**从行业 Campaign 反推大盘）· B. 当前 Theme / Theme Cycle（无当前年份数据 →
    **诚实空态**，不把历史数据伪装成当前状态）· C. **Research Attention** 状态分类
    （`当前值得研究` / `保持观察` / `历史参考`，**不是评分 / 概率 / 信号**）。
  - **Historical Similar Phase v1（Lifecycle Lens）**：按「阶段 → Theme Cycle Pattern →
    Drivers 重叠」检索，Top 3 上限、「高/中/参考」分级（无百分比）、必给「为什么类似」、
    无证据 → 空态不凑数。与「历史同期（Calendar Lens）」并存、不可互相替代。
  - **Macro Theme 聚合接口**（仅 View/Adapter；本轮**不改** Timeline 视觉）。
  - IA（视觉优先级 `Timeline > Current Lens > Similar Phase`）：
    **① Timeline → ② 当前时间研究导航 → ③ 历史相似阶段 → ④ 历史同期（日历）**。
  **不做**预测 / 荐股 / 交易信号 / 评分 / 概率 / 实时数据。

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
npm test          # Vitest，当前 282 项
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

**用户视觉 / 交互 Review（Phase 6 V2.0）。** 实现完成后**停止**：
不新增行业、不新增 Rule、不新增统计、不新增 Radar、不新增预测。

请用户在真实使用中依次判断 6 个产品目的问题：

1. Timeline 是否仍是第一视觉？（Lens 是研究导航层，但不能压过 Timeline）
2. Lens A 层 `A股整体周期：Unknown` 是否被理解为「诚实的不知道」，而不是「系统没做完」？
3. Lens B 层的 2026 空态是否清楚表达了「不用 2025 冒充 2026」？
4. Research Attention 的三种状态（当前值得研究 / 保持观察 / 历史参考）是否不被误读为「推荐度 / 评分」？
5. 历史相似阶段是否让你产生了「想去研究某个方向」的动机？（研究入口是否有效）
6. 「日历同期」与「生命周期相似」两个视角是否清楚可区分、且都需要保留？
