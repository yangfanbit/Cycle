#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""recompute_market_regime_metrics_v0_1.py —— market_regime 两项统计口径的**只读复算**（v0.46）。

## 为什么有这个脚本

`MS-2026-10-23-01` 的 `MR-EV-02`（breadth）与 `MR-EV-04`（涨停家数）原先只由一次性探针算出，
**仓库里没有可复现的计算代码** → 审阅者无法核对。本脚本把两个口径固化为代码，
**只读**、不写任何产物、不参与 CI 门禁、不产生新的判定或阈值。

## 口径（与 `docs/MARKET_REGIME_AI_INTERFACE_v0.1.md` §2.3 / §2.5 一致）

### breadth（`breadth_state`）
- 分子：当日**上涨家数**（收盘价较上一交易日上涨，即 pct > 0）
- 分母：**上涨 + 下跌**（平盘不计入分母；见 `--denominator` 可切换以便核对）
- 样本：`scan_series.status = 'OK'` 的个股；当日与其**相邻交易日**（按 CSI300 交易日序列判定）
  都必须有**有效收盘价**（非 NULL、非 0）
  - 停牌 → 当日无行 → 自然不计入分子/分母
  - 新股首日 → 无上一交易日收盘 → 自然排除
  - ST → **不剔除**（库内 `name` 只是抓取时点的名称，无法还原历史 ST 状态；
    见 `--exclude-st` 的敏感性对比）
- 周值 = 该 ISO 周内**逐日占比的算术平均**（不是「合计上涨 / 合计可比」的池化口径）
- 4 周值 = 4 个周值的算术平均

### 涨停家数（`risk_appetite_state` 的信号之一）
- 判定：收盘价相对上一**相邻交易日**收盘的涨跌幅落在板块档位带内
  - 主板（含中小板）：9.8% – 10.6%
  - 创业板（300\*，2020-08-24 起）/ 科创板（688\*）：19.5% – 21.2%
  - 北交所（bj / 4\* / 8\* / 92\*）：**不检测**（本项目未定义 30% 档；按主板档计入会产生假涨停）
- ST：**不剔除**（同 breadth，无法还原历史 ST 状态）
- 周值 = 该周**逐日家数的算术平均**；两组对比 = 两组周值的算术平均

## 用法

    python research/scripts/recompute_market_regime_metrics_v0_1.py
    python research/scripts/recompute_market_regime_metrics_v0_1.py --json
    python research/scripts/recompute_market_regime_metrics_v0_1.py --as-of 2026-10-23
    python research/scripts/recompute_market_regime_metrics_v0_1.py --denominator all   # 敏感性
    python research/scripts/recompute_market_regime_metrics_v0_1.py --exclude-st        # 敏感性
"""
import argparse
import collections
import datetime
import json
import os
import sqlite3
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DB = os.path.join(REPO, "research", "database", "history_scan.db")

# ★ 与 docs/MARKET_REGIME_AI_INTERFACE_v0.1.md §2 一致；**不得**在这里新增档位
BAND_MAIN = (9.8, 10.6)
BAND_GROWTH = (19.5, 21.2)      # 创业板 2020-08-24 起 / 科创板
GEM_REFORM = "2020-08-24"


def code_of(series_id):
    """sh688137 → 688137；sz300123 → 300123；bj920023 → 920023"""
    return series_id[2:] if series_id[:2] in ("sh", "sz", "bj") else series_id


def is_bse(series_id):
    c = code_of(series_id)
    return series_id.startswith("bj") or c[:1] in ("4", "8") or c.startswith("92")


def band_of(series_id, date):
    """返回 (lo, hi)；None 表示该板块不在检测范围。"""
    c = code_of(series_id)
    if c.startswith("688"):
        return BAND_GROWTH
    if c.startswith("300"):
        return BAND_GROWTH if date >= GEM_REFORM else BAND_MAIN
    if is_bse(series_id):
        return None
    return BAND_MAIN


def iso_week(date):
    return datetime.date(int(date[:4]), int(date[5:7]), int(date[8:10])).isocalendar()[1]


def load(con, begin, end):
    """{series_id: {date: close}}（仅 status='OK' 的个股）"""
    out = collections.defaultdict(dict)
    for sid, d, c in con.execute(
            "SELECT d.series_id, d.trade_date, d.close FROM scan_daily d "
            "JOIN scan_series s ON s.series_id = d.series_id "
            "WHERE s.kind = 'stock' AND s.status = 'OK' "
            "AND d.trade_date BETWEEN ? AND ?", (begin, end)):
        out[sid][d] = c
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", default=None, help="右端点（默认取 CSI300 最后一个交易日）")
    ap.add_argument("--weeks", default="36-43", help="要统计的 ISO 周区间，如 36-43")
    ap.add_argument("--denominator", choices=["updn", "all"], default="updn",
                    help="breadth 分母：updn=上涨+下跌（默认，平盘不计）；all=含平盘")
    ap.add_argument("--exclude-st", action="store_true",
                    help="剔除名称含 ST 的个股（敏感性对比用；**不是**主口径）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    if not os.path.exists(DB):
        print("SKIP: history_scan.db 不存在（CI 不携带该库，1.3 GB 未入库）")
        return 0

    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        cal = [r[0] for r in con.execute(
            "SELECT trade_date FROM scan_daily WHERE series_id='CSI300' ORDER BY trade_date")]
        if not cal:
            print("FAIL: 缺 CSI300 交易日序列"); return 1
        as_of = a.as_of or cal[-1]
        cal = [d for d in cal if d <= as_of]
        pos = {d: i for i, d in enumerate(cal)}

        w_lo, w_hi = (int(x) for x in a.weeks.split("-"))
        # 往前多取 30 个交易日，保证每组第一周的首日也有前收盘
        i0 = max(0, pos[cal[-1]] - 30 * 3)
        begin = cal[i0] if cal else as_of
        rows = load(con, begin, as_of)
        names = dict(con.execute(
            "SELECT series_id, name FROM scan_series WHERE kind='stock' AND status='OK'"))
    finally:
        con.close()

    def keep(sid):
        return not (a.exclude_st and "ST" in (names.get(sid) or ""))

    breadth_day = collections.defaultdict(lambda: [0, 0, 0])   # up, down, flat
    limit_day = collections.Counter()
    for sid, s in rows.items():
        if not keep(sid):
            continue
        ds = sorted(s)
        for i in range(1, len(ds)):
            d0, d1 = ds[i - 1], ds[i]
            if pos.get(d1, -1) - pos.get(d0, -1) != 1:
                continue                                  # 必须相邻交易日
            c0, c1 = s[d0], s[d1]
            if not c0 or not c1:
                continue                                  # 无有效收盘 → 排除
            pct = (c1 / c0 - 1) * 100
            b = breadth_day[d1]
            if pct > 0: b[0] += 1
            elif pct < 0: b[1] += 1
            else: b[2] += 1
            band = band_of(sid, d1)
            if band and band[0] <= pct <= band[1]:
                limit_day[d1] += 1

    # ---- breadth：周内逐日占比的算术平均 ----
    wk_ratio = collections.defaultdict(list)
    for d, (up, dn, flat) in breadth_day.items():
        den = up + dn if a.denominator == "updn" else up + dn + flat
        if den:
            wk_ratio[iso_week(d)].append(up / den)

    weeks = [w for w in range(w_lo, w_hi + 1) if wk_ratio.get(w)]
    breadth = [{"week": w, "days": len(wk_ratio[w]),
                "mean_pct": round(100 * statistics.mean(wk_ratio[w]), 2)} for w in weeks]
    b4 = [x["mean_pct"] for x in breadth[-4:]]
    breadth_4w = round(statistics.mean(b4), 2) if len(b4) == 4 else None

    # ---- 涨停家数：周内逐日家数的算术平均 ----
    wk_cnt = collections.defaultdict(list)
    for d, n in limit_day.items():
        wk_cnt[iso_week(d)].append(n)
    limits = [{"week": w, "days": len(wk_cnt[w]),
               "mean_per_day": round(statistics.mean(wk_cnt[w]), 1),
               "total": sum(wk_cnt[w])} for w in weeks if wk_cnt.get(w)]
    cur = [x["mean_per_day"] for x in limits if x["week"] >= w_hi - 3]
    prev = [x["mean_per_day"] for x in limits if w_hi - 7 <= x["week"] < w_hi - 3]
    cur_avg = round(statistics.mean(cur), 1) if cur else None
    prev_avg = round(statistics.mean(prev), 1) if prev else None
    chg = round((cur_avg / prev_avg - 1) * 100, 1) if (cur_avg and prev_avg) else None

    daily = [{"date": d, "up": v[0], "down": v[1], "flat": v[2],
              "comparable": v[0] + v[1] if a.denominator == "updn" else v[0] + v[1] + v[2],
              "up_ratio_pct": round(100 * v[0] / (v[0] + v[1]), 1) if (v[0] + v[1]) else None,
              "limit_up": limit_day.get(d, 0)}
             for d, v in sorted(breadth_day.items()) if iso_week(d) >= w_lo]

    doc = {
        "as_of": as_of, "weeks": [w_lo, w_hi],
        "caliber": {
            "breadth": {"numerator": "当日上涨家数", "denominator": a.denominator,
                        "sample": "status=OK 个股；当日与相邻交易日均需有效收盘",
                        "st": "excluded" if a.exclude_st else "included",
                        "week_value": "周内逐日占比的算术平均"},
            "limit_up": {"main": list(BAND_MAIN), "growth": list(BAND_GROWTH),
                         "bse": "不检测", "st": "excluded" if a.exclude_st else "included",
                         "week_value": "周内逐日家数的算术平均"},
        },
        "breadth_weekly": breadth, "breadth_4w_mean_pct": breadth_4w,
        "limit_up_weekly": limits,
        "limit_up_current_4w": cur_avg, "limit_up_previous_4w": prev_avg,
        "limit_up_change_pct": chg,
        "daily": daily,
    }

    if a.json:
        print(json.dumps(doc, ensure_ascii=False, indent=1))
        return 0

    print("as_of %s · 周 %d–%d · 分母=%s · ST=%s" % (
        as_of, w_lo, w_hi, a.denominator, "剔除" if a.exclude_st else "不剔除"))
    print("\n[breadth] 周内逐日占比的算术平均")
    for x in breadth:
        print("  第 %2d 周: %d 日 · %.2f%%" % (x["week"], x["days"], x["mean_pct"]))
    print("  4 周均值: %s%%" % breadth_4w)
    print("\n[涨停家数] 周内逐日家数的算术平均")
    for x in limits:
        print("  第 %2d 周: %d 日 · 日均 %.1f 家 · 合计 %d" % (
            x["week"], x["days"], x["mean_per_day"], x["total"]))
    print("  近 4 周 %s vs 前 4 周 %s → %s%%" % (cur_avg, prev_avg, chg))
    print("\n[逐日明细] 最近 10 个交易日")
    for x in daily[-10:]:
        print("  %s 涨 %4d / 跌 %4d / 平 %3d · 可比 %4d · 占比 %5s%% · 涨停 %3d" % (
            x["date"], x["up"], x["down"], x["flat"], x["comparable"],
            x["up_ratio_pct"], x["limit_up"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
