"""Pilot 1-C1 Calibration：从腾讯财经(GTIMG)拉取真实日线并入库。

Provider 说明：
- 本机实验中 eastmoney(push2his) 与 swsindex.com 连接被重置/不可达、tushare MCP 无权限，
  故选用可稳定访问的腾讯财经 web.ifzq.gtimg.cn（免费、无 key）。
- 腾讯不提供申万行业指数(801880)，故 AUTO_SW 本轮无真实数据（如实标注 unavailable）；
  Layer A（汽车行业整体）改用真实指数挂钩的“汽车ETF sh516110(中证800汽车)”作代理（非伪造、非成分回填）。
- 所有 symbol 均为真实可访问代码；每行记录 data_source='tencent_gtimg'。

入库：market_daily（raw + adjusted(qfq) 两套，price_type 区分）。
文件：data/market/raw/*.csv、data/market/normalized/*.csv。
幂等：可重复运行。

用法: python scripts/fetch_market_tx.py
"""
import sys, os, json, csv, time, urllib.request, urllib.parse
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

conn = db.connect()
db.migrate(conn)

HDRS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120',
        'Referer': 'https://gu.qq.com/'}
BEG, END = "2024-05-01", "2024-09-30"
RAW_DIR = os.path.join(db.ROOT, "data", "market", "raw")
NORM_DIR = os.path.join(db.ROOT, "data", "market", "normalized")

# series_key -> (tencent_symbol, name, series_type)
SERIES = {
    # 现有 series
    "SH000300": ("sh000300", "沪深300(基准)", "benchmark"),
    "AUTO_ETF_516110": ("sh516110", "汽车ETF(中证800汽车, 行业代理)", "industry_index"),
    "DAZHONGTONG": ("sh600611", "大众交通", "stock"),
    "JINJIANG": ("sh600650", "锦江在线", "stock"),
    "JINLONG": ("sh600686", "金龙汽车", "stock"),
    "XINGYUYUDA": ("sz002829", "星网宇达", "stock"),
    "TIANMAI": ("sz300807", "天迈科技", "stock"),
}


def fetch(symbol, fq, retries=4):
    params = {"param": f"{symbol},day,{BEG},{END},700,{fq}"}
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urllib.parse.urlencode(params)
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            data = json.loads(urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore'))
            d = data.get("data", {}).get(symbol, {})
            ser = d.get(fq + "day") or d.get(fq) or d.get("day") or []
            if ser:
                return ser
        except Exception as e:
            time.sleep(1.5 + i)
    return []


def _num(x):
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str) and x.strip():
        try:
            return float(x)
        except ValueError:
            return None
    return None


def row_to_dict(rec, series_id, price_type):
    # Tencent: [date, open, close, high, low, volume, ?(可有 dict)]
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


def main():
    # 确保 market_series 存在
    for key, (sym, name, stype) in SERIES.items():
        db.insert(conn, "market_series", {
            "series_id": key, "name": name, "series_type": stype,
            "provider": "tencent", "symbol": sym, "frequency": "daily",
            "price_type": "adjusted", "adjustment_method": "qfq",
            "description": "腾讯财经GTIMG日线(qfq)，Pilot 1-C1 Calibration 已拉取" if key != "SH000300" else "沪深300基准(腾讯 sh000300 日线)",
        })
    conn.commit()

    summary = {}
    for key, (sym, name, _stype) in SERIES.items():
        raw = fetch(sym, "")
        qfq = fetch(sym, "qfq")
        # 写入 DB
        n = 0
        for rec in raw:
            db.insert(conn, "market_daily", row_to_dict(rec, key, "raw")); n += 1
        for rec in qfq:
            db.insert(conn, "market_daily", row_to_dict(rec, key, "adjusted")); n += 1
        # 写文件
        os.makedirs(RAW_DIR, exist_ok=True); os.makedirs(NORM_DIR, exist_ok=True)
        fields = ["trade_date", "open", "high", "low", "close", "volume", "amount", "price_type"]
        with open(os.path.join(RAW_DIR, f"tencent_{key}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["date","open","high","low","close","volume","amount","price_type"])
            for rec in raw:
                w.writerow([rec[0], rec[1], rec[3], rec[4], rec[2], rec[5],
                            rec[6] if len(rec) > 6 else "", "raw"])
        with open(os.path.join(NORM_DIR, f"{key}_daily.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for rec, pt in list(zip(raw, ["raw"] * len(raw))) + list(zip(qfq, ["adjusted"] * len(qfq))):
                d = row_to_dict(rec, key, pt)
                w.writerow({k: d.get(k) for k in fields})
        summary[key] = (len(raw), len(qfq))
        conn.commit()
        print(f"series {key} ({name}): raw={len(raw)} qfq={len(qfq)}")
        time.sleep(0.6)

    conn.close()
    print("DONE", json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()