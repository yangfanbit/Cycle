"""导出脚本：
1. research/summary/auto_2018_2025.csv  （试运行阶段仅含已录入年份）
2. exports/cycle_verified_candidates.json（Research 已整理、等待人工确认的候选数据）

用法: python scripts/export.py
"""
import sys, os, json, csv
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

ROOT = db.ROOT
conn = db.connect()

SUMMARY_CSV = os.path.join(ROOT, "research", "summary", "auto_2018_2025.csv")
EXPORT_JSON = os.path.join(ROOT, "exports", "cycle_verified_candidates.json")

CSV_FIELDS = [
    "year", "campaign_id", "classification", "start_date", "end_date", "peak_date",
    "base_pattern", "main_theme", "strength", "result", "catalyst", "leader", "confidence", "notes",
]


def query_all(q, *args):
    return [dict(r) for r in conn.execute(q, args).fetchall()]


def main():
    # ---- CSV ----
    rows = query_all("""
        SELECT c.campaign_year AS year, c.campaign_id, c.classification,
               c.start_date, c.end_date, c.peak_date,
               r.base_pattern,
               (SELECT GROUP_CONCAT(t.name, '|') FROM campaign_themes ct
                JOIN themes t ON t.theme_id = ct.theme_id
                WHERE ct.campaign_id = c.campaign_id AND ct.role='main') AS main_theme,
               c.strength, c.result,
               (SELECT GROUP_CONCAT(e.name, '|') FROM campaign_events ce
                JOIN events e ON e.event_id = ce.event_id
                WHERE ce.campaign_id = c.campaign_id AND ce.role IN ('trigger','catalyst')) AS catalyst,
               (SELECT GROUP_CONCAT(s.name, '|') FROM campaign_securities cs
                JOIN securities s ON s.security_id = cs.security_id
                WHERE cs.campaign_id = c.campaign_id AND cs.role IN ('leader','second_leader')) AS leader,
               c.date_confidence AS confidence,
               c.research_notes AS notes
        FROM campaigns c
        JOIN research_rules r ON r.rule_id = c.rule_id
        ORDER BY c.campaign_year, c.campaign_id
    """)
    os.makedirs(os.path.dirname(SUMMARY_CSV), exist_ok=True)
    with open(SUMMARY_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in CSV_FIELDS})
    print(f"CSV: {SUMMARY_CSV} ({len(rows)} rows)")

    # ---- JSON (兼容 Cycle HistoricalCampaign/CampaignTheme/CampaignSecurity/Evidence/ValidationRecord) ----
    out = {
        "meta": {
            "project": "Cycle-Research",
            "purpose": "research 阶段已整理、等待人工最终确认的候选数据（非 Cycle 正式 verified）",
            "exported_at": datetime.now().isoformat(),
            "rule": "rule_auto_summer",
            "notes": "仅在人工 Review 后，才由人工/指定 Agent 转入 Cycle/data/verified/",
        },
        "verified_candidates": [],
    }

    ars = query_all("SELECT * FROM annual_reviews WHERE rule_id='rule_auto_summer'")
    cands = query_all("SELECT * FROM campaigns WHERE rule_id='rule_auto_summer'")
    for c in cands:
        cid = c["campaign_id"]
        # theme
        themes = query_all("""
            SELECT t.*, ct.role FROM campaign_themes ct
            JOIN themes t ON t.theme_id = ct.theme_id WHERE ct.campaign_id=?""", cid)
        securities = query_all("""
            SELECT s.*, cs.role FROM campaign_securities cs
            JOIN securities s ON s.security_id = cs.security_id WHERE cs.campaign_id=?""", cid)
        events = query_all("""
            SELECT e.*, ce.role FROM campaign_events ce
            JOIN events e ON e.event_id = ce.event_id WHERE ce.campaign_id=?""", cid)
        phases = query_all("SELECT * FROM campaign_phases WHERE campaign_id=?", cid)
        evidences = query_all("""
            SELECT ev.*, s.title AS source_title, s.url AS source_url, s.tier AS source_tier
            FROM evidences ev LEFT JOIN sources s ON s.source_id = ev.source_id
            WHERE ev.evidence_id IN (
                SELECT ev2.evidence_id FROM evidences ev2 WHERE 1
            )""")  # 全量证据即本次分析依据；此处全量导出

        cand = {
            "campaign_id": cid,
            "rule": "rule_auto_summer",
            "year": c["campaign_year"],
            "classification": c["classification"],
            "dates": {
                "start_date": c["start_date"], "end_date": c["end_date"],
                "peak_date": c["peak_date"],
                "date_confidence": c["date_confidence"],
                "drift_vs_jun01": c["drift_vs_jun01"],
                "drift_vs_jul01": c["drift_vs_jul01"],
                "drift_vs_aug01": c["drift_vs_aug01"],
                "start_date_basis": c["start_date_basis"],
                "end_date_basis": c["end_date_basis"],
            },
            "result": c["result"],
            "strength": c["strength"],
            "description": c["description"],
            "research_notes": c["research_notes"],
            "campaign_themes": themes,
            "campaign_securities": securities,
            "campaign_events": events,
            "campaign_phases": phases if phases else None,
            "evidences": evidences,
            "validation": {
                "status": "awaiting_human_review",
                "min_independent_evidence_met": None,  # 人工决定
                "reviewed_by": None,
                "reviewed_at": None,
            },
        }
        out["verified_candidates"].append(cand)

    os.makedirs(os.path.dirname(EXPORT_JSON), exist_ok=True)
    with open(EXPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print(f"JSON: {EXPORT_JSON} ({len(out['verified_candidates'])} candidates)")


if __name__ == "__main__":
    main()
    conn.close()