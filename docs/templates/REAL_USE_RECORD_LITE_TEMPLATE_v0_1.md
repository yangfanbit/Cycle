# 真实使用记录模板 · 轻量版 v0.1（空白 · 日常记录入口）

> ★★ **本文件是空白模板，不含任何真实记录**，填写后的文件不要提交到仓库
> （导出文件放 `.tmp/real_use/records/`，已被 `.gitignore` 忽略）。
> 配套 `docs/REAL_USE_LITE_v0_1.md`（3 字段协议）与
> `docs/REAL_USE_DECISION_RULE_v0_1.md`（事前冻结的判定规则）。
> ★ 判定阈值在看到结果之前已锁死，**不得事后修改**；`check_real_use_protocol_v0_1.py --check`
> 会核对规则文件指纹，改动即 FAIL。

## 日常怎么用（2 分钟内）

工作台「历史检索 / 记录 → ③ 冻结判断」里填 3 个手填字段，点「冻结这条记录」；
事后核对在**独立区域**填写，不会改动正文。收口时点「导出 JSON」，
把文件放到 `.tmp/real_use/records/`，再跑校验器。本模板只在需要手写记录时使用。

## T 时刻正文（自动字段由系统生成，不用手填）

```yaml
record_id:      RU-YYYYMMDD-NN      # 自动
frozen_at:      YYYY-MM-DDTHH:MM+08:00   # 自动，不接受手填
data_as_of:     YYYY-MM-DD          # 自动，从页面/产物读取
artifact_ref:   ""                  # 自动，当时的产物版本
item_ref:       ""                  # 可空，关联的线索 ID

# ══ 以下为 T 时刻必须写下的内容 ══
question:       ""                  # 一句话研究问题，不写「随便看看」
verdict_at_T:   ""                  # 看到后续行情/结果之前写下：线索是什么、我此前是否考虑过、准备做什么
type:           LEAD                # 六类之一，见下（工作台里是下拉选择）
cluster_id:     ""                  # 同一题材 / 事件 / 同一周填同一个；可空但必须尽量填
```

★ **字段口径**：协议 §1 把「3 个手填字段」记作 `question` / `verdict_at_T` / `posthoc_check`，
其中 `posthoc_check` 在物理上**独立存储**、不属于 T 时刻正文；工作台导出的 `records[]` 里
是 `question` / `verdict_at_T` / `type` / `cluster_id`，`evals[]` 里是 `is_new_correspondence`。
`type` 与 `cluster_id` 在工作台 UI 上需要选择/填写（协议原文写「自动字段」是当时的表述），
**以工作台实际为准**；`frozen_at` / `data_as_of` / `record_id` / `artifact_ref` 才是真自动字段。

★ `NO_LEAD` / `BLOCKED` / `UI_FRICTION` 必须在 `verdict_at_T` 里写**触发量**
（看了哪些页、查了哪些题材、花多久、为什么没产出）。
★ `CONFIRM` 的增量可能为 0，也要记。正向 / 负向 / 零触发 / 摩擦**同等记录**。

## 事后核对 `posthoc_check`（独立文件 `<record_id>.eval.md`，不改正文）

```yaml
record_id:      RU-YYYYMMDD-NN
checked_at:     YYYY-MM-DDTHH:MM+08:00   # 必须晚于 frozen_at
is_new_correspondence: ""          # YES（可核）/ NO（本来就知道或不成立）/ UNVERIFIABLE
note:           ""                  # 指到具体一条：哪个题材、哪个年份、哪个事件 ID；写不出就填「无」
research_hours: 0                  # 净耗时（搜集 + 核对 + 比较），不含写记录本身
```

★ **首次判断才计分**：同一 `record_id` 若有多条核对，只取 `checked_at` 最早的一条计入判定；
后续修订单列 `REVISION`，标「学习记录，不计入 headline」，**不得**回头改 T 时刻正文。
★ 需要更正正文时新建 `amend-NN`，不覆盖原记录。

## 不做什么

- 不写「没有触发 = 工具无效 = 成功」；没有记录就写「本轮未开展」。
- 不用 5/10/20 日超额、命中率、胜率、行情涨跌作有效性证据。
- 不把线索写成推荐、买卖点、选股清单，或给龙头 / 弹性标签。
- 已结算 cluster < 20 时只报触发量与数据限制，**不下结论**。
