#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""validate_structural_analogy_v0_5.py —— Structural Analogy v0.4 **两层独立校验**（只读）。

★ 本校验器**不 import** 任何 SA builder / calibration 脚本；`level_v3()` 为**独立实现**。

## D1 Artifact Validation（结构 / 引用 / provenance / contract）
  A1  ruleset 仍为冻结的 `structural-analogy-ruleset-v0.3`
  A2  universe = 5 candidates × 79 historical objects = **395 pairs**
  A3  `historical_profiles` 与 export universe 集合相等
  A4  无重复 (candidate, cycle)；每 candidate 恰好 79 行
  A5  status ∈ 冻结等级词表
  A6  各维度取值 ∈ 冻结词表（含 evidence_sequence 维度状态 vs sequence_subtype **两套词表**）
  A7  **identity**：`historical_object_kind` 按来源数组正确；campaign_id / research_candidate_id 互斥且非空正确
  A8  explanations 与 research matrix 一一对应（395 条，状态一致，identity 一致）
  A9  provenance：rule_set / driver_canonicalization 版本指向当前版本
  A10 禁止字段（similarity / score / probability / ranking / prediction）
  A11 旧版本产物存在（v0.1 / v0.2 / v0.3 未被删除）

## D2 Independent Semantic Validation（重新实现 Rule Set v0.3，不 import builder）
  R1  逐行重算 `structural_status` 与 `strict`，要求与 artifact 完全一致（395 行）
  S1  `STRUCTURAL_PARTIAL ⇒ Driver ∈ {MATCH, PARTIAL}`
  S2  `STRUCTURAL_PARTIAL ⇒ Evidence Sequence ∈ {MATCH, PARTIAL}`
  S3  `STRUCTURAL_PARTIAL ⇒ 维度支持数 ≥ 2`
  S4  `Driver = MISMATCH ⇒ 状态 ∉ STRUCTURAL_*`
  S5  `Driver = PERIPHERAL_OVERLAP ⇒ 状态 ∉ STRUCTURAL_*`
  S6  `SUPPORTED ⇒ sequence_subtype ∈ {SEQUENCE_MATCH, SEQUENCE_PARTIAL}`
  S7  `SUPPORTED ⇒ lifecycle = MATCH` 且无核心 MISMATCH 且 `has_direct`
  S8  `SUPPORTED ⇒ Driver = MATCH` 或（`PARTIAL` 且 `MULTI_MECHANISM`）
  S9  `event_quality = SINGLE_TYPE_ONLY ⇒ event_structure ≠ PARTIAL`
  S10 `INSUFFICIENT_EVIDENCE ⇔ (n_av ≥ 2 或 Driver = NOT_AVAILABLE)`
  S11 结构支持不足 ⇒ SAME→`THEME_ONLY` / CROSS→`NO_VALID_CORRESPONDENCE`
  S12 Theme-Blind 重跑**不改变** Structural Status
  S13 负控制保持非结构状态
  S14 **全表 `Driver = MISMATCH` 的 `STRUCTURAL_PARTIAL` = 0**
  S15 ★ **driver 输入版本一致性**：artifact 的 `driver` 维度必须与**当前** Driver Canonicalization /
      Ledger **重新计算的结果完全一致** —— 防止「validator PASS 但 artifact 仍消费旧 driver」

退出码：0 = PASS（可有 WARN）；1 = FAIL。
用法：python research/scripts/validate_structural_analogy_v0_5.py
"""
from __future__ import annotations

import collections
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REP = os.path.join(ROOT, "research", "research", "reports")

R4P = os.path.join(REP, "structural_analogy_research_v0_5.json")
E4P = os.path.join(REP, "structural_analogy_explanations_v0_5.json")
CAN4P = os.path.join(REP, "historical_driver_canonicalization_v0_4.json")
LED4P = os.path.join(REP, "historical_driver_evidence_ledger_v0_4.json")
EXPP = os.path.join(ROOT, "exports", "timeline_export_v1.json")

EXPECT_RULESET_VER = "structural-analogy-ruleset-v0.3"
EXPECT_DRIVER_VER = "0.4"
LEVELS = ["STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL", "THEME_ONLY",
          "INSUFFICIENT_EVIDENCE", "NO_VALID_CORRESPONDENCE"]
GOOD = ("MATCH", "PARTIAL")
SEQ_OK = ("SEQUENCE_MATCH", "SEQUENCE_PARTIAL")
DRIVER_VOCAB = ["MATCH", "PARTIAL", "PERIPHERAL_OVERLAP", "MISMATCH", "UNKNOWN", "NOT_AVAILABLE"]
LC_VOCAB = ["MATCH", "PARTIAL", "MISMATCH", "UNKNOWN", "NOT_AVAILABLE", "COMPARISON_POINT_UNKNOWN"]
SEQ_STATUS_VOCAB = ["MATCH", "PARTIAL", "MISMATCH", "UNKNOWN", "NOT_AVAILABLE"]
SEQ_SUBTYPE_VOCAB = ["SEQUENCE_MATCH", "SEQUENCE_PARTIAL", "SET_ONLY", "SEQUENCE_MISMATCH",
                     "UNKNOWN", "NOT_AVAILABLE"]
EV_VOCAB = ["MATCH", "PARTIAL", "MISMATCH", "NOT_AVAILABLE"]
FORBIDDEN = re.compile(r"similarity_score|weighted_score|confidence_score|probability|"
                       r"\branking\b|best_analogue|prediction|win_rate|expected_return")

fails, warns = [], []


def fail(c, m):
    fails.append("%s  %s" % (c, m))


def warn(c, m):
    warns.append("%s  %s" % (c, m))


# ================================================================ D2：独立实现 Rule Set v0.3（不 import builder）
def level_v3_independent(d_lc, d_dr, d_sq, d_ev, seq_sub, has_direct, theme_rel, drv_quality):
    """Rule Set v0.3 §1 R1–R4 的**独立实现**。"""
    dims = [d_lc, d_dr, d_sq, d_ev]
    n_support = sum(1 for v in dims if v in GOOD)
    n_av = sum(1 for v in dims if v == "NOT_AVAILABLE")
    key_mismatch = (d_lc == "MISMATCH") or (d_dr == "MISMATCH") or (d_ev == "MISMATCH")
    drv_strong = (d_dr == "MATCH") or (d_dr == "PARTIAL" and drv_quality == "MULTI_MECHANISM")
    strict = (d_lc == "MATCH" and d_dr == "MATCH" and d_sq in GOOD and d_ev in GOOD
              and seq_sub in SEQ_OK and has_direct and not key_mismatch)
    non_lc = sum(1 for v in (d_dr, d_sq, d_ev) if v in GOOD)
    supported = (d_lc == "MATCH" and drv_strong and d_sq in GOOD and d_ev in GOOD
                 and seq_sub in SEQ_OK and has_direct and non_lc >= 2 and not key_mismatch)
    if n_av >= 2 or d_dr == "NOT_AVAILABLE":                      # R1
        return "INSUFFICIENT_EVIDENCE", strict
    if strict or supported:                                        # R2
        return "STRUCTURAL_SUPPORTED", strict
    if d_dr in GOOD and d_sq in GOOD and n_support >= 2:           # R3
        return "STRUCTURAL_PARTIAL", False
    return ("THEME_ONLY" if theme_rel == "SAME_MACRO_THEME" else "NO_VALID_CORRESPONDENCE"), False  # R4


# ================================================================ D2-S15：独立重算 driver 维度
def recompute_driver(exp, canon, ledger):
    """从**当前** export + canonicalization + ledger 独立重算每个 (candidate, cycle) 的 driver 维度。"""
    hist_drv = collections.defaultdict(lambda: collections.defaultdict(set))
    direct_cnt = collections.defaultdict(lambda: collections.Counter())
    for e in ledger:
        if e["bucket"] in ("start", "accelerator"):
            if e["mapping_status"] in ("DIRECT", "DERIVED") and e["canonical_driver"]:
                hist_drv[e["cycle_id"]][e["canonical_driver"]].add(e["mapping_status"])
            if e["mapping_status"] == "DIRECT" and e["canonical_driver"]:
                direct_cnt[e["cycle_id"]][e["canonical_driver"]] += 1
    primary = {}
    for cyc, c in direct_cnt.items():
        b = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
        primary[cyc] = b[0][0] if b and b[0][1] > 0 else "UNKNOWN"

    cur = json.load(io.open(os.path.join(ROOT, "research", "current", "current_candidates.json"),
                            encoding="utf-8"))
    cand_drv = {c["candidate_id"]: sorted(c.get("narrative_types") or []) for c in cur["candidates"]}

    out = {}
    for c in cur["candidates"]:
        cid = c["candidate_id"]
        for cyc in set(list(hist_drv.keys()) + [e["cycle_id"] for e in ledger]):
            cd = cand_drv.get(cid, [])
            hd = sorted(hist_drv.get(cyc, {}))
            if not cd or not hd:
                out[(cid, cyc)] = ("NOT_AVAILABLE", "NOT_AVAILABLE")
                continue
            ov = sorted(set(cd) & set(hd))
            prim = primary.get(cyc, "UNKNOWN")
            if not ov:
                out[(cid, cyc)] = ("MISMATCH", "NONE")
            elif set(cd) == set(hd) and len(ov) >= 2:
                if all(direct_cnt.get(cyc, {}).get(k, 0) >= 1 for k in ov):
                    out[(cid, cyc)] = ("MATCH", "CORE_EQUIVALENT")
                else:
                    out[(cid, cyc)] = ("PARTIAL", "SET_EQUAL_NO_PROVENANCE")
            elif len(ov) >= 2:
                out[(cid, cyc)] = ("PARTIAL", "MULTI_MECHANISM")
            elif prim != "UNKNOWN" and ov[0] == prim:
                out[(cid, cyc)] = ("PARTIAL", "PRIMARY_MECHANISM_OVERLAP")
            else:
                out[(cid, cyc)] = ("PERIPHERAL_OVERLAP", "PERIPHERAL_ONLY")
    return out


def _all_keys(o, acc=None):
    if acc is None:
        acc = set()
    if isinstance(o, dict):
        for k, v in o.items():
            acc.add(k)
            _all_keys(v, acc)
    elif isinstance(o, list):
        for v in o:
            _all_keys(v, acc)
    return acc


def main():
    for p in (R4P, E4P, CAN4P, LED4P):
        if not os.path.exists(p):
            fail("A0", "缺少产物: %s" % p)
            return report()

    r4 = json.load(io.open(R4P, encoding="utf-8"))
    e4 = json.load(io.open(E4P, encoding="utf-8"))
    can4 = json.load(io.open(CAN4P, encoding="utf-8"))
    led4 = json.load(io.open(LED4P, encoding="utf-8"))["entries"]
    exp = json.load(io.open(EXPP, encoding="utf-8"))

    # ---------------- D1 ----------------
    if r4.get("protocol", {}).get("protocol_version") != EXPECT_RULESET_VER:   # A1
        fail("A1", "protocol_version=%r 期望 %r" % (r4.get("protocol", {}).get("protocol_version"),
                                                    EXPECT_RULESET_VER))
    if r4.get("protocol", {}).get("driver_canonicalization_version") != EXPECT_DRIVER_VER:
        fail("A9", "driver_canonicalization_version=%r 期望 %r"
             % (r4.get("protocol", {}).get("driver_canonicalization_version"), EXPECT_DRIVER_VER))

    camp_ids = {c["campaign_id"] for c in exp["campaigns"]}
    rc_ids = {r["campaign_id"] for r in exp["research_candidates"]}
    hist_ids = camp_ids | rc_ids
    cand_ids = {c["candidate_id"] for c in r4["candidate_profiles"]}

    if len(r4["matrix"]) != len(hist_ids) * len(cand_ids):                      # A2
        fail("A2", "matrix=%d 期望 %d" % (len(r4["matrix"]), len(hist_ids) * len(cand_ids)))
    hp = {h["cycle_id"]: h for h in r4["historical_profiles"]}
    if set(hp) != hist_ids:                                                     # A3
        fail("A3", "historical_profiles 与 export 不一致：缺 %s / 多 %s"
             % (sorted(hist_ids - set(hp))[:5], sorted(set(hp) - hist_ids)[:5]))
    keys = [(m["candidate_id"], m["historical_cycle"]) for m in r4["matrix"]]
    dup = {k for k, v in collections.Counter(keys).items() if v > 1}
    if dup:
        fail("A4", "重复组合: %s" % sorted(dup)[:5])
    per = collections.Counter(m["candidate_id"] for m in r4["matrix"])
    if any(v != len(hist_ids) for v in per.values()):
        fail("A4", "每 candidate 行数应=%d，异常 %s" % (len(hist_ids), {k: v for k, v in per.items() if v != len(hist_ids)}))

    # A7 identity
    for h in r4["historical_profiles"]:
        cid = h["cycle_id"]
        want = "campaign" if cid in camp_ids else "research_candidate"
        if h.get("historical_object_kind") != want:
            fail("A7", "%s historical_object_kind=%r 期望 %r" % (cid, h.get("historical_object_kind"), want))
        if want == "campaign" and (h.get("campaign_id") != cid or h.get("research_candidate_id") is not None):
            fail("A7", "%s campaign identity 错误: %r / %r" % (cid, h.get("campaign_id"), h.get("research_candidate_id")))
        if want == "research_candidate" and (h.get("campaign_id") is not None or h.get("research_candidate_id") != cid):
            fail("A7", "%s RC identity 错误: %r / %r" % (cid, h.get("campaign_id"), h.get("research_candidate_id")))
    n_camp = sum(1 for h in r4["historical_profiles"] if h.get("historical_object_kind") == "campaign")
    if n_camp != len(camp_ids):
        fail("A7", "campaign 数=%d 期望 %d" % (n_camp, len(camp_ids)))

    for m in r4["matrix"]:
        cid, cyc = m["candidate_id"], m["historical_cycle"]
        tag = "%s×%s" % (cid, cyc)
        if m["structural_status"] not in LEVELS:                                # A5
            fail("A5", "%s status=%r" % (tag, m["structural_status"]))
        if m["driver"] not in DRIVER_VOCAB:                                     # A6
            fail("A6", "%s driver=%r" % (tag, m["driver"]))
        if m["lifecycle"] not in LC_VOCAB:
            fail("A6", "%s lifecycle=%r" % (tag, m["lifecycle"]))
        if m["evidence_sequence"] not in SEQ_STATUS_VOCAB:
            fail("A6", "%s evidence_sequence=%r" % (tag, m["evidence_sequence"]))
        if m["sequence_subtype"] not in SEQ_SUBTYPE_VOCAB:
            fail("A6", "%s sequence_subtype=%r" % (tag, m["sequence_subtype"]))
        if m["event_structure"] not in EV_VOCAB:
            fail("A6", "%s event_structure=%r" % (tag, m["event_structure"]))
        if m.get("historical_object_kind") != ("campaign" if cyc in camp_ids else "research_candidate"):
            fail("A7", "%s matrix.historical_object_kind 错误" % tag)

    # A8 explanations ↔ matrix
    m4 = {(m["candidate_id"], m["historical_cycle"]): m for m in r4["matrix"]}
    ex_all = [e for c in e4["candidates"] for e in c["explanations"]]
    if len(ex_all) != len(r4["matrix"]):
        fail("A8", "explanations=%d 与 matrix=%d 不等" % (len(ex_all), len(r4["matrix"])))
    for c in e4["candidates"]:
        for e in c["explanations"]:
            k = (c["candidate_id"], e["identity"]["historical_cycle_id"])
            m = m4.get(k)
            if not m:
                fail("A8", "explanations 有 matrix 中不存在的组合 %s" % (k,))
                continue
            if m["structural_status"] != e["structural_status"]:
                fail("A8", "%s 状态不一致 matrix=%s explanations=%s" % (k, m["structural_status"], e["structural_status"]))
            if e["identity"]["historical_object_kind"] != m["historical_object_kind"]:
                fail("A8", "%s identity 不一致" % (k,))
            if e["identity"]["historical_object_kind"] == "research_candidate" \
                    and e["identity"]["historical_campaign_id"] is not None:
                fail("A8", "%s RC 的 historical_campaign_id 应为 null" % (k,))
            if e["identity"]["historical_object_kind"] == "campaign" \
                    and e["identity"]["historical_research_candidate_id"] is not None:
                fail("A8", "%s campaign 的 historical_research_candidate_id 应为 null" % (k,))
    # A9 provenance
    if e4.get("contract", {}).get("source_artifact") != "research/research/reports/structural_analogy_research_v0_5.json":
        fail("A9", "explanations contract.source_artifact=%r" % e4.get("contract", {}).get("source_artifact"))
    if e4.get("contract", {}).get("driver_canonicalization_version") != EXPECT_DRIVER_VER:
        fail("A9", "explanations driver 版本=%r" % e4.get("contract", {}).get("driver_canonicalization_version"))
    # A10 forbidden
    for nm, obj in (("research_v0_5", r4), ("explanations_v0_5", e4)):
        hits = {k for k in _all_keys(obj) if FORBIDDEN.search(k)}
        if hits:
            fail("A10", "%s 出现禁止字段 %s" % (nm, sorted(hits)))
    # A11 旧版本存在
    for f in ("structural_analogy_research_v0_1.json", "structural_analogy_research_v0_2.json",
              "structural_analogy_research_v0_3.json", "structural_analogy_explanations_v0_1.json",
              "structural_analogy_explanations_v0_2.json", "structural_analogy_explanations_v0_3.json",
              "historical_driver_canonicalization_v0_1.json", "historical_driver_canonicalization_v0_2.json",
              "historical_driver_canonicalization_v0_3.json", "time_observation_patterns_v0_1.json"):
        if not os.path.exists(os.path.join(REP, f)):
            fail("A11", "旧版本产物缺失（不得删除）: %s" % f)

    # ---------------- D2 ----------------
    n_checked = 0
    for m in r4["matrix"]:
        cid, cyc = m["candidate_id"], m["historical_cycle"]
        tag = "%s×%s" % (cid, cyc)
        h = hp[cyc]
        has_direct = h.get("driver_direct_count", 0) > 0
        got, got_strict = level_v3_independent(m["lifecycle"], m["driver"], m["evidence_sequence"],
                                               m["event_structure"], m["sequence_subtype"],
                                               has_direct, m["theme_relation"], m["driver_quality"])
        n_checked += 1
        if got != m["structural_status"] or got_strict != bool(m["strict_structural_supported"]):   # R1
            fail("R1", "%s 独立重算不一致 artifact=%s/%s recomputed=%s/%s"
                 % (tag, m["structural_status"], m["strict_structural_supported"], got, got_strict))
        # S1–S3
        dims = [m["lifecycle"], m["driver"], m["evidence_sequence"], m["event_structure"]]
        n_sup = sum(1 for v in dims if v in GOOD)
        n_av = sum(1 for v in dims if v == "NOT_AVAILABLE")
        st = m["structural_status"]
        if st == "STRUCTURAL_PARTIAL":
            if m["driver"] not in GOOD:
                fail("S1", "%s PARTIAL 但 driver=%s" % (tag, m["driver"]))
            if m["evidence_sequence"] not in GOOD:
                fail("S2", "%s PARTIAL 但 seq=%s" % (tag, m["evidence_sequence"]))
            if n_sup < 2:
                fail("S3", "%s PARTIAL 但支持维度=%d" % (tag, n_sup))
        if m["driver"] == "MISMATCH" and st.startswith("STRUCTURAL"):           # S4
            fail("S4", "%s driver=MISMATCH 却为 %s" % (tag, st))
        if m["driver"] == "PERIPHERAL_OVERLAP" and st.startswith("STRUCTURAL"):  # S5
            fail("S5", "%s PERIPHERAL 却为 %s" % (tag, st))
        if st == "STRUCTURAL_SUPPORTED":                                        # S6/S7/S8
            if m["sequence_subtype"] not in SEQ_OK:
                fail("S6", "%s SUPPORTED 但 subtype=%s" % (tag, m["sequence_subtype"]))
            if m["lifecycle"] != "MATCH" or not has_direct:
                fail("S7", "%s SUPPORTED 但 lifecycle=%s / has_direct=%s" % (tag, m["lifecycle"], has_direct))
            if "MISMATCH" in (m["lifecycle"], m["driver"], m["event_structure"]):
                fail("S7", "%s SUPPORTED 但存在核心 MISMATCH" % tag)
            if not (m["driver"] == "MATCH" or (m["driver"] == "PARTIAL" and m["driver_quality"] == "MULTI_MECHANISM")):
                fail("S8", "%s SUPPORTED 但 driver=%s/%s" % (tag, m["driver"], m["driver_quality"]))
        if m.get("event_quality") == "SINGLE_TYPE_ONLY" and m["event_structure"] == "PARTIAL":  # S9
            fail("S9", "%s SINGLE_TYPE_ONLY 作为 event PARTIAL" % tag)
        is_ins = (n_av >= 2) or (m["driver"] == "NOT_AVAILABLE")                 # S10
        if (st == "INSUFFICIENT_EVIDENCE") != is_ins:
            fail("S10", "%s INSUFFICIENT 判据不一致 status=%s 判据=%s" % (tag, st, is_ins))
        if st in ("THEME_ONLY", "NO_VALID_CORRESPONDENCE"):                      # S11
            want = "THEME_ONLY" if m["theme_relation"] == "SAME_MACRO_THEME" else "NO_VALID_CORRESPONDENCE"
            if st != want:
                fail("S11", "%s theme=%s 但 status=%s" % (tag, m["theme_relation"], st))
    # S12 theme-blind
    tb = r4.get("regression_controls", {}).get("theme_blind", {})
    if tb.get("structural_status_changed", 0) != 0:
        fail("S12", "theme-blind 改变 %d 个 Structural Status" % tb.get("structural_status_changed"))
    # S13 negative controls
    for n in r4.get("regression_controls", {}).get("negative_controls", []):
        if not n.get("not_upgraded"):
            fail("S13", "负控制被升级 %s×%s → %s" % (n["candidate_id"], n["historical_cycle"], n["v0_3"]))
    # S14
    bad14 = [m for m in r4["matrix"] if m["driver"] == "MISMATCH" and m["structural_status"] == "STRUCTURAL_PARTIAL"]
    if bad14:
        fail("S14", "driver=MISMATCH → PARTIAL 有 %d 条" % len(bad14))
    # S15 ★ driver 输入版本一致性
    drv = recompute_driver(exp, can4, led4)
    mism = 0
    for m in r4["matrix"]:
        want = drv.get((m["candidate_id"], m["historical_cycle"]))
        if want is None:
            continue
        if (m["driver"], m["driver_quality"]) != want:
            mism += 1
            if mism <= 5:
                fail("S15", "%s×%s artifact driver=%s/%s 与当前 canonicalization v0.4 重算=%s/%s 不一致"
                     % (m["candidate_id"], m["historical_cycle"], m["driver"], m["driver_quality"],
                        want[0], want[1]))
    if mism > 5:
        fail("S15", "…另有 %d 条 driver 版本不一致" % (mism - 5))
    if can4.get("artifact_version") != EXPECT_DRIVER_VER:
        fail("S15", "canonicalization artifact_version=%r 期望 %r" % (can4.get("artifact_version"), EXPECT_DRIVER_VER))

    return report(r4, e4, n_checked, len(drv), mism)


def report(r4=None, e4=None, n_checked=0, n_drv=0, mism=0):
    print("=== validate_structural_analogy_v0_5.py（两层独立校验）===")
    if r4:
        s = r4["summary"]
        print("D1 artifact : %d cycles | %d candidates | %d pairs | explanations %d"
              % (s["historical_cycles_examined"], s["current_candidates"], s["pairs"],
                 sum(len(c["explanations"]) for c in e4["candidates"])))
        print("D1 identity : campaign %d / research_candidate %d"
              % (sum(1 for h in r4["historical_profiles"] if h["historical_object_kind"] == "campaign"),
                 sum(1 for h in r4["historical_profiles"] if h["historical_object_kind"] == "research_candidate")))
        print("D1 by_status:", s["by_status"])
        print("D1 STRICT   :", s["strict_structural_supported"])
        print("D2 独立重算 : %d / %d 行" % (n_checked, len(r4["matrix"])))
        print("D2 S14      : driver=MISMATCH → PARTIAL = %d（必须 0）"
              % len([m for m in r4["matrix"] if m["driver"] == "MISMATCH" and m["structural_status"] == "STRUCTURAL_PARTIAL"]))
        print("D2 S15      : driver 版本一致性 —— 重算 %d 组合，不一致 %d（必须 0）" % (n_drv, mism))
    print("-" * 66)
    for w in warns:
        print("WARN  " + w)
    for f in fails:
        print("FAIL  " + f)
    if warns:
        print("-" * 66)
    print()
    print("结果: %s（FAIL %d / WARN %d）" % ("PASS" if not fails else "FAIL", len(fails), len(warns)))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
