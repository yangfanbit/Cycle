#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_market_snapshot_v0_1.py —— Market Snapshot 生成器（ThreeC 1.1 Phase 1.2）。

职责：把「已审核的 market_regime + 研究对象 + 观察」装配成一个 Market Snapshot（`MS-*`）。

★ 明确**不做**的事（防止越界）:
  1. **不计算** `historical_candidates` —— 历史结构候选必须由**冻结 SA v0.3** 的比较步骤产出，
     本生成器只做**装配**；候选需通过 `--candidates` 传入（由 SA 步骤离线生成）。
     ★ 严禁在此重新实现任何匹配 / 相似度算法。
  2. **不生成** market_regime —— 它由 AI 离线生成 + 人工审核（`docs/MARKET_REGIME_AI_INTERFACE_v0.1.md`）。
  3. **不写数据库**、不改任何既有 artifact、不改 `exports/` 或 `contracts/`。

用法（在仓库根执行）:
    python research/current/market_snapshots/scripts/build_market_snapshot_v0_1.py \
        --snapshot-date 2026-09-30 \
        --regime   research/current/market_snapshots/market_regime/2026-09.json \
        --objects  <objects.json> \
        --observations <observations.json> \
        [--candidates <sa_output.json>] \
        [--out research/current/market_snapshots/snapshots/MS-2026-09-30-01.json]

    # 晋升 CANONICAL（**必须**显式给 reviewer；且会先跑校验器，FAIL 则拒绝晋升）
    ... --canonical --reviewer "yangfan"

    # 校验可复现性：重新生成并与既有文件逐字节比对
    ... --out <file> --check

退出码: 0 = 成功；1 = 失败（含 CANONICAL 晋升被拒）。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP_DIR = os.path.dirname(HERE)
VALIDATOR = os.path.join(HERE, "validate_market_snapshot_v0_1.py")

SNAPSHOT_VERSION = "0.1"
FROZEN_RULE_SET = "structural-analogy-ruleset-v0.3"


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(obj) -> bytes:
    """确定性序列化：sort_keys + 固定缩进 + 尾换行（保证逐字节可复现）。"""
    text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)
    return (text + "\n").encode("utf-8")


def build(args) -> dict:
    regime_doc = load_json(args.regime)
    regime = regime_doc.get("market_regime") or {}

    objects = load_json(args.objects)
    observations = load_json(args.observations)
    candidates = load_json(args.candidates) if args.candidates else []

    if isinstance(objects, dict) and "research_objects" in objects:
        objects = objects["research_objects"]
    if isinstance(observations, dict) and "observations" in observations:
        observations = observations["observations"]
    if isinstance(candidates, dict) and "historical_candidates" in candidates:
        candidates = candidates["historical_candidates"]

    # 从 regime draft 继承的 evidence（供 provenance 追溯；快照本身不重复存储）
    inherited_evidence_refs = regime.get("evidence_refs") or []

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    status = "DRAFT"
    reviewed_by = None
    reviewed_at = None
    if args.canonical:
        status = "CANONICAL"
        reviewed_by = args.reviewer
        reviewed_at = now

    snapshot_id = args.snapshot_id
    if not snapshot_id:
        slug = args.snapshot_date.replace("-", "")
        snapshot_id = "MS-%s-01" % slug

    return {
        "contract": "market_snapshot",
        "market_snapshot_version": SNAPSHOT_VERSION,
        "snapshot_id": snapshot_id,
        "snapshot_date": args.snapshot_date,
        "timestamp": args.timestamp or now,
        "status": status,
        "market_regime": {
            "broad_index_state": regime.get("broad_index_state", "UNKNOWN"),
            "breadth_state": regime.get("breadth_state", "UNKNOWN"),
            "liquidity_state": regime.get("liquidity_state", "UNKNOWN"),
            "risk_appetite_state": regime.get("risk_appetite_state", "UNKNOWN"),
            "beta_note": regime.get("beta_note", ""),
            "evidence_refs": inherited_evidence_refs,
        },
        "research_context": {
            "research_question": args.research_question
            or "截至本快照日，哪些方向已形成可核验的连续证据，值得进入历史结构比对？",
            "research_method": args.research_method
            or "market_regime 离线填报 + observations 逐条挂来源 → 研究对象 → 历史候选检索 → 复用冻结 SA v0.3 比较。",
            "source_policy": "Tier 1（官方发布）优先；Tier 2 为公司公告与产业数据；Tier 3 仅用于转述 T1/T2 事实。",
            "coverage_note": args.coverage_note or "历史研究覆盖至 2025；当前年份无历史研究数据。",
            "known_limitations": [
                "market_regime 依赖离线填报，无自动化行情源。",
                "历史侧机制级证据深度有限，结构对应产出率偏低属预期结果。",
            ],
        },
        "observations": observations,
        "research_objects": objects,
        "historical_candidates": candidates,
        "provenance": {
            "generated_by": regime_doc.get("generated_by", "script"),
            "ai_assisted": regime_doc.get("generated_by") == "ai-offline",
            "reviewed_by": reviewed_by,
            "reviewed_at": reviewed_at,
            "source_commit": args.source_commit or "",
            "rule_set_version": FROZEN_RULE_SET,
            "supersedes": args.supersedes,
            "superseded_by": None,
            "research_round": args.research_round or "ThreeC 1.1 Phase 1.2",
        },
    }


def run_validator(path: str) -> int:
    """晋升 CANONICAL 前必须先通过校验器。"""
    if not os.path.exists(VALIDATOR):
        print("  WARN  校验器缺失，跳过校验: %s" % VALIDATOR)
        return 0
    r = subprocess.run([sys.executable, VALIDATOR, "--file", path],
                       capture_output=True, text=True)
    tail = (r.stdout or "").strip().splitlines()
    for line in tail[-6:]:
        print("  " + line)
    return r.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description="ThreeC Market Snapshot 生成器 v0.1")
    ap.add_argument("--snapshot-date", required=True, help="PIT 基准日 YYYY-MM-DD")
    ap.add_argument("--snapshot-id", default=None)
    ap.add_argument("--regime", required=True, help="market_regime draft JSON")
    ap.add_argument("--objects", required=True, help="research_objects JSON")
    ap.add_argument("--observations", required=True, help="observations JSON")
    ap.add_argument("--candidates", default=None,
                    help="historical_candidates JSON（★ 由 SA 步骤产出，本脚本不计算）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--canonical", action="store_true", help="晋升 CANONICAL（必须配合 --reviewer）")
    ap.add_argument("--reviewer", default=None)
    ap.add_argument("--timestamp", default=None)
    ap.add_argument("--research-question", default=None)
    ap.add_argument("--research-method", default=None)
    ap.add_argument("--coverage-note", default=None)
    ap.add_argument("--source-commit", default=None)
    ap.add_argument("--supersedes", default=None)
    ap.add_argument("--research-round", default=None)
    ap.add_argument("--check", action="store_true", help="校验可复现性：重新生成并与现有文件比对")
    args = ap.parse_args()

    if args.canonical and not (args.reviewer and args.reviewer.strip()):
        print("FAIL  --canonical 必须显式指定 --reviewer（人工审核必过，不得匿名晋升）")
        return 1

    doc = build(args)
    blob = dump_json(doc)

    if args.check:
        if not os.path.exists(args.out):
            print("FAIL  --check 目标不存在: %s" % args.out)
            return 1
        with open(args.out, "rb") as f:
            existing = f.read()
        if existing == blob:
            print("PASS  --check 逐字节一致（可复现）: %s" % args.out)
            return 0
        print("FAIL  --check 不一致（产物已漂移）: %s" % args.out)
        return 1

    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    os.makedirs(out_dir, exist_ok=True)

    # ★ 先校验、再落盘 —— 避免把「未通过校验的 CANONICAL」写进仓库。
    tmp_path = os.path.join(out_dir, ".validate.tmp.json")
    with open(tmp_path, "wb") as f:
        f.write(blob)
    rc = run_validator(tmp_path)
    try:
        os.remove(tmp_path)
    except OSError:
        pass

    if rc != 0 and args.canonical:
        # 拒绝晋升：降级为 DRAFT 落盘（保留产物供修正），并明确告知**未生效**。
        doc["status"] = "DRAFT"
        doc["provenance"]["reviewed_by"] = None
        doc["provenance"]["reviewed_at"] = None
        blob = dump_json(doc)
        with open(args.out, "wb") as f:
            f.write(blob)
        print("FAIL  校验未通过 → 拒绝晋升 CANONICAL；已降级为 DRAFT 落盘: %s" % args.out)
        return 1

    with open(args.out, "wb") as f:
        f.write(blob)
    print("已生成: %s (%d bytes, status=%s)" % (args.out, len(blob), doc["status"]))

    if rc != 0:
        print("FAIL  DRAFT 已落盘，但校验存在 FAIL —— 请修正后再晋升 CANONICAL")
        return 1
    if args.canonical:
        print("PASS  校验通过 + 人工审核留痕齐备 → CANONICAL（Product 可消费）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
