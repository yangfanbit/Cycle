# Pilot 1-C1 最终报告：行情事实核验基础设施

> 目标：为下一阶段（Pilot 1-C2：用真实日线核验 2020–2025 Campaign 日期）建立**基础设施**。
> 本轮**未**新增任何 2021–2025 研究结论、**未**修改任何 Campaign 日期、**未**计算 Seasonality/胜率/Sharpe/alpha/概率、**未**开始最终统计。
> 方法学详见 `research/methodology/market_data_validation.md`。

---

## 1. 新增表（4 张）

| 表 | 用途 | 关键列 |
|---|---|---|
| `market_series` | 行情序列定义（指数/行业/概念/个股/基准） | series_id, name, series_type, provider, symbol, frequency, price_type, adjustment_method |
| `market_daily` | 日线行情，**每行明确价格口径** | (series_id, trade_date, price_type) PK, OHLC, adj_close, volume, amount, data_source, retrieved_at |
| `trading_calendar` | 交易日历 | trade_date PK, is_trading_day, calendar_type |
| `campaign_date_observations` | Campaign 日期核验观测 | candidate_date(保留) / verified_date(核验后可空) 分列，date_role, verification_method, confidence, evidence_id |

**核心不变量**：全部通过 `schema.sql` 定义，且 `scripts/db.py` 的 `migrate()` 幂等建表（对已有数据库可直接升级，不破坏既有数据）。`sources / evidences / campaigns / annual_reviews` 等原表**未改动**。

## 2. 数据目录

```
data/market/
├── raw/          原始下载行情（未统一字段，可追溯；如 `akshare_AUTO_SW_daily.csv`）
└── normalized/   统一字段后的行情（对应 market_daily 口径，可导回）
```

- `raw` 保原始、不统一字段、不复权。
- `normalized` 统一字段并声明 `price_type`。
- 两者严格区分（§12）。当前均为空占位（`.gitkeep`），等待 C2 灌入真数据。

## 3. Market Series 设计

- `series_type ∈ {industry_index, sector_index, concept_index, stock, benchmark, other}`。
- `symbol` **只填真实可确认代码**（如 `000300.SH` 沪深300、`801880.SI` 申万汽车），不确定留空（NULL），**不编造**。
- 已注册：`SH000300`（基准）、`AUTO_SW`、`AUTO_PARTS`（symbol 待核实）、`NEV`、`AD_AUTO`、`V2X`、`ROBOTAXI`（概念成分变化大，symbol 待核实，仅参考）。
- 每条声明 `price_type`（主口径）+ `adjustment_method`。

## 4. Daily Market Data 设计

- 行 = 某序列某交易日某口径的一条记录；PK `(series_id, trade_date, price_type)`。
- **raw / adjusted 分列**：`adj_close` 仅在 adjusted 行使用，raw 行禁止带 `adj_close`（validate 会 FAIL）。
- 同一 `series/date/price_type` 唯一 → **原始数据可追溯、禁止自动覆盖已有数据**。
- 记录 `data_source` / `retrieved_at` 保证溯源。

## 5. Candidate / Verified Date 如何区分

- `campaign_date_observations.candidate_date`：**从 `campaigns.start/end/peak_date` 原样快照**，永久保留（`seed_campaign_dates.py` 已为 8 个 Campaign 生成 23 条候选观测）。
- `verified_date`：独立列，核验完成前为 `NULL`；C2 用日线确认后再填。
- 两层分离 → **candidate 不会也不允许覆盖 verified**（validate 测试6 校验候选与 campaigns 一致）。
- `date_role ∈ {start,end,peak}`；`verification_method ∈ {manual, market_data, market_data_plus_event, unknown}`；`confidence ∈ {high,medium,low}`。

## 6. Trading Day / Calendar Day 区分

- **Calendar Day（自然日）** = 含周末/节假日的日历日。
- **Trading Day（交易日）** = 实际开市日。
- `market_daily.trade_date` 与 `trading_calendar.trade_date` **只取交易日**。
- 无独立日历源时，允许由 benchmark series 的 `distinct trade_date` 推导（编写进 `trading_calendar`）。
- C2 计算“启动后第 N 天”须按交易日而非自然日口径（README §4.2 + 方法学 §3）。

## 7. Price Policy

- **raw close** → 日期判断（启动/峰值/终点，在原始交易日序列上识别）与真实成交价叙述。
- **adjusted close** → 收益率计算（避免股本/送转/分红干扰）。
- 日期判断优先使用交易日原始序列；收益计算必须明确口径。
- **同一指标禁止混合不同调整口径**（`market_metrics.py` 每个函数带 `price_mode` 语义）。
- 见 README §4.1 与方法学 §6。

## 8. Survivorship Bias / Look-ahead Bias 防护

- **Survivorship**：历史概念成分 ≠ 当前成分股列表。Breadth 类指标必须基于**当日/当季真实成分快照**；本轮**不生产 Breadth 结果**，仅预留 `ThemeBreadthSnapshot.require_history_snapshot()` 接口（避免用当前成分回测历史造成 `no data → raise`，不编造）。
- **Look-ahead**：核验 `verified_date` 只使用该时点已知信息；不把事后确立的概念/成分回填到过去。前复权会因新除权事件重组历史数值，做“当日状态”判断以 raw 为准。
- `validate_db` 测试10（结构性）：本项目无“基于当前成分自动写历史 market_daily”的入库通道。

## 9. 是否修改已有 Campaign

**本轮没有修改任何已有 Campaign。**

- `campaigns.start_date/end_date/peak_date` 全部原样保留。
- 2021–2025 未新增 Campaign（保持 2018 no_clear / 2019 weak / 2020 strong / 2021 strong / 2022 strong / 2023 medium / 2024 medium / 2025 medium 不变）。
- `campaign_date_observations` 只是**快照引用**原日期，不回写 campaigns。

## 10. 测试结果

| # | §15 测试 | 结果 |
|---|---|---|
| 1 | Market Series 唯一性 | PASS（series_id 主键 + name 非空） |
| 2 | Daily Market Data 外键 → market_series | PASS（无孤儿） |
| 3 | trade_date 格式（ISO） | PASS（含 calendar） |
| 4 | 同一 series/date 不重复 | PASS（PK + 显式分组查） |
| 5 | raw / adjusted 区分、禁口径混用 | PASS（raw 行不得带 adj_close） |
| 6 | candidate 不覆盖 verified | PASS（候选与 campaigns 一致） |
| 7 | Date Observation 引用有效 Campaign | PASS（FK） |
| 8 | evidence_id 若存在必须有效 | PASS（FK） |
| 9 | raw/adjusted 价格口径明确 | PASS（每行必有 price_type） |
| 10 | 不用未来成分回填历史 | PASS（结构性无该通道） |
| 11 | export 不混入无关 Market Data | PASS（export 不查 market_*） |

`validate_db.py` 输出：**PASS（0 FAIL）**；`export.py` rebuild 同前（8 campaigns，evidence 隔离 PASS）；`gen_annual.py` 对既有年份重生成无回归。数据库可正常初始化（`db.init_db` / `db.migrate` 幂等）。

## 11. 是否具备开始“2020/2021 Campaign 日期行情核验”的条件

**是，基础设施已就绪**，但有两个前置注意点：

1. **已具备**：四表 + 度量函数 + 方法学 + 候选日期快照 + 校验全通过；C2 可读取真实日线（raw、交易日口径）对 2020/2021 Campaign 的 start/peak/end 做 `relative_return_vs_benchmark` / `drawdown` / `volume_change` 核验并填 `verified_date`。
2. **需在 C2 首步落地**：实际灌入 `data/market/raw` 的真实行情（优先 AkShare 免费源，`AUTO_SW` 与 `SH000300`）；确认 `AUTO_PARTS` 等 symbol；可选从 `SH000300` 推导交易日历。Breadth 因缺历史成分快照留待专门建设。

> 结论：本轮为 **C2 的准确前置**，已闭环。下一步即进入 Pilot 1-C2。

---

*本报告与 `research/methodology/market_data_validation.md` 配套；所有数据可经 `exports/cycle_verified_candidates.json` 与 SQLite 复查。*