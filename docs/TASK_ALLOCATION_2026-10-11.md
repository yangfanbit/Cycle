# TASK_ALLOCATION_2026-10-11.md

> | 项 | 值 |
> |---|---|
> | 性质 | **剩余任务的分工表**（谁做、输入、产出、入口、验收） |
> | 前提 | R02-03 主线已闭环：DB 57 Campaign / 84 对象 · export v1.1 · SA 504 对 · 快照已签发 · **测试 874 全绿** |
> | 角色依据 | 协议 §3 **角色分离**（产出者 ≠ 审查者）；`AGENTS.md` §4 冻结区 |

---

## 〇、三种角色（谁是谁）

| 角色 | 是谁 | 只能做什么 |
|---|---|---|
| **Research Agent** | **另一个 Agent**（你指派） | 产出 **Research Intake Package**（证据 + 候选 + 排除项）。**不得**写 canonical、不得改冻结区 |
| **ThreeC Agent** | **我** | 签发任务 · 出 Prompt · **审查**（八种结果）· **canonicalization** · 下游刷新 · 产品侧 |
| **你（用户）** | — | **授权**与**数据决策**（新增 taxonomy 行、签发快照、启动研究轮次） |

> ★★ **硬规则**：Research Agent 与 ThreeC Agent **不得是同一个执行者**。
> 依据：协议 §3；且 2026-10-08 实测 self-review 抓到 **27 条「改写冒充引文」**。

---

## 一、剩余任务总表

| # | 任务 | **谁** | 阻塞在 | 我能否单方面推进 |
|---|---|---|---|---|
| **A** | R02-03 的 **2 条 DEFER 补做** | **Research Agent** | 需我出 Prompt + 你交接 | ❌（角色分离） |
| **B** | **文化传媒「当前侧」研究对象** | **Research Agent**（新一轮 current research） | 需**你授权新轮次** | ❌ |
| **C** | **别名归一化**（`动力煤`/`游戏`/`影视`/`虚拟电厂` 查不到父主题） | **我**，但需你先选方案 | 需**合同决策**（见 §三） | ⚠️ 需你选 |
| **D** | 快照校验器补 **CANONICAL 唯一性**检查 | **我** | 无 | ✅ 可立即做 |
| **E** | `refresh_downstream.py` 扩展（版本号/白名单**全局一致性**检查） | **我** | 无 | ✅ 可立即做 |
| **F** | 命名歧义清理（`research/reports/` vs `research/research/reports/`） | **我** | 无 | ✅ 可立即做（低优先） |

---

## 二、给 Research Agent 的两件事（A / B）

### A. R02-03 的两条 DEFER 补做

**产出位置**：**新任务** `R02-04`（**不覆盖 R02-03** —— 升版规则：新版写新文件）。

| 候选 | 审查结果 | **指定的缺失项**（来自 `R02-03_verdicts_v0_1.json`） |
|---|---|---|
| `R02-COAL-002` 2022–24 煤炭高股息 | `DEFER` | ① **板块指数口径序列**（用于界定 peak / end）② 与 `R02-COAL-001` 及 2022 俄乌段的**边界判定** |
| `R02-MEDIA-002` 2018 版号周期 | `DEFER` | ① **重新界定为「版号恢复后的修复段」**并取得该段行情证据 ② 版号暂停**起止日**的可用口径说明（该暂停**未被正式公告**） |

**交接方式**（与 R02-03 完全相同的流程）：

```bash
# 1) 我出任务清单 + Prompt（需你先说「出」）
#    参照：research/intake/HISTORICAL_UNIVERSE_R02_TASK_MANIFEST_v0_1.json
#          docs/RESEARCH_AGENT_PROMPT_R02-03.md
# 2) 我生成沙箱（一条命令，仓库外、~300 KB）
python research/scripts/make_research_handoff_sandbox.py --task R02-04
# 3) 你把沙箱路径 + 00_START_HERE.md 交给 Research Agent
# 4) 它交回 research/intake/packages/R02-04/ → 我审查
```

**验收标准**（它交回前必须自己跑）：
```bash
/Users/yangfan/.workbuddy-ai/binaries/python/envs/default/bin/python \
  research/scripts/validate_historical_research_intake.py research/intake/packages/R02-04
# 必须 RESULT: PASS
```

> ★ **注意**：`DEFER` 的缺失项里 **`板块指数序列`** 正是 R02-03 `known_gaps` 记的那个坎 ——
> 「指数涨跌幅只能来自商用数据库（Wind 等）」。**若仍拿不到 Tier 1/2 一手行情，就如实记 `known_gaps`，不要凑。**
> 「拿不到」本身是可接受的结论。

### B. 文化传媒「当前侧」研究对象

**为什么需要**：文化传媒的**历史侧**已入库（`C-2023-MEDIA-AI`），但**当前侧没有研究对象**。
`AGENTS.md` §5 的结构对应需要**两侧**才能比 —— 只有历史侧时，`DirectionLookup` 的回答是
`historical-only`（「历史可用，但无法回答『现在处于什么阶段』」）。

**前置**：需你**授权一轮 current research**（属独立轮次，不在 R02-03 范围）。
★ 2026-10-07 那次是在**沙箱**里临时建的 `CC-2026-MEDIA-AICONTENT`，**未进 canonical**，**不可复用**。

---

## 三、★ C：别名归一化 —— 需你先做**一个方案选择**

**现象**：用户输入 `动力煤` / `游戏` / `影视` / `虚拟电厂` → `DirectionLookup` 答**「未覆盖」**，
但它们的父主题其实**已在库内**（`煤炭` / `文化传媒` / `电力（运营端）`）。

**根因**：产品只能看到 export，而 **export 里没有 taxonomy（`themes.parent_theme_id`）** ——
只有对象实际挂的**主题名**。`动力煤` 从未成为主题名（它只是 intake 的 proposal）。

**三个方案**：

| 方案 | 做法 | 代价 | 我的评价 |
|---|---|---|---|
| **C1** | **export 增加 `themes` taxonomy 段**（根 + 子 + parent） | 合同再升一版（v1.2）；产品侧做一次「名称 → 根」查找 | ★ **推荐** —— 与 v1.1 的 `macro_theme_root` 同源（都来自 CMTR），是**唯一事实来源**的延伸 |
| **C2** | 产品内硬编码「别名 → 主题」对照表 | ❌ 造**第二套 taxonomy** | ❌ **不做** —— `CMTR v1` 明确拒绝这种表 |
| **C3** | 把 intake 的 `theme_name_candidates`（proposals）也导进 export 当别名 | 合同升版；但 proposals 是**未经审查的**名字 | ⚠️ 不推荐 —— 会把「未采纳的提案」变成产品可见事实 |

**需要你决定**：选 **C1**（我推荐）还是其他。选 C1 我就做（研究侧 + 产品侧 + 合同文档）。

---

## 四、给 ThreeC Agent（我）的三件小事（D / E / F）

### D. 快照校验器补「CANONICAL 唯一性」

**现状**：`validate_market_snapshot_v0_1.py` 的 **V2 只检查 `status` ∈ 枚举**，
**不约束全索引内 `CANONICAL` 至多一份** —— 实测两份 CANONICAL 也能通过全部 14 项校验。
**动作**：新增检查（V11 或扩展 V2）。**无阻塞，可立即做。**

### E. `refresh_downstream.py` 扩展

**现状**：已有 C1–C5（RULES 白名单 / SA 版本引用 / 投影器 / 配色 / lifecycle 覆盖）。
**缺口**：这一轮第 4 次踩的坑 —— **产品适配器的版本断言**（`validateTimelineExportV1` 硬断言 `'1.0'`）
不在检查范围内 → 漏改导致 **117 个测试失败**。
**动作**：把「**版本号与字段白名单的全局一致性**」也纳入 `--check`。**无阻塞。**

### F. 命名歧义（低优先）

`research/reports/` 与 `research/research/reports/` 两个路径**并存且含义不同**，
已在 `batch_auto_research.py` 里见过路径不一致（我按实际存在的那个读了）。
**动作**：先**只记录**（不合并 —— 动目录风险高），在 `AGENTS.md` 或 README 里写明两者分工。

---

## 五、建议的执行顺序

```
① 你选 C 的方案（C1 / 其他）           ← 唯一需要你做的**决策**
② 你说「出 R02-04」→ 我出 Prompt + 沙箱  ← 你只需交接给 Research Agent
③ 你授权「文化传媒当前侧」轮次           ← 之后我出第二个 Prompt
④ 我并行做 D + E（无阻塞，我现在就能做）
⑤ Research Agent 交回 → 我审查 → canonicalization → 下游刷新
```

★ 其中 **④ 不需要等你** —— 说一句「先做 D+E」我就可以开始。

---

*分工表 · 2026-10-11 · 依据：协议 §3 角色分离 · `AGENTS.md` §4 冻结区*
