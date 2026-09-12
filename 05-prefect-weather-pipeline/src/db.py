"""
Load layer: fungsi murni untuk insert ke SQLite. Dipisah dari flows.py
supaya bisa di-test dengan database in-memory tanpa perlu Prefect.
"""
import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "weather.db"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    return conn


def insert_weather_reading(conn: sqlite3.Connection, record: dict) -> None:
    conn.execute(
        """INSERT OR IGNORE INTO fact_weather_reading
           (city_name, temperature_c, windspeed_kmh, weather_code, observed_at, fetched_at_utc)
           VALUES (:city_name, :temperature_c, :windspeed_kmh, :weather_code, :observed_at, :fetched_at_utc)""",
        record,
    )
    conn.commit()


def log_pipeline_run(conn: sqlite3.Connection, run_summary: dict) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO pipeline_run_log
           (run_id, started_at_utc, finished_at_utc, cities_requested,
            cities_succeeded, cities_failed, status)
           VALUES (:run_id, :started_at_utc, :finished_at_utc, :cities_requested,
                   :cities_succeeded, :cities_failed, :status)""",
        run_summary,
    )
    conn.commit()
