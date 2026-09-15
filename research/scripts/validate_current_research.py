#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""validate_current_research.py —— ThreeC Current Research Discovery 数据验证器（Phase 7）。

校验 `research/current/` 下的 Current Candidate 数据集与叙事标注是否满足协议。

用法（在仓库根执行）:
    python research/scripts/validate_current_research.py            # 校验 canonical 数据集
    python research/scripts/validate_current_research.py --all      # 额外校验 fixtures/
    python research/scripts/validate_current_research.py --file X   # 校验指定文件

退出码: 0 = 全部通过；1 = 存在 FAIL。

校验项（6 组）:
  1. Data Integrity      —— candidate_id 唯一 / snapshot_date / display_name / core_narrative / 枚举合法
  2. Temporal Integrity  —— source_date|event_date > snapshot_date 必须标 AFTER_SNAPSHOT；标记与推导必须一致
  3. Evidence Integrity  —— 每个候选至少 1 条可用证据，或显式在 uncertainty_notes 写明 UNKNOWN
  4. Phase Integrity     —— 禁止非法 phase；候选级的 phase 不得为 END
  5. Similarity Integrity—— reference_cases 必须引用真实存在且 start_date <= snapshot_date 的案例；
                            叙事标注必须引用真实存在的案例、类型合法
  6. Theme Boundary      —— 候选不得使用 C-/RC- 前缀，不得同名于 campaigns / research_candidates，
                            也不得出现在 exports/timeline_export_v1.json 的任何 id 中

本脚本**只读**：不修改任何数据。
"""

from __future__ import annotations

import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT_DIR = os.path.join(ROOT, "research", "current")
EXPORT_PATH = os.path.join(ROOT, "exports", "timeline_export_v1.json")

CANONICAL = os.path.join(CURRENT_DIR, "current_candidates.json")
FIXTURES_DIR = os.path.join(CURRENT_DIR, "fixtures")
ANNOTATIONS = os.path.join(CURRENT_DIR, "narrative_annotations.json")

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CANDIDATE_ID_RE = re.compile(r"^(FX-|CC-)[A-Za-z0-9._-]+$")

VALID_STATUS = {"CANDIDATE", "WATCH", "RESEARCHING", "PROMOTABLE", "REJECTED"}
VALID_PHASE = {
    "EARLY_SIGNAL", "THEME_FORMING", "BROAD_CONFIRMATION",
    "EXPANSION", "PEAK", "DECLINE", "UNKNOWN",
}
VALID_SIGNAL_LEVEL = {"ABSENT", "EMERGING", "PRESENT", "STRONG", "WEAKENING", "UNKNOWN"}
VALID_SOURCE_TYPE = {
    "POLICY", "INDUSTRY", "COMPANY", "MARKET", "MACRO", "CAPITAL", "SENTIMENT", "OTHER",
}
VALID_STRENGTH = {"STRONG", "MEDIUM", "WEAK"}
VALID_DIRECTION = {"SUPPORTIVE", "NEUTRAL", "NEGATIVE", "UNKNOWN"}
VALID_TEMPORAL = {"BEFORE_SNAPSHOT", "AT_SNAPSHOT", "AFTER_SNAPSHOT", "UNKNOWN"}
VALID_DIMENSIONS = [
    "narrative", "policy", "industry", "market",
    "capital", "breadth", "company", "information_marginal",
]
VALID_NARRATIVE_TYPE = {
    "POLICY_DRIVEN", "INDUSTRY_UPGRADE", "TECH_BREAKTHROUGH", "DEMAND_SURGE",
    "SUPPLY_CONTRACTION", "VALUATION_RESET", "CYCLE_REVERSAL", "EVENT_CATALYST",
    "UNKNOWN",
}

PASSES: list[str] = []
FAILS: list[tuple[str, str]] = []
WARNS: list[tuple[str, str]] = []


def ok(item: str) -> None:
    PASSES.append(item)


def fail(item: str, msg: str) -> None:
    FAILS.append((item, msg))


def warn(item: str, msg: str) -> None:
    WARNS.append((item, msg))


def load_json(path: str):
    with io.open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evidence_date(item: dict):
    return item.get("source_date") or item.get("event_date") or None


def derive_temporal(date, snapshot: str) -> str:
    if not date or not snapshot:
        return "UNKNOWN"
    if date < snapshot:
        return "BEFORE_SNAPSHOT"
    if date == snapshot:
        return "AT_SNAPSHOT"
    return "AFTER_SNAPSHOT"


def load_export_ids() -> tuple[set, dict, bool]:
    """返回 (全部 id 集合, {campaign_id: start_date}, export 是否存在)。"""
    if not os.path.isfile(EXPORT_PATH):
        return set(), {}, False
    data = load_json(EXPORT_PATH)
    ids = set()
    starts = {}
    for key in ("campaigns", "research_candidates"):
        for c in data.get(key, []):
            cid = c.get("campaign_id")
            if cid:
                ids.add(cid)
                starts[cid] = c.get("start_date")
    return ids, starts, True


# ------------------------------------------------------------------ 校验主体
def validate_dataset(path: str, label: str, export_ids: set, export_starts: dict) -> None:
    if not os.path.isfile(path):
        fail(label, "文件缺失: %s" % os.path.relpath(path, ROOT).replace("\\", "/"))
        return
    try:
        data = load_json(path)
    except Exception as e:  # noqa: BLE001
        fail(label, "JSON 解析失败: %s" % e)
        return

    rel = os.path.relpath(path, ROOT).replace("\\", "/")

    # ---------------- 1. Data Integrity ----------------
    if data.get("contract") != "current_candidates":
        fail(label, "contract 应为 current_candidates，实际 %r" % data.get("contract"))
    else:
        ok("%s · contract = current_candidates" % label)

    snapshot = data.get("snapshot_date")
    if not snapshot or not DATE_RE.match(str(snapshot)):
        fail(label, "缺少或非法的 snapshot_date: %r（Temporal Firewall 无法工作）" % snapshot)
        snapshot = None
    else:
        ok("%s · snapshot_date = %s" % (label, snapshot))

    candidates = data.get("candidates")
    if not isinstance(candidates, list):
        fail(label, "candidates 必须是数组")
        return

    seen_ids: set[str] = set()
    seen_evidence: set[str] = set()

    for cand in candidates:
        cid = cand.get("candidate_id")

        # --- id 唯一 + 命名空间 + Theme Boundary ---
        if not cid:
            fail(label, "存在缺少 candidate_id 的候选")
            continue
        if cid in seen_ids:
            fail(label, "candidate_id 重复: %s" % cid)
        seen_ids.add(cid)
        if not CANDIDATE_ID_RE.match(cid):
            fail(label, "%s: candidate_id 必须使用 CC- / FX- 前缀（命名空间隔离）" % cid)
        if cid in export_ids:
            fail(label, "%s: 候选 ID 与 export 中的正式 Campaign / Research Candidate 同名（Theme Boundary 违规）" % cid)

        # --- 必填字段 ---
        if not cand.get("display_name"):
            fail(label, "%s: 缺少 display_name" % cid)
        if not cand.get("core_narrative"):
            fail(label, "%s: 缺少 core_narrative" % cid)

        # --- 候选自身快照日不得晚于数据集 ---
        csnap = cand.get("snapshot_date")
        if not csnap or not DATE_RE.match(str(csnap)):
            fail(label, "%s: 缺少或非法的 snapshot_date" % cid)
        elif snapshot and csnap > snapshot:
            fail(label, "%s: candidate.snapshot_date(%s) 晚于数据集(%s)" % (cid, csnap, snapshot))

        # --- 状态枚举 ---
        status = cand.get("candidate_status")
        if status not in VALID_STATUS:
            fail(label, "%s: 非法 candidate_status = %r" % (cid, status))

        # --- 4. Phase Integrity ---
        phase = cand.get("attention_state")
        if phase not in VALID_PHASE:
            fail(label, "%s: 非法 attention_state = %r" % (cid, phase))
        elif phase == "END":
            fail(label, "%s: 候选阶段不得为 END（END 只属于已结束的历史 Campaign）" % cid)

        # --- phase_evidence 维度与水平 ---
        pe = cand.get("phase_evidence")
        if pe is not None:
            if not isinstance(pe, dict):
                fail(label, "%s: phase_evidence 必须是对象" % cid)
            else:
                for dim, level in pe.items():
                    if dim not in VALID_DIMENSIONS:
                        fail(label, "%s: phase_evidence 非法维度 %r" % (cid, dim))
                    if level not in VALID_SIGNAL_LEVEL:
                        fail(label, "%s: phase_evidence.%s 非法水平 %r" % (cid, dim, level))

        # --- 25 叙事类型 ---
        for nt in cand.get("narrative_types") or []:
            if nt not in VALID_NARRATIVE_TYPE:
                fail(label, "%s: 非法 narrative_types = %r" % (cid, nt))

        # --- 2. Temporal Integrity + 3. Evidence Integrity ---
        evidence = cand.get("evidence") or []
        if not isinstance(evidence, list):
            fail(label, "%s: evidence 必须是数组" % cid)
            evidence = []

        admissible = 0
        for ev in evidence:
            eid = ev.get("evidence_id")
            if not eid:
                fail(label, "%s: 存在缺少 evidence_id 的证据" % cid)
            elif eid in seen_evidence:
                warn(label, "%s: evidence_id 全局重复 %s" % (cid, eid))
            else:
                seen_evidence.add(eid)

            if ev.get("source_type") not in VALID_SOURCE_TYPE:
                fail(label, "%s/%s: 非法 source_type = %r" % (cid, eid, ev.get("source_type")))
            if ev.get("evidence_strength") not in VALID_STRENGTH:
                fail(label, "%s/%s: 非法 evidence_strength = %r" % (cid, eid, ev.get("evidence_strength")))
            if not ev.get("claim"):
                fail(label, "%s/%s: 缺少 claim（事实陈述）" % (cid, eid))
            direction = ev.get("direction")
            if direction is not None and direction not in VALID_DIRECTION:
                fail(label, "%s/%s: 非法 direction = %r" % (cid, eid, direction))

            declared = ev.get("temporal_relation")
            if declared is not None and declared not in VALID_TEMPORAL:
                fail(label, "%s/%s: 非法 temporal_relation = %r" % (cid, eid, declared))

            # 关键：时间关系推导（以候选自身 snapshot_date 为基准）
            derived = derive_temporal(evidence_date(ev), csnap)
            if derived == "AFTER_SNAPSHOT":
                if declared != "AFTER_SNAPSHOT":
                    fail(
                        label,
                        "%s/%s: 证据日期 %s 晚于快照 %s，必须显式标记 temporal_relation = "
                        "AFTER_SNAPSHOT（否则会被误用于当前判断）"
                        % (cid, eid, evidence_date(ev), csnap),
                    )
                # AFTER_SNAPSHOT 不计入可用证据（不得参与判断）
                continue
            if declared is not None and declared != derived:
                fail(
                    label,
                    "%s/%s: 声明的 temporal_relation=%s 与推导值 %s 不一致"
                    % (cid, eid, declared, derived),
                )
            if derived in ("BEFORE_SNAPSHOT", "AT_SNAPSHOT"):
                admissible += 1

        if admissible == 0:
            notes = " ".join(cand.get("uncertainty_notes") or [])
            if "UNKNOWN" not in notes.upper():
                fail(
                    label,
                    "%s: 没有任何快照内可用证据，必须在 uncertainty_notes 明确写出 UNKNOWN" % cid,
                )
            else:
                ok("%s · %s: 无可用证据，但已显式声明 UNKNOWN" % (label, cid))

        # --- 5. Similarity Integrity：reference_cases ---
        for rc in cand.get("reference_cases") or []:
            rid = rc.get("campaign_id")
            if not rid:
                fail(label, "%s: reference_cases 缺少 campaign_id" % cid)
                continue
            if rid not in export_ids:
                fail(label, "%s: reference_cases 引用了不存在的历史案例 %s" % (cid, rid))
                continue
            start = export_starts.get(rid)
            if start and csnap and start > csnap:
                fail(
                    label,
                    "%s: reference_cases 引用的 %s 起始于 %s，晚于快照 %s（引用未来历史记录）"
                    % (cid, rid, start, csnap),
                )

    ok("%s · %d 个候选完成 6 组校验" % (label, len(candidates)))


def validate_annotations(path: str, export_ids: set, export_starts: dict) -> None:
    label = "narrative_annotations"
    if not os.path.isfile(path):
        warn(label, "文件缺失（Narrative 层将不参与相似度）")
        return
    try:
        data = load_json(path)
    except Exception as e:  # noqa: BLE001
        fail(label, "JSON 解析失败: %s" % e)
        return
    if data.get("contract") != "narrative_annotations":
        fail(label, "contract 应为 narrative_annotations，实际 %r" % data.get("contract"))
        return

    seen = set()
    for a in data.get("annotations") or []:
        cid = a.get("campaign_id")
        if not cid:
            fail(label, "存在缺少 campaign_id 的标注")
            continue
        if cid in seen:
            warn(label, "重复标注: %s" % cid)
        seen.add(cid)
        if export_ids and cid not in export_ids:
            fail(label, "%s: 标注引用了不存在的历史案例" % cid)
        for nt in a.get("narrative_types") or []:
            if nt not in VALID_NARRATIVE_TYPE:
                fail(label, "%s: 非法叙事类型 %r" % (cid, nt))
        if not a.get("provenance"):
            warn(label, "%s: 缺少 provenance（标注依据不可回查）" % cid)

    ok("%s · %d 条标注完成校验" % (label, len(seen)))


def main() -> int:
    args = sys.argv[1:]
    files: list[tuple[str, str]] = []

    if "--file" in args:
        p = args[args.index("--file") + 1]
        files = [("custom", p if os.path.isabs(p) else os.path.join(ROOT, p))]
    else:
        files = [("canonical", CANONICAL)]

    if "--all" in args and os.path.isdir(FIXTURES_DIR):
        for fn in sorted(os.listdir(FIXTURES_DIR)):
            if fn.endswith(".json"):
                files.append(("fixture:" + fn, os.path.join(FIXTURES_DIR, fn)))

    export_ids, export_starts, export_ok = load_export_ids()
    if not export_ok:
        warn("export", "exports/timeline_export_v1.json 缺失 → Similarity / Theme Boundary 只做内部一致性检查")
    else:
        ok("export · 载入 %d 个历史案例 id" % len(export_ids))

    for label, path in files:
        validate_dataset(path, label, export_ids, export_starts)

    validate_annotations(ANNOTATIONS, export_ids, export_starts)

    print("=" * 68)
    print("Current Research Discovery 验证 (Phase 7)")
    print("=" * 68)
    for p in PASSES:
        print("  PASS  %s" % p)
    for w, m in WARNS:
        print("  WARN  [%s] %s" % (w, m))
    for f, m in FAILS:
        print("  FAIL  [%s] %s" % (f, m))
    print("-" * 68)
    print("结果: %d 通过 / %d 警告 / %d 失败" % (len(PASSES), len(WARNS), len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
