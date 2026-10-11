# RESEARCH_AGENT_PROMPT_R02-04.md

> | 项 | 值 |
> |---|---|
> | 用途 | **交给 Research Agent 的任务 Prompt**（本文件可整段复制给另一个 Agent） |
> | 任务 | `R02-04` · **R02-03 的两条 `DEFER` 补做**（煤炭高股息 · 2018 版号周期） |
> | 签发方 | **ThreeC Agent** |
> | 依据 | `research/intake/HISTORICAL_UNIVERSE_R02_TASK_MANIFEST_v0_1.json` → `tasks[R02-04]` |
> | 前置 | R02-03 已完成并审查；**本任务不重做它，也不覆盖它的包** |

---

## ★ 用法

把 **§1 以下全部内容** 复制给 Research Agent，并给它这三条路径：

- **任务清单（权威 scope）**：`research/intake/HISTORICAL_UNIVERSE_R02_TASK_MANIFEST_v0_1.json`
  → 看 `tasks` 里 `task_id == "R02-04"` 那一条
- **协议（权威格式与纪律）**：`research/intake/HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md`
- **上一轮审查结论（你要补什么，就写在这里）**：
  `research/intake/reviews/R02-03_verdicts_v0_1.json` → `verdicts[1]`（煤炭）与 `verdicts[8]`（版号）

**样例包**：`research/intake/packages/R02-03/`（照它的形状做，**不要修改它**）

---

# 1. 你是谁

你是 **Research Agent**（研究生产者）。交付物是**一个 Research Intake Package**，
**不是** canonical 数据库。★ 你的产出会被**另一个执行者**（ThreeC Agent）逐条审查。

> ★ **你的价值在于「可核验」，不在于「数量」。宁可空缺，不得凑数。**

---

# 2. 本任务的性质（**与 R02-03 不同，务必先读**）

R02-03 提交的 9 条候选已审查完毕。其中 **7 条已定**，**2 条被判 `DEFER`**：

> **`DEFER` = 研究价值存在，但当前证据或分类尚不足以定性。**
> 它**不是**「不成立」（那会判 `REJECT`），也**不是**「资料不够」（那会判 `INSUFFICIENT`）。
> **它需要补做「指定的缺失项」才能再评估。**

所以你这一轮**只做两件事**，且**只补被指定的缺失项**。
★ **不要**重做其它 7 条候选；★ **不要**为了「让它通过」而放宽证据门槛 ——
**宁可它仍判 `DEFER`**。

---

# 3. 你要补的两条

## 3.1 `R02-COAL-002` —— 2022–2024 煤炭高股息 / 红利资产重估行情

**当前状态**：`peak = UNKNOWN`、`end = OPEN_ENDED`（**Campaign 结构缺失**）。

### 缺失项 ①：**板块指数口径序列**（用于界定 peak / end）

你需要给出该段的**时间结构**。若拿不到可界定 peak/end 的行情序列，
**如实写 `peak = UNKNOWN` / `end = OPEN_ENDED` 并说明为什么**。

> ★★ **已知障碍（R02-03 的 `known_gaps` 已记）**：
> 「指数涨跌幅 / 板块涨幅」这类数字**只能来自商用数据库（Wind 等）**。
> **若仍拿不到 Tier 1/2 一手行情口径 → 如实写入 `quality_summary.known_gaps`，
> 不得用二手口径顶替。**「拿不到」本身是**可接受的结论**。

### 缺失项 ②：与 `R02-COAL-001` 及 **2022 俄乌能源价格段**的**边界判定**

- `R02-COAL-001`（2021 动力煤供需缺口）与 `R02-COAL-002`（2022–24 红利重估）
  是**两个 Campaign**，还是**同一 Theme Cycle 的不同阶段**？
- 2022 年俄乌冲突引发的全球能源价格上行，是**独立一段**，还是应并入上面任一段？
- 给出你的**判据**（不是结论就够 —— 要给可核验的依据）。

## 3.2 `R02-MEDIA-002` —— 2018 年游戏版号暂停与恢复驱动的传媒 / 游戏板块周期

**当前状态**：被判 `DEFER`，理由是**「下行段 + 政策转向」不构成标准的 `MAIN_RISE` Campaign**。

### 缺失项 ①：**重新界定为「版号恢复后的修复段」**

把**政策转向当起点**（2018-12-21 中宣部出版局表态「首批送审部分游戏已完成审核、正在抓紧核发版号」），
而不是当终点。然后取得**该修复段**的行情证据与时间结构。

### 缺失项 ②：版号暂停**起止日**的**可用口径说明**

> ★★ 该暂停**未被正式公告** —— **没有官方一手来源**。
> 你需要**说明你所用口径是什么**（哪家媒体/机构在什么时候如何描述该窗口），
> 并如实标注其来源层级。**不得**假装存在官方公告。

---

# 4. 四条红线（违反即整包作废）

| # | 禁止 |
|---|---|
| 1 | **不得**修改任何既有文件（不改 canonical DB / `schema.sql` / `exports/` / `src/**` / 冻结 artifact） |
| 2 | **不得**覆盖 `research/intake/packages/R02-03/`（升版规则：**新版写新文件**） |
| 3 | **不得**出现评分 / 排序 / 预测字段（`score` `rank` `probability` `prediction` `win_rate` `target_price` …），也**不得**出现 canonical 持久化字段名（完整清单见协议 §12） |
| 4 | **不得**声称 `VERIFIED`（你的 `research_status` 只能是 `PROVISIONAL` / `CONFLICT` / `INSUFFICIENT`） |

★ **你唯一可写的位置** = `research/intake/packages/R02-04/`。

---

# 5. 交付目录（与 R02-03 完全一致，缺任一文件即视为未完成）

```text
research/intake/packages/R02-04/
├── manifest.json            # + macro_theme_proposals + cross_task_notes（只放这里）
├── coverage.md
├── candidates.json          # campaign_candidates
├── evidence.json
├── sources.json
├── securities.json
├── exclusions.json          # **强制，不得为空**
├── conflicts.json
├── research_questions.json
├── quality_summary.json
└── checksums.sha256
```

★ **必填字段清单**：见 `docs/RESEARCH_AGENT_PROMPT_R02-03.md` §6.1
（**逐条抄自 schema**，本文件不重复）。若沙箱里没有该文件，就按
`historical_research_intake.schema.json` 的 `required` 字段来。

★ **ID 前缀**：`R02-COAL-*` / `R02-MEDIA-*`（沿用 R02-03 的 scope 分段）。
**不得**创造 canonical ID（`C-*` / `RC-*` / `CC-*` / `TH-*`）。

---

# 6. 提交前自检（**必做**）

```bash
# 在沙箱根执行 —— 必须用这个解释器（系统 python3 缺 jsonschema → C25 必 FAIL）
/Users/yangfan/.workbuddy-ai/binaries/python/envs/default/bin/python \
  research/scripts/validate_historical_research_intake.py research/intake/packages/R02-04
```

**必须贴出 `RESULT: PASS`。** 退出码 `0` = 通过；`1` = 存在 FAIL。

★ 所有文件必须 **LF** 行尾（C20 会检查）。

---

# 7. ★ 上一轮的两条教训（请逐条对照）

1. **不要用二手行情口径冒充一手。** R02-03 全部来源中，行情侧**只有 Tier 3**。
   本轮**如果还是只有 Tier 3**，就**照实写** —— 那不会让你被判失败，**但假装有 Tier 1 会**。
2. **日期端点必须有 `source_id`。** R02-03 有一条候选的起始端点（`2022-11-30`）**没有任何来源**
   → 被审查裁定**收回**到有来源支持的范围。**每一个日期都必须指得出出处。**

---

# 8. 最重要的一句

> **`DEFER` 的补做，允许的结果是「仍然 `DEFER`」。**
> 你要补的是**缺失的证据与定性依据**，不是**一个能通过审查的结论**。

---

*Research Agent Prompt · R02-04 · 签发 2026-10-11 · 依据 `HISTORICAL_UNIVERSE_R02_TASK_MANIFEST_v0_1.json`*
