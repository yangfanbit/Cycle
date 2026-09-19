# TASK_BRIEF.md — `R01-05`

> **task_status**: `PREPARED_NOT_STARTED`
> **research_round_id**: `R01`
> **source_threec_commit**: `2153f6d83b7481300696ab73d792e9e53aa31a07`

---

## 1. task_id

`R01-05`

## 2. scope

金融 / 地产（含银行、券商、保险、多元金融、房地产开发、建材、建筑装饰）

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

- 金融
- 房地产
- 银行
- 非银金融
- 建筑材料

> ⚠️ 最终 Macro Theme **必须**由 ThreeC Agent 走 **CMTR v1** 解析。
> Worker **不得**自行裁决。提交 `macro_theme_proposals` + `theme_name_candidates` 即可。

## 5. known_overlap

- R01-03（资源/化工）：建材与化工、基建需求
- R01-04（消费）：地产后周期与家电家居
- 「流动性 / 政策周期」是本任务的核心机制，但会与所有其他任务的**市场 Beta** 混淆

## 6. known_ambiguity

- ★ 本任务机制为**流动性与政策周期驱动**，与「政策驱动（POLICY_DRIVEN）」需要区分：前者是**货币/信用周期**，后者是**产业政策**
- ★★ Beta Contamination 风险最高：2018–2025 多次全市场行情会被误判为「金融 Campaign」（沿用 historical_campaign_validation_v1.md §4.3，无法排除时保持低置信度）
- 「券商行情」常常是市场 Beta 的代理 —— 是否构成独立 Campaign 需严格论证
- 地产政策（限购/信贷）与地产股行情的时间差需明确
- 「建材」属「地产链」还是独立行业，存在歧义

## 7. excluded_scope

- 纯宏观流动性研究（不是 Campaign）
- 商品期货行情
- 金融科技（倾向于「信息通信」或独立判定，本任务不强行纳入）

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

本任务对应新增方向「金融 / 地产」。当前 4 族**完全缺失「流动性 / 政策周期」机制轴**，且 **Beta Contamination 风险最高**。

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
