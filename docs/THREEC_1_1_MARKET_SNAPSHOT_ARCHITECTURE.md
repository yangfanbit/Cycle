# THREEC_1_1_MARKET_SNAPSHOT_ARCHITECTURE.md

> | 项目 | 值 |
> |---|---|
> | 文件性质 | **ThreeC 1.1 Phase 0 架构设计文档（DESIGN ONLY）** —— 不是实现、不是 schema 冻结件、不是 Contract |
> | 轮次 | ThreeC 1.1 Phase 0：**Market Snapshot Architecture Freeze** |
> | 日期 | 2026-09-25 |
> | Canonical Repository | https://github.com/yangfanbit/Cycle |
> | 基线 | `main` @ `dcf4786`（= `origin/main`）· tag `v1.0.0` → `064d39c` |
> | 本轮硬约束 | **只允许改 `docs/`；不改代码 / UI / 数据库 / Research 数据 / artifact** |
> | 状态 | **等待下一阶段确认** |
>
> 配套文档：
> `docs/MARKET_SNAPSHOT_CONTRACT_v0.2.md`（字段级契约）·
> `docs/MARKET_SNAPSHOT_GOVERNANCE.md`（治理规则）·
> `docs/THREEC_1_1_PHASE_0_DESIGN_FREEZE_REPORT.md`（本轮报告）

---

## 0. 本轮定位

ThreeC 1.1 目标：

```
从：历史机会地图
到：当前市场状态  →  历史结构研究  →  研究辅助系统
```

**ThreeC 不是预测系统。** 永久禁止：买卖信号 · 选股 · 价格预测 · score · ranking · probability · 胜率。

本文件定义 **Market Snapshot 的架构**：它是什么、如何流转、与冻结的历史基座如何分离、Product 能读什么、SA 在哪里介入。

---

## 1. Market Snapshot 定义

### 1.1 定义

> **Market Snapshot = 当前研究过程中的「状态记录 Artifact」。**
>
> 它记录「在某个 `snapshot_date`，我们把哪些当前市场状态、哪些观察、哪些研究对象放进了研究流程」。
> 它是**研究过程的快照**，不是结论，不是模型，不是信号。

**它不是**：

| ❌ 不是 | 说明 |
|---|---|
| 算法 / 模型 | 不内含任何打分或推断引擎 |
| 信号 / 预测 | 不产生买卖或方向判断 |
| 评分 / 排名 | 无 `score` / `ranking` / `probability` |
| 数据库 | 是静态 Artifact（JSON），不是运行时库 |

### 1.2 输入

| 输入 | 含义 |
|---|---|
| `market_regime` | **当前市场状态**：宽基方向 / 广度 / 流动性 / 风险偏好（离散枚举 + `UNKNOWN`） |
| `research_context` | **研究上下文**：这一轮为什么做、研究问题、方法、来源口径、覆盖范围 |
| `observations` | **观察**：带日期、带来源的可核验事实（事实 / 解释 / 推测三分离） |
| `research_objects` | **研究对象**：本快照要研究的对象（引用 `CC-*`，或声明 `URO-*` draft） |

### 1.3 输出

> **输出 = `historical_candidates`（历史结构候选）。**

- 「候选」= **研究候选**：值得继续研究的历史对象清单 + 逐维解释。
- **不是**预测结果，**不是**推荐，**不是**排名。

**禁止出现在输出中**：`prediction` · `signal` · `score` · `ranking` · `probability` · `confidence%` · `top N` · `best analogue`。

### 1.4 与既有对象的关系

| 既有概念 | 关系 |
|---|---|
| Current Candidate（`CC-*`） | Market Snapshot 的 `research_objects` **可引用**它；`CC-*` 仍是离线研究对象 |
| User Research Object（`URO-*`） | **仅 Draft**，须经 Human Review 才成为 Canonical Research Object（见 §9） |
| Historical Campaign（`C-*`）/ RC（`RC-*`） | 只出现在**历史侧**（匹配的右侧），绝不作为快照的研究对象 |
| Structural Analogy | 快照匹配**就是** SA 的一次执行；**不新增第二套匹配算法**（见 §8） |

---

## 2. Market Snapshot Lifecycle

### 2.1 四态

```
DRAFT
  ↓
REVIEW
  ↓
CANONICAL
  ↓
ARCHIVED
```

| 状态 | 含义 | 谁可写 | Product 可否消费 |
|---|---|---|---|
| `DRAFT` | 研究草稿（可含 AI 辅助产物） | 研究者 / 离线脚本 / AI（离线） | ❌ **不可** |
| `REVIEW` | 已提交人工评审，等待判定 | 研究者提交，评审人处理 | ❌ **不可** |
| `CANONICAL` | **已通过人工评审**，正式生效 | 仅评审通过后由流程置位 | ✅ **唯一可消费状态** |
| `ARCHIVED` | 已被新快照取代 / 不再使用 | 流程置位 | ❌ **不可**（保留供追溯） |

### 2.2 硬规则

1. **只有 `CANONICAL` 状态的 Market Snapshot 允许 Product 消费。**
2. 状态跃迁**必须**由人工评审触发（`DRAFT → REVIEW → CANONICAL`）；**不得**自动跳级。
3. `CANONICAL` 是**不可变**的：任何内容修改都**必须**产生新 revision（见 `MARKET_SNAPSHOT_CONTRACT_v0.2.md` §版本规则），不得就地编辑。
4. 快照被取代时置 `ARCHIVED`（**不删除**），并记录 `superseded_by`。

---

## 3. Research Request 生命周期

### 3.1 流程

```
Research Request
      ↓
Market Snapshot Draft
      ↓
Historical Research
      ↓
Human Review
      ↓
Canonical Artifact
```

| 段 | 说明 | 产物 |
|---|---|---|
| **Research Request** | 一次研究诉求：「我想研究 X」/「当前环境是否与历史某结构对应」 | `RR-*`（研究请求） |
| **Market Snapshot Draft** | 把请求落成 `DRAFT` 快照（填 `market_regime` / `observations` / `research_objects`） | `MS-*`（`DRAFT`） |
| **Historical Research** | 对研究对象做历史检索 + 复用 SA 做结构比较 | 候选 + 逐维解释 |
| **Human Review** | 人工判定：历史结构是否成立、是否值得继续研究 | 评审记录 |
| **Canonical Artifact** | 评审通过 → 置 `CANONICAL` → 可被 Product 消费 | `MS-*`（`CANONICAL`） |

### 3.2 AI 可以辅助的位置

> AI **只**出现在**离线研究生成端**，且产物一律是 **draft**。

| ✅ AI 可以 | 说明 |
|---|---|
| 搜索历史候选 | 在既有历史对象里**检索**可能相关的对象（检索，不判定） |
| 整理资料 | 把公开来源整理成 `observations`（带日期 / 来源 / 强度） |
| 生成 draft | 起草 `DRAFT` 快照与解释文本 |

### 3.3 AI 不可以

| ❌ AI 不可以 | 理由 |
|---|---|
| **自动确认结构相似** | 结构判定**只**由冻结 SA v0.3 规则 + 人工确认决定 |
| **自动 Promotion** | RC → Campaign 必须人工闸门（见 §7） |
| **自动评分** | 与项目初心直接冲突 |
| **自动排名** | 同上 |

> 任何 AI 产物都是 draft；**签发权永远在人工评审**。

---

## 4. Artifact 边界

### 4.1 两类 Artifact 必须分离

| 类别 | Artifact | 性质 | 可变性 |
|---|---|---|---|
| **历史 Artifact** | Timeline Export · Campaign · SA · TO · Driver | **历史事实**（已冻结） | **只读**；修改只能通过纠错流程产生新版本（§6） |
| **当前研究 Artifact** | **Market Snapshot** · **Research Request** · **Correction Record** | **当前研究过程** | 走 `DRAFT → REVIEW → CANONICAL` 生命周期 |

### 4.2 核心原则

> **历史事实 ≠ 当前研究过程。**

- 历史 Artifact 表达「**过去发生了什么**」，已冻结，不得被当前研究改写。
- 当前研究 Artifact 表达「**我们此刻在研究什么、观察到了什么**」，可迭代，但必须留痕。
- 两者**不得混存于同一文件**；Market Snapshot **不进入** `timeline_export_v1.json`（见 Contract §Artifact 边界）。

### 4.3 目录与命名（设计意图，Phase 0 不落盘）

| Artifact | 建议位置（Phase 1 决定） |
|---|---|
| Market Snapshot | `research/current/market_snapshots/`（**新增目录**，不动既有 schema） |
| Research Request | 同上 / 独立 `research/current/requests/` |
| Correction Record | `research/corrections/`（**新增**） |

---

## 5. Product 消费边界

### 5.1 允许

> **Product 只能读取 `CANONICAL` 状态的 Artifact。**

### 5.2 禁止

| ❌ Product 禁止读取 | 理由 |
|---|---|
| AI draft | 未经人工评审，不可信 |
| research notes | 研究过程材料，非正式产物 |
| temporary analysis | 临时分析，可能含 look-ahead |
| `DRAFT` / `REVIEW` / `ARCHIVED` 快照 | 非 canonical |

### 5.3 Product 行为约束（沿用 1.0 红线）

- 不重新实现 SA 规则 · 不产生新的研究结论
- 不把 `UNKNOWN` 当 `NO` · 不把 `PARTIAL` 当 `MATCH`
- 不生成 score / ranking / probability / prediction
- 不联网 · 不调 LLM（产品运行端）

---

## 6. Historical Correction Flow

### 6.1 流程

```
Correction Intake
      ↓
Evidence Collection
      ↓
Human Review
      ↓
New Artifact Version
      ↓
Product Read Only
```

| 段 | 动作 | 产物 |
|---|---|---|
| **Correction Intake** | 登记纠错请求（目标对象 / 字段 / 现值 / 建议值 / **原因**） | `CR-*`（`PENDING`） |
| **Evidence Collection** | 收集支撑证据（**必填**） | `CR-*.evidence[]` |
| **Human Review** | 人工判定 `ACCEPTED` / `REJECTED` / `NEEDS_EVIDENCE`，评估影响面 | 决策 + blast radius |
| **New Artifact Version** | **新建** artifact 版本（旧版本逐字节保留） | 新 artifact + 纠错台账 |
| **Product Read Only** | Product 只读消费，并展示修正 provenance | UI 溯源 |

### 6.2 硬约束

> **禁止直接修改历史 artifact。**
> 修正**只**通过「新建 artifact 版本 + 纠错台账」生效；原始值永久保留。
> `reason` 必填 · `evidence` 必填（见 `MARKET_SNAPSHOT_GOVERNANCE.md` §A）。

---

## 7. 新行情导入流程

### 7.1 流程（保持既有链路）

```
Observation
      ↓
Research Candidate
      ↓
Lifecycle Tracking
      ↓
Campaign Promotion
```

| 段 | 说明 | 约束 |
|---|---|---|
| **Observation** | 带日期 / 来源的可核验事实 | 事实 / 解释 / 推测三分离；`date ≤ snapshot_date` |
| **Research Candidate** | 对象化为 `RC-*` | ★ **RC ≠ Campaign**；不自动进入 `campaigns[]` |
| **Lifecycle Tracking** | 生命周期观察 | **append-only**；禁止 look-ahead |
| **Campaign Promotion** | 晋升为 `C-*` | ★ **必须人工确认**；新建，不覆盖 |

### 7.2 核心

> **Research Candidate ≠ Campaign。**
> **Promotion 必须人工确认。**
> 晋升失败（证据不足）是**合法结果** —— 保持 `RC-*` 并写明还缺什么。

---

## 8. SA 边界

### 8.1 Market Snapshot ≠ SA

> Market Snapshot 是**输入容器**；SA 是**结构比较规则**。两者不是同一件事。

### 8.2 关系

```
Market Snapshot
      ↓
Historical Candidate Retrieval      （检索：找出可能相关的历史对象）
      ↓
SA v0.3 Structure Comparison        （比较：复用冻结规则，产出逐维状态）
```

### 8.3 硬约束

> **只复用冻结 SA v0.3。不要设计新的匹配算法。**
>
> - 不新增 similarity / score / weighted / tier 判定体系
> - 不新增 driver vocabulary
> - `currentSimilarity.ts` 保持 LEGACY / FREEZE
> - `market_regime` 只作 supplementary context，**不参与** Structural Status

---

## 9. Namespace 规则

### 9.1 允许（本轮确认）

| 前缀 | 含义 | 状态 |
|---|---|---|
| `MS-*` | **Market Snapshot** | ✅ |
| `CR-*` | **Correction Record** | ✅ |
| `IR-*` | **Import Record** | ✅ |
| `URO-*` | **User Research Object Draft** | ✅ **仅 Draft** |

### 9.2 `URO-*` 规则（收紧）

```
URO Draft
      ↓
Human Review
      ↓
Canonical Research Object
```

> **禁止：用户自由声明后直接进入 Product。**
> `URO-*` 只能是 draft；必须经人工评审后才成为 Canonical Research Object，方可被 Product 消费。

### 9.3 删除 `OC-*`

> **不新增 Observed Change namespace。**
> 「事件 / 主题 / 产业变化」统一使用 **`Observation`** 概念承载（见 §1.2 输入的 `observations`）。
> **本轮起，`OC-*` 前缀作废。**

### 9.4 既有命名空间（不变）

`C-*`（Campaign）· `RC-*`（Research Candidate）· `CC-*`（Current Candidate）。
**新前缀不得与既有前缀混用。**

---

## 10. 等待确认

| # | 待确认 |
|---|---|
| Q-1 | Market Snapshot 作为**独立 Artifact**（不进 `timeline_export_v1.json`）？ |
| Q-2 | Lifecycle 四态（`DRAFT → REVIEW → CANONICAL → ARCHIVED`）且**仅 CANONICAL 可消费**？ |
| Q-3 | `URO-*` 收紧为 **Draft-only**（须人工评审）？ |
| Q-4 | 删除 `OC-*`，统一用 `Observation`？ |
| Q-5 | 匹配**只**复用冻结 SA v0.3？ |
| Q-6 | 4 个人工审核节点（见 `MARKET_SNAPSHOT_GOVERNANCE.md` §C）？ |

---

*架构文档结束 · ThreeC 1.1 Phase 0 · Market Snapshot Architecture · 2026-09-25 · 等待下一阶段确认*
