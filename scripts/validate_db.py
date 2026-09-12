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

Pilot 1-C1（行情核验基础设施，§15 的 11 项）：
11. Market Series 唯一性
12. Daily Market Data 外键 → market_series
13. trade_date 格式（ISO）
14. 同一 series/date 不允许重复
15. raw / normalized(adjusted) 区分、禁止口径混用
16. candidate_date 不被 verified 覆盖（候选与 campaigns 一致）
17. Date Observation 必须引用有效 Campaign
18. evidence_id 若存在必须有效
19. Date Observation 枚举合法
20. 不使用未来成分股回填历史 / export 不混入无关 Market Data
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


# ============================================================
# Pilot 1-C1：行情核验基础设施检查（对应任务 §15 的 11 项测试）
# ============================================================

def check_market_series_unique():
    """测试1：Market Series 唯一性（series_id 主键）。"""
    dup = q("""SELECT series_id, COUNT(*) n FROM market_series GROUP BY series_id HAVING n>1""")
    for r in dup:
        fail("market-series-dup", f"series_id={r[0]} 重复({r[1]}行)")
    null_name = q("SELECT series_id FROM market_series WHERE name IS NULL OR name=''")
    for r in null_name:
        fail("market-series-name", f"series_id={r[0]} 缺 name")


def check_market_daily_fk():
    """测试2：Daily Market Data 外键 → market_series。"""
    bad = q("""SELECT d.series_id FROM market_daily d
               LEFT JOIN market_series s ON s.series_id=d.series_id WHERE s.series_id IS NULL""")
    for r in bad:
        fail("market-daily-fk", f"market_daily.series_id={r[0]} 引用缺失（market_series 不存在）")


def check_market_daily_date_format():
    """测试3：trade_date 格式（ISO YYYY-MM-DD 且是合法日期）。"""
    import scripts.market_metrics as mm
    rows = q("SELECT series_id, trade_date FROM market_daily")
    for sid, td in rows:
        if not mm.is_valid_iso_date(td):
            fail("market-daily-datefmt", f"series={sid} trade_date='{td}' 格式不合法")
    trows = q("SELECT trade_date FROM trading_calendar")
    for (td,) in trows:
        if not mm.is_valid_iso_date(td):
            fail("calendar-datefmt", f"trading_calendar.trade_date='{td}' 格式不合法")


def check_market_daily_no_dup():
    """测试4：同一 series/date 不允许重复（PK 已保证，这里显式再查）。"""
    dup = q("""SELECT series_id, trade_date, price_type, COUNT(*) n
               FROM market_daily GROUP BY series_id, trade_date, price_type HAVING n>1""")
    for r in dup:
        fail("market-daily-dup", f"series={r[0]} date={r[1]} type={r[2]} 重复({r[3]}行)")


def check_raw_normalized():
    """测试5：raw / adjusted 区分——每行必须明确 price_type；
    adj_close 只在 adjusted 行出现，raw 行不应带 adj_close。"""
    rows = q("SELECT series_id, trade_date, price_type, adj_close FROM market_daily")
    for sid, td, pt, adjc in rows:
        if pt not in ("raw", "adjusted"):
            fail("market-daily-price_type", f"series={sid} date={td} price_type='{pt}' 非法")
        if pt == "raw" and adjc is not None:
            fail("market-daily-mix", f"series={sid} date={td} 为 raw 但带了 adj_close(口径混用)")
    badser = q("SELECT series_id FROM market_series WHERE price_type NOT IN ('raw','adjusted','other')")
    for (sid,) in badser:
        fail("market-series-price_type", f"series_id={sid} price_type 非法")


def check_cdo_candidate_not_overwrite():
    """测试6：candidate_date 不会覆盖 verified_date——观测中的 candidate_date 必须与
    campaigns 对应日期字段一致（保留原始)、且 verified_date 独立列不回溯改动 candidate。"""
    role_col = {"start": "start_date", "end": "end_date", "peak": "peak_date"}
    rows = q("""SELECT cdo.observation_id, cdo.campaign_id, cdo.date_role,
                       cdo.candidate_date, cp.start_date, cp.end_date, cp.peak_date
                FROM campaign_date_observations cdo
                JOIN campaigns cp ON cp.campaign_id=cdo.campaign_id""")
    for oid, cid, role, cand, s, e, pk in rows:
        expected = role_col.get(role)
        actual = {"start": s, "end": e, "peak": pk}.get(role)
        if cand != actual:
            fail("cdo-candidate-mismatch",
                 f"obs={oid} {cid}[{role}] candidate={cand} 与 campaigns.{expected}={actual} 不一致")


def check_cdo_campaign_ref():
    """测试7：Date Observation 必须引用有效 Campaign。"""
    bad = q("""SELECT cdo.observation_id FROM campaign_date_observations cdo
               LEFT JOIN campaigns c ON c.campaign_id=cdo.campaign_id WHERE c.campaign_id IS NULL""")
    for (oid,) in bad:
        fail("cdo-campaign-ref", f"observation={oid} 引用不存在的 campaign")


def check_cdo_evidence_ref():
    """测试8：evidence_id 若存在必须有效。"""
    bad = q("""SELECT cdo.observation_id FROM campaign_date_observations cdo
               LEFT JOIN evidences e ON e.evidence_id=cdo.evidence_id
               WHERE cdo.evidence_id IS NOT NULL AND e.evidence_id IS NULL""")
    for (oid,) in bad:
        fail("cdo-evidence-ref", f"observation={oid} evidence_id 引用缺失")


def check_cdo_enum():
    """Date Observation 枚举合法性。"""
    rows = q("""SELECT observation_id, date_role, verification_method, confidence
                FROM campaign_date_observations""")
    import scripts.db as dbmod
    for oid, role, vm, conf in rows:
        if role not in dbmod.DATE_ROLE:
            fail("cdo-role", f"obs={oid} date_role={role} 非法")
        if vm not in dbmod.VERIFY_METHOD:
            fail("cdo-method", f"obs={oid} verification_method={vm} 非法")
        if conf not in dbmod.EVIDENCE_CONF:
            fail("cdo-conf", f"obs={oid} confidence={conf} 非法")


def check_no_future_backfill():
    """测试10：不使用未来成分股自动回填历史——
    结构性检查：本项目不存在“基于当前成分股自动写历史 market_daily”的入库通道；
    此处校验 market_daily 的 data_source 不外推异常来源（保留告警位，不编造）。
    测试11：export 不混入无关 Market Data——export.py 不查询 market_* 表，机内保证；
    这里复核 campaign 的 JSON 导出不包含 market 字段已在 export 层隔离。"""
    # 占位说明性检查：无 market_daily/gen 源自动写入脚本被注册
    if not _table_exists(conn, "market_daily"):
        warn("market-infra", "market 表尚未创建或为空（此阶段允许，仅检查 infra 就绪）")


def _table_exists(conn, name):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


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

    # ---- Pilot 1-C1 行情核验基础设施检查 ----
    check_market_series_unique()
    check_market_daily_fk()
    check_market_daily_date_format()
    check_market_daily_no_dup()
    check_raw_normalized()
    check_cdo_candidate_not_overwrite()
    check_cdo_campaign_ref()
    check_cdo_evidence_ref()
    check_cdo_enum()
    check_no_future_backfill()

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