# Medical Health Campaign Boundary Decision v0.1

> **性质**：Research-level **边界决策报告**。**不是**数据录入、**不是**创建 Campaign、
> **不是**修改 DB / export / schema / UI。
> **唯一目标**：回答 —— **如果 ThreeC 第一次进入非汽车行业，应该生产什么粒度的数据？**
> **日期**：2026-09-14
> **上游依据**：`Medical_Health_Theme_Cycle_Discovery_v0.1.md`（医药发现）、
> `theme_campaign_separation_v1.md` **v1.1**（Gate Q1–Q5 + Theme Cycle Pattern + Lifecycle Measurement Rule）、
> `docs/THEME_CAMPAIGN_MODEL_AUDIT.md`（分层模型审计）。
> **纪律**：PIT 视角 · 区分事实与解释 · 不预测 · 不含买卖建议 · 未知即标 `Unknown` ·
> **不因「方便展示」而增加 Campaign**。

---

## 0. 前置：数据能力与一处更正（Errata）

### 0.1 数据能力现状（决定置信度上限）

| 证据类型 | 可用性 |
|---|---|
| 官方政策事实（Tier 1） | ✅ 可核（4+7 集采、医保谈判、集采扩围、中医药政策） |
| 行业景气数据（Tier 3） | ✅ 部分可核（研发投入、CRO 收入、CXO 业绩） |
| 当期市场评论（解释） | ⚠ 可用但属**解释**，仅用于还原 PIT 认知 |
| **ThreeC 行情数据库（医药）** | ❌ **0 条**（`market_series` 32 条全为汽车） |
| 个股历史高点/区间收益（本地） | ❌ **不可用**（本次以公开来源核对，标注为二手） |

> **硬约束**：Gate 的 **Q3（持续性）/ Q4（生命周期）无法本地验证** →
> 所有 Campaign 判定的置信度**上限为 medium**；本轮**不产生任何 `C-` 级 Campaign**。

### 0.2 ⚠ Errata：更正上游报告的一处推断

`Medical_Health_Theme_Cycle_Discovery_v0.1.md` §3.3 曾写：

> 「板块口径顶 2021-07-01 / **成长赛道口径顶 2022-01-04**（滞后约半年）」

**该"滞后半年"的推断不成立，应更正。** 依据本次核对：

| 标的（各自口径） | 历史高点 | 来源 |
|---|---|---|
| 英科医疗（疫情医疗·手套） | **2021-01-25**（296.99 元） | 公开行情（T3） |
| 疫苗指数 | 2020-07 / 08 | 券商周报（T3） |
| 医药板块（申万医药生物） | **2021-07-01** | 多来源（T2/T3） |
| 药明康德（CXO） | **2021-07-16**（172.49 元） | 公开报道（T2/T3） |
| 爱尔眼科 / 迈瑞医疗 / 通策医疗 | 2021Q3 | 公开报道（T2） |
| 中药 | 2021Q4 大涨；2022Q4 再涨（独立节奏） | 券商/媒体（T3） |

- **「A 股 CXO 板块 18 只股票的历史高点停留在 2021 年，占总数八成以上」**（公开报道）
  → 成长赛道**并未**滞后到 2022 年见顶。
- 此前引用的「创新药概念指数 2022 区间最高价 = 2022-01-04」**只是该区间起点恰为区间最高**，
  不等于"指数在 2022-01 见顶"。**属引用误读。**

**更正后的准确图景**：不同 Campaign 的顶**分散**在
**2021-01（疫情医疗）→ 2021-07（板块 / CXO / 器械 / 服务）→ 2021Q4–2022（中药独立节奏）**。
**这反而更支持「Parallel Cycle + 各 Campaign 独立 Peak」的判断**（见 §2）。

> 已在 `Medical_Health_Theme_Cycle_Discovery_v0.1.md` §3.3 加入同款更正注记。

---

## 1. Executive Summary

**一句话回答本任务的核心问题：**

> **ThreeC 第一次进入非汽车行业，应生产「Campaign 级」粒度 —— 但首批只做
> 1 个正式 Campaign（创新药 / CXO 主线）+ 2 个 Campaign Candidate（疫情医疗、中药），
> 并把 CXO 明确钉在 Sub-theme 层，不单独立为 Campaign。**

| 决策项 | 结论 |
|---|---|
| Theme Cycle 是否确认 | ✅ **KEEP**（结构成立；边界为 Candidate，待行情校准） |
| Pattern | **Parallel Cycle**（各 Campaign 独立生命周期、**Peak 时间分散**） |
| Candidate A 创新药 / CXO | **Campaign**（Cycle 的 **主线路**）；其中 **CXO = Sub-theme，不独立** |
| Candidate B 疫情医疗 | **Campaign Candidate（Case B，medium）** —— 非"异常加速阶段" |
| Candidate C 中药 / 中医药 | **Campaign Candidate（Case B，medium-low）**；归属（Sub-theme vs 独立 Macro Theme）**待人工决策** |
| 推荐结构 | **Version B′（改良版）**：1 正式 Campaign + 2 Candidate（不是 Version A 的压平，也不是 Version B 的冒进） |
| 首个数据生产粒度 | **Campaign 级**（Campaign → Sub-theme → Phase → Driver），**不做 Sub-theme 级独立生产** |

---

## 2. Theme Cycle Decision

### 2.1 决策：**KEEP**

| 项 | 内容 | 状态 |
|---|---|---|
| **Theme Cycle** | `medical_structural_upgrade_2019_2022` | **KEEP**（research-level 标签，不入库） |
| **Macro Theme** | 医药健康（对应产品侧 `th_pharma`） | **KEEP** |
| **Pattern** | **Parallel Cycle**（§2.2 论证） | **Confirmed**（形态判定） |

**为什么不 REJECT**：存在跨 4 年的、可描述的连续叙事，且**三个驱动层（Policy / Industry / Capital）均有 PIT 可核证据**（见发现报告 §4 PIT Timeline）。

**为什么不 NEED MORE EVIDENCE（对 Cycle 本身）**：Cycle 的**存在性**不依赖行情数据 ——
它由**政策与产业事实**支撑（4+7 → 科创板 → 医保谈判鼓励创新 → 集采扩围 → 估值出清），
且**分化的子行业表现**（2019 医疗服务 +59% vs 中药跑输；2021 中药 +31.7% 唯一上涨）本身就是结构的证据。

**但边界（各阶段日期）必须标 Candidate** —— 因为缺本地行情数据。

### 2.2 Pattern 判定：Parallel（附证据）

| 判据（v1.1 §5） | 医药是否满足 | 证据 |
|---|---|---|
| 多个叙事同时存在 | ✅ | 2020 年 TOP20 同时包含疫情医疗（英科 +1428%、振德、硕世、达安、智飞）**与**消费医疗/CXO（通策 +170%、美迪康/泰格/昭衍） |
| Peak 时间可能不同 | ✅ **关键** | 疫情医疗 **2021-01** ‖ 板块/CXO **2021-07** ‖ 中药 **2021Q4–2022** |
| 不要求相互替代 | ✅ | 疫情医疗回落（2021 全年 −84%）期间，CXO 仍创新高（2021-07-16） |

> **Parallel 不是"形式分类"，而是有实证错位支撑** —— 三类 Campaign 的顶相差可达 **半年**。

### 2.3 生命周期各阶段（Confirmation 分级）

| 阶段 | 候选时间 | 级别 | 依据 |
|---|---|---|---|
| **Formation** | 2019Q1–Q3 | **Confirmed** | 医保局体制（2018-05-31）+ 科创板开板（2019-07-22）为 Tier 1 事实；市场开始区分"创新 vs 仿制"有 PIT 报道支撑 |
| **Confirmation** | **2019-11-28** | **Confirmed** | 医保谈判结果：150→97、新增平均降幅 60.7%、**PD-1 首入医保**、**12 个国产重大创新药谈成 8 个**（Tier 1 官方） |
| **Expansion** | 2020Q1–2021H1 | **Candidate** | 疫情 + 流动性 + CXO 景气（有 T3 数据），但**区间边界需行情验证** |
| **Peak** | 2021-07-01（板块口径） | **Candidate** | 多来源一致（T2/T3），**本地无法验证** |
| **Decline** | 2021H2–2022 | **Candidate** | 集采扩围（人工关节 2021-09 / 胰岛素 2021-11）为 Tier 1；跌幅数据为 T3 |
| **End** | **未确认** | `Unknown` | 2022 年末估值降至近 10 年低位且政策转暖，**不足以判定 Cycle End** |

---

## 3. Campaign Candidate Review

### 3.1 Candidate A — 创新药 / CXO（2019–2021）

**先厘清一件事**：Candidate A **就是本 Theme Cycle 的主线路**，
它不是"从别的主题里拆出来的候选"，故其**作为 Campaign 的地位不需要 Gate 证明**（它是基线）。

真正需要 Gate 回答的是 **§四.1：CXO 是否独立**。

#### A-1 主线（创新药产业链升级）：**Campaign**（Cycle 的 primary line）

| Gate | 判定 | 依据 |
|---|---|---|
| Q1 Attention Center | ✅ | 2019–2021 医药的注意力中心即"创新/研发"叙事 |
| Q2 Representative Assets | ✅ | 恒瑞 / 药明康德 / 泰格 / 凯莱英 / 康龙化成 / 百济神州 |
| Q3 Persistence | ✅ | 2019–2021H1，约 2.5 年（T3 支撑，边界待验证） |
| Q4 Lifecycle | ✅ | Formation 2019 → Rise 2019H2–2020 → Peak 2021-07 → Decline 2021H2+ |
| Q5 Residual | — | 它是基线，无需残差检验 |

→ **`Campaign`**（主线路）。

#### A-2 CXO：**Sub-theme**（**不独立**）—— 回答 §四.1

| Gate | 判定 | 依据 |
|---|---|---|
| **Q1 Attention Center** | ❌ **否** | CXO 与创新药**共享同一资金池与同一叙事**（"创新药产业链" / "卖水人"）；机构持仓高度重叠（葛兰等同一批基金同时重仓药明、泰格、凯莱英、康龙化成）→ **触发 v1.1 Q1 Anti-example** |
| **Q2 Representative Assets** | ❌ **否** | 与主线龙头**高度重叠**（药明康德同时是"创新药"与"CXO"的代表标的） |
| **Q3 Persistence** | ❌ **否** | 与主线**同期**：CXO 回落与板块回落同步 |
| **Q4 Lifecycle** | ❌ **否** | 药明康德高点 **2021-07-16** ≈ 板块高点 **2021-07-01**（相差 15 天）→ **生命周期高度一致**；"CXO 板块 18 只股票历史高点停留在 2021 年，占八成以上" |
| **Q5 Residual** | ❌ **否** | 去掉 CXO 后，"创新药"主线**不完整**（CXO 是主线的产业链组成部分） |

→ **`Sub-theme`**（创新药产业链内的专业化环节），**不单独立为 Campaign**。

> ⚠ **重要反例澄清**：2022 年 CXO"业绩 +58.34%、估值 103x → 29.95x"看似独立，
> 但这是**估值杀**（Capital 驱动），**不是独立生命周期** → 不构成独立 Campaign 的依据。

---

### 3.2 Candidate B — 疫情医疗（2020–2021）

> **任务特别要求**：判断它是「独立事件驱动 Campaign」还是「原 Cycle 的异常加速阶段」。

| Gate | 判定 | 依据 |
|---|---|---|
| **Q1 Attention Center** | ✅ **是** | 全球防疫物资 / 检测 / 疫苗 是**完全独立于"创新药/CXO"**的注意力中心 |
| **Q2 Representative Assets** | ✅ **是** | 英科医疗 / 振德医疗 / 硕世生物 / 达安基因 / 智飞生物 —— 与 药明/泰格/恒瑞/通策 **几乎零交集** |
| **Q3 Persistence** | ✅ **是**（独立节奏） | 2020-01 → 2021，约 12–18 个月，且**节奏与主线相反** |
| **Q4 Lifecycle** | ✅ **是** | 可独立描述：Formation（2020-01 疫情）→ Rise（2020H1）→ **Peak 2021-01-25（英科 296.99 元）** → Decline（2021 全年 **−84%**，2021-12-31 收 47.00 元） |
| **Q5 Residual Test** | ✅ **是** | **去掉疫情医疗后，医药 Theme Cycle 仍完全成立**（创新药/CXO + 消费医疗 + 中药 均有独立政策与产业驱动） |

**是否为"异常加速阶段"？→ 不是。** 三条反证：

1. **龙头组完全分离**（Q2）—— 若是同一 Campaign 的加速阶段，龙头应重叠。
2. **驱动不同源**（External 疫情实物需求 vs Policy 医保改革 + Industry 研发外包）。
3. **Peak 与 Decline 节奏相反**：疫情医疗 **2021-01 见顶、2021 全年深跌**；
   而主线同期（2021H1）**仍在上涨**，直到 2021-07 才见顶。
   → 若为同一 Campaign，不可能一个跌 84% 而另一个创新高。

→ **`Campaign Candidate`（Case B，置信度 medium）**。

> **为何不升 Case C（正式 Campaign）**：Q3/Q4 的**精确边界**缺本地行情验证；
> 且需排除"疫情为全国 β 事件"的污染（任务外的下一步工作）。

---

### 3.3 Candidate C — 中药 / 中医药（2021–2022）

> **任务特别要求**：不要因为涨幅判断。

| Gate | 判定 | 依据（**尽量不依赖涨幅**） |
|---|---|---|
| **Q1 Attention Center** | ✅ **是** | 拥有**独立政策体系**：中医药专属政策（2021-12-31 国家医保局 + 国家中医药管理局《关于医保支持中医药传承创新发展的指导意见》、《"十四五"中医药发展规划》），**与创新药/集采主线不同源** |
| **Q2 Representative Assets** | ✅ **是** | 以岭药业 / 众生药业 / 康缘药业 / 片仔癀 / 华润三九 / 同仁堂 —— 与医药核心资产**基本不重合** |
| **Q3 Persistence** | ✅ **是** | 2021Q2 / Q4 上涨 → 2022H1 调整 → 2022Q4 再涨，**跨年且多次启动** |
| **Q4 Lifecycle** | ✅ **是** | 可独立描述：2021Q2 起势 → 2021Q4 政策催化高潮 → 2022H1 调整 → 2022Q4 再启动 |
| **Q5 Residual Test** | ✅ **是** | 去掉中药，剩余 Theme Cycle 完全成立 |

**不依赖涨幅的独立证据（三支柱）**：

1. **政策独立**：中医药有专属政策体系（非"医药集采"的一部分）。
2. **定价机制独立**：多数中药品种**未进入集采，可自主定价**（不受集采压制）—— 这是**结构性差异**，
   而非"涨得多"。
3. **估值体系独立**：中药长期 **20–30x PE** vs 创新药/CXO **上百倍** → 属**不同的定价逻辑**。

→ **`Campaign Candidate`（Case B，置信度 medium-low）**。

**⚠ 但存在一个未决的模型边界问题**：中药应归属
**（i）医药健康下的 Sub-theme**，还是 **（ii）独立 Macro Theme「中医药」**？
其政策体系与定价机制均独立 → 倾向（ii），但**本轮不擅自决定** → 记入 Unknown Register（U-C1）。

**⚠ 市场存在分歧**（应如实记录）：有人认为"中长期趋势拐点已现"，也有人认为
"更多是反弹，只是相对其他医药板块更具政策安全性"。→ 记为 `CONFLICT`，**不取单一结论**。

---

### 3.4 Candidate 汇总

| Candidate | Gate 结论 | 判定 | 置信度 |
|---|---|---|---|
| **A 主线：创新药产业链升级** | 基线 | **Campaign**（primary line） | medium |
| **A-2 CXO** | Q1/Q2/Q5 均否（共享资金池 + 龙头重叠 + 同期生命周期） | **Sub-theme**（**不独立**） | **high**（Anti-example 适用明确） |
| **B 疫情医疗** | Q1–Q5 全部「是」 | **Campaign Candidate（Case B）** | medium |
| **C 中药 / 中医药** | Q1–Q5 全部「是」（政策/定价/估值三重独立） | **Campaign Candidate（Case B）**；归属待决策 | medium-low |

**明确判为 Sub-theme（不设 Candidate）**：医疗器械 · IVD/检测 · 医药商业/药店 · 原料药 ·
创新药出海/License-out · 新冠小分子产业链 · **CXO**。

---

## 4. Recommended Boundary

### 4.1 Version A（最保守）

```
医药健康（Macro Theme）
└── Theme Cycle: medical_structural_upgrade_2019_2022（Parallel）
    └── Campaign 1（唯一）：创新药产业链升级（2019–2021）
        ├── Sub-theme: 创新药
        ├── Sub-theme: CXO（CRO/CDMO）
        ├── Sub-theme: 创新药出海 / License-out
        ├── Sub-theme: 消费医疗（医保免疫）
        ├── Sub-theme: 医疗器械 / IVD
        ├── Sub-theme: 中医药      ← 压平在此
        └── Sub-theme: 疫情医疗    ← 压平在此
```

**优点**：最稳妥，绝不冒进；数据量最小。
**缺点**：**丢失信息** —— 把"独立注意力中心 + 独立龙头组 + **错位半年的 Peak**"压平为 Sub-theme，
违反 v1.1 §5「Parallel Cycle 中 Peak 时间可能不同」与 Gate 的既有结论；也违反
「不得为整齐而合并」的对称原则。

### 4.2 Version B（较丰富）

```
医药健康（Macro Theme）
└── Theme Cycle: medical_structural_upgrade_2019_2022（Parallel）
    ├── Campaign 1: 创新药产业链升级（2019–2021）
    ├── Campaign 2: 疫情医疗（2020–2021）
    └── Campaign 3: 中药 / 中医药（2021–2022）
```

**优点**：忠实反映 Parallel 形态与独立 Peak。
**缺点**：把 M2/M3 **直接写成 Campaign**，**越过了 Case B → Case C 的证据门槛**
（Q3/Q4 无本地行情验证）→ **属冒进**。

### 4.3 ✅ 推荐：Version B′（改良版）

```
医药健康（Macro Theme）                         [KEEP，产品侧 th_pharma]
└── Theme Cycle: medical_structural_upgrade_2019_2022   [KEEP，research-level，Parallel]
    │
    ├── Campaign 1（正式，primary line）
    │     创新药产业链升级 · 2019–2021
    │       Sub-theme：创新药 · CXO(CRO/CDMO) · 创新药出海 · 特色原料药
    │
    ├── Campaign Candidate M1
    │     疫情医疗 · 2020–2021 · Case B · confidence: medium
    │       Sub-theme：防护耗材 · 检测/IVD · 疫苗 · 部分监护设备
    │
    ├── Campaign Candidate M2
    │     中药 / 中医药 · 2021–2022 · Case B · confidence: medium-low
    │       Sub-theme：品牌中药 · 中药创新药 · 抗疫中药
    │       ⚠ 归属待决策：Sub-theme vs 独立 Macro Theme「中医药」
    │
    └── Sub-theme only（不设 Candidate）
          医疗器械 · 医药商业/药店 · 原料药 · 消费医疗 · 新冠小分子
```

**为什么选 B′（三条理由，全部基于 Gate 而非展示便利）**：

1. **B′ 的每个层级都由 Gate 结论直接对应**：Campaign 1 = 基线；
   M1/M3 = Case B（**不升 C**）；CXO = Anti-example 判定的 Sub-theme。
   **没有为了层级好看而新增任何节点。**
2. **B′ 保留了 Version A 会丢失的关键信息**（独立 Peak 错位），
   同时**避免了 Version B 的证据越级**（Case B ≠ Case C）。
3. **B′ 与 ThreeC 既有机制零冲突**：Candidate 对应 `RC-` 前缀（研究候选），
   正式 Campaign 对应 `C-` 前缀 —— **现有 ID 设计已原生支持这种"混合粒度"**。

> **B′ 的实质 = 「1 正式 + 2 候选 + 完整 Sub-theme 层」**，
> 也就是对用户问题的回答：**首次进入非汽车行业，生产 Campaign 级粒度，但只给 1 个 Campaign 发正式身份。**

---

## 5. Unknown Register

| # | Unknown | 类型 | 为什么未知 | 需要什么才能解决 | 阻塞什么 |
|---|---|---|---|---|---|
| **U-C1** | **中药的归属**：Sub-theme of 医药健康 vs 独立 Macro Theme「中医药」 | 模型边界决策 | 中医药有独立政策体系 + 独立定价机制 + 独立估值体系 | **人工决策**（非数据问题） | 决定 M2 挂在 `th_pharma` 之下还是新建 root theme |
| U-C2 | 医药 Theme Cycle 的**精确 Start / End** | 缺失数据 | 本地无医药行情 | 录入申万医药生物（801150）等指数日线 | Cycle 边界定稿、PRE 观察区计算 |
| U-C3 | M1 / M2 / M3 的**精确 Peak 与 End** | 缺失数据 | 同上 | 各 Campaign 代表标 / 子指数行情 | Candidate → Campaign 升级 |
| U-C4 | Gate **Q3 持续性** 的量化验证 | 缺失数据 | 同上 | 区间收益 + 波动结构 | 同上 |
| U-C5 | 疫情医疗是否受**全国 β 污染** | 未做分离 | 未做 β / 行业代理对比 | 与 HS300 及行业代理对比 | M1 独立性的最终确认 |
| U-C6 | **消费医疗（医保免疫）** 的归属 | 证据不足 | 与主线共享资金池 → Q1 存疑 | 持仓集中度数据 + 人工判断 | 是否单列（当前判为 Sub-theme） |
| U-C7 | M3 的市场分歧（"拐点已现" vs "只是反弹"） | `CONFLICT` | 当时分析师意见不一致 | 后续行情（**超出本轮范围**） | M3 的最终强度标注 |
| U-C8 | 2022 年末是否已是 **Cycle End** 或新 Cycle 起点 | 窗口末端 | 后续数据不在范围内 | 2023+ 数据 | Cycle 收尾 |
| U-C9 | **器械 / IVD / 消费医疗** 是否真的只是 Sub-theme | 证据不足 | 未做独立 Gate 打分 | 各子指数行情 + 代表标 | 是否有第 4 个 Candidate |
| U-C10 | 上游发现报告 §3.3 的**引用误读**（已完成更正，但根源是二手数据） | 数据来源 | 本地无行情可复核 | 本地行情数据 | 全部日期类结论 |

---

## 6. Next Step Recommendation

### 6.1 推荐（唯一一件）

> **先做 U-C1（中药归属）的人工决策**，再做**最小行情数据准备**：
> 仅录入 **申万医药生物 + 3 个 Campaign 代表标的组**的日线（不录入完整医药历史）。

**理由**：

1. **U-C1 是纯决策问题、零数据成本**，且**阻塞数据落库位置**
   （决定 M2 挂 `th_pharma` 下还是建 root theme）→ **必须先做**。
2. 一旦归属定下，**U-C2/U-C3/U-C4 都由同一批行情数据一次性解决** ——
   它们**共享同一份数据源**，属"一次投入解三个 Unknown"。
3. **数据量极小**：1 个行业指数 + 3 组代表标（约 5–10 条 `market_series`），
   与汽车案例已有的 32 条同量级 → **不构成"大规模增加数据"**。

### 6.2 明确不做（本轮及下一步）

- ❌ 建 DB 记录 / 创建 Campaign 数据 / 修改 export / schema / UI
- ❌ 把 M1 / M2 直接升为正式 `C-` Campaign（证据未达 Case C）
- ❌ 把 CXO 单独立为 Campaign（Gate 已明确判否）
- ❌ 因"层级好看"而新增任何 Campaign 或 Sub-theme
- ❌ 一切 §十六 禁区（预测 / 概率 / 胜率 / seasonality / 荐股 / 买卖信号 / 雷达 / 通知）

### 6.3 进入数据生产的**门槛条件**（建议作为 Gate 之后的第二道关）

| 条件 | 说明 |
|---|---|
| ① U-C1 已人工决策 | 中药归属确定 |
| ② 行情数据到位 | 至少覆盖行业指数 + 各 Campaign 代表标 |
| ③ Q3/Q4 可验证 | Peak / End 能用**该 Campaign 自身口径**给出（v1.1 §6） |
| ④ 每个 Campaign ≥2 独立 Evidence | 沿用 Research Model v1.0 §5 门槛 |
| ⑤ 反 β 检查 | 与 HS300 / 行业代理对比，排除污染 |

---

## 7. 本报告明确未做的事

- ❌ 未建 DB 记录、未创建 Campaign 数据、未修改 export / schema / UI
- ❌ 未修改任何历史研究结论（仅对上游报告做**一处 Errata 更正**，见 §0.2）
- ❌ 未做预测 / 概率 / 胜率 / seasonality / 买卖建议
- ❌ 未把任何 Candidate 升级为正式 Campaign
- ❌ 未因"方便展示"而增加 Campaign

---

*本文件为 research-level 边界决策报告，不改 schema / DB / 数据 / export / 历史结论。*
*上游：`Medical_Health_Theme_Cycle_Discovery_v0.1.md` ｜
方法论：`research/research/methodology/theme_campaign_separation_v1.md`（v1.1）｜
审计：`docs/THEME_CAMPAIGN_MODEL_AUDIT.md`。*
