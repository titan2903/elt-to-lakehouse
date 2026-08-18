---
name: elt-data-visualization
description: Use when configuring Metabase, connecting dashboards to the serving layer, or designing SQL queries for the visualization layer.
---

# ELT Data Visualization

## Overview
Skill ini mengatur consumption layer: bagaimana data dari mart layer divisualisasikan di Metabase. Metabase HARUS terkoneksi ke PostgreSQL, BUKAN ke DuckDB.

## When to Use
- Setup Metabase container di Docker Compose
- Konfigurasi database connection di Metabase
- Mendesain dashboard, query, atau visualisasi
- Membuat monitoring dashboard (Fase 3)

## Connection Rules

🚩 **RED FLAG**: Jangan pernah mencoba menghubungkan Metabase langsung ke DuckDB. Metabase tidak punya native DuckDB driver. Community driver berisiko version mismatch.

Koneksi yang benar:
```
Metabase → PostgreSQL (schema: mart)
```

Config di Metabase:
- Host: `postgres` (service name di docker-compose)
- Port: `5434`
- Database: sesuai `POSTGRES_DB` di `.env`
- Schema filter: `mart` saja — jangan expose schema lain (`raw`, `staging`, `airflow_meta`)

## Dashboard Types

### 1. Business Dashboard (Fase 1+)
Metrik dari dimensional model (star schema). Contoh visualisasi:

| Visualisasi | Fact/Dim yang dipakai | Tipe chart |
|---|---|---|
| PR Merge Time Trend | `fct_pull_requests` (avg `duration_hours` per minggu) | Line chart |
| Issue Resolution Rate | `fct_issues` (% closed per bulan) | Bar chart |
| Top Contributors | `fct_pull_requests` JOIN `dim_users` (count per user) | Horizontal bar |
| Activity by Repository | `fct_pull_requests` JOIN `dim_repos` (count per repo) | Pie/Donut |
| Label Distribution | `fct_issues` JOIN `dim_labels` (count per label) | Stacked bar |

Contoh query pattern:
```sql
-- PR Merge Time Trend (weekly)
SELECT
    date_trunc('week', merged_at) AS week,
    avg(duration_hours) AS avg_merge_hours,
    count(*) AS pr_count
FROM mart.fct_pull_requests
WHERE state = 'merged'
GROUP BY 1
ORDER BY 1;
```

### 2. Monitoring Dashboard (Fase 3, opsional)
Observability pipeline health. Sumber data: Airflow metadata + Soda results.

| Visualisasi | Sumber | Tipe chart |
|---|---|---|
| Pipeline Run History | `airflow_meta.dag_run` (status per hari) | Stacked bar (success/fail) |
| Data Quality Score | Soda check results (% checks passed per run) | Line chart |
| Row Count Trend | `mart.fct_pull_requests` (count per run) | Line chart |
| Freshness Monitor | `max(updated_at)` per tabel per run | Gauge/Number |

> **Catatan**: Untuk monitoring dashboard, Metabase perlu akses ke schema `airflow_meta` selain `mart`. Ini adalah satu-satunya pengecualian dari aturan "hanya `mart` schema".

## Design Guidelines
- Gunakan filter dashboard-level (date range, repository) agar interaktif
- Judul dan deskripsi chart dalam **Bahasa Indonesia** (konsisten dengan docs)
- Minimal 1 dashboard di Fase 1, tambahan 1 monitoring dashboard di Fase 3
