# -*- coding: utf-8 -*-
"""
TEMPORARY RESEARCH SCRIPT — Seasonal Observation Pattern Discovery v0.1
========================================================================
STATUS: 临时研究脚本。**不是产品代码，不得进入 src/ 或 research/scripts/ 正式流水线。**
用途：从 ThreeC 既有 canonical export + research DB 读取全量历史对象，
      按固定优先级建立 observation_anchor，产出候选观测底表（CSV/JSON）。
纪律：只读；不写 DB / schema / export / contract。

运行： python build_dataset.py
输出： observation_anchors_raw.csv
       observation_units.csv          (聚合到「年度主题级」后的统计单元)
       data_fitness.json              (Data Fitness Assessment 原始计数)
"""

import csv
import json
import os
import sqlite3
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
EXPORT = os.path.join(REPO, "exports", "timeline_export_v1.json")
DB = os.path.join(REPO, "research", "database", "cycle_research.db")

# ---------------------------------------------------------------- 基础工具

def parse_iso(s):
    if not s:
        return None
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def doy(d):
    """年内序数（1-366）。用于跨年份比较时间位置。"""
    return d.timetuple().tm_yday


def leap_norm(d):
    """
    把闰年 day-of-year 归一到「非闰年基准」(365 天年)。
    规则：3 月 1 日及以后 -1。这样 06-18 在任何年份都得到同一序数，
    避免闰年把 6 月之后的所有日期整体后移 1 天。
    注：这只是归一化，不改变真实日期；跨年边界的处理另见 wrap 逻辑。
    """
    n = doy(d)
    if d.month >= 3 and _is_leap(d.year):
        n -= 1
    return n


def _is_leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def days_in_norm_year(y):
    return 366 if _is_leap(y) else 365


def circular_distance(a, b, period=365):
    """环形距离（处理 12 月 / 1 月边界）。"""
    d = abs(a - b) % period
    return min(d, period - d)


# ---------------------------------------------------------------- 读取数据

def load_export():
    with open(EXPORT, "r", encoding="utf-8") as f:
        return json.load(f)


def load_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


# ------------------------------------------------------- Anchor 优先级构建

ANCHOR_EARLY = "ANCHOR_A_EARLY_SIGNAL"
ANCHOR_FORMATION = "ANCHOR_B_FORMATION"
ANCHOR_START = "ANCHOR_C_CAMPAIGN_START"
ANCHOR_NONE = "ANCHOR_NONE"


def build_anchor(obj, signals_by_campaign):
    """
    observation_anchor 优先级（严格按研究任务定义）：
      Anchor A — Early Signal（lifecycle EARLY_SIGNAL.start 或 export early_signal）
      Anchor B — Formation Anchor：THEME_FORMING.start → BROAD_CONFIRMATION.start
      Anchor C — Campaign.start
    绝不把 Peak / End / 单日暴涨 / 新闻 当作启动观察日。
    返回 (anchor_date, anchor_type, anchor_source_detail)
    """
    lc = obj.get("lifecycle") or []
    stages = {s.get("stage"): s for s in lc}

    # --- Anchor A: Early Signal
    a_date, a_src = None, None
    es = obj.get("early_signal")
    if isinstance(es, dict):
        a_date, a_src = es.get("start"), "export.early_signal.start"
    elif isinstance(es, str) and es:
        a_date, a_src = es, "export.early_signal(str)"
    if not a_date and stages.get("EARLY_SIGNAL", {}).get("start"):
        a_date, a_src = stages["EARLY_SIGNAL"]["start"], "lifecycle.EARLY_SIGNAL.start"
    if not a_date:
        # signals[] 数组中的 EARLY_SIGNAL（export 顶层）
        sigs = signals_by_campaign.get(obj["campaign_id"], [])
        early = [s for s in sigs if s.get("type") == "EARLY_SIGNAL"]
        if early:
            early.sort(key=lambda s: s.get("date") or "")
            a_date, a_src = early[0].get("date"), "signals[].EARLY_SIGNAL(min)"
    if a_date:
        return a_date, ANCHOR_EARLY, a_src

    # --- Anchor B: Formation Anchor
    if stages.get("THEME_FORMING", {}).get("start"):
        return stages["THEME_FORMING"]["start"], ANCHOR_FORMATION, "lifecycle.THEME_FORMING.start"
    if stages.get("BROAD_CONFIRMATION", {}).get("start"):
        return (
            stages["BROAD_CONFIRMATION"]["start"],
            ANCHOR_FORMATION,
            "lifecycle.BROAD_CONFIRMATION.start",
        )

    # --- Anchor C: Campaign start
    if obj.get("start_date"):
        return obj["start_date"], ANCHOR_START, "start_date(campaign.start)"

    return None, ANCHOR_NONE, None


def main():
    exp = load_export()
    con = load_db()
    cur = con.cursor()

    # 主题层级（DB）
    cur.execute("SELECT theme_id, name, theme_type, parent_theme_id FROM themes")
    themes = {r["theme_id"]: dict(r) for r in cur.fetchall()}

    cur.execute("SELECT campaign_id, theme_id, role FROM campaign_themes")
    camp_themes = {}
    for r in cur.fetchall():
        camp_themes.setdefault(r["campaign_id"], []).append(dict(r))

    # signals 归属索引
    signals_by_campaign = {}
    for s in exp.get("signals", []):
        key = s.get("campaign_id") or s.get("research_candidate_id")
        if key:
            signals_by_campaign.setdefault(key, []).append(s)

    # 数据库中的日期观测（用于数据质量）
    cur.execute(
        "SELECT campaign_id, date_role, candidate_date, verified_date, verification_method, confidence "
        "FROM campaign_date_observations"
    )
    obs = {}
    for r in cur.fetchall():
        obs.setdefault(r["campaign_id"], {})[r["date_role"]] = dict(r)

    # Campaign status / research_status
    cur.execute("SELECT campaign_id, strength, result, classification, date_confidence, rule_id, campaign_year FROM campaigns")
    camp_meta = {r["campaign_id"]: dict(r) for r in cur.fetchall()}

    cur.execute("SELECT annual_review_id, rule_id, year, status FROM annual_reviews")
    annual = {}
    for r in cur.fetchall():
        annual[(r["rule_id"], r["year"])] = r["status"]

    rows = []

    def add(obj, kind):
        cid = obj["campaign_id"]
        a_date, a_type, a_src = build_anchor(obj, signals_by_campaign)
        d = parse_iso(a_date)
        meta = camp_meta.get(cid, {})
        main_theme = None
        sub_themes = []
        macro = None
        for t in camp_themes.get(cid, []):
            nm = themes.get(t["theme_id"], {}).get("name")
            if t["role"] == "main" and nm and main_theme is None:
                main_theme = nm
            if nm:
                sub_themes.append(nm)
            parent = themes.get(t["theme_id"], {}).get("parent_theme_id")
            if parent is None and nm:
                macro = nm
        rows.append(
            {
                "object_kind": kind,  # campaign | research_candidate
                "campaign_id": cid,
                "year": obj.get("year"),
                "rule_id": obj.get("rule_id"),
                "theme_cycle_id": obj.get("theme_cycle_id"),
                "main_theme": main_theme,
                "macro_theme": macro,
                "themes_all": ";".join(sub_themes),
                "anchor_date": a_date,
                "anchor_type": a_type,
                "anchor_source": a_src,
                "anchor_doy": doy(d) if d else None,
                "anchor_doy_norm": leap_norm(d) if d else None,
                "anchor_month": d.month if d else None,
                "anchor_md": d.strftime("%m-%d") if d else None,
                "campaign_start": obj.get("start_date"),
                "campaign_peak": obj.get("peak_date"),
                "campaign_end": obj.get("end_date"),
                "production_status": obj.get("status"),
                "research_status": obj.get("research_status"),
                "classification": obj.get("classification"),
                "strength": obj.get("strength") or meta.get("strength"),
                "result": obj.get("result") or meta.get("result"),
                "date_confidence": meta.get("date_confidence"),
                "has_conflict": bool(obj.get("conflicts")),
                "lifecycle_stages": ">".join([s.get("stage", "") for s in (obj.get("lifecycle") or [])]),
                "annual_status": annual.get((obj.get("rule_id"), obj.get("year"))),
                "n_evidence": None,
                "prod_status": obj.get("status"),
            }
        )

    for c in exp.get("campaigns", []):
        add(c, "campaign")
    for c in exp.get("research_candidates", []):
        add(c, "research_candidate")

    # 写出原始锚点表
    out_raw = os.path.join(HERE, "observation_anchors_raw.csv")
    cols = list(rows[0].keys())
    with open(out_raw, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # ------------------------------------------------ 年度主题级聚合（去重）
    # 规则：同一年 + 同一 theme_cycle_id（或同一主主题）的多个对象
    #       不当作多个独立年份样本；取当年最早有效锚点作为一个统计单元。
    groups = {}
    for r in rows:
        d = parse_iso(r["anchor_date"])
        if not d:
            continue
        key_thesis = r["theme_cycle_id"] or r["main_theme"] or r["macro_theme"] or r["campaign_id"]
        # 主题族键：把同一 Macro Theme 下的不同 Cycle 归入同一族（Level 3 探索）
        family = r["macro_theme"] or r["main_theme"] or key_thesis
        gkey = (r["year"], key_thesis)
        if gkey not in groups or d < parse_iso(groups[gkey]["anchor_date"]):
            groups[gkey] = r
        groups[gkey]["_family"] = family

    units = []
    for (year, thesis), r in sorted(groups.items(), key=lambda kv: (kv[1]["_family"] or "", kv[0][0])):
        rr = dict(r)
        rr["unit_key"] = f"{year}:{thesis}"
        rr["family"] = r["_family"]
        units.append(rr)

    out_units = os.path.join(HERE, "observation_units.csv")
    ucols = [c for c in cols if c != "_family"] + ["unit_key", "family"]
    with open(out_units, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=ucols)
        w.writeheader()
        for r in units:
            w.writerow({k: r.get(k) for k in ucols})

    # ------------------------------------------------ Data Fitness
    cur.execute("SELECT COUNT(*) FROM campaigns")
    n_campaigns = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM themes")
    n_themes = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM themes WHERE parent_theme_id IS NULL")
    n_macro = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM themes WHERE parent_theme_id IS NOT NULL")
    n_sub = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM annual_reviews")
    n_annual = cur.fetchone()[0]

    all_objs = exp.get("campaigns", []) + exp.get("research_candidates", [])
    fit = {
        "n_campaigns_export": len(exp.get("campaigns", [])),
        "n_campaigns_db": n_campaigns,
        "n_research_candidates_export": len(exp.get("research_candidates", [])),
        "n_total_export_objects": len(all_objs),
        "n_themes": n_themes,
        "n_macro_themes": n_macro,
        "n_sub_themes": n_sub,
        "n_annual_reviews": n_annual,
        "n_rules": len(exp.get("rules", [])),
        "n_signals": len(exp.get("signals", [])),
        "n_events": len(exp.get("events", [])),
        "n_securities": len(exp.get("securities", [])),
        "anchor_type_counts": {
            ANCHOR_EARLY: sum(1 for r in rows if r["anchor_type"] == ANCHOR_EARLY),
            ANCHOR_FORMATION: sum(1 for r in rows if r["anchor_type"] == ANCHOR_FORMATION),
            ANCHOR_START: sum(1 for r in rows if r["anchor_type"] == ANCHOR_START),
            ANCHOR_NONE: sum(1 for r in rows if r["anchor_type"] == ANCHOR_NONE),
        },
        "has_early_signal": sum(1 for r in rows if r["anchor_type"] == ANCHOR_EARLY),
        "has_theme_forming": sum(
            1 for r in all_objs if any(s.get("stage") == "THEME_FORMING" for s in (r.get("lifecycle") or []))
        ),
        "has_broad_confirmation": sum(
            1 for r in all_objs if any(s.get("stage") == "BROAD_CONFIRMATION" for s in (r.get("lifecycle") or []))
        ),
        "only_campaign_start": sum(
            1
            for r in all_objs
            if not r.get("early_signal")
            and not any(
                s.get("stage") in ("EARLY_SIGNAL", "THEME_FORMING", "BROAD_CONFIRMATION")
                for s in (r.get("lifecycle") or [])
            )
        ),
        "has_conflict": sum(1 for r in all_objs if r.get("conflicts")),
        "status_counts": {},
        "research_status_counts": {},
        "years_seen": sorted({r["year"] for r in all_objs if r.get("year")}),
        "units_total": len(units),
        "units_by_family": {},
        "verification_method_counts": {},
        "date_confidence_counts": {},
    }
    for r in all_objs:
        k = r.get("status")
        fit["status_counts"][k] = fit["status_counts"].get(k, 0) + 1
        k2 = r.get("research_status")
        fit["research_status_counts"][k2] = fit["research_status_counts"].get(k2, 0) + 1
    for r in units:
        fit["units_by_family"][r["family"]] = fit["units_by_family"].get(r["family"], 0) + 1
    for cid, roles in obs.items():
        for role, o in roles.items():
            k = o.get("verification_method")
            fit["verification_method_counts"][k] = fit["verification_method_counts"].get(k, 0) + 1
    for cid, m in camp_meta.items():
        k = m.get("date_confidence")
        fit["date_confidence_counts"][k] = fit["date_confidence_counts"].get(k, 0) + 1

    with open(os.path.join(HERE, "data_fitness.json"), "w", encoding="utf-8") as f:
        json.dump(fit, f, ensure_ascii=False, indent=2)

    print(json.dumps(fit, ensure_ascii=False, indent=2))
    print("\n--- RAW ANCHORS ---")
    for r in sorted(rows, key=lambda x: (x["rule_id"] or "", x["year"] or 0, x["campaign_id"])):
        print(
            f"{r['campaign_id']:22s} {r['year']} {str(r['anchor_date']):12s} "
            f"{r['anchor_type']:28s} md={r['anchor_md']} theme={r['main_theme']} cycle={r['theme_cycle_id']}"
        )


if __name__ == "__main__":
    main()
