{{ config(materialized='table') }}

WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

logs AS (
    SELECT * FROM {{ ref('stg_user_logs') }}
    -- checkout 이벤트만 필터링하여 기기 정보 획득
    WHERE event_name = 'checkout'
)

SELECT 
    CAST(o.order_time AS DATE) AS order_date,
    COALESCE(l.device, 'Unknown') AS device,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(o.amount) AS total_revenue
FROM orders o
LEFT JOIN logs l 
    ON o.user_id = l.user_id 
    -- 날짜가 같은 로그만 조인 (간단한 예시를 위해 날짜만 비교)
    AND CAST(o.order_time AS DATE) = CAST(l.event_time AS DATE)
WHERE o.status = 'COMPLETED'
GROUP BY 1, 2
ORDER BY 1 DESC, 2
