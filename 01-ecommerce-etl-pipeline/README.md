# E-Commerce Sales ETL Pipeline

Pipeline ETL batch untuk mengubah data transaksi e-commerce yang mentah dan
"kotor" menjadi data warehouse dengan skema bintang (star schema) yang siap
dianalisis — tanpa perlu Docker atau database server terpisah (pakai SQLite).

## Kenapa project ini dibuat
Menyimulasikan masalah nyata yang sering dihadapi data engineer: data sumber
dari sistem operasional biasanya punya duplikat, format tanggal tidak
konsisten, nilai kosong, dan whitespace liar. Pipeline ini menunjukkan cara
menangani semuanya secara terstruktur dan bisa diverifikasi (testable).

## Arsitektur

```
CSV mentah (data/raw/sales_raw.csv)
        │
        ▼
   [ extract.py ]   → baca raw data
        │
        ▼
   [ transform.py ] → cleaning + normalisasi + data quality gate
        │
        ▼
   [ load.py ]       → load ke star schema (SQLite)
        │
        ▼
   data/warehouse.db
   ├── dim_customer
   ├── dim_product
   ├── dim_date
   └── fact_sales
        │
        ▼
   [ dashboard/app.py ] → visualisasi Streamlit
```

Kalau salah satu data quality check gagal (misalnya ada quantity ≤ 0 atau
order_id duplikat), pipeline **berhenti (fail-fast)** dan tidak memuat data
kotor ke warehouse — ini prinsip penting dalam data engineering.

## Struktur folder

```
01-ecommerce-etl-pipeline/
├── data/raw/sales_raw.csv     # data sumber (sengaja dibuat "kotor")
├── src/
│   ├── extract.py             # extract layer
│   ├── transform.py           # transform + data quality checks
│   ├── load.py                # load ke SQLite (star schema)
│   └── run_pipeline.py        # orkestrasi end-to-end
├── sql/
│   ├── schema.sql              # DDL star schema
│   └── analysis_queries.sql    # contoh query analitik
├── dashboard/app.py            # dashboard Streamlit
├── tests/test_transform.py    # unit test dengan pytest
└── requirements.txt
```

## Cara menjalankan

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

python src/run_pipeline.py
```

Setelah selesai, warehouse SQLite ada di `data/warehouse.db`. Bisa dicek lewat SQL:

```bash
sqlite3 data/warehouse.db < sql/analysis_queries.sql
```

Atau buka dashboard-nya:
```bash
streamlit run dashboard/app.py
```
Dashboard akan tampil di browser (`localhost:8501`) dengan total revenue, tren harian, revenue per kategori, produk terlaris, dan top 10 customer.

Jalankan test:
```bash
pytest tests/
```

## Menjadwalkan pipeline (tanpa Airflow/Docker)
Untuk skenario production ringan, pipeline ini bisa dijadwalkan pakai cron
(Linux/Mac) atau Task Scheduler (Windows):
```
0 1 * * * cd /path/ke/project && venv/bin/python src/run_pipeline.py
```

## Poin teknis yang ditunjukkan project ini
- Desain **star schema** (fact & dimension tables)
- **Data quality checks** dengan fail-fast strategy
- Modular ETL (extract/transform/load terpisah, gampang di-unit-test)
- **Idempotency-aware design** — skema dan constraint (UNIQUE) mencegah data
  duplikat masuk ke dimension table
- Logging terstruktur untuk observability
- Unit testing dengan pytest

## Kemungkinan pengembangan lanjutan
- Ganti sumber data CSV menjadi API/database source
- Ganti SQLite dengan PostgreSQL/BigQuery untuk skala produksi
- Tambahkan orkestrasi dengan Airflow/Prefect
- Tambahkan incremental load (saat ini masih full load setiap run)
