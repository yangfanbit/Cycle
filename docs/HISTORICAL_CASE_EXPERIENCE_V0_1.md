# HISTORICAL_CASE_EXPERIENCE_v0_1

> | 项目 | 值 |
> |---|---|
> | 性质 | **产品体验闭环**（不新增 Research 能力、不重算 Structural Analogy） |
> | 完成日期 | 2026-09-19 |
> | 起始状态 | `HEAD = origin/main = 8d57dc8`，ahead/behind `0/0`，工作树 clean（**自行核对**；远程无新增，已在同步状态） |
> | **Gate** | **`PASS`** |
> | 未修改 | `research/**` · Research Artifact · Rule Set v0.2 · schema · `timeline_export_v1` · 历史数据 |

---

## 1. 当前 Historical Case 入口

**事实清单（实测）**：

| 问题 | 事实 |
|---|---|
| 点击历史 Campaign 后进入什么 | `App.tsx`：`selection = { kind:'campaign', id }` → 渲染 **`CampaignDetail`**（`<aside class="detail-panel" role="dialog">`，右侧抽屉，带 `×` 关闭） |
| Historical Case 页面已有什么 | 标题 / Research Candidate 徽章 / 跨年 / 强度 / 结果 / 状态；行情；完整日期；峰值；所属规律；早期信号；**生命周期**；题材；代表股票；研究分歧；**关联事件**；研究信号；**驱动因素四问**；备注；信息来源；免责声明 |
| 已可直接消费的 Research 数据 | `timeline_export_v1.json`（campaigns / events / securities / themes / lifecycle / drivers）· `structural_analogy_explanations_v0_2.json` · `historical_driver_canonicalization_v0_1.json` |
| 已存在但**未形成闭环**的 | SA 的「查看完整历史案例 →」**能打开** Case，但 Case **不知道用户从 SA 进来**：无对应上下文、无显式回流；且 **Mechanism Driver 与 Evidence Category 混在「驱动因素」里**，证据序列**未按时间与生命周期对齐** |
| 可复用的组件 | ✅ **`CampaignDetail` 本身即可复用**（已有 lifecycle / events / securities / drivers）→ **本轮不新建页面、不重复实现** |

**结论**：本轮**扩展现有 `CampaignDetail`**，不新建独立 Historical Case 页面。

---

## 2. 信息架构

```
CampaignDetail（Historical Case · 右侧抽屉）
├─ ① Structural Analogy 上下文（仅从 SA 进入时；轻量）
│    ├─ 为什么当前对象与这个历史案例对应
│    ├─ Structural Status（+ 严格口径）
│    ├─ 当前对象 + Theme Relation（背景信息）
│    ├─ 四维状态
│    ├─ 为什么对应 / 哪里不同
│    ├─ 未知维度（UNKNOWN / NOT_AVAILABLE 语义）
│    └─ ← 返回 Structural Analogy
├─ ② Case Header（新增「历史对象类型 / Macro Theme / Theme Cycle」）
├─ ③ 生命周期（原样消费 Research `phases`）
├─ ④ 驱动机制（Mechanism Driver）  ← 按需加载
├─ ⑤ 证据类别（Evidence Category） ← 由 event_type 确定性映射
├─ ⑥ 证据序列（按时间 + 生命周期阶段）
├─ ⑦ 关联事件 / 研究信号（既有）
├─ ⑧ 研究归因（四问 · 自由文本）  ← 由「驱动因素（为什么）」改名，消除与机制撞名
├─ ⑨ 题材 / 代表股票 / 研究分歧 / 备注 / 信息来源（既有）
└─ 免责声明（既有）
```

---

## 3. Current → Historical → Case 闭环

```
Current Time
    ↓
Current Candidate（Current Time Lens 内）
    ↓  「结构对应」提示（收起态可见）
Structural Analogy（逐维对应 + 为什么 / 哪里不同）
    ↓  「查看完整历史案例 →」（**携带 SA 上下文**）
Historical Object（Campaign / Research Candidate，身份明确）
    ↓
Historical Case（CampaignDetail）
    ↓  「← 返回 Structural Analogy」
回到原 Current Candidate / SA 状态
```

**上下文保持机制**：`CampaignDetail` 是**叠加渲染**（不替换 `main`），
`CurrentTimeLens` / `CurrentCandidateSection` **始终挂载** → 其 `openId`（展开的候选）与
`StructuralAnalogySection` 的 `filter` / `showAll` / `openId` 状态**自然保留**。
关闭或返回时仅清空 `analogyContext` + `selection`。

---

## 4. 复用的 Research 数据（全部只读）

| 数据 | 来源 | 用途 | 加载方式 |
|---|---|---|---|
| Campaign / 生命周期 / 事件 / 题材 / 证券 | `timeline_export_v1.json` | Header · Lifecycle · Evidence Sequence · 既有区块 | 既有静态链路 |
| **驱动机制**（canonical） | `historical_driver_canonicalization_v0_1.json` | ④ Mechanism Driver | **按需动态 import（11.25 kB chunk）** |
| **结构对应 + 逐维理由** | `structural_analogy_explanations_v0_2.json` | ① SA 上下文 | 既有按需加载（SA 展开时） |

**证据类别**由事件的 `event_type` **确定性映射**（`policy→POLICY` · `company→INDUSTRY` ·
`market→CAPITAL` · `macro→EXTERNAL`；`industry` / `news` / `holiday` / `other` **不映射，不猜测**）。

---

## 5. Product 不推导的内容（硬约束）

| Product **不**做 | 说明 |
|---|---|
| 不重新计算 Structural Analogy | ① 区块全部字段**原样来自** Explanation Artifact v0.2 |
| 不重新推导生命周期 | ③ 原样消费 Research `phases` |
| 不重新推导驱动机制 | ④ 原样消费 Canonicalization；`NOT_AVAILABLE` 明示「不代表没有驱动」 |
| 不发明事件分类 | ⑥ 使用 `timeline_export_v1` 既有 `event_type` / `role` |
| 不把 Theme Relation 当结构支持 | ① 标注「背景信息，不参与结构判定」 |
| 不把 UNKNOWN / NOT_AVAILABLE 当 NO | ① 与 ⑥ 均明示「资料不足 ≠ 不存在 / 不对应」 |
| 不把 PARTIAL 当 MATCH | 维度状态原样展示 |
| 不产生 score / ranking / probability / 预测 | 无任何打分或排序 |

---

## 6. `currentSimilarity` 依赖审计（§六）

### 6.1 全部 import 使用（非测试）

| 引用方 | 使用的符号 |
|---|---|
| `src/data/timeline/currentCandidateAdapter.ts` | `type CurrentSimilarityView` · `similarPhaseForCandidate` |
| `src/components/CurrentTimeLens/CurrentCandidateSection.tsx` | 经 `currentCandidateAdapter` 间接消费 `view.similarity`（**旧视图区块，已默认收起**） |

### 6.2 分类

| 类别 | 内容 |
|---|---|
| **仅属于旧 similarity UI 的逻辑** | `similarPhaseForCandidate` · `SIMILARITY_WEIGHTS` · `CurrentSimilarCase`（含 `score` / `tier` / `stars`）· `CurrentSimilarityView` · `tierOf` · Top-3 截断 |
| **真正仍需要的基础能力** | **无** —— `narrativeTypesOfCampaign` / `narrativeProvenanceOf` / `candidatePatternOf` / `phasePositionOf` / `driverCategoriesOf` **当前无任何非测试引用** |
| 旧 UI 依赖 | `CurrentCandidateSection` 的 `<details class="ccs-legacy">` 区块（默认收起） |

### 6.3 结论

> **耦合仅限「旧算法本身 + 旧视图」** —— 不存在被其他正式能力复用的中性 helper，
> 因此**无需抽取到中性模块**；**也不存在** Product 中第二个 Current → Historical 正式入口。
>
> **彻底退役需要同时移除** `currentCandidateAdapter.view.similarity` 与旧视图区块 ——
> 属**跨模块删除**，超出本轮范围。按 §六「如果本轮无法安全完成彻底退役，就保持现状，不强删」
> → **保持现状**（`LEGACY / FREEZE` 不变）。

---

## 7. UX 验证结果

### Path A · 完整闭环
`Timeline → Current Time Lens → Current Candidate → Structural Analogy → Historical Campaign → Historical Case`
✅ **闭环完整**：SA 的「查看完整历史案例 →」打开 `CampaignDetail`，且**携带 SA 上下文**。

### Path B · 回流
`Historical Case → 返回 Structural Analogy → 返回 Current Candidate`
✅ **上下文不丢**：
- 新增「← 返回 Structural Analogy（保持当前候选上下文）」按钮
- `CampaignDetail` 叠加渲染，`CurrentTimeLens` / `CurrentCandidateSection` **不卸载** → 候选展开态、SA 筛选态、SA 展开项**全部保留**
- 关闭按钮（`×`）同样清空上下文并回到原状态

### Path C · 窄屏
✅ 新增样式均带 `overflow-wrap: anywhere`（`.hcx-sa-from` / `.hcx-sa-block li` / `.hcx-seq-name`）；
`720px` 断点缩小 chip padding 与字号；四维 / 维度 chip / 证据序列均 `flex-wrap`，**无横向溢出**。

### Path D · UNKNOWN / NOT_AVAILABLE
✅ 仍与 `MISMATCH` **严格区分**：
- SA 上下文：`未知维度：事件结构 —— 资料不足，**不等于**「不存在」或「不对应」`
- 证据序列：阶段列显示「**阶段未知**」并说明「该事件日期不落在任何已记录生命周期区间内（UNKNOWN，**不是**不对应）」
- 驱动机制无数据 → `NOT_AVAILABLE` 明示「不代表「没有驱动」」

### Path E · Research Candidate
✅ `Historical Case` 的「历史对象类型」明示 **`Research Candidate（研究候选，非 Campaign）`**；
SA 侧对 Research Candidate **不提供** Campaign Detail 入口（沿用上轮边界，未放宽）。

### §七 入口微优化（30 秒发现性）
✅ 在 Current Candidate **收起态**新增轻量提示：**「结构对应」**（虚线 chip，含 `title` 说明）。

> **为何不显示数量**：显示「结构对应 N 个历史对象」需要 Explanation Artifact 的数据，
> 而该 Artifact **必须保持按需加载**（§九）。若为显示数量而预加载，会使首屏重新承担 292 kB；
> 若为此新建「仅含计数」的小 artifact，则需**修改 `research/**`**（§八 禁止）。
> → 采用**不依赖数据的等价表达**（§七 允许「或等价表达」），既解决发现性，又不破坏性能约束。
> **记录为后续可选优化**（需在「允许新增 research artifact」的轮次中处理）。

---

## 8. Performance 验证结果

| 指标 | 上轮（Gate v0.1） | **本轮** |
|---|---:|---:|
| 初始 JS | 398.63 kB | **406.08 kB**（+7.45 kB） |
| 初始 JS（gzip） | 141.17 kB | **143.75 kB** |
| SA 懒加载 chunk | 292.45 kB | **292.45 kB**（未变，仍按需） |
| **新增** 机制懒加载 chunk | — | **11.25 kB**（按需） |
| CSS | 43.45 kB | 45.56 kB |
| **`>500 kB` warning** | 无 | ✅ **仍无** |

**合规**：
- ✅ Structural Analogy 数据**仍按需加载**（未回退到首屏）
- ✅ **静态 PWA** · 无外部 API · 无运行时 LLM · 无在线 Research
- ✅ **未删历史数据** · **保留完整 provenance**
- ✅ 新增页面复用既有 `CampaignDetail`，**未引入大型 chunk**（新增仅 7.45 kB 初始 + 11.25 kB 按需）

---

## 9. 测试结果

```
npm test       → 510 passed（13 files；上轮 481 + 本轮新增 29）
npx tsc -b     → exit 0
npm run build  → PASS，无 chunk >500 kB 警告
```

**新增测试（`src/data/timeline/__tests__/historicalCase.test.tsx`，29 项）**：

| 分组 | 覆盖 |
|---|---|
| Case 视图模型 | header identity / `themeCycleId` / `macroTheme` / `objectKind`；lifecycle 原样；证据类别非机制；证据序列升序 + 阶段；阶段未知 → null |
| 证据类别映射 | 4 类映射正确；未映射类型不猜测；顺序稳定；无事件 → 空集 |
| 驱动机制按需加载 | 全 cycle 加载；缓存；补丁不改其他字段；未加载 → `null`；无对应 → `[]`；状态标签覆盖 |
| SA 上下文与回流 | 区块渲染；严格口径；返回按钮；无上下文不渲染；UNKNOWN 语义；Theme Relation 背景标注；明示不重算 |
| 信息层级与分层 | Header 三类信息；机制/证据分开且说明不是同一维；旧「驱动因素」已改名；证据序列说明；生命周期 |
| 边界 | Research Candidate 非 Campaign；无 score/ranking/概率/预测措辞 |

**回归**：原有 481 项全部通过（含旧 `CurrentCandidateSection`、Calendar / Lifecycle、SA 43 项）。

---

## 10. Gate

> ## ✅ **`PASS`**

| 验收项 | 结果 |
|---|---|
| Path A 完整闭环 | ✅ |
| Path B 回流不丢上下文 | ✅ |
| Path C 窄屏无横向溢出 | ✅ |
| Path D UNKNOWN / NOT_AVAILABLE 与 MISMATCH 区分 | ✅ |
| Path E Research Candidate 无 Campaign Detail 入口 | ✅ |
| `npm test` / `tsc -b` / `npm run build` | ✅ 510 passed / exit 0 / PASS |
| build 无新的 `>500 kB` warning | ✅ |
| Research / export / schema 无变化 | ✅ `git status` 为空 |
| working tree | ✅ 提交后 clean |
| 不新增 Research 能力 / 不重算 SA | ✅ |

### 本轮修改

| 文件 | 说明 |
|---|---|
| **A** `src/data/timeline/historicalCase.ts` | Historical Case 视图模型 + 证据类别轴 + 机制轴按需加载 + SA 上下文类型 |
| **A** `src/data/timeline/__tests__/historicalCase.test.tsx` | 29 项测试 |
| M `src/components/CampaignDetail/CampaignDetail.tsx` | SA 上下文 + 返回 · Header 三类信息 · 机制/证据分层 · 证据序列 · 旧「驱动因素」改名 |
| M `src/components/CurrentTimeLens/StructuralAnalogySection.tsx` | 打开 Case 时产出 SA 上下文 |
| M `src/components/CurrentTimeLens/CurrentCandidateSection.tsx` | 收起态「结构对应」提示 + 回调透传 |
| M `src/components/CurrentTimeLens/CurrentTimeLens.tsx` | 回调透传 |
| M `src/App.tsx` | `analogyContext` state + 接线 + 关闭/返回 |
| M `src/styles.css` | `.hcx-*` / `.ccs-sa-hint` 样式 + 移动端断点 |

### 本轮**未**修改
`research/**` · Research Artifact · Rule Set v0.2 · schema · `timeline_export_v1` ·
`currentSimilarity.ts` · `historicalSimilarPhase.ts` · `OpportunityRadar`

---

## 11. 后续可选（不在本轮）

| # | 项 | 阻塞原因 |
|---|---|---|
| 1 | 收起态显示「结构对应 N 个历史对象」 | 需预加载 292 kB（违反 §九）或新增 research artifact（违反 §八） |
| 2 | `currentSimilarity` 彻底退役 | 需跨模块删除 `view.similarity` + 旧视图区块 |
| 3 | Mechanism Driver 逐条 provenance（raw driver 文本） | 需扩展 canonicalization artifact 输出（属 Research 轮次） |
| 4 | Driver 证据深度（`MATCH 1/85`） | Research backlog |

---

*文档结束 · Historical Case Experience v0.1 · 2026-09-19*
