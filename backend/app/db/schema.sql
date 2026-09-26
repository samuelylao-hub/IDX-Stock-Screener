CREATE TABLE IF NOT EXISTS stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    subsector VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS stock_prices (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id),
    trade_date DATE NOT NULL,
    open NUMERIC(15, 2),
    high NUMERIC(15, 2),
    low NUMERIC(15, 2),
    close NUMERIC(15, 2),
    adjusted_close NUMERIC(15, 2),
    volume BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (stock_id, trade_date)
);

CREATE TABLE IF NOT EXISTS market_calendar (
    id SERIAL PRIMARY KEY,
    calendar_date DATE NOT NULL UNIQUE,
    is_trading_day BOOLEAN NOT NULL,
    holiday_name VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scheduled_jobs (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS job_runs (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES scheduled_jobs(id),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL,
    message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS foreign_daily_flow (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id),
    trade_date DATE NOT NULL,

    foreign_buy_value NUMERIC(20, 2),
    foreign_sell_value NUMERIC(20, 2),
    foreign_net_value NUMERIC(20, 2),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (stock_id, trade_date)
);

CREATE TABLE IF NOT EXISTS news_events (
    id SERIAL PRIMARY KEY,
    event_key VARCHAR(255) UNIQUE,
    symbol VARCHAR(10),
    canonical_title TEXT NOT NULL,

    first_published_at TIMESTAMPTZ NOT NULL,
    first_detected_at TIMESTAMPTZ NOT NULL,

    importance VARCHAR(20),
    validation_status VARCHAR(40),

    source_count INTEGER NOT NULL DEFAULT 0,
    official_source_count INTEGER NOT NULL DEFAULT 0,
    primary_source_count INTEGER NOT NULL DEFAULT 0,
    independent_source_count INTEGER NOT NULL DEFAULT 0,
    contradicting_source_count INTEGER NOT NULL DEFAULT 0,

    evidence_strength VARCHAR(20),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS news_event_sources (
    id SERIAL PRIMARY KEY,

    news_event_id INTEGER NOT NULL
        REFERENCES news_events(id)
        ON DELETE CASCADE,

    source_name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    source_tier INTEGER NOT NULL,

    country VARCHAR(50),

    url TEXT,

    published_at TIMESTAMPTZ,
    detected_at TIMESTAMPTZ,

    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    is_contradicting BOOLEAN NOT NULL DEFAULT FALSE,

    source_role VARCHAR(30),
    derived_from VARCHAR(255),
    relationship_note TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (news_event_id, source_name, url)
);