# FIRST_REAL_OBSERVATION_CYCLE_v0_1

> | 项目 | 值 |
> |---|---|
> | 性质 | **ThreeC 第一次真实研究使用周期**（不是新功能开发） |
> | 完成日期 | 2026-09-19 |
> | 起始状态 | `HEAD = origin/main = e90e80d`，ahead/behind `0/0`，工作树 clean（**自行核对**；远程无新增） |
> | **Gate** | **`PASS`** |
> | 代码变更 | **仅 3 项语义修复**（真实使用发现的明确语义误导/错误）· 零 Research 规则变更 · 零数据模型新增 |

---

## 1. Observation Context

| 项 | 值 |
|---|---|
| **snapshot_date** | **`2026-09-15`** |
| 使用日期 | `2026-09-19`（距快照 **4 天**） |
| 使用对象 | 当前 5 个 Current Candidate：`CC-2026-BCI-MEDTECH`（`THEME_FORMING`，**较早阶段**）· `CC-2026-OPTICAL-LINK`（`EXPANSION`，**较后阶段**）· 另含 `CC-2026-COMPUTE-POWER` / `CC-2026-EMBODIED-AI` / `CC-2026-OFFSHORE-WIND` |
| 历史数据 | `timeline_export_v1` · 13 Campaign + 4 Research Candidate · 研究覆盖至 **2025** |
| 观察方式 | 以**真实数据渲染真实组件**，逐字读取用户实际看到的文本；并结合 CSS 判断布局 |

> **当前为 2026-09-15 离线研究快照，不是实时市场数据。**

**观察环境说明**：本轮沙箱内 Vite dev server 无法绑定端口 → 改用「渲染真实组件 + 真实数据」逐字读取。
所见文本与用户实际读到的一致；**布局类结论依据 CSS 规则推导，已在报告中标注**。

---

## 2. Actual Paths

实际走完的路径：

```
① Current → Cycle Map → Case
   2026-W38 → 历史时间窗口（24 个周期 / 7 个年份）→ 2019 汽车·智能驾驶 → Case

② Current → SA → Case
   CC-2026-BCI-MEDTECH（THEME_FORMING）→ Structural Analogy（17 个历史对象）
   → C-2023-AD（结构支持 · 唯一严格口径）→ Case

③ Case → SA → Cycle Map
   C-2023-COMM-OPTICAL（从 OPTICAL-LINK 的 SA 进入）→ 返回 SA → 返回 Cycle Map
```

**全部三条路径均可走通** ✅ 无 BLOCKER。

---

## 3. Value Findings

| # | 有价值的部分 | 为什么真的帮到研究 |
|---|---|---|
| **V1** | **Cycle Map 的年份分组 + 案例区间 + Lifecycle 阶段** | 一眼回答「历史上这一周有哪些周期、各处于什么阶段」。实测：`2020` 年窗口内 4 个周期，阶段分别为 主升 / 回撤 / 主升 / 衰减 —— **这是「搜同名主题」得不到的信息** |
| **V2** | **`ENTERED_IN_WINDOW`（本窗口内开始）** | 直接回答「**这一时期刚进入某阶段**」，而不是「发生过」 |
| **V3** | **SA 的「驱动机制」与「证据类别」分层** | 明确区分机制判断（`POLICY_DRIVEN`）与证据来源（`POLICY`），不再混称 Driver |
| **V4** | **SA 的「为什么对应 / 哪里不同」并列** | 实测 `C-2019-AD`：生命周期部分对应 + 驱动机制部分对应 + 证据顺序无可用资料 + 事件结构不对应 —— **四项差异一次看清** |
| **V5** | **Case 的 Header 三类信息**（历史对象类型 / Macro Theme / Theme Cycle） | 实测 `C-2023-COMM-OPTICAL`：`信息通信` / `comm_ai_optical_2023_2025` —— 立刻知道这是哪个 Theme Cycle |
| **V6** | **Case 的「证据序列（按时间 + 阶段）」** | 实测 5 条事件按日期升序并标注阶段（主升 ×4 / 阶段未知 ×1）→ **「怎么发展」看得懂** |
| **V7** | **「阶段未知」明示** | 明确「不落在任何已记录生命周期区间内（UNKNOWN，**不是**不对应）」→ 不会被误读成「没发生」 |

---

## 4. Friction Findings

| # | 摩擦 | 实测证据 | 处置 |
|---|---|---|---|
| **F1** | **Case 中「证据序列」与「关联事件」几乎完全重复** | `C-2023-COMM-OPTICAL`：同一批 5 条事件出现 **2 次**（证据序列多一个阶段列） | **REWORK**（未改） |
| **F2** | **「研究归因（四问 · 自由文本）」与上两者高度重叠** | 同一批 `EV-COMM-07/08/09/10` 文本**第三次**出现 | **REWORK**（未改） |
| **F3** | **Cycle Map 的 Lifecycle 筛选原为中英混用** | 实测选项：`declining` / `主升` / `回撤` | ✅ **已修**（见 §6 Fix3） |
| **F4** | **`themeCycleId` 可读性低** | 显示 `auto_intelligence_2023` / `comm_ai_optical_2023_2025` 等内部 id | **POLISH**（未改） |

> F1 + F2 是本轮**最大的研究摩擦**：Case 详情里同一批事件信息重复三遍，
> 挤占了「继续往下研究」的注意力。**信息量没有增加，长度增加了约 3 倍。**

---

## 5. Confusion Findings

| # | 容易误解 | 实测证据 | 处置 |
|---|---|---|---|
| **C1** | **Cycle Map 的 ±2 周条全为 0** | `2026-W36…W40` 全部「0 个周期」→ 首屏 5 个零，用户会以为「这一周附近历史上没有周期」；而下方历史窗口实际有 **24 个周期** | ✅ **已修**（见 §6 Fix1） |
| **C2** | **Cycle Map 未标识 Research Candidate** | `2020 疫情医疗（…）` / `2021–2022 中医药（…）` 看起来像 Campaign；而**相邻的 Calendar Lens 有 `RC` 标** | ✅ **已修**（见 §6 Fix2） |
| **C3** | **Case 中 `phases` 与 `signals` 是两套阶段** | `C-2023-COMM-OPTICAL` 的 phases 只有 主升/回撤/退潮（3 段），而「研究信号」显示 早期信号/主题形成 —— 用户不知道以哪个为准 | **POLISH**（未改；属 Research 数据层差异，非 UI 可解） |
| **C4** | **SA 的「事件结构 · 不对应」高频出现** | BCI 前 6 条中 **6 条**均为「事件结构 不对应」→ 可能被读成「都不像」 | **DEFER**（属 Rule Set v0.2 的既有结论，**不放宽规则**） |

---

## 6. 本轮代码修复（仅 3 项，均为**明确语义误导/错误**）

| Fix | 问题 | 修复 | 依据 |
|---|---|---|---|
| **Fix1** | ±2 周条全 0，且未解释原因 → **明确语义误导** | 当 5 周全空时显示 `role="note"` 说明：「以上 5 周属于**当前年份**（2026），该年份尚未纳入历史研究（覆盖至 2025），因此计数为 0。**这不代表历史上这一周附近没有周期** —— 请见下方历史时间窗口」 | §二 / §十四「明确语义误导」 |
| **Fix2** | Research Candidate 在 Cycle Map 中**未标识** → 与相邻 Calendar Lens 不一致 → **identity 语义误导** | 为 `objectKind === 'research_candidate'` 增加 `Research Candidate` 徽章（复用既有语义） | §二 / §十四「明确语义误导」 |
| **Fix3** | Lifecycle 标签**中英混用**（`declining` / `early_signal` 回落为原始英文）→ **明确语义错误** | 补齐 product `TimelinePhaseSegment.phase` 的**小写**枚举标签（`early_signal`/`main_rise`/`peak`/`retracement`/`declining`/`ended`），与大写 Research 枚举并存 | §二 / §十四「明确语义错误」 |

**未做**：F1 / F2 / F4 / C3 / C4 **均只记录，未改代码**（避免范围膨胀；F1/F2 需产品设计决策，非本轮可轻改）。

---

## 7. Data Debt（只记录，不修复）

| # | 债务 | 实测 |
|---|---|---|
| **D1** | `campaign_date_observations verified = 0/24` | 仍未验证（本轮**未处理**，符合 §十一） |
| **D2** | 历史案例日期精度 | `C-2019-PHARMA-INNOV` 区间 2019-01-02 ~ 2022-10-31（约 3.7 年）→ 周级比较可用，日级不可 |
| **D3** | Case 的 `phases` 只覆盖 主升/回撤/退潮 | 缺少 早期信号/主题形成/扩散确认（这些只存在于 `signals`）→ 见 C3 |
| **D4** | 交易日历不完整 | 故采用自然周（周一→周日） |
| **D5** | `2020 疫情医疗` / `2021–2022 中医药` 无 `rule_id` 映射（显示 `rule_*` 原始 id） | 属 Research 层既有状态 |

---

## 8. Product Debt（仅真实使用发现）

| # | 项 | 类型 | 优先级 |
|---|---|---|---|
| **P1** | Case 中「证据序列」与「关联事件」重复 | REWORK | **HIGH** |
| **P2** | 「研究归因（四问）」与上两者重复 | REWORK | **HIGH** |
| **P3** | `themeCycleId` 内部 id 直接暴露给用户 | POLISH | MEDIUM |
| **P4** | Case 中 `phases` 与 `signals` 两套阶段未说明关系 | POLISH | MEDIUM |

---

## 9. Research Debt（只记录，不改规则）

| # | 项 |
|---|---|
| **R1** | `event_structure` 在 BCI 的 6 条可见对象中 **6 条 MISMATCH** → 该维度对候选的区分度低（既有结论，**不放宽规则**） |
| **R2** | `Driver MATCH = 1/85`（既有 Quality Backlog，**未放宽**） |
| **R3** | `MERGED` 不可机械判定（Refresh Loop 已记录 limitation） |

---

## 10. No-value Findings（做出来了但实际没用到）

| # | 项 | 实测使用情况 |
|---|---|---|
| **N1** | Case 的「**关联事件**」区块 | 与「证据序列」重复 → 实际只看了证据序列 |
| **N2** | Case 的「**研究归因（四问）**」自由文本 | 与证据序列重复 → 实际未逐条阅读 |
| **N3** | Cycle Map 的「**±2 周迷你条**」 | 修复前全为 0 → 完全未提供信息；修复后仅作「当前年份未纳入研究」的说明 |
| **N4** | SA 的「**逐维依据（Provenance）**」折叠入口 | 实测未展开（默认收起，符合预期，但**实际未使用**） |
| **N5** | Case 的「**代表股票**」 | 研究「结构」时未使用（属个股层面，超出 ThreeC 职责） |
| **N6** | Case 的「**备注 / 信息来源**」 | 未使用（属审计信息） |

> **N1 + N2 是本轮最重要的「无用信息」发现**：三处展示同一批事件，实际只用了其中一处。

---

## 11. 关键问题回答（§十三）

> **在真实使用中，Historical Cycle Map + Structural Analogy 是否让研究路径明显区别于普通的「搜同名历史主题」？**

### ✅ **是，但优势集中在两处**

| 证据 | 说明 |
|---|---|
| **Cycle Map 的 Lifecycle Position** | 实测 `2020` 年窗口：4 个周期分别处于 **主升 / 回撤 / 主升 / 衰减**。搜同名主题只会给出「2020 年有过新能源」，**不会告诉你当时处于什么阶段** |
| **SA 的跨族结构对应** | BCI（医药健康）的 `STRUCTURAL_SUPPORTED` 是 **`C-2023-AD`（汽车 · 智能驾驶）** —— **名称毫无关系**，靠「政策驱动 + 技术突破」机制对应。搜同名主题**永远找不到** |

**反证（优势不成立的情形）**：Cycle Map 的**同族**条目（如 OPTICAL-LINK ↔ 信息通信）与「搜同名主题」结果**基本相同** ——
优势只在**跨族结构对应**与**Lifecycle Position** 两处成立。

---

## 12. Next Action

| 项 | 判定 |
|---|---|
| **Cycle Map（年份分组 + Lifecycle Position）** | **KEEP** |
| **Structural Analogy（机制/证据分层 + 四维 + why/why-not）** | **KEEP** |
| **Historical Case（Header + 证据序列 + 阶段未知明示）** | **KEEP** |
| **Refresh Loop（`--check` + Diff + manifest）** | **KEEP** |
| **Lifecycle 标签 / RC 标识 / 周条空态说明** | **POLISH（本轮已修）** |
| **Case 中「关联事件」+「研究归因」与「证据序列」重复** | **REWORK** |
| **`themeCycleId` 可读性 / `phases` 与 `signals` 关系说明** | **POLISH** |
| **`event_structure` 区分度低 / Driver MATCH 1/85** | **DEFER**（Research Quality Backlog，**不放宽规则**） |
| **`campaign_date_observations` 验证** | **DEFER**（Future Data Precision Debt） |

### ★ 下一步唯一最高优先级

> ## **REWORK：消除 Historical Case 中的三处重复信息**
>
> 把「证据序列」「关联事件」「研究归因（四问）」合并为**一个**证据视图
> （保留时间序 + 阶段 + 类型 + 角色 + 研究归因），
> 使 Case 长度减少约 **2/3**，同时**不丢失任何信息**。
>
> **理由**：这是本轮唯一同时满足「真实使用发现」「影响研究效率」「不涉及 Research 规则变更」的问题。
> 其余项或属 Research 债务（DEFER）、或属设计增强（POLISH），优先级均低于此项。

---

## 13. Gate

> ## ✅ **`PASS`**

| 验收项 | 结果 |
|---|---|
| 完成一轮完整研究路径 | ✅ 三条路径全部走通 |
| 覆盖较早 + 较后阶段候选 | ✅ `THEME_FORMING` + `EXPANSION` |
| 无 BLOCKER | ✅ |
| 代码变更仅限「明确语义问题」 | ✅ 3 项（Fix1/2/3） |
| 未改 Research 规则 / 未新增数据模型 / 未新增算法 | ✅ |
| `refresh --check --snapshot-date 2026-09-15` | ✅ **PASS** |
| 7 个 research validators | ✅ 全 PASS |
| `npm test` / `tsc -b` / `npm run build` | ✅ **558 passed**（15 files；上轮 555 + 新 3）/ exit 0 / PASS |
| build 无新 `>500 kB` warning | ✅ |
| `git status` | ✅ 提交后 clean |

### 本轮修改

| 文件 | 说明 |
|---|---|
| M `src/data/timeline/historicalCase.ts` | Fix3：补齐 product 小写 `LifecyclePhase` 标签 |
| M `src/components/CurrentTimeLens/HistoricalCycleMapSection.tsx` | Fix1：周条空态说明；Fix2：Research Candidate 徽章 |
| M `src/data/timeline/__tests__/historicalCycleMap.test.tsx` | +3 项语义修复回归测试 |
| M `src/styles.css` | `.hcm-rc` / `.hcm-note-warn` |
| M `docs/PROJECT_STATE.md` | HEAD / 阶段 / 下一目标同步 |
| **A** `docs/FIRST_REAL_OBSERVATION_CYCLE_V0_1.md` | 本文档 |

### 本轮**未**修改
Research 规则（Rule Set v0.2）· Structural Analogy Artifact · `current_candidates.json` ·
schema · export contract · 历史数据 · Time Observation

---

*文档结束 · First Real Observation Cycle v0.1 · 2026-09-19*
