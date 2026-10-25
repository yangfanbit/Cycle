#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_official_index_parallel_v0_1.py —— 半导体地图的官方指数**并列**行情（Wave 2.1）。

## 它做什么

对 `semiconductor_ai_compute_historical_events_v0_6.json` 的**实际事件清单**（当前 7 个，
不硬编码数量），按每个事件**规范字段** `market_performance.window` 计算官方指数的并列行情：

| 项 | 口径（统一，不随事件变） |
|---|---|
| 区间收益 | `末交易日 close / 首交易日 close − 1`（百分点） |
| 基准 | 官方 `000300` 沪深300 同窗口区间收益 |
| 超额 | `H30184 区间收益 − 000300 区间收益`（**pp**） |
| 交易日 | 只取官方序列中**实际存在**的交易日；**不插值、不补造、不缩窗口** |
| 窗口来源 | **只读** `market_performance.window`；缺失即报缺口，**不从 `window_text` 猜** |

## ★★ 授权边界（写进代码，不靠口头约定）

中证官网的接口**公开无 token**，但「可公开访问」≠「许可公开再发布派生数据」。
本轮未找到明确许可 → **默认拒绝**写入 `research/current/`（生产产物），
真实派生数值只写 `.tmp/` 本地实验输出；确需生产写入必须显式 `--i-have-license`
并在产物里带 `license_basis`，否则直接 `REFUSE` 退出。

## 用法

    python research/scripts/build_official_index_parallel_v0_1.py            # 打印（不写）
    python research/scripts/build_official_index_parallel_v0_1.py --write    # 写 .tmp/（本地实验）
    python research/scripts/build_official_index_parallel_v0_1.py --write \
        --out research/current/xxx.json --i-have-license --license-basis "…"  # 仅在许可明确后
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
DEFAULT_OUT = os.path.join(REPO, ".tmp", "official_index_parallel_v0_1.json")

API = ("https://www.csindex.com.cn/csindex-home/perf/index-perf"
       "?indexCode=%s&startDate=%s&endDate=%s")
EVENTS_RE = re.compile(r"semiconductor_ai_compute_historical_events_v0_(\d+)\.json$")

INDEX = {
    "provider": "中证指数有限公司（China Securities Index Co., Ltd.）",
    "index_code": "H30184",
    "index_name": "中证全指半导体产品与设备指数",
    "identity": "OFFICIAL_EXACT",
    "identity_note": ("官方「半导体产品与设备」行业指数（设计/制造/封测/设备/材料全产业链）。"
                      "★ **不是**专门的 AI 算力指数 —— 不得把它的涨跌说成「AI 算力行情」。"),
    "published_from": "2013-07-15",
    "base_date": "2004-12-31",
    "base_value": 1000,
    "price_basis": "官方指数点位（收盘价口径；非前复权股价，无复权概念）",
    "source_url": API % ("H30184", "<startDate>", "<endDate>"),
}
BENCH = {
    "index_code": "000300",
    "index_name": "沪深300指数",
    "published_from": "2005-04-08",
    "base_date": "2004-12-31",
    "base_value": 1000,
    "source_url": API % ("000300", "<startDate>", "<endDate>"),
}

# ★ 授权状态：本轮实测结论，写进产物，避免下游误以为已获许可
LICENSE_STATUS = {
    "state": "UNCLEAR",
    "checked_at": "2026-10-25",
    "finding": ("中证官网数据接口公开可访问、无需 token；但**未找到**允许「公开再发布派生行情数据」的"
                "明确许可声明。按项目边界：公开可访问 ≠ 许可再发布。"),
    "consequence": ("真实派生收益**不写入** `research/current/` 生产产物、**不在**公开页面展示；"
                    "只落 `.tmp/` 本地实验输出，供内部复核。"),
    "to_resolve": "需人工向中证指数确认授权范围（属治理决策，本轮不做）。",
}


# ─────────────────────────── 纯计算（可单测，无网络） ───────────────────────────

def compute_window(series, window):
    """★ 纯函数：只在实际存在的交易日上计算，不插值、不补造。

    series: `[(YYYY-MM-DD, close), ...]` 升序；window: `(start, end)` 或 None。
    返回 dict：成功时含 `period_return_pct`；失败时 `status` + `error`，**数值字段为 None**（不填 0）。
    """
    if not window or len(window) != 2 or not window[0] or not window[1]:
        return {"status": "NO_WINDOW", "error": "事件缺 `market_performance.window`，未从 window_text 猜测",
                "window": None, "period_return_pct": None, "trading_days": 0}
    start, end = window[0], window[1]
    rows = [(d, c) for d, c in series if start <= d <= end and c]
    if len(rows) < 2:
        return {"status": "INSUFFICIENT_TRADING_DAYS",
                "error": "窗口内交易日不足 2 个（实际 %d）→ 不计算，不插值" % len(rows),
                "window": [start, end], "period_return_pct": None, "trading_days": len(rows)}
    first, last = rows[0], rows[-1]
    return {
        "status": "COMPUTED",
        "error": None,
        "window": [start, end],
        "window_actual": {"first_trade_date": first[0], "last_trade_date": last[0],
                          "first_close": first[1], "last_close": last[1],
                          "trading_days": len(rows)},
        "period_return_pct": round((last[1] / first[1] - 1) * 100, 4),
    }


def count_rows_before(series, published_from):
    """★ 由**实际获取的完整序列**计算发布前的行数（不是手写常数）。"""
    return sum(1 for d, _ in series if d < published_from)


def window_touches_backfill(series, window, published_from):
    """★ 事件窗口级标记：窗口内**只要有一个实际交易日**早于发布日期 → True。"""
    if not window:
        return None
    return any(window[0] <= d <= window[1] and d < published_from for d, _ in series)


# ─────────────────────────── 取数 ───────────────────────────

def fetch_series(code, start="20050101", end="20261023"):
    req = urllib.request.Request(API % (code, start, end), headers={
        "User-Agent": "Mozilla/5.0 (ThreeC official-index parallel)",
        "Referer": "https://www.csindex.com.cn/",
    })
    with urllib.request.urlopen(req, timeout=40) as r:
        doc = json.loads(r.read().decode("utf-8"))
    if not doc.get("success"):
        raise SystemExit("FAIL: 中证接口返回失败：%s" % doc.get("msg"))
    out = []
    for x in doc.get("data") or []:
        d = x["tradeDate"]
        out.append(("%s-%s-%s" % (d[:4], d[4:6], d[6:]), x.get("close")))
    out.sort(key=lambda r: r[0])
    return out


def latest_events_path():
    hits = [(int(EVENTS_RE.match(f).group(1)), f) for f in os.listdir(CURRENT) if EVENTS_RE.match(f)]
    if not hits:
        raise SystemExit("FAIL: 找不到 semiconductor_ai_compute_historical_events 产物")
    return os.path.join(CURRENT, sorted(hits)[-1][1])


# ─────────────────────────── 组装 ───────────────────────────

def build(events_doc, idx_series, bench_series):
    entries = []
    for e in events_doc["events"]:
        eid = e["event_id"]
        window = (e.get("market_performance") or {}).get("window")
        idx_w = compute_window(idx_series, window)
        bmk_w = compute_window(bench_series, window)

        backfilled = window_touches_backfill(idx_series, window, INDEX["published_from"])
        ok = idx_w["status"] == "COMPUTED" and bmk_w["status"] == "COMPUTED"
        item = {
            "event_id": eid,
            "provider": INDEX["provider"],
            "index_code": INDEX["index_code"],
            "index_name": INDEX["index_name"],
            "identity": INDEX["identity"],
            "identity_note": INDEX["identity_note"],
            "published_from": INDEX["published_from"],
            "base_date": INDEX["base_date"],
            "base_value": INDEX["base_value"],
            "source_first_date": idx_series[0][0],
            "source_last_date": idx_series[-1][0],
            # ★ 由实际序列计算，非手写常数
            "rows_before_publish": count_rows_before(idx_series, INDEX["published_from"]),
            # ★ 窗口级：窗口内是否含发布前的数据点（None = 无窗口，不得当 false）
            "backfilled": backfilled,
            "window": idx_w["window"],
            "window_actual": idx_w.get("window_actual"),
            "period_return_pct": idx_w["period_return_pct"],
            "benchmark_index_code": BENCH["index_code"],
            "benchmark_index_name": BENCH["index_name"],
            "benchmark_return_pct": bmk_w["period_return_pct"],
            "excess_period_pp": (round(idx_w["period_return_pct"] - bmk_w["period_return_pct"], 4)
                                 if ok else None),
            "price_basis": INDEX["price_basis"],
            "source_url": INDEX["source_url"],
            "benchmark_source_url": BENCH["source_url"],
            "status": "COMPUTED" if ok else "INCOMPLETE",
            "error": None if ok else "；".join(
                x for x in (idx_w.get("error"), bmk_w.get("error")) if x),
            "calculation_note": (
                "区间收益 = 末交易日 close / 首交易日 close − 1；"
                "基准 = 官方 000300 同窗口区间收益；超额 = 本指数 − 基准（pp）。"
                "★ 首尾收盘口径：两端都取**窗口内实际存在的第一个/最后一个交易日**的官方收盘点位，"
                "不含窗口前一日的涨跌；窗口首末若为非交易日，自动落到最近的实际交易日，**不插值**。"
                "★ 该指数是官方**半导体产品与设备**行业指数，不是 AI 算力专用指数。"
                "★ 历史成分名单不可得，本对象**不含**任何成分信息。"),
        }
        # ★ 缺失的强制字段显式报缺口，不静默填 0 / false
        missing = [k for k in ("period_return_pct", "benchmark_return_pct", "excess_period_pp",
                               "backfilled", "rows_before_publish", "window")
                   if item.get(k) is None]
        if missing:
            item["missing_required_fields"] = missing
        entries.append(item)
    return entries


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--i-have-license", action="store_true",
                    help="仅在**已确认**可公开再发布中证派生数据时使用")
    ap.add_argument("--license-basis", default="")
    a = ap.parse_args(argv)

    out_abs = os.path.abspath(a.out)
    under_current = os.path.commonpath([out_abs, CURRENT]) == CURRENT
    if under_current and not a.i_have_license:
        print("REFUSE: 目标是生产目录 `research/current/`，但授权状态 = %s。" % LICENSE_STATUS["state"])
        print("        %s" % LICENSE_STATUS["finding"])
        print("        真实派生数值只写本地实验输出（默认 `.tmp/`）。")
        print("        确需生产写入：加 `--i-have-license --license-basis \"<依据与链接>\"`。")
        return 2

    ev_path = latest_events_path()
    events_doc = json.loads(io.open(ev_path, encoding="utf-8").read())
    idx_series = fetch_series("H30184")
    bench_series = fetch_series("000300")
    entries = build(events_doc, idx_series, bench_series)

    n_ok = sum(1 for x in entries if x["status"] == "COMPUTED")
    print("事件源：%s（%d 个事件）" % (os.path.basename(ev_path), len(events_doc["events"])))
    print("官方序列：%s %s→%s（%d 行，发布前 %d 行）"
          % (INDEX["index_code"], idx_series[0][0], idx_series[-1][0], len(idx_series),
             count_rows_before(idx_series, INDEX["published_from"])))
    print("计算完成：%d / %d" % (n_ok, len(entries)))
    for x in entries:
        if x["status"] == "COMPUTED":
            print("  %-30s %s~%s 收益 %+7.2f%% 基准 %+7.2f%% 超额 %+7.2fpp backfilled=%s"
                  % (x["event_id"], x["window"][0], x["window"][1], x["period_return_pct"],
                     x["benchmark_return_pct"], x["excess_period_pp"], x["backfilled"]))
        else:
            print("  %-30s 缺口：%s" % (x["event_id"], x["error"]))

    doc = {
        "artifact": "official_index_parallel",
        "artifact_version": "0.1",
        "generated_by": "research/scripts/build_official_index_parallel_v0_1.py",
        "index": {k: INDEX[k] for k in ("provider", "index_code", "index_name", "identity",
                                       "identity_note", "published_from", "base_date",
                                       "base_value", "price_basis")},
        "benchmark": BENCH,
        "license": LICENSE_STATUS,
        "events_source": {"file": os.path.basename(ev_path),
                          "events": len(events_doc["events"])},
        "events": entries,
        "summary": {"events": len(entries), "computed": n_ok,
                    "gaps": [x["event_id"] for x in entries if x["status"] != "COMPUTED"],
                    "windows_with_backfill": [x["event_id"] for x in entries if x["backfilled"]],
                    "note": "★ 本文件是**本地实验输出**，未提交到仓库；授权明确前不进入生产产物。"},
    }
    body = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"

    if a.write:
        os.makedirs(os.path.dirname(out_abs), exist_ok=True)
        io.open(out_abs, "w", encoding="utf-8", newline="\n").write(body)
        print("\n已写 %s（%.1f KB）%s" % (
            os.path.relpath(out_abs, REPO), len(body.encode()) / 1024.0,
            "" if under_current else "（本地实验输出，不入库）"))
        if under_current:
            print("★ 生产写入已启用，license_basis = %r" % a.license_basis)
    else:
        print("\n（未写盘；加 --write 输出到 .tmp/）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
