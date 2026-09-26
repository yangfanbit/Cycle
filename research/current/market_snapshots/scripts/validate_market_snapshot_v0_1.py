#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""validate_market_snapshot_v0_1.py —— Market Snapshot / market_regime 校验器（ThreeC 1.1 Phase 1.2）。

校验对象：
  1. Market Snapshot（`contract = "market_snapshot"`，契约 v0.1）
  2. market_regime AI draft（`contract = "market_regime_draft"`，接口 v0.1）

用法（在仓库根执行）:
    python research/current/market_snapshots/scripts/validate_market_snapshot_v0_1.py            # 校验本目录下全部 *.json（排除 schema/）
    python research/current/market_snapshots/scripts/validate_market_snapshot_v0_1.py --file X   # 校验指定文件

退出码: 0 = 全部通过（允许 WARN）；1 = 存在 FAIL。

校验项（Market Snapshot，V1–V10）:
  V1  contract / market_snapshot_version 合法；snapshot_id 前缀为 MS-
  V2  status ∈ {DRAFT, REVIEW, CANONICAL, ARCHIVED}
  V3  snapshot_date 合法（YYYY-MM-DD）且存在
  V4  PIT：observations 与 research_objects 的日期不得晚于 snapshot_date
  V5  market_regime 四维枚举合法 + beta_note 必填（V3'）
  V6  observations：必填字段齐、枚举合法、AFTER_SNAPSHOT 必须被隔离（不参与判断）
  V7  research_objects：resolution_state 合法；URO-* 仅允许 Draft（不得直接进 Product）
  V8  historical_candidates：rule_set_version 必须是冻结 SA v0.3；**不得出现** score/ranking/probability/prediction
  V9  status = CANONICAL 时必须具备人工审核留痕（provenance.reviewed_by / reviewed_at）
  V10 provenance.generated_by 合法；ai_assisted = true 时不得为 CANONICAL 而无审核留痕

校验项（market_regime draft，R1–R10；对应接口文档 V1–V10）:
  R1  contract / version 合法
  R2  四维枚举合法
  R3  beta_note 必填
  R4  evidence_refs 至少 1 条且能在 evidence[] 中找到
  R5  PIT：每条 evidence.source_date <= snapshot_date
  R6  非 UNKNOWN 的维度必须至少有 1 条同维度证据
  R7  UNKNOWN 的维度必须在 unknown_notes 写明原因
  R8  risk_appetite_state 非 UNKNOWN 时须 >=2 个独立信号
  R9  不得出现 score / probability / prediction / signal / ranking 关键词
  R10 generated_by 必须为 ai-offline（AI 产物必须显式标注）

本脚本**只读**：不修改任何数据、不生成数据库、不写 schema。
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP_DIR = os.path.dirname(HERE)
SCHEMA_DIR = os.path.join(SNAP_DIR, "schema")

PASSES: list = []
WARNS: list = []
FAILS: list = []

DATE_RE = r"^\d{4}-\d{2}-\d{2}$"

STATUS_OK = {"DRAFT", "REVIEW", "CANONICAL", "ARCHIVED"}

REGIME_DIMS = {
    "broad_index_state": {"UP", "FLAT", "DOWN", "UNKNOWN"},
    "breadth_state": {"BROAD", "NORMAL", "NARROW", "UNKNOWN"},
    "liquidity_state": {"EXPANDING", "STABLE", "CONTRACTING", "UNKNOWN"},
    "risk_appetite_state": {"RISK_ON", "NEUTRAL", "RISK_OFF", "UNKNOWN"},
}

OBS_TYPE_OK = {"POLICY", "INDUSTRY", "COMPANY", "MARKET", "CAPITAL", "EXTERNAL"}
STRENGTH_OK = {"STRONG", "MEDIUM", "WEAK"}
DIRECTION_OK = {"SUPPORTIVE", "NEUTRAL", "NEGATIVE", "UNKNOWN"}
TEMPORAL_OK = {"BEFORE_SNAPSHOT", "AT_SNAPSHOT", "AFTER_SNAPSHOT", "UNKNOWN"}
RESOLUTION_OK = {"RESOLVED", "NEEDS_RESEARCH_ROUND", "INSUFFICIENT"}
PHASE_SOURCE_OK = {"DERIVED_FROM_EVIDENCE", "RESEARCH_DECLARED", "USER_DECLARED", "UNKNOWN"}
GENERATED_BY_OK = {"manual", "script", "ai-offline", "other"}

FROZEN_RULE_SET = "structural-analogy-ruleset-v0.3"

# 禁止出现在输出侧的词（红线）
BANNED_WORDS = [
    "score", "ranking", "probability", "prediction",
    "similarity_score", "win_rate", "expected_return",
]

import re


def ok(msg):
    PASSES.append(msg)


def warn(tag, msg):
    WARNS.append((tag, msg))


def fail(tag, msg):
    FAILS.append((tag, msg))


def is_date(v) -> bool:
    return isinstance(v, str) and re.match(DATE_RE, v) is not None


def scan_banned(text: str):
    low = text.lower()
    return [w for w in BANNED_WORDS if w in low]


def d_of(obj, key, default=None):
    v = obj.get(key, default)
    return v


# ---------------------------------------------------------------- Market Snapshot
def validate_snapshot(path: str, label: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        try:
            doc = json.load(f)
        except Exception as e:  # noqa: BLE001
            fail("V1·%s" % label, "JSON 解析失败: %s" % e)
            return

    if not isinstance(doc, dict):
        fail("V1·%s" % label, "顶层必须是 object")
        return

    # V1 contract / version / id
    if doc.get("contract") != "market_snapshot":
        fail("V1·%s" % label, "contract 应为 market_snapshot，实际 %r" % doc.get("contract"))
    else:
        ok("%s · V1 contract 合法" % label)

    if doc.get("market_snapshot_version") != "0.2":
        fail("V1·%s" % label, "market_snapshot_version 应为 0.2，实际 %r" % doc.get("market_snapshot_version"))
    else:
        ok("%s · V1 version 0.2" % label)

    sid = doc.get("snapshot_id")
    if not isinstance(sid, str) or not sid.startswith("MS-"):
        fail("V1·%s" % label, "snapshot_id 必须以前缀 MS- 开头，实际 %r" % sid)
    else:
        ok("%s · V1 snapshot_id 命名空间合法" % label)

    # V2 status
    status = doc.get("status")
    if status not in STATUS_OK:
        fail("V2·%s" % label, "status 非法: %r" % status)
    else:
        ok("%s · V2 status = %s" % (label, status))

    # V3 snapshot_date
    sdate = doc.get("snapshot_date")
    if not is_date(sdate):
        fail("V3·%s" % label, "snapshot_date 缺失或格式非法: %r" % sdate)
        sdate = None
    else:
        ok("%s · V3 snapshot_date = %s" % (label, sdate))

    # V5 market_regime
    regime = doc.get("market_regime") or {}
    if not isinstance(regime, dict):
        fail("V5·%s" % label, "market_regime 必须是 object")
    else:
        for dim, allowed in REGIME_DIMS.items():
            v = regime.get(dim)
            if v not in allowed:
                fail("V5·%s" % label, "market_regime.%s 非法: %r" % (dim, v))
        if not (isinstance(regime.get("beta_note"), str) and regime["beta_note"].strip()):
            fail("V5·%s" % label, "market_regime.beta_note 必填（β 不可分离说明）")
        else:
            ok("%s · V5 market_regime 四维 + beta_note 齐备" % label)

    # V4 PIT + V6 observations
    obs = doc.get("observations") or []
    if not isinstance(obs, list):
        fail("V6·%s" % label, "observations 必须是 array")
        obs = []

    after = 0
    for i, o in enumerate(obs):
        if not isinstance(o, dict):
            fail("V6·%s" % label, "observations[%d] 必须是 object" % i)
            continue
        for k in ("observation_id", "observation_type", "date", "claim", "evidence_strength", "direction"):
            if k not in o:
                fail("V6·%s" % label, "observations[%d] 缺字段 %s" % (i, k))
        if o.get("observation_type") not in OBS_TYPE_OK:
            fail("V6·%s" % label, "observations[%d].observation_type 非法: %r" % (i, o.get("observation_type")))
        if o.get("evidence_strength") not in STRENGTH_OK:
            fail("V6·%s" % label, "observations[%d].evidence_strength 非法: %r" % (i, o.get("evidence_strength")))
        if o.get("direction") not in DIRECTION_OK:
            fail("V6·%s" % label, "observations[%d].direction 非法: %r" % (i, o.get("direction")))
        tr = o.get("temporal_relation")
        if tr is not None and tr not in TEMPORAL_OK:
            fail("V6·%s" % label, "observations[%d].temporal_relation 非法: %r" % (i, tr))
        d = o.get("date")
        if is_date(d) and is_date(sdate):
            if d > sdate:
                if tr == "AFTER_SNAPSHOT":
                    after += 1
                else:
                    fail("V4·%s" % label, "observations[%d].date %s 晚于 snapshot_date 且未标 AFTER_SNAPSHOT" % (i, d))
    if obs:
        ok("%s · V6 observations 结构校验完成（%d 条）" % (label, len(obs)))
    if after:
        ok("%s · V4 已隔离 AFTER_SNAPSHOT 证据 %d 条（不参与判断）" % (label, after))

    # V7 research_objects
    objs = doc.get("research_objects") or []
    if not isinstance(objs, list) or len(objs) == 0:
        fail("V7·%s" % label, "research_objects 至少 1 条")
        objs = []
    for i, ro in enumerate(objs):
        if not isinstance(ro, dict):
            fail("V7·%s" % label, "research_objects[%d] 必须是 object" % i)
            continue
        oid = ro.get("object_id")
        rs = ro.get("resolution_state")
        if rs not in RESOLUTION_OK:
            fail("V7·%s" % label, "research_objects[%d].resolution_state 非法: %r" % (i, rs))
        ps = ro.get("phase_source")
        if ps is not None and ps not in PHASE_SOURCE_OK:
            fail("V7·%s" % label, "research_objects[%d].phase_source 非法: %r" % (i, ps))
        if isinstance(oid, str) and oid.startswith("URO-"):
            if ro.get("object_kind") != "user_research_object_draft":
                fail("V7·%s" % label, "research_objects[%d] 为 URO-* 但 object_kind 不是 user_research_object_draft" % i)
            if status == "CANONICAL":
                fail("V7·%s" % label, "URO-*（%s）为 Draft-only：CANONICAL 快照不得直接包含未评审的用户研究对象" % oid)
        if isinstance(oid, str) and (oid.startswith("C-") or oid.startswith("RC-")):
            fail("V7·%s" % label, "research_objects[%d].object_id %r 误用历史命名空间（C-/RC-）" % (i, oid))
    if objs:
        ok("%s · V7 research_objects 校验完成（%d 条）" % (label, len(objs)))

    # V8 historical_candidates（契约 v0.2：轻量索引，细节回指）
    SLIM_KEYS = {"identity", "structural_status", "strict_structural_supported"}
    cands = doc.get("historical_candidates") or []
    if not isinstance(cands, list):
        fail("V8·%s" % label, "historical_candidates 必须是 array")
        cands = []
    for i, c in enumerate(cands):
        if not isinstance(c, dict):
            fail("V8·%s" % label, "historical_candidates[%d] 必须是 object" % i)
            continue
        if "identity" not in c or "structural_status" not in c:
            fail("V8·%s" % label, "historical_candidates[%d] 缺 identity / structural_status" % i)
        extra = set(c.keys()) - SLIM_KEYS
        if extra:
            fail("V8·%s" % label,
                 "historical_candidates[%d] 含契约 v0.2 之外的字段（应回指而非复制）: %s"
                 % (i, ", ".join(sorted(extra))))
        hits = scan_banned(json.dumps(c, ensure_ascii=False))
        if hits:
            fail("V8·%s" % label, "historical_candidates[%d] 出现红线词: %s" % (i, ", ".join(hits)))

    # V8b candidates_source（有候选则必须回指）
    src = doc.get("candidates_source")
    if cands:
        src_ok = True
        if not isinstance(src, dict):
            fail("V8b·%s" % label, "有 historical_candidates 时必须提供 candidates_source（回指描述）")
            src_ok = False
        else:
            if src.get("rule_set_version") != FROZEN_RULE_SET:
                fail("V8b·%s" % label, "candidates_source.rule_set_version 必须是冻结 %s，实际 %r"
                     % (FROZEN_RULE_SET, src.get("rule_set_version")))
                src_ok = False
            if not src.get("artifact"):
                fail("V8b·%s" % label, "candidates_source.artifact 必填")
                src_ok = False
            if src.get("resolve_by") != "identity.historical_cycle_id":
                fail("V8b·%s" % label, "candidates_source.resolve_by 必须为 identity.historical_cycle_id")
                src_ok = False
        if src_ok:
            ok("%s · V8b candidates_source 回指校验通过（%s）" % (label, src.get("artifact")))
        ok("%s · V8 historical_candidates 轻量索引校验完成（%d 条，无多余字段）" % (label, len(cands)))

    # V9 / V10 provenance + CANONICAL 闸门
    prov = doc.get("provenance") or {}
    if not isinstance(prov, dict):
        fail("V10·%s" % label, "provenance 必须是 object")
        prov = {}
    gb = prov.get("generated_by")
    if gb not in GENERATED_BY_OK:
        fail("V10·%s" % label, "provenance.generated_by 非法: %r" % gb)

    if status == "CANONICAL":
        missing = []
        if not prov.get("reviewed_by"):
            fail("V9·%s" % label, "CANONICAL 快照必须有人审核留痕（provenance.reviewed_by）")
            missing.append("reviewed_by")
        if not prov.get("reviewed_at"):
            fail("V9·%s" % label, "CANONICAL 快照必须有审核时间（provenance.reviewed_at）")
            missing.append("reviewed_at")
        if not missing:
            ok("%s · V9 CANONICAL 审核留痕齐备" % label)
    if prov.get("ai_assisted") is True and gb != "ai-offline":
        warn("V10·%s" % label, "ai_assisted=true 但 generated_by=%r —— 建议统一标注" % gb)

    # 全局红线扫描
    full = json.dumps(doc, ensure_ascii=False)
    hits = scan_banned(full)
    if hits:
        fail("V8·%s" % label, "快照整体出现红线词: %s" % ", ".join(hits))
    else:
        ok("%s · 全局红线扫描通过（无 score/ranking/probability/prediction）" % label)


# ---------------------------------------------------------------- market_regime draft
def validate_regime(path: str, label: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        try:
            doc = json.load(f)
        except Exception as e:  # noqa: BLE001
            fail("R1·%s" % label, "JSON 解析失败: %s" % e)
            return

    if doc.get("contract") != "market_regime_draft":
        fail("R1·%s" % label, "contract 应为 market_regime_draft，实际 %r" % doc.get("contract"))
    else:
        ok("%s · R1 contract 合法" % label)

    if doc.get("market_regime_version") != "0.1":
        fail("R1·%s" % label, "market_regime_version 应为 0.1，实际 %r" % doc.get("market_regime_version"))
    else:
        ok("%s · R1 version 0.1" % label)

    sdate = doc.get("snapshot_date")
    if not is_date(sdate):
        fail("R5·%s" % label, "snapshot_date 缺失或格式非法: %r" % sdate)
        sdate = None
    else:
        ok("%s · R5 snapshot_date = %s" % (label, sdate))

    # R10 generated_by
    if doc.get("generated_by") != "ai-offline":
        fail("R10·%s" % label, "generated_by 必须为 ai-offline，实际 %r" % doc.get("generated_by"))
    else:
        ok("%s · R10 generated_by = ai-offline" % label)

    regime = doc.get("market_regime") or {}
    if not isinstance(regime, dict):
        fail("R2·%s" % label, "market_regime 必须是 object")
        return

    for dim, allowed in REGIME_DIMS.items():
        v = regime.get(dim)
        if v not in allowed:
            fail("R2·%s" % label, "market_regime.%s 非法: %r" % (dim, v))
    ok("%s · R2 四维枚举合法" % label)

    # R3 beta_note
    if not (isinstance(regime.get("beta_note"), str) and regime["beta_note"].strip()):
        fail("R3·%s" % label, "beta_note 必填")
    else:
        ok("%s · R3 beta_note 已填" % label)

    ev = doc.get("evidence") or []
    ev_ids = {e.get("evidence_id") for e in ev if isinstance(e, dict)}

    # R4 evidence_refs（★ 例外：四维全 UNKNOWN 的「诚实空态」允许为空）
    refs = regime.get("evidence_refs") or []
    all_unknown = all(regime.get(d) == "UNKNOWN" for d in REGIME_DIMS)
    if len(refs) < 1:
        if all_unknown:
            ok("%s · R4 四维全 UNKNOWN → 允许 evidence_refs 为空（诚实空态）" % label)
        else:
            fail("R4·%s" % label, "evidence_refs 至少 1 条（仅四维全 UNKNOWN 时可空）")
    for r in refs:
        if r not in ev_ids:
            fail("R4·%s" % label, "evidence_refs 中的 %r 在 evidence[] 中不存在" % r)
    if refs and all(r in ev_ids for r in refs):
        ok("%s · R4 evidence_refs 全部可解析（%d 条）" % (label, len(refs)))

    # R5 PIT
    for i, e in enumerate(ev):
        if not isinstance(e, dict):
            fail("R5·%s" % label, "evidence[%d] 必须是 object" % i)
            continue
        sd = e.get("source_date")
        if not is_date(sd):
            fail("R5·%s" % label, "evidence[%d].source_date 缺失或格式非法: %r" % (i, sd))
        elif is_date(sdate) and sd > sdate:
            fail("R5·%s" % label, "evidence[%d].source_date %s 晚于 snapshot_date（PIT 违规）" % (i, sd))
    if ev:
        ok("%s · R5 证据 PIT 校验完成（%d 条）" % (label, len(ev)))

    # R6 非 UNKNOWN 维度必须有同维度证据
    by_dim = {}
    for e in ev:
        if isinstance(e, dict):
            by_dim.setdefault(e.get("dimension"), []).append(e)
    for dim in REGIME_DIMS:
        v = regime.get(dim)
        if v is not None and v != "UNKNOWN":
            if not by_dim.get(dim):
                fail("R6·%s" % label, "%s = %s 但无任何 dimension=%s 的证据" % (dim, v, dim))
    ok("%s · R6 维度—证据配对校验完成" % label)

    # R7 UNKNOWN 必须写原因
    un = doc.get("unknown_notes") or {}
    for dim in REGIME_DIMS:
        if regime.get(dim) == "UNKNOWN":
            note = un.get(dim) if isinstance(un, dict) else None
            if not (isinstance(note, str) and note.strip()):
                fail("R7·%s" % label, "%s = UNKNOWN 但 unknown_notes.%s 未写明原因" % (dim, dim))
    ok("%s · R7 UNKNOWN 原因校验完成" % label)

    # R8 risk_appetite 需 >=2 独立信号
    if regime.get("risk_appetite_state") not in (None, "UNKNOWN"):
        sigs = by_dim.get("risk_appetite_state") or []
        metrics = {s.get("metric") for s in sigs if isinstance(s, dict)}
        if len(sigs) < 2:
            fail("R8·%s" % label, "risk_appetite_state 非 UNKNOWN 需 >=2 条独立信号，实际 %d 条" % len(sigs))
        elif len(metrics) < 2:
            warn("R8·%s" % label, "risk_appetite 有 %d 条证据但 metric 仅 %d 种 —— 请确认是否为独立信号"
                 % (len(sigs), len(metrics)))
        else:
            ok("%s · R8 risk_appetite 独立信号 %d 个" % (label, len(metrics)))

    # R9 红线词
    hits = scan_banned(json.dumps(doc, ensure_ascii=False))
    if hits:
        fail("R9·%s" % label, "出现红线词: %s" % ", ".join(hits))
    else:
        ok("%s · R9 红线扫描通过" % label)


def main() -> int:
    args = sys.argv[1:]
    files = []

    if "--file" in args:
        idx = args.index("--file")
        if idx + 1 < len(args):
            files.append(("file", args[idx + 1]))
    else:
        for root, dirs, fns in os.walk(SNAP_DIR):
            if os.path.abspath(root).startswith(os.path.abspath(SCHEMA_DIR)):
                continue
            for fn in sorted(fns):
                if fn.endswith(".json"):
                    p = os.path.join(root, fn)
                    rel = os.path.relpath(p, SNAP_DIR)
                    files.append((rel, p))

    if not files:
        print("未找到待校验文件（目录: %s）" % SNAP_DIR)
        return 0

    for label, path in files:
        if not os.path.exists(path):
            fail("IO", "文件不存在: %s" % path)
            continue
        with open(path, "r", encoding="utf-8") as f:
            try:
                head = json.load(f)
            except Exception as e:  # noqa: BLE001
                fail("IO·%s" % label, "JSON 解析失败: %s" % e)
                continue
        c = head.get("contract") if isinstance(head, dict) else None
        if c == "market_snapshot":
            validate_snapshot(path, label)
        elif c == "market_regime_draft":
            validate_regime(path, label)
        else:
            warn("IO·%s" % label, "未知 contract=%r —— 跳过（仅支持 market_snapshot / market_regime_draft）" % c)

    print("=" * 68)
    print("Market Snapshot / market_regime 验证（ThreeC 1.1 Phase 1.2）")
    print("=" * 68)
    for p in PASSES:
        print("  PASS  %s" % p)
    for t, m in WARNS:
        print("  WARN  [%s] %s" % (t, m))
    for t, m in FAILS:
        print("  FAIL  [%s] %s" % (t, m))
    print("-" * 68)
    print("结果: %d 通过 / %d 警告 / %d 失败" % (len(PASSES), len(WARNS), len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
