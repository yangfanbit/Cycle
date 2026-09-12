# Auto Lifecycle 2022-2024 统一建模

> 基于 Theme Lifecycle Model v0.2 的 2022-2024 三案例统一生命周期建模。
> 遵循 Research Signal / Campaign Phase 严格分层，确保历史事实优先。

---

## 2022 Auto Policy（theme_cycle_id = auto_policy_2022）

### Research Signals（不属于 Campaign Phase）

| Date | Signal | 依据 | 置信度 |
|---|---|---|---|
| 2022-04-27 | EARLY_SIGNAL | 行业修复/Setup（汽车指数自4月底启动，不到两月涨超60%） | medium |
| 2022-05-23 | THEME_FORMING | 国务院常务会议：阶段性减征乘用车购置税600亿元 | high |

**关键区分**：04-27 为 Industry Recovery / Setup，**不自动等于** Theme Campaign Start。

### Campaign Phases

| Phase | Date | 依据 |
|---|---|---|
| Campaign Start | 2022-05-23 | 国常会购置税政策催化 |
| Broad Confirmation | 2022-06-01 | 财政部/税务总局细则落地次日整车集体涨停 |
| Main Rise | 2022-05-23 → 2022-06-28 | 政策驱动主升 |
| Peak | cluster {2022-06-23, 2022-06-28} | 龙头与行业代理峰值可能不同 |
| Retracement | 2022-07 | 正常技术回撤，主题可能恢复 |
| Declining | 2022-08 | decline_cluster，08-01二高点后持续衰减 |
| End | 2022-08后续 | 最后一次板块同步/有效新高后确认 |

### 特殊事件处理

| Date | Event | 处理 |
|---|---|---|
| 2022-05-31 | 财政部/税务总局正式公告 | policy detail / confirmation event，**不与 05-23 合并** |
| 2022-05-13~30 | 中通客车12连板（+214.52%） | classification = event_driven（核酸检测车概念），**不并入** Main Auto Theme |

### Window Drift 证据
- **实际启动**：04-27（远早于 nominal 6-8月窗口）
- **意义**：为 Window Drift 提供强证据，支持"历史观察窗口"而非"固定季节窗口"

---

## 2023 Auto Intelligence（theme_cycle_id = auto_intelligence_2023）

### Campaign 1: Smart Driving

#### Research Signals

| Date | Signal | 依据 |
|---|---|---|
| 2023-06-12 | EARLY_SIGNAL | 预热阶段 |
| 2023-06-21 | THEME_FORMING | 工信部吹风会：支持L3及以上自动驾驶商业化、启动准入和上路通行试点 |

#### Campaign Phases

| Phase | Date | 依据 |
|---|---|---|
| Campaign Start | 2023-06-21 | L3政策吹风催化 |
| Confirmation | 2023-07-03 | 整车/智驾全面爆发（25股涨停、整车指数创4月新高） |
| Main Rise | 2023-07-03 ~ 2023-07-19 | SDIdx +33.5% vs AUTO+1.3% |
| Peak | 2023-07-12~19 | 板块峰值区间 |
| Secondary | 2023-08-04 | 次级活跃 |
| Cooling/Decline | 2023-08下~09上 | 主题持续衰减 |
| End | ≈2023-09-12 | 德赛/浙江见顶转跌，确认结束 |

### Campaign 2: Huawei Auto

#### Research Signals

| Date | Signal | 依据 | 置信度 |
|---|---|---|---|
| 2023-08-29 | EARLY_SIGNAL Candidate | 市场Beta + 汽车零部件 + 机器人 + 华为汽车同时活跃，**无法排除 Beta contamination** | low |
| 2023-09-04 | THEME_FORMING | 赛力斯首次明显突破（涨停） | medium |

**关键约束**：08-29 存在较强市场 Beta，汽车零部件与机器人同时活跃，**不直接确认**为 Huawei Auto Early Signal，保留 Candidate 状态。

#### Campaign Phases

| Phase | Date | 依据 |
|---|---|---|
| Campaign Start Candidate | 2023-09-12 | 问界M7 catalyst（产品发布） |
| Broad Confirmation | 2023-09-18 | 华为汽车核心扩散 + 多股同步 |
| Main Rise | 2023-09下~10 | 至2023-10-31 仍升 |

### Theme Drift（主题漂移）

| 维度 | Smart Driving | Huawei Auto | 变化 |
|---|---|---|---|
| **核心叙事** | L3政策预期 / Robotaxi | 华为新车 / AITO M7 / ADS2.0 | 明显迁移 |
| **核心股票** | 德赛/浙江/万安/众泰 | 赛力斯/江淮/德迈仕/铭科/华阳 | 明显更换 |
| **催化类型** | 政策吹风 | 产品发布 | 类型变化 |
| **Theme Family** | same_theme_family（汽车智能化） | same_theme_family | 保持一致 |

### Campaign Overlap（重叠）

| 时间段 | 状态 | 说明 |
|---|---|---|
| 2023-08-29 ~ 2023-09-12 | Overlap | 旧 Smart Driving（德赛/浙江）与华为汽车早段并存 |
| 2023-09-08 | Attention Shift | 浙江世宝涨停＝旧 SD 反抽，同时华为汽车早段起步 |

**约束**：不强迫 `A.end < B.start`，允许时间重叠但需记录 attention_shift。

---

## 2024 Robotaxi（theme_cycle_id = robotaxi_2024）

### Research Signals

| Date | Signal | 依据 |
|---|---|---|
| 2024-07-08 | EARLY_SIGNAL | Early Start（萝卜快跑武汉跑出圈，无人驾驶板块大涨4%） |

### Campaign Phases

| Phase | Date | 依据 |
|---|---|---|
| Broad Confirmation | 2024-07-10 | 板块广泛确认 |
| Main Rise | 2024-07 → | 主升阶段 |
| Peak | 2024-08-05 | 板块峰值 |
| First Decline | 2024-08-06 | 首次明显回撤 |
| Main Campaign End | 2024-08-23 | Major Breakpoint（主要行情结构被破坏） |
| Secondary | 2024-09-05~06 | Weak Secondary Campaign Candidate |

### 当前统一结论

- **Main Campaign**：2024-07-08 → 2024-08-23
- **Secondary Candidate**：2024-09-05~06（weak）
- **特别说明**：2024-10-10 特斯拉Robotaxi发布会仅一日脉冲后回落，**不作为**独立 Campaign

---

## 统一建模验证

### Research Signal vs Campaign Phase 边界

| 案例 | Research Signal 日期 | Campaign Start 日期 | 边界清晰 |
|---|---|---|---|
| 2022 | 04-27 (EARLY_SIGNAL), 05-23 (THEME_FORMING) | 05-23 | ✅ |
| 2023 SD | 06-12 (EARLY_SIGNAL), 06-21 (THEME_FORMING) | 06-21 | ✅ |
| 2023 HW | 08-29 (EARLY_SIGNAL Candidate), 09-04 (THEME_FORMING) | 09-12 (Candidate) | ✅ |
| 2024 | 07-08 (EARLY_SIGNAL) | 07-08 | ✅ |

### Campaign End 判定

| 案例 | End 判定依据 | 非单日跌停 | 非观察窗口结束 |
|---|---|---|---|
| 2022 | 08月 decline_cluster，最后一次板块同步 | ✅ | ✅ |
| 2023 SD | 09-12 德赛/浙江见顶转跌 | ✅ | ✅ |
| 2023 HW | 未结束（至10-31仍升） | N/A | N/A |
| 2024 | 08-23 Major Breakpoint | ✅ | ✅ |

### Theme Drift / Overlap

| 案例 | Theme Drift | Campaign Overlap |
|---|---|---|
| 2023 | Smart Driving → Huawei Auto | 08-29~09-12 重叠 |

---

## 方法学固化

本统一建模基于：
1. **Theme Lifecycle Model v0.2**：Research Signal / Campaign Phase 严格分层
2. **Historical Campaign Validation v1.0**：数据事实层/解释层/归组层分离
3. **真实历史事实优先**：不为支持 Rule 而修改研究结果

**未来扩展**：新增历史案例时，遵循相同分层原则，确保方法学一致性。
