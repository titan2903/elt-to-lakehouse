---
name: elt-devops
description: Use when managing docker-compose files, Makefile targets, environment variables, testing strategies, or pinning dependencies for the infrastructure.
---

# ELT DevOps & Infrastructure

## Overview
Skill ini memastikan proyek tetap reproducible, lightweight, dan mudah dijalankan oleh portfolio reviewer. Setiap keputusan infrastruktur harus bisa dipertanggungjawabkan saat interview.

## When to Use
- Menulis atau memodifikasi `docker-compose*.yml`
- Mengelola Python packages (`requirements.txt`) atau Docker image tags
- Menambah target di `Makefile`
- Setup testing (pytest, dbt test)
- Mengelola secrets (`.env`)

## Docker Compose — Progressive Infrastructure

JANGAN membuat satu file `docker-compose.yml` besar. Pisahkan per fase:

| File | Services | Fase |
|---|---|---|
| `docker-compose.yml` | `airflow-webserver`, `airflow-scheduler`, `postgres`, `metabase` | 1 (base) |
| `docker-compose.fase2.yml` | `minio` | 2 |
| `docker-compose.fase3.yml` | `n8n` | 3 |

Cara menjalankan:
```bash
# Fase 1
docker compose -f docker-compose.yml up -d

# Fase 1 + 2
docker compose -f docker-compose.yml -f docker-compose.fase2.yml up -d

# Full stack (Fase 1 + 2 + 3)
docker compose -f docker-compose.yml -f docker-compose.fase2.yml -f docker-compose.fase3.yml up -d
```

DuckDB TIDAK perlu container — embedded/in-process, dipanggil sebagai library dari Airflow task atau dbt.

## Version Pinning (WAJIB)

- Python packages di `requirements.txt`: gunakan `==X.Y.Z`, JANGAN `>=` atau tanpa versi
- Docker images: pin ke tag spesifik, JANGAN `:latest`

```
# ✅ BENAR
apache-airflow==2.10.5
dbt-core==1.9.1
dlt[filesystem,parquet]==1.6.1
soda-core-duckdb==3.3.5

# 🚩 SALAH
apache-airflow
dbt-core>=1.9
```

```yaml
# ✅ BENAR
image: apache/airflow:2.10.5-python3.11

# 🚩 SALAH
image: apache/airflow:latest
```

## Makefile Targets (8 WAJIB)

```makefile
setup:      # Install dependencies, init Airflow DB
up:         # docker compose up -d (sesuai fase)
down:       # docker compose down
test:       # Jalankan SEMUA test (pytest + dbt test)
test-dbt:   # Jalankan dbt test + dbt source freshness
test-dag:   # Jalankan pytest khusus DAG integrity
seed:       # Load sample data (DEMO_MODE)
lint:       # Jalankan linter (ruff/flake8 + sqlfluff)
```

## Secrets Management

- `.env` berisi real secrets → HARUS masuk `.gitignore`
- `.env.example` di-commit ke repo dengan dummy values

`.env.example` harus mengandung SEMUA variabel dari semua fase:
```env
# === Fase 1 ===
GITHUB_API_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
POSTGRES_USER=elt_user
POSTGRES_PASSWORD=elt_password
POSTGRES_DB=elt_lakehouse
DEMO_MODE=false

# === Fase 2 (tambahkan saat mulai Fase 2) ===
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# === Fase 3 (tambahkan saat mulai Fase 3) ===
N8N_WEBHOOK_URL=http://n8n:5678/webhook/pipeline-alert
TELEGRAM_BOT_TOKEN=123456:ABC-DEF
TELEGRAM_CHAT_ID=-1001234567890
```

## Testing Matrix (10 Jenis Test)

| # | Test | Tool | Lokasi | Fase | Jalankan via |
|---|---|---|---|---|---|
| 1 | DAG integrity (import test, no cyclic deps) | pytest | `tests/test_dag_integrity.py` | 1 | `make test-dag` |
| 2 | Pagination/backoff unit test | pytest | `tests/test_ingestion.py` | 1 | `make test` |
| 3 | Idempotency test (no duplicate on re-run) | pytest | `tests/test_idempotency.py` | 1 | `make test` |
| 4 | dbt generic test (`not_null`, `unique`, `relationships`) | dbt test | `dbt/models/*/schema.yml` | 1 | `make test-dbt` |
| 5 | dbt unit test (logic SQL, mock input/output) | dbt test | `dbt/tests/` atau inline di model | 1 | `make test-dbt` |
| 6 | dlt schema validation | dlt | `.dlt/` config | 2 | `make test` |
| 7 | Data contract test (schema API tidak berubah antar run) | pytest | `tests/test_ingestion.py` | 2 | `make test` |
| 8 | Integration test (e2e: dlt → DuckLake → dbt → PG mart) | pytest | `tests/test_integration.py` | 2 | `make test` |
| 9 | Soda Core checks (volume, freshness, schema, integrity) | Soda | `data_quality/checks/*.yml` | 3 | Airflow task |
| 10 | dbt source freshness | dbt | `dbt/models/staging/schema.yml` | 2 | `make test-dbt` |

Semua test HARUS bisa dijalankan tanpa koneksi ke GitHub API (gunakan seed data / mock).

## `.gitignore` Wajib

```gitignore
# Secrets
.env
dlt/.dlt/secrets.toml

# DuckDB
*.duckdb
*.duckdb.wal

# Python
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/

# dbt
dbt/target/
dbt/dbt_packages/
dbt/logs/

# IDE
.vscode/
.idea/
```
