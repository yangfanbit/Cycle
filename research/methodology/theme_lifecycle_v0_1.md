# Theme Lifecycle Model v0.1（研究级，Pilot 1-C1.5）

> 本文档定义**调研级 Theme Cycle / Campaign / Phase 抽象模型**，用于统一 2022、2023、2024 三案例。
> **本模型是研究状态，不是交易信号；不做预测/概率/seasonality。**
> 不创建正式 `theme_cycles` 表；以 **research-level `theme_cycle_id`** 标注。

---

## 1. Opportunity State（研究状态）

| State | 含义（research-level，非交易） |
|---|---|
| **EARLY_SIGNAL** | 最早值得开始观察：出现可辨识的、属于该主题的异动/关注（可早于正式催化） |
| **THEME_FORMING** | 主题初具雏形：龙头/叙事开始确立，但尚未形成广泛识别 |
| **CONFIRMED** | 主题已相对可靠确认（催化落地 / 多核心同步） |
| **MAIN_RISE** | 主升：板块/核心样本持续一致上行 |
| **PEAK** | 主升顶点（板块 peak 或 cluster） |
| **DECLINING** | 回落 / 丧失主导（First Decline → 衰减） |
| **SECONDARY** | 次级活跃 / 二次新高（可能仅部分个股） |
| **ENDED** | 主题失去持续主导，进入冷却或结束 |

- 这些是**对行情所处阶段的描述**，不意味着“可交易”；不预设必然出现。

## 2. Theme Cycle v0.1（结构）

```
Theme Cycle                            例：auto_intelligence_2023
│
├── Campaign 1（Smart Driving）
│   ├── Early Signal
│   ├── Formation
│   ├── Confirmation
│   ├── Main Rise
│   ├── Peak
│   └── Decline / End
│
└── Campaign 2（Huawei Auto）—— 同 theme family
    ├── Early Signal
    ├── Formation / Catalyst
    ├── Broad Confirmation
    └── Main Rise（可在 Campaign 1 结束前开始 → Overlap）
```

- **theme_cycle_id**：research 级标签（`auto_intelligence_2023`、`auto_policy_2022`、`robotaxi_2024` 等），不改 schema。
- 一个 Theme Cycle 可含多个 Campaign；Campaign 可有多个 Phase/Signal。

## 3. Theme Drift（主题漂移）

> **Theme Drift**：核心叙事 / 核心股票发生迁移，但属于同一大主题家族（same_theme_family）。

- 2023：7月 Smart Driving / Robotaxi / L3（德赛/浙江/万安/众泰）→ 9月 Huawei Auto / AITO M7 / ADS2.0（赛力斯/江淮/德迈仕/铭科/华阳）。
- 方向相邻 → same_theme_family；具体 Campaign 与 Leader 更替。
- 不作“强行归类”，允许 Campaign 含多个 Theme。

## 4. Campaign Overlap（重叠）

> **Campaign Overlap**：新旧 Campaign 时间部分重叠，但关注中心明显转移。

- 2023 例：08-29→09-12 期间，旧 Smart Driving（德赛/浙江）与华为汽车早段并存。
- **不是模型错误**；为避免重叠而修改 Campaign 日期是违规的。
- 记录 overlap + attention shift（如 09-08 浙江世宝涨停＝旧 SD 反抽，同时华为汽车早段起步）。

## 5. 三案例生命周期（research 摘要）

### 2022（theme_cycle_id = auto_policy_2022）
Setup(04-27, 行业修复) → Theme Formation(05-23 国常会600亿) → Broad Confirmation(06-01 细则落地) → Main(05-23→06-28) → Peak(cluster 06-23/06-28) → Retracement(07) → Decay(08, decline_cluster 08-01二高点后).
- 特别：实际启动 04-27（Setup/Industry）远早于 nominal 6-8月 → Window Drift 强证据。

### 2023（theme_cycle_id = auto_intelligence_2023，含两 Campaign）
- **Campaign 1（Smart Driving）**：预热(06-12) → 识别(06-21 L3吹风) → Confirmation(07-03) → Main(07-03~07-19, SDIdx +33.5% vs AUTO+1.3%) → Peak(07-12~19) → Secondary(08-04) → Cooling/Decline(08下-09上) → **End≈09-12（德赛/浙江见顶转跌）**.
- **Campaign 2（Huawei Auto）**：Early Signal(08-29) → Formation(09-04 赛力斯涨停) → Catalyst(09-12 M7上市) → Broad Confirmation(09-18) → Main Rise(09下-10, 至10-31 仍升).
- **Campaign Overlap**：08-29~09-12 两 Campaign 时间重叠；attention shift 向华为汽车。

### 2024（theme_cycle_id = robotaxi_2024）
Early Signal(07-08) → Broad Confirmation(07-10) → Main(07→) → Peak(08-05) → First Decline(08-06) → Main End(08-23) → Secondary(09-05~06, weak).

## 6. 是否值得进入正式 Schema（本阶段评估）

- **YES（建议下一轮正式化）**：2022/2023/2024 三案例均能自然表达 Theme Cycle → Campaign → Phase/Signal，无需强行修改历史数据。
- 但仍需：① 人工确认 verified 日期（start/peak/end）；② 明确 theme_cycles 表字段（是否含 overlap / theme_drift 标签）后再落库。
- **本轮不创建 schema / 不改 db.py / schema.sql**。

## 7. 纪律
- Opportunity State / Theme Cycle 均为研究描述，非交易信号。
- 先敌view下，Early Signal/Formation/Confirmation 用 Point-in-Time 信息判断（不事后倒推）。
- 不计算 seasonality_score / win_rate / probability / predictive_model。