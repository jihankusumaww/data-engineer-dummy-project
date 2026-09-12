# Subscription Analytics — dbt + DuckDB

Project analytics engineering yang mengubah data mentah subscription/SaaS
menjadi data mart yang siap dipakai untuk analisis bisnis (MRR, churn,
customer lifetime value), dibangun dengan **dbt** (industry-standard
transformation tool) dan **DuckDB** (embedded OLAP database, tanpa perlu
server terpisah).

> ⚠️ **Catatan jujur:** project ini butuh koneksi internet untuk instalasi
> (`pip install dbt-core dbt-duckdb`) dan saya tidak bisa menjalankan/test
> secara end-to-end di sandbox saya sendiri (tidak ada akses internet di
> sana). SQL dan struktur project ditulis mengikuti konvensi dbt yang
> standar, tapi kalau ketemu error kecil saat pertama kali dijalankan,
> kemungkinan cuma soal versi dbt/duckdb adapter — kabari saya untuk dibantu
> debug.

## Kenapa project ini beda dari yang lain di portofolio ini
Project 1-3 di portofolio ini logic transform-nya ditulis manual pakai
pandas/Python. Project ini menunjukkan pendekatan **analytics engineering**
modern: transformasi data ditulis sebagai **SQL + Jinja templating** yang
di-manage, di-test, dan di-dokumentasikan oleh dbt — pendekatan yang dipakai
banyak perusahaan (Airbnb, GoJek, dll) untuk data warehouse/data mart mereka.

## Arsitektur (medallion: raw → staging → marts)

```
seeds/ (raw CSV: customers, subscriptions, payments)
        │  dbt seed
        ▼
   raw.raw_customers, raw.raw_subscriptions, raw.raw_payments
        │
        ▼
models/staging/  (rename, cast type, cents→dollars)
   stg_customers, stg_subscriptions, stg_payments
        │
        ▼
models/marts/    (business logic, dimensional model)
   ├── dim_customers   → status subscription terkini per customer
   ├── fct_subscriptions → durasi & total pembayaran per subscription
   └── fct_mrr          → Monthly Recurring Revenue per plan per bulan
                           (pakai pola "date spine")
        │
        ▼
   dashboard/app.py → visualisasi Streamlit
```

## Struktur folder

```
04-dbt-analytics-engineering/
├── dbt_project.yml
├── profiles.yml              # koneksi ke DuckDB (self-contained, lihat isinya)
├── seeds/                     # raw CSV data
├── models/
│   ├── staging/                # 1:1 dengan source, cleaning ringan
│   └── marts/                  # business logic, dimensional model
├── macros/cents_to_dollars.sql # custom macro dbt
└── dashboard/app.py            # dashboard Streamlit
```

## Cara menjalankan

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Arahkan dbt ke profiles.yml di folder project ini (bukan ~/.dbt/)
export DBT_PROFILES_DIR=$(pwd)     # Windows: set DBT_PROFILES_DIR=%cd%

dbt seed          # load CSV mentah ke DuckDB
dbt run           # jalankan semua transformasi staging + marts
dbt test          # jalankan semua data quality test (unique, not_null, relationships, dll)
dbt docs generate && dbt docs serve   # (opsional) lihat dokumentasi & lineage graph interaktif

# Buka dashboard
streamlit run dashboard/app.py
```

## Poin teknis yang ditunjukkan project ini
- **Medallion architecture** (raw → staging → marts) — standar de-facto di
  modern data stack
- **dbt tests** built-in (`unique`, `not_null`, `relationships`,
  `accepted_values`) — data quality didefinisikan secara deklaratif, bukan
  kode manual
- **Date spine pattern** untuk menghitung metrik time-series (MRR) yang
  benar meskipun tidak ada event baru di suatu bulan — pola SQL analytics
  yang sering ditanyakan di interview data/analytics engineer
- **Custom dbt macro** (`cents_to_dollars`) — reusable logic di seluruh model
- **dbt docs & lineage graph** — dokumentasi dan dependency antar model
  ter-generate otomatis
- Pemisahan source-of-truth SQL dari visualisasi (dashboard cuma query,
  tidak ada business logic di layer presentasi)

## Kemungkinan pengembangan lanjutan
- Tambahkan `dbt_utils` package untuk date spine yang lebih robust
- Tambahkan snapshot dbt untuk SCD Type 2 (tracking histori perubahan plan)
- Ganti DuckDB dengan Snowflake/BigQuery untuk skala produksi (tinggal ganti
  `profiles.yml`, model SQL tidak perlu banyak berubah)
- Deploy dbt docs ke GitHub Pages
