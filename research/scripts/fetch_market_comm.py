"""补齐「信息通信」历史 Cycle 所需的行情数据（腾讯财经 GTIMG，免费无 key）。

背景（Wave 1B — 信息通信历史 Cycle）：
- Historical Coverage Audit v0.2 确认历史侧只有 TH-AUTO / TH-PHARMA / TH-POWER，
  「信息通信」在 taxonomy 与行情数据中均为空白；当前侧 `CC-2026-OPTICAL-LINK`
  声明 `macro_theme = "信息通信"` 但无同名历史 cycle。
- 本脚本只为**已经通过证据裁决**的信息通信 Campaign 拉取代表标的日线，
  用于**核验生命周期日期**（Peak / 区间），不作为主题形成的判定依据。

纪律（遵循 market_data_validation.md / seed_medical_min.py 的既有做法）：
- 每行明确 price_type（raw / adjusted(qfq)），两套都写，禁止混用口径。
- 同一 series+date+price_type 唯一（INSERT OR REPLACE，幂等）。
- 所有 symbol 均为真实可访问代码；data_source='tencent_gtimg' 可追溯。
- 拉不到的区间如实保留缺口，不伪造、不前向填充。
- ★ 已知上游风险：腾讯 qfq 对部分标的返回非正价格（Wave 1A 实测通威股份 sh600438）。
  本脚本写入前**对前复权序列做非正值检测**，命中则跳过该序列并显式报警（不写入损坏数据）。

用法: python scripts/fetch_market_comm.py
"""
import sys, os, json, csv, time, urllib.request, urllib.parse
from datetime import datetime, date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

conn = db.connect()
db.migrate(conn)

HDRS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120',
        'Referer': 'https://gu.qq.com/'}
RAW_DIR = os.path.join(db.ROOT, "data", "market", "raw")
NORM_DIR = os.path.join(db.ROOT, "data", "market", "normalized")
CHUNK = 700

# series_key -> (tencent_symbol, name, series_type, beg, end)
FETCH_PLAN = {
    # ---- 通信主设备 / 光通信设备 ----
    "ZTE":      ("sz000063", "中兴通讯(通信主设备)", "stock", "2018-01-01", "2025-12-31"),
    "FIBERHOME": ("sh600498", "烽火通信(光通信/主设备)", "stock", "2018-01-01", "2025-12-31"),
    # ---- 光模块 / 光器件 ----
    "INNOLIGHT": ("sz300308", "中际旭创(光模块)", "stock", "2018-01-01", "2025-12-31"),
    "EOPTOLINK": ("sz300502", "新易盛(光模块)", "stock", "2018-01-01", "2025-12-31"),
    "TFC":       ("sz300394", "天孚通信(光器件)", "stock", "2018-01-01", "2025-12-31"),
    "ACCELINK":  ("sz002281", "光迅科技(光模块/光器件)", "stock", "2018-01-01", "2025-12-31"),
    # ---- 光纤光缆 ----
    "YOFC":     ("sh601869", "长飞光纤(光纤光缆)", "stock", "2018-07-20", "2025-12-31"),
    "HENGTONG": ("sh600487", "亨通光电(光纤光缆/海缆)", "stock", "2018-01-01", "2025-12-31"),
}


def _num(x):
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str) and x.strip():
        try:
            return float(x)
        except ValueError:
            return None
    return None


def fetch_range(symbol, beg, end, fq, retries=3):
    """按自然年切片拉取 [beg, end] 区间日线（腾讯单次最多约 700 根）。"""
    segs = []
    y = date.fromisoformat(beg).year
    end_y = date.fromisoformat(end).year
    while y <= end_y:
        s = date(y, 1, 1)
        e = date(y, 12, 31)
        if s < date.fromisoformat(beg):
            s = date.fromisoformat(beg)
        if e > date.fromisoformat(end):
            e = date.fromisoformat(end)
        segs.append((s.isoformat(), e.isoformat()))
        y += 1

    out = []
    for seg_beg, seg_end in segs:
        params = {"param": f"{symbol},day,{seg_beg},{seg_end},{CHUNK},{fq}"}
        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urllib.parse.urlencode(params)
        got = None
        for i in range(retries):
            try:
                req = urllib.request.Request(url, headers=HDRS)
                data = json.loads(urllib.request.urlopen(req, timeout=15).read().decode('utf-8', 'ignore'))
                d = data.get("data", {}).get(symbol, {})
                ser = d.get(fq + "day") or d.get(fq) or d.get("day") or []
                got = ser if ser else None
                break
            except Exception:
                time.sleep(1.0 + i * 0.8)
        if got:
            out.extend(got)
        else:
            print(f"  !! {symbol} {fq} {seg_beg}~{seg_end} 无数据（保留为缺口）", flush=True)
    seen, dedup = set(), []
    for rec in out:
        if rec[0] not in seen:
            seen.add(rec[0]); dedup.append(rec)
    dedup.sort(key=lambda r: r[0])
    return dedup


def row_to_dict(rec, series_id, price_type):
    close = _num(rec[2])
    return {
        "series_id": series_id,
        "trade_date": rec[0],
        "open": _num(rec[1]), "close": close,
        "high": _num(rec[3]), "low": _num(rec[4]),
        "volume": _num(rec[5]) if len(rec) > 5 else None,
        "amount": _num(rec[6]) if len(rec) > 6 else None,
        "price_type": price_type,
        "adj_close": close if price_type == "adjusted" else None,
        "data_source": "tencent_gtimg",
        "retrieved_at": datetime.now().isoformat(),
    }


def regen_normalized_csv(series_id):
    os.makedirs(NORM_DIR, exist_ok=True)
    rows = conn.execute(
        "SELECT trade_date, open, high, low, close, volume, amount, price_type "
        "FROM market_daily WHERE series_id=? ORDER BY price_type, trade_date", (series_id,)).fetchall()
    with open(os.path.join(NORM_DIR, f"{series_id}_daily.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "open", "high", "low", "close", "volume", "amount", "price_type"])
        for r in rows:
            w.writerow([r["trade_date"], r["open"], r["high"], r["low"], r["close"],
                        r["volume"], r["amount"], r["price_type"]])


def main():
    summary = {}
    for key, (sym, name, stype, beg, end) in FETCH_PLAN.items():
        raw = fetch_range(sym, beg, end, "")
        qfq = fetch_range(sym, beg, end, "qfq")
        if not raw:
            print(f"!! {key} ({sym}): 无数据（{beg}~{end}）→ 如实 unavailable", flush=True)
            summary[key] = "unavailable"
            continue
        # ★ 前复权非正值检测（Wave 1A 实测腾讯 qfq 对部分标的不可靠）
        bad = [(r[0], _num(r[2])) for r in qfq if (_num(r[2]) is not None and _num(r[2]) <= 0)]
        if bad:
            print(f"!! {key} ({sym}): 前复权序列含非正值 {len(bad)} 条（如 {bad[:3]}）"
                  f"→ 按「不写入已知损坏数据」纪律**跳过该序列**，仅登记 raw", flush=True)
            qfq = []
        conn.execute(
            "INSERT INTO market_series (series_id, name, series_type, provider, symbol, frequency, price_type, adjustment_method, description) "
            "VALUES (?,?,?,?,?, 'daily',?,?,?) "
            "ON CONFLICT(series_id) DO UPDATE SET name=excluded.name, symbol=excluded.symbol",
            (key, name, stype, "tencent", sym,
             "adjusted" if qfq else "raw", "qfq" if qfq else None,
             f"腾讯GTIMG日线 信息通信 Wave 1B {beg}~{end}" + ("" if qfq else "（前复权序列不可用，仅 raw）")))
        for rec in raw:
            db.insert(conn, "market_daily", row_to_dict(rec, key, "raw"))
        for rec in qfq:
            db.insert(conn, "market_daily", row_to_dict(rec, key, "adjusted"))
        conn.commit()
        regen_normalized_csv(key)
        raw_path = os.path.join(RAW_DIR, f"tencent_{key}.csv")
        if not os.path.exists(raw_path):
            os.makedirs(RAW_DIR, exist_ok=True)
            with open(raw_path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["date", "open", "high", "low", "close", "volume", "amount", "price_type"])
                for rec in raw:
                    w.writerow([rec[0], rec[1], rec[3], rec[4], rec[2], rec[5],
                                rec[6] if len(rec) > 6 else "", "raw"])
        summary[key] = (len(raw), len(qfq))
        print(f"series {key} ({name}): raw={len(raw)} qfq={len(qfq)} [{beg}~{end}]", flush=True)
        time.sleep(0.4)
    conn.close()
    print("DONE", json.dumps(summary, ensure_ascii=False, default=str), flush=True)


if __name__ == "__main__":
    main()
