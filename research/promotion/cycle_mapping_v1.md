# Cycle Mapping v1.0

> Cycle HistoricalCampaign ↔ Cycle-Research campaigns 字段映射表。
> 版本：v1.0
> 日期：2026-09-13

---

## 1. 目的

本文档定义 Cycle HistoricalCampaign 与 Cycle-Research campaigns 之间的字段映射关系，确保晋级时字段正确转换。

---

## 2. 核心字段映射

| Cycle HistoricalCampaign | Cycle-Research campaigns | 说明 |
|---|---|---|
| campaign_id | campaign_id | 直接映射 |
| rule_id | rule_id | 直接映射 |
| season_id | season_id | 直接映射 |
| campaign_year | campaign_year | 直接映射 |
| start_date | start_date | 直接映射 |
| end_date | end_date | 直接映射 |
| peak_date | peak_date | 直接映射 |
| strength | strength | 直接映射 |
| result | result | 直接映射 |
| classification | classification | 直接映射（如果 Cycle 支持） |
| source_id | source_id | 直接映射 |
| date_confidence | date_confidence | 直接映射（如果 Cycle 支持） |
| cross_year | （计算字段） | year(end_date) > year(start_date) |

---

## 3. cross_year 计算

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

## 4. Campaign Phase 映射

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

**约束**：
- 如果无法 1:1 映射，不要强行转换
- 写 `mapping_required` 并在 manifest 中阻止 promotion

---

## 5. Evidence 映射

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

## 6. ValidationRecord 映射

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

## 7. 禁止事项

- 禁止修改 Cycle
- 禁止修改 Cycle-Research 核心 Schema
- 禁止修改 Research Model
- 禁止写入 Cycle/data/verified/
- 禁止强行转换无法 1:1 映射的字段

---

**版本**：v1.0
**状态**：ACTIVE
