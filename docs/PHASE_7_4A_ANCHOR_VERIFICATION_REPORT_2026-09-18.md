# Phase 7.4A Report — Anchor Verification + Data Quality 收敛

> | 项目 | 值 |
> |---|---|
> | 轮次 | `phase-7.4a-anchor-verification` |
> | 完成日期 | 2026-09-18 |
> | 范围 | **只处理现有 Time Observation 的可信度**；不进入 Wave 1C，不进入 Structural Analogy 实现 |
> | 起始状态 | `HEAD = origin/main = 707224b`，ahead/behind `0/0`，工作树 clean（**自行核对，未采信历史描述**） |
> | 未修改 | `schema/schema.sql` · `contracts/` · `research/current/` · Product 逻辑 / UI · **Promotion Gate 规则（N 阈值 / concentration / LOO / stability / derived structure gate）** |

---

## 1. Baseline

```
git status --short                        → 无输出（clean）
git log --oneline --decorate -5           → 707224b (HEAD -> main, origin/main) research: add historical information communication cycles
                                            052b79b research: add coverage audit v0.2 (post Wave 1A)
                                            cc4c2d4 research: add historical power equipment cycles
                                            f446cb8 docs(state): rebuild PROJECT_STATE from verified repo state; record recovery
                                            ff8b6eb docs(repo): record Repository Recovery Report 2026-09-17
git rev-list --left-right --count origin/main...HEAD → 0   0
```

**结论：工作树 clean，`HEAD == origin/main`，无异常。**

**基线核验状态（改动前实测）**：TOP-01 `verified 2 / unknown 5 / conflict 0`（共 7）。

| # | 锚点 | Campaign | 状态 | 规则 |
|---|---|---|---|---|
| 1 | 2019-08-15 | C-2019-AD | UNKNOWN | `R5_NO_EVIDENCE`（同日仅 Tier 3） |
| 2 | 2020-06-01 | C-2020-NEV | UNKNOWN | `R5_NO_EVIDENCE`（同日仅 Tier 4） |
| 3 | 2021-06-01 | C-2021-NEV | UNKNOWN | `R5_NO_EVIDENCE`（无同日证据） |
| 4 | 2022-04-27 | C-2022-POLICY | **VERIFIED** | `R1_MARKET_DATA` |
| 5 | 2023-06-12 | C-2023-AD | UNKNOWN | `R4_TEXT_MENTION_ONLY` |
| 6 | 2024-06-11 | C-2024-V2X | UNKNOWN | `R4_TEXT_MENTION_ONLY` |
| 7 | 2025-06-22 | C-2025-ROBOTAXI | **VERIFIED** | `R2B_EVENT_SOURCE` |

**核验范围（按 §二/§三 收敛）**：只核验 TOP-01 的 7 个锚点；
**未**把全库 24 个 `campaign_date_observations` 全部纳入人工核验。

---

## 2. TOP-01 Verification

> **TOP-01 verified = 2 / 7（未变化）**
> **unknown = 5 / 7** · **conflict = 0 / 7**

### 2.1 verified（2）

| 锚点 | 方法 | 来源（可追溯） |
|---|---|---|
| **2022-04-27** | `MARKET_DATA` | `cycle_research.db:campaign_date_observations(OBS-C-2022-POLICY-start)` — 该起始日期本身由行情观测得出 |
| **2025-06-22** | `PUBLIC_SOURCE`（R2B） | `cycle_research.db:events(EV-2025-01)` + `sources(S-2025-02)` — 同日事件（Tier 2）：特斯拉奥斯汀启动 Robotaxi 有偿试运营 |

> ⚠️ R2B 的既有 caveat 仍然成立：事件台账支持「该日期有来源可查的事实」，
> 但**不构成**对「该日期即行情起点」的独立确认。

### 2.2 unknown（5）—— 本轮逐项复核结论

**（a）2023-06-12（C-2023-AD）— 优先候选，本轮已完整核验 → 维持 UNKNOWN**

- R4 候选：`E-2023-04`（源 `S-2023-05`，界面新闻/证券时报，**tier 2**，2023-07-13）
- 该证据**仅在其 `description` 文本**提到「6/12预热」；日期**未作为独立日期证据登记**
- **已取回源文全文核对**：源文提到的日期为 **7/12、6/8、7/11、7/7、6/17、7/6、5月上旬**，
  **全文未出现「6月12日」**（源文明确写的是「赛力斯股价自 6月8日 触及 24.75 元最低点」）
- 同日 linked evidence = **0**、同日 linked event = **0**（无 tier ≤2）
- 行情佐证：代表标的（前复权 raw）在锚点 ±10 交易日内最低点均为 **2023-06-08**
  （浙江世宝 7.47 / 万安科技 8.60 / 众泰汽车 2.37）——**并非 2023-06-12**
- **→ 无同日可追溯证据，且行情亦不支持该日为起点 → 维持 UNKNOWN**

**（b）2024-06-11（C-2024-V2X）— 优先候选，本轮已完整核验 → 维持 UNKNOWN**

- R4 候选：`E-2024-03`（源 `S-2024-02`，财联社，**tier 2**，2024-06-18）
- 该证据**仅在其 `description` 文本**提到「车联网概念指数 6/11-6/21 涨超 9%」
- **已取回源文全文核对**：源文提到的日期为 **6/18、6/17、6/16**，**全文未出现「6月11日」**
- 同日 linked evidence = **0**、同日 linked event = **0**
- 行情佐证**不可得**：该 Campaign 的 4 个代表标的（华铭智能 / 金溢科技 / 索菱股份 / 万集科技）
  在 `market_series` 中**均无行情数据**（`V2X` 概念指数为 `EMPTY_PLACEHOLDER`，0 行）
- **→ 无同日可追溯证据 → 维持 UNKNOWN**

**（c）2019-08-15（C-2019-AD）→ 维持 UNKNOWN**

- 同日 linked evidence 存在 1 条：`E-2019-05`，但来源 `S-2019-05` 为 **tier 3**（转载/二手）→ **未达门槛**
- 同日 linked event = 0
- 行情：万安科技 ±10 日最低为 6.49 @**2019-08-09**（锚点 2019-08-15 当日 6.70，非窗口最低）；
  路畅科技无行情数据
- **→ 按 §五「只有 Tier 3 / Tier 4 → 继续 UNKNOWN」→ 维持 UNKNOWN**

**（d）2020-06-01（C-2020-NEV）→ 维持 UNKNOWN**

- 同日 linked evidence 存在 1 条：`E-2020-03`，来源为 **tier 4**（经验帖线索，**不可作为核验依据**）
- 该证据自身即写明：「线索(Tier4)：…全年视角可能早于 6/1 启动，**窗口漂移需核验**」
- 同日 linked event = 0
- 行情：比亚迪 ±10 日最低 56.03 @2020-05-22；江淮汽车 ±10 日最低 4.94 @2020-05-18
  （锚点当日已 9.97，即行情早在锚点前已启动）→ **锚点不是行情起点**
- **→ 维持 UNKNOWN**

**（e）2021-06-01（C-2021-NEV）→ 维持 UNKNOWN**

- 同日 linked evidence = **0**、同日 linked event = **0**
- 行情：比亚迪 ±10 日最低 158.70 @2021-05-18；小康股份 54.20 @2021-05-24；
  **长安汽车最低 21.22 @2021-06-16（晚于锚点）** → 无一致起点
- **→ 维持 UNKNOWN**

### 2.3 conflict（0）

无锚点存在「仓库内 evidence 明确指向另一个起始日期且互斥」的情形 → **CONFLICT = 0**（与改动前一致）。

### 2.4 ★ 本轮写入的 verification metadata

在两个优先候选上写入 **`status = UNKNOWN` 的 manual override**（**未升级为 VERIFIED**），
目的是**记录已完成的核验过程与结论**，避免后续重复劳动：

| campaign_id | anchor_date | status | rule |
|---|---|---|---|
| `C-2023-AD` | 2023-06-12 | UNKNOWN | `MANUAL_OVERRIDE` |
| `C-2024-V2X` | 2024-06-11 | UNKNOWN | `MANUAL_OVERRIDE` |

- 写入位置：`research/research/reports/time_observation_anchor_verification_v0_1.json` → `overrides`
  （原为空数组，本轮 0 → 2）
- 产物字段：`anchor_verification_policy.manual_overrides: 0 → 2`
- **`source` 为空数组** —— 因为**确实没有**可追溯来源；生成器对 VERIFIED 的空 source 会拒绝写盘，
  本轮 status 为 UNKNOWN，符合策略。

---

## 3. Statistics Before / After

**硬约束回归（§八）**：增加 verification metadata **不得**改变任何统计量。

| 统计量 | Before | After | 结果 |
|---|---|---|---|
| `observation_count`（TOP-01） | 7 | 7 | ✅ 一致 |
| `center_date` | `06-11` | `06-11` | ✅ 一致 |
| `typical_window` | `05-27 ~ 06-26`（31 天） | 同 | ✅ 一致 |
| `recurrence` | 命中 5/7（2020·2021·2023·2024·2025） | 同 | ✅ 一致 |
| `stability` | `SPLIT`（first 06-01 / second 06-11，位移 10.5） | 同 | ✅ 一致 |
| `leave_one_out` | base_hits 5 · max_center_shift 5.0 · 单年主导 = false | 同 | ✅ 一致 |
| `dispersion` | IQR 16 · MAD 10 · span 110 · 04-27 ~ 08-15 | 同 | ✅ 一致 |
| `promotion_status` | `TIMELINE` | `TIMELINE` | ✅ 一致 |
| **TOP-01 的 7 个 observations** | 7 条 | 7 条 | ✅ **逐条一致**（year/date/campaign_id） |
| TOP-02 / TOP-03 / TOP-04 全部统计量 | — | — | ✅ 一致 |
| `verified / unknown / conflict / total` | 2 / 5 / 0 / 7 | 2 / 5 / 0 / 7 | ✅ 一致 |
| `anchor_verification.methods` | `{UNKNOWN:5, MARKET_DATA:1, PUBLIC_SOURCE:1}` | 同 | ✅ 一致 |
| `all_verified` / `label` | `false` / `2 / 7 个锚点已完成仓库内证据核验` | 同 | ✅ 一致 |

**→ 统计量完全保持。** 唯一变化是**元数据**：
`manual_overrides` 0 → 2，两个锚点的 `rule` 由 `R4_TEXT_MENTION_ONLY` → `MANUAL_OVERRIDE`（status 仍 UNKNOWN），
以及 note 中记录的核验结论。

**未改动**（§十一）：N 阈值 · concentration 阈值 · LOO · stability · derived structure gate ·
`anchor_priority`（EARLY_SIGNAL → THEME_FORMING → BROAD_CONFIRMATION → Campaign.start）· `promotion_status` 判定。

---

## 4. Product Artifact Impact

**生成方式**：`python research/scripts/build_time_observation_patterns.py`（canonical flow，**未手工编辑**）。

| 检查项 | 结果 |
|---|---|
| 自检 | ✅ `PASS`（字段卫生 / 语义红线 / 判定一致性） |
| `--check`（逐字节可复现） | ✅ **PASS** |
| `TOP-01` | 不变（`TIMELINE`，N=7，中心 06-11） |
| `anchor_verification`（TOP-01） | `verified 2 / unknown 5 / conflict 0`（不变） |
| `label` | 「2 / 7 个锚点已完成仓库内证据核验」（不变） |
| `patterns` 数量与 ID | TOP-01 ~ TOP-04（不变） |
| 各 pattern 的 `observations` | **逐条一致**（不变） |

### 4.1 ★ 附带修正：产物中的「覆盖度元数据」此前已滞后

重新生成时发现该 Artifact 的 **coverage 元数据停留在 Wave 1A/1B 之前**（因为前两轮按指令未重跑本生成器）：

| 字段 | 重新生成前（滞后） | 重新生成后（正确） |
|---|---|---|
| `coverage.total_objects` | 13 | **17** |
| `coverage.campaigns` | 9 | **13** |
| `coverage.anchor_type_counts.EARLY_SIGNAL` | 13 | **17** |
| `coverage.annual_review_status` | 仅 3 个 rule | **4 个 rule**（补入 `rule_power_equipment#2018–2025` 与 `rule_infocomm#2018–2025`） |

- **这只是把产物与当前数据集对齐，未产生任何新 pattern**（TOP-01~04 完全不变）。
- 说明：`coverage` 是**元数据**（描述数据集规模），不是统计量；其变化不影响任何判定。
- ⚠️ 需知悉：`src/data/timeline/timeObservationPatterns.ts` 通过 `@observation` 别名**导入该 JSON**，
  因此本次变更会进入前端 bundle（380.87 kB → **382.27 kB**，+1.4 kB，全部为 verification note 文本）。
  `npm test` 395/395 通过（含 `timeObservationPatterns.test.tsx` 58 项）。

---

## 5. company / capital finding（§十二）

**问题**：Wave 1B 已出现 `source_type = company_announcement`（3 条），为何 `company` 的 **evidence_type** 仍为 0？

**结论：这是 taxonomy / normalization 缺口，不是 schema 缺口。**

### 5.1 根因（实测）

1. **两个词表彼此独立**：
   - `evidences.evidence_type` 描述**证据本身的类别**（实测在用 7 个值：
     `行情数据 34` · `行业数据 19` · `政策文件 13` · `media 8` · `行业月度产销数据 5` ·
     `official_document 3` · `market_data 1`）
   - `sources.source_type` 描述**来源的类别**（实测在用 7 个值：
     `media_tier2 47` · `regulator 22` · `media_tier3 7` · `website 3` ·
     **`company_announcement 3`** · `media_tier4 2` · `exchange 1`）
   - 二者**没有外键约束或映射关系** —— `company_announcement` 来源完全可以承载任意 `evidence_type` 的证据。

2. **审计脚本的归一化表缺键**：`audit_historical_coverage.py:191` 的 `EVIDENCE_TYPE_MAP`
   只映射 7 个**已观测到**的值 → 4 个 canonical 桶（`market` / `industry` / `policy` / `information`），
   **没有 `company` / `capital` 键**；而同一文件的 `CANONICAL_EVIDENCE_TYPES`（第 202 行）
   却声明了 6 类（含 `company` / `capital`）。**词表与 canonical 列表不一致。**

3. **Wave 1B 的处置**：为避免引入**未映射取值**（会落入 `UNCLASSIFIED`，反而污染审计产物），
   公司财报类证据的 `evidence_type` 使用了既有的 `行业数据`（→ `industry`），
   `source_type` 才用 `company_announcement`。**未伪造，也未新增未映射取值。**

### 5.2 最小修复建议（**本轮不实施**）

**两步，均不需要改 schema：**

1. **扩展归一化表**（`audit_historical_coverage.py:191`），补入公司 / 资金类键：
   ```python
   "公司公告": "company",
   "company_announcement": "company",
   "公司数据": "company",
   "资金流向": "capital",
   "capital_flow": "capital",
   ```
2. **把已有的 3 条公司财报类证据**的 `evidence_type` 由 `行业数据` 改为 `company_announcement`
   （E-COMM-12 / E-COMM-13 / E-COMM-14 —— 分别对应 NVIDIA FY2024 Q1 官方新闻稿、
   中际旭创 2023 半年报、中际旭创 2023 年报）。

**为何不在本轮实施**：
- 步骤 1 会改变 `EVIDENCE_TYPE_MAP` → 改变审计产物内容 → **必须注册新的审计轮次（v0.3）**，
  不能就地修改 v0.2 快照（§十一 的同类原则：不改既有判定口径）。
- 步骤 2 是 **DB 数据变更**，超出「本轮只处理 Time Observation 可信度」的范围。

**→ 按 §十二 要求：只提出建议 + 登记 `DATA_GAP`，不在本轮实施。**

### 5.3 DATA_GAP 登记

| DATA_GAP | 类型 | 说明 |
|---|---|---|
| `evidence_type` 缺 `company` / `capital` 归一化键 | taxonomy / normalization | 建议见 5.2；需新审计轮次 |
| `capital` 证据**完全不存在**（不只是词表缺键） | 数据缺口 | 全库 0 条资金流向类证据；即使补了词表仍为 0 |
| `evidence_type` 中英文混用未统一 | taxonomy | 既有 P1 待办；本轮沿用既有可归一化取值 |

---

## 6. Tests

| 门禁 | 结果 |
|---|---|
| `npm test` | ✅ **395 passed / 395（10 files）** |
| `npx tsc -b` | ✅ **exit 0** |
| `npm run build` | ✅ **PASS**（382.27 kB JS / 38.86 kB CSS） |

**本轮未修改任何测试文件**（无测试断言依赖 verification metadata 的具体 note 文本）。

---

## 7. Validators

| 校验器 | 结果 |
|---|---|
| `validate_db.py` | ✅ PASS |
| `validate_timeline_export.py` | ✅ PASS |
| `validate_batch_research.py` | ✅ PASS |
| `validate_promotion_manifest.py` | ✅ PASS |
| `check_doc_schema_consistency.py` | ✅ PASS |
| `validate_current_research.py` | ✅ PASS |
| `validate_monorepo_integrity.py` | ✅ PASS |

### 7.1 生成器状态（§十三 要求）

| 生成器 | 结果 | 说明 |
|---|---|---|
| `build_time_observation_patterns.py --check` | ✅ **PASS** | 本轮已重新生成，逐字节可复现 |
| `audit_historical_coverage.py --check` | ⚠️ **FAIL（预期）** | v0.2 是 Wave 1A 数据集快照；数据已前进。**未重跑**（§十八 禁止自动开始 Coverage Audit v0.3） |
| `discover_time_observation_patterns.py --check`（默认 0.4） | ⚠️ **FAIL（预期）** | 同上；候选池为旧快照。**未重跑** |
| `discover_time_observation_patterns.py --round 0.4 --check` | ⚠️ **FAIL（预期）** | 同上 |

> `ROUND_PROFILES`（实测）：`0.2` = direct 口径 · `0.3` = canonical 无派生门 · **`0.4`（默认）= canonical + 派生结构门**。
> 重跑 Discovery **必须新 `ROUND_PROFILE`（v0.5）**，不得覆盖 v0.2/v0.3/v0.4。

---

## 8. Determinism

| 检查 | 结果 |
|---|---|
| `build_time_observation_patterns.py --check` | ✅ **PASS —— 磁盘产物与重算结果逐字节一致（可复现）** |
| 核验 override 的键唯一性 | ✅ 生成器自检通过（重复键会 `SystemExit`） |
| VERIFIED 必须带 source | ✅ 未触发（本轮 status 均为 UNKNOWN） |
| 统计量 before/after | ✅ **完全一致**（见 §3） |
| `evidences` / `events` / `market_series` 变更 | ✅ **零变更**（本轮未改任何研究数据） |
| 换行符 | ✅ `i/lf w/lf`（无 EOL 抖动） |

---

## 9. Git

### 9.1 变更清单（2 个文件）

| 文件 | 变更 |
|---|---|
| `research/research/reports/time_observation_anchor_verification_v0_1.json` | `overrides: [] → [2 条 UNKNOWN override]`（+24 / −2 行） |
| `research/research/reports/time_observation_patterns_v0_1.json` | 重新生成：`manual_overrides 0→2` · 两个锚点 rule → `MANUAL_OVERRIDE` · coverage 元数据对齐（+33 / −17 行） |

**未修改**：`schema.sql` · `contracts/` · DB（`.db` 零变更）· `exports/` · `src/**`（含 Product TS Artifact）·
`research/current/` · 任何测试文件 · Promotion Gate 规则。

### 9.2 提交纪律

未使用 `git add -A`；逐文件 `git add`；提交前核对
`git diff --stat` / `git diff --cached --stat` / `git diff --cached --name-status`。
**未**执行 `force push` / `--amend` / `rebase` / `reset --hard`。

**Commit message**：`research: verify time observation anchors`

### 9.3 提交后状态

`HEAD == origin/main` · ahead/behind `0/0` · 工作树 clean（实际哈希见本轮回复与 `git log`）。

---

## 10. Remaining Data Gaps

| # | 缺口 | 严重度 | 说明 |
|---|---|---|---|
| 1 | **TOP-01 仍为 2/7 核验** | HIGH | 5 个锚点无 Tier ≤2 同日证据；本轮已穷尽仓库内可用证据 |
| 2 | **全库日期核验仍为 0/24** | HIGH | `campaign_date_observations.verified_date` 全为 NULL；本轮**未**改 DB（核验元数据层≠DB 核验字段） |
| 3 | **★ 证据描述文本与所引来源不一致** | **HIGH（本轮新发现）** | `E-2023-04` 称「6/12预热」、`E-2024-03` 称「6/11-6/21」——**两条源文全文均未出现该日期**。属**数据质量问题**：描述中的日期断言缺乏来源支撑 |
| 4 | **V2X 概念指数无行情数据** | MEDIUM | `V2X` 为 `EMPTY_PLACEHOLDER`（0 行）→ C-2024-V2X 的锚点无法以行情佐证 |
| 5 | `evidence_type` 缺 `company` / `capital` 键 | MEDIUM | 见 §5；需新审计轮次 |
| 6 | `capital` 证据完全不存在 | MEDIUM | 词表修好后仍为 0 |
| 7 | 交易日历仍为 371 行（2022-03 ~ 2024-09） | MEDIUM | 未补全 |
| 8 | `evidence_type` 中英文混用未统一 | MEDIUM | 既有 P1 |
| 9 | `audit` / `discover` 两类产物滞后 | LOW | 快照预期行为；需新轮次 |
| 10 | `F7`：`华为汽车` 不在 `themes` 表 | LOW | 既有 DEFER |

### 10.1 ★ 关于 #3 的处理建议

**不建议本轮修改 `evidences.description`**（那是数据变更，且会改变证据文本）。
建议在**下一轮**二选一：

- **A（推荐）**：为这两个锚点**补登独立的同日日期证据**（新增 `evidences` 行，date = 锚点日期），
  若届时能找到 Tier ≤2 来源 → 锚点可升为 VERIFIED；
- **B**：若确认无法找到来源 → 保留 UNKNOWN，并在证据描述中**显式标注该日期断言无来源支撑**，
  避免后续误用。

---

## 11. Recommended Next Step

### 11.1 本轮结论

> **TOP-01 verified = 2 / 7（未变化）** · unknown = 5 / 7 · conflict = 0 / 7
> **N / center / window / recurrence / stability / LOO / dispersion / promotion_status 完全保持。**
> 本轮**未能**提高核验数量 —— 这是**穷尽仓库内证据后的诚实结论**，不是执行失败。

**本轮的实际产出**：
1. 用**词边界**扫描 + **取回源文全文**，对 5 个 UNKNOWN 锚点逐一给出可复核的结论；
2. 把两个优先候选的核验过程**固化为 override 元数据**（`manual_overrides 0 → 2`），避免重复劳动；
3. 发现并登记一条 **HIGH 级数据质量问题**（证据描述含无来源支撑的日期断言，见 §10 #3）；
4. 修正了 Product Artifact 的**覆盖度元数据滞后**（13→17 对象）；
5. 给出 `company` / `capital` 的**根因定位 + 最小修复建议**（不实施）。

### 11.2 建议的下一单一步骤（**只做一件**）

> **先处理 §10 #3 的数据质量问题（证据描述与来源不一致）** ——
> 对 `E-2023-04`（2023-06-12）与 `E-2024-03`（2024-06-11）二选一执行 §10.1 的 A / B 方案。

**理由**：

1. 这是本轮**唯一新发现的 HIGH 级问题**，且**直接影响 TOP-01 的锚点可信度** ——
   两个「看起来有 Tier 2 支撑」的锚点，实际来源并不支持该日期。
   若不处理，下一轮会重复同样的核验工作，且描述中的错误断言会持续存在。
2. **成本极低**：A 方案是新增 2 条 evidence 行；B 方案是标注 2 条描述。
3. `theme_family_count` 已达 4、Wave 1B 已修复信息通信断裂 ——
   **继续扩覆盖度的边际收益低于先修数据质量**。
4. 它**不触碰** Promotion Gate 规则，也不进入 Structural Analogy，符合本轮边界。

**替代方案（若用户更倾向覆盖度优先）**：`Wave 1C（高端装备）`。

### 11.3 本轮**未**启动（等待授权）

Wave 1C · Structural Analogy · Coverage Audit v0.3 · Time Observation Discovery 重跑 ·
DB 层日期核验写回（`verified_date`）· `evidence_type` 词表扩展 · 交易日历补全。

---

*报告结束 · Phase 7.4A — Anchor Verification + Data Quality 收敛 · 2026-09-18*
