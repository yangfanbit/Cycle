# THREEC_1_0_RELEASE_DEFINITION.md — ThreeC 1.0 发布定义

> | 项目 | 值 |
> |---|---|
> | **文档性质** | **1.0 的正式发布定义（永久锁定）**。任何「宣布 1.0」的判断都必须以本文件为准。 |
> | **建立日期** | 2026-09-24 |
> | **审计基线** | HEAD `ad5e804`（Research Lifecycle Mapping Repair v0.1） |
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

| # | 要求 |
|---|---|
| M1 | Timeline 可横向查看（`.timeline` min-width 1080px 由 `overflow-x: auto` 承载） |
| M2 | Detail 不裁切（内容换行而非隐藏） |
| M3 | lifecycle 可读 |
| M4 | SA 四维可读 |
| M5 | 长 ID / 长文本不破坏布局 |
| M6 | 空态可读 |
| M7 | 页面纵向信息层级明确 |

---

### Gate D — Deployment / Release Engineering

**本文件首次正式定义**（此前仓库**没有任何部署配置、没有 git tag**）。

1.0 必须具备：

| # | 要求 |
|---|---|
| D1 | production build（`npm run build` → `dist/`） |
| D2 | **正式部署方式**（见 §2 最小可行方案） |
| D3 | **正式访问入口**（URL） |
| D4 | `version = 1.0.0`（`package.json`） |
| D5 | **release commit** + **Git tag**（`v1.0.0`） |
| D6 | **可回滚**到上一个稳定版本（tag 回退 + 重新部署） |
| D7 | **Research artifact ↔ Product build 的版本对应关系**（可追溯） |
| D8 | **更新 Research artifact 后的重新构建流程**（见 §3） |

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

## 2. 最小可行部署方案（Gate D2 设计）

**原则**：**纯静态站点**，**不引入后端**，**不引入 LLM runtime**。

| 项 | 方案 |
|---|---|
| 构建产物 | `npm run build` → `dist/`（静态 HTML/JS/CSS，无服务端） |
| 部署形态 | **静态托管**（对象存储 / 静态站点托管 / 任意 HTTP 静态服务） |
| 访问入口 | 托管平台分配的 HTTPS 域名（或自定义域名） |
| `base` | 若部署在**子路径**，需在 `vite.config.ts` 设 `base: '/<subpath>/'`；根路径部署保持默认 `/` |
| 缓存策略 | `index.html` **no-cache**；带 hash 的 `assets/*` **immutable** |
| 数据来源 | **构建时打包的 Research artifact**（`@observation` 别名 → `research/research/reports/*.json`）→ **运行时无网络请求** |
| 回滚 | `git checkout <上一个 tag>` → 重新 build → 重新部署 |
| 版本对应 | `package.json.version` ↔ Git tag ↔ 构建时 `exports/timeline_export_v1.json` 的 `source_commit` ↔ SA/TO artifact 版本 |

> **★ 部署尚未执行**：Gate D 的 D1–D3、D5–D8 **已设计**，但 **D4（version=1.0.0）与 D5（tag）不得在 1.0 正式宣布前设置**。
> 在存在 P0 的情况下提前打 tag 会造成「版本号已发布但未达标」的不可逆问题。

---

## 3. Research artifact 更新后的重新构建流程（Gate D8）

```text
1. 修改 / 重新生成 Research artifact（新版本，旧版本逐字节保留）
2. 运行 Research 验证链（validator 全 PASS；generator --check ×3 deterministic）
3. 运行 lifecycle coverage 校验（Intake == Export 恒等）
4. 若 artifact 影响 Product 输入 → 切换 Product 的 artifact 引用（最小改动，不重构）
5. npm test（0 failed）· tsc -b · vite build
6. 记录版本对应关系（见 §2 表格最后一行）
7. 部署；必要时回滚到上一 tag
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

## 6. Release Gap Matrix（审计基线 HEAD `ad5e804`）

| Gate | 当前状态 | 证据 | 是否阻塞 1.0 | 处理任务 |
|---|---|---|---|---|
| **Research** | **PASS** | 52 C + 27 RC = 79 · Driver v0.4 · SA v0.5（395 pairs）· TO v0.2 · lifecycle 由 intake 派生（单一真源）· 冻结基座未改 | **否** | — |
| **Product** | **PASS** | 5/5 Candidate 走通闭环（43 用例）· identity 52/27 正确 · 四维可读 · 无 score/ranking/probability | **否** | — |
| **Trust** | **★ FAIL（1 项 P0）** | T1–T7、T9 通过；**T8 未通过**：无 research lifecycle 的对象在 Historical Case 中被 Product **推导出 `main_rise`**（虚构阶段） | **★ 是（P0-1）** | **修 `historicalCaseOf` / `derivePhases` 的无-lifecycle 回退** |
| **Quality** | **PASS** | `npm test` **643 passed / 0 failed（17 files）** · `tsc -b` PASS · `vite build` PASS · 无 runtime crash · null 安全 | **否** | — |
| **Real Usage** | **PASS（含 1 项已知缺口）** | 场景 A/B/C/E 通过；**场景 D 部分通过**（D1/D2/D4/D5 通过，**D3 用 `it.fails` 锁定为 KNOWN GAP** → 同 P0-1） | **否（由 P0-1 覆盖）** | 随 P0-1 一并解决 |
| **Mobile** | **PASS（静态）** | 断点 110/240/300/720/900；375/390/412px **全部落在 720px 断点内** · 无 ≥400px 固定宽度（除 timeline 1080px 由 `overflow-x:auto` 承载）· `overflow-wrap` 28 处 · 7 个区块均有移动端规则 | **否** | **P2：真机/浏览器实测复核**（本轮为静态审计） |
| **Deployment** | **★ FAIL（P1）** | **无任何部署配置**（无 netlify/vercel/docker/.github/wrangler）· **无 git tag** · `package.json version = 0.1.0` · 无访问入口 · 无回滚定义 | **否（P1）** | 落地 §2 最小静态部署 + §3 重建流程；**1.0 宣布时**再设 `1.0.0` 与 tag |
| **Documentation** | **PASS（本轮已修）** | 新建本文件；`PROJECT_STATE` HEAD→`ad5e804`、SA→v0.5；`ROADMAP` 反映 Product 主线 + Lifecycle Repair；**`README` 旧状态（2026-09-19 / v0.2 / 4 Macro Themes）已重写** | **否** | — |

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

### P0 — 1.0 必须修（**1 项**）

| # | 问题 | 位置 | 为什么是 P0 |
|---|---|---|---|
| **P0-1** | **无 research lifecycle 时，Product 推导出具体阶段** | **精确路径**：`historicalCase.ts:243` 的 `lifecycle: c.phases.map(...)` 用的是 **adapter 派生**的 `c.phases`，**不是** export 的 `lifecycle`；而 `timelineAdapter.ts::derivePhases` 在 `peak == null` 时**无条件**返回 `[{ phase: 'main_rise', start, end }]`。→ 无 research lifecycle 的对象（当前 4 个 RC）在 Historical Case 中显示为「主升」。`researchAttention.ts::terminalPhaseOf` 第 3 条回退（视图分段）同理 | 违反 Gate T8（`UNKNOWN ≠ 自动推导具体阶段`）→ **用户会被误导**：研究明确说「阶段不可识别」，产品却显示「主升」。场景 D 的 D3 因此未通过（已用 `it.fails` 锁定） |
| **P0-1b** | **注释与行为不一致**（P0-1 的伴生问题） | `historicalCase.ts:161` 注释写「生命周期分段（**原样**来自 Research 导出的 phases）」，但实际读的是 adapter 派生的 `c.phases` —— **并非原样来自 Research** | 会误导后续维护者以为该字段可信；修 P0-1 时须一并修正注释 |

**修的方向（不预设实现）**：当对象**没有 research lifecycle** 时，Product **不得**给出具体阶段，
必须显示「阶段未判定 / 资料不足」（并保留 `research_status` 的语义），
同时**不得**因此让已结束的 Campaign 被误判为「扩张中」。

### P1 — 1.0 前应该修（**1 项**）

| # | 问题 | 说明 |
|---|---|---|
| **P1-1** | **无正式部署方式 / 无访问入口 / 无回滚定义** | §2 方案已设计；需落地最小静态部署 + 重建流程文档化。**不引入后端** |

### P2 — 1.0 后处理（**不做**）

| # | 项 |
|---|---|
| P2-1 | `src/components/OpportunityRadar/` **未被 App 引用**（dead code）→ 清理或保留待 1.1 |
| P2-2 | Mobile 真机/浏览器实测复核（本轮为静态审计） |
| P2-3 | 视觉 / 动画 / 边距 / 图标等 |

---

## 9. 下一 Single Goal

> # **修复 P0-1：让「无 research lifecycle」的对象在 Product 中显示「阶段未判定」，而不是推导出的具体阶段。**

**范围（严格）**：
- 修改 Product 侧对「无 research lifecycle」对象的阶段推导路径（`historicalCaseOf` / `derivePhases` / `terminalPhaseOf` 回退）；
- **不修改**任何 Research artifact / schema / contract / SA rule / TO 标准；
- **不新增**字段或枚举（如需表达「未判定」，使用**既有** `UNKNOWN` / `NOT_AVAILABLE` 语义）；
- **不改变** Campaign / RC 数量、identity、SA 四维定义；
- 修完后**必须**同步把 `releaseGateScenarios.test.tsx` 的 `D3` 由 `it.fails` 改为正常断言。

**验收**：
```text
[ ] 无 research lifecycle 的对象在 Historical Case 中不出现具体阶段
[ ] 4 个 UNKNOWN-only RC 显示「阶段未判定 / 资料不足」
[ ] 已结束 Campaign 不被误判为「扩张中」（P0-2 的兜底可回退为数据驱动）
[ ] npm test 0 failed（D3 从 it.fails 转为正常通过）
[ ] tsc -b / vite build PASS
[ ] 5/5 workflow + 场景 A–E 全部通过
```

---

## 10. 1.0 宣布条件（Checklist）

**只有以下全部为 ✅，才可宣布 ThreeC 1.0：**

```text
[ ] Gate R  PASS（含 lifecycle 完整性定义 §1.1）
[ ] Gate P  PASS
[ ] Gate T  PASS（含 T8）—— 当前 FAIL（P0-1）
[ ] Gate Q  PASS
[ ] Gate U  PASS（场景 A–E 全部正常通过，无 it.fails）
[ ] Gate M  PASS（含真机复核）
[ ] Gate D  PASS（部署已落地 · 访问入口可用 · version=1.0.0 · tag v1.0.0 · 回滚已验证）
[ ] Gate G  PASS（四份文档与仓库一致）
[ ] P0 清单为空
[ ] P1 清单已处理或明确接受
```

**宣布动作**（顺序固定）：
1. P0 清零 → 2. P1 处理 → 3. `package.json` → `1.0.0` → 4. release commit →
5. `git tag v1.0.0` → 6. 部署 → 7. 验证访问入口 → 8. 更新 `PROJECT_STATE` / `ROADMAP` / `README`。

---

*THREEC_1_0_RELEASE_DEFINITION.md · 2026-09-24 · 审计基线 `ad5e804` · 永久锁定*
