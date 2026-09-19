# R01-01 Intake Review v0.1 — 高端装备 / 机器人

> **性质**：ThreeC Agent 对 `research/intake/packages/R01-01/` 的**审查记录**（协议 §4 八种审查结果）。
> **状态**：Review / Dedupe / CMTR / Campaign Decision **已完成**；**Canonical DB 写入未执行**（见 §6）。
> **输入**：`research/intake/packages/R01-01/`（R01-HIEQ-*，7 候选 / 41 证据 / 35 来源 / 17 证券 / 10 排除 / 8 冲突 / 12 研究问题）
> **Intake provenance**：`source_commit = 2153f6d83f5724c0bab146a744c54fa562a7c45e`

---

## 0. Intake 验收

| 命令 | 结果 |
|---|---|
| `validate_historical_research_intake.py research/intake/packages/R01-01` | **PASS（24 checks, 0 FAIL, 0 WARN）** |
| `validate_historical_research_intake.py --check` | **PASS**（packages found: 1） |

**包质量评估**：机制轴组织（M1–M7）、PIT 三分、`same_origin` 标注、反证单列（E026）、
冲突 `KEEP_BOTH`/`UNRESOLVED` 保留、`exclusions` 10 项、无数量 KPI —— 均符合协议。
**未发现** canonical ID 冒用、评分/排序/预测字段、VERIFIED 声明。

---

## 1. §2 Review —— 逐候选审查

### 1.1 引用关系 / PIT / 独立性（机器可核验部分）

| candidate | ev | 独立 IG | role 分布 | temporal 分布 | PIT 支持 | ≥2 IG 门槛 |
|---|---:|---:|---|---|---:|---|
| `R01-HIEQ-001` 工程机械 2021 | 8 | **8** | supporting×8 | prior×2 / contemporaneous×2 / subsequent×4 | 4 | ✅ |
| `R01-HIEQ-002` 工业机器人下行 2019 | 5 | **5** | supporting×4 / context×1 | contemporaneous×3 / subsequent×2 | 3 | ✅ |
| `R01-HIEQ-003` 工业自动化复苏 2020 | 9 | **9** | supporting×8 / context×1 | subsequent×5 / contemporaneous×3 / retrospective×1 | 3 | ✅ |
| `R01-HIEQ-004` 机器人+政策 2023 | 4 | **4** | supporting×3 / context×1 | contemporaneous×3 / subsequent×1 | 3 | ✅ |
| `R01-HIEQ-005` 人形机器人叙事 2023 | 7 | **6** | supporting×6 / **contradicting×1** | contemporaneous×5 / subsequent×1 / retrospective×1 | 5 | ✅ |
| `R01-HIEQ-006` 设备更新政策 2024 | 4 | **4** | supporting×4 | contemporaneous×4 | 4 | ✅ |
| `R01-HIEQ-007` 人形机器人量产 2025 | 4 | **4** | supporting×3 / context×1 | retrospective×2 / contemporaneous×2 | **2** | ✅（临界） |

- **引用关系**：candidate→evidence / candidate→security / evidence→source 全部有效（validator C06/C07 PASS）。
- **Point-in-Time**：所有 `subsequent` / `retrospective` 证据均带 `point_in_time_note`；
  `retrospective` 均含 `retrospective_context`；`point_in_time_support` 均限于 `contemporaneous|prior`（C19 PASS）。
- **独立性**：`same_origin=true` 已显式标注 7 组（E005/E006、E015/E016、E022/E023、E024/E025、
  E033/E034、E007/E040/E041、E002/E038），不重复计入独立性 —— **符合 §7.2 纪律**。
- ★ **`R01-HIEQ-007` 的 E033 与 E034 同属 `IG-MEDIA-HUMANOID-*` 但实为两个 group**；
  包内已自述「E034 属厂商计划口径，与 E033 同源」→ **实际有效独立组低于表面值**，此为 007 判 INSUFFICIENT 的支撑证据之一。

### 1.2 重点对照对

#### `002` vs `003`（工业机器人下行 2018-09~2019-12 ↔ 工业自动化复苏 2020-03~2022-12）

| 判据 | 002 | 003 | 是否可分 |
|---|---|---|---|
| 时间 | 2018-09 → 2019-12 | 2020-03 → 2022-12 | **不重叠**（中间约 2 个月空档） |
| 方向 | **下行**（连续 13 个月负增长） | **上行**（2020-04→2021-06 主升） | ✅ 相反 |
| 驱动变量 | 制造业资本开支**收缩** + 汽车/电子下游下滑 | 资本开支**回补** + 自动化渗透率 | ✅ 不同 |
| 代表资产 | 埃斯顿 · 汇川技术 · 机器人(300024) | 埃斯顿 · 汇川技术 · 拓斯达 · 绿的谐波 · 步科股份 | ⚠️ **部分重叠**（埃斯顿/汇川） |
| 叙事 | 包内自述「独立主题叙事证据不足」→ `industry_trend` | 有行情证据（E012：2020-07 板块 +18.2%）→ `industry_trend` | — |

**判定**：**不合并**。二者由**一个低谷分隔、方向相反、驱动变量不同**，
符合 `theme_campaign_separation_v1.md` §5 **Pattern A（Sequential Cycle，顺序型）**
—— 即**同一 ThemeCycle 内的两个 Campaign**，而非同一 Campaign 的两个阶段。
> 依据：Gate **Q3（独立持续性）** 与 **Q4（独立生命周期）** 均成立；
> **Q5（残差检验）** 通过 —— 移除任一段，另一段仍可独立解释。
> **规则 3「不同时间 ≠ 不同 Campaign」不适用**：本判定不是「按时间切分」，
> 而是「方向 + 机制 + 生命周期」三重分离。

#### `004` vs `005`（机器人+政策 2023-01-19~02-03 ↔ 人形机器人叙事 2023-05~12）

| 判据 | 004 | 005 | 是否可分 |
|---|---|---|---|
| 注意力中心 | **工业机器人政策**（十七部门「机器人+」） | **人形机器人**（具身智能 / Optimus / 优必选） | ✅ **不同**（Q1 成立） |
| 催化类型 | 政策文本（`event_driven`） | 技术展示 + 产品代际 + 国家级政策（`theme_campaign`） | ✅ 不同 |
| 代表资产 | 埃斯顿 · 信邦智能 · 达意隆 · 双环传动 | 绿的谐波 · 步科股份 · 雷赛智能 · 兆威机电 · 埃夫特 | ⚠️ 无重叠 |
| 边界 | `end = UNKNOWN` | `start = DATE_WINDOW(2023-05-01~2023-08-29)` | ⚠️ **2023-03~04 无法切分** |

**判定**：**不合并**，但 **004 的 `end_date` 记为 NULL**（不得虚构边界）。
依据：Gate **Q1（独立注意力中心）成立**、Q2（代表资产组）**无重叠**、Q3/Q4/Q5 均成立。
> 二者同属一个 ThemeCycle（`hieq_robot_2023`），Pattern = **Sequential**。
> 2023-03~04 的未切分边界作为**已知限制**记录，不强行填补。

#### `005` vs `007`（人形机器人叙事 2023 ↔ 量产预期与国产加速 2024-09~2025）

| 判据 | 005 | 007 |
|---|---|---|
| 市场侧证据 | 有（E024/E025/E026，含单日涨停潮 + Beta 限定） | **完全缺失**（0 条行情证据） |
| 驱动机制 | 技术展示 + 叙事形成 | 量产规划 + 订单落地（中国移动 1.24 亿元） |
| 独立有效 IG | 6 | 4（其中 E033/E034 实际同源 → 有效更低） |
| Gate Q1 | 可验证 | **无法验证** |

**判定**：**不合并，且 007 不升级**。
- 005 → 独立 Campaign（其自身证据充分）
- 007 → **RESEARCH_ONLY**（`INSUFFICIENT`；市场侧证据为零，Q1 无法验证）
> 依据任务 §5：「007 当前为 INSUFFICIENT，**不得为了数量强行升级**」。
> 二者边界未切分（`CF008` UNRESOLVED）作为**未决问题**保留，不在本轮裁决。

### 1.3 其它逐项审查

| 项 | 结果 |
|---|---|
| **生命周期** | 7 个候选均有 lifecycle；001/003/004/005/006/007 使用 `MAIN_RISE/PEAK/DECLINING/RETRACEMENT` 标准枚举；002 为**下行周期**，其 `MAIN_RISE(None→2018-09-30)` 实为「前置上行背景」，包内已在 `why_not ①` 显式标注该语义偏移 —— **接受，但须在 canonical 记录中保留该说明** |
| **驱动机制** | 7 个候选四问（start/accelerator/turning/ending）**全部填满**（3–5 条/问），无占位符 |
| **标的归属** | ★ **发现 1 处重复**：`R01-HIEQ-SEC017`「拓斯达（国产产业链签约方，见 SEC008）」与 `R01-HIEQ-SEC008`「拓斯达 300607」为**同一标的的两条记录** → 合并为 1 条（保留 SEC008，SEC017 的角色说明并入 notes） |
| **标的 ticker 缺失** | `SEC015 兆威机电` / `SEC016 埃夫特` ticker 为空 —— 包内**未编造**，符合 AGENTS.md §3。Canonical 化时**保持为空**，不补 |
| **`why_campaign` / `why_not`** | 7/7 均有实质内容；`why_not` 均包含反证与限制（非形式化填充） |
| **冲突** | 8 项：`KEEP_BOTH`×5、`UNRESOLVED`×3（CF005 双飞股份归属 / CF007 机器人 vs 工业自动化 / CF008 人形机器人 1 or 2 Campaign）→ **全部保留**，不裁决 |
| **exclusions** | 10 项，覆盖 `SAME_CAMPAIGN` / `OBSERVATION_ONLY` / `OUT_OF_SCOPE` / `INSUFFICIENT_EVIDENCE` / `NOT_INDEPENDENT_MACRO_THEME` / `SINGLE_STOCK_EVENT` —— **反幸存者偏差纪律达成** |

---

## 2. §3 Cross-task Dedupe

### 2.1 与既有 4 个 family 的边界

| 既有 family | 潜在重叠 | 判定 |
|---|---|---|
| **汽车** | `C-2024-ROBOTAXI` / `C-2025-ROBOTAXI` / `C-2023-AD` 与「机器人」「人形机器人」叙事相邻；产业链（线控底盘、传感器、电机）部分共享 | **无底层对象重合**。R01-01 全部候选的驱动机制为制造业资本开支 / 设备更新 / 产业政策 / 产业叙事 / 技术突破，**无一以智驾或 Robotaxi 为驱动**。`cross_task_notes CT003` 已声明。→ **不合并** |
| **电力设备** | 工控与电力自动化**企业重叠**（典型：汇川技术） | **企业重叠 ≠ Campaign 重叠**。`C-2020-POWER-NE`（光伏/风电发电设备）与 `C-2022-POWER-GRID`（电网/输变电）的驱动为**电力投资周期**；R01-01 的驱动为**制造业资本开支**。→ **不合并**；汇川技术在 R01-01 中按「工业自动化链条代表资产」记录（`CT004` 已声明不作裁决） |
| **信息通信** | 无实质重叠 | 无 |
| **医药健康** | 无实质重叠 | 无 |

### 2.2 与 R01-02 / R01-06 的边界

| 任务 | 边界 | 处理 |
|---|---|---|
| **R01-02 半导体 / 电子** | 半导体设备（前道/后道）属 R01-02 | R01-01 **未纳入任何半导体设备标的**，仅在核心零部件（伺服/减速器/控制器）层面涉及装备制造。→ **以 R01-02 为准**（`CT001`） |
| **R01-06 军工** | 军民两用装备（液压件、精密传动、机床） | R01-01 全部候选**均不含纯军工订单驱动**（`CT002`）。R01-06 未启动，无法反向核验 → 记为**待办** |

### 2.3 跨任务结论

- **未删除任何候选**（协议 §10 规则 4）。
- 跨任务重复提示 6 项（`CT001`–`CT006`）**全部保留**，其中 `CT005`（004↔005 边界）与
  `CT006`（002↔003 可能同 ThemeCycle）已由本审查按 Gate 裁决（见 §1.2）。

---

## 3. §4 CMTR v1 结果

**唯一实现**：`research/scripts/theme_taxonomy.py`（规则集 `canonical-macro-theme-resolution-1`）

```
现有 Macro Theme 根节点：['信息通信', '医药健康', '汽车', '电力设备']   （4 个）
```

| proposal | 提案名称 | proposal_kind | CMTR status | matched | unmatched |
|---|---|---|---|---|---|
| `MT001` | 高端装备 | `NEW_MACRO_CANDIDATE` | **UNRESOLVED_NAME** | — | 高端装备 / 高端装备制造 / 装备制造 |
| `MT002` | 机器人 | `SUB_THEME` | **UNRESOLVED_NAME** | — | 机器人 / 工业机器人 / 人形机器人 / 具身智能 |
| `MT003` | 工业自动化 | `SUB_THEME` | **UNRESOLVED_NAME** | — | 工业自动化 / 通用自动化 / 工控设备 / 自动化设备 |
| `MT004` | 工程机械 | `SUB_THEME` | **UNRESOLVED_NAME** | — | 工程机械 / 挖掘机 / 建筑机械 |
| `MT005` | 轨道交通装备 | `SUB_THEME` | **UNRESOLVED_NAME** | — | 轨道交通装备 / 轨交设备 / 铁路装备 |

**候选级 `theme_name_candidates` 全量解析**：15 个名称 → **全部 `UNRESOLVED_NAME`**，0 matched。

> ★ **结论**：DB `themes` 表中**不存在**本任务任一方向的行。
> CMTR v1 如实报告 `UNRESOLVED_NAME`，**不发明 taxonomy 行**（沿用 `F7` 先例）。

**本审查未创建任何 canonical Theme。**

> ✅ **后续（T01，2026-09-19）**：taxonomy gap 已由**独立轮次 T01** 解决 ——
> 新增 7 个 root（含「高端装备」）+ 26 个子主题，`themes` 19 → 52 行。
> **R01-01 的 5 个提案与 7 个候选现已全部 `RESOLVED`**（均解析至根「高端装备」）。
> 见 `docs/T01_TAXONOMY_GAP_RESOLUTION_v0_1.md`。
> ⚠️ 本文件 §5「BLOCKED」与 §6 未决问题 1 的**历史结论保留**（记录当时状态）；
> Campaign 导入仍未执行。

---

## 4. §5 Campaign Decision

**依据**：Research Model v1.0 §5 + Campaign Independence Gate Q1–Q5 + `theme_campaign_separation_v1.md` §4 六条禁止规则

| candidate | year | 提案主题 | classification | research_status | confidence | **决定** |
|---|---:|---|---|---|---|---|
| `R01-HIEQ-001` | 2021 | 工程机械 | `industry_trend` | PROVISIONAL | high | **PROMOTE** |
| `R01-HIEQ-002` | 2019 | 机器人 | `industry_trend` | PROVISIONAL | high | **PROMOTE** |
| `R01-HIEQ-003` | 2020 | 工业自动化 | `industry_trend` | PROVISIONAL | high | **PROMOTE** |
| `R01-HIEQ-004` | 2023 | 机器人 | `event_driven` | PROVISIONAL | medium | **PROMOTE**（`end_date = NULL`） |
| `R01-HIEQ-005` | 2023 | 人形机器人 | `theme_campaign` | PROVISIONAL | medium | **PROMOTE** |
| `R01-HIEQ-006` | 2024 | 高端装备（设备更新） | `mixed` | **INSUFFICIENT** | low | **RESEARCH_ONLY** |
| `R01-HIEQ-007` | 2025 | 人形机器人 | `mixed` | **INSUFFICIENT** | low | **RESEARCH_ONLY** |

**无 `MERGE`、无 `EXCLUDE`**（002/003 与 004/005 均判定为 Sequential Cycle 的两个 Campaign，非 MERGE）。

### 4.1 `RESEARCH_ONLY` 的理由（不得升级）

**`R01-HIEQ-006` 设备更新政策 2024**
- 市场侧证据 **0 条** → Gate **Q1（独立注意力中心）无法验证**
- 行业口径过宽（11 个重点行业，含钢铁/有色/石化/化工/建材/电力）→ 与 R01-03 及「电力设备」实质重叠
- 政策与需求之间**缺少可验证的传导证据**
- 且其 4 个标的与 `R01-HIEQ-001` **完全重合**（三一重工/中联重科/徐工机械/恒立液压）
- → 保留为 **Research Candidate（`RC-*`）**，不进入 `campaigns`

**`R01-HIEQ-007` 人形机器人量产 2025**
- 市场侧证据 **0 条** → Gate **Q1 无法验证**
- `E033` 与 `E034` 实际同源 → 有效独立组不足
- `start` / `end` 均依赖回顾性来源（confidence = low）
- 与 `R01-HIEQ-005` 的边界未切分（`CF008` UNRESOLVED）
- → 保留为 **Research Candidate（`RC-*`）**，不进入 `campaigns`

### 4.2 未决冲突（保留，不裁决）

| conflict | 状态 | 说明 |
|---|---|---|
| `CF005` | **UNRESOLVED** | 2023-08-29 涨停潮「双飞股份」vs「双环传动」归属未定；未取得交易所口径当日明细 |
| `CF007` | **UNRESOLVED** | 「机器人」与「工业自动化」是否同一底层主题（Q1 Anti-example 风险）→ **必须由 CMTR/层级决策解决** |
| `CF008` | **UNRESOLVED** | 「人形机器人」2023–2025 应记为 1 个还是多个 Campaign |

---

## 5. §6 Canonical DB —— **未执行（BLOCKED）**

### 5.1 阻塞点

> **CMTR v1 对本任务全部 15 个主题名称返回 `UNRESOLVED_NAME`。**

要写入 `campaigns` + `campaign_themes`，必须先存在 canonical Macro Theme 根节点。
而**新增 taxonomy 行**在 ThreeC 现行治理下属于**独立数据决策轮次**：

| 出处 | 原文 |
|---|---|
| `research/scripts/theme_taxonomy.py`（`F7` 注释） | 「补录属数据决策，**须走独立轮次**（见 `docs/PROJECT_STATE.md`）」 |
| `research/intake/HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md` §11.1 | 「本协议**不修复**该缺口；补录属数据决策，**须走独立轮次**」 |
| `research/intake/HISTORICAL_UNIVERSE_COVERAGE_PLAN_v0_1.md` §3.3 | 「必须**单独轮次**处理，**不在 R01 内自动新增 taxonomy 行**」 |
| 本任务 §4 | 「**不能因为存在 proposal 就自动创建 canonical Theme**」 |

### 5.2 第二个阻塞点：Export 并非纯 DB 驱动

`exports/timeline_export_v1.json` 由 `research/scripts/batch_auto_research.py` 生成，而该脚本含
**硬编码的每-Campaign 元数据**：

| 硬编码位置 | 内容 |
|---|---|
| `RULES`（L39） | 4 个 rule 的白名单 |
| `RULE_META` | 每 rule 的 definition / observation_window |
| `CAMPAIGN_LIFECYCLE`（L307） | 按 `campaign_id` 的 lifecycle 数组 |
| `CAMPAIGN_DRIVERS`（L467） | 按 `campaign_id` 的四问归因 |
| `SIGNALS` / `RESEARCH_CANDIDATES` / `CONFLICT_MAP` | 研究信号 / 研究候选 / 冲突表 |
| `scope` 字符串（L905） | manifest 的范围描述 |

> 即：新增 Campaign 进入 Export **不只是插 DB 行**，还必须扩展该 Research 流水线脚本。
> 这是对**生成全部既有 canonical 数据的脚本**的修改，属于本轮之外的范围决策。

### 5.3 建议的最小执行路径（待授权）

**路径 A —— 新增 1 个根 + 4 个子主题**（与包内 `proposal_kind` 一致）

```
TH-HIEQ  高端装备            industry  （根）        ← MT001（唯一 NEW_MACRO_CANDIDATE）
├─ 工程机械                  industry                ← MT004
├─ 工业自动化                industry                ← MT003
├─ 机器人                    concept                 ← MT002
│  └─ 人形机器人             concept                 （2023 起注意力中心迁移）
└─ （轨道交通装备：不建立）                            ← MT005 无候选使用
```

- 新增 `research_rules` 1 行（`rule_high_end_equipment`）
- 新增 `annual_reviews`（rule × 年份）
- 5 个 PROMOTE 候选 → `campaigns`（`C-<YYYY>-<SLUG>`，**不使用 `R01-HIEQ-*`**）
- `RESEARCH_ONLY` 2 个 → `research_candidates`（`RC-*`）
- 41 证据 → `evidences` + `campaign_evidences`（保留 `temporal_relation` / `independence_group` / `same_origin`）
- 35 来源 → `sources`；17 证券 → 16（合并 `SEC017`）
- 扩展 `batch_auto_research.py` 的 `RULES` / `RULE_META` / `CAMPAIGN_LIFECYCLE` / `CAMPAIGN_DRIVERS` / `scope`
- 重跑 export → 验证 → Coverage Audit

**路径 B —— 先做 taxonomy 轮次，再落库**
把「新增 `高端装备` 根节点」单独作为一个最小授权轮次，R01-01 的 DB 写入顺延。

---

## 6. 未决问题（移交）

1. **taxonomy**：`高端装备` 是否应成为第 5 个 Macro Theme 根节点？`机器人` 是根还是子主题？（`CF007` 同源）
2. **`R01-HIEQ-002` 的 result 语义**：下行周期在 `result ∈ {positive,neutral,weak,failed,unknown}` 中应取何值？
   （既有 13 个 Campaign 中 **12 个 `positive` + 1 个 `weak`（`C-2019-AD`）**，**从未出现 `neutral` / `failed` / `unknown`**；
   本轮将首次引入「下行周期」型结构）
3. **`R01-HIEQ-004` 的 `end_date`**：保持 NULL（不虚构边界）还是留待 004/005 边界裁决后回填？
4. **`R01-HIEQ-001` 的 `campaign_year`**：包内提案 `2021`（峰值年），但 `start = 2016-08`（Priority B）。
   既有 13 个 Campaign 的 `campaign_year` **一律等于 start 年份** → 按既有口径应为 `2016`。
5. **`R01-HIEQ-006` 的标的与 001 完全重合**：`RC-*` 记录是否重复计入历史对象数？
6. **`CF005`**：双飞股份 vs 双环传动 —— 需交易所口径当日个股明细。
7. **`CF008`**：005 与 007 是否同一 Campaign。
