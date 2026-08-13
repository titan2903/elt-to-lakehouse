---
name: elt-automation
description: Use when writing or debugging Airflow DAGs, setting up orchestration tasks, configuring callbacks, or building n8n workflows for notifications.
---

# ELT Automation & Orchestration

## Overview
Skill ini mengatur bagaimana pipeline diorkestrasi (Airflow) dan bagaimana notifikasi dialirkan (n8n → Telegram). Prinsip utama: **separation of concerns** — Airflow mendeteksi masalah, n8n mengirim notifikasi.

## When to Use
- Menulis atau memodifikasi Airflow DAGs (`airflow/dags/`)
- Menulis custom Python callables untuk Airflow tasks
- Mengkonfigurasi `on_failure_callback`
- Mendesain atau mengekspor n8n workflows
- Setup Telegram Bot untuk alerting

## Airflow Rules

- Executor: **LocalExecutor** saja. Jangan CeleryExecutor atau KubernetesExecutor.
- Metadata DB: PostgreSQL schema `airflow_meta` (instance yang sudah ada).
- Semua DAG HARUS idempotent — aman dijalankan ulang untuk `execution_date` yang sama tanpa duplikasi data.
- Retry policy: wajib ada `retries` dan `retry_delay` di default_args.
- Modularity: logic berat (pagination, API calls, transformasi) di Python functions terpisah, bukan inline di DAG file.

## DAG Task Ordering (Full Pipeline — Fase 3)

```
ingest_data
    ↓
soda_check_raw          ← Soda Core cek raw layer
    ↓
dbt_run                 ← dbt staging → mart
    ↓
soda_check_mart         ← Soda Core cek mart layer
    ↓
[BranchPythonOperator]  ← (opsional: circuit breaker)
   ├── alert_and_stop   ← jika Soda gagal critical
   └── pipeline_done    ← jika semua lolos
```

Pada Fase 1 dan 2, pipeline lebih sederhana (tanpa Soda tasks).

## Alerting: Airflow → n8n → Telegram (Fase 3)

### Prinsip
- Airflow HANYA mengirim HTTP POST ke webhook n8n. JANGAN import library Telegram di Airflow.
- n8n menerima webhook, memformat pesan Markdown, routing ke Telegram.
- Satu perubahan format notifikasi = edit di n8n saja, tanpa redeploy Airflow.

### Callback Code (`airflow/plugins/callbacks.py`)

```python
import os
import requests

def send_alert_to_n8n(context, alert_type="pipeline_failure"):
    """Kirim alert ke n8n webhook. Satu fungsi untuk semua DAG."""
    webhook_url = os.getenv("N8N_WEBHOOK_URL")
    if not webhook_url:
        print("WARNING: N8N_WEBHOOK_URL not set, skipping alert")
        return

    payload = {
        "alert_type": alert_type,
        "dag_id": context["task_instance"].dag_id,
        "task_id": context["task_instance"].task_id,
        "execution_date": str(context["execution_date"]),
        "error_message": str(context.get("exception", "Unknown error")),
        "severity": "critical" if alert_type == "pipeline_failure" else "warning"
    }

    try:
        requests.post(webhook_url, json=payload, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Failed to send alert to n8n: {e}")
```

### Penggunaan di DAG
```python
from plugins.callbacks import send_alert_to_n8n

default_args = {
    "on_failure_callback": send_alert_to_n8n,
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
}
```

Untuk alert Soda yang bukan pipeline failure:
```python
send_alert_to_n8n(context, alert_type="data_quality_failure")
send_alert_to_n8n(context, alert_type="schema_drift")
```

### JSON Payload yang Diterima n8n

```json
{
  "alert_type": "pipeline_failure | data_quality_failure | schema_drift",
  "dag_id": "github_elt_dag",
  "task_id": "soda_check_mart",
  "execution_date": "2026-08-13T10:00:00",
  "error_message": "Soda check failed: row_count dropped 60%",
  "severity": "critical | warning"
}
```

### n8n Workflow (`n8n/workflows/pipeline-alert-flow.json`)

Flow: `Webhook (POST)` → `IF (route by alert_type)` → `Telegram (send Markdown)`

Severity-to-emoji mapping:
- `pipeline_failure` → 🔴
- `data_quality_failure` → 🟡
- `schema_drift` → 🟠

Contoh output Telegram:
```
🔴 *Pipeline Failure*
DAG: `github_elt_dag`
Task: `ingest_pull_requests`
Time: 2026-08-13 10:00 UTC
Error: GitHub API rate limit exceeded
```

### Env Vars Wajib (Fase 3)
- `N8N_WEBHOOK_URL` — production webhook URL dari n8n
- `TELEGRAM_BOT_TOKEN` — dari BotFather
- `TELEGRAM_CHAT_ID` — chat/group ID tujuan notifikasi

## Schema Drift (Fase 2/3)

Jika dlt mendeteksi schema change dari GitHub API:
- Kolom BARU: dlt otomatis evolve schema, tapi tetap kirim alert `severity=warning`
- Kolom HILANG: kirim alert `severity=critical` — ini bisa break downstream models
