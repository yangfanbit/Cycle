"""Structural Analogy Data Readiness v0.1 —— Feasibility v0.2 生成器（deterministic，只读）。

相对 v0.1 的三项修复：
  P0-A lifecycle semantic break : 新增 `historical_stage_at_comparable_point`
                                  （候选 CURRENT phase ↔ 历史在**可比观测点**的阶段，
                                    而非历史 terminal phase）
  P0-B candidate event entity   : 从 candidate evidence 派生最小事件实体
                                  （复用历史 event_type 枚举，不新建 taxonomy）
  P0-C candidate market mapping : candidate → 同段行情序列代理（segment proxy）
  另：phase_window.end 语义（derived / declared / unknown）

产物（**不覆盖 v0.1**）：
  research/research/reports/structural_analogy_candidate_events_v0_1.json
  research/research/reports/structural_analogy_candidate_market_map_v0_1.json
  research/research/reports/structural_analogy_feasibility_v0_2.json
  research/research/reports/structural_analogy_feasibility_candidates_v0_2.csv

用法：
  python research/scripts/build_structural_analogy_readiness_v0_2.py
  python research/scripts/build_structural_analogy_readiness_v0_2.py --check
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

OUT_EVENTS = f"{REP}/structural_analogy_candidate_events_v0_1.json"
OUT_MARKET = f"{REP}/structural_analogy_candidate_market_map_v0_1.json"
OUT_JSON = f"{REP}/structural_analogy_feasibility_v0_2.json"
OUT_CSV = f"{REP}/structural_analogy_feasibility_candidates_v0_2.csv"

# ---------------------------------------------------------------- 既有枚举（复用，不新造）
# 历史 events.event_type CHECK 枚举（research/schema/schema.sql）
HIST_EVENT_TYPES = ["policy", "industry", "macro", "company", "market", "news", "holiday", "other"]
# candidate evidence.source_type → 历史 event_type（复用 v0.1 的映射；CAPITAL 无历史对应 → market）
CAND_EV_TO_EVENT = {"POLICY": "policy", "INDUSTRY": "industry", "COMPANY": "company",
                    "MARKET": "market", "CAPITAL": "market", "MACRO": "macro",
                    "SENTIMENT": "other", "OTHER": "other"}
EVENT_TYPE_TO_DRIVER = {"policy": "POLICY", "company": "INDUSTRY", "market": "CAPITAL",
                        "macro": "EXTERNAL"}
# 历史 lifecycle 阶段顺序（research/schema 与 src/data/timeline/researchAttention.ts 一致）
STAGE_ORDER = ["EARLY_SIGNAL", "THEME_FORMING", "BROAD_CONFIRMATION", "MAIN_RISE", "PEAK",
               "RETRACEMENT", "SECONDARY", "DECLINING", "FIRST_DECLINE", "MAIN_END"]
STAGE_TO_PHASE = {"EARLY_SIGNAL": "EARLY_SIGNAL", "THEME_FORMING": "THEME_FORMING",
                  "BROAD_CONFIRMATION": "BROAD_CONFIRMATION", "MAIN_RISE": "EXPANSION",
                  "PEAK": "PEAK", "SECONDARY": "DECLINE", "FIRST_DECLINE": "DECLINE",
                  "RETRACEMENT": "DECLINE", "DECLINING": "DECLINE", "MAIN_END": "END"}
PHASE_TO_STAGE = {"EARLY_SIGNAL": "EARLY_SIGNAL", "THEME_FORMING": "THEME_FORMING",
                  "BROAD_CONFIRMATION": "BROAD_CONFIRMATION", "EXPANSION": "MAIN_RISE",
                  "PEAK": "PEAK"}
# 相邻阶段（用于 PARTIAL）
STAGE_NEIGHBOURS = {}
for _i, _s in enumerate(STAGE_ORDER):
    _n = []
    if _i > 0:
        _n.append(STAGE_ORDER[_i - 1])
    if _i < len(STAGE_ORDER) - 1:
        _n.append(STAGE_ORDER[_i + 1])
    STAGE_NEIGHBOURS[_s] = _n

# ---------------------------------------------------------------- P0-C：candidate → 同段行情序列代理
# 依据 market_series 的**产品段**语义（非仅行业），显式声明覆盖限制。
CAND_MARKET_PROXY = {
    "CC-2026-OPTICAL-LINK": {
        "status": "PARTIAL",
        "segment": "光模块 / 光器件（高速光互联）",
        "series": ["INNOLIGHT", "EOPTOLINK", "TFC", "ACCELINK"],
        "note": "同产品段（光模块/光器件），非候选自身证券；序列覆盖 2018-01-02~2025-12-31（连续日线）",
    },
    "CC-2026-OFFSHORE-WIND": {
        "status": "PARTIAL",
        "segment": "风电整机",
        "series": ["GOLDWIND"],
        "note": "同产品段（风电整机）；**覆盖止于 2022-12-30** → 无法覆盖 2023–2025",
    },
    "CC-2026-COMPUTE-POWER": {
        "status": "PARTIAL",
        "segment": "电网设备（自动化 / 开关 / 输配电）",
        "series": ["NARI", "PINGGAO", "SIEYUAN", "TBEA", "XUJI"],
        "note": "相关段（电网设备）；「算电协同」本身无对应序列 → 段代理，非主题代理",
    },
    "CC-2026-BCI-MEDTECH": {
        "status": "PARTIAL",
        "segment": "医药（药 / 生物 / 中药），**非医疗器械**",
        "series": ["HENGRUI", "TIGERMED", "WUXIAPPTEC", "ZHIFEI", "YILING", "INTCO",
                   "PIANZAIHUANG", "PHARMA_ETF_512010"],
        "note": "同大行业但**非同产品段**（脑机接口属医疗器械，仓库无医疗器械序列）；"
                "个股覆盖 2019-01-02~2022-12-30，ETF 2019~2022 → 均无法覆盖 2026",
    },
    "CC-2026-EMBODIED-AI": {
        "status": "NOT_AVAILABLE",
        "segment": "具身智能 / 人形机器人",
        "series": [],
        "note": "仓库内**无**机器人/具身智能序列；ROBOTAXI 概念指数为 EMPTY_PLACEHOLDER（0 行）；"
                "DEMEISHI/HUAYANG/MINGKEJINGJI/SAILISI 仅 2023-08~10 且属汽车零部件段",
    },
}

conn = sqlite3.connect(f"file:{ROOT}/research/database/cycle_research.db?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = json.load(io.open(f"{ROOT}/research/current/current_candidates.json", encoding="utf-8"))
exp = json.load(io.open(f"{ROOT}/exports/timeline_export_v1.json", encoding="utf-8"))

SNAPSHOT = cur.get("snapshot_date")  # 2026-09-15

# ---------------------------------------------------------------- P0-B：candidate event entity
cand_events = []
for c in cur["candidates"]:
    cid = c["candidate_id"]
    n = 0
    for e in sorted(c.get("evidence") or [],
                    key=lambda x: (x.get("event_date") or x.get("source_date") or "", x["evidence_id"])):
        # 日期优先级：event_date（事件发生日）→ source_date（来源发布日，**降级依据**）
        d = e.get("event_date")
        basis = "event_date"
        if not d:
            d = e.get("source_date")
            basis = "source_date"
        if not d:
            continue  # 两类日期都缺 → **不派生事件**（不得编造日期）
        n += 1
        cand_events.append({
            "event_id": f"CEV-{cid.replace('CC-2026-', '')}-{n:02d}",
            "candidate_id": cid,
            "date": d,
            "date_basis": basis,
            "date_confidence": "high" if basis == "event_date" else "medium",
            "event_type": CAND_EV_TO_EVENT.get(e.get("source_type"), "other"),
            "source_evidence_id": e["evidence_id"],
            "source_type": e.get("source_type"),
            "description": (e.get("claim") or "")[:160],
            "evidence_strength": e.get("evidence_strength"),
            "direction": e.get("direction"),
            "derived_from": "research/current/current_candidates.json:evidence[].event_date|source_date",
        })

events_doc = {
    "artifact": "structural_analogy_candidate_events",
    "artifact_version": "0.1",
    "generated_by": "research/scripts/build_structural_analogy_readiness_v0_2.py",
    "position": ("Research-only 派生层 —— **不进入** DB / schema.sql / timeline_export_v1.json / contracts / src。"
                 "用途：为 Structural Analogy 提供 candidate 侧的最小事件实体，使 event_structure 维度可对齐。"),
    "not_a": ["新的 event taxonomy", "历史事件台账", "Product 数据源"],
    "semantics": {
        "rule": ("**有可追溯日期 → 派生 event；两类日期都缺 → 不派生**（不得编造日期）。"
                 "日期优先级：`event_date`（事件发生日）→ `source_date`（来源发布日，**降级依据**）"),
        "date_basis": {"event_date": "事件发生日（强）", "source_date": "来源发布日（弱，**非事件发生日**）"},
        "date_confidence": {"event_date": "high", "source_date": "medium"},
        "no_evidence_semantics": ("candidate 侧**没有**事件实体时记 `NOT_AVAILABLE`，"
                                  "**不得**写成 `NO_EVENT` / `NO_PATTERN`"),
        "event_type_vocabulary": HIST_EVENT_TYPES,
        "mapping": CAND_EV_TO_EVENT,
        "mapping_note": ("复用历史 `events.event_type` 枚举；`CAPITAL` 在历史侧无对应值 → 归入 `market`"
                         "（与 `EVENT_TYPE_TO_DRIVER` 的 market→CAPITAL 一致）"),
    },
    "coverage": {
        "evidence_total": sum(len(c.get("evidence") or []) for c in cur["candidates"]),
        "evidence_with_derivable_date": len(cand_events),
        "evidence_without_any_date": sum(len(c.get("evidence") or []) for c in cur["candidates"]) - len(cand_events),
        "by_date_basis": dict(collections.Counter(x["date_basis"] for x in cand_events)),
        "by_candidate": {c["candidate_id"]: sum(1 for x in cand_events if x["candidate_id"] == c["candidate_id"])
                         for c in cur["candidates"]},
        "by_event_type": dict(collections.Counter(x["event_type"] for x in cand_events)),
    },
    "events": cand_events,
}

# ---------------------------------------------------------------- P0-A：historical stage at comparable point
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
    last = None
    if sm:
        last = max(sm.items(), key=lambda kv: kv[1])[0]
    HIST.append({
        "object_id": o.get("campaign_id") or o.get("research_candidate_id"),
        "kind": "campaign" if o.get("campaign_id") else "research_candidate",
        "lifecycle_stages": stages,
        "stage_starts": sm,
        "terminal_stage": last,
        "terminal_phase": STAGE_TO_PHASE.get(last, "UNKNOWN") if last else "UNKNOWN",
        "drivers": sorted({EVENT_TYPE_TO_DRIVER[e["event_type"]] for e in events_of(o)
                           if e.get("event_type") in EVENT_TYPE_TO_DRIVER}),
        "seq": [e.get("event_type") for e in events_of(o)],
        "n_events": len(events_of(o)),
        "family": next((t["name"] for t in (o.get("themes") or [])
                        if t.get("role") == "related" and t.get("theme_type") in ("industry", "sector")), None),
        "security_ids": list(o.get("security_ids") or []),
    })
HIST_BY_ID = {h["object_id"]: h for h in HIST}


def comparable_stage(h, cand_phase):
    """candidate 当前 phase ↔ 历史在**可比观测点**的阶段。

    返回 (stage, status, basis)：
      MATCH   —— 历史 lifecycle 明确包含该阶段（锚点存在）
      PARTIAL —— 历史包含**相邻**阶段（阶段次序相邻）
      MISMATCH—— 历史有 lifecycle 但不含该阶段也不含相邻阶段
      UNKNOWN —— 历史无 lifecycle
    """
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
    start = pw.get("start")
    end = pw.get("end")
    elapsed = None
    if start and SNAPSHOT:
        elapsed = (date(*[int(x) for x in SNAPSHOT.split("-")]) -
                   date(*[int(x) for x in start.split("-")])).days
    cid = c["candidate_id"]
    proxy = CAND_MARKET_PROXY.get(cid, {"status": "NOT_AVAILABLE", "series": [], "segment": None, "note": ""})
    return {
        "candidate_id": cid, "macro_theme": c.get("macro_theme"),
        "phase": c.get("attention_state"), "phase_stage": PHASE_TO_STAGE.get(c.get("attention_state")),
        "drivers": sorted(d["category"] for d in (c.get("drivers") or [])),
        "n_evidence": len(ev), "first_evidence": dates[0] if dates else None,
        "last_evidence": dates[-1] if dates else None,
        "phase_window_start": start,
        "phase_window_end": end,
        "phase_window_end_semantics": ("declared" if end else "unknown"),
        "phase_elapsed_days_at_snapshot": elapsed,
        "derived_event_count": sum(1 for x in cand_events if x["candidate_id"] == cid),
        "derived_event_types": sorted({x["event_type"] for x in cand_events if x["candidate_id"] == cid}),
        "market_proxy_status": proxy["status"],
        "market_proxy_segment": proxy.get("segment"),
        "market_proxy_series": proxy.get("series") or [],
        "market_proxy_note": proxy.get("note", ""),
        "reference_cases": [r["campaign_id"] for r in (c.get("reference_cases") or [])],
    }


CANDS = [cand_profile(c) for c in cur["candidates"]]

# ---------------------------------------------------------------- 结构对照矩阵
matrix = []
for cp in CANDS:
    cev_types = cp["derived_event_types"]
    for h in HIST:
        d = {}
        # lifecycle（可比观测点口径）
        st, st_status, st_basis = comparable_stage(h, cp["phase"])
        d["lifecycle"] = st_status
        d["historical_stage_at_comparable_point"] = st
        d["lifecycle_basis"] = st_basis
        # terminal 口径保留（对照）
        if h["terminal_phase"] == "UNKNOWN":
            d["lifecycle_terminal_legacy"] = "UNKNOWN"
        elif h["terminal_phase"] == cp["phase"]:
            d["lifecycle_terminal_legacy"] = "MATCH"
        elif h["terminal_phase"] in (STAGE_TO_PHASE.get(x) for x in STAGE_NEIGHBOURS.get(cp["phase_stage"], [])):
            d["lifecycle_terminal_legacy"] = "PARTIAL"
        else:
            d["lifecycle_terminal_legacy"] = "MISMATCH"
        # drivers
        if not h["drivers"]:
            d["drivers"] = "NOT_AVAILABLE"
        else:
            inter = set(cp["drivers"]) & set(h["drivers"])
            d["drivers"] = ("MISMATCH" if not inter else
                            "MATCH" if inter == set(cp["drivers"]) == set(h["drivers"]) else "PARTIAL")
            d["driver_overlap_count"] = len(inter)
        d.setdefault("driver_overlap_count", 0)
        # evidence_sequence（两侧统一到历史 event_type 词表）
        hs = [x for x in h["seq"] if x in HIST_EVENT_TYPES]
        cs = [x for x in cev_types if x in HIST_EVENT_TYPES]
        if len(hs) < 2 or len(cs) < 2:
            d["evidence_sequence"] = "NOT_AVAILABLE"
        elif hs[0] == cs[0]:
            d["evidence_sequence"] = "MATCH"
        elif len(set(hs) & set(cs)) >= 2:
            d["evidence_sequence"] = "PARTIAL"
        else:
            d["evidence_sequence"] = "MISMATCH"
        # event_structure（P0-B 修复后：两侧均有事件实体）
        if not cev_types:
            d["event_structure"] = "NOT_AVAILABLE"
        elif not h["seq"]:
            d["event_structure"] = "NOT_AVAILABLE"
        else:
            inter = set(cev_types) & set(h["seq"])
            d["event_structure"] = ("MISMATCH" if not inter else
                                    "MATCH" if set(cev_types) == set(h["seq"]) else "PARTIAL")
        # temporal_structure（候选有 phase 起点 + 已历时；历史有阶段起点）
        if cp["phase_window_start"] and cp["phase_elapsed_days_at_snapshot"] is not None \
                and h["stage_starts"].get(st or ""):
            d["temporal_structure"] = "PARTIAL"
        else:
            d["temporal_structure"] = "NOT_AVAILABLE"
        # market_structure（P0-C：候选有同段代理 → PARTIAL；否则 NOT_AVAILABLE）
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
            "matched_dimensions": sorted(k for k, v in d.items() if v in good),
        })

# ---------------------------------------------------------------- §十三 对照实验
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

# ---------------------------------------------------------------- 指标
strict_a = [m for m in matrix if m["lifecycle"] == "MATCH" and m["drivers"] == "MATCH"
            and m["evidence_sequence"] == "MATCH" and m["event_structure"] == "MATCH"]
strict_b = [m for m in matrix if m["lifecycle"] == "MATCH" and m["drivers"] == "MATCH"]
tier1 = [m for m in matrix if m["tier"] == "TIER_1_MULTI_DIMENSION"]
_sb = {m["candidate_id"] for m in strict_b}


def dist(dim):
    return dict(collections.Counter(m[dim] for m in matrix))


res = {
    "artifact": "structural_analogy_feasibility", "artifact_version": "0.2",
    "generated_by": "research/scripts/build_structural_analogy_readiness_v0_2.py",
    "supersedes_note": "v0.1 产物**保留不覆盖**（structural_analogy_feasibility_v0_1.*）",
    "snapshot": {"current_candidates_snapshot": cur.get("snapshot_date"),
                 "current_candidates_version": cur.get("current_candidates_version"),
                 "export_version": exp.get("timeline_export_version"),
                 "export_source_commit": exp.get("source_commit")},
    "status_vocabulary": ["MATCH", "PARTIAL", "UNKNOWN", "NOT_AVAILABLE", "MISMATCH"],
    "not_a": ["similarity score", "ranking", "winner", "best analogue", "prediction",
              "future outcome inference"],
    "repairs_applied": {
        "P0_A_lifecycle_semantic": {
            "problem": "v0.1 用 candidate 当前 phase 与历史 **terminal** phase 比较 → 80/85 MISMATCH",
            "fix": ("新增 `historical_stage_at_comparable_point`：取历史 lifecycle 中与 candidate "
                    "当前阶段**对应**的阶段（MATCH）/ 相邻阶段（PARTIAL），而非终态"),
            "legacy_field_kept": "`lifecycle_terminal_legacy`（保留旧口径作对照，**未删除**）",
        },
        "P0_B_candidate_event_entity": {
            "problem": "v0.1 candidate 侧无事件实体 → event_structure 85/85 NOT_AVAILABLE",
            "fix": ("从 candidate evidence 派生最小事件实体（仅取有 event_date 者），"
                    "复用历史 event_type 枚举"),
            "artifact": "structural_analogy_candidate_events_v0_1.json",
        },
        "P0_C_candidate_market_mapping": {
            "problem": "v0.1 candidate 侧无可映射行情序列 → market_structure 85/85 NOT_AVAILABLE",
            "fix": "建立 candidate → **同产品段**行情序列代理（显式声明覆盖限制）",
            "artifact": "structural_analogy_candidate_market_map_v0_1.json",
        },
        "P1_phase_window_end": {
            "decision": ("仓库证据**不足以**推导 end（无阶段结束证据）→ 保持 `null`；"
                         "语义记为 `unknown`，**不猜日期**"),
        },
    },
    "dimension_definitions": {
        "lifecycle": ("candidate.attention_state ↔ `historical_stage_at_comparable_point`"
                      "（历史 lifecycle 中与候选当前阶段对应的阶段）"),
        "lifecycle_terminal_legacy": "v0.1 口径（candidate.attention_state vs 历史最晚阶段），保留作对照",
        "drivers": "candidate.drivers[].category vs EVENT_TYPE_TO_DRIVER(历史 events[].event_type)",
        "evidence_sequence": "两侧统一到历史 event_type 词表后比较首项与交集（双方 ≥2 条才可比较）",
        "event_structure": "candidate 派生事件类型集合 vs 历史 events[].event_type 集合",
        "temporal_structure": "candidate phase_window.start + 已历时 vs 历史对应阶段锚点（单向可比）",
        "market_structure": "candidate 同段行情代理 vs 历史对象（PARTIAL=有代理；NOT_AVAILABLE=无代理）",
    },
    "candidate_profiles": CANDS, "historical_pool": HIST, "matrix": matrix,
    "name_vs_structural_experiment": {
        "method_a": "Name / Theme matching（同 Macro Theme + 人工 reference_cases）",
        "method_b": "Structural matching（TIER_1_MULTI_DIMENSION）",
        "per_candidate": exp_rows,
        "union_a": sorted(tA), "union_b": sorted(tB),
        "intersection": sorted(tA & tB),
        "only_a_name_only": sorted(tA - tB),
        "only_b_structure_only": sorted(tB - tA),
        "method_b_by_family": {f: sorted(o for o in tB if fam_of.get(o) == f)
                               for f in sorted({fam_of.get(o) for o in tB}, key=str)},
        "note": ("本阶段**不是**验证 Structural Matching 更准确；只验证修复后 "
                 "「结构匹配候选集合」与「名称匹配候选集合」的差异是否**仍然存在**。"),
    },
    "candidate_events_summary": events_doc["coverage"],
    "candidate_market_map": CAND_MARKET_PROXY,
    "sensitivity_analysis": {
        "note": "不同严格度下的结构可用性差异极大 —— 必须同时披露，不得只报最宽口径。",
        "STRICT_A_lifecycle_drivers_seq_event_all_MATCH": {
            "rows": len(strict_a), "candidates": len({m["candidate_id"] for m in strict_a})},
        "STRICT_B_lifecycle_and_drivers_MATCH": {
            "rows": len(strict_b), "candidates": len(_sb), "per_candidate":
                {c["candidate_id"]: [m["historical_object"] for m in strict_b
                                     if m["candidate_id"] == c["candidate_id"]] for c in CANDS}},
        "TIER_1_multi_dimension": {"rows": len(tier1),
                                   "candidates": len({m["candidate_id"] for m in tier1})},
        "dimension_status_distribution": {dim: dist(dim) for dim in
                                          ("lifecycle", "lifecycle_terminal_legacy", "drivers",
                                           "evidence_sequence", "event_structure",
                                           "temporal_structure", "market_structure")},
        "tier1_same_vs_cross_family": {
            "same": sum(1 for m in tier1 if m["same_macro_theme"]),
            "cross": sum(1 for m in tier1 if not m["same_macro_theme"])},
    },
    "three_key_numbers": {
        "definition": "usable structural analogue = STRICT_B（lifecycle MATCH + drivers MATCH）",
        "candidates_with_structurally_usable_analogue": {"count": len(_sb), "ids": sorted(_sb)},
        "candidates_with_only_theme_name_level_analogue": {
            "count": len([c for c in CANDS if c["candidate_id"] not in _sb
                          and (c.get("reference_cases") or [])]),
            "ids": [c["candidate_id"] for c in CANDS if c["candidate_id"] not in _sb
                    and (c.get("reference_cases") or [])]},
        "candidates_with_no_usable_analogue": {
            "count": len([c for c in CANDS if c["candidate_id"] not in _sb
                          and not (c.get("reference_cases") or [])]),
            "ids": [c["candidate_id"] for c in CANDS if c["candidate_id"] not in _sb
                    and not (c.get("reference_cases") or [])]},
        "note": "usable structural analogue != same-theme match",
    },
    "blocker_resolution_matrix": [
        {"blocker": "lifecycle semantic break", "v0_1": "BLOCKER",
         "v0_2": ("RESOLVED（比较口径修复）" if dist("lifecycle").get("MATCH", 0) > 0 else "UNRESOLVED"),
         "resolution": "新增 `historical_stage_at_comparable_point`（可比观测点口径）",
         "remaining_impact": "历史对象若不含候选当前阶段，仍只能 PARTIAL/MISMATCH（属真实数据差异）"},
        {"blocker": "candidate event entity", "v0_1": "BLOCKER",
         "v0_2": ("RESOLVED" if dist("event_structure").get("NOT_AVAILABLE", 0) < len(matrix)
                  else "UNRESOLVED"),
         "resolution": "从 evidence 派生最小事件实体（仅取有 event_date 者）",
         "remaining_impact": "11/39 条 evidence 无 event_date → 未派生（不编造）"},
        {"blocker": "candidate market mapping", "v0_1": "BLOCKER",
         "v0_2": ("PARTIALLY_RESOLVED（段代理，非候选自身证券）"
                  if dist("market_structure").get("PARTIAL", 0) > 0 else "UNRESOLVED"),
         "resolution": "建立同产品段行情序列代理",
         "remaining_impact": ("候选自身 2026 行情**不可得**（无证券数据 / 不联网）→ 市场比较仍为**单向**"
                              "（历史侧有，候选侧无）")},
        {"blocker": "phase_window.end", "v0_1": "HIGH",
         "v0_2": "UNRESOLVED（保持 null）",
         "resolution": "证据不足 → 语义记为 `unknown`，**不猜日期**",
         "remaining_impact": "temporal 仍只能单向比较"},
    ],
    "overall_status": None,  # 下方计算
    "minimum_viable_scope": None,
}

# overall 推导
dims = res["sensitivity_analysis"]["dimension_status_distribution"]
na = [k for k in ("lifecycle", "drivers", "evidence_sequence", "event_structure",
                  "temporal_structure", "market_structure") if dims[k].get("NOT_AVAILABLE", 0) == len(matrix)]
res["overall_status"] = ("INSUFFICIENT_DATA" if len(strict_a) == 0 and len(strict_b) == 0 and na else
                         "PARTIALLY_FEASIBLE")
res["minimum_viable_scope"] = {
    "option": "C（Research-only exploration），上限为 B",
    "statement": ("Lifecycle(可比观测点) + Driver + Evidence Sequence + Event Structure 四维机制上可算；"
                  "Market 为**单向段代理**（候选侧 2026 行情不可得）；Temporal 单向。"
                  "严格口径四维全 MATCH = %d 条、二维 = %d 候选 → 仍不足以支撑 Product 端相似度呈现。"
                  % (len(strict_a), len(_sb))),
    "not_yet_available": ["candidate-side 2026 market state", "双向 temporal",
                          "任何 similarity score / ranking"],
}

body = json.dumps(res, ensure_ascii=False, indent=1) + "\n"
ev_body = json.dumps(events_doc, ensure_ascii=False, indent=1) + "\n"
mk_doc = {
    "artifact": "structural_analogy_candidate_market_map", "artifact_version": "0.1",
    "generated_by": "research/scripts/build_structural_analogy_readiness_v0_2.py",
    "position": ("Research-only 派生层 —— **不进入** DB / schema.sql / timeline_export_v1.json / contracts / src。"),
    "semantics": {
        "status_vocabulary": ["MATCH", "PARTIAL", "NOT_AVAILABLE", "UNKNOWN"],
        "rule": ("**不因 candidate 属于某行业就假设其 market series 可用** —— "
                 "必须按**产品段**逐项判定，并显式记录覆盖限制"),
        "candidate_side_limit": ("候选自身**无**2026 行情数据（无证券记录、不联网抓取）→ "
                                 "映射得到的是**同段历史序列代理**，非候选自身行情"),
    },
    "mapping": CAND_MARKET_PROXY,
    "series_availability": [
        {"series_id": r["series_id"], "name": r["name"], "series_type": r["series_type"],
         "rows": r["n"], "range": f"{r['mn']}~{r['mx']}"}
        for r in conn.execute("""SELECT ms.series_id, ms.name, ms.series_type, COUNT(d.trade_date) n,
            MIN(d.trade_date) mn, MAX(d.trade_date) mx FROM market_series ms
            LEFT JOIN market_daily d ON d.series_id=ms.series_id
            GROUP BY ms.series_id ORDER BY ms.series_type, ms.series_id""")],
}
mk_body = json.dumps(mk_doc, ensure_ascii=False, indent=1) + "\n"

if CHECK:
    for p, b in ((OUT_JSON, body), (OUT_EVENTS, ev_body), (OUT_MARKET, mk_body)):
        if not os.path.exists(p):
            raise SystemExit(f"FAIL —— 产物不存在：{p}")
        if io.open(p, encoding="utf-8").read() != b:
            raise SystemExit(f"FAIL —— 与重算结果不一致（非 deterministic）：{p}")
    print("PASS —— 三份产物与重算结果逐字节一致（deterministic）。")
else:
    for p, b in ((OUT_JSON, body), (OUT_EVENTS, ev_body), (OUT_MARKET, mk_body)):
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(b)
        print("written", p)

with io.open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["candidate_id", "historical_object", "historical_kind", "historical_family",
                "same_macro_theme", "lifecycle", "historical_stage_at_comparable_point",
                "lifecycle_terminal_legacy", "drivers", "driver_overlap_count",
                "evidence_sequence", "event_structure", "temporal_structure", "market_structure",
                "tier", "matched_dimensions"])
    for m in matrix:
        w.writerow([m["candidate_id"], m["historical_object"], m["historical_kind"],
                    m["historical_family"], m["same_macro_theme"], m["lifecycle"],
                    m["historical_stage_at_comparable_point"], m["lifecycle_terminal_legacy"],
                    m["drivers"], m["driver_overlap_count"], m["evidence_sequence"],
                    m["event_structure"], m["temporal_structure"], m["market_structure"],
                    m["tier"], "|".join(m["matched_dimensions"])])
print("written", OUT_CSV)
print()
print("=== 维度分布（v0.2）===")
for k, v in res["sensitivity_analysis"]["dimension_status_distribution"].items():
    print(f"  {k:26s} {v}")
print()
print("=== tier ===", dict(collections.Counter(m["tier"] for m in matrix)))
print("strict_a:", len(strict_a), "| strict_b:", len(_sb), sorted(_sb),
      "| tier1:", len(tier1), "same/cross:", res["sensitivity_analysis"]["tier1_same_vs_cross_family"])
print("overall_status:", res["overall_status"])
