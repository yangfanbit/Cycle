# 用户授权转录记录 —— R02-05 canonicalization

> 本文件**只转录实际已发生的授权**，不扩展其适用范围，不新增研究判断，不虚构引用。

---

## 授权事项

**对象**：`research/intake/packages/R02-05` 的 **3 条 `ACCEPT_WITH_CHANGES`** 候选的
canonicalization（写入 DB 与下游 artifact）。

| candidate_id | 对应 canonical_id |
|---|---|
| `R02-COMM-001` | `C-2017-COMM-5G-SPECTRUM` |
| `R02-MEDIA2-001` | `C-2021-MEDIA-METAVERSE` |
| `R02-POWEROP-001` | `C-2023-POWEROP-THERMAL` |

**粒度裁定**（同一轮确认）：Campaign 粒度 = **机制段**；
长周期对象**保留不拆分**，在机制段对象的 `research_notes` 中标注所属长周期。
依据：`docs/DECISION_CAMPAIGN_GRANULARITY_2026-10-13.md`。

## 授权来源

- **日期**：2026-10-13
- **形式**：用户在与 ThreeC Agent 的对话中逐项确认：
  ① 「Campaign 粒度 = 机制段（长周期也标注）」
  ② 「**3 条 ACCEPT 现在写库**」
  ③ 「SF-a 立刻修」
- **原始审查裁定**：`research/intake/reviews/R02-05_verdicts_v0_1.json`
  （3 `ACCEPT_WITH_CHANGES` + 4 `DEFER`；`role_separation_declaration` 符合协议 §3）
- **粒度阻塞**：该裁定文件 `blocking_condition` 记录了「Campaign 粒度未定义」的协议层阻塞；
  由上述裁定 ① 解除。

## ★ 授权范围（**不得外推**）

本授权**仅**覆盖上表 3 条候选的 canonicalization 及其直接下游刷新
（lifecycle / export / SA / 快照重出 / 行情补抓）。

**明确不在范围内**：

- 该包的 **4 条 `DEFER`**（`R02-COMM-002` · `R02-POWEREQ-001` · `R02-POWEREQ-002` · `R02-POWEROP-002`）
  —— 未获入库授权，**仍未处置**。
- `R02-PHARMA-002`（G）与 `R02-PHARMA-003`（H）—— 与本授权无关，**未裁决**。
- `MS-2026-10-13-01` 的**签发** —— ★ 本文件**不**构成对该快照签发的授权
  （签发的批准见 `docs/SNAPSHOT_SIGNING_PREREQUISITES_v0_1.md` 与后续签发记录）。

## 授权留痕的补录说明

★ 该授权发生于 2026-10-13 的对话，**此前未落盘**（`R02-05_verdicts_v0_1.json`
的 `review_ref` 仍为 `None` —— **本文件不替它补写**，避免把转录伪装成原始引用）。

★ 本文件于 2026-10-14 创建，作为该授权的**可追溯转录记录**。
`decided_at` 语义 = **2026-10-13**（授权发生日），非本文件创建日。

---

*转录记录 · ThreeC Agent · 2026-10-14 · 无新研究判断*
