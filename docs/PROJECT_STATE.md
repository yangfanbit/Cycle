# PROJECT_STATE.md — ThreeC

> 接班必读②（读完根 `AGENTS.md` 后读本文件）。
> 一页到两页，覆盖接手所需的全部状态。**不要**为理解项目而通读其他文档。

---

## Project Purpose

**ThreeC = A股历史机会时间轴 / 历史机会地图。**

让用户回答：今天在一年中的什么位置 → 历史上这个时间发生过什么 → 主题如何形成 / 发展 /
转折 / 结束 → 有没有提前信号 → 为什么启动 / 加速 / 转折 / 结束 → **现在应该去研究什么**。

**核心价值 = 机会发现，不是交易决策。** 用户自己负责基本面 / 技术面 / 选股 / 入场时机。
详见 `docs/PRODUCT_PURPOSE.md`。

---

## Current Phase

**Phase 7.3：Observation Credibility & Coverage（IMPLEMENTED）。**
把 Phase 7.2 的 Time-based Observation Layer 从「可运行的研究型原型」推进为
**可信、可复现、产品语义清晰**的观察层。**不扩大研究范围**（不进入 Structural Analogy）。

### 已完成（承自 7.2）

- Time-based Observation Layer 落地：`TOP-01` 进入 Timeline（N=7 / 中心 06-11 / 窗口 05-27 ~ 06-26）
- Current Match（当前时间匹配）与 Historical Recall（历史观察回溯）**分离**
- canonical generator（deterministic，`--check` 逐字节一致）

### 本阶段目标（7.3）

| 项 | 内容 |
|---|---|
| **Anchor Verification** | 可复用的锚点核验结构：`research/research/reports/time_observation_anchor_verification_v0_1.json` 声明核验策略（R1–R5）+ 人工覆盖位；生成器从 research DB（`campaign_date_observations` / `evidences` + `sources.tier` / `events`）**机械推导**每条锚点的核验状态。**核验不改变锚点定义**。 |
| **Theme Family mapping** | Pattern 通过稳定的 `theme_family_id`（复用既有 Macro Theme：`TH-AUTO` / `TH-PHARMA`）引用主题族；`rule_id` **不再**充当主题身份。缺失时产品回退到 `theme_scope`。 |
| **Promotion status normalisation** | 新增统一字段 `promotion_status` ∈ `TIMELINE / EXPLORATORY / RESEARCH_ONLY / REJECTED`（authoritative）；旧的 `status` / `timeline_eligible` / `timeline_eligibility` 保留为**兼容输入**，生成器自检保证一致。 |

**当前核验结果（诚实）**：TOP-01 **2 / 7** 个锚点完成仓库内证据核验
（2022-04-27 = 行情观测；2025-06-22 = 同日事件台账 Tier 2）；其余 5 个保持 `UNKNOWN`
（其中 2023-06-12 / 2024-06-11 有 Tier ≤2 证据在描述中以词边界提到该日期，但未作为独立日期证据登记）。
→ 产品继续按「**探索性观察**」呈现，**不得**升级为「高度可信」。

**上一阶段 Phase 7.2：Time-based Observation Layer（IMPLEMENTED）。**
在「今天该研究什么」（Phase 7 / 7.1）之外，进一步回答
**「历史上，一年中的这个时间位置附近，反复出现过什么」** —— 即「**什么时候值得看**」。

完整交付：

- **Research**：`research/research/reports/time_observation_patterns_v0_1.json`
  （4 条模式：**1 条 `TIMELINE_ELIGIBLE`** / 2 条 `RESEARCH_ONLY` / 1 条 `REJECTED`）·
  整合报告 `Time_Observation_Pattern_Integration_v0_1.md` ·
  canonical 生成器 `research/scripts/build_time_observation_patterns.py`（可复现，`--check` 逐字节校验）
- **Product**：`src/data/timeline/timeObservationPatterns.ts`（宽容解析 + **跨年环形窗口** +
  邻近关系 + View Model）· `src/components/TimeObservation/TimeObservationLayer.tsx`（Timeline 内极轻一层）·
  `src/components/Timeline/trackPrimitives.tsx`（轨道原语，避免第二套月份网格实现）
- **语义纪律**：只讲「历史观察窗口 / 历史复现」；**不出现**概率 / 胜率 / 买卖信号；
  无可用窗口时**不渲染本层**
- **未改**：DB / `schema.sql` / canonical export / `contracts/` / Campaign 定义 / Research Model /
  Timeline 主视觉

**上一阶段 Phase 7 / 7.1：Current Research Discovery（IMPLEMENTED + 第一轮真实数据已落地）。**
Phase 7 v0.1 补齐了「2026 是当前时间、研究数据却截止到 2025」这一根本缺口；
**Phase 7.1 把协议第一次接入真实研究数据**（`snapshot_date = 2026-09-15`，5 个 `CC-*` 候选），
使产品能真正回答 **「今天这个时间点，我应该去历史资料里研究什么？」**

### 架构（网络与 AI 只在**离线研究数据生成端**，不进入运行时）

```
Web / AI Research（离线：人工 / 脚本 / AI）
        ↓
research/current/current_candidates.json      ← 静态研究 Artifact（可验证、可回溯）
        ↓
src/data/timeline/currentCandidate*.ts        ← Product Adapter（纯 View 层）
        ↓
Current Time Lens · 当前研究候选
        ↓
Historical Similar Phase（Similarity v2：候选 × 历史）
        ↓
Research Questions（研究方向）
```

### 交付

1. **数据协议层** `research/current/`
   `current_candidates.json`（canonical，**第一轮真实候选 5 条**：`snapshot_date = 2026-09-15`）· `schema.json`（JSON Schema 子集）·
   `README.md`（协议 + 如何新增候选）· `fixtures/example_candidates.json`（**示例，非真实数据**）·
   `narrative_annotations.json`（历史案例的结构化叙事标注，逐条带 provenance）。
2. **验证器** `research/scripts/validate_current_research.py`
   6 组校验：Data / Temporal / Evidence / Phase / Similarity / Theme Boundary。退出码 0/1。
3. **产品层（5 模块，纯 View）**
   - `currentCandidate.ts` —— 协议 / 类型 / 标签 / 宽容解析
   - `currentEvidence.ts` —— **Evidence Ledger + Temporal Firewall** + 相位证据矩阵 + 冲突检测 + 状态门
   - `currentPhaseInference.ts` —— **透明规则引擎**（R0–R8，命中规则 id 可审计）
   - `currentSimilarity.ts` —— **Similarity v2**（候选 × 历史）+ Research Questions
   - `currentCandidateAdapter.ts` —— 聚合为 UI View 模型
4. **UI** `CurrentTimeLens` 内新增克制的「当前研究候选」区（概览 + 就地展开详情），
   **不改**页面顺序、**不压过** Timeline。
5. `?candidates=example` 查询参数可查看示例 fixture（页面顶部有强提示「非真实研究数据」）。

### 五个核心机制

- **Temporal Firewall**：证据必须带 `source_date` / `event_date`；`> snapshot_date` 的必须标
  `AFTER_SNAPSHOT`，且**不得参与**阶段推断 / 状态判定 / 相似度。相似度侧只允许
  **`end <= snapshot_date`**（相对快照已完整结束）的历史案例作参照 —— 否则会引用未来信息。
- **Phase Evidence Matrix**：8 个维度（叙事 / 政策 / 产业 / 市场 / 资金 / 广度 / 公司 / 新增信息边际）。
  其中 3 个由研究声明，5 个由证据 `source_type × strength × direction` **确定性派生**；
  逐维标注来源。**禁用** `涨幅 > X ⇒ EXPANSION` 这类单一指标逻辑。
- **Research Attention Gate 只降不升**：无可用证据 → 不高于候选；有冲突 → 不高于保持观察；
  阶段 UNKNOWN → 不高于保持观察。**Conflict 候选永远不可能显示为可升级状态**。
- **Similarity v2 四层**：阶段（历史案例**曾经历**该阶段 30 / 曾经历相邻 15）
  → Theme Cycle Pattern（12/5）→ Drivers 重叠（×5）→ **Narrative 结构**重叠（×4）。
  Top 3 上限、**无百分比**、「高相似 / 中相似 / 参考案例」、必给「为什么类似」、
  无证据 → 空态**不凑数**。UI 明示：相似的是**阶段与结构**，不是未来走势。
- **Research Questions**：由模板 + 现有证据确定性生成（缺哪个维度就问哪个维度、
  有相似案例就问「该阶段历史分歧」、有冲突就问「如何交叉验证」）。是**研究问题**，不是买卖问题。

**不做**预测 / 荐股 / 交易信号 / 评分 / 概率 / 实时数据 / 后端 / 在线 API。

---

## Completed

| Phase | 内容 | 状态 |
|---|---|---|
| Phase 1 | Research Model v1.0（冻结） | ✅ |
| Phase 2 | Historical Data Production v1（2018–2025 批量研究） | ✅ |
| Phase 3 | Timeline MVP（+ Conflict Visual / Phase Window / Drivers / SamePeriod / Research Export Adapter / Preview-Production 隔离） | ✅ |
| Phase 4 | Monorepo Integration + Handoff Infrastructure | ✅ |
| Phase 5 | **Current Time Lens v0**（今天入口：时间定位 → 历史同期 → 历史阶段映射 → 可能驱动） | ✅ IMPLEMENTED |
| Phase 5.1 | **V1.8.1 主题级历史机会视图**（IA 重排：Timeline 第一视觉 + 历史同周期主题行 + Lens 降级） | ✅ IMPLEMENTED |
| Phase 5.2 | **V1.8.2 Timeline Detail UX + 提前观察区**（两级详情 / Inline Summary / Bottom Sheet / Pre-observation Window） | ✅ IMPLEMENTED |
| Phase 5.2.1 | **V1.8.2.1 Pre-observation Semantic Fix**（Formation Anchor 优先级 / Early Signal 与 Formation 分离 / 文案改「提前观察参考区」/ 视觉层级降序） | ✅ IMPLEMENTED |
| Phase 5.3 | **Theme / Campaign 分层模型统一审计**（Macro Theme → Theme Cycle → Campaign → Sub-theme；Campaign Independence Gate Q1–Q5；`docs/THEME_CAMPAIGN_MODEL_AUDIT.md`） | ✅ IMPLEMENTED |
| Phase 5.4 | **Research Model v1.1 方法论补丁**（Theme Cycle Pattern A/B/C · Campaign Lifecycle Measurement Rule · Gate Q1 Anti-example） | ✅ IMPLEMENTED |
| Phase 5.5 | **医药健康 Pilot**（Theme Cycle Discovery v0.1 → Campaign Boundary Decision v0.1 → 最小数据集接入：1 正式 Campaign + 2 Research Candidate + 8 行情序列） | ✅ IMPLEMENTED |
| Phase 5.6 | **V1.8.4 F-MED-1** 跨年 Campaign 年份语义修复（明细 `year` = 所属展示年份） | ✅ IMPLEMENTED |
| Phase 5.7 | **V1.9.0 Timeline Entry Identity**（`entryId = campaign_id@display_year`；展示实例 ≠ Campaign 选择） | ✅ IMPLEMENTED |
| Phase 5.8 | **V1.9.1 Timeline Year Coverage Rule**（两源 `years()` 统一为 start→end 连续） | ✅ IMPLEMENTED |
| Phase 6 | **V2.0 Product Core v2**（F-MED-6 Selection 身份分离 · Current Time Lens v2 三层 · Research Attention Gate v1 · Historical Similar Phase v1 · Macro Theme 聚合接口 · IA 重排） | ✅ IMPLEMENTED |
| Phase 7 | **Current Research Discovery v0.1**（`research/current/` 数据协议 + 验证器 · Temporal Firewall · Phase Evidence Matrix 与透明规则引擎 · Similarity v2（候选 × 历史）· Research Questions · 「当前研究候选」UI + 诚实空态） | ✅ IMPLEMENTED |
| Phase 7.1 | **First Real Current Research**（`snapshot 2026-09-15`：5 个真实候选 / 39 条证据 / 0 条快照后证据 · 拒绝候选池 5 条 · 跨会话并行轮次裁决） | ✅ IMPLEMENTED |
| Phase 7.2 | **Time-based Observation Layer**（`time_observation_patterns_v0_1.json`：4 条模式 → **1 条进入 Timeline** · canonical 生成器（可复现）· Adapter 跨年环形窗口 · Timeline 内极轻观察层 + Level 2 摘要） | ✅ IMPLEMENTED |

---

## Current Architecture

```
ThreeC/  (单一 Git, origin = yangfanbit/Cycle)
├─ src/                Product：React + TS + Vite (Timeline UI / Adapter / models)
├─ data/               Product 侧核验数据（verified 层当前为空）
├─ exports/            ★ canonical timeline_export_v1.json
├─ contracts/          timeline_export_v1.md（接口契约）
├─ research/           Research 子系统（Python + SQLite）
│   ├─ database/cycle_research.db   （提交 Git）
│   ├─ schema/schema.sql            （冻结）
│   ├─ scripts/                     （Python 流水线）
│   ├─ current/          ★ Phase 7：Current Candidate 数据协议（canonical + fixtures）
│   └─ research/                    （研究产物）
├─ docs/               项目级 + 产品级文档
└─ tests/
```

- **History migration**：Cycle 为根（原 11 commits），Cycle-Research 经
  `git subtree add --prefix=research` 并入（原 28 commits）。共 40 commits，
  双方原始 author / date / message 保留。
- **前端消费路径**：三个静态 Artifact，均为「Research 生成 → Product 只读消费」，无运行时网络请求：
  - `@exports/timeline_export_v1.json` —— 历史研究数据（alias → `exports/`）
  - `@current/current_candidates.json` —— **Phase 7** Current Candidate 数据集（alias → `research/current/`）
  - `@observation/time_observation_patterns_v0_1.json` —— **Phase 7.2** Time Observation Pattern
    （alias → `research/research/reports/`；该目录下的探索性脚本**不是**产品依赖）

---

## Research Status

- Research Model **v1.0 Frozen**；`schema.sql` 冻结（17 表 / 125 字段）。
- 2018–2025 八年度研究完成：**8 个正式 Campaign + 1 个 2018 反例年份**；医药健康 **+1 正式 Campaign**。
- 研究状态分布：`PROVISIONAL 9 / CONFLICT 1`。
- Research Candidates：`RC-2023-HUAWEI`、`RC-2024-SECONDARY`、`RC-2020-PANDEMIC`、`RC-2021-TCM`
  （永不 verified）。
- **★ Canonical Macro Theme Resolution v1（CMTR v1，2026-09-16）**：
  对象 Macro Theme = `themes[]` 名称 → DB `themes` 表归一化 → 沿 `parent_theme_id` 上溯至根。
  **唯一实现** = `research/scripts/theme_taxonomy.py`（`discover_time_observation_patterns.py`
  与 `audit_historical_coverage.py` 共用）。**已废止 `direct`（字面名称匹配）口径**。
  - 实测：`TH-AUTO` 7 → **9** 成员；`TH-PHARMA` 1 → **3** 成员。
  - 解析状态：`RESOLVED` 12 / `CONFLICT` 0 / `UNRESOLVED_NAME` 1（`RC-2023-HUAWEI` 的「华为汽车」，
    即 DEFER 项 `F7`）/ `NO_THEME` 0。
  - 收益：v0.2 的 5 对「口径脆弱」**全部归零**；两种 scope 口径下的 TOP-01 变体**收敛为同一样本集合**。
  - 边界：`theme_taxonomy.py` **只读** `themes` 表；**不发明 taxonomy 行**，未解析名称一律显式上报。
- **★ 派生结构门（Derivation Gate，v0.4，2026-09-16）**：`lifecycle_rhythm` 的
  `derived_from_early_signal` 判定**已进入 Promotion Gate**（此前只存在于研究报告里）。
  - 判据（阈值 21 天沿用既有设定，**未调整**）：阶段中心 ≈ EARLY_SIGNAL 中心 + 中位滞后（残差 ≤ 21 天）
    → 该阶段时间位置**不含超出 EARLY_SIGNAL 的额外信息** → 不得作为独立规律。
  - **三值判定，只降不升**：`True` → 降级 `EXPLORATORY`；`False` → 不动作；
    `None`（存在无节奏判定的阶段）→ **不下结论、不动作**。本轮 `False` = 0 条
    （本门**从不主动断言「非派生」**）。
  - 口径固化为 `ROUND_PROFILES`：`--round X` 一并恢复该轮口径 → v0.2 / v0.3 / v0.4 三轮产物**逐字节可复现**；
    未知轮次**显式 FAIL**。
  - **实测**：`effective TIMELINE_CANDIDATE` **4 → 2**；有效独立结构 **2 → 1**；
    实质性变化仅 2 条候选（`TOPC-004` / `TOPC-021`，均 MAIN_RISE）。
  - **★ 派生范围**：两个有节奏分析的 scope 各 **7 个阶段全部派生**（`THEME_FORMING` … `MAIN_END`）
    → **EARLY_SIGNAL 是本数据集里唯一的时间信息来源**，其余阶段皆为下游回声。
  - 边界：**规则变更，非数据变更**；未改 DB / export / contracts / Product Artifact。
- 结论：**"6–8 月汽车" = 历史观察窗口（Historical Observation Window），
  Partially Supported，非固定买入窗口**。
  （见 `research/research/summary/auto_2018_2025_final_review.md`）
- **Current Candidate（Phase 7）是独立于上述三者的第四类对象**：研究对象候选，
  不进入 `campaigns` 表、不进入 export、命名空间 `CC-`（fixture 用 `FX-`）。

---

## Product Status

- **页面 IA（V2.0）**：① **Timeline（第一视觉）** → ② **当前时间研究导航（Lens v2 + 当前研究候选）**
  → ③ **历史相似阶段（Lifecycle Lens）** → ④ **历史同期（Calendar Lens）**。
- **Timeline 永远保持第一视觉（V1.8.2 硬约束）**：点击主题 / Campaign **不遮挡** Timeline；
  无大型 modal 覆盖、无永久右侧大面板压缩。
- **两级详情（V1.8.2）**：
  - **Level 1 Inline Summary**：点击主题行 → **就地**展开摘要，**不离开主页面**。
  - **Level 2 Full CampaignDetail**：仅点「查看完整历史案例」才打开；桌面为右侧浮层；**移动端为 Bottom Sheet**。
- **提前观察参考区（V1.8.2 / V1.8.2.1）**：`historicalPreObservationDays = 30`（**UI / Research browsing buffer**）。
  语义 = 「主题正式形成前可开始关注的时间缓冲区」；**不是**预测 / 买入建议 / 未来信号 / 历史统计事实。
  - **Formation Anchor**：`THEME_FORMING.start → BROAD_CONFIRMATION.start → Campaign.start → null`；
    **禁止**取 lifecycle 最早 stage（会把 EARLY_SIGNAL 误认为形成）。
  - 视觉层级 `Campaign(0.95) > Early Signal(0.5/z-1) > 参考区(0.4/z-0)`。
  - 文案统一「**提前观察参考区**」（禁止「买入区 / 布局区 / 信号区」）。
- **历史同周期主题**（`SamePeriodView` = **Calendar Lens**）：一行 = 一个主主题；同主题多条独立行情**不合并**，
  RC 保留 badge、状态不升级；仅**重大冲突**（>10 天）显示 ⚠。
- **Current Time Lens v2（V2.0）**：三层 A（A股整体环境 = `Unknown`）/ B（当前 Theme · Theme Cycle，
  无当前年份数据 → 诚实空态）/ C（Research Attention 状态分类）。
- **Historical Similar Phase v1（V2.0）**：历史 × 历史；与 ④ Calendar Lens 并存、不可互相替代。
- **Macro Theme 聚合接口（V2.0）**：`macroTheme.ts`，**未改** Timeline 视觉。
- **Phase 7 · 当前研究候选**（`CurrentCandidateSection`）：
  - 概览：名称 · 阶段 · 有效状态 · 证据充分度 · 相似案例数 ·（若有）已隔离证据数 · 展开。
  - 详情（就地展开）：Why now → Current Evidence（含**已隔离证据单列**）→ Possible Drivers →
    Estimated Phase（矩阵逐维来源 + 命中规则）→ Historical Similar Cases（四问 + 为什么类似 +
    可跳转历史案例）→ What to research next → Uncertainty / Conflicts →
    **为什么它现在仍是 Candidate**（5 条升级条件核对表）。
  - **空数据模式**：无候选时显示「当前暂无经过验证的 Current Candidate 数据 / 历史研究覆盖至 2025 /
    当前市场实时数据：未接入」，**不编造内容**。
  - **UI 不显示相似度分数 / 百分比**；不显示新闻流。
- **Phase 7.2 · 时间型观察层**（`TimeObservationLayer`，Timeline 内新建的**极轻**一层）：
  - **Level 1**：历史观察窗口带（淡底纹 + 点划线边界 + 窗口标签；跨年窗口分两段渲染）+
    该年的**研究观察起点**标记（Early Signal 落点，可点击进入历史案例）。
  - **Level 2**（点击就地展开，不离开页面）：窗口 / 口径 · **历史复现 X / Y 个观测年份** ·
    年份案例（点击 → 既有 Campaign Detail）· 为什么值得看 · **限制说明** · 免责声明。
  - **今天的关系**：`当前位于历史观察窗口` / `接近历史观察窗口`（14 天浏览缓冲）/ 诚实空态
    「当前没有发现处于历史时间观察窗口的模式」。**多条命中不合并**，默认展开最相关的一条。
  - **硬约束**：不出现概率 / 胜率 / 买卖信号 / 分数；无可用窗口时**整层不渲染**（不显示空壳）。
- **Timeline Year Coverage Rule（V1.9.1）**：覆盖年份 = `start` 年 **连续到** `end` 年（两源同一 helper）。
- **Timeline Entry Identity（V1.9.0）**：`entryId = `${campaign_id}@${展示年份}``；React key / focus /
  年份页签用 `entryId`，**打开 Campaign Detail 仍以 `campaign_id`**。
- **F-MED-1 / F4** 已修复。
- 测试：`npm test` **372 项通过**（9 → 10 个测试文件；Phase 7.1 后 337，Phase 7.2 +35 → 372，
  新增 `timeObservationPatterns.test.tsx`）；`tsc -b` 通过；`build` 通过。

---

## Data Status

| 数据 | 位置 | 状态 |
|---|---|---|
| Canonical Export | `exports/timeline_export_v1.json` | **唯一**（本轮未改动） |
| Research DB | `research/database/cycle_research.db` | 6.1 MB，提交 Git |
| Schema | `research/schema/schema.sql` | 冻结（未改） |
| 历史研究产物 | `research/research/**` | **zero semantic diff** |
| 行情 CSV | `research/data/market/**` | 原样保留 |
| Product verified | `data/verified/` | 空（历史核验尚未开始） |
| **Current Candidate** | `research/current/current_candidates.json` | **第一轮真实候选 5 条**（`snapshot_date = 2026-09-15`，`generated_by = ai-offline`） |
| **示例 fixture** | `research/current/fixtures/example_candidates.json` | 4 个候选，**非真实数据** |
| **叙事标注** | `research/current/narrative_annotations.json` | 13 条，`PENDING_HUMAN_REVIEW` |

---

## Export Contract

- 唯一版本：`timeline_export_version = "1.0"`
- 契约：`contracts/timeline_export_v1.md`
- 顶层 11 字段白名单；未知字段拒绝。
- Research **生成**，Cycle **消费**。
- **Current Candidate 不走 export**：它是独立 Artifact（`research/current/`），
  设计上就不进入 canonical export —— 候选不是 Research 事实。

---

## Known Limitations

- Product 生产层（`data/verified/`）为空：真实历史核验（L0/L1 → L2）尚未开始，
  生产首页只能显示空态；实际内容需经 `?preview=1` 查看。
- 所有历史日期为**研究候选日期**，未全部完成人工最终核验 → 标注 provisional / conflict。
- `research/research/` 嵌套目录名为历史遗留，迁移时刻意保留。
- Research 脚本依赖腾讯免费行情接口（仅 `fetch_market_*` 需要网络）。
- **Current Candidate canonical 数据集已非空（Phase 7.1）**：第一轮真实离线研究数据 5 条候选
  （`snapshot_date = 2026-09-15`）。数据集本身仍是**静态 Artifact**，产品运行时不联网。
- **同一快照存在并行研究轮次（2026-09-16 合并记录）**：另一并行会话对同一
  `snapshot_date = 2026-09-15` 独立产出了 4 条候选（`6dac246`）。经方法论比对
  （相位矩阵 8 维全部手工声明、新建 4 个 `macro_theme`、候选粒度过粗、缺可复现性字段），
  canonical **采用本地 5 条轮次**；并行轮次保留在 Git 历史并在
  `research/current/README.md` §11 登记为交叉参考。两轮均通过验证器 →
  **分歧属粒度与矩阵写入协议问题，不是数据合规问题**。
  → 这意味着**同一快照可能有多个有效轮次**，下一轮必须显式声明 `research_round`。
- **Phase 7.1 发现的架构问题（已记录，未修改产品代码；详见 `research/current/README.md` §9）**：
  1. Similarity v2 的 **Pattern 层依赖 `macro_theme` 名称与历史 Theme Cycle 精确匹配** →
     本轮 5 个候选中 4 个的新 Macro Theme（电力设备 / 信息通信 / 高端装备）无同名 cycle，
     Pattern 层恒 0 → **等级最高只能到「中相似」，无法出现「高相似」**。
  2. **「关注度从高位回落」直接判 `WEAKENING`** → 触发结构冲突并把阶段退回 `UNKNOWN`；
     引擎无法区分「回落但仍高于一般水平」与「关注度消失」。
  3. **证据台账必须覆盖 `MARKET` 来源类型**，否则市场维度 `UNKNOWN`、阶段退回 `UNKNOWN`
     （本轮 `CC-2026-OPTICAL-LINK` 初稿即如此）。
  4. 「单日行情最多 `WEAK`」与「关注度下降 → `NEGATIVE`」两条规则**不对称**，
     使刚起步方向更难被归入 `THEME_FORMING`。
- `research/current/narrative_annotations.json` 为**产品侧结构标注（PENDING_HUMAN_REVIEW）**，
  仅驱动相似度第 4 层；未标注的历史案例该层不参与（不推断）。
- **Phase 7.2 观察层的限制（不是缺陷，是数据的真实状态；详见
  `research/research/reports/Time_Observation_Pattern_Integration_v0_1.md` §11 / §12）**：
  1. **只有 1 条 Pattern 达到 Timeline 门槛**（汽车主题上半年末启动观察窗口，N=7）→
     观察层的覆盖度长期受制于历史样本量（补录 2018 之前 / 非汽车主题族才能扩展）。
  2. **全部锚点为研究候选日期（未经行情人工核验）** → 数据质量上限 MEDIUM，
     产品必须永远带「探索性」标记。
  3. **幸存者偏差无法消除**：ThreeC 只记录「形成了 Campaign 的主题」，无法观测「同样在 6 月出现但未成势」的主题。
  4. **研究样本自身 6 月占比 33%**（均匀基准 8.3%）→ 时间聚集含研究选择偏差成分，已写入 Artifact `background_baseline`。
  5. Pattern 与 Theme Cycle **没有稳定映射键**（本轮用 `rule_id` 作主题族定义）；
     扩展到更多主题前需要一个显式的「主题族 ↔ rule / theme」定义表（模型层决策）。
  6. `timeline_eligible`（布尔）与 `timeline_eligibility`（三值）并存，解析器对不一致发告警；
     未来若出现第三种纳入状态应统一为枚举。
- `npm audit` 报告 5 项漏洞（构建工具链传递依赖，本轮未处理）。

---

## Current Blockers

**无硬性阻塞。** Phase 7 Current Research Discovery v0.1 已实现并通过全部门禁。

**真实数据限制（不是缺陷，是项目定位的一部分）：**
- A股整体环境（Layer A）为 `Unknown`：无指数 / 成交量 / 资金 / 情绪数据源，也不应由此推导大盘状态。
- 当前年份（2026）无历史研究数据 → Layer B 为**诚实空态**（研究覆盖至 2025）。
- Research Attention 的 `当前值得研究` 目前为空：现有正式 Campaign 均已记录到结束阶段。
- **「当前研究候选」已非空**：Phase 7.1 落地第一轮真实离线研究数据（5 个 `CC-*` 候选，
  `snapshot_date = 2026-09-15`）。其中 **1 个推导阶段为 `UNKNOWN`**（脑机接口：政策 / 标准连续落地
  但市场关注度自 1 月高位回落 → 结构冲突 → 引擎**拒绝归类**，与研究声明并列显示），
  这正是「诚实不下结论」的预期行为，不是缺陷。
  **空态仍可用**（数据集显式 `candidates: []` 时），已有独立测试覆盖。
- `Sentiment` driver 在研究数据中**没有来源** → 永不出现（不编造）。

### Research 侧数据瓶颈（`Historical Coverage Audit v0.1` 实测）

- `theme_family_count` **上限 = 2** → **跨族稳健性检查当前不可能通过**（数据问题，非算法问题）。
- 当前侧声明 4 个 Macro Theme，历史侧仅 2 个 → **3 个主题（电力设备 / 信息通信 / 高端装备）无历史可类比**。
- 生命周期仅 **3 / 13** 对象 COMPLETE；`THEME_FORMING` / `BROAD_CONFIRMATION` 覆盖仅 **46%**。
- 事件 `NOT_AVAILABLE` **7 类**；证据 `company` / `capital` **各 0 条**；核验日期 **0 / 24**。
- **Time Observation v0.4 结论**：独立稳健时间结构 = **1 个**（汽车族 EARLY_SIGNAL 上半年末窗口）。
  v0.3 曾显示「2 个」，其中第 2 个（`MAIN_RISE`，残差 1 天）经 `lifecycle_rhythm` 判定为**派生结果**；
  v0.4 已把该判定**落进 Promotion Gate** → 有效 `TIMELINE_CANDIDATE` 4 → 2、独立结构 2 → 1。
  **数字回到 1，但依据比 v0.2 时更硬。**
- **派生门覆盖边界（诚实限制）**：本门只对有节奏分析的 **2 个 scope** 生效（`rule_auto_summer` / `TH-AUTO`）。
  其余 18 个 scope **无节奏分析** → `is_derived = None` → 本门**无法**对它们下结论。
  这**不是**「已证非派生」，而是「无证据」。**不得**把 `None` 读作「独立」。
  完整账目：191 = 139（无节奏分析）+ 22（含非 export 阶段）+ 30（全部阶段派生）。

---

## Next Single Goal

> **派生结构门已完成（v0.4）：`effective TIMELINE_CANDIDATE` 4 → 2，有效独立结构 2 → 1。**
> **规则链已稳定 —— 当前真正的瓶颈是「数据」，不是「方法」。**
> **下一步唯一一件事：Wave 1 数据扩容（P0 电力设备 / P0 信息通信历史 Cycle）。**

**为什么是数据，不是方法**

v0.4 之后，时间观察层的规则链（数值门槛 → 口径稳健 → 派生门）**三次收敛到同一个结论：独立结构 = 1 个**。
继续在 1 个结构上做方法学微调，**边际收益低于扩大样本**。三个硬限制全部是**数据问题**：

| 限制 | 现状 | 只能靠什么解决 |
|---|---|---|
| 跨族稳健性无法检验 | `theme_family_count` 上限 = 2，有效候选全为汽车族 | 引入**非汽车族**的历史 Theme Cycle |
| 交易日历覆盖不足 | 仅 2.6 / 8 年 → 时间统计退化为自然日口径 | **补全 2018–2025 交易日历** |
| 核验比例为 0 | 0 / 24 核验，全部 `confidence = low` | 补证据来源（`company` / `capital` 各 0 条） |

**要做的（只做这一件）**：按 `Historical_Coverage_Audit_v0_1.md` §12 执行 **Wave 1**：

1. **P0 · 电力设备历史 Cycle**、**P0 · 信息通信历史 Cycle**
   —— 修复「当前侧有候选、历史侧无 Cycle」这一**已存在的断裂**（3 个主题无历史可类比）。
2. **P1 · 统一 `evidences.evidence_type` 口径**。
3. **P1 · 补全 2018–2025 交易日历**。

**执行方式（协议要求，不可跳步）**：
Coverage Audit → Wave 1 入库 → 逐项验证 → **重跑 Time Observation（新轮次）** → Coverage Audit v0.2 → 再决定 Wave 2。

> **红线**：**不为了增加 Pattern 数量而放松纳入标准**（不降 N、不拓宽窗口、不弱化 LOO、不制造 Pattern）。
> 若扩容后独立结构**仍为 1 个**，那就是诚实结论，**照实报告**。

**之后（同一序列，不同轮次）**：
1. `Historical Coverage Audit` 升级为 **v0.2**（消费 v0.4 候选池）。
2. `F7`（`华为汽车` taxonomy 缺口）—— 随扩容一并处理，属**数据决策**。

**在此之前不新增功能、不改产品代码、不改 DB 数据（除 Wave 1 明确列入的条目）。**

用户视觉 / 交互 Review（Phase 7.1）可同时进行：

1. 「当前研究候选」区是否克制（不抢 Timeline）？
2. 空态是否读得懂「系统在诚实地说不知道」，而不是「系统没做完」？
3. `?candidates=example` 的示例是否清楚表达了「这是协议示例、不是真实研究对象」？
4. 详情里的「为什么它现在仍是 Candidate」核对表，是否让你更想去看证据而不是看结论？
5. Temporal Firewall（已隔离证据）是否被理解为「不引用未来信息」的保证？
6. Historical Similar Cases 的「四问」是否比「历史涨了多少」更有用？

---

## Explicitly Not Doing

本轮及默认状态下**明确不做**：

- 新行业 / 新 Rule / 新统计 / 新 Radar / 新预测 / 新 UI redesign / Dashboard / Notification / Backend
- 修改 Research Model v1.0 / v1.1、`schema.sql`、`contracts/`、已有历史研究结论
- 新增数据库实体（含 `theme_cycles` / `theme_relations`）
- 把 Current Candidate 写入 DB / schema / export / contracts；把候选自动升级为 Campaign
- **产品运行时联网**：不抓新闻、不调 LLM、不取实时行情 / 资金 / 情绪数据（保持静态 PWA）
- 自动研究流水线（本阶段只交付协议 + 验证器 + 消费端）
- 相似度分数 / 百分比 / 概率 / 胜率 / 评分榜 / 买卖信号 / 荐股 / 目标价
- 用历史年份数据冒充当前年份状态（look-ahead）
- 改动 `src/models/` 与 Research 侧语义
- 把提前观察区做成「预测 / 买入建议 / 历史统计事实」
- force push
- 删除现有测试
