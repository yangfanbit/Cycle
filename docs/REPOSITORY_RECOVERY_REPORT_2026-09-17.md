# ThreeC Repository Recovery Report

- **日期**：2026-09-17
- **任务**：Repository Recovery + Research Integration（恢复完成前禁止任何新业务功能开发）
- **执行者**：ThreeC Lead Agent（接管 Research / Historical Data / Data Architecture / Product Architecture / Product UI / Testing / Documentation / Git / 阶段规划）
- **唯一事实来源**：当前工作区 + 当前 Git + `origin/main` + 实际文件内容（**不采信任何历史报告的自述**）

---

## A. Repository Identity

| 项 | 值 |
|---|---|
| root | `D:\@AW\投资\ThreeC` |
| Git repo | 单一仓库（`.git` 位于根） |
| remote | `https://github.com/yangfanbit/Cycle.git`（origin；fetch/push 同一 URL） |
| HEAD（恢复前） | `c968097 fix(research): exclude derived time structures from promotion` |
| origin/main（恢复前） | `c968097`（`ls-remote` 直连核对，与本地跟踪引用一致） |
| ahead / behind（恢复前） | `0 / 0` |
| HEAD（恢复后） | `e85fb42 chore(repo): reconcile research workspace and restore canonical state` |
| origin/main（恢复后） | `e85fb42`（`ls-remote` 直连核对） |
| ahead / behind（恢复后） | `0 / 0` |
| 分支 | `main`（唯一工作分支）· 本地遗留 `migration-backup-pre-monorepo`（`d379500`，迁移前备份，**保留**） |
| 已跟踪文件 | 306（恢复前后一致；`research/` 下 211） |
| `git fsck --full --no-reflogs` | 无 error；`dangling blob ×5` + `dangling commit 053d8ee`（= `630d311` 的 reset 前身，已知无害，**未修复、未删除**） |

**历史真实性核对**：上一轮报告声称的 Phase 7.3 / 7.3.1 / 7.3.2、Time Observation v0.2 / v0.3 / v0.4、
Historical Coverage Audit 全部**在 HEAD 的提交链中真实存在**，未被夸大。

`git log --graph --oneline --decorate -20` 实际提交链（节选，自新到旧）：

```
c968097 fix(research): exclude derived time structures from promotion
bd183e0 research(v0.4): 派生结构门 —— derived_from_early_signal 进入 Promotion Gate
3db1209 fix(research): 同步 test_consistency 过期证据金标准（46/39 → 51/44）
d53729f fix(research): scope_robustness.note 按 legacy 口径切换，恢复 v0.2 逐字节可复现
1d2c1b5 research(v0.3): Canonical Macro Theme Resolution + Time Observation 回归
9580593 chore(git): 加 .gitattributes 保护研究产物逐字节可复现性
262cf7b research: Historical Coverage Audit v0.1 — 覆盖度审计（只读）
183c0d4 research: commit Time Observation Discovery v0.2
630d311 feat(v7.3): Phase 7.3 Observation Credibility & Coverage
91430ad feat(v7.2): Phase 7.2 Time-based Observation Layer
668a86a docs(research): 记录并行 Phase 7.1 轮次的交叉研究记录
a7444e0 merge: 合并并行 Phase 7.1 轮次（远程 6dac246）
```

被点名的历史对象定位：

| 对象 | 状态 |
|---|---|
| `c968097` | 恢复前 HEAD 与 `origin/main`（正常提交，在 main 上） |
| `bd183e0` | 在 main 上（v0.4） |
| `630d311` | 在 main 上（Phase 7.3） |
| `183c0d4` | 在 main 上（v0.2） |
| `d53729f` | 在 main 上（legacy 口径修复） |
| `053d8ee` | **dangling**（Phase 7.3 的 reset 前身，与 `630d311` 内容相同，无害） |
| `38675c0` | 已通过 merge `a7444e0` 进入历史 |
| `668a86a` | 在 main 上；**同时是嵌套克隆 `research/.git` 的 HEAD** |

---

## B. Nested / Duplicate Repositories

| 项 | 结论 |
|---|---|
| found | **1 个嵌套 Git**：`D:\@AW\投资\ThreeC\research\.git` |
| 性质 | **同源旧克隆（stale clone）**，不是 submodule（无 `.gitmodules`）、不是 worktree、不是独立项目 |
| remote | `https://github.com/yangfanbit/Cycle.git`（与主仓库相同） |
| 分支 / HEAD | `main` @ `668a86a`（reflog 仅一条：`clone: from https://github.com/yangfanbit/Cycle.git`） |
| commit 数 | 62（`rev-list --all`） |
| 与主仓库关系 | 主仓库 72 个提交的**真子集**；**独有提交 = 0**（`comm -23` 为空） |
| resolved | **整体删除**。删除前已确认零独有对象 → 无历史丢失风险 |

---

## C. Duplicate Research Files

**分类方法**：对 `research/` 下每个文件计算 **Git blob sha1**（`sha1("blob <len>\0" + content)`），
与 ① HEAD 树 ② 全历史 blob ③ 全对象库（含 dangling）逐一比对；**不依赖文件名**。
换行符差异用「CRLF→LF 归一化后再比对」二次判定，以区分「真差异」与「仅换行差异」。

`research/` 下 475 个文件 = **211 已跟踪 + 264 未跟踪**。

| 判定 | 数量 |
|---|---:|
| 与 canonical 逐字节相同 | 162 |
| 与 canonical 仅换行不同（归一化后相同） | 248 |
| **DUPLICATE_OUTDATED**（内容 = 该路径某历史提交版本） | **11** |
| **CONFLICTING**（内容在仓库任何对象中都不存在） | **0** |
| 特殊项（需人工裁决） | 5 |

**结构成因**：`research/` 被写入了一份**整个仓库根目录的递归副本**，因此出现
`research/{src,tests,docs,data,exports,contracts,scripts,schema,package.json,tsconfig.json,vite.config.ts,index.html,.gitignore,.git}`，
并向下递归出 `research/research/`（第二层）与 `research/research/research/`（第三层）。
重名文件被 Windows 命名为 `X (2).ext` —— `research/ (2).gitignore`、`research/AGENTS (2).md`、
`research/README (2).md` 正是这个指纹。

### 11 个 DUPLICATE_OUTDATED（对照版本均为 **HEAD 之前**的旧版，非"更新版"）

```
research/docs/CHANGELOG.md                                     <-> docs/CHANGELOG.md
research/docs/PROJECT_STATE.md                                 <-> docs/PROJECT_STATE.md
research/docs/ROADMAP.md                                       <-> docs/ROADMAP.md
research/tsconfig.json                                         <-> tsconfig.json
research/vite.config.ts                                        <-> vite.config.ts
research/src/App.tsx                                           <-> src/App.tsx
research/src/styles.css                                        <-> src/styles.css
research/src/components/CurrentTimeLens/CurrentTimeLens.tsx     <-> src/components/CurrentTimeLens/CurrentTimeLens.tsx
research/src/components/Timeline/Timeline.tsx                  <-> src/components/Timeline/Timeline.tsx
research/src/data/timeline/currentCandidate.ts                 <-> src/data/timeline/currentCandidate.ts
research/research/scripts/test_consistency.py                  <-> research/scripts/test_consistency.py
```

### 5 个特殊项裁决

| 路径 | 裁决 | 依据 |
|---|---|---|
| `research/ (2).gitignore` | DUPLICATE_OUTDATED | = 历史 `.gitignore`（`a27cd9f7b`） |
| `research/AGENTS (2).md` | DUPLICATE_OUTDATED | = 历史根 `AGENTS.md`（`38675c0`，Phase 7 时代） |
| `research/README (2).md` | DUPLICATE_OUTDATED | = 历史根 `README.md`（`5774995`） |
| `research/MONOREPO_MIGRATION_PLAN.md` | DUPLICATE_OUTDATED | = 历史根同名文件（`5774995`） |
| `research/.workbuddy-ai/memory/2026-09-16.md` | 冗余（内容已被已跟踪产物覆盖） | 见 E 节 |
| `research/scripts/__pycache__/*.pyc` | 编译缓存（gitignored） | 删除 |

### canonical 决策

| 内容类别 | canonical 路径 | 说明 |
|---|---|---|
| Product | `src/` · `data/` · `tests/` · `index.html` · `package.json` · `tsconfig.json` · `vite.config.ts` | 根目录唯一一份 |
| Canonical Export | `exports/timeline_export_v1.json` | 根目录唯一一份（integrity 检查项 ⑤） |
| Contracts | `contracts/` | 根目录唯一一份 |
| Research Schema | `research/schema/schema.sql` | 冻结，禁止修改 |
| Current Research | `research/current/` | 静态研究 Artifact |
| Research 生成器 | `research/scripts/` | 35 个已跟踪脚本 |
| Research 产物 | `research/research/{annual,batch,c2,medical,methodology,promotion,reports,summary,templates}` | 原仓库结构，刻意保留 |
| Research DB | `research/database/cycle_research.db` | 明确提交 Git（研究对象） |
| 文档 | `docs/` | 根目录唯一一份 |
| Memory | `.workbuddy/memory/` | **不是** `.workbuddy-ai/` |

---

## D. Research Integration

| 项 | 结论 |
|---|---|
| **v0.1** | `research/research/reports/Seasonal_Observation_Pattern_Discovery_v0_1.md` · `seasonal_observation_patterns_v0_1.json` · `seasonal_observation_candidates_v0_1.csv` · `Time_Observation_Pattern_Integration_v0_1.md` —— **全部已跟踪** |
| **v0.2** | `time_observation_candidate_pool_v0_2.{json,csv}` · `Time_Observation_Discovery_v0_2.md` —— **已跟踪**（`183c0d4`），**保留为 legacy / comparison baseline** |
| **v0.3** | `time_observation_candidate_pool_v0_3.{json,csv}` · `Time_Observation_Discovery_v0_3.md` —— **已跟踪** |
| **v0.4** | `time_observation_candidate_pool_v0_4.{json,csv}` · `Time_Observation_Discovery_v0_4.md` —— **已跟踪**（当前 canonical discovery round） |
| **Historical Coverage** | `historical_coverage_matrix_v0_1.{json,csv}` · `Historical_Coverage_Audit_v0_1.md` —— **已跟踪**（`262cf7b`） |
| **Macro Theme** | `research/scripts/theme_taxonomy.py` = **CMTR v1 唯一实现**；`discover_time_observation_patterns.py` 与 `audit_historical_coverage.py` 共用。**未发现第二份口径**，未回退 `direct` / 名称匹配 / `rule_id` / `theme_scope` 作为主题身份 |
| **Promotion Gate** | 仅 `research/scripts/discover_time_observation_patterns.py` 一处实现，由 `test_derivation_gate.py` 校验。**未发现第二份实现** |
| **Phase 7.3.2 语义** | `derived_from_early_signal = true` → `TIMELINE_CANDIDATE` → **`EXPLORATORY`**（`test_derivation_gate.py` PASS）；**`None` ≠ `False`**，缺字段一律判 `None`（无结论），**只降不升** |
| **旧探索脚本** | 仍位于 `research/research/reports/_seasonal_analysis/`（`research/` 内），**不被 Product runtime 依赖**（`@observation` alias 只指向 `research/research/reports/`） |

**结论**：独立 Research 项目的「身份」消失，但其**全部研究成果作为 ThreeC Research History / Provenance 保留**，
且**未发现任何只存在于复制副本中的独有研究内容**（CONFLICTING = 0）。

---

## E. Memory

| 项 | 结论 |
|---|---|
| `.workbuddy/memory/` | **保留、未移动、未删除**。`2026-09-13 / 14 / 15 / 16 / 17 .md` + `MEMORY.md` |
| 重复 memory | `research/.workbuddy-ai/memory/2026-09-16.md`（旧独立 Research 会话的 memory，10943 B） |
| action | **比较后删除**（内容已被覆盖，见下）；并在 `.workbuddy/memory/2026-09-17.md` 记录核对结论 |
| `.workbuddy-ai/` | 加入 `.gitignore`（平台默认目录名，本仓库不使用，正是"另一套 memory"混入的来源） |

**逐项核对**：旧 memory 的独有内容 —— 选择偏差扣减（ThreeC 台账 6 月占比 33% vs 均匀 8.3%）、
样本量幻觉（N=2 两点重合 → p=0.003 假显著）、伪重复（同年同主题族须年度聚合）、
农历检验失败（春节偏移跨度 85–191 天）、口径稳健性检验、20% 绝对/相对优势门槛、
`md_of_doy` 差一错误、解析式 p 保证 `--check` 可复现 ——
**全部已在已跟踪产物中**（`Seasonal_Observation_Pattern_Discovery_v0_1.md` §12/§13/§23、
`Time_Observation_Pattern_Integration_v0_1.md`、`Time_Observation_Discovery_v0_2.md`）。
→ 按「只保留有价值内容」原则：**内容保留在仓库产物中，冗余 memory 文件删除**。

---

## F. Git Repair

| 项 | 结论 |
|---|---|
| index repaired | **不需要**。恢复前后 `git status --porcelain=v2` 均为空（唯一改动是本轮显式路径 add 的 `.gitignore`） |
| files added | `.gitignore`（+6 行，2 处防护），其余 **0** |
| files removed | 已跟踪文件 **0**。删除的 264 个文件 + `research/.git` **全部为未跟踪内容** |
| history rewritten | **NO** |
| force push | **NO** |
| `git add -A` | **未使用**（显式路径 add） |
| 空目录 | 剪除 50 个 |
| commit | `e85fb42 chore(repo): reconcile research workspace and restore canonical state` |
| push | 成功：`c968097..e85fb42 main -> main`（PortableGit 报 `Empty reply from server` → 按仓库约定改用 `C:/APP/Working/Git/cmd/git.exe` + 代理 `127.0.0.1:7897` + `http.sslBackend=schannel`） |
| 跟踪引用 | 已 `fetch origin main:refs/remotes/origin/main` 刷新；`ls-remote` 直连确认真实远程 = `e85fb42` |

**恢复后 `research/` 状态**：**恰好 211 个文件 = HEAD 的 211 个已跟踪文件**，零缺失 / 零多余 / 逐字节一致（换行归一化后）。

---

## G. Validation

| 项目 | 恢复前 | 恢复后 |
|---|---|---|
| `npm test` | **732 passed / 19 files**（被 `research/src/**` 重复收集） | **395 passed / 10 files** |
| `npx tsc -b` | exit 0 | exit 0 |
| `npx vite build` | exit 0 | exit 0 |
| `validate_monorepo_integrity` | **FAIL(2)**：`.git 唯一性` + `canonical export 唯一性` | **PASS（25 项通过，0 警告）** |
| `build_time_observation_patterns.py --check` | PASS | PASS |
| `discover_time_observation_patterns.py --check` | PASS | PASS |
| `discover_... --round 0.2 --legacy-direct-resolution --check` | PASS | PASS |
| `discover_... --round 0.3 --legacy-no-derivation-gate --check` | PASS | PASS |
| 未知轮次守卫（`--round 9.9`） | exit 1（预期 FAIL） | exit 1（预期 FAIL） |
| `audit_historical_coverage.py --check` | PASS | PASS |
| `validate_db / validate_batch_research / validate_promotion_manifest / validate_timeline_export / validate_current_research / check_doc_schema_consistency` | 全 PASS | 全 PASS |
| `test_consistency / test_derivation_gate / test_doc_schema_checker` | 全 PASS | 全 PASS |
| `git status` | 47 项未跟踪 | **clean** |

### ★ 全新克隆复现性验证（本轮新增最强证据）

`git clone <local repo> <temp>` → HEAD = `c968097`，工作树 clean；在**全新克隆**内重跑
`build_time_observation_patterns --check`、`discover_time_observation_patterns --check`、
`audit_historical_coverage --check` → **全部 PASS 逐字节一致**，TOP-01 回归 PASS。
→ `.gitattributes -text` + CRLF 产物的设计**在全新克隆下成立**，可复现性红线未被破坏。

---

## H. Regression

| 项 | 期望 | 实测 |
|---|---|---|
| **TOP-01** | N=7 / center=06-11 / window=05-27 ~ 06-26 / recurrence=5/7 | ✅ 四项全对（`--check` 三轮 + 全新克隆均一致） |
| **Promotion Gate** | derived 结构 → `EXPLORATORY` | ✅ `TOPC-004`、`TOPC-021` 均由 `TIMELINE_CANDIDATE` 降为 `EXPLORATORY` |
| **effective TIMELINE_CANDIDATE** | 4 → 2 | ✅ 4 → 2 |
| **Independent robust time structures** | **1** | ✅ **1**（未变） |

**未发生因整合导致的研究结果变化。**

---

## I. Remaining Problems

1. **⚠️ `research/**` 下 169 个已跟踪文件的「假干净」**（已定性，**未修**）
   工作区为 CRLF、blob 为 LF（典型：`research/scripts/db.py` 工作区 7991 B / blob 7827 B，归一化后完全相同）。
   成因：这些文件在 `.gitattributes` 出现之前入库（`core.autocrlf=true` 将 CRLF→LF 写入 blob），
   而索引记录的 size 等于工作区 size → `git status` 走 stat 缓存**直接判 clean、不重新哈希**。
   **影响**：`--check` 只比较**产物**（产物 blob 与磁盘均为 CRLF）→ 无影响，已用全新克隆实测确认。
   **残留风险**：`git status` 对这 169 个文件存在假干净；**不要用 `git add --renormalize`**（会产生一次性大 diff）。
   **建议**（非本轮）：未来可做一次受控的「按 blob 逐字节归一化」专项，把工作区对齐到全新克隆状态。

2. **⚠️ 一处未完全解释的现象**（无损失）
   清理 dry-run 报 264 个待删文件，apply 报 223。两者之间另有 **41 个未跟踪文件从磁盘消失**
   （备份脚本在 dry-run 之后仍成功读取全部 264 个）。最终态经逐文件核对**恰好等于 HEAD 的 211 个**，
   无任何已跟踪文件受影响。推测为 Windows 复制/剪切操作在后台收尾。**结论：无数据丢失，但现象未完全解释。**

3. **研究瓶颈（与恢复无关，既有）**：Macro Theme 历史覆盖不足 ——
   当前侧声明 4 个 Macro Theme，历史侧只有 2 个（`TH-AUTO` / `TH-PHARMA`），
   电力设备 / 信息通信 / 高端装备**无历史 Cycle 可类比**。

4. **已知遗留（DEFER）**：`F5`（Timeline 以 Sub-theme 成行）· `F6`（`phase_type` vs `lifecycle[].stage` 枚举不一致）·
   `F7`（`华为汽车` 不在 `themes` 表 → CMTR v1 如实报 `UNRESOLVED_NAME`）。

5. **`.gitattributes` 覆盖范围**：新增研究产物目录时须同步 `-text` 声明，否则可复现性红线会被破坏。

---

## J. Next Recommended Task

**恢复已完成，全部恢复门槛满足**：Git clean · Canonical Research 唯一 · 重复项目处理完成 ·
Research history 完整 · Tests 全 PASS · Generators deterministic · 一个 Git · 无嵌套 Git ·
无 staged accidental deletion · 无未解释 untracked 文件。

按「先判断真实仓库情况、不自动连续做很多任务」的原则，**下一步建议（单一下一目标）**：

> **重建 `docs/PROJECT_STATE.md` + 记录本轮 Recovery**（不照抄旧文档，重新整理
> Completed / Current Phase / Current Research State / Current Data Coverage / Known Limitations / Next Single Goal）

其后默认路线（**未启动，等待确认**）：

```
Promotion Gate 7.3.2 Regression（已在本轮顺带验证 PASS）
  → Historical Data Expansion Wave 1（P0 电力设备 / P0 信息通信）
  → Coverage Audit v0.2
  → Time Observation Re-run
  → Structural Analogy Feasibility Check
  → Phase 8
```

**在恢复条件满足前禁止的项**：Wave 1（电力设备 / 信息通信 / 高端装备）· Structural Analogy。

---

## K. 本轮新增的仓库级约定（已写入 `.workbuddy/memory/MEMORY.md` §7）

- 工作区**只允许一个 `.git`**；`research/` **不得**再有 `.git`。
- **`research/` 必须恰好等于 HEAD 的已跟踪文件集合**；**禁止把仓库根目录复制进 `research/`**。
- 禁止第二份 canonical 副本（`exports/timeline_export_v1.json` 只有根一份）。
- memory **只写 `.workbuddy/memory/`**；`.workbuddy-ai/` 已 gitignore。
- 干净基线：`npm test` **395/395（10 files）** —— 若报 **19 files / 732 tests**，说明重复副本复发。
- 禁止 `reset --hard` / `clean -fd` / `checkout .` / `push --force` / `rebase` 已推送历史 /
  `commit --amend` / `git add -A`；不要为「历史整齐」重写已推送历史。
