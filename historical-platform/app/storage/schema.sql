-- HIP / HAP append-only historical store (separate from live KAIP)

CREATE TABLE IF NOT EXISTS historical_raw_archive (
    event_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    collector_id TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    company_symbol TEXT,
    category TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    effective_start TEXT,
    effective_end TEXT,
    checksum TEXT NOT NULL,
    validation_status TEXT,
    validation_errors_json TEXT,
    ingestion_run_id TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_symbol_cat
    ON historical_raw_archive(company_symbol, category, retrieved_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_checksum
    ON historical_raw_archive(checksum);

CREATE TABLE IF NOT EXISTS historical_ingestion_runs (
    run_id TEXT PRIMARY KEY,
    mode TEXT NOT NULL,
    collector_id TEXT NOT NULL,
    symbols_json TEXT NOT NULL,
    categories_json TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL,
    raw_accepted INTEGER NOT NULL DEFAULT 0,
    raw_rejected INTEGER NOT NULL DEFAULT 0,
    objects_written INTEGER NOT NULL DEFAULT 0,
    detail_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_knowledge_objects (
    object_id TEXT PRIMARY KEY,
    object_type TEXT NOT NULL,
    subject_key TEXT NOT NULL,
    company_symbol TEXT,
    effective_date TEXT NOT NULL,
    period_kind TEXT NOT NULL,
    version INTEGER NOT NULL,
    previous_object_id TEXT,
    knowledge_json TEXT NOT NULL,
    entity_refs_json TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_hko_type_subject_eff
    ON historical_knowledge_objects(object_type, subject_key, effective_date, version DESC);

CREATE TABLE IF NOT EXISTS historical_prices (
    object_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    period_kind TEXT NOT NULL,
    version INTEGER NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    knowledge_json TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_symbol_date_ver
    ON historical_prices(company_symbol, effective_date, period_kind, version);

CREATE TABLE IF NOT EXISTS historical_financials (
    object_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    period_kind TEXT NOT NULL,
    statement_type TEXT NOT NULL,
    version INTEGER NOT NULL,
    revenue REAL,
    net_income REAL,
    knowledge_json TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fins_symbol_period_ver
    ON historical_financials(company_symbol, effective_date, period_kind, statement_type, version);

CREATE TABLE IF NOT EXISTS historical_balance_sheets (
    object_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    period_kind TEXT NOT NULL,
    version INTEGER NOT NULL,
    knowledge_json TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_cashflows (
    object_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    period_kind TEXT NOT NULL,
    version INTEGER NOT NULL,
    knowledge_json TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_dividends (
    object_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    version INTEGER NOT NULL,
    amount REAL,
    knowledge_json TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_actions (
    object_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    action_type TEXT NOT NULL,
    version INTEGER NOT NULL,
    knowledge_json TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_events (
    object_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    event_type TEXT NOT NULL,
    version INTEGER NOT NULL,
    knowledge_json TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_reports (
    object_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    report_type TEXT NOT NULL,
    version INTEGER NOT NULL,
    title TEXT,
    knowledge_json TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_company_profiles (
    object_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    version INTEGER NOT NULL,
    knowledge_json TEXT NOT NULL,
    entity_refs_json TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_news (
    object_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    version INTEGER NOT NULL,
    title TEXT,
    knowledge_json TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_metadata (
    meta_key TEXT PRIMARY KEY,
    meta_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_entities (
    company_symbol TEXT PRIMARY KEY,
    company_name TEXT,
    sector TEXT,
    sector_key TEXT,
    industry TEXT,
    index_membership_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
