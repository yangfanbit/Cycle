# Canonical Timeline Export Regeneration Report

> 项目：Cycle-Research · 日期：2026-09-13 · 本轮：仅重新生成 canonical `exports/timeline_export_v1.json`，修正 `source_commit` 失真。

---

## 1. 原 source_commit 为什么错误

`exports/timeline_export_v1.json` 中的 `source_commit` 仍为 `49797cc...`（HDP v1 提交），但当前 HEAD 已是 `4bbe257...`（Timeline Export Contract v1.0 Finalization）。该字段语义为"数据来源 Git commit 可追溯"，指向旧提交导致**可追溯性失真**（数据状态与导出批次不对应）。

## 2. 当前 HEAD

`4bbe257d37d5991a2c6ce33def205df9a67e2593`（Timeline Export Contract v1.0 Finalization）

## 3. 新 source_commit

`4bbe257d37d5991a2c6ce33def205df9a67e2593` == `git rev-parse HEAD` ✅

## 4. generated_at

`2026-09-13T12:53:04`（重新生成时间戳）

## 5. Campaign 数量

**8**（C-2019-AD / C-2020-NEV / C-2021-NEV / C-2022-POLICY / C-2023-AD / C-2024-V2X / C-2024-ROBOTAXI / C-2025-ROBOTAXI）

## 6. Candidate 数量

**2**（RC-2023-HUAWEI、RC-2024-SECONDARY）

## 7. Signals / Events / Securities 数量

- **Signals：9**
- **Events：26**（19 绑定 + 6 全局 + 1 候选事件）
- **Securities：39**（31 campaign + 8 candidate）

## 8. 是否有业务数据变化

**无**。新旧导出逐字段 diff 仅 2 处：`/generated_at` 与 `/source_commit`。`research/batch/auto_2018_2025_batch_manifest.json` 与 `conflicts.json` 亦仅这 2 个元数据字段变化（纯生成差异）。Campaigns / research_candidates / signals / events / securities / themes / dates / 引用全部零变化。

## 9. 是否修改 DB

❌ **未修改**。`database/cycle_research.db` **zero diff**（git diff 为空）。

## 10. 是否修改 Schema

❌ **未修改**。`schema.sql` **zero diff**；`scripts/db.py` 未改；未修改 campaigns / annual_reviews / Research Model / Research Candidate / Evidence / Market Data / 日期；未新增历史研究。

## 11. 测试结果

```
validate_timeline_export.py    → PASS（contract=timeline_export；version="1.0"；顶层 11 字段；8/2/9/26/39；source_commit==HEAD）
validate_batch_research.py     → PASS（0 FAIL）
validate_db.py                 → PASS（0 FAIL, 0 WARNING）
```

`source_commit == git rev-parse HEAD` 重点校验：**相等，通过**。

---

## Git 变更清单

| 文件 | 变化 |
|---|---|
| `exports/timeline_export_v1.json` | 仅 `generated_at` + `source_commit`（49797cc → 4bbe257） |
| `research/batch/auto_2018_2025_batch_manifest.json` | 仅 `generated_at` + `source_commit`（纯生成差异） |
| `research/batch/conflicts.json` | 仅 `generated_at` + `source_commit`（纯生成差异） |
| `database/cycle_research.db` | **zero diff** |
| `schema/schema.sql` | **zero diff** |

---

# READY FOR CYCLE EXPORT SYNC

`exports/timeline_export_v1.json`（canonical v1.0）已重新生成，`source_commit = 4bbe257`（当前 HEAD），业务数据零变化，三项校验全部 PASS。Cycle 可于下一轮按契约同步本 JSON。
