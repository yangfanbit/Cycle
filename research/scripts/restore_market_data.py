#!/usr/bin/env python3
"""行情数据库 —— **恢复入口**（干净克隆 → 本地 `market_data.db`）。

## 定位

`research/database/market_data.db` **不入 Git**（本地生成物）。干净克隆在**无网络**前提下，
用版本管理的**便携快照**（`research/data/market/snapshot/`）把它完整恢复出来。

★ 恢复**不依赖**实时行情接口，也不依赖本机残留的 `market_data.db` 或被忽略的 `*.csv`。

## 用法

```bash
python research/scripts/restore_market_data.py --check    # 校验快照 + 已恢复库是否与快照**完全一致**
python research/scripts/restore_market_data.py --apply    # 恢复（幂等：已一致则 no-op）
python research/scripts/restore_market_data.py --apply --force   # 库与快照不一致时强制重建
```

## 退出码

`0` 成功 · `1` 失败（**明确失败**，不静默跳过）。CI 依赖行情表的门禁**必须**在 `--apply` 之后运行。
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAPSHOT_DIR = os.path.join(ROOT, "data", "market", "snapshot")
TARGET_DB = os.path.join(ROOT, "database", "market_data.db")

sys.path.insert(0, HERE)
from make_market_snapshot import (  # noqa: E402
    MARKET_TABLES, read_manifest, schema_sql, table_columns,
)


# --------------------------------------------------------------------- 快照读取

def iter_shard_rows(path: str):
    """逐行读 gzip CSV，返回 (columns, row_iterator)。空字段 → None（NULL）。"""
    with gzip.open(path, "rt", encoding="utf-8", newline="") as fh:
        rd = csv.reader(fh)
        cols = next(rd)
        for row in rd:
            yield cols, [None if c == "" else c for c in row]


def snapshot_columns(m: dict, table: str) -> list[str]:
    return list(m["tables"][table]["columns"])


# --------------------------------------------------------------------- 恢复

def restore(snap_dir: str, target: str, force: bool) -> int:
    m = read_manifest(os.path.join(snap_dir, "MANIFEST.json"))

    with io.open(os.path.join(snap_dir, m["schema_file"]), encoding="utf-8") as fh:
        ddl = fh.read()

    conn = sqlite3.connect(target)
    try:
        conn.execute("PRAGMA foreign_keys=OFF")
        existing = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        present = [t for t in MARKET_TABLES if t in existing]

        if present and not force:
            if verify_against_snapshot(conn, snap_dir) == 0:
                print("  已与快照一致 → no-op（未改动 %s）" % os.path.relpath(target, ROOT))
                return 0
            print("  ★ 目标库已存在但与快照**不一致**。")
            print("    若要按快照重建（会丢弃本地未快照化的行情），请加 `--force`。")
            return 1

        # 先删依赖方，再删被依赖方
        for t in ("market_daily", "trading_calendar", "market_series"):
            conn.execute("DROP TABLE IF EXISTS %s" % t)
        conn.commit()

        # DDL 取自快照（含索引），语句间以 `;` 结尾
        for stmt in [s.strip() for s in ddl.split(";") if s.strip()]:
            conn.execute(stmt)
        conn.commit()

        for t in MARKET_TABLES:
            cols = snapshot_columns(m, t)
            ph = ",".join("?" * len(cols))
            sql = "INSERT INTO %s (%s) VALUES (%s)" % (t, ",".join(cols), ph)
            total = 0
            for shard in sorted(m["tables"][t]["shards"].values(), key=lambda s: s["file"]):
                p = os.path.join(snap_dir, shard["file"])
                batch: list[tuple] = []
                for _cols, row in iter_shard_rows(p):
                    batch.append(tuple(row))
                    if len(batch) >= 20000:
                        conn.executemany(sql, batch); total += len(batch); batch.clear()
                if batch:
                    conn.executemany(sql, batch); total += len(batch)
            conn.commit()
            print("  %-18s %8d 行" % (t, total))

        bad = conn.execute("PRAGMA foreign_key_check").fetchall()
        if bad:
            print("  FAIL: 外键校验失败 %d 项" % len(bad)); return 1
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            print("  FAIL: integrity_check 未通过"); return 1
        return 0
    finally:
        conn.close()


# --------------------------------------------------------------------- 校验

def verify_snapshot_files(snap_dir: str, m: dict) -> int:
    bad = 0
    for t, meta in m["tables"].items():
        for key, sh in meta["shards"].items():
            p = os.path.join(snap_dir, sh["file"])
            if not os.path.exists(p):
                print("  FAIL: 缺分片 %s" % sh["file"]); bad += 1; continue
            data = open(p, "rb").read()
            if hashlib.sha256(data).hexdigest() != sh["sha256"]:
                print("  FAIL: 哈希不符 %s" % sh["file"]); bad += 1
            elif len(data) != sh["bytes"]:
                print("  FAIL: 字节数不符 %s" % sh["file"]); bad += 1
    sp = os.path.join(snap_dir, m["schema_file"])
    if not os.path.exists(sp):
        print("  FAIL: 缺 %s" % m["schema_file"]); bad += 1
    elif hashlib.sha256(open(sp, "rb").read()).hexdigest() != m["schema_sha256"]:
        print("  FAIL: schema 哈希不符"); bad += 1
    return bad


def verify_against_snapshot(conn: sqlite3.Connection, snap_dir: str) -> int:
    """★ 端到端一致性：从**目标库**重新生成快照到临时目录，逐分片比对 sha256。

    这比「比行数」强得多 —— 它证明**每一个 REAL 值逐位相同**（见 make_market_snapshot 的 repr 编码）。
    """
    from make_market_snapshot import build  # 局部导入，避免顶层循环
    m = read_manifest(os.path.join(snap_dir, "MANIFEST.json"))
    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        regen = build(conn, tmp)
        for t in MARKET_TABLES:
            a, b = m["tables"][t], regen["tables"][t]
            if a["rows"] != b["rows"]:
                print("  FAIL: %s 行数 快照=%d 目标库=%d" % (t, a["rows"], b["rows"])); bad += 1
            for key in a["shards"]:
                if key not in b["shards"]:
                    print("  FAIL: %s 缺分片 %s" % (t, key)); bad += 1; continue
                if a["shards"][key]["sha256"] != b["shards"][key]["sha256"]:
                    print("  FAIL: %s/%s 内容哈希不符" % (t, key)); bad += 1
        if m.get("schema_sha256") != regen.get("schema_sha256"):
            print("  FAIL: schema 与目标库不一致"); bad += 1
    return bad


def check(snap_dir: str, target: str) -> int:
    mpath = os.path.join(snap_dir, "MANIFEST.json")
    if not os.path.exists(mpath):
        print("  FAIL: 快照不存在：%s" % snap_dir)
        print("        （它应当被 Git 跟踪；若缺失说明克隆不完整）")
        return 1
    m = read_manifest(mpath)

    print("  [1/2] 快照自身完整性")
    bad = verify_snapshot_files(snap_dir, m)
    if bad:
        return 1
    print("        PASS · %d 表 · %d 行 · %.2f MiB"
          % (len(m["tables"]), m["total_rows"], m["total_bytes"] / 1048576))

    print("  [2/2] 已恢复库与快照的一致性")
    if not os.path.exists(target):
        print("        FAIL: %s 不存在 —— 请先运行：" % os.path.relpath(target, ROOT))
        print("              python research/scripts/restore_market_data.py --apply")
        return 1
    conn = sqlite3.connect("file:%s?mode=ro" % target, uri=True)
    try:
        bad = verify_against_snapshot(conn, snap_dir)
    finally:
        conn.close()
    if bad:
        return 1
    print("        PASS · 逐分片内容哈希一致（含全部 REAL 逐位相同）")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="行情数据库恢复入口")
    ap.add_argument("--check", action="store_true", help="校验快照 + 已恢复库（不写盘）")
    ap.add_argument("--apply", action="store_true", help="从快照恢复 market_data.db（幂等）")
    ap.add_argument("--force", action="store_true", help="与快照不一致时强制重建")
    ap.add_argument("--snapshot", default=SNAPSHOT_DIR)
    ap.add_argument("--target", default=TARGET_DB)
    a = ap.parse_args(argv)

    if not a.check and not a.apply:
        ap.print_help()
        return 2

    print("=" * 74)
    if a.apply:
        print("恢复行情数据库 → %s" % os.path.relpath(a.target, ROOT))
        print("=" * 74)
        rc = restore(a.snapshot, a.target, a.force)
        if rc:
            print("  结果: FAIL")
            return rc
        print("  结果: 已恢复")
    if a.check:
        if a.apply:
            print()
        print("=" * 74)
        print("校验行情数据库")
        print("=" * 74)
        rc = check(a.snapshot, a.target)
        print("  结果: %s" % ("PASS" if rc == 0 else "FAIL"))
        return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
