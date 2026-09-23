#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""validate_lifecycle_coverage_v0_1.py —— **lifecycle 覆盖恒等校验**（防回归 invariant）。

## 目的
杜绝再次出现：
```text
Intake lifecycle = complete
Export lifecycle = incomplete
```

## 检查项（**结构化恒等**，不写死 27）
  L1  **ID 集合恒等**：export 的 (campaigns ∪ research_candidates) ID 集合
      ⊇ 有 intake lifecycle 的 ID 集合；无 orphan / 无错配 / 无重复
  L2  **intake → export 段覆盖**：intake 中每个 **Contract 允许** 的 stage
      必须在 export 同 ID 的 lifecycle 中逐段出现（stage + start + end 三者一致）
  L3  **Contract 合规**：export 的每个 stage ∈ Contract 11 阶段；precision ∈ 三值
  L4  **UNKNOWN 不被伪装**：intake `UNKNOWN` 段**不得**出现在 export 中，
      也不得被映射成任何具体 stage（`MAIN_RISE/DECLINING/PEAK/...`）
  L5  **PEAK 保留**：intake 有 PEAK 的对象，export 必须有 PEAK
  L6  **open-ended 段保留**：intake 段 `end = null` 时，export 同段 `end` 也必须为 null
      （**不得**制造精确日期）
  L7  **coverage 报告**：逐对象输出 intake / export 段数，标注 only-UNKNOWN 的例外
  L8  **Driver 输入未受影响**：Driver Canonicalization 仍为 v0.4（lifecycle 修复不应改 driver）

退出码：0 = PASS；1 = FAIL。
用法：python research/scripts/validate_lifecycle_coverage_v0_1.py
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PKG = os.path.join(ROOT, "research", "intake", "packages")
REP = os.path.join(ROOT, "research", "research", "reports")
CONTRACT_STAGES = {"EARLY_SIGNAL", "THEME_FORMING", "BROAD_CONFIRMATION", "MAIN_RISE", "PEAK",
                   "RETRACEMENT", "DECLINING", "SECONDARY", "FIRST_DECLINE", "MAIN_END", "ENDED"}
VALID_PRECISION = {"EXACT_DATE", "DATE_WINDOW", "PHASE_WINDOW"}
PREFIX = {"R01-01": "R01-HIEQ-", "R01-02": "R01-SEMICONDUCTOR-", "R01-03": "R01-RESOURCES-",
          "R01-04": "R01-CONSUMER-", "R01-05": "R01-FINRE-", "R01-06": "R01-MIL-"}

fails, warns = [], []


def fail(code, msg):
    fails.append("%s  %s" % (code, msg))


def main():
    # ---- intake 侧 ----
    mapping = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "research", "scripts", "import_r01_0*_canonical_v0_1.py"))):
        pkg = "R01-" + re.search(r"import_r01_(\d{2})_canonical", f).group(1)
        t = io.open(f, encoding="utf-8").read()
        for m in re.finditer(r'k="(\d{3})",\s*cid="((?:RC|C)-[A-Z0-9\-]+)"', t):
            mapping[m.group(2)] = (pkg, m.group(1))
        for m in re.finditer(r'cid="((?:RC|C)-[A-Z0-9\-]+)",\s*intake="R01-[A-Z]+-(\d{3})"', t):
            mapping[m.group(1)] = (pkg, m.group(2))

    cache = {}

    def intake_lc(cid):
        if cid not in mapping:
            return None
        pkg, k = mapping[cid]
        if pkg not in cache:
            cache[pkg] = {x["candidate_id"]: x
                          for x in json.load(io.open(os.path.join(PKG, pkg, "candidates.json"), encoding="utf-8"))}
        x = cache[pkg].get(PREFIX[pkg] + k)
        return (x.get("lifecycle") or []) if x else None

    exp = json.load(io.open(os.path.join(ROOT, "exports", "timeline_export_v1.json"), encoding="utf-8"))
    objs = ([("campaign", o) for o in exp["campaigns"]] +
            [("research_candidate", o) for o in exp["research_candidates"]])
    exp_by_id = {o["campaign_id"]: o for _, o in objs}

    # L1 ID 集合恒等
    intake_ids = {cid for cid, _ in objs if intake_lc(cid)}
    orphan = sorted(intake_ids - set(exp_by_id))
    if orphan:
        fail("L1", "intake 有 lifecycle 但 export 无此 ID（orphan）: %s" % orphan)
    from collections import Counter as _C
    dup = [k for k, v in _C(o["campaign_id"] for _, o in objs).items() if v > 1]
    if dup:
        fail("L1", "export 存在重复 ID: %s" % sorted(dup))
    if len(exp_by_id) != len(objs):
        fail("L1", "export ID 不唯一：%d 对象 / %d 唯一 ID" % (len(objs), len(exp_by_id)))

    stats = {"with_intake": 0, "seg_expected": 0, "seg_found": 0,
             "only_unknown": [], "peak_expected": 0, "peak_found": 0, "open_ended": 0}
    rc_total = sum(1 for k, _ in objs if k == "research_candidate")
    rc_nonempty = 0

    for kind, o in objs:
        cid = o["campaign_id"]
        il = intake_lc(cid)
        if il is None:
            continue
        stats["with_intake"] += 1
        el = o.get("lifecycle") or []
        if kind == "research_candidate" and el:
            rc_nonempty += 1

        # Contract 允许的 intake 段（UNKNOWN 不算）
        allowed = []
        unknown_segs = []
        for l in il:
            st = l.get("stage_proposal")
            if st == "UNKNOWN":
                unknown_segs.append(l)
                continue
            if st not in CONTRACT_STAGES:
                fail("L3", "%s intake stage=%r 不在 Contract 集合内（无法映射）" % (cid, st))
                continue
            allowed.append((st, l.get("start"), l.get("end")))
        stats["seg_expected"] += len(allowed)
        stats["seg_found"] += len(el)

        eset = {(l.get("stage"), l.get("start"), l.get("end")) for l in el}
        for seg in allowed:
            if seg not in eset:
                fail("L2", "%s intake 段未进入 export: %s" % (cid, seg))

        # L4 UNKNOWN 不得伪装
        if not allowed and unknown_segs:
            stats["only_unknown"].append(cid)
            if el:
                fail("L4", "%s 仅有 intake UNKNOWN 段，但 export lifecycle 非空（**虚构阶段**）: %s"
                     % (cid, [l.get("stage") for l in el]))
        for l in el:
            if l.get("stage") == "UNKNOWN":
                fail("L4", "%s export 出现 UNKNOWN stage（Contract 不允许）" % cid)

        # L5 PEAK 保留
        if any(a == "PEAK" for a, _, _ in allowed):
            stats["peak_expected"] += 1
            if not any(l.get("stage") == "PEAK" for l in el):
                fail("L5", "%s intake 有 PEAK 但 export 缺失" % cid)
        if any(l.get("stage") == "PEAK" for l in el):
            stats["peak_found"] += 1

        # L6 open-ended 段保留（end=null 不得被填成具体日期）
        for st, a, b in allowed:
            if b is None:
                stats["open_ended"] += 1
                m = [l for l in el if l.get("stage") == st and l.get("start") == a]
                if not m:
                    fail("L6", "%s open-ended 段丢失: (%s, %s, null)" % (cid, st, a))
                elif m[0].get("end") is not None:
                    fail("L6", "%s open-ended 段被填成具体日期: %s → %s" % (cid, st, m[0].get("end")))

        # L3 Contract 合规
        for l in el:
            if l.get("stage") not in CONTRACT_STAGES:
                fail("L3", "%s export stage=%r 非法" % (cid, l.get("stage")))
            if l.get("precision") not in VALID_PRECISION:
                fail("L3", "%s export precision=%r 非法" % (cid, l.get("precision")))

    # L8 Driver 未受影响
    can = os.path.join(REP, "historical_driver_canonicalization_v0_4.json")
    if not os.path.exists(can):
        fail("L8", "Driver Canonicalization v0.4 产物缺失（lifecycle 修复不应改 driver）")
    else:
        d = json.load(io.open(can, encoding="utf-8"))
        if d.get("artifact_version") != "0.4":
            fail("L8", "Driver artifact_version=%r 期望 0.4" % d.get("artifact_version"))

    # ---- 报告 ----
    print("=== validate_lifecycle_coverage_v0_1.py ===")
    print("  L1 ID 集合恒等        : export %d 唯一 ID / %d 对象 · intake 有 lifecycle %d"
          % (len(exp_by_id), len(objs), stats["with_intake"]))
    print("  L2 段覆盖             : 期望 %d 段 / export 实有 %d 段"
          % (stats["seg_expected"], stats["seg_found"]))
    print("  L5 PEAK 保留          : intake 有 PEAK %d 对象 / export 有 PEAK %d 对象"
          % (stats["peak_expected"], stats["peak_found"]))
    print("  L6 open-ended 段      : %d 段（end=null 必须保持 null）" % stats["open_ended"])
    # export 侧 RC 非空总数（含 pre-R01 静态字典回退的对象）
    rc_nonempty_total = sum(
        1 for kind, o in objs if kind == "research_candidate" and (o.get("lifecycle") or [])
    )
    from_intake = sum(
        1 for kind, o in objs
        if kind == "research_candidate" and o["campaign_id"] in mapping
        and (o.get("lifecycle") or [])
    )
    print("  Research Candidate    : %d / %d export lifecycle 非空"
          "（其中 intake 派生 %d + 静态字典回退（pre-R01）%d）"
          % (rc_nonempty_total, rc_total, from_intake, rc_nonempty_total - from_intake))
    print("  ★ 仅含 intake UNKNOWN（export 保持空，**不虚构**）: %d %s"
          % (len(stats["only_unknown"]), stats["only_unknown"]))
    print("-" * 62)
    for f in fails:
        print("FAIL  " + f)
    for w in warns:
        print("WARN  " + w)
    print()
    print("结果: %s（FAIL %d / WARN %d）" % ("PASS" if not fails else "FAIL", len(fails), len(warns)))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
