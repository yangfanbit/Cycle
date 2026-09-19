# Historical Universe Intake Protocol v0.1

> **性质**：ThreeC 下一阶段 Research 主线的**基础设施**（R00）。本文件**不新增任何历史研究结论**。
> **状态**：`v0.1`（第一版协议，未冻结）
> **适用对象**：所有参与 Historical Universe Expansion 的独立 Research Agent，以及承担 canonicalization 的 ThreeC Agent。

---

## 0. 本协议解决什么问题

ThreeC 当前的主要瓶颈**不是 Product 功能**，而是：

> **Historical Universe 太窄，导致历史结构比较空间有限。**

当前实测基线（`research/database/cycle_research.db`）：

| 项 | 值 |
|---|---:|
| Macro Theme 根节点 | **4**（汽车 · 医药健康 · 信息通信 · 电力设备） |
| Campaign | 13 |
| themes 行 | 19 |
| Structural Analogy 比较对象 | 17 |
| `STRUCTURAL_SUPPORTED` / 其中 STRICT | 4 / **1**（85 条比较） |

**问题**：跨 Macro Theme 结构对应的**候选池太小**。只有 4 个 Macro Theme 时，
「跨族结构对应」在结构上就只能落在极少数组合上 —— 这不是规则太严，而是**宇宙太窄**。

因此需要一个**可重复、可审查、可并行**的历史研究生产流程：

```text
多个独立 Research Agent（并行）
        ↓  各自产出 Intake Package
ThreeC Agent（唯一 canonicalization 权限）
        ↓
Canonical SQLite → validate_db → Coverage Audit → Export
        ↓
Product
```

本协议定义这条链路上**每一步的边界、交付格式与禁止事项**。

---

## 1. Historical Universe 的正式定义

### 1.1 定义

> **Historical Universe** = 为 ThreeC 提供**足够广度**、**足够结构多样性**、
> 可以进行**生命周期比较**与**跨 Macro Theme Structural Analogy** 的
> **「功能性历史机会宇宙」**。

关键词是**功能性**：它的价值不由「收录了多少条」衡量，而由
**「能否支撑结构比较」** 衡量。

### 1.2 明确不是什么

| 不是 | 说明 |
|---|---|
| ❌ 学术型 A 股历史数据库 | 不做穷尽式史料整理；不追求「史料完整度」 |
| ❌ 全市场穷举 | 不要求覆盖所有行业 / 所有年份 / 所有题材 |
| ❌ 按「热门程度」排序 | **不建立任何热度 / 排名 / 权重** |
| ❌ 以 Campaign 数量为 KPI | 见 §9「禁止数量 KPI」 |
| ❌ 对空缺零容忍 | **没有可靠证据的领域允许保持空缺** |

### 1.3 七条判定原则

1. **不是学术数据库。** 目标是「可比较」，不是「可考据」。
2. **不是全市场穷举。** 允许大面积留空。
3. **不是按热门程度排序。** 热门 ≠ 有结构价值。
4. **不以 Campaign 数量为目标。** 数量是**描述性指标**，不是产出目标。
5. **没有可靠证据的领域允许保持空缺。** 空缺是**合法研究状态**，必须显式记录（见 §8 `exclusions`）。
6. **重要的是「结构覆盖」而不是「名称覆盖」。**
   一个 Macro Theme 下只有 1 个 Campaign，且与已有案例机制高度重复 → **结构上等于没有扩容**。
7. **一个 Macro Theme 只出现一次，不代表已经形成充分历史覆盖。**
   覆盖面 = 该族内**机制 / 生命周期 / 事件结构**的多样性，不是「族名出现过」。

### 1.4 关于「同一主题的多个 Campaign」

- **同一个主题的不同年份 / 不同机制可以形成不同 Campaign。**
  例：`C-2019-COMM-5G` 与 `C-2023-COMM-OPTICAL` 同属「信息通信」，
  但机制（政策驱动 vs 需求+技术突破）、生命周期、事件结构均不同 → **两个独立 Campaign 成立**。
- **同一底层事件拆成多个名字，不应自动成为多个独立 Campaign。**
  判定必须走 **Campaign Independence Gate（Q1–Q5）**：
  `research/research/methodology/theme_campaign_separation_v1.md` §2。
  六条禁止规则（同文件 §4）同样适用，尤其：
  - 规则 2：`Sub-theme ≠ Campaign`
  - 规则 3：`不同时间 ≠ 不同 Campaign`
  - 规则 4：`同一时间 ≠ 同一个 Campaign`
  - 规则 6：**不得为「整齐」人为切 Campaign**

> **Research Agent 可以在 `why_campaign` / `why_not` 中给出 Gate 判据的建议结论，
> 但最终判定权在 ThreeC Agent。**

---

## 2. 时间范围（第一轮）

搜索范围 **2015–2025**，**分层处理**：

| 层级 | 年份 | 性质 |
|---|---|---|
| **Priority A** | **2018–2025** | 当前 ThreeC 历史主宇宙的**直接扩容区** |
| **Priority B** | **2015–2017** | **历史回填区** |

### 2.1 硬约束

- Research Agent **可以**一次性研究 2015–2025。
- **不得**因为 2015–2017 资料较难，而**阻塞** 2018–2025 的产出。
  即：Priority A 必须**独立可交付**。
- 2015–2017 的资料**允许大面积 `INSUFFICIENT`**（见 §8 审查结果）。

### 2.2 为什么是 2015

早于 2015 的历史题材存在**结构性资料缺口**（当时的公开信息可得性、
概念板块口径、行情数据可得性均与 2018 年后不可比）。
第一轮**不要求**覆盖 2015 年之前，也**不建议**在未验证资料质量前扩张。

---

## 3. 角色定义

### 3.1 Research Agent（研究生产者）

**可以做**

| 能力 | 交付位置 |
|---|---|
| 搜索历史资料 / 历史事件 | `sources` |
| 建立 Campaign Candidate | `campaign_candidates` |
| 建立 Evidence | `evidence` |
| 建立 Source | `sources` |
| 提出 Lifecycle Proposal | `campaign_candidates[].lifecycle` |
| 提出 Drivers Proposal（四问） | `campaign_candidates[].drivers` |
| 提出 Securities Candidate | `securities` |
| 提出 Macro Theme Proposal | `macro_theme_proposals` |
| 提交 exclusions（**强制**） | `exclusions` |
| 提交 conflicts | `conflicts` |
| 提交重复候选 | `campaign_candidates[].possible_duplicate_of` |
| 提交研究结论与开放问题 | `quality_summary` / `research_questions` |

**不可以做（红线）**

| 禁止 | 原因 |
|---|---|
| ❌ 修改 canonical SQLite（`research/database/cycle_research.db`） | 研究产物不等于 canonical 事实 |
| ❌ 修改 `research/schema/schema.sql` | Research Model v1.0 冻结 |
| ❌ 修改现有历史 Campaign / Evidence / Theme | 已冻结结论不得被新轮次覆盖 |
| ❌ 修改 Macro Theme canonical taxonomy（DB `themes` 表） | canonicalization 是 ThreeC Agent 的权限 |
| ❌ 修改 Product（`src/**`） | 职责分离 |
| ❌ 修改 `exports/timeline_export_v1.json` | 唯一交换目录，只由 exporter 写入 |
| ❌ 修改 Structural Analogy Rule Set v0.2 | 规则冻结 |
| ❌ 宣称自己产出的是 `VERIFIED` | 见 §7.3 |
| ❌ 创造 canonical DB ID（`C-*` / `RC-*` / `TH-*` / `rule_*` / `summer_*` …） | 见 §6.3 |

> **Research Agent 的交付物是 `Research Intake Package`，不是 Canonical Research DB。**

### 3.2 ThreeC Agent（唯一 canonicalization 权限）

**独有权限**

1. 对每个 Package 作出 §4 的**审查结果**。
2. **Cross-task dedupe**（§10）。
3. **Macro Theme Canonicalization** —— 必须走 **CMTR v1**（§11.1）。
4. **Campaign Decision** —— 必须走 **Research Model v1.0 §5**（§11.2）。
5. **Evidence Mapping** —— 写入 `campaign_evidences` 桥表（§11.3）。
6. 写入 Canonical SQLite，并运行 `validate_db`。
7. 决定是否进入 Coverage Audit 与 Export。

**同样受约束**

- 不得修改 Research Model v1.0 / schema / 既有冻结结论。
- 不得为了让某个候选「成立」而放宽 Campaign 判定。
- 不得建立 ranking / score / probability / prediction。

---

## 4. 审查结果（八种，封闭集合）

ThreeC Agent 对**每一个 candidate** 必须给出**恰好一个**结果：

| 结果 | 含义 | 后续动作 |
|---|---|---|
| **`ACCEPT`** | 满足 Campaign 标准，证据充分 | 进入 canonicalization → `campaigns` |
| **`ACCEPT_WITH_CHANGES`** | 成立，但需修正（日期口径 / 分类 / 主题归组 / 阶段） | 修正后进入 canonicalization；**必须记录改动内容** |
| **`MERGE`** | 与**另一个 Package** 的候选属**同一底层 Campaign / Cycle** | 合并为一个 canonical Campaign；**保留双方 provenance** |
| **`DUPLICATE`** | **同一历史事件 / 同一 Campaign 被不同研究任务重复发现**（同一 Package 内或跨 Package） | 只保留一份；被弃者记录 `duplicate_of` |
| **`OBSERVATION_ONLY`** | 存在明显市场事件，但**不满足 Campaign 标准** | 不进入 `campaigns`；可保留为研究观察记录 |
| **`REJECT`** | 不成立（非 Campaign / 数据错误 / 违反方法论） | 不进入 canonical；**必须写明理由** |
| **`INSUFFICIENT`** | **资料不足**，保留候选但暂不进入 canonical Campaign | 留在 intake 层；可作为后续轮次输入 |
| **`DEFER`** | **研究价值存在，但当前证据或分类尚不足** | 留在 intake 层；需指定**缺失项** |

### 4.1 `MERGE` 与 `DUPLICATE` 的区别（必须分清）

| | `MERGE` | `DUPLICATE` |
|---|---|---|
| 对象 | **同一底层 Campaign / Cycle**，被不同 Agent 以不同命名 / 不同边界描述 | **同一历史事件 / 同一 Campaign** 被重复发现 |
| 典型情形 | A 包把「智能驾驶」与「华为汽车」合成一个；B 包拆成两个 → 边界分歧 | 两个任务都发现了 `2019 5G 商用` |
| 处理 | 合并边界，取**证据更强**的边界；记录分歧 | 只留一份；被弃者标 `duplicate_of` |
| provenance | **双方都要保留** | 保留一方，另一方记录指向 |

### 4.2 `OBSERVATION_ONLY` / `INSUFFICIENT` / `DEFER` 的区别

| | 判定依据 | 是否可再进入 |
|---|---|---|
| `OBSERVATION_ONLY` | **有事件、有市场反应，但不够 Campaign**（单股 / 单日脉冲 / 零散新闻） | 需**新的独立证据**改变性质 |
| `INSUFFICIENT` | **资料不够**（不知道发生了什么 / 日期不可考 / 来源不可得） | **补齐资料即可**再评估 |
| `DEFER` | **有价值**，但**分类或证据结构**尚不足以定性 | 需**方法论或分类**层面的澄清 |

> 三者**不得混用**。特别地：
> **「资料不足」不等于「不成立」** —— 用 `INSUFFICIENT`，不要用 `REJECT`。

---

## 5. Research Intake Package

### 5.1 机器可校验结构

**Schema（机器可校验）**：`research/intake/historical_research_intake.schema.json`

### 5.2 顶层字段

```json
{
  "intake_protocol_version": "0.1",
  "research_round_id": "R01",
  "task_id": "R01-01",
  "task_scope": { "...": "见 schema" },
  "generated_at": "2026-09-19T00:00:00Z",
  "source_commit": "<git sha>",
  "macro_theme_proposals": [],
  "campaign_candidates": [],
  "evidence": [],
  "sources": [],
  "securities": [],
  "exclusions": [],
  "conflicts": [],
  "cross_task_notes": [],
  "research_questions": [],
  "quality_summary": {}
}
```

> ⚠️ 这些字段是**交接格式**，**不是新的 Research DB schema**。
> 不得据此新增 SQLite 表 / 列。

### 5.3 标准交接目录（§19 约定）

```text
<task_package>/
├── manifest.json              # task_id / research_round_id / generated_at / source_commit / task_scope
│                              #   + macro_theme_proposals + cross_task_notes（见下方说明）
├── coverage.md                # 人类可读：本任务覆盖了什么、没覆盖什么
├── candidates.json            # campaign_candidates
├── evidence.json              # evidence
├── sources.json               # sources
├── securities.json            # securities
├── exclusions.json            # exclusions（强制）
├── conflicts.json             # conflicts
├── research_questions.json    # research_questions
├── quality_summary.json       # quality_summary
└── checksums.sha256           # 各文件 sha256（用于交接完整性）
```

> **目录模式的字段归属说明**：`macro_theme_proposals` 与 `cross_task_notes`
> **没有**独立的文件，二者放在 `manifest.json` 中（validator 据此装配）。
> 单文件模式则把它们与其他字段一起放在同一个 JSON 顶层。

**硬约束**

- 每个 Task **一个独立 package**。
- **不允许**直接写 canonical DB。
- **不允许**直接修改 existing campaigns。
- **不允许覆盖**以前 package。
- **同一 round 不覆盖旧 task package。**
- Package 可独立保存 / zip / 传递给 ThreeC Agent。

> Validator 同时支持**目录形式**（按上述拆分）与**单文件形式**（把所有数组合并进一个 `.json`）。

---

## 6. ID 与命名空间

### 6.1 既有 canonical 命名空间（Research Agent **不得**使用）

| 实体 | 形态 | 示例 |
|---|---|---|
| Historical Campaign | `C-<YYYY>-<SLUG>` | `C-2023-AD` |
| Research Candidate | `RC-<YYYY>-<SLUG>` | `RC-2023-HUAWEI` |
| Current Candidate | `CC-<YYYY>-<SLUG>` | `CC-2026-BCI-MEDTECH` |
| Theme | `TH-*` | `TH-AUTO` |
| Rule | `rule_*` | `rule_auto_summer` |
| Season | `<season>_<YYYY>` | `summer_2023` |
| Evidence / Source / Event | `E-*` / `S-*` / `EV-*` | `E-2023-01` |

### 6.2 Intake-local ID（**必须**使用）

所有 intake ID **必须带 round 前缀**：

```text
R<NN>-<SCOPE>-<SEQ>
```

示例：

```text
R01-SEMICONDUCTOR-001        candidate
R01-SEMICONDUCTOR-E001       evidence
R01-SEMICONDUCTOR-S001       source
R01-SEMICONDUCTOR-SEC001     security
R01-SEMICONDUCTOR-X001       exclusion
R01-SEMICONDUCTOR-CF001      conflict
R01-SEMICONDUCTOR-MT001      macro theme proposal
R01-SEMICONDUCTOR-Q001       research question
```

> **Validator 规则**：任何 intake ID 若不匹配 `^R\d{2}-...`，**一律 FAIL**。
> 这同时覆盖了「不得创造 canonical DB ID」与「不得冒充 canonical ID」两条。

### 6.3 最终映射由 ThreeC Agent 完成

```text
R01-SEMICONDUCTOR-001  →  （ThreeC Agent 决定）  →  C-2020-SEMI-XXX
```

**Research Agent 不得预填目标 canonical ID。**
不得出现 `target_campaign_id` / `proposed_canonical_id` 一类字段（见 §12 禁止字段）。

---

## 7. Date / Evidence / Source / Point-in-Time Policy

### 7.1 Date Policy（§十）

**不要求**把日期研究到 VERIFIED。允许四种精度：

| `date_precision` | 含义 | 必填 |
|---|---|---|
| `EXACT_DATE` | 可确认到具体某一天 | `date` |
| `DATE_WINDOW` | 只知道一个日期窗口 | `window_start` + `window_end` |
| `PHASE_WINDOW` | 只知道「处于某阶段」，无法定位到日历窗口 | `phase_note` |
| `UNKNOWN` | 无法确定 | 无（但须说明） |

`start` / `peak` / `end` 的每一个候选日期都应尽量给出：

- `date` / `window_*`
- `source_ids`（依据来源）
- `basis`（**依据说明**：observed / inferred / official_event / unknown）
- `confidence`（`high` / `medium` / `low`）
- `alternative_dates`（备选日期）
- `conflict_note`（冲突说明）

**当前阶段原则**：

> **方向正确优先于过度精确；高价值案例以后可以再做 date verification。**

**禁止**：为了得到一个「漂亮日期」而**强制选择**一个口径。
日期存在分歧时，**保留双方**（`alternative_dates` / `conflicts`），不得自动取舍。

### 7.2 Evidence / Source Policy（§十一）

**概念链不可跳跃**：

```text
Source ≠ Evidence ≠ Historical Fact ≠ Verification
```

**Source 必须尽量保留**：`url` · `title` · `publisher` · `published_at` · `tier` · `source_type`

**Evidence 必须尽量保留**：`claim` · `evidence_role` · `event_date` · `evidence_date` · `source_id` · `independence_group`

`evidence_role` 封闭集合：

```text
supporting | contradicting | context
```

**独立性纪律（硬性）**：

> **同一新闻被多个网站转载 ≠ 多个独立 Evidence。**

Research Agent **应主动标记**：

| 标记 | 含义 |
|---|---|
| `independence_group` | 独立性分组（**不同 group 才算独立证据**） |
| `same_origin` | 与另一条 evidence 同源 |
| `retelling` | 转述 / 二手复述 |
| `primary_source` | 一手来源（原始文件 / 官方发布 / 原始数据） |

**Confirmed 门槛**（沿用既有）：**≥2 条 Evidence 且 ≥2 个 `independence_group`**。

### 7.3 来源分级

沿用既有 Tier 1–4（`schema.sql` `sources.tier`）：

| Tier | 类型 |
|---|---|
| **1** | 官方政策 / 部委 / 监管 / 交易所 / 公司公告 / 财报 |
| **2** | 权威媒体 / 行业协会 / 产业原始数据 |
| **3** | 财经媒体转述 / 一般报道 |
| **4** | 论坛 / 博客 / 社交媒体（**只能做线索，不得作为独立证据**） |

`source_type` 与 `tier` **不得矛盾**（沿用 `historical_campaign_validation_v1.md` §1.2）。

### 7.4 Point-in-Time / Temporal Firewall（§十二）

Research Agent **可以**使用今天的回顾性资料帮助确认
**「历史上发生了什么」**。

**不可以**把事后信息伪装成**当时市场已经知道的信息**。

因此每条 Evidence 必须标注 `support_kind`（可多选）：

| `support_kind` | 能用于 | 不能用于 |
|---|---|---|
| `historical_fact_support` | 证明**历史事件确实发生** | 证明当时已知 |
| `point_in_time_support` | 证明**当时（contemporaneous / prior）** 已知 | — |
| `retrospective_context` | 复盘 / 反例 / 结果解释 | **不得**充当启动或主升的同期催化 |

**典型例子**（沿用 `point_in_time.md`）：

> 2025 年文章回顾 2020 年某事件 ——
> ✅ 可以用于「**证明历史事件确实发生**」
> ❌ 不能直接用于「**证明 2020 年投资者当时已经知道这个信息**」

**一致性规则（validator 强制）**：

- `support_kind` 含 `point_in_time_support` → `temporal_relation` 必须是
  `contemporaneous` 或 `prior`。
- `temporal_relation` 是 `subsequent` 或 `retrospective` →
  **必须**填写 `point_in_time_note`（说明其**不得**作为同期催化）。
- `temporal_relation` 是 `retrospective` → `support_kind` **必须**含 `retrospective_context`。

`temporal_relation` 封闭集合（沿用 `schema.sql`）：

```text
contemporaneous | prior | subsequent | retrospective | unknown
```

### 7.5 Research Status

```text
PROVISIONAL | CONFLICT | INSUFFICIENT
```

> **Research Agent 一律不得声明 `VERIFIED`。**
> `VERIFIED` 只能由 ThreeC Agent 在 canonicalization 之后、经人工最终复核授予。

### 7.6 Confidence

```text
high | medium | low
```

**这是研究置信度，不是概率、不是胜率、不是分数。**
不得用于排序，不得换算成任何数值。

---

## 8. Campaign 判定与强制 exclusions

### 8.1 Campaign 判定（基于 Research Model v1.0 §5）

Campaign **至少**需要：

1. **明确 Theme** —— 主题可识别
2. **持续性** —— 不是单日脉冲
3. **市场关注** —— 有可观察的市场参与
4. **可解释 start / end** —— 能说明为什么在这里开始 / 结束
5. **≥2 独立 Evidence**（≥2 个 `independence_group`）

必须保留的状态表达（不得强行升级）：

```text
failed | weak | neutral | unknown | no_clear_campaign | observation-only
```

> **严禁为了「填满行业」而把边缘事件升级为 Campaign。**

`classification_proposal` 封闭集合（沿用 `schema.sql`）：

```text
theme_campaign | industry_trend | event_driven | mixed | unclear
```

### 8.2 `exclusions[]` —— **强制字段**（§十四）

**每个 Research Task 必须提交 `exclusions[]`，且不得为空。**

必须记录：

- 为什么某**热门事件**没有进入 Campaign
- 为什么某案例是**单股事件**
- 为什么两个候选**属于同一 Campaign**
- 为什么某案例**证据不足**
- 为什么某主题**不能建立独立 Macro Theme**

`reason_code` 封闭集合：

```text
OBSERVATION_ONLY | SINGLE_STOCK_EVENT | SAME_CAMPAIGN | INSUFFICIENT_EVIDENCE
| NOT_INDEPENDENT_MACRO_THEME | NOT_A_CAMPAIGN | OUT_OF_SCOPE | OTHER
```

**目的**：**防止只收集成功案例。**

> 若某任务确实「没有需要排除的东西」，必须记录至少一条**范围边界类** exclusion
> （例如：为什么某个相邻方向未被纳入本任务 scope）。

---

## 9. 禁止数量 KPI（§十五）

**协议中明确：不存在任何数量目标。**

| ❌ 不存在 | ❌ 不存在 |
|---|---|
| 「每个行业至少 3 个 Campaign」 | 「必须达到 30 个案例」 |
| 「必须提高 Structural Analogy 支持数量」 | 「必须覆盖 N 个 Macro Theme」 |

**数字只能用于**：

- 描述实际覆盖
- 做 Coverage Audit
- 判断研究是否**明显不足**

**不能**作为 Research Agent 的硬性产出目标。

`quality_summary.no_quantity_kpi_acknowledged` **必须为 `true`**（validator 强制），
作为每个 Package 对这条纪律的显式确认。

---

## 10. 重复与跨任务协调（§十七）

**每个 Research Agent 都可能发现同一案例。**

因此：

| 规则 | 说明 |
|---|---|
| 1 | `candidate_id` **只要求本任务内唯一** |
| 2 | evidence / source **必须可追溯** |
| 3 | **cross-task dedupe 由 ThreeC Agent 执行** |
| 4 | **不得因为与其他任务重复就自行删除** |
| 5 | 重复候选**必须**标记 `possible_duplicate_of` |
| 6 | **merge 由 ThreeC Agent 决定** |

跨任务提示写入 `cross_task_notes[]`：

```text
POSSIBLE_DUPLICATE | OVERLAP | BOUNDARY | HANDOFF
```

> **宁可重复提交，也不要因「怕撞车」而删掉候选。**
> 漏掉一个候选的代价，远高于让 ThreeC Agent 做一次 merge。

---

## 11. Review → Canonical DB 流程（§二十）

```text
Research Agent
      ↓  产出 Intake Package（§5.3 目录）
Intake Package
      ↓
Package Validator          ← research/scripts/validate_historical_research_intake.py
      ↓
ThreeC Agent Review        ← §4 八种审查结果
      ↓
Dedupe                     ← cross-task（§10）
      ↓
Macro Theme Canonicalization  ← ★ 必须走 CMTR v1
      ↓
Campaign Decision          ← ★ 必须走 Research Model v1.0 §5 + Independence Gate Q1–Q5
      ↓
Evidence Mapping           ← 写入 campaign_evidences 桥表
      ↓
Canonical SQLite           ← research/database/cycle_research.db
      ↓
validate_db                ← 必须 0 FAIL
      ↓
Coverage Audit
      ↓
Export                     ← exports/timeline_export_v1.json
```

### 11.1 Macro Theme Canonicalization —— 必须走 CMTR v1

- 唯一实现：`research/scripts/theme_taxonomy.py`
- 规则集标识：`canonical-macro-theme-resolution-1`
- **唯一事实来源是 DB `themes` 表。不接受任何硬编码的「主题族名称表」。**
- 名称无法解析时**不静默丢弃** —— 必须显式报告
  （`UNRESOLVED_NAME` / `unmatched_names`）。
- Research Agent 只能提交 `macro_theme_proposals`（**proposal**），
  并附 `theme_name_candidates` 作为 CMTR 的**输入名称**。
- **不得自行发明第二套 Macro Theme Resolution。**

> **已知 taxonomy 缺口**（沿用 `theme_taxonomy.py` 文档）：
> `F7` —— `RC-2023-HUAWEI` 的题材「华为汽车」不在 DB `themes` 表中。
> 本协议**不修复**该缺口；补录属数据决策，须走独立轮次。

### 11.2 Campaign Decision

- 走 `research_model_v1_0.md` §5（Campaign 判定标准）
- 走 `theme_campaign_separation_v1.md` §2（Independence Gate Q1–Q5）
- 走 §4（六条禁止规则）
- 走 `historical_campaign_validation_v1.md` §5（Start / End / Peak 判定）

### 11.3 Evidence Mapping

- **必须**通过 `campaign_evidences` 桥表显式绑定
- **禁止**将全库 Evidence 挂到一个 Campaign
- 沿用 `point_in_time.md` §4 校验规则

### 11.4 Product 只能消费 Export

Product **不读 intake**、**不读 SQLite**、**不读 DB**。
唯一交换目录：`exports/`。

---

## 12. 禁止字段（validator 强制）

Package 中**不得出现**下列字段（它们是 canonical 持久化字段，出现即意味着越过边界）：

```text
campaign_id  annual_review_id  rule_id  season_id  campaign_year
start_date  end_date  peak_date  strength  result  classification
date_confidence  drift_vs_jun01  drift_vs_jul01  drift_vs_aug01
theme_id  event_id  phase_id  series_id  trade_date
observation_id  verification_method  verified_date  candidate_date
target_campaign_id  proposed_canonical_id  canonical_id
```

**允许**的 intake-local 引用键（值必须带 round 前缀）：

```text
candidate_id  evidence_id  source_id  security_id
```

**禁止的评分 / 排序 / 预测类字段**（含 `*_score` / `*_rank*` / `*_probability` / `*_prediction*` 形态）：

```text
score  rank  ranking  similarity_score  probability  win_rate
expected_return  prediction  forecast  target_price  recommendation
signal_strength  confidence_score
```

> `confidence`（`high|medium|low`）是**研究置信度**，**允许**；
> `confidence_score`（数值）**禁止**。

---

## 13. 机器校验器

```bash
# 校验一个 package（目录或单文件）
python research/scripts/validate_historical_research_intake.py <package>

# 基础设施自检（schema / manifest / packages 目录 / 确定性）
python research/scripts/validate_historical_research_intake.py --check
```

覆盖 20 项检查（见脚本 docstring 与 `--list-checks`）。
**退出码**：`0` = 全部通过；`1` = 存在 FAIL。

---

## 14. 本轮（R00）明确不做

- ❌ 不新增历史 Campaign
- ❌ 不新增大量 Evidence
- ❌ 不修改现有 DB
- ❌ 不修改 schema
- ❌ 不修改 export
- ❌ 不修改 Product
- ❌ 不修改 Structural Analogy
- ❌ 不重跑 Time Observation
- ❌ 不开始研究任何行业
- ❌ 不创建自动执行后续任务的 Prompt

> **R00 只建立基础设施。研究从 R01 开始，且需单独授权。**

---

## 15. 版本与变更

| 版本 | 内容 |
|---|---|
| **v0.1** | 首版：Historical Universe 定义 · 角色边界 · 八种审查结果 · Intake Package 格式 · Date / Evidence / PIT Policy · Campaign 判定 · 强制 exclusions · 禁止数量 KPI · 跨任务协调 · Review→DB 流程 · 禁止字段 |

**变更纪律**：本协议的任何语义变更必须**新建版本**（`v0.2` …），
**不得覆盖 v0.1**（沿用 `AGENTS.md` §4「新增研究轮次必须新建 round / artifact」）。
