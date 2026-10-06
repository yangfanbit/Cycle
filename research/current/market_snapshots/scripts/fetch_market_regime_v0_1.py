#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""fetch_market_regime_v0_1.py —— 从东方财富 EOD 行情计算 market_regime 维度（ThreeC 1.1 Phase 1.4）。

## 为什么需要
`MARKET_REGIME_AI_INTERFACE_v0.1.md` §2.2–2.5 的规则**要求指标序列**（20 / 60 交易日窗口）。
靠「媒体转述的离散事实」无法满足 —— 首轮实测就因此把 `broad_index_state` 判成了 `FLAT`
（用上证综指替代缺失的沪深300），而真实主标的是 **-5.50% → DOWN**。

本脚本按用户提供的路径（**东方财富行情**）拉取 **EOD 日线**，让规则可以真正被满足。

## ★ 边界（不得违反）
- **只在 Research 侧离线运行**；Product 运行时不联网（静态 PWA 不变）。
- 拉的是 **EOD 日线**（收盘后数据），**不是实时行情**、不做资金异动监控。
- 只输出「建议值 + 证据」，**不写快照**、不签发、不改任何既有 artifact。
- 计算口径与 `MARKET_REGIME_AI_INTERFACE_v0.1.md` §2 完全一致；口径不足时**如实降级**。

## 用法（在仓库根执行）
    python research/current/market_snapshots/scripts/fetch_market_regime_v0_1.py \
        --as-of 2026-09-30 --out /tmp/regime_suggest.json

退出码: 0 = 成功；1 = 失败（含窗口不足导致无法计算）。

## ⚠️ 已知环境限制
本沙箱（WorkBuddy）**直连 push2his.eastmoney.com 会被断连**（首个请求成功后持续 RemoteDisconnected）。
在**本机**运行通常正常。若被限流，请加大 `--sleep` 或稍后重试。
本次用于 Phase 1.4 的数值是经另一条网络路径取到同一接口的数据后计算的，已逐条留痕在
`market_regime/2026-10.json` 的 evidence 中。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request

HOST = "https://push2his.eastmoney.com/api/qt/stock/kline/get"

# secid 约定：1 = 上交所，0 = 深交所
SECID_HS300 = "1.000300"   # 沪深300 —— broad_index_state 的**主标的**
SECID_SSE = "1.000001"     # 上证综指（沪市全部）—— 两市成交额的沪市部分
SECID_SZSE = "0.399106"    # 深证综指（深市全部）—— 两市成交额的深市部分

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"


def fetch_kline(secid: str, beg: str, end: str, sleep: float = 1.0, tries: int = 4):
    """拉取 EOD 日线。返回 [(date, close, amount), ...]（amount 单位：元）。"""
    url = ("%s?secid=%s&fields1=f1,f2&fields2=f51,f52,f53,f54,f55,f56,f57"
           "&klt=101&fqt=1&beg=%s&end=%s" % (HOST, secid, beg, end))
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                       "Referer": "https://quote.eastmoney.com/"})
            with urllib.request.urlopen(req, timeout=20) as r:
                doc = json.loads(r.read().decode("utf-8"))
            data = doc.get("data") or {}
            rows = []
            for k in data.get("klines") or []:
                p = k.split(",")
                rows.append((p[0], float(p[2]), float(p[6])))
            return data.get("name"), rows
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(sleep * (i + 1))
    raise last  # type: ignore[misc]


def band(value: float, up: float, down: float) -> str:
    if value >= up:
        return "UP"
    if value <= down:
        return "DOWN"
    return "FLAT"


def main() -> int:
    ap = argparse.ArgumentParser(description="东方财富 EOD → market_regime 维度计算")
    ap.add_argument("--as-of", required=True, help="快照日 YYYY-MM-DD（取其前最后一个交易日为右端点）")
    ap.add_argument("--lookback-days", type=int, default=140, help="回溯自然日数（覆盖 60 交易日）")
    ap.add_argument("--sleep", type=float, default=1.0, help="请求间隔秒（防限流）")
    ap.add_argument("--out", default=None, help="输出建议 JSON（不写则只打印）")
    args = ap.parse_args()

    from datetime import date, timedelta
    end = args.as_of.replace("-", "")
    y, m, d = (int(x) for x in args.as_of.split("-"))
    beg = (date(y, m, d) - timedelta(days=args.lookback_days)).strftime("%Y%m%d")

    try:
        n1, hs300 = fetch_kline(SECID_HS300, beg, end, args.sleep)
        time.sleep(args.sleep)
        n2, sse = fetch_kline(SECID_SSE, beg, end, args.sleep)
        time.sleep(args.sleep)
        n3, szse = fetch_kline(SECID_SZSE, beg, end, args.sleep)
    except Exception as e:  # noqa: BLE001
        print("FAIL  行情拉取失败: %s: %s" % (type(e).__name__, e))
        print("      若为 RemoteDisconnected，多为限流；请加大 --sleep 或稍后重试。")
        return 1

    if len(hs300) < 21:
        print("FAIL  沪深300 交易日不足 21（得到 %d）—— 无法计算近 20 交易日区间" % len(hs300))
        return 1

    # ---- broad_index_state：沪深300 近 20 交易日区间涨跌 ----
    last_close = hs300[-1][1]
    base20 = hs300[-21][1]
    chg20 = (last_close / base20 - 1.0) * 100.0
    broad = band(chg20, 5.0, -5.0)

    # ---- liquidity_state：两市日均成交额 近20日 vs 近60日 ----
    by_date = {r[0]: r[2] for r in sse}
    for r in szse:
        by_date[r[0]] = by_date.get(r[0], 0.0) + r[2]
    days = sorted(by_date)
    tot = [by_date[k] for k in days]
    liq = None
    liq_note = None
    if len(tot) >= 60:
        avg20 = sum(tot[-20:]) / 20
        avg60 = sum(tot[-60:]) / 60
        rel = (avg20 / avg60 - 1.0) * 100.0
        liq = "EXPANDING" if rel >= 15 else ("CONTRACTING" if rel <= -15 else "STABLE")
        liq_note = "近20日均值 %.0f 亿 · 近60日均值 %.0f 亿 → %+.1f%%（%d 个交易日）" % (
            avg20 / 1e8, avg60 / 1e8, rel, len(tot))
    else:
        liq = "UNKNOWN"
        liq_note = ("★ 窗口不足：仅有 %d 个交易日，规则要求 60 —— 按契约「数据不可得 → UNKNOWN」，"
                    "**不以更短窗口替代**。" % len(tot))

    out = {
        "contract": "market_regime_suggestion",
        "suggestion_version": "0.1",
        "as_of": args.as_of,
        "right_endpoint": hs300[-1][0],
        "computed": {
            "broad_index_state": {
                "value": broad,
                "metric": "沪深300 近 20 交易日区间涨跌",
                "value_text": "%.2f / %.2f − 1 = %+.2f%%" % (last_close, base20, chg20),
                "window": "%s ~ %s（20 个交易日）" % (hs300[-21][0], hs300[-1][0]),
                "source_tier": "T2",
            },
            "liquidity_state": {
                "value": liq,
                "metric": "两市日均成交额 近20日 vs 近60日",
                "value_text": liq_note,
                "source_tier": "T2",
            },
        },
        "not_computed": {
            "breadth_state": "东方财富 EOD K线不含「全市场涨跌家数」序列 → 需另行取数或按诚实空态 UNKNOWN",
            "risk_appetite_state": "需 ≥2 个独立信号（如高低β相对表现、涨停家数），本脚本未覆盖",
        },
        "sources": {"hs300": n1, "sse": n2, "szse": n3},
    }

    text = json.dumps(out, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print("已写出建议: %s" % args.out)
    print(text)
    print("\n★ 建议值仅供人工审核；本脚本不写快照、不签发、不改任何 artifact。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
