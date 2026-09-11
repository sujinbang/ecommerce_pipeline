# 이커머스 ELT 데이터 파이프라인

## 📌 Summary & Key Features
클라우드 비용 없이 로컬에서 **Modern Data Stack**(DuckDB + dbt + Airflow)을 구성한 프로젝트입니다.
단순 실행에 그치지 않고, **집계 정합성 검증과 증분 처리**를 파이프라인에 편성했습니다.

```
generate_mock_data.py     load_data_to_duckdb.py          dbt                    dashboard.py
   원본 데이터 생성    →      DuckDB raw 적재      →   staging → intermediate → marts   →   Streamlit
     (Extract)                   (Load)                    (Transform)              (Consume)
                                                     ▲
                                          Airflow + Cosmos 가 스케줄링·재시도 관리
```

## 빠른 실행

```bash
make setup      # 가상환경 + 의존성 + dbt deps
make pipeline   # 데이터 생성 → 적재 → dbt build (변환 + 테스트)
make dashboard  # Streamlit 대시보드
make airflow    # Airflow standalone (http://localhost:8080)
```

`make help`로 전체 타겟을 확인할 수 있습니다.

## 모델 구조

| 레이어 | 모델 | 역할 |
|---|---|---|
| staging | `stg_orders` | 날짜 포맷 통일, 금액 결측/음수 정제 |
| staging | `stg_user_logs` | 누락된 `event_properties` 방어 후 device 추출 |
| intermediate | `int_daily_checkout_device` | checkout 로그를 **user-day 그레인으로 축약** |
| marts | `mart_daily_revenue` | 일자 + 기기별 매출/주문 집계 (**증분 모델**) |

## 🛠️ TroubleShooting & Deep Dive

### 1. 조인 fan-out으로 인한 매출 과대계상

초기 구현은 마트에서 주문과 checkout 로그를 직접 조인했습니다.

```sql
FROM orders o
LEFT JOIN logs l ON o.user_id = l.user_id
                AND CAST(o.order_time AS DATE) = CAST(l.event_time AS DATE)
```

같은 사용자가 같은 날 `checkout`을 2번 남기면 **주문 행이 복제되어 `SUM(amount)`가 부풀었습니다.**
원본 데이터에 이미 중복 checkout user-day가 7쌍 존재했지만, 주문과 겹치는 날이 없어
**결과가 우연히 맞아 문제가 드러나지 않는 잠재 결함**이었습니다.

재현 테스트로 확인한 오차:

| 조건 | 매출 | 주문 |
|---|---|---|
| 원본 기준 정답 (2023-10-14) | 254,800 | 9 |
| 버그 로직 + 중복 로그 1건 | 279,400 (**+24,600**) | 10 |

**해결** — 조인 전에 로그를 user-day 그레인으로 축약하는 `int_daily_checkout_device` 계층을 두어
fan-out을 구조적으로 차단했습니다. 같은 날 여러 기기로 결제한 경우
`ARG_MAX(device, event_time)`으로 **마지막 결제 기기를 대표값으로 채택**하는 규칙을 명시했습니다.

### 2. 오차를 원인과 무관하게 탐지하는 정합성 테스트

fan-out은 `SUM(amount)`만 부풀리고 단일 그룹의 `COUNT(DISTINCT order_id)`는 정상값을 유지합니다.
**주문 건수만 모니터링하면 매출 오차를 놓칩니다.**

그래서 마트 집계를 원본과 직접 대조하는 테스트를 추가했습니다.
→ `dbt/macros/test_reconciles_with_stg_orders.sql`

이 테스트는 오차 원인을 몰라도 **오차가 발생한 일자와 금액을 지목**합니다.
버그 로직으로 되돌려 검증한 결과 정확히 실패하며 위 표의 오차를 반환했습니다.

singular test(`tests/*.sql`)가 아니라 **generic test로 구현한 이유**가 있습니다.
Cosmos의 기본 `TestBehavior`(`after_each`)는 모델에 연결된 테스트만 Airflow 태스크로 만들기 때문에,
singular test는 로컬 `dbt build`에서는 돌지만 **Airflow DAG에서는 실행되지 않습니다.**
가장 중요한 테스트가 스케줄러에서 누락되는 것을 막기 위해 마트 모델에 붙는 generic test로 전환했습니다.

### 3. 데이터 품질 테스트 (총 30개)

| 대상 | 검증 내용 |
|---|---|
| `stg_orders` | `order_id` unique/not_null, `amount >= 0`, `status` 허용값 |
| `stg_orders.order_time` | 파싱 실패 유입을 **warn severity**로 감지 (파이프라인은 중단하지 않음) |
| `stg_user_logs` | `log_id` unique, `event_name`·`device` 허용값 |
| `int_daily_checkout_device` | **user-day 당 1행 그레인 계약** (이후 수정으로 그레인이 깨지면 실패) |
| `mart_daily_revenue` | `(order_date, device)` 조합 유일성, 금액/건수 범위 |
| 정합성 | 마트 매출·주문이 원본과 일치 |

### 4. 전체 재생성 대신 증분 처리

`@daily` 스케줄에서 마트를 매번 전체 재생성하면 파이프라인을 둔 이유가 사라집니다.

```sql
{{ config(materialized='incremental',
          unique_key=['order_date','device'],
          incremental_strategy='delete+insert') }}
```

`lookback_days`(기본 3일)만큼 되돌아가 재집계하여 **지연 도착 주문을 흡수**하고,
`delete+insert`로 해당 구간의 기존 행을 교체합니다.
전체 재생성이 필요하면 `make build-full`.

### 5. 실행 환경 재현성

초기 버전은 DAG와 `profiles.yml`에 절대경로가 하드코딩되어 있어
**디렉토리를 옮기자 파이프라인이 전부 깨졌습니다.**

- DAG는 파일 위치에서 레포 루트를 역산 (`Path(__file__).resolve().parents[2]`)
- `profiles.yml`은 `env_var('DUCKDB_PATH')` 사용
- Python 스크립트는 `Path(__file__).parent` 기준 경로 사용
- `raw_data/`는 gitignore 대상이라 clone 직후 없으므로 실행 시 자동 생성
- 버전 고정: `requirements.txt`

### 6. 실패 처리

DuckDB는 파일 하나에 쓰기 커넥션이 하나만 붙기 때문에 태스크가 겹치면 락 충돌이 발생합니다.

- `max_active_tasks=1`, `max_active_runs=1`, dbt `threads: 1`로 동시 쓰기 차단
- 일시적 실패는 `retries=2` + exponential backoff로 흡수
- 최종 실패 시 `on_failure_callback` 호출 (운영에서는 이 지점에 Slack/PagerDuty 연결)

## 기술 스택

`Python` `DuckDB` `dbt` `Apache Airflow 3` `astronomer-cosmos` `Streamlit` `SQL`

## 참고: 왜 대시보드에서 원본을 직접 쿼리하지 않는가

1. **성능/비용** — 미리 계산한 마트를 읽으면 대시보드가 가벼워집니다.
2. **단일 진실 공급원** — 정제된 마트를 여러 팀이 일관되게 재사용합니다.
3. **신뢰성** — 깨진 원본이 대시보드에 그대로 노출되는 것을 테스트 단계에서 차단합니다.
