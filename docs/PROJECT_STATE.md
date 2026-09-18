# PROJECT_STATE.md — ThreeC

> 接班必读②（读完根 `AGENTS.md` 后读本文件）。
> **本文件描述的是「仓库当前真实状态」，不是「计划」也不是「历史报告的自述」。**
> 所有数字均可由仓库内命令复算；发现不一致时**以仓库为准**。

- **重建日期**：2026-09-17（Repository Recovery 之后重写，未照抄旧版）
- **最近更新**：2026-09-18 · **Phase 7.4B — Date Claim Cleanup + Evidence Normalization**（`company` 0→3）
- **HEAD**：见 `git log -1`（`fix(research): clean unsupported historical date claims`）· 本文件随该提交入库
- **Phase 7.4B 前的基线**：`HEAD = origin/main = 2c16058` · ahead / behind `0 / 0` · 工作树 clean

---

## Project Purpose

**ThreeC = A股历史机会时间轴 / 历史机会地图。**

回答：今天在一年中的什么位置 → 历史上这个时间发生过什么 → 主题如何形成 / 发展 / 转折 / 结束 →
有没有提前信号 → 为什么启动 / 加速 / 转折 / 结束 → **现在应该去研究什么**。

**核心价值 = 机会发现，不是交易决策。** 基本面 / 技术面 / 选股 / 入场时机由用户自己负责。
详见 `docs/PRODUCT_PURPOSE.md`。

---

## Repository Identity & Hygiene

**唯一真相源原则：一个 Git、一个 ThreeC 根、一套 canonical Research、一套 Product。**
Research 与 Product 仍是**逻辑分层**，但**不再由两个独立会话 / 两个独立仓库管理**。

```
root                    D:\@AW\投资\ThreeC
Git                    单一仓库（根 .git，无嵌套仓库）
remote                  https://github.com/yangfanbit/Cycle.git
已跟踪文件               306（research/ 下 211）
research/ 磁盘内容       恰好 = HEAD 的 211 个文件（零多余、零缺失）
memory canonical 位置    .workbuddy/memory/      ← 不是 .workbuddy-ai/
```

- **2026-09-17 完成 Repository Recovery**：上一轮会话把独立 Research 项目整体复制进工作区，
  产生嵌套克隆 `research/.git` 与 264 个未跟踪重复文件。已全部清除（**零已跟踪文件被改动**）。
  完整报告：`docs/REPOSITORY_RECOVERY_REPORT_2026-09-17.md`。
- **干净基线（复算即可自证）**：

  | 门禁 | 期望值 |
  |---|---|
  | `npm test` | **395 / 395，10 files** |
  | `npx tsc -b` · `npx vite build` | exit 0 |
  | `scripts/validate_monorepo_integrity.py` | **PASS（25 项，0 警告）** |
  | `research/scripts/build_time_observation_patterns.py --check` | PASS 逐字节 |
  | `research/scripts/discover_time_observation_patterns.py --check` | PASS 逐字节 + TOP-01 回归 |
  | `... --round 0.2 --legacy-direct-resolution --check` | PASS 逐字节 |
  | `... --round 0.3 --legacy-no-derivation-gate --check` | PASS 逐字节 |
  | `... --round 9.9 --check` | **exit 1**（未知轮次守卫，预期） |
  | `research/scripts/audit_historical_coverage.py --check` | PASS 逐字节 |
  | `validate_*.py` ×6 · `test_*.py` ×3 | 全 PASS |

- **★ 灵敏探针**：若 `npm test` 报 **19 files / 732 tests**，说明 `research/` 下又出现了第二套
  `src/**`（重复副本复发）。若 `validate_monorepo_integrity` 报 `.git 唯一性` 或
  `canonical export 唯一性`，同理。
- **禁止**：`git add -A` · `reset --hard` · `clean -fd` · `checkout .` · `push --force` ·
  `rebase` 已推送历史 · `commit --amend` · `git add --renormalize`。详见 `.workbuddy/memory/MEMORY.md` §7。

---

## Current Phase

**Phase 7.3.2：Promotion Gate — Derived Structure Exclusion（IMPLEMENTED，已推送）。**

把「`derived_from_early_signal = true` 的结构不得作为独立规律」从研究报告里的观察
**正式落进 Promotion Gate**：`TIMELINE_CANDIDATE` → **降级 `EXPLORATORY`**。

- 判据：阶段中心 ≈ EARLY_SIGNAL 中心 + 中位滞后（残差 ≤ 21 天，阈值沿用既有设定，**未调整**）。
- **三值判定，只降不升**：`True` → 降级；`False` → 不动作；`None`（无节奏判定 / 缺字段）→ **不下结论**。
  **`None` ≠ 独立，只是「无证据」。** 本门**从不主动断言「非派生」**（实测 `False` = 0 条）。
- 口径固化在 `ROUND_PROFILES`：`--round X` 一并恢复该轮口径 → v0.2 / v0.3 / v0.4 **三轮逐字节可复现**；
  未知轮次**显式 FAIL**（`SystemExit`，不静默降级）。
- 降级落点为何是 `EXPLORATORY` 而非 `RESEARCH_ONLY`：派生候选**数值门槛已通过**，缺的是**独立性** ——
  逐字命中 `EXPLORATORY` 定义；`RESEARCH_ONLY` 描述的是数值弱。先例一致（`FRAGILE_SCOPE_DEPENDENT` 同样落此）。
- 可追溯：`derivation_verdict` 含 `derived_from_pattern_id` / `derived_from_stage` / `stage_verdicts` /
  `reason` / `note`。**派生候选一律保留，不得删除。**
- 回归测试：`research/scripts/test_derivation_gate.py`（6 组，含合成输入覆盖真实数据中不存在的路径）。
- 报告：`research/research/reports/Time_Observation_Discovery_v0_4.md` §12。

**本轮（2026-09-17）另完成 Repository Recovery**（无功能变更，只清理重复副本 + 补两处 gitignore 防护）。

**下一阶段未启动。** Wave 1 数据扩容与 Structural Analogy 仍处于**禁止**状态，见「Next Single Goal」。

---

## Completed

| Phase | 内容 | 状态 |
|---|---|---|
| Phase 1 | Research Model v1.0（**Frozen**） | ✅ |
| Phase 2 | Historical Data Production v1（2018–2025 批量研究） | ✅ |
| Phase 3 | Timeline MVP（Conflict Visual / Phase Window / Drivers / SamePeriod / Export Adapter / Preview-Production 隔离） | ✅ |
| Phase 4 | Monorepo Integration（Cycle 11 commits + Cycle-Research 28 commits 经 `git subtree` 并入，保留原始 author / date / message）+ Handoff Infrastructure | ✅ |
| Phase 5 | Current Time Lens v0（今天入口：时间定位 → 历史同期 → 历史阶段映射 → 可能驱动） | ✅ |
| Phase 5.1 | V1.8.1 主题级历史机会视图（IA 重排：Timeline 第一视觉） | ✅ |
| Phase 5.2 | V1.8.2 Timeline Detail UX + 提前观察参考区 | ✅ |
| Phase 5.2.1 | V1.8.2.1 Pre-observation Semantic Fix（Formation Anchor） | ✅ |
| Phase 5.3 | Theme / Campaign 分层模型统一审计（Macro Theme → Theme Cycle → Campaign → Sub-theme；Independence Gate Q1–Q5） | ✅ |
| Phase 5.4 | Research Model v1.1 方法论补丁（Theme Cycle Pattern A/B/C · Lifecycle Measurement Rule · Gate Q1 反例） | ✅ |
| Phase 5.5 | 医药健康 Pilot（首个非汽车 Macro Theme：1 正式 Campaign + 2 Research Candidate） | ✅ |
| Phase 5.6–5.8 | F-MED-1 跨年年份语义 · Timeline Entry Identity（`entryId`）· Year Coverage Rule | ✅ |
| Phase 6 | V2.0 Product Core v2（F-MED-6 身份分离 · Current Time Lens v2 三层 · Research Attention Gate v1 · Historical Similar Phase v1 · Macro Theme 聚合接口 · IA 重排） | ✅ |
| Phase 7 | Current Research Discovery v0.1（`research/current/` 协议 + 验证器 · Temporal Firewall · Phase Evidence Matrix · 透明规则引擎 R0–R8 · Similarity v2 · Research Questions · 当前研究候选 UI） | ✅ |
| Phase 7.1 | First Real Current Research（`snapshot 2026-09-15`：5 个真实候选 / 39 条证据 / 0 条快照后证据 · 并行轮次裁决） | ✅ |
| Phase 7.2 | Time-based Observation Layer（`time_observation_patterns_v0_1.json`：4 条模式 → **1 条进入 Timeline** · canonical 生成器 · 跨年环形窗口 · Timeline 内极轻观察层） | ✅ |
| Phase 7.3 | Observation Credibility & Coverage（锚点核验 R1–R5 机械推导 · Theme Family · `promotion_status` 统一 · Current Match vs Historical Recall 分离） | ✅ |
| **Phase 7.3.2** | **Promotion Gate — Derived Structure Exclusion**（派生结构门进 Gate · `ROUND_PROFILES` 固化 · `compare_time_observation_rounds.py` · `test_derivation_gate.py`） | ✅ |
| **Recovery** | **Repository Recovery + Research Integration**（嵌套克隆清除 · 264 重复文件裁决清除 · 全新克隆复现性验证 · 报告留档） | ✅ |

---

## Current Research State

### 模型与数据基座

- **Research Model v1.0 Frozen**；`research/schema/schema.sql` 冻结（**17 表**）。
- 研究状态词汇：`RAW / PROVISIONAL / CONFLICT / INSUFFICIENT / VERIFIED`（表达在 batch / manifest 层，**不改 SQLite 正式 schema**）。

### 数据库实测（`research/database/cycle_research.db`）

| 表 | 行数 | 表 | 行数 |
|---|---:|---|---:|
| campaigns | 13 | themes | 19 |
| campaign_themes | 31 | campaign_phases | 48 |
| campaign_date_observations | 24 | campaign_evidences | 76 |
| campaign_events | 42 | campaign_securities | 51 |
| evidences | 83 | events | 49 |
| market_series | 56 | market_daily | 79,466 |
| trading_calendar | 371 | sources | 85 |
| securities | 48 | annual_reviews | 28 |
| research_rules | 4 | | |

> Wave 1B（2026-09-18）后实测值。核验相关：`campaign_date_observations` 仍 **24 行、
> `verified_date` 全为 NULL（核验 0/24）** —— Wave 1A / 1B **两轮均未新增日期核验**。

### Canonical Export（`exports/timeline_export_v1.json`，`timeline_export_version = "1.0"`）

- **13 个 Campaign**：12 `PROVISIONAL` + 1 `CONFLICT`（`C-2024-ROBOTAXI`）；**13 个 Theme Cycle**。
  年份跨度 2019–2025（跨年 Campaign：`C-2019-PHARMA-INNOV` 2019–2022 · `C-2020-POWER-NE` 2020–2022 ·
  `C-2022-POWER-GRID` 2022–2025 · `C-2019-COMM-5G` 2019–2022 · `C-2023-COMM-OPTICAL` 2023–2025）。
- 4 个 Research Candidate（永不 verified）· 52 个 events · 63 个 securities · 22 个 signals · 4 个 rules。
- 顶层 11 字段白名单，未知字段拒绝；契约 `contracts/timeline_export_v1.md`。**Research 生成，Product 只读消费。**

### Canonical Macro Theme Resolution v1（CMTR v1）

- **唯一实现** `research/scripts/theme_taxonomy.py`（`discover_time_observation_patterns.py` 与
  `audit_historical_coverage.py` 共用）。**禁止再写第二份口径。**
- 方向：`themes[]` 名称 → DB `themes` 表归一化 → 沿 `parent_theme_id` 上溯至根。
  **已废止 `direct`（字面名称匹配）**，`rule_id` / `theme_scope` **不再**充当主题身份。
- 实测（Wave 1B 后）：`TH-AUTO` 9 成员 · `TH-PHARMA` 3 成员 · `TH-POWER` 2 成员 · **`TH-COMM` 2 成员**；
  `RESOLVED` 16 / `CONFLICT` 0 / `UNRESOLVED_NAME` 1（`华为汽车` = DEFER `F7`）/ `NO_THEME` 0。
- **Macro Theme root 实测 4 个**：`TH-AUTO`（汽车）· `TH-PHARMA`（医药健康）· `TH-POWER`（电力设备）·
  **`TH-COMM`（信息通信）**。
  `TH-POWER` 由 Wave 1A（2026-09-17）新建，含 3 个 Sub-theme；
  `TH-COMM` 由 Wave 1B（2026-09-18）新建，含 2 个 Sub-theme（`TH-COMM-5G` / `TH-COMM-OPTICAL`）。
  命名受 `candidatePatternOf()` 的**精确字符串匹配**约束 → `name` 必须与 Current 侧声明一致
  （「电力设备」/「信息通信」）。
- 只读：不修改数据、不发明 taxonomy 行、不改变锚点定义与统计量。
- 收益：v0.2 的 5 对「口径脆弱」**全部归零**；两种 scope 口径下的 TOP-01 变体收敛为同一样本集合。

### Time Observation（当前研究结论）

**Canonical Product Artifact**：`research/research/reports/time_observation_patterns_v0_1.json`
（生成器 `research/scripts/build_time_observation_patterns.py`，`--check` 逐字节可复现）。

> ⚠️ **以下全部结论基于 Wave 1A 之前的输入数据集**（2 个 Macro Theme / 9 Campaign）。
> Wave 1A（2026-09-17）新增 `TH-POWER` + 2 个 Cycle 后，**本轮刻意未重跑 Time Observation Discovery**
> （不得覆盖 v0.2 / v0.3 / v0.4 provenance）。因此：
> - `build_time_observation_patterns.py --check` 与 `discover_time_observation_patterns.py --check`
>   现为 **FAIL**（产物为旧数据集快照）—— 这是**预期状态，不是回归**；
> - 下列 TOP-01 ~ TOP-04 与「独立稳健结构 = 1」**仍是对旧数据集的有效结论**，
>   但**尚未在含电力设备的新数据集上复核**；
> - 重跑**必须注册新 `ROUND_PROFILE`（v0.5）**，并保留 v0.2/v0.3/v0.4 产物。

| Pattern | 主题范围 | 观测年数 | 中心 | 典型窗口 | 复现 | 强度 | `promotion_status` |
|---|---|---:|---|---|---|---|---|
| **TOP-01** | 汽车（上半年末启动） | **7** | **06-11** | **05-27 ~ 06-26**（31 天） | **5 / 7**（2020·2021·2023·2024·2025 命中；2019·2022 未命中） | **A** | **TIMELINE** |
| TOP-02 | 汽车 | 4 | 06-17 | 06-09 ~ 06-25 | 3 / 4 | B | RESEARCH_ONLY |
| TOP-03 | 汽车（电动化） | 2 | 06-01 | 不可构建 | — | C | EXPLORATORY |
| TOP-04 | 医药健康 | 3 | 01-23 | 不可构建 | — | D | REJECTED |

- **`promotion_status` 为 authoritative**；`status` / `timeline_eligible` / `timeline_eligibility` 为**兼容输入**。
- **锚点核验（Phase 7.3 建立 · Phase 7.4A 收敛）**：策略 + 人工覆盖位在
  `time_observation_anchor_verification_v0_1.json`；生成器从 research DB **机械推导**。
  合计 **VERIFIED 3 / UNKNOWN 13 / CONFLICT 0**；
  **TOP-01 = 2 / 7**（2022-04-27 `MARKET_DATA`；2025-06-22 `PUBLIC_SOURCE` Tier2）。
  **核验通过 ≠ 规律有效**，也不代表未来会重复。
- **Phase 7.4A（2026-09-18）**：对 TOP-01 的 5 个 UNKNOWN 锚点逐一完成核验（**含取回源文全文**），
  **verified 仍为 2 / 7** —— 5 个锚点均无 Tier ≤2 同日证据。
  两个优先候选（`2023-06-12` / `2024-06-11`）已固化为 **UNKNOWN override**（`manual_overrides` 0 → 2），
  记录核验过程以避免重复劳动。**统计量（N / center / window / recurrence / LOO / stability /
  promotion_status）完全保持。**
  报告：`docs/PHASE_7_4A_ANCHOR_VERIFICATION_REPORT_2026-09-18.md`。
- **Phase 7.4B（2026-09-18）**：清理 2 条**无来源日期断言**（`E-2023-04` 的「6/12预热」、
  `E-2024-03` 的「6/11-6/21」）→ 标注 **UNSUPPORTED**（保留证据本身，只改断言）；
  并把 3 条公司自身披露证据的 `evidence_type` 规范化为 **`company`**（**0 → 3**）；
  **`capital` 保持 0**（全库无此类证据，未虚构）。
  **TOP-01 与 anchor 完全未变**；`UNCLASSIFIED` 仍为 0。
  报告：`docs/PHASE_7_4B_DATE_CLAIM_CLEANUP_REPORT_2026-09-18.md`。
- **Discovery 轮次**（研究侧候选池，非产品 Artifact）：

  | 轮次 | 口径 | 产物 |
  |---|---|---|
  | v0.2 | `direct_resolution = True`，无派生门 | `time_observation_candidate_pool_v0_2.{json,csv}` · `Time_Observation_Discovery_v0_2.md`（**legacy baseline，保留不删**） |
  | v0.3 | `direct_resolution = False` | `..._v0_3.*` · `Time_Observation_Discovery_v0_3.md` |
  | **v0.4（默认）** | `derivation_gate = True` | `..._v0_4.*` · `Time_Observation_Discovery_v0_4.md` |

- **★ 结论：独立稳健时间结构 = 1 个**（TOP-01，汽车族 EARLY_SIGNAL 上半年末窗口）。
  `effective TIMELINE_CANDIDATE` **4 → 2**；`EXPLORATORY`（effective）44 → 46。
  受影响候选恰好 2 条：`TOPC-004`（派生自 `TOPC-001`）、`TOPC-021`（派生自 `TOPC-018`），均 MAIN_RISE，中心 06-22。
- **★ 派生范围**：两个有节奏分析的 scope 各 **7 个阶段全部派生**
  （`THEME_FORMING` … `MAIN_END`）→ **EARLY_SIGNAL 是本数据集里唯一的时间信息来源**，其余阶段皆为下游回声。
- **账目**：191 = 139（scope 无节奏分析）+ 22（含非 export 阶段）+ 30（全部阶段派生）。
- **背景基线（选择偏差，已写入 Artifact `background_baseline`）**：ThreeC 自建事件台账 6 月占比
  **33.33%**（均匀基准 8.33%）；即使只看指数「最优 30 日窗口」6 月占比也达 **18.75%**
  → 任何 6 月偏好**部分来自研究样本选择偏差**，不可解读为主题独有季节性。
- 结论表述（不可越界）：**「6–8 月汽车」= 历史观察窗口（Historical Observation Window），
  Partially Supported，非固定买入窗口。**
  见 `research/research/summary/auto_2018_2025_final_review.md`。

### Current Candidate（Phase 7 / 7.1，第四类对象）

- 数据：`research/current/current_candidates.json`（`snapshot_date = 2026-09-15`，
  `research_round = First Real Current Research Discovery（Phase 7.1）`）—— **5 个真实候选 / 39 条证据**。
- **不是** Theme / Campaign；**不写** DB / schema / export / contracts；命名空间 `CC-*`（fixture `FX-*`）。

| candidate_id | 推导阶段 | 证据数 |
|---|---|---:|
| `CC-2026-BCI-MEDTECH` | `UNKNOWN`（诚实空态：政策/标准落地但关注度自高位回落 → 结构冲突 → 引擎拒绝归类） | 7 |
| `CC-2026-COMPUTE-POWER` | 广泛确认 | 10 |
| `CC-2026-EMBODIED-AI` | 扩张（存在冲突 → 降级观察） | 8 |
| `CC-2026-OPTICAL-LINK` | 扩张 | 8 |
| `CC-2026-OFFSHORE-WIND` | 主题形成 | 6 |

- 验证器 `research/scripts/validate_current_research.py`（6 组校验，退出码 0/1）实测
  **5 通过 / 0 警告 / 0 失败**；`narrative_annotations.json` 13 条标注亦通过。

---

## Current Data Coverage

> 来源：**`Historical Coverage Audit v0.3`**（`research/research/reports/historical_coverage_matrix_v0_3.{json,csv}`，
> 生成器 `research/scripts/audit_historical_coverage.py --round 0.3`）+ 本轮 DB 实测复核。
>
> **多轮约定**：审计产物是「某个数据快照」的确定性函数。`--round X` 一并恢复该轮的
> 产物路径 / 快照日期 / 版本号；**未知轮次显式失败**，不静默降级。已登记 `0.1`（Wave 1A 之前）
> 与 `0.2`（Wave 1A 之后）。
>
> ⚠️ **v0.1 快照对应 Wave 1A 之前的数据集**（其 `--check` 现与重算结果不一致，属**预期**，
> 不是回归）；v0.1 产物**原样保留**、未被覆盖。下表为 **v0.2 / 2026-09-17 实测**。

| 维度 | Wave 1A 后（实测） | Wave 1A 前（Audit v0.1） | 缺口 |
|---|---|---|---|
| Campaigns / Theme Cycles / Macro Themes | **13 / 13 / 4** | 11 / 11 / 3 | `theme_family_count` **首次达到 ≥ 4 门槛**（但跨族稳健性检验需重跑 Time Observation 才能判定） |
| 有效年份 | **2019–2025（7 年）** | 同 | 2018 为 `no_clear_campaign`（刻意排除，非缺失）；未达 `N ≥ 8` |
| Lifecycle 完整度 | 17 对象：`THEME_FORMING` **58.8%** · `BROAD_CONFIRMATION` **58.8%** | 15 对象：各 53.3% | 最弱仍是这两个阶段（Formation Anchor 依赖） |
| Evidences | **83**（policy 16 · industry 21 · **company 3** · market 35 · information 8 · **capital 0**） | 67 | **Phase 7.4B 后 `company` 0 → 3**（公司自身披露类证据规范化）；`capital` **真实为 0**（全库无可归类证据，未虚构）；`UNCLASSIFIED` = 0 |
| Events | **49（DB）/ 52（export）**；`industry` 1 → **2** | 39 / 42 | 仍 6 类 `NOT_AVAILABLE`；本轮新增 5 项 `DATA_GAP` 登记（见 Wave 1B 报告 §F.1） |
| Market Series | **56**（新增 8 条信息通信代表标的） | 48 | 仍是「按 Campaign 窗口采样」 |
| Trading Calendar | **371 天，仅覆盖 2022–2024** | 同 | **未补全** |
| 日期核验 | **0 / 24**（DB `verified_date` 全为 NULL） | 同 | **可信度硬天花板**。⚠️ **核验元数据层**（`time_observation_anchor_verification_v0_1.json`）另有 **VERIFIED 3 / UNKNOWN 13**；TOP-01 = **2/7**（Phase 7.4A 后未变）。两层不是同一件事 |
| 主题族数 | `theme_family_count` **= 4** | 3 | **已达 audit 的 ≥ 4 门槛** |
| 当前侧 vs 历史侧 | 历史侧 4 个；当前侧 4 个 | 历史侧 3 个 | **电力设备 / 信息通信均已修复断裂**；**仅剩 高端装备** → Similarity Pattern 层仍为 `UNKNOWN` |

**Wave 1 优先级（`Historical_Coverage_Audit_v0_1.md` §12）**：

| 优先级 | 动作 | 状态 |
|---|---|---|
| P0 | 补录「电力设备」历史 Cycle | ✅ **已完成（Wave 1A，2026-09-17，2 个 Cycle）** |
| P0 | 补录「信息通信」历史 Cycle | ✅ **已完成（Wave 1B，2026-09-18，2 个 Cycle）** |
| P1 | 统一 `evidences.evidence_type` 口径 | ⏳ 未做（另需扩展词表以支持 `company` / `capital`） |
| P1 | 补全 2018–2025 交易日历 | ⏳ 未做 |
| P1 | 修复 `C-2019-AD` 的 Macro Theme 挂接 | ⏳ 未做（`F7` 相关） |

---

## Product Status

- **IA（V2.0，硬约束）**：① **Timeline（永远第一视觉）** → ② 当前时间研究导航（Lens v2 + 当前研究候选）
  → ③ 历史相似阶段（Lifecycle Lens）→ ④ 历史同期（Calendar Lens）。
  点击主题 / Campaign **不遮挡** Timeline；无大型 modal 覆盖。
- **两级详情（V1.8.2）**：Level 1 Inline Summary（就地展开，不离开页面）→ Level 2 Full CampaignDetail
  （桌面右侧浮层 / 移动端 Bottom Sheet）。
- **提前观察参考区**（`historicalPreObservationDays = 30`，UI / Research browsing buffer）：
  Formation Anchor = `THEME_FORMING.start → BROAD_CONFIRMATION.start → Campaign.start → null`；
  **禁止**取 lifecycle 最早 stage（会把 EARLY_SIGNAL 误认为形成）。文案统一「提前观察参考区」。
- **Timeline 身份语义**：`entryId = ${campaign_id}@${展示年份}`（React key / 高亮 / focus / 年份页签）；
  打开 Campaign Detail 仍用 `campaign_id`。覆盖年份 = `start` 年**连续到** `end` 年。
- **Current Time Lens v2 三层**：A 股整体环境 = `Unknown`（**绝不**从行业 Campaign 反推大盘）·
  当前 Theme / Theme Cycle（无当前年份数据 → **诚实空态**）· Research Attention 状态分类
  （`当前值得研究` / `保持观察` / `历史参考`，**不是评分 / 概率 / 信号**）。
- **Historical Similar Phase v1**：按「阶段 → Theme Cycle Pattern → Drivers 重叠」检索，Top 3 上限、
  「高 / 中 / 参考」分级、**无百分比**、必给「为什么类似」、无证据 → 空态不凑数。与 ④ 并存不可互替。
- **Phase 7.2 时间型观察层**（`TimeObservationLayer`，Timeline 内极轻一层）：
  Level 1 历史观察窗口带 + 研究观察起点标记 → Level 2 就地展开（窗口 / 口径 · **历史复现 X / Y 个观测年份** ·
  年份案例 · 为什么值得看 · 限制说明 · 免责声明）。**无可用窗口时整层不渲染。**
- **Phase 7 当前研究候选**：概览 → 就地展开详情（Why now → Current Evidence（含已隔离证据单列）→
  Possible Drivers → Estimated Phase（矩阵逐维来源 + 命中规则）→ Historical Similar Cases（四问）→
  What to research next → Uncertainty / Conflicts → **为什么它现在仍是 Candidate**）。
  **不显示相似度分数 / 百分比**；无候选时诚实空态，**不编造内容**。
- **三条机制红线**：① Temporal Firewall（`> snapshot_date` 的证据必须标 `AFTER_SNAPSHOT`，
  不参与阶段推断 / 状态判定 / 相似度；相似度只引用 `end <= snapshot_date` 的历史案例）·
  ② 8 维相位证据矩阵（**仅 3 维可研究声明**：narrative / breadth / information_marginal；
  **另 5 维必须由证据派生**：policy / industry / market / capital / company）·
  ③ Research Attention Gate **只降不升**（无证据 → ≤CANDIDATE；冲突 → ≤WATCH；UNKNOWN → ≤WATCH）。
- **Similarity v2**：阶段（曾经历 30 / 相邻 15）→ Theme Cycle Pattern（12/5）→ Drivers（×5）→
  Narrative 结构（×4）；Top3、**无百分比**、无证据 → 空态不凑数。
- **测试**：`npm test` **395 / 395（10 files）** · `tsc -b` · `vite build` 全绿。

---

## Architecture & Contracts

```
ThreeC/  (单一 Git, origin = yangfanbit/Cycle)
├─ src/                Product：React + TS + Vite（Timeline UI / Adapter / models）
├─ data/               Product 侧核验数据（verified 层当前为空）
├─ exports/            ★ canonical timeline_export_v1.json（唯一一份）
├─ contracts/          timeline_export_v1.md
├─ research/           Research 子系统（Python + SQLite）
│   ├─ database/cycle_research.db   （提交 Git，研究对象）
│   ├─ schema/schema.sql            （冻结）
│   ├─ scripts/                     （canonical 生成器 + 验证器）
│   ├─ current/                     ★ Current Candidate 数据协议（canonical + fixtures）
│   └─ research/                    （研究产物；嵌套目录名为历史遗留，刻意保留）
├─ scripts/            validate_monorepo_integrity.py
├─ docs/               项目级 + 产品级文档
└─ tests/
```

**前端只读消费三个静态 Artifact，运行时零网络请求：**

| alias | 指向 | 内容 |
|---|---|---|
| `@exports` | `exports/` | 历史研究数据（`timeline_export_v1.json`） |
| `@current` | `research/current/` | Current Candidate 数据集 |
| `@observation` | `research/research/reports/` | Time Observation Pattern（该目录下的探索性脚本**不是**产品依赖） |

**网络 / AI 只出现在离线研究数据生成端，不进入运行时。**
**Research 产物换行符约定**：`.gitattributes` 对 `research/**` · `exports/**` · `contracts/**` 声明 `-text`；
新增研究产物目录时**必须同步**该文件，否则可复现性红线会被破坏。

---

## Known Limitations

**数据类（不是缺陷，是项目定位与当前覆盖的真实状态）**

- Product 生产层（`data/verified/`）为空 → 生产首页只能显示空态，实际内容需 `?preview=1`。
- 所有历史日期为**研究候选日期**；`verified_date` **0 / 24**，全部 `confidence = low`。
- A股整体环境（Layer A）为 `Unknown`：无指数 / 成交量 / 资金 / 情绪数据源，**也不应由此推导大盘状态**。
- 2026 年无历史研究数据 → Layer B 为诚实空态（研究覆盖至 2025）。`Sentiment` driver 在研究数据中**没有来源** → 永不出现。
- Research Attention 的「当前值得研究」目前为空：现有正式 Campaign 均已记录到结束阶段。
- **幸存者偏差无法消除**：ThreeC 只记录「形成了 Campaign 的主题」，无法观测「同样在 6 月出现但未成势」的主题。
- 研究样本自身 6 月占比 33% → 时间聚集含研究选择偏差成分（已写入 Artifact `background_baseline`）。
- **Pattern 与 Theme Cycle 没有稳定映射键**：扩展到更多主题前需要一个显式的「主题族 ↔ rule / theme」定义表（模型层决策）。
- **派生门覆盖边界**：只对有节奏分析的 **2 个 scope** 生效；其余 18 个 scope `is_derived = None` →
  本门**无法**对它们下结论。**这不是「已证非派生」，而是「无证据」；不得把 `None` 读作「独立」。**
- `research/research/` 嵌套目录名为历史遗留，迁移时刻意保留。
- Research 脚本依赖腾讯免费行情接口（仅 `fetch_market_*` 需要网络）。

**Current Candidate 架构类（Phase 7.1 发现，已记录，未改产品代码；详见 `research/current/README.md` §9）**

1. Similarity v2 的 Pattern 层依赖 `macro_theme` 名称与历史 Theme Cycle 精确匹配 →
   本轮 4 个候选的新 Macro Theme 无同名 cycle，Pattern 层恒 0 → **等级最高只能到「中相似」**。
2. 「关注度从高位回落」直接判 `WEAKENING` → 触发结构冲突并把阶段退回 `UNKNOWN`；
   引擎无法区分「回落但仍高于一般水平」与「关注度消失」。
3. 证据台账必须覆盖 `MARKET` 来源类型，否则市场维度 `UNKNOWN`、阶段退回 `UNKNOWN`。
4. 「单日行情最多 `WEAK`」与「关注度下降 → `NEGATIVE`」两条规则**不对称**，使刚起步方向更难归入 `THEME_FORMING`。
- **同一快照可能有多个有效轮次**（2026-09-16 并行会话事件）→ 下一轮必须显式声明 `research_round`。

**仓库工程类**

- ⚠️ `research/**` 下 **169 个已跟踪文件存在「假干净」**：工作区 CRLF / blob LF，索引 stat 缓存使
  `git status` 直接判 clean 而不重新哈希。**不影响 `--check`**（产物 blob 与磁盘均为 CRLF），已用全新克隆实测确认。
  **不要用 `git add --renormalize`**（会产生一次性大 diff）。详见 Recovery Report §I.1。
- `npm audit` 报告 5 项漏洞（构建工具链传递依赖，未处理）。

**已解决（不再列为限制）**：`timeline_eligible` 与 `timeline_eligibility` 双字段并存 → Phase 7.3 已统一为
authoritative `promotion_status`（旧字段降为兼容输入，生成器自检保证一致）。`F-MED-1 / F4 / F8` 已修复。

---

## Next Single Goal

> **Phase 7.4B（Date Claim Cleanup + Evidence Normalization）已完成（2026-09-18）** ——
> `company` 0 → 3 · `capital` 保持 0 · `UNCLASSIFIED` 0 · Coverage Audit **v0.3** 已建立 ·
> **TOP-01 与 anchor 完全未变**。
> 见 `docs/PHASE_7_4B_DATE_CLAIM_CLEANUP_REPORT_2026-09-18.md`。
> **当前瓶颈仍是「数据」，不是「方法」——已从「覆盖度」转向「可信度与一致性」。**

**Wave 1A / 1B 已完成什么**

| 项 | Wave 1A（电力设备） | Wave 1B（信息通信） |
|---|---|---|
| 新建 Macro Theme root | `TH-POWER`「电力设备」+ 3 Sub-theme | `TH-COMM`「信息通信」+ 2 Sub-theme |
| 新增 Theme Cycle | 2 个 | 2 个 |
| 新增 Evidence / Event / Source | +16 / +9 / +15 | +16 / +10 / +15 |
| 修复的断裂 | `CC-2026-OFFSHORE-WIND` / `CC-2026-COMPUTE-POWER` | **`CC-2026-OPTICAL-LINK`** |
| 未解决 | 核验 0/24 · `company`/`capital` 仍 0 | 同（**两轮均未增加核验**）→ **Phase 7.4B 已修 `company`（0→3）** |

**下一步（默认路径）**

> **Time Observation Discovery 新轮次** —— 三项前置条件已全部完成：
> Date Claim Cleanup ✅ + Evidence Normalization ✅ + **Coverage Audit v0.3 ✅（已确认正常）**。
>
> ⚠️ **重跑必须新 `ROUND_PROFILE`（v0.5），不得覆盖 v0.2 / v0.3 / v0.4。**

**为什么现在可以进 Discovery**

1. Phase 7.4B 已完成用户设定的三项前置条件，且 Coverage Audit v0.3 的 `--check` **PASS**（可复现）。
2. v0.3 已把 `theme_family_count` 确认为 **4**、`company` 纳入统计、
   `declared_but_no_history` 收窄至 **`[高端装备]`** —— 覆盖度与词表口径均已稳定，
   可安全作为 Discovery 的新输入基线。
3. 继续做「数据质量」的边际收益已下降：7.4A 已穷尽 TOP-01 的仓库内证据，
   7.4B 已清理已定位的断言问题。

**替代方案（若优先补可信度）**

- 为 `2023-06-12` / `2024-06-11` 寻找**独立 Tier ≤2 来源**
  （若能找到 → 两锚点可升 VERIFIED，TOP-01 → **3/7 或 4/7**）；
- 或做**全库 evidence 描述 vs 源文一致性抽检**（7.4B §11.1 的系统性观察：
  E-2024-03 的情况提示同类问题可能不止 2 条）。

**仍需长期解决（不在下一步内）**

- **DB 层日期核验仍为 0/24**（`campaign_date_observations.verified_date` 全为 NULL）——
  ⚠️ 注意区分三层：DB 的 `verified_date`（0/24）≠ 核验**元数据层**的
  `time_observation_anchor_verification_v0_1.json`（VERIFIED 3 / UNKNOWN 13；TOP-01 2/7）
  ≠ **日期断言的来源支撑**（7.4B 处理的对象）。
- `capital` 的 `evidence_type` 为 0 —— 这是**真实为 0**（全库无可归类证据），
  词表键已在 7.4B 补齐；**不得为凑齐 6 类而虚构**。
- `evidence_type` 中英文混用未统一 · 交易日历不完整 · V2X 概念指数无行情数据。
- 交易日历仍不完整。
3. 三类快照型产物（Product Artifact / Discovery 候选池 / Coverage Matrix）持续**滞后于数据集**，
   继续扩张前应先决定重跑口径（**Time Observation 必须新 `ROUND_PROFILE` v0.5，不得覆盖 v0.3 / v0.4**）。

**之后（同一序列，不同轮次）**：`Wave 1C 高端装备` →
`Time Observation 重跑（新轮次）` → `Coverage Audit v0.3` → `F7`（`华为汽车` taxonomy 缺口）→
`Structural Analogy Feasibility Check` → Phase 8。

> **红线（不变）**：**不为了增加 Pattern 数量而放松纳入标准**。
> 若扩容后独立结构**仍为 1 个**，那就是诚实结论，**照实报告**。

**在获得授权前不新增功能、不改产品代码、不改 DB 数据（除已明确列入的条目）。**

---

## Explicitly Not Doing

- 新行业 / 新 Rule / 新统计 / 新 Radar / 新预测 / 新 UI redesign / Dashboard / Notification / Backend
- 修改 Research Model v1.0 / v1.1、`schema.sql`、`contracts/`、已有历史研究结论
- 新增数据库实体（含 `theme_cycles` / `theme_relations`）
- 把 Current Candidate 写入 DB / schema / export / contracts；把候选自动升级为 Campaign
- **产品运行时联网**：不抓新闻、不调 LLM、不取实时行情 / 资金 / 情绪数据（保持静态 PWA）
- 自动研究流水线（本阶段只交付协议 + 验证器 + 消费端）
- 相似度分数 / 百分比 / 概率 / 胜率 / 评分榜 / 买卖信号 / 荐股 / 目标价
- 用历史年份数据冒充当前年份状态（look-ahead）
- 把提前观察区做成「预测 / 买入建议 / 历史统计事实」
- **在 `research/` 下放置第二套产品 / 研究副本**；新增第二个 `.git`
- force push · 删除现有测试
