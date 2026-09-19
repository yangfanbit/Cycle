# TASK_BRIEF.md — `R01-01`

> **task_status**: `PREPARED_NOT_STARTED`
> **research_round_id**: `R01`
> **source_threec_commit**: `2153f6d83b7481300696ab73d792e9e53aa31a07`

---

## 1. task_id

`R01-01`

## 2. scope

高端装备 / 机器人（含工业自动化、人形机器人、工程机械、轨交装备）

## 3. years

**2015–2025**

| 层级 | 年份 | 性质 | 要求 |
|---|---|---|---|
| **Priority A** | **2018–2025** | 当前 ThreeC 历史主宇宙的直接扩容区 | **必须独立可交付** |
| **Priority B** | **2015–2017** | 历史回填区 | 允许大面积 `INSUFFICIENT` |

> **不得**因 2015–2017 资料较难而**阻塞** 2018–2025 的产出。
> Priority A 的 package **不得**因为 Priority B 未完成而延后提交。

## 4. macro_theme_candidates

以下是**候选名称**，**不是**最终 Macro Theme：

- 高端装备
- 机器人
- 工业自动化
- 工程机械
- 轨道交通装备

> ⚠️ 最终 Macro Theme **必须**由 ThreeC Agent 走 **CMTR v1** 解析。
> Worker **不得**自行裁决。提交 `macro_theme_proposals` + `theme_name_candidates` 即可。

## 5. known_overlap

- R01-02（半导体/电子）：自动化设备的电子元器件与工控芯片边界
- R01-06（军工）：部分装备制造企业同时具备军民两用属性
- 已有 family「汽车」：`C-2024-ROBOTAXI` / `C-2025-ROBOTAXI` 与「机器人」在叙事上相邻
- 已有 family「电力设备」：工控与电力自动化存在企业重叠

## 6. known_ambiguity

- 「机器人」是独立 Macro Theme，还是「高端装备」下的 Theme / 子主题 —— 必须交 CMTR v1 判定，不得自行决定
- 「人形机器人」2023–2025 的多次行情是否属同一 Campaign（需走 Independence Gate Q1–Q5）
- 「工业自动化」与「机器人」是否同一底层主题的不同命名（Q1 Anti-example 风险）

## 7. excluded_scope

- 消费级电子产品与家电（属 R01-04）
- 纯军工订单驱动的装备（属 R01-06）
- 汽车整车与零部件（已有 family，不在本任务）
- 2015 年之前的装备行情

## 8. expected_output

**Research Intake Package** —— 按 `01_PROTOCOL/HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md` §5.3
的目录结构，交付到：

```text
05_OUTPUT/
├─ manifest.json
├─ coverage.md
├─ candidates.json
├─ evidence.json
├─ sources.json
├─ securities.json
├─ exclusions.json
├─ conflicts.json
├─ research_questions.json
├─ quality_summary.json
└─ checksums.sha256
```

**交付前必须通过**：

```bash
python tools/validate_historical_research_intake.py 05_OUTPUT
```

## 9. forbidden_actions

- 修改 canonical SQLite（research/database/cycle_research.db）
- 修改 research/schema/schema.sql
- 修改任何现有历史 Campaign / Evidence / Theme / Rule 结论
- 修改 DB themes 表（canonical Macro Theme taxonomy）
- 修改 src/**（Product）
- 修改 exports/timeline_export_v1.json
- 修改 Structural Analogy Rule Set v0.2
- 重跑 Time Observation
- 宣称产出为 VERIFIED
- 创造 canonical DB ID（C-* / RC-* / CC-* / TH-* / rule_* / summer_*）
- 新增 SQLite 表 / 列 / 实体
- 建立 ranking / score / probability / prediction / 胜率 / 目标价 / 推荐
- 覆盖已有 intake package 或同一 round 的旧 task package
- 因为与其他任务重复而自行删除候选
- 为了填满行业而把边缘事件升级为 Campaign
- 新增 DB themes 行（taxonomy 变更属独立轮次）

> **路径说明（REFERENCE ONLY）**：上表中出现的 `research/database/...` ·
> `research/schema/...` · `exports/...` · `src/...` 等路径属于 **ThreeC 主仓库**，
> **不在本 Workspace 内**。列出它们是为了说明「为什么本 Workspace 必须隔离」，
> **不是** Worker 需要访问的路径 —— 本 Workspace 中**不存在**这些目录，
> 上述禁止项在这里**物理上也不可行**。
> Worker 的操作路径一律使用 **workspace-relative**（如 `05_OUTPUT/`、`tools/`、`01_PROTOCOL/`）。

---

## 10. 本任务特别提示

本任务对应新增方向「高端装备 / 机器人」。当前 baseline **完全没有**该方向的 Campaign —— 该族在 DB `themes` 中**不存在根节点**。

---

## 11. ⚠️ 没有数量目标

> **不存在**「每个行业至少 3 个 Campaign」「必须达到 30 个案例」
> 「必须提高 STRUCTURAL_SUPPORTED 数量」。

数字只能用于**描述实际覆盖**、做 Coverage Audit、判断研究是否明显不足。

**不得**为了填满行业而把边缘事件升级为 Campaign。
**没有可靠证据的领域允许保持空缺** —— 用 `exclusions` 显式记录。

---

## 12. 任务状态

**`PREPARED_NOT_STARTED`** —— 尚未开始。

**不得**把本任务写成 `STARTED`。
启动需**单独授权**。
