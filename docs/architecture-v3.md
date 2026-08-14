# Arsitektur Fase 3: Data Quality, Monitoring & Alerting

Fase 3 berfokus pada observabilitas pipeline. Di fase ini, kita mengintegrasikan *data quality checks* terotomatisasi di dalam DAG Airflow dan mengimplementasikan mekanisme *alerting* ke Telegram untuk memastikan kita segera tahu bila terjadi anomali pada data atau kegagalan pipeline.

## Diagram Arsitektur Alerting & Data Quality

```mermaid
graph TD
    subgraph Airflow DAG [github_elt_pipeline]
        A[ingest_dlt_to_minio] --> B(soda_check_raw)
        B --> C[dbt_run]
        C --> D[dbt_test]
        D --> E(soda_check_mart)
    end

    subgraph Data Quality (Soda)
        B -.->|Checks| DuckDB_Parquet[(MinIO / Raw Parquet)]
        E -.->|Checks| Postgres_Mart[(PostgreSQL / Mart Schema)]
    end

    subgraph Notification Router
        n8n[n8n Webhook Node]
        Switch{Routing Switch}
        n8n --> Switch
    end

    subgraph Telegram
        T_Fail[Telegram: Pipeline Failure]
        T_DQ[Telegram: Data Quality Alert]
        T_Drift[Telegram: Schema Drift]
    end

    %% Failure Callbacks
    A -.->|on_failure_callback| n8n
    B -.->|on_data_quality_failure| n8n
    C -.->|on_failure_callback| n8n
    E -.->|on_data_quality_failure| n8n

    %% n8n routing
    Switch -.->|payload.alert_type == 'pipeline_failure'| T_Fail
    Switch -.->|payload.alert_type == 'data_quality_failure'| T_DQ
    Switch -.->|payload.alert_type == 'schema_drift'| T_Drift

    classDef dagTask fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef dqTask fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef n8nNode fill:#fce4ec,stroke:#c2185b,stroke-width:2px;
    classDef telegram fill:#e3f2fd,stroke:#1976d2,stroke-width:2px;

    class A,C,D dagTask;
    class B,E dqTask;
    class n8n,Switch n8nNode;
    class T_Fail,T_DQ,T_Drift telegram;
```

## Komponen Utama Fase 3

### 1. Soda Core (Data Quality)
Soda Core dipilih karena pendekatannya yang deklaratif (YAML) dan konfigurasinya yang ringan. Kita membagi pengecekan dalam dua tahapan:
- **`raw.yml`**: Berjalan setelah data mendarat di MinIO (di-*query* lewat DuckDB). Mengecek agar baris data tidak kosong (freshness/volume) sebelum dbt dijalankan. Jika gagal, Airflow menghentikan pipeline dan mencegah *bad data* menjalar ke layer dbt.
- **`mart.yml`**: Berjalan setelah dbt transformasi selesai (di-*query* lewat PostgreSQL). Mengecek integrasi referensial, range waktu, dan kelengkapan kolom yang dibutuhkan Metabase.

### 2. n8n (Notification Router)
Sebagai ganti menulis kode koneksi Telegram langsung di Airflow `callbacks.py`, kita mengalihkannya ke **n8n**. Ini menerapkan *Separation of Concerns*:
- **Airflow**: Hanya bertugas menyadari jika ada gagal lalu mengirimkan payload HTTP POST sederhana ke webhook.
- **n8n**: Bertugas menerima webhook, mem-*parsing* JSON payload (mengecek atribut `alert_type`), dan melakukan *formatting* Markdown, lalu mengirimkannya ke Telegram menggunakan kredensial Bot API. Jika di masa depan kita butuh alert ke Slack atau Email, kita tidak perlu memodifikasi kode Airflow sama sekali; cukup edit alur di n8n.

### 3. Telegram Bot API
Penerima pesan akhir (sink) dengan format *Rich Text (MarkdownV2)* agar error terlihat rapi dengan indikator emoji tingkat keparahan (🔴 Pipeline Error vs 🟡 Data Quality Warning).

## Mengapa Menggunakan "Sustainable Use License"
Karena proyek ini mengutamakan teknologi sumber terbuka untuk operasional lokal dan *portofolio*, **n8n** cocok karena gratis untuk pemakaian pribadi dan *self-hosted* (lisensi *Sustainable Use* dan bukan OSS penuh seperti Apache 2.0). Ini menunjukkan pragmatisme: kita tidak selalu butuh kakas (tools) komersial berat (seperti PagerDuty) untuk arsitektur mandiri atau *startup* tahap awal.
