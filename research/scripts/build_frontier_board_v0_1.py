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
    out["note"] = "历史统计，未校准，不是未来概率；只作行情附注，不参与研究增量验收"
    return out if any(v is not None for k, v in out.items() if k != "note") else None


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
    # G1→G4，组内保持产物原序（不按收益重排 —— 产物已有顺序即研究浏览顺序）
    ordered = sorted(enumerate(cards), key=lambda p: (GROUP_ORDER.index(p[1].get("group", "G4"))
                                                      if p[1].get("group") in GROUP_ORDER else 99, p[0]))
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
        })

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
            "meaning": "研究浏览优先顺序（产物已有分组，无分数）；不是收益排序、不是概率、不是买卖建议",
            "attention_label_rule": ATTENTION_BY_GROUP,
            "internal_wilson_score": "本产物不含任何启发式打分字段；那类字段只存在于评估视图，用于对照实验",
        },
        "counts": {
            "items": len(items),
            "by_group": {g: sum(1 for x in items if x["group"] == g) for g in GROUP_ORDER},
            "by_track": {"STATISTICAL": len(items)},
            "with_mechanism_link": sum(1 for x in items if x["mechanism_reason"]),
            "mechanism_feed": len(feed),
            "calendar_entries": len(cal_entries),
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
            "★ 本产物不含任何启发式打分字段（评估视图的内部排序不进入默认页面）。",
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
        errs.append("order 必须连续，且按 G1→G4 后组内原序")
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
