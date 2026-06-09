"""
scraping_dag.py
Runs the competitor price scraper every day at 7am.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import sys
import os

sys.path.insert(0, "/opt/airflow")

default_args = {
    "owner": "grubgrid",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="grubgrid_scraping",
    description="Daily competitor price scraping pipeline",
    default_args=default_args,
    schedule_interval="0 7 * * *",     # every day at 7am
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["grubgrid", "scraping"],
) as dag:

    run_scraper = BashOperator(
        task_id="run_price_scraper",
        bash_command="cd /opt/airflow && python scraping/price_scraper.py",
    )

    run_comparator = BashOperator(
        task_id="run_price_comparator",
        bash_command="cd /opt/airflow && python scraping/price_comparator.py",
    )

    # scraper must finish before comparator runs
    run_scraper >> run_comparator