# WORKER_OPERATING_RULES.md — Research Worker 运行边界

> 本文件是本 Workspace 中 Research Agent 的**操作边界**。
> 与 `HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md` 一致；冲突时以 Protocol 为准。

---

## 1. 可以做

| 能力 | 交付位置 |
|---|---|
| 搜索历史资料 | `04_RESEARCH/`（过程）→ `05_OUTPUT/sources.json` |
| **使用互联网进行历史研究** | — |
| 形成 campaign candidate | `05_OUTPUT/candidates.json` |
| 建 Evidence | `05_OUTPUT/evidence.json` |
| 建 Source | `05_OUTPUT/sources.json` |
| 提出 lifecycle | `candidates[].lifecycle` |
| 提出 drivers（四问） | `candidates[].drivers` |
| 提出 exclusions（**强制**） | `05_OUTPUT/exclusions.json` |
| 提出 conflicts | `05_OUTPUT/conflicts.json` |
| 提出 cross-task notes | `manifest.json` |
| 形成 research questions | `05_OUTPUT/research_questions.json` |
| 提出 macro theme proposal | `manifest.json` |

---

## 2. 不可以做

| 禁止 | 原因 |
|---|---|
| ❌ 修改 SQLite | 研究产物不等于 canonical 事实 |
| ❌ 修改 schema | Research Model v1.0 冻结 |
| ❌ 修改 canonical Theme | canonicalization 属 ThreeC Agent |
| ❌ 修改现有 Campaign | 已冻结结论不得被新轮次覆盖 |
| ❌ 修改 Export | 唯一交换目录，只由 exporter 写入 |
| ❌ 修改 Product | 职责分离 |
| ❌ 创建 canonical DB ID（`C-*` / `RC-*` / `CC-*` / `TH-*` / `rule_*` / `summer_*`） | 必须用 intake-local `R01-<SCOPE>-<SEQ>` |
| ❌ 宣称 `VERIFIED` | 只能用 `PROVISIONAL` / `CONFLICT` / `INSUFFICIENT` |
| ❌ 创建 ranking | 产品禁止 |
| ❌ 创建 score | 产品禁止 |
| ❌ 创建 probability | 产品禁止 |
| ❌ 创建 prediction / forecast | 产品禁止 |
| ❌ 为数量制造 Campaign | 见下方 §4 |
| ❌ 因重复而自行删除 candidate | 见下方 §5 |

> 本 Workspace 中没有 SQLite / DB dump / `src/` / `exports/` ——
> 上述禁止项在本 Workspace 内**物理上也不可行**。

---

## 3. Point-in-Time 纪律（硬性）

> **「事后知道」≠「当时知道」。**

每条 Evidence 必须标注 `support_kind`：

| 值 | 能用于 | 不能用于 |
|---|---|---|
| `historical_fact_support` | 证明**历史事件确实发生** | 证明当时已知 |
| `point_in_time_support` | 证明**当时**已知 | — |
| `retrospective_context` | 复盘 / 反例 / 结果解释 | **不得**充当启动或主升的同期催化 |

一致性规则（validator 强制）：

- `support_kind` 含 `point_in_time_support` → `temporal_relation` 必须是 `contemporaneous` 或 `prior`
- `temporal_relation` 为 `subsequent` / `retrospective` → **必须**填 `point_in_time_note`
- `temporal_relation` 为 `retrospective` → `support_kind` **必须**含 `retrospective_context`

---

## 4. 没有数量 KPI

> **不存在**「每个行业至少 3 个 Campaign」「必须达到 30 个案例」「必须提高 STRUCTURAL_SUPPORTED 数量」。

数字只能用于**描述实际覆盖**、做 Coverage Audit、判断研究是否明显不足。

**不得**为了填满行业而把边缘事件升级为 Campaign。
`quality_summary.no_quantity_kpi_acknowledged` **必须为 `true`**。

**没有可靠证据的领域允许保持空缺** —— 空缺是**合法研究状态**，用 `exclusions` 显式记录。

---

## 5. 重复优先：宁可重复提交

> ## **宁可重复提交，也不要因为可能重复而删除候选。**

- `candidate_id` **只要求本任务内唯一**
- 跨任务重复**由 ThreeC Agent 做 dedupe**
- 重复候选**必须**标记 `possible_duplicate_of`
- 跨任务提示写入 `cross_task_notes`（`POSSIBLE_DUPLICATE` / `OVERLAP` / `BOUNDARY` / `HANDOFF`）

**漏掉一个候选的代价，远高于让 ThreeC Agent 做一次 merge。**

---

## 6. 日期纪律

**不要求**把日期研究到 VERIFIED。四种精度都合法：

`EXACT_DATE` · `DATE_WINDOW` · `PHASE_WINDOW` · `UNKNOWN`

> **方向正确优先于过度精确；高价值案例以后可以再做 date verification。**

**禁止**为了得到一个「漂亮日期」而**强制选择**一个口径。
日期存在分歧时，**保留双方**（`alternative_dates` / `conflicts`），**不得自动取舍**。

---

## 7. Evidence 独立性

> **同一新闻被多个网站转载 ≠ 多个独立 Evidence。**

必须使用 `independence_group`；并主动标记 `same_origin` / `retelling` / `primary_source`。

Confirmed 门槛（沿用既有）：**≥2 条 Evidence 且 ≥2 个 `independence_group`**。

---

## 8. exclusions 强制

每个 Task **必须**提交 `exclusions[]`，且**不得为空**。

必须记录：为什么某热门事件没进 Campaign · 为什么某案例是单股事件 ·
为什么两个候选属同一 Campaign · 为什么某案例证据不足 · 为什么某主题不能建立独立 Macro Theme。

**目的：防止只收集成功案例。**

---

## 9. 交付与校验

```bash
# 交付位置（唯一）
05_OUTPUT/

# 校验
python tools/validate_historical_research_intake.py 05_OUTPUT
python tools/validate_historical_research_intake.py --check
python tools/test_validate_historical_research_intake.py
```

**必须 0 FAIL 才能交付。**

---

## 10. 边界提醒

> Research Worker 可以提出 **proposal / overlap / boundary**；
> 但 **Macro Theme canonicalization 只能由 ThreeC Agent 的 CMTR v1 完成**。
> Research Worker **不得**自行发明第二套 Macro Theme Resolution。
