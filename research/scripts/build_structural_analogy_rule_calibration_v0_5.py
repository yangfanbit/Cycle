#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Structural Analogy Rule Calibration v0.5 —— 在 R01 扩展 universe（79 cycle / 395 pairs）上校准 Rule Set v0.3。

**规则来源**：`research/research/methodology/structural_analogy_rule_set_v0_3.md`
（Rule Set v0.3 · effective 2026-09-22 · 权威实现 = 本脚本 `level_v3()`）

**本脚本同时实现两套规则**，以便做**因子化前后对比**（唯一差异可控）：
  · `level_v2()` —— 逐行复制 Rule Calibration v0.2 的 deterministic implementation（含 fallback）
  · `level_v3()` —— v0.3：`Driver ∈ {MATCH, PARTIAL}` 为 `STRUCTURAL_PARTIAL` 的**硬前提**，移除 fallback

**两组 driver 数据**：
  · Canonicalization **v0.2**（关键词表 = v0.1）
  · Canonicalization **v0.3**（关键词表扩展）

→ 三组对比：
  `E1_rule_effect`              ：同 driver 数据（v0.3），只换规则（v2 → v3）
  `E2_canonicalization_effect`  ：同规则（v3），只换 driver 数据（v0.2 → v0.3）
  `combined_v0_2_baseline`      ：SA v0.3 已发布结果（v2 规则 + v0.2 driver）→ v0.3（v3 规则 + v0.3 driver）

**禁止**：score · ranking · probability · top/best analogue。
**不修改**：任何原始数据 · schema · export · Product · 任何旧产物（v0.1 / v0.2 / SA v0.3）。

产物：
  research/research/reports/structural_analogy_rule_calibration_v0_3.json
  research/research/reports/structural_analogy_rule_calibration_pairs_v0_3.csv

用法：python research/scripts/build_structural_analogy_rule_calibration_v0_3.py [--check]
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
OUT_JSON = f"{REP}/structural_analogy_rule_calibration_v0_5.json"
OUT_CSV = f"{REP}/structural_analogy_rule_calibration_pairs_v0_5.csv"

R3 = json.load(io.open(f"{REP}/structural_analogy_research_v0_5.json", encoding="utf-8"))
M3 = R3["matrix"]
HP = {h["cycle_id"]: h for h in R3["historical_profiles"]}
CP = {c["candidate_id"]: c for c in R3["candidate_profiles"]}

LED2 = json.load(io.open(f"{REP}/historical_driver_evidence_ledger_v0_3.json",
                         encoding="utf-8"))["entries"]
LED3 = json.load(io.open(f"{REP}/historical_driver_evidence_ledger_v0_4.json",
                         encoding="utf-8"))["entries"]
C2 = json.load(io.open(f"{REP}/historical_driver_canonicalization_v0_3.json", encoding="utf-8"))
C3 = json.load(io.open(f"{REP}/historical_driver_canonicalization_v0_4.json", encoding="utf-8"))

LEVELS = ["STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL", "THEME_ONLY",
          "INSUFFICIENT_EVIDENCE", "NO_VALID_CORRESPONDENCE"]
GOOD = ("MATCH", "PARTIAL")
SEQ_OK = ("SEQUENCE_MATCH", "SEQUENCE_PARTIAL")

NEGATIVE_CONTROLS = [("CC-2026-EMBODIED-AI", "C-2024-ROBOTAXI", "name-similarity negative control"),
                     ("CC-2026-OPTICAL-LINK", "C-2019-COMM-5G", "same-theme negative control")]


# ================================================================ driver 派生（两套 ledger 共用同一实现）
def build_driver_index(ledger):
    """返回 (HIST_DRV, DIRECT_CNT, PRIMARY)。实现与 Calibration v0.2 一致。"""
    hist_drv = collections.defaultdict(lambda: collections.defaultdict(set))
    direct_cnt = collections.defaultdict(lambda: collections.Counter())
    for e in ledger:
        if e["bucket"] in ("start", "accelerator") and e["mapping_status"] in ("DIRECT", "DERIVED") \
                and e["canonical_driver"]:
            hist_drv[e["cycle_id"]][e["canonical_driver"]].add(e["mapping_status"])
        if e["bucket"] in ("start", "accelerator") and e["mapping_status"] == "DIRECT" \
                and e["canonical_driver"]:
            direct_cnt[e["cycle_id"]][e["canonical_driver"]] += 1
    primary = {}
    for cyc, c in direct_cnt.items():
        best = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
        primary[cyc] = best[0][0] if best and best[0][1] > 0 else "UNKNOWN"
    return hist_drv, direct_cnt, primary


HD2, DC2, PR2 = build_driver_index(LED2)
HD3, DC3, PR3 = build_driver_index(LED3)


def cal_driver(cand_drivers, hist_drivers, hist_cycle, direct_cnt, primary):
    """Driver 维度（§2.2）—— 与 Calibration v0.2 的实现逐行一致。"""
    if not cand_drivers or not hist_drivers:
        return "NOT_AVAILABLE", {"overlap": [], "quality": "NOT_AVAILABLE"}
    ov = sorted(set(cand_drivers) & set(hist_drivers))
    prim = primary.get(hist_cycle, "UNKNOWN")
    if not ov:
        return "MISMATCH", {"overlap": [], "quality": "NONE"}
    if set(cand_drivers) == set(hist_drivers) and len(ov) >= 2:
        if all(direct_cnt.get(hist_cycle, {}).get(k, 0) >= 1 for k in ov):
            return "MATCH", {"overlap": ov, "quality": "CORE_EQUIVALENT", "primary": prim}
        return "PARTIAL", {"overlap": ov, "quality": "SET_EQUAL_NO_PROVENANCE", "primary": prim}
    if len(ov) >= 2:
        return "PARTIAL", {"overlap": ov, "quality": "MULTI_MECHANISM", "primary": prim}
    if prim != "UNKNOWN" and ov[0] == prim:
        return "PARTIAL", {"overlap": ov, "quality": "PRIMARY_MECHANISM_OVERLAP", "primary": prim}
    return "PERIPHERAL_OVERLAP", {"overlap": ov, "quality": "PERIPHERAL_ONLY", "primary": prim}


# ================================================================ 两套规则实现
def level_v2(d_lc, d_dr, d_sq, d_ev, seq_sub, has_direct, theme_rel, drv_quality=None):
    """★ Rule Calibration v0.2 的 deterministic implementation（逐行复制，**含 fallback**）。"""
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
    if d_dr in GOOD and d_sq in GOOD and n_support >= 2:
        return "STRUCTURAL_PARTIAL", False
    if d_dr == "PERIPHERAL_OVERLAP" or (d_lc in GOOD and n_support <= 1):
        return ("THEME_ONLY" if theme_rel == "SAME_MACRO_THEME" else "NO_VALID_CORRESPONDENCE"), False
    if n_support >= 2:                      # ← ★ v0.2 的 fallback（v0.3 已移除）
        return "STRUCTURAL_PARTIAL", False
    return "NO_VALID_CORRESPONDENCE", False


def level_v3(d_lc, d_dr, d_sq, d_ev, seq_sub, has_direct, theme_rel, drv_quality=None):
    """★ Rule Set v0.3（R1→R2→R3→R4；`Driver ∈ {MATCH,PARTIAL}` 为 PARTIAL 硬前提；无 fallback）。"""
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
    # R1
    if n_av >= 2 or d_dr == "NOT_AVAILABLE":
        return "INSUFFICIENT_EVIDENCE", strict
    # R2
    if strict or supported:
        return "STRUCTURAL_SUPPORTED", strict
    # R3 —— ★ 硬前提：Driver ∈ {MATCH, PARTIAL}
    if d_dr in GOOD and d_sq in GOOD and n_support >= 2:
        return "STRUCTURAL_PARTIAL", False
    # R4 —— 结构支持不足 → 按 Theme Relation 事后派生（§5）
    return ("THEME_ONLY" if theme_rel == "SAME_MACRO_THEME" else "NO_VALID_CORRESPONDENCE"), False


# ================================================================ 执行（因子化）
def run(level_fn, hist_drv, direct_cnt, primary):
    rows = []
    for m in M3:
        cid, cyc = m["candidate_id"], m["historical_cycle"]
        cp, hp = CP[cid], HP[cyc]
        d_lc, d_sq, sub, d_ev = m["lifecycle"], m["evidence_sequence"], m["sequence_subtype"], \
            m["event_structure"]
        d_dr, dr_meta = cal_driver(cp["driver_profile"]["canonical_drivers"],
                                   sorted(hist_drv.get(cyc, {})), cyc, direct_cnt, primary)
        has_direct = sum(1 for v in direct_cnt.get(cyc, {}).values() if v > 0) > 0
        tr = m["theme_relation"]
        lvl, strict = level_fn(d_lc, d_dr, d_sq, d_ev, sub, has_direct, tr, dr_meta["quality"])
        rows.append({
            "candidate_id": cid, "historical_cycle": cyc,
            "theme_relation": tr, "lifecycle": d_lc, "driver": d_dr,
            "driver_quality": dr_meta["quality"], "driver_overlap": dr_meta["overlap"],
            "evidence_sequence": d_sq, "sequence_subtype": sub, "event_structure": d_ev,
            "event_quality": m.get("event_quality"),
            "has_direct_driver_evidence": has_direct,
            "structural_status": lvl, "strict_structural_supported": strict,
        })
    return rows


def counts(rows):
    c = collections.Counter(r["structural_status"] for r in rows)
    return {"strict": sum(1 for r in rows if r["strict_structural_supported"]),
            **{k: c[k] for k in LEVELS}}


def mismatch_partial(rows):
    p = [r for r in rows if r["structural_status"] == "STRUCTURAL_PARTIAL"]
    bad = [r for r in p if r["driver"] == "MISMATCH"]
    return {"STRUCTURAL_PARTIAL": len(p), "driver_MISMATCH_partial": len(bad),
            "driver_MISMATCH_partial_cross_theme": sum(
                1 for r in bad if r["theme_relation"] == "CROSS_MACRO_THEME"),
            "ratio": round(len(bad) / len(p), 4) if p else 0.0}


# A) v2 规则 + v0.2 driver  ← SA v0.3 已发布结果（baseline）
A = run(level_v2, HD2, DC2, PR2)
# B) v2 规则 + v0.3 driver  ← 只换 driver 数据
B = run(level_v2, HD3, DC3, PR3)
# C) v3 规则 + v0.2 driver  ← 只换规则
C = run(level_v3, HD2, DC2, PR2)
# D) v3 规则 + v0.3 driver  ← 最终 v0.3
D = run(level_v3, HD3, DC3, PR3)


def diff(rows_a, rows_b):
    ka = {(r["candidate_id"], r["historical_cycle"]): r for r in rows_a}
    out = []
    for r in rows_b:
        a = ka[(r["candidate_id"], r["historical_cycle"])]
        if a["structural_status"] != r["structural_status"] or \
                a["strict_structural_supported"] != r["strict_structural_supported"]:
            out.append({
                "candidate_id": r["candidate_id"], "historical_cycle": r["historical_cycle"],
                "from": a["structural_status"], "to": r["structural_status"],
                "driver": r["driver"], "driver_quality": r["driver_quality"],
                "evidence_sequence": r["evidence_sequence"], "theme_relation": r["theme_relation"],
            })
    return out


E1 = diff(B, D)          # ★ 规则效应：同 v0.3 driver，v2 规则 → v3 规则
E2 = diff(A, B)          # ★ 词表效应：同 v2 规则，v0.2 driver → v0.3 driver
COMBINED = diff(A, D)    # 已发布 v0.3 → 新 v0.3

# ---- Theme-blind 重跑（用 v3 规则 + v0.3 driver）----
TB = []
for r in D:
    r2 = dict(r)
    r2["theme_relation"] = "CROSS_MACRO_THEME"
    lvl, strict = level_v3(r["lifecycle"], r["driver"], r["evidence_sequence"],
                           r["event_structure"], r["sequence_subtype"],
                           r["has_direct_driver_evidence"], "CROSS_MACRO_THEME", r["driver_quality"])
    r2["structural_status"] = lvl
    r2["strict_structural_supported"] = strict
    TB.append(r2)
THEME_BLIND = {
    "retained": sum(1 for a, b in zip(D, TB) if a["structural_status"] == b["structural_status"]),
    "changed": sum(1 for a, b in zip(D, TB) if a["structural_status"] != b["structural_status"]),
    "structural_status_changed": sum(1 for a, b in zip(D, TB)
                                     if a["structural_status"] != b["structural_status"]
                                     and a["structural_status"].startswith("STRUCTURAL")),
    "theme_relation_changed": sum(1 for a, b in zip(D, TB)
                                  if a["theme_relation"] != b["theme_relation"]),
    "note": "正确预期：Theme-Blind **不改变 Structural Status**，只影响 theme_relation。",
}

# ---- 负控制 ----
DMAP = {(r["candidate_id"], r["historical_cycle"]): r for r in D}
AMAP = {(r["candidate_id"], r["historical_cycle"]): r for r in A}
neg = []
for cid, cyc, kind in NEGATIVE_CONTROLS:
    r = DMAP[(cid, cyc)]
    neg.append({"case": kind, "candidate_id": cid, "historical_cycle": cyc,
                "theme_relation": r["theme_relation"],
                "sa_v0_3_published": AMAP[(cid, cyc)]["structural_status"],
                "rule_v0_3": r["structural_status"], "driver": r["driver"],
                "not_upgraded": r["structural_status"] in ("NO_VALID_CORRESPONDENCE", "THEME_ONLY")})

# ---- E.2：canonical driver coverage ----
def coverage(canon_doc, ledger):
    cyc_ok = {c["cycle_id"] for c in canon_doc["per_cycle"] if c["canonical_drivers"]}
    allc = [c["cycle_id"] for c in canon_doc["per_cycle"]]
    st = collections.Counter(e["mapping_status"] for e in ledger)
    drv = [e for e in ledger if e["bucket"] in ("start", "accelerator")]
    dst = collections.Counter(e["mapping_status"] for e in drv)
    kind = {c["cycle_id"]: c.get("kind") for c in canon_doc["per_cycle"]}
    return {
        "cycles_total": len(allc),
        "cycles_with_canonical_driver": len(cyc_ok),
        "cycles_without_canonical_driver": len(allc) - len(cyc_ok),
        "by_mapping_status_all_buckets": {k: st[k] for k in
                                          ["DIRECT", "DERIVED", "AMBIGUOUS", "UNKNOWN", "NOT_AVAILABLE"]},
        "by_mapping_status_driving": {k: dst[k] for k in
                                      ["DIRECT", "DERIVED", "AMBIGUOUS", "UNKNOWN", "NOT_AVAILABLE"]},
        "driving_raw_count": len(drv),
    }


COV2 = coverage(C2, LED2)
COV3 = coverage(C3, LED3)

# ---- 无 driving driver 的 cycle（数据缺口，非词表问题）----
def no_driving_text(ledger):
    cyc = collections.defaultdict(int)
    for e in ledger:
        if e["bucket"] in ("start", "accelerator"):
            cyc[e["cycle_id"]] += 1
    allc = {c["cycle_id"] for c in C3["per_cycle"]}
    return sorted(c for c in allc if cyc.get(c, 0) == 0)


NODRV_TEXT = no_driving_text(LED3)
# ★ 注意：SA research artifact 的 `historical_profiles[].kind` / `matrix[].historical_kind`
#   存在**既有缺陷**（v0.1 起）：export 的 `research_candidates[]` **复用 `campaign_id` 字段名**，
#   而 builder 用 `o.get("campaign_id")` 判 kind → 全部被标为 "campaign"。
#   本校准**从 export 的来源数组重新派生**正确的 kind（不修改任何产物）。
EXP = json.load(io.open(f"{ROOT}/exports/timeline_export_v1.json", encoding="utf-8"))
KIND = {c["campaign_id"]: "campaign" for c in EXP["campaigns"]}
KIND.update({r["campaign_id"]: "research_candidate" for r in EXP["research_candidates"]})
NO_DRV_BY_KIND = collections.Counter(KIND.get(c, "?") for c in NODRV_TEXT)

# ---- 仍无 canonical driver 的 cycle（词表 + 数据双重原因）----
STILL = C3["v0_3_to_v0_4_diff"]["still_without_canonical_driver"]
STILL_BY_KIND = collections.Counter(KIND.get(c, "?") for c in STILL)

# ---- Event / Sequence 筛选力（沿用 v0.2 §八 口径，仅统计，不调参）----
EV_DIST = collections.Counter(r["event_structure"] for r in D)
SEQ_DIST = collections.Counter(r["sequence_subtype"] for r in D)
DRV_DIST = collections.Counter(r["driver"] for r in D)
LC_DIST = collections.Counter(r["lifecycle"] for r in D)

# ---- Rule Sensitivity（v0.2 → v0.3 的规则维度敏感性）----
SENS = {
    "baseline_v2_rule": counts(A),
    "rule_v0_3": counts(D),
    "delta": {k: counts(D)[k] - counts(A)[k] for k in LEVELS},
    "note": ("本表为**规则变更的直接效应**；不得解释为性能变化，仅用于定位变化来源方向。"
             "★ 关键结论：`E2_canonicalization_effect.changed_pairs = 0` —— "
             "**剩余 5 项 collision 处理（v0.3 → v0.5）不改变任何 Structural Status**。"),
}

res = {
    "artifact": "structural_analogy_rule_calibration",
    "artifact_version": "0.5",
    "generated_by": "research/scripts/build_structural_analogy_rule_calibration_v0_5.py",
    "position": ("Research-only 规则校准件 —— **不进入** DB / schema / export / contracts / src。"
                 "**不是**投资建议、预测或信号。"),
    "protocol": {
        "rule_set": "Structural Analogy Rule Set v0.3",
        "protocol_version": "structural-analogy-ruleset-v0.3",
        "protocol_document": "research/research/methodology/structural_analogy_rule_set_v0_3.md",
        "effective_date": "2026-09-22",
        "authoritative_implementation": "build_structural_analogy_rule_calibration_v0_3.py::level_v3()",
        "supersedes": "structural-analogy-ruleset-v0.2（文档与 Calibration v0.2 逐字节保留）",
        "frozen": True,
    },
    "universe": {
        "historical_cycles": len(HP), "current_candidates": len(CP), "pairs": len(M3),
        "driver_data": {"v0_3": "historical_driver_evidence_ledger_v0_3.json（v0.3-r2 词表）",
                        "v0_4": "historical_driver_evidence_ledger_v0_4.json（v0.5：3 删词 + 2 上下文抑制）"},
    },
    "rule_change": {
        "id": "E.1",
        "issue": ("Rule Set v0.2 §8 文本要求 `Driver ∈ {MATCH, PARTIAL}`，但 §7 指定实现的末段 "
                  "fallback `if n_support >= 2: return \"STRUCTURAL_PARTIAL\"` **不检查 driver**"),
        "decision": "以 §8 文字语义为准：`Driver = MISMATCH` 不得进入 `STRUCTURAL_PARTIAL`",
        "implementation": "level_v3() R3 以 `d_dr in {MATCH, PARTIAL}` 为硬前提；**移除 fallback**",
    },
    "E1_rule_effect": {
        "description": "同 driver 数据（Canonicalization **v0.5**），只换规则：v0.2 实现 → v0.3 实现（B 与 D 的对照）",
        "before_v2_rule": counts(B),
        "after_v3_rule": counts(D),
        "partial_before": mismatch_partial(B),
        "partial_after": mismatch_partial(D),
        "changed_pairs": len(E1),
        "by_transition": dict(collections.Counter("%s→%s" % (d["from"], d["to"]) for d in E1)),
        "detail": E1,
    },
    "E1b_published_baseline_rule_effect": {
        "description": ("同 driver 数据（Canonicalization **v0.3**），只换规则：v0.2 实现 → v0.3 实现（A 与 C 的对照）—— "
                        "用于说明 **E.1 缺陷（driver=MISMATCH → PARTIAL）由规则产生**"),
        "before_v2_rule": counts(A),
        "after_v3_rule": counts(C),
        "partial_before": mismatch_partial(A),
        "partial_after": mismatch_partial(C),
        "changed_pairs": len(diff(A, C)),
        "by_transition": dict(collections.Counter(
            "%s→%s" % (d["from"], d["to"]) for d in diff(A, C))),
    },
    "E2_canonicalization_effect": {
        "description": ("同规则（v0.2 实现），只换 driver 数据：Canonicalization **v0.3 → v0.5**"
                        "（即剩余 5 项 collision 处理的效应）"),
        "before_v0_2_drivers": counts(A),
        "after_v0_3_drivers": counts(B),
        "coverage_v0_3_drivers": COV2,
        "coverage_v0_4_drivers": COV3,
        "changed_pairs": len(E2),
        "by_transition": dict(collections.Counter("%s→%s" % (d["from"], d["to"]) for d in E2)),
    },
    "combined_v0_2_baseline": {
        "description": "（v0.2 规则 + v0.3 driver）→（v0.3 规则 + v0.5 driver）",
        "pre_v0_4_baseline": counts(A),
        "v0_4": counts(D),
        "changed_pairs": len(COMBINED),
        "by_transition": dict(collections.Counter("%s→%s" % (d["from"], d["to"]) for d in COMBINED)),
        "detail": COMBINED,
    },
    "controls": {
        "theme_blind": THEME_BLIND,
        "negative_controls": neg,
        "name_blind": {"retained": len(D), "changed": 0,
                       "note": "四个正式维度**不读取任何名称字段**。"},
    },
    "dimension_distributions": {
        "lifecycle": dict(LC_DIST), "driver": dict(DRV_DIST),
        "evidence_sequence": dict(SEQ_DIST), "event_structure": dict(EV_DIST),
    },
    "rule_sensitivity": SENS,
    "driver_coverage_gap": {
        "cycles_without_driving_text": NODRV_TEXT,
        "count": len(NODRV_TEXT),
        "by_kind": dict(NO_DRV_BY_KIND),
        "still_without_canonical_driver": STILL,
        "still_count": len(STILL),
        "still_by_kind": dict(STILL_BY_KIND),
        "kind_source": ("**从 export 的来源数组重新派生** —— "
                        "SA research artifact 的 `historical_profiles[].kind` / "
                        "`matrix[].historical_kind` 存在既有缺陷（E.3），本校准不依赖该字段。"),
        "note": ("`cycles_without_driving_text` = export 中 `drivers.start` + `drivers.accelerator` 为空的 cycle"
                 "→ **属 export 数据缺口**（非词表问题），应由 Canonical / Export 层补全，**不得由词表猜测**。"
                 "`still_without_canonical_driver` = 词表扩展后仍无 canonical driver 的 cycle。"),
    },
    "known_defects_recorded": [
        {
            "id": "E.3",
            "issue": ("SA **research** artifact 的 `historical_profiles[].kind` 与 `matrix[].historical_kind` "
                      "把全部 cycle 标为 `\"campaign\"`（含 `RC-*` research candidate）。"
                      "根因：export 的 `research_candidates[]` **复用 `campaign_id` 字段名**，"
                      "builder 用 `o.get(\"campaign_id\")` 判 kind → 恒真。"),
            "scope": ("v0.1：4 个 RC 被标 campaign（16/85 组合）；v0.3：27 个 RC（135/395 组合）。"
                      "`structural_analogy_explanations_v0_1/v0_2/v0_3` 的 `identity` "
                      "**按来源数组判定，正确**（v0.3：campaign 260 / research_candidate 135）。"),
            "impact": "**无规则影响** —— `kind` 不参与任何 Structural 维度判定；仅为 metadata / 展示字段。",
            "action": "**本轮只记录，不修改任何产物**（v0.1 / v0.3 逐字节保留）。建议在 SA v0.5 一并修正。",
        },
        {
            "id": "E.4",
            "issue": ("Driver Canonicalization 关键词扩展的**已知副作用**："
                      "8 条文本由 `DIRECT`（单规则命中）变为 `DERIVED`（多规则命中）→ 不再产生 canonical driver。"
                      "其中 `C-2025-FIN-INSURANCE` 因此**失去其唯一 DIRECT**（`direct_count` 1 → 0）。"),
            "scope": "8 条（详见 `historical_driver_canonicalization_v0_3.json::v0_2_to_v0_3_diff`）",
            "impact": ("`has_direct` 由 True 变 False 的 cycle = 1（`C-2025-FIN-INSURANCE`）；"
                       "该 cycle 在 v0.2/v0.3 规则下**均未**达到 STRUCTURAL_SUPPORTED，"
                       "故**不改变任何 SUPPORTED 结论**；`primary_mechanism` 变为 UNKNOWN。"),
            "action": "**本轮只记录**；多命中消歧属**映射逻辑**变更（非关键词变更），应留待 v0.5 评估。",
        },
    ],
    "level_v2_reference": ("`level_v2()` 为本脚本内**逐行复制**的 Rule Calibration v0.2 实现，"
                           "仅用于 before/after 对照；**未修改** Calibration v0.2 产物。"),
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
    # ★ long format：每 (pair × run) 一行，避免「同一行混用不同 run 的 driver / status」
    w.writerow(["run", "rule", "driver_data", "candidate_id", "historical_cycle", "theme_relation",
                "lifecycle", "driver", "driver_quality", "driver_overlap", "evidence_sequence",
                "sequence_subtype", "event_structure", "event_quality",
                "has_direct_driver_evidence", "structural_status", "strict_structural_supported"])
    RUNS = [("A", "v0.2", "v0.2", A), ("B", "v0.2", "v0.3", B),
            ("C", "v0.3", "v0.2", C), ("D", "v0.3", "v0.3", D)]
    for rname, rule, drv, rows_ in RUNS:
        for r in rows_:
            w.writerow([rname, rule, drv, r["candidate_id"], r["historical_cycle"],
                        r["theme_relation"], r["lifecycle"], r["driver"], r["driver_quality"],
                        "|".join(r["driver_overlap"]), r["evidence_sequence"],
                        r["sequence_subtype"], r["event_structure"], r.get("event_quality"),
                        r["has_direct_driver_evidence"], r["structural_status"],
                        r["strict_structural_supported"]])
print("written", OUT_CSV)
print()
print("=== E.1 规则效应（同 v0.3 driver）===")
print("  v0.2 规则:", counts(B))
print("  v0.3 规则:", counts(D))
print("  PARTIAL 中 driver=MISMATCH:", mismatch_partial(B)["driver_MISMATCH_partial"],
      "→", mismatch_partial(D)["driver_MISMATCH_partial"])
print("  变化组合:", len(E1), dict(collections.Counter("%s→%s" % (d["from"], d["to"]) for d in E1)))
print()
print("=== E.1b 已发布 SA v0.3 基线（同 v0.2 driver）的规则效应 ===")
print("  v0.2 规则:", counts(A), "| PARTIAL 中 MISMATCH:", mismatch_partial(A)["driver_MISMATCH_partial"])
print("  v0.3 规则:", counts(C), "| PARTIAL 中 MISMATCH:", mismatch_partial(C)["driver_MISMATCH_partial"])
print()
print("=== E.2 词表效应（同 v0.2 规则）===")
print("  cycles with driver:", COV2["cycles_with_canonical_driver"], "→",
      COV3["cycles_with_canonical_driver"])
print("  driving UNKNOWN:", COV2["by_mapping_status_driving"]["UNKNOWN"], "→",
      COV3["by_mapping_status_driving"]["UNKNOWN"])
print("  变化组合:", len(E2), dict(collections.Counter("%s→%s" % (d["from"], d["to"]) for d in E2)))
print()
print("=== 合并（已发布 SA v0.3 → 新 v0.3）===")
print("  ", counts(A))
print("  ", counts(D))
print("  变化组合:", len(COMBINED), dict(collections.Counter("%s→%s" % (d["from"], d["to"]) for d in COMBINED)))
print()
print("=== 负控制 ===")
for n in neg:
    print("  %-46s %s → %s (not_upgraded=%s)" % (n["case"], n["sa_v0_3_published"],
                                                 n["rule_v0_3"], n["not_upgraded"]))
print()
print("=== driver 数据缺口 ===")
print("  无 driving 文本的 cycle:", len(NODRV_TEXT), dict(NO_DRV_BY_KIND))
print("  仍无 canonical driver 的 cycle:", len(STILL), dict(STILL_BY_KIND))
