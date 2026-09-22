"""Structural Analogy Research v0.4 —— 在 **79 Historical Objects** 上执行**已冻结**的 Rule Set v0.3。

**与 v0.2 的关系**
  · **规则不变**：仍使用 `Structural Analogy Rule Set v0.2`（`structural-analogy-ruleset-v0.2`，冻结）；
    规则实现与 `build_structural_analogy_rule_calibration_v0_2.py::level_v2()` 逐条一致。
  · **唯一变化 = Historical Universe 扩容**：v0.2 时历史侧仅 17 个 cycle；R01-01~R01-06 完成后
    历史侧为 **79 个 cycle（52 campaigns + 27 research_candidates）** → 组合数 5 × 79 = **395**。
  · v0.1 / v0.2 产物**逐字节保留**，本版本写入独立文件。

**输入（全部只读）**
  · `exports/timeline_export_v1.json`（历史侧 universe + 事件）
  · `research/current/current_candidates.json`（5 个 current candidate）
  · `research/research/reports/historical_driver_canonicalization_v0_2.json`
  · `research/research/reports/historical_driver_evidence_ledger_v0_2.json`
    （★ v0.2 版本 —— 同规则、全 universe 覆盖；已验证原 17 cycle 与 v0.1 逐条相同）
  · `research/research/reports/structural_analogy_candidate_events_v0_1.json`（candidate 事件，沿用）
  · `research/research/reports/structural_analogy_candidate_market_map_v0_1.json`（candidate 行情映射，沿用）
  · `research/research/reports/governance_classification_v0_1.json`（**governance-gates-v0.1** 元数据）

**governance 元数据的用法（严格遵守 governance-gates-v0.1）**
  · `market_evidence_state` / `beta_level` / `peak|end` 四态 **只进入 `supplementary_context`**；
  · **不参与 Structural Status 判定**（Rule Set v0.2 §12：Market / Temporal 为非正式维度）；
  · **不得**把 L1 当 Alpha、**不得**把 `A_SHARE_MARKET` 当作「独立 Campaign」的证据；
  · `result=weak` = 方向为负，**不降低**该 cycle 参与结构类比（上行/下行 cycle 均可参与）。

**严禁**：similarity_score · weighted_score · confidence_score · probability · ranking ·
top/best analogue · winner · 预测 / 胜率 / 涨跌判断 / 推荐 / 买卖信号。

产物：
  research/research/reports/structural_analogy_research_v0_4.json
  research/research/reports/structural_analogy_research_candidates_v0_4.csv

用法：python research/scripts/build_structural_analogy_research_v0_4.py [--check]
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
OUT_JSON = f"{REP}/structural_analogy_research_v0_4.json"
OUT_CSV = f"{REP}/structural_analogy_research_candidates_v0_4.csv"

# ---------------------------------------------------------------- 冻结规则常量（Rule Set v0.2）
RULE_SET = "Structural Analogy Rule Set v0.3"
RULE_VER = "structural-analogy-ruleset-v0.3"
RULE_DOC = "research/research/methodology/structural_analogy_rule_set_v0_3.md"
LEVELS = ["STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL", "THEME_ONLY",
          "INSUFFICIENT_EVIDENCE", "NO_VALID_CORRESPONDENCE"]
GOOD = ("MATCH", "PARTIAL")
SEQ_OK = ("SEQUENCE_MATCH", "SEQUENCE_PARTIAL")
DRIVER_GOOD = ("MATCH", "PARTIAL")
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
TERMINAL_MAP = {"EARLY_SIGNAL": "EARLY_SIGNAL", "THEME_FORMING": "THEME_FORMING",
                "BROAD_CONFIRMATION": "BROAD_CONFIRMATION", "MAIN_RISE": "EXPANSION",
                "PEAK": "PEAK", "SECONDARY": "DECLINE", "FIRST_DECLINE": "DECLINE",
                "RETRACEMENT": "DECLINE", "DECLINING": "DECLINE", "MAIN_END": "END"}

# ---------------------------------------------------------------- 输入
cur = json.load(io.open(f"{ROOT}/research/current/current_candidates.json", encoding="utf-8"))
exp = json.load(io.open(f"{ROOT}/exports/timeline_export_v1.json", encoding="utf-8"))
CANON = json.load(io.open(f"{REP}/historical_driver_canonicalization_v0_4.json", encoding="utf-8"))
LEDGER = json.load(io.open(f"{REP}/historical_driver_evidence_ledger_v0_4.json",
                           encoding="utf-8"))["entries"]
CEV = json.load(io.open(f"{REP}/structural_analogy_candidate_events_v0_1.json",
                        encoding="utf-8"))["events"]
MMAP = json.load(io.open(f"{REP}/structural_analogy_candidate_market_map_v0_1.json",
                         encoding="utf-8"))["mapping"]
GOV = {c["campaign_id"]: c for c in
       json.load(io.open(f"{REP}/governance_classification_v0_1.json", encoding="utf-8"))["campaigns"]}
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
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            dp[i][j] = dp[i - 1][j - 1] + 1 if a[i - 1] == b[j - 1] else max(dp[i - 1][j], dp[i][j - 1])
    return dp[len(a)][len(b)]


# ---------------------------------------------------------------- 历史 profile（HIST）
HIST_DRV = collections.defaultdict(lambda: collections.defaultdict(set))
for e in LEDGER:
    if e["bucket"] in ("start", "accelerator") and e["mapping_status"] in ("DIRECT", "DERIVED") \
            and e["canonical_driver"]:
        HIST_DRV[e["cycle_id"]][e["canonical_driver"]].add(e["mapping_status"])
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


HIST = []
# ★ v0.4 修正（E.3）：identity 必须**按来源数组**判定，不得用 `o.get("campaign_id")`。
#   根因：export 的 `research_candidates[]` **复用 `campaign_id` 字段名** → 该判定恒真，
#   v0.1~v0.3 把全部 79 个 historical object 都写成 `kind="campaign"`（含 27 个 RC）。
for _kind, _arr in (("campaign", exp.get("campaigns") or []),
                    ("research_candidate", exp.get("research_candidates") or [])):
    for o in _arr:
        c = oid(o)
        sm = {l["stage"]: l.get("start") for l in (o.get("lifecycle") or []) if l.get("start")}
        stages = sorted(sm, key=lambda s: STAGE_ORDER.index(s) if s in STAGE_ORDER else 99)
        last = max(sm.items(), key=lambda kv: kv[1])[0] if sm else None
        evs = events_of(o)
        HIST.append({
            "cycle_id": c,
            "historical_object_kind": _kind,
            "campaign_id": c if _kind == "campaign" else None,
            "research_candidate_id": c if _kind == "research_candidate" else None,
            "kind": _kind,                      # 兼容字段（与 historical_object_kind 同值）
            "macro_theme": macro_theme(o), "sub_themes": sub_themes(o),
            "lifecycle_stages": stages, "stage_starts": sm,
            "terminal_phase": (TERMINAL_MAP.get(last, "UNKNOWN")) if last else "UNKNOWN",
            "canonical_drivers": sorted(HIST_DRV.get(c, {})),
            "driver_provenance": {k: sorted(v) for k, v in sorted(HIST_DRV.get(c, {}).items())},
            "driver_direct_count": sum(1 for v in HIST_DRV.get(c, {}).values() if "DIRECT" in v),
            "primary_mechanism": primary_of(c)[0],
            "evidence_sequence": [e.get("event_type") for e in evs],
            "evidence_dates": [e.get("date") for e in evs],
            "event_profile": [{"event_id": e["event_id"], "date": e["date"],
                               "event_type": e.get("event_type")} for e in evs],
            "n_events": len(evs),
        })
HIST_BY_ID = {h["cycle_id"]: h for h in HIST}
KIND_BY_ID = {h["cycle_id"]: h["historical_object_kind"] for h in HIST}


def comparison_point(h, phase):
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


# ---------------------------------------------------------------- candidate profile（CANDS）
CANDS = []
for c in cur["candidates"]:
    cid = c["candidate_id"]
    ev = c.get("evidence") or []
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
        "candidate_id": cid, "macro_theme": c.get("macro_theme"), "industry": c.get("macro_theme"),
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
            (["candidate_side_2026_market_state_not_available"] if proxy["status"] != "MATCH" else []) +
            (["phase_window_end_unknown"] if not end else []) +
            (["evidence_sequence_partial"] if seq_partial else []) +
            (["no_event_entity"] if not cev else [])),
    })
CAND_BY_ID = {c["candidate_id"]: c for c in CANDS}


# ---------------------------------------------------------------- 冻结规则实现（= Rule Set v0.2）
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
    """★ Rule Set **v0.3** §1 R1–R4 —— 与 `build_structural_analogy_rule_calibration_v0_3.py::level_v3()` 逐条一致。

    ★ 与 v0.2 实现的**唯一差别**：`STRUCTURAL_PARTIAL` 以 `Driver ∈ {MATCH, PARTIAL}` 为**硬前提**，
      **移除** v0.2 末段 fallback `if n_support >= 2: return "STRUCTURAL_PARTIAL"`
      （该 fallback 会放行 `driver = MISMATCH` → E.1 缺陷）。
    """
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
    if d_dr in DRIVER_GOOD and d_sq in GOOD and n_support >= 2:
        return "STRUCTURAL_PARTIAL", False
    # R4 —— 结构支持不足 → 按 Theme Relation 事后派生
    return ("THEME_ONLY" if theme_rel == "SAME_MACRO_THEME" else "NO_VALID_CORRESPONDENCE"), False


# ---------------------------------------------------------------- 执行
def run(theme_blind=False):
    rows = []
    for cp in CANDS:
        cid = cp["candidate_id"]
        for h in HIST:
            cyc = h["cycle_id"]
            cpt = comparison_point(h, cp["current_phase"])
            d_lc = cpt["status"]
            d_dr, dr_meta = driver_rule(cp["driver_profile"]["canonical_drivers"],
                                        h["canonical_drivers"], cyc)
            cs_seq, hs_seq = cp["evidence_sequence"], h["evidence_sequence"]
            if len(cs_seq) < 2 or len(hs_seq) < 2:
                d_sq, sub = "NOT_AVAILABLE", "NOT_AVAILABLE"
            else:
                n = lcs(cs_seq, hs_seq)
                ov = len(set(cs_seq) & set(hs_seq))
                if n >= 2 and cs_seq[0] == hs_seq[0]:
                    d_sq, sub = "MATCH", "SEQUENCE_MATCH"
                elif n >= 2:
                    d_sq, sub = "PARTIAL", "SEQUENCE_PARTIAL"
                elif n == 1 and ov >= 2:
                    d_sq, sub = "PARTIAL", "SET_ONLY"
                else:
                    d_sq, sub = "MISMATCH", "SEQUENCE_MISMATCH"
            d_ev, ev_meta = event_rule(sorted({e["event_type"] for e in cp["event_profile"]}), hs_seq)
            same_theme = (h["macro_theme"] == cp["macro_theme"]) and h["macro_theme"] is not None
            tr = "CROSS_MACRO_THEME" if (theme_blind or not same_theme) else "SAME_MACRO_THEME"
            lvl, strict = level_rule(d_lc, d_dr, d_sq, d_ev, sub,
                                     h["driver_direct_count"] > 0, tr, dr_meta["quality"])
            reasons = []
            if d_lc in GOOD:
                reasons.append(f"Lifecycle={d_lc}（{cpt['basis']}）")
            if d_dr in GOOD:
                reasons.append(f"Driver={d_dr}/{dr_meta['quality']}（交集 {dr_meta['overlap']}）")
            if d_sq in GOOD:
                reasons.append(f"EvidenceSequence={d_sq}/{sub}")
            if d_ev in GOOD:
                reasons.append(f"EventStructure={d_ev}/{ev_meta['quality']}")
            mismatch = [k for k, v in (("lifecycle", d_lc), ("driver", d_dr),
                                       ("evidence_sequence", d_sq), ("event_structure", d_ev))
                        if v == "MISMATCH"]
            unknown = [k for k, v in (("lifecycle", d_lc), ("driver", d_dr),
                                      ("evidence_sequence", d_sq), ("event_structure", d_ev))
                       if v in ("UNKNOWN", "NOT_AVAILABLE")]
            g = GOV.get(cyc)
            rows.append({
                "candidate_id": cid, "historical_cycle": cyc,
                "historical_kind": h["historical_object_kind"],   # ★ v0.4：按来源数组判定
                "historical_object_kind": h["historical_object_kind"],
                "historical_campaign_id": h["campaign_id"],
                "historical_research_candidate_id": h["research_candidate_id"],
                "historical_cycle_id": h["cycle_id"],
                "historical_macro_theme": h["macro_theme"],
                "theme_relation": tr,
                "lifecycle": d_lc, "historical_stage_at_comparable_point": cpt["stage"],
                "driver": d_dr, "driver_quality": dr_meta["quality"], "driver_overlap": dr_meta["overlap"],
                "historical_primary_mechanism": h["primary_mechanism"],
                "evidence_sequence": d_sq, "sequence_subtype": sub,
                "event_structure": d_ev, "event_quality": ev_meta["quality"],
                "structural_status": lvl, "strict_structural_supported": strict,
                "structural_reasons": reasons, "mismatch_dimensions": mismatch,
                "unknown_dimensions": unknown,
                # ---- governance-gates-v0.1（**仅 supplementary context**，不参与 Structural Status）----
                "supplementary": {
                    "market_structure": "SUPPLEMENTARY_ONLY",
                    "temporal_structure": "SUPPLEMENTARY_ONLY",
                    "governance_gates": {
                        "ruleset": "governance-gates-v0.1",
                        "market_evidence_state": (g or {}).get("market_evidence_state"),
                        "beta_level": (g or {}).get("beta_level"),
                        "peak_state": ((g or {}).get("peak") or {}).get("state"),
                        "end_state": ((g or {}).get("end") or {}).get("state"),
                        "result": (g or {}).get("result"),
                        "note": ("governance 元数据 **不参与** Structural Status 判定"
                                 "（Rule Set v0.2 §12）；beta_level=1 **不等于** Alpha；"
                                 "market_evidence_state=A_SHARE_MARKET **不等于**独立 Campaign；"
                                 "result=weak = 方向为负，**不降低**参与结构类比的资格"),
                    },
                },
            })
    return rows


V3 = run()
TB = run(theme_blind=True)


def counts(rows):
    c = collections.Counter(r["structural_status"] for r in rows)
    return {"strict": sum(1 for r in rows if r["strict_structural_supported"]),
            **{k: c[k] for k in LEVELS}}


C3 = counts(V3)
cross = [r for r in V3 if r["theme_relation"] == "CROSS_MACRO_THEME"]
same = [r for r in V3 if r["theme_relation"] == "SAME_MACRO_THEME"]

# ---------------------------------------------------------------- 回归控制
# ★ Rule Set §10 的**负控制**只有 2 个（必须**保持非结构状态**）；
#   另 2 个是 v0.1→v0.2 的**正向修正案例**（v0.2 时已是 STRUCTURAL_PARTIAL），
#   其正确预期是「与 v0.2 一致」，而不是「不得为结构状态」。
NEGATIVE_CONTROLS = [("CC-2026-EMBODIED-AI", "C-2024-ROBOTAXI", "name-similarity negative control"),
                     ("CC-2026-OPTICAL-LINK", "C-2019-COMM-5G", "same-theme negative control")]
EXPECTED_CHANGE_CASES = [("CC-2026-BCI-MEDTECH", "C-2019-PHARMA-INNOV",
                          "v0.1→v0.2 正向修正案例（v0.2 起为 STRUCTURAL_PARTIAL）"),
                         ("CC-2026-OFFSHORE-WIND", "C-2020-POWER-NE",
                          "v0.1→v0.2 theme-decoupling 修正案例（v0.2 起为 STRUCTURAL_PARTIAL）")]
RMAP = {(r["candidate_id"], r["historical_cycle"]): r for r in V3}
TMAP = {(r["candidate_id"], r["historical_cycle"]): r for r in TB}
neg = []
for cid, cyc, kind in NEGATIVE_CONTROLS:
    r = RMAP.get((cid, cyc))
    if not r:
        continue
    t = TMAP[(cid, cyc)]
    neg.append({"case": kind, "candidate_id": cid, "historical_cycle": cyc,
                "theme_relation": r["theme_relation"], "v0_3": r["structural_status"],
                "theme_blind": t["structural_status"], "driver": r["driver"],
                "event_structure": r["event_structure"],
                "not_upgraded": r["structural_status"] in ("NO_VALID_CORRESPONDENCE", "THEME_ONLY")})
exp_cases = []
for cid, cyc, kind in EXPECTED_CHANGE_CASES:
    r = RMAP.get((cid, cyc))
    if not r:
        continue
    exp_cases.append({"case": kind, "candidate_id": cid, "historical_cycle": cyc,
                      "theme_relation": r["theme_relation"], "v0_3": r["structural_status"],
                      "driver": r["driver"], "event_structure": r["event_structure"]})

# ---- ★ 最强非回归控制：v0.2 已覆盖的 17 个历史 cycle，其 v0.3 状态必须与 v0.2 完全一致 ----
V2P = f"{REP}/structural_analogy_research_v0_3.json"
NONREG = {"available": os.path.exists(V2P), "checked_pairs": 0, "changed": [], "identical": True,
          "note": "v0.3 与 v0.2 使用**同一冻结规则实现**；对 v0.2 已覆盖的 17 个历史 cycle，"
                  "结构状态与 strict 标记必须逐条一致（唯一差异来源 = 新增 62 个 cycle）。"}
if NONREG["available"]:
    _v2 = json.load(io.open(V2P, encoding="utf-8"))
    _m2 = {(m["candidate_id"], m["historical_cycle"]): m for m in _v2["matrix"]}
    for (cid, cyc), m2 in _m2.items():
        r = RMAP.get((cid, cyc))
        if not r:
            continue
        NONREG["checked_pairs"] += 1
        if (m2["structural_status"] != r["structural_status"]
                or bool(m2["strict_structural_supported"]) != bool(r["strict_structural_supported"])):
            NONREG["changed"].append({
                "candidate_id": cid, "historical_cycle": cyc,
                "v0_2": m2["structural_status"], "v0_3": r["structural_status"]})
    NONREG["identical"] = not NONREG["changed"]

STRUCT_CHANGED = sum(1 for a, b in zip(V3, TB)
                     if a["structural_status"] != b["structural_status"]
                     and a["structural_status"].startswith("STRUCTURAL"))
THEME_BLIND = {"retained": sum(1 for a, b in zip(V3, TB) if a["structural_status"] == b["structural_status"]),
               "changed": sum(1 for a, b in zip(V3, TB) if a["structural_status"] != b["structural_status"]),
               "structural_status_changed": STRUCT_CHANGED,
               "theme_relation_changed": sum(1 for a, b in zip(V3, TB)
                                             if a["theme_relation"] != b["theme_relation"]),
               "note": "正确预期：Theme-Blind **不改变 Structural Status**，只影响 theme_relation。"}

# ---------------------------------------------------------------- 机制型 Analog 分类（v0.3 新增）
MECH_GROUPS = collections.defaultdict(list)
for r in V3:
    if r["structural_status"] not in ("STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL"):
        continue
    for m in r["driver_overlap"]:
        MECH_GROUPS[m].append({
            "candidate_id": r["candidate_id"], "historical_cycle": r["historical_cycle"],
            "theme_relation": r["theme_relation"], "structural_status": r["structural_status"],
            "historical_primary_mechanism": r["historical_primary_mechanism"],
            "is_historical_primary": r["historical_primary_mechanism"] == m,
            "historical_macro_theme": r["historical_macro_theme"],
        })
mechanism_analogs = []
for m in sorted(MECH_GROUPS):
    items = MECH_GROUPS[m]
    cross_items = [x for x in items if x["theme_relation"] == "CROSS_MACRO_THEME"]
    mechanism_analogs.append({
        "mechanism": m,
        "n_correspondences": len(items),
        "n_cross_macro_theme": len(cross_items),
        "cross_macro_theme_examples": sorted(
            {x["historical_cycle"] for x in cross_items})[:20],
        "note": ("同机制交集 **不等于** 结构对应 —— 本组仅列出已同时通过 "
                 "Rule Set v0.2 §7/§8 的 STRUCTURAL_SUPPORTED / STRUCTURAL_PARTIAL 组合；"
                 "`is_historical_primary` 标记该机制是否为该历史 cycle 的 primary mechanism。"),
    })

# ---------------------------------------------------------------- 跨族 analog（核心价值）
cross_analogs = [r for r in V3
                 if r["theme_relation"] == "CROSS_MACRO_THEME"
                 and r["structural_status"] in ("STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL")]

# ---------------------------------------------------------------- 逐候选分组
per_cand = []
for cp in CANDS:
    cid = cp["candidate_id"]
    rows = [r for r in V3 if r["candidate_id"] == cid]
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
             "driver_quality": r["driver_quality"], "event_quality": r["event_quality"],
             "historical_macro_theme": r["historical_macro_theme"],
             "historical_primary_mechanism": r["historical_primary_mechanism"]} for r in corr],
        "non_correspondence_set": [
            {"historical_cycle": r["historical_cycle"], "status": r["structural_status"],
             "mismatch_dimensions": r["mismatch_dimensions"]} for r in nonc],
        "theme_relations": dict(collections.Counter(r["theme_relation"] for r in rows)),
        "counts": dict(collections.Counter(r["structural_status"] for r in rows)),
    })

# ---------------------------------------------------------------- Evidence Cards
cards = []
for r in V3:
    if r["structural_status"] not in ("STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL"):
        continue
    cp = CAND_BY_ID[r["candidate_id"]]
    h = HIST_BY_ID[r["historical_cycle"]]
    g = (r["supplementary"] or {}).get("governance_gates") or {}
    negl = []
    if r["driver"] == "MISMATCH":
        negl.append("driver mismatch")
    if r["lifecycle"] == "MISMATCH":
        negl.append("lifecycle mismatch")
    if r["evidence_sequence"] == "MISMATCH":
        negl.append("evidence sequence mismatch")
    if r["event_structure"] == "MISMATCH":
        negl.append("event structure mismatch")
    if r["sequence_subtype"] == "SET_ONLY":
        negl.append("sequence is SET_ONLY（无法证明顺序）")
    if r["historical_cycle"] not in {h2["cycle_id"] for h2 in HIST if h2["driver_direct_count"] > 0}:
        negl.append("历史侧无 DIRECT driver 证据")
    if r["unknown_dimensions"]:
        negl.append(f"{len(r['unknown_dimensions'])} 个维度 NOT_AVAILABLE")
    if r["theme_relation"] == "CROSS_MACRO_THEME":
        negl.append("跨族：无同主题上下文支撑")
    cards.append({
        "candidate_id": r["candidate_id"], "historical_cycle": r["historical_cycle"],
        "status": r["structural_status"], "strict_supported": r["strict_structural_supported"],
        "lifecycle": {"status": r["lifecycle"],
                      "comparison_point": RMAP[(r["candidate_id"], r["historical_cycle"])]
                      and comparison_point(HIST_BY_ID[r["historical_cycle"]], cp["current_phase"])},
        "driver": {"status": r["driver"], "overlap": r["driver_overlap"],
                   "candidate_drivers": cp["driver_profile"]["canonical_drivers"],
                   "historical_drivers": h["canonical_drivers"],
                   "historical_provenance": h["driver_provenance"],
                   "historical_primary_mechanism": h["primary_mechanism"]},
        "evidence_sequence": {"status": r["evidence_sequence"], "subtype": r["sequence_subtype"],
                              "candidate_sequence": cp["evidence_sequence"],
                              "historical_sequence": h["evidence_sequence"]},
        "event_structure": {"status": r["event_structure"], "overlap": r["event_quality"] and None or None,
                            "candidate_event_types": sorted({e["event_type"] for e in cp["event_profile"]}),
                            "historical_event_types": sorted(set(h["evidence_sequence"]))},
        "governance_context": {
            "market_evidence_state": g.get("market_evidence_state"),
            "beta_level": g.get("beta_level"),
            "peak_state": g.get("peak_state"), "end_state": g.get("end_state"),
            "result": g.get("result"),
            "note": "**supplementary only** —— 不参与 Structural Status。",
        },
        "why_considered": (f"Lifecycle={r['lifecycle']}；Driver={r['driver']}"
                           f"（交集 {r['driver_overlap']}）；"
                           f"EvidenceSequence={r['evidence_sequence']}（{r['sequence_subtype']}）；"
                           f"EventStructure={r['event_structure']} → "
                           f"{sum(1 for v in (r['lifecycle'], r['driver'], r['evidence_sequence'], r['event_structure']) if v in GOOD)}/4 维度有真实对应"),
        "why_not_strong_analogy": ("；".join(negl) if negl else
                                   "无显著负证据，但仍受历史驱动证据粒度与事件覆盖限制"),
    })

res = {
    "artifact": "structural_analogy_research", "artifact_version": "0.4",
    "generated_by": "research/scripts/build_structural_analogy_research_v0_4.py",
    "position": ("Research-only Structural Analogy Engine —— **不进入** Product / src / DB / schema / "
                 "export / contracts。**不是**投资建议、预测、交易信号、相似度评分或排名。"),
    "not_a": ["product UI", "user recommendation", "investment advice", "prediction",
              "trading signal", "similarity score", "weighted score", "confidence score",
              "ranking", "best historical analogue", "winner"],
    "protocol": {
        "rule_set": RULE_SET, "protocol_version": RULE_VER, "protocol_document": RULE_DOC,
        "effective_date": "2026-09-22",
        "source_calibration_artifact": "research/research/reports/structural_analogy_rule_calibration_v0_3.json",
        "frozen": True,
        "authoritative_implementation": "build_structural_analogy_rule_calibration_v0_3.py::level_v3()",
        "rule_implementation_parity": "与 build_structural_analogy_rule_calibration_v0_3.py::level_v3() 逐条一致",
        "changed_vs_v0_3": ("**规则未变**（仍为 Rule Set v0.3）；变化 = ① 消费 Driver Canonicalization v0.4"
                            "（含剩余 5 项 collision 处理）② 修正 historical object identity（campaign / research_candidate）"),
        "driver_canonicalization_version": "0.4",
    },
    "inputs": {
        "current_candidates": "research/current/current_candidates.json",
        "export": "exports/timeline_export_v1.json",
        "driver_canonicalization": "research/research/reports/historical_driver_canonicalization_v0_4.json",
        "driver_ledger": "research/research/reports/historical_driver_evidence_ledger_v0_4.json",
        "governance_classification": "research/research/reports/governance_classification_v0_1.json",
        "governance_ruleset": "governance-gates-v0.1",
        "governance_usage": ("market_evidence_state / beta_level / peak|end 四态 **只进入 supplementary**；"
                             "**不参与 Structural Status**（Rule Set v0.2 §12）"),
    },
    "snapshot": {"current_candidates_snapshot": SNAPSHOT,
                 "export_version": exp.get("timeline_export_version"),
                 "export_source_commit": exp.get("source_commit")},
    "universe": {
        "historical_cycles": len(HIST),
        "campaigns": sum(1 for h in HIST if h["historical_object_kind"] == "campaign"),
        "research_candidates": sum(1 for h in HIST if h["historical_object_kind"] == "research_candidate"),
        "current_candidates": len(CANDS),
        "pairs": len(V3),
        "macro_theme_roots_covered": sorted({h["macro_theme"] for h in HIST if h["macro_theme"]}),
        "v0_3_universe_cycles": 79,
        "added_by_r01": len(HIST) - 17,
    },
    "dimension_vocabulary": ["MATCH", "PARTIAL", "MISMATCH", "UNKNOWN", "NOT_AVAILABLE"],
    "correspondence_levels": LEVELS,
    "excluded_dimensions": {
        "market_structure": {"status": "SUPPLEMENTARY_ONLY", "reason": "PARTIALLY_RESOLVED（候选侧 2026 行情不可得，单向）"},
        "temporal_structure": {"status": "SUPPLEMENTARY_ONLY", "reason": "candidate-side one-way"},
        "governance_gates": {"status": "SUPPLEMENTARY_ONLY",
                             "reason": "governance-gates-v0.1 元数据不参与 Structural Status（Rule Set v0.2 §12）"},
        "rule": "**不参与 v0.2 成立判据**",
    },
    "candidate_profiles": CANDS, "historical_profiles": HIST, "matrix": V3,
    "summary": {
        "current_candidates": len(CANDS),
        "historical_cycles_examined": len(HIST),
        "pairs": len(V3),
        "by_status": {k: C3[k] for k in LEVELS},
        "strict_structural_supported": C3["strict"],
        "by_status_cross_family": {k: sum(1 for m in cross if m["structural_status"] == k) for k in LEVELS},
        "by_status_same_family": {k: sum(1 for m in same if m["structural_status"] == k) for k in LEVELS},
    },
    "mechanism_analogs": mechanism_analogs,
    "cross_macro_theme_analogs": cross_analogs,
    "per_candidate": per_cand,
    "regression_controls": {
        "name_blind": {"retained": len(V3), "changed": 0,
                       "note": "Rule Set v0.2 的四个正式维度**不读取任何名称字段**；名称仅用于展示。"},
        "theme_blind": THEME_BLIND,
        "negative_controls": neg,
        "expected_change_cases": exp_cases,
        "non_regression_vs_v0_2": NONREG,
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
    w.writerow(["candidate_id", "historical_cycle", "historical_kind", "historical_macro_theme",
                "theme_relation", "comparison_point_stage", "lifecycle", "driver", "driver_quality",
                "driver_overlap", "evidence_sequence", "sequence_subtype", "event_structure",
                "structural_status", "strict_supported",
                "market_evidence_state", "beta_level", "peak_state", "end_state", "result"])
    for m in V3:
        g = m["supplementary"]["governance_gates"]
        w.writerow([m["candidate_id"], m["historical_cycle"], m["historical_kind"],
                    m["historical_macro_theme"], m["theme_relation"],
                    m["historical_stage_at_comparable_point"], m["lifecycle"], m["driver"],
                    m["driver_quality"], "|".join(m["driver_overlap"]), m["evidence_sequence"],
                    m["sequence_subtype"], m["event_structure"], m["structural_status"],
                    m["strict_structural_supported"],
                    g.get("market_evidence_state"), g.get("beta_level"),
                    g.get("peak_state"), g.get("end_state"), g.get("result")])
print("written", OUT_CSV)
print()
print("candidates:", len(CANDS), "| historical cycles:", len(HIST), "| pairs:", len(V3))
print("by_status:", {k: C3[k] for k in LEVELS})
print("STRICT_STRUCTURAL_SUPPORTED:", C3["strict"])
print("cross-family:", {k: sum(1 for m in cross if m["structural_status"] == k) for k in LEVELS})
print("same-family:", {k: sum(1 for m in same if m["structural_status"] == k) for k in LEVELS})
print("cross-macro-theme analogs:", len(cross_analogs))
print("negative controls not upgraded:", all(n["not_upgraded"] for n in neg))
print("non-regression vs v0.2: checked=%d identical=%s changed=%d"
      % (NONREG["checked_pairs"], NONREG["identical"], len(NONREG["changed"])))
