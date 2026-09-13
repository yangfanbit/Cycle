# research/AGENTS.md — Research 子系统职责书

> 本文件是 `ThreeC/research/` 的**局部**规范。全局规范以仓库根 `AGENTS.md` 为准；
> 两者冲突时，**根 AGENTS.md 优先**。
>
> 接手 Research 任务时：先读根 `AGENTS.md` + `docs/PROJECT_STATE.md`，再读本文件。

---

## 0. 我是谁

本目录是 `ThreeC` 的 **Research 子系统**，由原独立仓库 `yangfanbit/Cycle-Research`
经 `git subtree` 并入（历史完整保留，可用 `git log -- research/` 追溯）。

**研究产物目录**：`research/research/`（`annual / batch / c2 / methodology / promotion / summary / templates`）
——这是原仓库既有结构，刻意保留以维持零语义漂移。

---

## 1. Research Model v1.0 — 冻结

> **`Research Model v1.0` 处于 Frozen 状态。Monorepo 迁移不改动它。**

- 模型正文：`research/methodology/research_model_v1_0.md`
- 冻结报告：`RESEARCH_MODEL_V1_FREEZE_REPORT.md`
- 数据库 schema：`schema/schema.sql`（**禁止修改**）

**禁止新增**：

- `ThemeCycle` schema
- `CampaignRelation` schema
- 任何新的数据库实体 / 新表 / 新列

研究级状态（`RAW / PROVISIONAL / CONFLICT / INSUFFICIENT / VERIFIED`）表达在
`research/batch/` 与 export manifest 层，**不改 SQLite 正式 schema**。

---

## 2. Research 负责什么

| 职责 | 位置 |
|---|---|
| 数据收集 | `data/market/{raw,normalized}/` |
| Source（来源分级 Tier 1–4） | 数据库 `sources` |
| Evidence（supporting / contradicting / context） | 数据库 `evidences` + `campaign_evidences` 桥表 |
| Market Data（行情核验） | `market_series / market_daily / trading_calendar` |
| Campaign（可识别行情） | 数据库 `campaigns` + 桥表 |
| Lifecycle（周期阶段） | export `lifecycle` 字段 |
| Drivers（驱动归因四问） | export `drivers` 字段 |
| Research Export | `exports/`（canonical 写入 `../exports/`） |

**概念链（逐级不可跳跃）**：

```
Source ≠ Evidence ≠ Rule ≠ Historical Fact ≠ Verification ≠ Prediction
```

- 单日板块上涨 ≠ Campaign；媒体描述 ≠ 市场事实。
- `evidences.independence_group` 区分同源转引与真正独立来源；
  **媒体数量 ≠ 独立证据数量**。
- Confirmed 门槛：**≥2 条 Evidence 且 ≥2 个 independence_group**
  （由 `scripts/validate_db.py` 程序化检查）。

---

## 3. Research 不负责什么

**明确不属于 Research**：

- UI / 前端渲染
- Timeline 排版与视觉
- PWA / 离线能力
- 前端交互逻辑
- 任何 `src/` 下的产品代码

Research **只产出数据**；如何呈现是 Product 的事。
**不要**在 Research 侧写 UI 相关逻辑，也**不要**为了"前端方便"改变导出结构。

---

## 4. 目录与路径语义（Monorepo 后）

```python
# research/scripts/db.py
ROOT             = <repo>/research          # Research 子系统根
REPO_ROOT        = <repo>                   # Monorepo 根
EXPORTS_DIR      = <repo>/exports           # ★ canonical export 目录
TIMELINE_EXPORT_PATH = <repo>/exports/timeline_export_v1.json
```

- `database/`、`schema/`、`research/`、`data/` 均相对 `ROOT` 解析（与迁移前一致）。
- **canonical export 在 `ROOT` 的上一级**：`<repo>/exports/`。
  Research 脚本只**写入**该目录；Product 只**消费**该目录。
  禁止在 `research/` 内维护第二份 `timeline_export_v1.json`。

---

## 5. 标准工作流

```bash
cd research

# 1) 行情补齐（幂等，腾讯免费接口）
python scripts/fetch_market_batch.py

# 2) 批量研究：生成 manifest / conflicts / timeline_export_v1
python scripts/batch_auto_research.py

# 3) 校验
python scripts/validate_db.py
python scripts/validate_batch_research.py
python scripts/validate_timeline_export.py
python scripts/validate_promotion_manifest.py
python scripts/check_doc_schema_consistency.py
```

**注意**：本轮（Monorepo Integration）**不重新生产数据**。
`batch_auto_research.py` 会重写 `exports/timeline_export_v1.json`，
`generated_at` / `source_commit` 属允许变化的元数据；**业务内容必须 zero semantic diff**。

---

## 6. Export Contract（Research 侧）

- Research 负责**生成**：`exports/timeline_export_v1.json`
- 唯一版本 `timeline_export_version = "1.0"`
- 契约正文：`../contracts/timeline_export_v1.md`
- 守门人：`scripts/validate_timeline_export.py`
- 生成脚本**只读数据库，不写 DB，不改 schema**

**Schema 变更必须同时更新**：`contracts/` + Research exporter + Cycle adapter。
任何一侧不得单方面改变。

---

## 7. 红线

- 不修改 Research Model v1.0 / `schema/schema.sql` / 已有历史研究结论
- 不新增数据库实体
- 不让 PROVISIONAL / CONFLICT / INSUFFICIENT 伪装为 VERIFIED
- 不因迁移改动 2018–2025 的 Campaign / Theme / Evidence / Market Data / Lifecycle / Drivers 内容
- 不丢 Git 历史
- 允许：路径调整、import 调整、文档路径调整 —— **数据内容必须 zero semantic diff**
