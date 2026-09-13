# Theme Lifecycle Model v0.2（研究级，2022-2024 统一建模）

> 本文档在 v0.1 基础上固化 **Research Signal** 与 **Campaign Phase** 的边界，统一 2022、2023、2024 三案例生命周期建模。
> **本模型是研究状态，不是交易信号；不做预测/概率/seasonality。**
> 不创建正式 `theme_cycles` 表；以 **research-level `theme_cycle_id`** 标注。

---

## 1. 状态分层（严格区分）

### 1.1 Research Signal（研究信号层）

属于 **Rule / Theme / ThemeCycle research layer**，表达"尚未形成正式 Campaign，但已值得开始观察"。

| Signal State | 含义（research-level，非交易） |
|---|---|
| **EARLY_SIGNAL** | 最早值得观察：出现可辨识的、属于该主题的异动/关注（可早于正式催化） |
| **THEME_FORMING** | 主题初具雏形：龙头/叙事开始确立，但尚未形成广泛识别 |
| **CONFIRMATION_CANDIDATE** | 确认候选：出现可能升级为正式 Campaign 的信号，待验证 |

**关键约束**：Research Signal **不属于 Campaign Phase**，不得写入 `campaign_phases` 表。

### 1.2 Campaign Phase（战役阶段层）

属于 **Historical Campaign** 正式阶段，记录已确认的市场行情结构。

| Phase State | 含义（research-level，非交易） |
|---|---|
| **MAIN_RISE** | 主升：板块/核心样本持续一致上行 |
| **PEAK** | 主升顶点（板块 peak 或 cluster） |
| **RETRACEMENT** | 回撤：价格/题材回撤，但不足以确认 Campaign 结束（新增） |
| **DECLINING** | 衰减：主题持续性明显下降，丧失主导权 |
| **SECONDARY** | 次级活跃 / 二次新高（可能仅部分个股） |
| **ENDED** | 主题失去持续主导，进入冷却或结束 |

**RETRACEMENT vs DECLINING 严格区分**：
- **RETRACEMENT**：正常技术回撤，主题可能恢复；幅度/时间未破坏主升结构
- **DECLINING**：主题持续性明显下降，资金持续流出，难以恢复主升

### 1.3 Opportunity State（机会状态分类）

作为 research classification 统一枚举：

```
EARLY_SIGNAL → THEME_FORMING → CONFIRMATION_CANDIDATE → CONFIRMED → 
MAIN_RISE → PEAK → RETRACEMENT → DECLINING → SECONDARY → ENDED
```

**必须明确**：这些不是交易信号，仅为研究描述。

---

## 2. 时间字段体系

不要假设一个 `start_date` 解决所有问题。研究层允许记录：

| 字段 | 含义 | 所属层级 |
|---|---|---|
| `early_signal_date` | 最早可辨识信号日期 | Research Signal |
| `theme_formation_date` | 主题形成日期 | Research Signal |
| `campaign_start_date` | Campaign 正式启动日期 | Campaign |
| `broad_confirmation_date` | 广泛确认日期 | Campaign Phase |
| `peak_date` | 峰值日期（可为 cluster） | Campaign Phase |
| `first_decline_date` | 首次明显回撤日期 | Campaign Phase |
| `main_end_date` | 主升结束日期 | Campaign Phase |
| `secondary_start_date` | 次级行情启动日期 | Campaign Phase |

**HistoricalCampaign 正式事实层**暂时保持：
- `start_date` / `end_date` / `peak_date`

除非审查证明必须调整正式模型，优先通过 **Research Signal / Campaign Phase** 表达额外时间信息。

---

## 3. Theme Cycle v0.2（结构）

```
Theme Cycle                            例：auto_intelligence_2023
│
├── Research Signals（不属于 Campaign Phase）
│   ├── EARLY_SIGNAL (date)
│   ├── THEME_FORMING (date)
│   └── CONFIRMATION_CANDIDATE (date)
│
├── Campaign 1（Smart Driving）
│   ├── MAIN_RISE
│   ├── PEAK (cluster 允许)
│   ├── RETRACEMENT / DECLINING
│   └── ENDED
│
└── Campaign 2（Huawei Auto）—— 同 theme family
    ├── Research Signals (early/formation/candidate)
    ├── MAIN_RISE
    └── ...
```

- **theme_cycle_id**：research 级标签（`auto_policy_2022`、`auto_intelligence_2023`、`robotaxi_2024` 等），不改 schema。
- 一个 Theme Cycle 可含多个 Campaign；Campaign 可有多个 Phase/Signal。
- **Campaign Overlap**：允许旧 Campaign 尚未正式 End，新 Campaign 已开始 Early Signal。

---

## 4. Theme Drift（主题漂移）

> **Theme Drift**：核心叙事 / 核心股票发生迁移，但属于同一大主题家族（same_theme_family）。

- 2023：7月 Smart Driving / Robotaxi / L3（德赛/浙江/万安/众泰）→ 9月 Huawei Auto / AITO M7 / ADS2.0（赛力斯/江淮/德迈仕/铭科/华阳）。
- 方向相邻 → same_theme_family；具体 Campaign 与 Leader 更替。
- 不作"强行归类"，允许 Campaign 含多个 Theme。

**判定标准**：
1. 核心叙事明显迁移（如 L3政策 → 华为新车）
2. 核心股票明显更换（德赛/浙江 → 赛力斯/江淮）
3. 催化事件类型变化（政策吹风 → 产品发布）

---

## 5. Campaign Overlap（重叠）

> **Campaign Overlap**：新旧 Campaign 时间部分重叠，但关注中心明显转移。

- 2023 例：08-29→09-12 期间，旧 Smart Driving（德赛/浙江）与华为汽车早段并存。
- **不是模型错误**；为避免重叠而修改 Campaign 日期是违规的。
- 记录 overlap + attention shift（如 09-08 浙江世宝涨停＝旧 SD 反抽，同时华为汽车早段起步）。

**约束**：不强迫 `A.end < B.start`，允许时间重叠但需记录 attention_shift。

---

## 6. Campaign End 判定标准（严格区分）

| 概念 | 定义 | 判定标准 |
|---|---|---|
| **First Decline** | 第一轮明显回撤 | 价格/题材首次显著回撤，但结构未破坏 |
| **Retracement** | 正常回撤 | 幅度/时间未破坏主升结构，可能恢复 |
| **Declining** | 持续衰减 | 主题持续性明显下降，资金持续流出 |
| **Main Campaign End** | 主升结束 | 主要行情结构被破坏，难以恢复 |
| **Theme Cycle End** | 主题周期结束 | 整个主题家族不再产生新的明显 Campaign |

**禁止**：
- 单日跌停 = Campaign End
- 观察窗口结束 = Campaign End

**必须找**：
- 最后一次板块同步
- 最后一次主题扩散
- 最后一次有效新高
- 最后一次有效催化

允许 **decline_cluster**（多日期候选）。

---

## 7. 三案例生命周期（统一建模）

### 2022（theme_cycle_id = auto_policy_2022）

**Research Signals**：
- EARLY_SIGNAL: 04-27（行业修复/Setup，不等于 Theme Campaign Start）
- THEME_FORMING: 05-23（国常会购置税600亿政策）

**Campaign Phases**：
- Campaign Start: 05-23（政策催化）
- Broad Confirmation: 06-01（细则落地次日整车集体涨停）
- Main Rise: 05-23 → 06-28
- Peak: cluster {06-23, 06-28}（龙头与行业代理峰值可能不同）
- Retracement: 07月（正常回撤）
- Declining: 08月（decline_cluster，08-01二高点后）
- End: 08月后续（最后一次板块同步/有效新高）

**特殊处理**：
- 05-31（财政部/税务总局公告）= policy detail / confirmation event，不与 05-23 合并
- 中通客车 classification = event_driven，不并入 Main Auto Theme

### 2023（theme_cycle_id = auto_intelligence_2023，含两 Campaign）

**Campaign 1（Smart Driving）**：
- Research Signals: 06-12（预热）→ 06-21（L3吹风）
- Campaign Start: 06-21
- Confirmation: 07-03
- Main Rise: 07-03 ~ 07-19（SDIdx +33.5% vs AUTO+1.3%）
- Peak: 07-12~19
- Secondary: 08-04
- Cooling/Decline: 08下-09上
- End≈09-12（德赛/浙江见顶转跌）

**Campaign 2（Huawei Auto）**：
- Research Signals: 
  - EARLY_SIGNAL Candidate: 08-29（存在市场Beta，需排除 contamination）
  - THEME_FORMING: 09-04（赛力斯首次明显突破）
- Campaign Start Candidate: 09-12（问界M7 catalyst）
- Broad Confirmation: 09-18（华为汽车核心扩散+多股同步）
- Main Rise: 09下-10（至10-31 仍升）

**Campaign Overlap**：08-29~09-12 两 Campaign 时间重叠；attention shift 向华为汽车。

### 2024（theme_cycle_id = robotaxi_2024）

**Research Signals**：
- EARLY_SIGNAL: 07-08（Early Start）

**Campaign Phases**：
- Broad Confirmation: 07-10
- Main Rise: 07→
- Peak: 08-05
- First Decline: 08-06
- Main Campaign End: 08-23（Major Breakpoint）
- Secondary: 09-05~06（Weak Secondary Campaign Candidate）

**当前结论**：07-08→08-23 为 Main Campaign；09-05/06 为 Weak Secondary Candidate。

---

## 8. 是否进入正式 Schema（本阶段评估）

- **维持现状**：2022/2023/2024 三案例均能自然表达 Theme Cycle → Campaign → Phase/Signal，无需强行修改历史数据。
- **不创建** `theme_cycles` 表、`campaign_relations` 表。
- **不修改** 正式 schema；保持 research-level 标注。
- **未来扩展**：新增历史案例时，若 research-level 标签不足，再提出最小 schema。

---

## 9. 纪律

- Opportunity State / Theme Cycle 均为研究描述，非交易信号。
- 先敌view下，Early Signal/Formation/Confirmation 用 Point-in-Time 信息判断（不事后倒推）。
- 不计算 seasonality_score / win_rate / probability / predictive_model。
- 宁可 unknown / candidate / no_clear_campaign，也不伪装 verified。
- 真实历史事实优先，不为支持 Rule 而修改研究结果。
