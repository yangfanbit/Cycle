CREATE TABLE market_series (
            series_id         TEXT PRIMARY KEY,
            name              TEXT NOT NULL,
            series_type       TEXT NOT NULL CHECK (series_type IN
                                ('industry_index','sector_index','concept_index','stock','benchmark','other')),
            provider          TEXT,
            symbol            TEXT,
            frequency         TEXT NOT NULL DEFAULT 'daily'
                                CHECK (frequency IN ('daily','weekly','monthly','intraday','other')),
            price_type        TEXT NOT NULL CHECK (price_type IN ('raw','adjusted','other')),
            adjustment_method TEXT,
            description       TEXT,
            created_at        TEXT DEFAULT (datetime('now'))
        );

CREATE TABLE trading_calendar (
            trade_date      TEXT PRIMARY KEY,
            is_trading_day  INTEGER NOT NULL CHECK (is_trading_day IN (0,1)),
            calendar_type   TEXT NOT NULL DEFAULT 'cn',
            created_at      TEXT DEFAULT (datetime('now'))
        );

CREATE TABLE market_daily (
            series_id     TEXT NOT NULL REFERENCES market_series(series_id),
            trade_date    TEXT NOT NULL,
            open          REAL, high REAL, low REAL, close REAL,
            adj_close     REAL,
            price_type    TEXT NOT NULL CHECK (price_type IN ('raw','adjusted')),
            volume        REAL,
            amount        REAL,
            data_source   TEXT,
            retrieved_at  TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (series_id, trade_date, price_type)
        );

CREATE INDEX idx_mdaily_series ON market_daily(series_id, trade_date);
