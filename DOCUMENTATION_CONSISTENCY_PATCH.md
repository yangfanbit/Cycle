# Research Model v1.0 Documentation Consistency Patch

> 文档一致性修复报告：确保冻结版研究模型文档与当前实际 SQLite Schema / 正式数据完全一致。
> 修复日期：2026-09-13

---

## 执行摘要

✅ **DOCUMENTATION CONSISTENCY PATCH COMPLETED**

所有文档已与实际 SQLite Schema 对齐，未修改任何数据库内容或历史研究数据。

---

## 1. 2023 Campaign 日期冲突修复

### 问题
- `research/annual/2023.md`：C-2023-AD 是 2023-06-12 → 2023-07-19
- `RESEARCH_MODEL_V1_FREEZE_REPORT.md` §10：错误地写为 "Campaign 1 (Smart Driving): 06-21 → 09-12"

### 修复
**已修复 `RESEARCH_MODEL_V1_FREEZE_REPORT.md`**：

```markdown
### 2023 Auto Intelligence
- **Formal Campaign**: C-2023-AD (Smart Driving): 06-12 → 07-19
- **Research Candidate**: RC-2023-HUAWEI (Huawei Auto)
- **09-12**: 原 Smart Driving 后验结束/转折观察点，**不是**正式 Campaign end_date
- **Theme Drift**: Smart Driving → Huawei Auto
- **Campaign Overlap**: 08-29~09-12
```

**已修复 `research/methodology/research_model_v1_0.md`**：

```markdown
### 2023 Auto Intelligence（theme_cycle_id = auto_intelligence_2023）

**Formal Campaign: C-2023-AD (Smart Driving)**
- Research Signals: 06-12 (EARLY_SIGNAL), 06-21 (THEME_FORMING)
- Campaign Start: 06-12
- Main Rise: 07-03 ~ 07-19
- End: 07-19

**Research Candidate: RC-2023-HUAWEI (Huawei Auto)**
- Research Signals: 08-29 (EARLY_SIGNAL Candidate), 09-04 (THEME_FORMING)
- Campaign Start Candidate: 09-12
- Broad Confirmation: 09-18
- Main Rise: 09下~10

**09-12**：原 Smart Driving 后验结束/转折观察点，**不是**正式 Campaign end_date
```

**结果**：✅ 日期冲突已解决，与数据库一致

---

## 2. rule_type 处理

### 问题
- `research_model_v1_0.md` 写了 `rule_type` 属性
- 但 `schema.sql` 的 `research_rules` 表没有此字段

### 修复
**已修复 `research_model_v1_0.md`**：

```markdown
### 属性
- `rule_id`：规则标识（如 `rule_auto_summer`）
- `status`：candidate / under_review / confirmed / weak / rejected
- **属于 Research Prior / Hypothesis**，不是市场事实

**注**：`rule_type` 为 conceptual classification / future candidate，当前 SQLite schema 未持久化此字段。
```

**结果**：✅ 明确标记为 future candidate，未虚构数据库字段

---

## 3. Campaign Status 处理

### 问题
- `research_model_v1_0.md` 定义了 Campaign Status（candidate/confirmed/weak/rejected）
- 但 `campaigns` 表没有 `status` 字段

### 修复
**已修复 `research_model_v1_0.md`**：

```markdown
## 6. Campaign Status（战役状态）

### 状态枚举
| Status | 含义 |
|---|---|
| **candidate** | 候选，待验证 |
| **confirmed** | 已确认 |
| **weak** | 弱，证据不足 |
| **rejected** | 已拒绝 |

**注意**：
- `confirmed` 是 Campaign status，不是 Campaign Phase。
- **Campaign status 是研究层概念**，当前正式 SQLite schema 不单独持久化 `status` 字段。
- 当前数据库正式字段仍是：`classification`、`strength`、`result`、`date_confidence`。
```

**结果**：✅ 明确标记为研究层概念，未虚构数据库字段

---

## 4. security_type 处理

### 问题
- `research_model_v1_0.md` 写了 `security_type` 属性（stock/index/etf）
- 但 `securities` 表没有此字段

### 修复
**已修复 `research_model_v1_0.md`**：

```markdown
## 10. Security（证券）

### 定义
Campaign 相关的股票 / 指数 / ETF。

### 属性
- `security_id`：证券标识
- `role`：leader / second_leader / representative / follow
- **Layer 1 Fact**：客观数据

**注**：`security_type`（stock / index / etf）为 research-level conceptual classification，当前 SQLite schema 未持久化此字段。
```

**结果**：✅ 明确标记为 research-level，未虚构数据库字段

---

## 5. 文档 ↔ Schema 全库检查结果

### 检查范围
- `research_model_v1_0.md`
- `README.md`
- `research/methodology/*.md`
- `RESEARCH_MODEL_V1_FREEZE_REPORT.md`
- `schema/schema.sql`

### 检查结果

| 实体 | 文档字段 | Schema 字段 | 状态 |
|---|---|---|---|
| **Rule** | rule_id, status, rule_type | rule_id, status | ✅ rule_type 标记为 future candidate |
| **Campaign** | campaign_id, classification, strength, result, status | campaign_id, classification, strength, result | ✅ status 标记为研究层概念 |
| **Campaign Phase** | phase_id, phase_type, start_date, end_date | phase_id, phase_type, start_date, end_date | ✅ 一致 |
| **Security** | security_id, role, security_type | security_id, role (campaign_securities) | ✅ security_type 标记为 research-level |
| **Evidence** | evidence_id, evidence_role, temporal_relation, independence_group | evidence_id, evidence_role, temporal_relation, independence_group | ✅ 一致 |
| **Market Data** | series_id, trade_date, price_type | series_id, trade_date, price_type | ✅ 一致 |

### 验证
- 创建了 `check_doc_schema_consistency.py` 脚本
- 所有文档字段已与 schema 对齐
- 不存在于 schema 的字段已标记为 future candidate / research-level
- 文档未虚构数据库字段

**结果**：✅ 文档与 Schema 完全一致

---

## 6. 是否修改 schema

**✅ 未修改**

**确认**：
- `schema.sql` 未做任何修改
- 所有文档修复仅涉及标记和说明，未涉及数据库结构变更

---

## 7. 是否修改任何历史研究数据

**✅ 没有**

**确认**：
- 2018–2025 annual_status 未改变
- formal campaigns 未改变
- research candidates 未改变
- Campaign dates 未改变
- database contents 未改变

**验证**：所有测试通过，数据完整性保持

---

## 8. 所有测试结果

| 测试项 | 结果 | 说明 |
|---|---|---|
| validate_db.py | ✅ PASS | 0 FAIL，0 WARNING |
| export.py | ✅ PASS | evidence isolation 验证通过 |
| gen_annual.py | ✅ PASS | 生成 2018-2025 全部年度报告 |
| gen_summary.py | ✅ PASS | 生成汇总报告 |
| calibrate_robotaxi.py | ✅ PASS | 9/9 tests |
| point_in_time_robotaxi.py | ✅ PASS | 12/12 tests |
| test_consistency.py | ✅ PASS | 9/9 tests |

**总计**：0 FAIL，0 WARNING

---

## 9. 修复文件清单

### 修改的文件
1. `RESEARCH_MODEL_V1_FREEZE_REPORT.md` - 修复 2023 Campaign 日期冲突
2. `research/methodology/research_model_v1_0.md` - 修复 rule_type、Campaign Status、security_type

### 新增的文件
1. `scripts/check_doc_schema_consistency.py` - 文档与 Schema 一致性检查脚本

---

## 10. 最终状态

✅ **DOCUMENTATION CONSISTENCY PATCH COMPLETED**

- 所有文档已与实际 SQLite Schema 对齐
- 未修改任何数据库内容或历史研究数据
- 所有测试通过（0 FAIL, 0 WARNING）
- Schema 未修改
- 文档未虚构数据库字段

**模型状态**：Research Model v1.0 保持冻结，文档一致性已确保。

---

**修复时间**：2026-09-13
**修复版本**：Research Model v1.0 Documentation Consistency Patch
**状态**：COMPLETED
