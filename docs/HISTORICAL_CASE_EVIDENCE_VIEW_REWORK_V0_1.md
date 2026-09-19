# HISTORICAL_CASE_EVIDENCE_VIEW_REWORK_v0_1

> | 项目 | 值 |
> |---|---|
> | 性质 | **Product Rework**（第一次真实使用后确认的唯一 P1；不是新功能） |
> | 完成日期 | 2026-09-19 |
> | 起始状态 | `HEAD = origin/main = 8ccc487`，ahead/behind `0/0`，工作树 clean（**自行核对**；远程无新增） |
> | **Gate** | **`PASS`** |
> | 未修改 | `research/**` · Research Artifact · Rule Set v0.2 · schema · export contract · 历史数据 · Driver Canonicalization · Time Observation |

---

## 1. Real Observation Finding

来自 `docs/FIRST_REAL_OBSERVATION_CYCLE_V0_1.md`（第一次真实研究使用周期）：

> Historical Case 中**同一批事件被展示了三次** —— 「证据序列」+「关联事件」+「研究归因（四问）」。
> 信息量没有增加，阅读长度显著增加，直接拖慢「继续研究」的效率。

**实测基线（`C-2023-COMM-OPTICAL`）**：

| 区块 | 渲染条目 |
|---|---:|
| 证据序列（按时间） | **5** |
| 关联事件 | **5** |
| 研究归因（四问 · 自由文本） | **12** |
| **合计** | **22** 项 / **仅 5 个事件** |

---

## 2. Before Structure

```
CampaignDetail
├─ Header（历史对象类型 / Macro Theme / Theme Cycle）
├─ 生命周期 · 题材 · 代表股票
├─ 驱动机制（Mechanism Driver）
├─ 证据类别（Evidence Category）
├─ 证据序列（按时间）        ← 5 条事件        ┐
├─ 关联事件                  ← 同一批 5 条事件  ├ 同一批事件 ×3
├─ 研究信号                                   │
├─ 研究归因（四问 · 自由文本） ← 同一批事件 ×12  ┘
└─ 备注 / 信息来源
```

---

## 3. Problem

| # | 问题 |
|---|---|
| **P1** | 「证据序列」与「关联事件」展示**同一批 Event**（仅多一个阶段列） |
| **P2** | 「研究归因（四问）」**第三次**引用同一批 Event / Event Name |
| **P3** | 信息量未增加，阅读长度显著增加 → 直接影响从案例继续研究的效率 |
| **P4** | 三个区块各自为政，用户需要**自行合并**才能看懂「这个案例是怎么演化出来的」 |

---

## 4. Unified Evidence View Design

### 4.1 视图模型（Product View Model，**不写 DB / schema**）

`src/data/timeline/historicalCase.ts`：

```ts
type AttributionPhase = 'START' | 'ACCELERATE' | 'TURN' | 'END' | 'OTHER';

interface HistoricalEvidenceRow {
  key: string;                  // 稳定去重键：`date|name`
  date: string;
  lifecycleStage: string | null;
  lifecycleStageLabel: string;  // 阶段未知 → '阶段未知'
  eventType: string;
  role: string | null;
  name: string;
  attributionPhase: AttributionPhase;
}

interface HistoricalEvidenceTimeline {
  rows: HistoricalEvidenceRow[];          // 按日期升序；**每个事件只出现一次**
  hasEvents: boolean;
  attribution: AttributionGroupView[];    // 四问（阶段级）
  attributionSource: 'RESEARCH' | 'TIME_GROUPING';
  hasUnknownStage: boolean;
}
```

### 4.2 去重实现

`historicalEvidenceTimelineOf(c)` 以 **`date|name`** 为稳定键，重复即跳过 ——
**每个事件只出现一次**，一行承载
`日期 + Lifecycle 阶段 + Event Type + Role + Event Name + 归组阶段`。

### 4.3 展示形式（按时间排序的时间线）

```
历史演化证据
按时间排序，每个事件只展示一次；同一行承载 日期 · 生命周期阶段 · 事件类型 · 角色 · 事件名 · 归组阶段。
归组阶段表示该事件在案例时间轴上的位置，不代表因果证明。

2022-02-17  [阶段未知]  policy · context        其他时间位置   「东数西算」工程正式全面启动…
2023-03-21  [主升]      industry · trigger      启动附近       NVIDIA GTC 2023 主题演讲…
2023-05-24  [主升]      company · catalyst      加速段         NVIDIA FY2024 Q1 财报…
2023-08-28  [主升]      company · catalyst      加速段         中际旭创 2023 年半年报…
2024-04-21  [主升]      company · follow_up     加速段         中际旭创 2023 年年报…

「阶段未知」= 该事件日期不落在任何已记录生命周期区间内（UNKNOWN）—— 不代表事件不存在或不重要。

阶段级研究归因
为什么启动？  启动附近   NVIDIA GTC 2023 主题演讲（EV-COMM-07…）／context：「东数西算」…
为什么加速？  加速段     NVIDIA FY2024 Q1 财报…／中际旭创 2023 半年报…／中际旭创 2023 年报…
为什么转折？  转折附近   2024-10-08 代表标的同步出现阶段高点后回撤…／★ 该回撤后板块重启上行…
为什么结束？  结束附近   unknown（至本地行情窗口末端仍在上行…）／★ 通信设备亦受益…
```

---

## 5. Data Conservation（信息守恒对照）

**基线：`C-2023-COMM-OPTICAL`（真实案例）**

| 项 | Before | After | 结论 |
|---|---:|---:|---|
| **Event 渲染行数** | **10**（证据序列 5 + 关联事件 5） | **5** | **−50%**，每事件只 1 行 |
| 独立区块数 | **3** | **1**（+ 1 个阶段级归因区块） | 三块合一 |
| events 数量 | 5 | **5** | ✅ 不丢 |
| date / eventType / role / name | — | 逐条与 `events` 一致 | ✅ 不变 |
| Lifecycle 映射 | — | 与 `historicalCaseOf()` **完全一致** | ✅ 不变 |
| drivers start / accelerate / turn / end | 2 / 4 / 2 / 2 | **2 / 4 / 2 / 2** | ✅ 内容不丢 |
| 重复 Event | 10 行含 5 组重复 | **0** | ✅ |

**回归断言**（新增测试）：统一视图包含全部原始 Event，且 `date|name` **只出现一次**。

---

## 6. Attribution Semantics（阶段级归因）

- **`campaignDrivers()` 语义完全保留**（未重新设计 Driver 算法）：
  - 有 Research V1.7 `drivers` → **优先原样采用**（每组最多 3 条）
  - 无 `drivers` → 按事件时间窗口归组（每组最多 3 条，trigger/catalyst 优先）
- **归因从「重复事件列表」改为「阶段级研究归因」**：
  四问（为什么启动 / 加速 / 转折 / 结束）+ 阶段标签（启动附近 / 加速段 / 转折附近 / 结束附近）
- **UI 明确声明**：「归因是研究归组 / 研究判断，**不是**单条事件的因果证明」
- **`attributionSource` 区分展示**：`RESEARCH`（V1.7 研究归因）vs `TIME_GROUPING`（时间归组线索）

### 单事件 → 单一归组阶段（§九）

新增 `driverGroupBounds()`（**从 `campaignDrivers()` 抽出，语义完全一致**）供 Product 复用：

```
START       [start−30, start+15]
ACCELERATE  (start+15, peak−7]
TURN        [peak−10, peak+10]
END         [end−25, end+7]     （openEnded → 不归组）
OTHER       其余 → **不强行归因**
```

> **一个 Event → 一个时间位置 → 一个 `attributionPhase`**，不会因视觉需求同时出现在多个阶段。

---

## 7. Lifecycle Semantics（保持不变）

- 阶段**原样来自** Research `phases`（`historicalCaseOf()` 的同一映射）
- 事件日期不落在任何已记录区间 → **`阶段未知`**（虚线 + 灰）
- UI 明确声明：「**不代表**事件不存在或不重要」
- **不把 `UNKNOWN` 转成其他阶段** ✓

---

## 8. Phase / Signal Clarification（消除语义误解）

真实使用发现 `phases`（历史行情阶段）与 `signals`（Research 前置观察标记）是**两套阶段体系**。
本轮**未改 Research 数据**，但在 Case 中增加一句轻量说明：

> **生命周期 = 历史行情阶段（来自 Research `lifecycle`）；研究信号 = Research 层的前置观察标记（来自 `signals`）。两者不是同一套阶段体系。**

---

## 9. Mobile Validation

| 项 | 处置 |
|---|---|
| 长 Event Name | `.hcx-ev-name` `overflow-wrap: anywhere` |
| 长 Driver 文本 | `.hcx-attr-items li` `overflow-wrap: anywhere` + **2 行截断**（`-webkit-line-clamp: 2`），完整文本仍在 `title` |
| 日期 | `font-family: var(--mono)`，固定宽度不换行 |
| Lifecycle chip | `white-space: nowrap` + 外层 `flex-wrap` |
| Event Type / Role | 合并为一个 chip，窄屏字号降至 9.5px |
| 归因行 | 720px 断点下 `grid-template-columns: minmax(0,1fr)`（**单列堆叠**，不再挤压） |
| 时间线宽度 | 左侧 2px 竖线 + 缩进，**不产生横向溢出** |

**结论**：✅ 一条 Event 与其归组阶段在视觉上仍属同一时间结构（同一行 + 同一左边界）。

---

## 10. Performance

| 指标 | 上轮 | **本轮** |
|---|---:|---:|
| 初始 JS | 414.70 kB | **416.59 kB**（+1.89 kB） |
| 初始 JS（gzip） | 146.59 kB | **147.44 kB** |
| SA 懒加载 chunk | 292.45 kB | 292.45 kB（未变，仍按需） |
| 机制懒加载 chunk | 11.25 kB | 11.25 kB（按需） |
| CSS | 50.33 kB | 52.08 kB |
| **`>500 kB` warning** | 无 | ✅ **仍无** |

---

## 11. Tests

```
npm test       → 575 passed（15 files；上轮 558 + 本轮新增 17）
npx tsc -b     → exit 0
npm run build  → PASS，无 chunk >500 kB 警告
```

**新增测试（`historicalCase.test.tsx`，17 项）**：

| 分组 | 覆盖 |
|---|---|
| **去重与信息守恒** | `date\|name` 唯一 · events 数量一致（5）· date/type/role/name 逐条不变 · 按日期升序 · Lifecycle 映射与 `historicalCaseOf` 一致 · 每事件恰一个 `attributionPhase` · 四问内容不丢 · 归因是阶段级而非事件列表 |
| **UNKNOWN 与空态** | 阶段未知保持 `null` 且标签为「阶段未知」· 无事件 → `hasEvents=false` 且 UI 显示 `NOT_AVAILABLE` + 「不代表「当时没有事件」」 |
| **UI 只有一个统一视图** | 存在「历史演化证据」· **旧三块全部消失** · 该标题全页只出现 **1** 次 · 事件行数 = `events` 数 · 四问齐备 · 明示非因果证明 · Phase/Signal 说明已加入 · **另一案例同样适用（无硬编码）** |

**回归**：上轮 558 项全部通过（含 3 项按本轮重构更新的旧断言）。

---

## 12. Gate

> ## ✅ **`PASS`**

| 验收项 | 结果 |
|---|---|
| 每个历史事件只展示一次 | ✅ `date\|name` 去重，事件行 10 → 5 |
| 信息不减少 | ✅ events / date / type / role / Lifecycle / drivers 全部保留 |
| 不是「三个 section 塞进一个 section」 | ✅ 旧三块**全部移除**，旧 helper 仅保留非 UI 调用 |
| `campaignDrivers()` 语义保留 | ✅ 抽出 `driverGroupBounds()`，规则未变 |
| 一 Event → 一 attributionPhase | ✅ `OTHER` 表示不强行归因 |
| Research Attribution 保留为阶段级 | ✅ 四问 + 阶段标签，明示非因果证明 |
| UNKNOWN 语义不变 | ✅ `阶段未知` + 说明，未转成其他阶段 |
| Phase / Signal 说明 | ✅ 已加入 |
| Mobile 无横向溢出 | ✅ |
| 旧三块不再渲染 | ✅ 测试断言 |
| 真实案例回归（`C-2023-COMM-OPTICAL`） | ✅ 5 条事件仍 5 条，无第二/第三份列表 |
| 另一案例无硬编码 | ✅ `C-2019-COMM-5G` |
| `npm test` / `tsc -b` / `npm run build` | ✅ 575 passed / exit 0 / PASS |
| build 无新 `>500 kB` warning | ✅ |
| Research 内容字节级不变 | ✅ `research/**` 零改动 |

### 本轮修改

| 文件 | 说明 |
|---|---|
| M `src/data/timeline/timelineAdapter.ts` | 抽出 `driverGroupBounds()`（**语义完全一致**，供 Product 复用） |
| M `src/data/timeline/historicalCase.ts` | 新增 `historicalEvidenceTimelineOf()` + `AttributionPhase` + `PHASE_SIGNAL_CLARIFICATION` |
| M `src/components/CampaignDetail/CampaignDetail.tsx` | **删除**「证据序列」「关联事件」「研究归因（四问）」三块；**新增**「历史演化证据」+「阶段级研究归因」；Phase/Signal 说明 |
| M `src/data/timeline/__tests__/historicalCase.test.tsx` | +17 项；更新 3 项旧断言 |
| M `src/styles.css` | `.hcx-ev-*` / `.hcx-attr-*` / `.hcx-phase-signal` + 720px 断点 |
| M `docs/PROJECT_STATE.md` | 下一目标同步 |
| **A** `docs/HISTORICAL_CASE_EVIDENCE_VIEW_REWORK_V0_1.md` | 本文档 |

### 本轮**未**修改
`research/**` · Research Artifact · Rule Set v0.2 · schema · export contract · 历史数据 ·
Driver Canonicalization · Time Observation · Structural Analogy 规则

---

## 13. 成功标准对照

| 目标 | 结果 |
|---|---|
| **信息不减少** | ✅ events / 日期 / 类型 / 角色 / Lifecycle / drivers 全保留 |
| **事件不重复** | ✅ 事件渲染行 **10 → 5**（−50%），`date\|name` 唯一 |
| **阅读长度下降** | ✅ 独立区块 **3 → 1**；旧「关联事件」整块移除；归因文本 2 行截断（完整文本保留在 `title`） |
| **更快看懂「怎么演化出来的」** | ✅ 单一时间线：日期 → 阶段 → 类型/角色 → 事件名 → 归组阶段，一次读完 |

> ⚠️ **诚实说明**：文本总长度下降幅度**小于**「三块合一」的直觉预期 ——
> 因为 Research V1.7 的归因自由文本（12 条）按 §七 要求**必须保留**。
> 真正的收益在**结构**（3 块 → 1 块、事件行 −50%）与**视觉**（2 行截断 + 单列移动端布局）。

---

*文档结束 · Historical Case Evidence View Rework v0.1 · 2026-09-19*
