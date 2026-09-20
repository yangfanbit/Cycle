# R01-06 Canonical Decision & Import v0.1 — 国防军工

> **性质**：R01-06 的 Canonical Decision + DB Import 落地记录。
> **前置**：`docs/R01_06_INTAKE_REVIEW_v0_1.md`（Intake PASS：C01–C25 = 0 FAIL / 0 WARN，C25 Strict Draft-07 = 0 违规）。
> **Package**：`research/intake/packages/R01-06/`（11 文件 · `source_commit 2153f6d`）。
> **边界**：**未修改** Schema / Research Model v1.0 / Export Contract v1.0 / CMTR v1 / taxonomy /
> Structural Analogy / Time Observation。**未回头修改 R01-01 ~ R01-05。**
> **未处理 R01 全局治理问题**（Source Tier 口径 / 市场关注口径 / Beta 判据 / 商品峰值口径 / taxonomy aliases /
> Worker-Validator 版本差异 —— 统一记录，待 R01 全部完成后另开 Governance / Consistency Review）。
> **判据**：Research Model v1.0 §5 + Campaign Independence Gate Q1–Q5（`theme_campaign_separation_v1.md` §2）。

---

## 1. 7 个 Candidate 最终状态

| # | intake | 年 | 机制 | **最终处置** | canonical_id / 说明 |
|---|---|---:|---|---|---|
| 1 | `001` 2020–2021 装备放量 / 主机厂订单与预付款 | 2020 | 装备采购 / 订单释放 | **PROMOTE** | `C-2020-MIL-EQUIP-ORDER` |
| 2 | `002` 2019「南北船」合并 / 集团战略重组 | 2019 | 军工集团改革 / 资产重组 | **PROMOTE** | `C-2019-MIL-GROUP-RESTRUCTURE` |
| 3 | `003` 2019 国庆 70 周年阅兵 | 2019 | 事件注意力 | **RESEARCH_ONLY** | `RC-2019-MIL-PARADE-70` |
| 4 | `004` 2025 抗战 80 周年阅兵 / 军贸 / 十五五 | 2025 | 事件 + 军贸 + 政策预期（复合） | **RESEARCH_ONLY** | `RC-2025-MIL-PARADE-80` |
| 5 | `005` 2017 军民融合 / 军工混改 | 2017 | 政策文本驱动 | **RESEARCH_ONLY**（需补证） | `RC-2017-MIL-MIXED-REFORM` |
| 6 | `006` 2015 改革牛 / 资产证券化 | 2015 | 改革预期 + 估值（**Beta**） | **RESEARCH_ONLY** | `RC-2015-MIL-REFORM-BULL` |
| 7 | `007` 2024–2025 商业航天 / 卫星互联网 | 2024 | 产业规划 + 商业需求 | **RESEARCH_ONLY** | `RC-2024-MIL-COMMERCIAL-SPACE` |

**2 PROMOTE · 5 RESEARCH_ONLY** · 无 `MERGE` · 无 `EXCLUDE` · 无候选级拆分。

> ★ **未为增加 Campaign 数量而提升 003 / 006**（用户明确要求）。
> ★ **未为「2025 新结构」而机械 Promote 004**。
> ★ **未因当前 root 是「国防军工」就默认纳入 007**。

---

## 2. Gate Q1–Q5 逐候选判定表

| # | Q1 独立注意力中心 | Q2 独立代表标的 | Q3 独立持续性 | Q4 独立生命周期 | Q5 Residual Test | 结果 |
|---|---|---|---|---|---|---|
| **001** | 否（倾向）★同一资金池 | **否**（标的完全重叠） | 无法判定（数据空白） | 无法判定（数据空白） | **单向成立** | **不拆分 → Case C** |
| **002** | **是** | **是**（船舶系 3 标的，与主机厂不重叠） | **是**（约 5 个月，事件链有层级跃迁） | **独立但未完全闭合**（peak 缺失） | **是** | **Case C** |
| **003** | 是 | **否**（仅 1 宽基指数） | **否**（约 4 周） | **否**（全 retrospective） | 否（与 002 同资金池） | **Case A/B → RO** |
| **004** | 是 | **否**（仅 2 宽基指数） | 弱（约 2.5 个月） | **否**（未闭合，阅兵后无材料） | **否** | **Case B → RO** |
| **005** | 是 | **否**（仅 1 宽基指数） | 无法判定（2 月后不可考） | **否**（未闭合） | 无法执行 | **Case B → RO** |
| **006** | 无法与 Beta 分离 | **否**（仅 1 指数，ticker 缺失） | **否**（起止不可考） | **否**（起止不可考） | 无法执行 | **Case A → RO** |
| **007** | 是 | **是**（中国卫星/中天火箭/宏达电子） | 是（约 17 个月） | **否**（未闭合） | 取决于族属 | **族属未定 → RO** |

---

## 3. P0 Conflict 最终裁决

### 3.1 `CF008`｜军费 → 订单传导时滞 → **传导存在但不稳定；军费层不得作为 start 锚点**

**实测链条（2021）**：

| 环节 | 时点 | 来源 | 与下一环节的间隔 |
|---|---|---|---|
| ① 军费预算公布 | **2021-03-08** | 国防部官网（`E-MIL-04`，**T1**，13795.44 亿元 / +6.8%） | → 22 天 |
| ② 订单 / 预付款披露 | **2021-03-30** | 中航沈飞**日常关联交易预计公告**（`E-MIL-01`，**巨潮资讯网 T1 一手 PDF**） | → 2 天 |
| ③ 五大主机厂集中披露 | **2021-04-01** | 天风证券研报（`E-MIL-02`，T3） | → **约 6 周** |
| ④ A 股市场主升启动 | **2021-05-11** | 中证军工指数（`E-MIL-08`） | → 约 3.5 个月 |
| ⑤ 合同负债体现（2021H1 末） | 2021-06-30（半年报 8–9 月披露） | `E-MIL-03`（377.37 亿元，**会计口径代理变量**） | — |
| ⑥ 区间高点 | **2021-12-01** | 中证军工指数 14748 点（`E-MIL-09`） | **距预算公布约 9 个月** |

**★ 关键发现**：
1. **2020H2 启动（2020-06-25 窗口）早于 2021 预算公布约 8 个月** → **2020H2 不可能由 2021 预算驱动**；
   其驱动为 2020-07 媒体「装备采购加速」叙事（`E-MIL-05/07`）+ 券商「十四五」叙事（**非政策文件**）。
2. **预算公布 → 市场主升的时滞约 9 周**（2021-03-08 → 2021-05-11）；**→ 区间高点约 9 个月**。
3. **★ 反向对照**：**2022 年国防预算 +7.1%（阶段新高，`E-MIL-42`）而军工板块全年 -23.63%** → **传导非稳定**。

**裁决**：
- **传导「存在但不稳定」** → 保留 `KEEP_BOTH` 的实质（两方证据均保留）；
- **军费层只能作 `context`**，**不得作为 Campaign start 锚点**（`E-MIL-04` 的 description 亦自述「不是订单本身」）；
- **`start` 取 2020H2 启动窗口（2020-06-25），非军费公布日**；
- **时滞 caveat 已写入** `campaigns.research_notes` 与 `rule_defense_military.observation_window`。

### 3.2 `CF001`｜2020H2 与 2021 是否同一 Campaign → **判为一个 Campaign，不拆分**

- **Q2 = 否**（代表标的完全重叠：中航沈飞 / 航发动力 / 中直股份 / 洪都航空 / 中航西飞）；
- **Q1 倾向否**（同一资金池，Q1 Anti-example）；
- **Q3 / Q4 无法判定**（**2020-08 中旬~12 月区间数据缺失**，无法证明两段之间存在明确阶段边界）；
- **Q5 单向成立**（去掉 2020H2，2021 的「预算→订单→合同负债→市场」链条仍完整；
  去掉 2021，2020H2 仅剩约 1.5 个月预期段 + 5 个月空白，**不能独立构成 Campaign**）。
- → 多数项为「否 / 无法判定」→ **按 Gate 不拆分**。

**★ 未按年度机械拆分**；`start` 取两个候选锚点中的**第一个（2020-06-25）**，第二个（2021-03-29~31）
作为「订单兑现段起点」记录在 `drivers.accelerator`。
**★ 保留重新评估条件**：若后续补齐 2020-08~12 连续行情数据并证明存在明确阶段边界，可重新评估拆分。

### 3.3 `CF004`｜商业航天族属 → **保留 UNRESOLVED；007 不进入任何族的 canonical**

| 维度 | 判定 |
|---|---|
| 军事需求 | 有战略 / 空间资源属性，但**星座本身是商业通信基础设施** |
| 民用商业需求 | **主要驱动**（商业航天、卫星互联网、火箭发射服务） |
| 军民融合 | 跨族方向（`MT007` CROSS_FAMILY），**非独立行业** |
| 资本市场主题 | 有 |
| **主管部门 / 主题** | **工信部 / 国家航天局**，主题是**商业航天 / 卫星通信产业发展** |
| **CMTR v1** | `商业航天` / `卫星互联网` / `卫星导航` → **UNRESOLVED_NAME**（taxonomy 不存在）；仅 `航天装备` → `国防军工` |
| **任务书 excluded_scope** | 「卫星互联网的通信属性部分（可能与信息通信重叠）」→ `X008` **OUT_OF_SCOPE** |

→ **不扩展 taxonomy**（taxonomy 变更属独立轮次）；**007 保持 Candidate 但不进入错误的 `国防军工` Campaign**。

### 3.4 `CF006`｜2015 Beta → **Beta 无法排除 → 006 保持 Research Only**

本包自述「**无法证明这是军工 Campaign 而不是市场 Beta 在军工板块的投射**」、
「**没有任何证据可以把 2015 年军工涨幅与市场 Beta 分离**」、
「**若 ThreeC Agent 判定 Beta 无法排除，应降级为 OBSERVATION_ONLY**」→ **本裁决采纳降级**。
★ **未因 2015 是历史回填空缺年份而降低标准**。

### 3.5 其余 Conflict 裁决

| conflict | 原状态 | **本轮裁决** |
|---|---|---|
| **`CF002`** 2019 南北船 vs 2019 阅兵 是否合并 | UNRESOLVED | **裁决：不合并**。机制不同（集团组织与资产重组 vs 重大纪念事件注意力）；**未因同属 2019 年军工而合并**。002 → Campaign；003 → Research Only |
| **`CF003`** 军工电子 Sub-theme vs 独立 Campaign | RESOLVED_PREFERRED | **确认：Sub-theme，不单独建 Campaign**。与 T01 既定 taxonomy 一致（T01 已将 `军工电子` 设为 `国防军工` 下的 `concept`）；与 R01-02 的 cross-task dedupe 仍待办 |
| **`CF005`** 船舶：民船周期 vs 军品订单 | UNRESOLVED | **保留 UNRESOLVED**。002 **仅承载「集团重组」机制**；2021–2024 民船订单/船价周期未建候选（`X005` HANDOFF）。**与 T01 的张力已记录**（T01 将 `船舶制造`（含民用造船周期）归 `国防军工`）→ 待 R01 收口 Governance Review 对齐 |
| **`CF007`** 2025 阅兵 classification / 持续性 | UNRESOLVED | **裁决：不通过 Gate → 无需在 `theme_campaign` vs `event_driven` 之间选择（两者皆不成立）**；004 → Research Only |
| **`CF009`** 2017 军民融合 vs 混改 | UNRESOLVED | **保留 UNRESOLVED**（不影响 005 的存废判定） |

> **9 条全部处理：5 条给出明确裁决（`CF008` / `CF001` / `CF004` / `CF006` / `CF002` + `CF003` 确认 + `CF007` 判定），
> 3 条明确保留（`CF005` / `CF009`）。未为「解决 Conflict」而强行做确定结论。**

---

## 4. `001` 四层证据链最终评价

| 层 | 承载证据 | tier | **评价** |
|---|---|---|---|
| ① 军费（政策层） | `E-MIL-04` 2021 国防预算 13795.44 亿元 / +6.8%（**国防部官网**） | **T1** | ✅ 成立；★ **evidence 自述「不是订单本身，不单独构成订单兑现证据」**；**只作 context**（`CF008`） |
| ② 订单 / 预付款（订单层） | `E-MIL-01` 中航沈飞 2021 年度**日常关联交易预计公告**（**巨潮资讯网 = 证监会指定披露平台**，一手 PDF） | **T1** | ✅ 成立；★ **该 evidence 明确写「公告具体金额本文不引用，以避免依赖二级转述」→ 未把代理变量写成精确订单总额** |
| ② 补强 | `E-MIL-02` 截至 2021-04-01 五大主机厂均已披露（天风证券研报） | T3 | ✅ 行业级而非单股级；自述「研报统计基于公告，**独立性弱于公告原文**」 |
| ③ 公司经营（基本面层） | `E-MIL-03` 中航沈飞 2021H1 末**合同负债 377.37 亿元** | T3 | ⚠️ 成立但**明确标注为会计口径代理变量**，且自述「**未取得公告原文**」；`E-MIL-15` 2021Q3 公募军工持仓 2.10% |
| ④ A 股市场响应（市场层） | `E-MIL-08`/`09`（中证军工指数 2021 +8.97%、2021-12-01 高点 14748 点）、`E-MIL-10`/`12`（申万军工 2021 +8.6%）、`E-MIL-16`（2022 细分板块下跌） | **全 T3** | ✅ 成立，但**市场层全部为二手整理**（`known_gaps[11]`：未取得指数公司官方历史点位原文） |

**最终评价**：
- **四层链条成立**，且**每一层都标注了其证据等级与局限**；
- **订单层未越界**（一手证据刻意不引用金额；代理变量显式标注为会计口径）；
- **`strength` 定为 `medium`，不升 `strong`** —— 尽管四层完整，但：市场层全为 T3 二手、
  **2020-07 启动段 Beta 未分离**、`peak` 存在 2 个口径、`end` 存在 2 个口径、**2020-08 中旬~12 月数据缺失**。
  → **四层证据完整 ≠ 强度 strong**（用户明确要求）。

---

## 5. `007` 商业航天最终族属

**裁决：族属 UNRESOLVED → 不进入任何族的 canonical（`RC-2024-MIL-COMMERCIAL-SPACE`）**。

理由（四层）：
1. **CMTR v1 无法解析**：`商业航天` / `卫星互联网` / `卫星导航` 均为 `UNRESOLVED_NAME`；
2. **机制不是国防采购**（本包自述）；
3. **主管部门是工信部 / 国家航天局**，主题是商业航天 / 卫星通信产业；
4. **`X008` 已将通信属性列为 OUT_OF_SCOPE** → 继续遵守。

★ **未扩展 taxonomy**；★ **未因当前 root 是「国防军工」就默认纳入**；
★ 与信息通信族 / R01-02 的 cross-task dedupe 仍待办（`N004` POSSIBLE_DUPLICATE）。

---

## 6. `E042` 最终处置 → **入 Canonical DB，但不绑定任何 Campaign**

| 项 | 值 |
|---|---|
| evidence | `E-MIL-42`（intake `R01-MIL-E042`） |
| claim | 2022 年全国财政安排国防支出预算约 1.45 万亿元，同比增长 **7.1%**，为 2019 年以来首次突破 7% |
| date | 2022-03-10 |
| source | 国防部官网（`S-MIL-02`，**T1**） |
| role | `context` |
| confidence | **high** |
| temporal_relation | `contemporaneous` |
| **Campaign 绑定** | **无（research-level）** |

**处置理由（逐条对应用户要求）**：
1. **2022 年证据是否应进入 2015 Campaign** → **否**。原绑定对象 `006`（2015）判为 RESEARCH_ONLY，
   且 2022-03-10 的证据与 2015 结构**无时间关系**；
2. **是否只保留为独立 context / research-level evidence** → **是**。**入 DB 但不绑定任何 Campaign**
   （`evidence_role = context`），与 **R01-05 的 `E141`（沪深300 基准）同口径**；
3. **是否应机械写入 Campaign** → **否**。★ **未为满足 evidence attribution 而破坏 temporal consistency**：
   若将其绑定到 2015 Campaign，`validate_db` 的 `evidence-temporal-mislabel`
   （`contemporaneous` 且 `date > campaigns.end_date`）**必然触发**。
   → 不绑定后，**未产生任何新的 temporal warning**（实测见 §10）。
4. **原始研究 Package 保留** ✓（未修改 Package 任何文件）。

**附带记录**（不在本轮修改）：全包 `evidence_role = contradicting` 数量为 **0**，而本包核心方法论主张
即「军费增长 ≠ 军工行情」→ **反证的 role 标注偏保守**（`E042` 标为 `context`）。
**本轮保持 `context` 不变**（改 role 属修改研究内容）；建议在 R01 Governance Review 中统一。

---

## 7. 新增 2 个 Canonical Campaign

| canonical_id | 年 | start | peak | end | class | strength | result | dc | Theme Cycle |
|---|---:|---|---|---|---|---|---|---|---|
| `C-2020-MIL-EQUIP-ORDER` | 2020 | 2020-06-25 | 2021-12-01 | 2022-12-31 | `mixed` | **medium** | positive | medium | `military_equipment_order_cycle_2020_2022` |
| `C-2019-MIL-GROUP-RESTRUCTURE` | 2019 | 2019-07-01 | **NULL** | 2019-11-26 | `event_driven` | **medium** | positive | medium | `military_group_restructure_2019` |

**关键点**：
- **2 个 Campaign 均 `strength = medium`**（无一个升 strong）；
- **`002` 的 `peak_date = NULL`** —— 未取得 2019-07~08 中船系峰值的可靠日期证据，**不制造精确日期**；
- **`002` 的市场侧行情证据完全缺失**（涨幅 / 峰值 / 持续时间均不可考）→ 已如实记录；
- **`001` 的 `end = 2022-12-31`**（「主题持续性下降」口径，与 lifecycle DECLINING 段一致）；
  alternative = 2022-01-31（「最后一次有效催化」口径）→ 两口径并存，已记录；
- **`001` 的 `peak = 2021-12-01`**（EXACT_DATE）；alternative = 2021-08-24 → **peak cluster，不强行取单日**。

### 7.1 主题归属

| Campaign | main theme | related theme |
|---|---|---|
| `C-2020-MIL-EQUIP-ORDER` | `TH-DEFENSE-AIR`（航空装备） | `TH-DEFENSE`（国防军工） |
| `C-2019-MIL-GROUP-RESTRUCTURE` | `TH-DEFENSE-SHIP`（船舶制造） | `TH-DEFENSE`（国防军工） |

### 7.2 生命周期（`campaign_phases`）

**`C-2020-MIL-EQUIP-ORDER`（6 段）**：
`main_rise` 2020-06-25→2020-08-10 · `retracement` 2021-01-08→2021-05-10（**-32%**）·
`main_rise` 2021-05-11→2021-08-24（**+43%**）· `retracement` 2021-08-25→2021-10-13（-13.8%）·
`secondary_rally` 2021-10-14→2021-11-30（+22.5%）· `decline` 2021-12-02→2022-12-31

**`C-2019-MIL-GROUP-RESTRUCTURE`（2 段）**：
`main_rise` 2019-07-02→**NULL**（结束日期不可考，不强行取值）· `secondary_rally` 2019-10-25→2019-10-28

> ★ `ENDED` / `UNKNOWN` 段无对应 `phase_type`（Schema 无该枚举），**不入 DB**（与 R01-05 同口径）。

---

## 8. Theme Cycle（新增 2 个）

| Theme Cycle | Campaign | Pattern |
|---|---|---|
| `military_equipment_order_cycle_2020_2022` | `C-2020-MIL-EQUIP-ORDER` | 单一 |
| `military_group_restructure_2019` | `C-2019-MIL-GROUP-RESTRUCTURE` | 单一 |

**★ 刻意分成 2 个 Cycle**：两 Campaign **机制不同**（装备采购/订单 vs 集团改革/资产重组）、
**窗口不重叠**（2020–2022 vs 2019）→ 不构成 Sequential（同机制先后）或 Parallel（同机制并存）关系。
★ **Theme Cycle 未成为「无法独立成立的 Campaign」的替代品** —— 两个 Campaign 各自通过 Gate。

---

## 9. 5 个 RESEARCH_ONLY 的独立否决理由

| intake | canonical | **否决理由** |
|---|---|---|
| `003` | `RC-2019-MIL-PARADE-70` | Q2 否（仅 1 宽基指数）· Q3 否（约 4 周）· **Q4 否（全部 3 条证据均为 2025 年 retrospective 复盘，无任何同期一手证据）** · 与 002 同资金池。★ 本包自述「不应作为已成立的历史 Campaign 使用」 |
| `004` | `RC-2025-MIL-PARADE-80` | Q2 否 · Q3 弱（约 2.5 个月）· **Q4 否（生命周期未闭合，阅兵后无材料）** · **Q5 否**（去掉阅兵，军贸无数据 / 十五五无落地证据）。★ **机制复合（阅兵 + 军贸 + 十五五）无法形成统一生命周期 → 不强行合并、不机械 Promote** |
| `005` | `RC-2017-MIL-MIXED-REFORM` | Q2 否 · Q3 无法判定 · **Q4 否（生命周期无法闭合，2017 年 2 月后不可考）**。★ **只能证明「政策存在」，不能证明市场结构** → **需补证后重新评估** |
| `006` | `RC-2015-MIL-REFORM-BULL` | Q2 否 · Q3 否 · **Q4 否（起止均不可考）** · **Q5 无法执行**。★ **Beta 无法排除** → 保持 Research Only |
| `007` | `RC-2024-MIL-COMMERCIAL-SPACE` | **族属 UNRESOLVED** · Q4 否（生命周期未闭合）。★ **不进入任何族的 canonical** |

---

## 10. DB / Export 变化

### 10.1 DB（`research/database/cycle_research.db`）

逐表集合比对（导入前备份 vs 导入后，`set` 差集）：

| table | before | after | Δ | 说明 |
|---|---:|---:|---:|---|
| `themes` | 52 | 52 | **+0** | **taxonomy 未变** |
| `research_rules` | 9 | 10 | +1 | `rule_defense_military` |
| `annual_reviews` | 56 | 58 | +2 | `AR-MIL-2019` / `AR-MIL-2020` |
| `campaigns` | 50 | 52 | +2 | 见 §7 |
| `sources` | 345 | 382 | +37 | |
| `evidences` | 331 | 354 | +23 | 42 intake − 19 RC-only |
| `events` | 123 | 131 | +8 | |
| `securities` | 158 | 171 | +13 | 全部新建（**无 mnemonic / ticker 冲突**） |
| `campaign_themes` | 103 | 107 | +4 | |
| `campaign_evidences` | 309 | 329 | +20 | 001 的 17 + 002 的 3 |
| `campaign_events` | 116 | 124 | +8 | |
| `campaign_securities` | 185 | 194 | +9 | 001 的 6 + 002 的 3 |
| `campaign_phases` | 108 | 116 | +8 | |
| `campaign_date_observations` | 126 | 131 | +5 | 001 的 3（start/peak/end）+ 002 的 2（start/end；peak = NULL 跳过） |

- **全部差异均为 `+N / −0`（纯新增）**，**无任何既有行被修改或删除**；
- `themes` / `market_series` / `market_daily` / `trading_calendar` **完全未变**；
- **R01-01 ~ R01-05 的既有 campaign 逐 rule 比对：0 added / 0 removed** ✓
- **每个 `campaign_year` 均有 `annual_review`**（2019 / 2020，JOIN 验证 2/2 OK）；
- **未绑定 evidence（孤儿 context）3 条**：`E-MIL-40`（2018-12-31）· `E-MIL-41`（2022-08-03）· **`E-MIL-42`（2022-03-10 = E042）**。

### 10.2 Export（`exports/timeline_export_v1.json`，Contract v1.0 不变）

| 数组 | before | after | Δ |
|---|---:|---:|---:|
| `rules` | 9 | 10 | +1 |
| `campaigns` | 50 | 52 | +2 |
| `research_candidates` | 22 | 27 | +5 |
| `events` | 130 | 138 | +8 |
| `signals` | 22 | 22 | **+0** |
| `securities` | 241 | 258 | +17 |

- 顶层结构（`contract` / `timeline_export_version` / `project`）**完全一致**；仅 `generated_at` / `source_commit` 例行更新；
- **既有 50 个 Campaign 逐条深比对：0 修改 / 0 删除**；`research_candidates` 既有 22 个 **0 修改**；
- **`conflicts.json` 的 `conflicts` 数组逐字节一致**；
- **manifest 的既有 51 条目逐条深比对：0 修改**；`Y2018-NO-CLEAR` **与导入前逐元素相同**
  （★ R01-05 修复的 `build_2018()` 跨 Rule 污染防护**继续生效** —— `E-MIL-40` 的 2018-12-31 **未泄漏**）。

---

## 11. 全部验证结果 → **全部 PASS**

| 检查 | 结果 |
|---|---|
| `validate_db.py` | **PASS**（3 条警告 —— 均为 R01-02 **已记录为 unresolved** 的 `E-SEMI-29/47/48`；**与导入前完全相同，未新增任何 temporal warning**） |
| `validate_timeline_export.py`（Contract v1.0） | **PASS**（0 警告；52 campaigns / 27 RC / 138 events / 258 securities） |
| `validate_batch_research.py` | **PASS**（0 警告；53 条目；`{PROVISIONAL: 52, CONFLICT: 1}`） |
| `validate_promotion_manifest.py` | **PASS** |
| `check_doc_schema_consistency.py` | **PASS** |
| `validate_current_research.py` | **PASS** |
| `validate_monorepo_integrity.py` | **PASS** |
| `refresh_current_research.py --check` | **PASS** |
| `validate_historical_research_intake.py --check` | **PASS**（packages found 6） |
| Intake Validator × 6（R01-01 ~ R01-06） | **PASS** |
| Intake Validator 单元测试 | **PASS**（44 tests） |
| 幂等性（import `--verify`） | **PASS**（`计划写入 0 行`） |
| Export 幂等性 / 深比对 | **PASS**（既有 50 Campaign 0 修改） |
| **taxonomy 未变 / R01-01~05 无无关变化** | **PASS**（themes 52→52；各既有 rule 0 added / 0 removed） |
| **无新增 temporal warning** | **PASS**（3 条与导入前完全相同） |

---

## 12. 尚未解决的问题

| # | 问题 | 状态 |
|---|---|---|
| 1 | **`CF001`** 2020H2 与 2021 的阶段边界 | 判为一个 Campaign；**保留重新评估条件**（需补齐 2020-08~12 连续行情） |
| 2 | **`CF005`** 船舶：民船周期 vs 军品订单 | **UNRESOLVED**；与 T01 的归属张力待对齐 |
| 3 | **`CF009`** 2017 军民融合 vs 混改 | **UNRESOLVED** |
| 4 | **`CF004`** 商业航天族属 | **UNRESOLVED**；007 保持 Candidate |
| 5 | **`001` 的 Beta 污染**（2020-07 启动段） | **未分离**（`Q002` 未决） |
| 6 | **`002` 市场侧行情证据完全缺失** | 已如实记录；`peak` 为 NULL |
| 7 | **`003` / `004` / `005` / `007` 生命周期未闭合** | 已如实记录 |
| 8 | **`005` 需补证** | 补证方向：2017 年军工板块全年 / 分月行情序列 + 混改落地公告（`Q008`） |
| 9 | **全包 `evidence_role = contradicting` = 0** | `E042` 标为 `context`；建议 R01 Governance Review 统一 |
| 10 | **本地无军工行情序列** | Export `market_data = unavailable`；市场数据仅引自 intake 二手整理 |
| 11 | **`R01-MIL-SEC003`（国证军工指数）`ticker = null`** | 已如实记录（`basis` 说明「未取得指数代码」） |
| 12 | **`CF004.note` 笔误「TwoC Agent」** | Package 侧文档缺陷，已记录，**未修改 Package** |
| 13 | **`002.why_not` 引用「R01-MIL-CF004」讨论 classification** | Package 侧交叉引用错误（CF004 实为商业航天族属），已记录 |
| 14 | **4 条 evidence 缺 `event_date`**（`E-MIL-08` / `17` / `37` / `38`） | DB 导入后 `date = NULL`（Schema 允许） |
| 15 | `E-SEMI-29/47/48` temporal 标注（**R01-02 遗留**） | 保留现状（非本轮引入） |
| 16 | **R01 全局治理问题**（Source Tier 口径 / 市场关注口径 / Beta 判据 / 商品峰值口径 / taxonomy aliases / Worker-Validator 版本差异） | **本轮统一记录，未修改**；待 R01 全部完成后另开 **R01 Governance / Consistency Review** |

---

## 13. 本轮严格未做

- ❌ 未修改 **Schema** / **Research Model v1.0** / **Export Contract v1.0** / **CMTR v1** / **taxonomy**；
- ❌ 未修改 `themes`（52 → 52）、`market_series` / `market_daily` / `trading_calendar`（零改动）；
- ❌ 未修改 **Structural Analogy** / **Time Observation**；
- ❌ 未回头修改 **R01-01 ~ R01-05** 的任何 Campaign / Evidence / Source / Export 数据（逐 rule 验证 0 变化）；
- ❌ 未修改任何 **Intake Package**（R01-01 ~ R01-06 的 11 文件与 checksums 均未动）；
- ❌ **未处理 R01 全局治理问题**（用户明确要求本轮只记录、不修改）；
- ❌ 未为增加 Campaign 数量而提升 003 / 006；未为「2025 新结构」而机械 Promote 004；
- ❌ 未把「市场关注必须有 A 股市场侧证据」写成新的正式 Protocol，**未回改 R01-01 ~ R01-05**；
- ❌ 未把 `E042` 机械写入 Campaign；未为满足 evidence attribution 而破坏 temporal consistency；
- ❌ 未因「国庆 70 周年 / 抗战 80 周年阅兵」事件重大而默认形成 Campaign；
- ❌ 未把「商业航天」直接等同于「国防军工」；未扩展 taxonomy。

---

## 14. 交付物

| 文件 | 说明 |
|---|---|
| `research/scripts/import_r01_06_canonical_v0_1.py` | 本轮 Canonical Import 脚本（幂等；`--dry-run` / `--verify`） |
| `research/scripts/batch_auto_research.py` | 扩展 R01-06 的 `MIL_RULE` / THEME_CYCLE / RESEARCH_CANDIDATES / CAMPAIGN_LIFECYCLE / CANDIDATE_LIFECYCLE / CAMPAIGN_DRIVERS / CANDIDATE_DRIVERS / RULE_META / PROXY_NOTE / scope |
| `research/database/cycle_research.db` | 新增 2 Campaign 及其关系（**纯新增**） |
| `exports/timeline_export_v1.json` | Contract v1.0（**纯新增**） |
| `research/research/batch/auto_2018_2025_batch_manifest.json` | 51 → 53 条目 |
| `research/research/batch/conflicts.json` | `conflicts` 数组未变 |
| `docs/R01_06_CANONICAL_DECISION_v0_1.md` | 本文件 |
| `docs/PROJECT_STATE.md` | 同步更新 |
