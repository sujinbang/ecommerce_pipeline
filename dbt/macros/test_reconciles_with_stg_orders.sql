{% test reconciles_with_stg_orders(model) %}
--
-- 마트 집계값이 스테이징 원본과 일치하는지 검증하는 정합성(reconciliation) 테스트.
--
-- 조인 fan-out으로 주문 행이 복제되면 SUM(amount)만 부풀고 단일 그룹의
-- COUNT(DISTINCT order_id)는 정상값을 유지한다. 주문 건수만 모니터링하면 매출 오차를 놓친다.
-- 이 테스트는 매출과 주문 건수를 원본과 직접 대조하므로 오차 원인과 무관하게 탐지한다.
--
-- singular test(tests/*.sql)가 아니라 generic test로 구현한 이유:
-- Cosmos의 기본 TestBehavior(after_each)는 모델에 연결된 테스트만 Airflow 태스크로 만든다.
-- singular test는 어떤 모델 노드에도 붙지 않아 DAG에서 실행되지 않는다.
--
-- 증분 모델이므로 마트에 존재하는 일자에 한해 비교한다(INNER JOIN).
-- 행이 하나라도 반환되면 실패.
--
WITH source_daily AS (
    SELECT
        CAST(order_time AS DATE) AS order_date,
        SUM(amount) AS revenue,
        COUNT(DISTINCT order_id) AS orders
    FROM {{ ref('stg_orders') }}
    WHERE status = 'COMPLETED'
      AND order_time IS NOT NULL
    GROUP BY 1
),

mart_daily AS (
    SELECT
        order_date,
        SUM(total_revenue) AS revenue,
        SUM(total_orders) AS orders
    FROM {{ model }}
    GROUP BY 1
)

SELECT
    s.order_date,
    s.revenue AS source_revenue,
    m.revenue AS mart_revenue,
    m.revenue - s.revenue AS revenue_diff,
    s.orders AS source_orders,
    m.orders AS mart_orders
FROM source_daily s
INNER JOIN mart_daily m
    ON s.order_date = m.order_date
WHERE s.revenue <> m.revenue
   OR s.orders <> m.orders

{% endtest %}
