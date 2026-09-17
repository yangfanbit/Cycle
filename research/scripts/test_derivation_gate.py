"""派生结构门（Derivation Gate）回归测试 —— Phase 7.3.2。

规则：`derived_from_early_signal = true` 的 lifecycle rhythm **不构成独立时间规律**，
不得作为独立 Time Observation Pattern 晋级为 `TIMELINE_CANDIDATE`。

覆盖 5 条必须验证的行为（对应 Phase 7.3.2 验收清单）：

    1. derived = true            → 不得晋级为独立 Timeline Pattern（降级 EXPLORATORY）
    2. derived = false           → 原规则继续生效（**不得被误降级**）
    3. 缺字段 / 无节奏判定        → 安全处理，**不默认派生**，也不默认「已证非派生」
    4. 派生候选保留 source trace  → derived_from_pattern_id / derived_from_stage /
                                   stage_verdicts / note 齐备
    5. canonical Macro Theme resolution 不回退 direct

另加 2 组产物级检查：
    6. 产物级一致性（派生候选不得为 effective TIMELINE_CANDIDATE；来源引用必须真实存在）
    7. CSV 可追溯列齐备且自解释（人工浏览视图同样能看到「为什么」）

设计说明（重要）
----------------
真实产物中 `is_derived = False` 的候选数为 **0**，且不存在「阶段缺字段」的情形。
因此第 2、3 条**只能用合成输入做单元测试** —— 若只对真实产物断言，
这两条路径**永远不会被执行到**，等于没测。

用法: python scripts/test_derivation_gate.py
退出码：0 = 全部通过；1 = 失败。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import discover_time_observation_patterns as D
from scripts import theme_taxonomy as TT

REPORTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "research", "reports",
)
ARTIFACT = os.path.join(REPORTS, "time_observation_candidate_pool_v0_4.json")


# ---------------------------------------------------------------- 合成夹具

def _stage(stage, derived, center="06-22", lag=10, pred="06-21", resid=1):
    """构造一个节奏分析阶段记录。"""
    return {
        "stage": stage,
        "n": 7,
        "center_md": center,
        "median_lag_from_early_signal_days": lag,
        "predicted_center_md": pred,
        "center_residual_days": resid,
        "derived_from_early_signal": derived,
    }


def _rhythm(scope, stages):
    return {
        scope: {
            "status": "OK",
            "baseline_stage": "EARLY_SIGNAL",
            "baseline_center_md": "06-11",
            "baseline_n": 7,
            "stages": stages,
        }
    }


def _cand(pid, scope, stage, promotion="TIMELINE_CANDIDATE", n=7):
    return {
        "pattern_id": pid,
        "scope_id": scope,
        "lifecycle_stage": stage,
        "promotion_status": promotion,
        "sample_size": n,
        "name": pid,
    }


def _tcr(pairs):
    return {"detail": [{"pattern_id": p, "robustness_verdict": v} for p, v in pairs]}


def _run(cands, tcr, rhythm):
    D.annotate_effective_status(cands, tcr, rhythm)
    return {c["pattern_id"]: c for c in cands}


def _dv(c):
    """取出 derivation_verdict，缺失时给出**可诊断**的失败信息（而非 KeyError）。"""
    dv = c.get("derivation_verdict")
    assert dv is not None, (
        "%s 缺少 derivation_verdict —— 派生门未生效或未写入" % c.get("pattern_id")
    )
    return dv


# ---------------------------------------------------------------- 1. derived = true

def test_derived_true_not_promoted():
    """① 判定为派生的候选不得晋级为独立 Timeline Pattern。"""
    rhythm = _rhythm("S1", [_stage("MAIN_RISE", True)])
    cands = [_cand("P-0", "S1", "EARLY_SIGNAL"), _cand("P-1", "S1", "MAIN_RISE")]
    by = _run(cands, _tcr([("P-0", "ROBUST"), ("P-1", "ROBUST")]), rhythm)

    dv = _dv(by["P-1"])
    assert dv["is_derived"] is True, "MAIN_RISE 应判定为派生"
    assert by["P-1"]["effective_promotion_status"] == "EXPLORATORY", (
        "派生候选必须降级，实际 %s" % by["P-1"]["effective_promotion_status"]
    )
    assert by["P-1"]["effective_status_reason"], "降级必须记录原因"
    # 降级落点必须是 EXPLORATORY 而非 RESEARCH_ONLY：
    # 该候选数值门槛已通过，缺的是「独立性」—— 正是 EXPLORATORY 的定义。
    assert by["P-1"]["effective_promotion_status"] != "RESEARCH_ONLY", (
        "派生降级不得使用 RESEARCH_ONLY（其定义为数值弱，语义不符）"
    )
    # 基线候选（EARLY_SIGNAL）不受派生门影响
    assert by["P-0"]["effective_promotion_status"] == "TIMELINE_CANDIDATE", (
        "EARLY_SIGNAL 基线本身不得被派生门降级"
    )
    print("PASS: ① derived=true → 降级 EXPLORATORY，基线不受影响")


# ---------------------------------------------------------------- 2. derived = false

def test_derived_false_rule_still_applies():
    """② 明确非派生（残差 > 21 天）→ 原规则继续生效，不得被误降级。"""
    rhythm = _rhythm("S1", [_stage("MAIN_RISE", False, resid=40)])
    cands = [_cand("P-0", "S1", "EARLY_SIGNAL"), _cand("P-1", "S1", "MAIN_RISE")]
    by = _run(cands, _tcr([("P-0", "ROBUST"), ("P-1", "ROBUST")]), rhythm)

    dv = _dv(by["P-1"])
    assert dv["is_derived"] is False, "残差 40 天应判定为非派生"
    assert by["P-1"]["effective_promotion_status"] == "TIMELINE_CANDIDATE", (
        "非派生候选不得被派生门降级，实际 %s" % by["P-1"]["effective_promotion_status"]
    )
    assert by["P-1"]["effective_status_reason"] is None, "未降级不应写降级原因"
    assert dv["derived_from_pattern_id"] is None, "非派生不得带来源字段（误导性）"
    print("PASS: ② derived=false → 原规则继续生效，未被误降级")


# ---------------------------------------------------------------- 3. 缺字段安全处理

def test_missing_fields_safe():
    """③ 缺字段 / 无节奏判定 → 安全处理：不默认派生，也不默认「已证非派生」。"""
    cases = [
        ("scope 无节奏分析", _rhythm("OTHER", [_stage("MAIN_RISE", True)])),
        ("阶段不在 export 10 阶段内", _rhythm("S1", [_stage("PHASE_MAIN_RISE", True)])),
        ("阶段条目存在但缺 derived 字段",
         _rhythm("S1", [{"stage": "MAIN_RISE", "n": 7, "center_md": "06-22"}])),
        ("derived 字段为 null",
         _rhythm("S1", [_stage("MAIN_RISE", None)])),
    ]
    for label, rhythm in cases:
        cands = [_cand("P-0", "S1", "EARLY_SIGNAL"), _cand("P-1", "S1", "MAIN_RISE")]
        by = _run(cands, _tcr([("P-0", "ROBUST"), ("P-1", "ROBUST")]), rhythm)
        dv = _dv(by["P-1"])

        assert dv["is_derived"] is None, (
            "[%s] 缺证据应返回 None（无结论），实际 %r" % (label, dv["is_derived"])
        )
        assert dv["is_derived"] is not False, (
            "[%s] 缺字段**不得**被当作「明确非派生」—— False 是肯定性断言" % label
        )
        assert dv["reason"], "[%s] 不下结论必须记录 reason" % label
        assert by["P-1"]["effective_promotion_status"] == "TIMELINE_CANDIDATE", (
            "[%s] 无判定不得降级，实际 %s" % (label, by["P-1"]["effective_promotion_status"])
        )
        assert dv["derived_from_pattern_id"] is None, "[%s] 无判定不得带来源字段" % label
    print("PASS: ③ 缺字段 / 无节奏判定 → None，不降级，reason 齐备（4 种情形）")


# ---------------------------------------------------------------- 4. source trace

def test_source_trace_preserved():
    """④ 派生候选必须保留可追溯来源，不得简单删除或只留状态。"""
    rhythm = _rhythm("S1", [
        _stage("MAIN_RISE", True),
        _stage("PEAK", True, center="07-11", lag=40, pred="07-21", resid=10),
    ])
    cands = [
        _cand("P-0", "S1", "EARLY_SIGNAL"),
        _cand("P-1", "S1", "MAIN_RISE"),
        _cand("P-2", "S1", "MAIN_RISE->PEAK"),
    ]
    by = _run(
        cands,
        _tcr([("P-0", "ROBUST"), ("P-1", "ROBUST"), ("P-2", "ROBUST")]),
        rhythm,
    )

    for pid, expect_stages in (("P-1", ["MAIN_RISE"]), ("P-2", ["MAIN_RISE", "PEAK"])):
        c = by[pid]
        dv = _dv(c)
        # §6 要求的可追溯字段
        assert c["pattern_id"], "%s 缺少 candidate_id" % pid
        assert c["lifecycle_stage"], "%s 缺少 source lifecycle" % pid
        assert dv["is_derived"] is True, "%s 应为派生" % pid
        assert dv["derived_from_pattern_id"] == "P-0", (
            "%s 的 derived_from_pattern_id 应为 P-0，实际 %r" % (pid, dv["derived_from_pattern_id"])
        )
        assert dv["derived_from_stage"] == "EARLY_SIGNAL", "%s 缺少派生基线阶段" % pid
        assert sorted(dv["stage_verdicts"]) == expect_stages, (
            "%s stage_verdicts 应为 %s，实际 %s" % (pid, expect_stages, sorted(dv["stage_verdicts"]))
        )
        assert dv["note"], "%s 缺少 derivation note" % pid
        assert "P-0" in dv["note"], "%s 的 note 应指明来源候选" % pid
        assert c["effective_promotion_status"] == "EXPLORATORY", "%s 应降级" % pid
        assert c["promotion_status"] == "TIMELINE_CANDIDATE", (
            "%s 原始数值门槛结论应保留（可审计），不得被覆盖" % pid
        )
    print("PASS: ④ 派生候选来源可追溯（含多阶段过渡），原始状态保留")


# ---------------------------------------------------------------- 5. canonical resolution

def test_canonical_resolution_not_direct():
    """⑤ canonical Macro Theme resolution 不回退 direct。"""
    assert not D.LEGACY_DIRECT_RESOLUTION, "默认轮次不得启用 legacy direct 口径"
    assert D.ROUND_PROFILES[D.DEFAULT_ROUND]["direct_resolution"] is False, (
        "默认轮次档案必须声明 direct_resolution=False"
    )
    assert D.ROUND_PROFILES[D.DEFAULT_ROUND]["derivation_gate"] is True, (
        "默认轮次档案必须声明 derivation_gate=True"
    )

    with open(ARTIFACT, "r", encoding="utf-8") as f:
        art = json.load(f)
    tr = art.get("theme_resolution")
    assert tr, "产物缺少 theme_resolution（canonical 解析报告）"
    assert tr["ruleset"] == TT.RULESET, (
        "theme_resolution.ruleset 应为 %s，实际 %s" % (TT.RULESET, tr["ruleset"])
    )
    # 4 个「只登记子主题」的对象必须被 canonical 口径正确归属（direct 口径会判为空）
    expect = {
        "C-2019-AD": "TH-AUTO",
        "RC-2024-SECONDARY": "TH-AUTO",
        "RC-2020-PANDEMIC": "TH-PHARMA",
        "RC-2021-TCM": "TH-PHARMA",
    }
    got = {r["campaign_id"]: r for r in tr["objects_resolved"]}
    for cid, macro in expect.items():
        assert cid in got, "解析报告缺少对象 %s" % cid
        assert macro in got[cid]["macro_theme_ids"], (
            "%s 应归属 %s，实际 %s" % (cid, macro, got[cid]["macro_theme_ids"])
        )
        assert got[cid]["status"] == "RESOLVED", (
            "%s 状态应为 RESOLVED，实际 %s" % (cid, got[cid]["status"])
        )
    print("PASS: ⑤ canonical CMTR v1 生效，未回退 direct（4 个对象归属正确）")


# ---------------------------------------------------------------- 产物级一致性

def test_artifact_consistency():
    """产物级：派生候选不得以 TIMELINE_CANDIDATE 出现；来源引用必须真实存在。"""
    with open(ARTIFACT, "r", encoding="utf-8") as f:
        art = json.load(f)
    cands = art["candidates"]
    ids = {c["pattern_id"] for c in cands}
    derived = []
    for c in cands:
        dv = c.get("derivation_verdict")
        assert dv is not None, "%s 缺少 derivation_verdict" % c["pattern_id"]
        if dv.get("is_derived") is True:
            derived.append(c["pattern_id"])
            assert c["effective_promotion_status"] != "TIMELINE_CANDIDATE", (
                "%s 判定为派生却仍为 effective TIMELINE_CANDIDATE" % c["pattern_id"]
            )
            src = dv.get("derived_from_pattern_id")
            assert src and src in ids, (
                "%s 的来源 %r 不是已存在的候选（不可追溯）" % (c["pattern_id"], src)
            )
            assert dv.get("note"), "%s 缺少 derivation note" % c["pattern_id"]
        else:
            assert not dv.get("derived_from_pattern_id"), (
                "%s 非派生却带来源字段" % c["pattern_id"]
            )
    assert derived, "产物中应存在被判定为派生的候选（否则本测试形同虚设）"
    # 本轮已知的 2 条被降级候选必须在内
    for pid in ("TOPC-004", "TOPC-021"):
        assert pid in derived, "%s 应被判定为派生" % pid
    print("PASS: 产物级一致性（%d 条派生候选，来源引用全部有效）" % len(derived))


def test_csv_traceability_columns():
    """CSV（人工浏览视图）必须同样携带派生来源，否则只看到状态看不到原因。"""
    import csv as _csv

    csv_path = ARTIFACT[:-5] + ".csv"
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(_csv.DictReader(f))
    assert rows, "CSV 为空"
    cols = set(rows[0].keys())
    for col in ("is_derived", "derived_from_pattern_id", "derived_from_stage", "derivation_note"):
        assert col in cols, "CSV 缺少可追溯列 %s" % col

    by = {r["pattern_id"]: r for r in rows}
    # 被降级候选：CSV 必须能自解释
    for pid in ("TOPC-004", "TOPC-021"):
        r = by[pid]
        assert r["is_derived"] == "true", "%s 的 CSV is_derived 应为 true" % pid
        assert r["derived_from_pattern_id"], "%s 的 CSV 缺少来源候选" % pid
        assert r["derived_from_pattern_id"] in by, (
            "%s 的 CSV 来源 %r 不是已存在的候选" % (pid, r["derived_from_pattern_id"])
        )
        assert r["derivation_note"], "%s 的 CSV 缺少派生理由" % pid
        assert r["effective_promotion_status"] == "EXPLORATORY", "%s 应降级" % pid
    # 基线候选：不得带来源，但必须说明为何不下结论
    base = by["TOPC-001"]
    assert base["is_derived"] == "", "非派生候选的 CSV is_derived 应为空"
    assert base["derived_from_pattern_id"] == "", "非派生候选不得带来源"
    assert base["derivation_note"], "不下结论也必须给出 reason"
    print("PASS: CSV 可追溯列齐备且自解释（%d 行 × %d 列）" % (len(rows), len(cols)))


# ---------------------------------------------------------------- main

def main():
    print("=== Phase 7.3.2 派生结构门回归测试 ===\n")
    try:
        test_derived_true_not_promoted()
        test_derived_false_rule_still_applies()
        test_missing_fields_safe()
        test_source_trace_preserved()
        test_canonical_resolution_not_direct()
        test_artifact_consistency()
        test_csv_traceability_columns()
        print("\n=== 所有测试通过 ===")
        print("PASS: 0 FAIL, 0 WARNING")
    except AssertionError as e:
        print("\nFAIL: %s" % e)
        sys.exit(1)
    except Exception as e:
        print("\nERROR: %s" % e)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
