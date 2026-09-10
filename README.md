# 🛒 이커머스 데이터 파이프라인 프로젝트 (Local Environment)

이 프로젝트는 클라우드(BigQuery 등) 비용 없이, **100% 로컬 컴퓨터 안에서 최신 데이터 엔지니어링 파이프라인(Modern Data Stack)을 경험**해보기 위해 만들어진 실습 프로젝트입니다.

---

## 🏗️ 전체 아키텍처 (어떤 흐름으로 데이터가 흐르는가?)

1. **원천 데이터 (Raw Data)**: 지저분한 가짜 쇼핑몰 데이터를 파이썬으로 생성
2. **데이터 웨어하우스 (DuckDB)**: 엄청 빠르고 가벼운 로컬 분석용 DB (`ecommerce.duckdb`)
3. **데이터 변환 (dbt)**: 지저분한 데이터를 정제(Staging)하고 비즈니스 지표(Marts)로 변환
4. **오케스트레이션 (Airflow + Cosmos)**: 매일 자정마다 dbt 작업을 자동으로 순서에 맞게 실행하고 모니터링
5. **데이터 시각화 (Streamlit)**: 완성된 마트 테이블을 연동하여 웹 대시보드로 시각화

---

## 🧩 파이프라인 ELT 매핑 (Extract, Load, Transform)

최신 데이터 인프라의 표준인 **ELT 구조**에 맞춰 이 프로젝트를 요약하면 다음과 같습니다.

* **E (Extract / 데이터 추출)** 👉 `generate_mock_data.py`
  * 외부 API나 DB에서 원본 데이터를 긁어오는 단계 (본 프로젝트에서는 파이썬 가짜 데이터 생성으로 대체)
* **L (Load / 데이터 적재)** 👉 `load_data_to_duckdb.py`
  * 긁어온 원본 데이터를 가공 없이 날것(Raw) 그대로 분석용 데이터베이스(`DuckDB`)에 쏟아붓는 단계
* **T (Transform / 데이터 변환)** 👉 `dbt` + `Airflow`
  * DB 안에서 SQL을 돌려 에러 데이터를 청소하고(Staging), 비즈니스 통계 테이블로 예쁘게 요약(Mart)하는 핵심 단계
* **+ (Consume / 데이터 소비)** 👉 `dashboard.py` (Streamlit)
  * 가공이 끝난 마트(Mart) 데이터를 시각화 대시보드나 엑셀로 뽑아 비즈니스 의사결정에 활용하는 단계

---

## 💡 왜 이런 복잡한 파이프라인(Airflow+dbt)을 구축해야 할까?

단순히 대시보드(Streamlit)에서 원본 데이터를 직접 쿼리하지 않고 데이터 파이프라인을 두는 3가지 핵심 이유:
1. **성능 및 서버 비용 최적화**: 대용량 데이터를 대시보드에서 매번 쿼리하면 로딩이 오래 걸리고 클라우드 비용이 폭발함. 새벽에 미리 계산해둔 요약본(Mart) 데이터를 대시보드가 가볍게 읽어오게 만듦.
2. **팀별 데이터 공유 (Single Source of Truth)**: 정제된 마트 데이터를 엑셀, 대시보드 등 다양한 방식으로 각 팀에서 일관성 있게 재사용 가능함.
3. **데이터 신뢰성 및 사고 방지**: 망가진 원본 데이터가 대시보드에 그대로 노출되는 것을 막고, 파이프라인 단계에서 오류를 감지해 슬랙 알림 등으로 미리 방어할 수 있음.

---

## 📂 폴더 및 주요 파일 구조

```text
ecommerce_pipeline/
│
├── README.md                    # 파이프라인 요약 및 실행 가이드 (현재 파일)
├── venv/                        # 파이썬 가상환경
│
├── raw_data/                    # [Extract] 가짜 원본 데이터 (csv, jsonl)
├── generate_mock_data.py        # 원본 데이터를 만들어내는 스크립트
├── load_data_to_duckdb.py       # [Load] 원본 데이터를 DuckDB에 적재하는 스크립트
├── ecommerce.duckdb             # 로컬 데이터 웨어하우스 (DuckDB 파일)
├── check_duckdb.py              # DuckDB 안의 데이터를 터미널에서 빠르게 조회하는 파이썬 스크립트
│
├── dbt/                         # [Transform] 데이터 정제 및 가공 (dbt 프로젝트)
│   ├── dbt_project.yml          
│   ├── profiles.yml             # DuckDB 절대경로 연결 설정
│   └── models/
│       ├── staging/             # (1차 정제) stg_orders.sql, stg_user_logs.sql
│       └── marts/               # (2차 집계) mart_daily_revenue.sql
│
├── airflow/                     # [Orchestration] 스케줄링 (Airflow)
│   └── dags/
│       └── dbt_pipeline.py      # Cosmos를 이용해 dbt를 Airflow 그래프로 만들어주는 DAG 파일
│
└── dashboard.py                 # [Consume] 완성된 데이터를 시각화하는 Streamlit 대시보드 앱
```

---

## 🚀 실행 가이드 (처음부터 끝까지 돌려보기)

터미널을 열고 아래 순서대로 실행하시면 됩니다.

**1. 가상환경 켜기 (모든 작업의 필수)**
```bash
cd ~/ecommerce_pipeline
source venv/bin/activate
```

**2. 초기 데이터 생성 및 DuckDB 적재**
```bash
python3 generate_mock_data.py
python3 load_data_to_duckdb.py
```

**3. Airflow 파이프라인 자동화 켜기**
```bash
export AIRFLOW_HOME=$(pwd)/airflow
airflow standalone
```
* 터미널에 뜬 `admin` 비밀번호를 복사 후 브라우저에서 `http://localhost:8080` 접속
* `ecommerce_dbt_pipeline` 실행(Trigger) -> dbt가 자동으로 데이터를 정제하고 마트 테이블을 생성함.
* ⚠️ **주의:** Airflow 실행 시 DBeaver 같은 DB 툴이 `ecommerce.duckdb`를 물고 있다면 연결을 해제해야 에러가 안 납니다. (DuckDB Lock 방지)

**4. Streamlit 대시보드로 결과 시각화하기**
새 터미널을 열고 가상환경 활성화 후 아래 명령어 실행:
```bash
python3 -m streamlit run dashboard.py
```
* 브라우저에서 `http://localhost:8501` 에 접속하여 완성된 대시보드 감상!
