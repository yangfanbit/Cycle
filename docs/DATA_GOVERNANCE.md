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

## 当前种子数据的诚信边界（V1 基线）

- 10 条候选规律：全部来自用户经验材料（src_exp_001），status = candidate。
- cmp_auto_2023 / cmp_auto_2024：材料明确提到题材—年份对应；起止日期为典型窗口近似，已在 description 注明。
- cmp_media_2026_2027：需求文档的跨年结构示例（src_spec_001），**不是真实历史行情**，已在 description 注明。
