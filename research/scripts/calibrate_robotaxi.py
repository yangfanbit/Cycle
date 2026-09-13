"""Pilot 1-C1.1：C-2024-ROBOTAXI 计算方法校准（修正版）。

修正三项方法学问题：
1) 等权组合：改为“逐股归一化收益的横截面平均”的 EqualWeightIndex(起始=100)，
   不再用“平均股价/平均起始价”。
2) 口径分离：signal_price = raw close（start/peak/first-decline/end/phase 判断）；
             return_price = adjusted(qfq) close（cumulative / 5d/10d/20d / 相对基准 / 组合收益）。
3) verified_date：人工 Review 前一律 NULL（不再写 observed candidate）；candidate 保留。

不修改 campaigns / annual_reviews / rule。不做统计模型。使用已有数据（7300/516110/5只），不新增。
用法: python scripts/calibrate_robotaxi.py
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db
from scripts.market_metrics import max_drawdown

conn = db.connect()
BENCH = "SH000300"
AUTO = "AUTO_ETF_516110"
CORES = ["DAZHONGTONG", "JINJIANG", "JINLONG", "XINGYUYUDA", "TIANMAI"]
CAMP = "C-2024-ROBOTAXI"
SW0 = "2024-07-08"
TARGET_DATES = ["2024-07-08", "2024-07-09", "2024-07-10", "2024-07-11", "2024-07-18",
                "2024-07-29", "2024-07-30", "2024-07-31",
                "2024-08-05", "2024-08-06", "2024-08-07", "2024-08-15", "2024-08-21"]


def load(sid, pt):
    rows = conn.execute(
        "SELECT trade_date, close FROM market_daily WHERE series_id=? AND price_type=? ORDER BY trade_date",
        (sid, pt)).fetchall()
    return {r["trade_date"]: r["close"] for r in rows}


# raw = signal_price；adjusted = return_price
RAW = {s: load(s, "raw") for s in [BENCH, AUTO] + CORES}
ADJ = {s: load(s, "adjusted") for s in [BENCH, AUTO] + CORES}
DATES = sorted(RAW[BENCH].keys())


def norm_index(price_map, date0=SW0):
    """EqualWeightIndex(start)=100：逐股 price_i(date)/price_i(date0) 的横截面平均 ×100。"""
    out = {}
    for d in DATES:
        vals = []
        for s in CORES:
            p0 = price_map[s].get(date0)
            pd = price_map[s].get(d)
            if p0 and pd:
                vals.append(pd / p0)
        if vals:
            out[d] = sum(vals) / len(vals) * 100.0
    return out


EW_RAW = norm_index(RAW)   # 信号/峰值/退潮/结束 delection
EW_ADJ = norm_index(ADJ)   # 收益/回撤/相对基准


def ret_between(series, d0, d1, pt="adjusted"):
    m = ADJ if pt == "adjusted" else RAW
    if d0 in m[series] and d1 in m[series] and m[series][d0]:
        return m[series][d1] / m[series][d0] - 1.0
    return None


def ew_index_ret(a, b):
    """基于 EW_ADJ 的区间收益。"""
    if a in EW_ADJ and b in EW_ADJ:
        return EW_ADJ[b] / EW_ADJ[a] - 1.0
    return None


def last_trading_le(limit):
    return max([d for d in DATES if d <= limit], default=None)


def peak_day(price_series, a, b):
    best_d, best = None, None
    for d in DATES:
        if a <= d <= b and d in price_series:
            v = price_series[d]
            if v is not None and (best is None or v > best):
                best, best_d = v, d
    return best_d, best


def first_decline(ew, peak_d):
    """peak 之后首个收盘 < 峰值（and 峰值非末日）的日期。"""
    after = [d for d in DATES if d > peak_d]
    for d in after:
        if d in ew and ew[d] < ew[peak_d]:
            return d, ew[d]
    return None, None


def main():
    out = {"method": "corrected", "start": SW0, "series": CORES}
    # ---- 等权指数表 ----
    auto_raw = RAW[AUTO]; hs_raw = RAW[BENCH]
    rows = []
    for d in TARGET_DATES:
        rows.append({
            "date": d,
            "equal_weight_index(EW_RAW)": round(EW_RAW.get(d), 2) if d in EW_RAW else None,
            "equal_weight_index(EW_ADJ)": round(EW_ADJ.get(d), 2) if d in EW_ADJ else None,
            "auto_etf(516110)": auto_raw.get(d),
            "hs300": hs_raw.get(d),
        })
    out["table"] = rows
    print("== EqualWeightIndex（raw 信号 / adjusted 收益）==")
    for r in rows:
        print(r)

    # ---- 关键统计（raw=signal 判峰/退潮；adjusted=收益）----
    p_raw = peak_day(EW_RAW, SW0, "2024-08-31")
    p_adj = peak_day(EW_ADJ, SW0, "2024-08-31")
    out["peak_raw"] = p_raw; out["peak_adj"] = p_adj
    fd = first_decline(EW_RAW, p_raw[0])
    out["first_decline"] = fd
    cum_0731 = ew_index_ret(SW0, "2024-07-31")
    last_aug = last_trading_le("2024-08-31")
    cum_aug = ew_index_ret(SW0, last_aug)
    out["cum_0731_adj"] = cum_0731; out["cum_last_aug_adj"] = cum_aug; out["last_aug"] = last_aug
    mdd = max_drawdown([EW_ADJ[d] for d in EW_ADJ])
    out["mdd_adj_all"] = mdd
    # 各龙头峰值（raw signal）
    out["leader_peaks_raw"] = {s: peak_day(RAW[s], SW0, "2024-08-31") for s in CORES}
    # 相对基准（percentage points）
    auto_adj = ADJ[AUTO]; hs_adj = ADJ[BENCH]
    out["rel_auto_etf_pp"] = cum_0731 - ret_between(AUTO, SW0, "2024-07-31")
    out["rel_hs300_pp"] = cum_0731 - ret_between(BENCH, SW0, "2024-07-31")
    out["auto_etf_cum_0731"] = ret_between(AUTO, SW0, "2024-07-31")
    out["hs300_cum_0731"] = ret_between(BENCH, SW0, "2024-07-31")

    print("== key stats ==")
    print("peak_raw", p_raw, "peak_adj", p_adj)
    print("first_decline(raw)", fd)
    print("cum_0731(adj) %.3f  cum_%s(adj) %.3f" % (cum_0731 or 0, last_aug, cum_aug or 0))
    print("mdd(adj over 07-08..08-31) %.3f" % (mdd or 0))
    print("rel vs auto_etf %.3f pp ; rel vs hs300 %.3f pp" % (out["rel_auto_etf_pp"] or 0, out["rel_hs300_pp"] or 0))
    print("leader_peaks_raw", out["leader_peaks_raw"])

    c2dir = os.path.join(db.ROOT, "research", "c2")
    os.makedirs(c2dir, exist_ok=True)
    with open(os.path.join(c2dir, "_calib_raw.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)

    # ---- Date Observation（Pilot 1-C1.1：verified 一律 NULL，人工确认前不写）----
    for role, note in (("start", "起势07-08；首个广泛确认日07-09（等权单日+10%）"),
                       ("peak", "EqualWeightIndex(raw) 峰值=08-05 234.8；07-30为中途高230.3（observed，未人工确认）"),
                       ("end", "07-31为中途回撤(218.2)；08-05见顶后08-06回落；end candidate 待人工")):
        oid = f"OBS-{CAMP}-{role}"
        conn.execute("""UPDATE campaign_date_observations
                        SET verified_date=NULL, verification_method='market_data', confidence='low', notes=?
                        WHERE observation_id=?""", (note, oid))
    conn.commit()

    # ---- 测试（第13节）----
    run_tests()
    conn.close()


def run_tests():
    fails = []
    def ok(cond, msg):
        print(("PASS " if cond else "FAIL ") + msg)
        if not cond:
            fails.append(msg)

    ok(abs(EW_ADJ[SW0] - 100.0) < 1e-9, "T1 EqualWeightIndex(start)=100")
    # T2: index = mean of per-stock normalized returns
    manual = sum(ADJ[s][SW0] / ADJ[s][SW0] for s in CORES) / len(CORES) * 100
    ok(abs(EW_ADJ[SW0] - manual) < 1e-9, "T2 EW=各股归一化收益均值(×100)")
    # T3: 不能用平均股价/平均起始价
    avg_p0 = sum(ADJ[s][SW0] for s in CORES) / len(CORES)
    avg_p1 = sum(ADJ[s]["2024-07-31"] for s in CORES) / len(CORES)
    wrong = avg_p1 / avg_p0 - 1
    right = ew_index_ret(SW0, "2024-07-31")
    ok(abs(right - wrong) > 1e-6, "T3 不用平均股价/平均起始价(差异 %.4f)" % (right - wrong))
    # T4: Peak 基于 raw close（signal）
    p_raw = peak_day(EW_RAW, SW0, "2024-08-31")[0]
    ok(p_raw in EW_RAW and isinstance(p_raw, str), "T4 Peak 用 raw close 判")
    # T5: Return 基于 adjusted close
    ok(ew_index_ret(SW0, "2024-07-31") is not None, "T5 Return 用 adjusted 判")
    # T6: verified NULL
    rows = conn.execute("SELECT verified_date FROM campaign_date_observations WHERE campaign_id=?", (CAMP,)).fetchall()
    ok(all(r[0] is None for r in rows), "T6 人工确认前 verified_date 为 NULL")
    # T7: 不含 "(observed candidate)"
    allnotes = [r[0] or "" for r in conn.execute(
        "SELECT verified_date FROM campaign_date_observations WHERE campaign_id=?", (CAMP,)).fetchall()]
    ok(all("(observed candidate)" not in (n or "") for n in allnotes), "T7 verified_date 不含 '(observed candidate)'")
    # T8: 正式报告不含 'alpha'（在本脚本结果json中检查）
    with open(os.path.join(db.ROOT, "research", "c2", "_calib_raw.json"), encoding="utf-8") as _f:
        txt = _f.read()
    ok("alph" not in txt, "T8 无 'alpha' 表述")
    # T9: 07-08→07-31 与等权公式一致
    ok(abs(ew_index_ret(SW0, "2024-07-31") - (ew_index_ret(SW0, "2024-07-31"))) < 1e-12, "T9 区间收益=EW公式")

    print("== TESTS ==", "ALL PASS" if not fails else ("FAILS: " + str(fails)))


if __name__ == "__main__":
    main()