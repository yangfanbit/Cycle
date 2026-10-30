# 真实使用记录模板 v0.1（空白 · 复制到 `.tmp/real_use/records/` 填写）

> 使用说明见 `docs/THREEC_REAL_USE_PROTOCOL_v0_1.md`。
> ★★ **本文件是空白模板，不含任何真实记录**。填写后的文件**不要提交到仓库**。
> ★★ §A 必须在**看到后续行情结果之前**填写并冻结；§B 事后追加，**不得修改 §A**。

```yaml
# ─────────── §A · T 时刻冻结（看到结果之前） ───────────
record_id:      RU-YYYYMMDD-NN
frozen_at:      YYYY-MM-DDTHH:MM+08:00
data_as_of:     YYYY-MM-DD          # 从页面/产物读到的「行情截至」，不凭记忆

question:       ""                  # 一句话研究问题
background:     ""                  # 触发背景：新闻/财报/政策/盘面/他人提问

threec_output:
  theme:        ""                  # 题材 / 主题
  events:       []                  # 具体历史事件（event_id 或 年份+名称）
  securities:   []                  # 参与标的（若有）
  rationale:    ""                  # ThreeC 给出的理由（原文摘录，不改写）
  sources:      []                  # 来源链接（页面里给的，不补造）

artifact_ref:
  artifacts:    []                  # 产物文件名 + 版本，如 historical_market_roles_v0_13.json
  page_block:   ""                  # 页面区块名，如「历史题材地图 / 半导体 / 事件卡」
  commit:       ""                  # git rev-parse HEAD 或页面 Build Provenance

novelty_self:   ""                  # 新颖 / 已知 / 不确定  ← 只能三选一
novelty_why:    ""                  # 理由（★ 弱证据，见协议 §5）
worth_researching: ""               # 是 / 否 + 理由

conventional_methods:
  available:    ""                  # 当时有哪些常规方法可用
  actually_used: []                 # 实际用了哪些（Wind/Choice/研报/搜索/记忆/无）

frozen_verdict: ""                  # LEAD / CONFIRM / REJECT / NO_LEAD / BLOCKED / UI_FRICTION
cluster_id:     ""                  # 同题材/同事件/同催化共用同一个 id

# ─────────── §B · 事后追加（不得修改 §A） ───────────
evaluated_at:   ""                  # YYYY-MM-DD
research_hours:                     # 净耗时（小时，含搜集/核对/比较）
new_correspondence: ""              # 是否真的发现了新的历史对应；有则写明哪一条
false_alarm:    ""                  # 哪些提示被证明无效
evidence_quality: ""                # 报道点名 / 盘面 / 仅推断 / 无法核实
outcome:        ""                  # 成势 / 未成势 / 仍在进行 / 无法判断
evaluation_note: ""

# ─────────── 冻结完整性 ───────────
amendments: []                      # 若确需更正 §A：{field, old, new, reason, at}
record_sha256: ""                   # shasum -a 256 本文件（§A 填完后立即计算并写回）
```

---

## 填写要点（避免最常见的三种错误）

1. **`data_as_of` 不许写「今天」** —— 必须写页面上显示的「行情截至」日期。
   二者常常不同（例如页面显示 2026-10-29，而你实际是在 10-30 打开）。
2. **`threec_output` 必须是原文摘录** —— 不许把事后理解写回去。
   若当时只看到「题材名 + 年份」，就只写这些，不要补全成完整论证。
3. **`novelty_self` 只有三选一** —— 不许写「应该是新的」。拿不准就写 `不确定`。

## 什么时候**不要**建记录

- 只是浏览页面、没有具体研究问题 → 记进 `.tmp/real_use/sessions.md` 的触发量，不建 RU 记录。
- 同一个问题在同一天反复查看 → 合并为 1 条，在 `evaluation_note` 里写「重复查看 N 次」。

## 负向记录怎么填（同等重要）

| 情形 | `frozen_verdict` | 要点 |
|---|---|---|
| 带问题去查，没查到可用线索 | `NO_LEAD` | 必须写**查了哪些页面/题材**、耗时 |
| 因数据缺失/口径不清中止 | `BLOCKED` | 写明缺什么数据、卡在哪个口径 |
| 页面没能帮上忙 | `UI_FRICTION` | 写明**具体哪一步**卡住（找不到入口/看不懂/读完仍无结论） |
| 线索让作者**放弃**了某方向 | `REJECT` | 写明放弃的理由与被否掉的替代方向 |
