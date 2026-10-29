# 当下行情刷新与公开表达修正 · 2026-10-29（v0.60）

> 本轮目标：让 ThreeC **达到可以开始真实使用的状态** —— 行情日期尽可能新、观察数据口径正确、
> 公开表述与实际证据一致。**不是**扩功能。
> 基线：`origin/main = eb4ffa0`（v0.59）。

---

## 1 · 各数据集的实际截止日期（分别标注，不得互相冒充）

| 数据集 | 轮前 | 轮后 | 说明 |
|---|---|---|---|
| `history_scan.db` · `index` | 2026-10-23 | **2026-10-29** | 4/4 序列（CSI300 / 上证 / 深证 / 创业板） |
| `history_scan.db` · `industry_board` | 2026-10-23 | **2026-10-29**（222/226） | 4 个板块仍 10-28：`BK884181 航空装备` / `BK884182 地面兵装` / `BK884184 特钢` / `BK884189 啤酒` —— **上游按年文件未含 10-29**，非我方缺口 |
| `history_scan.db` · `stock` | 2026-10-23 | **2026-10-29**（5,568/5,576） | 8 只落后：`*ST清越` 09-10、`*ST岭南` 10-12、`科瑞思` 10-12、`博盈特焊` 10-16、`秦港股份` 10-20 等（停牌/退市，**无新行情可取**） |
| `history_scan.db` · `concept_basket` | 2026-10-23 | **2026-10-29**（173/173） | 用 `scan_meta` 里**建库当时的成分快照**增量延长，**历史行未改动** |
| `history_scan.db` · `scan_daily` 总行数 | 13,008,438 | **13,034,444**（+26,006） | 个股 +22,275 · 板块 +3,023 · 篮子 +693 · 指数 +16 |
| `market_data.db` · `raw`（21 条当前前瞻序列 + 基准） | 2026-10-23 | **2026-10-29** | +84 行（21 × 4） |
| `market_data.db` · `market_daily` | 416,109 | **416,193** | |
| 行情快照 `research/data/market/snapshot/` | 416,109 行 / 6.74 MiB | **419,271 行 / 6.75 MiB** | 已重生成；`restore --check` **PASS**（逐分片哈希，含 REAL 逐位相同） |

**不同数据集日期确实不同，且都写在产物里**：`history_scan.db` 的 4 个板块停在 10-28、
8 只个股停在更早日期 —— 这些**不是**统一刷新失败，而是上游/标的自身没有新行情。

`market_data.db` 其余 187 条序列停在各自**事件窗口末**，属设计如此（事件窗口历史库），本轮未追。

---

## 2 · 当前观察产物与页面

| 产物 | 轮前 | 轮后 | 页面位置 |
|---|---|---|---|
| `early_observation_v0_2.json` `current_market` | **2026-10-20** | **2026-10-29** | 页头「当前市场状态」条（第一屏） |
| `forward_observation` | v0_3（as_of 10-23） | **v0_4（as_of 10-29）** | 「当前前瞻观察」区 |
| `pattern_discovery` | v0_10（as_of 20261023） | **v0_11（as_of 20261029）** | 「数据发现的历史季节性结构」 |
| `pattern_discovery_summary` | ← v0_10 | **← v0_11** | 同上（产品读摘要，不读 5.5 MB 全量） |
| `candidate_digest` | v0_9（price_as_of 10-23 / 含 10-20） | **v0_10（205 张卡 price_as_of 全为 10-29）** | 「本期研究快照」 |
| `candidate_ledger` | market_as_of 2026-10-23 | **2026-10-29** + 快照 `CL-2026-10-29-v0_2.json` | 「候选追踪」 |

**前端已全部改读新版本**：`forwardObservation.ts → v0_4`、`CurrentCandidatesSection.tsx → candidate_digest_v0_10`
（摘要/发现类产物按版本号自动发现最新，无需改引用）。

### 当前市场状态（可复算）

| 项 | 值 | 复算 |
|---|---|---|
| `SH000300` 收盘 | **4041.84**（2026-10-29） | 库内 `raw` 收盘 |
| 20 日收益 | **−10.52%** | 4517.28（09-23）→ 4041.84（10-29）= −10.5249% |
| 量分位（60 日） | 0.317 | 窗口内 ≤ 当日成交量 的占比 |
| 波动率比（20 日/60 日） | 1.026 | |
| MA20 / MA60 | **均在下** | |

### 流感题材 20 日超额（口径 v0_3，未改）

| 项 | 轮前（as_of 10-23） | 轮后（as_of 10-29） |
|---|---|---|
| 中位超额 | +4.60pp | **−2.85pp** |
| 广度 | 0.65 | **0.40** |
| 有数据参与者 | 20/20 | 20/20（剔除陈旧 0 只） |
| 参与者窗口 | 2026-09-17 → 2026-10-23 | **2026-09-23 → 2026-10-29** |

**独立复算**：逐只取 `2026-09-23` 与 `2026-10-29` 收盘，基准 4517.28 → 4041.84（−10.5249%），
20 只个股超额取中位数 = **−2.85pp**、广度 = **0.400**，与产物**完全一致**。

★ 数值方向翻转的原因是**市场本身**：同期基准跌 10.52%，题材参与者跌得更多（中位 −13.4%）。
这不是口径变化（`method_version` 仍 `v0_3`），也没有任何结论被"改好"。

### 概念篮子独立复算（抽样 `CPT_5Ggn` 5G概念）

用 `scan_meta` 里的成分快照重算 10-23 → 10-26：成员可算 43/47，均值收益 −0.567583%，
期望水平 5016.7520，库内实际 **5016.7520**（差 0.000000）。

---

## 3 · 公开表达修正（定向，未全站改）

| 位置 | 改了什么 | 为什么 |
|---|---|---|
| `README.md` | 「核心价值 = 机会发现」→「**产品目标 = 机会发现（长期方向，效果未验证）**」，并写明「其相对于常规研究方法的**增量价值仍待验证**；目前没有对照实验」 | 原文把长期目标写成了已实现的效果 |
| `README.md` | 新增**三层能力表**：① 历史证据整理 ✅ 已实现 · ② 研究线索发现 ✅ 已实现但 **❌ 有效性未验证** · ③ 已验证预测能力 **❌ 不存在**（样本外 4–6 步 << 门槛 30，事前特征 0） | 原文只有一段散落说明，容易被读成"已有预测能力" |
| `README.md` | 经验基准概率行**就地**补：样本量 n=7 / n=9（完整可比较年份）、观察期限、**分母范围**、三条限制 | 原文只给 `1/7`、`1/9` 与区间，没有就地解释样本与范围 |
| `README.md` | 行情数据截止改为**按数据集分列**（并注明 `adjusted` 未动） | 原写 `market_data.db = 2026-10-20`，已过期 |
| `README.md` | 历史角色行 `v0_8 / 73 条` → **`v0_13 / 84 条`**（RESEARCHED_PIT 15 · NOT_RESEARCHED 6） | 公开证据覆盖数字落后 4 个版本 |
| `docs/PRODUCT_PURPOSE.md` | 同一处定位改写；**修掉与 `AGENTS.md` §3.1 冲突的旧禁令**（原文写「❌ 胜率 / 季节性评分等量化结论」，而产品实际在展示经验基准概率） | 同一仓库两套规则，读者会得出相反结论 |
| `EmpiricalProbabilityBlock` | 新增「**分母范围 ≠ 完整观察总体**」：分母是**本题材**在**这些年份**里完整可比较的窗口，**不是**「所有可能题材（含从未成势方向）」的完整总体 → 不能外推为「任意题材同期上涨的概率」；并明写「本区**不缺**分母，缺的是未成势方向那一层观察」 | 原声明只说"分母只含完整可比较年份"，没区分**分母口径**与**观察总体**——这正是最容易被误读的一步 |
| `CurrentMarketStrip` | 补一行口径与来源：`原始收盘（未复权）· 20 日 = 最近 21 根 · 量分位 = 60 日窗口 · 来源：market_data.db` | 只给数字不给口径，使用者无从判断 |

**没有做的事**：没有全站加免责声明；没有删除任何有依据的历史描述；
没有把统计数字机械贴"无分母"标签（分母是有的，缺的是另一个总体）。

---

## 4 · 本轮踩到并修掉的数据完整性缺陷

### 4.1 ★★ 日期格式混写 → 整段历史被复制（已造成并已清理）

`backfill_history_v0_1.py --stocks` 走 `merge_rows(old, new)`，后者把日期**统一成紧凑格式**
（`20261023`）；而 `scan_daily` 里的个股历史是**带横线格式**（`2026-10-23`）。两者混写 →
**同一个交易日两行**。实测：处理 2,520 只股票后，`stock` 行数从 11,873,493 涨到 16,999,130
（**多出 5,155,656 行重复**，每只约 1,421 行）。

处置：
1. 精确删除紧凑格式的个股行（5,155,656 行），按库内实际内容回填 `rows/first_date/last_date`；
2. 复核：总行数回到 **13,011,352**、`(序列, 归一化日)` **重复组 = 0**；
3. 修掉根因：`merge_rows` **沿用既有行的格式**（不再混写），并注明当日增量应走新脚本；
4. 新增 `research/scripts/update_scan_stocks_v0_1.py`：**只插 `trade_date > 库内最大日`**、
   保持原格式、追加前做同日收盘重叠校验、失败只记录不补造。

### 4.2 空结果覆盖元数据

`upsert_series` 在抓取为空时无条件 `INSERT OR REPLACE ... rows=0 / first=NULL / last=NULL` ——
一次限流就会把序列从所有 `WHERE rows>0` 的查询里**抹掉**（数据还在 `scan_daily`）。
已加守卫：已有数据的序列只更新 `status/note`，**不动** `rows/first/last`。

### 4.3 硬编码的「当前」与「抓取日」

| 位置 | 原值 | 问题 |
|---|---|---|
| `build_early_observation_v0_2.py` `current_market.note` | 写死「快照日 2026-09-15；行情已补至 2026-09-30」 | 页头第一屏的说明在**陈述过期事实** |
| `build_forward_observation_v0_1.py` `GENERATED_AT` | 写死 `2026-10-24` | 每次刷新的「抓取日」都写成 10-24，溯源字段说谎 |
| `update_market_data_current_v0_1.py` `target_series` | 写死读 `forward_observation_v0_2.json` | 升到 v0_3/v0_4 后仍读旧版，参与者集合会悄悄停在旧版 |
| `build_candidate_digest_v0_1.py` | 写死读 `forward_observation_v0_2.json`（3 处） | 摘要里 `price_as_of` 仍是 **2026-10-20**，与页面其他位置自相矛盾 |

全部改为**由数据/实际日期派生**（最新版本号、运行时日期、实际末日）。

### 4.4 一处旧行为快照型测试

`test_candidate_ledger_v0_2.py::T12` 写死批次号 `CF-2026-10-23-02`。批次号 = `CF-<候选源 as_of>-NN`，
候选源 as_of 从 20261023 推进到 20261029 后自然变成 `CF-2026-10-29-01`。
改为**按 `formed_at` 推导**，断言的是不变量（拒绝时不得新建批次快照 / 成功时必须新建），
而不是某个具体日期。

---

## 5 · 校验（本地实测）

| 项 | 结果 |
|---|---|
| `restore_market_data --check` | **PASS**（419,271 行逐分片哈希） |
| `discover_seasonal_patterns_v0_5 --check` | **PASS**（as_of 20261029 · 1,300 达标 · 204 窗口指标已重算） |
| `build_pattern_summary_v0_1 --check` | **PASS**（← v0_11） |
| `build_candidate_ledger_v0_2 --check` | **PASS**（批次 1 · 实例 204 · 结算日 2026-10-29） |
| `build_candidate_digest_v0_1 --check` | **PASS**（213 张 · G1 29 / G2 63 / G3 0 / G4 121） |
| `build_forward_observation_v0_1 --check` | **PASS**（as_of 2026-10-29） |
| `build_theme_market_performance --check` | **PASS**（全部数值可由 `market_data.db` 复算） |
| `build_participant_evidence_v0_1 --check` | **PASS**（33 事件 / 148 条） |
| `audit_market_limit_up_v0_1 --check` | **PASS**（135 信号日） |
| `build_historical_market_roles_v0_1 --check` | **PASS**（84 角色 / PIT 0 违规） |
| `refresh_downstream --check` | **0 FAIL** |
| `test_discover_seasonal_patterns_v0_5.py` | **30 项 OK** |
| `test_candidate_ledger_v0_2.py` | **12 项 OK** |
| `tsc -b --force` | 干净 |
| `npx vitest run` | **1494 / 1494**（80 文件） |

---

## 6 · 仍存在的限制（可能影响真实使用）

1. **4 个板块停在 10-28、8 只个股停在更早日期** —— 上游文件滞后 / 标的停牌退市，**未补造**。
2. **`market_data.db` 只有 21 条当前序列到 10-29**；其余 187 条停在事件窗口末（设计如此）。
3. **`adjusted`（前复权）序列本轮一律未动** → `theme_market_performance` 的窗口行情仍基于旧复权序列。
   改前复权必须整段重取，属单独轮次。
4. **历史成分仍不可得**：概念篮子是「**建库当时**成分的等权合成」，不是历史成分；板块无历史成分。
5. **候选账本 204 条中 152 条仍 `PRE_WINDOW`**（11 月窗口 11-02 才开始），20 日结算最早 11-05 成熟；
   **本轮新增结算 0 条**，不得表述为「前瞻有效性已验证」。
6. **官方指数派生数值仍未接入**（授权 `UNCLEAR`），页面不展示。
7. `Market Snapshot`（`MS-2026-10-23-01`）仍是 DRAFT，**本轮未签发、未归档、未改 `index.json`**；
   快照里的 `market_regime` 用旧数据，属治理资产，不在普通行情刷新范围内。

---

## 7 · 复现命令

```bash
# 1) 基准指数 + 行业板块 + 个股（history_scan.db）
python research/scripts/backfill_history_v0_1.py --indices
python research/scripts/backfill_history_v0_1.py --boards --start-year 2026 --end-year 2026
python research/scripts/update_scan_stocks_v0_1.py --write

# 2) 概念篮子（用已存成分增量延长，不改历史）
python research/scripts/extend_concept_baskets_v0_1.py --write

# 3) 当前前瞻序列（market_data.db）+ 快照
python research/scripts/update_market_data_current_v0_1.py --write
python research/scripts/make_market_snapshot.py

# 4) 派生链
python research/scripts/build_early_observation_v0_2.py
python research/scripts/build_forward_observation_v0_1.py --fetch
python research/scripts/build_forward_observation_v0_1.py --write --version N
python research/scripts/discover_seasonal_patterns_v0_5.py --write --version N
python research/scripts/build_pattern_summary_v0_1.py --write
python research/scripts/monthly_candidate_ledger.py --write
python research/scripts/build_candidate_digest_v0_1.py --write --version N

# 5) 校验
python research/scripts/restore_market_data.py --check
python research/scripts/discover_seasonal_patterns_v0_5.py --check
python research/scripts/refresh_downstream.py --check
```

★ **顺序有依赖**：概念篮子必须在 `discover_seasonal_patterns` 之前延长，否则产物 as_of 与源数据不一致。
