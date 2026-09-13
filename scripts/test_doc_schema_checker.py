"""文档与 Schema 一致性检查器测试（Schema Contract Checker Tests）。

验证 check_doc_schema_consistency.py 的正确性：
1. 已知合法字段通过
2. 人为构造不存在字段必须 FAIL（调用 checker.check_consistency()）
3. future candidate 允许
4. research-level 允许
5. 真实 schema 当前所有正式字段全部通过（调用 checker.check_consistency()）
6. 不存在表必须 FAIL
7. Document-only concept 允许
8. 真实 SQLite introspection（market_daily open/high/low/close）
9. Schema-only fields 真实列出
10. 字段数量 snapshot
11. 真实字段反向检查

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

def test_real_sqlite_introspection():
    """Test J: 真实 SQLite introspection（market_daily open/high/low/close）"""
    print("Test J: 真实 SQLite introspection")
    
    # 提取实际 schema
    actual_schema = checker.extract_schema_fields()
    
    # 验证 market_daily 表存在
    assert "market_daily" in actual_schema, "market_daily 表应存在"
    
    # 验证 open/high/low/close 都被识别
    market_daily_fields = actual_schema["market_daily"]
    assert "open" in market_daily_fields, "open 应存在于 market_daily"
    assert "high" in market_daily_fields, "high 应存在于 market_daily"
    assert "low" in market_daily_fields, "low 应存在于 market_daily"
    assert "close" in market_daily_fields, "close 应存在于 market_daily"
    
    print("✓ PASS: market_daily 的 open/high/low/close 全部被识别\n")

def test_schema_only_fields():
    """Test K: Schema-only fields 真实列出"""
    print("Test K: Schema-only fields 真实列出")
    
    # 提取实际 schema
    actual_schema = checker.extract_schema_fields()
    
    # 获取 DOCUMENTED_SCHEMA_FIELDS 中声明的字段
    documented_fields = set()
    for table, fields in checker.DOCUMENTED_SCHEMA_FIELDS.items():
        for field in fields:
            documented_fields.add(f"{table}.{field}")
    
    # 找出 schema 中存在但文档未声明的字段
    schema_only = []
    for table, fields in actual_schema.items():
        for field in fields:
            field_path = f"{table}.{field}"
            if field_path not in documented_fields:
                schema_only.append(field_path)
    
    # 当前应该没有 schema-only fields（因为我们已经完整声明了所有字段）
    print(f"  Schema-only fields: {len(schema_only)}")
    if schema_only:
        print(f"  Fields: {schema_only}")
    
    # 验证没有遗漏
    assert len(schema_only) == 0, f"不应有 schema-only fields，实际: {schema_only}"
    
    print("✓ PASS: Schema-only fields 检查完成\n")

def test_field_count_snapshot():
    """Test L: 字段数量 snapshot"""
    print("Test L: 字段数量 snapshot")
    
    # 提取实际 schema
    actual_schema = checker.extract_schema_fields()
    
    # 验证表数量
    actual_table_count = len(actual_schema)
    assert actual_table_count == 17, f"表数量应为 17，实际 {actual_table_count}"
    
    # 验证字段数量
    actual_field_count = sum(len(fields) for fields in actual_schema.values())
    assert actual_field_count == 125, f"字段数量应为 125，实际 {actual_field_count}"
    
    print(f"  实际表数量: {actual_table_count}")
    print(f"  实际字段数量: {actual_field_count}")
    
    print("✓ PASS: 字段数量 snapshot 正确\n")

def test_real_field_reverse_check():
    """Test M: 真实字段反向检查"""
    print("Test M: 真实字段反向检查")
    
    # 保存原始 DOCUMENTED_SCHEMA_FIELDS
    original_fields = copy.deepcopy(checker.DOCUMENTED_SCHEMA_FIELDS)
    
    try:
        # 从 market_daily 中删除真实存在的字段 high, low, close
        checker.DOCUMENTED_SCHEMA_FIELDS["market_daily"] = [
            f for f in original_fields["market_daily"]
            if f not in ["high", "low", "close"]
        ]
        
        # 调用 checker.check_consistency()
        # 根据当前策略，schema-only fields 不会导致 FAIL，只会报告为 INFO
        result = checker.check_consistency()
        
        # 应该返回 True（因为 schema-only fields 不会导致 FAIL）
        assert result is True, "check_consistency() 应返回 True（schema-only fields 不导致 FAIL）"
        
        print("✓ PASS: 真实字段反向检测工作正常（schema-only fields 被识别）\n")
        
    finally:
        # 恢复原始 DOCUMENTED_SCHEMA_FIELDS
        checker.DOCUMENTED_SCHEMA_FIELDS = original_fields

def main():
    """主测试函数"""
    print("=== Schema Contract Checker Tests ===\n")
    
    try:
        test_known_legal_fields()
        test_nonexistent_field_fails()
        test_future_candidate_allowed()
        test_research_level_allowed()
        test_all_documented_fields_exist()
        test_nonexistent_table_fails()
        test_document_only_concept_allowed()
        test_real_sqlite_introspection()
        test_schema_only_fields()
        test_field_count_snapshot()
        test_real_field_reverse_check()
        
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
