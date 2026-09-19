# R01-02 数据质量收口 v0.1

> **性质**：对 R01-02 Canonicalization 报告中**已明确记录**的遗留问题做小范围收口。
> **边界**：未改 Schema / Protocol / Research Model / CMTR / 历史研究结论 / Campaign 设计；
> 未新增 Campaign；未启动 R01-03；未刷新 Structural Analogy / Time Observation。
> **结论**：**未做任何数据性修改** —— 两处遗留均判为「口径差异 / 归属 caveat」，非数据错误；
> 以 **canonical 注记** 形式收口（写入 `campaigns.research_notes`）。

---

## 1. E056 归属核查

### 1.1 原始内容（intake）

```
evidence_id      R01-SEMICONDUCTOR-E056
claim            大基金一期(2014, 约1387亿, 芯片制造) / 二期(2019, 2041.5亿, 设备与材料上游)
                 / 三期(2024-05-24, 3440亿, 先进制造/高端设备/AI 芯片) 三阶段
event_date       2024-05-24        ← 三期成立日
evidence_date    2026-02-10        ← 中国金融新闻网（金融时报）回顾性文章
temporal_relation subsequent       ← 正确（发布日 2026-02-10 确为事后）
independence_group IG-JRSB
evidence_role    supporting
description      「…用于交叉核对大基金三期的规模与投向，**提升 002 / 008 的证据独立性**」
```

### 1.2 为什么被绑定到 `C-2020-SEMI-EQUIPMENT`

Worker 在 `evidence_ids` 中同时列入 **002 与 008**（其 `description` 已自述该意图）。
在 canonical 化时按「1 evidence : 1 campaign」（`validate_batch_research` 强制）做唯一归属：
`E056` → **002**（`E035` 归 007）。

### 1.3 是否存在更正确的归属

| 候选 | 能否承载 | 理由 |
|---|---|---|
| **002**（当前） | ✅ | 002 的驱动即「大基金二期（2019-10-22 成立、投向设备与材料上游薄弱环节）」—— 见 002 的 `start.alternative_dates`；E056 是该事实的**第三个独立来源** |
| 008（三期） | ❌ | **RESEARCH_ONLY，不入 `campaigns` 表**，无法承载 |
| 007 | ❌ | 起点 2024-09-24 **晚于** E056 的 event_date（2024-05-24）；机制为存储涨价，非大基金 |

→ **002 是唯一在 canonical 层成立的归属**。

### 1.4 是否违反既有规则

**否。** 逐条核验：

| 规则 | 结果 |
|---|---|
| `validate_db.check_evidence_temporal_present` | ✅ `temporal_relation = subsequent`（非空且合法） |
| `validate_db.check_retrospective_not_contemporaneous` | ✅ **该规则仅约束 `contemporaneous`**；E056 为 `subsequent`，不触发 |
| `validate_db.check_event_temporal_consistency` | ✅ 仅作用于 `campaign_events`，不作用于 evidence |
| `validate_batch_research`（1 evidence : 1 campaign） | ✅ 仅绑定 002 |
| `historical_campaign_validation_v1.md §4.3` | ✅ 事后证据已正确标注，未伪装为同期催化 |

### 1.5 Export 是否受影响

**否。** 实测：

```
canonical exports/timeline_export_v1.json  →  无 evidence_ids / evidences 字段（字段级差异仅 generated_at + source_commit）
research/research/batch/auto_2018_2025_batch_manifest.json  →  含 evidence_ids（E-SEMI-56 列于 C-2020-SEMI-EQUIPMENT）
```

即：**canonical Export 完全不携带 evidence 归属** → 不受影响；
Research 侧 batch manifest 如实反映该归属（预期行为）。

### 1.6 最终处理

> **保留绑定 002 + canonical 注记。**

已写入 `C-2020-SEMI-EQUIPMENT.research_notes`（标记 `【R01-02 数据质量收口 v0.1】`）。
**未修改** `event_date` / `temporal_relation` / `evidence_role`（那属研究结论）。

★ **已知 caveat（unresolved）**：E056 的 `event_date`（2024-05-24，三期）落在本 Campaign 窗口
（2020-07-16~2021-09-30）之外 —— 属「多事实证据取了三期日期」的口径问题，**保留待后续复核轮次**。

---

## 2. E-SEMI-29 / E-SEMI-47 / E-SEMI-48

三条 `validate_db` WARNING（`evidence-temporal-mislabel`）逐条核查：

| # | intake | event_date | temporal_relation | role | 绑定 Campaign | Campaign end | 来源 |
|---|---|---|---|---|---|---|---|
| 1 | `E029` | 2020-12-28 | contemporaneous | **context** | `C-2019-SEMI-LOCALIZATION` | 2020-09-30 | 第一财经年终盘点《半导体的2020：13只个股翻番，全年先扬后抑》 |
| 2 | `E047` | 2022-12-29 | contemporaneous | supporting | `C-2022-SEMI-DOWNTURN` | 2022-10-12 | 证券时报网《半导体行业主动去库存或将开启》（年终行业复盘） |
| 3 | `E048` | 2022-10-31 | contemporaneous | **context** | `C-2022-SEMI-DOWNTURN` | 2022-10-12 | 同上（2022-10 美国再次收紧对华半导体限制） |

### 逐项检查结果

| 检查维度 | 结果 |
|---|---|
| **evidence 日期** | 三条的 `event_date` 均**确为**其记载事件之日（年终盘点 / 出口管制），无录入错误 |
| **`temporal_relation`** | 三条均标 `contemporaneous`（**年份级**口径：2020 年 / 2022 年） |
| **lifecycle 起止** | 与 Campaign 的 `end_date` **一致**（001 RETRACEMENT→2020-09-30；009 DECLINING→2022-10-12）—— **lifecycle 无错** |
| **`campaign_date_observations`** | 与 lifecycle / `end_date` 一致，**无错** |
| **source 日期** | 与 `evidence_date` 一致（E047/E048 同源 `S029`，`same_origin = true`） |
| **原始 Intake Package** | 三条标注与 Package **完全一致**（非导入错误） |

### 判定

> ## **口径差异，非数据错误。**

- Package 的 `temporal_relation` 采用「**年份级**同期」口径（证据所属年份 = Campaign 所属年份）；
- `validate_db` 采用「**窗口级**」口径（证据日期不得晚于 `campaign.end_date`）；
- 三条中 **2 条为 `context`**（E029 / E048），**未**被用作同期催化；E047 虽为 `supporting`，
  但其 claim 属**行业机制识别**（库存周期 + 需求收缩），非启动/主升催化；
- E048 的 event（2022-10-31 出口管制）距 `end_date` **仅 19 天**，属本轮下行的尾部政策因素。

### 最终处理

> **保留现状（3 条 WARNING 保留）+ canonical 注记。**

**未修改** `temporal_relation`。理由：
1. 修改 `temporal_relation` = **变更研究结论**（超出本轮授权）；
2. 会使 **canonical DB 与 intake Package 分歧** —— 破坏 provenance 一致性（Package 是冻结交付物，其 `checksums.sha256` 已锁定）；
3. 该检查本身是 **WARN 而非 FAIL**，`validate_db` 结果仍为 **PASS**；
4. 属「无法可靠判断 → 保留现状并明确记录为 unresolved」。

已写入 `C-2019-SEMI-LOCALIZATION.research_notes` 与 `C-2022-SEMI-DOWNTURN.research_notes`
（标记 `【R01-02 数据质量收口 v0.1】`）。

---

## 3. 本轮实际数据变更

> **零数据性变更。** 仅追加 canonical 注记。

| 表 | 新增行 | 删除行 | 修改行 | 修改字段 |
|---|---:|---:|---:|---|
| `campaigns` | 0 | 0 | **3** | **仅 `research_notes`** |
| 其余 13 张表（themes / rules / annual_reviews / evidences / sources / securities / events / 全部桥表 / phases / CDO） | 0 | 0 | **0** | — |

**26 个 Canonical Campaign 未发生任何无关变化**（仅 3 个的 `research_notes` 文本追加）。

| 文件 | 差异 |
|---|---|
| `exports/timeline_export_v1.json` | **仅 `generated_at` + `source_commit`**（内容逐字段一致） |
| `research/research/batch/auto_2018_2025_batch_manifest.json` | 3 × `research_notes` + 元数据 |
| `research/research/batch/conflicts.json` | 元数据 |

---

## 4. 验证结果 → 全部 PASS

| 检查 | 结果 |
|---|---|
| `validate_db` | **PASS**（**3 条 WARNING —— 与收口前完全相同，无新增**） |
| `validate_timeline_export` | **PASS** |
| `validate_batch_research` | **PASS** |
| `validate_promotion_manifest` | **PASS** |
| `check_doc_schema_consistency` | **PASS** |
| `validate_current_research` | **PASS** |
| `validate_monorepo_integrity` | **PASS** |
| `validate_historical_research_intake --check` | **PASS** |
| `test_validate_historical_research_intake.py` | **PASS（44 / 44）** |
| `refresh_current_research --check` | **PASS** |
| R01-01 / R01-02 Intake Validator | **PASS / PASS** |

**Export 与 DB 一致**：campaigns 26 = 26 · research_candidates 10 · rules 6 · events 86 · securities 129 ·
`timeline_export_version = "1.0"`（未变）。

---

## 5. ★ 附带事件：`.git` 目录损坏与修复（与本轮任务无因果关系，但必须记录）

**发生**：在执行一次仓库内部对比时使用了 `git stash --keep-index`，该命令被超时中断（SIGTERM）。
中断触发了一次未完成的 `git maintenance`，导致：

| 受损项 | 现象 |
|---|---|
| `.git/refs/` | **整个目录缺失** → `git` 报 `fatal: not a git repository` |
| `.git/objects/pack/*.pack` | **pack 文件丢失**（仅剩 2 个孤立 `.idx`）→ `fatal: bad object HEAD` |
| `.git/objects/maintenance.lock` / `bitmap-ref-tips_*` | 中断残留 |
| `.git/logs/*` | 含 2 条指向已不存在对象的 reflog 条目 |

**修复步骤**（全部可验证）：

1. **先备份**工作区 4 个改动文件到仓库外临时目录（`cycle_research.db` / `timeline_export_v1.json` /
   `auto_2018_2025_batch_manifest.json` / `conflicts.json`）—— 确认字节数后继续
2. 删除中断残留：`maintenance.lock` · `bitmap-ref-tips_*`
3. 重建 `.git/refs/{heads,tags,remotes/origin}`，并按 **reflog 最后已知 SHA** 写回：
   - `refs/heads/main` = `9e694f6d152cb53fa7cfe97bceebb7dbf3653d79`
   - `refs/remotes/origin/main` = 同上（与 `FETCH_HEAD` 一致）
   - `refs/heads/migration-backup-pre-monorepo` = `d3795002…`
4. 从远端恢复对象库：`git fetch origin --tags --force`（→ `pack-b02b88b8…`，13.3 MB）
5. 清理 2 个孤立 `.idx` + 失效 `multi-pack-index`；移除 2 条坏 reflog 条目
6. **校验**：`git fsck` → **exit 0，无任何输出** ✓

**修复后状态**：`HEAD = 9e694f6` · `branch = main` · `a/b = 0/0` · 工作区 4 个改动完好 · `git log` 正常。

**结论**：**未丢失任何提交、未丢失任何工作区改动**；远端（GitHub）始终保有完整历史。

★ **操作教训（写入项目记忆）**：在含大二进制文件（15 MB SQLite）的仓库中，
**不要使用 `git stash`** 做对比；对比 HEAD 版本应直接用 `git show HEAD:<path>` 读入临时文件。
本仓库已启用 `git maintenance`（会在后台触发 `repack`/`pack-refs`），
`stash` 会与之竞争并可能留下未完成状态。

---

## 6. 遗留（unresolved，**未在本轮处理**）

| # | 项 | 说明 |
|---|---|---|
| 1 | `E056` 的 `event_date` 与 `C-2020-SEMI-EQUIPMENT` 窗口不符 | 多事实证据取了三期日期；保留绑定 002 + 注记 |
| 2 | `E029` / `E047` / `E048` 的 `temporal_relation` 口径 | 年份级 vs 窗口级；3 条 WARNING 保留 + 注记；建议后续统一口径 |
| 3 | `CF006`（2024-09-24 后市场 Beta） | 仍 UNRESOLVED |
| 4 | `CF008`（2017 显卡/矿机归属） | 仍 UNRESOLVED |
| 5 | 别名 taxonomy 缺口 | 未扩展 |
| 6 | `C-2016-PANEL-CYCLE` 证据偏薄 | 3 ev / 2 IG |
| 7 | Structural Analogy / Time Observation | 未刷新 |
