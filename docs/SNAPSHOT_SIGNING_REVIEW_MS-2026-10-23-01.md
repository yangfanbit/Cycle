# 签发审阅材料 · `MS-2026-10-23-01`（DRAFT）

> | 项 | 值 |
> |---|---|
> | 审阅对象 | `research/current/market_snapshots/snapshots/MS-2026-10-23-01.json`（**status = DRAFT**） |
> | 对照基线 | `MS-2026-10-13-01`（当前唯一 **CANONICAL**） |
> | 依据 HEAD | `61359e0`（2026-10-25） |
> | 材料性质 | **独立审阅材料** —— 不是批准、不是签发、不替代治理 C-4 的人工决定 |
> | 编写方式 | 全部数字由脚本从产物实测（命令见 §11），未手工抄录 |
>
> ★★ **本文件不复制 `MS-2026-10-13-01` 的审阅结论。** 上一份快照的批准只对它自己有效；
> 本次审阅重新核对每一项，并对「上一份 CANONICAL 本身存在的瑕疵」单列（§9.3）。

---

## 0. 一句话结论

**结构与 PIT 校验全部通过、输入全部按快照 ID 落盘、`--check` 逐字节可复现 → 具备签发条件；
但有 1 项会影响结论的保留意见（`risk_appetite` 缺「反向信号检查」记录）与 4 项非阻塞瑕疵，
建议由人工在签发前决定「先补 / 接受并留痕」。**

---

## 1. 与 `MS-2026-10-13-01` 的实质差异

### 1.1 元信息

| 字段 | 10-13（CANONICAL） | 10-23（DRAFT） | 说明 |
|---|---|---|---|
| `snapshot_date` | 2026-10-13 | **2026-10-23** | 最后一个完整交易日（10-24 为周六） |
| `status` | CANONICAL | **DRAFT** | 本轮**未**执行 `--canonical` |
| `timestamp` | `2026-10-14T11:28:32+00:00` | `2026-10-24T20:30:00+08:00` | 时区表示不同（UTC vs +08:00） |
| `provenance.reviewed_by` / `reviewed_at` | `yangfan` / `2026-10-14T11:28:32+00:00` | **`null` / `null`** | 未评审 —— 与 DRAFT 状态一致 |
| `provenance.research_round` | `ThreeC 1.1 Phase 1.2` | `… · Round 2026-10-23（月度刷新）` | — |
| `provenance.supersedes` | `MS-2026-10-12-01` | **`null`** | 未建立替代关系（未签发） |
| `provenance.rule_set_version` | `structural-analogy-ruleset-v0.3` | **同** | 冻结规则未变 |
| `market_snapshot_version` | `0.3` | **`0.3`** | 契约未变 |

### 1.2 内容量

| 段 | 10-13 | 10-23 | 差异 |
|---|---|---|---|
| `observations` | 13 | **25** | **+12**（旧 13 条逐字段未变，见 §2） |
| `research_objects` | 6 | 6 | 同一批 `object_id`，`evidence_sequence` 共 **+12** 条（见 §3） |
| `historical_candidates` | 534 | 534 | **逐字段完全一致**（见 §4） |
| `market_regime` 四维 | DOWN / NORMAL / STABLE / NEUTRAL | DOWN / NORMAL / **UNKNOWN** / **RISK_OFF** | 2 维变化（见 §5–§6） |
| `research_context` | 5 段 | 5 段 | 重写（新增行情/研究记录日期与 5 条 known_limitations） |

**实质变化 = ① 12 条新观察；② 研究对象证据序列 +12 条（阶段全部未改）；③ 2 个 regime 维度改档。
历史候选、冻结 SA、契约版本、对象清单都没有变化。**

### 1.3 可追溯性差异（重要，对签发有利）

| 输入 | 10-13 实际来源 | 10-23 实际来源 |
|---|---|---|
| `market_regime` | `market_regime/MS-2026-10-06-10.json`（该文件 `snapshot_date = 2026-10-06`，证据最晚 `source_date = 2026-09-30`） | `market_regime/MS-2026-10-23-01.json`（`snapshot_date = 2026-10-23`） |
| `observations` | `observations/MS-2026-10-06-10.json` | `observations/MS-2026-10-23-01.json` |
| `research_context` | **等于 `context/MS-2026-09-15-01.json` 的 5 个字段**（9 月 15 日的上下文） | `context/MS-2026-10-23-01.json`（与快照逐字段一致，仅多两个信封字段 `contract` / `context_version`） |
| 是否存在同名输入文件 | **三份全部 MISSING** | **三份全部存在** |

> ★ 也就是说：**当前 CANONICAL 的 `market_regime` 证据比它的 `snapshot_date` 早 13 天，
> `research_context` 是 9-15 的；而新 DRAFT 的三份输入都按快照 ID 落盘且日期对齐。**
> 新快照在「可复现 / 可追溯」这一维度上**强于**现有 CANONICAL。这一点必须写进签发说明，
> 否则会被误读成「新快照在追赶一个更严谨的基线」。

---

## 2. 新增的 12 条 observations，以及旧观察是否被动过

### 2.1 append-only 实测

```
旧观察 13 条 · 新观察 25 条
被删除的旧 observation_id：[]            ← 0 条
逐字段完全一致（含 source_tier / direction / evidence_strength / temporal_relation / linked_object_id）：13 / 13
被改写的旧 observation_id：[]            ← 0 条
```

> 校验器的「跨快照 append-only 自检」亦 PASS（27 个 observation_id）。
> 字段集合也一致：新旧观察的 key 集合无差异；`linked_object_id` 仍是**可选**字段（8 条旧观察有、5 条旧观察没有，与本轮无关）。

### 2.2 新增 12 条逐项

| # | observation_id | date | type | tier | strength | direction | 关联对象 | 事实（截断） |
|---|---|---|---|---|---|---|---|---|
| 1 | `OBS-2026-10-001` | 2026-10-20 | POLICY | **T1** | STRONG | SUPPORTIVE | BCI-MEDTECH | 药监局批准诺尔康「听觉脑干植入体」创新产品注册（原文未称「脑机接口」） |
| 2 | `OBS-2026-10-002` | 2026-10-21 | INDUSTRY | T3 | MEDIUM | SUPPORTIVE | BCI-MEDTECH | 大湾区脑机接口产业创新大会：成立创新联合体、启动区域标准体系 |
| 3 | `OBS-2026-10-003` | 2026-10-22 | POLICY | T3 | STRONG | SUPPORTIVE | AUTO-SMARTDRIVE | 工信部：L3 级自动驾驶产品第二批准入试点正在进行 |
| 4 | `OBS-2026-10-004` | **2026-10-12** | INDUSTRY | T3 | MEDIUM | SUPPORTIVE | COMPUTE-POWER | 内蒙古能源局：和林格尔绿电使用比例 >85% |
| 5 | `OBS-2026-10-005` | 2026-10-23 | INDUSTRY | T3 | STRONG | SUPPORTIVE | EMBODIED-AI | 商务部：前三季度具身智能机器人销售额 +22.6% |
| 6 | `OBS-2026-10-006` | 2026-10-16 | INDUSTRY | T3 | MEDIUM | NEUTRAL | EMBODIED-AI | 上半年全球人形机器人出货近 2.5 万台（+432.1%） |
| 7 | `OBS-2026-10-007` | 2026-10-23 | INDUSTRY | T2 | MEDIUM | SUPPORTIVE | OPTICAL-LINK | 光通信产业链公司回应：生产经营正常、订单交付有序、1.6T 放量 |
| 8 | `OBS-2026-10-008` | 2026-10-10 | INDUSTRY | T3 | STRONG | SUPPORTIVE | OFFSHORE-WIND | 龙源射阳 100 万千瓦海风一期首批机组并网 |
| 9 | `OBS-2026-10-009` | 2026-10-20 | POLICY | **T1** | MEDIUM | SUPPORTIVE | OFFSHORE-WIND | 广东生态环境厅：明阳巴斯夫徐闻东三示范项目环评拟批准公示 |
| 10 | `OBS-2026-10-010` | 2026-10-22 | MARKET | T2 | MEDIUM | **NEGATIVE** | —（市场层） | 沪深300 -1.84%，全市场上涨家数占比 9.6% |
| 11 | `OBS-2026-10-011` | 2026-10-23 | MARKET | T2 | MEDIUM | NEUTRAL | —（市场层） | 沪深300 +1.71%，上涨家数占比 83.2%，涨停 83 家 |
| 12 | `OBS-2026-10-012` | 2026-10-23 | MARKET | T2 | STRONG | **NEGATIVE** | —（市场层） | 20 交易日：沪深300 -7.96%、深证成指 -12.95%、创业板指 -18.62% |

分布：T1 5 / T2 4 / T3 16；STRONG 10 / MEDIUM 15；SUPPORTIVE 16 / NEGATIVE 5 / NEUTRAL 4。

### 2.3 PIT

- 全部 25 条 `temporal_relation = BEFORE_SNAPSHOT`；`max(date) = 2026-10-23` = `snapshot_date`，**无一条越界**。
- ★ **1 条属事后补录**：`OBS-2026-10-004` 日期 **2026-10-12**，早于上一快照日 10-13，但本轮才登记。
  这**合法**（append-only 允许补录历史事实），但**不得**据此声称「10-13 当时已知」。
  同理，研究对象证据里也有 2 条日期早于 10-13 的追加项（§3）。签发说明里应保留这句限定。
- 发布晚于 10-23 的材料已主动排除（例：某央企 10-23 采购公告只能经 10-24 报道核实 → 未纳入）。

---

## 3. 6 个 research objects 的 `evidence_sequence` 变化

`object_id` 集合完全相同；`declared_phase` **6 个全部未变**；`phase_source` 全为 `RESEARCH_DECLARED`；
`resolution_state` 全为 `RESOLVED`；除 `evidence_sequence` 外**无其他字段变化**。

| object_id | declared_phase | 序列 | 追加项（date / type） | 旧序列是新序列的严格前缀 |
|---|---|---|---|---|
| `CC-2026-AUTO-SMARTDRIVE` | THEME_FORMING | 6 → 7 | `2026-10-22 / policy` | ✅ |
| `CC-2026-BCI-MEDTECH` | THEME_FORMING | 7 → 9 | `2026-10-20 / policy`、`2026-10-21 / industry` | ✅ |
| `CC-2026-COMPUTE-POWER` | BROAD_CONFIRMATION | 10 → 11 | `2026-10-12 / industry` | ✅ |
| `CC-2026-EMBODIED-AI` | EXPANSION | 7 → 9 | `2026-10-16 / industry`、`2026-10-23 / industry` | ✅ |
| `CC-2026-OFFSHORE-WIND` | THEME_FORMING | 6 → 8 | `2026-10-10 / industry`、`2026-10-20 / policy` | ✅ |
| `CC-2026-OPTICAL-LINK` | EXPANSION | 7 → 9 | `2026-10-22 / market`、`2026-10-23 / company` | ✅ |

合计 **+12 条**，与 §2 的 12 条新观察一一对应（同一批事实）。

### 3.1 ★ 必须知道的限制：`stage_review` 没有进入快照

`research/current/current_candidates.json` 本轮新增了 `stage_review`
（`status = REVIEWED_MAINTAINED` + 逐对象维持理由），但 `project_cc_to_objects_v0_1.py` 是**白名单投影**，
`research_objects` 只有 11 个字段，**不含 `stage_review`**。

后果：**只看快照的人无法区分「本轮重新检查证据后决定维持阶段」与「沿用旧判断、尚未重新评估」。**
`research_context.known_limitations` 第 3 条写的是「沿用 2026-10-08 轮判定……故未强改」，
与 `current_candidates.json` 里的 `REVIEWED_MAINTAINED` 措辞并不完全一致（前者听起来像「没重查」）。

→ 这是**待人工决定事项**（§10-④）：接受该限制并在签发说明中写明，还是先扩投影器（属代码变更，本轮不做）。

---

## 4. `historical_candidates` 与冻结 SA

| 检查 | 结果 |
|---|---|
| 条数 | 534 → **534** |
| 逐字段比较（`sort_keys` 规范化后整段比对） | **完全一致（True）** —— 不是「数量相同」，是内容相同 |
| `candidates_source.artifact` | `research/research/reports/structural_analogy_explanations_v0_13.json`（未变） |
| `candidates_source.artifact_version` | `0.13`（未变） |
| `candidates_source.rule_set_version` | `structural-analogy-ruleset-v0.3`（未变） |
| 校验项 | `V8`（534 条轻量索引，无多余字段）PASS；`V8b`（回指校验）PASS |

**结论：本轮未重跑、未改规则、未改结论；SA 侧与 10-13 等价。**

---

## 5. 四维市场状态的前后差异与证据

| 维度 | 10-13 | 10-23 | 变化 | 依据（10-23） |
|---|---|---|---|---|
| `broad_index_state` | DOWN | **DOWN** | 档位未变，**幅度显著加深** | `MR-EV-01`：沪深300 `4105.329 / 4460.156 − 1 = -7.96%`（20 个交易日，2026-09-17→10-23），跌破 -5% 档 |
| `breadth_state` | NORMAL | **NORMAL** | 档位未变，**证据质量提升** | `MR-EV-02`：近 4 自然周周均上涨家数占比 `42.6 / 45.9 / 32.2 / 48.2%` → 均值 **42.23%**（40–60% 档） |
| `liquidity_state` | STABLE | **UNKNOWN** | **证据不可得**（不是市场变化，见 §6） | `MR-EV-05`：取数失败记录 |
| `risk_appetite_state` | NEUTRAL | **RISK_OFF** | **档位改变**（见 §5.2） | `MR-EV-03` 高β跑输 10.67pp + `MR-EV-04` 涨停家数 -15.2% |

### 5.1 两个「档位未变」维度的证据其实换了

- **broad**：10-13 是 `-5.50%`（4357.62/4611.44，窗口 09-01→09-30，来源「东方财富 EOD 前复权」T2）；
  10-23 是 `-7.96%`（本地 `history_scan.db` CSI300，窗口 09-17→10-23，T2）。
  **同一档位、不同窗口、不同数据源**。档位一致不等于「市场没变」——实际跌幅扩大了 2.46pp。
- **breadth**：10-13 用的是 **4 个离散交易日的媒体报道**（T3，且自注「★ 不足规则要求的近 4 周周均」）；
  10-23 是 **4 个自然周、每日 ≥3,000 只可比样本**的实测均值（T2）。
  → 新证据**更强**，但两次的 NORMAL 不是同一个测量。

### 5.2 `risk_appetite` 从 NEUTRAL 到 RISK_OFF：为什么会变，以及一处需要回答的问题

**10-13 判 NEUTRAL 的理由（原文 `MR-EV-07`）**：存在**方向相反**的信号 ——
低 β 防御（银行股创历史新高、创业板跌超 8%）指向收缩，但同期题材投机仍活跃
（CRO 近岸蛋白 +133%、PCB 澳弘电子 +88%、黄酒会稽山 +93%）→ 按「信号冲突 → NEUTRAL」。

**10-23 判 RISK_OFF 的理由**：两个**可计算**信号同向且无相反信号记录 ——
① 高β（创业板指 -18.62%）相对低β（沪深300 -7.96%）**低 10.67pp**；
② 近 4 周日均涨停 **52.1** 家 vs 前 4 周 **61.5** 家（**-15.2%**）。

> ⚠️ **保留意见（唯一会影响结论的一项）**：10-23 的 regime 文件**没有记录「是否检查过反向信号」**。
> 10-13 之所以是 NEUTRAL，正是因为有 MR-EV-07 这类反例；本轮没有对应的「已检查、未发现」记录。
> 在签发前，建议补一句显式说明（检查了哪些方向、结论如何），否则无法排除
> 「因为没找反例才得到 RISK_OFF」。**这不需要改数，只需要在 `MR-EV-03/04` 或 `unknown_notes`
> 里留一句可核验的检查记录。**

---

## 6. `liquidity_state`：STABLE → UNKNOWN 的真实原因

### 6.1 结论

> **这是「成交额证据不可得」，不是「流动性已经恶化」。**
> 不得把 UNKNOWN 读成 CONTRACTING，也不得读成「流动性转差」。

### 6.2 证据

`MR-EV-05` 记录了三路取数失败（`source_date = 2026-10-23`）：

| 尝试 | 结果 |
|---|---|
| 东方财富 `push2his` EOD 接口 | 空响应（HTTP 000），直连与代理均失败 |
| 网易财经 `chddata` 历史接口 | HTTP 502 |
| 本地 `market_data.db` | `market_daily.amount` 对 `SH000300` **全为 NULL** |
| 本地 `history_scan.db` | 只有 `volume`，**无 `amount`** |

按 `MARKET_REGIME_AI_INTERFACE_v0.1` §2.7 第 3/4 条：**不得**用成交量换算、**不得**用单日成交额
（腾讯/新浪只提供当日快照）替代 20/60 日均值口径，也**不得**缩短窗口凑档位 → 记 `UNKNOWN`，
并在 `unknown_notes.liquidity_state` 里写明原因。校验项 `R7`（UNKNOWN 原因）PASS。

### 6.3 一个必须一起说的背景：10-13 的 STABLE 本身是降级口径

- 10-13 的 `MR-EV-03` 自注：`窗口 2026-08-03 ~ 2026-09-30（42 个交易日；★ 不足规则要求的 60 日）`，
  结论 `近20日均值 18039 亿 vs 窗口均值 20269 亿 → -11.0%`，未达 CONTRACTING 门槛 → STABLE。
- 数据源为「东方财富 EOD 日线」——**正是本轮已失效的那条源**。

> 所以真实的变化链是：**「降级口径的 STABLE」→「源不可用 → 诚实的 UNKNOWN」**，
> 而不是「市场从稳定转为恶化」。签发说明里应这样表述，避免读者误读。

---

## 7. 新 `market_regime` 的证据、来源质量、PIT 与未解决限制

### 7.1 五条证据

| id | 维度 | 指标 | 值 | 窗口 | tier | source_date |
|---|---|---|---|---|---|---|
| `MR-EV-01` | broad_index | 沪深300 20 日涨跌 | `4105.329/4460.156−1 = -7.96%` | 09-17→10-23（20 交易日） | T2 | 2026-10-23 |
| `MR-EV-02` | breadth | 上涨家数占比 4 周均值 | `42.6/45.9/32.2/48.2% → 42.23%` | 第 40–43 周（≥3,000 只/日） | T2 | 2026-10-23 |
| `MR-EV-03` | risk_appetite | 高β−低β 20 日相对 | `-18.62% − (-7.96%) = -10.67pp` | 09-17→10-23 | T2 | 2026-10-23 |
| `MR-EV-04` | risk_appetite | 涨停家数 周均环比 | `52.1 vs 61.5 家/日 = -15.2%` | 第 40–43 周 vs 36–39 周 | T2 | 2026-10-23 |
| `MR-EV-05` | liquidity | 成交额 20/60 日 | **不可得 → UNKNOWN** | 07-24→10-23（未取到） | T2* | 2026-10-23 |

`evidence_refs` = 01–05，**全部可解析**（R4 PASS）；**全部 `source_date ≤ snapshot_date`**（R5 PASS）；
维度—证据配对合法（R6）；`risk_appetite` 有 **2 个独立信号**（R8）；红线词扫描通过（R9）。

### 7.2 来源质量

- 4 条来自**本地 EOD 序列** `history_scan.db`（5,576 只个股日收盘 / CSI300 / SZSE / CHINEXT），
  按固定公式复算，属**可重复但非交易所直连**的口径 —— `research_context.known_limitations` 第 2 条已声明。
- `beta_note` 明确写了「不得用单一指数代表全市场」，并显式排除 2 个单日极值
  （10-22 上涨占比 9.6%、10-23 反弹 83.2% / 涨停 83 家），声明「单日数据不用于任何维度定档」。
  **这是本轮做得比 10-13 更严谨的地方。**

### 7.3 未解决限制（签发时应一并写明）

| # | 限制 | 影响 |
|---|---|---|
| L1 | `liquidity_state` 无可用成交额序列 | 四维只有三维可判定 |
| L2 | 行情序列来自本地自建库（`history_scan.db`，**1.3GB 未入库**） | 外部读者**无法独立复算**这四个数；只能复核公式与输入文件 |
| L3 | `risk_appetite` 缺「反向信号检查」记录 | 见 §5.2 保留意见 |
| L4 | `MR-EV-05` 是「取数失败记录」，却标了 `source_tier: "T2"` | 元数据小瑕疵：失败记录不应占一个来源层级，建议改 `N/A`（不改数） |
| L5 | `market_regime.generated_at = 2026-10-24T20:10:00`（**无时区**） | 与快照 `timestamp` 的 `+08:00` 表示不一致，跨时区读者可能误解 |
| L6 | `market_data.db` 仍截至 **2026-10-20**，与 `history_scan.db` 的 10-23 **不同** | 两库日期不得互相冒充；本快照只用后者 |
| L7 | breadth 未说明是否剔除 ST / 停牌（仅写「每日可比样本 ≥3,000 只」） | 口径可复核性略弱 |

---

## 8. `provenance.source_commit` 为空的可追溯性影响

| 项 | 10-13 | 10-23 |
|---|---|---|
| `provenance.source_commit` | `""` | `""` |

**影响**：
1. 快照**无法绑定到生成它的那棵树** —— 不能证明它是用哪一版 `current_candidates.json` /
   SA 解释产物 / observations 输入生成的。
2. 快照提交进 git 之后，`git log` 只能证明「这个文件何时被提交」，**不能**证明「生成时的源码状态」。
   若之后 `current_candidates.json` 再被刷新，`--check` 复现会失败，而读者无从判断差异来自数据还是代码。
3. 治理 C-4（版本替换）要求「留痕」；`reviewed_by/at` 能记录**谁批的**，
   `source_commit` 才能记录**批的是哪一版**。

**缓解（本轮已具备的）**：
- 三份输入**按快照 ID 落盘**且与快照内容逐字段一致（regime / observations 全等；context 仅差两个信封字段）；
- `--check` **逐字节一致**（固定 `--timestamp` 后复现成功）；
- `historical_candidates` 通过 `candidates_source` **回指**带版本号的 SA artifact（`0.13` + `rule_set v0.3`）；
- 观测/对象都带日期，PIT 可核。

**建议（不改产物，交人工决定）**：
生成器**已支持** `--source-commit`（`build_market_snapshot_v0_1.py` 里 `args.source_commit`），
只是本轮未传。若决定补，需**重新生成**该 DRAFT（本轮任务禁止），或用一次专门的「元数据补录」轮次处理。
**注意：10-13 CANONICAL 同样是空 —— 这不是新回归，而是既有治理缺口，签发时应作为待办记录。**

---

## 9. 校验结果与 8 条 WARN 的具体归属

### 9.1 总览

```
validate_market_snapshot_v0_1.py（全目录，只读）
结果: 370 通过 / 8 警告 / 0 失败
```

`build_market_snapshot_v0_1.py … --out <现有快照> --check`
→ `PASS  --check 逐字节一致（可复现）`（固定 `--timestamp 2026-10-24T20:30:00+08:00`）

### 9.2 8 条 WARN 逐条归属 —— 全部是**历史遗留**，与本快照无关

| WARN | 文件 | 内容 |
|---|---|---|
| 1–8 | `observations/MS-2026-10-06-01.json` … `observations/MS-2026-10-06-08.json` | `O7`：该文件**全部证据均为 T3**（财经媒体转述），建议补 T1/T2 一手来源 |

- 这 8 个文件是 **10-06 系列快照**的观察输入（对应 `MS-2026-10-06-01`…`-08`，均 `ARCHIVED`），
  **既不是 10-13 的输入，也不是 10-23 的输入**。
- **`MS-2026-10-23-01` 及其三份输入：0 WARN。**
- 处置建议：**不修**（它们是归档快照的历史输入，改了就破坏 append-only）。这不是签发阻塞项。

### 9.3 与新快照相关的 PASS 明细（节选，均为实测输出）

```
snapshots/MS-2026-10-23-01.json · V1 contract / version 0.3 / snapshot_id 命名空间   PASS
snapshots/MS-2026-10-23-01.json · V2 status = DRAFT                                PASS
snapshots/MS-2026-10-23-01.json · V3 snapshot_date = 2026-10-23                    PASS
snapshots/MS-2026-10-23-01.json · V5 market_regime 四维 + beta_note 齐备            PASS
snapshots/MS-2026-10-23-01.json · V6 observations 结构校验（25 条）                  PASS
snapshots/MS-2026-10-23-01.json · V7 research_objects 校验（6 条）                  PASS
snapshots/MS-2026-10-23-01.json · V8 historical_candidates 轻量索引（534 条，无多余字段） PASS
snapshots/MS-2026-10-23-01.json · V8b candidates_source 回指校验                    PASS
snapshots/MS-2026-10-23-01.json · L1 观察→对象关联（17 条已关联）                    PASS
market_regime/MS-2026-10-23-01.json · R1/R2/R3/R4/R5/R6/R7/R8/R9/R10               PASS
context/MS-2026-10-23-01.json · C1/C2                                              PASS
observations/MS-2026-10-23-01.json · O1/O3/O4/O5（25 条）                           PASS
跨快照 append-only 自检（27 个 observation_id）                                      PASS
index.json · I5 索引与目录一致（15 份）/ I6 CANONICAL 唯一（MS-2026-10-13-01）        PASS
```

### 9.4 索引状态（只读核对，未修改）

`index.json` 共 15 条：`MS-2026-10-13-01` = **CANONICAL**（唯一）；`MS-2026-10-23-01` = **DRAFT**；
其余 13 份 `ARCHIVED` 或 `DRAFT`（`MS-2026-09-15-01` 为 DRAFT）。
★ `index.json` 条目**不含 `supersedes` 字段** —— 版本链只存在于快照 `provenance` 里，
签发时若要查「谁替代谁」，必须读快照本体，不能只读索引。

---

## 10. 签发建议、保留意见、必须由人工决定的事项

### 10.1 建议

**技术条件已具备**：结构 / PIT / SA 回指 / 索引 / 复现性全部通过，输入可追溯性**优于**现有 CANONICAL。

**建议路径（二选一，均由人工决定）**：

- **路径 A（推荐）**：先在 DRAFT 上补两条**不改数**的记录，再签发 ——
  ① `risk_appetite` 的反向信号检查说明（§5.2）；② `MR-EV-05` 的 `source_tier` 改为 `N/A`（§7.3 L4）。
  两者都只动 regime 输入文件的文字/元数据，需要重建快照（`--check` 会随之更新）。
- **路径 B**：接受现状直接签发，并在签发说明中把 §5.2 / §7.3 / §8 的限制**原文写进** `review` 留痕。

> 若选 B，**必须**在签发说明里明确三句：① liquidity UNKNOWN ≠ 流动性恶化；
> ② risk_appetite 缺反向信号检查记录；③ `source_commit` 为空、版本链仅存于快照本体。

### 10.2 保留意见（按严重度）

| # | 保留意见 | 严重度 | 是否阻塞 |
|---|---|---|---|
| 1 | `risk_appetite` 从 NEUTRAL 改 RISK_OFF，但**没有记录反向信号检查**（10-13 正是因为反例才 NEUTRAL） | **高** | 建议不阻塞，但必须留痕 |
| 2 | `liquidity_state = UNKNOWN`：四维只有三维可判定 | 中 | 否（`UNKNOWN` 是契约合法状态，`R7` PASS） |
| 3 | `provenance.source_commit` 为空 | 中 | 否（10-13 同样为空，属既有缺口） |
| 4 | `stage_review`（重查后维持）未进入快照，读者无法区分「重查维持 / 沿用未查」 | 中 | 否（需人工决定是否扩投影器） |
| 5 | `MR-EV-05` 以 T2 标注一条取数失败记录 | 低 | 否 |
| 6 | `generated_at` 无时区；`timestamp` 与快照用不同时区表示 | 低 | 否 |
| 7 | 行情序列在未入库的 1.3GB 本地库，外部无法独立复算 | 中 | 否（`known_limitations` 已声明） |

### 10.3 必须由人工决定（治理 C-4 / C-1）

| # | 决定事项 | 说明 |
|---|---|---|
| ① | **是否签发**，以及 `reviewer` 署名与 `decided_at` | 只能由人执行 `--canonical --reviewer <name> --supersedes MS-2026-10-13-01`；**本轮未执行** |
| ② | 走路径 A（先补两条记录）还是路径 B（接受并留痕） | 见 §10.1 |
| ③ | 是否接受 `liquidity_state = UNKNOWN` 作为 CANONICAL 快照的状态 | 治理 §D：`UNKNOWN` 合法，不得当 `NO` |
| ④ | 是否要求先补 `source_commit`（需重生成 DRAFT） | 生成器已支持 `--source-commit` |
| ⑤ | 是否扩展 `project_cc_to_objects` 白名单以携带 `stage_review` | 属代码变更，本轮**未做** |
| ⑥ | 是否同时归档 `MS-2026-10-13-01` | 签发时由生成器自动置 `ARCHIVED`；**本轮未归档** |
| ⑦ | 是否接受「10-13 的 regime / context 输入滞后」这一既有瑕疵不被追溯修正 | 见 §1.3；修它需要重生成 CANONICAL，风险更大 |
| ⑧ | 历史候选（C-1 结构确认）是否沿用 10-13 的取舍 | 本轮 534 条逐字段一致，未重跑 SA |

### 10.4 本轮**没有**做的事（边界声明）

- ❌ 未运行 `--canonical`；未改任何 `status`；未改 `index.json`；未改 `supersedes` 链
- ❌ 未归档 `MS-2026-10-13-01`
- ❌ 未重新生成快照 / 历史角色 / 季节性产物（只读校验）
- ❌ 未改 Research DB / schema / 冻结 SA 规则 / 角色支持等级
- ❌ 未把 `liquidity_state` 改成任何其他状态
- ❌ 未实现「负面点名」新口径

---

## 11. 本次核对所用命令（可复跑）

```bash
S=research/current/market_snapshots
PY=~/.workbuddy-ai/binaries/python/envs/default/bin/python

# 全目录校验（只读）
$PY $S/scripts/validate_market_snapshot_v0_1.py

# 复现性（只读；固定 timestamp）
$PY $S/scripts/build_market_snapshot_v0_1.py \
  --snapshot-date 2026-10-23 --snapshot-id MS-2026-10-23-01 \
  --timestamp "2026-10-24T20:30:00+08:00" \
  --regime $S/market_regime/MS-2026-10-23-01.json \
  --context $S/context/MS-2026-10-23-01.json \
  --objects .tmp/objects-1023.json \
  --observations $S/observations/MS-2026-10-23-01.json \
  --candidates .tmp/candidates-1023.json \
  --research-round "ThreeC 1.1 Phase 1.2 · Round 2026-10-23（月度刷新）" \
  --out $S/snapshots/MS-2026-10-23-01.json --check
```

其余差异统计（append-only、四维对比、输入一致性、WARN 归属）均由一次性只读 Python 片段对上述 4 个 JSON
逐字段比对得出，未写入任何文件。

---

*审阅材料结束 · `MS-2026-10-23-01` 仍为 DRAFT · 未签发、未归档 · 2026-10-25*
