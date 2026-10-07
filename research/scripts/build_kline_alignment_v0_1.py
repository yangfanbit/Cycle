#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_kline_alignment_v0_1.py —— 用**真实 K 线**对照 campaign 的 start / peak / end。

## 它回答什么

「记录里的 start / peak / end，与**代表标的真实行情**算出来的，是否一致？」

→ 让日期锚点从「媒体转述」变成「**市场客观事实**」（见
`docs/DESIGN_KLINE_VALIDATION_AND_EARLY_WINDOW_v0_1.md` §1.3）。

## ★★ 口径纪律（必须遵守，否则结论会被极端标的带偏）

`C-2019-COMM-5G` 的教训：等权组合的峰值由**涨幅最大的那只**决定
（新易盛 +536% 峰在 2020-07-14），而另两只峰在 2020-02 —— 与记录一致。
**因此本脚本：**
- **默认输出「逐标的」明细**（不掩盖分歧）
- 同时给出**中位数**口径（稳健）
- **不给「等权组合」作为主口径**（易被极端值主导），但保留为参考

## 边界

- **只读** DB；**不修改**任何 campaign / evidence / 记录口径。
- **不产生** score / ranking / probability —— 只输出「一致 / 不一致」的**计数事实**。
- 覆盖不足者**如实标 `NO_DATA`**，不推断。

## 用法

    python research/scripts/build_kline_alignment_v0_1.py            # 生成 artifact
    python research/scripts/build_kline_alignment_v0_1.py --check    # 只比对，不写
"""

from __future__ import annotations

import io
import json
import os
import statistics
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

# 注：db.ROOT = <repo>/research，故 reports 位于 <repo>/research/research/reports
REP = os.path.join(db.ROOT, "research", "reports")
OUT = os.path.join(REP, "kline_alignment_v0_1.json")

# 对照窗口：记录 start 前 60 个自然日 ~ 记录 end 后 30 个自然日
PRE_DAYS = 60
POST_DAYS = 30

# 一致性判定（**计数事实**，不是评分）
TOL_SAME = 7      # 相差 ≤7 自然日 → SAME
TOL_NEAR = 31     # 相差 ≤31 日 → NEAR
# 其余 → DIVERGENT


def closes(conn, sid, beg, end):
    return [
        (d, v)
        for d, v in conn.execute(
            "SELECT trade_date, adj_close FROM market_daily "
            "WHERE series_id=? AND price_type='adjusted' AND adj_close IS NOT NULL "
            "AND trade_date BETWEEN ? AND ? ORDER BY trade_date",
            (sid, beg, end),
        )
    ]


def d(s):
    return date.fromisoformat(s)


def analyse_security(conn, sid, cstart, cend):
    beg = (d(cstart) - timedelta(days=PRE_DAYS)).isoformat()
    end = (d(cend) + timedelta(days=POST_DAYS)).isoformat()
    r = closes(conn, sid, beg, end)
    if len(r) < 20:
        return {"security_id": sid, "status": "NO_DATA", "rows": len(r)}
    base = r[0][1]
    hi = max(r, key=lambda x: x[1])
    lo = min(r, key=lambda x: x[1])
    return {
        "security_id": sid,
        "status": "OK",
        "rows": len(r),
        "first_date": r[0][0],
        "last_date": r[-1][0],
        "peak_date": hi[0],
        "peak_ret_pct": round(100 * (hi[1] / base - 1), 1),
        "trough_date": lo[0],
        "trough_ret_pct": round(100 * (lo[1] / base - 1), 1),
        "final_ret_pct": round(100 * (r[-1][1] / base - 1), 1),
    }


def verdict(recorded, measured):
    if not recorded or not measured:
        return "UNKNOWN"
    delta = abs((d(recorded) - d(measured)).days)
    if delta <= TOL_SAME:
        return "SAME"
    if delta <= TOL_NEAR:
        return "NEAR"
    return "DIVERGENT"


def main(argv):
    check = "--check" in argv
    conn = db.connect()

    rows = conn.execute(
        "SELECT campaign_id, campaign_year, start_date, peak_date, end_date, strength "
        "FROM campaigns ORDER BY campaign_year, campaign_id"
    ).fetchall()

    out = {}
    tally = {"SAME": 0, "NEAR": 0, "DIVERGENT": 0, "UNKNOWN": 0, "NO_COVERAGE": 0}
    for cid, yr, s, p, e, strength in rows:
        secs = [r[0] for r in conn.execute(
            "SELECT security_id FROM campaign_securities WHERE campaign_id=?", (cid,))]
        if not secs:
            out[cid] = {"campaign_id": cid, "status": "NO_SECURITIES"}
            tally["NO_COVERAGE"] += 1
            continue
        per = [analyse_security(conn, x, s, e or s) for x in secs]
        ok = [x for x in per if x["status"] == "OK"]
        if not ok:
            out[cid] = {"campaign_id": cid, "status": "NO_DATA", "per_security": per}
            tally["NO_COVERAGE"] += 1
            continue
        # ★ 主口径 = 逐标的；辅助 = 中位数
        peaks = sorted(x["peak_date"] for x in ok)
        med = peaks[len(peaks) // 2] if len(peaks) % 2 else peaks[len(peaks) // 2 - 1]
        # 逐标的判定
        for x in ok:
            x["peak_verdict"] = verdict(p, x["peak_date"])
        v = verdict(p, med)
        tally[v] = tally.get(v, 0) + 1
        out[cid] = {
            "campaign_id": cid,
            "campaign_year": yr,
            "status": "OK",
            "recorded": {"start": s, "peak": p, "end": e},
            "coverage": {"securities": len(secs), "with_data": len(ok)},
            "aggregation": "PRIMARY=per_security · AUX=median_peak_date（★ 不用等权组合作主口径）",
            "per_security": per,
            "median_peak_date": med,
            "median_peak_verdict": v,
        }

    res = {
        "artifact": "kline_alignment",
        "artifact_version": "0.1",
        "generated_by": "research/scripts/build_kline_alignment_v0_1.py",
        "position": ("Research-only —— 用真实 K 线对照 campaign 的 start/peak/end。"
                     "**不改动任何记录口径**；只输出「一致 / 不一致」的计数事实。"),
        "rules": {
            "window": "记录 start 前 %d 日 ~ 记录 end 后 %d 日" % (PRE_DAYS, POST_DAYS),
            "aggregation": "主口径 = 逐标的；辅助 = peak_date 中位数；★ 等权组合易被极端标的带偏，不作主口径",
            "tolerance": {"SAME": "≤%d 日" % TOL_SAME, "NEAR": "≤%d 日" % TOL_NEAR, "DIVERGENT": ">%d 日" % TOL_NEAR},
            "no_score": "本 artifact **不含** score / ranking / probability；只有计数事实",
        },
        "summary": tally,
        "by_campaign": out,
    }

    body = json.dumps(res, ensure_ascii=False, indent=1) + "\n"
    if check:
        if os.path.exists(OUT) and io.open(OUT, encoding="utf-8").read() == body:
            print("PASS —— 与既有产物逐字节一致")
            return 0
        print("FAIL —— 与既有产物不一致（或产物不存在）")
        return 1
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    print("written", OUT)
    print("summary:", json.dumps(tally, ensure_ascii=False))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
