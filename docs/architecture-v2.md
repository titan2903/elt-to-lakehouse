# Architecture Fase 2: Lakehouse Migration

```mermaid
flowchart TD
    %% Define components
    subgraph External
        GitHubAPI["GitHub API"]
    end

    subgraph "Airflow (Orchestration)"
        DLTTask["DLT Pipeline Task"]
        DBTRun["dbt run"]
        DBTTest["dbt test"]
    end

    subgraph "Data Lakehouse (MinIO)"
        RawZone["s3://lakehouse/raw/github_data/\n(Parquet)"]
    end

    subgraph "Compute Engine (DuckDB)"
        DBTDuck["dbt-duckdb"]
    end

    subgraph "PostgreSQL (Serving Layer)"
        MartSchema[("pg.main_mart\n(Star Schema)")]
    end

    subgraph "BI (Metabase)"
        Dashboard["Dashboards"]
    end

    %% Data Flow
    GitHubAPI -- "REST API" --> DLTTask
    DLTTask -- "dlt ingest (JSON -> Parquet)" --> RawZone
    
    DBTRun -- "Triggers" --> DBTDuck
    RawZone -- "httpfs extension" --> DBTDuck
    DBTDuck -- "Transforms & Tests" --> DBTDuck
    DBTDuck -- "Postgres ATTACH" --> MartSchema
    
    MartSchema -- "SQL Queries" --> Dashboard
```

## Deskripsi Arsitektur
Fase 2 memigrasikan penyimpanan raw data dari database operasional (PostgreSQL) ke Object Storage (MinIO) dalam format Parquet, membentuk arsitektur Lakehouse yang lebih scalable.
Compute layer dipisahkan dari storage layer. `dlt` (data load tool) digunakan untuk mengekstrak data dari GitHub API dan meloadnya langsung ke MinIO.
`dbt-duckdb` kemudian digunakan sebagai in-memory analytical database yang membaca Parquet file dari MinIO menggunakan `httpfs` extension, melakukan transformasi dbt in-memory, dan langsung menulis hasil akhir (Mart Tables) kembali ke PostgreSQL (sebagai serving layer) menggunakan fitur `ATTACH` di DuckDB. 
Ini mengoptimalkan proses transformasi dan memastikan serving layer di PostgreSQL hanya berisi tabel-tabel agregasi siap pakai tanpa dibebani proses komputasi mentah.
