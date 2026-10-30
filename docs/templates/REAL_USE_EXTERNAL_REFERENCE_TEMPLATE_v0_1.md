# 外部独立参照模板 v0.1（空白 · 可选，本轮**不招募**）

> 流程与纪律见 `docs/THREEC_REAL_USE_PROTOCOL_v0_1.md` §4。
> ★★ **本文件是空白模板**。不得编造参照者、访谈或结论；没有参照者就写「本轮未开展」。
> ★★ 参照者数量 < 5 时，结论一律标 **`EXPLORATORY_CONTRAST`**，不得外推。

---

## 0 · 对照设置（先填，再开始）

```yaml
contrast_id:     XR-YYYYMMDD-NN
task_question:   ""          # 与研究问题完全一致，不得对参照者简化
data_as_of:      YYYY-MM-DD  # 与 ThreeC 侧完全相同
background_given: ""         # 提供给参照者的背景（逐字记录，证明没多给）
threec_output_shown: false   # ★ 必须为 false
reference_person:
  type:          ""          # 同事 / 朋友 / 其他（不记姓名，用代号）
  familiarity:   ""          # 对该题材的熟悉程度：高 / 中 / 低
  tools:         []          # 惯常工具：Wind / Choice / 研报库 / 搜索引擎 / 记忆
```

## 1 · 参照者侧（**先冻结，后比对**）

```yaml
ref_frozen_at:   YYYY-MM-DDTHH:MM+08:00
ref_hours:       0           # 研究耗时（小时）
ref_leads:                   # 参照者找到的线索清单（冻结，不随后修改）
  - theme:       ""
    years:       []
    securities:  []
    sources:     []
    confidence:  ""          # 高 / 中 / 低
ref_notes:       ""
```

## 2 · ThreeC 侧（同样先冻结）

```yaml
threec_frozen_at: YYYY-MM-DDTHH:MM+08:00
threec_hours:     0
threec_leads:
  - theme:        ""
    years:        []
    securities:   []
    sources:      []
    artifact_ref: ""         # 产物 + 版本 + commit
```

## 3 · 比对（双方都冻结后填）

```yaml
comparison:
  both:            []        # 共同发现（两边都有）
  threec_only:     []        # ThreeC 独有 —— ★ 必须经参照者确认「这确实是个历史对应」
  conventional_only: []      # ★ 常规工具独有 —— ThreeC 的盲区，必须逐条保留
  unverifiable:    []        # 双方都给不出可核来源
  task_differences: ""       # 任务理解差异（若两边理解的不是同一问题，本次对照作废）
  year_coverage:
    ref:     ""              # 参照者覆盖的历史年份范围
    threec:  ""              # ThreeC 覆盖的历史年份范围
  source_quality:  ""        # 一手 / 媒体 / 二手转述
```

## 4 · 结论（只能写到这个强度）

```yaml
verdict_label:   EXPLORATORY_CONTRAST     # ★ 数量 <5 时必须用这个
statement:       ""                       # 只描述「这 1 次对照里观察到了什么」
must_not_claim:  []                       # 明确列出本次不能说的话（如「ThreeC 优于常规方法 X%」）
```

---

## 填写要点

1. **`threec_output_shown: false` 是这次对照成立的前提**。若事先展示过，本次对照**作废**，
   改写 `task_differences: "已展示 ThreeC 输出 → 对照无效"`。
2. **`conventional_only` 是最有价值的一栏** —— 它直接暴露 ThreeC 的覆盖缺口（例如某个题材
   在 ThreeC 里根本没有地图）。不许因为「不好看」而省略。
3. **耗时对比只能在任务完全相同时比较**。若参照者理解的问题不同，只记耗时、不比较优劣。
4. **1 位参照者只能算 1 个观察**，且参照者本身也有自己的知识偏差（可能早就知道该题材）。
