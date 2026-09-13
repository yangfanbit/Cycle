# Promotion Summary

> Historical Fact Promotion Summary: Research Campaign 晋级状态总结。
> 日期：2026-09-13

---

## 1. 晋级状态总览

| Research Campaign | Status | Target Cycle ID | Date | Evidence | Mapping | Blocker |
|---|---|---|---|---|---|---|
| **C-2022-POLICY** | READY_FOR_HUMAN_REVIEW | null | 2022-04-27 ~ 2022-08-31 | 5 evidences, 4 groups | ✅ 完整 | reviewer 未填写 |
| **C-2023-AD** | READY_FOR_HUMAN_REVIEW | null | 2023-06-12 ~ 2023-07-19 | 7 evidences, 7 groups | ✅ 完整 | reviewer 未填写 |
| **C-2024-ROBOTAXI** | READY_FOR_HUMAN_REVIEW | null | 2024-07-08 ~ 2024-07-31 | 4 evidences, 4 groups | ✅ 完整 | reviewer 未填写 |
| **RC-2023-HUAWEI** | RESEARCH_CANDIDATE | null | 2023-09-12 ~ (ongoing) | 0 evidences | ⚠️ 研究候选 | 未达到正式 Campaign 门槛 |
| **RC-2024-SECONDARY** | RESEARCH_CANDIDATE | null | 2024-09-05 ~ 2024-09-06 | 0 evidences | ⚠️ 研究候选 | 未达到正式 Campaign 门槛 |

---

## 2. 详细说明

### 2.1 READY_FOR_HUMAN_REVIEW（3 个）

#### C-2022-POLICY
- **状态**: READY_FOR_HUMAN_REVIEW
- **日期**: 2022-04-27 ~ 2022-08-31
- **峰值**: 2022-06-10
- **证据**: 5 条，4 个独立组
- **映射**: 完整
- **阻碍**: reviewer 未填写（pending）

**说明**: 2022 Auto Policy Campaign，04-27 行业修复/Setup，05-23 国常会购置税政策启动，06-10 峰值，08-31 结束。中通客车为 Observation（核酸检测车概念），不计入 Campaign 主线。

**待人工裁决（日期口径）**：冻结 DB 行记录 start=2022-04-27（Setup 起点）；研究中亦存在 05-23（Theme Formation / Campaign Start Candidate）作为起点的口径。差异留待人工 Review 最终判断，manifest 严格镜像冻结 DB，不自行升级日期。

#### C-2023-AD
- **状态**: READY_FOR_HUMAN_REVIEW
- **日期**: 2023-06-12 ~ 2023-07-19
- **峰值**: 2023-07-11
- **证据**: 7 条，7 个独立组
- **映射**: 完整
- **阻碍**: reviewer 未填写（pending）

**说明**: 2023 Smart Driving Campaign，06-12 启动，07-11 峰值，07-19 结束。Huawei Auto 为 Research Candidate (RC-2023-HUAWEI)，不进入正式 Campaign。

#### C-2024-ROBOTAXI
- **状态**: READY_FOR_HUMAN_REVIEW
- **日期**: 2024-07-08 ~ 2024-07-31
- **峰值**: 2024-07-29
- **证据**: 4 条，4 个独立组
- **映射**: 完整
- **阻碍**: reviewer 未填写（pending）

**说明**: 2024 Robotaxi Campaign，07-08 萝卜快跑武汉跑出圈，07-29 峰值，07-31 结束。09-05~06 为 Weak Secondary Campaign Candidate，不进入正式 Campaign。

**待人工裁决（日期口径）**：冻结 DB 行记录 peak=2024-07-29 / end=2024-07-31；而 EW 等权指数分析（calibrate_robotaxi.py）显示 raw 峰值 2024-08-05、首次回落 2024-08-06，行情观察延续至 08-23。两套口径的差异留待人工 Review 最终判断，manifest 严格镜像冻结 DB，不自行升级日期。

---

### 2.2 RESEARCH_CANDIDATE（2 个）

#### RC-2023-HUAWEI
- **状态**: RESEARCH_CANDIDATE
- **日期**: 2023-09-12 ~ (ongoing)
- **证据**: 0 条
- **映射**: 研究候选
- **阻碍**: 未达到正式 Campaign 门槛

**说明**: Huawei Auto 2023 Research Candidate，08-29 Early Signal Candidate，09-04 Theme Formation，09-12 Campaign Start Candidate。当前仍为研究候选，未达到正式 Campaign 门槛。

#### RC-2024-SECONDARY
- **状态**: RESEARCH_CANDIDATE
- **日期**: 2024-09-05 ~ 2024-09-06
- **证据**: 0 条
- **映射**: 研究候选
- **阻碍**: 未达到正式 Campaign 门槛

**说明**: 2024 Robotaxi Secondary Campaign Candidate，09-05~06 Weak Secondary。当前仍为研究候选，未达到正式 Campaign 门槛。

---

## 3. Promotion Blocker

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

## 4. Cycle 字段映射

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

## 5. cross_year 计算

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

## 6. Phase 映射

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

**当前状态**：✅ 1:1 可映射

---

## 7. Evidence 映射

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

## 8. ValidationRecord 映射

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

**版本**：v1.0
**状态**：READY_FOR_HUMAN_REVIEW
