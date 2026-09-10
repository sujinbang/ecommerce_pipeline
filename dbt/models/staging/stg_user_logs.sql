{{ config(materialized='view') }}

WITH raw AS (
    SELECT * FROM main.raw_user_logs
)

SELECT
    log_id,
    user_id,
    event_time,
    event_name,
    -- JSON 안의 struct에서 device 정보만 추출. (만약 event_properties 전체가 누락된 경우 'Unknown'으로 처리)
    COALESCE(event_properties.device, 'Unknown') AS device
FROM raw
