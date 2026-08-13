from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from ingest_github import ingest_pull_requests, ingest_issues

default_args = {
    'owner': 'data_engineering_team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=3),
    # Phase 3 will add on_failure_callback here
}

with DAG(
    dag_id='github_elt_pipeline',
    default_args=default_args,
    description='Batch ELT pipeline from GitHub API to Lakehouse (Phase 1)',
    schedule='@daily',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['elt', 'github', 'phase1'],
) as dag:

    task_ingest_prs = PythonOperator(
        task_id='ingest_pull_requests',
        python_callable=ingest_pull_requests,
    )

    task_ingest_issues = PythonOperator(
        task_id='ingest_issues',
        python_callable=ingest_issues,
    )

    # dbt run & dbt test
    # Note: we use BashOperator to run dbt commands inside the airflow container.
    # The 'dbt' directory is mounted to /opt/airflow/dbt.
    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command='cd /opt/airflow/dbt && dbt run --profiles-dir .',
    )

    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command='cd /opt/airflow/dbt && dbt test --profiles-dir .',
    )

    [task_ingest_prs, task_ingest_issues] >> dbt_run >> dbt_test
