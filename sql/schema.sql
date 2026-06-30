-- ============================================================
-- Web Analytics Schema
-- ============================================================

-- ─── RAW LAYER ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS raw_ga4_sessions (
    id                  BIGSERIAL PRIMARY KEY,
    session_date        DATE NOT NULL,
    session_id          VARCHAR(64),
    user_pseudo_id      VARCHAR(64),
    user_id             VARCHAR(128),
    country             VARCHAR(64),
    city                VARCHAR(128),
    device_category     VARCHAR(32),   -- desktop | mobile | tablet
    operating_system    VARCHAR(64),
    browser             VARCHAR(64),
    channel_grouping    VARCHAR(64),   -- Organic Search | Paid Search | Direct | Referral | Social | Email
    source              VARCHAR(128),
    medium              VARCHAR(64),
    campaign            VARCHAR(256),
    landing_page        TEXT,
    sessions            INTEGER DEFAULT 1,
    new_users           INTEGER DEFAULT 0,
    pageviews           INTEGER DEFAULT 0,
    bounce              BOOLEAN DEFAULT FALSE,
    session_duration_s  NUMERIC(10,2),
    conversions         INTEGER DEFAULT 0,
    revenue             NUMERIC(12,2) DEFAULT 0,
    ingested_at         TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ga4_date    ON raw_ga4_sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_ga4_channel ON raw_ga4_sessions(channel_grouping);


CREATE TABLE IF NOT EXISTS raw_server_logs (
    id              BIGSERIAL PRIMARY KEY,
    log_time        TIMESTAMPTZ NOT NULL,
    ip_address      INET,
    method          VARCHAR(10),
    url             TEXT,
    query_string    TEXT,
    status_code     SMALLINT,
    response_bytes  INTEGER,
    referrer        TEXT,
    user_agent      TEXT,
    response_time_ms INTEGER,
    ingested_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_logs_time   ON raw_server_logs(log_time);
CREATE INDEX IF NOT EXISTS idx_logs_status ON raw_server_logs(status_code);
CREATE INDEX IF NOT EXISTS idx_logs_url    ON raw_server_logs(url);


CREATE TABLE IF NOT EXISTS raw_scrape_pages (
    id              BIGSERIAL PRIMARY KEY,
    scraped_at      TIMESTAMPTZ NOT NULL,
    url             TEXT NOT NULL,
    canonical_url   TEXT,
    title           TEXT,
    meta_description TEXT,
    h1              TEXT,
    word_count      INTEGER,
    internal_links  INTEGER DEFAULT 0,
    external_links  INTEGER DEFAULT 0,
    images_count    INTEGER DEFAULT 0,
    has_schema_org  BOOLEAN DEFAULT FALSE,
    page_size_kb    NUMERIC(8,2),
    load_time_ms    INTEGER,
    http_status     SMALLINT,
    ingested_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scrape_url  ON raw_scrape_pages(url);
CREATE INDEX IF NOT EXISTS idx_scrape_time ON raw_scrape_pages(scraped_at);


CREATE TABLE IF NOT EXISTS raw_clickstream_events (
    id              BIGSERIAL PRIMARY KEY,
    event_time      TIMESTAMPTZ NOT NULL,
    session_id      VARCHAR(64),
    user_pseudo_id  VARCHAR(64),
    event_name      VARCHAR(128) NOT NULL,   -- click | scroll | form_submit | page_view | custom
    page_url        TEXT,
    element_id      VARCHAR(256),
    element_class   VARCHAR(256),
    element_text    TEXT,
    scroll_depth_pct SMALLINT,              -- 0-100
    event_value     NUMERIC(12,2),
    event_params    JSONB,
    device_category VARCHAR(32),
    ingested_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_time    ON raw_clickstream_events(event_time);
CREATE INDEX IF NOT EXISTS idx_events_session ON raw_clickstream_events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_name    ON raw_clickstream_events(event_name);


-- ─── DIMENSION LAYER ────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_pages (
    page_id         BIGSERIAL PRIMARY KEY,
    url             TEXT NOT NULL UNIQUE,
    url_path        TEXT,
    url_domain      TEXT,
    page_title      TEXT,
    page_section    VARCHAR(128),  -- derived from first path segment
    is_landing_page BOOLEAN DEFAULT FALSE,
    word_count      INTEGER,
    first_seen      DATE,
    last_seen       DATE,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dim_pages_url ON dim_pages(url);


CREATE TABLE IF NOT EXISTS dim_dates (
    date_id         INTEGER PRIMARY KEY,   -- YYYYMMDD
    full_date       DATE NOT NULL UNIQUE,
    year            SMALLINT,
    quarter         SMALLINT,
    month           SMALLINT,
    month_name      VARCHAR(12),
    week            SMALLINT,              -- ISO week
    day_of_week     SMALLINT,              -- 1=Mon … 7=Sun
    day_name        VARCHAR(12),
    is_weekend      BOOLEAN,
    is_month_start  BOOLEAN,
    is_month_end    BOOLEAN
);


-- ─── FACT LAYER ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fct_sessions (
    session_key         BIGSERIAL PRIMARY KEY,
    session_id          VARCHAR(64),
    user_pseudo_id      VARCHAR(64),
    date_id             INTEGER REFERENCES dim_dates(date_id),
    page_id             INTEGER REFERENCES dim_pages(page_id),
    channel_grouping    VARCHAR(64),
    source              VARCHAR(128),
    medium              VARCHAR(64),
    campaign            VARCHAR(256),
    country             VARCHAR(64),
    device_category     VARCHAR(32),
    is_new_user         BOOLEAN DEFAULT FALSE,
    pageviews           INTEGER DEFAULT 0,
    session_duration_s  NUMERIC(10,2),
    bounced             BOOLEAN DEFAULT FALSE,
    conversions         INTEGER DEFAULT 0,
    revenue             NUMERIC(12,2) DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_fct_sess_date    ON fct_sessions(date_id);
CREATE INDEX IF NOT EXISTS idx_fct_sess_channel ON fct_sessions(channel_grouping);
CREATE INDEX IF NOT EXISTS idx_fct_sess_page    ON fct_sessions(page_id);


CREATE TABLE IF NOT EXISTS fct_events (
    event_key       BIGSERIAL PRIMARY KEY,
    event_time      TIMESTAMPTZ NOT NULL,
    date_id         INTEGER REFERENCES dim_dates(date_id),
    session_id      VARCHAR(64),
    user_pseudo_id  VARCHAR(64),
    page_id         INTEGER REFERENCES dim_pages(page_id),
    event_name      VARCHAR(128),
    scroll_depth_pct SMALLINT,
    event_value     NUMERIC(12,2),
    device_category VARCHAR(32)
);

CREATE INDEX IF NOT EXISTS idx_fct_evt_date    ON fct_events(date_id);
CREATE INDEX IF NOT EXISTS idx_fct_evt_session ON fct_events(session_id);
CREATE INDEX IF NOT EXISTS idx_fct_evt_name    ON fct_events(event_name);
