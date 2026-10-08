#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_early_observation_v0_1.py —— 「提前观察窗口」的**描述性**产物（历史侧）。

## 核心链路里那一段

```
… → 相关因素 → **提前观察** → 当前状态与历史结构对照
```

实测：export 里 `early_signal` 字段 **0 个 campaign 有值** —— **这一段从未实现**。
本脚本实现其中的**历史侧**：*每个历史 Campaign 启动前 N 个交易日，K 线上长什么样。*

## ★★ 红线（决定性）

`AGENTS.md` §1 明令禁止 **概率 / 胜率 / 推荐分 / 预测**。因此本产物**只描述事实**：

- ✅ 「这个 Campaign 启动前 20 个交易日，成交量分位 / 相对强度 / 波动率 / 均线位置分别是多少」
- ❌ 「出现这种形态后，N 日内上涨的概率是 P%」—— **不做**
- ❌ 任何评分 / 排序 / 档位 —— **不做**

## ★ 全部观测量都是 **ex-ante**（只用当日及之前的数据）

| 观测量 | 定义 |
|---|---|
| `vol_pct60` | 当日成交量在**过去 60 个交易日**中的分位（0–1） |
| `ret_20` | 过去 20 个交易日收益率（%） |
| `rel_strength_20` | `ret_20` − 基准（SH000300）同期收益，百分点 |
| `vol_ratio` | 20 日已实现波动率 / 60 日已实现波动率（日对数收益标准差之比） |
| `above_ma20` / `above_ma60` | 收盘价是否站上 20 / 60 日均线 |

## ★ 口径纪律

- **逐标的为主口径**，另给**跨标的中位数**作辅助（`C-2019-COMM-5G` 教训：等权组合易被极端标的带偏）。
- 用**原始价**（与 peak 对照口径一致）；成交量取原始行。
- 数据不足者**如实标 `NO_DATA`**，不推断、不外推。

## 用法

    python research/scripts/build_early_observation_v0_1.py
"""

from __future__ import annotations

import io
import json
import math
import os
import statistics
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

REP = os.path.join(db.ROOT, "research", "reports")
OUT = os.path.join(REP, "early_observation_v0_1.json")

BENCH = "SH000300"
LOOKBACK = 20          # 「启动前 N 个交易日」
MIN_HISTORY = 60       # 算 vol_pct60 / vol_ratio 所需的最小历史


def load_series(conn, sid):
    return conn.execute(
        "SELECT trade_date, close, volume FROM market_daily "
        "WHERE series_id=? AND price_type='raw' AND close IS NOT NULL ORDER BY trade_date",
        (sid,)).fetchall()


def observables(rows, i, bench_ret20):
    """在 rows[i] 这一天，**只用 ≤ i 的数据**算观测量。"""
    if i + 1 < MIN_HISTORY:
        return None
    close = [r[1] for r in rows]
    vol = [r[2] for r in rows]
    # 成交量分位（过去 60 日，含当日）
    win = [v for v in vol[i - 59:i + 1] if v is not None]
    vp = None
    if len(win) >= 30 and vol[i] is not None:
        vp = round(sum(1 for v in win if v <= vol[i]) / len(win), 3)
    # 20 日收益
    ret20 = (close[i] / close[i - 20] - 1) * 100
    # 波动率比
    def sd(a):
        rs = [math.log(a[k] / a[k - 1]) for k in range(1, len(a)) if a[k] and a[k - 1]]
        return statistics.pstdev(rs) if len(rs) >= 5 else None
    s20, s60 = sd(close[i - 20:i + 1]), sd(close[i - 60:i + 1])
    vr = round(s20 / s60, 3) if (s20 and s60) else None
    ma20 = sum(close[i - 19:i + 1]) / 20
    ma60 = sum(close[i - 59:i + 1]) / 60
    return {
        "date": rows[i][0],
        "close": round(close[i], 3),
        "vol_pct60": vp,
        "ret_20_pct": round(ret20, 2),
        "rel_strength_20": (round(ret20 - bench_ret20, 2) if bench_ret20 is not None else None),
        "vol_ratio": vr,
        "above_ma20": close[i] > ma20,
        "above_ma60": close[i] > ma60,
    }


def median_of(items, key):
    vals = [x[key] for x in items if x.get(key) is not None]
    return round(statistics.median(vals), 3) if vals else None


def main():
    conn = db.connect()
    bench = load_series(conn, BENCH)
    bench_idx = {r[0]: i for i, r in enumerate(bench)}

    def bench_ret20_on(day):
        i = bench_idx.get(day)
        if i is None or i < 20:
            return None
        return (bench[i][1] / bench[i - 20][1] - 1) * 100

    rows = conn.execute("SELECT campaign_id, campaign_year, start_date, peak_date, end_date FROM campaigns ORDER BY campaign_year, campaign_id").fetchall()
    cache, out = {}, {}
    tally = {"OK": 0, "PARTIAL": 0, "NO_DATA": 0}

    for cid, yr, s, p, e in rows:
        if not s:
            out[cid] = {"campaign_id": cid, "status": "NO_START"}
            tally["NO_DATA"] += 1
            continue
        secs = [x[0] for x in conn.execute("SELECT security_id FROM campaign_securities WHERE campaign_id=?", (cid,))]
        per, notes = [], []
        for sid in secs:
            if sid not in cache:
                cache[sid] = load_series(conn, sid)
            rs = cache[sid]
            idx = [i for i, r in enumerate(rs) if r[0] < s]     # 启动**之前**的交易日
            if len(idx) < MIN_HISTORY:
                per.append({"security_id": sid, "status": "NO_DATA",
                            "rows_before_start": len(idx)})
                continue
            pts = idx[-LOOKBACK:]
            series = [observables(rs, i, bench_ret20_on(rs[i][0])) for i in pts]
            series = [x for x in series if x]
            if not series:
                per.append({"security_id": sid, "status": "NO_DATA", "rows_before_start": len(idx)})
                continue
            per.append({
                "security_id": sid, "status": "OK",
                "lookback_from": series[0]["date"], "lookback_to": series[-1]["date"],
                "series": series,
                "at_last_day": series[-1],
            })
        ok = [x for x in per if x["status"] == "OK"]
        if not ok:
            out[cid] = {"campaign_id": cid, "campaign_year": yr, "start": s,
                        "status": "NO_DATA", "per_security": per}
            tally["NO_DATA"] += 1
            continue
        # 辅助口径：跨标的中位数（★ 非主口径）
        n = max(len(x["series"]) for x in ok)
        med = []
        for k in range(-n, 0):
            items = [x["series"][k] for x in ok if len(x["series"]) >= -k]
            if not items:
                continue
            med.append({"date": items[-1]["date"],
                        "vol_pct60": median_of(items, "vol_pct60"),
                        "ret_20_pct": median_of(items, "ret_20_pct"),
                        "rel_strength_20": median_of(items, "rel_strength_20"),
                        "vol_ratio": median_of(items, "vol_ratio")})
        status = "OK" if len(ok) == len(secs) else "PARTIAL"
        tally[status] += 1
        if len(ok) < len(secs):
            notes.append("仅 %d/%d 个标的在启动前有足够历史" % (len(ok), len(secs)))
        out[cid] = {
            "campaign_id": cid, "campaign_year": yr,
            "start": s, "peak": p, "end": e,
            "status": status,
            "lookback_trading_days": LOOKBACK,
            "benchmark": BENCH,
            "aggregation": "PRIMARY=per_security · AUX=median（★ 等权组合易被极端标的带偏，不作主口径）",
            "per_security": per,
            "median_series": med,
            "notes": notes,
        }

    res = {
        "artifact": "early_observation",
        "artifact_version": "0.1",
        "generated_by": "research/scripts/build_early_observation_v0_1.py",
        "position": ("Research-only 描述性产物 —— **只描述**「历史 Campaign 启动前 N 个交易日的量价状态」。"
                     "**不含**概率 / 胜率 / 评分 / 排序 / 预测。"),
        "scope": {
            "covered": "**历史侧**（每个 campaign 的启动前窗口）",
            "not_covered": ("**当前侧** —— 6 个当前研究对象**没有任何标的字段**，"
                            "无法用同一套量计算「现在像不像」。"
                            "因此设计文档 §2.3 设想的「历史 ↔ 当前并列呈现」**目前无法实现**，"
                            "需研究侧先决定「当前对象如何映射到标的」。"),
        },
        "rules": {
            "window": "启动日前 %d 个交易日" % LOOKBACK,
            "ex_ante": "全部观测量**只用当日及之前**的数据计算（滚动窗口），不引入未来信息",
            "observables": {
                "vol_pct60": "当日成交量在过去 60 个交易日中的分位（0–1）",
                "ret_20_pct": "过去 20 个交易日收益率（%）",
                "rel_strength_20": "ret_20 − 基准 SH000300 同期收益（百分点）",
                "vol_ratio": "20 日已实现波动率 / 60 日已实现波动率（日对数收益标准差之比）",
                "above_ma20": "收盘价是否站上 20 日均线",
                "above_ma60": "收盘价是否站上 60 日均线",
            },
            "price_basis": "原始价 close（与 peak 对照口径一致）",
            "aggregation": "主口径 = 逐标的；辅助 = 跨标的中位数",
            "no_probability": ("★ **不做**「出现该形态后 N 日内上涨的概率」；**不做**评分 / 排序 / 档位。"
                               "样本极小（最多 53 段），任何『规律』都极不稳健 —— 正因为它像预测，才更严格不做预测。"),
        },
        "summary": tally,
        "by_campaign": out,
    }
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    print("written", OUT)
    print("summary:", json.dumps(tally, ensure_ascii=False))
    print()
    print("=== 样例：C-2023-AD 启动前 20 个交易日（逐标的末值）===")
    v = out.get("C-2023-AD")
    if v and v.get("status") != "NO_DATA":
        for x in v["per_security"]:
            if x["status"] == "OK":
                a = x["at_last_day"]
                print("  %-14s %s  vol_pct60=%-5s ret20=%-6s rel_str=%-6s vol_ratio=%-5s ma20=%s ma60=%s" % (
                    x["security_id"], a["date"], a["vol_pct60"], a["ret_20_pct"], a["rel_strength_20"],
                    a["vol_ratio"], a["above_ma20"], a["above_ma60"]))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
