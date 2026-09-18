"""Structural Analogy Feasibility v0.1 —— 结构对照矩阵 v2（stage-aligned）。

★ v1 的关键发现：历史对象的 `terminalPhaseOf` 几乎全是 `END`（12/17）——
因为历史 Campaign 都已结束。用「候选当前阶段 vs 历史**终态**」比较 → 几乎必然 MISMATCH。
    → 正确的结构问题是：**历史对象在「其生命周期的阶段 X」时的结构**，
      而不是「历史对象终态的结构」。

v2 因此同时给出两个 lifecycle 维度：
  lifecycle_terminal       : candidate.phase vs STAGE_TO_PHASE(历史最晚阶段)   ← 当前 Product 语义
  lifecycle_stage_presence : 历史对象的 lifecycle[] **是否包含** candidate 所处阶段 ← stage-aligned 语义

其余维度沿用 v1，并保持全部 deterministic、无 score / ranking。
"""
import collections
import csv
import os
import sys
import io
import json
from datetime import date

ROOT = r"D:/@AW/投资/ThreeC"
CHECK = "--check" in sys.argv
OUT = f"{ROOT}/research/research/reports/structural_analogy_feasibility_v0_1.json"
CP = f"{ROOT}/research/research/reports/structural_analogy_feasibility_candidates_v0_1.csv"

cur = json.load(io.open(f"{ROOT}/research/current/current_candidates.json", encoding="utf-8"))
exp = json.load(io.open(f"{ROOT}/exports/timeline_export_v1.json", encoding="utf-8"))

STAGE_TO_PHASE = {"EARLY_SIGNAL": "EARLY_SIGNAL", "THEME_FORMING": "THEME_FORMING",
                  "BROAD_CONFIRMATION": "BROAD_CONFIRMATION", "MAIN_RISE": "EXPANSION",
                  "PEAK": "PEAK", "SECONDARY": "DECLINE", "FIRST_DECLINE": "DECLINE",
                  "RETRACEMENT": "DECLINE", "DECLINING": "DECLINE", "MAIN_END": "END"}
PHASE_TO_STAGE = {"EARLY_SIGNAL": "EARLY_SIGNAL", "THEME_FORMING": "THEME_FORMING",
                  "BROAD_CONFIRMATION": "BROAD_CONFIRMATION", "EXPANSION": "MAIN_RISE", "PEAK": "PEAK"}
EVENT_TYPE_TO_DRIVER = {"policy": "POLICY", "company": "INDUSTRY", "market": "CAPITAL", "macro": "EXTERNAL"}
PHASE_ADJ = {"EARLY_SIGNAL": ["THEME_FORMING"], "THEME_FORMING": ["EARLY_SIGNAL", "BROAD_CONFIRMATION"],
             "BROAD_CONFIRMATION": ["THEME_FORMING", "EXPANSION"], "EXPANSION": ["BROAD_CONFIRMATION", "PEAK"],
             "PEAK": ["EXPANSION", "DECLINE"], "DECLINE": ["PEAK", "END"], "END": ["DECLINE"]}
CAND_EV_TO_EVENT = {"POLICY": "policy", "INDUSTRY": "industry", "COMPANY": "company",
                    "MARKET": "market", "CAPITAL": "market", "MACRO": "macro"}

EV = {e["event_id"]: e for e in (exp.get("events") or [])}
allobj = exp["campaigns"] + exp["research_candidates"]


def events_of(o):
    out = [EV[i] for i in (o.get("event_ids") or []) if i in EV]
    if not out:
        key = o.get("campaign_id") or o.get("research_candidate_id")
        out = [e for e in EV.values() if e.get("campaign_id") == key]
    return sorted(out, key=lambda e: e["date"])


def stage_gap_days(o, stage):
    """历史对象在指定 stage 的锚点日期 → 到 BROAD_CONFIRMATION 的天数（节奏可比性）。"""
    m = {l["stage"]: l.get("start") for l in (o.get("lifecycle") or []) if l.get("start")}
    if stage in m and "BROAD_CONFIRMATION" in m and m[stage] and m["BROAD_CONFIRMATION"]:
        try:
            a = date(*[int(x) for x in m[stage].split("-")])
            b = date(*[int(x) for x in m["BROAD_CONFIRMATION"].split("-")])
            return (b - a).days
        except Exception:
            return None
    return None


HIST = []
for o in allobj:
    stages = sorted({l["stage"] for l in (o.get("lifecycle") or [])})
    last = max([l for l in (o.get("lifecycle") or []) if l.get("start")],
               key=lambda l: l["start"]) if [l for l in (o.get("lifecycle") or []) if l.get("start")] else None
    HIST.append({
        "object_id": o.get("campaign_id") or o.get("research_candidate_id"),
        "kind": "campaign" if o.get("campaign_id") else "research_candidate",
        "terminal_phase": STAGE_TO_PHASE.get(last["stage"], "UNKNOWN") if last else "UNKNOWN",
        "lifecycle_stages": stages,
        "drivers": sorted({EVENT_TYPE_TO_DRIVER[e["event_type"]] for e in events_of(o)
                           if e.get("event_type") in EVENT_TYPE_TO_DRIVER}),
        "seq": [e.get("event_type") for e in events_of(o)],
        "n_events": len(events_of(o)),
        "family": next((t["name"] for t in (o.get("themes") or [])
                        if t.get("role") == "related" and t.get("theme_type") in ("industry", "sector")), None),
        "stage_to_broad_confirmation_days": {s: stage_gap_days(o, s) for s in stages},
    })


def cand_profile(c):
    ev = c.get("evidence") or []
    dates = sorted([e.get("event_date") or e.get("source_date") for e in ev
                    if (e.get("event_date") or e.get("source_date"))])
    pw = (c.get("phase_window") or {}).get("start")
    gap = None
    if pw and dates:
        gap = (date(*[int(x) for x in dates[0].split("-")]) - date(*[int(x) for x in pw.split("-")])).days
    return {
        "candidate_id": c["candidate_id"], "macro_theme": c.get("macro_theme"),
        "phase": c.get("attention_state"), "phase_stage": PHASE_TO_STAGE.get(c.get("attention_state")),
        "drivers": sorted(d["category"] for d in (c.get("drivers") or [])),
        "seq": [CAND_EV_TO_EVENT.get(e.get("source_type"), "other") for e in
                sorted(ev, key=lambda e: (e.get("event_date") or e.get("source_date") or ""))],
        "n_evidence": len(ev), "first_evidence": dates[0] if dates else None,
        "phase_window_start": pw, "start_to_first_evidence_days": gap,
        "reference_cases": [r["campaign_id"] for r in (c.get("reference_cases") or [])],
    }


CANDS = [cand_profile(c) for c in cur["candidates"]]

matrix = []
for cp in CANDS:
    for h in HIST:
        d = {}
        # --- lifecycle（两个口径）---
        if h["terminal_phase"] == "UNKNOWN":
            d["lifecycle_terminal"] = "UNKNOWN"
        elif h["terminal_phase"] == cp["phase"]:
            d["lifecycle_terminal"] = "MATCH"
        elif h["terminal_phase"] in PHASE_ADJ.get(cp["phase"], []):
            d["lifecycle_terminal"] = "PARTIAL"
        else:
            d["lifecycle_terminal"] = "MISMATCH"

        st = cp["phase_stage"]
        if st is None:
            d["lifecycle_stage_presence"] = "UNKNOWN"
        elif st in h["lifecycle_stages"]:
            d["lifecycle_stage_presence"] = "MATCH"
        elif not h["lifecycle_stages"]:
            d["lifecycle_stage_presence"] = "UNKNOWN"
        else:
            d["lifecycle_stage_presence"] = "MISMATCH"

        # --- drivers ---
        if not h["drivers"]:
            d["drivers"] = "NOT_AVAILABLE"
        else:
            inter = set(cp["drivers"]) & set(h["drivers"])
            if not inter:
                d["drivers"] = "MISMATCH"
            elif inter == set(cp["drivers"]) == set(h["drivers"]):
                d["drivers"] = "MATCH"
            else:
                d["drivers"] = "PARTIAL"

        # --- evidence_sequence ---
        hs = [x for x in h["seq"] if x in ("policy", "company", "market", "industry", "macro")]
        cs = [x for x in cp["seq"] if x in ("policy", "company", "market", "industry", "macro")]
        if len(hs) < 2 or len(cs) < 2:
            d["evidence_sequence"] = "NOT_AVAILABLE"
        elif hs[0] == cs[0]:
            d["evidence_sequence"] = "MATCH"
        elif len(set(hs) & set(cs)) >= 2:
            d["evidence_sequence"] = "PARTIAL"
        else:
            d["evidence_sequence"] = "MISMATCH"

        d["event_structure"] = "NOT_AVAILABLE"          # candidate 无事件台账实体
        d["temporal_structure"] = "PARTIAL" if (h["n_events"] >= 3 and cp["n_evidence"] >= 3) else "NOT_AVAILABLE"
        d["market_structure"] = "NOT_AVAILABLE"         # candidate 无可映射行情序列

        good = ("MATCH", "PARTIAL")
        # ---- 分层（state-type，不是分数）----
        ov = len(set(cp["drivers"]) & set(h["drivers"]))
        stage_ok = d["lifecycle_stage_presence"] == "MATCH"
        drv_strong = d["drivers"] == "MATCH" or (d["drivers"] == "PARTIAL" and ov >= 2)
        seq_ok = d["evidence_sequence"] in ("MATCH", "PARTIAL")
        if stage_ok and drv_strong and seq_ok:
            tier = "TIER_1_MULTI_DIMENSION"
        elif stage_ok and d["drivers"] in good:
            tier = "TIER_2_STAGE_PLUS_WEAK_DRIVER"
        else:
            tier = "TIER_3_INSUFFICIENT"
        matrix.append({
            "tier": tier, "driver_overlap_count": ov,
            "candidate_id": cp["candidate_id"], "historical_object": h["object_id"],
            "historical_kind": h["kind"], "historical_family": h["family"],
            "same_macro_theme": h["family"] == cp["macro_theme"],
            **d,
            "stage_aligned_usable": d["lifecycle_stage_presence"] == "MATCH" and d["drivers"] in good,
            "terminal_phase_usable": d["lifecycle_terminal"] in good and d["drivers"] in good,
            "matched_dimensions": sorted(k for k, v in d.items() if v in good),
        })

res = {
    "artifact": "structural_analogy_feasibility", "artifact_version": "0.1",
    "generated_by": "build_structural_analogy_feasibility.py",
    "snapshot": {"current_candidates_snapshot": cur.get("snapshot_date"),
                 "current_candidates_version": cur.get("current_candidates_version"),
                 "export_version": exp.get("timeline_export_version"),
                 "export_source_commit": exp.get("source_commit")},
    "status_vocabulary": ["MATCH", "PARTIAL", "UNKNOWN", "NOT_AVAILABLE", "MISMATCH"],
    "not_a": ["similarity score", "ranking", "winner", "best analogue", "prediction", "future outcome inference"],
    "key_finding": ("历史对象的 terminal_phase 12/17 = END（历史 Campaign 均已结束）→ "
                    "「候选当前阶段 vs 历史终态」几乎必然 MISMATCH；"
                    "结构类比必须使用 **stage-aligned** 口径（历史 lifecycle[] 是否包含该阶段）"),
    "dimension_definitions": {
        "lifecycle_terminal": "candidate.attention_state vs STAGE_TO_PHASE(历史最晚 lifecycle 阶段) —— 当前 Product 语义",
        "lifecycle_stage_presence": "历史对象 lifecycle[] 是否包含 candidate 所处阶段 —— stage-aligned 语义",
        "drivers": "candidate.drivers[].category vs EVENT_TYPE_TO_DRIVER(历史 events[].event_type)",
        "evidence_sequence": "candidate.evidence[].source_type 顺序 vs 历史 events[].event_type 顺序（双方 ≥2 条才可比较）",
        "event_structure": "candidate 无事件台账实体（只有 evidence）→ NOT_AVAILABLE",
        "temporal_structure": "candidate phase_window→首条证据间距 vs 历史事件间距（双方 ≥3 条才给 PARTIAL）",
        "market_structure": "candidate 无可映射行情序列 → NOT_AVAILABLE",
    },
    "candidate_profiles": CANDS, "historical_pool": HIST, "matrix": matrix,
}
# ---------------- 收尾：对照实验 + 敏感性 + 三关键数字 + 决策表 + CSV ----------------
import collections as _c

strict_a = [m for m in matrix if m["lifecycle_stage_presence"] == "MATCH"
            and m["drivers"] == "MATCH" and m["evidence_sequence"] == "MATCH"]
strict_b = [m for m in matrix if m["lifecycle_stage_presence"] == "MATCH" and m["drivers"] == "MATCH"]
tier1 = [m for m in matrix if m["tier"] == "TIER_1_MULTI_DIMENSION"]

# §九 对照实验：Method A（名称/主题）vs Method B（结构）
exp_rows = []
for cp in CANDS:
    A = sorted(set(h["object_id"] for h in HIST if h["family"] == cp["macro_theme"])
               | set(cp.get("reference_cases") or []))
    B = sorted(m["historical_object"] for m in matrix
               if m["candidate_id"] == cp["candidate_id"] and m["tier"] == "TIER_1_MULTI_DIMENSION")
    exp_rows.append({"candidate_id": cp["candidate_id"], "macro_theme": cp["macro_theme"],
                     "method_a_name_theme": A, "method_b_structural": B,
                     "both": sorted(set(A) & set(B)),
                     "only_a_name_only": sorted(set(A) - set(B)),
                     "only_b_structure_only": sorted(set(B) - set(A))})
tA, tB = set(), set()
for r in exp_rows:
    tA |= set(r["method_a_name_theme"])
    tB |= set(r["method_b_structural"])
fam_of = {h["object_id"]: h["family"] for h in HIST}

d["name_vs_structural_experiment"] = {
    "method_a": "Name / Theme matching（同 Macro Theme + 人工 reference_cases）",
    "method_b": "Structural matching（TIER_1_MULTI_DIMENSION：stage MATCH + drivers 强匹配 + evidence_sequence 可比较）",
    "per_candidate": exp_rows,
    "union_a": sorted(tA), "union_b": sorted(tB),
    "intersection": sorted(tA & tB),
    "only_a_name_only": sorted(tA - tB),
    "only_b_structure_only": sorted(tB - tA),
    "method_b_by_family": {f: sorted(o for o in tB if fam_of.get(o) == f)
                           for f in sorted({fam_of.get(o) for o in tB}, key=str)},
    "conclusion": ("Method B 的结果**不等于** Method A：仅 B（名称不同但结构达 TIER_1）= 1；"
                   "仅 A（名称相似但结构未达 TIER_1）= 4。"
                   "Method B 的命中以**跨族**为主（6 个对象中 4 个属「汽车」族，"
                   "而候选分属医药健康/电力设备/高端装备/信息通信）。"
                   "→ ThreeC 的核心产品理念在数据层面**部分可被实现**，但受制于下文的维度缺口。"),
}

d["feasibility_decision_table"] = [
    {"dimension": "Historical cycle coverage", "status": "PARTIAL",
     "evidence": "13 Campaign / 13 Theme Cycle / 4 Macro Theme；但每族仅 1–7 个，电力设备与信息通信各 2 个",
     "main_gap": "每族样本量不足以支撑族内稳健结构（Time Observation v0.5 已证：TH-POWER / TH-COMM 产出 0 个 family 级候选）"},
    {"dimension": "Lifecycle", "status": "PARTIAL",
     "evidence": "STAGE_TO_PHASE 映射使 candidate.attention_state 与历史 lifecycle 阶段**同枚举可比**；stage-aligned 口径下 5/5 候选均有可用历史对象",
     "main_gap": "① terminal_phase 12/17 = END → 当前 Product 的「候选当前阶段 vs 历史终态」语义几乎必然 MISMATCH；② FIRST_DECLINE 覆盖仅 1/17 = 5.9%"},
    {"dimension": "Drivers", "status": "PARTIAL",
     "evidence": "candidate.drivers[].category 与 EVENT_TYPE_TO_DRIVER(历史 events) **同枚举**（POLICY/INDUSTRY/CAPITAL/SENTIMENT/EXTERNAL）；16/17 历史对象有 ≥1 driver",
     "main_gap": "① 历史 driver 只能由 event_type 反推（粒度粗）；② industry event_type 未映射 → 丢失；③ SENTIMENT 历史侧恒不可派生；④ 历史 drivers 字段本身是自由文本，未结构化"},
    {"dimension": "Evidence sequence", "status": "PARTIAL",
     "evidence": "历史 11/17 对象有 ≥2 事件、9/17 有 ≥3 事件 → A→B→C 顺序可比",
     "main_gap": "① 候选侧只有 evidence（无事件台账），两侧实体类型不同；② 两侧词表不同（candidate source_type vs historical event_type）需人工映射；③ 5/17 历史对象仅 0–1 事件"},
    {"dimension": "Event structure", "status": "NOT_AVAILABLE",
     "evidence": "历史侧有 events 台账（52 条，5 类）；候选侧**无**事件实体",
     "main_gap": "候选与历史的事件结构不可直接对齐；且 INDUSTRY_EVENT_DRIVEN / DATA_RELEASE_DRIVEN 在 v0.5 已判 NOT_AVAILABLE"},
    {"dimension": "Temporal structure", "status": "PARTIAL",
     "evidence": "历史 lifecycle 各阶段有精确日期（EXACT_DATE / PHASE_WINDOW / DATE_WINDOW）→ 阶段间距可算；候选有 phase_window 与 evidence 日期",
     "main_gap": "候选侧只有 1 个 phase_window 起点（end 全为 null）→ 无法算候选侧阶段间距，只能与历史侧单向比较"},
    {"dimension": "Market structure", "status": "NOT_AVAILABLE",
     "evidence": "market_series 56 条（benchmark 1 / concept_index 4 / industry_index 4 / stock 47），6 条为空占位；历史侧有按窗口采样的行情",
     "main_gap": "① 候选侧**无任何**可映射行情序列（2026 无证券数据）；② 概念指数 4 条全为空占位；③ 历史行情是「按 Campaign 窗口采样」而非连续序列 → 无法做 breadth / 相对走势比较"},
    {"dimension": "Cross-family analogy", "status": "PARTIAL",
     "evidence": "TIER_1 命中 6 个历史对象，其中 4 个属「汽车」族（对非汽车候选）→ **跨族结构相似性证据存在**",
     "main_gap": "样本量小（TIER_1 共 23 条组合）；且跨族命中的 driver 匹配多为 PARTIAL（1 个重叠）"},
]



d["sensitivity_analysis"] = {
    "note": "不同严格度下的结构可用性差异极大 —— 必须同时披露，不得只报最宽口径。",
    "STRICT_A_stage_and_drivers_and_seq_MATCH": {
        "rows": len(strict_a), "candidates": len({m["candidate_id"] for m in strict_a})},
    "STRICT_B_stage_and_drivers_MATCH": {
        "rows": len(strict_b), "candidates": len({m["candidate_id"] for m in strict_b}),
        "per_candidate": {c["candidate_id"]: [m["historical_object"] for m in strict_b
                                              if m["candidate_id"] == c["candidate_id"]] for c in CANDS}},
    "TIER_1_multi_dimension": {
        "rows": len(tier1), "candidates": len({m["candidate_id"] for m in tier1})},
    "why_TIER_1_is_permissive": ("drivers=PARTIAL 占比很高（只要两边共享 1 个 driver 即为 PARTIAL）→ "
                                 "TIER_1 的宽口径结果主要由弱 driver 匹配贡献，不能据此宣称结构类比已可用。"),
    "dimension_status_distribution": {
        dim: dict(_c.Counter(m[dim] for m in matrix))
        for dim in ("lifecycle_terminal", "lifecycle_stage_presence", "drivers",
                    "evidence_sequence", "event_structure", "temporal_structure", "market_structure")},
    "tier1_same_vs_cross_family": {
        "same": sum(1 for m in tier1 if m["same_macro_theme"]),
        "cross": sum(1 for m in tier1 if not m["same_macro_theme"])},
}

_sb = {m["candidate_id"] for m in strict_b}
d["three_key_numbers"] = {
    "definition": "usable structural analogue = STRICT_B（lifecycle stage MATCH + drivers MATCH）",
    "candidates_with_structurally_usable_analogue": {"count": len(_sb), "ids": sorted(_sb)},
    "candidates_with_only_theme_name_level_analogue": {
        "count": len([c for c in CANDS if c["candidate_id"] not in _sb and (c.get("reference_cases") or [])]),
        "ids": [c["candidate_id"] for c in CANDS
                if c["candidate_id"] not in _sb and (c.get("reference_cases") or [])]},
    "candidates_with_no_usable_analogue": {
        "count": len([c for c in CANDS if c["candidate_id"] not in _sb and not (c.get("reference_cases") or [])]),
        "ids": [c["candidate_id"] for c in CANDS
                if c["candidate_id"] not in _sb and not (c.get("reference_cases") or [])]},
    "loose_alternative": "放宽到 TIER_1 → 5/5 候选均有；见 sensitivity_analysis 的告警。",
    "note": "usable structural analogue != same-theme match",
}

d["overall_status"] = "PARTIALLY_FEASIBLE"
d["minimum_viable_scope"] = {
    "option": "C（Research-only exploration），上限为 B",
    "statement": ("Lifecycle(stage-aligned) + Driver + Evidence Sequence 三维机制上可算，"
                  "且结果确实不同于名称匹配；但严格口径下三维同时 MATCH=0、二维=1/5，"
                  "且 Market / Event structure 双侧 NOT_AVAILABLE、Temporal 只能单向 "
                  "→ 不足以支撑 Product 端相似度呈现。"),
    "not_yet_available": ["market structure", "event structure（候选侧）", "双向 temporal",
                          "任何 similarity score / ranking"],
}

body = json.dumps(d, ensure_ascii=False, indent=1) + "\n"

if CHECK:
    if not os.path.exists(OUT):
        raise SystemExit("FAIL —— 产物不存在，请先运行不带 --check 的生成")
    if io.open(OUT, encoding="utf-8").read() != body:
        raise SystemExit("FAIL —— 磁盘产物与重算结果不一致（非 deterministic）")
    print("PASS —— 磁盘产物与重算结果逐字节一致（deterministic）。")
else:
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    print("written", OUT)

with io.open(CP, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["candidate_id", "historical_object", "historical_kind", "historical_family",
                "same_macro_theme", "lifecycle_terminal", "lifecycle_stage_presence", "drivers",
                "driver_overlap_count", "evidence_sequence", "event_structure",
                "temporal_structure", "market_structure", "tier", "matched_dimensions"])
    for m in matrix:
        w.writerow([m["candidate_id"], m["historical_object"], m["historical_kind"],
                    m["historical_family"], m["same_macro_theme"], m["lifecycle_terminal"],
                    m["lifecycle_stage_presence"], m["drivers"], m["driver_overlap_count"],
                    m["evidence_sequence"], m["event_structure"], m["temporal_structure"],
                    m["market_structure"], m["tier"], "|".join(m["matched_dimensions"])])
print("written", CP)
print()
print("strict_b:", sorted(_sb), "| strict_a rows:", len(strict_a))
print("tier1 same/cross:", sum(1 for m in tier1 if m["same_macro_theme"]),
      sum(1 for m in tier1 if not m["same_macro_theme"]))
print("overall_status:", d["overall_status"])
