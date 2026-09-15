# research/current — Current Research Discovery 数据协议 v1.0

> **Phase 7** 的离线研究数据端。回答的问题是：
> **「今天这个时间点，我应该去历史资料里研究什么？」**
> 而不是「明天应该买什么」。

---

## 1. 为什么存在这一层

ThreeC 的历史研究数据覆盖到 **2025**，而「当前时间」是 **2026**。
Current Time Lens 原本只能回答「现在是几月，这个月历史上发生过什么」，
无法回答「现在可能有什么值得开始研究的 Theme」。

本层补上这一段：把**离线研究**（人 / 脚本 / AI）产出的「当前研究对象候选」
以**可验证的静态数据**形式交给产品端。

```
Web / AI Research（离线，人工或脚本）
        ↓
research/current/current_candidates.json      ← 本目录
        ↓
Product Adapter（src/data/timeline/currentCandidate.ts）
        ↓
Current Time Lens（当前研究候选）
        ↓
Historical Similar Phase（Similarity v2）
        ↓
Research Questions（研究方向）
```

### 硬边界

| 允许 | 禁止 |
|---|---|
| 离线人工 / 脚本 / AI 生成候选数据 | 产品运行时联网抓取 |
| 静态 JSON 落库并提交 Git | 前端调用 LLM / 外部 API / 新闻源 |
| 产品端只读消费 | 产品端写入 DB / schema / export / contract |
| GitHub Pages / PWA 静态部署 | 引入后端 / 实时行情 / 资金 / 情绪数据 |

**网络与 AI 只出现在「研究数据生成端」，不进入「产品运行端」。**

---

## 2. 文件

| 文件 | 作用 |
|---|---|
| `current_candidates.json` | **canonical 数据集**（产品端默认消费）。当前为**空集** —— 诚实空态。 |
| `schema.json` | 数据协议（JSON Schema，draft-07 子集）。字段与枚举的权威说明。 |
| `fixtures/example_candidates.json` | **示例 fixture，不是真实研究数据**。仅用于验证协议 / 防线 / 推断 / 相似度行为。 |
| `validate_current_research.py` | 见 `../scripts/validate_current_research.py`（验证器）。 |

---

## 3. 核心概念

### 3.1 Candidate ≠ Theme ≠ Campaign

```
Raw Signal → Candidate → Evidence Accumulation → Theme Hypothesis
           → Theme Forming → 正式 Research Campaign
```

**Current Candidate 是研究对象，不是已经验证的 Theme。**
它可以被继续观察 / 被证伪 / 被合并 / 被拆分 / 最终升级为正式 Campaign / 被删除。

它**绝不**自动写入 `campaigns` / 正式导出。命名空间隔离：

| 前缀 | 含义 |
|---|---|
| `C-*` | 正式 Historical Campaign（Research 生产） |
| `RC-*` | Research Candidate（Research 生产） |
| `CC-*` / `FX-*` | **Current Candidate**（本层；`FX-` 仅 fixture） |

候选 ID 使用 `C-` / `RC-` 前缀会被验证器拒绝。

### 3.2 事实 / 解释 / 推测必须分开

| 层级 | 唯一允许出现的位置 |
|---|---|
| **事实**（Fact） | `evidence[].claim` —— 只写「谁在什么时候发布了什么」，禁止写入推断 |
| **解释**（Interpretation） | `core_narrative` —— 对事实的解读 |
| **推测 / 未知**（Hypothesis / Unknown） | `uncertainty_notes` —— 必须显式写出 UNKNOWN |

### 3.3 阶段由「相位证据矩阵」推导，不由单一指标决定

禁止 `涨幅 > X ⇒ EXPANSION`。阶段来自 8 个维度的证据组合：

| 维度 | 含义 | 可否由证据派生 |
|---|---|---|
| `narrative` | 是否形成清晰主线 | ✗ 研究声明 |
| `policy` | 是否出现政策催化 | ✓ 由 `POLICY` 证据派生 |
| `industry` | 是否出现产业反馈 | ✓ 由 `INDUSTRY` 证据派生 |
| `market` | 是否出现市场关注 | ✓ 由 `MARKET` 证据派生 |
| `capital` | 是否出现资金响应 | ✓ 由 `CAPITAL` 证据派生 |
| `breadth` | 是否从少数标的扩散 | ✗ 研究声明 |
| `company` | 是否出现公司层验证 | ✓ 由 `COMPANY` 证据派生 |
| `information_marginal` | 新增信息边际（区分 PEAK / EXPANSION） | ✗ 研究声明 |

水平枚举（统一 6 值，逐维度语义见 `schema.json`）：
`ABSENT` / `EMERGING` / `PRESENT` / `STRONG` / `WEAKENING` / `UNKNOWN`

**研究只需声明无法由证据派生的三个维度**（`narrative` / `breadth` /
`information_marginal`）；其余留空即由证据确定性派生。声明值优先于派生值，
UI 会逐维度标注来源（研究声明 / 由证据派生 / 未标注）。

### 3.4 枚举只能是有意义的有限集，不能是伪精确数值

| 字段 | 允许值 |
|---|---|
| `candidate_status` | `CANDIDATE` / `WATCH` / `RESEARCHING` / `PROMOTABLE` / `REJECTED` |
| `attention_state` | `EARLY_SIGNAL` / `THEME_FORMING` / `BROAD_CONFIRMATION` / `EXPANSION` / `PEAK` / `DECLINE` / `UNKNOWN` |
| `evidence_strength` | `STRONG` / `MEDIUM` / `WEAK` |
| `evidence.direction` | `SUPPORTIVE` / `NEUTRAL` / `NEGATIVE` / `UNKNOWN` |
| `temporal_relation` | `BEFORE_SNAPSHOT` / `AT_SNAPSHOT` / `AFTER_SNAPSHOT` / `UNKNOWN` |

**禁止** `confidence: "87%"` 这类看起来精确但无统计意义的字段。
`PROMOTABLE` 也不表示「上涨确认」，只表示「可考虑进入正式 Theme / Campaign 研究」。

---

## 4. Temporal Firewall（时间防火墙）

这是本层最重要的基础设施。

1. 数据集必须有 `snapshot_date`；每个候选有自己的 `snapshot_date`（必须 ≤ 数据集）。
2. 每条证据必须有 `source_date` 或 `event_date`。
3. 推导规则：

```
date = source_date ?? event_date
date === null              → UNKNOWN
date  < snapshot_date      → BEFORE_SNAPSHOT
date === snapshot_date     → AT_SNAPSHOT
date  > snapshot_date      → AFTER_SNAPSHOT   ← 违规：不得参与任何判断
```

4. `AFTER_SNAPSHOT` 证据：
   - 不得影响 candidate state
   - 不得参与 Phase 推断
   - 不得参与 Similarity
   - UI 中单列显示为「已隔离（快照后）」

这样才能让 ThreeC 未来具备真正的 **Historical Discovery Benchmark** 能力
（回到某个历史时点，只用当时可得的信息做判断），而不会发生 look-ahead。

---

## 5. 如何新增一个候选

1. 在 `current_candidates.json` 的 `candidates` 加一条，`candidate_id` 用 `CC-` 前缀。
2. `snapshot_date` 填**你做研究的那一天**。
3. 每条事实写一条 `evidence`，注明 `source_date` / `source_type` / `evidence_strength`。
   **快照之后才知道的事，仍然可以写入并标记**（验证器会要求 `AFTER_SNAPSHOT`），
   但它在判断中被隔离。
4. 至少声明 `narrative`（无法由证据派生）。无任何证据时，必须在
   `uncertainty_notes` 明确写 `UNKNOWN`。
5. 跑验证器：

```bash
python research/scripts/validate_current_research.py
```

6. 产品端**不需要改代码** —— 数据集是静态 import，重新构建即可看到。

---

## 6. 明确不做

- 不做自动联网研究流水线（本层只定义**协议 + 验证器 + 消费端**）。
- 不做「AI 自动下结论」：候选必须带证据、必须能被证伪、必须写出 UNKNOWN。
- 不做评分 / 概率 / 胜率 / 买卖信号 / 目标价。
- 不把候选升级为正式 Campaign（那是 Research 的独立评审流程）。
