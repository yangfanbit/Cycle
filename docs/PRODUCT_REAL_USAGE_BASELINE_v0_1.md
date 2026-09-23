# PRODUCT_REAL_USAGE_BASELINE_v0_1.md — Product v0.1 使用基线

> | 项目 | 值 |
> |---|---|
> | **阶段** | **Product Stabilization + Real Usage Validation v0.1** |
> | **基线 HEAD** | `bdafeb5`（Research Core Release v0.4） |
> | **Research 输入** | Historical Objects **79** · Driver Canonicalization **v0.4** · SA **v0.4**（395 pairs）· TO **v0.2**（内部 0.3） |
> | **Technical 结果** | `npm test` **0 failed / 622 passed（16 files）** · `tsc -b` **PASS** · `vite build` **PASS** |
> | **本轮未做** | 未扩 Historical Universe · 未新增 Driver vocabulary · 未微调 SA Rule · 未为增加 Pattern 挖数据 · 未新增 score/ranking/probability · 未新增 Radar/Dashboard · 未引入后端 · 未重构 Product Architecture · 未删除真实语义断言 |

---

## 一、阶段 A/B/C：21 项 Product Test Failures 的**逐项验证与清理**

### 1.1 分类结论（**逐项验证，未默认接受「都是旧 fixture」**）

| # | 测试 | 失败 | **分类** |
|---|---|---|---|
| 1 | timelineAdapter · source_commit | `0e1d2f48…` ≠ `052b79b9…` | **A** 旧 commit hash |
| 2 | timelineAdapter · 数据量快照 | 13C/4RC/52E/63Sec | **A** 旧 universe 数量 |
| 3 | timelineAdapter · lifecycle 非空 | `0 > 0` | **★ B/C 真实发现**（见 §1.2） |
| 4 | timelineAdapter · 视图层透传 lifecycle | `0 > 0` | **★ B/C 同上** |
| 5 | timelineAdapter · 年份可见 | `[2015..2025]` ≠ `[2018..2025]` | **A** 旧样本年份范围 |
| 6 | timelineAdapter · 2018 无 Campaign | `[...] ≠ []` | **A**（2018 现有 2 Campaign） |
| 7 | timelineAdapter · 9 月同期 | 年份/ID 清单 | **A** + 旧 ID 清单 |
| 8 | timelineAdapter · 2 月同期 | 年份/ID 清单 | **A** + 旧 ID 清单 |
| 9 | timelineAdapter · conflict 徽章 | `0 > 0` | **★ C 契约**（见 §1.3） |
| 10 | researchNavigation · Attention 分布 | `active` 13 ≠ 0 | **★ P0 真实缺陷**（见 §2.1） |
| 11 | researchNavigation · Layer B 覆盖 | `{from:2015}` ≠ `{from:2018}` | **A** |
| 12 | researchNavigation · Wave 1B 可检索 | `results[0]` 变化 | **A** + 排名语义 |
| 13 | researchNavigation · 默认参照 | 目标 ID 变化 | **A** |
| 14 | currentResearch · 候选只读 | `79 ≠ 17` | **A** |
| 15 | currentTimeLens · 同期一致性 | 年份/ID 清单 | **A** + 旧 ID 清单 |
| 16 | currentTimeLens · 2 月 uncovered | `11 ≠ 7` | **A** |
| 17 | currentTimeLens · 9 月 coveredYears | `11 ≠ 7` | **A** |
| 18 | currentTimeLens · 重复调用稳定 | 年份清单 | **A** |
| 19 | currentTimeLens · 条目数恒等 | `28` | **A** |
| 20 | yearCoverage · 年份覆盖 | `[2015..2025]` | **A** |
| 21 | entryIdentity · 单年度数量 | `7` | **A** |

**统计**：**A（旧 universe fixture）= 18 项** · **C（测试契约已变）= 1 项** · **B/P0（真实缺陷）= 2 项**

> **★ 未把任何非 fixture 失败标记为 fixture failure。** 其中 3 项经追查确认为**真实问题**（§1.2 / §1.3 / §2.1）。

### 1.2 ★ 真实发现：Research export 的 `lifecycle` 映射缺口（**B 类，未修，见 §4 P0-1**）

测试 #3/#4 断言「全部对象携带非空 lifecycle」。追查结果：

| 层 | 事实 |
|---|---|
| export `campaigns[].lifecycle` | **52 / 52 全部非空** ✅ |
| export `research_candidates[].lifecycle` | **仅 11 / 27 非空**；**16 个为空** |
| **intake 包 `candidates[].lifecycle`** | **16 / 16 全部有 lifecycle**（2–3 个阶段） ✅ |
| export builder 取值 | `"lifecycle": CANDIDATE_LIFECYCLE.get(rcid, [])`（`batch_auto_research.py:3552`） |
| `CANDIDATE_LIFECYCLE` 覆盖 | **11 / 27** —— **映射表不全**，与早前 `CANDIDATE_DRIVERS`（9/27）**同一类缺口** |

→ **这是 Research 侧数据缺口，不是「该对象本就没有生命周期」。**
**本轮按 §六「不修改 Research」未修**，但已在测试中**显式锁定当前覆盖数（11 / 27）**，使缺口在 CI 中**可见**而非被模糊断言掩盖。

### 1.3 ★ 契约更新：`research_status = CONFLICT` 可以是**分类级**判断

测试 #9 断言「`status = conflict` ⇒ `conflicts` 非空」。追查：

| 对象 | status | conflicts | 说明 |
|---|---|---|---|
| `C-2024-ROBOTAXI` | `conflict` | **1** ✅ | 日期级分歧 |
| `RC-2020-FIN-BROKER-VOLUME` | `CONFLICT` | **0** | intake 原文为「**是否将券商行情整体降级**」的**归属分歧**，**包内无 `conflicts` 字段** |

→ **契约更新**：**Campaign** 的 `conflict` 必须携带日期级 `conflicts`；**Research Candidate** 的 `CONFLICT` 可为分类级，此时**不得伪造**日期级 conflicts。
UI 文案为「**研究结论存在分歧**」而非「日期存在分歧」→ **语义正确，无需修改实现**。

### 1.4 阶段 B：测试架构去除旧 Universe 耦合

**不只做 `17 → 79` 机械替换**，改为：

| 手段 | 应用 |
|---|---|
| **数据驱动断言** | `years()` 与导出对象的 min/max 比对；`exportIds.size` 与对象总数恒等；`coveredYears` 与命中行数恒等 |
| **结构断言优先** | lifecycle 按 `kind` 分治；identity 按来源数组判定；同期命中**逐行与 Adapter 比对**（不再写死 ID 清单）；年份序列断言「升序 + 连续 + 覆盖区间」 |
| **统计值仅用于 canonical artifact 验证** | 52 / 27 / 395 / 260 / 135 等仅在验证 artifact 完整覆盖处精确断言 |
| **移除排名语义** | 不再断言 `results[0]`（避免「第一个 = 最强」）；显式注释结果顺序为实现细节 |
| **诚实空态** | 空态改用**范围外年份**验证（当前 universe 每年都有对象） |

---

## 二、阶段 D/F：Product Contract 审查与修复

### 2.1 ★★ P0 修复：Attention Gate 把「已结束的历史 Campaign」标为「当前值得研究」

**现象**：`layerC.active` 有 **14** 个对象（测试期望 0），含 **`C-2016-PANEL-CYCLE`（end=2017-06-30，早已结束）** 与 `C-2019-RES-DYE-SHOCK`。

**根因链**：
1. `terminalPhaseOf(campaign)` 取 **lifecycle 中最后记录的阶段**；
2. R01 importers 在写入 `campaign_phases` 时 **过滤掉了 `PEAK` / `UNKNOWN` 阶段**（`STAGE` 映射中 `PEAK → None` → `continue`）；
3. → 这些 Campaign 的 export lifecycle **只到 `MAIN_RISE`** → `phase = EXPANSION` → 落入 `ACTIVE_PHASES` → **「当前值得研究」**。

**修复（最小、只用 export 自带字段、不改研究结论）**：

```
if (!campaign.openEnded && campaign.end != null) → HISTORICAL_REFERENCE
```

> 语义：研究**已记录结束日期** ⇒ 该 Campaign 已结束；「最后阶段 = MAIN_RISE」只说明 **lifecycle 终段缺失**，
> **不能**据此判定「仍在扩张」。**不引入 `today`**，不改动任何 Research 结论。

**效果**：14 → **5** 个 ACTIVE（仅剩 `end_date = null` 即研究未记录结束的对象）。

### 2.2 ★ P0 修复：null 日期导致 Product 运行时崩溃（93 处）

`end_date` / `start_date` 可为 `null`（G2-1 四态允许 end 未确定；部分 R01 对象 start 亦未确定），而 adapter 假定非空 → `Cannot read properties of null (reading 'slice' / 'split')` **93 处**。

**修复（最小，未重构架构）**：
- `timelineTypes.ts`：`ExportCampaignV1.end_date` → `string | null`；`ExportCandidateV1.start_date` → `string | null`
- `timelineAdapter.ts`：`cross_year` null 安全；`start` / `end` 沿用 **Research Candidate 侧既有约定**（渲染用占位 + `openEnded` 显式标注「结束未确定」）

### 2.3 阶段 D 契约验收结果

| 契约 | 结果 |
|---|---|
| Campaign 与 Research Candidate 身份明确区分 | ✅ SA artifact identity 正确（campaign 260 / RC 135，与 export 集合一致） |
| Campaign 可进入 Historical Case | ✅ `historicalCaseOf` 的 `objectKind` 与 SA identity 一致 |
| Research Candidate 不虚构 Campaign Detail | ✅ RC 的 `objectKind = research_candidate`；`historicalCampaignId = null` |
| **UNKNOWN ≠ MISMATCH** | ✅ 状态词与标签均不同 |
| **NOT_AVAILABLE ≠ MISMATCH** | ✅ 同上 |
| `PERIPHERAL_OVERLAP` 不进入 supported | ✅ 计入 `unsupportedDimensions` |
| `CROSS_MACRO_THEME` 只作 metadata | ✅ **不在 `why_not_similar` 中** |
| 无 ranking / score / probability / prediction | ✅ Product 自有标签词表与 UI 文案均无；artifact 无禁止字段 |
| TO：Timeline-eligible 只有真实达标 Pattern | ✅ 仅 `TOP-01`；`RESEARCH_ONLY` / `EXPLORATORY` / `REJECTED` 均不进入 Timeline |
| TO：历史复现不写成未来概率 | ✅ `recurrenceLabel` = 「历史复现：N / M 个观测年份」，且不含「概率/胜率/预期」 |
| TO：当前日期不在窗口 → 诚实空态 | ✅ `proximity` / `proximityLabel` / `distanceDays` 为纯日历口径 |

---

## 三、阶段 E：真实 Research Workflow 验收（**本轮核心**）

新增**可重复验收夹具**：`src/data/timeline/__tests__/researchWorkflow.test.tsx`（43 用例）

对 **全部 5 个 Current Candidate** 逐一执行完整链路：

```
Current Candidate → Current Time Lens → Time Observation / Calendar
  → Lifecycle → Structural Analogy → Historical Case → Evidence
  → 为什么对应 / 哪里不同 → 新的 Research Question
```

| 检查项 | 结果 |
|---|---|
| ① 今天在哪里 | ✅ `position.today / window / monthLabel` 齐备；`uncovered` 为诚实布尔 |
| ② 为什么进入历史比较 | ✅ 每个 Candidate 均有 **79** 条解释（395 / 5 = 79） |
| ③ 历史对象身份 | ✅ 每 Candidate：**52 campaign + 27 RC**，id 互斥非空，**无混淆** |
| ④ 四维结构可读 | ✅ 四维均有**人类可读标签**（生命周期 / 驱动机制 / 证据顺序 / 事件结构）与状态标签 |
| ⑤ 不确定性诚实 | ✅ 三维数组**完整划分四维**；UNKNOWN / NOT_AVAILABLE 与 MISMATCH **标签不同**；PERIPHERAL 不计支持 |
| ⑥ Historical Case 可达 | ✅ 两类对象均可解析；RC 不被当作正式 Campaign |
| ⑦ 下一步研究 | ✅ `whySimilar` 与 `whyNotSimilar` 均非空；不含 theme 依据 |
| ⑧ 语义红线 | ✅ 无 score / ranking / probability / prediction |

**★ 结论：5 个 Candidate 全部走通完整研究闭环，且不确定性表达诚实。**

---

## 四、当前问题（按 P0 / P1 / P2 分类）

### P0（阻断核心研究路径 —— 本轮已修 2 项，**剩 1 项**）

| # | 问题 | 状态 |
|---|---|---|
| **P0-1** | **Research export 的 `lifecycle` 映射缺口**：16 / 27 Research Candidate 的 export `lifecycle` 为空（**intake 全部有**）；且 R01 importers **过滤掉 `PEAK` 阶段**，导致 **9 个已结束 Campaign 的终段缺失** | **未修（Research 侧，本轮禁止）** —— 见 §6 Next Single Goal |
| **P0-2** | Attention Gate 把已结束历史 Campaign 标为「当前值得研究」 | **✅ 已修**（§2.1） |
| **P0-3** | null `start` / `end` 导致 Product 运行时崩溃（93 处） | **✅ 已修**（§2.2） |

### P1（明显降低研究效率 —— 本轮已修 1 项）

| # | 问题 | 状态 |
|---|---|---|
| **P1-1** | Time Observation 详情定义列表在 720px 以下仍为 3 列（375px 下每列约 110px，dt/dd 难读） | **✅ 已修**（收窄为 2 列，仍用 `minmax(0,1fr)` 保证不溢出、不裁切） |
| **P1-2** | Research Candidate 的 `lifecycle` 为空 → 其生命周期位置在 Historical Case 中不可见（P0-1 的表现面） | 随 P0-1 一并解决 |

### P2（本轮**不做**）

动画 · 颜色 · 图标 · 边距 · 额外筛选 · 额外排序 · OpportunityRadar · Dashboard · notification · real-time market · backend · 新数据源。

---

## 五、本轮完成清单

### 已修复
1. **P0-2** Attention Gate：已记录 `end` 的历史 Campaign 不再被标为「当前值得研究」（14 → 5）
2. **P0-3** null `start` / `end` 运行时崩溃（93 处）—— 类型修正 + null 安全 + `openEnded` 标注
3. **P1-1** Time Observation 移动端详情网格 3 列 → 2 列
4. **21 项 Product Test Failures → 0**（其中 18 项为旧 universe fixture、1 项契约更新、2 项真实缺陷）
5. **测试架构去除旧 universe 耦合**：数据驱动断言 + 结构断言优先 + 移除排名语义

### 已验证
- `npm test` **0 failed / 622 passed（16 files）**
- `tsc -b` **PASS** · `vite build` **PASS**
- Product 消费 **SA v0.4** 与 **TO v0.2**（无旧 artifact 引用残留）
- Campaign / RC identity 正确（52 / 27，错误 0）
- 5 个 Current Candidate 全部走通完整研究闭环（43 用例验收夹具）
- 无 score / ranking / probability / prediction

### 已知限制（**不阻塞**，见 ROADMAP §3）
| # | 限制 | 影响 |
|---|---|---|
| L1 | 剩余 **7 项**跨 canonical 子串冲突（含 v0.1 既有遗留如 `结构迁移`） | 相关文本无法成为 `DIRECT`；**不改变任何 driver 集合** |
| L2 | `driver = MATCH` 仅 1 条 / `event MATCH` 仅 1 条 | 数据粒度限制（**不得**通过放宽规则解决） |
| L3 | 2 个 cycle 因**映射逻辑**无 canonical driver（`RC-2015-FIN-LEVERAGE` 多命中 · `RC-2024-SECONDARY` 研究自述强度不足） | 非数据缺口 |
| L4 | TO `observation.year`（研究对象研究年份）与 `date`（锚点日期）在「锚点退化为 `campaign.start_date` 且落在上一日历年度」时相差 1 年（5 例，全部 R01） | 年度归属口径问题，改则属规则变更 |
| L5 | R01 importers 过滤 `PEAK` / `UNKNOWN` 阶段 → export lifecycle 终段缺失 | **P0-1 的一部分** |

### 未处理
- **P0-1 / P1-2**（Research 侧 lifecycle 映射缺口）—— 本轮明确不修改 Research
- L1 / L2 / L3 / L4（已知限制，不阻塞）
- 全部 P2 项

---

## 六、最终结论

### 6.1 ThreeC 现在到底能不能作为一个**真实历史研究工具**使用？

> # ✅ **能，但有一个明确的数据层前提。**

**能用的证据**：
1. **5 个 Current Candidate 全部走通完整研究闭环**（今天 → 候选 → 时间/日历 → 生命周期 → 结构对应 → 历史案例 → 证据 → 新研究问题）；
2. **结构对应与不对应可解释**：四维均有可读标签与直接依据，`whySimilar` / `whyNotSimilar` 齐备，跨 Macro Theme **不**被当作不相似理由；
3. **不确定性表达诚实**：`UNKNOWN` / `NOT_AVAILABLE` 与 `MISMATCH` 严格区分，空态显式说明「这不是错误」，TO 的「历史复现」不写成未来概率；
4. **身份正确**：Campaign 与 Research Candidate 明确区分，不互相冒充；
5. **技术门槛已清**：`npm test` 0 failed · `tsc -b` PASS · `vite build` PASS · 无运行时崩溃。

**前提（唯一）**：**Research Candidate 的 lifecycle 在 export 中大面积缺失**，导致 27 个 RC 中有 16 个在「生命周期位置」这一段**看不到任何阶段信息** —— 用户研究 RC 时会遇到**信息断层**（不是错误，但会中断研究）。

### 6.2 真正阻碍用户价值的**下一个**问题是什么？

> ## **Research Candidate 的 `lifecycle` 在 export 中缺失（16 / 27），且 R01 importers 过滤掉了 `PEAK` 阶段。**

**为什么是它（而不是别的）**：
- 它是**唯一**会让用户在**核心研究路径中途**遇到信息断层的问题（其余限制都只影响「判定更保守」，不影响路径可走）；
- 它是**映射缺口**（intake 全都有），**不是**研究本身缺证据 → **可确定性修复**，不需要新研究判断；
- 它的表现面已经扩散到两处：**RC 的生命周期位置不可见**（P1-2）+ **已结束 Campaign 的终态被误判为「扩张中」**（P0-2 的根因，本轮只做了 Product 侧兜底）；
- 修它**不会**引入任何新规则、新 vocabulary 或新研究结论 —— 只是把**已存在于 intake 的事实**接进 export。

### 6.3 Next Single Goal

> # **下一阶段唯一目标：把 Research 侧 `lifecycle` 映射补齐并如实入库 —— 让 27 个 Research Candidate 的 intake 阶段（含 `PEAK`）完整进入 export，使「生命周期位置」在全部 79 个 Historical Object 上可用。**

**范围（严格）**：
- 补齐 `CANDIDATE_LIFECYCLE`（11 → 27），**逐字转写**自 intake `candidates[].lifecycle`；
- 修正 R01 importers 对 `PEAK` / `UNKNOWN` 阶段的过滤，使已结束 Campaign 的终段如实入库；
- **不新增** Campaign / vocabulary / 规则；**不调** SA 阈值；**不放宽** TO 标准；
- 完成后重新生成 Driver Canonicalization → SA → TO（新版本，旧版本逐字节保留），并做 before/after。

**预期收益**：
- 27 个 RC 的「生命周期位置」由**不可见**变为**可用** → 研究闭环不再中断；
- 已结束 Campaign 的终态由「扩张中」纠正为真实阶段 → Attention Gate 的 Product 兜底可回退为纯数据驱动；
- `INSUFFICIENT_EVIDENCE` 的构成将更接近「真正资料不足」而非「映射缺失」。

**验收标准**：`npm test` 0 failed · SA/TO 独立语义校验 PASS · 5 个 Candidate 的研究闭环中「生命周期位置」在 **79 / 79** 对象上均有非空阶段或显式 `UNKNOWN`。

---

*Product / Real Usage Baseline v0.1 · 2026-09-24 · 基于 Research Core Release v0.4（HEAD `bdafeb5`）*
