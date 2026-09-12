# {year} 汽车（Base Pattern: 汽车）

> Rule: `rule_auto_summer` · Annual Review 状态：`{annual_status}`
> 数据来源：见本页 Evidence 引用与 SQLite `sources`/`evidences` 表。
> 说明：媒体描述 ≠ 市场事实；板块上涨 ≠ Campaign。所有 Campaign 判定须满足主题可识别、有持续性、可解释启动/结束、有证据。

## 年度结论
（一段话总结：今年 6—8 月汽车相关机会是否出现？是主题还是行业趋势？窗口是否漂移？有无反例？）

## Campaign
### Campaign {id}
- 时间：{start_date} ~ {end_date}（峰值 {peak_date}）
- 窗口漂移：相对 6/1 {drift_jun01} 天；相对 7/1 {drift_jul01} 天；相对 8/1 {drift_aug01} 天
- 主题（Annual Theme）：{main_theme}（classification: {classification}）
- 启动（start_date_basis）：...
- 结束（end_date_basis）：...
- 催化（事件）：...
- 代表股（leader / second_leader）：...
- 结果：{result}（strength: {strength}）
- 描述：...
（若同一年有多个独立 Campaign，分列 A / B / C；无法判断是否同一轮的用 representative 列出并 `classification=unclear`）

## 行业趋势
（若只是行业整体上涨，无明确主题，归入此处，classification=industry_trend，不作为 theme_campaign）

## 失败/反例
（明确记录：无主题 / 窗口提前或延后 / 无明显行情 / 但板块上涨却无 Campaign）

## Wave / Phase
（仅当证据充分时记录：启动→退潮→二次催化→再加速→最终退潮。否则注明"暂不记录"）

## Evidence
- 每条：来源 title（tier）/ URL / 日期 / 角色(supporting|contradicting|context) / confidence / 摘要与为何相关