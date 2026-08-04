from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.bash import BashOperator
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator


default_args = {
    "owner": "data_engineering_team",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=1),
}


with DAG(
    dag_id="olist_delivery_risk_pipeline",
    description="Olist ETL Pipeline",
    start_date=datetime(2026, 8, 1),
    schedule="0 2 * * *",
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["olist", "etl", "databricks"],
) as dag:

    batch_id = "{{ ts_nodash }}"


    start = EmptyOperator(
        task_id="start"
    )


    extract = BashOperator(
        task_id="extract_postgres_to_bronze",
        bash_command="""
        cd /opt/airflow &&
        python src/extract/extract.py "{{ ts_nodash }}"
        """,
    )

    run_databricks_job = DatabricksRunNowOperator(
        task_id="run_databricks_job",

        databricks_conn_id="databricks_default",

        job_id=468734488863687,

        notebook_params={
            "batch_id": batch_id
        },

        wait_for_termination=True,

        polling_period_seconds=30,
    )


    end = EmptyOperator(
        task_id="end"
    )

    start >> extract >> run_databricks_job >> end