# research/current — Current Research Discovery 数据协议 v1.0

> **Phase 7** 的离线研究数据端。回答的问题是：
> **「今天这个时间点，我应该去历史资料里研究什么？」**
> 而不是「明天应该买什么」。

---

## 1. 为什么存在这一层

ThreeC 的历史研究数据覆盖到 **2025**，而「当前时间」是 **2026**。
Current Time Lens 原本只能回答「现在是几月，这个月历史上发生过什么」，
无法回答「现在可能有什么值得开始研究的 Theme」。

本层补上这一段：把**离线研究**（人 / 脚本 / AI）产出的「当前研究对象候选」
以**可验证的静态数据**形式交给产品端。

```
Web / AI Research（离线，人工或脚本）
        ↓
research/current/current_candidates.json      ← 本目录
        ↓
Product Adapter（src/data/timeline/currentCandidate.ts）
        ↓
Current Time Lens（当前研究候选）
        ↓
Historical Similar Phase（Similarity v2）
        ↓
Research Questions（研究方向）
```

### 硬边界

| 允许 | 禁止 |
|---|---|
| 离线人工 / 脚本 / AI 生成候选数据 | 产品运行时联网抓取 |
| 静态 JSON 落库并提交 Git | 前端调用 LLM / 外部 API / 新闻源 |
| 产品端只读消费 | 产品端写入 DB / schema / export / contract |
| GitHub Pages / PWA 静态部署 | 引入后端 / 实时行情 / 资金 / 情绪数据 |

**网络与 AI 只出现在「研究数据生成端」，不进入「产品运行端」。**

---

## 2. 文件

| 文件 | 作用 |
|---|---|
| `current_candidates.json` | **canonical 数据集**（产品端默认消费）。自 **Phase 7.1** 起承载**第一轮真实研究候选**（5 条，`snapshot_date = 2026-09-15`）；空态仅在数据集显式为 `candidates: []` 时出现，详见 §7。 |
| `schema.json` | 数据协议（JSON Schema，draft-07 子集）。字段与枚举的权威说明。 |
| `fixtures/example_candidates.json` | **示例 fixture，不是真实研究数据**。仅用于验证协议 / 防线 / 推断 / 相似度行为。 |
| `validate_current_research.py` | 见 `../scripts/validate_current_research.py`（验证器）。 |

---

## 3. 核心概念

### 3.1 Candidate ≠ Theme ≠ Campaign

```
Raw Signal → Candidate → Evidence Accumulation → Theme Hypothesis
           → Theme Forming → 正式 Research Campaign
```

**Current Candidate 是研究对象，不是已经验证的 Theme。**
它可以被继续观察 / 被证伪 / 被合并 / 被拆分 / 最终升级为正式 Campaign / 被删除。

它**绝不**自动写入 `campaigns` / 正式导出。命名空间隔离：

| 前缀 | 含义 |
|---|---|
| `C-*` | 正式 Historical Campaign（Research 生产） |
| `RC-*` | Research Candidate（Research 生产） |
| `CC-*` / `FX-*` | **Current Candidate**（本层；`FX-` 仅 fixture） |

候选 ID 使用 `C-` / `RC-` 前缀会被验证器拒绝。

### 3.2 事实 / 解释 / 推测必须分开

| 层级 | 唯一允许出现的位置 |
|---|---|
| **事实**（Fact） | `evidence[].claim` —— 只写「谁在什么时候发布了什么」，禁止写入推断 |
| **解释**（Interpretation） | `core_narrative` —— 对事实的解读 |
| **推测 / 未知**（Hypothesis / Unknown） | `uncertainty_notes` —— 必须显式写出 UNKNOWN |

### 3.3 阶段由「相位证据矩阵」推导，不由单一指标决定

禁止 `涨幅 > X ⇒ EXPANSION`。阶段来自 8 个维度的证据组合：

| 维度 | 含义 | 可否由证据派生 |
|---|---|---|
| `narrative` | 是否形成清晰主线 | ✗ 研究声明 |
| `policy` | 是否出现政策催化 | ✓ 由 `POLICY` 证据派生 |
| `industry` | 是否出现产业反馈 | ✓ 由 `INDUSTRY` 证据派生 |
| `market` | 是否出现市场关注 | ✓ 由 `MARKET` 证据派生 |
| `capital` | 是否出现资金响应 | ✓ 由 `CAPITAL` 证据派生 |
| `breadth` | 是否从少数标的扩散 | ✗ 研究声明 |
| `company` | 是否出现公司层验证 | ✓ 由 `COMPANY` 证据派生 |
| `information_marginal` | 新增信息边际（区分 PEAK / EXPANSION） | ✗ 研究声明 |

水平枚举（统一 6 值，逐维度语义见 `schema.json`）：
`ABSENT` / `EMERGING` / `PRESENT` / `STRONG` / `WEAKENING` / `UNKNOWN`

**研究只需声明无法由证据派生的三个维度**（`narrative` / `breadth` /
`information_marginal`）；其余留空即由证据确定性派生。声明值优先于派生值，
UI 会逐维度标注来源（研究声明 / 由证据派生 / 未标注）。

### 3.4 枚举只能是有意义的有限集，不能是伪精确数值

| 字段 | 允许值 |
|---|---|
| `candidate_status` | `CANDIDATE` / `WATCH` / `RESEARCHING` / `PROMOTABLE` / `REJECTED` |
| `attention_state` | `EARLY_SIGNAL` / `THEME_FORMING` / `BROAD_CONFIRMATION` / `EXPANSION` / `PEAK` / `DECLINE` / `UNKNOWN` |
| `evidence_strength` | `STRONG` / `MEDIUM` / `WEAK` |
| `evidence.direction` | `SUPPORTIVE` / `NEUTRAL` / `NEGATIVE` / `UNKNOWN` |
| `temporal_relation` | `BEFORE_SNAPSHOT` / `AT_SNAPSHOT` / `AFTER_SNAPSHOT` / `UNKNOWN` |

**禁止** `confidence: "87%"` 这类看起来精确但无统计意义的字段。
`PROMOTABLE` 也不表示「上涨确认」，只表示「可考虑进入正式 Theme / Campaign 研究」。

---

## 4. Temporal Firewall（时间防火墙）

这是本层最重要的基础设施。

1. 数据集必须有 `snapshot_date`；每个候选有自己的 `snapshot_date`（必须 ≤ 数据集）。
2. 每条证据必须有 `source_date` 或 `event_date`。
3. 推导规则：

```
date = source_date ?? event_date
date === null              → UNKNOWN
date  < snapshot_date      → BEFORE_SNAPSHOT
date === snapshot_date     → AT_SNAPSHOT
date  > snapshot_date      → AFTER_SNAPSHOT   ← 违规：不得参与任何判断
```

4. `AFTER_SNAPSHOT` 证据：
   - 不得影响 candidate state
   - 不得参与 Phase 推断
   - 不得参与 Similarity
   - UI 中单列显示为「已隔离（快照后）」

这样才能让 ThreeC 未来具备真正的 **Historical Discovery Benchmark** 能力
（回到某个历史时点，只用当时可得的信息做判断），而不会发生 look-ahead。

---

## 5. 如何新增一个候选

1. 在 `current_candidates.json` 的 `candidates` 加一条，`candidate_id` 用 `CC-` 前缀。
2. `snapshot_date` 填**你做研究的那一天**。
3. 每条事实写一条 `evidence`，注明 `source_date` / `source_type` / `evidence_strength`。
   **快照之后才知道的事，仍然可以写入并标记**（验证器会要求 `AFTER_SNAPSHOT`），
   但它在判断中被隔离。
4. 至少声明 `narrative`（无法由证据派生）。无任何证据时，必须在
   `uncertainty_notes` 明确写 `UNKNOWN`。
5. 跑验证器：

```bash
python research/scripts/validate_current_research.py
```

6. 产品端**不需要改代码** —— 数据集是静态 import，重新构建即可看到。

---

## 6. 明确不做

- 不做自动联网研究流水线（本层只定义**协议 + 验证器 + 消费端**）。
- 不做「AI 自动下结论」：候选必须带证据、必须能被证伪、必须写出 UNKNOWN。
- 不做评分 / 概率 / 胜率 / 买卖信号 / 目标价。
- 不把候选升级为正式 Campaign（那是 Research 的独立评审流程）。

---

## 7. First Real Discovery Round（Phase 7.1）

**这是第一轮真实离线研究数据，不是实时产品数据。** 产品运行时不联网、不调用 LLM、
不抓取新闻；以上内容全部在离线端生成后以静态 JSON 提交。

```
snapshot_date:            2026-09-15
candidate_count:          5
generated_by:             ai-offline（网络与 AI 仅用于离线研究数据生成）
research_coverage_until:  2025（历史 Campaign 只到 2025-08，当前年份无历史研究数据）
```

### 研究问题

> **截至 2026-09-15，我现在应该开始研究哪些 Theme？**
> 不是「明天买什么」、不是「哪只股票会上涨」、不是「哪个板块收益最高」。

### research_method

`Signal → Evidence → Candidate`：

1. 按 5 个方向检索（AI 算力 / 光互联；AI + 能源 / 算电协同；具身智能 / 人形机器人；
   医疗科技 / 脑机接口；其他产业升级方向），**不预设哪一条一定入选**。
2. 只登记**可核验事实**（政策原文、部委发布、公司公告、指数与资金数据），每条带
   `source_date` / `event_date`；**事实 / 解释 / 推测三分离**（`evidence[].claim` /
   `core_narrative` / `uncertainty_notes`）。
3. 一个方向需 ≥3 条证据、且跨 ≥3 类来源，才允许写入候选。
4. **阶段不由研究声明决定**：数据集只声明无法由证据派生的三个维度
   （`narrative` / `breadth` / `information_marginal`）；`policy` / `industry` / `market` /
   `capital` / `company` 由产品端 Phase Evidence Matrix **确定性派生**。
5. **相似度不手填**：`reference_cases` 只是人工对照备注，相似结果全部由产品端
   Similarity v2 实时计算。

### source_policy

Tier 1（国务院 / 发改委 / 工信部 / 国家能源局 / 国家药监局等官方发布）优先；
Tier 2 为公司公告与产业原始数据；Tier 3 为财经媒体，**仅用于转述 Tier 1/2 的事实**，
不单独承担结论。

### 方向标记规则（本轮确立，写入数据集 `known_limitations`）

| 证据形态 | 允许的强度 / 方向 |
|---|---|
| 单日价格、单日涨停潮 | 最多 `WEAK`（**单日行情不足以证明「市场关注形成」**） |
| 多交易日、多标的的板块级关注 | 可达 `MEDIUM` |
| 周度 / 月度资金净流入、月度统计 | 可达 `MEDIUM` |
| 受大盘 β 影响的指数区间变动 | `NEUTRAL`（方向不作单向解读，并在 claim 中声明 β 不可分离） |
| 直接削弱当前假设的事实（关注度明确转弱 / 订单性质证伪 / 盈利未兑现） | `NEGATIVE` |

### 本轮候选（5 条）

| candidate_id | display_name | macro_theme | 证据 | 快照内可用 | 已隔离 | 日期未知 |
|---|---|---|---|---|---|---|
| `CC-2026-OFFSHORE-WIND` | 海上风电与整机价格修复 | 电力设备 | 6 | 6 | 0 | 0 |
| `CC-2026-COMPUTE-POWER` | 算电协同（算力网 × 新型电力系统） | 电力设备 | 10 | 9 | 0 | 1 |
| `CC-2026-EMBODIED-AI` | 具身智能与人形机器人 | 高端装备 | 8 | 7 | 0 | 1 |
| `CC-2026-OPTICAL-LINK` | 高速光互联（1.6T / NPO / CPO） | 信息通信 | 8 | 7 | 0 | 1 |
| `CC-2026-BCI-MEDTECH` | 脑机接口医疗器械 | 医药健康 | 7 | 7 | 0 | 0 |

> 快照后证据为 0 条（本轮未登记任何 `AFTER_SNAPSHOT`）；「日期未知」的 3 条按不可用处理。

### 本轮实测：产品端规则引擎输出（**不是数据集声明**）

| 候选 | 声明阶段 | 推导阶段 | 命中规则 | 一致 | 证据充分度 | 冲突 | 状态门 |
|---|---|---|---|---|---|---|---|
| `CC-2026-OFFSHORE-WIND` | 主题形成 | 主题形成 | `R6_THEME_FORMING` | ✅ | 中等 | 证据方向冲突 ×1 | 候选 → 候选 |
| `CC-2026-COMPUTE-POWER` | 广泛确认 | 广泛确认 | `R5_BROAD_CONFIRMATION` | ✅ | 较充分 | 无 | 研究中 → 研究中 |
| `CC-2026-EMBODIED-AI` | 扩张 | 扩张 | `R4_EXPANSION_DIFFUSION` | ✅ | 较充分 | 证据方向冲突 ×1 | 研究中 → **保持观察** |
| `CC-2026-OPTICAL-LINK` | 扩张 | 扩张 | `R4_EXPANSION_DIFFUSION` | ✅ | 较充分 | 无 | 研究中 → 研究中 |
| `CC-2026-BCI-MEDTECH` | 主题形成 | **未知** | `R8_UNCLASSIFIED` | ❌ | 较充分 | **结构冲突 + 证据冲突** | 研究中 → **保持观察** |

相似度（Similarity v2，Top 3 / 无百分比 / 中相似=★★☆）：

- `CC-2026-OFFSHORE-WIND` → `C-2023-AD`、`C-2022-POLICY`、`RC-2021-TCM`
- `CC-2026-COMPUTE-POWER` → `C-2023-AD`、`C-2022-POLICY`、`C-2019-PHARMA-INNOV`
- `CC-2026-EMBODIED-AI` → `C-2023-AD`、`C-2025-ROBOTAXI`、`C-2022-POLICY`
- `CC-2026-OPTICAL-LINK` → `C-2021-NEV`、`C-2025-ROBOTAXI`、`C-2023-AD`
- `CC-2026-BCI-MEDTECH` → **空态**（推导阶段为 UNKNOWN → 不进入相似度检索，不凑案例）

### known_limitations

- 全部证据来自公开渠道，未接入行情 / 资金实时源。
- **2026-09-15 当日全市场普跌（沪指 -0.54%、超 4300 只个股下跌）且成交额 16253 亿元
  持平年内最低单日记录**，存在明显 β 干扰；跨主题比较市场层时以周 / 月口径为主。
- 本轮有 3 条证据因无法确认发布日期而按「日期未知」处理（不参与判断）。
- 4 个候选的 `macro_theme`（电力设备 / 信息通信 / 高端装备）在历史 Theme Cycle 中
  没有同名 cycle → Similarity v2 的 Pattern 层对其恒为 `UNKNOWN`（见 §9）。

---

## 8. 拒绝候选池（本轮 5 条）

记录被筛掉的方向，供未来做 **Discovery Benchmark**（「AI 是否真的比其他主题更值得关注？」）。

| 方向 | 为什么考虑 | 为什么暂不进入 Candidate | 缺什么证据 |
|---|---|---|---|
| **低空经济** | 政策定位三年三级跃升（新增长引擎 → 安全健康发展 → **新兴支柱产业**）；修订后《民用航空法》2026-07-01 施行并首次增设发展促进专章；民航局新设低空安全司；十部门《低空经济标准体系建设指南（2025 年版）》 | 核心制度变化集中在 **2024—2025**；2026 年主线是规范、立法与安全监管配套，属**制度补全**而非新叙事形成，新增信息边际不足 | 运营侧规模数据（常态化载人航线数、低空物流量、eVTOL 交付量）；2026 下半年是否出现新的产业层边际变化 |
| **固态电池** | 2026 被业界称为装车验证与中试密集落地之年（多家车企发布装车计划、多家电池企业中试线贯通或投产） | 政策支持文件主要停留在 **2025 年**；量产口径集中在 **2027—2030**；2026 年尚无可核验的规模产业化证据，属**技术验证期**，进入本框架会与已有技术突破型候选混淆 | 2026 年新增政策 / 标准；半固态 / 准固态实际出货量（有报道称 2026 年或达 10GWh 级，但未取得可核验来源）；装车后用户侧数据 |
| **商业航天** | 2026-05 国家航天局与市场监管总局发布《商业航天标准体系（1.0 版）》；「十五五」规划首次纳入「加快建设航天强国」；地方推动千吨级重复使用火箭工程化试点 | 证据集中在**标准与规划层**，产业层与公司层无可核验数据；商业化时点跨度长 | 年度发射次数与成功率、在轨资产规模、商业订单与收入口径 |
| **可控核聚变 / 量子科技** | 均为「十五五」规划纲要明确的未来产业；合肥紧凑型聚变能实验装置推进工程总装（预计 2027 年实现全球首次聚变能发电演示）；量子计算接连刷新纪录 | 证据以**科学装置里程碑与地方布局**为主，产业层 / 公司层无初现信号（本框架要求）；按商业化时点（2035 工程实验堆 / 2045 商用示范堆）判断不属「当前」 | 可核验的设备订单、供应链收入、经济性数据 |
| **消费 / 白酒（茅概念）** | 市场层出现明确资金流出（2026-09-07 至 09-11 茅概念主力资金净流出逾 94 亿元） | 除资金流外**未发现任何政策 / 产业 / 公司层边际变化**，属「无新增信息」而非「正在形成」 | 需求端（动销、价格、库存）的可核验口径 |

---

## 9. 本轮发现的架构问题（已记录，未修改产品代码）

1. **Pattern 层依赖 `macro_theme` 名称与历史 Theme Cycle 精确匹配。**
   本轮 5 个候选中 4 个的 `macro_theme`（电力设备 / 信息通信 / 高端装备）在历史数据里
   没有同名 cycle → `candidatePatternOf()` 返回 `UNKNOWN`，Pattern 层恒为 0 分。
   后果：即使阶段、Drivers、Narrative 三层全中，等级最高只能到「中相似」，
   **无法出现「高相似」**。建议未来补一个「跨 Macro Theme 的 Pattern 归一」或
   允许候选声明其 Pattern（属于模型层决策，本轮不动）。
2. **「关注度从高位回落」被判为 `WEAKENING`，会直接触发结构冲突并把阶段退回 `UNKNOWN`。**
   `CC-2026-BCI-MEDTECH` 即如此：政策（3 项 Tier 1 标准）/ 产业 / 公司层均在推进，
   但市场关注度指标显示从 1 月高位回落 → 引擎判 `UNKNOWN`（R8）。
   引擎目前**无法区分「关注度回落但仍高于一般水平」与「关注度消失」**。
3. **证据台账必须覆盖 `MARKET` 来源类型，否则市场维度为 `UNKNOWN`、阶段退回 `UNKNOWN`。**
   `CC-2026-OPTICAL-LINK` 初稿只登记了资金流（`CAPITAL`）而漏登记市场关注证据，
   阶段即退化为 `UNKNOWN`。这说明「来源类型覆盖度」本身是阶段判定的前置条件，
   建议未来在验证器里加一条「维度来源覆盖」提示（本轮未改验证器）。
4. **单日行情证据规则与关注度指标口径不对称。**
   规则要求「单日行情最多 `WEAK`」（→ 市场维度最高 `EMERGING`），
   但「关注度指标下降」被读作 `NEGATIVE`（→ `WEAKENING`）。
   两者都不算错，但会让「刚出现的关注」与「关注回落」在维度上处于不对称位置，
   导致刚起步的方向更难被归入 `THEME_FORMING`（除非没有任何回落记录）。

---

## 10. 下一轮应记录什么（供对照与 Discovery Benchmark）

1. **本轮 5 个候选各自的后续演化**：阶段是否推进 / 是否被证伪 / 是否被并入上位主线。
2. **拒绝候选池的对照结果**：被拒方向与入选方向在随后一段时间的公开证据边际变化对比。
3. **每个候选的「首个可核验里程碑」**：本轮已在 `research_questions` 中写明了各自
   需要什么口径的数据才能推进判断，下一轮应回填这些口径是否出现。
4. **口径变化**：`snapshot_date` 之外的任何口径调整都必须显式记录，避免两轮不可比。

