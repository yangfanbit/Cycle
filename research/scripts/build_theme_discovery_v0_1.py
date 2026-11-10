#!/usr/bin/env python3
"""build_theme_discovery_v0_1.py —— 当前主题挖掘（v0.82，双轨并列）。

## 为什么需要它
v0.81 的「本周最新研究」其实是把本周事件往 **6 个 2026-10-23 人工研究对象**里塞
（`DIRECTION_TO_CANDIDATES` 硬编码）；那不是从市场信息里挖主题，是历史档案的展示。
本产物改成：主题候选由**本周可核信息 + 客观行情结构**共同聚合产生，不预设主题集合。

## 两条轨并列，不做因果拼接
- 信息轨：雷达本周窗口的官方文件，只按**标题关键词精确匹配**到板块序列，逐条带 URL / 日期 / 关联理由。
- 行情轨：库内 241 行业板块 + 173 概念篮子的 OHLCV，算**客观历史描述量**
  （5/10/20 日相对 CSI300 超额、20 日成交额代理相对前 20 日比值、20 日已实现波动率）。
  这些是描述统计，**不是预测、不是打分、不是排序依据**。

## 硬约束
- **不预设主题**：候选由 board_series + theme_tag 聚类产生。
- **零编造**：词表是显式映射表，构建时双向校验（板块序列必须在库内存在）；
  不做正文匹配、不做子串匹配公司名；无命中写原因，不补关联。
- **不越宪法**：产物不含 score / ranking / probability / prediction 字段；
  G1–G4 是**互斥类型分组**，不是排序；个股层只投影历史 PIT 角色记录（带来源与识别日），
  不给「龙头 / 弹性」标签、不给当前标的判断、不构成推荐。
- **PIT 纪律**：历史角色只取 `pit_safe == True`，事后信息不当事前证据。
- **确定性**：不写 generated_at；source_sha256_16 对账全部上游文件。

用法：--write / --check
"""
import argparse
import collections
import glob
import hashlib
import json
import os
import re
import sqlite3
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
DB = os.path.join(REPO, "research", "database", "history_scan.db")
BOARD = os.path.join(CURRENT, "frontier_board_v0_1.json")
SEM = os.path.join(CURRENT, "board_semantics_v0_1.json")
CAL = os.path.join(CURRENT, "event_calendar_v0_1.json")
OUT = os.path.join(CURRENT, "theme_discovery_v0_1.json")

# ★ 显式映射：keyword -> (theme_tag, board_series, board_name, relation, rationale)
#   rationale 只陈述「为什么这个标题词属于这个板块环节」，不推断因果、不预测收益。
#   board_series 在 build() 里逐个校验必须存在于 scan_series，失败写 dropped_mappings。
KEYWORD_MAP = {
    "医用耗材": ("医用耗材分类与价格", "BK881144", "医疗器械", "DIRECT",
                 "耗材分类与代码属医疗器械监管范围，直接作用于该板块"),
    "神经介入": ("医用耗材分类与价格", "BK881144", "医疗器械", "DIRECT",
                 "神经介入植入材料属医疗器械监管范围"),
    "汽车座椅": ("汽车零部件标准", "BK881126", "汽车零部件", "DIRECT",
                 "座椅及头枕强度标准直接作用于汽车零部件环节"),
    "头枕强度": ("汽车零部件标准", "BK881126", "汽车零部件", "DIRECT",
                 "头枕强度强制性国家标准直接作用于汽车零部件环节"),
    "石墨化增碳剂": ("钢铁上游辅料", "BK881112", "钢铁", "PROXY",
                   "增碳剂用于炼钢环节，属钢铁上游辅料，为代理关联"),
    "元宇宙": ("数字内容管理", "BK881164", "文化传媒", "PROXY",
               "数字内容管理要求属文化传媒/数字内容监管范围，为代理关联"),
    "数字内容": ("数字内容管理", "BK881164", "文化传媒", "PROXY",
                 "数字内容管理要求属文化传媒/数字内容监管范围，为代理关联"),
    "北斗卫星": ("卫星导航", "BK881276", "军工电子", "PROXY",
                 "北斗卫星合作文件涉及卫星导航应用，军工电子为代理关联"),
    "半导体": ("半导体与集成电路", "BK881121", "半导体", "DIRECT",
               "标题直接指向半导体产业环节"),
    "风电": ("风电设备", "BK881280", "风电设备", "DIRECT",
             "标题直接指向风电设备环节"),
    "光伏": ("光伏设备", "BK881279", "光伏设备", "DIRECT",
             "标题直接指向光伏设备环节"),
    "电力市场": ("电力市场规则", "BK881145", "电力", "DIRECT",
                 "电力市场规则直接作用于电力板块"),
    "机器人": ("机器人与具身智能", "CPT_zjqrgn", "机器人概念", "DIRECT",
               "标题直接指向机器人概念"),
    "固态电池": ("固态电池", "CPT_gtdc", "固态电池", "DIRECT",
                 "标题直接指向固态电池概念"),
    "创新药": ("创新药", "CPT_cxy", "创新药", "DIRECT",
               "标题直接指向创新药概念"),
}

# ★ 主题标签 -> 历史同类事件 theme_id（historical_market_roles 里的真实枚举）
#   只有精确相等的 theme_id 才建关联；找不到就写「库内无可核历史同类事件」。
#   ★ 只映射真正同轴的族；座椅标准≠智能驾驶、耗材分类≠流感、风电≠迎峰度夏，
#     这些**不硬贴**（宁可返回 NO_MAPPED_HISTORY_THEME）。
HISTORY_THEME_MAP = {
    "半导体与集成电路": "SEMICONDUCTOR_AI",
    "机器人与具身智能": "ROBOTICS",
    "数字内容管理": "MEDIA",
    "消费旺季": "CONSUMER_SEASON",
    "资源与金属": "RESOURCE_METAL",
}

RULES = {
    "matching": "只匹配事件标题；词表显式映射；不做正文匹配、不做公司名子串匹配、不做模糊关联",
    "market_gate": {
        "abs_excess20_pp_gt": 5.0,
        "amount_ratio_20_over_prev20_gt": 1.5,
        "logic": "OR",
        "basis": "399 个可算序列实测：|20 日超额|>5pp 命中 113 条，短期放量>1.5x 命中 9 条，"
                 "取并集后 114 条（28.6%）。成交额代理不用「历史分位」——成交量长期增长会让"
                 "近 20 日均值几乎恒为历史最高（实测 176/399 处于 >90% 分位），那是趋势不是异动。",
    },
    "lookback_trading_days": 280,
    "min_common_trading_days": 60,
    "benchmark": "CSI300（raw 收盘，dashed 日期）；板块序列日期归一后按基准交易日对齐",
    "sections": {
        "G1": "双轨命中：有可核信息侧关联 + 行情结构命中门槛",
        "G2": "仅行情结构：无可核信息侧理由，只给规模与紧凑列表（默认折叠）",
        "G3": "仅信息侧：有可核官方文件关联但行情未命中 —— 提前观察的重点",
        "G4": "证据不足：两侧都不命中，只给规模与原因，不逐条铺开",
    },
    "section_coverage": "G1–G4 + excluded_fuzzy_gate_hit = scanned_series，互斥且全覆盖；"
                         "名称不可解释的杂项桶即使行情命中也不单列主题，另计规模与原因",
    "count_units": {
        "events_with_board_link": "窗口内**去重事件数**（一个事件标题可命中多个关键词）",
        "board_link_entries": "事件×关键词产生的**关联条目数**（≥ 事件数）",
        "no_link_reasons": "窗口内**未命中词表的事件数**，按原因互斥分组",
        "invariant": "events_with_board_link + sum(no_link_reasons.values()) == events_in_window",
    },
    "not_a_ranking": "G1–G4 是互斥类型分组，不是优先级排序；分组内按 board_series 字典序，确定性",
    "not_a_recommendation": "所有行情量是历史描述统计，不是预测、不是打分、不构成买卖点；"
                            "历史角色是既有 PIT 记录，不是当前标的判断",
    "pit": "历史角色只取 pit_safe == True；事后信息不当事前证据；每条带来源与识别日",
}

LIMITS = [
    "★ 主题候选由**本周可核信息 + 客观行情结构**聚合产生，不预设主题集合；两轨并列、不做因果拼接。",
    "★ 行情量（相对超额 / 放量比值 / 波动率）是**历史描述统计**，不是预测，不构成买卖点。",
    "★ 词表是显式映射，构建时校验板块序列必须在库内存在；不做正文匹配、不补造关联。",
    "★ 「采集范围未发现」≠「已核实没有」，逐条写原因与下一步。",
    "★ G1–G4 是**互斥类型分组，不是排序**；不产出 score / ranking / probability / prediction。",
    "★ 计数单位是**去重事件数**，不是关联条目数；一条事件标题可命中多个关键词，两类数量分别登记。",
    "★ G1–G4 与「不可解释杂项桶中行情命中被排除」合计覆盖全部扫描序列，没有静默丢失。",
    "★ 个股层只给历史同类事件里的 PIT 角色记录（带来源与识别日），不给当前标的判断、不给推荐标签。",
    "★ 不可解释的杂项桶（board_semantics.interpretable=false）不进 G1/G3，单列规模与原因。",
]

BANNED_WORDS = ("买入", "卖出", "目标价", "仓位", "胜率", "评分",
                "TODO", "TBD", "PLACEHOLDER", "待回填")
# ★ 标的层的结论性标签：宪法禁止，产物里连否定式说明都不要写（避免自扫误报）
BANNED_LABELS = ("龙头", "弹性", "推荐买入", "建议买入", "首选")
FORBIDDEN_KEYS = {"priority_score", "wilson_low", "score", "ranking", "rank",
                  "probability", "prediction", "forecast", "recommend", "target_price"}


def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _dump(p, obj):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def _latest(pattern):
    files = glob.glob(os.path.join(CURRENT, pattern))
    if not files:
        raise RuntimeError("找不到产物：%s" % pattern)
    def ver(p):
        m = re.search(r"_v(\d+(?:_\d+)*)", os.path.basename(p))
        return tuple(int(x) for x in m.group(1).split("_")) if m else ()
    return sorted(files, key=ver)[-1]


def _norm_date(d):
    """紧凑 20261106 / dashed 2026-11-06 → 统一 dashed。"""
    d = str(d or "")
    if "-" in d:
        return d[:10]
    return "%s-%s-%s" % (d[:4], d[4:6], d[6:8]) if len(d) >= 8 else ""


def _forbidden_keys(obj, path="$"):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in FORBIDDEN_KEYS:
                hits.append("%s.%s" % (path, k))
            hits.extend(_forbidden_keys(v, "%s.%s" % (path, k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(_forbidden_keys(v, "%s[%d]" % (path, i)))
    return hits


def market_structure(con):
    """客观历史描述量。返回 {series_id: {...}} + 基准 as_of。"""
    base = sorted(r[0] for r in con.execute(
        "select trade_date from scan_daily where series_id='CSI300' order by trade_date desc limit ?",
        (RULES["lookback_trading_days"],)))
    lo = base[0]
    # ★ 日期混格式：industry_board 是紧凑 20261106、concept_basket/index 是 dashed。
    #   直接拿 dashed 阈值做字符串比较会把紧凑格式的历史整段捞进来（方向相反）。
    #   → 用 replace() 归一成紧凑后再比，两种格式都按同一时间轴过滤。
    lo_compact = lo.replace("-", "")
    rows = con.execute(
        "select d.series_id,d.trade_date,d.close,d.volume,s.kind,s.name "
        "from scan_daily d join scan_series s on d.series_id=s.series_id "
        "where s.kind in ('industry_board','concept_basket') "
        "and replace(d.trade_date,'-','')>=?", (lo_compact,)).fetchall()
    by = collections.defaultdict(lambda: {"c": {}, "a": {}})
    meta = {}
    for sid, dt, close, vol, kind, name in rows:
        d = _norm_date(dt)
        c = float(close or 0)
        v = float(vol or 0)
        if c > 0 and d:
            by[sid]["c"][d] = c
            by[sid]["a"][d] = c * v
        meta[sid] = {"kind": kind, "name": name}
    bc = {r[0]: float(r[1]) for r in con.execute(
        "select trade_date,close from scan_daily where series_id='CSI300' and trade_date>=?", (lo,))}
    out = {}
    for sid, v in by.items():
        cl, am = v["c"], v["a"]
        common = [d for d in base if d in cl and d in bc]
        if len(common) < RULES["min_common_trading_days"]:
            continue
        def excess(n):
            if len(common) < n + 1:
                return None
            a, b = common[-n - 1], common[-1]
            if not (cl.get(a) and bc.get(a)):
                return None
            return round(((cl[b] / cl[a] - 1) - (bc[b] / bc[a] - 1)) * 100, 2)
        aa = [am[d] for d in common if d in am]
        ratio = None
        if len(aa) >= 40:
            prev = statistics.mean(aa[-40:-20])
            if prev > 0:
                ratio = round(statistics.mean(aa[-20:]) / prev, 3)
        rets = [(cl[common[i]] / cl[common[i - 1]] - 1)
                for i in range(len(common) - 19, len(common))
                if cl.get(common[i - 1])]
        vol20 = round(statistics.pstdev(rets) * 100, 2) if len(rets) >= 10 else None
        e20 = excess(20)
        gate = RULES["market_gate"]
        hit = ((e20 is not None and abs(e20) > gate["abs_excess20_pp_gt"])
               or (ratio is not None and ratio > gate["amount_ratio_20_over_prev20_gt"]))
        out[sid] = {
            "board_name": meta[sid]["name"],
            "board_kind": meta[sid]["kind"],
            "as_of": common[-1],
            "common_trading_days": len(common),
            "excess_5_pp": excess(5),
            "excess_10_pp": excess(10),
            "excess_20_pp": e20,
            "amount_ratio_20_over_prev20": ratio,
            "volatility_20_pct": vol20,
            "market_gate_hit": hit,
        }
    return out, base[-1]


def event_links(radar, feed_window, valid_series, dropped):
    """只按标题精确匹配词表。返回 (links, no_link_reasons)。"""
    lo, hi = feed_window
    links = []
    reasons = collections.Counter()
    for e in sorted(radar.get("events") or [], key=lambda x: (x.get("event_date") or "", x.get("event_id") or "")):
        d = e.get("event_date") or ""
        if not (lo <= d <= hi):
            continue
        title = e.get("title") or ""
        matched = [k for k in KEYWORD_MAP if k in title]
        if not matched:
            nature = (e.get("nature") or {}).get("kind")
            if nature in ("BACKGROUND", "UNCLASSIFIED"):
                reasons["BACKGROUND_OR_UNCLASSIFIED"] += 1
            else:
                reasons["GENERIC_POLICY_NO_TITLE_KEYWORD"] += 1
            continue
        for kw in matched:
            tag, sid, bname, relation, rationale = KEYWORD_MAP[kw]
            if sid not in valid_series:
                dropped.append({"keyword": kw, "reason": "映射的板块序列不在库内：%s" % sid})
                continue
            src = e.get("source") or {}
            links.append({
                "event_id": e.get("event_id"),
                "title": title,
                "event_date": d,
                "url": src.get("url"),
                "publisher": src.get("name"),
                "doc_class": e.get("doc_class"),
                "nature_kind": (e.get("nature") or {}).get("kind"),
                "first_seen": e.get("first_seen"),
                "keyword": kw,
                "theme_tag": tag,
                "board_series": sid,
                "board_name": bname,
                "relation": relation,
                "rationale": rationale,
            })
    return links, dict(sorted(reasons.items()))


def historical_roles(roles_doc, theme_tag):
    """投影历史同类事件的 PIT 角色；映射不到就写原因，不补造。"""
    tid = HISTORY_THEME_MAP.get(theme_tag)
    if not tid:
        return {"status": "NO_MAPPED_HISTORY_THEME", "theme_id": None,
                "event_count": 0, "role_count": 0, "roles": [],
                "reason": "库内有 %d 个历史题材事件 / %d 条 PIT 角色，但没有与该标签精确同轴的 "
                          "theme_id；相邻不同轴的族不做模糊关联（宁缺不编）"
                          % (len(roles_doc.get("events") or {}),
                             (roles_doc.get("summary") or {}).get("pit_safe_roles", 0))}
    events = roles_doc.get("events") or {}
    matched = [(k, v) for k, v in events.items() if v.get("theme_id") == tid]
    rows = []
    for eid, ev in matched:
        for rr in ev.get("roles") or []:
            if rr.get("pit_safe") is not True:
                continue
            evi = rr.get("evidence") or {}
            rows.append({
                "event_id": eid,
                "security_id": rr.get("security_id"),
                "name": rr.get("name"),
                "role": rr.get("role"),
                "identified_date": rr.get("identified_date"),
                "support_level": rr.get("support_level"),
                "evidence_url": evi.get("url"),
                "source_record": rr.get("source_record"),
            })
    if not rows:
        return {"status": "NO_PIT_SAFE_ROLE", "theme_id": tid,
                "event_count": len(matched), "role_count": 0, "roles": [],
                "reason": "映射到了历史主题，但该主题下没有 pit_safe == True 的角色记录"}
    return {
        "status": "PIT_SAFE_ROLES", "theme_id": tid,
        "event_count": len(matched), "role_count": len(rows),
        "roles": sorted(rows, key=lambda x: (x["identified_date"] or "", x["event_id"], x["security_id"] or "")),
        "note": "★ 这些是历史同类事件里的 PIT 角色记录（带识别日与来源），"
                "不是当前标的判断、不是推荐；事后信息未当事前证据。",
    }


def role_archive(roles_doc):
    """历史 PIT 角色层：按历史题材族组织，不硬贴到当前主题。

    这是「龙头 / 弹性」的合规替代材料 —— 只给历史同类事件里**已被可核记录点名或盘面观察到**
    的标的、关系性质、识别日与来源；不给当前判断、不给标签、不给排名。
    """
    events = roles_doc.get("events") or {}
    fam = collections.defaultdict(lambda: {"events": 0, "roles": []})
    for eid, ev in events.items():
        tid = ev.get("theme_id") or "UNKNOWN"
        fam[tid]["events"] += 1
        for rr in ev.get("roles") or []:
            if rr.get("pit_safe") is not True:
                continue
            evi = rr.get("evidence") or {}
            fam[tid]["roles"].append({
                "event_id": eid,
                "security_id": rr.get("security_id"),
                "name": rr.get("name"),
                "role": rr.get("role"),
                "identified_date": rr.get("identified_date"),
                "support_level": rr.get("support_level"),
                "evidence_url": evi.get("url"),
                "source_record": rr.get("source_record"),
            })
    out = []
    for tid, v in sorted(fam.items()):
        roles = sorted(v["roles"], key=lambda x: (x["identified_date"] or "",
                                                  x["event_id"], x["security_id"] or ""))
        out.append({"theme_id": tid, "event_count": v["events"],
                    "pit_safe_role_count": len(roles), "roles": roles[:6],
                    "roles_truncated": len(roles) > 6})
    return {
        "purpose": "历史同类事件里的 PIT 角色档案（合规替代材料，按历史题材族组织）",
        "theme_families": out,
        "total_events": len(events),
        "total_pit_safe_roles": sum(len(v["roles"]) for v in fam.values()),
        "note": "★ 全部是既有历史记录，带识别日与来源；不是当前标的判断、不是当前材料、"
                "不构成推荐。只取 pit_safe == True，事后信息未当事前证据。"
                "按历史题材族组织，★ 不把某个族硬贴到当前主题（同轴才映射，见 historical_roles 字段）。",
    }


def constituent_availability(sid, ms):
    """成分可得性：只写状态与原因，不列标的清单。"""
    kind = (ms or {}).get("board_kind") or ("concept_basket" if sid.startswith("CPT_")
                                           else "industry_board")
    if kind == "concept_basket":
        return {"status": "CURRENT_SNAPSHOT_ONLY",
                "reason": "概念篮子成员是建库当时成分的等权合成，不是历史成分；当前成分回溯有幸存者偏差"}
    return {"status": "NO_HISTORICAL_CONSTITUENTS",
            "reason": "行业板块是编制指数，库内无历史成分名单（ACCESS_GATED）；如实标注，不编造代表股"}


def build():
    radar_path = _latest("new_theme_radar_v*_view.json")
    roles_path = _latest("historical_market_roles_v*.json")
    radar = _load(radar_path)
    roles_doc = _load(roles_path)
    board = _load(BOARD)
    sem = _load(SEM)
    cal = _load(CAL)
    feed_window = board["tracks"]["mechanism"]["feed_window"]

    if not os.path.exists(DB):
        raise RuntimeError("缺 history_scan.db（1.3 GB 未入库）→ 无法计算行情结构量")
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        valid_series = {r[0] for r in con.execute(
            "select series_id from scan_series where kind in ('industry_board','concept_basket')")}
        structs, market_as_of = market_structure(con)
    finally:
        con.close()

    fuzzy = {e["series_id"] for e in (sem.get("entries") or []) if not e.get("interpretable")}
    dropped = []
    links, no_link_reasons = event_links(radar, feed_window, valid_series, dropped)

    # 按 board_series + theme_tag 聚类（不预设主题）
    groups = collections.defaultdict(list)
    for l in links:
        groups[(l["board_series"], l["theme_tag"])].append(l)

    all_ids = set(valid_series)
    candidates = []
    for (sid, tag), evs in sorted(groups.items()):
        ms = structs.get(sid)
        pubs = {e.get("publisher") for e in evs if e.get("publisher")}
        urls = {e.get("url") for e in evs if e.get("url")}
        first_in_window = any(str(e.get("first_seen") or "")[:10] >= feed_window[0] for e in evs)
        gate = bool(ms and ms["market_gate_hit"])
        if gate:
            sec, pos = "G1", "IN_WINDOW"
        else:
            sec, pos = "G3", "PRE_OBSERVATION" if first_in_window else "WATCH_ONLY"
        why = ("本周 %d 条官方文件标题命中「%s」，映射 %s（%s，%s）；"
               "行情结构%s命中门槛，%s" % (
                   len(evs), tag, sid, evs[0]["board_name"], evs[0]["relation"],
                   "已" if gate else "未",
                   "属双轨并列" if gate else "属前置观察窗口，行情未启动不等于无效"))
        candidates.append({
            # ★ 中文 theme_tag 不能用「去非 ASCII」当 ID（会全部退化成 X 而冲突）→ 取 tag 哈希
            "theme_id": "TD-%s-%s" % (sid, hashlib.sha256(tag.encode("utf-8")).hexdigest()[:8]),
            "section": sec,
            "time_position": pos,
            "board_series": sid,
            "board_name": evs[0]["board_name"],
            "board_kind": (ms or {}).get("board_kind"),
            "theme_tag": tag,
            "interpretable": sid not in fuzzy,
            "information_side": {
                "event_count": len(evs),
                "independent_publishers": len(pubs),
                "independent_urls": len(urls),
                "first_seen_in_window": first_in_window,
                "events": [{k: e[k] for k in (
                    "event_id", "title", "event_date", "url", "publisher", "doc_class",
                    "nature_kind", "first_seen", "keyword", "relation", "rationale")} for e in evs],
            },
            "market_side": ms or {
                "status": "NO_MARKET_DATA",
                "reason": "该板块在库内没有足够与 CSI300 对齐的交易日（< %d）"
                          % RULES["min_common_trading_days"],
            },
            "market_gate_hit": gate,
            "constituent_availability": constituent_availability(sid, ms),
            "why_now": why,
            "caveat": "标题/日期/URL 为可核事实；与板块的关联是显式词表映射，不证明因果；"
                      "行情量是历史描述统计，不是预测。",
            "gap_reason": None if ms else "行情侧数据不足（已写原因，不补造）",
            "historical_roles": historical_roles(roles_doc, tag),
        })

    # G2：仅行情结构命中、无可核信息侧理由（给全量规模，紧凑列表）
    info_sids = {c["board_series"] for c in candidates}
    g2 = []
    for sid, ms in sorted(structs.items()):
        if not ms["market_gate_hit"] or sid in info_sids or sid in fuzzy:
            continue
        g2.append({"board_series": sid, "board_name": ms["board_name"],
                   "board_kind": ms["board_kind"],
                   "excess_20_pp": ms["excess_20_pp"],
                   "amount_ratio_20_over_prev20": ms["amount_ratio_20_over_prev20"],
                   "volatility_20_pct": ms["volatility_20_pct"],
                   "note": "行情结构命中，但本周采集范围未发现可核的标题关键词关联 → 无可核理由，只作观察起点"})
    # ★ 互斥全覆盖：不可解释杂项桶中「行情命中但按可解释性门槛排除」的序列，
    #   既不进 G1/G3（无信息侧关联）也不进 G2（不可解释），必须**显式单列**，不能静默丢失。
    excluded_fuzzy = {sid for sid in all_ids
                      if sid in fuzzy and structs.get(sid, {}).get("market_gate_hit")
                      and sid not in info_sids}
    g2_sids = {x["board_series"] for x in g2}
    g4_count = len(all_ids) - len(info_sids) - len(g2_sids) - len(excluded_fuzzy)
    # 与「两侧都不命中」的原始定义对账：两者必须一致，否则分组互斥被破坏
    assert g4_count == sum(1 for sid in all_ids
                           if sid not in info_sids and sid not in g2_sids
                           and (sid not in structs or not structs[sid]["market_gate_hit"])), \
        "G4 计数与互斥分组不一致"

    sections = {
        "G1": {"label": RULES["sections"]["G1"],
               "items": [c for c in candidates if c["section"] == "G1"]},
        "G2": {"label": RULES["sections"]["G2"], "items": g2},
        "G3": {"label": RULES["sections"]["G3"],
               "items": [c for c in candidates if c["section"] == "G3"]},
        "G4": {"label": RULES["sections"]["G4"], "items": [],
               "total": g4_count,
               "reason": "两轨都不命中门槛的序列只给规模，不逐条铺开（避免用数量决定可见性）",
               "excluded_interpretable_false": {
                   "count": len(excluded_fuzzy),
                   "reason": "名称含「其他/综合」的兜底桶没有单一产业对象；其中行情结构命中的 "
                             "%d 条按可解释性门槛排除，不计入 G2/G4，也不单列为主题" % len(excluded_fuzzy),
               }},
    }

    doc_archive = role_archive(roles_doc)
    sources = [radar_path, roles_path, BOARD, SEM, CAL]
    doc = {
        "artifact": "theme_discovery",
        "artifact_version": "0.1",
        "purpose": "从本周可核市场信息 + 客观行情结构聚合出当前值得研究的概念板块与理由；不预设主题集合",
        "as_of": radar.get("as_of"),
        "market_as_of": market_as_of,
        "feed_window": list(feed_window),
        "feed_window_source": "frontier_board_v0_1.json:tracks.mechanism.feed_window（同源，不另算）",
        "rules": RULES,
        "counts": {
            "scanned_series": len(valid_series),
            "series_with_market_structure": len(structs),
            "market_gate_hit": sum(1 for x in structs.values() if x["market_gate_hit"]),
            "events_in_window": sum(1 for e in (radar.get("events") or [])
                                    if feed_window[0] <= (e.get("event_date") or "") <= feed_window[1]),
            # ★ 单位口径：事件数与关联条目数分开登记，不做混用
            "events_with_board_link": len({l["event_id"] for l in links}),
            "board_link_entries": len(links),
            "no_link_reasons": no_link_reasons,
            "theme_candidates": len(candidates),
            "by_section": {"G1": len(sections["G1"]["items"]), "G2": len(g2),
                           "G3": len(sections["G3"]["items"]), "G4": g4_count},
            "excluded_fuzzy_gate_hit": len(excluded_fuzzy),
            "dropped_mappings": len(dropped),
            "fuzzy_boards_excluded": len(fuzzy),
            "historical_role_families": len(doc_archive["theme_families"]),
        },
        "sections": sections,
        "historical_role_archive": doc_archive,
        "dropped_mappings": dropped,
        "observation_windows": [
            {"date": x["date"], "label": x.get("label"), "candidate_id": x.get("candidate_id"),
             "fact_vs_assumption": x.get("fact_vs_assumption")}
            for x in (cal.get("entries") or []) if x.get("kind") == "OBSERVATION_WINDOW"
        ],
        "limits": LIMITS,
        "source_sha256_16": {os.path.basename(p): _sha(p) for p in sources},
    }
    return doc


def check():
    """范围：与上游逐字节复算 / 词表校验 / 互斥计数 / URL / 禁用字段与措辞。

    ★ CI 无 history_scan.db（1.3 GB 不入库）：行情结构量部分**显式 SKIP 降级**，
    仍跑完所有不依赖大库的形状 / 语义 / 禁用词校验；SKIP 范围必须打印，不得静默通过。
    """
    errs = []
    skips = []
    if not os.path.exists(OUT):
        print("FAIL 产物不存在：%s" % OUT)
        return 1
    doc = _load(OUT)
    db_available = os.path.exists(DB) and os.path.getsize(DB) > 0
    if db_available:
        rebuilt = build()
        if json.dumps(rebuilt, ensure_ascii=False, sort_keys=True) != \
           json.dumps(doc, ensure_ascii=False, sort_keys=True):
            errs.append("产物与上游重算结果不一致（周更后需 --write 重算）")
    else:
        skips.append("上游逐字节复算 + 行情结构量（缺 history_scan.db，CI 环境）")
        # ★ 无库时仍对账产物声明的 as_of / 规模自洽，避免「空跑也算 PASS」
        if doc.get("as_of") != doc.get("market_as_of"):
            errs.append("as_of 与 market_as_of 不一致")

    c = doc.get("counts") or {}
    s = doc.get("sections") or {}
    by = c.get("by_section") or {}
    for k in ("G1", "G2", "G3"):
        if by.get(k) != len((s.get(k) or {}).get("items") or []):
            errs.append("counts.by_section.%s 与 sections 不一致" % k)
    if by.get("G4") != (s.get("G4") or {}).get("total"):
        errs.append("counts.by_section.G4 与 total 不一致")
    if c.get("theme_candidates") != by.get("G1", 0) + by.get("G3", 0):
        errs.append("主题候选数不等于 G1+G3")
    # ★★ 单位口径自洽：事件数 + 未命中事件数 == 窗口事件数（关联条目数另算）
    try:
        if c.get("events_with_board_link") + sum(c.get("no_link_reasons", {}).values()) != \
           c.get("events_in_window"):
            errs.append("事件计数不守恒：命中事件数 + 未命中原因合计 != 窗口事件数")
        if c.get("board_link_entries", 0) < c.get("events_with_board_link", 0):
            errs.append("关联条目数不得少于命中事件数")
        if sum(by.get(k, 0) for k in ("G1", "G2", "G3", "G4")) + \
           c.get("excluded_fuzzy_gate_hit", 0) != c.get("scanned_series"):
            errs.append("分组不互斥/不全覆盖：G1–G4 + 排除的杂项桶 != 扫描序列数")
    except TypeError:
        errs.append("计数单位字段缺失或类型错误（事件数 / 条目数 / 排除数）")
    for k in ("G1", "G3"):
        for it in (s.get(k) or {}).get("items") or []:
            if not it.get("interpretable"):
                errs.append("不可解释杂项桶进入 %s：%s" % (k, it.get("board_series")))
            for e in (it.get("information_side") or {}).get("events") or []:
                if not str(e.get("url") or "").startswith(("http://", "https://")):
                    errs.append("事件缺可核 URL：%s" % e.get("event_id"))
            if not it.get("why_now") or not it.get("caveat"):
                errs.append("主题候选缺理由 / 边界：%s" % it.get("theme_id"))
            ca = it.get("constituent_availability") or {}
            if not ca.get("status") or not ca.get("reason"):
                errs.append("主题候选缺成分可得性状态/原因：%s" % it.get("theme_id"))
    arc = doc.get("historical_role_archive") or {}
    fams = arc.get("theme_families") or []
    if arc.get("total_events") != sum(f.get("event_count", 0) for f in fams):
        errs.append("历史角色档案 event 总数与族加总不一致")
    if arc.get("total_pit_safe_roles") != sum(f.get("pit_safe_role_count", 0) for f in fams):
        errs.append("历史角色档案 PIT 角色总数与族加总不一致")
    for f in fams:
        for rr in f.get("roles") or []:
            if not rr.get("identified_date") or not rr.get("role"):
                errs.append("历史角色缺识别日 / 角色类型：%s" % rr.get("security_id"))
    if c.get("historical_role_families") != len(fams):
        errs.append("counts.historical_role_families 与档案不一致")
    bad = _forbidden_keys(doc)
    if bad:
        errs.append("出现打分/排序/概率/预测字段：%s" % ", ".join(bad[:5]))
    blob = json.dumps(doc, ensure_ascii=False)
    for w in BANNED_WORDS + BANNED_LABELS:
        if w in blob:
            errs.append("出现禁止措辞或占位符：%s" % w)
    # 词表指向的序列必须真实存在（无库时退化为「产物内登记的序列 ID 非空」）
    if db_available:
        con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
        valid = {r[0] for r in con.execute(
            "select series_id from scan_series where kind in ('industry_board','concept_basket')")}
        con.close()
        for kw, v in KEYWORD_MAP.items():
            if v[1] not in valid:
                errs.append("词表映射的序列不存在：%s -> %s" % (kw, v[1]))
    else:
        skips.append("词表→库内序列存在性（缺 history_scan.db）")
        # 无库时退化为形状校验：BK+数字（行业板块）或 CPT_xxx（概念篮子）
        for kw, v in KEYWORD_MAP.items():
            sid = str(v[1] or "")
            if not (sid.startswith("BK") and sid[2:].isdigit()) and not sid.startswith("CPT_"):
                errs.append("词表映射的序列 ID 形状不合法：%s -> %s" % (kw, sid))
    for tag, tid in HISTORY_THEME_MAP.items():
        if not tid:
            errs.append("历史主题映射为空：%s" % tag)

    if errs:
        for e in errs:
            print("FAIL " + e)
        print("--check：%d 项 FAIL" % len(errs))
        return 1
    scope = "上游逐字节复算 / 词表双向校验 / 互斥计数 / 事件 URL / 禁用字段与措辞"
    if skips:
        scope += "（SKIP：%s）" % "；".join(skips)
    print("--check PASS · 范围：%s · 扫描 %d 序列 · 主题候选 %d · G2 %d 条"
          % (scope, c["scanned_series"], c["theme_candidates"], by.get("G2", 0)))
    return 0


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        d = build()
        _dump(OUT, d)
        print("--write OK · as_of %s · 扫描 %d 序列 · 主题候选 %d · 各段 %s"
              % (d["as_of"], d["counts"]["scanned_series"],
                 d["counts"]["theme_candidates"], d["counts"]["by_section"]))
        return 0
    return check()


if __name__ == "__main__":
    sys.exit(main())
