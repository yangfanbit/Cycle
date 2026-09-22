#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""audit_rc_export_driver_gap.py —— 18 个 RC 的 Export driver 缺口审计（**只读**）。

**链路**（driver 数据的真实流向）：
  ① Intake Package `candidates[].drivers`（raw 研究文本，已通过 Intake Review）
  ② `batch_auto_research.py::CANDIDATE_DRIVERS`（**人工转写映射层**）
  ③ `exports/timeline_export_v1.json` → `research_candidates[].drivers`
  ④ `historical_driver_canonicalization_v0_3.json`（**只读 ③**）
  ⑤ `historical_driver_evidence_ledger_v0_3.json`

★ **③ 是 ④ 的唯一输入** —— 因此「canonicalization 已有 driver 而 export 为空」在结构上不可能出现。
   真正的缺口只能发生在 **① → ② → ③** 这段映射链上。

产物：`research/research/reports/rc_export_driver_gap_audit_v0_3.json`
用法：python research/scripts/audit_rc_export_driver_gap.py
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
PKG = os.path.join(ROOT, "research", "intake", "packages")

EXP = json.load(io.open(os.path.join(ROOT, "exports", "timeline_export_v1.json"), encoding="utf-8"))
C3 = json.load(io.open(os.path.join(REP, "historical_driver_canonicalization_v0_3.json"), encoding="utf-8"))
L3 = json.load(io.open(os.path.join(REP, "historical_driver_evidence_ledger_v0_3.json"), encoding="utf-8"))["entries"]
PER_CYCLE = {x["cycle_id"]: x for x in C3["per_cycle"]}

# ---- 从 importer 脚本提取 RC → (package, intake_candidate) 映射 ----
IMPORTER_RC = {}
for fn in sorted(os.listdir(os.path.join(ROOT, "research", "scripts"))):
    m = re.match(r"import_r01_(\d{2})_canonical_v0_1\.py$", fn)
    if not m:
        continue
    pkg = "R01-" + m.group(1)
    txt = io.open(os.path.join(ROOT, "research", "scripts", fn), encoding="utf-8").read()
    for rc in sorted(set(re.findall(r"RC-[A-Z0-9\-]+", txt))):
        IMPORTER_RC.setdefault(rc, pkg)

# ---- 载入全部 intake 候选 ----
INTAKE = {}
for pkg in sorted(os.listdir(PKG)):
    p = os.path.join(PKG, pkg, "candidates.json")
    if not os.path.exists(p):
        continue
    for x in json.load(io.open(p, encoding="utf-8")):
        INTAKE[(pkg, x["candidate_id"])] = x


def n_drv(d):
    return sum(len((d or {}).get(b) or []) for b in ("start", "accelerator", "turning", "ending"))


def match_intake(rc, title, pkg_hint):
    """把 RC 匹配到 intake candidate：先按包内 title 精确/包含匹配，再全局匹配。"""
    cands = [x for (p, _), x in INTAKE.items() if p == pkg_hint] if pkg_hint else []
    for x in cands:
        if x.get("title") and title and (x["title"][:24] in title or title[:24] in x["title"]):
            return (pkg_hint, x["candidate_id"]), x
    for (p, cid), x in INTAKE.items():
        if x.get("title") and title and (x["title"][:20] in title or title[:20] in x["title"]):
            return (p, cid), x
    return None, None


rows = []
for r in EXP["research_candidates"]:
    rc = r["campaign_id"]
    drv = r.get("drivers") or {}
    n_exp = n_drv(drv)
    pkg_hint = IMPORTER_RC.get(rc)
    key, intake = match_intake(rc, r.get("title") or "", pkg_hint)
    n_int = n_drv((intake or {}).get("drivers"))
    pc = PER_CYCLE.get(rc, {})
    led = [e for e in L3 if e["cycle_id"] == rc]
    led_driving = [e for e in led if e["bucket"] in ("start", "accelerator")]

    # 缺口层级判定
    if n_exp > 0:
        layer = "OK"
    elif n_int > 0:
        layer = "MAPPING_GAP（① intake 有 driver → ②③ Export 丢失）"
    elif intake is None:
        layer = "UNMATCHED_INTAKE（未匹配到 intake 候选）"
    else:
        layer = "INSUFFICIENT_DRIVER_EVIDENCE（① intake 本身无 driver）"

    rows.append({
        "cycle_id": rc,
        "export_title": (r.get("title") or "")[:80],
        "intake_package": key[0] if key else None,
        "intake_candidate_id": key[1] if key else None,
        "intake_candidate_title": ((intake or {}).get("title") or "")[:80],
        "n_intake_drivers": n_int,
        "n_export_drivers": n_exp,
        "export_drivers_empty": n_exp == 0,
        "canonical_driver": pc.get("canonical_drivers") or [],
        "canonical_driver_count": pc.get("canonical_driver_count", 0),
        "ledger_entries": len(led),
        "ledger_driving_entries": len(led_driving),
        "mapping_status_driving": dict(collections.Counter(e["mapping_status"] for e in led_driving)),
        "gap_layer": layer,
        "intake_drivers_preview": {
            b: [(t or "")[:90] for t in ((intake or {}).get("drivers") or {}).get(b, [])]
            for b in ("start", "accelerator", "turning", "ending")
        } if intake else None,
    })

summary = collections.Counter(x["gap_layer"].split("（")[0] for x in rows)
gap18 = [x for x in rows if x["export_drivers_empty"]]

out = {
    "artifact": "rc_export_driver_gap_audit", "artifact_version": "0.3",
    "generated_by": "research/scripts/audit_rc_export_driver_gap.py",
    "position": "Research-only 审计件 —— **只读**；不修改 export / DB / 词表 / 规则集。",
    "chain": [
        "① Intake Package candidates[].drivers（raw 研究文本）",
        "② batch_auto_research.py::CANDIDATE_DRIVERS（人工转写映射层）",
        "③ exports/timeline_export_v1.json research_candidates[].drivers",
        "④ historical_driver_canonicalization_v0_3.json（**只读 ③**）",
        "⑤ historical_driver_evidence_ledger_v0_3.json",
    ],
    "chain_note": ("★ ③ 是 ④ 的唯一输入 —— 「canonicalization 已有 driver 而 export 为空」在结构上不可能；"
                   "真正的缺口只能发生在 ①→②→③ 这段映射链上。"),
    "summary": {
        "research_candidates_total": len(rows),
        "export_drivers_empty": len(gap18),
        "by_gap_layer": dict(summary),
    },
    "rows": rows,
}

p = os.path.join(REP, "rc_export_driver_gap_audit_v0_3.json")
with io.open(p, "w", encoding="utf-8", newline="\n") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
    f.write("\n")

print("=== RC Export driver 缺口审计 ===")
print("RC 总数: %d | export drivers 为空: %d" % (len(rows), len(gap18)))
print("按缺口层级:", dict(summary))
print()
print("  %-32s %-9s %-9s %-26s %s" % ("cycle_id", "intake", "export", "canonical_driver", "缺口层级"))
for x in rows:
    print("  %-32s %-9d %-9d %-26s %s" % (x["cycle_id"], x["n_intake_drivers"], x["n_export_drivers"],
                                          ",".join(x["canonical_driver"]) or "-",
                                          x["gap_layer"].split("（")[0]))
print()
print("written", p)
