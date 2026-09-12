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
    """根据 schema.sql 建库。当前为空库即可安全执行。"""
    own = conn is None
    conn = conn or connect()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    if own:
        conn.close()


def insert(conn: sqlite3.Connection, table: str, row: dict) -> None:
    cols = list(row.keys())
    sql = f"INSERT OR REPLACE INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})"
    conn.execute(sql, [row[c] for c in cols])
    conn.commit()