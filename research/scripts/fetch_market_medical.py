"""Medical Health 最小数据集：行情序列拉取（Research → DB）。

背景（Medical Health Minimum Dataset v0.1）：
- 首次将非汽车 Macro Theme（医药健康）接入 ThreeC 数据链路，验证 Research → DB → Export → Timeline。
- 本脚本只做「最小验证集合」：7 只代表标的 + 1 条行业代理，覆盖 2019-01-01 ~ 2022-12-31。
- **不覆盖医药行业**，只为验证 Campaign lifecycle（Peak/End 口径按 v1.1 §6：用 Campaign 自身代表标的）。

数据来源：腾讯财经 GTIMG（`web.ifzq.gtimg.cn`，免费无 key；与既有 fetch_market_tx.py 同源）。
- 单次请求约 700 根上限，故按「年」分段拉取（每年 ~243 根），合并后去重。
- raw 与 adjusted(qfq) 两套均入库；每行 data_source='tencent_gtimg'。
- 幂等：market_daily 主键 (series_id, trade_date, price_type)，INSERT OR REPLACE 可重复运行。

禁止：不伪造数据；取不到的标的如实失败并报告（不填 0）。

用法: python scripts/fetch_market_medical.py
"""
import sys, os, json, csv, time, urllib.request, urllib.parse
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

HDRS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120',
        'Referer': 'https://gu.qq.com/'}

BEG_YEAR, END_YEAR = 2019, 2022
RAW_DIR = os.path.join(db.ROOT, "data", "market", "raw")
NORM_DIR = os.path.join(db.ROOT, "data", "market", "normalized")

# series_id -> (tencent_symbol, name, series_type, description)
# 说明：Campaign 归属
#   创新药产业链升级（主线）→ HENGRUI / WUXIAPPTEC / TIGERMED
#   疫情医疗（RC）        → INTCO / ZHIFEI
#   中药（RC）            → PIANZAIHUANG / YILING
#   行业代理（仅参照，不作 Campaign Peak 口径）→ PHARMA_ETF_512010
MEDICAL_SERIES = {
    "HENGRUI": ("sh600276", "恒瑞医药", "stock",
                "创新药龙头（创新药产业链升级主线代表标的）"),
    "WUXIAPPTEC": ("sh603259", "药明康德", "stock",
                   "创新药产业链·CXO 龙头（Sub-theme 代表标的）"),
    "TIGERMED": ("sz300347", "泰格医药", "stock",
                 "临床 CRO 龙头（CXO Sub-theme 代表标的）"),
    "INTCO": ("sz300677", "英科医疗", "stock",
              "一次性防护手套龙头（疫情医疗 Candidate 代表标的）"),
    "ZHIFEI": ("sz300122", "智飞生物", "stock",
               "疫苗龙头（疫情医疗 Candidate 代表标的）"),
    "PIANZAIHUANG": ("sh600436", "片仔癀", "stock",
                     "品牌中药（中药 Candidate 代表标的）"),
    "YILING": ("sz002603", "以岭药业", "stock",
               "中药创新/抗疫中药（中药 Candidate 代表标的）"),
    "PHARMA_ETF_512010": ("sh512010", "医药ETF(沪深300医药, 行业代理)", "industry_index",
                          "医药行业代理（仅作参照；Campaign Peak 不得使用上位指数口径，见 v1.1 §6）"),
}


def fetch(symbol, beg, end, fq, retries=4):
    """单段拉取。fq='' 为不复权，'qfq' 为前复权。"""
    params = {"param": f"{symbol},day,{beg},{end},700,{fq}"}
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urllib.parse.urlencode(params)
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            data = json.loads(urllib.request.urlopen(req, timeout=25).read().decode('utf-8', 'ignore'))
            d = data.get("data", {}).get(symbol, {})
            ser = d.get((fq or "") + "day") or d.get(fq) or d.get("day") or []
            if ser:
                return ser
        except Exception:
            time.sleep(1.5 + i)
    return []


def fetch_range(symbol, fq):
    """按年分段拉取并合并（腾讯单次 ~700 根上限）。"""
    merged, seen = [], set()
    for y in range(BEG_YEAR, END_YEAR + 1):
        for rec in fetch(symbol, f"{y}-01-01", f"{y}-12-31", fq):
            if rec[0] not in seen:
                seen.add(rec[0])
                merged.append(rec)
        time.sleep(0.5)
    merged.sort(key=lambda r: r[0])
    return merged


def _num(x):
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str) and x.strip():
        try:
            return float(x)
        except ValueError:
            return None
    return None


def to_row(rec, series_id, price_type):
    close = _num(rec[2])
    return (series_id, rec[0], _num(rec[1]), _num(rec[3]), _num(rec[4]), close,
            close if price_type == "adjusted" else None,
            price_type,
            _num(rec[5]) if len(rec) > 5 else None,
            _num(rec[6]) if len(rec) > 6 else None,
            "tencent_gtimg", datetime.now().isoformat())


INSERT_SQL = """INSERT OR REPLACE INTO market_daily
    (series_id, trade_date, open, high, low, close, adj_close, price_type, volume, amount, data_source, retrieved_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"""


def main():
    conn = db.connect()
    db.migrate(conn)

    # 1) 注册 market_series（幂等）
    for key, (sym, name, stype, desc) in MEDICAL_SERIES.items():
        db.insert(conn, "market_series", {
            "series_id": key, "name": name, "series_type": stype,
            "provider": "tencent", "symbol": sym, "frequency": "daily",
            "price_type": "adjusted", "adjustment_method": "qfq",
            "description": desc,
        })
    print(f"[series] 注册 {len(MEDICAL_SERIES)} 条 market_series")

    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(NORM_DIR, exist_ok=True)
    fields = ["date", "open", "high", "low", "close", "volume", "amount", "price_type"]

    summary, failed = {}, []
    for key, (sym, name, _stype, _desc) in MEDICAL_SERIES.items():
        raw = fetch_range(sym, "")
        qfq = fetch_range(sym, "qfq")
        if not raw or not qfq:
            failed.append((key, sym, len(raw), len(qfq)))
            print(f"  !! {key} ({name}) 拉取失败 raw={len(raw)} qfq={len(qfq)}（如实记录，不填 0）")
            continue

        rows = [to_row(r, key, "raw") for r in raw] + [to_row(r, key, "adjusted") for r in qfq]
        conn.executemany(INSERT_SQL, rows)
        conn.commit()

        with open(os.path.join(RAW_DIR, f"tencent_{key}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(fields)
            for r in raw:
                w.writerow([r[0], r[1], r[3], r[4], r[2], r[5] if len(r) > 5 else "",
                            r[6] if len(r) > 6 else "", "raw"])
        with open(os.path.join(NORM_DIR, f"{key}_daily.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(fields)
            for r in raw:
                w.writerow([r[0], r[1], r[3], r[4], r[2], r[5] if len(r) > 5 else "",
                            r[6] if len(r) > 6 else "", "raw"])
            for r in qfq:
                w.writerow([r[0], r[1], r[3], r[4], r[2], r[5] if len(r) > 5 else "",
                            r[6] if len(r) > 6 else "", "adjusted"])

        summary[key] = {"raw": len(raw), "qfq": len(qfq),
                        "first": raw[0][0], "last": raw[-1][0]}
        print(f"  {key:20s} {name:22s} raw={len(raw):4d} qfq={len(qfq):4d}  {raw[0][0]} ~ {raw[-1][0]}")
        time.sleep(0.5)

    conn.close()
    print("\nDONE", json.dumps({"series": summary, "failed": failed}, ensure_ascii=False))


if __name__ == "__main__":
    main()
