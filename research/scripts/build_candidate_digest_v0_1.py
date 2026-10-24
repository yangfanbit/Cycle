#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_candidate_digest_v0_1.py —— 统一「当前候选前瞻」汇总产物（v0.38）。

把四类来源合并成**一份**候选池，按可解释规则分组排序：
  · current_candidates.json       当前研究对象（6 个，研究记录 2026-10-08）
  · forward_observation_v0_2.json 专项前瞻候选（生肖 / 流感 / 台海）
  · pattern_discovery_v0_7.json   自动发现的当前/下月窗口（204 条）
  · market_snapshots/index.json   本期快照状态（已签发/草稿）

★ 合并只按**明确 ID**；名称相近不合并（宁可分开）。
★ 排序是**研究浏览优先顺序**，不是收益预测：G1 历史重复+OOS+时间优势 → G2 结构参照/催化临近 →
  G3 有当前事实但历史证据不足 → G4 探索/陈旧/无法检验。
★ 所有日期原样保留（price_as_of / research_as_of / snapshot_status），不把旧数据改成最新。
"""
from __future__ import annotations

import argparse, json, os, re, sys, time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
OUT_RE = re.compile(r"candidate_digest_v0_(\d+)\.json$")


def iso(d):
    """20261023 / 2026-10-23 / 2026-10-23T.. → 2026-10-23"""
    if not d:
        return None
    d = str(d)[:10]
    return "%s-%s-%s" % (d[:4], d[4:6], d[6:8]) if "-" not in d else d


def days_old(d, ref):
    from datetime import date
    try:
        a = date.fromisoformat(iso(d)); b = date.fromisoformat(iso(ref))
        return (b - a).days
    except Exception:
        return None


def load(name):
    p = os.path.join(CURRENT, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def latest(prefix):
    files = sorted([f for f in os.listdir(CURRENT) if re.match(prefix + r"_v0_(\d+)\.json$", f)],
                   key=lambda f: int(re.search(r"v0_(\d+)", f).group(1)))
    return files[-1] if files else None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--version", type=int, default=None)
    a = ap.parse_args(argv)

    pd_file = latest("pattern_discovery")
    pd = load(pd_file)
    fwd = load("forward_observation_v0_2.json")
    cand = load("current_candidates.json")
    snap = load(os.path.join("market_snapshots", "index.json"))

    cards = []

    # ① 自动发现的当前/下月窗口
    for p in pd["current_windows"]:
        oos_ok = p.get("oos_status") == "REPORTED" and (p.get("oos_hit_rate") or 0) >= 0.5
        g = ("G1" if (p["tier"] == "STRICT" and oos_ok) else
             "G2" if p["tier"] == "STRICT" else "G4")
        cards.append({
            "id": p["pattern_id"], "source": ["pattern_discovery"], "kind": "SEASONAL_WINDOW",
            "title": "%s · %d 月" % (p["board"], p["month"]),
            "subtitle": ("自建概念等权" if p["kind"] == "concept_basket" else "行业板块"),
            "why_now": "进入历史 %d 月窗口（%s）" % (p["month"], "当月" if p["current_status"] == "IN_WINDOW" else "下月"),
            "time_position": p["current_status"], "group": g,
            "history": {"n_years": p["n_years"], "median_excess_pct": p["median_excess_pct"],
                        "hit_rate": p["hit_rate"], "tier": p["tier"],
                        "oos_status": p.get("oos_status"), "oos_tests": p.get("oos_tests"),
                        "oos_hit_rate": p.get("oos_hit_rate"),
                        "years": p.get("years")},
            "representative_stocks": p.get("representative_stocks") or [],
            "gap": ("行业板块无历史成分 → 不绑个股" if p["kind"] != "concept_basket" else
                    p.get("rep_stock_gap")),
            "watch_next": "窗口内该板块相对沪深300的 20 日超额与广度",
            "invalidate_if": "窗口结束前中位超额 ≤ 0 且广度 < 0.5",
            "trigger_type": "CALENDAR_WINDOW",
            "dates": {"price_as_of": iso(pd["as_of"]), "research_as_of": iso(pd["generated_at"])},
            "evidence_ref": {"artifact": pd_file, "pattern_id": p["pattern_id"]},
        })

    # ② 专项前瞻候选（人工预设假设）
    for c in (fwd or {}).get("candidates", []):
        st = c.get("evidence_status")
        g = "G2" if st == "PRE_OBSERVATION" else "G4"
        cards.append({
            "id": c["candidate_id"], "source": ["forward_observation"], "kind": "SPECIAL_HYPOTHESIS",
            "title": c["title"], "subtitle": "专项假设（非全部规律）",
            "why_now": c.get("why_now"), "time_position": st, "group": g,
            "history": c.get("historical_stats") or {},
            "current_performance": c.get("current_performance"),
            "gap": c.get("not_a_candidate_reason"),
            "watch_next": c.get("what_to_watch"), "invalidate_if": c.get("invalidate_if"),
            "trigger_type": "ASSUMPTION",
            "dates": {"price_as_of": iso((c.get("current_performance") or {}).get("price_as_of")),
                      "research_as_of": iso((fwd or {}).get("as_of"))},
            "evidence_ref": {"artifact": "forward_observation_v0_2.json", "candidate_id": c["candidate_id"]},
        })

    # ③ 当前研究对象
    for x in (cand or {}).get("candidates", []):
        refs = x.get("reference_cases") or []
        drivers = x.get("drivers") or []
        scheduled = [d for d in drivers if d.get("category") in ("POLICY", "INDUSTRY", "STANDARD", "EVENT")]
        g = "G2" if refs else "G3"
        cards.append({
            "id": x["candidate_id"], "source": ["current_candidates"], "kind": "CURRENT_OBJECT",
            "title": x.get("display_name"), "subtitle": x.get("theme_type") or "",
            "why_now": (x.get("core_narrative") or "")[:180],
            "time_position": x.get("attention_state") or "UNKNOWN", "group": g,
            "history": {"reference_cases": refs},
            "trigger": {"type": "CURRENT_FACT+EXPECTATION",
                        "items": [{"category": d.get("category"), "note": (d.get("note") or "")[:160]}
                                  for d in scheduled[:3]]},
            "watch_next": (x.get("research_questions") or [None])[0],
            "invalidate_if": None,
            "trigger_type": "CURRENT_FACT",
            "watchboard": {
                "attention_state": x.get("attention_state"),
                "candidate_status": x.get("candidate_status"),
                "theme_type": x.get("theme_type"),
                "phase_window": x.get("phase_window"),
                "phase_evidence": x.get("phase_evidence"),
                "narrative_types": x.get("narrative_types"),
                "conflict_notes": x.get("conflict_notes"),
                "uncertainty_notes": x.get("uncertainty_notes"),
                "research_questions": x.get("research_questions"),
                "source_summary": x.get("source_summary"),
                "reference_cases": x.get("reference_cases"),
            },
            "dates": {"research_as_of": iso(x.get("snapshot_date") or (cand or {}).get("generated_at")),
                      "price_as_of": None},
            "evidence_ref": {"artifact": "current_candidates.json", "candidate_id": x["candidate_id"]},
        })

    # ④ 快照状态（只作数据日期披露，不生成候选）
    snaps = (snap or {}).get("snapshots") or []
    canonical = [s for s in snaps if s.get("status") == "CANONICAL"]

    for c in cards:
        d = c["dates"].get("research_as_of")
        n = days_old(d, pd["as_of"])
        c["dates"]["research_days_old"] = n
        c["dates"]["research_stale"] = bool(n is not None and n > 7)
    order = {"G1": 0, "G2": 1, "G3": 2, "G4": 3}
    cards.sort(key=lambda c: (order[c["group"]],
                              -(c["history"].get("median_excess_pct") or -99),
                              -(c["history"].get("oos_hit_rate") or 0)))

    doc = {
        "artifact": "candidate_digest", "artifact_version": "0.1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "as_of": iso(pd["as_of"]),
        "group_rule": {
            "G1": "历史重复 STRICT + 样本外 REPORTED 且命中≥50% + 当前/下月窗口",
            "G2": "历史重复 STRICT（无合格 OOS）或有结构参照的当前对象 / 前置观察",
            "G3": "有当前事实与驱动，但历史重复证据不足",
            "G4": "探索线索 / 数据陈旧 / 证据不足 / 无法检验",
            "note": "排序=研究浏览优先顺序，不是收益预测；同组按中位超额与 OOS 命中排序",
        },
        "counts": {g: sum(1 for c in cards if c["group"] == g) for g in ("G1", "G2", "G3", "G4")},
        "data_dates": {
            "price_as_of": pd["as_of"],
            "research_candidates_as_of": iso((cand or {}).get("generated_at")),
            "research_candidates_days_old": days_old((cand or {}).get("generated_at"), pd["as_of"]),
            "pattern_discovery_generated_at": iso(pd["generated_at"]),
            "snapshot_latest_canonical": (canonical[-1] if canonical else None),
            "snapshot_latest_any": (snaps[-1] if snaps else None),
            "market_strip_note": "市场状态条行情截至 2026-10-20（另有数据源）",
        },
        "sources": [
            {"id": "current_candidates", "file": "current_candidates.json", "count": len((cand or {}).get("candidates", [])),
             "date": (cand or {}).get("generated_at", "")[:10]},
            {"id": "forward_observation", "file": "forward_observation_v0_2.json",
             "count": len((fwd or {}).get("candidates", [])), "date": (fwd or {}).get("as_of")},
            {"id": "pattern_discovery", "file": pd_file, "count": len(pd["current_windows"]), "date": pd["as_of"]},
            {"id": "market_snapshots", "file": "market_snapshots/index.json", "count": len(snaps),
             "date": (snaps[-1] or {}).get("snapshot_date") if snaps else None},
        ],
        "cards": cards,
        "limitations": [
            "★ 不同来源日期不同（研究记录 / 行情 / 快照），卡片分别标注，不统一改写为最新。",
            "★ 分组是研究浏览优先顺序，不是概率、胜率或荐股。",
            "★ 行业板块无历史成分 → 不绑个股；概念代表股票为当前成分。",
            "★ 外部线索的内部同月结构支持 ≠ 外部报告已验证。",
        ],
    }

    if a.check:
        files = sorted([f for f in os.listdir(CURRENT) if OUT_RE.match(f)],
                       key=lambda f: int(OUT_RE.match(f).group(1)))
        if not files:
            print("FAIL: 汇总产物不存在")
            return 1
        d = json.load(open(os.path.join(CURRENT, files[-1]), encoding="utf-8"))
        errs = []
        for c in d["cards"]:
            if c["group"] not in ("G1", "G2", "G3", "G4"):
                errs.append("%s 分组非法" % c["id"])
            if c["group"] == "G1":
                h = c["history"]
                if h.get("tier") != "STRICT" or h.get("oos_status") != "REPORTED":
                    errs.append("%s 进 G1 但证据不足" % c["id"])
        if len(d["cards"]) < 100:
            errs.append("候选过少（%d）—— 自动发现窗口未接入？" % len(d["cards"]))
        if errs:
            print("FAIL: %s" % errs[:5])
            return 1
        print("PASS: 候选汇总一致（%d 张 · %s）" % (len(d["cards"]), d["counts"]))
        return 0

    print("候选 %d 张 · 分组 %s" % (len(cards), doc["counts"]))
    for c in cards[:5]:
        print("  [%s] %s · %s" % (c["group"], c["title"], c["time_position"]))
    if a.write:
        if a.version is None:
            print("FAIL: --write 需要 --version N")
            return 1
        out = os.path.join(CURRENT, "candidate_digest_v0_%d.json" % a.version)
        if os.path.exists(out):
            print("FAIL: 目标已存在：%s" % out)
            return 1
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        print("已生成 %s" % os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
