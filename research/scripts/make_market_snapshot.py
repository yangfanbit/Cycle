#!/usr/bin/env python3
"""行情便携快照 —— **生成**（Research 侧）。

## 为什么需要

`research/database/cycle_research.db` 一度 66 MB，其中 `market_daily`（373k 行）是唯一主因。
本仓库把行情三表（`market_daily` / `market_series` / `trading_calendar`）拆到**不入库**的
`research/database/market_data.db`，由**本快照**在干净克隆中恢复。

## 快照格式（`research/data/market/snapshot/`）

```
MANIFEST.json                     # 无时间戳 → 逐字节可复现；含每分片 rows / bytes / sha256
market_schema.sql                 # 三表 DDL（取自源库 sqlite_master，**逐字节**）
market_daily/<YYYY>.csv.gz        # ★ 按 trade_date 年份分片，含全部 price_type
market_series.csv.gz
trading_calendar.csv.gz
```

★ **无损性**：所有 REAL 用 Python `repr()` 写出（round-trip 精确）；**不得**四舍五入。
★ **可复现**：gzip 用 `mtime=0` 且不写入原始文件名 → 同一源库两次生成**逐字节相同**。
★ **可 diff**：按年分片 → 单年变化只产生该年分片的 git 增量。

## 用法

```bash
python research/scripts/make_market_snapshot.py            # 生成/刷新快照
python research/scripts/make_market_snapshot.py --check    # 只校验：快照是否与源库一致（不写盘）
```

★ 本脚本**只读**源库；**不写**任何数据库。
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_DIR = os.path.join(ROOT, "data", "market", "snapshot")
CANONICAL_DB = os.path.join(ROOT, "database", "cycle_research.db")
MARKET_DB = os.path.join(ROOT, "database", "market_data.db")

# ★ 顺序即依赖顺序（market_daily 引用 market_series）
MARKET_TABLES = ("market_series", "trading_calendar", "market_daily")
SHARDED_TABLE = "market_daily"
FORMAT_VERSION = "0.1"


def resolve_source(explicit: str | None) -> str:
    """源库解析：显式 → market_data.db（拆分后）→ cycle_research.db（拆分前）。

    ★★ 2026-10-16 增补警告：拆分后 canonical 库里**已无**行情三表。若有人在
       `cycle_research.db` 里新建了同名表并落到这个分支，快照会**静默**从一个
       非权威库生成（不报错、只是内容错）→ 在此显式断言三表非空，避免错源。
    """
    if explicit:
        if not os.path.exists(explicit):
            raise SystemExit("源库不存在: %s" % explicit)
        return explicit
    if os.path.exists(MARKET_DB):
        return MARKET_DB
    if os.path.exists(CANONICAL_DB):
        # 拆分后的正常克隆**不该**走到这里（canonical 无行情表）→ 走这里即异常
        conn = sqlite3.connect("file:%s?mode=ro" % CANONICAL_DB, uri=True)
        try:
            n = conn.execute("SELECT COUNT(*) FROM market_daily").fetchone()[0]
        except sqlite3.OperationalError:
            raise SystemExit(
                "FAIL: %s 中没有 market_daily 表 —— 拆分后行情只住在 %s。\n"
                "  ★ 请先恢复行情库：python research/scripts/restore_market_data.py --apply"
                % (os.path.relpath(CANONICAL_DB, ROOT), os.path.relpath(MARKET_DB, ROOT)))
        finally:
            conn.close()
        if n == 0:
            raise SystemExit(
                "FAIL: %s 的 market_daily 为 **0 行** —— 这不是有效的行情源。\n"
                "  ★ 请先恢复行情库：python research/scripts/restore_market_data.py --apply"
                % os.path.relpath(CANONICAL_DB, ROOT))
        print("  ★ 警告：从 canonical 库读取行情三表（%d 行）—— 拆分后这不该发生，"
              "请确认源库选择是否符合预期。" % n)
        return CANONICAL_DB
    raise SystemExit("找不到源库（既无 market_data.db 也无 cycle_research.db）")


def table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r[1] for r in conn.execute("PRAGMA table_info(%s)" % table)]


def schema_sql(conn: sqlite3.Connection) -> str:
    """三表 DDL（含索引），取自源库 sqlite_master —— 保证恢复后 schema **逐字节**一致。"""
    out: list[str] = []
    for t in MARKET_TABLES:
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()
        if not row or not row[0]:
            raise SystemExit("源库缺少表: %s" % t)
        out.append(row[0].rstrip().rstrip(";") + ";")
    for name, tbl in conn.execute(
            "SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL "
            "ORDER BY tbl_name, name"):
        if tbl in MARKET_TABLES:
            sql = conn.execute("SELECT sql FROM sqlite_master WHERE name=?", (name,)).fetchone()[0]
            out.append(sql.rstrip().rstrip(";") + ";")
    return "\n\n".join(out) + "\n"


def fmt(v) -> str:
    """单元格 → 文本。★ REAL 用 repr()（精确 round-trip）；None → 空（NULL）。"""
    if v is None:
        return ""
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        if v == "":
            raise SystemExit("★ 源库出现空字符串（与 NULL 无法区分）—— 拒绝生成快照")
        return v
    raise SystemExit("未知类型 %r" % type(v))


def write_csv_gz(path: str, columns: list[str], rows) -> tuple[int, int, str]:
    """写 gzip CSV，返回 (rows, bytes, sha256)。★ mtime=0 且不写原文件名 → 可复现。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0, compresslevel=9) as gz:
        with io.TextIOWrapper(gz, encoding="utf-8", newline="") as txt:
            w = csv.writer(txt, lineterminator="\n")
            w.writerow(columns)
            n = 0
            for row in rows:
                w.writerow([fmt(v) for v in row])
                n += 1
    data = buf.getvalue()
    with open(path, "wb") as fh:
        fh.write(data)
    return n, len(data), hashlib.sha256(data).hexdigest()


def build(conn: sqlite3.Connection, out_dir: str) -> dict:
    manifest: dict = {
        "artifact": "market_data_snapshot",
        "format_version": FORMAT_VERSION,
        "position": ("★ 行情三表的**便携快照** —— 干净克隆在**无网络**下据此恢复 "
                     "`research/database/market_data.db`。权威写入方仍是抓取器；本快照是它的**可版本化镜像**。"),
        "why": ("`cycle_research.db` 曾达 66 MB（market_daily 373k 行占绝大部分），超过 GitHub 建议的 50 MB。"
                "行情三表拆出为不入库的本地 `market_data.db`，由本快照恢复。"),
        "source_tables": list(MARKET_TABLES),
        "sharded_table": SHARDED_TABLE,
        "shard_key": "trade_date 的年份（YYYY）",
        "float_encoding": "Python repr() —— 精确 round-trip，**不得**四舍五入",
        "null_encoding": "空字段（CSV 空列）",
        "gzip": {"mtime": 0, "filename": "", "compresslevel": 9},
        "restore": {
            "script": "research/scripts/restore_market_data.py",
            "check": "python research/scripts/restore_market_data.py --check",
            "apply": "python research/scripts/restore_market_data.py --apply",
            "target": "research/database/market_data.db",
        },
        "tables": {},
    }

    for t in MARKET_TABLES:
        cols = table_columns(conn, t)
        if t == SHARDED_TABLE:
            years = [r[0] for r in conn.execute(
                "SELECT DISTINCT substr(trade_date,1,4) y FROM %s ORDER BY y" % t)]
            shards, total = {}, 0
            for y in years:
                sql = ("SELECT %s FROM %s WHERE trade_date LIKE ? ORDER BY %s"
                       % (",".join(cols), t, ",".join(cols)))
                rows = conn.execute(sql, (y + "-%",))
                rel = "%s/%s.csv.gz" % (t, y)
                n, b, h = write_csv_gz(os.path.join(out_dir, rel), cols, rows)
                shards[y] = {"file": rel, "rows": n, "bytes": b, "sha256": h}
                total += n
            manifest["tables"][t] = {
                "columns": cols, "rows": total, "shard_count": len(shards), "shards": shards,
                "bytes": sum(s["bytes"] for s in shards.values()),
            }
        else:
            rows = conn.execute("SELECT %s FROM %s ORDER BY %s" % (",".join(cols), t, cols[0]))
            rel = "%s.csv.gz" % t
            n, b, h = write_csv_gz(os.path.join(out_dir, rel), cols, rows)
            manifest["tables"][t] = {
                "columns": cols, "rows": n, "shard_count": 1,
                "shards": {"all": {"file": rel, "rows": n, "bytes": b, "sha256": h}},
                "bytes": b,
            }

    ddl = schema_sql(conn)
    with open(os.path.join(out_dir, "market_schema.sql"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(ddl)
    manifest["schema_file"] = "market_schema.sql"
    manifest["schema_sha256"] = hashlib.sha256(ddl.encode("utf-8")).hexdigest()

    total_bytes = sum(v["bytes"] for v in manifest["tables"].values())
    manifest["total_bytes"] = total_bytes
    manifest["total_rows"] = sum(v["rows"] for v in manifest["tables"].values())

    with open(os.path.join(out_dir, "MANIFEST.json"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    return manifest


def read_manifest(path: str) -> dict:
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def check(conn: sqlite3.Connection, snap_dir: str) -> int:
    """校验：快照自身完整性 + 与源库一致性。返回 0/1。"""
    mpath = os.path.join(snap_dir, "MANIFEST.json")
    if not os.path.exists(mpath):
        print("  FAIL: 快照不存在（%s）" % snap_dir)
        return 1
    m = read_manifest(mpath)
    bad = 0

    for t, meta in m["tables"].items():
        for key, sh in meta["shards"].items():
            p = os.path.join(snap_dir, sh["file"])
            if not os.path.exists(p):
                print("  FAIL: 缺分片 %s" % sh["file"]); bad += 1; continue
            data = open(p, "rb").read()
            h = hashlib.sha256(data).hexdigest()
            if h != sh["sha256"]:
                print("  FAIL: 分片哈希不符 %s" % sh["file"]); bad += 1
            if len(data) != sh["bytes"]:
                print("  FAIL: 分片字节数不符 %s" % sh["file"]); bad += 1
    # schema
    sp = os.path.join(snap_dir, m["schema_file"])
    if not os.path.exists(sp):
        print("  FAIL: 缺 %s" % m["schema_file"]); bad += 1
    elif hashlib.sha256(open(sp, "rb").read()).hexdigest() != m["schema_sha256"]:
        print("  FAIL: schema 哈希不符"); bad += 1

    if bad:
        print("  结果: FAIL（%d 项）" % bad)
        return 1

    # 与源库比对（行数 + 内容哈希）
    for t in MARKET_TABLES:
        cols = table_columns(conn, t)
        live = conn.execute("SELECT count(*) FROM %s" % t).fetchone()[0]
        if live != m["tables"][t]["rows"]:
            print("  FAIL: %s 行数 源库=%d 快照=%d" % (t, live, m["tables"][t]["rows"])); bad += 1
    if bad:
        print("  结果: FAIL（与源库不一致）")
        return 1

    print("  结果: PASS（%d 表 · %d 行 · %.2f MiB · 分片哈希全部一致）"
          % (len(MARKET_TABLES), m["total_rows"], m["total_bytes"] / 1048576))
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="行情便携快照 —— 生成/校验")
    ap.add_argument("--source", help="源库路径（默认自动：market_data.db → cycle_research.db）")
    ap.add_argument("--out", default=SNAPSHOT_DIR, help="快照输出目录")
    ap.add_argument("--check", action="store_true", help="只校验，不写盘")
    a = ap.parse_args(argv)

    src = resolve_source(a.source)
    conn = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    try:
        if a.check:
            print("=" * 74)
            print("校验行情快照：%s" % a.out)
            print("=" * 74)
            return check(conn, a.out)

        # ★ 先写临时目录再原子替换 → 失败不会留下半成品
        with tempfile.TemporaryDirectory(dir=os.path.dirname(a.out) or ".") as tmp:
            stage = os.path.join(tmp, "snapshot")
            os.makedirs(stage)
            m = build(conn, stage)
            if os.path.isdir(a.out):
                for name in os.listdir(a.out):
                    p = os.path.join(a.out, name)
                    if os.path.isdir(p):
                        shutil.rmtree(p)
                    else:
                        os.remove(p)
            else:
                os.makedirs(a.out, exist_ok=True)
            for name in os.listdir(stage):
                s, d = os.path.join(stage, name), os.path.join(a.out, name)
                if os.path.isdir(s):
                    os.makedirs(d, exist_ok=True)
                    for f in os.listdir(s):
                        os.replace(os.path.join(s, f), os.path.join(d, f))
                else:
                    os.replace(s, d)

        print("=" * 74)
        print("行情快照已生成：%s" % a.out)
        print("=" * 74)
        print("  源库      : %s" % os.path.relpath(src, ROOT))
        for t, meta in sorted(m["tables"].items()):
            print("  %-18s %8d 行 · %2d 分片 · %8.2f KiB"
                  % (t, meta["rows"], meta["shard_count"], meta["bytes"] / 1024))
        print("  %-18s %8d 行 · %8.2f MiB" % ("合计", m["total_rows"], m["total_bytes"] / 1048576))
        print()
        print("  恢复命令  : python research/scripts/restore_market_data.py --apply")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
