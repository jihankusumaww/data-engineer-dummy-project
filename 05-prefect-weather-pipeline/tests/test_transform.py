"""
Unit test untuk business logic murni (transform.py & db.py).
Sengaja TIDAK butuh Prefect atau koneksi internet -- ini keuntungan dari
memisahkan business logic dari orchestration layer.

Jalankan dengan: pytest tests/
"""
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from transform import parse_weather_response, validate_record, build_open_meteo_url, InvalidWeatherDataError
from db import get_connection, insert_weather_reading, SCHEMA_PATH


SAMPLE_RESPONSE = {
    "latitude": -6.2,
    "longitude": 106.8,
    "current_weather": {
        "temperature": 31.5,
        "windspeed": 12.3,
        "weathercode": 1,
        "time": "2024-01-10T08:00",
    },
}


def test_parse_valid_response():
    record = parse_weather_response(SAMPLE_RESPONSE, "Jakarta")
    assert record["city_name"] == "Jakarta"
    assert record["temperature_c"] == 31.5
    assert record["weather_code"] == 1


def test_parse_missing_current_weather_raises():
    with pytest.raises(InvalidWeatherDataError):
        parse_weather_response({}, "Jakarta")


def test_parse_missing_field_raises():
    bad_response = {"current_weather": {"temperature": 30}}  # windspeed, weathercode, time hilang
    with pytest.raises(InvalidWeatherDataError):
        parse_weather_response(bad_response, "Jakarta")


def test_validate_record_rejects_extreme_temperature():
    record = {"city_name": "X", "temperature_c": 999, "windspeed_kmh": 10}
    with pytest.raises(InvalidWeatherDataError):
        validate_record(record)


def test_validate_record_rejects_negative_windspeed():
    record = {"city_name": "X", "temperature_c": 30, "windspeed_kmh": -5}
    with pytest.raises(InvalidWeatherDataError):
        validate_record(record)


def test_validate_record_accepts_normal_data():
    record = {"city_name": "Jakarta", "temperature_c": 31.5, "windspeed_kmh": 12.3}
    validate_record(record)  # tidak boleh raise


def test_build_open_meteo_url():
    url = build_open_meteo_url(-6.2, 106.8)
    assert "latitude=-6.2" in url
    assert "longitude=106.8" in url
    assert "current_weather=true" in url


def test_insert_weather_reading_is_idempotent():
    """Insert record yang sama dua kali tidak boleh duplikat (UNIQUE constraint)."""
    conn = sqlite3.connect(":memory:")
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())

    record = parse_weather_response(SAMPLE_RESPONSE, "Jakarta")
    insert_weather_reading(conn, record)
    insert_weather_reading(conn, record)  # insert kedua, harus di-ignore

    count = conn.execute("SELECT COUNT(*) FROM fact_weather_reading").fetchone()[0]
    assert count == 1
    conn.close()
