# -*- coding: utf-8 -*-
"""临时审计脚本：全库状态检查（任务后删除）。"""
import sqlite3, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = sqlite3.connect('database/cycle_research.db')
c.row_factory = sqlite3.Row

print('== TABLES ==')
for (n,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    cnt = c.execute(f"SELECT COUNT(*) FROM {n}").fetchone()[0]
    print(f'{n}: {cnt}')

print('\n== CAMPAIGNS ==')
for r in c.execute("""SELECT campaign_id, campaign_year, start_date, end_date, peak_date,
                      classification, strength, result, date_confidence
                      FROM campaigns ORDER BY campaign_year"""):
    print(dict(r))

print('\n== ANNUAL REVIEWS ==')
for r in c.execute("SELECT year, status FROM annual_reviews ORDER BY year"):
    print(dict(r))

print('\n== CAMPAIGN_PHASES (enum check) ==')
for r in c.execute("SELECT campaign_id, phase_type, start_date, end_date FROM campaign_phases ORDER BY campaign_id, start_date"):
    print(dict(r))

print('\n== CAMPAIGN_DATE_OBSERVATIONS ==')
for r in c.execute("""SELECT observation_id, campaign_id, date_role, candidate_date, verified_date,
                      verification_method, confidence FROM campaign_date_observations ORDER BY campaign_id, date_role"""):
    print(dict(r))

print('\n== EVIDENCES per campaign (bridge) ==')
for r in c.execute("""SELECT ce.campaign_id, ce.role, e.evidence_id, e.evidence_role, e.temporal_relation,
                      e.independence_group, s.tier, s.source_type, e.date
                      FROM campaign_evidences ce
                      JOIN evidences e ON e.evidence_id=ce.evidence_id
                      LEFT JOIN sources s ON s.source_id=e.source_id
                      ORDER BY ce.campaign_id, e.date"""):
    print(dict(r))

print('\n== SOURCES tier/type consistency ==')
for r in c.execute("SELECT source_id, source_type, tier FROM sources ORDER BY source_id"):
    print(dict(r))

print('\n== MARKET_SERIES ==')
for r in c.execute("SELECT series_id, name, series_type, provider, symbol, price_type FROM market_series ORDER BY series_id"):
    print(dict(r))

print('\n== MARKET_DAILY summary ==')
for r in c.execute("""SELECT series_id, price_type, COUNT(*) n, MIN(trade_date) d0, MAX(trade_date) d1
                      FROM market_daily GROUP BY series_id, price_type ORDER BY series_id"""):
    print(dict(r))

print('\n== EVENTS ==')
for r in c.execute("SELECT event_id, date, event_type, name FROM events ORDER BY date"):
    print(dict(r))

print('\n== SECURITIES ==')
for r in c.execute("SELECT security_id, ticker, name FROM securities ORDER BY security_id"):
    print(dict(r))

print('\n== CAMPAIGN_SECURITIES ==')
for r in c.execute("SELECT campaign_id, security_id, role FROM campaign_securities ORDER BY campaign_id"):
    print(dict(r))

print('\n== CAMPAIGN_EVENTS ==')
for r in c.execute("SELECT campaign_id, event_id, role FROM campaign_events ORDER BY campaign_id"):
    print(dict(r))

print('\n== CAMPAIGN_THEMES ==')
for r in c.execute("SELECT campaign_id, theme_id, role FROM campaign_themes ORDER BY campaign_id"):
    print(dict(r))

print('\n== RESEARCH_RULES ==')
for r in c.execute("SELECT rule_id, status, base_pattern FROM research_rules"):
    print(dict(r))
c.close()
