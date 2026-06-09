"""
forecasting_dag.py
Runs Prophet demand forecasting every day at 10am.
Depends on transformation_dag completing successfully.
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
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="grubgrid_forecasting",
    description="Daily Prophet demand forecasting pipeline",
    default_args=default_args,
    schedule_interval="0 10 * * *",    # every day at 10am
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["grubgrid", "forecasting", "prophet"],
) as dag:

    # wait for transformation DAG to finish before forecasting
    wait_for_transformation = ExternalTaskSensor(
        task_id="wait_for_transformation",
        external_dag_id="grubgrid_transformation",
        external_task_id=None,          # wait for whole DAG
        timeout=3600,
        poke_interval=60,
        mode="poke",
    )

    run_forecasting = BashOperator(
        task_id="run_demand_forecast",
        bash_command="cd /opt/airflow && python forecasting/demand_forecast.py",
    )

    wait_for_transformation >> run_forecasting