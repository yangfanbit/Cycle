"""Schema Snapshot：使用 SQLite introspection 提取真实 schema。

不修改 schema.sql，仅在内存中执行以提取表结构。

用法: python scripts/schema_snapshot.py
"""
import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def extract_schema_via_sqlite():
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

def print_snapshot(tables):
    """打印 schema snapshot"""
    print("=== SQLite Schema Snapshot ===\n")
    
    total_tables = len(tables)
    total_fields = sum(len(fields) for fields in tables.values())
    
    print(f"Total tables: {total_tables}")
    print(f"Total fields: {total_fields}\n")
    
    for table_name in sorted(tables.keys()):
        fields = tables[table_name]
        print(f"{table_name}:")
        print(f"  Field count: {len(fields)}")
        print(f"  Fields: {', '.join(fields)}")
        print()

def main():
    """主函数"""
    try:
        tables = extract_schema_via_sqlite()
        print_snapshot(tables)
        
        print("=== RESULT ===")
        print("PASS: Schema snapshot extracted successfully")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
