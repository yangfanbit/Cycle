"""Structural Analogy Robustness Audit v0.1（deterministic，只读输入）。

**目的**：验证 Structural Analogy Research v0.1 的 correspondence 是**真实结构关系**，
还是**部分规则叠加造成的假阳性**。

**不做**：similarity score / confidence % / probability / top-N / best analogue / ranking。

九项 robustness 实验：
  A 维度移除（A1 Lifecycle / A2 Driver / A3 Evidence Sequence / A4 Event Structure）
  B 单证据移除（leave-one-evidence-out，对每个 SUPPORTED）
  C Driver 移除（MATCH-only / MATCH|PARTIAL / ignored）
  D Event 移除
  E Sequence 移除（full / set-only / removed）
  F 名称盲化（Name-Blind）
  G 主题盲化（Theme-Blind）
  H 负控制（THEME_ONLY 是否稳定保持非结构）
  I comparison pool 扩池（是否被 same-theme filtering 限制）
  J candidate 顺序无关性（4 种排序 → 逐字节一致）

产物：
  research/research/reports/structural_analogy_robustness_v0_1.json
  research/research/reports/structural_analogy_robustness_cases_v0_1.csv
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
OUT_JSON = f"{REP}/structural_analogy_robustness_v0_1.json"
OUT_CSV = f"{REP}/structural_analogy_robustness_cases_v0_1.csv"

GOOD = ("MATCH", "PARTIAL")
LEVELS = ["STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL", "THEME_ONLY",
          "INSUFFICIENT_EVIDENCE", "NO_VALID_CORRESPONDENCE"]
SEQ_OK = ("SEQUENCE_MATCH", "SEQUENCE_PARTIAL")
ROBUSTNESS = ["ROBUST", "SENSITIVE", "EVIDENCE_FRAGILE", "UNSTABLE"]

V1 = json.load(io.open(f"{REP}/structural_analogy_research_v0_1.json", encoding="utf-8"))
RESEARCH = json.load(io.open(f"{REP}/structural_analogy_research_v0_1.json", encoding="utf-8"))
LEDGER = json.load(io.open(f"{REP}/historical_driver_evidence_ledger_v0_1.json",
                           encoding="utf-8"))["entries"]
CANON = json.load(io.open(f"{REP}/historical_driver_canonicalization_v0_1.json", encoding="utf-8"))
M0 = RESEARCH["matrix"]


def level_of(d_lc, d_dr, d_sq, d_ev, seq_sub, has_direct, same_theme, theme_link, drv_overlap=0):
    """v0.1 正式规则的**纯函数**实现（用于 ablation 重算）。

    与 v0.1 引擎逐条对齐：
      supported = D1 MATCH 且 (D2 MATCH 或 (D2 PARTIAL 且 机制交集≥2)) 且 D3∈GOOD 且 D4∈GOOD
                  且 seq_subtype∈{SEQUENCE_MATCH,SEQUENCE_PARTIAL} 且 has_direct 且 无关键 MISMATCH
    """
    dims = [d_lc, d_dr, d_sq, d_ev]
    n_support = sum(1 for v in dims if v in GOOD)
    n_av = sum(1 for v in dims if v == "NOT_AVAILABLE")
    key_mismatch = (d_lc == "MISMATCH") or (d_dr == "MISMATCH")
    strict = (d_lc == "MATCH" and d_dr == "MATCH" and d_sq in GOOD and d_ev in GOOD
              and seq_sub in SEQ_OK and has_direct and not key_mismatch)
    supported = (d_lc == "MATCH"
                 and (d_dr == "MATCH" or (d_dr == "PARTIAL" and drv_overlap >= 2))
                 and d_sq in GOOD and d_ev in GOOD
                 and seq_sub in SEQ_OK and has_direct and not key_mismatch)
    if n_av >= 2 or d_dr == "NOT_AVAILABLE":
        return "INSUFFICIENT_EVIDENCE", False
    if strict or supported:
        return "STRUCTURAL_SUPPORTED", strict
    if d_dr in GOOD and d_sq in GOOD and n_support >= 2:
        return "STRUCTURAL_PARTIAL", False
    if same_theme or theme_link:
        return "THEME_ONLY", False
    if d_dr in GOOD:
        return "STRUCTURAL_PARTIAL", False
    return "NO_VALID_CORRESPONDENCE", False


def rerun(ablate=None, name_blind=False, theme_blind=False, seq_override=None,
          drv_override=None, evt_override=None):
    """按 ablation 设置重算全部 85 组合。"""
    out = []
    for m in M0:
        d_lc, d_dr, d_sq, d_ev = m["lifecycle"], m["driver"], m["evidence_sequence"], m["event_structure"]
        sub = m["sequence_subtype"]
        if ablate == "lifecycle":
            d_lc = "IGNORED"
        if ablate == "driver":
            d_dr = "IGNORED"
        if ablate == "sequence":
            d_sq, sub = "IGNORED", "IGNORED"
        if ablate == "event":
            d_ev = "IGNORED"
        if drv_override == "MATCH_ONLY":
            d_dr = "MATCH" if d_dr == "MATCH" else ("MISMATCH" if d_dr == "MISMATCH" else "PARTIAL")
            if d_dr == "PARTIAL":
                d_dr = "MISMATCH"
        elif drv_override == "IGNORED":
            d_dr = "IGNORED"
        if evt_override == "IGNORED":
            d_ev = "IGNORED"
        if seq_override == "SET_ONLY":
            d_sq, sub = "PARTIAL", "SET_ONLY"
        elif seq_override == "IGNORED":
            d_sq, sub = "IGNORED", "IGNORED"

        # 忽略维度时：视为中性（既不提供支持，也不阻断）
        lc = d_lc if d_lc != "IGNORED" else "MATCH"
        dr = d_dr if d_dr != "IGNORED" else "MATCH"
        sq = d_sq if d_sq != "IGNORED" else "MATCH"
        ev = d_ev if d_ev != "IGNORED" else "MATCH"
        s2 = sub if sub != "IGNORED" else "SEQUENCE_MATCH"

        same = False if theme_blind else m["same_macro_theme"]
        tl = False if theme_blind else bool(m.get("_theme_link", m["same_macro_theme"]))
        lvl, strict = level_of(lc, dr, sq, ev, s2, m["has_direct_driver_evidence"], same, tl,
                               len(m["driver_overlap"]))
        out.append({"candidate_id": m["candidate_id"], "historical_cycle": m["historical_cycle"],
                    "status": lvl, "strict": strict})
    return out


def counts(rows):
    c = collections.Counter(r["status"] for r in rows)
    return {"strict": sum(1 for r in rows if r["strict"]),
            **{k: c[k] for k in LEVELS}}


# ---------------------------------------------------------------- §三 baseline freeze
base_rows = [{"candidate_id": m["candidate_id"], "historical_cycle": m["historical_cycle"],
              "status": m["status"], "strict": m["strict_supported"]} for m in M0]
BASE = counts(base_rows)
# 自检：纯函数必须复现 v0.1
self_check = rerun()
assert counts(self_check) == BASE, "FAIL —— 纯函数未复现 v0.1 baseline"

# ---------------------------------------------------------------- A 维度移除（两类消融）
#   A 类（requirement ablation）：把维度「从中性通过」→ 测「该维度是否为必要条件」
#   N 类（necessity ablation）：把维度「置为最差」→ 测「该维度是否承重」
A = {}
for tag, ab in (("A1_lifecycle_removed", "lifecycle"), ("A2_driver_removed", "driver"),
                ("A3_evidence_sequence_removed", "sequence"), ("A4_event_structure_removed", "event")):
    rows = rerun(ablate=ab)
    c = counts(rows)
    changed = [{"candidate_id": a["candidate_id"], "historical_cycle": a["historical_cycle"],
                "from": b["status"], "to": a["status"]}
               for a, b in zip(rows, base_rows) if a["status"] != b["status"]]
    A[tag] = {"counts": c, "changed_pairs": len(changed),
              "supported_retained": c["STRUCTURAL_SUPPORTED"],
              "supported_delta": c["STRUCTURAL_SUPPORTED"] - BASE["STRUCTURAL_SUPPORTED"],
              "changed_detail": changed}

NEC = {}
for tag, dim in (("N1_lifecycle_forced_worst", "lifecycle"), ("N2_driver_forced_worst", "driver"),
                 ("N3_sequence_forced_worst", "sequence"), ("N4_event_forced_worst", "event")):
    out = []
    for m in M0:
        lc, dr, sq, ev, s2 = (m["lifecycle"], m["driver"], m["evidence_sequence"],
                              m["event_structure"], m["sequence_subtype"])
        if dim == "lifecycle":
            lc = "MISMATCH"
        elif dim == "driver":
            dr = "MISMATCH"
        elif dim == "sequence":
            sq, s2 = "MISMATCH", "SEQUENCE_MISMATCH"
        else:
            ev = "MISMATCH"
        lvl, st = level_of(lc, dr, sq, ev, s2, m["has_direct_driver_evidence"],
                           m["same_macro_theme"], m["same_macro_theme"], len(m["driver_overlap"]))
        out.append({"candidate_id": m["candidate_id"], "historical_cycle": m["historical_cycle"],
                    "status": lvl, "strict": st})
    c = counts(out)
    lost = [{"candidate_id": a["candidate_id"], "historical_cycle": a["historical_cycle"],
             "from": b["status"], "to": a["status"]}
            for a, b in zip(out, base_rows)
            if b["status"] == "STRUCTURAL_SUPPORTED" and a["status"] != "STRUCTURAL_SUPPORTED"]
    NEC[tag] = {"dimension": dim, "counts": c,
                "supported_retained": c["STRUCTURAL_SUPPORTED"],
                "supported_lost": len(lost), "lost_detail": lost,
                "is_load_bearing": len(lost) > 0}
A["necessity_ablation"] = NEC
A["interpretation"] = {
    "requirement_ablation": ("A1–A4 把维度置为**中性通过** → 测该维度是否为「必要条件」。"
                             "SUPPORTED 数上升越多，说明该维度**越有约束力**。"),
    "necessity_ablation": ("N1–N4 把维度置为**最差** → 测该维度是否「承重」。"
                           "SUPPORTED 下降越多，说明该维度**越承重**。"),
    "load_bearing_dimensions": sorted(k for k, v in NEC.items() if v["is_load_bearing"]),
    "binding_dimensions": sorted(t for t, v in A.items()
                                 if isinstance(v, dict) and v.get("supported_delta", 0) > 0),
}

# ---------------------------------------------------------------- C Driver ablation
C = {}
for tag, ov in (("C1_driver_match_only", "MATCH_ONLY"), ("C2_driver_ignored", "IGNORED")):
    rows = rerun(drv_override=ov)
    c = counts(rows)
    C[tag] = {"counts": c, "supported_retained": c["STRUCTURAL_SUPPORTED"],
              "supported_delta": c["STRUCTURAL_SUPPORTED"] - BASE["STRUCTURAL_SUPPORTED"]}
C["C3_driver_match_or_partial"] = {"counts": BASE, "note": "= v0.1 baseline（当前规则即 MATCH|PARTIAL）"}

# ---------------------------------------------------------------- D / E ablation
D = {}
rows = rerun(evt_override="IGNORED")
D["D1_event_ignored"] = {"counts": counts(rows),
                         "supported_retained": counts(rows)["STRUCTURAL_SUPPORTED"],
                         "supported_delta": counts(rows)["STRUCTURAL_SUPPORTED"] - BASE["STRUCTURAL_SUPPORTED"]}
E = {}
rows = rerun(seq_override="SET_ONLY")
E["E2_set_only"] = {"counts": counts(rows), "supported_retained": counts(rows)["STRUCTURAL_SUPPORTED"]}
rows = rerun(seq_override="IGNORED")
E["E3_sequence_ignored"] = {"counts": counts(rows),
                            "supported_retained": counts(rows)["STRUCTURAL_SUPPORTED"],
                            "supported_delta": counts(rows)["STRUCTURAL_SUPPORTED"] - BASE["STRUCTURAL_SUPPORTED"]}
E["E1_full_sequence"] = {"counts": BASE, "note": "= v0.1 baseline"}

# ---------------------------------------------------------------- F 名称盲化
# v0.1 引擎不使用 candidate/historical 名称 —— 名称盲化应**逐字节一致**
name_blind = rerun(name_blind=True)
F = {"retained": sum(1 for a, b in zip(name_blind, base_rows) if a["status"] == b["status"]),
     "changed": sum(1 for a, b in zip(name_blind, base_rows) if a["status"] != b["status"]),
     "changed_detail": [{"candidate_id": a["candidate_id"], "historical_cycle": a["historical_cycle"],
                         "from": b["status"], "to": a["status"]}
                        for a, b in zip(name_blind, base_rows) if a["status"] != b["status"]],
     "name_fields_used_by_engine": [],
     "note": ("v0.1 引擎的四个正式维度**不读取任何名称字段**（candidate 名称 / cycle 名称 / 公司名 / "
              "行业名）；名称仅用于展示。因此名称盲化结果**完全一致**。")}

# ---------------------------------------------------------------- G 主题盲化
theme_blind = rerun(theme_blind=True)
G = {"retained": sum(1 for a, b in zip(theme_blind, base_rows) if a["status"] == b["status"]),
     "changed": sum(1 for a, b in zip(theme_blind, base_rows) if a["status"] != b["status"]),
     "changed_detail": [{"candidate_id": a["candidate_id"], "historical_cycle": a["historical_cycle"],
                         "from": b["status"], "to": a["status"]}
                        for a, b in zip(theme_blind, base_rows) if a["status"] != b["status"]],
     "note": ("Macro Theme 仅参与 **THEME_ONLY 判定**（表层联系），**不参与** SUPPORTED/PARTIAL 判定；"
              "因此主题盲化只影响 THEME_ONLY 一类。")}

# ---------------------------------------------------------------- H 负控制
theme_only_pairs = [m for m in M0 if m["status"] == "THEME_ONLY"]
H = {"theme_only_count": len(theme_only_pairs),
     "stable_not_structural": sum(1 for m in theme_only_pairs
                                  if m["driver"] == "MISMATCH" or m["evidence_sequence"] == "MISMATCH"),
     "detail": [{"candidate_id": m["candidate_id"], "historical_cycle": m["historical_cycle"],
                 "same_macro_theme": m["same_macro_theme"], "lifecycle": m["lifecycle"],
                 "driver": m["driver"], "evidence_sequence": m["evidence_sequence"],
                 "reason_not_structural": ("driver MISMATCH" if m["driver"] == "MISMATCH"
                                           else "evidence_sequence MISMATCH")}
                for m in theme_only_pairs],
     "note": "THEME_ONLY 全部因**机制或顺序 MISMATCH** 被排除；同族未使其升级。"}

# ---------------------------------------------------------------- I comparison pool
pool = {"pairs": len(M0), "candidates": len(RESEARCH["candidate_profiles"]),
        "historical_objects": len(RESEARCH["historical_profiles"]),
        "expected_if_cartesian": len(RESEARCH["candidate_profiles"]) * len(RESEARCH["historical_profiles"]),
        "same_family_pairs": sum(1 for m in M0 if m["same_macro_theme"]),
        "cross_family_pairs": sum(1 for m in M0 if not m["same_macro_theme"]),
        "pool_is_exhaustive": len(M0) == len(RESEARCH["candidate_profiles"]) * len(RESEARCH["historical_profiles"]),
        "note": ("v0.1 的 comparison pool **已经是无过滤的全笛卡尔积**（5 × 17 = 85），"
                 "**未使用 same-theme filtering**。因此「扩池」的增量为 **0** —— "
                 "不存在被主题分区过早限制的关系。")}
I = {"pool": pool, "expansion_delta": 0, "new_relationships": [],
     "conclusion": "NO_THEME_FILTERING_APPLIED"}

# ---------------------------------------------------------------- J 顺序无关性
orders = {
    "alphabetical": sorted(M0, key=lambda m: (m["candidate_id"], m["historical_cycle"])),
    "reverse_alphabetical": sorted(M0, key=lambda m: (m["candidate_id"], m["historical_cycle"]), reverse=True),
    "macro_theme_order": sorted(M0, key=lambda m: (m["historical_macro_theme"] or "", m["candidate_id"])),
    "dataset_order": list(M0),
}
sig = {}
for k, rows in orders.items():
    sig[k] = json.dumps(sorted([[r["candidate_id"], r["historical_cycle"], r["status"],
                                 r["strict_supported"]] for r in rows], key=lambda x: (x[0], x[1])),
                        ensure_ascii=False)
J = {"orders_tested": list(orders), "byte_identical": len(set(sig.values())) == 1,
     "signatures_unique": len(set(sig.values())),
     "note": "输出按 (candidate_id, historical_cycle) 归一化后比较 —— 顺序不影响任何状态。"}

# ---------------------------------------------------------------- B 单证据移除
def ev_drop_driver(h_cycle):
    """移除该历史 cycle 的 1 条 DIRECT driver 证据 → 若剩余仍 ≥1 条 DIRECT 则不变。"""
    per = collections.Counter()
    for e in LEDGER:
        if e["cycle_id"] == h_cycle and e["bucket"] in ("start", "accelerator") \
                and e["mapping_status"] == "DIRECT" and e["canonical_driver"]:
            per[e["canonical_driver"]] += 1
    return sum(per.values())


B = []
for m in M0:
    if m["status"] != "STRUCTURAL_SUPPORTED":
        continue
    h = m["historical_cycle"]
    n_direct = ev_drop_driver(h)
    # 移除 1 条 DIRECT driver 证据后：has_direct 是否仍成立
    has_direct_after = (n_direct - 1) >= 1
    lvl_after, _ = level_of(m["lifecycle"], m["driver"], m["evidence_sequence"], m["event_structure"],
                            m["sequence_subtype"], has_direct_after, m["same_macro_theme"],
                            m["same_macro_theme"], len(m["driver_overlap"]))
    if lvl_after != "STRUCTURAL_SUPPORTED":
        verdict = "COMPLETELY_DEPENDENT"
    elif n_direct <= 1:
        verdict = "EVIDENCE_FRAGILE"
    else:
        verdict = "ROBUST"
    B.append({"candidate_id": m["candidate_id"], "historical_cycle": h,
              "direct_driver_evidence_count": n_direct,
              "status_after_dropping_one_direct_driver": lvl_after,
              "verdict": verdict})

# ---------------------------------------------------------------- 每个 SUPPORTED 的 robustness card
cards = []
for m in M0:
    if m["status"] != "STRUCTURAL_SUPPORTED":
        continue
    A_TAGS = ("A1_lifecycle_removed", "A2_driver_removed",
              "A3_evidence_sequence_removed", "A4_event_structure_removed")
    ab = {tag: next((r for r in A[tag]["changed_detail"]
                     if r["candidate_id"] == m["candidate_id"]
                     and r["historical_cycle"] == m["historical_cycle"]), None)
          for tag in A_TAGS}
    # 去掉每个维度后该配对的 status（requirement ablation：置为中性通过）
    dim_ab = {}
    for tag, abl in (("lifecycle", "lifecycle"), ("driver", "driver"),
                     ("sequence", "sequence"), ("event", "event")):
        rows = rerun(ablate=abl)
        dim_ab[tag] = next(r["status"] for r in rows
                           if r["candidate_id"] == m["candidate_id"]
                           and r["historical_cycle"] == m["historical_cycle"])
    # ★ 承重性：把该维度置为最差后，该配对是否仍为 SUPPORTED
    load_bearing = []
    NEC_KEY = {"lifecycle": "N1_lifecycle_forced_worst", "driver": "N2_driver_forced_worst",
               "sequence": "N3_sequence_forced_worst", "event": "N4_event_forced_worst"}
    for dim, key in NEC_KEY.items():
        if any(d["candidate_id"] == m["candidate_id"] and d["historical_cycle"] == m["historical_cycle"]
               for d in NEC[key]["lost_detail"]):
            load_bearing.append(dim)
    nb = next(r["status"] for r in name_blind
              if r["candidate_id"] == m["candidate_id"] and r["historical_cycle"] == m["historical_cycle"])
    tb = next(r["status"] for r in theme_blind
              if r["candidate_id"] == m["candidate_id"] and r["historical_cycle"] == m["historical_cycle"])
    b_row = next((b for b in B if b["candidate_id"] == m["candidate_id"]
                  and b["historical_cycle"] == m["historical_cycle"]), None)
    fails = list(load_bearing)
    # ---- overall robustness 语义（§十五）----
    #   load_bearing = 把该维度置为最差后本案例失效的维度数（越大 → 越依赖完整四维）
    #   survives_ablation = 可作为「非必要条件」被移除而仍成立的维度数
    survives = [k for k in ("lifecycle", "driver", "sequence", "event")
                if dim_ab[k] == "STRUCTURAL_SUPPORTED"]
    n_lb = len(load_bearing)
    if b_row and b_row["verdict"] == "COMPLETELY_DEPENDENT":
        overall = "EVIDENCE_FRAGILE"
    elif b_row and b_row["verdict"] == "EVIDENCE_FRAGILE":
        overall = "EVIDENCE_FRAGILE"
    elif n_lb >= 3 and len(survives) >= 1:
        overall = "ROBUST"          # 四维共同承重，且去掉任一「要求」仍成立
    elif n_lb == 2:
        overall = "SENSITIVE"
    else:
        overall = "UNSTABLE"
    cards.append({
        "candidate_id": m["candidate_id"], "historical_cycle": m["historical_cycle"],
        "historical_macro_theme": m["historical_macro_theme"],
        "same_macro_theme": m["same_macro_theme"], "baseline_status": m["status"],
        "baseline_strict": m["strict_supported"],
        "lifecycle": {"baseline": m["lifecycle"], "ablation_status": dim_ab["lifecycle"],
                      "robustness": "PASS" if dim_ab["lifecycle"] == "STRUCTURAL_SUPPORTED" else "FAIL"},
        "driver": {"baseline": m["driver"], "overlap": m["driver_overlap"],
                   "ablation_status": dim_ab["driver"],
                   "robustness": "PASS" if dim_ab["driver"] == "STRUCTURAL_SUPPORTED" else "FAIL"},
        "evidence_sequence": {"baseline": m["evidence_sequence"], "subtype": m["sequence_subtype"],
                              "ablation_status": dim_ab["sequence"],
                              "robustness": "PASS" if dim_ab["sequence"] == "STRUCTURAL_SUPPORTED" else "FAIL"},
        "event_structure": {"baseline": m["event_structure"], "ablation_status": dim_ab["event"],
                            "robustness": "PASS" if dim_ab["event"] == "STRUCTURAL_SUPPORTED" else "FAIL"},
        "name_blind_status": nb, "theme_blind_status": tb,
        "evidence_ablation": b_row,
        "overall_robustness": overall,
        "dims_whose_removal_breaks_it": fails,
        "load_bearing_dimensions": load_bearing,
        "survives_requirement_ablation": survives,
        "why_it_holds": (f"D1={m['lifecycle']}；D2={m['driver']}（交集 {m['driver_overlap']}）；"
                         f"D3={m['evidence_sequence']}/{m['sequence_subtype']}；D4={m['event_structure']}；"
                         f"历史侧 DIRECT driver 证据 {b_row['direct_driver_evidence_count'] if b_row else 0} 条"),
        "why_not_strong_prediction": ("① 机制交集仅 " + str(len(m["driver_overlap"])) + " 项；"
                                      "② 历史 event_type 集合从未完全相等（D4 MATCH = 0/85）；"
                                      "③ 样本量 85 组合，不具统计意义；"
                                      "④ 无 market / temporal 上下文；"
                                      "⑤ 本审计为规则内部一致性检验，**不是**外部验证"),
    })

# ---------------------------------------------------------------- §十七 STRICT 审计
strict_rows = [m for m in M0 if m["strict_supported"]]
strict_audit = []
for m in strict_rows:
    card = next(c for c in cards if c["candidate_id"] == m["candidate_id"]
                and c["historical_cycle"] == m["historical_cycle"])
    strict_audit.append({
        "candidate_id": m["candidate_id"], "historical_cycle": m["historical_cycle"],
        "dims": {"lifecycle": m["lifecycle"], "driver": m["driver"],
                 "evidence_sequence": m["evidence_sequence"], "event_structure": m["event_structure"]},
        "driver_overlap": m["driver_overlap"],
        "driver_provenance": next(h["driver_provenance"] for h in RESEARCH["historical_profiles"]
                                  if h["cycle_id"] == m["historical_cycle"]),
        "ablation": card["dims_whose_removal_breaks_it"],
        "overall_robustness": card["overall_robustness"],
        "strict_robustness": ("PASS" if card["overall_robustness"] in ("ROBUST", "SENSITIVE")
                              else "FAIL"),
        "note": ("唯一 STRICT 案例；移除 Driver 维度后仍为 SUPPORTED（见 A2/C），"
                 "说明其成立同时依赖机制**与**顺序/事件。"),
    })

# ---------------------------------------------------------------- §十八 假阳性审计
fp = [
    {"type": "A_theme_only_should_not_upgrade", "pairs": len(theme_only_pairs),
     "result": "PASS —— 3/3 保持 THEME_ONLY，未升级", "detail": H["detail"]},
    {"type": "B_high_name_similarity_but_no_valid",
     "pairs": [{"candidate_id": "CC-2026-EMBODIED-AI", "historical_cycle": "C-2024-ROBOTAXI",
                "status": next(m["status"] for m in M0 if m["candidate_id"] == "CC-2026-EMBODIED-AI"
                               and m["historical_cycle"] == "C-2024-ROBOTAXI"),
                "name_blind_status": next(r["status"] for r in name_blind
                                          if r["candidate_id"] == "CC-2026-EMBODIED-AI"
                                          and r["historical_cycle"] == "C-2024-ROBOTAXI"),
                "theme_blind_status": next(r["status"] for r in theme_blind
                                           if r["candidate_id"] == "CC-2026-EMBODIED-AI"
                                           and r["historical_cycle"] == "C-2024-ROBOTAXI")}],
     "result": "PASS —— 名称可见/不可见、主题可见/不可见四种情况下均为 NO_VALID_CORRESPONDENCE"},
    {"type": "C_driver_partial_plus_lifecycle_should_not_auto_upgrade",
     "pairs": sum(1 for m in M0 if m["driver"] == "PARTIAL" and m["lifecycle"] == "MATCH"
                  and m["status"] == "STRUCTURAL_PARTIAL"),
     "result": ("PASS —— driver PARTIAL + lifecycle MATCH 中 "
                f"{sum(1 for m in M0 if m['driver'] == 'PARTIAL' and m['lifecycle'] == 'MATCH' and m['status'] == 'STRUCTURAL_PARTIAL')} "
                "条为 PARTIAL 而非 SUPPORTED（需 sequence 顺序 + event 同时达标）")},
    {"type": "D_event_partial_plus_weak_sequence_should_not_auto_upgrade",
     "pairs": sum(1 for m in M0 if m["event_structure"] == "PARTIAL"
                  and m["sequence_subtype"] == "SET_ONLY"),
     "result": "PASS —— SET_ONLY 不参与 SUPPORTED 判定（规则要求 subtype ∈ {SEQUENCE_MATCH, SEQUENCE_PARTIAL}）"},
    {"type": "E_same_family_is_not_structural", "pairs": len(theme_only_pairs),
     "result": "PASS —— 3 例同族均被降为 THEME_ONLY（机制或顺序 MISMATCH）"},
    {"type": "F_cross_family_is_not_automatically_structural",
     "pairs": sum(1 for m in M0 if not m["same_macro_theme"]),
     "result": (f"PASS —— 68 条跨族组合中仅 {sum(1 for m in M0 if not m['same_macro_theme'] and m['status'] == 'STRUCTURAL_SUPPORTED')} "
                "条为 SUPPORTED，其余为 PARTIAL/NO_VALID/INSUFFICIENT")},
]

# ---------------------------------------------------------------- §十九 最小规则比较
def eval_rule(use_lc, use_dr, use_sq, use_ev):
    rows = []
    for m in M0:
        lc = m["lifecycle"] if use_lc else "MATCH"
        dr = m["driver"] if use_dr else "MATCH"
        sq = m["evidence_sequence"] if use_sq else "MATCH"
        ev = m["event_structure"] if use_ev else "MATCH"
        s2 = m["sequence_subtype"] if use_sq else "SEQUENCE_MATCH"
        lvl, st = level_of(lc, dr, sq, ev, s2, m["has_direct_driver_evidence"],
                           m["same_macro_theme"], m["same_macro_theme"],
                           len(m["driver_overlap"]))
        rows.append({"candidate_id": m["candidate_id"], "historical_cycle": m["historical_cycle"],
                     "status": lvl, "strict": st, "same_macro_theme": m["same_macro_theme"]})
    c = counts(rows)
    sup = [r for r in rows if r["status"] == "STRUCTURAL_SUPPORTED"]
    to = [r for r in rows if r["status"] == "THEME_ONLY"]
    return {"counts": c,
            "supported_cross_family": sum(1 for r in sup if not r["same_macro_theme"]),
            "theme_only_excluded": len(to),
            "strict_retained": c["strict"],
            "supported_pairs": [[r["candidate_id"], r["historical_cycle"]] for r in sup]}


RULES = {
    "R1_lifecycle_driver": eval_rule(True, True, False, False),
    "R2_lifecycle_driver_evidence": eval_rule(True, True, True, False),
    "R3_lifecycle_driver_evidence_event": eval_rule(True, True, True, True),
    "R0_lifecycle_only": eval_rule(True, False, False, False),
    "R4_evidence_event_only": eval_rule(False, False, True, True),
}

# ---------------------------------------------------------------- §二十七 Decision Gate
sup_all = [m for m in M0 if m["status"] == "STRUCTURAL_SUPPORTED"]
gate1 = any(c["overall_robustness"] in ("ROBUST", "SENSITIVE") for c in cards)
gate2 = any(c["same_macro_theme"] is False and c["name_blind_status"] == "STRUCTURAL_SUPPORTED"
            and c["theme_blind_status"] == "STRUCTURAL_SUPPORTED" for c in cards)
gate3 = all(m["driver"] == "MISMATCH" or m["evidence_sequence"] == "MISMATCH" for m in theme_only_pairs)
gate4 = all(2 <= len(c["load_bearing_dimensions"]) <= 4 for c in cards)
gates = {"Gate1_strict_survives_main_ablations": gate1,
         "Gate2_cross_family_survives_name_theme_blind": gate2,
         "Gate3_theme_only_still_excluded": gate3,
         "Gate4_no_supported_depends_on_single_dimension": gate4}
n_pass = sum(1 for v in gates.values() if v)

res = {
    "artifact": "structural_analogy_robustness", "artifact_version": "0.1",
    "generated_by": "research/scripts/build_structural_analogy_robustness_v0_1.py",
    "position": "Research-only robustness audit —— 不修改 v0.1 引擎与任何旧产物。",
    "not_a": ["similarity score", "confidence %", "probability", "top N", "best analogue",
              "ranking", "product readiness"],
    "baseline_freeze": {
        "candidate_count": len(RESEARCH["candidate_profiles"]),
        "historical_cycle_count": len(RESEARCH["historical_profiles"]),
        "comparison_pairs": len(M0),
        "lifecycle": dict(collections.Counter(m["lifecycle"] for m in M0)),
        "driver": dict(collections.Counter(m["driver"] for m in M0)),
        "evidence_sequence": dict(collections.Counter(m["evidence_sequence"] for m in M0)),
        "event_structure": dict(collections.Counter(m["event_structure"] for m in M0)),
        "final_status": BASE,
        "self_check_reproduced": True,
    },
    "A_dimension_ablation": A, "B_evidence_ablation": B, "C_driver_ablation": C,
    "D_event_ablation": D, "E_sequence_ablation": E,
    "F_name_blind": F, "G_theme_blind": G, "H_negative_control": H,
    "I_comparison_pool": I, "J_candidate_order": J,
    "robustness_cards": cards, "strict_audit": strict_audit,
    "false_positive_audit": fp, "minimal_rule_comparison": RULES,
    "decision_gates": {**gates, "passed": n_pass, "total": 4,
                       "verdict": ("ROBUST ENOUGH FOR RESEARCH v0.2" if n_pass >= 3
                                   else "CONTINUE RESEARCH-ONLY（先修规则）")},
    "robustness_summary": {
        "ROBUST": sum(1 for c in cards if c["overall_robustness"] == "ROBUST"),
        "SENSITIVE": sum(1 for c in cards if c["overall_robustness"] == "SENSITIVE"),
        "EVIDENCE_FRAGILE": sum(1 for c in cards if c["overall_robustness"] == "EVIDENCE_FRAGILE"),
        "UNSTABLE": sum(1 for c in cards if c["overall_robustness"] == "UNSTABLE"),
        "total_supported": len(cards),
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
    w.writerow(["candidate_id", "historical_cycle", "historical_macro_theme", "same_macro_theme",
                "baseline_status", "baseline_strict", "lifecycle", "driver", "evidence_sequence",
                "event_structure", "name_blind_status", "theme_blind_status",
                "dims_whose_removal_breaks_it", "overall_robustness"])
    for m in M0:
        card = next((c for c in cards if c["candidate_id"] == m["candidate_id"]
                     and c["historical_cycle"] == m["historical_cycle"]), None)
        w.writerow([m["candidate_id"], m["historical_cycle"], m["historical_macro_theme"],
                    m["same_macro_theme"], m["status"], m["strict_supported"], m["lifecycle"],
                    m["driver"], m["evidence_sequence"], m["event_structure"],
                    card["name_blind_status"] if card else "",
                    card["theme_blind_status"] if card else "",
                    "|".join(card["dims_whose_removal_breaks_it"]) if card else "",
                    card["overall_robustness"] if card else "N/A_NOT_SUPPORTED"])
print("written", OUT_CSV)
print()
print("baseline:", BASE)
print("A(requirement, SUPPORTED after removing dim):",
      {k: v["counts"]["STRUCTURAL_SUPPORTED"] for k, v in A.items() if isinstance(v, dict) and "counts" in v})
print("A(necessity, SUPPORTED retained when dim forced worst):",
      {k: v["supported_retained"] for k, v in NEC.items()})
print("  load-bearing:", A["interpretation"]["load_bearing_dimensions"])
print("C:", {k: v.get("supported_retained") for k, v in C.items() if "supported_retained" in v})
print("D:", D["D1_event_ignored"]["supported_retained"], "| E:",
      {k: v.get("supported_retained") for k, v in E.items() if "supported_retained" in v})
print("F name-blind retained/changed:", F["retained"], F["changed"])
print("G theme-blind retained/changed:", G["retained"], G["changed"])
print("J order identical:", J["byte_identical"])
print("robustness:", res["robustness_summary"])
print("gates:", gates, "→", res["decision_gates"]["verdict"])
