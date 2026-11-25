#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""历史信息侧数据源 v0.1：回溯抓取已有 5 个来源的公开列表页历史分页。

★ 口径在 docs/HISTORICAL_INFO_SOURCES_DESIGN_v0_1.md 中**先于本脚本**冻结；
  设计全文 sha256_16 锁在 LOCKED_DESIGN_SHA16，改口径必须升版并留痕。
★ 只在已有 SOURCES 上做历史分页回溯，不新增来源站点；抓不到逐来源写原因，不补造。
★ --fetch 才联网（节流 1.1s/页）；--check 绝不联网，CI 可安全执行。
★ 用 2026 年构建的词表检索历史标题属**事后检索**，产物显式声明非当时可得信号。

用法：
  python research/scripts/build_historical_info_events_v0_1.py --fetch --write
  python research/scripts/build_historical_info_events_v0_1.py --check
"""
import argparse
import collections
import datetime
import hashlib
import importlib.util
import json
import os
import re
import sqlite3
import sys
import time
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(ROOT, "research", "current")
DOCS = os.path.join(ROOT, "docs")
SCRIPTS = os.path.join(ROOT, "research", "scripts")
DB = os.path.join(ROOT, "research", "database", "history_scan.db")

OUT = os.path.join(CURRENT, "historical_info_events_v0_1.json")
DESIGN = os.path.join(DOCS, "HISTORICAL_INFO_SOURCES_DESIGN_v0_1.md")
RADAR_SCRIPT = os.path.join(SCRIPTS, "build_new_theme_radar_v0_1.py")
TD_SCRIPT = os.path.join(SCRIPTS, "build_theme_discovery_v0_1.py")
HR2_SCRIPT = os.path.join(SCRIPTS, "build_historical_replay_v0_2.py")
RADAR = os.path.join(CURRENT, "new_theme_radar_v0_10_view.json")
ROLES = os.path.join(CURRENT, "historical_market_roles_v0_13.json")
SEM = os.path.join(CURRENT, "board_semantics_v0_1.json")

LOCKED_DESIGN_SHA16 = "74928a7191bebf26"
THROTTLE_SEC = 1.1
# 设计 §6.1：外来原文键，逐字保留、不参与禁用措辞扫描
ORIGINAL_TEXT_KEYS = ("title", "url")

# 设计 §1：只有这两个来源有可核的历史分页（首页 createPageHTML 给出总页数）
HISTORY_PAGES = {"NDRC_ZCFB_TZ": 20, "NDRC_XWFB": 40}
# 设计 §1.3：另外三个来源的分页能力探测（每个只请求一次，记录实测证据）
GAP_PROBES = [
    {"source_id": "NHSA_NOTICE", "kind": "PROXY_EMPTY_RESPONSE",
     "url": "https://www.nhsa.gov.cn/module/web/jpage/dataproxy.jsp",
     "note": "jpage 分页接口；实测带 startrecord/endrecord/perpage 仍返回 54 B 空响应，"
             "疑需会话态，本轮不猜测参数组合"},
    {"source_id": "NEA_XNY", "kind": "EMPTY_SHELL_PAGE",
     "url": "https://www.nea.gov.cn/sjzz/xny/index_2.htm",
     "note": "index_N.htm 返回约 24 KB 但 0 条可解析 <li> 条目（空壳页）"},
    {"source_id": "MIIT_KJS", "kind": "NO_HISTORICAL_PAGINATION",
     "url": "https://www.miit.gov.cn/jgsj/kjs/index_1.html",
     "note": "栏目无 index_N.html 分页，只有单页近期列表"},
]
GAP_LEGEND = {
    "PROXY_EMPTY_RESPONSE": "分页代理接口返回空响应，未取得任何历史条目",
    "EMPTY_SHELL_PAGE": "分页 URL 可达但页面无可解析条目（空壳/JS 渲染）",
    "NO_HISTORICAL_PAGINATION": "该栏目未提供历史分页入口",
}

# 设计 §3：L3 名称自匹配的通用词排除表（避免宏观政策标题被泛化词全命中）
GENERIC_TERMS = (
    "关于", "通知", "工作", "情况", "发展", "建设", "管理", "政策", "有关", "印发",
    "国家", "问题", "意见", "加强", "推进", "开展", "组织", "实施", "部门", "全国",
    "公告", "公示", "答复", "函", "会议", "领导", "重要", "进一步", "若干", "措施",
)

BANNED = ("买入", "卖出", "目标价", "仓位", "胜率", "准确性", "荐股", "选股清单",
          "龙头", "弹性", "大概率", "未来概率", "TODO", "TBD", "PLACEHOLDER")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _sha16_bytes(b):
    return hashlib.sha256(b).hexdigest()[:16]


def _sha16(path):
    return _sha16_bytes(open(path, "rb").read())


def _dump(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, sort_keys=True, indent=1)
        f.write("\n")


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _event_id(source_id, date, url):
    return "HIE-%s" % hashlib.sha256(("%s|%s|%s" % (source_id, date, url)).encode()).hexdigest()[:16]


def _generated_strings(obj):
    """设计 §6.1：递归收集生成性文本；键名为 title/url 的外来原文逐字跳过。"""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ORIGINAL_TEXT_KEYS:
                continue
            out.extend(_generated_strings(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_generated_strings(v))
    elif isinstance(obj, str):
        out.append(obj)
    return out


def _board_universe():
    """库内真实序列清单，写进产物供 --check 在无大库环境做双向校验。"""
    if not (os.path.exists(DB) and os.path.getsize(DB) > 0):
        return None
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        rows = con.execute(
            "select series_id,name,kind from scan_series "
            "where kind in ('industry_board','concept_basket')").fetchall()
    finally:
        con.close()
    return {sid: {"name": name, "kind": kind} for sid, name, kind in rows}


def _l3_name_map(universe, fuzzy):
    """设计 §3：库内可解释板块/篮子名称本身，>=3 字、排除通用词；同名词冲突写 dropped。"""
    out, dropped = {}, []
    for sid, meta in sorted(universe.items()):
        name = meta["name"]
        if sid in fuzzy:
            continue
        if len(name) < 3:
            dropped.append({"name": name, "series_id": sid, "reason": "NAME_TOO_SHORT"})
            continue
        # ★ 设计 §3 的「排除通用词」按**子串**判定：只查全等会漏掉
        #   「基础建设」「沿海发展」这类包含泛化词的板块名。
        if any(g in name for g in GENERIC_TERMS):
            dropped.append({"name": name, "series_id": sid,
                            "reason": "GENERIC_TERM_SUBSTRING",
                            "matched": [g for g in GENERIC_TERMS if g in name]})
            continue
        if name in out and out[name] != sid:
            dropped.append({"name": name, "series_id": sid,
                            "reason": "DUPLICATE_NAME_CONFLICT", "existing": out[name]})
            continue
        out[name] = sid
    return dict(sorted(out.items())), dropped


def _probe_gaps(radar):
    """实测三个无分页来源，记录可核证据（不把 0 条写成「有」）。"""
    probes = []
    for p in GAP_PROBES:
        u = p["url"]
        if p["source_id"] == "NHSA_NOTICE":
            u += "?startrecord=1&endrecord=45&perpage=15&col=1&appid=1&webid=1&path=/&permissiontype=0"
        src = radar.SRC_BY_ID[p["source_id"]]
        h = radar._get(u, headers={"Referer": src["referer"]} if src.get("referer") else None)
        parsed = 0
        if h:
            try:
                parsed = len(radar.PARSE_LIST[src["adapter"]](h, src))
            except Exception:
                parsed = 0
        probes.append({"source_id": p["source_id"], "url": u, "kind": p["kind"],
                       "http_body_bytes": len(h) if h else 0,
                       "parsed_items": parsed, "note": p["note"]})
        time.sleep(THROTTLE_SEC)
    return probes


def build_fetch():
    radar = _module("radar_src", RADAR_SCRIPT)
    td = _module("td_kw", TD_SCRIPT)
    hr2 = _module("hr2_const", HR2_SCRIPT)
    kw = dict(td.KEYWORD_MAP)
    role_map = dict(hr2.ROLE_MAP)
    sem = _load(SEM)
    fuzzy = {e["series_id"] for e in (sem.get("entries") or []) if not e.get("interpretable")}

    universe = _board_universe()
    if universe is None:
        raise RuntimeError("缺 history_scan.db → 无法构建 L3 名称映射与序列白名单")
    l3, l3_dropped = _l3_name_map(universe, fuzzy)

    # ── 抓取：NDRC 两个来源的完整历史分页 ──
    pages, failures, raw = [], [], []
    for sid, n in HISTORY_PAGES.items():
        src = radar.SRC_BY_ID[sid]
        for i in range(n):
            page = "" if i == 0 else "index_%d.html" % i
            url = src["list_url"] + page
            h = radar._get(url)
            if not h:
                failures.append({"source_id": sid, "page": page, "url": url,
                                 "reason": "HTTP_OR_NETWORK_FAILURE"})
                pages.append({"source_id": sid, "page": page, "url": url,
                              "http_body_bytes": 0, "html_sha256_16": None, "items": 0})
                time.sleep(THROTTLE_SEC)
                continue
            got = radar.PARSE_LIST[src["adapter"]](h, src)
            for x in got:
                x["page"] = page
                x["source_id"] = sid
                x["publisher"] = src["publisher"]
            pages.append({"source_id": sid, "page": page, "url": url,
                          "http_body_bytes": len(h),
                          "html_sha256_16": _sha16_bytes(h.encode("utf-8", "ignore")),
                          "items": len(got)})
            raw.extend(got)
            time.sleep(THROTTLE_SEC)

    # URL 去重（栏目间/翻页间可能重复）
    uniq = {}
    for x in raw:
        uniq.setdefault(x["url"], x)
    items = sorted(uniq.values(), key=lambda x: (x["date"], x["source_id"], x["url"]))

    # ── 三层映射 ──
    l1_hits, l3_hits, dropped = [], [], []
    for x in items:
        title = x["title"] or ""
        ks = [k for k in kw if k in title]
        ns = [n for n in l3 if n in title]
        x["l1_keywords"] = sorted(ks)
        x["l3_names"] = sorted(ns)
        if ks:
            l1_hits.append({"event_id": _event_id(x["source_id"], x["date"], x["url"]),
                            "date": x["date"], "title": title, "keywords": sorted(ks),
                            "boards": sorted({kw[k][1] for k in ks}),
                            "relations": sorted({kw[k][3] for k in ks})})
        if ns:
            l3_hits.append({"event_id": _event_id(x["source_id"], x["date"], x["url"]),
                            "date": x["date"], "title": title, "names": sorted(ns),
                            "boards": sorted({l3[n] for n in ns})})

    for k, v in kw.items():
        if v[1] not in universe:
            dropped.append({"layer": "L1", "keyword": k, "target": v[1],
                            "reason": "TARGET_SERIES_NOT_IN_DB"})
    for tid, (sid, _rel) in role_map.items():
        if sid not in universe:
            dropped.append({"layer": "L2", "keyword": tid, "target": sid,
                            "reason": "TARGET_SERIES_NOT_IN_DB"})
    for d in l3_dropped:
        d["layer"] = "L3"
    dropped.extend(l3_dropped)

    # ── 事件明细 ──
    events = []
    for x in items:
        events.append({
            "event_id": _event_id(x["source_id"], x["date"], x["url"]),
            "source_id": x["source_id"], "publisher": x["publisher"],
            "title": x["title"], "url": x["url"], "event_date": x["date"],
            "date_source": x["date_source"], "page": x["page"],
            "title_sha256_16": _sha16_bytes((x["title"] or "").encode("utf-8")),
            "l1_keywords": x["l1_keywords"], "l3_names": x["l3_names"],
        })

    years = collections.Counter(e["event_date"][:4] for e in events)
    by_source = collections.Counter(e["source_id"] for e in events)

    # ── 词表版本化：首次「可核出现」年份（弱证据，不用外部知识猜） ──
    lexicon = {}
    for k, v in kw.items():
        ys = sorted(h["date"][:4] for h in l1_hits if k in h["keywords"])
        lexicon[k] = {
            "board_series": v[1], "relation": v[3], "rationale": v[4],
            "first_verifiable_mention_year": int(ys[0]) if ys else None,
            "mention_status": "OBSERVED_IN_HISTORICAL_LIST" if ys else "NO_OBSERVED_MENTION",
        }

    # ── 无分页来源的实测缺口 ──
    probes = _probe_gaps(radar)
    gap_counts = collections.Counter(p["kind"] for p in probes)
    source_coverage = []
    for sid in ("NDRC_ZCFB_TZ", "NDRC_XWFB"):
        pp = [p for p in pages if p["source_id"] == sid]
        ds = sorted(e["event_date"] for e in events if e["source_id"] == sid)
        source_coverage.append({
            "source_id": sid, "status": "HISTORICAL_PAGINATION_OK",
            "pages_requested": HISTORY_PAGES[sid],
            "pages_ok": len([p for p in pp if p["items"] > 0]),
            "items": by_source[sid],
            "date_min": ds[0] if ds else None, "date_max": ds[-1] if ds else None,
            "gap_reason": None,
        })
    for p in probes:
        src = radar.SRC_BY_ID[p["source_id"]]
        source_coverage.append({
            "source_id": p["source_id"], "status": p["kind"],
            "pages_requested": 1, "pages_ok": 0, "items": 0,
            "date_min": None, "date_max": None,
            "gap_reason": GAP_LEGEND[p["kind"]],
            "probe": {"url": p["url"], "http_body_bytes": p["http_body_bytes"],
                      "parsed_items": p["parsed_items"], "note": p["note"]},
            "list_url": src["list_url"],
        })

    # ── L2 历史角色窗口（与 v0.2 同源，供 v0.3 合并事件表） ──
    roles = _load(ROLES)
    role_events, no_exact = [], collections.Counter()
    for eid, v in (roles.get("events") or {}).items():
        tid, w = v.get("theme_id"), (v.get("window") or [])
        if tid in hr2.NO_EXACT_MAPPING_THEMES:
            no_exact[tid] += 1
            continue
        if tid not in role_map or not w:
            continue
        sid, rel = role_map[tid]
        role_events.append({"event_id": "ROLE-%s" % eid, "theme_id": tid,
                            "event_date": w[0], "board_series": sid,
                            "relation": rel, "date_source": "PIT_WINDOW_START"})

    # ── 现有雷达的 L1 命中（v0.2 同源；v0.3 合并用） ──
    radar_view = _load(RADAR)
    radar_pairs = set()
    for e in radar_view.get("events") or []:
        title, d = e.get("title") or "", e.get("event_date")
        if not d:
            continue
        for k, v in kw.items():
            if k in title:
                radar_pairs.add((d, v[1], k))
    radar_l1 = [{"event_date": d, "board_series": sid, "keyword": k,
                 "date_source": "LIST_PAGE_OR_URL_PATH"}
                for d, sid, k in sorted(radar_pairs)]

    payload = {
        "artifact": "historical_info_events",
        "artifact_version": "0.1",
        "purpose": "补历史信息侧数据源：已有 5 个来源的公开列表页历史分页回溯；"
                   "只作历史描述统计与特征可用性评估，不构成当时可得信号",
        "design": "docs/HISTORICAL_INFO_SOURCES_DESIGN_v0_1.md",
        "design_sha256_16_locked": LOCKED_DESIGN_SHA16,
        "fetched_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "lexicon_is_post_hoc": True,
        "lexicon_built_at": "2026-11-15",
        "not_point_in_time_signal": True,
        "pit_note": "用 2026 年构建的词表检索 2017–2026 历史标题属事后检索；"
                    "事件日当天不计入反应；特征回看 365 自然日且 event_date <= T；"
                    "板块历史成分 ACCESS_GATED 未解，不用当前成分冒充历史成分",
        "date_rule": "事件日期取列表页上网日，date_source=LIST_PAGE；"
                     "列表日 != 成文日 != URL 路径日期，不用正文 PubDate 冒充首次公开时间",
        "limits": [
            "★ 公开列表页最远只到 2017-12-18（网站仅保留 20 / 40 页），非 2014；这是数据边界，不补造。",
            "★ 事后检索：词表为 2026 年构建，不得解读为当时投资者可得的信号。",
            "★ L3 名称自匹配是 WEAK 检索线索，仅敏感性对照，不等于事件关联该板块。",
            "★ 三个来源无历史分页，逐来源写原因与实测证据，未把 0 条写成「有」。",
            "★ 不新增来源站点、不用官方指数接口、不做正文或公司名子串匹配。",
            "★ 板块历史成分 ACCESS_GATED 未解，本轮不做成分级回填。",
            "★ 词表首次可核出现年份只是弱证据，不用于裁剪历史、不改变词表。",
        ],
        "source_coverage": source_coverage,
        "gap_counts": dict(sorted(gap_counts.items())),
        "gap_legend": GAP_LEGEND,
        "pages": pages,
        "page_failures": failures,
        "page_reconciliation": {
            "pages_requested": sum(HISTORY_PAGES.values()),
            "pages_ok": len([p for p in pages if p["items"] > 0]),
            "page_failures": len(failures),
            "raw_items": len(raw),
            "unique_items": len(items),
            "duplicates_removed": len(raw) - len(items),
        },
        "events": events,
        "event_counts": {
            "total": len(events),
            "by_year": dict(sorted(years.items())),
            "by_source": dict(sorted(by_source.items())),
            "url_scheme_distribution": dict(sorted(collections.Counter(
                ("https" if e["url"].startswith("https://") else
                 "http" if e["url"].startswith("http://") else "OTHER")
                for e in events).items())),
            "date_min": events[0]["event_date"] if events else None,
            "date_max": events[-1]["event_date"] if events else None,
        },
        "banned_scan_scope": {
            "method": "递归收集所有字符串值，跳过键名为 title / url 的外来原文字段",
            "excluded_keys": list(ORIGINAL_TEXT_KEYS),
            "reason": "原文标题与 URL 逐字保留；真实农业政策类标题中的复合词会造成形状误判，"
                      "不得为过检查而改写原文",
        },
        "lexicon_l1": lexicon,
        "lexicon_l1_size": len(kw),
        "lexicon_l1_mapped_series": sorted({v[1] for v in kw.values()}),
        "lexicon_l2_role_map": {k: {"board_series": v[0], "relation": v[1]}
                                for k, v in sorted(role_map.items())},
        "lexicon_l3_name_map": l3,
        "lexicon_l3_size": len(l3),
        "generic_terms_excluded": list(GENERIC_TERMS),
        "mapping_hits": {
            "l1_titles": len(l1_hits),
            "l1_unique_boards": len({b for h in l1_hits for b in h["boards"]}),
            "l3_titles": len(l3_hits),
            "l3_unique_boards": len({b for h in l3_hits for b in h["boards"]}),
            "l1_detail": l1_hits,
            "l3_detail": l3_hits,
        },
        "validation": {
            "board_universe_size": len(universe),
            "fuzzy_series_count": len(fuzzy),
            "dropped": dropped,
            "dropped_count": len(dropped),
            "valid_series": sorted(universe),
            "no_exact_mapping_themes": dict(sorted(no_exact.items())),
        },
        "merge_inputs_for_replay_v0_3": {
            "historical_l1_events": [
                {"event_date": h["date"], "board_series": b,
                 "date_source": "LIST_PAGE", "origin": "NDRC_HISTORY_PAGES"}
                for h in l1_hits for b in h["boards"]],
            "radar_l1_events": radar_l1,
            "role_window_events": role_events,
            "l3_events_sensitivity_only": [
                {"event_date": h["date"], "board_series": b,
                 "relation": "NAME_MATCH_ONLY", "evidence_grade": "WEAK",
                 "origin": "NDRC_HISTORY_PAGES"}
                for h in l3_hits for b in h["boards"]],
        },
        "source_sha256_16": {
            os.path.basename(p): _sha16(p) for p in
            (DESIGN, RADAR_SCRIPT, TD_SCRIPT, HR2_SCRIPT, RADAR, ROLES, SEM)
        },
    }
    # 内容指纹（不含 fetched_at，供 --check 检测篡改）
    stable = {k: v for k, v in payload.items() if k != "fetched_at"}
    payload["payload_sha256_16"] = _sha16_bytes(
        json.dumps(stable, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    return payload


def _resolve(name):
    for base in (CURRENT, DOCS, SCRIPTS):
        p = os.path.join(base, name)
        if os.path.exists(p):
            return p
    return None


def check():
    """只读校验：不联网、不读大库。范围见 --check PASS 行。"""
    errs, skips = [], []
    if not os.path.exists(OUT):
        print("FAIL 产物不存在：%s" % OUT)
        return 1
    doc = _load(OUT)

    if not os.path.exists(DESIGN):
        errs.append("设计文档缺失")
    else:
        actual = _sha16(DESIGN)
        if actual != LOCKED_DESIGN_SHA16:
            errs.append("设计文档已被改动（%s / 锁定 %s）→ 必须升版"
                        % (actual, LOCKED_DESIGN_SHA16))
        if doc.get("design_sha256_16_locked") != LOCKED_DESIGN_SHA16:
            errs.append("产物声明的设计指纹与脚本锁定值不一致")
    for name, want in (doc.get("source_sha256_16") or {}).items():
        p = _resolve(name)
        if not p:
            skips.append("上游文件不在干净 checkout：%s" % name)
        elif _sha16(p) != want:
            errs.append("上游指纹漂移：%s" % name)

    stable = {k: v for k, v in doc.items() if k not in ("fetched_at", "payload_sha256_16")}
    if _sha16_bytes(json.dumps(stable, ensure_ascii=False, sort_keys=True).encode("utf-8")) != \
       doc.get("payload_sha256_16"):
        errs.append("内容指纹不匹配（产物被篡改或 --fetch 后未更新指纹）")

    # 事后检索声明
    for k, want in (("lexicon_is_post_hoc", True), ("not_point_in_time_signal", True)):
        if doc.get(k) is not want:
            errs.append("事后检索声明缺失或被改：%s" % k)

    # 页级守恒
    pr = doc.get("page_reconciliation") or {}
    if pr.get("pages_requested") != pr.get("pages_ok", 0) + pr.get("page_failures", 0):
        errs.append("页级守恒不成立")
    if pr.get("unique_items") + pr.get("duplicates_removed", 0) != pr.get("raw_items"):
        errs.append("事件去重守恒不成立")
    cov = doc.get("source_coverage") or []
    if sum(c["items"] for c in cov) != pr.get("unique_items"):
        errs.append("来源条目之和与事件总数不一致")
    for c in cov:
        if c["status"] != "HISTORICAL_PAGINATION_OK" and not c.get("gap_reason"):
            errs.append("无分页来源缺 gap_reason：%s" % c["source_id"])
        if c["status"] == "HISTORICAL_PAGINATION_OK" and c["pages_ok"] != c["pages_requested"]:
            errs.append("有分页来源未取全：%s" % c["source_id"])
    if doc.get("gap_counts") and sum(doc["gap_counts"].values()) != \
       len([c for c in cov if c["status"] != "HISTORICAL_PAGINATION_OK"]):
        errs.append("gap_counts 与 source_coverage 不一致")

    # 事件形状与逐年守恒
    ev = doc.get("events") or []
    if not ev:
        errs.append("事件表为空")
    years = collections.Counter(e["event_date"][:4] for e in ev)
    if dict(sorted(years.items())) != (doc.get("event_counts") or {}).get("by_year"):
        errs.append("逐年计数不一致")
    if len({e["url"] for e in ev}) != len(ev):
        errs.append("事件 URL 未去重")
    for e in ev:
        if not DATE_RE.match(e["event_date"] or ""):
            errs.append("事件日期格式错：%s" % e.get("event_id"))
            break
        if e.get("date_source") not in ("LIST_PAGE", "URL_PATH"):
            errs.append("date_source 枚举错：%s" % e.get("event_id"))
            break
        if not re.match(r"^https?://[^/\s]+", str(e.get("url") or "")):
            errs.append("事件 URL 非法或 host 为空：%s" % e.get("event_id"))
            break
        if _sha16_bytes((e["title"] or "").encode("utf-8")) != e.get("title_sha256_16"):
            errs.append("标题指纹不匹配：%s" % e.get("event_id"))
            break

    # 映射双向校验（用产物自带的 valid_series，无需大库）
    valid = set((doc.get("validation") or {}).get("valid_series") or [])
    if not valid:
        errs.append("valid_series 白名单为空")
    for k, v in (doc.get("lexicon_l1") or {}).items():
        if v["board_series"] not in valid:
            errs.append("L1 词表目标序列不在白名单：%s -> %s" % (k, v["board_series"]))
        if v["mention_status"] == "OBSERVED_IN_HISTORICAL_LIST" and \
           v["first_verifiable_mention_year"] is None:
            errs.append("L1 词首次出现年份声明矛盾：%s" % k)
    for k, v in (doc.get("lexicon_l2_role_map") or {}).items():
        if v["board_series"] not in valid:
            errs.append("L2 映射目标序列不在白名单：%s" % k)
    for name, sid in (doc.get("lexicon_l3_name_map") or {}).items():
        if sid not in valid:
            errs.append("L3 映射目标序列不在白名单：%s" % name)
            break
        if len(name) < 3 or any(g in name for g in doc.get("generic_terms_excluded", ())):
            errs.append("L3 含过短或通用词子串：%s" % name)
            break
    dropped = (doc.get("validation") or {}).get("dropped") or []
    if (doc.get("validation") or {}).get("dropped_count") != len(dropped):
        errs.append("dropped 计数不一致")

    # L3 只能用于敏感性对照
    for h in (doc.get("mapping_hits") or {}).get("l3_detail") or []:
        if h.get("relation") == "DIRECT":
            errs.append("L3 不得标 DIRECT")
            break

    scope = doc.get("banned_scan_scope") or {}
    if scope.get("excluded_keys") != list(ORIGINAL_TEXT_KEYS):
        errs.append("禁用措辞扫描范围声明与设计 §6.1 不一致")
    gen_blob = "\n".join(_generated_strings(doc))
    for w in BANNED:
        if w in gen_blob:
            errs.append("生成性文本出现禁止措辞或占位符：%s" % w)
    schemes = (doc.get("event_counts") or {}).get("url_scheme_distribution") or {}
    if schemes.get("OTHER"):
        errs.append("存在非 http(s) 事件 URL")

    if errs:
        for e in errs:
            print("FAIL " + e)
    for s in skips:
        print("SKIP " + s)
    if errs:
        print("--check：%d 项 FAIL · 范围：设计指纹 / 内容指纹 / 事后检索声明 / "
              "页级与逐年守恒 / 事件形状 / 三层映射双向校验 / 禁用措辞" % len(errs))
        return 1
    print("--check PASS · 范围：设计指纹 %s / 内容指纹 / 事后检索声明 / 页级 %d / "
          "事件 %d（%s→%s）/ URL scheme / 逐年守恒 / 三层映射 %d 项 / "
          "禁用措辞（仅生成性文本，排除 title/url 原文）· SKIP %d 项"
          % (LOCKED_DESIGN_SHA16, pr.get("pages_requested", 0), len(ev),
             (doc.get("event_counts") or {}).get("date_min"),
             (doc.get("event_counts") or {}).get("date_max"),
             len(doc.get("lexicon_l1") or {}) + len(doc.get("lexicon_l3_name_map") or {}),
             len(skips)))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="联网重抓历史分页")
    ap.add_argument("--write", action="store_true", help="写产物（需与 --fetch 同用）")
    ap.add_argument("--check", action="store_true", help="只读校验，不联网")
    a = ap.parse_args()
    if a.fetch and a.write:
        doc = build_fetch()
        _dump(OUT, doc)
        print("--fetch --write OK: %s · 页 %d / 事件 %d · L1 命中 %d / L3 命中 %d"
              % (os.path.basename(OUT), doc["page_reconciliation"]["pages_ok"],
                 doc["event_counts"]["total"],
                 doc["mapping_hits"]["l1_titles"], doc["mapping_hits"]["l3_titles"]))
        return 0
    if a.write:
        print("FAIL --write 必须与 --fetch 同用（抓取是快照，不支持离线重算）")
        return 2
    return check()


if __name__ == "__main__":
    sys.exit(main())
