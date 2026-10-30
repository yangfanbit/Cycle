#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""update_market_data_current_v0_1.py —— 把「当前市场」用到的日线更新到最新交易日（Wave 2.3）。

## 为什么需要它

`market_data.db` 里参与**当前前瞻观察**的序列长期停在旧日期（实测：流感题材参与者止于
**2026-01-30**，基准 `SH000300` 止于 **2026-10-20**）。而 `build_forward_observation_v0_1.py`
用「参与者最近 21 根」算 20 日超额、却用「`as_of` 最近 21 根」算基准 —— 两段窗口**完全不重叠**，
「超额」在口径上不成立。

## 它做什么（★ 只追加，不改历史）

1. 目标序列 = `forward_observation_v0_2.json` 的季节窗口所引用的题材参与者 + 基准 `SH000300`；
2. 对每条序列用腾讯 GTIMG 取**未复权日线**（`fq=""`，`day` 数组），
   **只插入 `trade_date > 已有最大日` 的行**，**不 UPDATE、不 DELETE 既有行**；
3. ★ 追加前做**重叠校验**：取回序列中与库内重叠的最后一行，`close` 必须一致（容差 1e-6），
   不一致 → 该序列**跳过并报错**（不静默改历史）；
4. 节流 `PACING` 秒，串行请求（GTIMG 突发请求会触发 WAF）；
5. `--check` 只读：报告每条序列「库内最新日 / 远端最新日 / 差几个交易日」。

## 字段口径（★ 腾讯 fqkline 固定 `[date, open, close, high, low, volume]`）

    F_DATE=0  F_OPEN=1  F_CLOSE=2  F_HIGH=3  F_LOW=4  F_VOL=5

禁止裸写 `rec[3]` 当 close（v0.27 踩过：把 high 当 close 算完整个审计）。

## 用法

    python research/scripts/update_market_data_current_v0_1.py            # 只报告（--check）
    python research/scripts/update_market_data_current_v0_1.py --write    # 追加写入
    python research/scripts/update_market_data_current_v0_1.py --write --limit 5   # 只跑前 N 条
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
DB = os.path.join(REPO, "research", "database", "market_data.db")
BENCH = "SH000300"

# ★★ v0.62：`web.ifzq.gtimg.cn` 的 `fqkline/get` 会被 WAF 拦截 —— 返回 **HTTP 501 + JS 挑战页**
#   （2026-10-30 实测：`web.` 前缀 100% 失败，同路径去掉 `web.` 后 200 正常）。
#   已验证 `ifzq.gtimg.cn` 返回**同一字段顺序、同一数值**（sh000300 2026-10-30 close 3985.500，
#   与新浪 3985.501 仅三位小数舍入差异）→ 换主机不换路径，不改变任何口径。
API = "https://ifzq.gtimg.cn/appstock/app/fqkline/get?"
HDRS = {"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"}
PACING = 1.2

# ★ 腾讯 fqkline 字段位置（固定顺序，必须用具名常量）
F_DATE, F_OPEN, F_CLOSE, F_HIGH, F_LOW, F_VOL = 0, 1, 2, 3, 4, 5


def _open_ro():
    return sqlite3.connect("file:%s?mode=ro" % DB, uri=True)


def latest_trade_day():
    """★ 用**已到最新交易日**的 `history_scan.db`（CSI300 日历）作为 as_of，
    而不是 `market_data.db` 自身 —— 否则「库内最新日」与「as_of」循环定义，永远判不出落后。
    """
    scan = os.path.join(REPO, "research", "database", "history_scan.db")
    if os.path.exists(scan):
        con = sqlite3.connect("file:%s?mode=ro" % scan, uri=True)
        try:
            d = con.execute("SELECT MAX(trade_date) FROM scan_daily WHERE series_id='CSI300'").fetchone()[0]
            if d:
                return d if "-" in d else "%s-%s-%s" % (d[:4], d[4:6], d[6:])
        finally:
            con.close()
    con = _open_ro()
    try:
        return con.execute("SELECT MAX(trade_date) FROM market_daily WHERE series_id=?",
                           (BENCH,)).fetchone()[0]
    finally:
        con.close()


def target_series():
    """forward_observation 的季节窗口所引用的题材参与者 + 基准。"""
    idx = json.loads(io.open(os.path.join(CURRENT, "historical_event_maps_index.json"), encoding="utf-8").read())
    # ★★ v0.60：原来硬编码 v0_2 —— 升到 v0_3/v0_4 后仍读旧文件，参与者集合会悄悄停在旧版。
    #   改为**取版本号最大的** forward_observation_v*.json。
    _fo = sorted(glob.glob(os.path.join(CURRENT, "forward_observation_v*.json")),
                 key=lambda p: int(re.sub(r"\D", "", os.path.basename(p)) or 0))
    if not _fo:
        raise SystemExit("找不到 forward_observation_v*.json")
    fo = json.loads(io.open(_fo[-1], encoding="utf-8").read())
    theme_files = {e["theme_id"]: e["file"] for e in idx["maps"]}
    out = set()
    for w in fo.get("seasonal_windows", {}).get("themes", []) or []:
        fn = theme_files.get(w["theme_id"])
        if not fn:
            continue
        doc = json.loads(io.open(os.path.join(CURRENT, fn), encoding="utf-8").read())
        for e in doc.get("events") or []:
            for p in e.get("participants") or []:
                out.add(p["security_id"])
    out.add(BENCH)
    return sorted(out)


def symbol_of(con, sid):
    r = con.execute("SELECT symbol, provider FROM market_series WHERE series_id=?", (sid,)).fetchone()
    return (r[0], r[1]) if r else (None, None)


def fetch_raw(symbol, beg, end, n=700, retries=3):
    param = "%s,day,%s,%s,%d," % (symbol, beg, end, n)   # fq 留空 = 未复权
    url = API + urllib.parse.urlencode({"param": param})
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            d = json.loads(urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore"))
            data = d.get("data")
            if isinstance(data, dict):
                node = data.get(symbol) or {}
                for k in ("day", "qfqday"):
                    if node.get(k):
                        return node[k], None
                return [], "empty"
            return [], "api:%s" % (d.get("msg") or "no-data")
        except Exception as ex:                     # noqa: BLE001
            if i == retries - 1:
                return [], "fetch-error: %s" % ex
            time.sleep(1.5 + i)
    return [], "unreachable"


def find_gaps(con, sid, min_days=60):
    """★ 返回内部空洞 `[(prev_date, next_date)]` —— 相邻两行间隔 > min_days 个自然日。"""
    ds = [r[0] for r in con.execute(
        "SELECT trade_date FROM market_daily WHERE series_id=? AND price_type='raw' ORDER BY trade_date", (sid,))]
    out = []
    for i in range(1, len(ds)):
        a = datetime.strptime(ds[i - 1], "%Y-%m-%d")
        b = datetime.strptime(ds[i], "%Y-%m-%d")
        if (b - a).days > min_days:
            out.append((ds[i - 1], ds[i]))
    return out


def append_rows(con, sid, parsed, db_last):
    """★ 只插入 `trade_date > db_last` 的行（不改历史）。返回追加行数。"""
    new = [x for x in parsed if x[0] > db_last]
    if not new:
        return 0
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    cur = con.executemany(
        "INSERT OR IGNORE INTO market_daily "
        "(series_id, trade_date, open, high, low, close, adj_close, price_type, volume, amount,"
        " data_source, retrieved_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        [(sid, d, o, h, l, c, None, "raw", v, None, "tencent_gtimg", now)
         for (d, o, h, l, c, v) in new])
    con.commit()
    return cur.rowcount if cur.rowcount and cur.rowcount > 0 else len(new)


def parse(ser):
    out = []
    for rec in ser:
        try:
            out.append((rec[F_DATE], float(rec[F_OPEN]), float(rec[F_HIGH]),
                        float(rec[F_LOW]), float(rec[F_CLOSE]), float(rec[F_VOL])))
        except (TypeError, ValueError, IndexError):
            continue
    out.sort(key=lambda x: x[0])
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--fill-gaps", action="store_true",
                    help="补内部空洞（相邻行间隔 > 60 天）：按缺口区间分段取数，只插入缺口内的日期")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args(argv)

    if not os.path.exists(DB):
        print("SKIP: market_data.db 不存在（不入库，需先 restore_market_data.py --apply）")
        return 0

    as_of = latest_trade_day()
    con = _open_ro()
    try:
        targets = target_series()
        rows = []
        for sid in targets:
            sym, prov = symbol_of(con, sid)
            mx, n = con.execute(
                "SELECT MAX(trade_date), COUNT(*) FROM market_daily WHERE series_id=? AND price_type='raw'",
                (sid,)).fetchone()
            rows.append({"sid": sid, "symbol": sym, "provider": prov, "db_last": mx, "rows": n})
    finally:
        con.close()
    if a.limit:
        rows = rows[:a.limit]

    print("基准最新交易日（库内）：%s" % as_of)
    print("目标序列：%d 条（forward_observation 季节窗口参与者 + 基准）\n" % len(rows))

    behind = [r for r in rows if r["db_last"] != as_of]
    print("库内已是最新的：%d 条 · 落后：%d 条" % (len(rows) - len(behind), len(behind)))
    for r in behind:
        print("  %-22s %-9s 库内 %s" % (r["sid"], r["symbol"] or "-", r["db_last"]))

    if not a.write:
        print("\n（--check 模式，未写入；加 --write 追加新交易日）")
        return 0
    if not behind and not a.fill_gaps:
        print("\n无需更新：全部已到 %s" % as_of)
        return 0
    if not behind:
        print("\n无新增交易日；继续执行 --fill-gaps")

    stats = {"series": 0, "appended": 0, "skipped": 0, "failed": 0, "details": []}
    print("\n开始追加（只插入 trade_date > 库内最大日 的行，不改历史）：")
    con = sqlite3.connect(DB)
    stats = {"series": 0, "appended": 0, "skipped": 0, "failed": 0, "details": []}
    try:
        for i, r in enumerate(behind):
            sid, sym = r["sid"], r["symbol"]
            if not sym:
                print("  %-22s 跳过：无 symbol" % sid)
                stats["failed"] += 1
                stats["details"].append({"series_id": sid, "status": "NO_SYMBOL"})
                continue
            # 取足够长的窗口覆盖缺口（700 根 ≈ 2.8 年）
            ser, err = fetch_raw(sym, "2018-01-01", as_of)
            time.sleep(PACING)
            if not ser:
                print("  %-22s 取数失败：%s" % (sid, err))
                stats["failed"] += 1
                stats["details"].append({"series_id": sid, "status": "FETCH_FAILED", "error": err})
                continue
            parsed = []
            for rec in ser:
                try:
                    parsed.append((rec[F_DATE], float(rec[F_OPEN]), float(rec[F_HIGH]),
                                   float(rec[F_LOW]), float(rec[F_CLOSE]), float(rec[F_VOL])))
                except (TypeError, ValueError, IndexError):
                    continue
            parsed.sort(key=lambda x: x[0])
            if not parsed:
                stats["failed"] += 1
                stats["details"].append({"series_id": sid, "status": "PARSE_EMPTY"})
                continue
            # ★ 重叠校验：库内最后一行必须与远端同日同价（否则远端基准已变，禁止追加）
            db_last, db_close = con.execute(
                "SELECT trade_date, close FROM market_daily WHERE series_id=? AND price_type='raw' "
                "ORDER BY trade_date DESC LIMIT 1", (sid,)).fetchone()
            remote = {x[0]: x for x in parsed}
            if db_last in remote and abs(remote[db_last][4] - db_close) > 1e-6:
                print("  %-22s 跳过：重叠日 %s 收盘不一致（库内 %.3f / 远端 %.3f）"
                      % (sid, db_last, db_close, remote[db_last][4]))
                stats["skipped"] += 1
                stats["details"].append({"series_id": sid, "status": "OVERLAP_MISMATCH",
                                         "db_close": db_close, "remote_close": remote[db_last][4]})
                continue
            new = [x for x in parsed if x[0] > db_last]
            if not new:
                stats["skipped"] += 1
                stats["details"].append({"series_id": sid, "status": "NO_NEW_ROWS"})
                continue
            now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            con.executemany(
                "INSERT OR IGNORE INTO market_daily "
                "(series_id, trade_date, open, high, low, close, adj_close, price_type, volume, amount,"
                " data_source, retrieved_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                [(sid, d, o, h, l, c, None, "raw", v, None, "tencent_gtimg", now)
                 for (d, o, h, l, c, v) in new])
            con.commit()
            stats["series"] += 1
            stats["appended"] += len(new)
            print("  %-22s +%d 行（%s → %s）" % (sid, len(new), new[0][0], new[-1][0]))
            stats["details"].append({"series_id": sid, "status": "APPENDED",
                                     "rows": len(new), "from": new[0][0], "to": new[-1][0]})
    finally:
        con.close()

    print("\n完成：序列 %d · 追加 %d 行 · 跳过 %d · 失败 %d"
          % (stats["series"], stats["appended"], stats["skipped"], stats["failed"]))
    if stats["failed"] or stats["skipped"]:
        print("★ 未更新的序列（原因见上）不会被补造；forward_observation 必须把它们计为「陈旧/不可用」")

    # ── 可选：补内部空洞 ──
    if a.fill_gaps:
        print("\n=== 补内部空洞（> 60 天）===")
        con = sqlite3.connect(DB)
        try:
            filled = 0
            for r in rows:
                sid, sym = r["sid"], r["symbol"]
                if not sym:
                    continue
                for prev_d, next_d in find_gaps(con, sid):
                    got, end = 0, next_d
                    for _ in range(8):           # 每轮最多 700 根，最多 8 轮（防死循环）
                        ser, _err = fetch_raw(sym, prev_d, end)
                        time.sleep(PACING)
                        parsed = [x for x in parse(ser) if prev_d < x[0] < next_d]
                        if not parsed:
                            break
                        n = append_rows(con, sid, parsed, prev_d)
                        got += n
                        earliest = parsed[0][0]
                        if n == 0 or earliest <= prev_d:
                            break
                        end = earliest            # 继续往更早的缺口段取
                    if got:
                        filled += got
                        print("  %-22s 缺口 %s→%s 补 %d 行" % (sid, prev_d, next_d, got))
            print("  合计补入 %d 行" % filled)
        finally:
            con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
