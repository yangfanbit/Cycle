# Research Model v1.0 Final Freeze Report

> 研究模型 v1.0 最终冻结报告：一致性清理完成，模型冻结。
> 冻结日期：2026-09-13

---

## 执行摘要

✅ **RESEARCH MODEL v1.0 FROZEN**

所有一致性问题已解决，数据库、脚本、研究报告、方法学、导出完全同步。

---

## 1. Campaign count 是否一致？

**✅ 一致**

| 年份 | formal_campaign_count | research_campaign_candidate_count | 状态 |
|---|---|---|---|
| 2018 | 0 | 0 | no_clear_campaign |
| 2019 | 1 | 0 | weak |
| 2020 | 1 | 0 | strong |
| 2021 | 1 | 0 | strong |
| 2022 | 1 | 0 | strong |
| 2023 | 1 | 1 (RC-2023-HUAWEI) | medium |
| 2024 | 2 | 0 | medium |
| 2025 | 1 | 0 | medium |

**验证**：`test_consistency.py` PASS

---

## 2. 2022 中通客车最终是什么？

**✅ Observation（观察）**

**判定**：
- 12连板（+214.52%）但系"核酸检测车"概念个股事件
- 不符合 Campaign 判定标准（无明确主题、非汽车主线）
- **分类**：Observation，不进入 `campaigns` 表
- **证据**：E-2022-05（contradicting，independence_group=orig_counter_single_stock）

**统一**：
- `research/annual/2022.md`：明确标注为中通客车为个股事件，不计入 Campaign 主线
- `research/c2/2022_auto_boundary_review.md`：已记录
- `research/summary/auto_2018_2025_final_review.md`：已统一

---

## 3. 2023 Huawei Auto 是 formal 还是 research candidate？

**✅ Research Candidate（研究候选）**

**判定**：
- 保留为 `RC-2023-HUAWEI`，不进入 `campaigns` 表
- 保留在 `research/c2/` 文件中
- 未达到正式 Campaign 门槛（需人工确认）

**统一**：
- `research/annual/2023.md`：formal_campaign_count = 1（C-2023-AD）
- `research/summary/auto_2018_2025_final_review.md`：明确标注 research_campaign_candidate_count = 1
- `research/methodology/research_model_v1_0.md`：定义 Campaign Candidate 标准

---

## 4. 2024 Secondary 是 formal 还是 research candidate？

**✅ Research Candidate（研究候选）**

**判定**：
- 2024-09-05~06 为 Weak Secondary Campaign Candidate
- 不进入 `campaigns` 表
- 保留为研究级候选

**统一**：
- `research/annual/2024.md`：formal_campaign_count = 2（C-2024-V2X, C-2024-ROBOTAXI）
- `research/summary/auto_2018_2025_final_review.md`：明确标注 Secondary 为 Candidate

---

## 5. Total Evidence / Bound / Unbound 数量

**✅ 明确**

| 类型 | 数量 | 说明 |
|---|---|---|
| **Total Evidence** | 46 | 全部证据 |
| **Campaign-bound** | 39 | 通过 campaign_evidences 显式绑定 |
| **Unbound** | 7 | 合法状态，支持整个 Rule 或无法属于特定 Campaign 的反例 |

**验证**：`test_consistency.py` PASS

**修复**：
- `COMPREHENSIVE_AUDIT_REPORT.md`：已更新为正确数量（46/39/7）
- 不再写"46 条 Evidence 全部显式绑定"

---

## 6. Tier 1–4 是否统一

**✅ 统一**

| Tier | 定义 | 示例 |
|---|---|---|
| **Tier 1** | 交易所 / 监管机构 / 政府 / 公司正式公告 / 财报 | 证监会、国务院、公司公告 |
| **Tier 2** | 中国证券报 / 证券时报 / 第一财经 / 财联社 / 界面 / 新华社 / 权威行业协会 | 中证报、证券时报、财联社 |
| **Tier 3** | 券商研报 / 研究机构 / 专业财经网站 | 券商研报、Wind、同花顺 |
| **Tier 4** | 雪球 / 自媒体 / 论坛 / 博客 / 社交媒体 | 雪球、微博、知乎 |

**约束**：
- Tier 4 只能作为线索，不能单独使 Campaign 成为 Research Confirmed
- `source_type` 与 `tier` 不得矛盾

**验证**：`test_consistency.py` PASS

**统一**：
- `schema.sql`：CHECK 约束支持 Tier 1-4
- `README.md`：已更新
- `research/methodology/historical_campaign_validation_v1.md`：已更新
- `research/methodology/research_model_v1_0.md`：已更新
- 所有 annual reports：已统一

---

## 7. Opportunity State 是否统一

**✅ 统一**

### Research Signal
- EARLY_SIGNAL
- THEME_FORMING
- CONFIRMATION_CANDIDATE

### Campaign Status
- candidate
- confirmed
- weak
- rejected

### Campaign Phase
- MAIN_RISE
- PEAK
- RETRACEMENT
- DECLINING
- SECONDARY
- ENDED

**关键约束**：
- `CONFIRMED` 是 Campaign status，**不是** Campaign Phase
- Research Signal **不属于** Campaign Phase
- Campaign start 后才能产生 Campaign Phase

**验证**：`test_consistency.py` PASS

---

## 8. Rule 最终定义

**✅ 历史观察窗口（Historical Observation Window）**

**评价**：**Partially Supported**（部分支持）

**约束**：
- 这是 **research conclusion**，不是预测
- 需结合 Research Signal 触发
- 需排除市场 β contamination
- 强度需根据具体年份评估

**统一**：
- `research/summary/auto_2018_2025_final_review.md`：明确定义
- `research/methodology/research_model_v1_0.md`：明确约束

---

## 9. Schema 是否修改

**✅ 未修改**

**理由**：
- 2022/2023/2024 三案例均能自然表达，无需强行修改
- research-level 标注已足够表达 Theme Cycle / Theme Drift / Campaign Overlap
- 避免过度设计，保持简洁

**未创建**：
- `theme_cycles` 表
- `campaign_relations` 表
- 新的正式 research candidate tables

---

## 10. 2022/2023/2024 是否全部自然表达

**✅ 全部自然表达**

### 2022 Auto Policy
- Research Signals: 04-27 (EARLY_SIGNAL), 05-23 (THEME_FORMING)
- Campaign Phases: 05-23 → 06-28 (Main Rise), Peak cluster, Retracement, Declining, End
- 中通客车 = Observation

### 2023 Auto Intelligence
- **Formal Campaign**: C-2023-AD (Smart Driving): 06-12 → 07-19
- **Research Candidate**: RC-2023-HUAWEI (Huawei Auto)
- **09-12**: 原 Smart Driving 后验结束/转折观察点，**不是**正式 Campaign end_date
- **Theme Drift**: Smart Driving → Huawei Auto
- **Campaign Overlap**: 08-29~09-12

### 2024 Robotaxi
- Main Campaign: 07-08 → 08-23
- Secondary: 09-05~06 (Weak Candidate)

**验证**：`test_consistency.py` PASS

---

## 11. 是否仍存在内部矛盾

**✅ 无内部矛盾**

**已解决**：
1. ✅ Campaign Count 统一（formal vs research candidate）
2. ✅ Evidence Count 统一（total/bound/unbound）
3. ✅ Source Tier 统一（Tier 1-4 定义一致）
4. ✅ Opportunity State 统一（Signal/Status/Phase 分离）
5. ✅ 三层语义统一（Fact/Interpretation/Grouping）
6. ✅ Campaign vs Observation 判定规则固化
7. ✅ Research Campaign Candidate 处理（Huawei Auto 2023）

---

## 12. 是否可以冻结研究模型

**✅ 可以冻结**

**理由**：
1. 所有一致性问题已解决
2. 数据库、脚本、研究报告、方法学、导出完全同步
3. 所有测试通过（0 FAIL, 0 WARNING）
4. 方法学已固化（research_model_v1_0.md）
5. 三案例统一建模完成（2022/2023/2024）

**冻结内容**：
- Research Model v1.0
- Theme Lifecycle v0.2
- Historical Campaign Validation v1.0
- 2018-2025 数据与报告

---

## 13. 测试总结

| 测试项 | 结果 | 说明 |
|---|---|---|
| validate_db.py | ✅ PASS | 0 FAIL，0 WARNING |
| export.py | ✅ PASS | evidence isolation 验证通过 |
| gen_annual.py | ✅ PASS | 生成 2018-2025 全部年度报告 |
| gen_summary.py | ✅ PASS | 生成汇总报告 |
| calibrate_robotaxi.py | ✅ PASS | 9/9 tests |
| point_in_time_robotaxi.py | ✅ PASS | 12/12 tests |
| test_consistency.py | ✅ PASS | 9/9 tests（新增一致性测试） |

**总计**：0 FAIL，0 WARNING

---

## 14. Git 状态

- **分支**：main
- **状态**：up to date with origin/main
- **提交**：待提交

---

## 15. 最终结论

✅ **RESEARCH MODEL v1.0 FROZEN**

所有一致性问题已解决，研究模型 v1.0 已冻结，可以进入下一阶段。

**下一阶段**：
1. 人工确认 verified 日期（start/peak/end）
2. 将 verified 数据导入 Cycle/data/verified/
3. 应用 Theme Lifecycle v0.2 到新行业/题材
4. 开发长期历史规律研究基础设施

---

**冻结时间**：2026-09-13
**冻结版本**：Research Model v1.0
**状态**：FROZEN
