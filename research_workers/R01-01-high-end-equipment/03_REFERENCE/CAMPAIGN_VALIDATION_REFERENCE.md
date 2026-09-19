<!-- READ-ONLY REFERENCE COPY —— 请勿修改 -->
> **来源**：ThreeC 仓库 `research/research/methodology/historical_campaign_validation_v1.md` @ `2153f6d83b7481300696ab73d792e9e53aa31a07`
> **性质**：**原文只读副本**（正文未修改，仅在顶部附加本 provenance 块）
> **用途**：Research Worker 参考既有方法论
> **禁止**：不得在本 Workspace 中修改本文件

---

# Historical Campaign Validation Methodology v1.0

> 历史 Campaign 验证方法学：确保研究结果的客观性、一致性和可扩展性。
> 适用于 A股行业/题材/时间规律的长期研究基础设施建设。

---

## 1. 验证原则

### 1.1 数据事实层与解释层分离

| 层级 | 内容 | 示例 | 验证标准 |
|---|---|---|---|
| **Layer 1 Fact** | 客观数据 | 某日赛力斯上涨 10.7% | 来源：Market Data |
| **Layer 2 Interpretation** | 研究解释 | "09-04 = Huawei Auto Theme Formation" | 研究者判断 |
| **Layer 3 Grouping** | 研究归组 | "Smart Driving 与 Huawei Auto 属于同一 ThemeCycle" | 研究者归组 |

**约束**：未来统计时，Layer 1 客观数据、Layer 2 研究解释、Layer 3 研究归组不能混淆。

### 1.2 证据治理

#### 来源分级（Source Tier）
- **Tier 1**：官方公告、政府文件、财报
- **Tier 2**：权威媒体、行业协会数据
- **Tier 3**：市场传闻、社交媒体、自媒体

**一致性检查**：`source_type` 与 `tier` 不得矛盾。

#### 证据绑定（Evidence Binding）
- **必须**通过 `campaign_evidences` 桥表显式绑定
- **禁止**将全库 Evidence 挂到一个 Campaign
- **角色分类**：`supporting` / `contradicting` / `context`
- **独立性判断**：`independence_group` 用于区分独立证据 vs 同一原文转载

#### 证据数量要求
- **Research Confirmed / Final Confirmed**：至少 2 Evidence + 2 independence_group
- **禁止**：同一原文转载的两篇新闻被当成两个独立来源

---

## 2. Point-in-Time vs Retrospective

### 2.1 严格区分

| 类型 | 定义 | 用途 | 信息约束 |
|---|---|---|---|
| **Retrospective** | 站在今天回看过去 | 复盘 | 可用后来结果/公告/最终价格 |
| **Point-in-Time** | 站在当时 | "提前观察"研究 | 仅用当时已公开信息 |

**禁止**：用10月文章证明9月8日已经知道某股票是 Leader。

### 2.2 Leader 命名规范

| 类型 | 定义 | 用途 |
|---|---|---|
| **Historical Leader Set** | 完整行情结束后回看确认的核心标的 | 复盘 |
| **Point-in-Time Basket** | 截至具体日期当时公开信息可识别的股票 | "提前观察"研究 |

**约束**：两者绝对不能混用；Leader Basket 始终标记 `survivorship-aware / retrospective`。

---

## 3. 市场数据口径

### 3.1 价格口径分离

| 用途 | 价格类型 | 说明 |
|---|---|---|
| **Signal / Phase Detection** | raw close | 原始收盘价，用于识别信号/阶段 |
| **Return Calculation** | adjusted(qfq) | 前复权价格，用于计算收益率 |

**禁止混用**。

### 3.2 等权指数计算

**正确方法**：
```
Equal-Weight Return(t) = Σ[price_i(t) / price_i(start)] / N
```

**禁止**：
```
avg(price_t) / avg(price_start)
```

**命名规范**：
- **正确**：Historical Leader Equal-Weight Index / Historical Leader Normalized Equal-Weight Index
- **禁止**：Robotaxi 板块指数（暗示官方指数）

### 3.3 行业代理约束

- **516110**：仅可作为 2024 汽车行业代理（成立时间晚于2018）
- **AUTO_SW 801880**：历史数据源不可用时不得伪造
- **回填禁止**：不使用今天的概念成分股回填过去；无历史快照则 `breadth = unavailable`

---

## 4. Bias 控制

### 4.1 Survivorship Bias
- Leader Basket 标记 `survivorship-aware / retrospective`
- 明确说明是基于事后确认的幸存者

### 4.2 Look-Ahead Bias
- Point-in-Time 研究仅用当时已公开信息
- Retrospective 研究明确标注使用 hindsight

### 4.3 Beta Contamination
- 识别市场整体 β 对主题表现的影响
- 如 2023-08-29：市场 Beta + 汽车零部件 + 机器人 + 华为汽车同时活跃
- 无法排除 contamination 时，保持 `EARLY_SIGNAL Candidate` 低置信度

---

## 5. Campaign 边界判定

### 5.1 Start 判定
- 不默认 `04-27 = Industry Recovery` 自动等于 `Theme Campaign Start`
- 需明确催化事件（如 05-23 国常会政策）
- 区分 `Setup` 与 `Campaign Start`

### 5.2 End 判定
- **禁止**：单日跌停 = End；观察窗口结束 = End
- **必须找**：最后一次板块同步/主题扩散/有效新高/有效催化
- **允许**：`decline_cluster`（多日期候选）

### 5.3 Peak 判定
- 允许 `peak_cluster`（如 06-23 vs 06-28）
- 考虑龙头与行业代理峰值可能不同

---

## 6. 测试与验证

### 6.1 数据库一致性
```bash
python scripts/validate_db.py    # 0 FAIL
```

### 6.2 导出一致性
```bash
python scripts/export.py         # 验证 campaign_evidences 绑定
python scripts/gen_annual.py     # 生成年度报告
python scripts/gen_summary.py    # 生成汇总报告
```

### 6.3 市场数据验证
```bash
python scripts/calibrate_robotaxi.py      # Robotaxi 日期校准
python scripts/point_in_time_robotaxi.py  # PIT Leader 验证
```

### 6.4 测试要求
- **0 FAIL** / **0 WARNING**（除非明确解释为允许的研究不确定性）
- 所有 pytest / unittest 全部通过

---

## 7. 结果表达

### 7.1 Rule 最终评价
基于 2018–2025，回答"6—8月汽车"应定义为：
- A. 固定季节窗口
- B. 历史观察窗口
- C. 汽车二三季度观察窗口
- D. 条件性观察窗口

**允许结论**：Supported / Partially Supported / Weak / Unsupported / Insufficient Evidence

### 7.2 隐含假设禁止
对关键定义必须明确标注：
- **来源**（Source）
- **研究者解释**（Researcher Interpretation）
- **暂定假设**（Working Assumption）

**禁止**："大家都知道" / "显然" / "通常" / "经验上" 而无依据。

---

## 8. 扩展性

本方法学旨在支持：
- 未来大量历史 Campaign 扩展
- 新行业/题材/时间规律研究
- 长期 A股市场历史规律研究基础设施

**核心原则**：真实历史事实优先；不为证明 Rule 而修改研究结果。
