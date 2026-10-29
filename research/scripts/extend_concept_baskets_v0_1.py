#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""extend_concept_baskets_v0_1.py —— 概念篮子（`CPT_*`）**增量延长**。

## 为什么单独一个脚本

`backfill_concepts_v0_1.py --concepts` 会用**新浪当前概念成分**把整条篮子**重建一遍** ——
那等于「用今天的成分回溯改写历史」，与项目纪律冲突（见 `AGENTS.md` §3）。

本脚本走另一条路：`scan_meta` 里已经存了每只篮子**建库当时**的成分快照
（`members:CPT_xxx`），因此可以**只追加新交易日**，历史逐行不动。

## 口径（与原建库逻辑一致，不另造）

- 篮子 = 成员**等权**：逐日取「同标的 昨收→今收」收益的**算术均值**，累乘到水平值
- 水平值起点沿用库内最后一行（**不重设基点**），因此新行与旧行天然连续
- 每个新交易日要求**当日可计算收益的成员数 ≥ 建库时记录的下限**（`required_min_covered`）；
  达不到就**跳过该日并记录**，**不补造、不插值**
- 行格式与既有行一致：`open=high=low=close=水平值`、`volume=0`

## 用法

    python research/scripts/extend_concept_baskets_v0_1.py            # 只报告（默认）
    python research/scripts/extend_concept_baskets_v0_1.py --write     # 追加写入

## 不做

- 不重新抓概念名单、不改成分、不改任何既有行
- 不写 `market_data.db`（概念篮子只存在于 `history_scan.db`）
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(REPO, "research", "database", "history_scan.db")
BENCH = "CSI300"


def _norm(d: str) -> str:
    return d if "-" in d else "%s-%s-%s" % (d[:4], d[4:6], d[6:])


def calendar(con) -> list:
    """交易日历：**用 CSI300 自己的日期序列**（比独立日历表更可靠）。"""
    return sorted({_norm(r[0]) for r in con.execute(
        "SELECT trade_date FROM scan_daily WHERE series_id=?", (BENCH,))})


def member_closes(con, members, dates) -> dict:
    """{date: {sid: close}}，只取给定日期集合（避免把全历史拉进内存）。"""
    out = {}
    q = ",".join("?" * len(members))
    for d, sid, close in con.execute(
            "SELECT trade_date, series_id, close FROM scan_daily "
            "WHERE series_id IN (%s) AND close>0" % q, list(members)):
        dn = _norm(d)
        if dn in dates:
            out.setdefault(dn, {})[sid] = close
    return out


def plan(con):
    """算出每只篮子的待追加行（纯函数式，不写库）。"""
    cal = calendar(con)
    if not cal:
        raise SystemExit("FAIL: 交易日历为空（缺 %s）" % BENCH)
    idx = {d: i for i, d in enumerate(cal)}

    rows = con.execute(
        "SELECT series_id, name FROM scan_series WHERE kind='concept_basket' AND rows>0 "
        "AND status='OK' ORDER BY series_id").fetchall()
    plan_out, skipped = [], []
    for sid, name in rows:
        last = con.execute("SELECT trade_date, close FROM scan_daily WHERE series_id=? "
                           "ORDER BY trade_date DESC LIMIT 1", (sid,)).fetchone()
        if not last:
            continue
        last_d = _norm(last[0])
        last_lv = last[1]
        if last_d >= cal[-1]:
            continue                                  # 已是最新
        new_dates = [d for d in cal if d > last_d]
        if not new_dates:
            continue

        raw_members = con.execute("SELECT v FROM scan_meta WHERE k=?", ("members:" + sid,)).fetchone()
        if not raw_members:
            skipped.append((sid, name, "无成分快照（members:%s）→ 不延长，避免用当前成分回溯" % sid))
            continue
        members = json.loads(raw_members[0])

        cov = con.execute("SELECT v FROM scan_meta WHERE k=?", ("coverage:" + sid,)).fetchone()
        min_need = json.loads(cov[0]).get("required_min_covered") if cov else None
        min_need = int(min_need) if min_need else max(3, int(0.2 * len(members)))

        # 需要「上一交易日」的收盘才能算收益 → 连 last_d 一起取
        need_dates = set(new_dates) | {last_d}
        closes = member_closes(con, members, need_dates)

        level = last_lv
        new_rows, per_day, holes = [], [], []
        for d in new_dates:
            i = idx[d]
            prev_d = cal[i - 1]
            cur = closes.get(d, {})
            prev = closes.get(prev_d, {})
            rets = [cur[s] / prev[s] - 1.0 for s in cur if s in prev and prev[s] > 0]
            if len(rets) < min_need:
                holes.append((d, len(rets)))
                per_day.append((d, len(rets), "覆盖不足（< %d）" % min_need))
                continue
            level *= 1.0 + statistics.fmean(rets)
            new_rows.append([d, level, level, level, level, 0.0])
            per_day.append((d, len(rets), None))
        # ★★ 全有或全无：只要有一天覆盖不足，**整只篮子本轮不写**。
        #   否则会写出「10-26、10-28、10-29 有值但 10-27 缺失」的内部空洞，
        #   而下一轮又从最后一行往后延 → 空洞永久留下。
        if holes:
            skipped.append((sid, name, "%d 个新交易日覆盖不足（如 %s 仅 %d 只）→ 整只跳过，不写半截"
                            % (len(holes), holes[0][0], holes[0][1])))
            continue
        plan_out.append({"sid": sid, "name": name, "last": last_d, "last_lv": round(last_lv, 2),
                         "rows": new_rows, "per_day": per_day, "min_need": min_need,
                         "members": len(members)})
    return plan_out, skipped


def main(argv):
    ap = argparse.ArgumentParser(description="概念篮子增量延长（只追加，不改历史）")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)

    if not os.path.exists(DB):
        print("FAIL: 数据库不存在 %s" % DB)
        return 1
    con = sqlite3.connect(DB)
    try:
        plan_out, skipped = plan(con)
        print("待延长篮子: %d · 跳过: %d" % (len(plan_out), len(skipped)))
        total = 0
        for p in plan_out:
            total += len(p["rows"])
            print("  %-14s %-10s 自 %s（水平 %.2f）→ +%d 行"
                  % (p["sid"], p["name"], p["last"], p["last_lv"], len(p["rows"])))
            for d, n, why in p["per_day"]:
                if why:
                    print("      %s 可算成员 %d < %d：%s" % (d, n, p["min_need"], why))
        for sid, name, why in skipped:
            print("  SKIP %-14s %-10s %s" % (sid, name, why))
        print("合计新增行: %d" % total)
        if not a.write:
            print("\n[dry-run] 加 --write 才会写入")
            return 0

        n_series = 0
        for p in plan_out:
            if not p["rows"]:
                continue
            con.executemany("INSERT INTO scan_daily VALUES (?,?,?,?,?,?,?) "
                            "ON CONFLICT(series_id,trade_date) DO NOTHING",
                            [(p["sid"], r[0], r[1], r[2], r[3], r[4], r[5]) for r in p["rows"]])
            # ★ 按库内实际内容回填 rows / last_date（不相信传入值）
            n, f, l = con.execute("SELECT COUNT(*), MIN(trade_date), MAX(trade_date) "
                                  "FROM scan_daily WHERE series_id=?", (p["sid"],)).fetchone()
            con.execute("UPDATE scan_series SET rows=?, first_date=?, last_date=? WHERE series_id=?",
                        (n, f, l, p["sid"]))
            n_series += 1
        con.commit()
        print("\n已写入 %d 只篮子 · %d 行（历史行未改动）" % (n_series, total))
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
