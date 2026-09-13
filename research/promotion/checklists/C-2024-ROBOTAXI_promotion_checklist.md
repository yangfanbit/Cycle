# Promotion Checklist: C-2024-ROBOTAXI

> 2024 Robotaxi Campaign 晋级检查清单。
> 状态：READY_FOR_HUMAN_REVIEW
> 日期：2026-09-13

---

## 晋级检查项

- [x] Campaign 判定成立（主题可识别 + 持续性 + 市场关注 + 可解释启动/结束，非 Observation）
- [ ] Start 最终确认（研究候选值 2024-07-08，待人工最终判断）
- [ ] End 最终确认（研究候选值 2024-07-31，待人工最终判断）
- [ ] Peak 最终确认（研究候选值 2024-07-29，待人工最终判断）
- [x] Evidence >= 2（4 条：E-2024-05 ~ E-2024-08，均经 campaign_evidences 显式绑定）
- [x] independent_group >= 2（4 组：orig_robotaxi_momentum / orig_robotaxi_leader / orig_robotaxi_retreat / orig_robotaxi_thirdwave）
- [x] Source Tier 合法（Tier 1–4 范围内，详见 evidences.source_id）
- [x] Point-in-Time 边界明确（PIT 与 Retrospective 未混淆）
- [x] 无严重 temporal conflict（start <= peak <= end，无 look-ahead）
- [ ] reviewer 已填写（当前 pending）
- [ ] reviewed_at 已填写（当前 null）
- [x] Cycle mapping 完整（见 cycle_mapping_v1.md，13 个核心字段全部直接映射）
- [x] Phase mapping 完整（startup / main_rise / decline → 1:1 可映射）
- [x] Theme mapping 完整（main: TH-ROBOTAXI；related: TH-AUTO）
- [x] Security mapping 完整（leader: DADONGTRAFFIC；second_leader: JINJIANGONLINE / JINLONG；representative: JIANGLING）

---

## 研究备注

- 07-08 萝卜快跑武汉跑出圈（启动）；07-29 峰值；07-31 结束。
- 09-05~06 为 Weak Secondary Campaign Candidate（RC-2024-SECONDARY），保持研究候选，不进入本 Campaign。
- cross_year = false（2024-07-08 ~ 2024-07-31 同年）。
- **待人工裁决（日期口径）**：冻结 DB 行记录 peak=2024-07-29 / end=2024-07-31；EW 等权指数分析（calibrate_robotaxi.py）显示 raw 峰值 2024-08-05、首次回落 2024-08-06，行情观察延续至 08-23。两套口径留待人工 Review 最终判断。

## 当前阻碍（Blocker）

1. reviewer = "pending"
2. reviewed_at = null

解除阻碍后，promotion_status 可由 READY_FOR_HUMAN_REVIEW 升级为 READY_FOR_PROMOTION。
