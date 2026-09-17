"""补齐「电力设备」历史 Cycle 所需的行情数据（腾讯财经 GTIMG，免费无 key）。

背景（Wave 1A — 电力设备历史 Cycle）：
- Historical Coverage Audit v0.1 确认历史侧只有 TH-AUTO / TH-PHARMA，
  「电力设备」在 taxonomy 与行情数据中均为空白。
- 本脚本只为**已经通过证据裁决**的电力设备 Campaign 拉取代表标的日线，
  用于**核验生命周期日期**（Peak / 区间），不作为主题形成的判定依据。

纪律（遵循 market_data_validation.md / seed_medical_min.py 的既有做法）：
- 每行明确 price_type（raw / adjusted(qfq)），两套都写，禁止混用口径。
- 同一 series+date+price_type 唯一（INSERT OR REPLACE，幂等）。
- 所有 symbol 均为真实可访问代码；data_source='tencent_gtimg' 可追溯。
- 拉不到的区间如实保留缺口，不伪造、不前向填充。

用法: python scripts/fetch_market_power.py
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
#
# ⚠️ 已知上游数据缺陷（2026-09-17 实测，本脚本**刻意不纳入**）：
#   通威股份 sh600438 的腾讯 **前复权（qfq）** 序列在 2018 年区间返回非正价格
#   （如 2018-10-18 close = -0.218，而同日 raw close = 5.04）。
#   已直接请求腾讯接口确认：是上游返回本身的问题（`data.sh600438.qfqday` 即含负值），
#   不是本地解析错误。因「不伪造 / 不写入已知损坏数据」的纪律，本轮不登记该序列；
#   硅料环节改由 特变电工（TBEA，含新特能源多晶硅）作旁证，并在 Campaign
#   research_notes 中显式标注该混淆。
FETCH_PLAN = {
    # ---- 光伏 / 新能源发电设备（power_ne_equipment_2020_2022）----
    "LONGI":      ("sh601012", "隆基绿能(单晶硅片/组件)", "stock", "2018-01-01", "2022-12-31"),
    "SUNGROW":    ("sz300274", "阳光电源(光伏逆变器)", "stock", "2018-01-01", "2022-12-31"),
    "GOLDWIND":   ("sz002202", "金风科技(风电整机)", "stock", "2018-01-01", "2022-12-31"),
    # ---- 电网 / 输配电设备（power_grid_uhv_2022_2025）----
    "NARI":       ("sh600406", "国电南瑞(电网自动化)", "stock", "2022-01-01", "2025-12-31"),
    "TBEA":       ("sh600089", "特变电工(变压器/输变电)", "stock", "2022-01-01", "2025-12-31"),
    "XUJI":       ("sz000400", "许继电气(直流输电设备)", "stock", "2022-01-01", "2025-12-31"),
    "PINGGAO":    ("sh600312", "平高电气(高压开关)", "stock", "2022-01-01", "2025-12-31"),
    "SIEYUAN":    ("sz002028", "思源电气(输配电设备)", "stock", "2022-01-01", "2025-12-31"),
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
                time.sleep(1.2 + i * 0.8)
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
        conn.execute(
            "INSERT INTO market_series (series_id, name, series_type, provider, symbol, frequency, price_type, adjustment_method, description) "
            "VALUES (?,?,?,?,?, 'daily','adjusted','qfq',?) "
            "ON CONFLICT(series_id) DO UPDATE SET name=excluded.name, symbol=excluded.symbol",
            (key, name, stype, "tencent", sym, f"腾讯GTIMG日线(qfq) 电力设备 Wave 1A {beg}~{end}"))
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
        time.sleep(0.5)
    conn.close()
    print("DONE", json.dumps(summary, ensure_ascii=False, default=str), flush=True)


if __name__ == "__main__":
    main()
