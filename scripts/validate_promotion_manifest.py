"""Promotion Manifest 验证脚本。

验证 promotion_manifest.json 的正确性：
1. campaign 存在
1b. manifest 字段与 DB campaign 行一致（含 cross_year 计算校验）
2. rule 存在
3. dates 合法
4. source 存在
5. evidence 存在
6. evidence 不跨 Campaign
7. independent groups >= 2
8. reviewer/reviewed_at 关系合法
9. research candidate 不得标 READY_FOR_PROMOTION
10. 未解决 mapping 不得 READY_FOR_PROMOTION

用法: python scripts/validate_promotion_manifest.py
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

def load_manifest():
    """加载 promotion manifest"""
    manifest_path = os.path.join(db.ROOT, "research", "promotion", "promotion_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_campaign_exists(campaign_id):
    """验证 campaign 存在"""
    conn = db.connect()
    cursor = conn.execute(
        "SELECT COUNT(*) FROM campaigns WHERE campaign_id = ?",
        (campaign_id,)
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def validate_campaign_matches_db(campaign):
    """验证 manifest 字段与 DB campaign 行一致（仅正式 Campaign，RC 除外）"""
    campaign_id = campaign.get("research_campaign_id")
    if campaign_id.startswith("RC-"):
        return True, None  # Research Candidate 不在 DB 中，跳过

    conn = db.connect()
    cursor = conn.execute(
        "SELECT rule_id, season_id, campaign_year, start_date, end_date, peak_date, "
        "strength, result, classification, date_confidence "
        "FROM campaigns WHERE campaign_id = ?",
        (campaign_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False, f"Campaign '{campaign_id}' 不存在于 DB"

    db_values = {
        "rule_id": row[0],
        "season_id": row[1],
        "campaign_year": row[2],
        "start_date": row[3],
        "end_date": row[4],
        "peak_date": row[5],
        "strength": row[6],
        "result": row[7],
        "classification": row[8],
        "date_confidence": row[9],
    }

    mismatches = []
    for field, db_value in db_values.items():
        manifest_value = campaign.get(field)
        if manifest_value != db_value:
            mismatches.append(
                f"{field}: manifest='{manifest_value}' != DB='{db_value}'"
            )

    if mismatches:
        return False, "manifest 与 DB 不一致: " + "; ".join(mismatches)

    # cross_year 必须由 promotion layer 计算且正确
    start_date = campaign.get("start_date")
    end_date = campaign.get("end_date")
    if start_date and end_date:
        expected_cross_year = int(end_date[:4]) > int(start_date[:4])
        if campaign.get("cross_year") != expected_cross_year:
            return False, (
                f"cross_year 计算错误: manifest={campaign.get('cross_year')} "
                f"!= 计算值={expected_cross_year}"
            )

    return True, None

def validate_rule_exists(rule_id):
    """验证 rule 存在"""
    conn = db.connect()
    cursor = conn.execute(
        "SELECT COUNT(*) FROM research_rules WHERE rule_id = ?",
        (rule_id,)
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def validate_dates(start_date, end_date, peak_date):
    """验证日期合法"""
    if not start_date:
        return False, "start_date 不能为空"
    
    if end_date and start_date > end_date:
        return False, f"start_date ({start_date}) 不能晚于 end_date ({end_date})"
    
    if peak_date and (peak_date < start_date or (end_date and peak_date > end_date)):
        return False, f"peak_date ({peak_date}) 必须在 start_date 和 end_date 之间"
    
    return True, None

def validate_source_exists(source_id):
    """验证 source 存在"""
    if not source_id:
        return False, "source_id 不能为空"
    
    conn = db.connect()
    cursor = conn.execute(
        "SELECT COUNT(*) FROM sources WHERE source_id = ?",
        (source_id,)
    )
    count = cursor.fetchone()[0]
    conn.close()
    
    if count == 0:
        return False, f"source_id '{source_id}' 不存在"
    
    return True, None

def validate_evidence_exists(evidence_ids):
    """验证 evidence 存在"""
    if not evidence_ids:
        return False, "evidence_ids 不能为空"
    
    conn = db.connect()
    for evidence_id in evidence_ids:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM evidences WHERE evidence_id = ?",
            (evidence_id,)
        )
        count = cursor.fetchone()[0]
        if count == 0:
            conn.close()
            return False, f"evidence_id '{evidence_id}' 不存在"
    
    conn.close()
    return True, None

def validate_evidence_not_cross_campaign(campaign_id, evidence_ids):
    """验证 evidence 不跨 Campaign"""
    if not evidence_ids:
        return False, "evidence_ids 不能为空"
    
    conn = db.connect()
    for evidence_id in evidence_ids:
        cursor = conn.execute(
            "SELECT campaign_id FROM campaign_evidences WHERE evidence_id = ?",
            (evidence_id,)
        )
        rows = cursor.fetchall()
        for row in rows:
            if row[0] != campaign_id:
                conn.close()
                return False, f"evidence_id '{evidence_id}' 跨 Campaign（属于 {row[0]}）"
    
    conn.close()
    return True, None

def validate_independent_groups(independent_evidence_groups):
    """验证 independent groups >= 2"""
    if not independent_evidence_groups:
        return False, "independent_evidence_groups 不能为空"
    
    if len(independent_evidence_groups) < 2:
        return False, f"independent_evidence_groups 数量不足（{len(independent_evidence_groups)} < 2）"
    
    return True, None

def validate_reviewer_status(promotion_status, reviewer, reviewed_at):
    """验证 reviewer/reviewed_at 关系合法"""
    if promotion_status == "READY_FOR_PROMOTION":
        if reviewer == "pending" or not reviewer:
            return False, "READY_FOR_PROMOTION 要求 reviewer 已填写"
        
        if not reviewed_at:
            return False, "READY_FOR_PROMOTION 要求 reviewed_at 已填写"
    
    return True, None

def validate_research_candidate_status(research_campaign_id, promotion_status):
    """验证 research candidate 不得标 READY_FOR_PROMOTION"""
    if research_campaign_id.startswith("RC-"):
        if promotion_status == "READY_FOR_PROMOTION":
            return False, f"Research Candidate ({research_campaign_id}) 不得标 READY_FOR_PROMOTION"
    
    return True, None

def validate_mapping_complete(campaign):
    """验证 mapping 完整"""
    # 检查是否有 mapping_required 标记
    if campaign.get("mapping_required"):
        return False, "存在未解决的 mapping"
    
    return True, None

def validate_manifest():
    """验证 promotion manifest"""
    print("=== Promotion Manifest Validation ===\n")
    
    manifest = load_manifest()
    campaigns = manifest.get("campaigns", [])
    
    if not campaigns:
        print("FAIL: manifest 中没有 campaigns")
        return False
    
    all_pass = True
    results = []
    
    for campaign in campaigns:
        campaign_id = campaign.get("research_campaign_id")
        promotion_status = campaign.get("promotion_status")
        
        print(f"Checking {campaign_id} ({promotion_status})...")
        
        errors = []
        
        # 1. campaign 存在
        if not validate_campaign_exists(campaign_id):
            if not campaign_id.startswith("RC-"):  # Research Candidate 可以不存在
                errors.append(f"Campaign '{campaign_id}' 不存在")

        # 1b. manifest 字段与 DB campaign 行一致（含 cross_year 计算校验）
        valid, error = validate_campaign_matches_db(campaign)
        if not valid:
            errors.append(error)
        
        # 2. rule 存在
        rule_id = campaign.get("rule_id")
        if not validate_rule_exists(rule_id):
            errors.append(f"Rule '{rule_id}' 不存在")
        
        # 3. dates 合法
        start_date = campaign.get("start_date")
        end_date = campaign.get("end_date")
        peak_date = campaign.get("peak_date")
        valid, error = validate_dates(start_date, end_date, peak_date)
        if not valid:
            errors.append(error)
        
        # 4. source 存在
        source_id = campaign.get("source_id")
        valid, error = validate_source_exists(source_id)
        if not valid:
            # Source 可以不存在（研究候选）
            if not campaign_id.startswith("RC-"):
                errors.append(error)
        
        # 5. evidence 存在
        evidence_ids = campaign.get("evidence_ids", [])
        if evidence_ids:  # 只有非空才验证
            valid, error = validate_evidence_exists(evidence_ids)
            if not valid:
                errors.append(error)
        
        # 6. evidence 不跨 Campaign
        if evidence_ids:
            valid, error = validate_evidence_not_cross_campaign(campaign_id, evidence_ids)
            if not valid:
                errors.append(error)
        
        # 7. independent groups >= 2
        independent_evidence_groups = campaign.get("independent_evidence_groups", [])
        if promotion_status == "READY_FOR_PROMOTION":
            valid, error = validate_independent_groups(independent_evidence_groups)
            if not valid:
                errors.append(error)
        
        # 8. reviewer/reviewed_at 关系合法
        reviewer = campaign.get("reviewer")
        reviewed_at = campaign.get("reviewed_at")
        valid, error = validate_reviewer_status(promotion_status, reviewer, reviewed_at)
        if not valid:
            errors.append(error)
        
        # 9. research candidate 不得标 READY_FOR_PROMOTION
        valid, error = validate_research_candidate_status(campaign_id, promotion_status)
        if not valid:
            errors.append(error)
        
        # 10. 未解决 mapping 不得 READY_FOR_PROMOTION
        if promotion_status == "READY_FOR_PROMOTION":
            valid, error = validate_mapping_complete(campaign)
            if not valid:
                errors.append(error)
        
        if errors:
            all_pass = False
            print(f"  ✗ FAIL: {len(errors)} errors")
            for error in errors:
                print(f"    - {error}")
            results.append({
                "campaign_id": campaign_id,
                "status": "FAIL",
                "errors": errors
            })
        else:
            print(f"  ✓ PASS")
            results.append({
                "campaign_id": campaign_id,
                "status": "PASS",
                "errors": []
            })
        
        print()
    
    # 总结
    print("=== SUMMARY ===")
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed
    
    print(f"Total campaigns: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()
    
    if all_pass:
        print("PASS: All campaigns validated successfully")
        return True
    else:
        print("FAIL: Some campaigns failed validation")
        return False

def main():
    """主函数"""
    try:
        success = validate_manifest()
        if success:
            print("\n=== RESULT ===")
            print("PASS: Promotion manifest validation completed")
            sys.exit(0)
        else:
            print("\n=== RESULT ===")
            print("FAIL: Promotion manifest validation failed")
            sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
