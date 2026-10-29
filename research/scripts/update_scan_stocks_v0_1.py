#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""update_scan_stocks_v0_1.py —— 个股日线**增量追加**（`history_scan.db` · `kind='stock'`）。

## 为什么不用 `backfill_history_v0_1.py --stocks`

那条路径会 `merge_rows(old, new)` 把**整段历史**读出来重写一遍，且 `merge_rows` 会把日期
统一成**紧凑格式**（`20261023`）；而 `scan_daily` 里的个股历史是**带横线格式**（`2026-10-23`）。
两者混用 = 同一个交易日被写成两行，一次刷新就把每只股票的历史**复制一份**
（实测：2,520 只股票多出 5,155,656 行重复）。见 `docs/PROJECT_STATE.md` v0.60 的教训记录。

## 本脚本的口径（与 `update_market_data_current_v0_1.py` 一致）

- **只插入 `trade_date > 库内最大日` 的行**，既有行一律不动（不重写、不重算复权）
- 日期格式**沿用该序列既有格式**（带横线 / 紧凑），不混写
- 追加前做**同日收盘重叠校验**：远端同日收盘与库内不一致 → 该序列跳过并报告
  （远端基准变了，宁可不动历史）
- 单只失败只记录，不中断整批，**不补造**
- 串行 + 节流（新浪突发请求会限流）

## 用法

    python research/scripts/update_scan_stocks_v0_1.py               # 只报告
    python research/scripts/update_scan_stocks_v0_1.py --write       # 追加写入
    python research/scripts/update_scan_stocks_v0_1.py --limit 50 --write
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(REPO, "research", "database", "history_scan.db")
BENCH = "CSI300"
PACING = 0.18
DATALEN = 60          # 只取最近 60 根，够覆盖任何合理的追赶缺口

UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"}


def _norm(d: str) -> str:
    return d if "-" in d else "%s-%s-%s" % (d[:4], d[4:6], d[6:])


def target_day(con) -> str:
    """目标交易日 = 基准（CSI300）最后一根日线（**不写死**）。"""
    d = con.execute("SELECT MAX(trade_date) FROM scan_daily WHERE series_id=?", (BENCH,)).fetchone()[0]
    if not d:
        raise SystemExit("FAIL: 缺基准 %s" % BENCH)
    return _norm(d)


def fetch(symbol: str, datalen: int = DATALEN, retries: int = 3) -> list:
    """新浪日线 → [(date, open, high, low, close, volume)]，日期**带横线**。"""
    url = ("https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
           "CN_MarketData.getKLineData?symbol=%s&scale=240&ma=no&datalen=%d" % (symbol, datalen))
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
                raw = r.read().decode("utf-8", "replace")
            d = json.loads(raw)
            if not isinstance(d, list):
                return []
            return sorted({x["day"]: [x["day"], float(x["open"]), float(x["high"]),
                                      float(x["low"]), float(x["close"]), float(x["volume"])]
                           for x in d}.values(), key=lambda x: x[0])
        except Exception as exc:  # noqa: BLE001
            last = "%s: %s" % (type(exc).__name__, str(exc)[:60])
            time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(last or "unknown")


def fmt_of(con, sid: str) -> str:
    """该序列既有的日期格式：带横线 or 紧凑（**沿用，不混写**）。"""
    r = con.execute("SELECT trade_date FROM scan_daily WHERE series_id=? LIMIT 1", (sid,)).fetchone()
    return "dashed" if (r and "-" in r[0]) else "compact"


def main(argv):
    ap = argparse.ArgumentParser(description="个股日线增量追加（只追加，不改历史）")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--pacing", type=float, default=PACING)
    a = ap.parse_args(argv)

    if not os.path.exists(DB):
        print("FAIL: 数据库不存在 %s" % DB)
        return 1
    con = sqlite3.connect(DB, timeout=60)
    # ★ 扫描库可重建 → 用 NORMAL 同步即可；**不设 WAL**（会在仓库内留下 -shm/-wal 污染 git）
    con.execute("PRAGMA synchronous=NORMAL")
    try:
        target = target_day(con)
        rows = con.execute(
            "SELECT series_id, name, symbol, last_date, rows FROM scan_series "
            "WHERE kind='stock' AND rows>0 ORDER BY series_id").fetchall()
        behind = [(s, n, sym, ld, rw) for s, n, sym, ld, rw in rows
                  if not ld or _norm(ld) < target]
        print("目标交易日: %s（基准 %s）" % (target, BENCH))
        print("个股序列 %d 只 · 已最新 %d · 落后 %d" % (len(rows), len(rows) - len(behind), len(behind)))
        if a.limit:
            behind = behind[:a.limit]
            print("★ --limit %d：本轮只处理前 %d 只" % (a.limit, len(behind)))
        if not behind:
            print("无需更新")
            return 0

        st = {"series": 0, "appended": 0, "uptodate": 0, "failed": 0, "overlap_skip": 0,
              "details": [], "failures": []}
        for i, (sid, name, sym, ld, rw) in enumerate(behind, 1):
            if not sym:
                st["failed"] += 1
                st["failures"].append((sid, "无 symbol"))
                continue
            try:
                bars = fetch(sym)
            except Exception as exc:  # noqa: BLE001
                st["failed"] += 1
                st["failures"].append((sid, str(exc)[:80]))
                continue
            finally:
                time.sleep(a.pacing)

            if not bars:
                st["failed"] += 1
                st["failures"].append((sid, "返回空（不当作『无行情』，记为失败）"))
                continue

            last_norm = _norm(ld) if ld else ""
            # ★ 重叠校验：同日收盘必须一致，否则远端基准变了 → 跳过，不改历史
            old_same = con.execute("SELECT close FROM scan_daily WHERE series_id=? AND trade_date=?",
                                   (sid, bars[-1][0])).fetchone()
            if old_same and old_same[0] and abs(old_same[0] - bars[-1][4]) > 1e-6:
                st["overlap_skip"] += 1
                st["details"].append((sid, "重叠不一致 %.4f vs %.4f → 跳过"
                                      % (old_same[0], bars[-1][4])))
                continue

            new = [b for b in bars if b[0] > last_norm]
            if not new:
                st["uptodate"] += 1
                continue
            fmt = fmt_of(con, sid)
            payload = [(sid, b[0] if fmt == "dashed" else b[0].replace("-", ""),
                        b[1], b[2], b[3], b[4], b[5]) for b in new]
            if a.write:
                con.executemany("INSERT INTO scan_daily VALUES (?,?,?,?,?,?,?) "
                                "ON CONFLICT(series_id,trade_date) DO NOTHING", payload)
                r = con.execute("SELECT COUNT(*), MIN(trade_date), MAX(trade_date) "
                                "FROM scan_daily WHERE series_id=?", (sid,)).fetchone()
                con.execute("UPDATE scan_series SET rows=?, first_date=?, last_date=? WHERE series_id=?",
                            (r[0], r[1], r[2], sid))
                # ★ 批量提交：每只都 commit 会把 1.3 GB 库的 journal fsync 变成瓶颈
                #   （实测 3.1/s → 1.8/s）。每 50 只提交一次；中断最多丢 50 只，重跑即可续。
                if (st["series"] % 50) == 0:
                    con.commit()
            st["series"] += 1
            st["appended"] += len(payload)
            if i % 500 == 0:
                print("  ...%d/%d（累计追加 %d 行，失败 %d）"
                      % (i, len(behind), st["appended"], st["failed"]), flush=True)

        con.commit()          # ★ 收尾提交（批量提交的最后一截）
        print("\n完成：序列 %d · 追加 %d 行 · 已最新 %d · 重叠跳过 %d · 失败 %d%s"
              % (st["series"], st["appended"], st["uptodate"], st["overlap_skip"], st["failed"],
                 "" if a.write else "（dry-run，未写盘）"))
        if st["failures"]:
            print("★ 失败清单（**不补造**，下游必须按「陈旧/不可用」处理）：")
            for sid, why in st["failures"][:15]:
                print("   %-14s %s" % (sid, why))
            if len(st["failures"]) > 15:
                print("   …共 %d 条" % len(st["failures"]))
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
