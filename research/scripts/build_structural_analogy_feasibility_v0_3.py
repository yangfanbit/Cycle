"""Structural Analogy Feasibility v0.3 —— Driver Canonicalization 隔离实验。

**只改 Driver 维度**，其余维度（lifecycle / evidence_sequence / event / temporal / market）
与 v0.2 **逐字沿用同一规则**，以便做隔离对照。

Driver 维度新口径：
  candidate side : `narrative_types`（canonical，schema 的 narrativeType 枚举）
  historical side: driving 相位（start + accelerator）的 canonical driver 集合
  MATCH   —— 集合相等
  PARTIAL —— 交集非空且不等
  MISMATCH—— 两侧均非空、交集为空
  UNKNOWN —— 历史无 canonical driver，但 driving 文本存在
  NOT_AVAILABLE —— 历史 driving 相位无可编码文本

产物：
  structural_analogy_feasibility_v0_3.json
  structural_analogy_feasibility_candidates_v0_3.csv
"""
import collections
import csv
import io
import json
import os
import sqlite3
import sys
from datetime import date

ROOT = r"D:/@AW/投资/ThreeC"
REP = f"{ROOT}/research/research/reports"
CHECK = "--check" in sys.argv
OUT_JSON = f"{REP}/structural_analogy_feasibility_v0_3.json"
OUT_CSV = f"{REP}/structural_analogy_feasibility_candidates_v0_3.csv"

HIST_EVENT_TYPES = ["policy", "industry", "macro", "company", "market", "news", "holiday", "other"]
CAND_EV_TO_EVENT = {"POLICY": "policy", "INDUSTRY": "industry", "COMPANY": "company",
                    "MARKET": "market", "CAPITAL": "market", "MACRO": "macro",
                    "SENTIMENT": "other", "OTHER": "other"}
EVENT_TYPE_TO_DRIVER = {"policy": "POLICY", "company": "INDUSTRY", "market": "CAPITAL",
                        "macro": "EXTERNAL"}
STAGE_ORDER = ["EARLY_SIGNAL", "THEME_FORMING", "BROAD_CONFIRMATION", "MAIN_RISE", "PEAK",
               "RETRACEMENT", "SECONDARY", "DECLINING", "FIRST_DECLINE", "MAIN_END"]
STAGE_TO_PHASE = {"EARLY_SIGNAL": "EARLY_SIGNAL", "THEME_FORMING": "THEME_FORMING",
                  "BROAD_CONFIRMATION": "BROAD_CONFIRMATION", "MAIN_RISE": "EXPANSION",
                  "PEAK": "PEAK", "SECONDARY": "DECLINE", "FIRST_DECLINE": "DECLINE",
                  "RETRACEMENT": "DECLINE", "DECLINING": "DECLINE", "MAIN_END": "END"}
PHASE_TO_STAGE = {"EARLY_SIGNAL": "EARLY_SIGNAL", "THEME_FORMING": "THEME_FORMING",
                  "BROAD_CONFIRMATION": "BROAD_CONFIRMATION", "EXPANSION": "MAIN_RISE",
                  "PEAK": "PEAK"}
STAGE_NEIGHBOURS = {}
for _i, _s in enumerate(STAGE_ORDER):
    _n = []
    if _i > 0:
        _n.append(STAGE_ORDER[_i - 1])
    if _i < len(STAGE_ORDER) - 1:
        _n.append(STAGE_ORDER[_i + 1])
    STAGE_NEIGHBOURS[_s] = _n

CAND_MARKET_PROXY = json.load(io.open(f"{REP}/structural_analogy_candidate_market_map_v0_1.json",
                                      encoding="utf-8"))["mapping"]
CANON = json.load(io.open(f"{REP}/historical_driver_canonicalization_v0_1.json", encoding="utf-8"))
LEDGER = json.load(io.open(f"{REP}/historical_driver_evidence_ledger_v0_1.json",
                           encoding="utf-8"))["entries"]

DRIVING = ("start", "accelerator")
HIST_DRIVERS = {}
for e in LEDGER:
    if e["bucket"] in DRIVING and e["mapping_status"] in ("DIRECT", "DERIVED") and e["canonical_driver"]:
        HIST_DRIVERS.setdefault(e["cycle_id"], set()).add(e["canonical_driver"])
HIST_DRIVING_RAW = collections.Counter(e["cycle_id"] for e in LEDGER if e["bucket"] in DRIVING)

conn = sqlite3.connect(f"file:{ROOT}/research/database/cycle_research.db?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = json.load(io.open(f"{ROOT}/research/current/current_candidates.json", encoding="utf-8"))
exp = json.load(io.open(f"{ROOT}/exports/timeline_export_v1.json", encoding="utf-8"))
SNAPSHOT = cur.get("snapshot_date")
EV = {e["event_id"]: e for e in (exp.get("events") or [])}
allobj = exp["campaigns"] + exp["research_candidates"]


def events_of(o):
    out = [EV[i] for i in (o.get("event_ids") or []) if i in EV]
    if not out:
        key = o.get("campaign_id") or o.get("research_candidate_id")
        out = [e for e in EV.values() if e.get("campaign_id") == key]
    return sorted(out, key=lambda e: e["date"])


def stage_map(o):
    return {l["stage"]: l.get("start") for l in (o.get("lifecycle") or []) if l.get("start")}


HIST = []
for o in allobj:
    sm = stage_map(o)
    stages = sorted(sm, key=lambda s: STAGE_ORDER.index(s) if s in STAGE_ORDER else 99)
    last = max(sm.items(), key=lambda kv: kv[1])[0] if sm else None
    HIST.append({
        "object_id": o.get("campaign_id") or o.get("research_candidate_id"),
        "kind": "campaign" if o.get("campaign_id") else "research_candidate",
        "lifecycle_stages": stages, "stage_starts": sm,
        "terminal_stage": last,
        "terminal_phase": STAGE_TO_PHASE.get(last, "UNKNOWN") if last else "UNKNOWN",
        "canonical_drivers": sorted(HIST_DRIVERS.get(
            o.get("campaign_id") or o.get("research_candidate_id"), set())),
        "driving_raw_count": HIST_DRIVING_RAW.get(
            o.get("campaign_id") or o.get("research_candidate_id"), 0),
        "seq": [e.get("event_type") for e in events_of(o)],
        "n_events": len(events_of(o)),
        "family": next((t["name"] for t in (o.get("themes") or [])
                        if t.get("role") == "related" and t.get("theme_type") in ("industry", "sector")), None),
    })
HIST_BY_ID = {h["object_id"]: h for h in HIST}


def comparable_stage(h, cand_phase):
    target = PHASE_TO_STAGE.get(cand_phase)
    if not target or not h["lifecycle_stages"]:
        return None, "UNKNOWN", "历史无 lifecycle 或 candidate phase 不可映射"
    if target in h["stage_starts"]:
        return target, "MATCH", f"历史 lifecycle 含该阶段（锚点 {h['stage_starts'][target]}）"
    for nb in STAGE_NEIGHBOURS.get(target, []):
        if nb in h["stage_starts"]:
            return nb, "PARTIAL", f"历史不含 {target}，含相邻阶段 {nb}"
    return h["terminal_stage"], "MISMATCH", "历史不含该阶段及其相邻阶段"


def cand_profile(c):
    ev = c.get("evidence") or []
    dates = sorted([e.get("event_date") or e.get("source_date") for e in ev
                    if (e.get("event_date") or e.get("source_date"))])
    pw = c.get("phase_window") or {}
    start, end = pw.get("start"), pw.get("end")
    elapsed = None
    if start and SNAPSHOT:
        elapsed = (date(*[int(x) for x in SNAPSHOT.split("-")]) -
                   date(*[int(x) for x in start.split("-")])).days
    cid = c["candidate_id"]
    proxy = CAND_MARKET_PROXY.get(cid, {"status": "NOT_AVAILABLE", "series": [], "segment": None, "note": ""})
    cev = [e for e in (cur.get("_derived_events") or [])]
    return {
        "candidate_id": cid, "macro_theme": c.get("macro_theme"),
        "phase": c.get("attention_state"), "phase_stage": PHASE_TO_STAGE.get(c.get("attention_state")),
        "canonical_drivers": sorted(c.get("narrative_types") or []),
        "driver_category_axis": sorted(d["category"] for d in (c.get("drivers") or [])),
        "n_evidence": len(ev), "first_evidence": dates[0] if dates else None,
        "phase_window_start": start, "phase_window_end": end,
        "phase_window_end_semantics": "declared" if end else "unknown",
        "phase_elapsed_days_at_snapshot": elapsed,
        "market_proxy_status": proxy["status"], "market_proxy_series": proxy.get("series") or [],
        "reference_cases": [r["campaign_id"] for r in (c.get("reference_cases") or [])],
    }


CANDS = [cand_profile(c) for c in cur["candidates"]]

# candidate 派生事件（沿用 v0.2 同一规则）
CEV = json.load(io.open(f"{REP}/structural_analogy_candidate_events_v0_1.json",
                        encoding="utf-8"))["events"]
CEV_TYPES = collections.defaultdict(set)
for e in CEV:
    CEV_TYPES[e["candidate_id"]].add(e["event_type"])

matrix = []
for cp in CANDS:
    cev_types = sorted(CEV_TYPES.get(cp["candidate_id"], set()))
    for h in HIST:
        d = {}
        st, st_status, st_basis = comparable_stage(h, cp["phase"])
        d["lifecycle"] = st_status
        d["historical_stage_at_comparable_point"] = st
        d["lifecycle_basis"] = st_basis

        # ---- ★ Driver（新口径：canonical mechanism）----
        cs, hs = set(cp["canonical_drivers"]), set(h["canonical_drivers"])
        if not hs:
            d["drivers"] = "NOT_AVAILABLE" if h["driving_raw_count"] == 0 else "UNKNOWN"
        elif not cs:
            d["drivers"] = "NOT_AVAILABLE"
        elif cs == hs:
            d["drivers"] = "MATCH"
        elif cs & hs:
            d["drivers"] = "PARTIAL"
        else:
            d["drivers"] = "MISMATCH"
        d["driver_overlap"] = sorted(cs & hs)
        d["driver_overlap_count"] = len(cs & hs)
        # v0.2 旧口径（category 轴）保留对照
        hd_cat = sorted({EVENT_TYPE_TO_DRIVER[e["event_type"]] for e in events_of(
            next(o for o in allobj if (o.get("campaign_id") or o.get("research_candidate_id")) == h["object_id"]))
            if e.get("event_type") in EVENT_TYPE_TO_DRIVER})
        cc = set(cp["driver_category_axis"])
        d["drivers_legacy_category_axis"] = ("NOT_AVAILABLE" if not hd_cat else
                                             "MISMATCH" if not (cc & set(hd_cat)) else
                                             "MATCH" if cc == set(hd_cat) else "PARTIAL")

        # ---- 以下维度与 v0.2 规则一致（未改）----
        seqs = [x for x in h["seq"] if x in HIST_EVENT_TYPES]
        if len(seqs) < 2 or len(cev_types) < 2:
            d["evidence_sequence"] = "NOT_AVAILABLE"
        elif seqs[0] == cev_types[0]:
            d["evidence_sequence"] = "MATCH"
        elif len(set(seqs) & set(cev_types)) >= 2:
            d["evidence_sequence"] = "PARTIAL"
        else:
            d["evidence_sequence"] = "MISMATCH"

        if not cev_types or not h["seq"]:
            d["event_structure"] = "NOT_AVAILABLE"
        else:
            inter = set(cev_types) & set(h["seq"])
            d["event_structure"] = ("MISMATCH" if not inter else
                                    "MATCH" if set(cev_types) == set(h["seq"]) else "PARTIAL")

        d["temporal_structure"] = ("PARTIAL"
                                   if cp["phase_window_start"] and cp["phase_elapsed_days_at_snapshot"] is not None
                                   and h["stage_starts"].get(st or "") else "NOT_AVAILABLE")
        d["market_structure"] = "PARTIAL" if cp["market_proxy_status"] == "PARTIAL" else "NOT_AVAILABLE"

        good = ("MATCH", "PARTIAL")
        stage_ok = d["lifecycle"] == "MATCH"
        drv_strong = d["drivers"] == "MATCH" or (d["drivers"] == "PARTIAL" and d["driver_overlap_count"] >= 2)
        seq_ok = d["evidence_sequence"] in good
        evt_ok = d["event_structure"] in good
        if stage_ok and drv_strong and seq_ok and evt_ok:
            tier = "TIER_1_MULTI_DIMENSION"
        elif stage_ok and d["drivers"] in good and evt_ok:
            tier = "TIER_2_STAGE_DRIVER_EVENT"
        elif stage_ok and d["drivers"] in good:
            tier = "TIER_3_STAGE_DRIVER"
        else:
            tier = "TIER_4_INSUFFICIENT"

        matrix.append({
            "candidate_id": cp["candidate_id"], "historical_object": h["object_id"],
            "historical_kind": h["kind"], "historical_family": h["family"],
            "same_macro_theme": h["family"] == cp["macro_theme"],
            **d, "tier": tier,
            "matched_dimensions": sorted(k for k, v in d.items()
                                         if v in good and not k.endswith("_legacy_category_axis")),
        })

strict_a = [m for m in matrix if m["lifecycle"] == "MATCH" and m["drivers"] == "MATCH"
            and m["evidence_sequence"] == "MATCH" and m["event_structure"] == "MATCH"]
strict_b = [m for m in matrix if m["lifecycle"] == "MATCH" and m["drivers"] == "MATCH"]
tier1 = [m for m in matrix if m["tier"] == "TIER_1_MULTI_DIMENSION"]
_sb = sorted({m["candidate_id"] for m in strict_b})


def dist(dim):
    return dict(collections.Counter(m[dim] for m in matrix))


# v0.1 / v0.2 对照
V1 = json.load(io.open(f"{REP}/structural_analogy_feasibility_v0_1.json", encoding="utf-8"))
V2 = json.load(io.open(f"{REP}/structural_analogy_feasibility_v0_2.json", encoding="utf-8"))

res = {
    "artifact": "structural_analogy_feasibility", "artifact_version": "0.3",
    "generated_by": "research/scripts/build_structural_analogy_feasibility_v0_3.py",
    "supersedes_note": "v0.1 / v0.2 产物**保留不覆盖**",
    "snapshot": {"current_candidates_snapshot": cur.get("snapshot_date"),
                 "export_version": exp.get("timeline_export_version"),
                 "export_source_commit": exp.get("source_commit")},
    "status_vocabulary": ["MATCH", "PARTIAL", "UNKNOWN", "NOT_AVAILABLE", "MISMATCH"],
    "not_a": ["similarity score", "weighted score", "total score", "ranking", "best driver match",
              "prediction", "future outcome inference"],
    "isolated_change": {
        "scope": "**只改 Driver 维度**；lifecycle / evidence_sequence / event / temporal / market "
                 "与 v0.2 **逐字沿用同一规则**",
        "driver_v0_2": "candidate.drivers[].category（POLICY/INDUSTRY/CAPITAL/…，**类别轴**）"
                       " vs EVENT_TYPE_TO_DRIVER(历史 events)",
        "driver_v0_3": "candidate.narrative_types（**机制轴**，canonical）"
                       " vs 历史 driving 相位的 canonical driver 集合",
        "why": ("§四：Event Type ≠ Driver。v0.2 的 category 轴更接近**事件/来源类别**，"
                "不是**驱动机制**；v0.3 改用仓库既有的 narrativeType 机制枚举。"),
        "legacy_field_kept": "drivers_legacy_category_axis（保留 v0.2 口径作对照）",
    },
    "driver_canonicalization": {
        "canonical_vocabulary": CANON["canonical_vocabulary"]["values"],
        "vocabulary_source": CANON["canonical_vocabulary"]["source"],
        "historical_raw_driver_count": CANON["summary"]["historical_raw_driver_count"],
        "historical_canonical_driver_count": CANON["summary"]["historical_canonical_driver_count"],
        "driving_raw_count": CANON["summary"]["driving_raw_count"],
        "driving_canonical_driver_count": CANON["summary"]["driving_canonical_driver_count"],
        "by_mapping_status": CANON["summary"]["by_mapping_status"],
        "by_canonical_driver": CANON["summary"]["by_canonical_driver"],
        "driving_by_canonical_driver": CANON["summary"]["driving_by_canonical_driver"],
        "candidate_side_frequency": CANON["canonical_vocabulary"]["candidate_side_frequency"],
        "historical_not_available": CANON["canonical_vocabulary"]["historical_not_available"],
        "per_cycle": CANON["per_cycle"],
    },
    "dimension_definitions": {
        "lifecycle": "candidate.attention_state ↔ historical_stage_at_comparable_point（与 v0.2 同）",
        "drivers": "candidate.narrative_types ↔ 历史 driving 相位 canonical drivers（**v0.3 新口径**）",
        "drivers_legacy_category_axis": "v0.2 口径，保留对照",
        "evidence_sequence": "两侧统一到历史 event_type 词表（与 v0.2 同）",
        "event_structure": "candidate 派生事件类型集合 vs 历史 events（与 v0.2 同）",
        "temporal_structure": "candidate phase_window + 已历时 vs 历史阶段锚点（与 v0.2 同）",
        "market_structure": "candidate 同段行情代理（与 v0.2 同）",
    },
    "candidate_profiles": CANDS, "historical_pool": HIST, "matrix": matrix,
    "driver_before_after": {
        "v0_2_category_axis": V2["sensitivity_analysis"]["dimension_status_distribution"]["drivers"],
        "v0_3_canonical_mechanism_axis": dist("drivers"),
        "note": "两套口径不可直接比较数字高低 —— v0.2 是**类别轴**（宽），v0.3 是**机制轴**（严）。",
    },
    "sensitivity_analysis": {
        "STRICT_A_4dim_all_MATCH": {"rows": len(strict_a), "candidates": len({m["candidate_id"] for m in strict_a})},
        "STRICT_B_lifecycle_and_drivers_MATCH": {"rows": len(strict_b), "candidates": len(_sb),
                                                 "per_candidate": {c["candidate_id"]:
                                                                   [m["historical_object"] for m in strict_b
                                                                    if m["candidate_id"] == c["candidate_id"]]
                                                                   for c in CANDS}},
        "TIER_1_multi_dimension": {"rows": len(tier1), "candidates": len({m["candidate_id"] for m in tier1})},
        "dimension_status_distribution": {dim: dist(dim) for dim in
                                          ("lifecycle", "drivers", "drivers_legacy_category_axis",
                                           "evidence_sequence", "event_structure",
                                           "temporal_structure", "market_structure")},
        "tier1_same_vs_cross_family": {"same": sum(1 for m in tier1 if m["same_macro_theme"]),
                                       "cross": sum(1 for m in tier1 if not m["same_macro_theme"])},
    },
    "three_key_numbers": {
        "definition": "usable structural analogue = STRICT_B（lifecycle MATCH + drivers MATCH）",
        "candidates_with_structurally_usable_analogue": {"count": len(_sb), "ids": _sb},
        "candidates_with_only_theme_name_level_analogue": {
            "count": len([c for c in CANDS if c["candidate_id"] not in _sb and (c.get("reference_cases") or [])]),
            "ids": [c["candidate_id"] for c in CANDS if c["candidate_id"] not in _sb
                    and (c.get("reference_cases") or [])]},
        "candidates_with_no_usable_analogue": {
            "count": len([c for c in CANDS if c["candidate_id"] not in _sb and not (c.get("reference_cases") or [])]),
            "ids": [c["candidate_id"] for c in CANDS if c["candidate_id"] not in _sb
                    and not (c.get("reference_cases") or [])]},
        "note": "usable structural analogue != same-theme match",
    },
    "blocker_resolution_matrix": [
        {"blocker": "lifecycle semantic break", "v0_2": "RESOLVED",
         "v0_3": "RESOLVED（未变）", "resolution": "可比观测点口径（v0.2 引入，本轮未改）"},
        {"blocker": "candidate event entity", "v0_2": "RESOLVED",
         "v0_3": "RESOLVED（未变）", "resolution": "候选事件实体（v0.2 引入，本轮未改）"},
        {"blocker": "candidate market mapping", "v0_2": "PARTIALLY_RESOLVED",
         "v0_3": "PARTIALLY_RESOLVED（未变）",
         "resolution": "段代理（v0.2 引入）", "remaining_impact": "候选侧 2026 行情不可得 → 单向"},
        {"blocker": "historical driver structure", "v0_2": "BLOCKER",
         "v0_3": ("PARTIALLY_RESOLVED" if dist("drivers").get("MATCH", 0) > 0 else "UNRESOLVED"),
         "resolution": "Historical Driver Canonicalization v0.1（机制轴 + 相位拆分 + 价格结果排除）",
         "remaining_impact": ("历史 driving 文本 60/154 仍为 UNKNOWN(22)/NOT_AVAILABLE(38)；"
                              "`VALUATION_RESET` / `CYCLE_REVERSAL` 等在 candidate 侧无对应")},
        {"blocker": "phase_window.end", "v0_2": "UNRESOLVED",
         "v0_3": "UNRESOLVED（未变）", "resolution": "保持 null（v0.2 决定，本轮未改）"},
    ],
}
dims = res["sensitivity_analysis"]["dimension_status_distribution"]
res["overall_status"] = "PARTIALLY_FEASIBLE"
res["minimum_viable_scope"] = {
    "option": "C（Research-only exploration），上限为 B",
    "statement": ("Driver 已从**类别轴**换为**机制轴**（canonical narrativeType），可比性提升；"
                  "但严格口径 STRICT_A=%d 条 / STRICT_B=%d 候选；市场仍单向、temporal 仍单向。"
                  % (len(strict_a), len(_sb))),
    "not_yet_available": ["candidate-side 2026 market state", "双向 temporal",
                          "任何 similarity score / ranking"],
}

body = json.dumps(res, ensure_ascii=False, indent=1) + "\n"
if CHECK:
    if not os.path.exists(OUT_JSON):
        raise SystemExit("FAIL —— 产物不存在")
    if io.open(OUT_JSON, encoding="utf-8").read() != body:
        raise SystemExit("FAIL —— 与重算结果不一致（非 deterministic）")
    print("PASS —— 产物与重算结果逐字节一致（deterministic）。")
else:
    with io.open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    print("written", OUT_JSON)

with io.open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["candidate_id", "historical_object", "historical_family", "same_macro_theme",
                "lifecycle", "historical_stage_at_comparable_point", "drivers",
                "driver_overlap", "driver_overlap_count", "drivers_legacy_category_axis",
                "evidence_sequence", "event_structure", "temporal_structure", "market_structure",
                "tier", "matched_dimensions"])
    for m in matrix:
        w.writerow([m["candidate_id"], m["historical_object"], m["historical_family"],
                    m["same_macro_theme"], m["lifecycle"], m["historical_stage_at_comparable_point"],
                    m["drivers"], "|".join(m["driver_overlap"]), m["driver_overlap_count"],
                    m["drivers_legacy_category_axis"], m["evidence_sequence"], m["event_structure"],
                    m["temporal_structure"], m["market_structure"], m["tier"],
                    "|".join(m["matched_dimensions"])])
print("written", OUT_CSV)
print()
print("=== Driver 维度 before/after ===")
print("  v0.2 category axis :", res["driver_before_after"]["v0_2_category_axis"])
print("  v0.3 mechanism axis:", dist("drivers"))
print()
print("=== 全部维度 ===")
for k, v in res["sensitivity_analysis"]["dimension_status_distribution"].items():
    print(f"  {k:32s} {v}")
print()
print("tier:", dict(collections.Counter(m["tier"] for m in matrix)))
print("strict_a:", len(strict_a), "| strict_b:", len(_sb), _sb, "| tier1:", len(tier1),
      "same/cross:", res["sensitivity_analysis"]["tier1_same_vs_cross_family"])
