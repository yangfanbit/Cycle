# Auto 2018-2025 Final Review

> 基于 2018-2025 八年数据的最终评估：回答"6—8月汽车"应如何定义。
> 遵循"真实历史事实优先"原则，不为证明 Rule 而修改研究结果。

---

## 执行摘要

**最终结论**："6—8月汽车"应定义为 **B. 历史观察窗口**（Historical Observation Window），而非固定季节窗口。

**核心证据**：
- 2022 年实际启动 04-27，远早于 6-8月窗口（Window Drift 强证据）
- 2018 年明确反例（no_clear_campaign，板块整体下行）
- 2024 年实际启动 07-08，接近窗口尾部
- 2025 年受大盘 β 与 FSD 未落地双重约束，强度需降档

---

## 1. 年度汇总（2018-2025）

| 年份 | Annual Status | Campaign数 | 最早启动 | 最晚启动 | 关键特征 |
|---|---|---|---|---|---|
| 2018 | no_clear_campaign | 0 | — | — | 行业下行+贸易摩擦+购置税退坡，反例年份 |
| 2019 | weak | 1 | 2019-08-15 | 2019-08-15 | 事件驱动，启动偏窗口尾部 |
| 2020 | strong | 1 | 2020-06-01 | 2020-06-01 | 特斯拉国产化+新能源，清晰主题 Campaign |
| 2021 | strong | 1 | 2021-06-01 | 2021-06-01 | 新能源/电池主线，非全面汽车行情 |
| 2022 | strong | 1 | 2022-04-27 | 2022-04-27 | 政策驱动，启动明显提前（Window Drift） |
| 2023 | medium | 1 | 2023-06-12 | 2023-06-12 | 智能驾驶主题，Theme Drift（→Huawei Auto） |
| 2024 | medium | 2 | 2024-06-11 | 2024-07-08 | Robotaxi脉冲，快涨快退 |
| 2025 | medium | 1 | 2025-06-22 | 2025-06-22 | 受大盘β与FSD未落地约束，强度降档 |

---

## 2. 关键发现

### 2.1 Window Drift（窗口漂移）

**强证据**：
- **2022**：实际启动 04-27，比 6-8月窗口提前约 5 周
- **2024**：实际启动 07-08，接近窗口尾部
- **2019**：启动 08-15，明显偏窗口尾部

**结论**：不支持"固定季节窗口"定义。

### 2.2 反例年份（2018）

**2018 年明确反例**：
- 6-8月窗口内汽车板块整体下行
- 中汽协：7月销量同比-4%，为年内第二个同比下降月份
- 申万汽车/同花顺汽车板块上半年整体跌约22.59%
- 仅特斯拉临港建厂造成短暂事件脉冲，不构成 Campaign

**意义**：证明"6-8月汽车"并非每年有效。

### 2.3 主题集中度 vs 全面行情

**2021 年关键区分**：
- Campaign 集中于新能源/电池（比亚迪/宁德时代/长城/长安）
- 整体汽车销量受芯片短缺拖累同比转负
- **非全面汽车行情**，而是"新能源渗透+电池高景气"主线

**2025 年约束**：
- 夏季涨幅部分来自8月大盘牛市β（沪指+8%/创业板+24%）
- 特斯拉FSD 2025年未正式落地（2026-05-21才宣布监督版入华）
- 点火源是"Robotaxi试点"而非"FSD入华"

---

## 3. Rule 最终评价

### 3.1 定义选项评估

| 选项 | 定义 | 支持度 | 理由 |
|---|---|---|---|
| **A. 固定季节窗口** | 严格6-8月 | ❌ 不支持 | 2022启动04-27，2019启动08-15，漂移明显 |
| **B. 历史观察窗口** | 历史观察期 | ✅ **推荐** | 允许漂移，关注启动信号而非固定日期 |
| **C. 汽车二三季度观察窗口** | Q2-Q3观察 | ⚠️ 部分支持 | 涵盖Q2-Q3，但不如B灵活 |
| **D. 条件性观察窗口** | 条件触发 | ⚠️ 需定义条件 | 需明确触发条件，当前证据不足 |

### 3.2 最终建议

**定义为 B. 历史观察窗口**：

**理由**：
1. **Window Drift 证据充分**：2022提前5周，2019/2024偏尾部
2. **反例存在**：2018明确无效
3. **主题多样性**：政策驱动（2022）vs 产品驱动（2023 Huawei）vs 事件驱动（2024 Robotaxi）
4. **强度变化**：2020-2021强，2023-2025中等，2018弱/无效

**操作定义**：
- **观察期**：Q2-Q3（4-9月）
- **触发条件**：出现 Research Signal（EARLY_SIGNAL / THEME_FORMING）
- **确认条件**：Campaign Phase 确认（Broad Confirmation / Main Rise）
- **强度评估**：需排除市场 β contamination

---

## 4. 方法学贡献

### 4.1 Theme Lifecycle Model v0.2

**固化成果**：
- Research Signal（EARLY_SIGNAL / THEME_FORMING / CONFIRMATION_CANDIDATE）与 Campaign Phase（MAIN_RISE / PEAK / RETRACEMENT / DECLINING / SECONDARY / ENDED）严格分层
- RETRACEMENT 正式加入 Campaign Phase（区别于 DECLINING）
- 时间字段体系（early_signal_date / theme_formation_date / campaign_start_date 等）

### 4.2 Historical Campaign Validation v1.0

**固化成果**：
- 数据事实层 / 解释层 / 归组层分离
- Point-in-Time vs Retrospective 严格区分
- Evidence 治理（≥2独立证据组）
- Bias 控制（Survivorship / Look-Ahead / Beta contamination）

### 4.3 统一建模（2022-2024）

**固化成果**：
- 三案例统一生命周期建模
- Theme Drift（Smart Driving → Huawei Auto）
- Campaign Overlap（08-29~09-12 重叠）

---

## 5. 研究不确定性（允许的 WARNING）

以下不确定性属于研究允许范围，**非错误**：

1. **2023-08-29 Early Signal Candidate**：存在市场Beta contamination，无法完全排除，保持 low confidence
2. **2022 Peak Cluster**：06-23 vs 06-28，龙头与行业代理峰值可能不同，允许 cluster
3. **2024 Secondary**：09-05~06 为 Weak Secondary Candidate，强度不足
4. **2025 强度降档**：受大盘β与FSD未落地约束，判定为 medium 而非 strong

---

## 6. 最终结论

### 6.1 Rule 评价

**"6—8月汽车"最终评价**：**Partially Supported**（部分支持）

**条件**：
- 作为**历史观察窗口**有效
- 需结合 Research Signal 触发
- 需排除市场 β contamination
- 强度需根据具体年份评估

### 6.2 研究基础设施

**已建立**：
- 稳定的方法论（Theme Lifecycle v0.2 + Validation v1.0）
- 统一建模案例（2022-2024）
- 完整验证流程（数据库/导出/市场数据）

**可扩展性**：
- 支持未来大量历史 Campaign 扩展
- 支持新行业/题材/时间规律研究
- 支持长期 A股市场历史规律研究基础设施

---

## 7. 纪律声明

- 真实历史事实优先，不为证明 Rule 而修改研究结果
- 宁可 unknown / candidate / no_clear_campaign，也不伪装 verified
- 所有关键定义明确标注来源/研究者解释/暂定假设
- 禁止"大家都知道" / "显然" / "通常" / "经验上" 而无依据
