# Time Observation Discovery v0.5

> | 项目 | 值 |
> |---|---|
> | 轮次 | `round_id = 0.5` · `research_round = time-observation-discovery-v0.5` |
> | 完成日期 | 2026-09-18 |
> | 性质 | **四族齐备后的首次完整 Time Observation 新研究轮次**（Research-only） |
> | 起始状态 | `HEAD = origin/main = d3fa89f`，ahead/behind `0/0`，工作树 clean（**自行核对**） |
> | 产物 | `time_observation_candidate_pool_v0_5.{json,csv}` · `time_observation_candidate_diff_v0_4_to_v0_5.json` · 本报告 |
> | 未覆盖 | **v0.2 / v0.3 / v0.4 全部产物逐字节保留** |

**核心问题**：经过历史数据扩容与口径统一后，ThreeC 的时间型历史结构是否**仍然只有 1 个**独立稳健结构？
**答案（由运行结果决定）**：**是。仍为 1。**

---

## 0. ROUND_PROFILE 0.5（§五）

新增独立档案（**未复用 v0.4 条目**）：

```python
"0.5": {"direct_resolution": False, "derivation_gate": True,
        "label": "四族齐备后的首次完整重跑（4 个 Macro Theme：AUTO / PHARMA / POWER / COMM；canonical CMTR v1 + 派生结构门）"}
```

| 维度 | v0.5 取值 |
|---|---|
| dataset scope | 2018-01-01 ~ 2025-12-31；**观测年 2019–2025**；2018 = `no_clear_campaign`（**保留既有语义，未删**） |
| data snapshot | export `source_commit` 见 `input_snapshot`；DB = Phase 7.4B 之后 |
| taxonomy version | **canonical-macro-theme-resolution-1（CMTR v1）**；root = 4 |
| discovery script version | `time-observation-discovery-0.5` |
| ruleset version | `time-observation-discovery-0.5` |
| promotion gate version | 与 v0.4 相同（含派生结构门）—— **口径不变量** |
| statistics version | 与 v0.4 相同（N / 集中度 / 窗口 / recurrence / stability / LOO）—— **未调整任何阈值** |
| input artifact identifiers | `exports/timeline_export_v1.json` · `research/database/cycle_research.db` · `theme_taxonomy.py` |

**口径不变量声明**：`direct_resolution` / `derivation_gate` 与 v0.4 **完全一致**；
本轮**未**调整 N 阈值、concentration、LOO、stability 或 Promotion Gate 任何规则。

---

## 1. Dataset

| 指标 | v0.4 | v0.5 |
|---|---:|---:|
| Macro Themes | 3 | **4**（+`TH-COMM`） |
| Theme Cycles | 11 | **13** |
| Campaigns | 11 | **13** |
| Research Candidates | 4 | 4 |
| Evidence | 67 | **83** |
| Events（DB / export） | 39 / 42 | **49 / 52** |
| Years（观测） | 2019–2025 | 2019–2025 |
| anchor_records | — | **105** |
| transition_records | — | **77** |
| db_phase_records | — | **69** |
| event_records | — | **52** |

**taxonomy 解析实测**：`RESOLVED 16 / CONFLICT 0 / UNRESOLVED_NAME 1 / NO_THEME 0`；
root = `TH-AUTO` · `TH-COMM` · `TH-PHARMA` · `TH-POWER`。

---

## 2. Discovery

| 指标 | v0.4 | v0.5 |
|---|---:|---:|
| **Raw candidates** | 191 | **315**（+124） |
| **distinct samples** | 89 | **139** |
| duplicate_scope_candidates | 102 | 176 |
| **N ≥ 3** | 72 | **81** |
| **N ≥ 5** | 30 | **34** |
| concentration ≤ 0.45 | 69 | 79 |
| p ≤ 0.05 | 49 | **50** |
| **Bonferroni 通过** | `TOPC-113, TOPC-130` | **`[]`（无）** |
| expected false positives @0.05 | 1.5 | **1.7** |
| Bonferroni 阈值 | 0.000262 | **0.000159** |
| **TIMELINE_CANDIDATE（原始）** | 4 | 4 |
| **effective TIMELINE_CANDIDATE** | 2 | 2 |
| **★ independent structures（effective distinct）** | **1** | **1** |

**状态分布**：`EXPLORATORY 43` · `INSUFFICIENT_DATA 234` · `REJECTED 32` · `RESEARCH_ONLY 2` · `TIMELINE_CANDIDATE 4`。

**pattern_type 覆盖**（§九）：`PHASE_TRANSITION` · `CALENDAR_DRIVEN` · `SEASONAL` · `HOLIDAY_RELATIVE` 均产出候选；
`INDUSTRY_EVENT_DRIVEN` / `DATA_RELEASE_DRIVEN` **未出现** → 记为 **`NOT_AVAILABLE`**（不是 `NO_PATTERN`）：
仓库无行业事件日历 / 制度性数据发布日历的结构化数据。

**Absolute vs Relative**（§十）：`absolute_vs_relative` 与 `holiday_offsets` 字段在全部候选中保留；
TOP-01 的春节相对时间替代解释比较沿用既有 20% advantage / `INCONCLUSIVE_SIMILAR` 规则，**未改动**。

---

## 3. v0.4 → v0.5 Diff（§十八）

**匹配键** = `(scope_type, scope_id, lifecycle_stage, pattern_type)`（`pattern_id` 为扫描序，跨轮次不可比）。

| 项 | 值 |
|---|---:|
| v0.4 候选 | 191 |
| v0.5 候选 | 315 |
| **键相同（共有）** | **191** |
| 仅 v0.4（消失） | **0** |
| 仅 v0.5（新增） | **124** |
| 共有中数值完全一致 | **164** |
| 共有中数值变化 | 27 |
| 共有中状态变化 | **16** |

**状态迁移矩阵**：

| v0.4 → v0.5 | 条数 | |
|---|---:|---|
| INSUFFICIENT_DATA → INSUFFICIENT_DATA | 114 | |
| EXPLORATORY → EXPLORATORY | 43 | |
| REJECTED → REJECTED | 12 | |
| **RESEARCH_ONLY → REJECTED** | **10** | ← 变化 |
| **INSUFFICIENT_DATA → REJECTED** | **5** | ← 变化 |
| TIMELINE_CANDIDATE → TIMELINE_CANDIDATE | 4 | |
| RESEARCH_ONLY → RESEARCH_ONLY | 2 | |
| **EXPLORATORY → REJECTED** | **1** | ← 变化 |

**★ 关键归因**：**全部 16 处状态变化均为「降级 → REJECTED」，无任何升级**；
且**全部发生在 `scope_type ∈ {ALL, EVENT_TYPE}` 的跨库聚合候选上**。

**降级原因（实测，均为正当统计理由）**：
- `IQR = 122.0 ~ 136.8 天` → 锚点跨三个以上季节，无法构建有意义的观察窗口（不得人为造窗口）
- `留一法显示结果由单一年份主导（最大中心位移 50.0 天）` → 不构成时间规律

**归因**：新增 POWER / COMM 后，这些「跨全库」候选的锚点被新对象的**异季锚点**稀释 →
离散度（IQR）暴增 → 触发既有 REJECTED 规则。
**这是数据扩容带来的正当筛选，不是规则变更。**

**变化归因分类**（§十八 要求，不允许「莫名其妙变化」）：
- 数据扩容（data expansion）：16 处降级 + 27 处数值变化 —— 全部可追溯
- taxonomy canonicalization：**0 处**（v0.4 已是 canonical）
- evidence normalization：**0 处**（`evidence_type` 不参与时间模式计算）
- new gate：**0 处**（派生门与 v0.4 相同）

---

## 4. TOP-01 Regression（§十九）

**TOPC-018**（`rule_auto_summer · EARLY_SIGNAL`）—— 全项逐项比对：

| 项 | v0.4 | v0.5 | |
|---|---|---|---|
| `N` | 7 | **7** | ✅ |
| `center` | 06-11 | **06-11** | ✅ |
| `window` | 05-27 ~ 06-26 | **05-27 ~ 06-26** | ✅ |
| `recurrence` | 5/7 | **5/7** | ✅ |
| `concentration_ratio` | 0.4018 | **0.4018** | ✅ |
| `stability.status` | SPLIT | **SPLIT** | ✅ |
| `stability.front_back` | STABLE | **STABLE** | ✅ |
| `loo_max_shift_days` | 5.0 | **5.0** | ✅ |
| `single_year_dominance` | False | **False** | ✅ |
| `dispersion.iqr_days` | 16.0 | **16.0** | ✅ |
| `promotion_status` | TIMELINE_CANDIDATE | **TIMELINE_CANDIDATE** | ✅ |
| `effective_promotion_status` | TIMELINE_CANDIDATE | **TIMELINE_CANDIDATE** | ✅ |
| `years` | 2019–2025 | **2019–2025** | ✅ |
| `recurrence_years` | [2020,2021,2023,2024,2025] | **同** | ✅ |
| `theme_family_count` | 1 | **1** | ✅ |

**→ 全项完全一致，无一处变化。** 生成器内置 `top01_regression` 亦报 **`status: PASS`**。

**为什么它不变**：TOP-01 的观测集合 = `rule_auto_summer` 的 7 个年度锚点，
全部来自 `TH-AUTO`；Wave 1A/1B 新增的是 **POWER / COMM 的对象**，
不进入 `rule_auto_summer` 的成员集合 → **N 与全部派生统计量天然不变**。

---

## 5. Cross-family（§十一）

### 5.1 候选的 `theme_family_count` 分布

| theme_family_count | 候选数 |
|---:|---:|
| 0 | 6 |
| 1 | **284** |
| 2 | 4 |
| 3 | 11 |
| 4 | 10 |

→ **跨族候选共 25 条（7.9%）**。

### 5.2 ★ 25 条跨族候选**全部**是 `ALL:ALL` 跨库聚合，且**无一可用**

| effective 状态 | 条数 |
|---|---:|
| REJECTED | 21 |
| RESEARCH_ONLY | 4 |
| **TIMELINE_CANDIDATE** | **0** |

**→ 跨族候选的 `TIMELINE_CANDIDATE` = 0。不存在任何跨族稳健时间结构。**

### 5.3 各家族候选产出（`scope_type = THEME_FAMILY`）

| Macro Theme | 候选数 | 状态分布 | 最大 N |
|---|---:|---|---:|
| **`TH-AUTO`** | 26 | TIMELINE_CANDIDATE 2 · EXPLORATORY 17 · INSUFFICIENT_DATA 7 | **7** |
| `TH-PHARMA` | 24 | REJECTED 2 · INSUFFICIENT_DATA 22 | **3** |
| **`TH-POWER`** | **0** | — | **0** |
| **`TH-COMM`** | **0** | — | **0** |

**★ 关键结论**：`TH-POWER` 与 `TH-COMM` **各自只有 2 个 Theme Cycle**，
低于 `THEME_FAMILY` 级扫描的 **N ≥ 3** 门槛 → **不产出任何 family 级候选**。

**非 AUTO 的 THEME / THEME_FAMILY 候选共 151 条，其中 `RESEARCH_ONLY` / `TIMELINE_CANDIDATE` = 0 条。**

### 5.4 逐问回答（§十一 的 5 问）

| # | 问题 | 答案 |
|---|---|---|
| 1 | 原 TOP-01 是否仍然成立？ | ✅ **成立，全项未变** |
| 2 | 原候选是否因跨族而消失？ | ❌ 无消失（`only_v0_4 = 0`）；但有 **16 条跨库候选被降级为 REJECTED** |
| 3 | 是否产生新的跨族候选？ | ⚠️ 新增跨族候选全部落在 `ALL:ALL`，且 **21/25 REJECTED、4/25 RESEARCH_ONLY、0 晋级** |
| 4 | 某候选是否只由单族驱动？ | ✅ **两个 TIMELINE_CANDIDATE 全部只由 `TH-AUTO` 单族驱动**（`theme_family_count = 1`） |
| 5 | `theme_family_count` 是否真正改善？ | ⚠️ **数据侧改善（3 → 4），但结构侧未改善** —— `N` 提升未转化为 `independent_theme_family_count` 提升 |

### 5.5 ★ `N` vs `independent_theme_family_count`（§十一 要求区分）

| 概念 | v0.4 | v0.5 | 说明 |
|---|---:|---:|---|
| `N`（TOP-01 样本量） | 7 | **7** | 未变 |
| **`independent_theme_family_count`** | **1** | **1** | **未变** —— 仍是只有 `TH-AUTO` |
| 全库 Macro Theme 数 | 3 | 4 | 数据侧 +1 |
| 产出可用候选的家族数 | 1 | **1** | 只有 `TH-AUTO` |

→ **「四族齐备」提升的是数据覆盖，不是跨族证据。**

---

## 6. Primary / Related 与事实复制检查（§十二）

- 全部 13 个 Campaign 的 `theme_family_id` 由 CMTR v1 解析，**`CONFLICT = 0`** →
  不存在「同一历史事实通过标签复制增加 N」。
- 交叉检查 `AUTO × POWER` / `POWER × COMM` / `AI × COMM` / `AI × POWER`：
  实测**无任何 Campaign 同时归属 ≥2 个 Macro root**（`macro_theme_members` 中每个对象的
  `macro_theme_ids` 长度均为 1）→ **Related 未进入 `campaign_themes`，规则得到执行**。
- **`TH-COMM` 的 2 个 Cycle 与 `TH-POWER` 的 2 个 Cycle 之间无共享对象。**

---

## 7. Derived Structures（§十三 / §十六）

| `is_derived` | v0.4 | v0.5 |
|---|---:|---:|
| `True` | 30 | **30** |
| `None` | 161 | 285 |
| `False` | 0 | 0 |

- **全部 30 条 `is_derived = True` 的候选均来自 `TH-AUTO`**
  （`THEME_FAMILY:TH-AUTO` 或 `RULE:rule_auto_summer`），
  `derived_from_pattern_id` 分别为 `TOPC-001` / `TOPC-018`（即 EARLY_SIGNAL 结构）。
- 其中 26 条被降级为 `EXPLORATORY`、4 条为 `INSUFFICIENT_DATA`。
- **`None` 的语义**：v0.4 的 161 → v0.5 的 285（新增 124 条新候选**全部**为 `None`）——
  即**无节奏判定 / 缺字段 = 无证据**，**不等于独立**（沿用既有语义，未改）。
- **未恢复 v0.3 的错误**：`derived structure` **从未**被计为 `independent structure`。
- **TOP-01（TOPC-018）本身不是派生结构**（`is_derived = None`，它是 EARLY_SIGNAL 的源头）。

---

## 8. Small-sample 与假阳性（§十四 / §十七）

| 分层 | 候选数 |
|---|---:|
| N < 3 | 234 |
| N = 3–4 | 47 |
| **N ≥ 5** | **34** |

**N ≥ 5 且 concentration ≤ 0.45 且 effective 非 INSUFFICIENT/REJECTED 的候选 = 16 条**，
其中：
- `THEME_FAMILY:TH-AUTO` / `RULE:rule_auto_summer`：**14 条**（全部 `TH-AUTO` 单族）
- `ALL:ALL`：2 条（`TOPC-062 MAIN_END` / `TOPC-166 PEAK->MAIN_END`）——
  实测其成员同样由 AUTO 主导，且**与 AUTO 的 stage 候选高度重叠**（属同一结构的切面）

**→ 无任何非 AUTO 候选进入「N ≥ 5 且高集中度」的强候选集合。**

**多重比较（§十七）**：
- 扫描空间 191 → **315**（+65%）
- Bonferroni 阈值随之收紧 0.000262 → **0.000159**
- **通过 Bonferroni 的候选由 2 条降为 0 条**

> **这是本轮最重要的统计观察之一**：v0.4 中看似最强的 `TOPC-113` / `TOPC-130`
> 在新扫描空间下**不再通过 Bonferroni**。它们本就是 `is_derived = True` 的 AUTO 派生切面。
> → **扫描空间扩大后，原先「最漂亮」的 p 值消失了** —— 这正是多重比较校正应有的行为，
> 也印证了「不因某个 p 值很小就晋级」的既有纪律。

---

## 9. Lifecycle Rhythm 去重与结构计数（§十六 / §二十）

**`candidate_overlap`（Jaccard ≥ 0.5）**：

| | v0.4 | v0.5 |
|---|---:|---:|
| TIMELINE_CANDIDATE 条数 | 4 | 4 |
| **distinct structures** | **2** | **2** |
| 结构分组 | `TOPC-001:[001,018]` · `TOPC-004:[004,021]` | **同** |

**`timeline_candidate_robustness`**：`robust_count 4 / fragile_count 0 / untested_count 0`（与 v0.4 相同）。

**结构计数链**：

```
4 条 TIMELINE_CANDIDATE
  → candidate_overlap 去重 → 2 个 distinct structures
      （① AUTO EARLY_SIGNAL；② AUTO MAIN_RISE）
  → 派生门排除 ② （MAIN_RISE 是 EARLY_SIGNAL + 中位滞后 10d 的派生结果，残差 1d）
  → effective distinct structures = 1
```

**effective TIMELINE_CANDIDATE = `['TOPC-001', 'TOPC-018']`**（两者 Jaccard = 1.0，同一结构）。

### ★ 最终指标

> **v0.4 independent structures = 1**
> **v0.5 independent structures = 1**
>
> - 新结构：**0**
> - 消失结构：**0**
> - 合并结构：**0**
> - 降级结构：**0**（16 条降级均为 `ALL` / `EVENT_TYPE` 跨库候选，**不属任何独立结构**）

---

## 10. Mechanism

- 唯一独立结构（AUTO EARLY_SIGNAL，上半年末窗口）的机制画像**未变**：
  `CALENDAR_DRIVEN` + 政策节奏（购置税 / 车展 / 半年报窗口）——沿用既有记录，**未重新推断**。
- POWER / COMM 的候选全部停留在 `INSUFFICIENT_DATA`（N ≤ 2 或 N = 3 且集中度不足），
  **不足以支撑机制推断** → 机制留空，未编造。

---

## 11. 最终结论（§二十七 汇总）

| 项 | 结果 |
|---|---|
| **Independent robust time structures** | **1** |
| 是否仍只有 1 个 | **是** |
| 是否因四族齐备而增加 | **否** |
| 跨族稳健结构 | **0** |
| 场景判定 | **情况 B**（仍只有 1 个独立结构） |

**为什么扩容没有带来新结构**（诚实归因）：

1. **POWER / COMM 各自只有 2 个 Theme Cycle** → 低于 `THEME_FAMILY` 级 N ≥ 3 门槛
   → **结构性地产不出 family 级候选**。这是样本量问题，不是方法问题。
2. **PHARMA 有 1 个 Cycle（N = 3）** → 全部 `INSUFFICIENT_DATA` / `REJECTED`。
3. **跨库（`ALL`）候选看似跨族，实则被新对象的异季锚点稀释** → 16 条降级为 `REJECTED`。
   → 数据扩容**削弱**了原本就脆弱的跨库伪模式 —— 这是质量提升，不是回归。
4. **唯一稳健结构（AUTO）本身未被触动** → 新增对象不进入其成员集合。

**结论**：ThreeC 的时间型历史结构**仍然只有 1 个独立稳健结构**。
数据扩容提升了**覆盖度与可信度**，但**未提升跨族证据强度**。

---

## 12. Determinism（§二十五）

```
run   --round 0.5          → 生成 v0_5.{json,csv}
check --round 0.5 --check  → PASS（逐字节一致）+ PASS（TOP-01 回归）
再 run / 再 check          → 最终以 --check 为准（报告文本修改后再跑，见 §14 验证记录）
```
- v0.2 / v0.3 / v0.4 产物**逐字节未改**。
- `ROUND_PROFILES` 新增 0.5 条目；v0.4 条目**未修改**。

---

## 13. Validation

| 项 | 结果 |
|---|---|
| `discover_time_observation_patterns.py --round 0.5 --check` | ✅ **PASS** |
| TOP-01 回归（内置） | ✅ **PASS** |
| `build_time_observation_patterns.py --check` | ✅ PASS |
| `audit_historical_coverage.py --round 0.3 --check` | ✅ PASS |
| 7 个 research 校验器 | ✅ 全 PASS |
| `npm test` / `tsc -b` / `build` | ✅ 395/395 · exit 0 · PASS |

---

## 14. Git（§二十六）

只提交 v0.5 相关文件与必要文档；未使用 `git add -A`；未 force push / amend / rebase / reset --hard。

**建议 commit message**：`research: run time observation discovery v0.5`

---

## 15. 明确回答

| 问题 | 回答 |
|---|---|
| schema changed | **NO** |
| timeline export contract changed | **NO** |
| 现有 Campaign 事实 changed | **NO** |
| Product（`src/**` / Artifact / UI）changed | **NO** |
| 阈值（N / concentration / LOO / stability / gate）changed | **NO** |
| breaking change | **NO** |

---

## 16. Next Recommendation（§二十八）

**场景 = 情况 B**（仍只有 1 个独立结构）。

> **建议：Time Observation 暂时冻结，重点转向 `Structural Analogy Feasibility Check`。**

理由：

1. 本轮已**穷尽**当前数据下的时间型结构空间（315 个候选、7 类模式、4 个 scope 层级）。
   唯一稳健结构仍是 AUTO EARLY_SIGNAL。**继续为了 Pattern 数量补数据，边际收益已极低。**
2. POWER / COMM 的瓶颈是**样本量（各 2 个 Cycle）**，不是方法。
   即便补到 N ≥ 3，也要先证明它们的时间结构**独立于 AUTO** —— 而本轮跨族候选 0 晋级，
   说明跨族证据本身很弱。
3. Structural Analogy 回答的是另一个问题（「当前候选在历史上像谁」），
   **不依赖新增时间结构**，且 `theme_family_count = 4` 已满足其最低门槛。

**不建议现在做 Wave 1C**：它会把 `theme_family_count` 推到 5，
但本轮证明**「家族数增加 ≠ 跨族证据增加」**——先做 Feasibility Check 更有效率。

**本轮未启动**：Wave 1C · Structural Analogy implementation · Product Integration。

---

*报告结束 · Time Observation Discovery v0.5 · 2026-09-18*
