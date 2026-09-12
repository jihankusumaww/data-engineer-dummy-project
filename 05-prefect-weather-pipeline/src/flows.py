"""
Orchestration layer pakai Prefect. Semua business logic sengaja diimpor dari
transform.py & db.py (lihat komentar di sana) -- file ini HANYA berisi
"pengkabelan" (wiring): retry policy, concurrency, logging, dan urutan
eksekusi task.

Cara jalan sekali (ad-hoc):
    python src/flows.py

Cara membuat jadwal otomatis (deployment), misalnya tiap jam:
    prefect deployment build src/flows.py:weather_etl_flow \
        --name "hourly-weather-etl" --cron "0 * * * *"
    prefect deployment apply weather_etl_flow-deployment.yaml
    prefect agent start -q default

Kenapa Prefect (bukan Airflow) untuk project skala kecil-menengah ini:
- Bisa dijalankan sebagai script Python biasa tanpa perlu webserver/scheduler
  terpisah yang jalan terus-menerus (lebih ringan untuk laptop biasa)
- Retry, logging, dan observability (Prefect UI/Cloud) tetap dapat tanpa
  overhead setup Airflow yang jauh lebih berat
"""
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from prefect import flow, task, get_run_logger

sys.path.append(str(Path(__file__).resolve().parent))
from transform import (
    DEFAULT_CITIES,
    InvalidWeatherDataError,
    build_open_meteo_url,
    parse_weather_response,
    validate_record,
)
from db import get_connection, insert_weather_reading, log_pipeline_run


@task(
    name="fetch_weather_for_city",
    retries=3,
    retry_delay_seconds=10,
    tags=["extract", "external-api"],
)
def fetch_weather_for_city(city: dict) -> dict:
    """
    Ambil data cuaca untuk satu kota. Task ini akan otomatis di-retry
    oleh Prefect sampai 3 kali (dengan jeda 10 detik) kalau API sedang
    tidak stabil -- ini keuntungan utama pakai orchestrator dibanding
    script polos: retry policy dideklarasikan, bukan ditulis manual
    dengan try/except + sleep di mana-mana.
    """
    logger = get_run_logger()
    url = build_open_meteo_url(city["latitude"], city["longitude"])
    logger.info(f"Fetching cuaca untuk {city['name']} dari {url}")

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    record = parse_weather_response(response.json(), city["name"])
    validate_record(record)
    logger.info(f"[{city['name']}] {record['temperature_c']}°C, angin {record['windspeed_kmh']} km/h")
    return record


@task(name="load_weather_reading")
def load_weather_reading(record: dict) -> None:
    conn = get_connection()
    try:
        insert_weather_reading(conn, record)
    finally:
        conn.close()


@flow(name="multi-city-weather-etl", log_prints=True)
def weather_etl_flow(cities: list[dict] = None):
    """
    Flow utama: fetch cuaca untuk semua kota SECARA PARALEL (pakai
    .submit(), bukan loop biasa), lalu load satu-satu. Kalau satu kota
    gagal (misal API down untuk request itu), kota lain tetap lanjut --
    ini pola "partial failure tolerance" yang penting di pipeline production.
    """
    logger = get_run_logger()
    cities = cities or DEFAULT_CITIES
    run_id = str(uuid.uuid4())[:8]
    started_at = datetime.now(timezone.utc).isoformat()

    logger.info(f"=== Run {run_id}: memproses {len(cities)} kota ===")

    # Submit semua fetch task secara paralel (Prefect menjalankannya
    # concurrently, tidak menunggu satu-satu selesai dulu)
    futures = [fetch_weather_for_city.submit(city) for city in cities]

    succeeded, failed = 0, 0
    for future, city in zip(futures, cities):
        try:
            record = future.result()
            load_weather_reading(record)
            succeeded += 1
        except InvalidWeatherDataError as e:
            logger.warning(f"[{city['name']}] Data tidak valid, dilewati: {e}")
            failed += 1
        except Exception as e:
            logger.error(f"[{city['name']}] Gagal setelah semua retry: {e}")
            failed += 1

    status = "success" if failed == 0 else ("partial_failure" if succeeded > 0 else "failed")

    conn = get_connection()
    try:
        log_pipeline_run(conn, {
            "run_id": run_id,
            "started_at_utc": started_at,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "cities_requested": len(cities),
            "cities_succeeded": succeeded,
            "cities_failed": failed,
            "status": status,
        })
    finally:
        conn.close()

    logger.info(f"=== Run {run_id} selesai: {succeeded} sukses, {failed} gagal (status: {status}) ===")
    return {"run_id": run_id, "succeeded": succeeded, "failed": failed, "status": status}


if __name__ == "__main__":
    weather_etl_flow()
