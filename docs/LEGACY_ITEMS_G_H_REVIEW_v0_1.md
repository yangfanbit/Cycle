# 遗留事项 G / H 核实结论

> 核实人：ThreeC Agent · 2026-10-13 · **只读核实，未修改任何 canonical 数据**
> 触发：用户 2026-10-13 任务 §4.2
> 定义来源：`docs/TASK_ALLOCATION_2026-10-11.md:60-61` · `docs/PROJECT_RETROSPECTIVE_AND_PLAN_2026-10-12.md:91-92`

---

## G：R02-01 标的漏挂（恒瑞医药）

### 定义（原文）

> R02-01 包声明 4 条 securities，导入器只登记 3 条 —— `R02-PHARMA-SEC004`（恒瑞医药，
> 库内 `HENGRUI`）**没进** `C-2023-PHARMA-GLP1`

### 实测事实

```
包声明（research/intake/packages/R02-01/securities.json）:
  R02-PHARMA-SEC001 常山药业 · SEC002 翰宇药业 · SEC003 博瑞医药 · SEC004 恒瑞医药   ← 4 条

DB campaign_securities（C-2023-PHARMA-GLP1）:
  CHANGSHAN 常山药业 leader · HANYU 翰宇药业 representative · BORUI 博瑞医药 representative   ← 3 条

HENGRUI 是否在 securities 表      : **是**（已存在）
HENGRUI 是否挂在 C-2023-PHARMA-GLP1: **否**   ← ★ 确认漏挂
```

### 结论

| 项 | 判定 |
|---|---|
| 原始输入是否存在 | ✅ 存在（包内声明 4 条） |
| 当前记录情况 | ★ **`HENGRUI` 在 `securities` 表，但 `campaign_securities` 缺一行** |
| 性质 | **漏挂**（不是「未入库」，也不是「被排除」）—— 标的主记录已在，只缺关联 |
| 影响面 | `campaign_securities` 1 行；下游 `export.securities`（campaign_id 关联）会少 1 条；产品「代表股票」少显示恒瑞医药 |

### ★ 修正的可行性与风险

- **技术成本**：极低（新增 1 行 `campaign_securities`）。
- ★ **但必须确认「role」** —— 包内声明的角色是什么？**未取得**该字段（需查包内 securities.json 的 role）。
  ★ 若包未给 role，**不得**臆测（`leader` / `representative` 语义不同）。
- ★ **属已入库轮次**（R02-01 已 canonicalize）→ 按 `AGENTS.md` §4，
  修改已冻结研究结论需**明确授权**。

### 建议

**待负责人裁决**（不建议自行补挂）：
- 若批准：以**覆盖层机制**（同 `review_overrides`）补该关联，并留 `basis` + `review_ref`；
- 补后需重跑下游（export / SA 不受影响，但 export 的 securities 段会变）。

---

## H：R02-02 从未入库

### 定义（原文）

> R02-02 包（`R02-PHARMA-003`）**无导入器、无 campaign、无审查结论** = 「已校验未处置」

### 实测事实

```
包存在            : ✅ research/intake/packages/R02-02/（11 个文件）
候选              : R02-PHARMA-003「药品与医疗器械审评审批制度改革驱动的创新周期（2017–2018）」
                    research_status = **INSUFFICIENT**（包内自称）
导入器            : **无**
DB 对应 campaign  : **无**（DB 只有 C-2019-PHARMA-INNOV / C-2023-PHARMA-FLU / C-2023-PHARMA-GLP1）
独立审查裁定文件   : **无**（research/intake/reviews/ 下无 R02-02*）
```

### ★★ 关键澄清：「无审查结论」**不完全准确**

实测在**文档层**找到了处置结论：

```
docs/STAGE_REVIEW_2026-10-07.md:109   intake 包  R02-01 PASS · **R02-02 PASS(DEFER)**
docs/STAGE_REVIEW_2026-10-07.md:132   | 2 | **R02-02（2017–2018 医药）为 DEFER** |
                                        缺行情序列 + 与 C-2019-PHARMA-INNOV 的边界裁决 |
docs/DESIGN_KLINE_VALIDATION_AND_EARLY_WINDOW_v0_1.md:90
                                      R02-02 被 DEFER 的原因是「缺行情序列、peak 无法界定」
```

→ **R02-02 已判 `DEFER`**（2026-10-07），**未入库是正确的**（DEFER 不应入库）。
★ 缺的是**结构化裁定文件**（`R02-02_verdicts_v0_1.json` 之类），而非「没有结论」。

### 结论

| 项 | 判定 |
|---|---|
| 原始输入是否存在 | ✅ 存在 |
| 是否「漏挂 / 未入库 / 被排除 / 未完成审核」 | ★ **都不是** —— 是**已判 DEFER**（文档级），故**按规则不入库** |
| 当前记录缺口 | ★ **缺结构化裁定文件**（只有 `.md` 记录，无 `.json` 裁定） |

### ★ 新情况：原 DEFER 理由之一**可能已解除**

原 DEFER 理由 ①「**缺行情序列、peak 无法界定**」——
★ 而本项目此后已落地 **K 线证实机制**（`kline_confirmation_v0_2.json`，
五状态含 `NO_PEAK_RECORDED` / `NO_DATA`）与 **peak 参照物**（`peak_referent_v0_2.json`）。
→ 该理由**在基础设施层面已可处理**（至少可给出明确状态，而非「无法界定」）。

★ 理由 ②「与 `C-2019-PHARMA-INNOV` 的边界裁决」—— **未变**，仍需裁决。

### 建议

**待负责人裁决**（不建议自行重新评估）：
1. **是否重新评估 R02-02**（理由 ① 的基础设施已具备）；
2. 若重新评估 → 走**独立轮次**（角色分离：Research 产出 / ThreeC 审查）；
3. **补结构化裁定文件**（把 `.md` 里的 DEFER 结论形式化，便于机器追溯）。

---

## 总表

| 项 | 原始输入 | 当前记录 | 性质 | 本轮动作 | 待决 |
|---|---|---|---|---|---|
| **G** | ✅ 有（4 条） | 3 条关联，`HENGRUI` **漏挂** | **漏挂** | 未动 | ★ 是否授权补挂（需先确认 role） |
| **H** | ✅ 有 | 无 campaign / 无结构化裁定 | **已判 DEFER**（文档级） | 未动 | ★ 是否重新评估 + 补结构化裁定 |

★★ **两项均未修改任何数据**（符合用户「不得在未确认来源及影响前直接补挂、入库」的指令）。

---

*核实结论 · 2026-10-13 · ThreeC Agent · 只读*
