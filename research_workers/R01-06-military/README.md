# R01-06-military — ThreeC Historical Research Worker Workspace

> **task_id**: `R01-06` · **research_round_id**: `R01` · **status**: `PREPARED_NOT_STARTED`
> **workspace_version**: `0.1` · **source_threec_commit**: `2153f6d83b7481300696ab73d792e9e53aa31a07`

---

## 1. 这是什么

这是 **ThreeC Historical Universe Expansion** 的**独立 Research Worker Workspace**。

它对应 `R01` 轮次中的任务 **`R01-06`**：军工（含航空装备、航天装备、船舶、兵器、军工电子、卫星导航）

---

## 2. 可以脱离 ThreeC 主仓库移动

> 本 Workspace **完全自包含**（`standalone = true`）。
> 它不依赖 ThreeC 主仓库、不依赖 SQLite、不依赖 Product、不依赖网络。

可以直接整体移动到一个新的独立工作空间，交给 Research Agent 执行。

---

## 3. Research Agent 的职责边界

**只负责生产 `Research Intake Package`。**

**不负责 Canonicalization。**

最终唯一正式交付位置：

```text
05_OUTPUT/
```

---

## 4. 完成后由 ThreeC Agent 执行

```text
05_OUTPUT/（Research Intake Package）
        ↓
ThreeC Agent
        ↓
Review（八种审查结果）
        ↓
Dedupe（cross-task）
        ↓
Merge
        ↓
Macro Theme Canonicalization   ← ★ CMTR v1
        ↓
Campaign Decision              ← ★ Research Model v1.0 §5 + Independence Gate Q1–Q5
        ↓
DB Import
        ↓
Validation（validate_db）
        ↓
Coverage Audit
        ↓
Export
```

---

## 5. 明确声明

> ## 本 Workspace 本身**永远不是** Canonical Research DB。

- 它**不含** SQLite / DB dump / `src/` / `exports/timeline_export_v1.json` / Product 代码。
- 它**不能**修改 ThreeC canonical data。
- 它产出的东西是**研究候选**，不是历史事实。

---

## 6. 目录结构

```text
R01-06-military/
├─ README.md                          ← 本文件
├─ workspace_manifest.json            ← 自描述（standalone / 权限边界）
├─ workspace_checksums.sha256         ← 关键输入文件校验（规则版本一致性）
│
├─ 00_TASK/
│  ├─ TASK_BRIEF.md                   ← 本任务的任务书
│  └─ R01_TASK_MANIFEST_CONTEXT.json  ← **READ_ONLY REFERENCE**（全部 6 个 task）
│
├─ 01_PROTOCOL/
│  ├─ HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md   ← R00 通过版本（字节一致）
│  ├─ historical_research_intake.schema.json        ← R00 通过版本（字节一致）
│  └─ WORKER_OPERATING_RULES.md                     ← Worker 运行边界
│
├─ 02_BASELINE/
│  ├─ HISTORICAL_UNIVERSE_BASELINE_SNAPSHOT.md      ← READ_ONLY BASELINE SNAPSHOT
│  └─ KNOWN_TAXONOMY_AND_OVERLAP_NOTES.md
│
├─ 03_REFERENCE/
│  ├─ RESEARCH_MODEL_V1_REFERENCE.md
│  ├─ CAMPAIGN_VALIDATION_REFERENCE.md
│  ├─ POINT_IN_TIME_REFERENCE.md
│  ├─ CAMPAIGN_SEPARATION_REFERENCE.md
│  └─ STRUCTURAL_ANALOGY_CONTEXT.md
│
├─ 04_RESEARCH/
│  └─ README.md                       ← 临时研究区（不是交付结构）
│
├─ 05_OUTPUT/
│  └─ README.md                       ← ★ 唯一正式交付位置
│
└─ tools/
   ├─ validate_historical_research_intake.py
   ├─ test_validate_historical_research_intake.py
   └─ fixtures/minimal_valid_package/  ← 合成夹具（不是研究数据）
```

---

## 7. 校验

```bash
# 校验交付（默认路径即 05_OUTPUT）
python tools/validate_historical_research_intake.py 05_OUTPUT

# 基础设施自检（schema / task context / workspace manifest / checksums / 确定性）
python tools/validate_historical_research_intake.py --check

# 自测（33+ tests，无需网络 / SQLite / Product）
python tools/test_validate_historical_research_intake.py

# 列出 24 项检查
python tools/validate_historical_research_intake.py --list-checks
```

退出码：`0` = 无 FAIL；`1` = 存在 FAIL。

---

## 8. 规则版本一致性

`workspace_checksums.sha256` 记录了 Protocol / Schema / Task Context / Reference / Validator 的 SHA256。
**校验器会在 `--check` 时验证它们**，确保本 Workspace 使用的是与 R00 相同的规则版本。

---

## 9. 任务状态

**`PREPARED_NOT_STARTED`** —— 本 Workspace 已准备就绪，**尚未开始任何研究**。

启动需**单独授权**。

---

## 10. 只读参考

`00_TASK/R01_TASK_MANIFEST_CONTEXT.json` 是 **READ_ONLY REFERENCE**：
它保留全部 6 个 task，让 Research Agent 能看到其它 Task 的 `known_overlap` / `known_ambiguity`。

> **不得修改 ThreeC 主仓库的 manifest。**
> 本副本只用于理解任务边界。

---

## 11. 自包含性（Portability）

本 Workspace 已经过**真实搬移测试**：整体复制到 ThreeC 仓库**之外**的目录后，

```bash
python tools/test_validate_historical_research_intake.py   # 36 passed
python tools/validate_historical_research_intake.py --check # PASS（24 checks, 0 FAIL）
python tools/validate_historical_research_intake.py 05_OUTPUT
python tools/validate_historical_research_intake.py tools/fixtures/minimal_valid_package
```

**全部可正常运行** —— 不依赖 ThreeC 主仓库、不依赖 SQLite、不依赖 Product、不依赖网络。

### 路径引用规则

| 类型 | 处理 |
|---|---|
| **Worker 操作说明** | 一律 **workspace-relative**（`05_OUTPUT/` · `tools/` · `01_PROTOCOL/` · `02_BASELINE/` · `03_REFERENCE/`） |
| **禁止事项中的 ThreeC 路径** | 仅作 **REFERENCE / 来源说明**（说明为什么本 Workspace 必须隔离），**不是** Worker 需要访问的路径 |
| **Protocol 原文中的路径** | **保留原样**（协议为字节一致的只读副本，不因路径而改写） |

### 为什么这不影响使用

本 Workspace 中**不存在** `research/` · `src/` · `exports/` · `*.db` · `node_modules/` ·
`package.json`。因此 Protocol / Manifest 中提到的那些 ThreeC 侧路径
**在本 Workspace 内物理上不可达** —— 隔离由**结构**保证，不只靠文字约束。
