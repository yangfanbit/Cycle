# Historical Driver Canonicalization v0.1 · Structural Analogy Feasibility v0.3

> | 项目 | 值 |
> |---|---|
> | 性质 | **Research-layer Driver 规范化 + Feasibility v0.3（不是 Structural Analogy 实现）** |
> | 完成日期 | 2026-09-19 |
> | 起始状态 | `HEAD = origin/main = 3d81c67`，ahead/behind `0/0`，工作树 clean（**自行核对**） |
> | 对照基线 | Feasibility **v0.1 / v0.2（均保留不覆盖）** |
> | 未修改 | `src/**` · Product IA / UI · schema.sql · frozen export contract · Research Model v1.0 · 历史原始 driver 文本 · candidate driver · Time Observation v0.2–v0.5 |

---

## 1. Executive Summary

**目标**：解决 Structural Analogy 的主要剩余瓶颈 —— 历史侧 `drivers` 为自由文本，无法与 candidate 做可靠的机制级比较。

**做法**：建立 **Research-layer Canonical Driver Representation**，两侧统一到**仓库既有**的
`narrativeType` 枚举（`POLICY_DRIVEN / INDUSTRY_UPGRADE / TECH_BREAKTHROUGH / DEMAND_SURGE /
SUPPLY_CONTRACTION / VALUATION_RESET / CYCLE_REVERSAL / EVENT_CATALYST / UNKNOWN`）。

### ★ 最重要结论

> **Driver bottleneck 属于「部分解决」，且暴露出更本质的问题：**
> **不只是 vocabulary mismatch —— 而是 mechanism-level evidence insufficiency。**
>
> 换成更严的**机制轴**后，`MATCH 3 → 1`、`MISMATCH 6 → 29`、`TIER_1 21 → 4`。
> **v0.2 的「PARTIAL 71/85」有相当部分是「类别轴」造成的虚高** ——
> 只要两侧都有 `POLICY` 就记 PARTIAL，与「机制是否相同」无关。

### 四项关键发现

1. **★ 同族 ≠ 结构相似**：4 组同族配对中，**2 组在机制轴上 `MISMATCH`**
   （`BCI-MEDTECH × C-2019-PHARMA-INNOV`、`OPTICAL-LINK × C-2019-COMM-5G`）——
   而旧口径把两者都记作 `PARTIAL`。**机制轴能区分「同族但机制不同」。**
2. **★ `C-2023-AD`（智能驾驶）成为跨族强对应**：对 `BCI-MEDTECH` 与 `EMBODIED-AI`
   **双双**达到 `TIER_1`（共享 `POLICY_DRIVEN + TECH_BREAKTHROUGH`）——两者分属医药健康 / 高端装备。
3. **★ 排除价格结果污染**：154 条原始文本中 **49 条**是价格/行情**结果**描述
   （涨停 / 连板 / 涨 233% / 见顶…）→ 按 §十五 **不得作为 driver**，标 `NOT_AVAILABLE`。
4. **★ 相位拆分必要**：首次运行 `CYCLE_REVERSAL` 命中 26 条中 **25 条来自 turning/ending** ——
   那是「**周期如何终结**」，不是「**什么驱动了周期**」。拆分为 driving / terminal 后降至 9。

---

## 2. Repo Baseline

```
git status --short          → 无输出（clean）
git rev-parse HEAD          → 3d81c673ada01307380633a26efd5251a9e068ac
git rev-parse origin/main   → 3d81c673ada01307380633a26efd5251a9e068ac
git branch --show-current   → main
git diff --stat / --cached  → 空 / 空
ahead/behind                → 0  0
```
`git log --oneline -10`：`3d81c67`(HEAD, origin/main) → `ded84d7` → `fd5914f` → `d3fa89f` → `2c16058`
→ `052b79b` → `cc4c2d4` → `f446cb8` → `ff8b6eb` → `e85fb42`。
**无 staged / unstaged / untracked 文件。** 与任务书一致（**已自行核对**）。

---

## 3. Vocabulary（§三 / §二十七-1）

### Candidate-side canonical drivers（**复用，未新造**）
来源：`research/current/schema.json:definitions.narrativeType`

| canonical driver | candidate 出现次数 |
|---|---:|
| `POLICY_DRIVEN` | 4 |
| `TECH_BREAKTHROUGH` | 3 |
| `INDUSTRY_UPGRADE` | 3 |
| `DEMAND_SURGE` | 2 |
| `SUPPLY_CONTRACTION` | 1 |
| `VALUATION_RESET` / `CYCLE_REVERSAL` / `EVENT_CATALYST` | **0** |
| `UNKNOWN` | 0 |

### Historical-side

| 项 | 值 |
|---|---:|
| **raw driver 文本数** | **154**（17 个对象 × 4 桶） |
| 其中 driving 相位（start + accelerator） | **81** |
| 其中 terminal 相位（turning + ending） | **73** |
| **canonical driver 数（全相位）** | **8** |
| **canonical driver 数（driving 相位）** | **7** |

**Historical driving 相位 canonical 分布**：
`POLICY_DRIVEN 17` · `CYCLE_REVERSAL 9` · `VALUATION_RESET 9` · `DEMAND_SURGE 6` ·
`EVENT_CATALYST 5` · `TECH_BREAKTHROUGH 4` · `INDUSTRY_UPGRADE 2` · `SUPPLY_CONTRACTION 1`

**★ `HISTORICAL_NOT_AVAILABLE`**（candidate 有、历史侧无法表达）：
**无** —— 8 个 canonical 值在历史侧均有命中；反向地，`VALUATION_RESET` / `CYCLE_REVERSAL` /
`EVENT_CATALYST` 在 **candidate 侧**为 0（属 candidate 侧的未使用值，非缺口）。

---

## 4. Driver ≠ Event Type（§四 —— 本阶段最重要语义要求）

**已严格区分并写入 artifact 的 `semantic_rules`：**

| 概念 | 定义 | 本阶段用法 |
|---|---|---|
| **Event Type** | 发生了什么类型的事件（`policy`/`industry`/`company`/`market`/`macro`） | 仅用于 `event_structure` 维度 |
| **Driver** | 该周期由什么**机制**推动（`POLICY_DRIVEN`/`DEMAND_SURGE`/…） | 用于 `drivers` 维度 |

**明确禁止（写入 artifact `forbidden_inferences`）**：
`industry → DEMAND_IMPROVEMENT` · `company → EARNINGS_CONFIRMATION` · `capital → CAPEX_EXPANSION` ·
`market rising → SENTIMENT_POSITIVE` · **价格涨跌 / 结果变量 → 任何 driver**。

**★ 由此发现 v0.2 的口径问题**：v0.2 的 driver 维度用的是 `candidate.drivers[].category`
（`POLICY`/`INDUSTRY`/`CAPITAL`/`SENTIMENT`/`EXTERNAL`）—— 那是**来源/类别轴**，
且历史侧由 `EVENT_TYPE_TO_DRIVER(event_type)` 反推 —— **正是 §四 禁止的 `event_type → driver` 硬映射**。
v0.3 改用机制轴（`narrative_types` ↔ 历史 canonical drivers）。旧口径以
`drivers_legacy_category_axis` **保留作对照**。

---

## 5. Mapping Ontology 与规则（§五 / §六 / §七）

**mapping_status 定义**（写入 artifact，可审计）：

| status | 判据 |
|---|---|
| `DIRECT` | 命中**恰好 1 条**规则，**且**文本可追溯至 evidence/event/source 引用（`EV-`/`E-`/`S-`） |
| `DERIVED` | 命中 ≥2 条规则（需综合判断）；或命中 1 条但**无引用** |
| `AMBIGUOUS` | 命中 **≥4** 条规则 → 无法收敛，**不硬拆** |
| `UNKNOWN` | 有文本但无规则命中 → **不强行归类** |
| `NOT_AVAILABLE` | 文本为空 / 纯非机制表述 / **价格行情结果描述** |

**规则形态**：显式关键词表（8 个 canonical driver 各一组，见 artifact `rules`）。
**不使用** `event_type`、**不使用**价格/涨跌、**不使用**任何结果变量。
**可追溯链**：`canonical_driver` → `raw_driver` → `references`（EV-/E-/S-）→ `event_refs`（含 event_type/date）。

### 映射结果（154 条）

| mapping_status | 条数 | 占比 |
|---|---:|---:|
| **`DIRECT`** | **36** | 23.4% |
| **`DERIVED`** | **46** | 29.9% |
| **`AMBIGUOUS`** | **1** | 0.6% |
| **`UNKNOWN`** | **22** | 14.3% |
| **`NOT_AVAILABLE`** | **49** | 31.8% |

### 相位拆分（★ 关键修正）

| 相位 | 含义 | 用途 |
|---|---|---|
| `start` + `accelerator` | 「**什么推动了该周期**」 | **driver 比较只用这一部分** |
| `turning` + `ending` | 「什么终结了该周期」 | 记为 `terminal_mechanisms`，**不与 driver 混用** |

> 首次运行未拆分时 `CYCLE_REVERSAL` 命中 26 条（25 条来自 turning/ending）→ 拆分后 **9 条**。
> **若不拆分，几乎每个 cycle 都会「共享 CYCLE_REVERSAL」，造成系统性假阳性。**

---

## 6. 逐 Cycle 审计（§九）

| cycle_id | macro_theme | raw | driving | canonical drivers（driving） | terminal mechanisms | D/V/A/U/NA | driving 完整度 |
|---|---|---:|---:|---|---|---:|---:|
| `C-2019-AD` | 汽车 | 6 | 3 | `POLICY_DRIVEN` | `CYCLE_REVERSAL` | 2/1/0/1/2 | 1.00 |
| `C-2020-NEV` | 汽车 | 9 | 4 | `INDUSTRY_UPGRADE` `VALUATION_RESET` | `CYCLE_REVERSAL` | 4/1/0/1/3 | 1.00 |
| `C-2021-NEV` | 汽车 | 9 | 5 | `SUPPLY_CONTRACTION` `VALUATION_RESET` | `CYCLE_REVERSAL` | 3/3/0/0/3 | 1.00 |
| `C-2022-POLICY` | 汽车 | 12 | 6 | `POLICY_DRIVEN` `VALUATION_RESET` | `CYCLE_REVERSAL` | 5/3/0/0/4 | 1.00 |
| `C-2023-AD` | 汽车 | 10 | 3 | `POLICY_DRIVEN` `TECH_BREAKTHROUGH` | `CYCLE_REVERSAL` | 3/0/0/2/5 | 1.00 |
| `C-2024-V2X` | 汽车 | 8 | 2 | `POLICY_DRIVEN` | `CYCLE_REVERSAL` | 1/4/0/1/2 | 1.00 |
| `C-2024-ROBOTAXI` | 汽车 | 10 | 3 | `EVENT_CATALYST` | `CYCLE_REVERSAL` | 2/1/0/1/6 | 1.00 |
| `C-2025-ROBOTAXI` | 汽车 | 8 | 2 | `DEMAND_SURGE` `INDUSTRY_UPGRADE` | `CYCLE_REVERSAL` | 2/0/0/2/4 | 1.00 |
| `C-2019-COMM-5G` | 信息通信 | 13 | 6 | `EVENT_CATALYST` `POLICY_DRIVEN` | `CYCLE_REVERSAL` | 4/2/1/3/3 | 0.83 |
| `C-2023-COMM-OPTICAL` | 信息通信 | 10 | 5 | `DEMAND_SURGE` `TECH_BREAKTHROUGH` | `CYCLE_REVERSAL` | 2/3/0/2/3 | 0.80 |
| `C-2019-PHARMA-INNOV` | 医药健康 | 10 | 3 | `DEMAND_SURGE` `EVENT_CATALYST` | `CYCLE_REVERSAL` | 2/7/0/0/1 | 1.00 |
| `C-2020-POWER-NE` | 电力设备 | 12 | 3 | `POLICY_DRIVEN` | `CYCLE_REVERSAL` | 2/6/0/2/2 | 1.00 |
| `C-2022-POWER-GRID` | 电力设备 | 12 | 3 | `EVENT_CATALYST` `POLICY_DRIVEN` | `CYCLE_REVERSAL` | 1/6/0/4/1 | 1.00 |
| `RC-2023-HUAWEI` | 汽车 | 6 | 2 | `EVENT_CATALYST` `TECH_BREAKTHROUGH` | — | 1/2/0/2/1 | 1.00 |
| `RC-2024-SECONDARY` | 汽车 | 4 | 1 | **（无）** | — | 0/1/0/0/3 | 1.00 |
| `RC-2020-PANDEMIC` | 医药健康 | 8 | 3 | `DEMAND_SURGE` `VALUATION_RESET` | `CYCLE_REVERSAL` | 1/3/0/1/3 | 1.00 |
| `RC-2021-TCM` | 医药健康 | 7 | 3 | `POLICY_DRIVEN` `VALUATION_RESET` | `CYCLE_REVERSAL` | 1/3/0/0/3 | 1.00 |

**driving 相位完整度全部 = 1.00**（除 `C-2019-COMM-5G` 0.83、`C-2023-COMM-OPTICAL` 0.80 —— 各有 1 条 AMBIGUOUS）。
**唯一无 canonical driver**：`RC-2024-SECONDARY`（弱候选，文本本身即 `weak`/`unknown`）。

---

## 7. Driver Evidence Ledger（§十）

`historical_driver_evidence_ledger_v0_1.json` —— **154 条**，每条含：
`cycle_id` · `macro_theme` · `bucket` · `seq` · `raw_driver` · `canonical_driver` · `mapping_status` ·
`matched_rules` · `references` · `event_refs`(event_id/date/event_type) · `source_type` · `reason`。

**复用既有 convention**：引用沿用仓库的 `EV-`/`E-`/`S-` 编号体系，未创造平行体系。

---

## 8. 隔离实验：Driver 维度 Before / After（§十二 / §十三）

> **只改 Driver 维度**；`lifecycle` / `evidence_sequence` / `event_structure` / `temporal` / `market`
> **逐字沿用 v0.2 同一规则**。

| Metric | Before（v0.2 · 类别轴） | After（v0.3 · 机制轴） |
|---|---:|---:|
| `MATCH` | 3 | **1** |
| `PARTIAL` | **71** | **50** |
| `MISMATCH` | 6 | **29** |
| `UNKNOWN` | 0 | **5** |
| `NOT_AVAILABLE` | 5 | 0 |
| **合计** | 85 | 85 |

### ★ 归因（不得只展示 MATCH 增长 —— 本轮 MATCH 实际**下降**）

- **哪些是真正的语义对齐**：`50/85` 的 PARTIAL 是**机制级**的真实交集
  （如 `POLICY_DRIVEN`、`DEMAND_SURGE`、`TECH_BREAKTHROUGH`），**不是**类别巧合。
- **哪些是 v0.2 的虚高**：旧口径下 `MISMATCH 仅 6`，因为只要两侧都有 `POLICY` 即记 PARTIAL；
  机制轴下 `MISMATCH 升至 29` —— **这 23 条差额是旧口径的虚高被剔除**。
- **哪些仍无法判断**：`UNKNOWN 5`（历史 driving 文本无规则命中）+ `22 条 UNKNOWN 原始文本`
  （主要是不含机制词的合作/事件描述，如「宁德时代与本田战略合作」）。
- **`NOT_AVAILABLE 49 → 0` 的变化说明**：历史侧 49 条是价格结果描述（不是 driver）；
  而 candidate 侧 `narrative_types` **100% 非空** → 组合层面不再出现 NOT_AVAILABLE。
  **这是口径澄清，不是「补齐了数据」。**

**Tier 变化**：`TIER_1` **21 → 4** · `TIER_2` 34 → 36 · `TIER_3` 1 → 1 · `TIER_4` 29 → 44。

---

## 9. 反例审计（§十四）

### 9.1 False positive（看起来相似但证据不足）—— 已纠正 3 类

| # | 原始误判 | 纠正 |
|---|---|---|
| 1 | `CYCLE_REVERSAL` 命中 26 条（含 25 条 turning/ending）→ 几乎每 cycle 都「共享」 | **相位拆分** → driving 仅 9 条 |
| 2 | 价格结果文本（涨停/连板/涨 233%/见顶/断板）本可被 `CYCLE_REVERSAL` 或 `VALUATION_RESET` 吸收 | **新增 `PRICE_ACTION` 规则** → 49 条标 `NOT_AVAILABLE`（§十五） |
| 3 | 旧口径「两侧都有 POLICY ⇒ PARTIAL」 | **机制轴** → `MISMATCH 6 → 29`，虚高被剔除 |

### 9.2 False negative（历史文本实际表达 driver 但未被识别）

- `UNKNOWN 22` 条中，部分含机制线索但无显式关键词，例：
  「宁德时代与本田战略合作 + 为特斯拉供货（EV-2020-03）」—— 实质接近 `EVENT_CATALYST` / `DEMAND_SURGE`，
  但文本未出现规则词 → **保持 `UNKNOWN`，不补规则强行匹配**。
- 「6月国五/六切换促销式回暖后市场寻找新方向」—— 含「促销/回暖」但属需求侧边际，
  **未**强行归入 `DEMAND_SURGE`。
- **结论**：存在少量 false negative，但**不通过放宽规则消除**（那会制造 false positive）。

### 9.3 Ambiguous（一个 raw driver 对应多个 canonical）

- **仅 1 条**（`C-2019-COMM-5G` 的 ending 桶）。处理方式：**保留 `AMBIGUOUS`、不硬拆、
  不产生多个独立 driver**，并在比较时**不参与 driver 集合**。

---

## 10. 禁止价格结果反推 Driver（§十五）

**已在代码与 artifact 中显式实现**：
- `PRICE_ACTION` 关键词表（涨停/跌停/连板/天地板/断板/走强/活跃/爆发/大涨/回调/见顶/见底/回撤/新高/低点/高点/板块/指数/市值/涨幅/倍/板）
- 判据：`命中 0 条规则 且 含价格词` **或** `唯一命中 CYCLE_REVERSAL 且 含价格词 且 无引用` → `NOT_AVAILABLE`
- 结果：**49 条**被判为「价格结果描述，非 driver」。

**未使用**：价格序列、涨跌幅、市值变化、行情窗口 → 任何 driver 判定。

---

## 11. SENTIMENT 处理（§十六）

| 项 | 结论 |
|---|---|
| 历史侧 SENTIMENT 结构化来源 | **不存在** |
| 是否新增 | **否** |
| 是否从涨跌推导 | **否** |
| 是否从 media event 数量推导 | **否** |
| 状态 | **`NOT_AVAILABLE`** |

> **缺失 sentiment ≠ 没有 sentiment** —— 而是**当前资料不足以可靠编码**。
> 本轮**未**为改善 MATCH 数字而补齐 SENTIMENT。

---

## 12. 五个 Current Candidates（§十七）

### `CC-2026-BCI-MEDTECH`（医药健康）
- canonical drivers：`POLICY_DRIVEN` `TECH_BREAKTHROUGH`
- driver 状态：PARTIAL 9 · MISMATCH 6 · **MATCH 1** · UNKNOWN 1
- **★ 同族 `C-2019-PHARMA-INNOV` → `MISMATCH`（交集为空）** —— 旧口径记 PARTIAL。
  候选是「政策+技术突破」，PHARMA 是「需求+事件催化」→ **同族但机制不同**。
- **真正的结构对应是跨族的 `C-2023-AD`**（`POLICY_DRIVEN + TECH_BREAKTHROUGH`）→ **`TIER_1`**，
  且为**唯一 `STRICT_B`**。
- 未解缺口：同族机制不对应；`event_date` 缺 0 条但 `phase_window.end` 缺失。

### `CC-2026-COMPUTE-POWER`（电力设备）
- canonical drivers：`DEMAND_SURGE` `INDUSTRY_UPGRADE` `POLICY_DRIVEN`
- driver 状态：**PARTIAL 13** · MISMATCH 3 · UNKNOWN 1（**5 个候选中 driver 覆盖最好**）
- 共享机制：`POLICY_DRIVEN 8` · `DEMAND_SURGE 4` · `INDUSTRY_UPGRADE 2`
- 同族 `C-2022-POWER-GRID` / `C-2020-POWER-NE` 均 `PARTIAL`（共享 `POLICY_DRIVEN`）→ `TIER_2`
- **确认存在 evidence-backed 共同 driver**：infrastructure / capex 语义由 `POLICY_DRIVEN` +
  `DEMAND_SURGE` 承载（政策试点 + 电网投资上行）。
- 未解缺口：`phase_window.end` 缺失；市场代理为**相关段**（电网设备）非主题本身。

### `CC-2026-EMBODIED-AI`（高端装备）
- canonical drivers：`INDUSTRY_UPGRADE` `POLICY_DRIVEN` `TECH_BREAKTHROUGH`
- driver 状态：PARTIAL 12 · MISMATCH 4 · UNKNOWN 1
- **★ 跨族结构对应更清晰**：`C-2023-AD`（`POLICY_DRIVEN + TECH_BREAKTHROUGH`）→ **`TIER_1`**；
  `C-2025-ROBOTAXI`（`INDUSTRY_UPGRADE`）→ `TIER_2`
- **反例**：`C-2024-ROBOTAXI`（看似最相关）→ `MISMATCH`（交集为空，其 canonical 仅 `EVENT_CATALYST`）
- **未因缺 `TH-HIGH-END` 而无法比较** —— 跨族类比已给出 `TIER_1`。

### `CC-2026-OPTICAL-LINK`（信息通信）
- canonical drivers：`DEMAND_SURGE` `INDUSTRY_UPGRADE` `TECH_BREAKTHROUGH`
- driver 状态：MISMATCH 9 · PARTIAL 7 · UNKNOWN 1（**MISMATCH 最多**）
- **★ 同族对比**：
  - `C-2023-COMM-OPTICAL` → `PARTIAL`（共享 `DEMAND_SURGE + TECH_BREAKTHROUGH`）→ **`TIER_1`** ✅
  - `C-2019-COMM-5G` → **`MISMATCH`**（其 canonical 仅 `EVENT_CATALYST + POLICY_DRIVEN`）—— 旧口径记 PARTIAL
  - → **TH-COMM 的两个 cycle 中，只有一个真正结构对应**；另一个只是同族。
- 跨族：`C-2025-ROBOTAXI`（`DEMAND_SURGE + INDUSTRY_UPGRADE`，且 `evidence_sequence = MATCH`）→ `TIER_1`
- 未解缺口：9 条 MISMATCH（历史 cycle 多由 `POLICY_DRIVEN`/`VALUATION_RESET` 驱动）。

### `CC-2026-OFFSHORE-WIND`（电力设备）
- canonical drivers：`POLICY_DRIVEN` `SUPPLY_CONTRACTION`
- driver 状态：PARTIAL 9 · MISMATCH 7 · UNKNOWN 1
- 同族 `C-2022-POWER-GRID` / `C-2020-POWER-NE` 均 `PARTIAL`（共享 `POLICY_DRIVEN`）→ `TIER_2`
- **`SUPPLY_CONTRACTION` 在历史 driving 相位仅 1 条命中**（`C-2021-NEV`）→ 该维度证据稀薄
- **价格修复（price recovery）在历史 driving 文本中无独立证据支撑** → **不编造**
- 未解缺口：市场代理 `GOLDWIND` 覆盖止 2022；`SUPPLY_CONTRACTION` 证据不足。

---

## 13. Driver 是否已可比较（§二十一）

> **判定：`PARTIAL` —— 情况 B。**

- **已达到可比较程度**：8 个 canonical driver 在历史侧**全部有命中**；
  driving 相位完整度 **17/17 对象 ≥ 0.80**；`50/85` 组合存在**真实机制交集**。
- **仍不足以支撑「可靠比较」**：
  - 机制级 `MATCH`（集合相等）仅 **1/85** —— 因两侧 driver 数量不等（candidate 2–3 个 vs 历史 1–2 个）；
  - `MISMATCH 29/85` —— 历史 cycle 多由 `VALUATION_RESET`（9）/`CYCLE_REVERSAL`（9）驱动，
    而 candidate 侧这两个值为 **0**；
  - `UNKNOWN 22 条`原始文本 —— 属**证据不足**，非规则缺陷。
- **结论**：**不再需要继续补 driver 数据**（历史 driving 相位已充分编码）；
  但也**未达到可支撑 Product 的确定性**。

---

## 14. Blocker Resolution Matrix（§二十）

| Blocker | v0.2 | v0.3 | Resolution | Remaining impact |
|---|---|---|---|---|
| lifecycle semantic break | RESOLVED | **RESOLVED（未变）** | 可比观测点口径（v0.2 引入） | 历史不含该阶段 → MISMATCH 3/85 |
| candidate event entity | RESOLVED | **RESOLVED（未变）** | 候选事件实体（v0.2 引入） | 3/39 evidence 无日期 |
| candidate market mapping | PARTIALLY_RESOLVED | **PARTIALLY_RESOLVED（未变）** | 段代理（v0.2 引入） | 候选侧 2026 行情不可得 → 单向 |
| **historical driver structure** | **BLOCKER** | ⚠️ **PARTIALLY_RESOLVED** | **Canonical Driver v0.1**（机制轴 + 相位拆分 + 价格结果排除） | 机制级 MATCH 仅 1/85；MISMATCH 29/85；`VALUATION_RESET`/`CYCLE_REVERSAL` 在 candidate 侧为 0 |
| phase_window.end | UNRESOLVED | **UNRESOLVED（未变）** | 保持 null（v0.2 决定） | temporal 单向 |

**★ 未伪造任何 improvement**：`market_structure`（PARTIAL 68 / NA 17）与
`temporal_structure`（PARTIAL 85）与 v0.2 **完全一致**，未因本轮改动而变化。

---

## 15. Feasibility Decision（§二十七-6）

| 项 | 结论 |
|---|---|
| **Overall Status** | **`PARTIALLY_FEASIBLE`** |
| **Research feasibility** | **改善但更保守** —— Driver 从「类别轴」升级为「机制轴」，可比性提升；但机制级一致度被**如实揭示为偏低** |
| **Product readiness** | **仍为 NO** —— `STRICT_A 0/85`、`STRICT_B 1/5`、市场单向、temporal 单向 |
| **Remaining blocker** | **机制级证据不足**（不是 vocabulary mismatch）：`MISMATCH 29/85` + `UNKNOWN 22 条` |
| **Wave 1C necessity** | **NOT REQUIRED** —— 无 BLOCKER 需新增历史 Theme Family 才能解决 |
| **Can Structural Analogy Research v0.1 start** | **可以（Research-only）** —— 但**仅限**四维：`Lifecycle(可比观测点)` + `Driver(机制轴)` + `Evidence Sequence` + `Event Structure` |
| **Minimum viable dimensions** | 上述四维；**不含** market（单向）与 temporal（单向） |

### 三关键数字

| 指标 | v0.1 | v0.2 | **v0.3** |
|---|---:|---:|---:|
| 有结构可用历史类比（`STRICT_B`） | 1/5 | 1/5 | **1/5** |
| 仅有主题/名称级类比 | 4/5 | 4/5 | **4/5** |
| 无任何可用历史类比 | 0/5 | 0/5 | **0/5** |

> 顶层数字未变，但**含义变了**：v0.3 的 `STRICT_B` 建立在**机制轴**上（更严），
> 不再是 v0.2 的类别巧合。

---

## 16. 明确回答（§二十七 汇总）

| 问题 | 回答 |
|---|---|
| Candidate canonical drivers | 5 个在用（`POLICY_DRIVEN` 4 · `TECH_BREAKTHROUGH` 3 · `INDUSTRY_UPGRADE` 3 · `DEMAND_SURGE` 2 · `SUPPLY_CONTRACTION` 1） |
| Historical raw driver count | **154** |
| Historical canonical driver count | **8**（全相位）/ **7**（driving 相位） |
| DIRECT / DERIVED / AMBIGUOUS / UNKNOWN / NOT_AVAILABLE | **36 / 46 / 1 / 22 / 49** |
| Driver MATCH before → after | **3 → 1** |
| Driver PARTIAL before → after | **71 → 50** |
| Driver MISMATCH（v0.3） | **29** |
| Driver NOT_AVAILABLE（v0.3） | **0**（v0.2 为 5） |
| schema changed | **NO** |
| export contract changed | **NO** |
| 历史原始 driver 文本 changed | **NO** |
| candidate driver changed | **NO** |
| Time Observation v0.2–v0.5 changed | **NO**（逐字节保留） |
| `src/**` / Product changed | **NO** |
| 是否实现 Structural Analogy | **NO** |
| 是否进入 Wave 1C | **NO**（`NOT REQUIRED`） |
| breaking change | **NO** |

---

## 17. Limitations

- 关键词规则为**显式但粗糙**的文本规则；存在少量 false negative（已审计，**不通过放宽规则消除**）。
- `DIRECT` 要求「命中唯一规则 + 有引用」，因此**无引用**的明确表述被降为 `DERIVED`。
- `driving` / `terminal` 相位划分沿用 export 既有桶语义，未重新定义。
- candidate 侧 `narrative_types` 与 `drivers[].category` 是**两条正交轴**；本轮用前者作机制轴，
  后者仅保留作对照。
- 样本量小（85 组合），**任何比例数字都不具统计意义**。
- 未做多重比较校正（本轮不产出 p 值）。

---

## 18. Reproducibility

- 生成器：`research/scripts/canonicalize_historical_drivers_v0_1.py` ·
  `research/scripts/build_structural_analogy_feasibility_v0_3.py`
  （**deterministic**：无随机 / 无时间依赖 / 无网络 / 无 LLM / 规则显式可审计）。
- 均支持 `--check`：产物与重算结果**逐字节一致**（已执行 `run → check → run → check`）。
- 输入：`exports/timeline_export_v1.json` · `research/current/current_candidates.json` ·
  `research/database/cycle_research.db`（只读）。
- **v0.1 / v0.2 产物保留不覆盖**；**未写** DB / schema / export / `src/**`。

---

*报告结束 · Historical Driver Canonicalization v0.1 · Structural Analogy Feasibility v0.3 · 2026-09-19*
