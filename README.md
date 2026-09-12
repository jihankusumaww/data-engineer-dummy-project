# Portofolio Data Engineer

Dua project data engineering yang dirancang untuk dijalankan ringan di laptop
biasa — cukup Python + SQLite, **tanpa Docker/database server**, tapi tetap
menunjukkan konsep inti data engineering: ETL, star schema, data quality,
incremental processing, orkestrasi, dan testing.

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

## Tech stack (sengaja ringan)
- **Python** (pandas, requests)
- **SQLite** sebagai warehouse (tanpa perlu install/setup database server)
- **Streamlit** untuk dashboard (ketiga project punya dashboard-nya masing-masing)
- **pytest** untuk unit testing
- Orkestrasi via cron (didokumentasikan di masing-masing README), bukan
  Airflow — supaya tidak perlu resource besar untuk menjalankannya

## Cara pakai portofolio ini
Masing-masing folder project adalah repo yang berdiri sendiri — silakan
push tiap folder sebagai repo GitHub terpisah (lebih rapi untuk ditaruh di
CV/LinkedIn), atau jadikan satu repo mono-repo. Setiap project punya README
sendiri dengan instruksi detail cara menjalankan.

## Catatan untuk lamaran kerja
Di CV/portofolio, sertakan link ke masing-masing repo + 1-2 kalimat tentang
masalah apa yang diselesaikan (bukan cuma "bikin pipeline ETL") — misalnya:
"Merancang pipeline ETL dengan data quality gate yang mencegah data kotor
masuk ke warehouse" lebih kuat daripada sekadar "membuat script Python".
