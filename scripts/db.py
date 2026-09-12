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
    """v1.5 增量迁移：对已有数据库补建新表/新列，不破坏既有数据。幂等。"""
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
    conn.commit()
    if own:
        conn.close()


def insert(conn: sqlite3.Connection, table: str, row: dict) -> None:
    cols = list(row.keys())
    sql = f"INSERT OR REPLACE INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})"
    conn.execute(sql, [row[c] for c in cols])
    conn.commit()