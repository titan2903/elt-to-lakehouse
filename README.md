# Data Engineering Portofolio: ELT to Lakehouse

Proyek ini mendemonstrasikan progresi arsitektur data dari pipeline ELT batch konvensional menjadi arsitektur Lakehouse modern. Dibangun secara bertahap (Fase 1 → Fase 2 → Fase 3) untuk menunjukkan kemampuan mendesain, memigrasi arsitektur, dan menerapkan *best practices* data engineering, bukan sekadar mengeksekusi tutorial tunggal.

## Arsitektur Tingkat Tinggi (Evolusi)

Proyek ini direncanakan dan dieksekusi dalam tiga fase utama:

1. **Fase 1 (Baseline)**: Batch ELT menggunakan Python custom script (ingestion), Airflow (orchestration), PostgreSQL (storage), dbt-postgres (transformation), dan Metabase (visualization).
2. **Fase 2 (Lakehouse Migration)**: Migrasi ingestion ke dlt, storage ke MinIO (Parquet), dan compute layer ke DuckLake + DuckDB (`dbt-duckdb`), dengan PostgreSQL bertindak sebagai *serving layer* (mart schema).
3. **Fase 3 (Data Quality & Alerting)**: Penambahan Soda Core untuk *data quality checks* terotomatisasi di Airflow DAGs, dan integrasi alerting via webhook n8n ke Telegram.

*(Detail diagram arsitektur dan dokumentasi teknis untuk setiap fase dapat dilihat di folder `docs/` setelah fase tersebut diimplementasikan)*

## Quick Start (DEMO_MODE)

Proyek ini dilengkapi dengan `DEMO_MODE` yang menggunakan *seed data* (sampel JSON snapshot GitHub API) sehingga dapat langsung dieksekusi di *local machine* tanpa memerlukan akses token atau API keys eksternal.

```bash
# 1. Clone repository
git clone https://github.com/username/elt-to-lakehouse.git
cd elt-to-lakehouse

# 2. Siapkan environment variables (gunakan template bawaan)
cp .env.example .env

# 3. Setup, jalankan container, dan load sample data
make setup
make up
make seed
```

## Dokumentasi Pembahasan & Desain

Setiap fase memiliki dokumentasi mendetail terkait alasan arsitektural, *trade-off*, keputusan teknis, dan evaluasi hasil:

- [Fase 1: Batch ELT Baseline](docs/architecture-v1.md)
- [Fase 2: Lakehouse Migration](docs/architecture-v2.md) *(Akan datang)*
- [Fase 3: Data Quality, Monitoring & Alerting](docs/architecture-v3.md) *(Akan datang)*
- [Catatan Evaluasi Diri](docs/self-evaluation/)

## Arsitektur Baseline (Fase 1)

Fase 1 menggunakan pendekatan konvensional dengan ekstraksi via *Python scripts* (REST API pagination), dimuat mentah (raw JSON) ke dalam PostgreSQL, lalu ditransformasikan menggunakan `dbt-postgres` ke dalam skema *star schema* (fakta & dimensi) sebelum divisualisasikan oleh Metabase. Pendekatan ini sengaja dibuat manual tanpa *tools* ingestion seperti `dlt` untuk mendemonstrasikan fondasi dasar ELT sebelum diabstraksi di fase-fase berikutnya.

## Tech Stack Utama
- **Orchestration**: Apache Airflow
- **Ingestion**: Python (custom REST API pagination), dlt (data load tool)
- **Lakehouse Layer**: MinIO (storage), DuckLake (catalog), DuckDB (compute)
- **Transformation**: dbt-core (`dbt-postgres`, `dbt-duckdb`)
- **Data Quality**: Soda Core
- **Serving & Visualization**: PostgreSQL, Metabase
- **Alerting & Routing**: n8n, Telegram Bot API
- **Infrastructure**: Docker Compose, Makefile

## Lisensi

Kode asli di dalam repositori ini didistribusikan di bawah [MIT License](LICENSE).