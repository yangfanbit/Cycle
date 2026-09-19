# AGENTS.md — ThreeC 项目宪法

> 接手顺序：先读本文件，再读 `docs/PROJECT_STATE.md`。只有任务涉及 Research / Product 具体实现时，再读取对应局部文档。
> **本文件只放长期有效规则；当前阶段、数字、下一步不写在这里。**

## 1. 项目初心

ThreeC = **A股历史机会时间轴 / 历史机会地图**。

核心链路：

`今天的位置 → 历史同期 → Theme / Campaign 生命周期 → 相关因素 → 提前观察 → 当前状态与历史结构对照`

产品目标是帮助用户**发现值得继续研究的方向**，不是交易决策系统。

禁止把 ThreeC 做成：
- 买卖信号 / 自动交易
- 荐股 / 选股
- 价格或收益预测
- 概率 / 胜率 / 推荐分
- 实时行情 / 资金异动监控
- 学术型历史数据库

## 2. 一个项目、两层系统

仓库只有一个 Git、一个项目根目录、一个 canonical Research、一个 Product。

- `src/`：Product，React + TypeScript + Vite
- `research/`：Research，Python + SQLite
- `exports/`：Research → Product 唯一交换目录
- `contracts/`：Export contract
- `docs/`：项目规范、状态、路线与审计记录

逻辑边界必须保持：

> **Research 生产研究结论；Product 消费研究结果。**

Product runtime 不联网、不调用 LLM、不自行生成研究结论。

## 3. 数据与研究原则

永久有效的概念链：

`Source ≠ Evidence ≠ Rule ≠ Historical Fact ≠ Verification ≠ Prediction`

必须遵守：

- 不编造历史事实、日期、涨幅、代表股或统计结论。
- 缺少证据是合法状态，使用 `UNKNOWN / NOT_AVAILABLE / INSUFFICIENT` 表达。
- `PROVISIONAL ≠ VERIFIED`。
- 失败年份保留，不为让规律成立而删除。
- Research Candidate 不自动成为正式 Campaign。
- Theme / Name 相似不等于 Structural Correspondence。
- 历史比较必须遵守 Point-in-Time / Temporal Firewall，禁止 look-ahead。

## 4. Frozen 基座

除非明确授权，不修改：

- Research Model v1.0
- `research/schema/schema.sql`
- `contracts/timeline_export_v1.md` 与 canonical export v1.0
- 已冻结历史研究结论
- 既有轮次产物的 provenance

新增研究轮次必须新建 round / artifact，**不得覆盖旧轮次**。

Canonical Macro Theme Resolution = **CMTR v1**，唯一实现：
`research/scripts/theme_taxonomy.py`。

Structural Analogy 当前冻结规则以：
`research/research/methodology/structural_analogy_rule_set_v0_2.md`
为准，后续执行不得擅自调规则。

## 5. Product 语义边界

当前产品的四个核心视角必须保持区分：

- **Timeline**：历史机会主体，第一视觉。
- **Calendar Lens**：这个时间附近历史上发生过什么。
- **Lifecycle Lens**：历史上处于类似生命周期位置的案例。
- **Structural Analogy**：当前结构与历史结构有哪些可解释的对应与不对应。

“相似”必须说明**为什么**，不能只给一个分数。

## 6. Git 安全

禁止未经明确授权执行：

`git reset --hard` · `git clean -fd` · `git checkout/restore 覆盖工作` · force push · 已推送历史 rebase · commit amend · `git add -A` · `git add --renormalize`

Research / export / contract 文件保持 LF 与逐字节可复现；Windows 编辑后必须检查 EOL。

## 7. 每次任务默认工作方式

1. 先自行核对真实 HEAD / working tree / 当前状态。
2. 读取必要的文档，而不是把整个仓库重新“培训”一遍。
3. 只修改本任务允许的范围。
4. 先验证，再写结论。
5. 完成目标即停止，不顺手扩范围。

> 动态状态请以 `docs/PROJECT_STATE.md` 为准；未来路线请以 `docs/ROADMAP.md` 为准；历史细节以 `docs/CHANGELOG.md` 为准。
