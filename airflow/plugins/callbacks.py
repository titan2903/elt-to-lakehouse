import os
import requests
import logging

def send_alert_to_n8n(context, alert_type="pipeline_failure", custom_message=None):
    """Kirim alert ke n8n webhook. Satu fungsi untuk semua DAG."""
    # N8N webhook URL defaults to internal docker network URL if not provided
    webhook_url = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook/pipeline-alert")
    
    exception = context.get("exception")
    error_message = custom_message if custom_message else str(exception) if exception else "Unknown error"
    
    payload = {
        "alert_type": alert_type,
        "dag_id": context["task_instance"].dag_id,
        "task_id": context["task_instance"].task_id,
        "execution_date": str(context["execution_date"]),
        "error_message": error_message,
        "severity": "critical" if alert_type == "pipeline_failure" else "warning"
    }
    
    try:
        logging.info(f"Sending {alert_type} alert to n8n webhook: {webhook_url}")
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logging.info("Successfully sent alert to n8n.")
    except Exception as e:
        logging.error(f"Failed to send alert to n8n: {e}")

def on_failure_callback(context):
    """Default callback for DAG or task failure."""
    send_alert_to_n8n(context, alert_type="pipeline_failure")

def on_data_quality_failure_callback(context):
    """Callback specific for data quality failures (Soda)."""
    send_alert_to_n8n(context, alert_type="data_quality_failure")

def on_schema_drift_callback(context, drift_info: str):
    """Callback for schema drift detection from dlt."""
    send_alert_to_n8n(context, alert_type="schema_drift", custom_message=drift_info)
