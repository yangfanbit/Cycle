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
    -- 独立性分组：同一事实被多个媒体转载时，仅为转引、不得自动计为多条独立证据。
    -- 同源转引填 same_origin_xxx；真正独立来源使用不同 group。
    independence_group TEXT,
    -- 时间关系（Pilot 1-C0）：相对其关联 Campaign 的时间语义，防止"事后证据"伪装成"当时信息"。
    --   contemporaneous : 发生/发布于 Campaign 期间
    --   prior           : 发生于 Campaign 开始前
    --   subsequent      : Campaign 后，用于解释结果/退潮/反证
    --   retrospective   : 更晚的历史资料，站在未来回顾过去（hindsight）
    --   unknown         : 无法判断
    temporal_relation TEXT CHECK (temporal_relation IN
                        ('contemporaneous','prior','subsequent','retrospective','unknown')),
    created_at      TEXT DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- Campaign ↔ Evidence 显式关联（v1.5 新增）
-- 一个 Campaign 只能引用其真实支撑/反驳/背景证据，禁止全库混入。
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS campaign_evidences (
    campaign_id     TEXT NOT NULL REFERENCES campaigns(campaign_id),
    evidence_id     TEXT NOT NULL REFERENCES evidences(evidence_id),
    role            TEXT NOT NULL CHECK (role IN ('supporting','contradicting','context')),
    created_at      TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (campaign_id, evidence_id)
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
    -- [v1.5 兼容设计] 未来推荐拆分为：
    --   start_date_basis_code / end_date_basis_code: observed | inferred | official_event | unknown
    --   start_date_basis_note / end_date_basis_note: 具体依据说明
    -- 当前旧字段保留长说明文本，暂不迁移（不破坏试点结论）。
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

-- ============================================================
-- Pilot 1-C1：行情事实核验基础设施
-- Market Series → Daily Market Data → Date Verification → Campaign
-- 数据只用于“核验每个已存在 Campaign 的日期事实”，不用于自动判定 Campaign
-- ============================================================

-- 行情序列（指数/行业/概念/个股/基准）。只填真实可确认的 symbol，否则留空待补。
CREATE TABLE IF NOT EXISTS market_series (
    series_id         TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    series_type       TEXT NOT NULL CHECK (series_type IN
                        ('industry_index','sector_index','concept_index','stock','benchmark','other')),
    provider          TEXT,             -- 数据提供方（如 akshare / sw / csi），非付费 token
    symbol            TEXT,             -- 真实可确认代码；不确定则为 NULL
    frequency         TEXT NOT NULL DEFAULT 'daily'
                        CHECK (frequency IN ('daily','weekly','monthly','intraday','other')),
    price_type        TEXT NOT NULL CHECK (price_type IN ('raw','adjusted','other')),
    adjustment_method TEXT,             -- adjusted 时填充：前复权/后复权(hfq/qfq)；raw 为 NULL
    description       TEXT,
    created_at        TEXT DEFAULT (datetime('now'))
);

-- 日线行情。每行必须明确价格口径（raw / adjusted），禁止同一行混用。
-- 同一 series 同一交易日同一口径唯一（原始数据可追溯，勿自动覆盖）。
CREATE TABLE IF NOT EXISTS market_daily (
    series_id     TEXT NOT NULL REFERENCES market_series(series_id),
    trade_date    TEXT NOT NULL,        -- ISO YYYY-MM-DD，仅交易日
    open          REAL, high REAL, low REAL, close REAL,
    adj_close     REAL,                 -- 仅当 price_type='adjusted' 时使用
    price_type    TEXT NOT NULL CHECK (price_type IN ('raw','adjusted')),
    volume        REAL,
    amount        REAL,
    data_source   TEXT,
    retrieved_at  TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (series_id, trade_date, price_type)
);

-- 交易日历。calendar_type 标识市场（如 cn）。
-- 若无独立数据源，允许由 benchmark series 的 distinct trade_date 推导（见 README）。
CREATE TABLE IF NOT EXISTS trading_calendar (
    trade_date      TEXT PRIMARY KEY,
    is_trading_day  INTEGER NOT NULL CHECK (is_trading_day IN (0,1)),
    calendar_type   TEXT NOT NULL DEFAULT 'cn',
    created_at      TEXT DEFAULT (datetime('now'))
);

-- Campaign 日期核验观测。分开保存 candidate（原始研究日期，不得被覆盖）与 verified（核验后日期）。
CREATE TABLE IF NOT EXISTS campaign_date_observations (
    observation_id     TEXT PRIMARY KEY,
    campaign_id        TEXT NOT NULL REFERENCES campaigns(campaign_id),
    date_role          TEXT NOT NULL CHECK (date_role IN ('start','end','peak')),
    candidate_date     TEXT NOT NULL,   -- 原始 Research Candidate（抄自 campaigns，保留不改）
    verified_date      TEXT,            -- 行情/人工核验后日期（可空=未核验）
    verification_method TEXT NOT NULL CHECK (verification_method IN
                            ('manual','market_data','market_data_plus_event','unknown')),
    confidence         TEXT NOT NULL CHECK (confidence IN ('high','medium','low')),
    evidence_id        TEXT REFERENCES evidences(evidence_id),  -- 若有则必须有效
    notes              TEXT,
    created_at         TEXT DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- 索引
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_evidence_source   ON evidences(source_id);
CREATE INDEX IF NOT EXISTS idx_campaign_rule     ON campaigns(rule_id);
CREATE INDEX IF NOT EXISTS idx_campaign_review   ON campaigns(annual_review_id);
CREATE INDEX IF NOT EXISTS idx_event_date        ON events(date);
CREATE INDEX IF NOT EXISTS idx_mdaily_series      ON market_daily(series_id, trade_date);
CREATE INDEX IF NOT EXISTS idx_cdo_campaign       ON campaign_date_observations(campaign_id);