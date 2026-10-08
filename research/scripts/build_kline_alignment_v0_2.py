#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_kline_alignment_v0_2.py —— 用**真实 K 线**对照 campaign 的 start / peak / end。

## ★★★ v0_1 → v0_2 的唯一变化：**价格口径修正**

v0_1 用 `adj_close`（**前复权收盘价**）算峰值。**这是错的，而且是错两次**：

1. **不该用前复权**。前复权会按**后续分红/送转**缩放历史价格，**峰值日会移位**。
   实测（`MUYUAN` 牧原股份，窗口 2020-01 ~ 2021-12）：

   | 口径 | 峰值日 | 峰值 |
   |---|---|---|
   | **原始价 `high`（盘中最高）** | **2020-03-09** | **139.92** |
   | 原始价 `close` | 2020-04-28 | 133.70 |
   | 前复权 `close`（v0_1 用的） | 2021-02-19 | 85.89 |

   而该 campaign 的 evidence **原文写着**：「牧原股份于 2020-03-09 盘中触及**历史最高价 139.92**」
   —— 与**原始价 `high`** 逐字吻合。**研究侧锚定的是原始价的盘中最高，不是前复权收盘。**

2. **不该用 `close`**。研究侧记录的是「**盘中最高**」（evidence 反复用这个词），对应 `high` 列。

**影响**：`C-2020-CONS-WHITE-GOODS` 因此从 `DIVERGENT` 翻转为 `SAME`
（`AIMEIKE` 爱美客：前复权峰 2021-07-01，**原始价峰 2021-02-18** —— 正是记录 peak）。

## 主口径与辅助口径

- **主口径（判定用）= 原始价 `high` 的峰值日**
- 辅助（仅记录，不参与判定）：原始价 `close` 峰、前复权 `close` 峰 —— 让口径差异**可见**

## 其余口径纪律（沿用 v0_1）

- **默认输出「逐标的」明细**（不掩盖分歧）；辅助给**中位数**；
  **不用等权组合作主口径**（`C-2019-COMM-5G` 教训：新易盛 +536% 峰在 7 月，另两只峰在 2 月）
- 判定：≤7 日 `SAME` · ≤31 日 `NEAR` · >31 日 `DIVERGENT`
- **只读** DB；**不修改**任何 campaign / evidence / 记录口径
- **不产生** score / ranking / probability —— 只有「一致 / 不一致」的**计数事实**

## 用法

    python research/scripts/build_kline_alignment_v0_2.py            # 生成 artifact
    python research/scripts/build_kline_alignment_v0_2.py --check    # 只比对，不写
"""

from __future__ import annotations

import io
import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

# 注：db.ROOT = <repo>/research，故 reports 位于 <repo>/research/research/reports
REP = os.path.join(db.ROOT, "research", "reports")
OUT = os.path.join(REP, "kline_alignment_v0_2.json")

PRE_DAYS = 60
POST_DAYS = 30

TOL_SAME = 7      # 相差 ≤7 自然日 → SAME（★ 用户 2026-10-08 明确：历史日期按**周**粒度即可）
TOL_NEAR = 31     # 相差 ≤31 日 → NEAR
# 其余 → DIVERGENT


def d(s):
    return date.fromisoformat(s)


def series(conn, sid, beg, end, col, price_type):
    """取某一列（原始价用 price_type='raw'；前复权用 'adjusted'）。"""
    return [
        (x, v)
        for x, v in conn.execute(
            "SELECT trade_date, %s FROM market_daily "
            "WHERE series_id=? AND price_type=? AND %s IS NOT NULL "
            "AND trade_date BETWEEN ? AND ? ORDER BY trade_date" % (col, col),
            (sid, price_type, beg, end),
        )
    ]


def argmax(r):
    return max(r, key=lambda x: x[1]) if r else None


def analyse_security(conn, sid, cstart, cend):
    beg = (d(cstart) - timedelta(days=PRE_DAYS)).isoformat()
    end = (d(cend) + timedelta(days=POST_DAYS)).isoformat()

    raw_hi = series(conn, sid, beg, end, "high", "raw")
    raw_cl = series(conn, sid, beg, end, "close", "raw")
    adj_cl = series(conn, sid, beg, end, "adj_close", "adjusted")
    if len(raw_hi) < 20:
        return {"security_id": sid, "status": "NO_DATA", "rows": len(raw_hi)}

    hi = argmax(raw_hi)
    base = raw_hi[0][1]
    out = {
        "security_id": sid,
        "status": "OK",
        "rows": len(raw_hi),
        "first_date": raw_hi[0][0],
        "last_date": raw_hi[-1][0],
        # ★ 主口径：原始价 high
        "peak_date": hi[0],
        "peak_high": hi[1],
        "peak_ret_pct": round(100 * (hi[1] / base - 1), 1),
        "final_ret_pct": round(100 * (raw_hi[-1][1] / base - 1), 1),
    }
    # 辅助口径（仅记录，便于看清口径差异）
    rc, ac = argmax(raw_cl), argmax(adj_cl)
    out["peak_date_raw_close"] = rc[0] if rc else None
    out["peak_date_adj_close"] = ac[0] if ac else None
    out["basis_note"] = ("主口径 = 原始价 high（盘中最高）；辅助记录原始 close 峰与前复权 close 峰。"
                         "★ 前复权会按后续分红缩放历史价，峰值日可能移位。")
    return out


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
    tally_adj = {"SAME": 0, "NEAR": 0, "DIVERGENT": 0, "UNKNOWN": 0}
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
        peaks = sorted(x["peak_date"] for x in ok)
        med = peaks[len(peaks) // 2] if len(peaks) % 2 else peaks[len(peaks) // 2 - 1]
        for x in ok:
            x["peak_verdict"] = verdict(p, x["peak_date"])
            # 辅助：若改用前复权口径，会是什么判定（用于暴露口径差异）
            x["peak_verdict_adj_close"] = verdict(p, x.get("peak_date_adj_close"))
        v = verdict(p, med)
        va = verdict(p, sorted(x["peak_date_adj_close"] for x in ok if x.get("peak_date_adj_close"))[
            len([x for x in ok if x.get("peak_date_adj_close")]) // 2] if any(x.get("peak_date_adj_close") for x in ok) else None)
        tally[v] = tally.get(v, 0) + 1
        tally_adj[va] = tally_adj.get(va, 0) + 1
        out[cid] = {
            "campaign_id": cid,
            "campaign_year": yr,
            "status": "OK",
            "recorded": {"start": s, "peak": p, "end": e},
            "coverage": {"securities": len(secs), "with_data": len(ok)},
            "price_basis": "PRIMARY=raw high（盘中最高）· AUX=raw close / adjusted close",
            "aggregation": "PRIMARY=per_security · AUX=median_peak_date（★ 不用等权组合作主口径）",
            "per_security": per,
            "median_peak_date": med,
            "median_peak_verdict": v,
        }

    res = {
        "artifact": "kline_alignment",
        "artifact_version": "0.2",
        "generated_by": "research/scripts/build_kline_alignment_v0_2.py",
        "position": ("Research-only —— 用真实 K 线对照 campaign 的 start/peak/end。"
                     "**不改动任何记录口径**；只输出「一致 / 不一致」的计数事实。"),
        "basis_change": {
            "from": "v0_1 用 adj_close（前复权收盘价）",
            "to": "v0_2 用 raw high（原始价盘中最高）",
            "why": ("① 前复权按后续分红缩放历史价 → 峰值日会移位（MUYUAN：原始 high 峰 2020-03-09=139.92，"
                    "前复权 close 峰 2021-02-19=85.89）；② evidence 原文用「盘中最高」→ 对应 high 列。"
                    "实测影响：C-2020-CONS-WHITE-GOODS 由 DIVERGENT 翻转为 SAME。"),
            "cross_check": "MUYUAN 原始 high 峰 2020-03-09 = 139.92，与该 campaign evidence 原文逐字吻合",
        },
        "rules": {
            "window": "记录 start 前 %d 日 ~ 记录 end 后 %d 日" % (PRE_DAYS, POST_DAYS),
            "price_basis": "原始价 high（盘中最高）—— 与 evidence 的表述一致",
            "aggregation": "主口径 = 逐标的；辅助 = peak_date 中位数；★ 等权组合易被极端标的带偏，不作主口径",
            "tolerance": {"SAME": "≤%d 日（周粒度）" % TOL_SAME, "NEAR": "≤%d 日" % TOL_NEAR,
                          "DIVERGENT": ">%d 日" % TOL_NEAR},
            "no_score": "本 artifact **不含** score / ranking / probability；只有计数事实",
        },
        "summary": tally,
        "summary_if_adj_close_basis": tally_adj,
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
    print("summary (raw high 口径):", json.dumps(tally, ensure_ascii=False))
    print("summary (前复权口径，仅供对比):", json.dumps(tally_adj, ensure_ascii=False))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
