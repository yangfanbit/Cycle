# AGENTS.md — ThreeC 接班入口（项目宪法）

> **任何 AI 模型 / Agent / 协作者接手本仓库时，先读本文件，再读 `docs/PROJECT_STATE.md`。**
> 只有在具体任务需要时，才进一步深入 `research/AGENTS.md` 或产品侧文档。
> **不要为了"了解项目"而通读全部文档** —— 本文件 + PROJECT_STATE 已覆盖 90% 的接手上下文。

---

## 1. 项目初心（最高优先级）

**ThreeC = A股历史机会时间轴 / 历史机会地图。**

这个项目最终**不是**：

- 学术型历史数据库
- 炒股预测软件
- 自动荐股 / 选股工具
- 买卖信号系统
- AI 预测系统

**真正目标**——帮助用户回答：

1. 今天处于一年中的哪个时间位置？
2. 历史上这个时间附近发生过什么主题 / 行情？
3. 这些主题通常如何形成、发展、转折、结束？
4. 有没有提前信号？
5. 为什么启动 / 加速 / 转折 / 结束？
6. 通过历史规律，发现当前值得继续研究的方向。

**用户自己负责**：基本面、技术面、个股选择、入场时机。ThreeC 不做这些。

> **核心价值 = 机会发现，不是交易决策。**
> 每个任务开始前先自问：「这个工作是否提高了历史对比与机会发现能力？」
> 如果只是工程复杂化 —— **不要做**。

---

## 2. 当前阶段

**Wave 1B：Historical Data Expansion — 信息通信历史 Cycle（IMPLEMENTED，2026-09-18）。**
**上一阶段 Wave 1A：电力设备历史 Cycle（IMPLEMENTED，2026-09-17）** 的内容紧随其后。

- **历史侧 Macro Theme 3 → 4**：新建 root **`TH-COMM`「信息通信」**（+ 2 个最小 Sub-theme）。
- **新增 2 个 Historical Theme Cycle**：`comm_5g_infrastructure_2019_2022` · `comm_ai_optical_2023_2025`。
- **修复的断裂**：`CC-2026-OPTICAL-LINK`（高速光互联）首次具备历史可比对象。
- **`theme_family_count` = 4** —— **首次达到 audit 的「≥ 4」门槛**
  （但跨族稳健性检验需重跑 Time Observation 才能判定，**不等于已通过**）。
- **报告**：`docs/HISTORICAL_DATA_WAVE_1B_INFOCOMM_REPORT_2026-09-18.md`。
- **仍受限**：日期核验 **0/24**（Wave 1A/1B 两轮均未增加核验）· `company` / `capital` 的
  **evidence_type** 仍为 0（来源侧 `company_announcement` 已 0 → 3）。

**下一阶段尚未启动**：Wave 1C（高端装备）与 Structural Analogy 仍处于**禁止**状态
（见 `docs/PROJECT_STATE.md`「Next Single Goal」→ 建议先做**日期人工核验**）。

### Wave 1A（已完成）

**历史侧 Macro Theme 2 → 3**：新建 root **`TH-POWER`「电力设备」**（+ 3 个最小 Sub-theme）；
新增 `power_ne_equipment_2020_2022` · `power_grid_uhv_2022_2025`；
修复 `CC-2026-OFFSHORE-WIND` / `CC-2026-COMPUTE-POWER` 的断裂。
**报告**：`docs/HISTORICAL_DATA_WAVE_1A_POWER_EQUIPMENT_REPORT_2026-09-17.md`。

### Primary / Related Macro Theme 规则（Wave 1A 确立，Wave 1B 继承）

`research/research/methodology/macro_theme_primary_related_v0_1.md`：
**每个 Theme Cycle 有且只有一个 Primary Macro Theme**；Related 不增加独立样本数，
且**不写入 `campaign_themes`**（否则 CMTR 判 CONFLICT 并使 `theme_family_id = None`）。

**仓库身份**：单一 Git / 单一根 / 一套 canonical Research / 一套 Product。
`research/` 必须**恰好等于 HEAD 的已跟踪文件集合**；**禁止**在 `research/` 下放置第二套副本或第二个 `.git`。
2026-09-17 已完成 Repository Recovery（`docs/REPOSITORY_RECOVERY_REPORT_2026-09-17.md`）。

### Phase 7.3.2（已完成）

把 Phase 7.2 的观察层从「可运行的研究型原型」推进为**可信、可复现、产品语义清晰**的观察层。
**不扩大研究范围**（不进入 Structural Analogy），**不为凑数量放松纳入标准**。

- **Anchor Verification（P0）**：策略 + 人工覆盖位在
  `research/research/reports/time_observation_anchor_verification_v0_1.json`；
  生成器从 research DB **机械推导**每条锚点的核验状态，写入
  `observations[].verification{status, method, sources, rule, note}` 与 `patterns[].anchor_verification`。
  **核验不改变锚点定义与统计量**；`VERIFIED` 必须带 `sources`（自检 + 解析侧双重把关）。
- **Theme Family**：Pattern 通过 `theme_family_id` 引用既有 Macro Theme（`TH-AUTO` / `TH-PHARMA`）；
  `rule_id` **不再**充当主题身份；缺失时产品回退到 `theme_scope`。
- **Promotion Status**：统一 `promotion_status`（TIMELINE / EXPLORATORY / RESEARCH_ONLY / REJECTED）
  作为展示门槛；`status` / `timeline_eligible` / `timeline_eligibility` 为**兼容输入**。
  - **派生结构门（Phase 7.3.2 / v0.4）**：`lifecycle_rhythm` 的 `derived_from_early_signal` 判定**已进入 Gate** ——
    阶段中心可由「EARLY_SIGNAL 中心 + 中位滞后」解释（残差 ≤ 21 天）者属**派生结果**，降级为 `EXPLORATORY`。
    **只降不升**；`is_derived = None`（无节奏判定 / 缺字段）**不等于**独立，只是**无证据**。
    **派生候选一律保留、不得删除**，来源写入 `derivation_verdict.derived_from_pattern_id`（见 §2 末尾）。
    **口径必须固化在 `ROUND_PROFILES`**（见 §2 末尾「Research 侧口径约定」）。
  - **当前研究结论：独立稳健时间结构 = 1 个**（汽车族 EARLY_SIGNAL 上半年末窗口，TOP-01）。
    `effective TIMELINE_CANDIDATE` 4 → 2（v0.4）。
- **Current Match vs Historical Recall**：`currentMatch`（今天是否在窗口附近）与
  `historicalRecall`（**始终**可回看中心 / 窗口 / 年份案例）分离；
  「当前无匹配」≠「没有历史参考」。
- **未改**：DB / `schema.sql` / canonical export / `contracts/` / Research Model / Campaign 数据 / Timeline 主视觉。

**上一阶段 Phase 7.2：Time-based Observation Layer（IMPLEMENTED）。**

回答「**历史上，一年中的这个时间位置附近，反复出现过值得研究的主题启动 / 观察现象吗？**」
即「**什么时候值得看**」。

- **Research**：`research/research/reports/time_observation_patterns_v0_1.json`（4 条模式 →
  **仅 1 条 `TIMELINE_ELIGIBLE`**）+ 整合报告 + canonical 生成器
  `research/scripts/build_time_observation_patterns.py`（**产物必须由脚本生成，禁止手工编辑 JSON**；
  `--check` 校验逐字节一致）。
- **Product**：`src/data/timeline/timeObservationPatterns.ts`（跨年环形窗口 + 邻近关系 + View Model）·
  `src/components/TimeObservation/TimeObservationLayer.tsx`（Timeline 内极轻一层）·
  `src/components/Timeline/trackPrimitives.tsx`（轨道原语）。
- **语义红线（本层新增）**：只说「历史观察窗口 / 历史复现 X / Y 个观测年份」；
  **不得**把 `historical_ratio` 解释成「今年有 X% 概率」；不得出现概率 / 胜率 / 买卖信号 / 推荐分；
  无可用窗口时**整层不渲染**。
- **边界**：Pattern ≠ Campaign（不修改 Campaign 定义）；与 Current Candidate 独立
  （一个答「什么时候值得看」，一个答「当前出现了什么」）；与「提前观察参考区」并存不可互替。
- **未改**：DB / `schema.sql` / canonical export / `contracts/` / Research Model / Timeline 主视觉。

**上一阶段 Phase 7 / 7.1：Current Research Discovery v0.1（IMPLEMENTED）。**

补齐「**2026 是当前时间、研究数据却截止到 2025**」这一根本缺口：让产品能回答
**「今天这个时间点，我应该去历史资料里研究什么？」**
架构原则：网络与 AI 只出现在**离线研究数据生成端**，不进入运行时。

- **数据协议层** `research/current/`：canonical 数据集（**Phase 7.1 起承载第一轮真实候选 5 条**，
  `snapshot_date = 2026-09-15`）+ JSON Schema + README（含本轮研究记录与拒绝候选池）+
  示例 fixture（**非真实数据**）+ 历史案例叙事标注（带 provenance）。
- **验证器** `research/scripts/validate_current_research.py`：Data / Temporal / Evidence /
  Phase / Similarity / Theme Boundary 六组校验（退出码 0/1）。
- **产品层 5 个纯 View 模块**：`currentCandidate`（协议 / 宽容解析）·
  `currentEvidence`（Evidence Ledger + **Temporal Firewall** + 相位证据矩阵 + 冲突检测 + 状态门）·
  `currentPhaseInference`（透明规则引擎 R0–R8，命中规则 id 可审计）·
  `currentSimilarity`（**Similarity v2：候选 × 历史** + 四问答案）·
  `currentCandidateAdapter`（聚合 + Research Questions + 升级条件核对表）。
- **UI**：Current Lens 内新增克制的「当前研究候选」区（概览 + 就地展开详情 + 诚实空态）；
  `?candidates=example` 可查看示例 fixture。**不改**页面顺序、**不压过** Timeline。
- **四条红线**：① Temporal Firewall（快照后证据隔离；相似度只引用相对快照已结束的案例）·
  ② 禁用单一指标推阶段（相位证据矩阵 8 维）· ③ 状态门**只降不升**（Conflict 永不显示为可升级）·
  ④ 相似度**无百分比**、无证据**不凑数**。
- 候选**不会**自动变成 Campaign；**不写入** DB / schema / export / contracts。

**上一阶段 Phase 6：Product Core v2（IMPLEMENTED）。**
把 Timeline + Historical Same Period + Current Time Lens 升级为**当前研究导航层**
（Current Time Lens v2 + Historical Similar Phase v1 + Macro Theme 聚合接口）。

- Phase 4 Monorepo Integration 已完成：单一仓库 `ThreeC`，单一 Git，保留双方完整历史。
- Phase 5.x 已完成：Current Time Lens v0 → V1.8.1 主题级历史机会视图（IA 重排）→
  V1.8.2 两级详情 + 提前观察参考区 → V1.8.2.1 Formation Anchor 语义修正。
- Phase 5.3–5.5 已完成：**Theme / Campaign 分层模型统一审计**（Macro Theme → Theme Cycle →
  Campaign → Sub-theme + Campaign Independence Gate Q1–Q5）· **Research Model v1.1 方法论补丁**
  （Theme Cycle Pattern A/B/C · Lifecycle Measurement Rule · Gate Q1 Anti-example）·
  **医药健康 Pilot**（首个非汽车 Macro Theme，1 正式 Campaign + 2 Research Candidate）。
- Phase 5.6–5.8 已完成：F-MED-1 跨年年份语义 · **Timeline Entry Identity**
  （`entryId = campaign_id@display_year`）· **Year Coverage Rule**（两源 `years()` 统一）。
- **Phase 6 V2.0 已完成**：
  - **F-MED-6**：Selection 区分展示实例（`entryId`，条目高亮 / focus）与完整历史案例
    （`campaign_id`，Campaign Detail）—— 跨年 Campaign 不再多行同时高亮。
  - **Current Time Lens v2 三层**：A. A股整体环境 = `Unknown`（无整体市场周期模型，
    **绝不**从行业 Campaign 反推大盘）· B. 当前 Theme / Theme Cycle（无当前年份数据 →
    **诚实空态**，不把历史数据伪装成当前状态）· C. **Research Attention** 状态分类
    （`当前值得研究` / `保持观察` / `历史参考`，**不是评分 / 概率 / 信号**）。
  - **Historical Similar Phase v1（Lifecycle Lens）**：按「阶段 → Theme Cycle Pattern →
    Drivers 重叠」检索，Top 3 上限、「高/中/参考」分级（无百分比）、必给「为什么类似」、
    无证据 → 空态不凑数。与「历史同期（Calendar Lens）」并存、不可互相替代。
  - **Macro Theme 聚合接口**（仅 View/Adapter；本轮**不改** Timeline 视觉）。
  - IA（视觉优先级 `Timeline > Current Lens > Similar Phase`）：
    **① Timeline → ② 当前时间研究导航 → ③ 历史相似阶段 → ④ 历史同期（日历）**。
  **不做**预测 / 荐股 / 交易信号 / 评分 / 概率 / 实时数据。

### Research 侧口径约定：Canonical Macro Theme Resolution v1（CMTR v1）

> **任何 Research 脚本判定「对象属于哪个 Macro Theme」时，必须使用唯一实现
> `research/scripts/theme_taxonomy.py`。禁止再写第二份口径。**

```
对象 Macro Theme = themes[] 名称 → DB `themes` 表归一化为 theme_id
                 → 沿 parent_theme_id 上溯至根 → 根节点集合
```

- **已废止 `direct`（Macro Theme 名称字面出现在 `themes[]` 中）口径** ——
  它会把「只登记子主题」的对象误判为无 Macro Theme（实测影响 4 个对象）。
- `status ∈ {RESOLVED, CONFLICT, UNRESOLVED_NAME, NO_THEME}`；
  **未解析名称不静默丢弃**，一律进 `unmatched_theme_names`；`CONFLICT` **不可归属、不得任选其一**。
- **只读**：本解析**不修改**任何数据，**不发明 taxonomy 行**，**不改变**锚点定义与统计量。
- **回归证明方式**（改口径后必须做）：
  `discover_time_observation_patterns.py --round 0.2 --legacy-direct-resolution --check`
  → 与历史轮次产物**逐字节比对**，证明除口径外零行为变化。

**Research 产物换行符约定**：`.gitattributes` 对 `research/**` · `exports/**` · `contracts/**`
声明 `-text`（禁用 EOL 转换）。原因：仓库 `core.autocrlf=true`，否则全新克隆会把 LF 改写为 CRLF，
使所有研究脚本的 `--check` **逐字节校验必然失败**。

> ⚠️ **编辑侧陷阱（实测踩过）**：在 Windows 上用**行内编辑工具**修改 `research/**` 下的文件，
> 会把行尾写成 **CRLF**。因 `.gitattributes` 声明了 `-text`，git **不做归一化** →
> 整个文件会被视为「全部行都改了」，`git diff --stat` 出现虚高的增删行数，
> 并可能破坏该文件的逐字节复现性。
> **改完必须归一化回 LF**，再确认 `git diff --stat` 只显示预期改动行数。
> （`docs/**` 与根 `AGENTS.md` 不受影响 —— 它们由 `core.autocrlf=true` 自动归一化。）

### Research 侧口径约定：轮次档案与派生结构门（Derivation Gate）

> **`discover_time_observation_patterns.py` 的每一轮口径必须固化在 `ROUND_PROFILES` 中。
> 新增轮次必须登记其口径设置，否则该轮产物不可复现、不可比对。**

```python
ROUND_PROFILES = {
    "0.2": {"direct_resolution": True,  "derivation_gate": False},
    "0.3": {"direct_resolution": False, "derivation_gate": False},
    "0.4": {"direct_resolution": False, "derivation_gate": True},   # 当前默认
}
```

- `--round X` **一并恢复该轮口径**（`--legacy-*` 开关保留给显式实验）。
- **未知轮次必须 `SystemExit`**，**不得**静默降级为默认口径。
- **改口径后的强制回归**（三选三，全部必须 PASS）：
  ```bash
  python research/scripts/discover_time_observation_patterns.py --check                                          # 当前轮逐字节自洽
  python research/scripts/discover_time_observation_patterns.py --round 0.3 --legacy-no-derivation-gate --check  # 复现 v0.3
  python research/scripts/discover_time_observation_patterns.py --round 0.2 --legacy-direct-resolution   --check  # 复现 v0.2
  ```
  **`--check` 必须在所有编辑完成后重跑** —— 中途 PASS 不是最终证据
  （产物里的**说明性文本**也是产物内容，改文案同样会破坏逐字节一致）。
- **轮次归因**用 `research/scripts/compare_time_observation_rounds.py --from X --to Y`（只读）：
  它**严格区分「字段新增（结构性，by design）」与「字段值变化（实质性）」**，
  避免把新增字段误报成「结论变化」。

**派生结构门（Phase 7.3.2 / v0.4）**：`lifecycle_rhythm` 的 `derived_from_early_signal` 判定**已进入 Promotion Gate**。

```
拟合中心 = EARLY_SIGNAL 中心 + 该阶段相对 EARLY_SIGNAL 起点的中位滞后
残差 ≤ 21 天 → derived_from_early_signal = true → 该阶段时间位置不含额外信息
```

- **三值判定，只降不升**：`True` → 降级 `EXPLORATORY`；`False` → 不动作；
  `None`（存在无节奏判定的阶段 / 缺字段）→ **不下结论、不动作**。
- **本门从不主动断言「非派生」** → `False` 可以为 0 条。**`None` ≠ 独立**，只是「无证据」。
- **缺字段 / `null` 一律视为 `None`（无判定）**，**不得**降级为 `False` ——
  `False` 是肯定性断言；把「缺字段」当 `False` 等于把「无证据」伪装成「已证清白」。
- **降级落点必须是 `EXPLORATORY`，不得用 `RESEARCH_ONLY`** ——
  派生候选数值门槛**已通过**，缺的是「独立性」（`EXPLORATORY` 的定义）；
  `RESEARCH_ONLY` 描述的是「集中度 > 0.60 / 样本不足」这类**数值弱**，语义不符。
- **派生候选一律保留、不得删除**，来源必须写入 `derivation_verdict`：
  `is_derived` / `derived_from_pattern_id`（派生自哪个候选）/ `derived_from_stage` /
  `stage_verdicts` / `reason`（为何不下结论）/ `note`（为何判定为派生，含滞后与残差数字）。
  自检强制来源引用必须指向**真实存在的候选**。
- **只对有节奏分析的 scope 生效**（当前仅 `rule_auto_summer` / `TH-AUTO`）；
  其余 scope **本门无法下结论** —— 报告与产品文案**不得**把 `None` 读作「独立规律」。
- **阈值 21 天为既有设定**（`lifecycle_rhythm` 早已使用）；**调整它属规则变更，必须单独留痕**。
- **回归测试**：`research/scripts/test_derivation_gate.py`（6 组，含 4 种退化输入 + 反向对照）。
  注意 `is_derived = False` 在真实数据中为 0 条 → **该分支只能用合成输入测**，否则等于没测。

**研究结论口径（不变）**：独立稳健时间结构 = **1 个**（汽车族 EARLY_SIGNAL 上半年末窗口）。
**不为了增加 Pattern 数量而放松纳入标准**（不降 N、不拓宽窗口、不弱化 LOO、不制造 Pattern）。

阶段全景见 `docs/ROADMAP.md`。下一个唯一目标见 `docs/PROJECT_STATE.md`「Next Single Goal」。

---

## 3. 产品 / Research 边界

| | Product（Cycle） | Research（Cycle-Research） |
|---|---|---|
| 位置 | 仓库根（`src/`、`public/`、`package.json`） | `research/` |
| 职责 | Timeline UI、PWA、历史对比、机会发现呈现 | 数据收集、Source、Evidence、Market Data、Campaign、Lifecycle、Drivers、Research Export |
| 不做 | 数据生产、改 Research Model | UI、Timeline 排版、PWA、前端交互 |
| 语言 | TypeScript / React / Vite | Python（标准库 sqlite3） |

**两个逻辑模块，一个项目目标。** 边界必须清晰：Research 只产出数据，Product 只消费数据。

---

## 4. 目录结构

```
ThreeC/
├─ .git/                       ← 唯一 Git
├─ .gitignore
├─ AGENTS.md                   ← 本文件（接班入口）
├─ README.md
├─ package.json / tsconfig.json / vite.config.ts
│
├─ src/                        ← Product：前端源码
│   ├─ components/             ← Timeline（第一视觉）/ SamePeriodView（Calendar Lens）/ CurrentTimeLens（②研究导航 + 当前研究候选）/ HistoricalSimilarPhase（③Lifecycle Lens）/ CampaignDetail（Level 2 完整历史案例）/ OpportunityRadar（未引用，待清理）…
│   ├─ data/
│   │   └─ timeline/           ← Timeline Adapter（消费 exports/）+ preObservation.ts（提前观察区，纯 UI 层）
│   ├─ models/                 ← 核心数据模型（禁擅改）
│   └─ utils/
├─ public/
├─ index.html
│
├─ docs/                       ← 项目级文档
│   ├─ PROJECT_STATE.md        ← 接班必读②
│   ├─ PRODUCT_PURPOSE.md
│   ├─ ROADMAP.md
│   ├─ CHANGELOG.md            ← 统一变更记录
│   ├─ THEME_CAMPAIGN_MODEL_AUDIT.md ← Theme/Campaign 分层模型审计（Macro Theme→Theme Cycle→Campaign→Sub-theme）
│   └─ (Cycle 原有) PRODUCT.md / DATA_MODEL.md / DATA_GOVERNANCE.md /
│        HISTORICAL_VALIDATION.md / ARCHITECTURE.md / UI_SPEC.md
│
├─ exports/                    ← ★ Research → Product 唯一交换目录
│   └─ timeline_export_v1.json ← ★ 唯一 canonical export
├─ research/current/           ← ★ Phase 7/7.1：Current Candidate 数据集（经 @current alias 消费；5 条真实候选）
├─ research/research/reports/  ← ★ Phase 7.2：Time Observation Pattern canonical Artifact
│                                 （经 @observation alias 消费；_seasonal_analysis/ 为探索性脚本，非产品依赖）
├─ contracts/
│   └─ timeline_export_v1.md   ← 跨模块接口契约
│
├─ research/                   ← Research 子系统（原 Cycle-Research 仓库）
│   ├─ AGENTS.md               ← Research 职责书
│   ├─ README.md               ← 原 Cycle-Research README
│   ├─ database/cycle_research.db  ← 研究数据库（提交 Git，见 §11）
│   ├─ schema/schema.sql       ← 冻结（禁改）
│   ├─ data/market/            ← raw / normalized 行情 CSV
│   ├─ exports/cycle_verified_candidates.json
│   ├─ scripts/                ← Python 流水线
│   └─ research/               ← 研究产物：annual / batch / c2 / methodology / promotion / summary / templates
│
├─ data/                       ← Product 侧核验数据（raw / candidate / verified / validation）
└─ tests/
```

> 注：`research/research/` 是历史既有嵌套（Research 仓库内原本就有 `research/` 产物目录），
> 迁移时**刻意保留**该相对结构以维持零语义漂移与历史可追溯，不是冗余。

---

## 5. 数据流（单向，禁止手工 Copy）

```
research/                      Python 研究流水线
    ↓  Research scripts
exports/timeline_export_v1.json   ← ★ 唯一 canonical
    ↓  Cycle Timeline Adapter（src/data/timeline/timelinePreview.ts → timelineAdapter.ts）
Timeline UI
```

**禁止**：Research → 手工 Copy → Cycle 内 JSON。
**禁止**：在仓库内长期存在两个 canonical JSON 副本。

---

## 6. Export Contract

- 唯一版本：`timeline_export_version = "1.0"`。
- 契约正文：`contracts/timeline_export_v1.md`。
- 顶层 11 字段白名单：`contract / timeline_export_version / generated_at / source_commit / project / rules / signals / campaigns / research_candidates / events / securities`。
- 守门人：`research/scripts/validate_timeline_export.py`。
- **Schema 变更必须同时更新三处**：`contracts/` + Research exporter + Cycle adapter。
  任何一侧不得单方面改变。

---

## 7. 数据状态（严格分层，禁止越级）

```
Source ≠ Evidence ≠ Rule ≠ Historical Fact ≠ Verification ≠ Prediction
```

**Research 研究状态**（大写）：`RAW / PROVISIONAL / CONFLICT / INSUFFICIENT / VERIFIED`
**生产状态**（小写，Cycle 消费）：`verified / provisional / conflict / preview`

- `PROVISIONAL ≠ VERIFIED`。PROVISIONAL 可用于预览，**不得**自动进入 verified。
- Research Candidate（`RC-` 前缀）**永不**映射为 verified；与正式 Campaign 是**并列**来源，非升级关系。
- 生产 `verified` 数据位于 `data/verified/`；前端 `?preview=1` 消费 `exports/`，默认生产模式消费 `data/verified/`。

---

## 8. 禁止事项（红线）

**数据与模型**

- 修改 Research Model v1.0
- 新增 ThemeCycle / CampaignRelation schema 或数据库实体
- 修改 `research/schema/schema.sql`
- 修改 2018–2025 已有历史研究结论（Campaign / Theme / Evidence / Market Data / Lifecycle / Drivers）
- 让 PROVISIONAL 自动进入 verified；把 Candidate 当 confirmed
- 丢 Git 历史 / 丢 Research 数据
- 把 **Current Candidate** 写入 DB / schema / export / contracts，或让它自动升级为 Campaign
- 用快照之后（`source_date > snapshot_date`）的证据参与当前判断 / 相似度（look-ahead）
- 手工编辑 **Time Observation Pattern** 产物（必须由 `build_time_observation_patterns.py` 生成）
- 把 **Time Observation Pattern** 写成 DB / schema / export / contracts，或当成 Campaign / Theme
- 用价格类指标（涨停 / 涨幅 / 成交额）定义「启动观察锚点」—— 锚点只能是 Early Signal / Formation / Campaign.start
- 把「历史复现率」表述为未来概率（**只能**写「历史样本中 X / Y 个观测年份」）
- **伪造锚点核验**：状态标 `VERIFIED` 却给不出来源（必须能指向 DB 观测行 / evidence_id / source_id / 事件台账）
- 把「核验通过」表述成「规律有效 / 高可信预测」；核验只描述**证据支持**，不证明规律
- 改动锚点核验元数据后**不重跑生成器**（核验结果必须由 `build_time_observation_patterns.py` 产出）
- 手工编辑 Time Observation Pattern 产物 / 核验产物（两者都必须由脚本生成）
- 为凑 Pattern 数量而降低纳入标准（N < 5、放宽窗口、合并年份、给 RESEARCH_ONLY 强行 TIMELINE）
- 产品运行时联网（抓新闻 / 调 LLM / 取实时行情资金情绪）—— 网络与 AI 只允许在离线研究数据生成端

**产品**

- 实时行情 / 资金流 / 异动监控
- AI 预测、确定性未来预测、"必涨 / 必跌"
- 买入 / 卖出 / 建仓 / 清仓建议；股票推荐；自动交易信号
- 伪造胜率 / 季节性评分等量化结论
- 用户登录 / 权限系统 / 后端 / 自动爬虫

UI 文案中「买入 / 卖出 / 建仓 / 清仓 / 推荐」只允许出现在**否定性免责声明**中。

---

## 9. 测试策略

**Product（Node）**

```bash
npm test          # Vitest，当前 395 项
npx tsc -b        # 类型检查
npm run build     # 生产构建
```

**Research（Python，标准库 sqlite3）**

```bash
cd research
python scripts/validate_db.py
python scripts/validate_timeline_export.py
python scripts/validate_batch_research.py
python scripts/validate_promotion_manifest.py
python scripts/check_doc_schema_consistency.py
python scripts/validate_current_research.py      # Phase 7：Current Candidate 数据集（Data/Temporal/Evidence/Phase/Similarity/Theme Boundary）
python scripts/build_time_observation_patterns.py --check   # Phase 7.2：Time Observation Pattern 产物可复现性（逐字节一致）
```

**Integrity**

```bash
python scripts/validate_monorepo_integrity.py   # 仓库结构 / canonical 唯一性 / 数据流
```

改动后必须运行相关测试；不得删除现有测试。

---

## 10. 修改规则

1. 先搜索是否已有实现；**优先修改已有实现**，不重复造轮子。
2. 最小修改原则：不做「为了更优雅」的重构；不做「未来可能需要」的预留。
   "未来可能需要" 记入 `docs/ROADMAP.md`，不写进代码。
3. 不擅自重构核心数据模型（`src/models/`）或改变产品定位（§1）。
4. 若任务与本文件冲突：**优先遵守本文件**，在最终报告中明确指出冲突点，等待确认。
5. 每轮修改必须说明：改了什么、为什么改、为什么属于必要修改。

---

## 11. Git 规则

- **唯一 Git**：仓库根 `.git`。`research/` 内**不再**有独立 `.git`。
- **唯一远程**：`origin` → `https://github.com/yangfanbit/Cycle.git`。不新建第三个仓库。
- `research/database/cycle_research.db` **继续提交 Git**（Research 明确依赖可回查数据库）；
  不因通用最佳实践自动忽略 SQLite。
- 禁止 `force push`。若遇无法解决的问题，先停止并报告。
- 默认普通 fast-forward push。
- 提交前确认：工作树干净、`origin` 正确、`main` 正确、历史完整。

**Research 历史追溯**：`git log -- research/` 可回溯原 Cycle-Research 全部历史提交
（经 `git subtree` 并入，原始 author / date / message 保留）。

---

## 12. 当前唯一下一目标

> 见 `docs/PROJECT_STATE.md`。

**人工复核 TOP-01 剩余的 5 个 UNKNOWN 锚点（离线研究轮，非本仓库代码任务）。**

Phase 7.3 已完成「可由仓库资料自动确认」的部分：TOP-01 **2 / 7 已核验**
（2022-04-27 = 行情观测；2025-06-22 = 同日事件台账 Tier 2）。剩余 5 个保持 `UNKNOWN`，
其中 **2023-06-12 / 2024-06-11 有 Tier ≤2 证据在描述中以词边界提到该日期**（生成器已在
`verification.note` 中标出候选证据）—— 这两个优先人工复核；2019-08-15 / 2020-06-01 /
2021-06-01 仓库内仅有 Tier 3/4 线索或间接证据。

人工核验结果写入 `research/research/reports/time_observation_anchor_verification_v0_1.json`
的 `overrides`（写 `VERIFIED` 时必须提供 `source`，否则生成器自检失败），然后重跑生成器。
**理由**：核验是观察层可信度的天花板 —— 它决定「探索性」标记能否去掉，也决定下一阶段
（Phase 8 Structural Historical Analogy）有没有可靠底座。

核验后如锚点日期变化，必须重新运行：

```bash
python research/scripts/build_time_observation_patterns.py            # 重新生成 Artifact
python research/scripts/build_time_observation_patterns.py --check    # 确认可复现
```

**在此之前不新增功能、不新增行业、不改模型、不改产品代码。**

用户视觉 / 交互 Review（Phase 7.2）可同时进行：

1. 「时间型观察层」是否足够克制（一条薄带、不抢 Campaign 主体）？
2. 今天落在窗口内时，「当前位于历史观察窗口」是否被理解成**日历位置**而不是市场状态判断？
3. 「历史复现：5 / 7 个观测年份」是否不会被误读成「今年 71% 概率」？
4. 点击年份进入 Campaign Detail 的闭环是否自然（是否还需要别的东西）？
5. 「探索性」标记与限制说明是否足够显眼，让人不会把它当成熟统计结论？
6. 不在窗口时的空态（「当前没有发现处于历史时间观察窗口的模式」）是否读得懂？

上一轮（Phase 7 / 7.1）已完成的 Review 项：

1. 「当前研究候选」区是否克制（不抢 Timeline）？
2. 空态是否读得懂「系统在诚实地说不知道」，而不是「系统没做完」？
3. `?candidates=example` 的示例是否清楚表达了「这是协议示例、不是真实研究对象」？
4. 详情里的「为什么它现在仍是 Candidate」核对表，是否让你更想去看证据而不是看结论？
5. Temporal Firewall（已隔离证据）是否被理解为「不引用未来信息」的保证？
6. Historical Similar Cases 的「四问」是否比「历史涨了多少」更有用？
