#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""project_cc_to_objects_v0_1.py —— Current Candidate → Market Snapshot `research_objects` 投影器（Phase 1.2b）。

职责：把 `research/current/current_candidates.json` 里的 Current Candidate **投影**成
Market Snapshot 契约 v0.1 的 `research_objects[]`。

★ 纯投影：不判定、不重算、不新增字段语义、不改变 `resolution_state` 之外的任何结论。
★ `resolution_state` 固定为 `RESOLVED`（这些候选**已经过离线研究**）——
   若某候选证据不足，应在研究侧修正，**不在本脚本里猜测**。

用法（在仓库根执行）:
    python research/current/market_snapshots/scripts/project_cc_to_objects_v0_1.py \
        --object CC-2026-BCI-MEDTECH [--object ...] --out /tmp/objects.json
    --all    # 投影全部候选

退出码: 0 = 成功；1 = 失败。
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))))
CC_FILE = os.path.join(ROOT, "research", "current", "current_candidates.json")

CANONICAL_DRIVERS = {
    "POLICY_DRIVEN", "INDUSTRY_UPGRADE", "TECH_BREAKTHROUGH", "DEMAND_SURGE",
    "SUPPLY_CONTRACTION", "VALUATION_RESET", "CYCLE_REVERSAL", "EVENT_CATALYST", "UNKNOWN",
}
EVIDENCE_CATEGORIES = {"POLICY", "INDUSTRY", "COMPANY", "MARKET", "CAPITAL", "EXTERNAL"}
PHASE_OK = {
    "EARLY_SIGNAL", "THEME_FORMING", "BROAD_CONFIRMATION",
    "EXPANSION", "PEAK", "DECLINE", "UNKNOWN",
}


def derive_sequence(evidence: list) -> list:
    """证据台账 → 证据序列（type, date）。纯投影：date 取 event_date ?? source_date。"""
    seq = []
    for e in evidence:
        d = e.get("event_date") or e.get("source_date")
        if not d:
            continue
        t = (e.get("source_type") or "unknown").lower()
        seq.append({"type": t, "date": d})
    seq.sort(key=lambda x: x["date"])
    return seq


def project_one(c: dict) -> dict:
    phase = c.get("attention_state")
    if phase not in PHASE_OK:
        phase = "UNKNOWN"

    drivers = sorted({
        n for n in (c.get("narrative_types") or []) if n in CANONICAL_DRIVERS
    })
    cats = sorted({
        d.get("category") for d in (c.get("drivers") or [])
        if isinstance(d, dict) and d.get("category") in EVIDENCE_CATEGORIES
    })

    return {
        "object_id": c.get("candidate_id"),
        "object_kind": "current_candidate",
        "display_name": c.get("display_name"),
        "macro_theme": c.get("macro_theme"),
        "declared_phase": phase,
        "phase_source": "RESEARCH_DECLARED",
        "canonical_drivers": drivers,
        "evidence_categories": cats,
        "evidence_sequence": derive_sequence(c.get("evidence") or []),
        "events": [],
        "resolution_state": "RESOLVED",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Current Candidate → research_objects 投影器 v0.1")
    ap.add_argument("--object", action="append", default=[])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(CC_FILE):
        print("FAIL  数据源不存在: %s" % CC_FILE)
        return 1
    with open(CC_FILE, "r", encoding="utf-8") as f:
        cc = json.load(f)

    wanted = set(args.object)
    if not args.all and not wanted:
        print("FAIL  必须指定 --object 或 --all")
        return 1

    out = []
    for c in cc.get("candidates", []):
        if not args.all and c.get("candidate_id") not in wanted:
            continue
        out.append(project_one(c))

    if not out:
        print("FAIL  投影结果为空")
        return 1

    out.sort(key=lambda x: x["object_id"])
    blob = json.dumps(out, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(blob + ("\n" if args.pretty else ""))

    print("已投影: %s（%d 个 research_objects）" % (args.out, len(out)))
    for o in out:
        print("  %s · %s · phase=%s(%s) · drivers=%s · seq=%d"
              % (o["object_id"], o["macro_theme"], o["declared_phase"], o["phase_source"],
                 ",".join(o["canonical_drivers"]) or "-", len(o["evidence_sequence"])))
    print("  ★ 未做判定；resolution_state 一律 RESOLVED（这些候选已经过离线研究）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
