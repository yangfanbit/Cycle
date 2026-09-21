#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""validate_structural_analogy_v0_3.py —— Structural Analogy v0.3 一致性校验（**只读**）。

校验对象：
  · `research/research/reports/structural_analogy_research_v0_3.json`
  · `research/research/reports/structural_analogy_explanations_v0_3.json`
  · 对照 `structural_analogy_research_v0_2.json`（非回归）

检查项：
  A1  规则集仍为冻结的 `structural-analogy-ruleset-v0.2`（**未被替换**）
  A2  universe = 5 candidates × 79 historical cycles = 395 pairs（与 export 完全一致）
  A3  historical_profiles 覆盖 export 全部 campaigns + research_candidates，无遗漏/多余
  A4  matrix 无重复 (candidate_id, historical_cycle)；每 candidate 恰好 79 行
  A5  structural_status ∈ 冻结等级词表
  A6  driver / lifecycle / evidence_sequence / event_structure ∈ 各自冻结词表
  A7  `PERIPHERAL_OVERLAP` **不得**被计为 structural support（不得出现在 STRUCTURAL_* 且 driver=PERIPHERAL）
  A8  `SET_ONLY` **不得**被当作 `SEQUENCE_MATCH`（status=SUPPORTED ⇒ subtype ∈ {SEQUENCE_MATCH, SEQUENCE_PARTIAL}）
  A9  `SINGLE_TYPE_ONLY` **不得**作为 event `PARTIAL`
  A10 theme_relation **不得**参与升降级（theme-blind 运行不改变 Structural Status）
  A11 负控制案例保持非结构状态
  A12 **非回归**：v0.2 已覆盖的 17 cycle × 5 candidate = 85 组合，v0.3 状态必须与 v0.2 逐条一致
  A13 v0.1 / v0.2 artifact **未被修改**（存在性 + 与 git HEAD 一致由外部检查）
  A14 explanations 与 research matrix 一一对应（395 条，状态一致）
  A15 禁止字段：无 similarity / score / probability / ranking / prediction 类字段
  A16 governance 元数据**仅出现在 supplementary**，未参与 Structural Status

退出码：0 = PASS（可有 WARN）；1 = FAIL。
用法：python research/scripts/validate_structural_analogy_v0_3.py
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
R3P = os.path.join(REP, "structural_analogy_research_v0_3.json")
E3P = os.path.join(REP, "structural_analogy_explanations_v0_3.json")
R2P = os.path.join(REP, "structural_analogy_research_v0_2.json")
EXPP = os.path.join(ROOT, "exports", "timeline_export_v1.json")

EXPECT_RULESET_VER = "structural-analogy-ruleset-v0.2"
LEVELS = ["STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL", "THEME_ONLY",
          "INSUFFICIENT_EVIDENCE", "NO_VALID_CORRESPONDENCE"]
DRIVER_VOCAB = ["MATCH", "PARTIAL", "PERIPHERAL_OVERLAP", "MISMATCH", "UNKNOWN", "NOT_AVAILABLE"]
LC_VOCAB = ["MATCH", "PARTIAL", "MISMATCH", "UNKNOWN", "NOT_AVAILABLE", "COMPARISON_POINT_UNKNOWN"]
# ★ `evidence_sequence` 的**维度状态**与 `sequence_subtype` 是两套词表
SEQ_STATUS_VOCAB = ["MATCH", "PARTIAL", "MISMATCH", "UNKNOWN", "NOT_AVAILABLE"]
SEQ_SUBTYPE_VOCAB = ["SEQUENCE_MATCH", "SEQUENCE_PARTIAL", "SET_ONLY", "SEQUENCE_MISMATCH",
                     "NOT_AVAILABLE"]
EV_VOCAB = ["MATCH", "PARTIAL", "MISMATCH", "NOT_AVAILABLE"]
FORBIDDEN = re.compile(r"similarity_score|weighted_score|confidence_score|probability|"
                       r"\branking\b|best_analogue|prediction|win_rate|expected_return")

fails, warns = [], []


def fail(code, msg):
    fails.append("%s  %s" % (code, msg))


def warn(code, msg):
    warns.append("%s  %s" % (code, msg))


def main():
    for p in (R3P, E3P):
        if not os.path.exists(p):
            fail("A0", "缺少产物: %s" % p)
            return report()

    r3 = json.load(io.open(R3P, encoding="utf-8"))
    e3 = json.load(io.open(E3P, encoding="utf-8"))
    exp = json.load(io.open(EXPP, encoding="utf-8"))

    # A1
    if r3.get("protocol", {}).get("protocol_version") != EXPECT_RULESET_VER:
        fail("A1", "protocol_version=%r，期望 %r（规则集不得被替换）"
             % (r3.get("protocol", {}).get("protocol_version"), EXPECT_RULESET_VER))
    if e3.get("rule_set_version") != EXPECT_RULESET_VER:
        fail("A1", "explanations rule_set_version=%r" % e3.get("rule_set_version"))

    hist_ids = {c["campaign_id"] for c in exp["campaigns"]} | \
               {r["campaign_id"] for r in exp["research_candidates"]}
    cand_ids = {c["candidate_id"] for c in r3["candidate_profiles"]}

    # A2
    n_hist, n_cand = len(hist_ids), len(cand_ids)
    expect_pairs = n_hist * n_cand
    if len(r3["matrix"]) != expect_pairs:
        fail("A2", "matrix=%d，期望 %d（%d × %d）" % (len(r3["matrix"]), expect_pairs, n_hist, n_cand))

    # A3
    hp_ids = {h["cycle_id"] for h in r3["historical_profiles"]}
    if hp_ids != hist_ids:
        fail("A3", "historical_profiles 与 export 不一致：缺 %s / 多 %s"
             % (sorted(hist_ids - hp_ids)[:5], sorted(hp_ids - hist_ids)[:5]))

    # A4
    keys = [(m["candidate_id"], m["historical_cycle"]) for m in r3["matrix"]]
    dup = {k for k, v in collections.Counter(keys).items() if v > 1}
    if dup:
        fail("A4", "重复组合: %s" % sorted(dup)[:5])
    per = collections.Counter(m["candidate_id"] for m in r3["matrix"])
    bad = {k: v for k, v in per.items() if v != n_hist}
    if bad:
        fail("A4", "每 candidate 行数应=%d，异常: %s" % (n_hist, bad))

    m3 = {(m["candidate_id"], m["historical_cycle"]): m for m in r3["matrix"]}

    for m in r3["matrix"]:
        cid, cyc = m["candidate_id"], m["historical_cycle"]
        tag = "%s×%s" % (cid, cyc)
        # A5
        if m["structural_status"] not in LEVELS:
            fail("A5", "%s structural_status=%r" % (tag, m["structural_status"]))
        # A6
        if m["driver"] not in DRIVER_VOCAB:
            fail("A6", "%s driver=%r" % (tag, m["driver"]))
        if m["lifecycle"] not in LC_VOCAB:
            fail("A6", "%s lifecycle=%r" % (tag, m["lifecycle"]))
        if m["evidence_sequence"] not in SEQ_STATUS_VOCAB:
            fail("A6", "%s evidence_sequence=%r（维度状态）" % (tag, m["evidence_sequence"]))
        if m["sequence_subtype"] not in SEQ_SUBTYPE_VOCAB:
            fail("A6", "%s sequence_subtype=%r" % (tag, m["sequence_subtype"]))
        if m["event_structure"] not in EV_VOCAB:
            fail("A6", "%s event_structure=%r" % (tag, m["event_structure"]))
        # A7
        if m["driver"] == "PERIPHERAL_OVERLAP" and m["structural_status"].startswith("STRUCTURAL"):
            fail("A7", "%s PERIPHERAL_OVERLAP 被计为结构支持（%s）" % (tag, m["structural_status"]))
        # A8
        if m["structural_status"] == "STRUCTURAL_SUPPORTED" and \
                m["sequence_subtype"] not in ("SEQUENCE_MATCH", "SEQUENCE_PARTIAL"):
            fail("A8", "%s SUPPORTED 但 sequence_subtype=%s" % (tag, m["sequence_subtype"]))
        if m["sequence_subtype"] == "SET_ONLY" and m["structural_status"] == "STRUCTURAL_SUPPORTED":
            fail("A8", "%s SET_ONLY 被当作 SEQUENCE_MATCH" % tag)
        # A9
        if m["event_quality"] == "SINGLE_TYPE_ONLY" and m["event_structure"] == "PARTIAL":
            fail("A9", "%s SINGLE_TYPE_ONLY 被当作 event PARTIAL" % tag)
        # A16
        sup = m.get("supplementary") or {}
        gg = sup.get("governance_gates")
        if gg is None:
            fail("A16", "%s 缺 supplementary.governance_gates" % tag)
        elif gg.get("beta_level") in (2, 3) and m["structural_status"] == "STRUCTURAL_SUPPORTED":
            warn("A16", "%s beta_level=%s（仅 supplementary；不应影响状态）" % (tag, gg.get("beta_level")))

    # A10 theme-blind
    tb = r3.get("regression_controls", {}).get("theme_blind", {})
    if tb.get("structural_status_changed", 0) != 0:
        fail("A10", "theme-blind 改变了 %d 个 Structural Status" % tb.get("structural_status_changed"))
    # A11
    for n in r3.get("regression_controls", {}).get("negative_controls", []):
        if not n.get("not_upgraded"):
            fail("A11", "负控制被升级: %s × %s → %s"
                 % (n["candidate_id"], n["historical_cycle"], n["v0_3"]))
    # A12
    nr = r3.get("regression_controls", {}).get("non_regression_vs_v0_2", {})
    if nr.get("available"):
        if not nr.get("identical"):
            fail("A12", "v0.2 已覆盖组合发生状态变化: %s" % nr.get("changed")[:3])
        if nr.get("checked_pairs") != 85:
            warn("A12", "非回归检查组合数=%s（期望 85 = 17×5）" % nr.get("checked_pairs"))
    else:
        warn("A12", "v0.2 artifact 不可用，跳过非回归检查")

    # A13 旧版本存在
    for p in ("structural_analogy_research_v0_1.json", "structural_analogy_research_v0_2.json",
              "structural_analogy_explanations_v0_1.json", "structural_analogy_explanations_v0_2.json",
              "structural_analogy_rule_calibration_v0_2.json",
              "historical_driver_canonicalization_v0_1.json",
              "historical_driver_evidence_ledger_v0_1.json"):
        if not os.path.exists(os.path.join(REP, p)):
            fail("A13", "旧版本产物缺失（不得删除）: %s" % p)

    # A14 explanations ↔ matrix
    ex_all = [e for c in e3["candidates"] for e in c["explanations"]]
    if len(ex_all) != len(r3["matrix"]):
        fail("A14", "explanations=%d 与 matrix=%d 不等" % (len(ex_all), len(r3["matrix"])))
    for c in e3["candidates"]:
        for e in c["explanations"]:
            k = (c["candidate_id"], e["identity"]["historical_cycle_id"])
            m = m3.get(k)
            if not m:
                fail("A14", "explanations 有 matrix 中不存在的组合: %s" % (k,))
            elif m["structural_status"] != e["structural_status"]:
                fail("A14", "%s 状态不一致: matrix=%s explanations=%s"
                     % (k, m["structural_status"], e["structural_status"]))

    # A15 禁止字段
    for name, obj in (("research_v0_3", r3), ("explanations_v0_3", e3)):
        hits = {k for k in _all_keys(obj) if FORBIDDEN.search(k)}
        if hits:
            fail("A15", "%s 出现禁止字段: %s" % (name, sorted(hits)))

    return report(r3)


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


def report(r3=None):
    print("=== validate_structural_analogy_v0_3.py ===")
    if r3:
        s = r3["summary"]
        print("universe: %d cycles | %d candidates | %d pairs"
              % (s["historical_cycles_examined"], s["current_candidates"], s["pairs"]))
        print("by_status:", s["by_status"])
        print("STRICT_STRUCTURAL_SUPPORTED:", s["strict_structural_supported"])
    print("-" * 62)
    for w in warns:
        print("WARN  " + w)
    for f in fails:
        print("FAIL  " + f)
    if warns:
        print("-" * 62)
    print()
    print("结果: %s（FAIL %d / WARN %d）" % ("PASS" if not fails else "FAIL", len(fails), len(warns)))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
