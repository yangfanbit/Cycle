# AGENTS.md — 项目宪法

本文件是 **A股机会时间轴** 仓库的最高级开发规范。
任何 AI Agent / 模型 / 人类协作者在开始修改本仓库前，**必须先完整阅读本文件**。

阅读顺序：AGENTS.md → docs/PRODUCT.md → docs/DATA_MODEL.md → docs/DATA_GOVERNANCE.md → docs/HISTORICAL_VALIDATION.md → docs/ARCHITECTURE.md → docs/UI_SPEC.md → 具体任务 Prompt。

---

## 1. 项目定位

项目名称：**A股机会时间轴**（A-Share Opportunity Timeline）

核心定位：

> 以时间为主线，把 A 股历史上反复出现的行业、题材、事件与行情窗口放在同一条轴上，
> 对比历史、观察当年偏离，寻找下一阶段值得提前关注的方向。

核心问题只有三个：

1. 今天处于全年时间轴的什么位置？
2. 历史上这个时间附近发生过什么？
3. 接下来哪些历史规律值得提前观察？

本项目**不是**：

- 荐股软件
- 买卖信号系统
- 收益预测系统
- 大盘预测系统
- 自动交易系统

---

## 2. 数据与认知边界（不可逾越）

以下概念严格区分，逐级不可跳跃：

```
Source（来源） ≠ Evidence（证据） ≠ Rule（规律假设） ≠ Historical Fact（历史事实）
≠ Verification（统计验证） ≠ Prediction（预测）
```

- 别人提出的经验，只能作为**候选规律来源**（Source → candidate Rule）。
- 不得因为数据"看起来合理"，就自行把 `candidate` 改成 `verified`。
- **Evidence 是证据，不是结论**：它只记录"某来源说了 / 显示了什么"，是人工核验的输入，
  本身不构成历史事实。材料提及 ≠ 发生过，更 ≠ 规律成立。
- 核验数据（`data/`）的录入与升层规则见 docs/HISTORICAL_VALIDATION.md。

### 两个独立维度：证据 ≠ 验证

**Evidence Status（证据状态）**——我们掌握了多少历史证据：

```
L0 原始经验/未核验 → L1 找到历史证据 → L2 人工完成历史事实核验
→ L3 已完成程序统计验证 → L4 多来源交叉验证
```

**Verification Status（验证状态）**——规律是否已通过验证：

```
not_tested → under_review → statistically_supported / cross_validated / unsupported
```

关键：**L2 ≠ 规律成立**。
例："已逐年核验 2018—2025 年广电行情"只说明 `evidence_status = L2`（事实核验完成），
不代表 `verification_status = statistically_supported`（规律验证完成）。
只有真正完成统计验证后才能标记 `statistically_supported`。

### 核验范围：Rule ≠ Campaign

ValidationRecord 的 `validation_scope` 必须区分核验对象：

- `'rule'`：验证整条 Rule（规律假设本身），campaign_id 省略；
- `'campaign'`：验证具体 HistoricalCampaign 的历史事实，campaign_id 必填。

两者不得混淆：Campaign 事实核验完成（L2）不等于其所属 Rule 成立；
Rule 成立必须经过统计验证（L3+，statistically_supported）。

### 前瞻性分析 ≠ 确定性预测

本项目禁止：

- 确定性未来预测
- 保证收益
- 个股买卖建议
- "必涨 / 必跌"等结论
- 自动交易信号

但允许（未来阶段）：

- 历史统计、历史相似案例、当前状态识别
- 时间窗口分析、历史条件分布、情景分析
- 前瞻性观察窗口、"提前观察"提示

即使未来完成统计验证，展示的也是"历史统计特征"，不是未来承诺。

---

## 3. Agent 开发原则

任何 Agent 开始修改代码前必须：

1. 阅读 AGENTS.md。
2. 阅读 docs/ 下与任务相关的文档。
3. 检查现有实现，搜索是否已有相关代码。
4. **优先修改已有实现**，避免重复逻辑。
5. 修改后运行相关测试（`npm test`）与类型检查（`npx tsc -b`）。
6. 如修改数据模型或核验数据（`data/`），必须同步更新 docs/DATA_MODEL.md、
   docs/HISTORICAL_VALIDATION.md 与 docs/CHANGELOG.md。
7. 修改 `data/` 核验数据前必须阅读 docs/HISTORICAL_VALIDATION.md；
   candidate → verified 的升层必须在 CHANGELOG.md 留痕，禁止为填充 verified 层而编造事实。

任何 Agent 不得：

- 擅自重构核心数据模型（`src/models/`）。
- 擅自改变产品定位（见第 1 节）。
- 擅自增加实时交易、荐股、买卖信号逻辑。
- 擅自把经验描述改写为"市场事实"。
- 擅自引入新的测试框架、构建工具或数据库（变更技术栈需先修改 docs/ARCHITECTURE.md 并在任务 Prompt 中明确授权）。

---

## 4. 冲突处理

如果任务 Prompt 与本规范冲突：

- **优先遵守本规范**。
- 不得偷偷选择其中一个执行。
- 必须在最终报告中明确指出冲突点。
- 若确有必要变更规范，说明建议如何修改规范本身，并等待确认。

---

## 5. 最小修改原则

- 除非存在明确 Bug 或架构性问题，不重写已有功能。
- 优先 incremental change，不做"为了更优雅"的重构。
- "未来可能需要"不是现在实现的理由——记入 docs/ROADMAP.md，而不是代码。
- 每轮修改必须说明：改了什么、为什么改、为什么属于必要修改。

---

## 6. 产品红线（V1 及默认状态）

除非任务 Prompt 明确授权进入对应阶段（见 docs/ROADMAP.md），否则禁止：

- 接实时行情 / 实时资金流 / 实时异动监控
- AI 预测、确定性未来预测
- "必涨 / 必跌"等结论
- 买入 / 卖出 / 建仓 / 清仓等操作建议
- 股票推荐
- 自动交易信号
- 自动消息推送
- 用户登录 / 权限系统
- 自动爬虫
- 伪造胜率、季节性评分等量化结论

UI 文案中 "买入/卖出/建仓/清仓/推荐" 等词只允许出现在**否定性免责声明**中（如"不构成买卖建议"）。
