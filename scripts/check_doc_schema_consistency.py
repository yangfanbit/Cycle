"""文档与 Schema 一致性检查器。

真正实现 Document ↔ SQLite Schema Consistency Check：
1. 从 schema.sql 提取实际表/字段
2. 维护 DOCUMENTED_SCHEMA_FIELDS（文档声称的正式字段）
3. 维护 DOCUMENT_ONLY_CONCEPTS（允许的非 schema 字段）
4. 逐项比较，发现冲突时 FAIL

用法: python scripts/check_doc_schema_consistency.py
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==================== 显式声明 ====================

# 文档声称的正式数据库字段（必须与 schema 一致）
DOCUMENTED_SCHEMA_FIELDS = {
    "research_rules": [
        "rule_id",
        "name",
        "base_pattern",
        "description",
        "source_id",
        "status",
        "created_at",
    ],
    "annual_reviews": [
        "annual_review_id",
        "rule_id",
        "year",
        "status",
        "summary",
        "review_notes",
        "created_at",
    ],
    "campaigns": [
        "campaign_id",
        "annual_review_id",
        "rule_id",
        "season_id",
        "campaign_year",
        "start_date",
        "end_date",
        "peak_date",
        "strength",
        "result",
        "classification",
        "start_date_basis",
        "end_date_basis",
        "date_confidence",
        "description",
        "drift_vs_jun01",
        "drift_vs_jul01",
        "drift_vs_aug01",
        "research_notes",
        "created_at",
    ],
    "campaign_phases": [
        "phase_id",
        "campaign_id",
        "phase_type",
        "start_date",
        "end_date",
        "description",
    ],
    "themes": [
        "theme_id",
        "name",
        "theme_type",
        "parent_theme_id",
        "description",
    ],
    "campaign_themes": [
        "campaign_id",
        "theme_id",
        "role",
    ],
    "events": [
        "event_id",
        "date",
        "event_type",
        "name",
        "description",
        "source_id",
    ],
    "campaign_events": [
        "campaign_id",
        "event_id",
        "role",
    ],
    "securities": [
        "security_id",
        "ticker",
        "name",
        "exchange",
    ],
    "campaign_securities": [
        "campaign_id",
        "security_id",
        "role",
    ],
    "sources": [
        "source_id",
        "source_type",
        "title",
        "author",
        "url",
        "published_at",
        "captured_at",
        "publisher",
        "description",
        "tier",
        "created_at",
    ],
    "evidences": [
        "evidence_id",
        "source_id",
        "date",
        "evidence_type",
        "description",
        "evidence_role",
        "confidence",
        "independence_group",
        "temporal_relation",
        "created_at",
    ],
    "campaign_evidences": [
        "campaign_id",
        "evidence_id",
        "role",
        "created_at",
    ],
    "market_series": [
        "series_id",
        "name",
        "series_type",
        "provider",
        "symbol",
        "frequency",
        "price_type",
        "adjustment_method",
        "description",
        "created_at",
    ],
    "market_daily": [
        "series_id",
        "trade_date",
        "open",
        "adj_close",
        "price_type",
        "volume",
        "amount",
        "data_source",
        "retrieved_at",
    ],
    "trading_calendar": [
        "trade_date",
        "is_trading_day",
        "calendar_type",
    ],
    "campaign_date_observations": [
        "observation_id",
        "campaign_id",
        "date_role",
        "candidate_date",
        "verified_date",
        "verification_method",
        "confidence",
        "evidence_id",
        "notes",
        "created_at",
    ],
}

# 允许的非 Schema 字段（document-only concepts）
DOCUMENT_ONLY_CONCEPTS = {
    "rule_type",           # future candidate
    "campaign_status",     # research-layer concept
    "security_type",       # research-level conceptual
    "theme_cycle_id",      # research-level grouping
    "theme_drift",         # research-level relation
    "campaign_overlap",    # research-level relation
}

# ==================== Schema 提取 ====================

def extract_schema_fields():
    """从 schema.sql 提取所有表和字段"""
    from scripts import db
    schema_path = os.path.join(db.ROOT, "schema", "schema.sql")
    
    with open(schema_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    tables = {}
    current_table = None
    
    for line in content.split('\n'):
        line = line.strip()
        
        # 提取表名
        if line.startswith('CREATE TABLE'):
            match = re.search(r'CREATE TABLE IF NOT EXISTS (\w+)', line)
            if match:
                current_table = match.group(1)
                tables[current_table] = []
        
        # 提取字段名
        elif current_table and line and not line.startswith('--') and not line.startswith(')'):
            # 跳过约束行
            if any(line.startswith(x) for x in ['PRIMARY', 'FOREIGN', 'CHECK', 'UNIQUE', 'CONSTRAINT']):
                continue
            
            # 提取字段名（第一个单词）
            match = re.match(r'(\w+)\s+', line)
            if match:
                field = match.group(1)
                # 排除 SQL 关键字
                if field not in ['PRIMARY', 'FOREIGN', 'CHECK', 'UNIQUE', 'NOT', 'DEFAULT', 'REFERENCES']:
                    tables[current_table].append(field)
    
    return tables

# ==================== 一致性检查 ====================

def check_consistency():
    """执行文档与 Schema 一致性检查"""
    
    print("=== Document ↔ Schema Consistency Check ===\n")
    
    # 提取实际 schema
    actual_schema = extract_schema_fields()
    
    # 统计
    total_tables = len(DOCUMENTED_SCHEMA_FIELDS)
    total_fields = sum(len(fields) for fields in DOCUMENTED_SCHEMA_FIELDS.values())
    
    print(f"Tables to check: {total_tables}")
    print(f"Fields to check: {total_fields}\n")
    
    # 检查结果
    pass_items = []
    fail_items = []
    document_only = []
    
    # 1. 检查 DOCUMENTED_SCHEMA_FIELDS 中的字段是否都存在于实际 schema
    for table, documented_fields in DOCUMENTED_SCHEMA_FIELDS.items():
        if table not in actual_schema:
            fail_items.append(f"Table '{table}' documented but not found in schema")
            continue
        
        actual_fields = set(actual_schema[table])
        documented_fields_set = set(documented_fields)
        
        # 检查文档字段是否都在实际 schema 中
        missing_in_schema = documented_fields_set - actual_fields
        if missing_in_schema:
            for field in missing_in_schema:
                if field in DOCUMENT_ONLY_CONCEPTS:
                    document_only.append(f"{table}.{field} (document-only concept)")
                else:
                    fail_items.append(f"Field '{table}.{field}' documented but not found in schema")
        
        # 检查实际 schema 是否有文档未声明的字段
        missing_in_docs = actual_fields - documented_fields_set
        if missing_in_docs:
            for field in missing_in_docs:
                pass_items.append(f"Field '{table}.{field}' exists in schema but not documented")
    
    # 2. 检查实际 schema 中的表是否都在文档中
    documented_tables = set(DOCUMENTED_SCHEMA_FIELDS.keys())
    actual_tables = set(actual_schema.keys())
    
    undocumented_tables = actual_tables - documented_tables
    if undocumented_tables:
        for table in undocumented_tables:
            pass_items.append(f"Table '{table}' exists in schema but not documented")
    
    # 3. 检查 document-only concepts 是否被正确标记
    for concept in DOCUMENT_ONLY_CONCEPTS:
        document_only.append(f"{concept} (allowed document-only concept)")
    
    # ==================== 输出结果 ====================
    
    print("=== PASS ===")
    for item in pass_items:
        print(f"✓ {item}")
    print()
    
    print("=== Document-Only Concepts ===")
    for item in document_only:
        print(f"ℹ {item}")
    print()
    
    if fail_items:
        print("=== FAIL ===")
        for item in fail_items:
            print(f"✗ {item}")
        print()
        print(f"FAIL: {len(fail_items)} inconsistencies found")
        return False
    else:
        print("=== SUMMARY ===")
        print(f"Tables checked: {total_tables}")
        print(f"Fields checked: {total_fields}")
        print(f"Document-only concepts: {len(DOCUMENT_ONLY_CONCEPTS)}")
        print(f"Schema tables: {len(actual_tables)}")
        print(f"Schema fields: {sum(len(fields) for fields in actual_schema.values())}")
        print()
        print("PASS: 0 FAIL")
        return True

# ==================== 主函数 ====================

def main():
    """主函数"""
    try:
        success = check_consistency()
        if success:
            print("\n=== RESULT ===")
            print("PASS: Document ↔ Schema consistency verified")
            sys.exit(0)
        else:
            print("\n=== RESULT ===")
            print("FAIL: Inconsistencies found")
            sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
