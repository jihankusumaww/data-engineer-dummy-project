# Multi-City Weather ETL — Orchestrated with Prefect

Pipeline yang mengambil data cuaca beberapa kota sekaligus (paralel) dari API
publik, dengan **retry policy otomatis**, **partial failure tolerance**, dan
**observability** (setiap run pipeline tercatat kesehatannya) — dibangun
dengan **Prefect**, orchestration framework modern yang lebih ringan dari
Airflow tapi konsepnya setara.

> ⚠️ **Catatan jujur:** project ini butuh koneksi internet (untuk
> `pip install prefect` dan memanggil API cuaca) dan saya tidak bisa
> menjalankan flow Prefect-nya secara end-to-end di sandbox saya (tidak ada
> akses internet di sana). Yang **sudah saya test dan pastikan jalan**:
> semua business logic di `src/transform.py` dan `src/db.py` (parsing,
> validasi, insert idempotent) — lihat `tests/test_transform.py`. Bagian
> yang belum tervalidasi otomatis: wiring Prefect di `src/flows.py`
> (`@task`/`@flow` decorator, retry, `.submit()`) — ditulis mengikuti API
> Prefect 2.x standar, tapi kabari saya kalau ada error versi saat pertama
> kali dijalankan.

## Kenapa project ini beda dari yang lain di portofolio ini
Project ini fokus ke **orchestration**, bukan transformasi data. Poin
utamanya: retry otomatis kalau API gagal, beberapa kota diproses paralel,
dan kalau satu kota gagal total (setelah semua retry habis) kota lain tetap
lanjut diproses -- pipeline tidak "all-or-nothing".

## Desain: business logic dipisah dari orchestration
```
src/transform.py  → pure functions (parsing, validasi) — TIDAK tahu soal Prefect
src/db.py         → pure functions (insert ke SQLite) — TIDAK tahu soal Prefect
src/flows.py      → HANYA wiring: @task/@flow, retry policy, urutan eksekusi
```
Kenapa dipisah begini? Supaya business logic bisa di-unit-test tanpa perlu
menjalankan orchestrator beneran (lihat `tests/test_transform.py` — semua
test di situ jalan tanpa Prefect), dan supaya kalau suatu saat pindah
orchestrator (misal ke Airflow), logic intinya tidak perlu ditulis ulang.

## Arsitektur

```
DEFAULT_CITIES (Jakarta, Bandung, Surabaya, Semarang, Medan)
        │
        ▼ (diproses PARALEL via .submit())
[ fetch_weather_for_city ]  ← retry 3x kalau API gagal
        │
        ▼
[ parse_weather_response + validate_record ]  ← reject data aneh
        │
        ▼
[ load_weather_reading ] → fact_weather_reading (SQLite)
        │
        ▼
pipeline_run_log ← tercatat: berapa kota sukses/gagal per run
        │
        ▼
dashboard/app.py → data cuaca + tab "Pipeline Health"
```

## Struktur folder

```
05-prefect-weather-pipeline/
├── src/
│   ├── transform.py   # business logic murni (testable tanpa Prefect)
│   ├── db.py           # load layer murni (testable tanpa Prefect)
│   └── flows.py         # orchestration: @task, @flow, retry, parallel execution
├── sql/schema.sql
├── dashboard/app.py     # dashboard: data cuaca + observability pipeline
├── tests/test_transform.py
└── requirements.txt
```

## Cara menjalankan

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Jalankan pipeline sekali (ad-hoc)
python src/flows.py

# Buka dashboard
streamlit run dashboard/app.py

# Jalankan test (tidak butuh internet/Prefect server)
pytest tests/
```

### (Opsional) Membuat jadwal otomatis tiap jam
```bash
prefect deployment build src/flows.py:weather_etl_flow \
    --name "hourly-weather-etl" --cron "0 * * * *"
prefect deployment apply weather_etl_flow-deployment.yaml
prefect agent start -q default
```

## Poin teknis yang ditunjukkan project ini
- **Retry policy deklaratif** (`@task(retries=3, retry_delay_seconds=10)`)
  — tidak perlu tulis manual try/except + sleep loop
- **Parallel task execution** (`.submit()`) — 5 kota di-fetch bersamaan,
  bukan satu-satu berurutan
- **Partial failure tolerance** — satu kota gagal tidak menggagalkan
  seluruh run
- **Pipeline observability** — setiap run tercatat statusnya
  (`pipeline_run_log`), bukan cuma datanya
- **Separation of concerns**: business logic vs orchestration layer,
  supaya testable dan tidak terkunci ke satu framework
- **Idempotent write** (`INSERT OR IGNORE` + `UNIQUE` constraint)

## Kemungkinan pengembangan lanjutan
- Tambahkan Prefect notification block (Slack/email) kalau ada
  `partial_failure`
- Ganti Open-Meteo dengan sumber data lain yang butuh API key + secrets
  management (Prefect Blocks)
- Deploy ke Prefect Cloud (gratis untuk personal use) untuk UI monitoring
- Tambahkan caching supaya kota yang datanya belum berubah tidak di-fetch ulang
