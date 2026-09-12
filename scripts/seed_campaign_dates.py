"""Pilot 1-C1：为每个现有 Campaign 建立候选日期观测（campaign_date_observations）。

目的：
- 把 campaigns.start_date/end_date/peak_date 原样快照为 candidate_date（保留原始，不覆盖）。
- verified_date 本轮留空（NULL），待 Pilot 1-C2 用真实日线核验后填入。

- 幂等：candidate 已存在则不重复创建。绝不修改 campaigns 本身。
用法: python scripts/seed_campaign_dates.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

conn = db.connect()
db.migrate(conn)

ROLE_MAP = [("start", "start_date"), ("end", "end_date"), ("peak", "peak_date")]

campaigns = conn.execute(
    "SELECT campaign_id FROM campaigns WHERE rule_id='rule_auto_summer' ORDER BY campaign_id").fetchall()

existing = {r[0] for r in conn.execute(
    "SELECT observation_id FROM campaign_date_observations").fetchall()}

created = 0
for (cid,) in campaigns:
    row = conn.execute(
        "SELECT start_date, end_date, peak_date FROM campaigns WHERE campaign_id=?", (cid,)).fetchone()
    for role, col in ROLE_MAP:
        cand = row[col]
        if not cand:
            continue
        oid = f"OBS-{cid}-{role}"
        if oid in existing:
            continue
        db.insert(conn, "campaign_date_observations", {
            "observation_id": oid,
            "campaign_id": cid,
            "date_role": role,
            "candidate_date": cand,          # 原始研究日期，快照保留
            "verified_date": None,           # 本轮留空，C2 核验后填
            "verification_method": "unknown",
            "confidence": "low",
            "evidence_id": None,
            "notes": "candidate 快照自 campaigns；未经行情核验。",
        })
        created += 1

conn.commit()
conn.close()
print(f"Seeded {created} candidate date observations（campaigns 未修改；verified 留空待核验）。")