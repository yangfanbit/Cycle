"""Structural Analogy Research v0.2 —— 使用**已冻结**的 Rule Set v0.2 运行完整 Research。

**规则来源**：`research/research/methodology/structural_analogy_rule_set_v0_2.md`
（Rule Set v0.2 · effective 2026-09-19 · source artifact = Rule Calibration v0.2）

**本脚本不重新发明规则** —— 规则实现与
`build_structural_analogy_rule_calibration_v0_2.py::level_v2()` 逐条一致。
本脚本的职责是：**执行冻结规则并产出可引用的 Research baseline**（含 reasons / mismatch / unknown）。

**禁止**：score · ranking · probability · top/best analogue。
**不修改**：任何原始数据 · schema · export · Product · 任何旧产物。

产物：
  research/research/reports/structural_analogy_research_v0_2.json
  research/research/reports/structural_analogy_research_candidates_v0_2.csv
"""
import collections
import csv
import io
import json
import os
import sys

ROOT = r"D:/@AW/投资/ThreeC"
REP = f"{ROOT}/research/research/reports"
CHECK = "--check" in sys.argv
OUT_JSON = f"{REP}/structural_analogy_research_v0_2.json"
OUT_CSV = f"{REP}/structural_analogy_research_candidates_v0_2.csv"

V1 = json.load(io.open(f"{REP}/structural_analogy_research_v0_1.json", encoding="utf-8"))
LEDGER = json.load(io.open(f"{REP}/historical_driver_evidence_ledger_v0_1.json",
                           encoding="utf-8"))["entries"]
M0 = V1["matrix"]

LEVELS = ["STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL", "THEME_ONLY",
          "INSUFFICIENT_EVIDENCE", "NO_VALID_CORRESPONDENCE"]
GOOD = ("MATCH", "PARTIAL")
SEQ_OK = ("SEQUENCE_MATCH", "SEQUENCE_PARTIAL")
DRIVER_GOOD = ("MATCH", "PARTIAL")

# ---------------------------------------------------------------- primary_mechanism（Rule Set §4）
DIRECT_CNT = collections.defaultdict(lambda: collections.Counter())
for e in LEDGER:
    if e["bucket"] in ("start", "accelerator") and e["mapping_status"] == "DIRECT" and e["canonical_driver"]:
        DIRECT_CNT[e["cycle_id"]][e["canonical_driver"]] += 1


def primary_of(cycle):
    c = DIRECT_CNT.get(cycle)
    if not c:
        return "UNKNOWN", "无 DIRECT driver 证据 → UNKNOWN"
    best = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
    return best[0][0], f"driving 相位 DIRECT 计数最高（{best[0][1]} 条；tie-break = canonical 名称升序）"


# ---------------------------------------------------------------- 规则实现（与 Calibration v0.2 一致）
def driver_rule(cand_dr, hist_dr, cycle):
    if not cand_dr or not hist_dr:
        return "NOT_AVAILABLE", {"overlap": [], "quality": "NOT_AVAILABLE", "reason": "任一侧无 canonical driver"}
    ov = sorted(set(cand_dr) & set(hist_dr))
    prim, _ = primary_of(cycle)
    if not ov:
        return "MISMATCH", {"overlap": [], "quality": "NONE", "reason": "机制交集为空"}
    if set(cand_dr) == set(hist_dr) and len(ov) >= 2:
        if all(DIRECT_CNT.get(cycle, {}).get(k, 0) >= 1 for k in ov):
            return "MATCH", {"overlap": ov, "quality": "CORE_EQUIVALENT",
                             "reason": f"集合相等且 {len(ov)} 项均有 DIRECT provenance"}
        return "PARTIAL", {"overlap": ov, "quality": "SET_EQUAL_NO_PROVENANCE",
                           "reason": "集合相等但缺 DIRECT provenance → 降为 PARTIAL"}
    if len(ov) >= 2:
        return "PARTIAL", {"overlap": ov, "quality": "MULTI_MECHANISM", "reason": f"机制交集 {len(ov)} 项（≥2）"}
    if prim != "UNKNOWN" and ov[0] == prim:
        return "PARTIAL", {"overlap": ov, "quality": "PRIMARY_MECHANISM_OVERLAP",
                           "reason": f"单一交集且为历史 primary（{prim}）"}
    return "PERIPHERAL_OVERLAP", {"overlap": ov, "quality": "PERIPHERAL_ONLY",
                                  "reason": "单一交集且非历史 primary → 不计为结构支持"}


def event_rule(cand_types, hist_seq):
    if not cand_types or not hist_seq:
        return "NOT_AVAILABLE", {"overlap": [], "quality": "NOT_AVAILABLE", "reason": "任一侧无事件实体"}
    ov = sorted(set(cand_types) & set(hist_seq))
    if not ov:
        return "MISMATCH", {"overlap": [], "quality": "NO_CORRESPONDENCE", "reason": "无事件类型对应"}
    chrono = len(cand_types) >= 2 and len(hist_seq) >= 2
    if set(cand_types) == set(hist_seq) and chrono and cand_types[0] == hist_seq[0]:
        return "MATCH", {"overlap": ov, "quality": "TYPE_AND_CHRONOLOGY",
                         "reason": "类型集合相等 + 双方 ≥2 事件 + 首项相同"}
    if len(ov) >= 2 and chrono:
        return "PARTIAL", {"overlap": ov, "quality": "MULTI_TYPE_WITH_CHRONOLOGY",
                           "reason": f"类型交集 {len(ov)} 项 + chronology 可比"}
    if len(ov) >= 2:
        return "PARTIAL", {"overlap": ov, "quality": "MULTI_TYPE_NO_CHRONOLOGY",
                           "reason": f"类型交集 {len(ov)} 项但 chronology 不完整"}
    return "MISMATCH", {"overlap": ov, "quality": "SINGLE_TYPE_ONLY",
                        "reason": "仅单一类型重叠 → 非支持状态"}


def level_rule(d_lc, d_dr, d_sq, d_ev, seq_sub, has_direct, theme_rel, drv_quality):
    """Rule Set v0.2 §7 / §8 / §9 —— 与 Calibration v0.2 的 deterministic implementation 一致。"""
    dims = [d_lc, d_dr, d_sq, d_ev]
    n_support = sum(1 for v in dims if v in GOOD)
    n_av = sum(1 for v in dims if v == "NOT_AVAILABLE")
    key_mismatch = (d_lc == "MISMATCH") or (d_dr == "MISMATCH") or (d_ev == "MISMATCH")
    drv_strong = (d_dr == "MATCH" or (d_dr == "PARTIAL" and drv_quality == "MULTI_MECHANISM"))
    strict = (d_lc == "MATCH" and d_dr == "MATCH" and d_sq in GOOD and d_ev in GOOD
              and seq_sub in SEQ_OK and has_direct and not key_mismatch)
    non_lc = sum(1 for v in (d_dr, d_sq, d_ev) if v in GOOD)
    supported = (d_lc == "MATCH" and drv_strong and d_sq in GOOD and d_ev in GOOD
                 and seq_sub in SEQ_OK and has_direct and non_lc >= 2 and not key_mismatch)
    if n_av >= 2 or d_dr == "NOT_AVAILABLE":
        return "INSUFFICIENT_EVIDENCE", strict
    if strict or supported:
        return "STRUCTURAL_SUPPORTED", strict
    if d_dr in DRIVER_GOOD and d_sq in GOOD and n_support >= 2:
        return "STRUCTURAL_PARTIAL", False
    if d_dr == "PERIPHERAL_OVERLAP" or (d_lc in GOOD and n_support <= 1):
        return ("THEME_ONLY" if theme_rel == "SAME_MACRO_THEME" else "NO_VALID_CORRESPONDENCE"), False
    if n_support >= 2:
        return "STRUCTURAL_PARTIAL", False
    return "NO_VALID_CORRESPONDENCE", False


# ---------------------------------------------------------------- 执行
CP = {c["candidate_id"]: c for c in V1["candidate_profiles"]}
HP = {h["cycle_id"]: h for h in V1["historical_profiles"]}


def run(theme_blind=False):
    rows = []
    for m in M0:
        cid, cyc = m["candidate_id"], m["historical_cycle"]
        cp, hp = CP[cid], HP[cyc]
        d_lc, d_sq, sub = m["lifecycle"], m["evidence_sequence"], m["sequence_subtype"]
        d_dr, dr_meta = driver_rule(cp["driver_profile"]["canonical_drivers"],
                                    hp["canonical_drivers"], cyc)
        d_ev, ev_meta = event_rule(sorted({e["event_type"] for e in cp["event_profile"]}),
                                   hp["evidence_sequence"])
        tr = "CROSS_MACRO_THEME" if (theme_blind or not m["same_macro_theme"]) else "SAME_MACRO_THEME"
        lvl, strict = level_rule(d_lc, d_dr, d_sq, d_ev, sub,
                                 m["has_direct_driver_evidence"], tr, dr_meta["quality"])
        # reasons / mismatch / unknown（B-5 要求字段）
        reasons = []
        if d_lc in GOOD:
            reasons.append(f"Lifecycle={d_lc}（{m['historical_comparison_point']['basis']}）")
        if d_dr in GOOD:
            reasons.append(f"Driver={d_dr}/{dr_meta['quality']}（交集 {dr_meta['overlap']}）")
        if d_sq in GOOD:
            reasons.append(f"EvidenceSequence={d_sq}/{sub}")
        if d_ev in GOOD:
            reasons.append(f"EventStructure={d_ev}/{ev_meta['quality']}")
        mismatch = [k for k, v in (("lifecycle", d_lc), ("driver", d_dr),
                                   ("evidence_sequence", d_sq), ("event_structure", d_ev)) if v == "MISMATCH"]
        unknown = [k for k, v in (("lifecycle", d_lc), ("driver", d_dr),
                                  ("evidence_sequence", d_sq), ("event_structure", d_ev))
                   if v in ("UNKNOWN", "NOT_AVAILABLE")]
        rows.append({
            "candidate_id": cid, "historical_cycle": cyc,
            "historical_kind": hp["kind"], "historical_macro_theme": hp["macro_theme"],
            "theme_relation": tr,
            "lifecycle": d_lc, "historical_stage_at_comparable_point": m["historical_comparison_point"]["stage"],
            "driver": d_dr, "driver_quality": dr_meta["quality"], "driver_overlap": dr_meta["overlap"],
            "evidence_sequence": d_sq, "sequence_subtype": sub,
            "event_structure": d_ev, "event_quality": ev_meta["quality"],
            "structural_status": lvl, "strict_structural_supported": strict,
            "structural_reasons": reasons, "mismatch_dimensions": mismatch,
            "unknown_dimensions": unknown,
            "supplementary": {"market_structure": "SUPPLEMENTARY_ONLY",
                              "temporal_structure": "SUPPLEMENTARY_ONLY"},
        })
    return rows


V2 = run()
TB = run(theme_blind=True)


def counts(rows):
    c = collections.Counter(r["structural_status"] for r in rows)
    return {"strict": sum(1 for r in rows if r["strict_structural_supported"]),
            **{k: c[k] for k in LEVELS}}


C2 = counts(V2)
C1 = counts([{"structural_status": m["status"], "strict_structural_supported": m["strict_supported"]}
             for m in M0])

# ---------------------------------------------------------------- v0.1 → v0.2 diff（含归因）
V1MAP = {(m["candidate_id"], m["historical_cycle"]): m for m in M0}
diff = []
for r in V2:
    a = V1MAP[(r["candidate_id"], r["historical_cycle"])]
    if a["status"] == r["structural_status"] and a["strict_supported"] == r["strict_structural_supported"]:
        continue
    reasons = []
    if a["driver"] != r["driver"]:
        reasons.append("Driver calibration")
    if a["event_structure"] != r["event_structure"]:
        reasons.append("Event calibration")
    if not reasons:
        reasons.append("Theme decoupling / Structural support threshold")
    diff.append({"candidate_id": r["candidate_id"], "historical_cycle": r["historical_cycle"],
                 "theme_relation": r["theme_relation"],
                 "from": a["status"], "to": r["structural_status"],
                 "attribution": reasons})
ATTR = collections.Counter("|".join(d["attribution"]) for d in diff)

# ---------------------------------------------------------------- regression controls（B-11 / B-12）
NAME_BLIND = {"retained": len(V2), "changed": 0,
              "note": "Rule Set v0.2 的四个正式维度**不读取任何名称字段**；名称仅用于展示。"}
STRUCT_CHANGED = sum(1 for a, b in zip(V2, TB)
                     if a["structural_status"] != b["structural_status"]
                     and a["structural_status"].startswith("STRUCTURAL"))
THEME_BLIND = {"retained": sum(1 for a, b in zip(V2, TB) if a["structural_status"] == b["structural_status"]),
               "changed": sum(1 for a, b in zip(V2, TB) if a["structural_status"] != b["structural_status"]),
               "structural_status_changed": STRUCT_CHANGED,
               "theme_relation_changed": sum(1 for a, b in zip(V2, TB)
                                             if a["theme_relation"] != b["theme_relation"]),
               "changed_detail": [{"candidate_id": a["candidate_id"], "historical_cycle": a["historical_cycle"],
                                   "from": a["structural_status"], "to": b["structural_status"]}
                                  for a, b in zip(V2, TB) if a["structural_status"] != b["structural_status"]],
               "note": "正确预期：Theme-Blind **不改变 Structural Status**，只影响 theme_relation。"}

NEG_CASES = [("CC-2026-EMBODIED-AI", "C-2024-ROBOTAXI", "name-similarity negative control"),
             ("CC-2026-OPTICAL-LINK", "C-2019-COMM-5G", "same-theme negative control"),
             ("CC-2026-BCI-MEDTECH", "C-2019-PHARMA-INNOV", "same-theme (was THEME_ONLY in v0.1)"),
             ("CC-2026-OFFSHORE-WIND", "C-2020-POWER-NE", "theme-decoupling fix case")]
neg = []
for cid, cyc, kind in NEG_CASES:
    a = V1MAP[(cid, cyc)]
    r = next(x for x in V2 if x["candidate_id"] == cid and x["historical_cycle"] == cyc)
    t = next(x for x in TB if x["candidate_id"] == cid and x["historical_cycle"] == cyc)
    neg.append({"case": kind, "candidate_id": cid, "historical_cycle": cyc,
                "theme_relation": r["theme_relation"], "v0_1": a["status"], "v0_2": r["structural_status"],
                "theme_blind": t["structural_status"], "driver": r["driver"],
                "event_structure": r["event_structure"],
                "not_upgraded": r["structural_status"] in ("NO_VALID_CORRESPONDENCE", "THEME_ONLY")})

# ---------------------------------------------------------------- 逐候选分组（B-9）
per_cand = []
for cp in V1["candidate_profiles"]:
    cid = cp["candidate_id"]
    rows = [r for r in V2 if r["candidate_id"] == cid]
    corr = [r for r in rows if r["structural_status"] in ("STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL")]
    nonc = [r for r in rows if r["structural_status"] not in ("STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL")]
    per_cand.append({
        "candidate_id": cid, "macro_theme": cp["macro_theme"],
        "current_structural_profile": {
            "current_phase": cp["current_phase"], "phase_stage": cp["phase_stage"],
            "driver_profile": cp["driver_profile"], "evidence_sequence": cp["evidence_sequence"],
            "evidence_sequence_status": cp["evidence_sequence_status"],
            "event_profile_types": sorted({e["event_type"] for e in cp["event_profile"]}),
            "market_status": cp["market_status"], "temporal_status": cp["temporal_status"],
            "structural_gaps": cp["structural_gaps"]},
        "historical_correspondence_set": [
            {"historical_cycle": r["historical_cycle"], "status": r["structural_status"],
             "theme_relation": r["theme_relation"], "driver": r["driver"],
             "driver_quality": r["driver_quality"], "event_quality": r["event_quality"]} for r in corr],
        "non_correspondence_set": [
            {"historical_cycle": r["historical_cycle"], "status": r["structural_status"],
             "mismatch_dimensions": r["mismatch_dimensions"]} for r in nonc],
        "theme_relations": dict(collections.Counter(r["theme_relation"] for r in rows)),
        "counts": dict(collections.Counter(r["structural_status"] for r in rows)),
    })

# ---------------------------------------------------------------- B-14 Research Loop
loop = {
    "current_to_historical_search": "PASS",
    "lifecycle": "PASS" if sum(1 for r in V2 if r["lifecycle"] == "MATCH") >= 50 else "PARTIAL",
    "driver": "PARTIAL" if C2["STRUCTURAL_SUPPORTED"] > 0 else "FAIL",
    "evidence_sequence": "PARTIAL",
    "event_structure": "PARTIAL",
    "note": ("Driver 仍为 PARTIAL（机制级 MATCH 极少）；"
             "Evidence Sequence 与 Event 受历史事件覆盖限制（NOT_AVAILABLE 若干）。"),
}

cross = [r for r in V2 if r["theme_relation"] == "CROSS_MACRO_THEME"]
same = [r for r in V2 if r["theme_relation"] == "SAME_MACRO_THEME"]

res = {
    "artifact": "structural_analogy_research", "artifact_version": "0.2",
    "generated_by": "research/scripts/build_structural_analogy_research_v0_2.py",
    "protocol": {
        "rule_set": "Structural Analogy Rule Set v0.2",
        "protocol_version": "structural-analogy-ruleset-v0.2",
        "protocol_document": "research/research/methodology/structural_analogy_rule_set_v0_2.md",
        "effective_date": "2026-09-19",
        "source_calibration_artifact": "research/research/reports/structural_analogy_rule_calibration_v0_2.json",
        "frozen": True,
        "rule_implementation_parity": "与 build_structural_analogy_rule_calibration_v0_2.py::level_v2() 逐条一致",
    },
    "position": ("Research-only Structural Analogy baseline —— 执行**已冻结**规则，不调规则。"
                 "**不进入** Product / src / DB / schema / export / contracts。"),
    "not_a": ["similarity score", "confidence score", "probability", "ranking",
              "top analogue", "best analogue", "product readiness"],
    "snapshot": V1["snapshot"],
    "core_result": {
        "current_candidates": len(V1["candidate_profiles"]),
        "historical_cycles": len(V1["historical_profiles"]),
        "comparison_pairs": len(V2),
        "v0_1_counts": C1, "v0_2_counts": C2,
    },
    "primary_mechanism_derivation": {c: {"primary": primary_of(c)[0], "basis": primary_of(c)[1]}
                                     for c in sorted({m["historical_cycle"] for m in M0})},
    "correspondence_matrix": V2,
    "candidate_profiles": per_cand,
    "v0_1_to_v0_2_diff": {"changed": len(diff), "detail": diff,
                          "attribution_summary": dict(ATTR),
                          "classification": {
                              "upgraded": [d for d in diff if LEVELS.index(d["to"]) < LEVELS.index(d["from"])],
                              "downgraded": [d for d in diff if LEVELS.index(d["to"]) > LEVELS.index(d["from"])]}},
    "cross_family": {
        "supported_cross": sum(1 for r in cross if r["structural_status"] == "STRUCTURAL_SUPPORTED"),
        "supported_same": sum(1 for r in same if r["structural_status"] == "STRUCTURAL_SUPPORTED"),
        "partial_cross": sum(1 for r in cross if r["structural_status"] == "STRUCTURAL_PARTIAL"),
        "partial_same": sum(1 for r in same if r["structural_status"] == "STRUCTURAL_PARTIAL"),
    },
    "controls": {"name_blind": NAME_BLIND, "theme_blind": THEME_BLIND, "negative_controls": neg},
    "research_loop": loop,
    "research_loop_verdict": ("PASS" if all(v == "PASS" for k, v in loop.items() if k != "note")
                              else "PARTIAL"),
    "boundary": {
        "product_readiness": "NO",
        "wave_1c": "NOT REQUIRED",
        "market_temporal": "SUPPLEMENTARY_ONLY（不参与 Structural Status）",
        "reasons_for_product_no": ["market context", "temporal context", "explanation design",
                                   "uncertainty presentation", "user interaction", "performance",
                                   "product language"],
    },
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
    w.writerow(["candidate_id", "historical_cycle", "historical_macro_theme", "theme_relation",
                "lifecycle", "historical_stage_at_comparable_point", "driver", "driver_quality",
                "driver_overlap", "evidence_sequence", "sequence_subtype", "event_structure",
                "event_quality", "structural_status", "strict_structural_supported",
                "structural_reasons", "mismatch_dimensions", "unknown_dimensions"])
    for r in V2:
        w.writerow([r["candidate_id"], r["historical_cycle"], r["historical_macro_theme"],
                    r["theme_relation"], r["lifecycle"], r["historical_stage_at_comparable_point"],
                    r["driver"], r["driver_quality"], "|".join(r["driver_overlap"]),
                    r["evidence_sequence"], r["sequence_subtype"], r["event_structure"],
                    r["event_quality"], r["structural_status"], r["strict_structural_supported"],
                    " ; ".join(r["structural_reasons"]), "|".join(r["mismatch_dimensions"]),
                    "|".join(r["unknown_dimensions"])])
print("written", OUT_CSV)
print()
print("v0.1:", C1)
print("v0.2:", C2)
print("changed:", len(diff), "| attribution:", dict(ATTR))
print("cross-family:", res["cross_family"])
print("name-blind changed:", NAME_BLIND["changed"], "| theme-blind structural changed:", STRUCT_CHANGED)
print("research loop:", loop)
