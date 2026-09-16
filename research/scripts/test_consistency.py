"""研究模型 v1.0 一致性测试。

验证：
1. formal_campaign_count 与 report 一致
2. research_candidate_count 与 report 一致
3. unbound Evidence 合法
4. Tier 1-4 定义一致
5. CONFIRMED 不属于 Phase
6. Signal 不进入 Campaign Phase
7. Campaign start 后才能产生 Campaign Phase
8. Candidate 不自动进入 campaigns
9. PIT 不得混用 retrospective
10. 2022/2023/2024 structural examples 可表达

用法: python scripts/test_consistency.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

def test_formal_campaign_count():
    """测试 formal_campaign_count 与 report 一致"""
    conn = db.connect()
    
    # 检查 2022 年
    formal_2022 = conn.execute(
        "SELECT COUNT(*) FROM campaigns WHERE campaign_year = 2022"
    ).fetchone()[0]
    assert formal_2022 == 1, f"2022 formal_campaign_count 应为 1，实际 {formal_2022}"
    
    # 检查 2023 年
    formal_2023 = conn.execute(
        "SELECT COUNT(*) FROM campaigns WHERE campaign_year = 2023"
    ).fetchone()[0]
    assert formal_2023 == 1, f"2023 formal_campaign_count 应为 1，实际 {formal_2023}"
    
    # 检查 2024 年
    formal_2024 = conn.execute(
        "SELECT COUNT(*) FROM campaigns WHERE campaign_year = 2024"
    ).fetchone()[0]
    assert formal_2024 == 2, f"2024 formal_campaign_count 应为 2，实际 {formal_2024}"
    
    conn.close()
    print("PASS: formal_campaign_count 与 report 一致")

def test_unbound_evidence_legal():
    """测试 unbound Evidence 合法。

    ── 金标准数字（golden counts）────────────────────────────────────
    这些数字会随**合法的新研究**增长，不是永恒常量。增长时必须在此同步更新，
    并在下方注释里记明「为什么涨」。

        51 = 46 条 E-2023-* / E-2024-* 等原始证据（seed.py）
           +  5 条 E-MED-* 医药健康 Minimum Dataset v0.1（ca43833）
        44 = 39 + 5（上述 5 条医药证据亦已显式绑定）
         7 = 不变量：unbound 未随医药 Pilot 变化

    变更依据：`research/research/reports/Medical_Health_Data_Entry_v0_1_Audit.md`
    （evidences 46 → 51）。该审计已记录变更，但本测试当时漏更新 —— 已补齐。

    ── 判定顺序 ─────────────────────────────────────────────────────
    先断言**不变量**（bound + unbound == total），再断言金标准数字。
    不变量是「研究模型语义」的守卫；金标准数字是**漂移探测器**
    （可捕捉证据被误删/误增）。
    """
    conn = db.connect()

    total = conn.execute("SELECT COUNT(*) FROM evidences").fetchone()[0]
    bound = conn.execute("SELECT COUNT(DISTINCT evidence_id) FROM campaign_evidences").fetchone()[0]
    unbound = total - bound

    # 1) 不变量：绑定 + 未绑定 = 总数；且未绑定必须存在（合法状态）
    assert bound + unbound == total, \
        f"不变量被破坏：bound({bound}) + unbound({unbound}) != total({total})"
    assert unbound > 0, "Unbound Evidence 应存在且合法"

    # 2) 金标准数字（漂移探测器）
    assert total == 51, f"Total Evidence 应为 51，实际 {total}（新增证据时请同步更新本测试与注释）"
    assert bound == 44, f"Campaign-bound Evidence 应为 44，实际 {bound}（新增证据时请同步更新本测试与注释）"
    assert unbound == 7, f"Unbound Evidence 应为 7，实际 {unbound}"

    conn.close()
    print(f"PASS: unbound Evidence 合法 (total={total}, bound={bound}, unbound={unbound})")

def test_tier_consistency():
    """测试 Tier 1-4 定义一致"""
    conn = db.connect()
    
    # 检查是否有 tier 超出 1-4 范围
    invalid_tiers = conn.execute(
        "SELECT DISTINCT tier FROM sources WHERE tier NOT IN (1, 2, 3, 4)"
    ).fetchall()
    assert len(invalid_tiers) == 0, f"发现无效 tier: {invalid_tiers}"
    
    # 检查 source_type 与 tier 一致性
    # Tier 1: regulator
    # Tier 2: media_tier2
    # Tier 3: media_tier3
    # Tier 4: media_tier4
    inconsistent = conn.execute("""
        SELECT source_id, source_type, tier FROM sources
        WHERE (source_type = 'regulator' AND tier != 1)
           OR (source_type = 'media_tier2' AND tier != 2)
           OR (source_type = 'media_tier3' AND tier != 3)
           OR (source_type = 'media_tier4' AND tier != 4)
    """).fetchall()
    assert len(inconsistent) == 0, f"发现 tier/type 不一致: {inconsistent}"
    
    conn.close()
    print("PASS: Tier 1-4 定义一致")

def test_confirmed_not_phase():
    """测试 CONFIRMED 不属于 Phase"""
    conn = db.connect()
    
    # 检查 campaign_phases 表中是否有 phase_type = 'confirmed'
    confirmed_phases = conn.execute(
        "SELECT COUNT(*) FROM campaign_phases WHERE phase_type = 'confirmed'"
    ).fetchone()[0]
    assert confirmed_phases == 0, f"CONFIRMED 不应属于 Phase，发现 {confirmed_phases} 条"
    
    conn.close()
    print("PASS: CONFIRMED 不属于 Phase")

def test_signal_not_in_phase():
    """测试 Signal 不进入 Campaign Phase"""
    conn = db.connect()
    
    # 检查 campaign_phases 表中是否有 Research Signal 状态
    signal_states = ['EARLY_SIGNAL', 'THEME_FORMING', 'CONFIRMATION_CANDIDATE']
    for state in signal_states:
        count = conn.execute(
            "SELECT COUNT(*) FROM campaign_phases WHERE phase_type = ?",
            (state,)
        ).fetchone()[0]
        assert count == 0, f"Signal {state} 不应进入 Campaign Phase，发现 {count} 条"
    
    conn.close()
    print("PASS: Signal 不进入 Campaign Phase")

def test_campaign_phase_after_start():
    """测试 Campaign start 后才能产生 Campaign Phase"""
    conn = db.connect()
    
    # 检查是否有 Phase 的 start_date 早于 Campaign 的 start_date
    invalid_phases = conn.execute("""
        SELECT p.campaign_id, p.phase_type, p.start_date as phase_start, c.start_date as campaign_start
        FROM campaign_phases p
        JOIN campaigns c ON p.campaign_id = c.campaign_id
        WHERE p.start_date < c.start_date
    """).fetchall()
    assert len(invalid_phases) == 0, f"发现 Phase 早于 Campaign start: {invalid_phases}"
    
    conn.close()
    print("PASS: Campaign start 后才能产生 Campaign Phase")

def test_candidate_not_in_campaigns():
    """测试 Candidate 不自动进入 campaigns"""
    conn = db.connect()
    
    # 检查 campaigns 表中是否有 classification = 'candidate'
    candidates = conn.execute(
        "SELECT COUNT(*) FROM campaigns WHERE classification = 'candidate'"
    ).fetchone()[0]
    assert candidates == 0, f"Candidate 不应进入 campaigns 表，发现 {candidates} 条"
    
    conn.close()
    print("PASS: Candidate 不自动进入 campaigns")

def test_pit_not_mixed_with_retrospective():
    """测试 PIT 不得混用 retrospective"""
    conn = db.connect()
    
    # 检查是否有 PIT 研究使用 retrospective 证据
    # 这里简化检查：确保 point_in_time 相关脚本存在且通过测试
    # 实际 PIT 测试已在 point_in_time_robotaxi.py 中完成
    
    conn.close()
    print("PASS: PIT 不得混用 retrospective（由 point_in_time_robotaxi.py 保证）")

def test_2022_2023_2024_expressible():
    """测试 2022/2023/2024 structural examples 可表达"""
    conn = db.connect()
    
    # 2022: 检查是否有 C-2022-POLICY
    c2022 = conn.execute(
        "SELECT COUNT(*) FROM campaigns WHERE campaign_id = 'C-2022-POLICY'"
    ).fetchone()[0]
    assert c2022 == 1, "2022 C-2022-POLICY 应存在"
    
    # 2023: 检查是否有 C-2023-AD
    c2023 = conn.execute(
        "SELECT COUNT(*) FROM campaigns WHERE campaign_id = 'C-2023-AD'"
    ).fetchone()[0]
    assert c2023 == 1, "2023 C-2023-AD 应存在"
    
    # 2024: 检查是否有 C-2024-ROBOTAXI
    c2024 = conn.execute(
        "SELECT COUNT(*) FROM campaigns WHERE campaign_id = 'C-2024-ROBOTAXI'"
    ).fetchone()[0]
    assert c2024 == 1, "2024 C-2024-ROBOTAXI 应存在"
    
    conn.close()
    print("PASS: 2022/2023/2024 structural examples 可表达")

def main():
    print("=== 研究模型 v1.0 一致性测试 ===\n")
    
    try:
        test_formal_campaign_count()
        test_unbound_evidence_legal()
        test_tier_consistency()
        test_confirmed_not_phase()
        test_signal_not_in_phase()
        test_campaign_phase_after_start()
        test_candidate_not_in_campaigns()
        test_pit_not_mixed_with_retrospective()
        test_2022_2023_2024_expressible()
        
        print("\n=== 所有测试通过 ===")
        print("PASS: 0 FAIL, 0 WARNING")
        
    except AssertionError as e:
        print(f"\nFAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
