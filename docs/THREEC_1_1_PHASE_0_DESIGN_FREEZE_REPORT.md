# THREEC_1_1_PHASE_0_DESIGN_FREEZE_REPORT.md

> | 项目 | 值 |
> |---|---|
> | 报告性质 | **Phase 0 轮次报告（ROUND REPORT）** |
> | 轮次 | ThreeC 1.1 Phase 0：**Architecture Freeze Execution** |
> | 日期 | 2026-09-25 |
> | Canonical Repository | https://github.com/yangfanbit/Cycle |
> | 基线 | `main` @ `dcf4786`（= `origin/main`）· tag `v1.0.0` → `064d39c` |
> | 本轮改动范围 | **仅 `docs/`**（+ 工作区 LF 恢复） |
> | 状态 | **等待下一阶段确认** |

---

## 1. 本轮目标与结果

| 目标 | 结果 |
|---|---|
| 确认基线（branch / status / log -1 / tag / main==origin/main） | ✅ 已确认 |
| LF 恢复（限 `research/**` · `exports/**` · `contracts/**`） | ✅ 已完成（166 文件） |
| 完善 Market Snapshot 架构文档（8 个必备章节） | ✅ |
| 新增 Market Snapshot Contract v0.1 | ✅ |
| 新增 Market Snapshot Governance | ✅ |
| Namespace 调整（`MS-*` / `CR-*` / `IR-*` / `URO-*` draft-only；删除 `OC-*`） | ✅ 已写入设计 |
| **不写代码 / 不改 UI / 不改 DB / 不改 Research / 不改 schema** | ✅ 遵守 |

---

## 2. 基线确认（实测）

| 项 | 实测值 |
|---|---|
| `git branch` | `main` |
| `git log -1` | `dcf4786 feat(product-1.1.2): replace yearly Panorama with Macro Theme × annual window seasonal map; detail-level data moves to drill-down` |
| `git tag` | `v1.0.0`（annotated → commit `064d39c`） |
| `main == origin/main` | ✅ **是**（ahead/behind = `0 / 0`） |

---

## 3. LF 恢复结果

### 3.1 恢复前

- 工作区 **177 个文件**报告为 modified。
- 实测：`git diff --stat` = `71289 insertions(+) / 71289 deletions(-)`；
  `git diff --ignore-cr-at-eol` = **空** → **纯 EOL 差异，零内容变化**。

### 3.2 执行

| 步骤 | 命令 | 范围 |
|---|---|---|
| 1 | `git restore --source=HEAD -- research exports contracts` | **授权范围**（166 文件） |
| 2 | `git read-tree HEAD` | 重建 index stat cache（**不触碰工作区**） |

> **未执行** `git restore .`（全仓）—— 遵守「禁止 git restore 全仓」。

### 3.3 ★ 关键发现：177 个「伪修改」的**两层**原因

**第一层：真实 EOL 翻转。** 工作区文件被外部工具改写为 CRLF（仓库 blob 为 LF）。
`git restore` 已把授权范围内的文件写回 LF。

**第二层（★ 隐蔽）：index 是「Windows 生成的陈旧 stat cache」。**
`git restore` 之后，文件已是 LF、内容与 HEAD 逐字节一致，但 `git status` **仍报告 modified**。
诊断结果：

```
$ git ls-files --debug research/.gitignore
  ctime: 1789284971:294673700
  mtime: 1789284971:294673700
  dev: 0   ino: 0          ← Windows 索引特征（无 Unix dev/ino）
  uid: 0   gid: 0          ← 同上
  size: 206                ← CRLF 时代的体积

$ stat -f 'size=%z mtime=%m' research/.gitignore
  size=196 mtime=1790347837   ← 实际 LF 体积

$ git hash-object research/.gitignore   → 213ef54…
$ git rev-parse :research/.gitignore    → 213ef54…   （index blob）
$ git rev-parse HEAD:research/.gitignore→ 213ef54…   （HEAD blob）
$ shasum research/.gitignore            → 4c1471e4…  （原始 sha1）
$ git cat-file blob :research/.gitignore | shasum → 4c1471e4…
```

→ **内容逐字节相同**，但 index 的 stat cache 是 Windows 时代产物（`dev/ino/uid/gid = 0`，`size = 206`），
git 永远无法用 stat 命中 → 每次都要重算，并持续报告 modified。

**修复**：`git read-tree HEAD` —— 用 HEAD 树重建 index（**index 本就 == HEAD，内容无变化**；
仅重置 stat cache）。修复后 `git status` 立即正确。

> 注：`git read-tree` 不在 `AGENTS.md` §6 的禁止清单内；它**不修改工作区、不改变 index 内容**，
> 只重建 stat 元数据。**已在此显式披露。**

### 3.4 恢复后

| 项 | 结果 |
|---|---|
| `git diff --ignore-cr-at-eol` | ✅ **空**（零内容差异） |
| `git diff --cached` | ✅ **空**（index == HEAD） |
| `research/**` 剩余 CRLF | ✅ **0** |
| `contracts/**` 剩余 CRLF | ✅ **0** |
| `exports/**` 剩余 CRLF | ✅ **0** |

**授权范围（`research/` · `exports/` · `contracts/`）已 100% clean。**

### 3.5 ⚠️ 残留（**超出授权范围，未处理**）

仍有 **11 个文件**是 CRLF（与授权范围同类问题，但不在 `research/exports/contracts` 内）：

```
 M AGENTS.md
 M docs/ARCHITECTURE.md
 M docs/PRODUCT_SIMILARITY_ARCHITECTURE_REVIEW.md
 M src/components/CampaignDetail/CampaignDetail.tsx
 M src/data/timeline/__tests__/historicalCase.test.tsx
 M src/data/timeline/__tests__/releaseGateScenarios.test.tsx
 M src/data/timeline/currentSimilarity.ts
 M src/data/timeline/currentTimeLens.ts
 M src/data/timeline/historicalCase.ts
 M src/data/timeline/researchAttention.ts
 M src/data/timeline/timelineTypes.ts
```

> **工作区尚未完全 clean。** 因用户明确「禁止 git restore 全仓」且范围限定
> `research/exports/contracts`，这 11 个文件**未恢复**，等待授权（见 §7 Q-7）。
> 处理方式与已授权范围完全相同：`git restore --source=HEAD -- <paths>`（纯 EOL，零内容变化）。

---

## 4. 交付物（本文件 + 3 份设计文档）

| # | 文件 | 性质 |
|---|---|---|
| 1 | `docs/THREEC_1_1_MARKET_SNAPSHOT_ARCHITECTURE.md` | **完善**（8 个必备章节 + Namespace 调整） |
| 2 | `docs/MARKET_SNAPSHOT_CONTRACT_v0.1.md` | **新增**（字段契约 + Artifact 边界 + 版本规则） |
| 3 | `docs/MARKET_SNAPSHOT_GOVERNANCE.md` | **新增**（纠错 / 新行情 / 人工节点治理） |
| 4 | `docs/THREEC_1_1_PHASE_0_DESIGN_FREEZE_REPORT.md` | **新增**（本报告） |

### 4.1 架构文档必备章节对照

| 用户要求 | 落点 |
|---|---|
| 1. Market Snapshot 定义（输入 / 输出 / 禁止） | §1 |
| 2. Market Snapshot Lifecycle（DRAFT→REVIEW→CANONICAL→ARCHIVED） | §2 |
| 3. Research Request 生命周期 + AI 可/不可 | §3 |
| 4. Artifact 边界（历史 vs 当前研究） | §4 |
| 5. Product 消费边界（只读 Canonical） | §5 |
| 6. Historical Correction Flow | §6 |
| 7. 新行情导入流程（RC ≠ Campaign） | §7 |
| 8. SA 边界（只复用冻结 v0.3） | §8 |

---

## 5. 本轮设计决策（已写入文档）

| # | 决策 |
|---|---|
| D-1 | Market Snapshot = **当前研究过程的「状态记录 Artifact」**，不是算法 / 模型 / 信号 / 预测 |
| D-2 | 输出仅 `historical_candidates`（研究候选）；**禁止** prediction / signal / score / ranking / probability |
| D-3 | Lifecycle 四态；**只有 `CANONICAL` 允许 Product 消费** |
| D-4 | **历史事实 ≠ 当前研究过程**：历史 Artifact 与当前研究 Artifact 分离，不混存 |
| D-5 | Market Snapshot 是**独立 Artifact**，**不进 `timeline_export_v1.json`** |
| D-6 | 匹配**只复用冻结 SA v0.3**，**不设计新匹配算法** |
| D-7 | Namespace：新增 `MS-*` / `CR-*` / `IR-*`；`URO-*` **收紧为 Draft-only**；**删除 `OC-*`**，统一用 `Observation` |
| D-8 | **4 个人工审核节点**必须人工确认（历史结构 / Correction 生效 / Campaign Promotion / Artifact Version 替换） |
| D-9 | AI 只在**离线研究生成端**产出 draft；**不自动确认结构相似 / 不自动 Promotion / 不自动评分 / 不自动排名** |
| D-10 | 版本规则：结构变化 = minor · 破坏性变化 = major · 内容修正 = artifact revision |

---

## 6. 本轮明确**未做**

- ❌ 未写 Market Snapshot 代码
- ❌ 未接 AI API
- ❌ 未修改 UI
- ❌ 未修改 Research Core（`research/` 内容零变化）
- ❌ 未修改 `schema.sql` · 未生成数据库
- ❌ 未导入 2026 行情
- ❌ 未修改 `exports/` · `contracts/`
- ❌ 未执行全仓 `git restore`

---

## 7. 等待下一阶段确认

| # | 待确认 |
|---|---|
| Q-1 | Market Snapshot 独立 Artifact（不进 `timeline_export_v1.json`）？ |
| Q-2 | Lifecycle 四态 + **仅 CANONICAL 可消费**？ |
| Q-3 | `URO-*` 收紧为 Draft-only？ |
| Q-4 | 删除 `OC-*`，统一 `Observation`？ |
| Q-5 | 匹配只复用冻结 SA v0.3？ |
| Q-6 | 4 个人工审核节点？ |
| **Q-7** | **是否授权恢复残留 11 个文件（`AGENTS.md` · `docs/` ×2 · `src/` ×8）到 LF，使工作区完全 clean？** |

---

*报告结束 · ThreeC 1.1 Phase 0 · Design Freeze Report · 2026-09-25 · 等待下一阶段确认*
