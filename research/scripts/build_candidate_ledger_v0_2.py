#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_candidate_ledger_v0_2.py —— 候选**形成日志** + 滚动**结算账本**（v0.51）。

## v0_1 的三个致命缺陷（本版逐个修）

1. **形成记录会被覆盖**：v0_1 每次 `--write` 都用「当前」`pattern_discovery` 重算整份账本，
   上个月的候选直接消失 → 无法跨月滚动追踪。
2. **没有稳定实例标识**：只有 `candidate_id = SEAS-<series>-M<month>`，**不含年份** →
   同一板块同一月份在**不同年份**是同一个 id，跨月/跨年无法区分。
3. **`--check` 要求「最新账本 == 最初快照」**：结算结果必然随行情推进而变化 → 这个检查
   在下一个交易日起就永久 FAIL，只能靠不断覆盖快照来「修复」= 假检查。

## 本版结构

- **`candidate_formation_log_v0_1.json`**（追加式，**只增不改**）：每次形成候选登记一个 `batch`。
  `batch.instances[]` 是**形成记录**——只写「形成当时知道的事」，之后**永不修改**。
- **`candidate_ledger_v0_2.json`**（派生视图）：形成记录**逐字投影** + 在 `market_as_of`
  重算的结算字段。可以随行情变化，但只变结算部分。
- 冻结快照两种，**都不可被 `--write` 静默覆盖**：
  - `candidate_ledger_snapshots/CF-<batch_id>.json` —— 单批形成快照（写一次）
  - `candidate_ledger_snapshots/CL-<market_as_of>-v0_2.json` —— 该结算日的账本（写一次）

## ★★ 稳定实例 ID

    instance_id = "<board_series>__<window_year>-<MM>"

窗口 = 「该板块的下一个该月份」。同一板块同一目标月份，无论在哪一天被重复选中，
`instance_id` 相同 → **复用最初的形成记录**，只在新批次里记一条 `reappearances`。

## ★★ 两个必须分清的「结果类型」（口径不变）

- `FORWARD_PENDING`：形成日**早于**窗口起点 → 真正的前瞻候选；
- `IN_WINDOW_PARTIAL`：形成日**已在**窗口内 → 已实现部分**不是**样本外前瞻。

## 用法

    # 一次性迁移：把 v0_1 的 204 条候选登记为首批形成记录（日志已存在则拒绝）
    python research/scripts/build_candidate_ledger_v0_2.py --bootstrap

    # 月度刷新：结算旧候选 + 形成新候选 + 写 latest 与快照
    python research/scripts/build_candidate_ledger_v0_2.py --write

    # 校验（默认两者都查）
    python research/scripts/build_candidate_ledger_v0_2.py --check
    python research/scripts/build_candidate_ledger_v0_2.py --check-formations
    python research/scripts/build_candidate_ledger_v0_2.py --check-settlement
    python research/scripts/build_candidate_ledger_v0_2.py --check --market-as-of 2026-10-23
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

LOG_NAME = "candidate_formation_log_v0_1.json"
OUT_NAME = "candidate_ledger_v0_2.json"
V01_NAME = "candidate_ledger_v0_1.json"
PD_RE = re.compile(r"pattern_discovery_v0_(\d+)\.json$")
DIGEST_RE = re.compile(r"candidate_digest_v0_(\d+)\.json$")
HORIZONS = (5, 10, 20)
BENCH = "CSI300"

# ★ 形成字段（来自形成日志，逐字投影，永不随行情变化）
FORMATION_FIELDS = (
    "instance_id", "candidate_id", "group", "direction", "board", "board_series",
    "kind", "month", "window_year", "window_declared", "formed_at",
    "selection_basis", "representative_stocks", "rep_stock_gap",
)
# ★ 结算字段（每次 build 在 market_as_of 重算）
SETTLEMENT_FIELDS = ("anchor", "window", "status", "outcome_type", "outcome")


# ─────────────────────────── 基础工具 ───────────────────────────

def _latest(pattern):
    files = [f for f in os.listdir(CURRENT) if pattern.match(f)]
    if not files:
        raise SystemExit("FAIL: 缺产物 %s" % pattern.pattern)
    return os.path.join(CURRENT, sorted(files, key=lambda f: int(pattern.match(f).group(1)))[-1])


def _sha(path):
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()


def _read(path):
    return json.loads(io.open(path, encoding="utf-8").read())


def _dump(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def _norm(d):
    """行业板块的 scan_daily 用紧凑日期（20261023），其余用 2026-10-23 → 统一成后者。"""
    return d if "-" in d else "%s-%s-%s" % (d[:4], d[4:6], d[6:])


def instance_id(board_series, window_year, month):
    """★★ 稳定实例标识：板块 + 目标年月。同一板块同一目标月份永远得到同一个 id。"""
    return "%s__%d-%02d" % (board_series, int(window_year), int(month))


def load_series(con, sid):
    rows = con.execute(
        "SELECT trade_date, close FROM scan_daily WHERE series_id=? ORDER BY trade_date", (sid,)
    ).fetchall()
    return [(_norm(d), c) for d, c in rows if c]


def month_window(cal, year, month):
    """该月的首末交易日（用**已截断到 market_as_of** 的日历界定）。"""
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


# ─────────────────────────── 形成日志 ───────────────────────────

def load_log():
    path = os.path.join(CURRENT, LOG_NAME)
    if not os.path.exists(path):
        return None
    return _read(path)


def log_index(log):
    """instance_id → 形成记录（取**最早**那次）。"""
    idx = {}
    for b in log["batches"]:
        for rec in b["instances"]:
            idx.setdefault(rec["instance_id"], rec)
    return idx


def next_batch_id(log, formed_at):
    n = sum(1 for b in log["batches"] if b["formed_at"] == formed_at) if log else 0
    return "CF-%s-%02d" % (formed_at, n + 1)


def make_formation_record(w, window_year, as_of_iso, group):
    """从 `pattern_discovery.current_windows` 的一条窗口生成**形成记录**。

    ★ 只写「形成当时知道的事」：`window_declared.start` 若当月尚未开始则为 null。
    ★★ **不写 `end`** —— 它当时只是「已知的最后一个交易日」，会随行情推进变化，
      不是形成事实（v0_1 把它写进候选记录，是「滚动值冒充快照」的典型）。
    """
    start, _end = (None, None)  # 由调用方用日历补（见 form_batch）
    return {
        "instance_id": instance_id(w["board_series"], window_year, w["month"]),
        "candidate_id": w["pattern_id"],
        "group": group,
        "direction": "%s · %d 月" % (w["board"], int(w["month"])),
        "board": w["board"], "board_series": w["board_series"], "kind": w["kind"],
        "month": int(w["month"]),
        "window_year": int(window_year),
        "window_declared": {"start": start, "start_status": "UNKNOWN_AT_FORMATION"},
        "formed_at": as_of_iso,
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
    }


def form_batch(log, pd, dg, as_of_iso, cal):
    """用当前 `pattern_discovery.current_windows` 形成新批次；已存在的实例只记 `reappearances`。

    返回 (batch_or_None, info)。**不修改** `log`。
    """
    group_of = {c["id"]: c.get("group") for c in dg.get("cards") or []}
    known = log_index(log) if log else {}
    year, cur_month = int(as_of_iso[:4]), int(as_of_iso[5:7])
    new, reappeared = [], []
    for w in pd["current_windows"]:
        month = int(w["month"])
        wy = year if month >= cur_month else year + 1
        iid = instance_id(w["board_series"], wy, month)
        if iid in known:
            reappeared.append({
                "instance_id": iid,
                "first_batch": next(b["batch_id"] for b in log["batches"]
                                    if any(r["instance_id"] == iid for r in b["instances"])),
                "first_formed_at": known[iid]["formed_at"],
                "note": "同一板块同一目标月份已登记 → 复用最初的形成记录，不重复登记",
            })
            continue
        rec = make_formation_record(w, wy, as_of_iso, group_of.get(w["pattern_id"]))
        start, _ = month_window(cal, wy, month)
        if start:
            rec["window_declared"] = {"start": start, "start_status": "KNOWN"}
        new.append(rec)

    if not new:
        return None, {"new": 0, "reappeared": len(reappeared), "reappearances": reappeared}

    batch = {
        "batch_id": next_batch_id(log, as_of_iso),
        "formed_at": as_of_iso,
        "source": {"pattern_discovery": {"file": os.path.basename(pd["_path"]),
                                         "as_of": pd["as_of"],
                                         "sha256": _sha(pd["_path"])},
                   "candidate_digest": {"file": os.path.basename(dg["_path"]),
                                        "sha256": _sha(dg["_path"])},
                   "migrated_from": None},
        "counts": {"new_instances": len(new), "reappeared": len(reappeared),
                   "by_kind": dict(collections.Counter(r["kind"] for r in new))},
        "reappearances": reappeared,
        "instances": sorted(new, key=lambda r: r["instance_id"]),
    }
    return batch, {"new": len(new), "reappeared": len(reappeared), "reappearances": reappeared}


def bootstrap_batch():
    """把 v0_1 的候选登记为首批形成记录（**一次性迁移**）。

    v0_1 的 `window.end` 是「当时已知的最后一个交易日」= 滚动值 → 不进入形成记录，
    只在 `source.note` 里说明它被丢弃的理由。
    """
    path = os.path.join(CURRENT, V01_NAME)
    if not os.path.exists(path):
        raise SystemExit("FAIL: 缺 %s，无法迁移" % V01_NAME)
    d = _read(path)
    instances = []
    for c in d["candidates"]:
        wy = int(c["window"]["year"])
        start = c["window"]["start"]
        instances.append({
            "instance_id": instance_id(c["board_series"], wy, c["month"]),
            "candidate_id": c["candidate_id"],
            "group": c.get("group"),
            "direction": c["direction"],
            "board": c["board"], "board_series": c["board_series"], "kind": c["kind"],
            "month": int(c["month"]),
            "window_year": wy,
            "window_declared": {"start": start,
                                "start_status": "KNOWN" if start else "UNKNOWN_AT_FORMATION"},
            "formed_at": c["formation_date"],
            "selection_basis": c["selection_basis"],
            "representative_stocks": c["representative_stocks"],
            "rep_stock_gap": c.get("rep_stock_gap"),
        })
    instances.sort(key=lambda r: r["instance_id"])
    return {
        "batch_id": "CF-%s-01" % d["as_of"],
        "formed_at": d["as_of"],
        "source": {
            "pattern_discovery": (d.get("sources") or {}).get("pattern_discovery"),
            "candidate_digest": (d.get("sources") or {}).get("candidate_digest"),
            "migrated_from": V01_NAME,
            "migrated_sha256": _sha(path),
            "note": ("★ 迁移自 v0_1：这 204 条就是首批形成记录。v0_1 的 `window.end` 是"
                     "「当时已知的最后一个交易日」（滚动值），不进入形成记录。"),
        },
        "counts": {"new_instances": len(instances), "reappeared": 0,
                   "by_kind": dict(collections.Counter(r["kind"] for r in instances))},
        "reappearances": [],
        "instances": instances,
    }


# ─────────────────────────── 结算账本 ───────────────────────────

def build_ledger(log, market_as_of, pd=None, dg=None, formation_run=None):
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        allcal = [_norm(r[0]) for r in con.execute(
            "SELECT trade_date FROM scan_daily WHERE series_id=? ORDER BY trade_date", (BENCH,))]
        # ★★ 结算必须**钉在 market_as_of**：日历截断后重算 → 同一 market_as_of 永远同一结果
        cal = [d for d in allcal if d <= market_as_of]
        if not cal:
            raise SystemExit("FAIL: 日历在 %s 之前没有交易日" % market_as_of)
        cal_index = {d: i for i, d in enumerate(cal)}
        bench = dict(load_series(con, BENCH))
        cache = {}

        def series_of(sid):
            if sid not in cache:
                cache[sid] = dict(load_series(con, sid))
            return cache[sid]

        entries = []
        for b in log["batches"]:
            for f in b["instances"]:
                wy, month = f["window_year"], f["month"]
                start, end = month_window(cal, wy, month)
                if start is None:
                    status = "PRE_WINDOW"
                elif market_as_of > end:
                    status = "POST_WINDOW"
                elif start <= market_as_of <= end:
                    status = "IN_WINDOW"
                else:
                    status = "PRE_WINDOW"
                outcome_type = ("FORWARD_PENDING"
                                if (start is None or f["formed_at"] < start)
                                else "IN_WINDOW_PARTIAL")
                bseries = series_of(f["board_series"])
                hz, settled, pending = {}, [], []
                for h in HORIZONS:
                    if start is None:
                        hz[str(h)] = {"status": "NOT_STARTED", "settle_date": None,
                                      "board_ret": None, "bench_ret": None, "excess_pp": None,
                                      "rep_median_ret": None, "rep_median_excess_pp": None,
                                      "n_reps": 0}
                        pending.append(str(h))
                        continue
                    st, bret, settle = horizon_value(bseries, cal, cal_index, start, h)
                    bst, bmk, _ = horizon_value(bench, cal, cal_index, start, h)
                    reps = f.get("representative_stocks") or []
                    r_rets, r_exc = [], []
                    for r in reps:
                        rst, rret, _ = horizon_value(series_of(r["series_id"]), cal,
                                                     cal_index, start, h)
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
                    (settled if ok else pending).append(str(h))

                e = {k: f[k] for k in FORMATION_FIELDS}
                e.update({
                    "batch_id": b["batch_id"],
                    "window": {
                        "start": start, "end": end, "year": wy,
                        "complete": bool(end and end != cal[-1]),
                        "note": ("窗口已完整走完" if (end and end != cal[-1])
                                 else ("窗口尚未开始（起点待交易日历确认）" if not start
                                       else "窗口进行中：end 为当前已知的最后一个交易日，非月末")),
                    },
                    "anchor": start,
                    "status": status,
                    "outcome_type": outcome_type,
                    "settled_horizons": settled,
                    "pending_horizons": pending,
                    "outcome": hz,
                })
                entries.append(e)
    finally:
        con.close()

    entries.sort(key=lambda e: (e["formed_at"], e["instance_id"]))
    avail = collections.Counter()
    for e in entries:
        for h in HORIZONS:
            avail[(h, e["outcome"][str(h)]["status"])] += 1

    return {
        "artifact": "candidate_ledger",
        "artifact_version": "0.2",
        "generated_by": "research/scripts/build_candidate_ledger_v0_2.py",
        "market_as_of": market_as_of,
        "as_of": market_as_of,
        # ★ 本次形成运行的结果（出处记录）：新增 0 时不会追加批次，重现事件只能记在这里
        "formation_run": formation_run,
        "formation_log": {
            "file": LOG_NAME,
            "sha256": _sha(os.path.join(CURRENT, LOG_NAME)),
            "batches": len(log["batches"]),
            "instances": sum(len(b["instances"]) for b in log["batches"]),
            "earliest_formed_at": min(b["formed_at"] for b in log["batches"]),
        },
        "sources": {
            "pattern_discovery": ({"file": os.path.basename(pd["_path"]),
                                   "artifact_version": pd.get("artifact_version"),
                                   "sha256": _sha(pd["_path"])} if pd else None),
            "candidate_digest": ({"file": os.path.basename(dg["_path"]),
                                  "artifact_version": dg.get("artifact_version"),
                                  "sha256": _sha(dg["_path"])} if dg else None),
            "market": {"db": "research/database/history_scan.db",
                       "benchmark": BENCH, "calendar_last": cal[-1],
                       "calendar_last_all": allcal[-1]},
        },
        "caliber": {
            "anchor": "窗口首个交易日收盘",
            "horizons": list(HORIZONS),
            "return": "close[anchor+h] / close[anchor] − 1",
            "excess": "板块收益 − 沪深300 同区间收益（pp）",
            "representative_stocks": "直接用形成记录里的 representative_stocks（当前口径），取中位数",
            "outcome_type": {
                "FORWARD_PENDING": "形成日早于窗口起点 → 真正的前瞻候选，尚未结算",
                "IN_WINDOW_PARTIAL": "形成日已在窗口内 → 已实现部分不是样本外前瞻",
            },
            "settlement_fields": list(SETTLEMENT_FIELDS),
            "formation_fields": list(FORMATION_FIELDS),
            "settlement_pin": ("结算固定在 market_as_of 重算：日历截断到该日，"
                               "因此同一 market_as_of 永远得到同一结果"),
        },
        "summary": {
            "candidates": len(entries),
            "batches": [{"batch_id": b["batch_id"], "formed_at": b["formed_at"],
                         "new_instances": b["counts"]["new_instances"],
                         "reappeared": b["counts"]["reappeared"]} for b in log["batches"]],
            "by_batch": dict(collections.Counter(e["batch_id"] for e in entries)),
            "by_status": dict(collections.Counter(e["status"] for e in entries)),
            "by_outcome_type": dict(collections.Counter(e["outcome_type"] for e in entries)),
            "by_kind": dict(collections.Counter(e["kind"] for e in entries)),
            "windows_complete": sum(1 for e in entries if e["window"]["complete"]),
            "windows_open": sum(1 for e in entries if not e["window"]["complete"]),
            "horizon_status": {"%dd" % h: {k: v for (hh, k), v in avail.items() if hh == h}
                               for h in HORIZONS},
            "settled": {"%dd" % h: sum(1 for e in entries if str(h) in e["settled_horizons"])
                        for h in HORIZONS},
            "pending": {"%dd" % h: sum(1 for e in entries if str(h) in e["pending_horizons"])
                        for h in HORIZONS},
            "with_representative_stocks": sum(1 for e in entries if e["representative_stocks"]),
        },
        "limitations": [
            "概念篮子用**当前成分**合成历史序列 → 回填的是「当前成分在该窗口的表现」，不是当时成分的表现。",
            "行业板块无历史成分 → 不绑个股（representative_stocks 为空，rep_stock_gap 已注明）。",
            "代表股票收益用**当前**名单 → 存在幸存者偏差，不等于当时可买到的组合。",
            "IN_WINDOW_PARTIAL 的已实现天数**不是**样本外前瞻，只是窗口内已发生的部分。",
            "形成记录来自形成日志，**不随行情改写**；本文件的结算字段在 market_as_of 重算。",
            "本账本只做描述：不含评分、排名、预测或买卖信号。",
        ],
        "candidates": entries,
    }


# ─────────────────────────── 校验 ───────────────────────────

def check_formations(log):
    """F1–F6：形成日志的**稳定性**（与行情无关）。返回 (fails, warns, notes)。"""
    fails, warns, notes = [], [], []
    if not log:
        return ["F0: 形成日志不存在（%s）" % LOG_NAME], warns, notes
    batches = log.get("batches") or []
    if not batches:
        return ["F1: 形成日志没有任何批次"], warns, notes

    seen_batch, seen_inst = set(), {}
    for b in batches:
        bid = b.get("batch_id")
        if not bid:
            fails.append("F1: 存在无 batch_id 的批次")
            continue
        if bid in seen_batch:
            fails.append("F1: batch_id 重复 %s" % bid)
        seen_batch.add(bid)
        for rec in b["instances"]:
            iid = rec.get("instance_id")
            want = instance_id(rec["board_series"], rec["window_year"], rec["month"])
            if iid != want:
                fails.append("F2: %s 的 instance_id 与 (board_series, window_year, month) 不符"
                             "（应为 %s）" % (iid, want))
            if iid in seen_inst:
                fails.append("F3: %s 在 %s 与 %s 两次被登记为**新实例**"
                             "（重复选中应记 reappearances，不应新建）"
                             % (iid, seen_inst[iid], bid))
            else:
                seen_inst[iid] = bid
        # 批次内实例排序 + 计数自洽
        if [r["instance_id"] for r in b["instances"]] != sorted(r["instance_id"] for r in b["instances"]):
            fails.append("F4: %s 的 instances 未按 instance_id 排序（破坏逐字节可比）" % bid)
        if b["counts"]["new_instances"] != len(b["instances"]):
            fails.append("F4: %s 的 counts.new_instances=%d ≠ 实际 %d"
                         % (bid, b["counts"]["new_instances"], len(b["instances"])))
        # reappearances 必须指向已存在的实例
        for rp in b.get("reappearances") or []:
            if rp["instance_id"] not in seen_inst:
                fails.append("F5: %s 的 reappearance %s 在更早批次中不存在"
                             % (bid, rp["instance_id"]))
            elif rp["first_batch"] != seen_inst[rp["instance_id"]]:
                fails.append("F5: %s 的 reappearance %s 声称首批 %s，实际 %s"
                             % (bid, rp["instance_id"], rp["first_batch"],
                                seen_inst[rp["instance_id"]]))
        # 冻结快照必须存在且逐字节一致
        snap = os.path.join(SNAP_DIR, "%s.json" % bid)
        if not os.path.exists(snap):
            fails.append("F6: 缺冻结形成快照 %s" % os.path.relpath(snap, REPO))
        elif io.open(snap, encoding="utf-8").read() != _dump(b):
            fails.append("F6: 冻结形成快照与日志中的批次不一致 %s（被改过或被覆盖）"
                         % os.path.relpath(snap, REPO))
    notes.append("批次 %d · 实例 %d" % (len(batches), len(seen_inst)))
    return fails, warns, notes


def check_settlement(log, ledger, market_as_of):
    """S1–S5：结算结果的**一致性**（钉在 ledger.market_as_of 重算）。"""
    fails, warns, notes = [], [], []
    recalc = build_ledger(log, market_as_of)
    a = {c["instance_id"]: c for c in ledger["candidates"]}
    b = {c["instance_id"]: c for c in recalc["candidates"]}
    if set(a) != set(b):
        fails.append("S1: 账本候选集合与形成日志不一致（账本 %d / 日志 %d；差集 %s）"
                     % (len(a), len(b), sorted(set(a) ^ set(b))[:5]))
    for iid in sorted(set(a) & set(b)):
        for k in SETTLEMENT_FIELDS:
            if a[iid].get(k) != b[iid].get(k):
                fails.append("S1: %s 的结算字段 %s 与重算不一致" % (iid, k))
                break
        # S4：结果类型必须与形成日/窗口起点的关系自洽
        want = ("FORWARD_PENDING" if (b[iid]["anchor"] is None
                                      or b[iid]["formed_at"] < b[iid]["anchor"])
                else "IN_WINDOW_PARTIAL")
        if a[iid].get("outcome_type") != want:
            fails.append("S4: %s 的 outcome_type=%s，但形成日 %s 与锚点 %s 的关系应为 %s"
                         % (iid, a[iid].get("outcome_type"), a[iid].get("formed_at"),
                            b[iid]["anchor"], want))
        # S3：任何结算日都不得晚于 market_as_of
        for h in HORIZONS:
            sd = (a[iid]["outcome"].get(str(h)) or {}).get("settle_date")
            if sd and sd > market_as_of:
                fails.append("S3: %s 的 %d 日结算日 %s 晚于 market_as_of %s"
                             % (iid, h, sd, market_as_of))
    snap = os.path.join(SNAP_DIR, "CL-%s-v0_2.json" % market_as_of)
    if not os.path.exists(snap):
        fails.append("S2: 缺该结算日的快照 %s" % os.path.relpath(snap, REPO))
    elif io.open(snap, encoding="utf-8").read() != _dump(ledger):
        fails.append("S2: 结算快照与当前账本不一致 %s（同一 market_as_of 结果应可复现）"
                     % os.path.relpath(snap, REPO))
    last = (ledger.get("sources", {}).get("market") or {}).get("calendar_last_all")
    if last and last > market_as_of:
        n = sum(1 for d in _trading_days_after(market_as_of))
        warns.append("S5: 行情已推进到 %s，账本仍停在 %s（落后 %d 个交易日）"
                     "→ 需要跑 --write 追加新结算快照" % (last, market_as_of, n))
    notes.append("结算日 %s · 候选 %d" % (market_as_of, len(a)))
    return fails, warns, notes


def _trading_days_after(d):
    """★ 不能用 SQL 字符串比较：CSI300 用 dashed 日期，紧凑日期与它比较方向是反的。"""
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        rows = [_norm(r[0]) for r in con.execute(
            "SELECT trade_date FROM scan_daily WHERE series_id=? ORDER BY trade_date", (BENCH,))]
    finally:
        con.close()
    return [x for x in rows if x > d]


def _db_last_day():
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        r = con.execute("SELECT MAX(trade_date) FROM scan_daily WHERE series_id=?", (BENCH,)).fetchone()
    finally:
        con.close()
    return _norm(r[0]) if r and r[0] else None


# ─────────────────────────── 落盘（先检查，后写入） ───────────────────────────
#
# ★★★ v0.52 修复：旧顺序是「写形成快照 → 追加形成日志 → 才检查结算快照与 latest」，
#   一旦后两步拒绝，**形成日志已经被改过** —— 拒绝却没有回到操作前状态。
#   现在拆成两个阶段：
#     ① `preflight()` 把**所有**冲突判断做完（纯读，不写任何文件）；
#     ② 只有全部通过，才按固定顺序落盘（此时不会再有「因冲突而失败」的写入）。
#   不引入事务框架：冲突类失败全部由预检拦截，落盘阶段只剩 I/O 失败（会由 --check 报出）。

def write_guard_problem(path, body):
    """★ 纯检查：返回拒绝原因（`None` = 可以写）。**不修改任何文件。**"""
    if not os.path.exists(path):
        return None
    if io.open(path, encoding="utf-8").read() == body:
        return None
    return "已存在且内容不同（冻结文件只能写一次）"


def log_append_problem(old, new):
    """★ 纯检查：追加式约束。返回拒绝原因（`None` = 可以追加）。**不修改任何文件。**"""
    if old is None:
        return None
    old_by = {b["batch_id"]: b for b in old["batches"]}
    for b in new["batches"]:
        if b["batch_id"] in old_by and _dump(old_by[b["batch_id"]]) != _dump(b):
            return "历史批次 %s 被改动" % b["batch_id"]
    if [b["batch_id"] for b in old["batches"]] != [
            b["batch_id"] for b in new["batches"][:len(old["batches"])]]:
        return "批次顺序被改动"
    return None


def latest_ledger_problem(out, body, market_as_of):
    """★ 纯检查：同一 `market_as_of` 下 latest 账本不得变形（行情推进则允许更新）。"""
    if not os.path.exists(out):
        return None
    if _read(out).get("market_as_of") != market_as_of:
        return None
    if io.open(out, encoding="utf-8").read() == body:
        return None
    return "同一 market_as_of（%s）下内容发生变化" % market_as_of


def _write_guard(path, body, what):
    """★ 冻结文件不可被静默覆盖：内容不同 → 拒绝（返回 False）。"""
    if os.path.exists(path):
        if write_guard_problem(path, body) is None:
            print("  不变（已存在且一致）：%s" % os.path.relpath(path, REPO))
            return True
        print("REFUSE: %s 已存在且内容不同 → 拒绝覆盖（冻结文件只能写一次）" % what)
        print("        文件：%s" % os.path.relpath(path, REPO))
        print("        若确需新版本：升 artifact 版本（v0_2 → v0_3），不要改旧文件。")
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, "w", encoding="utf-8", newline="\n").write(body)
    print("  已写 %s" % os.path.relpath(path, REPO))
    return True


def save_log(log):
    """★ 追加式：已有批次必须逐字节保留，只允许追加新批次。"""
    path = os.path.join(CURRENT, LOG_NAME)
    p = log_append_problem(_read(path) if os.path.exists(path) else None, log)
    if p:
        print("REFUSE: 形成日志：%s → 拒绝写入" % p)
        return False
    io.open(path, "w", encoding="utf-8", newline="\n").write(_dump(log))
    print("  已写 %s" % os.path.relpath(path, REPO))
    return True


def preflight(new_log, batch, market_as_of, body, out, snap):
    """★★ 把所有「会不会被拒绝」的判断**在写任何文件之前**做完。

    返回 `(problems, plan)`：`problems` 非空 → 一个字节都不写；否则 `plan` 是按序落盘的动作。
    ★ 顺序：形成日志（提交点）→ 形成快照 → 结算快照 → latest。
      日志先写，是为了让「快照缺失」变成 `--check` 的 F6 FAIL（**响亮**），
      而不是留下一个没人检查的孤儿快照。
    """
    problems, plan = [], []
    old_log = load_log()

    # 1) 形成日志的追加式约束（无新批次时根本不重写这个文件）
    p = log_append_problem(old_log, new_log)
    if p:
        problems.append("形成日志：%s" % p)
    elif batch:
        plan.append(("log", None, None, "形成日志"))

    # 2) 冻结形成快照是否允许创建
    if batch:
        path = os.path.join(SNAP_DIR, "%s.json" % batch["batch_id"])
        p = write_guard_problem(path, _dump(batch))
        if p:
            problems.append("形成快照 %s：%s" % (batch["batch_id"], p))
        else:
            plan.append(("guard", path, _dump(batch), "形成快照 %s" % batch["batch_id"]))

    # 3) 同一 market_as_of 的结算快照
    p = write_guard_problem(snap, body)
    if p:
        problems.append("结算快照 CL-%s-v0_2：%s" % (market_as_of, p))
    else:
        plan.append(("guard", snap, body, "结算快照 CL-%s-v0_2" % market_as_of))

    # 4) 同一结算日的 latest 账本
    p = latest_ledger_problem(out, body, market_as_of)
    if p:
        problems.append("latest 账本：%s" % p)
    else:
        plan.append(("plain", out, body, "latest 账本"))

    return problems, plan


# ─────────────────────────── 入口 ───────────────────────────

def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", action="store_true", help="一次性：把 v0_1 迁成首批形成记录")
    ap.add_argument("--write", action="store_true", help="形成新候选 + 结算 + 写 latest 与快照")
    ap.add_argument("--check", action="store_true", help="校验（形成稳定性 + 结算一致性）")
    ap.add_argument("--check-formations", action="store_true")
    ap.add_argument("--check-settlement", action="store_true")
    ap.add_argument("--market-as-of", default=None, help="钉住结算日（默认取行情库最后交易日）")
    a = ap.parse_args(argv)

    # ★★ 形成稳定性**不需要**行情库 → CI 也要跑；只有结算一致性才依赖 history_scan.db。
    do_f = a.check or a.check_formations
    do_s = a.check or a.check_settlement
    if do_s and not os.path.exists(DB):
        print("SKIP 结算一致性：history_scan.db 不存在（CI 不携带 1.3GB 库）"
              " —— 形成稳定性仍会校验，**未**重算任何结算数字")
        do_s = False
        if not do_f:
            return 0
    if not (do_f or do_s or a.bootstrap or a.write):
        print("（无动作；加 --write / --check / --bootstrap）")
        return 0
    # ── bootstrap ──
    if a.bootstrap:
        if os.path.exists(os.path.join(CURRENT, LOG_NAME)):
            print("FAIL: %s 已存在 → bootstrap 只允许执行一次" % LOG_NAME)
            return 1
        batch = bootstrap_batch()
        log = {"artifact": "candidate_formation_log", "artifact_version": "0.1",
               "generated_by": "research/scripts/build_candidate_ledger_v0_2.py",
               "note": ("★ 追加式日志：已写入的批次**永不修改**，新批次只能追加。"
                        "形成记录只写「形成当时知道的事」，结算结果不写在这里。"),
               "instance_id_rule": "<board_series>__<window_year>-<MM>",
               "batches": [batch]}
        # ★ v0.52：同样先检查后写入（避免「写了形成快照、日志却被拒」留下孤儿快照）。
        #   顺序 = 快照 → 日志：一次性迁移若在日志处失败，可原样重跑（快照内容一致 → 幂等）。
        cf = os.path.join(SNAP_DIR, "%s.json" % batch["batch_id"])
        p = write_guard_problem(cf, _dump(batch))
        if p:
            print("REFUSE: 形成快照 %s：%s → **未修改任何文件**" % (batch["batch_id"], p))
            return 2
        _write_guard(cf, _dump(batch), "形成快照 %s" % batch["batch_id"])
        if not save_log(log):
            print("FAIL: 形成日志落盘被拒绝 → 请跑 --check 核对当前状态")
            return 2
        print("bootstrap 完成：%d 个实例 → 批次 %s" % (batch["counts"]["new_instances"],
                                                     batch["batch_id"]))
        return 0

    # ── check ──
    if do_f or do_s:
        log = load_log()
        fails, warns, notes = [], [], []
        if do_f:
            f, w, n = check_formations(log)
            fails += f; warns += w; notes += ["形成：" + x for x in n]
        if do_s:
            lp = os.path.join(CURRENT, OUT_NAME)
            if not os.path.exists(lp):
                fails.append("S0: 账本不存在 %s，请先 --write" % OUT_NAME)
            elif not log:
                fails.append("S0: 形成日志不存在，无法核对结算")
            else:
                ledger = _read(lp)
                pinned = a.market_as_of or ledger.get("market_as_of")
                f, w, n = check_settlement(log, ledger, pinned)
                fails += f; warns += w; notes += ["结算：" + x for x in n]
        for w in warns:
            print("WARN: %s" % w)
        if fails:
            for f in fails:
                print("FAIL: %s" % f)
            print("—— %d 项失败（%s）" % (len(fails), " · ".join(notes)))
            return 1
        print("PASS: 候选账本（%s）" % " · ".join(notes))
        return 0

    # ── build / write ──
    log = load_log()
    if not log:
        print("FAIL: 缺 %s —— 首次请先跑 --bootstrap（迁移 v0_1）" % LOG_NAME)
        return 1
    market_as_of = a.market_as_of or _db_last_day()
    pd_path, dg_path = _latest(PD_RE), _latest(DIGEST_RE)
    pd, dg = _read(pd_path), _read(dg_path)
    pd["_path"], dg["_path"] = pd_path, dg_path
    pd_as_of = pd["as_of"]
    pd_as_of_iso = pd_as_of if "-" in pd_as_of else "%s-%s-%s" % (
        pd_as_of[:4], pd_as_of[4:6], pd_as_of[6:])

    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        cal_all = [_norm(r[0]) for r in con.execute(
            "SELECT trade_date FROM scan_daily WHERE series_id=? ORDER BY trade_date", (BENCH,))]
    finally:
        con.close()

    # ★ 形成日必须等于行情最后交易日，否则「形成时间」是伪造的
    form_info = {"new": 0, "reappeared": 0, "skipped": None}
    batch = None
    if pd_as_of_iso != market_as_of:
        form_info["skipped"] = ("候选源 as_of=%s ≠ 行情 %s → 本次不形成新批次"
                                "（请先重跑 discover_seasonal_patterns_v0_5.py --write）"
                                % (pd_as_of_iso, market_as_of))
    else:
        batch, form_info = form_batch(log, pd, dg, market_as_of, cal_all)

    new_log = {"artifact": log["artifact"], "artifact_version": log["artifact_version"],
               "generated_by": log["generated_by"], "note": log["note"],
               "instance_id_rule": log["instance_id_rule"],
               "batches": list(log["batches"]) + ([batch] if batch else [])}

    formation_run = {
        "formed_at": market_as_of,
        "source_as_of": pd_as_of_iso,
        "skipped": form_info.get("skipped"),
        "new_instances": form_info["new"],
        "reappeared": form_info["reappeared"],
        "batch_id": batch["batch_id"] if batch else None,
        "note": ("新增 0 时不追加批次；重现事件（同一 instance_id 再次被选中）只记在本字段，"
                 "不写入形成日志（形成日志只记「第一次形成」）"),
    }
    ledger = build_ledger(new_log, market_as_of, pd, dg, formation_run)
    body = _dump(ledger)
    out = os.path.join(CURRENT, OUT_NAME)
    snap = os.path.join(SNAP_DIR, "CL-%s-v0_2.json" % market_as_of)

    s = ledger["summary"]
    print("形成日志：%d 批 / %d 实例（最早 %s）"
          % (len(new_log["batches"]), s["candidates"], ledger["formation_log"]["earliest_formed_at"]))
    if form_info.get("skipped"):
        print("  形成：跳过 —— %s" % form_info["skipped"])
    else:
        print("  形成：新增 %d · 重现 %d" % (form_info["new"], form_info["reappeared"]))
    print("结算（market_as_of %s）：候选 %d · 状态 %s"
          % (market_as_of, s["candidates"], s["by_status"]))
    for h in HORIZONS:
        print("  %2d 日：已结算 %d · 待 %d"
              % (h, s["settled"]["%dd" % h], s["pending"]["%dd" % h]))
    print("  结果类型：%s" % s["by_outcome_type"])

    if not a.write:
        print("（未写盘；加 --write 落盘）")
        return 0

    # ★★ v0.52：**先检查，后写入**。任何一项拒绝 → 一个字节都不写，返回 2。
    problems, plan = preflight(new_log, batch, market_as_of, body, out, snap)
    if problems:
        print("REFUSE: 预检未通过 → **未修改任何文件**"
              "（形成日志 / 冻结形成快照 / 冻结结算快照 / latest 账本 均保持操作前状态）")
        for p in problems:
            print("  - %s" % p)
        print("  若确需新版本：升 artifact 版本（v0_2 → v0_3），不要改旧文件。")
        return 2

    # 预检通过 → 按 plan 顺序落盘；此时不存在「因冲突而失败」的写入
    for kind, path, payload, label in plan:
        if kind == "log":
            if not save_log(new_log):
                # 只可能是落盘瞬间被外部改动（预检已通过）→ 立即停下并指向 --check
                print("FAIL: %s 落盘时被拒绝 → 请跑 --check 核对当前状态" % label)
                return 2
        elif kind == "guard":
            _write_guard(path, payload, label)
        else:
            if os.path.exists(path) and io.open(path, encoding="utf-8").read() == payload:
                print("  不变（已存在且一致）：%s" % os.path.relpath(path, REPO))
            else:
                io.open(path, "w", encoding="utf-8", newline="\n").write(payload)
                print("  已写 %s" % os.path.relpath(path, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
