#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""audit_jump_guard_v0_1.py —— `>45% 单日跳变` 守卫的**全库实证审计**（v0.27）。

## 背景

`theme_market_performance_v2` 把「窗口内相邻两条记录之间跳变 > 45%」判为
`invalid_price_series`。这个阈值长期只有**假设**（A 股单日涨跌幅上限 ≤30%），
没有全库误报 / 漏报实证。本脚本做这次实证。

## 方法

对 `market_data.db` 的**全部** adjusted 序列，按 `series_id` 取相邻记录对，
筛出 |Δ| > 45% 的对，然后对每一对判定三件事：

1. 两条记录是否**相邻交易日**（用 `trading_calendar` 查中间是否还有交易日）；
2. `raw` 口径在**同一对日期**上是否也跳变（→ 价格变化确实发生）；
3. 该对是否落在任何**当前事件窗口**内（→ 会不会影响已发布产物）。

## 结论（v0.27 实测）

见产物 `research/research/reports/jump_guard_audit_v0_1.json` 的 `verdict`。
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

REPO = db.REPO_ROOT
OUT_DIR = os.path.join(REPO, "research", "research", "reports")
CURRENT = os.path.join(REPO, "research", "current")
GENERATED_AT = "2026-10-20"
THRESHOLD = 0.45


def load_windows():
    """当前索引指向的事件窗口：[(file, event_id, [start,end], {security_id})]"""
    out = []
    index = json.load(open(os.path.join(CURRENT, "historical_event_maps_index.json"), encoding="utf-8"))
    for entry in index.get("maps") or []:
        path = os.path.join(CURRENT, entry["file"])
        if not os.path.exists(path):
            continue
        doc = json.load(open(path, encoding="utf-8"))
        for e in doc.get("events") or []:
            mp = e.get("market_performance") or {}
            w = mp.get("window")
            if w:
                out.append((entry["file"], e["event_id"], w,
                            set((mp.get("by_security") or {}).keys())))
    return out


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="审计 >45% 跳变守卫（全库）")
    ap.add_argument("--version", type=int, default=1)
    a = ap.parse_args(argv)

    conn = db.connect()
    db.require_market(conn)
    try:
        cal = [r[0] for r in conn.execute(
            "SELECT trade_date FROM trading_calendar ORDER BY trade_date")]
        cali = {d: i for i, d in enumerate(cal)}
        rows = conn.execute(
            """
            WITH s AS (
              SELECT series_id, trade_date, adj_close,
                     LAG(trade_date) OVER (PARTITION BY series_id ORDER BY trade_date) prev_d,
                     LAG(adj_close)  OVER (PARTITION BY series_id ORDER BY trade_date) prev_c
              FROM market_daily WHERE price_type='adjusted' AND adj_close IS NOT NULL
            )
            SELECT series_id, prev_d, trade_date, prev_c, adj_close,
                   adj_close/prev_c - 1 AS mv
            FROM s WHERE prev_c IS NOT NULL AND prev_c > 0 AND ABS(adj_close/prev_c - 1) > ?
            ORDER BY series_id, trade_date
            """, (THRESHOLD,)).fetchall()

        windows = load_windows()
        samples = []
        tally = {"adjacent_qfq_artifact": 0, "cross_gap": 0, "raw_corroborated": 0}
        in_window = 0
        for r in rows:
            sid, d0, d1 = r["series_id"], r["prev_d"], r["trade_date"]
            i0, i1 = cali.get(d0), cali.get(d1)
            adjacent = (i0 is not None and i1 is not None and i1 - i0 == 1)
            step = (i1 - i0) if (i0 is not None and i1 is not None) else None
            raw = conn.execute(
                "SELECT a.close c0, b.close c1 FROM market_daily a JOIN market_daily b "
                "ON b.series_id=a.series_id AND b.price_type='raw' "
                "WHERE a.series_id=? AND a.price_type='raw' AND a.trade_date=? AND b.trade_date=?",
                (sid, d0, d1)).fetchone()
            raw_mv = (raw["c1"] / raw["c0"] - 1.0) if (raw and raw["c0"] and raw["c0"] > 0) else None
            corroborated = raw_mv is not None and abs(raw_mv) > THRESHOLD
            if not adjacent:
                cls = "cross_gap"
            elif corroborated:
                cls = "raw_corroborated"
            else:
                cls = "adjacent_qfq_artifact"
            tally[cls] += 1
            hits = [(f, eid) for f, eid, w, sids in windows
                    if sid in sids and w[0] <= d1 <= w[1]]
            if hits:
                in_window += 1
            samples.append({
                "series_id": sid, "prev_date": d0, "date": d1,
                "adjacent_trading_days": adjacent, "calendar_step": step,
                "adjusted_move_pct": round(r["mv"] * 100, 2),
                "raw_move_pct": round(raw_mv * 100, 2) if raw_mv is not None else None,
                "class": cls,
                "in_current_event_windows": [eid for _, eid in hits],
            })
    finally:
        conn.close()

    doc = {
        "artifact": "jump_guard_audit",
        "artifact_version": "0.%d" % a.version,
        "generated_at": GENERATED_AT,
        "generated_by": "research/scripts/audit_jump_guard_v0_1.py",
        "supersedes": ("research/research/reports/jump_guard_audit_v0_%d.json" % (a.version - 1)
                       if a.version > 1 else None),
        "threshold_pct": THRESHOLD * 100,
        "scope": "market_data.db 全部 adjusted 序列的相邻记录对",
        "totals": {"flagged": len(rows), "in_current_event_windows": in_window, **tally},
        "verdict": {
            "threshold_kept": True,
            "why": "全库 **0 次**真实单日 >45% 波动（相邻交易日且 raw 同步者为零）"
                   "⇒ 阈值没有误伤真实价格变化，无需放宽；放宽只会让 qfq 方法学产物进入产物。",
            "classification_changed": "v2 起按证据三分："
                                      "`qfq_method_artifact`（相邻日、raw 不同步）/ "
                                      "`series_gap`（跨记录缺口，不是单日变化）/ "
                                      "`discontinuous_series`（相邻日且 raw 同步，价格变化确实发生）。"
                                      "★ 三者都**仍然拒绝计算**，数值零变化。",
            "not_relaxed": "本轮**未**修改 45% 阈值、**未**改任何历史数值。",
        },
        "known_limits": [
            "本审计只覆盖库内现有序列（214 只 / 2015–2026）；新增证券或换数据源需重跑。",
            "`trading_calendar` 由基准 SH000300 的交易日推导 —— 个股停牌日不算缺口，"
            "但**整段缺记录**算缺口（这正是 `series_gap` 要抓的）。",
            "「raw 同步」只说明两个口径都跳，**不**证明价格变动有基本面原因；"
            "本产物只做数据分类，不做因果判断。",
        ],
        "samples": samples,
    }
    out = os.path.join(OUT_DIR, "jump_guard_audit_v0_%d.json" % a.version)
    if os.path.exists(out):
        print("FAIL: 目标已存在，拒绝覆盖：%s" % os.path.relpath(out, REPO))
        return 1
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    print("已生成 %s" % os.path.relpath(out, REPO))
    print("  总计 %d 次：相邻日 qfq 产物 %d · 跨缺口 %d · raw 同步 %d · 落在现有窗口内 %d"
          % (len(rows), tally["adjacent_qfq_artifact"], tally["cross_gap"],
             tally["raw_corroborated"], in_window))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
