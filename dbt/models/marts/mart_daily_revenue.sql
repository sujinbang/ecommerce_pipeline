{{
    config(
        materialized='incremental',
        unique_key=['order_date', 'device'],
        incremental_strategy='delete+insert'
    )
}}

WITH orders AS (
    SELECT *
    FROM {{ ref('stg_orders') }}
    WHERE status = 'COMPLETED'
      -- 파싱 실패한 주문 시각은 일자 집계 키를 만들 수 없어 제외한다.
      -- 유입 여부는 stg_orders.order_time의 not_null(warn) 테스트로 감지한다.
      AND order_time IS NOT NULL

    {% if is_incremental() %}
      -- 전체 재생성 대신 최근 구간만 재집계한다.
      -- lookback_days만큼 겹쳐 읽어 지연 도착(late-arriving) 주문을 흡수하고,
      -- delete+insert 전략이 해당 구간의 기존 행을 교체한다.
      AND order_time >= (
            SELECT COALESCE(MAX(order_date), DATE '1900-01-01')
                   - INTERVAL {{ var('lookback_days') }} DAY
            FROM {{ this }}
      )
    {% endif %}
),

-- user-day 그레인이 보장된 모델을 참조하므로 아래 조인은 행을 복제하지 않는다.
checkout AS (
    SELECT
        user_id,
        event_date,
        device
    FROM {{ ref('int_daily_checkout_device') }}
)

SELECT
    CAST(o.order_time AS DATE) AS order_date,
    COALESCE(c.device, 'Unknown') AS device,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(o.amount) AS total_revenue
FROM orders o
LEFT JOIN checkout c
    ON o.user_id = c.user_id
   AND CAST(o.order_time AS DATE) = c.event_date
GROUP BY 1, 2
