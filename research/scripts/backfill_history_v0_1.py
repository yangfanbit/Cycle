#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""backfill_history_v0_1.py —— 历史行情**批量回补**（v0.34 第一阶段收官）。

## 回补什么

1. **行业板块多年日线**：同花顺 `bk_881xxx` 的**按年**接口（实测 2010 年起可用），
   140 个行业板块 × 2010–2026；
2. **全市场个股日线**：新浪 `CN_MarketData.getKLineData`（一次 3000 根，约 2014 起），
   标的来自新浪全 A 列表（5,500+ 只）；
3. **基准**：沪深300 / 上证 / 深证 / 创业板指。

## 存储

写入 `research/database/history_scan.db`（**与 `market_data.db` 同列语义**：`scan_daily` 的
`open/high/low/close/volume` 与 `market_daily` 一致，`price_type` 固定 `raw`）。

★ 为什么单独一个库：`market_data.db` 的 3 张表参与**行情快照恢复**（`make_market_snapshot --check`
  逐表哈希），直接加表会破坏该合同。扫描层只读、可重建，故独立成库，并在 `scan_meta` 里写清来源与口径；
  事件相关研究仍以 `market_data.db` 为准。

## 可重复 / 断点续传

- 每个标的抓完立即提交，`scan_series.last_date/rows/fetched_at` 记录进度；
- 重跑时按 `--since-days` 只补最近一段，或用 `--force` 全量重取；
- 单标的失败只记 `error`，不中断整批。

用法：
    python research/scripts/backfill_history_v0_1.py --boards            # 板块多年（默认 2010-2026）
    python research/scripts/backfill_history_v0_1.py --stocks --limit 500
    python research/scripts/backfill_history_v0_1.py --stocks            # 全市场（可断点续传）
    python research/scripts/backfill_history_v0_1.py --report
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(REPO, "research", "database", "history_scan.db")
UA = {"User-Agent": "Mozilla/5.0"}
PACING = 0.18
START_YEAR = 2010

SCHEMA = """
CREATE TABLE IF NOT EXISTS scan_series (
  series_id TEXT PRIMARY KEY,
  name TEXT, kind TEXT,          -- industry_board / stock / index
  provider TEXT, symbol TEXT,
  price_type TEXT DEFAULT 'raw',
  first_date TEXT, last_date TEXT, rows INTEGER,
  fetched_at TEXT, status TEXT, note TEXT
);
CREATE TABLE IF NOT EXISTS scan_daily (
  series_id TEXT, trade_date TEXT,
  open REAL, high REAL, low REAL, close REAL, volume REAL,
  PRIMARY KEY (series_id, trade_date)
);
CREATE TABLE IF NOT EXISTS scan_meta (k TEXT PRIMARY KEY, v TEXT);
"""


def _get(url: str, referer: str | None = None, timeout: int = 25) -> bytes:
    h = dict(UA)
    if referer:
        h["Referer"] = referer
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        return r.read()


def conn():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB)
    c.executescript(SCHEMA)
    return c


def refresh_stats(c, sid):
    """★ 写完后按**数据库实际内容**回填 rows/first_date/last_date（不再相信传入值）。"""
    n, f, l = c.execute(
        "SELECT COUNT(*), MIN(trade_date), MAX(trade_date) FROM scan_daily WHERE series_id=?", (sid,)).fetchone()
    c.execute("UPDATE scan_series SET rows=?, first_date=?, last_date=? WHERE series_id=?", (n, f, l, sid))
    return n, f, l


def upsert_series(c, sid, name, kind, provider, symbol, rows, status="OK", note=None):
    if not rows:
        # ★★ v0.60：**不得**用空结果覆盖已有序列的元数据。
        #   原实现无条件 `INSERT OR REPLACE ... rows=0 / first=NULL / last=NULL`，
        #   于是一次限流或空响应就会把该序列从所有 `WHERE rows>0` 的查询里抹掉
        #   （数据还在 `scan_daily`，但扫描层再也看不到它）。
        #   现在：已有数据的序列只更新状态与说明，不动 rows/first/last。
        old = c.execute("SELECT rows FROM scan_series WHERE series_id=?", (sid,)).fetchone()
        if old and old[0]:
            c.execute("UPDATE scan_series SET status=?, note=? WHERE series_id=?",
                      (status, note or "本轮抓取为空 —— 保留既有数据，未清零", sid))
            c.commit()
            return
        c.execute("INSERT OR REPLACE INTO scan_series VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (sid, name, kind, provider, symbol, "raw", None, None, 0,
                   time.strftime("%Y-%m-%d %H:%M:%S"), status, note))
        return
    c.executemany(
        "INSERT INTO scan_daily VALUES (?,?,?,?,?,?,?) ON CONFLICT(series_id,trade_date) DO UPDATE SET "
        "open=excluded.open, high=excluded.high, low=excluded.low, close=excluded.close, volume=excluded.volume",
        [(sid, r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows])
    c.execute("INSERT OR REPLACE INTO scan_series VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
              (sid, name, kind, provider, symbol, "raw", rows[0][0], rows[-1][0], len(rows),
               time.strftime("%Y-%m-%d %H:%M:%S"), status, note))
    refresh_stats(c, sid)
    c.commit()


def board_list() -> list:
    """板块清单：优先列表页；**403 时退回已有缓存**（缓存里是上次成功抓到的板块代码）。"""
    cache = os.path.join(REPO, "research", "data", "forward_scan", "cache_v0_1.json")
    try:
        t = _get("http://q.10jqka.com.cn/thshy/", referer="http://q.10jqka.com.cn").decode("gbk", "replace")
    except Exception:
        if os.path.exists(cache):
            c = json.load(open(cache, encoding="utf-8")).get("boards") or {}
            print("  ★ 列表页不可用 → 用缓存板块 %d 个" % len(c), flush=True)
            return [{"code": k, "name": v.get("name") or k} for k, v in c.items()]
        raise
    seen, out = set(), []
    for code, name in re.findall(r"/thshy/detail/code/(\d+)/\"[^>]*>([^<]{1,20})<", t):
        if code in seen:
            continue
        seen.add(code)
        out.append({"code": code, "name": name.strip()})
    return out


def board_rows(code: str, years: range) -> list:
    rows = []
    for y in years:
        try:
            raw = _get("http://d.10jqka.com.cn/v6/line/bk_%s/01/%d.js" % (code, y),
                       referer="http://q.10jqka.com.cn").decode("utf-8", "replace")
            m = re.search(r'"data":"([^"]*)"', raw)
            if not m:
                continue
            for seg in m.group(1).split(";"):
                p = seg.split(",")
                if len(p) < 7:
                    continue
                rows.append([p[0], float(p[1]), float(p[2]), float(p[3]), float(p[4]), float(p[5])])
        except Exception:
            continue
        time.sleep(PACING)
    return sorted({r[0]: r for r in rows}.values(), key=lambda r: r[0])


def sina_kline(symbol: str, datalen: int = 3000) -> list:
    url = ("https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
           "CN_MarketData.getKLineData?symbol=%s&scale=240&ma=no&datalen=%d" % (symbol, datalen))
    d = json.loads(_get(url, referer="https://finance.sina.com.cn").decode("utf-8", "replace"))
    return sorted({x["day"]: [x["day"], float(x["open"]), float(x["high"]), float(x["low"]),
                              float(x["close"]), float(x["volume"])] for x in d}.values(),
                  key=lambda r: r[0])


def backfill_boards(c, years):
    boards = board_list()
    c.execute("INSERT OR REPLACE INTO scan_meta VALUES ('boards_listed', ?)", (str(len(boards)),))
    done = 0
    for b in boards:
        sid = "BK" + b["code"]
        rows = board_rows(b["code"], years)
        upsert_series(c, sid, b["name"], "industry_board", "ths",
                      "bk_%s" % b["code"], rows,
                      status="OK" if rows else "EMPTY",
                      note=None if rows else "该板块按年接口无数据")
        done += 1
        if done % 10 == 0:
            print("  boards %d/%d（最新 %s %s 行）" % (done, len(boards), b["name"], len(rows)), flush=True)
    c.execute("INSERT OR REPLACE INTO scan_meta VALUES ('boards_years', ?)",
              ("%d-%d" % (years.start, years.stop - 1),))
    c.commit()
    return done


def backfill_stocks(c, limit=None, force=False, datalen=3000, since_days=45):
    uni_path = os.path.join(REPO, "research", "data", "forward_scan", "universe_v0_1.json")
    if os.path.exists(uni_path):
        universe = json.load(open(uni_path, encoding="utf-8"))
    else:
        universe = []
        page = 1
        while page <= 80:
            url = ("https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
                   "Market_Center.getHQNodeData?page=%d&num=80&sort=symbol&asc=1&node=hs_a" % page)
            try:
                d = json.loads(_get(url, referer="https://finance.sina.com.cn").decode("utf-8", "replace"))
            except Exception:
                break
            if not d:
                break
            universe.extend(d)
            page += 1
            time.sleep(0.12)
    done = skipped = 0
    for u in universe:
        sym, name = u.get("symbol"), u.get("name")
        if not sym:
            continue
        if limit and done >= limit:
            break
        row = c.execute("SELECT last_date, rows FROM scan_series WHERE series_id=?", (sym,)).fetchone()
        # ★★ 默认**增量刷新最近一段**（不再「有数据就永久跳过」）；--force 才整段重取
        has = bool(row and row[1])
        if has and not force:
            if row[0] and row[0] >= _latest_trade_day(c):
                skipped += 1
                continue
            datalen_use = max(60, int(since_days * 5 / 7) + 10)
        else:
            datalen_use = datalen
        rows = []
        for attempt in range(3):
            try:
                rows = sina_kline(sym, datalen_use)
                if rows:
                    break
            except Exception:
                time.sleep(0.5 * (attempt + 1))
        try:
            if has and not force:
                old = [list(r) for r in c.execute(
                    "SELECT trade_date, open, high, low, close, volume FROM scan_daily WHERE series_id=?", (sym,))]
                rows = merge_rows(old, rows)
            upsert_series(c, sym, name, "stock", "sina", sym, rows,
                          status="OK" if rows else "EMPTY")
        except Exception as exc:  # noqa: BLE001
            c.execute("INSERT OR REPLACE INTO scan_series VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                      (sym, name, "stock", "sina", sym, "raw", None, None, 0,
                       time.strftime("%Y-%m-%d %H:%M:%S"), "ERROR", "%s: %s" % (type(exc).__name__, str(exc)[:80])))
            c.commit()
        done += 1
        if done % 100 == 0:
            print("  stocks %d（累计已存 %d，跳过 %d）" % (done, c.execute(
                "SELECT COUNT(*) FROM scan_series WHERE kind='stock' AND rows>0").fetchone()[0], skipped), flush=True)
        time.sleep(PACING)
    c.commit()
    return done


def backfill_indices(c):
    for sid, name, sym in (("CSI300", "沪深300", "sh000300"), ("SSE", "上证综指", "sh000001"),
                           ("SZSE", "深证成指", "sz399001"), ("CHINEXT", "创业板指", "sz399006")):
        rows = sina_kline(sym, 3000)
        upsert_series(c, sid, name, "index", "sina", sym, rows, status="OK" if rows else "EMPTY")
        time.sleep(PACING)
    c.commit()


def _latest_trade_day(c):
    r = c.execute("SELECT MAX(trade_date) FROM scan_daily WHERE series_id='CSI300'").fetchone()
    return (r[0] or "9999-99-99").replace("-", "") if r[0] else "99999999"


def merge_rows(old, new):
    """按日期合并（新值覆盖旧值）。

    ★★ v0.60：日期格式**沿用既有行的格式**（带横线 / 紧凑），**不得混写**。
    原实现无条件统一成紧凑格式，而库内个股历史是**带横线**格式 →
    一次 `--stocks` 刷新就把每只股票的整段历史**复制成两份**
    （实测 2,520 只多出 5,155,656 行重复，已清理）。当日增量请用
    `update_scan_stocks_v0_1.py`（只追加、保格式），本函数仅作整段重建时使用。
    """
    dashed = any("-" in str(r[0]) for r in old) if old else True

    def _k(d):
        s = str(d)
        return s if dashed else s.replace("-", "")

    m = {}
    for r in old:
        m[_k(r[0])] = [_k(r[0]), r[1], r[2], r[3], r[4], r[5]]
    for r in new:
        m[_k(r[0])] = [_k(r[0]), r[1], r[2], r[3], r[4], r[5]]
    return [m[d] for d in sorted(m)]


def report():
    if not os.path.exists(DB):
        print("FAIL: 数据库不存在")
        return 1
    c = sqlite3.connect(DB)
    for kind in ("industry_board", "stock", "index"):
        n, rows, first, last = c.execute(
            "SELECT COUNT(*), SUM(rows), MIN(first_date), MAX(last_date) FROM scan_series "
            "WHERE kind=? AND rows>0", (kind,)).fetchone()
        print("%-16s 序列 %4d · 行数 %8s · 覆盖 %s → %s" % (kind, n or 0, rows or 0, first, last))
    print("meta:", dict(c.execute("SELECT k,v FROM scan_meta").fetchall()))
    c.close()
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description="历史行情批量回补")
    ap.add_argument("--boards", action="store_true")
    ap.add_argument("--stocks", action="store_true")
    ap.add_argument("--indices", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--start-year", type=int, default=START_YEAR)
    ap.add_argument("--end-year", type=int, default=2026)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args(argv)
    if a.report:
        return report()
    c = conn()
    if a.indices:
        backfill_indices(c)
    if a.boards:
        backfill_boards(c, range(a.start_year, a.end_year + 1))
    if a.stocks:
        backfill_stocks(c, limit=a.limit, force=a.force)
    c.close()
    return report()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
