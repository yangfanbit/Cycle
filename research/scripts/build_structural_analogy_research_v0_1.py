"""Structural Analogy Research v0.1 —— Research-only Structural Analogy Engine。

四维结构对应（v0.1 成立判据）：
  D1 Lifecycle         candidate.current_phase ↔ historical_stage_at_comparable_point（stage-aligned）
  D2 Mechanism Driver  candidate.narrative_types ↔ 历史 driving 相位 canonical drivers
  D3 Evidence Sequence 证据出现的**顺序**（LCS），而非仅集合
  D4 Event Structure   event_type + chronology + linkage

**明确排除**（§六）：Market Structure（PARTIALLY_RESOLVED）、Temporal Structure（单向）
→ 记录为 `SUPPLEMENTARY_ONLY`，**不参与成立判据**。

**严禁**：similarity_score / weighted_score / confidence_score / ranking / best analogue / winner。

产物：
  research/research/reports/structural_analogy_research_v0_1.json
  research/research/reports/structural_analogy_research_candidates_v0_1.csv

用法：python research/scripts/build_structural_analogy_research_v0_1.py [--check]
"""
import collections
import csv
import io
import json
import os
import sys
from datetime import date

ROOT = r"D:/@AW/投资/ThreeC"
REP = f"{ROOT}/research/research/reports"
CHECK = "--check" in sys.argv
OUT_JSON = f"{REP}/structural_analogy_research_v0_1.json"
OUT_CSV = f"{REP}/structural_analogy_research_candidates_v0_1.csv"

HIST_EVENT_TYPES = ["policy", "industry", "macro", "company", "market", "news", "holiday", "other"]
CAND_EV_TO_EVENT = {"POLICY": "policy", "INDUSTRY": "industry", "COMPANY": "company",
                    "MARKET": "market", "CAPITAL": "market", "MACRO": "macro",
                    "SENTIMENT": "other", "OTHER": "other"}
STAGE_ORDER = ["EARLY_SIGNAL", "THEME_FORMING", "BROAD_CONFIRMATION", "MAIN_RISE", "PEAK",
               "RETRACEMENT", "SECONDARY", "DECLINING", "FIRST_DECLINE", "MAIN_END"]
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

LEVELS = ["STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL", "THEME_ONLY",
          "INSUFFICIENT_EVIDENCE", "NO_VALID_CORRESPONDENCE"]
DIM_STATUS = ["MATCH", "PARTIAL", "MISMATCH", "UNKNOWN", "NOT_AVAILABLE"]
GOOD = ("MATCH", "PARTIAL")

# ---- 输入 ----
cur = json.load(io.open(f"{ROOT}/research/current/current_candidates.json", encoding="utf-8"))
exp = json.load(io.open(f"{ROOT}/exports/timeline_export_v1.json", encoding="utf-8"))
CANON = json.load(io.open(f"{REP}/historical_driver_canonicalization_v0_1.json", encoding="utf-8"))
LEDGER = json.load(io.open(f"{REP}/historical_driver_evidence_ledger_v0_1.json",
                           encoding="utf-8"))["entries"]
CEV = json.load(io.open(f"{REP}/structural_analogy_candidate_events_v0_1.json",
                        encoding="utf-8"))["events"]
MMAP = json.load(io.open(f"{REP}/structural_analogy_candidate_market_map_v0_1.json",
                         encoding="utf-8"))["mapping"]
SNAPSHOT = cur.get("snapshot_date")
EV = {e["event_id"]: e for e in (exp.get("events") or [])}
ALL_OBJ = exp["campaigns"] + exp["research_candidates"]


def oid(o):
    return o.get("campaign_id") or o.get("research_candidate_id")


def macro_theme(o):
    t = next((t for t in (o.get("themes") or [])
              if t.get("role") == "related" and t.get("theme_type") in ("industry", "sector")), None)
    return t["name"] if t else None


def sub_themes(o):
    return sorted(t["name"] for t in (o.get("themes") or []) if t.get("role") == "main")


def events_of(o):
    out = [EV[i] for i in (o.get("event_ids") or []) if i in EV]
    if not out:
        key = oid(o)
        out = [e for e in EV.values() if e.get("campaign_id") == key]
    return sorted(out, key=lambda e: e["date"])


def lcs(a, b):
    """最长公共子序列长度（deterministic）。"""
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            dp[i][j] = dp[i - 1][j - 1] + 1 if a[i - 1] == b[j - 1] else max(dp[i - 1][j], dp[i][j - 1])
    return dp[len(a)][len(b)]


# ---------------------------------------------------------------- 历史 profile
HIST_DRV = collections.defaultdict(lambda: collections.defaultdict(set))
for e in LEDGER:
    if e["bucket"] in ("start", "accelerator") and e["mapping_status"] in ("DIRECT", "DERIVED") \
            and e["canonical_driver"]:
        HIST_DRV[e["cycle_id"]][e["canonical_driver"]].add(e["mapping_status"])

HIST = []
for o in ALL_OBJ:
    c = oid(o)
    sm = {l["stage"]: l.get("start") for l in (o.get("lifecycle") or []) if l.get("start")}
    stages = sorted(sm, key=lambda s: STAGE_ORDER.index(s) if s in STAGE_ORDER else 99)
    last = max(sm.items(), key=lambda kv: kv[1])[0] if sm else None
    evs = events_of(o)
    HIST.append({
        "cycle_id": c, "campaign_id": c if o.get("campaign_id") else None,
        "kind": "campaign" if o.get("campaign_id") else "research_candidate",
        "macro_theme": macro_theme(o), "sub_themes": sub_themes(o),
        "lifecycle_stages": stages, "stage_starts": sm,
        "terminal_phase": ({"EARLY_SIGNAL": "EARLY_SIGNAL", "THEME_FORMING": "THEME_FORMING",
                            "BROAD_CONFIRMATION": "BROAD_CONFIRMATION", "MAIN_RISE": "EXPANSION",
                            "PEAK": "PEAK", "SECONDARY": "DECLINE", "FIRST_DECLINE": "DECLINE",
                            "RETRACEMENT": "DECLINE", "DECLINING": "DECLINE",
                            "MAIN_END": "END"}.get(last, "UNKNOWN")) if last else "UNKNOWN",
        "canonical_drivers": sorted(HIST_DRV.get(c, {})),
        "driver_provenance": {k: sorted(v) for k, v in sorted(HIST_DRV.get(c, {}).items())},
        "driver_direct_count": sum(1 for v in HIST_DRV.get(c, {}).values() if "DIRECT" in v),
        "evidence_sequence": [e.get("event_type") for e in evs],
        "evidence_dates": [e.get("date") for e in evs],
        "event_profile": [{"event_id": e["event_id"], "date": e["date"],
                           "event_type": e.get("event_type")} for e in evs],
        "n_events": len(evs),
    })
HIST_BY_ID = {h["cycle_id"]: h for h in HIST}


def comparison_point(h, phase):
    """§九 historical_comparison_point —— Research-layer 派生观测点，不是新生命周期阶段。"""
    target = PHASE_TO_STAGE.get(phase)
    if not target or not h["lifecycle_stages"]:
        return {"stage": None, "status": "COMPARISON_POINT_UNKNOWN",
                "basis": "历史无 lifecycle 或 candidate phase 不可映射", "anchor_date": None}
    if target in h["stage_starts"]:
        return {"stage": target, "status": "MATCH",
                "basis": f"历史 lifecycle 明确包含该阶段（锚点 {h['stage_starts'][target]}）",
                "anchor_date": h["stage_starts"][target]}
    for nb in STAGE_NEIGHBOURS.get(target, []):
        if nb in h["stage_starts"]:
            return {"stage": nb, "status": "PARTIAL",
                    "basis": f"历史不含 {target}，使用相邻阶段 {nb}",
                    "anchor_date": h["stage_starts"][nb]}
    return {"stage": h["lifecycle_stages"][0], "status": "MISMATCH",
            "basis": "历史不含该阶段及其相邻阶段；回落到最早阶段仅作记录",
            "anchor_date": h["stage_starts"].get(h["lifecycle_stages"][0])}


# ---------------------------------------------------------------- candidate profile
CANDS = []
for c in cur["candidates"]:
    cid = c["candidate_id"]
    ev = c.get("evidence") or []
    dates = sorted([e.get("event_date") or e.get("source_date") for e in ev
                    if (e.get("event_date") or e.get("source_date"))])
    pw = c.get("phase_window") or {}
    start, end = pw.get("start"), pw.get("end")
    elapsed = None
    if start and SNAPSHOT:
        elapsed = (date(*[int(x) for x in SNAPSHOT.split("-")]) -
                   date(*[int(x) for x in start.split("-")])).days
    cev = sorted([e for e in CEV if e["candidate_id"] == cid], key=lambda e: (e["date"], e["event_id"]))
    seq = [e["event_type"] for e in cev]
    seq_partial = len(cev) < len(ev)
    proxy = MMAP.get(cid, {"status": "NOT_AVAILABLE", "series": []})
    CANDS.append({
        "candidate_id": cid, "macro_theme": c.get("macro_theme"),
        "industry": c.get("macro_theme"),
        "current_phase": c.get("attention_state"),
        "phase_stage": PHASE_TO_STAGE.get(c.get("attention_state")),
        "driver_profile": {
            "canonical_drivers": sorted(c.get("narrative_types") or []),
            "axis_note": "机制轴（narrative_types）；非 drivers[].category 类别轴",
            "category_axis_supplementary": sorted(d["category"] for d in (c.get("drivers") or [])),
            "evidence_references": [e["evidence_id"] for e in ev],
        },
        "evidence_sequence": seq,
        "evidence_sequence_status": "SEQUENCE_PARTIAL" if seq_partial else "SEQUENCE_FULL",
        "event_profile": [{"event_id": e["event_id"], "date": e["date"],
                           "event_type": e["event_type"], "date_basis": e.get("date_basis")}
                          for e in cev],
        "n_evidence": len(ev), "n_derived_events": len(cev),
        "phase_window": {"start": start, "end": end,
                         "end_semantics": "declared" if end else "unknown"},
        "phase_elapsed_days_at_snapshot": elapsed,
        "market_status": f"SUPPLEMENTARY_ONLY（{proxy['status']}）",
        "temporal_status": "SUPPLEMENTARY_ONLY（candidate-side one-way）",
        "structural_gaps": sorted(
            (["candidate_side_2026_market_state_not_available"]
             if proxy["status"] != "MATCH" else []) +
            (["phase_window_end_unknown"] if not end else []) +
            (["evidence_sequence_partial"] if seq_partial else []) +
            (["no_event_entity"] if not cev else [])),
    })
CAND_BY_ID = {c["candidate_id"]: c for c in CANDS}

# ---------------------------------------------------------------- 四维比较
def dim_driver(cs, hs):
    if not hs:
        return "NOT_AVAILABLE", {"overlap": []}
    if not cs:
        return "NOT_AVAILABLE", {"overlap": []}
    ov = sorted(set(cs) & set(hs))
    if set(cs) == set(hs):
        return "MATCH", {"overlap": ov}
    if ov:
        return "PARTIAL", {"overlap": ov}
    return "MISMATCH", {"overlap": []}


def dim_evseq(cs, hs):
    if len(cs) < 2 or len(hs) < 2:
        return "NOT_AVAILABLE", {"subtype": "NOT_AVAILABLE", "lcs": 0}
    n = lcs(cs, hs)
    ov = len(set(cs) & set(hs))
    if n >= 2 and cs[0] == hs[0]:
        return "MATCH", {"subtype": "SEQUENCE_MATCH", "lcs": n}
    if n >= 2:
        return "PARTIAL", {"subtype": "SEQUENCE_PARTIAL", "lcs": n}
    if n == 1 and ov >= 2:
        return "PARTIAL", {"subtype": "SET_ONLY", "lcs": n}
    return "MISMATCH", {"subtype": "SEQUENCE_MISMATCH", "lcs": n}


def dim_event(cev_types, hs):
    if not cev_types or not hs:
        return "NOT_AVAILABLE", {"overlap": []}
    ov = sorted(set(cev_types) & set(hs))
    if set(cev_types) == set(hs):
        return "MATCH", {"overlap": ov}
    if len(ov) >= 2:
        return "PARTIAL", {"overlap": ov}
    if len(ov) == 1:
        return "PARTIAL", {"overlap": ov}
    return "MISMATCH", {"overlap": []}


matrix = []
for cp in CANDS:
    cid = cp["candidate_id"]
    cs_drv = cp["driver_profile"]["canonical_drivers"]
    cs_seq = cp["evidence_sequence"]
    cs_evt = sorted({e["event_type"] for e in cp["event_profile"]})
    for h in HIST:
        cpt = comparison_point(h, cp["current_phase"])
        d_lc = cpt["status"]
        d_dr, dr_meta = dim_driver(cs_drv, h["canonical_drivers"])
        d_sq, sq_meta = dim_evseq(cs_seq, h["evidence_sequence"])
        d_ev, ev_meta = dim_event(cs_evt, h["evidence_sequence"])

        dims = {"lifecycle": d_lc, "driver": d_dr, "evidence_sequence": d_sq, "event_structure": d_ev}
        n_support = sum(1 for v in dims.values() if v in GOOD)
        n_av = sum(1 for v in dims.values() if v == "NOT_AVAILABLE")
        key_mismatch = any(dims[k] == "MISMATCH" for k in ("lifecycle", "driver"))
        has_direct = h["driver_direct_count"] > 0
        same_theme = h["macro_theme"] == cp["macro_theme"]
        theme_link = same_theme or bool(set(cp["driver_profile"]["category_axis_supplementary"]) &
                                        set(h["sub_themes"]))

        # ---- §十一 / §十三 成立判据（deterministic，顺序敏感）----
        #   ★ 关键收紧（§十二）：**driver == MISMATCH 不得成为 STRUCTURAL_PARTIAL** ——
        #     机制不对应时，即使 sequence/event 有重叠，也退化为 THEME_ONLY / NO_VALID。
        strict = (d_lc == "MATCH" and d_dr == "MATCH" and d_sq in GOOD and d_ev in GOOD
                  and sq_meta["subtype"] in ("SEQUENCE_MATCH", "SEQUENCE_PARTIAL")
                  and has_direct and not key_mismatch)
        supported = (d_lc == "MATCH" and (d_dr == "MATCH" or (d_dr == "PARTIAL" and len(dr_meta["overlap"]) >= 2))
                     and d_sq in GOOD and d_ev in GOOD
                     and sq_meta["subtype"] in ("SEQUENCE_MATCH", "SEQUENCE_PARTIAL")
                     and has_direct and not key_mismatch)

        if n_av >= 2 or d_dr == "NOT_AVAILABLE":
            level = "INSUFFICIENT_EVIDENCE"
        elif strict or supported:
            level = "STRUCTURAL_SUPPORTED"
        elif d_dr in GOOD and d_sq in GOOD and n_support >= 2:
            level = "STRUCTURAL_PARTIAL"
        elif same_theme or theme_link:
            level = "THEME_ONLY"
        elif d_dr in GOOD:
            level = "STRUCTURAL_PARTIAL"
        else:
            level = "NO_VALID_CORRESPONDENCE"

        matrix.append({
            "candidate_id": cid, "historical_cycle": h["cycle_id"],
            "historical_kind": h["kind"], "historical_macro_theme": h["macro_theme"],
            "same_macro_theme": same_theme,
            "historical_comparison_point": cpt,
            "lifecycle": d_lc, "driver": d_dr, "evidence_sequence": d_sq,
            "event_structure": d_ev, "status": level,
            "strict_supported": strict,
            "driver_overlap": dr_meta["overlap"],
            "sequence_subtype": sq_meta["subtype"],
            "sequence_lcs": sq_meta["lcs"],
            "event_overlap": ev_meta["overlap"],
            "n_supporting_dimensions": n_support,
            "n_not_available_dimensions": n_av,
            "has_direct_driver_evidence": has_direct,
            "supplementary": {"market_structure": "SUPPLEMENTARY_ONLY", "temporal_structure": "SUPPLEMENTARY_ONLY"},
        })

# ---------------------------------------------------------------- 汇总
by_level = collections.Counter(m["status"] for m in matrix)
strict_count = sum(1 for m in matrix if m["strict_supported"])
cross = [m for m in matrix if not m["same_macro_theme"]]
same = [m for m in matrix if m["same_macro_theme"]]

# ---- §十七 Name vs Structural ----
exp_rows = []
for cp in CANDS:
    cid = cp["candidate_id"]
    A = sorted(set(h["cycle_id"] for h in HIST if h["macro_theme"] == cp["macro_theme"])
               | set(r["campaign_id"] for r in (next(c for c in cur["candidates"]
                                                      if c["candidate_id"] == cid).get("reference_cases") or [])))
    B = sorted(m["historical_cycle"] for m in matrix if m["candidate_id"] == cid
               and m["status"] in ("STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL"))
    exp_rows.append({"candidate_id": cid, "macro_theme": cp["macro_theme"],
                     "name_theme_set": A, "structural_set": B,
                     "both": sorted(set(A) & set(B)),
                     "only_name": sorted(set(A) - set(B)),
                     "only_structural": sorted(set(B) - set(A)),
                     "neither_count": len([h for h in HIST
                                           if h["cycle_id"] not in set(A) | set(B)])})
uA = set().union(*[set(r["name_theme_set"]) for r in exp_rows]) if exp_rows else set()
uB = set().union(*[set(r["structural_set"]) for r in exp_rows]) if exp_rows else set()

# ---- §二十 Evidence Cards（仅 SUPPORTED / PARTIAL）----
cards = []
for m in matrix:
    if m["status"] not in ("STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL"):
        continue
    cp = CAND_BY_ID[m["candidate_id"]]
    h = HIST_BY_ID[m["historical_cycle"]]
    neg = []
    if m["driver"] == "MISMATCH":
        neg.append("driver mismatch")
    if m["lifecycle"] == "MISMATCH":
        neg.append("lifecycle mismatch")
    if m["evidence_sequence"] == "MISMATCH":
        neg.append("evidence sequence mismatch")
    if m["event_structure"] == "MISMATCH":
        neg.append("event structure mismatch")
    if m["sequence_subtype"] == "SET_ONLY":
        neg.append("sequence is SET_ONLY（无法证明顺序）")
    if not m["has_direct_driver_evidence"]:
        neg.append("历史侧无 DIRECT driver 证据")
    if m["n_not_available_dimensions"]:
        neg.append(f"{m['n_not_available_dimensions']} 个维度 NOT_AVAILABLE")
    if not m["same_macro_theme"]:
        neg.append("跨族：无同主题上下文支撑")
    cards.append({
        "candidate_id": m["candidate_id"], "historical_cycle": m["historical_cycle"],
        "status": m["status"], "strict_supported": m["strict_supported"],
        "lifecycle": {"status": m["lifecycle"], "comparison_point": m["historical_comparison_point"]},
        "driver": {"status": m["driver"], "overlap": m["driver_overlap"],
                   "candidate_drivers": cp["driver_profile"]["canonical_drivers"],
                   "historical_drivers": h["canonical_drivers"],
                   "historical_provenance": h["driver_provenance"]},
        "evidence_sequence": {"status": m["evidence_sequence"], "subtype": m["sequence_subtype"],
                              "lcs": m["sequence_lcs"],
                              "candidate_sequence": cp["evidence_sequence"],
                              "historical_sequence": h["evidence_sequence"]},
        "event_structure": {"status": m["event_structure"], "overlap": m["event_overlap"],
                            "candidate_event_types": sorted({e["event_type"] for e in cp["event_profile"]}),
                            "historical_event_types": sorted(set(h["evidence_sequence"]))},
        "why_considered": (f"Lifecycle={m['lifecycle']}；Driver={m['driver']}"
                           f"（交集 {m['driver_overlap']}）；"
                           f"EvidenceSequence={m['evidence_sequence']}（{m['sequence_subtype']}）；"
                           f"EventStructure={m['event_structure']} → "
                           f"{m['n_supporting_dimensions']}/4 维度有真实对应"),
        "why_not_strong_analogy": ("；".join(neg) if neg else
                                   "无显著负证据，但仍受样本量（85 组合）与历史驱动证据粒度限制"),
    })

res = {
    "artifact": "structural_analogy_research", "artifact_version": "0.1",
    "generated_by": "research/scripts/build_structural_analogy_research_v0_1.py",
    "position": ("Research-only Structural Analogy Engine —— **不进入** Product / src / DB / schema / "
                 "export / contracts。**不是**投资建议、预测、交易信号、相似度评分或排名。"),
    "not_a": ["product UI", "user recommendation", "investment advice", "prediction",
              "trading signal", "similarity score", "weighted score", "confidence score",
              "ranking", "best historical analogue", "winner"],
    "snapshot": {"current_candidates_snapshot": cur.get("snapshot_date"),
                 "export_version": exp.get("timeline_export_version"),
                 "export_source_commit": exp.get("source_commit")},
    "dimension_vocabulary": DIM_STATUS,
    "correspondence_levels": LEVELS,
    "excluded_dimensions": {
        "market_structure": {"status": "SUPPLEMENTARY_ONLY", "reason": "PARTIALLY_RESOLVED（候选侧 2026 行情不可得，单向）"},
        "temporal_structure": {"status": "SUPPLEMENTARY_ONLY", "reason": "candidate-side one-way"},
        "rule": "**不参与 v0.1 成立判据**（§六）",
    },
    "correspondence_rules": {
        "STRUCTURAL_SUPPORTED": [
            "D1 Lifecycle = MATCH",
            "D2 Driver = MATCH，或 PARTIAL 且机制交集 ≥2",
            "D3 Evidence Sequence ∈ {MATCH, PARTIAL} 且 subtype ∈ {SEQUENCE_MATCH, SEQUENCE_PARTIAL}",
            "D4 Event Structure ∈ {MATCH, PARTIAL}",
            "历史侧存在 ≥1 个 DIRECT driver 证据",
            "D1/D2 无 MISMATCH",
        ],
        "STRICT_STRUCTURAL_SUPPORTED": "同 STRUCTURAL_SUPPORTED，但 D2 Driver 必须 = MATCH（§二十六 单独计数）",
        "STRUCTURAL_PARTIAL": "≥2 个维度存在真实对应，但未满足上述条件",
        "THEME_ONLY": "只有 macro theme / sector / keyword 等表层联系（含同族但结构不成立）",
        "INSUFFICIENT_EVIDENCE": "≥2 个维度 NOT_AVAILABLE → 理论上可比较但证据不足",
        "NO_VALID_CORRESPONDENCE": "四维中 ≤1 维度有对应，且无主题联系",
        "note": ("规则为 **v0.1 工作定义**（§十三 允许在数据不足时显式调整）；"
                 "**deterministic**、顺序敏感、无连续分数。"),
        "driver_rules": {
            "MATCH": "机制语义一致（集合相等）",
            "PARTIAL": "部分机制一致（交集非空且不等）",
            "MISMATCH": "机制核心方向明显不同（交集为空）",
            "NOT_AVAILABLE": "任一侧无 canonical driver",
        },
        "sequence_rules": {
            "SEQUENCE_MATCH": "LCS ≥2 且首项相同",
            "SEQUENCE_PARTIAL": "LCS ≥2 但首项不同",
            "SET_ONLY": "LCS =1 且类型交集 ≥2（**不得**当作 SEQUENCE_MATCH）",
            "SEQUENCE_MISMATCH": "LCS ≤1 且类型交集 <2",
            "NOT_AVAILABLE": "任一侧 <2 条带日期事件",
        },
        "forbidden": ["从 event_type 推 driver", "从价格/涨跌推 driver 或 lifecycle",
                      "把 market/temporal 计入成立判据", "把 SET_ONLY 当作 SEQUENCE_MATCH",
                      "因同族而自动升级等级"],
    },
    "candidate_profiles": CANDS, "historical_profiles": HIST, "matrix": matrix,
    "summary": {
        "current_candidates": len(CANDS),
        "historical_cycles_examined": len(HIST),
        "pairs": len(matrix),
        "by_status": {k: by_level[k] for k in LEVELS},
        "strict_structural_supported": strict_count,
        "by_status_cross_family": {k: sum(1 for m in cross if m["status"] == k) for k in LEVELS},
        "by_status_same_family": {k: sum(1 for m in same if m["status"] == k) for k in LEVELS},
    },
    "name_vs_structural": {
        "name_theme_set_union": sorted(uA), "structural_set_union": sorted(uB),
        "both": sorted(uA & uB), "only_name": sorted(uA - uB), "only_structural": sorted(uB - uA),
        "per_candidate": exp_rows,
        "note": "**不声称 Structural Matching 更准确** —— 只验证研究对象是否与 Theme Lookup 不同。",
    },
    "evidence_cards": cards,
}

body = json.dumps(res, ensure_ascii=False, indent=1) + "\n"
if CHECK:
    if not os.path.exists(OUT_JSON) or io.open(OUT_JSON, encoding="utf-8").read() != body:
        raise SystemExit("FAIL —— 产物与重算结果不一致")
    print("PASS —— 产物与重算结果逐字节一致（deterministic）。")
else:
    with io.open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    print("written", OUT_JSON)

with io.open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["candidate_id", "historical_cycle", "historical_macro_theme", "same_macro_theme",
                "comparison_point_stage", "comparison_point_status", "lifecycle", "driver",
                "driver_overlap", "evidence_sequence", "sequence_subtype", "event_structure",
                "status", "strict_supported", "n_supporting_dimensions",
                "n_not_available_dimensions"])
    for m in matrix:
        w.writerow([m["candidate_id"], m["historical_cycle"], m["historical_macro_theme"],
                    m["same_macro_theme"], m["historical_comparison_point"]["stage"],
                    m["historical_comparison_point"]["status"], m["lifecycle"], m["driver"],
                    "|".join(m["driver_overlap"]), m["evidence_sequence"], m["sequence_subtype"],
                    m["event_structure"], m["status"], m["strict_supported"],
                    m["n_supporting_dimensions"], m["n_not_available_dimensions"]])
print("written", OUT_CSV)
print()
print("candidates:", len(CANDS), "| historical cycles:", len(HIST), "| pairs:", len(matrix))
print("by_status:", {k: by_level[k] for k in LEVELS})
print("STRICT_STRUCTURAL_SUPPORTED:", strict_count)
print("cross-family:", {k: sum(1 for m in cross if m["status"] == k) for k in LEVELS})
print("name/structural: A=%d B=%d both=%d only_name=%d only_struct=%d"
      % (len(uA), len(uB), len(uA & uB), len(uA - uB), len(uB - uA)))
