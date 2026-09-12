# DATA_MODEL.md — 数据模型

本文件记录 **当前代码中实际存在** 的数据模型（`src/models/`），字段命名一律 snake_case，
与未来 SQLite / PostgreSQL 表结构一一对应。

数据文件自 V1.5 起位于根目录 `data/`（raw / candidate / verified / validation 四层，
语义见 data/README.md 与 docs/HISTORICAL_VALIDATION.md）；
`src/data/index.ts` 是唯一 re-export 出口。

当前实现与概念模型无已知冲突；差异在文末"差异记录"中标注。

---

## 1. Source — 信息来源

`src/models/source.ts`

| 字段 | 类型 | 说明 |
|------|------|------|
| source_id | string | 主键 |
| source_type | enum | personal / article / official / research / market_data / quant_verification |
| title | string | |
| author / url / published_at / description | 可选 | |
| captured_at | string (ISO) | 收录日期 |

经验材料的 source_type 只能是 `personal` / `article`，不能直接当作事实数据。

### RawExcerpt — 原始材料摘录（同文件）

字段：excerpt_id, source_id, text（保留原始口吻）, captured_at, related_rule_ids?

raw 层数据（`data/raw/excerpts.ts`），是 candidate Rule 与 Evidence 的最上游审计依据。

## 2. Rule — 一条待研究的历史规律假设

`src/models/rule.ts`

字段：rule_id, name, rule_type, base_sector, description, mechanism?, tags[], status, source_id, statistics?, created_at, updated_at

- rule_type：`seasonal_sector | event_driven | disclosure | other`
- status：`candidate | under_review | verified | weak | rejected | deprecated`
- **V1 数据只允许 `candidate` / `under_review`**；`verified` 必须有可追溯的统计来源。
- status 是单维生命周期字段。治理规范已区分 Evidence Status（L0–L4）与
  Verification Status（not_tested / under_review / statistically_supported / cross_validated / unsupported）
  两个维度，映射见 DATA_GOVERNANCE.md。**当前未拆分字段**，拆分列入 ROADMAP。
- statistics 当前只允许 `{ status: 'not_verified' }`，见第 11 节。

## 3. TimeWindow — 规律的时间窗口

`src/models/timeWindow.ts`

字段：window_id, rule_id, window_type, start_md?, end_md?, anchor_event?, start_offset_days?, end_offset_days?, preheat_days, note?

window_type 五种表达，**不可混用语义**：

| 类型 | 含义 | 例 |
|------|------|----|
| calendar | 固定日期窗口 | 06-01 → 08-31 |
| relative_event | 相对锚点事件 + 偏移 | 春节前20天 → 节后30天 |
| holiday | 节假日相关 | （预留） |
| regulatory | 监管/披露节点 | （预留） |
| empirical | 经验估计窗口（日期未精确验证） | 约11月 → 次年1月15日 |

- `start_md` / `end_md` 为 `MM-DD`；`end_md < start_md` 表示跨年窗口。
- `relative_event` 的跨年由锚点日期 + 偏移的实际结果决定，不写死。

## 4. HistoricalCampaign — 一次真实发生的历史行情

`src/models/campaign.ts`

字段：campaign_id, rule_id, season_id, campaign_year, start_date, end_date, peak_date?, cross_year, strength, result, description?, source_id, start_date_basis?, end_date_basis?, date_confidence?

- strength：`strong | medium | weak`
- result：`positive | neutral | weak | failed | unknown` —— **必须允许失败/弱表现年份，不能只保存成功案例**。
- start_date / end_date 为完整 ISO 日期；`peak_date` 为行情峰值，未核验时为 null（合法状态）。
- `start_date_basis` / `end_date_basis`：`observed | inferred | official_event | unknown`
  （启动/结束日期判定方式，人工核验机制，见 HISTORICAL_VALIDATION.md）。
- `date_confidence`：`high | medium | low`。
- 约束：end_date ≥ start_date；跨年时 cross_year=true 且 end 年份 > start 年份。

### Cross-Year 定义

跨年行情是一条完整记录，示例：

```
season_id:      2026-2027
campaign_year:  2026
start_date:     2026-11-01
end_date:       2027-01-15
cross_year:     true
```

不得拆成 "2026 广电" 和 "2027 广电" 两条。

## 5. Theme — 题材（支持父子层级）

`src/models/theme.ts`

字段：theme_id, name, theme_type（sector / industry / concept）, parent_theme_id?, description?

Base Pattern（底层行业）与 Annual Theme（年度题材）通过父子层级分离：

```
汽车（sector）
  ├─ 减速器（concept，2023）
  ├─ 自动驾驶（concept，2024）
  └─ 智能座舱（concept）
```

## 6. CampaignTheme — 行情 ↔ 题材

`src/models/theme.ts`

字段：campaign_id, theme_id, role（main / secondary / catalyst / related）

## 7. Security — 代表股票

`src/models/security.ts`

字段：security_id, ticker, name, exchange（SH/SZ/BJ）, sector?

V1 为空表。**不得凭空生成龙头股。**

## 8. CampaignSecurity — 行情 ↔ 股票

`src/models/campaign.ts`

字段：campaign_id, security_id, role（leader / second_leader / follow / representative）

## 9. Event — 日历事件

`src/models/event.ts`

字段：event_id, name, event_type（holiday / regulatory / macro / industry / market / experience）, date_rule, description?, source_id?

date_rule 三种形态：

- `{ kind: 'fixed', md }` — 固定日期（国庆）
- `{ kind: 'range', start_md, end_md }` — 固定范围（中报披露期）
- `{ kind: 'variable', approx_md, dates: {年: MM-DD}, description? }` — 变动日期（春节，逐年登记）

## 10. Observation — 当前人工观察

`src/models/security.ts`

字段：observation_id, date, theme_id, description, confidence（low/medium/high）, source_id?

**Observation 不得直接修改 Rule。** V1 已建模，UI 尚未实现。

## 11. Evidence — 历史证据（V1.5 新增）

`src/models/evidence.ts`

字段：evidence_id, source_id, evidence_type, description, date?（可 null）, confidence, rule_id?, campaign_id?, theme_id?, notes?

- evidence_type：`market_data | article | official | news | manual_review | other`
- confidence：`high | medium | low`
- 概念链：Source → Evidence → Historical Fact / Campaign。
- **Evidence 是证据，不是结论**：只记录"来源说了 / 显示了什么"，是人工核验的输入。
- date 为 null 表示来源未提供日期（合法状态，禁止编造）。
- 数据位于 `data/validation/evidence.ts`；当前 6 条，全部为 article 型（src_exp_001）。

## 12. ValidationRecord — 核验记录（V1.5 新增）

`src/models/validation.ts`

字段：validation_id, rule_id, campaign_id?, evidence_status, verification_status, reviewer, created_at, reviewed_at, notes, method_version

- evidence_status：`L0 | L1 | L2 | L3 | L4`（证据等级，见 DATA_GOVERNANCE.md）
- verification_status：`not_tested | under_review | statistically_supported | cross_validated | unsupported`
- 只记录"事实是否核验"，**不计算统计分数**。
- `created_at`：核验记录的建立日期（ISO）。
- `reviewed_at`：**人工核验完成日期，可空**（`string | null`）。未核验时
  `reviewer = 'pending'` 且 `reviewed_at = null`——没有核验人就不得有核验完成日期。
- method_version 保证核验方法可追溯。
- 数据位于 `data/validation/records.ts`；当前 3 条（对应 3 条 Pilot），全部 not_tested。

### PilotPlan — 核验计划（同文件）

字段：pilot_id, rule_id, sample_name, base_pattern, test_focus[], status, created_at

status：`planned | in_progress | fact_verified | statistically_verified`。
数据位于 `data/validation/pilot.ts`；当前 3 条 Pilot（夏季汽车 / 年底广电 / 国庆后大消费）。

## 13. Statistics — 统计占位

`src/models/common.ts` 的 `StatisticsPlaceholder`

V1 不允许伪造 seasonality_score / win_rate / success_rate。
没有真实统计结果时：`{ status: 'not_verified' }`。

未来 V1.5 可计算字段（必须可追溯方法论）：sample_count, launch_date_median, launch_date_std,
average_duration, excess_return, repeat_rate, seasonality_score。

---

## 差异记录（当前实现 vs 概念模型）

| 项 | 状态 |
|----|------|
| 实体字段 | 与概念模型一致，无冲突 |
| Rule.status 维度 | 单维生命周期字段；治理规范已区分 Evidence / Verification 双维度（见 DATA_GOVERNANCE.md 映射表），字段拆分列入 ROADMAP，当前不改代码 |
| 数据源形态 | 类型化 TS 模块，位于根目录 `data/` 四层目录（raw / candidate / verified / validation），经 `src/data/index.ts` barrel 导出。字段名与 SQL 对齐，迁移时按目录语义建表 |
| verified 层 | 已建目录与空表（`data/verified/campaigns.ts`，0 条）——人工核验完成前保持为空 |
| 市场日期基准 | `marketTodayISO()`（src/utils/date/dateUtils.ts）：A 股"今天"固定基于 Asia/Shanghai，不随用户机器时区漂移；纯日期运算仍用 UTC |
| Observation | 已建模，V1 UI 未实现（符合预期） |
| Security / CampaignSecurity | 已建模，V1 为空表（符合"缺少数据是合法状态"原则） |
