#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""validate_historical_research_intake.py —— Historical Universe Intake 包验证器（R00 · standalone）。

本文件是 ThreeC R00 验证器的 **standalone 版本**：
- 所有路径改为 **Workspace-relative**（不依赖 ThreeC 主仓库）
- **C01–C24 的校验语义与主仓库版本完全一致**（检查函数逐字节相同，由生成器保证）
- 不依赖 SQLite / Product / 网络

校验 Research Agent 提交的 `Research Intake Package` 是否满足
`01_PROTOCOL/HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md`。

用法（在 Workspace 根执行）:
    python tools/validate_historical_research_intake.py                # 默认校验 05_OUTPUT
    python tools/validate_historical_research_intake.py <package>      # 目录或 .json
    python tools/validate_historical_research_intake.py --check        # 基础设施自检
    python tools/validate_historical_research_intake.py --list-checks  # 列出检查项
    python tools/validate_historical_research_intake.py <pkg> --json   # 机器可读输出

退出码: 0 = 全部通过（无 FAIL）；1 = 存在 FAIL。

检查项（24 项；C01–C20 对应协议 §18 的 20 条，C21–C24 为一致性补强）:
  C01  schema version            —— intake_protocol_version 必须等于协议版本
  C02  required fields           —— 顶层 16 个必需字段齐备且类型正确
  C03  candidate_id uniqueness   —— campaign_candidates[].candidate_id 本包内唯一
  C04  evidence_id uniqueness    —— evidence[].evidence_id 唯一
  C05  source_id uniqueness      —— sources[].source_id 唯一
  C06  candidate -> evidence ref —— evidence_ids / date_candidates 引用必须存在
  C07  candidate -> security ref —— security_ids 引用必须存在
  C08  source tier / type        —— tier 合法、source_type 合法、二者不矛盾
  C09  evidence role             —— evidence_role 合法
  C10  research_status           —— 合法且**不得为 VERIFIED**
  C11  confidence                —— 合法（high|medium|low），不得为数值
  C12  date precision            —— 合法 + 条件字段齐备（EXACT/DATE_WINDOW/PHASE_WINDOW）
  C13  no canonical DB ID        —— 所有 intake id 必须带 round 前缀，禁止冒充 canonical id
  C14  no forbidden schema field —— 不得出现 canonical 持久化字段
  C15  no ranking/score/predict  —— 不得出现 score / rank / probability / prediction 类字段
  C16  provenance present        —— source_commit / generated_at / task_id / 逐条 source_id
  C17  exclusions present        —— exclusions 为数组且**不得为空**（协议 §8.2）
  C18  source URL present        —— url 为空时必须提供 no_url_reason
  C19  point-in-time notes       —— subsequent/retrospective 必须填 point_in_time_note 等
  C20  LF / determinism          —— 文件必须 LF；重复运行结果必须一致
  C21  counts consistency        —— quality_summary.counts 必须与实际数组长度一致
  C22  no quantity KPI           —— no_quantity_kpi_acknowledged 必须为 true
  C23  year in scope             —— candidate.year 必须落在 task_scope.years 内
  C24  task id consistency       —— task_id 与 task_scope.task_id 一致、round 前缀一致

本脚本**只读**：不修改任何数据。
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import sys

# ------------------------------------------------------------------ 路径

# Workspace-relative 路径（standalone：不依赖 ThreeC 主仓库）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(SCRIPT_DIR)
PROTOCOL_DIR = os.path.join(WORKSPACE_ROOT, "01_PROTOCOL")
TASK_DIR = os.path.join(WORKSPACE_ROOT, "00_TASK")
SCHEMA_PATH = os.path.join(PROTOCOL_DIR, "historical_research_intake.schema.json")
MANIFEST_PATH = os.path.join(TASK_DIR, "R01_TASK_MANIFEST_CONTEXT.json")
PACKAGES_DIR = os.path.join(WORKSPACE_ROOT, "05_OUTPUT")
WORKSPACE_MANIFEST_PATH = os.path.join(WORKSPACE_ROOT, "workspace_manifest.json")
WORKSPACE_CHECKSUMS_PATH = os.path.join(
    WORKSPACE_ROOT, "workspace_checksums.sha256"
)

PROTOCOL_VERSION = "0.1"

# ------------------------------------------------------------------ 正则

INTAKE_ID_RE = re.compile(r"^R\d{2}-[A-Z0-9]+-[A-Z]*\d{3,}$")
ROUND_ID_RE = re.compile(r"^R\d{2}$")
TASK_ID_RE = re.compile(r"^R\d{2}-\d{2}$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_DT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$")
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")

# 会被误当作 canonical DB id 的形态（C-2023-AD / RC-2023-HUAWEI / TH-AUTO / rule_x / summer_2023）
CANONICAL_ID_RE = re.compile(
    r"^(C|RC|CC)-\d{4}-|^TH-|^rule_|^[a-z]+_\d{4}$|^(E|S|EV)-\d{4}-\d+$"
)

# 协议 §12：canonical 持久化字段（出现即越过边界）
FORBIDDEN_KEYS = {
    "campaign_id",
    "annual_review_id",
    "rule_id",
    "season_id",
    "campaign_year",
    "start_date",
    "end_date",
    "peak_date",
    "strength",
    "result",
    "classification",
    "date_confidence",
    "drift_vs_jun01",
    "drift_vs_jul01",
    "drift_vs_aug01",
    "theme_id",
    "event_id",
    "phase_id",
    "series_id",
    "trade_date",
    "observation_id",
    "verification_method",
    "verified_date",
    "candidate_date",
    "target_campaign_id",
    "proposed_canonical_id",
    "canonical_id",
    "macro_theme_id",
    "macro_theme_ids",
}

# 协议 §12：评分 / 排序 / 预测类字段（精确名）
FORBIDDEN_SCORE_KEYS = {
    "score",
    "rank",
    "ranking",
    "similarity_score",
    "probability",
    "win_rate",
    "expected_return",
    "prediction",
    "forecast",
    "target_price",
    "recommendation",
    "signal_strength",
    "confidence_score",
    "weight",
    "priority_score",
}

# 协议 §12：评分 / 排序 / 预测类字段（后缀形态）
FORBIDDEN_SCORE_SUFFIX_RE = re.compile(
    r"(_score|_rank|_ranking|_probability|_prediction|_forecast|_win_rate)$"
)

# 允许的 intake-local 引用键（值必须带 round 前缀）
INTAKE_REF_KEYS = {"candidate_id", "evidence_id", "source_id", "security_id"}

# 非 intake id 的 `*_id` 键（round 号 / task 号有自己的格式，不是 R<NN>-<SCOPE>-<SEQ>）
NON_ID_KEYS = {"task_id", "target_task_id", "research_round_id"}


def is_id_key(key: str) -> bool:
    """该 key 的值是否为 intake id（含 `*_ids` 数组）。"""
    if key in NON_ID_KEYS:
        return False
    return key in INTAKE_REF_KEYS or key.endswith("_id") or key.endswith("_ids")

# source_type <-> tier 允许组合（沿用 schema.sql + historical_campaign_validation_v1.md §1.2）
SOURCE_TYPE_TIER = {
    "exchange": (1,),
    "regulator": (1,),
    "company_announcement": (1,),
    "industry_association": (1, 2),
    "research_report": (2,),
    "media_tier2": (2,),
    "media_tier3": (3,),
    "media_tier4": (4,),
    "website": (2, 3, 4),
    "forum_blog": (4,),
    "social_media": (4,),
    "other": (1, 2, 3, 4),
}

# 目录模式的拆分文件名
DIR_FILES = {
    "manifest": "manifest.json",
    "coverage": "coverage.md",
    "candidates": "candidates.json",
    "evidence": "evidence.json",
    "sources": "sources.json",
    "securities": "securities.json",
    "exclusions": "exclusions.json",
    "conflicts": "conflicts.json",
    "research_questions": "research_questions.json",
    "quality_summary": "quality_summary.json",
    "checksums": "checksums.sha256",
}

# ------------------------------------------------------------------ schema 驱动

SCHEMA_CACHE: dict | None = None


def load_schema() -> dict:
    """加载 intake schema（enum / required 的唯一来源，避免在代码里重复硬编码）。"""
    global SCHEMA_CACHE
    if SCHEMA_CACHE is None:
        with io.open(SCHEMA_PATH, encoding="utf-8") as fh:
            SCHEMA_CACHE = json.load(fh)
    return SCHEMA_CACHE


def _def(name: str) -> dict:
    return load_schema()["definitions"][name]


def enum_of(definition: str) -> list:
    return list(_def(definition).get("enum", []))


def top_required() -> list:
    return list(load_schema()["required"])


# ------------------------------------------------------------------ 结果收集


class Report:
    """稳定排序的问题收集器（保证重复运行输出一致）。"""

    def __init__(self, label: str):
        self.label = label
        self.issues: list[dict] = []

    def add(self, check: str, level: str, message: str) -> None:
        self.issues.append({"check": check, "level": level, "message": message})

    def fail(self, check: str, message: str) -> None:
        self.add(check, "FAIL", message)

    def warn(self, check: str, message: str) -> None:
        self.add(check, "WARN", message)

    def info(self, check: str, message: str) -> None:
        self.add(check, "INFO", message)

    def fails(self) -> list[dict]:
        return [i for i in self.issues if i["level"] == "FAIL"]

    def warns(self) -> list[dict]:
        return [i for i in self.issues if i["level"] == "WARN"]

    def sorted_issues(self) -> list[dict]:
        return sorted(self.issues, key=lambda i: (i["check"], i["level"], i["message"]))

    def ok(self) -> bool:
        return not self.fails()


# ------------------------------------------------------------------ 工具


def read_text(path: str) -> str:
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def read_bytes(path: str) -> bytes:
    with io.open(path, "rb") as fh:
        return fh.read()


def walk_keys(node, path="$"):
    """递归产出 (key, path) —— 用于禁止字段扫描。"""
    if isinstance(node, dict):
        for k, v in node.items():
            yield k, "%s.%s" % (path, k)
            yield from walk_keys(v, "%s.%s" % (path, k))
    elif isinstance(node, list):
        for idx, v in enumerate(node):
            yield from walk_keys(v, "%s[%d]" % (path, idx))


def walk_id_values(node, path="$", in_id_list=False):
    """递归产出 (key, value, path) —— 仅产出**应为 intake id** 的字符串。

    只认 `*_id` / `*_ids` 键（`task_id` / `target_task_id` 除外）。
    普通字符串数组（如 `theme_name_candidates`）不会被误判为 id。
    """
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, str) and is_id_key(k):
                yield k, v, "%s.%s" % (path, k)
            elif isinstance(v, list) and k.endswith("_ids"):
                yield from walk_id_values(v, "%s.%s" % (path, k), True)
            elif not isinstance(v, str):
                yield from walk_id_values(v, "%s.%s" % (path, k), False)
    elif isinstance(node, list):
        for idx, v in enumerate(node):
            if isinstance(v, str):
                if in_id_list:
                    yield None, v, "%s[%d]" % (path, idx)
            else:
                yield from walk_id_values(v, "%s[%d]" % (path, idx), False)


# ------------------------------------------------------------------ 装载


def load_package(path: str, rep: Report) -> dict | None:
    """把目录或单文件统一装配成一个 package dict。"""
    if os.path.isdir(path):
        return _load_dir_package(path, rep)
    if os.path.isfile(path):
        raw = read_bytes(path)
        if b"\r\n" in raw:
            rep.fail("C20", "文件包含 CRLF（必须 LF）: %s" % path)
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as exc:  # pragma: no cover - 依赖输入
            rep.fail("C01", "JSON 解析失败: %s" % exc)
            return None
        if not isinstance(data, dict):
            rep.fail("C01", "package 顶层必须是 object")
            return None
        return data
    rep.fail("C01", "路径不存在: %s" % path)
    return None


def _load_dir_package(path: str, rep: Report) -> dict | None:
    """按协议 §5.3 目录结构装配。

    `macro_theme_proposals` 与 `cross_task_notes` 从 `manifest.json` 读取
    （协议 §5.3 未为它们单独定义文件）。
    """
    pkg: dict = {}
    missing = []
    for key, fname in DIR_FILES.items():
        fp = os.path.join(path, fname)
        if not os.path.isfile(fp):
            missing.append(fname)
    if missing:
        rep.fail("C02", "package 目录缺少文件: %s" % ", ".join(sorted(missing)))
        return None

    # LF 检查（含 coverage.md / checksums.sha256）
    for fname in sorted(DIR_FILES.values()):
        fp = os.path.join(path, fname)
        if os.path.isfile(fp) and b"\r\n" in read_bytes(fp):
            rep.fail("C20", "文件包含 CRLF（必须 LF）: %s" % fname)

    manifest = json.loads(read_text(os.path.join(path, DIR_FILES["manifest"])))
    pkg["intake_protocol_version"] = manifest.get("intake_protocol_version")
    pkg["research_round_id"] = manifest.get("research_round_id")
    pkg["task_id"] = manifest.get("task_id")
    pkg["task_scope"] = manifest.get("task_scope")
    pkg["generated_at"] = manifest.get("generated_at")
    pkg["source_commit"] = manifest.get("source_commit")
    pkg["macro_theme_proposals"] = manifest.get("macro_theme_proposals", [])
    pkg["cross_task_notes"] = manifest.get("cross_task_notes", [])
    pkg["campaign_candidates"] = json.loads(
        read_text(os.path.join(path, DIR_FILES["candidates"]))
    )
    pkg["evidence"] = json.loads(read_text(os.path.join(path, DIR_FILES["evidence"])))
    pkg["sources"] = json.loads(read_text(os.path.join(path, DIR_FILES["sources"])))
    pkg["securities"] = json.loads(
        read_text(os.path.join(path, DIR_FILES["securities"]))
    )
    pkg["exclusions"] = json.loads(
        read_text(os.path.join(path, DIR_FILES["exclusions"]))
    )
    pkg["conflicts"] = json.loads(read_text(os.path.join(path, DIR_FILES["conflicts"])))
    pkg["research_questions"] = json.loads(
        read_text(os.path.join(path, DIR_FILES["research_questions"]))
    )
    pkg["quality_summary"] = json.loads(
        read_text(os.path.join(path, DIR_FILES["quality_summary"]))
    )

    # checksums.sha256（若填写则必须一致）
    _verify_checksums(path, rep)
    return pkg


def _verify_checksums(path: str, rep: Report) -> None:
    import hashlib

    fp = os.path.join(path, DIR_FILES["checksums"])
    lines = [ln.strip() for ln in read_text(fp).splitlines() if ln.strip()]
    if not lines:
        rep.fail("C20", "checksums.sha256 为空")
        return
    for ln in lines:
        parts = ln.split(None, 1)
        if len(parts) != 2:
            rep.fail("C20", "checksums.sha256 行格式错误: %s" % ln)
            continue
        digest, name = parts[0], parts[1].lstrip("*")
        target = os.path.join(path, name)
        if not os.path.isfile(target):
            rep.fail("C20", "checksums 引用的文件不存在: %s" % name)
            continue
        actual = hashlib.sha256(read_bytes(target)).hexdigest()
        if actual != digest:
            rep.fail("C20", "checksum 不一致: %s" % name)


# ------------------------------------------------------------------ 24 项检查


def validate_package(pkg: dict, rep: Report) -> None:
    if not isinstance(pkg, dict):
        rep.fail("C01", "package 必须是 object")
        return

    c01_schema_version(pkg, rep)
    c02_required_fields(pkg, rep)
    c03_c05_uniqueness(pkg, rep)
    c06_c07_references(pkg, rep)
    c08_sources(pkg, rep)
    c09_evidence_role(pkg, rep)
    c10_research_status(pkg, rep)
    c11_confidence(pkg, rep)
    c12_date_precision(pkg, rep)
    c13_no_canonical_id(pkg, rep)
    c14_no_forbidden_field(pkg, rep)
    c15_no_ranking(pkg, rep)
    c16_provenance(pkg, rep)
    c17_exclusions(pkg, rep)
    c18_source_url(pkg, rep)
    c19_point_in_time(pkg, rep)
    c21_counts(pkg, rep)
    c22_no_quantity_kpi(pkg, rep)
    c23_year_in_scope(pkg, rep)
    c24_task_id_consistency(pkg, rep)
    # C20 的「确定性」部分由 run_validation() 的两次比较完成


def c01_schema_version(pkg: dict, rep: Report) -> None:
    v = pkg.get("intake_protocol_version")
    if v != PROTOCOL_VERSION:
        rep.fail("C01", "intake_protocol_version 必须为 %r，实际 %r" % (PROTOCOL_VERSION, v))


def c02_required_fields(pkg: dict, rep: Report) -> None:
    for key in top_required():
        if key not in pkg:
            rep.fail("C02", "缺少必需顶层字段: %s" % key)
            continue
        val = pkg[key]
        if key in (
            "macro_theme_proposals",
            "campaign_candidates",
            "evidence",
            "sources",
            "securities",
            "exclusions",
            "conflicts",
            "cross_task_notes",
            "research_questions",
        ) and not isinstance(val, list):
            rep.fail("C02", "%s 必须是数组" % key)
        if key in ("task_scope", "quality_summary") and not isinstance(val, dict):
            rep.fail("C02", "%s 必须是 object" % key)
    rid = pkg.get("research_round_id")
    if isinstance(rid, str) and not ROUND_ID_RE.match(rid):
        rep.fail("C02", "research_round_id 格式非法: %r" % rid)
    tid = pkg.get("task_id")
    if isinstance(tid, str) and not TASK_ID_RE.match(tid):
        rep.fail("C02", "task_id 格式非法: %r" % tid)


def _uniq(rep: Report, check: str, label: str, values: list) -> None:
    seen = {}
    for v in values:
        seen[v] = seen.get(v, 0) + 1
    for v, n in sorted(seen.items()):
        if n > 1:
            rep.fail(check, "%s 重复 %d 次: %r" % (label, n, v))


def c03_c05_uniqueness(pkg: dict, rep: Report) -> None:
    _uniq(
        rep,
        "C03",
        "candidate_id",
        [c.get("candidate_id") for c in _list(pkg, "campaign_candidates")],
    )
    _uniq(
        rep,
        "C04",
        "evidence_id",
        [e.get("evidence_id") for e in _list(pkg, "evidence")],
    )
    _uniq(
        rep,
        "C05",
        "source_id",
        [s.get("source_id") for s in _list(pkg, "sources")],
    )


def _list(pkg: dict, key: str) -> list:
    v = pkg.get(key)
    return v if isinstance(v, list) else []


def _dicts(pkg: dict, key: str) -> list:
    return [x for x in _list(pkg, key) if isinstance(x, dict)]


def c06_c07_references(pkg: dict, rep: Report) -> None:
    ev_ids = {e.get("evidence_id") for e in _dicts(pkg, "evidence")}
    sec_ids = {s.get("security_id") for s in _dicts(pkg, "securities")}
    src_ids = {s.get("source_id") for s in _dicts(pkg, "sources")}

    def check_refs(check: str, label: str, ids: list, pool: set, kind: str) -> None:
        for i in sorted(x for x in ids if isinstance(x, str)):
            if i not in pool:
                rep.fail(check, "%s 引用了不存在的 %s: %r" % (label, kind, i))

    for c in _dicts(pkg, "campaign_candidates"):
        cid = c.get("candidate_id")
        check_refs("C06", "candidate %s" % cid, c.get("evidence_ids") or [], ev_ids, "evidence")
        check_refs("C07", "candidate %s" % cid, c.get("security_ids") or [], sec_ids, "security")
        dc = c.get("date_candidates") or {}
        if isinstance(dc, dict):
            for role in ("start", "peak", "end"):
                for entry in dc.get(role) or []:
                    if not isinstance(entry, dict):
                        continue
                    check_refs("C06", "candidate %s date_candidates.%s" % (cid, role), entry.get("evidence_ids") or [], ev_ids, "evidence")
                    check_refs("C06", "candidate %s date_candidates.%s" % (cid, role), entry.get("source_ids") or [], src_ids, "source")

    for s in _dicts(pkg, "securities"):
        check_refs("C06", "security %s" % s.get("security_id"), s.get("source_ids") or [], src_ids, "source")

    for x in _dicts(pkg, "exclusions"):
        check_refs("C06", "exclusion %s" % x.get("exclusion_id"), x.get("source_ids") or [], src_ids, "source")
        check_refs("C06", "exclusion %s" % x.get("exclusion_id"), x.get("evidence_ids") or [], ev_ids, "evidence")

    for cf in _dicts(pkg, "conflicts"):
        for pos in cf.get("positions") or []:
            if isinstance(pos, dict):
                check_refs("C06", "conflict %s" % cf.get("conflict_id"), pos.get("source_ids") or [], src_ids, "source")

    # evidence -> source
    for e in _dicts(pkg, "evidence"):
        sid = e.get("source_id")
        if isinstance(sid, str) and sid not in src_ids:
            rep.fail("C06", "evidence %s 引用了不存在的 source: %r" % (e.get("evidence_id"), sid))


def c08_sources(pkg: dict, rep: Report) -> None:
    valid_types = set(enum_of("source_type"))
    for s in _dicts(pkg, "sources"):
        sid = s.get("source_id")
        st = s.get("source_type")
        tier = s.get("tier")
        if st not in valid_types:
            rep.fail("C08", "source %s source_type 非法: %r" % (sid, st))
        if not isinstance(tier, int) or tier not in (1, 2, 3, 4):
            rep.fail("C08", "source %s tier 非法: %r" % (sid, tier))
        elif st in SOURCE_TYPE_TIER and tier not in SOURCE_TYPE_TIER[st]:
            rep.fail(
                "C08",
                "source %s tier 与 source_type 矛盾: %s 允许 %s，实际 %s"
                % (sid, st, SOURCE_TYPE_TIER[st], tier),
            )
        if not s.get("independence_group"):
            rep.fail("C08", "source %s 缺少 independence_group" % sid)
        if not s.get("publisher"):
            rep.fail("C16", "source %s 缺少 publisher（provenance）" % sid)


def c09_evidence_role(pkg: dict, rep: Report) -> None:
    valid = set(enum_of("evidence_role"))
    for e in _dicts(pkg, "evidence"):
        if e.get("evidence_role") not in valid:
            rep.fail("C09", "evidence %s evidence_role 非法: %r" % (e.get("evidence_id"), e.get("evidence_role")))
        if not e.get("independence_group"):
            rep.fail("C09", "evidence %s 缺少 independence_group（媒体数量 != 独立证据数量）" % e.get("evidence_id"))


def c10_research_status(pkg: dict, rep: Report) -> None:
    valid = set(enum_of("research_status"))
    for c in _dicts(pkg, "campaign_candidates"):
        st = c.get("research_status")
        if st == "VERIFIED" or st not in valid:
            rep.fail(
                "C10",
                "candidate %s research_status 非法: %r（Research Agent 不得声明 VERIFIED）"
                % (c.get("candidate_id"), st),
            )


def c11_confidence(pkg: dict, rep: Report) -> None:
    valid = set(enum_of("confidence"))

    def chk(label: str, val) -> None:
        if val not in valid:
            rep.fail("C11", "%s confidence 非法: %r（不得为数值）" % (label, val))

    for c in _dicts(pkg, "campaign_candidates"):
        chk("candidate %s" % c.get("candidate_id"), c.get("confidence"))
        dc = c.get("date_candidates") or {}
        if isinstance(dc, dict):
            for role in ("start", "peak", "end"):
                for entry in dc.get(role) or []:
                    if isinstance(entry, dict):
                        chk("candidate %s date_candidates.%s" % (c.get("candidate_id"), role), entry.get("confidence"))
    for e in _dicts(pkg, "evidence"):
        chk("evidence %s" % e.get("evidence_id"), e.get("confidence"))


def c12_date_precision(pkg: dict, rep: Report) -> None:
    valid = set(enum_of("date_precision"))
    for c in _dicts(pkg, "campaign_candidates"):
        dc = c.get("date_candidates")
        if not isinstance(dc, dict):
            rep.fail("C12", "candidate %s 缺少 date_candidates" % c.get("candidate_id"))
            continue
        for role in ("start", "peak", "end"):
            if role not in dc:
                rep.fail("C12", "candidate %s date_candidates 缺少 %s" % (c.get("candidate_id"), role))
                continue
            for idx, entry in enumerate(dc.get(role) or []):
                if not isinstance(entry, dict):
                    rep.fail("C12", "candidate %s date_candidates.%s[%d] 必须是 object" % (c.get("candidate_id"), role, idx))
                    continue
                label = "%s.%s[%d]" % (c.get("candidate_id"), role, idx)
                p = entry.get("date_precision")
                if p not in valid:
                    rep.fail("C12", "%s date_precision 非法: %r" % (label, p))
                    continue
                if p == "EXACT_DATE":
                    if not _is_date(entry.get("date")):
                        rep.fail("C12", "%s EXACT_DATE 必须有合法 date" % label)
                    if entry.get("window_start") is not None or entry.get("window_end") is not None:
                        rep.fail("C12", "%s EXACT_DATE 不得同时给 window_*" % label)
                elif p == "DATE_WINDOW":
                    if not _is_date(entry.get("window_start")) or not _is_date(entry.get("window_end")):
                        rep.fail("C12", "%s DATE_WINDOW 必须有 window_start + window_end" % label)
                    elif entry["window_start"] > entry["window_end"]:
                        rep.fail("C12", "%s DATE_WINDOW 起止倒置" % label)
                    if entry.get("date") is not None:
                        rep.fail("C12", "%s DATE_WINDOW 不得同时给 date" % label)
                elif p == "PHASE_WINDOW":
                    if not entry.get("phase_note"):
                        rep.fail("C12", "%s PHASE_WINDOW 必须有 phase_note" % label)
                if not entry.get("basis"):
                    rep.fail("C12", "%s 缺少 basis" % label)


def _is_date(v) -> bool:
    return isinstance(v, str) and bool(ISO_DATE_RE.match(v))


def c13_no_canonical_id(pkg: dict, rep: Report) -> None:
    for _key, val, path in walk_id_values(pkg):
        if CANONICAL_ID_RE.match(val):
            rep.fail("C13", "禁止 canonical DB id（必须 intake-local R<NN>-...）: %s = %r" % (path, val))
        elif not INTAKE_ID_RE.match(val):
            rep.fail("C13", "intake id 必须匹配 ^R\\d{2}-...: %s = %r" % (path, val))


def c14_no_forbidden_field(pkg: dict, rep: Report) -> None:
    for key, path in walk_keys(pkg):
        if key in FORBIDDEN_KEYS:
            rep.fail("C14", "禁止出现 canonical 持久化字段: %s" % path)


def c15_no_ranking(pkg: dict, rep: Report) -> None:
    for key, path in walk_keys(pkg):
        if key in FORBIDDEN_SCORE_KEYS or FORBIDDEN_SCORE_SUFFIX_RE.search(key):
            rep.fail("C15", "禁止评分/排序/预测类字段: %s" % path)


def c16_provenance(pkg: dict, rep: Report) -> None:
    sc = pkg.get("source_commit")
    if not (isinstance(sc, str) and SHA_RE.match(sc)):
        rep.fail("C16", "source_commit 缺失或格式非法: %r" % sc)
    ga = pkg.get("generated_at")
    if not (isinstance(ga, str) and ISO_DT_RE.match(ga)):
        rep.fail("C16", "generated_at 缺失或格式非法（需带时区）: %r" % ga)
    for e in _dicts(pkg, "evidence"):
        if not e.get("source_id"):
            rep.fail("C16", "evidence %s 缺少 source_id" % e.get("evidence_id"))


def c17_exclusions(pkg: dict, rep: Report) -> None:
    ex = pkg.get("exclusions")
    if not isinstance(ex, list):
        rep.fail("C17", "exclusions 必须是数组（强制字段）")
        return
    if not ex:
        rep.fail("C17", "exclusions 不得为空（协议 §8.2：防止只收集成功案例）")
    valid = {
        "OBSERVATION_ONLY",
        "SINGLE_STOCK_EVENT",
        "SAME_CAMPAIGN",
        "INSUFFICIENT_EVIDENCE",
        "NOT_INDEPENDENT_MACRO_THEME",
        "NOT_A_CAMPAIGN",
        "OUT_OF_SCOPE",
        "OTHER",
    }
    for x in ex:
        if not isinstance(x, dict):
            rep.fail("C17", "exclusion 必须是 object")
            continue
        if x.get("reason_code") not in valid:
            rep.fail("C17", "exclusion %s reason_code 非法: %r" % (x.get("exclusion_id"), x.get("reason_code")))
        if not x.get("rationale"):
            rep.fail("C17", "exclusion %s 缺少 rationale" % x.get("exclusion_id"))


def c18_source_url(pkg: dict, rep: Report) -> None:
    for s in _dicts(pkg, "sources"):
        url = s.get("url")
        if not url:
            if not s.get("no_url_reason"):
                rep.fail(
                    "C18",
                    "source %s 缺少 url 且未提供 no_url_reason" % s.get("source_id"),
                )
        elif not isinstance(url, str) or not url.strip():
            rep.fail("C18", "source %s url 非法: %r" % (s.get("source_id"), url))


def c19_point_in_time(pkg: dict, rep: Report) -> None:
    valid_tr = set(enum_of("temporal_relation"))
    valid_sk = set(enum_of("support_kind"))
    for e in _dicts(pkg, "evidence"):
        eid = e.get("evidence_id")
        tr = e.get("temporal_relation")
        sk = e.get("support_kind") or []
        if tr not in valid_tr:
            rep.fail("C19", "evidence %s temporal_relation 非法: %r" % (eid, tr))
            continue
        if not isinstance(sk, list) or not sk:
            rep.fail("C19", "evidence %s 缺少 support_kind" % eid)
            continue
        bad = [x for x in sk if x not in valid_sk]
        if bad:
            rep.fail("C19", "evidence %s support_kind 非法: %r" % (eid, bad))
            continue
        if tr in ("subsequent", "retrospective") and not e.get("point_in_time_note"):
            rep.fail(
                "C19",
                "evidence %s temporal_relation=%s 必须填写 point_in_time_note（说明不得作为同期催化）"
                % (eid, tr),
            )
        if tr == "retrospective" and "retrospective_context" not in sk:
            rep.fail("C19", "evidence %s retrospective 必须含 support_kind=retrospective_context" % eid)
        if "point_in_time_support" in sk and tr not in ("contemporaneous", "prior"):
            rep.fail(
                "C19",
                "evidence %s 含 point_in_time_support 但 temporal_relation=%s（必须 contemporaneous|prior）"
                % (eid, tr),
            )


def c21_counts(pkg: dict, rep: Report) -> None:
    qs = pkg.get("quality_summary")
    if not isinstance(qs, dict):
        rep.fail("C21", "quality_summary 必须是 object")
        return
    counts = qs.get("counts")
    if not isinstance(counts, dict):
        rep.fail("C21", "quality_summary.counts 必须是 object")
        return
    actual = {
        "campaign_candidates": len(_list(pkg, "campaign_candidates")),
        "evidence": len(_list(pkg, "evidence")),
        "sources": len(_list(pkg, "sources")),
        "securities": len(_list(pkg, "securities")),
        "exclusions": len(_list(pkg, "exclusions")),
        "conflicts": len(_list(pkg, "conflicts")),
    }
    for k, v in sorted(actual.items()):
        if counts.get(k) != v:
            rep.fail("C21", "quality_summary.counts.%s 与实际不符: 声明 %r，实际 %d" % (k, counts.get(k), v))

    dist = qs.get("confidence_distribution")
    if not isinstance(dist, dict):
        rep.fail("C21", "quality_summary.confidence_distribution 必须是 object")
        return
    tally = {"high": 0, "medium": 0, "low": 0}
    for c in _dicts(pkg, "campaign_candidates"):
        if c.get("confidence") in tally:
            tally[c["confidence"]] += 1
    for k in ("high", "medium", "low"):
        if dist.get(k) != tally[k]:
            rep.fail("C21", "confidence_distribution.%s 与实际不符: 声明 %r，实际 %d" % (k, dist.get(k), tally[k]))


def c22_no_quantity_kpi(pkg: dict, rep: Report) -> None:
    qs = pkg.get("quality_summary")
    if not isinstance(qs, dict) or qs.get("no_quantity_kpi_acknowledged") is not True:
        rep.fail("C22", "quality_summary.no_quantity_kpi_acknowledged 必须为 true（协议 §9）")
    # 全包扫描：任何 "expected_*count*" 形态字段都视为数量 KPI
    for key, path in walk_keys(pkg):
        if key.startswith("expected_") and "count" in key:
            rep.fail("C22", "禁止数量 KPI 字段: %s" % path)


def c23_year_in_scope(pkg: dict, rep: Report) -> None:
    scope = pkg.get("task_scope")
    if not isinstance(scope, dict):
        return
    yrs = scope.get("years")
    if not isinstance(yrs, dict):
        return
    lo, hi = yrs.get("from"), yrs.get("to")
    for c in _dicts(pkg, "campaign_candidates"):
        y = c.get("year")
        if isinstance(y, int) and isinstance(lo, int) and isinstance(hi, int):
            if y < lo or y > hi:
                rep.fail("C23", "candidate %s year=%d 超出 task_scope.years %d-%d" % (c.get("candidate_id"), y, lo, hi))
    # Priority A/B 定义必须存在且落在 years 内
    for k in ("priority_a_years", "priority_b_years"):
        r = scope.get(k)
        if not isinstance(r, dict) or not isinstance(r.get("from"), int) or not isinstance(r.get("to"), int):
            rep.fail("C23", "task_scope.%s 缺失或格式非法" % k)
        elif isinstance(lo, int) and isinstance(hi, int):
            if r["from"] < lo or r["to"] > hi:
                rep.fail("C23", "task_scope.%s 超出 years 范围" % k)


def c24_task_id_consistency(pkg: dict, rep: Report) -> None:
    tid = pkg.get("task_id")
    rid = pkg.get("research_round_id")
    scope = pkg.get("task_scope")
    if isinstance(scope, dict) and scope.get("task_id") != tid:
        rep.fail("C24", "task_scope.task_id (%r) 与 task_id (%r) 不一致" % (scope.get("task_id"), tid))
    if isinstance(tid, str) and isinstance(rid, str) and not tid.startswith(rid + "-"):
        rep.fail("C24", "task_id %r 未使用 research_round_id %r 前缀" % (tid, rid))
    # intake id 的 round 前缀必须与 research_round_id 一致
    if isinstance(rid, str):
        for key, val, path in walk_id_values(pkg):
            if isinstance(val, str) and INTAKE_ID_RE.match(val) and not val.startswith(rid + "-"):
                rep.fail("C24", "id 前缀与 research_round_id 不一致: %s = %r" % (path, val))


# ------------------------------------------------------------------ 运行


CHECKS = [
    ("C01", "schema version"),
    ("C02", "required fields"),
    ("C03", "candidate_id uniqueness"),
    ("C04", "evidence_id uniqueness"),
    ("C05", "source_id uniqueness"),
    ("C06", "candidate -> evidence refs"),
    ("C07", "candidate -> security refs"),
    ("C08", "source tier / type"),
    ("C09", "evidence role"),
    ("C10", "research_status"),
    ("C11", "confidence"),
    ("C12", "date precision"),
    ("C13", "no canonical DB id"),
    ("C14", "no forbidden schema field"),
    ("C15", "no ranking/score/prediction"),
    ("C16", "provenance present"),
    ("C17", "exclusions present"),
    ("C18", "source URL present"),
    ("C19", "point-in-time notes"),
    ("C20", "LF / determinism"),
    ("C21", "counts consistency"),
    ("C22", "no quantity KPI"),
    ("C23", "year in scope"),
    ("C24", "task id consistency"),
]


def validate_once(pkg: dict) -> list[dict]:
    rep = Report("package")
    validate_package(pkg, rep)
    return rep.sorted_issues()


def _is_pristine_output_dir(path: str) -> bool:
    """交付目录**尚未开始研究**：空目录，或仅含 README.md。

    这是**合法状态**（`task_status = PREPARED_NOT_STARTED`），**不是错误**。
    任何其它不完整状态（例如只有部分文件）仍按正常流程 FAIL。
    """
    if not os.path.isdir(path):
        return False
    entries = sorted(e for e in os.listdir(path) if e != ".gitkeep")
    return len(entries) == 0 or entries == ["README.md"]


def run_validation(path: str) -> tuple[Report, bool]:
    """返回 (report, deterministic)。"""
    rep = Report(path)
    if _is_pristine_output_dir(path):
        rep.info(
            "C02",
            "交付目录尚未开始研究（空目录或仅含 README.md）"
            "—— PREPARED_NOT_STARTED 属正常状态: %s" % path,
        )
        return rep, True
    pkg = load_package(path, rep)
    if pkg is None:
        rep.fail("C20", "无法装配 package")
        return rep, True

    first = validate_once(pkg)
    second = validate_once(pkg)
    deterministic = first == second
    if not deterministic:
        rep.fail("C20", "重复运行结果不一致（确定性失败）")
    for issue in first:
        rep.add(issue["check"], issue["level"], issue["message"])
    return rep, deterministic


def print_report(rep: Report, as_json: bool) -> None:
    issues = rep.sorted_issues()
    if as_json:
        sys.stdout.write(
            json.dumps(
                {
                    "package": rep.label,
                    "checks": len(CHECKS),
                    "issues": issues,
                    "fails": len([i for i in issues if i["level"] == "FAIL"]),
                    "warns": len([i for i in issues if i["level"] == "WARN"]),
                    "result": "PASS" if rep.ok() else "FAIL",
                },
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n"
        )
        return

    sys.stdout.write("ThreeC · Historical Research Intake Validator v0.1\n")
    sys.stdout.write("package: %s\n" % rep.label)
    sys.stdout.write("-" * 62 + "\n")
    for i in issues:
        sys.stdout.write("%-5s %-5s %s\n" % (i["level"], i["check"], i["message"]))
    nf = len([i for i in issues if i["level"] == "FAIL"])
    nw = len([i for i in issues if i["level"] == "WARN"])
    if not issues:
        sys.stdout.write("(no issues)\n")
    sys.stdout.write("-" * 62 + "\n")
    sys.stdout.write("checks: %d   FAIL: %d   WARN: %d\n" % (len(CHECKS), nf, nw))
    sys.stdout.write("RESULT: %s\n" % ("PASS" if rep.ok() else "FAIL"))


# ------------------------------------------------------------------ --check


def check_infrastructure(as_json: bool) -> int:
    """基础设施自检：schema / manifest / packages 目录 / 确定性。

    确定性做法：把整个自检实现为**纯函数** `_check_infrastructure_once()`，
    连跑两次并比较序列化结果 —— 而不是只重跑其中一部分。
    """
    first = _check_infrastructure_once()
    second = _check_infrastructure_once()
    rep = Report("--check (infrastructure)")
    for issue in first.sorted_issues():
        rep.add(issue["check"], issue["level"], issue["message"])
    if first.sorted_issues() != second.sorted_issues():
        rep.fail("C20", "--check 重复运行结果不一致（确定性失败）")
    print_report(rep, as_json)
    return 0 if rep.ok() else 1


def _check_infrastructure_once() -> Report:
    rep = Report("--check (infrastructure)")

    # 1) schema
    if not os.path.isfile(SCHEMA_PATH):
        rep.fail("C01", "缺少 schema: %s" % SCHEMA_PATH)
    else:
        raw = read_bytes(SCHEMA_PATH)
        if b"\r\n" in raw:
            rep.fail("C20", "schema 文件包含 CRLF（必须 LF）")
        try:
            sch = json.loads(raw.decode("utf-8"))
            for key in ("$schema", "definitions", "properties", "required"):
                if key not in sch:
                    rep.fail("C01", "schema 缺少 %s" % key)
            if sch.get("properties", {}).get("intake_protocol_version", {}).get("const") != PROTOCOL_VERSION:
                rep.fail("C01", "schema 的 intake_protocol_version const 与协议版本不一致")
            for d in ("confidence", "source_type", "evidence_role", "temporal_relation", "support_kind", "research_status", "date_precision", "classification_proposal"):
                if d not in sch.get("definitions", {}):
                    rep.fail("C01", "schema 缺少 definitions.%s" % d)
        except Exception as exc:
            rep.fail("C01", "schema JSON 解析失败: %s" % exc)

    # 2) manifest
    if not os.path.isfile(MANIFEST_PATH):
        rep.fail("C02", "缺少 R01 task manifest: %s" % MANIFEST_PATH)
    else:
        raw = read_bytes(MANIFEST_PATH)
        if b"\r\n" in raw:
            rep.fail("C20", "manifest 包含 CRLF（必须 LF）")
        try:
            man = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            rep.fail("C02", "manifest JSON 解析失败: %s" % exc)
            man = {}
        tasks = man.get("tasks") or []
        ids = [t.get("task_id") for t in tasks if isinstance(t, dict)]
        expected = ["R01-0%d" % i for i in range(1, 7)]
        if ids != expected:
            rep.fail("C02", "manifest tasks 应为 %s，实际 %s" % (expected, ids))
        if man.get("research_round_id") != "R01":
            rep.fail("C02", "manifest research_round_id 必须为 R01")
        gc = man.get("global_constraints") or {}
        if not isinstance(gc, dict) or gc.get("no_quantity_kpi") is not True:
            rep.fail("C22", "manifest.global_constraints.no_quantity_kpi 必须为 true")
        for key in ("forbidden_actions", "expected_output", "macro_theme_resolution", "campaign_decision"):
            if not gc.get(key):
                rep.fail("C02", "manifest.global_constraints 缺少 %s" % key)
        for t in tasks:
            if not isinstance(t, dict):
                continue
            for key in ("task_id", "scope", "macro_theme_candidates", "years", "priority", "known_overlap", "known_ambiguity", "excluded_scope", "expected_output", "forbidden_actions"):
                if key not in t:
                    rep.fail("C02", "task %s 缺少字段 %s" % (t.get("task_id"), key))
            for key in list(t.keys()):
                if key.startswith("expected_") and "count" in key:
                    rep.fail("C22", "manifest task %s 出现数量 KPI 字段: %s" % (t.get("task_id"), key))

    # 3) packages 目录
    pkg_dirs = []
    if os.path.isdir(PACKAGES_DIR):
        pkg_dirs = sorted(
            os.path.join(PACKAGES_DIR, d)
            for d in os.listdir(PACKAGES_DIR)
            if os.path.isdir(os.path.join(PACKAGES_DIR, d))
        )
    else:
        rep.info("C02", "05_OUTPUT 目录尚不存在（研究未开始属正常）: %s" % PACKAGES_DIR)

    for d in pkg_dirs:
        sub, _ = run_validation(d)
        for i in sub.sorted_issues():
            rep.add(i["check"], i["level"], "[%s] %s" % (os.path.basename(d), i["message"]))

    # 4) workspace_manifest.json（自描述 / 权限边界）
    if not os.path.isfile(WORKSPACE_MANIFEST_PATH):
        rep.fail("C02", "缺少 workspace_manifest.json: %s" % WORKSPACE_MANIFEST_PATH)
    else:
        raw = read_bytes(WORKSPACE_MANIFEST_PATH)
        if b"\r\n" in raw:
            rep.fail("C20", "workspace_manifest.json 包含 CRLF（必须 LF）")
        try:
            wm = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            rep.fail("C02", "workspace_manifest.json JSON 解析失败: %s" % exc)
            wm = {}
        for key in (
            "workspace_version",
            "workspace_kind",
            "research_round_id",
            "task_id",
            "task_status",
            "source_threec_commit",
            "intake_protocol_version",
            "standalone",
            "canonical_db_access",
            "product_access",
            "canonicalization_authority",
        ):
            if key not in wm:
                rep.fail("C02", "workspace_manifest.json 缺少字段 %s" % key)
        if wm.get("workspace_kind") != "threec_historical_research_worker":
            rep.fail("C02", "workspace_kind 非法: %r" % wm.get("workspace_kind"))
        if wm.get("task_status") != "PREPARED_NOT_STARTED":
            rep.fail(
                "C02",
                "task_status 必须为 PREPARED_NOT_STARTED，实际 %r（不得写成 STARTED）"
                % wm.get("task_status"),
            )
        if wm.get("standalone") is not True:
            rep.fail("C02", "workspace_manifest.standalone 必须为 true")
        for flag in ("canonical_db_access", "product_access", "canonicalization_authority"):
            if wm.get(flag) is not False:
                rep.fail("C02", "workspace_manifest.%s 必须为 false（Worker 无该权限）" % flag)
        if wm.get("intake_protocol_version") != PROTOCOL_VERSION:
            rep.fail("C02", "workspace_manifest.intake_protocol_version 与协议版本不一致")
        sc = wm.get("source_threec_commit")
        if not (isinstance(sc, str) and SHA_RE.match(sc)):
            rep.fail("C16", "workspace_manifest.source_threec_commit 缺失或格式非法: %r" % sc)
        # task_id 必须出现在 context manifest 的 task 列表中
        if isinstance(wm.get("task_id"), str):
            ids = [t.get("task_id") for t in tasks if isinstance(t, dict)]
            if ids and wm["task_id"] not in ids:
                rep.fail("C24", "workspace task_id %r 不在 task manifest context 中" % wm["task_id"])

    # 5) workspace_checksums.sha256（规则版本一致性）
    if not os.path.isfile(WORKSPACE_CHECKSUMS_PATH):
        rep.fail("C20", "缺少 workspace_checksums.sha256: %s" % WORKSPACE_CHECKSUMS_PATH)
    else:
        raw = read_bytes(WORKSPACE_CHECKSUMS_PATH)
        if b"\r\n" in raw:
            rep.fail("C20", "workspace_checksums.sha256 包含 CRLF（必须 LF）")
        lines = [ln.strip() for ln in raw.decode("utf-8").splitlines() if ln.strip()]
        if not lines:
            rep.fail("C20", "workspace_checksums.sha256 为空")
        for ln in lines:
            parts = ln.split(None, 1)
            if len(parts) != 2:
                rep.fail("C20", "workspace_checksums.sha256 行格式错误: %s" % ln)
                continue
            digest, name = parts[0], parts[1].lstrip("*")
            target = os.path.join(WORKSPACE_ROOT, name)
            if not os.path.isfile(target):
                rep.fail("C20", "workspace_checksums 引用的文件不存在: %s" % name)
                continue
            actual = hashlib.sha256(read_bytes(target)).hexdigest()
            if actual != digest:
                rep.fail("C20", "workspace checksum 不一致（规则版本可能被改动）: %s" % name)

    rep.info("C20", "packages found: %d" % len(pkg_dirs))
    return rep


# ------------------------------------------------------------------ main


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}
    as_json = "--json" in flags

    if "--list-checks" in flags:
        for cid, name in CHECKS:
            sys.stdout.write("%s  %s\n" % (cid, name))
        return 0

    if "--check" in flags:
        return check_infrastructure(as_json)

    if not args:
        # 无参数 → 默认校验唯一正式交付位置
        args = ["05_OUTPUT"]

    path = args[0]
    if not os.path.isabs(path):
        path = os.path.join(WORKSPACE_ROOT, path)
    rep, _ = run_validation(path)
    print_report(rep, as_json)
    return 0 if rep.ok() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
