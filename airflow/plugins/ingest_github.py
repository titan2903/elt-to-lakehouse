import json
import logging
import os
import time

import dlt
import requests

logger = logging.getLogger(__name__)


def fetch_github_data(endpoint, repo="dbt-labs/dbt-core"):
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    if demo_mode:
        logger.info(f"DEMO_MODE is ON. Loading seed data for {endpoint}.")
        seed_file = f"/opt/airflow/data/seed/{endpoint}.json"
        try:
            with open(seed_file, "r") as f:
                data = json.load(f)
                yield data
        except FileNotFoundError:
            logger.warning(f"Seed file not found: {seed_file}")
            yield []
        return

    token = os.getenv("GITHUB_API_TOKEN")
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ELT-Lakehouse-Pipeline",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    base_url = f"https://api.github.com/repos/{repo}/{endpoint}"
    params = {"per_page": 100, "state": "all"}
    url = base_url

    while url:
        logger.info(f"Fetching {url}")

        # Exponential backoff loop
        max_retries = 3
        for attempt in range(max_retries):
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                break
            elif response.status_code in (403, 429):
                reset_time = int(
                    response.headers.get("X-RateLimit-Reset", time.time() + 60)
                )
                sleep_time = max(reset_time - int(time.time()), 5)
                logger.warning(
                    f"Rate limit hit. Sleeping for {sleep_time} seconds. Attempt {attempt + 1}/{max_retries}"
                )
                time.sleep(sleep_time)
            else:
                response.raise_for_status()

        data = response.json()
        if not data:
            break

        yield data

        if "next" in response.links:
            url = response.links["next"]["url"]
            params = {}
        else:
            url = None


@dlt.resource(name="pull_requests", write_disposition="replace")
def get_pull_requests():
    yield from fetch_github_data("pulls")


@dlt.resource(name="issues", write_disposition="replace")
def get_issues():
    yield from fetch_github_data("issues")


def run_dlt_pipeline():
    # Setup MinIO credentials for dlt
    os.environ["DESTINATION__FILESYSTEM__BUCKET_URL"] = "s3://lakehouse/raw"
    os.environ["DESTINATION__FILESYSTEM__CREDENTIALS__ENDPOINT_URL"] = (
        "http://minio:9000"
    )
    os.environ["DESTINATION__FILESYSTEM__CREDENTIALS__AWS_ACCESS_KEY_ID"] = os.getenv(
        "MINIO_ACCESS_KEY", "minioadmin"
    )
    os.environ["DESTINATION__FILESYSTEM__CREDENTIALS__AWS_SECRET_ACCESS_KEY"] = (
        os.getenv("MINIO_SECRET_KEY", "minioadmin")
    )

    pipeline = dlt.pipeline(
        pipeline_name="github_pipeline",
        destination="filesystem",
        dataset_name="github_data",
    )

    # Record schema version before load to detect schema drift
    try:
        initial_version = pipeline.default_schema.version
    except Exception:
        initial_version = 0

    load_info = pipeline.run(
        [get_pull_requests(), get_issues()], loader_file_format="parquet"
    )
    logger.info(load_info)

    # Detect Schema Drift
    try:
        final_version = pipeline.default_schema.version
    except Exception:
        final_version = 0

    if final_version > initial_version:
        drift_msg = f"Schema evolved from version {initial_version} to {final_version}. New columns/tables were added."
        logger.warning(f"SCHEMA DRIFT DETECTED: {drift_msg}")

        # Use GMT+7 (WIB)
        from datetime import datetime, timedelta, timezone

        wib = timezone(timedelta(hours=7))
        execution_time = datetime.now(wib).strftime("%Y-%m-%dT%H:%M:%S%z")

        webhook_url = os.getenv(
            "N8N_WEBHOOK_URL", "http://n8n:5678/webhook/pipeline-alert"
        )
        payload = {
            "alert_type": "schema_drift",
            "dag_id": "github_elt_pipeline",
            "task_id": "ingest_dlt_to_minio",
            "execution_date": execution_time,
            "error_message": drift_msg,
            "severity": "warning",
        }
        try:
            requests.post(webhook_url, json=payload, timeout=10)
            logger.info("Schema drift alert sent to n8n.")
        except Exception as e:
            logger.error(f"Failed to send schema drift alert: {e}")


def ingest_pull_requests(**kwargs):
    # Dummy to not break DAG if we migrate step by step
    # We will just run the full pipeline here, and leave ingest_issues empty.
    run_dlt_pipeline()


def ingest_issues(**kwargs):
    pass
