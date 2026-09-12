# Web Server Log Analytics Pipeline

Pipeline untuk parsing dan monitoring log server (Nginx/Apache-style access
log) — data yang sifatnya **teks tidak terstruktur**, bukan CSV/API yang
sudah rapi seperti dua project lain di portofolio ini. Dashboard-nya bisa
langsung memproses file log yang di-upload dari browser.

## Kenapa project ini berbeda dari 2 project lain
| | Project 1 (ETL E-Commerce) | Project 2 (Crypto Incremental) | Project 3 (ini) |
|---|---|---|---|
| Sumber data | CSV terstruktur | REST API (JSON) | **Teks log mentah (unstructured)** |
| Tantangan utama | Data quality (duplikat, null) | Incremental processing | **Parsing dengan regex, schema-on-read** |
| Strategi error | Fail-fast (stop kalau ada masalah) | Idempotent write | **Tolerant parsing (skip & catat, tidak stop)** |
| Interaksi dashboard | Baca DB hasil pipeline | Baca DB hasil pipeline | **Upload file langsung dari browser** |

## Arsitektur

```
access.log (raw text, campur baris valid & rusak)
     │
     ▼
[ parser.py ]  → regex parsing per baris, return None kalau gagal
     │
     ▼
[ pipeline.py ] → pisahkan baris valid vs gagal
     │
     ├──► fact_log_event      (baris valid, terstruktur)
     ├──► parse_error_log     (baris gagal, untuk audit)
     └──► pipeline_run_summary (ringkasan tiap run: success rate, dll)
     │
     ▼
[ dashboard/app.py ] → visualisasi + bisa upload file log baru langsung
```

## Struktur folder

```
03-log-analytics-pipeline/
├── data/raw/access.log     # sample log (sengaja ada baris korup/rusak)
├── src/
│   ├── parser.py            # regex parser, tolerant terhadap baris rusak
│   └── pipeline.py           # orkestrasi + load ke SQLite
├── sql/schema.sql
├── dashboard/app.py          # dashboard Streamlit + fitur upload file
├── tests/test_parser.py      # unit test parser
└── requirements.txt
```

## Cara menjalankan

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Cara 1: jalankan pipeline lewat terminal
python src/pipeline.py                     # pakai sample data/raw/access.log
python src/pipeline.py path/ke/log_lain.log # atau pakai file log lain

# Cara 2: langsung lewat dashboard (lebih interaktif)
streamlit run dashboard/app.py
```

Di dashboard, kamu bisa pilih pakai sample data bawaan, atau **upload file
`.log`/`.txt` sendiri** lewat sidebar — pipeline akan langsung parsing dan
menampilkan hasilnya real-time, termasuk baris mana saja yang gagal di-parse.

Jalankan test:
```bash
pytest tests/
```

## Poin teknis yang ditunjukkan project ini
- **Parsing data tidak terstruktur** dengan regex (skill yang sering
  dibutuhkan untuk log, teks, atau sumber data non-tabular lain)
- **Tolerant/graceful error handling** — baris rusak tidak menghentikan
  pipeline, tapi tetap tercatat untuk audit (beda pendekatan dari
  fail-fast di Project 1)
- **Data quality observability** — setiap run tercatat di
  `pipeline_run_summary` (success rate parsing), bukan cuma pass/fail biner
- **Time-series aggregation** (request per jam) dan analisis sederhana untuk
  deteksi anomali (IP dengan request bertubi-tubi)
- Dashboard dengan **input dinamis dari user** (file upload), bukan cuma
  menampilkan data yang sudah diproses sebelumnya

## Kemungkinan pengembangan lanjutan
- Tambahkan deteksi anomali otomatis (misal alert kalau error rate > threshold)
- Dukung format log lain (JSON log, syslog)
- Streaming ingestion pakai file watcher, bukan batch upload
- Load ke data lake (S3) untuk skala besar
