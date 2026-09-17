# Historical Coverage Audit v0.2

> | 项目 | 值 |
> |---|---|
> | 文件性质 | **Research Layer Deliverable**（研究层交付物） |
> | 轮次 | `historical-coverage-audit-v0.2` |
> | 规则集 | `historical-coverage-audit-0.2` |
> | 快照日期 | 2026-09-17 |
> | 生成器 | `research/scripts/audit_historical_coverage.py --round 0.2`（deterministic，`--check` 逐字节一致） |
> | 输入（只读） | `exports/timeline_export_v1.json` + `research/database/cycle_research.db` + `research/current/current_candidates.json` |
> | 产物 | `historical_coverage_matrix_v0_2.json` / `.csv` |
> | **未修改** | `src/` · Timeline · `exports/` 契约 · `contracts/` · `schema.sql` · Product Artifact |
>
> **与 v0.1 的关系**：本报告是 **Wave 1A（电力设备历史 Cycle）之后**的覆盖度快照。
> v0.1（`Historical_Coverage_Audit_v0_1.md` + `historical_coverage_matrix_v0_1.*`）是**Wave 1A 之前**的快照，
> **原样保留、未覆盖**。v0.1 的 `--check` 现与重算结果不一致 —— 这是**快照的预期行为，不是回归**。

---

## 0. 一句话结论

> **Wave 1A 把历史侧 Macro Theme 从 2 个推到 3 个，电力设备的断裂已修复；**
> **但 `theme_family_count` 仍 < 4（跨族稳健性仍不能通过），日期核验仍为 0/24 —— 瓶颈依旧在数据，不在方法。**

---

## 1. Dataset

| 项目 | v0.2（本轮） | v0.1（上轮） | Δ |
|---|---:|---:|---:|
| Campaigns（DB = export） | **11** | 9 | +2 |
| Research Candidates | 4 | 4 | 0 |
| **Theme Cycles** | **11** | 9 | **+2** |
| **Macro Themes（历史侧）** | **3** | 2 | **+1** |
| Themes（全部） | 16 | 12 | +4 |
| 孤立 theme | 2 | 2 | 0 |
| Lifecycle 记录（DB `campaign_phases`） | 36 | 23 | +13 |
| Evidence | **67** | 51 | **+16** |
| Events（DB / export） | 39 / 42 | 30 / 33 | +9 / +9 |
| Years | 2019–2025（有效 7 年） | 同 | — |
| **已完成核验的日期** | **0 / 24** | 0 / 24 | **0** |
| Market series | 48 | 40 | +8 |
| market_daily 行数 | 48,772 | 31,816 | +16,956 |
| trading_calendar | 371 行（2022-03 ~ 2024-09） | 同 | — |

**Lifecycle 评级**：`COMPLETE 5 / PARTIAL 9 / SPARSE 1 / UNKNOWN 0`（共 15 个对象；v0.1 为 3 / 9 / 1）。

---

## 2. Macro Theme Coverage

| Macro Theme | Theme Cycles | Campaigns | RC | Years | Lifecycle 阶段 | Evidence | Events | Securities | Status |
|---|---:|---:|---:|---|---:|---:|---:|---:|---|
| `TH-AUTO` 汽车 | 8 | 8 | 1 | 2019–2025 | **10 / 10** | 39 | 19 | 23 | `COVERED` |
| `TH-PHARMA` 医药健康 | 1 | 1 | 2 | 2019–2021 | 7 / 10 | 5 | 4 | 3 | `COVERED` |
| **`TH-POWER` 电力设备** | **2** | **2** | 0 | **2020 · 2022** | **9 / 10** | **16** | **8** | **8** | **`COVERED`** |

**`TH-POWER` 的两个 Cycle**：
- `power_ne_equipment_2020_2022` — 双碳驱动的清洁能源发电设备重估（Peak 2021-10-27~11-04）
- `power_grid_uhv_2022_2025` — 电网投资与特高压第四轮建设（Peak 2024-07-09~10-14）

**唯一缺失阶段**：`FIRST_DECLINE`（全库仅 1 例）→ 写 UNKNOWN，**未猜**。

---

## 3. Domain Coverage

| 领域 | v0.2 | v0.1 | 说明 |
|---|---|---|---|
| 汽车 | `COVERED_WITH_CYCLES`（8 Cycle） | 同 | 不变 |
| 新能源（车用电池） | `COVERED_WITH_CYCLES`（3 Cycle） | 同 | **是汽车族子集，不贡献独立主题族** |
| 医药 | `COVERED_SINGLE_CYCLE`（1 Cycle） | 同 | 不变 |
| **电力设备** | ✅ **`COVERED_WITH_CYCLES`（2 Cycle / 2020·2022）** | ❌ `ABSENT` | **Wave 1A 修复** |
| 信息通信 | ❌ `ABSENT` | ❌ `ABSENT` | Wave 1B 待做 |
| 高端装备 | ❌ `ABSENT` | ❌ `ABSENT` | Wave 1C 待做 |
| 消费 | ⚠️ `SCATTERED_ONLY` | 同 | 仍仅为名称匹配，无独立 Cycle |
| 其余 13 个领域 | ❌ `ABSENT` | 同 | 数据库无记录 |

---

## 4. Evidence Coverage

| canonical 类别 | v0.2 | v0.1 | Δ |
|---|---:|---:|---:|
| `market`（行情） | 33 | 31 | +2 |
| `industry`（行业） | 18 | 11 | +7 |
| `policy`（政策） | 13 | 8 | +5 |
| `information`（信息/媒体） | 3 | 1 | +2 |
| **`company`（公司）** | **0** | **0** | **0** |
| **`capital`（资金）** | **0** | **0** | **0** |
| `UNCLASSIFIED` | 0 | 0 | 0 |

> **`company` 与 `capital` 仍完全缺失** → Phase Evidence Matrix 的公司 / 资金维度**仍无法派生**。
> **`evidence_type` 中英文混用仍未统一**（v0.1 的 P1 项，本轮未做）。
> 本轮新增 16 条证据**全部落在既有可归一化取值**内，**未扩 schema**。

---

## 5. Event Coverage

**DB 分布**：`policy` 22 · `company` 12 · `market` 4 · **`industry` 1**（v0.1 为 0）。

- **`industry` 类型首次使用**（Wave 1A 的「沙戈荒外送特高压开工」）。
- `NOT_AVAILABLE` 由 **7 类降为 6 类**（`industry` 移出）。
- 仍缺：`holiday` · `data_release` · `reporting` · `meeting` · `trade_fair` · `product`。
- **未新增任何 `event_type`** —— 沿用 schema 既有枚举。

---

## 6. Market Data Coverage

- 48 条 series：**连续 1**（`SH000300`）· **窗口采样 22** · **空占位 6** · 股票 39 · 指数 5。
- **仍为「按 Campaign 窗口采样」，不是连续时间序列。**
- **电力设备行业指数代理不可得**（相关 ETF 均晚于本轮窗口成立）→ 未补，如实记录。
- `trading_calendar` **仍为 371 行（2022-03 ~ 2024-09）**，未补全。

---

## 7. Verification Coverage

| 项目 | v0.2 | v0.1 |
|---|---:|---:|
| `campaign_date_observations` 总数 | 24 | 24 |
| `verified_date` 非空 | **0** | 0 |
| `confidence = low` | **24 / 24** | 24 / 24 |

> ⚠️ **本轮新增 2 个 Cycle / 36 条 DB phases，却未增加任何核验** ——
> **核验缺口被放大**，这是本轮最需要正视的负面结论。
> 核验仍是 audit 认定的「**数据可信度硬天花板**」，也是产品必须永远带「探索性」标记的直接原因。

---

## 8. Coverage Ceiling

```
theme_family_count = 3   （跨族稳健性检验门槛为 ≥ 4）
```

| 解锁项 | 条件 | 当前 |
|---|---|---|
| 跨族稳健性 | `theme_family_count ≥ 4`（还需 **1** 个独立 Macro Theme） | ❌ 3 |
| 稳定规律档位 | 有效观测 ≥ 8 年 | ❌ 7 年 |
| Structural Analogy | 补录当前侧已声明但无历史者 | ⏳ **仅剩 信息通信 / 高端装备** |

**当前侧 vs 历史侧**：

| 侧 | Macro Theme | 数量 |
|---|---|---:|
| Current Candidate | 医药健康 · **电力设备** · 信息通信 · 高端装备 | 4 |
| 历史研究 | 汽车 · 医药健康 · **电力设备** | 3 |
| **仍断裂** | **信息通信 / 高端装备** | **2**（原为 3） |

---

## 9. Research Capability Matrix

| 能力 | 状态 | 主要限制 |
|---|---|---|
| Time Observation | `PARTIAL` | `theme_family_count = 3`（门槛 ≥ 4）；有效观测仅 7 年 |
| Seasonal | `BLOCKED` | 无终端需求季节性数据；无连续行情序列做中性基准 |
| Calendar-driven | `PARTIAL` | 无制度性日历结构化数据；机制解释多为 post-hoc |
| Event-driven | `BLOCKED` | 仍无结构化行业事件日历 → 事件样本不足以支撑 Pattern |
| Phase Transition | `LIMITED` | 阶段迁移节奏 = EARLY_SIGNAL 聚集 + 典型时长 → 无独立信息 |
| **Structural Analogy** | `BLOCKED` | 历史侧 3 个 Macro Theme；**仍无历史者：信息通信 / 高端装备** |

> **`Structural Analogy` 仍为 `BLOCKED`（不是 `PARTIAL`）** ——
> 4 个当前候选中仍有 2 个（`CC-2026-OPTICAL-LINK` / `CC-2026-EMBODIED-AI`）无同名历史 cycle。
> 电力设备的 2 个候选已解锁，但这不足以让整体能力跨档。**这是保守判定，不是漏报。**

---

## 10. Priority Framework（数据建设优先级，**不是投资价值排名**）

| 排名 | 领域 | 总分 | 当前侧需求 | 状态 |
|---:|---|---:|---|---|
| 1 | 电力设备 | 24 / 24 | `CC-2026-COMPUTE-POWER` · `CC-2026-OFFSHORE-WIND` | ✅ **已完成（Wave 1A）** |
| 2 | 信息通信 | 23 / 24 | `CC-2026-OPTICAL-LINK` | ⏳ **下一步候选** |
| 3 | 高端装备 / 机器人 | 20 / 24 | `CC-2026-EMBODIED-AI` | ⏳ Wave 1C |
| 4 | 半导体 / 电子 | 24 / 24 | — | Wave 2 |
| 5 | 金融 / 地产 | 21 / 24 | — | Wave 2 |
| 6 | 有色 / 资源 / 化工 | 20 / 24 | — | Wave 2 |
| 7 | 消费 | 20 / 24 | — | Wave 2 |
| 8 | 军工 | 19 / 24 | — | Wave 2 |

---

## 11. Data Risks

| 严重度 | 风险 | 说明 |
|---|---|---|
| HIGH | 样本量不足（有效观测仅 7 年） | N ≤ 7，达不到 N ≥ 8 |
| HIGH | **主题族数量 = 3（未达 ≥ 4）** | 跨族稳健性仍不可能通过（Wave 1A 已由 2 → 3） |
| HIGH | **日期核验为 0** | 全部 `verified_date = NULL`，全部 `confidence = low` |
| HIGH | 幸存者偏差无法消除 | 无「主题级未成势」负样本 |
| HIGH | **当前侧声明 4 个，历史侧 3 个** | 信息通信 / 高端装备 仍无历史 Cycle |
| MEDIUM | 行情为「窗口采样」而非连续序列 | 空占位 6 条；年度活跃 series 数逐年衰减 |
| MEDIUM | Event Calendar 缺 6 类能力关键事件 | 两类 Pattern 无法研究 |
| MEDIUM | Evidence 口径不统一（中英文混用） | 统计前须归一化 |
| MEDIUM | taxonomy 缺口 | 1 个 Campaign 未挂接 Macro Theme；2 个孤立 theme；export 独有 theme `华为汽车` |
| MEDIUM | 生命周期普遍不完整 | 15 个对象中仅 5 个 COMPLETE |

---

## 12. 本轮对生成器的两处修正（**只改叙述与探针，不改统计量**）

> v0.2 是本审计的**第一次多轮运行**。过程中发现生成器内有两处**按 v0.1 数据快照写死**的内容，
> 若不修正，v0.2 产物会与**它自身的数据**自相矛盾。两处均已修正，且**未改变任何统计量**。

### 12.1 叙述文本写死（已改为派生）

`CAPABILITY_MATRIX` / `data_risks` / `coverage_ceiling.statement` 中若干数字为 v0.1 的实测值，例如：

| 位置 | 修正前（v0.1 文本） | 修正后（派生） |
|---|---|---|
| Time Observation blocker | 「theme_family_count 上限 = 2」 | 「theme_family_count = **3**（门槛 ≥ 4）」 |
| Structural Analogy blocker | 「历史侧仅 2 个…3 个主题无历史可类比」 | 「历史侧 **3** 个…仍无历史者：**信息通信 / 高端装备**」 |
| Phase Transition unlock_by | 「当前仅 1/13 达 COMPLETE」 | 「当前 **5/15** 达 COMPLETE」 |
| Event-driven evidence | 「事件表无 industry / holiday 类型」 | 「industry **已启用（1 条）**、holiday 仍为 0 条」 |
| data_risk 标题 | 「主题族上限 = 2」 | 「主题族数量 = **3**（未达 ≥ 4）」 |
| data_risk 标题 | 「Event Calendar 缺 3 类」 | 「Event Calendar 缺 **6** 类」（派生自 `not_available_count`） |

新增函数 `_patch_derived_notes(art)` 在写盘前就地修正这些叙述，
并改为把 `CAPABILITY_MATRIX` 的**副本**放进产物（避免污染模块级常量）。

### 12.2 `DOMAIN_PROBES` 写死 theme_id（已改为名称精确匹配）

`DOMAIN_PROBES` 中「电力设备」的 `theme_ids` 为 **空列表**（v0.1 时该主题尚不存在），
导致 v0.2 一度把电力设备报成 `SCATTERED_ONLY`（0 Campaign）—— **与自身数据矛盾**。

修正：按**主题名称精确匹配**动态补入 `theme_id`。
- 精确匹配（非子串）是刻意的 —— 否则「消费」会误命中「汽车消费/购置税刺激」。
- 实测影响面**仅限电力设备**：`消费` 仍为 `SCATTERED_ONLY`，其余领域状态不变。

---

## 13. 诚实限制

1. 本审计的优先级框架含 **JUDGMENT** 成分（8 维中 6 维为研究判断），**不是纯数据推导的排序**。
2. `macro_theme_matrix` 用 `resolved`（沿 parent 链）口径；`theme_cycles` 用 export 的 `theme_cycle_id`。
3. Event Coverage 的 `NOT_AVAILABLE` 只表示「数据库无记录」，**不表示机制不存在**。
4. Lifecycle 评级是启发式规则，**未补齐任何缺失阶段**。
5. `evidence_type` 归一化映射是人工定义的；若未来统一口径，映射表应同步更新。
6. 行情 `sampling_class` 判据为「年度跨度」，不评价数据质量或复权正确性。
7. **v0.1 的 `--check` 现为 FAIL**（数据已前进）；这是快照的预期行为，**不是回归**。
8. 本审计**只读**，未修改任何 DB / schema / export / 产品代码。

---

## 14. 下一步

> **进入 Wave 1B（信息通信）** 是自然的下一步 —— 它同时服务 `CC-2026-OPTICAL-LINK`
> 并把 `theme_family_count` 推到 4（跨族稳健性门槛）。
>
> 但**建议先做一件成本更低的事**：**人工核验日期**（当前 0/24）。
> 理由：Wave 1A 把 Cycle 数从 9 推到 11、DB phases 从 23 推到 36，
> 却**没有增加任何核验** —— 可信度缺口在被放大，而这是 audit 反复认定的**硬天花板**。
>
> 两者不冲突：核验是数据质量工作，Wave 1B 是覆盖度工作。**由用户决定顺序。**

---

*报告结束 · Historical Coverage Audit v0.2 · 2026-09-17 · Wave 1A 之后*
