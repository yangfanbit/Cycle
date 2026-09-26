#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""project_sa_to_candidates_v0_1.py —— SA 解释 → Market Snapshot `historical_candidates` 投影器（ThreeC 1.1 Phase 1.2b）。

职责：把**冻结的** Structural Analogy 解释产物（`structural_analogy_explanations_v0_5.json`）
投影成 Market Snapshot 契约 v0.1 的 `historical_candidates[]`。

★ 本脚本是**纯投影（pure projection）**，不做任何判定：
  - **不重新计算** 任何维度 / 结构状态 / 相似度
  - **不新增** 词表、不改状态、不排序（只按 `historical_cycle_id` 升序 = 稳定 identity 顺序）
  - **不读取** DB / 中间产物；只读**冻结 artifact**
  - 只做「字段改名 + 结构搬运 + 白名单裁剪」

★ 契约裁剪（v0.1）：SA 解释里的 `snapshot_date` / `governance_context` / `supplementary_context`
   **不在** Market Snapshot 契约 v0.1 的 `historicalCandidate` 白名单内 → **丢弃**并计入报告。
   若将来需要，须按契约版本规则**升 minor 版本**后另行加入（不得悄悄透传）。

用法（在仓库根执行）:
    python research/current/market_snapshots/scripts/project_sa_to_candidates_v0_1.py \
        --object CC-2026-BCI-MEDTECH --out /tmp/candidates.json

    --all                         # 投影全部候选
    --include-status A,B          # 只保留指定结构状态（默认：全部，不做编辑性筛选）
    --pretty                      # 人类可读缩进（默认紧凑）

退出码: 0 = 成功；1 = 失败（含 rule_set_version 不是冻结 v0.3 的守卫失败）。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))))
SA_ARTIFACT = os.path.join(
    ROOT, "research", "research", "reports", "structural_analogy_explanations_v0_5.json"
)

FROZEN_RULE_SET = "structural-analogy-ruleset-v0.3"

# 契约 v0.1 允许的 historicalCandidate 字段（白名单）
ALLOWED_KEYS = {
    "identity",
    "rule_set_version",
    "structural_status",
    "strict_structural_supported",
    "theme_relation",
    "dimensions",
    "supported_dimensions",
    "unknown_dimensions",
    "unsupported_dimensions",
    "why_similar",
    "why_not_similar",
    "dimension_evidence",
    "background_sources",
}


def project_one(exp: dict) -> tuple:
    """把一条 SA 解释投影为契约字段；返回 (candidate, dropped_keys)。"""
    dropped = sorted(k for k in exp.keys() if k not in ALLOWED_KEYS)
    cand = {k: exp[k] for k in ALLOWED_KEYS if k in exp}
    return cand, dropped


def main() -> int:
    ap = argparse.ArgumentParser(description="SA → historical_candidates 投影器 v0.1")
    ap.add_argument("--object", action="append", default=[], help="候选 id（可重复）")
    ap.add_argument("--all", action="store_true", help="投影全部候选")
    ap.add_argument("--include-status", default=None,
                    help="只保留指定结构状态（逗号分隔）；默认全部")
    ap.add_argument("--out", required=True)
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(SA_ARTIFACT):
        print("FAIL  冻结 SA artifact 不存在: %s" % SA_ARTIFACT)
        return 1

    with open(SA_ARTIFACT, "r", encoding="utf-8") as f:
        sa = json.load(f)

    # ★ 守卫：只允许投影冻结规则版本的产物
    rs = sa.get("rule_set_version")
    if rs != FROZEN_RULE_SET:
        print("FAIL  rule_set_version 不是冻结版本：%r（期望 %s）→ 拒绝投影" % (rs, FROZEN_RULE_SET))
        return 1
    print("OK    冻结规则版本校验通过：%s" % rs)

    wanted = set(args.object)
    if not args.all and not wanted:
        print("FAIL  必须指定 --object 或 --all")
        return 1

    status_filter = None
    if args.include_status:
        status_filter = {s.strip() for s in args.include_status.split(",") if s.strip()}

    out_cands = []
    dropped_counter = Counter()
    status_counter = Counter()
    per_object = {}

    for c in sa.get("candidates", []):
        cid = c.get("candidate_id")
        if not args.all and cid not in wanted:
            continue
        kept = 0
        for exp in c.get("explanations", []):
            st = exp.get("structural_status")
            if status_filter is not None and st not in status_filter:
                continue
            cand, dropped = project_one(exp)
            for d in dropped:
                dropped_counter[d] += 1
            status_counter[st] += 1
            out_cands.append(cand)
            kept += 1
        per_object[cid] = kept

    if not out_cands:
        print("FAIL  投影结果为空（检查 --object / --include-status）")
        return 1

    # ★ 稳定 identity 顺序（不是强弱排名）
    out_cands.sort(key=lambda x: x.get("identity", {}).get("historical_cycle_id", ""))

    blob = json.dumps(out_cands, ensure_ascii=False, indent=2 if args.pretty else None,
                      sort_keys=True)
    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(blob + ("\n" if args.pretty else ""))

    print("已投影: %s（%d 条 historical_candidates）" % (args.out, len(out_cands)))
    for cid, n in per_object.items():
        print("  对象 %s → %d 条" % (cid, n))
    print("  结构状态分布: %s" % json.dumps(dict(status_counter), ensure_ascii=False))
    if dropped_counter:
        print("  按契约 v0.1 白名单丢弃的字段（非透传）: %s"
              % json.dumps(dict(dropped_counter), ensure_ascii=False))
    print("  ★ 未做任何判定 / 重算 / 排序（仅按 historical_cycle_id 升序）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
