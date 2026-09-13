# Campaign 日期质量说明（Pilot 1-C0）

> 明确：当前 `campaigns.start_date / end_date / peak_date` 全部是 **research candidate dates（研究候选日期）**，**不是**最终 verified facts。
> 最终事实将由 `campaign_date_observations`（Pilot 1-C1 已建表）在接入真实日线（Pilot 1-C2）后二次核验。

## 1. 日期字段当前定位

- `campaigns.*_date` = 原始研究（媒体/证据）给出的候选，**本轮及此前均未改动**。
- `campaign_date_observations.candidate_date` = 其原样快照（保留原始）。
- `campaign_date_observations.verified_date` = **核验后**日期，目前为 NULL，待 C2 填写。

## 2. “暂定研究边界 / 待日线核验”的日期

以下 `end_date` 属**宽窗口/暂定边界**，不代表已确认的真实结束，C2 需用日线收缩：

| Campaign | 当前 end_date | 性质 | 说明 |
|---|---|---|---|
| C-2021-NEV | 2021-09-30 | 暂定边界 | 主升在 8/6（比亚迪新高），其后高位衰减；9月末结束为宽界定，待日线核验 |
| C-2022-POLICY | 2022-08-31 | 暂定边界 | 7月后分化/回调，8月政策边际减弱；精确结束待核验 |
| C-2025-ROBOTAXI | 2025-08-31 | 暂定边界 | 8月随大盘牛β放量、9/12月另有两轮催化超出夏季窗口；需日线划分波次 |

> 这些日期**本轮不改**；其确切结束应由 C2 的真实日线 + `verified_date` 收敛后，再决定是否更新 Campaign Fact。

## 3. annual_status 性质

- 2018 no_clear / 2019 weak / 2020 strong / 2021 strong / 2022 strong / 2023 medium / 2024 medium / 2025 medium，是 **qualitative research assessment（定性研究评估）**，**不是统计评分**。
- 未来如需要，可拆分为更细维度（`industry_trend_score` / `theme_activity_score` / `campaign_strength`），本轮不实现。

## 4. 校验
`validate_db.py` 第 24 项熔断：2018–2025 的 `annual_status` 若被改动将 FAIL，保证本轮不符动机改往年定稿。