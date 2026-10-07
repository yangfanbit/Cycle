#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""fetch_market_batch_v0_2.py —— 把 K 线覆盖从 **13/53** 提上去（腾讯 GTIMG，免费无 key）。

## 与 v0_1 的区别（唯一）

v0_1 的 `FETCH_PLAN` 是**硬编码的固定列表**；本版**从数据库自动构建计划**：
凡 `campaign_securities` 关联的证券而 `market_daily` 无数据者，全部纳入。

**v0_1 逐字节保留。**

## 区间口径（★ 为「提前观察窗口」预留）

对每个证券，区间 = `min(关联 campaign 的 start_date) − 1 年` ~ `max(关联 campaign 的 end_date)`。
**多取前 1 年**，是为了让「启动前 N 日的量价形态」有数据可算（见
`docs/DESIGN_KLINE_VALIDATION_AND_EARLY_WINDOW_v0_1.md`）。

## 纪律（沿用 `market_data_validation.md` + v0_1）

- 每行明确 `price_type`（raw / adjusted(qfq)），**两套都写**，禁止混用口径。
- 同一 `series+date+price_type` 唯一（幂等）。
- **腾讯不可得的，如实 unavailable，不伪造。**
- 幂等：重复运行结果一致。

## 用法

    python research/scripts/fetch_market_batch_v0_2.py --dry-run   # 只列计划
    python research/scripts/fetch_market_batch_v0_2.py             # 抓取
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

HDRS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120",
    "Referer": "https://gu.qq.com/",
}
CHUNK = 700
RAW_DIR = os.path.join(db.ROOT, "data", "market", "raw")
NORM_DIR = os.path.join(db.ROOT, "data", "market", "normalized")


def _num(x):
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str) and x.strip():
        try:
            return float(x)
        except ValueError:
            return None
    return None


def tencent_symbol(ticker: str, exchange: str) -> str:
    """ticker + exchange → 腾讯代码（sh/sz + 6 位）。

    ★ ticker 里可能**自带交易所后缀**（如 ）—— 必须先剥离，
      否则会拼出 （错误代码）。
    """
    t = (ticker or "").strip().upper()
    for suf in (".SH", ".SZ", ".SS", ".BJ"):
        if t.endswith(suf):
            if not exchange:
                exchange = suf[1:]
            t = t[: -len(suf)]
            break
    ticker = t
    ex = (exchange or "").strip().upper()
    pre = {"SH": "sh", "SS": "sh", "SZ": "sz"}.get(ex)
    if pre is None:
        # 兜底：6 开头→sh，0/3 开头→sz；**不做其他猜测**
        pre = "sh" if ticker.startswith("6") else "sz"
    return pre + ticker


def fetch_range(symbol, beg, end, fq, retries=4):
    """拉取 [beg, end] 区间日线（按自然年切片，避免腾讯 count 上限）。"""
    segs = []
    y = date.fromisoformat(beg).year
    end_y = date.fromisoformat(end).year
    while y <= end_y:
        s = max(date(y, 1, 1), date.fromisoformat(beg))
        e = min(date(y, 12, 31), date.fromisoformat(end))
        segs.append((s.isoformat(), e.isoformat()))
        y += 1
    out = []
    for seg_beg, seg_end in segs:
        params = {"param": f"{symbol},day,{seg_beg},{seg_end},{CHUNK},{fq}"}
        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urllib.parse.urlencode(params)
        got = None
        blocked = False
        for i in range(retries):
            try:
                req = urllib.request.Request(url, headers=HDRS)
                body = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
                # ★ 关键：腾讯在限流时返回 **HTML 反爬页**（不是 JSON）——
                #   必须与「真的无数据」区分，否则会把有效代码误标为 unavailable。
                if body.lstrip().startswith("<"):
                    blocked = True
                    time.sleep(3.0 + i * 3.0)   # 长退避
                    continue
                data = json.loads(body)
                d = data.get("data", {}).get(symbol, {})
                ser = d.get(fq + "day") or d.get(fq) or d.get("day") or []
                got = ser if ser else None
                blocked = False
                break
            except Exception:
                time.sleep(2.0 + i * 2.0)
        if got:
            out.extend(got)
        elif blocked:
            # ★ 限流未恢复 → **不写 unavailable**，明确标为「被限流，需重跑」
            raise RuntimeError("RATE_LIMITED: %s %s %s~%s" % (symbol, fq, seg_beg, seg_end))
        else:
            print(f"  !! {symbol} {fq} {seg_beg}~{seg_end} 无数据（已确认非限流，保留为缺口）", flush=True)
    seen, dedup = set(), []
    for rec in out:
        if rec[0] not in seen:
            seen.add(rec[0])
            dedup.append(rec)
    dedup.sort(key=lambda r: r[0])
    return dedup


def row_to_dict(rec, series_id, price_type):
    return {
        "series_id": series_id,
        "trade_date": rec[0],
        "open": _num(rec[1]),
        "close": _num(rec[2]),
        "high": _num(rec[3]),
        "low": _num(rec[4]),
        "volume": _num(rec[5]) if len(rec) > 5 else None,
        "amount": _num(rec[6]) if len(rec) > 6 else None,
        "adj_close": _num(rec[2]) if price_type == "adjusted" else None,
        "price_type": price_type,
        "data_source": "tencent_gtimg",
        "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def regen_normalized_csv(conn, series_id, name):
    rows = conn.execute(
        "SELECT trade_date,open,high,low,close,adj_close,volume,amount,price_type "
        "FROM market_daily WHERE series_id=? ORDER BY price_type, trade_date",
        (series_id,),
    ).fetchall()
    os.makedirs(NORM_DIR, exist_ok=True)
    with open(os.path.join(NORM_DIR, f"{series_id}_daily.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["trade_date", "open", "high", "low", "close", "adj_close", "volume", "amount", "price_type"])
        w.writerows(rows)


def build_plan(conn):
    """从 DB 自动构建：凡有 campaign 关联但 market_daily 无数据的证券。"""
    rows = conn.execute(
        """
        SELECT s.security_id, s.ticker, s.name, s.exchange,
               MIN(cp.start_date) AS beg, MAX(COALESCE(cp.end_date, cp.start_date)) AS end
        FROM securities s
        JOIN campaign_securities cs ON cs.security_id = s.security_id
        JOIN campaigns cp ON cp.campaign_id = cs.campaign_id
        WHERE s.ticker IS NOT NULL AND s.ticker <> ''
          AND s.security_id NOT IN (SELECT DISTINCT series_id FROM market_daily)
        GROUP BY s.security_id
        ORDER BY s.security_id
        """
    ).fetchall()
    plan = {}
    for sid, ticker, name, exch, beg, end in rows:
        if not beg:
            continue
        # ★ 多取前 1 年（提前观察窗口需要）
        y = date.fromisoformat(beg).year - 1
        beg2 = date(y, 1, 1).isoformat()
        end2 = end or date.today().isoformat()
        if end2 > "2025-12-31":  # 与研究区间上限一致，不外扩
            end2 = "2025-12-31"
        plan[sid] = (tencent_symbol(ticker, exch), name or sid, "stock", beg2, end2)
    return plan


def main(argv):
    dry = "--dry-run" in argv
    conn = db.connect()
    plan = build_plan(conn)
    print("ThreeC · K 线补齐 v0_2 —— 目标：把 K 线覆盖从 13/53 提上去")
    print("-" * 62)
    print("待抓取证券: %d 个" % len(plan))
    if dry:
        for sid, (sym, nm, st, b, e) in list(plan.items())[:25]:
            print("   %-18s %-10s %-16s %s ~ %s" % (sid, sym, nm[:14], b, e))
        if len(plan) > 25:
            print("   ... 另 %d 个" % (len(plan) - 25))
        print("-" * 62)
        print("[dry-run] 未发起任何请求")
        conn.close()
        return 0

    ok = fail = 0
    for i, (sid, (sym, nm, stype, beg, end)) in enumerate(sorted(plan.items()), 1):
        try:
            raw = fetch_range(sym, beg, end, "")
            qfq = fetch_range(sym, beg, end, "qfq")
        except RuntimeError as e:
            print("[%3d/%3d] ⏸ %-18s %s → **被限流，跳过（重跑本脚本即可续）**" % (i, len(plan), sid, str(e)[:60]), flush=True)
            fail += 1
            time.sleep(20)
            continue
        if not raw:
            print("[%3d/%3d] !! %-18s %-10s 无数据 → 如实 unavailable" % (i, len(plan), sid, sym), flush=True)
            fail += 1
            continue
        conn.execute(
            "INSERT INTO market_series (series_id,name,series_type,provider,symbol,frequency,price_type,"
            "adjustment_method,description) VALUES (?,?,?,?,?,'daily','adjusted','qfq',?) "
            "ON CONFLICT(series_id) DO UPDATE SET name=excluded.name, symbol=excluded.symbol",
            (sid, nm, stype, "tencent", sym, f"腾讯GTIMG日线(qfq) v0_2 自动计划 {beg}~{end}"),
        )
        for rec in raw:
            db.insert(conn, "market_daily", row_to_dict(rec, sid, "raw"))
        for rec in qfq:
            db.insert(conn, "market_daily", row_to_dict(rec, sid, "adjusted"))
        conn.commit()
        regen_normalized_csv(conn, sid, nm)
        raw_csv = os.path.join(RAW_DIR, f"tencent_{sid}.csv")
        if not os.path.exists(raw_csv):
            os.makedirs(RAW_DIR, exist_ok=True)
            with open(raw_csv, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["date", "open", "high", "low", "close", "volume", "amount", "price_type"])
                for rec in raw:
                    w.writerow([rec[0], rec[1], rec[3], rec[4], rec[2], rec[5],
                                rec[6] if len(rec) > 6 else "", "raw"])
        print("[%3d/%3d] %-18s %-10s raw=%4d qfq=%4d  %s~%s" % (i, len(plan), sid, sym, len(raw), len(qfq), beg, end), flush=True)
        ok += 1
        time.sleep(0.4)
    conn.close()
    print("-" * 62)
    print("DONE 成功 %d · 无数据 %d · 共 %d" % (ok, fail, len(plan)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
