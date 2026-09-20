# PROJECT_STATE.md — ThreeC 当前真实状态

> 动态接班文档：只回答“现在是什么状态、哪里有问题、下一步做什么”。
> 长期规则见 `AGENTS.md`；未来路线见 `docs/ROADMAP.md`；历史细节见 `docs/CHANGELOG.md`。

- 更新日期：2026-09-20
- branch：`main`
- ahead / behind：`0 / 0`
- working tree：clean
- HEAD：`5c288c0`（`feat(research): import R01-06 defense/military canonical research`；本文件随 R01 Governance Review 提交入库）
- 最近完成：**R01 Governance / Consistency Review v0.1**（**审计完成，未改任何业务数据**；
  **G0 = 0 · G1 = 5 · G2 = 6 · G3 = 4**；4 项为 SA/TO 刷新前置阻塞项；详见 `docs/R01_GOVERNANCE_CONSISTENCY_REVIEW_v0_1.md`）

## 1. 项目当前定位

**ThreeC = A股历史机会时间轴 / 历史机会地图。**

核心价值：

> 从历史周期里找结构，而不是从历史数据里找同名主题。

主链路：

`今天 → 历史同期 → 历史周期阶段 → 当前研究对象 → 历史结构对应 → 为什么对应 / 哪里不同 → 继续研究`

不是交易决策、预测、买卖信号、概率或推荐系统。

## 2. 当前总阶段

### Research Core：第一版闭环完成

`Historical Model → Historical Data → Time Observation → Current Research → Structural Analogy`

当前已完成：
- Structural Analogy Rule Set v0.2 冻结
- Structural Analogy Research v0.2 baseline
- Structural Analogy Explanation Artifact v0.2
- Product Similarity Architecture Gate v0.1 — PASS
- Product Adapter v0.1（Structural Analogy Artifact → Product View Model）
- Time Observation v0.5
- CMTR v1
- Historical Driver Canonicalization
- Robustness / Feasibility / Readiness

### Product Core：闭环已成立，并已具备可重复的研究更新循环

```
Current Time → Current Candidate → Structural Analogy → Historical Case
             → Historical Cycle Map → Current Research Refresh Loop
```

**已完成**：Product Similarity Architecture Gate v0.1（PASS）· Product Adapter v0.1 ·
Product UI Integration v0.1 · UX Review + Performance Gate v0.1（PASS）·
Historical Case Experience v0.1（PASS）· Historical Cycle Map v0.1（PASS）·
**Current Research Refresh Loop v0.1（PASS）**。

当前 Product 主线：

`Timeline → Current Time Lens → Lifecycle Lens → Calendar Lens`

Current Candidate 已进入 Current Time Lens。

Structural Analogy 已通过 Adapter 接入 Current Candidate / Current Time Lens。UI Integration v0.1 已完成。

## 3. Structural Analogy 当前基线

Research v0.2：
- 5 Current Candidates
- 17 Historical Cycles
- 85 comparison pairs
- STRICT_STRUCTURAL_SUPPORTED = 1
- STRUCTURAL_SUPPORTED = 4
- STRUCTURAL_PARTIAL = 36
- THEME_ONLY = 3
- INSUFFICIENT_EVIDENCE = 5
- NO_VALID_CORRESPONDENCE = 37

规则版本：

`structural-analogy-ruleset-v0.2`

最大瓶颈仍是机制级 Driver 证据深度，不是规则或 vocabulary。

## 4. Product-facing Artifact 与 Adapter

已新增：
- `docs/STRUCTURAL_ANALOGY_EXPLANATION_ARTIFACT_v0_1.md`
- `research/research/reports/structural_analogy_explanations_v0_1.json`
- `research/scripts/build_structural_analogy_explanation_v0_1.py`
- `research/research/reports/structural_analogy_explanations_v0_2.json`
- `research/scripts/build_structural_analogy_explanation_v0_2.py`
- `src/data/timeline/structuralAnalogy.ts`
- `src/data/timeline/__tests__/structuralAnalogy.test.ts`
- `src/components/CurrentTimeLens/StructuralAnalogySection.tsx`
- `src/components/CurrentTimeLens/__tests__/structuralAnalogySection.test.tsx`

Artifact 覆盖 85 explanations，且：
- 来源唯一 = Structural Analogy Research v0.2
- 规则唯一 = Rule Set v0.2
- Product READ_ONLY
- 无 score / ranking / probability
- `--check` 可逐字节复现

**v0.2 已通过 Architecture Gate；Adapter v0.1 已消费该契约。**
1. `why_not_similar` 不应把 CROSS_MACRO_THEME 当成“为什么不相似”。
2. explanations 当前按 structural status 再按 cycle id 排列；虽然不是研究 ranking，但 Product 很容易把数组顺序误读为排名，应去除这种暗示。
3. `historical_campaign_id` 同时承载 historical campaign 与 Research Candidate，需要在 Adapter 前明确 cycle / campaign identity。
4. provenance 需要明确哪些证据支撑哪个维度，避免 Product 误把候选全部证据理解为每个维度的直接依据。

因此：

> **Explanation Artifact v0.2 是当前 Product Adapter 的 Research-facing 输入；v0.1 只作为历史保留。**

## 5. 当前 Product Architecture Debt

### 三套比较体系

1. `currentSimilarity.ts`
   - Current Candidate × Historical
   - 内部 score / tier
   - 当前 UI 已使用

2. `historicalSimilarPhase.ts`
   - Historical × Historical
   - Lifecycle Lens
   - 内部 score / tier

3. Structural Analogy
   - Current Candidate × Historical Cycle
   - Lifecycle / Mechanism Driver / Evidence Sequence / Event Structure
   - 正式 Research Correspondence
   - 离散状态，不以 score 定义

长期目标：

- Calendar = 时间邻近浏览
- Lifecycle = 生命周期浏览
- Structural Analogy = 正式结构对应

不能长期维护三套“历史相似算法”。

### Driver 双层语义

Product Current Candidate：
- 证据类别：POLICY / INDUSTRY / CAPITAL / SENTIMENT / EXTERNAL

Structural Analogy：
- 驱动机制：POLICY_DRIVEN / INDUSTRY_UPGRADE / TECH_BREAKTHROUGH / …

以后必须明确区分“证据类别”与“驱动机制”。

### OpportunityRadar

`src/components/OpportunityRadar/` 当前不在 `App.tsx` 主流程。

状态：

**LEGACY / DEFER**

不在 Architecture Gate 前删除。

## 6. Time Observation

Time Observation v0.5 已完成并暂时冻结：

- raw candidates = 315
- distinct samples = 139
- independent robust structures = 1
- TOP-01 = N7 / center 06-11 / window 05-27~06-26 / recurrence 5/7
- cross-family robust = 0

不再为了增加 Pattern 数量继续扩容或放宽标准。

## 7. 当前唯一下一目标

# R01 收口 → **治理修复决策**（Governance Review 已完成，待决定是否修复）

**已完成（全部 PASS）**：… Product 侧全部轮次 · **R00**（Intake Protocol）· **T01**（taxonomy gap）·
**R01-01 / R01-02 / R01-03 / R01-04 / R01-05 / R01-06 Canonical Import** · **Intake Validator C25**（严格 Draft-07）。

### R01 进度

| task_id | scope | status |
|---|---|---|
| `R01-01` | 高端装备 / 机器人 | ✅ 已导入（+5 campaigns / 2 RC） |
| `R01-02` | 半导体 / 电子 | ✅ 已导入（+8 campaigns / 4 RC） |
| `R01-03` | 资源 / 有色 / 化工 | ✅ 已导入（+6 campaigns / 5 RC） |
| `R01-04` | 消费 | ✅ 已导入（+11 campaigns / 2 RC） |
| `R01-05` | 金融 / 地产 | ✅ 已导入（+7 campaigns / 5 RC） |
| `R01-06` | 军工 | ✅ 已导入（**+2 campaigns / 5 RC**） |

> **★ R01 六个任务已全部完成 Canonicalization**（Intake → Canonical Decision → DB Import → Export）。
> **★ R01 Governance / Consistency Review v0.1 已完成**（审计 + 分级 + 影响范围 + SA/TO 前置条件），**未修改任何业务数据**。
> **下一步（待决策）**：是否按 G1 / G2 清单执行治理修复；修复完成后再刷新 SA / TO。
> **★ 建议顺序**：① G1-1 / G1-3 / G1-5 落地「约定」（改数据）→ 解 SA 阻塞 ② G2-1 Peak/End 四态规范 → 解 TO 阻塞
> ③ 刷新 SA ④ 刷新 TO ⑤ G1-2 / G1-4 / G2-3 / G2-4 / G2-6 按独立轮次处理。

### Governance Issue 分级（R01 Governance Review v0.1）

| 级别 | 数量 | 项 |
|---|---:|---|
| **G0 必须修复** | **0** | 无机械性错误 / 数据损坏 / 契约违规 |
| **G1 应统一** | **5** | G1-1 市场侧证据门槛（软门槛，非硬门槛）· G1-2 `research_report` Tier 向 Research Model §15 对齐 · G1-3 Beta / 相对收益 Level 0–3 分级 · G1-4 Validator 缺 orphan 检查 · G1-5 `result=weak` 语义（残留 `C-2019-AD` 的 `strength=weak`） |
| **G2 建议统一** | **6** | G2-1 Peak/End 四态规范 · G2-2 Theme Cycle Pattern 标注（4 个存疑）· G2-3 `campaign_date_observations` 缺失（5 个 pre-R01）· G2-4 孤儿 source / evidence 处置规范 · G2-5 3 条 temporal warning 定性 · G2-6 taxonomy aliases / Mechanism 登记 |
| **G3 可保持差异** | **4** | promote 率差异（29%~85%）· `campaign_themes.role` 未用 `catalyst` · 8 个未使用 theme · `classification` 分布差异 |

**实测关键数据**：DB↔Export **0 字段不一致** · 共享 evidence **0**（1:1 全库零违规）· rule↔campaign_year↔annual_review **零缺失** ·
taxonomy 未被任何 R01 修改（52 行 / 11 root，**11/11 均有 Campaign**）·
**Beta caveat 覆盖率 pre-R01 0/13 → R01-01 1/5 → R01-02 1/8 → R01-03 1/6 → R01-04 1/11 → R01-05 7/7 → R01-06 2/2**（标准随时间演进，非随机差异）·
`research_report` DB 内 **23 条全 tier=2**（R01-01 7 / R01-02 2 / R01-03 2 / R01-04 2 / R01-05 10 / **R01-06 0**；R01-06 改用 `media_tier3`+T3）·
孤儿 evidence **25**（R01-04 9 / R01-05 4 / R01-06 3 / R01-01 2 / legacy 7）· 孤儿 source **84**（R01-05 22 / R01-03 18 / R01-06 16 / R01-02 11 / R01-01 5 / R01-04 5 / legacy 7）·
**无任何 Campaign 达到 Beta Level 2 / 3**（L1 仅 R01-05 的 7 个 + R01-06 的 `C-2020-MIL-EQUIP-ORDER`）·
**3 条 DB warning 全部来自 R01-02**，属「期末/年度总结类证据」的内容期 vs 发布期口径差，**非数据错误**。

### Historical Universe 当前实测

| 项 | 值 |
|---|---:|
| Macro Theme 根节点 | **11** |
| **有 Campaign 的根节点** | **11 / 11**（汽车 · 医药健康 · 信息通信 · 电力设备 · 高端装备 · 电子 · 资源 · 消费 · 金融 · 房地产 · **国防军工**）★ **全覆盖，无空缺 root** |
| Historical Campaign | **52** |
| Research Candidate（导出层） | 27 |
| 跨族 Campaign 对 | `C(11,2)` = **55** |

**R01-06 新增 2 个 Canonical**：`C-2020-MIL-EQUIP-ORDER`（2020–2022 装备采购/订单景气；17 ev / 14 IG；
唯一具备「军费→订单→基本面→市场」四层可复核链条）· `C-2019-MIL-GROUP-RESTRUCTURE`（2019「南北船」集团战略重组；
**peak = NULL**，市场侧行情证据缺失）。
**5 个 RESEARCH_ONLY**：`RC-2019-MIL-PARADE-70` · `RC-2025-MIL-PARADE-80` · `RC-2017-MIL-MIXED-REFORM` ·
`RC-2015-MIL-REFORM-BULL` · `RC-2024-MIL-COMMERCIAL-SPACE`。
详见 `docs/R01_06_CANONICAL_DECISION_v0_1.md`。

**R01-06 关键裁决**：**`CF008`** 军费→订单传导**存在但不稳定**（2021 时滞约 9 周；**2022 预算 +7.1% 而板块 -23.63%** 为反证）→
**军费层只能作 `context`，不得作为 start 锚点** · **`CF001`** 2020H2 与 2021 **判为一个 Campaign（不拆分）** ·
**`CF004`** 商业航天**族属 UNRESOLVED** → 007 不进入任何族 · **`CF006`** 2015 Beta 不可分离 → 006 Research Only ·
**`E042`** 入 DB 但**不绑定任何 Campaign**（research-level，避免 temporal-mislabel）。

**R01-05 新增 7 个 Canonical**：`C-2022-RE-POLICY-THREE` · `C-2020-RE-DEBT-RISK`（`result = weak`）·
`C-2024-FIN-BROKER-POLICY` · `C-2023-FIN-SOE-VALUATION` · `C-2024-FIN-BANK-DIVIDEND`（peak/end = NULL）·
`C-2020-FIN-BANK-CREDIT` · `C-2025-FIN-INSURANCE`（peak/end = NULL）。
**5 个 RESEARCH_ONLY**：`RC-2024-RE-POLICY-517` · `RC-2019-RE-EASING` · `RC-2020-FIN-BROKER-VOLUME` ·
`RC-2016-RE-SHANTY` · `RC-2015-FIN-LEVERAGE`。
详见 `docs/R01_05_CANONICAL_DECISION_v0_1.md`。

**新增机制轴覆盖**：地产政策周期（融资收紧→风险暴露→政策修复）· **信用周期驱动**（银行顺周期）·
**估值重估/资金配置**（中特估 · 高股息）· **市场风险偏好/流动性**（券商 · 保险资产端）·
**装备采购/订单释放**（含甲方预付款 / 合同负债代理）· **军工集团改革/资产重组**。

**新增 Theme Cycle（7）**：`realestate_policy_cycle_2020_2023`(Sequential) · `bank_valuation_2023_2025`(Parallel) ·
`broker_risk_appetite_2024` · `bank_credit_cycle_2020_2021` · `insurance_asset_liability_2025` ·
`military_equipment_order_cycle_2020_2022` · `military_group_restructure_2019`。

### Structural Analogy / Time Observation

**未刷新**（`structural_analogy_explanations_v0_2.json` 字节不变）。Rule Set v0.2 与 Research v0.2 均 FROZEN。

**★ SA / TO 前置条件（Governance Review v0.1 结论）**：

| 类别 | 项 |
|---|---|
| **必须在刷新前处理（阻塞）** | ① **G1-1** 市场侧证据门槛统一（SA 按 `strength` 跨族比较前须确定「无市场侧证据」的 strength 上限） ② **G1-3** Beta / 相对收益 Level 0–3 标注（防止把相对超额当 Alpha） ③ **G1-5** `result=weak` 语义统一（残留 `C-2019-AD` 的 `strength=weak`） ④ **G2-1** Peak / End 四态规范（**TO 直接依赖日期窗口与 peak**） |
| **可带 caveat 进入刷新** | ① G1-2 `research_report` Tier（23 条历史 tier=2 为兼容，不影响结论） ② G1-4 孤儿未机器校验（已人工复核） ③ G2-2 Theme Cycle Pattern 4 个存疑（overlap 已记录） ④ G2-3 5 个 pre-R01 无 date_observation ⑤ G2-5 3 条 temporal warning ⑥ G2-6 taxonomy aliases（164 个中 ~95 alias / ~45 机制名） ⑦ G3-1 promote 率差异 |

**建议刷新顺序**：① G1-1/1-3/1-5 约定落地 → ② G2-1 Peak/End 规范 → ③ 刷新 SA（新 artifact 版本）→ ④ 刷新 TO（新 artifact 版本）
→ ⑤ G1-2 / G1-4 / G2-3 / G2-4 / G2-6 按独立轮次处理。

### 未决与待办（**未排期**）

| 类型 | 项 |
|---|---|
| OPEN | **`CF013` 股息口径差**（个股前复权含股息 vs 沪深300 价格指数不含股息）—— **UNRESOLVED**；已转为**结论约束**（**不得解释为行业 Alpha**、未伪造调整后收益）；需以**中证红利全收益 / 银行行业全收益指数**重算 |
| OPEN | R01-05 保留未决：`CF001`(Q2 标的重叠) · `CF003`(券商全市场 Beta) · `CF004`(红利风格因子) · `CF005`(中特估银行/保险边界) · `CF006`(房地产 vs 金融 Cycle 归属) · `CF008`(2020-07 券商驱动) · `CF009`(KEEP_BOTH) · `CF011`(两龙头方向相反，不允许取平均) · `CF012`(保险代表标的 vs 板块叙事) |
| OPEN | R01-05 生命周期未闭合：`C-2024-FIN-BANK-DIVIDEND` / `C-2025-FIN-INSURANCE` **peak/end = NULL** · `C-2023-FIN-SOE-VALUATION` peak/end 为推断值；`C-2020-FIN-BANK-CREDIT` 仅 4 ev / 4 IG + 单一标的 → **建议后续补证** |
| OPEN | **本地无金融/地产行情序列** → R01-05 的 Export `market_data = unavailable`（相对表现仅引自 intake 一级行情证据） |
| OPEN | **`CF007`**（医美归属：消费 vs 医药健康）保留未裁决 · **`CF005`**（白电驱动归因）保留 · **`CF010`**（补贴 vs 真实需求；**`+11%` vs `-4.3%` 口径冲突完整保留**）· **`CF001`**（白酒 classification）保留 |
| OPEN | **`RC-2020-CONS-SMALL-APPLIANCE`（007）仍需补证**（渗透率一手数据 + 同期证据）· **`RC-2024-CONS-PET-FOOD`（013）保持 Research Only** |
| OPEN | `C-2020-CONS-DUTYFREE` **A 股广度不足**（sec=1）· `C-2023-CONS-VALUE-RETAIL` **start 年度级 + end NULL** · `C-2024-CONS-TRADE-IN` **Beta 未排除** |
| OPEN | **跨任务「市场关注」口径差异未统一**（R01-03 起更严 vs R01-01/02）—— **本轮未固化新 Protocol、未回改历史**；**R01-06 `N007` 另提出「R01-05 与 R01-06 的 Beta 判据应保持一致，否则跨族结构比较不可比」** |
| OPEN | **`美容护理` / `商贸零售` taxonomy 缺口**（`MT006`/`MT007` 提案级未解析）—— 不扩展 |
| OPEN | R01-03 的 `CF003`（锂跨族）· `CF009`（黄金背离）保留未决 |
| OPEN | R01-02 的 3 条 `evidence-temporal-mislabel` 警告（已收口为 caveat） |
| OPEN | **仅剩 1 个 root 无 Campaign：国防军工** —— **R01-06 已导入 2 个 Campaign**（`C-2020-MIL-EQUIP-ORDER` / `C-2019-MIL-GROUP-RESTRUCTURE`）→ **11 个 root 中已有 11 个具备 Campaign**（原「无 Campaign 的 root」问题**已解决**） |
| OPEN | **R01-06 保留未决**：`CF005`（船舶：民船周期 vs 军品订单；**与 T01 的归属张力**待对齐）· `CF009`（2017 军民融合 vs 混改）· `CF004`（商业航天族属 UNRESOLVED）· `CF001`（2020H2/2021 阶段边界，**保留重新评估条件**） |
| OPEN | **R01-06 待处理项**：`E042` 的 `role = context`（全包 `contradicting = 0` → 建议 R01 Governance Review 统一）；4 条 evidence 缺 `event_date`（E008/E017/E037/E038）；`SEC003`（国证军工指数）`ticker = null`；`CF004.note` 笔误「TwoC Agent」；`002.why_not` 交叉引用错误（引 CF004 讨论 classification） |
| OPEN | **R01-06 的 `001` Beta 污染未分离**（2020-07 启动段）· **`002` 市场侧行情证据完全缺失**（`peak = NULL`）· `003/004/005/007` 生命周期未闭合 · `005` 需补证（2017 分月行情 + 混改落地公告） |
| OPEN | **本地无军工行情序列** → R01-06 的 Export `market_data = unavailable`（市场数据仅引自 intake 二手整理，全 T3） |
| OPEN | Validator C08 vs Research Model v1.0 §15 的 `research_report` tier 冲突（**R01-03 `H1` / R01-05 `K` / R01-06 第三次复现** → **Cross-task governance issue，待 R01 Governance Review 统一处理**） |
| OPEN | **治理修复待决策（Governance Review v0.1 已分级，尚未执行）**：**G1-1** 市场侧证据软门槛 · **G1-2** `research_report` Tier 对齐（C08 `(2,)` → `(2,3)` + 23 行 migration） · **G1-3** Beta Level 0–3 强制标注 · **G1-4** Validator 新增 C26 orphan report（WARN 级） · **G1-5** `result=weak` 语义 + `C-2019-AD` 的 `strength=weak` 残留 · **G2-1** Peak/End 四态规范 · **G2-2** Theme Cycle Pattern（4 个存疑） · **G2-3** 5 个 pre-R01 缺 `campaign_date_observations` · **G2-4** 孤儿处置规范 · **G2-5** 3 条 temporal warning 定性 · **G2-6** taxonomy alias 表 + Mechanism 登记表（**不扩展 taxonomy**） |
| OPEN | **Worker ↔ ThreeC 规则统一待办**：Worker 报 `24 checks` vs ThreeC `C01–C25` · Worker 无 Strict Draft-07 · Worker `--check` 目录假设差异 · **Worker 无 orphan 检查** · **须向 Worker 提供 T01 后的 taxonomy 快照（11 root / 52 行）**（R01-06 manifest 曾误称 root 仅 4 个） · 建议后续为 Worker 增加 C26 并统一 `--check` 行为（**本轮不重建 Worker**） |
| OPEN | R01-05 孤儿证据 `E-FINRE-49/50/51/63`（intake 中未被任何候选引用）按既有惯例导入；`E-FINRE-63` = 全局基准 E141 · R01-06 孤儿证据 `E-MIL-40/41/42`（`E-MIL-42` = E042 反向证据，research-level 不绑定） |
| POLISH | `themeCycleId` 可读性 · `event_type` ↔ 证据类别标签对应 |

### 边界

- 不新增 Product 功能 / 不新增 Dashboard
- 不改 Research Model v1.0 / schema / CMTR v1 / Export Contract v1.0 /
  Structural Analogy Rule Set v0.2 / Time Observation v0.5
- 不引入实时网络 / LLM · 不建立 ranking / score / probability / prediction

## 8. 当前质量债务

非主线 blocker：
- campaign_date_observations verified = 0/131
- Driver DIRECT evidence depth
- market / temporal = SUPPLEMENTARY_ONLY
- historical coverage imbalance

这些问题暂不阻塞本阶段 Review，但性能问题必须在 Product polish 前闭环。

## 9. 验证基线

最近已报告全绿：
- Structural Analogy Explanation `--check` PASS
- Research validators 全 PASS（`validate_db` / `validate_timeline_export` / `validate_batch_research` /
  `validate_promotion_manifest` / `check_doc_schema_consistency` / `validate_current_research` /
  `validate_monorepo_integrity` / `refresh --check`）
- **Intake Validator `--check` PASS（25 checks，FAIL 0，WARN 0；含 C25 严格 Draft-07；packages found 6）**
- **Intake Package R01-01 ~ R01-06 各 PASS（C01–C25）** · **Validator 单元测试 44/44 PASS**
- **R01-06 Canonical Import**：`validate_db` PASS（**3 条 WARNING 与导入前完全相同，无新增 temporal warning**）·
  既有 50 Campaign 逐条深比对 0 修改 · taxonomy `themes` 52→52 未变 · `import --verify` 幂等 · LF 不变式全 CRLF=0
- **R01 Governance Review（审计，未改数据）**：DB↔Export **0 字段不一致**（52↔52）· 共享 evidence **0**（1:1 全库零违规）·
  孤儿 evidence 25 / 孤儿 source 84 已人工复核 · 6 个新 rule 的 `campaign_year` ⊇ `annual_review` **零缺失** ·
  **3 条 DB warning 全部来自 R01-02**（总结类证据内容期 vs 发布期口径差，非数据错误）· **G0 = 0**
- npm test 476/476
- tsc -b PASS
- vite build PASS

下一轮任何实现先核对真实 HEAD，再执行验证。
