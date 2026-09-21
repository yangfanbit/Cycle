#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""validate_structural_analogy_semantics.py —— Structural Analogy **Rule Set v0.3 语义一致性校验**（只读）。

**动机**：SA v0.3 的 `validate_structural_analogy_v0_3.py`（A1–A16）只检查**结构/引用/契约一致性**，
**不重算规则语义** —— 因此出现「Validator PASS 但规则语义与 Rule Set 文本不一致」（E.1）时无法发现。
本校验器补上这一层。

**方法（两层，互相独立）**

  **第 1 层 — 独立重算（Independent Recompute）**
    本文件**从 Rule Set v0.3 文本独立重新实现** `level_v3()`（**不 import** builder 的实现），
    对 `structural_analogy_rule_calibration_v0_3.json` 中 4 组运行（A/B/C/D）的每一行**逐行重算**
    `structural_status` 与 `strict_structural_supported`，并要求**与产物完全一致**。

  **第 2 层 — 语义不变量（Semantic Invariants）**
    直接从 Rule Set v0.3 的硬约束派生，**不依赖任何实现**：
      S1  `STRUCTURAL_PARTIAL` ⇒ `Driver ∈ {MATCH, PARTIAL}`          （§4-1，★ E.1 修复的判据）
      S2  `STRUCTURAL_PARTIAL` ⇒ `Evidence Sequence ∈ {MATCH, PARTIAL}`（§4-2）
      S3  `STRUCTURAL_PARTIAL` ⇒ 维度支持数 ≥ 2                        （§4-3）
      S4  `Driver = MISMATCH` ⇒ 状态 ∉ STRUCTURAL_*                    （§4 硬约束 / §11 新增禁止项）
      S5  `Driver = PERIPHERAL_OVERLAP` ⇒ 状态 ∉ STRUCTURAL_*          （§2.2 / §3.3）
      S6  `STRUCTURAL_SUPPORTED` ⇒ `sequence_subtype ∈ {SEQUENCE_MATCH, SEQUENCE_PARTIAL}`（§3-3 / §5）
      S7  `STRUCTURAL_SUPPORTED` ⇒ `lifecycle = MATCH` 且 无核心 MISMATCH 且 `has_direct`（§3-1/6/8）
      S8  `STRUCTURAL_SUPPORTED` ⇒ `Driver = MATCH` 或（`PARTIAL` 且 `quality = MULTI_MECHANISM`）（§3-2）
      S9  `event_quality = SINGLE_TYPE_ONLY` ⇒ `event_structure ≠ PARTIAL`（§2.4 硬约束）
      S10 `INSUFFICIENT_EVIDENCE` ⇔（`NOT_AVAILABLE` 维度 ≥2 或 `Driver = NOT_AVAILABLE`）（§6 / R1）
      S11 结构支持不足 ⇒ `SAME_MACRO_THEME → THEME_ONLY` / `CROSS_MACRO_THEME → NO_VALID_CORRESPONDENCE`（§5 / R4）
      S12 Theme-Blind 重跑**不改变** `Structural Status`（§8）
      S13 负控制保持非结构状态（§7）
      S14 **全表 `Driver = MISMATCH` 的 `STRUCTURAL_PARTIAL` 计数必须为 0**（★ E.1 修复的最终判据）

**退出码**：0 = PASS（可有 WARN）；1 = FAIL。
用法：python research/scripts/validate_structural_analogy_semantics.py
"""
from __future__ import annotations

import collections
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REP = os.path.join(ROOT, "research", "research", "reports")
CAL3 = os.path.join(REP, "structural_analogy_rule_calibration_v0_3.json")
C3 = os.path.join(REP, "historical_driver_canonicalization_v0_3.json")

LEVELS = ["STRUCTURAL_SUPPORTED", "STRUCTURAL_PARTIAL", "THEME_ONLY",
          "INSUFFICIENT_EVIDENCE", "NO_VALID_CORRESPONDENCE"]
GOOD = ("MATCH", "PARTIAL")
SEQ_OK = ("SEQUENCE_MATCH", "SEQUENCE_PARTIAL")

fails, warns = [], []


def fail(code, msg):
    fails.append("%s  %s" % (code, msg))


def warn(code, msg):
    warns.append("%s  %s" % (code, msg))


# ================================================================ 第 1 层：独立重算
# ★ 本实现**直接依据 Rule Set v0.3 文本**（§1 R1–R4 / §3 / §4 / §5 / §6）独立编写，
#   **不 import** build_structural_analogy_rule_calibration_v0_3.py 的实现。
def _b(v):
    """CSV 布尔解析（'True'/'False' 字符串 → bool）。★ 不得用 bool(str)。"""
    return str(v).strip().lower() == "true"


def level_v2_independent(r):
    """Rule Set v0.2 实现（逐行复制 Calibration v0.2，**含 fallback**）—— 用于 A / B 组复核。"""
    d_lc, d_dr, d_sq, d_ev = r["lifecycle"], r["driver"], r["evidence_sequence"], r["event_structure"]
    sub, drv_q = r["sequence_subtype"], r.get("driver_quality")
    has_direct = _b(r["has_direct_driver_evidence"])
    theme_rel = r["theme_relation"]
    dims = [d_lc, d_dr, d_sq, d_ev]
    n_support = sum(1 for v in dims if v in GOOD)
    n_av = sum(1 for v in dims if v == "NOT_AVAILABLE")
    key_mismatch = (d_lc == "MISMATCH") or (d_dr == "MISMATCH") or (d_ev == "MISMATCH")
    drv_strong = (d_dr == "MATCH") or (d_dr == "PARTIAL" and drv_q == "MULTI_MECHANISM")
    strict = (d_lc == "MATCH" and d_dr == "MATCH" and d_sq in GOOD and d_ev in GOOD
              and sub in SEQ_OK and has_direct and not key_mismatch)
    non_lc = sum(1 for v in (d_dr, d_sq, d_ev) if v in GOOD)
    supported = (d_lc == "MATCH" and drv_strong and d_sq in GOOD and d_ev in GOOD
                 and sub in SEQ_OK and has_direct and non_lc >= 2 and not key_mismatch)
    if n_av >= 2 or d_dr == "NOT_AVAILABLE":
        return "INSUFFICIENT_EVIDENCE", strict
    if strict or supported:
        return "STRUCTURAL_SUPPORTED", strict
    if d_dr in GOOD and d_sq in GOOD and n_support >= 2:
        return "STRUCTURAL_PARTIAL", False
    if d_dr == "PERIPHERAL_OVERLAP" or (d_lc in GOOD and n_support <= 1):
        return ("THEME_ONLY" if theme_rel == "SAME_MACRO_THEME" else "NO_VALID_CORRESPONDENCE"), False
    if n_support >= 2:                      # ← v0.2 的 fallback
        return "STRUCTURAL_PARTIAL", False
    return "NO_VALID_CORRESPONDENCE", False


def level_v3_independent(r):
    d_lc = r["lifecycle"]
    d_dr = r["driver"]
    d_sq = r["evidence_sequence"]
    d_ev = r["event_structure"]
    sub = r["sequence_subtype"]
    drv_q = r.get("driver_quality")
    has_direct = _b(r["has_direct_driver_evidence"])
    theme_rel = r["theme_relation"]

    dims = [d_lc, d_dr, d_sq, d_ev]
    n_support = sum(1 for v in dims if v in GOOD)
    n_av = sum(1 for v in dims if v == "NOT_AVAILABLE")
    key_mismatch = (d_lc == "MISMATCH") or (d_dr == "MISMATCH") or (d_ev == "MISMATCH")
    drv_strong = (d_dr == "MATCH") or (d_dr == "PARTIAL" and drv_q == "MULTI_MECHANISM")
    strict = (d_lc == "MATCH" and d_dr == "MATCH" and d_sq in GOOD and d_ev in GOOD
              and sub in SEQ_OK and has_direct and not key_mismatch)
    non_lc = sum(1 for v in (d_dr, d_sq, d_ev) if v in GOOD)
    supported = (d_lc == "MATCH" and drv_strong and d_sq in GOOD and d_ev in GOOD
                 and sub in SEQ_OK and has_direct and non_lc >= 2 and not key_mismatch)

    # R1
    if n_av >= 2 or d_dr == "NOT_AVAILABLE":
        return "INSUFFICIENT_EVIDENCE", strict
    # R2
    if strict or supported:
        return "STRUCTURAL_SUPPORTED", strict
    # R3 —— Driver ∈ {MATCH, PARTIAL} 为硬前提（无 fallback）
    if d_dr in GOOD and d_sq in GOOD and n_support >= 2:
        return "STRUCTURAL_PARTIAL", False
    # R4
    return ("THEME_ONLY" if theme_rel == "SAME_MACRO_THEME" else "NO_VALID_CORRESPONDENCE"), False


def main():
    if not os.path.exists(CAL3):
        fail("R0", "缺少 Calibration v0.3: %s" % CAL3)
        return report()

    cal = json.load(io.open(CAL3, encoding="utf-8"))
    runs = cal.get("_runs")  # 若产物未内嵌逐行数据，则从各段 detail 重建

    # ---- 从 calibration 产物重建 4 组逐行结果 ----
    # A/B/C/D 的逐行状态并不全部内嵌；此处以 CSV 为准（含 A 与 D），
    # 并对 C 组用「E1b」段落 + 独立重算复核。
    csv_path = os.path.join(REP, "structural_analogy_rule_calibration_pairs_v0_3.csv")
    if not os.path.exists(csv_path):
        fail("R0", "缺少 calibration CSV: %s" % csv_path)
        return report()

    import csv as _csv
    rows = list(_csv.DictReader(io.open(csv_path, encoding="utf-8")))
    if not rows:
        fail("R0", "calibration CSV 为空")
        return report()

    RUNS = ["A", "B", "C", "D"]
    by_run = collections.defaultdict(list)
    for r in rows:
        by_run[r["run"]].append(r)
    if sorted(by_run) != RUNS:
        fail("R0", "CSV run 标签应为 %s，实际 %s" % (RUNS, sorted(by_run)))
        return report()
    n_pairs = len(by_run["D"])
    if len(by_run["D"]) != 395:
        fail("R0", "D 组行数应为 395，实际 %d" % len(by_run["D"]))

    # ---- 第 1 层：对 **全部 4 组运行** 逐行独立重算 ----
    n_checked = 0
    mismatches = []
    for run in RUNS:
        for r in by_run[run]:
            exp_status = r["structural_status"]
            exp_strict = _b(r["strict_structural_supported"])
            got, got_strict = level_v3_independent(r) if run in ("C", "D") \
                else level_v2_independent(r)
            n_checked += 1
            if got != exp_status or got_strict != exp_strict:
                mismatches.append({
                    "run": run, "candidate_id": r["candidate_id"],
                    "historical_cycle": r["historical_cycle"],
                    "artifact": exp_status, "recomputed": got,
                    "artifact_strict": exp_strict, "recomputed_strict": got_strict,
                })
    if mismatches:
        for m in mismatches[:10]:
            fail("R1", "[%s] 独立重算不一致 %s×%s：artifact=%s / recomputed=%s"
                 % (m["run"], m["candidate_id"], m["historical_cycle"],
                    m["artifact"], m["recomputed"]))
        if len(mismatches) > 10:
            fail("R1", "…另有 %d 条不一致" % (len(mismatches) - 10))

    rows = by_run["D"]   # 第 2 层语义不变量针对 v0.3 最终结果（D 组）
    for r in rows:
        tag = "%s×%s" % (r["candidate_id"], r["historical_cycle"])
        st = r["structural_status"]
        d_dr = r["driver"]
        d_sq = r["evidence_sequence"]
        d_ev = r["event_structure"]
        d_lc = r["lifecycle"]
        sub = r["sequence_subtype"]
        q = r["driver_quality"]
        has_direct = _b(r["has_direct_driver_evidence"])
        tr = r["theme_relation"]
        dims = [d_lc, d_dr, d_sq, d_ev]
        n_support = sum(1 for v in dims if v in GOOD)
        n_av = sum(1 for v in dims if v == "NOT_AVAILABLE")

        # S1 / S2 / S3
        if st == "STRUCTURAL_PARTIAL":
            if d_dr not in GOOD:
                fail("S1", "%s PARTIAL 但 driver=%s" % (tag, d_dr))
            if d_sq not in GOOD:
                fail("S2", "%s PARTIAL 但 evidence_sequence=%s" % (tag, d_sq))
            if n_support < 2:
                fail("S3", "%s PARTIAL 但支持维度=%d" % (tag, n_support))
        # S4 —— ★ E.1 修复判据
        if d_dr == "MISMATCH" and st.startswith("STRUCTURAL"):
            fail("S4", "%s driver=MISMATCH 却为 %s（§4 硬约束违反）" % (tag, st))
        # S5
        if d_dr == "PERIPHERAL_OVERLAP" and st.startswith("STRUCTURAL"):
            fail("S5", "%s PERIPHERAL_OVERLAP 被计为结构支持（%s）" % (tag, st))
        # S6 / S7 / S8
        if st == "STRUCTURAL_SUPPORTED":
            if sub not in SEQ_OK:
                fail("S6", "%s SUPPORTED 但 sequence_subtype=%s" % (tag, sub))
            if d_lc != "MATCH":
                fail("S7", "%s SUPPORTED 但 lifecycle=%s" % (tag, d_lc))
            if not has_direct:
                fail("S7", "%s SUPPORTED 但 has_direct=False" % tag)
            if (d_lc == "MISMATCH") or (d_dr == "MISMATCH") or (d_ev == "MISMATCH"):
                fail("S7", "%s SUPPORTED 但存在核心 MISMATCH" % tag)
            if not (d_dr == "MATCH" or (d_dr == "PARTIAL" and q == "MULTI_MECHANISM")):
                fail("S8", "%s SUPPORTED 但 driver=%s/%s" % (tag, d_dr, q))
        # S9
        if r.get("event_quality") == "SINGLE_TYPE_ONLY" and d_ev == "PARTIAL":
            fail("S9", "%s SINGLE_TYPE_ONLY 被当作 event PARTIAL" % tag)
        # S10
        is_ins = (n_av >= 2) or (d_dr == "NOT_AVAILABLE")
        if (st == "INSUFFICIENT_EVIDENCE") != is_ins:
            fail("S10", "%s INSUFFICIENT 判据不一致：status=%s / 判据=%s（n_av=%d, driver=%s）"
                 % (tag, st, is_ins, n_av, d_dr))
        # S11
        if st in ("THEME_ONLY", "NO_VALID_CORRESPONDENCE"):
            want = "THEME_ONLY" if tr == "SAME_MACRO_THEME" else "NO_VALID_CORRESPONDENCE"
            if st != want:
                fail("S11", "%s 派生不一致：theme=%s 但 status=%s" % (tag, tr, st))

    # S14 —— 全表 driver=MISMATCH 的 PARTIAL 计数
    bad14 = [r for r in by_run["D"] if r["driver"] == "MISMATCH"
             and r["structural_status"] == "STRUCTURAL_PARTIAL"]
    if bad14:
        fail("S14", "driver=MISMATCH → STRUCTURAL_PARTIAL 仍有 %d 条（未彻底消除）" % len(bad14))
    bad14_pub = [r for r in by_run["A"] if r["driver"] == "MISMATCH"
                 and r["structural_status"] == "STRUCTURAL_PARTIAL"]
    bad14_c = [r for r in by_run["C"] if r["driver"] == "MISMATCH"
               and r["structural_status"] == "STRUCTURAL_PARTIAL"]

    # ---- S12 Theme-Blind ----
    tb = cal.get("controls", {}).get("theme_blind", {})
    if tb.get("structural_status_changed", 0) != 0:
        fail("S12", "theme-blind 改变了 %d 个 Structural Status" % tb.get("structural_status_changed"))
    # ---- S13 负控制 ----
    for n in cal.get("controls", {}).get("negative_controls", []):
        if not n.get("not_upgraded"):
            fail("S13", "负控制被升级：%s × %s → %s"
                 % (n["candidate_id"], n["historical_cycle"], n["rule_v0_3"]))

    # ---- 附加：Rule Set v0.3 文档与 Calibration 的 protocol 一致性 ----
    doc_path = os.path.join(ROOT, "research", "research", "methodology",
                            "structural_analogy_rule_set_v0_3.md")
    if not os.path.exists(doc_path):
        fail("P1", "缺少 Rule Set v0.3 文档")
    else:
        doc = io.open(doc_path, encoding="utf-8").read()
        pv = cal.get("protocol", {}).get("protocol_version")
        if pv and pv not in doc:
            fail("P1", "Calibration protocol_version=%r 未出现在 Rule Set v0.3 文档中" % pv)
        if "structural-analogy-ruleset-v0.3" != pv:
            fail("P1", "protocol_version 期望 structural-analogy-ruleset-v0.3，实际 %r" % pv)

    # ---- 附加：v0.1 / v0.2 / SA v0.3 未被修改（存在性）----
    for f in ("structural_analogy_rule_set_v0_2.md", "structural_analogy_rule_calibration_v0_2.json",
              "structural_analogy_research_v0_1.json", "structural_analogy_research_v0_2.json",
              "structural_analogy_research_v0_3.json", "structural_analogy_explanations_v0_1.json",
              "structural_analogy_explanations_v0_2.json", "structural_analogy_explanations_v0_3.json",
              "historical_driver_canonicalization_v0_1.json", "historical_driver_evidence_ledger_v0_1.json",
              "historical_driver_canonicalization_v0_2.json", "historical_driver_evidence_ledger_v0_2.json"):
        p = os.path.join(ROOT, "research", "research", "methodology", f)
        if not os.path.exists(p):
            p = os.path.join(REP, f)
        if not os.path.exists(p):
            fail("P2", "旧版本产物缺失（不得删除）: %s" % f)

    return report(n_checked, len(by_run["D"]), len(bad14), len(bad14_pub), len(bad14_c))


def report(n_checked=0, n_rows=0, n_bad14=0, n_bad14_pub=0, n_bad14_c=0):
    print("=== validate_structural_analogy_semantics.py（structural-analogy-ruleset-v0.3）===")
    print("独立重算行数: %d / %d" % (n_checked, n_rows))
    print("★ S14：driver=MISMATCH → STRUCTURAL_PARTIAL")
    print("     D 组（v0.3 规则 + v0.3 driver）: %d 条  ← 必须为 0" % n_bad14)
    print("     C 组（v0.3 规则 + v0.2 driver）: %d 条" % n_bad14_c)
    print("     A 组（v0.2 规则 + v0.2 driver）: %d 条  ← SA v0.3 已发布基线" % n_bad14_pub)
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
