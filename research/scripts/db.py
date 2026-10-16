"""ThreeC Research 子系统共享配置与数据库工具。

Monorepo（ThreeC）说明：
- 本文件位于 `<repo>/research/scripts/`，因此 `ROOT` = `<repo>/research`（Research 子系统根）。
- Research 侧的 `database/`、`schema/`、`research/`、`data/` 均相对 `ROOT` 解析。
- **canonical Research Export 不在本子系统内**：唯一源为 `<repo>/exports/timeline_export_v1.json`
  （Research → Product 交换文件），由 `EXPORTS_DIR` 指向。Research 脚本只写入该目录，
  Product（前端）只消费该目录，禁止在任一子系统内维护第二份副本。

运行环境：需要 Python3（含 sqlite3 标准库）。
用法：确保本项目根目录在 sys.path 中，import scripts.db as db。
"""
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "database", "cycle_research.db")
SCHEMA_PATH = os.path.join(ROOT, "schema", "schema.sql")

# ---------------------------------------------------------------- 行情数据库（2026-10-16 拆分）
#
# ★ 背景：`cycle_research.db` 曾达 66 MB，其中 `market_daily`（373k 行）占绝大部分，
#   超过 GitHub 建议的 50 MB 单文件阈值。行情三表已拆到**不入库**的 `market_data.db`。
#
# ★ 权威来源：
#   - **写入方**仍是抓取器（`fetch_market_batch_v0_3.py`）
#   - 干净克隆在**无网络**下由**被跟踪的便携快照**恢复：
#       python research/scripts/restore_market_data.py --apply
#
# ★ 连接约定（实测过语义，见 `attach_market()` 的注释）：
#   - `connect()`         → canonical；**若行情库存在**则同时挂上 `market` schema +
#                           行情三表的 **TEMP VIEW 只读兼容层** → 未限定表名的 SELECT 照常工作
#   - `connect_market()`  → 只要行情库（写行情时必须用它）
#   - `db.insert()`       → 行情表**自动路由**到 `market.<table>`（写侧脚本无需改动）
#   - 行情库缺失时：canonical-only 脚本照常工作；**需要行情表的脚本会明确失败**
#     （`no such table` 或 `MarketDataMissing`），**不静默返回空结果**。
MARKET_DB_PATH = os.path.join(ROOT, "database", "market_data.db")
MARKET_TABLES = ("market_series", "market_daily", "trading_calendar")
MARKET_ATTACH_SCHEMA = "market"
MARKET_RESTORE_CMD = "python research/scripts/restore_market_data.py --apply"


class MarketDataMissing(RuntimeError):
    """行情数据库缺失。★ 不静默降级 —— 调用方必须显式处理。"""


def market_db_available() -> bool:
    return os.path.exists(MARKET_DB_PATH)


def market_attached(conn: sqlite3.Connection) -> bool:
    return any(r[1] == MARKET_ATTACH_SCHEMA for r in conn.execute("PRAGMA database_list"))


def attach_market(conn: sqlite3.Connection, required: bool = True,
                  readonly: bool = False) -> bool:
    """把行情库 ATTACH 为 `market`，并为三表建 **TEMP VIEW 只读兼容层**。

    ★ 语义**实测结论**（不是照 API 说明假定）：
      · 未限定 `market_daily` 的 SELECT / JOIN（含与 canonical 表跨库 JOIN）→ **正常**
      · `PRAGMA table_info(market_daily)` → 正常
      · `sqlite_master` **不**列出它们（在 `sqlite_temp_master` 里）→ 需要「表是否存在」判断的
        代码必须走 `market_attached()`，不能只看 `sqlite_master`
      · ★ 对兼容层的 **INSERT/UPDATE/DELETE 一律报错**（`cannot modify … because it is a view`）
        → 写行情**必须**走 `connect_market()` 或 `db.insert()`（它会自动加 `market.` 前缀）
      · ATTACH 到**不存在的路径**会报错（不会静默建空库）——但仍先显式检查文件是否存在，
        以免在「目录存在但文件不存在」时被 SQLite 建出一个空库而掩盖问题。
      · 主连接以 `mode=ro` 打开时，ATTACH 与 TEMP VIEW **均正常**（只读场景实测通过）；
        `readonly=True` 时行情库本身也以 `?mode=ro` 打开，**绝不**因挂载而产生写入。
    """
    if not market_db_available():
        if required:
            raise MarketDataMissing(
                "行情数据库不存在：%s\n"
                "  ★ 请先恢复（干净克隆在无网络下即可完成）：\n"
                "      %s" % (MARKET_DB_PATH, MARKET_RESTORE_CMD))
        return False
    if market_attached(conn):
        return True
    target = MARKET_DB_PATH
    if readonly:
        target = "file:%s?mode=ro" % MARKET_DB_PATH
    conn.execute("ATTACH DATABASE ? AS %s" % MARKET_ATTACH_SCHEMA, (target,))
    existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_temp_master WHERE type='view'")}
    for t in MARKET_TABLES:
        if t in existing:
            conn.execute("DROP VIEW temp.%s" % t)
        conn.execute("CREATE TEMP VIEW %s AS SELECT * FROM %s.%s"
                     % (t, MARKET_ATTACH_SCHEMA, t))
    return True


def connect(attach_market_shim: bool = True) -> sqlite3.Connection:
    """canonical 连接。

    ★ `attach_market_shim=True`（默认）：行情库**存在时**挂只读兼容层；
      **不存在时不报错**（不需要行情表的脚本不受影响）。需要行情表的脚本会在查询时报错。
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if attach_market_shim:
        attach_market(conn, required=False)
    return conn


def connect_market() -> sqlite3.Connection:
    """**只连行情库**（写行情必须用它）。行情库缺失 → `MarketDataMissing`。"""
    if not market_db_available():
        raise MarketDataMissing(
            "行情数据库不存在：%s\n  ★ 请先恢复：%s" % (MARKET_DB_PATH, MARKET_RESTORE_CMD))
    conn = sqlite3.connect(MARKET_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def require_market(conn: sqlite3.Connection) -> None:
    """显式断言「本连接可用行情表」—— 用于把「缺行情库」变成**可读的明确失败**。"""
    attach_market(conn, required=True)

# canonical Research Export 目录：Monorepo 根的 exports/（= research/ 的上一级）
REPO_ROOT = os.path.dirname(ROOT)
EXPORTS_DIR = os.path.join(REPO_ROOT, "exports")
TIMELINE_EXPORT_PATH = os.path.join(EXPORTS_DIR, "timeline_export_v1.json")

# 常用枚举（与 schema CHECK 保持一致）
EVIDENCE_ROLE = ("supporting", "contradicting", "context")
EVIDENCE_CONF = ("high", "medium", "low")
RULE_STATUS = ("candidate", "under_review", "confirmed", "weak", "rejected")
ANNUAL_STATUS = ("strong", "medium", "weak", "no_clear_campaign", "unknown")
CAMPAIGN_RESULT = ("positive", "neutral", "weak", "failed", "unknown")
CAMPAIGN_CLASS = ("theme_campaign", "industry_trend", "event_driven", "mixed", "unclear")
THEME_TYPE = ("sector", "industry", "concept")
EVENT_TYPE = ("policy", "industry", "macro", "company", "market", "news", "holiday", "other")
SECURITY_ROLE = ("leader", "second_leader", "representative", "follow")
# Pilot 1-C1
SERIES_TYPE = ("industry_index", "sector_index", "concept_index", "stock", "benchmark", "other")
PRICE_TYPE = ("raw", "adjusted", "other")
DATE_ROLE = ("start", "end", "peak")
VERIFY_METHOD = ("manual", "market_data", "market_data_plus_event", "unknown")
# Pilot 1-C0
TEMPORAL_RELATION = ("contemporaneous", "prior", "subsequent", "retrospective", "unknown")


def init_db(conn: sqlite3.Connection = None) -> None:
    """根据 schema.sql 建库（**canonical 表**）。

    ★ 2026-10-16 拆分后：`schema.sql` 里的**行情三表 DDL 会被跳过** ——
      它们属于 `market_data.db`，由 `research/scripts/restore_market_data.py --apply`
      从便携快照恢复（`schema.sql` 是冻结文件，不改；这里只是运行时过滤）。
    """
    own = conn is None
    conn = conn or connect()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql = f.read()
    for stmt in _strip_market_ddl(sql):
        conn.executescript(stmt + ";")
    conn.commit()
    if own:
        conn.close()


def _strip_market_ddl(sql: str) -> list:
    """从 schema.sql 文本中剔除**行情三表**及其索引的 DDL 语句（运行时过滤，不改冻结文件）。"""
    out = []
    for stmt in sql.split(";"):
        s = stmt.strip()
        if not s:
            continue
        low = " ".join(s.lower().split())
        if any(("create table" in low and (" %s " % t) in low + " ") for t in MARKET_TABLES):
            continue
        if any(("create index" in low and ("on %s" % t) in low) for t in MARKET_TABLES):
            continue
        out.append(s)
    return out


def _table_exists(conn, name) -> bool:
    r = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    return r is not None


def _column_exists(conn, table, col) -> bool:
    try:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    except Exception:
        return False
    return col in cols


def migrate(conn: sqlite3.Connection = None) -> None:
    """增量迁移：对已有数据库补建新表/新列，不破坏既有数据。幂等。
    v1.5 → evidences.independence_group、campaign_evidences
    Pilot 1-C1 → market_series / market_daily / trading_calendar / campaign_date_observations
    """
    own = conn is None
    conn = conn or connect()

    # 1) 新增 evidences.independence_group 列
    if _table_exists(conn, "evidences") and not _column_exists(conn, "evidences", "independence_group"):
        conn.execute("ALTER TABLE evidences ADD COLUMN independence_group TEXT")
        print("[migrate] + evidences.independence_group")

    # 2) 新增 campaign_evidences 桥表
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS campaign_evidences (
            campaign_id     TEXT NOT NULL REFERENCES campaigns(campaign_id),
            evidence_id     TEXT NOT NULL REFERENCES evidences(evidence_id),
            role            TEXT NOT NULL CHECK (role IN ('supporting','contradicting','context')),
            created_at      TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (campaign_id, evidence_id)
        );
    """)

    # 3) 新增 evidences.temporal_relation 列（Pilot 1-C0）
    if _table_exists(conn, "evidences") and not _column_exists(conn, "evidences", "temporal_relation"):
        conn.execute("ALTER TABLE evidences ADD COLUMN temporal_relation TEXT")
        print("[migrate] + evidences.temporal_relation")

    # ---- Pilot 1-C1 行情核验基础设施 ----
    # ★ 2026-10-16 拆分后：行情三表**不再**在 canonical 库创建。
    #   它们住在 `market_data.db`（不入库），由便携快照恢复：
    #       python research/scripts/restore_market_data.py --apply
    #   （`market_daily` / `market_series` / `trading_calendar` 的 DDL 见快照内的 market_schema.sql）
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS campaign_date_observations (
            observation_id     TEXT PRIMARY KEY,
            campaign_id        TEXT NOT NULL REFERENCES campaigns(campaign_id),
            date_role          TEXT NOT NULL CHECK (date_role IN ('start','end','peak')),
            candidate_date     TEXT NOT NULL,
            verified_date      TEXT,
            verification_method TEXT NOT NULL CHECK (verification_method IN
                                ('manual','market_data','market_data_plus_event','unknown')),
            confidence         TEXT NOT NULL CHECK (confidence IN ('high','medium','low')),
            evidence_id        TEXT REFERENCES evidences(evidence_id),
            notes              TEXT,
            created_at         TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_cdo_campaign  ON campaign_date_observations(campaign_id);
    """)
    if not market_db_available():
        print("[migrate] ★ 行情数据库不存在 —— 需要行情表的脚本请先运行：%s" % MARKET_RESTORE_CMD)
    conn.commit()
    if own:
        conn.close()


def insert(conn: sqlite3.Connection, table: str, row: dict, schema: str = None) -> None:
    """`INSERT OR REPLACE`。

    ★ 2026-10-16 拆分后：**行情表自动路由**到 ATTACH 的 `market` schema
      → 写侧脚本无需改动，只要连接来自 `connect()`（默认挂兼容层）或 `connect_market()`。
      ★ 行情库缺失时**明确失败**（`MarketDataMissing`），**不静默写入 canonical**。
    """
    if schema is None and table in MARKET_TABLES:
        if market_attached(conn):
            schema = MARKET_ATTACH_SCHEMA
        else:
            raise MarketDataMissing(
                "无法写入行情表 %s：行情数据库未挂载。\n"
                "  ★ 请先恢复：%s" % (table, MARKET_RESTORE_CMD))
    target = ("%s.%s" % (schema, table)) if schema else table
    cols = list(row.keys())
    sql = f"INSERT OR REPLACE INTO {target} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})"
    conn.execute(sql, [row[c] for c in cols])
    conn.commit()