# R01-03 Intake Review — Addendum v0.1（008 定向修正）

> **性质**：对 `docs/R01_03_INTAKE_REVIEW_v0_1.md` 的**增量复核**。
> **不覆盖上一轮记录** —— 上一轮文档保持原样（点-in-time 记录）。
> **本轮未创建 Canonical Campaign · 未导入 DB · 未修改 Canonical 数据 · 未修改 taxonomy ·
> 未启动 R01-04 的 ThreeC Intake · 未启动 R01-03 Canonicalization。**

---

## 1. 为什么 008 被修正

上一轮 Intake Review（v0.1 §5.4）判定 **`R01-RESOURCES-008.why_not` 的核心反例论据不成立**：

> 旧 `why_not`：「A 股「化肥」板块 **2022-03-15 至 2022-12-30** 区间涨跌幅为 **-12.05%**，
> 即商品价格上行期板块并未同向走强，商品与 A 股主题的传导证据不足。」

**问题**：008 自身 `date_candidates.peak = 2022-03-01 ~ 2022-04-30`。
以 **2022-03-15（≈候选自身峰值）** 为起点度量，得到的是**峰值之后的下跌段**，
**不能**用于证明「商品上行期板块未同向走强」。

**该包自身的证据即已否定该结论**：
`E075`（2021-12-31, contemporaneous, supporting）——
「A 股「化肥」概念板块 **2021-01-04 至 2021-12-31 区间涨跌幅为 +24.24%**，区间最高点 1048.07 点（2021-09-28）」
→ 在 008 的 **MAIN_RISE 期（2021-01 → 2022-03）**，A 股化肥板块**是上涨的**。

**对照 `011`（反例成立）**：`011` 的反例 `E105` 取 **2016-01-04 ~ 2016-12-30（完整全年）**，
与商品口径**同一窗口**（商品 +29.84% vs 板块 -7.13%）→ 反例有效。
**008 的反例无效**，因为窗口错位。

---

## 2. 修正后结论（Worker 已交付）

### 2.1 `why_not`（新版）

> ① 无法确立商品与 A 股主题的完整因果证据链（结论降级为「**证据不足 / 无法确认**」）：
> E075 显示板块级响应确实存在（+24.24%），**故不能据此断定「商品上行期板块未同步走强」**；
> 但 E075 仅覆盖 2021 年，其峰值（2021-09-28）与本候选观测到的商品 peak 窗口（2022-03—2022-04）
> 存在约半年的**领先滞后错位**，包内现有证据**无法判定二者是否属同一结构或存在领先滞后关系**。
> ② 本候选现有 evidence 无一条同期可观察证据可直接锁定 A 股主题启动；
> ③ 因此核心缺口不是「存在反例」，而是「**无法确认传导**」；
> ④ 是否属「农业/粮食安全」主题（R01-04）仍需边界裁定。

### 2.2 修正是否准确（本轮判定）

| 复核项 | 结论 |
|---|---|
| 原错误反例的「商品上涨期 A 股板块未同步」定性是否已删除 | ✅ **已删除**，并**显式撤回**（「故不能据此断定…」） |
| 是否准确降级为「证据不足 / 无法确认」 | ✅ **是**（原文用词即「证据不足 / 无法确认」） |
| 是否被重新解释成已有证据无法支持的结论 | ✅ **否** —— 修正**没有**反向过度解释（既未主张「已确认传导」，也未主张「反例成立」），而是**如实降级**并指明缺口 |
| 是否指明需补什么 | ✅ 是（「需补齐 2022 年逐月板块序列与同期政策/价格锚点」） |

### 2.3 ★ 发现一处**措辞与数据不符**（不阻塞，供后续措辞修正）

新 `why_not` ② 称「本候选现有全部 evidence **均为 subsequent 口径**」，并列举
`E071 FAO 2022-12-05 / E072 USDA 2022-04-06 / E073·E074 商务部 2023-01-13`（共 4 条）。

**实测**：008 的 5 条证据中 **`E075` 的 `temporal_relation = contemporaneous`**（非 subsequent）。

**但该措辞偏差不影响结论**：`E075` 虽为 `contemporaneous`，其 `support_kind` **不含
`point_in_time_support`**（008 的 **PIT 证据数 = 0**）—— 因此「**无同期可观察证据可直接锁定
A 股主题启动**」这一**实质判断仍然成立**。

> **判定**：属**措辞精度问题**（把「无 PIT 支撑」表述为「全部 subsequent」），
> **不改变结论、不阻塞接收**。建议在后续轮次统一为
> 「E075 虽为 contemporaneous，但未标 `point_in_time_support`」。
> **本轮不修改 Package**（用户明确本轮不擅改 Package）。

---

## 3. 新版 Package 校验结果

### 3.1 改动范围（逐文件字段级比对：上一轮 HEAD vs 新版）

| 文件 | 改动 |
|---|---|
| `candidates.json` | **仅 2 处**：`candidates[7].why_not` · `candidates[7].notes`（= `R01-RESOURCES-008`） |
| `evidence.json` | **仅 1 处**：`evidence[44].description`（= `E075`，补充领先滞后说明） |
| `quality_summary.json` | **仅 1 处**：`known_gaps[3]`（C8 条目重写为「证据不足且无法确认」） |
| `coverage.md` | 文本 2 行（「弱传导案例」→「**C8 农化不作反例**」） |
| `checksums.sha256` | 重算（10 条，文件集合与顺序不变） |

**其余全部未变** ✓：

| 项 | 结果 |
|---|---|
| 其余 **10 个 Candidate**（001–007、009–011） | **逐字节完全一致** ✓ |
| **12 个 Conflict** | **完全一致** ✓ |
| `sources.json` · `securities.json` · `exclusions.json` · `research_questions.json` · `manifest.json` | **完全一致** ✓ |

### 3.2 校验

| 检查 | 结果 |
|---|---|
| 现有 Intake Validator（**C01–C25**） | ✅ **PASS（0 FAIL / 0 WARN）** · `INFO C25 Strict Draft-07 校验通过（0 违规）` |
| **Strict Draft-07**（独立 `jsonschema` 4.26.0 复核） | ✅ **0 违规**（R01-01 / R01-02 对照亦 0） |
| `checksums.sha256`（10 条） | ✅ **ALL OK**（R01-01 / R01-02 / R01-03 三包均 ALL OK） |
| 悬空引用（candidate→evidence / →security / evidence→source / date_candidates→source） | ✅ **无** |
| 孤儿 Evidence / Security | ✅ **0 / 0** |
| 孤儿 Source | ⚠️ **1（`R01-RESOURCES-S012`）** —— **与上一轮相同，008 修正未涉及**（Worker 自述「作为背景参考，未单独绑定 evidence」；不阻塞） |
| **008 引用关系** | ✅ **未损坏** —— `evidence_ids = E071–E075`（5 条全部存在）· `security_ids = SEC018/SEC027/SEC028`（3 条全部存在）· `date_candidates` 引用的 evidence/source 全部存在 |

### 3.3 `intake --check`

```
INFO  C20   packages found: 3
INFO  C25   [R01-01] … 0 违规
INFO  C25   [R01-02] … 0 违规
INFO  C25   [R01-03] … 0 违规
checks: 25   FAIL: 0   WARN: 0   RESULT: PASS
```

✅ **恢复 PASS / 0 FAIL / 0 WARN** —— 上一轮报告的 **H2（`packages/R01-04/` 空目录）已被移除**，
`packages found` 由 4 恢复为 **3**。

---

## 4. 上一轮结论哪些保持不变

> ## **上一轮 `R01-03 Intake Review v0.1` 的全部结论**继续有效**，除 008 的处置描述需按 §5 更新外，无实质变化。**

| 上一轮结论 | 是否变化 |
|---|---|
| **A** Package 通过 Intake | ✅ **不变**（新版仍 PASS） |
| **B** 必须修复项 = `008.why_not` 反例论据不成立 | ✅ **已由 Worker 修正 → 该项关闭**（见 §2） |
| **C** Protocol / Schema / Validator 结论 | ✅ **全部不变** —— Schema 无问题 · Protocol 无需修改 · **Validator C08 与 Research Model v1.0 §15 的 `research_report` tier 冲突（H1）依旧成立**（与 008 无关） |
| **D** 可进入 Canonicalization 名单 | ✅ **不变**：`001` `002` `003` `004` `005` `007` `009` `010`（8 个） |
| **E** Research Only 名单 | ⚠️ **`011` 不变（明确 Research Only）**；**`006` 不变（建议 Research Only，理由与 008 无关）**；**`008` 需更新** —— 见 §5 |
| **F** Conflict 优先级（12 条全部移交） | ✅ **不变**：P0 = `CF001` `CF003` `CF006` `CF009`；P1 = `CF002` `CF004` `CF005` `CF007` `CF010` `CF012`；P2 = `CF008` `CF011` |
| **H** 独立工程问题 | ✅ **不变**：H1（C08 vs Research Model tier）仍待处理；**H2（R01-04 空目录）已解决**；H3（Validator 无孤儿检查）仍待处理 |
| 12 Conflict 一条未消解 | ✅ **不变** |
| 未创建 Canonical Campaign / 未导 DB | ✅ **不变** |

---

## 5. 008 的最终处置（**更新上一轮 E 项**）

| | 上一轮 v0.1 | 本轮 Addendum v0.1 |
|---|---|---|
| `008` 的判定 | **建议 Research Only** —— 理由：PIT = 0 + `why_not` 反例论据**不成立** → 结论不可信 | **建议 Research Only（理由已更新）** —— 反例论据**已被 Worker 撤回**；保留 Research Only 的**真实理由**为：<br>① **PIT 证据 = 0**（无任何 `point_in_time_support`）；<br>② **全部可观察证据与商品 peak 窗口存在约半年错位**，无法判定是否同一结构；<br>③ `E075` 仅覆盖 2021 年，**缺 2022 年逐月板块序列**；<br>④ 归属（资源/化工 vs 农业/粮食安全）仍需边界裁定 |

> ★ **重要**：008 的 Research Only 判定**不是**因为「商品涨而 A 股跌」（该结论已撤回），
> 而是因为「**无法确认传导**」。这一区分是上一轮 Review 与本次修正共同确立的。

**若后续补证**（2022 年逐月板块序列 + 同期政策/价格锚点），可在**独立复核轮次**重新评估。

---

## 6. 是否可以正式进入 R01-03 Canonicalization

> ## ✅ **可以正式进入。**

| 条件 | 状态 |
|---|---|
| Package 通过 Intake（C01–C25 + Strict Draft-07） | ✅ PASS / 0 违规 |
| checksums 完整 | ✅ ALL OK |
| 引用完整性 / 无孤儿 evidence·security | ✅ 无悬空 / 0 / 0 |
| 必须修复项 | ✅ **0**（上一轮的 008 反例问题已关闭） |
| 12 Conflict 已识别并分级 | ✅ P0×4 · P1×6 · P2×2 |
| taxonomy | ✅ 11/11 候选 RESOLVED → 根「资源」· 无阻塞 gap |
| 可进入 Canonicalization 的候选 | **8 个**（001–005、007、009、010） |
| 保留 Research Only | **3 个**（011 明确；006 / 008 建议） |

**进入 Canonicalization 时须一并提交 Canonical Decision 的事项**：
1. 12 条 Conflict 全部裁决（P0 优先：`CF001` `CF003` `CF006` `CF009`）
2. `011` 保持 RESEARCH_ONLY；`006` / `008` 按 Research Only 处置（或先补证）
3. `CF012`（同一证券跨候选）提示 `001`/`004`/`007`/`008`/`009`/`010` 的边界可能需重划
4. 别名 taxonomy 缺口（工业金属/铜/电解铝/锂/锂矿/能源金属/稀土/稀土永磁/化工/染料/化肥/黄金）—— **只记录，不扩展**

---

## 7. 本轮附带发现：`R01-01` / `R01-02` 的 `README.md` 被删除

**现象**：新版 `05_OUTPUT` 覆盖时，`research/intake/packages/R01-01/README.md` 与
`R01-02/README.md` **被删除**（git 状态为 ` D`）。

**核查**：

| 项 | 结论 |
|---|---|
| 该 README 是什么 | **Research Worker 工作区的模板说明文件**（`# 05_OUTPUT/ — 唯一正式交付位置`，67 行）—— **不是 Package 数据** |
| 是否属于「标准 11 个正式文件」 | ❌ **不属于**（Protocol §5.3 的标准集为 manifest / coverage / candidates / evidence / sources / securities / exclusions / conflicts / research_questions / quality_summary / checksums） |
| 是否被 checksums 覆盖 | ❌ **未覆盖**（R01-01 / R01-02 的 checksums 均为 10 条，不含 README） |
| 删除是否破坏校验 | ❌ **不破坏** —— 三包 checksums 仍 **ALL OK** |

**处理**：**接受该删除**（不改动）。理由：① 非 Package 数据；② 未被 checksum 覆盖；
③ 删除后 R01-01 / R01-02 与 R01-03 **统一为标准 11 文件布局**，与「只更新标准 11 个正式文件」的意图一致。
**本轮未恢复、未修改 R01-01 / R01-02 的任何数据文件。**

---

## 8. 本轮严格未做

- ❌ 未创建 Canonical Campaign · 未导入 DB · 未修改任何 Canonical 数据
- ❌ 未修改 taxonomy（CMTR v1 只读）
- ❌ 未启动 R01-04 的 ThreeC Intake（R01-04 Worker 可继续独立研究）
- ❌ 未启动 R01-03 Canonicalization
- ❌ 未修改 R01-03 Package 的任何字节（§2.3 的措辞问题**只报告不修**）
- ❌ 未覆盖上一轮 `R01_03_INTAKE_REVIEW_v0_1.md`（本文件为独立 Addendum）
