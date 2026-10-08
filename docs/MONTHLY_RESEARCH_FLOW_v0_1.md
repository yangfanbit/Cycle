# MONTHLY_RESEARCH_FLOW_v0_1.md

> | 项目 | 值 |
> |---|---|
> | 性质 | **月度研究刷新流程**（`PROJECT_STATE §7` 的 **1.2e**） |
> | 入口 | `python research/scripts/monthly_refresh.py` |
> | 配套 | `archive_current_round.py`（不可变归档）· `refresh_current_research.py`（机械动作 + 校验 + diff） |
> | 日期 | 2026-10-08 |

---

## 〇、为什么需要它（实测暴露）

| # | 实测问题 |
|---|---|
| 1 | `0479661` 那一轮**加了候选（`last_updated=2026-10-07`）却没推进 `snapshot_date`（仍 2026-09-15）** → 契约检查 **FAIL** |
| 2 | 检查器**存在但不在任何自动链路里** —— 产品照样消费，**无人发现** |
| 3 | 数据集**原地覆盖** —— 上一轮内容**只能靠 git 找回**（现已建归档） |
| 4 | 层间不同步：候选层 09-15 vs 环境层 10-06，**差 21 天而无人报警** |

> ★ 本流程把「一轮」串成**一条可执行、可失败、可追溯**的路径。

---

## 一、两种动作，不要混

| 类型 | 谁做 | 内容 |
|---|---|---|
| **机械动作** | **脚本** | 校验 · diff · 归档 · 报告 |
| **研究判断** | **离线研究（AI 或人）** | 检索证据 · 更新候选 · 判定阶段 · 推进快照日 |

★ **脚本不做研究判断，也不代替研究判断。**
`current_candidates.json` 的**内容**必须由离线研究准备好。

---

## 二、一轮的完整清单

### A · 研究侧（离线，**本流程不代替**）

| # | 动作 | 硬约束 |
|---|---|---|
| A1 | 检索新证据 | ★ **每条证据的 `source_date` / `event_date` ≤ 新快照日**（Temporal Firewall） |
| A2 | 记录来源 | 每条证据须有 `source_url` / `source_title` / `source_type` / `evidence_strength` |
| A3 | 更新候选的 `evidence` | 不编造；检索不到就**留空** |
| A4 | 更新 `phase_evidence` / `narrative_types` / `research_questions` | 同上 |
| A5 | **推进 `snapshot_date`** | ★★ **只要新增/修改了任何内容，就必须同步推进** —— 上一轮正是漏了这一步 |
| A6 | 同步推进各候选自身的 `snapshot_date` | 必须 **≤** 数据集快照日 |
| A7 | 写入 `current_candidates.json` | 用 LF；不手改 JSON 缩进以外的格式 |

### B · 机械侧（跑脚本）

```bash
# ① 一条命令走完：校验 → diff → 归档 → 报告
python research/scripts/monthly_refresh.py

# ② 若需要把已准备好的内容写入 canonical（显式）
python research/scripts/monthly_refresh.py --write-canonical
```

★ **校验失败即停** —— 不归档、不 diff。最常见原因：**内容改了但快照日没推进**。

### C · 收尾

| # | 动作 |
|---|---|
| C1 | `git add` 显式路径 → commit（commit message 写清本轮**真实变化**，不含记账变更） |
| C2 | 若产品侧基线受影响（如快照日变化影响 `stalenessDays`），同步更新测试 |
| C3 | 若涉及 Research artifact 升版（SA / 导出），走既有升版链路 |

---

## 三、★ 读 diff 时要小心的一处

`refresh_current_research.py` 的 `candidate_fingerprint` 对**整条记录**取指纹 ——
**`snapshot_date` / `last_updated` 变了也会算「UPDATED」**。

> 实测：2026-10-08 那轮报 `UPDATED 5`，但**真实内容变化只有 1 个对象 + 1 条证据**。

★ **看真实变化**：排除 `snapshot_date` / `last_updated` 后再比对。
（已知 limitation，记录在案；**未擅自扩展状态机**。）

---

## 四、归档（不可变）

```
research/current/candidates_archive/
    current_candidates_<snapshot_date>.json     ← 每轮原样副本
    archive_index.json                          ← {日期, 候选数, sha256, 归档时间, 来源}
```

★ **不可变纪律**：同一 `snapshot_date` 已存在且内容不同 → **拒绝**（需 `--force`）。
★ 这条守卫**第一次运行就抓到了契约违规本身**（同一日期下两种内容）。

---

## 五、已知未做（诚实记录）

| # | 缺口 |
|---|---|
| 1 | **四层 diff**（环境 `market_regime` / 对象 `research_objects` / 候选 `historical_candidates` / 观察 `observations`）—— 现只有 candidate 级（`PROJECT_STATE §7` 的 **1.2d**） |
| 2 | **层间时间一致性检查**（候选层比环境层旧 N 天时应报警） |
| 3 | `market_regime` / `observations` 的填报仍无脚本辅助 |

---

*流程 v0_1 · 2026-10-08*
