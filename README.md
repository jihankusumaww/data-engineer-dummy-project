# Portofolio Data Engineer

Lima project data engineering dan analytics engineering yang dirancang untuk
menunjukkan konsep nyata: ETL, star schema, data quality, incremental
processing, dbt modeling, orchestration, observability, dan testing.

## Daftar Project

### 1. [E-Commerce Sales ETL Pipeline](./01-ecommerce-etl-pipeline)
Pipeline batch klasik: membersihkan data transaksi yang "kotor" (duplikat,
format tanggal campuran, nilai kosong) dan memuatnya ke data warehouse
dengan **star schema**, lalu divisualisasikan lewat **dashboard Streamlit**
(revenue per kategori, tren harian, top customer, produk terlaris).
Menunjukkan: data quality gate (fail-fast), dimensional modeling, unit testing.

### 2. [Crypto Price Incremental Pipeline](./02-crypto-incremental-pipeline)
Pipeline yang menarik data dari **REST API publik**, memprosesnya secara
**incremental** memakai watermark (bukan full reload), menghitung metrik
turunan (moving average, % perubahan), dan menampilkannya di **dashboard
Streamlit**. Menunjukkan: integrasi API, append-only raw layer, incremental
processing, idempotent write.

### 3. [Web Server Log Analytics Pipeline](./03-log-analytics-pipeline)
Pipeline untuk parsing **data teks tidak terstruktur** (log server ala
Nginx/Apache) dengan regex, tahan terhadap baris korup (tolerant parsing,
bukan fail-fast), dan **dashboard Streamlit yang bisa langsung memproses
file log yang di-upload user**. Menunjukkan: schema-on-read, data quality
observability (success rate parsing per run), deteksi pola anomali sederhana.

### 4. [Subscription Analytics — dbt + DuckDB](./04-dbt-analytics-engineering)
Project analytics engineering yang mengubah data subscription menjadi data
mart bisnis menggunakan **dbt** dan **DuckDB**. Model staging dan marts
menghasilkan MRR dengan pola date spine, status customer, total pembayaran,
serta dilengkapi dbt tests dan dokumentasi model. Dashboard Streamlit
menampilkan MRR, active subscribers, churn, dan plan economics.

Menunjukkan: SQL modular, Jinja templating, dimensional modeling, data tests,
documentation-driven development, dan analytics-ready marts.

### 5. [Multi-City Weather ETL — Prefect](./05-prefect-weather-pipeline)
Pipeline yang mengambil data cuaca dari Open-Meteo untuk beberapa kota dengan
**Prefect**. Setiap task punya retry policy, kota yang gagal tidak menghentikan
kota lain, dan setiap run dicatat ke tabel observability. Dashboard Streamlit
menampilkan kondisi kota, tren suhu, status run, dan partial failure.

Menunjukkan: orchestration, retries, parallel execution, partial-failure
tolerance, pipeline health tracking, dan API integration.

## Tech stack (sengaja ringan)
- **Python** (pandas, requests)
- **SQLite** untuk warehouse dan observability pipeline
- **DuckDB + dbt** untuk analytics engineering dan data marts
- **Prefect** untuk orchestration, retries, dan flow monitoring
- **Streamlit** untuk dashboard setiap project
- **pytest** untuk unit testing

## Deployment dashboard

Semua dashboard dapat dideploy sebagai app terpisah di Streamlit Cloud dari
repository GitHub yang sama. Gunakan `main` sebagai branch dan pilih entrypoint
berikut pada field **Main file path**:

```text
01-ecommerce-etl-pipeline/dashboard/app.py
02-crypto-incremental-pipeline/dashboard/app.py
03-log-analytics-pipeline/dashboard/app.py
04-dbt-analytics-engineering/dashboard/app.py
05-prefect-weather-pipeline/dashboard/app.py
```

## Cara pakai portofolio ini
Semua project berada dalam satu repository mono-repo. Setiap folder memiliki
README dan dependency sendiri sehingga bisa dijalankan atau dideploy secara
terpisah.

## Catatan untuk lamaran kerja
Di CV/portofolio, sertakan link ke masing-masing repo + 1-2 kalimat tentang
masalah apa yang diselesaikan (bukan cuma "bikin pipeline ETL") — misalnya:
"Merancang pipeline ETL dengan data quality gate yang mencegah data kotor
masuk ke warehouse" lebih kuat daripada sekadar "membuat script Python".
