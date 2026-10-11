#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""import_r02_03_canonical_v0_1.py —— 把 R02-03 的 4 条候选写入 canonical DB。

## 依据

- 审查结果：`docs/R02_03_REVIEW_v0_1.md`（4 条 `ACCEPT_WITH_CHANGES`，其余留 intake）
- 独立性闸门：`docs/R02_03_CANONICALIZATION_PLAN_v0_1.md`（Q1–Q5 **全部通过**）
- 方法学：`theme_campaign_separation_v1.md` · `macro_theme_primary_related_v0_1.md`
- 协议 §3.2：**只有 ThreeC Agent 有 canonicalization 权限**（本脚本即该动作）

## 写入的 4 条 Campaign

| canonical_id | 来源候选 | main / related | peak | 参照物 |
|---|---|---|---|---|
| `C-2021-RES-COAL`    | R02-COAL-001    | 煤炭 + 资源 | 2021-10-19 | **政策事件** |
| `C-2021-POWER-GREEN` | R02-POWER-002   | 绿电/新能源运营商 + 电力（运营端） | 2021-09-28 | **政策事件** |
| `C-2023-PHARMA-FLU`  | R02-VACCINE-002 | 流感疫苗 + 医药健康 | 2023-03-20 | **行业指标** |
| `C-2023-MEDIA-AI`    | R02-MEDIA-001   | 文化传媒 | NULL | 未界定 |

## ★★ 两条硬纪律

1. **peak 参照物必须落库**。三条的 peak **都不是股价高点** →
   按 `AGENTS.md` §5.1，K 线证实状态为 **`NOT_APPLICABLE`**，**不得**记 `UNCONFIRMED`。
   参照物写入 `campaign_date_observations.notes` 与 `campaigns.research_notes`。
2. **Temporal Firewall 信息不得丢失**。DB `evidences` 表**没有** `support_kind` /
   `point_in_time_note` 列 → 这两项**追加进 `description`**，否则 PIT 声明在 canonical 层消失。

## 安全设计

- `--dry-run` 打印完整计划（不写）；`--apply` 单事务写入；`--verify` 只做导入后验收。
- **幂等**：campaign_id 已存在且**关键列一致** → 跳过；**不一致** → **拒绝**。
- **ID 冲突防护**：任何新 ID 若已存在于对应表 → **拒绝**（不静默覆盖）。
- **不写** `events` / `campaign_events`（候选未提供事件实体，证据已覆盖）。
- 复用既有 `AR-RES-2021` / `AR-MED-2023`（`annual_reviews` 有 `UNIQUE(rule_id, year)`）。
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
PKG = os.path.join(ROOT, "research", "intake", "packages", "R02-03")

sys.path.insert(0, SCRIPT_DIR)


def rd(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


# ================================================================ 规格

# 新 taxonomy 行（依据用户「电力细分按市场炒作过的概念区分」）
NEW_THEMES = [{
    "theme_id": "TH-POWER-OP-GREEN", "name": "绿电 / 新能源运营商",
    "theme_type": "concept", "parent_theme_id": "TH-POWER-OP",
    "description": "绿色电力交易试点与新能源运营商（2021）。"
                   "★ 属「电力（运营端）」下的具体概念 —— 依用户 2026-10-09 指令"
                   "「电力 细分 根据市场炒作过的概念/板块进行区分」。"
                   "（R02-03 canonicalization · 2026-10-10）",
}]

# 新规则。★ 必须以 candidate 建立 —— 包明确记载季节性「未取得可复现证据」
NEW_RULES = [
    {"rule_id": "rule_power_operation", "name": "电力（运营端）历史观察窗口",
     "base_pattern": "电力（运营端）", "status": "candidate",
     "description": "电力运营端（发电 / 电网运营）的历史题材窗口。"
                    "★ **观察窗口未经核验** —— R02-03 明确记载季节性（迎峰度夏 / 水电汛期）"
                    "「未取得可复现炒作窗口的证据」（R02-POWER-Q003）。"
                    "**不得**据此推断季节性。（R02-03 · 2026-10-10）"},
    {"rule_id": "rule_media", "name": "文化传媒历史观察窗口",
     "base_pattern": "文化传媒", "status": "candidate",
     "description": "文化传媒（政策 / 监管周期 + 内容供给 + 平台经济）的历史题材窗口。"
                    "★ **观察窗口未经核验** —— R02-03 明确记载春节档 / 暑期档季节性"
                    "「未取得可复现炒作窗口的证据」（R02-MEDIA-Q002）。"
                    "**不得**据此推断季节性。（R02-03 · 2026-10-10）"},
]

# ★★ 标准格式的 canonical → intake 映射（供 `build_lifecycle_from_intake` 提取）。
#    格式必须是 `INTAKE_MAP = [("<canonical>", "<intake_id>")]` —— 该构建器用正则扫本文件。
#    R02-03 的 4 个方向在**同一个包**里用了 4 个前缀（COAL/POWER/VACCINE/MEDIA），
#    因此构建器必须按**完整 intake id** 查表，不能靠「包 → 单一前缀」拼接。
INTAKE_MAP = [
    ("C-2021-RES-COAL", "R02-COAL-001"),
    ("C-2021-POWER-GREEN", "R02-POWER-002"),
    ("C-2023-PHARMA-FLU", "R02-VACCINE-002"),
    ("C-2023-MEDIA-AI", "R02-MEDIA-001"),
]

# 新年度综述（另两条复用既有：AR-RES-2021 / AR-MED-2023）
NEW_ANNUAL = [
    {"annual_review_id": "AR-PWROP-2021", "rule_id": "rule_power_operation", "year": 2021,
     "status": "medium",
     "summary": "2021 年电力运营端出现「绿色电力交易试点」驱动的题材段（09-07 复函 → 09-28 试点启动）。"
                "同期存在能耗双控 / 限电的系统性背景。",
     "review_notes": "★ 该窗口**未经核验**；2021 年同族另有「电力设备」（制造端）段，机制不同、不合并。"},
    {"annual_review_id": "AR-MEDIA-2023", "rule_id": "rule_media", "year": 2023,
     "status": "medium",
     "summary": "2023 年文化传媒出现「AI + 内容」驱动的板块行情（年初至 7 月末申万传媒 +28%）。"
                "★ 这是本族在全库的**第一段**历史对象。",
     "review_notes": "★ 该窗口**未经核验**；春节档 / 暑期档季节性未获证据。"},
]

# 证券（slug 沿用既有风格：LONGI / GOLDWIND / SUNGROW）
SECURITY_MAP = {
    "R02-COAL-SEC001": "CHINASHENHUA", "R02-COAL-SEC002": "SHAANXICOAL",
    "R02-COAL-SEC003": "YANKUANG",
    "R02-POWER-SEC001": "SANXIAENERGY", "R02-POWER-SEC002": "JINGNENG",
    "R02-POWER-SEC003": "YINXING",
    "R02-VACCINE-SEC001": "HUALANVAX", "R02-VACCINE-SEC002": "JINDIKE",
    "R02-VACCINE-SEC003": "BAIKEBIO",
    "R02-MEDIA-SEC001": "SANQI", "R02-MEDIA-SEC002": "GUANGXIAN",
    "R02-MEDIA-SEC003": "ZWONLINE",
}

# 4 条 Campaign 的规格
SPECS = [
    {
        "candidate_id": "R02-COAL-001",
        "campaign_id": "C-2021-RES-COAL", "slug": "COAL",
        "annual_review_id": "AR-RES-2021", "rule_id": "rule_resources",
        "season_id": "res_coal_2021",
        "start": "2021-08-01", "peak": "2021-10-19", "end": "2021-11-30",
        "strength": "strong", "result": "positive", "classification": "theme_campaign",
        "date_confidence": "medium",
        "start_basis": "研究候选窗口 2021-08-01~09-30（intake R02-COAL-001 start，DATE_WINDOW）："
                       "6 月初至 9 月动力煤价高位震荡，9 月至 10 月中旬冬储需求释放后快速上涨"
                       "（据 S-COAL-02，tier2）；同期 9 月多地拉闸限电（据 S-COAL-03，tier2）。"
                       "**未取得精确起涨日**，按窗口起点记录。",
        "end_basis": "保供稳价政策落地后产地供应增加、电厂库存提升，价格快速回落（据 S-COAL-02，tier2）。"
                     "为降温窗口终点，非精确终局日。",
        "peak_referent": "政策事件",
        "kline_consequence": "NOT_APPLICABLE",
        "themes": [("TH-RES-COAL", "main"), ("TH-RES", "related")],
        "phases": [("MAIN_RISE", "2021-08-01", "2021-10-19", "上行：供给收缩（安监/环保/超能力检查、澳煤进口减量）"
                                                       "+ 需求激增（工业用电、高温与冬储）+ 9 月限电强化供给紧张叙事。"),
                   ("RETRACEMENT", "2021-10-19", "2021-11-30", "回撤：2021-10-19 发改委研究依法干预煤炭价格，"
                                                           "保供稳价下价格快速回落。")],
    },
    {
        "candidate_id": "R02-POWER-002",
        "campaign_id": "C-2021-POWER-GREEN", "slug": "PWROP",
        "annual_review_id": "AR-PWROP-2021", "rule_id": "rule_power_operation",
        "season_id": "power_green_2021",
        "start": "2021-09-07", "peak": "2021-09-28", "end": None,
        "strength": "medium", "result": "positive", "classification": "theme_campaign",
        "date_confidence": "medium",
        "start_basis": "2021-09-07 国家发展改革委、国家能源局复函国家电网、南方电网推动绿电交易试点"
                       "（据 S-PWROP-01，tier1 一手，contemporaneous）。",
        "end_basis": "★ **未界定** —— 本包未取得该段终结的可核验证据，按协议**不推断**。"
                     "按既有开放式 Campaign 惯例记 OPEN_ENDED（end_date = NULL）。",
        "peak_referent": "政策事件",
        "kline_consequence": "NOT_APPLICABLE",
        "themes": [("TH-POWER-OP-GREEN", "main"), ("TH-POWER-OP", "related")],
        "phases": [("MAIN_RISE", "2021-09-07", "2021-09-28",
                    "上行：绿电交易试点从复函（09-07）到正式启动（09-28）；"
                    "同期能耗双控与电力供应紧张强化新能源运营商稀缺性叙事。")],
    },
    {
        "candidate_id": "R02-VACCINE-002",
        "campaign_id": "C-2023-PHARMA-FLU", "slug": "FLU",
        "annual_review_id": "AR-MED-2023", "rule_id": "rule_pharma_upgrade",
        "season_id": "pharma_flu_2023",
        "start": "2023-02-20", "peak": "2023-03-20", "end": "2023-04-15",
        "strength": "medium", "result": "positive", "classification": "event_driven",
        "date_confidence": "medium",
        "start_basis": "研究候选窗口 2023-02-20~03-06（intake R02-VACCINE-002 start，DATE_WINDOW）："
                       "冬春季流感高发，主要流行株 A(H1N1)pdm09；抗流感药物需求上升（据 S-FLU-02，tier3 转述）。",
        "end_basis": "国家流感中心第 12 周（截至 2023-03-24）南方省份阳性率上升趋缓、北方下降"
                     "（据 S-FLU-01，tier1 一手）；行情回落窗口至 2023-04-15（据 S-FLU-02，tier3）。",
        "peak_referent": "行业指标",
        "kline_consequence": "NOT_APPLICABLE",
        "themes": [("TH-PHARMA-FLU", "main"), ("TH-PHARMA", "related")],
        "phases": [("MAIN_RISE", "2023-02-20", "2023-03-20",
                    "上行：流感季节性高发 → 抗流感概念股走高、部分药企满负荷生产（据 S-FLU-02）；"
                    "2023-03-20 官方表态「3 月中旬已进入高峰、整体处高位」（据 S-FLU-03，tier3 转述官方表态）。"),
                   ("RETRACEMENT", "2023-03-24", "2023-04-15",
                    "回落：国家流感中心第 12 周监测显示阳性率上升趋缓 / 北方下降（据 S-FLU-01，tier1）；行情降温。")],
    },
    {
        "candidate_id": "R02-MEDIA-001",
        "campaign_id": "C-2023-MEDIA-AI", "slug": "MEDIA",
        "annual_review_id": "AR-MEDIA-2023", "rule_id": "rule_media",
        "season_id": "media_ai_2023",
        "start": "2023-03-31", "peak": None, "end": "2023-07-31",
        "strength": "medium", "result": "positive", "classification": "theme_campaign",
        "date_confidence": "low",
        "start_basis": "★ 审查要求修正：原 intake 起始窗口端点 2022-11-30（ChatGPT 发布）**在证据中无 source_id** "
                       "→ 端点收回到 S-MEDIA-02 实际支持的范围。来源记载「A 股传媒板块 2022-11 处于估值低点，"
                       "此后受益于内容供给释放和 AI 技术应用逐步修复」（据 S-MEDIA-02，tier2，subsequent）。"
                       "取 2023-03-31（2023Q1 末）为可支持的上行段起点。",
        "end_basis": "机构研究以「年初至 7 月末」为统计区间，说明上行段至少延续至 7 月末"
                     "（据 S-MEDIA-01，tier2，subsequent）。**不声称此为终局日**，仅界定统计终点。",
        "peak_referent": "未界定",
        "kline_consequence": "—",
        "themes": [("TH-MEDIA", "main")],
        "phases": [("MAIN_RISE", "2023-03-31", "2023-07-31",
                    "上行：生成式 AI 主题扩散至内容行业（游戏 / 出版 / 影视）；"
                    "2023H1 传媒子板块普涨，游戏涨幅居首（据 S-MEDIA-02，tier2）；"
                    "年初至 7 月末申万传媒 +28%（据 S-MEDIA-01，tier2）。")],
    },
]


def main(argv):
    ap = argparse.ArgumentParser(description="R02-03 → canonical 导入")
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
                "【R02-03 canonicalization · 2026-10-10】来源候选 %s。"
                "★★ **peak 参照物 = %s** —— 按 AGENTS.md §5.1 硬语义边界，"
                "参照物非股价时 K 线证实状态为 **%s**，**不得**记为 UNCONFIRMED。"
                "独立性闸门：见 docs/R02_03_CANONICALIZATION_PLAN_v0_1.md（Q1–Q5 通过）。"
                "审查：docs/R02_03_REVIEW_v0_1.md。"
                % (spec["candidate_id"], spec["peak_referent"], spec["kline_consequence"])
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
                "description": "【R02-03 导入】来源 intake ID = %s。%s"
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

        # 证券
        for sid in c.get("security_ids") or []:
            o = secs[sid]
            new_id = SECURITY_MAP[sid]
            if not any(x["security_id"] == new_id for x in plan["securities"]):
                plan["securities"].append({
                    "security_id": new_id, "ticker": o.get("ticker"),
                    "name": o.get("name"), "exchange": o.get("exchange"),
                })
            plan["campaign_securities"].append((cid, new_id, o.get("role") or "representative"))

        # 阶段
        for n, (pt, s, e, desc) in enumerate(spec["phases"], 1):
            plan["campaign_phases"].append({
                "phase_id": "PH-%s-%02d" % (slug, n), "campaign_id": cid,
                "phase_type": pt.lower(), "start_date": s, "end_date": e,
                "description": desc,
            })

        # 日期观察（含参照物声明）
        dc = c.get("date_candidates") or {}
        for role, col in (("start", spec["start"]), ("peak", spec["peak"]), ("end", spec["end"])):
            if col is None:
                continue
            note = "参照物 = %s；K 线证实状态 = %s" % (spec["peak_referent"], spec["kline_consequence"]) \
                if role == "peak" else None
            plan["date_obs"].append({
                "observation_id": "OBS-%s-%s" % (cid, role), "campaign_id": cid,
                "date_role": role, "candidate_date": col, "verified_date": col,
                "verification_method": "unknown", "confidence": spec["date_confidence"],
                "evidence_id": None, "notes": note,
            })

    # ---- 冲突检查 ----
    # (DB 表名, plan 键, 主键列)
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

    print("=" * 78)
    print("R02-03 → canonical 导入计划")
    print("=" * 78)
    for k in ("themes", "rules", "annual", "sources", "evidences", "securities",
              "campaigns", "campaign_themes", "campaign_evidences",
              "campaign_securities", "campaign_phases", "date_obs"):
        print("  %-22s %d" % (k, len(plan[k])))
    print()
    for r in plan["campaigns"]:
        print("  %-22s %s → %s → %s   peak 参照物=%s"
              % (r["campaign_id"], r["start_date"], r["peak_date"], r["end_date"] or "OPEN_ENDED",
                 [s["peak_referent"] for s in SPECS if s["campaign_id"] == r["campaign_id"]][0]))
    if problems:
        print()
        print("!! 冲突检查失败：")
        for p in problems:
            print("   - %s" % p)
        return 1
    print()
    print("冲突检查：PASS（所有新 ID 均不存在于 DB）")

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
    print("  campaigns 总数 = %d（原 53）" % cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM themes")
    print("  themes 总数    = %d（原 57）" % cur.fetchone()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
