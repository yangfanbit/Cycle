#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""fetch_market_batch_v0_3.py —— 补齐 K 线覆盖（v0_2 的修复版）。

## 为什么要 v0_3：v0_2 的三个缺陷（都是 2026-10-08 实测暴露的）

1. **计划只检查一侧**。v0_2 的跳过条件是
   `have_max >= end2[:8]+"01" or have_max >= "2025-11-01"` —— 只看**终点**。
   于是「起点缺」被静默跳过：例如某证券需要 2021-01 起的数据，实际只有 2022-01 起，
   `have_max` 达标 → 直接跳过，**前半段永远补不上**。
2. **请求级无节流**。v0_2 只在**证券之间** `sleep(0.4)`，而每个证券要发
   `2 × 年数` 个请求（raw + qfq）→ 连发十几个请求 → 触发腾讯限流。
3. **限流 = 永久跳过**。v0_2 遇限流 `continue`，该证券**本轮再也不会重试** ——
   21 个「零数据」正是这样产生的，而其中 18 个是**有效 A 股代码**（已逐一验证端点可用）。

## v0_3 的做法

- 计划**同时检查两侧**（`have_min` 与 `have_max`）。
- **请求级节流**：每次请求前 `PACING` 秒 + 抖动。
- **限流不等于跳过**：指数退避重试；仍失败则进入 `deferred`，多轮集中重试。
- **「确认无数据」与「被限流」严格分开**：
  - 前者（合法 JSON + 空序列，如上市前的区间）写入 `fetch_gaps.json`，避免每轮重复请求；
  - 后者**绝不落盘**，只进 `deferred`。
- **整段重取**：需要扩展的序列，重取整个 `[beg2, end2]`（而非只补缺口），
  因为腾讯的**前复权价每次除权都会整体重算** —— 只补缺口会让新旧两批 qfq 在拼接处出现跳变。
  已确认无数据的年段仍跳过（见上）。
- 缺 `ticker` 的证券用**经名称核验**的覆盖表；不可取的（申万指数）**显式列名跳过，不代以他指数**。

## 纪律（沿用 `market_data_validation.md` + v0_1/v0_2）

- 每行明确 `price_type`（raw / adjusted(qfq)），**两套都写**，禁止混用口径。
- 同一 `series+date+price_type` 唯一（`INSERT OR REPLACE`，幂等）。
- **拿不到的如实记为缺口，不伪造。**

## 用法

    python research/scripts/fetch_market_batch_v0_3.py --dry-run
    python research/scripts/fetch_market_batch_v0_3.py
    python research/scripts/fetch_market_batch_v0_3.py --only EFORT,ZHAOWEI
"""

from __future__ import annotations

import csv
import io
import json
import os
import random
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

HDRS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120",
    "Referer": "https://gu.qq.com/",
}
CHUNK = 700
PACING = 1.2                      # ★ 请求级节流（秒）；v0_2 无此项
RANGE_CEIL = "2025-12-31"         # 与研究区间上限一致
RAW_DIR = os.path.join(db.ROOT, "data", "market", "raw")
NORM_DIR = os.path.join(db.ROOT, "data", "market", "normalized")
GAP_FILE = os.path.join(db.ROOT, "data", "market", "fetch_gaps.json")
REP_DIR = os.path.join(db.ROOT, "research", "reports")

# ★ 缺 ticker 的证券 —— 代码经**腾讯返回名称**核验，非猜测。
#   埃夫特 688165 → 返回「埃夫特-U」；兆威机电 003021 → 返回「兆威机电」。
TICKER_FIX = {
    "EFORT": ("688165", "SH", "腾讯返回名称=埃夫特-U（2026-10-08 核验）"),
    "ZHAOWEI": ("003021", "SZ", "腾讯返回名称=兆威机电（2026-10-08 核验）"),
}

# ★ 显式不可取：列名跳过，**不代以其他指数**（避免偷换口径）
NOT_FETCHABLE = {
    "SWMIL": "申万国防军工指数（801740.SI）—— 腾讯 GTIMG 不提供申万指数（实测 sz801740 返回空）。"
             "本脚本**不代以中证军工/军工 ETF 等替代指数**：那会偷换口径。留待研究侧决定代理口径。",
    "CNIMIL": "国证军工指数 —— 无 ticker，且**未被任何 campaign 引用**（0 引用），本轮不取。",
}


class RateLimited(RuntimeError):
    pass


class InvalidSymbol(RuntimeError):
    """代码无效（腾讯不认这个 symbol）—— ★ 与「上市前无数据」**必须区分**。

    实测（2026-10-08）：无效代码 `sz999999` 返回
    `{"code":0,"msg":"","data":{"sz999999":{"day":[],"qt":{"sz999999":[],...}}}}`
    —— **与「上市前无数据」的返回形状完全相同**（合法 JSON + 空序列）。
    唯一可靠的区分：**`qt` 是否带证券名**（有效代码 `qt[1]` 是名称；无效代码 `qt` 为空数组）。
    若不区分，无效代码会被静默写成「确认无数据」并持久化 —— 那是**把假 absence 固化**。
    """


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

    ★ ticker 可能自带交易所后缀（如 `600893.SH`）—— 必须先剥离，
      否则会拼出 `sh600893.SH`（错误代码）。
    """
    t = (ticker or "").strip().upper()
    for suf in (".SH", ".SZ", ".SS", ".BJ"):
        if t.endswith(suf):
            if not exchange:
                exchange = suf[1:]
            t = t[: -len(suf)]
            break
    ex = (exchange or "").strip().upper()
    pre = {"SH": "sh", "SS": "sh", "SZ": "sz"}.get(ex)
    if pre is None:
        pre = "sh" if t.startswith("6") else "sz"
    return pre + t


def year_segments(beg, end):
    y, end_y = date.fromisoformat(beg).year, date.fromisoformat(end).year
    out = []
    while y <= end_y:
        s = max(date(y, 1, 1), date.fromisoformat(beg))
        e = min(date(y, 12, 31), date.fromisoformat(end))
        out.append((s.isoformat(), e.isoformat()))
        y += 1
    return out


def request_segment(symbol, seg_beg, seg_end, fq, retries=6):
    """取单个年段。返回记录列表（可能为空 = 确认无数据）；限流未恢复则抛 RateLimited。

    ★ 关键：腾讯限流时返回 **HTML 反爬页**（不是 JSON）——
      必须与「真的无数据」区分，否则会把有效代码误标为 unavailable。
    """
    params = {"param": f"{symbol},day,{seg_beg},{seg_end},{CHUNK},{fq}"}
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urllib.parse.urlencode(params)
    for i in range(retries):
        time.sleep(PACING + random.uniform(0.0, 0.6))   # ★ 请求级节流
        try:
            req = urllib.request.Request(url, headers=HDRS)
            body = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")
        except Exception:
            time.sleep(2.0 * (i + 1))
            continue
        if body.lstrip().startswith("<"):
            time.sleep(5.0 * (i + 1))                    # 限流：长退避
            continue
        try:
            data = json.loads(body)
        except Exception:
            time.sleep(2.0 * (i + 1))
            continue
        # ★ 守卫①：`data` 字段不是对象（如 param error 时返回 `"data":[]`）→ 视为异常，不当作无数据
        if not isinstance(data.get("data"), dict):
            time.sleep(2.0 * (i + 1))
            continue
        d = data["data"].get(symbol)
        # ★ 守卫②：响应里没有该 symbol 键 → 异常，不当作无数据
        if not isinstance(d, dict):
            time.sleep(2.0 * (i + 1))
            continue
        ser = d.get(fq + "day") or d.get(fq) or d.get("day") or []
        if ser:
            return ser
        # ★ 守卫③：序列为空时，用 `qt` 是否带证券名区分「上市前无数据」与「代码无效」
        qt = d.get("qt", {}).get(symbol) or []
        name = qt[1] if isinstance(qt, list) and len(qt) > 1 else None
        if not name:
            raise InvalidSymbol("%s %s~%s（qt 无名称 → 代码无效）" % (symbol, seg_beg, seg_end))
        return []
    raise RateLimited("%s %s %s~%s" % (symbol, fq, seg_beg, seg_end))


def fetch_series(symbol, beg, end, fq, gaps, stats):
    """整段取 [beg, end]（跳过已确认无数据的年段）。"""
    out = []
    segs = gaps["segments"]
    for seg in year_segments(beg, end):
        key = "%s|%s|%s|%s" % (symbol, fq, seg[0], seg[1])
        if key in segs:
            stats["skipped_known_gap"] += 1
            continue
        ser = request_segment(symbol, seg[0], seg[1], fq)
        if ser:
            out.extend(ser)
        else:
            segs[key] = {"symbol": symbol, "fq": fq, "seg": list(seg),
                         "confirmed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                         "note": "合法 JSON + 空序列 → 确认该区间无数据（如上市前），非限流"}
            stats["confirmed_empty"] += 1
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


def regen_normalized_csv(conn, series_id):
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


def load_gaps():
    """返回 {"segments": {...}, "floors": {...}}。

    - `segments`：**已确认无数据**的年段（合法 JSON + 空序列），避免每轮重复请求。
    - `floors`：某序列**最早可得日**。★ 只有「已成功取过含 beg2 的区间、结果仍从更晚开始」时才写入 ——
      这证明更早的数据**不存在**（如上市日之前），而非「我们没取」。缺了它，
      上市前的「起点缺」会让该证券**每一轮都被重新抓取**。
    """
    if not os.path.exists(GAP_FILE):
        return {"segments": {}, "floors": {}}
    try:
        d = json.load(io.open(GAP_FILE, encoding="utf-8"))
    except Exception:
        return {"segments": {}, "floors": {}}
    if "segments" not in d:          # 兼容早期扁平结构
        d = {"segments": d, "floors": {}}
    d.setdefault("floors", {})
    return d


def save_gaps(gaps):
    os.makedirs(os.path.dirname(GAP_FILE), exist_ok=True)
    io.open(GAP_FILE, "w", encoding="utf-8", newline="\n").write(
        json.dumps(gaps, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    )


def build_plan(conn, gaps, only=None, extra=None):
    """从 DB 自动构建计划：**同时**检查区间两侧是否不足。

    `extra`：显式指定的 security_id 列表 —— 即使**未挂到任何 campaign** 也纳入抓取。
    ★ 为什么需要：记录里**点名**但未登记的标的（如白电三巨头）不在 campaign 关联里，
      但它们正是判断「标的清单是否错位」的关键证据，必须能取到行情。
    """
    rows = conn.execute(
        """
        SELECT s.security_id, s.ticker, s.name, s.exchange,
               MIN(cp.start_date) AS beg, MAX(COALESCE(cp.end_date, ?)) AS end
        FROM securities s
        JOIN campaign_securities cs ON cs.security_id = s.security_id
        JOIN campaigns cp ON cp.campaign_id = cs.campaign_id
        GROUP BY s.security_id
        ORDER BY s.security_id
        """,
        (RANGE_CEIL,),
    ).fetchall()

    plan, skipped = {}, []
    for sid, ticker, name, exch, beg, end in rows:
        if only and sid not in only:
            continue
        if sid in NOT_FETCHABLE:
            skipped.append((sid, "NOT_FETCHABLE: " + NOT_FETCHABLE[sid]))
            continue
        if not ticker:
            fix = TICKER_FIX.get(sid)
            if not fix:
                skipped.append((sid, "缺 ticker 且无经核验的覆盖值"))
                continue
            ticker, exch = fix[0], fix[1]
        if not beg:
            continue
        # ★ 多取前 1 年（「提前观察窗口」需要）
        beg2 = date(date.fromisoformat(beg).year - 1, 1, 1).isoformat()
        end2 = min(end or RANGE_CEIL, RANGE_CEIL)

        cur = conn.execute(
            "SELECT MIN(trade_date), MAX(trade_date) FROM market_daily WHERE series_id=?", (sid,)
        ).fetchone()
        have_min, have_max = (cur[0], cur[1]) if cur else (None, None)

        if have_min is not None and have_max is not None:
            # ★ v0_3 修：**两侧都看**。v0_2 只看 have_max，导致「起点缺」被静默跳过。
            #   容忍 31 日：年末/节假日自然不满整段，不应因此反复重抓。
            #   另：若该序列的**最早可得日**（floors）已被证实晚于 beg2（如上市日之前），
            #   则「起点缺」不是缺陷 —— 数据本身不存在。
            tol_min = (date.fromisoformat(beg2) + timedelta(days=31)).isoformat()
            floor = gaps["floors"].get(sid)
            min_ok = have_min <= tol_min or (floor is not None and have_min <= floor)
            max_ok = have_max >= (date.fromisoformat(end2) - timedelta(days=31)).isoformat()
            if min_ok and max_ok:
                continue
            why = ("起点缺 %s>%s%s" % (have_min, beg2, "（已证最早可得）" if floor else "") if not min_ok else "") + \
                  (" 终点缺 %s<%s" % (have_max, end2) if not max_ok else "")
        else:
            why = "完全无数据"
        plan[sid] = (tencent_symbol(ticker, exch), name or sid, "stock", beg2, end2, why.strip())

    # ★ extra：未挂 campaign 的标的（点名但未登记），按显式区间抓取
    for sid in (extra or []):
        if sid in plan:
            continue
        row = conn.execute("SELECT ticker, name, exchange FROM securities WHERE security_id=?", (sid,)).fetchone()
        if not row or not row[0]:
            skipped.append((sid, "extra：不在 securities 表或缺 ticker"))
            continue
        ticker, name, exch = row
        beg2, end2 = extra.get(sid) if isinstance(extra, dict) else (None, None)
        beg2 = beg2 or "2016-01-01"
        end2 = min(end2 or RANGE_CEIL, RANGE_CEIL)
        cur = conn.execute("SELECT MIN(trade_date), MAX(trade_date) FROM market_daily WHERE series_id=?", (sid,)).fetchone()
        if cur[0] and cur[1] and cur[0] <= beg2 and cur[1] >= (date.fromisoformat(end2) - timedelta(days=31)).isoformat():
            continue
        plan[sid] = (tencent_symbol(ticker, exch), name or sid, "stock", beg2, end2, "extra：点名但未挂 campaign")
    return plan, skipped


def main(argv):
    dry = "--dry-run" in argv
    only = None
    if "--only" in argv:
        only = set(argv[argv.index("--only") + 1].split(","))
    # ★ --extra MIDEA,GREE,HAIER：抓取**未挂 campaign** 的标的（记录点名但未登记）
    extra = None
    if "--extra" in argv:
        extra = [x for x in argv[argv.index("--extra") + 1].split(",") if x]

    conn = db.connect()
    gaps = load_gaps()
    plan, skipped = build_plan(conn, gaps, only, extra)

    print("ThreeC · K 线补齐 v0_3")
    print("-" * 78)
    print("待抓取证券: %d 个   （已知无数据年段 %d 个、已知最早可得日 %d 个，将跳过）" % (
        len(plan), len(gaps["segments"]), len(gaps["floors"])))
    for sid, (sym, nm, st, b, e, why) in sorted(plan.items()):
        print("   %-18s %-10s %-14s %s ~ %s   [%s]" % (sid, sym, nm[:12], b, e, why))
    if skipped:
        print("-" * 78)
        print("显式跳过: %d 个" % len(skipped))
        for sid, why in skipped:
            print("   %-18s %s" % (sid, why[:110]))
    if dry:
        print("-" * 78)
        print("[dry-run] 未发起任何请求")
        conn.close()
        return 0

    stats = {"ok": 0, "unavailable": 0, "invalid_symbol": 0, "confirmed_empty": 0, "skipped_known_gap": 0, "requests": 0}
    results = {}
    todo = dict(plan)
    for rnd in (1, 2, 3):
        deferred = {}
        if rnd > 1:
            print("-" * 78)
            print("第 %d 轮：重试上一轮被限流的 %d 个" % (rnd, len(todo)))
        for i, (sid, (sym, nm, stype, beg, end, why)) in enumerate(sorted(todo.items()), 1):
            try:
                raw = fetch_series(sym, beg, end, "", gaps, stats)
                qfq = fetch_series(sym, beg, end, "qfq", gaps, stats)
            except InvalidSymbol as e:
                # ★ 代码无效 ≠ 无数据。**不写 gaps**（那会把假 absence 固化），改为显式报告。
                print("[%d轮 %2d/%2d] ✗ %-18s %-10s **代码无效** %s" % (rnd, i, len(todo), sid, sym, str(e)[:52]), flush=True)
                stats["invalid_symbol"] += 1
                results[sid] = {"status": "INVALID_SYMBOL", "symbol": sym, "reason": str(e)}
                continue
            except RateLimited as e:
                print("[%d轮 %2d/%2d] ⏸ %-18s 限流未恢复，转入下一轮  %s" % (rnd, i, len(todo), sid, str(e)[:44]), flush=True)
                deferred[sid] = (sym, nm, stype, beg, end, why)
                continue
            if not raw:
                print("[%d轮 %2d/%2d] !! %-18s %-10s 无数据（已确认非限流）" % (rnd, i, len(todo), sid, sym), flush=True)
                stats["unavailable"] += 1
                results[sid] = {"status": "UNAVAILABLE", "symbol": sym, "reason": "合法 JSON + 空序列"}
                save_gaps(gaps)
                continue
            conn.execute(
                "INSERT INTO market_series (series_id,name,series_type,provider,symbol,frequency,price_type,"
                "adjustment_method,description) VALUES (?,?,?,?,?,'daily','adjusted','qfq',?) "
                "ON CONFLICT(series_id) DO UPDATE SET name=excluded.name, symbol=excluded.symbol",
                (sid, nm, stype, "tencent", sym, "腾讯GTIMG日线(qfq) v0_3 自动计划 %s~%s" % (beg, end)),
            )
            for rec in raw:
                db.insert(conn, "market_daily", row_to_dict(rec, sid, "raw"))
            for rec in qfq:
                db.insert(conn, "market_daily", row_to_dict(rec, sid, "adjusted"))
            conn.commit()
            regen_normalized_csv(conn, sid)
            # ★ 记录该序列的「最早可得日」：已成功取过含 beg2 的区间，结果仍从更晚开始 →
            #   证明更早的数据不存在（上市日之前），而非我们没取。避免每轮重复抓取。
            if raw[0][0] > (date.fromisoformat(beg) + timedelta(days=31)).isoformat():
                gaps["floors"][sid] = raw[0][0]
            print("[%d轮 %2d/%2d] %-18s %-10s raw=%4d qfq=%4d  %s~%s" % (rnd, i, len(todo), sid, sym, len(raw), len(qfq), beg, end), flush=True)
            stats["ok"] += 1
            results[sid] = {"status": "OK", "symbol": sym, "raw_rows": len(raw), "qfq_rows": len(qfq), "range": [beg, end]}
        save_gaps(gaps)
        todo = deferred
        if not todo:
            break
        print("   等待 60s 后进入下一轮…")
        time.sleep(60)

    if todo:
        print("-" * 78)
        print("仍被限流: %d 个 → 重跑本脚本即可续（未写入任何假 absence）" % len(todo))
        for sid in sorted(todo):
            results[sid] = {"status": "RATE_LIMITED", "symbol": todo[sid][0]}

    save_gaps(gaps)
    conn.close()
    os.makedirs(REP_DIR, exist_ok=True)
    io.open(os.path.join(REP_DIR, "market_fetch_v0_3_report.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "stats": stats,
                    "planned": len(plan), "results": results,
                    "not_fetchable": NOT_FETCHABLE, "ticker_fix": {k: v[2] for k, v in TICKER_FIX.items()}},
                   ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    )
    print("-" * 78)
    print("DONE 成功 %d · 确认无数据 %d · **代码无效 %d** · 跳过已知空段 %d · 确认空段新增 %d" % (
        stats["ok"], stats["unavailable"], stats["invalid_symbol"], stats["skipped_known_gap"], stats["confirmed_empty"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
