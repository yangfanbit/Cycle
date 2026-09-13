# Batch Research（批量研究层）

> 生产哲学（HDP v1）：**Raw → Multi-source Collection → Cross-check → PROVISIONAL → Human Review → VERIFIED**。
> 人工 Review 不再是批量生产的前置条件；**PROVISIONAL 可以用于研究预览与主 Cycle 开发预览**，但 **PROVISIONAL ≠ VERIFIED**，不得进入 Cycle verified。

## 目录说明

| 文件 | 说明 |
|---|---|
| `auto_2018_2025_batch_manifest.json` | 2018–2025 批量研究清单：每个 Campaign/年度条目含研究状态、日期候选、主题、证据/来源/独立组、行情快照、研究信号 |
| `conflicts.json` | 研究日期口径冲突记录（candidate_a = DB 冻结值 vs candidate_b = 研究复核候选），不强行解决，由人工 Review 裁决 |
| `README.md` | 本文件 |

## 状态定义（研究级，不进 SQLite schema）

| 状态 | 含义 | 使用约束 |
|---|---|---|
| **RAW** | 原始素材 | 尚未整理 |
| **PROVISIONAL** | 主题可识别 + 有行情/媒体证据 + ≥1 可靠来源 + 主要日期有依据 + 无跨时间因果错误 + 多来源已交叉比对 | 可用于研究预览 / Cycle Timeline 开发预览；**不进入 verified** |
| **CONFLICT** | Start/Peak/End/Theme 存在口径冲突 | 保留 candidate_a / candidate_b + 支持/反驳证据，不强行解决 |
| **VERIFIED** | 人工最终复核确认 | 唯一允许进入 Cycle verified 的状态（本轮为 0） |

**重要**：当前 SQLite 正式 schema 不要求增加这些字段；状态优先在 `research/batch/` 与 export manifest 层表达。

## 生成方式

```powershell
python scripts/fetch_market_batch.py      # 补齐缺失行情（幂等，腾讯免费接口）
python scripts/batch_auto_research.py     # 生成 manifest / conflicts / timeline_export_v1
python scripts/validate_batch_research.py # 校验批量研究输出
python scripts/validate_timeline_export.py# 校验时间轴导出契约
```

## 纪律

- 模型 v1.0 冻结：不新增实体/字段/schema，不改动正式 Campaign 日期。
- 增量丰富，不重写历史；发现更好日期 → 记录 research candidate / 本目录，不覆盖正式 DB（除非明确数据修复且有充分证据）。
- 失败年份（如 2018 no_clear_campaign）必须保留，不得为"证明 6–8 月汽车"而删除。
- 行情数据缺失时如实记录 `unavailable`，不伪造（AUTO_SW 申万汽车腾讯不可得）。
- 不计算 seasonality_score / win_rate / probability / predictive_model。
