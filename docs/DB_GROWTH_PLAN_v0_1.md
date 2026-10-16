# 数据库增长方案（评估 · 未执行）

> 评估人：ThreeC Agent · 2026-10-13
> 触发：用户 2026-10-13 指令第 4 项 —— 「研究 DB 可重建方案与 Git LFS 的成本和风险，
> **先提交可执行方案，不要直接迁移或改写 Git 历史**」。
> ★ 本文**只有评估与方案**，**未执行任何迁移**。

---

## 一、实测事实（全部为本机实测）

### 1.1 DB 体积的**真正来源**

```
文件体积           59.5 MB
page_count×size    59.4 MB · freelist 2 页（**无空闲** → VACUUM 无用）

表                    行数
market_daily        337,995    ← ★ 几乎全部体积
sources                 432
evidences               414
campaign_evidences      389
trading_calendar        371
campaign_securities     220
securities              193
market_series           191
（其余 9 张表均 < 200 行）
campaigns                62
themes                   59
```

★ **结论：体积 ≈ `market_daily` 一张表。canonical 研究数据（campaigns / themes /
evidences / sources / …）合计 < 3,000 行，不足 1 MB。**

### 1.2 ★★ 行情数据**存了两份**（重复）

```
research/data/market/normalized/*.csv   19 MB · 180 文件 · **git 跟踪**（328 个文件含 raw）
research/data/market/raw/              6.5 MB · 145 文件 · **git 跟踪**
DB 的 market_daily                      59 MB · 337,995 行 · **git 跟踪**
```

实测比对（`ZTE` 2016-01-04 的 adjusted 行）：

```
CSV : 2016-01-04,15.522,15.742,13.832,13.862,13.862,457692.0,,adjusted
DB  : ('ZTE', '2016-01-04', 15.522, 15.742, 13.832, 13.862, 13.862)
                                    ↑ 完全一致
```

→ **同一份行情数据在仓库里存了 2 份（CSV + DB），合计 ~78 MB。**

### 1.3 压缩率

```
market_daily → CSV      32.1 MB
market_daily → CSV+gzip  **6.1 MB**（19%）
```

---

## 二、为什么必须处理

GitHub：**建议 50 MB / 硬上限 100 MB**。实测增长：

```
2026-10-12  推送时  55.51 MB
2026-10-13  推送时  59.46 MB     （单轮 +3.95 MB）
```

→ 按此速度，**再约 10 轮同类抓取即撞 100 MB 硬上限**，届时推送被**直接拒绝**。
★ 且**一旦撞上，历史里的 59 MB 无法通过常规手段移除**（用户已明确：不改写 Git 历史）。

---

## 三、三个方案（成本 / 风险 / 可复现性）

### 方案 A：**去重 + DB 的 `market_daily` 不入库**（推荐）

**做法**

1. **保留** `research/data/market/normalized/*.csv`（人类可读、可 diff、已被 328 个文件跟踪）
2. **新增** 重建脚本 `research/scripts/rebuild_market_daily_from_csv.py`：
   从 normalized CSV 导入 `market_daily`
3. **`cycle_research.db` 的 `market_daily` 改为可重建** → 但**单文件 DB 无法只排除一张表**

   → ★ **因此必须拆分**：把 `market_daily` / `market_series` / `trading_calendar`
   拆到**独立的 `market_data.db`**（`.gitignore`，不入库），
   `cycle_research.db` 只保留 canonical（< 1 MB，入库）。

**收益**：入库体积 **59 MB → < 1 MB**（行情改为本地重建，19 MB CSV 仍在库中）

**成本**

- ★ **已实测（2026-10-13）**：`research/scripts/` 下引用
  `market_daily` / `market_series` / `trading_calendar` 的 **`.py` 脚本共 31 个**，
  其中**活跃脚本 12 个**（非 `_v0_1`/`_v0_2` 历史版本、非一次性 `seed_*`/`fetch_market_*`）：
  `db.py` · `batch_auto_research.py` · `refresh_downstream.py` · `validate_db.py` ·
  `build_early_observation_v0_2.py` · `build_kline_alignment_v0_2.py` ·
  `check_security_list_alignment_v0_1.py` · `audit_historical_coverage.py` ·
  `build_structural_analogy_feasibility.py` · `calibrate_robotaxi.py` ·
  `check_doc_schema_consistency.py` · `_audit_dump.py`
- ★★ **真正的成本点**：`db.py` 虽有统一的 `connect()`，但实测
  **45 个脚本 `import db`**，而 **28 个脚本直接 `sqlite3.connect`（绕过 `db.py`）**。
  → 拆库需**逐个核对那 28 处**（哪些连的是 canonical、哪些连行情）。
  **这是方案 A 的主要工作量，也是它必须单独成轮次的原因。**
- 需新增重建脚本 + 文档
- CI 里若跑依赖 `market_daily` 的检查，需先重建（增加 CI 时间）

**风险**

- ★ **中**：改 DB 拓扑会影响所有读行情的脚本（本项目 144 个 py 文件），
  属**结构性改动**，须单独轮次 + 完整回归
- 行情可重抓（腾讯 GTIMG），但**依赖第三方接口稳定性**；
  且 `fetch_gaps.json` 的「已确认空段 / 最早可得日」是**累积知识**，必须一并保留

---

### 方案 B：**只去重（DB 入库，CSV 不入库）**

**做法**：`git rm --cached` 掉 `research/data/market/`（保留 DB 为唯一存储），
加 `.gitignore`。

**收益**：入库体积 **59 MB**（去掉 19 MB CSV）

**成本**：极低（一条 `git rm --cached` + gitignore）

**风险**

- ★ CSV 是**人类可读的审计面**（可以 diff、可以 grep）；
  移除后**只能通过 SQL 查**，审计便利性下降
- ★ `raw/`（6.5 MB）是**抓取原始响应**，是「拿不到 ≠ 不存在」纪律的**证据链**，
  移除后无法复核当时的接口返回
- 不改 DB 拓扑 → **不影响脚本**（最低风险）

---

### 方案 C：**Git LFS**

**做法**：`git lfs track "research/database/*.db"` + 迁移指针。

**收益**：仓库 .git 体积减小（大文件走 LFS）

**成本 / 风险**

- ★ **LFS 有配额**：GitHub 免费 **1 GB 存储 + 1 GB/月流量**。
  当前 DB 59 MB → 每轮 +4 MB，**配额约 15~20 轮耗尽**（与硬上限同量级）
- ★ **已推送的历史需要 `git lfs migrate`** —— 那会**改写 Git 历史**，
  **用户已明确禁止**
- ★ clone / CI 需 LFS 客户端（GitHub Actions 默认支持，但**每次拉 59 MB**）
- ★ **不解决根本问题**（只是把大文件挪到另一个配额里）

---

## 四、推荐

### 短期（**本轮即可执行，零风险**）：方案 B 的**保守变体**

**不做任何删除**，只**止住增长**：

1. 新增 `docs/` 说明「行情数据的唯一事实来源与重建路径」
2. **不改**任何已跟踪文件（避免动历史）

★ 但**这不解决增长**。

### 中期（**需单独轮次**）：方案 A

**理由**：

- 体积问题的**根因是重复存储**（CSV + DB 各一份）—— 方案 A 直接消除重复
- `market_daily` 是**派生物**（可从 CSV 重建），而 canonical 数据（< 1 MB）才是**不可再生**的
- **不改 Git 历史**（新增文件 + gitignore）
- 不依赖 LFS 配额

**执行前置（已完成的与仍需做的）**：

1. ✅ **已完成（2026-10-13）**：统计引用 `market_daily` / `market_series` /
   `trading_calendar` 的脚本 —— **31 个 `.py`，其中活跃 12 个**；
   并查明 **28 个脚本直接 `sqlite3.connect`（绕过 `db.py`）** ← 主要工作量在此
2. ⬜ **仍需做**：逐个核对那 28 处连接的**目标库**（canonical vs 行情）
3. ⬜ 设计 `market_data.db` 的 ATTACH 约定，并**先在一个副本上验证**全套脚本
4. ⬜ 新增 `rebuild_market_daily_from_csv.py` + 校验（重建后行数 / 首末日期与原库一致）
5. ⬜ 走**独立轮次**（不与其他改动混合）

### 明确**不推荐**：方案 C（LFS）

理由：配额量级与硬上限相同、**需改写历史（用户禁止）**、不解决根因。

---

## 五、结论（如实）

- **本轮只提交本方案**，**未执行任何迁移**（用户要求）。
- ★ **方案 A 的必要前置（脚本清单统计）已完成** —— 见 §三·方案 A「成本」：
  **31 个脚本引用相关表 · 活跃 12 个 · 28 个绕过 `db.py` 直连**。
  下一步是把那 28 处**逐个核对目标库**（仍未做）。
- ★ **「不改历史」意味着已入库的 78 MB 不会被移除** ——
  本方案只能**止住未来增长**，不能让仓库变小。**这一点必须在决策前明确。**
- 当前 DB **59.5 MB**，距硬上限 100 MB 尚有 ~40 MB（约 10 轮）余量，
  **不紧急但需在本轮之后的下一轮启动**。

---

*评估 · 2026-10-13 · ThreeC Agent · 未执行迁移*

---

# 附录 A：2026-10-13 第二轮审计（★ 修正上一轮的结论）

> 用户要求「重新实测，而不是当作无需核实的既定事实」。
> ★ **本轮实测推翻了本文件 §1.2 的一处结论** —— 见 A.3。

## A.1 DB 构成（重新实测 · 与上轮一致）

```
文件体积  59.46 MB · freelist 2 页（无空闲 → VACUUM 无用）

market_daily       337,995 行   ★ 体积主因
trading_calendar       371 行
market_series          191 行
（canonical 全部表合计 < 3,000 行）
```

★ 结论不变：**体积 ≈ `market_daily` 一张表**。

## A.2 直接连接清单（28 个脚本 · 实测）

**直接 `sqlite3.connect`**：**28 个**脚本；**经 `db.py` 统一入口**：45 个。

★ **同时满足「直接连接」且「触及行情表」的**（拆分方案的主要改动面）：

```
research/scripts/_audit_dump.py
research/scripts/audit_historical_coverage.py
research/scripts/batch_auto_research.py
research/scripts/build_structural_analogy_readiness_v0_2.py
research/scripts/check_doc_schema_consistency.py   （连的是 :memory:）
research/scripts/db.py                              （统一入口本身）
```

★ 目标路径形态：多数为 `DB_PATH`（来自 `db.py`），少数内联
`'database/cycle_research.db'` / `f"file:{ROOT}/research/database/cycle_research.db..."`。
→ **路径形态不统一**，拆库前需逐个核对。

## A.3 ★★ 重复性验证：**上一轮的结论需要修正**

### ★★★ 2026-10-14 更正：上一轮的「确认重复」是**对的**；本附录的「推翻」是**错的**

#### 错误的来源（我的比对脚本有 bug）

v0.2（本附录）的比对脚本把 DB 的 `trade_date`（形如 `'2023-01-03'`）
做了 `.replace('-','')` 后再去查 DB 的 dict —— 而 dict 的 key **没有**做同样处理
→ **永远匹配不上** → 误报「一致 0 · 不一致 5,441」。

★ **教训：当结论与预期完全相反时，先怀疑自己的工具，而不是结论。**
（与「结构校验只查形状」同族：**校验器本身的 bug 会伪装成数据问题**。）

#### 修正后的全量核验（只读）

```
180 个 CSV · 比对 **169,205 行** · 一致 **169,205** · 不一致 **0** · DB 无此日 **0**
```

```
标的        CSV行    一致   不一致
ABC          727     727       0
ACCELINK    1942    1942       0
AECPOWER      961     961       0
AIMEIKE     1275    1275       0
AMEC         536     536       0
...（全部 180 个文件，均为 0 不一致）
```

→ ★★ **CSV 与 DB 的 adjusted 行 100% 一致** —— **确认是同一份数据**。

#### 为什么必然一致：CSV 是 DB 的**派生视图**（实测权威关系）

```
research/scripts/fetch_market_batch_v0_3.py
  :457-459   db.insert(conn, "market_daily", … raw / adjusted)   ← ★ **DB 是权威（写入方）**
  :233-244   regen_normalized_csv(conn, series_id)               ← ★ **CSV 由 DB 导出（派生）**
                SELECT … FROM market_daily WHERE series_id=? ORDER BY price_type, trade_date
                → 写 {series_id}_daily.csv（9 列标准格式）
```

→ **权威口径由 `fetch_market_batch_v0_3.py`（写 DB）定义**；CSV 只是它的**可读导出**。

#### 附带发现（独立问题）：CSV 有三种历史格式

```
157 个: trade_date,…,adj_close,…      (regen_normalized_csv 的现行 9 列格式)
 20 个: date,…,                        ← 列名不同、无 adj_close
  3 个: trade_date,…,                  ← 无 adj_close
```
★ 后 23 个是**早期抓取器**留下的（不再由现行 `regen_normalized_csv` 生成）。
★ 这**不影响**去重决策（因为任何一方都可从 DB 重建），但**影响**「读 CSV 的下游脚本」
—— 它们必须容忍三种列集，否则会 `KeyError` 或整列缺失。

### A.4 附带发现：CSV **格式不统一**（三种列集）

```
157 个: trade_date,open,high,low,close,adj_close,volume,amount,price_type
 20 个: date,open,high,low,close,volume,amount,price_type          ← 列名不同 + 无 adj_close
  3 个: trade_date,open,high,low,close,volume,amount,price_type   ← 无 adj_close
```

★ 这是**独立于体积问题**的数据质量问题：任何「读 CSV 重建」的脚本
都必须先处理**三种格式**，否则会**静默漏读**（`KeyError` 或整列缺失）。

## A.5 压缩率（不变）

```
market_daily → CSV      : 32.1 MB
market_daily → CSV+gzip : 6.1 MB（19%）
```

## A.6 ★ 本轮结论：**暂缓迁移**，先补两项前置

1. ★ **确定权威来源**：CSV 与 DB 谁是权威？各自对应哪个复权基准时点？
   → 未确定前，**任何「重建」都可能换口径**（属静默失真）。
2. ★ **统一 CSV 格式**（三种列集 → 一种），否则重建脚本无法可靠工作。

★ 在这两项完成前，**方案 A 不具可执行性**；方案 B（只去重 CSV）**同样受阻**
（因为 CSV 可能承载 DB 没有的信息，如不同的复权口径）。
→ **本轮明确不改动任何数据**（符合用户指令）。

---

*附录 A · 2026-10-13 · ThreeC Agent · 只读审计，未修改任何数据*


## A.7 ★ 本轮最终结论（2026-10-14 · 权威关系已实测）

### 已确认事实

| 问题 | 结论 | 证据 |
|---|---|---|
| CSV 与 DB 是否重复 | ★ **是**（169,205 行 100% 一致） | 修正后的全量核验 |
| 谁是权威 | ★ **DB `market_daily`** | 抓取器 `db.insert()` 写 DB；`regen_normalized_csv` 从 DB 导出 CSV |
| 能否从权威重建 CSV | ★ **能** | `regen_normalized_csv` 本身就是重建函数 |
| 遗留问题 | CSV 有 23 个旧格式文件 | 三种列集（157/20/3） |

### ★ 因此方案 B（去重 CSV）**现在具备可执行性**

理由：CSV 是 **DB 的派生视图** 且可从 DB 重建（`regen_normalized_csv` 有实测先例）
→ 把 `research/data/market/normalized/*_daily.csv` 移出 git 跟踪**不会丢失任何信息**。

**执行步骤**（本轮**未执行**，待批准）：

1. `git rm --cached research/data/market/normalized/*_daily.csv` + `.gitignore`
   → 入库体积 19 MB → ~0 MB（**硬上限压力由 ~10 轮延至 ~25 轮**）
2. 保留 `fetch_gaps.json` 与 `raw/`（后者是「拿不到 ≠ 不存在」的**证据链**）
   ★ 但 `raw/` 6.5 MB 亦可按同一逻辑处理（可从腾讯接口重取，但**重取不保证一致** —— 建议保留）
3. 新增一条 CI/校验规则：**若需 CSV，先跑 `regen_normalized_csv`**
4. ★ **不改 DB**（DB 仍是权威，仍需入 git —— 59 MB 的问题留给方案 A）

### 方案 A（DB 拆库）仍待前置

① DB 本身 59 MB 入 git —— 这部分**只能靠方案 A**（把 `market_daily` 拆到不入库的
`market_data.db`）；而它**也可从 CSV / 原始接口重建**，技术上可行。
② 前置仍是那 **28 处直连**的逐个核对（本轮已列出触及行情表的 6 个活跃脚本）。

---

*附录 A.7 · 2026-10-14 · 更正并定稿 · 未执行任何迁移*

---

## 六、执行结果（2026-10-16 · 方案 A 已落地）

> 上方 §一–§五为 2026-10-13/14 的**方案原文**，保持不动。本节只追加执行结果。
> 完整说明与实测数据：`docs/MARKET_DATA_DB_v0_1.md`。

**落地形态**（与 §四·方案 A 的设想**有一处重要差异**，如实记录）：

- `cycle_research.db` **66.15 MB → 0.96 MB**（canonical 17 表入库；拆分后逐行内容不变）
- `market_data.db`（行情三表，373,917 行）**不入库**（`.gitignore`）
- ★★ **恢复输入不是 `normalized/*.csv`，而是新的「便携快照」** `research/data/market/snapshot/`
  （按年分片 `*.csv.gz` + `MANIFEST.json` + `market_schema.sql`，**6.08 MiB = 源库 9.2%**）
  · 理由：CSV 当初被移出 Git 的前提是「可从权威 DB 重建」—— 但 DB 拆走后该前提消失，
    必须有一个**被跟踪的**无损输入，否则干净克隆无法恢复。快照浮点**逐位无损**
    （2,053,911 个 REAL 差异 0）、gzip `mtime=0` **两次生成 sha256 相同**（可复现字节）。
  · `raw/**/*.json`（留痕）与 `normalized/*.csv`（派生）角色不变，`.gitignore` 注释已写清三者分工。

**§五清单逐项对账**：

| 原清单 | 状态 |
|---|---|
| 1. ✅ 统计引用行情的脚本（31 / 活跃 12 / 28 直连） | ✅ **复核一致**（A 工作流全仓库实测：28 直连 / 45 import db / 31 触及，活跃口径差异已注明原因） |
| 2. ⬜ 逐个核对 28 处连接的目标库 | ✅ **完成** —— 产出可执行清单（文件/行号/读写表/分类/是否 CI/迁移动作）；★ 实测**跨表 SQL 0 条**，读侧走 `db.connect()` 兼容层零改动，写侧 7 个改 `market.` 前缀，3 个直连改走统一入口 |
| 3. ⬜ 设计 ATTACH 约定并在副本上验证 | ✅ **完成** —— ATTACH + TEMP VIEW 兼容层；语义**逐条实测**（跨库 JOIN 453,028 行 / 只读主连接可挂载 / 写兼容层明确报错 / `sqlite_master` 不列行情表→`validate_db` 假阴性已修） |
| 4. ⬜ `rebuild_market_daily_from_csv.py` + 校验 | ➡️ **改为** `restore_market_data.py`（从快照恢复，非从 CSV）：`--check` 会**从目标库重生成快照逐分片比对 sha256**，比原计划的「行数/首末日期」强得多 |
| 5. ⬜ 走独立轮次（不与其他改动混合） | ✅ **完成** —— 本轮只做迁移 + 恢复 + CI 接入 + 文档；未改冻结产物、未新增 Campaign、未改 Research 结论 |

**风险澄清（§五已预言，现确认）**：不改历史 → 旧提交里的大 DB blob **仍在**，仓库历史体积不变；
本轮解决的是**停止未来增长**（新 blob ≈ 0.96 MB，未来每轮增量仅 canonical 部分）。
