# 半导体官方指数并列展示 · Wave 2.1 交付报告（v0.1）

> 基线：`origin/main = 24a9e2de`（v0.55 Wave 2 调查结论）。
> 核验日期：2026-10-25。
> 计算脚本：`research/scripts/build_official_index_parallel_v0_1.py`
> 测试：`research/scripts/test_official_index_parallel.py`（8 项）· `src/data/timeline/__tests__/officialIndexBlock.test.tsx`（7 项）

---

## 0. 一句话结论

**计算与展示能力已完成并验证；生产接入因授权未明确而暂缓。**
官方指数派生收益**不写入** `research/current/`、**不上公开页面**，只落 `.tmp/` 本地实验输出。
授权闸门写在代码里（`REFUSE` + 退出码 2），不是口头约定。

---

## 1. 实际覆盖事件数：**7 个**（以仓库清单为准）

从 `research/current/semiconductor_ai_compute_historical_events_v0_6.json` 读取，**不硬编码数量**：

| # | 事件 | `market_performance.window`（规范字段） |
|---|---|---|
| 1 | `SEMI-2019-LOCALIZATION` | 2019-05-16 → 2020-07-14 |
| 2 | `SEMI-2020-CHIPSHORTAGE` | 2020-12-01 → 2021-12-31 |
| 3 | `SEMI-2021-EQUIPMENT` | 2021-04-01 → 2021-07-30 |
| 4 | `SEMI-2022-DOWNTURN` | 2022-01-04 → 2022-10-12 |
| 5 | `SEMI-2023-AI-COMPUTE` | 2023-01-30 → 2023-04-10 |
| 6 | `SEMI-2024-FUND3` | 2024-09-24 → 2024-11-29 |
| 7 | `SEMI-2025-MEMORY` | 2025-07-01 → 2025-10-31 |

★ **窗口只读 `market_performance.window`**，不从 `window_text` 猜。7/7 都有规范窗口，**0 个缺口**。

---

## 2. 计算口径（统一，不随事件变）

| 项 | 口径 |
|---|---|
| 指数 | `H30184` 中证全指半导体产品与设备指数（发布 2013-07-15 / 基日 2004-12-31 / 基点 1000） |
| 基准 | `000300` 沪深300（官方同源） |
| 区间收益 | `末交易日 close / 首交易日 close − 1` |
| 超额 | 本指数区间收益 − 基准区间收益（**pp**） |
| 交易日 | 只取官方序列中**实际存在**的交易日；**不插值、不补造、不缩窗口** |
| 首尾口径 | 两端都取**窗口内实际存在的第一个/最后一个交易日**收盘点位，**不含窗口前一日的涨跌**；窗口首末若为非交易日，自动落到最近的实际交易日 |

★ **指数身份**：官方「半导体产品与设备」行业指数（设计/制造/封测/设备/材料），
**不是** AI 算力专用指数 —— 该说明已写进 `identity_note` 与 `calculation_note`，页面上也会显示。

---

## 3. 复算结果（只报结构与状态，不列数值）

| 项 | 结果 |
|---|---|
| 计算完成 | **7 / 7**（0 缺口） |
| 官方序列覆盖 | 2005-01-01 → 2026-10-23（5,296 行） |
| `rows_before_publish` | **2,068**（由**实际获取的完整序列**统计，非手写常数） |
| `backfilled`（窗口级） | **7/7 = `false`** —— 全部窗口起点 ≥ 2019，晚于发布日 2013-07-15 |
| 数据自洽 | v0.55 已核：`close/prev_close−1` vs 接口 `changePct`，5,293 行中位差 0.0026pp，仅「首行/发布日」两处口径差异 |

★★ **为什么不列每个事件的收益数字**：授权未明确（见 §5）。真实派生数值只写入
`.tmp/official_index_parallel_v0_1.json`（本地实验输出，`.gitignore` 已覆盖，未提交）。
本报告只记录**能证明计算正确性**的结构性事实。

★ **`backfilled=false` 不等于「指数序列没有回溯段」**：指数级仍有 2,068 行发布前数据，
只是这 7 个事件窗口都没用到它。页面上这两件事**分开显示**。

---

## 4. 字段结构（`official_index`，与 `market_performance` **并列不合并**）

```
provider · index_code · index_name · identity · identity_note
published_from · base_date · base_value
source_first_date · source_last_date · rows_before_publish · backfilled
window · window_actual{first_trade_date,last_trade_date,first_close,last_close,trading_days}
period_return_pct · benchmark_index_code · benchmark_index_name · benchmark_return_pct
excess_period_pp · price_basis · source_url · benchmark_source_url
status · error · calculation_note · missing_required_fields?
```

强制语义（由测试守住）：

| 字段 | 语义 | 缺失时 |
|---|---|---|
| `rows_before_publish` | **由实际序列统计**的发布前行数 | 显式列入 `missing_required_fields` |
| `backfilled` | **窗口级**三态：`true` 含发布前数据点 / `false` 全在发布后 / `null` 未知 | 页显示「未知」，**不得**当 `false` |
| `period_return_pct` / `excess_period_pp` | 不可计算时 **`null`** | 页显示「字段缺失」，**不补 0** |
| `window` | 只来自 `market_performance.window` | `NO_WINDOW` 状态 + 缺口说明 |

---

## 5. 授权结论：**未解决（UNCLEAR）**

| 项 | 内容 |
|---|---|
| 实测 | 中证官网日线接口**公开可访问、无需 token / 积分 / 登录** |
| 已查 | 官网首页、条款类路径（`about/statement` 等 3 条路径均 404）、公开检索 |
| 未找到 | 允许「**公开再发布派生行情数据**」的明确许可声明 |
| 结论 | **公开可访问 ≠ 许可公开再发布** → 判定 `UNCLEAR` |
| 后果 | 真实派生收益**不写入** `research/current/` 生产产物、**不在**公开 Pages 展示 |
| 代码闸门 | `--write` 默认只写 `.tmp/`；写 `research/current/` 必须 `--i-have-license --license-basis "…"`，否则 **`REFUSE` + rc=2 且不创建文件**（有测试） |
| 待办 | 需人工向中证指数确认授权范围 —— **属治理决策，本轮不代为假定** |

---

## 6. 展示层（已实现，生产页面当前不渲染）

`HistoricalEventMap` 新增 `OfficialIndexBlock`，位置在「实测行情」之后、独立成区：

- 表头：指数 / 窗口（声明）/ 区间收益 / 基准 / 超额；
- 明细行：指数名 + 代码 + `identity` 徽标；`window_actual` 显示**实际首末交易日与交易日数**；
- 元信息行：发布日 / 基日 / 基点 / 官方序列覆盖 / **发布前数据点行数** / 价格口径；
- **回溯说明三态**：`true` 强警示「事后回溯、不得作当时可知证据」/ `false` 说明「窗口全在发布日之后，
  但序列本身仍含回溯段」/ `null` 显示「未知，不得当作 false」；
- 来源链接（指数 / 基准各一条）+ 「公开可访问 ≠ 许可再发布」声明。

★★ 三条硬约束：**不合并口径**（不出现合成收益值）· **不改结论**（不因官方指数涨跌改机制判定）·
**不改研究状态**（不升级 `INSUFFICIENT`、不把参与者标成领导股）。

★ 生产现状：7 个事件均**没有** `official_index` → 该区块在生产页面**不渲染**（测试断言 7/7 为空）。

---

## 7. 检查结果

| 检查 | 结果 |
|---|---|
| `test_official_index_parallel.py`（8 项） | **OK** —— 收益/超额可复算 · `rows_before_publish` 由序列算 · `backfilled` 三态 · 交易日不足不补数 · 非交易日端点不插值 · 授权闸门拒绝生产写入且不建文件 · 缺窗口写缺口 · 指数身份非 AI 算力 |
| `officialIndexBlock.test.tsx`（7 项） | **OK** —— 字段渲染 · 三态语义 · 缺失显示「字段缺失」不补 0 · **不覆盖**原 `board`/`market_performance`（逐个股数值前后一致、官方值只在官方区块）· 无 `official_index` 时不渲染 · 两个 RC 状态与角色计数不变 · 覆盖全部 7 事件 |
| 角色 `--check` | PASS（33 事件 · 84 角色 · PIT 0 违规） |
| 审计 `--check` | PASS（135 信号日） |
| `refresh_downstream --check` | **0 FAIL** |
| `tsc -b --force` | 干净 |
| 全量前端 | 见提交信息（1493 项） |

★ 测试**全部使用合成 fixture**（`T99999` / 假数值），不依赖网络、不含真实官方数值。

---

## 8. 尚存限制

1. **授权未明**：真实派生收益不能进生产产物、不能上公开页面 —— 这是当前唯一的阻断项。
2. **历史成分仍不可得**：`consNumber` 只给数量；名单只有最新快照 + 调样公告。本对象**不含任何成分信息**，
   也**没有**用当前成分冒充历史成分。
3. **指数语义边界**：`H30184` 是「半导体产品与设备」，不是 AI 算力指数；对 `SEMI-2023-AI-COMPUTE`
   这类事件只能算**行业层代理**，页面 `identity_note` 已写明。
4. **未接入生产管线**：`market_data.db` / `history_scan.db` 未写入任何官方指数序列；
   接入方式（新表 vs 快照文件）尚未决策。
5. 东财 `push2his` 本机仍不可达（不影响本轮，因官方源已够用）。

---

## 9. 授权明确后的实施顺序（备查）

1. 填 `--license-basis` 并生产写入 `official_index`（7 事件）→ 页面自动显示；
2. 把 `published_from` / `rows_before_publish` / `backfilled` 设为**强制字段**（缺则 FAIL，不静默）；
3. 决定官方序列入库方式（建议独立表 + 快照，不混入现有 `scan_daily`）；
4. 再评估医药 `000933`（PROXY）与电力 `H30199`（口径未决，见 Wave 2 §5）。
