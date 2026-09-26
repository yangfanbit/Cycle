#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""project_sa_to_candidates_v0_1.py —— SA 解释 → Market Snapshot `historical_candidates` 投影器。

★ 产出遵循 **Market Snapshot Contract v0.2**（回指模式）：
   `historical_candidates` 只存**轻量索引**（`identity` + `structural_status` +
   `strict_structural_supported`），四维解释 / why_similar / why_not_similar /
   dimension_evidence / background_sources 一律**不复制**，
   改由顶层 `candidates_source` 描述**回指**的冻结 artifact。

★ 本脚本是**纯投影（pure projection）**，不做任何判定：
  - **不重新计算** 任何维度 / 结构状态 / 相似度
  - **不新增** 词表、不改状态、不排序（只按 `historical_cycle_id` 升序 = 稳定 identity 顺序）
  - **不读取** DB / 中间产物；只读**冻结 artifact**
  - 带**冻结规则版本守卫**（`rule_set_version` 必须为 `structural-analogy-ruleset-v0.3`）

用法（在仓库根执行）:
    python research/current/market_snapshots/scripts/project_sa_to_candidates_v0_1.py \
        --object CC-2026-BCI-MEDTECH --out /tmp/candidates.json
    --all                  # 投影全部候选
    --include-status A,B   # 只保留指定结构状态（默认全部，不做编辑性筛选）

退出码: 0 = 成功；1 = 失败（含守卫失败）。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))))
SA_ARTIFACT_REL = "research/research/reports/structural_analogy_explanations_v0_5.json"
SA_ARTIFACT = os.path.join(ROOT, SA_ARTIFACT_REL)

FROZEN_RULE_SET = "structural-analogy-ruleset-v0.3"

# ★ 轻量索引字段（契约 v0.2）。其余字段一律回指 SA artifact，不复制。
SLIM_KEYS = ("identity", "structural_status", "strict_structural_supported")

# 仅用于报告：这些字段**故意不复制**（回指代替）
REFERRED_KEYS = (
    "theme_relation", "dimensions",
    "supported_dimensions", "unknown_dimensions", "unsupported_dimensions",
    "why_similar", "why_not_similar", "dimension_evidence", "background_sources",
    "governance_context", "supplementary_context", "snapshot_date", "rule_set_version",
)


def project_one(exp: dict) -> dict:
    """把一条 SA 解释压成轻量索引（契约 v0.2）。"""
    out = {k: exp[k] for k in SLIM_KEYS if k in exp}
    # identity 只保留契约字段：去掉 SA artifact 的说明性 `identity_note`
    # （它是同一段样板文字，在 395 条里逐条重复，不属契约数据）。
    ident = out.get("identity")
    if isinstance(ident, dict):
        out["identity"] = {k: v for k, v in ident.items() if k != "identity_note"}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="SA → historical_candidates 投影器（契约 v0.2 回指模式）")
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

    items = []
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
            items.append(project_one(exp))
            status_counter[st] += 1
            kept += 1
        per_object[cid] = kept

    if not items:
        print("FAIL  投影结果为空（检查 --object / --include-status）")
        return 1

    # ★ 稳定 identity 顺序（不是强弱排名）
    items.sort(key=lambda x: x.get("identity", {}).get("historical_cycle_id", ""))

    doc = {
        "candidates_source": {
            "artifact": SA_ARTIFACT_REL,
            "artifact_version": sa.get("artifact_version"),
            "rule_set_version": rs,
            "resolve_by": "identity.historical_cycle_id",
            "mode": "INDEX_ONLY —— 本快照只存 identity / structural_status / strict_structural_supported；"
                    "其余解释字段一律回指该 artifact，不复制。",
            "reader_must": "读取方必须先校验该 artifact 的 rule_set_version 与本字段一致，再按 resolve_by 合并。",
        },
        "historical_candidates": items,
    }

    blob = json.dumps(doc, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True)
    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(blob + ("\n" if args.pretty else ""))

    print("已投影: %s（%d 条轻量索引）" % (args.out, len(items)))
    for cid, n in per_object.items():
        print("  对象 %s → %d 条" % (cid, n))
    print("  结构状态分布: %s" % json.dumps(dict(status_counter), ensure_ascii=False))
    print("  回指: %s（artifact %s / %s）"
          % (SA_ARTIFACT_REL, sa.get("artifact_version"), rs))
    print("  故意不复制（回指代替）: %s" % ", ".join(REFERRED_KEYS))
    print("  ★ 未做任何判定 / 重算 / 排序（仅按 historical_cycle_id 升序）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
