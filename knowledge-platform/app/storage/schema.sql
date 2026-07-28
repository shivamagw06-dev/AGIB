-- KAIP Sprint 6.1 storage — keep it small.

CREATE TABLE IF NOT EXISTS raw_events (
    event_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    collector_id TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    company_symbol TEXT,
    payload_json TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    checksum TEXT NOT NULL,
    validation_status TEXT,
    validation_errors_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_events_source_checksum
    ON raw_events(source, company_symbol, checksum, timestamp);

CREATE TABLE IF NOT EXISTS knowledge_objects (
    object_id TEXT PRIMARY KEY,
    object_type TEXT NOT NULL,
    company_symbol TEXT NOT NULL,
    version INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    entity_refs_json TEXT NOT NULL,
    source_event_ids_json TEXT NOT NULL,
    published_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ko_symbol_type
    ON knowledge_objects(company_symbol, object_type, version DESC);

CREATE TABLE IF NOT EXISTS company_profiles (
    company_symbol TEXT PRIMARY KEY,
    object_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    entity_refs_json TEXT NOT NULL,
    version INTEGER NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS market_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    object_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    as_of TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_market_symbol_asof
    ON market_snapshots(company_symbol, as_of DESC);

CREATE TABLE IF NOT EXISTS corporate_events (
    event_object_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    object_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    event_date TEXT,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_corp_events_symbol
    ON corporate_events(company_symbol, event_date DESC);

CREATE TABLE IF NOT EXISTS corporate_actions (
    action_object_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    object_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    ex_date TEXT,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_corp_actions_symbol
    ON corporate_actions(company_symbol, ex_date DESC);

CREATE TABLE IF NOT EXISTS financial_statements (
    statement_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    object_id TEXT NOT NULL,
    statement_type TEXT NOT NULL,
    period_end TEXT,
    payload_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_financials_symbol
    ON financial_statements(company_symbol, statement_type, period_end DESC);

CREATE TABLE IF NOT EXISTS learning_events (
    learning_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    field_name TEXT NOT NULL,
    previous_value_json TEXT,
    new_value_json TEXT,
    delta_json TEXT,
    materiality TEXT NOT NULL,
    reason TEXT NOT NULL,
    object_type TEXT,
    object_id TEXT,
    source_event_ids_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    published_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_learning_symbol
    ON learning_events(company_symbol, created_at DESC);

CREATE TABLE IF NOT EXISTS entity_registry (
    company_symbol TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    company_name TEXT NOT NULL,
    sector TEXT,
    industry TEXT,
    indexes_json TEXT NOT NULL DEFAULT '[]',
    peers_json TEXT NOT NULL DEFAULT '[]',
    aliases_json TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scheduler_runs (
    run_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    detail_json TEXT NOT NULL DEFAULT '{}'
);
