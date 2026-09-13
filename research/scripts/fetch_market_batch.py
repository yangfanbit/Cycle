"""补齐 2018–2025 批量研究所缺行情数据（腾讯财经 GTIMG，免费无 key）。

背景：Pilot 1-C1 只覆盖了 2022-2024 部分系列。本轮为 2019/2020/2021/2025
的 Campaign 补齐代表个股与基准日线，并扩展 SH000300 基准与 AUTO_ETF_516110
到 2025 年末。

纪律（遵循 market_data_validation.md）：
- 每行明确 price_type（raw / adjusted(qfq)），两套都写，禁止混用口径。
- 同一 series+date+price_type 唯一（INSERT OR REPLACE，幂等）。
- AUTO_SW(申万汽车) 腾讯不可得，如实 unavailable，不伪造。
- 516110 成立于 2021-11 之后，不得回溯用于其成立之前（本脚本只向后扩展）。
- 所有 symbol 均为真实可访问代码；data_source='tencent_gtimg' 可追溯。

用法: python scripts/fetch_market_batch.py
"""
import sys, os, json, csv, time, urllib.request, urllib.parse
from datetime import datetime, date, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

conn = db.connect()
db.migrate(conn)

HDRS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120',
        'Referer': 'https://gu.qq.com/'}
RAW_DIR = os.path.join(db.ROOT, "data", "market", "raw")
NORM_DIR = os.path.join(db.ROOT, "data", "market", "normalized")
CHUNK = 700  # 腾讯单次最多约 700 根

# series_key -> (tencent_symbol, name, series_type)
FETCH_PLAN = {
    # 基准：全区间 2018–2025
    "SH000300": ("sh000300", "沪深300(基准)", "benchmark", "2018-01-01", "2025-12-31"),
    # 行业代理：516110 成立于 2021-11，仅向后扩展到 2025
    "AUTO_ETF_516110": ("sh516110", "汽车ETF(中证800汽车, 行业代理)", "industry_index", "2022-01-01", "2025-12-31"),
    # 2019 C-2019-AD（智能驾驶/无人驾驶）
    "WANAN": ("sz002590", "万安科技", "stock", "2019-05-01", "2019-12-31"),
    "LUCHANG": ("sz002813", "路畅科技", "stock", "2019-05-01", "2019-12-31"),
    "YATAI": ("sz002284", "亚太股份", "stock", "2019-05-01", "2019-12-31"),
    # 2020 C-2020-NEV（特斯拉国产化+新能源）
    "BIDI": ("sz002594", "比亚迪", "stock", "2020-01-01", "2021-12-31"),
    "NINGDE": ("sz300750", "宁德时代", "stock", "2020-01-01", "2021-12-31"),
    "JAC": ("sh600418", "江淮汽车", "stock", "2020-01-01", "2020-12-31"),
    "XUSHENG": ("sh603305", "旭升股份", "stock", "2020-01-01", "2020-12-31"),
    # 2021 C-2021-NEV（新能源/电池）
    "CHANGAN": ("sz000625", "长安汽车", "stock", "2021-01-01", "2021-12-31"),
    "GREATWALL": ("sh601633", "长城汽车", "stock", "2021-01-01", "2022-09-30"),
    "XIAOKANG": ("sh601127", "小康股份(现赛力斯)", "stock", "2021-01-01", "2021-12-31"),
    # 2022 C-2022-POLICY（补长城/广汽）
    "GUANGQI": ("sh601238", "广汽集团", "stock", "2022-03-01", "2022-09-30"),
    # 2025 C-2025-ROBOTAXI
    "DESAYSV": ("sz002920", "德赛西威", "stock", "2025-01-01", "2025-12-31"),
    "ZHEJIANGSHISHI": ("sz002703", "浙江世宝", "stock", "2025-01-01", "2025-12-31"),
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


def fetch_range(symbol, beg, end, fq, retries=4):
    """拉取 [beg, end] 区间日线。

    腾讯 fqkline 语义：返回**截止 end 的最后 count 根**（beg 仅在区间内根数 < count 时生效）。
    因此按自然年切片（每年 ~243 根 << 700），逐段请求后合并去重，保证完整覆盖。
    """
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
                time.sleep(1.2 + i * 0.8)
        if got:
            out.extend(got)
        else:
            print(f"  !! {symbol} {fq} {seg_beg}~{seg_end} 无数据（保留为缺口）", flush=True)
    # 去重保序
    seen, dedup = set(), []
    for rec in out:
        if rec[0] not in seen:
            seen.add(rec[0]); dedup.append(rec)
    dedup.sort(key=lambda r: r[0])
    return dedup


def row_to_dict(rec, series_id, price_type):
    # Tencent: [date, open, close, high, low, volume, amount?, ...]
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


def regen_normalized_csv(series_id, name):
    """从 DB 重新生成 normalized CSV（保持既有文件约定，整段覆盖）。"""
    os.makedirs(NORM_DIR, exist_ok=True)
    fields = ["trade_date", "open", "high", "low", "close", "volume", "amount", "price_type"]
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
            print(f"!! {key} ({sym}): 无数据（{beg}~{end}）→ 如实 unavailable")
            summary[key] = "unavailable"
            continue
        # market_series upsert
        conn.execute(
            "INSERT INTO market_series (series_id, name, series_type, provider, symbol, frequency, price_type, adjustment_method, description) "
            "VALUES (?,?,?,?,?, 'daily','adjusted','qfq',?) "
            "ON CONFLICT(series_id) DO UPDATE SET name=excluded.name, symbol=excluded.symbol",
            (key, name, stype, "tencent", sym, f"腾讯GTIMG日线(qfq) 批量补齐 {beg}~{end}"))
        n = 0
        for rec in raw:
            db.insert(conn, "market_daily", row_to_dict(rec, key, "raw")); n += 1
        for rec in qfq:
            db.insert(conn, "market_daily", row_to_dict(rec, key, "adjusted")); n += 1
        conn.commit()
        regen_normalized_csv(key, name)
        # raw CSV 仅新系列写入（既有系列 raw CSV 保留原样，DB 为准）
        if not os.path.exists(os.path.join(RAW_DIR, f"tencent_{key}.csv")):
            os.makedirs(RAW_DIR, exist_ok=True)
            with open(os.path.join(RAW_DIR, f"tencent_{key}.csv"), "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["date", "open", "high", "low", "close", "volume", "amount", "price_type"])
                for rec in raw:
                    w.writerow([rec[0], rec[1], rec[3], rec[4], rec[2], rec[5],
                                rec[6] if len(rec) > 6 else "", "raw"])
        summary[key] = (len(raw), len(qfq))
        print(f"series {key} ({name}): raw={len(raw)} qfq={len(qfq)} [{beg}~{end}]", flush=True)
        time.sleep(0.5)
    conn.close()
    print("DONE", json.dumps(summary, ensure_ascii=False, default=str), flush=True)


if __name__ == "__main__":
    main()
