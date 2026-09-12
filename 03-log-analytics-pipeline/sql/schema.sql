-- Skema untuk log analytics pipeline
-- Database: SQLite

DROP TABLE IF EXISTS fact_log_event;
DROP TABLE IF EXISTS parse_error_log;
DROP TABLE IF EXISTS pipeline_run_summary;

-- Setiap baris log yang berhasil di-parse jadi satu event terstruktur
CREATE TABLE fact_log_event (
    event_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address      TEXT NOT NULL,
    event_timestamp TEXT NOT NULL,      -- ISO format
    http_method     TEXT NOT NULL,
    path            TEXT NOT NULL,
    status_code     INTEGER NOT NULL,
    response_size   INTEGER,
    status_class    TEXT NOT NULL       -- 'success' | 'client_error' | 'server_error'
);

-- Baris log yang GAGAL di-parse, tetap dicatat (bukan dibuang diam-diam)
-- supaya ada jejak untuk audit kualitas data sumber
CREATE TABLE parse_error_log (
    error_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_line        TEXT NOT NULL,
    run_id          TEXT NOT NULL
);

-- Ringkasan tiap kali pipeline dijalankan: berapa baris valid vs gagal
CREATE TABLE pipeline_run_summary (
    run_id          TEXT PRIMARY KEY,
    source_file     TEXT NOT NULL,
    total_lines     INTEGER NOT NULL,
    parsed_ok       INTEGER NOT NULL,
    parse_failed    INTEGER NOT NULL,
    parse_success_rate REAL NOT NULL,
    run_at_utc      TEXT NOT NULL
);

CREATE INDEX idx_event_timestamp ON fact_log_event(event_timestamp);
CREATE INDEX idx_event_status ON fact_log_event(status_class);
