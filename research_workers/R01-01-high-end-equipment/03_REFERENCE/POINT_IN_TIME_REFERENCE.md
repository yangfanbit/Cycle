<!-- READ-ONLY REFERENCE COPY —— 请勿修改 -->
> **来源**：ThreeC 仓库 `research/research/methodology/point_in_time.md` @ `2153f6d83b7481300696ab73d792e9e53aa31a07`
> **性质**：**原文只读副本**（正文未修改，仅在顶部附加本 provenance 块）
> **用途**：Research Worker 参考既有方法论
> **禁止**：不得在本 Workspace 中修改本文件

---

# Point-in-Time 研究边界（Pilot 1-C0）

> 核心警惕：**“事后知道” ≠ “当时知道”。**
> 本文件界定本库在处理证据时，哪些可以回看(Retrospective)，哪些必须锚定当时(Point-in-Time)。

---

## 1. 两类视角

### Retrospective Research（回看/复盘）
允许后续资料用于：
- 解释结果（为什么走完/没走完）
- 判断最终结束与退潮
- 复盘与归因
- 识别反例 / 事后反证

### Point-in-Time Research（时点内）
**只能使用在当时已经公开的信息**：
- 某日当时的股价/板块/量能
- 当时已公告的政策、公司公告、行业数据
- 当时媒体可见的叙事（在报道日之前已发生或已公开的事实）

**禁止**：把 2026 年才发生/才公开的信息，当作 2025 年“当时已知的催化”来使用。

---

## 2. 与本库字段的对应

`evidences.temporal_relation`（相对其绑定 Campaign 的时间语义）：

| 值 | 含义 | 能用于什么 |
|---|---|---|
| `contemporaneous` | 发生/发布于 Campaign 期间 | 启动/主升/run 的同期证据 |
| `prior` | 发生于 Campaign 开始前 | 前提/政策预期/蓄势 |
| `subsequent` | Campaign 后，用于解释结果/退潮/反证 | 结束判断、退潮、反证 |
| `retrospective` | 更晚的历史资料，站在未来回顾过去 | 复盘、识别反例（非“当时已知”） |
| `unknown` | 无法判断 | 仅占位，不作为强证据 |

**纪律**：`retrospective` / `subsequent` 证据**不得**被当作 Campaign 进行中的“当时催化”来支持启动/主升。它们只能作为 retrospective review、结束与反例的说明。

---

## 3. 三个已落库案例（Pilot 1-C0）

| 证据 | Campaign | temporal_relation | 说明 |
|---|---|---|---|
| E-2025-04（FSD 2026-05-21 才宣布入华） | C-2025-ROBOTAXI（6/22-8/31） | `retrospective` | 是 hindsight，只用于复盘约束（FSD 非点火的证明），**不得**作为 2025-06-22 的 point-in-time signal |
| E-2023-06（L3 准入文件成文 11/17） | C-2023-AD（6/12-7/19） | `subsequent` | 事后反证：证明夏季行情是“预期驱动”，**不是**夏季同期反证的一部分 |
| E-2024-01（车路云 20 城试点 7/3） | C-2024-V2X（6/11-6/25） | `subsequent` | 7/3 晚于 6/25 结束；政策后续信号，仅作 follow-up，不充当 6/25 前窗口的 catalyst |

---

## 4. 校验规则（validate_db）
- trigger / catalyst 事件日期不得晚于 Campaign `end_date`。
- 绑定 Campaign 的证据必须有 `temporal_relation`。
- 标为 `contemporaneous` 但日期晚于 `end_date` 的证据将被告警（疑似应标 subsequent/retrospective）。
- `retrospective` 证据允许任意时点，但**不得被绑定为 Campaign 进行中的主驱动**（由人工在 Review 时把关）。

---

## 5. C2 落地提醒
在 Pilot 1-C2（真实日线核验）中：
- 计算启动/峰值/ending 时只用 `contemporaneous` + `prior` 与交易日原始价格；`retrospective` 仅用于解释差异。
- 任何用“更晚资料”修正当时判断的行为，都须标注为 retrospective/subsequent，且不能改写 campaign 原研究日期。