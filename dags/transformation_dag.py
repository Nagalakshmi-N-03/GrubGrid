"""
transformation_dag.py
Runs dbt transformations every day at 9am.
Depends on scraping_dag completing successfully.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.sensors.external_task import ExternalTaskSensor

default_args = {
    "owner": "grubgrid",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="grubgrid_transformation",
    description="Daily dbt transformation pipeline",
    default_args=default_args,
    schedule_interval="0 9 * * *",     # every day at 9am
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["grubgrid", "dbt", "transformation"],
) as dag:

    # wait for scraping DAG to finish before transforming
    wait_for_scraping = ExternalTaskSensor(
        task_id="wait_for_scraping",
        external_dag_id="grubgrid_scraping",
        external_task_id=None,          # wait for whole DAG
        timeout=3600,
        poke_interval=60,
        mode="poke",
    )

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command="cd /opt/airflow/dbt_project && dbt deps --profiles-dir .",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt_project && dbt run --profiles-dir .",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt_project && dbt test --profiles-dir .",
    )

    wait_for_scraping >> dbt_deps >> dbt_run >> dbt_test