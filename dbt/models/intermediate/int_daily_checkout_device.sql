{{ config(materialized='view') }}

-- 주문과 조인하기 전에 checkout 로그를 user_id + 일자 그레인으로 축약한다.
-- 이 축약이 없으면 같은 user-day에 checkout 로그가 2건 이상일 때 주문 행이 복제되어
-- SUM(amount)가 과대계상된다. COUNT(DISTINCT order_id)는 정상값을 유지하기 때문에
-- 주문 건수만 보고 있으면 매출 오차를 탐지할 수 없다.

WITH checkout_logs AS (
    SELECT
        user_id,
        CAST(event_time AS DATE) AS event_date,
        event_time,
        device
    FROM {{ ref('stg_user_logs') }}
    WHERE event_name = 'checkout'
      AND event_time IS NOT NULL
)

SELECT
    user_id,
    event_date,
    -- 같은 날 여러 기기로 checkout한 경우 마지막 결제 기기를 대표값으로 채택
    ARG_MAX(device, event_time) AS device,
    COUNT(*) AS checkout_count
FROM checkout_logs
GROUP BY user_id, event_date
