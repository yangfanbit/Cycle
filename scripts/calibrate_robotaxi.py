"""Pilot 1-C1 Calibration：C-2024-ROBOTAXI 行情核验（真实数据计算 + Date Observation）。

- 读取 market_daily（腾讯GTIMG，一律用 adjusted(qfq) close 计算收益；相对基准用同口径）。
- 计算：窗口累计/日收益、5/10/20d 收益、相对沪深300超额、回撤、成交量变化。
- 更新 campaign_date_observations（candidate 保留；verified 记 observed candidate，低置信、market_data）。
- 输出 research/c2/2024_robotaxi_market_validation.md。
不修改 campaigns / annual_reviews / rule。不做统计模型。
"""
import sys, os, json
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db
from scripts.market_metrics import daily_return, cumulative_return, drawdown, max_drawdown, volume_change

conn = db.connect()

BENCH = "SH000300"
AUTO = "AUTO_ETF_516110"
CORES = ["DAZHONGTONG", "JINJIANG", "JINLONG", "XINGYUYUDA", "TIANMAI"]
CAMP = "C-2024-ROBOTAXI"

# 关键观察窗口
WIN0 = "2024-07-08"; WIN1 = "2024-07-31"


def load(sid):
    rows = conn.execute(
        "SELECT trade_date, close FROM market_daily WHERE series_id=? AND price_type='adjusted' ORDER BY trade_date",
        (sid,)).fetchall()
    return {r["trade_date"]: r["close"] for r in rows}


SER = {sid: load(sid) for sid in [BENCH, AUTO] + CORES}
DATES = sorted(SER[BENCH].keys())


def ret_between(series, d0, d1):
    if d0 in SER[series] and d1 in SER[series] and SER[series][d0]:
        return SER[series][d1] / SER[series][d0] - 1.0
    return None


def n_days_ret(series, anchor, n):
    """anchor 前 n 个交易日至 anchor 的区间收益（用于启动前 1/后 1 等）。"""
    ds = [d for d in DATES if d <= anchor]
    if len(ds) <= n:
        return None
    d0 = ds[-(n + 1)]
    return ret_between(series, d0, anchor)


def peak_in_range(series, a, b):
    """a~b 内收盘最高之日(或次日回落前的峰值日)。"""
    best_d, best = None, None
    for d in DATES:
        if a <= d <= b:
            v = SER[series].get(d)
            if v is not None and (best is None or v > best):
                best, best_d = v, d
    return best_d, best


def dump():
    out = {"bench": BENCH, "auto": AUTO, "cores": CORES, "window": (WIN0, WIN1), "data": {}}
    for sid in [BENCH, AUTO] + CORES:
        info = {
            "cum_null": ret_between(sid, WIN0, WIN1),
            "cum_0708_0730": ret_between(sid, "2024-07-08", "2024-07-30"),
            "d0708": SER[sid].get("2024-07-08"), "d0709": SER[sid].get("2024-07-09"), "d0710": SER[sid].get("2024-07-10"),
            "acc0709": ret_between(sid, "2024-07-08", "2024-07-09"),
            "acc0710": ret_between(sid, "2024-07-08", "2024-07-10"),
            "acc0711": ret_between(sid, "2024-07-08", "2024-07-11"),
        "peak_0708_0831": peak_in_range(sid, "2024-07-08", "2024-08-31"),
        "maxdd_0708_0831": max_drawdown([SER[sid][d] for d in DATES if "2024-07-08" <= d <= "2024-08-31"]),
        "close_0831": SER[sid].get("2024-08-31"),
        "rel_bench_win": ret_between(sid, WIN0, WIN1) - ret_between(BENCH, WIN0, WIN1),
    }
        # 关键日均线（启动 5/10/20 日）
        info["ret5_0708"] = n_days_ret(sid, "2024-07-08", 5)
        info["ret10_0708"] = n_days_ret(sid, "2024-07-08", 10)
        out["data"][sid] = info
    # 龙头平均（等权收盘）
    avg = {}
    for d in DATES:
        vals = [SER[s][d] for s in CORES if SER[s].get(d)]
        if vals:
            avg[d] = sum(vals) / len(vals)
    out["data"]["ROBOTAXI_AVG"] = {
        "cum_null": avg[WIN1] / avg[WIN0] - 1 if WIN0 in avg and WIN1 in avg else None,
        "d0708": avg.get("2024-07-08"),
        "acc0709": (avg["2024-07-09"]/avg["2024-07-08"]-1 if all(x in avg for x in ["2024-07-08","2024-07-09"]) else None),
        "acc0710": (avg["2024-07-10"]/avg["2024-07-08"]-1 if all(x in avg for x in ["2024-07-08","2024-07-10"]) else None),
        "acc0711": (avg["2024-07-11"]/avg["2024-07-08"]-1 if all(x in avg for x in ["2024-07-08","2024-07-11"]) else None),
        "maxdd_0708_0831": max_drawdown([avg[d] for d in avg]),
    }
    # 龙头平均的真实峰值（自定义）
    best_d, best = None, None
    for d in DATES:
        if "2024-07-08" <= d <= "2024-08-31" and d in avg:
            if best is None or avg[d] > best:
                best, best_d = avg[d], d
    out["data"]["ROBOTAXI_AVG"]["peak_0708_0831"] = (best_d, best)
    return out


def main():
    res = dump()
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    c2dir = os.path.join(db.ROOT, "research", "c2")
    os.makedirs(c2dir, exist_ok=True)
    with open(os.path.join(c2dir, "_calib_raw.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    # ---- Date Observation（candidate 保留，verified 记 observed，不覆盖 campaigns）----
    # 更新已存在/新建观测：verified_date 只记“观察候选”，不覆盖 candidate_date。
    obs = {
        "start": ("2024-07-08 ", "启动：07/08为起势、07/09龙头等权单日+13%（首个广泛反应日）"),
        "peak": ("2024-07-30 ", "峰值：龙头5只等权收盘于07/30见顶(19.85)；大众交通个股高点在08/05"),
        "end": ("2024-07-31 ", "End:07/31为首次回落(等权18.80)，非最终结束；8/15金龙再创新高=secondary rally"),
    }
    for role in ("start", "peak", "end"):
        oid = f"OBS-{CAMP}-{role}"
        if oid in {r[0] for r in conn.execute(
                "SELECT observation_id FROM campaign_date_observations WHERE campaign_id=?", (CAMP,))}:
            conn.execute(
                "UPDATE campaign_date_observations SET verified_date=?, verification_method=?, confidence=?, notes=? "
                "WHERE observation_id=?", (obs[role][0] + "(observed candidate)", "market_data", "low",
                                            obs[role][1], oid))
        else:
            db.insert(conn, "campaign_date_observations", {
                "observation_id": oid, "campaign_id": CAMP, "date_role": role,
                "candidate_date": {"start": "2024-07-08", "peak": "2024-07-29", "end": "2024-07-31"}[role],
                "verified_date": obs[role][0] + "(observed candidate)",
                "verification_method": "market_data", "confidence": "low",
                "evidence_id": None, "notes": obs[role][1],
            })
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()