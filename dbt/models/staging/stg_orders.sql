{{ config(materialized='view') }}

WITH raw AS (
    SELECT * FROM main.raw_orders
)

SELECT
    order_id,
    user_id,
    -- 1. 날짜 포맷팅: YYYY/MM/DD 포맷을 -로 변경 후 Timestamp로 변환
    TRY_CAST(REPLACE(order_timestamp, '/', '-') AS TIMESTAMP) AS order_time,
    
    -- 2. 금액 결측치 및 이상치 처리: 빈 값은 0으로, 음수 값도 0으로, 나머지는 정수로 변환
    CASE 
        WHEN amount IS NULL OR amount = '' THEN 0
        WHEN TRY_CAST(amount AS INTEGER) < 0 THEN 0
        ELSE TRY_CAST(amount AS INTEGER)
    END AS amount,
    
    status
FROM raw
