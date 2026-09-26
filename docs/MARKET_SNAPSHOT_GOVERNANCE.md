# MARKET_SNAPSHOT_GOVERNANCE.md

> | 项目 | 值 |
> |---|---|
> | 文件性质 | **治理规则（GOVERNANCE）** —— Phase 0 草案，**不是实现** |
> | 日期 | 2026-09-25 |
> | 依赖 | `docs/THREEC_1_1_MARKET_SNAPSHOT_ARCHITECTURE.md` · `docs/MARKET_SNAPSHOT_CONTRACT_v0.2.md` |
> | 适用范围 | Market Snapshot · Correction Record · Import Record · Promotion |
> | 状态 | **等待下一阶段确认** |
>
> 治理只回答一件事：**谁有权在什么时候改什么，以及必须留下什么痕迹。**
> 一切修改**必须可追踪**；一切结论**必须可证伪**。

---

## A. 历史纠错治理

> 解决：「历史行情发现错误怎么办？」

### A.1 流程

```
Correction Intake  →  Evidence Collection  →  Human Review  →  New Artifact Version  →  Product Read Only
```

### A.2 Correction Record（`CR-*`）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `correction_id` | `CR-*` | ✅ | 纠错记录 id |
| `target.artifact` | `timeline_export_v1` / `structural_analogy` / `time_observation` | ✅ | 目标 artifact |
| `target.object_kind` | `campaign` / `research_candidate` | ✅ | — |
| `target.object_id` | `C-*` / `RC-*` | ✅ | — |
| `target.field` | string | ✅ | 目标字段 |
| `current_value` | any | ✅ | 现值 |
| `proposed_value` | any | ✅ | 建议值 |
| `reason` | string | ✅ ★ | **必填**：为什么认为它是错的 |
| `evidence` | `[{source_type, date, claim}]` | ✅ ★ | **必填**：支撑证据 |
| `reported_by` / `reported_at` | string / ISO | ✅ | 报告者与时间 |
| `review.status` | `PENDING` / `ACCEPTED` / `REJECTED` / `NEEDS_EVIDENCE` | ✅ | 评审状态 |
| `review.reviewer` / `review.decided_at` / `review.rationale` | string / ISO / string | ❌ | 评审留痕 |
| `blast_radius` | `{affects_lifecycle, affects_driver, affects_sa, affects_to, estimated_sa_changes}` | ❌ | 影响面评估 |
| `effective_revision` | string | ❌ | 生效的 artifact revision |

### A.3 Evidence（必填）

> **`evidence` 必填。** 无证据的纠错请求**不得**进入 `ACCEPTED`。

- 证据必须带 `source_type`（Tier 1/2/3 口径）与日期。
- 证据日期**不得晚于**该纠错对应的研究时点（PIT 约束）。

### A.4 Review（人工评审）

| 判定 | 含义 |
|---|---|
| `ACCEPTED` | 接受，进入「新建 artifact 版本」 |
| `REJECTED` | 拒绝，记录理由 |
| `NEEDS_EVIDENCE` | 证据不足，退回补证（**不得**默认接受） |

> 涉及**生命周期 / 驱动 / SA 结论**的纠错**必须**人工评审；**禁止**自动接受。

### A.5 Version（新建版本，不覆盖）

> **禁止直接修改历史 artifact。**

```
旧 artifact（逐字节保留）
      +
CR-*（reason + evidence + review）
      ↓
新 artifact revision（新文件）
```

- 修正**只**通过「新建 artifact revision + 纠错台账」生效。
- 原始值**永久保留**（可追溯）。
- **内容修正 ≠ 契约版本升级**（见 Contract §6）。

### A.6 与研究结论的隔离

> 纠错**只**修正**事实层**（日期 / 证据 / 归属）。
> 若纠错会**改变研究结论**（如 `STRUCTURAL_PARTIAL → STRUCTURAL_SUPPORTED`），
> **必须**走「新 SA round」重跑冻结规则，**不得**手工改结论。

---

## B. 新行情治理

> 解决：「新行情如何合法地进入历史体系？」

### B.1 流程

```
Observation  →  Research Candidate  →  Lifecycle Tracking  →  Campaign Promotion
```

### B.2 Observation（观察）

| 要求 | 说明 |
|---|---|
| 带日期 | `date` 必填 |
| 带来源 | Tier 1/2/3 口径 |
| 三分离 | 事实（`claim`）/ 解释 / 推测 必须分开 |
| PIT | `date ≤ snapshot_date`；`AFTER_SNAPSHOT` 被隔离，不参与判断 |

### B.3 Research Candidate（`RC-*`）

| 要求 | 说明 |
|---|---|
| 进入条件 | 主题可识别 + 证据齐 + 日期有依据 |
| 命名 | `RC-*`（**不得**用 `C-*`） |
| `research_status` | `PROVISIONAL` / `CONFLICT` / `INSUFFICIENT`（**无**生产 `status`） |
| 位置 | 只在 `research_candidates[]`，**不进** `campaigns[]` |

> ★ **Research Candidate 不能直接成为 Campaign。**

### B.4 Lifecycle Tracking（生命周期追踪）

| 要求 | 说明 |
|---|---|
| **append-only** | 每次观察**追加**，**不得**回改历史观察 |
| 记录 | `{observed_at, stage, note, evidence_refs}` |
| **禁止 look-ahead** | 不得用未来信息回填早期阶段 |
| 诚实空态 | 阶段未知写 `UNKNOWN`，**不伪装** |

### B.5 Campaign Promotion（晋升）

**进入条件（全部满足）**：

| # | 检查项 |
|---|---|
| 1 | 存在 A 股市场侧证据（商品价格 ≠ A 股市场侧证据） |
| 2 | Beta Level 可判定（0–3） |
| 3 | `start / peak / end` 四态可判定（EXACT / WINDOW / ALTERNATIVE / NULL） |
| 4 | 无 look-ahead（全部证据 `date ≤ 晋升日`） |
| 5 | `macro_theme` 合法（CMTR v1 既有 root） |
| 6 | **人工确认通过** |

**晋升结果**：

- 通过 → **新建** `C-*`（**不覆盖**任何既有 Campaign）。
- 不通过 → **保持 `RC-*`**（合法结果），并写明还缺什么口径的数据。

---

## C. 人工审核节点

> 以下 **4 个节点必须人工确认**，**不得**由脚本 / AI 自动通过。

| # | 节点 | 位置 | 必须人工确认的内容 |
|---|---|---|---|
| **C-1** | **历史结构确认** | Market Snapshot 的 `historical_candidates` 生成后 | 历史结构对应是否成立、是否值得继续研究（**不是**打分，是取舍） |
| **C-2** | **Correction 生效** | 纠错评审（§A.4） | `ACCEPTED` / `REJECTED` / `NEEDS_EVIDENCE`；涉及结论的纠错必须重跑规则 |
| **C-3** | **Campaign Promotion** | §B.5 | RC → Campaign 的晋升（新建，不覆盖） |
| **C-4** | **Artifact Version 替换** | 新 revision 生效时 | 旧版本 → 新版本的替换决定（含 `supersedes` 链） |

### C.1 禁止自动通过

| ❌ 禁止 | 说明 |
|---|---|
| AI 自动确认结构相似 | 结构判定只由冻结 SA v0.3 + 人工确认 |
| AI 自动 Promotion | 晋升必须人工闸门 |
| 脚本自动 `ACCEPTED` 纠错 | 评审必须人工 |
| 自动评分 / 排名 | 与项目初心冲突 |

### C.2 留痕

> 每个节点的决定**必须**写回对应 artifact：
> `human_review` / `review.*` / `import_record.promotion_gate` / `supersedes`。
> **无留痕 = 未发生。**

---

## D. 治理红线（汇总）

- ❌ 禁止直接修改历史 artifact
- ❌ 禁止 Research Candidate 直接成为 Campaign
- ❌ 禁止 `reason` 或 `evidence` 缺失的纠错被接受
- ❌ 禁止自动 Promotion / 自动结构确认 / 自动评分 / 自动排名
- ❌ 禁止 Product 消费非 `CANONICAL` 的 artifact
- ❌ 禁止用未来信息（look-ahead）回填历史
- ❌ 禁止把 `UNKNOWN` / `NOT_AVAILABLE` 当作 `NO`

---

*治理文档结束 · Market Snapshot Governance · 2026-09-25 · 等待下一阶段确认*
