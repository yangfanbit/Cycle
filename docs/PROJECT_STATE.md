# PROJECT_STATE.md — ThreeC 当前真实状态

> 动态接班文档：只回答“现在是什么状态、哪里有问题、下一步做什么”。
> 长期规则见 `AGENTS.md`；未来路线见 `docs/ROADMAP.md`；历史细节见 `docs/CHANGELOG.md`。

## ★★ 当前状态（2026-10-18 修订 · 历史题材地图 ×6 + 行情可信展示 + 标的与 Research 对象对账）

> 上一版停在 2026-10-13。本节之后（10-14/15）完成了：历史事件地图**跨年份比较产品化**、
> 流感 **11 季**窗口统一（v0_6）、电力 10 年复核（v0_3）、事件级行情状态与端点可达性修复。
> ★★ **2026-10-16 上午：行情数据库拆分完成** —— `cycle_research.db` **66.15 MB → 0.96 MB**，
> 行情三表迁入**不入库**的 `market_data.db`，干净克隆由**被跟踪的便携快照**无网恢复。
> ★★ **2026-10-16 同日晚（长程任务 v0.5：研究数据治理与地图有效性）** ——
> ① `trading_calendar` 由 **371 行补全到 2,855 行**（口径 = 基准 `SH000300` 的 distinct 交易日，
> 无外部源；补全**不改变任何研究数字**，因**无一处交易日逻辑读该表**）；
> ② 流感 v0_6 / 电力 v0_3 的**陈旧文字与分类口径**更正（`corrections` 留痕，**数值零变化**）；
> ③ 组件三处误导性展示修复 + 5 条回归测试；④ readiness `--check` 措辞与覆盖面改正。
> 完整说明：`docs/MARKET_DATA_DB_v0_1.md`（拆分）与本文本节（治理）。
> ★★ **2026-10-18 晚（v0.16）**：① 新增**第 6 个历史题材「半导体 / AI 算力 / 存储」**纵切片
> （**7 事件 / 29 参与记录 / 16 只去重标的**，行情全部来自 `market_data.db` 实算；大基金三期窗口
> 登记标的不覆盖 → **逐条如实留空、不补数**）；② 把**反例（`COUNTER_EXAMPLE`）**从
> **证据不足（`INSUFFICIENT`）**中分离出来（各自类别、各自文案）。
> ★★ **2026-10-18 晚（v0.17）**：① **行情表可信展示** —— 不再只显示 `security_id`，显示**名称 / 代码 /
> 关系类别 / 窗口状态**；**只有 `COMPUTED`** 的标的按完整窗口展示，其余标
> 「**仅局部数据，不可视为完整窗口可比结果**」+ 实际可用首末日期，并**下沉分组**；
> 反例（`COUNTER_EXAMPLE`）单独标「反例（不同轴）」、数据仍可查看。② **标的 × Research 对象对账** ——
> 按 `campaign_facts.object_id`（兼容 `campaign_id`）与 canonical export 的 Campaign / RC `security_ids`
> **精确对账**，分**对象已登记关联 / 地图补充记录 / 无法核对**三类（**不猜身份、不改 Research 数据**），
> 在事件详情与标的索引逐次记录呈现，**六题材通用**（实测：123 条参与记录 = 已登记 63 / 地图补充 0 / 无法核对 60）。

### 实测基线（2026-10-18 · 全部实测）

| 项 | 值 |
|---|---|
| **git HEAD（真实）** | `bcfa36c`（**v0.17 实现**：历史行情可信展示 + 标的与 Research 对象对账）· ★ 若其后还有 `docs(state)` 回填提交，HEAD 会再前移一位 —— **接班必须跑 `git log -1`** |
| **最近功能提交** | `bcfa36c`（v0.17：行情可信展示 + 标的对账）· `0c8ee96`（v0.16：半导体/AI 算力纵切片 + 反例语义分离）· `59dedcc`（v0.15：汽车智能化纵切片）· `3edfe80`（v0.14：窗口→对象详情闭环）· `b522f02`（v0.13：线索→对照→研究请求闭环）· `8ecdb64`（v0.12：外部季节性时间轴）· `126ce8d`（v0.11：题材标的索引）· `50300f8`（v0.10：历史题材地图主入口）· `d3a01dc`（v0.9：概率层）· `05c897d`（v0.8：草稿交接 + 生命周期对照）· `f012dc3`（v0.7：草稿生命周期） |
| **快照** | **`MS-2026-10-13-01` = 唯一 `CANONICAL`**（实测 `index.json`：CANONICAL 计数 = 1；10-12 及更早 12 份 `ARCHIVED`，09-15 仍 `DRAFT`）· `candidates_source` = `artifact_version 0.13` / `rule_set_version structural-analogy-ruleset-v0.3`，与 SA `v0_13` **逐一相等** |
| **数据库拓扑** | `cycle_research.db` **0.96 MB**（canonical 17→14 表，**入库**） · `market_data.db` **65.62 MB**（行情三表 **376,401 行**，**不入库**） · `data/market/snapshot/` **6.09 MiB**（**入库**，恢复唯一输入） |
| **trading_calendar** | **2,855 行**（2015-01-05 ~ 2026-09-30，`calendar_type='cn'`）· 覆盖 `market_daily` **全部** distinct 日期 · **0** 个基准外日期 |
| **恢复命令** | `python research/scripts/restore_market_data.py --apply`（`--check` 校验；`--force` 重建）—— **无网络可用** |
| **快照格式** | 按年分片 `market_daily/YYYY.csv.gz` + `MANIFEST.json`（每分片 sha256）· repr() 浮点**逐位无损**（**2,053,911 个 REAL 差异 0**）· 两次生成 sha256 相同 · **376,401 行** |
| **历史宇宙** | **62 Campaign + 27 Research Candidate = 89 对象** · DB `themes` **59**（13 个根） |
| **测试** | **1383 passed / 0 failed / 68 files**（v0.17：+22 —— 对账 13 + 行情表可信展示 6 + v0.17 端到端 3；v0.16 计 1361/66) |
| **Export / SA / 快照** | Contract v1.2 · SA `v0_13` · 快照 `MS-2026-10-13-01` —— 均**未随拆分/治理改动** |
| **Research 门禁** | `validate_db` PASS（4 警告，同基线）· `validate_timeline_export` PASS（0 警告）· `validate_market_snapshot` 342/8/0 · `intake --check` PASS · `refresh_downstream --check` PASS · `resolve_sa_artifact` / `validate_monorepo` / `make_market_snapshot --check` 全 exit=0 |
| **CI** | deploy.yml 在 Research 门禁**之前**跑 restore `--apply` + `--check`（失败即 workflow 失败，不跳门禁）· ★ 真实提交 `975108f` 与 **`5d7efaa` 的 CI 均 success**（Actions runner 本身就是干净检出 = 干净环境实证；干净克隆另在本地复验：恢复 2,855 行日历 + 全部门禁 PASS + monorepo 25/25 + npm ci/tsc/**1021 测试**/build 全 OK） |
| **历史事件地图** | **v0.10 起为首页直接入口**（`HistoricalThemeMaps`，索引驱动 · **6 题材 / 26 事件**（流感 6 · 电力 4 · 传媒 2 · 机器人 1 · 汽车智能化 6 · 半导体/AI 算力 7）· 可切换）· 跨年比较已产品化（流感 **11 季** / 电力 **10 年**）· 经验基准概率区块（分母 = `comparable === true`：电力 **7** / 流感 **9**）· v0.5 审计结论：当时 13 事件数值零计算错误 · ★ **v0.17**：行情表带**关系类别 / 窗口状态**，参与者与标的索引带 **Research 对象对账**（六题材通用） |
| **版本** | 1.0 RELEASED（`v1.0.0` · `064d39c`）· 1.1 RELEASED（`v1.1.0`） |

### v0.5 批次已修（真实缺陷，逐条有 DB 实测依据）

| # | 缺陷 | 修法 |
|---|---|---|
| 1 | `trading_calendar` 371 行 vs 基准 2,855 个交易日（**2,484 个 `market_daily` 日期无日历**） | 重跑权威生成器 `seed_trading_calendar.py`（从 SH000300 distinct date 推导）→ **2,855 行**；随后**重生成快照**（顺序：先 seed 后 snapshot）并 `restore --check` PASS。★ 先证明**无消费者**才对数据动手 |
| 2 | 流感 v0_6 `cannot_conclude⑥` 称「疫苗三只 2023 行情为碎片」，而同文件 2023/24 季行自身 `coverage=FULL`、三只**实测各 102/102 交易日** | 按 DB 实测重写该条 + `can_conclude⑤` + `recommended_next_steps[1]` + 9 只 `db_coverage`；真实缺口改为**智飞生物（2023+）** |
| 3 | 三个事件级 `by_security` 用重复序列 id `YILING-002603`（与跨年表 `YILING` 撞成两个 id，同窗口数值完全相同） | 统一为 `YILING`（改名前后值已断言一致） |
| 4 | 三个事件 `window_text` 仍写「行情窗口待核验」（补数后已有完整行情表） | 删除陈旧短语 |
| 5 | power 两个**反例**事件被标 `THEME_ADJACENT`（定义 = 机制不同轴、仅供参考）→ 把最强负面证据挡在范围外 | 改判 `THEME_DIRECT`（label 仍写「反例」，证据方向不丢） |
| 6 | 「2023 恰是库内唯一登记 Campaign 的年份」未加限定（`rule_power_operation` 下另有 2021 新能源发电·开放式） | 两处补范围限定 |
| 7 | UI：「报道当日涨幅」区在 `by_security=null` 时恒显「无行情」，而 10/8 只报道点名涨幅一直在 `reported_same_day_moves` 里从未渲染（note 还引用不存在的「上表」） | 组件改为渲染 `reported_same_day_moves` |
| 8 | UI：阶段名只读 `phase_type`，研究侧真字段是 `stage` → `<strong></strong>` 空标签 | 两读 + 缺省「（阶段名未标注）」；类型同步 |
| 9 | UI：标的区标题硬编码「当次历史炒作标的」（机制池事件被说成炒作池） | 改中性「事件相关标的」，池性质交回各标的 `category`/`rationale` |
| 10 | readiness `--check`：① FAIL 一律叫「非 deterministic」（最常见其实是**产物过期**）② CSV 伴生产物**从不校验**（曾 85→534 行漂移永不报） | 措辞改为区分「过期 / 不确定」并指明处置路径；四份产物（含 CSV）全部纳入比对并**汇总报告** |
| 11 | `restore --apply` 遇不一致只提示 `--force`（诱导丢弃本地未快照数据） | 提示改为先判断「忘重生成快照」还是「确要重建」 |
| 12 | `make_market_snapshot` 源库回退分支可能静默从错源生成 | canonical 分支加断言（无表/0 行即 FAIL） |

### v0.6 批次已修（产品工作流验收与用户研究请求入口）

| # | 缺陷 | 严重度 | 修法 |
|---|---|---|---|
| 1 | ★★ **方向查询默认看不到当前研究对象**（`App.tsx` 默认传 `dataset=null`）→ 同页 Watchboard 展示汽车候选，而查询「汽车」答「只有历史案例」——**一页两个相反答案** | **P0** | 默认改为 canonical 数据集；★ 选取规则抽成纯函数 `selectCurrentCandidateDataset()`（`appDatasets.ts`）使「默认必须是 canonical」**可断言**，并补 App 层接线回归（5 条，含反向对照） |
| 2 | ★ **快照×SA 版本门禁 fail-open**：`if (expected && …)` 在快照缺 `candidates_source` / 缺版本字段时**短路放行**，静默合并来源不明的产物（与 2026-10-13 混版事故同模式） | 中（潜伏） | 改为 **fail-closed**：版本字段缺失/空串一律拒绝合并（诚实「未解析」）；补 7 条回归测试（`snapshotVersionGate.test.ts`） |
| 3 | ★ **覆盖边界横幅过期**：硬编码称「煤炭 / 电力 / 流感疫苗 / 文化传媒 一个都没有命中」，而这四个方向**此后都已入库**（DB 实测：`TH-MEDIA` 文化传媒为**根主题**、`TH-RES-COAL` 煤炭、`TH-POWER-OP` 电力（运营端）、`TH-PHARMA-FLU` 流感疫苗） | P1 | 改为**数据驱动**：由 Contract v1.2 `taxonomy` 段实时列出根大主题，不再人工维护（已两次落后于数据） |
| 4 | **SA UI 测试清单漏第 6 个候选**（`ALL_CANDIDATE_IDS` 手写 5 个，缺 `CC-2026-AUTO-SMARTDRIVE`）→ 汽车方向从未被该套 UI 测试覆盖 | P2 | 补齐 + 加**清单完整性断言**（手写清单必须与数据集逐一相等，防再次漂移） |
| 5 | **无用户研究请求入口**（用户关心的方向无法转化为可交接的研究请求） | P2 | 新增**草稿**能力（扩建 `DirectionLookupSection`，非新建第二套）：5 字段表单 + 覆盖查询结果随行 + JSON/Markdown 导出/复制 + 本机 localStorage；★ 无正式 ID、不入库、不上传 |

### v0.7 批次已修（研究请求生命周期可靠性与覆盖语义校准）

> 本轮**只做产品侧的可靠性修复**，**不是**研究能力扩展：未新增 Campaign / Research Candidate、
> 未改 schema / canonical export / 冻结 SA / CANONICAL 快照、未改行情库拆分与快照结构。
> ★ 4 个并行工作流（A 草稿存储 · B 查询关联 · C taxonomy 语义 · D 测试基础与回归）。

| # | 缺陷 | 严重度 | 修法 |
|---|---|---|---|
| 1 | ★★ **清空草稿后被立刻回填** —— 判定是「方向字段为空就填」，于是①点「清空草稿」后立刻被填回；②**手动删掉方向也会被填回** ⇒ 该字段在有查询时**等同不可清空**；且清空未清关联状态与复制态 | **P0** | 判定抽成纯函数 `shouldAutoFillDirection()`：**只对空草稿**自动填一次，并记住「用户为哪个查询显式清空过」（`userClearedFor`）→ 清空是真的清空；清空动作**同时**清表单 + 关联 + 持久化 + 复制态 |
| 2 | ★★ **存储内容缺结构校验** —— `JSON.parse` 只挡语法错误；**合法 JSON 但字段类型错误**（`{"direction":123}`）会被展开进草稿，下游 `.trim()` 抛 `TypeError` → **组件崩（浏览器与 SSR 都崩）** | **P0** | 新增 `researchRequestDraftStorage.ts`：`normalizeDraft()` **白名单 + 逐字段校验 + 超长截断 + 未知字段丢弃**；**非字符串一律置空**（**不** `String()` 强转，避免把坏数据伪装成合法内容） |
| 3 | ★ **存储异常静默 / 假装保存成功** —— `setItem` 抛错（配额 / 权限）被吞掉，UI 却仍写「存在本机」；`window` 仅在 try/catch 里被**副作用式**保护（**0 处 `typeof window` 守卫**） | P1 | `loadDraft`/`saveDraft` 返回**结果对象**（`unavailable` / `corrupt` / `write_failed` …），UI 据此显示「**未保存到本机**」「**刷新后会丢失**」；`browserDraftStorage()` 是唯一触碰 `window` 处（显式探测） |
| 4 | ★ **恢复语义缺失** —— 损坏记录**直接崩**；且 v0.6 只在有查询结果时渲染草稿区 → 恢复的草稿在用户再查一次之前**看不见**，再查时新查询结果又会**冒充原证据** | P1 | 损坏记录 → `corrupt` 状态**披露且不覆盖新输入**；草稿区改为「有查询 **或** 草稿非空」即渲染（恢复可见可编辑） |
| 5 | ★★ **查询证据静默漂移** —— 导出时直接取「当前查询结果」；用户先查「汽车」（方向自动填「汽车」）再改查「医药」→ 草稿还是汽车的，证据却变成**医药的**（**两份请求静默混合**） | **P0** | 草稿新增 `linkedQuery` / `linkedAt` / `linkedCoverage`（**冻结证据**）；导出新增 `linkage{linked_query, current_query, changed, evidence_source, …}`；换查询**只披露**「与本草稿证据不同」，**不改绑**；新增显式「**以当前查询新建草稿**」按钮 |
| 6 | ★★ **未查询却导出 `verdict: "none"`** —— 恢复草稿（无 live 查询）时 `verdict` 落到默认值 `'none'`，与真实「两侧都没覆盖」**字面完全相同** → 读者必然误读 | **P0** | 未执行查询时 `verdict` 改为 **`null`** + `executed: false`；Markdown 明确写「**未关联任何覆盖查询**，不代表「未覆盖」」 |
| 7 | ★★ **横幅把分类事实说成覆盖承诺** —— 写「不在此列表内的方向即为**未覆盖**」；实测**假**（46 个非根主题名里 44 个能命中历史对象；「电力」甚至不是库内主题名却 `both`） | P1 | 横幅改为「**分类体系**有 N 个**根主题**」+ 明说「**不在根清单里 ≠ 未覆盖**，具体结论以**方向查询的实际命中**为准」+ 列出**四个互不相同的事实**（分类有根 / 查询命中 / 冻结 SA 结构对应 / 资料不足 vs 无对应） |
| 8 | ★ 方向查询的「未覆盖」说明**硬编码「44 个主题名」**（实测 59） | P2 | 改为由 `resolution.taxonomySize` 注入（`noneExplain(n)`，纯函数可测） |

### ★★ 测试能力边界（v0.7 显式声明 —— 不得再用静态 HTML 宣称交互已验证）

- 测试环境是 `environment: 'node'`（**无 jsdom / 无 testing-library**）。
- ★★ **SSR（`renderToStaticMarkup`）不执行 `useEffect`** —— 实测确认（effect 体与 cleanup 均不跑；
  `useState` 初始化函数**会**跑，这正是 `loadDraft()` 在 SSR 下被调用的原因）。
- → 因此**「保存 / 恢复 / 清空 / 回填 / 点击」等生命周期行为，静态渲染测试无法验证**。
  v0.7 的处理办法（**不加依赖**）：
  · 把存储与判定抽成**纯函数 + 可注入接口**（`researchRequestDraftStorage.ts`）→ 在 node 下直测；
  · 组件只保留「把 props 渲染出来」的部分 → 用静态渲染验证**文案与状态披露**；
  · 并**更正**了 3 处会误导的测试标题（原称「可点击进入」/「接通 → 打开」，实际只验证渲染）。
- ★ 是否加 jsdom：**本轮判定不需要**（已确认缺陷都在**逻辑**而非 React 调度层）。
  若将来要测「点击 → state 变」，需重量级 devDep + 按文件切 environment —— 届时另行决策。
- 另：`<App />` 此前**在 node 下渲染即崩**（`window is not defined`），这也是「App 层零测试」的原因之一；
  v0.7 把 3 处 URL flag 与路径访问改为 **SSR 安全**（无 `window` → 默认模式），
  于是**新增了 App 层的分类体系横幅测试**（守住「横幅与查询结论不矛盾」这类跨区块 bug）。

### v0.8 批次已修（草稿交接三缺陷 + 生命周期对照交付）

> ★ **只做产品实现**：未新增 Campaign / RC、未改 schema / canonical export / 冻结 SA /
> CANONICAL 快照、未动行情库拆分、无网络无 LLM、不云同步。
> ★ 4 个并行工作流中 A/B 完成并产出证据；C/D 因外部限流未启动，其职责
> （jsdom 可行性实测、文档与发布验收）由主 Agent 直接完成。

#### ① 草稿交接三缺陷（A 节，全部有 jsdom 真实点击回归）

| # | 缺陷 | 修法 |
|---|---|---|
| 1 | ★★ **「以当前查询新建草稿」关联永不建立** —— 只设 `direction`，指望后续自动回填 effect 补关联；而 effect 守卫是 `isDraftBlank(draft)`：`direction` 非空 ⇒ **不 blank** ⇒ effect **不跑** ⇒ 导出仍显示「未关联任何查询」 | 新增纯函数 `buildLinkedDraft(query, r, at)` **一次性**写全 `direction` + `linkedQuery` + `linkedAt` + `linkedCoverage`；自动回填与新建草稿**共用**它（防两处漂移） |
| 2 | ★★ **命中依据 `matchedOn` 五处丢失** —— `DirectionHit.matchedOn` → `LinkedCoverage` → localStorage → JSON → Markdown，**每层都只留 id/title**，导出层甚至写死 `matched_on: []` | 全链路保留：`CoverageHit.matchedOn: string[] \| null`（`null` = **旧草稿未保存该信息**，`[]` = 上游确实无依据）；`draft_version 0.2 → 0.3`、存储结构版本 `__v 3`；**存储键不换**（换键会丢用户在机草稿）；旧数据**不得**用当前 live 查询回填依据 |
| 3 | ★ **复制失败无反馈** —— catch 只 `setCopied(null)`，用户既不知道失败、也不知道下一步（预览是折叠的） | 新增 `src/data/timeline/clipboard.ts`：`copyTextToClipboard()` 分级降级（`navigator.clipboard` → `execCommand`）并**返回结果对象**；失败 → 明确文案「复制失败：…」（按 `unavailable` / `rejected` / `no_dom` / `no_platform` 分因）+ **自动展开导出预览**；**绝不**显示「已复制」 |

★ 顺带修掉 3 个连带问题：① `serializeDraft` 只看 `isDraftEmpty` → 「仅有关联」的草稿被误删（与 `loadDraft` 的合取不一致）→ 改 `isDraftBlank`；② 序列化写的 `__v` 被 `normalizeDraft` 当未知字段每次报一条 issue → 进白名单；③ payload builder 直读 `h.matchedOn`，未过 normalize 的对象会得 `undefined` → `?? null`。

#### ② 功能交付：生命周期对照（B 节）

- 新增 `src/components/CurrentTimeLens/LifecycleComparisonSection.tsx`，宿主 = `CurrentCandidateSection` 的
  `CandidateDetail`，**紧随 SA 之后**（先看唯一权威的结构对应，再看并排展示的阶段对照）。
- 呈现 = **两列表格**（刻意不做甘特/时间轴：画轴需归一化两侧尺度，属「为图表重建数据管线」）：
  左列当前侧研究自述（`attention_state` + `phase_window`），右列历史对象阶段序列（导出**原序**，
  标注起点/终点/**开放区间**/精度），末列**原样引用**冻结 SA 的 lifecycle 维度。
- 默认只列 SA 判为「结构支持」的历史对象；`COMPUTE-POWER` / `OFFSHORE-WIND` **零 SUPPORTED → 诚实空态**。
- 入口用 `onSelect`（**不**带 SA 上下文）—— 本区不是结构声明，附上下文等于把描述当结论。
- ★★ 前置必修的真实缺陷：`COMPARISON_POINT_UNKNOWN`（534 条 SA 里 **24 条**）**不在**类型 /
  文案 / `INDETERMINATE_DIMENSION_STATUSES` 里 → 回落英文且**不被识别为不确定**；
  `isIndeterminate()` 又**硬编码**两个值 → artifact 自己把它列入 `unknown_dimensions` 而函数说
  「不是未知」（被既有测试抓到）。→ 类型 + 文案 + 常量集三处补齐，`isIndeterminate` 改为读常量。
- ★ 另补 `LIFECYCLE_STAGE_LABEL.ENDED`（Contract 11 阶段之一，导出实测 2 条，此前无标签）。

### ★★ 测试能力边界（v0.8 更新：引入 jsdom）

- **本版本轮起引入 `jsdom`（devDependency）** —— 用户明确允许「必要时引入轻量测试依赖」。
  用**文件级** `// @vitest-environment jsdom`，**不影响**其它 44 个文件仍跑在 node 下。
- 于是 **v0.7 声明的「交互无法自动化」已被打破**：`draftInteraction.test.tsx`（7 条）用
  `react-dom/client` + `act` **真点真输入**，覆盖用户要求的 5 条交互：
  ① 查询→建草稿、导出与页面一致 ② 改查询→证据不漂移+披露变更 ③ 点「以当前查询新建草稿」→
  一次性关联新证据 ④ 清空→不被回填、**刷新（重挂载）后也不恢复** ⑤ 剪贴板失败→不假报成功+
  预览自动展开。
- ★ 仍未自动化（诚实声明）：`document.execCommand` 在 jsdom **未实现** → 降级路径由
  `clipboard.test.ts` 以**注入 env** 覆盖；生命周期对照的「打开历史案例」真实跳转、以及
  `useLayoutEffect` / 布局相关行为仍靠人工验收。
- ★ 踩坑记录：jsdom 下 `document` 在同文件所有用例间**共享** → 失败的用例若没 unmount 干净，
  后续用例的 `querySelector` 会读到别人的 DOM（实测踩到）。→ 测试用**作用域化 Session**（
  `host.querySelector`）+ `afterEach` 清 `document.body`。

### v0.9 批次（概率研究开放 + 首个经验基准概率原型）

> ★ **只做产品与研究表达**：未新增 Campaign / Research Candidate、未改 `schema.sql`、
> 未重算冻结 SA / CANONICAL 快照、未改任何事件数据数值、未动行情库拆分、无网络、无 LLM。
> ★ 4 个工作流：A（规则修订与全局审计）· B（跨年份统计与区间）· C（展示修复与 UI 接入）·
> D（真实数据测试、样本外评估可行性、发布验收）。

#### ① ★★ 规则调整：撤销「概率 / 预测」全局禁令（A 节）

`AGENTS.md` §1 原来把「价格或收益预测」「概率 / 胜率 / 推荐分」列为**禁止做**的产品形态。
v0.9 改为：**可以研究**历史频率 / 条件概率 / 阶段变化概率 / 未来窗口预测，
但必须满足**准入条件**（新增 §3.1，长期有效）：

1. 口径七要素写明：预测目标 · 样本范围 · 观察期限 · **分母** · 排除规则 · 来源 · 不确定性；
2. 分母只含**完整可比较**观察；`partial` / 不可比 / 缺数据**逐条列出原因**，不得算成成功或失败；
   ★ `ThemeAnnualRow.comparableYears` **不是**分母（它只数「含历史窗口的年份」）；
3. 结果定义**来自原数据**（沿用 `outcome_rule`），不得把「任意上涨」当作严格规则的成功；
4. 不确定性必须显示（二元比例给 **95% Wilson 区间**，小样本自然宽）；
5. 新预测模型**必须按时间顺序验证**（禁随机拆分 / 禁未来信息泄漏），与**简单历史基准**比较，
   记录 **Brier / Log Loss / 校准 / 样本量**；
6. 价格 / 收益预测**不自动等于买卖建议**；但概率输出不得与买卖措辞共现、不得生成买卖信号；
7. 架构不变：Research 生产 · Product 消费版本化产物 · 纯静态 / 不联网 / 不调 LLM。

**三层口径**（产品与文档都必须分开）：① 历史统计描述 → ② **经验基准概率**（未校准）→
③ 已验证预测模型（**目前没有**）。②不得写成「未来概率」。

★ **真实语义守卫全部保留，只限定范围**（不删断言）：
`timeObservationPatterns` 的 `expectNoPredictiveLanguage` 明确限定为 **Time Observation 层**；
`seasonalMap` / `researchWorkflow` 的禁词测试标题改为「**本层**不引入…」；
`researchRequestDraft` 的 `DRAFT_CONSTRAINTS` 原写「不给概率；不做预测」（现已不成立）→
改为「本文件本身不含概率或预测数值（若请求涉及历史频率 / 条件比例，须在正式研究中声明分母、样本与不确定性）」。

#### ② ★★ 首个经验基准概率原型（C 节）

- 计算模块：`src/data/timeline/empiricalProbability.ts`（纯函数，无 IO）
  · `wilsonInterval(k, n, z)` · `computeEmpiricalEstimate(years, target)` ·
  `timeOrderedBaseline(years, target)` · `assessModelFeasibility(ev)` ·
  `empiricalTargetOf(doc, cmp)`（**只读定义**，缺 `outcome_rule` → 返回 `null`，宁可不展示）
- UI：`src/components/ExternalSeasonalRadar/EmpiricalProbabilityBlock.tsx`，
  挂在**既有**「跨年份比较」区段内部（`CrossYearSection` 年份表之后），**不另造第二套地图**。
- 展示：目标定义（含 `outcome_rule` 原文）· 结果分布 · **k/n + 95% Wilson** ·
  计入分母年份 · 成功年份明细 · **排除表（逐年带源数据原因）** · 机制分布 · 三层口径说明 ·
  模型可行性（默认折叠）。

**实测结果（全部由数据算出，无硬编码）**：

| 题材 | 分母 | 成功 | 比例 | 95% Wilson | 排除 |
|---|---|---|---|---|---|
| 电力（迎峰度夏 5–7 月） | **7** | **1**（2022） | 14.3% | **2.6% – 51.3%** | 2016 / 2019 / 2024（`partial`，交易日不足或末笔早于窗口末） |
| 流感（9 月–次年 1 月） | **9** | **1**（2019/20） | 11.1% | **2.0% – 43.5%** | 2015 / 2016（`partial`） |

★★ **流感的关键事实**：唯一 UP 年（2019/20）的窗口内事件类型是 **`UNKNOWN_PUBLIC_HEALTH`**
（2019-12 武汉不明原因肺炎），**不是流感**；`SEASONAL_FLU` 的 4 个完整可比年份 UP 计数 = **0**。
→ 页面原样列出事件类型，**不把价格结果写成机制成功**。

★ 电力逐年没有 `event_type` → 机制桶显示 `UNRECORDED`（**不猜**成某个机制）。

#### ③ 模型可行性（D 节）：**不训练**

- 评估方式：**严格按年份升序** expanding-window；第 i 年只用**严格早于**它的年份估计历史频率；
  **不做**随机拆分（会打乱时间顺序）。
- 门槛**预先声明**：`MODEL_MIN_OUT_OF_SAMPLE_STEPS = 30`（写死在代码里，先定门槛再看数据）。
- 实测：

| 题材 | 样本外步数 | Brier | LogLoss | 结论 |
|---|---|---|---|---|
| 电力 | **4**（7−3） | 0.267 | **5.282** | 不训练 |
| 流感 | **6**（9−3） | 0.046 | 0.231 | 不训练 |

★ 电力 LogLoss 5.28 的来源是**一次「预测 0 实际 1」**（2022）→ `-log(1e-9)` ≈ 20.7 被平均进 4 步。
这正是「样本太小 + 基线无特征」的直接后果，**不是**模型缺陷。
- 缺什么（页面逐条列出）：样本外步数不足（缺 26 / 24 步）· 完整可比年份仅 7–9 个 ·
  **缺事前特征**（窗口开始前可观测：库存 / 来水 / 煤价 / 气温 / 政策日历）· 缺跨题材样本。

#### ④ v0.8 遗留展示修复（B 节）

| # | 问题 | 修法 |
|---|---|---|
| 1 | `LifecycleComparisonSection` 的 caption 写「左列 = 当前研究对象」，而表头第一列是**历史对象**（说明与表头矛盾） | caption 改为「左列 = 历史对象 · 第二列 = 当前研究对象 · 第三列 = 阶段序列」，并加断言锁死顺序 |
| 2 | 历史阶段只显示起止，**没有持续时间** | 新增 `src/data/timeline/lifecycleDuration.ts`：`EXACT_DATE` / `DATE_WINDOW` 且起止不同 → 给天数 + 近似月数；**开放区间 / 单日锚点 / 缺日期 / 阶段窗口精度 / 起止倒置 / 不可解析** → 逐项说明**无法计算**（实测电力/流感数据里 129 个单日锚点、15 个开放区间、347 个阶段窗口精度） |
| 3 | 生命周期区与概率区**露出 Markdown 星号**（JSX 不解析 `**`） | 统一按 `**` 切分渲染 `<strong>`（含源数据自带 `**` 的 `forbidden_comparison` / `outcome_rule`），并加「渲染结果不含 `**`」断言 |
| 4 | README 状态表停在 **2026-10-13 / 881 测试 / 33 files** | 更新为 2026-10-18 / **1222 / 51**，并补概率层与「预测模型未建立」两行 |

#### ⑤ 验证（全部实测）

```
npx tsc -b OK · npm run build 成功 · npm test **1223 passed / 0 failed / 51 files**（+56）
新增：empiricalProbability 27（Wilson 数学性质 / 分母筛选 / partial 排除 / UP 严格规则 /
      流感非流感机制 / 缺失数据 / 时间前推无泄漏 / Brier-LogLoss 可复算 / 可行性门槛）
      EmpiricalProbabilityBlock 15（分母与区间上屏 / 排除原因 / 三层口径 / 校准分箱 / 无字面星号 / 无买卖词）
      lifecycleDuration 9（六类「不能算」原因逐条）/ LifecycleComparisonSection +5（列序 / 时长）
Research 门禁：validate_db PASS · validate_timeline_export PASS · validate_market_snapshot 342/8/0
      intake --check PASS · refresh_downstream --check PASS · resolve_sa_artifact / monorepo / restore 全 exit=0
```

### v0.10 批次（历史题材地图主入口 + 概率基准修正）

> ★ **只做产品入口与展示**：未新增题材、未补造事件、未改写任何历史行情数值、
> 未改 `schema.sql` / canonical export / 冻结 SA / CANONICAL 快照、无网络、无 LLM。

#### ① ★★ 主交付：历史题材地图成为**直接入口**

**问题**：v0.9 之前，4 个题材的历史事件地图**只能**从「外部季节性观察雷达」的线索卡里间接进入 ——
用户必须先展开「全部线索」、找到某条外部线索，才能在卡内看到地图。
但地图是 **ThreeC 自己的历史事后重建**，与「外部资料声称的窗口」是两种东西；
把它藏在外部线索里，等于让用户以为它也是外部参考。

**修法**（复用，不重建）：

- 新增容器 `src/components/HistoricalThemeMaps/HistoricalThemeMaps.tsx`：
  **索引驱动**（`allResolvedEventMaps()`）列出全部已建地图题材，通过题材切换渲染
  **同一个** `HistoricalEventMap` —— 事件卡 / 跨年份比较 / 经验基准概率**全部原样复用**，
  **没有**第二套事件卡实现。
- 位置：首页「季节性地图」之后、「外部季节性观察雷达」之前 → **首屏即可切换**，
  不需要展开任何外部线索。
- 计数全部现算：题材数来自索引，事件数来自 `doc.events.length`（**不读**索引里的 `event_count`，防漂移）。
  当前实测 **4 个题材 / 13 个事件**（流感 6 · 电力 4 · 文化传媒 2 · 机器人 1）。
- ★ **雷达职责收窄**：不再内嵌完整地图（同一批 13 个事件会渲染两遍），
  改为「该线索已有历史事件地图（N 个事件）→ 在「历史题材地图」中查看」的**跳转指针**
  （点一下即选中该题材并滚到区块；无 `onOpenMap` 时只给事实说明，**不假装可点**）。
- ★ 顺手修掉地图里的**可见缺陷**：源数据文本（`display.note` / `class_caveats` / `reading` /
  `limitations` / 事件 `label` / `window_text` / `evidence_basis` / 催化 `text` / 阶段 `description` /
  标的 `rationale` / `known_gaps` …）此前把 `**强调**` **原样显示成星号** → 统一按 `**` 切分渲染
  `<strong>`；`title` 属性无法放标签 → 去标记。

#### ② 概率基准修正（B 节，小修）

| 问题 | 修法 |
|---|---|
| 训练集成功数为 0 时原始频率 = **0**，LogLoss 用 `1e-9` 裁剪 → 一次未预料到的成功即 `-log(1e-9) ≈ 20.7`，**整组结果被单样本主导**（v0.9 电力 LogLoss 5.28 就是这么来的） | 评估基准改为 **Jeffreys 平滑频率** `(k + 0.5) / (n + 1)`（`JEFFREYS_ALPHA/BETA = 0.5`，**固定先验、不调参**）；Brier / LogLoss 用**实际展示的**逐步预测值计算；原始 `k/n` 另存 `rawFrequency` 作参照 |
| 原始经验比例与区间**不得**被平滑污染 | `computeEmpiricalEstimate` **未改**：`rate = k/n`（电力 1/7 · 流感 1/9）、Wilson 区间**仍是未平滑值**；页面明写「平滑只用于评估」 |
| `assessModelFeasibility()` 只看步数 → 「步数达标」被当成「已具备训练条件」，而现有数据**一个事前特征都没有** | 拆成**两道门槛**：`stepsSufficient`（≥ 30 步）· `featuresSufficient`（≥ **3** 个事前特征，`MODEL_MIN_EX_ANTE_FEATURES`）；`sufficient`（训练条件）= 两者**同时**满足；结论文案明写「**步数达标 ≠ 可以训练**」；UI 分三格显示（步数 / 事前特征 / 训练条件） |

**实测（重算后）**：

| 题材 | k/n（未平滑） | 95% Wilson | 样本外步数 | Brier | LogLoss | 训练条件 |
|---|---|---|---|---|---|---|
| 电力 | **1/7 = 14.3%** | 2.6% – 51.3% | 4 | **0.234**（原 0.267） | **0.741**（原 **5.282**） | 不具备（0 个事前特征） |
| 流感 | **1/9 = 11.1%** | 2.0% – 43.5% | 6 | **0.067**（原 0.046） | **0.291**（原 0.231） | 不具备（0 个事前特征） |

★ 平滑的代价也要说清：流感 LogLoss 从 0.231 **升到** 0.291 ——
因为预测不再贴着 0（原始频率 0.13 被抬到 0.167），对「实际 0」的拟合略差。
这正是「不假装确定」的成本，**不是**退步；电力的 5.28 → 0.741 才是修掉的那个真问题。

★ **不训练新模型**，也不把平滑后的回测描述成已验证预测模型。

#### ③ 验证（全部实测）

```
npx tsc -b OK · npm run build 成功 · npm test **1245 passed / 0 failed / 53 files**（+22）
新增：HistoricalThemeMaps 11（入口 / 索引驱动 / 计数现算 / 概率区块归属 / 雷达指针）
      HistoricalThemeMaps.interaction 2（jsdom 真点：题材切换 / 受控模式）
      empiricalProbability +6（Jeffreys 公式 / 单样本不再主导 / 两道门槛分离）
      EmpiricalProbabilityBlock +3（基准标注 / 原始 k/n 与平滑值并列 / 三格门槛）
```

### v0.11 批次（历史题材标的索引 + 跨事件证据追踪）

> ★ 只用**现有**题材 / 事件 / 参与标的 / 证据 / 行情数据：未新增题材或事件、未改 `outcome` 规则、
> 未编造指数、未改 `schema.sql` / canonical export / 冻结 SA / CANONICAL 快照、无网络无 LLM。

#### ① 新增：题材 → 参与标的 → 跨事件记录

**动机**：v0.10 的入口只能「按年看事件」。用户真正会问的第二层问题是
「这个题材历史上涉及哪些股票、各自出现在哪几年、当时为什么被纳入」。

- 聚合模块 `src/data/timeline/themeSecurityIndex.ts`（纯函数，无 IO）：
  `themeSecurityIndexOf(doc)` · `filterSecurityIndex(index, q)` ·
  `evidenceSummaryOf(entry)` · `SECURITY_INDEX_DISCLAIMER`
- UI `src/components/HistoricalThemeMaps/ThemeSecurityIndexSection.tsx`，
  放在 `HistoricalThemeMaps` 当前题材面板内、**逐事件列表之前**；
  数据完全来自当前题材 `doc.events[].participants`，**不复制**研究数据、不建第二套地图。
- 展示：公司名称 / 代码 / 涉及事件数 / 出现年份 / **逐次统计的证据类别**；
  展开后逐次列出：事件（年 + 标题）/ 参与类别 / 证据等级 / 纳入理由 / 来源 /
  同期报道当日涨幅 / 该事件实测行情（区间 / 至高点 / 超额，**按该事件原口径**）。
- 搜索：按名称 / 代码 / **历史别名**（如 `ST香雪`）过滤；无命中时明说
  「本索引只含**已记录**的参与标的，**未记录 ≠ 未参与**」。

**实测（真实数据）**：

| 题材 | 标的数 | 出现次数 | 有标的事件 |
|---|---|---|---|
| 流感 / 邻近公共卫生 | **20** | 42 | 6 |
| 迎峰度夏 / 电力运营 | **6** | 21 | 4 |
| 文化传媒 | **4** | 4 | 2 |
| AI+ / 机器人 | **5** | 5 | 1 |

★ 流感 21 条参与者记录合并为 **20 只**：`XIANGXUE-300147` 在 2024 年改名为「香雪制药（ST香雪）」，
按 `security_id` 合并为同一标的，**两个名称都保留**（展示名 + 别名）。

#### ② ★★ 证据区别（本轮的核心约束）

| 规则 | 实现 |
|---|---|
| `REPORT_NAMED` = 同期报道点名，**不等于**业务机制已证实 | 逐次显示「仅报道点名」；不因出现次数多就升级 |
| `BUSINESS_VERIFIED` = 业务有独立资料，**不等于**驱动了当次行情 | 逐次显示「业务机制已核实」；配合 `business_mechanism_caveat` 原文 |
| **不得**合成「概念相关度」分数 | 无 score / rank / relevance 字段（测试钉死 `Object.keys`） |
| **不得**跨事件汇总收益率或做统一排名 | 行情数字只挂在**单次 occurrence** 上；entry 上**没有** `periodReturnPct` 等字段 |
| 同一标的跨事件可能是**混合**证据等级 | 摘要按类型计数（`业务机制已核实 ×1 · 仅报道点名 ×1`），**不取最高级**当整只股票的标签 |
| 报道点名但**未关联**参与者的记录 | `unlinkedReports` 独立状态 `REPORTED_NOT_LINKED`；只在 `security_id` 或 `ticker` **完全相等**时关联，否则**不猜身份**（当前真实数据 0 条，用合成输入测该分支） |
| 排序 | **只按公司名称**（中文 locale）→ `security_id`；**不按**涨幅 / 出现次数（测试断言顺序 ≠ 次数降序） |

#### ③ 顺带整理

- 把 `RichText` / `plain`（源数据 `**强调**` 渲染）抽成共享组件 `src/components/RichText.tsx`，
  `HistoricalEventMap` 与 `EmpiricalProbabilityBlock` 改为引用 —— 消除三份重复实现。
- 修正 v0.10 的入口说明：`PROJECT_STATE` / `ROADMAP` 里「地图只能从外部雷达进入」的表述已过期。

#### ④ 验证（全部实测）

```
npx tsc -b OK · npm run build 成功 · npm test **1261 passed / 0 failed / 55 files**（+16）
新增：themeSecurityIndex 12（跨事件汇总 / 名称变体合并 / 混合证据 / 排序 / 无收益汇总字段 /
      未关联报道独立状态）
      ThemeSecurityIndexSection.interaction 2（jsdom 真点：搜索 / 展开 / 收起）
      HistoricalThemeMaps +2（四题材索引都在且位于事件列表之前 / 无字面星号）
```

### v0.12 批次（完整外部季节性时间轴）

> ★ 只做产品呈现：未新增题材 / 线索、未补造日级日期、未改外部日历数据、
> 未改 `schema.sql` / canonical export / 冻结 SA / CANONICAL 快照、无网络无 LLM。

#### ① 主交付：25 条外部线索全部上轴

- 数据层 `src/data/timeline/externalSeasonalTimeline.ts`（纯函数）：
  `buildExternalTimeline(entries)` · `segmentsOfWindow(w)` · `isActiveInMonth` · `segmentAt` ·
  `crossYearNote` · `EXTERNAL_TIMELINE_NOTE`
- UI `src/components/ExternalSeasonalRadar/ExternalSeasonTimeline.tsx`，
  位于 `ExternalSeasonalRadar` 内、详细卡片**之前**；**一个筛选器**同时作用于时间轴与卡片。
- 呈现：12 个月表头 × 每条线索一行（名称 / 类别 / 窗口原文 / 映射状态 / 地图跳转），
  填充格 = 该月在该线索声称的窗口内；跨年窗口用深一档底色区分。

**实测（全部由 `externalCalendarEntries()` 现算）**：

| 项 | 值 |
|---|---|
| 外部线索总数 | **25** |
| 有月份窗口 | **23**（上轴） |
| 无固定窗口 | **2**（`EXT-23` / `EXT-24`，单列「事件驱动 / 无固定窗口」区） |
| 窗口段数 | **24** |
| 跨年窗口 | **4**（EXT-10 12→2 · EXT-11 10→3 · EXT-12 9→1 · EXT-21 11→1） |
| 上轴显示段数 | **28**（跨年拆到年末 + 年初） |
| 映射状态 | 已映射 **16** / 未映射 **9** |

★ 每月覆盖条数（1→12 月）：6 · 4 · 5 · 3 · 3 · 6 · 6 · 5 · 6 · 6 · 5 · 5。

#### ② 口径与边界（全部有断言）

| 约束 | 实现 |
|---|---|
| **月份精度**，不推断日级 | 只输出 `1..12`；页面不出现任何 `YYYY-MM-DD`（测试扫描） |
| **跨年正确拆分** | EXT-11 → `[10,11,12] + [1,2,3]`；EXT-21（两窗口）→ `[3] + [11,12] + [1]` |
| **无窗口不消失** | EXT-23 / EXT-24 在独立区，仍带「外部参考」与映射状态 |
| **UNMAPPED 正常显示** | 9 条全部可见，不因未映射被隐藏或折叠 |
| **一律外部参考** | 每条带「外部参考」徽标；`MAPPED` 只写「已映射 · 宏观主题」，**不写成 ThreeC 结论** |
| **跳转只在真有关系时** | `eventMapByExternalId()` 有值才给按钮（**4 条**：EXT-12/13/14/23）；其余 **21 条**明写「未建历史题材地图」 |
| **不再藏 21 条** | 详细卡片默认**全部展开**（25 张），折叠按钮改为「收起 21 项的详细卡片」 |
| **与历史地图区分** | 本区统一**琥珀色** + 「外部资料参考」徽标 + 明写「与历史季节性地图不同源、不同色、不合并」 |

#### ③ 顺手修复

- `themeSecurityIndex` 的**同年多名称**规则：原实现先 push 年份再比较，导致
  `e.year >= latestYear` 恒真 → 同一年里「最后遇到的名称获胜」（依赖事件顺序）。
  改为先记 `prevLatestYear`：**更晚年份优先**；**同一年取字典序最小** —— 与顺序无关。
  测试用两份顺序相反的合成 doc 断言展示名一致。
- `PROJECT_STATE` 把**真实 git HEAD**（文档回填提交）与**最近功能提交**拆成两行 ——
  此前一行混写，会让接班人误以为 HEAD 就是功能提交。

#### ④ 验证（全部实测）

```
npx tsc -b OK · npm run build 成功 · npm test **1282 passed / 0 failed / 56 files**（+21）
新增：ExternalSeasonTimeline 19（完整覆盖 / 跨年拆分 / 无窗口 / 映射状态 / 跳转 / 来源区分）
      themeSecurityIndex +2（同年多名称确定性）
      重写 1 条既有断言（折叠区默认收起 → 默认展开全部 25 条）
```

### v0.13 批次（季节性线索 → 历史窗口对照 → 研究请求闭环）

> ★ 只做产品打通：未新增题材 / 线索 / 历史对象、未改外部日历与事件数据数值、
> 未改 `schema.sql` / canonical export / 冻结 SA / CANONICAL 快照、无网络请求（产品侧）、无 LLM。

#### ① 主交付 A：外部窗口 × 历史 `MAIN_RISE` 并排对照

- 数据层 `src/data/timeline/externalThemeComparison.ts`：`compareExternalToTheme(entry, macroRows)`
  · `fracToMonthLabel` · `THEME_COMPARISON_DISCLAIMER`
- UI `ExternalSeasonTimeline` 内点「对照历史窗口」展开 `ExternalThemeComparisonPanel`
  （`src/components/ExternalSeasonalRadar/ExternalThemeComparisonPanel.tsx`）。
- **关联方式唯一**：`mapping.status === 'MAPPED'` 时，用 `mapping.macro_theme` 与
  **宏观粒度**主题行的 `theme` 做**精确字符串相等**匹配。★ 不做模糊 / 语义 / 同义词匹配。
  ★ 对照行由 App 以 `themeAnnualRowsOf(dataSource, 'macro')` 单独传入 —— **不随首页粒度切换变化**。
- **两层时间轴**：① 外部资料声称的月份窗口（琥珀 · 月份精度 · 外部参考）；
  ② 该宏观主题历史 `MAIN_RISE` 窗口（青蓝 · 来自 Research 投影）。
  历史侧逐条显示：标题 / ID / `Campaign` 或 `Research Candidate` / 年份 / **原始起止**。
- 显式声明：**宏观主题映射 ≠ 事件机制相同；并排对照不是统计验证。**
  不计算重合率 / 命中率 / 规律成立率，不生成分数 / 排名 / 预测。

**实测（真实数据）**：

| 线索 | 映射主题 | 历史窗口 | 关键事实 |
|---|---|---|---|
| EXT-12 流感 / 医药（9–1 月） | 医药健康 | 4 段（3 Campaign + 2 RC） | 流感疫苗对象 `C-2023-PHARMA-FLU` 的 MAIN_RISE 在 **2023-02-20 → 2023-03-20**，与外部 9–1 月**明显不同** —— 页面并排呈现差异 |
| EXT-14 迎峰度夏电力（5–7 月） | 电力（运营端） | 2 段 | `C-2023-POWEROP-THERMAL` 2023-01-03→05-29、`C-2021-POWER-GREEN` 2021-09-07→09-28，用户可自行比对 |
| EXT-23（无固定窗口） | 高端装备 | 6 段 | 外部层明示「无固定月份窗口 → 不绘制外部月份条」，历史层正常显示 |
| EXT-17 防汛 / 水利 | **未映射** | 无 | 明示未映射、不给历史关联；改走「带入研究请求」 |

#### ② 主交付 B：未映射线索 → 现有研究请求草稿

- 数据层 `src/data/timeline/externalLeadDraft.ts`：`draftFromExternalLead` / `makeDraftSeed`
  · `EXTERNAL_LEAD_DRAFT_NOTE` · `draftReplaceConfirmText`
- `DirectionLookupSection` 新增 `seed` prop：**空草稿直接带入；非空草稿先出确认横幅**，
  只有点「替换现有草稿」才写入；「保留现有草稿」不动原内容。
  → 复用的是**同一份**草稿 / 同一个 localStorage 键 / 同一套导出，不新建第二套表单。
- 带入内容：研究方向 = 线索名；已知线索 = 原始窗口文本（月份精度）/ 类别 / 来源名 /
  `evidence_refs` / 「外部参考、未经 ThreeC 验证」；研究问题建议 = 可核实句式。
  ★ `linkedQuery` / `linkedCoverage` 全空（种子不是一次覆盖查询，不伪造证据）。

#### ③ 体验与修复（C 节）

1. 时间轴接入 `today` → 标出**当前月份**（表头加深 + 「今」标记），并明写「仅日历事实，无涨跌含义」。
2. 25 条外部线索在**时间轴上默认全部可见**（23 行 + 2 条无窗口）—— 全覆盖由时间轴保证。
3. 详细卡片改回**按需展开**（时间轴已给概览，卡片不再重复铺开）；来源 / 线索正文 / 交互全部保留。
4. 修 `MapLink`：未提供 `onOpenMap` 时**不渲染按钮**，只给事实文本（不给「看起来能点但点了没反应」的东西）。
5. 跨年拆分 / 月份精度 / 外部参考标记维持不变。

#### ③-bis ★★ 三个真实用户场景（页面级 jsdom：挂载真实 `<App />` + 真实点击）

| 场景 | 用户路径 | 实测结果 |
|---|---|---|
| 1 流感 / 医药 | EXT-12「对照历史窗口」→ 两层时间轴 → 跳历史题材地图 | ✅ 外部层 9–1 月；历史层 `C-2023-PHARMA-FLU` **MAIN_RISE 2023-02-20 → 2023-03-20**（与外部窗口**明显不同**，页面并排呈现）；跳转后 FLU 题材选中、`FLU-2017-AVIAN` 事件卡、标的索引、经验概率全部在场 |
| 2 迎峰度夏电力 | EXT-14「对照历史窗口」→ 电力事件地图 | ✅ `C-2023-POWEROP-THERMAL` 2023-01-03→05-29 与 `C-2021-POWER-GREEN` 2021-09-07→09-28 逐条显示（含 ID / 类型 / 年份 / 原始起止）；两层来源标签不同；跳转后 POWER-2022-SUMMER 事件在场 |
| 3 防汛 / 水利 | EXT-17（未映射）→ 带入研究请求 | ✅ 未映射行**没有**「对照历史窗口」；草稿方向 = 防汛 / 水利、已知线索含「6–7 月 + 来源名 + 未经 ThreeC 验证」、无日级日期；预置非空草稿后再带入 → **先出确认横幅**，「保留现有草稿」不动、「替换现有草稿」才写入 |
| 附加 EXT-23 | 无固定窗口但有映射 | ✅ 历史主题窗口正常显示；外部层明示「无固定月份窗口 → 不绘制外部月份条（不虚构）」 |

★ 环境限制（如实说明）：本机无 Chrome/Chromium，`playwright-core` 因沙箱拦截 node_modules rename 装不上
→ 未做 Chromium 截图级验证；改为**页面级真实点击**（挂载 `<App />`，断言基于点击后真实状态，非静态字符串扫描）。

#### ④ 验证（全部实测）

```
npx tsc -b OK · npm run build 成功 · npm test **1312 passed / 0 failed / 61 files**（+30）
新增：externalThemeComparison 12 · externalLeadDraft 7
      ExternalSeasonTimeline.interaction 4（jsdom 真点：两层对照 / 无窗口线索 / 带入回调 / 当前月）
      externalLeadSeed.interaction 3（jsdom 真点：空草稿带入 / 非空确认 / 保留与替换）
      v013UserFlows 6（**挂载真实 <App /> 页面级**走完用户指定场景）
      重写 2 条既有断言（卡片默认展开 → 时间轴全覆盖 + 卡片按需展开；按钮回调缺失）
```

### v0.14 批次（完整用户工作流 + 历史窗口详情跳转）

> ★ 只做产品打通与可核对性：未新增题材 / 历史对象、未改 `schema.sql` / canonical export /
> 冻结 SA / CANONICAL 快照、未训练模型、无网络无 LLM。

#### ① ★★ A：历史窗口对照的数量语义修正（真实错误）

**问题（实测复现）**：对照 note 把 `row.campaignCount` / `row.candidateCount`（**整个宏观主题**的对象数）
当成「历史窗口涉及的对象数」。实测 EXT-05 国防军工：窗口只有 2 段、实际涉及 **1 Campaign + 1 RC**，
但旧文案写成「2 Campaign + 5 Research Candidate」—— 5 个 RC 里只有 1 个有 `MAIN_RISE`，另外
4 个 RC + 1 个 Campaign 根本没有 MAIN_RISE 记录，却被算进窗口。

**修法**（`externalThemeComparison.ts`，纯函数）：
- 新增 `windowCounts`：按 `objectId` **去重**统计投影实际涉及的 Campaign / RC 数；
- 新增 `objectsOutsideWindows`：主题下未进入窗口的对象**逐条列出 + 原因**
  （`no-main-rise` / `main-rise-not-projected` 异常路径）；
- `counts`（全主题对象数）**仍然保留**，与 `windowCounts` 分开呈现；
- note 改为可核对表述：「N 段历史 MAIN_RISE 窗口（投影段数；实际涉及 X Campaign + Y RC，按对象去重）。
  另有 Z 个对象因没有 MAIN_RISE 记录未进入窗口（该主题共 M 个对象）」；
- UI（`ExternalThemeComparisonPanel`）加 `data-ecp-counts` 计数块：段数 / 去重对象数 /
  「同一对象跨年可有多段投影，段数不是对象数」/ 未进入对象可展开（`<details>`）。

实测（真实数据）：军工 2 段 → 1C+1RC（5 个未进入）；医药健康 4 段 → 3C+1RC（`RC-2021-TCM` 未进入）；
消费 14 段 → 11C+2RC；电子 11 段 → 7C+4RC；房地产 2 段 → 1C+1RC（3 个未进入）；高端装备 6 段 → 4C+2RC；
文化传媒 4 段 → 3C+0RC；电力 2 段 → 2C+0RC。

#### ② ★★ B：历史窗口 → 对象详情（复用既有流程，零新弹窗）

- `ExternalThemeComparisonPanel` 历史对象列表每条加「**查看对象详情**」按钮；
- 接线：面板 → `ExternalSeasonTimeline` → `ExternalSeasonalRadar` → **App**：
  `openHistoricalObject(id)` = 既有的 `setSelection({kind:'campaign', id})` → 同一个 `CampaignDetail`；
  Campaign 与 Research Candidate 都走这里，**身份保持原样**（详情头部「历史行情 ·」vs「研究候选 ·」）。
- ★ B.4「返回不丢上下文」：关详情只清 `selection`，不碰时间轴 `openCompareId` / `mapTheme` /
  `draftSeed` → 对照面板仍展开、线索仍选中（场景测试实点断言）。
- ★ B.5「不能放无效按钮」：两道检查缺一不可 —— ① 页面注入了 `onOpenObject`；
  ② `canOpenObject(id)` 为真（App 用 `campaignById` / `researchCampaignsById` 判定）。
  否则渲染事实文本（「无法通过现有详情流程解析」/「本页未接线对象详情」），**不给假按钮**。
- ★ 顺手补 `data-campaign-id` / `data-object-kind` 锚点到详情面板
  （此前标题只显示 `season_id`，「从哪个对象进来」无法在页面上核对 —— B.3 要求「至少能看到对象身份」）。

#### ③ ★★ C：两层时间轴统一月份坐标

**问题**：`MonthScale` 刻度在 `(m-1)/12`，外部条在 `(月份-1)/12`，历史条在 `frac×100%`。
`frac` 是**年内日期比例**，与「等月格」是同一把 0..1 尺上的两种解释（50% 既是「7 月初」也是「年中第 182 天」）。

**修法**（`externalSeasonalTimeline.ts` 新增唯一换算处）：
- `fracToMonthFraction(frac)` = `frac × 12`；`monthToMonthFraction(m)` = `m-1`；
  `monthFractionToPct(mf)` = `mf/12 × 100%`；
- 两层全部改为在月份坐标 `mf ∈ [0,12]` 上定位：刻度 tick、外部条、历史条同一把尺；
- ★ 不重算 Research 原始起止、不把外部月份解释成日级 —— 换算只用于对齐坐标；
- 闰年 / 单日窗口（最小可视宽度 0.8/12 月）/ 跨年拆分段 / 长周期 onset 均按各自身份呈现。

#### ④ ★★ D：四个真实用户场景（页面级 jsdom：挂载真实 `<App />`）

| 场景 | 路径 | 实测结果 |
|---|---|---|
| 1 汽车 | 首页地图点「汽车」行 → 附页（8 Campaign / 1 RC）→ 第一个对象进详情 → 关闭回附页 → 「查一个方向」查「汽车」→ 历史案例进详情 | ✅ 附页计数如实；详情含生命周期；「这是查找，不是结构对应」在场；两侧判定与渲染一致 |
| 2 医药健康 | 查「医药」→ 历史案例进详情（生命周期 / 研究问题）→ 关详情 → 流感题材地图 | ✅ 历史侧命中；FLU tab 选中后「历史参与标的索引」+ `FLU-2017-AVIAN` 事件卡 + `data-empirical-probability` + `data-cross-year` 全部仍在 |
| 3 文化传媒 | 查「文化传媒」→ 历史侧展示、当前侧不谎报 → 历史案例进详情 → 草稿编辑 → 导出 | ✅ verdict 与块存在一致（无当前块时不说「两侧都有」）；`研究方向` 输入可编辑；无 clipboard → 「复制失败 + 手动选中复制」，**不出现「已复制」** |
| 4 外部线索 | EXT-12 对照 → 查看对象详情 → 关闭 → EXT-17 带入研究请求 | ✅ 详情 = 该行 `data-ecp-hist` 对象；关闭后对照面板仍展开、上下文不丢；EXT-17 草稿方向含「防汛」+「6–7 月」原文 + 「外部参考」 |

★ 环境限制（如实说明）：本机无 Chrome/Chromium，`playwright-core` 因沙箱拦截 node_modules
rename 装不上 → **未做浏览器截图 / 窄屏视觉核验**；上述为页面级真实点击（断言基于点击后真实状态）。

#### ⑤ 验证（全部实测）

```
npx tsc -b OK · npm run build 成功 · npm test 1328 passed / 0 failed / 62 files
新增：externalThemeComparison +5（计数语义）· 时间轴交互 +5（计数块 / 跳转 / 假按钮 / 坐标）
      v014UserFlows 6（四个场景）
既有断言重写 0 条（v0.13 场景测试全部保持通过）
### v0.15 批次（汽车智能化题材纵切片 + v0.14 残余修复 + 计数口径澄清）

> ★ 新增数据走**现有认可机制**：`research/current/` 新增版本化文件（不覆盖任何旧轮次），
> 沿用事件 JSON 契约（TS 类型 + `validateHistoricalEvents`）与索引 `maps[]` 登记；
> 未改 `schema.sql` / canonical export / 冻结 SA / CANONICAL 快照、无网络无 LLM、未训练模型。

#### ① ★★ 主交付：第 5 个历史题材「汽车智能化 / 智能驾驶」纵切片

**方向选择依据（证据盘点实测）**：汽车方向有 10 个库内对象（8 Campaign + 2 RC）、
export securities 注册表直接登记 22 条「对象→标的」关系、行情库 26 只全入库；
半导体/算力方向有 RC-2024-SEMI-FUND3 行情链断裂（4 只登记标的全不覆盖窗口）且叙事横跨
电子+信息通信两个 macro 主题 → **选汽车智能化**。

- 新数据文件 `research/current/auto_intelligence_historical_events_v0_1.json`（新文件，
  旧文件逐字节未动）：**6 个事件 / 22 条参与记录（19 只标的去重）/ 21 个可算行情组合**。
- 事件 → 库内对象：C-2019-AD · C-2023-AD · RC-2023-HUAWEI（RC，**不伪装 Campaign**）·
  C-2024-V2X（无 MAIN_RISE → 用 Campaign 起止，口径已标注）· C-2024-ROBOTAXI（CONFLICT
  状态如实标注）· C-2025-ROBOTAXI（3 日窗口 + β 主导如实标注）。
- ★ **题材边界**：新能源消费 / 购置税叙事（C-2020/21/22-NEV/POLICY）与智能化**不同轴，不纳入**；
  RC-2024-SECONDARY（弱次级，c2 封存记录「强度不足，不升级」）不建事件 —— 均写进 known_gaps。
- ★ **关系性质四类齐全**：直接机制（德赛西威域控 / 浙江世宝转向 / 万安线控 / V2X 终端三只 /
  赛力斯问界整车）· 产业链（江淮代工 / 华阳 HUD / 亚太制动 / 金龙客车等）· **运营侧反例**
  （大众交通 = 出租牌照方，category=INSUFFICIENT，说明「与技术链不同轴」）· 证据不足（众泰）。
- ★ **行情全部由 market_data.db 实算**（窗口内首末/高低/区间/至高点/回撤/相对 SH000300 超额），
  `by_security` 与 `participants` 同源同值；**赛力斯 series 止于 2021-12-31 → 不覆盖 2023 华为
  窗口 → 如实 `insufficient_data_in_window`（不补造）**。
- ★ **时间与证据区分**：每事件带四概念声明（事件窗口 / Campaign peak_date / 催化剂日期 /
  个股行情高点不得强行对齐）；催化剂全部引自库内 drivers（含 EV-/S-/E- 引用编号）+
  c2 封存记录（T3，research-level）。
- 注册：`historicalEventMaps.ts` DOCS 静态登记 + 索引 `maps[]` 追加（纯增量 diff）；
  `external_entry_ids=[]` + **显式 `external_link_status: NO_EXTERNAL_COUNTERPART`**
  （校验器允许显式声明无外部对应；未声明而留空仍报问题）。

**产品路径（全部实测可用）**：首页「历史题材地图」→ 选「汽车智能化」→ 标的索引（19 只，
可搜索/展开逐次证据）→ 事件卡展开（窗口 / 对象身份 / 催化 / 标的 / 行情）→
**「查看对象详情」→ 既有 CampaignDetail（复用 selection 流程，RC 保持 Research Candidate 身份）→
关闭回到原题材与展开中的事件（上下文不丢）**。事件卡 / 对照面板两处的详情跳转都执行
「两道检查」：注入了回调 **且** 对象可解析，缺一不给按钮。

#### ② ★★ v0.14 残余修复

| # | 问题 | 修法 |
|---|---|---|
| 1 | 未进入窗口对象的汇总说明把两种原因混在一句 | `outsideByReason` 分开计数（`no-main-rise` / `main-rise-not-projected`）；note 与 UI 同源，逐条原因与汇总严格一致 |
| 2 | 详情按钮条件可被短路 | 收紧为 `onOpenObject` 与 `canOpenObject` **都有效**才渲染；缺任一给事实说明（「本页未接线」/「无法解析」） |
| 3 | 历史窗口用 `frac×12` 近似定位（50% 既读成 7 月初又读成年中第 182 天） | `projectMainRise` 输出每段**裁剪后真实日期**（`segStart`/`segEnd`）；新增 `dateToMonthFraction`（按真实公历：月初落刻度 / 月末落前一格 / 闰年 2 月 29 合法）；外部月份仍走整数月边界，**不伪装成日级** |
| 4 | 文档计数口径混用 | 见下表（三层分列，均实测） |

**三层对象计数口径（不得混用）**：

| 层 | Campaign | Research Candidate | securities | 备注 |
|---|---|---|---|---|
| DB（cycle_research.db） | **62**（campaigns 表） | **不落表**（RC 不进 campaigns） | 210（campaign_securities 220 行） | events 表 136 |
| canonical export（timeline_export_v1.json） | **62** | **27** | **284**（含 RC 登记标的） | events 136 |
| Product 实际消费（researchTimelineSource） | 去重 **89**（62+27） | — | 事件地图 5 题材合计 **54 只**标的（20+6+4+5+19） | ★ 年份切片 **157** ≠ 对象数（跨年对象按年切） |

#### ③ 验证（全部实测）

```
npx tsc -b OK · npm run build 成功 · npm test 1349 passed / 0 failed / 64 files
新增：autoIntelligenceEvents 9（注册表核对 / 枚举 / 反例 / 索引合并 / 超额自洽 / 赛力斯留空）
      v015UserFlows 3（页面级端到端：题材→事件→反例标的→证据→对象详情→关闭回上下文；
      RC 不伪装；标的索引搜索）
      HistoricalEventMap +2（NO_EXTERNAL_COUNTERPART 显式声明 / 未声明仍报问题）
      ExternalSeasonTimeline +6（dateToMonthFraction 公历性质）· 交互测试改写 3 条
硬编码断言更新 3 条（题材清单 4→5 · 事件总数 13→19 · DESAYSV 出现次数）
```

### v0.16 批次（半导体 / AI 算力 / 存储题材纵切片 + 反例语义分离）

> ★ 新增数据走**现有认可机制**：`research/current/` 新增**版本化文件**（不覆盖任何旧轮次），
> 沿用事件 JSON 契约（TS 类型 + `validateHistoricalEvents`）与索引 `maps[]` 登记；
> 未改 `schema.sql` / canonical export / 冻结 SA / CANONICAL 快照、无网络无 LLM、未训练模型。

#### ① ★★ 主交付：第 6 个历史题材「半导体 / AI 算力 / 存储」纵切片

- 新数据文件 `research/current/semiconductor_ai_compute_historical_events_v0_1.json`（新文件，
  旧文件逐字节未动）：**7 个事件 / 29 条参与记录 / 16 只去重标的 / 21 个可算行情组合**。
- 事件 → 库内对象：`C-2019-SEMI-LOCALIZATION` · `RC-2022-SEMI-CHIPSHORTAGE`（RC，**不伪装 Campaign**）·
  `C-2020-SEMI-EQUIPMENT` · `C-2022-SEMI-DOWNTURN` · `C-2023-AI-COMPUTE-SEMI` ·
  `RC-2024-SEMI-FUND3`（RC，官方 `status=INSUFFICIENT`）· `C-2024-SEMI-MEMORY`。
- ★ **关系性质五类齐全**：直接机制 · 产业链扩散（长电科技封测 / 中芯国际代工）· 历史市场参与（寒武纪）·
  **反例**（京东方A = 显示面板与集成电路不同轴）· 证据不足（中芯@2019 / 拓荆 / 通富）。
- ★ **行情全部由 `market_data.db` 实算**（窗口内首末/高低/区间/至高点/回撤/相对 `SH000300` 超额），
  `by_security` 与 `participants` 同源同值。★ **大基金三期窗口（2024-09-24 → 2024-11-29）的全部 4 只
  登记标的**（中芯国际 / 中微公司 / 拓荆科技 / 海光信息）**库内 series 均不覆盖该窗口 →
  逐条 `insufficient_data_in_window`（不补数）**；拓荆科技无登记 series、海光信息 series 止于
  2022-10-12 → 同此处理。事件级行情状态 = `NO_PRICE_DATA`（诚实空洞，索引校验允许）。
- 注册：`historicalEventMaps.ts` DOCS 静态登记 + 索引 `maps[]` 追加（纯增量 diff）；
  `external_entry_ids=[]` + **显式 `external_link_status: NO_EXTERNAL_COUNTERPART`**。

#### ② ★★ 反例（`COUNTER_EXAMPLE`）与证据不足（`INSUFFICIENT`）语义分离

| # | 问题 | 修法 |
|---|---|---|
| 1 | 大众交通是**运营侧反例**却被放进 `INSUFFICIENT`，通用 UI 显示为「证据不足 / 反面参照」—— 与「尚不足以判断」混同 | 新增独立类别 `COUNTER_EXAMPLE` + 文案「反例（不同轴）」；`INSUFFICIENT` 文案改为「证据不足」（去掉「/ 反面参照」）；新增 `NON_THEME_CATEGORIES` + `isThemeParticipant()` |
| 2 | 通用组件与标的索引仍把两者同等处理 | `eventHasAnalysableData` / `eventStudyState` / 标的索引 `CATEGORY_ORDER` 全部改读 `isThemeParticipant`；`styles.css` 增 `.cat-counter_example`；`fluHistoricalEvents.ts` 同构同步 |
| 3 | 汽车题材把大众交通当 `INSUFFICIENT` | 大众交通改判 `COUNTER_EXAMPLE`（**保留**「运营牌照方、与智驾技术链不同轴」原解释）；众泰汽车保留 `INSUFFICIENT` → **两类别在同一题材并存可测** |

#### ③ 验证（全部实测）

```
npx tsc -b OK · npm run build 成功 · npm test 1361 passed / 0 failed / 66 files
新增：semiconductorEvents 9（注册表核对 / 枚举 / 反例≠证据不足 / 索引合并 / 超额自洽 / 大基金三期全留空）
      v016UserFlows 3（页面级端到端：题材→事件行情→对象详情→关闭；反例与证据不足同卡并存；RC 不伪装 + 留空）
硬编码断言更新 3 条（题材清单 5→6 · 事件总数 19→26 · 事件级行情「诚实空洞」允许项）
```

★ 环境限制（如实说明）：本机无 Node/Chrome —— `tsc` / `vite build` / `vitest` 由**便携 Node v22.23.3**
跑通，**未做浏览器截图 / 窄屏视觉核验**；上述为页面级真实点击（断言基于点击后真实状态）。

### v0.17 批次（历史行情可信展示 + 标的与 Research 对象对账）

> ★ 只读派生：不改任何版本化题材 JSON、不改 `schema.sql` / canonical export / 冻结 SA / CANONICAL 快照；
> 无网络、无 LLM 运行时、未训练模型。**六题材通用**（复用同一套 `marketDataCoverage` / 组件 / 索引）。
>
> 依据（原任务书）：当前 `MarketPerformanceBlock` 直接展示 `by_security` 数值，**未在行情表内**呈现
> 每只标的的关系类别与覆盖判定 → 局部收益与完整窗口结果**看起来等价**；且反例/覆盖不足**无从区分**。

#### ① ★★ 行情表可信展示（`MarketPerformanceBlock`）

| # | 问题 | 修法 |
|---|---|---|
| 1 | 行情表只显示 `security_id` | 显示**名称 + 代码**，新增「**关系类别**」「**窗口状态**」两列（复用 `PARTICIPANT_CATEGORY_LABEL` / `MARKET_DATA_STATUS_LABEL`） |
| 2 | 局部收益与完整窗口结果视觉等价 | **只有 `COMPUTED`** 行标「完整窗口已计算」；其余行标「覆盖不足 / 该窗口未计算 / 行情不可得」+「**实际可用 首末日期**」+「**仅局部数据，不可视为完整窗口可比结果**」 |
| 3 | 覆盖不足行混在完整行之间 | 按状态**下沉分组**（`COMPUTED` 优先），非完整行加 `fem-perf-partial` 弱化样式 |
| 4 | 反例与证据不足暗示不同 | 反例行单独标「**反例（不同轴）**」并加 `fem-perf-counter`；**数据保留可见、不删除** |

#### ② ★★ 标的 × Research 对象对账（新增 `src/data/timeline/objectReconciliation.ts`）

- 只读派生自 canonical export：对象 → `security_ids`（Campaign 与 Research Candidate 同表，`kind` 区分身份）、
  全局证券注册表。
- 按 `campaign_facts.object_id`（兼容旧 `campaign_id`）**精确对账**，**不**按名称模糊匹配、**不**推断身份、**不**改 Research 数据。
- 三分类（封闭集合）：**对象已登记关联**（在对象 `security_ids` 中）· **地图补充记录**
  （全局注册表在册、但不在对象 `security_ids` 中 → Product 补充关联，**不自动**视为错误）· **无法核对**
  （缺关联对象或注册信息 → 逐条列原因）。
- 呈现：事件详情（`EventCardBody` 汇总 + `ParticipantRow` 徽标）· 标的索引逐次记录（`OccurrenceRow` + 头部汇总）。

**★ 六题材对账实测汇总（123 条参与记录）**：

| 题材 | 事件 | 参与记录 | 已登记关联 | 地图补充 | 无法核对 |
|---|---|---|---|---|---|
| 流感 FLU | 6 | 42 | 0 | 0 | **42**（事件未记录关联对象） |
| 电力 POWER_SUMMER | 4 | 21 | 3 | 0 | **18**（事件未记录关联对象） |
| 文化传媒 MEDIA | 2 | 4 | 4 | 0 | 0 |
| 机器人 ROBOTICS | 1 | 5 | 5 | 0 | 0 |
| 汽车智能化 AUTO_INTELLIGENCE | 6 | 22 | 22 | 0 | 0 |
| 半导体/AI 算力 SEMICONDUCTOR_AI | 7 | 29 | 29 | 0 | 0 |
| **合计** | **26** | **123** | **63** | **0** | **60** |

> ★ **无法核对 60 条的真实原因**：流感 / 电力为**早期题材文档**，事件**未填 `campaign_facts`**
> （无 `object_id`）→ 无法与 Research 对象核对；**不是**「证券不存在」，也**不猜**其归属。
> ★ 地图补充记录当前为 **0**（现有题材 JSON 的 `security_id` 均取自对象 `security_ids`）。

#### ③ 验证（全部实测）

```
npx tsc -b OK · npm run build 成功 · npm test 1383 passed / 0 failed / 68 files
新增：objectReconciliation 13（三分类可区分 / 全局锚点 63·0·60 / 六题材汇总）
      HistoricalEventMap F2 6（行情表类别+窗口状态 / 局部数据声明+首末 / 反例样式 / 对账徽标）
      v017UserFlows 3（页面级端到端：行情→对象详情→关闭；覆盖不足如实；索引对账）
更新：行情表列位断言（8 列→10 列，超额列移至 [8]/[9]）
```

★ 环境限制（如实说明）：本机无 Node/Chrome —— 由**便携 Node v22.23.3** 跑通，**未做浏览器截图 / 窄屏视觉核验**。

### ★★ v0.5 后仍**未解决**（不得当成已完成）

1. ★ **SAR 冻结产物漂移（A 工作流定性：影响 = 0，不重生成）** ——
   `structural_analogy_feasibility_v0_2.json`（+2 个伴生产物）与 `historical_coverage_matrix_v0_1.json`
   与当前 DB 漂移（重算比较数如 74→317）。**实测证据**：原版脚本 + 拆分前原库**同样 FAIL/同样差异**
   → 早于本轮；**消费者矩阵**：产品 / CI / 快照投影器**均不读**；按冻结规则**不得原地重生成**。
   → 已把 `--check` 改成诚实诊断（见上表 #10），漂移本身留给后续 Research 轮次审批处理。
2. R02-05 的 4 条 DEFER 未处置（`COMM-002` · `POWEREQ-001/002` · `POWEROP-002`）。
   ★ 2026-10-16（v0.6）**删除**了此前写在这里的「`MS-2026-10-13-01` 未签发、产品 CANONICAL
   仍是 `MS-2026-10-12-01`」—— 实测 `research/current/market_snapshots/index.json`：
   **10-13 是唯一 `CANONICAL`**（10-12 及更早全部 `ARCHIVED`），该说法**早已不成立**。
   第一手证据：索引里 `CANONICAL` 计数 = 1；10-13 快照 `candidates_source`
   `artifact_version=0.13` / `rule_set_version=structural-analogy-ruleset-v0.3`
   与 SA `v0_13` 顶层字段**逐一相等**。
3. 三项存量异常均**不修正**（已论证非数据错误）：11 只负前复权价（qfq 口径特性）·
   `SH000300` 2015-03-27 OHLC 违律（源缺陷，不在任何窗口）· `YILING-002603` 重复序列
   （★ 本轮的 id 统一已让**事件地图层面**不再双计，DB 层的重复序列仍在）。
4. `raw/**/*.json` 6.5 MB 仍入库并按序列增长；旧提交里已入库的大 DB blob **仍在历史中**
   （禁改写历史）→ 历史体积不变，**未来不再增长**。
5. 智飞生物（ZHIFEI）库内止于 2022-12-30 → 2022/23 之后各季跨年比较实际为 8 只（已如实标注）。

## ★★ 当前状态（2026-10-16 上午 · 行情库拆分）—— 已被上一节取代，保留为历史

> ★ **本节 2026-10-13 重写** —— 上一版停在 2026-10-12（57 Campaign / SA v0.11 / 874 测试），
> 未反映其后的 **R02-04 / R02-05 入库**、**SA v0.13**、**Contract v1.2**、**Research CI 门禁**。
> 下方历史小节保留（仍是事实），但**不代表当前进度**。

### 实测基线（2026-10-13 · 全部实测）

| 项 | 值 |
|---|---|
| **git HEAD** | `ad3d854` · working tree **clean**（★ 接班仍须跑 `git log -1`，本文件不硬编码权威 SHA） |
| **历史宇宙** | **62 Campaign + 27 Research Candidate = 89 对象** · DB `themes` **59**（13 个根） |
| **测试** | **881 passed / 0 failed / 33 files** |
| **Export** | **Contract v1.2** —— `macro_theme_root` + **`taxonomy` 段**（59 行 · 13 根） |
| **SA** | `structural_analogy_explanations_v0_13.json` · **6 候选 × 89 = 534 对** · 规则集冻结未变 |
| **快照** | `MS-2026-10-13-01` = **CANONICAL**（已签发，回指 **v0_13**；supersedes `MS-2026-10-12-01`→ARCHIVED）· 批准记录 2026-10-14 |
| **CI** | Product（tsc / npm test / build）+ **Research 只读 5 项**（`validate_db` / `validate_timeline_export` / `validate_market_snapshot` / `intake --check` / `refresh_downstream --check`） |
| **DB 体积** | **59.5 MB**（≈ 全部来自 `market_daily` 338k 行；canonical < 1 MB）· 方案见 `docs/DB_GROWTH_PLAN_v0_1.md` |
| **历史事件地图** | 4 题材 / **13 事件**（流感 6 · 电力 4 · 传媒 2 · 机器人 1）· ★ 跨年份比较**已产品化**（流感 **11 季** 2015/16–2025/26 · 电力 **10 年** 5–7 月窗口）|
| **外部季节性日历** | `research/current/external_seasonal_calendar_v0_1.json` · **25 项** · 全部 `EXTERNAL_REFERENCE` |
| **版本** | 1.0 RELEASED（`v1.0.0` · `064d39c`）· 1.1 RELEASED（`v1.1.0`） |

### ★★ 两处**已知未解决**（不得当成已完成）

1. **`MS-2026-10-13-01` 未签发** —— 产品当前 CANONICAL 是 `MS-2026-10-12-01`（回指 **v0_12**），
   而产品消费 **SA v0_13**。`snapshotAdapter` 已修复为**同时校验 `artifact_version`**
   → 因此**默认视图的「候选明细」现在显示「未解析」**（诚实空态，拒绝跨版本合并）。
   **签发 `MS-2026-10-13-01` 后恢复**（签发 = 人工审核，属用户决定）。

   > ★★ **【2026-10-16 作废】本条已不成立**：`MS-2026-10-13-01` **已于 2026-10-14 签发**，
   > 是当前**唯一** `CANONICAL`（10-12 及更早全部 `ARCHIVED`）。
   > 原文保留仅为留痕；**以文件顶部「当前状态」一节为准**。
   > 实测依据：`research/current/market_snapshots/index.json`（CANONICAL 计数 = 1）+
   > 10-13 快照 `candidates_source` 与 SA `v0_13` 版本字段逐一相等。
2. **R02-05 的 4 条 DEFER 未处置** —— `COMM-002`（证据错配 D1）· `POWEREQ-001/002`
   （与 `C-2020-POWER-NE` 的阶段归属）· `POWEROP-002`（驱动复合）。
   粒度裁定（机制段）**只解除「粒度」阻塞**，不自动通过其余缺陷。
   ★ 结果：**电力设备仍 2 个、电力（运营端）仍 2 个**（< 3，季节性仍不可评估）。

### 当前阶段：**R02 波次收口中**

```
R01-01..06   ✅ 已入库（52 Campaign）
R02-01       ✅ 已入库（医药：GLP-1 / 创新药 BD）
R02-02       ⚠️ **从未入库**（无导入器 / 无 campaign / 无审查结论 —— 待确认是遗漏还是已否决）
R02-03       ✅ 已闭环（+4 Campaign → 57；Contract v1.1；SA v0.11；快照已签发）
R02-04       ⏸ **研究侧完成 + 已审查，但未写库**
              · 2 条由 DEFER → ACCEPT_WITH_CHANGES（语义数字 14/14 经一手来源复算命中）
              · 待办：写 `import_r02_04_canonical_v0_1.py` → 下游刷新 → 快照重出
```

### 本阶段的三个新增能力（1.1 RELEASED 之后建立）

1. **审查裁定生效通道** `research/research/reports/review_overrides_v0_1.json`
   —— 让 `ACCEPT_WITH_CHANGES` 的裁定真正落地，且**防漂移**（原值不匹配则拒绝应用）。
2. **下游刷新入口** `research/scripts/refresh_downstream.py --check / --apply`
   —— 前置自检 C0–C7（版本号 / 字段白名单 / 配色 / lifecycle 覆盖的**全局一致性**）。
   ★ 做它的理由：**下游每一层都硬编码上游版本**，且**不报错** —— 同类缺陷已踩 **5 次**。
3. **标的映射检查泛化** `check_intake_security_map_v0_2.py`
   —— v0_1 只扫 `R01-*`，R02 包的标的映射**从未被检查**。

### ★ 进度明细与分工

**以 `docs/TASK_ALLOCATION_2026-10-11.md` §「进度修订（2026-10-12）」为准**（A–F 逐项状态 + 新增 G/H/I）。

### 原「当前阶段」记录（2026-10-06 · 保留为历史）

| 项 | 值 |
|---|---|
| **Version** | **`1.1.0`** |
| **Tag** | **`v1.1.0`** |
| **Production** | **https://yangfanbit.github.io/Cycle/** |
| **1.0** | RELEASED（Tag `v1.0.0` · `064d39c` · Gate R/P/T/Q/U/M/D/G 全部 PASS · P0/P1 = 0/0） |
| **1.1** | **RELEASED** —— Phase 0 设计冻结 ✅ · 1.1 架构审查 ✅ · 1.2 运行时 ✅ · 1.3 Product 只读页面 ✅ · 1.4 观察接入 + Lifecycle Tracking ✅ |

- branch：`main` · ahead / behind：`0 / 0` · working tree：clean
- HEAD：**以 `git log -1` 实测为准**（本文件不硬编码当前 SHA）
  · 1.0 Release 提交链：`f8b6c82`（Gate M 收口）→ `064d39c`（**release: ThreeC 1.0.0**）
  · ★ **任何接班第一步必须跑 `git log -1`**；上文 SHA 仅为可读线索，不是权威值

### 1.1 已完成（2026-09-25 ~ 2026-09-26）

| 阶段 | 产出 | commit |
|---|---|---|
| **Phase 0 设计冻结** | 架构 / 契约 / 治理 / 冻结报告 共 4 份 | `738638d` |
| **Phase 1.1 架构审查** | `THREEC_REPOSITORY_ARCHITECTURE_REVIEW_v1.1.md`（发现 F-1~F-4） | `dc614bb` |
| **G-1 退役** | 旧「历史相似阶段」视图（`currentSimilarity` 自算 tier/stars）退出 UI，**不得恢复** | `dc614bb` |
| **G-2 / G-3** | `AGENTS.md` §5.1 消费白名单 · `research/current/market_snapshots/` 建立 | `dc614bb` |
| **F-3 处置** | 仓库根 `data/` 实测**无消费者**（非双源）；保留 + 标注（人工核验为后续计划） | `7688b00` |
| **Phase 1.2 运行时** | JSON Schema（draft-07）+ 校验器（V1–V10 / R1–R10）+ 生成器（CANONICAL 闸门） | `cd2dc2d` |
| **Phase 1.2b 投影器** | `project_sa_to_candidates`（带冻结规则版本守卫）· `project_cc_to_objects` | `9339b47` |
| **Phase 1.2c 首份快照** | `MS-2026-09-15-01`（DRAFT · 5 对象 · 395 候选） | `9339b47` |
| **契约 v0.2 回指** | `historical_candidates` 改轻量索引 + `candidates_source` 回指冻结 SA；**1.9 MB → 168 KB** | `a94774e` |
| **首页配色** | 12 个大主题分类配色（`src/components/SeasonalMap/themeColors.ts`，含不变量测试） | `b3a65fb` |
| **契约 v0.3 修复** | `historical_candidates` 新增必填 `current_object_id` —— **修 v0.2「候选无法指回当前对象」的可用性缺陷**；校验器加 V8c（悬空关联即 FAIL） | 见下 |
| **第二份快照** | `MS-2026-10-06-01`（延续快照，regime 全 UNKNOWN，已标注未执行新研究轮次） | 见下 |
| **1.2d 快照 diff** | `src/data/marketSnapshot/`（types + `diffSnapshots` 纯函数 + 15 条测试，含真实快照集成检查）；四层比较，**只说事实不说好坏** | 见下 |
| **1.2e 月度流程** | `docs/MONTHLY_RESEARCH_RUNBOOK.md`（checklist + 可直接复制的命令 + 质量门 + 踩过的坑） | 见下 |
| **1.3 Product 只读页面** | `src/components/CurrentSnapshot/` + `snapshotAdapter`（索引静态 / 快照按需 lazy）+ **CANONICAL 门禁**（`?snapshot=draft` 可预览未签发） | 见下 |
| **1.4 观察接入** | `observations/`（契约化输入）+ 校验 **O1–O7**；**首份真实 `market_regime`** | 见下 |
| **1.4 东财取数 + 证据等级** | `fetch_market_regime_v0_1.py`（EOD 序列，**非实时行情**）+ 规则 **§2.7 G1/G2/G3 降级机制** | 见下 |
| **1.4 真实数据修正** | 真实序列推翻媒体证据：`broad` FLAT→**DOWN**、`liquidity` CONTRACTING→**STABLE**；走 **revision 02** 取代 01 | 见下 |
| **1.4 Lifecycle Tracking** | `lifecycleTimeline.ts`（**派生式**、append-only、**PIT 安全**）+ 校验 **L1/L3** | 见下 |

> ★ **1.1 已完成，Product 首次具备「当前 → 历史」的完整可见链路**：
> 快照（真实 regime + 观察）→ diff（月度变化）→ 页面（只读 CANONICAL）。

### ★ 1.1 关键结论（后续轮次必须遵守）

1. **Product 数据入口 = 4 个**（已形式化进 `AGENTS.md` §5.1）：`@exports` · `@current` · `@observation` + 仓库根 `data/`（legacy，无消费者）。
2. **正式「当前 → 历史」入口唯一** = `StructuralAnalogySection`（冻结 SA v0.5）；旧 `currentSimilarity` 分档/星级**已退役，不得恢复**。
3. **Market Snapshot 契约 = `v0.2`**（回指模式）：`historical_candidates` 只存轻量索引，细节由 `candidates_source` 回指冻结 SA artifact；**读取方必须先校验 `rule_set_version` 一致，不一致即拒绝合并**。
4. **`market_regime` 无任何数据源** —— 首份快照四维全 `UNKNOWN`（诚实空态，**不编造**）。
5. **SA 产出率**：395 条解释中「有结构对应」= 45（11%），`NO_VALID_CORRESPONDENCE` = 225（57%）→ **不得靠放宽规则提高命中率**。
6. **月度节奏 ⇒「变化」比「状态」重要** —— 快照 diff 是 1.1 的最大设计缺口（详见 §7）。

### 1.0 Release 完成事实

- **Product version**：`package.json` = `1.0.0`（`package-lock.json` 同步）
- **Git tag**：`v1.0.0`（annotated）→ commit `064d39c` = HEAD = origin/main
- **部署**：GitHub Actions `build` + `deploy` 走 **Release commit**，environment `github-pages`
- **线上 provenance 实测**：Product version `1.0.0` · 构建 commit `064d39c` ·
  Research export 1.0 · source_commit `c56e70f` · 52 Campaign + 27 RC = 79 ·
  SA artifact 0.5（`structural-analogy-ruleset-v0.3`）· TO artifact 0.3 ·
  **无 `__THREEC_` / `process.env` / `undefined` / `NaN`**
- **线上 smoke test**：`/` · `?preview=1` · `?candidates=example` · `?foo=bar`
  → 全部 HTTP 200 / JS 200 / CSS 200 / 无 pageerror / 刷新正常 / **横向溢出 = 0**
- **语义红线复查（线上）**：UNKNOWN-only RC 显示「阶段未标注」（无具体阶段）·
  ENDED Campaign 显示 `ENDED`（非 UNKNOWN）· RC identity 未混淆 · SA 四维可读且无
  score / ranking / probability / prediction

### 冻结状态

- **Research Core：FROZEN**（Research Model v1.0 · `schema.sql` · Timeline Export Contract v1.0）
- **Historical Universe：79**（52 Campaign + 27 Research Candidate）
- **SA：FROZEN**（rule set v0.3）· **TO：FROZEN**（artifact 0.3）
- **Research expansion：DEFERRED**

---

- HEAD：**以 `git log -1` 实测为准**（本文件不硬编码当前 SHA）
  · 1.0 Release 提交链：`f8b6c82`（Gate M 收口）→ `064d39c`（**release: ThreeC 1.0.0**，tag `v1.0.0`）
  · ★ **任何接班第一步必须跑 `git log -1`**；上文 SHA 仅为可读线索，不是权威值
- **★ 当前阶段：ThreeC 1.1 — IN PROGRESS**（1.0 已 RELEASED 并冻结）
- **★ 线上入口：`https://yangfanbit.github.io/Cycle/`（HTTP 200 OK，GitHub Pages）**
- **★ Gate 状态**：**R / P / T / Q / U / M / D / G = 全部 PASS**
  · Gate M（真机 / 实际浏览器复核）已于 2026-09-24 完成（真实 Chromium 驱动，375 / 390 / 412 / 768）
  · Gate D 的 D4（`version = 1.0.0`）/ D5（`tag v1.0.0`）**已在 1.0 Release 轮执行**
- **★ P0 = 0 · P1 = 0**
- 最近完成：**ThreeC 1.1 Phase 1.2 —— Market Snapshot 运行时 + 首份真实快照 + 契约 v0.2**
  · 交付：JSON Schema（draft-07）· 校验器（V1–V10 / R1–R10）· 生成器（CANONICAL 闸门）· 两个投影器 · `MS-2026-09-15-01`
  · 契约 v0.2 回指：`historical_candidates` 改轻量索引 + `candidates_source` 回指冻结 SA → **1.9 MB → 168 KB**
  · 未修改 Research artifact / SA artifact / TO artifact / Export Contract / Research Model / schema 任何版本
- 上一完成：**ThreeC 1.0 Final Release —— v1.0.0 正式发布**
  · `package.json` `0.1.0` → `1.0.0`（`package-lock.json` 同步）· release commit `064d39c` · annotated tag `v1.0.0`
  · GitHub Actions 部署 Release commit（environment `github-pages`）· 线上 provenance 与 smoke test 全部实测通过

<details>
<summary>历史：1.0 发布前的 Deployment / Gate M 阶段记录（保留原貌，不篡改）</summary>

- 历史阶段：**ThreeC 1.0 Deployment / Release Engineering —— 已完成**（详见 `docs/DEPLOYMENT_RUNBOOK.md`）
  · **部署形态**：**GitHub Pages**（唯一平台；未使用 Vercel / Netlify / Docker / 云服务器 / CDN 产品化）
  · **自动构建**：`.github/workflows/deploy.yml` —— push `main` → `npm ci` → `tsc -b` → `npm test` → `npm run build`
    → 上传 `dist/` → `deploy-pages`（**不允许跳过 `npm test`**；**不允许上传未 build 的源码**；**不提交 `dist/`**）
    · CI **实测 PASS**：`build` PASS + `deploy` PASS（environment `github-pages`）
    · workflow 内**硬 Gate**「Verify base path is /Cycle/」：产物含 `/assets/` 绝对引用即 FAIL，不上线
  · **Vite `base`**：`resolveBase()` = `THREEC_BASE` 显式覆盖 > `GITHUB_ACTIONS === 'true'` → `/Cycle/` > 默认 `/`
    （**刻意不用 `command === 'serve'`**，使 `vite preview` 可复现生产行为；本地 `dev` / `preview` 不受影响）
  · **D7 provenance（非仅文档）**：`src/data/buildProvenance.ts` 在 Product 内展示 `package.json.version` ·
    git commit · `exports/timeline_export_v1.json` 的 `source_commit` · SA / TO artifact 版本
  · **D6 / D8**：`docs/DEPLOYMENT_RUNBOOK.md`（正常发布 / Product-only / Research artifact 更新 / 回滚 / smoke test）
  · **★ 该阶段排查并解决 2 个真实部署阻塞**：
    (1) `has_pages = false` —— 仓库从未启用 Pages，`deploy` job 必然失败 → 已启用（`build_type = workflow`）
    (2) **user-site 自定义域名级联 301** —— `yangfanbit.github.io`（user site）设了 `cname: yfnwu.com`，
        GitHub Pages 将其级联到 `Cycle`，导致入口 301 → `yfnwu.com`（Vercel 托管、无该路由）→ 404；
        **本项目 `cname` 本就是 `null`，无法自行修复** → 已获用户授权清空该 user-site 的 custom domain，
        入口立即恢复 200。**未改动任何 DNS。** 详见 runbook §8.1 / §8.2
  · Gate M 轮修复 3 处 P1 移动端横向溢出（详见 `docs/CHANGELOG.md` 2026-09-24 条目）
  · **未修改** `research/` · `exports/` · `contracts/` · `schema.sql` · SA rule · TO 标准；**未新增**产品功能；**未引入**后端 / runtime 网络 / LLM

</details>
- 最近完成：**ThreeC 1.0 P0 修复轮 —— Gate T8 / P0-1（含 P0-1b/c/d/e）**
  · **结果：Gate T 由 ★ FAIL → PASS；P0 清单清零**。纯 Product 语义修复，`research/` · `exports/` · `contracts/` · `schema.sql` 零改动
  · `historicalCase.ts` 改读 Research `c.lifecycle`（空则 `[]`）；`researchAttention.ts::terminalPhaseOf` 删除 `c.phases` 回退 → `UNKNOWN`
  · `STAGE_TO_PHASE` 补 `ENDED: 'END'`（P0-1c）· `ExportLifecycleStageV1.start/end` → `string | null`（P0-1d）·
    `CampaignDetail` 第二处 `m.phases` 渲染路径改读 Research `lifecycle`（P0-1e）
  · `derivePhases()` 与 `c.phases` **完整保留**（Timeline 视觉分段仍依赖）
  · 验证：`npm test` **654 passed / 0 failed（17 files）** · `tsc -b` **0 error** · `vite build` **PASS**
- 最近完成：**ThreeC 1.0 Release Definition + Release Gap Audit**（详见 `docs/THREEC_1_0_RELEASE_DEFINITION.md`）
  · 8 个硬 Gate（R / P / T / Q / U / M / D / G）+ Blocker 分级（P0 / P1 / P2）
  · **4 个仅 UNKNOWN lifecycle 的 RC 判定为 `KNOWN DATA LIMITATION`，不是 1.0 Blocker**
- **★ Research Core 基线（FROZEN）**：79 Historical Objects（52 Campaign + 27 RC）· Driver Canonicalization **v0.4** ·
  SA **v0.5**（395 pairs）· TO **v0.2**（内部 0.3）· Product **已消费最新 SA / TO artifact**
- **Known Limitations（不阻塞推进，详见 ROADMAP §3）**：
  L1 剩余 5 项子串冲突（不改变 driver 集合）· L2 `driver=MATCH` 仅 1 条 · L3 2 个 cycle 因映射逻辑无 driver ·
  L4 TO `year`/`date` 相差 1 年（5 例）· L5 4 个仅 UNKNOWN lifecycle 的 RC（`KNOWN DATA LIMITATION`，已不再是 Next Single Goal）

### 最近完成：**ThreeC 1.0 Deployment / Release Engineering**

> **结果：P1-1（无部署方式 / 无访问入口 / 无回滚定义）已闭环；线上入口实测可用；
> Gate D 的 D1–D3、D6–D8 落地并验证；本轮为纯 deployment engineering，
> `research/` · `exports/` · `contracts/` · `schema.sql` 零改动。**

- **新增文件**：`.github/workflows/deploy.yml` · `src/data/buildProvenance.ts` ·
  `src/data/__tests__/deployment.test.ts`（24 用例）· `docs/DEPLOYMENT_RUNBOOK.md`
- **修改文件**：`vite.config.ts`（`base` + `define`）· `src/App.tsx`（`<BuildProvenanceFooter />`）· `src/styles.css` ·
  `.gitattributes`（workflow 强制 LF）· `.gitignore`（忽略 `.tmp/`）·
  `README.md` · `docs/ROADMAP.md` · `docs/THREEC_1_0_RELEASE_DEFINITION.md` · `docs/PROJECT_STATE.md`（本文件）
- **验证**：`npm test` **678 passed / 0 failed（18 files）** · `tsc -b` **0 error** · `vite build` **PASS**
  · Actions `build` PASS + `deploy` PASS · 线上入口 200 OK
- **未做**：未设 `package.json.version = 1.0.0` · 未创建 `v1.0.0` tag · 未提交 `dist/` · 未引入后端 / SPA router / `.nojekyll`
  （Product 无 client-side router，只有 query param，故无需 404 回退）
- **★ 边界**：**「Deployment Engineering 完成」≠「ThreeC 1.0 正式发布」。**

### 上一完成：**ThreeC 1.0 P0 修复轮 —— Gate T8 / P0-1（含审计新发现 P0-1c / P0-1d）**

> **结果：Gate T 由 ★ FAIL → PASS；P0 清单清零（0 项）；**全 8 个 Gate 中 T/Q/U 已 PASS**。
> 本轮为**纯 Product 语义修复**，`research/` · `exports/` · `contracts/` · `schema.sql` **零改动**。

- **P0-1（原判 P0）**：`historicalCase.ts` 的 `lifecycle` 改为读 **Research `c.lifecycle`**（空则 `[]`），
  **不再回退** adapter 派生的 `c.phases`；`researchAttention.ts::terminalPhaseOf` **删除 `c.phases` 回退**
  → 无 Research lifecycle 时返回 `UNKNOWN`。**P0-1b** 伴生误导注释同步改写。
  · **实证**：4 个仅 UNKNOWN 的 RC（`RC-2019-RE-EASING` / `RC-2020-FIN-BROKER-VOLUME` /
    `RC-2016-RE-SHANTY` / `RC-2015-FIN-LEVERAGE`）修复前一律显示「主升 `main_rise`」/ `EXPANSION`，
    修复后 **`lifecycle = []` / `UNKNOWN`**；虚构计数 **4 → 0**（两个函数各自 4 → 0）。
  · **`derivePhases()` 与 `c.phases` 完整保留**（Timeline 视觉分段仍依赖；4 个 RC 的 `phases` 均在）。
- **P0-1c（★ 本轮审计新发现，同属 Gate T8 家族）**：`STAGE_TO_PHASE` **漏映射 `ENDED`**
  —— `ENDED` 是 Contract `VALID_LIFECYCLE_STAGE` 成员且在当前 export 中出现 **2 次**，
  漏映射使 `phaseOfStage('ENDED')` **静默退化为 `UNKNOWN`**（`UNKNOWN ≠ 未映射`：前者是研究未判定，
  后者是 Product 没接上 → **低估研究结论**）。受影响对象 `C-2019-MIL-GROUP-RESTRUCTURE` /
  `C-2020-RE-DEBT-RISK` 由 `UNKNOWN` **纠正为 `END`**。已补映射，并新增
  `CONTRACT_LIFECYCLE_STAGES`（11 项全量）与 F7/F8/F9 覆盖度不变量。
- **P0-1d（★ 本轮审计新发现）**：`ExportLifecycleStageV1.start/end` 类型曾写死为 `string`，
  但 Contract 明确 `start`/`end` **可为 null**（开放区间；`is_iso_date(None) == True`）
  → 5 个消费点存在 `null` 运行时风险（`terminalPhaseOf` 排序、`peakWindowOf`、`stageSegmentOf`、
  `historicalPhasesInWindow`、`CampaignDetail` 旧字段区）。**全部显式处理开放区间，不猜测端点。**
  `tsc -b` 由 **12 error → 0 error**。
- **P0-1e（本轮 UI 审计新发现）**：`CampaignDetail` 存在 **第二处独立 `m.phases` 渲染路径**
  （旧 `历史行情` 字段区），与 `historicalCaseOf` 无关但同样虚构「主升」→ 已改读 Research `lifecycle`，
  空则**整区不渲染**。
- **Gate U 正式化**：D3 由 `it.fails`（KNOWN GAP）**正式化为 `it(...)` 正常断言**；
  新增 **D3b**（UI「生命周期」字段区不得出现具体阶段名）与 **Scenario F1–F9**（Gate T8 全局不变量，
  含 **F3 反向非空断言** —— 证明修复不是靠「一律返回空」蒙过、**F5** 证明 `phases` 未被删除）。
- **验证链**：`npm test` **654 passed / 0 failed（17 files）**（643 → 654）· `tsc -b` **0 error** ·
  `vite build` **PASS** · `researchWorkflow.test.tsx` 5/5 Candidate 闭环仍全通 · 无 runtime crash。
- **本轮未做**：未改 `research/` / `exports/` / `contracts/` / `schema.sql` / SA v0.5 / Driver v0.4 / TO v0.2 /
  lifecycle 映射规则 / Historical Universe；未设 `1.0.0`、未打 tag、未部署、未引入托管。

## 1. 项目当前定位

**ThreeC = A股历史机会时间轴 / 历史机会地图。**

核心价值：

> 从历史周期里找结构，而不是从历史数据里找同名主题。

主链路：

`今天 → 历史同期 → 历史周期阶段 → 当前研究对象 → 历史结构对应 → 为什么对应 / 哪里不同 → 继续研究`

不是交易决策、预测、买卖信号、概率或推荐系统。

## 2. 当前总阶段

### Research Core：第一版闭环完成

`Historical Model → Historical Data → Time Observation → Current Research → Structural Analogy`

当前已完成：
- Structural Analogy Rule Set v0.2 冻结
- Structural Analogy Research v0.2 baseline
- Structural Analogy Explanation Artifact v0.2
- Product Similarity Architecture Gate v0.1 — PASS
- Product Adapter v0.1（Structural Analogy Artifact → Product View Model）
- Time Observation v0.5
- CMTR v1
- Historical Driver Canonicalization
- Robustness / Feasibility / Readiness

### Product Core：闭环已成立，并已具备可重复的研究更新循环

```
Current Time → Current Candidate → Structural Analogy → Historical Case
             → Historical Cycle Map → Current Research Refresh Loop
```

**已完成**：Product Similarity Architecture Gate v0.1（PASS）· Product Adapter v0.1 ·
Product UI Integration v0.1 · UX Review + Performance Gate v0.1（PASS）·
Historical Case Experience v0.1（PASS）· Historical Cycle Map v0.1（PASS）·
**Current Research Refresh Loop v0.1（PASS）**。

当前 Product 主线：

`Timeline → Current Time Lens → Lifecycle Lens → Calendar Lens`

Current Candidate 已进入 Current Time Lens。

Structural Analogy 已通过 Adapter 接入 Current Candidate / Current Time Lens。UI Integration v0.1 已完成。

## 3. Structural Analogy 当前基线

Research v0.2：
- 5 Current Candidates
- 17 Historical Cycles
- 85 comparison pairs
- STRICT_STRUCTURAL_SUPPORTED = 1
- STRUCTURAL_SUPPORTED = 4
- STRUCTURAL_PARTIAL = 36
- THEME_ONLY = 3
- INSUFFICIENT_EVIDENCE = 5
- NO_VALID_CORRESPONDENCE = 37

规则版本：

`structural-analogy-ruleset-v0.2`

最大瓶颈仍是机制级 Driver 证据深度，不是规则或 vocabulary。

## 4. Product-facing Artifact 与 Adapter

已新增：
- `docs/STRUCTURAL_ANALOGY_EXPLANATION_ARTIFACT_v0_1.md`
- `research/research/reports/structural_analogy_explanations_v0_1.json`
- `research/scripts/build_structural_analogy_explanation_v0_1.py`
- `research/research/reports/structural_analogy_explanations_v0_2.json`
- `research/scripts/build_structural_analogy_explanation_v0_2.py`
- `src/data/timeline/structuralAnalogy.ts`
- `src/data/timeline/__tests__/structuralAnalogy.test.ts`
- `src/components/CurrentTimeLens/StructuralAnalogySection.tsx`
- `src/components/CurrentTimeLens/__tests__/structuralAnalogySection.test.tsx`

Artifact 覆盖 85 explanations，且：
- 来源唯一 = Structural Analogy Research v0.2
- 规则唯一 = Rule Set v0.2
- Product READ_ONLY
- 无 score / ranking / probability
- `--check` 可逐字节复现

**v0.2 已通过 Architecture Gate；Adapter v0.1 已消费该契约。**
1. `why_not_similar` 不应把 CROSS_MACRO_THEME 当成“为什么不相似”。
2. explanations 当前按 structural status 再按 cycle id 排列；虽然不是研究 ranking，但 Product 很容易把数组顺序误读为排名，应去除这种暗示。
3. `historical_campaign_id` 同时承载 historical campaign 与 Research Candidate，需要在 Adapter 前明确 cycle / campaign identity。
4. provenance 需要明确哪些证据支撑哪个维度，避免 Product 误把候选全部证据理解为每个维度的直接依据。

因此：

> **Explanation Artifact v0.2 是当前 Product Adapter 的 Research-facing 输入；v0.1 只作为历史保留。**

## 5. 当前 Product Architecture Debt

### 三套比较体系

1. `currentSimilarity.ts`
   - Current Candidate × Historical
   - 内部 score / tier
   - 当前 UI 已使用

2. `historicalSimilarPhase.ts`
   - Historical × Historical
   - Lifecycle Lens
   - 内部 score / tier

3. Structural Analogy
   - Current Candidate × Historical Cycle
   - Lifecycle / Mechanism Driver / Evidence Sequence / Event Structure
   - 正式 Research Correspondence
   - 离散状态，不以 score 定义

长期目标：

- Calendar = 时间邻近浏览
- Lifecycle = 生命周期浏览
- Structural Analogy = 正式结构对应

不能长期维护三套“历史相似算法”。

### Driver 双层语义

Product Current Candidate：
- 证据类别：POLICY / INDUSTRY / CAPITAL / SENTIMENT / EXTERNAL

Structural Analogy：
- 驱动机制：POLICY_DRIVEN / INDUSTRY_UPGRADE / TECH_BREAKTHROUGH / …

以后必须明确区分“证据类别”与“驱动机制”。

### OpportunityRadar

`src/components/OpportunityRadar/` 当前不在 `App.tsx` 主流程。

状态：

**LEGACY / DEFER**

不在 Architecture Gate 前删除。

## 6. Time Observation

Time Observation v0.5 已完成并暂时冻结：

- raw candidates = 315
- distinct samples = 139
- independent robust structures = 1
- TOP-01 = N7 / center 06-11 / window 05-27~06-26 / recurrence 5/7
- cross-family robust = 0

不再为了增加 Pattern 数量继续扩容或放宽标准。

## 7. 当前唯一下一目标

# **ThreeC 1.1 — IN PROGRESS** 🚧

**1.0 已发布并冻结**：Version `1.0.0` · Release commit `064d39c` · annotated tag `v1.0.0`（本地 + origin）·
Production 线上 provenance = `1.0.0` / `064d39c` · Gate R/P/T/Q/U/M/D/G **全部 PASS** · P0 = 0 · P1 = 0。

**1.1 已完成**：Phase 0 设计冻结 → Phase 1.1 架构审查 → Phase 1.2 运行时（见本文件顶部「1.1 已完成」表）。

### ★ 当前唯一下一目标：**1.2d 快照 diff**

**理由**：用户已确认 —— **月度节奏下「变化」比「状态」重要**。
实测发现快照契约有 `supersedes` / `superseded_by`（**版本链存在**），但
**「变化」本身没有任何设计**（无 diff 概念）→ **这是 1.1 最大的设计缺口**。

| 步 | 内容 | 前置 |
|---|---|---|
| **1.2d** | **快照 diff**：四层比较（环境 `market_regime` / 对象 `research_objects` / 候选 `historical_candidates` / 观察 `observations`）；Product 侧纯函数，**只说「变了什么」，不说好坏或含义** | 需第二份快照作数据 |
| **1.2e** | **月度研究流程**：checklist + 半自动脚本（regime 填报 → 候选更新 → 快照装配 → 校验 → diff） | 需求由 1.2d 定义 |
| **1.3** | **Product 只读页面**：基于真实数据 + diff；把「无对应」做成一等公民（57% 是 `NO_VALID_CORRESPONDENCE`） | 1.2d |
| **1.4** | **2026 接入 / Lifecycle Tracking** | 1.3 |

**★ 已明确不做**：不扩 Historical Universe（瓶颈是机制级证据深度，不是覆盖量）· 不接实时行情 ·
不追 AI 自动化率（AI 只做 draft、人审核）· 不为「有东西可看」先做 UI。

---

<details>
<summary>历史背景：1.0 正式发布前的「待发布」记录（保留原貌，不篡改）</summary>

**（发布前状态，已过期）** Deployment / Release Engineering 已完成（线上入口实测 200 OK）；
后续唯一主线 = Gate M 真机复核 → `package.json → 1.0.0` → release commit →
`git tag v1.0.0` → 部署 → 验证入口 → 文档收口。**当时不设 `1.0.0`、不创建 `v1.0.0`。**

</details>

---

<details>
<summary>历史背景：R01 收口（已完成，保留存档）</summary>

**已完成（全部 PASS）**：… Product 侧全部轮次 · **R00**（Intake Protocol）· **T01**（taxonomy gap）·
**R01-01 / R01-02 / R01-03 / R01-04 / R01-05 / R01-06 Canonical Import** · **Intake Validator C25**（严格 Draft-07）。

### R01 进度

| task_id | scope | status |
|---|---|---|
| `R01-01` | 高端装备 / 机器人 | ✅ 已导入（+5 campaigns / 2 RC） |
| `R01-02` | 半导体 / 电子 | ✅ 已导入（+8 campaigns / 4 RC） |
| `R01-03` | 资源 / 有色 / 化工 | ✅ 已导入（+6 campaigns / 5 RC） |
| `R01-04` | 消费 | ✅ 已导入（+11 campaigns / 2 RC） |
| `R01-05` | 金融 / 地产 | ✅ 已导入（+7 campaigns / 5 RC） |
| `R01-06` | 军工 | ✅ 已导入（**+2 campaigns / 5 RC**） |

### ★ `governance-gates-v0.1` 已落地（第一批：SA / TO 前置 4 项）

| Gate | 结论 |
|---|---|
| **G1-1 市场侧证据** | **软门槛**（影响 `strength` / `date_confidence`），**非** Campaign 存废硬门槛；**不回溯**。三态：`A_SHARE_MARKET` **48** / `INDUSTRY_COMPANY_ONLY` **4** / `NONE` **0**。4 个仅行业公司证据：`C-2019-MIL-GROUP-RESTRUCTURE` · `C-2018-HIEQ-ROBOT-DOWN` · `C-2016-PANEL-CYCLE`（面板价格属商品）· `C-2020-RES-RAREEARTH`。★ **商品价格 ≠ A 股市场侧证据** |
| **G1-3 Beta Level 0–3** | **L0 = 43 · L1 = 9 · L2 = 0 · L3 = 0**（**未虚构 L2/L3**）。L1 共 9 个：R01-05 的 7 个 + `C-2023-HIEQ-ROBOT-PLUS` + `C-2025-ROBOTAXI`。★ **修正 Review 预估**：`C-2020-MIL-EQUIP-ORDER` 实为 **L0**（只有中证军工指数绝对涨跌，无宽基对比）；已排除伪 L1：`C-2024-SEMI-MEMORY`（绝对指数涨跌）· `C-2020-SEMI-EQUIPMENT`（「超额配售」为发行术语）· `C-2020-RES-LITHIUM`（「同期」对比对象是商品锂价） |
| **G1-5 `result=weak`** | 正式定义 = **行业 / 市场方向为负**（≠ 证据弱 / confidence 低 / 不成立）。`strength` **不得**为 `weak`。全库 `result=weak` **4** 个；**`strength=weak` 违例 1 个 = `C-2019-AD`**（legacy 残留）→ **本轮不修**，由校验器 **V8 持续 WARN**，提出独立修复（→ `strength: medium`，保留 `result: weak`） |
| **G2-1 Peak / End 四态** | EXACT / WINDOW / ALTERNATIVE（非空 `alternative` 表示）/ NULL。实测 peak：EXACT 22 / WINDOW 26 / NULL 4；end：EXACT 16 / WINDOW 30 / NULL 6；带 alternative 13 / 3。**未回填任何新日期**。★ 保留「商品 peak ≠ A 股 peak」（`C-2020-RES-LITHIUM` A股 2021-09-13 vs 商品 2022-11-11） |

**交付**：`docs/R01_GOVERNANCE_GATES_v0_1.md`（规则集，不覆盖冻结基座）·
`research/research/reports/governance_classification_v0_1.json`（机器可读，研究级）·
`research/scripts/build_governance_classification_v0_1.py` · `research/scripts/validate_governance_gates.py`

**★ 重要约束（实测）**：本轮**曾尝试**把 `governance` 加入 `exports/timeline_export_v1.json`，
触发 `validate_timeline_export` 的 **`CAMPAIGN_FIELDS` 严格白名单 FAIL（52 处）** →
在 Export 加字段 **= 事实上的 Contract 变更** → 依「不修改 Export Contract v1.0」**已回退**。
治理分类改由 **SA / TO 直接读取研究级 JSON**（与 `time_observation_patterns_v0_1.json` 同类）。
若确需进 Export，须**独立轮次**加入白名单并升 Contract v1.1。

**未改动（已核验 diff 为空）**：`batch_auto_research.py` · `validate_timeline_export.py` · DB Schema ·
DB 业务数据（campaigns 52 / themes 52 不变）· Intake Packages · Research Model v1.0 · Protocol · CMTR v1 · taxonomy。
**DB warning 仍为 3 条**（未新增）。

> **★ R01 六个任务已全部完成 Canonicalization**（Intake → Canonical Decision → DB Import → Export）。
> **★ Governance Review + 第一批治理修复已完成**。
> **下一步（待决策）**：① 是否执行第二批治理修复（G1-2 / G1-4 / G2-2 / G2-3 / G2-5 / G2-6）
> ② 是否刷新 SA / TO ③ `C-2019-AD` 的 `strength=weak` 独立修复。
> **下一步（待决策）**：是否按 G1 / G2 清单执行治理修复；修复完成后再刷新 SA / TO。
> **★ 建议顺序**：① G1-1 / G1-3 / G1-5 落地「约定」（改数据）→ 解 SA 阻塞 ② G2-1 Peak/End 四态规范 → 解 TO 阻塞
> ③ 刷新 SA ④ 刷新 TO ⑤ G1-2 / G1-4 / G2-3 / G2-4 / G2-6 按独立轮次处理。

### Governance Issue 分级（R01 Governance Review v0.1）

| 级别 | 数量 | 项 |
|---|---:|---|
| **G0 必须修复** | **0** | 无机械性错误 / 数据损坏 / 契约违规 |
| **G1 应统一** | **5** | G1-1 市场侧证据门槛（软门槛，非硬门槛）· G1-2 `research_report` Tier 向 Research Model §15 对齐 · G1-3 Beta / 相对收益 Level 0–3 分级 · G1-4 Validator 缺 orphan 检查 · G1-5 `result=weak` 语义（残留 `C-2019-AD` 的 `strength=weak`） |
| **G2 建议统一** | **6** | G2-1 Peak/End 四态规范 · G2-2 Theme Cycle Pattern 标注（4 个存疑）· G2-3 `campaign_date_observations` 缺失（5 个 pre-R01）· G2-4 孤儿 source / evidence 处置规范 · G2-5 3 条 temporal warning 定性 · G2-6 taxonomy aliases / Mechanism 登记 |
| **G3 可保持差异** | **4** | promote 率差异（29%~85%）· `campaign_themes.role` 未用 `catalyst` · 8 个未使用 theme · `classification` 分布差异 |

**实测关键数据**：DB↔Export **0 字段不一致** · 共享 evidence **0**（1:1 全库零违规）· rule↔campaign_year↔annual_review **零缺失** ·
taxonomy 未被任何 R01 修改（52 行 / 11 root，**11/11 均有 Campaign**）·
**Beta caveat 覆盖率 pre-R01 0/13 → R01-01 1/5 → R01-02 1/8 → R01-03 1/6 → R01-04 1/11 → R01-05 7/7 → R01-06 2/2**（标准随时间演进，非随机差异）·
`research_report` DB 内 **23 条全 tier=2**（R01-01 7 / R01-02 2 / R01-03 2 / R01-04 2 / R01-05 10 / **R01-06 0**；R01-06 改用 `media_tier3`+T3）·
孤儿 evidence **25**（R01-04 9 / R01-05 4 / R01-06 3 / R01-01 2 / legacy 7）· 孤儿 source **84**（R01-05 22 / R01-03 18 / R01-06 16 / R01-02 11 / R01-01 5 / R01-04 5 / legacy 7）·
**无任何 Campaign 达到 Beta Level 2 / 3**（L1 仅 R01-05 的 7 个 + R01-06 的 `C-2020-MIL-EQUIP-ORDER`）·
**3 条 DB warning 全部来自 R01-02**，属「期末/年度总结类证据」的内容期 vs 发布期口径差，**非数据错误**。

### Historical Universe 当前实测

| 项 | 值 |
|---|---:|
| Macro Theme 根节点 | **11** |
| **有 Campaign 的根节点** | **11 / 11**（汽车 · 医药健康 · 信息通信 · 电力设备 · 高端装备 · 电子 · 资源 · 消费 · 金融 · 房地产 · **国防军工**）★ **全覆盖，无空缺 root** |
| Historical Campaign | **52** |
| Research Candidate（导出层） | 27 |
| 跨族 Campaign 对 | `C(11,2)` = **55** |

**R01-06 新增 2 个 Canonical**：`C-2020-MIL-EQUIP-ORDER`（2020–2022 装备采购/订单景气；17 ev / 14 IG；
唯一具备「军费→订单→基本面→市场」四层可复核链条）· `C-2019-MIL-GROUP-RESTRUCTURE`（2019「南北船」集团战略重组；
**peak = NULL**，市场侧行情证据缺失）。
**5 个 RESEARCH_ONLY**：`RC-2019-MIL-PARADE-70` · `RC-2025-MIL-PARADE-80` · `RC-2017-MIL-MIXED-REFORM` ·
`RC-2015-MIL-REFORM-BULL` · `RC-2024-MIL-COMMERCIAL-SPACE`。
详见 `docs/R01_06_CANONICAL_DECISION_v0_1.md`。

**R01-06 关键裁决**：**`CF008`** 军费→订单传导**存在但不稳定**（2021 时滞约 9 周；**2022 预算 +7.1% 而板块 -23.63%** 为反证）→
**军费层只能作 `context`，不得作为 start 锚点** · **`CF001`** 2020H2 与 2021 **判为一个 Campaign（不拆分）** ·
**`CF004`** 商业航天**族属 UNRESOLVED** → 007 不进入任何族 · **`CF006`** 2015 Beta 不可分离 → 006 Research Only ·
**`E042`** 入 DB 但**不绑定任何 Campaign**（research-level，避免 temporal-mislabel）。

**R01-05 新增 7 个 Canonical**：`C-2022-RE-POLICY-THREE` · `C-2020-RE-DEBT-RISK`（`result = weak`）·
`C-2024-FIN-BROKER-POLICY` · `C-2023-FIN-SOE-VALUATION` · `C-2024-FIN-BANK-DIVIDEND`（peak/end = NULL）·
`C-2020-FIN-BANK-CREDIT` · `C-2025-FIN-INSURANCE`（peak/end = NULL）。
**5 个 RESEARCH_ONLY**：`RC-2024-RE-POLICY-517` · `RC-2019-RE-EASING` · `RC-2020-FIN-BROKER-VOLUME` ·
`RC-2016-RE-SHANTY` · `RC-2015-FIN-LEVERAGE`。
详见 `docs/R01_05_CANONICAL_DECISION_v0_1.md`。

**新增机制轴覆盖**：地产政策周期（融资收紧→风险暴露→政策修复）· **信用周期驱动**（银行顺周期）·
**估值重估/资金配置**（中特估 · 高股息）· **市场风险偏好/流动性**（券商 · 保险资产端）·
**装备采购/订单释放**（含甲方预付款 / 合同负债代理）· **军工集团改革/资产重组**。

**新增 Theme Cycle（7）**：`realestate_policy_cycle_2020_2023`(Sequential) · `bank_valuation_2023_2025`(Parallel) ·
`broker_risk_appetite_2024` · `bank_credit_cycle_2020_2021` · `insurance_asset_liability_2025` ·
`military_equipment_order_cycle_2020_2022` · `military_group_restructure_2019`。

### Structural Analogy / Time Observation

**★★ SA 已至 v0.4 · Time Observation 已至 v0.2（内部 0.3）—— Research Core Release 完成**（2026-09-23）。

**规则集状态**：**`Structural Analogy Rule Set v0.3`（`structural-analogy-ruleset-v0.3`）当前生效**；
v0.2 已被取代（其文本与 Calibration **逐字节保留**）。

**★ E.1 修复效果（`Driver = MISMATCH` 不得进入 `STRUCTURAL_PARTIAL`）**

| 组 | 规则 | driver 数据 | `STRUCTURAL_PARTIAL` | **其中 driver=MISMATCH** |
|---|---|---|---:|---:|
| A | v0.2 | v0.2 | 89 | **50**（= 已发布 SA v0.3 基线） |
| C | **v0.3** | v0.2 | 24 | **0** ✅ |
| D | **v0.3** | v0.3 | **39** | **0** ✅ |

→ **已彻底消除（50 → 0）**，且 **`STRUCTURAL_SUPPORTED` / `STRICT` 完全未变（4 / 1）** —— 未误伤强结构对应。

**★ E.2 词表扩展效果**：有 canonical driver 的 cycle **55 → 60**（**再经 RC driver 缺口修复 → 77 / 79**）· driving `UNKNOWN` **85 → 23**（修复后 86）·
新增覆盖 `C-2019-RES-DYE-SHOCK` / `C-2020-CONS-BEAUTY-CN` / `C-2020-RE-DEBT-RISK` / `C-2022-CONS-SERVICE-REBOUND` / `RC-2019-MIL-PARADE-70` / `RC-2025-MIL-PARADE-80`；
**4 个被点名的 Canonical Campaign 的缺口确认为「纯词表缺口」→ 无需 export 数据补全** ✅

**★ v0.3-r1 修订（2026-09-23，收口审计）**：「**阅兵**」「**纪念大会**」由 `POLICY_DRIVEN` **移至 `EVENT_CATALYST`** ——
原归属为**语义错误**（阅兵是一次性重大纪念活动 = 事件，不改变任何产业规则；且 v0.1 `EVENT_CATALYST` 已含「大会」等同类型活动）。
影响：`RC-2019-MIL-PARADE-70` `['POLICY_DRIVEN']`→`['EVENT_CATALYST']`；`RC-2025-MIL-PARADE-80` `[]`→`['EVENT_CATALYST']`；
`by_canonical_driver`：`POLICY_DRIVEN 58→56` · `EVENT_CATALYST 14→18`；`AMBIGUOUS 2→1`；**有 driver 的 cycle 59→60**。
★ **SA 层结构状态 0 变化**（两 cycle 各有 ≥2 个 `NOT_AVAILABLE` 维度 → 均落 `INSUFFICIENT_EVIDENCE`），
但 **driver 语义已由「资料不足」纠正为「机制不对应」**。

**★ 收口审计发现（`docs/DRIVER_KEYWORD_COLLISION_AUDIT_v0_3.md`）**：
新增词 **133**（声明 134，净新增 131；v0.1 基础 158 → 合并后 289）·
**新增词跨 canonical 重复 = 0** ✅ · 既有遗留跨 canonical 重复 **1**（`结构迁移`，v0.1 起，**不修**）·
**宽关键词风险 37** · **跨 canonical 子串冲突 6 → 5**（~~`扩产/扩产周期`~~ **✅ 已由 v0.3-r2 消除**；剩余 `增长/负增长` · `整治/整治提升` · `出口/出口管制` · `采购/装备采购` · `储备/黄金储备`）·
新增 `AMBIGUOUS` **0** · `DIRECT→DERIVED` **8**（受影响 Campaign 失去唯一 DIRECT 的仅 `C-2025-FIN-INSURANCE`，**不改变任何 SUPPORTED 结论**）·
**52 个 Canonical Campaign 100% 有 canonical driver** ✅ · 19 个无 driver 的 cycle **全部为 RC，未猜测** ✅

**★ v0.2 → v0.3 汇总（99 条变化）**：`PARTIAL 89→39` · `THEME_ONLY 6→9` · `INSUFFICIENT 145→125` · `NO_VALID 151→218` · `SUPPORTED 4→4` · `STRICT 1→1`

**★ 新增语义一致性校验器** `validate_structural_analogy_semantics.py`：**独立重算**（不 import builder 实现）
A/B/C/D **四组 1580 行逐行复核** + 语义不变量 **S1–S14**（含 **S14：`driver=MISMATCH` 的 `PARTIAL` 必须为 0**）。
**结果 PASS（FAIL 0 / WARN 0；1580/1580 一致）**。补齐了 A1–A16 未重算规则语义的缺口。

**★ 新增产物（8 个）**：`structural_analogy_rule_set_v0_3.md` · `structural_analogy_rule_calibration_v0_3.json` ·
`..._calibration_pairs_v0_3.csv`（**long format：395 × 4 = 1580 行**）· `historical_driver_canonicalization_v0_3.json` ·
`historical_driver_evidence_ledger_v0_3.json` · 3 个脚本（含 2 个生成器 + 语义校验器）

**★ SA v0.4 前处理项（全部已闭环）**：
| # | 问题 | 级别 |
|---|---|---|
| ~~1~~ | ~~18 个 Research Candidate 的 export `drivers` 全为空~~ → **✅ 本轮已修复**（18/18 为 `CANDIDATE_DRIVERS` 映射遗漏；9 → 27 条；RC 空 drivers **18 → 0**；有 driver 的 cycle **60 → 77 / 79**）。详见 `docs/RC_EXPORT_DRIVER_GAP_AUDIT_v0_3.md` | **已解除** |
| ~~2~~ | ~~`扩产` vs `扩产周期` 语义自相矛盾~~ → **✅ 本轮已裁决并修复（v0.3-r2）**：`扩产` → **A 保留在 `DEMAND_SURGE`**；`扩产周期` → **D 删除**（零增量覆盖 + 方向错误 + 实际损害）。详见 `docs/KUOCHAN_SEMANTICS_DECISION_v0_3.md` | **已解除** |
| ~~3~~ | ~~剩余 5 项跨 canonical 子串冲突~~ → **✅ 已完成（v0.4）**：3 项删词（`整治提升` / `装备采购` / `黄金储备`）+ 2 项最小上下文消歧（`增长` 否定语境 · `出口` 限制语境）。子串冲突 **10 → 7**；**`E2` driver 效应 = 0 条 Structural Status 变化**。详见 `docs/RESEARCH_CORE_RELEASE_v0_4.md` | **已解除** |
| ~~4~~ | ~~SA v0.3 产物过期~~ → **✅ 已由 SA v0.4 消费**（`structural_analogy_research_v0_4.json` / `..._explanations_v0_4.json`）；v0.3 产物**逐字节保留**作为历史版本 | **已解除** |
| ~~5~~ | ~~E.3 identity 缺陷~~ → **✅ v0.4 已修正**（按来源数组判定：**52 campaign / 27 research_candidate**，identity 错误 = 0） | **已解除** |
| 6 | **E.4**：关键词扩展副作用 —— 8 条 `DIRECT→DERIVED`；`C-2025-FIN-INSURANCE` 失去唯一 DIRECT（**不改变任何 SUPPORTED 结论**） | 轻微 |
| 7 | （观测）2 个 cycle 因**映射逻辑**仍无 canonical driver（`RC-2015-FIN-LEVERAGE` 多命中无消歧 · `RC-2024-SECONDARY` 研究自述强度不足）—— **非数据缺口** | 观测 |

> **★★ Research Core Release 已完成** —— 上表 1~5 全部闭环；SA v0.4 已生成并通过两层独立校验（含 S15 driver 版本一致性）。
> 剩余项见「Known Limitations」，**不再阻塞推进**。
> ★ 数据层（原问题 1）与 `扩产/扩产周期`（原问题 2）**均已不再是阻塞**。

**★ Governance 元数据接入**：`governance-gates-v0.1` 的 `market_evidence_state` / `beta_level` / `peak|end` / `result`
仅进入 `supplementary` / `governance_context`，**不参与 Structural Status**（Rule Set §9）。

**★ SA / TO 输入字段来源（因 Export Contract v1.0 未改）**：治理字段**不在**
`exports/timeline_export_v1.json` 中（加入会触发 `CAMPAIGN_FIELDS` 白名单 FAIL），
SA / TO 须**直接读取** `research/research/reports/governance_classification_v0_1.json`。

**下一步（待决策）**：① export 数据补全（18 RC 的 drivers）② 多命中消歧评估 ③ 修正 E.3（kind metadata）
④ **生成 SA v0.4**（用 Rule Set v0.3 + Canonicalization v0.3）⑤ **Time Observation 刷新**（建议在 SA v0.4 之后）
⑥ 第二批治理修复 ⑦ `C-2019-AD` 的 `strength=weak` 修复。

### 未决与待办（**未排期**）

| 类型 | 项 |
|---|---|
| OPEN | **`CF013` 股息口径差**（个股前复权含股息 vs 沪深300 价格指数不含股息）—— **UNRESOLVED**；已转为**结论约束**（**不得解释为行业 Alpha**、未伪造调整后收益）；需以**中证红利全收益 / 银行行业全收益指数**重算 |
| OPEN | R01-05 保留未决：`CF001`(Q2 标的重叠) · `CF003`(券商全市场 Beta) · `CF004`(红利风格因子) · `CF005`(中特估银行/保险边界) · `CF006`(房地产 vs 金融 Cycle 归属) · `CF008`(2020-07 券商驱动) · `CF009`(KEEP_BOTH) · `CF011`(两龙头方向相反，不允许取平均) · `CF012`(保险代表标的 vs 板块叙事) |
| OPEN | R01-05 生命周期未闭合：`C-2024-FIN-BANK-DIVIDEND` / `C-2025-FIN-INSURANCE` **peak/end = NULL** · `C-2023-FIN-SOE-VALUATION` peak/end 为推断值；`C-2020-FIN-BANK-CREDIT` 仅 4 ev / 4 IG + 单一标的 → **建议后续补证** |
| OPEN | **本地无金融/地产行情序列** → R01-05 的 Export `market_data = unavailable`（相对表现仅引自 intake 一级行情证据） |
| OPEN | **`CF007`**（医美归属：消费 vs 医药健康）保留未裁决 · **`CF005`**（白电驱动归因）保留 · **`CF010`**（补贴 vs 真实需求；**`+11%` vs `-4.3%` 口径冲突完整保留**）· **`CF001`**（白酒 classification）保留 |
| OPEN | **`RC-2020-CONS-SMALL-APPLIANCE`（007）仍需补证**（渗透率一手数据 + 同期证据）· **`RC-2024-CONS-PET-FOOD`（013）保持 Research Only** |
| OPEN | `C-2020-CONS-DUTYFREE` **A 股广度不足**（sec=1）· `C-2023-CONS-VALUE-RETAIL` **start 年度级 + end NULL** · `C-2024-CONS-TRADE-IN` **Beta 未排除** |
| OPEN | **跨任务「市场关注」口径差异未统一**（R01-03 起更严 vs R01-01/02）—— **本轮未固化新 Protocol、未回改历史**；**R01-06 `N007` 另提出「R01-05 与 R01-06 的 Beta 判据应保持一致，否则跨族结构比较不可比」** |
| OPEN | **`美容护理` / `商贸零售` taxonomy 缺口**（`MT006`/`MT007` 提案级未解析）—— 不扩展 |
| OPEN | R01-03 的 `CF003`（锂跨族）· `CF009`（黄金背离）保留未决 |
| OPEN | R01-02 的 3 条 `evidence-temporal-mislabel` 警告（已收口为 caveat） |
| OPEN | **仅剩 1 个 root 无 Campaign：国防军工** —— **R01-06 已导入 2 个 Campaign**（`C-2020-MIL-EQUIP-ORDER` / `C-2019-MIL-GROUP-RESTRUCTURE`）→ **11 个 root 中已有 11 个具备 Campaign**（原「无 Campaign 的 root」问题**已解决**） |
| OPEN | **R01-06 保留未决**：`CF005`（船舶：民船周期 vs 军品订单；**与 T01 的归属张力**待对齐）· `CF009`（2017 军民融合 vs 混改）· `CF004`（商业航天族属 UNRESOLVED）· `CF001`（2020H2/2021 阶段边界，**保留重新评估条件**） |
| OPEN | **R01-06 待处理项**：`E042` 的 `role = context`（全包 `contradicting = 0` → 建议 R01 Governance Review 统一）；4 条 evidence 缺 `event_date`（E008/E017/E037/E038）；`SEC003`（国证军工指数）`ticker = null`；`CF004.note` 笔误「TwoC Agent」；`002.why_not` 交叉引用错误（引 CF004 讨论 classification） |
| OPEN | **R01-06 的 `001` Beta 污染未分离**（2020-07 启动段）· **`002` 市场侧行情证据完全缺失**（`peak = NULL`）· `003/004/005/007` 生命周期未闭合 · `005` 需补证（2017 分月行情 + 混改落地公告） |
| OPEN | **本地无军工行情序列** → R01-06 的 Export `market_data = unavailable`（市场数据仅引自 intake 二手整理，全 T3） |
| OPEN | Validator C08 vs Research Model v1.0 §15 的 `research_report` tier 冲突（**R01-03 `H1` / R01-05 `K` / R01-06 第三次复现** → **Cross-task governance issue，待 R01 Governance Review 统一处理**） |
| OPEN | **✅ 第一批治理修复已完成**（`governance-gates-v0.1`）：G1-1 市场侧证据软门槛 · G1-3 Beta Level 0–3 · G1-5 `result=weak` 语义 · G2-1 Peak/End 四态。**规则 + 机器可读清单 + 校验器已交付，未改任何 Campaign / Schema / Contract / taxonomy** |
| OPEN | **✅ Rule Set v0.2 的 E.1 / E.2 已修复（2026-09-22）**：新建 **Rule Set v0.3**（`Driver=MISMATCH` 不得进入 `STRUCTURAL_PARTIAL`，**50 → 0 彻底消除**）+ **Driver Canonicalization v0.3**（词表扩展，有 driver 的 cycle **55 → 59**）+ **Rule Calibration v0.3** + **语义一致性校验器**（S1–S14，1580/1580 一致）。**未生成 SA v0.4 · 未覆盖 SA v0.3 · 未刷新 TO** |
| CLOSED | **SA v0.4 前置待办 —— ✅ 全部闭环（Research Core Release）**：① 18 个 RC export driver 缺口 ✅ · ② `扩产/扩产周期` ✅ · ③ 剩余 5 项 collision ✅（v0.4：3 删词 + 2 上下文抑制）· ④ SA v0.3 过期 ✅（由 SA v0.4 消费）· ⑤ E.3 identity ✅（52/27）· ⑥ E.4 轻微（保留为已知限制）· ⑦ 2 个 cycle 映射逻辑（保留为已知限制） |
| OPEN | **Time Observation 仍未刷新**（SA 已至 v0.3；建议在 SA v0.4 之后统一刷新） |
| OPEN | **第二批治理修复待决策（本轮未做，仅 issue register）**：G1-2 `research_report` Tier（**须逐条确认是否真属 Research Model §15 的券商研报，不得把 23 条 tier=2 一律改成 tier=3**）· G1-4 Validator 加 C26 orphan report · G2-2 Theme Cycle Pattern · G2-3 5 个 pre-R01 缺 date_observations · G2-5 3 条 temporal warning · G2-6 taxonomy alias 表 + Mechanism 登记表（**不扩展 taxonomy**） |
| OPEN | **历史数据修复需求（唯一 1 项，待独立评审）**：`C-2019-AD` 的 `strength='weak'` → 建议改 `medium`（保留 `result='weak'`）。属 legacy 语义残留，非本轮规则引入；由 `validate_governance_gates.py` **V8 持续 WARN**。影响：DB 1 行 / Export 1 条 / SA 轻微 |
| OPEN | **Worker ↔ ThreeC 规则统一待办**：Worker 报 `24 checks` vs ThreeC `C01–C25` · Worker 无 Strict Draft-07 · Worker `--check` 目录假设差异 · **Worker 无 orphan 检查** · **须向 Worker 提供 T01 后的 taxonomy 快照（11 root / 52 行）**（R01-06 manifest 曾误称 root 仅 4 个） · 建议后续为 Worker 增加 C26 并统一 `--check` 行为（**本轮不重建 Worker**） |
| OPEN | R01-05 孤儿证据 `E-FINRE-49/50/51/63`（intake 中未被任何候选引用）按既有惯例导入；`E-FINRE-63` = 全局基准 E141 · R01-06 孤儿证据 `E-MIL-40/41/42`（`E-MIL-42` = E042 反向证据，research-level 不绑定） |
| POLISH | `themeCycleId` 可读性 · `event_type` ↔ 证据类别标签对应 |

### 边界

- 不新增 Product 功能 / 不新增 Dashboard
- 不改 Research Model v1.0 / schema / CMTR v1 / Export Contract v1.0 /
  Structural Analogy Rule Set v0.2 / Time Observation v0.5
- 不引入实时网络 / LLM · 不建立 ranking / score / probability / prediction

| DONE | **★★ Research Core Release 完成（2026-09-23）**：Driver Canonicalization **v0.4** · **SA v0.4**（395 pairs · identity 52/27 · 两层独立校验 PASS · `driver=MISMATCH→PARTIAL` = 0）· **Time Observation v0.2**（79 objects · 12 patterns · **Timeline 仍仅 TOP-01**）· **Product 已消费最新 artifact**（`tsc -b` / `vite build` PASS）· 旧版本 18 个文件逐字节 UNCHANGED。详见 `docs/RESEARCH_CORE_RELEASE_v0_4.md` |

</details>

## 8. 当前质量债务

非主线 blocker：
- campaign_date_observations verified = 0/131
- Driver DIRECT evidence depth
- market / temporal = SUPPLEMENTARY_ONLY
- historical coverage imbalance

这些问题暂不阻塞本阶段 Review，但性能问题必须在 Product polish 前闭环。

## 9. 验证基线

最近已报告全绿：
- Structural Analogy Explanation `--check` PASS
- Research validators 全 PASS（`validate_db` / `validate_timeline_export` / `validate_batch_research` /
  `validate_promotion_manifest` / `check_doc_schema_consistency` / `validate_current_research` /
  `validate_monorepo_integrity` / `refresh --check`）
- **Intake Validator `--check` PASS（25 checks，FAIL 0，WARN 0；含 C25 严格 Draft-07；packages found 6）**
- **Intake Package R01-01 ~ R01-06 各 PASS（C01–C25）** · **Validator 单元测试 44/44 PASS**
- **R01-06 Canonical Import**：`validate_db` PASS（**3 条 WARNING 与导入前完全相同，无新增 temporal warning**）·
  既有 50 Campaign 逐条深比对 0 修改 · taxonomy `themes` 52→52 未变 · `import --verify` 幂等 · LF 不变式全 CRLF=0
- **R01 Governance Review（审计，未改数据）**：DB↔Export **0 字段不一致**（52↔52）· 共享 evidence **0**（1:1 全库零违规）·
  孤儿 evidence 25 / 孤儿 source 84 已人工复核 · 6 个新 rule 的 `campaign_year` ⊇ `annual_review` **零缺失** ·
  **3 条 DB warning 全部来自 R01-02**（总结类证据内容期 vs 发布期口径差，非数据错误）· **G0 = 0**
- npm test 476/476
- tsc -b PASS
- vite build PASS

下一轮任何实现先核对真实 HEAD，再执行验证。
