# Medical Health Data Entry v0.1 — Audit

> **性质**：首次将非汽车 Macro Theme 接入 ThreeC 数据链路的**最小验证数据集**审计报告。
> **目标**：验证 `Research → DB → Export → Timeline` 完整流程是否可跑通。
> **日期**：2026-09-14 ｜ **范围**：最小数据集（**不是**完整医药数据库）
> **未修改**：`schema.sql` / `contracts/` / export contract / Timeline UI / Research Model。
> **纪律**：不伪造数据（取不到的标 unavailable）；不计算 seasonality / win_rate / probability；
> Candidate ≠ Verified。

---

## 1. Created

### 1.1 数据库（`research/database/cycle_research.db`）

| 表 | 新增 | 内容 |
|---|---|---|
| `research_rules` | **+1** | `rule_pharma_upgrade`（医药健康结构性升级观察窗口，base_pattern=医药健康，status=under_review） |
| `annual_reviews` | **+4** | `AR-MED-2019..2022`（medium / strong / strong / weak） |
| `themes` | **+5** | `TH-PHARMA 医药健康`(industry, root) + 4 个子题材：`TH-PHARMA-INNOV 创新药` / `TH-PHARMA-CXO CXO(研发外包)` / `TH-PHARMA-PANDEMIC 疫情医疗` / `TH-PHARMA-TCM 中医药`（均 concept，`parent_theme_id=TH-PHARMA`） |
| `campaigns` | **+1** | **`C-2019-PHARMA-INNOV` 创新药产业链升级** |
| `campaign_themes` | **+3** | 医药健康(related) · 创新药(**main**) · CXO(related) |
| `campaign_phases` | **+6** | startup / acceleration / main_rise / diffusion / retracement / decline |
| `securities` | **+7** | 恒瑞医药 · 药明康德 · 泰格医药 · 英科医疗 · 智飞生物 · 片仔癀 · 以岭药业 |
| `campaign_securities` | **+3** | HENGRUI(leader) · WUXIAPPTEC(leader) · TIGERMED(second_leader) |
| `sources` | **+6** | `S-MED-01..06`（含 4 条 Tier 1：医保局 / 上交所 / CDE / 医保局+中医药局；1 条 Tier 2；1 条行情源 Tier 3） |
| `evidences` | **+5** | `E-MED-01..05`（**5 个独立分组**） |
| `campaign_evidences` | **+5** | 3 supporting + 2 context |
| `events` | **+5** | `EV-MED-01..05`（4+7 集采 / 科创板 / 医保谈判 / CDE 指导原则 / 中医药政策） |
| `campaign_events` | **+4** | trigger ×1 · catalyst ×1 · context ×2 |
| `market_series` | **+8** | 7 只代表标的 + 1 条行业代理（`PHARMA_ETF_512010`） |
| `market_daily` | **+15,550** | 2019-01-02 ~ 2022-12-30，raw + adjusted(qfq) 两套 |

### 1.2 行情数据文件（`research/data/market/`）

- `raw/tencent_<SERIES>.csv` × 8
- `normalized/<SERIES>_daily.csv` × 8

### 1.3 研究脚本（`research/scripts/`）

| 文件 | 说明 |
|---|---|
| `fetch_market_medical.py` | **新增**：医药最小行情集拉取（腾讯 GTIMG，按年分段，raw+qfq，幂等） |
| `seed_medical_min.py` | **新增**：医药最小数据集入库（Rule / Annual / Themes / Campaign / Phases / Securities / Sources / Evidences / Events） |
| `batch_auto_research.py` | **修改**：由「单 Rule 硬编码」改为**多 Rule 驱动**（`RULES = [rule_auto_summer, rule_pharma_upgrade]`）；`build_campaign` 改用 `c["rule_id"]`；新增医药 lifecycle / drivers / signals / theme_cycle / proxy / 2 个 Research Candidate；**修复 2018 反例年证据越权吸收**（见 §4.3） |

### 1.4 导出与产品侧

- `exports/timeline_export_v1.json`：**重新生成**（由既有生成器产出，**未手工编辑**）
  → `rules: 2` ｜ `campaigns: 9` ｜ `research_candidates: 4` ｜ `signals: 14` ｜ `events: 33` ｜ `securities: 46`
- `src/data/timeline/__tests__/*`：**3 个测试文件的数据快照断言同步更新**（见 §4.4）

---

## 2. Not Created

| 项 | 状态 |
|---|---|
| 正式 Campaign | **只创建 1 个**（`C-2019-PHARMA-INNOV`）。**未**创建医药第 2/3 个 Campaign |
| 疫情医疗 / 中医药 | **保持 Research Candidate**（`RC-2020-PANDEMIC` / `RC-2021-TCM`），**不进入 `campaigns` 表** |
| `data/verified/campaigns.ts`（产品 verified 层） | **未写入** —— 保持空（见 §3.3 说明） |
| `theme_cycles` / `campaign_relations` 表 | **未创建**（维持 research-level 决定） |
| 医药行业完整覆盖 | **未做**（仅 8 条行情序列，7 只标的） |
| 其他行业（电力/消费/传媒/教育…） | **未触及** |
| `schema.sql` / `contracts/` / export contract / Timeline 组件 UI | **未修改** |
| 预测 / 概率 / 胜率 / seasonality / 买卖建议 | **未产生** |

---

## 3. Data Coverage

### 3.1 全库规模（本次前 → 后）

| 表 | 前 | 后 |
|---|---|---|
| `research_rules` | 1 | **2** |
| `annual_reviews` | 8 | **12** |
| `campaigns` | 8 | **9** |
| `themes` | 7 | **12** |
| `campaign_themes` | 18 | **21** |
| `campaign_phases` | 17 | **23** |
| `securities` | 27 | **34** |
| `sources` | 49 | **55** |
| `evidences` | 46 | **51** |
| `events` | 25 | **30** |
| `market_series` | 32 | **40** |
| `market_daily` | 16,266 | **31,816** |
| DB 体积 | — | 6.1 MB |

### 3.2 正式 Campaign：`C-2019-PHARMA-INNOV`

| 字段 | 值 | 依据 |
|---|---|---|
| 时间 | **2019-01-02 → 2022-10-31**（约 3.8 年） | 本地行情复核（`start_date_basis/end_date_basis = market_data`） |
| peak_date | **2021-07-01** | 药明康德 / 泰格医药自身高点 |
| Peak Window（lifecycle） | **2020-12-25 → 2021-07-01**（DATE_WINDOW） | 恒瑞医药 2020-12-25 + 药明/泰格 2021-07-01 → **分批见顶** |
| strength / result / classification | strong / positive / theme_campaign | 研究判定 |
| date_confidence | medium | 边界为研究候选，未人工最终核验 |
| theme_cycle_id | `medical_structural_upgrade_2019_2022` | research-level 标签 |
| status（生产） | **`provisional`** | 见 §3.3 |

**lifecycle（7 阶段）**：EARLY_SIGNAL 2019-01-02 → THEME_FORMING 2019-07-22 → BROAD_CONFIRMATION 2019-11-28
→ MAIN_RISE 2020-01-01~2020-12-24 → **PEAK 2020-12-25~2021-07-01** → DECLINING 2021-07-02~2022-10-31 → MAIN_END 2022-10-31

**drivers（四问）**：start 2 条 · accelerator 2 条 · turning 3 条 · ending 3 条（均内嵌 EV-/E- 来源引用）

**Evidence（5 条 / 5 个独立分组 ≥2 ✓）**
| ID | 分组 | 角色 | 内容 |
|---|---|---|---|
| E-MED-01 | `med_market_innov` | supporting | 药明/泰格 2021-07-01 区间高点；恒瑞 2020-12-25 |
| E-MED-02 | `med_policy_insurance` | supporting | 2019-11-28 医保谈判（PD-1 首入医保） |
| E-MED-03 | `med_policy_ipo` | supporting | 2019-07-22 科创板开板 |
| E-MED-04 | `med_policy_cde` | context | 2021-07-02 CDE 抗肿瘤药物指导原则 |
| E-MED-05 | `med_policy_vbp` | context | 2018-12-17 4+7 集采（Setup 背景，`temporal_relation=prior`） |

> **Peak 口径合规**：严格按 `theme_campaign_separation_v1.md` **v1.1 §6** —— 使用 **Campaign 自身代表标的**
> （恒瑞 / 药明 / 泰格），**未**使用医药指数口径（`PHARMA_ETF_512010` 仅作行业参照）。

### 3.3 ⚠ 关于「verified / confirmed」的处理（**关键决定**）

任务要求正式 Campaign 状态为 `verified / confirmed`。**本轮实际写入 `provisional`**，原因：

1. **导出契约与校验器不支持 `verified` 经此路径产生**：
   `validate_timeline_export.py` 的 `VALID_RESEARCH_STATUS = {PROVISIONAL, CONFLICT, INSUFFICIENT}`，
   生成器的 `production_status()` 只映射出 `provisional / conflict / preview`。
2. **`verified` 在本项目的定义是「人工最终复核确认」**（Contract §9；`data/verified/campaigns.ts` 的录入标准），
   **不能由 AI 自行声明**；该文件当前为 0 条，其注释明确「不得为了填充 verified 层而编造历史事实」。
3. **与既有 8 条汽车 Campaign 保持一致**（同为 `provisional`）。

→ 因此：**「已进入正式 `campaigns` 表（非候选）」已达成**（`C-` 前缀、`research_status=PROVISIONAL`），
但**「人工核验的 verified」需人工 Review 后另行提升**（该动作未由本轮执行）。

### 3.4 行情覆盖（最小集，非行业覆盖）

| 序列 | 标的 | 归属 | 覆盖 |
|---|---|---|---|
| HENGRUI | 恒瑞医药 | 主线（创新药） | 972 根 ×2 |
| WUXIAPPTEC | 药明康德 | 主线（CXO） | 972 ×2 |
| TIGERMED | 泰格医药 | 主线（CXO） | 972 ×2 |
| INTCO | 英科医疗 | RC-2020-PANDEMIC | 972 ×2 |
| ZHIFEI | 智飞生物 | RC-2020-PANDEMIC | 972 ×2 |
| PIANZAIHUANG | 片仔癀 | RC-2021-TCM | 972 ×2 |
| YILING | 以岭药业 | RC-2021-TCM | 972 ×2 |
| PHARMA_ETF_512010 | 医药ETF(沪深300医药) | **仅行业参照** | 971 ×2 |

### 3.5 显式未覆盖（如实声明）

- **无**医药行业完整指数（申万医药生物 801150 未能取得 → 未编造，改用沪深300医药 ETF 作代理并标注）；
- **无** 2018 年及以前的医药行情（本地窗口自 2019-01-02 起）；
- **无** 2023 年及以后数据（窗口末端 2022-12-30）；
- **无** 疫情医疗 / 中医药的 DB 级 Campaign 记录（保持 Candidate，仅存在于 export `research_candidates`）。

---

## 4. Validation

### 4.1 门禁结果（全部通过）

| 门禁 | 结果 |
|---|---|
| `npm test` | ✅ **192 / 192 passed**（191 → 192，+1：新增 F-MED-1 固定用例） |
| `npx tsc -b` | ✅ exit 0 |
| `npm run build` | ✅ ok（58 modules） |
| `validate_db.py` | ✅ PASS（0 警告） |
| `validate_timeline_export.py` | ✅ PASS（0 警告；9 Campaign / 4 Candidate / 33 Event / 46 Security） |
| `validate_batch_research.py` | ✅ PASS |
| `validate_promotion_manifest.py` | ✅ PASS |
| `check_doc_schema_consistency.py` | ✅ PASS（17 表 / 125 字段一致，0 FAIL） |
| `validate_monorepo_integrity.py` | ✅ PASS（25 项通过，0 警告） |

### 4.2 汽车回归（**零回归**，逐字段比对）

对生成前后的 `timeline_export_v1.json` 做结构化 diff（基线已备份）：

| 对比项 | 结果 |
|---|---|
| 顶层字段白名单 | ✅ SAME |
| `rule_auto_summer` 全部字段 | ✅ SAME |
| 8 条汽车 Campaign 全字段 | ✅ **ALL SAME** |
| 2 条汽车 Research Candidate 全字段 | ✅ **ALL SAME** |
| 汽车归属 events / securities | ✅ SAME |
| 汽车 signals | ✅ SAME |

→ **既有汽车数据 100% 未被改动**；新增仅为**追加**（1 rule / 1 campaign / 2 candidates / +1 全局事件）。

### 4.3 过程中修复的两处缺陷

| # | 缺陷 | 现象 | 修复 |
|---|---|---|---|
| **P-1** | `build_2018()` 的 2018 反例年**无条件吸收所有 2018 年证据** | 医药的 `E-MED-05`（2018-12-17）被同时归入 `Y2018-NO-CLEAR` 与 `C-2019-PHARMA-INNOV` → `validate_batch_research.py` 报 `evidence-cross-campaign` FAIL | 改为只吸收**未显式绑定任何 Campaign**的 2018 年证据（`evidence_id NOT IN (SELECT evidence_id FROM campaign_evidences)`）。属**通用修复**：今后任何新 Rule 的 2018 年证据都不会被误并入汽车反例年 |
| **P-2** | `campaign_themes` 出现**两条 `role='main'`**（创新药 + CXO） | 产品端 `primaryThemeName()` 取「第一个 main」，顺序依赖 SQLite 物理顺序 → 主题行键不确定（实测落在「CXO(研发外包)」） | 改为**唯一 main**（创新药），CXO 置 `related`（CXO 是本 Campaign 内的产业链环节，非独立 Campaign） |

### 4.4 测试同步说明（诚实记录）

新增数据使 **10 条**「数据集形状快照」断言失效，均已**更新**（未删除任何测试）：

| 文件 | 更新内容 |
|---|---|
| `timelineAdapter.test.ts` | `source_commit` 快照；数据量快照 8/2/9/26/39 → **9/4/14/33/46**；「9 月同期」逐年命中（医药跨年 Campaign 使 2019-2022 每年多 1~2 条）；「2 月同期」由「历史各年皆空」改为「2019-2022 由跨年 Campaign 覆盖」 |
| `currentTimeLens.test.tsx` | `byYear` 2019/2022 期望值；2019 阶段用例改为**按 campaign_id 取条目**（原为 `entries[0]`）；「2 月 → uncovered」改为 `coveredYears=4`；条目总数 7 → **14**；SSR 空态用例改用**真正空的数据源**（生产 verified 层） |
| `themeRows.test.tsx` | 行级不变式改为「primaryPhase 与 phaseSummary 一致」；**新增** 1 条用例固定 F-MED-1 当前行为 |

### 4.5 仍存在的缺陷（**仅记录，未修**）

#### **F-MED-1（数据层 · 中等）**：跨年 Campaign 的 `ThemeCampaignEntry.year` 取错 → 行级 `primaryPhase` 为 null

- **位置**：`src/data/timeline/themeRows.ts:186` → `year: c.year,`
- **根因**：entry 的 `year` 取的是 **campaign 自身年份**（`c.year`，即 export 的 `year` 字段 = 2019），
  而非**所属行的年份**（`row.year`）。行级代表阶段聚合时用 `samePeriodWindow(e.year, month)`，
  于是跨年 Campaign 的 4 个年份条目全部用 **2019 年的窗口**计算 → 命中为空 → `primaryPhase = null`。
- **为何此前未暴露**：汽车 Campaign 的 `campaign_year` 恒等于其展示年份（一年一条），
  两者数值巧合相同；**只有多年度 Campaign 才会分离**。
- **已实测证据**：`e.year` 4 条全为 `2019`；而各条目自身 `phaseLabel` 正确为 `[null, 主升, 退潮, 退潮]`；
  直接调用 `historicalPhasesInWindow` 得 `主升:62 / 退潮:62 / 退潮:62`（应得 `primaryPhase = 退潮`）。
- **影响**：① 跨年 Campaign 行的「代表阶段」显示为「阶段未标注」；② 若 UI 直接展示 entry 年份会与行年份不一致。
- **最小修复（1 处）**：`year: c.year` → `year: row.year`（并同步更新 §4.4 中固定该行为的用例）。
- **为何本轮未修**：任务 §六 明确禁止修改 Timeline UI；`themeRows.ts` 自述为 UI/Adapter 视图层，**待确认后单独立项**。

#### **F-MED-2（语义 · 低）**：跨年结构性 Campaign 使「历史同期」失去淡季空态

- 医药 Campaign 跨 2019-01-02 ~ 2022-10-31，故 2019–2022 的**任意月份**窗口都会命中它。
- 既有的「2 月淡季无 Campaign」是**汽车季节性数据集**的产物，**不是产品不变式**。
- **不是错误**，但需产品侧确认：跨年 Campaign 是否应在「历史同期」中逐月重复出现（当前行为：是）。

#### **F-MED-3（结构 · 低）**：Research Candidate **无法绑定 Evidence**

- `campaign_evidences.campaign_id` 外键指向 `campaigns`，而 RC 不在 `campaigns` 表 →
  `RC-2020-PANDEMIC` / `RC-2021-TCM` 的 Gate 依据只能写入 export 的 `notes`，**无法结构化绑定证据**。
- 本轮按既有结构处理（写入 notes 并如实声明）；**建议后续评估是否需为候选提供证据绑定能力**（属 schema 议题，本轮不动）。

---

## 5. Remaining Unknown

| # | Unknown | 类型 | 需要什么才能解决 |
|---|---|---|---|
| **U-D1** | 医药 Theme Cycle 精确 Start / End | 数据 | 2018 年及更早行情（4+7 集采 Setup 在本地窗口之外） |
| **U-D2** | `RC-2020-PANDEMIC` / `RC-2021-TCM` 的精确 Peak / End | 数据 | 更完整的子行业与代表标的行情 |
| **U-D3** | 疫情医疗是否受全国 β 污染 | 方法 | 与 HS300 / 行业代理做 β 分离（数据已在库，待做） |
| **U-D4** | 中医药归属：Sub-theme vs 独立 Macro Theme（U-C1 未决） | 决策 | **人工决策** |
| **U-D5** | 创新药与 CXO 的 Peak 相差 6 个月（2020-12-25 vs 2021-07-01）是否意味着 CXO 应升为独立 Campaign | 方法 | 按 v1.1 Gate 重跑（本轮沿用「共享资金池 + 龙头重叠 → Sub-theme」结论，但需承认 Peak 错位这一新证据） |
| **U-D6** | 申万医药生物行业指数（801150）真实数据 | 数据 | 权威数据源（当前**如实 unavailable**，未编造） |
| **U-D7** | 2018 年医药证据（E-MED-05）的完整行情支撑 | 数据 | 2018 年行情 |
| **U-D8** | `verified` 状态提升 | 流程 | **人工 Review**（Contract §9 / `data/verified/campaigns.ts` 录入标准） |
| **U-D9** | F-MED-1 修复方案确认 | 决策 | 确认是否允许修改 `themeRows.ts`（1 行） |

---

## 6. 结论

> **ThreeC 可以从汽车平滑扩展到医药健康 —— 全链路 `Research → DB → Export → Timeline` 已跑通，且汽车数据零回归。**

- **平滑的部分**：Rule / Annual / Themes（含 `parent_theme_id` 层级）/ Campaign / Phases / Evidence / Event /
  Market Series / Export 契约 / 产品 Adapter 与 Timeline —— **均无需改 schema、无需改契约、无需改 UI 即可承载新行业**。
  `RC-` / `C-` 前缀与 `research_candidates` 隔离机制**原生支持「1 正式 + 2 候选」的混合粒度**。
- **暴露的摩擦**：① 生成器原为单 Rule 硬编码，需改为多 Rule（本轮已完成，且**未影响汽车输出**）；
  ② 「数据集形状快照」测试需随数据更新；③ **F-MED-1**（跨年 Campaign 的 entry 年份取错）是首次接入多年度 Campaign
  才暴露的**既有适配层缺陷**；④ **F-MED-3** RC 无法结构化绑定证据。
- **直接价值**：本轮正是「最小验证数据集」应有的收获 —— **用最小代价把扩展时必须修的 4 个点全部暴露出来**，
  而不是等到录入完整医药数据后才发现。

### 下一步建议（唯一一件，**不自动执行**）

> **确认 F-MED-1 的处理方式**（是否允许 1 行修复 `themeRows.ts:186`）。
> 它是唯一会**影响产品正确展示**的阻塞项；其余三项（F-MED-2 / F-MED-3 / U-D5）可先记录。

---

*本报告为 research-level 数据接入审计；未修改 schema / contracts / export contract / Timeline UI / Research Model。
配套：`Medical_Health_Theme_Cycle_Discovery_v0.1.md`（发现）、`Medical_Health_Campaign_Boundary_Decision_v0_1.md`（边界决策）、
`theme_campaign_separation_v1.md` v1.1（方法论）。*
