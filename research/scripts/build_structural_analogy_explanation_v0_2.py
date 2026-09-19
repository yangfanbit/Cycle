"""Structural Analogy Explanation Artifact v0.2 —— Product-facing 契约语义修正版。

依据：`docs/ARCHITECTURE.md` §5（Step 2 Artifact 的接口风险 5.1–5.4）
      `docs/PRODUCT_SIMILARITY_ARCHITECTURE_REVIEW.md` §6 / §7
      `docs/ROADMAP.md` Step 2

**修正 4 项**（均为 Product-facing 契约语义，**不改变任何研究结论**）：
  5.1 WHY NOT   —— `CROSS_MACRO_THEME` **移出** `why_not_similar`；改入 `theme_relation_note`（背景 metadata）
  5.2 ORDERING  —— `explanations[]` **不再按 structural_status 排序**；改为**稳定 identity 顺序**（historical_cycle_id 升序）
  5.3 IDENTITY  —— 正式区分 historical cycle / campaign / research candidate identity
                   （v0.1 把 `RC-*` 标为 campaign —— **语义错误**：export 的 `research_candidates[]`
                    复用了 `campaign_id` 字段名，必须按**来源数组**判定 kind）
  5.4 PROVENANCE—— 拆为 `dimension_evidence`（各维度**直接依据**）与 `background_sources`（**背景来源**）

**保留**：v0.1 artifact 逐字节不变（`structural_analogy_explanations_v0_1.json`）。
**不修改**：Structural Analogy Research v0.2 · Rule Set v0.2 · 任何原始数据 · schema · export · `src/**`。

产物：
  research/research/reports/structural_analogy_explanations_v0_2.json
"""
import collections
import io
import json
import os
import sys

ROOT = r"D:/@AW/投资/ThreeC"
REP = f"{ROOT}/research/research/reports"
CHECK = "--check" in sys.argv
OUT_JSON = f"{REP}/structural_analogy_explanations_v0_2.json"

R2 = json.load(io.open(f"{REP}/structural_analogy_research_v0_2.json", encoding="utf-8"))
V1P = json.load(io.open(f"{REP}/structural_analogy_research_v0_1.json", encoding="utf-8"))
CUR = json.load(io.open(f"{ROOT}/research/current/current_candidates.json", encoding="utf-8"))
EXP = json.load(io.open(f"{ROOT}/exports/timeline_export_v1.json", encoding="utf-8"))
LEDGER = json.load(io.open(f"{REP}/historical_driver_evidence_ledger_v0_1.json",
                           encoding="utf-8"))["entries"]

RULE_SET = R2["protocol"]["rule_set"]
RULE_SET_VER = R2["protocol"]["protocol_version"]
SNAPSHOT = R2["snapshot"]["current_candidates_snapshot"]
CUR_BY_ID = {c["candidate_id"]: c for c in CUR["candidates"]}
HP = {h["cycle_id"]: h for h in V1P["historical_profiles"]}

# ★ 5.3 identity：按**来源数组**判定 kind（export 的 research_candidates[] 复用 campaign_id 字段名）
KIND, CAMP_ID, RC_ID, THEME_CYCLE = {}, {}, {}, {}
for c in EXP.get("campaigns") or []:
    KIND[c["campaign_id"]] = "campaign"
    CAMP_ID[c["campaign_id"]] = c["campaign_id"]
    RC_ID[c["campaign_id"]] = None
    THEME_CYCLE[c["campaign_id"]] = c.get("theme_cycle_id")
for r in EXP.get("research_candidates") or []:
    rid = r["campaign_id"]  # export 字段名（值为 RC-*）
    KIND[rid] = "research_candidate"
    CAMP_ID[rid] = None
    RC_ID[rid] = rid
    THEME_CYCLE[rid] = r.get("theme_cycle_id")

LEDGER_BY_CYCLE = collections.defaultdict(list)
for e in LEDGER:
    LEDGER_BY_CYCLE[e["cycle_id"]].append(e)

# 各维度的**直接依据**（evidence id 级）
DIM_EVIDENCE_DIM = {
    "lifecycle": "candidate_evidence + historical lifecycle anchor",
    "mechanism_driver": "historical driver evidence（raw → canonical，含 DIRECT/DERIVED provenance）",
    "evidence_sequence": "candidate evidence chronology + historical event chronology",
    "event_structure": "candidate event entity + historical events",
}


def dim_evidence(cycle, canon_list, cand):
    out = {}
    # lifecycle：历史阶段锚点
    hp = HP[cycle]
    out["lifecycle"] = [{"source": "historical_lifecycle_anchor",
                         "stage": hp["stage_starts"] and None or None,
                         "note": "阶段锚点日期见 historical_profiles.stage_starts"}]
    # mechanism driver：逐 canonical driver 的 raw 证据
    drv = []
    for c in canon_list:
        for e in LEDGER_BY_CYCLE.get(cycle, []):
            if e["bucket"] in ("start", "accelerator") and e["canonical_driver"] == c:
                drv.append({"canonical_driver": c, "mapping_status": e["mapping_status"],
                            "raw_driver": e["raw_driver"][:120], "references": e["references"]})
    out["mechanism_driver"] = drv
    # evidence_sequence / event_structure：两侧事件
    out["evidence_sequence"] = [{"source": "candidate_evidence",
                                 "evidence_ids": [e["evidence_id"] for e in (cand.get("evidence") or [])]},
                                {"source": "historical_events",
                                 "event_ids": [e["event_id"] for e in hp.get("event_profile", [])]}]
    out["event_structure"] = out["evidence_sequence"]
    return out


def background_sources(cycle, cand):
    """**背景来源** —— 不作为任何维度的直接依据。"""
    hp = HP[cycle]
    return [
        {"source": "historical_macro_theme", "value": hp["macro_theme"],
         "role": "BACKGROUND_ONLY（不参与 Structural Status）"},
        {"source": "historical_terminal_phase", "value": hp["terminal_phase"],
         "role": "BACKGROUND_ONLY（不得用于 current-phase analogy）"},
        {"source": "historical_driver_provenance_summary",
         "value": hp.get("driver_provenance", {}),
         "role": "BACKGROUND_ONLY（逐维直接依据见 dimension_evidence）"},
        {"source": "candidate_source_summary",
         "value": [e.get("source_title") for e in (cand.get("evidence") or [])][:5],
         "role": "BACKGROUND_ONLY"},
    ]


def build_explanation(r, cand):
    cid, cyc = r["candidate_id"], r["historical_cycle"]
    hp = HP[cyc]
    dims = {"lifecycle": r["lifecycle"], "mechanism_driver": r["driver"],
            "evidence_sequence": r["evidence_sequence"], "event_structure": r["event_structure"]}
    supported = sorted(k for k, v in dims.items() if v in ("MATCH", "PARTIAL"))
    unknown = sorted(k for k, v in dims.items() if v in ("UNKNOWN", "NOT_AVAILABLE"))
    unsupported = sorted(k for k, v in dims.items() if k not in supported and k not in unknown)

    # ★ 5.1 why_similar / why_not_similar —— **不含任何 Theme Relation 内容**
    why_sim, why_not = [], []
    if r["lifecycle"] in ("MATCH", "PARTIAL"):
        why_sim.append(f"生命周期阶段对应（{r['lifecycle']}）：历史在可比观测点处于 "
                       f"{r['historical_stage_at_comparable_point']}")
    else:
        why_not.append(f"生命周期阶段不对应（{r['lifecycle']}）")
    if r["driver"] in ("MATCH", "PARTIAL"):
        why_sim.append(f"驱动机制存在交集：{r['driver_overlap']}（{r['driver_quality']}）")
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

    return {
        # ★ 5.3 identity
        "identity": {
            "historical_object_kind": KIND.get(cyc, "unknown"),
            "historical_cycle_id": cyc,
            "historical_campaign_id": CAMP_ID.get(cyc),
            "historical_research_candidate_id": RC_ID.get(cyc),
            "historical_theme_cycle_id": THEME_CYCLE.get(cyc),
            "identity_note": ("`historical_campaign_id` **仅对真实 Campaign 非空**；"
                              "Research Candidate 的 id 见 `historical_research_candidate_id`。"
                              "**不得**把 `historical_campaign_id` 当作所有历史对象的总身份。"),
        },
        "snapshot_date": SNAPSHOT,
        "rule_set_version": RULE_SET_VER,
        "structural_status": r["structural_status"],
        "strict_structural_supported": r["strict_structural_supported"],
        "theme_relation": {
            "value": r["theme_relation"],
            "role": "METADATA_ONLY —— **不参与** Structural Status 判定，**不得**据此升降级",
            "note": ("跨 Macro Theme **不是**「不相似」的依据；同族 **也不是**「相似」的依据。"
                     "本字段仅供界面作为背景展示。"),
        },
        "dimensions": {
            "lifecycle": {
                "status": r["lifecycle"],
                "candidate_phase": None,
                "historical_stage_at_comparable_point": r["historical_stage_at_comparable_point"],
                "note": "候选当前阶段 ↔ 历史在**可比观测点**的阶段（stage-aligned）",
                "forbidden_comparison": "candidate.current_phase ↔ historical.terminalPhaseOf（**禁止**）",
            },
            "mechanism_driver": {
                "status": r["driver"], "quality": r["driver_quality"], "overlap": r["driver_overlap"],
                "axis": "机制轴（Mechanism Driver）—— **不等于**证据类别（Evidence Category）",
                "note": {
                    "MATCH": "机制语义真正对应，且历史侧对共有机制有 DIRECT provenance",
                    "PARTIAL": "存在明确机制交集；MULTI_MECHANISM=交集≥2；"
                               "PRIMARY_MECHANISM_OVERLAP=单一交集且为历史 primary",
                    "PERIPHERAL_OVERLAP": "仅外围/非主要机制交集 → **不计为结构支持**",
                    "MISMATCH": "机制交集为空",
                    "NOT_AVAILABLE": "任一侧无 canonical driver",
                }.get(r["driver"], ""),
            },
            "evidence_sequence": {
                "status": r["evidence_sequence"], "subtype": r["sequence_subtype"],
                "note": "证据出现的**顺序**比较（LCS）；`same evidence types ≠ sequence match`",
            },
            "event_structure": {
                "status": r["event_structure"], "quality": r["event_quality"],
                "note": "event_type + chronology + linkage；`SINGLE_TYPE_ONLY` 不得作为 PARTIAL；"
                        "Event **不能**证明 Driver",
            },
        },
        "supported_dimensions": supported,
        "unknown_dimensions": unknown,
        "unsupported_dimensions": unsupported,
        "why_similar": why_sim,
        "why_not_similar": why_not,
        # ★ 5.4 provenance 分层
        "dimension_evidence": dim_evidence(cyc, r["driver_overlap"], cand),
        "background_sources": background_sources(cyc, cand),
        "supplementary_context": {
            "market_structure": "SUPPLEMENTARY_ONLY",
            "temporal_structure": "SUPPLEMENTARY_ONLY",
            "note": "Market / Temporal **不参与** Structural Status，仅作补充背景",
        },
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
    # ★ 5.2 稳定 identity 顺序（historical_cycle_id 升序）—— **不按 structural_status 排序**
    exps.sort(key=lambda x: x["identity"]["historical_cycle_id"])
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
    "artifact_version": "0.2",
    "generated_by": "research/scripts/build_structural_analogy_explanation_v0_2.py",
    "supersedes_note": ("v0.1（`structural_analogy_explanations_v0_1.json`）**逐字节保留**；"
                        "本版仅做 **Product-facing 契约语义修正**，"
                        "**不改变任何研究结论**（structural_status 计数与 v0.1 完全一致）。"),
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
    "changelog_v0_1_to_v0_2": [
        {"id": "5.1", "issue": "CROSS_MACRO_THEME 出现在 why_not_similar",
         "fix": "移出 why_not_similar；theme_relation 改为对象（value + role + note），显式标注 METADATA_ONLY"},
        {"id": "5.2", "issue": "explanations[] 按 structural_status 排序 → 易被读成「从强到弱」",
         "fix": "改为**稳定 identity 顺序**（historical_cycle_id 升序），并显式声明不是排名"},
        {"id": "5.3", "issue": "historical_campaign_id 被用作所有历史对象的总身份（RC-* 实为 Research Candidate）",
         "fix": "新增 identity 对象，按**来源数组**区分 campaign / research_candidate；"
                "historical_campaign_id 仅对真实 Campaign 非空"},
        {"id": "5.4", "issue": "provenance 混在一起，Product 易做因果推断",
         "fix": "拆为 dimension_evidence（各维度**直接依据**）与 background_sources（**背景来源**）"},
    ],
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
        "evidence_category": {"label_zh": "证据类别", "label_en": "Evidence Category",
                              "values": ["POLICY", "INDUSTRY", "CAPITAL", "SENTIMENT", "EXTERNAL"],
                              "meaning": "「公司公告」是一类**证据来源**"},
        "mechanism_driver": {"label_zh": "驱动机制", "label_en": "Mechanism Driver",
                             "values": ["POLICY_DRIVEN", "INDUSTRY_UPGRADE", "TECH_BREAKTHROUGH",
                                        "DEMAND_SURGE", "SUPPLY_CONTRACTION", "VALUATION_RESET",
                                        "CYCLE_REVERSAL", "EVENT_CATALYST"],
                             "meaning": "「产业升级」是一个**机制判断**"},
    },
    "semantics": {
        "unknown_vs_absent": "`UNKNOWN` / `NOT_AVAILABLE` ≠ 现象不存在；表示**当前资料不足以编码**",
        "theme_relation_is_metadata": "`theme_relation` **不参与** Structural Status 判定，仅为背景 metadata",
        "ordering_semantics": ("`explanations[]` 按 `historical_cycle_id` 升序排列 —— "
                                    "**这是稳定 identity 顺序，不是强弱排名**"),
        "supplementary_only": "Market / Temporal 为 `SUPPLEMENTARY_ONLY`，不参与 Structural Status",
        "product_must_not": ["把 UNKNOWN 当成 NO", "把 PARTIAL 当成 MATCH",
                             "把 Theme Relation 变成等级因素", "重新计算四个维度",
                             "生成 score / ranking / probability", "联网"],
    },
    "candidates": candidates,
    "coverage": {
        "candidates": len(candidates),
        "explanations": sum(len(c["explanations"]) for c in candidates),
        "by_status": dict(collections.Counter(
            e["structural_status"] for c in candidates for e in c["explanations"])),
        "by_historical_object_kind": dict(collections.Counter(
            e["identity"]["historical_object_kind"] for c in candidates for e in c["explanations"])),
    },
}

# 禁止字段自检（只扫数据字段名）
_BANNED = ("score", "percentage", "probability", "winner", "ranking", "confidence")
_HITS = []


def _scan(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            if any(b in k.lower() for b in _BANNED):
                _HITS.append(f"{path}.{k}")
            _scan(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _scan(v, f"{path}[{i}]")


_scan(res)
if _HITS:
    raise SystemExit("FAIL —— artifact 含禁止字段：" + ", ".join(_HITS))

# 一致性自检：状态计数必须与 Research v0.2 完全一致（不改变研究结论）
R2_COUNTS = R2["core_result"]["v0_2_counts"]
for k in ("STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL", "THEME_ONLY",
          "INSUFFICIENT_EVIDENCE", "NO_VALID_CORRESPONDENCE"):
    assert res["coverage"]["by_status"].get(k, 0) == R2_COUNTS[k], f"FAIL —— {k} 计数与 Research v0.2 不一致"

# 5.1 自检：why_not_similar 不得含 theme / macro theme 内容
for c in candidates:
    for e in c["explanations"]:
        for t in e["why_not_similar"]:
            assert "跨 Macro Theme" not in t and "theme" not in t.lower(), \
                f"FAIL —— why_not_similar 仍含 theme 内容：{t}"

body = json.dumps(res, ensure_ascii=False, indent=1) + "\n"
if CHECK:
    if not os.path.exists(OUT_JSON) or io.open(OUT_JSON, encoding="utf-8").read() != body:
        raise SystemExit("FAIL —— 产物与重算结果不一致")
    print("PASS —— 产物与重算结果逐字节一致（deterministic）。")
else:
    with io.open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    print("written", OUT_JSON)

print("forbidden-field self-check: PASS")
print("consistency self-check vs Research v0.2: PASS")
print("5.1 self-check (why_not_similar 无 theme): PASS")
print()
print("candidates:", res["coverage"]["candidates"], "| explanations:", res["coverage"]["explanations"])
print("by_status:", res["coverage"]["by_status"])
print("by_kind:", res["coverage"]["by_historical_object_kind"])
