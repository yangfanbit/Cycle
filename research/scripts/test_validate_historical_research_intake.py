#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""validate_historical_research_intake 测试（Intake Validator Tests）。

验证 `validate_historical_research_intake.py` 的正确性：
  1. 合法 package 全项通过（C01–C25，0 FAIL）
  2. 每个检查项都有对应的**失败路径**（人为构造违规必须 FAIL）
  3. 目录模式装配 + checksums 校验
  4. 单文件模式 + CRLF 拒绝
  5. 确定性（重复运行结果一致）
  6. 基础设施自检（--check）
  7. 真实 schema / manifest 自洽
  8. **C25 严格 JSON Schema（Draft-07）校验**：额外属性 / enum / type / pattern /
     temporal_relation 五类人为注入缺陷必须全部检出，且必须导致整体 FAIL

关键原则：
- 测试必须调用 validator 的真实函数（`validate_package` / `run_validation` / `_check_infrastructure_once`），
  而不是重复实现校验逻辑。
- 使用 `copy.deepcopy()` 确保测试隔离。
- 不修改仓库内任何文件：目录模式测试写入系统临时目录。

用法: python research/scripts/test_validate_historical_research_intake.py
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
sys.path.insert(0, SCRIPT_DIR)

import validate_historical_research_intake as V  # noqa: E402


# ------------------------------------------------------------------ fixture


def valid_package() -> dict:
    """一个**结构完整、全部检查项通过**的最小 package（合成数据，不代表任何真实研究）。"""
    return {
        "intake_protocol_version": "0.1",
        "research_round_id": "R01",
        "task_id": "R01-02",
        "task_scope": {
            "task_id": "R01-02",
            "family_directions": ["半导体 / 电子"],
            "years": {"from": 2015, "to": 2025},
            "priority_a_years": {"from": 2018, "to": 2025},
            "priority_b_years": {"from": 2015, "to": 2017},
            "included_scope": "测试用 scope",
            "excluded_scope": "测试用 excluded scope",
        },
        "generated_at": "2026-09-19T00:00:00Z",
        "source_commit": "2ba94bd83f5724c0bab146a744c54fa562a7c45e",
        "macro_theme_proposals": [
            {
                "proposal_id": "R01-SEMICONDUCTOR-MT001",
                "proposed_name": "半导体",
                "theme_name_candidates": ["半导体", "集成电路"],
                "proposal_kind": "NEW_MACRO_CANDIDATE",
                "rationale": "测试用 rationale",
                "known_overlap": ["信息通信"],
                "notes": None,
            }
        ],
        "campaign_candidates": [
            {
                "candidate_id": "R01-SEMICONDUCTOR-001",
                "title": "测试候选（合成）",
                "year": 2020,
                "macro_theme_proposal": "半导体",
                "theme_name_candidates": ["半导体"],
                "theme_summary": "测试用 theme summary",
                "date_candidates": {
                    "start": [
                        {
                            "date_precision": "DATE_WINDOW",
                            "date": None,
                            "window_start": "2020-05-01",
                            "window_end": "2020-05-31",
                            "phase_note": None,
                            "basis": "inferred",
                            "source_ids": ["R01-SEMICONDUCTOR-S001"],
                            "evidence_ids": ["R01-SEMICONDUCTOR-E001"],
                            "confidence": "medium",
                            "alternative_dates": [
                                {
                                    "date": "2020-04-27",
                                    "basis": "备选口径",
                                    "source_ids": ["R01-SEMICONDUCTOR-S002"],
                                }
                            ],
                            "conflict_note": "两口径并存，不自动取舍",
                        }
                    ],
                    "peak": [
                        {
                            "date_precision": "PHASE_WINDOW",
                            "date": None,
                            "window_start": None,
                            "window_end": None,
                            "phase_note": "主升后段",
                            "basis": "inferred",
                            "source_ids": [],
                            "evidence_ids": [],
                            "confidence": "low",
                            "alternative_dates": [],
                            "conflict_note": None,
                        }
                    ],
                    "end": [
                        {
                            "date_precision": "UNKNOWN",
                            "date": None,
                            "window_start": None,
                            "window_end": None,
                            "phase_note": None,
                            "basis": "unknown",
                            "source_ids": [],
                            "evidence_ids": [],
                            "confidence": "low",
                            "alternative_dates": [],
                            "conflict_note": None,
                        }
                    ],
                },
                "lifecycle": [
                    {
                        "stage_proposal": "MAIN_RISE",
                        "start": "2020-05-01",
                        "end": "2020-07-15",
                        "basis": "测试用 basis",
                        "notes": None,
                    }
                ],
                "classification_proposal": "theme_campaign",
                "drivers": {
                    "start": ["测试用启动归因"],
                    "accelerator": ["测试用加速归因"],
                    "turning": ["测试用转折归因"],
                    "ending": ["测试用结束归因"],
                },
                "evidence_ids": [
                    "R01-SEMICONDUCTOR-E001",
                    "R01-SEMICONDUCTOR-E002",
                ],
                "security_ids": ["R01-SEMICONDUCTOR-SEC001"],
                "research_status": "PROVISIONAL",
                "confidence": "medium",
                "point_in_time_notes": "测试用 PIT 说明",
                "why_campaign": "测试用 why_campaign",
                "why_not": "测试用 why_not",
                "possible_duplicate_of": [],
                "notes": "",
            }
        ],
        "evidence": [
            {
                "evidence_id": "R01-SEMICONDUCTOR-E001",
                "claim": "测试用 claim（合成）",
                "evidence_role": "supporting",
                "evidence_type": "official_document",
                "event_date": "2020-05-15",
                "evidence_date": "2020-05-16",
                "source_id": "R01-SEMICONDUCTOR-S001",
                "confidence": "medium",
                "independence_group": "IG-A",
                "same_origin": False,
                "retelling": False,
                "primary_source": True,
                "temporal_relation": "contemporaneous",
                "support_kind": [
                    "historical_fact_support",
                    "point_in_time_support",
                ],
                "point_in_time_note": None,
                "description": "测试用 description",
            },
            {
                "evidence_id": "R01-SEMICONDUCTOR-E002",
                "claim": "测试用 retrospective claim（合成）",
                "evidence_role": "contradicting",
                "evidence_type": "media",
                "event_date": "2020-07-15",
                "evidence_date": "2024-01-10",
                "source_id": "R01-SEMICONDUCTOR-S002",
                "confidence": "low",
                "independence_group": "IG-B",
                "same_origin": False,
                "retelling": False,
                "primary_source": False,
                "temporal_relation": "retrospective",
                "support_kind": [
                    "historical_fact_support",
                    "retrospective_context",
                ],
                "point_in_time_note": "事后复盘资料，不得作为同期催化。",
                "description": "测试用 description",
            },
        ],
        "sources": [
            {
                "source_id": "R01-SEMICONDUCTOR-S001",
                "title": "测试用官方来源（合成）",
                "url": "https://example.invalid/official/1",
                "no_url_reason": None,
                "publisher": "测试用 publisher",
                "author": None,
                "published_at": "2020-05-16",
                "captured_at": None,
                "source_type": "regulator",
                "tier": 1,
                "independence_group": "IG-A",
                "description": None,
            },
            {
                "source_id": "R01-SEMICONDUCTOR-S002",
                "title": "测试用媒体来源（合成）",
                "url": "https://example.invalid/media/2",
                "no_url_reason": None,
                "publisher": "测试用 media publisher",
                "author": None,
                "published_at": "2024-01-10",
                "captured_at": None,
                "source_type": "media_tier3",
                "tier": 3,
                "independence_group": "IG-B",
                "description": None,
            },
        ],
        "securities": [
            {
                "security_id": "R01-SEMICONDUCTOR-SEC001",
                "ticker": "000001",
                "name": "测试用证券（合成）",
                "exchange": "SZ",
                "role": "leader",
                "basis": "测试用 basis",
                "source_ids": ["R01-SEMICONDUCTOR-S001"],
                "point_in_time_note": "Historical Leader Set（retrospective）",
                "survivorship_aware": True,
            }
        ],
        "exclusions": [
            {
                "exclusion_id": "R01-SEMICONDUCTOR-X001",
                "subject": "测试用被排除事件（合成）",
                "reason_code": "OUT_OF_SCOPE",
                "rationale": "测试用 rationale",
                "source_ids": [],
                "evidence_ids": [],
            }
        ],
        "conflicts": [],
        "cross_task_notes": [],
        "research_questions": [
            {
                "question_id": "R01-SEMICONDUCTOR-Q001",
                "question": "测试用研究问题？",
                "why_it_matters": "测试用 why",
                "related_candidate_ids": ["R01-SEMICONDUCTOR-001"],
            }
        ],
        "quality_summary": {
            "counts": {
                "campaign_candidates": 1,
                "evidence": 2,
                "sources": 2,
                "securities": 1,
                "exclusions": 1,
                "conflicts": 0,
            },
            "confidence_distribution": {"high": 0, "medium": 1, "low": 0},
            "coverage_notes": "测试用 coverage notes",
            "known_gaps": ["测试用 gap"],
            "no_quantity_kpi_acknowledged": True,
        },
    }


# ------------------------------------------------------------------ 工具


def issues_of(pkg: dict) -> list:
    rep = V.Report("test")
    V.validate_package(pkg, rep)
    return rep.sorted_issues()


def fails_of(pkg: dict) -> list:
    return [i for i in issues_of(pkg) if i["level"] == "FAIL"]


def expect_fail(check: str, pkg: dict, label: str) -> None:
    got = [i for i in fails_of(pkg) if i["check"] == check]
    assert got, "%s: 期望 %s FAIL，但未触发。全部 issues=%s" % (
        label,
        check,
        [i["check"] for i in issues_of(pkg)],
    )


def expect_pass(pkg: dict, label: str) -> None:
    f = fails_of(pkg)
    assert not f, "%s: 期望 0 FAIL，实际 %s" % (
        label,
        [(i["check"], i["message"]) for i in f],
    )


# ------------------------------------------------------------------ 测试

RESULTS: list = []


def case(fn):
    RESULTS.append(fn)
    return fn


@case
def test_valid_package_passes():
    """合法 package 全 24 项 0 FAIL。"""
    expect_pass(valid_package(), "valid package")


@case
def test_check_count_is_25():
    """检查项数量固定为 25，且 C01–C25 齐备（C25 = 严格 JSON Schema）。"""
    ids = [c[0] for c in V.CHECKS]
    assert len(ids) == 25, "检查项数量应为 25，实际 %d" % len(ids)
    assert ids == ["C%02d" % i for i in range(1, 26)], ids


@case
def test_c01_schema_version():
    p = valid_package()
    p["intake_protocol_version"] = "9.9"
    expect_fail("C01", p, "protocol version")


@case
def test_c02_required_fields():
    p = valid_package()
    del p["task_scope"]
    expect_fail("C02", p, "missing task_scope")
    p2 = valid_package()
    p2["campaign_candidates"] = "not-a-list"
    expect_fail("C02", p2, "campaign_candidates not list")


@case
def test_c03_c04_c05_uniqueness():
    p = valid_package()
    p["campaign_candidates"].append(copy.deepcopy(p["campaign_candidates"][0]))
    expect_fail("C03", p, "duplicate candidate_id")

    p2 = valid_package()
    p2["evidence"].append(copy.deepcopy(p2["evidence"][0]))
    expect_fail("C04", p2, "duplicate evidence_id")

    p3 = valid_package()
    p3["sources"].append(copy.deepcopy(p3["sources"][0]))
    expect_fail("C05", p3, "duplicate source_id")


@case
def test_c06_dangling_evidence_ref():
    p = valid_package()
    p["campaign_candidates"][0]["evidence_ids"].append("R01-SEMICONDUCTOR-E999")
    expect_fail("C06", p, "dangling evidence ref")


@case
def test_c06_dangling_source_ref_in_evidence():
    p = valid_package()
    p["evidence"][0]["source_id"] = "R01-SEMICONDUCTOR-S999"
    expect_fail("C06", p, "dangling source ref")


@case
def test_c07_dangling_security_ref():
    p = valid_package()
    p["campaign_candidates"][0]["security_ids"].append("R01-SEMICONDUCTOR-SEC999")
    expect_fail("C07", p, "dangling security ref")


@case
def test_c08_tier_type_contradiction():
    p = valid_package()
    p["sources"][0]["source_type"] = "forum_blog"  # 只允许 tier 4
    expect_fail("C08", p, "forum_blog with tier 1")

    p2 = valid_package()
    p2["sources"][0]["tier"] = 9
    expect_fail("C08", p2, "tier out of range")

    p3 = valid_package()
    p3["sources"][0]["source_type"] = "not_a_type"
    expect_fail("C08", p3, "invalid source_type")


@case
def test_c09_evidence_role():
    p = valid_package()
    p["evidence"][0]["evidence_role"] = "maybe"
    expect_fail("C09", p, "invalid evidence_role")

    p2 = valid_package()
    p2["evidence"][0]["independence_group"] = ""
    expect_fail("C09", p2, "missing independence_group")


@case
def test_c10_research_status():
    p = valid_package()
    p["campaign_candidates"][0]["research_status"] = "VERIFIED"
    expect_fail("C10", p, "VERIFIED must be rejected")

    p2 = valid_package()
    p2["campaign_candidates"][0]["research_status"] = "DONE"
    expect_fail("C10", p2, "invalid research_status")


@case
def test_c11_confidence():
    p = valid_package()
    p["campaign_candidates"][0]["confidence"] = 0.87
    expect_fail("C11", p, "numeric confidence")

    p2 = valid_package()
    p2["evidence"][0]["confidence"] = "very-high"
    expect_fail("C11", p2, "invalid evidence confidence")


@case
def test_c12_date_precision():
    p = valid_package()
    d = p["campaign_candidates"][0]["date_candidates"]["start"][0]
    d["date_precision"] = "EXACT_DATE"  # 但 date=None
    expect_fail("C12", p, "EXACT_DATE without date")

    p2 = valid_package()
    d2 = p2["campaign_candidates"][0]["date_candidates"]["start"][0]
    d2["window_end"] = None  # DATE_WINDOW 缺 window_end
    expect_fail("C12", p2, "DATE_WINDOW without window_end")

    p3 = valid_package()
    d3 = p3["campaign_candidates"][0]["date_candidates"]["peak"][0]
    d3["phase_note"] = None  # PHASE_WINDOW 缺 phase_note
    expect_fail("C12", p3, "PHASE_WINDOW without phase_note")

    p4 = valid_package()
    p4["campaign_candidates"][0]["date_candidates"]["start"][0]["date_precision"] = "SOMEDAY"
    expect_fail("C12", p4, "invalid date_precision")


@case
def test_c13_no_canonical_id():
    p = valid_package()
    p["campaign_candidates"][0]["candidate_id"] = "C-2020-SEMI"
    expect_fail("C13", p, "canonical campaign id")

    p2 = valid_package()
    p2["campaign_candidates"][0]["candidate_id"] = "RC-2020-SEMI"
    expect_fail("C13", p2, "canonical research candidate id")

    p3 = valid_package()
    p3["evidence"][0]["source_id"] = "S-2020-01"
    expect_fail("C13", p3, "canonical source id")

    p4 = valid_package()
    p4["macro_theme_proposals"][0]["proposal_id"] = "TH-SEMI"
    expect_fail("C13", p4, "canonical theme id")

    p5 = valid_package()
    p5["exclusions"][0]["exclusion_id"] = "X-001"  # 无 round 前缀
    expect_fail("C13", p5, "id without round prefix")


@case
def test_c13_theme_names_are_not_ids():
    """`theme_name_candidates` 是普通字符串数组，不得被误判为 id。"""
    p = valid_package()
    p["campaign_candidates"][0]["theme_name_candidates"] = ["半导体", "集成电路"]
    expect_pass(p, "theme names are not ids")


@case
def test_c14_no_forbidden_schema_field():
    for field in ("campaign_id", "start_date", "peak_date", "theme_id", "result", "verified_date"):
        p = valid_package()
        p["campaign_candidates"][0][field] = "x"
        expect_fail("C14", p, "forbidden field %s" % field)

    p2 = valid_package()
    p2["macro_theme_proposals"][0]["macro_theme_id"] = "TH-X"
    expect_fail("C14", p2, "macro_theme_id")


@case
def test_c15_no_ranking_score_prediction():
    for field in ("score", "rank", "probability", "prediction", "win_rate", "confidence_score"):
        p = valid_package()
        p["campaign_candidates"][0][field] = 1
        expect_fail("C15", p, "forbidden score field %s" % field)

    p2 = valid_package()
    p2["campaign_candidates"][0]["similarity_score"] = 0.9
    expect_fail("C15", p2, "similarity_score")

    p3 = valid_package()
    p3["campaign_candidates"][0]["custom_rank"] = 3
    expect_fail("C15", p3, "custom_rank suffix")


@case
def test_c16_provenance():
    p = valid_package()
    del p["source_commit"]
    expect_fail("C16", p, "missing source_commit")

    p2 = valid_package()
    p2["generated_at"] = "2026-09-19 00:00:00"  # 无时区
    expect_fail("C16", p2, "generated_at without timezone")

    p3 = valid_package()
    p3["sources"][0]["publisher"] = ""
    expect_fail("C16", p3, "missing publisher")


@case
def test_c17_exclusions_mandatory():
    p = valid_package()
    p["exclusions"] = []
    expect_fail("C17", p, "empty exclusions")

    p2 = valid_package()
    del p2["exclusions"]
    expect_fail("C02", p2, "missing exclusions")

    p3 = valid_package()
    p3["exclusions"][0]["reason_code"] = "BECAUSE"
    expect_fail("C17", p3, "invalid reason_code")


@case
def test_c18_source_url():
    p = valid_package()
    p["sources"][0]["url"] = None
    expect_fail("C18", p, "no url and no reason")

    p2 = valid_package()
    p2["sources"][0]["url"] = None
    p2["sources"][0]["no_url_reason"] = "纸质文件，无公开链接"
    expect_pass(p2, "no url but reason given")


@case
def test_c19_point_in_time():
    p = valid_package()
    p["evidence"][1]["point_in_time_note"] = None  # retrospective
    expect_fail("C19", p, "retrospective without note")

    p2 = valid_package()
    p2["evidence"][1]["support_kind"] = ["historical_fact_support"]  # 缺 retrospective_context
    expect_fail("C19", p2, "retrospective without retrospective_context")

    p3 = valid_package()
    p3["evidence"][0]["support_kind"] = [
        "historical_fact_support",
        "point_in_time_support",
    ]
    p3["evidence"][0]["temporal_relation"] = "subsequent"  # PIT support 却非当时
    p3["evidence"][0]["point_in_time_note"] = "x"
    expect_fail("C19", p3, "PIT support with subsequent relation")

    p4 = valid_package()
    p4["evidence"][0]["temporal_relation"] = "whenever"
    expect_fail("C19", p4, "invalid temporal_relation")


@case
def test_c21_counts_consistency():
    p = valid_package()
    p["quality_summary"]["counts"]["evidence"] = 99
    expect_fail("C21", p, "counts mismatch")

    p2 = valid_package()
    p2["quality_summary"]["confidence_distribution"]["medium"] = 7
    expect_fail("C21", p2, "confidence distribution mismatch")


@case
def test_c22_no_quantity_kpi():
    p = valid_package()
    p["quality_summary"]["no_quantity_kpi_acknowledged"] = False
    expect_fail("C22", p, "KPI not acknowledged")

    p2 = valid_package()
    p2["campaign_candidates"][0]["expected_campaign_count"] = 5
    expect_fail("C22", p2, "expected_campaign_count field")


@case
def test_c23_year_in_scope():
    p = valid_package()
    p["campaign_candidates"][0]["year"] = 2030
    expect_fail("C23", p, "year out of scope")

    p2 = valid_package()
    p2["task_scope"]["priority_a_years"] = {"from": 2010, "to": 2025}
    expect_fail("C23", p2, "priority_a out of years")


@case
def test_c24_task_id_consistency():
    p = valid_package()
    p["task_scope"]["task_id"] = "R01-03"
    expect_fail("C24", p, "task_scope.task_id mismatch")

    p2 = valid_package()
    p2["task_id"] = "R02-02"
    expect_fail("C24", p2, "round prefix mismatch")

    p3 = valid_package()
    p3["campaign_candidates"][0]["candidate_id"] = "R02-SEMICONDUCTOR-001"
    expect_fail("C24", p3, "id prefix mismatch with round")


@case
def test_determinism_same_input_same_output():
    """同一输入重复校验 → 结果逐字节一致。"""
    p = valid_package()
    a = json.dumps(issues_of(p), ensure_ascii=False, sort_keys=True)
    b = json.dumps(issues_of(p), ensure_ascii=False, sort_keys=True)
    assert a == b, "重复运行结果不一致"

    bad = valid_package()
    bad["exclusions"] = []
    bad["campaign_candidates"][0]["confidence"] = 1
    c = json.dumps(issues_of(bad), ensure_ascii=False, sort_keys=True)
    d = json.dumps(issues_of(bad), ensure_ascii=False, sort_keys=True)
    assert c == d, "失败路径重复运行结果不一致"


@case
def test_single_file_mode_and_crlf():
    """单文件模式：LF 通过，CRLF 拒绝。"""
    tmp = tempfile.mkdtemp(prefix="threec_intake_")
    try:
        pkg = valid_package()
        ok_path = os.path.join(tmp, "package.json")
        with io.open(ok_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(pkg, fh, ensure_ascii=False)
        rep, det = V.run_validation(ok_path)
        assert rep.ok(), [i for i in rep.sorted_issues()]
        assert det, "确定性应为 True"

        crlf_path = os.path.join(tmp, "crlf.json")
        # indent 使 json 输出真实换行，newline="\r\n" 再把它翻成 CRLF
        with io.open(crlf_path, "w", encoding="utf-8", newline="\r\n") as fh:
            json.dump(pkg, fh, ensure_ascii=False, indent=2)
        assert b"\r\n" in V.read_bytes(crlf_path), "fixture 未生成 CRLF，测试无效"
        rep2, _ = V.run_validation(crlf_path)
        assert not rep2.ok(), "CRLF 应被拒绝"
        assert any(i["check"] == "C20" for i in rep2.fails()), "应为 C20 FAIL"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@case
def test_directory_mode_with_checksums():
    """目录模式：按协议 §5.3 装配 + checksums 校验。"""
    tmp = tempfile.mkdtemp(prefix="threec_intake_")
    try:
        pkg = valid_package()
        d = os.path.join(tmp, "R01-02")
        os.makedirs(d)
        manifest = {
            "intake_protocol_version": pkg["intake_protocol_version"],
            "research_round_id": pkg["research_round_id"],
            "task_id": pkg["task_id"],
            "task_scope": pkg["task_scope"],
            "generated_at": pkg["generated_at"],
            "source_commit": pkg["source_commit"],
            "macro_theme_proposals": pkg["macro_theme_proposals"],
            "cross_task_notes": pkg["cross_task_notes"],
        }
        files = {
            "manifest.json": manifest,
            "candidates.json": pkg["campaign_candidates"],
            "evidence.json": pkg["evidence"],
            "sources.json": pkg["sources"],
            "securities.json": pkg["securities"],
            "exclusions.json": pkg["exclusions"],
            "conflicts.json": pkg["conflicts"],
            "research_questions.json": pkg["research_questions"],
            "quality_summary.json": pkg["quality_summary"],
        }
        for name, data in files.items():
            with io.open(os.path.join(d, name), "w", encoding="utf-8", newline="\n") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
        with io.open(os.path.join(d, "coverage.md"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# coverage\n\n测试用。\n")

        lines = []
        for name in sorted(list(files.keys()) + ["coverage.md"]):
            h = hashlib.sha256(V.read_bytes(os.path.join(d, name))).hexdigest()
            lines.append("%s  %s" % (h, name))
        with io.open(os.path.join(d, "checksums.sha256"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")

        rep, det = V.run_validation(d)
        assert rep.ok(), [(i["check"], i["message"]) for i in rep.fails()]
        assert det, "确定性应为 True"

        # 篡改内容 → checksum 必须失败
        with io.open(os.path.join(d, "exclusions.json"), "a", encoding="utf-8", newline="\n") as fh:
            fh.write("\n")
        rep2, _ = V.run_validation(d)
        assert not rep2.ok(), "篡改后应 FAIL"
        assert any("checksum" in i["message"] for i in rep2.fails()), "应为 checksum FAIL"

        # 缺文件 → C02 FAIL
        os.remove(os.path.join(d, "coverage.md"))
        rep3, _ = V.run_validation(d)
        assert any(i["check"] == "C02" for i in rep3.fails()), "缺文件应为 C02 FAIL"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@case
def test_infrastructure_check_detects_known_r01_01_violation():
    """`--check` 必须检出**已记录的** R01-01 Schema 违规，且 R01-02 必须干净。

    背景：R01-01 的 `R01-HIEQ-CF005` 含额外键 `_position_note`，违反
    `additionalProperties: false`。该违规在 C25 之前**被放过并已入库** ——
    本测试是这条历史缺陷的回归守卫。
    """
    rep = V._check_infrastructure_once()
    fails = [(i["check"], i["message"]) for i in rep.fails()]
    c25 = [m for c, m in fails if c == "C25"]
    # R01-01：必须检出
    r01_01 = [m for m in c25 if "R01-01" in m]
    assert r01_01, "C25 未检出 R01-01 的已知 Schema 违规: %s" % fails
    assert any("_position_note" in m for m in r01_01), r01_01
    # R01-02：必须干净
    assert not [m for m in c25 if "R01-02" in m], c25
    # 除上述已知违规外不得有其它 FAIL
    others = [(c, m) for c, m in fails if c != "C25"]
    assert not others, "存在非预期的 FAIL: %s" % others


@case
def test_schema_is_lf_and_self_consistent():
    """schema 文件必须 LF，且关键 definitions 齐备。"""
    raw = V.read_bytes(V.SCHEMA_PATH)
    assert b"\r\n" not in raw, "schema 含 CRLF"
    sch = json.loads(raw.decode("utf-8"))
    for d in (
        "confidence",
        "source_type",
        "evidence_role",
        "temporal_relation",
        "support_kind",
        "research_status",
        "date_precision",
        "classification_proposal",
    ):
        assert d in sch["definitions"], "schema 缺 definitions.%s" % d
    assert sch["properties"]["intake_protocol_version"]["const"] == V.PROTOCOL_VERSION
    assert sch["properties"]["exclusions"].get("minItems") == 1, "exclusions 必须 minItems=1"
    assert (
        sch["definitions"]["quality_summary"]["properties"]["no_quantity_kpi_acknowledged"]["const"]
        is True
    )


@case
def test_manifest_is_lf_and_complete():
    """R01 task manifest 必须 LF、6 个任务、无数量 KPI、含禁止动作。"""
    raw = V.read_bytes(V.MANIFEST_PATH)
    assert b"\r\n" not in raw, "manifest 含 CRLF"
    man = json.loads(raw.decode("utf-8"))
    ids = [t["task_id"] for t in man["tasks"]]
    assert ids == ["R01-0%d" % i for i in range(1, 7)], ids
    assert man["global_constraints"]["no_quantity_kpi"] is True
    assert man["global_constraints"]["forbidden_actions"], "必须列出 forbidden_actions"
    # 数量 KPI 检查按**键名**判断（文档正文提到该词不算违规）
    kpi_keys = [
        path
        for key, path in V.walk_keys(man)
        if key.startswith("expected_") and "count" in key
    ]
    assert not kpi_keys, "manifest 不得含数量 KPI 字段: %s" % kpi_keys
    for t in man["tasks"]:
        for key in (
            "task_id",
            "scope",
            "macro_theme_candidates",
            "years",
            "priority",
            "known_overlap",
            "known_ambiguity",
            "excluded_scope",
            "expected_output",
            "forbidden_actions",
        ):
            assert key in t, "task %s 缺 %s" % (t["task_id"], key)
        assert t["years"] == {"from": 2015, "to": 2025}, t["task_id"]


@case
def test_enums_come_from_schema():
    """枚举必须由 schema 驱动（单一事实来源），不在代码里重复硬编码。"""
    assert set(V.enum_of("confidence")) == {"high", "medium", "low"}
    assert set(V.enum_of("research_status")) == {"PROVISIONAL", "CONFLICT", "INSUFFICIENT"}
    assert "VERIFIED" not in V.enum_of("research_status")
    assert set(V.enum_of("evidence_role")) == {"supporting", "contradicting", "context"}
    assert "contemporaneous" in V.enum_of("temporal_relation")
    assert set(V.enum_of("date_precision")) == {
        "EXACT_DATE",
        "DATE_WINDOW",
        "PHASE_WINDOW",
        "UNKNOWN",
    }
    assert V.top_required()[0] == "intake_protocol_version"
    assert len(V.top_required()) == 16, "顶层必需字段应为 16"


@case
def test_cli_exit_codes():
    """CLI：合法 package 退出 0；非法 package 退出 1（预期输出已抑制）。"""
    import contextlib

    tmp = tempfile.mkdtemp(prefix="threec_intake_")
    try:
        ok = os.path.join(tmp, "ok.json")
        with io.open(ok, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(valid_package(), fh, ensure_ascii=False)
        bad = valid_package()
        bad["exclusions"] = []
        bad_path = os.path.join(tmp, "bad.json")
        with io.open(bad_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(bad, fh, ensure_ascii=False)

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_ok = V.main(["prog", ok])
            rc_bad = V.main(["prog", bad_path])
            rc_check = V.main(["prog", "--check"])
            rc_list = V.main(["prog", "--list-checks"])

        assert rc_ok == 0, "合法 package 应退出 0"
        assert rc_bad == 1, "非法 package 应退出 1"
        # ★ 前提变更：C25 上线后 `--check` 扫描 packages/ 下所有正式 Package。
        #   R01-01 存在**已记录的** Schema 违规（`R01-HIEQ-CF005._position_note`），
        #   故 `--check` 退出码 = 1 —— 这是**正确**信号，不是回归。
        #   修复该违规属独立 remediation 任务，不在本轮范围。
        assert rc_check == 1, "--check 应退出 1（R01-01 已知 Schema 违规）"
        assert rc_list == 0, "--list-checks 应退出 0"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ================================================================== C25 严格 JSON Schema


def _c25_fails(pkg):
    """返回 C25 的 FAIL 列表（调用真实 validate_package）。"""
    rep = V.Report("c25")
    V.validate_package(copy.deepcopy(pkg), rep)
    return [i for i in rep.fails() if i["check"] == "C25"]


def _mutate_and_assert_c25(name, mutate, expect_substr=None):
    pkg = copy.deepcopy(valid_package())
    mutate(pkg)
    fails = _c25_fails(pkg)
    assert fails, "C25 未检出「%s」—— Schema 约束未真正执行" % name
    if expect_substr:
        joined = " | ".join(i["message"] for i in fails)
        assert expect_substr in joined, "C25 检出但内容不符（%s）: %s" % (name, joined)


@case
def test_c25_valid_package_passes():
    """合法 package 必须通过 C25（0 违规）。"""
    assert _c25_fails(valid_package()) == []


@case
def test_c25_detects_extra_property():
    """additionalProperties: false 必须真正执行。"""
    _mutate_and_assert_c25(
        "额外属性",
        lambda p: p["campaign_candidates"][0].update({"_extra_note": "injected"}),
        expect_substr="Additional properties are not allowed",
    )
    def _add_conflict_then_extra(p):
        p["conflicts"].append({
            "conflict_id": "R01-FIXTURE-CF001",
            "subject": "合成夹具冲突",
            "positions": [
                {"position": "A", "source_ids": ["R01-FIXTURE-S001"]},
                {"position": "B", "source_ids": ["R01-FIXTURE-S002"]},
            ],
            "resolution": "KEEP_BOTH",
            "note": None,
        })
        p["conflicts"][0]["_position_note"] = "injected"

    _mutate_and_assert_c25(
        "conflict 额外属性（R01-01 的历史违规形态）",
        _add_conflict_then_extra,
        expect_substr="_position_note",
    )


@case
def test_c25_detects_wrong_enum_confidence():
    """enum（confidence）必须真正执行。"""
    _mutate_and_assert_c25(
        "confidence 非法枚举",
        lambda p: p["campaign_candidates"][0].update({"confidence": "very-high"}),
        expect_substr="is not one of",
    )


@case
def test_c25_detects_wrong_type():
    """type 必须真正执行（C01–C24 曾漏检 year 为字符串）。"""
    _mutate_and_assert_c25(
        "year 类型错误",
        lambda p: p["campaign_candidates"][0].update({"year": "2020"}),
        expect_substr="is not of type",
    )
    _mutate_and_assert_c25(
        "candidates 类型错误",
        lambda p: p.update({"campaign_candidates": {}}),
        expect_substr="is not of type",
    )


@case
def test_c25_detects_wrong_pattern():
    """pattern（intake id）必须真正执行。"""
    _mutate_and_assert_c25(
        "candidate_id 违反 pattern（canonical id 形态）",
        lambda p: p["campaign_candidates"][0].update({"candidate_id": "C-2020-SEMI"}),
        expect_substr="does not match",
    )


@case
def test_c25_detects_wrong_enum_temporal_relation():
    """enum（temporal_relation）必须真正执行。"""
    _mutate_and_assert_c25(
        "temporal_relation 非法枚举",
        lambda p: p["evidence"][0].update({"temporal_relation": "whenever"}),
        expect_substr="is not one of",
    )


@case
def test_c25_detects_missing_required():
    """required 必须真正执行。"""
    _mutate_and_assert_c25(
        "缺少 why_not",
        lambda p: p["campaign_candidates"][0].pop("why_not"),
        expect_substr="is a required property",
    )
    _mutate_and_assert_c25(
        "缺少顶层 quality_summary",
        lambda p: p.pop("quality_summary"),
        expect_substr="is a required property",
    )


@case
def test_c25_strict_failure_makes_package_fail():
    """严格 Schema 校验失败 → 整个 Package 必须 FAIL（不得放行）。"""
    pkg = copy.deepcopy(valid_package())
    pkg["campaign_candidates"][0]["_extra_note"] = "injected"
    rep = V.Report("x")
    V.validate_package(pkg, rep)
    assert not rep.ok(), "严格 Schema 违规却未导致 FAIL"
    assert [i for i in rep.fails() if i["check"] == "C25"]


@case
def test_c25_strict_failure_exit_code_1():
    """CLI：严格 Schema 违规必须退出码 1。"""
    import contextlib

    tmp = tempfile.mkdtemp(prefix="threec_c25_")
    try:
        pkg = copy.deepcopy(valid_package())
        pkg["campaign_candidates"][0]["_extra_note"] = "injected"
        path = os.path.join(tmp, "package.json")
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(pkg, fh, ensure_ascii=False)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = V.main(["prog", path])
        assert rc == 1, "期望退出码 1，实际 %d" % rc
        out = buf.getvalue()
        assert "C25" in out and "Additional properties are not allowed" in out, out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@case
def test_c25_rescan_r01_02_clean():
    """回扫：R01-02 正式 Package 必须 0 违规。"""
    pkg_dir = os.path.join(REPO, "research", "intake", "packages", "R01-02")
    if not os.path.isdir(pkg_dir):
        return  # 包不存在时跳过（不改变测试结果语义）
    rep, _det = V.run_validation(pkg_dir)
    c25 = [i for i in rep.fails() if i["check"] == "C25"]
    assert c25 == [], "R01-02 存在 Schema 违规: %s" % c25
    assert rep.ok(), [(i["check"], i["message"]) for i in rep.fails()]


@case
def test_c25_rescan_r01_01_known_violation():
    """回扫：R01-01 正式 Package 的**已知** `_position_note` 违规必须被检出。

    该违规在 C25 之前被放过并已导入 canonical DB —— 本测试锁定这一事实，
    防止将来被静默“修掉”而失去可追溯性。
    """
    pkg_dir = os.path.join(REPO, "research", "intake", "packages", "R01-01")
    if not os.path.isdir(pkg_dir):
        return
    rep, _det = V.run_validation(pkg_dir)
    c25 = [i for i in rep.fails() if i["check"] == "C25"]
    assert c25, "R01-01 的已知 Schema 违规未被检出"
    joined = " | ".join(i["message"] for i in c25)
    assert "_position_note" in joined, c25
    # 且不得引入其它 Schema 违规
    assert len(c25) == 1, "R01-01 出现额外的 Schema 违规: %s" % c25


# ------------------------------------------------------------------ main


def main() -> None:
    print("Intake Validator Tests —— validate_historical_research_intake.py")
    print("=" * 62)
    failed = 0
    for fn in RESULTS:
        name = fn.__name__
        try:
            fn()
            print("PASS  %s" % name)
        except AssertionError as exc:
            failed += 1
            print("FAIL  %s\n      %s" % (name, exc))
        except Exception as exc:  # pragma: no cover
            failed += 1
            print("ERROR %s\n      %r" % (name, exc))
            import traceback

            traceback.print_exc()
    print("=" * 62)
    print("tests: %d   failed: %d" % (len(RESULTS), failed))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
