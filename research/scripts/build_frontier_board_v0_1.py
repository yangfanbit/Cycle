#!/usr/bin/env python3
"""build_frontier_board_v0_1.py —— 「前瞻排程」派生器（v0.77）。

## 为什么存在

v0.74 的工作台是「我提问 → 系统给历史对照」的 **pull / 事后研究**，与使用者的
真实目标（系统主动推出「接下来值得关注的概念板块 + 理由」）方向相反。
本脚本不改任何既有研究方法，只把**已经存在**的产物重新组织成一张主动清单：

  统计轨（季度更新）: candidate_digest_v0_*.json
      → 177 张卡，G1→G4 研究浏览顺序、why_now / watch_next / invalidate_if / history
  机制轨（每周更新）: new_theme_radar_v0_*_view.json + event_calendar_v0_1.json
      → 本周新增可核政策事件 + 已知日历事实 + A_CALENDAR 假说族前置观察

## 三条硬约束

1. **两轨并列，不做因果拼接**。统计理由与机制理由分别标注各自的 as_of；
   实测 177 张统计卡里能与雷达板块序列**精确**匹配上的只有 1 条 ——
   不给其余卡硬贴机制理由，也不做模糊关键词匹配（实测会误命中「贸易」←「石油加工贸易」）。
2. **零编造**。日历日期全部从 `forward_observation` 的 `ZODIAC_NAME.years` 抽取；
   机制事件全部来自雷达产物；谐音层只是**人工声明草案**，标
   `UNVERIFIED_ASSUMPTION`，不进统计、不参与排序、不构成篮子。
3. **排序分两种，不得混读**。默认页展示的是产物已有的 **G1→G4 研究浏览分组**
   （无分数）；内部 Wilson `priority_score` 只存在于评估视图，本产物**不得**出现。

用法：
  python build_frontier_board_v0_1.py --write    生成两个产物
  python build_frontier_board_v0_1.py --check    只读复算（含逐字段对账与不变量）
"""
import argparse
import glob
import hashlib
import json
import math
import os
import re
import sys
from datetime import datetime, timedelta

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
OUT_BOARD = os.path.join(CURRENT, "frontier_board_v0_1.json")
OUT_CALENDAR = os.path.join(CURRENT, "event_calendar_v0_1.json")

# ★ 一律动态选最新版本（版本号按**数字**排序，字符串排序会让 v0_9 < v0_12）
PATTERNS = {
    "digest": ("candidate_digest_v0_*.json", r"_v0_(\d+)\.json$"),
    "forward": ("forward_observation_v0_*.json", r"_v0_(\d+)\.json$"),
    "radar_view": ("new_theme_radar_v0_*_view.json", r"_v0_(\d+)_view\.json$"),
}

# 排序语义：只映射产物已有分组，**不引入任何分数**
GROUP_ORDER = ["G1", "G2", "G3", "G4"]
ATTENTION_BY_GROUP = {
    "G1": "值得关注",
    "G2": "可斟酌的决策点",
    "G3": "探索线索",
    "G4": "探索线索 / 仅留档",
}

TOP_N = 6
POS_RANK = {"IN_WINDOW": 3, "PRE_WINDOW": 2}
HIT_RATE_DEFINITION = ("历史该板块×月份窗口 n 年里，月收益跑赢沪深300 的年份数 / n；"
                       "是历史描述统计，不是事件命中，也不是对未来涨跌的预测")
SELECTION_RULE = {
    "hard_gate": "仅 G1（STRICT + OOS REPORTED + oos_hit_rate >= 0.5 + pit_eligible_years >= 1），"
                 "且 time_position != INSUFFICIENT",
    "sort_keys": ["oos_tests DESC", "oos_hit_rate DESC", "n_years DESC",
                  "time_position(IN_WINDOW>PRE_WINDOW>其它)", "Wilson 区间下界 DESC",
                  "median_excess_pct DESC（仅平局）", "id ASC（确定性）"],
    "month_quota": None,
    "month_quota_note": "不设同月配额：实测 G1 28 条里 27 条为 11 月，硬套同月≤3 只能凑出 4 条；"
                        "当前就是 11 月，全部为当月窗口是合理的",
    "fixed_sections_not_competing": ["CURRENT_OBJECT（6 条）", "SPECIAL_HYPOTHESIS（3 条）"],
    "note": "排序是证据强度/研究浏览优先顺序，不是收益预测、不是概率；"
            "Wilson 下界在 n=12 时区分度很低，只作平局裁决，不当分数展示",
}


def _wilson_low(k, n, z=1.96):
    """Wilson 95% 区间下界；小样本/高不确定性自动降权。n=0 → 0。"""
    if not n:
        return 0.0
    p = k / n
    den = 1 + z * z / n
    return (p + z * z / (2 * n)
            - z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / den


def _evidence_key(c):
    """★ 证据强度排序键（沿用 digest 的 rank_key 语义，但分组改为硬门槛而非键）。"""
    h = c.get("history") or {}
    n = h.get("n_years") or 0
    k = round((h.get("hit_rate") or 0) * n)
    oos_ok = 1 if h.get("oos_status") == "REPORTED" else 0
    return (-oos_ok, -(h.get("oos_tests") or 0), -(h.get("oos_hit_rate") or 0),
            -n, -POS_RANK.get(c.get("time_position"), 1), -_wilson_low(k, n),
            -(h.get("median_excess_pct") or -99), c.get("id") or "")


def _rank_reason(c):
    """一行可核的「为什么排到这里」。"""
    h = c.get("history") or {}
    n = h.get("n_years") or 0
    k = round((h.get("hit_rate") or 0) * n)
    pos = {"IN_WINDOW": "窗口内", "PRE_WINDOW": "窗口未开始"}.get(
        c.get("time_position"), c.get("time_position") or "—")
    return ("样本外 %s / %s 次（命中 %s）· 历史 %s 年（跑赢 %s 年）· "
            "Wilson 下界 %.3f · %s"
            % (h.get("oos_status") or "—", h.get("oos_tests") or 0,
               h.get("oos_hit_rate") or "—", n, k,
               _wilson_low(k, n), pos))

# ★★ 人工声明的映射草案（使用者 2026-11-07 提出）。不是数据、不是结论。
# 现有 ZODIAC_NAME 只到 LITERAL 层；后两层会改变研究问题与分母，必须另立 hypothesis_id。
CALENDAR_HYPOTHESIS = {
    "family": "A_CALENDAR",
    "pattern_id": "ZODIAC_NAME",
    "title": "生肖名称炒作（春节前 20 交易日 ~ 节后 20 交易日）",
    "role": "BEHAVIORAL_HYPOTHESIS",
    "not_a_theme": True,
    "note": "与基本面无关、生命周期极短；既有产物明写「不得赋予行业属性」。"
            "只作为前置观察窗口接入，不升级为可执行候选。",
    "mapping_layers": [
        {"layer": "LITERAL", "rule": "证券名称含当年生肖字",
         "examples": [], "status": "IN_EXISTING_ARTIFACT", "usage": "EXISTING_ARTIFACT",
         "note": "现有假设只到这一层。2027 羊年当前名称仅 2 只 → 无法构成篮子，"
                 "既有产物结论为 evidence_status=INSUFFICIENT，本轮不改写。"},
        {"layer": "HOMOPHONE", "rule": "同音/近音字映射（羊 / 洋 / 阳 / 扬）",
         "examples": ["九阳股份", "圣阳股份", "阳光电源"],
         "status": "UNVERIFIED_ASSUMPTION",
         "usage": "NOT_IN_STATISTICS_NOT_IN_RANKING_NOT_A_BASKET",
         "note": "人工声明草案，来自使用者举例；系统未核验证券名称与历史时点，"
                 "不进统计、不参与排序、不构成篮子。启用前必须另立 hypothesis_id。"},
        {"layer": "SEMANTIC", "rule": "语义关联（如「狼吃羊」类叙事）",
         "examples": [], "status": "UNVERIFIED_ASSUMPTION",
         "usage": "NOT_IN_STATISTICS_NOT_IN_RANKING_NOT_A_BASKET",
         "note": "外部事后报道出现过，库内无可核记录；只登记，不采信。"},
    ],
    "status_in_existing_artifact": "C_EXPLORATORY",
}

KNOWN_GAPS = [
    {"id": "PIT_NAME_SNAPSHOT_MISSING",
     "detail": "历史证券名称 / 改名 / 上市退市快照缺失。既有 forward_observation.limitations "
               "已自述「概念/名称候选池用当前快照回溯 → 存在幸存者偏差与成分变更偏差」；"
               "12 个年份里 10 个 testable=false 皆因此。周更行情不含此数据，本轮无法补齐。",
     "blocks": "任何生肖历史统计升级为线索"},
    {"id": "LAUNCH_DATE_DRIFTS",
     "detail": "启动点逐年漂移（2026 马年 6 月、2027 羊年 11 月），无固定提前量；"
               "窗口 start 只是「最早开始观察」，不是启动日。应采用触发式观察。",
     "blocks": "写死「提前 N 天」的日历规则"},
    {"id": "ONLY_LITERAL_MATCH",
     "detail": "现有假设只匹配生肖字面，不含谐音/语义；使用者举例的三只标的都不在池内。",
     "blocks": "把谐音标的并入现有统计分母"},
    {"id": "NO_FUTURE_POLICY_CALENDAR",
     "detail": "本版日历只含库内可核的农历新年与既有观察窗口；两会 / 政策生效日 / 指数调样 / "
               "行业大会等库内无可核来源，故不编造。周更时须由可核来源逐条补入。",
     "blocks": "声称已覆盖完整未来事件日历"},
]


def _latest(key):
    pat, rex = PATTERNS[key]
    fs = [f for f in glob.glob(os.path.join(CURRENT, pat)) if re.search(rex, f)]
    if not fs:
        raise RuntimeError("找不到输入产物：%s" % pat)
    fs.sort(key=lambda f: int(re.search(rex, f).group(1)))
    return fs[-1]


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def _month_hint(card):
    """窗口只有月份级，产物无精确起止日 —— 如实说明，不推算交易日。"""
    m = re.search(r"-M(\d{1,2})$", card.get("id") or "")
    if m:
        return "%s 月窗口（月份级；产物无精确起止日，不推算具体交易日）" % int(m.group(1))
    return "无固定月份窗口（专项假设 / 当前对象）"


def _stat_reason(card):
    h = card.get("history") or {}
    keep = ("n_years", "hit_rate", "median_excess_pct", "tier", "oos_status", "oos_tests",
            "oos_hit_rate", "pit_eligible_years", "pit_first_year", "pit_basis",
            "discovery_basis", "evidence_grade")
    out = {k: h.get(k) for k in keep if k in h}
    n = h.get("n_years") or 0
    out["hit_years"] = round((h.get("hit_rate") or 0) * n) if n else None
    out["hit_rate_definition"] = HIT_RATE_DEFINITION
    # ★ 字段名与评估视图的打分字段 wilson_low 区分开：这里是公开的统计区间下界，
    #   不是 INTERNAL_EVAL_ONLY 的启发式打分，也不参与「默认页零打分字段」的禁用扫描。
    out["wilson_ci_low"] = _wilson_low(out["hit_years"] or 0, n)
    out["note"] = "历史统计，未校准，不是未来概率；只作行情附注，不参与研究增量验收"
    return out if any(v is not None for k, v in out.items() if k not in ("note", "hit_rate_definition")) else None


def build():
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    paths = {k: _latest(k) for k in PATTERNS}
    digest, forward, radar = (_load(paths[k]) for k in ("digest", "forward", "radar_view"))

    # ── 日历事实：全部从既有产物抽取，不手写日期 ──
    zodiac = next((p for p in forward.get("patterns", [])
                   if p.get("pattern_id") == "ZODIAC_NAME"), None)
    if not zodiac:
        raise RuntimeError("forward_observation 里找不到 ZODIAC_NAME 假设")
    years = zodiac.get("years") or []
    cal_entries = []
    for y in years:
        cal_entries.append({
            "date": y["lunar_new_year"], "kind": "LUNAR_NEW_YEAR",
            "year": y["year"], "animal": y.get("animal"),
            "name_matches_in_current_snapshot": y.get("name_matches"),
            "testable_in_existing_artifact": y.get("testable"),
            "source": "%s:patterns[ZODIAC_NAME].years" % os.path.basename(paths["forward"]),
            "verification": "DERIVED_FROM_EXISTING_ARTIFACT",
            "fact_vs_assumption": "FACT",
        })
    zodiac_cand = next((c for c in forward.get("candidates", [])
                        if c.get("candidate_id") == "CAND-ZODIAC-2027"), None)
    if zodiac_cand:
        w = zodiac_cand.get("window") or {}
        for key, label in (("start", "前置观察窗口开始"), ("peak", "农历新年 / 峰值"),
                           ("end", "前置观察窗口结束")):
            if w.get(key):
                cal_entries.append({
                    "date": w[key], "kind": "OBSERVATION_WINDOW", "label": label,
                    "candidate_id": zodiac_cand["candidate_id"],
                    "source": "%s:candidates[CAND-ZODIAC-2027].window" % os.path.basename(paths["forward"]),
                    "verification": "DERIVED_FROM_EXISTING_ARTIFACT",
                    "fact_vs_assumption": "ASSUMPTION（窗口为人工设定的观察起点，不是行情启动日）",
                })
    cal_entries.sort(key=lambda x: (x["date"], x["kind"]))

    calendar = {
        "artifact": "event_calendar", "artifact_version": "0.1", "generated_at": now,
        "as_of": forward.get("as_of"),
        "track": "MECHANISM", "cadence": "WEEKLY",
        "scope_note": "本版只登记库内可核的日历事实与既有观察窗口；"
                      "不含任何推测、编造或未来政策日程。周更时由可核来源逐条补入。",
        "entries": cal_entries,
        "hypotheses": [CALENDAR_HYPOTHESIS],
        "known_gaps": KNOWN_GAPS,
        "source_sha256_16": {os.path.basename(paths[k]): _sha(paths[k])
                             for k in ("forward",)},
    }

    # ── 机制信息流：本周新增的可核事件（动态：以雷达最新事件日往前 7 天） ──
    evs = radar.get("events") or []
    dates = sorted({e.get("event_date") for e in evs if e.get("event_date")})
    if not dates:
        raise RuntimeError("雷达展示包无事件日期")
    t_end = dates[-1]
    dt_end = datetime.strptime(t_end, "%Y-%m-%d")
    t_start = (dt_end - timedelta(days=7)).strftime("%Y-%m-%d")

    feed = []
    for e in sorted(evs, key=lambda x: (x.get("event_date") or "", x.get("event_id") or "")):
        d = e.get("event_date") or ""
        if not (t_start <= d <= t_end):
            continue
        src = e.get("source") or {}
        feed.append({
            "event_id": e.get("event_id"), "date": d, "title": e.get("title"),
            "publisher": src.get("name") or src.get("publisher"),
            "url": src.get("url"), "doc_class": e.get("doc_class"),
            "theme_tags": e.get("theme_tags") or [],
            "fact_vs_assumption": "FACT_PUBLISHED_DOCUMENT",
            "caveat": "已发布文件的标题 / 日期 / URL 是事实；与板块的关联是关键词匹配，不证明因果",
        })

    # ── 机制理由：**只按 board_series 精确匹配**，不做子串/语义扩圈 ──
    series_events = {}
    for e in evs:
        for l in (e.get("theme_links") or []):
            sid = l.get("board_series")
            if sid:
                series_events.setdefault(sid, []).append(e)

    items = []
    cards = digest.get("cards") or []
    # ★ v0.78：分组仍 G1→G4（全量列表），但**组内按证据强度**而不是产物原序 ——
    #   v0.77 用「分组优先 + 组内原序」把 digest 现成的 rank_key 覆盖掉了。
    ordered = sorted(enumerate(cards), key=lambda p: (
        GROUP_ORDER.index(p[1].get("group", "G4"))
        if p[1].get("group") in GROUP_ORDER else 99,
        _evidence_key(p[1]), p[0]))
    for order, (_, c) in enumerate(ordered):
        group = c.get("group", "G4")
        mech = None
        m = re.match(r"SEAS-([A-Za-z0-9_]+)-M\d+$", c.get("id") or "")
        if m and m.group(1) in series_events:
            e = sorted(series_events[m.group(1)], key=lambda x: x.get("event_date") or "")[-1]
            src = e.get("source") or {}
            mech = {
                "kind": "POLICY_EVENT_LINK", "relation": "EXACT_SERIES_MATCH",
                "board_series": m.group(1), "event_id": e.get("event_id"),
                "event_date": e.get("event_date"), "title": e.get("title"),
                "url": src.get("url"),
                "caveat": "同一板块序列上的已发布政策事件；序列匹配不证明因果，也不代表事件驱动该窗口",
            }
        items.append({
            "id": c.get("id"), "track": "STATISTICAL", "group": group, "order": order,
            "attention_label": ATTENTION_BY_GROUP.get(group, "探索线索 / 仅留档"),
            "title": c.get("title"), "subtitle": c.get("subtitle"),
            "kind": c.get("kind"), "time_position": c.get("time_position"),
            "window_hint": _month_hint(c),
            "why_now": c.get("why_now"),
            "statistical_reason": _stat_reason(c),
            "mechanism_reason": mech,
            "trigger_type": c.get("trigger_type"), "watch_next": c.get("watch_next"),
            "invalidate_if": c.get("invalidate_if"), "gap": c.get("gap"),
            "evidence_ref": c.get("evidence_ref"),
            "source_artifacts": c.get("source"),
            # ★★ v0.78：补回 v0.77 派生时漏掉的个股参照（105 张概念卡本来就有）
            "representative_stocks": (c.get("representative_stocks") or [])[:6],
            "representative_stocks_total": len(c.get("representative_stocks") or []),
            "stock_gap_reason": c.get("stock_gap_reason"),
        })

    # ── Top 6 精选：G1 硬门槛 + 证据强度排序，不加月份配额 ──
    def _gate(c):
        h = c.get("history") or {}
        return (c.get("group") == "G1" and h.get("tier") == "STRICT"
                and h.get("oos_status") == "REPORTED"
                and (h.get("oos_hit_rate") or 0) >= 0.5
                and (h.get("pit_eligible_years") or 0) >= 1
                and c.get("time_position") != "INSUFFICIENT")

    eligible = [c for c in cards if _gate(c)]
    top_cards = sorted(eligible, key=_evidence_key)[:TOP_N]
    top6 = [{"id": c["id"], "rank": i + 1, "rank_reason": _rank_reason(c)}
            for i, c in enumerate(top_cards)]
    fixed = {
        "current_objects": [c["id"] for c in cards if c.get("kind") == "CURRENT_OBJECT"],
        "special_hypotheses": [c["id"] for c in cards if c.get("kind") == "SPECIAL_HYPOTHESIS"],
    }

    board = {
        "artifact": "frontier_board", "artifact_version": "0.1", "generated_at": now,
        "source_kind": "DERIVED_FROM_EXISTING_ARTIFACTS",
        "purpose": "系统主动推出的前置观察清单：统计轨 + 机制轨并列，各自可核、互不冒充",
        "tracks": {
            "statistical": {
                "as_of": digest.get("as_of"), "cadence": "QUARTERLY",
                "source": os.path.basename(paths["digest"]),
                "note": "历史统计按季度全量重算；每周行情/信息更新不改本轨 as_of",
            },
            "mechanism": {
                "as_of": radar.get("as_of"), "cadence": "WEEKLY",
                "source": [os.path.basename(paths["radar_view"]),
                           os.path.basename(OUT_CALENDAR)],
                "note": "使用者每周触发、AI 辅助更新行情与市场信息后重算；"
                        "无后端、无常驻抓取、无新增 CI Job",
                "feed_window": [t_start, t_end],
            },
        },
        "group_rule": {
            "order": GROUP_ORDER,
            "source": digest.get("group_rule"),
            "meaning": "研究浏览优先顺序：分组 G1→G4，组内按证据强度；"
                       "不是收益排序、不是概率、不是买卖建议",
            "attention_label_rule": ATTENTION_BY_GROUP,
        },
        "selection_rule": SELECTION_RULE,
        "top6": top6,
        "fixed_sections": fixed,
        "hit_rate_definition": HIT_RATE_DEFINITION,
        "counts": {
            "items": len(items),
            "by_group": {g: sum(1 for x in items if x["group"] == g) for g in GROUP_ORDER},
            "by_track": {"STATISTICAL": len(items)},
            "with_mechanism_link": sum(1 for x in items if x["mechanism_reason"]),
            "with_representative_stocks": sum(1 for x in items if x["representative_stocks_total"]),
            "mechanism_feed": len(feed),
            "calendar_entries": len(cal_entries),
            "top6_eligible": len(eligible),
            "top6_selected": len(top6),
        },
        "limits": [
            "★ 两轨**并列**，统计理由与机制理由分别标注各自 as_of；不做因果拼接，"
            "不给每张统计卡硬贴机制理由（实测精确序列匹配仅 %d 条）。" %
            sum(1 for x in items if x["mechanism_reason"]),
            "★ 统计理由是历史重复与样本外检验结果，**未校准、不是未来概率**；"
            "5/10/20 日超额只作行情附注，不参与研究增量验收。",
            "★ 「值得关注 / 可斟酌的决策点」= 前置观察窗口 / 研究起点，"
            "**不是买卖点**；具体的买卖决策由使用者自行做出。",
            "★ 窗口只有**月份级**，产物无精确起止交易日，不推算具体交易日。",
            "★ 机制轨的事件标题/日期/URL 是可核事实，但与板块的关联是序列匹配，不证明因果。",
            "★ 日历只含库内可核事实；未来政策日程、历史证券名称快照尚未接入，见 event_calendar.known_gaps。",
            "★ 「命中率」= 历史该板块×月份窗口跑赢沪深300 的年份占比，**不是**事件命中，"
            "也不预测未来涨跌；页面一律显示为「历史跑赢 N/M 年」。",
            "★ 个股参照来自**当前概念成分 + 基准日历对齐**（幸存者/成分变更偏差）；"
            "行业板块无历史成分名单，如实标 NO_HISTORICAL_CONSTITUENTS，**不编造代表股**。",
            "★ 本产物不含启发式打分字段（评估视图的内部打分不进入默认页面）；"
            "wilson_ci_low 是公开统计区间下界，只作平局裁决与可核依据，不是分数。",
        ],
        "items": items,
        "mechanism_feed": feed,
        "calendar_ref": os.path.basename(OUT_CALENDAR),
        "source_sha256_16": {os.path.basename(p): _sha(p) for p in paths.values()},
    }
    return board, calendar, paths


def check():
    errs = []
    for p in (OUT_BOARD, OUT_CALENDAR):
        if not os.path.exists(p):
            print("FAIL 产物不存在：%s" % p)
            return 1
    board, calendar, paths = build()
    cur_board, cur_cal = _load(OUT_BOARD), _load(OUT_CALENDAR)

    def norm(o):
        o = dict(o)
        o.pop("generated_at", None)     # 运行时字段，不参与逐字节复算
        return json.dumps(o, ensure_ascii=False, sort_keys=True)

    if norm(cur_board) != norm(board):
        errs.append("frontier_board 与重新派生结果不一致（逐字段）")
    if norm(cur_cal) != norm(calendar):
        errs.append("event_calendar 与重新派生结果不一致（逐字段）")

    # ── 显式不变量（不只依赖重算） ──
    items = cur_board.get("items") or []
    if not items:
        errs.append("零条目前瞻排程不得通过校验")
    orders = [x["order"] for x in items]
    if orders != list(range(len(items))):
        errs.append("order 必须连续，且按 G1→G4 后组内证据强度")
    groups = [x["group"] for x in items]
    if groups != sorted(groups, key=lambda g: GROUP_ORDER.index(g) if g in GROUP_ORDER else 99):
        errs.append("默认顺序不是 G1→G4 研究浏览顺序")
    for x in items:
        if x["attention_label"] != ATTENTION_BY_GROUP.get(x["group"], "探索线索 / 仅留档"):
            errs.append("%s attention_label 与分组规则不符" % x["id"])
        m = x.get("mechanism_reason")
        if m:
            if m["relation"] != "EXACT_SERIES_MATCH":
                errs.append("%s 机制关联不是精确序列匹配" % x["id"])
            if not (m.get("url") or "").startswith(("http://", "https://")):
                errs.append("%s 机制关联缺可核 URL" % x["id"])
    for e in cur_board.get("mechanism_feed") or []:
        if not (e.get("url") or "").startswith(("http://", "https://")):
            errs.append("%s 机制事件 URL 不可核" % e.get("event_id"))
    blob = json.dumps(cur_board, ensure_ascii=False)
    for banned in ("priority_score", "wilson_low", "INTERNAL_EVAL_ONLY", "买入", "卖出",
                   "目标价", "仓位", "胜率", "推荐买入"):
        if banned in blob:
            errs.append("产物出现禁用字段/措辞：%s" % banned)
    tr = cur_board.get("tracks") or {}
    if not tr.get("statistical", {}).get("as_of") or not tr.get("mechanism", {}).get("as_of"):
        errs.append("两轨 as_of 缺失")
    if tr.get("statistical", {}).get("cadence") != "QUARTERLY" or \
       tr.get("mechanism", {}).get("cadence") != "WEEKLY":
        errs.append("两轨更新节奏声明错误")
    # 日历事实必须来自既有产物，不能出现来源不明的日期
    z = next((h for h in (cur_cal.get("hypotheses") or [])
              if h.get("pattern_id") == "ZODIAC_NAME"), None)
    if not z:
        errs.append("日历缺 A_CALENDAR / ZODIAC_NAME 假说登记")
    for layer in (z or {}).get("mapping_layers", []):
        if layer["layer"] != "LITERAL" and layer.get("status") != "UNVERIFIED_ASSUMPTION":
            errs.append("非字面映射层必须标 UNVERIFIED_ASSUMPTION：%s" % layer["layer"])
    for g in cur_cal.get("known_gaps") or []:
        if g["id"] == "PIT_NAME_SNAPSHOT_MISSING":
            break
    else:
        errs.append("日历缺 PIT_NAME_SNAPSHOT_MISSING 缺口声明")

    # ── v0.78 Top 6 / 个股 / 命中率口径不变量 ──
    by_id = {x["id"]: x for x in items}
    top = cur_board.get("top6") or []
    if len(top) != TOP_N:
        errs.append("Top 6 精选必须恰好 %d 条，实际 %d" % (TOP_N, len(top)))
    if len({t["id"] for t in top}) != len(top):
        errs.append("Top 6 出现重复 id")
    for i, t in enumerate(top, 1):
        x = by_id.get(t["id"])
        if not x:
            errs.append("Top 6 的 %s 不在 items 里" % t["id"])
            continue
        if t["rank"] != i:
            errs.append("Top 6 rank 不连续：%s" % t["id"])
        h = x.get("statistical_reason") or {}
        ok = (x["group"] == "G1" and h.get("tier") == "STRICT"
              and h.get("oos_status") == "REPORTED"
              and (h.get("oos_hit_rate") or 0) >= 0.5
              and (h.get("pit_eligible_years") or 0) >= 1
              and x.get("time_position") != "INSUFFICIENT")
        if not ok:
            errs.append("Top 6 的 %s 不满足 G1 硬门槛" % t["id"])
        if not t.get("rank_reason"):
            errs.append("Top 6 的 %s 缺可核排序理由" % t["id"])
    # 与按同一规则重算的前 6 完全一致
    cards = _load(paths["digest"]).get("cards") or []
    def _gate2(c):
        h = c.get("history") or {}
        return (c.get("group") == "G1" and h.get("tier") == "STRICT"
                and h.get("oos_status") == "REPORTED"
                and (h.get("oos_hit_rate") or 0) >= 0.5
                and (h.get("pit_eligible_years") or 0) >= 1
                and c.get("time_position") != "INSUFFICIENT")
    want = [c["id"] for c in sorted((c for c in cards if _gate2(c)),
                                    key=_evidence_key)[:TOP_N]]
    if [t["id"] for t in top] != want:
        errs.append("Top 6 与证据强度规则复算不一致（产物 %s vs 复算 %s）"
                    % ([t["id"] for t in top], want))
    fixed = cur_board.get("fixed_sections") or {}
    for key in ("current_objects", "special_hypotheses"):
        for cid in fixed.get(key) or []:
            if cid not in by_id:
                errs.append("固定区 %s 的 %s 不在 items 里" % (key, cid))
        if set(fixed.get(key) or []) & {t["id"] for t in top}:
            errs.append("固定区 %s 与 Top 6 不得重复" % key)
    # 个股字段必须完整，且无编造
    if cur_board["counts"]["with_representative_stocks"] == 0:
        errs.append("个股参照字段丢失（v0.77 的缺陷）")
    for x in items:
        if "representative_stocks" not in x or "stock_gap_reason" not in x:
            errs.append("%s 缺个股/缺股原因字段" % x["id"])
            break
        if x["representative_stocks_total"] == 0 and not x["stock_gap_reason"] \
           and x["kind"] == "SEASONAL_WINDOW":
            errs.append("%s 无个股却未写明缺股原因" % x["id"])
        for s in x["representative_stocks"]:
            if not s.get("series_id") or not s.get("source"):
                errs.append("%s 个股记录缺可核字段" % x["id"])
    if HIT_RATE_DEFINITION not in json.dumps(cur_board, ensure_ascii=False):
        errs.append("缺命中率定义")
    if cur_board.get("hit_rate_definition") != HIT_RATE_DEFINITION:
        errs.append("hit_rate_definition 与常量不一致")

    if errs:
        for e in errs:
            print("  FAIL", e)
        print("\n--check：%d 项 FAIL。" % len(errs))
        return 1
    print("--check PASS · items=%d · 机制精确关联=%d · 机制事件=%d · 日历=%d · 两轨 as_of=%s / %s"
          % (len(items), cur_board["counts"]["with_mechanism_link"],
             cur_board["counts"]["mechanism_feed"], cur_board["counts"]["calendar_entries"],
             tr["statistical"]["as_of"], tr["mechanism"]["as_of"]))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        return check()
    if not a.write:
        board, calendar, paths = build()
        print("输入：", ", ".join(os.path.basename(p) for p in paths.values()))
        print("items=%d  G1/G2/G3/G4=%s  机制精确关联=%d  机制事件=%d  日历=%d"
              % (board["counts"]["items"],
                 "/".join(str(board["counts"]["by_group"][g]) for g in GROUP_ORDER),
                 board["counts"]["with_mechanism_link"], board["counts"]["mechanism_feed"],
                 board["counts"]["calendar_entries"]))
        return 0
    board, calendar, _ = build()
    for path, obj in ((OUT_BOARD, board), (OUT_CALENDAR, calendar)):
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")
        print("已生成 %s（%d 字节）" % (os.path.relpath(path, REPO), os.path.getsize(path)))
    return check()


if __name__ == "__main__":
    sys.exit(main())
