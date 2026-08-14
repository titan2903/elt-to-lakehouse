# Data Engineering Portofolio: ELT to Lakehouse

Proyek ini mendemonstrasikan progresi arsitektur data dari pipeline ELT konvensional menjadi arsitektur Lakehouse modern. Proyek ini dibangun untuk menunjukkan kemampuan mendesain sistem, melakukan migrasi arsitektur yang *scalable*, dan menerapkan *best practices* data engineering secara utuh (End-to-End).

## Arsitektur Tingkat Tinggi (Evolusi)

Proyek ini merupakan kesatuan sistem yang berevolusi melalui tiga pendekatan utama:

1. **Baseline ELT**: Batch ELT menggunakan Python custom script (ingestion), Airflow (orchestration), PostgreSQL (storage), dbt-postgres (transformation), dan Metabase (visualization).
2. **Lakehouse Migration**: Migrasi lapisan ingestion menggunakan dlt, penyimpanan *raw data* ke MinIO (Parquet), dan pemrosesan analitik menggunakan DuckLake + DuckDB (`dbt-duckdb`), dengan PostgreSQL bertindak sebagai *serving layer* (mart schema).
3. **Data Quality & Alerting**: Observabilitas penuh dengan menambahkan Soda Core untuk *data quality checks* otomatis di dalam DAG Airflow, serta integrasi *alerting* *real-time* via webhook n8n ke Telegram.

*(Detail diagram arsitektur dan dokumentasi teknis untuk setiap tahapan evolusi dapat dilihat di folder `docs/`)*

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

Repositori ini menyertakan dokumentasi mendetail terkait alasan arsitektural, *trade-off*, keputusan teknis, dan evaluasi hasil:

- [Arsitektur Baseline ELT](docs/architecture-v1.md)
- [Arsitektur Migrasi Lakehouse](docs/architecture-v2.md)
- [Arsitektur Data Quality, Monitoring & Alerting](docs/architecture-v3.md)
- [Catatan Evaluasi Diri](docs/self-evaluation/)

## Detail Komponen Arsitektur

### 1. Pendekatan Baseline ELT
Menggunakan pendekatan konvensional dengan ekstraksi via *Python scripts* (REST API pagination), dimuat mentah (raw JSON) ke dalam PostgreSQL, lalu ditransformasikan menggunakan `dbt-postgres` ke dalam skema *star schema* (fakta & dimensi) sebelum divisualisasikan oleh Metabase. Pendekatan ini mendemonstrasikan pemahaman kuat atas fondasi dasar ELT sebelum diabstraksi ke *tools* modern.

### 2. Implementasi Arsitektur Lakehouse
Penyimpanan *raw data* dari database operasional dipindahkan ke *Object Storage* (MinIO) dalam format Parquet, membentuk arsitektur Lakehouse yang *scalable*. *Compute layer* dipisahkan dari *storage layer* menggunakan DuckDB secara *in-memory* yang membaca Parquet langsung dari MinIO. dbt-duckdb melakukan transformasi dan hasilnya dimaterialisasikan kembali ke PostgreSQL sebagai *serving layer* melalui koneksi ATTACH, mengoptimalkan proses tanpa membebani database utama.

### 3. Implementasi Data Quality & Alerting
Observabilitas pipeline dijamin dengan menambahkan pemeriksaan kualitas data (*data quality checks*) menggunakan Soda Core, dan *alerting* otomatis ke Telegram menggunakan n8n.
- **Data Quality Strategy**: Pemeriksaan dibagi menjadi pengecekan *raw layer* (freshness & validasi dasar sebelum transformasi dbt) dan *mart layer* (integritas data setelah transformasi dbt) demi mencegah perambatan data kotor ke dashboard.
- **Alerting Boundary (Separation of Concerns)**: Airflow hanya bertanggung bertanggung jawab menyadari kegagalan (deteksi) lalu mengirim HTTP POST webhook, sedangkan n8n memegang logika merutekan (routing) dan memformat (*formatting*) pesan untuk dikirim ke Telegram.

*Disclaimer: Penggunaan `n8n` dalam repositori ini tunduk pada "Sustainable Use License". Ia disertakan secara khusus semata-mata sebagai dependensi runtime (orchestrator notifikasi mandiri).*

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