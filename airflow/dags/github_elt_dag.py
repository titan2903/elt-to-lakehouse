from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from callbacks import on_failure_callback, on_data_quality_failure_callback
from soda_runner import run_soda_duckdb, run_soda_postgres
from ingest_github import run_dlt_pipeline

default_args = {
    'owner': 'data_engineering_team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=3),
    'on_failure_callback': on_failure_callback,
}

with DAG(
    dag_id='github_elt_pipeline',
    default_args=default_args,
    description='Lakehouse pipeline from GitHub API to DuckDB to Postgres',
    schedule='@daily',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['elt', 'lakehouse', 'phase3', 'data-quality'],
) as dag:

    task_ingest_data = PythonOperator(
        task_id='ingest_dlt_to_minio',
        python_callable=run_dlt_pipeline,
    )

    soda_check_raw = PythonOperator(
        task_id='soda_check_raw',
        python_callable=run_soda_duckdb,
        op_kwargs={'check_file': '/opt/airflow/data_quality/checks/raw.yml'},
        on_failure_callback=on_data_quality_failure_callback,
    )

    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command='export PYTHONPATH=/opt/airflow/dbt:$PYTHONPATH && cd /opt/airflow/dbt && dbt run --profiles-dir . --log-path /tmp/dbt_logs --target-path /tmp/dbt_target',
    )

    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command='export PYTHONPATH=/opt/airflow/dbt:$PYTHONPATH && cd /opt/airflow/dbt && dbt test --profiles-dir . --log-path /tmp/dbt_logs --target-path /tmp/dbt_target',
    )

    soda_check_mart = PythonOperator(
        task_id='soda_check_mart',
        python_callable=run_soda_postgres,
        op_kwargs={'check_file': '/opt/airflow/data_quality/checks/mart.yml'},
        on_failure_callback=on_data_quality_failure_callback,
    )

    task_ingest_data >> soda_check_raw >> dbt_run >> dbt_test >> soda_check_mart

