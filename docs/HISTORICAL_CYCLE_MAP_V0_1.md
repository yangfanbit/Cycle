# HISTORICAL_CYCLE_MAP_v0_1

> | 项目 | 值 |
> |---|---|
> | 性质 | **产品体验**（周级时间窗口浏览；不新增 Research 能力） |
> | 完成日期 | 2026-09-19 |
> | 起始状态 | `HEAD = origin/main = 6dfb4b7`，ahead/behind `0/0`，工作树 clean（**自行核对**；远程无新增，已在同步状态） |
> | **Gate** | **`PASS`** |
> | 未修改 | `research/**` · Rule Set v0.2 · Structural Analogy Artifact · schema · export contract |

---

## 1. Product Problem

ThreeC 此前已完成：

```
Current Time → Current Candidate → Structural Analogy → Historical Case → Case Experience
```

但**缺少横向观察**：用户只能从「当前候选」出发看**结构对应**，无法回答

> **「现在这一周，在历史上有没有出现过类似的周期窗口？」**

本轮补齐这一环：以**周级分辨率**建立「当前时间窗口 ↔ 历史时间窗口」的横向浏览，
并让用户发现有价值的案例后进入**已有** Historical Case。

**与 Structural Analogy 的分工（不得合并）**：

| 视角 | 回答 | 性质 |
|---|---|---|
| **Historical Cycle Map** | 现在这一周，历史上有没有类似的周期窗口？当时走到哪一步？ | **时间窗口浏览** |
| Structural Analogy | 当前结构与历史结构在哪些维度对应？ | **正式结构对应** |
| Lifecycle Lens | 历史上谁处于类似生命周期阶段？ | 历史阶段浏览 |
| Calendar Lens | 这个时间附近历史上发生过什么？ | 时间邻近浏览 |

---

## 2. Week-level Time Model（正式定义）

> **ThreeC 的观察分辨率 = 周级（week-level），不是日级。**

| 项 | 定义 |
|---|---|
| 交易周 | **周一 → 周日**（`weekWindowOf`）；`marketTodayISO` 的 Asia/Shanghai 基准 |
| 周标签 | ISO-8601（如 `2026-W38`），**仅用于展示，不用于排序** |
| 窗口锚点 | 周三（周中）—— 用于「同一周」的跨年映射 |
| 历史映射 | 保留**月-日**、仅替换年份（`calendarWindowInYear`）；跨年周**截断到年内** |
| 日期用途 | **只用于排序与窗口相交** —— **不制造虚假的日期精确度** |

**实测**（`today = 2026-09-16`）：当前周 = `2026-09-14 ~ 2026-09-20` · 标签 `2026-W38`。

---

## 3. Calendar Window（维度一）

回答：**「历史上同一时期发生了什么？」**

- 默认窗口：**当前周 ± 2 周**（共 **5** 周，偏移 `−2 … +2`）
- 每周年内窗口 = 该年同月-日区间（如 2019-09-14 ~ 2019-09-20）
- 纳入条件：**Campaign 区间与窗口相交**（`c.start ≤ win.end 且 c.end ≥ win.start`）
  → **不要求精确日期**；长周期（跨年）同样纳入

**UI**：「当前交易周」+ 5 周迷你条（当前周高亮 + 各周周期数）。

---

## 4. Lifecycle Position（维度二）

回答：**「历史案例在这个时间点走到了哪一步？」**

- **不重新定义 Lifecycle**：阶段**原样来自** Research `phases`（`timeline_export_v1`）
- 锚点：窗口中心若落在案例区间内 → 用**窗口中心**；否则用**重叠起点**（保证在案例内）
- 三态：

| `stageStatus` | 含义 |
|---|---|
| `IN_WINDOW` | 窗口锚点落在某阶段内 |
| **`ENTERED_IN_WINDOW`** | 案例在**本窗口内开始** → UI 标注「**本窗口内开始**」（即「这一时期刚进入」） |
| `UNKNOWN` | 窗口锚点**不落在任何已记录阶段区间内** → 显示 `UNKNOWN` 并说明**不是**「没有阶段」 |

---

## 5. Historical Cycle Map（UI）

位置：**Current Time Lens 内**（Current Candidate 之后、Calendar Lens 之前），**不新增 Dashboard**。

```
Historical Cycle Map（历史周期地图）        [周级 · 时间窗口浏览]
├─ 当前交易周  2026-W38   2026-09-14 ~ 2026-09-20
│  └─ [−2周][−1周][本周][+1周][+2周]   ← 各周「N 个周期」
├─ 筛选：Macro Theme / Theme Cycle / Lifecycle   ← **筛选，不是排序**
└─ 历史时间窗口（按年份升序）
   └─ 2019  2019-09-14 ~ 2019-09-20   3 个周期
      ├─ 汽车 · 智能驾驶  [汽车][auto_intelligence_2023][主升]  查看历史案例 →
      │  └─ 横向 span（案例在窗口中的位置；**不是分数**）
      └─ …
```

每个历史案例显示：**Campaign 名称 · 年份 · Macro Theme · Theme Cycle · Lifecycle 阶段**，并可点击进入 Historical Case。

**信息量控制**：第一眼看结构（当前周 + 5 周条）→ 第二眼看案例（年份分组，默认前 4 个年份，可「显示全部」）→ 第三眼进入细节。

---

## 6. Navigation

**两条入口都成立**（§十）：

```
① Historical Cycle Map → 发现历史案例 → Historical Case → 值得进一步研究 → Structural Analogy
② Current Candidate → Structural Analogy → Historical Case → 继续横向查看 → Historical Cycle Map
```

- 点击 Cycle Map 条目 → `onSelect({ kind: 'campaign', id })` —— **复用既有 Campaign Detail 入口**，未新建导航模型
- Historical Case 已具备「← 返回 Structural Analogy」；关闭后 `CurrentTimeLens` **始终挂载** → 返回 Current Time Lens 时**上下文不丢**
- **不新建平行的数据模型**：Cycle Map 只消费既有 `TimelineDataSource`

---

## 7. Mobile UX

| 项 | 处置 |
|---|---|
| 5 周迷你条 | `grid-template-columns: repeat(5, minmax(0,1fr))`；720px 断点缩小 padding / 字号 |
| 横向时间轴（span） | 相对定位 + 百分比宽度，**不产生横向滚动** |
| 长 Campaign 名 | `.hcm-entry-title` 加 `overflow-wrap: anywhere` |
| 多案例 | 年份分组 + 默认前 4 个年份 + 「显示全部」；**不做算法排序** |
| Lifecycle label | chip 形式，`white-space: nowrap` + 外层 `flex-wrap` |
| 筛选 | 720px 断点下标签独占一行（`min-width: 100%`） |
| 点击 / 返回 | 条目整块可点（`button` 全宽）；关闭后回到 Current Time Lens |

**结论**：✅ 结构可用，**无横向溢出**。

---

## 8. Performance

| 指标 | 上轮 | **本轮** |
|---|---:|---:|
| 初始 JS | 406.08 kB | **413.89 kB**（+7.81 kB） |
| 初始 JS（gzip） | 143.75 kB | **146.34 kB** |
| SA 懒加载 chunk | 292.45 kB | **292.45 kB（未变，仍按需）** |
| 机制懒加载 chunk | 11.25 kB | 11.25 kB（按需） |
| CSS | 45.56 kB | 49.79 kB |
| **`>500 kB` warning** | 无 | ✅ **仍无** |

**合规**：静态 PWA · 无外部 API · 无运行时 LLM · 无 Research runtime ·
SA artifact **继续按需加载** · **未新增任何 Research 数据**（全部复用现有 export）。

---

## 9. Data Limitations

| 项 | 说明 |
|---|---|
| 窗口为**周级近似** | 历史年份的「同一周」按**月-日**平移，**不声称**与历史自然周完全对齐 |
| 跨年周 | 截断到年内（`01-01` 起） |
| 阶段未知 | 窗口锚点不落在任何已记录 `phases` 区间内 → `UNKNOWN`（**不是**「没有阶段」） |
| `campaign_date_observations` | **0/24 verified** —— 本轮**不阻塞**（周级视图不依赖日级核验） |
| 事件精确时间 | 属 Optional，本轮不使用 |

**本轮只做轻量完整性检查**：窗口相交一致性 · 生命周期顺序（`phases` 由 Research 保证）·
identity 非空 · navigation id 有效 —— **未做逐来源人工式日期验证**。

---

## 10. Future Data Precision Debt（不阻塞本轮）

| # | 债务 |
|---|---|
| 1 | `campaign_date_observations` 深度验证（当前 `verified = 0/24`） |
| 2 | Source-level historical fact verification |
| 3 | 更精细时间边界（日级窗口 / 事件级锚定） |
| 4 | 交易日历完整性（当前不完整，故采用自然周） |

---

## 11. Test Results

```
npm test       → 547 passed（14 files；上轮 510 + 本轮新增 37）
npx tsc -b     → exit 0
npm run build  → PASS，无 chunk >500 kB 警告
```

**新增测试（`src/data/timeline/__tests__/historicalCycleMap.test.tsx`，37 项）**：

| 分组 | 覆盖 |
|---|---|
| 周级时间模型 | 周一→周日 · 周内任意日同周 · ISO 标签 · **跨年周** |
| 当前周 ± 2 周 | `weeksAround` 5 窗口 · 偏移日期 · 地图含 5 周且仅 1 个 offset=0 |
| 日历窗口 | 保留月-日 · 跨年截断（`start ≤ end` 且同年） |
| 案例进入窗口 | 年份分组覆盖全研究年 · 相交验证 · 命中/未命中具体案例 · 时间序 · 字段完整 |
| Lifecycle Position | 阶段来自 phases · `UNKNOWN` 语义 · `ENTERED_IN_WINDOW` · 三态 |
| 日期精度边界 | 只要求相交 · 空数据源不抛错 · 无阶段 → `UNKNOWN` |
| 筛选 | 保持顺序 · Macro Theme / Lifecycle 筛选 · facets 去重稳定 |
| span | 0..1 且宽度为正 |
| UI | 首屏三问 · 5 周条 · 可点击 · 阶段标签 · `UNKNOWN` 独立视觉 · 明示周级/不排序/不评分 · 无 score/ranking/概率/预测/最强/最像 · 移动端结构 |
| 集成 | Current Time Lens 含 Cycle Map 且既有区块未替换 · `onSelect` kind = campaign |

**回归**：上轮 510 项全部通过（含 SA 43 项 · Historical Case 29 项 · 旧 Current Candidate · Calendar / Lifecycle）。

---

## 12. Gate

> ## ✅ **`PASS`**

| 验收项 | 结果 |
|---|---|
| 当前交易周计算 | ✅ 周一→周日 + ISO 标签 + 跨年 |
| 当前周 ± 2 周窗口 | ✅ 5 窗口 |
| 历史 Campaign 正确进入对应窗口 | ✅ 相交判定，实测命中/未命中 |
| Lifecycle 映射正确 | ✅ 原样来自 `phases`；`ENTERED_IN_WINDOW` 表达「刚进入」 |
| 不因 exact date 缺失导致案例消失 | ✅ 只要求窗口相交 |
| Historical Case navigation | ✅ 复用既有 `onSelect` |
| 返回 Current Time Lens | ✅ Lens 始终挂载，上下文不丢 |
| Mobile layout | ✅ 无横向溢出 |
| UNKNOWN / NOT_AVAILABLE 不被误认为不存在 | ✅ 独立视觉 + 明示 |
| `npm test` / `tsc -b` / `npm run build` | ✅ 547 passed / exit 0 / PASS |
| build 无新 `>500 kB` warning | ✅ |
| Research / export / schema 无变化 | ✅ `git status` 为空 |
| **不排序 / 不评分 / 不预测** | ✅ 仅筛选 + 时间序 |

### 本轮修改

| 文件 | 说明 |
|---|---|
| **A** `src/data/timeline/historicalCycleMap.ts` | 周级时间模型 + Calendar Window + Lifecycle Position + 筛选 + span |
| **A** `src/components/CurrentTimeLens/HistoricalCycleMapSection.tsx` | Cycle Map UI |
| **A** `src/data/timeline/__tests__/historicalCycleMap.test.tsx` | 37 项测试 |
| **A** `docs/HISTORICAL_CYCLE_MAP_V0_1.md` | 本文档 |
| M `src/components/CurrentTimeLens/CurrentTimeLens.tsx` | 在 Current Candidate 之后、Calendar Lens 之前接入 |
| M `src/styles.css` | `.hcm-*` 样式 + 720px 断点 |

### 本轮**未**修改
`research/**` · Rule Set v0.2 · Structural Analogy Artifact · schema · export contract ·
`currentSimilarity.ts` · `historicalSimilarPhase.ts` · `OpportunityRadar`

---

## 13. 完成后的产品路径

```
「现在这一周在哪里」
    ↓  Historical Cycle Map · 当前交易周 + ±2 周
「历史上这一周附近发生过哪些周期」
    ↓  按年份分组的 Calendar Window
「这些周期在当时分别处于什么阶段」
    ↓  Lifecycle Position（含「本窗口内开始」）
「哪个案例值得继续看」
    ↓  筛选（Macro Theme / Theme Cycle / Lifecycle）—— **不是算法排序**
「点击进入 Historical Case」
    ↓  复用既有 Campaign Detail
「再进一步通过 Structural Analogy 理解当前与历史的结构对应」
```

---

*文档结束 · Historical Cycle Map v0.1 · 2026-09-19*
