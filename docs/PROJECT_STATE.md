# PROJECT_STATE.md — ThreeC 当前真实状态

> 动态接班文档：只回答“现在是什么状态、哪里有问题、下一步做什么”。
> 长期规则见 `AGENTS.md`；未来路线见 `docs/ROADMAP.md`；历史细节见 `docs/CHANGELOG.md`。

## ★★ 当前状态（2026-10-20 修订 · 历史题材地图 ×8（33 事件） + 行情刷新至 2026-10-20 + 季节性 25 项逐项核验 + 标的与 Research 对象对账 + SA 交叉引用可导航 + 数据缺口审计）

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
> 在事件详情与标的索引逐次记录呈现，**六题材通用**（v0.17 当时口径：123 条参与记录 = 已登记 63 / 地图补充 0 / 无法核对 60 —— **v0.18 起已拆为四分类**，见下）。
> ★★ **2026-10-18 晚（v0.18）**：① **补齐已有明确证据的对象关联** —— `FLU-2023-H1N1` 新增
> `campaign_facts → object_id = C-2023-PHARMA-FLU`（依据：其 `evidence_basis` 明确引用该 Campaign、
> 3 只标的与对象 `security_ids` **逐一相等**），流感题材升 **v0_7**（v0_1~v0_6 逐字节保留，**数值零变化**）；
> ② **对账四分类** —— 把「事件未记录对象」从 `UNRESOLVED` 拆出为 **`NO_OBJECT_REFERENCE`（未登记对象关联）**，
> 与「已提供引用但对象无法解析 / 证券注册信息缺失」的 `UNRESOLVED` **区分**。
> 实测 123 条参与记录 = 已登记 **66** / 地图补充 0 / 未登记对象关联 **57** / 无法核对 **0**。
> ★★ **2026-10-18 晚（v0.19）**：① **对账语义收口** —— 把「证券是否**精确命中** canonical export
> 注册表」作为**独立第二个事实**分开呈现（**不**新增第五类、**不**互相推导）：未命中时如实标
> 「证券注册表：未命中」并声明「只是需核对的标识差异 ≠ 证券不存在 ≠ 可自动匹配」
> （实测 **87 命中 / 36 未命中**，全部在流感旧式标识，如 `YILING-002603` vs `YILING`）；
> ② **三场景真实工作流闭环验证**（汽车 / 医药 / 文化传媒）并**修复一处真实缺陷**
> （催化时间线同日同前缀 → React 重复 key）。
> ★★ **2026-10-18 晚（v0.20）**：① **未关联行情行不再只给裸 ID** —— 行情键在本事件 `participants`
> 里找不到**同一精确 ID** 时，标「**行情记录未关联事件参与者**」+ 声明「**行情记录存在 ≠ 事件参与者记录存在**」；
> 名称 / 代码只取自**同一精确 ID** 的 canonical export 注册表（**不**跨 ID 推断、**不**自动合并）。
> 实测 3 条（全为 `YILING`）；② **草稿复制动作验收**（复制 JSON / Markdown 内容 = 预览内容、失败不虚报）。

> ★★ 浏览器复核（v0.20 起）：本机**有 Edge / Safari**，用户已指出此前「本机无浏览器」的说法不成立 ——
> 自本批次起，**部署后必须用浏览器实机复核线上 Pages**（不再以「无浏览器」为由跳过视觉核验）。
> ★★ **2026-10-18/19（v0.21）**：① **历史事件 × 冻结 SA 精确交叉引用** —— 事件详情新增
> 「与当前冻结 SA 的关系」块：按事件 `object_id`（兼容 `campaign_id`）与唯一 `CANONICAL` 快照
> （`MS-2026-10-13-01`）的 `historical_candidates.identity` **精确匹配**，列出引用该历史对象的
> 当前研究对象与**既有** `structural_status`（**不重算 SA、不推测归属**）；
> 实测（v0.24 口径）**26 事件中 18 个有对象引用 · 18 个命中 · 0 个未命中**，匹配记录 **108 条**；★ v0.25 地图扩到 8 题材 / 33 事件后，新增 7 个事件均挂库内 Campaign（`campaign_facts.object_id`），SA 交叉引用按同一精确 ID 规则自动覆盖；
> ② **真实浏览器窄屏实测发现并修复一处布局缺陷**（长不可断串撑破题材地图 → 整页横向溢出）。
> ★★ **2026-10-19（v0.22）**：① **SA 交叉引用可导航到「当前研究对象」详情** —— 事件详情
> 「与当前冻结 SA 的关系」列表每条新增「**查看当前对象详情**」，接入 App **既有**
> `focusObject` / CurrentTimeLens 流程（**不**复用历史对象的 `openHistoricalObject`，
> 两种对象各走各的既有流程）；按 SA 记录里的 `currentObjectId` **精确 ID** 确认可被
> `current_candidates.json` 的 `CC-*` 解析，**解析不了就不给按钮**（保留 ID / 名称 / 状态并说明）。
> ② **修复 CANONICAL 唯一性门禁** —— 原 `loadSaCrossReference()` 对 CANONICAL 排序后**取最后一项**
> （= 索引意外出现两个 CANONICAL 时**静默选最新**）；改为抽出可测纯函数 `pickCanonicalSnapshot`：
> **0 个 → 无法判定**、**恰好 1 个 → 载入并二次确认**、**多于 1 个 → 拒绝选择并披露**（不再静默）。
> ③ **真实浏览器复测线上 Pages**：缓存绕过（`?v=nocache1`）后「半导体事件 → SA 当前对象列表 →
> 当前对象结构详情」**闭环走通**（6 行 × 6 个按钮；点击后定位 Current Time Lens、恰好一个候选展开、
> 显示 Structural Analogy 区块与当前对象名称）。
> ★★ **2026-10-19（v0.23 · 数据缺口审计）**：本轮**不堆 UI**，只把三处长期缺口核验成**可追溯裁决表**
> （`research/research/reports/data_gap_audit_v0_1.json`，由 `research/scripts/build_data_gap_audit_v0_1.py`
> 确定性生成，**只读**）：
> **A** 证券注册表未命中（**36 条记录 / 17 个不同标识**，全部流感）→ 根因 = canonical export 的 `securities`
> 注册表是 **owner-scoped**（合同 §8；**实测**注册表 190 条 == 各 owner `security_ids` 并集 190 条，零差集），
> 17 个标识**全部存在于** DB `securities` 原始记录（含 ticker / 交易所），但**未被任何导出对象引用**；
> 逐条经**交易所披露**（深/沪年报摘要或上市交易通知，URL + 日期入表）核验身份 →
> **1 PROVISIONAL**（`YILING-002603` → `YILING`：DB 内同 ticker 002603 同名的**重复标识**，目标在注册表内；
> ★ 依硬约束**不自动合并**，仅**提出**映射）+ **16 UNRESOLVED**（身份已确认但**无**规范 ID 可映射 ⇒
> 缺口性质是 **ownership 覆盖**，**不是**标识错误）。
> **B** 未登记对象关联（**57 条记录 / 8 事件**：流感 5 + 电力 3）→ 逐事件核验：事件文本**未引用**任何
> Campaign / RC id，且参与者 `security_id` 集合与**任何**导出对象的 `security_ids`**均不相等**
> → **8 / 8 UNRESOLVED**（无证据支持归属；**不**按主题相近或年份相近推断）。
> **C** 大基金三期窗口 4 只标的（SMIC / AMEC / PIOTECH / HYGON）→ 实测根因：**3 只序列抓取止于
> 2021-09-30 / 2022-10-12**（`FETCH_COVERAGE_GAP`）+ **1 只序列从未登记**（拓荆科技，`SERIES_NOT_REGISTERED`）
> —— **非标识问题**。★★ **用户授权后已执行「数据层补齐」**：用**既有**抓取流程
> `research/scripts/fetch_market_batch_v0_3.py`（`--only` + `--series` 显式区间）从**同一 provider**
> 取真值 → `market_daily` **376,401 → 380,771 行**、`market_series` **213 → 214**（补登拓荆科技序列），
> 随后 `make_market_snapshot.py` **重生成便携快照**（**6.09 → 6.22 MiB**）且 `restore --check` **PASS**
> （逐分片哈希一致、REAL 逐位相同）；★ 既有行**逐 (date,price_type) 比对：0 变更 / 0 丢失**。
> → 窗口 2024-09-24 ~ 2024-11-29 现各有 **44** 个 adjusted 交易日 ⇒ **数据层缺口已关闭（4 RESOLVED）**。
> ★★ 但**地图展示未刷新**（**UNRESOLVED**）：实测 **12 份题材文档的 `max_drawdown_from_high_pct` 等口径
> 互相不一致**，任一单一公式都**无法复现**（逐一验算仅 3/12 可完全复现）⇒ 强行重算＝编造，
> 须由**独立、可复现的转写流程**（新轮次）统一口径后再生效；本轮**未手工改任何展示值**。
> ★ **A/B 未改任何数据**（前后计数完全相同）；未改 canonical export / SA / TO / Driver / `schema.sql` /
> 冻结历史轮次。合计 **RESOLVED 4 · PROVISIONAL 1 · UNRESOLVED 24**（+ C 的转写待办 1 项）。
> ★★ **2026-10-19（v0.24 · 行情转写合同 + 漂移门禁）**：把「行情库 ↔ 题材地图」这条**唯一断链**接上。
> ① **查清了口径**（这是 v0.23「仅 3/12 可复现」的根因，**不是**文件互相矛盾）：
>    `max_drawdown_from_high_pct` 的语义是「**自窗口最高收盘价之后**的最大回撤」，
>    而 v0.23 的验算用的是「**全窗口**最大回撤」——两者在「高点不在窗口首日」时必然不同
>    （实测 FLU-2018 基准：-3.0 vs -6.07）。改用合同口径后，**93 / 105 组数值逐字段复现**
>    （容差 0.05pp = 1 位小数的半个单位），**12 份文档中 11 份可完全复现**。
> ② **建立唯一入口** `research/scripts/build_theme_market_performance.py`，口径写成
>    **代码 + 产物里的 `market_performance_contract`**（`theme_market_performance_v1`）：
>    adjusted 收盘 · 窗口双端包含 · `high` = 窗口内最高**收盘**（非 `high` 列、非 Campaign `peak_date`）·
>    回撤自至高点之后 · 超额 = 个股 − 基准（两列口径不同）· 1 位小数 · 缺失给 `error + reason`。
>    `--check` 只读、非零退出；`--write` 生成**新版本**、**拒绝覆盖**、同时改索引。
> ③ **交付 `SEMI-2024-FUND3`**：`semiconductor_ai_compute_historical_events_v0_2.json`（v0_1 逐字节保留），
>    4 只标的**从恢复后的库重算**（各 44 个 adjusted 交易日）：
>    中芯国际 **+101.3%**（至高点 +134.5%，高点 2024-11-11）· 中微公司 **+83.6%**（+103.8%，11-12）·
>    拓荆科技 **+86.2%**（+98.5%，11-11）· 海光信息 **+61.4%**（+81.9%，11-07）；
>    同期基准 SH000300 **+16.8%**（至高点 +27.0%）。`study_state` `NO_PRICE_DATA → HAS_PRICE_DATA`。
>    ★★ **`RC-2024-SEMI-FUND3` 官方 `INSUFFICIENT` 判定不变**，Beta Contamination 写在 `known_gaps` 首条。
> ④ **实机渲染探针暴露并修复两处静默缺陷**：① `power_historical_events_v0_3.json` 用**扁平**
>    `high_date`/`high_close` 写高点，而 UI 只读 `high.date` → **12 行「高点日」一直显示 `—`**；
>    新增 `highPointOf()` 两种写法统一读取（数值零变化）。② 行情段 / 业务机制段的两条免责声明
>    与 **7 处**说明文字（含 SA 交叉引用三条分支、注册表未命中说明、催化来源、报道当日涨幅）
>    把 `**` **原样显示成星号**（本项目已知陷阱）→ 全部改走 `<RichText>` / `<strong>`；`title` 属性走 `plain()`。
>    ★ 新增**穷举断言**：**6 题材 × 26 事件 × 4 种 SA 分支的展开态**渲染结果都不得出现 `**`
>    （折叠态扫不到正文 —— 这正是它长期没被发现的原因）。③ 索引 `display.note` 里「大基金三期窗口
>    全部标的行情均不覆盖」**已成假话** → 按实况改写（这是**渲染**才暴露的语义漂移，不是字段问题）。
> ⑤ **新发现（本轮未关闭）**：`POWER-2017-SUMMER-COUNTEREXAMPLE` 的 4 组数值**无法由当前行情库复算**
>    —— 华电 / 建投能源 / 天富能源 序列**自 2022-01-04 起**、京能 2020-01-02 起，2017 窗口**无任何行**。
>    按纪律标 **UNVERIFIABLE（WARN）**：**不改数、不删数、不补数**，要关闭须补 2017 段行情。
> ⑥ **CI 门禁**：`deploy.yml` 在 `restore_market_data --apply/--check` **之后**新增
>    「Theme market performance consistency (--check)」+ 契约单测；**只读**，失败即**不部署**，
>    **不得**在 CI 内 `--write`（CI 不自行签发版本化产物）。
> ★★ **2026-10-20（v0.25 · 初始可用化）** —— 目标：让 ThreeC 达到「可以开始正常使用」。
> ① **阶段 A · 行情刷新到最后一个实际交易日**：`SH000300` 由 2026-09-30 补到 **2026-10-19**
>    （`fetch_market_batch_v0_3.py`，按**真实交易日**、不按日历天补数）；`trading_calendar` 2,863 天、
>    便携快照重建（market_daily **394,184 行**、3 表合计 **397,261 行**）；提前观察 `as_of` 同步
>    **2026-10-19**（收盘 4174.53 · 20 日 -7.44%）。（注：**v0.26 已再刷新**，见下方 v0.26 段；
>    本行 397,261 是 v0.25 当轮的**3 表合计**口径，与基线表的 market_daily 单表数不矛盾。）
>    另为进入历史题材地图的代表标的补抓**全历史** 10 只（SMIC / PIOTECH / HYGON / MAXSCEND / NSIG /
>    AIMEIKE / BLOOMAGE / BETTENI / KINCO / LEADERDRIVE；WUHANFANGU 无 ticker、SWMIL 申万指数
>    不在本抓取流程覆盖内，两者**如实记为无序列**）。
>    ★ **门禁当场捕获漂移**：半导体 v0_2 参与者覆盖文本过期（序列范围已变）→ 按流程升 **v0_3**
>    （**数值零变化**，仅文本刷新）—— 这正是 v0.24 门禁的设计目的，不是手工改数。
> ② **阶段 B · 25 项季节性线索逐项核验**：`external_seasonal_calendar_v0_2.json`（v0_1 逐字节保留）。
>    每项回答六问（原始窗口与来源 / 性质分类 / 库内真实事件 / 反例 / 代表标的 / 处置与下一步）。
>    处置分布（**以产物 `verification_summary` 实测为准**）：**MAPPED 1 · OBSERVING 13 ·
>    PARTIALLY_VALIDATED 2 · EXTERNAL_REFERENCE 9**；
>    **没有任何一项**达到 `THREEC_VALIDATED`（正式研究标准未满足则不抬升），也无一项被 `REJECTED`
>    —— 证据不足的如实写「证据不足」。原报告不在仓库 → `source_check.report_available: false` 逐项写明，
>    **没有一项声称读过原报告**（外部来源缺口如实保留）。
>    下一步分布：**MAP 10 · DRAFT 11 · OBSERVE 2 · NONE 2**；产品侧无地图条目给
>    「带入『研究方向查询』草稿」按钮（携带题材、原始窗口、外部来源**与 ThreeC 已有核验结论**；
>    核验日期只到**月份精度**，遵守草稿红线）。
> ③ **阶段 C · 两张新题材地图**：**消费旺季 / 大众消费（5 事件）** 与 **资源品 / 黄金·稀土（2 事件）**
>    （`build_theme_map_v0_1.py` 从**库内 Campaign** 生成；窗口 = Campaign **主升段**，
>    **不是**季节性月份窗口 —— 地图**不**证明季节性规律，`display.note` 明写）。
>    Product 地图 **6 → 8**、事件 **26 → 33**、参与记录 +25。
>    ★ 新发现两处**数据源方法学**问题并升级合同（不改数、不猜数）：
>    上游 qfq「除权价差」法在**高分红个股早年会产生负价**（2015–2016 白酒段：茅台 / 五粮液 / 泸州老窖）
>    → `invalid_price_series`（`non_positive_adj_close`），**不用负价算收益率**，事件 `known_gaps` 明写原因；
>    另加守卫：窗口内任一对相邻交易日 **跳变 >45%** → `discontinuous_series`（A 股单日涨跌幅上限 ≤30%）。
> ④ **阶段 D · 提前观察可用化**：覆盖 **OK 49 → 54 · PARTIAL 13 → 8 · NO_DATA 0**（本轮刷新前基线）。
>    剩余 8 个 PARTIAL **逐条查因并写入产物**：10 只「上市/序列起始日晚于 Campaign 起始」·
>    1 只「启动前不足 60 个交易日」· 2 只「无行情序列」（WUHANFANGU = 证券归属缺口，本轮边界不动；
>    SWMIL = 申万指数，本抓取流程不覆盖）。**产品侧不再过滤 NO_DATA 行** ——
>    缺哪几只、为什么，在 Campaign 详情里逐条可见（此前静默过滤 = 用户看不到缺口）。
>    当前市场状态在全局位置展示，日期与产物 `as_of` 逐字一致（断言锁住）。
> ⑤ **实机复核再抓一处措辞漂移（渲染才可见）**：AUTO 行情缺口行原先把**所有**不可得
>    一律写成「库内无该证券日线登记或无窗口数据」—— 对 2016 白酒段（库内**有**序列、
>    只是 qfq 早年**非正价格**）是**错的归因**。改为**逐类写原因**（`no_series` /
>    `no_rows_in_window` / `non_positive_adj_close` / `discontinuous_series` 各一句），
>    并按纪律升版：`consumer_season_…_v0_2` · `resource_metal_…_v0_2` ·
>    `semiconductor_…_v0_4`（v0_1 / v0_3 逐字节保留，**数值零变化**，只改 AUTO 文字）。

> ★★ **2026-10-20（v0.26 · 行情刷新 + POWER-2017 补齐 + 事实一致性修正）**：
> ① **当前市场状态刷新到 2026-10-20**（当日已收盘；按真实交易日推进，不按日历天）：
>    `SH000300` 收盘 **4152.11** · 20 日 **-7.32%** · 量分位 0.183 · 波动率比 0.803（MA20/MA60 下）；
>    同时刷新本流程覆盖的 **10 只标的**（SMIC / PIOTECH / HYGON / MAXSCEND / NSIG / AIMEIKE /
>    BLOOMAGE / BETTENI / KINCO / LEADERDRIVE）。`trading_calendar` 2,863 → **2,864 行**；
>    快照重建（`market_daily` **395,038 行**、3 表合计 **398,116 行**）；`restore --check` 与
>    `make_market_snapshot --check` 均 PASS（逐分片哈希一致）；`early_observation` 的
>    `current_market.as_of` 与页面市场条日期**逐字一致**（断言锁住）。
>    ★ 漂移门禁再次生效：`--check` 报 **11 行覆盖文本过期**（序列末端 2026-10-19 → 10-20）
>    → 按流程升版而非手改（见 ③）。
> ② **POWER-2017 的 4 组 UNVERIFIABLE 关闭（WARN 4 → 0）**：此前 4 只标的（华电国际 /
>    建投能源 / 天富能源 / 京能电力）**序列只抓到 2022 年起**，2017 窗口无行。本轮按**真实证券标识**
>    （sh600027 / sz000600 / sh600509 / sh600578）请求 **2017-04-01~2017-08-31**，provider **返回真实数据**
>    （各 104 行，2017-04-05 起）→ 复算值与产物**完全吻合**（63 个交易日）：
>    华电 **-8.2%** · 建投 **-27.4%** · 天富 **+8.0%** · 京能 **-4.0%**（同期基准 **+9.1%** —— 与「反例」定性一致）。
>    ★ **没有**手填数值、**没有**用其他指数替代、**没有**为消警改数据 —— 只是把本来就有的数据抓全。
> ③ **两个题材按现有规则升版**（旧版逐字节保留，**数值零变化**）：
>    · `power_historical_events_v0_4.json`（v0_3 保留）：2017 四只**验证通过**；修正参与者
>      `market_data` 陈旧文案（旧写「2016-01-04~2025-12-31 / 2419 行」，库内实况
>      「2017-04-05~2024-12-31 / 1640 行」—— 页面会显示错的首末日期）；补 `corrections`。
>    · `semiconductor_ai_compute_historical_events_v0_5.json`（v0_4 保留）：仅覆盖文本末端刷新。
>    百分比由旧 2 位小数 → 合同 1 位小数（等价，容差内，例 -27.35 → -27.4）。
> ④ **v0.25 事实一致性修正**（文档对齐产物，**不改产物**）：
>    · 25 项处置分布：README / PROJECT_STATE 原写 `MAPPED 1 · OBSERVING 15 · PARTIALLY_VALIDATED 2 ·
>      EXTERNAL_REFERENCE 7`；产物 `verification_summary` 实测为 **1 / 13 / 2 / 9** → 文档已按产物修正
>      （★★ 不反向改产物去凑文案）。
>    · v0.25 段的「快照 397,261 行」= **3 表合计**口径，与基线表 `market_daily` 单表 394,184 **不矛盾**；
>      本轮起基线表统一为单表口径并注明合计，杜绝两数并存的读法。
>    · 总标题由「2026-10-19 · 地图 ×6」更新为「2026-10-20 · 地图 ×8（33 事件）」。
>    · 补记 **`5901b07` 的用户可见修复**：AUTO 行情缺口行**逐类写原因**（此前把所有不可得
>      一律写成「库内无该证券日线登记或无窗口数据」，对 2015–2016 白酒段是**错归因** ——
>      库内**有**序列，真实原因是 qfq 早年**非正价格**）。
> ⑤ **v0.26 结果**：`--check` = **FAIL 0 / WARN 0**（`--write` 前为 FAIL 11 / WARN 4 ——
>    同一次运行里「过期检测」与「不可复算」两类问题都被抓出并按流程处置）。

> ⚠️ **本节 HFQ 相关数字已由 v0.27.1 复核并取代**：v0.27 的审计脚本把 **最高价（rec[3]）**
> 当成收盘价算了全部统计（因子步进 / 仿射拟合 / 窗口收益 / qfq 非正天数）。
> **本节引用的 HFQ 数字一律作废**，以 `hfq_basis_audit_v0_2.json`（按 rec[2]=close 重算）为准；
> 定性结论（NOT_ADOPTED）经复核**仍然成立**，但理由换成更强的证据（见 v0.27.1 段）。
> ★ `>45%` 跳变实证（`jump_guard_audit_v0_1.json`）读的是数据库 `adj_close`（本来就是 close），
> **不受本次字段错误影响**。
>
> ★★ **2026-10-20（v0.27 · 行情计算方法审计 + 历史收益恢复的裁定）**：
> ① **早年高分红股（茅台 / 五粮液 / 泸州老窖）的历史收益：仍不可计算，但原因已查清并留证。**
>    `CONS-2016-BAIJIU` 的窗口起点 2016-06-01 落在 qfq **非正价格**区间
>    （茅台 2015-01-05~2016-06-29 共 363 日 · 五粮液 ~2016-06-16 共 285 日 · 泸州老窖 ~2016-10-21 共 393 日），
>    按合同 `invalid_price_series / non_positive_adj_close` **如实拒绝计算**。
>    ★ **评估了三种替代口径，全部未采用**，审计产物 `research/research/reports/hfq_basis_audit_v0_1.json`：
>    · **hfq（后复权）**：取数可得、无非正价格、跨请求区间取值稳定（锚定上市首日）；
>      **但逐日复权因子并非常数** —— 57% / 72% / 86% 的交易日的因子变化超过 0.05%
>      （舍入量级约 0.0001%，即超出 500–8600 倍），p99 达 0.38% / 0.77% / 1.90%，除权日 +1.53%；
>      且「hfq = k·raw + c」的加性模型残差**不随跨度缩小**（15 日段仍达 4.8–32.3）。
>      ⇒ 复权约定**无法从数据解释**、收益**无法由 raw + 公司行为独立核验** → **NOT_ADOPTED**。
>    · **raw（原始价）**：仅价格、不含分红 → 会把「价格涨幅」冒充「含分红收益」，明令禁止。
>    · **自建复权因子**：缺少可核验的分红/送转记录，等于自造因子 → 不采用。
>    ★ **真正缺失的东西**：一份可核验的分红 / 送转记录（除权日 + 每股派息 / 送转比例），
>    或换用**复权方法有明文文档**的数据源。拿到之前，该事件的行情状态**保持不可计算**。
> ② **`>45% 单日跳变` 守卫：全库实证完成，阈值保留、分类修正。**
>    审计产物 `research/research/reports/jump_guard_audit_v0_1.json`（确定性生成器 `audit_jump_guard_v0_1.py`）：
>    全库 adjusted 序列共 **222 次** >45% 的「跳变」，实测分布为
>    **相邻交易日 + raw 不同步 = 217 次**（provider qfq「除权价差」法的**方法学产物**，
>    价格被打到 0 附近再继续累计）· **跨记录缺口 = 5 次**（缺口 14–1095 个交易日，
>    根本不是单日变化）· **真实单日 >45% = 0 次**。
>    ⇒ **阈值没有误伤真实价格变化 → 保持 45% 不变**（放宽只会让 qfq 产物进入产物）；
>       **分类改为按证据三分**：`qfq_method_artifact` / `series_gap` / `discontinuous_series`，
>       ★ 三者**仍然拒绝计算**，数值零变化。
>    ★ 顺带查实一处真实缺陷：`LAG` 把「跨 4.3 年的两条记录」（建投能源 2017-08-31 → 2022-01-04，
>       1055 个交易日）当成「相邻日」，于是把跨四年的价格变化误读成「单日 -60% 跳变」。
>       现在 `series_gap` 只用于**给超阈值的跳变定性**，**不**否决「含缺口的窗口」
>       （圣邦股份窗口覆盖 96.5%、+802.9% 合法，未被误杀）。
> ③ **合同升 `theme_market_performance_v2`**：① 每个标的块显式声明 `price_basis`（当前只有
>    `adjusted_qfq`）；② 跳变按证据分类（见上）。★ 四个受影响产物按现有规则升版
>    （power **v0_5** · semiconductor **v0_6** · consumer **v0_3** · resource **v0_3**，
>    旧版逐字节保留），**全部数值零变化**（逐字段比对 = 0 差异）。

> ★★ **2026-10-21（v0.27.1 · HFQ 审计字段修正 + 重新裁定）**：
> ① **字段缺陷**：腾讯 `fqkline` 记录为 `[date, open, close, high, low, volume]`
>    （与 `fetch_market_batch_v0_3.row_to_dict` 一致：`rec[2]→close`、`rec[3]→high`）。
>    v0.27 的审计脚本取了 `r[3]` —— **实际是最高价**，注释却写「收盘」。
>    ⇒ 因子步进分布、仿射拟合残差、三只股票的窗口收益、qfq 非正天数**全部受影响**；
>    已改为具名常量 `F_CLOSE=2`，并加 `field_audit` 留证 + `regression_ok` 自检
>    （close 与 high 必须同日不等、且两者算出的收益必须不同，否则**拒绝生成产物**）。
> ② **按收盘价重算（`hfq_basis_audit_v0_2.json`，v0_1 逐字节保留）**：
>
>    | 项 | MOUTAI | WULIANGYE | LUZHOULAOJIAO |
>    |---|---|---|---|
>    | qfq 非正天数 / 区间 | **369** 日 · 2015-01-05~**2016-09-29** | **294** 日 · ~**2016-06-24** | **414** 日 · ~**2016-10-24** |
>    | 窗口内因子变化 | **−3.21%** | **−4.13%** | **−13.95%** |
>    | 现金分红步进（正） | +3.71% | +4.06% | +4.50% |
>    | 送转步进（负） | 0 | 0 | −1.81%（2016-07-06） |
>    | **不可解释漂移** | **−6.92%** | **−8.19%** | **−16.64%** |
>    | 窗口收益 raw（价格） | +164.41% | +166.98% | +167.86% |
>    | 窗口收益 hfq | **+155.92%** | **+155.95%** | **+130.50%** |
>    | qfq 窗口收益 | 不可算（起点非正） | 不可算 | 不可算 |
>    | 逐日因子 >0.05% 的占比 | **65.9%** | **76.7%** | **89.3%** |
>    | 仿射残差（15 日段） | 28.23 | 4.80 | 9.32 |
>
> ③ **重新裁定：仍然 `NOT_ADOPTED`**（四条准入里第 ②③④ 条不过），但理由比 v0.27 更硬：
>    · **决定性**：现金分红的因子步进是**正的**（+3.71%/+4.06%/+4.50%），窗口内因子却**净下降**
>      （−3.21%/−4.13%/−13.95%）；扣掉分红与送转后仍有 **−6.92%/−8.19%/−16.64%** 的漂移。
>      **任何标准后复权都不可能出现「一边派现金、一边因子净下降」**；
>    · **后果**：hfq 收益比 raw 价格收益还低 **8.5 / 11.0 / 37.4 个百分点** —— 含分红的序列不可能低于纯价格；
>    · 逐日因子变化在 65.9%–89.3% 的交易日超过 0.05%（舍入量级约 1e-4，超出 500–9000 倍）；
>    · 仿射模型 `hfq = k·raw + c` 的残差**不随跨度缩小**（15 日段仍 4.8–28.2）。
>    ⇒ `CONS-2016-BAIJIU` 三只标的**保持 `invalid_price_series / non_positive_adj_close` 不可计算**；
>      **不**把 hfq 或 raw 写进 `adjusted_qfq`，**不**手填任何收益。
> ④ **与 v0.27 的具体差异（v0.27 数字作废）**：hfq 窗口收益 164.47/160.03/134.91 → **155.92/155.95/130.50**；
>    因子 >0.05% 占比 57.3/72.4/86.3% → **65.9/76.7/89.3%**；仿射 15 日残差 32.27/4.77/9.46 → **28.23/4.80/9.32**；
>    qfq 非正天数 363/285/393 → **369/294/414**（用最高价会**掩盖**收盘已为负的交易日，区间端点也随之后移）。
> ⑤ **回归验证**：新增 `test_hfq_audit_uses_close_not_high` —— 断言产物 `field_used` 含 `rec[2]`、
>    每只证券 `close_ne_high` 与 `regression_ok` 为真、窗口收益等于 close→close 复算值；
>    任何一条不满足即失败（防同类字段错误复现）。契约测试 14 项全过。
> ⑥ **本轮未改**：题材产物、合同（仍 v2）、`--check` 结果、`>45%` 跳变实证、任何冻结区。

> ★★ **2026-10-21（v0.28 · 历史机会地图 → 证据地图：三维度拆分 + 角色来源核验）**：
> ① **把「一只股票的角色」拆成三条互不冒充的轴**（此前只有一个 `category` 标签，
>    把「参与过行情」「业务与机制有关」「对象登记角色」压成同一格）：
>    · `market_participation`（同期报道能证明什么）：报道涨停 **20** · 报道涨幅 **10** ·
>      报道区间涨幅 **1** · 报道点名 **32** · 未见点名报道 **85**；
>    · `mechanism_relation`（业务与题材机制的关系）：直接机制 **85** · 产业链扩散 **16** ·
>      机制未登记 **41** · 不同机制轴 **2** · 未知 **4**；
>    · `registry_role`（Research 对象内部登记 + 出处）：**库内可核 76** ·
>      仅文档登记（RC 无角色表）**12** · 未登记 **60**；
>    · `study_standing`：纳入 **142** · 反例 **2** · 证据不足 **4**。
>    产物 `research/current/participant_evidence_v0_1.json`（**148 条**参与者记录 / 33 事件），
>    生成器 `build_participant_evidence_v0_1.py`（`--check` 已接入 CI，漂移即失败）。
> ② **查出并修掉一处「角色只存在于自由文本」的缺口**：12 条参与者的角色**只写在 `rationale`
>    里**（「库内 Campaign `C-2023-POWEROP-THERMAL` 登记的标的（role=leader）」），
>    `registry_role` 字段为空 → 页面显示「对象：未登记角色」。
>    现在从文本解析出 (对象, 角色) 并**逐个与库内 `campaign_securities.role` 对齐** ——
>    12/12 全部一致（`VERIFIED_DB`），**没有一条**是仅凭文本采信。
>    ★ 同时保留两条**互不取消**的事实：`AUTO-2024-ROBOTAXI / 大众交通` 被对象登记为 `leader`
>    （按当次行情 16 个交易日 +233%），但在本题材机制轴上属**反例**（出租运营牌照方）——
>    页面同时显示两者并解释「不能用涨幅证明机制成立，也不能因反例说它没涨」。
> ③ **UI**：参与者行改为三枚独立徽标（同期 / 机制 / 对象）+ 事件级**可核对计数**
>    （报道点名 N 只 · 报道涨停 M 只 · 机制说明 X 只 · 对象登记 Y 只，库内可核 Z 只），
>    并新增两类必读说明：`登记 leader ≠ 当时公认的龙头`、
>    `未见点名报道 ≠ 当日没涨`。旧版只有单一 `category` 标签时，这三件事无法分辨。
> ④ **缺口 A 的身份层推进**（`data_gap_ticker_identity_v0_1.json`）：
>    按 **(ticker, exchange) 精确相等**（ticker 在同交易所唯一，名称相似无证明力）核验 17 个旧式标识：
>    **1 身份已确定**（`YILING-002603` → 注册表 `YILING`，owner `RC-2021-TCM`）·
>    **16 归属缺口**（ticker 在注册表中**完全不存在** → 未被任何导出对象引用，不是标识写错、更不是证券不存在）·
>    0 歧义。★ **未建立任何 Campaign 归属**；每项都写明「下一步需要什么证据」。
> ⑤ **HFQ 审计措辞收口（v0_3）**：更正 v0_2 的一处错误说明 ——
>    「qfq 非正天数不受字段影响」是**错的**：high ≥ close，用 high 会**掩盖**
>    「收盘已为负、当日最高价仍为正」的交易日（363→369 / 285→294 / 393→414 日）。
>    并把 `NOT_ADOPTED` **限定**为「本数据源 + 本样本 + 本核验条件下不适合作为已验证的替代口径」，
>    明确**不外推**到所有标准后复权方法。v0_1 / v0_2 均逐字节保留。

> ★★ **2026-10-22（v0.29 · 证据分类校正 + 历史市场角色 PIT 证据层）**：
> ① **校正 v0.28 的两处「字段非空 = 事实成立」**（产物 `participant_evidence_v0_2.json`，v0_1 保留）：
>    · **同期报道**：v0.28 把 `evidence_level=REPORT_NAMED` 一律写成「报道点名」，
>      但实测其 `source` 大量是「DB campaign_securities / 本轮研究」「export securities」——
>      **不是**同期报道。v0.29 先判**来源类型**（`REPORT_WITH_URL` / `REPORT_NAMED_NO_URL` /
>      `DB_OR_RESEARCH_ONLY` / `NOT_RECORDED`），只有前两者才允许 `REPORT_CONFIRMED_*`。
>      结果：**报道确认 28 条**（涨停 18 · 涨幅 10，全部带来源）/ **仅库内或研究记录 120 条**。
>      ★ 被降级的典型：大众交通的「16 个交易日 +233%」出处是**研究记录**（S-2024-05），
>      不是同期报道 —— 现在标 `RESEARCH_OR_DB_ONLY` 且 `reported_move_backed=false`。
>    · **业务机制**：v0.28 因 `business_mechanism` 非空就判 `DIRECT`（85 条）；
>      v0.29 改为以**研究分类**为准：`DIRECT_CONFIRMED` **56** · `INDIRECT_CONFIRMED` **16** ·
>      `BUSINESS_DESCRIBED_UNCONFIRMED` **29**（有业务说明但研究未判定机制类别）· `NOT_STUDIED` **41**。
>    · 新增 `reported_move_backed`：涨跌幅文本存在 ≠ 有报道出处，两者分开记。
>    · UI 同步：旧 `evidence_level` 徽标**不再显示**（与校正语义冲突，只留 ⓘ 原始值），
>      报道有 URL 时给出「同期报道原文」链接。
> ② **新建历史市场角色证据层**（`historical_market_roles_v0_1.json`，独立维度，不与前四轴混用）：
>    角色分 `PIT_MEDIA_NAMED_LEADER` / `PIT_MEDIA_NAMED_MOVER` / `PIT_MARKET_OBSERVED` /
>    `POSTHOC_LEADER_SET` / `INSUFFICIENT`，每条带**识别日、来源、URL、置信度、判定依据**。
>    · **33/33 事件**都有研究状态：`RESEARCHED_PIT` **1**（2024 Robotaxi）·
>      `DERIVED_FROM_REPORT` **3**（流感 2017 / 武汉 2019 / 超级真菌 2019，共 28 条角色）·
>      `NOT_RESEARCHED` **29**（逐条写明缺什么）。
>    · 角色共 **33 条**：`PIT_MEDIA_NAMED_MOVER` 32 · `PIT_MARKET_OBSERVED` 1 ·
>      ★ **`PIT_MEDIA_NAMED_LEADER` = 0** —— 库内没有任何同期材料明确称某股为「龙头」，
>      **不把「报道涨停」升格为「龙头」**。
>    · **时间前推**：Robotaxi 的 3 个切片（07-08 / 07-10 / 07-15）由「识别日 ≤ 切片日」
>      规则**重新推导**，与原始研究记录**逐条一致**（`matches_document=true`）；
>      07-08 因只有 1 只低置信盘面异动 → `NOT_USABLE`；事后集合标 `posthoc=true / pit_safe=false`
>      并写明幸存者偏差。
> ③ **查出一处真实的数据完整性缺陷**：PIT 研究 CSV 的证券 ID 与注册表**命名空间不同**——
>    `DAZHONGTONG`（大众交通）在注册表叫 `DADONGTRAFFIC`；更危险的是 CSV 的 `JINJIANG`
>    （名称写「锦江在线」）在注册表里是**锦江酒店 600754（另一家公司）**。
>    ⇒ 角色绑定**只按名称精确相等 + 本事件参与者唯一**，并标 `review=NAME_MATCH_ONLY`
>    （需人工确认）；`XINGYUYUDA` / `TIANMAI` 不在本图参与者中 → 标 `UNBOUND` 并显示
>    「未在地图参与者中」，切片同时列出 `not_in_map` 覆盖缺口。**不做 ID 硬匹配**。
> ④ **门禁**：`build_participant_evidence --check`（v2）+ 不变量 11 项、
>    `build_historical_market_roles --check` + PIT 不变量 7 项，均已接入 CI；
>    不变量测试替换了 v0.28 里「无条件成立」的断言（如 `or True`）。

> ★ **2026-10-22（v0.29.1 · 线上验收暴露的两处口径问题，已修）**：
> ① **计数行「业务机制说明」与行内状态不符**：`evidenceCounts.mechanism` 只数
>    `DIRECT_CONFIRMED` / `INDIRECT_CONFIRMED`，但标签写「业务机制说明」——
>    于是 `FLU-2017-AVIAN` 出现「业务机制说明 0 只」而每行都标着
>    `BUSINESS_DESCRIBED_UNCONFIRMED`（有业务说明、机制未定级）。
>    改为两个独立计数：**机制已确认 N 只** + **有业务说明但机制未定级 M 只**（`businessOnly`）。
> ② **两处「报道点名」口径并置会被读成矛盾**：`AUTO-2024-ROBOTAXI` 的角色节写「报道点名 4 只」，
>    而标的行计数写「同期报道点名 0 只」——两者都对：角色节来自 **PIT 研究登记的同期报道记录**
>    （带 URL 与识别日），标的行的「同期」徽标要求**该参与者自己的来源字段**就是报道
>    （其来源写的是「DB / 研究轮次」→ 只能算「仅库内/研究记录」）。
>    已加显式口径说明（`data-role-scope-note`），并加断言锁住这段说明必须存在。
> ③ 两项均有产品断言（14 项证据/角色测试通过），未改任何研究产物与数值。

### 后续待办（含 v0.26 新增）

> · ✅ **「>45% 单日跳变 = 序列错误」已完成实证（v0.27 关闭）**：全库 222 次实测 =
>   相邻日 qfq 方法学产物 **217** · 跨记录缺口 **5** · **真实单日 >45% = 0** ⇒ 阈值保留 45%，
>   分类改为 `qfq_method_artifact` / `series_gap` / `discontinuous_series`（仍拒绝计算）。
>   证据：`research/research/reports/jump_guard_audit_v0_1.json`。
> · ⛔ **早年高分红股（2016 白酒段）收益仍不可计算（v0.27 裁定，未解决）**：qfq 非正价格；
>   hfq 复权约定无法解释（逐日因子变化 57–86% 的交易日超舍入量级）→ NOT_ADOPTED。
>   需要的输入：**可核验的分红/送转记录**或**复权方法有明文文档**的数据源。
>   证据：`research/research/reports/hfq_basis_audit_v0_1.json`。

### 实测基线（2026-10-20 · 全部实测）

| 项 | 值 |
|---|---|
| **最近功能提交** | `V029_SHA`（v0.29：证据分类校正 + 历史市场角色 PIT 层）· `3b0e14f`（v0.28：地图证据三维度 + 角色来源核验 + 缺口 A 身份层）· `4e92c04`（v0.27.1：HFQ 审计字段修正 + 重新裁定）· `9a44e89`（v0.27：行情计算方法审计 —— hfq 裁定 NOT_ADOPTED · >45% 守卫全库实证 · 合同 v2）· `afd30d9`（v0.26：行情刷新到 2026-10-20 + POWER-2017 四只补齐验证 + 事实一致性修正）· `9230af2`（v0.25：行情刷新到 2026-10-19 + 25 项季节性逐项核验 v0_2 + 消费旺季 / 资源品两张新地图 + 提前观察缺因披露）· `3fcdf24`（v0.24：行情转写合同 `theme_market_performance_v1` + 题材文件漂移门禁 + 大基金三期行情落地 + 高点日扁平写法修复）· `8d3d32a`（v0.23：状态回填）· `a018f72`（v0.23：C 数据层补齐 —— 大基金三期 4 只标的行情 + 快照重生成）· `c9e4f26`（v0.23：数据缺口审计 A/B/C）· `1fc52a8`（v0.22：SA 交叉引用可导航到当前对象详情 + CANONICAL 唯一性门禁）· `9bc2c45`（v0.21 修复：窄屏长不可断串撑破题材地图容器）· `d47fd1d`（v0.21：历史事件 × 冻结 SA 精确交叉引用）· `5ae9c84`（v0.20：未关联行情行显式标注 + 草稿复制动作验收）· `5c0bce5`（v0.19：对账语义收口 + 三场景真实工作流）· `b0ca645`（v0.18：FLU-2023-H1N1 对象关联补齐 + 对账四分类）· `bcfa36c`（v0.17：行情可信展示 + 标的对账）· `0c8ee96`（v0.16：半导体/AI 算力纵切片 + 反例语义分离）· `59dedcc`（v0.15：汽车智能化纵切片）· `3edfe80`（v0.14：窗口→对象详情闭环）· `b522f02`（v0.13：线索→对照→研究请求闭环）· `8ecdb64`（v0.12：外部季节性时间轴）· `126ce8d`（v0.11：题材标的索引）· `50300f8`（v0.10：历史题材地图主入口）· `d3a01dc`（v0.9：概率层）· `05c897d`（v0.8：草稿交接 + 生命周期对照）· `f012dc3`（v0.7：草稿生命周期） |
| **最后核实 Git 状态** | 核实于 2026-10-19：本地 `main` = `origin/main`，工作区仅有 **2 个未跟踪本地库**（`market_data.db` / `cycle_research.db`，**不入库、不提交**） · ★ **本行不再写「HEAD = 某个功能提交」** —— `docs(state)` 回填提交本身会把 HEAD 前移一位，旧写法两次制造了「HEAD 滞后」的误读。**接班必须跑 `git log -1` / `git status` / `git rev-parse origin/main`** 以实际为准，不要相信文档里的固定 SHA |
| **快照** | **`MS-2026-10-13-01` = 唯一 `CANONICAL`**（实测 `index.json`：CANONICAL 计数 = 1；10-12 及更早 12 份 `ARCHIVED`，09-15 仍 `DRAFT`）· `candidates_source` = `artifact_version 0.13` / `rule_set_version structural-analogy-ruleset-v0.3`，与 SA `v0_13` **逐一相等** |
| **数据库拓扑** | `cycle_research.db` **0.96 MB**（canonical 17→14 表，**入库**） · `market_data.db` **72.85 MB**（行情三表 **395,038 行** = v0.26 补齐 **+854** 行；v0.25 时 394,184，**不入库**） · `data/market/snapshot/` **6.45 MiB**（**入库**，恢复唯一输入） |
| **trading_calendar** | **2,864 行**（2015-01-05 ~ **2026-10-20**，`calendar_type='cn'`）· 覆盖 `market_daily` **全部** distinct 日期 · **0** 个基准外日期 |
| **恢复命令** | `python research/scripts/restore_market_data.py --apply`（`--check` 校验；`--force` 重建）—— **无网络可用** |
| **快照格式** | 按年分片 `market_daily/YYYY.csv.gz` + `MANIFEST.json`（每分片 sha256）· repr() 浮点**逐位无损**（**2,053,911 个 REAL 差异 0**）· 两次生成 sha256 相同 · **395,038 行**（market_daily 单表；3 表合计 398,116） |
| **历史宇宙** | **62 Campaign + 27 Research Candidate = 89 对象** · DB `themes` **59**（13 个根） |
| **当前市场 / 提前观察（v0.26 刷新）** | `SH000300` **as_of = 2026-10-20**（收盘 4152.11 · 20 日 -7.32% · 量分位 0.183 · 波动率比 0.803 · MA20 下 · MA60 下；全页面唯一「当前」标签）· 提前观察（`research/research/reports/early_observation_v0_2.json`）：**OK 54 / PARTIAL 8 / NO_DATA 0**（62 Campaign）· PARTIAL 缺因分布：**上市/序列起始晚于 Campaign 起始 10** · 启动前不足 60 个交易日 1 · **无行情序列 2**（WUHANFANGU 无 ticker = A 的归属缺口；SWMIL = 申万指数，本抓取流程不覆盖）· L1 市场层全 62 段可算 |
| **测试** | **1448 passed / 0 failed / 76 files**（v0.29：+8 —— 历史市场角色 PIT 语义与渲染；v0.28：+7 —— 参与者证据三维度语义与渲染；v0.27：+1 —— price_basis 声明断言；v0.25：+6 —— v025UserFlows 端到端 2 · earlyObservation 缺因披露 2 · 雷达下一步入口 2；v0.24 计 1426/72，v0.23 产品未改动计数不变；v0.22：+7） |
| **Export / SA / 快照** | Contract v1.2 · SA `v0_13` · 快照 `MS-2026-10-13-01` —— 均**未随拆分/治理改动** |
| **Research 门禁** | `validate_db` PASS（4 警告，同基线）· `validate_timeline_export` PASS（0 警告）· `validate_market_snapshot` 342/8/0 · `intake --check` PASS · `refresh_downstream --check` PASS · `resolve_sa_artifact` / `validate_monorepo` / `make_market_snapshot --check` 全 exit=0 · ★ **v0.24 新增** `build_theme_market_performance --check`（合同 **v2**，v0.27）= **PASS（FAIL 0 / WARN 0）** + 契约单测 **12 passed**（在 CI 的 restore 之后运行）· ★ **v0.25 新增** `build_theme_map_v0_1.py`（消费 / 资源两张地图的确定性生成器）与 `build_external_seasonal_review_v0_2.py`（25 项核验产物生成器）—— 均**确定性**（同输入同输出） |
| **CI / 部署（当前）** | workflow `deploy.yml` = `Verify & build` + `Deploy` 两 job：Research 门禁**之前**跑 restore `--apply` + `--check`（失败即 workflow 失败，不跳门禁），随后 `npm ci` / `tsc -b` / `npm test` / build（base = `/Cycle/`）→ GitHub Pages。★ **本行不写死旧 run**（旧编号属「当时」状态，不得当作当前）—— 每次推送以 Actions 实际为准。**最近核实（v0.28）**：`3b0e14f` run [`39631075960`](https://github.com/yangfanbit/Cycle/actions/runs/39631075960) —— 两 job 均 **success**（含新增的参与者证据门禁）。历史（v0.27.1）：`4e92c04` run [`39521857909`](https://github.com/yangfanbit/Cycle/actions/runs/39521857909) —— 两 job 均 **success**。历史（v0.27）：`9a44e89` run [`39453720795`](https://github.com/yangfanbit/Cycle/actions/runs/39453720795) —— 两 job 均 **success**。历史（v0.26）：`afd30d9` run [`39427385891`](https://github.com/yangfanbit/Cycle/actions/runs/39427385891) —— 两 job 均 **success**。历史（v0.25）：`9230af2` run [`39354976253`](https://github.com/yangfanbit/Cycle/actions/runs/39354976253) —— 两 job 均 **success**（含 v0.25 新增的门禁步骤）。历史（v0.24）：`2f03db4` run [`39272571712`](https://github.com/yangfanbit/Cycle/actions/runs/39272571712) —— 两 job 均 **success**；`3fcdf24` run [`39264015668`](https://github.com/yangfanbit/Cycle/actions/runs/39264015668) · `e4c0c01` run [`39267989768`](https://github.com/yangfanbit/Cycle/actions/runs/39267989768) 均 success · ★ **门禁实证**：临时分支 `verify/v024-gate`（已删）run [`39264948321`](https://github.com/yangfanbit/Cycle/actions/runs/39264948321) —— `npm test` **success**、`--check` **failure**、build/upload **skipped**、`Deploy` **skipped**。历史（v0.23）：`c9e4f26` run [`39248636166`](https://github.com/yangfanbit/Cycle/actions/runs/39248636166) —— `Verify & build` 与 `Deploy` 两 job 均 **success**；线上 https://yangfanbit.github.io/Cycle/ 实测 **HTTP 200**。历史（v0.22）：`1fc52a8` run [`39243767285`](https://github.com/yangfanbit/Cycle/actions/runs/39243767285)（两 job success，含真实浏览器复核）· `f07d839` run [`39244995823`](https://github.com/yangfanbit/Cycle/actions/runs/39244995823)（两 job success）· v0.21：`d47fd1d` run [`39144898184`](https://github.com/yangfanbit/Cycle/actions/runs/39144898184) · `9bc2c45` run [`39145683955`](https://github.com/yangfanbit/Cycle/actions/runs/39145683955) —— 两 job 均 success |
| **历史事件地图** | **v0.10 起为首页直接入口**（索引驱动（`HistoricalThemeMaps`，索引驱动 · **8 题材 / 33 事件**（流感 6 · 电力 4 · 传媒 2 · 机器人 1 · 汽车智能化 6 · 半导体/AI 算力 7 · 消费旺季 5 · 资源品 2）· 可切换）· 跨年比较已产品化（流感 **11 季** / 电力 **10 年**）· 经验基准概率区块（分母 = `comparable === true`：电力 **7** / 流感 **9**）· v0.5 审计结论：当时 13 事件数值零计算错误 · **v0.17**：行情表带**关系类别 / 窗口状态**，参与者与标的索引带 **Research 对象对账** · **v0.18**：流感题材升 **v0_7**（`FLU-2023-H1N1` 补齐对象关联），对账拆为**四分类** · **v0.19**：再分出**独立事实**「证券注册表精确命中」（实测 **87 / 36**）· **v0.21**：事件详情带「**与当前冻结 SA 的关系**」（精确对象 ID 交叉引用；实测 18 命中 / 108 条匹配记录）· **v0.22**：SA 列表每条带「**查看当前对象详情**」（按精确 `currentObjectId` 解析，不可解析则不给按钮）· **v0.23**：三处缺口的**裁决表**（数据本身**未改**，计数不变）· **v0.24**：半导体题材升 **v0_2**（大基金三期 4 只标的行情按合同重算，`study_state` → `HAS_PRICE_DATA`；其余 6 事件百分比零变化）· 高点日扁平写法（power）修复 · **v0.25**：地图 **6 → 8**（+ 消费旺季 / 大众消费 **5 事件** · 资源品 / 黄金·稀土 **2 事件**，均从库内 Campaign 生成、窗口 = 主升段）；合同新增 `invalid_price_series`（非正价格 / >45% 跳变）守卫 · **AUTO 缺口行逐类写原因** · **v0.26**：电力升 **v0_4**（POWER-2017 四只补齐验证通过，WARN 4→0；`market_data` 陈旧文案更正）、半导体升 **v0_5**（覆盖文本随刷新更新，**数值零变化**） |
| **数据缺口审计（v0.23）** | `research/research/reports/data_gap_audit_v0_1.json`（只读 · 确定性生成）· **A 注册表未命中** = 36 条记录 / 17 标识（全流感）→ 根因 **owner-scoped 注册表**（190 == 190 零差集）· 身份**逐条**经交易所披露核验 · **1 PROVISIONAL**（`YILING-002603` → `YILING`，**不自动合并**）+ **16 UNRESOLVED**（无规范 ID 可映射）· **B 未登记对象** = 57 条 / 8 事件 → **8 UNRESOLVED**（无精确 `security_ids` 相等、事件未引用对象）· **C 大基金三期行情** = 4 只 → **已授权补齐数据层**（既有抓取流程 + 快照重生成，窗口各 44 交易日）→ **4 RESOLVED**；★ 地图转写 **UNRESOLVED**（口径不可复现）· 合计 **RESOLVED 4 / PROVISIONAL 1 / UNRESOLVED 24** · **v0.24 追加**：C 的**转写待办关闭**（`theme_market_performance_v1` 合同 + `--check` 门禁，FUND3 四只标的落地）→ 审计口径变为 **RESOLVED 5 / PROVISIONAL 1 / UNRESOLVED 23**；★ 同时新发现 **POWER-2017 4 组数值不可复算**（序列自 2022 起）→ **+4 UNVERIFIABLE**（WARN，不改数） |
| **版本** | 1.0 RELEASED（`v1.0.0` · `064d39c`）· 1.1 RELEASED（`v1.1.0`） |

### 行情转写合同（v0.24 · `theme_market_performance_v1` · 唯一口径）

> 代码即合同：`research/scripts/build_theme_market_performance.py`；产物里的
> `market_performance_contract` 是**同内容的副本**（供 Product / 人工核对）。
> 改口径 = 改版本号，**不得**只改一边。

| 项 | 定义 | 反例（不要这样做） |
|---|---|---|
| 价格序列 | `market_daily.price_type='adjusted'` 的 **`adj_close`** | 混用 raw；用 `close` 冒充前复权 |
| 窗口 | `market_performance.window = [start, end]`，`trade_date BETWEEN start AND end`（**双端包含**） | 只取 `>` / `<`；按日历天数 |
| 交易日数 | 窗口内该序列**实际行数** | 用基准交易日数代替个股（停牌会多算） |
| `high` | 窗口内 adj_close 的**最大值**（首次出现） | 用 `high` 列（日内最高）；用 Campaign `peak_date` |
| `period_return_pct` | `(last.close / first.close − 1) × 100` | 用窗口外首日 |
| `to_high_pct` | `(high.close / first.close − 1) × 100` | 用 `peak_date` 的收盘 |
| `max_drawdown_from_high_pct` | ★★ `min over t ≥ high.date of (close_t / high.close − 1) × 100`（**自至高点之后**） | **全窗口**最大回撤（v0.23 的误判来源） |
| 超额 | `excess_period_pp` = 区间 − 基准区间；`excess_to_high_pp` = 至高点 − 基准至高点（**两列不同口径**） | 把两列混用；用「相对收益」代替 |
| 舍入 | 百分比 **1 位小数**（Python `round`）；超额由**已舍入**的两数相减 | 用 3 位小数冒充精度 |
| 缺失 | `< 2` 行 → `{"error":"insufficient_data_in_window","reason":...}`（`no_series` / `no_rows_in_window` / `single_row`） | 补 0；借相邻日期；用「上一次收盘」延展 |

**命令**（都在仓库根执行）：

```bash
python research/scripts/restore_market_data.py --apply          # 干净克隆先恢复行情库
python research/scripts/build_theme_market_performance.py --check        # 只读校验（CI 门禁）
python research/scripts/build_theme_market_performance.py --write SEMICONDUCTOR_AI   # 升版（不覆盖）
python research/scripts/test_build_theme_market_performance.py           # 契约单测（12 项）
```

**校验分级**（`--check` 的语义，必须分清）：

| 级别 | 触发条件 | 处置 |
|---|---|---|
| **FAIL** | 库内**可算**但产物写 `error`（**旧缺失状态过期**）；或数值 / 日期 / 交易日 / 超额超出容差；或 `study_state` 与现算不符；或 `[AUTO:MARKET_DATA]` 行与覆盖不符 | 非零退出，**阻止部署**；按合同 `--write` 重生成，**不手改数值** |
| **WARN · UNVERIFIABLE** | 库内**不覆盖**该窗口（无行），而产物有数值 | **不改数、不删数**；如实计入汇总，等补行情 |
| **WARN** | 事件未登记 `window` | 跳过，不猜 |

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

### v0.18 批次（补齐明确对象关联 + 对账四分类）

> ★ 只读 + **版本化新增**：不覆盖旧轮次、不改 canonical export / 冻结 SA / CANONICAL 快照；无网络、无 LLM 运行时、未训练模型。
> 依据（原任务书）：`objectReconciliation` 把「事件没记录对象 ID」与「对象 ID 已有但无法解析」
> 都归入 `UNRESOLVED` → 汇总容易把**缺字段**误读成**对象解析失败**。

#### ① ★★ 补齐已有明确证据的对象关联（任务 A）

| # | 事件 | 处理 | 依据 |
|---|---|---|---|
| 1 | `FLU-2023-H1N1` | ✅ 补 `campaign_facts → object_id = C-2023-PHARMA-FLU`（`object_kind = campaign`） | `evidence_basis` **明确引用**该 Campaign；3 只标的（HUALANVAX / BAIKEBIO / JINDIKE）与对象 `security_ids` **逐一相等**；行情窗口匹配 |
| 2 | `FLU-2024-SEASONAL` | ⛔ 不补 | `evidence_basis` = 「官方监测 / 发布会 + 同期市场报道」，**无**对象引用；虽有 3 只标的与上面重合，但**股票重合不足以指定** Campaign |
| 3 | `FLU-2017-AVIAN` / `FLU-2018-SEASONAL` / `PUBLICHEALTH-2019-WUHAN` / `SUPERFUNGUS-2019-CANDIDA` | ⛔ 不补 | 依据均为**同期报道**，**无**库内对象引用 |
| 4 | 电力 `POWER-2017/2022/2024-*-SUMMER` | ⛔ 不补 | 季节性观察窗口**不必然**对应一个正式 Campaign；**无**对象引用证据 → 保留未登记 |
| — | 电力 `POWER-2023-SUMMER` | 既有（v0_3 已带 `C-2023-POWEROP-THERMAL`，**未改动**） | 既有 |

- 新增版本化文件 `research/current/flu_historical_events_v0_7.json`（**保留** v0_1~v0_6 逐字节；
  `supersedes` = v0_6；`corrections` 留痕）。**只**改 `FLU-2023-H1N1.campaign_facts` —— 事件 / 行情 / 跨年份**数值零变化**。
- 流感通用地图导入升 v0_7；索引 `maps[FLU].file` → v0_7（索引 `artifact_version` 0.3 → 0.4）。

#### ② ★★ 对账四分类（最小修正）

| 状态 | 含义 |
|---|---|
| `OBJECT_REGISTERED` | 证券在关联对象的 `security_ids` 中 |
| `MAP_SUPPLEMENT` | 证券在全局注册表、但不在关联对象 `security_ids` 中 |
| `NO_OBJECT_REFERENCE` | **事件未记录关联对象** → 当前无法做对象级对账（★ 不暗示证券不存在、不自动判定归属） |
| `UNRESOLVED` | **已提供**对象引用但对象无法解析，**或**证券注册信息缺失 |

- 统一更新：事件详情汇总（`EventCardBody`）· 参与者行徽标（`ParticipantRow`）· 标的索引逐次记录（`OccurrenceRow`）+ 头部汇总。

**★ 更新后的对账分类数量（六题材，123 条参与记录）**：

| 题材 | 事件 | 参与记录 | 已登记关联 | 地图补充 | 未登记对象关联 | 无法核对 |
|---|---|---|---|---|---|---|
| 流感 FLU | 6 | 42 | **3** | 0 | **39** | 0 |
| 电力 POWER_SUMMER | 4 | 21 | 3 | 0 | 18 | 0 |
| 文化传媒 MEDIA | 2 | 4 | 4 | 0 | 0 | 0 |
| 机器人 ROBOTICS | 1 | 5 | 5 | 0 | 0 | 0 |
| 汽车智能化 AUTO_INTELLIGENCE | 6 | 22 | 22 | 0 | 0 | 0 |
| 半导体/AI 算力 SEMICONDUCTOR_AI | 7 | 29 | 29 | 0 | 0 | 0 |
| **合计** | **26** | **123** | **66** | **0** | **57** | **0** |

> ★ v0.17 → v0.18 变化：**已登记 63 → 66**（`FLU-2023-H1N1` 3 条）；**无法核对 60 → 0**
> —— 其中 57 条为「**未登记对象关联**」（流感 39 + 电力 18），另 3 条随补齐转为已登记。
> ★ 「无法核对 0」**不是**把缺口藏起来：57 条**明确标注「未登记对象关联」**，逐条保留原因，**不**自动判定其应属某个 Campaign。

#### ③ 验证（全部实测）

```
npx tsc -b OK · npm run build 成功 · npm test 1386 passed / 0 failed / 68 files
新增/更新：objectReconciliation 15（FLU 补齐生效 / 未登记 vs 无法核对区分 / 四分类文案 / 全局锚点 66·0·57·0）
          HistoricalEventMap +1（FLU-2023-H1N1 对象关联补齐）+ D 区版本断言 0.6 → 0.7
```

★ 环境限制（如实说明）：本机无 Node/Chrome —— 由**便携 Node v22.23.3** 跑通，**未做浏览器截图 / 窄屏视觉核验**。

### v0.19 批次（对账语义收口 + 三场景真实工作流）

> ★ 不改冻结产物：未动 canonical export / SA / TO / Driver / `schema.sql` / 行情快照；
> 未扩题材或股票池；**不**自动合并证券 ID、**不**按名称 / 日期 / 题材推断对象归属。

#### ① ★★ 对账语义收口：两个**独立事实**分开呈现

| 事实 | 含义 | 呈现位置 |
|---|---|---|
| ① 对象关联状态（四分类，**语义不变**） | `OBJECT_REGISTERED` / `MAP_SUPPLEMENT` / `NO_OBJECT_REFERENCE` / `UNRESOLVED` | 参与者行徽标 · 事件详情汇总 · 标的索引 |
| ② **证券注册表精确命中**（v0.19 新分出） | 该 `security_id` 是否在 canonical export `securities` 中**精确命中** | 未命中时单独标「证券注册表：未命中」+ 事件级 / 题材级计数 |

- ★★ **不新增第五类**，也**不**让二者互相推导：`NO_OBJECT_REFERENCE` 时，注册表命中**仍照常判定**并返回。
- ★ 未命中的语义（`REGISTRY_MISS_CAVEAT`）：「只是需核对的**标识差异** ≠ 证券不存在 ≠ 可自动匹配其它 ID」
  （例：地图 `YILING-002603` ↔ export `YILING`，**代码相同、标识不同**）。
- 修正陈旧描述：`reconciliationOf` 的 JSDoc 曾写「无对象引用 → `UNRESOLVED`」→ 改为 `NO_OBJECT_REFERENCE`。

**★ 真实数据派生（六题材，123 条参与记录）**：

| 项 | 数量 |
|---|---|
| 证券注册表**精确命中** | **87** |
| 证券注册表**未命中**（需核对的标识差异） | **36**（**全部**在流感 v0_7 的旧式标识） |
| 对象关联四分类 | 已登记 **66** / 地图补充 0 / 未登记对象关联 **57** / 无法核对 **0**（**与 v0.18 一致，未变**） |

> ★ 各题材命中（命中/未命中）：流感 6/36 · 电力 21/0 · 传媒 4/0 · 机器人 5/0 · 汽车 22/0 · 半导体 29/0。

#### ② ★★ 三场景真实工作流（页面级 jsdom + 真实数据接线）

| 场景 | verdict（实测） | 走通情况 | 修复的实际阻塞 |
|---|---|---|---|
| **汽车智能化** | `both`（历史案例数 > 当前对象数，**计数在块标题可见** → 不误称「覆盖充分」） | ✅ 方向查询 → 两侧命中与边界 → 历史题材地图事件 / 标的 / 纳入理由 → 对象详情 → 草稿带方向 + 研究问题 + 时间范围 + 冻结证据 | — |
| **医药** | `both` | ✅ 两侧**独立成块**不混为一条 → 详情（生命周期）→ 草稿保留用户输入与查询证据 | — |
| **文化传媒** | `historical-only`（当前侧空） | ✅ 明确「当前侧没有研究对象」而非故障 → 历史事件 / 标的可看 → 草稿仍可建立 → JSON / MD 导出分开「用户输入（§1–5）」与「系统命中（§6）」 | — |
| **全站渲染** | — | ✅ 催化时间线 | ★ **修复**：同日同前缀催化产生 **React 重复 key**（MEDIA 事件实测触发警告 → 子节点可能被复制 / 丢项）→ 改「日期 + 序号」 |

#### ③ 验证（全部实测）

```
npx tsc -b OK · npm run build 成功 · npm test 1396 passed / 0 failed / 69 files
新增：objectReconciliation D 5（全局 87/36 · 各题材明细 · 「无对象引用且未命中」边界 · 「已登记且命中」边界 · registryStatusOf）
      v019UserFlows 5（汽车 2 · 医药 1 · 文化传媒 2；真实数据 + 真实 DOM 点击 + 导出载荷核对）
```

★ 视口说明（v0.20 更正）：v0.19 批次当时**未做**浏览器复核；自 **v0.20** 起已恢复
（本机**有 Edge / Safari**）—— 见下方 v0.20 批次 ④「浏览器实机复核」。当时以页面级真实 DOM 点击为准，**不**因此停工。

### v0.20 批次（未关联行情行显式标注 + 草稿复制动作验收）

> ★ 不改冻结产物：未动 canonical export / SA / TO / Driver / `schema.sql` / 行情快照；未新增题材；
> **不**自动合并证券 ID、**不**为了消除展示差异改写 Research 数据。

#### ① ★★ 未关联行情行不再只给裸 ID

| 问题 | 修法 |
|---|---|
| 行情表里某些行**只显示裸 ID + 关系类别「—」**，用户看不出它是谁、也没解释 | 行情键在本事件 `participants` 中找不到**同一精确 ID** 时 → 标「**行情记录未关联事件参与者**」+ 琥珀虚线左边框 |
| 「有行情记录」容易被读成「该证券被本事件纳入」 | 行内说明 + 表内声明（`data-perf-unlinked-caveat`）：「**行情记录存在 ≠ 事件参与者记录存在**」；**不**代表该证券已被本事件确认纳入 |
| 裸 ID 无从辨认 | 名称 / 代码只取自**同一精确 ID** 的 canonical export 注册表（新增 `registeredSecurityOf`）；查不到就**不填**，**绝不**跨 ID 推断；**原始 ID 一并保留显示** |
| 数值与覆盖状态 | **原样不动**（原始 ID、行情数值、覆盖状态全部保留） |

**★ 实测（v0.20 数据核查）**：六题材 26 事件中，`by_security` 键 **120** 条、参与者 **123** 条；
**3 条**行情键在本事件参与者里无同 ID —— **全部为 `YILING`**：

| 事件 | 行情键 | 展示 |
|---|---|---|
| `FLU-2018-SEASONAL` | `YILING` | 以岭药业 / 002603 / 原值 区间 **-11.9%**（103 交易日） |
| `PUBLICHEALTH-2019-WUHAN` | `YILING` | 以岭药业 / 002603 / 原值 区间 **+69.9%**（28 交易日） |
| `FLU-2024-SEASONAL` | `YILING` | 以岭药业 / 002603 / 原值不变 |

> ★★ `PUBLICHEALTH-2019-WUHAN` 另有参与者 `YILING-002603`（另有其参与者条目与「该窗口未计算」状态）——
> **两者是两回事**：行情键 `YILING` **不会**变成参与者 `YILING-002603`，**不自动合并**（代码相同、标识不同）。

**★ 反向核查**：**6 条**参与者在本事件无同 ID 行情键
（`PUBLICHEALTH-2019-WUHAN:YILING-002603` · `MEDIA-2018-GAMELICENSE:GIANTNET / SANQI` ·
`ROBOTICS-2023-HUMANOID:KINCO / LEADERDRIVE / LEADSHINE`）—— 逐条**如实显示 `该窗口未计算`**（`NOT_COMPUTED`），
**不补 0、不伪造**；经审查**展示准确**，故**未做修改**。

#### ② ★★ 草稿复制动作验收（v0.20 新增）

- 注入可捕获剪贴板（`currentClipboardEnv()` 读 `navigator.clipboard`）→ 在**文化传媒仅历史**场景填研究问题 + 时间范围：
  - 「复制 JSON」「复制 Markdown」**捕获内容 = 预览内容**（逐字节相等）；
  - 复制内容里**用户输入**（`request.*`）与**系统命中**（`coverage_check.*`）仍分开；
  - 失败路径（权限被拒 `NotAllowedError`）**不虚报成功**（无「已复制」），并给出下一步（手动选中复制）。
- ★ 产品仍是**复制 JSON / Markdown**（未改成文件下载）。

#### ③ 验证（全部实测）

```
npx tsc -b OK · npm run build 成功 · npm test 1405 passed / 0 failed / 69 files（+9）
新增：HistoricalEventMap F3 5（三个 YILING 行文案 / 不自动合并 / 原值不变 / 正常行四要素 / 无键参与者不补 0）
      objectReconciliation E 2（全题材不匹配 3 条与 6 条，逐条列事件 ID）
      v019UserFlows +2（复制内容 = 预览内容、用户输入与系统命中分开；失败不虚报）
```

#### ④ ★★ 浏览器实机复核（v0.20 起恢复，不再以「无浏览器」为由跳过）

线上 https://yangfanbit.github.io/Cycle/ 用**真实浏览器**复核（截图留证）：

- 首页「历史题材地图」→ **流感** tab → 展开 `PUBLICHEALTH-2019-WUHAN`；
- **实测行情表**中 `data-security-id="YILING"` 行：标的格显示 **以岭药业 / 002603 / YILING**，
  关系类别格显示「**行情记录未关联事件参与者**」（琥珀虚线），窗口状态「完整窗口已计算」，区间涨跌 **+69.9% 原值不变**；
- 相邻 `LUKANG-600789` 行仍为 **历史市场参与者** + **完整窗口已计算**（正常行四要素齐全）；
- 事件详情「与 Research 对象的标的对账」块显示：已登记 0 / 地图补充 0 / 未登记对象关联 10 / 无法核对 0，
  且**证券注册表：精确命中 0 · 未命中 10**（与该事件参与者全为旧式标识一致）；
- **浏览器控制台无错误**；「查一个方向」区域与输入框正常渲染。

> ★ 说明：本机**有 Edge / Safari**，此前文档中「本机无浏览器」的表述**不成立**，已在本批更正为
> 「**部署后必须用浏览器实机复核**」（截图证据见会话记录）。

### v0.21 批次（历史事件 × 冻结 SA 交叉引用 + 窄屏实机验收）

> ★ 不改冻结产物：未动 canonical export / SA / TO / Driver / 历史快照 / `schema.sql` / 行情快照；
> 未新增题材；**不**自动合并证券 ID；**不**产生新的结构状态或评分。

#### ① ★★ 历史事件 × 冻结 SA 的**精确交叉引用**

| 项 | 做法 |
|---|---|
| 数据来源 | **唯一** `CANONICAL` 快照 `MS-2026-10-13-01` 的 `historical_candidates`（`current_object_id` / `identity` / `structural_status`）+ 同快照 `research_objects`（当前对象显示名 / 大主题） |
| 匹配 | 事件侧 `campaign_facts.object_id`（兼容 `campaign_id`）；SA 侧 `identity.historical_campaign_id` **或** `identity.historical_research_candidate_id` —— **完全相等**才匹配 |
| 不做什么 | **不**重算 SA、**不**按主题名/年份/名称相似度推测、**不**新增状态 |
| 展示 | 事件详情「**与当前冻结 SA 的关系**」块：匹配 → 列出引用它的当前研究对象 + **既有** `structural_status`；未匹配 → 「**当前冻结 SA 快照未找到该历史对象的对应记录**」（≠ 不存在结构对应、≠ 已否决）；事件未记录对象 → 明确「无法进行对象级交叉引用」；快照未载入 → 「**无法判定**」（≠ 未找到） |
| 硬边界 | 对象级 `structural_status` 是**对象之间**的判定，**不是**对某只股票的确认 —— 与证券注册表 / 四分类对账**分开呈现、不得混为一谈** |

**★ 精确交叉核对（真实文件计算，非预填）**：

| 项 | 数量 |
|---|---|
| 事件总数 | **26** |
| 有明确对象引用的事件 | **18** |
| 在冻结 SA 快照中**找到**对应历史对象的事件 | **18** |
| **未找到**对应历史对象的事件 | **0** |
| 另有**未记录对象**的事件（对象级交叉引用不适用） | **8** |
| 匹配后的 SA 记录数（18 × 6 当前对象） | **108** |

**★ 匹配记录按既有 `structural_status` 汇总**：`STRUCTURAL_SUPPORTED` **4** ·
`STRUCTURAL_PARTIAL` **9** · `NO_VALID_CORRESPONDENCE` **56** · `INSUFFICIENT_EVIDENCE` **36** · `THEME_ONLY` **3**。

#### ② ★★ 窄屏 / 实机验收（真实浏览器，非 jsdom）

> ★★ 工具限制（**如实**）：所用浏览器工具**无法模拟**要求的目标视口
> （1366×768 / 768×1024 / 390×844 / 320×700）—— **实际视口 677×662**；
> 也未按 Edge / Safari 分别验收（工具是单一内置浏览器）。故本轮为**单浏览器 × 677×662**
> 的真实渲染验收；窄于 720px 断点，属有效窄屏证据，但**不等于**四个目标视口已逐一验收。

| 检查 | 结果 |
|---|---|
| 流感 tab 切换 + 展开 `PUBLICHEALTH-2019-WUHAN` | ✅（真实 DOM 点击） |
| `data-security-id="YILING"` 行显示「行情记录未关联事件参与者」 | ✅ |
| 历史参与标的索引（`tsi-table`）渲染、无裁剪/重叠 | ✅ |
| 行情表容器 `fem-table-wrap` 存在且 `clientWidth == scrollWidth`（578 ≈ 可视宽） | ✅（该视口下表格未溢宽，无需滚动） |
| 控制台错误 / 失败请求 | 仅 `@vite/client` 404（静态部署无害），**无其它错误** |

★★ **实测发现并修复的一处真实布局缺陷**：

| 阶段 | 数值（677px 视口） |
|---|---|
| **修复前** | `documentElement.scrollWidth` **904** > `clientWidth` **662**；`.htm-panel` 876 vs 604；`.app-main` 905 vs 662 → **整页横向溢出** |
| 根因 | 题材地图里的**长不可断串**（催化来源 URL / 长 id）不换行，撑宽 `.htm-panel` |
| 修法 | `.htm { overflow-wrap: anywhere; }`（继承属性，覆盖其下文本块；`anywhere` 参与 min-content 计算 → 容器可收缩）。**未**把宽表改成卡片，全部宽表仍在 `fem-table-wrap`（`overflow-x:auto`）内 |
| **修复后（真实浏览器复测）** | `documentElement` clientWidth 662 / scrollWidth **662**；`body` 662/662；`.htm-panel` 604/604；`.app-main` 662/662 → **整页溢出已消除**（`.seasonal-scroll` 638/720 为其**自身**设计内的横向滚动） |

#### ③ 验证（全部实测）

```
npx tsc -b OK · npm run build 成功 · npm test 1415 passed / 0 failed / 71 files（+10）
新增：saCrossReference 8（索引 89×6=534 · 事件侧 18/18/0 + 108 · 状态汇总 · RC 类型 · 旧字段兼容 · 未匹配 · 空索引）
      v021UserFlows 2（页面级：半导体命中列出 6 个当前对象；流感未记录对象说明）
```

### v0.22 批次（SA 交叉引用可导航 + CANONICAL 唯一性门禁）（2026-10-19）

> ★ 不改冻结产物：未动 canonical export / SA / TO / Driver / 历史快照 / `schema.sql` / 行情快照；
> 未新增题材；**不**自动合并证券 ID；**不**产生新的结构状态或评分；**不**新增第七个题材。

#### ① ★★ SA 交叉引用 → **当前研究对象**详情（导航闭环）

| 项 | 做法 |
|---|---|
| 入口 | 事件详情「与当前冻结 SA 的关系」列表，**每条**新增「**查看当前对象详情**」 |
| 接线 | `App` → `HistoricalThemeMaps` → `HistoricalEventMap` → `EventCard` → `EventCardBody`（callback `onOpenCurrentObject` / `canOpenCurrentObject`） |
| 导航 | 接入 App **既有** `focusObject` / CurrentTimeLens 流程（展开 `#drill-current-time-lens` 并就地展开该候选），**不**新建第二套详情面板 |
| 语义边界 | **不**复用历史对象的 `openHistoricalObject` —— **当前研究对象**（`CC-*`）与**历史对象**（Campaign / RC）是**两种对象类型**，各走各的既有流程 |
| 可解析判定 | 操作对象 = SA 记录里的 `currentObjectId`，按**精确 ID** 经 `canOpenCurrentObject`（canonical `current_candidates.json` 的 `CC-*`）确认；**解析不了 → 不渲染按钮**，保留 ID / 名称 / 状态并说明「无法通过现有详情流程解析」 |
| 不做什么 | **不**改 SA 判定、**不**新增结构状态、**不**把对象级结果说成个股确认；不改 SA / TO / Driver artifact / 快照 / export |

实测（真实数据）：6 行当前研究对象 × 6（每行一个按钮，全部可解析），**`CC-*` 精确 ID 与 `current_candidates.json` 逐一相等**。

#### ② ★★ CANONICAL 唯一性门禁（修复静默选最新）

| 项 | 做法 |
|---|---|
| 原缺陷 | `loadSaCrossReference()` 对 CANONICAL 条目排序后**取最后一项** —— 索引若意外出现两个 CANONICAL 会**静默选最新**，把未察觉的索引异常当成正常结果 |
| 修法 | 抽出**可测试纯函数** `pickCanonicalSnapshot(entries)`：**0 个 → `ok=false` 披露「无法判定」**（≠「未找到」）· **恰好 1 个 → `ok=true`**（调用方仍**二次确认**快照自身 `status`）· **多于 1 个 → `ok=false` 拒绝选择并披露**索引违反「唯一 CANONICAL」预期（列出全部 id） |
| 披露 | 载入失败原因（`loadError`）在事件详情 SA 块**清楚呈现**（`data-sa-load-error`），不静默 |
| 不做什么 | **不**改动真实冻结索引 / 快照文件（测试用**合成数组**覆盖 0 / 1 / 多） |

#### ③ ★★ 回归测试与真实工作流

```
npx tsc -b OK · npm run build 成功 · npm test 1422 passed / 0 failed / 72 files（+7）
新增/扩展：
  saCrossReference +4（pickCanonicalSnapshot 合成 0 / 1 / 多 + 真实索引恰好 1 个）
  v022UserFlows 3（页面级真实 App：
    ① 点击 SA 里真实 CC-* → 经既有流程定位到该当前对象（恰好一个候选展开）及其结构对应详情；
    ② 历史对象既有导航（查看对象详情 → CampaignDetail）不受影响；
    ③ 注入合成索引：不可解析当前对象 ID → 无按钮、保留 ID / 名称 / 状态 + 说明）
不变：原 108 条交叉引用与状态汇总（SUPPORTED 4 / PARTIAL 9 / NO_VALID 56 / INSUFFICIENT 36 / THEME_ONLY 3）；
      SA 对象级状态与「证券注册表 / 四分类对账」仍是**两个独立事实**
```

**★★ 真实浏览器复测线上 Pages（非 jsdom）**：

| 检查 | 结果 |
|---|---|
| 首次加载（未绕缓存）主脚本 = 旧产物 `index-CVj0HTbJ.js` | SA 列表**无**按钮（属**缓存旧页**，非新代码缺陷） |
| 缓存绕过 `?v=nocache1` 后主脚本 = 新产物 `index-D-pPNoxU.js` | SA 列表 6 行 × **6 个**「查看当前对象详情」按钮（`[data-sa-open="current-object"]`=6，`unresolved`=0） |
| 点击第一条（`CC-2026-AUTO-SMARTDRIVE`） | 页面定位到「当前时间研究导航（Current Time Lens）」；**恰好一个**当前候选展开，含「Structural Analogy（结构对应 · 当前 → 历史）」与当前研究对象名「智能驾驶合规化（L3/L4 强制国标—责任划分—量产准入）」→ **闭环走通** |
| 控制台错误 | 无（首次缓存加载时见 `@vite/client` ERR_ABORTED，静态部署无害） |
| 实际视口 | **1085 × 750**（工具**无法模拟**目标视口 1366×768 / 768×1024 / 390×844 / 320×700；也未按 Edge / Safari 分别验收 —— **如实记录**） |
| 整页横向溢出 | 该视口下 **无** 整页横向溢出（内容宽 1070 ≤ 视口 1085）；★ **窄屏（~677px）**未在本轮复测（工具无法设视口），v0.21 的 `.htm { overflow-wrap: anywhere; }` 仍在，本轮仅新增 flex-wrap 行内按钮 |

### v0.23 批次（数据缺口审计 · 只读裁决表）（2026-10-19）

> ★★ 本轮**性质是「核验 + 建裁决表」，不是「改数据」** —— A/B/C 三处缺口的**前后计数完全相同**。
> ★ 未改 canonical export / SA / TO / Driver / `schema.sql` / 历史快照 / `market_data.db` 与便携快照（逐字节未动）；
> 未新增题材、未改 SA 判定、未推断逐证券结构对应；**不**做买卖信号 / 选股 / 预测。

**产物与生成器**：

| 项 | 值 |
|---|---|
| 产物 | `research/research/reports/data_gap_audit_v0_1.json`（`artifact=data_gap_audit` · `artifact_version=0.1`） |
| 生成器 | `research/scripts/build_data_gap_audit_v0_1.py`（**确定性**：连跑两次 sha1 相同 `8ddf599e…`；**只读**；自检：未命中标识缺权威来源 / 标识后缀与 ticker 不一致 → **FAIL 退出**） |
| 数据来源 | `cycle_research.db :: securities`（既有原始记录）· `exports/timeline_export_v1.json` · `historical_event_maps_index.json` 指到的 **ACTIVE** 题材版本 · `market_data.db`（`market_series` / `market_daily` 实测量程） |

#### ① A · 证券注册表未命中（36 条记录 / 17 个不同标识）

| 项 | 实测 |
|---|---|
| 记录行数 / 不同标识 | **36 / 17**（全部在流感题材；单标识最多 3 行：`DAAN-002030` · `HAIWANG-000078` · `HUALAN-002007` · `LIANHUAN-600513` · `LUKANG-600789` · `NEPHARM-000597` · `TIANKA-002100` · `XIANGXUE-300147`） |
| **根本原因** | canonical export 的 `securities` 注册表是 **owner-scoped**（合同 §8「扁平数组，必须知道属于谁」）。**实测零差集**：注册表 **190** 条 == 各 owner（Campaign / RC）`security_ids` **并集 190** 条。17 个标识**全部存在于** DB `securities` 原始记录（含 ticker / 交易所），但**未被任何导出对象引用** ⇒ 必然落在注册表外 |
| 身份核验 | 17 个**逐条**经交易所披露核验：`股票简称 / 股票代码 / 交易所` 与 DB 记录**一致**；标识后缀 == DB ticker（脚本自检 **17/17 通过**）。来源为**深交所/上交所年报摘要或上市交易通知**（URL + 发布日期入表，如 `DAAN-002030` 2026-04-28 年报摘要、`HUALAN-002007` 2004-06-18 上市交易通知、`LIANHUAN-600513` 2026-04-21 上交所年报） |
| 分类 | **PROVISIONAL ×1**：`YILING-002603` → `YILING` —— DB 内存在**同 ticker(002603) + 同名称(以岭药业)** 的**重复标识**，且 `YILING` **在**注册表内（owner = `RC-2021-TCM`）⇒ **提出映射**。★ 依硬约束**不自动合并**（`YILING` ≠ `YILING-002603`）—— 落库合并须单独 Research 轮次裁定 |
| 分类 | **UNRESOLVED ×16**：身份已确认，但 DB 内**没有**可映射的规范 ID（既无声称的同名同 ticker 其它标识，也无它们在 export 注册表中的身影）⇒ 缺口性质是 **ownership / 覆盖缺口**，**不是**标识错误。关闭它须由 Research 轮次按证据决定「该证券是否归属于某个对象」 |
| 前后计数 | 36 / 17 → **36 / 17（未变）** |

#### ② B · 未登记对象关联（57 条记录 / 8 个事件）

| 事件 | 题材 | 参与者记录 | 文本引用对象 | 精确 `security_ids` 相等的对象 |
|---|---|---|---|---|
| `FLU-2017-AVIAN` | FLU | 10 | 无 | 无 |
| `FLU-2018-SEASONAL` | FLU | 4 | 无 | 无 |
| `FLU-2024-SEASONAL` | FLU | 7 | 无 | 无（与 `C-2023-PHARMA-FLU` 仅 **3/3** 重叠但其参与者共 7 只，**不相等**） |
| `PUBLICHEALTH-2019-WUHAN` | FLU | 10 | 无 | 无 |
| `SUPERFUNGUS-2019-CANDIDA` | FLU | 8 | 无 | 无 |
| `POWER-2017-SUMMER-COUNTEREXAMPLE` | POWER_SUMMER | 6 | 无 | 无（与 `C-2021-POWER-GREEN` / `C-2023-POWEROP-THERMAL` 各 **3/3** 重叠，**不相等**） |
| `POWER-2022-SUMMER` | POWER_SUMMER | 6 | 无 | 无 |
| `POWER-2024-SUMMER-COUNTEREXAMPLE` | POWER_SUMMER | 6 | 无 | 无 |

- 证据标准沿用 **v0.18**：只有 `evidence_basis` **明确引用**某对象**且**标的集合与该对象 `security_ids` **逐一相等**才补关联。
- 结果：**UNRESOLVED ×8（0 新补）** —— 事件文本**未引用**任何 Campaign / RC id，精确相等者**为零**
  ⇒ **不得**按主题相近或年份相近认定属于同一 Campaign。
- 前后计数：57 / 8 → **57 / 8（未变）**。

#### ③ C · 大基金三期窗口（2024-09-24 ~ 2024-11-29）4 只缺价标的 —— **数据层已补齐**

| 标的 | ticker | 补齐前根因 | 补齐前量程 | 补齐后量程 | 窗口内（adjusted） |
|---|---|---|---|---|---|
| SMIC 中芯国际 | 688981 | `FETCH_COVERAGE_GAP` | 2020-07-16 → 2021-09-30 | 2020-07-16 → **2025-12-31** | **44** |
| AMEC 中微公司 | 688012 | `FETCH_COVERAGE_GAP` | 2019-07-22 → 2021-09-30 | 2019-07-22 → **2025-12-18** | **44** |
| HYGON 海光信息 | 688041 | `FETCH_COVERAGE_GAP` | 2022-08-12 → 2022-10-12 | 2022-08-12 → **2025-12-31** | **44** |
| PIOTECH 拓荆科技 | 688072 | `SERIES_NOT_REGISTERED` | —（无序列） | **2022-04-20** → 2025-12-31 | **44** |

**补齐动作（用户授权后 · 全部走既有流程）**：

| 项 | 值 |
|---|---|
| 抓取器 | `research/scripts/fetch_market_batch_v0_3.py`（**既有权威抓取器**，未新建抓取代码） |
| 命令 | `--only SMIC,AMEC,HYGON,PIOTECH --series SMIC@2016-01-01~2025-12-31,AMEC@…,HYGON@…,PIOTECH@2022-01-01~2025-12-31` |
| 来源 | `tencent_gtimg`（项目既有抓取流程所用源），每行记 `price_type`（raw / adjusted-qfq 两套）、`data_source`、`retrieved_at` |
| 取回 | AMEC raw/qfq **1557/1557** · HYGON **812/812** · PIOTECH **900/900** · SMIC **1321/1321** |
| 序列登记 | 拓荆科技**补登** `market_series`（provider=tencent / symbol=sh688072）—— 原无登记 |
| 历史保护 | ★ 逐 `(trade_date, price_type)` 与补齐前备份比对：SMIC/AMEC/HYGON **既有行 0 变更 / 0 丢失**（`INSERT OR REPLACE` 幂等，且实测 qfq **未重算**） |
| 快照 | `make_market_snapshot.py` 重生成 → `market_daily` **376,401 → 380,771 行** · `market_series` **213 → 214** · 快照 **6.09 → 6.22 MiB**；`restore_market_data.py --check` **PASS**（逐分片哈希一致 + REAL 逐位相同） |
| 溯源 | `research/research/reports/market_fetch_v0_3_report.json`（本次 4 只的 symbol / 区间 / 行数）+ 审计产物 `C.backfill` |
| 分类 | **数据层 4 RESOLVED** |

**★★ 仍未解决（与数据层分开记录）**：**地图展示未刷新** —— 题材文档（`semiconductor_ai_compute_historical_events_v0_1.json`）的 `market_data` 文本与 `by_security` 仍是「不覆盖」状态。**本轮不刷新**，且**未手工改任何展示值**：实测 **12 份题材文档的 `max_drawdown_from_high_pct` 等口径互相不一致**（逐一用两组候选公式验算，**仅 3/12 份可完全复现**），任何单一公式都会**编造**数字 ⇒ 须由**独立、可复现的转写流程**（新轮次）统一口径后再生效。

#### ④ 本轮合计与验证

```
RESOLVED 4（C 数据层）· PROVISIONAL 1（A 的 YILING-002603 → YILING 提案）· UNRESOLVED 24（A:16 + B:8）
+ C 地图转写待办 1 项（UNRESOLVED）
A / B 前后计数完全相同（36/17 · 57/8，未改任何数据）
tsc -b OK · npm run build OK · npm test 1422 passed / 0 failed / 72 files（产品代码未改动 → 计数不变）
Research 门禁：validate_db PASS（4 警告，同基线）· validate_timeline_export PASS（0 警告）·
  validate_market_snapshot 342/8/0 · intake --check PASS（26 checks / 0 FAIL）·
  refresh_downstream --check 0 FAIL / 12 PASS · validate_monorepo_integrity PASS（25 项）· resolve_sa_artifact PASS
  restore_market_data --check PASS · make_market_snapshot 重生成后两次内容一致
```

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
