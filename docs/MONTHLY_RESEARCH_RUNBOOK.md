# MONTHLY_RESEARCH_RUNBOOK.md — 月度研究更新手册

> | 项目 | 值 |
> |---|---|
> | 性质 | **操作手册（Runbook）** —— ThreeC 1.1 Phase 1.2e |
> | 目的 | 让「每月一次市场研究更新」**不变成负担** |
> | 频率 | **每月一次**，**由用户主导触发**（★ 无自动化定时任务） |
> | 上游 | `docs/MARKET_SNAPSHOT_CONTRACT_v0.3.md` · `docs/MARKET_REGIME_AI_INTERFACE_v0.1.md` · `docs/MARKET_SNAPSHOT_GOVERNANCE.md` |

---

## 0. 为什么需要这份手册

月度更新的输入（`market_regime` + observations + 研究对象状态）**全部依赖离线研究**。
如果不把流程固化成「可执行清单 + 可直接复制的命令」，它会在第 2 或第 3 个月停掉 ——
**工具一旦「要花半天准备」就变成负担，而 Product 做得再漂亮也救不了一个不更新的工具。**

---

## 1. 总览：一次月度更新做什么

```
① 定快照日 ──► ② market_regime（AI draft + 人审）──► ③ 研究对象状态复核
                                                          │
                       ⑥ diff 对照上一期 ◄── ⑤ 装配 + 校验 ◄── ④ 新增观察
                                                          │
                                                    ⑦ 人工签发 CANONICAL（可选）
```

**可自动化**：② 的采集归类（AI 离线）、③④⑤⑥ 的脚本
**不可自动化**：② 的人工审核、⑦ 的 CANONICAL 签发

---

## 2. 操作清单（Checklist）

> 约定：`S=research/current/market_snapshots`，命令均在**仓库根**执行。

### ☐ 步骤 1 · 定快照日

- 快照日 = 本轮研究截止日（**不是**今天，是「研究证据覆盖到哪天」）。
- ★ **PIT 硬约束**：所有 observation / evidence 的日期必须 `<= snapshot_date`。
- ★ 若本轮**未执行新研究**（纯延续），快照日照填，并在步骤 5 用 `--limitation` 说明。

### ☐ 步骤 2 · 产出 `market_regime` draft

1. AI 离线采集 + 按 `MARKET_REGIME_AI_INTERFACE_v0.1.md` §2 规则归类；
2. 写入 `$S/market_regime/<YYYY-MM>.json`（模板参考 `2026-09.json` / `2026-10.json`）；
3. **没有数据源就写 `UNKNOWN` + `unknown_notes` 说明原因** —— **不得编造**（校验 V7 强制）；
4. 人工审核后把 `review.status` 改为 `ACCEPTED`（或 `NEEDS_EVIDENCE` 打回）。

```bash
# 校验 regime draft（必须先过）
python3 $S/scripts/validate_market_snapshot_v0_1.py --file $S/market_regime/<YYYY-MM>.json
```

### ☐ 步骤 3 · 复核研究对象状态

- 若 Research 侧更新了 `research/current/current_candidates.json`（新增/移除候选、阶段变化），
  投影器会自动带出；**不要在本步骤手改快照**。
- 若有用户声明的 `URO-*` 对象，先走人工评审 —— ★ **CANONICAL 快照不得含未评审的 `URO-*`**（校验 V7）。

```bash
python3 $S/scripts/project_cc_to_objects_v0_1.py --all --out /tmp/objects.json
```

### ☐ 步骤 4 · 新增观察（observations）

- 每条观察必须有：`observation_id` / `observation_type` / `date` / `claim` / `evidence_strength` / `direction`。
- ★ **只写事实**（谁在何时发布了什么），不写推断。
- 无新观察 → 空数组 `[]`（合法，不要为凑数而写）。

**★ 关联到研究对象（Lifecycle Tracking 的数据来源）**：

- 若该观察属于某个**当前研究对象**，**必须**填 `linked_object_id`（= `research_objects[].object_id`）。
- 校验 **L1** 会检查它必须存在于同一快照的 `research_objects` 中（悬空关联即 FAIL）。
- 市场级观察（无归属对象）留空即可。

> **为什么重要**：Lifecycle Tracking（`docs/THREEC_1_1_LIFECYCLE_TRACKING_DESIGN.md`）
> **不建独立日志**，而是**从快照序列派生**「某对象的观察时间线」。
> **因此：不填 `linked_object_id`，该对象的生命周期就永远是空的。**
>
> 校验 **L3** 会保证 append-only：同一 `observation_id` 跨快照出现时**内容必须一致** ——
> **一旦写下，不得改写**（改了就触发 FAIL，时间线才不会变成「随时可重写的叙述」）。

### ☐ 步骤 5 · 投影候选 + 装配快照

```bash
# 5.1 从冻结 SA artifact 投影候选（带冻结规则版本守卫）
python3 $S/scripts/project_sa_to_candidates_v0_1.py --all --out /tmp/candidates.json

# 5.2 观察（示例：空）
echo '[]' > /tmp/observations.json

# 5.3 装配（★ --timestamp 固定才能复现）
python3 $S/scripts/build_market_snapshot_v0_1.py \
    --snapshot-date <YYYY-MM-DD> \
    --timestamp "<YYYY-MM-DDTHH:MM:SS+08:00>" \
    --regime $S/market_regime/<YYYY-MM>.json \
    --objects /tmp/objects.json \
    --observations /tmp/observations.json \
    --candidates /tmp/candidates.json \
    --out $S/snapshots/MS-<YYYY-MM-DD>-01.json \
    [--limitation "<本轮未执行新研究轮次的说明>"]
```

> 生成器会**先校验、再落盘**；若晋升 CANONICAL 校验不过，**自动降级为 DRAFT** 并 exit 1。

### ☐ 步骤 6 · 全量校验 + 与上一期对照

```bash
# 6.1 全目录校验（必须 0 失败）
python3 $S/scripts/validate_market_snapshot_v0_1.py

# 6.2 与上一期做 diff（集成测试会打印真实 diff）
./node_modules/.bin/vitest run src/data/marketSnapshot
```

**diff 四层**：环境（`market_regime`）· 对象（`research_objects`）· 候选（`historical_candidates`）· 观察（`observations`）。
★ diff **只说「变了什么」，不说好坏** —— 判断属 Research，不属 Product。

### ☐ 步骤 7 ·（可选）签发 CANONICAL

```bash
python3 $S/scripts/build_market_snapshot_v0_1.py ... --canonical --reviewer "<审核人>"
```

- ★ **只有 `CANONICAL` 允许 Product 消费**；`DRAFT` 不进产品。
- ★ `--reviewer` **必填**（人工审核必过，不得匿名晋升）。

### ☐ 步骤 8 · 提交

```bash
git add -- research/current/market_snapshots
git commit -m "chore(research-1.1): monthly market snapshot <YYYY-MM>"
```

---

## 3. 一次更新的产出物

| 产出 | 路径 |
|---|---|
| regime draft | `$S/market_regime/<YYYY-MM>.json` |
| 快照 | `$S/snapshots/MS-<YYYY-MM-DD>-01.json` |

**不需要**新增的：schema · 校验器 · 生成器 · 投影器（这些是工具，一次建好反复用）。

---

## 4. 质量门（任一不过即不得签发 CANONICAL）

| # | 门 |
|---|---|
| 1 | `validate_market_snapshot_v0_1.py` **0 失败** |
| 2 | JSON Schema（draft-07）校验通过 |
| 3 | `market_regime` 无数据源的维度一律 `UNKNOWN` + 写明原因 |
| 4 | 所有 `date` / `source_date` `<= snapshot_date`（PIT） |
| 5 | 快照内**无** `score` / `ranking` / `probability` / `prediction` / `signal` |
| 6 | 若有候选：`candidates_source.rule_set_version` 与冻结 SA 一致 |
| 7 | 每个候选的 `current_object_id` 都能在 `research_objects` 中找到（V8c） |

---

## 5. 常见坑（都是实际踩过的）

| 坑 | 说明 |
|---|---|
| **`--timestamp` 不固定** | `--check` 会因时间戳不同而报「不一致」。要复现必须固定 `--timestamp` |
| **忘了 `--limitation`** | 纯延续快照若不说清楚，读的人会以为执行了新研究 |
| **想给 UNKNOWN 维度「凑」证据** | **禁止**。缺证据是合法状态；校验 V7 会要求写明「为什么不知道」 |
| **把当前行情写进历史 artifact** | **禁止**。快照是独立 artifact，**不进** `exports/timeline_export_v1.json` |
| **以为候选列表不需要关联** | 契约 v0.3 起每项**必填** `current_object_id`；缺了整份列表不可用（v0.2 的真实缺陷） |

---

## 6. 当前缺口（诚实记录）

| 缺口 | 影响 |
|---|---|
| `market_regime` **仍无数据源** | 四维只能写 `UNKNOWN`；需 B 路径（AI 调研 + 挂来源）或 C 路径（接低频公开统计） |
| 研究对象状态**仍依赖人工更新 `current_candidates.json`** | 该步骤尚未脚本化；候选新增/阶段变化仍需研究侧动手 |
| 尚无「月度更新提醒」 | ★ **按用户要求不建自动化定时任务**；频次由用户主导 |

---

*Runbook · ThreeC 1.1 Phase 1.2e · 2026-10-06*
