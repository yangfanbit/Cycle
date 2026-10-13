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

### 上一轮的说法（本文件 §1.2）

> 「实测 ZTE 2016-01-04 的 adjusted 行**逐字段一致** → 确认重复」

### 本轮更系统的抽样（5 个标的 · adjusted 行 · 比对 open/close）

```
标的        CSV总行   adj行    DB行    一致    不一致
ABC          1454     727     727      0      727
ACCELINK     3884    1942    1942      0     1942
AECPOWER     1922     961     961      0      961
AIMEIKE      2550    1275    1275      0     1275
AMEC         1072     536     536      0      536
★ 一致 0 行 · 不一致 5,441 行
```

### ★ 修正后的结论

- **行数与日期完全对应**（727=727、1942=1942 …）→ 二者**同源**（同一批行情、同一交易日集合）。
- **数值系统性不一致** → **不是**「逐字段一致的重复」。
  ★ 最可能的原因是**复权基准时点不同**（前复权价随每次除权**整体重算** ——
  这正是本项目已知的纪律：抓取器「必须整段重取，不能只补缺口」）。
- → 上一轮基于**单个标的（ZTE）**得出「确认重复」，**样本不足**。
  本轮的 5 标的抽样**推翻**了该结论。

★★ **因此方案 A 的前提需要重新论证**：在「CSV 与 DB 数值不一致」的情况下，
**不能**简单地把任一方当作另一方的可重建来源 —— 必须先确定
**哪一方是权威**（以及各自对应哪个复权基准时点），否则「重建」会**静默换口径**。

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
