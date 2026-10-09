# RESEARCH_AGENT_PROMPT_R02-03.md

> | 项 | 值 |
> |---|---|
> | 用途 | **交给 Research Agent 的任务 Prompt**（本文件可整段复制给另一个 Agent） |
> | 任务 | `R02-03` · 四方向历史扩容：煤炭 / 电力（运营端） / 流感疫苗 / 文化传媒 |
> | 签发方 | **ThreeC Agent**（本次对话执行者） |
> | 依据 | `research/intake/HISTORICAL_UNIVERSE_R02_TASK_MANIFEST_v0_1.json` |
> | 状态 | 用户 **2026-10-09 已授权启动** |

---

## ★ 用法

把本文件 **§1 以下全部内容** 复制给 Research Agent，并把这两条路径一并给它：

- 任务清单（**权威 scope，与本文件冲突时以它为准**）：
  `research/intake/HISTORICAL_UNIVERSE_R02_TASK_MANIFEST_v0_1.json`
- 协议（**权威格式与纪律**）：
  `research/intake/HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md`
  · Schema：`research/intake/historical_research_intake.schema.json`

**样例包**（照它们的形状做）：
`research/intake/packages/R02-01/` · `research/intake/packages/R02-02/`

---

# 1. 你是谁

你是 **Research Agent**（研究生产者）。你的交付物是
**一个 Research Intake Package** —— **不是** canonical 研究数据库。

> ★ 你的产出**一定会被另一个执行者（ThreeC Agent）逐条审查**。
> 你的价值在于**可核验**，不在于**数量**。**宁可空缺，不得凑数。**

---

# 2. 最小必要背景（你不需要读整个仓库）

**ThreeC** 是一个「A 股历史机会时间轴 / 历史机会地图」。它要回答的是：

> **一年中，历史上哪些时间窗口反复出现过什么类型的题材炒作？**

所以它需要的不是「行业统计」，而是**市场上真正被炒作过的题材，以及它们的时间结构**。

核心链路：

```
今天的位置 → 历史同期 → Theme/Campaign 生命周期 → 相关因素 → 提前观察 → 当前状态与历史结构对照
```

**它明确不是**：买卖信号 / 荐股 / 价格收益预测 / 概率 / 胜率 / 推荐分 / 实时行情。

**为什么需要这一包**：用户 2026-10-08 亲自点名了四个方向
（煤炭 / 电力 / 流感疫苗 / 文化传媒），而实测这四个方向在现有历史研究里
**一个都不命中**（最细口径 41 行主题材，全部未命中）。这是**覆盖缺口**，不是显示问题。

---

# 3. 四条红线（违反即整包作废）

| # | 禁止 | 说明 |
|---|---|---|
| 1 | **不得**修改任何既有文件 | 不改 canonical SQLite · 不改 `schema.sql` · 不改任何现有 Campaign / Evidence / Theme · 不改 `exports/` · 不改 `src/**` · 不改 SA 规则集 |
| 2 | **不得**创造 canonical ID | 不得出现 `C-*` / `RC-*` / `CC-*` / `TH-*` / `rule_*` / `E-*` / `S-*`。**所有 ID 必须带 round 前缀**（见 §9） |
| 3 | **不得**出现评分 / 排序 / 预测字段 | 禁止 `score` `rank` `ranking` `probability` `win_rate` `expected_return` `prediction` `forecast` `target_price` `recommendation` `signal_strength` `confidence_score`。也**不得**出现 `campaign_id` `start_date` `peak_date` `theme_id` 等 canonical 持久化字段名（完整清单见协议 §12） |
| 4 | **不得**声称 `VERIFIED` | 你的 `research_status` 只能是 `PROVISIONAL` / `CONFLICT` / `INSUFFICIENT` |

★ **你的写入范围只有一处**：新建目录 `research/intake/packages/R02-03/`。
**不得覆盖**任何已有 package（包括 R02-01 / R02-02）。

---

# 4. 你的任务：四个方向

四个方向**各自独立成族**，必须分别给出 coverage 与 exclusions，**不得**合并成一条「泛周期」。

## 4.1 煤炭

- **机制假设**（待你核验，不是结论）：供给收缩 / 价格驱动 —— 供给侧改革、安监限产、长协、进口政策。
- ★ **与已有「资源」族的关系**：库内已有 `有色金属` / `贵金属` / `稀有金属·稀土`。
  煤炭**是否**属同一族、还是独立族 —— 你**只能提交 proposal**，
  最终由 ThreeC Agent 走 CMTR v1 判定。**不得**自行归入。
- ★ 若判定为同族，你必须说清煤炭的机制轴与既有对象的**差异**，否则这个方向等于没有增量。

## 4.2 电力（公用事业 · **运营端**）

> ★★ 用户 2026-10-09 指令原文：「**电力 细分 根据市场炒作过的概念/板块进行区分**」

**这条指令是本节的核心，必须严格执行。**

### (a) 细分口径 = **市场炒作过的概念 / 板块**

- ✅ **要**：A 股当年**实际被当作独立题材炒作过**的概念名 / 板块名（用**当时的原始名**，不要事后重命名）。
- ❌ **不要**：教科书式行业分类（火电 / 水电 / 核电 / 风电 这种静态切分），也不要申万三级行业表。
- ★ **一个细分若在市场上从未被当作独立题材炒作过，就不应单独成段** —— 那会造出一行没有历史对应物的空行。

### (b) 待核验的概念候选清单（**不是已确认事实**）

| 概念候选 | 可能的时间带 | 备注 |
|---|---|---|
| 电力体制改革 / 新电改（售电侧 · 配售电） | 2015 前后 | 中发 9 号文 |
| 火电（煤价—电价剪刀差 · 煤电联动） | 2015–2016 / 2021 | |
| 水电（来水 · 汛期 · 利用小时） | 多轮 | ★ **季节性最可能明显**，见 (d) |
| 核电（核准重启 · 华龙一号） | 2019 前后 | |
| 绿电 / 新能源运营商（风光运营 · 绿电交易） | 2021 前后 | |
| 电力现货市场 / 辅助服务市场 | 2022–2024 | |
| 虚拟电厂 / 需求侧响应 | 2023–2025 | |
| 抽水蓄能 / 储能**运营** | 2021–2022 | ★ 储能**设备**属「电力设备」，不属本方向 |
| 电价改革（分时电价 · 容量电价） | 2021–2023 | |
| 绿证 / CCER / 碳交易 | 2017 / 2021–2024 | ★ 与「资源」可能交叉 |
| 「算力+电力」/ 数据中心供电 | 2024–2025 | ★ 与「信息通信」「电子」高度交叉，**默认不归本方向**，除非证据显示炒作主线是电力供给侧 |

**每一条都必须用来源核验**「该概念在 A 股是否真被当作独立题材炒作过、在哪几年」。
**核验不通过的写入 `exclusions[]`，不得留在 candidates 里。**

### (c) ★★ 必须与库内已有的「电力设备」严格区分

| | 库内 `电力设备` | 本方向 `电力` |
|---|---|---|
| 端 | **制造端** | **运营端** |
| 机制 | 设备需求与产能 | 成本、电价与利用率 |
| 库内已有主题材 | `电网/输变电设备` · `光伏/新能源发电设备` | 无 |

**明确排除**（不属本方向）：特高压 · 电网投资 · 输变电设备 · 光伏/风电**制造** · 储能**设备**。
**若你的命名被 CMTR 解析到「电力设备」根节点，必须显式标记 `CONFLICT`，不得静默归入。**

### (d) ★ 季节性必须专门核验

用户点名这四个方向的理由是「**时间相关性都挺高的**」。
所以每个细分都要核验**是否存在可复现的年内窗口**（如水电来水与汛期、迎峰度夏、冬季供暖）。
★ 这是**待核验假设**，结果必须来自来源，**不得凭常识写入**。

## 4.3 流感疫苗

- **机制假设**：季节性需求 + 公共卫生事件驱动（毒株预测、批签发、接种率）。
- ★ **与既有对象的重叠判定**：库内已有 `RC-2020-PANDEMIC`（Research Candidate）
  与主题材「疫情医疗」。
  流感疫苗有**可预期的年度季节性**，与一次性疫情事件机制不同 ——
  但你必须走 **Campaign Independence Gate（Q1–Q5）** 证明其独立性，
  **不得**仅凭名称不同就新建。
- ★ 库内医药健康是**最薄**的一族，这是**已知缺口**，不是你必须填满的配额。

## 4.4 文化传媒

- **机制假设**：政策/监管周期 + 内容供给 + 平台经济（游戏版号、影视、出版、广告）。
- ★★★ **全库零覆盖** —— 主题材层 41 行里「传媒 / 文化 / 娱乐 / 教育」一个都不命中；
  大主题层 12 行同样没有。**这是最彻底的空缺。**
- ★ **重要澄清（避免误会）**：「广电 / 传媒」这个**名字**确实存在于仓库里，
  但在 **legacy 层** `data/candidate/themes.ts` —— 而 `data/` 已被判定
  **「无消费者」**（`AGENTS.md` §5.1），**不在 canonical export 里**，产品不消费它。
  **所以产品实际口径下文化传媒是 0 覆盖**，不是「已包含在细分里」。
- ★ **季节性假设**：春节档 / 暑期档 —— 同样**必须用来源核验**。
- ★ 本任务只做**历史侧**。文化传媒还需要一个**当前研究对象**（当前侧），
  但那**不属本任务范围** —— 不要去做。

---

# 5. 时间范围

| 层级 | 年份 | 要求 |
|---|---|---|
| **Priority A** | **2018–2025** | **必须独立可交付** |
| Priority B | 2015–2017 | 允许大面积 `INSUFFICIENT` |

**硬约束**：不得因 Priority B 资料难找而阻塞 Priority A 的产出。
**不建议**扩张到 2015 年之前。

---

# 6. 交付目录（缺任一文件即视为未完成）

```text
research/intake/packages/R02-03/
├── manifest.json            # task_id / research_round_id / generated_at / source_commit / task_scope
│                            #   + macro_theme_proposals + cross_task_notes（这两个字段只放在这里）
├── coverage.md              # 人类可读：覆盖了什么、没覆盖什么
├── candidates.json          # campaign_candidates
├── evidence.json            # evidence
├── sources.json             # sources
├── securities.json          # securities
├── exclusions.json          # exclusions（**强制，不得为空**）
├── conflicts.json           # conflicts
├── research_questions.json  # research_questions
├── quality_summary.json     # quality_summary
└── checksums.sha256         # 各文件 sha256（用于交接完整性）
```

顶层必填字段（schema 强制）：

```
intake_protocol_version · research_round_id · task_id · task_scope · generated_at
· source_commit · macro_theme_proposals · campaign_candidates · evidence · sources
· securities · exclusions · conflicts · cross_task_notes · research_questions · quality_summary
```

## 6.1 各结构的必填字段

**`campaign_candidates[]`**
`candidate_id` · `title` · `year` · `macro_theme_proposal` · `theme_name_candidates`
· `theme_summary` · `date_candidates` · `lifecycle` · `classification_proposal` · `drivers`
· `evidence_ids` · `security_ids` · `research_status` · `confidence` · `point_in_time_notes`
· `why_campaign` · `why_not` · `notes`

> ★ `why_not` 是**必填** —— 你必须写出「为什么它**可能不是**一个 Campaign」。
> 这是防止只收集成功案例的机制。

**`date_candidates[]`**（`start` / `peak` / `end` 各一个）
必填：`date_precision` · `basis` · `confidence`
可选：`date` · `window_start` · `window_end` · `phase_note` · `source_ids` · `evidence_ids`
· `alternative_dates` · `conflict_note`

`date_precision` 四值：`EXACT_DATE` · `DATE_WINDOW` · `PHASE_WINDOW` · `UNKNOWN`
`basis`：`observed` / `inferred` / `official_event` / `unknown`

**`lifecycle[]`**
必填：`stage_proposal` · `start` · `end`
`stage_proposal` 七值：`MAIN_RISE` · `PEAK` · `RETRACEMENT` · `DECLINING` · `SECONDARY` · `ENDED` · `UNKNOWN`

**`evidence[]`**
必填：`evidence_id` · `claim` · `evidence_role` · `evidence_type` · `source_id`
· `confidence` · `independence_group` · `temporal_relation` · `support_kind` · `description`

**`sources[]`**
必填：`source_id` · `title` · `publisher` · `source_type` · `tier` · `independence_group`

**`securities[]`**
必填：`security_id` · `name` · `role` · `basis` · `source_ids` · `point_in_time_note`
`role` 四值：`leader` · `second_leader` · `representative` · `follow`
（另有可选 `ticker` · `exchange` · `survivorship_aware`）

**`exclusions[]`** — 必填：`exclusion_id` · `subject` · `reason_code` · `rationale`
`reason_code` 八值：`OBSERVATION_ONLY` · `SINGLE_STOCK_EVENT` · `SAME_CAMPAIGN`
· `INSUFFICIENT_EVIDENCE` · `NOT_INDEPENDENT_MACRO_THEME` · `NOT_A_CAMPAIGN` · `OUT_OF_SCOPE` · `OTHER`

**`conflicts[]`** — 必填：`conflict_id` · `subject` · `positions` · `resolution`

**`research_questions[]`** — 必填：`question_id` · `question`

**`macro_theme_proposals[]`** — 必填：`proposal_id` · `proposed_name`
· `theme_name_candidates` · `proposal_kind` · `rationale`

**`quality_summary`** — 必填：`counts` · `confidence_distribution` · `coverage_notes`
· `known_gaps` · **`no_quantity_kpi_acknowledged`（必须为 `true`）**

---

# 7. 日期策略

**不要求**把日期研究到 VERIFIED。四种精度任选，但**必须诚实标注**：

| 精度 | 含义 | 必填 |
|---|---|---|
| `EXACT_DATE` | 可确认到具体某一天 | `date` |
| `DATE_WINDOW` | 只知道一个窗口 | `window_start` + `window_end` |
| `PHASE_WINDOW` | 只知道「处于某阶段」 | `phase_note` |
| `UNKNOWN` | 无法确定 | 说明原因 |

> **方向正确优先于过度精确。**

**禁止**为了得到一个「漂亮日期」而强制选一个口径。
日期有分歧时**保留双方**（`alternative_dates` / `conflicts`），**不得自动取舍**。

---

# 8. 来源与证据策略

## 8.1 概念链不可跳跃

```
Source ≠ Evidence ≠ Historical Fact ≠ Verification
```

## 8.2 来源分级

| Tier | 类型 |
|---|---|
| **1** | 官方政策 / 部委 / 监管 / 交易所 / 公司公告 / 财报 |
| **2** | 权威媒体 / 行业协会 / 产业原始数据 |
| **3** | 财经媒体转述 / 一般报道 |
| **4** | 论坛 / 博客 / 社交媒体（**只能做线索，不得作为独立证据**） |

★★ **关键约束（R02-01 踩过的坑）**：
**Tier 3 只能用于「转述 Tier 1/2 的事实」。**
凡「指数涨跌幅 / 市值口径」这类**只能来自商用数据库（Wind 等）** 的数字，
**不得**作为独立事实提交。若确需引用，必须在 `quality_summary.known_gaps` 里
**显式标注不满足协议要求**，交由 ThreeC Agent 判定。
**宁可空缺，不得凑数。**

## 8.3 独立性纪律（硬性）

> **同一新闻被多个网站转载 ≠ 多个独立 Evidence。**

必须标记：`independence_group`（不同 group 才算独立）· `same_origin` · `retelling` · `primary_source`

**Confirmed 门槛**：**≥2 条 Evidence 且 ≥2 个 `independence_group`**。

## 8.4 Temporal Firewall（时点防火墙）

你可以用**今天的回顾性资料**帮助确认「历史上发生了什么」，
**不可以**把事后信息伪装成「当时市场已经知道的信息」。

每条 Evidence 必须标 `support_kind`（可多选）：

| `support_kind` | 能用于 | **不能**用于 |
|---|---|---|
| `historical_fact_support` | 证明历史事件**确实发生** | 证明当时已知 |
| `point_in_time_support` | 证明**当时（同期或之前）已知** | — |
| `retrospective_context` | 复盘 / 反例 / 结果解释 | **不得**充当启动或主升的同期催化 |

一致性规则（validator 强制）：
- `support_kind` 含 `point_in_time_support` → `temporal_relation` 必须是 `contemporaneous` 或 `prior`
- `temporal_relation` 是 `subsequent` / `retrospective` → **必须**填 `point_in_time_note`
- `temporal_relation` 是 `retrospective` → `support_kind` **必须**含 `retrospective_context`

`temporal_relation` 五值：`contemporaneous` · `prior` · `subsequent` · `retrospective` · `unknown`

---

# 9. ID 命名（**全部必须带 round 前缀**）

```
R<NN>-<SCOPE>-<SEQ>
```

本任务用 `R02-` 前缀，建议 scope 分段：

```text
R02-COAL-001      煤炭 candidate        R02-COAL-E001      evidence
R02-POWER-001     电力 candidate        R02-POWER-S001     source
R02-VACCINE-001   流感疫苗 candidate    R02-VACCINE-SEC001 security
R02-MEDIA-001     文化传媒 candidate    R02-MEDIA-X001     exclusion
R02-*-CF001       conflict              R02-*-MT001        macro theme proposal
R02-*-Q001        research question
```

> **Validator 规则**：任何 ID 不匹配 `^R\d{2}-...` **一律 FAIL**。
> **不得预填目标 canonical ID**，也不得出现 `target_campaign_id` / `proposed_canonical_id`。

---

# 10. ★ 提交前自检（**必做**）

```bash
# ★ 必须用这个解释器（系统 python3 缺 jsonschema，C25 会 FAIL）
/Users/yangfan/.workbuddy-ai/binaries/python/envs/default/bin/python \
  research/scripts/validate_historical_research_intake.py research/intake/packages/R02-03

# 查看全部检查项
... --list-checks
```

**退出码 `0` = 全部通过；`1` = 存在 FAIL。**
校验器覆盖 **25 项**检查（C01–C25），包括：
ID 前缀、必填字段、引用完整性、来源分级、时点一致性、**禁止字段**、
**禁止评分/排序/预测**、exclusions 非空、**LF 行尾与确定性**、**严格 JSON Schema（C25）**。

> ★ **未通过严格 Schema 校验的 Package 不得接收。**
> 交回前请贴出 `RESULT: PASS` 的输出。

**行尾**：所有文件必须 **LF**（不要 CRLF）—— C20 会检查。

---

# 11. ★★ 常见失败模式（本项目实测教训，请逐条避免）

| # | 失败模式 | 后果 |
|---|---|---|
| 1 | **把摘要写进引号里当成原文** | 本项目 self-review 实测抓到 **27 条**「改写冒充引文」。引用必须**逐字**，否则改用间接叙述 |
| 2 | **为了填满方向而把边缘事件升级为 Campaign** | 明令禁止。**「该方向历史上没有形成 Campaign」是合法且有价值的结论** |
| 3 | **靠放宽规则提高命中率** | 禁止。`NO_VALID_CORRESPONDENCE` 是**结论**，不是缺陷 |
| 4 | **把「名字相近」当成「结构对应」** | `Theme / Name 相似 ≠ Structural Correspondence` |
| 5 | **只收集成功案例** | 所以 `exclusions[]` 强制非空、`why_not` 必填 |
| 6 | **同一新闻多站转载当成多条独立证据** | 必须用 `independence_group` 去重 |
| 7 | **拿商用数据库的指数涨跌幅当独立事实** | Tier 3 只能转述 Tier 1/2；否则写入 `known_gaps` |
| 8 | **把 2026 年当下的事件写成历史 Campaign** | 超出 2015–2025 历史研究窗口 |

---

# 12. 交付后会发生什么

1. **ThreeC Agent**（本次对话的执行者）对你**每一个 candidate** 给出**恰好一个**审查结果
   （八种封闭集合：协议 §4）。
2. Cross-task dedupe（与 R01-01…R02-02 去重）。
3. Macro Theme 走 **CMTR v1** 解析；Campaign 走 **Research Model v1.0 §5 + 独立性闸门 Q1–Q5**。
4. 只有通过审查的才会写入 canonical SQLite 并进入 Export。
5. **你不得**自己写入 canonical —— 那是 ThreeC Agent 的**独有权限**。

★ **角色分离是硬规则**：产出者与审查者**不得**是同一个执行者。
所以请把「我认为它成立」的理由写足，但**不要**代替审查下结论。

---

*Research Agent Prompt · R02-03 · 签发 2026-10-09 · 依据 `HISTORICAL_UNIVERSE_R02_TASK_MANIFEST_v0_1.json`*
