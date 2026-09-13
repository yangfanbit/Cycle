"""文档与 Schema 一致性检查器测试。

验证 check_doc_schema_consistency.py 的正确性：
1. 已知合法字段通过
2. 人为构造不存在字段必须 FAIL（调用 checker.check_consistency()）
3. future candidate 允许
4. research-level 允许
5. 真实 schema 当前所有正式字段全部通过（调用 checker.check_consistency()）
6. 不存在表必须 FAIL
7. Document-only concept 允许

关键原则：
- 测试必须调用 checker.check_consistency()，而不是重复实现字段比较逻辑
- 使用 copy.deepcopy() 确保测试隔离
- 不调用 main()，直接调用 check_consistency()

用法: python scripts/test_doc_schema_checker.py
"""
import sys, os, copy
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
    """Test B: 人为构造不存在字段必须 FAIL（调用 checker.check_consistency()）"""
    print("Test B: 人为构造不存在字段")
    
    # 保存原始 DOCUMENTED_SCHEMA_FIELDS
    original_fields = copy.deepcopy(checker.DOCUMENTED_SCHEMA_FIELDS)
    
    try:
        # 添加一个不存在的字段
        checker.DOCUMENTED_SCHEMA_FIELDS["campaigns"] = (
            original_fields["campaigns"] + ["NON_EXISTENT_FIELD"]
        )
        
        # 调用 checker.check_consistency()，应该返回 False
        result = checker.check_consistency()
        
        assert result is False, "check_consistency() 应返回 False（检测到不存在字段）"
        print("✓ PASS: 不存在字段被正确检测（check_consistency() 返回 False）\n")
        
    finally:
        # 恢复原始 DOCUMENTED_SCHEMA_FIELDS
        checker.DOCUMENTED_SCHEMA_FIELDS = original_fields

def test_future_candidate_allowed():
    """Test C: future candidate 允许"""
    print("Test C: future candidate 允许")
    
    # rule_type 是 future candidate，应该在 DOCUMENT_ONLY_CONCEPTS 中
    assert "rule_type" in checker.DOCUMENT_ONLY_CONCEPTS, "rule_type 应在 DOCUMENT_ONLY_CONCEPTS 中"
    
    # 调用 checker.check_consistency()，应该返回 True（rule_type 被允许）
    result = checker.check_consistency()
    
    assert result is True, "check_consistency() 应返回 True（rule_type 作为 future candidate 被允许）"
    print("✓ PASS: future candidate 被正确允许\n")

def test_research_level_allowed():
    """Test D: research-level 允许"""
    print("Test D: research-level 允许")
    
    # campaign_status 和 security_type 是 research-level，应该在 DOCUMENT_ONLY_CONCEPTS 中
    assert "campaign_status" in checker.DOCUMENT_ONLY_CONCEPTS, "campaign_status 应在 DOCUMENT_ONLY_CONCEPTS 中"
    assert "security_type" in checker.DOCUMENT_ONLY_CONCEPTS, "security_type 应在 DOCUMENT_ONLY_CONCEPTS 中"
    
    # 调用 checker.check_consistency()，应该返回 True（这些概念被允许）
    result = checker.check_consistency()
    
    assert result is True, "check_consistency() 应返回 True（research-level 概念被允许）"
    print("✓ PASS: research-level 概念被正确允许\n")

def test_all_documented_fields_exist():
    """Test E: 真实 schema 当前所有正式字段全部通过（调用 checker.check_consistency()）"""
    print("Test E: 所有文档字段存在性验证")
    
    # 调用 checker.check_consistency()，应该返回 True（所有字段都存在）
    result = checker.check_consistency()
    
    assert result is True, "check_consistency() 应返回 True（所有文档字段都存在于 schema）"
    print("✓ PASS: 所有文档字段都存在于 schema（check_consistency() 返回 True）\n")

def test_nonexistent_table_fails():
    """Test F: 不存在表必须 FAIL"""
    print("Test F: 不存在表")
    
    # 保存原始 DOCUMENTED_SCHEMA_FIELDS
    original_fields = copy.deepcopy(checker.DOCUMENTED_SCHEMA_FIELDS)
    
    try:
        # 添加一个不存在的表
        checker.DOCUMENTED_SCHEMA_FIELDS["NON_EXISTENT_TABLE"] = ["field1", "field2"]
        
        # 调用 checker.check_consistency()，应该返回 False
        result = checker.check_consistency()
        
        assert result is False, "check_consistency() 应返回 False（检测到不存在表）"
        print("✓ PASS: 不存在表被正确检测（check_consistency() 返回 False）\n")
        
    finally:
        # 恢复原始 DOCUMENTED_SCHEMA_FIELDS
        checker.DOCUMENTED_SCHEMA_FIELDS = original_fields

def test_document_only_concept_allowed():
    """Test G: Document-only concept 允许"""
    print("Test G: Document-only concept 允许")
    
    # 保存原始 DOCUMENTED_SCHEMA_FIELDS
    original_fields = copy.deepcopy(checker.DOCUMENTED_SCHEMA_FIELDS)
    
    try:
        # 添加一个 document-only concept 到 campaigns 表
        # rule_type 是 document-only concept，应该被允许
        checker.DOCUMENTED_SCHEMA_FIELDS["campaigns"] = (
            original_fields["campaigns"] + ["rule_type"]
        )
        
        # 调用 checker.check_consistency()，应该返回 True（rule_type 是 document-only concept）
        result = checker.check_consistency()
        
        assert result is True, "check_consistency() 应返回 True（rule_type 作为 document-only concept 被允许）"
        print("✓ PASS: Document-only concept 被正确允许\n")
        
    finally:
        # 恢复原始 DOCUMENTED_SCHEMA_FIELDS
        checker.DOCUMENTED_SCHEMA_FIELDS = original_fields

def test_schema_extraction():
    """Test H: Schema 提取正确性"""
    print("Test H: Schema 提取正确性")
    
    actual_schema = checker.extract_schema_fields()
    
    # 验证提取的表数量
    assert len(actual_schema) >= 17, f"应至少提取 17 个表，实际 {len(actual_schema)}"
    
    # 验证关键表存在
    key_tables = ["research_rules", "campaigns", "evidences", "market_series", "market_daily"]
    for table in key_tables:
        assert table in actual_schema, f"{table} 应被提取"
    
    print(f"✓ PASS: Schema 提取正确，共 {len(actual_schema)} 个表\n")

def test_documented_fields_count():
    """Test I: 文档字段数量统计"""
    print("Test I: 文档字段数量统计")
    
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
        test_nonexistent_table_fails()
        test_document_only_concept_allowed()
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
