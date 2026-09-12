"""
Unit test untuk logika watermark & incremental processing.
Jalankan dengan: pytest tests/
"""
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from pipeline import (  # type: ignore[import-not-found]
    get_watermark,
    set_watermark,
    load_raw_snapshot,
    transform_and_load_incremental,
    SCHEMA_PATH,
)


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    with open(SCHEMA_PATH) as f:
        connection.executescript(f.read())
    yield connection
    connection.close()


def test_watermark_defaults_to_epoch(conn):
    assert get_watermark(conn, "bitcoin") == "1970-01-01T00:00:00+00:00"


def test_watermark_roundtrip(conn):
    set_watermark(conn, "bitcoin", "2024-01-01T00:00:00+00:00")
    assert get_watermark(conn, "bitcoin") == "2024-01-01T00:00:00+00:00"


def test_incremental_only_processes_new_rows(conn):
    rows = [
        {"coin_id": "bitcoin", "price_usd": 40000, "market_cap_usd": 1e12, "fetched_at_utc": "2024-01-01T00:00:00+00:00"},
        {"coin_id": "bitcoin", "price_usd": 41000, "market_cap_usd": 1e12, "fetched_at_utc": "2024-01-01T01:00:00+00:00"},
    ]
    load_raw_snapshot(conn, rows)
    transform_and_load_incremental(conn, ["bitcoin"])

    count_first_run = conn.execute("SELECT COUNT(*) FROM fact_price_hourly").fetchone()[0]
    assert count_first_run == 2

    # Run kedua tanpa data baru -> tidak ada baris tambahan
    transform_and_load_incremental(conn, ["bitcoin"])
    count_second_run = conn.execute("SELECT COUNT(*) FROM fact_price_hourly").fetchone()[0]
    assert count_second_run == 2

    # Watermark harus terupdate ke timestamp terakhir yang diproses
    assert get_watermark(conn, "bitcoin") == "2024-01-01T01:00:00+00:00"
