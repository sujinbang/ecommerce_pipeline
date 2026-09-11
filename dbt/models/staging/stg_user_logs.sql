{{ config(materialized='view') }}

WITH raw AS (
    SELECT * FROM {{ source('raw', 'raw_user_logs') }}
)

SELECT
    log_id,
    user_id,
    TRY_CAST(event_time AS TIMESTAMP) AS event_time,
    event_name,
    -- event_properties 자체가 누락된 행이 있어 struct 접근 전 COALESCE로 방어
    COALESCE(event_properties.device, 'Unknown') AS device
FROM raw
