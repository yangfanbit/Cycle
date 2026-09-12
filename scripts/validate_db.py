"""数据库一致性检查（v1.5）。

用法: python scripts/validate_db.py
输出：所有项 PASS 则 exit 0；有 FAIL 则打印明细并 exit 1。

检查项：
1. campaign_evidences.campaign_id → campaigns 存在
2. campaign_evidences.evidence_id → evidences 存在
3. Evidence 不跨 Campaign 错配（桥表 role 与 evidence.evidence_role 一致性提示）
4. Confirmed / Research Confirmed Campaign 独立证据门槛（≥2 条且 ≥2 个 independence_group）
5. source_type / tier 一致性
6. campaign_theme 引用有效
7. campaign_event 引用有效
8. campaign_security 引用有效
9. campaign_phase 引用有效
10. 桥表证据角色是否与 evidences.evidence_role 冲突告警（warning）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

conn = db.connect()
FAILS = []
WARNS = []


def fail(rule, msg):
    FAILS.append((rule, msg))


def warn(rule, msg):
    WARNS.append((rule, msg))


def q(sql, *a):
    return conn.execute(sql, a).fetchall()


def check_refs(label, bridge_table, id_col, ref_table):
    """通用外键引用有效性检查。"""
    bad = q(f"""SELECT r.campaign_id, r.{id_col}, c.{id_col}
                FROM {bridge_table} r
                LEFT JOIN {ref_table} c ON c.{id_col} = r.{id_col}
                WHERE c.{id_col} IS NULL""")
    if bad:
        for b in bad:
            fail(f"{label}-ref", f"{bridge_table}.{id_col}={b[1]} 引用缺失（对应 {ref_table} 不存在）")
        return False
    nullc = q(f"""SELECT r.campaign_id, r.{id_col} FROM {bridge_table} r
                  LEFT JOIN campaigns c ON c.campaign_id = r.campaign_id
                  WHERE c.campaign_id IS NULL""")
    for b in nullc:
        fail(f"{label}-ref", f"{bridge_table}.campaign_id={b[0]} 引用缺失（campaign 不存在）")
    return True


def check_camp_evidence():
    # 1) 桥表引用
    bad_ce = q("""SELECT ce.campaign_id, ce.evidence_id FROM campaign_evidences ce
                  LEFT JOIN campaigns c ON c.campaign_id=ce.campaign_id
                  LEFT JOIN evidences e ON e.evidence_id=ce.evidence_id
                  WHERE c.campaign_id IS NULL OR e.evidence_id IS NULL""")
    for b in bad_ce:
        fail("campaign_evidence-ref", f"桥表引用缺失: campaign={b[0]}, evidence={b[1]}")
    # 角色一致性（warning）
    role_conflict = q("""SELECT ce.campaign_id, ce.evidence_id, ce.role, e.evidence_role
                         FROM campaign_evidences ce JOIN evidences e ON e.evidence_id=ce.evidence_id
                         WHERE ce.role IS NOT NULL AND e.evidence_role IS NOT NULL
                           AND ce.role != e.evidence_role""")
    for r in role_conflict:
        warn("campaign_evidence-role",
             f"桥表 role({r[2]}) 与 evidence_role({r[3]}) 不一致: c={r[0]}, e={r[1]}")


def check_confirmed_evidence_threshold():
    """Confirmed 状态 Campaign 至少 2 条关联证据且 ≥2 个独立 group。"""
    # confirmed 判定：research_rule.status = confirmed 视为 Confirmed
    conf = q("""SELECT c.campaign_id FROM campaigns c
                JOIN research_rules r ON r.rule_id = c.rule_id
                WHERE r.status = 'confirmed'""")
    for (cid,) in conf:
        evs = q("""SELECT COUNT(DISTINCT e.evidence_id) n, COUNT(DISTINCT e.independence_group) g
                   FROM campaign_evidences ce JOIN evidences e ON e.evidence_id=ce.evidence_id
                   WHERE ce.campaign_id=?""", cid)
        n, g = evs[0][0], evs[0][1]
        if n < 2 or g < 2:
            fail("confirmed-threshold",
                 f"Confirmed 候选 {cid} 仅 {n} 条证据 / {g} 个独立组（需≥2 证据且≥2 组），不得判为 confirmed")


def check_source_tier():
    media_map = {"media_tier2": 2, "media_tier3": 3, "media_tier4": 4}
    rows = q("""SELECT source_id, source_type, tier FROM sources
                WHERE source_type IN ('media_tier2','media_tier3','media_tier4')""")
    for sid, st, tier in rows:
        if media_map.get(st) != tier:
            fail("source-tier", f"{sid}: source_type={st} 但 tier={tier}，不一致")


def check_orphan_evidences():
    """任何 evidence 若与某 campaign 无桥表关联，且其 evidence_role=supporting，做 warning
    （context/contradicting 可独立存在，不告警）。"""
    rows = q("""SELECT e.evidence_id, e.evidence_role FROM evidences e
                WHERE NOT EXISTS (SELECT 1 FROM campaign_evidences ce WHERE ce.evidence_id=e.evidence_id)
                  AND e.evidence_role='supporting'""")
    for r in rows:
        warn("orphan-supporting-evidence", f"{r[0]} 为 supporting 但未关联任何 Campaign，需核对其归属")


def main():
    print("=== validate_db.py 一致性检查 ===\n")

    check_camp_evidence()
    check_confirmed_evidence_threshold()
    check_source_tier()
    check_orphan_evidences()
    check_refs("theme", "campaign_themes", "theme_id", "themes")
    check_refs("event", "campaign_events", "event_id", "events")
    check_refs("security", "campaign_securities", "security_id", "securities")
    # campaign_phase 引用
    nullp = q("""SELECT p.phase_id, p.campaign_id FROM campaign_phases p
                 LEFT JOIN campaigns c ON c.campaign_id=p.campaign_id WHERE c.campaign_id IS NULL""")
    for b in nullp:
        fail("phase-ref", f"campaign_phases.phase_id={b[0]} 的 campaign={b[1]} 不存在")

    print(f"PASS: {len(FAILS)==0 and len(WARNS)>=0}")
    print("-" * 40)
    for rule, msg in WARNS:
        print(f"WARNING [{rule}] {msg}")
    for rule, msg in FAILS:
        print(f"FAIL    [{rule}] {msg}")
    print("-" * 40)

    if FAILS:
        print(f"\n结果: FAIL（{len(FAILS)} 处）——需修复后再继续。")
        conn.close()
        sys.exit(1)
    else:
        print(f"\n结果: PASS（{len(WARNS)} 条警告，需人工留意）")
        conn.close()


if __name__ == "__main__":
    main()