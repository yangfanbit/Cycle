# _seasonal_analysis —— 探索性分析脚本（**已由 canonical 生成器取代**）

> ⚠️ **本目录不是产品代码，也不是 canonical 数据生成路径。** 请勿在流水线中引用。

## 状态

| 项目 | 说明 |
|---|---|
| 性质 | **探索性脚本（exploratory scripts）** + 中间结果 |
| 轮次 | Seasonal Observation Pattern Discovery v0.1（2026-09-16） |
| 是否 canonical | **否** —— 已被 `research/scripts/build_time_observation_patterns.py` 取代 |
| 是否产品依赖 | **否** —— 产品只读 `time_observation_patterns_v0_1.json` |

## 内容

- 脚本：`build_dataset.py` / `analyze.py` / `drilldown.py` / `baseline.py` / `validate_patterns.py` / `make_deliverables.py`
- 中间结果：`observation_anchors_raw.csv` / `observation_units.csv` / `data_fitness.json` /
  `statistics_results.json` / `family_analysis.json` / `baseline_analysis.json` /
  `pattern_validation.json` / `seasonal_observation_candidates_v0_1.csv`

## 保留理由

作为**探索过程与中间结果的记录**保留（可追溯上游结论是怎么来的）。其中的锚点口径、
拒绝规则与背景基准已被正式写进研究报告与 canonical 生成器：

- 探索结论：`../Seasonal_Observation_Pattern_Discovery_v0_1.md`
- 整合报告（含与探索脚本的口径差异）：`../Time_Observation_Pattern_Integration_v0_1.md`
- canonical 生成器（唯一正式路径）：`research/scripts/build_time_observation_patterns.py`

## 若要复现 canonical 产物

```bash
python research/scripts/build_time_observation_patterns.py           # 生成
python research/scripts/build_time_observation_patterns.py --check   # 校验逐字节一致
```

**不要再运行本目录下的脚本去生成产品数据。**
