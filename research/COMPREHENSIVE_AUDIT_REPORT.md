# Cycle-Research Comprehensive Research & Model Audit

> 全面研究模型审计报告：基于 2018-2025 数据，固化方法学，确保长期可扩展性。

---

## 1. 当前项目状态

### 数据库状态
- **Tables**: 18 个表全部正常 populated
- **Campaigns**: 8 个（2018-2025，2018 为 no_clear_campaign）
- **Evidences**: 46 条总计
  - **Campaign-bound**: 39 条（通过 campaign_evidences 显式绑定）
  - **Unbound**: 7 条（合法状态，支持整个 Rule 或无法属于特定 Campaign 的反例）
- **Sources**: 49 个，tier/type 一致性验证通过
- **Market Data**: 4,934 条日线数据，25 个 series
- **Trading Calendar**: 371 个交易日（从 SH000300 推导）

### 验证状态
- **validate_db.py**: PASS（0 FAIL，0 WARNING）
- **export.py**: PASS（evidence isolation 验证通过）
- **gen_annual.py**: PASS（生成 2018-2025 全部年度报告）
- **gen_summary.py**: PASS（生成汇总报告）
- **calibrate_robotaxi.py**: PASS（9/9 tests）
- **point_in_time_robotaxi.py**: PASS（12/12 tests）

---

## 2. 本轮发现的问题

### 已解决
1. **trading_calendar 空表**：创建 `seed_trading_calendar.py`，从 benchmark 推导 371 个交易日
2. **gen_annual.py 仅生成 2018-2020**：扩展为 2018-2025 全部年份
3. **Research Signal 与 Campaign Phase 混淆**：固化 v0.2 模型，严格分层

### 持续监控
1. **2023-08-29 Early Signal Candidate**：存在 Beta contamination，保持 low confidence
2. **2022 Peak Cluster**：06-23 vs 06-28，允许 cluster 存在

---

## 3. 修改的问题

### 方法学固化
- **theme_lifecycle_v0_2.md**：Research Signal（EARLY_SIGNAL/THEME_FORMING/CONFIRMATION_CANDIDATE）与 Campaign Phase（MAIN_RISE/PEAK/RETRACEMENT/DECLINING/SECONDARY/ENDED）严格分层
- **historical_campaign_validation_v1.md**：数据事实层/解释层/归组层分离，PIT/Retrospective 严格区分
- **auto_lifecycle_2022_2024.md**：三案例统一生命周期建模
- **auto_2018_2025_final_review.md**：Rule 最终评价为"历史观察窗口"

### 基础设施
- **seed_trading_calendar.py**：交易日历自动推导，幂等
- **_audit_dump.py**：数据库状态审计工具

---

## 4. 未修改的问题及原因

### Schema 保持不变
**原因**：2022/2023/2024 三案例均能自然表达 Theme Cycle → Campaign → Phase/Signal，无需强行修改历史数据。research-level 标注已足够。

### 不创建 theme_cycles 表
**原因**：ThemeCycle 本质是 Research Grouping，不是 Market Fact。保持 research-level 避免过度设计。

### 不创建 campaign_relations 表
**原因**：当前三案例的 Theme Drift / Campaign Overlap 可通过 research-level 标签表达，无需正式表。

---

## 5. Research Signal 模型

### 状态定义
| Signal State | 含义 | 所属层级 |
|---|---|---|
| EARLY_SIGNAL | 最早值得观察的异动/关注 | Research Layer |
| THEME_FORMING | 主题初具雏形，龙头/叙事确立 | Research Layer |
| CONFIRMATION_CANDIDATE | 可能升级为正式 Campaign 的候选 | Research Layer |

### 关键约束
- **不属于 Campaign Phase**，不得写入 `campaign_phases` 表
- 用 Point-in-Time 信息判断，不事后倒推
- 非交易信号，仅为研究描述

---

## 6. Campaign Phase 模型

### 状态定义
| Phase State | 含义 | 关键区分 |
|---|---|---|
| MAIN_RISE | 主升：板块/核心样本持续一致上行 | — |
| PEAK | 主升顶点（允许 cluster） | — |
| RETRACEMENT | 正常回撤，主题可能恢复 | 幅度/时间未破坏主升结构 |
| DECLINING | 主题持续性明显下降 | 资金持续流出，难以恢复 |
| SECONDARY | 次级活跃/二次新高 | 可能仅部分个股 |
| ENDED | 主题失去持续主导 | 进入冷却或结束 |

### RETRACEMENT vs DECLINING
- **RETRACEMENT**：技术回撤，结构未破坏
- **DECLINING**：持续性衰减，结构破坏

---

## 7. 2022 最终生命周期

### Research Signals
- **04-27 EARLY_SIGNAL**：行业修复/Setup（不等于 Campaign Start）
- **05-23 THEME_FORMING**：国常会购置税600亿政策

### Campaign Phases
- **Campaign Start**: 05-23（政策催化）
- **Broad Confirmation**: 06-01（细则落地次日涨停）
- **Main Rise**: 05-23 → 06-28
- **Peak**: cluster {06-23, 06-28}
- **Retracement**: 07月（正常回撤）
- **Declining**: 08月（decline_cluster）
- **End**: 08月后续（最后一次板块同步）

### 特殊处理
- **05-31**：财政部公告 = policy detail / confirmation event，不与 05-23 合并
- **中通客车**：classification = event_driven，不并入 Main Auto Theme

---

## 8. 2023 最终生命周期

### Campaign 1: Smart Driving
- **Research Signals**: 06-12 (EARLY_SIGNAL), 06-21 (THEME_FORMING)
- **Campaign Start**: 06-21
- **Main Rise**: 07-03 ~ 07-19 (SDIdx +33.5% vs AUTO+1.3%)
- **Peak**: 07-12~19
- **End**: ≈09-12（德赛/浙江见顶转跌）

### Campaign 2: Huawei Auto
- **Research Signals**: 08-29 (EARLY_SIGNAL Candidate, low confidence), 09-04 (THEME_FORMING)
- **Campaign Start Candidate**: 09-12（问界M7 catalyst）
- **Broad Confirmation**: 09-18（核心扩散+多股同步）
- **Main Rise**: 09下~10（至10-31仍升）

### Theme Drift
- **叙事**: L3政策预期 → 华为新车/AITO M7
- **股票**: 德赛/浙江 → 赛力斯/江淮
- **Theme Family**: same_theme_family（汽车智能化）

### Campaign Overlap
- **08-29~09-12**：旧 Smart Driving 与华为汽车早段并存
- **Attention Shift**：09-08 浙江世宝涨停＝旧 SD 反抽

---

## 9. 2024 最终生命周期

### Research Signals
- **07-08 EARLY_SIGNAL**：萝卜快跑武汉跑出圈

### Campaign Phases
- **Broad Confirmation**: 07-10
- **Main Rise**: 07→
- **Peak**: 08-05
- **First Decline**: 08-06
- **Main Campaign End**: 08-23（Major Breakpoint）
- **Secondary**: 09-05~06（Weak Candidate）

### 统一结论
- **Main Campaign**: 07-08 → 08-23
- **Secondary Candidate**: 09-05~06（weak）

---

## 10. 2023 Theme Drift

**确认存在 Theme Drift**：
- Smart Driving（L3政策预期）→ Huawei Auto（华为新车）
- 核心叙事、核心股票、催化类型均明显迁移
- 属 same_theme_family（汽车智能化）

---

## 11. Campaign Overlap

**确认存在 Campaign Overlap**：
- 2023-08-29 ~ 2023-09-12：Smart Driving 与 Huawei Auto 时间重叠
- 不强迫 `A.end < B.start`，允许重叠但记录 attention_shift

---

## 12. ThemeCycle

**保持 research-level**：
- theme_cycle_id 作为研究标签（auto_policy_2022 / auto_intelligence_2023 / robotaxi_2024）
- 不创建正式 theme_cycles 表
- 避免将主观归组固化成客观事实

---

## 13. Point-in-Time

### 严格区分
| 类型 | 信息约束 | 用途 |
|---|---|---|
| Retrospective | 可用后来结果/公告/最终价格 | 复盘 |
| Point-in-Time | 仅用当时已公开信息 | "提前观察"研究 |

### Leader 命名
- **Historical Leader Set**：完整行情结束后回看确认
- **Point-in-Time Basket**：截至具体日期当时可识别
- **禁止混用**

---

## 14. Historical Leader vs PIT Leader

**2024 Robotaxi 案例**：
- **07-08 PIT Basket**: unavailable（无可靠公开主题识别）
- **07-10 PIT Basket**: [DAZHONGTONG, JINJIANG, XINGYUYUDA, TIANMAI]
- **07-15 PIT Basket**: +JINLONG（金龙07-12才进入）
- **Historical Leader**: 包含全部（事后确认）

**关键**：金龙(07-12)不进入 07-08/07-10 切片，避免 look-ahead bias。

---

## 15. Market Data

### 价格口径分离
- **Signal/Phase Detection**: raw close
- **Return Calculation**: adjusted(qfq)
- **禁止混用**

### 等权指数计算
**正确**：`Equal-Weight Return(t) = Σ[price_i(t) / price_i(start)] / N`
**禁止**：`avg(price_t) / avg(price_start)`

### 行业代理约束
- **516110**：仅2024代理（成立时间晚于2018）
- **AUTO_SW 801880**：历史数据不可用时不伪造

---

## 16. Beta / Survivorship / Look-Ahead Bias

### Beta Contamination
- **2023-08-29**：市场Beta + 汽车零部件 + 机器人 + 华为汽车同时活跃
- **处理**：保持 EARLY_SIGNAL Candidate，low confidence

### Survivorship Bias
- Leader Basket 标记 `survivorship-aware / retrospective`
- 明确说明基于事后确认的幸存者

### Look-Ahead Bias
- PIT 研究仅用当时已公开信息
- Retrospective 研究明确标注使用 hindsight

---

## 17. Evidence Governance

### 证据绑定
- **必须**通过 campaign_evidences 显式绑定
- **禁止**全库 Evidence 挂到一个 Campaign

### 证据数量
- **Research Confirmed**：≥2 Evidence + ≥2 independence_group
- **禁止**：同一原文转载算作两个独立来源

### 来源分级
- **Tier 1**：官方公告、政府文件、财报
- **Tier 2**：权威媒体、行业协会数据
- **Tier 3**：市场传闻、社交媒体

---

## 18. 2018–2025 Rule 最终评价

### 定义选项
| 选项 | 支持度 | 理由 |
|---|---|---|
| A. 固定季节窗口 | ❌ | 2022启动04-27，漂移明显 |
| **B. 历史观察窗口** | ✅ **推荐** | 允许漂移，关注启动信号 |
| C. 汽车二三季度观察窗口 | ⚠️ | 涵盖Q2-Q3，但不如B灵活 |
| D. 条件性观察窗口 | ⚠️ | 需定义条件，证据不足 |

### 最终结论
**"6—8月汽车"应定义为 B. 历史观察窗口**

**理由**：
1. Window Drift 证据充分（2022提前5周）
2. 反例存在（2018明确无效）
3. 主题多样性（政策/产品/事件驱动）
4. 强度变化（2020-2021强，2023-2025中，2018弱）

### Rule 评价
**Partially Supported**（部分支持），条件：
- 作为历史观察窗口有效
- 需结合 Research Signal 触发
- 需排除市场 β contamination
- 强度需根据具体年份评估

---

## 19. 是否需要正式 Schema Migration

**NO**

**理由**：
1. 2022/2023/2024 三案例均能自然表达，无需强行修改
2. research-level 标注已足够表达 Theme Cycle / Theme Drift / Campaign Overlap
3. 避免过度设计，保持简洁

---

## 20. 如果 YES（N/A）

不适用。

---

## 21. 如果 NO

**为什么 research-level 已经足够**：

1. **ThemeCycle 本质**：是 Research Grouping，不是 Market Fact
2. **表达充分**：theme_cycle_id + Theme Drift + Campaign Overlap 标签已能完整表达
3. **避免固化**：不将主观归组固化成客观事实
4. **扩展性**：未来新增案例时，若 research-level 不足，再提出最小 schema

---

## 22. Cycle 是否可以重新启动开发

**YES**

**具体允许开始**：
1. **数据导入**：将 Cycle-Research 中 verified 的历史事实导入 Cycle/data/verified/
2. **API 开发**：基于 stable schema 开发查询 API
3. **前端开发**：展示历史 Campaign / Theme Cycle / Evidence
4. **研究工具**：开发新的历史规律探索工具

**前提**：
- 仅导入经过严格人工/研究确认的历史事实
- 保持 Cycle-Research 作为研究实验室的独立性

---

## 23. 当前推荐下一阶段

### 优先级 1：数据验证与导入
- 人工确认 verified 日期（start/peak/end）
- 将 verified 数据导入 Cycle/data/verified/

### 优先级 2：方法学扩展
- 应用 Theme Lifecycle v0.2 到新行业/题材
- 验证方法学的普适性

### 优先级 3：工具开发
- 开发自动化研究工具
- 建立长期历史规律研究基础设施

---

## 24. 测试

| 测试项 | 结果 | 说明 |
|---|---|---|
| validate_db.py | ✅ PASS | 0 FAIL，0 WARNING |
| export.py | ✅ PASS | evidence isolation 验证通过 |
| gen_annual.py | ✅ PASS | 生成 2018-2025 全部年度报告 |
| gen_summary.py | ✅ PASS | 生成汇总报告 |
| calibrate_robotaxi.py | ✅ PASS | 9/9 tests |
| point_in_time_robotaxi.py | ✅ PASS | 12/12 tests |
| seed_trading_calendar.py | ✅ PASS | 371 个交易日，全部覆盖 |

**总计**：0 FAIL，0 WARNING（除明确解释的研究不确定性）

---

## 25. 核心原则遵守

✅ **真实历史事实优先**：不为证明 Rule 而修改研究结果
✅ **宁可 unknown**：不伪装 verified
✅ **宁可 candidate**：不强行确认
✅ **宁可 no_clear_campaign**：不为支持 Rule 而寻找行情
✅ **宁可 research-level grouping**：不把主观归组固化成客观事实

---

## 26. 最终状态

- **数据库**：一致，0 警告
- **导出**：最新，evidence isolation 验证通过
- **研究文档**：同步，方法学固化
- **测试**：全部通过
- **Git**：准备提交

**项目已准备好进入下一阶段。**
