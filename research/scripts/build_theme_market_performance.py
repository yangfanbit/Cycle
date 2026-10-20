#!/usr/bin/env python3
"""build_theme_market_performance.py —— 题材事件地图的**行情转写**与**漂移校验**。

## 为什么存在这个脚本（v0.24）

历史题材地图的 `market_performance` 此前是**逐份手写**的：同一批字段在不同题材文件里
由不同轮次、不同临时查询算出，**口径没有写下来**。后果（v0.23 实测）：

- 拿「全窗口最大回撤」去验算，12 份题材文档里**只有 3 份**能复现；
- 于是既不敢改、也无法证明「没改错」——行情数据库补齐后，地图仍停在「不覆盖」的旧状态。

本脚本把口径**写成代码 + 写进产物**，并提供唯一入口：
**从恢复后的 `market_data.db` 重算 → 与已发布 JSON 逐字段比对**。

## 计算合同 `theme_market_performance_v1`（★ 唯一权威定义）

| 项 | 定义 |
|---|---|
| 价格序列 | `market_daily.price_type = 'adjusted'`，取 **`adj_close`**（前复权收盘）。**不混用 raw**。 |
| 窗口 | `event.market_performance.window = [start, end]`，**双端包含**：`trade_date BETWEEN start AND end`。 |
| 交易日数 | 窗口内该序列的**实际行数**（`trading_days`）。**不是**日历天数、**不是**基准交易日数。 |
| `first` / `last` | 窗口内**第一条 / 最后一条**记录的 `(trade_date, adj_close)`。端点不是交易日时自然落到最近的交易日。 |
| `high` | 窗口内 **adj_close 的最大值**，取**首次**出现的日期。★ 不是 `high` 列（日内最高价），也不是 Campaign 的 `peak_date`。 |
| `low` | 窗口内 adj_close 的最小值（首次出现）。 |
| `period_return_pct` | `(last.close / first.close - 1) × 100` |
| `to_high_pct` | `(high.close / first.close - 1) × 100` |
| `max_drawdown_from_high_pct` | ★★ **自窗口最高收盘价「之后」的最大回撤**：`min over t >= high.date of (close_t / high.close - 1) × 100`（≤ 0）。**不是**全窗口最大回撤 —— 这正是 v0.23「只有 3/12 可复现」的根因：用全窗口回撤去验算，会把「至高点之前」的下跌也算进去。 |
| 基准 | `SH000300`，**同窗口、同价格口径**。`excess_period_pp = period_return_pct − bench.period_return_pct`；`excess_to_high_pp = to_high_pct − bench.to_high_pct`（**两列口径不同，不得混用**）。 |
| 舍入 | 所有百分比 **1 位小数**（Python `round`，即 IEEE754 下的银行家舍入；实测与既有文件一致）。超额由**已舍入**的两个百分比相减后再舍入。 |
| 缺失 | 窗口内 < 2 行 → `{"error": "insufficient_data_in_window", "reason": ...}`。**绝不用 0 / 相邻日期 / 推测值代替**。`reason` 取值：`no_series`（库内无该序列）· `no_rows_in_window`（序列存在但窗口内无行）· `single_row`（只有 1 行）。 |
| 非正价格 | ★ 窗口内任一条 `adj_close <= 0` → `{"error": "invalid_price_series", "reason": "non_positive_adj_close"}`。**不得**用负价算收益率（上游 qfq 按除权价差计算，高分红个股在早年会出现负价 —— 这是**数据源方法学限制**，不是抓取错误）。 |
| 序列不连续 | ★ 窗口内任一对相邻交易日 `abs(close_t/close_{t-1} - 1) > 0.45` → `{"error": "invalid_price_series", "reason": "discontinuous_series"}`（A 股单日涨跌幅上限 ≤30%；qfq 已消除除权跳空）。 |

★ 合同**不**推断因果：价格结果 ≠ 题材机制成功。所有 `market_performance` 都带
`is_campaign_ruling: false`，且 Beta Contamination（同期全市场涨跌）必须在 `known_gaps` 里明写。

## 用法

```bash
# 只读校验（CI 门禁用）：不写任何文件；有偏差 → 非零退出
python research/scripts/build_theme_market_performance.py --check

# 生成新版本（★ 永不覆盖旧文件；同时把索引指向新文件）
python research/scripts/build_theme_market_performance.py --write SEMICONDUCTOR_AI

# 只生成到指定路径（确定性验证 / 草稿），不动索引
python research/scripts/build_theme_market_performance.py --write SEMICONDUCTOR_AI --out /tmp/a.json
```

前置条件：`research/database/market_data.db` 已由**被跟踪的便携快照**恢复
（`python research/scripts/restore_market_data.py --apply`）。缺失 → **明确失败**，不静默跳过。

## 退出码

`0` 一致 / 生成成功 · `1` 存在漂移或生成失败 · `2` 用法错误
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                 # <repo>/research
REPO = os.path.dirname(ROOT)                 # <repo>
CURRENT_DIR = os.path.join(ROOT, "current")
INDEX_PATH = os.path.join(CURRENT_DIR, "historical_event_maps_index.json")
MARKET_DB = os.path.join(ROOT, "database", "market_data.db")
RESTORE_CMD = "python research/scripts/restore_market_data.py --apply"

# ---------------------------------------------------------------- 合同常量
CONTRACT_VERSION = "theme_market_performance_v2"
PRICE_TYPE = "adjusted"
BENCHMARK_ID = "SH000300"
DECIMALS = 1
# ★ 容差 = 1 位小数的半个单位（0.05）+ 浮点余量。既容纳「文件写 2 位小数」的旧文件
#   （如 power v0_3 的 26.27 vs 合同值 26.3），也足以拦住任何真实错误（测试用 +5pp 注入）。
TOLERANCE_PP = 0.051
TOLERANCE_PRICE = 0.0051
GENERATED_AT = "2026-10-20"                  # ★ 固定值 → 生成结果可复现（不取 now()）

# ★ 行情缺口行的机器可识别前缀：只有带此前缀的 `known_gaps` 由本脚本负责重写。
#   人类写的 Beta Contamination 等条目**原样保留**（本脚本不发明研究结论）。
AUTO_GAP_PREFIX = "[AUTO:MARKET_DATA]"

# ★ UNAVAILABLE 的逐类原因措辞（v0.25 修：不得把「有序列但价格为负」写成「库内无登记」）
UNAVAILABLE_REASON_TEXT = {
    "no_series": "库内无该证券的行情序列",
    "no_rows_in_window": "序列存在，但本窗口内无交易日（上市 / 序列起始晚于窗口）",
    "single_row": "本窗口内只有 1 个交易日，不足以计算",
    "non_positive_adj_close": ("上游前复权（qfq）按除权价差计算，早年高分红段出现"
                               "**非正价格**（分红累计超过当时股价），按合同不用于算收益率"),
    "discontinuous_series": ("窗口内出现 **>45% 的单日跳变**且 **raw 口径同步跳变**"
                             " → 价格变化确实发生（A 股单日涨跌幅上限 ≤30%）"),
    "series_gap": ("窗口内相邻两条记录之间**缺了交易日**（记录缺口，非单日变化）"
                   "—— 跨缺口算收益不是「窗口收益」，按合同拒绝"),
    "qfq_method_artifact": ("窗口内出现 **>45% 的单日跳变**但 **raw 口径不同步**"
                            " → 上游 qfq「除权价差」法的**方法学产物**，非真实价格变化"
                            "（v0.27 全库实证：222 次中 219 次属此类）"),
    "unknown": "原因未标注（应补 reason）",
}

# 与 Product 侧 `marketDataCoverage()` 对齐的判定常量（改动必须两边同时改 + 测试）
COVERAGE_RATIO = 0.6
ENDPOINT_TOLERANCE_TRADING_DAYS = 5

# ---------------------------------------------------------------- 价格基准（v0.27）

# ★ 每个标的块显式声明价格基准。当前**只有一种**：adjusted_qfq（前复权收盘）。
#   ★ v0.27 曾评估 hfq（后复权）作为早年高分红段的替代基准，**未采用**
#     —— 逐日复权因子并非常数（±0.15% 常态 / 除权日 +1.53%），复权约定无法从数据解释、
#       收益无法独立核验。审计过程见 `research/research/reports/hfq_basis_audit_v0_1.json`。
PRICE_BASIS_DEFAULT = "adjusted_qfq"


# ---------------------------------------------------------------- 行情读取

def open_market_ro() -> sqlite3.Connection:
    """只读打开行情库。★ 不存在 → 明确失败（不静默返回空）。"""
    if not os.path.exists(MARKET_DB):
        raise SystemExit(
            "FAIL: 行情数据库不存在：%s\n"
            "      ★ 请先恢复（无网络即可）：%s" % (MARKET_DB, RESTORE_CMD))
    conn = sqlite3.connect("file:%s?mode=ro" % MARKET_DB, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def series_span(conn, sid: str):
    """序列全量范围：(min_date, max_date, rows)；无该序列 → None。"""
    r = conn.execute(
        "SELECT MIN(trade_date), MAX(trade_date), COUNT(*) FROM market_daily "
        "WHERE series_id=? AND price_type=? AND adj_close IS NOT NULL",
        (sid, PRICE_TYPE)).fetchone()
    if not r or r[2] == 0:
        return None
    return r[0], r[1], r[2]


def window_rows(conn, sid: str, start: str, end: str):
    return conn.execute(
        "SELECT trade_date, adj_close FROM market_daily "
        "WHERE series_id=? AND price_type=? AND adj_close IS NOT NULL "
        "AND trade_date BETWEEN ? AND ? ORDER BY trade_date",
        (sid, PRICE_TYPE, start, end)).fetchall()


def _series_span_text(conn, sid: str) -> str:
    span = series_span(conn, sid)
    if span is None:
        return "库内无该序列"
    return "%s → %s，%d 行" % span


# ---------------------------------------------------------------- 指标计算

def _pct(x: float) -> float:
    return round(x, DECIMALS)


def adjacent_trading_days(conn, d0: str, d1: str) -> bool:
    """d0 与 d1 是否为**相邻交易日**（日历上两者之间没有别的交易日）。

    ★ v0.27 实证：库内存在跨 14–1095 个交易日的**记录缺口**（如建投能源
    2017-08-31 → 2022-01-04）。`LAG` 会把这类两条记录当成「相邻日」，
    于是把「跨四年的价格变化」误读成「单日 -60% 跳变」。
    """
    a = conn.execute("SELECT COUNT(*) FROM trading_calendar WHERE trade_date > ? AND trade_date < ?",
                     (d0, d1)).fetchone()[0]
    return a == 0


def raw_jump_corroborates(conn, sid: str, prev_date: str, date: str) -> bool:
    """★ v0.27 实证分类：raw 口径在**同一对相邻交易日**是否也有 >45% 跳变。

    全库扫描结论（v0.27）：adjusted 上 >45% 的跳变共 222 次，其中 **219 次 raw 不同步**
    —— 那是 provider qfq「除权价差」法的**方法学产物**（价格被打到 0 附近再继续累计），
    不是真的价格变化；raw 同步的仅 3 次（建投能源 2022-01-04、锦江酒店 2024-05-06、
    盐湖股份 2021-08-10）—— 价格变化确实发生。
    ⇒ 同一阈值下必须**分开归类**，不能把复权缺陷说成「序列不连续」。
    """
    r = conn.execute(
        "SELECT a.close AS c0, b.close AS c1 FROM market_daily a JOIN market_daily b "
        "ON b.series_id=a.series_id AND b.price_type='raw' "
        "WHERE a.series_id=? AND a.price_type='raw' AND a.trade_date=? AND b.trade_date=?",
        (sid, prev_date, date)).fetchone()
    if not r or r["c0"] is None or r["c1"] is None or r["c0"] <= 0:
        return False
    return abs(r["c1"] / r["c0"] - 1.0) > 0.45


def compute_raw(conn, sid: str, start: str, end: str) -> dict:
    """按 `theme_market_performance_v1` 计算单个序列在窗口内的**未舍入**指标。

    缺失 → `{"error": ..., "reason": ...}`（**不补 0、不借相邻日期**）。
    价格基准：默认 `adjusted_qfq`；登记在 `hfq_price_basis_v0_1.json` 的证券用 `hfq`
    （产物自带 `price_basis` 声明，**不**混用两种口径）。
    """
    basis = PRICE_BASIS_DEFAULT
    rows = [(r["trade_date"], r["adj_close"]) for r in window_rows(conn, sid, start, end)]
    if len(rows) < 2:
        if series_span(conn, sid) is None:
            reason = "no_series"
        elif not rows:
            reason = "no_rows_in_window"
        else:
            reason = "single_row"
        return {"error": "insufficient_data_in_window", "reason": reason,
                "price_basis": basis}

    dates = [r[0] for r in rows]
    closes = [r[1] for r in rows]
    # ★★ 非正价格 → 明确失败（负价算收益率会产生 +1000% 级假数）
    if any(c <= 0 for c in closes):
        return {"error": "invalid_price_series", "reason": "non_positive_adj_close",
                "price_basis": basis}
    # ★★ 相邻两条记录之间的跳变 → 拒绝计算，但**按证据分类**（v0.27 全库实证）
    #   全库 222 次 >45%「跳变」的实测分布：
    #     217 次 = 相邻交易日、raw 不同步 → provider qfq 方法学产物（非真实价格变化）
    #       5 次 = 跨 14–1095 个交易日的**记录缺口** → 根本不是单日变化
    #       0 次 = 真实单日 >45% 波动
    #   ★ 缺口只用来**给超阈值的跳变定性**，不否决「含缺口的窗口」——
    #     窗口收益只看首末收盘，中间缺几天不影响首末比值（如 SGMC 覆盖 96.5%、+802.9% 合法）。
    for (d0, a), (d1, b) in zip(zip(dates, closes), zip(dates[1:], closes[1:])):
        if a > 0 and abs(b / a - 1.0) > 0.45:
            if not adjacent_trading_days(conn, d0, d1):
                reason = "series_gap"                  # ★ 跨缺口的「跳变」不是单日变化
            elif raw_jump_corroborates(conn, sid, d0, d1):
                reason = "discontinuous_series"        # ★ 价格变化确实发生（raw 同步）
            else:
                reason = "qfq_method_artifact"         # ★ 复权口径产物（raw 不同步）
            return {"error": "invalid_price_series", "reason": reason,
                    "price_basis": basis, "at": d1}
    high_i = closes.index(max(closes))            # ★ 首次出现
    low_i = closes.index(min(closes))
    hi = closes[high_i]

    # ★★ 自至高点「之后」的最大回撤（不是全窗口回撤）
    mdd = min(c / hi - 1.0 for c in closes[high_i:])

    return {
        "trading_days": len(rows),
        "first": {"date": dates[0], "close": closes[0]},
        "last": {"date": dates[-1], "close": closes[-1]},
        "high": {"date": dates[high_i], "close": hi},
        "low": {"date": dates[low_i], "close": closes[low_i]},
        "period": (closes[-1] / closes[0] - 1.0) * 100.0,
        "to_high": (hi / closes[0] - 1.0) * 100.0,
        "mdd": mdd * 100.0,
        "price_basis": basis,
    }


def finalize(raw: dict, bench_raw: dict | None = None) -> dict:
    """把未舍入指标变成**写进产物**的形态（1 位小数 + 两列超额 + 价格基准声明）。"""
    if "error" in raw:
        out = {"error": raw["error"], "reason": raw["reason"],
               "price_basis": raw.get("price_basis", PRICE_BASIS_DEFAULT)}
        if "at" in raw:
            out["at"] = raw["at"]
        return out
    out = {
        "price_basis": raw.get("price_basis", PRICE_BASIS_DEFAULT),
        "trading_days": raw["trading_days"],
        "first": raw["first"],
        "last": raw["last"],
        "high": raw["high"],
        "low": raw["low"],
        "period_return_pct": _pct(raw["period"]),
        "to_high_pct": _pct(raw["to_high"]),
        "max_drawdown_from_high_pct": _pct(raw["mdd"]),
    }
    if bench_raw is not None and "error" not in bench_raw:
        # ★ 生成统一用「先舍入再相减」：读者能用页面上的两个数手算核对。
        out["excess_period_pp"] = round(out["period_return_pct"]
                                        - _pct(bench_raw["period"]), DECIMALS)
        out["excess_to_high_pp"] = round(out["to_high_pct"]
                                         - _pct(bench_raw["to_high"]), DECIMALS)
    return out


def alt_excess(raw: dict, bench_raw: dict) -> tuple:
    """另一种**等价**写法：先相减再舍入（既有文件混用过两种，差 ≤ 0.1pp）。"""
    return (round(raw["period"] - bench_raw["period"], DECIMALS),
            round(raw["to_high"] - bench_raw["to_high"], DECIMALS))


def compute_window(conn, sid: str, start: str, end: str) -> dict:
    """便捷包装：单序列（无超额）。"""
    return finalize(compute_raw(conn, sid, start, end))


def _as_point(v):
    """兼容两种既有写法：`high: {date, close}` 与 `high_date` + `high_close`。"""
    if isinstance(v, dict):
        return v
    return None


def _point_of(block: dict, name: str):
    nested = _as_point(block.get(name))
    if nested:
        return nested.get("date"), nested.get("close")
    if name == "high":
        return block.get("high_date"), block.get("high_close")
    return None, None


def _with_excess(block: dict, bench: dict) -> dict:
    """在已算好的个股块上补两列超额（★ 由**已舍入**的百分比相减）。"""
    if "error" in block or "error" in bench:
        return block
    out = dict(block)
    out["excess_period_pp"] = round(block["period_return_pct"] - bench["period_return_pct"], DECIMALS)
    out["excess_to_high_pp"] = round(block["to_high_pct"] - bench["to_high_pct"], DECIMALS)
    return out


def _bench_of(mp: dict) -> dict:
    return (mp.get("benchmark") or {}).get(BENCHMARK_ID) or {}


# ---------------------------------------------------------------- 覆盖状态（与 Product 同规则）

def _shift_weekdays(iso: str, n: int):
    """按**工作日**平移（跳过周六日）—— 与 Product `shiftTradingDays()` 完全一致。"""
    try:
        d = _dt.date.fromisoformat(iso)
    except (ValueError, TypeError):
        return None
    step = -1 if n < 0 else 1
    remaining = abs(n)
    while remaining > 0:
        d = d + _dt.timedelta(days=step)
        if d.weekday() < 5:
            remaining -= 1
    return d.isoformat()


def coverage_status(event: dict, sid: str, expected_bench: dict) -> str:
    """★★ 与 Product `marketDataCoverage()` 同规则（COMPUTED / NOT_COMPUTED / UNAVAILABLE / INSUFFICIENT）。"""
    mp = event.get("market_performance") or {}
    by = mp.get("by_security") or {}
    st = by.get(sid)
    bench = (mp.get("benchmark") or {}).get(BENCHMARK_ID) or {}
    window_days = bench.get("trading_days") or 0
    if not window_days:
        window_days = max([v.get("trading_days") or 0 for v in by.values()] or [0])

    part = next((p for p in event.get("participants") or [] if p.get("security_id") == sid), None)
    unavailable_text = bool(part and part.get("market_data")
                            and ("无登记" in part["market_data"] or "无行情" in part["market_data"]))

    if not st:
        return "UNAVAILABLE" if unavailable_text else "NOT_COMPUTED"

    td = st.get("trading_days") or 0
    if st.get("status") == "NO_DATA" or td <= 0 or st.get("period_return_pct") is None:
        return "UNAVAILABLE"

    ratio = (td / window_days) if window_days else 0.0
    w = mp.get("window") or [None, None]
    b_first = (bench.get("first") or {}).get("date")
    b_last = (bench.get("last") or {}).get("date")
    start = w[0] or b_first
    end = w[1] or b_last
    if b_first and start and b_first > start:
        start = b_first
    if b_last and end and b_last < end:
        end = b_last

    first_d = (st.get("first") or {}).get("date")
    last_d = (st.get("last") or {}).get("date")
    endpoints_ok = True
    if start and end and first_d and last_d:
        lo = _shift_weekdays(start, ENDPOINT_TOLERANCE_TRADING_DAYS)
        hi = _shift_weekdays(end, -ENDPOINT_TOLERANCE_TRADING_DAYS)
        if lo and first_d > lo:
            endpoints_ok = False
        if hi and last_d < hi:
            endpoints_ok = False

    if ratio < COVERAGE_RATIO or not endpoints_ok:
        return "INSUFFICIENT"
    return "COMPUTED"


def event_study_state(event: dict, expected_bench: dict) -> str:
    """与 Product `eventStudyState()` 同规则。"""
    parts = [p for p in (event.get("participants") or [])
             if p.get("category") not in ("COUNTER_EXAMPLE", "INSUFFICIENT")]
    if not event.get("participants") or not event.get("catalysts"):
        return "NOT_VERIFIED"
    statuses = [coverage_status(event, p["security_id"], expected_bench) for p in parts]
    if "COMPUTED" in statuses:
        return "HAS_PRICE_DATA"
    if "INSUFFICIENT" in statuses:
        return "INSUFFICIENT_COVERAGE"
    if "NOT_COMPUTED" in statuses:
        return "NOT_COMPUTED"
    return "NO_PRICE_DATA"


# ---------------------------------------------------------------- 转写

def coverage_text(conn, sid: str, start: str, end: str) -> str:
    """参与者 `market_data` 的规范文案（**只描述实况**）。

    """
    span = series_span(conn, sid)
    if span is None:
        return "库内无该证券日线登记（无行情）"
    mn, mx, total = span
    n = len(window_rows(conn, sid, start, end))
    if n == 0:
        return "库内行情不覆盖该窗口（series %s → %s；本窗口 0 个交易日）" % (mn, mx)
    return "%s~%s（%d 行）；本窗口 %d 个交易日" % (mn, mx, total, n)


def auto_gap_lines(event: dict, doc: dict, conn, window) -> list:
    """按当前覆盖状况生成 `[AUTO:MARKET_DATA]` 行。

    ★ 只描述计数与缺失，**逐类写原因**：四种不可得是不同性质的缺口，
    混成一句「库内无登记或无窗口数据」会把「库内有序列但价格为负」说成「没有数据」
    （v0.25 实机复核发现并修复的措辞漂移）。
    """
    parts = [p for p in (event.get("participants") or [])
             if p.get("category") not in ("COUNTER_EXAMPLE", "INSUFFICIENT")]
    if not parts or not window:
        return []
    statuses = {p["security_id"]: coverage_status(event, p["security_id"], {}) for p in parts}
    c = sum(1 for s in statuses.values() if s == "COMPUTED")
    i = sum(1 for s in statuses.values() if s == "INSUFFICIENT")
    u = sum(1 for s in statuses.values() if s == "UNAVAILABLE")
    n = sum(1 for s in statuses.values() if s == "NOT_COMPUTED")
    lines = ["%s 本窗口行情覆盖：可计算 %d / 覆盖不足 %d / 不可得 %d / 未计算 %d（共 %d 只本题材标的）"
             % (AUTO_GAP_PREFIX, c, i, u, n, len(parts))]

    # ★ 按 reason 分组 —— 每组一句，原因逐类写清（见 compute_raw 的守卫生成）
    start, end = window[0], window[1]
    by_reason: dict = {}
    for p in parts:
        sid = p["security_id"]
        if statuses[sid] != "UNAVAILABLE":
            continue
        raw = compute_raw(conn, sid, start, end)
        by_reason.setdefault(raw.get("reason") or "unknown", []).append(sid)
    for reason, sids in sorted(by_reason.items()):
        lines.append("%s 行情不可得：%s —— %s，**不补数**"
                     % (AUTO_GAP_PREFIX, " / ".join(sorted(sids)),
                        UNAVAILABLE_REASON_TEXT.get(reason, UNAVAILABLE_REASON_TEXT["unknown"])))
    return lines


def rewrite_event(conn, event: dict, doc: dict) -> dict:
    """重算单个事件的行情块 + 参与者覆盖文案 + 事件行情状态 + AUTO 缺口行。"""
    e = json.loads(json.dumps(event))            # 深拷贝，保持键序
    mp = e.get("market_performance")
    if not mp:
        return e
    window = mp.get("window")
    if not window or len(window) != 2:
        return e                                  # 无窗口 → 不猜（`--check` 会提示）

    start, end = window[0], window[1]
    bench_raw = compute_raw(conn, BENCHMARK_ID, start, end)
    mp["benchmark"] = {BENCHMARK_ID: finalize(bench_raw)}

    by = {}
    for sid in (mp.get("by_security") or {}):
        by[sid] = finalize(compute_raw(conn, sid, start, end), bench_raw)
    mp["by_security"] = by
    mp["contract_version"] = CONTRACT_VERSION
    e["market_performance"] = mp

    for p in e.get("participants") or []:
        sid = p.get("security_id")
        if sid:
            p["market_data"] = coverage_text(conn, sid, start, end)

    e["study_state"] = event_study_state(e, finalize(bench_raw))

    # ★ 只重写带 AUTO 前缀的缺口行；人类写的条目（Beta Contamination 等）原样保留
    kept = [g for g in (e.get("known_gaps") or []) if not g.startswith(AUTO_GAP_PREFIX)]
    e["known_gaps"] = auto_gap_lines(e, doc, conn, window) + kept
    return e


def rewrite_doc(conn, doc: dict) -> dict:
    out = json.loads(json.dumps(doc))
    out["events"] = [rewrite_event(conn, ev, doc) for ev in doc.get("events") or []]
    return out


# ---------------------------------------------------------------- 校验

class Issue:
    def __init__(self, level, file, event, sid, field, message):
        self.level, self.file, self.event = level, file, event
        self.sid, self.field, self.message = sid, field, message

    def __str__(self):
        bits = [self.file]
        if self.event:
            bits.append(self.event)
        if self.sid:
            bits.append(self.sid)
        if self.field:
            bits.append(self.field)
        return "  %s %s: %s" % (self.level, " / ".join(bits), self.message)


def _num_diff(a, b, tol):
    if a is None or b is None:
        return None
    try:
        return abs(float(a) - float(b))
    except (TypeError, ValueError):
        return None


def compare_event(conn, fname, event, issues) -> None:
    mp = event.get("market_performance")
    if not mp:
        return
    window = mp.get("window")
    if not window or len(window) != 2:
        issues.append(Issue("WARN", fname, event.get("event_id"), None, "window",
                            "未登记窗口 → 无法复算（跳过，不猜测）"))
        return
    start, end = window[0], window[1]

    # ---- 基准
    bench_raw = compute_raw(conn, BENCHMARK_ID, start, end)
    bench_exp = finalize(bench_raw)
    bench_act = (mp.get("benchmark") or {}).get(BENCHMARK_ID)
    if not bench_act:
        issues.append(Issue("FAIL", fname, event.get("event_id"), BENCHMARK_ID, "benchmark", "缺少基准块"))
    else:
        _compare_block(fname, event, BENCHMARK_ID, bench_act, bench_exp, issues,
                       is_bench=True)

    # ---- 标的
    for sid, act in (mp.get("by_security") or {}).items():
        raw = compute_raw(conn, sid, start, end)
        _compare_block(fname, event, sid, act, finalize(raw, bench_raw), issues,
                       span_text=_series_span_text(conn, sid),
                       alt=alt_excess(raw, bench_raw) if "error" not in raw
                       and "error" not in bench_raw else None)

    # ---- 事件级状态（★ 用**产物自身**的数据判定，与 Product 同规则）
    declared = event.get("study_state")
    computed = event_study_state(event, bench_exp)
    if declared and declared != computed:
        issues.append(Issue("FAIL", fname, event.get("event_id"), None, "study_state",
                            "声明 %s，按产物数据应为 %s" % (declared, computed)))

    # ---- AUTO 缺口行（只在产物带合同版本时强制：旧文件没有这些标记）
    auto = [g for g in (event.get("known_gaps") or []) if g.startswith(AUTO_GAP_PREFIX)]
    if mp.get("contract_version") == CONTRACT_VERSION:
        want = auto_gap_lines(event, {}, conn, window)
        if auto != want:
            issues.append(Issue("FAIL", fname, event.get("event_id"), None, "known_gaps",
                                "AUTO 行情缺口行与当前覆盖不符（应重跑 --write）"))


def _compare_block(fname, event, sid, act, exp, issues, is_bench=False, alt=None,
                   span_text="—") -> None:
    eid = event.get("event_id")
    if "error" in exp:
        if act.get("error"):
            if act.get("error") != exp["error"]:
                issues.append(Issue("FAIL", fname, eid, sid, "error",
                                    "产物 %s，实况 %s" % (act.get("error"), exp["error"])))
            elif act.get("reason") and act.get("reason") != exp["reason"]:
                issues.append(Issue("FAIL", fname, eid, sid, "reason",
                                    "缺失原因不符：产物 %s，实况 %s"
                                    % (act.get("reason"), exp["reason"])))
            return
        # ★★ 行情库**不覆盖**该窗口，而产物给出了数值 → **无法复算**。
        #    这不是「数值错了」，也不据此改数/删数 —— 如实标 UNVERIFIABLE 并计入汇总。
        why = {
            "non_positive_adj_close": "序列在窗口内出现**非正价格**（上游 qfq 除权价差法，高分红个股早年会出现负价）",
            "discontinuous_series": "序列在窗口内出现 **>45% 的单日跳变**（raw 同步 → 价格变化确实发生）",
            "qfq_method_artifact": "序列在窗口内出现 **>45% 的单日跳变**但 raw 不同步 → 上游 qfq 方法学产物（非真实价格变化）",
        }.get(exp.get("reason"), "行情库不覆盖该窗口")
        issues.append(Issue("WARN", fname, eid, sid, "UNVERIFIABLE",
                            "%s（%s；序列 %s）→ 产物数值**无法复算**，原样保留"
                            % (why, exp["reason"], span_text)))
        return
    if act.get("error"):
        issues.append(Issue("FAIL", fname, eid, sid, "error",
                            "★ 产物标记 %s，但库内本窗口可计算（%d 个交易日）→ 旧缺失状态已过期"
                            % (act["error"], exp["trading_days"])))
        return

    if act.get("trading_days") != exp["trading_days"]:
        issues.append(Issue("FAIL", fname, eid, sid, "trading_days",
                            "产物 %s，实况 %s" % (act.get("trading_days"), exp["trading_days"])))
    for name in ("first", "last", "high"):
        ad, ac = _point_of(act, name)
        ed, ec = _point_of(exp, name)
        if ad != ed:
            issues.append(Issue("FAIL", fname, eid, sid, name + ".date",
                                "产物 %s，实况 %s" % (ad, ed)))
        d = _num_diff(ac, ec, TOLERANCE_PRICE)
        if d is not None and d > TOLERANCE_PRICE:
            issues.append(Issue("FAIL", fname, eid, sid, name + ".close",
                                "产物 %s，实况 %s" % (ac, ec)))
    for key in ("period_return_pct", "to_high_pct", "max_drawdown_from_high_pct"):
        d = _num_diff(act.get(key), exp.get(key), TOLERANCE_PP)
        if d is None:
            issues.append(Issue("FAIL", fname, eid, sid, key,
                                "产物缺该字段（实况 %s）" % exp.get(key)))
        elif d > TOLERANCE_PP:
            issues.append(Issue("FAIL", fname, eid, sid, key,
                                "产物 %s，实况 %s（差 %.2fpp）" % (act.get(key), exp.get(key), d)))
    if not is_bench:                    # ★ 基准没有「超额」两列
        for key, alt_key in (("excess_period_pp", 0), ("excess_to_high_pp", 1)):
            got = act.get(key)
            if got is None:
                issues.append(Issue("FAIL", fname, eid, sid, key,
                                    "产物缺该字段（实况 %s）" % exp.get(key)))
                continue
            # ★ 两种等价写法都接受：先舍入再相减（生成用） / 先相减再舍入（部分旧文件）
            ok = _num_diff(got, exp.get(key), TOLERANCE_PP) is not None \
                and _num_diff(got, exp.get(key), TOLERANCE_PP) <= TOLERANCE_PP
            if not ok and alt is not None:
                ok = _num_diff(got, alt[alt_key], TOLERANCE_PP) <= TOLERANCE_PP
            if not ok:
                issues.append(Issue("FAIL", fname, eid, sid, key,
                                    "产物 %s，实况 %s（另一种等价写法 %s）"
                                    % (got, exp.get(key), alt[alt_key] if alt else "—")))
    if act.get("max_drawdown_from_high_pct") is not None and act["max_drawdown_from_high_pct"] > 0:
        issues.append(Issue("FAIL", fname, eid, sid, "max_drawdown_from_high_pct",
                            "回撤必须 ≤ 0（实得 %s）" % act["max_drawdown_from_high_pct"]))
    if act.get("to_high_pct") is not None and act.get("period_return_pct") is not None:
        if act["to_high_pct"] + 1e-9 < act["period_return_pct"]:
            issues.append(Issue("FAIL", fname, eid, sid, "to_high_pct",
                                "至高点涨幅 %s < 区间涨跌 %s（至高点定义不自洽）"
                                % (act["to_high_pct"], act["period_return_pct"])))


def check_doc(conn, fname, doc) -> list:
    issues: list = []
    mp_contract = doc.get("market_performance_contract")
    if mp_contract and mp_contract.get("version") != CONTRACT_VERSION:
        issues.append(Issue("FAIL", fname, None, None, "market_performance_contract",
                            "合同版本 %s ≠ 本脚本 %s" % (mp_contract.get("version"), CONTRACT_VERSION)))
    for ev in doc.get("events") or []:
        compare_event(conn, fname, ev, issues)
        if mp_contract:                     # ★ 仅对「本脚本生成」的文件校验覆盖文案
            mp = ev.get("market_performance") or {}
            w = mp.get("window")
            if w:
                for p in ev.get("participants") or []:
                    sid = p.get("security_id")
                    if not sid:
                        continue
                    want = coverage_text(conn, sid, w[0], w[1])
                    if p.get("market_data") != want:
                        issues.append(Issue("FAIL", fname, ev.get("event_id"), sid, "market_data",
                                            "产物「%s」≠ 实况「%s」" % (p.get("market_data"), want)))
    return issues


def load_index() -> dict:
    with open(INDEX_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def active_docs(index: dict):
    for entry in index.get("maps") or []:
        path = os.path.join(CURRENT_DIR, entry["file"])
        if not os.path.exists(path):
            yield entry, None
            continue
        with open(path, encoding="utf-8") as fh:
            yield entry, json.load(fh)


# ---------------------------------------------------------------- 生成

def next_version_path(src_name: str) -> str:
    m = re.match(r"^(.*)_v(\d+)_(\d+)\.json$", src_name)
    if not m:
        raise SystemExit("FAIL: 无法从文件名推导版本号：%s" % src_name)
    minor = int(m.group(2))
    patch = int(m.group(3)) + 1
    return "%s_v%d_%d.json" % (m.group(1), minor, patch)


def dump(doc: dict, path: str) -> None:
    text = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def write_theme(theme_id: str, out: str | None, update_index: bool) -> int:
    index = load_index()
    entry = next((m for m in index["maps"] if m.get("theme_id") == theme_id), None)
    if entry is None:
        print("FAIL: 索引里没有题材 %s" % theme_id)
        return 1
    src_name = entry["file"]
    src_path = os.path.join(CURRENT_DIR, src_name)
    with open(src_path, encoding="utf-8") as fh:
        src = json.load(fh)

    new_name = next_version_path(src_name)
    target = out or os.path.join(CURRENT_DIR, new_name)
    if os.path.exists(target):
        print("FAIL: 目标文件已存在，拒绝覆盖（版本化产物必须逐字节保留）：%s" % target)
        return 1

    conn = open_market_ro()
    try:
        doc = rewrite_doc(conn, src)
    finally:
        conn.close()

    # ★ 版本号来自**推导出的新文件名**（与 --out 的路径无关），保证产物自洽
    doc["artifact_version"] = "v" + new_name.rsplit("_v", 1)[-1][:-5].replace("_", ".")
    doc["supersedes"] = src_name
    doc["generated_at"] = GENERATED_AT
    doc["generated_by"] = "research/scripts/build_theme_market_performance.py（v0.24）"
    doc["market_performance_contract"] = {
        "version": CONTRACT_VERSION,
        "price_series": "market_daily.price_type='adjusted' → adj_close（前复权收盘）",
        "window": "market_performance.window [start, end]，双端包含",
        "trading_days": "窗口内该序列实际行数（不是日历天数、不是基准交易日数）",
        "high": "窗口内 adj_close 最大值（首次出现）；不是 high 列、不是 Campaign peak_date",
        "period_return_pct": "(last.close / first.close - 1) × 100",
        "to_high_pct": "(high.close / first.close - 1) × 100",
        "max_drawdown_from_high_pct": "★ 自至高点「之后」的最大回撤 = min over t>=high.date of (close_t/high.close - 1) × 100；不是全窗口最大回撤",
        "benchmark": "SH000300，同窗口、同价格口径；excess = 个股 − 基准（区间与至高点两列口径不同，不得混用）",
        "rounding": "百分比 1 位小数（Python round）；超额由已舍入的两个百分比相减后再舍入",
        "missing": "窗口内 < 2 行 → error=insufficient_data_in_window + reason（no_series / no_rows_in_window / single_row），不补 0",
        "non_positive_price": "★ 窗口内任一条 adj_close <= 0 → error=invalid_price_series（上游 qfq 除权价差法在高分红个股早年会产生负价，属数据源方法学限制）",
        "discontinuous_series": "★ 窗口内相邻交易日跳变 > 45% → error=invalid_price_series。"
                                "★ v2 起按 raw 佐证分类：raw 同步跳变 → discontinuous_series（价格变化确实发生）；"
                                "raw 不同步 → qfq_method_artifact（上游 qfq 除权价差法的方法学产物，非真实价格变化）",
        "series_gap": "★ v2 起：窗口内相邻两条记录之间缺交易日（记录缺口）→ error=invalid_price_series，"
                      "reason=series_gap（跨缺口算收益不是窗口收益）。全库实测 5 例，缺口 14–1095 个交易日。",
        "price_basis": "★ v2 起每个标的块显式声明 price_basis。当前**只有** adjusted_qfq。"
                       "v0.27 曾评估 hfq（后复权）作为早年高分红段替代基准，**未采用**："
                       "逐日复权因子并非常数（±0.15% 常态 / 除权日 +1.53%），复权约定无法从数据解释、"
                       "收益无法独立核验（审计见 research/research/reports/hfq_basis_audit_v0_1.json）。"
                       "★ 基准 SH000300 为价格指数（qfq ≡ raw，2864/2864 天）。",
        "source": "research/database/market_data.db（由被跟踪的便携快照恢复）",
        "generated_by": "research/scripts/build_theme_market_performance.py",
    }

    dump(doc, target)
    print("已生成：%s" % os.path.relpath(target, REPO))

    if update_index and not out:
        entry["file"] = new_name
        entry["event_count"] = len(doc.get("events") or [])
        index["generated_at"] = GENERATED_AT
        dump(index, INDEX_PATH)
        print("索引已指向：%s（event_count=%d）" % (new_name, entry["event_count"]))
    return 0


# ---------------------------------------------------------------- main

def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="题材事件地图行情转写 / 漂移校验")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="只读校验全部活跃题材文件（不写盘）")
    g.add_argument("--write", metavar="THEME_ID", help="生成新版本化文件（永不覆盖旧文件）")
    ap.add_argument("--out", help="仅配合 --write：输出到指定路径（不动索引）")
    ap.add_argument("--no-index", action="store_true", help="仅配合 --write：不更新索引")
    a = ap.parse_args(argv)

    if a.write:
        return write_theme(a.write, a.out, update_index=not a.no_index)

    print("=" * 74)
    print("题材事件地图 · 行情一致性校验（%s）" % CONTRACT_VERSION)
    print("=" * 74)
    conn = open_market_ro()
    try:
        index = load_index()
        issues: list = []
        n_events = 0
        for entry, doc in active_docs(index):
            if doc is None:
                issues.append(Issue("FAIL", entry["file"], None, None, "file",
                                    "索引指向的文件不存在"))
                continue
            n_events += len(doc.get("events") or [])
            issues += check_doc(conn, entry["file"], doc)
    finally:
        conn.close()

    fails = [i for i in issues if i.level == "FAIL"]
    warns = [i for i in issues if i.level == "WARN"]
    unverifiable = [i for i in warns if i.field == "UNVERIFIABLE"]
    for i in issues:
        print(i)
    print("-" * 74)
    print("题材 %d · 事件 %d · FAIL %d · WARN %d（其中 UNVERIFIABLE %d）"
          % (len(index["maps"]), n_events, len(fails), len(warns), len(unverifiable)))
    if fails:
        print("结果: FAIL（产物与行情库不一致 —— 请按合同重跑 --write，不要手改数值）")
        return 1
    if unverifiable:
        print("结果: PASS（可复算的数值全部一致；%d 组因**行情库不覆盖该窗口**无法复算，"
              "原样保留、不补数）" % len(unverifiable))
        return 0
    print("结果: PASS（全部数值可由 market_data.db 复算）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
