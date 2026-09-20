# R01-03 Intake Review v0.1 — 资源 / 有色 / 化工

> **性质**：ThreeC Agent 对 `research/intake/packages/R01-03/` 的 **Intake 层**审查。
> **本轮范围**：只做 Intake Review。**未创建 Canonical Campaign · 未导入 DB · 未修改既有 Campaign ·
> 未修改 taxonomy · 未刷新 Structural Analogy / Time Observation · 未启动 R01-04 ·
> 未修改 Protocol / Schema / Validator / Package。**
> **Worker 报告的 12 条 Conflict 一条未消解**；Campaign 的合并 / 拆分**未提前决定**。

---

## 0. 结论摘要

| 项 | 结果 |
|---|---|
| **A. Package 是否通过 Intake** | ✅ **通过** |
| 现有 Intake Validator（C01–C25） | **PASS（0 FAIL / 0 WARN）** |
| **C25 Strict Draft-07** | **0 违规**（独立复核确认） |
| checksums.sha256（10 条） | 全部一致 ✓ |
| **B. 必须修复的问题** | **1 项**（`008.why_not` 反例窗口错误，见 §5.4） |
| **G. 是否建议进入 Canonicalization** | ✅ **建议**（8 个候选可进入；011 Research Only；006 / 008 附条件） |

---

## 1. Package 验收

### 1.1 规模与 checksum

```
R01-03/  manifest.json · coverage.md · candidates.json · evidence.json · sources.json
         securities.json · exclusions.json · conflicts.json · research_questions.json
         quality_summary.json · checksums.sha256        （11 文件 / 4865 行）
```

| 项 | 数量 |
|---|---:|
| Candidates | **11** |
| Evidence | **61** |
| Sources | **48** |
| Securities | **30** |
| Exclusions | **12** |
| Conflicts | **12** |
| Research Questions | **8** |
| Macro Theme Proposals | **7** |
| Cross-task Notes | **8** |

`manifest`：`intake_protocol_version = 0.1` · `research_round_id = R01` · `task_id = R01-03` ·
`source_commit = 2153f6d83b7481300696ab73d792e9e53aa31a07` · `years 2015–2025`

**checksums**：10 条**全部一致**，引用文件全部存在，无未纳入项 ✓

### 1.2 现有 Intake Validator

```
validate_historical_research_intake.py research/intake/packages/R01-03
  → checks: 25   FAIL: 0   WARN: 0   RESULT: PASS
  → INFO C25  Strict JSON Schema (Draft-07) 校验通过（0 违规）
```

### 1.3 ★ Strict Schema（C25）正式校验

**用 ThreeC 当前已修复的 C25 正式校验**（不沿用 Worker 报告的旧 C01–C24 结论）：

| Package | Draft-07 违规数 |
|---|---:|
| **R01-03** | **0** ✓ |
| R01-01（对照） | 0 |
| R01-02（对照） | 0 |

独立复核（`jsonschema` 4.26.0 / `Draft7Validator` / `FormatChecker`，按 Validator 的装配规则组装完整对象）→ **0 违规** ✓

---

## 2. 结构与引用关系

### 2.1 引用完整性

| 检查 | 结果 |
|---|---|
| candidate → evidence 悬空 | **无** ✓ |
| candidate → security 悬空 | **无** ✓ |
| evidence → source 悬空 | **无** ✓ |
| date_candidates → source 悬空 | **无** ✓ |

### 2.2 孤儿检查（**Worker 报告第 3 项**）

| 类型 | 结果 |
|---|---|
| 悬空引用 | **无** ✓ |
| 孤儿 Evidence（定义但未被引用） | **无（0）** ✓ |
| **孤儿 Source** | **1 个：`R01-RESOURCES-S012`** ⚠️ |
| 孤儿 Security | **无（0）** ✓ |

> ★ **Worker 的「无孤儿 Source」表述不准确。** 存在 1 个孤儿来源：
> `S012`「碳酸锂逼近 60 万元/吨…」（新浪财经转载证券日报，2022-11-14，`media_tier3`/tier 3，
> `IG-SECDAILY-LI`）。其自身 `description` 已写明「**本任务中作为背景参考，未单独绑定 evidence**」
> —— 即**有意引入但未绑定**。经全包扫描，`S012` 在 candidates / evidence / conflicts / exclusions /
> research_questions / coverage / manifest **中均未出现**。
> **不阻塞**（Schema 不要求反向引用；C01–C25 无孤儿检查）。**建议**：绑定至相关 evidence 或移除。

### 2.3 Research Model v1.0 §5 证据门槛

**11 / 11 候选全部满足「≥2 Evidence 且 ≥2 independence_group」** ✓

| candidate | ev | IG | sec | PIT 证据 | 门槛 |
|---|---:|---:|---:|---:|---|
| `001` 工业金属（铜/铝） | 7 | **7** | 6 | 1 | ✅ |
| `002` 能源金属（锂） | 6 | **6** | 5 | 2 | ✅ |
| `003` 稀土 | 7 | **5** | 4 | 3 | ✅ |
| `004` 基础化工（能耗双控） | 6 | **5** | 5 | 5 | ✅ |
| `005` 染料 / 中间体 | 6 | **5** | 2 | 4 | ✅ |
| `006` 黄金（2019–2020） | 4 | **3** | 3 | **1** | ✅ |
| `007` 黄金（2024–2025） | 4 | **4** | 4 | 3 | ✅ |
| `008` 农化（化肥） | 5 | **4** | 3 | **0** ⚠️ | ✅ |
| `009` 铜（2024–2025） | 5 | **3** | 3 | 1 | ✅ |
| `010` 电解铝（2017） | 6 | **5** | 3 | **5** | ✅ |
| `011` 化工（2016） | 5 | **4** | **0** | 1 | ✅ |

### 2.4 evidence 治理

| 维度 | 分布 |
|---|---|
| `temporal_relation` | contemporaneous 31 · subsequent 28 · retrospective 1 · prior 1 |
| `evidence_role` | supporting 56 · context 4 · **contradicting 1** |
| `support_kind` | historical_fact_support 61 · **point_in_time_support 26** · retrospective_context 1 |
| `confidence` | high 30 · medium 31 |
| subsequent / retrospective **缺 `point_in_time_note`** | **无** ✓ |

**共享 evidence（跨候选）**：**0 条** ✓ —— 无需 1:1 消歧（与 R01-01 的 2 条、R01-02 的 2 条不同）。

### 2.5 securities

30 条，**全部有 `ticker`** ✓ · **全部 `survivorship_aware = True`** ✓ ·
`role` 分布：leader 10 · representative 10 · second_leader 5 · follow 5

---

## 3. CMTR v1 检查（**未修改 taxonomy**）

**唯一实现**：`research/scripts/theme_taxonomy.py`（`canonical-macro-theme-resolution-1`）
现有根节点（**11**）：信息通信 · 医药健康 · 国防军工 · 房地产 · 汽车 · 消费 · 电力设备 · 电子 ·
**资源** · 金融 · 高端装备

### 3.1 Macro Theme Proposals

| proposal | 名称 | kind | CMTR status | root |
|---|---|---|---|---|
| `MT001` | 有色金属 | NEW_MACRO_CANDIDATE | **RESOLVED** | **资源** |
| `MT002` | 基础化工 | NEW_MACRO_CANDIDATE | **RESOLVED** | **资源** |
| `MT003` | 贵金属 | SUB_THEME | **RESOLVED** | **资源** |
| `MT004` | 稀有金属/稀土 | SUB_THEME | **RESOLVED** | **资源** |
| `MT005` | 农化 | SUB_THEME | **RESOLVED** | **资源** |
| `MT006` | 能源金属 | CROSS_FAMILY | **UNRESOLVED_NAME** | — ✅ **正确**（跨族问题，非新根） |
| `MT007` | 供给收缩 | MECHANISM | **UNRESOLVED_NAME** | — ✅ **正确**（机制，非主题） |

### 3.2 候选级解析

**11 / 11 候选全部 `RESOLVED`，root = `资源`** ✓
（匹配名：`有色金属` · `基础化工` · `贵金属` · `稀有金属/稀土` · `农化`）

### 3.3 记录的别名缺口（**非阻塞，只记录，本轮不扩展**）

```
工业金属 · 铜 · 电解铝 · 锂 · 锂矿 · 能源金属 · 稀土 · 稀土永磁
化工 · 化学原料及化学制品制造业 · 染料 · 化肥 · 黄金
```

> **判定：无阻塞性 taxonomy gap。** T01 补齐的 `资源` 根及其 5 个子主题足以覆盖 R01-03。
> `MT006 能源金属` 与 `MT007 供给收缩` 的 `UNRESOLVED_NAME` 是**协议期望的正确结果**
> （前者为跨族归属问题、后者为机制轴），**不构成 taxonomy 缺口**。

---

## 4. Worker 报告的 4 个问题 —— 逐项核查

### 4.1 ① Protocol / Validator 的 `research_report` Tier 冲突

**Worker 主张**：Protocol §7.3 规定券商研报 = Tier 3，Validator C08 要求 `research_report` = Tier 2。

**核查结果**：

| 出处 | 对「券商研报」的 tier 规定 |
|---|---|
| **`research/intake/HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md` §7.3** | ❌ **完全未提及「券商研报」**（该节只有通用四级表：Tier 2 = 权威媒体/行业协会/产业原始数据；Tier 3 = 财经媒体转述/一般报道） |
| **`research/research/methodology/research_model_v1_0.md` §15**（**冻结基座**） | ✅ **Tier 3** —— 「Tier 3｜**券商研报** / 研究机构 / 专业财经网站」 |
| **`research/README.md` §5** | ✅ **Tier 3** —— 「Tier 3：券商研报、专业财经网站」 |
| **`research/RESEARCH_MODEL_V1_FREEZE_REPORT.md`** | ✅ **Tier 3**（同 research_model） |
| `historical_campaign_validation_v1.md` §1.2 | 未提及（仅 1/2/3 三级，无 4） |
| **Validator `SOURCE_TYPE_TIER['research_report']`** | ❌ **`(2,)`** —— 强制 Tier 2 |
| **canonical DB 既有数据** | **9 / 9 行全部 tier 2**（`S-HIEQ-*` 与 `S-SEMI-*`） |

**R01-03 Package 的实际情况**：2 个 `research_report`（`S014` / `S040`）**均为 tier 2** → **符合 C08 与 DB 既有惯例** ✓

**定性**：

| 归属 | 判定 |
|---|---|
| **Protocol 问题？** | ❌ **否** —— Protocol §7.3 **根本没有**关于券商研报的规定；Worker 的归因不准确（真实出处是 **Research Model v1.0 §15** 与 `research/README.md`） |
| **Validator 问题？** | ✅ **是** —— C08 的 `research_report → (2,)` 与 **Research Model v1.0 §15（冻结基座）** 直接冲突 |
| **历史兼容口径？** | ✅ **是** —— DB 既有 **9/9 行全部 tier 2**，说明**实际执行一直是 Tier 2**；C08 把这个惯例**固化**了，从而与冻结模型分歧 |

> ★ **结论**：这是 **Validator ↔ Research Model v1.0 的口径冲突**，且属**历史兼容口径**。
> **Package 无过错**（它遵循了实际生效的验证规则）。
> **本轮只记录，不修改**（Research Model v1.0 是冻结基座；Validator 是上一轮刚交付的修复）。
> 详见 §8 H1。

### 4.2 ② `--check` 对 Worker `05_OUTPUT` 的目录假设

**Worker 主张**：其自身 workspace 的 `tools/validate_...py --check` 对 `05_OUTPUT` 目录有假设。

**核查结果**：

- 那是 **Worker 自身 workspace 内**的 standalone validator 问题，**与 ThreeC 主仓库的 Intake 流程无关**
  —— 主仓库的 `--check` 是 R00 版本（`research/scripts/validate_historical_research_intake.py`），
  扫描的是 `research/intake/packages/`，**不是** `05_OUTPUT/`。
- **不影响** ThreeC 主仓库当前 Intake 流程 ✓ → **记录即可，不需修 Worker**。

> ⚠️ **但另有一项独立发现**：主仓库的 `--check` 当前 **FAIL（2 项）**，
> 原因**不是** R01-03，而是 `research/intake/packages/` 下存在一个**空目录 `R01-04/`**
> （19:34 创建，0 个文件）→ Validator 把它当成一个 Package 目录扫描 → `C02 缺少文件` + `C20 无法装配`。
> 详见 §8 H2。

### 4.3 ③ 孤儿 Source

见 §2.2。**结论：有 1 个孤儿 Source（`S012`）**，Worker 的「无孤儿 Source」表述不准确；
但该来源系**有意引入且已自述未绑定**，**不阻塞**。

### 4.4 ④ Strict Schema

见 §1.3。**已用 ThreeC 当前修复后的 C25 Draft-07 正式校验 → 0 违规** ✓
（未沿用 Worker 报告的旧 C01–C24 结论。）

---

## 5. 重点审阅

### 5.1 2021 工业金属 / 锂 / 稀土 / 化工：一个大类周期还是多个独立 Campaign

**载体**：`CF001`（UNRESOLVED）· `CF002`（KEEP_BOTH）· `Q001` · `Q008`

Worker 的做法：建立 `001`（工业金属）、`002`（锂）、`003`（稀土）、`004`（基础化工）四个候选，
**互不合并**，并把「是否属同一「通胀交易 / 周期风格」Theme Cycle」保留为 `CF001`（UNRESOLVED）。

**Intake 判断**：
- 四者的**机制、政策工具、代表标的、启动锚点**均不同（全球流动性+需求复苏 / 新能源需求拉动 /
  配额型供给约束 / 能耗双控行政限产）→ 与「同一时间 ≠ 同一个 Campaign」（规则 4）一致；
- Worker **未**因时间重叠而强行合并，也**未**强行拆分 ✓；
- 但 `CF012` 指出 **同一证券跨候选**（紫金矿业同时属 001/007/009；云天化同时属 004/008；
  中国铝业/云铝股份同时属 001/004/010）→ 这**不构成**合并理由（多主业是合法历史事实），
  但**提示边界可能需重划**。
- **→ 具备进入 Canonicalization 的条件**（`001` `002` `003` `004`），最终边界由 Independence Gate Q1–Q5 判定。

### 5.2 五类机制是否应拆分

Worker 已把「供给收缩」拆为 **5 个子类型**：行政去产能（010）· 能耗双控（004）· 环保约束（011）·
配额型（003）· 安全事故冲击（005）；另加 3 条非供给收缩型：全球流动性+需求复苏（001）·
新能源需求拉动（002）· 成本冲击+出口限制（008）· 矿端结构性缺口（009）。

**Intake 判断**：拆分**有据**（各子类型的政策工具与启动锚点不同），且 Worker 已用 `MT007 供给收缩
（kind = MECHANISM）` 明确声明**它是机制轴而非 Macro Theme** ✓ —— 符合协议。

### 5.3 商品价格 → A 股主题的领先 / 滞后

**载体**：`Q005` · `CF006`（锂：商品 peak 2022-11-11 vs 股价 peak 2021-09-13，差约 14 个月）·
`CF009`（2025-12 金价创新高但 A 股金矿龙头未同步）· `CF010`（2016 化工：商品 +29.84% vs A 股 -7.13%）

**Intake 判断**：这是本包**最有价值**的部分 —— 它**没有**假设「商品涨 → A 股涨」，
而是**主动保留反例**。尤其 `CF010` / `011` 的**同窗口**对照（2016 全年商品 +29.84% vs
申万基础化工全年 -7.13%）是**有效的反例**（见 §5.5 的对照分析）。

### 5.4 ★ 必须修复的问题：`008.why_not` 的反例窗口错误

**Worker 的 `008.why_not`** 称：
> 「A 股「化肥」板块 **2022-03-15 至 2022-12-30** 区间涨跌幅为 **-12.05%**，
> 即商品价格上行期板块并未同向走强，商品与 A 股主题的传导证据不足。」

**问题**：`008` 自身的 `date_candidates.peak` = **2022-03-01 ~ 2022-04-30**。
以 **2022-03-15（≈候选自身峰值）** 为起点度量，得到的是**峰值之后的下跌段**，
**不能**用于证明「商品价格上行期板块未同向走强」。

**该包自身的证据即已否定该结论**：

```
E075  (2021-12-31, contemporaneous, supporting)
      「A 股「化肥」概念板块 2021-01-04 至 2021-12-31 区间涨跌幅为 +24.24%，
        区间最高点 1048.07 点（2021-09-28）」
```

→ 在 `008` 的 **MAIN_RISE 期（2021-01 → 2022-03）**，A 股化肥板块**是上涨的（+24.24%）**。

**对照 `011`（反例成立）**：`011` 的反例 `E105` 取 **2016-01-04 ~ 2016-12-30（完整全年）**，
与商品口径 **同一窗口**（商品 +29.84% vs 板块 -7.13%）→ **反例有效** ✓

> ## 判定：`008.why_not` 的**核心反例论据不成立**（窗口取在峰值之后），
> ## 且与**本包自身的 `E075` 直接矛盾**。
> **属 Package 侧必须修复项**（`why_not` 的结论性表述错误）。
> **本轮只报告，不修改 Package**（协议要求不得擅自改 Package）。

**连带影响**：`008` 的 `classification = mixed`、`confidence = medium` 可能因该错误论据而偏低。
另 `008` 的 **PIT 证据数 = 0**（无任何 `point_in_time_support`）—— 尽管 `E075` 是 `contemporaneous`，
其 `support_kind` 未标 `point_in_time_support`。

### 5.5 资源 / 有色 / 化工之间的 Macro Theme 边界

**载体**：`CF003`（UNRESOLVED，锂跨族）· `CF004`（KEEP_BOTH，稀土机制）· `Q002`–`Q004` · `Q006`

**Intake 判断**：
- CMTR v1 已把 `有色金属` / `基础化工` / `贵金属` / `稀有金属·稀土` / `农化` **全部解析至根 `资源`** ✓
  → **taxonomy 层无缺口**
- 但 `CF003`（锂应归 `资源` 还是 `电力设备`/`汽车`）与 `CF004`（稀土属资源属性还是政策属性）
  属**机制归属**问题，CMTR v1 **不回答**（它只做名称 → 根的解析）→ 必须交 Canonical Decision ✓
- `MT006 能源金属（kind = CROSS_FAMILY）` 的 `UNRESOLVED_NAME` **正确** —— 它本就是一个跨族问题，
  不应作为新根建立 ✓

### 5.6 2016–2017 Priority B 的证据是否达到后续 Canonicalization 要求

| candidate | 年份 | ev / IG | PIT | A 股侧证据 | 判断 |
|---|---:|---|---:|---|---|
| `010` 电解铝 | 2017 | 6 / 5 | **5** | ❌ 无板块指数序列（仅沪铝价格） | **PIT 覆盖优秀**（5/6），但 **A 股扩散证据弱于商品端** → 可进入，须在 Canonical Decision 中评估 |
| `011` 化工 | 2016 | 5 / 4 | 1 | ✅ 有（**-7.13%**，且与商品**同窗口**） | **INSUFFICIENT** → Research Only |

**Intake 判断**：Priority B 的**证据密度确实低于** Priority A，但 `010` 的 PIT 覆盖（5/6）**优于**
多数 Priority A 候选 → **不因 Priority B 而自动降级**；`011` 的问题是**实质性的**（商品与 A 股同窗口反向），
与 Priority B 无关 ✓

### 5.7 `011` 这类「证据薄、A 股同步性弱」的候选

`011`：`research_status = INSUFFICIENT` · `confidence = low` · `0 securities` ·
含 **1 条 `contradicting`**（`E105`，板块 -7.13%）。
Worker 的 `why_not` 明确：「商品价格上行未伴随 A 股板块行情；缺少板块内部结构证据；
也缺少可识别的启动锚点与扩散过程。按协议 §4.2，「资料不足」不等于「不成立」，故用 INSUFFICIENT 而非 REJECT。」

> ## 判定：**应保留 Research Only** ✓
> 反例**同窗口且有效**；`0 securities` 意味着无法建立代表资产组；无启动锚点与扩散过程。
> **不得为了增加 Campaign 数量而强行提升**（与 R01-01 的 006/007、R01-02 的 010/012 同口径）。

---

## 6. Candidate 处置

### D. 具备进入 Canonicalization 的条件

| candidate | 依据 | 附带的 Conflict |
|---|---|---|
| `001` 工业金属（铜/铝） | 7 ev / **7 IG** · high · PIT 1 | `CF001` `CF005` `CF012` |
| `002` 能源金属（锂） | 6 ev / **6 IG** · high · PIT 2 | **`CF003`（跨族，P0）** `CF006` `CF012` |
| `003` 稀土 | 7 ev / 5 IG · high · PIT 3 | `CF004`（机制归类） |
| `004` 基础化工（能耗双控） | 6 ev / 5 IG · high · PIT **5** | `CF001` `CF002` `CF011` `CF012` |
| `005` 染料 / 中间体 | 6 ev / 5 IG · high · PIT 4 | 退潮段证据不足（end 为 PHASE_WINDOW, low） |
| `007` 黄金（2024–2025） | 4 ev / 4 IG · medium · PIT 3 | **`CF009`（P0）** · `end = UNKNOWN` |
| `009` 铜（2024–2025） | 5 ev / 3 IG · medium · PIT 1 | `CF001` `CF012` · A 股传导证据不足 |
| `010` 电解铝（2017） | 6 ev / 5 IG · medium · **PIT 5** | Priority B · A 股扩散证据弱 |

### E. 应保留 Research Only

| candidate | 判定 | 理由 |
|---|---|---|
| **`011` 化工（2016）** | **明确 Research Only** | `INSUFFICIENT` · `low` · **0 securities** · **同窗口反例有效**（商品 +29.84% vs 板块 -7.13%）· 无启动锚点与扩散过程 |
| **`006` 黄金（2019–2020）** | **建议 Research Only**（或补证后进入） | 4 条证据**全部为商品端**（金价 / 美联储 / COMEX 期货 / 2019 金价）—— **A 股板块证据为零**；而 Campaign 要素之一为「市场关注」，`why_campaign` 断言「市场关注充分」**无证据支撑** |
| **`008` 农化（化肥）** | **建议 Research Only**（或修正后进入） | **PIT 证据 = 0**（无任何 `point_in_time_support`）；且 `why_not` 的核心反例论据**不成立**（§5.4）→ 该候选的「商品 vs A 股」结论**当前不可信**，须重新研究 |

> ★ 三者**均不得为了数量而强行提升**。`006` / `008` 若补证（`006` 补 A 股板块序列；`008` 修正
> `why_not` 并补 PIT 标注），可在**后续复核轮次**重新评估。

### F. 必须交给 Canonical Decision 的 Conflict

| 优先级 | Conflict | 议题 | 影响 |
|---|---|---|---|
| **P0** | **`CF001`**（UNRESOLVED） | 2021 资源类：多个独立 Campaign vs 一个「大宗商品超级周期」 | 决定 campaigns 表 1 行还是 4 行 |
| **P0** | **`CF003`**（UNRESOLVED） | 锂的跨族归属（资源 vs 电力设备/汽车） | 决定 002 的 Macro Theme 归属 |
| **P0** | **`CF006`**（KEEP_BOTH） | 锂 peak 口径（商品 2022-11-11 vs 股价 2021-09-13，差 ~14 个月） | 决定 002 的 canonical peak |
| **P0** | **`CF009`**（UNRESOLVED） | 2025-12 贵金属「现货热、股价冷」背离 | 决定 007 的存废与置信度 |
| P1 | `CF002`（KEEP_BOTH） | 2021 电解铝机制归属（再通胀 vs 能耗双控） | 001 / 004 的边界 |
| P1 | `CF004`（KEEP_BOTH） | 稀土机制归类（资源属性 vs 政策属性） | 003 的机制与 classification |
| P1 | `CF005`（KEEP_BOTH） | 2021 有色涨幅口径（申万 40.47% vs 中证 31.31%） | 引用口径，不得混用 |
| P1 | `CF007`（KEEP_BOTH） | 2020 黄金峰值三口径（现货盘中 / 期货盘中 / 期货结算） | 006 的 canonical peak |
| P1 | `CF010`（KEEP_BOTH） | 2016 化工：商品上行 vs A 股下行 | 011 的反例基础 |
| P1 | `CF012`（KEEP_BOTH） | 同一证券跨候选归属（紫金矿业 / 云天化 / 中国铝业等） | 提示 001/004/007/008/009/010 边界可能需重划 |
| P2 | `CF008`（KEEP_BOTH） | 响水事故伤亡人数通报口径（44 / 78 人） | 005 的事件事实 |
| P2 | `CF011`（KEEP_BOTH） | 双控方案印发日期（2021-09-11 / 2021-09-16） | 004 的 start 锚点 |

> **12 条全部移交，本轮一条未消解。**

---

## 7. Intake 层面五项检查

| 检查 | 结果 |
|---|---|
| **完整性** | ✅ Protocol §5.3 的 11 个文件齐备；manifest 16 个顶层字段齐备；各候选 `drivers` 四问、`why_campaign` / `why_not`、`lifecycle` 均填充 |
| **一致性** | ✅ `quality_summary.counts` 与实际一致（C21 PASS）；`confidence_distribution` 6 high / 4 medium / 1 low 与 11 候选一致；分类枚举全部合法 |
| **可追溯性** | ✅ evidence → source 全链可达；`subsequent` / `retrospective` 全部带 `point_in_time_note`；政策锚点优先官方文件（`E091` 四部委通知、`E102` 调度令）；**商品 / 行业 / 政策 / 市场 / 公司事实五类信息严格分列** |
| **冲突识别** | ✅ 12 条冲突，**3 UNRESOLVED + 9 KEEP_BOTH**，全部保留双方；`CF010` 保留商品与 A 股的反向证据；`E105` 单列 `contradicting` |
| **进入 Canonicalization 的条件** | ✅ 见 §6 D / E |

**独立性纪律**：`independence_group` 按来源机构分组；同源转引标记 `retelling` / `primary_source`
（如 `E021`–`E023` 同源于中稀稀土研究院同一文件，共用 `IG-CREOL-RE`，**不虚增独立证据数**）✓
`securities` 区分 **Historical Leader Set（retrospective）** 与 **Point-in-Time Basket** ✓

---

## 8. H. 需要独立工程处理的问题

| # | 问题 | 归属 | 是否阻塞 R01-03 | 建议 |
|---|---|---|---|---|
| **H1** | **Validator C08 的 `research_report → (2,)` 与 Research Model v1.0 §15（券商研报 = Tier 3，冻结基座）冲突**；DB 既有 9/9 行均为 tier 2 → 属**历史兼容口径**被固化 | **Validator ↔ Research Model 口径冲突** | ❌ 不阻塞（R01-03 的 2 个 research_report 均 tier 2，符合 C08） | 独立任务：二者择一对齐。**不得**为对齐而擅改冻结的 Research Model v1.0 |
| **H2** | `research/intake/packages/R01-04/` 为**空目录**（0 文件）→ 主仓库 `intake --check` **FAIL（C02 + C20）** | **仓库卫生**（非 Validator 缺陷） | ❌ 不阻塞 R01-03 单包校验 | 一行修复：移除空目录（或放入 R01-04 的正式 Package）。**本轮未执行**（用户明确不启动 R01-04） |
| **H3** | Validator 无「孤儿 source / evidence」检查（与 R01-02 Review 报告同类） | Validator 增强 | ❌ 不阻塞 | 已在 R01-02 Review 记录；本轮再次实证（`S012`） |

---

## 9. 本轮严格未做

- ❌ 未创建 Canonical Campaign · 未导入 DB · 未修改既有 Campaign
- ❌ 未修改 taxonomy（CMTR v1 只读）· 未修改 Protocol / Schema / Validator / Package
- ❌ 未刷新 Structural Analogy / Time Observation · 未启动 R01-04
- ❌ 未消解任何 Conflict · 未提前决定任何 Campaign 的合并 / 拆分
- ❌ 未修改 `R01-03` Package 的任何字节（`008.why_not` 的问题**只报告不修**）
