-- Skema untuk pipeline cuaca multi-kota
CREATE TABLE IF NOT EXISTS fact_weather_reading (
    reading_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    city_name       TEXT NOT NULL,
    temperature_c   REAL NOT NULL,
    windspeed_kmh   REAL NOT NULL,
    weather_code    INTEGER NOT NULL,
    observed_at     TEXT NOT NULL,        -- waktu observasi dari API
    fetched_at_utc  TEXT NOT NULL,        -- waktu pipeline mengambil data
    UNIQUE(city_name, observed_at)
);

CREATE TABLE IF NOT EXISTS pipeline_run_log (
    run_id          TEXT PRIMARY KEY,
    started_at_utc  TEXT NOT NULL,
    finished_at_utc TEXT,
    cities_requested INTEGER NOT NULL,
    cities_succeeded INTEGER NOT NULL,
    cities_failed    INTEGER NOT NULL,
    status          TEXT NOT NULL           -- 'success' | 'partial_failure' | 'failed'
);
