{{ config(materialized='view') }}

WITH raw AS (
    SELECT * FROM {{ source('raw', 'raw_orders') }}
)

SELECT
    order_id,
    user_id,
    -- 날짜 포맷 통일: YYYY/MM/DD 표기를 - 로 치환한 뒤 TIMESTAMP 변환
    TRY_CAST(REPLACE(order_timestamp, '/', '-') AS TIMESTAMP) AS order_time,

    -- 금액 결측/이상치 처리: 빈 값과 음수는 0으로 수렴
    CASE
        WHEN amount IS NULL OR amount = '' THEN 0
        WHEN TRY_CAST(amount AS INTEGER) < 0 THEN 0
        ELSE TRY_CAST(amount AS INTEGER)
    END AS amount,

    status
FROM raw
