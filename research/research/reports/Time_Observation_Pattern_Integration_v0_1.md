# Time Observation Pattern 整合报告（Phase 7.2）

> **文件性质**：研究层交付物（Research Layer Deliverable）。不是产品代码，不进入 `src/`、不进入 DB schema、不进入 canonical export。
> **轮次**：`time-observation-pattern-v0.1`
> **日期**：2026-09-16
> **上游研究**：`Seasonal_Observation_Pattern_Discovery_v0_1.md`（探索性研究，确立锚点口径与拒绝规则）
> **本轮产物**：`time_observation_patterns_v0_1.json`（**产品可消费的 canonical Artifact**）
> **生成器**：`research/scripts/build_time_observation_patterns.py`（可复现，`--check` 校验逐字节一致）
> **产品接入**：`src/data/timeline/timeObservationPatterns.ts` + `src/components/TimeObservation/TimeObservationLayer.tsx`

---

## §0 一句话结论

**把「时间型观察规律」从研究层送进了 Timeline：4 条模式中只有 1 条（TOP-01 汽车主题上半年末启动观察窗口，N=7、窗口 05-27 ~ 06-26、历史复现 5/7）达到纳入门槛并进入产品；另外 2 条留在研究层、1 条被拒绝。** 产品由「今天 → 历史观察窗口 → 历史 Campaign」形成最小闭环，且全程未修改 Campaign 定义、未改 schema / export / DB。

---

## §1 本轮目标与边界

**目标**：交付 **Time-based Observation Layer（时间型观察层）** —— 让用户浏览 Timeline 时能知道
**「历史上，一年中的这个时间位置附近，反复出现过值得研究的主题启动吗？」**

**不做**（与上游研究及项目红线一致）：

- 不做预测 / 不输出未来概率 / 胜率 / 收益预测 / 买卖信号 / 最佳埋伏点；
- 不实现 Structural Historical Analogy、不做 embedding / 向量库 / 新后端 / 实时数据；
- 不新建 DB 表、不改 `research/schema/schema.sql`、不改 `exports/timeline_export_v1.json`、不改 `contracts/`；
- 不改 Campaign 定义、不改 Research Model、不重写 Timeline。

**Pattern ≠ Campaign**：一条 Pattern 对应多年、多个 Campaign；Pattern 只是「多年观察结果的统计摘要」，
Campaign 依旧是历史事实对象。

---

## §2 数据链路（唯一，无手工 Copy）

```
exports/timeline_export_v1.json  +  research/database/cycle_research.db   （只读输入）
                     ↓  research/scripts/build_time_observation_patterns.py
     research/research/reports/time_observation_patterns_v0_1.json         （canonical Research Artifact）
                     ↓  @observation alias（静态 import，运行时零网络）
             src/data/timeline/timeObservationPatterns.ts                   （Product Adapter / View）
                     ↓
     src/components/TimeObservation/TimeObservationLayer.tsx               （Timeline 内极轻一层）
```

与研究侧既有链路一致：**Research 只产数据，Product 只消费数据**。

---

## §3 锚点口径（与 ThreeC 既有语义统一）

优先级严格为：

```
1. EARLY_SIGNAL.start          （lifecycle.EARLY_SIGNAL.start / export.early_signal / signals[].EARLY_SIGNAL 最早）
2. THEME_FORMING.start
3. BROAD_CONFIRMATION.start
4. Campaign.start              （末选）
```

与 `src/data/timeline/preObservation.ts` 的 Formation Anchor 规则同口径。
**不发明**「第一次涨停 / 第一次大涨 / 最高成交额 / 最低点」这类新定义。

> 实测：13 个历史对象 **13/13 全部取到 Anchor A（EARLY_SIGNAL）**，无需退化 → 口径统一，不存在
> 「部分年份用 A、部分年份用 B」的污染。

---

## §4 统计口径与判定（可复核）

| 项目 | 口径 |
|---|---|
| 年内定位 | 日序 + **闰年归一**（3 月 1 日起 −1），使 06-18 跨年可比 |
| 典型窗口 | `Median ± 1×MAD×1.4826`（抗离群）；同时并列保留 P25–P75 与「月降级」两种口径 |
| 离散度 | IQR / MAD / 跨度 |
| 集中度比率 | 跨度 ÷ 均匀期望跨度 `(N-1)/(N+1)×365` |
| 历史复现 | 落入窗口年数 ÷ 有效观测年数（**只描述过去**） |
| 稳定性 | 年份前后两半中位位移：< 21d `STABLE` / 21–44d `MILD_DRIFT` / ≥ 45d `DRIFTING` |
| 单年主导（LOO） | 逐点剔除后中位位移 ≥ 45 天 |

**纳入判定**：

```
TIMELINE_ELIGIBLE : N ≥ 5 且 窗口可构建 且 集中度 ≤ 0.45 且 STABLE 且 无单年主导
REJECTED          : 单年主导，或 窗口不可构建（N ≥ 3 且 IQR > 90 天）
RESEARCH_ONLY     : 其余（样本不足 / 稳定性或集中度未达门槛）
```

窗口可构建性用 `IQR ≤ 90 天` 判定 —— 超过说明锚点跨三个以上季节，任何「窗口」都是人为造的。

> **不输出 permutation p 值**：上游研究已给出（SOP-03 经验 p ≈ 0.0055），但产品数据中不承载显著性数值，
> 避免在产品层出现伪精确。p 与检验细节留在上游报告中。

---

## §5 与上游 v0.1 研究的差异（诚实记录）

本轮的 canonical 生成器**重新计算**了上游探索研究的结果。头条数字完全复现，但有三处**方法学口径差异**
（均为有意收紧，不影响最终分类）：

| # | 项目 | 上游 v0.1 | 本轮 canonical | 理由 |
|---|---|---|---|---|
| 1 | 单年主导判据 | 中位位移 ≥ 45 天 **或** 命中数下降 ≥ 2 | **只用中位位移 ≥ 45 天** | 窗口宽度随样本重算而变化，边缘年份会让命中数跳动 1–2 个（边缘效应），不足以判定「单年主导」。按上游口径 SOP-03 会被误判为 REJECTED（实测命中数会掉 2 个）|
| 2 | 窗口半径 | MAD 取整后再乘 1.4826 | **用浮点 MAD** 再乘 1.4826 | 先取整会人为放宽窗口（SOP-01 会从 06-09~06-25 变成 06-08~06-26）|
| 3 | 无窗口时的复现计数 | 未定义 | **不计算**（`matched_years` 留空、`historical_ratio` 为 null）| 避免「先造一个窗口再数命中」|

**复现结果对照（本轮 = 上游）**：

| 模式 | N | 中心 | 窗口 | 复现 | 强度 | 状态 | 纳入判定 |
|---|---|---|---|---|---|---|---|
| TOP-01 ← SOP-03 | 7 | 06-11 | 05-27 ~ 06-26 | **5 / 7** | A | MODERATE_CANDIDATE | **TIMELINE_ELIGIBLE** |
| TOP-02 ← SOP-01 | 4 | 06-17 | 06-09 ~ 06-25 | 3 / 4 | B | MODERATE_CANDIDATE | RESEARCH_ONLY |
| TOP-03 ← SOP-02 | 2 | 06-01 | 不生成 | 不计算 | C | EXPLORATORY | RESEARCH_ONLY |
| TOP-04 ← SOP-04 | 3 | 01-23 | 不生成 | 不计算 | D | REJECTED | REJECTED |

> 另有 LOO 实测：TOP-01 最大中位位移 5 天 → 无单年主导；TOP-04 最大位移 141 天 → 完全由单一年份（2020 疫情）决定。

---

## §6 哪些进入了 Timeline，为什么

**只有 TOP-01（汽车主题上半年末启动观察窗口）**：

- N = 7（2019–2025），**唯一**达到可做探索性统计规模的族；
- 中心 06-11，典型窗口 05-27 ~ 06-26（31 天，宽窗口），集中度比率 0.4018 ≤ 0.45；
- 前后半段 STABLE（中位位移 +10.5 天）；
- 留一法无单年主导（最大中位位移 5 天）；
- 机制明确：**CALENDAR_DRIVEN 为主**（年中稳增长政策节奏 + 中报预告日历 + 月度产销数据日历 + 国际产业事件），
  **不是** SEASONAL_DEMAND（无终端需求季节性证据）；
- **但仍是探索性**：样本 7 年、全部为研究候选日期（未经行情人工最终核验）→ 产品必须标注「探索性」。

产品呈现方式（强制）：

1. 只显示**宽窗口**，不显示单点日期；
2. 明确机制类别（日历驱动），不写成「夏季汽车旺季」；
3. 一律「历史复现：5 / 7 个观测年份」，**不出现概率**；
4. 必须同时展示限制说明与免责声明。

---

## §7 哪些被拒绝 / 留在研究层

| 模式 | 判定 | 理由 |
|---|---|---|
| TOP-02 汽车智能化 | RESEARCH_ONLY | N=4 < 5；且前后半段 MILD_DRIFT（−27.5 天）；2019 锚点为弱事件驱动，与其他年份不是同一强度样本 |
| TOP-03 汽车电动化 | RESEARCH_ONLY | N=2；两点完全重合（06-01 / 06-01）→ **样本量幻觉**（会让集中度指标与检验出现假显著）；保留供扩样后复查 |
| TOP-04 医药健康 | REJECTED | N=3、锚点分属 3 个月（IQR 151.5 天）→ 无法构建窗口；LOO 位移 141 天 → 完全由单一年份主导 |

> **本轮最重要的反面发现**：医药是数据集中**唯一**跨年重复的 Theme Cycle，却**恰恰不构成时间规律**
> → **主题重复 ≠ 时间规律**。

---

## §8 背景基准（必须保留的限制）

时间聚集**不能**只靠「某月事件多」证明：

| 基准 | 6 月占比 |
|---|---|
| ThreeC 自建事件台账 | **33.3%（10/30）** |
| 指数「最优 30 日窗口」起点 | 18.75% |
| 均匀分布理论值 | 8.33% |

→ 「6 月集中」**部分来自研究样本自身的选择偏差**。该基准已写入 Artifact 的 `background_baseline`，
并在产品限制说明中体现（幸存者偏差：ThreeC 只记录「形成了 Campaign 的主题」）。

---

## §9 研究脚本处置（临时 / canonical / 产品三层明确分开）

| 层 | 内容 | 状态 |
|---|---|---|
| **探索性脚本**（不会长期维护） | `research/research/reports/_seasonal_analysis/`（6 个脚本 + 中间结果） | 保留为探索记录，**已标注 superseded**；不是产品依赖，不再用于生成 canonical Artifact |
| **canonical 生成器** | `research/scripts/build_time_observation_patterns.py` | **正式流水线脚本**：只读输入、自检不过不写盘、`--check` 校验可复现 |
| **产品代码** | `src/data/timeline/timeObservationPatterns.ts`、`src/components/TimeObservation/` | 只读消费 Artifact，不含任何研究算法 |

**自动化程度**：Artifact 完全由脚本生成（**不手工编辑 JSON**）。以后数据扩到 2005–2025、
新增主题族，只需重新运行生成器。

**复现验证**：`python research/scripts/build_time_observation_patterns.py --check`
→ `PASS —— 磁盘产物与重算结果逐字节一致`。

---

## §10 产品接入

| 文件 | 职责 |
|---|---|
| `src/data/timeline/timeObservationPatterns.ts` | 宽容解析 + MM-DD 窗口（含**跨年环形窗口**）+ 邻近关系（`IN_WINDOW` / `NEAR_WINDOW` / `OUTSIDE`）+ View Model 排序 |
| `src/components/TimeObservation/TimeObservationLayer.tsx` | Timeline 内极轻一层：窗口带 + 该年观察起点标记 + Level 2 摘要 |
| `src/components/Timeline/trackPrimitives.tsx` | 从 `Timeline.tsx` 抽出的月份网格 / 今天线原语（**避免第二套轨道实现**） |

**关键产品决策**：

- **日期逻辑只有一套**：复用 `src/utils/date/dateUtils`（`mdToISO` / `isCrossYearMD` / `dayOfYearISO` / `yearFraction`），
  不新造日历；跨年窗口（如 12-20 ~ 01-15）已实现并测试。
- **允许跨年窗口两段渲染**（年末段 + 年初段），与既有 `cont-prev / cont-next` 视觉语言一致。
- **邻近缓冲 `nearWindowDays = 14`**：与 `historicalPreObservationDays = 30` 同性质的 **UI 浏览缓冲**，
  不是统计量、不是预测依据（代码内已注明）。
- **三层结构**：Timeline 窗口带（Level 1）→ 就地展开 Pattern 摘要（Level 2）→ 既有 Campaign Detail（Level 3），
  **不新建第四套详情**。
- **多条模式同时命中不合并**（§26）：今天可能同时处于多条窗口，全部列出，默认展开最相关的一条。
- **允许「什么都没有」**：不在任何窗口时输出「当前没有发现处于历史时间观察窗口的模式」，
  不强行推荐最近的窗口。
- **与 Current Candidate 保持独立**：Time Pattern 回答「什么时候值得看」，Current Candidate 回答
  「当前出现了什么」，本轮不做组合。
- **与「提前观察参考区」并存**：前者是跨年份的时点分布，后者是单个 Campaign 内部的浏览缓冲，两者不可互相替代。

---

## §11 本轮发现的架构问题（已记录，未修改产品代码）

1. **可展示的 Pattern 数量取决于历史样本量，通常只有 1 条** —— 产品层已按「1 条也能成立」设计
   （无窗口时不渲染该层），但这也意味着**观察层的价值会长期受制于样本量**。
   要扩展，需要补录 2018 之前的历史主题与非汽车主题族（上游研究 §33 的 P1/P2 建议）。
2. **宏观主题命名与 Theme Cycle 仍不匹配**：TOP-01 的 `theme_scope` 是 Macro Theme「汽车」，
   而历史 Theme Cycle 是 8 个单年 cycle（auto_ad_2019 / auto_nev_2020 / …），
   Pattern 与 Theme Cycle 之间**没有稳定的映射键**；本轮只用 `rule_id` 作主题族定义。
   若要扩展到更多主题，需要一个显式的「主题族 ↔ rule / theme」定义表（属模型层决策，本轮未动）。
3. **日期核验状态是产品可信度的天花板**：全部锚点 `verification_method = unknown`（未经行情人工核验），
   使数据质量上限只能是 MEDIUM，且 Pattern 永远带「探索性」标记。
   人工核验 7 个锚点日期是**性价比最高的一步**（上游 §33 P0 亦如此建议）。
4. **`timeline_eligible` 布尔与 `timeline_eligibility` 三值并存**：为兼容建议结构保留了冗余布尔，
   解析器会对不一致发告警。若未来出现第三种纳入状态，应统一为枚举。

---

## §12 已知限制（诚实清单）

1. 样本仅 2018–2025（有效观测 7 年；2018 为 `no_clear_campaign` 反例年）；
2. 全部锚点为研究候选日期，未经行情人工最终核验；
3. ThreeC 只记录「形成 Campaign 的主题」→ **幸存者偏差无法消除**；
4. 事件台账本身 6 月占比 33%（均匀基准 8.3%）→ 时间聚集含研究选择偏差成分；
5. 研究规则在 2019–2022 与 2023–2024 之间存在口径差异（2019-01-02 实为本地数据窗口起点）；
6. 该规律**不是**农历型（春节偏移跨度 85–191 天），任何「春节后第 N 天」表达都是错的；
7. 本层是**探索性历史规律**：样本有限，只表示历史复现情况，不代表未来重演。

---

## §13 下一步建议

**P0（最高优先级，唯一一件事）**：**人工核验 TOP-01 的 7 个锚点日期**
（尤其 2019-08-15 弱事件锚点与 2022-04-27 政策锚点），把数据质量从 MEDIUM 提上去 ——
这是当前提升观察层可信度**性价比最高**的一步，也直接决定下一轮能否把「探索性」标签去掉。

**P1**：补录「未成势主题」（量化幸存者偏差）；扩样到 2018 之前或 2026 新年度。

**P2**：建立显式的「主题族 ↔ rule / theme」定义表，把观察层从汽车扩展到电力、医药、TMT 等主题族。

**P3（本轮之后的下一阶段）**：再考虑 Structural Historical Analogy（当前状态 → 结构签名 → 历史阶段）。
本轮只完成「**什么时候值得看**」这一层。

---

## §14 Phase 7.3 更新（Observation Credibility & Coverage）

Phase 7.3 在**不改研究结论、不放松纳入标准**的前提下，补齐了观察层的三个短板：

### 14.1 Anchor Verification（新增）

- 策略与人工覆盖位：`time_observation_anchor_verification_v0_1.json`（artifact_version 0.1）。
- 生成器从 research DB **机械推导**每条锚点核验状态（deterministic，随生成器一起可复现）：

| 规则 | 条件 | 结果 |
|---|---|---|
| `R1_MARKET_DATA` | DB `campaign_date_observations.verification_method = market_data` | VERIFIED / MARKET_DATA |
| `R2_PUBLIC_SOURCE` | 同日 linked evidence 且 `sources.tier ≤ 2` | VERIFIED / PUBLIC_SOURCE |
| `R2B_EVENT_SOURCE` | 同日事件台账且 `sources.tier ≤ 2` | VERIFIED / PUBLIC_SOURCE（**不**等于确认行情起点） |
| `R3_MULTI_SOURCE` | ≥2 个独立 `independence_group` 的同日 evidence | VERIFIED / MULTI_SOURCE |
| `R4_TEXT_MENTION_ONLY` | 仅 Tier ≤2 证据/事件在描述中以**词边界**提到该日期 | **保持 UNKNOWN**（记录候选证据） |
| `R5_NO_EVIDENCE` | 其余（含仅 Tier 3/4 线索） | UNKNOWN |

- **实测**：TOP-01 = 2 / 7（2022-04-27 行情观测；2025-06-22 同日事件 Tier 2）；
  TOP-02 = 1 / 4；TOP-03 = 0 / 2；TOP-04 = 0 / 3。合计 VERIFIED 3 / UNKNOWN 13 / CONFLICT 0。
  5 个 UNKNOWN 中，2023-06-12 与 2024-06-11 有 Tier ≤2 候选证据（已在 note 中标注），优先人工复核。
- **实现修正（重要）**：日期文本匹配必须做**词边界检查**。首版用朴素子串匹配，
  把 `6/18`、`6/10`、`6/11` 全部误判为「提到了 6/1」，导致 5 条假 R4 命中 ——
  修正后 UNKNOWN 的分布才与证据实际强度一致。该约束已写入策略文件的 `implementation_note`。
- **反伪造**：`VERIFIED` 必须携带 `sources`；生成器自检失败即拒绝写盘，产品解析侧对
  「无来源的 VERIFIED」降级为 UNKNOWN。

### 14.2 Theme Family（新增）

- Pattern 通过 `theme_family_id` 引用**既有** Macro Theme：`TH-AUTO`（汽车）/ `TH-PHARMA`（医药健康），
  来源 = `themes` 表 `parent_theme_id IS NULL`；生成器启动即校验存在性（不存在直接失败）。
- `rule_id` 降级为「研究规则范围」，**不再**充当主题身份；mapping 缺失时产品回退到 `theme_scope`。
- 仍未解决：主题族目前只覆盖 2 个 Macro Theme（见 §11.2），扩展到更多主题前需要显式的
  「主题族 ↔ rule / theme」定义表 —— 现在这个表的**位置**已确定（生成器的 `THEME_FAMILY_BY_SCOPE`），
  但内容仍需逐个主题补齐。

### 14.3 Promotion Status（新增）

- 统一字段 `promotion_status ∈ {TIMELINE, EXPLORATORY, RESEARCH_ONLY, REJECTED}`（authoritative）：
  `TIMELINE_ELIGIBLE → TIMELINE`；`REJECTED → REJECTED`；强度 `C → EXPLORATORY`；其余 `RESEARCH_ONLY`。
- 旧字段（`status` / `timeline_eligible` / `timeline_eligibility`）保留为兼容输入；
  生成器自检与产品解析双重校验一致性 → **无破坏性迁移**。
- canonical 结果：`TOP-01 TIMELINE` / `TOP-02 RESEARCH_ONLY` / `TOP-03 EXPLORATORY` / `TOP-04 REJECTED`。

### 14.4 Current Match 与 Historical Recall 分离

- `currentMatch`（今天与窗口的日历关系，三态）与 `historicalRecall`（**始终可用**的回看：
  中心 / 窗口 / 观测年份案例）拆成两个独立语义块。
- 空态分两种：① 无任何可展示窗口 → 「当前没有发现处于历史时间观察窗口的模式」；
  ② 有窗口但今天不在附近 → 「当前日期不在任何历史观察窗口内（**仍可回看**历史窗口与年份案例）」。
- **核验不改变结论**：TOP-01 的核心数字（N=7 / 06-11 / 05-27~06-26 / 5-7 /
  MODERATE_CANDIDATE / CALENDAR_DRIVEN）与窗口、复现、稳定性、LOO 全部不变
  —— 有专门测试断言「加核验前后统计量一致」。

### 14.5 兼容性

| 项 | 是否修改 |
|---|---|
| `research/schema/schema.sql` | 未修改 |
| `exports/timeline_export_v1.json`（contract v1.0） | 未修改 |
| 2018–2025 已有 Campaign 结论 | 未修改 |
| Research Model v1.0 | 未修改 |
| `contracts/` | 未修改 |
| Breaking change | 无（新增字段 + 兼容输入） |

### 14.6 下一步（唯一一件）

人工复核 TOP-01 剩余的 5 个 UNKNOWN 锚点，写入核验文件的 `overrides` 后重跑生成器。
优先 **2023-06-12** 与 **2024-06-11**（已有 Tier ≤2 候选证据）。

---

*Phase 7.3 更新结束 · 2026-09-16*

