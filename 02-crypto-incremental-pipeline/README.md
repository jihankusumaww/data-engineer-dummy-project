# Crypto Price Incremental Pipeline

Pipeline yang menarik data harga cryptocurrency dari API publik (CoinGecko)
secara berkala, memprosesnya secara **incremental** (bukan full reload tiap
kali), lalu menampilkannya di dashboard interaktif — semuanya berjalan lokal
tanpa Docker.

## Kenapa project ini dibuat
Menunjukkan pola yang umum dipakai di pipeline data real-time/near-real-time:
polling API, append-only raw layer, dan **watermark-based incremental
processing** — supaya pipeline tidak memproses ulang data yang sudah
diproses sebelumnya (penting untuk efisiensi di skala besar).

## Arsitektur

```
CoinGecko API
     │  (polling per interval)
     ▼
[ extract_api.py ] → ambil snapshot harga terkini
     │
     ▼
raw_price_snapshot (append-only, raw layer)
     │
     ▼
[ pipeline.py ] → baca watermark → proses HANYA data baru
     │              → hitung moving average & % perubahan
     ▼
fact_price_hourly (clean layer, siap dianalisis)
     │
     ▼
pipeline_watermark → update "sudah diproses sampai mana"
     │
     ▼
[ dashboard/app.py ] → visualisasi Streamlit
```

## Struktur folder

```
02-crypto-incremental-pipeline/
├── src/
│   ├── extract_api.py   # extract dari CoinGecko API
│   └── pipeline.py       # load raw + incremental transform + watermark logic
├── sql/schema.sql         # raw, fact, dan watermark table
├── dashboard/app.py       # dashboard Streamlit
├── tests/test_pipeline.py # unit test watermark & incremental logic
└── requirements.txt
```

## Cara menjalankan

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Jalankan pipeline (idealnya beberapa kali dengan jeda, untuk simulasi data historis)
python src/pipeline.py

# Buka dashboard
streamlit run dashboard/app.py
```

## Menjadwalkan pipeline
Supaya data terus bertambah tiap jam tanpa Airflow/Docker, pakai cron:
```
0 * * * * cd /path/ke/project && venv/bin/python src/pipeline.py
```

Jalankan test:
```bash
pytest tests/
```

## Poin teknis yang ditunjukkan project ini
- Integrasi dengan **REST API publik** sebagai sumber data
- **Append-only raw layer** (pola yang umum di data lake / bronze layer)
- **Watermark-based incremental processing** — hanya memproses data baru
- Perhitungan metrik turunan (moving average, % perubahan) yang menyambung
  antar-run, bukan cuma dalam satu batch
- Idempotent write (`INSERT OR IGNORE` / `INSERT OR REPLACE`) supaya pipeline
  aman dijalankan ulang tanpa duplikasi
- Dashboard interaktif untuk konsumsi data akhir
- Unit test untuk logika incremental (bukan cuma manual testing)

## Kemungkinan pengembangan lanjutan
- Ganti polling dengan webhook/streaming source (Kafka) untuk true real-time
- Tambahkan alerting kalau harga berubah drastis
- Ganti SQLite dengan warehouse cloud (BigQuery/Snowflake) untuk skala besar
- Deploy dashboard ke Streamlit Community Cloud
