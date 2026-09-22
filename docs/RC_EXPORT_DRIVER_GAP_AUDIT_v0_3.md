# RC Export Driver 缺口审计与修复报告（v0.3）

> | 项目 | 值 |
> |---|---|
> | **性质** | **18 个 Research Candidate 的 Export `drivers` 缺口审计 + 数据链路修复** |
> | **基线** | HEAD `0e1d2f4` · a/b `0/0` · worktree clean |
> | **结论** | **18 / 18 全部为 Export 映射链路丢失（Class A）· 0 个为原始证据不足（Class B）** |
> | **是否需要改 Export Contract** | **不需要** —— `drivers` 字段已在白名单内，本次只补 **值**、未改 **字段** |
> | **未做** | 未生成 SA v0.4 · 未刷新 Time Observation · 未改 Rule Set v0.3 · 未改 Driver Canonicalization v0.3 关键词 · 未处理 `扩产/扩产周期` · 未处理 6 项 substring collision · 未改 DB schema · 未改 taxonomy · 未重新研究 R01 · 未猜测或补写机制 |
> | **新增产物** | `research/research/reports/rc_export_driver_gap_audit_v0_3.json` · `research/scripts/audit_rc_export_driver_gap.py` |

---

## 1. Driver 数据的真实链路（**追源头**）

```
① Intake Package  candidates[].drivers            ← raw 研究文本（已通过 Intake Review）
        ↓  （人工转写映射层）
② batch_auto_research.py::CANDIDATE_DRIVERS        ← ★ 缺口发生在这里
        ↓
③ exports/timeline_export_v1.json  research_candidates[].drivers
        ↓  （**只读 ③**）
④ historical_driver_canonicalization_v0_3.json
        ↓
⑤ historical_driver_evidence_ledger_v0_3.json
```

> **★ 结构性事实**：**③ 是 ④ 的唯一输入**。
> 因此「canonicalization / ledger 已有 driver 而 Export 为空」**在结构上不可能出现** ——
> 真正的缺口只能发生在 **① → ② → ③** 这段映射链上。

### 1.1 缺口的直接原因（已定位到行）

```python
# batch_auto_research.py（修复前）
"drivers": CANDIDATE_DRIVERS.get(rcid, {"start": [], "accelerator": [], "turning": [], "ending": []}),
```

- 修复前 `CANDIDATE_DRIVERS` 只有 **9 条**（原 R00 期 4 条 + R01-06 新增 5 条）；
- 其余 **18 个 RC 落回空默认值** → 与实测的 18 个空 drivers **完全对应**；
- 这 18 个 RC 在 `RESEARCH_CANDIDATES` 中注册时，**遗漏了本映射层的 driver 条目**。

### 1.2 §四「特别检查」逐项回答

| 检查项 | 结果 |
|---|---|
| 是否存在 `canonical_driver` 非空但 export 为空 | **不可能**（④ 只读 ③）→ 实测 0 |
| export builder 对 `campaign` 与 `research_candidate` 是否用不同字段 | ✅ **是** —— campaign 用 `CAMPAIGN_DRIVERS`（52/52 齐全），RC 用 `CANDIDATE_DRIVERS`（9/27） |
| 是否存在「只导出 Campaign、不导出 RC driver」的分支 | ❌ 否 —— 两条路径都存在，但 RC 侧**映射表覆盖不全** |
| 是否存在 RC driver 在某中间 artifact 存在、最终 export 被丢弃 | ✅ **是** —— 存在于 **① intake**，在 **②** 未被转写 |
| 是否因 Export Contract 白名单被合法排除 | ❌ 否 —— `drivers` 已在 `CANDIDATE_FIELDS` 白名单内 |
| **是否需要扩大 Export Contract** | ❌ **不需要**（只补值，未改字段） |

---

## 2. 18 个 RC 的完整缺口表

| cycle_id | intake 包/候选 | intake drivers | export drivers | canonical_driver（修复前） | **缺口层级** |
|---|---|---:|---:|---|---|
| `RC-2024-HIEQ-EQUIP-UPDATE` | R01-01 / `R01-HIEQ-006` | **13** | 0 | — | **MAPPING_GAP** |
| `RC-2024-HIEQ-HUMANOID-MASS` | R01-01 / `R01-HIEQ-007` | **13** | 0 | — | **MAPPING_GAP** |
| `RC-2022-SEMI-CHIPSHORTAGE` | R01-02 / `004` | **10** | 0 | — | **MAPPING_GAP** |
| `RC-2024-SEMI-FUND3` | R01-02 / `008` | **9** | 0 | — | **MAPPING_GAP** |
| `RC-2015-SEMI-LEVERAGE` | R01-02 / `010` | **6** | 0 | — | **MAPPING_GAP** |
| `RC-2017-GPU-MINING` | R01-02 / `012` | **6** | 0 | — | **MAPPING_GAP** |
| `RC-2016-RES-CHEM-ENV` | R01-03 / `011` | **9** | 0 | — | **MAPPING_GAP** |
| `RC-2017-RES-ALUMINUM` | R01-03 / `010` | **13** | 0 | — | **MAPPING_GAP** |
| `RC-2020-RES-GOLD-RATES` | R01-03 / `006` | **12** | 0 | — | **MAPPING_GAP** |
| `RC-2022-RES-FERTILIZER` | R01-03 / `008` | **13** | 0 | — | **MAPPING_GAP** |
| `RC-2025-RES-COPPER` | R01-03 / `009` | **12** | 0 | — | **MAPPING_GAP** |
| `RC-2020-CONS-SMALL-APPLIANCE` | R01-04 / `007` | **7** | 0 | — | **MAPPING_GAP** |
| `RC-2024-CONS-PET-FOOD` | R01-04 / `013` | **4** | 0 | — | **MAPPING_GAP** |
| `RC-2024-RE-POLICY-517` | R01-05 / `R01-FINRE-002` | **6** | 0 | — | **MAPPING_GAP** |
| `RC-2019-RE-EASING` | R01-05 / `R01-FINRE-003` | **5** | 0 | — | **MAPPING_GAP** |
| `RC-2020-FIN-BROKER-VOLUME` | R01-05 / `R01-FINRE-009` | **5** | 0 | — | **MAPPING_GAP** |
| `RC-2016-RE-SHANTY` | R01-05 / `R01-FINRE-011` | **6** | 0 | — | **MAPPING_GAP** |
| `RC-2015-FIN-LEVERAGE` | R01-05 / `R01-FINRE-012` | **5** | 0 | — | **MAPPING_GAP** |

**合计**：intake drivers **154 条** → export **0 条**。

### 2.1 按证据分类（用户 §三）

| 类别 | 数量 | 判定 |
|---|---:|---|
| **A 类：上游有 driver，Export 丢失** | **18** | ✅ 全部属此类 → **只修映射链路** |
| **B 类：原始 Research 本身无足够 driver** | **0** | 无 —— **未对任何 cycle 标记 `INSUFFICIENT_DRIVER_EVIDENCE`** |

> **18 个 RC 的 intake `drivers` 均为实质研究文本**（如「三道红线」类制度表述、「棚改货币化安置形成的需求侧机制」、
> 「大基金二期聚焦设备/材料」等），**不是占位符**。

---

## 3. 修复方式（**只做数据转写，未新造机制**）

在 `batch_auto_research.py::CANDIDATE_DRIVERS` 中补齐 18 条条目，**从对应 intake 包 `candidates[].drivers` 逐字转写**。

**约束遵守**：
- ✅ **未改变 canonical driver 判定**（未改 `canonicalize_historical_drivers_v0_3.py` —— `git diff --quiet` **UNCHANGED**）
- ✅ **未新造 driver**（全部为 intake 原文转写，无改写、无补写）
- ✅ **未修改 Rule Set v0.3**（`structural_analogy_rule_set_v0_3.md` **UNCHANGED**）
- ✅ **未修改 Driver Canonicalization v0.3 关键词**（脚本 **UNCHANGED**）
- ✅ **未扩大 Export Contract**（`drivers` 已在白名单内）
- ✅ **未改 DB schema / taxonomy / R01 研究**

**规模**：`CANDIDATE_DRIVERS` **9 → 27 条**（覆盖全部 27 个 RC）。

---

## 4. 修复前 / 后对比

### 4.1 Export（③）

| 项 | 修复前 | **修复后** |
|---|---:|---:|
| RC 总数 | 27 | 27 |
| **RC `drivers` 为空** | **18** | **0** ✅ |
| RC driver 条目合计 | 58 | **212** |

**Export 差异范围（深度比对）**：

| 检查 | 结果 |
|---|---|
| 顶层 keys | **完全一致** ✅ |
| `campaigns` 数 | 52 → 52 · **除 `drivers` 外 0 变化** · **campaign `drivers` 0 变化** ✅ |
| `research_candidates` 数 | 27 → 27 · **除 `drivers` 外 0 变化** ✅ |
| **`drivers` 有变化的 RC** | **恰好 18 个**（即目标 18 个）✅ |
| `rules` / `signals` / `events` / `securities` | **完全一致** ✅ |
| `manifest`（除 `generated_at`/`source_commit`） | **完全一致** ✅ |
| `conflicts` 数组 | **完全一致** ✅ |
| **DB ↔ Export 一致性** | DB 52 ↔ Export 52 · DB-only 0 · Export-only 0 · 字段不一致 **0** ✅ |
| DB 表计数 | `campaigns 52` / `themes 52` / `evidences 354` —— **未改** ✅ |

### 4.2 Canonicalization v0.3（④⑤）

| 项 | 修复前 | **修复后** |
|---|---:|---:|
| ledger 条目 | 541 | **695**（+154 = 18 个 RC 的 intake driver 数） |
| `DIRECT` | 55 | **55**（未变） |
| `DERIVED` | 337 | **454** |
| `AMBIGUOUS` | 1 | **2** |
| `UNKNOWN` | 59 | **86** |
| `NOT_AVAILABLE` | 89 | **98** |
| **有 canonical driver 的 cycle** | **60 / 79** | **77 / 79** ✅ |
| **无 canonical driver 的 cycle** | **19** | **2** |
| **无 driving 文本的 cycle** | **18** | **0** ✅ |

**canonical driver 计数**：`POLICY_DRIVEN 56→75` · `DEMAND_SURGE 47→62` · `SUPPLY_CONTRACTION 47→69` ·
`CYCLE_REVERSAL 31→40` · `VALUATION_RESET 24→30` · `TECH_BREAKTHROUGH 13→16` ·
`EVENT_CATALYST 18→18` · `INDUSTRY_UPGRADE 10→10`

### 4.3 SA Calibration v0.3（对已发布 SA v0.3 基线）

| status | 修复前 | **修复后** |
|---|---:|---:|
| `STRUCTURAL_SUPPORTED` | 4 | **4**（未变） |
| `STRICT_STRUCTURAL_SUPPORTED` | 1 | **1**（未变） |
| `STRUCTURAL_PARTIAL` | 39 | **40** |
| `THEME_ONLY` | 9 | **10** |
| **`INSUFFICIENT_EVIDENCE`** | **125** | **115**（−10） |
| `NO_VALID_CORRESPONDENCE` | 218 | **226** |

**归因（相对已发布 SA v0.3 基线的 109 条变化）**：
`PARTIAL→NO_VALID 64`（E.1 规则）· **`INSUFFICIENT→NO_VALID 24`** · **`INSUFFICIENT→PARTIAL 5`** ·
**`INSUFFICIENT→THEME_ONLY 1`**（后三项共 **30 条**由本轮 driver 修复驱动）·
`NO_VALID→PARTIAL 12` · `PARTIAL→THEME_ONLY 2` · `NO_VALID→THEME_ONLY 1`

> **★ E.1 修复未被破坏**：`driver = MISMATCH` 的 `STRUCTURAL_PARTIAL` = **0**（D 组）✅
> **★ `STRUCTURAL_SUPPORTED` / `STRICT` 未受影响（4 / 1）** —— 本轮只把 cycle 从「资料不足」移出，
> 未提升任何强结构对应。

### 4.4 仍无 canonical driver 的 2 个 cycle（**均非数据缺口**）

| cycle | 原因 | 性质 |
|---|---|---|
| `RC-2015-FIN-LEVERAGE` | driving 文本「政策宽松（货币与流动性）」命中 **2 条规则**（`POLICY_DRIVEN` + `VALUATION_RESET`）→ 按既有映射逻辑落 `DERIVED`（**无 canonical**）；「成交额大幅放大…涨幅」命中 `PRICE_ACTION` → `NOT_AVAILABLE` | **映射逻辑（多命中无消歧）** —— §一 禁止修改映射逻辑 → **保持现状** |
| `RC-2024-SECONDARY` | 全部 driving 文本为 `NOT_AVAILABLE`（「退潮后次级活跃（weak）」/「unknown（强度不足）」）；唯一机制命中在 `ending` 相位 | **研究自述「强度不足」** → 正确保持无 driving driver |

> 两者**均为冻结映射逻辑的诚实结果**，**不是 Export 丢失、也不是可猜测的缺口**。

---

## 5. 验证结果（全 PASS）

| 检查 | 结果 |
|---|---|
| `validate_timeline_export` | **PASS** |
| `validate_db` | **PASS**（**3 条 warning 未新增**） |
| `validate_batch_research` | **PASS** |
| `validate_current_research` | **PASS** |
| `validate_monorepo_integrity` | **PASS** |
| `validate_promotion_manifest` | **PASS** |
| `check_doc_schema_consistency` | **PASS** |
| `refresh --check` | **PASS** |
| `intake --check` | **PASS** |
| validator tests | **PASS**（44/44） |
| `validate_governance_gates` | **PASS** |
| **Driver Canonicalization v0.3 `--check`** | **PASS**（deterministic） |
| **Rule Calibration v0.3 `--check`** | **PASS**（deterministic） |
| **Structural Analogy v0.3 validator** | **PASS** |
| **Structural Analogy semantic validator** | **PASS**（1580/1580；S1–S14 全绿；S14 = 0） |
| **旧产物 / 冻结件逐字节未变** | **PASS**（v0.1/v0.2 canonicalization+ledger · Rule Set v0.2/v0.3 · Calibration v0.2 · **SA research v0.3** · **SA explanations v0.3** · `canonicalize_historical_drivers_v0_3.py` —— 全部 `git diff --quiet` UNCHANGED） |

---

## 6. ⚠️ 一项必须记录的**新不一致**（本轮修复的副作用）

**SA v0.3 产物相对修复后的 driver 链已过期。**

- `structural_analogy_research_v0_3.json` / `structural_analogy_explanations_v0_3.json` 是在**修复前**的
  driver 链上生成的，**本轮未重新生成**（§一「只处理 Export driver 数据链路 + PROJECT_STATE」+「不生成 SA v0.4」）；
- 因此其 `matrix[].driver` / `evidence_cards` 与当前的 `historical_driver_canonicalization_v0_3.json` **不一致**；
- **现有校验器不会捕获它**（`validate_structural_analogy_v0_3` 与语义校验器都是**自引用**的：
  前者读 SA 产物自身，后者读 calibration v0.3 自身）；
- **未修改 SA 产物的理由**：既不能「覆盖 SA v0.3」，也不允许「生成 SA v0.4」→ 保持原样并**显式记录**。

**建议**：由 **SA v0.4** 消费修复后的 driver 链（届时 `INSUFFICIENT_EVIDENCE` 预计再降 ~30 条、
`STRUCTURAL_PARTIAL` 与跨族结构对应数上升）。

---

## 7. 最终报告（逐项回答 §七）

| # | 问题 | 回答 |
|---|---|---|
| **1** | 18 个 RC 中多少属于 **Export 丢失** | **18 / 18（100%）** —— 全部为 `CANDIDATE_DRIVERS` 映射层遗漏（Class A） |
| **2** | 多少属于 **原始证据不足** | **0 / 18** —— 无任何 cycle 被标记 `INSUFFICIENT_DRIVER_EVIDENCE`；未猜测、未补写 |
| **3** | 是否需要修改 **Export Contract** | **不需要** —— `drivers` 字段已在白名单内；本次只补**值**、未改**字段**、未扩白名单 |
| **4** | 修复后是否还有**真正的数据层阻塞** | **无数据层阻塞** ✅ —— 无 driving 文本的 cycle **18 → 0**；RC 空 drivers **18 → 0**；<br>剩余 2 个无 canonical driver 的 cycle 属**映射逻辑**（多命中无消歧）与**研究自述强度不足**，**非数据缺口** |
| **5** | 下一轮是否可以进入 **`扩产 / 扩产周期` 处理** | ✅ **可以** —— 数据层阻塞已解除；`扩产/扩产周期` 属**词表级**问题，与数据链路无关，可独立处理 |

**当前剩余阻塞（更新后）**：
1. **Driver mapping collision audit** —— `扩产 / 扩产周期` 语义矛盾（**词表级**）+ 6 项跨 canonical 子串冲突（**映射逻辑级**）
2. **SA v0.3 产物相对修复后 driver 链已过期** → 须由 SA v0.4 消费
3. （观测）`driver = MATCH` 仅 1 条 / `event MATCH` 仅 1 条 —— 属数据粒度限制

**下一步建议顺序**：① 处理 `扩产 / 扩产周期` → ② 评估 6 项子串冲突的多命中消歧（独立版本 + 重新校准）
→ ③ 生成 **SA v0.4**（消费修复后的 driver 链）→ ④ 之后才考虑 **Time Observation** 刷新。

---

## 8. 本轮严格未做

- ❌ 未生成 **SA v0.4**；❌ 未刷新 **Time Observation**；
- ❌ 未修改 **Rule Set v0.3**（文档 UNCHANGED）；
- ❌ 未修改 **Driver Canonicalization v0.3 关键词**（脚本 UNCHANGED）；
- ❌ 未处理 **`扩产 / 扩产周期`**；❌ 未处理 **6 项 substring collision**；
- ❌ 未修改 **DB schema** / **taxonomy** / **Canonical DB** / **Export Contract**；
- ❌ 未重新研究 **R01**；
- ❌ **未为提高 driver coverage 而猜测或补写机制** —— 18 条条目全部为 intake 原文**逐字转写**；
- ❌ 未覆盖 **SA v0.3** 产物（research / explanations 均 UNCHANGED）。

---

*RC Export Driver 缺口审计与修复 · 2026-09-23 · 未生成 SA v0.4 · 未刷新 Time Observation*
