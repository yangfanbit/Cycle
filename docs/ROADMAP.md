# ROADMAP.md — ThreeC 当前路线

> 路线图只描述当前之后的工作；历史实施细节见 `docs/CHANGELOG.md`。

## 1. 已完成基座

### Research
- Research Model v1.0 Frozen
- Historical Data Production
- Theme / Campaign / Sub-theme model
- CMTR v1
- Current Research Discovery
- Time Observation v0.5
- Driver Canonicalization
- Structural Analogy Feasibility / Robustness / Calibration
- **Structural Analogy Rule Set v0.3**（Frozen）
- **Structural Analogy Research v0.4**
- **Structural Analogy Explanation Artifact v0.4**
- **Driver Canonicalization v0.4**
- **Time Observation v0.2**（内部 `artifact_version` 0.3）

### ★★ Research Core Release v0.4 —— **COMPLETE / FROZEN**（2026-09-23）

| 项 | 正式基线 |
|---|---|
| Historical Objects | **79**（52 Campaign + 27 Research Candidate） |
| Macro Theme roots | 11 |
| Driver Canonicalization | **v0.4** |
| Structural Analogy | **v0.5**（395 pairs · lifecycle 输入修复后） |
| Time Observation | **v0.2**（内部 0.3） |
| Product 消费 | **已消费最新 SA / TO artifact** |

> **Research Core 后续只允许由「真实 Product Usage 暴露的问题」触发新研究轮次。**
> 不再主动：扩展 Historical Universe · 新增 Driver vocabulary · 微调 SA rule · 为增加 Pattern 挖数据。

### Product
- Timeline
- Current Time Lens
- Calendar Lens
- Lifecycle Lens
- Current Candidate
- Preview / Production isolation
- Static PWA runtime

## ★★ 当前主线（下一步）：**ThreeC 1.3 —— 用户驱动的研究请求 + 真实工作流验证**（2026-10-16 起）

> 置于此处是刻意的：**这是现在唯一要做的事**。下方 §2 起为状态与历史存档。

### 上一主线（ThreeC 1.2 · 接通工作流）—— ✅ **已完成**（2026-10-16 实测确认）

> 原文与逐段对照保留在下方「2026-10-06 规划」存档中，**不改写**。
> 这里只记录**完成事实与证据**（v0.6 A 工作流逐条核验）：

| 原 P0 | 状态 | 代码证据 | 测试证据 |
|---|---|---|---|
| 快照页的**研究对象 → SA 详情** | ✅ 已完成 | `CurrentSnapshotSection.tsx:404-413`（`onOpenObject` → `onClick`）· 接线 `App.tsx:313` → `focusObject`（`App.tsx:155`） | `CurrentSnapshotBody.test.tsx:248` |
| **候选计数 → 具体历史对象**（含「为什么不对应」） | ✅ 已完成 | `CurrentSnapshotSection.tsx:114-123`（`onOpenHistoricalCase` → `onClick`）· 接线 `App.tsx:312` | `CurrentSnapshotBody.test.tsx:210 / 220 / 227` |
| **结构对应可查看**（维度 / 为什么 / 哪里不同 / 还缺什么） | ✅ 已完成 | `snapshotAdapter.ts`（回指解析）+ `CurrentSnapshotSection.tsx:440-475` | `CurrentSnapshotBody.test.tsx:238 / 258` · `snapshotAdapter.test.ts:69-88`（真实数据：resolved=true、89 条明细、唯一 `SUPPORTED` = `C-2023-AD` 跨主题） |
| 覆盖边界**不再人工维护** | ✅ 已完成（v0.6） | `App.tsx` 覆盖边界横幅改为由 Contract v1.2 `taxonomy` 段**实时推导**根大主题 | `themeGranularity` / 现有 taxonomy 断言 |
| ★ **分类事实 vs 覆盖承诺的语义** | ✅ 已完成（v0.7） | 横幅改为「**分类体系**有 N 个**根主题**」+「**不在根清单里 ≠ 未覆盖**，以方向查询实际命中为准」+ 四个互不相同的事实 | `src/components/__tests__/taxonomyScope.test.tsx`（15 条，App 层真实渲染） |

★ 2026-10-06 的原文与当时的对象数（5 个当前对象 / 79 条比对）是**当时的快照**，
不得与当前（6 个候选 / 89 个历史对象 / 534 对）混写 —— 故原文整体保留为历史。

### 主线目标（1.3）

> **不再无条件扩大题材或 Research Core** —— 先让**真实用户**能把「我关心的方向」
> 变成可交接的研究请求，并用**真实工作流**验证它跑得通。

| 优先级 | 做什么 | 实用理由 |
|---|---|---|
| **P0** | **用户研究请求草稿**（方向 + 研究问题 + 为什么关注 + 已知线索 + 时间范围；随行带覆盖查询结果；导出 JSON / Markdown） | 6 个候选是研究侧选的；用户关心的方向**大概率不在其中**，此前只能「查到没有」然后**无处可去**。★ 草稿**不落库、不给正式编号**，须经 Research 审查 |
| **P0″** | ✅ **历史题材地图主入口 + 标的索引**（v0.10 / v0.11 **已交付**）—— 首页「历史题材地图」区块，索引驱动、可切换题材；每个题材面板内**先给「历史参与标的」索引**（跨事件汇总 / 搜索 / 展开逐次证据），再给逐事件列表。复用同一个 `HistoricalEventMap`（事件卡 / 跨年份比较 / 经验概率全部原样） | 地图此前**只能**从外部雷达的线索卡间接进入，被误读成「外部参考」；且用户只能「按年看事件」，无法回答「这个题材历史上有哪些股票、各自出现在哪几年、为什么被纳入」 |
| **P0‴** | ✅ **完整外部季节性时间轴**（v0.12 **已交付**）—— 25 条外部线索按 1–12 月铺开（23 条上轴 / 24 段窗口 / 跨年拆成 28 段），2 条无固定窗口单列；每条带「外部参考」与映射状态，有历史地图的 4 条给跳转、其余 21 条明写未建 | 此前 21 条藏在「展开其余」后面，用户看不到全年分布；且容易把「外部声称的窗口」误当成 ThreeC 的历史结论 |
| **P0⁗** | ✅ **季节性线索 → 历史窗口对照 → 研究请求闭环**（v0.13 **已交付**）—— 外部时间轴每条 MAPPED 线索可展开「外部月份窗口 × 该主题历史 `MAIN_RISE` 窗口」两层对照；UNMAPPED 线索可把原文/窗口/来源**带入现有**研究请求草稿（非空草稿先确认） | 此前线索的终点是「看到外部窗口」或「未映射」，无法继续走到历史证据或下一步研究 |
| **P0⁘** | ✅ **历史窗口 → 对象详情闭环 + 计数口径修正**（v0.14 **已交付**）—— 外部×历史对照面板每条历史对象可「查看对象详情」（复用既有 CampaignDetail，返回不丢对照上下文）；窗口计数改为「投影段数 / 去重对象数 / 未进入窗口对象逐条列原因」；两层时间轴统一到同一把月份坐标尺 | 此前 v0.13 的 note 把**全主题对象数**当成**窗口涉及对象数**（军工实测写成 2+5，实际 1+1），且用户到历史窗口就看得到「到此为止」，进不去具体对象 |
| **P1″** | ✅ **第 5 个题材纵切片：汽车智能化**（v0.15 **已交付**）—— 6 事件 / 19 只标的（export 注册表 + DB 实算行情），含 RC 不伪装、赛力斯行情缺口如实留空；数据文件版本化进 `research/current/`（**不覆盖旧轮次**） | 地图此前只有 4 个题材，且 v0.14 遗留计数口径混用（DB 62 / export 62+27 / Product 去重 89·切片 157） |
| **P1‴** | ✅ **第 6 个题材纵切片：半导体 / AI 算力 / 存储**（v0.16 **已交付**）—— 7 事件 / 29 参与记录 / 16 只去重标的 / 21 可算行情组合（全由 `market_data.db` 实算），含 RC 不伪装、大基金三期窗口登记标的 series 不覆盖 → **逐条如实留空**；并把**反例（`COUNTER_EXAMPLE`）**从**证据不足（`INSUFFICIENT`）**中分离（大众交通 → 反例，保留「运营牌照方、与智驾技术链不同轴」原解释） | 关系性质此前**五类混用**：反例被并进证据不足，通用 UI 显示为「证据不足 / 反面参照」；地图题材 5 → 6 |
| **P1⁗** | ✅ **历史行情可信展示 + 标的与 Research 对象对账**（v0.17 **已交付**）—— 行情表显示**名称 / 代码 / 关系类别 / 窗口状态**；**只有 `COMPUTED`** 按完整窗口展示，其余标「**仅局部数据，不可视为完整窗口可比结果**」+ 实际可用首末并**下沉分组**；新增 `objectReconciliation`：按 `campaign_facts.object_id` 与 canonical export 的 Campaign / RC `security_ids` **精确对账**（对象已登记关联 / 地图补充记录 / 无法核对），**六题材通用** · 实测 123 条参与记录 = 已登记 **63** / 地图补充 0 / 无法核对 **60** | 用户查看历史行情时**不会**把反例或覆盖不足当成完整可比结果；查看一只股票时**也能知道**它与哪个 Research 对象存在什么类型的关联 |
| **P1⁘** | ✅ **补齐明确对象关联 + 对账四分类**（v0.18 **已交付**）—— `FLU-2023-H1N1` 补 `campaign_facts → C-2023-PHARMA-FLU`（依据：`evidence_basis` 明确引用、3 只标的与对象 `security_ids` **逐一相等**），流感升 **v0_7**（旧文件逐字节保留、**数值零变化**）；对账拆出 **`NO_OBJECT_REFERENCE`（未登记对象关联）**，与 `UNRESOLVED`（已提供引用但无法解析 / 证券注册信息缺失）**区分** · 六题材实测 123 条 = 已登记 **66** / 地图补充 0 / 未登记对象关联 **57** / 无法核对 **0** | 此前把「**缺对象字段**」误报成「**对象解析失败**」；「无法核对 60」里 57 条其实只是**事件未登记对象**（流感 39 + 电力 18），**不**暗示证券不存在、**不**自动判定归属 |
| **P1⁹** | ✅ **对账语义收口 + 三场景真实工作流闭环**（v0.19 **已交付**）—— ①「**证券是否精确命中注册表**」作为**独立第二个事实**分开呈现（未命中如实标「证券注册表：未命中」+ 声明「仅是**需核对的标识差异** ≠ 证券不存在 ≠ 可自动匹配」，实测 **87 命中 / 36 未命中**，全部在流感旧式标识如 `YILING-002603` vs `YILING`）；② 三场景页面级真实工作流（汽车 / 医药 / 文化传媒）走通；③ 修复催化时间线 **React 重复 key** 真实缺陷 | 「事件未登记对象」≠「证券注册表未命中」—— 二者是**两个独立事实**，混在一处会让「缺字段」看起来像「证券不存在」；用户须能**从方向查询一路走到可交接的研究请求草稿**并看清覆盖边界 |
| **P1¹⁰** | ✅ **历史事件 × 冻结 SA 精确交叉引用 + 窄屏实机验收**（v0.21 **已交付**）—— 事件详情新增「与当前冻结 SA 的关系」：按 `campaign_facts.object_id`（兼容 `campaign_id`）与唯一 `CANONICAL` 快照的 `identity` **精确匹配**，列出引用该对象的当前研究对象与**既有** `structural_status`（**不重算 SA**）· 实测 **26 事件 = 18 有对象引用 / 18 命中 / 0 未命中 / 8 未记录对象**，匹配记录 **108 条**（SUPPORTED 4 · PARTIAL 9 · NO_VALID 56 · INSUFFICIENT 36 · THEME_ONLY 3）；真实浏览器窄屏实测发现并**修复**「长不可断串撑破题材地图容器 → 整页横向溢出」（docEl scrollWidth 904 → 662） | 此前用户无法从历史事件看出「这个对象是否被**当前唯一已签发 SA** 研究过」；且窄屏存在真实横向溢出（677px 视口实测）——两者都需要**精确**而非推测的答案 |
| **P0′** | ★ **草稿生命周期可靠性**（v0.7 完成 —— **产品侧局部修复，不是研究能力扩展**）：清空真的清空 · 坏数据不崩 · 保存失败不谎报 · 请求原文与查询证据**分离且可追溯** · 命中依据全程不丢 | 用户已经填写的请求**不得被误清空 / 误覆盖 / 与错误的查询证据关联** —— 这是入口可用的**前提**，而不是新增研究能力 |
| **P2** | ✅ **当前对象 vs 历史生命周期对照**（v0.8 **已交付**）—— `LifecycleComparisonSection`：两列表格（当前自述阶段 ↔ 历史阶段序列），标缺失阶段 / 开放区间 / UNKNOWN，**不**做时间轴归一化、**不**当结构对应结论 | 「理解主题生命周期」目标的落点：用户能看出**阶段顺序、时长与日期差异**，并能点进历史案例详情 |
| **P1¹¹** | ✅ **SA 交叉引用可导航到当前对象详情 + CANONICAL 唯一性门禁**（v0.22 **已交付**）—— ① 事件详情「与当前冻结 SA 的关系」列表每条新增「**查看当前对象详情**」，接入 App **既有** `focusObject` / CurrentTimeLens 流程（**不**复用历史对象的 `openHistoricalObject`，两者是**两种对象类型**）；按 SA 记录里的 `currentObjectId` **精确 ID** 确认可由 `current_candidates.json` 的 `CC-*` 解析，**解析不了就不给按钮**（保留 ID / 名称 / 状态并说明）；② 抽出可测纯函数 `pickCanonicalSnapshot`，修掉原「CANONICAL 排序后取最后一项 = 静默选最新」的缺陷：**0 个 → 无法判定 / 恰好 1 个 → 载入并二次确认 / 多于 1 个 → 拒绝选择并披露**；③ 真实浏览器（缓存绕过）复测线上 Pages：半导体事件 → SA 当前对象列表 → 当前对象结构详情 **闭环走通** | v0.21 让用户**看见**该历史对象是否被当前 SA 引用，但 SA 列表只是静态文本 —— 无法继续走到**当前研究对象**详情；且 `loadSaCrossReference` 对 CANONICAL 唯一性**无显式门禁**（多份时静默取最新） |
| **P1** | ✅ **真实工作流验证**（v0.19 **三场景走通** · v0.20 **补复制动作验收**）—— 汽车（历史足 / 当前窄）· 医药（两侧都有）· 文化传媒（仅历史）三场景**页面级真实数据**走通（`v019UserFlows`）；v0.20 追加「复制 JSON / Markdown 内容 = 预览内容、失败不虚报」验收 | 用**真实场景**而非单元测试证明「七段连成一条路」 |
| **P2′** | ✅ **经验基准概率原型**（v0.9 **已交付**）—— 挂在既有跨年份区段：分母只收 `comparable === true`、排除项逐条带原因、二元目标给 **k/n + 95% Wilson 区间**、标「探索性 · 未校准」 | 用户最自然的问题是「历史上这种情况多久出现一次」。此前整词禁掉「概率」只能回答「描述」，无法给出**可核对的比例** |
| **P2″** | ⛔ **预测模型（未交付，有明确门槛）** —— 需样本外 **≥30 步** **且** **≥3 个事前特征**（v0.10 起两道门槛分开判）；当前 4–6 步、**0 个事前特征** → **不训练** | 基准已用 **Jeffreys 平滑**重算（电力 LogLoss 5.28 → 0.74），但「步数达标 ≠ 可训练」—— 没有事前特征就没有模型 |
| **P3** | 补 **T1/T2 一手来源** | 现有观察**全为 T3**（媒体转述），可信度上限受限 |

**下一步（v0.22 之后候选，未承诺）**：① 预测模型仍缺**事前特征**（库存 / 来水 / 煤价 / 气温 / 政策日历），
需先由 Research 轮次补数据，Product 侧不得自行推断；② 经验概率仍只覆盖电力 / 流感两题材；
③ 标的对账已到 canonical export 的 `security_ids`（v0.17–v0.19，含**注册表命中独立事实**），
且已与**冻结 SA 的对象级记录**建立精确交叉引用（v0.21）并能**导航到当前研究对象详情**（v0.22）；
但**尚未**把 SA 的**结构维度**与标的身份做交叉核对
（SA 为**对象级**判定，**不**含逐证券结构数据 —— 不得据此声称某只股票获得结构确认）；
④ 外部×历史对照目前**只到「并排呈现」+「对象详情跳转」**：重合度 / 命中率等统计量仍未定义；
⑤ 半导体大基金三期（2024 窗口）4 只登记标的 `market_data.db` series **均不覆盖**；
⑥ **36 条「注册表未命中」**（流感 v0_7 旧式标识）与 **57 条「未登记对象关联」**（流感 39 / 电力 18）
仍属待 Research 核对的标识 / 对象缺口；⑦ **视口 / 多浏览器验收仍未完成** —— v0.21 与 v0.22 均为
**单浏览器**的实际视口（v0.21 = 677×662 · v0.22 = 1085×750），**工具不支持设视口模拟**
（目标 1366×768 / 768×1024 / 390×844 / 320×700）也未按 Edge / Safari 分别验收 —— **如实记录**。
以上缺失须由 Research 抓取 / 研究轮次补数据，Product 侧不得补数、不得自行推断。

★ 明确**不做**：买卖信号 / 荐股 / 选股清单 / 实时行情 / **未声明口径的预测**。
★ v0.9 起**允许**：历史频率 / 条件概率 / 阶段变化概率 / 未来窗口预测 —— 但必须满足
`AGENTS.md` §3.1 的七条准入条件（口径 / 分母 / 排除 / 区间 / 时间前推 / 基准比较 / 架构不变）。
★ 仍不做：不因题材数好看而扩题材（扩边属**研究轮次**，须有真实用户需求或研究依据）；
不把可视对照写成结构对应结论。

## 存档：上一主线（ThreeC 1.2 —— 接通工作流（Usage-Driven））（2026-10-06 起）

> ★ 以下为 **2026-10-06 的规划原文**，保留为历史分析（含当时的对象数与判定）。
> 完成情况见上方「上一主线 —— ✅ 已完成」。

> **规划依据**：用 §5「产品最终工作流」逐段对照现状。
> **结论：七段都存在，但没连成一条能走通的路。**

### 逐段对照（2026-10-06 实测）

| 段 | 现状 | 判定 |
|---|---|---|
| 今天 | 首页 Today 线 | ✅ |
| 历史同期 | Calendar Lens | ✅ |
| 历史周期阶段 | Lifecycle Lens | ✅ |
| **当前研究对象** | 本期快照列出 5 个对象 | ⚠️ **列了但点不进去** |
| 历史结构对应 | `StructuralAnalogySection` 四维 | ✅ 但入口在**另一个钻取区** |
| 为什么对应 / 哪里不同 | SA 的 `why_similar` / `why_not_similar` | ✅ 同上 |
| **继续研究** | `research_questions` | ⚠️ 在 CurrentTimeLens 里，**不在快照页** |

**★ 实测证据**：`src/components/CurrentSnapshot/CurrentSnapshotSection.tsx` 中
**没有任何 `onClick` / `onSelect` / `href` / `<button>`** —— 它是一个**死胡同**：
用户看到「79 条比对 · 有结构对应 1 条 · 无有效对应 47 条」，
**既看不到是哪些历史对象，也无法跳去详情**。
（对照：`StructuralAnalogySection.tsx` 有 11 处交互。）

### 主线目标

> **不加新能力，先让已有的七段连成一条能走通的路。**

| 优先级 | 做什么 | 实用理由 |
|---|---|---|
| **P0** | **接通**：快照页的研究对象 → SA 详情；候选计数 → **具体历史对象**（含「为什么不对应」） | 现在页面**给了数字不给内容**，用户无法据此做研究 |
| **P1** | **用户声明研究方向**（`URO-*` 入口 + Research Request） | 5 个对象是研究侧选的；用户关心的方向可能不在其中 —— **无法自己问** |
| **P2** | 当前对象 **vs 历史生命周期**对照 | 「理解主题生命周期」目标的落点 |
| **P3** | 补 **T1/T2 一手来源** | 现有观察**全为 T3**（媒体转述），可信度上限受限 |

### ★★ 2026-10-07 实测修正：**瓶颈是「覆盖」，不是「连接」**

拿用户提的真实方向 **「文化传媒」** 一试，立刻暴露更根本的问题：

| 检查项 | 结果 |
|---|---|
| 52 个 Campaign 中含「传媒 / 文化 / 游戏 / 影视 / 短剧 / 出版 / 元宇宙」 | **0 条** |
| 44 个主题名中含传媒 / 文化类 | **0 个** |
| 5 个当前研究对象中含传媒 | **0 个** |
| 而该方向**当下正在动** | **2026-09-29 文化传媒板块领涨**（新浪财经当日复盘） |

**历史覆盖集中度（实测）**：汽车 · 消费 · 电子/半导体 · 资源 · 金融 · 高端装备 · 电力设备 ·
信息通信 · 医药健康 · 国防军工 · 房地产 —— **硬科技 + 高端制造 + 消费 + 资源 + 金融**。
**不含**传媒 / 文化 / 娱乐 / 教育 等方向。

**结论**：

1. **P0（接通）解决不了「文化传媒」** —— 数据里根本没有对应对象，接什么都接不上。
2. **已做的最小改动**：把**覆盖边界**做成首页可见的声明（`App.tsx` `.seasonal-scope`），
   用户一问就知道「在不在覆盖内」，而不是查半天查不到。
   ★ 该声明是**人工维护**的（canonical export 已冻结，不得改其 provenance）。
3. **待定**：是否**扩边**（把传媒 / 文化等纳入历史研究）？
   - ROADMAP §2 现行政策是 **`Research expansion: DEFERRED`**。
   - 扩边 = **新研究轮次**，工程量大，且必须遵守 Research 的规则（不得为凑数放宽）。

> ★ 这次实测印证了规划里那句话：**ThreeC 至今没有被真实使用过一次** ——
> 一用就撞到了最根本的边界问题。

### ★★ 2026-10-07 两次真实使用测试 → **覆盖地图**

| 方向 | 历史 | 当前对象 | 实测能做什么 |
|---|---|---|---|
| **医药健康** | 1 Campaign | **1** | ✅ **完整工作流** —— 给出**跨主题**结构洞察（报告见 `USAGE_TEST_2026-10-07_PHARMA.md`） |
| **汽车** | **7 Campaign** | **0** | ⚠️ **历史可用，问不了「现在」**（报告见 `USAGE_TEST_2026-10-07_AUTO.md`） |
| **文化传媒** | 0 | 0 | ❌ **完全覆盖不到** |

**三种缺口性质完全不同**：文化传媒 = 双向都无（需扩边）· 汽车 = 历史厚但当前空（需补当前对象）·
医药健康 = 两侧都有（只是没出口）。

> ★ **最重要的结论：缺的不是历史深度，是「当前侧」的覆盖面。**
> 全库 **5 个当前对象** vs **52 个 Campaign / 44 个主题名** ——
> 用户想研究的方向**大概率不在这 5 个里**。**这是入口太窄，不是数据不足。**

→ **P1（用户声明研究方向）应上调**：让用户能声明一个方向并得到明确回答
（有当前对象 → 完整工作流；只有历史 → 历史侧；都没有 → 诚实说覆盖不到）。

### ★★ 2026-10-07 复盘后的下一步规划（三层判定 + 三步走）

**目标接近程度——必须分层看，不能混为一谈：**

| 层 | 判定 | 实测依据 |
|---|---|---|
| **能力层**（该有的机制有没有） | **✅ 接近** | 六段链路全通 · SA 395 条解释 · 四视角齐 · 红线全无 |
| **覆盖层**（能不能答用户想问的） | **⚠️ 一半** | 历史 **79 对象 / 12 大主题**；当前**只有 5 个对象** |
| **验证层**（有没有被真实使用证明有用） | **❌ 最远** | **只有 2 次测试，且都是我自己跑的** |

> **最难的部分（机制）已经过了；卡住的是「宽度」与「验证」。**

**三步走（按此顺序，理由见下）：**

| 步 | 做什么 | 为什么排这里 |
|---|---|---|
| **1** | **把汽车候选正式采纳**（当前侧 5 → 6）：Research 审核 → artifact 版本化 `v0_6` → Product 接线 | ① **已验证**：7 条证据 → **1 条 `STRUCTURAL_SUPPORTED`**，不是猜测 ② **成本最小**：全链已在沙箱跑通 ③ **边际收益最高**：汽车是历史最厚的方向（7 Campaign，延伸到 2025）④ 直接回应复盘发现的**唯一结构性短板** |
| **2** | **真实使用验证**：你（或真实用户）拿一个**真正关心**的方向走完整条工作流 | ① **今天的 5 个缺陷全部来自「真去用」**（候选丢失关联 · 快照不可复现 · 管线跑不了 · 机制轴写错位置 · 传媒覆盖不到）—— **没有一个是读代码能发现的** ② 2 次测试都是我设计的，**我自己测自己有盲区** ③ **不需要写代码**，但信息量最大 |
| **3** | **覆盖宽度的决策**：是否把传媒 / 文化等纳入历史研究 | 唯一能改变「用户能不能问自己想问的」的动作，但**代价最大**（新研究轮次）。**建议先做第 2 步再定** |

**★ 为什么不先扩边**：它是**唯一可能白做**的动作 —— 在确认工具本身有用之前扩大历史研究，风险最高。

### 为什么 P0 排在「加功能」之前

1. **零新增能力** —— SA v0.5 的 395 条解释**已经在包里**，只是**没有出口**。
2. **不加这段，后面每加一个功能都会变成又一个死胡同。**
3. 它直接决定「这个工具到底帮不帮得上」—— 而 ThreeC **至今没有被真实使用过一次**。

### 与「使用测试」的关系

**P0 完成后立即做一次真实使用**：拿一个真正关心的方向，走完整条工作流，记录卡点。
**流程只有真跑过一次才算成立**（1.1 的月度流程演练已经证明了这一点 —— 5 个缺陷全是「真用」才暴露的）。

---

## 2. ★ 当前状态：**ThreeC 1.1 — RELEASED**（1.0 已冻结）

**目标（已达成）**：把已通过 Research / Product / Trust / Quality / Real Usage / Gate M 的 ThreeC，
变成**可稳定访问、可重复构建、可追溯、可回滚**的静态产品，并**正式发布 1.0**。

| 项 | 值 |
|---|---|
| **Version** | **`1.0.0`** |
| **Tag** | **`v1.0.0`**（annotated） |
| **Release commit** | **`064d39c`**（`release: ThreeC 1.0.0`） |
| **Production URL** | **https://yangfanbit.github.io/Cycle/** |
| **Gate R / P / T / Q / U / M / D / G** | **全部 PASS** |
| **P0 / P1** | **0 / 0** |

当前冻结 / 发布状态：

> Research Core：**FROZEN**
> Product **1.1.0：RELEASED**（tag `v1.1.0`）· 1.0 已冻结（tag `v1.0.0`）
> Deployment：**PRODUCTION**
> Historical Universe：**89**（62 Campaign + 27 Research Candidate）
> ★ 2026-10-16 更正：此前此处写 **79**（52 + 27）—— 那是 **v0.4 冻结时的对象数**，
>   此后 R02-03 / R02-04 / R02-05 等研究轮次已入库 10 个 Campaign（52 → 62）。
>   （v0.4 的 79 保留在本文上方「Research Core Release v0.4」历史记录里，**不改**。）
> Research expansion：**DEFERRED**
> SA / TO：**FROZEN**（SA `v0_13` · 快照 `MS-2026-10-13-01` = 唯一 CANONICAL）

**1.1 新增（已上线）**：Market Snapshot 运行时 · 本期研究快照页面 · 快照 diff（月度变化）·
两个纯投影器 · 东方财富 EOD 取数 · Lifecycle Tracking · 首页大主题分类配色 ·
旧「历史相似阶段」视图退役。详见 `docs/CHANGELOG.md` 1.1.0 条目。

**1.1+ 只允许由真实 Product Usage 或明确 Research Question 触发。不预设大量新功能。**

**发布主流程（已落地并已执行）**：

```text
push main
    ↓  GitHub Actions（.github/workflows/deploy.yml）
npm ci → tsc -b → npm test → npm run build（base=/Cycle/）→ 上传 dist/ → deploy-pages
    ↓
https://yangfanbit.github.io/Cycle/
    ↓  操作手册
docs/DEPLOYMENT_RUNBOOK.md
```

| 技术决策 | 结论 |
|---|---|
| 部署平台 | **GitHub Pages**（唯一）；不使用 Vercel / Netlify / Docker / 云服务器 / CDN 产品化 |
| 访问入口 | `https://yangfanbit.github.io/Cycle/` |
| Vite `base` | `THREEC_BASE` > `GITHUB_ACTIONS === 'true'` → `/Cycle/` > `/`（本地 dev / preview 不受影响） |
| provenance（D7） | `src/data/buildProvenance.ts` 在 Product 内展示 version / commit / export `source_commit` / SA / TO |
| 回滚（D6） | 基于 commit SHA + revert（**不伪造 `v1.0.0`**） |
| 重建（D8） | `DEPLOYMENT_RUNBOOK.md` §1–§3 |
| SPA fallback | **不需要**（无 client-side router，仅 query param） |
| `.nojekyll` | **不需要**（产物无 `_` 前缀文件） |

**已执行（Deployment / Release Engineering + 1.0 Release）**：

- `.github/workflows/deploy.yml`（`npm test` 为硬门禁，绝不跳过；只上传 `dist/`；权限最小化）
- `vite.config.ts` base 解析 + `vite define` 注入 provenance
- `src/data/buildProvenance.ts` + `<BuildProvenanceFooter />`
- `src/data/__tests__/deployment.test.ts`（24 用例，workflow 契约由测试锁死）
- `docs/DEPLOYMENT_RUNBOOK.md`
- **1.0 Release 执行**：`package.json → 1.0.0` → release commit `064d39c` →
  annotated tag `v1.0.0` → `git push origin main` + `git push origin v1.0.0` →
  Actions build + deploy PASS → 线上入口 **200 OK** → smoke / 语义 smoke 全通过
- **实测**：`npm test` 678 passed / 0 failed · `tsc -b` 0 error · `vite build` PASS ·
  Actions `build` PASS + `deploy` PASS · 线上 provenance = `1.0.0` / commit `064d39c`

**★ 明确不重开**（除非真实使用产生新的 P0 证据或明确 Research Question）：
R01 / Research 扩容 / SA 扩容 / TO 扩容 / Driver vocabulary / Dashboard / Radar / backend。

---


## 2a. 上一主线（已闭环）：**Product / Real Usage Iteration**（2026-09-23 起）

> Research Core 已 Release（见 §1）。主线曾由「Research → Product」切换为
> **Product Stabilization + Real Usage Validation**。
> **该主线已于 2026-09-24 闭环：P0 清零（Gate T8 PASS）。**

### 主流程（Product 必须逐段可用）

```
Today
 ↓  Current Candidate
 ↓  Time / Calendar（Current Time Lens · Time Observation）
 ↓  Lifecycle（生命周期位置）
 ↓  Structural Analogy（结构对应与不对应）
 ↓  Historical Case（历史对象详情）
 ↓  Evidence（证据 / 时间轴）
 ↓  New Research Question（「这里为什么不一样？」「还缺什么证据？」）
```

**★ Product 不重新实现 Research Logic** —— 只消费 Research artifact，保留 provenance 与不确定性。

### 已完成
- 阶段 A–C：Product 测试 **21 failed → 0 failed** · `tsc -b` PASS · `vite build` PASS
- 阶段 D–F：SA / TO 消费验收 · **P0 修复**（见 `docs/PRODUCT_REAL_USAGE_BASELINE_v0_1.md`）
- 阶段 G：移动端静态审计 + TO 详情网格 3 列 → 2 列（P1）

### 已完成（Lifecycle Repair v0.1）—— 已闭环上一轮 Next Single Goal
- 根因：export lifecycle 来自**手写静态字典**（与 intake 解耦）→ `CANDIDATE_LIFECYCLE` 仅 11/27，且丢 `UNKNOWN` / open-ended 段
- 修复：**从 intake 派生**（单一真源）`build_lifecycle_from_intake_v0_1.py` + `batch_auto_research.py` **intake 优先**
- 结果：RC lifecycle **11/27 → 23/27** · 段 **187 → 243** · **PEAK 22 → 46** · UNKNOWN **未被伪装**
- SA **v0.4 → v0.5**（60 条变化**全部仅 lifecycle 维度**；structural_status 变化 **0**）
- **Driver v0.4 不变**（输入未变）· **TO v0.2 不变**（输出未变）· 新增 `validate_lifecycle_coverage_v0_1.py` 防回归

### 已完成（1.0 P0 修复轮）—— **Gate T8 由 FAIL → PASS，P0 = 0**

> 完整定义见 `docs/THREEC_1_0_RELEASE_DEFINITION.md`。

- **P0-1**：`historicalCase.ts` 改读 Research `c.lifecycle`（空则 `[]`）；
  `researchAttention.ts::terminalPhaseOf` 删除 `c.phases` 回退 → `UNKNOWN`。
  **实证：4 个 UNKNOWN-only RC 的虚构阶段 4 → 0。**
- **P0-1c（审计新发现）**：`STAGE_TO_PHASE` 漏 `ENDED`（Contract 成员）→ 静默退化为 `UNKNOWN`
  → 已补；2 个已结束 Campaign 由 `UNKNOWN` 纠正为 `END`。
- **P0-1d**：`ExportLifecycleStageV1.start/end` 类型改为 `string | null`（Contract 允许开放区间）；
  5 个消费点显式处理，`tsc -b` **12 error → 0**。
- **P0-1e**：`CampaignDetail` 第二处独立 `m.phases` 渲染路径同样虚构「主升」→ 已改读 Research `lifecycle`。
- **D3 由 `it.fails` 正式化**；新增 **Scenario F1–F9** Gate T8 全局不变量（含反向非空断言）。
- `derivePhases()` / `c.phases` **完整保留**（Timeline 视觉分段仍依赖）。

### 1.0 八 Gate 现状

| Gate | 状态 |
|---|---|
| Research · Product · Trust · Quality · Real Usage · Documentation | **PASS** |
| Mobile | PASS（静态；真机复核为 **P2**） |
| **Deployment** | **★ 本轮目标**（P1-1 处理中；访问入口验证待线上执行） |
| P0 | **0** |
| P1 | 见 `docs/THREEC_1_0_RELEASE_DEFINITION.md` §8 |

---

## 2b. 历史主线：Research → Product（已归档）

> **同步说明（2026-09-19）**：Step 1–4 已全部完成（Gate PASS · Adapter · UI Integration · UX Review PASS）。
> 其后追加完成：**Historical Case Experience v0.1（PASS）** ·
> **Historical Cycle Map v0.1（PASS）** · **Current Research Refresh Loop v0.1（PASS）** ·
> **First Real Observation Cycle v0.1（PASS）** ·
> **Historical Case Evidence View Rework v0.1（PASS）** ·
> **Second Real Observation Cycle v0.1（PASS · 0 code change）**。
> 核心路径 `Current Candidate → Cycle Map → Lifecycle Position → Cross-family SA →
> Evidence Timeline → New Research Question` 已在真实使用中自然发生。
> 下一步由**用户**决定，**不在 roadmap 内预设**。

### Step 1 · Product Similarity Architecture Gate v0.1

**已完成：PASS。**

不是 UI 开发，而是 Product 语义和模块职责定稿。

必须正式决定：

1. Calendar / Lifecycle / Structural Analogy 三者边界
2. `currentSimilarity.ts`：兼容层 / 重构 / 废弃
3. `historicalSimilarPhase.ts` 长期定位
4. Structural Analogy 的唯一 Current → Historical Structural Correspondence 入口
5. Evidence Category vs Mechanism Driver
6. Structural Status / dimension status 的产品表达
7. WHY SIMILAR / WHY NOT / UNKNOWN 如何表达
8. Explanation Artifact 的最终接口
9. OpportunityRadar 的最终 legacy 处置

**已输出：**
- Architecture Gate / Decision document
- Explanation Artifact v0.2
- Product-facing Artifact 最小契约

本阶段结束，不再重复执行。

### Step 2 · Product Adapter v0.1

**已完成：PASS。**（后续由 Research Core Release 升级为 v0.4 artifact 输入）

`structural_analogy_explanations_v0_2.json → Product View Model`

前置条件：Step 1 Gate = PASS。

要求：
- Product 只消费 Research 结果
- 不重新实现 Structural Analogy
- 不做 score / ranking / probability
- 保留 provenance
- 保留 UNKNOWN / NOT_AVAILABLE
- 稳定导航到 historical cycle / campaign
- 不破坏 Calendar / Lifecycle

### Step 3 · Product UI Integration

优先进入：

**Current Time Lens / Current Candidate**

目标：

`Current Candidate → Structural Analogy → Historical Case`

不是新增一个孤立 Dashboard。

### Step 4 · UX Review

验证：
- 5 秒理解“今天在哪里”
- 30 秒找到研究入口
- 2 分钟完成一次历史结构比较
- 不把历史对应误读成预测
- 移动端可读
- 信息密度合理

## 3. 非主线 Quality Backlog

> **★ 状态说明（2026-09-23）**：以下全部为 **KNOWN LIMITATION**，
> **不再标记为 BLOCKING**，也不再阻塞任何 Product / Real Usage 推进。
> 只有当真实使用暴露「影响核心判断的错误」时才升级处理。

### ★ Known Limitations 清单（2026-09-24 更新）

| # | 限制 | 影响 | 状态 |
|---|---|---|---|
| **L1** | 剩余 **7 项**跨 canonical 子串冲突（含 v0.1 既有遗留如 `结构迁移`、`倍/翻倍`、`利润/净利润`、`出清/出清完成`、`标准体系/标准体系（2026 版）`） | 相关文本无法成为 `DIRECT`；**不改变任何 driver 集合** | `KNOWN LIMITATION` |
| **L2** | `driver = MATCH` 仅 **1** 条 / `event MATCH` 仅 **1** 条 | 数据粒度限制（**不得**通过放宽规则解决） | `KNOWN LIMITATION` |
| **L3** | **2** 个 cycle 因**映射逻辑**无 canonical driver（`RC-2015-FIN-LEVERAGE` 多命中 · `RC-2024-SECONDARY` 研究自述强度不足） | 非数据缺口 | `KNOWN LIMITATION` |
| **L4** | TO `observation.year`（研究对象研究年份）与 `date`（锚点日期）在「锚点退化为 `campaign.start_date` 且落在上一日历年度」时相差 1 年（5 例，全部 R01） | 年度归属口径问题；改则属规则变更，需独立轮次 | `KNOWN LIMITATION` |
| ~~L5~~ | ~~Research export `lifecycle` 映射缺口~~ → **✅ 已修复（Lifecycle Repair v0.1）**：改为**从 intake 派生**（单一真源）；RC lifecycle **11/27 → 23/27**、PEAK **22 → 46**；剩 4 个仅含 intake `UNKNOWN` 的 RC **保持空**（**不虚构**，语义由 `research_status = INSUFFICIENT` 承载） | **已解除** |

### Driver Evidence Depth

当前最大 Research 质量债：
- Driver MATCH = 1/79（Historical Objects 扩容后）
- MULTI_MECHANISM = 4

后续如补证据，必须围绕真实缺口，不得以提高 SUPPORTED 数量为目标。

### Historical Date Verification

`campaign_date_observations = 24`，当前 verified = 0/24。

不阻塞 Architecture / Adapter；作为可信度债继续记录。

### Market / Temporal Context

继续：

**SUPPLEMENTARY_ONLY**

除非新的 Research question 明确要求，不进入 Structural Status。

### Coverage Expansion

**Wave 1C 暂停。**

仅在新研究问题证明必须扩容时重新开启。

> **同步（2026-09-19）**：第二次真实使用已确认瓶颈是 **Historical Universe 太窄**
> （4 个 Macro Theme · 85 条比较中仅 1 条 STRICT 结构对应）→ **触发条件成立**。
> Coverage Expansion 以 **R01 独立研究轮次**形式重新开启；
> **R00（Historical Universe Expansion / Research Intake Protocol v0.1）已完成基础设施**：
> - `research/intake/HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md`（协议）
> - `research/intake/HISTORICAL_UNIVERSE_COVERAGE_PLAN_v0_1.md`（覆盖方向）
> - `research/intake/historical_research_intake.schema.json`（交付结构）
> - `research/intake/HISTORICAL_UNIVERSE_R01_TASK_MANIFEST_v0_1.json`（R01-01 ~ R01-06）
> - `research/scripts/validate_historical_research_intake.py`（机器校验器）
>
> **同步（2026-09-23）**：**R01-01 ~ R01-06 已全部完成并入库**（52 Campaign + 27 Research Candidate），
> Historical Universe 由 17 → **79** objects。**Coverage Expansion 现已回到 `FROZEN / DEFERRED`。**
>
> 重新开启的**唯一条件**：新的 Research Question 证明「Historical Universe 不足」。

## 4. 当前明确不做

- 不继续扩 Time Observation Pattern
- 不继续调 Structural Analogy v0.2 规则
- 不为了提高 SUPPORTED 数量放宽规则
- 不新增 schema entity
- 不做 similarity score / percentage / probability / ranking
- 不做实时行情 / 资金流 / 通知 / 后台
- 不做新的 Radar / Dashboard
- 不在 Adapter 前重写 Product

## 5. 产品最终工作流

```
今天
  ↓
历史同期
  ↓
历史周期阶段
  ↓
当前研究对象
  ↓
历史结构对应
  ↓
为什么对应 / 哪里不同
  ↓
继续研究
```
