# 真实使用记录模板 v0.1（空白 · 复制到 `.tmp/real_use/records/` 填写）

> 使用说明见 `docs/THREEC_REAL_USE_PROTOCOL_v0_1.md` §3。
> ★★ **本文件是空白模板，不含任何真实记录**。填写后的文件**不要提交到仓库**。
> ★★ 结构：**12 个通用必填字段 + 1 个条件字段（`threec_output`）= 13 个顶层字段**。
> ★★ 本文件 = **T 时刻冻结正文**。写完后**不再修改**；摘要另存 `.sha256`；
> 事后结果写 **`<record_id>.eval.md`**（见 `REAL_USE_EVAL_TEMPLATE_v0_1.md`）。

```yaml
# ══════════ T 时刻冻结（看到结果之前写完）══════════
record_id:      RU-YYYYMMDD-NN
frozen_at:      YYYY-MM-DDTHH:MM+08:00
data_as_of:     YYYY-MM-DD          # 从页面/产物读到的「行情截至」，不凭记忆

question:       ""                  # 一句话研究问题
background:     ""                  # 触发背景：新闻/财报/政策/盘面/他人提问

artifact_ref:
  commit:       ""                  # git rev-parse HEAD 或页面 Build Provenance
  page_blocks:  []                  # 看了哪些区块/产物，如 ["历史题材地图/半导体/事件卡"]
  artifacts:    []                  # 产物文件名 + 版本，如 historical_market_roles_v0_13.json

# ── 条件字段：有候选输出才填；没有就写 NONE / NOT_APPLICABLE + 原因 ──
threec_output:                      # LEAD / CONFIRM / REJECT → 必填
  theme:        ""
  events:       []                  # event_id 或 年份+名称
  securities:   []
  rationale:    ""                  # 原文摘录，不改写
  sources:      []                  # 页面给的链接，不补造
# 负向类型（NO_LEAD / BLOCKED / UI_FRICTION）改填下面两行，并删掉上面的块：
# threec_output:        NOT_APPLICABLE
# output_absent_reason: ""          # 为什么没有输出（必须具体：查了什么、卡在哪）

novelty_self:   ""                  # 新颖 / 已知 / 不确定  ← 三选一
novelty_why:    ""                  # 理由（★ 弱证据，见协议 §5）
worth_researching: ""               # 是 / 否 + 理由

conventional_methods:
  available:     ""                 # 当时有哪些常规方法可用
  actually_used: []                 # 实际用了哪些（Wind/Choice/研报/搜索/记忆/无）

frozen_verdict: ""                  # LEAD / CONFIRM / REJECT / NO_LEAD / BLOCKED / UI_FRICTION
cluster_id:     ""                  # 同题材/同事件/同催化共用同一个 id
```

---

## 填写要点（避免四种最常见的错误）

1. **`data_as_of` 不许写「今天」** —— 必须写页面上显示的「行情截至」。
   两者常常不同（页面 2026-10-30，而你 10-31 才打开）。
2. **`threec_output` 必须是原文摘录** —— 不许把事后理解写回去。当时只看到「题材名 + 年份」
   就只写这些，不要补全成完整论证。
3. **`novelty_self` 只有三选一** —— 不许写「应该是新的」。拿不准就写 `不确定`。
4. **本文件写完后不要再动** —— 事后内容写 `<record_id>.eval.md`；要更正就新建 `amend-NN.md`。

## 负向记录怎么填（同等重要）

| 情形 | `frozen_verdict` | `threec_output` | 必须写清 |
|---|---|---|---|
| 带问题去查，没查到可用线索 | `NO_LEAD` | `NOT_APPLICABLE` | 查了哪些 `page_blocks`、耗时、为什么没结果 |
| 因数据缺失/口径不清中止 | `BLOCKED` | `NOT_APPLICABLE` | 缺什么数据、卡在哪个口径 |
| 页面没能帮上忙 | `UI_FRICTION` | `NOT_APPLICABLE` | 具体哪一步卡住（找不到入口/看不懂/读完仍无结论） |
| 线索让作者**放弃**某方向 | `REJECT` | **必填**（写出被否掉的方向） | 放弃的理由 |

★★ **不许为了让字段「完整」而编造 `theme`** —— 没有输出就是没有输出，这是合法状态。

## 冻结操作（两行命令）

```bash
cd .tmp/real_use/records
# ① 写完正文后立即生成外置摘要（不要把摘要写进正文，那是自引用）
shasum -a 256 RU-20261030-01.md > RU-20261030-01.md.sha256
# ② 事后核对内容是否被改动
shasum -a 256 -c RU-20261030-01.md.sha256
```

★ SHA-256 只能核对「内容与摘要是否一致」，**不能证明创建时间**（摘要可被事后重算）。
需要时间证据时另存当时的检索记录 / 笔记 / 对话历史 / 带日期的 commit。

## 什么时候**不要**建记录

- 只是浏览页面、没有具体研究问题 → 记进 `.tmp/real_use/sessions.md` 的触发量，不建 RU 记录。
- 同一个问题在同一天反复查看 → 合并为 1 条，在 eval 文件里写「重复查看 N 次」。
