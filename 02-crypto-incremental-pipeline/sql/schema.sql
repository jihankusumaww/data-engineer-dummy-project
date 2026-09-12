-- Skema untuk pipeline incremental harga crypto
-- Database: SQLite

CREATE TABLE IF NOT EXISTS raw_price_snapshot (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id         TEXT NOT NULL,
    price_usd       REAL NOT NULL,
    market_cap_usd  REAL,
    fetched_at_utc  TEXT NOT NULL,       -- ISO timestamp saat data diambil
    UNIQUE(coin_id, fetched_at_utc)
);

CREATE TABLE IF NOT EXISTS fact_price_hourly (
    coin_id             TEXT NOT NULL,
    price_usd           REAL NOT NULL,
    market_cap_usd       REAL,
    fetched_at_utc       TEXT NOT NULL,
    moving_avg_3         REAL,          -- moving average 3 titik data terakhir
    pct_change_from_prev REAL,          -- % perubahan dari snapshot sebelumnya
    PRIMARY KEY (coin_id, fetched_at_utc)
);

-- Watermark table: menyimpan timestamp terakhir yang sudah diproses per coin,
-- supaya pipeline tahu dari mana harus lanjut (incremental processing).
CREATE TABLE IF NOT EXISTS pipeline_watermark (
    coin_id             TEXT PRIMARY KEY,
    last_processed_utc  TEXT NOT NULL
);
