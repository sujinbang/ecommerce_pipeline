.PHONY: help setup data load deps build test pipeline airflow dashboard clean

REPO_ROOT := $(shell pwd)
VENV      := $(REPO_ROOT)/venv
PY        := $(VENV)/bin/python
DBT       := $(VENV)/bin/dbt
DBT_DIR   := $(REPO_ROOT)/dbt

export DUCKDB_PATH  := $(REPO_ROOT)/ecommerce.duckdb
export DBT_EXECUTABLE := $(DBT)
export AIRFLOW_HOME := $(REPO_ROOT)/airflow

help:
	@echo "make setup      - 가상환경 생성 및 의존성 설치"
	@echo "make pipeline   - 데이터 생성 → 적재 → dbt build(변환+테스트) 전체 실행"
	@echo "make data       - 원본 목 데이터 생성"
	@echo "make load       - 원본 데이터를 DuckDB raw 테이블로 적재"
	@echo "make build      - dbt run + dbt test (증분 반영)"
	@echo "make test       - dbt test 만 실행"
	@echo "make airflow    - Airflow standalone 실행 (http://localhost:8080)"
	@echo "make dashboard  - Streamlit 대시보드 실행"
	@echo "make clean      - DuckDB 파일 및 dbt 산출물 삭제"

setup:
	python3 -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt
	cd $(DBT_DIR) && $(DBT) deps

data:
	$(PY) generate_mock_data.py

load:
	$(PY) load_data_to_duckdb.py

deps:
	cd $(DBT_DIR) && $(DBT) deps

build:
	cd $(DBT_DIR) && $(DBT) build

test:
	cd $(DBT_DIR) && $(DBT) test

# 전체 재생성이 필요할 때: make build-full
build-full:
	cd $(DBT_DIR) && $(DBT) build --full-refresh

pipeline: data load deps build

airflow:
	$(VENV)/bin/airflow standalone

dashboard:
	$(PY) -m streamlit run dashboard.py

clean:
	rm -f $(DUCKDB_PATH)
	rm -rf $(DBT_DIR)/target $(DBT_DIR)/dbt_packages $(DBT_DIR)/logs
