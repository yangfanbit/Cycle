# MARKET_SNAPSHOT_CONTRACT_v0.1.md

> | 项目 | 值 |
> |---|---|
> | 文件性质 | **设计契约（DESIGN CONTRACT）** —— Phase 0 草案，**不是已冻结实现** |
> | 契约名 | `market_snapshot` |
> | 契约版本 | **`0.1`** |
> | 日期 | 2026-09-25 |
> | 依赖 | `docs/THREEC_1_1_MARKET_SNAPSHOT_ARCHITECTURE.md` · `docs/MARKET_SNAPSHOT_GOVERNANCE.md` |
> | 本轮不产出 | **不生成 `schema.sql` · 不实现数据库 · 不写代码** |
> | 状态 | **等待下一阶段确认** |
>
> 本文件只定义**字段与边界**。所有枚举**优先复用既有冻结定义**
> （`attention_state` · `evidence_strength` · `direction` · `source_type` ·
> Driver Canonicalization v0.4 · SA 状态词表），**不发明第二套语义**。

---

## 1. 契约总览

```jsonc
{
  "contract": "market_snapshot",
  "market_snapshot_version": "0.1",     // ← 本契约版本
  "snapshot_id": "MS-2026-09-30-01",
  "timestamp": "2026-09-30T20:00:00",

  "market_regime": { /* §2.1 */ },
  "research_context": { /* §2.2 */ },
  "observations": [ /* §2.3 */ ],
  "research_objects": [ /* §2.4 */ ],

  "historical_candidates": [ /* §3 · 输出 */ ],
  "provenance": { /* §4 */ }
}
```

- **顶层字段 = 9**（白名单式；禁止额外字段，与既有 export 风格一致）。
- `historical_candidates` 为**输出**；其余为**输入 / 上下文**。
- **禁止字段**：`prediction` · `signal` · `score` · `ranking` · `probability` · `confidence`。

---

## 2. 输入字段

### 2.1 `market_regime`（当前市场状态）

| 字段 | 枚举 | 必填 | 说明 |
|---|---|---|---|
| `broad_index_state` | `DOWN` / `FLAT` / `UP` / `UNKNOWN` | ✅ | 宽基方向（**区间口径，非单日**） |
| `breadth_state` | `NARROW` / `NORMAL` / `BROAD` / `UNKNOWN` | ✅ | 市场广度 |
| `liquidity_state` | `CONTRACTING` / `STABLE` / `EXPANDING` / `UNKNOWN` | ✅ | 流动性 |
| `risk_appetite_state` | `RISK_OFF` / `NEUTRAL` / `RISK_ON` / `UNKNOWN` | ✅ | 风险偏好 |
| `beta_note` | string | ✅ | **强制**：说明 β 不可分离程度 |
| `evidence_refs` | `OBS-*[]` | ❌ | 支撑以上判断的 observation id |

> **`market_regime` 不参与 Structural Status**（supplementary context only）。

### 2.2 `research_context`（研究上下文）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `research_question` | string | ✅ | 这一轮要回答什么（**不是**「买什么」） |
| `research_method` | string | ✅ | 方法（可复现性字段） |
| `source_policy` | string | ✅ | Tier 1 / 2 / 3 口径 |
| `coverage_note` | string | ❌ | 历史覆盖范围（如「历史研究覆盖至 2025」） |
| `known_limitations` | string[] | ❌ | 本轮已知限制 |

### 2.3 `observations[]`（观察 · 统一承载「事件 / 主题 / 产业变化」）

> ★ 原 `OC-*` 命名空间**已作废**；变化统一用 `Observation` 表达。

| 字段 | 类型 / 枚举 | 必填 | 说明 |
|---|---|---|---|
| `observation_id` | `OBS-*` | ✅ | 观察 id |
| `observation_type` | `POLICY` / `INDUSTRY` / `COMPANY` / `MARKET` / `CAPITAL` / `EXTERNAL` | ✅ | **证据类别**（≠ 驱动机制） |
| `date` | ISO date | ✅ | 观察日期 |
| `claim` | string | ✅ | **只写事实**：谁在何时发布了什么 |
| `evidence_strength` | `STRONG` / `MEDIUM` / `WEAK` | ✅ | 沿用既有 |
| `direction` | `SUPPORTIVE` / `NEUTRAL` / `NEGATIVE` / `UNKNOWN` | ✅ | 沿用既有 |
| `temporal_relation` | `BEFORE_SNAPSHOT` / `AT_SNAPSHOT` / `AFTER_SNAPSHOT` / `UNKNOWN` | ❌ | **派生**，不手填 |
| `linked_object_id` | `CC-*` / `URO-*` / `null` | ❌ | `null` = 全局观察 |

### 2.4 `research_objects[]`（研究对象）

| 字段 | 类型 / 枚举 | 必填 | 说明 |
|---|---|---|---|
| `object_id` | `CC-*` / `URO-*` | ✅ | `URO-*` **仅 Draft**（见治理 §C） |
| `object_kind` | `current_candidate` / `user_research_object_draft` | ✅ | 二态 |
| `display_name` | string | ✅ | — |
| `macro_theme` | string（**必须为 CMTR v1 既有 root**） | ✅ | **不得新建 Macro Theme** |
| `declared_phase` | `attention_state` 词表 ∪ `UNKNOWN` | ❌ | 沿用 `EARLY_SIGNAL` … `DECLINE` / `UNKNOWN` |
| `phase_source` | `DERIVED_FROM_EVIDENCE` / `RESEARCH_DECLARED` / `USER_DECLARED` / `UNKNOWN` | ✅ | 声明 vs 派生必须可区分 |
| `canonical_drivers` | Driver Canonicalization v0.4 词表 | ❌ | `POLICY_DRIVEN` / `TECH_BREAKTHROUGH` / `DEMAND_SURGE` / `SUPPLY_CONTRACTION` / `VALUATION_RESET` / `CYCLE_REVERSAL` / `EVENT_CATALYST` / `INDUSTRY_UPGRADE` / `UNKNOWN` |
| `evidence_categories` | 同 `observation_type` | ❌ | **证据类别**（与驱动机制分开命名） |
| `evidence_sequence` | `[{type, date}]` | ❌ | 供 SA `evidence_sequence` 维度（LCS） |
| `events` | `[{event_type, date, role}]` | ❌ | 供 SA `event_structure` 维度 |
| `resolution_state` | `RESOLVED` / `NEEDS_RESEARCH_ROUND` / `INSUFFICIENT` | ✅ | ★ 决定**能否进入匹配** |

**硬约束**：

> `resolution_state ≠ RESOLVED` 的对象**不得进入结构匹配**，只能输出
> 「证据不足以进行结构对应」+ 一条 `research_question`（**不凑案例**）。

---

## 3. 输出字段

### 3.1 `historical_candidates[]`（历史结构候选）

> **只能表达「研究候选」。** 每项 = 一个历史对象 + 逐维解释。

```jsonc
{
  "historical_candidates": [
    {
      "identity": {
        "historical_object_kind": "campaign | research_candidate",
        "historical_cycle_id": "…",              // 稳定 id，始终非空
        "historical_campaign_id": "C-… | null",  // 仅真实 Campaign 非空
        "historical_research_candidate_id": "RC-… | null",
        "historical_theme_cycle_id": "…"
      },
      "rule_set_version": "structural-analogy-ruleset-v0.3",   // ★ 复用冻结规则
      "structural_status": "STRUCTURAL_SUPPORTED | STRUCTURAL_PARTIAL | THEME_ONLY | INSUFFICIENT_EVIDENCE | NO_VALID_CORRESPONDENCE",
      "strict_structural_supported": false,
      "theme_relation": { "value": "SAME_MACRO_THEME | CROSS_MACRO_THEME", "role": "METADATA_ONLY" },
      "dimensions": {
        "lifecycle":         { "status": "MATCH | PARTIAL | MISMATCH | UNKNOWN | NOT_AVAILABLE" },
        "mechanism_driver":  { "status": "MATCH | PARTIAL | PERIPHERAL_OVERLAP | MISMATCH | UNKNOWN | NOT_AVAILABLE" },
        "evidence_sequence": { "status": "SEQUENCE_MATCH | SEQUENCE_PARTIAL | SET_ONLY | SEQUENCE_MISMATCH | UNKNOWN | NOT_AVAILABLE" },
        "event_structure":   { "status": "MATCH | PARTIAL | MISMATCH | NOT_AVAILABLE" }
      },
      "supported_dimensions": ["…"],
      "unknown_dimensions": ["…"],
      "unsupported_dimensions": ["…"],
      "why_similar": ["…"],
      "why_not_similar": ["…"],
      "dimension_evidence": { "…": ["…"] },      // 直接依据
      "background_sources": ["…"]                // 背景，非依据
    }
  ]
}
```

**硬约束**：

1. **禁止**：`prediction` · `signal` · `score` · `ranking` · `probability` · `top N` · `best analogue`。
2. `historical_candidates[]` 按 `historical_cycle_id` **升序**（稳定 identity 顺序，**不是强弱排名**）。
3. `theme_relation` **只作 metadata**，**不得**据此升降级。
4. 状态词表**必须**与 SA v0.3 一致（**不新增状态**）。

---

## 4. `provenance`（可追溯性）

| 字段 | 说明 |
|---|---|
| `generated_by` | `manual` / `script` / `ai-offline` / `other`（沿用既有枚举） |
| `ai_assisted` | boolean —— 是否含 AI 草稿 |
| `reviewed_by` / `reviewed_at` | 人工评审者与时间（**进入 CANONICAL 必填**） |
| `source_commit` | 生成时的 git commit |
| `rule_set_version` | `structural-analogy-ruleset-v0.3` |
| `supersedes` / `superseded_by` | 版本链（可空） |

---

## 5. Artifact 边界

### 5.1 Market Snapshot 是**独立 Artifact**

> **Market Snapshot 不进入 `timeline_export_v1.json`。**

理由：

1. `timeline_export_v1` 是**历史事实**的 canonical 交换契约（Contract v1.0，严格白名单）。
2. Market Snapshot 是**当前研究过程**；二者语义不同（架构 §4）。
3. 向 export 加字段 = 事实上的 Contract 变更（历史上已因 `CAMPAIGN_FIELDS` 白名单 FAIL 而回退）。

### 5.2 边界对照

| 项 | 位置 |
|---|---|
| 历史事实 | `exports/timeline_export_v1.json`（**只读，本契约不触碰**） |
| 当前研究过程 | **独立 artifact**（Market Snapshot / Research Request / Correction Record） |
| 交换方式 | 各自独立文件；**不互相嵌入** |

---

## 6. 版本规则

### 6.1 版本层级

| 变化类型 | 版本动作 | 示例 |
|---|---|---|
| **结构变化**（新增可选字段 / 新增枚举值，向后兼容） | **minor**（`0.1 → 0.2`） | 新增 `market_regime.sector_rotation_state` |
| **破坏性变化**（删除字段 / 改语义 / 改必填性） | **major**（`0.x → 1.0`） | 删除 `research_context` |
| **内容修正**（同一结构下的数据修正） | **artifact revision**（**不动契约版本**） | 某 `observation.claim` 修正 |

### 6.2 规则

1. 契约版本字段：`market_snapshot_version`（**唯一版本字段**）。
2. `0.x` 阶段：结构可演进；**任何结构变化必须 minor bump**。
3. `1.0` 之后：`v1.0` 字段**不得**被后续版本删除或改语义（只允许新增可选字段）。
4. **内容修正 ≠ 版本升级**：修正通过 artifact revision（新文件 + 台账）表达，契约版本不变。
5. 已 `CANONICAL` 的 artifact **不可变**；修正 → 新 revision（见治理 §A）。

### 6.3 与既有契约的关系

| 契约 | 版本 | 本契约是否触碰 |
|---|---|---|
| Timeline Export | `1.0` | ❌ **不触碰** |
| Current Candidate Dataset | `1.0` | ❌ **不触碰**（Market Snapshot 独立） |
| SA Rule Set | `v0.3` | ❌ **不触碰**（只复用） |

---

## 7. 明确不做（本契约范围外）

- ❌ **不生成 `schema.sql`**
- ❌ **不实现数据库**
- ❌ 不写代码 / 不加 UI / 不接 AI API
- ❌ 不修改 `research/` · `exports/` · `contracts/` · `schema.sql`
- ❌ 不新增 score / ranking / probability / prediction

---

*契约结束 · Market Snapshot Contract v0.1 · 2026-09-25 · 等待下一阶段确认*
