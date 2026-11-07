#!/usr/bin/env python3
"""cross_check_price_v0_1.py —— L0 真实 A 股行情交叉校验（v0.78）。

## 回答的问题
「概念篮子 CPT_* 是等权自建（当前成分回溯）」—— 用**真实个股日线**独立复算一遍，
看它究竟是不是真的等于成分等权，以及「未上市成员被回溯计入」会造成多大偏差。

## 做法（纯只读，不改任何既有产物 / 数据库）
 1. 从 scan_meta 取 `members:<CPT_*>`（当前成分名单）；
 2. 从 scan_daily 取这些个股的**真实收盘**（本库 price_type=raw，未复权）；
 3. 逐交易日等权：成员 = 当日与前一交易日都有 close 的股票，
    `ret_t = mean(close_t / close_prev - 1)`；
 4. 与库内 CPT_* 序列自身的日收益对照（Pearson / 中位绝对差 / 重合日数）；
 5. 变体 B：只保留「该交易日之前已上市满 365 天」的成员（按 scan_series.first_date），
    量化幸存者 / 上市日偏差；
 6. 输出报告到 research/research/reports/（调查材料目录）。

## 边界
 - **不改写** scan_daily / 任何 research/current 产物；
 - raw 未复权是既有口径，本报告如实标注，不偷偷换成复权价；
 - 结论只说明「自建序列能否被真实个股复现」，**不证明**成分名单在当时可知。
"""
import argparse
import json
import math
import os
import sqlite3
import statistics
import sys
from datetime import datetime, timedelta

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(REPO, "research", "database", "history_scan.db")
OUT = os.path.join(REPO, "research", "research", "reports", "price_cross_check_v0_1.json")
SAMPLE = ["CPT_hwhs", "CPT_scp1", "CPT_gqgn", "CPT_xny", "CPT_hwqc"]


def norm(d):
    return str(d).replace("-", "")


def pearson(a, b):
    if len(a) < 3:
        return None
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return round(num / (da * db), 6) if da and db else None


def one_basket(con, sid):
    row = con.execute("SELECT v FROM scan_meta WHERE k=?", ("members:" + sid,)).fetchone()
    if not row:
        return {"series_id": sid, "status": "NO_MEMBER_SNAPSHOT"}
    members = json.loads(row[0])
    first = dict(con.execute(
        "SELECT series_id, first_date FROM scan_series WHERE series_id IN (%s)"
        % ",".join("?" * len(members)), members).fetchall())
    q = ",".join("?" * len(members))
    stock_rows = con.execute(
        "SELECT series_id, trade_date, close FROM scan_daily "
        "WHERE series_id IN (%s) AND close>0 ORDER BY trade_date" % q, members).fetchall()
    by_date = {}
    for s, d, c in stock_rows:
        by_date.setdefault(norm(d), {})[s] = float(c)
    dates = sorted(by_date)

    # 库内自建篮子序列
    own = {norm(d): float(c) for d, c in con.execute(
        "SELECT trade_date, close FROM scan_daily WHERE series_id=? AND close>0", (sid,))}

    pair, pair_b, diffs, diffs_b = [], [], [], []
    for i in range(1, len(dates)):
        d0, d1 = dates[i - 1], dates[i]
        if d1 not in own or d0 not in own:
            continue
        prev, cur = by_date[d0], by_date[d1]
        common = [s for s in cur if s in prev]
        if not common:
            continue
        rets = [cur[s] / prev[s] - 1 for s in common]
        a = statistics.fmean(rets) * 100                    # 等权日收益（%）
        b = (own[d1] / own[d0] - 1) * 100                   # 库内序列日收益（%）
        pair.append((a, b))
        diffs.append(abs(a - b))

        cutoff = (datetime.strptime(d1, "%Y%m%d") - timedelta(days=365)).strftime("%Y%m%d")
        listed = [s for s in common if norm(first.get(s) or "99999999") <= cutoff]
        if listed:
            bb = statistics.fmean([cur[s] / prev[s] - 1 for s in listed]) * 100
            pair_b.append((bb, a))
            diffs_b.append(abs(bb - a))

    return {
        "series_id": sid, "status": "OK",
        "member_count": len(members),
        "trading_days_with_members": len(dates),
        "overlap_days": len(pair),
        "pearson_all_vs_own": pearson([x for x, _ in pair], [y for _, y in pair]),
        "median_abs_diff_pp": round(statistics.median(diffs), 4) if diffs else None,
        "max_abs_diff_pp": round(max(diffs), 4) if diffs else None,
        "listed_1y_filter": {
            "overlap_days": len(pair_b),
            "pearson_filtered_vs_all": pearson([x for x, _ in pair_b], [y for _, y in pair_b]),
            "median_abs_diff_pp": round(statistics.median(diffs_b), 4) if diffs_b else None,
            "note": "只保留该交易日之前已上市满 365 天的成员；与『全部当前成分』的差异即上市日偏差",
        },
    }


def build():
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        baskets = [one_basket(con, s) for s in SAMPLE]
        price_types = con.execute(
            "SELECT price_type, COUNT(*) FROM scan_series GROUP BY price_type").fetchall()
    finally:
        con.close()
    return {
        "artifact": "price_cross_check", "artifact_version": "0.1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "purpose": "用真实 A 股个股日线独立复算概念篮子，量化自建序列可复现性与上市日偏差",
        "source": {"db": os.path.relpath(DB, REPO),
                   "price_types": {k: n for k, n in price_types},
                   "price_type_note": "扫描层全部为 raw（未复权）；本报告不改写口径"},
        "baskets": baskets,
        "limits": [
            "CPT_* 是『当前成分等权自建』，不是官方概念指数；成员名单为当前快照，存在幸存者/成分变更偏差。",
            "个股日为 raw 未复权收盘；除权除息日会造成单日跳变，本报告只做序列一致性复核，不修正历史。",
            "行业板块 BK_* 是同花顺编制指数，库内无历史成分名单 → 无法用个股复现，未纳入本次抽样。",
            "本报告不改写任何既有产物或数据库，也不构成对历史收益结论的重新认定。",
        ],
    }


def check():
    if not os.path.exists(OUT):
        print("FAIL 报告不存在：%s" % OUT)
        return 1
    d = json.load(open(OUT, encoding="utf-8"))
    errs = []
    if len(d.get("baskets") or []) != len(SAMPLE):
        errs.append("抽样篮子数不符")
    for b in d.get("baskets") or []:
        if b["status"] == "OK":
            if not b["overlap_days"]:
                errs.append("%s 无重合交易日" % b["series_id"])
            p = b["pearson_all_vs_own"]
            if p is not None and p < 0.5:
                errs.append("%s 与真实个股复现相关性过低 %s" % (b["series_id"], p))
    if errs:
        for e in errs:
            print("  FAIL", e)
        return 1
    print("--check PASS · 抽样 %d 个篮子" % len(d["baskets"]))
    for b in d["baskets"]:
        print("  %-12s 重合 %4d 日 · 相关 %s · 中位差 %s pp · 上市日过滤差 %s pp"
              % (b["series_id"], b["overlap_days"], b["pearson_all_vs_own"],
                 b["median_abs_diff_pp"], (b.get("listed_1y_filter") or {}).get("median_abs_diff_pp")))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        return check()
    d = build()
    if not a.write:
        print(json.dumps(d, ensure_ascii=False, indent=1)[:2600])
        return 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    print("已生成 %s" % os.path.relpath(OUT, REPO))
    return check()


if __name__ == "__main__":
    sys.exit(main())
