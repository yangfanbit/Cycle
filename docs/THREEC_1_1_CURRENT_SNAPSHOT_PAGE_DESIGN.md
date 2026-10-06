# THREEC_1_1_CURRENT_SNAPSHOT_PAGE_DESIGN.md

> | 项目 | 值 |
> |---|---|
> | 性质 | **页面设计（Design）** —— ThreeC 1.1 Phase 1.3 |
> | 日期 | 2026-10-06 |
> | 上游 | `docs/MARKET_SNAPSHOT_CONTRACT_v0.3.md` · `docs/THREEC_1_1_MARKET_SNAPSHOT_ARCHITECTURE.md` · `docs/MONTHLY_RESEARCH_RUNBOOK.md` |
> | 数据 | `research/current/market_snapshots/`（快照 + index）· `src/data/marketSnapshot/snapshotDiff.ts` |

---

## 1. 这一页回答什么

> **「跟上一次比，变了什么？现在该研究什么？」**

**不回答**：明天买什么 · 未来走势 · 哪个更好。

**用户画像**：一个月打开一次的研究者。

## 2. 核心设计判断（三条）

### 判断 1 · 主角是「变化」，不是「状态」
月度节奏下用户关心增量。因此页面**第一屏就是 diff 摘要**（本期 N 处变化），
而不是把当前状态铺开。「无变化」也要**明确说出来**（那本身是信息）。

### 判断 2 · 「无对应」是一等公民
实测：395 条结构比对里 `NO_VALID_CORRESPONDENCE` = **225 条（57%）**，
真正「有结构对应」的只有 45 条（11%）。

**这不是缺陷，是 ThreeC 的立身之本** —— 市面上的「主题相似」工具做的是名字匹配，
ThreeC 说的是「看起来像 ≠ 结构上成立」。因此：

- 「无有效对应」必须**有自己的呈现**（不是一个灰色空态）；
- 每条都要能回答**「为什么不对应」**（`why_not_similar`）；
- 并给出**「还缺什么证据才能改变结论」**（研究问题）。

### 判断 3 · 首页不变，本页进钻取区
首页 1.1.2 的既定原则是「**首页是地图，不是数据库**」。
因此本期快照作为**钻取区的第一个入口**，不抢占首页第一视觉；
但折叠标题上直接显示摘要（`DRAFT · 与上期比 0 处变化`），**不展开也能看到关键信息**。

## 3. 页面结构

```
┌ 本期研究快照（Current Snapshot）  [状态徽章] [快照日] ────────────┐
│                                                                  │
│  ① 与上期比（diff 摘要）      ← 主角，第一屏                      │
│     环境 n · 对象 n · 候选 n · 观察 n      或「本期无变化」        │
│                                                                  │
│  ② 当前市场环境（market_regime）                                  │
│     四维 + beta_note；UNKNOWN 必须显示「为什么不知道」             │
│                                                                  │
│  ③ 研究对象（research_objects）                                   │
│     每个对象：名称 / 阶段 / 解析状态 / 驱动机制 / 证据类别         │
│                                                                  │
│  ④ 历史结构候选（historical_candidates）  ← 含「无对应」一等公民   │
│     按研究对象分组；每组先给状态分布（含 NO_VALID 计数）           │
│                                                                  │
│  ⑤ 观察（observations）                                           │
│                                                                  │
│  ⑥ 研究声明（research_context + known_limitations）               │
└──────────────────────────────────────────────────────────────────┘
```

## 4. 状态与门禁（硬约束）

| 状态 | Product 是否展示 |
|---|---|
| `CANONICAL` | ✅ 默认展示 |
| `DRAFT` / `REVIEW` | ❌ 默认**不展示**（按 `AGENTS.md` §5.1 / 契约：只有 CANONICAL 允许 Product 消费） |
| 任何状态 + `?snapshot=draft` | ⚠️ 允许预览，但**必须常驻醒目徽章**「未签发 · 仅供预览」 |

- 无任何 `CANONICAL` 快照时：显示**明确的空态**，说明「尚无已签发的快照」+ 指向 Runbook，**不显示空白**。
- ★ 空态与「无变化」都是**一等公民**，不得用「暂无数据」一句敷衍。

## 5. 数据流

```
research/current/market_snapshots/
├── index.json                    ← 生成器维护（id / date / status / file），极小
└── snapshots/MS-*.json           ← 快照本体（~192 KB/份）

Product：
  index.json（静态 import，极小）
      ↓ 选「最新 CANONICAL」+「上一个 CANONICAL」
  按需 lazy import 这 2 份快照（不把全部快照打进主包）
      ↓
  diffSnapshots(prev, latest)  ← 纯函数，只陈述事实
      ↓
  ViewModel → 页面
```

**为什么不 glob 全部快照**：快照按月累积（~192 KB/份），全量进包会持续膨胀。
索引 + 按需加载让**主包不随月份增长**。

## 6. 语义红线（页面层）

| ✅ 可以有 | ❌ 不得有 |
|---|---|
| 「本期 3 处变化」 | 「本期改善 / 恶化」 |
| 「`NO_VALID_CORRESPONDENCE` 47 条」 | 「相似度 0.87」「最像 XX」 |
| 「阶段：主题形成」 | 「建议关注」「值得买入」 |
| 「还缺什么证据」 | 「预计上涨概率」 |
| 计数事实 | 概率 / 胜率 / 排名 / 评分 / 信号 |

## 7. 本轮不做

- ❌ 不改首页第一视觉（SeasonalMap 保持）
- ❌ 不做交互式筛选 / 搜索 / 排序（**排序即排名**，红线）
- ❌ 不在产品端联网 / 调 LLM
- ❌ 不做快照的编辑（Product 只读）

---

*设计 · ThreeC 1.1 Phase 1.3 · 2026-10-06*
