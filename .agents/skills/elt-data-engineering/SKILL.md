---
name: elt-data-engineering
description: Use when writing data ingestion pipelines (dlt), transformation models (dbt), configuring Lakehouse components (DuckLake/DuckDB), or writing data quality checks (Soda Core) for the project.
---

# ELT Data Engineering Core

## Overview
Skill ini mengatur bagaimana data mengalir dari sumber (GitHub API) melalui lakehouse layer ke mart layer. Mencakup ingestion, storage, transformation, dan data quality.

## When to Use
- Menulis Python ingestion script atau konfigurasi `dlt` pipeline
- Menulis dbt models (staging, mart) atau konfigurasi `profiles.yml`
- Setup DuckLake catalog atau query via DuckDB
- Menulis Soda Core checks atau dbt tests

## Ingestion Rules

### Fase 1: Custom Python Script
- Sumber: GitHub REST API (pull requests, issues, events dari organisasi/repo publik)
- Pagination: cursor/page-based, tangani semua halaman
- Rate limiting: exponential backoff saat menerima HTTP 429 atau 403
- Incremental load: gunakan field `updated_at` sebagai watermark — JANGAN full load setiap kali
- Script harus modular (function-based), bukan satu file monolitik
- Lokasi: `airflow/dags/github_elt_dag.py` (callable functions yang dipanggil oleh DAG)

### Fase 2: Migrasi ke dlt
- Gunakan `dlt init github` (verified source) atau `rest_api_source`
- Destination: `filesystem` ke MinIO, format Parquet (`loader_file_format="parquet"`)
- Config: `.dlt/config.toml` dengan `endpoint_url` MinIO
- Secrets: `.dlt/secrets.toml` (masuk `.gitignore`)
- Schema evolution detection: aktifkan, alert jika ada field baru/hilang

### DEMO_MODE (Kedua Fase)
- Jika env var `DEMO_MODE=true`, skip API call dan load dari `data/seed/`
- Fase 1: seed data berupa JSON snapshots di `data/seed/`
- Fase 2: seed data berupa Parquet files di MinIO
- JANGAN menggunakan dummy/fake data generator — gunakan snapshot nyata dari GitHub API

## Lakehouse Layer (Fase 2)

```
MinIO (Parquet files) ← "hard disk"
    ↓
DuckLake (catalog di PostgreSQL `ducklake_catalog`) ← "file system"
    ↓
DuckDB (embedded, in-process) ← "CPU"
```

Rules:
- DuckDB adalah library, BUKAN server container. Jangan membuat Docker service untuk DuckDB.
- DuckLake catalog HARUS di PostgreSQL schema `ducklake_catalog` (instance yang sudah ada).
- MinIO menyimpan Parquet files. Pin image version di docker-compose.

## Transformation (dbt)

### Data Modeling — Star Schema WAJIB

```
staging/                    marts/
├── stg_pull_requests.sql   ├── fct_pull_requests.sql   (fact)
├── stg_issues.sql          ├── fct_issues.sql          (fact)
├── stg_events.sql          ├── dim_repos.sql           (dimension)
└── stg_users.sql           ├── dim_users.sql           (dimension)
                            └── dim_labels.sql          (dimension)
```

Rules:
- Fase 1: adapter `dbt-postgres`, semua model di PostgreSQL
- Fase 2: adapter `dbt-duckdb`, staging di DuckDB, mart HARUS ditulis ke PostgreSQL `mart` schema (serving layer Metabase)
- Setiap model HARUS punya `schema.yml` dengan: deskripsi kolom, `not_null` test, `unique` test, `relationships` test
- Minimal 2 dbt unit test (built-in sejak dbt-core 1.8+) untuk model dengan logic non-trivial
- Tambahkan `dbt source freshness` di Fase 2+

## Data Quality — Soda Core (Fase 3)

Tool: **Soda Core** (Apache 2.0). JANGAN gunakan Great Expectations.

### File Structure
```
data_quality/
├── configuration.yml       # connection config (DuckDB + PostgreSQL)
└── checks/
    ├── raw.yml             # checks untuk raw layer
    └── mart.yml            # checks untuk mart layer
```

### Raw Layer Checks (`data_quality/checks/raw.yml`)
| Check | Threshold | Action jika gagal |
|---|---|---|
| `row_count` change | Tidak turun > 50% dari run sebelumnya | Alert `severity=warning` |
| Freshness (`max(updated_at)`) | Tidak lebih lama dari 24 jam | Alert `severity=warning` |
| Schema (kolom wajib) | `id`, `title`, `state`, `created_at`, `updated_at` harus ada | Alert `severity=critical` |

### Mart Layer Checks (`data_quality/checks/mart.yml`)
| Check | Threshold | Action jika gagal |
|---|---|---|
| Referential integrity | Semua `user_id` di `fct_pull_requests` valid di `dim_users` | Alert `severity=critical` |
| Value range | `duration_hours` ≥ 0, `created_at` ≤ now() | Alert `severity=warning` |
| Completeness | Null rate di `title`, `state`, `user_id` < 1% | Alert `severity=warning` |

### Posisi di DAG
```
ingest → soda_check_raw → dbt_run → soda_check_mart → done
```
Soda checks adalah Airflow tasks terpisah, BUKAN bagian dari dbt run.
