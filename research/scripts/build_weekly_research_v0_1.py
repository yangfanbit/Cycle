#!/usr/bin/env python3
"""build_weekly_research_v0_1.py —— 本周最新研究（v0.80，机制轨周更视图）。

## 替代了什么
默认页固定区原先把「产业机制阶段：扩散（研究侧声明 2026-10-23）」放在首屏，
行情一更新就成了没有信息量的静态旧判断。本产物把它换成**本周新增可核证据 +
对应板块 + 前置观察窗口**，5/10/20 日超额退为行情附注（仍由 theme_market 承载）。

## 零编造
- 事件标题 / 日期 / URL / 发布主体 / 板块序列 / 关联理由全部**逐字投影**
  `new_theme_radar_v*_view.json` 的 `theme_links`；不做正文匹配、不做模糊匹配。
- 方向 → 当前研究主题用**显式映射表**，构建时双向校验（方向名精确相等 +
  candidate_id 在 current_candidates 中存在），失败写 `dropped[]`，宁缺不编。
- 本周窗口取自 `frontier_board.mechanism_feed_window`（同源，不另算一份）。
- 没命中的方向**写原因**，不补造关联；不产出概率 / 打分 / 买卖措辞。
- 「前置观察窗口」= 事件 `time.observe_from`（真实可用时点）与日历中
  `OBSERVATION_WINDOW` 条目；不是行情启动日。

## 确定性
不写 `generated_at`；`source_sha256_16` 对账四个上游文件。
用法：--write / --check
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
CAL = os.path.join(CURRENT, "event_calendar_v0_1.json")
BOARD = os.path.join(CURRENT, "frontier_board_v0_1.json")
CC = os.path.join(CURRENT, "current_candidates.json")
OUT = os.path.join(CURRENT, "weekly_research_v0_1.json")

# ★ 显式映射：radar 的「研究方向」是上层分组，一个方向可对应多个当前研究主题。
#   构建时双向校验，不靠子串匹配。
DIRECTION_TO_CANDIDATES = {
    "具身智能与人形机器人": ["CC-2026-EMBODIED-AI"],
    "海上风电与风电设备": ["CC-2026-OFFSHORE-WIND"],
    "算电协同 / 算力与光互联": ["CC-2026-COMPUTE-POWER", "CC-2026-OPTICAL-LINK"],
    "智能驾驶与汽车产业": ["CC-2026-AUTO-SMARTDRIVE"],
    "医疗器械与脑机接口": ["CC-2026-BCI-MEDTECH"],
}

RULE = {
    "matching": "只按事件标题命中的关键词 → theme_links.board_series 精确关联；"
                "正文不建关联、不做模糊匹配、不按方向名反推板块",
    "direction_role": "research_directions 是上层分组（UPPER_GROUPING_ONLY），不等于具体细分主题；"
                      "具体主题看事件上的 theme_tags 与 theme_links.rationale",
    "no_match": "本周窗口内未命中即写原因（采集覆盖缺口 / 标题未命中），不补造关联",
    "window_source": "feed_window 取自 frontier_board.tracks.mechanism.feed_window，两处同源",
    "observation": "observe_from 是事件后可用时点（保守规则）；日历窗口是人工设定的观察起点，不是行情启动日",
}

LIMITS = [
    "★ 本产物是**本周研究材料**，不是行情终端：事件与板块是事实陈列，行情数字只作附注。",
    "★ 「值得关注 / 前置观察」= 研究起点，**不是买卖点**；具体买卖决策由使用者自行做出。",
    "★ 事件标题 / 日期 / URL 可核，但与板块的关联是关键词映射，**不证明因果**。",
    "★ 未命中的方向如实写原因；★ 方向是上层分组，**不是**具体细分主题。",
    "★ 阶段声明不出现在默认页，已下沉到内部评估视图的声明时间线（供事后回测留痕）。",
    "★ 行情推进后必须重算本产物（记录上游 sha256）；统计轨按季度、机制轨按周更，as_of 不互冒。",
]


def _latest_radar_view():
    files = glob.glob(os.path.join(CURRENT, "new_theme_radar_v*_view.json"))
    if not files:
        raise RuntimeError("找不到 new_theme_radar_v*_view.json")

    def ver(p):
        m = re.search(r"new_theme_radar_v(\d+(?:_\d+)*)_view\.json$", os.path.basename(p))
        return tuple(int(x) for x in m.group(1).split("_")) if m else ()

    return sorted(files, key=ver)[-1]


def _latest_round():
    """最新研究轮次（文件名含日期，字典序即时间序）—— 不硬编码某一轮。"""
    files = glob.glob(os.path.join(CURRENT, "research_round_*_v0_1.json"))
    return sorted(files)[-1] if files else None


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _dump(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def build():
    radar_path = _latest_radar_view()
    round_path = _latest_round()
    radar, cal, board, cc = (_load(p) for p in (radar_path, CAL, BOARD, CC))
    rd = _load(round_path) if round_path else None
    feed_window = board["tracks"]["mechanism"]["feed_window"]
    lo, hi = feed_window[0], feed_window[1]

    events = [e for e in (radar.get("events") or [])
              if lo <= (e.get("event_date") or "") <= hi]
    events.sort(key=lambda e: (e.get("event_date") or "", e.get("event_id") or ""))

    radar_dirs = {d["direction"]: d for d in (radar.get("research_directions") or [])}
    cc_ids = {c["candidate_id"] for c in (cc.get("candidates") or [])}

    dropped = []
    mapping = {}
    for name, cids in DIRECTION_TO_CANDIDATES.items():
        if name not in radar_dirs:
            dropped.append({"direction": name,
                            "reason": "radar research_directions 里无此方向（名称不精确相等）"})
            continue
        missing = [x for x in cids if x not in cc_ids]
        if missing:
            dropped.append({"direction": name,
                            "reason": "current_candidates 里找不到 %s" % ", ".join(missing)})
            continue
        mapping[name] = cids

    def slim(e):
        links = []
        for l in (e.get("theme_links") or []):
            links.append({
                "board_series": l.get("board_series"),
                "board_name": l.get("board_name"),
                "relation": l.get("relation"),
                "rationale": l.get("rationale") or "",
            })
        statuses = sorted({m.get("status") for m in (e.get("markets") or []) if m.get("status")})
        src = e.get("source") or {}
        return {
            "event_id": e.get("event_id"),
            "title": e.get("title"),
            "event_date": e.get("event_date"),
            "url": src.get("url"),
            "publisher": src.get("name"),
            "doc_class": e.get("doc_class"),
            "nature_kind": (e.get("nature") or {}).get("kind"),
            "status": e.get("status"),
            "theme_tags": e.get("theme_tags") or [],
            "boards": links,
            "observe_from": (e.get("time") or {}).get("observe_from"),
            "observation_status": statuses,
            "caveat": "标题 / 日期 / URL 为可核事实；与板块的关联是关键词映射，不证明因果。"
                      "观察起点按保守可用时点规则，事件日当天不计入反应。",
        }

    directions = []
    linked_ids = set()
    for name, d in sorted(radar_dirs.items()):
        hits = [e for e in events if name in (e.get("research_directions") or [])]
        for e in hits:
            linked_ids.add(e["event_id"])
        directions.append({
            "direction": name,
            "series": d.get("series") or [],
            "scope_note": d.get("scope_note") or "",
            "candidate_ids": mapping.get(name, []),
            "matched_events": [slim(e) for e in hits],
            "no_match_reason": None if hits else
                "本周窗口（%s → %s）未发现标题关键词命中该方向的可核文件；%s"
                % (lo, hi, d.get("scope_note") or "当前采集范围有限"),
        })

    # ★ 前端不重算：把「当前研究主题 → 本周研究结论」的索引在产物里算好
    theme_index = {}
    for d in directions:
        for cid in d["candidate_ids"]:
            theme_index[cid] = {
                "direction": d["direction"],
                "matched_count": len(d["matched_events"]),
                "no_match_reason": d["no_match_reason"],
                "candidate_ids_in_direction": list(d["candidate_ids"]),
            }

    other = [e for e in events if e["event_id"] not in linked_ids]
    by_nature = {}
    for e in other:
        k = (e.get("nature") or {}).get("kind") or "UNCLASSIFIED"
        by_nature[k] = by_nature.get(k, 0) + 1

    windows = [
        {"date": x["date"], "label": x.get("label"), "candidate_id": x.get("candidate_id"),
         "fact_vs_assumption": x.get("fact_vs_assumption"),
         "source": x.get("source")}
        for x in (cal.get("entries") or []) if x.get("kind") == "OBSERVATION_WINDOW"
    ]
    windows.sort(key=lambda x: x["date"])

    # ★ 本轮研究结论由 Research 侧轮次产物投影，前端不重算、不改写
    round_view = None
    if rd:
        round_view = {
            "round_id": rd.get("round_id"),
            "as_of": rd.get("as_of"),
            "source_file": os.path.basename(round_path),
            "counts": rd.get("counts"),
            "theme_reviews": [
                {"candidate_id": r["candidate_id"], "display_name": r["display_name"],
                 "verdict": r.get("verdict"), "new_evidence_count": r.get("new_evidence_count"),
                 "next_research_question": r.get("next_research_question")}
                for r in (rd.get("theme_reviews") or [])
            ],
            "new_watch_directions": rd.get("new_watch_directions") or [],
            "limits": rd.get("limits") or [],
        }

    sources = [radar_path, CAL, BOARD, CC] + ([round_path] if round_path else [])
    n_matched = sum(len(d["matched_events"]) for d in directions)
    return {
        "artifact": "weekly_research",
        "artifact_version": "0.1",
        "purpose": "本周新增可核证据 + 对应板块 + 前置观察窗口；替代默认页里的静态阶段声明",
        "cadence": "WEEKLY",
        "track": "MECHANISM",
        "as_of": radar.get("as_of"),
        "feed_window": list(feed_window),
        "feed_window_source": "frontier_board_v0_1.json:tracks.mechanism.feed_window",
        "rule": RULE,
        "counts": {
            "events_in_window": len(events),
            "linked_to_direction": n_matched,
            "other_verifiable_documents": len(other),
            "directions": len(directions),
            "directions_with_match": sum(1 for d in directions if d["matched_events"]),
            "observation_windows": len(windows),
            "dropped_mappings": len(dropped),
        },
        "directions": directions,
        "theme_index": dict(sorted(theme_index.items())),
        "other_verifiable_documents": {
            "count": len(other),
            "by_nature": dict(sorted(by_nature.items())),
            "note": "本周窗口内未与已映射研究方向建立关联的可核文件；"
                    "标题 / 日期 / URL 见「近 7 日可核事件」区，本产物不重复列一遍。",
        },
        "observation_windows": windows,
        "dropped_mappings": dropped,
        "research_round": round_view,
        "limits": LIMITS,
        "source_sha256_16": {os.path.basename(p): _sha(p) for p in sources},
    }


def check():
    errs = []
    if not os.path.exists(OUT):
        print("FAIL 产物不存在：%s" % OUT)
        return 1
    doc = _load(OUT)
    rebuilt = build()
    if json.dumps(rebuilt, ensure_ascii=False, sort_keys=True) != \
       json.dumps(doc, ensure_ascii=False, sort_keys=True):
        errs.append("产物与上游重算结果不一致（周更后需 --write 重算）")

    c = doc.get("counts") or {}
    if c.get("events_in_window") != c.get("linked_to_direction", 0) + c.get("other_verifiable_documents", 0):
        errs.append("互斥分组不自洽：窗口事件 != 已关联 + 其它可核文件")
    if sum(len(d["matched_events"]) for d in doc["directions"]) != c.get("linked_to_direction"):
        errs.append("directions 命中数与 counts 不一致")
    # 前端不重算：theme_index 必须与 directions 的映射逐项一致（dropped 允许但不静默）
    mapped_ids = set()
    by_direction = {}
    for d in doc["directions"]:
        mapped_ids.update(d["candidate_ids"])
        by_direction[d["direction"]] = d
    if mapped_ids != set(doc.get("theme_index") or {}):
        errs.append("theme_index 未覆盖全部已映射主题")
    for cid, v in (doc.get("theme_index") or {}).items():
        d = by_direction.get(v["direction"])
        if d is None or v["matched_count"] != len(d["matched_events"]) \
           or v["no_match_reason"] != d["no_match_reason"]:
            errs.append("theme_index 与 directions 不一致：%s" % cid)
    rr = doc.get("research_round")
    if rr:
        review_ids = {r["candidate_id"] for r in rr.get("theme_reviews") or []}
        if review_ids != set(doc.get("theme_index") or {}):
            errs.append("research_round.theme_reviews 未覆盖全部当前研究主题")
        for w in rr.get("new_watch_directions") or []:
            if not str((w.get("event") or {}).get("url") or "").startswith(("http://", "https://")):
                errs.append("观察方向缺可核 URL：%s" % w.get("direction_id"))
    for d in doc["directions"]:
        if not d["matched_events"] and not d["no_match_reason"]:
            errs.append("未命中方向缺原因：%s" % d["direction"])
        if d["no_match_reason"] and d["matched_events"]:
            errs.append("命中方向却写了未命中原因：%s" % d["direction"])
        for e in d["matched_events"]:
            if not (doc["feed_window"][0] <= e["event_date"] <= doc["feed_window"][1]):
                errs.append("事件越出本周窗口：%s" % e["event_id"])
            if not e.get("url", "").startswith(("http://", "https://")):
                errs.append("事件缺可核 URL：%s" % e["event_id"])
    for name, sha in (doc.get("source_sha256_16") or {}).items():
        p = os.path.join(CURRENT, name)
        if name.startswith("new_theme_radar_"):
            p = _latest_radar_view()
        if not os.path.exists(p) or _sha(p) != sha:
            errs.append("上游 sha256 不一致：%s" % name)
    # 禁用词：本产物不得出现未声明口径的预测 / 打分 / 买卖措辞
    flat = json.dumps(doc, ensure_ascii=False)
    for w in ("买入", "卖出", "目标价", "仓位", "推荐买入", "选股清单"):
        if w in flat:
            errs.append("出现禁止措辞：%s" % w)

    if errs:
        for e in errs:
            print("FAIL " + e)
        print("--check：%d 项 FAIL" % len(errs))
        return 1
    print("--check PASS · 范围：与四个上游逐字节复算 / 互斥计数 / 窗口与 URL / sha256 / 禁用词"
          " · 窗口 %s→%s · 事件 %d · 命中方向 %d/%d"
          % (doc["feed_window"][0], doc["feed_window"][1], c["events_in_window"],
             c["directions_with_match"], c["directions"]))
    return 0


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        doc = build()
        _dump(OUT, doc)
        print("--write OK · 窗口 %s→%s · 事件 %d · 命中方向 %d/%d · 前置观察窗口 %d"
              % (doc["feed_window"][0], doc["feed_window"][1],
                 doc["counts"]["events_in_window"], doc["counts"]["directions_with_match"],
                 doc["counts"]["directions"], doc["counts"]["observation_windows"]))
        return 0
    return check()


if __name__ == "__main__":
    sys.exit(main())
