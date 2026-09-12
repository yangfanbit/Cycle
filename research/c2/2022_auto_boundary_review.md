# 2022 Auto Campaign Boundary Review（Pilot 1-C1.3.1）

> 对象：2022 汽车。基于真实日线（腾讯 GTIMG）：沪深300、AUTO_ETF_516110（2022 汽车行业代理）、比亚迪/长安/中通客车。
> 目的：把 `04-27 → 08-31` 这个 Campaign candidate 重新切分为 **Setup / Theme Formation / Main Campaign / Retracement / Decay**，并给出坐标 Theme Start / Peak-cluster / End-candidate。
> 本文件为 **research-level** 判断；**不改** 正式 `campaigns` / `annual_reviews` / `rule` / `Cycle` / `Cycle/data/verified`；verified 一律 NULL。
> 口径：signal=raw close；return=adjusted(qfq)。

---

## 1. 结论速览

| 阶段 | 区间 | 说明 |
|---|---|---|
| Setup（Industry Recovery） | 2022-04-27 → 05-13 | 全市场超跌反弹 + 复工复产/政策预期；主题未确认 |
| Theme Formation / Confirmation | 2022-05-23 → 06-01 | 05-23国常会购置税600亿=首个 Point-in-Time 主题催化；05-31细则；06-01落地买盘 |
| Main Campaign | 2022-05-23 → 06-28 | 政策+新能源主线主升 |
| Peak cluster | 龙头 06-23 / 行业代理 06-28 | 分散记录 |
| Retracement | 2022-07 | 高位回落/轮动 |
| Decay / decline_cluster | 2022-08（08-01二高点 → 08-31） | 未同步新高后持续衰减；**End 非机械 8/31** |

## 2. Theme Start Candidate（重点比较）

| 日期 | AUTO | HS300 | 比亚迪 | 判断 |
|---|---|---|---|---|
| 04-27 | 0.85（转上） | 3895 | 235.0 | **Industry Recovery**（超跌反弹/复苏起点，非主题） |
| 05-13 | 0.998 | 3989 | 270.1 | 仍为 Industry Recovery（无政策催化、无主题确认） |
| **05-23** | 1.047 | 4054 | 295.2 | **Theme Confirmation Candidate**（国常会600亿购税，AUTO连日走强） |
| 05-24 | 1.037 | 3959 | 281.0 | 政策日波动（现货回踩） |
| 05-25 | 1.073 | 3983 | 287.2 | 政策后加速 |
| 05-31 | 1.069 | 4092 | 295.9 | 财政部/税务总局细则公告（与05-23为同一事件簇的两个步骤） |
| 06-01 | 1.099 | 4083 | 300.0 | 细则落地买盘（+2.8% AUTO） |

- **Theme Start Candidate = 2022-05-23**（国常会购置税 600 亿，首个明确 Point-in-Time 政策催化）。
- **05-23 ≠ 05-31**：05-23 是国常会"计划减征 600 亿"的方向性宣布；05-31 是财政部/税务总局正式细则公告。两者为**同一事件簇的两个步骤**，05-23 定方向、05-31 给操作细节，共同构成 Theme Confirmation。
- **04-27 不是 Theme Start**：它只是行业超跌反弹 + 复苏起点（Setup）；05-13 前无任何可确认的主题催化。

## 3. Peak（Peak Cluster）

| 标的 | 峰值日 | 峰值(收盘) | 相对04-27 |
|---|---|---|---|
| 比亚迪 | 06-23 | 353.5 | +51% |
| 长安 | 06-23~24 | 22.35 | ~+137% |
| 汽车行业代理(AUTO) | 06-28 | 1.312 | +56%（相对04-26低点） |

- **peak_cluster = 06-23 ~ 06-28**，不强行取单日。
- **龙头(比亚迪/长安)峰值 06-23/24；行业代理峰值 06-28**——两者分列记录。

## 4. End（End Candidate / decline_cluster）

- **行业代理最后一个有效"高点"是 08-01（1.298）**，但：①低于 06-28 主峰（1.312），非新高；②**比亚迪 08-01 仅 330.5，远低于 06-23 峰（353.5），龙头不确认** → **08-01 是"未同步的二高点"，不是板块同步新高**。
- 比亚迪 07-01 后最高仅 07-07（349.38），之后持续走弱至 08-31 288。
- 大盘 HS300 同步走弱（06-30 4485 → 08-31 4078）。
- **最后一次板块同步 = 06-23~06-28 主峰**；其后 7 月 retracement、8 月为 **decline_cluster（08-01→08-31 持续衰减，02 且 APC 不同步）**。
- **End Candidate = 08-01 之后进入衰减（decline_cluster 08月中→08-31）**；**不因数据窗到 8/31 就机械定 End=8/31**。主 Campaign 的"主题主导"实际在 6 月主峰（06-23~28）后即进入后段。

## 5. Main Auto Campaign 判定

- **classification = theme_campaign（政策驱动：购置税 + 新能源）**，持续 05-23→06-28 主升，龙头明确（比亚迪/长安/长城/广汽）。
- 起点（04-27）含行业修复 β；5/23 政策催化后转为明确主题。`theme_campaign`（非 industry_trend，因有清晰政策题材 + 龙头 + 一段时间一致上行）。

## 6. 中通客车（保持独立）

- **classification = event_driven**（个体/短题材），**不作为 Main Auto Theme Leader**。
- 时间线（raw）：5/13 起涨 → **5/31 高潮（+281%）→ 6月停牌/监管核查（数据缺失）→ 7/18 峰值 25.43 → 8/31 16.34**。
- 独立核算，**不并入 Main Auto Campaign 主题强度**。其"核酸检测车"题材与汽车行业政策/新能源主线不同源。

## 7. Point-in-Time

- **04-27 当时知道**：全市场超跌反弹 + 复工复产预期；无确认主题（不能凭比亚迪"后来破万亿"倒推）。
- **05-13 当时知道**：行业修复延续、汽车需求/政策预期升温；但**无单一政策催化** → 主题仍 unconfirmed。
- **05-23 当时知道**：国常会宣布阶段性减征购置税 600 亿（当时公开）→ 主题催化可确认。
- **05-31 当时知道**：财政部/税务总局正式细则公告（当时公开）→ 更强形式确认。
- 全部用当时信息；未用事后资料解释早期日期。

## 8. Window Drift（2022 复述）

- 实际启动 04-27（Setup）/ Theme Start 05-23，nominal 窗口 06-01。
- **launch_lead_time_from_nominal_window**：以 04-27 计 **23 交易日**；以 Theme Start 05-23 计 **6 交易日**（05-23→06-01）。
- → 原始"6—8月汽车"窗口仍**晚于实际启动**（Theme 在 5 月已启动，主峰已在 6 月完成）。

## 9. Uncertainty

1. 行业代理（516110）仅为 2022 代理；`AUTO_SW`(801880) 仍 unavailable。
2. 中通客车停牌期（6月）数据缺失，其短题材枝节待厂方口径二次核对。
3. Theme Start（05-23 vs 06-01）、Peak cluster、End candidate 均为 market-data observation，**verified 一律 NULL**，待人工 Review。
4. 未做 breadth / 未做统计（本阶段禁止）。
5. 未按事后涨幅扩充股票池（纪律）。

---

*数据核验：`python scripts/fetch_market_2022.py`；本文件为 research-level，不改正式 schema/数据。*