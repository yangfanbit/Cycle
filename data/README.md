# data/ —— 历史规律核验数据目录（V1.5）

> ## ★ 当前状态（2026-09-26 复核 · 保留并标注）
>
> - **本目录当前无消费者**：`src/` 与 `tests/` 中均未 import `data/*`，
>   `src/data/index.ts`（barrel）亦无任何引用。
>   生产 Timeline 的**唯一**数据源是 `exports/timeline_export_v1.json`。
>   → **这不是「双源」，不构成运行时数据污染风险。**
> - **`verified/` 层当前为空（0 条）** —— 这是**合法状态**：人工核验（L2）尚未执行，
>   **不得为填充而编造历史事实**。
> - **人工核验是后续计划**：本目录按 V1.5 核验管线语义**保留**，待后续轮次启用；
>   启用前请勿将其当作活跃数据源，也不要删除。
> - 详见 `docs/THREEC_REPOSITORY_ARCHITECTURE_REVIEW_v1.1.md`「F-3 修正」。

本目录是核验管线的数据层，语义对应 docs/HISTORICAL_VALIDATION.md：

```
Source（来源） → Evidence（证据） → Historical Fact / Campaign（历史事实） → Verification（验证）
```

## 目录语义

| 目录 | 语义 | 当前内容 |
|------|------|----------|
| `raw/` | 原始数据：来源注册表（sources）与原始材料摘录（excerpts），保留原始口吻，不改写 | src_exp_001 等来源 + 材料要点摘录 |
| `candidate/` | 未经核验的候选知识：候选规律（rules + timeWindows）、题材分类与事件日历（themes / events，中性参考表，未经过核验流程）。**Preflight 方案 A 后：campaigns 恒空**——未核验行情线索只存 Evidence，不经本层 | rules / themes / events（campaigns 为空） |
| `verified/` | 已人工核验的历史事实（L2）。人工核验完成后真实 HistoricalCampaign 直接写入此层，不经过 candidate | **空**。录入标准见 docs/HISTORICAL_VALIDATION.md |
| `validation/` | 核验结果：证据（evidence）、核验记录（records）、Pilot 计划（pilot） | 3 条 Pilot 骨架 |

## 规则

1. **升层必须留痕**：candidate → verified 的每次移动都要在 CHANGELOG.md 记录依据（source_id / evidence_id）。
2. **禁止降级删数据**：核验中发现失败年份，应保留并更新 result，不得删除。
3. `src/data/index.ts` 是唯一 re-export 出口，应用代码不得直接 import 本目录内模块路径。
4. 数据仍为类型化 TS 模块；未来迁移 SQLite 时按目录语义建表（raw→sources/excerpts 表，candidate→rules/campaigns 表，verified→campaign_facts 表，validation→evidence/validation_records 表）。
5. **测试 / 结构示例数据禁止进入本目录**：fixture 只能放 `tests/fixtures/`（见 cmp_media_2026_2027 迁移先例）。
