#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_new_theme_radar_v0_1.py —— 「自动发现的新题材线索」第一版（v0.66）。

## 它做什么

从**公开、可核验、无需 API Key** 的政策发布页采集**带日期的真实事件**，规范化成事件记录，
按**显式关键词表**关联到已有行业板块序列，再用真实行情核验事件附近的市场反应，
最后按**可解释规则**判定「是否构成新题材线索」。

```
公开事件 → 规范化事件 → 题材/板块关联 → 市场反应核验 → 新题材候选 → 产品展示
```

## 三条硬边界（写进代码，不靠口头约定）

1. **不猜**：题材/板块关联只来自 `THEME_KEYWORDS` 的**逐字短语匹配**，每条都带 `rationale`；
   不做子串模糊匹配（会把「电力设备」错配到「电力」、把「智元机器人」错配到新松机器人）。
2. **不补**：行情缺失 / 交易日不足 / 板块无序列 → 一律写 `status` 与 `gaps`，**不补 0、不插值**；
   板块无历史成分 → 参与广度记为 `null` 并说明「无法计算」，不拿当前成分替代。
3. **不推荐**：输出是「**线索**」，不含评分 / 概率 / 排序收益 / 买卖信号；
   `is_candidate` 只是「值得人工看一眼」的机械筛选，不是预测。

## 覆盖范围（第一版，如实）

- **单一来源**：国家发展改革委 · 新闻发布（`/xwdt/xwfb/`），HTML 服务端渲染、带 `title` 与日期。
- **单一类别**：`POLICY_RELEASE`（政策/公告/价格机制类发布）。
- 时间范围 = 抓到的列表页覆盖区间（见产物 `coverage.date_range`）。
- 已知不可得：**参与广度**（行业板块无历史成分）、**证券映射**（首版不做个股级映射）。

## 用法

```
python research/scripts/build_new_theme_radar_v0_1.py --fetch --write --version 1
python research/scripts/build_new_theme_radar_v0_1.py --check        # 只读，不联网
```
"""
from __future__ import annotations

import argparse, hashlib, json, os, re, sqlite3, sys, time, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
OUT_RE = re.compile(r"new_theme_radar_v0_(\d+)\.json$")
SCAN_DB = os.path.join(REPO, "research", "database", "history_scan.db")

# ─────────────────────────── 事件源（两个栏目，同属发改委） ───────────────────────────
# 两个栏目都是**服务端渲染的公开 HTML 列表**（无需登录 / API Key），且都带发布日期与标题。
# 只做这两个栏目：不做全市场新闻挖掘，覆盖范围在产物 `coverage` 里如实标注。
SOURCES = [
    {
        "id": "NDRC_ZCFB_TZ",
        "name": "国家发展改革委 · 政策通知",
        "publisher": "国家发展改革委",
        "list_url": "https://www.ndrc.gov.cn/xxgk/zcfb/tz/",
        "pages": ["", "index_1.html"],
        "category": "POLICY_NOTICE",
        "access_note": "公开 HTML 列表页（服务端渲染），逐条回抓详情页取原文片段",
    },
    {
        "id": "NDRC_XWFB",
        "name": "国家发展改革委 · 新闻发布",
        "publisher": "国家发展改革委",
        "list_url": "https://www.ndrc.gov.cn/xwdt/xwfb/",
        "pages": ["", "index_1.html"],
        "category": "POLICY_NEWS",
        "access_note": "公开 HTML 列表页（服务端渲染），逐条回抓详情页取原文片段",
    },
]

# ─────────────────── 显式关键词 → 板块（逐字匹配，每条带依据） ───────────────────
# relation: DIRECT = 政策直接作用于该环节；PROXY = 首版用相近板块代理（须说明）
THEME_KEYWORDS = [
    ("成品油价格", "BK881180", "石油加工贸易", "DIRECT",
     "发改委成品油价格调控直接作用于炼化与成品油销售环节"),
    ("油价", "BK881180", "石油加工贸易", "DIRECT",
     "成品油/原油价格机制调整作用于炼化环节"),
    ("电价", "BK881145", "电力", "DIRECT",
     "电价机制与输配电价调整直接影响发电侧收入"),
    ("电力市场", "BK881145", "电力", "DIRECT",
     "电力市场规则变动影响发电与售电主体"),
    ("光伏", "BK881279", "光伏设备", "DIRECT",
     "光伏政策与装机目标直接作用于设备端"),
    ("风电", "BK881280", "风电设备", "DIRECT",
     "风电政策与装机目标直接作用于设备端"),
    ("储能", "BK881281", "电池", "PROXY",
     "储能支持政策主要作用于电池环节；首版用「电池」板块代理，非储能专营板块"),
    ("算力", "BK881162", "通信服务", "PROXY",
     "算力/数据中心政策主要作用于 IDC 与通信服务；首版用「通信服务」代理"),
    ("半导体", "BK881121", "半导体", "DIRECT",
     "集成电路政策直接作用于半导体板块"),
    ("集成电路", "BK881121", "半导体", "DIRECT",
     "集成电路政策直接作用于半导体板块"),
    ("新能源汽车", "BK881125", "汽车整车", "DIRECT",
     "新能源汽车政策直接作用于整车环节"),
]

# ─────────────────────────── 判定规则（v0.1，冻结在产物里） ───────────────────────────
RULES = {
    "reaction_trading_days": 3,      # 事件日之后再看 3 个交易日（反应窗口 = 事件日 + 3）
    "min_observation_trading_days": 3,
    "max_event_age_days": 45,
    "candidate_requires": [
        "有逐字关键词命中的板块关联（THEME_KEYWORDS）",
        "行情可核验：observation_trading_days >= 3",
        "板块相对基准超额 > 0（方向与事件一致）",
        "event_date 距 as_of <= 45 天",
    ],
    "not_scored": "不含打分 / 概率 / 收益排序 / 交易信号；is_candidate 只是机械筛选，需人工复核",
}

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ThreeC-research/0.1"}


def iso(d):
    if not d:
        return None
    d = str(d)[:10]
    return "%s-%s-%s" % (d[:4], d[4:6], d[6:8]) if "-" not in d else d


def _get(url, retries=2):
    last = None
    for i in range(retries + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:      # 网络错误一律如实返回 None，由上层记 gaps
            last = e
            time.sleep(1.0 + i)
    print("  WARN 取数失败 %s（%s）" % (url, type(last).__name__), file=sys.stderr)
    return None


def _parse_list(html, list_url, source_id):
    """★ 宽容解析：不同栏目里 `<span>日期</span>` 与 `</a>` 之间可能夹 `<script>`，
    所以按 `<li>` 块整体取 `<a>` 与 `<span>`，不依赖两者相邻。"""
    out = []
    for block in re.findall(r"<li[^>]*>(.*?)</li>", html, re.S):
        a = re.search(r'<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"', block, re.S)
        d = re.search(r"<span[^>]*>\s*(\d{4})[/-](\d{1,2})[/-](\d{1,2})\s*</span>", block)
        if not (a and d):
            continue
        href = a.group(1)
        full = href if href.startswith("http") else list_url + href.lstrip("./")
        out.append({"title": _clean(a.group(2)), "url": full,
                    "date": "%s-%02d-%02d" % (d.group(1), int(d.group(2)), int(d.group(3))),
                    "source_id": source_id})
    return out


def fetch_list():
    """返回 (items, fetched)；原始列表页字节数记入 `coverage.pages_fetched` 便于复核。"""
    items, fetched = [], []
    for src in SOURCES:
        for p in src["pages"]:
            url = src["list_url"] + p
            h = _get(url)
            if not h:
                continue
            got = _parse_list(h, src["list_url"], src["id"])
            fetched.append({"source": src["id"], "url": url, "bytes": len(h), "items": len(got)})
            items.extend(got)
            time.sleep(1.2)
    # 去重：同一 URL 只留一条（两个栏目可能互相转载 / 翻页重叠）
    seen, uniq = set(), []
    for it in items:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        uniq.append(it)
    return uniq, fetched


def _clean(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
    return re.sub(r"\s+", " ", s).strip()


def fetch_quote(url):
    """回抓详情页取正文片段（`div.article_con`）；取不到就返回 None（不编造）。"""
    h = _get(url)
    if not h:
        return None, None
    m = re.search(r'<div[^>]*class="[^"]*article_con[^"]*"[^>]*>(.*?)</div>', h, re.S)
    txt = _clean(m.group(1)) if m else ""
    if not txt:
        # 退化：去标签后取第一段 >60 字的中文
        t = re.sub(r"<script.*?</script>", "", h, flags=re.S)
        t = _clean(re.sub(r"<[^>]+>", " ", t))
        for seg in re.split(r"[。！？]", t):
            if len(seg) >= 60:
                txt = seg.strip() + "。"
                break
    return (txt[:300] or None), hashlib.sha256(txt.encode("utf-8")).hexdigest()[:16] if txt else None


def theme_links(title, quote):
    """逐字短语匹配；每条带 rationale 与命中位置（标题 / 原文）。不猜、不模糊。"""
    out, seen = [], set()
    for kw, sid, sname, rel, why in THEME_KEYWORDS:
        where = "TITLE" if kw in (title or "") else ("QUOTE" if kw in (quote or "") else None)
        if not where:
            continue
        key = (sid, kw)
        if key in seen:
            continue
        seen.add(key)
        out.append({"keyword": kw, "matched_in": where, "board_series": sid, "board_name": sname,
                    "relation": rel, "rationale": why})
    return out


def _cal(con):
    """交易日历：优先用 CSI300 自身日期序列（`trading_calendar` 可能落后）。"""
    return sorted({(r[0] if "-" in r[0] else "%s-%s-%s" % (r[0][:4], r[0][4:6], r[0][6:]))
                   for r in con.execute("SELECT trade_date FROM scan_daily WHERE series_id='CSI300'")})


def market_of(con, cal, sid, event_date, as_of):
    """★ 事件窗口行情 = **反应窗口**（不是「事件日到最新」）。

    基准 = 事件日**前一交易日**收盘；反应末日 = 事件日之后第 `reaction_trading_days` 个交易日
    （不足则截至 as_of）。这样「市场反应」不会被后面几个月的趋势稀释；
    事件至今的整体漂移另记在 `drift` 里，两者不混。
    """
    res = {"board_series": sid, "as_of": as_of, "window": None, "board_ret_pct": None,
           "bench_ret_pct": None, "excess_pp": None, "observation_trading_days": None,
           "breadth": None, "status": "INSUFFICIENT", "gaps": []}
    if not cal:
        res["gaps"].append("无交易日历（history_scan.db 不可用）")
        return res
    # 事件日 = 首个 >= event_date 的交易日；基准 = 它之前的那个交易日
    after = [d for d in cal if d >= event_date]
    if not after:
        res["gaps"].append("事件日晚于库内最后交易日")
        return res
    first = after[0]
    idx = cal.index(first)
    if idx == 0:
        res["gaps"].append("事件日之前没有交易日 → 无法取基准收盘")
        return res
    base_day = cal[idx - 1]
    last = min(as_of, cal[-1])
    if last < first:
        res["gaps"].append("as_of 早于事件日")
        return res
    # 反应窗口：事件日 + reaction_trading_days 个交易日，不足则截至 as_of
    target = min(idx + RULES["reaction_trading_days"], cal.index(last))
    end_day = cal[target]
    obs_days = target - idx + 1                      # 含事件日
    res.update({"window": [base_day, end_day], "observation_trading_days": obs_days,
                "reaction_days_after_event": target - idx})

    def close(series, day):
        """★★ 日期格式陷阱：`industry_board` 存**紧凑** `20261030`，index/stock 存 dashed。
        用 `REPLACE(...)` 归一化后再比，否则板块永远取不到收盘价（会被误读成「数据缺失」）。"""
        r = con.execute(
            "SELECT close FROM scan_daily WHERE series_id=? AND REPLACE(trade_date,'-','')=?",
            (series, day.replace("-", ""))).fetchone()
        return r[0] if r and r[0] else None

    b0, b1 = close(sid, base_day), close(sid, end_day)
    m0, m1 = close("CSI300", base_day), close("CSI300", end_day)
    if None in (b0, b1, m0, m1):
        res["gaps"].append("板块或基准在该窗口缺收盘价 → 不计算收益（不插值）")
        return res
    br = (b1 / b0 - 1) * 100
    mr = (m1 / m0 - 1) * 100
    res.update({"board_ret_pct": round(br, 2), "bench_ret_pct": round(mr, 2),
                "excess_pp": round(br - mr, 2), "status": "OBSERVED"})
    # ★ 事件至今的漂移：**只作背景**，不参与候选判定（否则「反应」会被长期趋势稀释）
    #   ★★ 基准必须取 `last` 当天的收盘 —— 用反应窗口末日的 `m1` 会把漂移的基准算错
    d1, m_last = close(sid, last), close("CSI300", last)
    if None not in (d1, m_last):
        dbr = (d1 / b0 - 1) * 100
        dmr = (m_last / m0 - 1) * 100
        res["drift"] = {"window": [base_day, last], "board_ret_pct": round(dbr, 2),
                        "bench_ret_pct": round(dmr, 2), "excess_pp": round(dbr - dmr, 2),
                        "note": "事件至今的整体漂移，**不参与**候选判定"}
    # ★ 参与广度需要板块历史成分；本库没有 → 明确记为无法计算，不拿当前成分替代
    res["gaps"].append("行业板块无历史成分 → 参与广度无法计算（不以当前成分替代）")
    return res


def classify(event, as_of):
    """状态机（可解释）：NO_THEME_LINK / PENDING_MARKET / INSUFFICIENT / CANDIDATE / WATCH。"""
    links = event["theme_links"]
    mk = event["market"]
    if not links:
        return "NO_THEME_LINK", ["事件标题与原文均未命中显式关键词表 → 不建立板块关联（不猜）"]
    if mk["status"] != "OBSERVED":
        return "INSUFFICIENT", ["行情无法核验：" + "；".join(mk["gaps"] or ["未知原因"])]
    if (mk["observation_trading_days"] or 0) < RULES["min_observation_trading_days"]:
        return "PENDING_MARKET", ["事件后交易日仅 %d 个（< %d）→ 观察窗口不足，暂不判定"
                                  % (mk["observation_trading_days"], RULES["min_observation_trading_days"])]
    from datetime import date
    age = (date.fromisoformat(as_of) - date.fromisoformat(event["event_date"])).days
    if age > RULES["max_event_age_days"]:
        return "WATCH", ["事件已过去 %d 天（> %d）→ 不再作为「新」线索，仅留档"
                         % (age, RULES["max_event_age_days"])]
    if (mk["excess_pp"] or 0) <= 0:
        return "WATCH", ["板块相对基准超额 %+.2fpp ≤ 0 → 市场反应方向与事件不一致，不升级为线索"
                         % (mk["excess_pp"] or 0)]
    return "CANDIDATE", []


SRC_BY_ID = {x["id"]: x for x in SOURCES}


def event_id(url, source_id):
    """`EVT-<来源>-<YYYYMMDD>-<文章号>`；解析不出文章号时用 URL 哈希（可追溯即可）。"""
    m = re.search(r"t(\d{8})_(\d+)\.html", url)
    if m:
        return "EVT-%s-%s-%s" % (source_id.replace("NDRC_", ""), m.group(1), m.group(2))
    return "EVT-%s-%s" % (source_id.replace("NDRC_", ""), hashlib.sha1(url.encode()).hexdigest()[:12])


def build(fetch=False):
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    items, fetched = (fetch_list() if fetch else ([], []))
    if fetch and not items:
        raise SystemExit("FAIL: 列表页未取到任何条目（检查网络 / 页面结构是否变化）")

    con = sqlite3.connect("file:%s?mode=ro" % SCAN_DB, uri=True) if os.path.exists(SCAN_DB) else None
    cal = _cal(con) if con else []
    as_of = cal[-1] if cal else None

    events = []
    for it in items:
        quote, qhash = (fetch_quote(it["url"]) if fetch else (None, None))
        if fetch:
            time.sleep(1.0)
        links = theme_links(it["title"], quote)
        mk = (market_of(con, cal, links[0]["board_series"], it["date"], as_of)
              if (con and links and as_of) else
              {"board_series": links[0]["board_series"] if links else None, "as_of": as_of,
               "window": None, "board_ret_pct": None, "bench_ret_pct": None, "excess_pp": None,
               "observation_trading_days": None, "breadth": None, "status": "INSUFFICIENT",
               "gaps": ["未建立板块关联或行情库不可用"]})
        src = SRC_BY_ID[it["source_id"]]
        ev = {
            "event_id": event_id(it["url"], it["source_id"]),
            "title": it["title"],
            "event_date": it["date"],
            "first_seen": now,
            "source": {"id": src["id"], "name": src["name"], "publisher": src["publisher"],
                       "url": it["url"], "list_url": src["list_url"],
                       "category": src["category"], "access": "PUBLIC_HTML"},
            "evidence_quote": quote,
            "evidence_sha256_16": qhash,
            "theme_links": links,
            "market": mk,
            "security_mapping": {"status": "NOT_MAPPED",
                                 "reason": "首版不做个股级映射：仅关联到行业板块序列；"
                                           "个股映射需另行按名称+代码核验"},
        }
        ev["status"], ev["gaps"] = classify(ev, as_of) if as_of else ("INSUFFICIENT", ["无行情基准日"])
        ev["gaps"] = ev["gaps"] + list(mk.get("gaps") or [])
        events.append(ev)
    if con:
        con.close()

    # 去重：同一 (event_date, 规范化标题) 只留一条（保留先出现的 URL）
    seen, uniq = set(), []
    for e in events:
        k = (e["event_date"], re.sub(r"\s+", "", e["title"]))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(e)

    by_status = {}
    for e in uniq:
        by_status[e["status"]] = by_status.get(e["status"], 0) + 1
    dates = [e["event_date"] for e in uniq]

    return {
        "artifact": "new_theme_radar",
        "artifact_version": "0.1",
        "generated_at": now,
        "as_of": as_of,
        "source_kind": "AUTO_DISCOVERED_EVENT",
        "coverage": {
            "publisher": "国家发展改革委",
            "sources": [{"id": x["id"], "name": x["name"], "list_url": x["list_url"],
                         "category": x["category"], "pages": x["pages"]} for x in SOURCES],
            "pages_fetched": fetched,
            "date_range": [min(dates), max(dates)] if dates else None,
            "events": len(uniq),
            "by_source": {sid: sum(1 for e in uniq if e["source"]["id"] == sid) for sid in SRC_BY_ID},
            "limits": [
                "**单一发布机构（国家发改委）、两个栏目**：政策通知 + 新闻发布，不是全市场新闻挖掘",
                "**类别有限**：只覆盖「政策/通知/价格机制」类发布，不含部委标准、地方政策、公司公告",
                "参与广度不可得：行业板块无历史成分 → 只给板块收益与相对基准，不给广度",
                "个股映射未做：首版只到行业板块级，未建立证券级映射",
                "事件日期取列表页标注日，可能与正文发布时点相差 1 个工作日",
                "**不是预测**：`CANDIDATE` 只是「值得人工看一眼」的机械筛选，需人工复核",
            ],
        },
        "rules": RULES,
        "theme_keywords": [{"keyword": k, "board_series": s, "board_name": n,
                            "relation": r, "rationale": w} for k, s, n, r, w in THEME_KEYWORDS],
        "summary": {"events": len(uniq), "by_status": by_status,
                    "candidates": by_status.get("CANDIDATE", 0)},
        "status_legend": {
            "CANDIDATE": "值得人工看一眼的线索（机械筛选，需人工复核；不是买卖建议）",
            "WATCH": "有板块关联但市场反应不支持 / 事件已过窗口 → 只留档",
            "PENDING_MARKET": "事件后交易日不足，暂不判定",
            "INSUFFICIENT": "行情或关联不足，无法核验",
            "NO_THEME_LINK": "未命中显式关键词表 → 不建立板块关联",
        },
        "events": sorted(uniq, key=lambda e: (e["event_date"], e["event_id"]), reverse=True),
    }


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="联网抓取（不带则只做只读校验）")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--version", type=int, default=None)
    a = ap.parse_args(argv)

    if a.check:
        files = sorted([f for f in os.listdir(CURRENT) if OUT_RE.match(f)],
                       key=lambda f: int(OUT_RE.match(f).group(1)))
        if not files:
            print("FAIL: 事件产物不存在")
            return 1
        d = json.load(open(os.path.join(CURRENT, files[-1]), encoding="utf-8"))
        errs = []
        # ① 结构 + 溯源：每条事件必须有来源 URL、日期、状态
        for e in d["events"]:
            if not e.get("source", {}).get("url"):
                errs.append("%s 缺来源 URL" % e.get("event_id"))
            if not e.get("event_date"):
                errs.append("%s 缺事件日期" % e.get("event_id"))
            if e.get("status") not in d["status_legend"]:
                errs.append("%s 状态非法（%s）" % (e.get("event_id"), e.get("status")))
            # ② 关联必须有依据（不猜）
            for L in e.get("theme_links") or []:
                if not L.get("rationale") or not L.get("keyword"):
                    errs.append("%s 板块关联缺依据" % e.get("event_id"))
            # ③ 候选必须满足规则（不允许「无关联却成候选」）
            if e.get("status") == "CANDIDATE":
                mk = e.get("market") or {}
                if not e.get("theme_links"):
                    errs.append("%s 无关联却标 CANDIDATE" % e["event_id"])
                if (mk.get("observation_trading_days") or 0) < d["rules"]["min_observation_trading_days"]:
                    errs.append("%s 观察日不足却标 CANDIDATE" % e["event_id"])
                if (mk.get("excess_pp") or 0) <= 0:
                    errs.append("%s 超额非正却标 CANDIDATE" % e["event_id"])
        # ④ 去重
        keys = [(e["event_date"], re.sub(r"\s+", "", e["title"])) for e in d["events"]]
        if len(keys) != len(set(keys)):
            errs.append("存在重复事件（同日期 + 同标题）")
        # ④b 状态机自洽：用产物自身的字段重跑 classify，必须与写入的 status 一致
        #     （不依赖行情库，CI 也能跑 —— 防止「状态是手写的」或规则改了没重算）
        for e in d["events"]:
            want, _ = classify(e, d["as_of"])
            if want != e["status"]:
                errs.append("%s 状态不自洽（产物 %s vs 规则 %s）" % (e["event_id"], e["status"], want))
        # ⑤ 行情可复算（有库才算，缺库显式 SKIP）
        if os.path.exists(SCAN_DB) and d.get("as_of"):
            con = sqlite3.connect("file:%s?mode=ro" % SCAN_DB, uri=True)
            cal = _cal(con)
            n = 0
            for e in d["events"]:
                mk = e.get("market") or {}
                if mk.get("status") != "OBSERVED" or not e.get("theme_links"):
                    continue
                re_mk = market_of(con, cal, e["theme_links"][0]["board_series"],
                                  e["event_date"], d["as_of"])
                for k in ("board_ret_pct", "bench_ret_pct", "excess_pp", "observation_trading_days"):
                    if re_mk.get(k) != mk.get(k):
                        errs.append("%s 的 %s 不可复算（产物 %s vs 重算 %s）"
                                    % (e["event_id"], k, mk.get(k), re_mk.get(k)))
                        break
                n += 1
            con.close()
            print("  行情复算覆盖 %d 条 OBSERVED 事件" % n)
        else:
            print("  SKIP 行情复算：history_scan.db 不存在（CI 不携带 1.3GB 库）")
        if errs:
            print("FAIL: %s" % errs[:6])
            return 1
        print("PASS: 新题材雷达一致（%d 事件 · %s）" % (len(d["events"]), d["summary"]["by_status"]))
        return 0

    doc = build(fetch=a.fetch)
    print("事件 %d 条 · 状态 %s · as_of %s" % (len(doc["events"]), doc["summary"]["by_status"], doc["as_of"]))
    for e in doc["events"][:8]:
        print("  [%-14s] %s %s" % (e["status"], e["event_date"], e["title"][:42]))
    if a.write:
        if a.version is None:
            print("FAIL: --write 需要 --version N")
            return 1
        out = os.path.join(CURRENT, "new_theme_radar_v0_%d.json" % a.version)
        if os.path.exists(out):
            print("FAIL: 目标已存在：%s" % out)
            return 1
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        print("已生成 %s" % os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
