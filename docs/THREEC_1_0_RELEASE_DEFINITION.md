# THREEC_1_0_RELEASE_DEFINITION.md — ThreeC 1.0 发布定义

> | 项目 | 值 |
> |---|---|
> | **文档性质** | **1.0 的正式发布定义（永久锁定）**。任何「宣布 1.0」的判断都必须以本文件为准。 |
> | **建立日期** | 2026-09-24 |
> | **审计基线** | HEAD `ad5e804`（Research Lifecycle Mapping Repair v0.1） |
> | **复核基线** | `7c7d64f`（P0 修复轮）· `1e42b6c`（Deployment 轮末次提交） |
> | **本轮性质** | **定义 + Gap Audit** —— 不开发新功能、不优化 Research、不扩 Universe |
> | **上游文档** | `docs/PROJECT_STATE.md`（动态状态）· `docs/ROADMAP.md`（路线） |

---

## 0. 第一句

> # **ThreeC 1.0 = 一个可以长期使用的 A 股历史机会时间轴 / 历史机会地图核心产品。**

**核心价值**：

> **从历史周期里找结构，而不是从历史数据里找同名主题。**

**最终用户核心任务（1.0 必须端到端可完成）**：

```text
今天在哪里
    ↓
历史同期发生过什么
    ↓
相关历史周期处于什么生命周期
    ↓
当前研究对象是什么
    ↓
历史上有哪些结构可比较
    ↓
为什么对应 / 为什么不同
    ↓
还缺什么证据
    ↓
形成新的研究问题
```

**ThreeC 明确不是**（永久边界）：

买卖信号 · 选股 / 荐股 · 价格预测 · 收益预测 · 概率 / 胜率 · 排名系统 · 自动交易 ·
实时行情系统 · AI 自动投资决策系统。

---

## 1. Release Gates（硬 Gate，不是「整体感觉差不多」）

1.0 必须在**全部 8 个 Gate 上同时成立**。任一 Gate 存在 **P0**，即**不得宣布 1.0**。

---

### Gate R — Research

| # | 要求 | 判定 |
|---|---|---|
| R1 | Historical Universe = **52 Campaign + 27 Research Candidate = 79 Historical Objects** | 精确 |
| R2 | Research Core = **Driver v0.4 · SA v0.5 · TO v0.2 · lifecycle 从 Intake 派生** | 精确 |
| R3 | **冻结**：Research Model v1.0 · `schema.sql` · Export Contract v1.0 · CMTR v1 · SA Rule Set v0.3（R1–R4）· TO 标准不放宽 | 逐字节 |
| R4 | lifecycle 完整性 | 见 §1.1 |

#### 1.1 lifecycle 完整性的正式定义（**不把「27/27 非空」作为硬标准**）

```text
27 / 27 Research Candidate 必须有「可追溯的 lifecycle 来源处理结果」：

  · 可识别阶段  → 进入 export.lifecycle（含 PEAK；open-ended 段保持 end=null）
  · 仅 UNKNOWN  → 保持 export.lifecycle 为空
                  + 明确 unknown / insufficient 语义（由 research_status 承载）
                  + 来源与原因可追溯（validator 记录）
```

**禁止**：
- 把 `UNKNOWN` 映射成具体阶段；
- 为了填充字段而虚构生命周期；
- 为达到「27/27 非空」而升级 Export Contract 或 `schema.sql`。

> **依据**：`UNKNOWN` 不是生命周期阶段，而是「阶段不可识别」。把它写成 `lifecycle.stage` 会违反
> Export Contract v1.0 的 stage 枚举；把它映射成 `MAIN_RISE` 等具体阶段则是**虚构研究结论**。

---

### Gate P — Product Core

必须端到端走通：

```text
Today → Current Candidate → Time / Calendar → Lifecycle
  → Structural Analogy → Historical Case → Evidence
  → Why Similar / Why Different → New Research Question
```

| # | 要求 |
|---|---|
| P1 | **全部 5 个 Current Candidate** 可完整走通（0 例外） |
| P2 | Campaign 与 Research Candidate **身份绝对区分**；RC 不冒充 Campaign |
| P3 | Historical Case 可到达（两类对象均可） |
| P4 | Structural Analogy **四维可读**（生命周期 / 驱动机制 / 证据顺序 / 事件结构，均有人类可读标签） |
| P5 | `UNKNOWN` / `NOT_AVAILABLE` / `MISMATCH` **清晰区分** |
| P6 | `PERIPHERAL_OVERLAP` 不进入 supported |
| P7 | `CROSS_MACRO_THEME` 不成为 `why_not` 的理由（仅作 metadata） |
| P8 | **无 score / ranking / probability / prediction / look-ahead** |

---

### Gate T — Trust / Semantic Safety

**1.0 必须硬锁住的一层。**

| # | 不变量 |
|---|---|
| T1 | **历史事实**：不编造日期、涨幅、代表股、阶段 |
| T2 | `UNKNOWN ≠ MISMATCH` |
| T3 | `NOT_AVAILABLE ≠ MISMATCH` |
| T4 | `INSUFFICIENT ≠ FAILED` |
| T5 | `PROVISIONAL ≠ VERIFIED` |
| T6 | `已结束 ≠ 当前活跃` |
| T7 | `end = null ≠ 已结束`（也不等于「仍在扩张」） |
| T8 | **`UNKNOWN ≠ 自动推导具体阶段`** |
| T9 | 历史复现必须表述为「**历史上出现过**」，不得写成「**未来将再次发生**」 |

---

### Gate Q — Product Quality

| # | 要求 |
|---|---|
| Q1 | `npm test` **0 failed** |
| Q2 | `tsc -b` **PASS** |
| Q3 | `vite build` **PASS** |
| Q4 | 无 runtime crash |
| Q5 | `null` `start` / `end` 安全 |
| Q6 | 5 / 5 workflow test PASS |
| Q7 | SA v0.5 Product adapter 正确（不消费旧 artifact） |
| Q8 | TO v0.2 Product adapter 正确 |
| Q9 | mobile layout 可用（375 / 390 / 412px） |
| Q10 | 长文本不裁切；空态可理解 |
| Q11 | Research / Product provenance 可追溯 |

---

### Gate U — Real Usage / Human Usability

**不得只依赖自动测试。** 以下 5 个场景必须可重复走通（已固化为
`src/data/timeline/__tests__/releaseGateScenarios.test.tsx`）：

| 场景 | 要求 |
|---|---|
| **A** | 时间窗口命中 TOP-01：`Today → Time Observation → 历史案例 → 生命周期 → Structural Analogy` 全链路可走 |
| **B** | 无匹配 Pattern 的窗口：**正常显示「暂无符合标准的历史结构」**，不是「错误」 |
| **C** | 一个 Research Candidate：**明确告知是 Research Candidate，不是正式 Campaign** |
| **D** | 一个 lifecycle 仅 UNKNOWN 的 RC：用户能理解「**没有足够生命周期信息**」，**不被错误阶段误导** |
| **E** | 一个 `end` 已知的历史 Campaign：**不显示成「当前仍处于扩张」** |

---

### Gate M — Mobile

至少验证 **375px / 390px / 412px**。重点不是「页面不崩」，而是：

| # | 要求 | 状态 |
|---|---|---|
| M1 | Timeline 可横向查看（`.timeline` min-width 1080px 由 `overflow-x: auto` 承载） | ⏳ 待真机复核 |
| M2 | Detail 不裁切（内容换行而非隐藏） | ⏳ 待真机复核 |
| M3 | lifecycle 可读 | ⏳ 待真机复核 |
| M4 | SA 四维可读 | ⏳ 待真机复核 |
| M5 | 长 ID / 长文本不破坏布局 | ⏳ 待真机复核 |
| M6 | 空态可读 | ⏳ 待真机复核 |
| M7 | 页面纵向信息层级明确 | ⏳ 待真机复核 |

> **★ Gate M 状态 = 未完成 / 待真机**（此前仅为 375/390/412px 断点的**静态审计**，非真实浏览器复核）。
> 真机测试对象：**线上** `https://yangfanbit.github.io/Cycle/`（而非本地 dev）。

---

### Gate D — Deployment / Release Engineering

**本文件首次正式定义**（此前仓库**没有任何部署配置、没有 git tag**）。

> **★ 必须区分两个不同概念（不得混为一谈）**：
>
> | 概念 | 内容 | 状态 |
> |---|---|---|
> | **Deployment Engineering** | production build · GitHub Pages · URL · CI/CD · provenance · rollback · rebuild flow | ✅ **已完成** |
> | **正式 1.0 Release 条件**（D4 / D5） | `package.json version = 1.0.0` · `git tag v1.0.0` | ⏳ **Gate M 通过后由独立 Release 轮执行** |
>
> `Gate D = PASS` 在此表示 **Deployment Engineering 已完成**，
> **不等于**已执行正式 1.0 Release。

1.0 必须具备：

| # | 要求 | 状态 |
|---|---|---|
| D1 | production build（`npm run build` → `dist/`） | ✅ |
| D2 | **正式部署方式**（见 §2） | ✅ GitHub Pages |
| D3 | **正式访问入口**（URL） | ✅ `https://yangfanbit.github.io/Cycle/` |
| D4 | `version = 1.0.0`（`package.json`） | ⏳ 宣布时设置（现 `0.1.0`） |
| D5 | **release commit** + **Git tag**（`v1.0.0`） | ⏳ 宣布时创建 |
| D6 | **可回滚**到上一个稳定版本（基于 commit SHA + 重新部署） | ✅ 见 `DEPLOYMENT_RUNBOOK.md` §7 |
| D7 | **Research artifact ↔ Product build 的版本对应关系**（可追溯） | ✅ `buildProvenance()` |
| D8 | **更新 Research artifact 后的重新构建流程**（见 §3） | ✅ `DEPLOYMENT_RUNBOOK.md` §3 |

---

### Gate G — Documentation

| # | 文件 | 要求 |
|---|---|---|
| G1 | `docs/THREEC_1_0_RELEASE_DEFINITION.md`（本文件） | 存在且为唯一 1.0 判据 |
| G2 | `docs/PROJECT_STATE.md` | HEAD / 当前阶段 / 基线版本**与仓库一致** |
| G3 | `docs/ROADMAP.md` | 与当前阶段一致（Research FROZEN · Product 主线 · 1.0 目标） |
| G4 | `README.md` | 反映真实当前状态（**不得**再出现旧 17-object / SA v0.2 / 「R01 未启动」） |

**禁止**：
- 把 HEAD 写成旧的 `c56e70f`；
- 把旧的 17-object / SA v0.2 状态写成当前状态；
- 把 R01 写成进行中；
- 把 Research Core 写成未完成；
- **把 4 个 lifecycle 仅 UNKNOWN 的 RC 视为「必须修复的数据错误」**（它是 `KNOWN DATA LIMITATION`）。

---

## 2. 部署方案（Gate D2，**已落地**）

**原则**：**纯静态站点**，**不引入后端**，**不引入 LLM runtime**。

| 项 | 方案（**已实施**） |
|---|---|
| 构建产物 | `npm run build` → `dist/`（静态 HTML/JS/CSS，无服务端） |
| 部署形态 | **GitHub Pages**（唯一平台；不使用 Vercel / Netlify / Docker / 云服务器 / CDN 产品化） |
| 访问入口 | **`https://yangfanbit.github.io/Cycle/`** |
| `base` | `resolveBase()`：`THREEC_BASE` 显式覆盖 > `GITHUB_ACTIONS === 'true'` → `/Cycle/` > 默认 `/`（本地 `dev` / `preview` 不受影响） |
| 自动构建 | `.github/workflows/deploy.yml`：push `main` → `npm ci` → `tsc -b` → `npm test` → `npm run build` → 上传 `dist/` → `deploy-pages` |
| 缓存策略 | 由 GitHub Pages 承担；带 hash 的 `assets/*` 天然不可变 |
| 数据来源 | **构建时打包的 Research artifact**（`@exports` / `@observation` 别名 → 仓库内 JSON）→ **运行时无网络请求** |
| 回滚 | revert 到上一稳定 commit → 重新 `npm ci` / `npm test` / `npm run build` → 重新部署（**基于 commit SHA，不依赖 tag**） |
| 版本对应 | `package.json.version` ↔ Git commit ↔ 构建时 `exports/timeline_export_v1.json` 的 `source_commit` ↔ SA/TO artifact 版本（**Product 内 `buildProvenance()` 展示**） |
| 操作手册 | **`docs/DEPLOYMENT_RUNBOOK.md`**（正常发布 / Product-only / Research artifact 更新 / 回滚 / smoke test） |

> **★ 部署已执行，1.0 未发布**：D1–D3、D6–D8 **已落地并验证**；
> **D4（`version = 1.0.0`）与 D5（`v1.0.0` tag）依然不得设置**。
> 部署产物 ≠ 1.0 发布；当前线上身份 = **commit SHA**（不伪造 `v1.0.0` 回滚目标）。

---

## 3. Research artifact 更新后的重新构建流程（Gate D8）

> **完整可执行版本见 `docs/DEPLOYMENT_RUNBOOK.md` §3。** 摘要：

```text
1. 修改 / 重新生成 Research artifact（新版本，旧版本逐字节保留）
2. 运行 Research 验证链（validator 全 PASS；generator --check ×3 deterministic）
3. 运行 lifecycle coverage 校验（Intake == Export 恒等）
4. 若 artifact 影响 Product 输入 → 切换 Product 的 artifact 引用（最小改动，不重构）
5. npm ci · npm test（0 failed）· tsc -b · vite build
6. 记录版本对应关系（见 §2 表格「版本对应」行）
7. 提交并推送 main → GitHub Actions 自动构建 + 部署
8. 线上 smoke test（`DEPLOYMENT_RUNBOOK.md` §6）；失败则回滚（§7）
```

**★ 不允许**：为了让 Product「消化」数据而修改 Product 语义；**Research 是唯一真源**。

---

## 4. 明确**不进入 1.0** 的冻结清单

以下全部进入 **1.1+**，除非真实使用产生新的 **P0** 证据：

```text
Historical Universe Expansion
新 Driver vocabulary
SA Rule 微调
TO Pattern 扩容
similarity score
ranking
probability
OpportunityRadar
Dashboard
notification
real-time market
backend
LLM runtime
自动选股
自动买卖判断
```

---

## 5. Blocker 分级定义

| 级别 | 定义 | 对 1.0 的影响 |
|---|---|---|
| **P0** | 核心研究路径错误 / **用户会被误导** / 数据链损坏 | **必须修，否则不得宣布 1.0** |
| **P1** | 显著影响可用性，但**不改变研究结论** | 1.0 前**应该**修 |
| **P2** | 视觉优化 / 新功能 / 性能增强 / Dashboard / Radar 等 | **1.0 后处理**（**不得为 P2 推迟 1.0**） |

---

## 6. Release Gap Matrix

> 审计基线 HEAD `ad5e804`；**P0 修复后复核基线** 见 §6.1。

| Gate | 当前状态 | 证据 | 是否阻塞 1.0 | 处理任务 |
|---|---|---|---|---|
| **Research** | **PASS** | 52 C + 27 RC = 79 · Driver v0.4 · SA v0.5（395 pairs）· TO v0.2 · lifecycle 由 intake 派生（单一真源）· 冻结基座未改 | **否** | — |
| **Product** | **PASS** | 5/5 Candidate 走通闭环（43 用例）· identity 52/27 正确 · 四维可读 · 无 score/ranking/probability | **否** | — |
| **Trust** | ~~★ FAIL（1 项 P0）~~ → **PASS** | T1–T9 **全部通过**：无 research lifecycle 的对象在 Historical Case 中**不再推导出具体阶段**（`[]`），`terminalPhaseOf → UNKNOWN` | ~~★ 是（P0-1）~~ → **已解除** | **已完成（P0 修复轮）** |
| **Quality** | **PASS** | `npm test` **654 passed / 0 failed（17 files）** · `tsc -b` PASS · `vite build` PASS · 无 runtime crash · null 安全 | **否** | — |
| **Real Usage** | **PASS（无缺口）** | 场景 A–E **全部正常通过**；**D3 已由 `it.fails` 正式化为正常断言**；新增 **Scenario F（Gate T8 全局不变量，F1–F9）** | **否** | — |
| **Mobile** | **★ 待真机（当前唯一未闭环）** | 断点 110/240/300/720/900；375/390/412px **全部落在 720px 断点内** · 无 ≥400px 固定宽度（除 timeline 1080px 由 `overflow-x:auto` 承载）· `overflow-wrap` 28 处 · 7 个区块均有移动端规则 —— 以上均为**静态审计** | **是（Gate M）** | 对**线上**入口做真机 / 实际浏览器复核（M1–M7） |
| **Deployment** | **PASS（Deployment Engineering 已完成）** | `.github/workflows/deploy.yml`（GitHub Pages）· 入口 `https://yangfanbit.github.io/Cycle/`（实测 200 OK）· `base = /Cycle/` · `buildProvenance()` 版本对应（D7，线上实测）· `DEPLOYMENT_RUNBOOK.md`（D8 + 回滚 D6）· Actions `build` + `deploy` 全 PASS | **否** | **D4（`1.0.0`）/ D5（`v1.0.0` tag）保留至 Gate M 通过后的独立 Release 轮** |
| **Documentation** | **PASS** | 本文件为唯一 1.0 判据；`PROJECT_STATE` 记录 HEAD → `1e42b6c`（不硬编码旧 SHA）、Gate 状态、P0/P1 = 0；`ROADMAP` §2 = Deployment 主线；`README` 真实当前阶段 + 线上入口并标注「尚未正式发布」 | **否** | — |

### 6.1 P0 修复轮复核（本文件 §8 P0 清单已清零）

| 项 | 修复前 | 修复后 |
|---|---|---|
| `historicalCaseOf` 无 lifecycle 时 | 回退 `c.phases` → 4 个 RC 全部显示「主升 `main_rise`」 | **`lifecycle = []`**（不渲染该字段区）→ 虚构数 **4 → 0** |
| `terminalPhaseOf` 无 lifecycle 时 | 回退 `campaign.phases` → 4 个 RC 全部 `EXPANSION` | **`UNKNOWN`** → 虚构数 **4 → 0** |
| `CampaignDetail` 旧字段区 | 第二处独立 `m.phases` 渲染路径，同样虚构「主升」 | 改读 Research `lifecycle`，空则整区不渲染 |
| `STAGE_TO_PHASE` 覆盖度 | **漏 `ENDED`**（Contract 成员，export 中出现 2 次）→ `phaseOfStage('ENDED')` 静默返回 `UNKNOWN` | 补 `ENDED: 'END'` → 2 个已结束 Campaign 由 `UNKNOWN` 纠正为 **`END`** |
| `derivePhases()` / `c.phases` | — | **完整保留**（Timeline 视觉分段仍依赖；4 个 RC 的 `phases` 均在） |
| D3 用例 | `it.fails`（KNOWN GAP） | **`it(...)` 正常断言**（另加 D3b UI 字段区断言） |
| 防回归 | 无 | 新增 **Scenario F1–F9**（含覆盖度与反向非空断言） |

---

## 7. 那 4 个只有 UNKNOWN lifecycle 的 RC —— **不是 1.0 Blocker**

**判定：`KNOWN DATA LIMITATION`，不阻塞 1.0。**

| 条件 | 状态 |
|---|---|
| 来源明确 | ✅ intake `lifecycle[].stage_proposal = UNKNOWN`，`basis` 记录原因（如「缺连续行情数据」） |
| 没有伪造 | ✅ export `lifecycle` 保持为空，**未映射成任何具体阶段** |
| Product 可明确显示信息不足 | ✅ `research_status = INSUFFICIENT`（3 个）/ `CONFLICT`（1 个）；SA `lifecycle` 维度为「资料不足」而非 `MISMATCH` |
| validator 能防止静默丢失 | ✅ `validate_lifecycle_coverage_v0_1.py` 的 **L4** 专门校验「UNKNOWN 不得被伪装」 |

对象：`RC-2019-RE-EASING` · `RC-2020-FIN-BROKER-VOLUME` · `RC-2016-RE-SHANTY` · `RC-2015-FIN-LEVERAGE`

> **★ 与 P0-1 的关系**：这 4 个对象本身没问题；**问题在 Product 端** —— 它对**任何**无 lifecycle 的对象
> 都会推导出一个 `main_rise` 段。修好 P0-1 后，这 4 个对象会正确显示「生命周期信息不足」。

---

## 8. 1.0 Blocker 清单

### P0 — 1.0 必须修（**当前 0 项，已全部关闭**）

> **P0-1 与 P0-1b 已于「ThreeC 1.0 P0 修复轮」关闭。** 修复细节见 §6.1。

| # | 问题 | 状态 |
|---|---|---|
| ~~**P0-1**~~ | ~~**无 research lifecycle 时，Product 推导出具体阶段**~~ | **✅ 已修** —— `historicalCase.ts` 改读 `c.lifecycle`（空则 `[]`）；`researchAttention.ts::terminalPhaseOf` 删除 `c.phases` 回退 → `UNKNOWN`；`CampaignDetail` 旧字段区改读 Research `lifecycle`。**修的方向**：不得给出具体阶段，保留 `research_status` 语义 |
| ~~**P0-1b**~~ | ~~**注释与行为不一致**~~ | **✅ 已修** —— `historicalCase.ts` 的 `HistoricalCaseView.lifecycle` 注释重写为「**原样**来自 Research 导出的 `lifecycle`」并注明 Gate T8 约束 |

**审计新发现（同属 Gate T8 家族，已随本轮一并关闭，非 1.0 遗留）**

| # | 问题 | 状态 |
|---|---|---|
| **P0-1c** | `researchAttention.ts::STAGE_TO_PHASE` **漏 `ENDED`**（Contract `VALID_LIFECYCLE_STAGE` 成员）→ `phaseOfStage('ENDED')` 静默退化为 `UNKNOWN`；2 个已结束 Campaign（`C-2019-MIL-GROUP-RESTRUCTURE` / `C-2020-RE-DEBT-RISK`）被误显示为「阶段未标注」。语义：`UNKNOWN ≠ 未映射` | **✅ 已修** —— 补映射 + `CONTRACT_LIFECYCLE_STAGES` 常量 + F7/F8/F9 覆盖度不变量 |
| **P0-1d** | `ExportLifecycleStageV1.start/end` 类型写成 `string`，但 Contract 允许 `null`（`is_iso_date(None) == True`）→ 5 处消费点存在 `null` 运行时风险 | **✅ 已修** —— 类型改为 `string \| null`，5 个消费点显式处理开放区间（不猜测端点） |

### P1 — 1.0 前应该修（**当前 0 项**）

| # | 问题 | 状态 |
|---|---|---|
| ~~**P1-1**~~ | ~~**无正式部署方式 / 无访问入口 / 无回滚定义**~~ | **✅ 已闭环（Deployment / Release Engineering 轮）** —— GitHub Pages + Actions 自动构建 + `base=/Cycle/` + `buildProvenance()` + `DEPLOYMENT_RUNBOOK.md`（含回滚）。**未引入后端**。 |

### P2 — 1.0 后处理（**不做**）

| # | 项 |
|---|---|
| P2-1 | `src/components/OpportunityRadar/` **未被 App 引用**（dead code）→ 清理或保留待 1.1 |
| P2-2 | ~~Mobile 真机/浏览器实测复核（本轮为静态审计）~~ → **已提升为 Gate M**（1.0 阻塞项，见 §6 / §9） |
| P2-3 | 视觉 / 动画 / 边距 / 图标等 |

---

## 9. 当前 Single Goal

> # **Gate M 真机 / 实际浏览器复核 + Release Readiness Audit** —— **当前唯一未闭环 Gate**。

**为什么这是唯一剩下的 Gate**：R / P / T / Q / U 已 PASS；Deployment Engineering（D1–D3、D6–D8）已完成；
G（文档）已同步。**Gate M 此前只有 375/390/412px 断点的静态审计，从未做过真实浏览器复核。**

**范围（严格）**：
- 对**线上** `https://yangfanbit.github.io/Cycle/` 做真机复核（375 / 390 / 412px；优先真实 iPhone Safari）；
- 走通完整主链路：`Today → Current Candidate → Time/Calendar → Lifecycle → Structural Analogy → Historical Case → Evidence → Why Similar/Different → New Research Question`；
- 验证 M1–M7，以及 Lifecycle 三类（正常 / UNKNOWN-only RC / ENDED）、Campaign vs RC identity、SA 四维、provenance；
- **不修改**任何 Research artifact / schema / contract / SA rule / TO 标准；
- **不新增**功能、**不引入** router / backend / runtime API；
- **不得**为了通过 Gate M 而删除 `derivePhases()` 或把 `c.phases` 重新当作 Research lifecycle。

**验收**：
```text
[ ] M1–M7 全部通过（真实浏览器，非仅断点审计）
[ ] Lifecycle 三类：正常有阶段 / UNKNOWN-only RC 显示「阶段未判定 · 资料不足」/ ENDED 显示 END
[ ] Campaign ≠ Research Candidate（identity 不混淆）
[ ] SA 四维可读；无 score / ranking / probability / prediction
[ ] 线上 provenance 无 `__THREEC_` / `process.env` / `undefined` / `NaN`
[ ] `/` · `?preview=1` · `?candidates=example` 均可打开，刷新正常
[ ] npm test 0 failed · tsc -b 0 error · vite build PASS（若本轮有代码修改则必须重跑）
[ ] ← 1.0 正式宣布（`1.0.0` + tag）**仍不在本轮**
```

**★ 通过后的结论只有一个**：**ThreeC 已具备进入 1.0 正式 Release 流程的条件。**
**本轮不执行** `1.0.0` / `v1.0.0` / release commit / 正式 Release —— 那是**下一独立 Release 轮**的动作。

---

## 10. 1.0 宣布条件（Checklist）

**只有以下全部为 ✅，才可宣布 ThreeC 1.0：**

```text
[x] Gate R  PASS（含 lifecycle 完整性定义 §1.1）
[x] Gate P  PASS
[x] Gate T  PASS（含 T8）—— ✅ 已通过（P0 修复轮）
[x] Gate Q  PASS
[x] Gate U  PASS（场景 A–E 全部正常通过，无 it.fails）
[ ] Gate M  PASS —— ★ 当前唯一未闭环（待真机 / 实际浏览器复核）
[x] Gate D  Deployment Engineering PASS（D1–D3 / D6–D8 已落地并验证）
    · ⏳ D4 `version = 1.0.0` / D5 `tag v1.0.0` —— 待 Gate M 通过后由独立 Release 轮执行
[x] Gate G  PASS（四份文档与仓库一致）
[x] P0 清单为空
[x] P1 清单已处理或明确接受（P1-1 已闭环）
```

**宣布动作**（顺序固定）：
1. ~~P0 清零~~ ✅ → 2. ~~P1 处理~~ ✅（部署已落地）→ **3. Gate M 真机复核（当前待办）** →
4. `package.json` → `1.0.0` → 5. release commit → 6. `git tag v1.0.0` → 7. 部署 →
8. 验证访问入口 → 9. 更新 `PROJECT_STATE` / `ROADMAP` / `README`。

> **★ 边界**：**Deployment Engineering 完成 ≠ ThreeC 1.0 正式发布。**
> `Gate D = PASS` 表示部署工程已完成；**D4 / D5 不得提前执行**。
> 线上身份为 commit SHA。**在 Gate M 通过前不设置 `1.0.0`、不创建 `v1.0.0`。**

---

*THREEC_1_0_RELEASE_DEFINITION.md · 2026-09-24 · 审计基线 `ad5e804` · 部署轮复核 `7c7d64f` · 永久锁定*
