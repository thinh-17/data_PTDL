WITH item_agg AS (
    SELECT order_id, SUM(price) AS order_value
    FROM staging.order_items
    GROUP BY order_id
),
daily AS (
    SELECT
        TO_CHAR(o.order_purchase_timestamp::date, 'YYYYMMDD')::int AS snapshot_date_key,
        COUNT(*) AS total_orders_created,
        COUNT(*) FILTER (WHERE o.order_approved_at IS NOT NULL) AS total_orders_approved,
        COUNT(*) FILTER (WHERE o.order_status = 'delivered') AS total_orders_delivered,
        COUNT(*) FILTER (WHERE o.order_status = 'canceled') AS total_orders_cancelled,
        SUM(COALESCE(ia.order_value, 0)) AS total_revenue
    FROM staging.orders o
    LEFT JOIN item_agg ia ON o.order_id = ia.order_id
    WHERE o.order_purchase_timestamp IS NOT NULL
    GROUP BY TO_CHAR(o.order_purchase_timestamp::date, 'YYYYMMDD')::int
)
INSERT INTO storage.fct_daily_order_snapshot(
    snapshot_date_key, total_orders_created, total_orders_approved,
    total_orders_delivered, total_orders_cancelled, total_revenue
)
SELECT snapshot_date_key, total_orders_created, total_orders_approved,
       total_orders_delivered, total_orders_cancelled, total_revenue
FROM daily
ON CONFLICT (snapshot_date_key) DO UPDATE
SET total_orders_created = EXCLUDED.total_orders_created,
    total_orders_approved = EXCLUDED.total_orders_approved,
    total_orders_delivered = EXCLUDED.total_orders_delivered,
    total_orders_cancelled = EXCLUDED.total_orders_cancelled,
    total_revenue = EXCLUDED.total_revenue;
