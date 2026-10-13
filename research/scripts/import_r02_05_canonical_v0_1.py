#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R02-05 canonicalization v0.1 —— 把 3 条 ACCEPT_WITH_CHANGES 候选写入 canonical。

★ 权限：**只有 ThreeC Agent 有 canonicalization 权限**（协议 §3.2）。
★ 本脚本**不改** schema.sql / 不改 intake 包 / 不覆盖任何既有对象。

## 写入范围（用户 2026-10-13 授权）

| canonical_id | 来源候选 | 方向 | start → peak → end |
|---|---|---|---|
| `C-2017-COMM-5G-SPECTRUM` | R02-COMM-001 | 信息通信 | 2017-08-31 → 2017-11-21 → 2018-02-09 |
| `C-2021-MEDIA-METAVERSE` | R02-MEDIA2-001 | 文化传媒 | 2021-09-06 → 2022-01-05 → 2022-01-28 |
| `C-2023-POWEROP-THERMAL` | R02-POWEROP-001 | 电力（运营端） | 2023-01-03 → 2023-05-29 → 2023-10-23 |

## ★ 审查裁定（`research/intake/reviews/R02-05_verdicts_v0_1.json`）的落实

- **D2 修正**：`COMM-001` 的超额改用**统一区间** —— +21.76pp（vs 中证全指）· +14.53pp（vs 沪深300）
- **D3 修正**：`POWEROP-001` 涉及的 `+22.61%` → **`+22.59%`**（实测 +22.5862%）
- **D4 说明**：`MEDIA2-001` 的 evidence 区间起点 08-20 ≠ lifecycle 起点 09-06（须写明）
- **E005 标注**：`+11.36%` 为**媒体口径**（一手复算 +9.02%），不得与一手数字混用
- **粒度裁定**：`docs/DECISION_CAMPAIGN_GRANULARITY_2026-10-13.md` ——
  在 `research_notes` 中标注**所属长周期对象**

## ★ 新增 taxonomy 行（1 条，已在决策文档中显式记录）

`TH-POWER-OP-THERMAL` = `火电 / 煤电`（concept，parent = TH-POWER-OP）
—— 与既有 `TH-POWER-OP-GREEN`（绿电 / 新能源运营商）**同层级对称**；**有对象挂靠**，非造空行。

## ★ slug 说明（避免 id 冲突）

包内 slug → 本脚本 slug：`COMM → COMM3` · `MEDIA2 → MEDIA3` · `POWEROP → POWEROP2`
（因 `S-COMM-*` / `S-MEDIA2-*` 已被 R01 / R02-04 占用）
"""
import argparse
import io
import json
import os
import re
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DB_PATH = os.path.join(ROOT, "research", "database", "cycle_research.db")
PKG = os.path.join(ROOT, "research", "intake", "packages", "R02-05")


def rd(p):
    return json.load(io.open(os.path.join(PKG, p), encoding="utf-8"))


# ---------------------------------------------------------------- id 重映射
SLUG = {"COMM": "COMM3", "MEDIA2": "MEDIA3", "POWEROP": "POWEROP2"}


def ren(xid):
    """R02-COMM-E001 → E-COMM3-01 ；R02-POWEROP-S002 → S-POWEROP2-02"""
    m = re.match(r"R02-([A-Z0-9]+)-([SE])(\d+)$", xid)
    if not m:
        return xid
    raw, kind, num = m.groups()
    return "%s-%s-%s" % (kind, SLUG.get(raw, raw), num)


def cid_of(intake_id):
    return {"R02-COMM-001": "C-2017-COMM-5G-SPECTRUM",
            "R02-MEDIA2-001": "C-2021-MEDIA-METAVERSE",
            "R02-POWEROP-001": "C-2023-POWEROP-THERMAL"}[intake_id]


# ---------------------------------------------------------------- 静态声明
INTAKE_MAP = [
    ("C-2017-COMM-5G-SPECTRUM", "R02-COMM-001"),
    ("C-2021-MEDIA-METAVERSE", "R02-MEDIA2-001"),
    ("C-2023-POWEROP-THERMAL", "R02-POWEROP-001"),
]

NEW_THEMES = [
    {"theme_id": "TH-POWER-OP-THERMAL", "name": "火电 / 煤电", "theme_type": "concept",
     "parent_theme_id": "TH-POWER-OP",
     "description": "电力（运营端）下的**火电 / 煤电**机制。与 `TH-POWER-OP-GREEN`"
                    "（绿电 / 新能源运营商）同层级对称。★ R02-05 canonicalization 新建"
                    "（2026-10-13）—— 承载 `C-2023-POWEROP-THERMAL` 的机制表达。"},
]

# 0 新 rule（rule_infocomm / rule_media / rule_power_operation 均复用）
NEW_RULES = []

NEW_ANNUAL = [
    {"annual_review_id": "AR-COMM-2017", "rule_id": "rule_infocomm", "year": 2017,
     "status": "medium",
     "summary": "2017 年信息通信出现「5G 标准与频谱预期」驱动的行情："
                "中证5G通信主题指数（931079）自 2017-08-31 收 907.46 上行至 2017-11-21 收 1133.22"
                "（+24.88%），2017-11-15 工信部发布 5G 中频段频率使用规划后见顶，"
                "其后回落至 2018-02-09（自峰值 -27.14%）。",
     "review_notes": "★ 超额（**统一区间** 2017-08-31→2017-11-21 实测）："
                     "931079 +24.88% vs 中证全指 +3.12% → **+21.76pp**；"
                     "vs 沪深300 +10.35% → **+14.53pp**。"
                     "（R02-05 canonicalization 落实审查 D2 修正 · 2026-10-13）"},
    {"annual_review_id": "AR-MEDIA-2021", "rule_id": "rule_media", "year": 2021,
     "status": "medium",
     "summary": "2021 年文化传媒出现「元宇宙」概念驱动的行情：中证动漫游戏指数（930901）"
                "自 2021-08-20 收 1255.89（区间最低收盘）上行至 2022-01-05 收 1802.38（+43.51%），"
                "2022-01 起回调。机制为**概念情绪驱动**。",
     "review_notes": "★ 峰值跨年至 2022-01（`campaign_year` 取 start 年份 2021，与全库约定一致）。"
                     "★ 机制为情绪面，可解释强度弱于政策/业绩驱动。"
                     "★ 窗口**未经核验**。"
                     "（R02-05 canonicalization · 2026-10-13）"},
    {"annual_review_id": "AR-PWROP-2023", "rule_id": "rule_power_operation", "year": 2023,
     "status": "medium",
     "summary": "2023 年电力（运营端）出现「煤价下行 + 迎峰度夏」驱动的**火电**行情："
                "中证全指公用事业指数（000995）自 2023-01-03 收 2329.82 上行至 2023-05-29 收 2584.43"
                "（+10.93%），其后回落至 2023-10-23。同期沪深300 -1.39%。",
     "review_notes": "★ 相对强度中等（超额约 +12.32pp vs 沪深300）—— 如实保留该限定。"
                     "★ 季节性主张（「夏炒电」）**未被独立核验**，不得据此建立 `confirmed` 状态的规则。"
                     "★ 与 `C-2021-POWER-GREEN`（开放式）的边界：**标的与机制双重不重叠**"
                     "（火电 vs 绿电运营）→ 独立成立。"
                     "（R02-05 canonicalization · 2026-10-13）"},
]

# 复用既有标的（不新建）；★ 中兴通讯 已在库（ZTE / 000063）
SEC_REUSE = {"ZTE": ("000063", "中兴通讯", "SZ")}
# 新建标的：**ticker 一律留空**（包未取得代码来源 → 不得凭常识补）
SEC_NEW = {
    "WUHANFANGU": (None, "武汉凡谷", None),
    "ZHONGQINGBAO": (None, "中青宝", None),
    "HUADIAN": (None, "华电国际", None),
    "JIANTONENERGY": (None, "建投能源", None),
    "TIANFUENERGY": (None, "天富能源", None),
}

# ---------------------------------------------------------------- 三条 Campaign 规格
SPECS = [
    {
        "intake_id": "R02-COMM-001",
        "campaign_id": "C-2017-COMM-5G-SPECTRUM",
        "annual_review_id": "AR-COMM-2017", "rule_id": "rule_infocomm",
        "season_id": "comm_5g_spectrum_2017", "campaign_year": 2017,
        "start_date": "2017-08-31", "peak_date": "2017-11-21", "end_date": "2018-02-09",
        "strength": "medium", "result": "positive", "classification": "theme_campaign",
        "date_confidence": "medium",
        "start_date_basis": ("`date_candidates.start` 为**日期窗口**（2017-08-31 ~ 2017-09-29）"
                             "→ canonical 取**窗口起点** 2017-08-31。★ 本包**不**声称更精确的起涨日。"
                             "依据：931079 自 2017-08-31 收 907.46 上行；同期媒体记载 5G 概念股涨停潮。"),
        "end_date_basis": ("峰值 2017-11-21（931079 收盘 1133.22，经一手复算为该段最高收盘）后回落至"
                           " 2018-02-09 收 825.64（自峰值 -27.14%）。"),
        "description": "2017 年 5G 主题「标准与频谱预期」驱动的通信板块行情（信息通信 · 机制段）。",
        "research_notes": (
            "★★ **机制段**：本对象为机制段（用户 2026-10-13 裁定粒度）。"
            "同族**长周期**对象 = `C-2019-COMM-5G`（2019-06-06 → 2022-10-11）—— "
            "本段在其**之前**（不重叠）。\n"
            "★ **超额口径（审查 D2 修正）**：统一区间 2017-08-31→2017-11-21 实测 —— "
            "931079 +24.88% vs 中证全指 **+3.12%** → 超额 **+21.76pp**；"
            "vs 沪深300 **+10.35%** → 超额 **+14.53pp**。"
            "（包原用**不同区间**相减得出 +12pp / +4.3pp —— 属**自我低估**，已按审查修正。）\n"
            "★ **驱动源**：5G 国际标准制定进入第一版基础版本关键期 + 国内频谱规划预期"
            "（2017-11-15 工信部 5G 中频段频率使用规划，Tier 1 一手）。\n"
            "★ 与 `C-2019-COMM-5G` **共享标的**中兴通讯 —— 同族共享，**不构成重复**。\n"
            "★ **K 线证实**：参照物 = **板块指数**（非股价）→ 按 `AGENTS.md` §5.1 "
            "**不得**因「指数创高」记 `CONFIRMED`。\n"
            "★ securities 的 ticker：武汉凡谷**留空待核**（包未取得代码来源，不凭常识补）。"
        ),
        "themes": [("TH-COMM", "related"), ("TH-COMM-5G", "main")],
        "securities": [("ZTE", "leader"), ("WUHANFANGU", "representative")],
        "phases": [
            ("PH-COMM3-01", "main_rise", "2017-08-31", "2017-11-21",
             "上行段：931079 自 907.46 至 1133.22（+24.88%，统一区间口径）。"),
            ("PH-COMM3-02", "retracement", "2017-11-21", "2018-02-09",
             "回落段：至 825.64（自峰值 -27.14%）。"),
        ],
        "obs": [("start", "2017-08-31", "2017-08-31", "market_data", "medium",
                 "窗口起点（非精确起涨日）；931079 经一手复算为该段最低收盘。"),
                ("peak", "2017-11-21", "2017-11-21", "market_data", "medium",
                 "931079 收盘高点，经一手复算确为该段最高收盘。★ 参照物 = 板块指数。"),
                ("end", "2018-02-09", "2018-02-09", "market_data", "medium",
                 "回落低点；931079 收 825.64。")],
    },
    {
        "intake_id": "R02-MEDIA2-001",
        "campaign_id": "C-2021-MEDIA-METAVERSE",
        "annual_review_id": "AR-MEDIA-2021", "rule_id": "rule_media",
        "season_id": "media_metaverse_2021", "campaign_year": 2021,
        "start_date": "2021-09-06", "peak_date": "2022-01-05", "end_date": "2022-01-28",
        "strength": "medium", "result": "positive", "classification": "event_driven",
        "date_confidence": "medium",
        "start_date_basis": ("★ 取 **lifecycle `MAIN_RISE.start` = 2021-09-06**"
                             "（2021-09-06 中青宝宣布推出元宇宙游戏《酿酒大师》）。"
                             "★★ **审查 D4 说明**：evidence 的**行情区间**起点为 2021-08-20"
                             "（该日收 1255.89，经一手复算为该区间最低收盘）—— "
                             "**二者相差 11 个交易日**，非同一概念：行情区间起点 ≠ 生命周期起点。"),
        "end_date_basis": ("峰值 2022-01-05（930901 收盘 1802.38，经复算为该区间最高收盘）后"
                           "回调至 2022-01-28。"),
        "description": "2021 年「元宇宙」概念驱动的传媒 / 游戏板块行情（文化传媒 · 机制段）。",
        "research_notes": (
            "★★ **机制段**：本对象为机制段（用户 2026-10-13 裁定粒度）。"
            "同族对象 = `C-2018-MEDIA-GAMELICENSE`（2018–2019 版号周期）与 "
            "`C-2023-MEDIA-AI`（2023 AI + 内容）—— 三者**机制各不同**（监管周期 / 概念情绪 / 技术主题），"
            "时间亦不重叠。\n"
            "★ **峰值跨年**：peak = 2022-01-05，落在 `campaign_year=2021` 之外。"
            "按全库约定（58/58），`campaign_year` 取 **start 年份**（先例 `C-2022-CONS-SERVICE-REBOUND`）。\n"
            "★ **机制为概念情绪驱动**（卖方研究自身记为「情绪面催化」）—— "
            "可解释强度**弱于**政策或业绩驱动，如实保留该限定。\n"
            "★ **K 线证实**：参照物 = **板块指数**（930901 收盘高点 2022-01-05）→ 按 §5.1 "
            "**不得**因「指数创高」记 `CONFIRMED`。\n"
            "★ securities 的 ticker：中青宝**留空待核**（包未取得代码来源）。"
        ),
        "themes": [("TH-MEDIA", "main")],
        "securities": [("ZHONGQINGBAO", "leader")],
        "phases": [
            ("PH-MEDIA3-01", "main_rise", "2021-09-06", "2022-01-05",
             "上行段：930901 自 2021-08-20 收 1255.89 至 2022-01-05 收 1802.38（+43.51%）。"),
            ("PH-MEDIA3-02", "retracement", "2022-01-05", "2022-01-28",
             "回调段（元宇宙概念龙头带头回调）。"),
        ],
        "obs": [("start", "2021-09-06", "2021-09-06", "manual", "medium",
                 "生命周期起点 = 中青宝公告日。★ evidence 行情区间起点为 2021-08-20（相差 11 个交易日）。"),
                ("peak", "2022-01-05", "2022-01-05", "market_data", "medium",
                 "930901 收盘高点，经复算为该区间最高收盘。★ 参照物 = 板块指数。"),
                ("end", "2022-01-28", "2022-01-28", "market_data", "medium",
                 "回调低点。")],
    },
    {
        "intake_id": "R02-POWEROP-001",
        "campaign_id": "C-2023-POWEROP-THERMAL",
        "annual_review_id": "AR-PWROP-2023", "rule_id": "rule_power_operation",
        "season_id": "powerop_thermal_2023", "campaign_year": 2023,
        "start_date": "2023-01-03", "peak_date": "2023-05-29", "end_date": "2023-10-23",
        "strength": "medium", "result": "positive", "classification": "mixed",
        "date_confidence": "medium",
        "start_date_basis": ("2023 年首个交易日 2023-01-03（000995 收 2329.82）。"
                             "★ 该日非年内最低收盘（年内最低为 2023-01-19 收 2286.47）—— 如实记录。"),
        "end_date_basis": ("峰值 2023-05-29（000995 收 2584.43，经一手复算为 2023 年内最高收盘）后"
                           "回落，至 2023-10-23。"),
        "description": "2023 年煤价下行与迎峰度夏驱动的火电 / 电力运营行情（电力（运营端）· 机制段）。",
        "research_notes": (
            "★★ **机制段**：本对象为机制段（用户 2026-10-13 裁定粒度）。"
            "同族**长周期**对象 = `C-2021-POWER-GREEN`（2021-09-07 → **OPEN**，开放式）—— "
            "★ 时间范围重叠**属既有对象的表达方式**（开放式），**不构成重复**："
            "本段标的为**火电**（华电国际 / 建投能源 / 天富能源），"
            "既有为**绿电运营**（京能电力 / 三峡能源 / 银星能源）—— **标的与机制双重不重叠**。\n"
            "★ **相对强度中等**：超额约 +12.32pp（vs 沪深300）—— 显著弱于本批其他候选（如 2021 光伏 +93pp），"
            "如实保留。\n"
            "★ **季节性主张未被独立核验**：「夏炒电」为来源观点，本对象**未**取得跨年份可复现的年内窗口证据 "
            "→ **不得**据此建立 `confirmed` 状态的规则。\n"
            "★ **D3 修正**：涉及 2019 年对照的 `+22.61%` → **`+22.59%`**（一手复算 +22.5862%）。\n"
            "★ **媒体口径标注**：`+11.36%`（2023-01-01→05-31，H30199）为**媒体口径**"
            "（澎湃新闻原文；一手复算为 +9.02%）→ **不得**与一手数字混用。\n"
            "★ **K 线证实**：参照物 = **板块指数**（000995 收盘高点 2023-05-29）→ 按 §5.1 "
            "**不得**因「指数创高」记 `CONFIRMED`。\n"
            "★ securities 的 ticker：三只**全部留空待核**（包未取得代码来源）。"
        ),
        "themes": [("TH-POWER-OP", "related"), ("TH-POWER-OP-THERMAL", "main")],
        "securities": [("HUADIAN", "leader"), ("JIANTONENERGY", "representative"),
                       ("TIANFUENERGY", "follow")],
        "phases": [
            ("PH-POWEROP2-01", "main_rise", "2023-01-03", "2023-05-29",
             "上行段：000995 自 2329.82 至 2584.43（+10.93%）。"),
            ("PH-POWEROP2-02", "decline", "2023-05-29", "2023-10-23",
             "回落段（包原记为 DECLINING）。"),
        ],
        "obs": [("start", "2023-01-03", "2023-01-03", "market_data", "medium",
                 "2023 年首个交易日。★ 非年内最低收盘（01-19 更低）。"),
                ("peak", "2023-05-29", "2023-05-29", "market_data", "medium",
                 "000995 收盘高点，经一手复算为 2023 年内最高收盘。★ 参照物 = 板块指数。"),
                ("end", "2023-10-23", "2023-10-23", "market_data", "low",
                 "回落段终点（DECLINING 段结束）。")],
    },
]


# ---------------------------------------------------------------- 构建计划
def build_plan():
    srcs = {s["source_id"]: s for s in rd("sources.json")}
    evs = {e["evidence_id"]: e for e in rd("evidence.json")}

    plan = {"themes": list(NEW_THEMES), "rules": list(NEW_RULES), "annual": list(NEW_ANNUAL),
            "sources": [], "evidences": [], "securities": [], "campaigns": [],
            "campaign_themes": [], "campaign_evidences": [], "campaign_securities": [],
            "campaign_phases": [], "date_obs": []}

    used_src, used_ev = set(), set()

    for spec in SPECS:
        cid = spec["campaign_id"]
        cand = next(c for c in rd("candidates.json")
                    if c["candidate_id"] == spec["intake_id"])

        plan["campaigns"].append({
            "campaign_id": cid, "annual_review_id": spec["annual_review_id"],
            "rule_id": spec["rule_id"], "season_id": spec["season_id"],
            "campaign_year": spec["campaign_year"], "start_date": spec["start_date"],
            "end_date": spec["end_date"], "peak_date": spec["peak_date"],
            "strength": spec["strength"], "result": spec["result"],
            "classification": spec["classification"],
            "start_date_basis": spec["start_date_basis"],
            "end_date_basis": spec["end_date_basis"],
            "date_confidence": spec["date_confidence"],
            "description": spec["description"], "research_notes": spec["research_notes"],
        })
        for tid, role in spec["themes"]:
            plan["campaign_themes"].append((cid, tid, role))
        for sid, role in spec["securities"]:
            plan["campaign_securities"].append((cid, sid, role))
        for row in spec["phases"]:
            plan["campaign_phases"].append({
                "phase_id": row[0], "campaign_id": cid, "phase_type": row[1],
                "start_date": row[2], "end_date": row[3], "description": row[4]})
        for role, cd, vd, vm, conf, note in spec["obs"]:
            plan["date_obs"].append({
                "observation_id": "OBS-%s-%s" % (cid, role), "campaign_id": cid,
                "date_role": role, "candidate_date": cd, "verified_date": vd,
                "verification_method": vm, "confidence": conf, "evidence_id": None,
                "notes": note})

        # evidences（★ support_kind / point_in_time_note 追加进 description ——
        #   DB `evidences` 表**没有**这两列，不追加会在 canonical 层丢失 PIT 声明）
        for eid in cand.get("evidence_ids") or []:
            if eid in used_ev:
                continue
            used_ev.add(eid)
            e = evs[eid]
            sid = e["source_id"]
            used_src.add(sid)
            desc = e.get("description") or ""
            sk = e.get("support_kind") or []
            pit = e.get("point_in_time_note")
            extra = []
            if sk:
                extra.append("support_kind=%s" % ",".join(sk))
            if pit:
                extra.append("point_in_time_note=%s" % pit)
            if extra:
                desc = (desc + " ｜ ★ " + " ｜ ".join(extra)).strip()
            plan["evidences"].append({
                "evidence_id": ren(eid), "source_id": ren(sid),
                "date": e.get("event_date"), "evidence_type": e.get("evidence_type"),
                "description": desc or (e.get("claim") or ""),
                "evidence_role": e.get("evidence_role") or "supporting",
                "confidence": e.get("confidence") or "medium",
                "independence_group": e.get("independence_group"),
                "temporal_relation": e.get("temporal_relation")})
            plan["campaign_evidences"].append(
                (cid, ren(eid), e.get("evidence_role") or "supporting"))

    for sid in sorted(used_src):
        s = srcs[sid]
        plan["sources"].append({
            "source_id": ren(sid), "source_type": s.get("source_type") or "website",
            "title": s.get("title") or "", "author": s.get("author"),
            "url": s.get("url"), "published_at": s.get("published_at") or s.get("date"),
            "captured_at": s.get("captured_at") or s.get("accessed_at"),
            "publisher": s.get("publisher"), "description": s.get("description"),
            "tier": s.get("tier")})

    for sid, (tk, nm, ex) in SEC_NEW.items():
        plan["securities"].append({"security_id": sid, "ticker": tk, "name": nm, "exchange": ex})

    return plan


# ---------------------------------------------------------------- main
def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args(argv)

    plan = build_plan()

    print("R02-05 canonicalization v0.1")
    print("-" * 62)
    for k in ("themes", "rules", "annual", "sources", "evidences", "securities",
              "campaigns", "campaign_themes", "campaign_evidences",
              "campaign_securities", "campaign_phases", "date_obs"):
        print("  %-20s %d" % (k, len(plan[k])))
    print()
    for r in plan["campaigns"]:
        print("  %-28s %s → %s → %s  [%s/%s]" % (
            r["campaign_id"], r["start_date"], r["peak_date"], r["end_date"],
            r["strength"], r["classification"]))
    print()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    problems = []
    # (plan 键, 表名, 主键列) —— ★ plan 键与表名不必相同（如 rules → research_rules）
    for pkey, tbl, key in (("themes", "themes", "theme_id"),
                           ("rules", "research_rules", "rule_id"),
                           ("annual", "annual_reviews", "annual_review_id"),
                           ("sources", "sources", "source_id"),
                           ("evidences", "evidences", "evidence_id"),
                           ("securities", "securities", "security_id"),
                           ("campaigns", "campaigns", "campaign_id"),
                           ("campaign_phases", "campaign_phases", "phase_id"),
                           ("date_obs", "campaign_date_observations", "observation_id")):
        for r in plan[pkey]:
            v = r[key]
            cur.execute("SELECT 1 FROM %s WHERE %s = ?" % (tbl, key), (v,))
            if cur.fetchone():
                problems.append("%s.%s 已存在：%s" % (tbl, key, v))
    # 复用的标的必须已存在
    for sid in SEC_REUSE:
        cur.execute("SELECT 1 FROM securities WHERE security_id = ?", (sid,))
        if not cur.fetchone():
            problems.append("复用的标的不存在：%s" % sid)

    if problems:
        print("!! 冲突检查失败：")
        for p in problems:
            print("   - %s" % p)
        return 1
    print("冲突检查：PASS（新 ID 均不存在；复用标的均存在）")

    if args.verify or args.dry_run:
        print()
        print("--dry-run：未写入任何内容。" if args.dry_run else "")
        return 0

    try:
        for r in plan["themes"]:
            cur.execute("INSERT INTO themes (theme_id,name,theme_type,parent_theme_id,description)"
                        " VALUES (?,?,?,?,?)", (r["theme_id"], r["name"], r["theme_type"],
                                                r["parent_theme_id"], r["description"]))
        for r in plan["annual"]:
            cur.execute("INSERT INTO annual_reviews (annual_review_id,rule_id,year,status,summary,review_notes)"
                        " VALUES (?,?,?,?,?,?)", (r["annual_review_id"], r["rule_id"], r["year"],
                                                  r["status"], r["summary"], r["review_notes"]))
        for r in plan["sources"]:
            cur.execute("INSERT INTO sources (source_id,source_type,title,author,url,published_at,"
                        "captured_at,publisher,description,tier) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (r["source_id"], r["source_type"], r["title"], r["author"], r["url"],
                         r["published_at"], r["captured_at"], r["publisher"], r["description"], r["tier"]))
        for r in plan["evidences"]:
            cur.execute("INSERT INTO evidences (evidence_id,source_id,date,evidence_type,description,"
                        "evidence_role,confidence,independence_group,temporal_relation)"
                        " VALUES (?,?,?,?,?,?,?,?,?)",
                        (r["evidence_id"], r["source_id"], r["date"], r["evidence_type"],
                         r["description"], r["evidence_role"], r["confidence"],
                         r["independence_group"], r["temporal_relation"]))
        for r in plan["securities"]:
            cur.execute("INSERT INTO securities (security_id,ticker,name,exchange) VALUES (?,?,?,?)",
                        (r["security_id"], r["ticker"], r["name"], r["exchange"]))
        for r in plan["campaigns"]:
            cur.execute("INSERT INTO campaigns (campaign_id,annual_review_id,rule_id,season_id,"
                        "campaign_year,start_date,end_date,peak_date,strength,result,classification,"
                        "start_date_basis,end_date_basis,date_confidence,description,research_notes)"
                        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (r["campaign_id"], r["annual_review_id"], r["rule_id"], r["season_id"],
                         r["campaign_year"], r["start_date"], r["end_date"], r["peak_date"],
                         r["strength"], r["result"], r["classification"], r["start_date_basis"],
                         r["end_date_basis"], r["date_confidence"], r["description"], r["research_notes"]))
        for cid, tid, role in plan["campaign_themes"]:
            cur.execute("INSERT INTO campaign_themes (campaign_id,theme_id,role) VALUES (?,?,?)",
                        (cid, tid, role))
        for cid, eid, role in plan["campaign_evidences"]:
            cur.execute("INSERT INTO campaign_evidences (campaign_id,evidence_id,role) VALUES (?,?,?)",
                        (cid, eid, role))
        for cid, sid, role in plan["campaign_securities"]:
            cur.execute("INSERT INTO campaign_securities (campaign_id,security_id,role) VALUES (?,?,?)",
                        (cid, sid, role))
        for r in plan["campaign_phases"]:
            cur.execute("INSERT INTO campaign_phases (phase_id,campaign_id,phase_type,start_date,"
                        "end_date,description) VALUES (?,?,?,?,?,?)",
                        (r["phase_id"], r["campaign_id"], r["phase_type"], r["start_date"],
                         r["end_date"], r["description"]))
        for r in plan["date_obs"]:
            cur.execute("INSERT INTO campaign_date_observations (observation_id,campaign_id,date_role,"
                        "candidate_date,verified_date,verification_method,confidence,evidence_id,notes)"
                        " VALUES (?,?,?,?,?,?,?,?,?)",
                        (r["observation_id"], r["campaign_id"], r["date_role"], r["candidate_date"],
                         r["verified_date"], r["verification_method"], r["confidence"],
                         r["evidence_id"], r["notes"]))
        conn.commit()
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        print()
        print("!! 写入失败，已 ROLLBACK：%s" % exc)
        return 1

    print()
    print("✓ 单事务提交完成")
    cur.execute("SELECT COUNT(*) FROM campaigns")
    print("  campaigns 总数 = %d（原 59）" % cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM themes")
    print("  themes 总数    = %d（原 58）" % cur.fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
