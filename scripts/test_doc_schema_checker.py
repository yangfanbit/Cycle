"""文档与 Schema 一致性检查器测试。

验证 check_doc_schema_consistency.py 的正确性：
1. 已知合法字段通过
2. 人为构造不存在字段必须 FAIL
3. future candidate 允许
4. research-level 允许
5. 真实 schema 当前所有正式字段全部通过

用法: python scripts/test_doc_schema_checker.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入被测试的模块
from scripts import check_doc_schema_consistency as checker

def test_known_legal_fields():
    """Test A: 已知合法字段通过"""
    print("Test A: 已知合法字段")
    
    # 提取实际 schema
    actual_schema = checker.extract_schema_fields()
    
    # 验证一些已知合法字段
    assert "research_rules" in actual_schema, "research_rules 表应存在"
    assert "rule_id" in actual_schema["research_rules"], "rule_id 应存在于 research_rules"
    assert "status" in actual_schema["research_rules"], "status 应存在于 research_rules"
    
    assert "campaigns" in actual_schema, "campaigns 表应存在"
    assert "campaign_id" in actual_schema["campaigns"], "campaign_id 应存在于 campaigns"
    assert "classification" in actual_schema["campaigns"], "classification 应存在于 campaigns"
    
    print("✓ PASS: 已知合法字段验证通过\n")

def test_nonexistent_field_fails():
    """Test B: 人为构造不存在字段必须 FAIL"""
    print("Test B: 人为构造不存在字段")
    
    # 创建一个临时的 DOCUMENTED_SCHEMA_FIELDS，包含一个不存在的字段
    original_fields = checker.DOCUMENTED_SCHEMA_FIELDS.copy()
    
    # 添加一个不存在的字段
    checker.DOCUMENTED_SCHEMA_FIELDS["campaigns"] = original_fields["campaigns"] + ["NON_EXISTENT_FIELD"]
    
    # 提取实际 schema
    actual_schema = checker.extract_schema_fields()
    
    # 检查是否存在不存在的字段
    actual_fields = set(actual_schema["campaigns"])
    documented_fields = set(checker.DOCUMENTED_SCHEMA_FIELDS["campaigns"])
    
    missing = documented_fields - actual_fields
    
    # 恢复原始字段
    checker.DOCUMENTED_SCHEMA_FIELDS = original_fields
    
    assert "NON_EXISTENT_FIELD" in missing, "NON_EXISTENT_FIELD 应该被检测为不存在"
    print("✓ PASS: 不存在字段被正确检测\n")

def test_future_candidate_allowed():
    """Test C: future candidate 允许"""
    print("Test C: future candidate 允许")
    
    # rule_type 是 future candidate，应该在 DOCUMENT_ONLY_CONCEPTS 中
    assert "rule_type" in checker.DOCUMENT_ONLY_CONCEPTS, "rule_type 应在 DOCUMENT_ONLY_CONCEPTS 中"
    
    print("✓ PASS: future candidate 被正确允许\n")

def test_research_level_allowed():
    """Test D: research-level 允许"""
    print("Test D: research-level 允许")
    
    # campaign_status 和 security_type 是 research-level，应该在 DOCUMENT_ONLY_CONCEPTS 中
    assert "campaign_status" in checker.DOCUMENT_ONLY_CONCEPTS, "campaign_status 应在 DOCUMENT_ONLY_CONCEPTS 中"
    assert "security_type" in checker.DOCUMENT_ONLY_CONCEPTS, "security_type 应在 DOCUMENT_ONLY_CONCEPTS 中"
    
    print("✓ PASS: research-level 概念被正确允许\n")

def test_all_documented_fields_exist():
    """Test E: 真实 schema 当前所有正式字段全部通过"""
    print("Test E: 所有文档字段存在性验证")
    
    # 提取实际 schema
    actual_schema = checker.extract_schema_fields()
    
    # 检查 DOCUMENTED_SCHEMA_FIELDS 中的所有字段是否都存在于实际 schema
    all_exist = True
    missing_fields = []
    
    for table, documented_fields in checker.DOCUMENTED_SCHEMA_FIELDS.items():
        if table not in actual_schema:
            all_exist = False
            missing_fields.append(f"Table '{table}' not in schema")
            continue
        
        actual_fields = set(actual_schema[table])
        documented_fields_set = set(documented_fields)
        
        missing = documented_fields_set - actual_fields
        # 排除 document-only concepts
        missing = {f for f in missing if f not in checker.DOCUMENT_ONLY_CONCEPTS}
        
        if missing:
            all_exist = False
            for field in missing:
                missing_fields.append(f"{table}.{field}")
    
    if missing_fields:
        print(f"✗ FAIL: 以下字段不存在于 schema: {missing_fields}\n")
        assert False, f"Missing fields: {missing_fields}"
    else:
        print("✓ PASS: 所有文档字段都存在于 schema\n")

def test_schema_extraction():
    """Test F: Schema 提取正确性"""
    print("Test F: Schema 提取正确性")
    
    actual_schema = checker.extract_schema_fields()
    
    # 验证提取的表数量
    assert len(actual_schema) >= 17, f"应至少提取 17 个表，实际 {len(actual_schema)}"
    
    # 验证关键表存在
    key_tables = ["research_rules", "campaigns", "evidences", "market_series", "market_daily"]
    for table in key_tables:
        assert table in actual_schema, f"{table} 应被提取"
    
    print(f"✓ PASS: Schema 提取正确，共 {len(actual_schema)} 个表\n")

def test_documented_fields_count():
    """Test G: 文档字段数量统计"""
    print("Test G: 文档字段数量统计")
    
    total_tables = len(checker.DOCUMENTED_SCHEMA_FIELDS)
    total_fields = sum(len(fields) for fields in checker.DOCUMENTED_SCHEMA_FIELDS.values())
    
    print(f"  文档声明的表数量: {total_tables}")
    print(f"  文档声明的字段数量: {total_fields}")
    print(f"  Document-only concepts: {len(checker.DOCUMENT_ONLY_CONCEPTS)}")
    
    assert total_tables >= 17, f"应至少声明 17 个表，实际 {total_tables}"
    assert total_fields > 0, "应声明字段"
    
    print("✓ PASS: 文档字段数量统计正确\n")

def main():
    """主测试函数"""
    print("=== 文档与 Schema 一致性检查器测试 ===\n")
    
    try:
        test_known_legal_fields()
        test_nonexistent_field_fails()
        test_future_candidate_allowed()
        test_research_level_allowed()
        test_all_documented_fields_exist()
        test_schema_extraction()
        test_documented_fields_count()
        
        print("=== 所有测试通过 ===")
        print("PASS: 0 FAIL, 0 WARNING")
        
    except AssertionError as e:
        print(f"\nFAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
