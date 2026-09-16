# Time Observation Discovery v0.3

> **ThreeC 全量历史时间结构扫描 · Canonical Macro Theme Resolution 回归轮**
>
> | 项目 | 值 |
> |---|---|
> | 文件性质 | **Research Layer Deliverable**（研究层交付物） |
> | 轮次 | `time-observation-discovery-v0.3` |
> | 规则集 | `time-observation-discovery-0.3` |
> | 口径规则集 | `canonical-macro-theme-resolution-1`（CMTR v1） |
> | 快照日期 | 2026-09-16 |
> | 生成器 | `research/scripts/discover_time_observation_patterns.py`（deterministic，`--check` 逐字节一致） |
> | 口径实现 | `research/scripts/theme_taxonomy.py`（**单一事实来源**） |
> | 上游 | `Time_Observation_Discovery_v0_2.md` · `Historical_Coverage_Audit_v0_1.md` |
> | 产物 | `time_observation_candidate_pool_v0_3.json` / `.csv` |
>
> **本阶段未修改** `src/` / Timeline / `exports/` / `contracts/` / `schema.sql` / DB 数据 / Product Artifact。
> **不进入** Structural Historical Analogy。

---

## 0. 一句话结论

> **本轮唯一的变化是修复 Macro Theme 归属口径。结果不是「发现更多规律」，而是「消掉一个伪差异」：**
>
> **v0.2 的 5 对「口径脆弱」全部归零（50/50 一致），两种 scope 口径下的 TOP-01 变体收敛为同一个样本集合。**
>
> **实质性独立稳健时间结构数量：仍然只有 1 个。**
> 新增的第 2 个「独立结构」经本脚本自身的 `lifecycle_rhythm` 判定为 **EARLY_SIGNAL 的派生结果（残差 1 天）** ——
> **不得**表述为「发现了 2 个规律」。

---

## 1. 本轮做了什么（唯一变化）

### 1.1 问题

`Historical_Coverage_Audit_v0_1.md` §2.2(d) 发现同一对象存在两种 Macro Theme 解析口径：

| 口径 | 判定方式 |
|---|---|
| `direct`（v0.2 使用） | 检查 `themes[]` 中是否**字面出现** Macro Theme 名称（如「汽车」） |
| `resolved`（canonical） | 沿 DB `themes.parent_theme_id` 链上溯至根节点 |

两者对**只登记子主题**的对象给出不同结果 → 同一「汽车主题族」存在两种不等价成员集合。

**受影响对象（4 个）**：

| 对象 | `themes` | `direct` | `resolved` |
|---|---|---|---|
| `C-2019-AD` | 智能驾驶/无人驾驶 | （空） | `TH-AUTO` |
| `RC-2024-SECONDARY` | Robotaxi/无人驾驶/智能网约车 | （空） | `TH-AUTO` |
| `RC-2020-PANDEMIC` | 疫情医疗 | （空） | `TH-PHARMA` |
| `RC-2021-TCM` | 中医药 | （空） | `TH-PHARMA` |

### 1.2 修复方式

新建 **`research/scripts/theme_taxonomy.py`** 作为 **canonical CMTR v1 单一事实来源**：

```
对象 Macro Theme = themes[] 名称
                   → DB `themes` 表归一化为 theme_id
                   → 沿 parent_theme_id 上溯至根
                   → 根节点集合
```

- **唯一事实来源是 DB `themes` 表**；不再接受硬编码「主题族名称表」。
- `discover_time_observation_patterns.py` 与 `audit_historical_coverage.py` **共用同一实现**（消除第二份口径）。
- 未解析名称**不静默丢弃** → `theme_resolution.unmatched_theme_names` 显式上报。
- `CONFLICT`（跨 Macro Theme）**不可归属，不得任选其一** → 返回 `None` 并计数（本轮 = 0）。

### 1.3 解析结果

| status | 数量 | 对象 |
|---|---:|---|
| `RESOLVED` | **12** | 9 Campaign + 3 RC |
| `CONFLICT` | **0** | — |
| `UNRESOLVED_NAME` | **1** | `RC-2023-HUAWEI`（题材「华为汽车」不在 `themes` 表 → 即已登记 DEFER 项 `F7`） |
| `NO_THEME` | **0** | — |

| Macro Theme | v0.2（`direct`） | v0.3（`resolved`） | 增量 |
|---|---:|---:|---|
| `TH-AUTO` 汽车 | 7 | **9** | `+C-2019-AD` `+RC-2024-SECONDARY` |
| `TH-PHARMA` 医药健康 | 1 | **3** | `+RC-2020-PANDEMIC` `+RC-2021-TCM` |

---

## 2. 零行为变化证明（关键验证）

为证明「**除口径外没有任何其他行为变化**」，v0.3 保留 legacy `direct` 开关：

```bash
# 用 legacy direct 口径复现 v0.2 → 与已提交 v0.2 产物逐字节比对
python research/scripts/discover_time_observation_patterns.py \
       --round 0.2 --legacy-direct-resolution --check
# → PASS —— 磁盘产物与重算结果逐字节一致（deterministic）。
```

> **结论：重构是行为中性的。** v0.3 与 v0.2 的**全部**差异都只可能来自 Macro Theme 归属口径，
> 不存在任何未声明的副作用。这是本轮可追溯性的核心证据。

---

## 3. Dataset（与 v0.2 完全一致，未变）

| 项目 | 值 |
|---|---|
| Campaigns | 9 |
| Research Candidates | 4 |
| Theme Cycles | 9 |
| 扫描 scope | 15 |
| 锚点记录 | 72 |
| 阶段迁移记录（export 口径） | 49 |
| DB 阶段记录 | 35 |
| 事件记录 | 33 |
| 有效年份 | 2019–2025（7 年） |

**未变**：锚点定义、窗口算法、集中度解析式、复现率、稳定性、留一法、机制归类、Promotion Gate 门槛。

---

## 4. 扫描结果 diff

### 4.1 scan_map

| 指标 | v0.2 | v0.3 | 变化 |
|---|---:|---:|---|
| 扫描候选总数 | 191 | 191 | — |
| 独立样本集合数 | 94 | **89** | −5（口径变体收敛） |
| 重复 scope 候选 | — | 102 | — |
| `TIMELINE_CANDIDATE`（原始） | 5 | **4** | −1 |
| **`effective TIMELINE_CANDIDATE`** | **2** | **4** | **+2** |
| **有效独立结构数** | **1** | **2** | **+1（派生，见 §6.1）** |
| `EXPLORATORY` | 43 / eff 46 | 44 | — |
| `REJECTED` | 10 | **12** | +2 |
| `INSUFFICIENT_DATA` | 121 | **119** | −2 |
| `RESEARCH_ONLY` | 12 | 12 | — |

### 4.2 ★ 口径稳健性：5 对脆弱 → 0

| 指标 | v0.2 | v0.3 |
|---|---:|---:|
| 比较的 scope 变体对 | 50 | 50 |
| 判定一致（稳健） | 45 | **50** |
| **判定不一致（脆弱）** | **5** | **0** |

> **这是本轮最重要的结果。**
> v0.2 曾指出「判定依赖 2019 年是否入样，而入样由 taxonomy 挂接缺口决定，不是有原则的筛选规则」。
> 修复口径后，**整个脆弱类别消失** —— 说明它确实完全由数据挂接缺口造成，不是真实的结构差异。
>
> 该检验在 v0.3 的语义已变为**回归检验**：若未来再次出现 `fragile_pairs > 0`，
> 说明引入了新的口径分歧，**必须记录并降级**，不得静默通过。

### 4.3 ★ 口径变体收敛（逐字节同一集合）

| 结构 | 两个 scope 变体 | `member_signature` | 是否同一集合 |
|---|---|---|---|
| EARLY_SIGNAL 窗口 | `TOPC-001`（TH-AUTO） / `TOPC-018`（rule_auto_summer） | `dd26a9ac86f1` | **完全相同** |
| MAIN_RISE 窗口 | `TOPC-004`（TH-AUTO） / `TOPC-021`（rule_auto_summer） | `273c6902b458` | **完全相同** |

**EARLY_SIGNAL 结构（即 TOP-01）在两口径下现已完全一致**：

| 字段 | v0.2 `TOPC-001`（TH-AUTO） | v0.3 `TOPC-001` | v0.3 `TOPC-018`（rule） |
|---|---|---|---|
| N | 6（不含 2019） | **7** | 7 |
| 中心 | 06-06 | **06-11** | 06-11 |
| 窗口 | 05-29 ~ 06-14（17d） | **05-27 ~ 06-26（31d）** | 05-27 ~ 06-26（31d） |
| 集中度 | 0.2148 | **0.4018** | 0.4018 |
| 复现 | 4/6 | **5/7** | 5/7 |

> ⚠️ **v0.2 §7.2 的警告已被结构性消除。**
> v0.2 曾提醒：「`TOPC-001` 的集中度 0.2148 明显优于 `TOPC-018` 的 0.4018，
> 但这不是因为它更强，而是因为它排除了 2019 年（唯一 8 月离群锚点）；
> **不得用「剔掉 2019 后集中度更高」作为 TOP-01 更强的证据**。」
>
> v0.3 中该「更优变体」**已不存在** —— 两个口径给出完全相同的样本集合与统计量。
> 这是修复口径的直接收益：**消除了一个会诱导错误结论的伪证据**。

---

## 5. TOP-01 回归（PASS）

| 项目 | 期望（Phase 7.2 canonical） | 实测（v0.3） |
|---|---|---|
| pattern_id | — | `TOPC-018` |
| N | 7 | **7** ✅ |
| 中心 | 06-11 | **06-11** ✅ |
| 窗口 | 05-27 ~ 06-26 | **05-27 ~ 06-26** ✅ |
| 复现 | 5/7 | **5/7** ✅ |

**7 个观测年份与锚点（可回溯到 Campaign）**：

| 年 | Campaign | Anchor | 日期 |
|---|---|---|---|
| 2019 | `C-2019-AD` | EARLY_SIGNAL | 2019-08-15 |
| 2020 | `C-2020-NEV` | EARLY_SIGNAL | 2020-06-01 |
| 2021 | `C-2021-NEV` | EARLY_SIGNAL | 2021-06-01 |
| 2022 | `C-2022-POLICY` | EARLY_SIGNAL | 2022-04-27 |
| 2023 | `C-2023-AD` | EARLY_SIGNAL | 2023-06-12 |
| 2024 | `C-2024-V2X` | EARLY_SIGNAL | 2024-06-11 |
| 2025 | `C-2025-ROBOTAXI` | EARLY_SIGNAL | 2025-06-22 |

> 统计量：集中度 0.4018 · 解析 p = 0.00389 · 前后半段 STABLE（位移 +10.5 d）· LOO 最大位移 5 d（无单年主导）。

**注意 TOP-01 走的是 `RULE` scope**（谓词 = `rule_id` 匹配），**不依赖 `theme_family_id`** ——
因此它**天然不受**本轮口径修复影响，回归 PASS 属预期结果，不是巧合。

---

## 6. 有效候选与独立结构

### 6.1 有效 `TIMELINE_CANDIDATE`（4 条 / 2 个样本结构）

| pattern_id | scope | 阶段 | N | 中心 | 窗口 | 集中度 | p | 复现 | 稳健性 |
|---|---|---|---|---:|---|---|---:|---:|---|
| `TOPC-018` | RULE/`rule_auto_summer` | EARLY_SIGNAL | 7 | 06-11 | 05-27~06-26 | 0.4018 | 0.00389 | 5/7 | ROBUST |
| `TOPC-001` | THEME_FAMILY/`TH-AUTO` | EARLY_SIGNAL | 7 | 06-11 | 05-27~06-26 | 0.4018 | 0.00389 | 5/7 | ROBUST |
| `TOPC-021` | RULE/`rule_auto_summer` | MAIN_RISE | 7 | 06-22 | 05-25~07-20 | 0.3068 | 0.000835 | 5/7 | ROBUST |
| `TOPC-004` | THEME_FAMILY/`TH-AUTO` | MAIN_RISE | 7 | 06-22 | 05-25~07-20 | 0.3068 | 0.000835 | 5/7 | ROBUST |

- 4 条 → **2 个独立样本结构**（EARLY_SIGNAL / MAIN_RISE），两两 `member_signature` 完全相同。
- `theme_family_count = 1`（全部为汽车族）· `theme_cycle_count = 7` · `campaign_count = 7`。
- 机制：`CALENDAR_DRIVEN` + `POLICY_CADENCE` + `REPORTING_CADENCE` + `DATA_RELEASE_CADENCE`（置信度 MEDIUM）。

### 6.2 ★ 但第 2 个结构是**派生结果**（不得计为独立规律）

本脚本 `lifecycle_rhythm` 对 `rule_auto_summer` 与 `TH-AUTO` 两个 scope 都给出：

| 阶段 | n | 中心 | 中位滞后 | 预测中心 | **残差** | `derived_from_early_signal` |
|---|---:|---|---:|---|---:|---|
| `THEME_FORMING` | 3 | 06-14 | 9 d | 06-20 | 6 d | **true** |
| `BROAD_CONFIRMATION` | 4 | 06-29 | 25 d | 07-06 | 7 d | **true** |
| `MAIN_RISE` | 7 | 06-22 | 10 d | 06-21 | **1 d** | **true** |

> **MAIN_RISE 的中心（06-22）可由「EARLY_SIGNAL 中心（06-11）+ 中位滞后（10 d）」几乎精确解释（残差 1 天）。**
> 因此 `TOPC-004` / `TOPC-021` **不是独立规律，而是 EARLY_SIGNAL 结构的派生呈现**。
>
> **实质结论：独立稳健时间结构 = 1 个**（与 v0.2 相同）。

### 6.3 未决方法学问题（本轮**不擅自改规则**）

`effective_promotion_status` 的门槛链（数值门槛 → 口径稳健性 → 派生检查）中：

- **口径稳健性**已含在 Promotion Gate（`timeline_candidate_robustness`）。
- **派生判定（`derived_from_early_signal`）目前只出现在 `lifecycle_rhythm` 报告里，未被 Promotion Gate 使用。**

v0.2 中 `TOPC-021` 被降级的原因是**脆弱**，不是派生；修复脆弱后它自动升为 `TIMELINE_CANDIDATE`。

> **这是一个待决问题，不是本轮可自行决定的事：**
> 「`derived_from_early_signal = true` 是否应作为 Promotion Gate 的降级理由？」
>
> **本轮不做任何规则变更** —— 协议明确禁止「为凑数量放松标准」，同样也禁止为压数量收紧标准。
> 该问题记入 §9「下一轮决策点」。

---

## 7. 变化归因（25 / 191 个候选有变化，全部可归因）

### 7.1 三组归因

| 组 | 机制 | 涉及候选数 |
|---|---|---:|
| **A** | `TH-AUTO` 成员 +1（`C-2019-AD` 入样 → 2019 年进入族口径） | 6 |
| **B** | `TH-PHARMA` 成员 +2（`RC-2020-PANDEMIC` / `RC-2021-TCM` 入样） | 9 |
| **C** | `theme_family_count` 由 0 → 1/2（RC 对象首次被归属 Macro Theme） | 9 |
| **D** | 口径脆弱消除引发的状态变化 | 3 |

> **没有任何一个变化无法归因到上述四类。** 这印证了 §2 的「零行为变化」结论。

### 7.2 完整变更明细

| pattern_id | scope | stage | 变化 |
|---|---|---|---|
| `TOPC-001` | THEME_FAMILY/TH-AUTO | EARLY_SIGNAL | N 6→7; Cycle 6→7; 中心 06-06→06-11; 窗口 05-29~06-14→05-27~06-26; 集中度 0.2148→0.4018 |
| `TOPC-004` | THEME_FAMILY/TH-AUTO | MAIN_RISE | N 6→7; Cycle 6→7; promo EXPLORATORY→TIMELINE_CANDIDATE; eff EXPLORATORY→TIMELINE_CANDIDATE; 中心 06-17→06-22; 窗口 05-24~07-11→05-25~07-20; 集中度 0.1879→0.3068; 稳健 None→ROBUST |
| `TOPC-005` | THEME_FAMILY/TH-AUTO | PEAK | N 6→7; Cycle 6→7; promo TIMELINE_CANDIDATE→EXPLORATORY; 中心 07-03→07-11; 窗口 06-14~07-22→06-07~08-14; 集中度 0.2186→0.3872; 稳健 FRAGILE_SCOPE_DEPENDENT→None |
| `TOPC-010` | THEME_FAMILY/TH-AUTO | MAIN_END | N 6→7; Cycle 6→7; 集中度 0.3721→0.3543 |
| `TOPC-011` | THEME_FAMILY/TH-PHARMA | EARLY_SIGNAL | N 1→3; promo INSUFFICIENT_DATA→REJECTED; eff INSUFFICIENT_DATA→REJECTED; 中心 01-02→12-12; 集中度 None→0.4548 |
| `TOPC-012` | THEME_FAMILY/TH-PHARMA | THEME_FORMING | N 1→2; 中心 07-22→10-11; 集中度 None→1.3315 |
| `TOPC-015` | THEME_FAMILY/TH-PHARMA | PEAK | N 1→3; promo INSUFFICIENT_DATA→REJECTED; eff INSUFFICIENT_DATA→REJECTED; 中心 12-25→12-28; 集中度 None→0.3068 |
| `TOPC-016` | THEME_FAMILY/TH-PHARMA | DECLINING | N 1→2; 中心 07-02→01-05; 集中度 None→0.4438 |
| `TOPC-017` | THEME_FAMILY/TH-PHARMA | MAIN_END | N 1→2; 中心 10-31→11-30; 集中度 None→0.5014 |
| `TOPC-021` | RULE/rule_auto_summer | MAIN_RISE | eff EXPLORATORY→TIMELINE_CANDIDATE; 稳健 FRAGILE_SCOPE_DEPENDENT→ROBUST |
| `TOPC-033` | RULE/rule_pharma_upgrade | DECLINING | 族 0→1 |
| `TOPC-039` | ALL/ALL | PEAK | 族 1→2 |
| `TOPC-042` | ALL/ALL | DECLINING | 族 1→2 |
| `TOPC-060` | THEME/TH-PHARMA-PANDEMIC | EARLY_SIGNAL | 族 0→1 |
| `TOPC-061` | THEME/TH-PHARMA-PANDEMIC | PEAK | 族 0→1 |
| `TOPC-062` | THEME/TH-PHARMA-TCM | EARLY_SIGNAL | 族 0→1 |
| `TOPC-063` | THEME/TH-PHARMA-TCM | THEME_FORMING | 族 0→1 |
| `TOPC-064` | THEME/TH-PHARMA-TCM | PEAK | 族 0→1 |
| `TOPC-078` | THEME_FAMILY/TH-AUTO | MAIN_RISE->PEAK | N 6→7; Cycle 6→7; promo TIMELINE_CANDIDATE→EXPLORATORY; 中心 07-12→07-13; 窗口 06-16~08-07→06-15~08-10; 集中度 0.2186→0.3872; 稳健 FRAGILE_SCOPE_DEPENDENT→None |
| `TOPC-079` | THEME_FAMILY/TH-AUTO | PEAK->MAIN_END | N 6→7; Cycle 6→7; 集中度 0.3721→0.3543 |
| `TOPC-080` | THEME_FAMILY/TH-PHARMA | EARLY_SIGNAL->THEME_FORMING | N 1→2; 中心 07-22→10-11; 集中度 None→1.3315 |
| `TOPC-083` | THEME_FAMILY/TH-PHARMA | THEME_FORMING->PEAK | N 1→2; 中心 12-25→12-12; 集中度 None→0.2055 |
| `TOPC-086` | THEME_FAMILY/TH-PHARMA | MAIN_RISE->PEAK | N 1→2; 中心 12-25→01-10; 集中度 None→0.2548 |
| `TOPC-087` | THEME_FAMILY/TH-PHARMA | PEAK->MAIN_END | N 1→2; 中心 10-31→11-30; 集中度 None→0.5014 |
| `TOPC-110` | ALL/ALL | MAIN_RISE->PEAK | 族 1→2 |

### 7.3 两个副结果

**(a) `TH-PHARMA` 从「不可统计」变为「样本仍不足」**

医药族的 EARLY_SIGNAL / PEAK 从 N=1 升到 **N=3**，首次具备最小样本。
但全部仍为 `REJECTED`（N=3 且中心分散：EARLY_SIGNAL 中心 12-12、PEAK 中心 12-28、集中度 0.4548 / 0.3068）。
**没有产生任何新候选** —— 这是诚实的「覆盖率提升但不足以支撑结论」。

**(b) `TOPC-039` / `TOPC-042` / `TOPC-110`（ALL scope）`theme_family_count` 1 → 2**

此前医药 RC 对象无 Macro Theme 归属，导致「全部历史对象」的族数被低估为 1。
修复后正确反映为 **2** —— 与 `Coverage Ceiling` 的 `theme_family_count = 2` 一致。

---

## 8. 诚实限制清单

1. **「2 个独立结构」中的第 2 个是派生结果**（`MAIN_RISE`，残差 1 天，`derived_from_early_signal = true`）。
   **实质性独立稳健时间结构仍为 1 个。不得表述为「发现了 2 个规律」。**
2. **`theme_family_count` 仍 = 1**（所有有效候选均为汽车族）→ **跨族稳健性仍无法检验**。
   本轮**没有**改善这一点（TH-PHARMA 样本仍不足）。
3. **`华为汽车` taxonomy 缺口未修**（`RC-2023-HUAWEI` → `UNRESOLVED_NAME`）。
   本轮**有意不修**：补录 `themes` 行属**数据决策**（已登记 DEFER 项 `F7`），
   不在「口径统一」范围内；且它不影响 §7.1 的任一组归因。
4. **核验比例 0 / 24**，全部 `confidence = low` → 数据质量上限不变。
5. **交易日历仅覆盖 2.6 / 8 年** → 时间统计仍只能退化为自然日口径。
6. **`derived_from_early_signal` 未进入 Promotion Gate** —— 见 §6.3，属**待决**，本轮不改规则。
7. **未做多重比较校正之外的稳健性扩展**：Bonferroni 通过者仅 `TOPC-113` / `TOPC-130`（DB 阶段口径，非 TIMELINE_CANDIDATE）。
8. **`scope_robustness.note` 已同步更新**为回归检验语义（原文本描述的是已修复的缺口）。
9. 本报告**只描述过去**。`5 / 7` 只能表述为「历史 7 个观测年份中有 5 个落入该观察窗口」，
   **不得**表述为未来概率。

---

## 9. 下一轮决策点（不擅自执行）

| # | 决策点 | 为什么需要决策 |
|---|---|---|
| **D1** | `derived_from_early_signal = true` 是否应成为 Promotion Gate 的降级理由？ | 当前使 2 个派生结构进入 `TIMELINE_CANDIDATE`。改与不改都会改变结论数量，**属规则变更**，必须显式决定并留痕 |
| **D2** | 是否补录 `华为汽车` 到 `themes` 表（`F7`）？ | 属**历史数据变更**；影响 `RC-2023-HUAWEI` 归属，不影响本轮任何归因组 |
| **D3** | `Historical Coverage Audit` 是否升级为 v0.2 并消费 v0.3 候选池？ | 现审计 v0.1 的 `discovery_scan_map` 引用的是 v0.2（当时口径）。升级属独立轮次 |
| **D4** | Wave 1 数据扩容（电力设备 / 信息通信） | 协议要求：**先完成本轮 diff 并稳定后**再决定扩容。本轮结论：口径已稳定，可以进入 |

> **推荐顺序**：D1（规则）→ D4（数据扩容）→ D3（审计升级）→ D2（随扩容一并处理）。
> **D1 必须最先**，因为它决定「独立结构数」的口径，会影响后续所有统计陈述。

---

## 10. 复现方式

```bash
# 生成 v0.3（canonical 口径）
python research/scripts/discover_time_observation_patterns.py

# 校验确定性（逐字节一致）
python research/scripts/discover_time_observation_patterns.py --check

# 生成并打印摘要
python research/scripts/discover_time_observation_patterns.py --print

# ★ 回归：用 legacy direct 口径复现 v0.2（证明重构零行为变化）
python research/scripts/discover_time_observation_patterns.py --round 0.2 --legacy-direct-resolution --check

# canonical 口径解析器的独立验证
python -c "import sys;sys.path.insert(0,'research/scripts');import theme_taxonomy as t,\
sqlite3,json;tax=t.load(sqlite3.connect('research/database/cycle_research.db'));\
print(json.dumps(t.resolution_report(tax,[]),ensure_ascii=False)[:200])"
```

退出码：`0` = 通过；`1` = 自检 / TOP-01 回归失败（**不写文件**）。

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
- 未修改 DB 任何一行数据（`theme_taxonomy.py` 只读 `themes` 表）。
- 未修改 Product Artifact（`time_observation_patterns_v0_1.json`）——
  该生成器只读 export + verification，**不依赖候选池**，故 Product 侧零影响。
- `time_observation_candidate_pool_v0_2.*` **保留未删**，作为口径修复前的可比基线。

---

*报告结束 · Time Observation Discovery v0.3 · 2026-09-16*
