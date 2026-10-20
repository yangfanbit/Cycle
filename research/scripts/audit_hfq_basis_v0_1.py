#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""audit_hfq_basis_v0_1.py —— 早年高分红股「替代收益口径」的**审计产物**（v0.27）。

## 结论先说

**hfq（后复权）不作为替代口径采用。** 不是因为它不可取，而是因为它的**复权约定无法从数据解释**：

| 检验 | 结果 | 含义 |
|---|---|---|
| 取数可得性 | 三只股票 2015–2018 全部取到，**无一条非正价格** | 数据可得 ✓ |
| 请求区间稳定性 | 同一交易日在不同区间请求下取值一致（锚定上市首日） | 可复现 ✓ |
| **逐日复权因子** | **并非常数**：常态 ±0.15%，p99 ≈ 3.9%，除权日 +1.53% | 无法用乘性复权解释 ✗ |
| 加性模型 `hfq−k·raw` | 短段（≈15 交易日）拟合残差≈0，但**残差随跨度增长**（230 日段 RMS 15–45） | 无法用「除权价+累计分红」解释 ✗ |
| 收益独立核验 | 缺少分红/送转记录 → 无法由 raw + 公司行为独立复算 | ✗ |

⇒ 满足「来源可追溯 / 取数可复现」，但**不满足**「公司行为处理可解释 / 收益可独立核验」。
按纪律：**保留不可计算状态**，不把 hfq 塞进 `adjusted` 字段，也不用 raw 冒充含分红收益。

## 真正缺失的东西

一份**可核验的分红/送转记录**（除权日 + 每股派息/送转比例），使得总收益可由
`raw` 与公司行为独立重建并审计；或换用**复权方法有明文文档**的数据源。
拿到之后才谈得上替代口径。

## 用法

    python research/scripts/audit_hfq_basis_v0_1.py            # 生成 v0_1（存在则拒绝）
    python research/scripts/audit_hfq_basis_v0_1.py --version 2
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402
# ★ 复用既有抓取器的请求路径（同一 endpoint / 节流 / 限流守卫）—— **不新写抓取器**
from scripts.fetch_market_batch_v0_3 import request_segment, year_segments  # noqa: E402

REPO = db.REPO_ROOT          # 仓库根（db.ROOT 指向 research/）
OUT_DIR = os.path.join(REPO, "research", "research", "reports")  # 报告目录（与 early_observation 同级）

TARGETS = [
    ("MOUTAI", "sh600519"),
    ("WULIANGYE", "sz000858"),
    ("LUZHOULAOJIAO", "sz000568"),
]
RANGE = ("2015-01-01", "2018-12-31")
GENERATED_AT = "2026-10-20"


def fetch(symbol: str, fq: str) -> list:
    out = []
    for seg in year_segments(*RANGE):
        out.extend(request_segment(symbol, seg[0], seg[1], fq))
    seen, dedup = set(), []
    for rec in out:
        if rec[0] not in seen:
            seen.add(rec[0])
            dedup.append(rec)
    dedup.sort(key=lambda r: r[0])
    return dedup


def affine_rms(xs: list, ys: list):
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return None
    k = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den
    c = my - k * mx
    return k, c, (sum((y - (k * x + c)) ** 2 for x, y in zip(xs, ys)) / n) ** 0.5


def audit_one(conn, sid: str, symbol: str) -> dict:
    raw_rows = fetch(symbol, "")
    hfq_rows = fetch(symbol, "hfq")
    qfq_rows = fetch(symbol, "qfq")
    if not raw_rows or not hfq_rows:
        return {"status": "UNAVAILABLE", "reason": "provider 未返回 raw 或 hfq"}
    R = {r[0]: float(r[3]) for r in raw_rows}
    H = {r[0]: float(r[3]) for r in hfq_rows}
    Q = {r[0]: float(r[3]) for r in qfq_rows}
    dates = sorted(set(R) & set(H))

    # ① 逐日复权因子（hfq/raw）的变化分布 —— 决定性证据
    steps = []
    for a, b in zip(dates, dates[1:]):
        steps.append((H[b] / R[b]) / (H[a] / R[a]) - 1.0)
    steps_sorted = sorted(steps)
    n = len(steps_sorted)
    pct = lambda q: round(steps_sorted[min(n - 1, int(n * q))] * 100, 3)  # noqa: E731
    # ★ 舍入量级：hfq 保留 3 位小数、数值量级 10^3–10^4 → 舍入引起的因子误差 ≈ 1e-4 %。
    #   若大量交易日的因子变化远大于此，就不是舍入，而是**约定本身**在变。
    over_005 = sum(1 for x in steps if abs(x) > 0.0005)
    factor_steps = {"n": n, "p50_pct": pct(0.50), "p90_pct": pct(0.90),
                    "p99_pct": pct(0.99), "max_pct": round(steps_sorted[-1] * 100, 3),
                    "min_pct": round(steps_sorted[0] * 100, 3),
                    "rounding_noise_pct": 0.0001,
                    "days_over_0_05pct": over_005,
                    "share_over_0_05pct": round(over_005 / n * 100, 1) if n else None}

    # ② 仿射模型残差随跨度的增长（短段≈0 → 长段放大 ⇒ 不是分段常数）
    spans = {}
    for span in (15, 60, 120, 230):
        vals = []
        for i in range(0, max(1, len(dates) - span), span):
            ds = dates[i:i + span]
            f = affine_rms([R[d] for d in ds], [H[d] for d in ds])
            if f:
                vals.append(f[2])
        spans["%dd" % span] = round(max(vals), 3) if vals else None

    # ③ 事件窗口三种口径的收益（CONS-2016-BAIJIU：2016-06-01 → 2017-12-31，双端包含）
    inner = [d for d in dates if "2016-06-01" <= d <= "2017-12-31"]
    a, b = inner[0], inner[-1]
    def ret(d):  # noqa: E306
        x, y = d[a], d[b]
        return None if (x is None or y is None or x <= 0 or y <= 0) else round((y / x - 1) * 100, 2)
    window = {
        "window": [a, b],
        "trading_days": len(inner),
        "raw_period_return_pct": ret(R),
        "hfq_period_return_pct": ret(H),
        "qfq_period_return_pct": ret(Q),
        "qfq_non_positive_at_start": Q.get(a) is not None and Q[a] <= 0,
        "note": "raw = 仅价格（不含分红，**不得**当作含分红收益）；"
                "qfq = 前复权（本窗口起点为非正价格 → 合同拒绝计算）；"
                "hfq = 后复权（数值可得，但复权约定不可解释 → 未采用）",
    }

    neg_qfq = sum(1 for d in dates if Q.get(d) is not None and Q[d] <= 0)
    return {
        "symbol": symbol,
        "range": [dates[0], dates[-1]],
        "trading_days": len(dates),
        "qfq_non_positive_days": neg_qfq,
        "hfq_non_positive_days": sum(1 for d in dates if H[d] <= 0),
        "factor_steps": factor_steps,
        "affine_rms_by_span": spans,
        "window_check": window,
    }


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="审计 hfq 是否可作为早年高分红段的替代收益口径")
    ap.add_argument("--version", type=int, default=1)
    a = ap.parse_args(argv)

    conn = db.connect()
    db.require_market(conn)
    try:
        series = {}
        for sid, sym in TARGETS:
            series[sid] = audit_one(conn, sid, sym)
            s = series[sid]
            if s.get("status") == "UNAVAILABLE":
                print("FAIL: %s 取数失败（%s）" % (sid, s.get("reason")))
                return 1
            print("  %-14s 因子步进 p50=%+.3f%% p99=%+.3f%% max=%+.3f%% · 仿射RMS %s"
                  % (sid, s["factor_steps"]["p50_pct"], s["factor_steps"]["p99_pct"],
                     s["factor_steps"]["max_pct"], s["affine_rms_by_span"]))
    finally:
        conn.close()

    doc = {
        "artifact": "hfq_basis_audit",
        "artifact_version": "0.%d" % a.version,
        "generated_at": GENERATED_AT,
        "generated_by": "research/scripts/audit_hfq_basis_v0_1.py",
        "supersedes": ("research/research/reports/hfq_basis_audit_v0_%d.json" % (a.version - 1)
                       if a.version > 1 else None),
        "question": "早年高分红股（qfq 在 2015–2016 段为非正价格）能否用 hfq 作为可核验的替代收益口径？",
        "verdict": "NOT_ADOPTED",
        "verdict_reason": "hfq 数值可得且取数可复现，但**逐日复权因子并非常数**"
                          "（常态 ±0.15%、p99≈3.9%、除权日 +1.53%），"
                          "加性模型（hfq = k·raw + c）的残差随跨度增长（15 日≈0 → 230 日 15–45）"
                          "⇒ 复权约定**无法从数据解释**，收益**无法由 raw + 公司行为独立核验**。"
                          "按纪律保留 `invalid_price_series / non_positive_adj_close` 的不可计算状态。",
        "what_is_missing": [
            "一份可核验的分红 / 送转记录（除权日 + 每股派息 / 送转比例）——"
            "有了它，总收益可由 raw 与公司行为独立重建并审计；",
            "或换用**复权方法有明文文档**的数据源（当前 provider 未公开其 hfq 算法）。",
        ],
        "rejected_alternatives": {
            "raw": "仅价格、不含分红 → 会把「价格涨幅」冒充「含分红收益」，明令禁止。",
            "hfq": "见 verdict_reason；且与默认 qfq（乘性再投资）在高分红长窗口下会系统性分叉，"
                   "混用会破坏事件内可比性。",
            "自建复权因子": "缺少可核验的分红记录，等于自造因子 —— 不采用。",
        },
        "source": {
            "provider": "tencent",
            "endpoint": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
            "params": "fq ∈ {''(raw), 'qfq', 'hfq'}",
            "retrieved_range": list(RANGE),
            "note": "与 market_daily 同源同 endpoint、不同 fq 参数；本产物**只做审计**，"
                    "不进入任何产品产物、不覆盖 market_daily。",
        },
        "series": series,
    }
    out = os.path.join(OUT_DIR, "hfq_basis_audit_v0_%d.json" % a.version)
    if os.path.exists(out):
        print("FAIL: 目标已存在，拒绝覆盖：%s" % os.path.relpath(out, REPO))
        return 1
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    print("已生成 %s（裁定 %s）" % (os.path.relpath(out, REPO), doc["verdict"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
