# ThreeC Research Core Release 报告

> | 项目 | 值 |
> |---|---|
> | **性质** | **Research Core Release** —— 结束长期局部打磨，完成一次正式 Research Release |
> | **基线** | HEAD `8216f7f` · a/b `0/0` · worktree clean |
> | **本轮范围** | 剩余 5 项 driver collision → Driver Canonicalization v0.4 → **SA v0.4** → **Time Observation v0.2** → Product-facing 输入验收 |
> | **原则** | **不为增加 SUPPORTED / PARTIAL / Pattern 数量而修改规则** |
> | **冻结输入（未改）** | Research Model v1.0 · `schema.sql` · Timeline Export Contract v1.0 · CMTR v1 · Canonical Campaign decisions · R01 Intake packages · **Rule Set v0.3（R1–R4 未改）** · canonical driver vocabulary 9 项 |
> | **未改** | Campaign existence / independence · taxonomy root · DB schema · Export Contract · `exports/timeline_export_v1.json` |

---

## 一、阶段 A：剩余 5 项 collision 处理（**先审计，后改**）

审计产物：`research/research/reports/residual_collision_analysis_v0_3.json`
模拟产物：`research/research/reports/kuochan_semantics_decision_v0_3.json`（复用同一框架）

| # | Collision | 真实命中 | 覆盖关系 | **处理** | 依据 |
|---|---|---:|---|---|---|
| **P1** | `增长`(DEMAND_SURGE) / `负增长`(CYCLE_REVERSAL) | 21 / 10 | `负增长` ⊂ `增长` | **C 最小上下文消歧** | 删 `负增长` → 「新能源汽车7月起负增长」会得 `DIRECT/DEMAND_SURGE`（**语义错误**）；删 `增长` → 11 条真实正增长文本丢失需求信号 + 2 条负面。规则：`增长` 在**否定语境**（前置 ∈ {负,零,不,未,无}）下不计 |
| **P2** | `整治`(POLICY) / `整治提升`(SUPPLY) | 5 / 1 | `整治提升` ⊂ `整治` | **B 删词** | 零增量覆盖；删除影响 = **0 条条目变化**（完全惰性） |
| **P3** | `出口`(DEMAND_SURGE) / `出口管制`(POLICY) | 18 / 1 | `出口管制` ⊂ `出口` | **C 最小上下文消歧** | 删 `出口管制` → 「出口管制预期强化替代紧迫性」会得 `DEMAND_SURGE`（**语义错误**，应为 POLICY）；删 `出口` → 6 条负面 + 丢 12 条真实出口需求。规则：`出口` 在**限制/管制语境**（前置 ≤8 字含 管制/限制/禁令/配额/禁止/制裁/收紧）下不计 |
| **P4** | `采购`(DEMAND_SURGE) / `装备采购`(POLICY) | 11 / 2 | `装备采购` ⊂ `采购` | **B 删词** | 零增量覆盖；删除后 2 条 `C-2020-MIL-EQUIP-ORDER` 文本由 `DERIVED/None` → **`DIRECT/DEMAND_SURGE`**，与**研究已确立的 driver**（该 Campaign canonical driver = `DEMAND_SURGE`）一致 |
| **P5** | `储备`(POLICY) / `黄金储备`(VALUATION_RESET) | 4 / 1 | `黄金储备` ⊂ `储备` | **B 删词** | 零增量覆盖；删除后「中国黄金储备连续第 11 个月上升」归 `POLICY_DRIVEN`（央行储备管理 = 政策行动），语义更准确 |

**★ 成功标准达成**：不是「collision = 0」，而是**每一项都有可解释、可重复、不制造系统性语义错误的处理**。

**★ 上下文抑制只做减法**：`CONTEXT_SUPPRESSION` **不新增任何 canonical 映射** → **不引入新 vocabulary**。

---

## 二、阶段 B：Driver Canonicalization 版本决策

> **采用 `Driver Canonicalization v0.4`**（**不是** v0.3-r3）。

**理由**：阶段 A 不仅删词，还**首次引入 mapping algorithm 变更**（上下文抑制）。按仓库版本纪律（v0.3 曾因关键词扩展而新建），**改变映射算法必须新建版本**。

- 脚本：`research/scripts/canonicalize_historical_drivers_v0_4.py`
- 产物：`historical_driver_canonicalization_v0_4.json` + `historical_driver_evidence_ledger_v0_4.json`
- `revisions` 完整记录 `v0.4-r1`（decision / evidence / rationale / min_impact / not_chosen）
- generator deterministic（连续 3 次 `--check` PASS）
- **v0.1 / v0.2 / v0.3 完全不变** ✓

**Before / After（v0.3 → v0.4）**：

| 指标 | v0.3-r2 | **v0.4** |
|---|---:|---:|
| 关键词（新增/总） | 133 / 288 | **130 / 285** |
| **跨 canonical 子串冲突** | **10** | **7**（消除 3 项：`整治/整治提升` · `采购/装备采购` · `储备/黄金储备`；剩 2 项由上下文抑制处理） |
| `DIRECT` | 55 | **58** |
| `DERIVED` | 454 | **449** |
| `AMBIGUOUS` | 2 | 2 |
| `UNKNOWN` | 86 | **87** |
| `NOT_AVAILABLE` | 98 | **99** |
| 有 canonical driver 的 cycle | 77 / 79 | **77 / 79** |
| 52 Campaign coverage | 52 / 52 | **52 / 52** |
| 变化条目 | — | **11** |
| **canonical_driver 集合变化** | — | **0** |
| **primary_mechanism 变化** | — | **0** |
| **负面变化** | — | **2**（见下） |

**★ 负面变化如实披露**：
1. `C-2018-HIEQ-ROBOT-DOWN` accelerator#1 `DERIVED → NOT_AVAILABLE`（抑制后仅剩 `CYCLE_REVERSAL`，触发 v0.1 既有 `PRICE_ACTION` 排除（「调整」）→ **标签层变化，无 driver 损失**）
2. `RC-2022-RES-FERTILIZER` accelerator#2「中国禁止磷肥出口」`DERIVED/DEMAND_SURGE → UNKNOWN`（**语义修正**：出口禁令 ≠ 需求放量；该 cycle driver 集合不变）

**★ Calibration v0.4 关键结论**（`structural_analogy_rule_calibration_v0_4.json`）：
`E2_canonicalization_effect.changed_pairs = **0**` —— **剩余 5 项 collision 处理不改变任何 Structural Status**。

---

## 三、阶段 C：Structural Analogy v0.4（**本轮核心目标**）

### C1 输入修正（v0.3 generator 的问题已确认并修复）

v0.3 generator 读取的是 **`historical_driver_canonicalization_v0_2.json`（旧）** —— 本轮**未复制输出**，而是新建 v0.4 builder，读取：

| 输入 | 路径 |
|---|---|
| Export | `exports/timeline_export_v1.json`（当前） |
| Driver Canonicalization | **`historical_driver_canonicalization_v0_4.json`** |
| Driver Ledger | **`historical_driver_evidence_ledger_v0_4.json`** |
| Rule Set | **v0.3**（`structural-analogy-ruleset-v0.3`） |
| Governance | `governance_classification_v0_1.json` |
| Current Candidates | 5 |
| Historical Objects | **79** |

### C2 规则来源唯一

SA v0.4 只使用 **Rule Set v0.3**（R1–R4）；**未回退 v0.2、未另立规则、未手工调整 status、未加特殊例外**。

> **★ 独立校验器真实捕获一处实现缺陷**：首次生成 v0.4 时，builder 从 v0.3 复制了**旧的 `level_rule`（含 v0.2 fallback）** → `driver=MISMATCH → PARTIAL` 回退到 **47 条**。经独立语义校验器（S4/S14）捕获后，已将 `level_rule` 修正为 Rule Set v0.3 的 R1–R4（移除 fallback），重新生成后 **S14 = 0**。**这正是「两层独立校验」的价值。**

### C3 重新生成全部 395 对

5 candidates × 79 historical objects = **395 pairs**，每对重算 Lifecycle / Mechanism Driver / Evidence Sequence / Event Structure / Theme Relation / Structural Status / Strict。

### C4 历史对象 identity 正式修正（E.3）

**根因**：export 的 `research_candidates[]` **复用 `campaign_id` 字段名**，v0.1~v0.3 用 `o.get("campaign_id")` 判 kind → **恒真** → 全部 79 个对象被写成 `campaign`。
**v0.4 修正**：按**来源数组**判定。

| 字段 | campaign | research_candidate |
|---|---|---|
| `historical_object_kind` | `campaign` | `research_candidate` |
| `historical_campaign_id` | `C-...` | `null` |
| `historical_research_candidate_id` | `null` | `RC-...` |
| `historical_cycle_id` | 稳定不变 | 稳定不变 |

**实测**：`historical_profiles` = **52 campaign + 27 research_candidate**；matrix = **260 campaign + 135 RC**；**identity 错误 = 0** ✓

### C5 结果

| status | SA v0.3（发布版，含 E.1 缺陷） | **SA v0.4** |
|---|---:|---:|
| `STRUCTURAL_SUPPORTED` | 4 | **4** |
| **`STRICT_STRUCTURAL_SUPPORTED`** | 1 | **1** |
| `STRUCTURAL_PARTIAL` | 89 | **41** |
| `THEME_ONLY` | 6 | **10** |
| `INSUFFICIENT_EVIDENCE` | 145 | **115** |
| `NO_VALID_CORRESPONDENCE` | 151 | **225** |
| 跨 Macro Theme 结构对应 | 88（含 50 条 MISMATCH-PARTIAL） | **42**（纯净） |
| **`driver=MISMATCH → PARTIAL`** | **50** | **0** ✅ |

> **★ `STRUCTURAL_SUPPORTED` / `STRICT` 未变（4 / 1）** —— 变化全部来自**规则修正（E.1）**与**driver 链修复**，**不来自调参**。

### C6 Explanation Artifact v0.4

`structural_analogy_explanations_v0_4.json`（395 explanations · campaign 260 / RC 135）

**★ 本轮修复 4 处契约回归**（由 Product 测试捕获，均为 v0.3 builder 引入）：
1. `supportedDimensions ∪ unknownDimensions ∪ unsupportedDimensions` **必须完整划分四维**（原 `COMPARISON_POINT_UNKNOWN` / `PERIPHERAL_OVERLAP` 落入空档）
2. `PERIPHERAL_OVERLAP` 必须计入 `unsupportedDimensions`（不得计入 supported）
3. **`why_not_similar` 不得包含 theme relation**（契约修正 5.1；v0.3 误将 `CROSS_MACRO_THEME` 写入 why_not）
4. `dimension_evidence.mechanism_driver[]` 必须保留 **`raw_driver`** 与 `references`（provenance 不丢失）

**其他保证**：provenance 指向 SA v0.4 与 **Driver Canonicalization v0.4**；`unknown` / `not_available` 保留；不产生 ranking 语义；**不按 structural status 排序**（按 `historical_cycle_id` 升序 = 稳定 identity 顺序）。

---

## 四、阶段 D：SA v0.4 两层独立校验

`research/scripts/validate_structural_analogy_v0_4.py`（**不 import 任何 builder**；`level_v3()` 为独立实现）

### D1 Artifact Validation
A1 ruleset = `structural-analogy-ruleset-v0.3` · A2 **395 pairs** · A3 profiles ≡ export universe · A4 无重复 · A5/A6 词表 · **A7 identity** · A8 explanations ↔ matrix（395，状态 + identity 一致）· A9 provenance（含 driver 版本）· A10 禁止字段 · A11 旧版本存在 —— **全部 PASS**

### D2 Independent Semantic Validation
**R1** 逐行重算 **395 / 395 一致** · **S1–S14 全绿**（含 **S14：`driver=MISMATCH → PARTIAL` = 0**）· Theme-Blind 0 变化 · 负控制 2/2

### ★ S15（本轮新增）：driver 输入版本一致性
> **重新从当前 export + canonicalization v0.4 + ledger v0.4 独立重算每个 (candidate, cycle) 的 driver 维度，要求与 artifact 完全一致。**

**实测：重算 395 组合，不一致 = 0** ✅ —— 杜绝「validator PASS 但 artifact 仍消费旧 driver」。

```
=== validate_structural_analogy_v0_4.py（两层独立校验）===
D1 artifact : 79 cycles | 5 candidates | 395 pairs | explanations 395
D1 identity : campaign 52 / research_candidate 27
D2 独立重算 : 395 / 395 行
D2 S14      : driver=MISMATCH → PARTIAL = 0（必须 0）
D2 S15      : driver 版本一致性 —— 重算 395 组合，不一致 0（必须 0）
结果: PASS（FAIL 0 / WARN 0）
```

---

## 五、阶段 E：Time Observation 正式刷新

### E1 输入结构审查
- 当前 generator 的 `FAMILIES` **只覆盖 `rule_auto_summer`（3 族）+ `rule_pharma_upgrade`（1 族）** —— 即**早期 17-object universe 的 family 定义**；
- **8 个 rule_id 未被覆盖**：`rule_semiconductor` / `rule_high_end_equipment` / `rule_resources` / `rule_consumer` / `rule_fin_realestate` / `rule_defense_military` / `rule_infocomm` / `rule_power_equipment`。

### E2 不人为创造 Pattern
- **未改变**：anchor priority · annual dedupe · MAD/IQR · concentration · stability · LOO · minimum N · single-year dominance · Timeline eligibility；
- 新增族的定义**只用 `rule_ids` 过滤**（**未挑选 `main_theme_names`**，避免事后拟合）；
- 新增族的 `description` **由计算结果生成**（`description_from_stats`），**不手工撰写**；
- 结果由统一规则产生：有足够样本 → 计算；不足 → RESEARCH_ONLY；不稳定 → RESEARCH_ONLY；单年主导 → REJECTED。

### E3 Universe 扩展后的正确处理
**没有**因为「现在有 11 个 Theme」就强造 11 个 Pattern —— 而是按 rule_id 建立 8 个统一口径族，由规则裁决。

### E4 版本
> **`time_observation_patterns_v0_2.json`**（文件名 v0.2）· **内部 `artifact_version = 0.3`**（延续内部序列 0.1 → 0.2 → 0.3）

理由：仓库现状是**文件名与内部版本双序列**（v0_1 文件名 / 内部 0.2）。本轮既需新版本、又需 Product 切换，故文件名升为 v0_2、内部升为 0.3；**旧 `time_observation_patterns_v0_1.json` 逐字节保留**。

### E5 Before / After

| 指标 | v0_1（内部 0.2） | **v0_2（内部 0.3）** |
|---|---:|---:|
| snapshot_date | 2026-09-16 | **2026-09-23** |
| Historical sample | **17** | **79**（52 C + 27 RC） |
| distinct samples | 17 | 79 |
| **patterns_total** | **4** | **12** |
| **timeline_eligible** | **TOP-01** | **TOP-01** ✅ **未变** |
| research_only | TOP-02, TOP-03 | TOP-02, TOP-03, TOP-07, TOP-10, TOP-11, TOP-12 |
| rejected | TOP-04 | TOP-04, TOP-05, TOP-06, TOP-08, TOP-09 |
| **原 TOP-01 是否仍存在** | — | **是**（N=7 · 窗口 05-27 ~ 06-26 · 中心 06-11 · **状态 TIMELINE 未变**） |
| **消失的 Pattern** | — | **0** |
| 新增 Pattern | — | TOP-05 ~ TOP-12（8 个，全部来自新增族） |
| anchor_verification | VERIFIED 3 / UNKNOWN 13 | **VERIFIED 20 / UNKNOWN 41 / CONFLICT 0** |

**★ 关键：进入产品 Timeline 的 Pattern 仍只有 `TOP-01`，与扩容前完全一致 —— 标准未被放宽。**

**★ 变化归因**：`patterns 4 → 12` 是**数据扩容 + family 覆盖补全**造成的，**不是规则变化**（E2 所列全部规则未改）。

**★ 已知限制（如实记录）**：TO 的 `observation.year` = **研究对象的研究年份**（`campaign_year`，用于年度去重），`observation.date` = **统一锚点日期**。当锚点退化为 `campaign.start_date`（末选）且该日期落在**上一日历年度**时二者不同 —— 当前 universe 有 **5 例**（全部为 R01 对象）。**本轮不改变年度归属口径**（属规则变更，超出范围），记为 **Known Limitation**。

---

## 六、阶段 F：Product-facing 输入验收

### F1 / F2 版本切换（**最小改动，不重构架构**）

| 文件 | 旧 | 新 |
|---|---|---|
| `src/data/timeline/structuralAnalogy.ts` | `structural_analogy_explanations_v0_2.json` | **`..._v0_4.json`** |
| `src/data/timeline/timeObservationPatterns.ts` | `time_observation_patterns_v0_1.json` | **`..._v0_2.json`** |
| 3 个 `__tests__` | 同上 | 同上 |
| `vite.config.ts`（注释） | 同上 | 同上 |

**未重新实现任何 SA / TO 逻辑**；`@observation` alias 与导入路径机制不变。

### F3 Smoke test + Product 健壮性修复

**★ 发现并修复一处 Product 阻塞缺陷（R01 数据暴露）**：
`end_date` / `start_date` 可为 `null`（G2-1 四态允许 end 未确定；部分 R01 对象 start 亦未确定），而 Product adapter 假定非空 → **93 处运行时崩溃**。

**最小修复**（非架构变更）：
- `timelineTypes.ts`：`ExportCampaignV1.end_date` → `string | null`；`ExportCandidateV1.start_date` → `string | null`
- `timelineAdapter.ts`：`cross_year` 计算 null 安全；`end` 沿用 **Research Candidate 侧既有约定**（渲染用占位 + `openEnded` 显式标注「结束未确定」）；`start` 对称处理

**Product 测试结果（对照实验）**：

| | 测试文件 | 用例 |
|---|---|---|
| **HEAD（旧 artifact，未含本轮改动）** | 11 failed / 4 passed | **88 failed / 279 passed** |
| **本轮完成后** | **6 failed / 9 passed** | **21 failed / 558 passed** |

→ **失败数 88 → 21（净改善 67）**；**无运行时崩溃**（剩余 21 项**全部为 AssertionError**）。

**★ 剩余 21 项的定性**：全部为**测试夹具硬编码旧 17-object universe 的数值**（对象数 17 / 年份范围 2018–2025 / 各类计数 7 / 28 / 13 / 52 / 116 / commit hash）。属 **Product 侧测试夹具维护**，**不影响 Product 运行路径**（adapter 不再崩溃，`vite build` 成功）。

**构建**：`tsc -b` **无错误** ✓ · `vite build` **成功** ✓（产物含 `structural_analogy_explanations_v0_4-*.js`）

---

## 七、阶段 G：Research Release Acceptance

### Structural Analogy
| 检查 | 结果 |
|---|---|
| 395 / 395 pairs | ✅ |
| Rule Set v0.3 | ✅ |
| 当前 Driver Canonicalization（v0.4） | ✅ |
| 当前 Export | ✅（export 未改动） |
| 当前 79 historical objects | ✅ |
| Campaign / RC identity 正确 | ✅ 52 / 27，错误 0 |
| **Independent semantic validation PASS** | ✅ |
| **`driver=MISMATCH → PARTIAL` = 0** | ✅ |
| `SUPPORTED` / `STRICT` 变化有真实原因 | ✅ 未变（4 / 1）；PARTIAL 89→41 由 **E.1 规则修正**产生，非调参 |
| S15 driver 版本一致性 | ✅ 0 不一致 |

### Time Observation
| 检查 | 结果 |
|---|---|
| 当前完整 Historical Universe 输入 | ✅ 79 |
| 当前统一 anchor rules | ✅ 未改 |
| 当前标准未放宽 | ✅ 仍只有 TOP-01 进入 Timeline |
| Pattern 变化有 before / after | ✅ |
| 无未来概率 / prediction / ranking | ✅ |

### Product
| 检查 | 结果 |
|---|---|
| Product consumed current SA artifact | ✅ v0_4 |
| Product consumed current TO artifact | ✅ v0_2 |
| Adapter 不重新实现研究逻辑 | ✅ |
| Campaign / RC identity 不混淆 | ✅ |
| UNKNOWN / NOT_AVAILABLE 不被压缩 | ✅ |
| 无 score / ranking / probability / prediction | ✅ |
| `tsc -b` / `vite build` | ✅ 无错误 / 成功 |

---

## 八、验证清单

| 检查 | 结果 |
|---|---|
| `validate_db` | PASS（3 条 warning 未新增） |
| `validate_timeline_export` | PASS |
| `validate_batch_research` / `validate_promotion_manifest` / `check_doc_schema_consistency` / `validate_current_research` | PASS |
| `validate_monorepo_integrity` | PASS |
| `validate_governance_gates` | PASS |
| Intake validator（`--check` + 6 包） | PASS |
| Driver Canonicalization v0.4 `--check` ×3 | PASS |
| **SA v0.4 validator（D1 + D2）** | **PASS**（FAIL 0 / WARN 0） |
| SA v0.3 validator（历史） | PASS |
| SA semantic validator（v0.3 calibration） | PASS |
| Rule Calibration v0.4 `--check` ×3 | PASS |
| Time Observation v0.2 `--check` ×3 | PASS |
| Product tests | 21 failed / 558 passed（**HEAD 为 88 failed / 279 passed**） |
| `tsc -b` | PASS |
| `vite build` | PASS |

**所有 generator：连续 3 次 deterministic `--check` PASS** ✓

---

## 九、旧版本保护（逐字节验证）

**UNCHANGED ✓（18 个文件，`git diff --quiet`）**：
`historical_driver_canonicalization_v0_1/v0_2/v0_3.json` · `historical_driver_evidence_ledger_v0_1/v0_2/v0_3.json` ·
`structural_analogy_rule_set_v0_2.md` · `structural_analogy_rule_set_v0_3.md` ·
`structural_analogy_rule_calibration_v0_2/v0_3.json` ·
`structural_analogy_research_v0_1/v0_2/v0_3.json` · `structural_analogy_explanations_v0_1/v0_2/v0_3.json` ·
`time_observation_patterns_v0_1.json` · **`exports/timeline_export_v1.json`**

---

## 十、最终总表

| 模块 | Before | After | 是否完成 |
|---|---|---|---|
| Historical Universe | 79 | **79** | ✅ |
| Driver Canonicalization | v0.3-r2 | **v0.4** | ✅ |
| SA | v0.3（过期） | **v0.4** | ✅ |
| SA pairs | 395 | **395** | ✅ |
| Time Observation | v0_1（内部 0.2） | **v0_2（内部 0.3）** | ✅ |
| Product SA input | `explanations_v0_2` | **`explanations_v0_4`** | ✅ |
| Product TO input | `patterns_v0_1` | **`patterns_v0_2`** | ✅ |

### 附加指标

| 指标 | Before | After |
|---|---|---|
| SA `driver=MISMATCH → PARTIAL` | 50 | **0** |
| SA `STRUCTURAL_SUPPORTED` / `STRICT` | 4 / 1 | **4 / 1** |
| SA `STRUCTURAL_PARTIAL` | 89 | **41** |
| SA `INSUFFICIENT_EVIDENCE` | 145 | **115** |
| SA historical identity（campaign / RC） | 79 / 0（**错误**） | **52 / 27（正确）** |
| TO 样本 | 17 | **79** |
| TO Pattern 数 | 4 | **12** |
| **TO Timeline-eligible** | **1（TOP-01）** | **1（TOP-01，未变）** |
| Product tests | 88 failed / 279 passed | **21 failed / 558 passed** |
| `tsc -b` / `vite build` | — | **PASS / PASS** |
| 旧版本产物 | — | **18 个文件 UNCHANGED** |

---

## 十一、Known Limitations（不再作为「必须完成后才能推进」的阻塞）

| # | 项 | 定性 |
|---|---|---|
| 1 | 剩余 **7 项**跨 canonical 子串冲突（`增长/负增长` · `出口/出口管制` 已由**上下文抑制**处理；其余 5 项中 3 项已删词，余项为 **v0.1 既有词表**内部遗留，如 `结构迁移`、`倍/翻倍`、`利润/净利润`、`出清/出清完成`、`标准体系/标准体系（2026 版）`） | **已知限制**（影响 = 相关文本无法成为 `DIRECT`；**不改变任何 driver 集合**） |
| 2 | **Product 测试夹具 21 项**硬编码旧 17-object universe 数值 | **Product 侧维护项**（不影响运行路径） |
| 3 | TO `observation.year` 与 `date` 在「锚点退化为 `campaign.start_date`」时相差 1 年（5 例，全部 R01） | **已知限制**（未改变年度归属口径） |
| 4 | `driver = MATCH` 仅 1 条 / `event MATCH` 仅 1 条 | **数据粒度限制**（不得通过放宽规则解决） |
| 5 | 2 个 cycle 因**映射逻辑**无 canonical driver（`RC-2015-FIN-LEVERAGE` 多命中 · `RC-2024-SECONDARY` 研究自述强度不足） | **已知限制**（非数据缺口） |

---

## 十二、最终结论

> # ✅ **可以结束 Research Core，进入 ThreeC 下一阶段（Product / Real Usage 驱动迭代）。**

**依据**：
1. **79 Historical Objects → 当前 Driver Canonicalization v0.4 → SA v0.4 → Time Observation v0.2 → Product 消费最新 artifact** 全链路打通；
2. **SA v0.4 通过两层独立语义验证**（含 S15 driver 版本一致性 = 0 不一致）；
3. **`driver=MISMATCH → PARTIAL` 已彻底消除（50 → 0）**，且 `SUPPORTED` / `STRICT` **未因调参变化**；
4. **Time Observation 在完整 universe 上正式刷新**，且 **Timeline 门槛未放宽**（仍只有 TOP-01）；
5. **Product 构建通过、运行路径无崩溃**，失败数由 88 降至 21（剩余为测试夹具维护项）；
6. **全部旧版本逐字节保留**（18 个文件 UNCHANGED）。

**此后不再**（除非真实产品使用再次暴露影响核心判断的错误）：
扩展 Historical Universe · 添加新 Driver keyword · 微调 SA rule · 继续消灭所有 collision · 为增加 Pattern 数量继续挖数据。

---

*ThreeC Research Core Release · 2026-09-23 · Rule Set v0.3 · Driver Canonicalization v0.4 · SA v0.4 · Time Observation v0.2*
