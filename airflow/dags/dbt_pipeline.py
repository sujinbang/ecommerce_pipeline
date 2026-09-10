from datetime import datetime
from pathlib import Path
from cosmos import DbtDag, ProjectConfig, ProfileConfig, ExecutionConfig

# dbt 프로젝트 및 실행 파일 경로 설정
DBT_PROJECT_DIR = Path("/Users/sjbang/ecommerce_pipeline/dbt")
DBT_EXECUTABLE = Path("/Users/sjbang/ecommerce_pipeline/venv/bin/dbt")

# 이미 설정해둔 dbt profiles.yml 파일을 그대로 사용하도록 설정
profile_config = ProfileConfig(
    profile_name="ecommerce_dbt",
    target_name="dev",
    profiles_yml_filepath=DBT_PROJECT_DIR / "profiles.yml"
)

# DbtDag 클래스를 사용하면 dbt 프로젝트를 자동으로 파싱해서 Airflow DAG로 만들어줍니다.
ecommerce_dbt_dag = DbtDag(
    project_config=ProjectConfig(DBT_PROJECT_DIR),
    profile_config=profile_config,
    execution_config=ExecutionConfig(dbt_executable_path=DBT_EXECUTABLE),
    
    # Airflow 스케줄링 설정
    schedule="@daily",
    start_date=datetime(2023, 10, 1),
    catchup=False,
    dag_id="ecommerce_dbt_pipeline",
    tags=["ecommerce", "dbt"],

    # DuckDB는 파일 하나에 쓰기 프로세스가 하나만 붙을 수 있어서,
    # 태스크/DAG run이 겹치면 lock 충돌로 실패한다.
    max_active_tasks=1,
    max_active_runs=1,
)
# DAG
