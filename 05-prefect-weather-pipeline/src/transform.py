"""
Business logic murni: parsing response API dan validasi data.

Sengaja dipisah dari flows.py (yang berisi Prefect @task/@flow) supaya:
1. Bisa di-unit-test tanpa perlu menjalankan Prefect atau memanggil API asli.
2. Logic bisnis tidak "menempel" ke satu orchestration framework -- kalau
   suatu saat pindah dari Prefect ke Airflow/Dagster, fungsi-fungsi ini
   tetap bisa dipakai tanpa perubahan.
"""
from datetime import datetime, timezone
from typing import Optional


class InvalidWeatherDataError(Exception):
    """Dilempar kalau response API tidak punya field yang dibutuhkan."""


DEFAULT_CITIES = [
    {"name": "Jakarta", "latitude": -6.2088, "longitude": 106.8456},
    {"name": "Bandung", "latitude": -6.9175, "longitude": 107.6191},
    {"name": "Surabaya", "latitude": -7.2575, "longitude": 112.7521},
    {"name": "Semarang", "latitude": -6.9932, "longitude": 110.4203},
    {"name": "Medan", "latitude": 3.5952, "longitude": 98.6722},
]


def parse_weather_response(raw_json: dict, city_name: str) -> dict:
    """
    Ubah response mentah Open-Meteo API menjadi record terstruktur.
    Melempar InvalidWeatherDataError kalau field penting tidak ada --
    supaya task Prefect di layer atas bisa retry atau menandai gagal,
    alih-alih diam-diam memuat data yang salah.
    """
    current = raw_json.get("current_weather")
    if not current:
        raise InvalidWeatherDataError(f"Response tidak punya 'current_weather' untuk {city_name}")

    required_fields = ["temperature", "windspeed", "weathercode", "time"]
    missing = [f for f in required_fields if f not in current]
    if missing:
        raise InvalidWeatherDataError(f"Field hilang untuk {city_name}: {missing}")

    return {
        "city_name": city_name,
        "temperature_c": float(current["temperature"]),
        "windspeed_kmh": float(current["windspeed"]),
        "weather_code": int(current["weathercode"]),
        "observed_at": current["time"],
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def validate_record(record: dict) -> None:
    """
    Data quality check sebelum load. Melempar InvalidWeatherDataError
    kalau nilai di luar rentang yang masuk akal (sanity check).
    """
    if not (-90 <= record["temperature_c"] <= 60):
        raise InvalidWeatherDataError(f"Suhu tidak masuk akal: {record['temperature_c']}°C")
    if record["windspeed_kmh"] < 0:
        raise InvalidWeatherDataError(f"Windspeed negatif: {record['windspeed_kmh']}")
    if not record["city_name"]:
        raise InvalidWeatherDataError("city_name kosong")


def build_open_meteo_url(latitude: float, longitude: float) -> str:
    """Bangun URL request ke Open-Meteo (API publik, tidak butuh API key)."""
    return (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}&current_weather=true"
    )
