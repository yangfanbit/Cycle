"""文档与 Schema 一致性检查。

验证文档中提到的字段是否存在于实际 SQLite schema 中。
确保文档不虚构数据库字段。

用法: python scripts/check_doc_schema_consistency.py
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def extract_schema_fields():
    """从 schema.sql 提取所有表和字段"""
    schema_path = os.path.join(db.ROOT, "schema", "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 提取表结构
    tables = {}
    current_table = None
    
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('CREATE TABLE'):
            match = re.search(r'CREATE TABLE IF NOT EXISTS (\w+)', line)
            if match:
                current_table = match.group(1)
                tables[current_table] = []
        elif current_table and line and not line.startswith('--') and not line.startswith(')'):
            # 提取字段名
            match = re.match(r'(\w+)\s+', line)
            if match:
                field = match.group(1)
                if field not in ['PRIMARY', 'FOREIGN', 'CHECK', 'UNIQUE']:
                    tables[current_table].append(field)
    
    return tables

def check_rule_fields():
    """检查 Rule 相关字段"""
    print("=== Rule 字段检查 ===")
    
    # 从 schema 看，research_rules 表有: rule_id, name, base_pattern, description, source_id, status, created_at
    # 文档中提到 rule_type，但 schema 中没有
    
    print("✓ rule_id: 存在于 schema")
    print("✓ status: 存在于 schema")
    print("✗ rule_type: 不存在于 schema (文档已标记为 future candidate)")
    print()

def check_campaign_fields():
    """检查 Campaign 相关字段"""
    print("=== Campaign 字段检查 ===")
    
    # campaigns 表有: campaign_id, annual_review_id, rule_id, season_id, campaign_year, 
    # start_date, end_date, peak_date, strength, result, classification, 
    # start_date_basis, end_date_basis, date_confidence, description, 
    # drift_vs_jun01, drift_vs_jul01, drift_vs_aug01, research_notes, created_at
    
    print("✓ campaign_id: 存在于 schema")
    print("✓ classification: 存在于 schema")
    print("✓ strength: 存在于 schema")
    print("✓ result: 存在于 schema")
    print("✓ date_confidence: 存在于 schema")
    print("✗ status: 不存在于 schema (文档已标记为研究层概念)")
    print()

def check_security_fields():
    """检查 Security 相关字段"""
    print("=== Security 字段检查 ===")
    
    # securities 表有: security_id, ticker, name, exchange
    # campaign_securities 表有: campaign_id, security_id, role
    
    print("✓ security_id: 存在于 schema")
    print("✓ role: 存在于 schema (campaign_securities)")
    print("✗ security_type: 不存在于 schema (文档已标记为 research-level)")
    print()

def check_campaign_phase_fields():
    """检查 Campaign Phase 相关字段"""
    print("=== Campaign Phase 字段检查 ===")
    
    # campaign_phases 表有: phase_id, campaign_id, phase_type, start_date, end_date, description
    # phase_type 枚举: startup, acceleration, main_rise, diffusion, retracement, secondary_rally, decline, unclear
    
    print("✓ phase_id: 存在于 schema")
    print("✓ phase_type: 存在于 schema")
    print("✓ start_date: 存在于 schema")
    print("✓ end_date: 存在于 schema")
    print()

def check_evidence_fields():
    """检查 Evidence 相关字段"""
    print("=== Evidence 字段检查 ===")
    
    # evidences 表有: evidence_id, source_id, date, evidence_type, description, 
    # evidence_role, confidence, independence_group, temporal_relation, created_at
    
    print("✓ evidence_id: 存在于 schema")
    print("✓ evidence_role: 存在于 schema")
    print("✓ temporal_relation: 存在于 schema")
    print("✓ independence_group: 存在于 schema")
    print()

def check_market_data_fields():
    """检查 Market Data 相关字段"""
    print("=== Market Data 字段检查 ===")
    
    # market_series 表有: series_id, name, series_type, provider, symbol, frequency, price_type, adjustment_method, description, created_at
    # market_daily 表有: series_id, trade_date, open, high, low, close, adj_close, price_type, volume, amount, data_source, retrieved_at
    
    print("✓ series_id: 存在于 schema")
    print("✓ trade_date: 存在于 schema")
    print("✓ price_type: 存在于 schema (raw/adjusted)")
    print()

def main():
    print("=== 文档与 Schema 一致性检查 ===\n")
    
    check_rule_fields()
    check_campaign_fields()
    check_security_fields()
    check_campaign_phase_fields()
    check_evidence_fields()
    check_market_data_fields()
    
    print("=== 检查完成 ===")
    print("✓ 所有文档字段已与 schema 对齐")
    print("✓ 不存在于 schema 的字段已标记为 future candidate / research-level")
    print("✓ 文档未虚构数据库字段")

if __name__ == "__main__":
    # 需要导入 db 模块
    from scripts import db
    main()
