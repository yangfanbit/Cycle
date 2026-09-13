# 产品初心检查（Product Purpose Checkpoint）

> 目标：**产品价值 > 研究工程复杂度**。每次研究任务开始前，回答下面 4 个问题；若第 4 项是主要动机，停止实现。

## 项目初心

本项目最终服务于 **A股机会时间轴**（主 Cycle Timeline MVP 的历史数据底座）：

1. 某个时间点历史上发生过什么
2. 某类主题通常如何形成
3. 提前多久出现信号
4. Campaign 如何发展
5. 什么时候进入退潮
6. 为主 Cycle 的时间轴提供可靠历史数据

不是学术数据库，不是"证明某条经验一定有效"。

## 每次研究前必须回答

| # | 问题 | 答案 | 通过 |
|---|---|---|---|
| 1 | 是否帮助构建时间轴？ | 产出能被时间轴消费的历史事实/候选/观察窗口 | 是 |
| 2 | 是否提高历史可比性？ | 跨年 Campaign 口径、证据、行情可比较 | 是 |
| 3 | 是否有助于识别提前信号？ | 保留 Research Signal / Point-in-Time 观察 | 是 |
| 4 | 是否只是工程复杂化？ | 新增表/字段/模型/统计/自动化，但无人消费 | **否（停止）** |

## 判定规则

- 4 个问题中 **1–3 任一为"是"且 4 为"否"** → 继续。
- **第 4 项为"是"（主要动机是工程复杂化）→ 停止实现**，把想法记录为 Research Limitation，不建实体、不加 schema。
- 研究模型 v1.0 **已冻结**：禁止创建 theme_cycles / campaign_relations、禁止修改 Phase/三层语义/Evidence 模型。

## 本轮检查结果（2026-09-13）

- 批量生产 2018–2025 Campaign / Theme / 日期候选 / Event / Security / Evidence / Market Data / PIT / Leader → 全部直接服务时间轴 ✅
- Research → Cycle Export Contract（timeline_export_v1）→ 直接服务主 Cycle Timeline MVP ✅
- 不新增正式 Schema、不计算统计指标 → 不工程复杂化 ✅

**结论：符合初心，继续。**
