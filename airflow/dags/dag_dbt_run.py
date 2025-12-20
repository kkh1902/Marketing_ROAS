from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# ============================================================================
# Default Arguments
# ============================================================================
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 12, 20),
    'email': ['data-team@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# ============================================================================
# DAG Definition
# ============================================================================
dag = DAG(
    dag_id='dag_dbt_run',
    default_args=default_args,
    description='dbt models execution and data validation DAG',
    schedule_interval='0 0 * * *',  # Daily at 00:00 UTC (09:00 KST)
    catchup=False,
    tags=['dbt', 'batch', 'transform'],
    max_active_runs=1,
)

# ============================================================================
# Tasks
# ============================================================================

# Task 1: dbt run - Execute dbt models
# stg_ad_events -> int_hourly_agg -> dim_campaigns -> fct_daily_metrics
dbt_run = BashOperator(
    task_id='dbt_run',
    bash_command="""
        cd /dbt && \
        dbt run \
            --profiles-dir . \
            --models staging intermediate marts \
            --threads 4 \
            --target dev
    """,
    dag=dag,
    trigger_rule='all_success',
)

# Task 2: dbt test - Data validation
# YAML-based tests (not_null, unique, relationships)
# SQL custom tests (CTR range, negative values, etc)
dbt_test = BashOperator(
    task_id='dbt_test',
    bash_command="""
        cd /dbt && \
        dbt test \
            --profiles-dir . \
            --threads 4 \
            --fail-fast
    """,
    dag=dag,
    trigger_rule='all_success',
)

# Task 3: dbt docs - Auto-generate documentation
dbt_docs = BashOperator(
    task_id='dbt_docs',
    bash_command="""
        cd /dbt && \
        dbt docs generate --profiles-dir .
    """,
    dag=dag,
    trigger_rule='all_success',
)

# ============================================================================
# Task Dependencies
# ============================================================================
dbt_run >> dbt_test >> dbt_docs

# ============================================================================
# DAG Description:
#
# 1. dbt_run: Execute 4 dbt models
#    - stg_ad_events (source data cleaning and validation)
#    - int_hourly_agg (hourly CTR aggregation)
#    - dim_campaigns (campaign master table with surrogate key)
#    - fct_daily_metrics (daily KPI metrics)
#
# 2. dbt_test: Data quality validation (17 custom tests)
#    - CTR range validation (0-100%)
#    - Clicks <= Impressions constraint
#    - Negative value removal
#    - Uniqueness and deduplication checks
#
# 3. dbt_docs: Generate HTML documentation
#    - Auto-document tables, columns, and relationships
#
# Schedule: Daily at 00:00 UTC (09:00 KST)
# Retries: 3 times with 5 minute intervals
# ============================================================================
