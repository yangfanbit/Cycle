# V1.7 Historical Opportunity Map Data Production Report

> 项目：Cycle-Research · 日期：2026-09-13 · 基线 HEAD：`2ff6fad`
> 本轮：为现有 2018–2025 Auto Campaign 补齐 **Phase Windows（lifecycle）+ Drivers**，应用 V1.7 时间精度策略，并准备多题材扩展接口（Rule Candidates）。
> 模型 v1.0 **保持 FROZEN**：未新增 Schema、未改 DB、未改正式 Campaign 日期。

---

## 1. 2018–2025 Auto Campaign 数量

**8 个正式 Campaign** + 2018 反例年度条目（`Y2018-NO-CLEAR`）+ **2 个 Research Candidate**（RC-2023-HUAWEI / RC-2024-SECONDARY）。

## 2. Phase Window 完成度

**8/8 Campaign 完成 lifecycle（Phase Windows）**，共 **49 个 stage 条目**；2/2 Candidate 完成。

| Campaign | lifecycle stages | 覆盖（Early Signal → Main End） |
|---|---|---|
| C-2019-AD | 4 | EARLY_SIGNAL / MAIN_RISE / PEAK / MAIN_END |
| C-2020-NEV | 6 | + RETRACEMENT / SECONDARY |
| C-2021-NEV | 5 | + DECLINING |
| C-2022-POLICY | 9 | 全链路（含 THEME_FORMING / BROAD_CONFIRMATION / SECONDARY / RETRACEMENT / DECLINING） |
| C-2023-AD | 8 | 全链路（含 SECONDARY / DECLINING） |
| C-2024-V2X | 4 | 快涨快退（EARLY / THEME_FORMING / PEAK / MAIN_END） |
| C-2024-ROBOTAXI | 8 | 全链路（含 PEAK Window / FIRST_DECLINE / SECONDARY） |
| C-2025-ROBOTAXI | 5 | 短主升（EARLY / BROAD_CONFIRMATION / MAIN_RISE / PEAK / MAIN_END） |

时间精度分布：`EXACT_DATE`（真实行情/正式事件）+ `DATE_WINDOW`（Peak/主升多指标差异）+ `PHASE_WINDOW`（7月回撤、8月衰减等用户周期阶段）。

## 3. Drivers 完成度

**8/8 Campaign + 2/2 Candidate 完成 `drivers {start, accelerator, turning, ending}`**（共 10 组 × 4 维度）。全部内嵌来源引用（EV-/E-/S- 编号），**无编造因果**；无可靠来源处如实写 `unknown`（RC-2024-SECONDARY 的 accelerator / turning）。

## 4. PROVISIONAL

**8**（含 2018 年度反例条目 + C-2019-AD / C-2020-NEV / C-2021-NEV / C-2022-POLICY / C-2023-AD / C-2024-V2X / C-2025-ROBOTAXI）。

## 5. CONFLICT

**1**（C-2024-ROBOTAXI end_date 07-31 vs 08-23）。按 V1.7 新标准（End 候选改变生命周期）保留。

## 6. VERIFIED

**0**（人工最终 Review 未发生，不阻塞生产；VERIFIED 等待后续集中 Review）。

## 7. 重大 Conflict

仅 **1 处**：`C-2024-ROBOTAXI.end_date`（2024-07-31 DB Candidate vs 2024-08-23 Research Review Candidate）。记录于 `research/batch/conflicts.json` 与 export `campaigns[].conflicts`（candidate_a / candidate_b），decision=pending_human_review。

## 8. 轻微 Date Window（已降级，不阻塞）

按 V1.7 新标准从 CONFLICT 降级为 date_window，用 `lifecycle` 表达：

| Campaign | 字段 | 处理 |
|---|---|---|
| C-2022-POLICY | start 04-27 vs 05-23（15 交易日 ≤20） | 语义分层：EARLY_SIGNAL 04-27（Setup）+ THEME_FORMING 05-23（政策催化）；正式 start_date 保持 04-27 冻结 |
| C-2024-ROBOTAXI | peak 07-29 vs 08-05（5 交易日、相邻月份） | PEAK = **DATE_WINDOW 07-29 ~ 08-05**，不再阻塞 |
| C-2022-POLICY | peak 06-10 vs 06-23/28（cluster） | PEAK = **DATE_WINDOW 06-10 ~ 06-28** |
| C-2023-AD | peak 07-11 vs 07-12~19 | PEAK = **DATE_WINDOW 07-11 ~ 07-19** |

## 9. 第一批 3–5 个 Rule Candidates

见 [rule_candidates_v1.md](research/methodology/rule_candidates_v1.md)：**5 个候选**（当前正式 Rule 仅 `rule_auto_summer`）：

1. `rule_power_summer`（电力/绿电，夏季迎峰度夏）
2. `rule_pharma_year`（医药，医保谈判/集采/创新药出海多窗口）
3. `rule_consumer_holiday`（消费，节假日时间轴）
4. `rule_media_cycle`（传媒/广电，暑期档/版号周期）
5. `rule_textile_export`（纺织服装，换季/出口数据窗口）

**均为 Rule Candidates，不假设有效**；进入正式生产前须通过产品初心四问 + 确认真实历史行情数据源。

## 10. Timeline Export 是否兼容

✅ **兼容**。顶层 11 字段 Contract **未改变**；仅新增 backward-compatible optional 字段：
- `campaigns[].lifecycle`（Phase Windows + 三档时间精度 EXACT_DATE / DATE_WINDOW / PHASE_WINDOW）
- `campaigns[].drivers`（start / accelerator / turning / ending）
- `research_candidates[].lifecycle` / `research_candidates[].drivers`

`validate_timeline_export.py` 已同步（字段白名单 + stage/precision 枚举 + 日期格式校验），**PASS（0 FAIL）**。契约文档 `timeline_export_contract_v1.md` 已更新（§0 时间精度 + §5/6 示例 + §13 向后兼容）。Cycle 现有 Adapter 不受影响。

## 11. 是否偏离项目初心

✅ **未偏离**。经产品初心四问：
1. 帮助回答"未来类似时间点历史上通常发生什么"？→ **是**（Phase Windows + Drivers 直接回答"何时启动/主升/转折/结束、什么驱动"）
2. 提高历史可比性？→ **是**（统一 lifecycle 阶段词汇 + 三档时间精度）
3. 识别提前信号？→ **是**（EARLY_SIGNAL / THEME_FORMING 阶段保留）
4. 只是工程复杂化？→ **否**（未加 Schema、未加审计字段、未加内部文档堆砌；Rule Candidates 仅名单不生产）

**未修改**：`database/cycle_research.db`（zero diff）、`schema.sql`（zero diff）、正式 Campaign 日期、Evidence、Market Data、Research Model。未新增历史研究、未做统计/预测。

## 12. 下一阶段建议

1. **集中 Review 窗口**：启动对 3 条 READY_FOR_HUMAN_REVIEW 正式候选（C-2022-POLICY / C-2023-AD / C-2024-ROBOTAXI）的人工最终 Review，产出 Verified Date（先裁决 C-2024-ROBOTAXI end 唯一重大 Conflict）。
2. **多题材 Pilot**：从 Rule Candidates 中挑 1–2 个（建议 `rule_power_summer` + `rule_consumer_holiday`）做轻量 2018–2025 时间轴骨架，先验证数据源可得性再全面生产。
3. **Cycle 同步**：下一轮由 Cycle 侧按契约 v1.0 同步 `timeline_export_v1.json`（含 lifecycle/drivers 可选字段）。

---

## 验证结果

```
validate_timeline_export.py    → PASS（含 lifecycle/drivers 白名单与枚举校验，0 FAIL）
validate_batch_research.py     → PASS（0 FAIL；状态分布 PROVISIONAL 8 / CONFLICT 1）
validate_db.py                 → PASS（0 FAIL, 0 WARNING）
```

---

# READY FOR MULTI-THEME TIMELINE

2018–2025 Auto 已具备：Campaign + Research Signal + Candidate + **Phase Windows（三档时间精度）** + **Drivers（来源可追溯）** + Evidence + 行情，Export 向后兼容。多题材时间轴扩展接口（Rule Candidates v1）已就绪。
