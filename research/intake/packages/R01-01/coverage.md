# R01-01 高端装备 / 机器人 — 研究覆盖说明（Coverage）

本文件为 `R01-01` 研究包的可读性说明，记录**本任务实际研究了什么、以什么方法研究、覆盖到哪、哪里没覆盖到**。它不是 Campaign 清单，不是产出统计，也不是 ThreeC 的最终结论。所有结构化内容以 `manifest.json` / `candidates.json` / `evidence.json` / `sources.json` / `securities.json` / `exclusions.json` / `conflicts.json` / `research_questions.json` / `quality_summary.json` 为准。

---

## 1. 任务与范围

| 项 | 内容 |
| --- | --- |
| 任务号 | `R01-01` |
| 方向 | 高端装备 / 机器人 |
| 覆盖年份 | 2015–2025 |
| Priority A（必须独立交付） | 2018–2025 |
| Priority B（允许大量 INSUFFICIENT） | 2015–2017 |
| 协议版本 | Historical Universe Intake Protocol v0.1 |
| 研究轮次 | `R01` |
| 来源 commit | `2153f6d83b7481300696ab73d792e9e53aa31a07` |

**纳入范围**：工业自动化与工控、工业机器人本体与核心零部件（减速器/伺服/控制器）、人形机器人（含具身智能叙事）、工程机械（挖掘机/起重机/混凝土机械及液压件）、轨道交通装备，以及支撑上述方向的设备更新与制造业资本开支周期。

**排除范围**：消费级电子与家电（R01-04）、纯军工订单驱动的装备（R01-06）、汽车整车/零部件与智驾 Robotaxi（已有 family「汽车」）、半导体设备与材料（R01-02）、2015 年前的装备行情、大宗商品与原材料价格周期本身（R01-03）。

---

## 2. 研究方法

本包按任务要求，从**产业侧的时间 → 事件 → 产业机制 → 主题 → 生命周期**构建，而非从「股票上涨 → 找一个故事解释」倒推。

### 2.1 先构建候选宇宙，再逐项验证

从**机制轴**出发列出可能的历史机会结构，而非从股票记忆出发：

| 机制轴 | 机制内容 | 对应候选 | 结果 |
| --- | --- | --- | --- |
| M1 | 设备更新周期 + 基建/地产投资 + 环保排放标准淘汰 | `R01-HIEQ-001` 工程机械 | PROVISIONAL / high |
| M2 | 制造业资本开支收缩 + 下游（汽车/电子）需求下滑 | `R01-HIEQ-002` 工业机器人下行 | PROVISIONAL / high |
| M3 | 疫情后资本开支回补 + 机器换人渗透率提升 | `R01-HIEQ-003` 工业自动化复苏 | PROVISIONAL / high |
| M4a | 产业政策驱动（十七部门联合发文，产业处于低位） | `R01-HIEQ-004` 「机器人+」政策 | PROVISIONAL / medium |
| M4b | 产业政策驱动（国务院行动方案 + 财政资金加码） | `R01-HIEQ-006` 大规模设备更新 | INSUFFICIENT / low |
| M5 | 技术突破 + AI 大模型外溢 + 产业叙事形成 | `R01-HIEQ-005` 人形机器人叙事形成 | PROVISIONAL / medium |
| M6 | 量产预期 + 国产产业链组织化 + 订单落地 | `R01-HIEQ-007` 量产与国产加速 | INSUFFICIENT / low |
| M7 | 单一买方（国铁集团）采购节奏 | 轨道交通装备 | 未形成结构，见 `X004` |
| M8 | 供需变化（供给端） | — | 本方向未找到以供给收缩为核心机制的对象 |

### 2.2 时间一致性（Point-in-Time）纪律

- 每条证据均标注 `temporal_relation`（contemporaneous / prior / subsequent / retrospective / unknown）与 `support_kind`。
- **所有 `subsequent` 与 `retrospective` 证据均填写 `point_in_time_note`**，显式声明其不得作为同期催化。
- 典型案例：埃斯顿 2022 年年报对行业周期的一手自述（`E015`）虽为一手披露，但属 hindsight，本包只用它界定「2020Q2→2021Q3 上行、2021-07 起下行」的分段锚点，不把它当作 2020–2021 行情中的催化。
- 日期精度严格区分：`EXACT_DATE` / `DATE_WINDOW` / `PHASE_WINDOW` / `UNKNOWN`。对无法收敛的锚点（如 `R01-HIEQ-005` 的 start、多个候选的 end）明确使用 `DATE_WINDOW` 或 `UNKNOWN`，不猜测具体日期。

### 2.3 证据独立性

- 用 `independence_group` 分组，**不同 group 才算独立证据**；同源转引计入同一 group 并标记 `same_origin: true`。
- 已标记同源的对：`E005/E006`、`E015/E016`、`E022/E023`、`E024/E025`、`E033/E034`、`E007/E040/E041`、`E002/E038`。
- Tier 4 来源（`S033` 前元投资）显式标注为**线索性来源，不得单独作为独立证据**。

### 2.4 反证与偏差控制

- **Beta Contamination**：`E026` 作为独立的 `contradicting` 证据单列，记录 2023-08-29 为全市场普涨日（沪指 +1.20%、超 4700 只个股上涨），使当日机器人板块表现无法完全归因于主题；据此将 `R01-HIEQ-005` 置信度压在 medium 而非 high。
- **Survivorship Bias**：`securities.json` 中所有条目设置 `survivorship_aware: true`，并在 `point_in_time_note` 中区分 **Historical Leader Set（retrospective 认定）** 与 **Point-in-Time Basket（当时可观察）**。
- **Look-Ahead Bias**：所有回顾性来源（如 `S018` 2025-09-16 的产业进程复盘）明确标注 `retelling: true` 或 `temporal_relation: retrospective`，不使用其证明「当时投资者已采信」。

---

## 3. 覆盖情况逐候选

| 候选 | 对象 | 年份 | 状态 | 置信度 | 生命周期证据完整度 |
| --- | --- | --- | --- | --- | --- |
| `R01-HIEQ-001` | 工程机械景气周期 | 2021 | PROVISIONAL | high | 上行/峰值/回撤三段有据；2022 年后未知；start 为窗口 |
| `R01-HIEQ-002` | 工业机器人产量下行周期 | 2019 | PROVISIONAL | high | 起止月度明确（2018-09 / 2019-12）；background 段缺 |
| `R01-HIEQ-003` | 工业自动化复苏周期 | 2020 | PROVISIONAL | high | 启动有同期证据（统计局+券商月报）；峰值依赖事后年报自述 |
| `R01-HIEQ-004` | 「机器人+」政策驱动 | 2023 | PROVISIONAL | medium | 启动证据最强（一手政策+当日行情）；end 为 UNKNOWN |
| `R01-HIEQ-005` | 人形机器人叙事形成 | 2023 | PROVISIONAL | medium | 事件链清晰；start 依赖回顾来源；存在 Beta 污染 |
| `R01-HIEQ-006` | 大规模设备更新政策 | 2024 | INSUFFICIENT | low | 政策侧完整（3 份一手文件）；**市场侧为零** |
| `R01-HIEQ-007` | 量产预期与国产加速 | 2025 | INSUFFICIENT | low | 订单证据唯一且同期；**市场侧为零** |

**依候选类型的机制分布**：`industry_trend` 3 个（001/002/003）、`event_driven` 1 个（004）、`theme_campaign` 1 个（005）、`mixed` 2 个（006/007）。分类均为提案，最终由 ThreeC Agent 判定。

---

## 4. 明确未覆盖 / 覆盖不足

1. **Priority B（2015–2017）**：仅覆盖工程机械 2016-08 起热销段与 2017 年销量数据；2015 年装备方向完全未覆盖；缺 2015–2016 逐月序列与同期市场反应。→ `exclusion R01-HIEQ-X008`
2. **市场侧行情序列**（最关键缺口）：`R01-HIEQ-006`、`R01-HIEQ-007` 市场侧为零；`R01-HIEQ-005` 仅 2023-08-29 单日；`R01-HIEQ-004` 峰值仅双周报窗口末点。直接限制 Campaign Independence Gate Q1 的可验证性。
3. **2023 年 2–4 月板块行情**：导致 `R01-HIEQ-004` 的 end 为 UNKNOWN，且与 `R01-HIEQ-005` 的边界无法切分。
4. **2022 年后工程机械完整走势**：`R01-HIEQ-001` 的 2022-01 起阶段标为 UNKNOWN。
5. **机制中间变量**：制造业固定资产投资逐月序列、设备更新实际落地投资、人形机器人实际交付与收入确认数据均缺失。
6. **轨交装备 2019–2020 与 2024–2025 段**：未采集，故 `INSUFFICIENT_EVIDENCE` 带有采集不足的不确定性（`research_question R01-HIEQ-Q012`）。
7. **一手政策原文**：《人形机器人创新发展指导意见》未取得 MIIT 官网原始通知页 → 印发日期存在两个口径（`CF001`，KEEP_BOTH）。
8. **标的归属瑕疵**：2023-08-29 报道中「双飞股份」与「双环传动」无法确认是否同一标的（`CF005`，UNRESOLVED），已在 `SEC013` 的 note 中声明不用于该日行情证据。

---

## 5. 未决问题与跨任务事项

### 5.1 需 ThreeC Agent 裁决的未决结构问题（12 项，见 `research_questions.json`）

最关键的四项：

- **`Q001`**：「机器人」与「工业自动化」是否同一底层主题？`R01-HIEQ-002` 与 `003` 是否应合并为同一 ThemeCycle 的两个阶段？
- **`Q002`**：人形机器人 2023–2025 多轮行情是一个 Campaign（多 Phase）还是两个（`005` / `007`）？
- **`Q005`**：「高端装备」是否应作为独立 Macro Theme 建立根节点，还是分列为多个根节点？
- **`Q007`**：`R01-HIEQ-004`（政策段）与 `R01-HIEQ-005`（叙事段）的边界如何切分？

### 5.2 跨任务事项（6 项，见 `manifest.json` → `cross_task_notes`）

| ID | 类型 | 指向 | 内容 |
| --- | --- | --- | --- |
| `R01-HIEQ-CT001` | BOUNDARY | R01-02 | 半导体设备归 R01-02；本包未纳入任何半导体设备标的 |
| `R01-HIEQ-CT002` | BOUNDARY | R01-06 | 纯军工订单驱动的装备归 R01-06；本包所有候选机制均为制造/政策/叙事/技术 |
| `R01-HIEQ-CT003` | OVERLAP | — | 与 family「汽车」的 C-2024/2025-ROBOTAXI 在叙事与产业链上相邻，请 dedupe 时确认无底层对象重合 |
| `R01-HIEQ-CT004` | OVERLAP | — | 与 family「电力设备」的企业重叠（汇川技术等），请以该判定为准 |
| `R01-HIEQ-CT005` | HANDOFF | — | 人形机器人多轮行情是否同一 Campaign，须走 Research Model v1.0 §5 + Gate Q1–Q5 |
| `R01-HIEQ-CT006` | POSSIBLE_DUPLICATE | — | `R01-HIEQ-002` 与 `003` 可能属同一 ThemeCycle 的两个阶段 |

### 5.3 Macro Theme 提案（5 项）

本包**不自行确定** Macro Theme，仅提交 `macro_theme_proposals` 供 CMTR v1（`canonical-macro-theme-resolution-1`）解析：

- `R01-HIEQ-MT001` **高端装备** → `NEW_MACRO_CANDIDATE`（基线快照 §D 第 5 项确认 DB 中无该方向根节点）
- `R01-HIEQ-MT002` **机器人** → `SUB_THEME`（含「人形机器人」「具身智能」名称候选）
- `R01-HIEQ-MT003` **工业自动化** → `SUB_THEME`
- `R01-HIEQ-MT004` **工程机械** → `SUB_THEME`
- `R01-HIEQ-MT005` **轨道交通装备** → `SUB_THEME`（低证据强度，不构成 Campaign 主张）

---

## 6. 边界声明

- 本包**不代表 ThreeC 的最终结论**；所有候选均为 `candidate`，所有分类均为 `proposal`。
- 未注册任何 canonical ID（`C-*` / `RC-*` / `CC-*` / `TH-*` / `rule_*` / `summer_*`），未修改 SQLite / canonical DB / schema / 既有 Campaign / canonical Theme / exports / Structural Analogy Rule Set。
- 未创建任何排名、评分、概率、预测、胜率、目标价或买卖建议。
- 未运行 Time Observation，未运行 Structural Analogy（`STRUCTURAL_ANALOGY_CONTEXT.md` 明确该判定权不在 worker）。
- 交付到 `05_OUTPUT/` 后即停止，不进入 ThreeC 主仓库。
- 本任务**没有数量目标**：候选、证据、来源的条目数均为实际研究发现的结果，不构成产出 KPI。
