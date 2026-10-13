# 快照签发审阅材料 —— `MS-2026-10-13-01`（v0.2 · 含候选级差异）

> 状态：**待人工审核** · ThreeC Agent · 2026-10-14（v0.1 为 2026-10-13，本轮补候选级逐条比较）
> ★★ **本文不代表「允许签发」**。签发是**产品负责人的人工决定**。
> ★ 本轮**未修改任何快照状态、未签发**。

---

## 一、两份快照的来源与版本绑定（实测）

| 项 | `MS-2026-10-12-01`（**CANONICAL**） | `MS-2026-10-13-01`（**DRAFT**） |
|---|---|---|
| `candidates_source.artifact` | `…_v0_12.json` | **`…_v0_13.json`** |
| `artifact_version` | **0.12** | **0.13** |
| `rule_set_version` | `structural-analogy-ruleset-v0.3` | **同**（规则集**未变**） |
| `research_objects` | 6 | 6 |
| `observations` | 13 | 13 |
| `status` | CANONICAL | DRAFT |

**产品实际消费**（权威）：`structural_analogy_explanations_v0_13.json`
（`src/data/buildProvenance.ts` 的静态 import）→ 与 DRAFT 快照**一致** ✓

---

## 二、★★ 候选级内容差异（本轮新增 · 这是审阅的核心）

### 2.1 方法

对 6 个候选**逐条**比较 `v0_12` 与 `v0_13` 的 `explanations`（以
`identity.historical_cycle_id` 为键），并**剔除快照级元数据**
（`snapshot_date` / `rule_set_version`）后逐字段比对。

### 2.2 结果（实测）

```
候选集合：6 个，**完全一致**（无增无减）

每个候选：86 → 89 条
  新增 3 · 移除 0 · ★★ **既有被修改 0**

汇总：新增 18 · 移除 0 · **既有被修改 0**
→ ★★ **既有 86 条解释逐字段完全未变**
```

★ 新增的 3 条（每个候选相同）：
`C-2017-COMM-5G-SPECTRUM` · `C-2021-MEDIA-METAVERSE` · `C-2023-POWEROP-THERMAL`
（即 R02-05 canonicalization 入库的 3 条机制段）。

### 2.3 差异的**性质判定**：纯增量，无实质研究解释变化

| 类型 | 具体 | 判定 |
|---|---|---|
| **版本号** | `artifact_version` 0.12 → 0.13 | 纯元数据 |
| **计数** | `coverage.explanations` 516 → 534；`by_historical_object_kind.campaign` 354 → 372 | 纯计数（由新增 18 条引起） |
| **状态分布** | ★ **只有 `INSUFFICIENT_EVIDENCE` 180 → 198（+18）**，其余状态（`STRUCTURAL_SUPPORTED` 5 / `STRUCTURAL_PARTIAL` 48 / `THEME_ONLY` 16 / `NO_VALID_CORRESPONDENCE` 267）**逐项不变** | 纯增量 |
| **候选级 summary** | 6 个候选**均只** `INSUFFICIENT_EVIDENCE` +3（30 → 33），其余键不变 | 纯增量 |
| **既有解释内容** | ★ **0 条被修改** | **无变化** |

★★ **结论：v0.12 → v0.13 是一次「只增不改」的版本演进** ——
既有的全部研究解释（86 条/候选 × 6）**逐字段未动**，新增的 18 条**不产生任何新的结构对应**
（`STRUCTURAL_SUPPORTED` / `STRUCTURAL_PARTIAL` 计数**完全没有增加**）。

### 2.4 新增 18 条的**内容**（为何是 `INSUFFICIENT_EVIDENCE`）

实测（以 `CC-2026-OPTICAL-LINK` 为例，其余候选同构）：

```
structural_status            : INSUFFICIENT_EVIDENCE
strict_structural_supported  : False
supported_dimensions         : ['lifecycle']                      ← 仅 1 维匹配
unknown_dimensions           : ['mechanism_driver',
                                'evidence_sequence',
                                'event_structure']                ← 3 维 NOT_AVAILABLE
why_similar                  : 生命周期阶段对应（MATCH）：历史在可比观测点处于 MAIN_RISE
why_not_similar              : 证据顺序不可比 / 事件结构资料不足
theme_relation               : METADATA_ONLY（★ 明确标注「不参与 Structural Status 判定」）
```

★ 这是**规则集的确定性输出**（同一规则 `v0.3`、同一输入 → 同一结论），
**不是**新的研究判断。★ 且 `theme_relation` 自带免责声明。

---

## 三、校验结果：**覆盖了什么 / 没覆盖什么**

### 3.1 实测通过情况

```
MS-2026-10-13-01 生成时：**13 通过 / 0 警告 / 0 失败**
全库校验（validate_market_snapshot_v0_1.py）：342 通过 / 8 警告 / 0 失败
快照 ↔ SA 版本绑定（snapshotAdapter 同时校验 artifact_version + rule_set_version）：**匹配** ✓
```

### 3.2 ★★ 校验**覆盖**的

- 快照**结构**合法性（必需字段、枚举取值）
- **版本绑定**：`candidates_source.artifact_version` 与 `rule_set_version`
- 对象 / 观测的**计数一致性**
- 回指的 SA artifact **存在性**
- 跨快照 append-only 自检（`observation_id`）

### 3.3 ★★ 校验**没有覆盖**的（不得误解「13 项通过」）

- ★ **SA 的研究解释内容是否经人工审批** —— 校验器**只查形状与绑定，不查语义**
  （这是本项目已两次踩到的同族缺口：错日期全 PASS / 错标的全 PASS）。
- ★ **新增解释的结论是否正确** —— 它只确认「该条目存在且格式合法」，
  **不确认** `INSUFFICIENT_EVIDENCE` 这个判定是否恰当。
- ★ **快照是否「应当」被签发** —— 那是治理判断，**任何校验器都不能代替**。

> ★★ **「13 通过 / 0 失败」≠「所有研究内容均已获审批」。**
> 它只说明「这份快照在结构与版本绑定上是自洽的」。

---

## 四、签发后对 Product 默认视图的影响（实测预期）

| 项 | 现状（未签发） | 签发后 |
|---|---|---|
| 默认视图（CANONICAL）候选明细 | **`resolved=false` · `details=0`**（诚实空态，拒绝跨版本合并） | `resolved=true` · **`details=89`** |
| preview 模式 | `resolved=true` · `details=89`（已正常） | 不变 |
| 快照 diff / observations（13 条） | 正常 | 不变 |
| 部署摘要的 SA 版本 | v0_13 ✓ | 不变 |

★ 即：**签发是恢复默认视图的唯一正当方式**。
★ **不得**通过放宽版本校验或删除旧 artifact 来绕过。

---

## 五、★ 签发建议

### 建议：**具备签发条件**（附两条前置确认）

**依据**：

1. ★ **差异是纯增量**：既有 86 条/候选**逐字段未变**，无一条被修改或移除（§2.2 实测）。
2. ★ **新增 18 条不改变任何研究结论**：全部为 `INSUFFICIENT_EVIDENCE`，
   `STRUCTURAL_SUPPORTED` / `STRUCTURAL_PARTIAL` 计数**零增加**（§2.3）。
3. ★ **新增内容是规则集的机械输出**，非新研究判断（§2.4）。
4. ★ **版本绑定一致**：DRAFT 快照回指的 v0_13 == 产品实际消费（§一）。
5. ★ **快照自身校验通过**（13 / 0 / 0）。

**前置确认（建议负责人过目，我未做）**：

- ⬜ **确认 v0.13 的 SA 本身已获研究侧认可** —— 本材料只证明了「快照与 SA 一致」，
  **没有**审查 SA v0.13 自身的研究质量（那属研究治理）。
- ⬜ **确认 R02-05 的 3 条机制段入库是已批准的** —— 它们是本次差异的**唯一来源**
  （`docs/R02_05_REVIEW_v0_1.md` + 粒度裁定 `docs/DECISION_CAMPAIGN_GRANULARITY_2026-10-13.md`）。

**签发时的操作要求**（既有规程）：

- ★ 必须带 `--supersedes`，否则索引里会出现**两份 CANONICAL**
  （且校验器 V2 **不检查 CANONICAL 唯一性** —— 已知缺口）。

---

## 六、签发后仍需注意的风险

1. `MS-2026-10-12-01` 转 ARCHIVED；**v0_12 快照保留不删**（若产品回退到 v0_12 仍可解析）。
2. `research_objects` / `observations` 数量**未变**（6 / 13）—— 签发只改变「回指的 SA 版本」。
3. ★ **本材料未审查 SA v0.13 的研究内容质量** —— 见 §五前置确认第 1 条。
4. CI 门禁**不检查「快照是否已签发」**（签发是人工治理动作，不自动化）。

---

*审阅材料 v0.2 · 2026-10-14 · ThreeC Agent · 未签发任何快照*
