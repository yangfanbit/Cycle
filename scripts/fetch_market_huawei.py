"""Pilot 1-C1.4.1：华为汽车/问界M7 连续性（2023-08-01..2023-10-31）。

序列：沪深300 / 516110 / 既有智驾龙头(德赛/浙江/万安/众泰) + 华为汽车核心
（赛力斯601127 / 江淮600418 / 华阳002906 / 德迈仕301007 / 铭科精技001319）。
新增股票：2023-09 华为汽车/问界M7/ADS2.0 公开行情 af parse（当代 contemporaneous evidence）支持。
raw+adjusted 入库。幂等。用法: python scripts/fetch_market_huawei.py
"""
import sys, os, time, json, urllib.request, urllib.parse
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

conn = db.connect()
db.migrate(conn)
HDRS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120', 'Referer': 'https://gu.qq.com/'}
BEG, END = "2023-08-01", "2023-10-31"
SERIES = {
    "SH000300": ("sh000300", "沪深300(基准)", "benchmark"),
    "AUTO_ETF_516110": ("sh516110", "汽车ETF(2023行业代理)", "industry_index"),
    "DESAYSV": ("sz002920", "德赛西威", "stock"),
    "ZHEJIANGSHISHI": ("sz002703", "浙江世宝", "stock"),
    "WANAN": ("sz002590", "万安科技", "stock"),
    "ZTELEVISION": ("sz000980", "众泰汽车", "stock"),
    # 华为汽车核心（contemporaneous 2023-09 问界M7/ADS2.0 行情）
    "SAILISI": ("sh601127", "赛力斯", "stock"),
    "JAC": ("sh600418", "江淮汽车", "stock"),
    "HUAYANG": ("sz002906", "华阳集团", "stock"),
    "DEMEISHI": ("sz301007", "德迈仕", "stock"),
    "MINGKEJINGJI": ("sz001319", "铭科精技", "stock"),
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
    p = {"param": f"{symbol},day,{BEG},{END},600,{fq}"}
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
            "adjustment_method": "qfq", "description": f"2023-08~10 {name}（腾讯GTIMG）"})
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
    print("DONE huawei-2023")


if __name__ == "__main__":
    main()