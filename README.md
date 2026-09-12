# Data Engineering Portfolio

Portofolio berisi **3 pipeline ETL / data engineering** yang dirancang ringan di laptop (cukup Python + SQLite, tanpa Docker). Fokus pada konsep praktis: **data quality, incremental processing, tolerant parsing, observability**.

Setiap project punya **dashboard Streamlit** dengan visual design modern (tema gelap charcoal, aksen cyan/amber), bukan cuma tabel polos.

---

## 📊 Project Overview

| # | Project | Problem | Konsep Utama | Tech Stack |
|---|---------|---------|------------|-----------|
| 1 | [E-Commerce ETL](#1-e-commerce-sales-etl-pipeline) | Data kotor (duplikat, format campuran) | Data quality gate, star schema, fail-fast | Python, pandas, SQLite, Streamlit, pytest |
| 2 | [Crypto Incremental](#2-crypto-price-incremental-pipeline) | Reprocessing data lama = boros resource | Watermark-based incremental, append-only | Python, requests, SQLite, Streamlit, pytest |
| 3 | [Log Analytics](#3-web-server-log-analytics-pipeline) | Data tidak terstruktur, baris korup | Tolerant parsing, regex, schema-on-read | Python, regex, SQLite, Streamlit, pytest |

---

## 1. E-Commerce Sales ETL Pipeline

**Problem:** Data transaksi mentah biasanya kotor — duplikat, format tanggal tidak konsisten, nilai kosong. Kalau langsung dipakai analisis, hasilnya bisa salah tanpa disadari.

**Solution:** Pipeline 3-layer (extract → transform → load) dengan **6 data quality checks otomatis**. Data yang tidak lolos validasi **ditolak sebelum masuk warehouse** (fail-fast), bukan diam-diam dimuat.

**Folder:** [`01-ecommerce-etl-pipeline/`](./01-ecommerce-etl-pipeline)

### Quick Start
```bash
cd 01-ecommerce-etl-pipeline
pip install -r requirements.txt
python src/run_pipeline.py
streamlit run dashboard/app.py
```

**Dashboard:** Revenue harian, kategori, produk terlaris, top customers dengan KPI cards yang terformat rapih.

---

## 2. Crypto Price Incremental Pipeline

**Problem:** Pipeline yang ambil data time-series dan reprocess ULANG semua dari awal setiap run = boros resource dan tidak scalable.

**Solution:** Pola **incremental berbasis watermark**: pipeline hanya proses data lebih baru dari checkpoint terakhir. Raw append-only, transform hanya run data baru.

**Folder:** [`02-crypto-incremental-pipeline/`](./02-crypto-incremental-pipeline)

### Quick Start
```bash
cd 02-crypto-incremental-pipeline
pip install -r requirements.txt
python src/pipeline.py
python src/pipeline.py  # Jalankan lagi, lihat incremental processing
streamlit run dashboard/app.py
```

**Dashboard:** Live price tracking, moving average, % perubahan harga dengan market snapshot ringkas.

---

## 3. Web Server Log Analytics Pipeline

**Problem:** Log server = data teks tidak terstruktur dengan baris korup / format tidak konsisten. Pipeline yang "stop" begitu ketemu satu baris rusak tidak realistis.

**Solution:** Parser regex dengan **tolerant parsing**: baris gagal di-parse dicatat audit, tapi tidak stop pipeline. Setiap run track success rate parsing.

**Folder:** [`03-log-analytics-pipeline/`](./03-log-analytics-pipeline)

### Quick Start
```bash
cd 03-log-analytics-pipeline
pip install -r requirements.txt
python src/pipeline.py
streamlit run dashboard/app.py  # Bisa upload file log sendiri atau pakai sample
```

**Dashboard:** Parser health signals, traffic trends per jam, status code mix, top endpoints, IP investigation untuk deteksi bot/abuse.

---

## 🎨 Dashboard Design

Ketiga dashboard **tema visual konsisten**:
- **Dark charcoal background** dengan aksen cyan/amber/merah
- **KPI cards** dengan status indicator (naik ✓ turun ⚠ netral ⊘)
- **Interactive charts** (area chart, bar chart, line chart)
- **Data tables terformat** dengan mata uang / persentase
- **Sidebar** untuk kontrol + status observability

---

## ✅ Testing

Setiap project punya unit tests (pytest):

```bash
cd 01-ecommerce-etl-pipeline && pytest tests/test_transform.py
cd 02-crypto-incremental-pipeline && pytest tests/test_pipeline.py
cd 03-log-analytics-pipeline && pytest tests/test_parser.py
```

---

## 📁 Repository Structure

```
portfolio-data-engineer/
├── 01-ecommerce-etl-pipeline/
│   ├── data/ → warehouse.db, raw/sales_raw.csv
│   ├── src/ → extract.py, transform.py, load.py, run_pipeline.py
│   ├── sql/ → schema.sql, analysis_queries.sql
│   ├── dashboard/ → app.py (Streamlit)
│   ├── tests/ → test_transform.py
│   └── requirements.txt
│
├── 02-crypto-incremental-pipeline/
│   ├── data/ → crypto.db, watermark tracking
│   ├── src/ → extract_api.py, pipeline.py
│   ├── sql/ → schema.sql
│   ├── dashboard/ → app.py (Streamlit)
│   ├── tests/ → test_pipeline.py
│   └── requirements.txt
│
├── 03-log-analytics-pipeline/
│   ├── data/ → logs.db, raw/access.log
│   ├── src/ → parser.py, pipeline.py
│   ├── sql/ → schema.sql
│   ├── dashboard/ → app.py (Streamlit)
│   ├── tests/ → test_parser.py
│   └── requirements.txt
│
└── README.md (this file)
```

---

## 🔑 Key Concepts

| Konsep | Dimana | Penerapan |
|--------|--------|-----------|
| **Data Quality Gate** | Project 1 | 6 automated checks sebelum load (fail-fast: duplikat, email kosong, quantity ≤ 0, dll) |
| **Incremental Processing** | Project 2 | Watermark table track last_processed_utc per coin → hanya proses data baru |
| **Append-only Raw Layer** | Project 2 | Raw data never updated, only appended → audit trail + re-processability |
| **Tolerant Parsing** | Project 3 | Regex parser yang tidak crash di error, log failures untuk audit |
| **Star Schema** | Project 1 | Fact + dimension tables → normalized query, fast join, maintainable |
| **Observability** | Project 2, 3 | Pipeline health tracked (parse success rate, watermark progress, run summary) |
| **Streamlit Dashboards** | All 3 | Modern visual design, KPI cards, interactive charts, data tables |

---

## 💡 Requirements

- **Python 3.8+**
- **pip / venv**
- **SQLite3** (included dengan Python)
- Dependencies listed di tiap `requirements.txt`

---

## 🚀 Quick Start (All Projects)

```bash
# Clone repo
git clone https://github.com/jihankusumaww/data-engineer-dummy-project.git
cd data-engineer-dummy-project

# Pilih project (1, 2, atau 3)
cd 01-ecommerce-etl-pipeline

# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run pipeline
python src/run_pipeline.py  # atau src/pipeline.py atau sesuai project

# Launch dashboard
streamlit run dashboard/app.py
```

Dashboard akan terbuka di `http://localhost:8501`

---

## 🔗 Links

- **GitHub Repo:** https://github.com/jihankusumaww/data-engineer-dummy-project
- **Streamlit Cloud:** (Ready to deploy kapan saja)

---

## 📝 Catatan untuk CV/Lamaran

Saat showcase ke recruiter, jelaskan **problem yang diselesaikan**, bukan cuma "bikin pipeline":

✅ **Good:** "Merancang pipeline ETL dengan 6 data quality checks otomatis yang menolak data kotor sebelum masuk warehouse (fail-fast pattern)"

✅ **Good:** "Implementasi incremental processing dengan watermark table → scalable untuk jutaan baris tanpa reprocess data lama"

✅ **Good:** "Tolerant parsing untuk data tidak terstruktur (log server) yang tetap menghasilkan insight meskipun ada baris korup"

❌ **Avoid:** "Membuat pipeline ETL", "Script Python untuk data processing"

---

**Created:** September 2026  
**Author:** Jihan Kusuma  
**License:** MIT
