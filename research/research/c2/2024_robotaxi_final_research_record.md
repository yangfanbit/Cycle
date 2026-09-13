# 2024 Robotaxi — Final Research Record（研究封存）

> 本文件为 **research-level 封存记录**，明确编号与判断，供后续跨年比较引用。
> **不改** 正式 `campaigns` / `annual_reviews` / `rule_auto_summer` / `Cycle` / `Cycle/data/verified/`，**不创建** 正式 theme_cycles schema。

---

## 1. Theme Cycle

- **Theme Cycle：2024 Smart Driving / Robotaxi（智能驾驶 / 无人驾驶，2024）**
- 一个 Theme Cycle 内含多个主/次级 Campaign（本记录以 research-level 标注，不建正式表）。

## 2. Main Campaign

| 项 | 值 |
|---|---|
| Main Campaign | **2024-07-08 → 2024-08-23** |
| Start（起势） | 2024-07-08（首个 Index 大日 / Retrospective Confirmation 07-09；Broad Theme Confirmation（Point-in-Time 可辩护）07-10） |
| Main Peak | **2024-08-05**（Historical Leader EW Index，raw close） |
| First Decline | **2024-08-06** |
| Main End / Major Breakpoint | **2024-08-23** |

## 3. Secondary Campaign

| 项 | 值 |
|---|---|
| Secondary Campaign Candidate | **2024-09-05 → 2024-09-06** |
| classification | **secondary_campaign_same_theme_cycle** |
| strength | **weak** |
| 原因 | 新催化（特斯拉 FSD 入华预期 + Robotaxi 10月 + 萝卜快跑扩容）；仍为无人驾驶/Robotaxi 主题；3/5 核心同步（大众/锦江/金龙），星网/天迈滞后；行业（AutoETF）/大盘（HS300）无明显共振；仅持续 2 日；09-09/10 快速回落回吐 |

- **未升级为 new_campaign**。
- **09-05/09-06 不写入正式 `campaigns` 表**；仅在本 research 记录。

## 4. 数据层级（明确，避免滥用）

- **Historical Leader Set** ＝ 行情结束后确认的 5 只核心样本（大众/锦江/金龙/星网/天迈）。用途：复盘。
- **Point-in-Time Basket** ＝ 按历史日期切片（07-08 unavailable / 07-10 {4} / 07-15 {5}）得到的、当时有公开证据可识别的股票。用途：模拟实时研究。
- **Historical Leader Equal-Weight Index** ＝ 事后研究工具（5 股等权归一，base 07-08=100）。
  - **不是** Robotaxi 板块指数；
  - **不是** 普通投资者当时可获得的实时收益。
- 两者与“板块平均收益 / 投资者可得收益”严格区分。

## 5. 08-23 语义

- **08-23 = Main Campaign End / Major Breakpoint。**
- **不是 Final Theme Cycle End**：主题在 09-05 出现同主题次级再启动，主题 Cycle 延续进入 9 月次级段。

## 6. 09-05/09-06 语义

- **Secondary Campaign Candidate：09-05 → 09-06，`secondary_campaign_same_theme_cycle`，weak**。
- 理由见 §3；不改规则为 new_campaign，不写入正式 campaigns。

## 7. 未修改项（确认）

- `campaigns.C-2024-ROBOTAXI.start_date/peak_date/end_date` 不变（07-08 / 07-29 / 07-31，仍为 research candidate）。
- `annual_reviews` 2024 = medium，不变。
- 未写 `verified`，未建 theme_cycles schema。

## 8. 参考文件

- `2024_robotaxi_market_validation.md`（C1.1 校正，计算方法）
- `2024_robotaxi_point_in_time.md`（C1.2，PIT 与边界）
- `2024_robotaxi_continuity_review.md`（C1.2.1，8/23→9/10 连续性）
- `point_in_time_leaders.csv`、`_calib_raw.json`、原始日线（`data/market/`）

*本记录为研究封存，结论经人工 Review 后再决定是否更新正式 `HistoricalCampaign`。*