# R01-04 Intake Review v0.1 — 消费

> **性质**：ThreeC Agent 对 `research/intake/packages/R01-04/` 的 **Intake 层**审查。
> **本轮范围**：只做 Intake Review。**未创建 Canonical Campaign · 未导入 DB · 未修改既有 Campaign ·
> 未修改 taxonomy · 未刷新 Structural Analogy / Time Observation · 未启动 R01-05 / R01-06 ·
> 未修改 Protocol / Schema / Validator / Package。**
> **12 条 Conflict 一条未消解**；Campaign 的合并 / 拆分**未提前决定**。

---

## 0. 结论摘要

| 项 | 结果 |
|---|---|
| **A. Package 是否通过 Intake** | ✅ **通过** |
| 现有 Intake Validator（**C01–C25**） | **PASS（0 FAIL / 0 WARN）** |
| **C25 Strict Draft-07** | **0 违规**（独立 `jsonschema` 4.26.0 复核确认） |
| checksums.sha256（10 条） | **ALL OK** ✓ |
| **B. 必须修复的问题** | **无**（Package 侧） |
| **H. 是否建议进入 Canonicalization** | ✅ **建议**（11 个可进入；007 建议补证后进入；013 保持 Research Only） |

> ★ **口径说明**：Worker 报告中的 `24 checks` 属其 **Workspace 口径**；
> ThreeC 当前正式版本为 **C01–C25**（含 C25 Strict Draft-07）。**最终以 ThreeC 当前 Validator 为准**。

---

## 1. Package 验收

### 1.1 规模与 checksum

```
R01-04/  manifest.json · coverage.md · candidates.json · evidence.json · sources.json
         securities.json · exclusions.json · conflicts.json · research_questions.json
         quality_summary.json · checksums.sha256      （11 文件 / 5499 行）
```

| 项 | 数量 |
|---|---:|
| Candidates | **13** |
| Evidence | **95** |
| Sources | **82** |
| Securities | **31** |
| Exclusions | **10** |
| Conflicts | **12** |
| Research Questions | **11** |
| Macro Theme Proposals | **10** |
| Cross-task Notes | **8** |

`manifest`：`intake_protocol_version = 0.1` · `research_round_id = R01` · `task_id = R01-04` ·
`source_commit = 2153f6d83b7481300696ab73d792e9e53aa31a07` · `years 2015–2025` ·
`family_directions` 含 消费 / 食品饮料 / 家用电器 / 农林牧渔 / 社会服务 / 商贸零售 / 美容护理

**checksums**：10 条**全部一致**，无未纳入项，无引用不存在的文件 ✓

### 1.2 现有 Intake Validator（C01–C25）

```
validate_historical_research_intake.py research/intake/packages/R01-04
  → checks: 25   FAIL: 0   WARN: 0   RESULT: PASS
  → INFO C25  Strict JSON Schema (Draft-07) 校验通过（0 违规）
```

### 1.3 ★ C25 Strict Draft-07

| Package | Draft-07 违规数 |
|---|---:|
| **R01-04** | **0** ✓ |
| R01-01 / R01-02 / R01-03（对照） | 0 / 0 / 0 |

独立复核（`jsonschema` 4.26.0 / `Draft7Validator` / `FormatChecker`，按 Validator 的装配规则组装完整对象）→ **0 违规** ✓

`--check`：**PASS（0 FAIL / 0 WARN）** · `packages found: 4` ✓

---

## 2. 结构与引用关系

### 2.1 引用完整性

| 检查 | 结果 |
|---|---|
| candidate → evidence 悬空 | **无** ✓ |
| candidate → security 悬空 | **无** ✓ |
| evidence → source 悬空 | **无** ✓ |
| date_candidates → source 悬空 | **无** ✓ |
| **conflict.positions → source / evidence 悬空** | **无**（12 条 conflict 全部逐 position 核验） ✓ |

### 2.2 孤儿检查

| 类型 | 结果 |
|---|---|
| 孤儿 Evidence | **0** ✓ |
| 孤儿 Source | **0** ✓ |
| 孤儿 Security | **0** ✓ |

> ★ **本包无任何孤儿** —— 优于 R01-03（曾有 1 个孤儿 source `S012`）。

### 2.3 Research Model v1.0 §5 证据门槛

**13 / 13 候选全部满足「≥2 Evidence 且 ≥2 independence_group」** ✓

| candidate | ev | IG | sec | **PIT 证据** |
|---|---:|---:|---:|---:|
| `001` 白酒 2016–2018 | 8 | 6 | 3 | 4 |
| `002` 白酒 2019–2021 | 7 | **7** | 6 | 2 |
| `003` 离岛免税 | **9** | **9** | **1** ⚠️ | 4 |
| `004` 疫后修复脉冲 | **11** | 7 | 4 | 4 |
| `005` 非瘟猪周期 | 7 | 6 | 3 | 3 |
| `006` 猪周期反转 | 8 | 7 | 3 | **6** |
| `007` 小家电/清洁电器 | **4** ⚠️ | 3 | 3 | **0** ⚠️ |
| `008` 白电 | 7 | 5 | 4 | **0** ⚠️ |
| `009` 医美 | 5 | 5 | 3 | 4 |
| `010` 国货美妆 | 6 | 6 | 2 | 3 |
| `011` 以旧换新 | 8 | 6 | 4 | 3 |
| `012` 量贩零食 | 6 | 6 | 2 | 1 |
| `013` 宠物食品 | **3** | 3 | 2 | **0** ⚠️ |

### 2.4 ★ 共享 evidence（跨候选）

**3 条** —— 全部为 **007 与 008 共享**：

| evidence | 内容 | 归属 |
|---|---|---|
| `E047` | 2020 年家电出口 4582 亿元、+24.2%（海关总署口径） | 007 / 008 |
| `E048` | 2020 年家电内销 7297 亿元、-9.2%；出口自 2020-06 起强劲反弹 | 007 / 008 |
| `E049` | 2021 年家电零售额 7603 亿元、+3.6%；行业主营收入 +15.5% | 007 / 008 |

> ★ 三条均为**家电行业整体口径**。**这正是 `CF008`（小家电 vs 白电是否合并）的实质**。
> Canonical 化时须按 **1 evidence : 1 campaign**（`validate_batch_research` 强制）做唯一归属
> （与 R01-01 的 `E009`/`E016`、R01-02 的 `E035`/`E056` 同口径处理）。

### 2.5 evidence / source / security 治理

| 维度 | 分布 |
|---|---|
| `temporal_relation` | subsequent 39 · contemporaneous 36 · retrospective 18 · prior 2 |
| `evidence_role` | supporting 71 · **context 16** · **contradicting 8** |
| `support_kind` | historical_fact_support 95 · **point_in_time_support 38** · retrospective_context 18 |
| subsequent / retrospective **缺 `point_in_time_note`** | **无** ✓ |
| `source_type` | **regulator 36** · media_tier2 14 · media_tier3 13 · industry_association 7 · company_announcement 4 · research_report 2 · exchange 2 · website 3 · **other 1** |
| `tier` | **tier 1 = 42** · tier 2 = 26 · tier 3 = 14 |
| securities | 31 条，**全部有 ticker** ✓ · **全部 `survivorship_aware = True`** ✓ · role：leader 9 / second_leader 8 / follow 9 / representative 5 |

> ★ `regulator` 36 + `tier 1` 42 —— **官方一手来源占比为本轮四包最高**，可追溯性强。

---

## 3. 数据质量重点核查（用户指定 5 项）

### 3.1 ★ 2025 家电零售 `+11%` vs `-4.3%` 冲突

| 检查 | 结果 |
|---|---|
| 冲突是否完整保留 | ✅ **是** —— `CF010` 的 **P3** 明确记录「国家统计局口径为 **+11%**，奥维云网推总口径为 **-4.3%**，方向相反」，且**挂有来源** `S076`（2025 年中国家电行业运行情况·内销篇）；`quality_summary.known_gaps[7]` 亦独立记录 ✓ |
| `-4.3%` 侧是否有 evidence | ✅ `E062`（2025-12-31, subsequent, 奥维云网推总口径 8931 亿元、-4.3%） |
| `+11%` 侧是否有独立 evidence 行 | ⚠️ **无** —— 仅由 `CF010.positions[2].source_ids = [S076]` 承载 |

> **判定：冲突已完整保留且**有来源**，不构成必须修复项。**
> 但 `+11%` 侧**缺独立 evidence 行** → 建议后续轮次补齐国家统计局口径的 evidence（**非阻塞**）。

### 3.2 猪价高点 / end 的非官方来源

| evidence | 口径 | 标注 |
|---|---|---|
| `E034`（2019-10-10, **contemporaneous**） | **官方**：2019 年第 40 周全国规模以上生猪定点屠宰企业生猪平均收购价 29.96 元/公斤 | ✅ 官方口径、同期 |
| `E045`（2022-12-21, subsequent） | **非官方**：「**行业信息站复盘称**」2022-12-21 回落至约 15.63 元/公斤、较 10 月高点 -44.9% | ✅ **明确标注非官方**（来源 `S074` 猪易网，`tier 3`） |

> **判定：非官方来源已明确标记** ✓ —— 表述用「行业信息站复盘称」，未冒充官方统计 ✓
> `quality_summary.known_gaps[6]` 亦显式记录「官方周度监测的对应期数未逐期补齐」✓

### 3.3 渗透率数据（估算值 vs 官方统计）

| evidence | 标注 |
|---|---|
| `E067`（2021-06-10, contemporaneous） | 「**券商研究（经媒体转述）**称 2019 年中国医美渗透率约 3.6%」 ✅ 明确标注为券商研究转述 |
| `E095`（2023-12-31, subsequent） | 「**艾媒咨询测算** 2023 年预制菜市场规模 5165 亿元…**渗透率无权威统一口径**」 ✅ 明确标注为测算、并声明无统一口径 |

> **判定：未把估算值当作官方统计** ✓ —— 两处均显式标明来源性质。
> `known_gaps[3]` 亦记录「渗透率类证据普遍缺失…只能以间接证据支撑」✓

### 3.4 后见之明资料的 temporal_relation / PIT

- `retrospective` **18 条**、`subsequent` **39 条** —— **全部带 `point_in_time_note`**（**无缺失** ✓）
- `retrospective_context` support_kind 18 条，与 `retrospective` 一一对应 ✓
- 年度涨跌幅、价格峰值均标注为 `retrospective` 并在 PIT note 中声明「**不得作为当时可识别的见顶/确认信号**」✓
- 官方统计（社零/CPI/海关）统一标 `subsequent` 并填 PIT note ✓

> **判定：后见之明资料标注正确** ✓

### 3.5 是否存在「只靠市场涨幅反推主题成立」的证据链

**实测：全包 95 条 evidence 中含「涨跌幅 / 区间涨幅 / 年内涨幅」字样的市场证据 = 0 条** ✓

- 市场侧证据采用 **个股/板块的「盘中最高价 + 日期」**（如 `E050` 小熊电器 165.90 元 @2020-07-23、
  `E054` 美的 108.00 元 @2021-02-10、`E082` 乖宝宠物 125.88 元 @2025-05-30），**而非涨幅**
- 且这些峰值证据**全部标注为 `retrospective`**，并在 PIT note 中声明不得作为当时信号 ✓

> **判定：不存在「只靠涨幅反推主题」的问题** ✓ —— 本包在这一点上做得比 R01-03 更干净。

---

## 4. CMTR v1 检查（**未修改 taxonomy**）

**唯一实现**：`research/scripts/theme_taxonomy.py`（`canonical-macro-theme-resolution-1`）
现有根节点（**11**）：信息通信 · 医药健康 · 国防军工 · 房地产 · 汽车 · **消费** · 电力设备 · 电子 · 资源 · 金融 · 高端装备

### 4.1 Macro Theme Proposals

| proposal | 名称 | kind | CMTR status |
|---|---|---|---|
| `MT001` | 消费 | NEW_MACRO_CANDIDATE | **RESOLVED → 消费** |
| `MT002` | 食品饮料 | NEW_MACRO_CANDIDATE | **RESOLVED → 消费** |
| `MT003` | 家用电器 | NEW_MACRO_CANDIDATE | **RESOLVED → 消费** |
| `MT004` | 农林牧渔 | NEW_MACRO_CANDIDATE | **RESOLVED → 消费** |
| `MT005` | 社会服务 | NEW_MACRO_CANDIDATE | **RESOLVED → 消费** |
| `MT006` | 美容护理 / 消费医疗 | **CROSS_FAMILY** | **UNRESOLVED_NAME** ✅ **正确**（跨族问题，非新根） |
| **`MT007`** | **商贸零售** | NEW_MACRO_CANDIDATE | **UNRESOLVED_NAME** ⚠️ **见 §4.3** |
| `MT008` | 消费升级 / 消费降级（机制轴） | MECHANISM | **UNRESOLVED_NAME** ✅ **正确** |
| `MT009` | 供给收缩 / 自然周期（机制轴） | MECHANISM | **UNRESOLVED_NAME** ✅ **正确** |
| `MT010` | 财政补贴驱动需求（机制轴） | MECHANISM | **UNRESOLVED_NAME** ✅ **正确** |

### 4.2 候选级解析

**13 / 13 候选全部 `RESOLVED`，root = `消费`** ✓
（匹配名：`消费` · `食品饮料` · `家用电器` · `农林牧渔` · `社会服务`）

### 4.3 ★ 记录的 taxonomy gap（**非阻塞，只记录，本轮不扩展**）

| 项 | 说明 |
|---|---|
| **`MT007` 商贸零售 未解析** | Worker 以 `NEW_MACRO_CANDIDATE` 提交，但 **T01 的 `消费` 根下未设 `商贸零售` 子主题**（T01 只设了 食品饮料 / 家用电器 / 农林牧渔 / 社会服务）。<br>★ **不阻塞**：候选 `012`（量贩零食）**经 `消费` 成功解析** ✓。属**提案级 gap**，非候选级 gap。 |
| `MT006` 美容护理 / 消费医疗 未解析 | `kind = CROSS_FAMILY`，**协议期望的正确结果**（跨族问题由 Canonical Decision 裁决，非新根） |
| `MT008`–`MT010` 未解析 | `kind = MECHANISM`，**协议期望的正确结果**（机制轴非主题） |
| 别名缺口（25 个） | 白酒 / 免税 / 医美 / 化妆品 / 猪周期 / 小家电 / 清洁电器 / 白色家电 / 地产后周期 / 量贩零食 / 宠物食品 / 以旧换新 / 消费升级 等 —— **只记录，不扩展** |

> **判定：无阻塞性 taxonomy gap。** R01-04 可正常进入 Canonicalization。

---

## 5. 重点审阅（用户指定 7 组边界）

### 5.1 白酒：`001`（2016–2018）vs `002`（2019–2021）

- `CF002`（UNRESOLVED）：拆为两个 Campaign vs 同一 Theme Cycle 的两段
- **P1 支持拆分**：2018 年出现 **-27% 级别年度回撤**与 2018-10-29 茅台一字跌停，资金逻辑重置；
  2019 年重启驱动为 **MSCI 扩容 + 外资增量**（与 2016–2017 的价格与龙头集中逻辑不同）；Q5 Residual Test 双向成立
- **P2 支持合并**：两段核心代表标的**完全重叠**（茅台/五粮液/泸州老窖），叙事同为「消费升级/高端化」
- `CF001`（UNRESOLVED）：白酒的 `classification`（industry_trend vs theme_campaign）—— P2 指出
  **2021 年社零 +12.5%、基本面未恶化而价格大幅回落** → 资金面权重高
- **Intake 判断**：两候选各 8 ev/6 IG 与 7 ev/7 IG，**均达标**；`001` 为 Priority B 段，证据明显弱于 `002`
  → **均具备进入条件**；**是否拆分 / 是否合并由 Canonical Decision 裁决**（`CF001` `CF002` 移交）

### 5.2 猪周期：`005`（2018–2021）vs `006`（2021–2022）

- `CF006`（UNRESOLVED，含 **4 个 position**）：
  - P1 属**自然周期**（农业农村部归因供给端、需求端稳定）→ 不应作为 Campaign
  - P2 具**可操作的历史机会属性**（能繁母猪存栏为先行指标、传导约 10 个月；官方逆周期调控框架；股价领先现货约 3 个月）
  - P3 两轮应视为**同一 Theme Cycle 的两段**（机制同源、代表标的部分重叠）
  - P4 两轮应**拆为两个 Campaign**（独立产能拐点：2019-10 首次回升 vs 2021-07 结束 21 个月增长；独立政策事件；部分独立标的）
- **Intake 判断**：`005`（7 ev/6 IG）· `006`（8 ev/7 IG，**PIT 6 为全包最高**）→ **均达标**
  → **均具备进入条件**；**「自然周期是否纳入 Campaign 宇宙」这一判据问题**（`Q001`）属**方法论层面**，
  须由 Canonical Decision 先行确立判据，**再**裁决两轮是否合并 → **`CF006` 移交，且优先级最高**

### 5.3 白电 / 小家电：`007` vs `008` —— `CF008` 驱动归因冲突

- `CF008`（UNRESOLVED）：拆为两个 Campaign vs 同一「家电」Campaign 的两个 sub-theme
  - P1 支持拆分：代表标的**完全不重叠**（科沃斯/石头科技/小熊 vs 美的/格力/海尔）；见顶错位 **5 个月至 1 年**
    （2020-07 / 2021-06–07 vs 2021-01–02）；驱动不同
  - P2 支持合并：同属申万家用电器一级分类、共享家电板块资金池、2021H2 共同受原材料涨价与地产下行压制
- **★ 三条共享 evidence（`E047`/`E048`/`E049`）正是争议的实质** —— 家电行业整体口径无法区分两个子结构
- **`CF005`（UNRESOLVED）**：白电的驱动归因 —— P1 地产后周期 vs P2 出口替代（**P2 数据更支持**：
  2020 出口 +24.2% / 内销 -9.2%）；**P3 反证地产传导的时间关系**（2020 竣工 -4.9% 而板块上行；2021 竣工 +11.2% 而板块已下行）
- **Intake 判断**：
  - `007`：**仅 4 ev / 3 IG，PIT = 0**，渗透率核心机制**缺一手量化数据** → **建议补证后进入**（见 §6 E）
  - `008`：7 ev / 5 IG，但 `research_status = CONFLICT`、**PIT = 0**、**「地产后周期」命名本身存疑** → **具备进入条件但须裁决 `CF005`**
- **★ 不因行业相近而直接合并** ✓ —— Worker 已按代表标的组与生命周期错位拆分，未做机械合并 ✓

### 5.4 医美 / 美妆：`009` vs `010`

- `CF007`（UNRESOLVED）：医美的 Macro Theme 归属 —— **「消费」 vs 「医药健康」**
  - P1 属消费：自费、可选、受收入与消费意愿驱动，与白酒/美妆同属「悦己消费」叙事
  - P2 属医药健康：医美耗材按**医疗器械**监管（药监局）、服务机构受**卫健委**监管，产业链与医疗器械高度重叠
- `CF009`（UNRESOLVED）：医美与国货美妆是否合并；**P3 指出医美监管具双重性质**
  （清退非法供给 = 加速因素；压制扩张预期 = 降温因素）→ Worker 已在 drivers 中**分别归入 accelerator 与 turning** ✓
- **Intake 判断**：
  - `009`（5 ev/5 IG）· `010`（6 ev/6 IG）→ **均达标**
  - `CF007` 属**跨族归属**问题：**CMTR v1 不回答**（它只做名称 → 根解析）；`MT006` 已按 `CROSS_FAMILY` 提交，
    **未自行增加 canonical theme** ✓ → **移交 Canonical Decision**
  - 医美「渗透率 + 产品创新 + 合规化」与美妆「国货替代 + 渠道红利 + 监管规范化」**机制不同**，
    且验证数据不同（医美无统一官方口径 vs 化妆品有国家统计局零售额）→ **倾向独立**，但**由 Canonical Decision 裁决**

### 5.5 免税 / 疫后修复：`003` vs `004` —— `CF011`

- `CF011`（UNRESOLVED）：是否属同一「服务消费」结构
  - P1 两个独立结构：免税 = **政策额度放开 + 出境消费回流替代**（验证：离岛免税销售额）；
    疫后修复 = **防控优化后补偿性需求释放**（验证：旅游人次与社零）→ 启动锚点、政策主体、验证数据均不同
  - P2 同一服务消费 Campaign 的两段：代表标的部分重叠（中国中免）；两段在「出行恢复」维度上连续
- **Intake 判断**：
  - `003`（**9 ev / 9 IG** —— 本包 IG 最多）· `004`（**11 ev** —— 本包 evidence 最多）→ **均达标**
  - `003` 的**结构弱点**：`security_ids` 仅 **1 个**（中国中免），**A 股广度严重不足**；
    且 2022 年降温数据仅取得媒体转述（`known_gaps[5]`）
  - `004` 的**结构弱点**：**主升段仅约 1–2 个月**，若严格按「持续性」标准可能被判定为 `OBSERVATION_ONLY`
  - **政策额度放开 / 出境回流替代 / 疫后补偿需求三者机制确实不同** ✓ → **倾向两个独立结构**，
    但**由 Canonical Decision 裁决** → **`CF011` 移交**

### 5.6 以旧换新：`011`（2024–2025）

**链条完整性检查**（这是本包最强的一条证据链）：

```
政策定调 2024-03-13（国发〔2024〕7 号）
 → 资金落地 2024-07-25（发改环资〔2024〕1104 号，1500 亿元）
 → 补贴细则 2024-08-24（8 类家电补 15%/20%）
 → ★ 官方需求验证：2024-09~12 零售额同比 +20.5% / +39.2% / +22.2% / +39.3%
 → 全年 10307 亿元、+12.3% 创历史新高；商务部口径 8 类家电超 6000 万台、超 2600 亿元
 → ★ 市场响应：2024-10-08 家电龙头区间高点
 → 降温：2025 年 Q3 起推总口径零售额明显回落
```

| 检查 | 结果 |
|---|---|
| 是否仅凭政策出台就认定主题成立 | ✅ **否** —— 有**官方销量验证**（连续 4 个月双位数增长）+ **市场响应**（2024-10-08 高点）两级验证 ✓ |
| `CF010`（UNRESOLVED） | 补贴驱动的**需求前置** vs **真实需求复苏**，是否应拆分。Worker 按「一个 Campaign、双驱动叠加」提交，理由：两者**时间完全重叠、代表标的相同**，拆分将违反 Q5 → **移交 Canonical Decision** |
| 反面对照 | ★ 2025 年**政策密集但无 Campaign**（`exclusion X001` / `CF012`）：社零 +3.7%、中证白酒 -16.2%、中证食品饮料 -12.0%，**年内高点恰在政策公开前后** → 是本包「**政策发布 ≠ 主题形成**」纪律的核心证据 ✓ |
| Beta 风险 | ⚠️ 峰值日 **2024-10-08 与全市场「9·24 行情」重合** → 存在 Beta Contamination，Worker 已将峰值置信度标为 **medium** 并保留 `CF010` ✓ |

> **判定：`011` 的「财政补贴 → 官方销量 → 行业/A 股响应」链条完整，足以支持独立 Campaign** ✓
> （但 Beta 风险与补贴/真实需求拆分须由 Canonical Decision 处理）

### 5.7 量贩零食 / 宠物食品：`012` / `013`

| 检查项 | `012` 量贩零食 | `013` 宠物食品 |
|---|---|---|
| ev / IG | 6 / 6 | **3 / 3** |
| PIT | 1 | **0** |
| **启动时间** | ⚠️ **年度级**（`2023-01-01~2023-12-31` DATE_WINDOW；门店总数**缺官方统计口径**） | PHASE_WINDOW（无明确启动事件锚点） |
| **end 是否确立** | ⚠️ **未确立**（lifecycle 末段 `UNKNOWN`；渠道龙头 2025-08 仍创区间新高） | ⚠️ 结束状态未知 |
| status / confidence | PROVISIONAL / medium | **INSUFFICIENT / low** |
| 板块广度 | 2 个标的（万辰集团 + 盐津铺子） | 2 个标的（乖宝宠物 + 中宠股份） |
| 官方一手证据 | 有（公司业绩） | ❌ **无任何一手官方证据**（`known_gaps[9]`） |

> **判定**：
> - `012` → **具备进入条件但附条件**（`date_confidence` 须为 **low**；`end` 保留 `UNKNOWN`/NULL）；
>   **建议补官方门店统计口径以定 start**
> - `013` → **保持 `INSUFFICIENT` / Research Only** ✓（Worker 建议正确，**不得为了数量强行提升**）

---

## 6. Candidate 处置

### D. 具备进入 Canonicalization 的条件（11）

| 组 | candidate | 附带的 Conflict / 条件 |
|---|---|---|
| **证据充分** | `002` 白酒 2019–2021 · `005` 非瘟猪周期 · `006` 猪周期反转 · `010` 国货美妆 | — |
| **附明确条件** | `001` 白酒 2016–2018（Priority B，证据弱于 002） | `CF001` `CF002` |
| | `003` 离岛免税（**sec = 1，A 股广度不足**） | `CF011` |
| | `004` 疫后修复（**主升仅 1–2 个月**） | `CF011` `CF004` |
| | `008` 白电（**PIT = 0**、命名存疑） | **`CF005`（P0）** `CF008` |
| | `009` 医美（跨族归属） | **`CF007`** `CF009` |
| | `011` 以旧换新（**Beta 风险**） | `CF010` `CF012` |
| | `012` 量贩零食（**start 年度级**、end 未确立 → `dc = low`） | `Q011` |

### E. 应保持 Research Only / 建议补证后进入（2）

| candidate | 判定 | 理由 |
|---|---|---|
| **`007` 小家电 / 清洁电器** | **建议补证后进入** | **仅 4 ev / 3 IG**（本包最少之一）· **PIT = 0** · 渗透率核心机制**缺一手量化数据**（`known_gaps[3]`）→ 证据强度明显低于其余候选 |
| **`013` 宠物食品** | **保持 Research Only** | `INSUFFICIENT` / `low` · **3 ev / 3 IG** · **PIT = 0** · **无任何一手官方证据** · 板块广度不足（2 标的）· 持续仅 2–3 季度（接近 `OBSERVATION_ONLY` 边界） |

### F. 12 条 Conflict 的优先级与须交 Canonical Decision 的事项

| 优先级 | Conflict | 须裁决的事项 |
|---|---|---|
| **P0** | **`CF002`** | 白酒 2016–2018 与 2019–2021：**两个独立 Campaign vs 同一 Theme Cycle 的两段** |
| **P0** | **`CF006`** | 猪周期：**「自然周期是否纳入 Campaign 宇宙」的判据**（`Q001`）+ 两轮是否合并（含 4 个 position） |
| **P0** | **`CF005`** | 白电驱动归因：**地产后周期 vs 出口替代**（P3 已给出地产传导的反证）→ 可能需**修改候选命名** |
| **P0** | **`CF008`** | 小家电 vs 白电：**两个 Campaign vs 同一 Campaign 的两个 sub-theme**（含 3 条共享 evidence 的 1:1 归属） |
| **P1** | `CF001` | 白酒的 `classification`（industry_trend vs theme_campaign） |
| **P1** | `CF007` | 医美的 Macro Theme 归属（**消费 vs 医药健康**）—— CMTR v1 不回答 |
| **P1** | `CF009` | 医美与国货美妆是否合并；医美监管的双重性质 |
| **P1** | `CF010` | 以旧换新：补贴驱动 vs 真实需求是否拆分；**2025 家电零售 +11% vs -4.3% 口径冲突** |
| **P1** | `CF011` | 免税 vs 疫后修复是否同属「服务消费」结构 |
| **P1** | `CF004` | **宏观消费数据改善 ≠ 具体消费行业启动**（本任务最核心的方法论冲突；Worker 已用「宏观数据仅作 context」处理） |
| **P2** | `CF003` | 2021 年规上白酒收入/利润增速口径（统计局 vs 茅台年报引述） |
| **P2** | `CF012` | 2025 年消费政策密集 vs 消费板块全年下跌（**政策发布 ≠ 主题形成**的对照样本） |

> **12 条全部移交，本轮一条未消解。**

---

## 7. Intake 层面五项检查

| 检查 | 结果 |
|---|---|
| **完整性** | ✅ Protocol §5.3 的 11 个文件齐备；manifest 16 个顶层字段齐备；各候选 `drivers` 四问、`why_campaign` / `why_not`、`lifecycle` 均填充 |
| **一致性** | ✅ `quality_summary.counts` 与实际一致（C21 PASS）；`confidence_distribution` 5 high / 7 medium / 1 low 与 13 候选一致；枚举全部合法 |
| **可追溯性** | ✅ evidence → source 全链可达；`subsequent` / `retrospective` **全部带 PIT note**；**官方一手来源占比为本轮四包最高**（`regulator` 36 / `tier 1` 42）；conflict positions 亦挂来源且**无悬空** ✓ |
| **冲突识别** | ✅ 12 条冲突，**9 UNRESOLVED + 2 KEEP_BOTH + 1 KEEP_BOTH**（`CF003`/`CF004`/`CF012` 为 KEEP_BOTH），全部保留双方；**8 条 `contradicting` 证据**单列保留 |
| **进入 Canonicalization 的条件** | ✅ 见 §6 D / E |

**独立性纪律**：`independence_group` 按来源机构分组；`macro 数据一律 context 角色`（`CF004`）；
**未用「涨跌幅」反推主题**（0 条）✓

---

## 8. I. 独立工程 / Protocol 问题

| # | 问题 | 定性 | 是否阻塞 | 处置 |
|---|---|---|---|---|
| **I1** | **`source_type` 缺少「指数编制机构 / 行情数据商」专门类型** | **Schema 表达损耗** | ❌ 不阻塞 | 实测本包 4 处：`S007` **MSCI**（`other`/tier 2）· `S065` 东方财富行情接口 · `S066` 腾讯财经行情接口（均 `website`/tier 2）· `S074` 猪易网（`website`/tier 3）。<br>**影响**：仅为**类型标签的表达损耗**，`publisher` 字段完整承载机构名，**可追溯性未受损**（C08 tier 校验通过、tier 与语义一致）。<br>→ **记录即可，不修改 Schema** ✓（符合用户指示） |
| **I2** | **`MT007` 商贸零售 未解析**（提案级 taxonomy gap） | **taxonomy 覆盖缺口** | ❌ 不阻塞（候选 `012` 经 `消费` 解析 ✓） | 记录；**本轮不扩展 taxonomy**。若后续认为需为「商贸零售」设子主题，须另起 taxonomy 轮次 |
| **I3** | **跨任务「市场关注」口径差异** | **跨任务治理问题** | ❌ 不阻塞 | R01-03 起采用更严格口径（「市场关注」需 A 股市场侧证据支撑）；R01-01 / R01-02 未采用同一口径。**本轮不将该标准固化为新 Protocol**（符合用户指示）→ **记录为跨任务治理问题**，待 R01 完成后统一 |
| **I4** | Worker 报告的 `24 checks` vs ThreeC `C01–C25` | **口径差异** | ❌ 不阻塞 | `24` 属 Worker Workspace 口径；ThreeC 当前为 **C01–C25**（含 C25 Strict Draft-07）。**以 ThreeC 当前 Validator 为准** ✓ |

---

## 9. 本轮严格未做

- ❌ 未创建 Canonical Campaign · 未导入 DB · 未修改既有 Campaign
- ❌ 未修改 taxonomy（CMTR v1 只读）· 未修改 Protocol / Schema / Validator / Package
- ❌ 未刷新 Structural Analogy / Time Observation
- ❌ 未启动 R01-05 / R01-06 的 ThreeC Intake
- ❌ 未消解任何 Conflict · 未提前决定任何 Campaign 的合并 / 拆分
- ❌ 未把 R01-03 的「市场关注」更严口径固化为新 Protocol
