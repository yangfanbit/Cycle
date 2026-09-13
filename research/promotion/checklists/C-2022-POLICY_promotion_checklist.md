# Promotion Checklist: C-2022-POLICY

> 2022 Auto Policy Campaign 晋级检查清单。
> 状态：READY_FOR_HUMAN_REVIEW
> 日期：2026-09-13

---

## 晋级检查项

- [x] Campaign 判定成立（主题可识别 + 持续性 + 市场关注 + 可解释启动/结束，非 Observation）
- [ ] Start 最终确认（研究候选值 2022-04-27，待人工最终判断）
- [ ] End 最终确认（研究候选值 2022-08-31，待人工最终判断）
- [ ] Peak 最终确认（研究候选值 2022-06-10，待人工最终判断）
- [x] Evidence >= 2（5 条：E-2022-01 ~ E-2022-05，均经 campaign_evidences 显式绑定）
- [x] independent_group >= 2（4 组：orig_policy_tax_catalyst / orig_nev_stock_price / orig_sector_momentum / orig_counter_single_stock）
- [x] Source Tier 合法（Tier 1–4 范围内，详见 evidences.source_id）
- [x] Point-in-Time 边界明确（PIT 与 Retrospective 未混淆）
- [x] 无严重 temporal conflict（start <= peak <= end，无 look-ahead）
- [ ] reviewer 已填写（当前 pending）
- [ ] reviewed_at 已填写（当前 null）
- [x] Cycle mapping 完整（见 cycle_mapping_v1.md，13 个核心字段全部直接映射）
- [x] Phase mapping 完整（startup / main_rise / secondary_rally / decline → 1:1 可映射）
- [x] Theme mapping 完整（main: TH-CAR-CONSUMPTION；related: TH-AUTO / TH-NEV）
- [x] Security mapping 完整（leader: BIDI / GWM；second_leader: CHANGAN / GAC；representative: ANKA）

---

## 研究备注

- 04-27 = 行业修复 / Setup；05-23 = 国常会购置税政策催化（Theme Formation / Campaign Start Candidate）；06-10 峰值；08-31 结束。
- 中通客车（核酸检测车概念）为 Observation，不计入 Campaign 主线。
- cross_year = false（2022-04-27 ~ 2022-08-31 同年）。

## 当前阻碍（Blocker）

1. reviewer = "pending"
2. reviewed_at = null

解除阻碍后，promotion_status 可由 READY_FOR_HUMAN_REVIEW 升级为 READY_FOR_PROMOTION。
