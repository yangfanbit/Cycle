# Driver Canonicalization v0.3 — 收口审计报告

> | 项目 | 值 |
> |---|---|
> | **性质** | **Rule Set v0.3 + Driver Canonicalization v0.3 的最后一次收口审计** |
> | **本轮修复** | **1 项语义不一致（「阅兵」归属）** + **1 项确定性缺陷（子串检测排序）** |
> | **审计对象** | v0.3 新增关键词（**未重新扩展词表**） |
> | **未做** | **未生成 SA v0.4** · **未刷新 Time Observation** · 未修改 Canonical DB · 未修改 Export · 未修改 taxonomy · **未修改 Rule Set v0.3 判定逻辑** · 未修改 v0.1 / v0.2 · 未新增 driver vocabulary · 未重新研究 R01 |
> | **新增产物** | `research/research/reports/driver_keyword_collision_audit_v0_3.json` · `research/scripts/audit_driver_keyword_collisions_v0_3.py` |
> | **重新生成** | `historical_driver_canonicalization_v0_3.json` · `historical_driver_evidence_ledger_v0_3.json` · `structural_analogy_rule_calibration_v0_3.json` · `..._pairs_v0_3.csv`（v0.3 为**本轮产物**，经明确授权重新生成；v0.1 / v0.2 **逐字节未动**） |

---

## 1. 「阅兵」最终处理 → **归 `EVENT_CATALYST`**（已修正）

### 1.1 裁决

> **「阅兵」= `EVENT_CATALYST`。「纪念大会」同。**
> **不允许同时作为 `POLICY_DRIVEN`。**

### 1.2 五条理由（按既有 Driver Canonicalization 原则，非为让结果漂亮）

| # | 理由 |
|---|---|
| **① 形式** | 阅兵有**明确日期、一次性**，属**重大纪念活动**，**不是**规则 / 制度性文件 |
| **② 机制** | 它**不改变任何产业规则** —— 无补贴、无准入、无配额、无采购规则变更。intake 原文即标注「**重大纪念事件的注意力驱动**」「**事件驱动型叙事**」（`RC-2019-MIL-PARADE-70` drivers 原文） |
| **③ 词表内部一致性** | v0.1 `EVENT_CATALYST` **已含**「**大会**」「峰会」「论坛」「启动仪式」等**同类型大型活动** → 将阅兵归 POLICY **与「大会」的既有归类自相矛盾** |
| **④ 实际损害** | 跨 canonical 重复命中使 `RC-2025-MIL-PARADE-80` 落入 `DERIVED`（**无 canonical driver**）→ **反而丢失机制**（修正前该 cycle 无任何 canonical driver） |
| **⑤ 禁止反向推理** | 不得为「让候选拿到 driver」而保留双重归属 —— 那正是「为了让结果更漂亮而选择」 |

### 1.3 为何**不**允许双重语义（`POLICY_DRIVEN` + `EVENT_CATALYST`）

1. canonical vocabulary 的 9 项是**互斥机制轴**（`POLICY_DRIVEN` = 规则/制度驱动 vs `EVENT_CATALYST` = 离散事件驱动）；
2. 允许同一关键词跨 canonical 会**系统性制造 `DERIVED` / `AMBIGUOUS`** —— v0.3 实测 8 条 `DIRECT→DERIVED`、1 条 `DERIVED→AMBIGUOUS` **均源于跨 canonical 重复**；
3. Rule Set §3.3「**不得仅凭 driver 名称相同判定 `MATCH`**」→ 同理，**不得让同一关键词同时充当两种机制**。

### 1.4 实施

- 从 `POLICY_DRIVEN` **移除**「阅兵」「纪念大会」；在 `EVENT_CATALYST` **加入**（「纪念大会」已被 v0.1「大会」覆盖，显式列入以便审计）；
- 写入 `revisions` 字段（`v0.3-r1`，含 decision / rationale / `allowed_dual_semantics: false`）；
- **canonical vocabulary 未动**（仍 9 项）；**v0.1 / v0.2 未动**；**重新生成 v0.3**。

### 1.5 对 R01-06 / RC 的影响（实测）

| cycle | 修正前 | **修正后** |
|---|---|---|
| `RC-2019-MIL-PARADE-70` | `['POLICY_DRIVEN']` ← **语义错误** | **`['EVENT_CATALYST']`** ✅ |
| `RC-2025-MIL-PARADE-80` | `[]`（双重命中 → DERIVED，**丢失机制**） | **`['EVENT_CATALYST']`** ✅ |
| `C-2020-MIL-EQUIP-ORDER` | `['DEMAND_SURGE']` | `['DEMAND_SURGE']`（未变） |
| `C-2019-MIL-GROUP-RESTRUCTURE` | `['EVENT_CATALYST', 'POLICY_DRIVEN']` | `['POLICY_DRIVEN']`（未变） |
| `RC-2017-MIL-MIXED-REFORM` / `RC-2015-MIL-REFORM-BULL` / `RC-2024-MIL-COMMERCIAL-SPACE` | — | 未变 |

**逐 cycle `canonical_drivers` 变化 = 2 个**（其余 77 个 cycle 未变）。
**`by_canonical_driver`**：`POLICY_DRIVEN 58→56` · `EVENT_CATALYST 14→18`（其余 6 项未变）。
**有 canonical driver 的 cycle：59 → 60**（`RC-2025-MIL-PARADE-80` 新纳入）。

> **★ 重要：SA 层结构状态 0 变化**（`combined` 99 条变化的前后分布**逐条相同**）。
> 原因：这两个 RC cycle 各有 **≥2 个 `NOT_AVAILABLE` 维度**（`evidence_sequence` + `event_structure`）
> → 无论 driver 为 `NOT_AVAILABLE` 还是 `MISMATCH`，均在 **R1** 落入 `INSUFFICIENT_EVIDENCE`。
> **修正的价值在语义正确性**：driver 由「**资料不足**（NOT_AVAILABLE）」纠正为「**机制不对应**（MISMATCH）」，
> 且 `RC-2025-MIL-PARADE-80` 重新获得 `EVENT_CATALYST` 机制标签。

---

## 2. 新增关键词 collision audit（**只审计，未扩展词表**）

### 2.1 规模（精确）

| 项 | 数量 |
|---|---:|
| v0.1 基础关键词 | **158** 条（唯一 157；跨 canonical 重复 1 个：`结构迁移`） |
| v0.3 声明新增 | **134** 条 |
| **去重后新增词** | **133 词** |
| 其中已在 v0.1 同 canonical 内 | 2（`国产替代` · `能源局`）→ **净新增 131 词** |
| 合并后总数 | **289** 条 |

### 2.2 Collision 数量汇总

| 检查 | 数量 | 明细 |
|---|---:|---|
| **新增词中命中多个 canonical** | **0** ✅ | 无（`v0.3` 新增词**未引入跨 canonical 重复**） |
| **既有跨 canonical 重复（v0.1 遗留）** | **1** | **`结构迁移`** 同时在 `TECH_BREAKTHROUGH` 与 `INDUSTRY_UPGRADE` —— **v0.1 起即存在，本轮不修**（禁改 v0.1） |
| **宽关键词风险**（命中 ≥2 且存在非决定性） | **37** | 见 §2.3 |
| **跨 canonical 子串冲突（涉及新增词）** | **6** | 见 §2.4 |
| **新增 `AMBIGUOUS`** | **0** ✅ | 无（且 `AMBIGUOUS` 由 2 → **1**，`RC-2025-MIL-PARADE-80` 因修正退出 AMBIGUOUS） |
| **`DIRECT → DERIVED`** | **8** | 见 §2.5 |

### 2.3 宽关键词风险 Top（命中数高但非决定性）

| keyword | canonical | 命中 | 决定性 | co-hit |
|---|---|---:|---:|---|
| `负增长` | `CYCLE_REVERSAL` | 10 | **0** | `DEMAND_SURGE 10` · `SUPPLY_CONTRACTION 1` · … |
| `渠道` | `DEMAND_SURGE` | 6 | **0** | `SUPPLY_CONTRACTION 3` · `INDUSTRY_UPGRADE 2` · `VALUATION_RESET 1` |
| `资本开支` | `DEMAND_SURGE` | 7 | 3 | `CYCLE_REVERSAL 3` · `INDUSTRY_UPGRADE 1` · … |
| `外资` | `VALUATION_RESET` | 4 | **0** | `INDUSTRY_UPGRADE 3` · `DEMAND_SURGE 1` |
| `指标` | `POLICY_DRIVEN` | 5 | 2 | `SUPPLY_CONTRACTION 2` · `DEMAND_SURGE 1` |
| `储备` | `POLICY_DRIVEN` | 4 | 1 | `CYCLE_REVERSAL 2` · `VALUATION_RESET 1` |
| `整治` | `POLICY_DRIVEN` | 4 | 1 | `SUPPLY_CONTRACTION 3` · `EVENT_CATALYST 1` · `CYCLE_REVERSAL 1` |
| `持仓` | `DEMAND_SURGE` | 3 | **0** | `VALUATION_RESET 3` |
| `门店` | `DEMAND_SURGE` | 3 | **0** | `INDUSTRY_UPGRADE 2` · `TECH_BREAKTHROUGH 1` |
| `下行周期` | `CYCLE_REVERSAL` | 3 | 1 | `SUPPLY_CONTRACTION 2` |
| `双控` | `SUPPLY_CONTRACTION` | 3 | 1 | `POLICY_DRIVEN 2` |
| `国产替代` | `INDUSTRY_UPGRADE` | 3 | 1 | `VALUATION_RESET 1` · `DEMAND_SURGE 1` |

**★ 最严重的一项**：`负增长` 命中 10 条文本，**决定性 0** —— 因为它与 v0.1 的 `增长`（`DEMAND_SURGE`）构成子串冲突，**每一条含「负增长」的文本都必然同时命中 `DEMAND_SURGE`** → 永远无法成为 `DIRECT`。

### 2.4 跨 canonical 子串冲突（**全部涉及新增词**）

| 较短词 | ⊂ 较长词 | 较短词归属 | 较长词归属 | 性质 |
|---|---|---|---|---|
| `增长` | `负增长` | `DEMAND_SURGE` | `CYCLE_REVERSAL` | ★ **新增词引入**；语义上「负增长」是「增长」的反面 |
| `整治` | `整治提升` | `POLICY_DRIVEN` | `SUPPLY_CONTRACTION` | ★ **两词均为本轮新增**（我自身造成） |
| `出口` | `出口管制` | `DEMAND_SURGE` | `POLICY_DRIVEN` | ★ **新增词引入**；「出口管制」是政策，「出口」是需求 |
| `采购` | `装备采购` | `DEMAND_SURGE` | `POLICY_DRIVEN` | ★ **新增词引入**；影响 `C-2020-MIL-EQUIP-ORDER` |
| `储备` | `黄金储备` | `POLICY_DRIVEN` | `VALUATION_RESET` | ★ **两词均为本轮新增** |
| `扩产` | `扩产周期` | `DEMAND_SURGE` | `SUPPLY_CONTRACTION` | ★★ **两词均为本轮新增，且语义自相矛盾** |

**★★ 唯一「自相矛盾」项：`扩产` vs `扩产周期`**
`扩产`（产能扩张）被归 `DEMAND_SURGE`，而 `扩产周期` 被归 `SUPPLY_CONTRACTION` ——
**同一概念（产能扩张）被分到两个方向相反的机制**。这是**本轮新增词自身引入的语义错误**（非 v0.1 遗留）。
其 `coverage_note` 原文写「方向相反，单列以利审计」—— **该推理不成立**：产能扩张不属于「供给收缩」。

> **本轮按用户 §2「只做审计」的要求，未修改该词。** 建议处置见 §7 问题 2。

### 2.5 `DIRECT → DERIVED`（8 条，已有 DIRECT 被新增词破坏）

| cycle | bucket | 原 canonical | 现命中 |
|---|---|---|---|
| `C-2019-AD` | turning | `DEMAND_SURGE` | `DEMAND_SURGE`, `CYCLE_REVERSAL` |
| `C-2019-MIL-GROUP-RESTRUCTURE` | start | `EVENT_CATALYST` | `POLICY_DRIVEN`, `EVENT_CATALYST` |
| `C-2020-MIL-EQUIP-ORDER` | start | `DEMAND_SURGE` | `POLICY_DRIVEN`, `DEMAND_SURGE` |
| `C-2020-MIL-EQUIP-ORDER` | accelerator | `DEMAND_SURGE` | `POLICY_DRIVEN`, `DEMAND_SURGE` |
| `C-2020-MIL-EQUIP-ORDER` | ending | `DEMAND_SURGE` | `POLICY_DRIVEN`, `DEMAND_SURGE` |
| `C-2022-RE-POLICY-THREE` | accelerator | `EVENT_CATALYST` | `POLICY_DRIVEN`, `EVENT_CATALYST` |
| `C-2025-FIN-INSURANCE` | accelerator | `EVENT_CATALYST` | `VALUATION_RESET`, `EVENT_CATALYST` |
| `C-2019-COMM-5G` | turning | `CYCLE_REVERSAL` | `DEMAND_SURGE`, `CYCLE_REVERSAL` |

**受影响 Canonical Campaign 的 `has_direct`（`direct_count` 是否归零）**：**仅 1 个** ——
`C-2025-FIN-INSURANCE`（`direct_count` 1 → 0，`primary_mechanism` → `UNKNOWN`）。
**该 cycle 在 v0.2 / v0.3 规则下均未达到 `STRUCTURAL_SUPPORTED`** → **不改变任何 SUPPORTED 结论**。

### 2.6 Canonical Campaign `primary_mechanism` 变化（4 个）

| cycle | v0.2 | v0.3 |
|---|---|---|
| `C-2019-MIL-GROUP-RESTRUCTURE` | `EVENT_CATALYST` | `POLICY_DRIVEN` |
| `C-2020-RE-DEBT-RISK` | `UNKNOWN` | `POLICY_DRIVEN` |
| `C-2022-RE-POLICY-THREE` | `EVENT_CATALYST` | `POLICY_DRIVEN` |
| `C-2025-FIN-INSURANCE` | `EVENT_CATALYST` | `UNKNOWN` |

**合理性评估**：
- `C-2019-MIL-GROUP-RESTRUCTURE` / `C-2022-RE-POLICY-THREE` → **`POLICY_DRIVEN` 合理**（集团战略性重组 / 三支箭均为**制度性行动**；原 `EVENT_CATALYST` 系 v0.1「上市」「获批」等宽词误命中）；
- `C-2020-RE-DEBT-RISK` → **`POLICY_DRIVEN` 合理**（三道红线 = 房地产金融审慎管理制度）；
- `C-2025-FIN-INSURANCE` → **`UNKNOWN` 是「诚实结果」**（唯一 DIRECT 被多命中消解，不猜测）—— 但属**副作用**，见 §7 问题 3。

---

## 3. 重点保护核查（全部通过）

| 保护项 | 结果 |
|---|---|
| **52 个 Canonical Campaign 均有 canonical driver** | ✅ **52 / 52，无一缺失** |
| **不为 19 个无 driver 的 RC 猜测 driver** | ✅ 全部如实标记为「无 canonical driver」，**未做任何猜测** |
| **`EVENT_TYPE != DRIVER`** | ✅ 映射仅依据 `raw_driver` 文本关键词；`canonical_driver` 非空但 `matched_rules` 为空 = **0** |
| **价格 / 涨跌不能反推 driver** | ✅ `PRICE_ACTION` 排除逻辑保持有效；`NOT_AVAILABLE` 条目中被赋 `canonical_driver` = **0** |
| **canonical vocabulary 不增加** | ✅ 仍为 **9 项**（未新增、未删除） |
| **v0.1 / v0.2 artifact 完全不变** | ✅ `historical_driver_canonicalization_v0_1/v0_2` · `ledger_v0_1/v0_2` · `rule_set_v0_2.md` · `calibration_v0_2` —— **6 个文件 `git diff --quiet` 全部 UNCHANGED** |

---

## 4. `DIRECT / DERIVED / AMBIGUOUS / UNKNOWN / NOT_AVAILABLE` 变化

| 状态 | 阅兵修正前（本轮初） | **修正后** | Δ |
|---|---:|---:|---:|
| `DIRECT` | 55 | **55** | 0 |
| `DERIVED` | 336 | **337** | +1 |
| `AMBIGUOUS` | 2 | **1** | **−1** |
| `UNKNOWN` | 59 | **59** | 0 |
| `NOT_AVAILABLE` | 89 | **89** | 0 |

> **`AMBIGUOUS` 由 2 → 1**：`RC-2025-MIL-PARADE-80` 的「复合叙事：阅兵 + 军贸 + 景气反转 +「十五五」」原命中 4 个 canonical → `AMBIGUOUS`；
> 修正后「阅兵」不再计入 POLICY，命中降为 3 → `DERIVED`。**这是一项改善**（`AMBIGUOUS` 越少越好，因为它表示无法收敛）。

**canonical driver 计数变化**：`POLICY_DRIVEN 58 → 56` · `EVENT_CATALYST 14 → 18`（其余 6 项未变）。

---

## 5. 52 个 Canonical Campaign 的 driver coverage

| 项 | 值 |
|---|---:|
| Canonical Campaign 总数 | **52** |
| **有 canonical driver** | **52（100%）** ✅ |
| 无 canonical driver | **0** |
| Research Candidate 总数 | 27 |
| 有 canonical driver | 8 |
| **无 canonical driver** | **19**（全部为 RC；18 个 export `drivers` 为空 + 1 个多命中/AMBIGUOUS） |
| **全 universe 有 driver** | **60 / 79**（v0.2 为 55 / 79） |

---

## 6. Rule Set v0.3 Semantic Conformance

| 校验 | 结果 |
|---|---|
| **独立重算**（从规则文本独立实现 `level_v3()`，不 import builder） | ✅ **A/B/C/D 四组 1580 / 1580 行逐行一致** |
| **语义不变量 S1–S14** | ✅ **全部 0 违规** |
| **S14**：全表 `driver=MISMATCH` 的 `STRUCTURAL_PARTIAL` | ✅ **0 条**（A 组对照 = 50） |
| **Theme-Blind 不改变 Structural Status** | ✅ 0 变化 |
| **负控制保持** | ✅ 2 / 2（`NO_VALID_CORRESPONDENCE` / `THEME_ONLY`） |
| **生成器确定性**（连续 3 次 `--check`） | ✅ 两个生成器均 **PASS** |

> **★ 本轮修正了一处确定性缺陷**：`canonicalize_historical_drivers_v0_3.py` 的子串冲突检测原用
> `sorted(set, key=len)` —— **不是全序**，等长元素顺序受 `set` 迭代顺序影响，
> 在 `PYTHONHASHSEED` 随机化下产出不同顺序 → **破坏逐字节可复现性**（`--check` 真实捕获）。
> 已改为 `key=lambda s: (len(s), s)`，连续 3 次 `--check` PASS。

**SA 层结构状态（重新生成后）**：

| 组 | 规则 | driver | SUPPORTED | STRICT | PARTIAL | THEME_ONLY | INSUFFICIENT | NO_VALID |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| A | v0.2 | v0.2 | 4 | 1 | 89 | 6 | 145 | 151 |
| D | **v0.3** | **v0.3** | **4** | **1** | **39** | **9** | **125** | **218** |

**E.1 消除状态**：`driver=MISMATCH` 的 `PARTIAL` **50 → 0**（A 组 50 / C 组 0 / D 组 0）✅ **保持消除**。

---

## 7. 是否已满足 SA v0.4 刷新条件

> ### **结论：尚未满足。** 有 3 项阻塞 / 建议项，其中 2 项为**本轮审计新发现**。

| # | 项 | 级别 | 说明 |
|---|---|---|---|
| **1** | **18 个 Research Candidate 的 export `drivers` 四 bucket 全为空** | **阻塞（数据层）** | 属 **export 数据缺口** → 应由 Canonical / Export 层补全，**不得由词表猜测**。补全后这 18 个 cycle 才能参与结构判定 |
| **2** | **`扩产` vs `扩产周期` 语义自相矛盾**（★ 本轮新发现，**我自身引入**） | **建议修复（词表）** | `扩产`→`DEMAND_SURGE` 而 `扩产周期`→`SUPPLY_CONTRACTION`，**同一概念分到方向相反的机制**。**本轮按「只做审计」未改**。建议：将 `扩产周期` 移出 `SUPPLY_CONTRACTION`（或删除该词，`扩产` 已覆盖），使两者同归 `DEMAND_SURGE` |
| **3** | **6 项跨 canonical 子串冲突**（`增长/负增长` · `整治/整治提升` · `出口/出口管制` · `采购/装备采购` · `储备/黄金储备` · `扩产/扩产周期`） | **建议处理（映射逻辑）** | 这些使相关文本**永远无法成为 `DIRECT`**（实测 8 条 `DIRECT→DERIVED`、1 个 Campaign 失去唯一 DIRECT）。**属映射逻辑问题**（多命中消歧），非关键词问题 → 应留待 **v0.4 评估**（本轮的「只审计」与「不改判定逻辑」约束下不动） |
| **4** | `E.3`：SA research artifact 的 `historical_kind` 把全部 cycle 标为 `campaign` | 建议 | **无规则影响**；`explanations` 侧已正确。建议 SA v0.4 一并修正 |
| **5** | `driver = MATCH` 仅 1 条 / `event MATCH` 仅 1 条 | 观测 | 属**数据粒度**限制，**不得**通过放宽规则解决 |

**建议的 SA v0.4 前置顺序**：
① 问题 1（export 数据补全）→ ② 问题 2（`扩产周期` 归属，**词表级**）→ ③ 问题 3（多命中消歧，**映射逻辑级，需独立版本 + 重新校准**）→ ④ 问题 4（kind metadata）→ ⑤ 生成 SA v0.4（Rule Set v0.3 + Canonicalization v0.3）→ ⑥ 之后才考虑 Time Observation 刷新。

> **★ 本轮已满足的部分**：Rule Set v0.3 的 **E.1 修复已彻底消除**（`driver=MISMATCH` 的 `PARTIAL` = 0），
> **语义一致性校验全绿**，**52 个 Canonical Campaign 100% 有 canonical driver**，
> **「阅兵」语义已纠正**。**SA v0.4 在结构规则层面已就绪，但数据层（问题 1）与两处词表/映射问题尚未闭环。**

---

## 8. 验证结果

| 检查 | 结果 |
|---|---|
| `validate_db` | **PASS**（3 条 warning 未新增） |
| `validate_timeline_export` | **PASS** |
| `validate_batch_research` | **PASS** |
| `validate_promotion_manifest` | **PASS** |
| `check_doc_schema_consistency` | **PASS** |
| `validate_current_research` | **PASS** |
| `validate_monorepo_integrity` | **PASS** |
| `refresh --check` | **PASS** |
| `intake --check` | **PASS** |
| validator tests | **PASS**（44/44） |
| `validate_governance_gates` | **PASS** |
| `validate_structural_analogy_v0_3` | **PASS** |
| **`validate_structural_analogy_semantics`** | **PASS**（1580/1580；S1–S14 全绿） |
| `canonicalize_historical_drivers_v0_3.py --check` ×3 | **PASS**（确定性已修复） |
| `build_structural_analogy_rule_calibration_v0_3.py --check` ×3 | **PASS** |
| **v0.1 / v0.2 逐字节未变** | **PASS**（6 个文件 UNCHANGED） |

---

## 9. 本轮严格未做

- ❌ **未生成 SA v0.4**；❌ **未刷新 Time Observation**；
- ❌ 未修改 Canonical DB / Export / `exports/timeline_export_v1.json` / taxonomy；
- ❌ **未修改 Rule Set v0.3 的其它判定逻辑**（R1–R4 / 各维度判据 / 负控制 / 边界 全部未动）；
- ❌ 未修改 v0.1 / v0.2 任何产物；
- ❌ 未新增 driver vocabulary；
- ❌ 未重新研究 R01；
- ❌ **未按审计发现修改任何关键词**（含 §2.4 的 `扩产周期` 矛盾项）—— 遵守「只做审计」。

**本轮唯一允许的修改**（用户 §1 明确授权）：「阅兵」「纪念大会」由 `POLICY_DRIVEN` 移至 `EVENT_CATALYST`，
并重新生成 v0.3 产物（v0.3 为本轮产物，非冻结历史件）。

---

*Driver Canonicalization v0.3 · 收口审计 · 2026-09-23 · 未刷新 Time Observation*
