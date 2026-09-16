# Time Observation Discovery v0.4

> **ThreeC 全量历史时间结构扫描 · 派生结构门（Derivation Gate）轮**
>
> | 项目 | 值 |
> |---|---|
> | 文件性质 | **Research Layer Deliverable**（研究层交付物） |
> | 轮次 | `time-observation-discovery-v0.4` |
> | 规则集 | `time-observation-discovery-0.4` |
> | 口径规则集 | `canonical-macro-theme-resolution-1`（CMTR v1，**未变**） |
> | 快照日期 | 2026-09-16 |
> | 生成器 | `research/scripts/discover_time_observation_patterns.py`（deterministic，`--check` 逐字节一致） |
> | 对比工具 | `research/scripts/compare_time_observation_rounds.py`（本轮新增，只读） |
> | 上游 | `Time_Observation_Discovery_v0_3.md`（其 §6.3 / §9-D1 提出的待决问题，本轮回答） |
> | 产物 | `time_observation_candidate_pool_v0_4.json` / `.csv` |
>
> **本阶段未修改** `src/` / Timeline / `exports/` / `contracts/` / `schema.sql` / DB 数据 / Product Artifact。
> **不进入** Structural Historical Analogy。

---

## 0. 一句话结论

> **本轮回答 v0.3 留下的唯一待决问题（D1），并把 `lifecycle_rhythm` 早已陈述的研究立场
> 落进 Promotion Gate —— 不是新增标准，而是让 Gate 与既有研究结论一致。**
>
> **结果：有效 `TIMELINE_CANDIDATE` 由 4 条降为 2 条；有效独立结构由 2 个降为 1 个。**
>
> **这个「1」才是诚实数字** —— 此前那个「2」里的第 2 个结构（`MAIN_RISE`）经本脚本自身的节奏判定，
> 其中心（06-22）可由「EARLY_SIGNAL 中心（06-11）+ 中位滞后（10 d）」解释，**残差仅 1 天**。
> 它不是独立规律，而是 EARLY_SIGNAL 结构的**派生呈现**。
>
> **注意方向：这是收紧，不是放宽。** 门槛链只增不减，宁少不多，**不制造 Pattern**。

---

## 1. 本轮做了什么（唯一变化）

### 1.1 问题（v0.3 §6.3 原文）

> **「`derived_from_early_signal = true` 是否应作为 Promotion Gate 的降级理由？」**
>
> v0.3 时该判定**只出现在 `lifecycle_rhythm` 报告里，未被 Promotion Gate 使用**，
> 导致 2 个派生结构以 `TIMELINE_CANDIDATE` 身份出现（`TOPC-004` / `TOPC-021`）。
> v0.3 明确**不擅自改规则**，将其记入决策点 D1。

### 1.2 本轮决定

**采纳。** 理由：

| 论据 | 说明 |
|---|---|
| **不是新标准** | `lifecycle_rhythm` 已独立判定这些结构为「派生：非独立证据」。Gate 不采纳它 = Gate 与自家研究报告互相矛盾 |
| **方向是收紧** | 只降级、不升级；不会增加任何 Pattern 数量 |
| **残差判据保守** | 阈值 21 天，远大于实际残差（`MAIN_RISE` 仅 1 天），不会误伤真实独立结构 |
| **可审计** | 判定结果写入 `derivation_verdict`，含逐阶段明细与理由，可回溯 |

### 1.3 实现（口径已固化为轮次档案）

```python
ROUND_PROFILES = {
    "0.2": {"direct_resolution": True,  "derivation_gate": False},  # 复现 v0.2
    "0.3": {"direct_resolution": False, "derivation_gate": False},  # 复现 v0.3
    "0.4": {"direct_resolution": False, "derivation_gate": True},   # 当前轮
}
```

- `--round X` **一并恢复该轮口径**，使历史轮次产物可逐字节复现（回归比对的前提）。
- 未知轮次**显式 FAIL**，不静默降级为默认口径。
- 新增字段 `candidates[].derivation_verdict = {is_derived, stage_verdicts, reason}`。

---

## 2. 零行为变化证明（关键验证）

为证明「**除派生门之外没有任何其他行为变化**」，本轮保留两个 legacy 开关，
并用新增的对比工具做**逐字节回归**：

```bash
# ① v0.4（默认口径）逐字节自洽
python research/scripts/discover_time_observation_patterns.py --check
#   → PASS —— 磁盘产物与重算结果逐字节一致（deterministic）。

# ② 用 v0.3 口径复现 v0.3 产物 → 逐字节比对
python research/scripts/discover_time_observation_patterns.py --round 0.3 --legacy-no-derivation-gate --check
#   → PASS

# ③ 用 v0.2 口径复现 v0.2 产物 → 逐字节比对
python research/scripts/discover_time_observation_patterns.py --round 0.2 --legacy-direct-resolution --check
#   → PASS

# ④ 未知轮次必须 FAIL（守卫有效性）
python research/scripts/discover_time_observation_patterns.py --round 9.9 --check
#   → FAIL —— 未知轮次 9.9。已知轮次：0.2, 0.3, 0.4（exit=1）
```

> **结论：本轮改动是行为中性的（除派生门外）。**
> ①②③ 三个 `--check` 全 PASS，说明 v0.4 与 v0.3 的**全部**差异都只可能来自派生门本身，
> 不存在任何未声明的副作用。④ 证明守卫真的会拦。

---

## 3. 派生结构门：判定逻辑

### 3.1 判据

对某 scope 的某个阶段：

```
预测中心 = EARLY_SIGNAL 中心 + 该阶段相对 EARLY_SIGNAL 起点的中位滞后
残差     = |实际中心 − 预测中心|
```

- **残差 ≤ 21 天** → 该阶段中心可由 EARLY_SIGNAL 聚集解释 → `derived_from_early_signal = true`。
- 含义：该阶段的**时间位置不含超出 EARLY_SIGNAL 的额外信息**，故不能作为独立规律。

### 3.2 三值判定（**关键设计：只降不升**）

| `is_derived` | 条件 | Gate 动作 |
|---|---|---|
| `True` | 该候选的**全部**阶段都判定为派生 | **降级**为 `EXPLORATORY` |
| `False` | 该候选至少一个阶段**明确非派生** | 不动作（保留原状态） |
| `None` | 存在**无节奏判定**的阶段（阶段不在 export 10 阶段内，或该阶段样本 < 3） | **不下结论，不动作** |

> ⚠️ **`False` 在本轮为 0 条** —— 这不是缺陷，而是本门的**单向性**：
> 它只输出「判定派生」或「不下结论」，**从不主动断言「非派生」**。
> 这与 Promotion Gate「状态门只降不升」的原则一致，避免把「证据不足」误当作「已证清白」。

---

## 4. 结果 diff（修正后的归因）

> 归因工具：`research/scripts/compare_time_observation_rounds.py --from 0.3 --to 0.4`
> 该工具严格区分「字段新增（结构性，by design）」与「字段值变化（实质性）」。

### 4.1 scan_map

| 指标 | v0.3 | v0.4 | 变化 |
|---|---:|---:|---|
| 扫描候选总数 | 191 | 191 | — |
| `TIMELINE_CANDIDATE`（原始） | 4 | 4 | — |
| **`effective TIMELINE_CANDIDATE`** | **4** | **2** | **−2** |
| **有效独立结构数** | **2** | **1** | **−1** |
| `EXPLORATORY` | 44 | **46** | +2 |
| `INSUFFICIENT_DATA` | 119 | 119 | — |
| `REJECTED` | 12 | 12 | — |
| `RESEARCH_ONLY` | 12 | 12 | — |

### 4.2 实质性变化：恰好 2 条候选（**全部可归因**）

| pattern_id | scope | 阶段 | 变化 |
|---|---|---|---|
| `TOPC-004` | THEME_FAMILY/`TH-AUTO` | MAIN_RISE | `effective` TIMELINE_CANDIDATE → **EXPLORATORY** |
| `TOPC-021` | RULE/`rule_auto_summer` | MAIN_RISE | `effective` TIMELINE_CANDIDATE → **EXPLORATORY** |

两条的降级理由相同（写入 `effective_status_reason`）：

> 通过数值门槛且口径稳健，但时间位置可由「EARLY_SIGNAL 中心 + 中位滞后」解释（残差 ≤ 21 天）
> → 属 EARLY_SIGNAL 聚集的**派生结果**，不含额外时间信息 → 降级为 EXPLORATORY，不得作为独立规律。

**除这 2 条外，191 个候选的字段值无任何变化。**

### 4.3 结构性变化（by design，不计为「结论变化」）

| 类型 | 内容 |
|---|---|
| 新增字段 | `candidates[].derivation_verdict` |
| 口径文本 | `promotion_gate.TIMELINE_CANDIDATE` / `promotion_gate.note` 增补派生门说明 |
| 版本号 | `ruleset_version` 0.3 → 0.4 |

---

## 5. 派生判定的完整账目（191 = 139 + 22 + 30）

| 桶 | 候选数 | `is_derived` | 说明 |
|---|---:|---|---|
| ① scope **无**节奏分析 | **139** | `None` | 无 rhythm 判定 → 不下结论 → 不动作 |
| ② 有节奏分析，但含**非 export 阶段** | **22** | `None` | 含 `PHASE_*` / `DB_*` / `RETRACEMENT` / `FIRST_DECLINE` 等无节奏判定的阶段 |
| ③ 有节奏分析，**全部阶段派生** | **30** | `True` | 判定为派生；若原为 `TIMELINE_CANDIDATE` 则降级 |
| | **191** | | ✅ 账目闭合 |

**桶 ② 明细**：其中 2 条为 EARLY_SIGNAL-only（`TOPC-001` / `TOPC-018`，即锚点自身，不可能「由自己派生」），
其余 20 条含 `PHASE_*` / `DB_*` 等非 export 阶段。

### 5.1 ★ 派生范围远超「只有 MAIN_RISE」

有节奏分析的两个 scope（`rule_auto_summer` / `TH-AUTO`）**各 7 个阶段全部派生**：

| 阶段 | n | 中心 | 中位滞后 | 预测中心 | 残差 | 派生 |
|---|---:|---|---:|---|---:|---|
| `THEME_FORMING` | 3 | 06-14 | 9 d | 06-20 | 6 d | ✅ |
| `BROAD_CONFIRMATION` | 4 | 06-29 | 25 d | 07-06 | 7 d | ✅ |
| `MAIN_RISE` | 7 | 06-22 | 10 d | 06-21 | **1 d** | ✅ |
| `PEAK` | 7 | 07-11 | 40 d | 07-21 | 10 d | ✅ |
| `SECONDARY` | 4 | 08-12 | 68.5 d | 08-18 | 6.5 d | ✅ |
| `DECLINING` | 4 | 08-04 | 61.5 d | 08-12 | 7.5 d | ✅ |
| `MAIN_END` | 7 | 08-31 | 70 d | 08-20 | 11 d | ✅ |

> **这是本轮最重要的结构性认识：**
> 汽车夏季主题的**整条生命周期**（从 `THEME_FORMING` 到 `MAIN_END`）的时间位置，
> **都可由 EARLY_SIGNAL 锚点 + 各阶段中位滞后推出**。
> 即：**EARLY_SIGNAL 是本数据集里唯一的时间信息来源**，其余阶段皆为它的下游回声。
>
> **门的「影响面」小（仅 2 条候选被降级），但「覆盖面」广（30 条候选被判定为派生）** ——
> 因为其余派生结构此前已因其他理由（口径脆弱 / 样本不足）落在 `EXPLORATORY` 之下，
> Gate 对它们已无可再降。**这正说明本门是「补齐最后一道口子」，而非制造新的淘汰。**

---

## 6. TOP-01 回归（PASS）

| 项目 | 期望（Phase 7.2 canonical） | 实测（v0.4） |
|---|---|---|
| pattern_id | — | `TOPC-018` |
| N | 7 | **7** ✅ |
| 中心 | 06-11 | **06-11** ✅ |
| 窗口 | 05-27 ~ 06-26 | **05-27 ~ 06-26** ✅ |
| 复现 | 5/7 | **5/7** ✅ |

> TOP-01 走 `RULE` scope（谓词 = `rule_id` 匹配），**不依赖 `theme_family_id`**，
> 且其为 EARLY_SIGNAL 阶段（派生门的基线本身）→ **天然不受本门影响**，回归 PASS 属预期，不是巧合。
>
> `5 / 7` 只能表述为「历史 7 个观测年份中有 5 个落入该观察窗口」，**不得**表述为未来概率。

---

## 7. 有效候选与独立结构（v0.4 终态）

| pattern_id | scope | 阶段 | N | 中心 | 窗口 | 集中度 | p | 复现 | 稳健性 |
|---|---|---|---|---:|---|---|---:|---:|---|
| `TOPC-018` | RULE/`rule_auto_summer` | EARLY_SIGNAL | 7 | 06-11 | 05-27~06-26 | 0.4018 | 0.00389 | 5/7 | ROBUST |
| `TOPC-001` | THEME_FAMILY/`TH-AUTO` | EARLY_SIGNAL | 7 | 06-11 | 05-27~06-26 | 0.4018 | 0.00389 | 5/7 | ROBUST |

- 2 条 → **1 个独立样本结构**（`member_signature` 完全相同）。
- `theme_family_count = 1`（全部汽车族）· `theme_cycle_count = 7` · `campaign_count = 7`。
- 机制：`CALENDAR_DRIVEN` + `POLICY_CADENCE` + `REPORTING_CADENCE` + `DATA_RELEASE_CADENCE`（置信度 MEDIUM）。

> **实质结论：独立稳健时间结构 = 1 个。**
> 这是本项目自 Phase 7.2 以来**始终未变**的结论 —— v0.3 曾短暂显示「2」，
> 本轮确认那第 2 个是派生结果。**数字回到 1，但依据比 v0.2 时更硬。**

---

## 8. 诚实限制清单

1. **独立稳健时间结构 = 1 个**（TOP-01，汽车夏季 EARLY_SIGNAL）。
   本轮**没有**增加任何 Pattern；相反，剔除了 1 个此前被误列为独立的结构。
2. **派生门只对 2 个有节奏分析的 scope 生效**（`rule_auto_summer` / `TH-AUTO`）。
   其余 18 个 scope **无节奏分析** → `is_derived = None` → 本门**无法**对它们下结论。
   这**不是**「已证非派生」，而是「无证据」。**不得**把 `None` 读作「独立」。
3. **`is_derived = False` 为 0 条** —— 本门是单向的（只降不升），从不主动断言「非派生」。
4. **`theme_family_count` 仍 = 1**（所有有效候选均为汽车族）→ **跨族稳健性仍无法检验**。
   本轮**没有**改善这一点。
5. **`华为汽车` taxonomy 缺口未修**（`RC-2023-HUAWEI` → `UNRESOLVED_NAME`）。
   属**数据决策**（已登记 DEFER 项 `F7`），不在本轮范围内。
6. **核验比例 0 / 24**，全部 `confidence = low` → 数据质量上限不变。
7. **交易日历仅覆盖 2.6 / 8 年** → 时间统计仍只能退化为自然日口径。
8. **残差阈值 21 天为既有设定**（`lifecycle_rhythm` 早已使用），本轮**未调整**。
   若未来调整该阈值，属**规则变更**，必须单独留痕。
9. 本报告**只描述过去**。**不得**出现概率 / 胜率 / 买卖信号 / 推荐分 / 目标价 / 收益率预测。

---

## 9. 下一轮决策点（不擅自执行）

| # | 决策点 | 状态 |
|---|---|---|
| **D1** | `derived_from_early_signal` 是否进入 Promotion Gate？ | ✅ **本轮已决（采纳）** |
| **D2** | 是否补录 `华为汽车` 到 `themes` 表（`F7`）？ | ⏳ 待决 · 属历史数据变更 |
| **D3** | `Historical Coverage Audit` 是否升级 v0.2 并消费 v0.4 候选池？ | ⏳ 待决 · 属独立轮次 |
| **D4** | Wave 1 数据扩容（电力设备 / 信息通信） | ⏳ 待决 · v0.3 已判「口径稳定，可以进入」 |

> **推荐顺序**：D4（数据扩容）→ D3（审计升级）→ D2（随扩容一并处理）。
> **理由**：D1 已决，规则链稳定。当前**真正的瓶颈是数据**（跨族稳健性无法检验、
> 交易日历覆盖不足、核验比例为 0）—— 继续在 1 个结构上做方法学微调，
> 边际收益低于扩大样本。**先扩数据，再谈结构。**

---

## 10. 复现方式

```bash
# 生成 v0.4（canonical 口径 + 派生门）
python research/scripts/discover_time_observation_patterns.py

# 校验确定性（逐字节一致）+ TOP-01 回归
python research/scripts/discover_time_observation_patterns.py --check

# 生成并打印摘要
python research/scripts/discover_time_observation_patterns.py --print

# ★ 回归：复现历史轮次（证明口径演进可追溯、零副作用）
python research/scripts/discover_time_observation_patterns.py --round 0.3 --legacy-no-derivation-gate --check
python research/scripts/discover_time_observation_patterns.py --round 0.2 --legacy-direct-resolution --check

# ★ 轮次归因对比（本轮新增工具）
python research/scripts/compare_time_observation_rounds.py --from 0.3 --to 0.4
```

退出码：`0` = 通过；`1` = 自检 / TOP-01 回归 / 未知轮次失败（**不写文件**）。

---

## 11. 边界声明

```text
schema changed        : NO
export changed        : NO
historical data changed: NO
breaking change       : NO
```

- 未修改 `src/` / Timeline / PWA / 前端交互。
- 未修改 `exports/timeline_export_v1.json` / `contracts/` / `schema.sql`。
- 未修改 DB 任何一行数据（生成器只读）。
- 未修改 Product Artifact（`time_observation_patterns_v0_1.json`）——
  该生成器只读 export + verification，**不依赖候选池**，故 Product 侧零影响。
- `time_observation_candidate_pool_v0_2.*` / `v0_3.*` **保留未删**，作为口径演进的可比基线。

---

*报告结束 · Time Observation Discovery v0.4 · 2026-09-16*
