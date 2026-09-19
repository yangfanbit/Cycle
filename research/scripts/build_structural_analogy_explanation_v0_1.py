"""Structural Analogy Explanation Artifact v0.1 —— Research-derived / Product-facing。

依据：
  `docs/ROADMAP.md` Step 2 · Structural Analogy Explanation Artifact
  `docs/PRODUCT_SIMILARITY_ARCHITECTURE_REVIEW.md` §6（Driver 分层）/ §7（Artifact 字段）

**定位**：Product **只读**本 artifact，**不重新实现** Structural Analogy 规则。
规则来源唯一 = `Structural Analogy Rule Set v0.2`
（`research/research/methodology/structural_analogy_rule_set_v0_2.md`）。

**禁止**：score · percentage · probability · winner · ranking · top/best analogue。
**不修改**：任何旧产物 · schema · export · `src/**` · Product。

产物：
  research/research/reports/structural_analogy_explanations_v0_1.json
"""
import collections
import io
import json
import os
import sys

ROOT = r"D:/@AW/投资/ThreeC"
REP = f"{ROOT}/research/research/reports"
CHECK = "--check" in sys.argv
OUT_JSON = f"{REP}/structural_analogy_explanations_v0_1.json"

R2 = json.load(io.open(f"{REP}/structural_analogy_research_v0_2.json", encoding="utf-8"))
CUR = json.load(io.open(f"{ROOT}/research/current/current_candidates.json", encoding="utf-8"))
LEDGER = json.load(io.open(f"{REP}/historical_driver_evidence_ledger_v0_1.json",
                           encoding="utf-8"))["entries"]

RULE_SET = R2["protocol"]["rule_set"]
RULE_SET_VER = R2["protocol"]["protocol_version"]
SNAPSHOT = R2["snapshot"]["current_candidates_snapshot"]

CUR_BY_ID = {c["candidate_id"]: c for c in CUR["candidates"]}
HP = {h["cycle_id"]: h for h in R2.get("historical_profiles", [])} if "historical_profiles" in R2 else {}
V1P = json.load(io.open(f"{REP}/structural_analogy_research_v0_1.json", encoding="utf-8"))
HP = {h["cycle_id"]: h for h in V1P["historical_profiles"]}

# 历史 driver 的 evidence provenance（raw → canonical）
LEDGER_BY_CYCLE = collections.defaultdict(list)
for e in LEDGER:
    LEDGER_BY_CYCLE[e["cycle_id"]].append(e)


def dim_provenance(cycle_id, canon):
    out = []
    for e in LEDGER_BY_CYCLE.get(cycle_id, []):
        if e["bucket"] in ("start", "accelerator") and e["canonical_driver"] == canon:
            out.append({"raw_driver": e["raw_driver"][:120],
                        "mapping_status": e["mapping_status"],
                        "references": e["references"],
                        "bucket": e["bucket"]})
    return out


# ---------------------------------------------------------------- 维度说明（Product 可读）
def explain_lifecycle(r):
    st = r["lifecycle"]
    stage = r["historical_stage_at_comparable_point"]
    return {
        "status": st,
        "candidate_phase": None,  # 由上层填
        "historical_stage_at_comparable_point": stage,
        "note": ("候选当前阶段 ↔ 历史在**可比观测点**的阶段（stage-aligned）"
                 if st != "NOT_AVAILABLE" else "历史无 lifecycle"),
        "forbidden_comparison": "candidate.current_phase ↔ historical.terminalPhaseOf（**禁止**）",
    }


def explain_driver(r):
    return {
        "status": r["driver"],
        "quality": r["driver_quality"],
        "overlap": r["driver_overlap"],
        "axis": "机制轴（Mechanism Driver），非证据类别轴",
        "note": {
            "MATCH": "机制语义真正对应，且历史侧对共有机制有 DIRECT provenance",
            "PARTIAL": "存在明确机制交集；MULTI_MECHANISM=交集≥2；PRIMARY_MECHANISM_OVERLAP=单一交集且为历史 primary",
            "PERIPHERAL_OVERLAP": "仅外围/非主要机制交集 → **不计为结构支持**",
            "MISMATCH": "机制交集为空",
            "NOT_AVAILABLE": "任一侧无 canonical driver",
        }.get(r["driver"], ""),
    }


def explain_sequence(r):
    return {
        "status": r["evidence_sequence"],
        "subtype": r["sequence_subtype"],
        "note": ("证据出现的**顺序**比较（LCS）；`same evidence types ≠ sequence match`；"
                 "`SET_ONLY` 不得当作 `SEQUENCE_MATCH`"),
    }


def explain_event(r):
    return {
        "status": r["event_structure"],
        "quality": r["event_quality"],
        "note": ("event_type + chronology + linkage；`SINGLE_TYPE_ONLY` 不得作为 PARTIAL；"
                 "Event **不能**证明 Driver"),
    }


def classify_dims(r):
    dims = {"lifecycle": r["lifecycle"], "mechanism_driver": r["driver"],
            "evidence_sequence": r["evidence_sequence"], "event_structure": r["event_structure"]}
    supported, unknown, unsupported = [], [], []
    for k, v in dims.items():
        if v in ("MATCH", "PARTIAL"):
            supported.append(k)
        elif v in ("UNKNOWN", "NOT_AVAILABLE"):
            unknown.append(k)
        else:
            unsupported.append(k)
    return dims, sorted(supported), sorted(unknown), sorted(unsupported)


def build_explanation(r, cand):
    cid, cyc = r["candidate_id"], r["historical_cycle"]
    hp = HP[cyc]
    dims, supported, unknown, unsupported = classify_dims(r)

    # why_similar / why_not_similar（由**结构维度**派生，不含任何 score）
    why_sim, why_not = [], []
    if r["lifecycle"] in ("MATCH", "PARTIAL"):
        why_sim.append(f"生命周期阶段对应（{r['lifecycle']}）："
                       f"历史在可比观测点处于 {r['historical_stage_at_comparable_point']}")
    else:
        why_not.append(f"生命周期阶段不对应（{r['lifecycle']}）")
    if r["driver"] in ("MATCH", "PARTIAL"):
        why_sim.append(f"驱动机制存在交集：{r['driver_overlap']}"
                       f"（{r['driver_quality']}）")
    elif r["driver"] == "PERIPHERAL_OVERLAP":
        why_not.append(f"仅外围机制重叠 {r['driver_overlap']} → 不计为结构支持")
    else:
        why_not.append(f"驱动机制无交集（{r['driver']}）")
    if r["evidence_sequence"] in ("MATCH", "PARTIAL"):
        why_sim.append(f"证据顺序可比（{r['sequence_subtype']}）")
    else:
        why_not.append(f"证据顺序不可比（{r['evidence_sequence']} / {r['sequence_subtype']}）")
    if r["event_structure"] in ("MATCH", "PARTIAL"):
        why_sim.append(f"事件结构存在对应（{r['event_quality']}）")
    else:
        why_not.append(f"事件结构不对应（{r['event_structure']} / {r['event_quality']}）")
    for d in r["mismatch_dimensions"]:
        why_not.append(f"{d} 明确冲突（MISMATCH）")
    for d in r["unknown_dimensions"]:
        why_not.append(f"{d} 资料不足（UNKNOWN / NOT_AVAILABLE）—— **缺失证据 ≠ 现象不存在**")
    if r["theme_relation"] == "CROSS_MACRO_THEME":
        why_not.append("跨 Macro Theme：无同主题上下文支撑（**不构成降级理由**，仅作背景）")

    prov = [{"source": "candidate_evidence",
             "evidence_ids": [e["evidence_id"] for e in (cand.get("evidence") or [])]}]
    for c in r["driver_overlap"]:
        prov.append({"source": "historical_driver_evidence", "canonical_driver": c,
                     "entries": dim_provenance(cyc, c)})
    prov.append({"source": "historical_events",
                 "event_ids": [e["event_id"] for e in hp.get("event_profile", [])]})

    return {
        "historical_campaign_id": hp.get("campaign_id") or cyc,
        "historical_cycle_id": cyc,
        "historical_kind": r["historical_kind"],
        "historical_macro_theme": r["historical_macro_theme"],
        "snapshot_date": SNAPSHOT,
        "rule_set_version": RULE_SET_VER,
        "structural_status": r["structural_status"],
        "strict_structural_supported": r["strict_structural_supported"],
        "theme_relation": r["theme_relation"],
        "dimensions": {
            "lifecycle": explain_lifecycle(r),
            "mechanism_driver": explain_driver(r),
            "evidence_sequence": explain_sequence(r),
            "event_structure": explain_event(r),
        },
        "supported_dimensions": supported,
        "unknown_dimensions": unknown,
        "unsupported_dimensions": unsupported,
        "why_similar": why_sim,
        "why_not_similar": why_not,
        "provenance": prov,
        "supplementary_context": r["supplementary"],
    }


candidates = []
for cp in R2["candidate_profiles"]:
    cid = cp["candidate_id"]
    cand = CUR_BY_ID.get(cid, {})
    rows = [r for r in R2["correspondence_matrix"] if r["candidate_id"] == cid]
    exps = []
    for r in rows:
        e = build_explanation(r, cand)
        e["dimensions"]["lifecycle"]["candidate_phase"] = cp["current_structural_profile"]["current_phase"]
        exps.append(e)
    # 稳定排序：结构等级序 → 历史 cycle id（**不是排名**，仅确定性排序）
    ORDER = {k: i for i, k in enumerate(
        ["STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL", "THEME_ONLY",
         "INSUFFICIENT_EVIDENCE", "NO_VALID_CORRESPONDENCE"])}
    exps.sort(key=lambda x: (ORDER[x["structural_status"]], x["historical_cycle_id"]))
    candidates.append({
        "candidate_id": cid,
        "display_name": cand.get("display_name"),
        "macro_theme": cp["macro_theme"],
        "current_structural_profile": {
            "current_phase": cp["current_structural_profile"]["current_phase"],
            "phase_stage": cp["current_structural_profile"]["phase_stage"],
            "mechanism_drivers": cp["current_structural_profile"]["driver_profile"]["canonical_drivers"],
            "evidence_categories": cp["current_structural_profile"]["driver_profile"]["category_axis_supplementary"],
            "evidence_sequence": cp["current_structural_profile"]["evidence_sequence"],
            "evidence_sequence_status": cp["current_structural_profile"]["evidence_sequence_status"],
            "event_types": cp["current_structural_profile"]["event_profile_types"],
            "market_status": cp["current_structural_profile"]["market_status"],
            "temporal_status": cp["current_structural_profile"]["temporal_status"],
            "structural_gaps": cp["current_structural_profile"]["structural_gaps"],
        },
        "summary": dict(collections.Counter(e["structural_status"] for e in exps)),
        "explanations": exps,
    })

res = {
    "artifact": "structural_analogy_explanations",
    "artifact_version": "0.1",
    "generated_by": "research/scripts/build_structural_analogy_explanation_v0_1.py",
    "contract": {
        "consumer": "Product",
        "mode": "READ_ONLY —— Product **不得重新实现** Structural Analogy 规则",
        "rule_source": "Structural Analogy Rule Set v0.2（唯一规则来源）",
        "rule_set_version": RULE_SET_VER,
        "source_artifact": "research/research/reports/structural_analogy_research_v0_2.json",
    },
    "not_a": ["score", "percentage", "probability", "winner", "ranking", "top analogue",
              "best analogue", "investment advice", "prediction", "trading signal"],
    "snapshot_date": SNAPSHOT,
    "rule_set": RULE_SET,
    "rule_set_version": RULE_SET_VER,
    "status_vocabulary": ["STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL", "THEME_ONLY",
                          "INSUFFICIENT_EVIDENCE", "NO_VALID_CORRESPONDENCE"],
    "dimension_vocabulary": {
        "lifecycle": ["MATCH", "PARTIAL", "MISMATCH", "UNKNOWN", "NOT_AVAILABLE"],
        "mechanism_driver": ["MATCH", "PARTIAL", "PERIPHERAL_OVERLAP", "MISMATCH",
                             "UNKNOWN", "NOT_AVAILABLE"],
        "evidence_sequence": ["MATCH", "PARTIAL", "MISMATCH", "UNKNOWN", "NOT_AVAILABLE"],
        "event_structure": ["MATCH", "PARTIAL", "MISMATCH", "NOT_AVAILABLE"],
    },
    "dimension_naming": {
        "rule": "产品文案**不要**把两者都简称「Driver」",
        "evidence_category": {
            "label_zh": "证据类别", "label_en": "Evidence Category",
            "values": ["POLICY", "INDUSTRY", "CAPITAL", "SENTIMENT", "EXTERNAL"],
            "meaning": "「公司公告」是一类**证据来源**",
        },
        "mechanism_driver": {
            "label_zh": "驱动机制", "label_en": "Mechanism Driver",
            "values": ["POLICY_DRIVEN", "INDUSTRY_UPGRADE", "TECH_BREAKTHROUGH", "DEMAND_SURGE",
                       "SUPPLY_CONTRACTION", "VALUATION_RESET", "CYCLE_REVERSAL", "EVENT_CATALYST"],
            "meaning": "「产业升级」是一个**机制判断**",
        },
    },
    "semantics": {
        "unknown_vs_absent": ("`UNKNOWN` / `NOT_AVAILABLE` ≠ 现象不存在；"
                              "表示**当前资料不足以编码**"),
        "theme_relation_is_metadata": ("`theme_relation` **不参与** Structural Status 判定，"
                                       "仅为背景 metadata；不得据此升降级"),
        "no_ordering": "本 artifact **不提供**任何排序、分数或概率；Product 不得据此生成榜单",
        "supplementary_only": "Market / Temporal 为 `SUPPLEMENTARY_ONLY`，不参与 Structural Status",
    },
    "candidates": candidates,
    "coverage": {
        "candidates": len(candidates),
        "explanations": sum(len(c["explanations"]) for c in candidates),
        "by_status": dict(collections.Counter(
            e["structural_status"] for c in candidates for e in c["explanations"])),
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

# 禁止字段自检：只扫描**数据字段名**（排除 not_a / semantics 描述）
_BANNED = ("score", "percentage", "probability", "winner", "ranking", "confidence")
_FORBIDDEN_HITS = []


def _scan(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            if any(b in k.lower() for b in _BANNED):
                _FORBIDDEN_HITS.append(f"{path}.{k}")
            _scan(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _scan(v, f"{path}[{i}]")


_scan(res)
if _FORBIDDEN_HITS:
    raise SystemExit("FAIL —— artifact 含禁止字段：" + ", ".join(_FORBIDDEN_HITS))
print("forbidden-field self-check: PASS（无 score / percentage / probability / winner / ranking / confidence 字段）")

print()
print("candidates:", res["coverage"]["candidates"], "| explanations:", res["coverage"]["explanations"])
print("by_status:", res["coverage"]["by_status"])
print("rule_set_version:", RULE_SET_VER)
