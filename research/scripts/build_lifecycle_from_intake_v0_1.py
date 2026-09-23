#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_lifecycle_from_intake_v0_1.py —— 从 **R01 intake 包** 派生 export 用的 lifecycle（**单一真源**）。

## 背景（根因）
export 的 lifecycle 原先来自 `batch_auto_research.py` 中**手写的静态字典**
`CAMPAIGN_LIFECYCLE` / `CANDIDATE_LIFECYCLE`，**与 intake 解耦**，导致：
  · `CANDIDATE_LIFECYCLE` 只登记 11 / 27 个 RC（16 个整条缺失）
  · 已登记的条目**丢掉 `UNKNOWN` 段与 open-ended 段**
  · `PEAK` 在 importers 写入 DB `campaign_phases` 时被过滤（**schema CHECK 不含 PEAK，属合法约束**），
    但 DB **不是** export 的来源 —— 真正的缺口在 export 装配层

## 本脚本的原则（**恢复已有真实数据，不重新人工编写研究数据**）
  1. **只从 intake 派生**：`candidates[].lifecycle[].{stage_proposal,start,end}`
  2. **stage**：仅接受 `Timeline Export Contract v1.0` 允许的 11 个阶段
     （`EARLY_SIGNAL/THEME_FORMING/BROAD_CONFIRMATION/MAIN_RISE/PEAK/RETRACEMENT/DECLINING/SECONDARY/FIRST_DECLINE/MAIN_END/ENDED`）
     · `UNKNOWN` **不在 Contract 内** → **丢弃该段**（**不虚构阶段、不新增 enum、不改 Contract**），
       但**逐条登记**到 `dropped_unknown`，语义由 `research_status = INSUFFICIENT` 承载
  3. **precision**：**机械派生**（非研究判断）—— `start == end` 且均非空 → `EXACT_DATE`；否则 → `PHASE_WINDOW`
  4. **start / end**：**原样保留（可为 null）** —— 验证器 `is_iso_date(None) == True`，且「不制造精确日期」是既有纪律
  5. **不修改** `schema.sql` / Export Contract / CMTR / taxonomy / Campaign Decision

## 产物
  `research/research/reports/lifecycle_from_intake_v0_1.json`（机器可读，含 coverage 与 provenance）

用法：python research/scripts/build_lifecycle_from_intake_v0_1.py [--check]
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REP = os.path.join(ROOT, "research", "research", "reports")
PKG = os.path.join(ROOT, "research", "intake", "packages")
OUT = os.path.join(REP, "lifecycle_from_intake_v0_1.json")

# Timeline Export Contract v1.0 允许的 lifecycle stage（**唯一权威**，与 validate_timeline_export.py 一致）
CONTRACT_STAGES = ["EARLY_SIGNAL", "THEME_FORMING", "BROAD_CONFIRMATION", "MAIN_RISE", "PEAK",
                   "RETRACEMENT", "DECLINING", "SECONDARY", "FIRST_DECLINE", "MAIN_END", "ENDED"]
# intake `stage_proposal` → Contract stage（仅**同义**映射；不做语义升级）
STAGE_ALIAS = {
    "EARLY_SIGNAL": "EARLY_SIGNAL", "THEME_FORMING": "THEME_FORMING",
    "BROAD_CONFIRMATION": "BROAD_CONFIRMATION", "MAIN_RISE": "MAIN_RISE", "PEAK": "PEAK",
    "RETRACEMENT": "RETRACEMENT", "DECLINING": "DECLINING", "SECONDARY": "SECONDARY",
    "FIRST_DECLINE": "FIRST_DECLINE", "MAIN_END": "MAIN_END", "ENDED": "ENDED",
    # ★ UNKNOWN **不映射** —— 它不是生命周期阶段，而是「阶段不可识别」
}
PREFIX = {"R01-01": "R01-HIEQ-", "R01-02": "R01-SEMICONDUCTOR-", "R01-03": "R01-RESOURCES-",
          "R01-04": "R01-CONSUMER-", "R01-05": "R01-FINRE-", "R01-06": "R01-MIL-"}


def derive_precision(start, end):
    """**机械派生** precision（不引入研究判断）。"""
    if start and end and start == end:
        return "EXACT_DATE"
    return "PHASE_WINDOW"


def build_mapping():
    """从 R01 importers 提取 `CID/RCID → (intake 包, 候选序号)`。"""
    m = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "research", "scripts", "import_r01_0*_canonical_v0_1.py"))):
        pkg = "R01-" + re.search(r"import_r01_(\d{2})_canonical", f).group(1)
        t = io.open(f, encoding="utf-8").read()
        for mm in re.finditer(r'k="(\d{3})",\s*cid="((?:RC|C)-[A-Z0-9\-]+)"', t):
            m[mm.group(2)] = (pkg, mm.group(1))
        for mm in re.finditer(r'cid="((?:RC|C)-[A-Z0-9\-]+)",\s*intake="R01-[A-Z]+-(\d{3})"', t):
            m[mm.group(1)] = (pkg, mm.group(2))
    return m


def main():
    check = "--check" in sys.argv
    mapping = build_mapping()
    cache = {}

    def intake_of(cid):
        if cid not in mapping:
            return None
        pkg, k = mapping[cid]
        if pkg not in cache:
            cache[pkg] = {x["candidate_id"]: x
                          for x in json.load(io.open(os.path.join(PKG, pkg, "candidates.json"), encoding="utf-8"))}
        return cache[pkg].get(PREFIX[pkg] + k)

    exp = json.load(io.open(os.path.join(ROOT, "exports", "timeline_export_v1.json"), encoding="utf-8"))
    objs = ([("campaign", o) for o in exp["campaigns"]] +
            [("research_candidate", o) for o in exp["research_candidates"]])

    out = {}
    stats = {"objects": 0, "with_intake": 0, "segments_kept": 0, "segments_dropped_unknown": 0,
             "segments_unknown_stage": 0, "rc_total": 0, "rc_nonempty": 0,
             "rc_only_unknown": [], "camp_total": 0, "camp_nonempty": 0}
    dropped = []

    for kind, o in objs:
        cid = o["campaign_id"]
        stats["objects"] += 1
        if kind == "research_candidate":
            stats["rc_total"] += 1
        else:
            stats["camp_total"] += 1
        cand = intake_of(cid)
        if not cand or not (cand.get("lifecycle") or []):
            continue
        stats["with_intake"] += 1
        segs = []
        has_real = False
        for l in cand["lifecycle"]:
            raw = l.get("stage_proposal")
            if raw == "UNKNOWN":
                stats["segments_dropped_unknown"] += 1
                dropped.append({"cycle_id": cid, "kind": kind, "intake_stage": "UNKNOWN",
                                "start": l.get("start"), "end": l.get("end"),
                                "basis": l.get("basis"),
                                "reason": "UNKNOWN 不是 Contract 允许的 lifecycle stage（不得虚构、不得新增 enum）"})
                continue
            stage = STAGE_ALIAS.get(raw)
            if stage is None:
                stats["segments_unknown_stage"] += 1
                dropped.append({"cycle_id": cid, "kind": kind, "intake_stage": raw,
                                "start": l.get("start"), "end": l.get("end"),
                                "reason": "intake stage_proposal 不在 Contract 允许集合内"})
                continue
            start, end = l.get("start"), l.get("end")
            segs.append({"stage": stage, "start": start, "end": end,
                         "precision": derive_precision(start, end)})
            has_real = True
            stats["segments_kept"] += 1
        if segs:
            out[cid] = {"kind": kind, "intake_package": mapping[cid][0], "intake_candidate": mapping[cid][1],
                        "lifecycle": segs,
                        "provenance": "intake:%s/%s" % (mapping[cid][0], PREFIX[mapping[cid][0]] + mapping[cid][1])}
            if kind == "research_candidate":
                stats["rc_nonempty"] += 1
            else:
                stats["camp_nonempty"] += 1
        elif kind == "research_candidate":
            stats["rc_only_unknown"].append(cid)

    res = {
        "artifact": "lifecycle_from_intake", "artifact_version": "0.1",
        "generated_by": "research/scripts/build_lifecycle_from_intake_v0_1.py",
        "position": ("Research-only —— 从 R01 intake 包派生 export 用的 lifecycle（**单一真源**）。"
                     "**不修改** schema.sql / Export Contract / CMTR / taxonomy / Campaign Decision。"),
        "contract_stages": CONTRACT_STAGES,
        "rules": {
            "stage": "仅接受 Contract 的 11 个 stage；`UNKNOWN` **丢弃该段**（不虚构、不新增 enum）",
            "precision": "机械派生：start == end 且均非空 → EXACT_DATE；否则 PHASE_WINDOW",
            "dates": "start / end **原样保留（可为 null）** —— 不制造精确日期",
            "priority": "本产物**优先于** batch_auto_research.py 的手写静态字典（后者仅用于无 intake 的旧对象）",
        },
        "coverage": stats,
        "dropped_segments": dropped,
        "by_cycle": out,
    }

    if check:
        if not os.path.exists(OUT):
            print("FAIL —— 产物不存在:", OUT)
            return 1
        old = json.load(io.open(OUT, encoding="utf-8"))
        same = json.dumps(old, ensure_ascii=False, sort_keys=True) == json.dumps(res, ensure_ascii=False, sort_keys=True)
        print("--check:", "PASS（逐字节一致）" if same else "FAIL（与磁盘产物不一致）")
        return 0 if same else 1

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
        f.write("\n")

    print("=" * 74)
    print("lifecycle_from_intake_v0_1")
    print("=" * 74)
    print("  对象总数            : %d" % stats["objects"])
    print("  有 intake lifecycle : %d" % stats["with_intake"])
    print("  保留段数            : %d" % stats["segments_kept"])
    print("  丢弃 UNKNOWN 段     : %d" % stats["segments_dropped_unknown"])
    print("  非 Contract stage   : %d" % stats["segments_unknown_stage"])
    print()
    print("  Research Candidate  : %d / %d 非空" % (stats["rc_nonempty"], stats["rc_total"]))
    print("  Campaign            : %d / %d 非空" % (stats["camp_nonempty"], stats["camp_total"]))
    print("  ★ 仅含 UNKNOWN 段（export 保持空）: %d %s"
          % (len(stats["rc_only_unknown"]), stats["rc_only_unknown"]))
    print()
    print("written", os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
