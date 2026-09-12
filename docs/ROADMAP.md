# ROADMAP.md — 阶段规划

> 规则：未来功能记录在这里，而不是提前实现在代码里。

## V1（当前）— 历史地图 / 数据化经验 / 时间轴

已完成：

- 全年四层时间轴（事件 / 季节性规律 / 历史题材 / 状态）
- TODAY 标记与年份切换
- 跨年行情完整建模与延续渲染
- Pre-heat 四态相位（NOT_ACTIVE / PRE_HEAT / ACTIVE / ENDED）
- Rule / Campaign 详情抽屉
- 未来关注窗口（7/30/60/90 天）
- 10 条候选规律种子数据（全部 candidate，来源可追溯）
- 18 项单元测试
- 治理文档体系（AGENTS.md + docs/）

## V1.5 — 历史统计与季节性验证

- 接入历史行情数据，逐条核验候选规律的历史案例（Evidence L0 → L2）
- 计算可追溯统计量：sample_count / launch_date_median / launch_date_std /
  average_duration / excess_return / repeat_rate / seasonality_score（→ L3）
- 统计方法论必须写入 statistics.methodology
- 统计结果表述为"历史统计特征"，禁止外推为未来承诺（见 PRODUCT.md「前瞻性分析 ≠ 确定性预测」）
- 评估 Rule.status 拆分为 evidence_status / verification_status 双字段（映射见 DATA_GOVERNANCE.md）
- 数据源迁移：TS 模块 → SQLite

## V2 — 当前状态 / Future Opportunity Radar

- Observation 录入 UI（人工观察，不得直接修改 Rule）
- 实时市场状态（行情接入在本阶段才允许评估）
- 雷达规则化升级

## V3 — 历史规律 vs 当年偏离

- 当年实际走势与历史窗口的偏离度对比
- 「今年是否重演」的情景分析框架（前瞻性分析，不是确定性预测）
- 历史相似案例检索、当前状态与历史条件的分布对比

## V4 — 个人投资研究工作台

- 个性化观察池
- 通知（仅在本阶段评估）
- 多来源研究材料管理

## 未来可能加入（均需届时单独评估授权）

- 实时行情、资金流、市场异动
- 个性化观察池
- 通知
- 组件级测试与 E2E 框架
