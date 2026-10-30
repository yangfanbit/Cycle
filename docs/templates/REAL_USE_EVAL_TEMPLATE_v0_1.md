# 真实使用事后评估模板 v0.1（空白 · 保存为 `<record_id>.eval.md`）

> 配套 `docs/THREEC_REAL_USE_PROTOCOL_v0_1.md` §3.2。
> ★★ **本文件是空白模板**。填写后的文件**不要提交到仓库**。
> ★★ 本文件与 `<record_id>.md`（T 时刻冻结正文）是**两个独立文件**：
> 这里写事后结果，**不得**回头修改冻结正文或其 `.sha256`。
> ★ 可多次追加；每次追加在末尾写日期，不改前面的内容。

```yaml
record_id:      RU-YYYYMMDD-NN      # 必须与冻结正文一致
frozen_check:   ""                  # shasum -a 256 -c 的结果：OK / MISMATCH（MISMATCH 时停止评估并说明）

# ══════════ 事后结果 ══════════
evaluated_at:       YYYY-MM-DD
research_hours:     0               # 净耗时（小时，含搜集/核对/比较）
new_correspondence: ""              # 是否真的发现了新的历史对应；有则写明哪一条
false_alarm:        ""              # 哪些提示被证明无效
evidence_quality:   ""              # 报道点名 / 盘面 / 仅推断 / 无法核实
outcome:            ""              # 成势 / 未成势 / 仍在进行 / 无法判断
evaluation_note:    ""
```

## 填写要点

1. **先跑 `frozen_check`**：若 `shasum -a 256 -c` 报 `MISMATCH`，说明冻结正文被改动过 ——
   此时**不要**继续评估，先新建 `amend-NN.md` 说明改动，再评估。
2. **`research_hours` 只算净耗时**（搜集 + 核对 + 比较），不含写这条记录本身的时间。
3. **`new_correspondence` 要能指到具体一条**（哪个题材、哪个年份、哪个事件 ID）。
   写不出具体的一条 → 填 `无`，不要写「有一些启发」。
4. **`false_alarm` 与 `outcome` 同等重要**：被证明无效的提示是下一轮改进的唯一依据。

## 需要更正冻结内容时

新建 `<record_id>.amend-NN.md`：

```yaml
record_id:   RU-YYYYMMDD-NN
amends:      <字段名>
old_value:   ""          # 原值（逐字抄自冻结正文）
new_value:   ""
reason:      ""
at:          YYYY-MM-DDTHH:MM+08:00
```

★ **不覆盖**原冻结文件与它的 `.sha256`；原文件的摘要仍然有效（它证明的是「当时写的是什么」）。
