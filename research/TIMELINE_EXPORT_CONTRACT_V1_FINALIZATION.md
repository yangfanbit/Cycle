# Timeline Export Contract v1.0 Finalization

> 项目：Cycle-Research · 日期：2026-09-13 · 基线 HEAD：`49797cc`（HDP v1）
> 本轮范围：Research → Cycle Timeline Export Contract v1.0 对齐。**未新增历史研究，未改 SQLite schema，未改 DB。**

---

## 1. 为什么旧 Contract 与 Cycle 不兼容

旧 `timeline_export_v1.json` 顶层为 `{contract, timeline_export_version, generated_at, source_commit, project, purpose, rules, signals, campaigns, events, securities}`，且：
- `campaigns.status` 使用 **promotion 词汇**（`READY_FOR_HUMAN_REVIEW` / `RESEARCH_CANDIDATE`），与生产语义混杂；
- `events` / `securities` 以 `[{campaign_id, events: [...]}]` **按 Campaign 嵌套**，无顶层扁平数组、无全局事件/候选归属表达；
- `signals` 嵌套且强制挂 `campaign_id`，无法表达 Research Candidate 信号；
- 无 `research_candidates`，RC-2023-HUAWEI / RC-2024-SECONDARY 无法进入 Cycle Preview；
- 版本字段语义不唯一、字段无契约文档。

而 Cycle Adapter 期待 `{export_version, generated_at, source_project, campaigns}` —— **两侧不是同一 Contract**，直接消费会失败。

## 2. Canonical Contract 最终是什么

见 [timeline_export_contract_v1.md](research/methodology/timeline_export_contract_v1.md)（唯一接口说明）。顶层 11 字段：

```
contract · timeline_export_version · generated_at · source_commit · project
· rules · signals · campaigns · research_candidates · events · securities
```

- `timeline_export_version = "1.0"`（唯一版本字段，不再出现 `export_version` / `source_project`）。
- 字段全部白名单校验，research-only 字段与 Cycle 字段严格分离。

## 3. research_candidates 为什么需要

RC-2023-HUAWEI（华为汽车 2023）与 RC-2024-SECONDARY（2024 Robotaxi 次级）是**已识别但未达正式 Campaign 门槛**的研究候选。它们**不进入正式 campaigns**，但**应在 Cycle Preview 中被展示**（帮助"提前观察"）。新增顶层 `research_candidates` 数组承载，每项含 `campaign_id / rule_id / year / title / 候选日期 / themes / event_ids / security_ids / early_signal / research_status / theme_cycle_id / conflicts / notes`。日期不确定则保留候选值，不伪装 Verified。

## 4. signals 如何归属

扁平数组，归属二选一：**`campaign_id`（formal signal）或 `research_candidate_id`（candidate signal）**。不强制 signal 必须挂 campaign。例：
`{"type":"EARLY_SIGNAL","date":"2023-08-29","confidence":"low","research_candidate_id":"RC-2023-HUAWEI"}`。

## 5. events 如何归属

扁平数组，每项带 `event_id / name / date / event_type / role / campaign_id / research_candidate_id`。**全局事件允许 `campaign_id = null`**（如 EV-2018-01 特斯拉临港建厂、EV-2024-04 特斯拉发布会、EV-2025-03 个股事件），不强行绑定。Campaign 通过 `event_ids` 引用（`event_ids` 引用必须与 events 归属一致，validator 校验）。

## 6. securities 如何归属

扁平数组，**每项必须知道属于谁**：`campaign_id` 或 `research_candidate_id`，禁止无归属条目（validator 对 `security_id` 无 owner 直接 FAIL）。同一证券可属于多个 owner（如 比亚迪 属于 3 个 Campaign），每 `(security_id, owner)` 一条。**禁止把整个证券表复制进每个 Campaign**——Campaign 只带 `security_ids` 引用。

## 7. status 如何统一

- **生产兼容 `status`**（Cycle 消费，小写）：`verified` / `provisional` / `conflict` / `preview`。
- **研究层 `research_status`**（大写）：`PROVISIONAL` / `CONFLICT` / `INSUFFICIENT`。
- **promotion 词汇**单独命名 `promotion_status`（如 `READY_FOR_HUMAN_REVIEW`），不再占用 `status`。
- 不再出现 `status = RESEARCH_CANDIDATE` 与 `research_status = PROVISIONAL` 混用。
- 当前映射：8 个 Campaign = provisional ×6 + conflict ×2；2 个候选 = preview（无生产 status）。

## 8. version 如何统一

只保留 `timeline_export_version = "1.0"`。validator 对顶层出现 `export_version` 直接 FAIL（版本语义唯一）。未来 1.1 只增不改删，2.0 才允许破坏性变更（见契约文档 §2 / §13）。

## 9. Cycle 是否可以直接消费

✅ 可以（机器可解析、字段白名单、归属一致、引用可追溯）。`validate_timeline_export.py` 全 14 项 PASS：顶层字段 / rules / signals / campaigns / research_candidates / events / securities / 字段白名单 / 日期格式 / ID 唯一性 / 候选不进 campaigns / CONFLICT 必有 conflicts / 候选不伪装 verified / source_commit 存在。Cycle Adapter 只需按 `timeline_export_version=1.0` 读取即可；`events`/`securities` 顶层扁平、`campaigns` 经 `event_ids`/`security_ids` 引用。

## 10. Validator 是否覆盖全部 Contract

✅ 是。`validate_timeline_export.py` 重写为 14 项 + **RC-2023-HUAWEI 关键测试**（模拟候选进入 `research_candidates`、确认不出现在 `campaigns`、但可出现在 `timeline_export`）。另运行 `validate_batch_research.py` / `validate_db.py` / `check_doc_schema_consistency.py` / `test_doc_schema_checker.py`，全部 PASS（0 FAIL, 0 WARNING）。

## 11. 是否修改 DB

❌ **未修改**。`database/cycle_research.db` 零变化（git status 无此文件）。本轮 batch 脚本只读数据库。

## 12. 是否修改 Schema

❌ **未修改**。`schema.sql` 零变化；`scripts/db.py` 未改。研究级状态全部表达在 export / batch / docs 层。

## 13. 当前 2018–2025 数据数量

| 指标 | 数量 |
|---|---|
| Campaign（formal） | 8（2019–2025，每年 1–2 个） |
| 2018 反例年份条目 | 1（Y2018-NO-CLEAR，保留） |
| Research Candidate | 2（RC-2023-HUAWEI、RC-2024-SECONDARY） |
| Research Signal | 9（5 组 campaign + 2 组 candidate） |
| Events | 26（19 绑定 + 6 全局 + 1 候选事件） |
| Securities（含归属） | 39（31 campaign + 8 candidate） |
| Evidences / Sources | 46 / 49 |
| Market daily / series | 16,266 行 / 32 条 |
| Verified Campaign | 0（人工 Review 未发生，不阻塞时间轴开发预览） |

## 14. Product Purpose Check

经 [product_purpose_checkpoint.md](research/methodology/product_purpose_checkpoint.md) 四问检查：
1. 是否帮助构建时间轴？→ ✅ 是（campaigns + research_candidates + events + securities 均可被时间轴消费）
2. 是否提高历史可比性？→ ✅ 是（状态/归属/引用统一）
3. 是否有助于识别提前信号？→ ✅ 是（signals 支持 candidate，early_signal 保留）
4. 是否只是工程复杂化？→ ❌ 否（未改 DB/schema，未新增研究，未做统计；改动仅限接口契约 + 校验 + 文档）

未偏离初心。无 AI 预测 / 实时行情 / 资金流 / 胜率 / 新库 / 新 Schema。

---

## 验证结果

```
validate_timeline_export.py    → PASS（14 项 + RC-2023-HUAWEI 测试，0 FAIL）
validate_batch_research.py     → PASS（0 FAIL）
validate_db.py                 → PASS（0 FAIL, 0 WARNING）
check_doc_schema_consistency   → PASS（0 FAIL）
test_doc_schema_checker        → PASS（0 FAIL, 0 WARNING）
```

---

# READY FOR CYCLE ADAPTER INTEGRATION

`exports/timeline_export_v1.json`（canonical v1.0）已重新生成：8 campaigns + 2 research_candidates + 26 events + 39 securities + 9 signals，字段白名单与归属全部通过 validator。Cycle Adapter 可直接按本契约接入；研究候选可进入 Cycle Preview；正式 Campaign 的 VERIFIED 层（0 条）待人工最终 Review（不影响开发预览）。

> `source_commit` = `49797cc`（本批数据状态基线）；本轮交付提交后将在 Git 历史可见。
