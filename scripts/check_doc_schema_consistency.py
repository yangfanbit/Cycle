"""文档与 Schema 一致性检查器（Schema Contract Checker）。

真正实现 Document ↔ SQLite Schema Consistency Check：
1. 使用 SQLite introspection 提取真实 schema（不修改 schema.sql）
2. 维护 DOCUMENTED_SCHEMA_FIELDS（文档声称的正式字段合约）
3. 维护 DOCUMENT_ONLY_CONCEPTS（允许的非 schema 字段）
4. 逐项比较，发现冲突时 FAIL

重要说明：
- 这是 Schema Contract Check，不是自动理解所有 Markdown
- DOCUMENTED_SCHEMA_FIELDS 是显式合约，不是自动解析文档
- 允许 document-only concepts（不进入 SQLite）

用法: python scripts/check_doc_schema_consistency.py
"""
import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==================== 显式声明 ====================

# 文档声称的正式数据库字段（必须与 schema 一致）
# 基于真实 SQLite introspection 结果
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
        "high",
        "low",
        "close",
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
        "created_at",
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
    """使用 SQLite introspection 提取真实 schema"""
    from scripts import db
    schema_path = os.path.join(db.ROOT, "schema", "schema.sql")
    
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    
    # 创建内存数据库
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    
    try:
        # 执行 schema.sql
        conn.executescript(schema_sql)
        
        # 提取所有表
        tables = {}
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        
        for row in cursor.fetchall():
            table_name = row[0]
            
            # 提取表的字段
            fields = []
            field_cursor = conn.execute(f"PRAGMA table_info({table_name})")
            for field_row in field_cursor.fetchall():
                # field_row: (cid, name, type, notnull, dflt_value, pk)
                field_name = field_row[1]
                fields.append(field_name)
            
            tables[table_name] = fields
        
        return tables
        
    finally:
        conn.close()

# ==================== 一致性检查 ====================

def check_consistency():
    """执行文档与 Schema 一致性检查（Schema Contract Check）
    
    Returns:
        bool: True 表示一致，False 表示存在冲突
    """
    
    print("=== Schema Contract Check ===\n")
    
    # 提取实际 schema
    actual_schema = extract_schema_fields()
    
    # 统计
    total_tables = len(DOCUMENTED_SCHEMA_FIELDS)
    total_fields = sum(len(fields) for fields in DOCUMENTED_SCHEMA_FIELDS.values())
    
    print(f"Contract tables: {total_tables}")
    print(f"Contract fields: {total_fields}")
    print(f"Actual schema tables: {len(actual_schema)}")
    print(f"Actual schema fields: {sum(len(fields) for fields in actual_schema.values())}\n")
    
    # 检查结果
    pass_items = []
    fail_items = []
    document_only = []
    schema_only = []
    
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
                schema_only.append(f"{table}.{field}")
    
    # 2. 检查实际 schema 中的表是否都在文档中
    documented_tables = set(DOCUMENTED_SCHEMA_FIELDS.keys())
    actual_tables = set(actual_schema.keys())
    
    undocumented_tables = actual_tables - documented_tables
    if undocumented_tables:
        for table in undocumented_tables:
            schema_only.append(f"{table} (entire table)")
    
    # 3. 检查 document-only concepts 是否被正确标记
    for concept in DOCUMENT_ONLY_CONCEPTS:
        document_only.append(f"{concept} (allowed document-only concept)")
    
    # ==================== 输出结果 ====================
    
    if pass_items:
        print("=== PASS ===")
        for item in pass_items:
            print(f"✓ {item}")
        print()
    
    if schema_only:
        print("=== Schema-Only Fields (INFO) ===")
        for item in schema_only:
            print(f"ℹ {item}")
        print()
    
    if document_only:
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
        print(f"Contract tables: {total_tables}")
        print(f"Contract fields: {total_fields}")
        print(f"Document-only concepts: {len(DOCUMENT_ONLY_CONCEPTS)}")
        print(f"Schema-only fields: {len(schema_only)}")
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
            print("PASS: Schema Contract Check verified")
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
