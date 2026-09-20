# R01-05 Intake Review — Addendum v0.1（K1 / K2 修正复核）

> **性质**：对 `docs/R01_05_INTAKE_REVIEW_v0_1.md` 的**增量复核**（K1 / K2 定向修正后）。
> **不覆盖上一轮记录** —— 上一轮文档保持原样（点-in-time 记录）。
> **本轮未创建 Canonical Campaign · 未导入 DB · 未修改既有 Campaign · 未修改 taxonomy ·
> 未修改 Schema / Protocol · 未刷新 SA / TO · 未启动 R01-05 Canonicalization · 未修改 Package。**

---

## 1. Package 基础复核

### 1.1 改动范围（逐文件比对：上一轮 HEAD vs 修正版）

| 文件 | 改动 |
|---|---|
| `checksums.sha256` | **2 增 / 3 删** —— 删除 `README.md` 行，10 条 ✓ |
| `manifest.json` | **3 增 / 3 删** —— `generated_at` · `task_scope.excluded_scope` · `cross_task_notes[2].note` |
| `coverage.md` | **1 增 / 1 删** —— 仅 `generated_at` |

**其余 8 个文件逐字节未变** ✓（`candidates.json` · `evidence.json` · `sources.json` · `securities.json` ·
`exclusions.json` · `conflicts.json` · `research_questions.json` · `quality_summary.json`）

### 1.2 ★ 校验结果 → **全部 PASS**

| 检查 | 结果 |
|---|---|
| **11 个正式文件** | ✅ 齐备（10 数据文件 + `checksums.sha256`） |
| **checksum 10 / 10** | ✅ **ALL OK** —— 条目 10 · 文件 10 · 未纳入 **无** · 引用但不存在 **无** |
| **C01–C25** | ✅ **PASS（0 FAIL / 0 WARN）** · `INFO C25 Strict Draft-07 校验通过（0 违规）` |
| **C25 Strict Draft-07**（独立 `jsonschema` 4.26.0 复核） | ✅ **0 违规** |
| **`intake --check`** | ✅ **PASS（0 FAIL / 0 WARN）· packages found: 5** |
| **`validator tests`** | ✅ **PASS（44 / 44）** |

> ★ **`svgREADME.md` 说明已落实**：Worker Workspace 中的 `svgREADME.md` **未进入 ThreeC Package**，
> 也**未进入 checksums** —— 修正后 `checksums.sha256` 恰为 **10 条 / 10 文件**，与 R01-01~R01-04 **完全一致** ✓

---

## 2. K2 复核 → **已关闭**

### 2.1 `manifest.task_scope.excluded_scope`（新版全文要点）

> 「…本包额外声明（**v2，2026-09-20 修订，取代 v1 的「富途行情接口不可用、未取得任何一级行情数据」表述**）：
> **已通过富途（moomoo）行情接口取得一级行情数据（Evidence E130—E141 / Source S057—S061，覆盖 15 个锚点日 × 6 个标的）**，
> 但该数据为**锚点日端点口径**，不是连续日线序列，因此未做日线校准，峰值精确日期、波动率与最大回撤仍不可判定；
> **Beta 中性验证仍未完成**（仅取得相对沪深300 的区间超额，未做 Beta 调整与风格因子剥离，**不得表述为行业 Alpha**）；
> 个股为前复权（含股息再投）而沪深300 为价格指数（不含股息），存在口径差（**见 CF013**）；
> 2015—2016 年前复权序列存在复权因子异常，**Priority B（R01-FINRE-011 / R01-FINRE-012）未采用量化相对收益证据**，
> 其市场响应层仍为空白；Tier 4 来源不作为独立证据。」

| 复核项 | 结果 |
|---|---|
| 已删除 v1「未取得任何一级行情数据」的**过时表述** | ✅ **已删除** —— 新文本**显式声明「取代 v1 的…表述」**（v1 字样仅作为**被取代的引用**出现，非残留） |
| 已准确反映 v2 已取得 E130–E141 一级行情 | ✅ 「已通过富途（moomoo）行情接口取得一级行情数据（E130—E141 / S057—S061，覆盖 15 个锚点日 × 6 个标的）」 |
| 保留「仅锚点端点、未完成 Beta 中性验证」等 caveat | ✅ **全部保留**：锚点端点口径 · 无连续日线 · **Beta 中性验证仍未完成** · **不得表述为行业 Alpha** · 复权口径差（CF013）· Priority B 留空 |
| **`cross_task_notes.N003` 与 v2 的 005 / 009 一致** | ✅ **一致** —— N003 现写「2024-09（**R01-FINRE-005，CONFLICT / medium**）、2020-07（**R01-FINRE-009，CONFLICT / medium**）、2018—2019（R01-FINRE-003，INSUFFICIENT / low）」，**与 `candidates.json` 的实际状态逐项吻合** ✓ |

### 2.2 数量复核 → **全部未变** ✓

| 项 | 上一轮 | 修正版 | 一致 |
|---|---:|---:|---|
| Candidates | 12 | **12** | ✅ |
| Evidence | 63 | **63** | ✅ |
| Sources | 60 | **60** | ✅ |
| Securities | 15 | **15** | ✅ |
| Conflicts | 13 | **13** | ✅ |
| Research Questions | 13 | **13** | ✅ |
| Exclusions | 12 | **12** | ✅ |
| Macro Theme Proposals / Cross-task Notes | 7 / 6 | **7 / 6** | ✅ |

★ `quality_summary.counts` 与实际数组长度**逐项一致** ✓
★ `confidence_distribution` = `high 0 / medium 8 / low 4` **未变** ✓

---

## 3. ★ 重点检查：S012 / S013

### 3.1 逐条核查

| source | type / tier | `independence_group` | 实际支持的事实 |
|---|---|---|---|
| **`S011`** | regulator / **tier 1** · 中国政府网（中国人民银行） | `IG-PBOC-517` | 央行 2024-05-17 政策：首付 15%/25% + 取消全国层面房贷利率下限 + 公积金 -0.25pct · **`primary_source = true`** |
| **`S012`** | regulator / **tier 1** · 中国政府网 | **`IG-PBOC-517`** ← **与 S011 同组** | **同一条央行/金融监管总局通知的部门动态稿**（**同一事实**） |
| **`S013`** | media_tier2 / tier 2 · 中国新闻网 | `IG-CNR-517` | **中新社对央行同一政策公告的同期报道**（**转述**） |
| `S014` | media_tier2 / tier 2 · 经济日报（中国经济网） | `IG-CE-517` | 3000 亿元保障性住房再贷款（**已被 E012 引用**） |
| `S015` | research_report / tier 2 · 东方财富 | `IG-RPT-517` | 券商对四部委政策组合的同期点评（**已被 E013 引用**） |

### 3.2 `E011` / `E012` 是否确实引用了对应事实 → ✅ **是**

| evidence | 引用的事实 | source | IG |
|---|---|---|---|
| **`E011`** | 首套/二套最低首付降至 **15% / 25%** · **取消全国层面房贷利率政策下限** · 公积金利率 **-0.25pct** | `S011` | `IG-PBOC-517` ✓ |
| **`E012`** | 央行设立 **3000 亿元保障性住房再贷款** | `S014` | `IG-CE-517` ✓ |

★ `candidates[002].date_candidates.start` 的 `source_ids = [S011, S014]` · `evidence_ids = [E011, E012]` —— **锚点引用完整** ✓
★ **两个事实均已由 evidence 覆盖，不存在事实缺失** ✓

### 3.3 是否应该作为 Evidence 的 provenance 挂接 → ❌ **不应该**（两者均不挂接）

| source | 判定 | 理由 |
|---|---|---|
| **`S012`** | ❌ **不挂接** | 它与 `S011` **同属 `IG-PBOC-517`**（**同一条通知的同源稿件**）。Protocol 明确「**同源转引必须同 group**」→ 挂接只会**重复计入同一 independence_group**，**不增加独立证据数**，属**无意义挂接** ✓ → **有意保留为背景 Source** ✓ |
| **`S013`** | ❌ **不挂接**（**且 IG 标注存疑**） | 中新社的报道是**对央行同一政策公告的转述**，按 Protocol「同源转引必须同 group」**本应归 `IG-PBOC-517`**，而它当前被标为独立的 `IG-CNR-517`。**若挂接，会虚增一个 independence_group** → **不得挂接** ✓ |

### 3.4 是 Package 数据缺陷还是可接受的背景 Source

| source | 定性 | 是否必须在 Canonicalization 前修复 |
|---|---|---|
| **`S012`** | ✅ **可接受的背景 Source**（记录同源关系，**非缺陷**） | ❌ **不必** |
| **`S013`** | ⚠️ **可接受的背景 Source**，但 **`independence_group` 标注与 Protocol 的同源规则不符** | ❌ **不必**（**未被任何 evidence 引用 → 不影响任何候选的 IG 计数**）→ 建议后续统一，**非阻塞** |

> ## ✅ **结论：S012 / S013 均不应挂接，本轮判定为「有意保留」**
> ★ **未为了消除 orphan 而机械把 Source 强行挂到 Evidence** ✓
> ★ **未虚构任何关系** ✓
> ★ 6 个孤儿 source（`S005`/`S012`/`S013`/`S019`/`S024`/`S029`）**与上一轮完全相同** —— 修正版**未触碰** `sources.json` ✓

---

## 4. 其余上一轮结论 → **全部继续有效**

| 上一轮结论 | 状态 |
|---|---|
| **`001` / `002` / `003` 的市场层证据及证伪** | ✅ **不变** —— `001` 有条件进入（`CF011` 两龙头方向相反）· `002` **市场层强反向证伪**（保利 -31.3% / 万科 -29.8%）→ Research Only · `003` **证伪** + `INSUFFICIENT` → Research Only |
| **`005` / `009` = CONFLICT** | ✅ **不变** —— 两者均 `CONFLICT / medium`（`N003` 已与之对齐 ✓） |
| **`006` / `007` / `008` / `010` 的金融内部机制区分** | ✅ **不变** —— `007`（资金配置驱动）与 `008`（信用周期驱动）机制相反且**未合并**；`006` 估值叙事；`010` 保险资产/负债端 |
| **Beta caveat** | ✅ **不变** —— 修正版 `excluded_scope` **完整保留**（且比上一轮**更集中、更明确**） |
| **金融与房地产未形成单一 Campaign** | ✅ **不变** —— `coverage.md §7` 未改；`MT002` 的 `金融地产` **CMTR 未解析为根** |
| **Priority B `011` / `012` 数据不足** | ✅ **不变** —— 两者均 `INSUFFICIENT / low`，市场层空白 |
| **CMTR v1 无阻塞性 taxonomy gap** | ✅ **不变** —— 12/12 候选 RESOLVED（房地产 5 + 金融 7）；`MT006`/`MT007`（MECHANISM）UNRESOLVED **正确** |
| **12 个 Candidate 的准入结论** | ✅ **不变** —— **7 有条件进入 · 1 需补证（008）· 4 Research Only（002/003/011/012）** |
| **13 条 Conflict 及其优先级** | ✅ **不变** —— **P0**：`CF013` `CF003` `CF004` `CF001` `CF007` · **P1**：`CF011` `CF008` `CF005` `CF006` `CF012` · **P2**：`CF002` `CF009` `CF010` |

> ★ **无实质变化** —— 修正版仅改动 `checksums.sha256` / `manifest.json`（描述性字段）/ `coverage.md`（时间戳），
> **未触碰任何 research 数据**（`candidates` / `evidence` / `sources` / `securities` / `conflicts` / `exclusions` / `research_questions` / `quality_summary` **逐字节未变**）✓

---

## 5. C19 / Schema 与富途 MCP

- **C19 / Schema**：继续使用当前 ThreeC Validator + C25 → **C01–C25 PASS · Strict Draft-07 0 违规** ✓
  上一轮结论「**C19 严于 Schema 属实，但属 Validator 业务规则分层，不构成真实冲突**」**继续有效** ✓
  （Schema 的 `point_in_time_note.description` 写「必填」但无 `if/then` 强制 —— 仍为**记录项**，本轮不处理）
- **富途 MCP 限制**：✅ **确认未影响当前正式 Package** —— 修正版仍含 E130–E141（12 条）与 S057–S061（5 条），
  且 `manifest.excluded_scope` 已**准确记录**其造成的两项限制（无连续日线 / Priority B 留空）✓ **不做工程修改** ✓

---

## 6. 最终结论

### A. 修正版 Package 是否 PASS

> ## ✅ **PASS**

C01–C25 **PASS（0/0）** · C25 Strict Draft-07 **0 违规** · checksum **10/10 ALL OK** ·
`intake --check` **PASS（0/0）** · `validator tests` **44/44 PASS**

### B. K1 / K2 是否关闭

> ## ✅ **两者均已关闭**

| # | 问题 | 状态 |
|---|---|---|
| **K1** | `checksums.sha256` 引用不存在的 `README.md` → C20 FAIL | ✅ **已关闭** —— 该行已删除；checksums 现为 **10 条 / 10 文件**，与 R01-01~R01-04 一致 |
| **K2** | `manifest.excluded_scope` 的 v1 残留文本与 v2 矛盾 | ✅ **已关闭** —— 已重写为 v2 口径，**显式声明取代 v1 表述**；caveat 全部保留；`N003` 已与 005/009 对齐 |

### C. S012 / S013 是否需要修复

> ## ❌ **不需要修复**（**有意保留**）

- **`S012`**：与 `S011` **同属 `IG-PBOC-517`**（同一通知的同源稿件）→ 挂接**无增益** → **有意保留为背景 Source** ✓
- **`S013`**：**对央行同一政策公告的转述**，按 Protocol 应归 `IG-PBOC-517`；当前标为 `IG-CNR-517` ——
  **若挂接会虚增 independence_group** → **不挂接** ✓
  ★ **附带记录（非阻塞）**：`S013` 的 `independence_group` 标注与 Protocol 的同源规则不符；
  因其**未被任何 evidence 引用**，**不影响任何候选的 IG 计数** → 建议后续统一
- ★ **未机械挂接、未虚构关系** ✓；两个事实（首付/利率、3000 亿再贷款）**均已由 E011 / E012 引用**，**无事实缺失** ✓

### D. 12 个 Candidate 的 Canonicalization 准入结论是否保持

> ## ✅ **保持** —— 7 有条件进入（`001` `004` `005` `006` `007` `009` `010`）· 1 需补证（`008`）· 4 Research Only（`002` `003` `011` `012`）

### E. 13 个 Conflict 是否保持

> ## ✅ **保持** —— 13 条全部保留、一条未消解；优先级不变
> **P0**：`CF013` · `CF003` · `CF004` · `CF001` · `CF007` ｜ **P1**：`CF011` `CF008` `CF005` `CF006` `CF012` ｜ **P2**：`CF002` `CF009` `CF010`

### F. 是否可以正式进入 R01-05 Canonicalization

> ## ✅ **可以正式进入**

| 条件 | 状态 |
|---|---|
| Package 通过 Intake（C01–C25 + Strict Draft-07） | ✅ PASS / 0 违规 |
| checksum 完整 | ✅ 10/10 ALL OK |
| `intake --check` / `validator tests` | ✅ PASS / 44-44 |
| 必须修复项 | ✅ **0**（K1 / K2 均已关闭） |
| CMTR v1 | ✅ 12/12 RESOLVED · **无阻塞性 taxonomy gap** |
| 13 条 Conflict 已分级 | ✅ P0×5 · P1×5 · P2×3 |

**进入 Canonicalization 时须一并提交 Canonical Decision 的事项**：
1. 13 条 Conflict 全部裁决（**P0 优先**，尤其 **`CF013` 口径差** —— 它系统性影响所有银行候选的幅度结论）
2. `002` / `003` / `011` / `012` 按 **Research Only** 处置；`008` 按**补证**处置
3. `E141`（沪深300 基准）被 10 个候选共享 → 须决定 1:1 归属处理方式
4. `E132`(004,008) / `E137`(007,010) / `E140`(006,007) 须做 1:1 消歧
5. 6 个孤儿 source（含 `S012` / `S013`）**保留不挂接**，其定性已在本文件记录

---

## 7. 本轮严格未做

- ❌ 未创建 Canonical Campaign · 未导入 DB · 未修改既有 Campaign
- ❌ 未修改 taxonomy · Schema · Protocol · Validator
- ❌ 未修改 R01-05 Package 的任何字节
- ❌ 未刷新 Structural Analogy / Time Observation
- ❌ 未启动 R01-05 Canonicalization
- ❌ 未机械挂接任何 orphan source · 未虚构关系
