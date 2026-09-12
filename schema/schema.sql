-- ============================================================
-- Cycle-Research schema
-- A股历史题材 / 行业季节性研究数据库（先行版）
-- 规则：research_rule 参照 Base Pattern；年份是其 Annual Theme 实例化
-- 本项目与 Cycle 完全独立；结论经人工 Review 后才转入 Cycle
-- ============================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- 来源表（Tier 1-4，Tier4 只能做线索）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sources (
    source_id       TEXT PRIMARY KEY,
    source_type     TEXT NOT NULL CHECK (source_type IN
                        ('exchange','regulator','company_announcement','industry_association',
                         'media_tier2','media_tier3','media_tier4','research_report','website',
                         'forum_blog','social_media','other')),
    title           TEXT NOT NULL,
    author          TEXT,
    url             TEXT,
    published_at    TEXT,          -- 来源发布日期 ISO
    captured_at     TEXT,          -- 抓取时间 ISO
    publisher       TEXT,
    description     TEXT,
    tier            INTEGER CHECK (tier IN (1,2,3,4)),  -- 来源优先级
    created_at      TEXT DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- 证据表（supporting / contradicting / context）
-- 强/弱结论都必须有独立证据支撑
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS evidences (
    evidence_id     TEXT PRIMARY KEY,
    source_id       TEXT REFERENCES sources(source_id),
    date            TEXT,          -- 事件日期 ISO
    evidence_type   TEXT NOT NULL, -- 行情数据/媒体/官方文件/行业文件 等
    description     TEXT NOT NULL,
    evidence_role   TEXT NOT NULL CHECK (evidence_role IN
                        ('supporting','contradicting','context')),
    confidence      TEXT NOT NULL CHECK (confidence IN ('high','medium','low')),
    created_at      TEXT DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- 研究规则表（Base Pattern）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS research_rules (
    rule_id         TEXT PRIMARY KEY,     -- rule_auto_summer
    name            TEXT NOT NULL,
    base_pattern    TEXT NOT NULL,        -- 汽车
    description     TEXT NOT NULL,
    source_id       TEXT REFERENCES sources(source_id),
    status          TEXT NOT NULL CHECK (status IN
                        ('candidate','under_review','confirmed','weak','rejected')),
    created_at      TEXT DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- 年度评审主表（每年一条母记录）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS annual_reviews (
    annual_review_id TEXT PRIMARY KEY,
    rule_id         TEXT NOT NULL REFERENCES research_rules(rule_id),
    year            INTEGER NOT NULL CHECK (year BETWEEN 2010 AND 2100),
    status          TEXT NOT NULL CHECK (status IN
                        ('strong','medium','weak','no_clear_campaign','unknown')),
    summary         TEXT,
    review_notes    TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE (rule_id, year)
);

-- ------------------------------------------------------------
-- Campaign 表
-- classification: theme_campaign / industry_trend / event_driven / mixed / unclear
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id        TEXT PRIMARY KEY,
    annual_review_id   TEXT REFERENCES annual_reviews(annual_review_id),
    rule_id            TEXT REFERENCES research_rules(rule_id),
    season_id          TEXT,             -- 例如 summer_2023
    campaign_year      INTEGER,
    start_date         TEXT,
    end_date           TEXT,
    peak_date          TEXT,
    strength           TEXT,
    result             TEXT NOT NULL CHECK (result IN ('positive','neutral','weak','failed','unknown')),
    classification     TEXT NOT NULL CHECK (classification IN
                            ('theme_campaign','industry_trend','event_driven','mixed','unclear')),
    start_date_basis   TEXT,
    end_date_basis     TEXT,
    date_confidence    TEXT CHECK (date_confidence IN ('high','medium','low')),
    description        TEXT,
    -- 窗口漂移
    drift_vs_jun01     INTEGER,          -- 相对6月1日的偏移天数
    drift_vs_jul01     INTEGER,          -- 相对7月1日的偏移天数
    drift_vs_aug01     INTEGER,          -- 相对8月1日的偏移天数
    research_notes     TEXT,
    created_at         TEXT DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- 主题表（Annual Theme）。Base Pattern(汽车) -> Theme(智能驾驶/车路云/Robotaxi) -> Campaign
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS themes (
    theme_id        TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    theme_type      TEXT NOT NULL CHECK (theme_type IN ('sector','industry','concept')),
    parent_theme_id TEXT REFERENCES themes(theme_id),
    description     TEXT
);

CREATE TABLE IF NOT EXISTS campaign_themes (
    campaign_id     TEXT REFERENCES campaigns(campaign_id),
    theme_id        TEXT REFERENCES themes(theme_id),
    role            TEXT NOT NULL CHECK (role IN ('main','secondary','catalyst','related')),
    PRIMARY KEY (campaign_id, theme_id)
);

-- ------------------------------------------------------------
-- 事件表
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS events (
    event_id        TEXT PRIMARY KEY,
    date            TEXT,
    name            TEXT NOT NULL,
    event_type      TEXT NOT NULL CHECK (event_type IN
                        ('policy','industry','macro','company','market','news','holiday','other')),
    description     TEXT,
    source_id       TEXT REFERENCES sources(source_id)
);

CREATE TABLE IF NOT EXISTS campaign_events (
    campaign_id     TEXT REFERENCES campaigns(campaign_id),
    event_id        TEXT REFERENCES events(event_id),
    role            TEXT NOT NULL CHECK (role IN ('trigger','catalyst','context','follow_up')),
    PRIMARY KEY (campaign_id, event_id)
);

-- ------------------------------------------------------------
-- 个股表（leader 需证据支撑）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS securities (
    security_id     TEXT PRIMARY KEY,
    ticker          TEXT,
    name            TEXT NOT NULL,
    exchange        TEXT
);

CREATE TABLE IF NOT EXISTS campaign_securities (
    campaign_id     TEXT REFERENCES campaigns(campaign_id),
    security_id     TEXT REFERENCES securities(security_id),
    role            TEXT NOT NULL CHECK (role IN ('leader','second_leader','representative','follow')),
    PRIMARY KEY (campaign_id, security_id)
);

-- ------------------------------------------------------------
-- Campaign Phase / Wave 表（第一阶段仅证据充分时记录）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS campaign_phases (
    phase_id        TEXT PRIMARY KEY,
    campaign_id     TEXT REFERENCES campaigns(campaign_id),
    phase_type      TEXT NOT NULL CHECK (phase_type IN
                        ('startup','acceleration','main_rise','diffusion',
                         'retracement','secondary_rally','decline','unclear')),
    start_date      TEXT,
    end_date        TEXT,
    description     TEXT
);

-- ------------------------------------------------------------
-- 索引
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_evidence_source   ON evidences(source_id);
CREATE INDEX IF NOT EXISTS idx_campaign_rule     ON campaigns(rule_id);
CREATE INDEX IF NOT EXISTS idx_campaign_review   ON campaigns(annual_review_id);
CREATE INDEX IF NOT EXISTS idx_event_date        ON events(date);