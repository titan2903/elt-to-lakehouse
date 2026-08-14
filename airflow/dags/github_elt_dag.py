from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from ingest_github import run_dlt_pipeline

default_args = {
    'owner': 'data_engineering_team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=3),
}

with DAG(
    dag_id='github_elt_pipeline',
    default_args=default_args,
    description='Lakehouse pipeline from GitHub API to DuckDB to Postgres (Phase 2)',
    schedule='@daily',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['elt', 'lakehouse', 'phase2'],
) as dag:

    task_ingest_data = PythonOperator(
        task_id='ingest_dlt_to_minio',
        python_callable=run_dlt_pipeline,
    )

    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command='cd /opt/airflow/dbt && dbt run --profiles-dir . --log-path /tmp/dbt_logs',
    )

    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command='cd /opt/airflow/dbt && dbt test --profiles-dir . --log-path /tmp/dbt_logs',
    )

    task_ingest_data >> dbt_run >> dbt_test
