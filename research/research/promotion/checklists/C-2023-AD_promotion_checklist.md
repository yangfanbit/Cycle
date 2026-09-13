# Promotion Checklist: C-2023-AD

> 2023 Smart Driving Campaign 晋级检查清单。
> 状态：READY_FOR_HUMAN_REVIEW
> 日期：2026-09-13

---

## 晋级检查项

- [x] Campaign 判定成立（主题可识别 + 持续性 + 市场关注 + 可解释启动/结束，非 Observation）
- [ ] Start 最终确认（研究候选值 2023-06-12，待人工最终判断）
- [ ] End 最终确认（研究候选值 2023-07-19，待人工最终判断）
- [ ] Peak 最终确认（研究候选值 2023-07-11，待人工最终判断）
- [x] Evidence >= 2（7 条：E-2023-01 ~ E-2023-07，均经 campaign_evidences 显式绑定）
- [x] independent_group >= 2（7 组：orig_l3_policy_expectation / orig_sales_trend / orig_sector_momentum / orig_ad_momentum / orig_ad_stock_price / orig_structure_pulse / orig_policy_schedule）
- [x] Source Tier 合法（含 Tier 1 regulator 来源）
- [x] Point-in-Time 边界明确（PIT 与 Retrospective 未混淆）
- [x] 无严重 temporal conflict（start <= peak <= end，无 look-ahead）
- [ ] reviewer 已填写（当前 pending）
- [ ] reviewed_at 已填写（当前 null）
- [x] Cycle mapping 规则已备（见 cycle_mapping_v1.md v1.1 / promotion_mapping_matrix_v1.md；TRANSFORM 项：season_id 格式、cross_year 计算、source_id 派生、classification 留 package）
- [x] Phase 处理已明确（research-only：NOT PERSISTED IN CURRENT CYCLE，非晋级必要条件；startup/main_rise/decline 保留在 Research）
- [x] Theme mapping 完整（main: TH-AD；related: TH-AUTO）
- [x] Security mapping 完整（leader: ZHEJIANGSHISHI；second_leader: DESAYSV / WANAN；representative: ZTELEVISION）

---

## 研究备注

- 06-12 启动；07-11 峰值；07-19 结束。
- Huawei Auto（RC-2023-HUAWEI）为独立 Research Candidate，不混入本 Campaign。
- cross_year = false（2023-06-12 ~ 2023-07-19 同年）。

## 当前阻碍（Blocker）

1. reviewer = "pending"
2. reviewed_at = null

解除阻碍后，promotion_status 可由 READY_FOR_HUMAN_REVIEW 升级为 READY_FOR_PROMOTION。
