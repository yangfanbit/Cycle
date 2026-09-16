#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compare_time_observation_rounds.py —— 轮次产物归因对比（只读）。

用途
----
对比两轮 Time Observation 候选池产物（`time_observation_candidate_pool_vX_Y.json`），
把差异**分类归因**，而不是笼统地报「N 个候选变了」。这是「口径演进」可审计的核心工具：
每次调整 Gate / 解析口径后，必须能回答「到底什么变了、为什么变、哪些是设计使然」。

归因分类
--------
  [1] 顶层键差异                结构性
  [2] 顶层实质字段变化          口径文本 / 计数（promotion_gate / scan_map / ruleset_version …）
  [3] 候选池结构                候选增删（pattern_id 集合）
  [4] 候选字段结构差异          新增/删除字段（by design）
  [5] 实质性变化                共有候选的字段值变化 —— **只看这个才是「结论变了」**
  [6] derivation_verdict 分布   说明「字段新增 ≠ 结论变化」
  [7] effective_promotion_status 汇总 + 有效候选 id 差异

设计要点（避免上一版临时脚本的缺陷）
------------------------------------
  * 严格区分「字段新增（by design）」与「字段值变化（实质性）」；
  * `derivation_verdict` 是 dict（`{is_derived, stage_verdicts, reason}`），
    必须按 `is_derived` 取值统计，不能拿整个 dict 当标量比较；
  * `is_derived=None` 表示「无节奏判定 -> 不下结论 -> 不降级」，是**设计使然**，
    不计入「变化」；
  * 元数据（generated_at / research_round / artifact_version）不计入实质变化。

用法
----
    python research/scripts/compare_time_observation_rounds.py --from 0.3 --to 0.4
    python research/scripts/compare_time_observation_rounds.py            # 默认 0.3 -> 0.4

退出码：0 = 对比完成（无论有无差异）；2 = 产物缺失。
"""
from __future__ import annotations

import argparse
import json
import os
import sys

REPORTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "research", "reports",
)

# 只在某一轮出现的字段 —— 结构性新增，by design，不计入「实质变化」。
# 每次新增轮次字段时在此登记，并写明其语义。
STRUCTURAL_FIELDS = {
    # v0.4 引入：派生结构判定 {is_derived, stage_verdicts, reason}
    "derivation_verdict",
}

# 逐字节元数据：不承载研究结论，不计入实质变化
METADATA_FIELDS = {"generated_at", "research_round", "artifact_version"}


def artifact_path(round_: str) -> str:
    tag = "v" + round_.replace(".", "_")
    return os.path.join(REPORTS_DIR, "time_observation_candidate_pool_%s.json" % tag)


def load(round_: str) -> dict:
    p = artifact_path(round_)
    if not os.path.exists(p):
        print("FAIL —— 产物不存在：%s" % p)
        sys.exit(2)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def eff_map(doc: dict) -> dict:
    m = {}
    for c in doc["candidates"]:
        k = c.get("effective_promotion_status")
        m[k] = m.get(k, 0) + 1
    return m


def main() -> int:
    ap = argparse.ArgumentParser(description="轮次产物归因对比（只读）")
    ap.add_argument("--from", dest="rfrom", default="0.3", help="基准轮次，如 0.3")
    ap.add_argument("--to", dest="rto", default="0.4", help="对比轮次，如 0.4")
    args = ap.parse_args()

    a, b = load(args.rfrom), load(args.rto)
    ta, tb = "v" + args.rfrom.replace(".", "_"), "v" + args.rto.replace(".", "_")

    print("=" * 78)
    print("轮次归因对比：%s -> %s" % (ta, tb))
    print("=" * 78)

    # ---- [1] 顶层键 ----
    ka, kb = set(a), set(b)
    print("\n[1] 顶层键差异")
    print("    仅 %s : %s" % (ta, sorted(ka - kb) or "（无）"))
    print("    仅 %s : %s" % (tb, sorted(kb - ka) or "（无）"))

    # ---- [2] 顶层实质字段 ----
    print("\n[2] 顶层实质字段变化（排除元数据）")
    top_changed = []
    for k in sorted(ka & kb):
        if k in METADATA_FIELDS or k == "candidates":
            continue
        if a[k] != b[k]:
            top_changed.append(k)
    if not top_changed:
        print("    （无）")
    for k in top_changed:
        print("    ~ %s" % k)
        va, vb = a[k], b[k]
        if isinstance(va, dict) and isinstance(vb, dict):
            for kk in sorted(set(va) | set(vb)):
                if va.get(kk) != vb.get(kk):
                    print("        .%s" % kk)
                    print("            %s: %r" % (ta, va.get(kk)))
                    print("            %s: %r" % (tb, vb.get(kk)))
        else:
            print("        %s: %r" % (ta, va))
            print("        %s: %r" % (tb, vb))

    # ---- [3] 候选池结构 ----
    ca = {c["pattern_id"]: c for c in a["candidates"]}
    cb = {c["pattern_id"]: c for c in b["candidates"]}
    print("\n[3] 候选池结构")
    print("    候选数: %s=%d  %s=%d" % (ta, len(ca), tb, len(cb)))
    print("    仅 %s : %s" % (ta, sorted(set(ca) - set(cb)) or "（无）"))
    print("    仅 %s : %s" % (tb, sorted(set(cb) - set(ca)) or "（无）"))

    # ---- [4] 字段结构差异 ----
    fa = set(next(iter(ca.values()))) if ca else set()
    fb = set(next(iter(cb.values()))) if cb else set()
    print("\n[4] 候选字段结构差异（结构性，by design）")
    print("    仅 %s 新增字段: %s" % (tb, sorted(fb - fa) or "（无）"))
    print("    仅 %s 旧字段  : %s" % (ta, sorted(fa - fb) or "（无）"))
    for f in sorted(fb - fa):
        known = "（已登记：结构性）" if f in STRUCTURAL_FIELDS else "（⚠ 未在 STRUCTURAL_FIELDS 登记）"
        print("        + %s %s" % (f, known))

    # ---- [5] 实质性变化 ----
    ignore = STRUCTURAL_FIELDS | METADATA_FIELDS
    print("\n[5] 实质性变化（共有候选，排除新增字段/元数据）")
    substantive = []
    for pid in sorted(set(ca) & set(cb)):
        diffs = {}
        for k in set(ca[pid]) | set(cb[pid]):
            if k in ignore:
                continue
            if ca[pid].get(k) != cb[pid].get(k):
                diffs[k] = (ca[pid].get(k), cb[pid].get(k))
        if diffs:
            substantive.append((pid, diffs))
    if not substantive:
        print("    （无）")
    for pid, diffs in substantive:
        c = cb[pid]
        print("    * %s  [%s · %s]" % (pid, c.get("scope_name"), c.get("lifecycle_stage")))
        for k, (x, y) in sorted(diffs.items()):
            print("        %s: %r -> %r" % (k, x, y))

    # ---- [6] derivation_verdict 分布 ----
    dv_field = "derivation_verdict"
    if any(dv_field in c for c in cb.values()):
        print("\n[6] %s 分布（说明「字段新增 ≠ 结论变化」）" % dv_field)
        by_v = {True: 0, False: 0, None: 0}
        none_reasons = {}
        for c in cb.values():
            dv = c.get(dv_field) or {}
            v = dv.get("is_derived")
            by_v[v] = by_v.get(v, 0) + 1
            if v is None:
                r = dv.get("reason")
                none_reasons[r] = none_reasons.get(r, 0) + 1
        print("    is_derived=True  （判定派生 -> 若原为 TIMELINE_CANDIDATE 则降级）: %d" % by_v[True])
        print("    is_derived=False （判定非派生）                              : %d" % by_v[False])
        print("    is_derived=None  （无节奏判定 -> 不下结论 -> 不降级）         : %d" % by_v[None])
        if none_reasons:
            print("    None 的原因分布:")
            for r, n in sorted(none_reasons.items(), key=lambda kv: -kv[1]):
                print("        %4d  %s" % (n, r))
        downgraded = [
            c["pattern_id"] for c in cb.values()
            if (c.get(dv_field) or {}).get("is_derived") is True
            and c.get("promotion_status") == "TIMELINE_CANDIDATE"
        ]
        print("    其中「原 TIMELINE_CANDIDATE 且判定派生」=> 实际降级: %s" % (downgraded or "（无）"))

    # ---- [7] effective_promotion_status 汇总 ----
    print("\n[7] effective_promotion_status 汇总")
    ea, eb = eff_map(a), eff_map(b)
    for k in sorted(set(ea) | set(eb), key=lambda x: (x is None, x)):
        mark = "  " if ea.get(k) == eb.get(k) else "->"
        print("    %s %-22s %s=%d  %s=%d" % (mark, k, ta, ea.get(k, 0), tb, eb.get(k, 0)))
    ids_a = sorted(c["pattern_id"] for c in a["candidates"]
                   if c["effective_promotion_status"] == "TIMELINE_CANDIDATE")
    ids_b = sorted(c["pattern_id"] for c in b["candidates"]
                   if c["effective_promotion_status"] == "TIMELINE_CANDIDATE")
    print("    effective TIMELINE_CANDIDATE ids:")
    print("        %s: %s" % (ta, ids_a))
    print("        %s: %s" % (tb, ids_b))
    print("    差异: %s" % (sorted(set(ids_a) ^ set(ids_b)) or "（无）"))

    print("\n" + "=" * 78)
    print("结论：实质变化 = %d 条候选（其余差异均为结构性 / 设计使然）" % len(substantive))
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
