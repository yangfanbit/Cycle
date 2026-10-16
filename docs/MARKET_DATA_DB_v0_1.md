# 行情数据库拆分与可复现恢复（v0.1 · 2026-10-16 执行）

> 上游方案：`docs/DB_GROWTH_PLAN_v0_1.md`（方案 A：拆库 + 可重建）。
> 本文记录**实际执行的拓扑、格式、命令与验证结果**，是该轮次的权威说明。

## 1. 为什么拆

`research/database/cycle_research.db` 达 **66.15 MB**（推送时 GitHub 提示
「66.15 MB > 建议 50 MB」），其中 `market_daily` **373,333 行**占绝大部分。
硬上限 100 MB，每轮补数都在逼近。目标：**停止未来提交继续产生大型单体 SQLite 文件**，
同时保持 Research / Product / 测试 / CI / 历史研究数据行为不变。
禁止改写 Git 历史 → 旧提交里的大 blob 仍在，本轮只解决**未来增长**。

## 2. 拓扑（执行后）

```
research/database/
  cycle_research.db    canonical 研究表（被 Git 跟踪）        0.96 MB   ← 入库
  market_data.db       行情三表（本地生成，.gitignore 忽略）   65.48 MB  ← 不入库
research/data/market/
  snapshot/            便携快照（被 Git 跟踪）                  6.08 MiB  ← 入库
    MANIFEST.json      格式版本 / 源库 sha256 / 每分片 rows+bytes+sha256 / 列顺序
    market_schema.sql  三表 DDL + 索引（与源库逐字节一致）
    market_daily/YYYY.csv.gz   按 trade_date 年份分片（含 raw + adjusted 全部 price_type）
    market_series.csv.gz · trading_calendar.csv.gz
  raw/**/*.json        抓取器留痕的原始响应快照（被跟踪，146 个，6.5 MB）
  normalized/*.csv     派生便捷 CSV（不跟踪，全仓库无消费者）
```

**三种行情数据角色的分工**（勿混淆）：

| 角色 | 位置 | 跟踪 | 用途 |
|---|---|---|---|
| 原始留痕 | `raw/**/*.json` | ✅ | 复核「当时接口返回了什么」 |
| **恢复输入** | **`snapshot/`** | ✅ | **干净克隆恢复 `market_data.db` 的唯一输入** |
| 派生 CSV | `normalized/*.csv` | ❌ | 便捷查看；需要时先重建，不假设存在 |
| 生成物 | `market_data.db` | ❌ | 本地查询/写入对象 |

## 3. 快照格式（为什么是按年分片 gzip CSV）

设计约束：**可版本管理**（git diff 只落在变化的年份）、**无网络可恢复**、
**浮点逐位无损**、**可校验**（每分片 sha256）。

实测数据（源库 66.15 MB）：

| 方案 | 体积 | 可 diff | 恢复复杂度 | 结论 |
|---|---|---|---|---|
| **按年分片 gzip CSV + MANIFEST** | **6.08 MiB（9.2%）** | ✅ 只动变化年 | 低 | **采用** |
| 单个 `.db.gz` 快照 | ~15 MB 量级 | ❌ 任何变动整包重传 | 低 | 否决 |
| 单一 CSV.gz（不分片） | 与分片相近 | ❌ 同上 | 低 | 否决 |
| Parquet | — | — | 需 pyarrow | 环境不具备，跳过 |

- **浮点无损**：CSV 用 Python `repr()` 写值（round-trip 精确），**不** `round()` / `%.2f`。
  实测恢复后 **2,053,911 个 REAL 值逐位相同**（`float.hex()` 比对，差异 0）。
- **可复现字节**：gzip `mtime=0` → 两次生成 **sha256 完全相同**（实测 0 差异文件）。
- **同时覆盖 raw 与 adjusted**：`price_type` 原样落盘，**不重算、不重新复权**、
  **不把 `adj_close` 设为 `close`**。
- `trading_calendar` / `market_series` 全量导出（含索引与主键）。

## 4. 恢复入口（幂等）

```bash
python research/scripts/restore_market_data.py --check    # 只读校验：快照完整性 + 已恢复库逐分片哈希一致
python research/scripts/restore_market_data.py --apply    # 恢复（已一致 → no-op）
python research/scripts/restore_market_data.py --apply --force   # 与快照不一致时按快照重建
```

- 退出码 `0` 成功 / `1` 失败（**明确失败，不静默跳过**）。
- `--check` 的强校验：从目标库**重新生成快照到临时目录**，逐分片比对 sha256
  → 等价于证明每个 REAL 逐位相同（比「比行数」强得多）。
- `--apply` 遇「目标库已存在但与快照不一致」→ **明确 FAIL** 并要求 `--force`，
  绝不会静默丢弃本地未快照化的数据。
- 快照再生成入口：`python research/scripts/make_market_snapshot.py`
  （抓取后更新快照时用；它会重写 MANIFEST 与全部受影响分片）。

## 5. 访问层（`research/scripts/db.py`）与实测语义

| 入口 | 用途 |
|---|---|
| `db.connect()` | canonical；**行情库存在时**自动 ATTACH `market` schema + 三表 **TEMP VIEW 只读兼容层** → 未限定表名的 SELECT/JOIN **行为不变** |
| `db.connect_market()` | 只连行情库（写行情的替代入口） |
| `db.insert(conn, table, row)` | 行情表**自动路由**到 `market.<table>` → 写侧脚本无需改动；行情库缺失 → `MarketDataMissing` |
| `db.require_market(conn)` | 显式断言「本连接可用行情表」，把缺库变成**可读的明确失败** |
| `db.market_attached(conn)` | 判断是否已挂载（★ 不能只看 `sqlite_master`，见下） |

**实测确认的语义**（不是照 API 说明假定）：

- ✅ 未限定 `market_daily` 的 SELECT / **与 canonical 表跨库 JOIN**（453,028 行）正常
- ✅ `PRAGMA table_info(market_daily)` 正常；主连接 `?mode=ro` 时 ATTACH + TEMP VIEW 仍正常
- ✅ `sqlite_master` **不**列出行情表（在 `sqlite_temp_master`）→ 「表是否存在」的判断必须两处都看
  （`validate_db.py` 的 `_table_exists` 已修，否则 market 检查组会**假阴性**静默失效）
- ✅ 对兼容层的 INSERT/UPDATE/DELETE **一律报错** → 写必须 `connect_market()` / `db.insert()` / `market.` 前缀
- ⚠️ ATTACH 到不存在路径会建空库 → 先显式检查文件存在，缺库时给恢复命令
- ⚠️ 缺行情库时 `connect()` **不报错**（不需要行情表的脚本不受影响），但未限定读会
  `no such table`、`db.insert` 抛 `MarketDataMissing` → **不静默返回空结果**

## 6. 脚本迁移（依据 A 清单：28 直连 / 45 import db / 31 触及行情表，与既有审计一致）

- **读侧零改动**（14 个脚本）：`db.connect()` 自动挂兼容层。含 CI 门禁 `validate_db.py`、
  `build_early_observation_v0_2` / `build_kline_alignment_v0_2` / `calibrate_robotaxi` /
  `check_security_list_alignment_v0_1` / `batch_auto_research` 等。
  ★ 跨表 SQL **0 条**（A 实测：无任何单语句混用两库）→ 不需要为 JOIN 改写。
- **写侧改 `market.` 前缀**（7 个）：`fetch_market_batch_v0_3.py`（现行抓取器）/
  `fetch_market_medical.py` / `seed_trading_calendar.py` / `fetch_market_batch.py` /
  `fetch_market_batch_v0_2.py` / `fetch_market_power.py` / `fetch_market_comm.py`。
  现行抓取器与日历生成器另加 `db.require_market(conn)`（缺库 → 可读失败）。
- **直连改走统一入口**（3 个）：`audit_historical_coverage.py` · `_audit_dump.py` ·
  `_seasonal_analysis/baseline.py`。
- **只读挂载**（1 个）：`build_structural_analogy_readiness_v0_2.py` ——
  ★★ 它支持 `THREEC_ROOT` 沙箱重定向，故行情库路径必须用**该脚本的 ROOT** 拼
  （不能用 `db.MARKET_DB_PATH`，否则沙箱会读到仓库里的真行情库）。
- **无需改动**：`fetch_market_2022/2023` · `fetch_market_huawei/tx` · `seed_market_series`
  （写全走 `db.insert()`，已自动路由）；`batch_auto_research` 的 themes 直连与
  `refresh_downstream` 的 campaigns 直连只碰 canonical，不受影响。

## 7. 迁移完整性验证（全部实测，非报告转引）

| 项 | 结果 |
|---|---|
| 迁移前基线 | 17 张表逐表内容哈希 + 质量指标存档（`.tmp/migrate/canonical.json` / `market.json`，不提交） |
| canonical 表 | 拆分后逐行**内容相同**（保留表哈希一致） |
| 行情表 | 行数 / 主键集合 / 类型 / 数值完全相同；`market_daily` 373,333 行 · `market_series` 213 · `trading_calendar` 371 |
| REAL 逐位 | 快照往返 **2,053,911 个 REAL 值差异 0**（`float.hex()` 比对） |
| 快照可复现 | 两次生成逐文件 sha256 **0 差异** |
| 恢复幂等 | 二次 `--apply` → no-op；`--apply --force` 重建后 `--check` PASS |
| 质量基线 | 重复键 0 · null OHLC 0 · 非正价 0 · OHLC 违律 0（迁移前后一致，见 §9） |
| 行情缺口标记 | `fetch_gaps.json` 未改动，缺口语义保留 |
| 行为保持 | `audit_historical_coverage.py`：原版脚本+原库 与 改版脚本+拆分库 输出 **JSON/CSV 逐字节一致** |

## 8. CI 集成（`.github/workflows/deploy.yml`）

Research 门禁之前新增一步 **`Restore market data DB (from versioned snapshot)`**：
`--apply` 后接 `--check`，任一步非零 → workflow 失败（`set -euo pipefail`）。
★ 不关闭任何门禁、不加跳过条件；`npm test` / `build` 在恢复步骤**之前**跑
（Product 不依赖 DB，不为它们无谓初始化行情）。

## 9. 已知缺口（均为**迁移前既有**，本轮不掩盖、不扩大）

1. ★ **`trading_calendar` 只有 371 行**，而 benchmark `SH000300` 有 **2,855** 个交易日
   → 2,484 个 `market_daily` 日期无日历覆盖（实测：`seed_trading_calendar.py` 一跑即
   371→2855）。拆分前原库同样 371 → **既有缺口**。日历补满是**数据决策**，不在迁移范围，
   如实记录；快照按**当前真实状态**（371）导出，不以「修数据」充数。
2. `research/research/reports/structural_analogy_feasibility_v0_2.json` 与当前 DB **漂移**
   （`sar_v0_2 --check` FAIL：重算比较数如 event_structure PARTIAL 74→317）。
   实测**原版脚本 + 拆分前原库同样 FAIL** → 与迁移无关，是 DB 增长后未重算的**冻结产物**。
   **不重生成**（属 Research 动作，非迁移动作）。
3. `historical_coverage_matrix_v0_1.json` 同理与当前 DB 有 237 字段漂移（同上证据链）。
4. 11 只证券负前复权价（腾讯 qfq 口径特性，非错误）· `SH000300` 2015-03-27 OHLC 违律
   （源数据缺陷，不在任何研究窗口内）· `YILING-002603` 重复序列（登记冗余，数值一致）
   → 三项均**不修正**（E 工作流已逐项论证）。
5. `raw/**/*.json` 6.5 MB 仍在 Git 中并按序列增长 —— 本轮未动（不扩范围）。
6. 旧提交里已入库的大 DB blob **仍在历史中**（禁止改写历史）→ 仓库历史体积不变，
   变的只是**未来不再增长**。

## 10. 干净克隆恢复（验收标准）

```bash
git clone <repo> && cd <repo>
python research/scripts/restore_market_data.py --apply
python research/scripts/restore_market_data.py --check     # PASS
python research/scripts/validate_db.py                      # PASS
# npm ci && npm test && npm run build
```

不依赖：本机残留 `market_data.db` · 被忽略的 `normalized/*.csv` · 任何实时外部接口。
