"""Pilot 1-C1.3：拉取 2022 年 4/1-8/31 汽车研究所需真实日线（腾讯 GTIMG）。

序列：SH000300(基准) / AUTO_ETF_516110(2022汽车行业代理, 2021上市故2022存在) /
      比亚迪(002594) / 中通客车(000957) / 长安汽车(000625)。
注意：516110 仅作 2022 行业代理（不作 2018-2020）。raw+adjusted(qfq) 双口径入库。
幂等。用法: python scripts/fetch_market_2022.py
"""
import sys, os, time, json, urllib.request, urllib.parse
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

conn = db.connect()
db.migrate(conn)
HDRS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120',
        'Referer': 'https://gu.qq.com/'}
BEG, END = "2022-03-01", "2022-09-30"

SERIES = {
    "SH000300": ("sh000300", "沪深300(基准)", "benchmark"),
    "AUTO_ETF_516110": ("sh516110", "汽车ETF(2022行业代理)", "industry_index"),
    "BIDI": ("sz002594", "比亚迪", "stock"),
    "ZHONGTONG": ("sz000957", "中通客车", "stock"),
    "CHANGAN": ("sz000625", "长安汽车", "stock"),
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


def fetch(symbol, fq, retries=4):
    p = {"param": f"{symbol},day,{BEG},{END},900,{fq}"}
    u = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urllib.parse.urlencode(p)
    for i in range(retries):
        try:
            req = urllib.request.Request(u, headers=HDRS)
            d = json.loads(urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore'))
            obj = d.get("data", {}).get(symbol, {})
            ser = obj.get(fq + "day") or obj.get(fq) or obj.get("day") or []
            if ser:
                return ser
        except Exception as e:
            time.sleep(1.5 + i)
    return []


def row(rec, sid, pt):
    close = _num(rec[2])
    return {"series_id": sid, "trade_date": rec[0], "open": _num(rec[1]), "close": close,
            "high": _num(rec[3]), "low": _num(rec[4]),
            "volume": _num(rec[5]) if len(rec) > 5 else None,
            "amount": _num(rec[6]) if len(rec) > 6 else None,
            "price_type": pt, "adj_close": close if pt == "adjusted" else None,
            "data_source": "tencent_gtimg", "retrieved_at": datetime.now().isoformat()}


def main():
    for sid, (sym, name, st) in SERIES.items():
        db.insert(conn, "market_series", {
            "series_id": sid, "name": name, "series_type": st, "provider": "tencent",
            "symbol": sym, "frequency": "daily", "price_type": "adjusted",
            "adjustment_method": "qfq", "description": f"2022 {name}（腾讯GTIMG）"})
    conn.commit()
    for sid, (sym, name, _) in SERIES.items():
        raw, qfq = fetch(sym, ""), fetch(sym, "qfq")
        for rec in raw:
            db.insert(conn, "market_daily", row(rec, sid, "raw"))
        for rec in qfq:
            db.insert(conn, "market_daily", row(rec, sid, "adjusted"))
        conn.commit()
        print(f"{sid} ({name}): raw={len(raw)} qfq={len(qfq)}", flush=True)
        time.sleep(0.6)
    conn.close()
    print("DONE 2022")


if __name__ == "__main__":
    main()