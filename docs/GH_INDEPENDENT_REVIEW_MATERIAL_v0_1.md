# G / H 独立研究材料（待审 · 未裁决）

> 制作：ThreeC Agent · 2026-10-14
> ★ **本文件不是裁决** —— 只整理证据、缺口与建议路径。
> ★ **G 与 H 是两件独立事项**，本文分节处理，**不合并成一个研究结论**。
> ★ 未写入任何 canonical 数据；未修改任何既有裁定。

---

## G：`R02-PHARMA-002`（创新药 BD 出海 / License-out）

### G.1 审理状态

| 项 | 状态 |
|---|---|
| 原始包 | ✅ `research/intake/packages/R02-01/candidates.json` |
| 包内自评 | `research_status = **INSUFFICIENT**` · `confidence = **low**` |
| 是否有正式裁决 | ★ **无** —— `research/intake/reviews/` 下无 R02-01* 裁定文件 |
| 是否入库 | **否**（DB 无对应 campaign） |
| 标的 | `R02-PHARMA-SEC004` **恒瑞医药（600276，role=leader）** |
| ★ 常见误判 | ★★ **不是** `C-2023-PHARMA-GLP1` 的漏挂（恒瑞不属于该对象） |

### G.2 候选定义（实测原文）

```
title : 创新药 BD 出海（License-out）行情 —— 交易兑现驱动
security_ids : ['R02-PHARMA-SEC004']
lifecycle : MAIN_RISE 2025-01-01 ~ 2025-06-30
  basis : 「上证报记载『2025 年上半年科创板创新药企业出海 BD 掀起新高潮，重磅交易频现』；
           本包未取得精确起涨日。」
  notes : ★ 起点精度仅为**半年窗口**，且 confidence=low
date_candidates: (未取得 EXACT_DATE)
why_not : 「本包主张其成立，未提出反对理由；该主张是否成立
           须由 ThreeC Agent 用 Campaign Independence Gate 判定。」
```

### G.3 与现有 Campaign 的关系（实测）

```
恒瑞医药（HENGRUI）当前归属：**C-2019-PHARMA-INNOV**（2019 创新药，role=leader）
  —— 属**另一个轮次**的对象，与 G 候选（2025 BD 出海）**时间不重叠**

DB 中是否存在「BD 出海」段对象：**无**
库内其他 PHARMA 对象：C-2019-PHARMA-INNOV · C-2023-PHARMA-FLU · C-2023-PHARMA-GLP1
```

★ **独立性问题**：G 候选主张 2025 上半年的 BD 出海段。
- 与 `C-2019-PHARMA-INNOV`：**时间不重叠**（2019 → 2025），但**机制同族**（均涉创新药）。
- ★ 需走 **Campaign Independence Gate**：是否构成**独立周期**还是既有对象的**后续阶段**。
  ★ 该判定**未做**（属研究判断）。

### G.4 证据缺口（逐条）

| # | 缺口 | 影响 |
|---|---|---|
| 1 | **无精确起涨日**（只有半年窗口） | `start_date` 精度不足 |
| 2 | **无 peak_date** | K 线层无法直接证伪 |
| 3 | **无 end_date** | 生命周期不闭合 |
| 4 | `date_candidates` 为空 | 无可替代日期 |
| 5 | 单一标的（恒瑞） | 样本极薄 |
| 6 | **从未被独立审查** | 无 verdict、无 `required_changes` |

### G.5 待回答的问题

1. 2025 上半年 BD 出海是否构成**独立 Campaign**，还是 `C-2019-PHARMA-INNOV` 的**后续阶段**？
2. 若独立 → `start` / `peak` / `end` 各是什么？**证据来源**是什么？
3. 恒瑞的 `leader` 角色在**该段**是否有依据（包内 basis 仅一句「BD 出海段的代表性交易主体」）？
4. 是否需要补更多标的（当前仅 1 个）？

### G.6 建议裁决路径

| 选项 | 说明 |
|---|---|
| ★ **建议：转入独立审查轮次** | 因 G 候选**从未被审查**，且包内自评为 `INSUFFICIENT`/`low`。 |
| 不建议：直接 DEFER | ★ 用户明确「**不得凭自评 INSUFFICIENT 或 confidence=low 自动生成正式裁决**」→ **不能**仅凭自评定 DEFER。 |
| 不建议：直接入库 | 缺口 1–6 未解决。 |

**具体路径**：

1. 由 **Research Agent** 补数据（精确起涨日 / peak / end / 更多标的 / date_candidates）——
   ★ 或由产品负责人决定「G 候选是否值得投入」。
2. ThreeC Agent 独立出具**首审 verdict**（含 Campaign Independence Gate）。
3. 再决定 canonicalization。

★ **阻塞条件**：缺口 1（精确起涨日）与 5（单一标的）未解决前，**不具备入库条件**。

---

## H：`R02-PHARMA-003` / R02-02（2017–2018 医药审评改革）

### H.1 历史裁决（**保留原文**，不追认）

来源：`docs/STAGE_REVIEW_2026-10-07.md`

```
:109   intake 包  R02-01 PASS · **R02-02 PASS(DEFER)**
:132   | 2 | **R02-02（2017–2018 医药）为 DEFER** |
           缺行情序列 + 与 C-2019-PHARMA-INNOV 的边界裁决 |
```

另见 `docs/DESIGN_KLINE_VALIDATION_AND_EARLY_WINDOW_v0_1.md:90`
（记 DEFER 原因为「缺行情序列、peak 无法界定」）。

★ 本材料**不改写、不扩大**该裁决。裁决号为 `DEFER`。

### H.2 候选定义（实测）

```
候选   : R02-PHARMA-003「药品与医疗器械审评审批制度改革驱动的创新周期（2017–2018）」
包内自评: research_status = INSUFFICIENT · confidence = low
lifecycle : MAIN_RISE 2017-10-08 ~ 2018-06-30
            basis 自述「**未取得该段的逐月行情证据**，仅以半年粒度记录」
date     : start = EXACT_DATE **2017-10-08**（制度起点，confidence=**high**，**有来源**：
           中办国办印发《关于深化审评审批制度改革鼓励药品医疗器械创新的意见》）
标的     : 恒瑞医药 600276（role=leader）
possible_duplicate_of : ['C-2019-PHARMA-INNOV']（包内自标）
evidence_ids : 4 条
```

### H.3 逐项核验（用户要求的四项）

#### ① 行情覆盖（实测）

```
标的 HENGRUI 的 market_daily 覆盖：**2018-01-02 ~ 2022-12-30**（2430 行）
  目标区间 2017-10 ~ 2018-06 内：**486 行**（仅覆盖 2018-01 起）
  ★★ **2017-10-08 ~ 2017-12-31 无行情**
`fetch_gaps.json` 的 floors：HENGRUI **未登记**（抓取器未确认其最早可得日）
```

→ 该候选的 MAIN_RISE **起点 2017-10-08 落在无行情区间**。
★ 已验证：2026-10-13 本机仅抓到 ZTE（2016 起），未抓 HENGRUI 的 2017 年
（**未确认**腾讯接口是否提供更早数据 → 待办）。

#### ② MAIN_RISE 起点

- 起点 `2017-10-08` = **政策文件印发日**（制度起点），**有来源、high confidence** ✓
- 但**不是行情起点** —— 「未取得精确起涨日」（包内自述）
- ★ 该段**无逐月来源支撑**（半年粒度）

#### ③ floor / peak 信息

| 信息 | 状态 |
|---|---|
| `floors` 登记 | **无 HENGRUI 条目** |
| `peak_date` | **缺失**（包内未给） |
| K 线机制能否处理无 peak | ✅ **能** —— 全库有 **5 个 `NO_PEAK_RECORDED`** 对象（实测），机制不阻塞 |

#### ④ 与 `C-2019-PHARMA-INNOV` 的边界

```
C-2019-PHARMA-INNOV : 2019-01-02 → 2021-07-01 → 2022-10-31
R02-PHARMA-003 提议 : 2017-10-08 → 2018-06-30
★ 时间**不重叠**（相隔约 6 个月），但**机制同族**（创新药政策驱动）
→ 需走 Campaign Independence Gate（★ 未做）
```

### H.4 结论：**技术机制已具备，但候选数据仍缺失 → 维持 DEFER**

| 维度 | 判定 |
|---|---|
| 技术机制 | ✅ 已具备（K 线五状态 + `NO_PEAK_RECORDED` 已实证可用） |
| 候选数据 | ❌ **仍缺失** —— 起点在无行情区间；`floors` 未登记；无 peak |
| 边界问题 | ❌ **未解决** —— 需 Independence Gate（未做） |
| 证据是否足以启动复核 | ★ **部分足以** —— 理由见下 |

**「足以启动复核」的判断**：

★ 可以启动一项**很窄的**前置核查：**确认 HENGRUI 的 2017 年行情是否可得**
（即补 `floors` 登记）。这只需跑一次抓取器，成本极低。
★ 但**不足以**启动独立审查轮次：因为 ①②③ 中只有 ③ 解决了一半，
MAIN_RISE 段仍无逐月来源支撑，边界裁决仍未做。

### H.5 结构化裁定文件的生成方式（**待审批**，本轮未创建）

**现状**：DEFER 裁决只存在于 `.md`（文档级），**机器不可追溯**。

**证据缺口**：`research/intake/reviews/` 下**无 R02-02 判定文件**。

**建议方案**（★ **未执行**）：

```
新建 research/intake/reviews/R02-02_verdicts_v0_1.json
  candidate_id : R02-PHARMA-003
  verdict      : DEFER
  decided_at   : 2026-10-07          ← ★ 用原裁决日期，不用今天
  decided_by   : "转录自 docs/STAGE_REVIEW_2026-10-07.md:109,132"
  source_doc   : "docs/STAGE_REVIEW_2026-10-07.md:109,132"
  reasons      : ["缺行情序列、peak 无法界定",
                  "与 C-2019-PHARMA-INNOV 的边界需裁决"]
  revision     : [{date:"2026-10-14", change:"**事后转录**历史 DEFER；无新裁决"}]
```

**三条硬约束**：

1. ★ `decided_at` 必须是 **2026-10-07**（原裁决日），**不得写成今天**（否则是伪造成新裁决）。
2. ★ `revision` 必须标明「**事后转录，无新裁决**」。
3. ★ 原 `.md` **不动**（历史留痕）。

**建议同时为 R02-01 补一份**（含 `R02-PHARMA-001` 入库结论 + **`R02-PHARMA-002` 未裁决状态**）。
★ G 候选用 `verdict: **PENDING**`（**不是** `DEFER` —— 未经审查，不得定 DEFER）。

---

## 总表

| 项 | 裁决状态 | 本轮结论 | 下一步 | 阻塞条件 |
|---|---|---|---|---|
| **G**（`R02-PHARMA-002`） | ★ **未裁决（PENDING）** | 从未被独立审查；有 6 项证据缺口 | 补数据 → 独立首审 → 再定 | 精确起涨日 / 单一标的 |
| **H**（`R02-PHARMA-003`） | **DEFER**（2026-10-07 原文保留） | 机制具备但数据缺失；维持 DEFER | 可选：先做「2017 行情可得性」窄核查 | MAIN_RISE 无逐月来源 / 边界未裁 |

★ **两项未合并**：G 是「未裁决」，H 是「已裁决 DEFER」—— **性质不同，理由不同，处置不同**。

---

*独立研究材料 · 2026-10-14 · 待审 · 未产生任何裁决*
