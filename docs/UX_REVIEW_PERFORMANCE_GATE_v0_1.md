# UX_REVIEW_PERFORMANCE_GATE_v0_1

> | 项目 | 值 |
> |---|---|
> | 性质 | **用户体验 + 性能闸门**（不新增研究能力） |
> | 完成日期 | 2026-09-19 |
> | 起始状态 | `HEAD = origin/main = 17339e0`，ahead/behind `0/0`，工作树 clean（**自行核对**，已先 `git merge --ff-only` 同步远程 doc commit） |
> | **Gate 结论** | **`PASS`** |
> | 未修改 | Research artifact · Rule Set v0.2 · schema · `timeline_export_v1` · 历史数据 |

---

## 0. Executive Summary

| 项 | 结果 |
|---|---|
| UX findings | 发现 **1 项明确信息密度问题** + **1 项移动端换行问题**（**均已修复**） |
| 信息层级 | ✅ **Timeline 仍为第一视觉**；Current Time Lens 未被压垮（修复后） |
| 移动端 | ✅ 结构可用（窄屏 flex-wrap + 断点；已补长文本换行） |
| Structural Analogy 可理解性 | ✅ 五级状态 / 四维 / UNKNOWN 语义 / Theme metadata 均清晰 |
| `currentSimilarity` 重复入口 | ✅ 已收进默认收起的兼容容器；**建议进一步弱化**（未删除） |
| **Performance** | ✅ **初始 bundle 688.19 → 398.63 kB（−42%）**，**>500 kB 警告消除** |
| 是否需要修复 | ✅ 需要，且**已完成** |

---

## 1. UX Findings

### 1.1 5 秒：用户是否知道今天处于什么时间位置、这里是什么产品

| 检查 | 结果 |
|---|---|
| 首屏顺序 | `App.tsx`：`<Timeline>`(148) → `<CurrentTimeLens>`(159) → `<HistoricalSimilarPhase>`(168) → `<SamePeriodView>`(174) |
| 结论 | ✅ **Timeline 是第一个主区**，符合 IA（`Timeline > Current Lens > Similar Phase`） |
| 产品定位 | Current Time Lens 标题含「研究导航 · 非预测」标签；Structural Analogy 含「研究 · 非预测」 |

### 1.2 30 秒：能否找到 Current Candidate 与 Structural Analogy 入口

| 检查 | 结果 |
|---|---|
| Current Candidate | 位于 Current Time Lens 内「当前研究候选」区 |
| Structural Analogy | 展开任一候选后**第 4 个 section**（Why now / Current Evidence / Phase Inference / **Structural Analogy**） |
| 结论 | ⚠️ **入口需要先展开候选**。属合理交互（避免首屏过载），但**新用户可能不立即发现** |

> **建议（未在本轮改）**：在候选行（收起态）增加一个轻量提示，如「结构对应 4」，
> 使用户在展开前就知道该候选有 Structural Analogy 内容。属**增强**，非阻塞。

### 1.3 2 分钟：能否完成一次「当前对象 → 历史对应 → 为什么 → 哪里不同 → 查看历史案例」

| 步骤 | UI 支持 |
|---|---|
| 当前对象 | ✅ `sa-subject`（显示名 + Macro Theme + 当前阶段） |
| 历史对应 | ✅ 列表 + 状态徽章（默认前 6 个，可「显示全部 17 个」） |
| 为什么对应 | ✅ 展开后「为什么对应」区块 |
| 哪里不同 | ✅ 展开后「哪里不同」区块 |
| 查看历史案例 | ✅ `查看完整历史案例 →`（仅可导航 Campaign） |

**结论**：✅ **闭环完整**。

### 1.4 信息层级（★ 本轮修复项）

| 检查 | 结果 |
|---|---|
| Timeline 是否仍为第一视觉 | ✅ 是（首位） |
| **Current Time Lens 是否被 Structural Analogy 压垮** | ⚠️ **修复前：是** → ✅ **修复后：否** |

**问题（明确信息密度问题）**：
Structural Analogy 区块**默认把 17 个历史对象全部展开渲染**，
单个候选的 SSR 标记约 **83 KB**，在 Current Time Lens 内形成极长的信息流。

**修复**：**渐进披露**（默认展示前 **6** 个，提供「显示全部 17 个历史对象」/「收起」）。

- ★ **截断不改变顺序**：被隐藏的是「后面的」，不是「较弱的」；UI 明示
  「按历史对象稳定顺序展示前 6 个；**不是**「最强的 6 个」」。
- ★ **深链安全**：若 `initialOpenCycleId` 指向第 7 个及之后，**自动展开全部**（避免「打开了看不见」）。
- ★ **总量不隐藏**：始终显示「显示全部 17 个历史对象」。

### 1.5 五级状态是否清楚区分

| 状态 | 中文 | 视觉 |
|---|---|---|
| `STRUCTURAL_SUPPORTED` | 结构支持 | 绿边 + 绿字徽章（+「严格口径」标记） |
| `STRUCTURAL_PARTIAL` | 结构部分支持 | 浅绿 |
| `THEME_ONLY` | 仅主题相关 | 黄 |
| `INSUFFICIENT_EVIDENCE` | 证据不足 | 褐 |
| `NO_VALID_CORRESPONDENCE` | 无有效结构对应 | 灰 |

✅ 五级**各自独立文案 + 独立配色**；测试断言 `sa-status s-<status>` 类名互不相同。

### 1.6 四维是否容易阅读

✅ 四维以紧凑 chip 呈现（`生命周期 / 驱动机制 / 证据顺序 / 事件结构`），
每维带状态词（`对应 / 部分对应 / 不对应 / 未知 / 无可用资料 / 仅外围机制重叠`）。
窄屏 `flex-wrap` + 断点缩小 padding/字号。

### 1.7 UNKNOWN / NOT_AVAILABLE 是否会被误读成「没有」

| 措施 | 说明 |
|---|---|
| 独立状态词 | `未知` / `无可用资料` —— **不是** `不对应` |
| 独立视觉 | `is-indeterminate` = **虚线边框 + 灰字**；`is-mismatch` = **红字** → **不同色** |
| 文案 | 展开后「哪些维度未知」区块明示「资料不足，**不等于**「不存在」或「不对应」」 |
| 分组 | `unknownDimensions` 与 `unsupportedDimensions` 分开 |

✅ 测试覆盖：`is-indeterminate` 与 `is-mismatch` 同时存在且语义不同。

### 1.8 Theme Relation 是否明确只是背景 metadata

| 措施 | 说明 |
|---|---|
| 展示位置 | 与「历史 Campaign」并排的 chip，文案为「跨 Macro Theme（**背景信息**）」 |
| `title` 提示 | `METADATA_ONLY —— 不参与 Structural Status 判定，不得据此升降级` |
| **不进入 `why_not_similar`** | ✅ 测试断言：「哪里不同」区块内**不含**「跨 Macro Theme」 |
| 对象化 | Artifact v0.2 已把 `theme_relation` 改为 `{value, role, note}` |

### 1.9 Historical Candidate 是否明确不是 Campaign

| 措施 | 说明 |
|---|---|
| 类型徽章 | `历史 Campaign` / `历史 Research Candidate`（不同 class/色） |
| 导航 | Research Candidate **不显示**「查看完整历史案例」按钮 |
| 文案 | 「该历史对象是 **Research Candidate**（不是 Campaign），没有对应的 Campaign Detail 页面 —— 不提供不存在的入口」 |

✅ 测试覆盖。

### 1.10 重复信息：旧 Current Similarity vs 新 Structural Analogy

| 项 | 状态 |
|---|---|
| 旧视图位置 | 收进 `<details className="ccs-legacy">`，**默认收起** |
| 旧视图标注 | 「历史相似阶段（**旧视图 · 兼容保留**）—— 该视图使用旧的阶段/分档口径，**不是**结构对应；正式入口见上方 Structural Analogy。」 |
| 视觉弱化 | `border-top: 1px dashed` + 灰色小字 summary |
| 是否仍像「两个相似度模块」 | ⚠️ **修复后大幅缓解**（默认不可见），但**未彻底消除**（展开旧视图仍可见分档/星级） |

> **建议**：`currentSimilarity` 的**最终去留**应在 UX 之后独立决策（§5）。

### 1.11 移动端

| 检查 | 结果 |
|---|---|
| 断点 | `@media (max-width: 720px)` 覆盖 `.sa-*`：状态徽章取消 `margin-left:auto`、四维缩小、筛选按钮间距收紧 |
| 长标题 | `.sa-name` + `.sa-id` 允许换行 |
| **长 why_similar / why_not_similar** | ⚠️ **修复前缺 `overflow-wrap`** → ✅ **已补 `overflow-wrap: anywhere`** |
| 四维展开后 | 四维为独立 chip + `flex-wrap`，不溢出 |
| 导航按钮 | 全宽可点（`ccs-open`） |

---

## 2. 信息层级问题

| # | 问题 | 严重度 | 处置 |
|---|---|---|---|
| 1 | Structural Analogy 默认展开 17 项 → 单候选约 83 KB 标记，信息流过长 | **HIGH** | ✅ **已修复**（渐进披露，默认 6） |
| 2 | 候选收起态无「有结构对应」提示，用户需逐个展开才发现 | LOW | 记录为**后续增强**（未改） |
| 3 | 旧 similarity 视图与新区块共存（虽默认收起） | MEDIUM | 已弱化；最终去留见 §5 |

---

## 3. 移动端问题

| # | 问题 | 严重度 | 处置 |
|---|---|---|---|
| 1 | `why_similar` / `why_not_similar` 长中文串在窄屏可能溢出 | MEDIUM | ✅ **已修复**（`overflow-wrap: anywhere`） |
| 2 | 状态徽章 `margin-left: auto` 在窄屏挤压标题 | LOW | ✅ 已在 720px 断点取消 |
| 3 | 17 项全展开在移动端需极长滚动 | **HIGH** | ✅ 由渐进披露解决 |

---

## 4. Structural Analogy 可理解性问题

| 检查 | 结论 |
|---|---|
| 「这不是相似度」是否说清 | ✅ 文案「回答：当前结构与哪些历史结构存在对应关系？为什么？哪里不同？」+「产品只读展示，不重新计算、不评分、不排名」 |
| 是否会被误读为预测 | ✅ 标签「研究 · 非预测」+ 空态「不是预测失败」 |
| Driver 分层是否说清 | ✅ 「驱动机制」与「证据类别」并列展示 + 注「两者不是同一维」 |
| 数组顺序是否会被误读为排名 | ✅ 明示「不是从强到弱」+「不是最强的 6 个」 |

---

## 5. `currentSimilarity` 重复入口评估

**本轮未重写、未删除。** 仅做 UX 层面判断：

| 问题 | 判断 |
|---|---|
| 是否应继续作为**默认可见入口**？ | ❌ **否** —— 已改为默认收起的兼容容器 |
| 是否已可**进一步弱化**？ | ⚠️ **可以** —— 建议下一步把旧视图移到「更多/历史视图」二级入口，或仅在用户显式切换时出现 |
| 是否仍有必要**继续保留**？ | ✅ **暂需保留** —— 其非重叠导出（`narrativeTypesOfCampaign` / `candidatePatternOf` / `phasePositionOf`）仍被 `currentCandidateAdapter.ts` 使用；直接删除会破坏现有流程 |

> **最终删除 / 迁移留待 UX 后独立决策**（本 Gate 不执行）。

---

## 6. Performance Diagnosis

### 6.1 体积来源（实测）

| 文件 | 原始大小 |
|---|---:|
| `research/research/reports/structural_analogy_explanations_v0_2.json` | **488.0 KB** |
| `research/research/reports/time_observation_patterns_v0_1.json` | 46.0 KB |

### 6.2 根因

`src/data/timeline/structuralAnalogy.ts` 原以 **静态 `import`** 引入 488 KB 的 Explanation Artifact
→ 被 Vite 打入**首屏主 chunk** → 用户在**从未展开任何候选**的情况下，
也必须为全部 85 条历史解释数据付首屏加载成本。

### 6.3 修复前 / 后（实测）

| | 修复前 | **修复后** |
|---|---:|---:|
| 初始 JS chunk | **688.19 kB**（gzip 162.37） | **398.63 kB**（gzip **141.17**） |
| 懒加载 chunk | — | **292.45 kB**（gzip **22.72**） |
| 初始 bundle 变化 | — | **−289.56 kB（−42.1%）** |
| Vite `>500 kB` 警告 | ⚠️ **存在** | ✅ **消除** |

---

## 7. 是否需要 bundle / loading 修复

✅ **需要，且已完成。**

**方案**：**Vite 动态 `import()` → 独立 chunk，按需加载**。

```ts
// structuralAnalogy.ts
export async function loadStructuralAnalogyDataset(): Promise<StructuralAnalogyDataset> {
  if (_cache) return _cache;                                   // 缓存，不重复加载
  const mod = await import('@observation/structural_analogy_explanations_v0_2.json');
  _cache = parseStructuralAnalogyDataset(mod.default);
  return _cache;
}
```

组件在**挂载时**（= 用户展开某个候选时）触发加载。

### 合规确认（硬约束逐项）

| 要求 | 结果 |
|---|---|
| Product runtime 仍是**静态部署** | ✅ 是 —— chunk 与 `index.html` 同源，无外部 API |
| 不依赖外部 API | ✅ 无 |
| 没有 LLM | ✅ 无 |
| 不改变 Research 数据语义 | ✅ 未改 artifact；仍解析全部 85 条、全部 provenance |
| 无交互闪烁 / 空状态误判 | ✅ **三态分离**：`loading`（「正在加载结构对应数据…」）· `failed`（「加载失败 —— 这不代表「没有历史对应」」）· 真实空态 |
| 不删除 Research 数据 | ✅ 未删 |
| 不减少 85 条 explanation | ✅ 仍是 85 条（测试断言） |
| 不删除 provenance | ✅ 保留 |
| 不把研究内容压缩成摘要 | ✅ 未压缩 |
| 不改 Research artifact / schema / export | ✅ 未改 |

**加载失败处理**：显示诚实提示，**不得**退化成「没有结构对应」（已写入组件与测试）。

---

## 8. 修复前后 bundle 数据（汇总）

| 指标 | 修复前 | 修复后 | 变化 |
|---|---:|---:|---:|
| 初始 JS | 688.19 kB | **398.63 kB** | **−289.56 kB（−42.1%）** |
| 初始 JS（gzip） | 162.37 kB | **141.17 kB** | −21.20 kB |
| 懒加载 JS | — | 292.45 kB | 新增（按需） |
| 懒加载（gzip） | — | 22.72 kB | 按需 |
| CSS | 43.26 kB | 43.45 kB | +0.19 kB |
| `>500 kB` 警告 | 有 | **无** | ✅ |

---

## 9. Gate

> ## ✅ **`PASS`**

### 判定依据

| 验收项 | 结果 |
|---|---|
| `npm test` | ✅ **481 passed**（12 files；原 476 + 新 5） |
| `tsc -b` | ✅ exit 0 |
| `npm run build` | ✅ PASS（**无 chunk >500 kB 警告**） |
| 原有功能不回归 | ✅ 旧 `CurrentCandidateSection` 测试通过 |
| Structural Analogy 语义不变 | ✅ 五级状态 / 四维 / UNKNOWN 语义 / Theme metadata 全部保持 |
| Calendar / Lifecycle 不回归 | ✅ 未改 `historicalSimilarPhase.ts`；Calendar Lens 未动 |
| Research artifact 不变 | ✅ `git status` 为空 |
| schema / export 不变 | ✅ `git status` 为空 |
| 移动端结构可用 | ✅ 断点 + 换行已补 |
| performance 修复后 bundle warning 得到合理处理 | ✅ 警告消除，初始 bundle −42% |

### 本轮代码修改（仅限允许范围）

| 文件 | 修改 | 依据 |
|---|---|---|
| `src/data/timeline/structuralAnalogy.ts` | 静态 import → 动态 `import()` + 缓存 | **明确由 688.19 kB 引起的加载性能问题** |
| `src/components/CurrentTimeLens/StructuralAnalogySection.tsx` | 三态加载 + 渐进披露 + 深链自动展开 | 性能 + **明确信息密度问题** |
| `src/data/timeline/__tests__/structuralAnalogy.test.ts` | 适配（显式解析数据集） | 测试 |
| `src/data/timeline/__tests__/structuralAnalogySection.test.tsx` | +5 项（加载态 / 缓存 / 渐进披露 / 换行断言） | 测试 |
| `src/styles.css` | 渐进披露 + 移动端 `overflow-wrap` | **明确移动端可用性问题** |

### 本轮**未**修改

`research/**` · `exports/**` · `schema` · Structural Analogy Rule Set v0.2 · Explanation Artifact ·
`timeline_export_v1` · `currentSimilarity.ts` · `historicalSimilarPhase.ts` · `OpportunityRadar` ·
`App.tsx` · Current Time Lens 既有结构（A股环境 / Theme Cycle / Research Attention / Calendar Lens）

---

## 10. 后续建议（不在本轮）

| # | 建议 | 类型 |
|---|---|---|
| 1 | 候选收起态增加「结构对应 N」轻提示，降低发现成本 | UX 增强 |
| 2 | 旧 similarity 视图移入二级入口或显式切换 | UX |
| 3 | `currentSimilarity` 最终去留（兼容保留 / thin adapter / 废弃） | 独立决策 |
| 4 | 懒加载 chunk 可进一步按候选切分（当前 292 kB 一次性） | 性能优化 |
| 5 | Driver 证据深度（`MATCH 1/85`） | Research backlog |

---

*报告结束 · UX Review + Performance Gate v0.1 · 2026-09-19*
