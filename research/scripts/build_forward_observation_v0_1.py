#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_forward_observation_v0_1.py —— 当前前瞻观察（v0.33）。

## 它回答什么

「**以最新完整交易日为观察时点，历史上哪些重复模式值得现在就开始看？**」

不是再补 33 个历史事件，而是把「历史行情批量扫描 → 高频重复模式 → 当前窗口」跑通：

1. 批量取**指数 / 行业板块 / 概念成分 / 个股**日线（腾讯 GTIMG + 新浪概念节点 + 同花顺行业板块）；
2. 对每个候选模式算统一口径的历史统计（`occurrence_count` / `response_count` / `response_rate` /
   `median_lead_days` / 事件前超额 / 事件后超额 / `sample_years` / `known_biases`）；
3. 以 `as_of` 为硬截止，只使用该日之前已公开的信息；`published_at` 与 `event_date` 分开；
4. 输出少量观察候选（可以为 0–3 个），并写清「哪些是计算事实、哪些只是研究假设」。

## 口径（写死，不许为让某个模式好看而改）

- 收益一律用**原始收盘价**（`qfq=0`）计算日度与窗口收益；跨期比较才用复权（本产物不用复权）。
- 基准 = 沪深300（`sh000300`）；超额 = 区间收益 − 基准同区间收益（pp）。
- 事件前窗口 = 事件日前 20 个交易日（不含当日）；事件后窗口 = 事件日后 20 个交易日。
- 响应判定：**篮子中位超额 > 0 且 广度 ≥ 0.5**（同时给出连续量，不只给布尔）。
- 涨停 = 原始收盘环比落在板块带内（主板 9.8–10.6%；创业板 2020-08-24 前 9.8–10.6%、之后 19.5–21.2%；
  科创板 19.5–21.2%）。ST 无法从库内判定 → 不检测（漏报方向）。
- `as_of` = 基准指数最后一根完整日线日期（由数据决定，不写死）。

## 用法

    python research/scripts/build_forward_observation_v0_1.py --fetch     # 抓数（本地缓存，可重跑）
    python research/scripts/build_forward_observation_v0_1.py --write --version 1
    python research/scripts/build_forward_observation_v0_1.py --check     # 只查产物结构/口径（不联网）

产物：`research/current/forward_observation_v0_1.json`
     + 带日期的快照 `research/current/forward_observation_snapshots/FO-<as_of>.json`（不可覆盖）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import time
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
CACHE_DIR = os.path.join(REPO, "research", "data", "forward_scan")
CACHE = os.path.join(CACHE_DIR, "cache_v0_1.json")

# ★ v0.59（Wave 2.3）：参与者末日距 as_of 超过这么多个交易日 → 剔除（不参与中位数、不补造）
MAX_STALE_TRADING_DAYS = 5
UNIVERSE = os.path.join(CACHE_DIR, "universe_v0_1.json")
SNAP_DIR = os.path.join(CURRENT, "forward_observation_snapshots")
OUT_RE = re.compile(r"forward_observation_v0_(\d+)\.json$")
# ★★ v0.60：原为硬编码 `"2026-10-24"` —— 之后每次刷新都会把「抓取日」写成 10-24，
#   与实际抓取日期不符（溯源字段说谎）。改为**运行时实际日期**。
#   本产物是**版本化快照**（每次 --write 生成新版本文件），因此不要求跨日字节一致。
GENERATED_AT = time.strftime("%Y-%m-%d")

PACING = 0.22
UA = {"User-Agent": "Mozilla/5.0"}

# ---------------------------------------------------------------- 数据源（实测可用）

INDICES = [
    ("CSI300", "沪深300", "sh000300"),
    ("SSE", "上证综指", "sh000001"),
    ("SZSE", "深证成指", "sz399001"),
    ("CHINEXT", "创业板指", "sz399006"),
]

# ★ 真实农历新年日期（春节首日；来源：国务院节假日安排 / 历法；本脚本只用于**对齐窗口**）
LUNAR_NEW_YEAR = {
    2016: "2016-02-08", 2017: "2017-01-28", 2018: "2018-02-16", 2019: "2019-02-05",
    2020: "2020-01-25", 2021: "2021-02-12", 2022: "2022-02-01", 2023: "2023-01-22",
    2024: "2024-02-10", 2025: "2025-01-29", 2026: "2026-02-17", 2027: "2027-02-06",
}
ZODIAC = {2016: "猴", 2017: "鸡", 2018: "狗", 2019: "猪", 2020: "鼠", 2021: "牛",
          2022: "虎", 2023: "兔", 2024: "龙", 2025: "蛇", 2026: "马", 2027: "羊"}

# ★ 台海事件（事实发生日 event_date / 信息最早公开日 published_at）
#   ★ 只作为**事件族样本**用于统计；若某事件进入最终候选，需再核原始来源（本产物标 needs_source）
STRAIT_EVENTS = [
    {"event_id": "TS-2016-0520", "event_date": "2016-05-20", "published_at": "2016-05-20",
     "label": "台湾地区领导人就职（两岸表述变化）", "category": "POLICY_STATEMENT"},
    {"event_id": "TS-2019-0102", "event_date": "2019-01-02", "published_at": "2019-01-02",
     "label": "《告台湾同胞书》发表 40 周年纪念", "category": "POLICY_STATEMENT"},
    {"event_id": "TS-2022-0802", "event_date": "2022-08-02", "published_at": "2022-08-02",
     "label": "美国众议长访台（事件日）", "category": "DIPLOMATIC_VISIT"},
    {"event_id": "TS-2022-0804", "event_date": "2022-08-04", "published_at": "2022-08-04",
     "label": "环台岛军事演训开始", "category": "MILITARY_DRILL"},
    {"event_id": "TS-2023-0408", "event_date": "2023-04-08", "published_at": "2023-04-08",
     "label": "环台岛战备警巡与「联合利剑」演习", "category": "MILITARY_DRILL"},
    {"event_id": "TS-2024-0520", "event_date": "2024-05-20", "published_at": "2024-05-20",
     "label": "台湾地区领导人就职", "category": "POLICY_STATEMENT"},
    {"event_id": "TS-2024-0523", "event_date": "2024-05-23", "published_at": "2024-05-23",
     "label": "「联合利剑-2024A」演习", "category": "MILITARY_DRILL"},
]

STRAIT_CONCEPT_NODE = "gn_hxxa"   # 新浪概念「海峡西岸」（78 只，**当前**成分）


def _get(url: str, timeout: int = 25, referer: str | None = None) -> bytes:
    h = dict(UA)
    if referer:
        h["Referer"] = referer
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


SINA_KLINE = ("https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
              "CN_MarketData.getKLineData?symbol=%s&scale=240&ma=no&datalen=%d")


def fetch_kline(symbol: str, datalen: int = 3000) -> tuple:
    """日线（**不复权**，原始收盘）。优先新浪（一次 3000 根，实测 2014-06 起），腾讯备用。

    返回 [[date, open, close, high, low, volume], ...]，按日期升序。
    ★ 新浪接口字段为 day/open/high/low/close/volume（**无前收**）→ 日涨跌幅用相邻收盘环比。
    """
    try:
        raw = _get(SINA_KLINE % (symbol, datalen), referer="https://finance.sina.com.cn").decode("utf-8", "replace")
        d = json.loads(raw)
        rows = [[x["day"], float(x["open"]), float(x["close"]), float(x["high"]),
                 float(x["low"]), float(x["volume"])] for x in d]
        if rows:
            return rows, "sina"
    except Exception:
        pass
    # 备用：腾讯 GTIMG（单次 ≤800 根）
    try:
        url = ("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
               "param=%s,day,2015-01-01,2026-12-31,800," % symbol)
        d = json.loads(_get(url).decode("utf-8", "replace"))
        node = (d.get("data") or {}).get(symbol) or {}
        rows = node.get("day") or node.get("qfqday") or []
        return [[r[0], float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])] for r in rows], "tencent"
    except Exception:
        return [], "unavailable"


def merge_series(old: list, new: list) -> list:
    """按日期合并去重（新数据覆盖同日旧值）。★ 增量刷新：旧数据不会因为「条数够多」被永久跳过。"""
    merged = {}
    for r in (old or []):
        merged[r[0]] = r
    for r in (new or []):
        merged[r[0]] = r
    return [merged[d] for d in sorted(merged)]


def fetch_universe() -> list:
    rows = []
    page = 1
    while page <= 80:
        url = ("https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
               "Market_Center.getHQNodeData?page=%d&num=80&sort=symbol&asc=1&node=hs_a" % page)
        try:
            d = json.loads(_get(url, referer="https://finance.sina.com.cn").decode("utf-8", "replace"))
        except Exception:
            break
        if not d:
            break
        rows.extend(d)
        page += 1
        time.sleep(0.12)
    return rows


def fetch_concept_members(node: str) -> list:
    out = []
    page = 1
    while page <= 5:
        url = ("https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
               "Market_Center.getHQNodeData?page=%d&num=100&sort=symbol&asc=1&node=%s" % (page, node))
        try:
            d = json.loads(_get(url, referer="https://finance.sina.com.cn").decode("utf-8", "replace"))
        except Exception:
            break
        if not d:
            break
        out.extend(d)
        page += 1
        time.sleep(0.12)
    return out


def fetch_industry_boards() -> list:
    """同花顺行业板块列表（140 个）+ 当年日线（last.js）。"""
    t = _get("http://q.10jqka.com.cn/thshy/", referer="http://q.10jqka.com.cn").decode("gbk", "replace")
    pairs = re.findall(r"/thshy/detail/code/(\d+)/\"[^>]*>([^<]{1,20})<", t)
    seen, boards = set(), []
    for code, name in pairs:
        if code in seen:
            continue
        seen.add(code)
        boards.append({"code": code, "name": name.strip()})
    out = []
    for b in boards:
        try:
            raw = _get("http://d.10jqka.com.cn/v6/line/bk_%s/01/last.js" % b["code"],
                       referer="http://q.10jqka.com.cn").decode("utf-8", "replace")
            m = re.search(r'"data":"([^"]*)"', raw)
            if not m:
                continue
            rows = []
            for seg in m.group(1).split(";"):
                p = seg.split(",")
                if len(p) < 7:
                    continue
                # ★ 字段：date, open, high, low, close, volume, amount
                rows.append([p[0], float(p[1]), float(p[2]), float(p[3]),
                             float(p[4]), float(p[5])])
            if len(rows) < 61:
                continue
            closes = [r[4] for r in rows]
            out.append({
                "code": b["code"], "name": b["name"],
                "close": closes[-1],
                "ret_20d": round((closes[-1] / closes[-21] - 1) * 100, 2),
                "ret_60d": round((closes[-1] / closes[-61] - 1) * 100, 2),
                "n": len(rows),
                "first_date": rows[0][0], "last_date": rows[-1][0],
            })
        except Exception:
            continue
        time.sleep(PACING)
    return out


def fetch_board_prices(codes: list) -> dict:
    """板块价格：last.js 不含价格，用同花顺「当年」K 线接口逐板块取（只取最近 60 交易日）。"""
    out = {}
    for code in codes:
        try:
            raw = _get("http://d.10jqka.com.cn/v6/line/bk_%s/01/last.js" % code,
                       referer="http://q.10jqka.com.cn").decode("utf-8", "replace")
            m = re.search(r'"price":"([^"]*)"', raw)
            if not m:
                continue
            prices = [float(x) for x in m.group(1).split(",") if x]
            if len(prices) >= 61:
                out[code] = {"close": prices[-1], "ret_20d": prices[-1] / prices[-21] - 1.0,
                             "ret_60d": prices[-1] / prices[-61] - 1.0, "n": len(prices)}
        except Exception:
            continue
        time.sleep(0.12)
    return out


# ---------------------------------------------------------------- 计算

def trading_days(rows: list) -> list:
    return [r[0] for r in rows]


def window_return(rows: list, start_idx: int, end_idx: int) -> float | None:
    if start_idx < 0 or end_idx >= len(rows) or end_idx <= start_idx:
        return None
    return rows[end_idx][2] / rows[start_idx][2] - 1.0


def limit_band(symbol: str, date: str) -> tuple:
    code = symbol[-6:]
    if code.startswith("688"):
        return 19.5, 21.2
    if code.startswith(("300", "301")):
        return (19.5, 21.2) if date >= "2020-08-24" else (9.8, 10.6)
    return 9.8, 10.6


def limit_up_days(rows: list, symbol: str, start: str, end: str) -> int:
    n = 0
    for i in range(1, len(rows)):
        d = rows[i][0]
        if d < start or d > end:
            continue
        lo, hi = limit_band(symbol, d)
        prev = rows[i - 1][2]
        if prev <= 0:
            continue
        pct = (rows[i][2] / prev - 1.0) * 100.0
        if lo <= pct <= hi:
            n += 1
    return n


def event_study(members: dict, bench: list, anchor_date: str, pre: int = 20,
                post_ks=(5, 10, 20)) -> dict:
    """★★ v0.33.1：**三个口径分开算**的事件研究（不再用「前 20 → 后 20」总收益冒充事件响应）。

    · `pre`：事件前 20 个交易日（事件前一交易日往前 20 日）相对基准超额；
    · `event_day`：**事件前一交易日收盘 → 事件日（或事件后第一个交易日）收盘** ——
      覆盖周末/节假日事件的首日跳空；
    · `post_k`：事件日收盘 → 事件后第 k 个交易日收盘，k ∈ {5,10,20}；
    · `responded` **只看事件后 20 日**（中位超额 > 0 且广度 ≥ 0.5），不看事件前。

    `anchor_date` 若落在非交易日，取**其后第一个交易日**为 `anchor_trading_day`（并记录原事件日）。
    """
    bdays = trading_days(bench)
    ai = next((i for i, d in enumerate(bdays) if d >= anchor_date), None)
    if ai is None or ai - 1 - pre < 0:
        return {"status": "OUT_OF_RANGE", "anchor_event_date": anchor_date}
    prev = ai - 1
    out = {"status": "OK", "anchor_event_date": anchor_date,
           "anchor_trading_day": bdays[ai], "prev_trading_day": bdays[prev],
           "window_non_trading": bdays[ai] != anchor_date}
    bench_idx = {d: i for i, d in enumerate(bdays)}

    def excess_between(d0: str, d1: str) -> list:
        if d0 not in bench_idx or d1 not in bench_idx:
            return []
        i0, i1 = bench_idx[d0], bench_idx[d1]
        if i1 <= i0:
            return []
        b = bench[i1][2] / bench[i0][2] - 1.0
        vals = []
        for sym, rows in members.items():
            m = {r[0]: r[2] for r in rows}
            if d0 not in m or d1 not in m or m[d0] <= 0:
                continue
            vals.append((m[d1] / m[d0] - 1.0 - b) * 100.0)
        return vals

    # ① 事件前 20 日
    d_pre0 = bdays[prev - pre]
    pre_vals = excess_between(d_pre0, bdays[prev])
    out["pre"] = {
        "window": [d_pre0, bdays[prev]],
        "members_with_data": len(pre_vals),
        "median_excess_pct": round(statistics.median(pre_vals), 2) if pre_vals else None,
        "breadth": round(sum(1 for x in pre_vals if x > 0) / len(pre_vals), 3) if pre_vals else None,
    }
    # ② 事件日（前收 → 事件日/其后首个交易日收）
    day_vals = excess_between(bdays[prev], bdays[ai])
    out["event_day"] = {
        "window": [bdays[prev], bdays[ai]],
        "members_with_data": len(day_vals),
        "median_excess_pct": round(statistics.median(day_vals), 2) if day_vals else None,
        "breadth": round(sum(1 for x in day_vals if x > 0) / len(day_vals), 3) if day_vals else None,
        "gap_included": bdays[ai] != anchor_date,
    }
    # ③ 事件后 k 日
    out["post"] = {}
    for k in post_ks:
        j = ai + k
        if j >= len(bdays):
            out["post"]["post%d" % k] = {"status": "INSUFFICIENT_FUTURE_DATA",
                                         "required_end": "第 %d 个交易日后" % k}
            continue
        vals = excess_between(bdays[ai], bdays[j])
        out["post"]["post%d" % k] = {
            "status": "OK", "window": [bdays[ai], bdays[j]],
            "members_with_data": len(vals),
            "median_excess_pct": round(statistics.median(vals), 2) if vals else None,
            "breadth": round(sum(1 for x in vals if x > 0) / len(vals), 3) if vals else None,
        }
    p20 = out["post"].get("post20") or {}
    if p20.get("status") == "OK" and p20.get("median_excess_pct") is not None:
        out["responded"] = bool(p20["median_excess_pct"] > 0 and (p20["breadth"] or 0) >= 0.5)
        out["response_basis"] = "post20"
    else:
        out["responded"] = None
        out["response_basis"] = "INSUFFICIENT_FUTURE_DATA"
    return out


def cumulative_lead(members: dict, bench: list, anchor_date: str, lookback: int = 20,
                    threshold_pct: float = 2.0) -> dict:
    """★★ 提前量：**累计超额**首次 ≥ 阈值 的交易日（负 = 事件前）。

    ★ 只是**价格信号时间**，不证明因果，也不证明信息泄露。
    样本不足（没有成员覆盖整段、或从未达到阈值）→ `lead_days = None` 并写原因，
    **不输出误导性的中位提前天数**。
    """
    bdays = trading_days(bench)
    ai = next((i for i, d in enumerate(bdays) if d >= anchor_date), None)
    if ai is None or ai - lookback < 1:
        return {"lead_days": None, "reason": "基准日历不足（事件前 20 个交易日不可用）"}
    base = bdays[ai - lookback]
    covered = 0
    for sym, rows in members.items():
        m = {r[0]: r[2] for r in rows}
        if base in m and bdays[ai - 1] in m:
            covered += 1
    if covered < 3:
        return {"lead_days": None, "reason": "覆盖事件前窗口的成员不足 3 只，无法计算累计超额"}
    for k in range(1, lookback + 1):
        d = bdays[ai - lookback + k]
        b = bench[ai - lookback + k][2] / bench[ai - lookback][2] - 1.0
        vals = []
        for sym, rows in members.items():
            m = {r[0]: r[2] for r in rows}
            if base not in m or d not in m or m[base] <= 0:
                continue
            vals.append((m[d] / m[base] - 1.0 - b) * 100.0)
        if len(vals) >= 3 and statistics.median(vals) >= threshold_pct:
            return {"lead_days": k - lookback, "reason": None,
                    "basis": "累计超额首次 ≥ +%.1fpp（起点 %s）" % (threshold_pct, base),
                    "note": "★ 仅为价格信号时间，不证明因果或信息泄露"}
    return {"lead_days": None,
            "reason": "事件前 %d 个交易日内累计超额从未达到 +%.1fpp" % (lookback, threshold_pct)}


def build_zodiac_pattern(universe: list, bench: list, cache: dict) -> dict:
    """生肖：按**当年生肖字**在当前证券名称里找候选（名称快照偏差必须披露）。"""
    years = []
    for year in range(2016, 2028):
        animal = ZODIAC[year]
        lny = LUNAR_NEW_YEAR[year]
        names = [u for u in universe if animal in (u.get("name") or "")]
        testable = len(names) >= 5
        rec = {
            "year": year, "animal": animal, "lunar_new_year": lny,
            "name_matches": len(names), "testable": testable,
            "why_not_testable": None if testable else
            "当前证券名称里含「%s」的只有 %d 只（缺历史名称快照，无法重建当年候选池）" % (animal, len(names)),
        }
        if testable:
            members = {}
            for u in names:
                sym = u["symbol"]
                rows = cache.get("stocks", {}).get(sym)
                if rows:
                    members[sym] = rows
            if lny <= bench[-1][0]:
                w = event_study(members, bench, lny)
                lead = cumulative_lead(members, bench, lny)
                rec.update({"window": w, "lead_days": lead.get("lead_days"),
                            "lead_note": lead.get("reason") or lead.get("basis"),
                            "responded": w.get("responded")})
            else:
                rec["window"] = {"status": "FUTURE", "anchor": lny}
        years.append(rec)

    tested = [y for y in years if y.get("window", {}).get("status") == "OK"]
    resp = [y for y in tested if y["window"].get("responded") is True]
    leads = [y["lead_days"] for y in tested if y.get("lead_days") is not None]
    return {
        "pattern_id": "ZODIAC_NAME",
        "family": "A_CALENDAR",
        "title": "生肖名称炒作（春节前 20 交易日 ~ 节后 20 交易日）",
        "hypothesis": ("A 股在农历新年前后对「名称含当年生肖字」的股票存在符号型情绪炒作；"
                       "与基本面无关，属情绪/符号型，不得赋予行业属性。"),
        "years": years,
        "stats": {
            "occurrence_count": len(tested),
            "response_count": len(resp),
            "response_rate": round(len(resp) / len(tested), 3) if tested else None,
            "median_lead_days": statistics.median(leads) if leads else None,
            "sample_years": [y["year"] for y in tested],
            "testable_years": [y["year"] for y in years if y["testable"]],
            "not_testable_years": [y["year"] for y in years if not y["testable"]],
        },
        "known_biases": [
            "★★ 名称用**当前**证券简称回溯，没有历史名称快照 → 2016–2023 的候选池被严重低估（多为 0–4 只），"
            "这**不是**「当年没有生肖炒作」，而是「本数据无法重建当年候选池」。",
            "候选含**非符号型**同名股（如「招商蛇口」「马钢股份」），会把篮子稀释；"
            "因此同时给中位超额与广度，不用均值。",
            "样本年份少（可检验年份见 sample_years），单年极端行情会主导结论。",
        ],
        "status": "C_EXPLORATORY",
        "status_reason": "可检验年份不足（<5）且名称快照缺失；只能作为探索线索，不得声称已验证。",
    }


def _cluster_stages(events: list, gap_days: int = 20) -> list:
    """★★ 把「同一轮、窗口高度重叠」的事件归入同一**事件阶段**（避免重复计数）。

    规则：按事件日排序；若下一事件日距上一事件**不足 20 个交易日**（≈ 统计窗口重叠），
    归入同一阶段。阶段是统计单位；原始事件仍逐条保留可追溯。
    """
    stages = []
    for e in sorted(events, key=lambda x: x["event_date"]):
        if not stages:
            stages.append({"stage_id": "S1", "events": [e["event_id"]],
                           "first_event_date": e["event_date"], "last_event_date": e["event_date"],
                           "_dates": [e["event_date"]]})
            continue
        cur = stages[-1]
        # 粗略交易日近似：自然日 ×5/7
        gap = (__import__("datetime").date.fromisoformat(e["event_date"])
               - __import__("datetime").date.fromisoformat(cur["last_event_date"])).days
        if gap * 5 / 7 <= gap_days:
            cur["events"].append(e["event_id"])
            cur["last_event_date"] = e["event_date"]
            cur["_dates"].append(e["event_date"])
        else:
            stages.append({"stage_id": "S%d" % (len(stages) + 1), "events": [e["event_id"]],
                           "first_event_date": e["event_date"], "last_event_date": e["event_date"],
                           "_dates": [e["event_date"]]})
    return stages


def build_strait_pattern(bench: list, cache: dict, members_meta: dict) -> dict:
    syms = [m["symbol"] if isinstance(m, dict) else m for m in members_meta]
    members = {s: cache["stocks"][s] for s in syms if s in cache.get("stocks", {})}
    events = []
    for ev in STRAIT_EVENTS:
        rec = dict(ev)
        # ★★ 事件发生日 ≠ 首次公开日：没有独立核实的公开日一律 None
        rec["published_at"] = ev.get("published_at") or None
        rec["published_at_status"] = ("VERIFIED" if ev.get("published_at") else "UNKNOWN")
        w = event_study(members, bench, ev["event_date"])
        rec["window"] = w
        if w.get("status") == "OK":
            lead = cumulative_lead(members, bench, ev["event_date"])
            rec["lead_days"] = lead.get("lead_days")
            rec["lead_note"] = lead.get("reason") or lead.get("basis")
            rec["responded"] = w.get("responded")
        events.append(rec)
    ok = [e for e in events if e["window"].get("status") == "OK"]
    resp = [e for e in ok if e.get("responded") is True]
    leads = [e["lead_days"] for e in ok if e.get("lead_days") is not None]

    # ★★ 按事件阶段去重计数
    stages = _cluster_stages(events)
    by_id = {e["event_id"]: e for e in events}
    for st in stages:
        st["responded"] = any(by_id[x].get("responded") is True for x in st["events"])
        st["post20"] = [by_id[x]["window"].get("post", {}).get("post20", {}).get("median_excess_pct")
                        for x in st["events"]]
        st.pop("_dates", None)
    stage_ok = [st for st in stages if any(by_id[x]["window"].get("status") == "OK" for x in st["events"])]
    stage_resp = [st for st in stage_ok if st["responded"]]

    def med(key, sub=None):
        vals = []
        for e in ok:
            v = (e["window"].get(key) or {})
            if sub:
                v = (v.get(sub) or {})
            v = v.get("median_excess_pct")
            if v is not None:
                vals.append(v)
        return round(statistics.median(vals), 2) if vals else None

    return {
        "pattern_id": "TAIWAN_STRAIT_EVENT",
        "family": "B_EVENT",
        "title": "台海事件 → 海峡西岸概念（事件驱动，无固定日历）",
        "hypothesis": ("台海相关事件（政策表态 / 军事演训 / 交流）会反复引发「海峡西岸」概念股的短期超额；"
                       "**不声称存在季节性**。"),
        "method": {
            "pre": "事件前 20 个交易日（相对基准超额）",
            "event_day": "事件前一交易日收盘 → 事件日（或其后首个交易日）收盘，含跳空",
            "post": "事件日收盘 → 后 5 / 10 / 20 个交易日收盘",
            "responded": "**只看 post20**：中位超额 > 0 且广度 ≥ 0.5",
            "stages": "同一轮窗口重叠的事件归入一个阶段；occurrence/response 按**阶段**统计",
            "lead": "累计超额首次 ≥ +2pp 的交易日；仅为价格信号时间，不证明因果",
        },
        "basket": {
            "concept": "海峡西岸", "node": STRAIT_CONCEPT_NODE,
            "members": len(members_meta), "members_with_data": len(members),
            "membership_bias": "★★ 概念成分为**当前**成分（新浪概念节点），不是各事件当年的成分；"
                               "历史成分变化无法还原，属已知偏差。",
        },
        "events": events,
        "stages": stages,
        "stats": {
            "occurrence_count": len(stage_ok),
            "response_count": len(stage_resp),
            "response_rate": round(len(stage_resp) / len(stage_ok), 3) if stage_ok else None,
            "raw_event_count": len(ok),
            "raw_event_response_count": len(resp),
            "median_lead_days": statistics.median(leads) if len(leads) >= 3 else None,
            "lead_sample_count": len(leads),
            "lead_days_reason": (None if len(leads) >= 3 else
                                 ("仅 %d 个事件有可计算的提前量（<3）→ 不给中位提前量" % len(leads))),
            "median_pre_excess_pct": med("pre"),
            "median_event_day_excess_pct": med("event_day"),
            "median_post5_excess_pct": med("post", "post5"),
            "median_post20_excess_pct": med("post", "post20"),
            "sample_years": sorted({int(e["event_date"][:4]) for e in ok}),
        },
        "known_biases": [
            "概念成分为当前成分 → 幸存者偏差 + 成分变更偏差。",
            "★★ 事件发生日 ≠ 信息首次公开日；未独立核实公开日的事件 `published_at` 保持 null。",
            "★★ 提前量只是价格信号时间，不证明因果或信息泄露。",
            "样本 7 个原始事件 / 归并为阶段后见 occurrence_count，事件强度不可比（政策表态 vs 军事演训）。",
        ],
        "status": "B_REPEATED" if len(stage_ok) >= 5 and len(stage_resp) >= 3 else "C_EXPLORATORY",
        "status_reason": "按事件阶段统计；时间不固定，属事件驱动，不是季节规律。",
    }


def build_sector_scan(cache: dict) -> dict:
    prices = cache.get("boards", {})
    rows = [{"code": c, "name": v.get("name"), "close": v.get("close"),
             "ret_20d": v.get("ret_20d"), "ret_60d": v.get("ret_60d")}
            for c, v in prices.items() if v.get("ret_20d") is not None]
    rows.sort(key=lambda x: -(x.get("ret_20d") or -9))
    return {
        "source": "同花顺行业板块（bk_881xxx）· 当年日线",
        "boards_scanned": len(prices),
        "as_of_note": "板块序列为**当年**（2026）日线，仅用于当前强弱定位，不用于多年季节性统计。",
        "top_20d": rows[:10],
        "bottom_20d": rows[-5:],
    }


def build(fetch: bool = False) -> dict:
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(open(CACHE, encoding="utf-8"))
    cache.setdefault("stocks", {})
    cache.setdefault("boards", {})

    if fetch:
        # ★★ v0.33.1：**每次都刷新**（不再「条数够了就永久跳过」），按日期合并去重
        cache.setdefault("sources", {})
        cache["universe"] = fetch_universe()
        json.dump(cache["universe"], open(UNIVERSE, "w", encoding="utf-8"), ensure_ascii=False)
        universe = cache["universe"]
        for sid, name, sym in INDICES:
            rows, src = fetch_kline(sym, 3000)
            if rows:
                cache[sid] = merge_series(cache.get(sid), rows)
            cache["sources"][sid] = {"provider": src, "fetched_at": GENERATED_AT,
                                     "last_date": (cache.get(sid) or [[None]])[-1][0],
                                     "rows": len(cache.get(sid) or [])}
            time.sleep(PACING)
        zsyms = set()
        for y in (2024, 2026, 2027):
            a = ZODIAC[y]
            zsyms |= {u["symbol"] for u in universe if a in (u.get("name") or "")}
        members = fetch_concept_members(STRAIT_CONCEPT_NODE)
        cache["strait_members"] = [{"symbol": m["symbol"], "name": m["name"]} for m in members]
        cache["sources"]["strait_members"] = {"provider": "sina", "fetched_at": GENERATED_AT,
                                              "count": len(members)}
        msyms = {m["symbol"] for m in members}
        targets = zsyms | msyms
        for i, sym in enumerate(sorted(targets)):
            rows, src = fetch_kline(sym, 3000)
            if rows:
                cache["stocks"][sym] = merge_series(cache["stocks"].get(sym), rows)
            cache["sources"][sym] = {"provider": src, "fetched_at": GENERATED_AT,
                                     "last_date": (cache["stocks"].get(sym) or [[None]])[-1][0]}
            time.sleep(PACING)
            if i % 20 == 0:
                json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
        # ★★ 板块刷新失败**不致命**：保留旧数据，但把状态与日期显式写出来
        try:
            boards = fetch_industry_boards()
            for b in boards:
                cache["boards"][b["code"]] = dict(b)
            cache["sources"]["ths_board"] = {"provider": "ths", "fetched_at": GENERATED_AT,
                                             "status": "OK", "boards": len(boards),
                                             "last_date": max((b.get("last_date") or "") for b in boards) if boards else None}
        except Exception as exc:  # noqa: BLE001
            old = cache.get("boards") or {}
            cache["sources"]["ths_board"] = {
                "provider": "ths", "fetched_at": GENERATED_AT, "status": "REFRESH_FAILED",
                "error": "%s: %s" % (type(exc).__name__, str(exc)[:120]),
                "boards": len(old),
                "last_date": max((v.get("last_date") or "") for v in old.values()) if old else None,
                "note": "★ 沿用上次成功抓取的板块数据（状态见 status / last_date）",
            }
        json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)

    universe = json.load(open(UNIVERSE, encoding="utf-8")) if os.path.exists(UNIVERSE) else []
    bench = cache.get("CSI300") or []
    if not bench:
        raise SystemExit("FAIL: 缺基准指数（先 --fetch）")
    as_of = bench[-1][0]

    def perf(n):
        if len(bench) <= n:
            return None
        return round((bench[-1][2] / bench[-1 - n][2] - 1) * 100, 2)

    zodiac = build_zodiac_pattern(universe, bench, cache)
    strait = build_strait_pattern(bench, cache, cache.get("strait_members") or [])
    sectors = build_sector_scan(cache)

    return {
        "artifact": "forward_observation",
        "artifact_version": "0.1",
        "generated_at": GENERATED_AT,
        "generated_by": "research/scripts/build_forward_observation_v0_1.py",
        "supersedes": None,
        "as_of": as_of,
        "as_of_source": ("%s · 沪深300(sh000300) 最后一根完整日线（%s）"
                         % ((cache.get("sources", {}).get("CSI300") or {}).get("provider", "unknown"), as_of)),
        # ★ v0_3：`current_performance` 口径变更（基准按参与者同段日期对齐、`price_as_of` = 实际参与序列最早末日、剔除落后参与者）
        "method_version": "v0_3",
        "data_sources": [
            {"id": "sina_kline", "used_for": "指数 / 个股日线（原始收盘，不复权）",
             "endpoint": SINA_KLINE % ("<symbol>", 3000), "status": "PRIMARY",
             "note": "一次最多 3000 根；按日期合并去重（增量刷新）",
             "series_from_sina": sum(1 for v in (cache.get("sources") or {}).values()
                                     if isinstance(v, dict) and v.get("provider") == "sina")},
            {"id": "tencent_gtimg", "used_for": "日线备用源（新浪失败时）",
             "endpoint": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get", "status": "FALLBACK",
             "note": "单次 ≤800 根；批量请求会触发 501 WAF",
             "series_from_tencent": sum(1 for v in (cache.get("sources") or {}).values()
                                        if isinstance(v, dict) and v.get("provider") == "tencent")},
            {"id": "sina_universe", "used_for": "全 A 股名称与代码（每次 --fetch 刷新）",
             "endpoint": "Market_Center.getHQNodeData?node=hs_a", "status": "OK",
             "count": len(universe)},
            {"id": "sina_concept", "used_for": "概念成分（海峡西岸）",
             "endpoint": "Market_Center.getHQNodeData?node=%s" % STRAIT_CONCEPT_NODE, "status": "OK",
             "note": "★ 当前成分，非历史成分",
             "count": len(cache.get("strait_members") or [])},
            {"id": "ths_board", "used_for": "行业板块当年日线",
             "endpoint": "http://d.10jqka.com.cn/v6/line/bk_881xxx/01/last.js", "status": "OK",
             "note": "★ 仅当年数据；概念板块（30xxxx）该接口 404 → 概念用成分篮子替代",
             "count": len(cache.get("boards") or {})},
            {"id": "eastmoney", "used_for": "（未使用）", "endpoint": "push2*.eastmoney.com",
             "status": "UNAVAILABLE", "note": "本机实测 RemoteDisconnected（含直连与代理）→ 未采用"},
        ],
        "refresh": {
            "policy": "每次 --fetch 全量刷新 + 按日期合并（不因条数够多而跳过）",
            "series_last_date": {k: v.get("last_date") for k, v in (cache.get("sources") or {}).items()
                                 if isinstance(v, dict) and v.get("last_date")},
            "stale_series": sorted(k for k, v in (cache.get("sources") or {}).items()
                                   if isinstance(v, dict) and v.get("last_date") and v["last_date"] < as_of),
        },
        "benchmark": {
            "series_id": "CSI300", "name": "沪深300", "close": bench[-1][2],
            "ret_5d": perf(5), "ret_10d": perf(10), "ret_20d": perf(20), "ret_60d": perf(60),
        },
        "indices": [
            {"series_id": sid, "name": name,
             "close": (cache.get(sid) or [[None, None, None]])[-1][2],
             "ret_5d": (lambda r: round((r[-1][2] / r[-6][2] - 1) * 100, 2) if len(r) > 5 else None)(cache.get(sid) or []),
             "ret_20d": (lambda r: round((r[-1][2] / r[-21][2] - 1) * 100, 2) if len(r) > 20 else None)(cache.get(sid) or []),
             "ret_60d": (lambda r: round((r[-1][2] / r[-61][2] - 1) * 100, 2) if len(r) > 60 else None)(cache.get(sid) or [])}
            for sid, name, _ in INDICES
        ],
        "sector_scan": sectors,
        "seasonal_windows": build_seasonal_windows({"as_of": as_of}),
        "patterns": [zodiac, strait],
        "candidates": [],   # 由 select_candidates() 填（见下）
        "limitations": [
            "★★ 所有超额均为**价格结果**，不证明因果；「响应」不等于「未来必涨」。",
            "★★ 概念/名称候选池用当前快照回溯 → 存在幸存者偏差与成分变更偏差（各模式已单独标注）。",
            "★ 板块序列只有当年（2026）数据 → 不做板块多年季节性统计，只做当前强弱定位。",
            "★ ST / 退市整理 / 新股首日无法从库内判定 → 涨停计数为**漏报方向**。",
            "★ 未使用复权价做窗口收益（原始价更接近当时可见的涨跌幅）；跨除权日的个别标的会有偏差。",
        ],
    }


def build_seasonal_windows(doc: dict) -> dict:
    """从**既有历史题材产物**里找「秋冬窗口」重复出现的事件族，并检查当前是否在窗口内。

    ★ 复用 `research/current/*_historical_events_*.json` 的 `market_performance.window`，
      不新增人工挑选；当前行情来自 `research/database/market_data.db`（截至其最后一行）。
    """
    import sqlite3
    idx = json.load(open(os.path.join(CURRENT, "historical_event_maps_index.json"), encoding="utf-8"))
    themes = []
    for entry in idx["maps"]:
        path = os.path.join(CURRENT, entry["file"])
        if not os.path.exists(path):
            continue
        doc_t = json.load(open(path, encoding="utf-8"))
        hits = []
        for e in doc_t.get("events") or []:
            w = (e.get("market_performance") or {}).get("window")
            if not w:
                continue
            sm, em = int(w[0][5:7]), int(w[1][5:7])
            if sm in (8, 9, 10) and em in (12, 1, 2):
                hits.append({"event_id": e["event_id"], "window": w})
        if len(hits) >= 2:
            themes.append({"theme_id": entry["theme_id"], "label": entry.get("label"),
                           "events": hits})
    as_of = doc["as_of"]
    out = []
    db_path = os.path.join(REPO, "research", "database", "market_data.db")
    conn = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True) if os.path.exists(db_path) else None
    for t in themes:
        w0 = t["events"][-1]["window"]
        cur_start = "%d%s" % (int(as_of[:4]) if as_of[5:7] >= w0[0][5:7] else int(as_of[:4]) - 1, w0[0][4:])
        cur_end = "%d%s" % (int(cur_start[:4]) + 1, w0[1][4:])
        inside = cur_start <= as_of <= cur_end
        perf = None
        if conn is not None:
            # 参与者从该题材的事件读取（去重）
            theme_doc = None
            for entry in idx["maps"]:
                if entry["theme_id"] != t["theme_id"]:
                    continue
                theme_doc = json.load(open(os.path.join(CURRENT, entry["file"]), encoding="utf-8"))
                break
            sids = [p["security_id"] for e in (theme_doc or {}).get("events", [])
                    for p in (e.get("participants") or [])]
            sids = sorted(set(sids))
            # ★★ v0.59 修复（Wave 2.3）：原实现有两个口径错误 ——
            #   ① 基准固定取「as_of 最近 21 根」，而参与者可能停在几个月前 →
            #      两段窗口**完全不重叠**，「超额」在口径上不成立；
            #   ② `price_as_of` 取**全库** raw 最大日（往往是基准自己的最新日），
            #      会把「参与者其实停在 2026-01-30」显示成「行情截至 2026-10-23」。
            #   现改为：基准按**参与者自己的首末日**取；`price_as_of` 取**实际参与计算的那些序列
            #   中最早的末日**；并对「末日距 as_of 超过 MAX_STALE_TRADING_DAYS 个交易日」的参与者
            #   直接剔除并计数（不参与中位数，不补造）。
            ex, used_last, used_win, stale_sids = [], [], [], []
            for sid in sids:
                rows = conn.execute(
                    "SELECT trade_date, close FROM market_daily WHERE series_id=? AND price_type='raw' "
                    "AND trade_date<=? ORDER BY trade_date DESC LIMIT 21", (sid, as_of)).fetchall()
                if len(rows) < 21:
                    continue
                d0, d1 = rows[-1][0], rows[0][0]
                # 交易日间隔（用基准自身的交易日计数，避免把自然日当交易日）
                gap = conn.execute(
                    "SELECT COUNT(*) FROM market_daily WHERE series_id='SH000300' AND price_type='raw' "
                    "AND trade_date>? AND trade_date<=?", (d1, as_of)).fetchone()[0]
                if gap > MAX_STALE_TRADING_DAYS:
                    stale_sids.append(sid)
                    continue
                # ★ 基准必须落在**同一段**日期上（参与者自己的首末日）
                brows = conn.execute(
                    "SELECT trade_date, close FROM market_daily WHERE series_id='SH000300' AND price_type='raw' "
                    "AND trade_date BETWEEN ? AND ? ORDER BY trade_date", (d0, d1)).fetchall()
                if len(brows) < 2 or brows[0][0] != d0 or brows[-1][0] != d1:
                    continue
                r = rows[0][1] / rows[-1][1] - 1
                b = brows[-1][1] / brows[0][1] - 1
                ex.append((r - b) * 100)
                used_last.append(d1)
                used_win.append((d0, d1))
            if ex:
                # ★★ price_as_of = **实际参与计算的序列里最早的末日**（不是全库最大值）
                last = min(used_last)
                perf = {"participants_with_data": len(ex),
                        "participants_total": len(sids),
                        "stale_participants": len(stale_sids),
                        "median_20d_excess_pct": round(statistics.median(ex), 2),
                        "breadth_20d": round(sum(1 for x in ex if x > 0) / len(ex), 3),
                        "price_as_of": last,
                        "stale": bool(last and last < as_of),
                        "stale_note": (None if (last and last >= as_of) else
                                       "★ 参与计算的序列最早只到 %s，早于观察时点 %s —— "
                                       "不得据此断言「已升温/前置观察」" % (last, as_of)),
                        # ★ 参与者 20 日窗口的并集（基准按每只参与者自己的这段日期对齐）
                        "participants_window": ([min(x[0] for x in used_win), max(x[1] for x in used_win)]
                                                if used_win else None),
                        "stale_participants_note": (
                            ("★ 另有 %d 只参与者因行情落后 >%d 个交易日被**剔除**（不参与中位数、不补造）"
                             % (len(stale_sids), MAX_STALE_TRADING_DAYS)) if stale_sids else None)}
        out.append({
            "theme_id": t["theme_id"], "label": t["label"],
            "occurrence_count": len(t["events"]),
            "events": t["events"],
            "projected_window": [cur_start, cur_end],
            "as_of_inside": inside,
            "current_performance": perf,
            "data_note": ("参与者 20 日超额来自 market_data.db（**原始收盘**，基准按参与者同一段日期对齐）；"
                          "`price_as_of` = 实际参与计算的序列中最早的末日，落后过多的参与者被剔除并计数"),
        })
    if conn is not None:
        conn.close()
    return {"source": "既有历史题材产物（market_performance.window）+ market_data.db",
            "criterion": "窗口起始月 ∈ {8,9,10} 且结束月 ∈ {12,1,2}，且同题材 ≥2 个事件",
            "themes": out}


def select_candidates(doc: dict) -> list:
    """以 `as_of` 为硬截止，从**已验证模式 + 现有历史研究**里挑少量当前窗口候选。

    ★ 只输出「有时间优势」的：窗口尚未结束或尚未开始；已经大幅上涨的不列。
    """
    as_of = doc["as_of"]
    out = []
    z = next(p for p in doc["patterns"] if p["pattern_id"] == "ZODIAC_NAME")
    nxt = next((y for y in z["years"] if y["year"] == 2027), None)
    if nxt:
        out.append({
            "candidate_id": "CAND-ZODIAC-2027",
            "title": "2027 羊年「生肖名称」窗口（前置观察）",
            "window": {"start": "2026-12-15", "peak": nxt["lunar_new_year"], "end": "2027-03-05"},
            "why_now": "距下一个农历新年（%s）约 4 个月，历史上该窗口的观察点在春节前 20 个交易日。"
                       % nxt["lunar_new_year"],
            "historical_stats": z["stats"],
            "evidence_status": "INSUFFICIENT",
            "not_a_candidate_reason": (
                "★ 当前名称里含「羊」的只有 %d 只 → **无法构成篮子**，本轮不列为可执行候选。"
                % nxt["name_matches"]),
            "what_to_watch": "是否有新的「羊」字证券上市/改名，以及节前 20 个交易日的板块成交与涨停分布。",
            "invalidate_if": "春节前 20 个交易日篮子中位超额 ≤ 0 且广度 < 0.5。",
            "fact_vs_assumption": {"fact": "农历新年日期与名称匹配数量为计算事实",
                                   "assumption": "「生肖符号炒作」在 2027 年仍会重演 —— 未验证"},
        })
    sw = doc.get("seasonal_windows") or {}
    for t in sw.get("themes", []):
        if not t.get("as_of_inside"):
            continue
        perf = t.get("current_performance") or {}
        med = perf.get("median_20d_excess_pct")
        out.append({
            "candidate_id": "CAND-SEASONAL-%s" % t["theme_id"],
            "title": "%s · 秋冬窗口（%s → %s）" % (t["label"], t["projected_window"][0], t["projected_window"][1]),
            "window": {"start": t["projected_window"][0], "peak": None, "end": t["projected_window"][1]},
            "why_now": "as_of %s 落在该题材历史上反复出现的秋冬窗口内（同题材 %d 个事件）。"
                       % (as_of, t["occurrence_count"]),
            "historical_stats": {"occurrence_count": t["occurrence_count"],
                                 "sample_windows": [e["window"] for e in t["events"]]},
            "current_performance": perf,
            "evidence_status": ("DATA_STALE" if (perf or {}).get("stale")
                                else "UNKNOWN" if med is None
                                else "PRE_OBSERVATION" if med < 10 else "ALREADY_WARM"),
            "what_to_watch": "窗口内该题材参与者的 20 日超额与广度是否转正；是否出现可核实的前置催化（带发布日）。",
            "invalidate_if": "窗口结束前中位超额 ≤ 0 且广度 < 0.5。",
            "fact_vs_assumption": {
                "fact": "窗口日期、事件数与当前 20 日超额为计算事实",
                "assumption": "该秋冬窗口在 2026–27 会重复出现 —— 仅 %d 个历史事件支持，证据不足" % t["occurrence_count"],
            },
        })
    s = next(p for p in doc["patterns"] if p["pattern_id"] == "TAIWAN_STRAIT_EVENT")
    out.append({
        "candidate_id": "CAND-STRAIT-WATCH",
        "title": "台海事件 → 海峡西岸概念（事件驱动，无常设窗口）",
        "window": {"start": None, "peak": None, "end": None},
        "why_now": "无固定日历；只有出现新的可核实事件（政策表态 / 演训 / 交流）时才进入观察窗口。",
        "historical_stats": s["stats"],
        "evidence_status": "WATCH_ONLY",
        "not_a_candidate_reason": "as_of 之前没有已公开、且尚未发生的台海事件 → 当前**没有时间优势**。",
        "what_to_watch": "官方公告/演训通告的**发布日**（不是传闻日）；事件后 1–20 个交易日概念篮子相对沪深300的超额与广度。",
        "invalidate_if": "事件后 20 个交易日中位超额 ≤ 0 或广度 < 0.5。",
        "fact_vs_assumption": {"fact": "历史事件的窗口超额为计算事实",
                               "assumption": "同一概念会对下一次事件重复响应 —— 仅部分支持"},
    })
    return out


def artifact_path(version=None):
    files = [f for f in os.listdir(CURRENT) if OUT_RE.match(f)]
    if version is not None:
        return os.path.join(CURRENT, "forward_observation_v0_%d.json" % version)
    if not files:
        return os.path.join(CURRENT, "forward_observation_v0_1.json")
    files.sort(key=lambda f: int(OUT_RE.match(f).group(1)))
    return os.path.join(CURRENT, files[-1])


def check(doc: dict) -> list:
    """产物自检（不联网）：口径一致性 + 三段窗口独立 + PIT 截止。"""
    errs = []
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", doc.get("as_of", "")):
        errs.append("as_of 缺失或格式错")
    for p in doc["patterns"]:
        st = p.get("stats") or {}
        if p["pattern_id"] == "ZODIAC_NAME":
            tested = [y for y in p.get("years", []) if (y.get("window") or {}).get("status") == "OK"]
            resp = [y for y in tested if y["window"].get("responded") is True]
        else:
            tested = [e for e in p.get("events", []) if (e.get("window") or {}).get("status") == "OK"]
            resp = [e for e in tested if e.get("responded") is True]
            stages = p.get("stages") or []
            if not stages:
                errs.append("%s 缺事件阶段（不能只给原始事件）" % p["pattern_id"])
            if st.get("occurrence_count") != len(stages):
                errs.append("%s occurrence_count 应按**阶段**统计" % p["pattern_id"])
        for e in tested:
            w = e["window"]
            for k in ("pre", "event_day", "post"):
                if k not in w:
                    errs.append("%s 缺 %s 段（三段口径必须独立）" % (e.get("event_id") or e.get("year"), k))
            # ★ responded 只能由 post20 决定
            p20 = (w.get("post") or {}).get("post20") or {}
            if p20.get("status") == "OK":
                expect = bool((p20.get("median_excess_pct") or 0) > 0 and (p20.get("breadth") or 0) >= 0.5)
                if e.get("responded") is not expect:
                    errs.append("%s responded 与 post20 不一致" % (e.get("event_id") or e.get("year")))
        if p["pattern_id"] == "ZODIAC_NAME" and st.get("response_rate") is not None and tested:
            if abs(st["response_rate"] - round(len(resp) / len(tested), 3)) > 1e-9:
                errs.append("%s response_rate 与明细不一致" % p["pattern_id"])
        if not p.get("known_biases"):
            errs.append("%s 缺 known_biases" % p["pattern_id"])
    for p in doc["patterns"]:
        for e in p.get("events", []):
            if e["event_date"] > doc["as_of"]:
                errs.append("%s 事件日晚于 as_of" % e["event_id"])
            w = e.get("window") or {}
            if w.get("status") == "OK":
                for seg in [w.get("pre") or {}, w.get("event_day") or {}] + \
                           list((w.get("post") or {}).values()):
                    win = seg.get("window")
                    if win and win[1] > doc["as_of"]:
                        errs.append("%s 窗口结束晚于 as_of（用了未来数据）" % e["event_id"])
    # ★ 数据新鲜度：stale 的候选不得给出「已升温 / 前置观察」
    for c in doc.get("candidates", []):
        perf = c.get("current_performance") or {}
        if perf.get("stale") and c.get("evidence_status") in ("ALREADY_WARM", "PRE_OBSERVATION"):
            errs.append("%s 行情陈旧却给了结论状态" % c["candidate_id"])
    return errs


def main(argv):
    ap = argparse.ArgumentParser(description="当前前瞻观察（历史重复模式 + 当前窗口）")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--version", type=int, default=None)
    a = ap.parse_args(argv)

    if a.check:
        path = artifact_path()
        if not os.path.exists(path):
            print("FAIL: 产物不存在：%s" % os.path.relpath(path, REPO))
            return 1
        doc = json.load(open(path, encoding="utf-8"))
        errs = check(doc)
        if errs:
            print("FAIL: 前瞻观察产物不满足口径（%d 条）：" % len(errs))
            for e in errs[:8]:
                print("  · " + e)
            return 1
        print("PASS: 前瞻观察产物一致（as_of %s · 模式 %d · 候选 %d）"
              % (doc["as_of"], len(doc["patterns"]), len(doc["candidates"])))
        return 0

    doc = build(fetch=a.fetch)
    doc["candidates"] = select_candidates(doc)
    errs = check(doc)
    if errs:
        print("FAIL: 口径自检不通过：%s" % errs[:5])
        return 1

    if not a.write:
        print(json.dumps({"as_of": doc["as_of"], "patterns": [
            {"id": p["pattern_id"], "status": p["status"], "stats": p["stats"]} for p in doc["patterns"]],
            "candidates": [c["candidate_id"] for c in doc["candidates"]]},
            ensure_ascii=False, indent=1))
        return 0

    if a.version is None:
        print("FAIL: --write 必须显式给 --version N")
        return 1
    out = artifact_path(a.version)
    os.makedirs(SNAP_DIR, exist_ok=True)
    snap = os.path.join(SNAP_DIR, "FO-%s-%s.json" % (doc["as_of"], doc.get("method_version", "v0_3")))
    # ★★ 先确认两个路径都可用，再写任何一个
    for path in (out, snap):
        if os.path.exists(path):
            print("FAIL: 目标已存在，拒绝覆盖：%s" % os.path.relpath(path, REPO))
            return 1
    doc["artifact_version"] = "0.%d" % a.version
    if a.version > 1:
        doc["supersedes"] = "research/current/forward_observation_v0_%d.json" % (a.version - 1)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    with open(snap, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    print("已生成 %s" % os.path.relpath(out, REPO))
    print("      快照 %s" % os.path.relpath(snap, REPO))
    for p in doc["patterns"]:
        print("  模式 %-20s %-14s %s" % (p["pattern_id"], p["status"], p["stats"]))
    print("  候选 %d 个：%s" % (len(doc["candidates"]), [c["candidate_id"] for c in doc["candidates"]]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
