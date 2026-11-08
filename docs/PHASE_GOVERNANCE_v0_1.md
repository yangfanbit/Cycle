# 阶段判定来源与更新机制 v0.1（2026-11-07，v0.79）

> 触发：使用者质疑「高速光互联 扩散阶段 —— 扩散个屁，个股板块都跌成啥样了？」
> 本文件回答两件事：**当初阶段是怎么定的**，以及**后面怎么更新**。

---

## ★★ v0.80 勘误（2026-11-08）：展示层调整，治理结论不变

使用者 2026-11-08 决策：**默认页不再显示「产业机制阶段：扩散（研究侧声明 2026-10-23）」**。
理由：行情持续更新，一次停在某个研究轮次的静态旧声明，不会给当前市场提供有效信息。

本文件 §1–§5 的**治理结论全部继续有效**：两条轴正交 · `auto_change_phase=false` ·
市场层不参与定档 · 信号只提示人工复核 · 改阶段必须人工研究轮次并留痕。
变更的只有**信息所在的层级**：

| 层 | v0.79 | v0.80 |
|---|---|---|
| 默认页固定区 | 阶段声明 + 市场层实测并列 | **本周最新研究**（`weekly_research_v0_1.json`：本周新增可核事件 + 对应板块 + 前置观察窗口）+ 5/10/20 日超额**行情附注** |
| 内部评估视图 | 启发式排序 | 启发式排序 **+ 阶段声明时间线**（`phase_declaration_log_v0_1_view.json`） |
| 研究记录 | `current_candidates.json` 的 `stage_review`（**原地覆盖**） | 追加式声明日志，**只增不改**，带 PIT 锚点、结算字段分离 |

★★ §3 表格里「页面写『产业机制阶段：扩散（研究侧声明 2026-10-23）』」是
**v0.79 的历史落地记录**，不再描述当前默认页；**原句保留不改**，以免抹掉历史审计。

### 为什么是「日志」而不是「留个字段」

`stage_review` 是原地覆盖字段：下一次人工改档，10-23 那条声明连同 `basis` 里
「板块回调不作反向证据」的推理就只剩 git 历史，而 git 不是可查询的研究数据。
`phase_declaration_log_v0_1.json` 把它做成 append-only 记录：

- `declaration_id = PD-<candidate_id>-<declared_at>`；已有 id 内容不一致 → **拒绝、零修改**；
- 取代关系写在**新条**的 `supersedes`（新 → 旧），旧条**不含** `superseded_by`
  —— 否则就得回头改旧条，违反只增不改；
- `market_anchor.as_of = declared_at`，口径 `DECLARATION_DATE_AS_PIT_UPPER_BOUND`，
  是「当时可知信息的上界」，**不是行情数据日期**；
- 日志**不含任何结算 / 收益 / 命中字段**（`--check` 扫字段白名单），
  结算沿用 `candidate_formation_log` / `candidate_ledger` 的形成—结算分离模式，另立一轮重算。

### 回测纪律（不然「准确性」会变成 look-ahead）

1. 窗口起点必须**严格晚于声明日**；★ **不得**用 `theme_market.as_of`（事后行情）当锚点。
   声明当时可见的行情截止日未单独落盘 → 已在 `known_gaps` 里如实登记。
2. 现有 6 条同属 2026-10-23 一个研究轮次，**不是 6 个独立观察**；同轮同日共享同一批
   宏观信息与同一次判断，不能直接当 n=6 算比例。
3. 任何事后核对比例的表述必须按 `AGENTS.md` §3.1 写全口径七要素、分母只算完整可比较的
   声明、带 95% Wilson 区间，并声明**未校准**；本日志本身不产出该比例。

### 周更口径

行情推进 → `theme_market` / `frontier_board` / `weekly_research` 重算，
**声明日志必须逐字节不变**（`build_phase_declaration_log_v0_1.py --check` 每轮复核）。
`REVIEW_STALE` 与 `DIVERGENCE_INDUSTRY_VS_MARKET` 信号**保留** —— 它们是
「提醒人工去写下一条声明」的触发器；连信号一起删，声明会永远停在 10-23，回测样本也断了。

---

## 1 · 当初是怎么定的：两套阶段，不是一个

| | 研究侧声明 `attention_state` | 产品端推导 `currentPhaseInference` |
|---|---|---|
| 载体 | `research/current/current_candidates.json`（`generated_by: ai-offline`） | `src/data/timeline/currentPhaseInference.ts` |
| 判定者 | **人工离线研究轮次** | **透明规则引擎 R0–R8**（`R0_INSUFFICIENT_EVIDENCE` … `R8_UNCLASSIFIED`） |
| 输入 | `evidence[]` 产业层证据（政策 / 订单 / 交付 / 产能）+ `phase_evidence` 三维定性（narrative / breadth / information_marginal） | `PhaseEvidenceMatrix` 七维证据（叙事 / 政策 / 产业 / 市场 / 资金 / 广度 / 公司层）+ 新增信息边际 |
| `EXPANSION` 判据 | 10-23 Round 月度刷新**重查后维持**（`REVIEWED_MAINTAINED`） | `R4_EXPANSION_DIFFUSION`：`market ≥ PRESENT` 且 `breadth ≥ PRESENT` 且 `narrative ≥ PRESENT` |
| 硬性禁止 | — | **禁止 `涨幅 > X ⇒ EXPANSION`**；证据不足返回 `UNKNOWN` |
| UI 规则 | 与推导值并列 | `agreesWithDeclared = false` 时**必须并列显示**，不得静默取一 |

★ 两者语义都是**产业机制 / 研究注意力的阶段分类**，不是行情状态标签。

### 10-23 那次评审到底写了什么（`CC-2026-OPTICAL-LINK`）

`stage_review.basis` 原文要点：

- 10-22/23 新易盛、中际旭创、天孚通信、光迅科技回应「生产经营正常、订单交付有序、1.6T 持续放量」→ 产业层证据延续；
- 10-22 板块回调**无法与全市场普跌分离**（当日上涨家数占比 **9.6%**）→ 按既有口径记 `NEUTRAL`，**不作反向证据**；
- ★ 明写「若把该回调当作反向证据，产品侧规则引擎会把『市场关注』判为转弱并推出 `UNKNOWN` —— **本轮明确不采用该处理**」；
- `core_narrative` 明写「阶段判断**只依据产业层证据**」，`uncertainty_notes` 明写「市场层未参与定档」。

→ 所以「扩散」是**产业机制层的人工判定**，从来不是「行情在扩散」。但旧 UI 只显示一句「阶段：扩散阶段」，把两条轴压成了一条。

## 2 · 为什么没随行情更新

1. **不在派生链里**：`current_candidates.json` 是人工产物，仓库里**没有任何重算 `stage_review` / `phase_evidence` 的脚本**（只有校验器）。v0.76 全套刷新动了行情库与派生链，没碰这个文件 —— 是设计如此，不是漏跑。
2. **6 个主题全部停在 2026-10-23**：`last_updated` / `snapshot_date` / `reviewed_at` 都是 10-23，状态全是 `REVIEWED_MAINTAINED`。
3. **行情列是空的**：`candidate_digest` 里 6 张 `CURRENT_OBJECT` 卡 `current_performance = null`、`price_as_of = null`，只有 `research_days_old = 13` / `research_stale = true` —— 系统知道陈旧，却没给任何数字。
4. **实测脱节有多大**（10-23 → 11-05，raw 收盘）：

| 标的 | 10 交易日 | 20 交易日 |
|---|---|---|
| 新易盛 | — | **-50.96%** |
| 中际旭创 | — | -36.99% |
| 天孚通信 | — | -44.91% |
| 光迅科技 | — | -36.00% |
| **4 只等权** | **-25.62%**（相对沪深300 **-27.53 pp**） | **-42.22%**（相对 **-37.65 pp**） |
| 沪深300 | +0.20%（10-23→11-05） | — |

## 3 · v0.79 怎么改（不把行情当因果）

| 项 | 落地 |
|---|---|
| **语义分离** | 页面写「**产业机制阶段：扩散（研究侧声明 2026-10-23）**」，同一行并列「**市场层实测 as_of 2026-11-05**」；明确「两条轴方向不一致 ≠ 矛盾，市场层不参与定档」 |
| **关联标的** | **人工声明** 6 个主题的参照池（17 只），每条带 `basis`；脚本按 `series_id + name` **自动校验库内存在**，17/17 通过。★ 不是板块成分、不是选股清单、不参与阶段判定 |
| **周更刷新** | 算 5/10/20 交易日等权绝对收益与相对 CSI300 超额，写 `market_layer.as_of` / `price_as_of`；行情口径 `raw` 未复权、日历用 CSI300 自身序列 |
| **两个信号** | `REVIEW_STALE`（研究判定 >7 天，实测 **6/6** 命中）· `DIVERGENCE_INDUSTRY_VS_MARKET`（产业阶段属扩散/广泛确认/峰值 且 20 日相对超额 < -10 pp，实测 **1 个**：光互联 -37.65 pp） |
| **不自动改阶段** | `phase_governance.update_policy.auto_change_phase = false`（使用者 2026-11-07 决策 3）。信号只提示人工复核 |

产物：`research/current/theme_market_v0_1.json`
（`build_theme_market_v0_1.py --write/--check`，17 只标的校验 / 6 主题行情与信号）。

## 4 · 后面阶段怎么更新（SOP）

### 周更（自动，不改阶段）

```
python research/scripts/build_theme_market_v0_1.py --write    # 刷新行情 / 陈旧度 / 背离信号
python research/scripts/build_frontier_board_v0_1.py --write # 把摘要并入前瞻排程
```

只刷新 `market_layer` / `price_as_of` / `research_days_old` / `signals`；
`attention_state` / `stage_review` / `phase_evidence` **一字不改**。

### 人工研究轮次（唯一允许改阶段的路径）

触发条件：出现 `REVIEW_STALE` 或 `DIVERGENCE_INDUSTRY_VS_MARKET`，或新增可核产业证据。
改阶段时**必须同时**更新并记录：

1. `attention_state`、`phase_evidence`、`core_narrative`；
2. `stage_review` 的 `declared_phase` / `basis` / `reviewed_at` / `review_round` / `status`；
3. `last_updated`、`snapshot_date`；
4. `basis` 里逐条写清依据、来源 URL、日期，以及**市场层是否参与、为什么不参与**；
5. 升版留痕：`current_candidates.json` 属人工产物，改后 `--check` 与文档同步。

★ 若将来要让产品端推导阶段随周更重算，前提是先把「周更新增证据」接入
`PhaseEvidenceMatrix`；**不能**直接用涨跌幅改 `market` 维度（R4 引擎与评审 basis 都明确禁止）。

## 5 · 边界

- 阶段是**研究侧分类**，不是概率、不是预测、不是买卖信号；
- 关联标的池只作事实参照，不构成组合、不构成推荐；
- 行情用 `raw` 未复权（既有口径），除权日可能有跳变；
- 信号不参与有效性验收，也不改变任何历史统计产物。
