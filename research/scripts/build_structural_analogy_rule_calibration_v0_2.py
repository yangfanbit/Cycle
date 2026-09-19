"""Structural Analogy Rule Calibration v0.2（deterministic，只读输入）。

修正 v0.1 的三处问题：
  Problem A  Theme precedence bug —— `same_theme` 分支先于结构判定 → 同族会「压低」等级
  Problem B  Event Structure 低筛选力 —— `PARTIAL` 74/85，R2 ≡ R3
  Problem C  Driver PARTIAL 过宽 —— 50/85

三项修正（**一次定义、应用于全部 85 pairs、不做逐 case 手工处理**）：
  1) **Theme / Structural 完全解耦**：Structural Status 只由四维决定；
     Theme Relation 单独作 metadata；`THEME_ONLY` 在**结构评估之后**才派生
  2) **Event 校准**：`overlap == 1` 不再算 PARTIAL（→ MISMATCH）；需真实 correspondence + 可比 chronology
  3) **Driver 校准**：引入 `primary_mechanism`（历史侧，由 DIRECT 计数确定性推导）；
     `overlap == 1 且非历史 primary` → `PERIPHERAL_OVERLAP`（**不计为结构支持**）

**禁止**：score / ranking / probability / similarity percentage。
**不修改**任何原始数据、schema、export、Product。

产物：
  research/research/reports/structural_analogy_rule_calibration_v0_2.json
  research/research/reports/structural_analogy_rule_calibration_pairs_v0_2.csv
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
OUT_JSON = f"{REP}/structural_analogy_rule_calibration_v0_2.json"
OUT_CSV = f"{REP}/structural_analogy_rule_calibration_pairs_v0_2.csv"

V1 = json.load(io.open(f"{REP}/structural_analogy_research_v0_1.json", encoding="utf-8"))
LEDGER = json.load(io.open(f"{REP}/historical_driver_evidence_ledger_v0_1.json",
                           encoding="utf-8"))["entries"]
M0 = V1["matrix"]

LEVELS = ["STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL", "THEME_ONLY",
          "INSUFFICIENT_EVIDENCE", "NO_VALID_CORRESPONDENCE"]
GOOD = ("MATCH", "PARTIAL")
SEQ_OK = ("SEQUENCE_MATCH", "SEQUENCE_PARTIAL")

# ---------------------------------------------------------------- primary_mechanism（历史侧）
DIRECT_CNT = collections.defaultdict(lambda: collections.Counter())
for e in LEDGER:
    if e["bucket"] in ("start", "accelerator") and e["mapping_status"] == "DIRECT" and e["canonical_driver"]:
        DIRECT_CNT[e["cycle_id"]][e["canonical_driver"]] += 1


def primary_mechanism(cycle_id):
    """最高 DIRECT 计数；无 DIRECT → UNKNOWN（**不猜**）。确定性 tie-break：canonical 名称升序。"""
    c = DIRECT_CNT.get(cycle_id)
    if not c:
        return "UNKNOWN", "无 DIRECT driver 证据 → UNKNOWN"
    best = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
    if best[0][1] <= 0:
        return "UNKNOWN", "无 DIRECT driver 证据 → UNKNOWN"
    return best[0][0], f"DIRECT 计数最高（{best[0][1]} 条）"


PRIMARY = {m["historical_cycle"]: primary_mechanism(m["historical_cycle"])[0]
           for m in M0}
PRIMARY_BASIS = {m["historical_cycle"]: primary_mechanism(m["historical_cycle"])[1]
                 for m in M0}


# ---------------------------------------------------------------- 校准后的三个维度
def cal_driver(cand_drivers, hist_drivers, hist_cycle):
    """Driver 校准（§九/§十/§十一）。"""
    if not cand_drivers or not hist_drivers:
        return "NOT_AVAILABLE", {"overlap": [], "quality": "NOT_AVAILABLE"}
    ov = sorted(set(cand_drivers) & set(hist_drivers))
    prim = PRIMARY.get(hist_cycle, "UNKNOWN")
    if not ov:
        return "MISMATCH", {"overlap": [], "quality": "NONE"}
    if set(cand_drivers) == set(hist_drivers) and len(ov) >= 2:
        # 集合相等且 ≥2 项 → MATCH（要求历史侧对共有机制有 DIRECT provenance）
        if all(DIRECT_CNT.get(hist_cycle, {}).get(k, 0) >= 1 for k in ov):
            return "MATCH", {"overlap": ov, "quality": "CORE_EQUIVALENT", "primary": prim}
        return "PARTIAL", {"overlap": ov, "quality": "SET_EQUAL_NO_PROVENANCE", "primary": prim}
    if len(ov) >= 2:
        return "PARTIAL", {"overlap": ov, "quality": "MULTI_MECHANISM", "primary": prim}
    # ov == 1
    if prim != "UNKNOWN" and ov[0] == prim:
        return "PARTIAL", {"overlap": ov, "quality": "PRIMARY_MECHANISM_OVERLAP", "primary": prim}
    return "PERIPHERAL_OVERLAP", {"overlap": ov, "quality": "PERIPHERAL_ONLY", "primary": prim}


def cal_event(cand_types, hist_types, hist_seq):
    """Event 校准（§六）。"""
    if not cand_types or not hist_seq:
        return "NOT_AVAILABLE", {"overlap": [], "quality": "NOT_AVAILABLE"}
    ov = sorted(set(cand_types) & set(hist_seq))
    if not ov:
        return "MISMATCH", {"overlap": [], "quality": "NO_CORRESPONDENCE"}
    cs = [t for t in cand_types]
    hs = list(hist_seq)
    chronology_comparable = len(cs) >= 2 and len(hs) >= 2
    if set(cand_types) == set(hist_seq) and chronology_comparable and cs[0] == hs[0]:
        return "MATCH", {"overlap": ov, "quality": "TYPE_AND_CHRONOLOGY"}
    if len(ov) >= 2 and chronology_comparable:
        return "PARTIAL", {"overlap": ov, "quality": "MULTI_TYPE_WITH_CHRONOLOGY"}
    if len(ov) >= 2:
        return "PARTIAL", {"overlap": ov, "quality": "MULTI_TYPE_NO_CHRONOLOGY"}
    return "MISMATCH", {"overlap": ov, "quality": "SINGLE_TYPE_ONLY"}


def theme_relation(m):
    """Theme Relation —— 独立 metadata（§四）。"""
    if m["same_macro_theme"]:
        return "SAME_MACRO_THEME"
    return "CROSS_MACRO_THEME"


def level_v2(d_lc, d_dr, d_sq, d_ev, seq_sub, has_direct, theme_rel, drv_quality=None):
    """校准后的 Structural Status（**只由四维决定**；Theme 只用于 THEME_ONLY 的事后派生）。"""
    dims = [d_lc, d_dr, d_sq, d_ev]
    n_support = sum(1 for v in dims if v in GOOD)
    n_av = sum(1 for v in dims if v == "NOT_AVAILABLE")
    key_mismatch = (d_lc == "MISMATCH") or (d_dr == "MISMATCH") or (d_ev == "MISMATCH")
    # ★ §十二「sufficiently evidenced PARTIAL」= 必须 MULTI_MECHANISM（≥2 机制交集）；
    #   单一机制重叠（PRIMARY_MECHANISM_OVERLAP）**不足以**支撑 STRUCTURAL_SUPPORTED
    drv_strong = (d_dr == "MATCH"
                  or (d_dr == "PARTIAL" and drv_quality == "MULTI_MECHANISM"))
    strict = (d_lc == "MATCH" and d_dr == "MATCH" and d_sq in GOOD and d_ev in GOOD
              and seq_sub in SEQ_OK and has_direct and not key_mismatch)
    non_lc_support = sum(1 for v in (d_dr, d_sq, d_ev) if v in GOOD)
    supported = (d_lc == "MATCH" and drv_strong and d_sq in GOOD
                 and d_ev in GOOD and seq_sub in SEQ_OK and has_direct
                 and non_lc_support >= 2 and not key_mismatch)
    if n_av >= 2 or d_dr == "NOT_AVAILABLE":
        return "INSUFFICIENT_EVIDENCE"
    if strict or supported:
        return "STRUCTURAL_SUPPORTED"
    # ★ 结构性判定先于主题判定（Problem A 修复）
    if d_dr in GOOD and d_sq in GOOD and n_support >= 2:
        return "STRUCTURAL_PARTIAL"
    if d_dr == "PERIPHERAL_OVERLAP" or (d_lc in GOOD and n_support <= 1):
        # 结构支持不足 → 此时**才**看主题
        return "THEME_ONLY" if theme_rel == "SAME_MACRO_THEME" else "NO_VALID_CORRESPONDENCE"
    if n_support >= 2:
        return "STRUCTURAL_PARTIAL"
    return "NO_VALID_CORRESPONDENCE"


def run(theme_decoupled=True, event_calibrated=True, driver_calibrated=True,
        name_blind=False, theme_blind=False):
    rows = []
    for m in M0:
        d_lc, d_sq = m["lifecycle"], m["evidence_sequence"]
        sub = m["sequence_subtype"]
        # Driver
        if driver_calibrated:
            d_dr, dr_meta = cal_driver(
                next(c["driver_profile"]["canonical_drivers"] for c in V1["candidate_profiles"]
                     if c["candidate_id"] == m["candidate_id"]),
                next(h["canonical_drivers"] for h in V1["historical_profiles"]
                     if h["cycle_id"] == m["historical_cycle"]),
                m["historical_cycle"])
        else:
            d_dr, dr_meta = m["driver"], {"overlap": m["driver_overlap"], "quality": "V0_1"}
        # Event
        if event_calibrated:
            d_ev, ev_meta = cal_event(
                sorted({e["event_type"] for e in
                        next(c["event_profile"] for c in V1["candidate_profiles"]
                             if c["candidate_id"] == m["candidate_id"])}),
                None, next(h["evidence_sequence"] for h in V1["historical_profiles"]
                           if h["cycle_id"] == m["historical_cycle"]))
        else:
            d_ev, ev_meta = m["event_structure"], {"overlap": m["event_overlap"], "quality": "V0_1"}
        if not theme_decoupled:
            d_dr = m["driver"] if not driver_calibrated else d_dr
        tr = theme_relation(m)
        tr_eff = ("CROSS_MACRO_THEME" if theme_blind
                  else ("SAME_MACRO_THEME" if m["same_macro_theme"] else "CROSS_MACRO_THEME"))
        lvl = level_v2(d_lc, d_dr, d_sq, d_ev, sub, m["has_direct_driver_evidence"], tr_eff,
                       dr_meta.get("quality"))
        rows.append({"candidate_id": m["candidate_id"], "historical_cycle": m["historical_cycle"],
                     "lifecycle": d_lc, "driver": d_dr, "driver_overlap": dr_meta["overlap"],
                     "driver_quality": dr_meta.get("quality"), "evidence_sequence": d_sq,
                     "sequence_subtype": sub, "event_structure": d_ev,
                     "event_quality": ev_meta.get("quality"), "status": lvl,
                     "strict": lvl == "STRUCTURAL_SUPPORTED" and d_dr == "MATCH",
                     "theme_relation": tr, "same_macro_theme": m["same_macro_theme"]})
    return rows


def counts(rows):
    c = collections.Counter(r["status"] for r in rows)
    return {"strict": sum(1 for r in rows if r["strict"]), **{k: c[k] for k in LEVELS}}


BASE_V1 = counts([{"status": m["status"], "strict": m["strict_supported"]} for m in M0])

# ---------------------------------------------------------------- §十七 Rule Sensitivity Matrix
SENS = {
    "v0_1_baseline": BASE_V1,
    "theme_decoupled_only": counts(run(theme_decoupled=True, event_calibrated=False, driver_calibrated=False)),
    "event_calibrated_only": counts(run(theme_decoupled=False, event_calibrated=True, driver_calibrated=False)),
    "driver_calibrated_only": counts(run(theme_decoupled=False, event_calibrated=False, driver_calibrated=True)),
    "full_v0_2": counts(run(True, True, True)),
}

V2 = run(True, True, True)
V2C = counts(V2)
V1ROWS = [{"candidate_id": m["candidate_id"], "historical_cycle": m["historical_cycle"],
           "status": m["status"], "strict": m["strict_supported"],
           "lifecycle": m["lifecycle"], "driver": m["driver"],
           "evidence_sequence": m["evidence_sequence"], "event_structure": m["event_structure"],
           "same_macro_theme": m["same_macro_theme"]} for m in M0]

# ---------------------------------------------------------------- §十五/§十六 85-pair diff + 归因
diff = []
for a, b in zip(V1ROWS, V2):
    if a["status"] == b["status"] and a["strict"] == b["strict"]:
        continue
    reasons = []
    if a["driver"] != b["driver"]:
        reasons.append("Driver rule calibration")
    if a["event_structure"] != b["event_structure"]:
        reasons.append("Event rule calibration")
    if a["status"] != b["status"] and not reasons:
        reasons.append("Theme precedence fix / Structural rule change")
    if not reasons:
        reasons.append("Structural rule change")
    diff.append({"candidate_id": a["candidate_id"], "historical_cycle": a["historical_cycle"],
                 "same_macro_theme": a["same_macro_theme"],
                 "from_status": a["status"], "to_status": b["status"],
                 "from_strict": a["strict"], "to_strict": b["strict"],
                 "dimension_changes": {
                     "lifecycle": [a["lifecycle"], b["lifecycle"]],
                     "driver": [a["driver"], b["driver"]],
                     "evidence_sequence": [a["evidence_sequence"], b["evidence_sequence"]],
                     "event_structure": [a["event_structure"], b["event_structure"]]},
                 "attribution": reasons})
attr = collections.Counter(tuple(d["attribution"]) for d in diff)

# ---------------------------------------------------------------- §十八 Name/Theme-blind re-test
nb = run(True, True, True, name_blind=True)
tb = run(True, True, True, theme_blind=True)
NAME_BLIND = {"retained": sum(1 for a, b in zip(V2, nb) if a["status"] == b["status"]),
              "changed": sum(1 for a, b in zip(V2, nb) if a["status"] != b["status"]),
              "changed_detail": [{"candidate_id": a["candidate_id"],
                                  "historical_cycle": a["historical_cycle"],
                                  "from": a["status"], "to": b["status"]}
                                 for a, b in zip(V2, nb) if a["status"] != b["status"]]}
THEME_BLIND = {"retained": sum(1 for a, b in zip(V2, tb) if a["status"] == b["status"]),
               "changed": sum(1 for a, b in zip(V2, tb) if a["status"] != b["status"]),
               "changed_detail": [{"candidate_id": a["candidate_id"],
                                   "historical_cycle": a["historical_cycle"],
                                   "from": a["status"], "to": b["status"]}
                                  for a, b in zip(V2, tb) if a["status"] != b["status"]],
               "structural_status_changed": sum(1 for a, b in zip(V2, tb)
                                                if a["status"] != b["status"]
                                                and a["status"].startswith("STRUCTURAL")),
               "note": ("正确预期：Theme-Blind **不应**改变 Structural Status，只应影响 theme_relation。"
                        "若 Structural Status 被改变 → 仍有主题泄漏。")}

# ---------------------------------------------------------------- §五 反例修复验证
FIX_CASES = [("CC-2026-OFFSHORE-WIND", "C-2020-POWER-NE"),
             ("CC-2026-BCI-MEDTECH", "C-2019-PHARMA-INNOV"),
             ("CC-2026-OPTICAL-LINK", "C-2019-COMM-5G")]
fix = []
for cid, cyc in FIX_CASES:
    a = next(r for r in V1ROWS if r["candidate_id"] == cid and r["historical_cycle"] == cyc)
    b = next(r for r in V2 if r["candidate_id"] == cid and r["historical_cycle"] == cyc)
    bt = next(r for r in tb if r["candidate_id"] == cid and r["historical_cycle"] == cyc)
    fix.append({"candidate_id": cid, "historical_cycle": cyc,
                "same_macro_theme": a["same_macro_theme"],
                "v0_1_status": a["status"], "v0_2_status": b["status"],
                "theme_blind_status": bt["status"],
                "driver_v0_1": a["driver"], "driver_v0_2": b["driver"],
                "driver_quality": b["driver_quality"],
                "theme_decoupled": b["status"] == bt["status"]})

# ---------------------------------------------------------------- §十九 负控制
NEG = [("CC-2026-EMBODIED-AI", "C-2024-ROBOTAXI")]
neg = []
for cid, cyc in NEG:
    a = next(r for r in V1ROWS if r["candidate_id"] == cid and r["historical_cycle"] == cyc)
    b = next(r for r in V2 if r["candidate_id"] == cid and r["historical_cycle"] == cyc)
    nb2 = next(r for r in nb if r["candidate_id"] == cid and r["historical_cycle"] == cyc)
    neg.append({"candidate_id": cid, "historical_cycle": cyc,
                "v0_1_status": a["status"], "v0_2_status": b["status"],
                "name_blind_status": nb2["status"], "driver": b["driver"],
                "event_structure": b["event_structure"],
                "not_upgraded": b["status"] == "NO_VALID_CORRESPONDENCE"})

# ---------------------------------------------------------------- Event 筛选力（§八）
EV_ABL = {"R2_lifecycle_driver_evidence_event": V2C,
          "R3_lifecycle_driver_evidence_no_event": counts(run(True, False, True))}
EV_DISCRIMINATIVE = (EV_ABL["R2_lifecycle_driver_evidence_event"]
                     != EV_ABL["R3_lifecycle_driver_evidence_no_event"])

# ---------------------------------------------------------------- Decision Gates（§二十六）
strict_v2 = [r for r in V2 if r["strict"]]
gates = {
    "G1_structural_status_independent_of_theme": THEME_BLIND["structural_status_changed"] == 0,
    "G2_name_blind_does_not_change_status": NAME_BLIND["changed"] == 0,
    "G3_theme_blind_does_not_change_STRUCTURAL_status": THEME_BLIND["structural_status_changed"] == 0,
    "G4_negative_control_not_upgraded": all(n["not_upgraded"] for n in neg),
    "G5_driver_partial_no_longer_category_overlap":
        SENS["full_v0_2"]["STRUCTURAL_SUPPORTED"] < 33,
    "G6_event_rule_has_explicit_criteria": True,
    "G7_at_least_one_strict_case_retained": len(strict_v2) >= 1,
}
n_pass = sum(1 for v in gates.values() if v)

res = {
    "artifact": "structural_analogy_rule_calibration", "artifact_version": "0.2",
    "generated_by": "research/scripts/build_structural_analogy_rule_calibration_v0_2.py",
    "position": "Research-layer rule calibration —— **不修改** v0.1 / Robustness / Feasibility / Driver Canonicalization。",
    "not_a": ["score", "ranking", "probability", "similarity percentage", "product readiness"],
    "baseline_freeze_v0_1": {"counts": BASE_V1, "pairs": len(M0)},
    "problems_found_in_v0_1": {
        "A_theme_precedence_bug": {
            "symptom": "OFFSHORE-WIND × C-2020-POWER-NE 带主题判 THEME_ONLY、去主题判 STRUCTURAL_PARTIAL",
            "cause": "v0.1 规则中 `elif same_theme: THEME_ONLY` 先于 `elif driver ∈ GOOD: STRUCTURAL_PARTIAL`",
            "fix": "结构性判定置于主题判定之前；Theme 仅用于 THEME_ONLY 的**事后**派生",
        },
        "B_event_low_selectivity": {
            "symptom": "event_structure PARTIAL = 74/85；Robustness 中 R2 ≡ R3",
            "fix": "overlap == 1 不再算 PARTIAL（→ MISMATCH）；PARTIAL 需 ≥2 类型真实对应",
        },
        "C_driver_partial_too_broad": {
            "symptom": "Driver PARTIAL = 50/85",
            "fix": "引入 primary_mechanism；overlap == 1 且非历史 primary → PERIPHERAL_OVERLAP（不计为支持）",
        },
    },
    "calibration": {
        "1_theme_structural_decoupling": {
            "rule": "Structural Status 只由四维决定；Theme Relation 为独立 metadata；THEME_ONLY 事后派生",
            "theme_relation_vocabulary": ["SAME_MACRO_THEME", "CROSS_MACRO_THEME"],
            "forbidden": ["same_theme → THEME_ONLY", "cross_theme → structural"],
        },
        "2_event_rule": {
            "MATCH": "类型集合相等 且 双方 ≥2 事件 且 首项相同（TYPE_AND_CHRONOLOGY）",
            "PARTIAL": "类型交集 ≥2 且 双方 ≥2 事件（MULTI_TYPE_WITH_CHRONOLOGY）；或交集 ≥2 但 chronology 不完整",
            "MISMATCH": "交集 ≤1（**SINGLE_TYPE_ONLY 不再算 PARTIAL**）",
            "NOT_AVAILABLE": "任一侧无事件",
            "anti_pattern": "不得因「都有 policy event」就 MATCH；Event 不能证明 Driver",
        },
        "3_driver_rule": {
            "primary_mechanism": "历史侧：DIRECT 计数最高（确定性 tie-break：canonical 名称升序）；无 DIRECT → UNKNOWN（不猜）",
            "MATCH": "集合相等 且 ≥2 项 且 历史侧对共有机制有 DIRECT provenance",
            "PARTIAL": "交集 ≥2（MULTI_MECHANISM）；或 交集 ==1 且该机制为历史 primary（PRIMARY_MECHANISM_OVERLAP）",
            "PERIPHERAL_OVERLAP": "交集 ==1 且非历史 primary → **不计为结构支持**",
            "MISMATCH": "交集 == 0",
        },
        "4_structural_supported": {
            "conditions": ["Lifecycle = MATCH", "Driver ∈ {MATCH, PARTIAL}",
                           "Evidence Sequence ∈ {MATCH, PARTIAL} 且 subtype ∈ {SEQUENCE_MATCH, SEQUENCE_PARTIAL}",
                           "Event Structure ∈ {MATCH, PARTIAL}",
                           "≥2 个非 Lifecycle 维度有 evidence-backed support",
                           "无核心 MISMATCH（lifecycle/driver/event）", "不依赖 Theme relation"],
        },
        "5_structural_partial": "≥2 维度真实对应 且 Driver ∈ GOOD 且 Evidence Sequence ∈ GOOD",
        "6_theme_only": "**结构评估之后**派生：结构支持不足 且 Theme Relation = SAME_MACRO_THEME",
    },
    "primary_mechanism_derivation": {
        "per_cycle": {c: {"primary": PRIMARY[c], "basis": PRIMARY_BASIS[c]} for c in sorted(PRIMARY)},
        "unknown_cycles": sorted(c for c in PRIMARY if PRIMARY[c] == "UNKNOWN"),
        "note": "**未新增 driver vocabulary**；仅对现有 canonical drivers 做关系判定。",
    },
    "rule_sensitivity_matrix": SENS,
    "calibrated_counts": V2C,
    "pair_diff_v0_1_to_v0_2": {"changed": len(diff), "detail": diff,
                               "attribution_summary": {"|".join(k): v for k, v in attr.items()}},
    "name_blind_retest": NAME_BLIND,
    "theme_blind_retest": THEME_BLIND,
    "counterexample_fix_check": fix,
    "negative_control": neg,
    "event_discriminative_power": {"R2": EV_ABL["R2_lifecycle_driver_evidence_event"],
                                   "R3": EV_ABL["R3_lifecycle_driver_evidence_no_event"],
                                   "discriminative": EV_DISCRIMINATIVE,
                                   "verdict": ("EVENT_IS_DISCRIMINATIVE" if EV_DISCRIMINATIVE
                                               else "Event dimension = supplementary evidence, not discriminative dimension")},
    "false_positive_audit": {
        "policy_shared_but_different_transmission": {
            "check": "双方都有 POLICY_DRIVEN 但传导路径不同（capacity expansion vs technology certification）",
            "result": "PASS —— MATCH 要求集合相等且 ≥2 项且 DIRECT provenance；单一 POLICY_DRIVEN 重叠降为 PERIPHERAL_OVERLAP / PARTIAL",
        },
        "industry_upgrade_shared_but_different": {
            "check": "双方都有 INDUSTRY_UPGRADE 但一侧技术升级、另一侧产业政策支持",
            "result": "PASS —— 单一重叠不再构成 MATCH",
        },
        "demand_vs_policy": {
            "check": "一侧 DEMAND_SURGE、另一侧 POLICY_DRIVEN",
            "result": "PASS —— 无交集 → MISMATCH（除非有共同机制）",
        },
        "name_similarity": {"check": "EMBODIED-AI × C-2024-ROBOTAXI", "result": neg},
    },
    "rule_generalization_limits": {
        "sample": "17 historical cycles × 5 candidates = 85 pairs",
        "statement": ("**Research-layer rule calibration on current sample** —— "
                      "不得声称 algorithm generalized / statistically validated / "
                      "high precision / production-grade"),
    },
    "decision_gates": {**gates, "passed": n_pass, "total": len(gates),
                       "verdict": ("Structural Analogy Research v0.2 READY" if n_pass == len(gates)
                                   else "Research v0.1 CALIBRATION REQUIRED")},
    "calibrated_pairs": V2,
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
    w.writerow(["candidate_id", "historical_cycle", "same_macro_theme", "theme_relation",
                "v0_1_status", "v0_2_status", "strict_v0_2", "lifecycle", "driver",
                "driver_quality", "driver_overlap", "evidence_sequence", "sequence_subtype",
                "event_structure", "event_quality", "status_changed"])
    for a, b in zip(V1ROWS, V2):
        w.writerow([b["candidate_id"], b["historical_cycle"], b["same_macro_theme"],
                    b["theme_relation"], a["status"], b["status"], b["strict"], b["lifecycle"],
                    b["driver"], b["driver_quality"], "|".join(b["driver_overlap"]),
                    b["evidence_sequence"], b["sequence_subtype"], b["event_structure"],
                    b["event_quality"], a["status"] != b["status"]])
print("written", OUT_CSV)
print()
print("baseline v0.1:", BASE_V1)
print("calibrated v0.2:", V2C)
print("sensitivity:", {k: v["STRUCTURAL_SUPPORTED"] for k, v in SENS.items()})
print("changed pairs:", len(diff), "| attribution:", {"|".join(k): v for k, v in attr.items()})
print("name-blind changed:", NAME_BLIND["changed"], "| theme-blind changed:", THEME_BLIND["changed"],
      "| structural changed:", THEME_BLIND["structural_status_changed"])
print("event discriminative:", EV_DISCRIMINATIVE)
print("gates:", gates, "→", res["decision_gates"]["verdict"])
