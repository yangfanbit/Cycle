# Structural Analogy Explanation Artifact v0.1

> | 项目 | 值 |
> |---|---|
> | 性质 | **Research-derived / Product-facing Artifact**（`docs/ROADMAP.md` **Step 2** 交付物） |
> | 完成日期 | 2026-09-19 |
> | Artifact | `research/research/reports/structural_analogy_explanations_v0_1.json` |
> | 生成器 | `research/scripts/build_structural_analogy_explanation_v0_1.py`（deterministic，支持 `--check`） |
> | 规则来源 | **`Structural Analogy Rule Set v0.2`**（唯一规则来源） |
> | 源 artifact | `research/research/reports/structural_analogy_research_v0_2.json` |
> | 不修改 | `src/**` · schema.sql · export contract v1.0 · 任何旧产物 |

---

## 1. 契约（Contract）

```
Consumer  : Product
Mode      : READ_ONLY —— Product **不得重新实现** Structural Analogy 规则
Rule src  : Structural Analogy Rule Set v0.2（唯一规则来源）
Snapshot  : 2026-09-15
Coverage  : 5 candidates × 17 historical cycles = 85 explanations
```

> **Product 只消费 Research 结果。** 任何维度判定都已在 Research 侧完成并冻结。

### 明确不是（`not_a`）

`score` · `percentage` · `probability` · `winner` · `ranking` · `top analogue` ·
`best analogue` · `investment advice` · `prediction` · `trading signal`

生成器内置**禁止字段自检**：扫描全部数据字段名，命中即 `FAIL`。

---

## 2. Artifact 结构

```jsonc
{
  "artifact": "structural_analogy_explanations",
  "artifact_version": "0.1",
  "rule_set": "Structural Analogy Rule Set v0.2",
  "rule_set_version": "structural-analogy-ruleset-v0.2",
  "snapshot_date": "2026-09-15",
  "status_vocabulary": [ ... ],          // 5 级
  "dimension_vocabulary": { ... },        // 4 维各自的状态词表
  "dimension_naming": {                   // ★ Driver 分层命名（review §6）
    "evidence_category": { "label_zh": "证据类别", "values": ["POLICY", ...] },
    "mechanism_driver":  { "label_zh": "驱动机制", "values": ["POLICY_DRIVEN", ...] }
  },
  "semantics": { ... },                   // UNKNOWN ≠ 不存在 / theme 仅 metadata / 无排序
  "candidates": [
    {
      "candidate_id": "...",
      "display_name": "...",
      "macro_theme": "...",
      "current_structural_profile": { ... },   // current_phase / 机制 / 证据类别 / 事件类型 / gaps
      "summary": { "STRUCTURAL_SUPPORTED": 1, ... },
      "explanations": [
        {
          "historical_campaign_id": "...",
          "historical_cycle_id": "...",
          "snapshot_date": "2026-09-15",
          "rule_set_version": "structural-analogy-ruleset-v0.2",
          "structural_status": "STRUCTURAL_SUPPORTED",
          "strict_structural_supported": true,
          "theme_relation": "CROSS_MACRO_THEME",
          "dimensions": {
            "lifecycle":        { "status": "...", "candidate_phase": "...",
                                  "historical_stage_at_comparable_point": "...",
                                  "forbidden_comparison": "..." },
            "mechanism_driver": { "status": "...", "quality": "...", "overlap": [...], "axis": "机制轴" },
            "evidence_sequence":{ "status": "...", "subtype": "..." },
            "event_structure":  { "status": "...", "quality": "..." }
          },
          "supported_dimensions":  [ ... ],
          "unknown_dimensions":    [ ... ],
          "unsupported_dimensions":[ ... ],
          "why_similar":      [ "..." ],
          "why_not_similar":  [ "..." ],
          "provenance": [
            { "source": "candidate_evidence",        "evidence_ids": [...] },
            { "source": "historical_driver_evidence","canonical_driver": "...", "entries": [...] },
            { "source": "historical_events",         "event_ids": [...] }
          ],
          "supplementary_context": { "market_structure": "SUPPLEMENTARY_ONLY", ... }
        }
      ]
    }
  ],
  "coverage": { "candidates": 5, "explanations": 85, "by_status": { ... } }
}
```

---

## 3. 与 review §7 的字段对应

| review §7 要求 | artifact 实现 |
|---|---|
| `candidate_id` | `candidates[].candidate_id` |
| `historical_campaign_id` | `explanations[].historical_campaign_id` |
| `snapshot_date` | 顶层 + 每条 explanation |
| `rule_set_version` | 顶层 + 每条 explanation |
| `structural_status` | `explanations[].structural_status` |
| `theme_relation` | `explanations[].theme_relation`（**metadata only**） |
| `dimensions: lifecycle / mechanism_driver / evidence_sequence / event_structure` | ✅ 同名 |
| `supported_dimensions[]` | ✅ |
| `unknown_dimensions[]` | ✅ |
| `unsupported_dimensions[]` | ✅ |
| `why_similar[]` | ✅（**由结构维度派生，不含任何分数**） |
| `why_not_similar[]` | ✅（含 mismatch / unknown / 跨族背景） |
| `provenance[]` | ✅（candidate evidence + 历史 driver 证据 + 历史事件） |

---

## 4. Driver 分层命名（review §6 落实）

| 层 | 中文 | 英文 | 取值 | 含义 |
|---|---|---|---|---|
| 1 | **证据类别** | Evidence Category | `POLICY` / `INDUSTRY` / `CAPITAL` / `SENTIMENT` / `EXTERNAL` | 「公司公告」是一类**证据来源** |
| 2 | **驱动机制** | Mechanism Driver | `POLICY_DRIVEN` / `INDUSTRY_UPGRADE` / `TECH_BREAKTHROUGH` / `DEMAND_SURGE` / `SUPPLY_CONTRACTION` / `VALUATION_RESET` / `CYCLE_REVERSAL` / `EVENT_CATALYST` | 「产业升级」是一个**机制判断** |

> **产品文案不要把两者都简称「Driver」。**
> 在 artifact 中：`current_structural_profile.evidence_categories` = 层 1；
> `current_structural_profile.mechanism_drivers` 与 `dimensions.mechanism_driver` = 层 2。

---

## 5. 语义红线（Product 必须遵守）

1. **`UNKNOWN` / `NOT_AVAILABLE` ≠ 现象不存在** —— 表示**当前资料不足以编码**。
2. **`theme_relation` 不参与** Structural Status 判定，仅为背景 metadata；
   **不得**据此升降级。
3. **无排序**：artifact 不提供任何排序、分数或概率；
   `explanations[]` 的排列顺序仅为**确定性排序**（等级序 → cycle id），**不是排名**。
4. **Market / Temporal 为 `SUPPLEMENTARY_ONLY`**，不参与 Structural Status。
5. **Product 不得重新计算**四个维度 —— 必须直接读取 artifact 中的判定与 provenance。

---

## 6. 本轮覆盖（2026-09-15 snapshot）

| structural_status | 条数 |
|---|---:|
| `STRUCTURAL_SUPPORTED` | **4** |
| `STRUCTURAL_PARTIAL` | **36** |
| `THEME_ONLY` | **3** |
| `INSUFFICIENT_EVIDENCE` | **5** |
| `NO_VALID_CORRESPONDENCE` | **37** |
| **合计** | **85** |

与 `Structural Analogy Research v0.2` 的计数**完全一致**（本 artifact 不重新判定）。

---

## 7. 下一步（不在本阶段）

`docs/ROADMAP.md` **Step 3 · Product Adapter**：
`Research Structural Analogy Artifact → Product View Model`（无 ranking / score，
不猜测 `UNKNOWN` / `NOT_AVAILABLE`，保留 provenance，不破坏现有 Timeline / Calendar / Lifecycle）。

**本阶段未做**：任何 `src/**` 改动 · UI · Product Adapter · Wave 1C · 规则调整。

---

*文档结束 · Structural Analogy Explanation Artifact v0.1 · 2026-09-19*
