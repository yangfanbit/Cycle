# DATA_GOVERNANCE.md — 数据治理标准

## 两个独立维度：证据 ≠ 验证

### Evidence Status（证据状态）——我们掌握了多少历史证据

| 等级 | 含义 |
|------|------|
| L0 | 原始经验 / 外部观点 / 未核验 |
| L1 | 找到历史证据（有个案） |
| L2 | 人工完成历史事实核验（逐年被核实） |
| L3 | 已完成程序统计验证 |
| L4 | 多来源交叉验证 |

### Verification Status（验证状态）——规律是否已通过验证

| 状态 | 含义 |
|------|------|
| not_tested | 未验证 |
| under_review | 验证中 |
| statistically_supported | 统计支持（L3 完成） |
| cross_validated | 多来源交叉验证（L4 完成） |
| unsupported | 验证后不成立 |

**关键原则：L2 ≠ 规律成立。**

例："已逐年核验 2018—2025 年广电行情"只说明 `evidence_status = L2`（历史事实核验完成），
不代表 `verification_status = statistically_supported`。
只有真正完成统计验证后才能进入 `statistically_supported`。

### 与当前代码字段的映射

当前代码中 `Rule.status`（candidate / under_review / verified / weak / rejected / deprecated）
是单维生命周期字段，对应关系：

| Rule.status | evidence | verification |
|-------------|----------|--------------|
| candidate | L0 | not_tested |
| under_review | L1–L2 | under_review |
| verified | L3–L4 | statistically_supported / cross_validated |
| weak | L3 | （统计支持度弱） |
| rejected | L3 | unsupported |
| deprecated | — | （规律已废弃，不再验证） |

未来推荐模型：将 `Rule.status` 拆分为 `evidence_status` 与 `verification_status` 两个字段。
**本轮不修改现有数据结构**，该拆分列入 ROADMAP（V1.5 数据迁移时一并评估）。

- 等级/状态跃迁必须写明证据来源（source_id）与日期，并在 CHANGELOG 记录。
- 发现反证时可降级，同样需记录。

## Source 原则

每条经验规律都必须能追溯到来源（Rule.source_id 必填）。

来源类型：personal / article / official / research / market_data / quant_verification。

- `article` / `personal` 来源的规律只能是 candidate（L0 / not_tested）。
- `quant_verification` 来源才能支撑 verified（statistically_supported 及以上）。
- **来源 URL 追溯**：已知原始来源 URL 的 Source 必须登记 `url` 字段
  （如 src_exp_001 登记了知乎原文链接），保证"经验从哪里来"可回溯；
  title 不确定时保持原 title，不得编造，但 URL 缺失不是合法状态——
  拿到 URL 后必须补登记。

## 市场日期基准（V1.5 Preflight 起）

本项目为 A 股研究工具，"市场今天是什么日期"固定基于 **Asia/Shanghai**
（`marketTodayISO()`，src/utils/date/dateUtils.ts），不随用户机器本地时区漂移：

- App 的 TODAY、Pre-heat / OpportunityRadar 的"今天"一律使用市场日期。
- 纯日期运算（diffDays / addDaysISO / 跨年分段等）仍使用 UTC 毫秒，
  与市场日期基准分离，避免 DST / 本地时区误差。
- 文档与数据中涉及"今天 / 当前窗口"的判断，基准均为 Asia/Shanghai。

## Evidence 原则（V1.5 起）

概念链：**Source → Evidence → Historical Fact / Campaign**。

- **Evidence 是证据，不是结论**：只记录"某来源说了 / 显示了什么"（字段见 DATA_MODEL.md 第 11 节），
  是人工核验的输入，本身不构成历史事实，更不得被改写成市场事实。
- 每条 Evidence 必须引用存在的 Source（evidence_id → source_id 可追溯）。
- 来源未提供日期时 `date = null`；未提供就是没有，禁止补写。
- "材料提及 2021 / 2022 / 2023 年广电行情"只能作为 L1 证据线索，
  不足以直接创建 Campaign 记录——必须逐年人工核验。
- 人工核验产出的历史事实进入 `data/verified/`，并保留指向 Evidence 的引用。

## 数据目录治理（V1.5 起）

```
data/
  raw/         原始数据（来源注册表 + 材料摘录）
  candidate/   未经核验的候选知识（规则 / 候选行情 / 题材 / 事件）
  verified/    已人工核验的历史事实（L2，当前 0 条）
  validation/  证据、核验记录、Pilot 计划
```

- candidate → verified 的每次升层必须在 CHANGELOG.md 留痕（依据 source_id / evidence_id）。
- 禁止为了填充 verified 层而编造事实；核验发现失败年份应更新 result 而非删除记录。
- 应用代码只能经 `src/data/index.ts` barrel 访问数据。

## 不允许的行为

- 不得伪造历史案例
- 不得补写不确定数据为确定事实
- 不得为了让规律看起来成立而删除失败年份
- 不得把作者观点直接改写成"市场事实"
- 不得凭空生成龙头股
- 不得凭空填写涨幅
- 不得凭空填写历史胜率

## "缺少数据"是合法状态

- 没有历史案例：UI 显示「历史案例待补充」
- 没有统计结果：`statistics.status = 'not_verified'`，UI 显示「未验证」
- 没有精确日期：使用 `window_type: 'empirical'` 并在 `note` 中说明估计性质
- 没有代表股票：Security 留空，UI 显示「暂无代表股票记录」

**不得通过编造内容来填空。**

## 经验描述的引用规范

- Rule.description 保留原始经验口吻，并标注「（原文为经验判断，未验证）」。
- 推测性机理写入 mechanism 字段并标注「待验证」。
- 近似日期必须在 description 或 note 中说明是近似值。

## 当前种子数据的诚信边界（V1.5 Preflight 后基线）

- 10 条候选规律：全部来自用户经验材料（src_exp_001），status = candidate。
- 生产行情层（allCampaigns = verifiedCampaigns）：**0 条**。人工核验未开始前，
  Timeline 第三层显示「暂无已核验历史行情（历史核验尚未开始）」。
- 材料"2023 汽车=减速器 / 2024 汽车=自动驾驶"的年度题材对应：仅登记为 Evidence
  （L1 线索），**不创建 Campaign**——未核验的 inferred/low 日期不得伪装为历史事实。
- 需求文档的跨年结构示例（2026-11-01 → 2027-01-15）：**不是真实历史行情**，
  已迁至 `tests/fixtures/campaignFixtures.ts`（测试专用），禁止进入 `data/` 任何层。
- 材料"提及 2021 / 2022 / 2023 年广电行情"但无任何细节：**未创建对应 Campaign**
  （仅登记 L1 证据线索），待人工核验——不得凭仅有年份的提及编造记录。

## V1.5 核验数据基线

- Evidence：6 条（`data/validation/evidence.ts`），全部 article 型、来自 src_exp_001、confidence = low。
- ValidationRecord：3 条（`data/validation/records.ts`），对应 3 条 Pilot
  （汽车 L1 / 广电 L1 / 大消费 L0），verification_status 全部 not_tested，
  reviewer = 'pending'、reviewed_at = null（审计字段语义见 DATA_MODEL.md 第 12 节）。
- verified 层：0 条。等待人工 Review 后进入"3 条 Pilot 规律的历史事实核验"阶段。
