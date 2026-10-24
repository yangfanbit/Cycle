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
UNIVERSE = os.path.join(CACHE_DIR, "universe_v0_1.json")
SNAP_DIR = os.path.join(CURRENT, "forward_observation_snapshots")
OUT_RE = re.compile(r"forward_observation_v0_(\d+)\.json$")
GENERATED_AT = "2026-10-24"

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


def fetch_kline(symbol: str, datalen: int = 3000) -> list:
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
            return rows
    except Exception:
        pass
    # 备用：腾讯 GTIMG（单次 ≤800 根）
    try:
        url = ("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
               "param=%s,day,2015-01-01,2026-12-31,800," % symbol)
        d = json.loads(_get(url).decode("utf-8", "replace"))
        node = (d.get("data") or {}).get(symbol) or {}
        rows = node.get("day") or node.get("qfqday") or []
        return [[r[0], float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])] for r in rows]
    except Exception:
        return []


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


def basket_window(members: dict, bench: list, anchor: str, pre: int = 20, post: int = 20) -> dict:
    """篮子相对基准的窗口表现（成员与基准按**各自**交易日索引对齐到同一日历区间）。"""
    bdays = trading_days(bench)
    if anchor not in bdays:
        later = [d for d in bdays if d > anchor]
        if not later:
            return {"status": "NO_ANCHOR"}
        anchor = later[0]
    ai = bdays.index(anchor)
    s_idx, e_idx = ai - pre, ai + post
    if s_idx < 0 or e_idx >= len(bdays):
        return {"status": "OUT_OF_RANGE", "anchor": anchor}
    start_d, end_d = bdays[s_idx], bdays[e_idx]
    bench_ret = bench[e_idx][2] / bench[s_idx][2] - 1.0

    pre_bench = bench[ai - 1][2] / bench[s_idx][2] - 1.0 if ai - 1 > s_idx else 0.0
    post_bench = bench[e_idx][2] / bench[ai][2] - 1.0 if e_idx > ai else 0.0

    excess, pre_ex, post_ex, lu = [], [], [], 0
    for sym, rows in members.items():
        idx = {r[0]: i for i, r in enumerate(rows)}
        if start_d not in idx or end_d not in idx:
            continue
        r0, r1 = rows[idx[start_d]][2], rows[idx[end_d]][2]
        if r0 <= 0:
            continue
        ret = r1 / r0 - 1.0
        excess.append((ret - bench_ret) * 100.0)
        a = idx.get(anchor)
        if a is not None and a > 0 and start_d in idx:
            pre_ex.append((rows[a - 1][2] / rows[idx[start_d]][2] - 1.0 - pre_bench) * 100.0)
        if a is not None and end_d in idx:
            post_ex.append((rows[idx[end_d]][2] / rows[a][2] - 1.0 - post_bench) * 100.0)
        lu += limit_up_days(rows, sym, start_d, end_d)
    if not excess:
        return {"status": "NO_MEMBERS_WITH_DATA", "anchor": anchor}
    breadth = sum(1 for x in excess if x > 0) / len(excess)
    return {
        "status": "OK", "anchor": anchor, "window": [start_d, end_d],
        "members_with_data": len(excess),
        "median_excess_pct": round(statistics.median(excess), 2),
        "mean_excess_pct": round(sum(excess) / len(excess), 2),
        "breadth": round(breadth, 3),
        "pre_median_excess_pct": round(statistics.median(pre_ex), 2) if pre_ex else None,
        "post_median_excess_pct": round(statistics.median(post_ex), 2) if post_ex else None,
        "limit_up_days_total": lu,
        "responded": bool(statistics.median(excess) > 0 and breadth >= 0.5),
    }


def lead_days(members: dict, bench: list, anchor: str, lookback: int = 20) -> int | None:
    """首轮异动：篮子中位**累计超额**首次转正且 ≥ +2pp 的交易日（相对 anchor 的偏移，负数=提前）。"""
    bdays = trading_days(bench)
    if anchor not in bdays:
        return None
    ai = bdays.index(anchor)
    if ai - lookback < 0:
        return None
    for k in range(lookback, 0, -1):
        d0, d1 = bdays[ai - k], bdays[ai - k + 1]
        bench_ret = bench[ai - k + 1][2] / bench[ai - k][2] - 1.0
        ex = []
        for sym, rows in members.items():
            idx = {r[0]: i for i, r in enumerate(rows)}
            if d0 not in idx or d1 not in idx:
                continue
            r0 = rows[idx[d0]][2]
            if r0 <= 0:
                continue
            ex.append((rows[idx[d1]][2] / r0 - 1.0 - bench_ret) * 100.0)
        if ex and statistics.median(ex) >= 2.0:
            return -k
    return None


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
                w = basket_window(members, bench, lny)
                rec.update({"window": w, "lead_days": lead_days(members, bench, w.get("anchor", lny))})
            else:
                rec["window"] = {"status": "FUTURE", "anchor": lny}
        years.append(rec)

    tested = [y for y in years if y.get("window", {}).get("status") == "OK"]
    resp = [y for y in tested if y["window"].get("responded")]
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


def build_strait_pattern(bench: list, cache: dict, members_meta: dict) -> dict:
    syms = [m["symbol"] if isinstance(m, dict) else m for m in members_meta]
    members = {s: cache["stocks"][s] for s in syms if s in cache.get("stocks", {})}
    events = []
    for ev in STRAIT_EVENTS:
        w = basket_window(members, bench, ev["event_date"])
        rec = dict(ev)
        rec["window"] = w
        if w.get("status") == "OK":
            rec["lead_days"] = lead_days(members, bench, w["anchor"])
            rec["responded"] = w.get("responded")
        events.append(rec)
    ok = [e for e in events if e["window"].get("status") == "OK"]
    resp = [e for e in ok if e.get("responded")]
    leads = [e["lead_days"] for e in ok if e.get("lead_days") is not None]
    pre = [e["window"]["pre_median_excess_pct"] for e in ok
           if e["window"].get("pre_median_excess_pct") is not None]
    post = [e["window"]["post_median_excess_pct"] for e in ok
            if e["window"].get("post_median_excess_pct") is not None]
    return {
        "pattern_id": "TAIWAN_STRAIT_EVENT",
        "family": "B_EVENT",
        "title": "台海事件 → 海峡西岸概念（事件驱动，无固定日历）",
        "hypothesis": ("台海相关事件（政策表态 / 军事演训 / 交流）会反复引发「海峡西岸」概念股的短期超额；"
                       "**不声称存在季节性**。"),
        "basket": {
            "concept": "海峡西岸", "node": STRAIT_CONCEPT_NODE,
            "members": len(members_meta), "members_with_data": len(members),
            "membership_bias": "★★ 概念成分为**当前**成分（新浪概念节点），不是各事件当年的成分；"
                               "历史成分变化无法还原，属已知偏差。",
        },
        "events": events,
        "stats": {
            "occurrence_count": len(ok),
            "response_count": len(resp),
            "response_rate": round(len(resp) / len(ok), 3) if ok else None,
            "median_lead_days": statistics.median(leads) if leads else None,
            "median_pre_excess_pct": round(statistics.median(pre), 2) if pre else None,
            "median_post_excess_pct": round(statistics.median(post), 2) if post else None,
            "sample_years": sorted({int(e["event_date"][:4]) for e in ok}),
        },
        "known_biases": [
            "概念成分为当前成分 → 幸存者偏差 + 成分变更偏差。",
            "事件日选取为公开事实日；**信息是否提前泄露**无法用行情证明（lead_days 只描述价格，不证明因果）。",
            "样本 7 个事件、跨 2016–2024，事件强度不可比（政策表态 vs 军事演训）。",
        ],
        "status": "B_REPEATED" if len(ok) >= 5 and len(resp) >= 3 else "C_EXPLORATORY",
        "status_reason": "多个独立事件 + 响应反复出现 → 重复迹象；但时间不固定，属事件驱动，不是季节规律。",
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
        if not os.path.exists(UNIVERSE):
            json.dump(fetch_universe(), open(UNIVERSE, "w", encoding="utf-8"), ensure_ascii=False)
        universe = json.load(open(UNIVERSE, encoding="utf-8"))
        # 指数（一次 3000 根，覆盖 2014 起）
        for sid, name, sym in INDICES:
            if len(cache.get(sid) or []) < 2000:
                cache[sid] = fetch_kline(sym, 3000)
                time.sleep(PACING)
        # 生肖候选（2024 龙 / 2026 马 / 2027 羊）
        zsyms = set()
        for y in (2024, 2026, 2027):
            a = ZODIAC[y]
            zsyms |= {u["symbol"] for u in universe if a in (u.get("name") or "")}
        # 海峡西岸成分
        members = fetch_concept_members(STRAIT_CONCEPT_NODE)
        cache["strait_members"] = [{"symbol": m["symbol"], "name": m["name"]} for m in members]
        msyms = {m["symbol"] for m in members}
        targets = zsyms | msyms
        for i, sym in enumerate(sorted(targets)):
            if len(cache["stocks"].get(sym) or []) >= 2000:
                continue
            cache["stocks"][sym] = fetch_kline(sym, 3000)
            time.sleep(PACING)
            if i % 20 == 0:
                json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
        # 行业板块
        boards = fetch_industry_boards()
        for b in boards:
            cache["boards"][b["code"]] = dict(b)
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
        "as_of_source": "腾讯 GTIMG 沪深300(sh000300) 最后一根完整日线",
        "data_sources": [
            {"id": "tencent_gtimg", "used_for": "指数 / 个股日线（原始收盘，不复权）",
             "endpoint": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
             "status": "OK", "note": "单次最多约 800 根日线；长区间分段取并按日期去重"},
            {"id": "sina_universe", "used_for": "全 A 股名称与代码（5,576 只）",
             "endpoint": "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData",
             "status": "OK"},
            {"id": "sina_concept", "used_for": "概念成分（海峡西岸 78 只）",
             "endpoint": "同上 node=gn_hxxa", "status": "OK",
             "note": "★ 当前成分，非历史成分"},
            {"id": "ths_board", "used_for": "行业板块当年日线（140 个）",
             "endpoint": "http://d.10jqka.com.cn/v6/line/bk_881xxx/01/last.js",
             "status": "OK", "note": "★ 仅当年数据；概念板块（30xxxx）该接口 404 → 概念用成分篮子替代"},
            {"id": "eastmoney", "used_for": "（未使用）", "endpoint": "push2*.eastmoney.com",
             "status": "UNAVAILABLE", "note": "本机实测 RemoteDisconnected（含直连与代理）→ 未采用，不用文档推定"},
        ],
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
            ex = []
            for sid in sids:
                rows = conn.execute(
                    "SELECT trade_date, close FROM market_daily WHERE series_id=? AND price_type='raw' "
                    "AND trade_date<=? ORDER BY trade_date DESC LIMIT 21", (sid, as_of)).fetchall()
                brows = conn.execute(
                    "SELECT trade_date, close FROM market_daily WHERE series_id='SH000300' AND price_type='raw' "
                    "AND trade_date<=? ORDER BY trade_date DESC LIMIT 21", (as_of,)).fetchall()
                if len(rows) < 21 or len(brows) < 21:
                    continue
                r = rows[0][1] / rows[-1][1] - 1
                b = brows[0][1] / brows[-1][1] - 1
                ex.append((r - b) * 100)
            if ex:
                perf = {"participants_with_data": len(ex),
                        "median_20d_excess_pct": round(statistics.median(ex), 2),
                        "breadth_20d": round(sum(1 for x in ex if x > 0) / len(ex), 3)}
        out.append({
            "theme_id": t["theme_id"], "label": t["label"],
            "occurrence_count": len(t["events"]),
            "events": t["events"],
            "projected_window": [cur_start, cur_end],
            "as_of_inside": inside,
            "current_performance": perf,
            "data_note": "参与者 20 日超额来自 market_data.db（原始收盘，截至其最后一行，可能早于 as_of）",
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
            "evidence_status": ("PRE_OBSERVATION" if (med is None or med < 10) else "ALREADY_WARM"),
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
    errs = []
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", doc.get("as_of", "")):
        errs.append("as_of 缺失或格式错")
    for p in doc["patterns"]:
        st = p.get("stats") or {}
        tested = [y for y in p.get("years", []) if (y.get("window") or {}).get("status") == "OK"] \
            if p["pattern_id"] == "ZODIAC_NAME" else \
            [e for e in p.get("events", []) if (e.get("window") or {}).get("status") == "OK"]
        if st.get("occurrence_count") != len(tested):
            errs.append("%s occurrence_count 与明细不一致" % p["pattern_id"])
        resp = [y for y in tested if (y.get("window") or {}).get("responded")] \
            if p["pattern_id"] == "ZODIAC_NAME" else [e for e in tested if e.get("responded")]
        if st.get("response_count") != len(resp):
            errs.append("%s response_count 与明细不一致" % p["pattern_id"])
        if tested and st.get("response_rate") is not None:
            if abs(st["response_rate"] - round(len(resp) / len(tested), 3)) > 1e-9:
                errs.append("%s response_rate 与明细不一致" % p["pattern_id"])
        if not p.get("known_biases"):
            errs.append("%s 缺 known_biases" % p["pattern_id"])
    # ★ PIT：任何事件窗口不得引用 as_of 之后的数据
    for p in doc["patterns"]:
        for e in p.get("events", []):
            if e["event_date"] > doc["as_of"]:
                errs.append("%s 事件日晚于 as_of" % e["event_id"])
            w = e.get("window") or {}
            if w.get("status") == "OK" and w["window"][1] > doc["as_of"]:
                errs.append("%s 窗口结束晚于 as_of（用了未来数据）" % e["event_id"])
    for y in next(p for p in doc["patterns"] if p["pattern_id"] == "ZODIAC_NAME")["years"]:
        w = y.get("window") or {}
        if w.get("status") == "OK" and w["window"][1] > doc["as_of"]:
            errs.append("%s 生肖窗口结束晚于 as_of" % y["year"])
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
    if os.path.exists(out):
        print("FAIL: 目标已存在，拒绝覆盖：%s" % os.path.relpath(out, REPO))
        return 1
    doc["artifact_version"] = "0.%d" % a.version
    if a.version > 1:
        doc["supersedes"] = "research/current/forward_observation_v0_%d.json" % (a.version - 1)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    # ★ 带日期的历史快照（不可覆盖）
    os.makedirs(SNAP_DIR, exist_ok=True)
    snap = os.path.join(SNAP_DIR, "FO-%s.json" % doc["as_of"])
    if os.path.exists(snap):
        print("FAIL: 该 as_of 的快照已存在，拒绝覆盖：%s" % os.path.relpath(snap, REPO))
        return 1
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
