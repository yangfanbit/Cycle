#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""audit_hfq_basis_v0_1.py —— 早年高分红股「替代收益口径」的**审计产物**。

## v0.2 修正（2026-10-21）

★★ **v0.1 用错了字段**：腾讯 `fqkline` 每条记录是
`[date, open, close, high, low, volume]`，即 **close 在 rec[2]、high 在 rec[3]**
（与 `fetch_market_batch_v0_3.row_to_dict` 一致）。v0.1 取了 `r[3]`，
于是把**最高价**当成收盘价算了全部统计（因子步进 / 仿射拟合 / 窗口收益）。
v0.2 起：
- 字段索引用**具名常量** `F_CLOSE / F_HIGH / …`，并在 `field_audit` 块里**留证**
  （同一交易日 close ≠ high，且收益按 close→close 复算）；
- 新增 `field_audit.regression_ok` 自检：若 close 与 high 未能区分（或两者算出的收益相同），
  **直接拒绝生成产物** —— 防止「改了注释没改字段」再次发生。

## 结论（v0.2，基于收盘价）

**hfq 不作为替代口径采用（NOT_ADOPTED）。** 判据不是「价格为正」，而是四条准入：

| 检验 | 结果 |
|---|---|
| ① 可取数 / 跨请求区间稳定 | ✓（锚定上市首日，同一交易日取值一致） |
| ② 复权关系符合可解释的价格调整模型 | ✗ 见下 |
| ③ 复权方法有可靠文档 | ✗ provider 未公开算法 |
| ④ 收益可由公司行为数据独立核验 | ✗ 缺分红 / 送转记录 |

②的具体证据（`CONS-2016-BAIJIU` 窗口 2016-06-01 → 2017-12-31）：
- 现金分红的因子步进是**正的**（+2.15%/+1.56% 等），但窗口内因子**累计下降**
  （−3.21% / −4.13% / −13.95%），且**没有**负向送转步进可解释这个下降
  —— 任何标准后复权都不可能出现「一边派现金、一边因子净下降」；
- 结果是 hfq 收益**低于** raw 价格收益（含分红应更高），经济上不成立；
- 逐日因子变化在 65.9% 的交易日超过 0.05%（舍入量级约 1e-4）；
- 仿射模型 `hfq = k·raw + c` 的残差**不随跨度缩小**（15 日段仍 4.8–28.2）。

⇒ 保留 `invalid_price_series / non_positive_adj_close` 的不可计算状态。
**真正缺失**：可核验的分红/送转记录，或复权方法有明文文档的数据源。

## 用法

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

REPO = db.REPO_ROOT
OUT_DIR = os.path.join(REPO, "research", "research", "reports")

# ★★ 腾讯 fqkline 记录字段（与 fetch_market_batch_v0_3.row_to_dict 一一对应）
#    [0]=date [1]=open [2]=close [3]=high [4]=low [5]=volume [6]=amount
#    ★ v0.1 的缺陷正是把 F_HIGH 当成了收盘价 —— 任何按价格计算的地方都**只用 F_CLOSE**。
F_DATE, F_OPEN, F_CLOSE, F_HIGH, F_LOW, F_VOL = 0, 1, 2, 3, 4, 5

TARGETS = [
    ("MOUTAI", "sh600519"),
    ("WULIANGYE", "sz000858"),
    ("LUZHOULAOJIAO", "sz000568"),
]
RANGE = ("2015-01-01", "2018-12-31")
WINDOW = ("2016-06-01", "2017-12-31")      # CONS-2016-BAIJIU 的行情窗口
GENERATED_AT = "2026-10-21"


# ★ 本地缓存：provider 对突发请求会返回 HTTP 501（WAF 页），重试代价高且会丢进度。
#   ★ 按**语义**缓存（close / high 两个字典），不缓存原始行 —— 避免字段索引换算出错。
CACHE_PATH = os.path.join(REPO, ".tmp", "hfq_audit_cache.json")


def _load_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(cache, fh, ensure_ascii=False)


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def fetch(symbol: str, fq: str, field: int = F_CLOSE) -> dict:
    """取 [RANGE] 内某口径的某字段 → {date: value}。**默认收盘价**。"""
    if field not in (F_CLOSE, F_HIGH):
        raise ValueError("只缓存/提供 close 与 high 两个字段（field=%r）" % field)
    slot = "close" if field == F_CLOSE else "high"
    cache = _load_cache()
    key = "%s|%s" % (symbol, fq)
    if key in cache and slot in cache[key]:
        return {d: v for d, v in cache[key][slot].items() if v is not None}

    out = []
    for seg in year_segments(*RANGE):
        out.extend(request_segment(symbol, seg[0], seg[1], fq))
    seen, dedup = set(), []
    for rec in out:
        if rec[F_DATE] in seen:
            continue
        seen.add(rec[F_DATE])
        dedup.append(rec)
    dedup.sort(key=lambda r: r[F_DATE])

    close = {}
    high = {}
    for r in dedup:
        c = _num(r[F_CLOSE])
        h = _num(r[F_HIGH])
        if c is not None:
            close[r[F_DATE]] = c
        if h is not None:
            high[r[F_DATE]] = h
    cache[key] = {"close": close, "high": high}
    _save_cache(cache)
    return close if slot == "close" else high


def affine_fit(xs: list, ys: list):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return None
    k = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den
    c = my - k * mx
    rms = (sum((y - (k * x + c)) ** 2 for x, y in zip(xs, ys)) / n) ** 0.5
    return k, c, rms


def audit_one(conn, sid: str, symbol: str) -> dict:
    R = fetch(symbol, "")
    H = fetch(symbol, "hfq")
    Q = fetch(symbol, "qfq")
    H_high = fetch(symbol, "hfq", F_HIGH)          # 仅用于 field_audit 对照，不参与任何指标
    if not R or not H:
        return {"status": "UNAVAILABLE", "reason": "provider 未返回 raw 或 hfq"}

    dates = sorted(set(R) & set(H) & set(Q))
    # ---- ① 因子稳定性（收盘价）
    steps = [(H[b] / R[b]) / (H[a] / R[a]) - 1.0 for a, b in zip(dates, dates[1:])]
    ss = sorted(steps)
    n = len(ss)
    over = sum(1 for x in steps if abs(x) > 0.0005)
    factor_steps = {
        "n": n, "p50_pct": round(ss[n // 2] * 100, 4),
        "p90_pct": round(ss[int(n * 0.90)] * 100, 4),
        "p99_pct": round(ss[int(n * 0.99)] * 100, 4),
        "max_pct": round(ss[-1] * 100, 4), "min_pct": round(ss[0] * 100, 4),
        "rounding_noise_pct": 0.0001,
        "days_over_0_05pct": over,
        "share_over_0_05pct": round(over / n * 100, 1) if n else None,
    }

    # ---- ② 仿射模型残差随跨度
    spans = {}
    for span in (15, 60, 120, 230):
        vals = []
        for i in range(0, max(1, len(dates) - span), span):
            ds = dates[i:i + span]
            f = affine_fit([R[d] for d in ds], [H[d] for d in ds])
            if f:
                vals.append(f[2])
        spans["%dd" % span] = round(max(vals), 4) if vals else None
    full = affine_fit([R[d] for d in dates], [H[d] for d in dates])

    # ---- ③ 窗口内：因子累计变化 vs 分红步进 vs 送转（负步进）
    inner = [d for d in dates if WINDOW[0] <= d <= WINDOW[1]]
    a, b = inner[0], inner[-1]
    fa, fb = H[a] / R[a], H[b] / R[b]
    w_steps = [(d1, (H[d1] / R[d1]) / (H[d0] / R[d0]) - 1.0)
               for d0, d1 in zip(dates, dates[1:]) if WINDOW[0] <= d1 <= WINDOW[1]]
    div_steps = [{"date": d, "step_pct": round(v * 100, 2)} for d, v in w_steps if v > 0.015]
    split_steps = [{"date": d, "step_pct": round(v * 100, 2)} for d, v in w_steps if v < -0.015]

    def ret(D):
        x, y = D.get(a), D.get(b)
        if x is None or y is None or x <= 0 or y <= 0:
            return None
        return round((y / x - 1.0) * 100, 2)

    window = {
        "window": [a, b],
        "trading_days": len(inner),
        "raw_period_return_pct": ret(R),
        "hfq_period_return_pct": ret(H),
        "qfq_period_return_pct": ret(Q),
        "qfq_non_positive_at_start": Q.get(a) is not None and Q[a] <= 0,
        "factor_at_start": round(fa, 4), "factor_at_end": round(fb, 4),
        "factor_change_pct": round((fb / fa - 1.0) * 100, 2),
        "cash_dividend_steps": div_steps,
        "split_steps": split_steps,
        "dividend_steps_sum_pct": round(sum(x["step_pct"] for x in div_steps), 2),
        "split_steps_sum_pct": round(sum(x["step_pct"] for x in split_steps), 2),
        "all_steps_sum_pct": round(sum(v for _, v in w_steps) * 100, 2),
        # ★ 不可解释漂移 = 因子累计变化 − 已解释步进（现金分红 + 送转）
        "unexplained_drift_pct": round((fb / fa - 1.0) * 100
                                       - sum(x["step_pct"] for x in div_steps)
                                       - sum(x["step_pct"] for x in split_steps), 2),
        "note": "raw = 仅价格（不含分红，**不得**当作含分红收益）；qfq = 前复权（起点非正价格 → 拒绝计算）；"
                "hfq = 后复权（数值可得，但见 verdict）。"
                "★ unexplained_drift_pct = 因子累计变化 − 现金分红步进 − 送转步进；"
                "无送转时它应 ≥ 0（分红只会抬高后复权价），**负值即不可解释**。",
    }

    # ---- ④ 字段自检：close 与 high 必须不同，且收益按 close 复算
    field_audit = {
        "fields": {"date": F_DATE, "open": F_OPEN, "close": F_CLOSE,
                   "high": F_HIGH, "low": F_LOW, "volume": F_VOL},
        "used_for_all_metrics": "close (F_CLOSE = 2)",
        "sample_date": a,
        "close_raw": R[a],
        "hfq_close": H[a],
        "hfq_high_same_date": H_high.get(a),
        "close_ne_high": H_high.get(a) is not None and abs(H[a] - H_high[a]) > 1e-9,
        "return_from_close_pct": ret(H),
        "return_from_high_pct": (round((H_high[b] / H_high[a] - 1.0) * 100, 2)
                                 if H_high.get(a) and H_high.get(b) and H_high[a] > 0 else None),
    }
    field_audit["regression_ok"] = bool(
        field_audit["close_ne_high"]
        and field_audit["return_from_close_pct"] is not None
        and field_audit["return_from_high_pct"] is not None
        and abs(field_audit["return_from_close_pct"] - field_audit["return_from_high_pct"]) > 1e-6)

    neg_qfq = [d for d in dates if Q.get(d) is not None and Q[d] <= 0]
    return {
        "symbol": symbol,
        "range": [dates[0], dates[-1]],
        "trading_days": len(dates),
        "qfq_non_positive_days": len(neg_qfq),
        "qfq_non_positive_range": [neg_qfq[0], neg_qfq[-1]] if neg_qfq else None,
        "hfq_non_positive_days": sum(1 for d in dates if H[d] <= 0),
        "factor_steps": factor_steps,
        "affine_rms_by_span": spans,
        "affine_full_range": {"k": round(full[0], 6), "c": round(full[1], 2),
                              "residual_rms": round(full[2], 4)} if full else None,
        "window_check": window,
        "field_audit": field_audit,
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
            w = s["window_check"]
            print("  %-14s 因子 %+.2f%% · 分红步进 %+.2f%% · 不可解释漂移 %+.2f%% · "
                  "raw %s / hfq %s · 自检 %s"
                  % (sid, w["factor_change_pct"], w["dividend_steps_sum_pct"],
                     w["unexplained_drift_pct"], w["raw_period_return_pct"],
                     w["hfq_period_return_pct"],
                     "OK" if s["field_audit"]["regression_ok"] else "**FAIL**"))
            if not s["field_audit"]["regression_ok"]:
                print("FAIL: 字段自检未通过 —— close 与 high 未能区分，拒绝生成产物")
                return 1
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
        "corrections": [{
            "at": GENERATED_AT,
            "what": "v0.1 用 **high（rec[3]）** 代替收盘价计算了全部统计；"
                    "v0.2 改用 **close（rec[2]）** 并加字段自检",
            "why": "腾讯 fqkline 记录为 [date, open, close, high, low, volume]；"
                   "v0.1 取 r[3] → 实际取的是最高价，注释却写「收盘」",
            "affected": [
                "因子步进分布（p50/p90/p99/max、超阈值天数）",
                "仿射模型残差（按跨度）",
                "三只股票的窗口收益 raw / hfq / qfq",
                "qfq 非正价格的「天数」不受影响（非正与否与取哪个字段无关，区间端点可能差一天）",
            ],
            "recheck": "按 close 重算后：因子仍不恒定（65.9% 的交易日 >0.05%）、"
                       "仿射残差仍不随跨度缩小、hfq 收益仍低于 raw 收益 ⇒ "
                       "**NOT_ADOPTED 的结论不变**，但 v0.1 引用的具体数字**作废**，以 v0.2 为准",
        }],
        "verdict": "NOT_ADOPTED",
        "verdict_basis": {
            "1_available_and_stable": "✓ 可取数、无非正价格、同一交易日跨请求区间取值一致（锚定上市首日）",
            "2_explainable_adjustment_model": "✗ 现金分红步进为正、窗口内因子却**净下降**"
                                              "（−3.21% / −4.13% / −13.95%），且无送转负步进可解释；"
                                              "结果是 hfq 收益**低于** raw 价格收益 —— 任何标准后复权都不可能如此",
            "3_documented_method": "✗ provider 未公开 hfq 算法",
            "4_independently_verifiable": "✗ 缺分红/送转记录，无法由 raw + 公司行为独立复算",
        },
        "what_is_missing": [
            "一份可核验的分红 / 送转记录（除权日 + 每股派息 / 送转比例）——"
            "有了它，总收益可由 raw 与公司行为独立重建并审计；",
            "或换用**复权方法有明文文档**的数据源（当前 provider 未公开其 hfq 算法）。",
        ],
        "rejected_alternatives": {
            "raw": "仅价格、不含分红 → 会把「价格涨幅」冒充「含分红收益」，明令禁止。",
            "hfq": "见 verdict_basis.2；且与默认 qfq 在高分红长窗口下会系统性分叉，混用会破坏事件内可比性。",
            "自建复权因子": "缺少可核验的分红记录，等于自造因子 —— 不采用。",
        },
        "source": {
            "provider": "tencent",
            "endpoint": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
            "params": "fq ∈ {''(raw), 'qfq', 'hfq'}",
            "field_used": "rec[2] = close（★ v0.2 修正；v0.1 误用 rec[3] = high）",
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
