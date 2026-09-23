"""Structural Analogy Explanation Artifact v0.5 —— Product-facing，基于 **Research v0.5**（79 Historical Objects · Rule Set v0.3 · Driver Canonicalization v0.5）。

依据：`docs/ARCHITECTURE.md` §5 · `docs/PRODUCT_SIMILARITY_ARCHITECTURE_REVIEW.md` §6/§7
      `research/research/methodology/structural_analogy_rule_set_v0_2.md`（**冻结规则，未修改**）

**与 v0.2 的关系**
  · **规则不变**（Rule Set v0.2 冻结）；**契约语义不变**（沿用 v0.2 的 4 项修正）。
  · **唯一变化 = 历史 universe 由 17 cycle 扩容至 79 cycle**（R01-01~R01-06 全部纳入）。
  · **新增** `governance_context`（`governance-gates-v0.1` 元数据，**仅 supplementary**）。
  · v0.1 / v0.2 artifact **逐字节保留**。

**保留**：v0.1 / v0.2 artifact 逐字节不变。
**不修改**：Rule Set v0.2 · Research v0.2 · 任何原始数据 · schema · export · `src/**`。

产物：
  research/research/reports/structural_analogy_explanations_v0_3.json
"""
import collections
import io
import json
import os
import sys

ROOT = r"D:/@AW/投资/ThreeC"
REP = f"{ROOT}/research/research/reports"
CHECK = "--check" in sys.argv
OUT_JSON = f"{REP}/structural_analogy_explanations_v0_5.json"

R3 = json.load(io.open(f"{REP}/structural_analogy_research_v0_5.json", encoding="utf-8"))
CUR = json.load(io.open(f"{ROOT}/research/current/current_candidates.json", encoding="utf-8"))
EXP = json.load(io.open(f"{ROOT}/exports/timeline_export_v1.json", encoding="utf-8"))
GOV = {c["campaign_id"]: c for c in
       json.load(io.open(f"{REP}/governance_classification_v0_1.json", encoding="utf-8"))["campaigns"]}

# ★ v0.5：driver 逐条证据（供 dimension_evidence 保留 raw_driver / references）
_LED4 = json.load(io.open(f"{REP}/historical_driver_evidence_ledger_v0_4.json",
                          encoding="utf-8"))["entries"]
DRV_ROWS = {}
for _e in _LED4:
    DRV_ROWS.setdefault(_e["cycle_id"], []).append(_e)

RULE_SET = R3["protocol"]["rule_set"]
RULE_SET_VER = R3["protocol"]["protocol_version"]
SNAPSHOT = R3["snapshot"]["current_candidates_snapshot"]
CUR_BY_ID = {c["candidate_id"]: c for c in CUR["candidates"]}
HP = {h["cycle_id"]: h for h in R3["historical_profiles"]}
CP = {c["candidate_id"]: c for c in R3["candidate_profiles"]}

# ★ identity：按**来源数组**判定 kind（export 的 research_candidates[] 复用 campaign_id 字段名）
KIND, CAMP_ID, RC_ID, THEME_CYCLE = {}, {}, {}, {}
for c in EXP.get("campaigns") or []:
    KIND[c["campaign_id"]] = "campaign"
    CAMP_ID[c["campaign_id"]] = c["campaign_id"]
    RC_ID[c["campaign_id"]] = None
    THEME_CYCLE[c["campaign_id"]] = c.get("theme_cycle_id")
for r in EXP.get("research_candidates") or []:
    rid = r["campaign_id"]
    KIND[rid] = "research_candidate"
    CAMP_ID[rid] = None
    RC_ID[rid] = rid
    THEME_CYCLE[rid] = r.get("theme_cycle_id")

DRIVER_DIM_NOTE = ("机制轴（Mechanism Driver）—— **不等于**证据类别（Evidence Category）；"
                   "`PERIPHERAL_OVERLAP` **不计入**结构支持")
SEQ_NOTE = "证据出现的**顺序**比较（LCS）；`same evidence types ≠ sequence match`；`SET_ONLY` 不得当作 `SEQUENCE_MATCH`"
EVENT_NOTE = ("event_type + chronology + linkage；`SINGLE_TYPE_ONLY` 不得作为 PARTIAL；"
              "Event **不能**证明 Driver")
LC_NOTE = "候选当前阶段 ↔ 历史在**可比观测点**的阶段（stage-aligned）"
LC_FORBID = "candidate.current_phase ↔ historical.terminalPhaseOf（**禁止**）"

# ---------------------------------------------------------------- 逐候选构造
candidates_out = []
for cp in R3["candidate_profiles"]:
    cid = cp["candidate_id"]
    cur_obj = CUR_BY_ID[cid]
    rows = [m for m in R3["matrix"] if m["candidate_id"] == cid]
    exps = []
    for m in sorted(rows, key=lambda x: x["historical_cycle"]):  # 稳定 identity 顺序
        cyc = m["historical_cycle"]
        h = HP[cyc]
        g = GOV.get(cyc) or {}
        dims = {
            "lifecycle": {"status": m["lifecycle"], "candidate_phase": cp["current_phase"],
                          "historical_stage_at_comparable_point": m["historical_stage_at_comparable_point"],
                          "note": LC_NOTE, "forbidden_comparison": LC_FORBID},
            "mechanism_driver": {"status": m["driver"], "quality": m["driver_quality"],
                                 "overlap": m["driver_overlap"], "axis": DRIVER_DIM_NOTE,
                                 "historical_primary_mechanism": m["historical_primary_mechanism"],
                                 "note": "存在明确机制交集；MULTI_MECHANISM=交集≥2；"
                                         "PRIMARY_MECHANISM_OVERLAP=单一交集且为历史 primary"},
            "evidence_sequence": {"status": m["evidence_sequence"], "subtype": m["sequence_subtype"],
                                  "note": SEQ_NOTE},
            "event_structure": {"status": m["event_structure"], "quality": m["event_quality"],
                                "note": EVENT_NOTE},
        }
        # ★ v0.5 修正：三维数组必须**完整划分**四维（互不重叠且并集 = 4 维）
        #   · COMPARISON_POINT_UNKNOWN 属 lifecycle 的「资料不足」态 → 计入 unknown
        #   · PERIPHERAL_OVERLAP 属「不计入结构支持」态 → 计入 unsupported（不是 supported）
        supported = [k for k, v in dims.items() if v["status"] in ("MATCH", "PARTIAL")]
        unknown = [k for k, v in dims.items()
                   if v["status"] in ("UNKNOWN", "NOT_AVAILABLE", "COMPARISON_POINT_UNKNOWN")]
        unsupported = [k for k, v in dims.items()
                       if v["status"] in ("MISMATCH", "PERIPHERAL_OVERLAP")]

        why_sim = []
        if m["lifecycle"] in ("MATCH", "PARTIAL"):
            why_sim.append(f"生命周期阶段对应（{m['lifecycle']}）：历史在可比观测点处于 "
                           f"{m['historical_stage_at_comparable_point']}")
        if m["driver"] in ("MATCH", "PARTIAL"):
            why_sim.append(f"驱动机制存在交集：{m['driver_overlap']}（{m['driver_quality']}）")
        if m["evidence_sequence"] in ("MATCH", "PARTIAL"):
            why_sim.append(f"证据顺序对应（{m['evidence_sequence']} / {m['sequence_subtype']}）")
        if m["event_structure"] in ("MATCH", "PARTIAL"):
            why_sim.append(f"事件结构对应（{m['event_structure']} / {m['event_quality']}）")
        if not why_sim:
            why_sim.append("无任何正式维度形成结构对应")

        why_not = []
        if m["evidence_sequence"] in ("NOT_AVAILABLE", "UNKNOWN"):
            why_not.append(f"证据顺序不可比（{m['evidence_sequence']} / {m['sequence_subtype']}）")
        if m["event_structure"] in ("NOT_AVAILABLE", "UNKNOWN"):
            why_not.append(f"事件结构资料不足（{m['event_structure']}）")
        for k in m["mismatch_dimensions"]:
            why_not.append(f"{k} 明确冲突（MISMATCH）")
        if m["driver"] == "PERIPHERAL_OVERLAP":
            why_not.append("仅存在**外围**机制交集（PERIPHERAL_OVERLAP）→ **不计入**结构支持")
        if m["sequence_subtype"] == "SET_ONLY":
            why_not.append("证据顺序为 `SET_ONLY`（**不得**当作 `SEQUENCE_MATCH`）")
        # ★ v0.5 修正（契约 5.1）：`theme_relation` **不得**进入 why_not_similar ——
        #   跨 Macro Theme 不是「不相似」的理由，它只是背景 metadata（见 theme_relation 字段）。
        if not why_not:
            why_not.append("无显著负证据，但仍受历史驱动证据粒度与事件覆盖限制")

        # ---- 各维度直接依据 ----
        dim_ev = {
            "lifecycle": [{"source": "historical_lifecycle_anchor",
                           "stage": m["historical_stage_at_comparable_point"],
                           "note": "阶段锚点日期见 historical_profiles.stage_starts"}],
            "mechanism_driver": [{
                "canonical_driver": k,
                "mapping_status": "|".join(h["driver_provenance"].get(k, [])),
                # ★ v0.5：保留逐条 raw_driver（provenance 不丢失）
                "raw_driver": next((e["raw_driver"] for e in DRV_ROWS.get(cyc, [])
                                    if e["canonical_driver"] == k and e["bucket"] in ("start", "accelerator")), ""),
                "references": next((e["references"] for e in DRV_ROWS.get(cyc, [])
                                    if e["canonical_driver"] == k and e["bucket"] in ("start", "accelerator")), []),
                "note": ("raw → canonical（Historical Driver Canonicalization **v0.5**；"
                         "规则集 = Rule Set v0.3）"),
            } for k in m["driver_overlap"]],
            "evidence_sequence": [{"source": "candidate_evidence", "sequence": cp["evidence_sequence"]},
                                  {"source": "historical_events",
                                   "sequence": h["evidence_sequence"]}],
            "event_structure": [{"source": "candidate_event_types",
                                 "values": sorted({e["event_type"] for e in cp["event_profile"]})},
                                {"source": "historical_event_types",
                                 "values": sorted(set(h["evidence_sequence"]))}],
        }

        exps.append({
            "identity": {
                "historical_object_kind": KIND.get(cyc, h["kind"]),
                "historical_cycle_id": cyc,
                "historical_campaign_id": CAMP_ID.get(cyc),
                "historical_research_candidate_id": RC_ID.get(cyc),
                "historical_theme_cycle_id": THEME_CYCLE.get(cyc),
                "identity_note": ("`historical_campaign_id` **仅对真实 Campaign 非空**；"
                                  "Research Candidate 的 id 见 `historical_research_candidate_id`。"),
            },
            "snapshot_date": SNAPSHOT,
            "rule_set_version": RULE_SET_VER,
            "structural_status": m["structural_status"],
            "strict_structural_supported": m["strict_structural_supported"],
            "theme_relation": {
                "value": m["theme_relation"],
                "role": "METADATA_ONLY —— **不参与** Structural Status 判定，**不得**据此升降级",
                "note": "跨 Macro Theme **不是**「不相似」的依据；同族 **也不是**「相似」的依据。",
            },
            "dimensions": dims,
            "supported_dimensions": supported,
            "unknown_dimensions": unknown,
            "unsupported_dimensions": unsupported,
            "why_similar": why_sim,
            "why_not_similar": why_not,
            "dimension_evidence": dim_ev,
            "background_sources": [
                {"source": "historical_macro_theme", "value": h["macro_theme"],
                 "role": "BACKGROUND_ONLY（不参与 Structural Status）"},
                {"source": "historical_terminal_phase", "value": h["terminal_phase"],
                 "role": "BACKGROUND_ONLY（不得用于 current-phase analogy）"},
                {"source": "historical_primary_mechanism", "value": h["primary_mechanism"],
                 "role": "BACKGROUND_ONLY（Rule Set §4 派生）"},
                {"source": "historical_driver_provenance_summary",
                 "value": h["driver_provenance"],
                 "role": "BACKGROUND_ONLY（逐维直接依据见 dimension_evidence）"},
            ],
            "governance_context": {
                "ruleset": "governance-gates-v0.1",
                "market_evidence_state": g.get("market_evidence_state"),
                "beta_level": g.get("beta_level"),
                "peak_state": (g.get("peak") or {}).get("state"),
                "end_state": (g.get("end") or {}).get("state"),
                "result": g.get("result"),
                "role": ("SUPPLEMENTARY_ONLY —— **不参与** Structural Status（Rule Set v0.2 §12）；"
                         "`beta_level=1` **不等于** Alpha；`A_SHARE_MARKET` **不等于**独立 Campaign；"
                         "`result=weak` = 方向为负，**不降低**该历史结构参与类比的资格"),
            },
            "supplementary_context": {
                "market_structure": "SUPPLEMENTARY_ONLY",
                "temporal_structure": "SUPPLEMENTARY_ONLY",
                "note": "Market / Temporal / governance **均不参与** Structural Status，仅作补充背景",
            },
        })

    counts = dict(collections.Counter(e["structural_status"] for e in exps))
    candidates_out.append({
        "candidate_id": cid,
        "display_name": cur_obj.get("display_name") or cur_obj.get("title") or cid,
        "macro_theme": cp["macro_theme"],
        "current_structural_profile": {
            "current_phase": cp["current_phase"], "phase_stage": cp["phase_stage"],
            "mechanism_drivers": cp["driver_profile"]["canonical_drivers"],
            "evidence_categories": sorted({e["event_type"].upper() for e in cp["event_profile"]}),
            "evidence_sequence": cp["evidence_sequence"],
            "evidence_sequence_status": cp["evidence_sequence_status"],
            "event_types": sorted({e["event_type"] for e in cp["event_profile"]}),
            "market_status": cp["market_status"], "temporal_status": cp["temporal_status"],
            "structural_gaps": cp["structural_gaps"],
        },
        "summary": counts,
        "explanations": exps,
    })

by_status = collections.Counter()
by_kind = collections.Counter()
for c in candidates_out:
    for e in c["explanations"]:
        by_status[e["structural_status"]] += 1
        by_kind[e["identity"]["historical_object_kind"]] += 1

res = {
    "artifact": "structural_analogy_explanations",
    "artifact_version": "0.5",
    "generated_by": "research/scripts/build_structural_analogy_explanation_v0_5.py",
    "supersedes_note": ("v0.1 / v0.2 / v0.3（`structural_analogy_explanations_v0_1/v0_2/v0_3.json`）**逐字节保留**；"
                        "本版**规则与契约语义不变**，唯一变化 = Historical Universe 扩容至 79 cycle，"
                        "并新增 `governance_context`（supplementary only）。"),
    "contract": {
        "consumer": "Product",
        "mode": "READ_ONLY —— Product **不得重新实现** Structural Analogy 规则",
        "rule_source": f"{RULE_SET}（唯一规则来源；**未修改**）",
        "rule_set_version": RULE_SET_VER,
        "driver_canonicalization_version": "0.4",
        "source_artifact": "research/research/reports/structural_analogy_research_v0_5.json",
    },
    "not_a": ["product UI", "user recommendation", "investment advice", "prediction",
              "trading signal", "similarity score", "weighted score", "confidence score",
              "ranking", "best historical analogue"],
    "snapshot_date": SNAPSHOT,
    "rule_set": RULE_SET,
    "rule_set_version": RULE_SET_VER,
    "changelog_v0_3_to_v0_4": [
        {"id": "U1", "issue": "消费 Driver Canonicalization v0.2（旧）",
         "fix": "改为消费 **Driver Canonicalization v0.5**（含剩余 5 项 collision 处理）"},
        {"id": "U2", "issue": "historical object identity 全部标为 campaign（E.3 缺陷）",
         "fix": "改为**按来源数组**判定：`historical_object_kind` / `historical_campaign_id` / "
                "`historical_research_candidate_id`（52 campaign + 27 research_candidate）"},
        {"id": "U3", "issue": "无 governance 元数据",
         "fix": "新增 `governance_context`（market_evidence_state / beta_level / peak|end 四态 / result），"
                "**明确标注 SUPPLEMENTARY_ONLY，不参与 Structural Status**"},
        {"id": "U4", "issue": "driver canonicalization 仅覆盖 17 cycle",
         "fix": "新增 `historical_driver_canonicalization_v0_2.json`（**同规则、全 universe**；"
                "已验证原 17 cycle 与 v0.1 逐条相同）"},
    ],
    "status_vocabulary": R3["correspondence_levels"],
    "dimension_vocabulary": {
        "lifecycle": ["MATCH", "PARTIAL", "MISMATCH", "UNKNOWN", "NOT_AVAILABLE"],
        "mechanism_driver": ["MATCH", "PARTIAL", "PERIPHERAL_OVERLAP", "MISMATCH",
                             "UNKNOWN", "NOT_AVAILABLE"],
        "evidence_sequence": ["SEQUENCE_MATCH", "SEQUENCE_PARTIAL", "SET_ONLY",
                              "SEQUENCE_MISMATCH", "UNKNOWN", "NOT_AVAILABLE"],
        "event_structure": ["MATCH", "PARTIAL", "MISMATCH", "NOT_AVAILABLE"],
    },
    "dimension_naming": {
        "rule": "产品文案**不要**把两者都简称「Driver」",
        "evidence_category": {"label_zh": "证据类别", "label_en": "Evidence Category",
                              "values": ["POLICY", "INDUSTRY", "COMPANY", "MARKET", "CAPITAL",
                                         "MACRO", "SENTIMENT", "OTHER"],
                              "meaning": "「公司公告」是一类**证据来源**"},
        "mechanism_driver": {"label_zh": "驱动机制", "label_en": "Mechanism Driver",
                             "values": R3["dimension_vocabulary"] and
                             ["POLICY_DRIVEN", "INDUSTRY_UPGRADE", "TECH_BREAKTHROUGH", "DEMAND_SURGE",
                              "SUPPLY_CONTRACTION", "VALUATION_RESET", "CYCLE_REVERSAL",
                              "EVENT_CATALYST", "UNKNOWN"],
                             "meaning": "「产业升级」是一个**机制判断**"},
    },
    "semantics": {
        "unknown_vs_absent": "`UNKNOWN` / `NOT_AVAILABLE` ≠ 现象不存在；表示**当前资料不足以编码**",
        "theme_relation_is_metadata": "`theme_relation` **不参与** Structural Status 判定，仅为背景 metadata",
        "ordering_semantics": "`explanations[]` 按 `historical_cycle_id` 升序 —— **这是稳定 identity 顺序，不是排名**",
        "supplementary_only": "Market / Temporal / governance 为 `SUPPLEMENTARY_ONLY`，不参与 Structural Status",
        "governance_gates": ("`governance-gates-v0.1`：`beta_level=1` **不等于** Alpha；"
                             "`A_SHARE_MARKET` **不等于**独立 Campaign；`result=weak` = 方向为负，"
                             "**不降低**参与结构类比的资格"),
        "product_must_not": ["重新实现规则", "计算 similarity / score / probability",
                             "按 status 排序或排名", "把 theme_relation 当作升降级依据",
                             "把 `UNKNOWN` / `NOT_AVAILABLE` 显示为「不相似」",
                             "把 governance 元数据（beta_level / market_evidence_state）当作 Structural Status 依据"],
    },
    "candidates": candidates_out,
    "coverage": {
        "candidates": len(candidates_out),
        "explanations": sum(len(c["explanations"]) for c in candidates_out),
        "by_status": {k: by_status[k] for k in R3["correspondence_levels"]},
        "by_historical_object_kind": dict(by_kind),
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
print("candidates:", len(candidates_out), "| explanations:", res["coverage"]["explanations"])
print("by_status:", res["coverage"]["by_status"])
print("by_kind:", res["coverage"]["by_historical_object_kind"])
