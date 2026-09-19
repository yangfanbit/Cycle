# R01-02 Intake Review v0.1 — 半导体 / 电子

> **性质**：ThreeC Agent 对 `research/intake/packages/R01-02/` 的 **Intake 层**审查记录。
> **本轮范围**：只做 Intake Review。**未创建任何 Canonical Campaign · 未 Promotion · 未导入 DB ·
> 未刷新 Structural Analogy / Time Observation · 未启动 R01-03 · 未修改 taxonomy。**
> **Worker 报告的 Conflict 一条未消解**；Campaign 的合并 / 拆分**未提前决定**。

---

## 0. 结论摘要

| 项 | 结果 |
|---|---|
| **A. Package 是否通过 Intake** | ✅ **通过** |
| 现有 Intake Validator（C01–C24） | PASS（0 FAIL / 0 WARN） |
| **严格 Draft-07 JSON Schema** | **0 错误** |
| checksums.sha256（10 条） | 全部一致 ✓（README.md 未纳入 checksum） |
| **B. 必须修复的问题** | **无**（Package 侧） |
| **C. Validator / Protocol 层问题** | **3 项，均为 Validator 缺陷**（见 §4） |
| **G. 是否建议进入 DB Import** | ✅ **建议**（在完成 §5 的 Canonical 决策后） |

---

## 1. Package 验收

### 1.1 文件与规模

```
R01-02/  README.md · manifest.json · coverage.md · candidates.json · evidence.json
         sources.json · securities.json · exclusions.json · conflicts.json
         research_questions.json · quality_summary.json · checksums.sha256
```

| 项 | 数量 |
|---|---:|
| Candidates | **12** |
| Evidence | **56** |
| Sources | **40** |
| Securities | **19** |
| Exclusions | **14** |
| Conflicts | **10** |
| Research Questions | **8** |
| Macro Theme Proposals | **6** |
| Cross-task Notes | **6** |

`manifest`：
- `intake_protocol_version = 0.1` · `research_round_id = R01` · `task_id = R01-02`
- `source_commit = 2153f6d83b7481300696ab73d792e9e53aa31a07`
- `years 2015–2025`，Priority A `2018–2025` / Priority B `2015–2017`

### 1.2 checksum 核对

10 条 checksum **全部一致**，引用文件全部存在。
`README.md` 未纳入 checksum —— 与 R01-01 **同一惯例**（R01-01 的 README 亦未纳入），**非 R01-02 个案问题**，记为提示项。

### 1.3 现有 Intake Validator

```
validate_historical_research_intake.py research/intake/packages/R01-02
  → checks: 24   FAIL: 0   WARN: 0   RESULT: PASS
--check → PASS（packages found: 2）
```

---

## 2. 严格 JSON Schema 校验（本轮新增）

**方法**：`jsonschema` 4.26.0 · `Draft7Validator` · 按 Validator 的装配规则
（`manifest.json` + 8 个数组文件）组装完整 Package 对象后校验。

| Package | Draft-07 严格错误数 | 说明 |
|---|---:|---|
| **R01-02** | **0** | ✅ 完全符合当前 Schema |
| R01-01（对照） | **1** | `conflicts/4`：`Additional properties are not allowed ('_position_note' was unexpected)` |

> ★ **R01-02 是本轮唯一通过严格 Schema 的包。R01-01 的既有违例记录在 §4.3。**

---

## 3. 结构与引用关系

### 3.1 引用完整性

| 检查 | 结果 |
|---|---|
| candidate → evidence 引用 | 悬空 **0** ✓ |
| candidate → security 引用 | 悬空 **0** ✓ |
| evidence → source 引用 | 悬空 **0** ✓ |
| **定义但未被引用** | source **1** 个（`R01-SEMICONDUCTOR-S006`）；evidence / security **0** ✓ |

`S006` 未被引用 —— **不阻塞**（Schema 不要求反向引用；R01-01 亦有 2 个未引用 source）。
建议 Canonical 化时补齐或删除。

### 3.2 Research Model v1.0 §5 证据门槛

**12 / 12 候选全部满足「≥2 Evidence 且 ≥2 independence_group」** ✓

| candidate | y | status | conf | classification | ev | IG | PIT | sec |
|---|---:|---|---|---|---:|---:|---:|---:|
| `001` 自主可控（实体清单） | 2019 | PROVISIONAL | high | theme_campaign | 10 | 6 | 10 | 8 |
| `002` 设备材料国产替代 | 2020 | PROVISIONAL | medium | theme_campaign | 7 | 6 | 5 | 4 |
| `003` 面板 LCD 上行（2020–22） | 2020 | PROVISIONAL | high | industry_trend | 5 | 4 | 4 | 2 |
| `004` 缺芯 / 全链涨价 | 2020 | PROVISIONAL | medium | industry_trend | 4 | 3 | 3 | 3 |
| `005` TWS / 可穿戴 | 2019 | PROVISIONAL | high | theme_campaign | 5 | 4 | 5 | 3 |
| `006` AI 算力 | 2023 | PROVISIONAL | medium | theme_campaign | 4 | 3 | 4 | 3 |
| `007` 存储超级周期 | 2024 | PROVISIONAL | medium | theme_campaign | 6 | 5 | 5 | 4 |
| `008` 大基金三期 / 自主可控 | 2024 | PROVISIONAL | **low** | mixed | 6 | 5 | 2 | 4 |
| `009` 2022 下行 / 去库存 | 2022 | PROVISIONAL | medium | industry_trend | 4 | **2** | 4 | 3 |
| `010` 2015 杠杆牛 | 2015 | **INSUFFICIENT** | low | unclear | 2 | 2 | 2 | **0** |
| `011` 面板（2016–17） | 2016 | PROVISIONAL | medium | industry_trend | 3 | 2 | 1 | 1 |
| `012` 2017 显卡 / 矿机 | 2017 | **INSUFFICIENT** | low | unclear | 2 | 2 | 1 | **0** |

★ `009` / `011` 的 IG 恰为 2（门槛边界）；`010` / `012` 无 securities（`security_ids = []`，Schema 允许）。

### 3.3 为后续 Canonical 化的预判（提示，不决定）

- **被多候选共享的 evidence：2 条** —— `E035`（007 / 008）· `E056`（002 / 008）。
  `validate_batch_research` 强制 **1 evidence : 1 campaign**，Canonical 化时须指定唯一归属
  （R01-01 已按同一规则处理过 E009 / E016）。
- **security 可共享**（桥表允许），11 个标的被多候选共享，无需消歧。
- `securities[].ticker` 格式为 `688981.SH`（带交易所后缀），而既有 DB 惯例为裸代码 `600031`。
  Schema 允许（无 pattern），但 Canonical 化时须做格式映射。

---

## 4. Worker 报告的 Protocol / Validator 问题 —— 定性

### 4.1 实证方法

在 **R01-02 的临时副本**（未触碰正式 Package）注入 5 个人为缺陷，对比两种校验的检出率：

| # | 注入缺陷 | Schema 约束 | C01–C24 | 严格 Draft-07 |
|---|---|---|:---:|:---:|
| M1 | 候选增加额外属性 `_extra_note` | `additionalProperties: false` | ❌ 漏 | ✅ 检出 |
| M2 | `confidence = "very-high"` | `enum` | ✅ C11 | ✅ 检出 |
| M3 | `year = "2020"`（字符串） | `type: integer` | ❌ 漏 | ✅ 检出 |
| M4 | `candidate_id = "C-2020-SEMI"` | `pattern` | ✅ C13 | ✅ 检出 |
| M5 | `temporal_relation = "whenever"` | `enum` | ✅ C19 | ✅ 检出 |
| | **检出数** | | **3 / 5** | **5 / 5** |

### 4.2 三项指控的定性结论

| Worker 指控 | 判定 | 依据 |
|---|---|---|
| **① C01–C24 不等同于完整 JSON-Schema 校验** | ✅ **成立 → Validator 缺陷** | 实证漏检 M1 / M3（2/5）。Validator 仅用 Schema 读取 `definitions` 的 enum 与顶层 `required`，**不做真实 schema validation**（代码中无 `jsonschema` / `Draft7` 引用） |
| **② 未检查「定义但未被引用」的对象** | ✅ **成立 → Validator 缺陷**（非 Schema 要求） | 代码中无 unreferenced / orphan 检查。R01-02 有 1 个未引用 source；R01-01 有 2 个。**不影响 Package 合法性** —— Schema 不要求反向引用 |
| **③ `additionalProperties` 等 Schema 约束是否实际执行** | ✅ **不执行 → Validator 缺陷** | `c14` 仅扫描硬编码的 `FORBIDDEN_KEYS` 集合，**不解析 `additionalProperties`**。`_extra_note` 之类的未知键一律放行 |

> **三者均属 Validator 缺陷，不是 Package 个案问题，也不是 Schema / Protocol 问题。**
> Schema 本身**没有问题** —— 一旦真正执行 Draft-07，全部约束均正确生效（5/5 检出）。
> **Protocol 亦无需修改**：协议 §5.3 已把 Schema 定为「唯一事实来源」，只是执行层未落实。

### 4.3 ★ Validator 缺陷的**实际影响实例：R01-01（已导入）**

```
conflicts/4  (R01-HIEQ-CF005)
  Additional properties are not allowed ('_position_note' was unexpected)
  _position_note = "本条的第二 position 来自本包内部核对（非外部来源），故 source_ids 仅列产业链映射来源 S020。"
```

这是**真实存在的违例**：R01-01 的 `CF005` 多了一个 `_position_note` 键，
C01–C24 **当时未检出**（R01-01 曾以 0 FAIL 通过并已导入）。
→ 证明该 Validator 缺陷**已经放过过一次真实数据**，不是纯理论问题。

**处置**：本轮**只记录**，不回滚、不修改 R01-01（超出本轮范围；且该键为说明性内容、无语义危害）。
建议在独立的 Validator 修复任务中一并评估是否需要清理 R01-01 的该键。

---

## 5. 12 个 Candidates 与 10 个 Conflicts 的重点审阅

> 只做**完整性 / 一致性 / 可追溯性 / 冲突识别**与**是否具备进入 Canonicalization 的条件**判断。
> **不消解任何 Conflict，不决定合并 / 拆分。**

### 5.1 ①2019–2021 半导体长周期 vs 多个 Campaign

- 载体：`CF001`（KEEP_BOTH，含 3 个 position）· `CF010`（3 个峰值口径）· `Q001`
- Worker 做法：建 `001`（2019 设计/制造）与 `002`（2020–21 设备材料），互相标注
  `possible_duplicate_of`；三个峰值口径（2020-02 底 / 2020-07-14 / 2021-07-30）**全部写入**
  `001.peak.alternative_dates`。
- **可追溯性**：✅ 三段区间、各段独立催化、三个峰值口径与来源均有据。
- **是否具备进入条件**：✅ **具备**。信息充分，待 Canonical 走 Independence Gate Q1–Q5 判定。

### 5.2 ②国产替代的阶段边界

- 载体：`CF002`（KEEP_BOTH）· `Q002`
- 争议：2019–20「首次被封锁」vs 2024–25「大基金三期 + 出口管制升级」，中间 2022-01—2024-01
  近两年独立下行期。
- **可追溯性**：✅ 两个方向的 position 与中间下行期均有证据与时间锚点。
- **是否具备进入条件**：✅ **具备**（001 / 002 / 008 三者信息均充分），
  但 **008 附带 Beta 与重叠问题**（见 §5.4）。

### 5.3 ③半导体 / 电子 / 面板 taxonomy 边界

- 载体：`CF003`（UNRESOLVED，半导体 vs 电子）· `CF004`（KEEP_BOTH，面板是否拆分）· `Q003`
- Worker **未自行裁决** —— 同时提交 `半导体` / `电子` / `面板/显示` 三个 proposal 交 CMTR v1。
- `X009` / `X010` 明确排除「算力升格为 Macro Theme」与「Worker 侧裁决合并」。
- **合规**：✅ 完全符合协议（Worker 不得发明第二套 resolution）。
- **CMTR v1 实际结果**：见 §6 —— **三个 proposal 均解析至 `电子`**，无需本轮扩展 taxonomy。

### 5.4 ④2024-09-24 后市场 Beta 污染

- 载体：`CF006`（KEEP_BOTH，2 个 position）· `Q005`
- Worker 处理：按 `historical_campaign_validation_v1.md §4.3`
  「无法排除 Beta Contamination 时保持限定」→ `008` 降为 `low`，`007` 保持 `medium`
  并**单列基本面驱动（存储价格数据）**。
- **可追溯性**：✅ 两个 position（跑赢 vs 全市场普涨）与来源均有据；`007` 额外给出相对独立的
  基本面锚点（江波龙市值/涨幅、存储价格）。
- **是否具备进入条件**：⚠️ **007 具备（附条件）** —— 须在 Canonical Decision 中裁决 `CF006`；
  **008 见 §5.5**。

### 5.5 ⑤2024–2025 候选（007 / 008）证据是否足以进入 Canonical Campaign

| | 007 存储超级周期 | 008 大基金三期 / 自主可控 |
|---|---|---|
| confidence | medium | **low** |
| evidence / IG | 6 / 5 | 6 / 5 |
| PIT 证据 | 5 | **2** |
| 与另一方关系 | 与 008 市场区间**高度重叠** | 与 007 高度重叠；`end` 为 PHASE「并入存储与 AI 主线，无独立结束点」 |
| Worker 自述 | 「能否与 924 政策行情切分开是**最大不确定项**」 | 「无法排除 Beta Contamination… 独立性存疑」 |

**Intake 结论（不决定）**：
- **007** —— 信息**充分但附条件**：有独立基本面锚点，但 `CF006` 未裁决。
  可进入 Canonicalization，**须把 `CF006` 一并提交 Canonical Decision**。
- **008** —— 信息**充分但置信度最低**（low）+ 与 007 重叠 + 无独立结束点。
  建议**保留 RESEARCH_ONLY**，或作为 007 的候选合并对象 —— **由 Canonical Decision 判定，本轮不裁决**。

### 5.6 ⑥INSUFFICIENT 候选（010 / 012）是否应继续保留 Research Only

| | 010（2015 杠杆牛） | 012（2017 显卡/矿机） |
|---|---|---|
| evidence / IG | 2 / 2（门槛边界） | 2 / 2（门槛边界） |
| securities | **0** | **0** |
| classification | `unclear` | `unclear` |
| Worker 自述 | 无法排除 Beta（2015 全面杠杆牛）；缺半导体自身基本面证据 | 主题归属存疑（半导体 vs 数字货币）；缺行业数据支撑 |
| 缺口根因 | Priority B 资料不足（quality_summary.known_gaps 第 2 项） | 同左 + `CF008` 归属争议 |

**Intake 结论**：✅ **两者均应继续保留为 RESEARCH_ONLY / INSUFFICIENT**。
证据恰在门槛、无代表标的、Beta 无法排除、归属争议未决 —— **不具备进入 Canonical Campaign 的条件**。
（与 R01-01 的 006 / 007 处置一致。）

### 5.7 其余候选

- **009（2022 下行）** —— 附 `CF009`（KEEP_BOTH）与 `Q007`：
  「纯下行周期是否应进入 canonical campaigns 表」属**方法论层面问题**，
  Worker 已明确标注它不是机会型结构（与 R01-01 的 `C-2018-HIEQ-ROBOT-DOWN` 同类）。
  IG = 2（门槛边界）。**可进入，但须裁决 `CF009`**。
- **011（2016–17 面板）** —— Priority B，`3 ev / 2 IG`，峰值只能定位到半年窗口。
  **证据薄但合规**；可进入但应在 Canonical 评估日期精度。
- **003 / 004 / 005 / 006** —— 证据充分（4–5 ev / 3–4 IG），
  附 `CF004` / `CF005` / `Q004` 等分类与归属争议，均具可追溯性。

---

## 6. CMTR v1 检查（**本轮未修改 taxonomy**）

**唯一实现**：`research/scripts/theme_taxonomy.py`（`canonical-macro-theme-resolution-1`）
现有根节点（**11**，T01 补齐后）：信息通信 · 医药健康 · 国防军工 · 房地产 · 汽车 · 消费 ·
电力设备 · **电子** · 资源 · 金融 · 高端装备

### 6.1 Macro Theme Proposals

| proposal | 名称 | kind | CMTR status | root |
|---|---|---|---|---|
| `MT001` | 半导体 | NEW_MACRO_CANDIDATE | **RESOLVED** | 电子 |
| `MT002` | 电子 | NEW_MACRO_CANDIDATE | **RESOLVED** | 电子 |
| `MT003` | 面板/显示 | CROSS_FAMILY | **RESOLVED** | 电子 |
| `MT004` | 半导体设备材料 | SUB_THEME | **RESOLVED** | 电子 |
| `MT005` | 算力 | MECHANISM | **UNRESOLVED_NAME** | — ✅ **正确**（机制，非主题；`X009` 已排除） |
| `MT006` | 国产替代 | MECHANISM | **UNRESOLVED_NAME** | — ✅ **正确**（机制，非主题） |

> ★ `MT005` / `MT006` 虽 `UNRESOLVED_NAME`，但其 `proposal_kind = MECHANISM` ——
> **这正是协议期望的结果**（「算力」「国产替代」是 Mechanism，不是 Macro Theme）。
> **不构成 taxonomy gap。**

### 6.2 候选级解析

**12 / 12 候选全部 `RESOLVED`，root = `电子`** ✓
（匹配名：`半导体` · `半导体设备` · `半导体材料` · `电子` · `面板/显示`）

### 6.3 记录的别名缺口（**非阻塞，只记录，本轮不扩展**）

下列名称在 taxonomy 中无对应行，但每个候选至少有 1 个名称命中，故**不阻塞解析**：

```
芯片 · 集成电路 · 半导体产业 · 面板 · 显示器件 · 存储 · 存储芯片 · DRAM · HBM · GPU
消费电子 · 苹果产业链 · TWS耳机 · 缺芯 · 半导体涨价 · 汽车芯片
自主可控 · 国产替代 · 算力 · AI算力 · 算力芯片 · 半导体库存周期 · 半导体产业周期
```

> **判定：无阻塞性 taxonomy gap。R01-02 可正常进入 Canonicalization。**
> 若后续希望这些别名可直接解析（而非依赖同级名称命中），须另起 taxonomy 轮次 —— **本轮不做**。

---

## 7. Intake 层面五项检查

| 检查 | 结果 |
|---|---|
| **完整性** | ✅ Protocol §5.3 的 12 个文件齐备；manifest 16 个顶层字段齐备；各候选 `drivers` 四问、`why_campaign` / `why_not`、`point_in_time_notes`、`lifecycle` 均填充 |
| **一致性** | ✅ `quality_summary.counts` 与 `confidence_distribution` 与实际一致（C21 通过）；`confidence` 分布 3 high / 6 medium / 3 low 与 12 候选一致；分类枚举全部合法 |
| **可追溯性** | ✅ evidence → source 全链可达；`event_date` 与 `evidence_date` 分列；`subsequent` / `retrospective` 均带 `point_in_time_note`；指数与个股价格锚点来自行情来源，政策锚点优先一手文件（如 `S001` Federal Register 原文） |
| **冲突识别** | ✅ 10 条冲突，**9 条 KEEP_BOTH + 1 条 UNRESOLVED（CF003）**，全部保留双方，**未自动取舍**；`CF010` 保留 3 个峰值口径 |
| **进入 Canonicalization 的条件** | ✅ **具备**（见 §8 D / E） |

**独立性纪律**：`independence_group` 按来源机构分组；同一来源多条证据标记 `same_origin` /
`retelling`，不重复计为独立证据；不以个股涨幅反推主题（卓胜微 +892% 等仅作个股事实记录）。

---

## 8. Review 结论（A–G）

### A. Package 是否通过 Intake

> ## ✅ **通过**

C01–C24 PASS（0/0）· **严格 Draft-07 Schema 0 错误** · checksum 全部一致。

### B. 是否存在必须修复的问题

> ## ❌ **Package 侧无必须修复项**

非阻塞提示项 2 个：
1. `R01-SEMICONDUCTOR-S006` 定义但未被引用（建议补齐或删除）
2. `README.md` 未纳入 checksum（与 R01-01 同一惯例）

### C. 哪些问题属于 Validator / Protocol 层问题

| 问题 | 归属 | 是否阻塞 R01-02 |
|---|---|:---:|
| C01–C24 不等同完整 Schema 校验（实证漏检 2/5） | **Validator 缺陷** | ❌ 不阻塞（R01-02 严格 Schema 0 错误） |
| 未检查「定义但未被引用」 | **Validator 缺陷** | ❌ 不阻塞（Schema 不要求） |
| `additionalProperties` 未执行 | **Validator 缺陷** | ❌ 不阻塞（R01-02 无额外属性） |
| Schema 本身 | **无问题** | — |
| Protocol 本身 | **无需修改** | — |

> ⚠️ **但是**：该 Validator 缺陷已放过 R01-01 的 1 个真实违例（`CF005._position_note`，见 §4.3），
> 因此**值得作为独立工程任务处理**（见 §9）。

### D. 哪些 Candidates 可以进入下一步 Canonicalization

| 组 | candidate | 备注 |
|---|---|---|
| **证据充分、信息齐备** | `001` `002` `003` `004` `005` `006` | 直接进入 Canonical Decision |
| **证据充分但附带高优先级 Conflict** | `007`（附 `CF006` Beta）· `009`（附 `CF009` 下行是否入库） | **须把 Conflict 一并提交 Canonical Decision** |
| **证据薄但合规** | `011`（3 ev / 2 IG，日期精度半年窗口） | 可进入，但须评估日期精度 |

### E. 哪些 Candidates 应保留 Research Only / Insufficient

| candidate | 结论 | 理由 |
|---|---|---|
| `010`（2015 杠杆牛） | **RESEARCH_ONLY** | 证据 2/2 恰在门槛、**0 个 securities**、Beta 无法排除、Priority B 资料不足 |
| `012`（2017 显卡/矿机） | **RESEARCH_ONLY** | 同上 + `CF008` 归属争议（半导体 vs 数字货币） |
| `008`（大基金三期） | **建议 RESEARCH_ONLY**（或作为 007 合并候选） | confidence **low**、与 007 市场区间高度重叠、无独立结束点、PIT 证据仅 2 —— **由 Canonical Decision 最终判定** |

### F. 哪些 Conflict 必须交给 Canonical Decision

| 优先级 | Conflict | 议题 |
|---|---|---|
| **P0** | **`CF001`** | 2019–2021 是「一个大周期」还是「多段 Campaign」（决定 campaigns 表 1 行还是 3 行） |
| **P0** | **`CF003`（UNRESOLVED）** | 半导体 vs 电子是否合并 —— **只能由 CMTR v1 / taxonomy 决策回答** |
| **P0** | **`CF006`** | 2024-09-24 后能否与市场 Beta 分离（决定 007 / 008 的存废与置信度） |
| **P1** | `CF002` | 2019–20 国产替代 vs 2024–25 自主可控是否同一 Campaign（Q3） |
| **P1** | `CF004` | 面板/显示是否拆分 |
| **P1** | `CF005` | 面板涨价 vs 缺芯是否同一供给结构两分支（Q5 Residual Test） |
| **P1** | `CF007` | 2016–17 面板 vs 2020–22 面板：两轮 or 两个 Campaign |
| **P1** | `CF009` | 纯下行周期是否进入 canonical campaigns 表（**方法论层面**） |
| **P2** | `CF008` | 2017 显卡/矿机归属（半导体 vs 数字货币） |
| **P2** | `CF010` | 峰值三口径（2020-02 / 2020-07-14 / 2021-07-30） |

> **10 条全部移交，本轮一条未消解。**

### G. 是否建议进入下一阶段 DB Import

> ## ✅ **建议进入**

条件：
1. §E 的 `010` / `012` **保持 RESEARCH_ONLY**（不进 `campaigns` 表）；`008` 按 Canonical Decision 处置
2. §F 的 10 条 Conflict **须在 Canonical Decision 阶段裁决**（尤其 `CF001` / `CF003` / `CF006`）
3. 导入时须处理 §3.3 的两项：共享 evidence（`E035` / `E056`）指定唯一归属；`ticker` 格式映射

**预计 Canonical 增量**（若 001–007 + 011 全部进入，008 待定）：7–8 个新 Campaign。

---

## 9. Validator / Schema 校验缺陷 —— 是否值得独立工程任务

> ## ✅ **值得**，且**必须与 R01-02 Canonicalization 解耦**

**理由**：
1. **已造成实际后果** —— R01-01 的 `CF005._position_note` 违例被放过并已入库（§4.3）
2. **覆盖面广** —— 影响所有后续 R01-03 ~ R01-06 及未来任何 intake 的接收质量
3. **实证确凿** —— 5 个注入缺陷漏检 2 个（额外属性、类型错误）
4. **修复范围清晰且小** —— 在现有 Validator 中增加一道真实 Draft-07 校验
   （并可选增加 unreferenced 提示），**不改 Protocol、不改 Schema**

**建议**（不在本轮执行）：
- 新建独立任务，在 `validate_historical_research_intake.py` 中接入 `jsonschema` Draft-07 校验，
  把 Schema 作为**可执行**约束而非仅 enum/required 的数据源
- 可选：增加 `--strict` 开关与 unreferenced 对象的 WARN 级提示
- 评估是否需要清理 R01-01 `CF005._position_note`

> ⚠️ **本轮不修 Validator** —— 它**不影响 R01-02 Package 的可信接收**
> （R01-02 严格 Schema **0 错误**），因此**不阻塞**本次 Intake Review。

---

## 10. 本轮严格未做

- ❌ 未修改任何已有 Campaign
- ❌ 未创建任何 Canonical Campaign
- ❌ 未执行 Promotion
- ❌ 未导入 DB
- ❌ 未刷新 Structural Analogy
- ❌ 未刷新 Time Observation
- ❌ 未启动 R01-03
- ❌ 未修改 taxonomy（只记录别名缺口）
- ❌ 未消解任何 Conflict
- ❌ 未提前决定任何 Campaign 的合并 / 拆分
- ❌ 未修改 Protocol / Schema / Validator
