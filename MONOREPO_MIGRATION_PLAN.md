# MONOREPO_MIGRATION_PLAN

> 本轮任务：Monorepo Integration + Project Handoff Infrastructure。
> 本文件在**任何 destructive 操作之前**建立，作为迁移的事实记录与回滚依据。
> 建立时间：2026-09-13

---

## 一、迁移前事实源（本地审计结论）

本地 `D:\@AW\投资\ThreeC` 为事实源，不以 GitHub 当前状态为准。

### 1.1 原 Cycle HEAD

| 项 | 值 |
|---|---|
| 路径 | `ThreeC/Cycle` |
| HEAD | `d37950027380037970447c163c8159f14f64d5f8` |
| HEAD 摘要 | `chore(v1.7.1): Sync Latest Cycle-Research Export（eadf06a）：lifecycle + drivers 接入` |
| 分支 | `main`（唯一分支，含 `remotes/origin/main`） |
| 远程 | `origin` → `https://github.com/yangfanbit/Cycle.git` |
| 提交数 | 11 |
| 首个提交 | `b4dd471 chore: initial commit — A股机会时间轴 V1` |
| 工作树 | 干净（`git status --porcelain` 0 行） |

### 1.2 原 Cycle-Research HEAD

| 项 | 值 |
|---|---|
| 路径 | `ThreeC/Cycle-research`（注意：本地目录名小写 `research`） |
| HEAD | `eadf06a1555b2c46817c543c3e8454d4326a5efb` |
| HEAD 摘要 | `V1.7: Phase Windows + Drivers for 2018-2025 Auto, Rule Candidates v1` |
| 分支 | `main`（唯一分支，含 `remotes/origin/main`） |
| 远程 | `origin` → `https://github.com/yangfanbit/Cycle-Research.git` |
| 提交数 | 28 |
| 首个提交 | `7de8c00 init: Cycle-Research A股题材/行业季节性研究数据库（试点 2018-2020）` |
| 工作树 | 干净（`git status --porcelain` 0 行） |

### 1.3 迁移前基线验证（Regression Baseline）

| 检查 | 结果 |
|---|---|
| Cycle `npm test` | **111 / 111 通过**（2 个测试文件） |
| Research `python scripts/validate_db.py` | **PASS**（0 条目警告） |
| Research `python scripts/validate_timeline_export.py` | **PASS**（8 Campaigns / 2 Research candidates / 26 Events / 39 Securities） |
| Research `python scripts/validate_batch_research.py` | **PASS**（9 条目：PROVISIONAL 8 / CONFLICT 1） |

### 1.4 关键文件哈希（迁移前）

| 文件 | SHA256 | 大小 |
|---|---|---|
| `Cycle-research/exports/timeline_export_v1.json` | `BF36FF7B419F4BFA982527B15F5853E3BB67F7CA4D8941D2932B358574EFD01E` | 47678 |
| `Cycle/src/data/timeline/data/timeline_export_v1.json` | `BF36FF7B419F4BFA982527B15F5853E3BB67F7CA4D8941D2932B358574EFD01E` | 47678 |
| `Cycle-research/exports/cycle_verified_candidates.json` | `68DE6A033559A9D047EBE1CA60755CB5CDDFA2F8433EB32557A678DDC3A9A439` | 70859 |
| `Cycle-research/database/cycle_research.db` | `775E1B54BF29A12484D8016999B0A27146A980BE810236BAB0CAB66C4D7DBF72` | 3428352 |
| `Cycle-research/schema/schema.sql` | `130A1AD8262112AAD43EC0B860242DA9BBD6C84B6AA7571BAE6771EC360A6209` | 13782 |
| `Cycle-research/research/methodology/timeline_export_contract_v1.md` | `F3ED8D32A5379E12A1852DDFBA3ED4A9C0D4BD4330B124370E4B81DDFB75E641` | 11092 |

**结论：两份 `timeline_export_v1.json` 逐字节完全相同（同一哈希）**，确认「双份 canonical 副本」问题真实存在，非内容漂移。

---

## 二、迁移策略

### 2.1 根容器决定

**`Cycle-Research` 原仓库子目录中已存在 `research/` 目录**（`research/annual|batch|c2|methodology|promotion|summary|templates`），而目标结构要求 `ThreeC/research/` 承载 Research 子系统。若把整个 Research 仓库放进 `ThreeC/research/`，将产生 `ThreeC/research/research/` 嵌套，语义含糊。

因此采用策略：

- **Research 仓库内容 → `ThreeC/research/`**，即 Research 仓库**根内容**平移到 `research/` 下；
  - `research/research/...` → `research/research/...` 保留原相对路径（不改动内部相对结构，保证语义 zero diff 与历史可追溯）。
  - 该嵌套由 `research/AGENTS.md` 明确解释：`research/research/` 为 Research 研究产物目录（annual / batch / c2 / methodology / promotion / summary）。

> 备选方案 A（未采用）：把 Research 仓库并入 `research/` 但重命名其内部 `research/` → `findings/`。**未采用原因**：会造成大量历史文档与脚本路径的语义改动，与第 26 条「数据内容必须 zero semantic diff」冲突风险更高。

### 2.2 Cycle 保留为根项目

`Cycle/` 的 `src/`、`package.json`、`vite.config.ts`、`tsconfig.json`、`index.html`、`data/`、`tests/`、`docs/` 直接提升为 `ThreeC/` 根内容。**不新建 `apps/cycle/`**。

### 2.3 Git 历史保留方式：`git subtree`

- 以 **Cycle 仓库为根仓库**（保留其 11 条历史与 `origin = yangfanbit/Cycle`）。
- 用 `git subtree add --prefix=research <Cycle-Research 本地路径> main` 将 Research 的 28 条历史并入，**生成一个 join commit，并保留全部原始提交**（历史提交的 author/date/message 不变，仅路径前缀变为 `research/`）。
- 该方式满足第 5 条：未来 `git log -- research/` 可完整追溯原 Cycle-Research 历史提交。

> 备选方案 B（未采用）：`git read-tree` + 手写 merge commit。可控但更易出错。
> 备选方案 C（禁止）：复制文件 + 删 `.git` + `git init`。会丢历史，违反第五/三十八条。

### 2.4 唯一远程

最终 `origin` → `https://github.com/yangfanbit/Cycle.git`（**不新建第三个仓库**）。
`Cycle-Research` 不再作为独立远程维护。

---

## 三、迁移执行顺序（安全边界）

```
0. 基线测试 + 文件哈希快照（已完成）
1. 物理备份 TwoC 全量（robocopy，排除 node_modules）
2. 建立 migration 分支（在根仓库）
3. Cycle 内容提升为 ThreeC 根内容（保留 .git）
4. git subtree add research/ <Cycle-Research 路径>
5. 消除 canonical export 副本（src/data/timeline/data/ → 指向 exports/）
6. 修正 Research 脚本路径（ROOT 语义变化）
7. 新增治理文档（AGENTS / PROJECT_STATE / PRODUCT_PURPOSE / README / ROADMAP / CHANGELOG）
8. 新增完整性校验脚本
9. 运行全部回归测试（Node + Python + semantic diff）
10. 验证内层 .git 已无必要 → 删除 Cycle/.git 与 Cycle-research/.git
11. 提交、验证 git log、push origin main
```

**硬约束**：第 10 步之前绝不删除任何 `.git`。

---

## 四、风险与缓解

| 风险 | 缓解 |
|---|---|
| Research 脚本 `ROOT` 由「仓库根」变为「`ThreeC/research`」 | 迁移后逐个验证 `python scripts/*.py` 仍可运行；`db.py` 的 `ROOT` 语义 = `research/` 根，恰好正确（`database/`、`schema/` 仍在 `research/` 下） |
| `sys.path.insert(0, 上一级目录)` 语义 | 迁移后上一级 = `ThreeC/research/`，`from scripts import db` 仍成立 |
| Cycle 前端 import 路径变化 | 副本迁出后 `src/data/timeline/timelinePreview.ts` 的 import 需调整；使用 Vite alias 或 tsconfig path 指向 `exports/` |
| tsconfig `include` 不含 `exports/` | 显式加入 `exports` |
| Research 大数据文件（4CSV / db 3.4MB） | 全部保留提交，不忽略；不做 LFS |
| 内层 `.git` 误删 | 严格遵守第 10 步门禁；备份先行 |
| 历史研究结论被改动 | 用 SHA256 逐文件比对 `research/` 内容与备份，仅允许路径前缀变化 |

---

## 五、回滚方法

### 5.1 迁移失败（未删内层 .git 时）

```powershell
# 直接回到原状：删除新建的 ThreeC 根内容，保留两个原目录
# （因 Cycle 根内容被提升，需从备份恢复）
robocopy <BACKUP>\ThreeC D:\@AW\投资\ThreeC /MIR /XD node_modules
```

### 5.2 迁移失败（已删内层 .git 但未 push 时）

```powershell
cd D:\@AW\投资\ThreeC
git reset --hard <backup-branch>
# 或直接从物理备份整目录恢复
```

### 5.3 已 push 后发现严重问题

- **禁止 force push**。
- 采用 `git revert <merge-commit>` 生成反向提交后正常 push。
- 若确需历史重置，必须先停止并向用户报告，等待明确授权。

### 5.4 物理备份位置

`D:\@AW\投资\ThreeC_BACKUP_<timestamp>\`（全量，排除 `node_modules`）

---

## 六、明确不做

- 不修改 Research Model v1.0、`schema.sql`、已有历史研究数据内容。
- 不新增 ThemeCycle / CampaignRelation schema 或数据库实体。
- 不新增 UI 功能 / Dashboard / Statistics / Prediction / Radar / Notification / Backend。
- 不让 PROVISIONAL 自动进入 verified。
- 不重新生产 Research 数据。
- 不 force push。
- 不删除任何现有测试。
