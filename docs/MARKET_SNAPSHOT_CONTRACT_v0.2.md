# MARKET_SNAPSHOT_CONTRACT_v0.2.md

> | 项目 | 值 |
> |---|---|
> | 文件性质 | **设计契约（DESIGN CONTRACT）** —— 0.x 阶段，结构可演进 |
> | 契约名 | `market_snapshot` |
> | 契约版本 | **`0.2`** |
> | 日期 | 2026-09-26（v0.1 为 2026-09-25） |
> | 依赖 | `docs/THREEC_1_1_MARKET_SNAPSHOT_ARCHITECTURE.md` · `docs/MARKET_SNAPSHOT_GOVERNANCE.md` · `docs/MARKET_REGIME_AI_INTERFACE_v0.1.md` |
> | 实现 | `research/current/market_snapshots/`（schema + validator + generator + 两个投影器） |
> | 本轮不产出 | **不生成 `schema.sql` · 不实现数据库** |
> | 状态 | **v0.2 已实现并验证**（`MS-2026-09-15-01`） |

## 0. 版本历史

| 版本 | 日期 | 变化 | 性质 |
|---|---|---|---|
| `0.1` | 2026-09-25 | 初版：11 个顶层字段；`historical_candidates[]` **内嵌全部解释字段** | — |
| **`0.2`** | **2026-09-26** | ① `historical_candidates[]` 改为**轻量索引**（只存 `identity` / `structural_status` / `strict_structural_supported`）；② **新增顶层字段 `candidates_source`**（回指冻结 SA artifact）；③ 顶层字段 11 → **12** | **minor**（0.x 阶段结构变化，按 §6.2） |

**v0.2 动机（实测）**：v0.1 的内嵌模式下，单份快照 **1.9 MB** —— 把冻结 SA artifact 的内容整体复制了一份，
按月更新约 23 MB/年，且与冻结 artifact **重复存储**、存在版本漂移风险。
改为**回指**后同一份快照降到 **168 KB（约 1/11）**，且**不丢信息**（细节仍可按 `rule_set_version` 取回）。

> **为什么是 minor 而不是 major**：契约仍在 `0.x`，§6.2 规定「0.x 阶段任何结构变化必须 minor bump」。
> 进入 `1.0` 之后，同性质的改动才需要 major。
>
> 本文件只定义**字段与边界**。所有枚举**优先复用既有冻结定义**
> （`attention_state` · `evidence_strength` · `direction` · `source_type` ·
> Driver Canonicalization v0.4 · SA 状态词表），**不发明第二套语义**。

---

## 1. 契约总览

```jsonc
{
  "contract": "market_snapshot",
  "market_snapshot_version": "0.2",     // ← 本契约版本
  "snapshot_id": "MS-2026-09-15-01",
  "snapshot_date": "2026-09-15",        // ★ PIT 基准（v0.2 起显式列出）
  "timestamp": "2026-09-30T20:00:00",
  "status": "DRAFT",                    // ★ 生命周期四态（v0.2 起显式列出）

  "market_regime": { /* §2.1 */ },
  "research_context": { /* §2.2 */ },
  "observations": [ /* §2.3 */ ],
  "research_objects": [ /* §2.4 */ ],

  "historical_candidates": [ /* §3 · 输出（轻量索引） */ ],
  "candidates_source": { /* §3.2 · 回指描述 */ },
  "provenance": { /* §4 */ }
}
```

- **顶层字段 = 12**（白名单式；除一个非语义的 `_comment` 外禁止额外字段，与既有 export 风格一致）。
- `historical_candidates` + `candidates_source` 为**输出**；其余为**输入 / 上下文**。
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

### 3.1 `historical_candidates[]`（历史结构候选 · **轻量索引**）

> **只能表达「研究候选」。** v0.2 起每项**只存索引**，解释细节**回指** `candidates_source`（§3.2）。

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
      "structural_status": "STRUCTURAL_SUPPORTED | STRUCTURAL_PARTIAL | THEME_ONLY | INSUFFICIENT_EVIDENCE | NO_VALID_CORRESPONDENCE",
      "strict_structural_supported": false
    }
  ]
}
```

**硬约束**：

1. **只允许上述 3 个字段**；出现其它字段即校验 **FAIL**（`V8`）—— 其余一律**回指**，不得复制。
2. **禁止**：`prediction` · `signal` · `score` · `ranking` · `probability` · `top N` · `best analogue`。
3. `historical_candidates[]` 按 `historical_cycle_id` **升序**（稳定 identity 顺序，**不是强弱排名**）。
4. 状态词表**必须**与 SA v0.3 一致（**不新增状态**）。

### 3.2 `candidates_source`（回指描述 · **v0.2 新增**）

> 说明「候选细节从哪里取回」。这是 v0.2 的核心：**索引在快照内，解释在冻结 artifact 里**。

```jsonc
{
  "candidates_source": {
    "artifact": "research/research/reports/structural_analogy_explanations_v0_5.json",
    "artifact_version": "0.5",
    "rule_set_version": "structural-analogy-ruleset-v0.3",   // ★ 必须为冻结版本
    "resolve_by": "identity.historical_cycle_id",             // ★ 唯一合并键
    "mode": "INDEX_ONLY —— 本快照只存 identity / structural_status / strict_structural_supported。",
    "reader_must": "读取方必须先校验该 artifact 的 rule_set_version 与本字段一致，再按 resolve_by 合并。"
  }
}
```

**硬约束**：

1. `historical_candidates` **非空**时 `candidates_source` **必填**（`V8b`）；为空时可写 `null`。
2. `rule_set_version` **必须**是冻结的 `structural-analogy-ruleset-v0.3` —— 防止回指到非冻结产物。
3. `resolve_by` **固定**为 `identity.historical_cycle_id`。
4. 读取方**必须**先校验目标 artifact 的 `rule_set_version` 与本字段一致；**不一致即拒绝合并**（不得静默降级）。

> **回指取回的字段**（**不在**快照内复制）：`theme_relation` · `dimensions` ·
> `supported/unknown/unsupported_dimensions` · `why_similar` · `why_not_similar` ·
> `dimension_evidence` · `background_sources` · `governance_context` · `supplementary_context`。
>
> ★ 这条规则的意义：**冻结的研究结论只有一份**（在 SA artifact 里），快照只引用它。
> 若快照复制一份，两者就可能漂移 —— 回指从结构上消除了这种可能。

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
