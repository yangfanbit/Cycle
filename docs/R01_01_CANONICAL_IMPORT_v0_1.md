# R01-01 Canonical Import v0.1

> **性质**：R01-01 Intake Package → ThreeC Canonical DB → Export 的完整落地记录（§8.5）。
> **前置**：T01 taxonomy 已完成（`docs/T01_TAXONOMY_GAP_RESOLUTION_v0_1.md`）；
> 审查结论已定（`docs/R01_01_INTAKE_REVIEW_v0_1.md`：5 PROMOTE + 2 RESEARCH_ONLY）。
> **边界**：**未修改** schema / Research Model v1.0 / CMTR v1 / Structural Analogy Rule Set v0.2 /
> Time Observation v0.5 / Timeline Export Contract v1.0。

---

## 1. DB 新增了什么

| 表 | 导入前 | 导入后 | 增量 |
|---|---:|---:|---:|
| `research_rules` | 4 | **5** | +1 |
| `annual_reviews` | 28 | **33** | +5 |
| `campaigns` | 13 | **18** | **+5** |
| `sources` | 85 | **115** | +30 |
| `evidences` | 83 | **116** | +33 |
| `events` | 49 | **64** | +15 |
| `securities` | 48 | **64** | +16 |
| `campaign_themes` | 31 | **42** | +11 |
| `campaign_evidences` | 76 | **107** | +31 |
| `campaign_events` | 42 | **57** | +15 |
| `campaign_securities` | 51 | **72** | +21 |
| `campaign_phases` | 48 | **57** | +9 |
| `campaign_date_observations` | 24 | **38** | +14 |
| `themes` | 52 | 52 | 0（T01 已补） |

**既有 13 个 Campaign / 83 条 evidence / 85 个 source / 48 个 security / 4 条 rule /
28 条 annual_review / 所有桥表行 —— 逐行比对确认「被改动：无」。**

新增 `research_rules`：`rule_high_end_equipment`（高端装备历史周期观察，`base_pattern=高端装备`，`status=under_review`）。
新增 `annual_reviews`：`AR-HIEQ-{2016, 2018, 2020, 2023, 2024}`（2024 无 Campaign 引用 —— 该年只产出 2 个 Research Candidate）。

---

## 2. 5 个 PROMOTE 的 Canonical 记录

| intake | **canonical_id** | year | start | peak | end | class | strength | result | ev(IG) | events | sec | phases |
|---|---|---:|---|---|---|---|---|---|---:|---:|---:|---:|
| `R01-HIEQ-001` | **`C-2016-HIEQ-CONSTR`** | 2016 | 2016-08-01 | 2021-01-25 | 2021-12-31 | `industry_trend` | strong | positive | 8(8) | 3 | 4 | 2 |
| `R01-HIEQ-002` | **`C-2018-HIEQ-ROBOT-DOWN`** | 2018 | 2018-09-30 | 2019-09-30 | 2019-12-31 | `industry_trend` | medium | **weak** | 5(5) | 3 | 3 | 2 |
| `R01-HIEQ-003` | **`C-2020-HIEQ-AUTOMATION`** | 2020 | 2020-04-01 | 2021-07-01 | 2022-12-31 | `industry_trend` | strong | positive | 7(7) | 3 | 5 | 2 |
| `R01-HIEQ-004` | **`C-2023-HIEQ-ROBOT-PLUS`** | 2023 | 2023-01-19 | 2023-02-03 | **NULL** | `event_driven` | medium | positive | 4(4) | 2 | 4 | 1 |
| `R01-HIEQ-005` | **`C-2023-HIEQ-HUMANOID`** | 2023 | 2023-05-01 | 2023-11-02 | 2023-12-31 | `theme_campaign` | medium | positive | 7(6) | 4 | 5 | 2 |

**ThemeCycle**（Sequential Cycle）：
- `C-2018-HIEQ-ROBOT-DOWN` + `C-2020-HIEQ-AUTOMATION` → `hieq_robot_2018_2019` / `hieq_automation_2020_2022`
  （**同一 ThemeCycle 的两个 Campaign**：低谷分隔、方向相反、驱动变量不同）
- `C-2023-HIEQ-ROBOT-PLUS` + `C-2023-HIEQ-HUMANOID` → `hieq_robot_2023`

### 3 处**偏离包内提案**的 canonical 决策（均已记入 `campaigns.research_notes`）

| 项 | 包内提案 | canonical 采用 | 理由 |
|---|---|---|---|
| `campaign_year` | 2021 / 2019 / 2025 | **2016 / 2018 / 2024** | 既有 13/13 Campaign 的 `campaign_year` **一律等于 start 年份**；采用既有口径 |
| `C-2016-HIEQ-CONSTR` 的 `peak_date` | DATE_WINDOW 2021-01-25~2021-04-30 | **2021-01-25**（资产价格高点） | 既有 `peak_date` 语义为行情/资产价格高点（如 `C-2022-POWER-GRID` 2024-10-08）；产业销量峰值 2021-03-31 记入 `research_notes`（`CF004` KEEP_BOTH） |
| `C-2018-HIEQ-ROBOT-DOWN` 的 `result` | — | **`weak`** | ThreeC 首个「下行周期」型结构；`result=weak` 表示该段行情为**负向**，非「弱 Campaign」 |

### 跨 Campaign 证据消歧（`validate_batch_research` 强制 1 evidence : 1 campaign）

intake 中 2 条证据同属两个候选，canonical 化指定唯一归属：

| intake evidence | 归属 | 另一 Campaign 的对应覆盖 |
|---|---|---|
| `E009`（2018/2019/2020 产量） | → `C-2018-HIEQ-ROBOT-DOWN` | `C-2020-HIEQ-AUTOMATION` 由 `E-HIEQ-11`（2020 年 237068 套）覆盖 |
| `E016`（2022/2023 产量） | → `C-2023-HIEQ-ROBOT-PLUS` | `C-2020-HIEQ-AUTOMATION` 由 `E-HIEQ-14`（2022 上半年 −11%）覆盖 |

---

## 3. 2 个 RESEARCH_ONLY 如何保存

> **不进入 `campaigns` 表**（Research Model v1.0 §4：Campaign Candidate「**不能进入** `campaigns` 表，除非人工确认」）。

| intake | 表示位置 | 状态 |
|---|---|---|
| `R01-HIEQ-006` | 导出 `research_candidates[]` → **`RC-2024-HIEQ-EQUIP-UPDATE`** | `research_status = INSUFFICIENT` |
| `R01-HIEQ-007` | 导出 `research_candidates[]` → **`RC-2024-HIEQ-HUMANOID-MASS`** | `research_status = INSUFFICIENT` |

**与既有设计一致**：现有 4 个 `RC-*`（`RC-2023-HUAWEI` 等）在 DB 中**零存在**，仅由
`research/scripts/batch_auto_research.py` 的 `RESEARCH_CANDIDATES` 承载。本轮遵循同一设计：

- 2 个 RC 的 `campaigns` / `campaign_*` 桥表 / `campaign_date_observations` **均未写入**
- 其**专属** evidence（8 条）/ source（5 个）/ event（4 个）**亦未入 DB** —— 避免产生
  `orphan-supporting-evidence` 告警（DB 保持 **0 警告**）
- 其 research 内容完整保留在 **intake package**（git）+ **导出 `research_candidates`**（含
  themes / securities / events / lifecycle / drivers / notes）

> **未强行 Promote**：两者的市场侧证据均为 **0 条** → Campaign Independence Gate **Q1 无法验证**。

---

## 4. Evidence / Source / Security / Event 映射

| 项 | intake | 入 DB | 映射规则 |
|---|---:|---:|---|
| Source | 35 | **30** | `S001..S035` → `S-HIEQ-01..S-HIEQ-30`；跳过 RC 专属 5 个（`S002/S003/S019/S028/S029`） |
| Evidence | 41 | **33** | `E001..E041` → `E-HIEQ-01..E-HIEQ-33`；跳过 RC 专属 8 个（`E027..E034`）；`temporal_relation` / `independence_group` / `evidence_role` / `confidence` **原样保留** |
| Security | 17 | **16** | 大写助记符（既有 `BIDI` / `CATL` 风格）；★ `SEC017`「拓斯达（见 SEC008）」与 `SEC008` 为**同一标的** → **合并为 `TOPSTAR`**；`SEC015 兆威机电` / `SEC016 埃夫特` 的 ticker **保持为空**（包内未编造，不补） |
| Event | 19 | **15** | `EV-HIEQ-01..EV-HIEQ-15`；跳过 RC 专属 4 个 |
| CDO | — | **14** | `OBS-<canonical_id>-{start,peak,end}`，`candidate_date` 快照自 intake，`verified_date = NULL`（未经行情核验） |

**PIT 纪律**：所有 `subsequent` / `retrospective` 证据的 `point_in_time_note` 已写入
`evidences.description`（`｜PIT: …`）；`contradicting` 证据 `E-HIEQ-26`（2023-08-29 全市场普涨）
**单列保留**，未被删除。

**Conflict 保留**：`CF001/CF002/CF003/CF004/CF006`（KEEP_BOTH）与
**`CF005`（双飞股份 vs 双环传动）/ `CF007`（机器人 vs 工业自动化）/ `CF008`（人形机器人 1 or 2 Campaign）
三项 UNRESOLVED** 均记入 `campaigns.research_notes`，**未被静默删除**。

---

## 5. 新增 Theme 使用情况

| root | 使用的 Campaign 数 |
|---|---:|
| **高端装备**（新） | **5** |
| 汽车（既有） | 7 |
| 信息通信（既有） | 2 |
| 电力设备（既有） | 2 |
| 医药健康（既有） | 1 |
| **电子 · 资源 · 消费 · 金融 · 房地产 · 国防军工**（T01 新增） | **0**（等 R01-02~06） |

子主题使用：机器人 3 · 工程机械 1 · 工业自动化 1 · 人形机器人 1。
**T01 新增的 7 个 root 中只有「高端装备」在本轮被使用** —— 其余 6 个是 R01-02~06 的前置准备。

---

## 6. Export

**使用现有流程**：`research/scripts/batch_auto_research.py`（未修改 Timeline Export Contract v1.0）。

### 最小必要扩展（7 处）

| # | 位置 | 扩展 |
|---|---|---|
| 1 | `HIEQ_RULE` / `RULES` | 登记新 rule |
| 2 | `THEME_CYCLE` | +5 条 |
| 3 | `RESEARCH_CANDIDATES` | +2 条（`RC-2024-HIEQ-*`） |
| 4 | `CAMPAIGN_LIFECYCLE` | +5 条 |
| 5 | `CANDIDATE_LIFECYCLE` | +2 条 |
| 6 | `CAMPAIGN_DRIVERS` | +5 条（四问原样来自 intake） |
| 7 | `RULE_META` / `scope` | +1 rule 元数据 / scope 追加 |
| 8 | **写出换行** | `open(..., "w", encoding="utf-8")` → `open(..., "w", encoding="utf-8", newline="\n")`（`MANIFEST` / `CONFLICTS` / `EXPORT` 三处）。原实现在 Windows 文本模式下把 `\n` 转成 `\r\n`，使 canonical export **丢失 LF 不变量**（AGENTS.md §6）。修正后三个文件均恢复 LF。**不改内容、不改契约。** |

### ★ 修正一处既有**规则范围 bug**（为让新记录正确进入 Export 所必需）

```python
# 原：if e["year"] == 2018: continue
# 现：if e["year"] == 2018 and e["rule_id"] == AUTO_RULE: continue
```

「2018 = 反例年份（no_clear_campaign）」是 **`rule_auto_summer`（汽车）专属**的年度约定，
原实现按 `year == 2018` **全局**跳过，会误删其它 Rule 的 2018 年真实 Campaign
（如 `C-2018-HIEQ-ROBOT-DOWN`）。按 rule 限定后，**对既有数据行为完全一致**
（既有各 Rule 均无 2018 年 Campaign）。

### 导出结果

| 项 | 导入前 | 导入后 |
|---|---:|---:|
| `campaigns` | 13 | **18** |
| `research_candidates` | 4 | **6** |
| `rules` | 4 | **5** |
| `events` | 52 | **71** |
| `securities` | 63 | **94** |

新增 campaign 均带 `themes` / `lifecycle` / `drivers` / `conflicts` / `notes`；
`C-2023-HIEQ-ROBOT-PLUS` 的 `end_date` 为 `null`（**不虚构边界**）。

---

## 7. 全部 Validator 结果 → **PASS**

| 命令 | 结果 |
|---|---|
| `research/scripts/validate_db.py` | **PASS（0 FAIL / 0 WARNING）** |
| `research/scripts/validate_timeline_export.py` | **PASS（0 警告）** |
| `research/scripts/validate_batch_research.py` | **PASS（0 警告）** |
| `research/scripts/validate_promotion_manifest.py` | **PASS** |
| `research/scripts/check_doc_schema_consistency.py` | **PASS** |
| `research/scripts/validate_current_research.py` | **PASS** |
| `scripts/validate_monorepo_integrity.py` | **PASS（25 项）** |
| `refresh_current_research.py --check` | **PASS** |
| `validate_historical_research_intake.py --check` | **PASS** |

> 任务书 §3 写的 `research/scripts/monorepo_integrity.py` **路径不存在** —— 真实位置是仓库根
> `scripts/validate_monorepo_integrity.py`。

**幂等性**：导入器重复运行 → 「计划写入 0 行」✓
**既有数据零改动**：导入后逐表比对确认 ✓

---

## 8. Coverage 变化（客观记录，不夸大）

| 指标 | 导入前 | 导入后 | 变化 |
|---|---:|---:|---|
| Macro Theme 根节点 | 4 | **11** | +7（T01 补齐，本轮只用到 1 个） |
| **有 Campaign 的根节点** | **4** | **5** | **+1（高端装备）** |
| Historical Campaign | 13 | **18** | +5 |
| Research Candidate（导出层） | 4 | **6** | +2 |
| Historical Object（合计） | 17 | **22** | +5 |
| **跨族 Campaign 对（有数据的根）** | **C(4,2) = 6** | **C(5,2) = 10** | **+4（+67%）** |
| 机制轴覆盖 | 政策/技术突破/产业升级/需求爆发 | **+ 供给收缩 · 纯需求端 · 流动性·Beta · 订单·事件驱动（仅 taxonomy 层，尚无 Campaign）** | — |

### R01-01 实际新增的历史结构

1. **工程机械 2016–2021 更新+基建+环保周期**（`C-2016-HIEQ-CONSTR`）—— 首个「设备更新周期」结构
2. **工业机器人 2018–2019 下行周期**（`C-2018-HIEQ-ROBOT-DOWN`）—— ★ **ThreeC 首个「下行周期」型结构**
3. **工业自动化 2020–2022 复苏周期**（`C-2020-HIEQ-AUTOMATION`）
4. **「机器人+」政策驱动行情 2023-01**（`C-2023-HIEQ-ROBOT-PLUS`）—— `event_driven`，`end_date` NULL
5. **人形机器人产业叙事形成段 2023**（`C-2023-HIEQ-HUMANOID`）—— `theme_campaign`

### 未进入 Canonical

- `RC-2024-HIEQ-EQUIP-UPDATE`（设备更新政策）· `RC-2024-HIEQ-HUMANOID-MASS`（人形机器人量产）—— **RESEARCH_ONLY**

### R01-01 仍存在的证据缺口（来自 intake `quality_summary.known_gaps`）

1. **市场侧行情序列严重不足** —— 多数候选缺少连续板块指数 / 代表资产日线；006/007 **为零**
2. **Priority B（2015–2017）覆盖不完整** —— 2016-08 起的逐月一手序列未取得
3. **机制链条中间变量缺失** —— 制造业固投逐月序列 / 设备投资落地数据 / 人形机器人交付与收入确认
4. **一手政策原文获取不全** —— 《人形机器人创新发展指导意见》未取得 MIIT 原文页（`CF001` KEEP_BOTH）
5. **2023 年 2-4 月板块行情序列缺失** —— 导致 004 的 `end` 与 004/005 边界无法切分
6. **轨交装备采集不足** —— `INSUFFICIENT_EVIDENCE` 结论带有采集不足的不确定性

### Historical Universe 是否实际扩大

> **是，但幅度有限。** 有 Campaign 的机制家族 **4 → 5**（+1），
> 跨族 Campaign 对比空间 **6 → 10 对**（+67%），Historical Object **17 → 22**（+29%）。
> **11 个 root 中有 6 个仍无任何 Campaign**（电子 · 资源 · 消费 · 金融 · 房地产 · 国防军工）——
> 它们只是 **R01-02~06 的前置 taxonomy 准备**，本轮**未带来实际覆盖**。

### Structural Analogy 比较空间

理论上限 `C(11,2) = 55` 对；**实际有数据的族对为 `C(5,2) = 10`**（此前 6）。
R01-01 的 5 个新 Campaign 使**「汽车 ↔ 高端装备」等 4 个新族对**首次具备可比对象。

---

## 9. Structural Analogy 是否刷新

> ## **未刷新。**

| 依据 | 说明 |
|---|---|
| **冻结** | `Structural Analogy Rule Set v0.2`（§0：「后续 Research 轮次只执行规则，不再调规则」）与 `Structural Analogy Research v0.2` 均为 **FROZEN** |
| **AGENTS.md §4** | 「新增研究轮次必须新建 round / artifact，**不得覆盖旧轮次**」—— 重跑 v0.2 会**覆盖** `structural_analogy_explanations_v0_2.json` |
| **时序** | R01 尚有 5 个任务（R01-02~06）未执行；每次落库后刷新会产生 6 次无谓变更 |
| **本轮边界** | 任务 §7 明确：不修改 Rule Set v0.2 / 不新增规则 / 不重新设计算法 |

**建议**：R01 全部任务完成后，以**新 artifact 版本**（v0.3，规则不变）统一刷新，
而不是覆盖 v0.2。当前 `structural_analogy_explanations_v0_2.json`（`snapshot_date 2026-09-15`，
5 candidates）**保持字节不变**。

---

## 10. 剩余问题

1. **`CF005` / `CF007` / `CF008` 三项 UNRESOLVED** 仍未裁决（保留，未删除）
2. **`CF007`（机器人 vs 工业自动化）** 与 T01 的层级决策相关 —— T01 刻意未建「工业机器人」行，该冲突保持开放
3. **`campaign_year` 口径**：本轮采用既有「start 年份」口径，与包内提案在 3 处不同；若项目希望改为「主升年份」，需另起决策
4. **`C-2023-HIEQ-ROBOT-PLUS` 的 `end_date = NULL`**：待 `CF008` 裁决后回填
5. **6 个 root 仍无 Campaign**（电子 · 资源 · 消费 · 金融 · 房地产 · 国防军工）—— 需 R01-02~06
6. **市场侧行情数据缺口**：R01-01 多数候选缺少连续行情序列，限制了 Campaign Independence Gate Q1 的可验证性
7. **Structural Analogy 未刷新** —— 待 R01 完成后以新 artifact 版本统一处理
