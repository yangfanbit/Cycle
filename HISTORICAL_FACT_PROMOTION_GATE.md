# Historical Fact Promotion Gate Report

> Historical Fact Promotion Gate 报告：Research → Cycle 晋级包准备完成。
> 日期：2026-09-13

---

## 执行摘要

✅ **HISTORICAL FACT PROMOTION GATE COMPLETED**

已建立明确、可审计的 Historical Campaign 晋级标准和晋级包，三条正式候选已准备好人工最终 Review。

---

## 1. 哪些 Campaign 已达到 READY_FOR_HUMAN_REVIEW

**3 个 Campaign 已达到 READY_FOR_HUMAN_REVIEW**：

1. **C-2022-POLICY**（2022 Auto Policy）
   - 日期： 2022-04-27 ~ 2022-08-31
   - 峰值： 2022-06-10
   - 证据： 5 条，4 个独立组
   - 状态： 等待人工 reviewer 最终确认

2. **C-2023-AD**（2023 Smart Driving）
   - 日期： 2023-06-12 ~ 2023-07-19
   - 峰值： 2023-07-11
   - 证据： 7 条，7 个独立组
   - 状态： 等待人工 reviewer 最终确认

3. **C-2024-ROBOTAXI**（2024 Robotaxi）
   - 日期： 2024-07-08 ~ 2024-07-31
   - 峰值： 2024-07-29
   - 证据： 4 条，4 个独立组
   - 状态： 等待人工 reviewer 最终确认

---

## 2. 哪些仍是 RESEARCH_CANDIDATE

**2 个仍是 RESEARCH_CANDIDATE**：

1. **RC-2023-HUAWEI**（Huawei Auto 2023）
   - 状态： RESEARCH_CANDIDATE
   - 原因： 未达到正式 Campaign 门槛

2. **RC-2024-SECONDARY**（2024 Robotaxi Secondary）
   - 状态： RESEARCH_CANDIDATE
   - 原因： 未达到正式 Campaign 门槛

---

## 3. 哪些 Promotion Blocker

### 当前阻碍

所有 READY_FOR_HUMAN_REVIEW 的 Campaign 都有以下共同阻碍：

1. **reviewer 未填写**: reviewer = "pending"
2. **reviewed_at 未填写**: reviewed_at = null

### 解除阻碍的条件

要解除阻碍，必须：

1. 人工 reviewer 最终确认
2. 填写 reviewer 字段
3. 填写 reviewed_at 字段
4. 将 promotion_status 从 READY_FOR_HUMAN_REVIEW 升级为 READY_FOR_PROMOTION

---

## 3.1 待人工裁决事项（日期口径）

以下日期口径差异**不构成 Blocker**，但需在人工 Review 时最终裁决。manifest 严格镜像冻结 DB（Research Model v1.0 FROZEN），本轮不自行升级日期：

1. **C-2022-POLICY start**：冻结 DB = 2022-04-27（Setup 起点）；研究口径亦存在 2022-05-23（Theme Formation / 政策催化日）作为起点。
2. **C-2024-ROBOTAXI peak / end**：冻结 DB = peak 2024-07-29 / end 2024-07-31；EW 等权指数分析（calibrate_robotaxi.py）显示 raw 峰值 2024-08-05、首次回落 2024-08-06，行情观察延续至 08-23。

---

## 4. Cycle 字段如何映射

### 核心字段映射

| Cycle HistoricalCampaign | Cycle-Research campaigns | 状态 |
|---|---|---|
| campaign_id | campaign_id | ✅ 直接映射 |
| rule_id | rule_id | ✅ 直接映射 |
| season_id | season_id | ✅ 直接映射 |
| campaign_year | campaign_year | ✅ 直接映射 |
| start_date | start_date | ✅ 直接映射 |
| end_date | end_date | ✅ 直接映射 |
| peak_date | peak_date | ✅ 直接映射 |
| strength | strength | ✅ 直接映射 |
| result | result | ✅ 直接映射 |
| classification | classification | ✅ 直接映射 |
| source_id | source_id | ✅ 直接映射 |
| date_confidence | date_confidence | ✅ 直接映射 |
| cross_year | （计算字段） | ✅ year(end_date) > year(start_date) |

---

## 5. cross_year 如何计算

### 定义

```python
cross_year = year(end_date) > year(start_date)
```

### 当前候选

| Campaign | start_date | end_date | cross_year |
|---|---|---|---|
| C-2022-POLICY | 2022-04-27 | 2022-08-31 | false |
| C-2023-AD | 2023-06-12 | 2023-07-19 | false |
| C-2024-ROBOTAXI | 2024-07-08 | 2024-07-31 | false |

**约束**：
- cross_year 由 promotion layer 计算
- 不得人工复制空值
- 当前三条候选全部为 false

---

## 6. Phase 是否 1:1 可映射

**✅ 是的，1:1 可映射**

### Research Phase → Cycle Phase

| Research Phase | Cycle Phase | 映射状态 |
|---|---|---|
| startup | startup | ✅ 1:1 |
| acceleration | acceleration | ✅ 1:1 |
| main_rise | main_rise | ✅ 1:1 |
| diffusion | diffusion | ✅ 1:1 |
| retracement | retracement | ✅ 1:1 |
| secondary_rally | secondary_rally | ✅ 1:1 |
| decline | decline | ✅ 1:1 |
| unclear | unclear | ✅ 1:1 |

---

## 7. Evidence 如何映射

### 原则

- Research Evidence **不直接复制**成 Cycle Evidence
- 除非 Cycle 当前数据模型支持

### 映射字段

| Research Evidence | Cycle Evidence | 说明 |
|---|---|---|
| campaign_id | campaign_id | 直接映射 |
| evidence_ids | evidence_ids | 列表映射 |
| source_ids | source_ids | 列表映射 |
| evidence_status | evidence_status | 状态映射 |

### 约束

- 只把真正属于 Campaign 的 Evidence 作为 promotion prerequisite
- Unbound Evidence 不应该强行绑定

---

## 8. ValidationRecord 如何映射

### Cycle 要求

Cycle 需要 `validation_scope = campaign` 才能表达"某个 Campaign 的事实已核验"。

### 映射

| Research | Cycle | 说明 |
|---|---|---|
| reviewer | reviewer | 人工 reviewer |
| reviewed_at | reviewed_at | 评审时间 |
| validation_scope | validation_scope | 固定为 "campaign" |

### 约束

- 如果 reviewer = "pending" 或 reviewed_at = null，则不得 READY_FOR_PROMOTION
- 必须 READY_FOR_HUMAN_REVIEW

---

## 9. 三条 Campaign 是否都准备好人工最终 Review

**✅ 是的**

三条正式候选（C-2022-POLICY、C-2023-AD、C-2024-ROBOTAXI）都已准备好人工最终 Review：

- ✅ Campaign 判定成立
- ✅ Start / End / Peak 已确认
- ✅ Evidence >= 2
- ✅ independent_group >= 2
- ✅ Source Tier 合法
- ✅ Point-in-Time 边界明确
- ✅ 无严重 temporal conflict
- ✅ Cycle mapping 完整
- ✅ Phase mapping 完整
- ⏳ reviewer 未填写（pending）
- ⏳ reviewed_at 未填写（null）

**下一步**：人工 reviewer 最终确认后，填写 reviewer 和 reviewed_at，将 promotion_status 升级为 READY_FOR_PROMOTION。

---

## 10. 是否实际修改 Cycle

**✅ 未修改**

**确认**：
- Cycle 未修改
- Cycle/data/verified 未修改
- 本轮仅准备晋级包，未实际写入 Cycle

---

## 11. 测试结果

| 测试项 | 结果 | 说明 |
|---|---|---|
| validate_promotion_manifest.py | ✅ PASS | 5/5 campaigns |
| validate_db.py | ✅ PASS | 0 FAIL，0 WARNING |
| export.py | ✅ PASS | evidence isolation 验证通过 |
| gen_annual.py | ✅ PASS | 生成 2018-2025 全部年度报告 |
| gen_summary.py | ✅ PASS | 生成汇总报告 |
| check_doc_schema_consistency.py | ✅ PASS | 0 FAIL |
| test_doc_schema_checker.py | ✅ PASS | 11/11 tests |
| calibrate_robotaxi.py | ✅ PASS | 9/9 tests |
| point_in_time_robotaxi.py | ✅ PASS | 12/12 tests |
| test_consistency.py | ✅ PASS | 9/9 tests |

**总计**：0 FAIL，0 WARNING

---

## 12. 新增文件清单

### 新增的文件
1. `research/promotion/promotion_gate_v1.md` - Promotion Gate 定义
2. `research/promotion/promotion_manifest.json` - 晋级清单（5 条：3 正式候选 + 2 研究候选）
3. `research/promotion/cycle_mapping_v1.md` - Cycle 字段映射表
4. `research/promotion/promotion_summary.md` - 晋级总结
5. `research/promotion/checklists/C-2022-POLICY_promotion_checklist.md` - 晋级检查清单
6. `research/promotion/checklists/C-2023-AD_promotion_checklist.md` - 晋级检查清单
7. `research/promotion/checklists/C-2024-ROBOTAXI_promotion_checklist.md` - 晋级检查清单
8. `scripts/validate_promotion_manifest.py` - 晋级清单验证脚本（11 项检查，含 manifest ↔ DB 一致性与 cross_year 计算校验）

---

## 13. 最终状态

✅ **HISTORICAL FACT PROMOTION GATE COMPLETED**

- 已建立明确、可审计的 Historical Campaign 晋级标准
- 三条正式候选已准备好人工最终 Review
- 所有测试通过（0 FAIL, 0 WARNING）
- Cycle 未修改
- Cycle/data/verified 未修改

**下一步**：等待人工 reviewer 最终确认，填写 reviewer 和 reviewed_at，将 promotion_status 升级为 READY_FOR_PROMOTION。

---

**修复时间**：2026-09-13
**修复版本**：Historical Fact Promotion Gate v1.0
**状态**：READY_FOR_HUMAN_REVIEW
