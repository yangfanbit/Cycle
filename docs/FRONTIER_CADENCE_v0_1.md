# ThreeC 前瞻排程 · 双轨更新节奏 v0.1

> 生效：**2026-11-07（v0.77）** · 基线 `ed5ad1f` · 状态：已落地
> 适用：独立工作台 `workbench.html` 的默认主入口「前瞻排程」
> 相关：`docs/EVALUATION_FRAMEWORK_v0_1.md` · `docs/REAL_USE_LITE_v0_1.md` ·
> `research/scripts/build_frontier_board_v0_1.py`

---

## 1 · 方向纠正（为什么有这份文档）

v0.74 的工作台做成「**我提问 → 系统给历史对照 → 我记下判断**」，是 pull / 事后研究。
使用者明确：目标是「**提前让系统推荐或挖掘可以提前埋伏的概念板块和理由**」，
「研究某个板块」是**已经筛出来之后**才会点进去做的事。原形态与目标相反。

v0.77 起：默认主入口改为 **push / 事前**——系统主动推出「接下来值得关注」的
前置观察窗口 + 双轨理由；历史检索、证据详情、T 时刻冻结都下沉为二级操作。
有效性口径仍为**研究增量**（v0.74），未改；改的是**系统先给什么**。

---

## 2 · 双轨定义（并列，不做因果拼接）

| | 统计轨 | 机制轨 |
|---|---|---|
| 回答的问题 | 「历史上这个板块 / 概念在这个时间窗常怎样」 | 「最近发生了什么可核的事、接下来有什么已知日程」 |
| 输入 | `candidate_digest_v0_*.json`（→ `pattern_discovery` → 账本） | `new_theme_radar_v0_*_view.json` + `event_calendar_v0_1.json` |
| 更新节奏 | **季度**（全量历史统计重算） | **每周**（使用者主动触发，AI 辅助） |
| `as_of` | digest 的 as_of；周更时**不变** | radar 的 as_of；周更时推进 |
| 产物字段 | `statistical_reason`（n_years / hit_rate / 中位超额 / OOS / PIT 资格） | `mechanism_feed`、`calendar`、`mechanism_reason` |

★ **两轨各自 as_of 独立标注，页面并列展示，不互相冒充、不做因果拼接。**

★ **机制理由不硬贴**：实测 177 张统计卡中，能与雷达板块序列 `board_series`
**精确匹配**的只有 **1 条**。因此机制轨是独立信息流，其余卡片如实写
「本期机制轨无可核关联」。曾尝试按名称子串匹配，会误命中
「贸易」←「石油加工贸易」、「脑机接口」←「脑机接口医疗器械」，**已明确禁用**。

★ 统计理由是历史重复与样本外检验结果，**未校准、不是未来概率**；
5/10/20 日超额只作行情附注，不参与研究增量验收。

---

## 3 · 周更 SOP（机制轨；使用者每周主动触发）

> 「机制的实时更新」在本架构下的准确含义：**每周可重复执行、由使用者触发、
> AI 辅助完成**，不是常驻抓取服务。项目无后端、无定时任务、**不新增 CI Job**。

```bash
P=~/.workbuddy-ai/binaries/python/envs/default/bin/python
cd <repo>

# ① 行情 + 市场信息：按 docs/MARKET_DATA_REFRESH_2026-10-29_v0_1.md §7 顺序
#    （全套刷新，勿只推进指数/板块 —— 基准与参与者日期必须对齐）
$P research/scripts/backfill_history_v0_1.py --indices
$P research/scripts/backfill_history_v0_1.py --boards --start-year <YYYY> --end-year <YYYY>
$P research/scripts/update_scan_stocks_v0_1.py --write
$P research/scripts/extend_concept_baskets_v0_1.py --write
$P research/scripts/update_market_data_current_v0_1.py --write
$P research/scripts/make_market_snapshot.py

# ② 雷达重抓（升版，不覆盖旧产物）
$P research/scripts/build_new_theme_radar_v0_1.py --fetch --write --version <N>

# ③ 未来事件日历增补：只加**可核来源**的条目，逐条写 source / 核验状态；
#    不得推测或编造两会、政策生效日、调样日等。无新事实时本步跳过。

# ④ 研究轮次（离线研究产物）先校验，再让周更视图投影最新一轮
$P research/scripts/check_research_round_v0_1.py --check

# ⑤ 重算前瞻排程（确定性派生缓存，原地更新，见 §5）
$P research/scripts/build_theme_market_v0_1.py --write
$P research/scripts/build_frontier_board_v0_1.py --write
# ★ v0.80：本周研究视图读排程的 feed_window 并记录其 sha256 → 必须排在 board 之后
$P research/scripts/build_weekly_research_v0_1.py --write
# ★ v0.81：新增研究轮次后要 --write 追加新声明（旧声明逐字保留）；
#   只跑 --check 会因 source.round_sources 的 sha256 变化而 FAIL。行情推进本身不改声明。
$P research/scripts/build_phase_declaration_log_v0_1.py --write

# ⑥ 验证
$P research/scripts/check_research_round_v0_1.py --check
$P research/scripts/build_phase_declaration_log_v0_1.py --check
$P research/scripts/build_theme_market_v0_1.py --check
$P research/scripts/build_frontier_board_v0_1.py --check
$P research/scripts/build_weekly_research_v0_1.py --check
npx tsc -b --force && npx vitest run && npx vite build
```

★ 周更**不重算** `pattern_discovery` / `candidate_digest` → 统计轨 `as_of` 保持上季度值，
这是设计如此，不是数据缺失。页面必须能看出两轨日期不同。

## 4 · 季更 SOP（统计轨）

```bash
$P research/scripts/discover_seasonal_patterns_v0_5.py --write --version <N>
$P research/scripts/build_candidate_digest_v0_1.py --write --version <N>
# 若专项假设 / 前置观察窗口有变，再跑 build_forward_observation_v0_1.py
$P research/scripts/build_frontier_board_v0_1.py --write
```

季更与周更可各自独立触发；`build_frontier_board_v0_1.py` 用
**glob + 版本号数字排序**动态选最新源，不需要改代码或前端 import。
★ 版本号不可用字符串排序（`v0_9` 会排在 `v0_12` 之后）。

## 5 · 产物性质（避免与「升版一律新文件」混淆）

| 文件 | 性质 |
|---|---|
| `research/current/frontier_board_v0_1.json` | **确定性派生缓存**，原地重算；不是研究产物 |
| `research/current/event_calendar_v0_1.json` | 同上；日历事实全部从既有产物抽取 |
| `candidate_digest_v0_*.json` / `new_theme_radar_v0_*.json` | 研究产物，**升版不覆盖**（既有约定不变） |

`--check` 逐字段复算两份缓存、校验输入 sha256、G1→G4 顺序、关注标签规则、
机制关联必须为精确序列匹配且 URL 可核、日历假说层状态、两轨节奏声明，
并扫描禁用字段与措辞。**既有研究产物一字未改。**

---

## 6 · 排序边界（两类排序，不得混读）

| | 出现位置 | 性质 |
|---|---|---|
| **G1→G4 研究浏览顺序** | **默认页面** | 产物 `group_rule` 已有分组；**无分数**、不是收益排序、不是概率 |
| Wilson 95% 下界启发式打分 | **仅**主动打开的「内部评估视图」 | `INTERNAL_EVAL_ONLY` · 未校准 · 非概率 · 不参与验收；数据按需加载 |

★ v0.74 的「**默认页面不做优先级排序**」条款**已撤销**（使用者 2026-11-07 决策 1）。
但「**默认页面零启发式打分字段**」这一不变量**保留**，并由产物 `--check`、
前端单测、浏览器探针三重锁定。两者不矛盾：分组顺序 ≠ 打分排序。

## 7 · 措辞边界（使用者 2026-11-07 决策 3）

| 允许 | 仍禁止 |
|---|---|
| 值得关注、可斟酌的决策点、前置观察窗口、研究起点、优先观察 | 买入 / 卖出 / 目标价 / 仓位 / 胜率 / 推荐买入 / 买卖信号 / 选股清单 |

「值得关注」= **前置观察窗口 / 研究起点**，**不是买卖点**；
具体的买卖决策由使用者自行做出。系统不替代这一步，也不对措辞过度自我审查。

## 8 · 生肖试点（并入机制轨 / T2，使用者决策 4）

定位：**A_CALENDAR 行为假说族**，不是题材，不得赋予行业属性（既有产物原约束）。
接入方式：日历事实 + 假说登记 + 前置观察窗口 + 缺口清单，**不升级为可执行候选**。

- 三层映射登记于 `event_calendar_v0_1.json`：`LITERAL`（现有假设仅此层）→
  `HOMOPHONE`（羊 / 洋 / 阳 / 扬，含九阳股份、圣阳股份、阳光电源）→ `SEMANTIC`。
  ★ 后两层标 `UNVERIFIED_ASSUMPTION`，**不进统计、不参与排序、不构成篮子**；
  启用前必须**另立 hypothesis_id**（加层会改变研究问题与分母）。
- 既有结论保持：`evidence_status = INSUFFICIENT`、当前名称含「羊」仅 2 只、
  无法构成篮子；`CAND-ZODIAC-2027` 窗口 `2026-12-15 → 2027-02-06 → 2027-03-05`。
- 启动点逐年漂移（2026 马年 6 月 / 2027 羊年 11 月）→ **触发式观察**，
  `window.start` 只是最早观察起点，不是行情启动日，不写死「提前 N 天」。

### 已核实、不得绕过的缺口

1. **`PIT_NAME_SNAPSHOT_MISSING`**：历史证券名称 / 改名 / 上市退市快照缺失。
   `forward_observation.limitations` 已自述「概念/名称候选池用当前快照回溯 →
   存在幸存者偏差与成分变更偏差」，12 个年份里 10 个 `testable=false` 皆因此。
   **周更行情不含此数据 → 本轮无法补齐**；在此之前任何生肖历史统计都不得升级为线索。
2. `NO_FUTURE_POLICY_CALENDAR`：本版日历只含库内可核的农历新年与既有观察窗口；
   两会 / 政策生效日 / 指数调样 / 行业大会库内无可核来源，**不编造**，
   周更时由可核来源逐条补入。

---

## 9 · 边界

不修改冻结的 Research Model、`schema.sql`、Export Contract、SA / TO / Driver；
不签发或归档 Market Snapshot、不改 `index.json`；不新增来源适配器、后端、
定时任务或 CI Job；不生成未有证据支持的数据；既有产物 v0.1–v0.9 全部保留。

---

## 10 · 行情校正（v0.78 补，独立于双轨节奏）

> 完整方法与结论见 `docs/PRICE_CALIBRATION_v0_1.md`。

两轨的统计侧原本建立在「同花顺编制指数 / 当前成分等权自建篮子 / raw 未复权 /
新浪 CSI300（2014-06-20 起）」之上。v0.78 用**真实 A 股个股**与**中证官方基准**
各做一次独立复核，结论是**并列不合并、不替换基准、不重算历史统计**（并列展示）：

- **L0**：5 个自建概念篮子与真实个股逐日复算相关 **1.0**、中位差 **0.0 pp**
  → 计算无误，偏差在「用今天的成分名单回溯」这个对象定义（幸存者 / 成分变更偏差）。
- **L2**：中证官方 `000300` 与库内 CSI300 重叠 **3,009** 个交易日 0.01 容差内全部一致、
  日收益相关 **1.0** → 库内基准就是官方点位，**差异仅在起点被 3,000 根截断**。
  发布日前 62 行标 `BACKFILLED_NOT_PIT`；2005-04-08→2014-06-19 共 2,233 行可用但未入库。
  授权 `state=UNCLEAR`、`program_verified=false`，闸门在联网前拒绝无授权写入。

★ **周更 SOP 不变**：校正产物是**对照证据**，不是新基准。
若将来要把超额口径延长到 2005 年，必须单独一轮：落盘官方逐日点位 → 重算全派生链 →
重排 Top 6，并声明回溯段不得用于时点判断。**不得在本周更流程里顺手替换基准。**

---

## 11 · 可解释性与阶段语义（v0.79 补）

> 完整方法见 `docs/BOARD_SEMANTICS_v0_1.md` 与 `docs/PHASE_GOVERNANCE_v0_1.md`。
>
> ★★ **v0.80 勘误（2026-11-08）**：本节第 3 条「当前研究主题的阶段是产业机制阶段，不是行情状态」
> 的**治理结论不变**，但「并列展示」的位置变了 —— **默认页不再展示阶段声明**，
> 改给本周最新研究（`weekly_research_v0_1.json`）与行情附注；阶段声明下沉到
> 内部评估视图的**追加式声明日志**（`phase_declaration_log_v0_1.json`），供日后回测留痕。
> 周更 SOP 相应增加两步（见 §3 第 ④ 步）；`REVIEW_STALE` / `DIVERGENCE_*` 信号保留，
> 它们是「提醒人工写新声明」的触发器。原句保留不改，此处仅作展示层勘误。

- **精选硬门槛加 `interpretable=true`**：名称含「其他 / 综合」的同花顺分类兜底桶（27 个）
  不进 Top 6，但统计不改、全量区可查、下方「待解释板块」区单独展示并给排除理由。
- **当前研究主题的阶段是产业机制阶段**，不是行情状态。周更只刷新关联标的行情、
  陈旧度（`REVIEW_STALE`）与产业/市场背离（`DIVERGENCE_INDUSTRY_VS_MARKET`）信号，
  **不自动改阶段**；改阶段必须走人工研究轮次并留痕。
- ★ **周更 SOP 增加两步**（在 §3 的第 ④ 步之前）：
  ```
  $P research/scripts/build_board_semantics_v0_1.py --write
  $P research/scripts/build_theme_market_v0_1.py --write
  $P research/scripts/build_frontier_board_v0_1.py --write
  ```
  顺序不可颠倒：frontier_board 会记录上游产物 sha256，上游重生成后必须重算排程。
