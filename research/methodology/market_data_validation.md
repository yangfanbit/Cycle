# 行情事实核验方法学（Pilot 1-C1）

> 目标：把“媒体/研究结论”中的 Campaign 日期，与**真实市场日线数据**挂钩核验。
> 本轮只建立方法与基础设施，**不**修改任何 Campaign 结论、**不**做统计建模。
> 数据流：`Market Series → Daily Market Data → Date Verification → Historical Campaign`。

---

## 1. Market Series

`market_series` 描述一条可核验的行情序列：

- `series_id` / `name` / `series_type`（industry_index / sector_index / concept_index / stock / benchmark / other）
- `provider`：数据提供方（akshare / sw / csi 等免费源），**不写付费 token、不写凭证**。
- `symbol`：**只有真实可确认的代码才填**，不确定就留空（NULL），不编造。例：`000300.SH`（沪深300）、`801880.SI`（申万汽车）。
- `price_type`：本序列主价格口径，`raw` 或 `adjusted`；`adjustment_method` 记录复权方式（qfq/hfq）。

典型用于核验的序列（已注册，symbol 不一定都已核实）：
- `SH000300` 基准（沪深300）
- `AUTO_SW` 申万汽车行业指数
- `AUTO_PARTS` 申万汽车零部件（symbol 待核实）
- `NEV` / `AD_AUTO` / `V2X` / `ROBOTAXI` 概念（成分变化大，仅参考）

## 2. Daily Market Data

`market_daily` 存日线（open/high/low/close/adj_close/volume/amount），关键纪律：

- **每行必须明确 `price_type`（raw 或 adjusted）**，禁止同一行混用。
- `adj_close` 只在 `adjusted` 行使用；`raw` 行不允许带 `adj_close`（validate 会 FAIL）。
- 同一 `series_id + trade_date + price_type` 唯一（原始数据可追溯，**禁止自动覆盖已有数据**）。
- `data_source` / `retrieved_at` 记录来源与抓取时间，保证可溯源。

## 3. Trading Calendar（Trading Day vs Calendar Day）

**Calendar Day（日历日）** = 自然日，含周末与节假日。
**Trading Day（交易日）** = 该市场实际开市日（跳过周末与法定休市）。

- `trading_calendar.trade_date` **只填交易日**（`is_trading_day=1`），或记录休市日（`=0`）。
- 若没有独立日历源，**允许由 benchmark series 的 `distinct trade_date` 推导**（基准序列天然只有交易日）。
- 所有 `market_daily.trade_date` 必须是交易日；核验时“启动后第 N 个交易日”应基于交易日历，而不是自然日。
- 窗口漂移字段（`drift_vs_jun01` 等）在 C2 应改为基于交易日而非自然日口径重新说明。

## 4. Candidate Date 与 Verified Date

- **Candidate Date（候选/原始研究日期）** = 从媒体与研究结论得到的日期，**保留不改**（`campaign_date_observations.candidate_date` 快照自 `campaigns.*_date`）。
- **Verified Date（核验后日期）** = 用真实日线确认后的日期（`verified_date`）。核验完成前为 NULL。
- 不覆盖 `campaigns.start_date/end_date/peak_date`：**两者分列存**，candidate 永久保留，verified 是独立列。
- `verification_method`：`manual` / `market_data` / `market_data_plus_event` / `unknown`。
- `confidence`：`high/medium/low`。
- 可选 `evidence_id`（若存在必须有效），用于把核验结论锚定到证据。

## 5. 核验研究流程（Pilot 1-C2 执行）

```
Candidate Campaign
  → 读取该主题对应的 Market Series 日线（raw，交易日）
  → 检查：启动前后走势 / 相对基准强度(relative_return_vs_benchmark)
          / 板块强度 / 核心股 / 成交量(volume_change) / 市场扩散
  → 记录 Date Observation（candidate 原样 + verified 填写）
  → 人工确认
  → 最终才更新 Campaign Fact
```

**禁止自动判定**：“上涨5%” / “连续3天上涨” / “龙头涨50%”**都不是** Campaign 判定依据。
程序只负责：数据、计算、展示、记录候选日期。**Campaign 是否成立由人工决定。**

## 6. Price Policy

- **raw close**：用于日期判断（启动/峰值/终点在原始交易日序列上识别）与“真实成交价”叙述。
- **adjusted close**：用于收益率计算（不受股本/送转/分红干扰）。
- **日期判断优先使用交易日原始价格序列**；收益计算必须明确价格口径。
- **不允许在同一指标中混合不同调整口径**（e.g. 不能把 raw 与 qfq 插入同一收益序列）。
- `market_metrics.py` 每个函数都带 `price_mode` 语义，调用方负责保证单一口径。

## 7. Survivorship Bias（幸存者偏差）

- **历史概念成分不能简单使用当前成分股列表**。
- 例如“新能源汽车今日成分股”不能代表 2021 年的成分；用当前成分回测历史会遗漏已退市/被剔除的标的，高估表现。
- Breadth 类指标（上涨家数/涨停家数/平均/中位收益）**必须基于当日/当季真实成分快照**；本轮不生产，仅预留在 `ThemeBreadthSnapshot.require_history_snapshot()`。

## 8. Look-ahead Bias（前视偏差）

- **固定成分回填 / 用基本面当期披露之外的信息**会引入前视偏差。
- 核验 `verified_date` 时只使用该时间点**已知**的信息（当日价格、当时可得公告/政策），不得用事后数据的成分或新闻。
- 交易日推导只向前看已发生的数据；不把未来某时点确立的概念回填到过去。
- `rebuild/adjustment` 采用前复权时要意识到它会随新除权事件重组历史数值——做“当日状态”判断应参考 raw 序列。

## 9. 数据来源

- 第一阶段优先 **AkShare / 公共历史行情接口**（免费、无 key）。
- 接口不稳定则记录 `provider`，不阻塞。
- **不依赖付费 API**；**不把访问凭证/token 写入代码或配置文件**。

## 10. 审查清单（C2 每步自检）
- [ ] 只用交易日（Trading Day）序列
- [ ] 单一口径做单指标计算
- [ ] candidate 原样保留，verified 独立填写
- [ ] BREAADTH 依赖历史成分快照，不编造
- [ ] 全程人工确认 Campaign 是否成立