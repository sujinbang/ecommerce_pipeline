import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from cosmos import DbtDag, ExecutionConfig, ProfileConfig, ProjectConfig

# 경로는 DAG 파일 위치에서 역산한다. (레포를 옮겨도 그대로 동작)
# <REPO_ROOT>/airflow/dags/dbt_pipeline.py 기준
REPO_ROOT = Path(__file__).resolve().parents[2]
DBT_PROJECT_DIR = REPO_ROOT / "dbt"
DUCKDB_PATH = Path(os.environ.get("DUCKDB_PATH", REPO_ROOT / "ecommerce.duckdb"))
DBT_EXECUTABLE = Path(os.environ.get("DBT_EXECUTABLE", REPO_ROOT / "venv" / "bin" / "dbt"))

# profiles.yml이 env_var('DUCKDB_PATH')를 읽으므로 절대경로로 고정해 둔다.
os.environ["DUCKDB_PATH"] = str(DUCKDB_PATH)

profile_config = ProfileConfig(
    profile_name="ecommerce_dbt",
    target_name="dev",
    profiles_yml_filepath=DBT_PROJECT_DIR / "profiles.yml",
)


def alert_on_failure(context):
    """태스크 최종 실패 시 호출. 운영 환경에서는 이 지점에 Slack/PagerDuty를 연결한다."""
    ti = context["task_instance"]
    logging.error(
        "[PIPELINE FAILED] dag=%s task=%s run=%s try=%s/%s",
        ti.dag_id,
        ti.task_id,
        context["run_id"],
        ti.try_number,
        ti.max_tries,
    )


default_args = {
    # 일시적 실패(락 충돌, 파일 점유)는 재시도로 흡수한다.
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "retry_exponential_backoff": True,
    "on_failure_callback": alert_on_failure,
}

ecommerce_dbt_dag = DbtDag(
    project_config=ProjectConfig(DBT_PROJECT_DIR),
    profile_config=profile_config,
    execution_config=ExecutionConfig(dbt_executable_path=DBT_EXECUTABLE),
    operator_args={
        "env": {"DUCKDB_PATH": str(DUCKDB_PATH)},
        # 모델 실행 직후 해당 모델의 dbt test를 함께 수행한다.
        "install_deps": True,
    },
    default_args=default_args,
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
