# Pilot 1-C0 最终报告：Evidence / Event / Campaign Temporal Integrity

> 目标：修复研究库中已出现的“时间因果”和“事后证据”语义问题，建立时间一致性校验。
> 本轮**未**新增 2021–2025 Campaign，**未**接行情数据、未下载日线、未改 Rule、未做统计/回测、未修改 Cycle / Cycle/data/verified/，**未**改动任何 Campaign 日期与 annual_status。
> 配套方法学：`research/methodology/point_in_time.md`、`research/methodology/campaign_date_quality.md`。

---

## 1. 时间因果错误修复

确认并修复的唯一违规项：

- **C-2024-V2X（6/11 ~ 6/25）**：`EV-2024-02`（五部门公布 20 城试点，2024-07-03）此前被标 `catalyst`，而 7/3 > 6/25 end，违反“event.date > campaign.end_date 时 role 不得为 trigger/catalyst”。
  - 处置（方案 A）：因研究证据表明车路云是 6—7 月的更长主题，将其角色改为 **`follow_up`**（后续/延续证据），不再充当 6/25 前窗口的 catalyst。
  - 对应证据 `E-2024-01`（7/3）标 `temporal_relation = subsequent`。
  - 未采用方案 B（扩大 Campaign）：无充分新证据支持重划边界，遵循“不要为修测试而机械改日期”。

其余全部 campaign_events 经逐条检查，trigger/catalyst 日期均在各自 Campaign window 内或之前，无异常。

## 2. 新增 temporal_relation

- `evidences.temporal_relation` 新列，枚举：`contemporaneous / prior / subsequent / retrospective / unknown`。
- Schema 增加 CHECK + 枚举常量（`db.TEMPORAL_RELATION`）+ `db.migrate()` 幂等 `ALTER TABLE`（老库可升级）。
- 自动补全（`seed.py` 末）：对仍为空的证据，按“相对其绑定 Campaign 的日期”——`prior`(早于 start) / `contemporaneous`(窗口内) / `subsequent`(晚于 end)；未绑定 Campaign 或跨多 Campaign 的保守置 `unknown`。
- 结果：46 条证据全部打标——contemporaneous 31 / prior 1 / subsequent 4 / retrospective 3 / unknown 7（null=0）。

## 3. Retrospective / Point-in-Time 的区别

- **Retrospective Research**：允许后续资料用于解释结果、判断最终结束、复盘、识别反例。
- **Point-in-Time Research**：只能使用当时已公开信息；“事后知道 ≠ 当时知道”。
- 落到字段：`retrospective`（hindsight，更晚资料回顾）+ `subsequent`（Campaign 后用于结果/退潮/反证）**不得**被当作 Campaign 进行中的“当时催化”；只有 `contemporaneous` / `prior` 可支持启动/主升。
- 详见 `point_in_time.md`。

## 4. 2024 V2X 7/3 事件处理结果

- Event 角色：`catalyst → follow_up`（见第 1 节）。
- 证据 `E-2024-01`：`temporal_relation = subsequent`。
- Campaign 日期 `6/11 ~ 6/25`：**未改动**。

## 5. 2025 FSD 后续证据处理结果

- `E-2025-04`（2025 年 FSD 未正式落地、2026-05-21 才宣布监督版入华）：标 `temporal_relation = retrospective`（据内容与来源均为事后回顾性质）。
- **保留该证据**，仅用于 retrospective review，**不得**作为 2025-06-22 的 point-in-time signal。

## 6. 2023 L3 文件处理结果

- `E-2023-06`（L3 准入文件成文 2023-11-17，作 contradicting）：标 `temporal_relation = subsequent`。
- 允许作为反证（证明夏季行情系“政策预期”驱动），但**不会被系统误当作夏季同期的逆证**。

## 7. Campaign 日期是否修改

**本轮没有修改任何 Campaign 日期。**

- `campaigns.start_date/end_date/peak_date` 原样保留（C-2021-NEV 09-30、C-2022-POLICY 08-31、C-2025-ROBOTAXI 08-31 等宽窗口边界均未动）。
- 已明确（`campaign_date_quality.md`）：当前日期为 **research candidate dates**，非最终 verified facts；最终事实由 `campaign_date_observations.verified_date` 在 C2 用日线二次核验。
- 2024 Robotaxi 的 8/5、8/6、8/15、8/21 等后续活跃/退潮叙事，本轮**未**扩 Campaign、**未**新增派生日期；其 `subsequent` 语义由“晚于 end 自动标 subsequent”覆盖，具体波次留 C2 用真实日线收敛（当前 DB 中 8/5–8/21 无独立 Evidence 行，遵循“本轮非新增历史数据”）。

## 8. 测试结果

`validate_db.py` 新增（§11 目标）全部通过，**结果 PASS（0 FAIL，0 WARNING）**：

| §11 目标 | 检查 | 结果 |
|---|---|---|
| 1 | Event→Campaign 时间一致性（trigger/catalyst 不晚于 end） | PASS（EV-2024-02 已改 follow_up 后通过） |
| 2 | Evidence temporal relation 存在且合法 | PASS（null=0） |
| 3 | 事后证据不得伪装 contemporaneous | PASS（无 mislabel 告警） |
| 4 | 7/3 V2X 事件不再作 6/25 结束 Campaign 的 catalyst | PASS（role=follow_up） |
| 5 | 2025 2026-FSD 证据标 retrospective/subsequent | PASS（E-2025-04=retrospective） |
| 6 | Campaign 日期保持不变（熔断：annual_status 不变+candidate 一致） | PASS（8 campaigns，日期未动） |
| 7 | 2018–2025 annual_status 不变 | PASS（熔断检查通过） |

另：`export.py`（8 candidates，evidence 隔离 PASS）、`gen_annual.py 2018-2025`（无回归）、`gen_summary.py`（8 行汇总）全部正常；数据库可正常初始化/迁移。

## 9. 当前是否 READY FOR PILOT 1-C1

**READY FOR MARKET DATA VALIDATION**

- 时间语义已就绪：candidate/verified 分层、temporal_relation 全量打标、计划行核验表（Pilot 1-C1 已建）就位。
- 往年定稿（Campaign 日期、annual_status）熔断保护已生效，后续统计不会意外改动研究候选。
- 下一步（Pilot 1-C2）即可用真实日线对 2020–2025 Campaign 日期做收敛核验。

---

*本报告与 `point_in_time.md` / `campaign_date_quality.md` 配套；数据可经 `exports/cycle_verified_candidates.json` 与 SQLite 复查。*