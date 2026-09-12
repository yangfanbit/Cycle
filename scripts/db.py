"""Cycle-Research 共享配置与数据库工具。

运行环境：需要 Python3（含 sqlite3 标准库）。
用法：确保本项目根目录在 sys.path 中，import scripts.db as db。
"""
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "database", "cycle_research.db")
SCHEMA_PATH = os.path.join(ROOT, "schema", "schema.sql")

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


def connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection = None) -> None:
    """根据 schema.sql 建库。空库或已存在库均可安全执行（增量迁移见 migrate()）。"""
    own = conn is None
    conn = conn or connect()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    if own:
        conn.close()


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

    # ---- Pilot 1-C1 行情核验基础设施（新增 4 表，幂等）----
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS market_series (
            series_id         TEXT PRIMARY KEY,
            name              TEXT NOT NULL,
            series_type       TEXT NOT NULL CHECK (series_type IN
                                ('industry_index','sector_index','concept_index','stock','benchmark','other')),
            provider          TEXT,
            symbol            TEXT,
            frequency         TEXT NOT NULL DEFAULT 'daily'
                                CHECK (frequency IN ('daily','weekly','monthly','intraday','other')),
            price_type        TEXT NOT NULL CHECK (price_type IN ('raw','adjusted','other')),
            adjustment_method TEXT,
            description       TEXT,
            created_at        TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS market_daily (
            series_id     TEXT NOT NULL REFERENCES market_series(series_id),
            trade_date    TEXT NOT NULL,
            open          REAL, high REAL, low REAL, close REAL,
            adj_close     REAL,
            price_type    TEXT NOT NULL CHECK (price_type IN ('raw','adjusted')),
            volume        REAL,
            amount        REAL,
            data_source   TEXT,
            retrieved_at  TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (series_id, trade_date, price_type)
        );
        CREATE TABLE IF NOT EXISTS trading_calendar (
            trade_date      TEXT PRIMARY KEY,
            is_trading_day  INTEGER NOT NULL CHECK (is_trading_day IN (0,1)),
            calendar_type   TEXT NOT NULL DEFAULT 'cn',
            created_at      TEXT DEFAULT (datetime('now'))
        );
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
        CREATE INDEX IF NOT EXISTS idx_mdaily_series ON market_daily(series_id, trade_date);
        CREATE INDEX IF NOT EXISTS idx_cdo_campaign  ON campaign_date_observations(campaign_id);
    """)
    conn.commit()
    if own:
        conn.close()


def insert(conn: sqlite3.Connection, table: str, row: dict) -> None:
    cols = list(row.keys())
    sql = f"INSERT OR REPLACE INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})"
    conn.execute(sql, [row[c] for c in cols])
    conn.commit()