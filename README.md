```markdown

```

# 🗄️ Enterprise Data & Analytics Engineering Lab

**Production-grade data pipelines built with robust architecture, data quality gates, incremental loading, and workflow orchestration.**

---

> ⚡ **Dynamic Repository Notice:** Repository ini merupakan *living engineering lab*. Modul baru, pengujian arsitektur *cloud-native*, serta otomatisasi pipeline tingkat lanjut akan terus di-commit secara berkala seiring berjalannya riset dan pengembangan.

---

## ⚡ Technical Matrix & Complexity Level

| Module | Core Paradigm | Complexity / Target Level | Storage Layer | Compute / Orchestration | Quality Assurance |
| --- | --- | --- | --- | --- | --- |
| **01. E-Commerce** | Batch ETL & Dimensional Modeling | `MID-LEVEL` | SQLite (OLTP) | Python (Pandas) | Fail-fast Assertions (`pytest`) |
| **02. Crypto Ingestion** | Incremental Loading & Watermarking | `MID TO HIGH` | SQLite | REST API Polling | Idempotency Key Checks |
| **03. Log Analytics** | Unstructured Parsing & Observability | `MID TO HIGH` | SQLite | RegEx Engine | Quarantine Rate Monitoring |
| **04. Subscription Mart** | Analytics Engineering & Date-Spine | `HIGH (ADVANCED)` | DuckDB (OLAP) | dbt Core | `dbt test` (Schema & Unique) |
| **05. Weather ETL** | Distributed Extraction & Fault Isolation | `HIGH (ADVANCED)` | SQLite | Prefect Core | Task-level Retries |

---

## 🏗️ System Architecture & Deep Dives

### 01. 🛒 E-Commerce Sales Batch Pipeline

* **Target Level:** `MID-LEVEL`
* **Focus:** Data Quality Gate, Star Schema, Unit Testing

```
  ┌────────────┐     ┌──────────────────────┐     ┌────────────────────────┐     ┌─────────────────┐
  │  Raw Data  │ ──► │ Pandas Quality Gate  │ ──► │  Star Schema Modeler   │ ──► │ SQLite Storage  │
  │ (Dirty CSV)│     │  (Error Threshold)   │     │ (Fact & Dim Tables)    │     │  (Streamlit BI) │
  └────────────┘     └──────────────────────┘     └────────────────────────┘     └─────────────────┘

```

#### Engineering Highlights:

* **Quality Gate Formula:** Pipeline akan menghentikan eksekusi secara otomatis (*fail-fast*) jika tingkat anomali data melampaui batas ambang:

$$\text{Error Rate} = \frac{N_{\text{invalid}}}{N_{\text{total}}} > 0.05$$

* **Data Modeling:** Konversi data mentah menjadi **Dimensional Modeling** berstandar industri: `fact_sales`, `dim_customers`, `dim_products`, dan `dim_dates`.

📁 `cd 01-ecommerce-etl-pipeline`

---

### 02. 📈 Crypto Price Incremental Engine

* **Target Level:** `MID TO HIGH`
* **Focus:** State-driven Extraction, Watermarking, Idempotent Ingestion

```
  ┌────────────────┐     ┌─────────────────────┐     ┌──────────────────────┐
  │ CoinGecko API  │ ──► │ Watermark Extractor │ ──► │ Append-Only Storage  │
  │ (REST Endpt)   │     │ (State: last_tstamp)│     │  (Idempotent Write)  │
  └────────────────┘     └─────────────────────┘     └──────────────────────┘

```

#### Engineering Highlights:

* **State Management:** Memanfaatkan teknik *watermarking* berbasis timestamp `T_{last}` untuk mengeliminasi ekstraksi data ganda:

$$\text{Query Filter:} \quad \text{timestamp} > T_{\text{last}}$$

* **Idempotency Execution:** Menjamin integritas data menggunakan constraint `UNIQUE(coin_id, timestamp)` pada level database agar transaksi yang sama tidak terisi ganda meskipun pipeline dijalankan secara repetitif.

📁 `cd 02-crypto-incremental-pipeline`

---

### 03. 📄 Web Log Stream Parser & Observability

* **Target Level:** `MID TO HIGH`
* **Focus:** Schema-on-Read, Fault-Tolerant Parsing, Anomaly Detection

```
  ┌─────────────────┐     ┌───────────────────┐     ├─► Valid Log ──► Metrics Table
  │ Unstructured    │ ──► │ RegEx Parser      │ ────┤
  │ Web Log (.log)  │     │ (Try-Catch Block) │     └─► Malformed ──► Dead Letter Queue
  └─────────────────┘     └───────────────────┘

```

#### Engineering Highlights:

* **Resilient Ingestion:** Parsing string log heterogen menggunakan ekspresi reguler yang terenkapsulasi, mencegah *catastrophic failure* saat menemukan payload rusak.
* **Pipeline Observability:** Pemantauan indikator kesehatan pipeline secara kuantitatif:

$$\text{Parsing Success Rate} = \left( 1 - \frac{N_{\text{quarantine}}}{N_{\text{processed}}} \right) \times 100\%$$

📁 `cd 03-log-analytics-pipeline`

---

### 04. 💳 Subscription Analytics (dbt + DuckDB)

* **Target Level:** `HIGH (ADVANCED)`
* **Focus:** Analytics Engineering, Modular SQL, Date Spine Modeling

```
  ┌───────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌────────────────┐
  │ Raw Source    │ ──► │ dbt Staging     │ ──► │ Intermediate    │ ──► │ Data Marts     │
  │ (DuckDB OLAP) │     │ (Renaming/Cast) │     │ (Date-Spine Logic)    │ (fct_mrr/users)│
  └───────────────┘     └─────────────────┘     └─────────────────┘     └────────────────┘

```

#### Engineering Highlights:

* **SaaS Metric Computation:** Membangun kalkulasi *Monthly Recurring Revenue* (MRR) dan *Churn Rate* menggunakan teknik *Date-Spine* untuk menangani kesenjangan tanggal (*date gaps*).
* **Automated Data Contracts:** Menjalankan `dbt test` untuk validasi keunikan entitas, integritas *foreign key*, dan kendala *not-null*.

📁 `cd 04-dbt-analytics-engineering`

---

### 05. ⛅ Multi-City Weather Pipeline (Prefect Orchestrated)

* **Target Level:** `HIGH (ADVANCED)`
* **Focus:** DAG Orchestration, Distributed Retries, Partial-Failure Isolation

```
           ┌──► Task: City A ──► Retry Policy (3x) ──► Load DB
  Flow DAG ┼──► Task: City B ──► Fail & Log Quarantine 
           └──► Task: City C ──► Retry Policy (3x) ──► Load DB

```

#### Engineering Highlights:

* **Workflow Orchestration:** Mengatur *execution graph* berbasis DAG menggunakan **Prefect**, lengkap dengan otomatisasi *exponential backoff retries*.
* **Fault Isolation:** Kegagalan ekstraksi pada satu node/wilayah tidak menggagalkan seluruh alur data, melainkan diisolasi ke *audit trail table*.

📁 `cd 05-prefect-weather-pipeline`

---

## 💻 Local Developer Guide

### 1. Environment Setup

```bash
# Clone the repository
git clone [https://github.com/your-username/data-engineering-portfolio.git](https://github.com/your-username/data-engineering-portfolio.git)
cd data-engineering-portfolio

# Initialize Virtual Environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install Core Dependencies
pip install -r requirements.txt

```

### 2. Execution Examples

```bash
# Execute Unit Tests across Pipelines
pytest

# Launch Specific Analytics Dashboard
streamlit run 04-dbt-analytics-engineering/dashboard/app.py

```

---

## 🌐 Streamlit Deployment Index

| Module | Deployment Main File Path |
| --- | --- |
| **01. E-Commerce Pipeline** | `01-ecommerce-etl-pipeline/dashboard/app.py` |
| **02. Crypto Ingestion** | `02-crypto-incremental-pipeline/dashboard/app.py` |
| **03. Log Analytics** | `03-log-analytics-pipeline/dashboard/app.py` |
| **04. dbt Subscription** | `04-dbt-analytics-engineering/dashboard/app.py` |
| **05. Prefect Weather** | `05-prefect-weather-pipeline/dashboard/app.py` |

```

```
