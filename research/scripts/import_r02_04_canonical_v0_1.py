#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""import_r02_04_canonical_v0_1.py —— R02-04 → canonical 导入（2 条 DEFER 补做候选）。

## 它做什么

把 R02-04 包的 2 条候选写进 canonical DB。**只有 ThreeC Agent 有该权限**（协议 §3.2）。

| canonical_id | 来源候选 | start → peak → end |
|---|---|---|
| `C-2023-RES-COAL-DIVIDEND` | `R02-COAL-002` | 2023-08-21 → 2024-05-29 → 2024-09-11 |
| `C-2018-MEDIA-GAMELICENSE` | `R02-MEDIA-002` | 2018-12-21 → 2019-03-12 → 2019-08-09 |

## ★★ 命名约定（2026-10-12 实测确定，第一次写错已修正）

实测全库 **58/58** 既有对象的 `campaign_id` 前缀年份 == `campaign_year` == **`start_date` 的年份**
（不是 peak 年份）。先例：`C-2022-CONS-SERVICE-REBOUND` —— start `2022-12-07`、peak `2023-01-31`，
但 id 年份与 `campaign_year` 都取 **2022**，年度综述为 `AR-CONS-2022`。

→ 故 MEDIA-002（start 2018-12-21）取 **2018**：`C-2018-MEDIA-GAMELICENSE` + `AR-MEDIA-2018`。
★ 我第一次写成 `C-2019-…` + `AR-MEDIA-2019`，导致 `(rule_media, 2018)` **无对应年度综述** →
`batch_auto_research` 在导出装配时抛 `TypeError`（`q1(...)["status"]` 取到 None）。
该不变式已加入 `refresh_downstream.py` 的 **C9** 检查，防止复发。

## ★★ 审查裁定（`docs/R02_04_REVIEW_v0_1.md`）在本文件里的落实

1. **COAL-002 标题区间收窄** —— 包自述「2022–2024 未被指数结构支持为单一段」，
   故只取指数支持的那一段（2023-08-21 → 2024-09-11），**不写 2022 段**。
2. **COAL-002 的 end 口径锁定煤炭指数** —— 包记录了两种基准下结论相反
   （红利口径 → 2025-11-13 仍新高）。按「不代以其他指数」原则，**用煤炭口径**。
3. **MEDIA-002 的 start = 政策转向日，不是行情低点** —— 必须连同
   「此后仍跌至 2019-01-31（-4.40%，相对沪深300 跑输 10.08pp）」一并落库，
   且 lifecycle **保留 DECLINING 段**（不得为让 start 之后即上涨而删）。
4. **MEDIA-002 超额 = 指数减法，非因子分离后的 Alpha** —— 如实降级。
5. **E002 反向证据保留** —— 官方致辞全文不含媒体转述的那句话，按包自带的
   `context` 角色落库，**不降级**。
6. **ticker 留空不凭常识填** —— 完美世界代码未在任何来源出现 → `ticker = NULL`。

## 与 R02-03 导入器的一处实质改进

`campaign_date_observations.verification_method` 在 R02-03 里一律写 `unknown`
（因为其参照物是政策事件）。R02-04 的日期**由指数口径界定并经一手来源复算**
（14/14 命中）→ 该列**如实写 `market_data`**（MEDIA-002 的 start 是媒体转述的政策日 → `manual`）。

## 用法

    python research/scripts/import_r02_04_canonical_v0_1.py --dry-run
    python research/scripts/import_r02_04_canonical_v0_1.py --apply
"""
import argparse
import io
import json
import os
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DB_PATH = os.path.join(ROOT, "research", "database", "cycle_research.db")
PKG = os.path.join(ROOT, "research", "intake", "packages", "R02-04")

sys.path.insert(0, SCRIPT_DIR)


def rd(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


# ================================================================ 规格

# ★ 不新建 taxonomy 行 —— `TH-RES-COAL` / `TH-RES` / `TH-MEDIA` 均已存在（R02-03 已建）
#   包提出的 `游戏` / `高股息 / 红利资产` 等候选名**本轮不建行**：
#   对应候选未成为独立主题，为其建行属「为整齐而造行」。
NEW_THEMES = []

# ★ 不新建规则 —— 复用同族既有规则：
#   COAL-002 → `rule_resources`（资源族）· MEDIA-002 → `rule_media`（文化传媒族，R02-03 建）
#   两条规则的 `status` 维持原值（`under_review` / `candidate`），本导入**不改**。
NEW_RULES = []

# ★★ 标准格式的 canonical → intake 映射（供 `build_lifecycle_from_intake` 提取）。
#    格式必须是 `INTAKE_MAP = [("<canonical>", "<intake_id>")]` —— 该构建器用正则扫本文件。
INTAKE_MAP = [
    ("C-2023-RES-COAL-DIVIDEND", "R02-COAL-002"),
    ("C-2018-MEDIA-GAMELICENSE", "R02-MEDIA-002"),
]

# 新年度综述（各 1 条；rule_resources 无 2023、rule_media 无 2019）
NEW_ANNUAL = [
    {"annual_review_id": "AR-RES-2023", "rule_id": "rule_resources", "year": 2023,
     "status": "medium",
     "summary": "2023 年资源族出现「低利率 + 分红监管强化 + 国企市值管理」驱动的煤炭 / 红利资产"
                "重估段：中证申万煤炭指数 2023-08-21（收 3541.84）→ 2024-05-29（收 5242.93，+48.03%）"
                "→ 2024-09-11（收 3857.16，自高点 -26.43%）。"
                "★ 该段与 2021 年「供需缺口 + 保供稳价」段**机制不同轴**，故为独立对象。",
     "review_notes": "★ 窗口**未经核验**（季节性未取得可复现证据）。"
                     "指数口径来自中证指数有限公司官网公开接口（T1），"
                     "由 ThreeC Agent 于 2026-10-12 独立复算 6/6 命中。"
                     "（R02-04 canonicalization · 2026-10-12）"},
    {"annual_review_id": "AR-MEDIA-2018", "rule_id": "rule_media", "year": 2018,
     "status": "medium",
     "summary": "2018 年文化传媒处于**监管周期**：3 月游戏版号审批暂停（通知原文随机构改革下线，"
                "无官方一手来源），至 12-21 中宣部出版局副局长在游戏产业年会现场表态"
                "「首批游戏已完成审核，正在抓紧核发版号」→ 政策转向；12-29 首批 80 款版号公布。"
                "★ 该政策转向所驱动的行情修复段落在 2019 年（2019-01-31 → 2019-03-12，"
                "中证传媒指数 +46.36%），故本对象 `start_date` = 2018-12-21、"
                "`campaign_year` = 2018（按「id 年份 = campaign_year = start 年份」约定）。",
     "review_notes": "★ 窗口**未经核验**。★ 该窗口恰为 2019 年春季全市场快速反弹"
                     "（沪深300 +17.29%），**超额 = 指数减法、非因子分离后的 Alpha**。"
                     "★ 与 2023 年「AI + 内容」段（`C-2023-MEDIA-AI`）**机制不同**"
                     "（监管周期 vs 技术主题）。"
                     "（R02-04 canonicalization · 2026-10-12）"},
]

# 证券：★ 优先复用既有 canonical 标的（避免重复造）
SEC_REUSE = {
    "R02-COAL2-SEC001": "CHINASHENHUA",     # 中国神华（R02-03 已建）
    "R02-COAL2-SEC002": "SHAANXICOAL",      # 陕西煤业（R02-03 已建）
    "R02-MEDIA2-SEC001": "SANQI",           # 三七互娱（R02-03 已建）
}

# 证券：需要新建的（`ticker` 无来源支撑者**留空**，不凭常识填）
SEC_NEW = {
    "R02-MEDIA2-SEC002": {"security_id": "PERFECTWORLD", "name": "完美世界",
                          "ticker": None, "exchange": None,
                          "note": "★ ticker 留空 —— 代码未在任何来源中出现（包 known_gaps #7）"},
    "R02-MEDIA2-SEC003": {"security_id": "GIANTNET", "name": "巨人网络",
                          "ticker": "002558", "exchange": "SZ",
                          "note": "ticker 有来源支撑（包 securities.json）；exchange 由代码前缀机械映射"},
}

# 2 条 Campaign 的规格
SPECS = [
    {
        "candidate_id": "R02-COAL-002",
        "campaign_id": "C-2023-RES-COAL-DIVIDEND", "slug": "COAL2",
        "annual_review_id": "AR-RES-2023", "rule_id": "rule_resources",
        "season_id": "res_coal_highdiv_2023",
        "start": "2023-08-21", "peak": "2024-05-29", "end": "2024-09-11",
        "strength": "strong", "result": "positive", "classification": "mixed",
        "date_confidence": "high",
        "start_basis": "2023-08-21 = 中证申万煤炭指数（000820）2023 年内最低收盘 3541.84 之日"
                       "（据 R02-COAL2-E001/E002，Tier 1 官方指数机构口径；ThreeC Agent 于 2026-10-12 "
                       "独立复算命中）。★ 取该日为「本段上行」的**行情起点**，属观测事实、非政策事件。"
                       "★★ **本对象不含 2022 年那一段** —— 包自述「2022–2024」未被指数结构支持为"
                       "单一段（2022 段与 2023-08 段机制不同轴），故按审查裁定**只取指数支持的那一段**。",
        "end_basis": "2024-09-11 = 自高点回落至 3857.16（自 2024-05-29 高点 -26.43%）之日"
                     "（据 R02-COAL2-E002）。★★ **口径锁定煤炭指数** —— 包同时记录了红利指数口径"
                     "（000922）下该段至 2025-11-13 仍创新高、OPEN_ENDED；两种基准结论相反。"
                     "按本项目「**不代以其他指数**」的登记原则，主体是煤炭 → **用煤炭口径**。",
        "peak_referent": "板块指数",
        "kline_consequence": "CONFIRMED",
        "peak_note": "参照物 = 板块指数（中证申万煤炭指数 000820 收盘高点 2024-05-29）；"
                     "K 线证实状态 = **CONFIRMED** —— 该日经一手来源复算确为区间最高收盘（5242.93）。"
                     "★ 与 R02-03 的煤炭段（`C-2021-RES-COAL`，参照物=政策事件→NOT_APPLICABLE）**不同**："
                     "本条参照物是股价/指数，故 K 线**是**合适的检验工具。",
        "themes": [("TH-RES-COAL", "main"), ("TH-RES", "related")],
        "phases": [
            ("main_rise", "2023-08-21", "2024-05-29",
             "上行：低利率环境下高股息 / 红利资产相对吸引力上升（中证红利指数 2023-10-23 收 4915.65 为年内最低）"
             "+ 2024-01-24 国务院国资委表态「进一步研究将市值管理纳入中央企业负责人业绩考核」"
             "+ 2024-04-12 国发〔2024〕10 号强化上市公司现金分红监管。"),
            ("retracement", "2024-05-29", "2024-09-11",
             "回撤：自 5242.93 高点回落至 3857.16（-26.43%）。包记录 2024 一季报煤炭板块盈利大幅回落，"
             "研报出现「煤炭高股息是否证伪?」的争论。"),
            ("secondary_rally", "2024-09-11", "2024-12-31",
             "后续段：2024-09-11 之后至年末。★ 包的生命周期提案含此段；"
             "本对象**不据此断言该段性质**，仅如实登记。"),
        ],
        "observations": [
            ("start", "2023-08-21", "market_data", "high", "R02-COAL2-E001", None),
            ("peak", "2024-05-29", "market_data", "high", "R02-COAL2-E002", None),   # notes 自动生成
            ("end", "2024-09-11", "market_data", "high", "R02-COAL2-E002", None),
        ],
    },
    {
        "candidate_id": "R02-MEDIA-002",
        "campaign_id": "C-2018-MEDIA-GAMELICENSE", "slug": "MEDIA2",
        "annual_review_id": "AR-MEDIA-2018", "rule_id": "rule_media",
        "season_id": "media_gamelicense_2018",
        "start": "2018-12-21", "peak": "2019-03-12", "end": "2019-08-09",
        "strength": "medium", "result": "positive", "classification": "event_driven",
        "date_confidence": "medium",
        "start_basis": "2018-12-21 = **政策转向日**：中宣部出版局副局长冯士新在 2018 中国游戏产业年会"
                       "现场表态「首批游戏已完成审核，正在抓紧核发版号」（GameLook T3 与中证网 T2 同期报道，"
                       "据 R02-MEDIA2-E001/E009）。"
                       "★★ **该日不是行情低点** —— 此后指数仍跌至 2019-01-31 的 1072.63（-4.40%，"
                       "相对沪深300 跑输 10.08pp，据 R02-MEDIA2-E005）。此事实**如实保留**，"
                       "未为迁就「政策转向当起点」而隐去。"
                       "★★ **无官方一手发布文本** —— 中国青年网同日发布的致辞**全文不含**该句"
                       "（R02-MEDIA2-E002，反向证据），故口径为「多家媒体同期一致报道，无官方文本」。",
        "end_basis": "2019-08-09 = 中证传媒指数收 1116.74，**低于**修复段起点 2019-01-31 的 1072.63 之上的水平、"
                     "亦低于中证动漫游戏指数同期（收 1471.71，低于 2019-01-31 的 1500.90）；"
                     "即修复段收益回吐完毕（据 R02-MEDIA2-E005/E006）。",
        "peak_referent": "板块指数",
        "kline_consequence": "CONFIRMED",
        "peak_note": "参照物 = 板块指数（中证传媒指数 399971 收盘高点 2019-03-12）；"
                     "K 线证实状态 = **CONFIRMED** —— 该日经一手来源复算确为 2019 年内最高收盘（1569.91）。",
        "themes": [("TH-MEDIA", "main")],
        "phases": [
            ("decline", "2018-12-21", "2019-01-31",
             "★★ **保留此段** —— 政策转向日之后指数仍下跌（-4.40%，相对沪深300 跑输 10.08pp），"
             "反映政策转向**未被市场即时定价**。不得为让 start 之后就是上涨而删除本段。"),
            ("main_rise", "2019-01-31", "2019-03-12",
             "上行：2018-12-29 首批 80 款版号公布（审批日 2018-12-19）、2019-01-09 第二批 84 款，"
             "券商侧形成「政策底」叙事；同期叠加 2019 年春季全市场快速反弹的系统性 Beta。"),
            ("retracement", "2019-03-12", "2019-08-09",
             "回撤：自 1569.91 高点回落，至 2019-08-09 收 1116.74（低于起点附近水平）。"),
        ],
        "observations": [
            ("start", "2018-12-21", "manual", "medium", "R02-MEDIA2-E001",
             "★ 起点 = **政策转向日**（媒体同期报道），**非**行情低点；该日无官方一手发布文本"
             "（R02-MEDIA2-E002 反向证据）。此后仍跌至 2019-01-31。"),
            ("peak", "2019-03-12", "market_data", "high", "R02-MEDIA2-E005", None),   # notes 自动生成
            ("end", "2019-08-09", "market_data", "high", "R02-MEDIA2-E005", None),
        ],
    },
]


def main(argv):
    ap = argparse.ArgumentParser(description="R02-04 → canonical 导入")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--verify", action="store_true")
    args = ap.parse_args(argv)

    cands = {c["candidate_id"]: c for c in rd(os.path.join(PKG, "candidates.json"))}
    evs = {e["evidence_id"]: e for e in rd(os.path.join(PKG, "evidence.json"))}
    srcs = {s["source_id"]: s for s in rd(os.path.join(PKG, "sources.json"))}
    secs = {s["security_id"]: s for s in rd(os.path.join(PKG, "securities.json"))}

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # ---- 组装计划 ----
    plan = {"themes": list(NEW_THEMES), "rules": list(NEW_RULES), "annual": list(NEW_ANNUAL),
            "sources": [], "evidences": [], "securities": [],
            "campaigns": [], "campaign_themes": [], "campaign_evidences": [],
            "campaign_securities": [], "campaign_phases": [], "date_obs": []}
    problems = []

    for spec in SPECS:
        cid = spec["campaign_id"]
        c = cands[spec["candidate_id"]]
        slug = spec["slug"]

        # campaigns
        plan["campaigns"].append({
            "campaign_id": cid, "annual_review_id": spec["annual_review_id"],
            "rule_id": spec["rule_id"], "season_id": spec["season_id"],
            "campaign_year": int(spec["start"][:4]), "start_date": spec["start"],
            "end_date": spec["end"], "peak_date": spec["peak"],
            "strength": spec["strength"], "result": spec["result"],
            "classification": spec["classification"],
            "start_date_basis": spec["start_basis"], "end_date_basis": spec["end_basis"],
            "date_confidence": spec["date_confidence"],
            "description": c.get("theme_summary") or c.get("title"),
            "research_notes": (
                "【R02-04 canonicalization · 2026-10-12】来源候选 %s（R02-03 判 DEFER 后的补做版本；"
                "R02-03 的同名包**未被覆盖**，仍在 research/intake/packages/R02-03/）。\n"
                "★★ **peak 参照物 = %s** —— K 线证实状态 = **%s**。%s\n"
                "审查：docs/R02_04_REVIEW_v0_1.md（裁定 ACCEPT_WITH_CHANGES）· "
                "机读：research/intake/reviews/R02-04_verdicts_v0_1.json。\n"
                "★ 语义核对：包中指数数字经 ThreeC Agent 于 2026-10-12 回一手来源复算 **14/14 精确命中**。"
                % (spec["candidate_id"], spec["peak_referent"], spec["kline_consequence"],
                   spec["peak_note"])
            ),
        })

        for tid, role in spec["themes"]:
            plan["campaign_themes"].append((cid, tid, role))

        # 来源 + 证据
        used_e = c.get("evidence_ids") or []
        used_s = sorted({evs[i]["source_id"] for i in used_e})
        smap = {}
        for n, sid in enumerate(used_s, 1):
            o = srcs[sid]
            new_sid = "S-%s-%02d" % (slug, n)
            smap[sid] = new_sid
            plan["sources"].append({
                "source_id": new_sid, "source_type": o.get("source_type") or "other",
                "title": o.get("title"), "author": o.get("author"),
                "url": o.get("url"), "published_at": o.get("published_at"),
                "captured_at": None, "publisher": o.get("publisher"),
                "description": "【R02-04 导入】来源 intake ID = %s。%s"
                               % (sid, o.get("description") or ""),
                "tier": o.get("tier"),
            })
        emap = {}
        for n, eid in enumerate(used_e, 1):
            e = evs[eid]
            new_eid = "E-%s-%02d" % (slug, n)
            emap[eid] = new_eid
            sk = e.get("support_kind")
            sk = sk if isinstance(sk, list) else ([sk] if sk else [])
            plan["evidences"].append({
                "evidence_id": new_eid, "source_id": smap.get(e.get("source_id")),
                "date": e.get("event_date"), "evidence_type": e.get("evidence_type") or "其他",
                "description": (
                    "%s\n\n【Temporal Firewall（DB 无对应列，追加于此以免丢失）】"
                    "temporal_relation=%s · support_kind=%s · independence_group=%s · "
                    "point_in_time_note=%s · 来源 intake ID=%s"
                    % (e.get("claim"), e.get("temporal_relation"), ",".join(sk),
                       e.get("independence_group"), e.get("point_in_time_note") or "—", eid)
                ),
                "evidence_role": e.get("evidence_role") or "supporting",
                "confidence": e.get("confidence") or "medium",
                "independence_group": e.get("independence_group"),
                "temporal_relation": e.get("temporal_relation"),
            })
            plan["campaign_evidences"].append((cid, new_eid, e.get("evidence_role") or "supporting"))

        # 证券（复用优先）
        for sid in c.get("security_ids") or []:
            o = secs[sid]
            if sid in SEC_REUSE:
                new_id = SEC_REUSE[sid]
            else:
                spec_sec = SEC_NEW[sid]
                new_id = spec_sec["security_id"]
                if not any(x["security_id"] == new_id for x in plan["securities"]):
                    plan["securities"].append({
                        "security_id": new_id, "ticker": spec_sec["ticker"],
                        "name": spec_sec["name"], "exchange": spec_sec["exchange"],
                    })
            plan["campaign_securities"].append((cid, new_id, o.get("role") or "representative"))

        # 阶段
        for n, (pt, s, e, desc) in enumerate(spec["phases"], 1):
            plan["campaign_phases"].append({
                "phase_id": "PH-%s-%02d" % (slug, n), "campaign_id": cid,
                "phase_type": pt, "start_date": s, "end_date": e, "description": desc,
            })

        # 日期观察（含参照物声明 + verification_method 如实标注）
        for role, dt, method, conf, ev_key, note in spec["observations"]:
            if role == "peak" and note is None:
                note = ("参照物 = %s；K 线证实状态 = **%s** —— %s"
                        % (spec["peak_referent"], spec["kline_consequence"], spec["peak_note"]))
            plan["date_obs"].append({
                "observation_id": "OBS-%s-%s" % (cid, role), "campaign_id": cid,
                "date_role": role, "candidate_date": dt, "verified_date": dt,
                "verification_method": method, "confidence": conf,
                "evidence_id": emap.get(ev_key), "notes": note,
            })

    # ---- 冲突检查 ----
    checks = [("themes", "themes", "theme_id"), ("research_rules", "rules", "rule_id"),
              ("annual_reviews", "annual", "annual_review_id"), ("sources", "sources", "source_id"),
              ("evidences", "evidences", "evidence_id"), ("securities", "securities", "security_id"),
              ("campaigns", "campaigns", "campaign_id"), ("campaign_phases", "campaign_phases", "phase_id"),
              ("campaign_date_observations", "date_obs", "observation_id")]
    for tbl, pkey, key in checks:
        rows = plan[pkey]
        for r in rows:
            v = r[key]
            cur.execute("SELECT 1 FROM %s WHERE %s = ?" % (tbl, key), (v,))
            if cur.fetchone():
                problems.append("%s.%s 已存在：%s" % (tbl, key, v))
        ids = [r[key] for r in rows]
        if len(set(ids)) != len(ids):
            problems.append("%s（plan=%s）计划内 ID 重复" % (tbl, pkey))

    # ★ 复用的 securities 必须真的存在（否则外键会失败）
    for old_id in SEC_REUSE.values():
        cur.execute("SELECT 1 FROM securities WHERE security_id = ?", (old_id,))
        if not cur.fetchone():
            problems.append("SEC_REUSE 指向不存在的既有标的：%s" % old_id)

    print("=" * 78)
    print("R02-04 → canonical 导入计划")
    print("=" * 78)
    for k in ("themes", "rules", "annual", "sources", "evidences", "securities",
              "campaigns", "campaign_themes", "campaign_evidences",
              "campaign_securities", "campaign_phases", "date_obs"):
        print("  %-22s %d" % (k, len(plan[k])))
    print()
    for r in plan["campaigns"]:
        sp = [s for s in SPECS if s["campaign_id"] == r["campaign_id"]][0]
        print("  %-26s %s → %s → %s" % (r["campaign_id"], r["start_date"],
                                        r["peak_date"], r["end_date"] or "OPEN_ENDED"))
        print("       peak 参照物 = %s · K 线 = %s · themes = %s"
              % (sp["peak_referent"], sp["kline_consequence"],
                 ", ".join("%s/%s" % t for t in sp["themes"])))
    print()
    print("  复用既有 securities：%s" % ", ".join(sorted(SEC_REUSE.values())))
    print("  新建 securities    ：%s" % (", ".join(s["security_id"] for s in plan["securities"]) or "无"))
    if problems:
        print()
        print("!! 冲突检查失败：")
        for p in problems:
            print("   - %s" % p)
        return 1
    print()
    print("冲突检查：PASS（所有新 ID 均不存在于 DB；复用的标的均已存在）")

    if args.verify or args.dry_run:
        print()
        print("--dry-run：未写入任何内容。" if args.dry_run else "")
        return 0

    # ---- 写入（单事务） ----
    try:
        for r in plan["themes"]:
            cur.execute("INSERT INTO themes (theme_id,name,theme_type,parent_theme_id,description)"
                        " VALUES (?,?,?,?,?)", (r["theme_id"], r["name"], r["theme_type"],
                                                r["parent_theme_id"], r["description"]))
        for r in plan["rules"]:
            cur.execute("INSERT INTO research_rules (rule_id,name,base_pattern,description,status)"
                        " VALUES (?,?,?,?,?)", (r["rule_id"], r["name"], r["base_pattern"],
                                                r["description"], r["status"]))
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
    print("  campaigns 总数 = %d（原 57）" % cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM themes")
    print("  themes 总数    = %d（原 58，本次未新建 taxonomy 行）" % cur.fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
