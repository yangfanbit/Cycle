#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""audit_historical_coverage.py —— Historical Coverage Audit v0.1（历史研究数据覆盖度审计）。

## 这个脚本是什么

对 ThreeC **全部**历史研究数据做一次**确定性、可复现**的覆盖度审计，回答：

    当前 ThreeC 的历史研究数据覆盖到了什么程度？还缺什么？
    哪些缺口最影响未来的 Time Observation 与 Structural Historical Analogy？

    exports/timeline_export_v1.json  +  research/database/cycle_research.db   （只读输入）
                      ↓  本脚本（只读，无网络，无随机数）
    research/research/reports/historical_coverage_matrix_v0_1.json
    research/research/reports/historical_coverage_matrix_v0_1.csv

**这不是产品集成**：不进入 `src/`、不进入 Timeline、不进入 DB / schema.sql / export / contracts。

## 本脚本**不做**什么

- 不判断主题好坏，**不做投资价值排名** —— 只做**数据建设优先级**。
- **不自行补齐缺失阶段** —— 只标记 COMPLETE / PARTIAL / SPARSE / UNKNOWN。
- 不把「数据库里没有某类事件」推断成「该机制不存在」——
  一律区分 **absence of evidence（无证据）** 与 **evidence of absence（证据表明不存在）**。

## 审计维度

1. Dataset Inventory（数量 + **分布**，不只给总量）
2. Macro Theme Coverage Matrix（主题族 × 周期 × Campaign × 年份 × lifecycle × evidence × event）
3. Taxonomy Integrity（孤立 theme / export-only theme / 声明但无历史）
4. Lifecycle Completeness（逐对象评级，不补齐）
5. Evidence Coverage（类型归一化 + 来源层级 + 逐族）
6. Event Coverage（缺失类别显式标 NOT_AVAILABLE）
7. Market Data Coverage（连续性 vs 窗口采样）
8. Verification Coverage（核验状态）
9. Domain Coverage（§六 领域清单：已有 / 声明无历史 / 缺失）
10. Research Capability Matrix（能力 × 限制 —— **加什么数据能解锁什么能力**）
11. Coverage Ceiling（theme_family_count 上限）
12. Priority Framework + Wave 1/2/3

## 确定性

无随机数、无时间戳漂移（`generated_at` 固定为 SNAPSHOT_DATE）、全序排序。

用法:
    python research/scripts/audit_historical_coverage.py                     # 生成（默认 round 0.1）
    python research/scripts/audit_historical_coverage.py --round 0.2         # 生成该轮（产物另存 v0_2）
    python research/scripts/audit_historical_coverage.py --check             # 校验逐字节一致
    python research/scripts/audit_historical_coverage.py --round 0.2 --check # 校验该轮
    python research/scripts/audit_historical_coverage.py --print             # 生成并打印摘要

**多轮说明**：产物是「某个数据快照」的确定性函数。数据集一变（如 Wave 1A 新增电力设备），
旧轮次产物即成为历史快照，其 `--check` 必然 FAIL —— 这是**预期行为**，不是回归。
新增轮次必须在 `ROUND_PROFILES` 中登记；未知轮次显式失败，不静默降级。

退出码: 0 = 通过；1 = 自检失败（**不写文件**）。
"""

from __future__ import annotations

import collections
import csv
import io
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT_PATH = os.path.join(ROOT, "exports", "timeline_export_v1.json")
DB_PATH = os.path.join(ROOT, "research", "database", "cycle_research.db")
CURRENT_CANDIDATES = os.path.join(ROOT, "research", "current", "current_candidates.json")
REPORTS_DIR = os.path.join(ROOT, "research", "research", "reports")

# canonical Macro Theme 解析（单一事实来源；与 discover_time_observation_patterns.py 共用）
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
import theme_taxonomy  # noqa: E402
OUT_JSON = os.path.join(REPORTS_DIR, "historical_coverage_matrix_v0_1.json")
OUT_CSV = os.path.join(REPORTS_DIR, "historical_coverage_matrix_v0_1.csv")

SNAPSHOT_DATE = "2026-09-16"
RULESET_VERSION = "historical-coverage-audit-0.1"
ARTIFACT_VERSION = "0.1"

# ---------------------------------------------------------------- 轮次档案
# 每一轮的**产物路径 / 快照日期 / 版本号**必须固化在此 ——
# 否则该轮产物不可复现、不可与其它轮比对。
# `--round X` 一并恢复该轮口径；**未知轮次必须显式失败**，不得静默降级为默认口径。
#
# 为什么需要多轮：本审计的产物是**某个数据快照**的确定性函数。
# 数据集一变（例如 Wave 1A 新增电力设备），旧轮次产物即成为历史快照，
# `--check` 对旧轮次必然 FAIL —— 这是**预期行为**，不是回归。
ROUND_PROFILES = {
    "0.1": {
        "json": "historical_coverage_matrix_v0_1.json",
        "csv": "historical_coverage_matrix_v0_1.csv",
        "snapshot_date": "2026-09-16",
        "ruleset_version": "historical-coverage-audit-0.1",
        "artifact_version": "0.1",
        "research_round": "historical-coverage-audit-v0.1",
        "label": "Wave 1A 之前的基线（2 个 Macro Theme / 9 Campaign）",
    },
    "0.2": {
        "json": "historical_coverage_matrix_v0_2.json",
        "csv": "historical_coverage_matrix_v0_2.csv",
        "snapshot_date": "2026-09-17",
        "ruleset_version": "historical-coverage-audit-0.2",
        "artifact_version": "0.2",
        "research_round": "historical-coverage-audit-v0.2",
        "label": "Wave 1A 之后（3 个 Macro Theme / 11 Campaign，新增 TH-POWER）",
    },
}
DEFAULT_ROUND = "0.1"
RESEARCH_ROUND = "historical-coverage-audit-v0.1"


def apply_round(round_id):
    """按轮次档案恢复输出路径与口径（就地更新模块级常量）。

    未知轮次 -> SystemExit（与 discover_time_observation_patterns.py 的 ROUND_PROFILES 约定一致）。
    """
    global OUT_JSON, OUT_CSV, SNAPSHOT_DATE, RULESET_VERSION, ARTIFACT_VERSION, RESEARCH_ROUND
    prof = ROUND_PROFILES.get(round_id)
    if prof is None:
        raise SystemExit(
            "未知轮次 %r —— 必须在 ROUND_PROFILES 中登记后才可使用（不得静默降级为默认口径）。"
            "可用轮次: %s" % (round_id, ", ".join(sorted(ROUND_PROFILES)))
        )
    OUT_JSON = os.path.join(REPORTS_DIR, prof["json"])
    OUT_CSV = os.path.join(REPORTS_DIR, prof["csv"])
    SNAPSHOT_DATE = prof["snapshot_date"]
    RULESET_VERSION = prof["ruleset_version"]
    ARTIFACT_VERSION = prof["artifact_version"]
    RESEARCH_ROUND = prof["research_round"]
    return prof

# ---------------------------------------------------------------- 枚举

# 导出 lifecycle 阶段（ThreeC 真实定义）
LC_STAGES = [
    "EARLY_SIGNAL",
    "THEME_FORMING",
    "BROAD_CONFIRMATION",
    "MAIN_RISE",
    "PEAK",
    "RETRACEMENT",
    "SECONDARY",
    "DECLINING",
    "FIRST_DECLINE",
    "MAIN_END",
]

# 任务书 §八 要求的 7 个评估阶段（与仓库真实阶段对齐，不发明新阶段）
AUDIT_STAGES = [
    "EARLY_SIGNAL",
    "THEME_FORMING",
    "BROAD_CONFIRMATION",
    "EXPANSION",       # ← 仓库中不存在，映射到 MAIN_RISE
    "PEAK",
    "WEAKENING",       # ← 仓库中不存在，映射到 DECLINING / RETRACEMENT / SECONDARY
    "DECLINE",         # ← 仓库中不存在，映射到 MAIN_END
]
# 任务书阶段 → 仓库真实阶段的**显式映射**（不发明新阶段，只做语义对齐）
STAGE_ALIAS = {
    "EXPANSION": ["MAIN_RISE"],
    "WEAKENING": ["DECLINING", "RETRACEMENT", "SECONDARY"],
    "DECLINE": ["MAIN_END", "FIRST_DECLINE"],
}

# 数据库 schema 允许的 event_type（用于判定"缺失类别"）
SCHEMA_EVENT_TYPES = ["policy", "industry", "macro", "company", "market", "news", "holiday", "other"]

# 事件覆盖审计关注的能力相关类别（§十）
EVENT_CAPABILITY_TYPES = [
    ("policy", "政策事件"),
    ("industry", "产业事件"),
    ("data_release", "数据发布"),
    ("reporting", "财报披露日"),
    ("meeting", "重大会议"),
    ("trade_fair", "展会"),
    ("product", "产品发布"),
    ("holiday", "节假日 / 日历"),
    ("company", "公司事件"),
    ("market", "市场事件"),
    ("macro", "宏观事件"),
]

# evidence_type 归一化映射（DB 内中英文混用，无 CHECK 约束）
EVIDENCE_TYPE_MAP = {
    "行情数据": "market",
    "market_data": "market",
    "行业数据": "industry",
    "行业月度产销数据": "industry",
    "政策文件": "policy",
    "official_document": "policy",
    "media": "information",
}

# 任务书 §九 要求的规范证据类别
CANONICAL_EVIDENCE_TYPES = ["policy", "industry", "company", "market", "capital", "information"]

# 任务书 §六 要求检查的领域清单 → 仓库中的对应物
DOMAIN_PROBES = [
    ("汽车", ["TH-AUTO"], ["汽车"]),
    ("医药", ["TH-PHARMA"], ["医药健康"]),
    ("新能源（车用电池）", ["TH-NEV"], ["新能源汽车/电池"]),
    ("电力设备", [], ["电力设备"]),
    ("信息通信", [], ["信息通信"]),
    ("高端装备", [], ["高端装备"]),
    ("半导体", [], ["半导体"]),
    ("电子", [], ["电子"]),
    ("通信", [], ["通信"]),
    ("计算机", [], ["计算机"]),
    ("AI / 算力", [], ["AI", "算力"]),
    ("机器人", [], ["机器人"]),
    ("军工", [], ["军工", "国防"]),
    ("消费", [], ["消费"]),
    ("有色 / 资源", [], ["有色", "资源"]),
    ("化工", [], ["化工"]),
    ("金融", [], ["金融", "银行", "券商"]),
    ("地产", [], ["地产", "房地产"]),
    ("TMT", [], ["TMT"]),
]

# ---------------------------------------------------------------- 优先级框架（§五）
#
# ⚠️ 重要：本框架是**数据建设优先级**，不是投资价值排名。
# 每个维度的 basis 显式标注 DATA_DERIVED（可从数据算出）或 JUDGMENT（研究判断）。
PRIORITY_DIMENSIONS = [
    ("a_share_historical_significance", "A股历史重要性", "JUDGMENT"),
    ("cycle_recurrence_potential", "历史周期重复潜力", "JUDGMENT"),
    ("cross_year_coverage_ability", "跨年份覆盖能力", "DATA_DERIVED"),
    ("independent_theme_cycle_ability", "可形成独立 Theme Cycle 的能力", "JUDGMENT"),
    ("structural_difference_vs_auto_pharma", "与现有 AUTO / PHARMA 的结构差异", "JUDGMENT"),
    ("increment_for_structural_analogy", "对 Structural Analogy 的增量价值", "JUDGMENT"),
    ("increment_for_time_observation", "对 Time Observation 的增量价值", "JUDGMENT"),
    ("current_data_gap_size", "当前 ThreeC 数据缺口大小", "DATA_DERIVED"),
]

# 候选补录主题的评分（1–3；JUDGMENT 项为研究判断，须在报告中明示）
PRIORITY_CANDIDATES = [
    {
        "domain": "电力设备",
        "already_declared_by": ["CC-2026-COMPUTE-POWER", "CC-2026-OFFSHORE-WIND"],
        "scores": {
            "a_share_historical_significance": 3,
            "cycle_recurrence_potential": 3,
            "cross_year_coverage_ability": 3,
            "independent_theme_cycle_ability": 3,
            "structural_difference_vs_auto_pharma": 3,
            "increment_for_structural_analogy": 3,
            "increment_for_time_observation": 3,
            "current_data_gap_size": 3,
        },
        "why": (
            "历史侧零覆盖，但 Current Candidate 侧已声明 2 个候选（算力电力 / 海风）→ "
            "Similarity 的 Pattern 层当前恒为 0（PROJECT_STATE 已记录）。补录可同时解锁"
            "历史能力与当前侧匹配能力，是**边际收益最高**的一项。"
        ),
    },
    {
        "domain": "信息通信",
        "already_declared_by": ["CC-2026-OPTICAL-LINK"],
        "scores": {
            "a_share_historical_significance": 3,
            "cycle_recurrence_potential": 3,
            "cross_year_coverage_ability": 3,
            "independent_theme_cycle_ability": 3,
            "structural_difference_vs_auto_pharma": 2,
            "increment_for_structural_analogy": 3,
            "increment_for_time_observation": 3,
            "current_data_gap_size": 3,
        },
        "why": "已有当前侧候选但无历史；光模块 / 光通信有多轮历史周期，补录可验证「跨族时间规律」。",
    },
    {
        "domain": "高端装备 / 机器人",
        "already_declared_by": ["CC-2026-EMBODIED-AI"],
        "scores": {
            "a_share_historical_significance": 2,
            "cycle_recurrence_potential": 2,
            "cross_year_coverage_ability": 2,
            "independent_theme_cycle_ability": 3,
            "structural_difference_vs_auto_pharma": 3,
            "increment_for_structural_analogy": 3,
            "increment_for_time_observation": 2,
            "current_data_gap_size": 3,
        },
        "why": "历史周期较短（2023 起），跨年样本可能不足；但结构差异大，对类比价值高。",
    },
    {
        "domain": "半导体 / 电子",
        "already_declared_by": [],
        "scores": {
            "a_share_historical_significance": 3,
            "cycle_recurrence_potential": 3,
            "cross_year_coverage_ability": 3,
            "independent_theme_cycle_ability": 3,
            "structural_difference_vs_auto_pharma": 3,
            "increment_for_structural_analogy": 3,
            "increment_for_time_observation": 3,
            "current_data_gap_size": 3,
        },
        "why": "2019–2025 有多轮清晰周期（国产替代 / 周期下行 / AI 驱动）；无当前侧候选，属纯历史补录。",
    },
    {
        "domain": "消费",
        "already_declared_by": [],
        "scores": {
            "a_share_historical_significance": 3,
            "cycle_recurrence_potential": 2,
            "cross_year_coverage_ability": 3,
            "independent_theme_cycle_ability": 2,
            "structural_difference_vs_auto_pharma": 2,
            "increment_for_structural_analogy": 2,
            "increment_for_time_observation": 3,
            "current_data_gap_size": 3,
        },
        "why": "消费有强日历属性（春节 / 双十一 / 中报），对 Calendar-driven 与 Holiday-relative 能力增量大。",
    },
    {
        "domain": "军工",
        "already_declared_by": [],
        "scores": {
            "a_share_historical_significance": 2,
            "cycle_recurrence_potential": 3,
            "cross_year_coverage_ability": 2,
            "independent_theme_cycle_ability": 2,
            "structural_difference_vs_auto_pharma": 3,
            "increment_for_structural_analogy": 2,
            "increment_for_time_observation": 2,
            "current_data_gap_size": 3,
        },
        "why": "订单 / 五年规划节奏强，Calendar-driven 潜力高；但公开数据披露弱，证据建设成本高。",
    },
    {
        "domain": "有色 / 资源 / 化工",
        "already_declared_by": [],
        "scores": {
            "a_share_historical_significance": 2,
            "cycle_recurrence_potential": 3,
            "cross_year_coverage_ability": 3,
            "independent_theme_cycle_ability": 2,
            "structural_difference_vs_auto_pharma": 3,
            "increment_for_structural_analogy": 2,
            "increment_for_time_observation": 2,
            "current_data_gap_size": 3,
        },
        "why": "价格周期驱动，机制与汽车 / 医药完全不同（供给端 + 商品价格），结构差异最大。",
    },
    {
        "domain": "金融 / 地产",
        "already_declared_by": [],
        "scores": {
            "a_share_historical_significance": 3,
            "cycle_recurrence_potential": 2,
            "cross_year_coverage_ability": 3,
            "independent_theme_cycle_ability": 2,
            "structural_difference_vs_auto_pharma": 3,
            "increment_for_structural_analogy": 2,
            "increment_for_time_observation": 3,
            "current_data_gap_size": 3,
        },
        "why": "政策周期极强（货币政策 / 地产调控），是 Calendar-driven 的天然样本；但更接近宏观而非主题。",
    },
]

# ---------------------------------------------------------------- Research Capability Matrix（§十一）

CAPABILITY_MATRIX = [
    {
        "capability": "Time Observation",
        "status": "PARTIAL",
        "evidence": "191 候选扫描 → 最终 1 个稳健独立结构（汽车族 EARLY_SIGNAL）",
        "blocker": "theme_family_count 上限 = 2；有效观测仅 7 年（N ≤ 7，达不到 N ≥ 8）",
        "unlock_by": "补录 ≥ 2 个独立主题族（使 theme_family_count ≥ 4）+ 扩样至 N ≥ 8",
    },
    {
        "capability": "Seasonal",
        "status": "BLOCKED",
        "evidence": "全量扫描中 SEASONAL 类候选 1 条（N=2，INSUFFICIENT_DATA）；无 SEASONAL_DEMAND 机制",
        "blocker": "无终端需求季节性数据（销量 / 库存 / 价格）；无连续行情序列做中性基准",
        "unlock_by": "补录需求侧数据（产销 / 库存 / 价格）+ 连续行业指数行情",
    },
    {
        "capability": "Calendar-driven",
        "status": "PARTIAL",
        "evidence": "汽车族机制画像为 CALENDAR_DRIVEN + POLICY_CADENCE + REPORTING_CADENCE（MEDIUM）",
        "blocker": "无制度性日历的结构化数据（财报窗口 / 会议 / 规划节奏）；机制解释多为 post-hoc（LOW）",
        "unlock_by": "建立「制度性日历」结构化表（财报窗口 / 国常会 / 五年规划 / 预算节奏）",
    },
    {
        "capability": "Event-driven",
        "status": "BLOCKED",
        "evidence": "INDUSTRY_EVENT_DRIVEN = 0 条候选；事件表无 industry / holiday 类型",
        "blocker": "无行业事件日历（车展 / CES / MWC / 发布会季）；event_type 未使用 industry",
        "unlock_by": "补录行业事件日历（展会 / 发布会 / 行业大会）+ 启用 industry / holiday 事件类型",
    },
    {
        "capability": "Phase Transition",
        "status": "LIMITED",
        "evidence": "115 条 PHASE_TRANSITION 候选，但 7/7 阶段全部为「派生」（残差 ≤ 11 天）",
        "blocker": "阶段迁移的时间节奏 = EARLY_SIGNAL 聚集 + 典型 Campaign 时长 → 无独立信息",
        "unlock_by": "补录更多「有完整 lifecycle」的历史对象（当前仅 1/13 达 COMPLETE）",
    },
    {
        "capability": "Structural Analogy",
        "status": "BLOCKED",
        "evidence": "PROJECT_STATE 已记录：5 个 Current Candidate 中 4 个的 Macro Theme 无同名历史 cycle → Pattern 层恒 0",
        "blocker": "历史侧仅 2 个 Macro Theme，当前侧已声明 4 个 → 3 个主题（电力设备 / 信息通信 / 高端装备）无历史可类比",
        "unlock_by": "补录当前侧已声明的 3 个 Macro Theme 的历史 Cycle（**最高优先级**）",
    },
]

# ---------------------------------------------------------------- 数据装载


def load_export():
    with io.open(EXPORT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_current_candidates():
    if not os.path.exists(CURRENT_CANDIDATES):
        return None
    with io.open(CURRENT_CANDIDATES, "r", encoding="utf-8") as f:
        return json.load(f)


def q(cur, sql, args=()):
    return cur.execute(sql, args).fetchall()


# ---------------------------------------------------------------- 1. Dataset Inventory


def dataset_inventory(cur, export):
    out = {}
    tables = [
        "campaigns", "themes", "campaign_themes", "research_rules", "annual_reviews",
        "campaign_phases", "events", "campaign_events", "evidences", "campaign_evidences",
        "sources", "securities", "campaign_securities", "market_series", "market_daily",
        "trading_calendar", "campaign_date_observations",
    ]
    out["db_row_counts"] = {t: q(cur, "SELECT COUNT(*) FROM %s" % t)[0][0] for t in tables}
    out["export_counts"] = {
        k: len(export.get(k) or []) for k in ("rules", "signals", "campaigns", "research_candidates", "events", "securities")
    }

    out["campaign_years"] = [
        {"year": r[0], "campaigns": r[1]}
        for r in q(cur, "SELECT campaign_year, COUNT(*) FROM campaigns GROUP BY campaign_year ORDER BY campaign_year")
    ]
    out["annual_review_status"] = [
        {"status": r[0], "n": r[1]}
        for r in q(cur, "SELECT status, COUNT(*) FROM annual_reviews GROUP BY status ORDER BY status")
    ]
    out["annual_reviews_by_rule"] = [
        {"rule_id": r[0], "years_reviewed": r[1], "years": r[2]}
        for r in q(
            cur,
            "SELECT rule_id, COUNT(*), GROUP_CONCAT(year) FROM annual_reviews GROUP BY rule_id ORDER BY rule_id",
        )
    ]
    out["classification_distribution"] = [
        {"classification": r[0], "n": r[1]}
        for r in q(cur, "SELECT classification, COUNT(*) FROM campaigns GROUP BY classification ORDER BY classification")
    ]
    out["strength_distribution"] = [
        {"strength": r[0], "n": r[1]}
        for r in q(cur, "SELECT COALESCE(strength,'(null)'), COUNT(*) FROM campaigns GROUP BY strength ORDER BY 1")
    ]
    out["result_distribution"] = [
        {"result": r[0], "n": r[1]}
        for r in q(cur, "SELECT result, COUNT(*) FROM campaigns GROUP BY result ORDER BY result")
    ]
    out["theme_type_distribution"] = [
        {"theme_type": r[0], "n": r[1]}
        for r in q(cur, "SELECT theme_type, COUNT(*) FROM themes GROUP BY theme_type ORDER BY theme_type")
    ]
    out["campaign_themes_role"] = [
        {"role": r[0], "n": r[1]}
        for r in q(cur, "SELECT role, COUNT(*) FROM campaign_themes GROUP BY role ORDER BY role")
    ]
    return out


# ---------------------------------------------------------------- 2. Macro Theme Coverage Matrix


def build_theme_index(cur):
    """构建 theme_id → macro_theme_id 映射（canonical CMTR v1：沿 parent 链上溯）。

    **与 `discover_time_observation_patterns.py` 共用同一实现**（`theme_taxonomy.py`），
    避免「resolved vs direct」两套口径再次分叉。本函数保持原返回契约
    （`(root_map, name_map, parent_map)`），因此审计输出与重构前逐字节一致。
    """
    tax = theme_taxonomy.load_from_cursor(cur)
    return tax.root_map(), tax.name_map(), tax.parent_map()


def macro_theme_matrix(cur, export):
    theme2macro, theme_name, _ = build_theme_index(cur)

    # campaign → themes（DB）
    camp_themes = collections.defaultdict(list)
    for cid, tid in q(cur, "SELECT campaign_id, theme_id FROM campaign_themes"):
        camp_themes[cid].append(tid)

    # campaign → year / rule / theme_cycle_id（theme_cycle_id 只在 export 侧）
    camp_year = {r[0]: r[1] for r in q(cur, "SELECT campaign_id, campaign_year FROM campaigns")}
    camp_rule = {r[0]: r[1] for r in q(cur, "SELECT campaign_id, rule_id FROM campaigns")}
    cycle_of = {}
    for o in export.get("campaigns") or []:
        cycle_of[o["campaign_id"]] = o.get("theme_cycle_id")

    # export 侧对象（含 research candidates）与 lifecycle
    objs = []
    for kind, key in (("campaign", "campaigns"), ("research_candidate", "research_candidates")):
        for o in export.get(key) or []:
            objs.append({"kind": kind, "id": o["campaign_id"], "obj": o, "year": o.get("year")})

    # evidence per campaign（DB）
    ev_per_camp = collections.defaultdict(int)
    for cid, n in q(cur, "SELECT campaign_id, COUNT(*) FROM campaign_evidences GROUP BY campaign_id"):
        ev_per_camp[cid] = n

    # event per campaign（DB）
    evt_per_camp = collections.defaultdict(int)
    for cid, n in q(cur, "SELECT campaign_id, COUNT(*) FROM campaign_events GROUP BY campaign_id"):
        evt_per_camp[cid] = n

    # macro theme → 归集
    agg = collections.defaultdict(
        lambda: {
            "theme_ids": set(),
            "campaign_ids": set(),
            "research_candidate_ids": set(),
            "years": set(),
            "cycles": set(),
            "lifecycle_stages": collections.Counter(),
            "evidence_total": 0,
            "evidence_objects": 0,
            "event_total": 0,
            "event_objects": 0,
            "lifecycle_complete": 0,
            "lifecycle_partial": 0,
            "lifecycle_sparse": 0,
            "lifecycle_unknown": 0,
            "series_ids": set(),
        }
    )

    # export 侧 theme 名 → DB theme_id 反查
    name2tid = {v: k for k, v in theme_name.items()}

    # ★ 两种 macro 解析方式（**必须同时记录**，二者不一致本身就是覆盖度问题）
    #   (a) resolved：沿 parent 链上溯（taxonomy 完整时正确）
    #   (b) direct  ：themes 列表中**直接出现** Macro Theme 名（v0.2 discovery 用的口径）
    macro_names = {r[0]: r[1] for r in q(cur, "SELECT theme_id, name FROM themes WHERE parent_theme_id IS NULL")}
    resolution_discrepancy = []

    for ob in objs:
        o = ob["obj"]
        tnames = [t.get("name") for t in (o.get("themes") or [])]
        macros_resolved = set()
        for tn in tnames:
            tid = name2tid.get(tn)
            if tid and theme2macro.get(tid):
                macros_resolved.add(theme2macro[tid])
        macros_direct = {tid for tid, nm in macro_names.items() if nm in tnames}

        if macros_resolved != macros_direct:
            resolution_discrepancy.append(
                {
                    "object_id": ob["id"],
                    "kind": ob["kind"],
                    "themes": tnames,
                    "resolved_macro": sorted(macros_resolved),
                    "direct_macro": sorted(macros_direct),
                    "note": "两种解析口径结果不同 → 该对象在「按名称匹配」的扫描中会被漏掉。",
                }
            )

        macros = macros_resolved
        if not macros:
            continue
        for m in macros:
            a = agg[m]
            a["theme_ids"].update(
                name2tid[tn] for tn in tnames if name2tid.get(tn) and theme2macro.get(name2tid[tn]) == m
            )
            if ob["kind"] == "campaign":
                a["campaign_ids"].add(ob["id"])
                cyc = cycle_of.get(ob["id"])
                if cyc:
                    a["cycles"].add(cyc)
            else:
                a["research_candidate_ids"].add(ob["id"])
            if ob["year"]:
                a["years"].add(ob["year"])
            stages = {l["stage"] for l in (o.get("lifecycle") or [])}
            for s in stages:
                a["lifecycle_stages"][s] += 1
            rating = rate_lifecycle(stages)
            a["lifecycle_" + rating.lower()] += 1
            if ob["kind"] == "campaign":
                a["evidence_total"] += ev_per_camp.get(ob["id"], 0)
                a["event_total"] += evt_per_camp.get(ob["id"], 0)
                if ev_per_camp.get(ob["id"], 0):
                    a["evidence_objects"] += 1
                if evt_per_camp.get(ob["id"], 0):
                    a["event_objects"] += 1

    # macro theme → securities（代理指标）
    sec_per_macro = collections.defaultdict(set)
    for cid, sid in q(cur, "SELECT campaign_id, security_id FROM campaign_securities"):
        tids = camp_themes.get(cid) or []
        for tid in tids:
            m = theme2macro.get(tid)
            if m:
                sec_per_macro[m].add(sid)

    out = []
    for r in q(cur, "SELECT theme_id, name FROM themes WHERE parent_theme_id IS NULL ORDER BY theme_id"):
        m, mname = r[0], r[1]
        a = agg.get(m)
        if a is None:
            out.append(
                {
                    "macro_theme_id": m,
                    "macro_theme_name": mname,
                    "theme_cycles": 0,
                    "theme_cycle_ids": [],
                    "campaigns": 0,
                    "research_candidates": 0,
                    "years_covered": [],
                    "lifecycle_coverage": {},
                    "lifecycle_stages_present": 0,
                    "lifecycle_stages_total": len(LC_STAGES),
                    "lifecycle_rating": {},
                    "evidence_coverage": {"total": 0, "objects_with_evidence": 0},
                    "event_coverage": {"total": 0, "objects_with_events": 0},
                    "securities": 0,
                    "status": "EMPTY",
                }
            )
            continue
        n_objs = len(a["campaign_ids"]) + len(a["research_candidate_ids"])
        lc_present = sum(1 for s in LC_STAGES if a["lifecycle_stages"].get(s))
        out.append(
            {
                "macro_theme_id": m,
                "macro_theme_name": mname,
                "theme_cycles": len(a["cycles"]),
                "theme_cycle_ids": sorted(a["cycles"]),
                "campaigns": len(a["campaign_ids"]),
                "research_candidates": len(a["research_candidate_ids"]),
                "years_covered": sorted(a["years"]),
                "years_span": (max(a["years"]) - min(a["years"]) + 1) if a["years"] else 0,
                "lifecycle_coverage": {s: a["lifecycle_stages"].get(s, 0) for s in LC_STAGES},
                "lifecycle_stages_present": lc_present,
                "lifecycle_stages_total": len(LC_STAGES),
                "lifecycle_rating": {
                    "complete": a["lifecycle_complete"],
                    "partial": a["lifecycle_partial"],
                    "sparse": a["lifecycle_sparse"],
                    "unknown": a["lifecycle_unknown"],
                },
                "evidence_coverage": {
                    "total": a["evidence_total"],
                    "objects_with_evidence": a["evidence_objects"],
                    "objects_total": len(a["campaign_ids"]),
                    "avg_per_campaign": round(a["evidence_total"] / len(a["campaign_ids"]), 2) if a["campaign_ids"] else 0,
                },
                "event_coverage": {
                    "total": a["event_total"],
                    "objects_with_events": a["event_objects"],
                    "objects_total": len(a["campaign_ids"]),
                },
                "securities": len(sec_per_macro.get(m, ())),
                "objects_total": n_objs,
                "status": "COVERED" if a["campaign_ids"] else ("RESEARCH_CANDIDATE_ONLY" if n_objs else "EMPTY"),
            }
        )
    return out, resolution_discrepancy


# ---------------------------------------------------------------- 3. Lifecycle Completeness


def rate_lifecycle(stages):
    """评级（**只评级，不补齐**）。"""
    s = set(stages)
    if not s:
        return "UNKNOWN"
    # COMPLETE：形成 → 确认 → 主升 → 顶 → 结束，全链路可读
    has_full = (
        "EARLY_SIGNAL" in s
        and "THEME_FORMING" in s
        and "BROAD_CONFIRMATION" in s
        and "MAIN_RISE" in s
        and "PEAK" in s
        and ({"DECLINING", "MAIN_END"} & s)
    )
    if has_full:
        return "COMPLETE"
    # PARTIAL：有起点 + 顶 + 结束，但缺形成 / 确认
    has_ends = "EARLY_SIGNAL" in s and "PEAK" in s and ({"MAIN_END", "DECLINING"} & s)
    if has_ends and len(s) >= 4:
        return "PARTIAL"
    # SPARSE：阶段过少
    if len(s) <= 3:
        return "SPARSE"
    return "PARTIAL"


def lifecycle_completeness(cur, export):
    theme2macro, theme_name, _ = build_theme_index(cur)
    name2tid = {v: k for k, v in theme_name.items()}
    rows = []
    for kind, key in (("campaign", "campaigns"), ("research_candidate", "research_candidates")):
        for o in export.get(key) or []:
            stages = [l["stage"] for l in (o.get("lifecycle") or [])]
            present = [s for s in LC_STAGES if s in stages]
            missing = [s for s in LC_STAGES if s not in stages]
            # 任务书 7 阶段视角（用别名映射）
            audit_present, audit_missing = [], []
            for st in AUDIT_STAGES:
                real = STAGE_ALIAS.get(st, [st])
                if any(r in stages for r in real):
                    audit_present.append(st)
                else:
                    audit_missing.append(st)
            macros = sorted(
                {
                    theme2macro[name2tid[t["name"]]]
                    for t in (o.get("themes") or [])
                    if name2tid.get(t.get("name")) and theme2macro.get(name2tid[t["name"]])
                }
            )
            rows.append(
                {
                    "object_id": o["campaign_id"],
                    "kind": kind,
                    "year": o.get("year"),
                    "macro_themes": macros,
                    "stages_present": present,
                    "stages_missing": missing,
                    "stage_count": len(present),
                    "audit_stages_present": audit_present,
                    "audit_stages_missing": audit_missing,
                    "rating": rate_lifecycle(stages),
                }
            )
    rows.sort(key=lambda r: (r["year"] or 0, r["object_id"]))
    return rows


# ---------------------------------------------------------------- 4. Evidence Coverage


def evidence_coverage(cur, export):
    raw = [
        {"evidence_type": r[0], "n": r[1]}
        for r in q(cur, "SELECT evidence_type, COUNT(*) FROM evidences GROUP BY evidence_type ORDER BY COUNT(*) DESC, evidence_type")
    ]
    canon = collections.Counter()
    unmapped = []
    for r in raw:
        c = EVIDENCE_TYPE_MAP.get(r["evidence_type"])
        if c is None:
            unmapped.append(r["evidence_type"])
            c = "UNCLASSIFIED"
        canon[c] += r["n"]

    by_role = [{"evidence_role": r[0], "n": r[1]} for r in q(cur, "SELECT evidence_role, COUNT(*) FROM evidences GROUP BY evidence_role ORDER BY evidence_role")]
    by_conf = [{"confidence": r[0], "n": r[1]} for r in q(cur, "SELECT confidence, COUNT(*) FROM evidences GROUP BY confidence ORDER BY confidence")]
    by_temporal = [
        {"temporal_relation": r[0] if r[0] is not None else "(null)", "n": r[1]}
        for r in q(cur, "SELECT temporal_relation, COUNT(*) FROM evidences GROUP BY temporal_relation ORDER BY 1")
    ]
    src_type = [{"source_type": r[0], "n": r[1]} for r in q(cur, "SELECT source_type, COUNT(*) FROM sources GROUP BY source_type ORDER BY COUNT(*) DESC, source_type")]
    src_tier = [{"tier": r[0], "n": r[1]} for r in q(cur, "SELECT tier, COUNT(*) FROM sources GROUP BY tier ORDER BY tier")]

    present_canon = [t for t in CANONICAL_EVIDENCE_TYPES if canon.get(t)]
    missing_canon = [t for t in CANONICAL_EVIDENCE_TYPES if not canon.get(t)]

    return {
        "total_evidences": sum(r["n"] for r in raw),
        "raw_evidence_type_distribution": raw,
        "canonical_distribution": {t: canon.get(t, 0) for t in CANONICAL_EVIDENCE_TYPES + ["UNCLASSIFIED"]},
        "canonical_present": present_canon,
        "canonical_missing": missing_canon,
        "normalization_map": EVIDENCE_TYPE_MAP,
        "unmapped_raw_types": sorted(set(unmapped)),
        "by_role": by_role,
        "by_confidence": by_conf,
        "by_temporal_relation": by_temporal,
        "source_type_distribution": src_type,
        "source_tier_distribution": src_tier,
        "data_quality_note": (
            "⚠️ `evidences.evidence_type` 在 schema 中是**自由文本（无 CHECK 约束）**，"
            "DB 内中英文混用（`行情数据` 与 `market_data`、`政策文件` 与 `official_document` 并存）→ "
            "统计前必须先归一化。这是可修复的数据质量问题，建议在下一轮补录时统一口径。"
        ),
    }


# ---------------------------------------------------------------- 5. Event Coverage


def event_coverage(cur, export):
    db_types = collections.Counter(r[0] for r in q(cur, "SELECT event_type FROM events"))
    ex_types = collections.Counter(e.get("event_type") for e in (export.get("events") or []))
    present = sorted(set(db_types) | set(ex_types))
    missing_schema_types = [t for t in SCHEMA_EVENT_TYPES if t not in present]

    by_year = [
        {"year": r[0], "n": r[1]}
        for r in q(cur, "SELECT substr(date,1,4) AS y, COUNT(*) FROM events GROUP BY y ORDER BY y")
    ]

    capability = []
    for key, label in EVENT_CAPABILITY_TYPES:
        if key in present:
            n = db_types.get(key, 0)
            status = "AVAILABLE" if n > 0 else "DECLARED_UNUSED"
        else:
            n = 0
            status = "NOT_AVAILABLE"
        capability.append(
            {
                "capability_key": key,
                "label": label,
                "status": status,
                "event_count": n,
                "schema_allows": key in SCHEMA_EVENT_TYPES,
            }
        )

    return {
        "total_events_db": sum(db_types.values()),
        "total_events_export": sum(ex_types.values()),
        "db_event_type_distribution": dict(sorted(db_types.items())),
        "export_event_type_distribution": dict(sorted(ex_types.items())),
        "present_types": present,
        "missing_schema_types": missing_schema_types,
        "capability_coverage": capability,
        "by_year": by_year,
        "not_available_count": sum(1 for c in capability if c["status"] == "NOT_AVAILABLE"),
        "epistemic_note": (
            "**absence of evidence ≠ evidence of absence**：以下类别在数据库中**不存在记录**，"
            "只说明 ThreeC **尚未登记**该类事件，**不能**推断该机制在 A 股历史中不存在。"
        ),
    }


# ---------------------------------------------------------------- 6. Market Data Coverage


def market_data_coverage(cur):
    by_year = [
        {"year": r[0], "active_series": r[1], "rows": r[2]}
        for r in q(
            cur,
            "SELECT substr(trade_date,1,4) AS y, COUNT(DISTINCT series_id), COUNT(*) "
            "FROM market_daily GROUP BY y ORDER BY y",
        )
    ]
    series = []
    for r in q(
        cur,
        "SELECT ms.series_id, ms.name, ms.series_type, MIN(md.trade_date), MAX(md.trade_date), COUNT(md.trade_date) "
        "FROM market_series ms LEFT JOIN market_daily md ON md.series_id = ms.series_id "
        "GROUP BY ms.series_id ORDER BY ms.series_type, ms.series_id",
    ):
        sid, name, stype, a, b, n = r
        span_days = _days(a, b) if (a and b) else None
        yrs = sorted({x[0] for x in q(cur, "SELECT DISTINCT substr(trade_date,1,4) FROM market_daily WHERE series_id=?", (sid,))})
        span_years = round(span_days / 365.0, 2) if span_days else 0
        # 采样分类：不是「行数够多」，而是「跨年跨度是否覆盖研究期」
        if (n or 0) <= 1:
            cls = "EMPTY_PLACEHOLDER"
        elif len(yrs) >= 6:
            cls = "CONTINUOUS"
        elif span_years < 3:
            cls = "WINDOW_SAMPLED"
        else:
            cls = "PARTIAL_SPAN"
        series.append(
            {
                "series_id": sid,
                "name": name,
                "series_type": stype,
                "first_date": a,
                "last_date": b,
                "rows": n or 0,
                "span_days": span_days,
                "span_years": span_years,
                "years_covered": yrs,
                "year_count": len(yrs),
                "sampling_class": cls,
            }
        )

    by_type = [
        {"series_type": r[0], "n": r[1]}
        for r in q(cur, "SELECT series_type, COUNT(*) FROM market_series GROUP BY series_type ORDER BY series_type")
    ]
    empty = [s["series_id"] for s in series if s["sampling_class"] == "EMPTY_PLACEHOLDER"]
    continuous = [s["series_id"] for s in series if s["sampling_class"] == "CONTINUOUS"]
    windowed = [s["series_id"] for s in series if s["sampling_class"] == "WINDOW_SAMPLED"]
    benchmarks = [s["series_id"] for s in series if s["series_type"] == "benchmark"]
    calendar = q(cur, "SELECT MIN(trade_date), MAX(trade_date), COUNT(*) FROM trading_calendar")[0]

    return {
        "series_by_type": by_type,
        "total_series": len(series),
        "empty_placeholder_series": empty,
        "empty_placeholder_count": len(empty),
        "continuous_series": continuous,
        "continuous_count": len(continuous),
        "window_sampled_series": windowed,
        "window_sampled_count": len(windowed),
        "benchmark_series": benchmarks,
        "benchmark_count": len(benchmarks),
        "by_year": by_year,
        "series_detail": series,
        "trading_calendar": {"first": calendar[0], "last": calendar[1], "rows": calendar[2]},
        "key_finding": (
            "**行情数据是「按 Campaign 窗口采样」的，不是连续时间序列。** "
            "40 条 series 中：连续（覆盖 ≥ 6 个年度）%d 条、窗口采样（跨度 < 3 年）%d 条、"
            "空占位（仅 1 行）%d 条；benchmark 仅 %d 条（SH000300，唯一覆盖完整 2018–2025）。"
            "年度活跃 series 数从 2022 的 15 条降到 2025 的 4 条。"
            % (len(continuous), len(windowed), len(empty), len(benchmarks))
        ),
        "consequences": [
            "无法为所有年份构造「中性市场基准」→ Time Observation 的背景基准只能部分可用",
            "无法做跨主题的相位对比 → Structural Analogy 缺少共同的可比时间轴",
            "%d 条概念指数为空占位（仅 1 行）→ AD_AUTO / NEV / ROBOTAXI / V2X / AUTO_PARTS / AUTO_SW 实际无数据" % len(empty),
            "2025 年仅 4 条 series 活跃 → 最新年度的行情核验能力最弱",
        ],
    }


def _days(a, b):
    y1, m1, d1 = int(a[0:4]), int(a[5:7]), int(a[8:10])
    y2, m2, d2 = int(b[0:4]), int(b[5:7]), int(b[8:10])
    return _ord(y2, m2, d2) - _ord(y1, m1, d1)


def _ord(y, m, d):
    per = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    days = 0
    for yy in range(1, y):
        days += 366 if (yy % 4 == 0 and (yy % 100 != 0 or yy % 400 == 0)) else 365
    if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0):
        per[1] = 29
    return days + sum(per[: m - 1]) + d


# ---------------------------------------------------------------- 7. Verification Coverage


def verification_coverage(cur):
    rows = [
        {
            "campaign_id": r[0],
            "date_role": r[1],
            "candidate_date": r[2],
            "verified_date": r[3],
            "verification_method": r[4],
            "confidence": r[5],
        }
        for r in q(
            cur,
            "SELECT campaign_id, date_role, candidate_date, verified_date, verification_method, confidence "
            "FROM campaign_date_observations ORDER BY campaign_id, date_role",
        )
    ]
    verified = [r for r in rows if r["verified_date"]]
    by_method = collections.Counter(r["verification_method"] for r in rows)
    by_conf = collections.Counter(r["confidence"] for r in rows)
    return {
        "total_date_observations": len(rows),
        "verified_count": len(verified),
        "verified_ratio": round(len(verified) / len(rows), 4) if rows else 0,
        "by_method": dict(sorted(by_method.items())),
        "by_confidence": dict(sorted(by_conf.items())),
        "rows": rows,
        "key_finding": (
            "**全部 %d 条日期观测的 `verified_date` 均为 NULL** —— 即使 `verification_method` 标为 "
            "`market_data` 的 6 条也未写回核验日期。且**全部 `confidence = low`**。"
            "→ 当前**没有任何日期完成最终核验**，这是数据可信度的硬天花板。" % len(rows)
        ),
    }


# ---------------------------------------------------------------- 8. Taxonomy Integrity


def taxonomy_integrity(cur, export, current):
    theme2macro, theme_name, parent = build_theme_index(cur)
    orphans = [
        {"theme_id": r[0], "name": r[1], "theme_type": r[2], "parent": r[3]}
        for r in q(
            cur,
            "SELECT t.theme_id, t.name, t.theme_type, t.parent_theme_id FROM themes t "
            "WHERE (SELECT COUNT(*) FROM campaign_themes ct WHERE ct.theme_id = t.theme_id) = 0 "
            "ORDER BY t.theme_id",
        )
    ]
    db_names = set(theme_name.values())

    # export 中出现但 DB themes 没有的 theme 名
    export_only = set()
    for key in ("campaigns", "research_candidates"):
        for o in export.get(key) or []:
            for t in o.get("themes") or []:
                n = t.get("name")
                if n and n not in db_names:
                    export_only.add(n)

    # 历史 Macro Theme
    hist_macros = [
        {"theme_id": r[0], "name": r[1]}
        for r in q(cur, "SELECT theme_id, name FROM themes WHERE parent_theme_id IS NULL ORDER BY theme_id")
    ]
    hist_macro_names = {m["name"] for m in hist_macros}

    # Current Candidate 声明的 Macro Theme
    declared = []
    if current:
        for c in current.get("candidates") or []:
            mt = c.get("macro_theme")
            if mt:
                declared.append({"candidate_id": c.get("candidate_id"), "macro_theme": mt})
    declared_names = sorted({d["macro_theme"] for d in declared})
    declared_no_history = [n for n in declared_names if n not in hist_macro_names]

    # C-2019-AD 的挂接缺口（Phase 7.3 已记录，此处量化）
    unlinked = []
    for r in q(
        cur,
        "SELECT c.campaign_id, c.campaign_year, GROUP_CONCAT(t.name, ' | ') "
        "FROM campaigns c JOIN campaign_themes ct ON ct.campaign_id = c.campaign_id "
        "JOIN themes t ON t.theme_id = ct.theme_id "
        "WHERE c.campaign_id NOT IN ("
        "  SELECT ct2.campaign_id FROM campaign_themes ct2 JOIN themes t2 ON t2.theme_id = ct2.theme_id "
        "  WHERE t2.parent_theme_id IS NULL) "
        "GROUP BY c.campaign_id ORDER BY c.campaign_id",
    ):
        unlinked.append({"campaign_id": r[0], "year": r[1], "themes": r[2]})

    return {
        "macro_themes_in_history": hist_macros,
        "macro_theme_count_history": len(hist_macros),
        "macro_themes_declared_by_current_candidates": declared_names,
        "macro_theme_count_declared": len(declared_names),
        "declared_but_no_history": declared_no_history,
        "declared_detail": declared,
        "orphan_themes": orphans,
        "orphan_theme_count": len(orphans),
        "export_only_themes": sorted(export_only),
        "campaigns_without_macro_theme_link": unlinked,
        "key_finding": (
            "**历史侧只有 %d 个 Macro Theme，而 Current Candidate 侧已声明 %d 个** → "
            "%s 在历史数据中**没有任何 Theme Cycle**。这直接导致 Similarity 的 Pattern 层恒为 0"
            "（PROJECT_STATE 已记录），是 Structural Analogy 当前最大的单点瓶颈。"
            % (len(hist_macros), len(declared_names), " / ".join(declared_no_history) or "（无）")
        ),
    }


# ---------------------------------------------------------------- 9. Domain Coverage


def domain_coverage(cur, export):
    theme2macro, theme_name, _ = build_theme_index(cur)
    db_names = set(theme_name.values())
    name2tid = {v: k for k, v in theme_name.items()}

    # 每个 macro theme 的 campaign 数与年份
    camp_themes = collections.defaultdict(set)
    for cid, tid in q(cur, "SELECT campaign_id, theme_id FROM campaign_themes"):
        camp_themes[cid].add(tid)
    camp_year = {r[0]: r[1] for r in q(cur, "SELECT campaign_id, campaign_year FROM campaigns")}
    # ★ 使用 export 的 theme_cycle_id（不是 rule_id —— rule 是观察规则，不是主题周期）
    cycle_of = {o["campaign_id"]: o.get("theme_cycle_id") for o in (export.get("campaigns") or [])}

    out = []
    for label, theme_ids, name_probes in DOMAIN_PROBES:
        # `DOMAIN_PROBES.theme_ids` 是 v0.1 的数据快照（当时「电力设备」尚不存在）。
        # 为避免探针表成为陈旧常量，此处按**主题名称精确匹配**动态补入 theme_id
        # （精确匹配 —— 不用子串，否则「消费」会误命中「汽车消费/购置税刺激」）。
        extra = {name2tid[nm] for nm in name_probes if nm in name2tid}
        matched_tids = sorted({t for t in theme_ids if t in theme_name} | extra)
        probe_hits = sorted(n for n in db_names if any(p in n for p in name_probes))
        cids = set()
        for cid, tids in camp_themes.items():
            if any(theme2macro.get(t) in matched_tids for t in tids) or any(t in matched_tids for t in tids):
                cids.add(cid)
        years = sorted({camp_year.get(c) for c in cids if camp_year.get(c)})
        cycles = sorted({cycle_of.get(c) for c in cids if cycle_of.get(c)})

        if cids and len(cycles) >= 2:
            status = "COVERED_WITH_CYCLES"
        elif cids:
            status = "COVERED_SINGLE_CYCLE"
        elif probe_hits:
            status = "SCATTERED_ONLY"
        else:
            status = "ABSENT"
        out.append(
            {
                "domain": label,
                "theme_ids": matched_tids,
                "theme_name_matches": probe_hits,
                "campaigns": sorted(cids),
                "campaign_count": len(cids),
                "theme_cycles": len(cycles),
                "theme_cycle_ids": cycles,
                "years_covered": years,
                "status": status,
            }
        )
    return out


# ---------------------------------------------------------------- 10. Coverage Ceiling


def coverage_ceiling(macro_matrix, discovery_scan_map, current):
    hist = [m for m in macro_matrix if m["status"] != "EMPTY"]
    return {
        "theme_family_count_history": len(hist),
        "theme_family_count_ceiling": len(hist),
        "statement": (
            "**theme_family_count 上限 = %d。** 因此："
            "(1) 单主题规律**不能**证明跨主题规律；"
            "(2) Structural Analogy 的 Pattern 层只能在 2 个族之间匹配；"
            "(3) Time Observation 的「跨族稳健性」检查在当前数据下**不可能通过**。"
            % len(hist)
        ),
        "consequences": [
            "Time Observation：v0.2 全量扫描中唯一稳健结构为**单族**（汽车），无法证明跨族普适性",
            "Structural Analogy：当前侧已声明 %d 个 Macro Theme，历史侧仅 %d 个 → 至少 %d 个主题无历史可类比"
            % (
                len({d.get('macro_theme') for d in (current.get('candidates') or []) if d.get('macro_theme')}) if current else 0,
                len(hist),
                max(
                    0,
                    len({d.get('macro_theme') for d in (current.get('candidates') or []) if d.get('macro_theme')}) - len(hist),
                )
                if current
                else 0,
            ),
            "统计功效：有效观测仅 7 年（2019–2025）→ 所有 N ≤ 7，永远达不到 N ≥ 8 的「稳定规律」档位",
        ],
        "minimum_to_unlock": {
            "cross_family_robustness": "theme_family_count ≥ 4（即再补 ≥ 2 个独立 Macro Theme）",
            "stable_pattern_grade": "有效观测 ≥ 8 年（补 2018 之前或 2026+）",
            "structural_analogy": "补录当前侧已声明但无历史的 %s"
            % (" / ".join(sorted({d.get('macro_theme') for d in (current.get('candidates') or []) if d.get('macro_theme')} - {m['macro_theme_name'] for m in hist}))
               if current
               else "（无）"),
        },
    }


# ---------------------------------------------------------------- 11. Waves


def build_waves(domain_rows, macro_matrix, taxonomy, event_cov, market_cov):
    return {
        "principle": "**以最少的数据建设成本，显著提升 ThreeC 的研究能力。** 不要求一次把整个 A 股历史全部录完。",
        "wave_1": {
            "goal": "最少补录，最大能力提升 —— **修复「当前侧有候选、历史侧无 Cycle」的断裂**",
            "items": [
                {
                    "priority": "P0",
                    "action": "补录「电力设备」Macro Theme 的历史 Cycle（至少 2 个 Campaign，覆盖 ≥ 3 年）",
                    "unlocks": "Structural Analogy Pattern 层（当前恒 0）；同时服务 2 个已存在的当前候选",
                    "why_first": "当前侧已有 CC-2026-COMPUTE-POWER / CC-2026-OFFSHORE-WIND，历史侧完全空白 —— 边际收益最高",
                },
                {
                    "priority": "P0",
                    "action": "补录「信息通信」Macro Theme 的历史 Cycle（至少 1–2 个 Campaign）",
                    "unlocks": "Structural Analogy；并给 Time Observation 提供**第 3 个独立主题族**",
                    "why_first": "当前侧已有 CC-2026-OPTICAL-LINK；光通信有多轮清晰历史周期",
                },
                {
                    "priority": "P1",
                    "action": "修复 taxonomy 缺口：为 C-2019-AD 挂接 Macro Theme「汽车」",
                    "unlocks": "消除 v0.2 中 3 条候选「口径脆弱」的根源（判定不再依赖 2019 是否入样）",
                    "why_first": "**改动量极小（1 行关联），但直接提升已有 Pattern 的稳健性**",
                },
                {
                    "priority": "P1",
                    "action": "统一 `evidences.evidence_type` 口径（中英文混用 → 单一枚举）",
                    "unlocks": "Evidence Coverage 可统计；Phase Evidence Matrix 的 5 个派生维度可靠",
                    "why_first": "纯数据清理，无新研究成本",
                },
                {
                    "priority": "P1",
                    "action": "补录 2018–2025 完整交易日历（当前仅 2022-03 ~ 2024-09）",
                    "unlocks": "所有时间统计可切换到交易日口径（与行情对齐）",
                    "why_first": "一次性、可自动获取、无研究判断成本",
                },
            ],
            "expected_capability_delta": {
                "Structural Analogy": "BLOCKED → PARTIAL（Pattern 层可匹配）",
                "Time Observation": "PARTIAL → PARTIAL+（theme_family_count 2 → 4，跨族稳健性检查首次可用）",
            },
        },
        "wave_2": {
            "goal": "扩展跨行业覆盖 —— 让「跨主题族规律」第一次成为可检验命题",
            "items": [
                {
                    "priority": "P2",
                    "action": "补录「高端装备 / 机器人」Macro Theme 历史 Cycle",
                    "unlocks": "当前侧 CC-2026-EMBODIED-AI 可类比；但历史周期短（2023 起），跨年样本有限",
                },
                {
                    "priority": "P2",
                    "action": "补录「半导体 / 电子」Macro Theme 历史 Cycle（2019–2025 多轮周期）",
                    "unlocks": "纯历史补录（无当前侧候选）；提供第 5 个独立族，显著提升 Time Observation 统计功效",
                },
                {
                    "priority": "P2",
                    "action": "补录「消费」Macro Theme 历史 Cycle",
                    "unlocks": "**Calendar-driven / Holiday-relative 能力的天然样本**（春节 / 双十一 / 中报）",
                },
                {
                    "priority": "P3",
                    "action": "补录「有色 / 资源 / 化工」Macro Theme 历史 Cycle",
                    "unlocks": "供给端 + 商品价格机制 —— 与汽车 / 医药结构差异最大，类比价值高",
                },
                {
                    "priority": "P3",
                    "action": "补录「军工」「金融 / 地产」历史 Cycle",
                    "unlocks": "政策周期样本；但更接近宏观，需先明确 Theme / Macro 边界",
                },
            ],
            "expected_capability_delta": {
                "Time Observation": "PARTIAL+ → USABLE（theme_family_count ≥ 5，跨族稳健性有统计意义）",
                "Seasonal": "BLOCKED → LIMITED（消费族带来需求季节性样本）",
            },
        },
        "wave_3": {
            "goal": "事件 / 日历类深度补录 —— 解锁 Event-driven 与真正的 Calendar-driven",
            "items": [
                {
                    "priority": "P2",
                    "action": "建立结构化「行业事件日历」表（车展 / CES / MWC / 开发者大会 / 发布会季）",
                    "unlocks": "`INDUSTRY_EVENT_DRIVEN` 从 0 条 → 可研究（当前完全没有该类数据）",
                },
                {
                    "priority": "P2",
                    "action": "建立结构化「数据发布日历」表（产销 / 库存 / 价格 / 出口 / PMI）",
                    "unlocks": "`DATA_RELEASE_DRIVEN` 从 0 条 → 可研究；把当前 LOW 置信度的 post-hoc 机制变为 data-supported",
                },
                {
                    "priority": "P3",
                    "action": "建立结构化「制度性日历」表（财报窗口 / 国常会节奏 / 五年规划 / 预算节奏）",
                    "unlocks": "Calendar-driven 从 PARTIAL → USABLE；机制解释从 post-hoc 升级为 data-supported",
                },
                {
                    "priority": "P3",
                    "action": "为每个 Macro Theme 补齐连续行业指数行情（当前仅 2 条 ETF 代理 + 6 条空占位）",
                    "unlocks": "中性市场基准可全年份构造；相位对比有共同时间轴",
                },
                {
                    "priority": "P3",
                    "action": "补录「未成势主题」负样本（观察到但未形成 Campaign）",
                    "unlocks": "**唯一能真正量化幸存者偏差的路径**（当前 negative-control coverage = WEAK）",
                },
            ],
            "expected_capability_delta": {
                "Event-driven": "BLOCKED → PARTIAL",
                "Calendar-driven": "PARTIAL → USABLE",
                "Seasonal": "LIMITED → PARTIAL",
            },
        },
    }


# ---------------------------------------------------------------- 12. Data Risks


def data_risks(inv, ev, evt, mkt, verif, tax, cap):
    return [
        {
            "risk": "样本量不足（有效观测仅 7 年）",
            "severity": "HIGH",
            "detail": "2019–2025；2018 为 no_clear_campaign 反例年 → 所有 N ≤ 7，达不到「稳定规律」档位（N ≥ 8）",
            "mitigation": "补 2018 之前或 2026+ 数据",
        },
        {
            "risk": "主题族上限 = 2（coverage ceiling）",
            "severity": "HIGH",
            "detail": "跨族稳健性检查在当前数据下不可能通过；单族规律无法证明普适性",
            "mitigation": "Wave 1/2 补录 ≥ 2 个独立 Macro Theme",
        },
        {
            "risk": "日期核验为 0（全部 verified_date = NULL，全部 confidence = low）",
            "severity": "HIGH",
            "detail": "即使 method=market_data 的 6 条也未写回核验日期 → 数据可信度硬天花板",
            "mitigation": "人工核验 TOP-01 的 7 个锚点（PROJECT_STATE 已列为 Next Single Goal）",
        },
        {
            "risk": "幸存者偏差无法消除",
            "severity": "HIGH",
            "detail": "只记录「形成 Campaign 的主题」；无「主题级未成势」负样本 → negative-control coverage = WEAK",
            "mitigation": "Wave 3：补录未成势主题",
        },
        {
            "risk": "行情数据为「窗口采样」而非连续序列",
            "severity": "MEDIUM",
            "detail": "仅 1 条 benchmark 连续；%d 条 series 为空占位；年度活跃 series 从 15（2022）降到 4（2025）"
            % len(mkt["empty_placeholder_series"]),
            "mitigation": "Wave 3：补连续行业指数",
        },
        {
            "risk": "Event Calendar 缺 3 类能力关键事件",
            "severity": "MEDIUM",
            "detail": "industry / data_release / holiday 等 %d 类在 DB 中 NOT_AVAILABLE → 两类 Pattern 无法研究"
            % evt["not_available_count"],
            "mitigation": "Wave 3：建立事件日历表",
        },
        {
            "risk": "Evidence 口径不统一（中英文混用，schema 无 CHECK）",
            "severity": "MEDIUM",
            "detail": "`行情数据` 与 `market_data`、`政策文件` 与 `official_document` 并存 → 统计前须归一化",
            "mitigation": "Wave 1：统一 evidence_type 枚举",
        },
        {
            "risk": "taxonomy 缺口造成判定脆弱",
            "severity": "MEDIUM",
            "detail": "%d 个 Campaign 未挂接 Macro Theme；%d 个 theme 为孤立；export 独有 theme：%s"
            % (len(tax["campaigns_without_macro_theme_link"]), tax["orphan_theme_count"], tax["export_only_themes"]),
            "mitigation": "Wave 1：修复 C-2019-AD 挂接 + 建立「主题族 ↔ theme」定义表",
        },
        {
            "risk": "当前侧声明 4 个 Macro Theme，历史侧仅 2 个",
            "severity": "HIGH",
            "detail": "结构性不对称：%s 无历史 Cycle → Similarity Pattern 层恒 0" % " / ".join(tax["declared_but_no_history"]),
            "mitigation": "Wave 1（P0）：优先补录这 3 个主题",
        },
        {
            "risk": "生命周期普遍不完整",
            "severity": "MEDIUM",
            "detail": "13 个对象中仅 1 个达到 COMPLETE；THEME_FORMING / BROAD_CONFIRMATION 各仅 6/13",
            "mitigation": "补录时强制要求完整 lifecycle",
        },
    ]


# ---------------------------------------------------------------- 叙述文本修正


def _patch_derived_notes(art):
    """把叙述文本中**随数据变化的数字/结论**替换为派生值（就地修改，只改叙述）。

    为什么需要：`CAPABILITY_MATRIX` / `data_risks` / `coverage_ceiling.statement` 的文本
    最初按 v0.1 的数据快照撰写，其中若干数字是**当时的实测值**。数据集变化后
    （如 Wave 1A 新增 `TH-POWER`），这些文本会与产物自身的数据**自相矛盾**。

    本函数在写盘前修正它们，使**同一份产物内叙事与数据一致**。

    **只改叙述文本，不改任何统计量**（统计量本身早已全部为派生值）。
    也**不新增字段** —— 只覆写既有字符串，保证 `validate()` 与 CSV 写出不受影响。
    """
    tax = art["taxonomy_integrity"]
    n_family = tax["macro_theme_count_history"]
    n_declared = tax["macro_theme_count_declared"]
    no_hist = list(tax["declared_but_no_history"])
    n_no_hist = len(no_hist)
    no_hist_txt = " / ".join(no_hist) if no_hist else "（无）"

    evt_dist = art["event_coverage"]["db_event_type_distribution"]
    n_industry_evt = evt_dist.get("industry", 0)
    n_holiday_evt = evt_dist.get("holiday", 0)

    lc = art["lifecycle_completeness"]
    n_obj = len(lc)
    n_complete = sum(1 for x in lc if x["rating"] == "COMPLETE")

    # 1) coverage_ceiling.statement
    art["coverage_ceiling"]["statement"] = (
        "**theme_family_count = %d（跨族稳健性检验门槛为 ≥ 4）。** 因此："
        "(1) 单主题规律**不能**证明跨主题规律；"
        "(2) Structural Analogy 的 Pattern 层只能在 %d 个族之间匹配；"
        "(3) Time Observation 的「跨族稳健性」检查在当前数据下**仍不可能通过**。"
        % (n_family, n_family)
    )

    # 2) research_capability_matrix
    for c in art["research_capability_matrix"]:
        name = c["capability"]
        if name == "Time Observation":
            c["blocker"] = ("theme_family_count = %d（门槛 ≥ 4）；有效观测仅 7 年（N ≤ 7，达不到 N ≥ 8）"
                            % n_family)
            c["unlock_by"] = ("补录独立 Macro Theme 至 ≥ 4（当前 %d，还需 %d 个）+ 扩样至 N ≥ 8"
                              % (n_family, max(0, 4 - n_family)))
        elif name == "Event-driven":
            c["evidence"] = ("INDUSTRY_EVENT_DRIVEN = 0 条候选；事件表 industry 类型已启用（%d 条）、"
                             "holiday 仍为 %d 条" % (n_industry_evt, n_holiday_evt))
            c["blocker"] = ("仍无结构化行业事件日历（车展 / CES / MWC / 发布会季）→ 事件样本不足以支撑 Pattern"
                            if n_industry_evt else
                            "无行业事件日历（车展 / CES / MWC / 发布会季）；event_type 未使用 industry")
        elif name == "Phase Transition":
            c["unlock_by"] = ("补录更多「有完整 lifecycle」的历史对象（当前 %d/%d 达 COMPLETE）"
                              % (n_complete, n_obj))
        elif name == "Structural Analogy":
            c["evidence"] = ("当前侧声明 %d 个 Macro Theme，其中 %d 个仍无同名历史 cycle → Pattern 层恒 UNKNOWN"
                             % (n_declared, n_no_hist))
            c["blocker"] = "历史侧 %d 个 Macro Theme；仍无历史者：%s" % (n_family, no_hist_txt)
            c["unlock_by"] = ("补录仍无历史的 %d 个 Macro Theme 的历史 Cycle（%s）" % (n_no_hist, no_hist_txt)
                              if no_hist else "已无缺口（当前侧声明的 Macro Theme 均有历史 Cycle）")

    # 3) data_risks
    for r in art["data_risks"]:
        if r["risk"].startswith("主题族上限"):
            r["risk"] = "主题族数量 = %d（未达 ≥ 4 的跨族稳健性门槛）" % n_family
            r["detail"] = ("跨族稳健性检查在当前数据下仍不可能通过；单族规律无法证明普适性"
                           "（Wave 1A 已由 2 提升至 %d）" % n_family)
            r["mitigation"] = "继续补录独立 Macro Theme 至 ≥ 4"
        elif r["risk"].startswith("当前侧声明"):
            r["risk"] = "当前侧声明 %d 个 Macro Theme，历史侧 %d 个" % (n_declared, n_family)
            r["detail"] = ("结构性不对称：%s 仍无历史 Cycle → Similarity Pattern 层恒 UNKNOWN" % no_hist_txt
                           if no_hist else
                           "结构性不对称已消除：当前侧声明的 Macro Theme 均有历史 Cycle")
            r["mitigation"] = ("Wave 1（P0）：优先补录这 %d 个主题" % n_no_hist) if no_hist else "无需再补"
        elif r["risk"].startswith("Event Calendar 缺"):
            r["risk"] = ("Event Calendar 缺 %d 类能力关键事件"
                         % art["event_coverage"]["not_available_count"])
        elif r["risk"].startswith("生命周期普遍不完整"):
            r["detail"] = ("%d 个对象中仅 %d 个达到 COMPLETE；THEME_FORMING / BROAD_CONFIRMATION 仍为最弱两项"
                           % (n_obj, n_complete))


# ---------------------------------------------------------------- 组装


def build_artifact():
    export = load_export()
    current = load_current_candidates()
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        inv = dataset_inventory(cur, export)
        macro_matrix, resolution_discrepancy = macro_theme_matrix(cur, export)
        lc = lifecycle_completeness(cur, export)
        ev = evidence_coverage(cur, export)
        evt = event_coverage(cur, export)
        mkt = market_data_coverage(cur)
        verif = verification_coverage(cur)
        tax = taxonomy_integrity(cur, export, current)
        domains = domain_coverage(cur, export)
    finally:
        conn.close()

    # discovery scan map（来自 v0.2，若存在）
    disc = None
    disc_path = os.path.join(REPORTS_DIR, "time_observation_candidate_pool_v0_2.json")
    if os.path.exists(disc_path):
        with io.open(disc_path, "r", encoding="utf-8") as f:
            d = json.load(f)
        disc = {
            "scan_space_size": d["scan_map"]["total_candidates"],
            "distinct_samples": d["scan_map"]["distinct_samples"],
            "timeline_candidate": d["scan_map"]["by_promotion_status"].get("TIMELINE_CANDIDATE"),
            "effective_timeline_candidate": d["scan_map"].get("effective_timeline_candidate_count"),
            "effective_distinct_structures": d["scan_map"].get("effective_timeline_candidate_distinct_structures"),
            "pattern_type_distribution": d["scan_map"]["by_pattern_type"],
            "multiple_testing": d["multiple_testing"],
        }

    ceiling = coverage_ceiling(macro_matrix, disc, current)
    waves = build_waves(domains, macro_matrix, tax, evt, mkt)
    risks = data_risks(inv, ev, evt, mkt, verif, tax, ceiling)

    # 优先级框架
    pf = []
    for c in PRIORITY_CANDIDATES:
        total = sum(c["scores"].values())
        has_demand = len(c["already_declared_by"]) > 0
        pf.append(
            {
                "domain": c["domain"],
                "already_declared_by_current_candidates": c["already_declared_by"],
                "has_current_candidate_demand": has_demand,
                "scores": c["scores"],
                "total_score": total,
                "max_score": 3 * len(PRIORITY_DIMENSIONS),
                "wave": "WAVE_1" if has_demand else "WAVE_2",
                "why": c["why"],
                "basis_note": "各维度 basis 见 priority_dimensions；JUDGMENT 项为研究判断，非数据计算结果。",
            }
        )
    # 排序：先「当前侧已有候选需求」（这些是**已存在的断裂**，补录边际收益最高），再总分，再名称
    pf.sort(key=lambda r: (not r["has_current_candidate_demand"], -r["total_score"], r["domain"]))

    art = {
        "artifact": "historical_coverage_matrix",
        "artifact_version": ARTIFACT_VERSION,
        "ruleset_version": RULESET_VERSION,
        "generated_at": SNAPSHOT_DATE,
        "snapshot_date": SNAPSHOT_DATE,
        "generated_by": "research/scripts/audit_historical_coverage.py",
        "research_round": RESEARCH_ROUND,
        "contract_note": (
            "Research Layer Deliverable —— 不是产品 schema，不进入 src/ / DB / schema.sql / "
            "timeline_export_v1.json / contracts / Timeline。"
        ),
        "question": (
            "ThreeC 当前历史数据覆盖到了什么程度？还缺什么？"
            "哪些缺口最影响未来 Time Observation 与 Structural Historical Analogy？"
        ),
        "not_a": [
            "这不是投资价值排名 —— 只做数据建设优先级",
            "这不推荐研究哪只股票或哪个行业",
            "这不补齐任何缺失数据 —— 只做评级与缺口识别",
            "这不把「数据库里没有」推断成「现实中不存在」",
        ],
        "input_snapshot": {
            "canonical_export": "exports/timeline_export_v1.json",
            "export_version": export.get("timeline_export_version"),
            "export_generated_at": export.get("generated_at"),
            "export_source_commit": export.get("source_commit"),
            "research_db": "research/database/cycle_research.db",
            "current_candidates": "research/current/current_candidates.json",
            "current_snapshot_date": current.get("snapshot_date") if current else None,
        },
        "audit_stage_mapping": {
            "note": (
                "任务书 §八 列出的 EXPANSION / WEAKENING / DECLINE 在仓库中**不存在**；"
                "本审计按**显式别名映射**对齐到仓库真实阶段，**不发明新阶段**。"
            ),
            "audit_stages": AUDIT_STAGES,
            "repo_stages": LC_STAGES,
            "alias_map": STAGE_ALIAS,
        },
        "dataset_inventory": inv,
        "macro_theme_matrix": macro_matrix,
        "macro_theme_resolution_discrepancy": {
            "note": (
                "★ 本审计发现：**同一对象的 Macro Theme 有两种解析口径** —— "
                "(a) `resolved`：沿 `themes.parent_theme_id` 链上溯；(b) `direct`：themes 列表中**直接出现** Macro Theme 名。"
                "v0.2 Time Observation Discovery 用的是 (b)，因此把下列对象**排除在主题族之外**，"
                "造成「同一主题族两种成员集合」→ 这正是 v0.2 中 3 条候选口径脆弱的根源。"
            ),
            "count": len(resolution_discrepancy),
            "items": resolution_discrepancy,
        },
        "taxonomy_integrity": tax,
        "lifecycle_completeness": lc,
        "evidence_coverage": ev,
        "event_coverage": evt,
        "market_data_coverage": mkt,
        "verification_coverage": verif,
        "domain_coverage": domains,
        "discovery_cross_reference": disc,
        "research_capability_matrix": [dict(c) for c in CAPABILITY_MATRIX],  # 副本：叙述修正不得污染常量
        "coverage_ceiling": ceiling,
        "priority_dimensions": [
            {"key": k, "label": l, "basis": b} for k, l, b in PRIORITY_DIMENSIONS
        ],
        "priority_framework": pf,
        "waves": waves,
        "data_risks": risks,
    }
    # 写盘前修正「按旧快照撰写」的叙述数字，使同一份产物内叙事与数据一致
    _patch_derived_notes(art)
    return art


# ---------------------------------------------------------------- 自检


def validate(art):
    issues = []
    # 计数一致性
    inv = art["dataset_inventory"]
    if inv["db_row_counts"]["campaigns"] != inv["export_counts"]["campaigns"]:
        issues.append("campaigns 数 DB 与 export 不一致")
    # 主题族矩阵合计
    tot_c = sum(m["campaigns"] for m in art["macro_theme_matrix"])
    if tot_c > inv["export_counts"]["campaigns"]:
        issues.append("macro matrix campaign 合计超过总数")
    # lifecycle 评级合法
    for r in art["lifecycle_completeness"]:
        if r["rating"] not in ("COMPLETE", "PARTIAL", "SPARSE", "UNKNOWN"):
            issues.append("%s: 非法 lifecycle rating %s" % (r["object_id"], r["rating"]))
        if set(r["stages_present"]) & set(r["stages_missing"]):
            issues.append("%s: present 与 missing 有交集" % r["object_id"])
    # event coverage 状态合法
    for c in art["event_coverage"]["capability_coverage"]:
        if c["status"] not in ("AVAILABLE", "DECLARED_UNUSED", "NOT_AVAILABLE"):
            issues.append("event capability %s: 非法状态" % c["capability_key"])
    # 能力矩阵状态合法
    for c in art["research_capability_matrix"]:
        if c["status"] not in ("USABLE", "PARTIAL", "LIMITED", "BLOCKED"):
            issues.append("capability %s: 非法状态" % c["capability"])
    # 禁用词（投资语义）
    banned = ["买入", "卖出", "目标价", "涨幅预测", "胜率", "收益率"]
    negations = ("不", "非", "无", "禁止", "未")
    for path, s in _iter_strings(art):
        for b in banned:
            i = s.find(b)
            while i >= 0:
                if not any(n in s[max(0, i - 12):i] for n in negations):
                    issues.append("%s: 出现非否定语境的「%s」" % (path, b))
                i = s.find(b, i + 1)
    return issues


def _iter_strings(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _iter_strings(v, "%s.%s" % (path, k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _iter_strings(v, "%s[%d]" % (path, i))
    elif isinstance(obj, str):
        yield path, obj


# ---------------------------------------------------------------- CSV


CSV_COLUMNS = [
    "section", "macro_theme_id", "macro_theme_name", "theme_cycles", "campaigns",
    "research_candidates", "years_covered", "lifecycle_stages_present",
    "lifecycle_stages_total", "evidence_total", "event_total", "securities", "status",
]


def write_csv(art):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n")
    w.writeheader()
    for m in art["macro_theme_matrix"]:
        w.writerow(
            {
                "section": "MACRO_THEME",
                "macro_theme_id": m["macro_theme_id"],
                "macro_theme_name": m["macro_theme_name"],
                "theme_cycles": m.get("theme_cycles", 0),
                "campaigns": m.get("campaigns", 0),
                "research_candidates": m.get("research_candidates", 0),
                "years_covered": "|".join(str(y) for y in m.get("years_covered") or []),
                "lifecycle_stages_present": m.get("lifecycle_stages_present", 0),
                "lifecycle_stages_total": m.get("lifecycle_stages_total", len(LC_STAGES)),
                "evidence_total": (m.get("evidence_coverage") or {}).get("total", 0),
                "event_total": (m.get("event_coverage") or {}).get("total", 0),
                "securities": m.get("securities", 0),
                "status": m.get("status", ""),
            }
        )
    for d in art["domain_coverage"]:
        w.writerow(
            {
                "section": "DOMAIN",
                "macro_theme_id": "",
                "macro_theme_name": d["domain"],
                "theme_cycles": d["theme_cycles"],
                "campaigns": d["campaign_count"],
                "research_candidates": "",
                "years_covered": "|".join(str(y) for y in d["years_covered"]),
                "lifecycle_stages_present": "",
                "lifecycle_stages_total": "",
                "evidence_total": "",
                "event_total": "",
                "securities": "",
                "status": d["status"],
            }
        )
    for c in art["event_coverage"]["capability_coverage"]:
        w.writerow(
            {
                "section": "EVENT_CAPABILITY",
                "macro_theme_id": "",
                "macro_theme_name": c["label"],
                "theme_cycles": "",
                "campaigns": "",
                "research_candidates": "",
                "years_covered": "",
                "lifecycle_stages_present": "",
                "lifecycle_stages_total": "",
                "evidence_total": "",
                "event_total": c["event_count"],
                "securities": "",
                "status": c["status"],
            }
        )
    for p in art["priority_framework"]:
        w.writerow(
            {
                "section": "PRIORITY",
                "macro_theme_id": "",
                "macro_theme_name": p["domain"],
                "theme_cycles": "",
                "campaigns": "",
                "research_candidates": len(p["already_declared_by_current_candidates"]),
                "years_covered": "",
                "lifecycle_stages_present": "",
                "lifecycle_stages_total": "",
                "evidence_total": "",
                "event_total": "",
                "securities": "",
                "status": "%d/%d|%s" % (p["total_score"], p["max_score"], p["wave"]),
            }
        )
    for it in art["macro_theme_resolution_discrepancy"]["items"]:
        w.writerow(
            {
                "section": "TAXONOMY_DISCREPANCY",
                "macro_theme_id": "",
                "macro_theme_name": it["object_id"],
                "theme_cycles": "",
                "campaigns": "",
                "research_candidates": "",
                "years_covered": "",
                "lifecycle_stages_present": "",
                "lifecycle_stages_total": "",
                "evidence_total": "",
                "event_total": "",
                "securities": "",
                "status": "resolved=%s|direct=%s" % ("+".join(it["resolved_macro"]) or "—", "+".join(it["direct_macro"]) or "—"),
            }
        )
    for x in art["lifecycle_completeness"]:
        w.writerow(
            {
                "section": "LIFECYCLE",
                "macro_theme_id": x["object_id"],
                "macro_theme_name": "+".join(x["macro_themes"]),
                "theme_cycles": "",
                "campaigns": "",
                "research_candidates": "",
                "years_covered": x["year"],
                "lifecycle_stages_present": x["stage_count"],
                "lifecycle_stages_total": len(LC_STAGES),
                "evidence_total": "",
                "event_total": "",
                "securities": "",
                "status": x["rating"],
            }
        )
    return "\ufeff" + buf.getvalue()


# ---------------------------------------------------------------- main


def main(argv):
    check_only = "--check" in argv
    do_print = "--print" in argv

    # `--round X` 恢复该轮的产物路径与口径（默认 0.1，保持既有行为）
    round_id = DEFAULT_ROUND
    if "--round" in argv:
        i = argv.index("--round")
        if i + 1 >= len(argv):
            raise SystemExit("--round 需要一个参数，例如 --round 0.2")
        round_id = argv[i + 1]
    prof = apply_round(round_id)

    art = build_artifact()
    issues = validate(art)
    if issues:
        print("FAIL —— 自检未通过，不写文件：")
        for i in issues[:40]:
            print("  -", i)
        return 1

    text = json.dumps(art, ensure_ascii=False, indent=2) + "\n"
    csv_text = write_csv(art)

    if check_only:
        ok = True
        for path, expected in ((OUT_JSON, text), (OUT_CSV, csv_text)):
            if not os.path.exists(path):
                print("FAIL —— 磁盘上不存在产物：", os.path.relpath(path, ROOT))
                ok = False
                continue
            with io.open(path, "r", encoding="utf-8", newline="") as f:
                if f.read() != expected:
                    print("FAIL —— 与重算结果不一致：", os.path.relpath(path, ROOT))
                    ok = False
        if ok:
            print("PASS —— 磁盘产物与重算结果逐字节一致（deterministic，round=%s）。" % round_id)
            return 0
        return 1

    with io.open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    with io.open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        f.write(csv_text)

    print("written (round=%s): %s" % (round_id, prof["label"]))
    print("  ", os.path.relpath(OUT_JSON, ROOT))
    print("  ", os.path.relpath(OUT_CSV, ROOT))

    if do_print:
        _print_summary(art)
    return 0


def _print_summary(art):
    inv = art["dataset_inventory"]
    print("=" * 78)
    print("Historical Coverage Audit v%s（round %s）" % (ARTIFACT_VERSION, art.get("research_round", "")))
    print("=" * 78)
    print("Dataset")
    print("  Campaigns          :", inv["db_row_counts"]["campaigns"], "(DB) /", inv["export_counts"]["campaigns"], "(export)")
    print("  Research Candidates:", inv["export_counts"]["research_candidates"])
    print("  Theme Cycles       :", sum(m.get("theme_cycles", 0) for m in art["macro_theme_matrix"]))
    print("  Macro Themes       :", art["taxonomy_integrity"]["macro_theme_count_history"])
    print("  Themes (all)       :", inv["db_row_counts"]["themes"], "| orphans:", art["taxonomy_integrity"]["orphan_theme_count"])
    print("  Lifecycle records  :", inv["db_row_counts"]["campaign_phases"], "(DB phases)")
    print("  Evidences          :", inv["db_row_counts"]["evidences"])
    print("  Events             :", inv["db_row_counts"]["events"], "(DB) /", inv["export_counts"]["events"], "(export)")
    print("  Years              :", [y["year"] for y in inv["campaign_years"]])
    print("  Verified dates     :", art["verification_coverage"]["verified_count"], "/",
          art["verification_coverage"]["total_date_observations"])
    print("  Lifecycle rating   : COMPLETE %d / PARTIAL %d / SPARSE %d / UNKNOWN %d"
          % (
              sum(1 for x in art["lifecycle_completeness"] if x["rating"] == "COMPLETE"),
              sum(1 for x in art["lifecycle_completeness"] if x["rating"] == "PARTIAL"),
              sum(1 for x in art["lifecycle_completeness"] if x["rating"] == "SPARSE"),
              sum(1 for x in art["lifecycle_completeness"] if x["rating"] == "UNKNOWN"),
          ))
    print("-" * 78)
    print("Macro Theme Coverage")
    for m in art["macro_theme_matrix"]:
        print("  %-10s %-8s cycles=%-3s campaigns=%-3s rc=%-3s years=%-22s lifecycle=%s/%s ev=%s status=%s"
              % (m["macro_theme_id"], m["macro_theme_name"], m.get("theme_cycles", 0), m.get("campaigns", 0),
                 m.get("research_candidates", 0), str(m.get("years_covered") or []),
                 m.get("lifecycle_stages_present", 0), len(LC_STAGES),
                 (m.get("evidence_coverage") or {}).get("total", 0), m.get("status")))
    print("-" * 78)
    print("Coverage Ceiling")
    print("  theme_family_count =", art["coverage_ceiling"]["theme_family_count_ceiling"])
    print("  declared by Current Candidates:", art["taxonomy_integrity"]["macro_themes_declared_by_current_candidates"])
    print("  declared but NO history      :", art["taxonomy_integrity"]["declared_but_no_history"])
    print("-" * 78)
    print("Research Capability Matrix")
    for c in art["research_capability_matrix"]:
        print("  %-22s %-9s %s" % (c["capability"], c["status"], c["blocker"][:56]))
    print("-" * 78)
    print("Event Coverage — NOT_AVAILABLE")
    for c in art["event_coverage"]["capability_coverage"]:
        if c["status"] != "AVAILABLE":
            print("  %-16s %-18s schema_allows=%s" % (c["capability_key"], c["status"], c["schema_allows"]))
    print("-" * 78)
    print("Priority (data build, NOT investment ranking)")
    for p in art["priority_framework"]:
        print("  %-16s %d/%d  declared=%s" % (p["domain"], p["total_score"], p["max_score"],
                                              ",".join(p["already_declared_by_current_candidates"]) or "—"))
    print("=" * 78)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
