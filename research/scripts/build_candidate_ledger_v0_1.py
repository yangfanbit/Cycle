#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_candidate_ledger_v0_1.py —— 候选快照 + 5/10/20 交易日表现账本（v0.50）。

## 解决什么问题

`pattern_discovery` 只回答「历史上哪些 板块×月份 结构成立」，`candidate_digest` 只回答
「本期该看哪些」。两者都**不记录候选形成之后实际发生了什么**。
本脚本把「本期候选」冻结成快照，并按**预先声明的锚点**回填 5 / 10 / 20 个交易日的
板块表现、基准表现与超额 —— 让「发现」变成「可追踪」。

## 口径（预先声明，不看结果再调）

| 项 | 规则 |
|---|---|
| 候选来源 | `pattern_discovery_v0_*.json` 的 `current_windows`（本期候选窗口）；**只复用，不重算** |
| 形成日 `formation_date` | 源产物的 `as_of`（= 行情最后交易日），即「这一版候选是在哪一天形成的」 |
| 窗口 | 该 `month` 的**首末交易日**（用 CSI300 交易日序列界定） |
| **表现锚点 `anchor`** | 窗口**首个交易日**收盘 |
| 5 / 10 / 20 日 | `close[anchor + h] / close[anchor] − 1`（h = 5/10/20 个交易日） |
| 基准 | 沪深300（`CSI300`）同区间收益 |
| 超额 | 板块收益 − 基准收益（个百分点） |
| 代表股票 | 直接用源产物 `representative_stocks`（概念篮子有、行业板块没有）；取**中位数** |
| 缺失 | 无序列 → `NO_SERIES`；代表股票为空 → `NO_REPS`；交易日不足 → `PENDING` + 预计结算日 |

## ★★ 两个必须分清的「结果类型」

- `FORWARD_PENDING`：**形成日早于窗口起点** → 这是真正的**前瞻**候选，尚未结算（PENDING 是正确状态）；
- `IN_WINDOW_PARTIAL`：**形成日已在窗口之内** → 已实现的那几天**不是样本外前瞻**，
  只是「窗口内已发生的部分」，必须在 UI 与报告里如实标注。

## 已知限制（写进产物，不在别处另说）

- 概念篮子是**当前成分**合成的历史序列 → 回填的是「当前成分在该窗口的表现」，
  **不是**当时成分的表现；行业板块无历史成分 → 不绑个股。
- 代表股票收益用**当前**名单 → 存在幸存者偏差，且不等于当时可买到的组合。
- 本账本只做**描述**，不做评分、不做排名、不预测。

## 用法

    python research/scripts/build_candidate_ledger_v0_1.py            # 打印规模（不写）
    python research/scripts/build_candidate_ledger_v0_1.py --write    # 写 latest + 冻结快照
    python research/scripts/build_candidate_ledger_v0_1.py --check    # 与磁盘逐字节比对
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
import os
import re
import sqlite3
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
SNAP_DIR = os.path.join(CURRENT, "candidate_ledger_snapshots")
DB = os.path.join(REPO, "research", "database", "history_scan.db")

OUT_NAME = "candidate_ledger_v0_1.json"
PD_RE = re.compile(r"pattern_discovery_v0_(\d+)\.json$")
DIGEST_RE = re.compile(r"candidate_digest_v0_(\d+)\.json$")
HORIZONS = (5, 10, 20)
BENCH = "CSI300"


def _latest(pattern):
    files = [f for f in os.listdir(CURRENT) if pattern.match(f)]
    if not files:
        raise SystemExit("FAIL: 缺产物 %s" % pattern.pattern)
    return os.path.join(CURRENT, sorted(files, key=lambda f: int(pattern.match(f).group(1)))[-1])


def _sha(path):
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()


def _read(path):
    return json.loads(io.open(path, encoding="utf-8").read())


def _norm(d):
    """行业板块的 scan_daily 用紧凑日期（20261023），其余用 2026-10-23 → 统一成后者。"""
    return d if "-" in d else "%s-%s-%s" % (d[:4], d[4:6], d[6:])


def load_series(con, sid):
    rows = con.execute(
        "SELECT trade_date, close FROM scan_daily WHERE series_id=? ORDER BY trade_date", (sid,)
    ).fetchall()
    return [( _norm(d), c) for d, c in rows if c]


def month_window(cal, year, month):
    """该月的首末交易日（用 CSI300 交易日序列界定）。"""
    days = [d for d in cal if d[:4] == str(year) and int(d[5:7]) == month]
    return (days[0], days[-1]) if days else (None, None)


def horizon_value(series, cal, cal_index, anchor, h):
    """anchor 之后第 h 个交易日的收益（%）。返回 (status, ret, settle_date)。"""
    i = cal_index.get(anchor)
    if i is None:
        return "NO_ANCHOR", None, None
    j = i + h
    if j >= len(cal):
        return "PENDING", None, None
    target = cal[j]
    c0 = series.get(anchor)
    c1 = series.get(target)
    if not c0 or not c1:
        return "NO_SERIES", None, None
    return "AVAILABLE", round((c1 / c0 - 1) * 100, 2), target


def build():
    pd_path = _latest(PD_RE)
    dg_path = _latest(DIGEST_RE)
    pd = _read(pd_path)
    dg = _read(dg_path)
    as_of = pd["as_of"]
    as_of_iso = "%s-%s-%s" % (as_of[:4], as_of[4:6], as_of[6:]) if "-" not in as_of else as_of
    group_of = {c["id"]: c.get("group") for c in dg.get("cards") or []}

    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        cal = [_norm(r[0]) for r in con.execute(
            "SELECT trade_date FROM scan_daily WHERE series_id=? ORDER BY trade_date", (BENCH,))]
        cal_index = {d: i for i, d in enumerate(cal)}
        bench = dict(load_series(con, BENCH))
        series_cache = {}

        def series_of(sid):
            if sid not in series_cache:
                series_cache[sid] = dict(load_series(con, sid))
            return series_cache[sid]

        year = int(as_of_iso[:4])
        entries = []
        for w in pd["current_windows"]:
            month = int(w["month"])
            wy = year if month >= int(as_of_iso[5:7]) else year + 1
            start, end = month_window(cal, wy, month)
            # 窗口尚未出现在日历里（下一年）→ 用「预计首日」占位，status 记 NOT_STARTED
            status = ("IN_WINDOW" if (start and start <= as_of_iso and as_of_iso <= (end or as_of_iso))
                      else "PRE_WINDOW")
            outcome_type = ("IN_WINDOW_PARTIAL" if (start and start <= as_of_iso) else "FORWARD_PENDING")
            bseries = series_of(w["board_series"])
            hz = {}
            for h in HORIZONS:
                if not start:
                    hz[str(h)] = {"status": "NOT_STARTED", "settle_date": None,
                                  "board_ret": None, "bench_ret": None, "excess_pp": None,
                                  "rep_median_ret": None, "rep_median_excess_pp": None, "n_reps": 0}
                    continue
                st, bret, settle = horizon_value(bseries, cal, cal_index, start, h)
                bst, bmk, _ = horizon_value(bench, cal, cal_index, start, h)
                reps = w.get("representative_stocks") or []
                r_rets, r_exc = [], []
                for r in reps:
                    rs = series_of(r["series_id"])
                    rst, rret, _ = horizon_value(rs, cal, cal_index, start, h)
                    if rst == "AVAILABLE" and rret is not None:
                        r_rets.append(rret)
                        if bmk is not None:
                            r_exc.append(rret - bmk)
                ok = st == "AVAILABLE" and bst == "AVAILABLE"
                hz[str(h)] = {
                    "status": "AVAILABLE" if ok else (st if st != "AVAILABLE" else bst),
                    "settle_date": settle,
                    "board_ret": bret if ok else None,
                    "bench_ret": bmk if ok else None,
                    "excess_pp": round(bret - bmk, 2) if ok else None,
                    "rep_median_ret": round(statistics.median(r_rets), 2) if r_rets else None,
                    "rep_median_excess_pp": round(statistics.median(r_exc), 2) if r_exc else None,
                    "n_reps": len(r_rets),
                }
            entries.append({
                "candidate_id": w["pattern_id"],
                "group": group_of.get(w["pattern_id"]),
                "direction": "%s · %d 月" % (w["board"], month),
                "board": w["board"], "board_series": w["board_series"], "kind": w["kind"],
                "month": month,
                # ★ 窗口是否「已走完」：末个交易日 == 日历最后一天 → 说明本月未结束（被日历截断）
                "window": {
                    "start": start, "end": end, "year": wy,
                    "complete": bool(end and end != cal[-1]),
                    "note": ("窗口已完整走完" if (end and end != cal[-1])
                             else ("窗口尚未开始（起点待交易日历确认）" if not start
                                   else "窗口进行中：end 为当前已知的最后一个交易日，非月末")),
                },
                "formation_date": as_of_iso,
                "status": status,
                "outcome_type": outcome_type,
                "anchor": start,
                "selection_basis": {
                    "tier": w.get("tier"), "n_years": w.get("n_years"),
                    "median_excess_pct": w.get("median_excess_pct"), "hit_rate": w.get("hit_rate"),
                    "pit_eligible_years": w.get("pit_eligible_years"),
                    "oos_status": w.get("oos_status"), "oos_tests": w.get("oos_tests"),
                    "evidence_grade": w.get("evidence_grade"),
                },
                "representative_stocks": [
                    {"series_id": r["series_id"], "name": r.get("name"),
                     "name_status": r.get("name_status"),
                     "historical_median_excess_pct": r.get("median_excess_pct"),
                     "years": r.get("years"), "source": r.get("source")}
                    for r in (w.get("representative_stocks") or [])
                ],
                "rep_stock_gap": w.get("rep_stock_gap") or (
                    None if w.get("representative_stocks") else "行业板块无历史成分 → 不绑个股"),
                "outcome": hz,
            })
    finally:
        con.close()

    # 计数（供报告与 UI 核对；不参与任何判定）
    avail = collections.Counter()
    for e in entries:
        for h in HORIZONS:
            avail[(h, e["outcome"][str(h)]["status"])] += 1

    return {
        "artifact": "candidate_ledger",
        "artifact_version": "0.1",
        "generated_by": "research/scripts/build_candidate_ledger_v0_1.py",
        "as_of": as_of_iso,
        "sources": {
            "pattern_discovery": {"path": os.path.relpath(pd_path, REPO),
                                  "artifact_version": pd.get("artifact_version"),
                                  "sha256": _sha(pd_path)},
            "candidate_digest": {"path": os.path.relpath(dg_path, REPO),
                                 "artifact_version": dg.get("artifact_version"),
                                 "sha256": _sha(dg_path)},
            "market": {"db": "research/database/history_scan.db",
                       "benchmark": BENCH, "calendar_last": cal[-1]},
        },
        "caliber": {
            "anchor": "窗口首个交易日收盘",
            "horizons": list(HORIZONS),
            "return": "close[anchor+h] / close[anchor] − 1",
            "excess": "板块收益 − 沪深300 同区间收益（pp）",
            "representative_stocks": "直接用 pattern_discovery 的 representative_stocks（当前口径），取中位数",
            "outcome_type": {
                "FORWARD_PENDING": "形成日早于窗口起点 → 真正的前瞻候选，尚未结算",
                "IN_WINDOW_PARTIAL": "形成日已在窗口内 → 已实现部分不是样本外前瞻",
            },
        },
        "summary": {
            "candidates": len(entries),
            "by_status": dict(collections.Counter(e["status"] for e in entries)),
            "by_outcome_type": dict(collections.Counter(e["outcome_type"] for e in entries)),
            "by_kind": dict(collections.Counter(e["kind"] for e in entries)),
            "windows_complete": sum(1 for e in entries if e["window"]["complete"]),
            "windows_open": sum(1 for e in entries if not e["window"]["complete"]),
            "horizon_status": {"%dd" % h: {k: v for (hh, k), v in avail.items() if hh == h}
                               for h in HORIZONS},
            "with_representative_stocks": sum(1 for e in entries if e["representative_stocks"]),
        },
        "limitations": [
            "概念篮子用**当前成分**合成历史序列 → 回填的是「当前成分在该窗口的表现」，不是当时成分的表现。",
            "行业板块无历史成分 → 不绑个股（representative_stocks 为空，rep_stock_gap 已注明）。",
            "代表股票收益用**当前**名单 → 存在幸存者偏差，不等于当时可买到的组合。",
            "IN_WINDOW_PARTIAL 的已实现天数**不是**样本外前瞻，只是窗口内已发生的部分。",
            "本账本只做描述：不含评分、排名、预测或买卖信号。",
        ],
        "candidates": entries,
    }


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.check and not os.path.exists(DB):
        # ★ 与季节性校验器同一约定：源库不在（CI 不携带 1.3GB 库）→ 显式 SKIP，不谎报通过
        print("SKIP: history_scan.db 不存在 → 无法重算候选账本（CI 不携带该库）；本地请先 --check")
        return 0
    doc = build()
    body = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    out = os.path.join(CURRENT, OUT_NAME)
    snap = os.path.join(SNAP_DIR, "CL-%s-v0_1.json" % doc["as_of"])

    if a.check:
        if not os.path.exists(out):
            print("FAIL: 产物不存在 %s" % out); return 1
        cur = io.open(out, encoding="utf-8").read()
        if cur != body:
            print("FAIL: 账本与当前数据不一致（需 --write 重建）"); return 1
        if not os.path.exists(snap) or io.open(snap, encoding="utf-8").read() != body:
            print("FAIL: 冻结快照与 latest 不一致: %s" % os.path.relpath(snap, REPO)); return 1
        print("PASS: 候选账本一致（%d 候选 · %s · 快照 %s）"
              % (doc["summary"]["candidates"], doc["as_of"], os.path.basename(snap)))
        return 0

    s = doc["summary"]
    print("候选 %d · 状态 %s · 结果类型 %s" % (s["candidates"], s["by_status"], s["by_outcome_type"]))
    for h in HORIZONS:
        print("  %2d 日: %s" % (h, s["horizon_status"]["%dd" % h]))
    print("  有代表股票的候选: %d" % s["with_representative_stocks"])
    if a.write:
        os.makedirs(SNAP_DIR, exist_ok=True)
        io.open(out, "w", encoding="utf-8", newline="\n").write(body)
        io.open(snap, "w", encoding="utf-8", newline="\n").write(body)
        print("已写 %s" % os.path.relpath(out, REPO))
        print("已写 %s" % os.path.relpath(snap, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
