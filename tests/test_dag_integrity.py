from airflow.models import DagBag

def test_dag_loaded():
    """Ensure that the DAG loads without any errors and there are no cyclic dependencies."""
    dagbag = DagBag(dag_folder="airflow/dags", include_examples=False)
    assert len(dagbag.import_errors) == 0, f"DAG import failures: {dagbag.import_errors}"
    assert "github_elt_pipeline" in dagbag.dags
    
def test_task_count():
    dagbag = DagBag(dag_folder="airflow/dags", include_examples=False)
    dag = dagbag.get_dag(dag_id="github_elt_pipeline")
    # ingest_pull_requests, ingest_issues, dbt_run, dbt_test
    assert len(dag.tasks) == 4
