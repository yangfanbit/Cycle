# Phase 7.4B Report — Historical Date Claim Cleanup + Evidence Normalization

> | 项目 | 值 |
> |---|---|
> | 轮次 | `phase-7.4b-date-claim-cleanup` |
> | 完成日期 | 2026-09-18 |
> | 性质 | **数据质量修复**（清理无来源日期断言 + evidence_type 规范化 + Coverage Audit v0.3） |
> | 起始状态 | `HEAD = origin/main = 2c16058`，ahead/behind `0/0`，工作树 clean（**自行核对**） |
> | 未进入 | Wave 1C · Structural Analogy · Time Observation 新研究轮次 · 新 UI |

**基线实测**：campaigns 13 · evidences 83 · events 49 · themes 19 ·
Macro roots `TH-AUTO / TH-COMM / TH-PHARMA / TH-POWER` ·
TOP-01 `N=7 / center 06-11 / window 05-27~06-26 / recurrence 0.7143`。

---

## 1. E-2023-04

### before
```
date            : 2023-07-13
evidence_type   : 行情数据
source          : S-2023-05（界面新闻/证券时报，media_tier2，tier=2，2023-07-13）
description     : 龙头区间涨幅：浙江世宝近一月翻倍(8→18)、德赛西威+80%、万安+70%、
                  赛力斯6/8见底后一月近翻倍。启动早于6/1(6/12预热、赛力斯6/8见底)。
关联            : C-2023-AD（role=supporting）
```

### after
```
date            : 2023-07-13            （未变）
evidence_type   : 行情数据               （未变）
source          : S-2023-05             （未变）
description     : 龙头区间涨幅（源文明确记载）：浙江世宝近一月不到8元→近18元(超100%)、
                  万安科技8.50→14.31(近70%)、德赛西威5月上旬不足百元→7/11最高179.50(约80%)、
                  赛力斯自6/8触及24.75低点后一月近翻倍。
                  〔Phase 7.4B 更正：原描述含「启动早于6/1(6/12预热)」——经取回源文
                  S-2023-05 全文核验，源文未出现「6月12日」，亦无「启动早于6/1」表述
                  → 该日期断言 UNSUPPORTED，已移除；源文可支持的最早起点为德赛西威
                  「5月上旬」。锚点日期不受本更正影响。〕
```

### source
- **保留** `S-2023-05`（未改）。
- **未补充新来源** —— 因为**没有找到**任何 Tier ≤2 来源记载「2023-06-12」为该主题起点
  （7.4A 已取回源文全文；本轮复扫全库无同日 Tier ≤2 证据）。

### verification
- 处理方式 = 用户 §三 的「**找不到 → 不猜日期、标记 UNSUPPORTED**」分支。
- **未扩 schema** —— 复用现有 `description` 字段（`evidences` 表无 `note`/`provenance` 列，实测确认）。
- `confidence` **保持 `high`** —— 因为**保留下来的事实**（四条标的区间涨幅）**全部由源文明文支持**；
  被移除的只是日期断言。
- **证据本身有效 → 未删除**（§二）。

---

## 2. E-2024-03

### before
```
date            : 2024-06-21
evidence_type   : 行情数据
source          : S-2024-02（财联社，media_tier2，tier=2，2024-06-18）
description     : 车联网(车路协同)概念指数6/11-6/21涨超9%，229家概念股近八成上涨；
                  6/21索菱5连板后巨量分歧。
关联            : C-2024-V2X（role=supporting）
```

### after
```
date            : 2024-06-21            （未变）
evidence_type   : 行情数据               （未变）
source          : S-2024-02             （未变）
description     : 6/18 车路云概念全线爆发：华铭智能、中海达、鸿泉物联、索菱股份、
                  金溢科技、长江通信等10余股涨停，华铭/金溢/索菱2连板——源文记为「行情高峰」。
                  〔Phase 7.4B 更正：原描述含「车联网(车路协同)概念指数6/11-6/21涨超9%」
                  「229家概念股近八成上涨」，经取回源文 S-2024-02 全文核验，源文均未提及
                  （且源文发布于 2024-06-18，不可能记载 6/21 数据）→ 该日期区间与统计断言
                  UNSUPPORTED，已移除。锚点日期不受本更正影响。〕
```

### source
- **保留** `S-2024-02`（未改）。
- **未补充新来源** —— 无 Tier ≤2 来源记载「2024-06-11」。

### verification
- **说明**：本条比 E-2023-04 更严重 —— 原描述的**主要统计断言**（概念指数区间涨幅、229 家概念股）
  在源文中**均不存在**，且源文日期（06-18）**早于**证据所声称的区间终点（06-21），
  存在**时间上不可能**的问题。
- 处理方式 = 改为**源文真正支持的内容**（6/18 全线爆发 + 索菱/金溢/华铭 2 连板），
  并显式标注被移除的断言。
- `confidence` **保持 `medium`**（原本即为 medium）。
- **证据本身保留**（其「6/18 为行情高峰」这一事实有 Tier 2 来源支撑，仍支撑 C-2024-V2X）。

---

## 3. Anchor Impact

### 3.1 ★ anchor 依赖链复核（§四 要求）

| Campaign | anchor | `campaigns.start_date` | `campaign_date_observations.evidence_id` | 结论 |
|---|---|---|---|---|
| `C-2023-AD` | 2023-06-12 | `2023-06-12` ✅ 未变 | **`None`** | **anchor 不依赖任何 evidence** |
| `C-2024-V2X` | 2024-06-11 | `2024-06-11` ✅ 未变 | **`None`** | **anchor 不依赖任何 evidence** |

- 两个锚点均来自 `campaigns.start_date`，其 `campaign_date_observations` 行的 `evidence_id` 为 **NULL**
  （notes 明确写「candidate 快照自 campaigns；未经行情核验」）。
- **→ evidence 的日期断言被标记 UNSUPPORTED，不会也不应改变 anchor。**
- 传播链（`campaigns.start_date_basis` / `annual_reviews.summary`）**已一并标注 UNSUPPORTED**，
  但**只改文本、不改日期**；且这两个字段**不在 export 中**（实测 `grep` 命中 0）。

### 3.2 TOP-01 before / after（§五 硬约束）

| 项 | before | after | 结果 |
|---|---|---|---|
| `N` | **7** | **7** | ✅ |
| `center` | **06-11** | **06-11** | ✅ |
| `window` | **05-27 ~ 06-26** | **05-27 ~ 06-26** | ✅ |
| `recurrence` | **0.7143**（命中 2020·2021·2023·2024·2025） | **0.7143**（同） | ✅ |
| `stability` | `SPLIT` | `SPLIT` | ✅ |
| `promotion_status` | `TIMELINE` | `TIMELINE` | ✅ |
| `observations` 7 条 | — | — | ✅ **逐条一致**（year/date/campaign_id） |
| `anchor_verification` | 2/5/0 | 2/5/0 | ✅ 未变 |

**→ TOP-01 完全未变。未为保留 TOP-01 修改任何阈值（§五 禁止项）。**

### 3.3 词边界复扫（§一 传播链核查）

对 `2023-06-12` / `2024-06-11` 复扫 `evidences.description` · `campaigns.start_date_basis` ·
`annual_reviews.summary`（lookaround 词边界，非朴素子串）：

- `2023-06-12`：4 处命中，**全部位于本轮新增的「已标注 UNSUPPORTED」说明文本内** ✅
- `2024-06-11`：4 处命中 —— 2 处为 UNSUPPORTED 说明 ✅；
  另 2 处为 **2020 年**的 `6/11`（`E-2020-01`「6/11 A股特斯拉板块大涨近4%」、
  `C-2020-NEV`「6/11 特斯拉板块涨停潮(据 S-2020-01)」）—— **不同年份、有 Tier 2 来源支撑**，非本次问题 ✅

**→ 无残留的无来源日期断言。**

---

## 4. Evidence Type Normalization

### 4.1 两个词表的关系（§七：先建立 mapping，不改 DB）

实测交叉表证明 **`source_type` 与 `evidence_type` 彼此独立**，不能互相反推：

| source_type | n | 实测承载的 evidence_type |
|---|---:|---|
| `media_tier2` | 47 | 行情数据 26 · media 8 · 行业数据 6 · 行业月度产销数据 4 · 政策文件 1（**5 种**） |
| `regulator` | 22 | 政策文件 11 · 行业数据 7 · official_document 2 · 行业月度产销数据 1（**4 种**） |
| `media_tier3` | 7 | 行业数据 3 · 行情数据 2 · 政策文件 1 |
| `website` | 3 | 行情数据 4 · market_data 1 |
| **`company_announcement`** | **3** | **行业数据 3** ← 本轮规范化对象 |
| `media_tier4` | 2 | 行情数据 2 |
| `exchange` | 1 | official_document 1 |

### 4.2 canonical mapping（本轮建立）

**（a）`evidence_type → canonical`（唯一归一化入口，已补键）**

```python
EVIDENCE_TYPE_MAP = {
    "行情数据": "market",        "market_data": "market",
    "行业数据": "industry",      "行业月度产销数据": "industry",
    "政策文件": "policy",        "official_document": "policy",
    "media": "information",
    # Phase 7.4B 补键（CANONICAL_EVIDENCE_TYPES 已声明但本表缺键）
    "company": "company",  "company_announcement": "company",  "公司公告": "company",
    "capital": "capital",  "capital_flow": "capital",          "资金流向": "capital",
}
```
词表条目 **7 → 13**；`UNCLASSIFIED` 仍为 **0**。

**（b）`source_type → 默认 canonical evidence_type`（仅对语义唯一对应的来源类型）**

```python
SOURCE_TYPE_DEFAULT_EVIDENCE_TYPE = {
    "regulator": "policy",              # 监管 / 官方发布
    "exchange": "policy",               # 交易所规则文件
    "company_announcement": "company",  # 公司自身披露（一手）
    "website": "market",                # 行情数据站
    # media_tier1/2/3/4：不固定 —— 必须按**内容**判定，不得按来源类型推断
}
```
⚠️ **本表不参与机械归一化**（归一化只走 `EVIDENCE_TYPE_MAP`），用途是新增证据时的默认取值参考
+ 人工复核清单。已在代码注释中显式写明「这不是来源类型决定证据类型」。

### 4.3 affected records

**§八 核查结果**：用户列出的 `E-COMM-12/13/14` 中，**E-COMM-12 实为媒体来源**
（`S-COMM-11`，36氪/智源社区，`media_tier2`）→ `evidence_type=media` **正确，未改**。
真正的 `company_announcement` 来源共 3 条，对应证据为 **`E-COMM-13 / E-COMM-14 / E-COMM-15`**：

| evidence_id | source_id | source_type | evidence_type before → after |
|---|---|---|---|
| `E-COMM-13` | `S-COMM-12`（NVIDIA 投资者关系官方新闻稿） | `company_announcement` | `行业数据` → **`company`** |
| `E-COMM-14` | `S-COMM-13`（中际旭创 2023 半年报） | `company_announcement` | `行业数据` → **`company`** |
| `E-COMM-15` | `S-COMM-14`（中际旭创 2023 年报） | `company_announcement` | `行业数据` → **`company`** |

- **`source_id` / `source_type` 全部保持不变**（§八 要求）。
- 规范化方式：**按 `source_type='company_announcement'` 机械选取目标集合**（非硬编码 ID），
  可复核、可重复。

### 4.4 company count / capital count

| canonical | before | after |
|---|---:|---:|
| `policy` | 13 | 16 |
| `industry` | 18 | **21** |
| **`company`** | **0** | **3** |
| `market` | 33 | 35 |
| **`capital`** | **0** | **0** |
| `information` | 3 | 8 |
| `UNCLASSIFIED` | 0 | **0** |

> `industry` 的 before(18) 是 **v0.2 快照值**；Wave 1B 曾把 6 条行业证据加入（→24），
> 本轮 7.4B 再把 3 条移入 `company`（→21）。**净变化需按轮次拆开看。**

### 4.5 capital 不虚构（§九）

- 实测全库**无任何**可归类为 `capital` 的证据
  （对 `evidence_type LIKE '%资金%'/'%capital%'` 及描述中的「北向/主力净流入/融资余额」扫描，命中 **0**）。
- **→ `capital` 保持 0。未为了让 6 类完整而制造任何 capital 证据。**

---

## 5. Coverage Audit v0.3

### 5.1 新轮次（不覆盖 v0.1 / v0.2）

- `ROUND_PROFILES` 新增 **`0.3`**：产物 `historical_coverage_matrix_v0_3.{json,csv}` ·
  `snapshot_date=2026-09-18` · `artifact_version=0.3`。
- **v0.1 / v0.2 产物逐字节未改**（`git status` 只显示 v0_3 为新增）。
- `--round 0.3` 生成成功；`--round 0.3 --check` **PASS**（逐字节可复现）。

### 5.2 delta vs v0.2

> ⚠️ v0.2 是 **Wave 1A 之后**的快照，因此 v0.2→v0.3 的 delta 同时包含
> **Wave 1B 的数据扩容** 与 **Phase 7.4B 的质量修复**。下表按来源拆分。

| 指标 | v0.2 | v0.3 | 主要来源 |
|---|---:|---:|---|
| Campaigns | 11 | **13** | Wave 1B |
| Themes（全部） | 16 | **19** | Wave 1B |
| Evidences | 67 | **83** | Wave 1B |
| Events（DB） | 39 | **49** | Wave 1B |
| Sources | 70 | **85** | Wave 1B |
| market_series / market_daily | 48 / 48,772 | **56 / 79,466** | Wave 1B |
| **`theme_family_count`** | **3** | **4** | Wave 1B（TH-COMM） |
| `declared_but_no_history` | `[信息通信, 高端装备]` | **`[高端装备]`** | Wave 1B |
| **`company`（canonical）** | **0** | **3** | **Phase 7.4B** |
| `industry`（canonical） | 18 | 21 | Wave 1B +6 / **7.4B −3** |
| `capital`（canonical） | 0 | **0** | 无变化（无证据） |
| `normalization_map` 条目 | 7 | **13** | **Phase 7.4B** |
| `UNCLASSIFIED` | 0 | **0** | 无回归 ✅ |

### 5.3 同时修正的两处叙述一致性

v0.2 中已存在的 `_patch_derived_notes()` 在 v0.3 下继续生效；
`declared_but_no_history` 现为 `['高端装备']`，v0.3 的 `coverage_ceiling.statement`
与 `Structural Analogy` blocker 均自动反映该状态（无需人工改文本）。

---

## 6. Product Impact

| 检查项 | 结果 |
|---|---|
| `exports/timeline_export_v1.json` | **未修改**（实测 export 中不含 evidence id / `start_date_basis` / annual summary） |
| `src/**`（含 Product Artifact `timeObservationPatterns.ts`） | **未修改** |
| `research/current/` | **未修改** |
| Time Observation Artifact（`time_observation_patterns_v0_1.json`） | **未修改**（`--check` PASS） |
| `npm run build` bundle | **382.27 kB（未变）** |
| `npm test` | **395 / 395 PASS**（未修改任何测试） |

**→ 本轮 DB 变更对 Product 是「零可见影响」** —— 因为被修改的字段全部处于
export 边界之内（research-only）。

---

## 7. Tests

| 门禁 | 结果 |
|---|---|
| `npm test` | ✅ **395 passed / 395（10 files）** |
| `npx tsc -b` | ✅ **exit 0** |
| `npm run build` | ✅ **PASS**（382.27 kB JS / 38.86 kB CSS） |

---

## 8. Validators

| 校验器 | 结果 |
|---|---|
| `validate_db.py` | ✅ PASS |
| `validate_timeline_export.py` | ✅ PASS |
| `validate_batch_research.py` | ✅ PASS |
| `validate_promotion_manifest.py` | ✅ PASS |
| `check_doc_schema_consistency.py` | ✅ PASS |
| `validate_current_research.py` | ✅ PASS |
| `validate_monorepo_integrity.py` | ✅ PASS |

---

## 9. Determinism

| 检查 | 结果 |
|---|---|
| `build_time_observation_patterns.py --check` | ✅ **PASS**（逐字节一致） |
| `audit_historical_coverage.py --round 0.3 --check` | ✅ **PASS**（逐字节一致） |
| v0.1 / v0.2 产物 | ✅ **逐字节未改**（快照保留） |
| TOP-01 统计量 before/after | ✅ **完全一致**（见 §3.2） |
| Macro roots before/after | ✅ `TH-AUTO / TH-COMM / TH-PHARMA / TH-POWER` 未变 |
| `UNCLASSIFIED` | ✅ 0 → 0 |
| 换行符 | ✅ 新增 CSV 为 LF；脚本为 LF |

---

## 10. Git

### 10.1 变更清单（4 项）

| 文件 | 变更 |
|---|---|
| `research/database/cycle_research.db` | 5 处文本更正 + 3 处 `evidence_type` 规范化 |
| `research/scripts/audit_historical_coverage.py` | +34 行：`EVIDENCE_TYPE_MAP` 补键 · 新增 `SOURCE_TYPE_DEFAULT_EVIDENCE_TYPE` · `ROUND_PROFILES["0.3"]` |
| `research/research/reports/historical_coverage_matrix_v0_3.json` | **新增**（Coverage Audit v0.3） |
| `research/research/reports/historical_coverage_matrix_v0_3.csv` | **新增** |

**未修改**：`schema/schema.sql` · `contracts/` · `exports/` · `src/**` · `research/current/` ·
任何测试文件 · `time_observation_*` 全部产物 · v0.1/v0.2 审计产物 · Promotion Gate 规则。

### 10.2 提交纪律

未使用 `git add -A`；逐文件 `git add`；提交前核对
`git diff --stat` / `git diff` / `git diff --cached --stat` / `git diff --cached --name-status`。
**未**执行 `force push` / `--amend` / `rebase` / `reset --hard`。

**Commit message**：`fix(research): clean unsupported historical date claims`
（本轮**同时**包含 date claim 清理与 normalization，该 message 已覆盖主变更；
正文中显式列出 normalization 与 Coverage Audit v0.3。）

### 10.3 提交后状态

`HEAD == origin/main` · ahead/behind `0/0` · 工作树 clean（实际哈希见本轮回复与 `git log`）。

---

## 11. Remaining Data Gaps

| # | 缺口 | 严重度 | 说明 |
|---|---|---|---|
| 1 | **DB 层日期核验仍为 0/24** | HIGH | `campaign_date_observations.verified_date` 全为 NULL；本轮**未**改该字段（本轮处理的是「日期断言的来源支撑」，不是「日期已核验」） |
| 2 | **两个锚点仍无来源支撑** | HIGH | `2023-06-12` / `2024-06-11` 的**锚点日期本身**保留（来自 `campaigns.start_date`），但其**事件描述已标注 UNSUPPORTED** → 需要独立的 Tier ≤2 来源才能真正核验 |
| 3 | `capital` evidence_type = 0 | MEDIUM | **真实为 0**（全库无可归类证据），非词表问题；词表键已补 |
| 4 | `evidence_type` 中英文混用未统一 | MEDIUM | 现有 8 个值中 4 中 4 英（`company` 为新增英文值，与 canonical 一致） |
| 5 | **V2X 概念指数无行情数据** | MEDIUM | `V2X` 为 `EMPTY_PLACEHOLDER`（0 行）→ C-2024-V2X 的锚点无法以行情佐证 |
| 6 | 交易日历仍 371 行（2022-03 ~ 2024-09） | MEDIUM | 未补全 |
| 7 | `discover_time_observation_patterns.py --check` | LOW | 仍 FAIL（旧快照）；按 §十二 **未重跑**，需新 `ROUND_PROFILE` v0.5 |
| 8 | `F7`：`华为汽车` 不在 `themes` 表 | LOW | 既有 DEFER |

### 11.1 关于「无来源日期断言」的系统性观察

本轮只处理了**已被 7.4A 定位的 2 条**。但从 E-2024-03 的情况看
（主要统计断言在源文中**均不存在**，且存在**时间上不可能**的问题），
**同类问题可能不止 2 条**。建议后续轮次做一次**全库 evidence 描述 vs 源文的一致性抽检**，
但**不在本轮范围**（§一 明确只处理这两条）。

---

## 12. Recommended Next Step

### 12.1 本轮结论

> **P0（无来源日期断言）已清理** —— 2 条 evidence + 3 处传播文本，全部标注 UNSUPPORTED；
> **P1（evidence_type 规范化）已完成** —— `company` **0 → 3**，`capital` 保持 0（未虚构），
> `UNCLASSIFIED` 仍为 0；**Coverage Audit v0.3 已建立**（v0.1/v0.2 保留）。
> **TOP-01 与 anchor 完全未变；Product 零可见影响。**

**明确回答**：

| 问题 | 回答 |
|---|---|
| **schema changed** | **NO**（`schema/schema.sql` 零改动；仅补归一化词表） |
| **export changed** | **NO**（`exports/timeline_export_v1.json` 零改动） |
| **historical cycle changed** | **NO**（13 Campaign / 13 Theme Cycle 的日期、主题、lifecycle 全部零改动；仅 2 条 `start_date_basis` 文本标注 + 1 条 annual summary 文本标注） |
| **current research changed** | **NO**（`research/current/` 零改动） |
| **breaking change** | **NO**（`UNCLASSIFIED` 0→0；bundle 体积不变；395/395 测试通过；无契约变更） |

### 12.2 建议的下一阶段（**默认路径**）

> **Time Observation Discovery 新轮次**（前提：Coverage Audit v0.3 正常 → **已确认正常**）。

**理由**：
1. 本轮已完成用户设定的三项前置条件：**Date Claim Cleanup + Evidence Normalization + Coverage Audit v0.3**。
2. v0.3 已把 `theme_family_count` 确认为 **4**、`company` 纳入统计、`declared_but_no_history` 收窄至 `[高端装备]`
   —— 覆盖度与词表口径均已稳定，可安全作为 Discovery 的新输入基线。
3. **重跑必须新 `ROUND_PROFILE`（v0.5），不得覆盖 v0.2/v0.3/v0.4**；
   同时应登记新轮次的 `ROUND_PROFILES` 口径（canonical CMTR + 派生门）。

**替代方案（若优先补可信度）**：
- 为 `2023-06-12` / `2024-06-11` 寻找独立 Tier ≤2 来源（若能找到 → 两锚点可升 VERIFIED，TOP-01 3/7 或 4/7）；
- 或做 §11.1 建议的全库 evidence-描述 vs 源文一致性抽检。

### 12.3 本轮**未**启动（等待授权）

Wave 1C · Structural Analogy · Time Observation Discovery 重跑 · DB 层日期核验写回
（`campaign_date_observations.verified_date`）· 交易日历补全 · 全库 evidence 一致性抽检。

---

*报告结束 · Phase 7.4B — Historical Date Claim Cleanup + Evidence Normalization · 2026-09-18*
