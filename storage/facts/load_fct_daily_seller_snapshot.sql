WITH order_review AS (
    SELECT order_id, AVG(review_score)::numeric(5,2) AS avg_review_score
    FROM staging.order_reviews
    GROUP BY order_id
),
daily AS (
    SELECT
        TO_CHAR(o.order_purchase_timestamp::date, 'YYYYMMDD')::int AS snapshot_date_key,
        ds.seller_key,
        COUNT(DISTINCT o.order_id) AS orders_created_cnt,
        COUNT(oi.order_item_id) AS items_sold_cnt,
        SUM(oi.price) AS total_revenue,
        COUNT(DISTINCT o.order_id) FILTER (WHERE o.order_status = 'delivered') AS delivered_orders_cnt,
        COUNT(DISTINCT o.order_id) FILTER (WHERE o.order_status = 'canceled') AS cancelled_orders_cnt,
        AVG(orv.avg_review_score)::numeric(5,2) AS avg_review_score,
        COUNT(DISTINCT oi.product_id) AS distinct_products_sold
    FROM staging.orders o
    JOIN staging.order_items oi ON o.order_id = oi.order_id
    JOIN storage.dim_seller ds
        ON oi.seller_id = ds.seller_id
       AND ds.is_current = TRUE
    LEFT JOIN order_review orv
        ON o.order_id = orv.order_id
    WHERE o.order_purchase_timestamp IS NOT NULL
    GROUP BY TO_CHAR(o.order_purchase_timestamp::date, 'YYYYMMDD')::int, ds.seller_key
)
INSERT INTO storage.fct_daily_seller_snapshot(
    snapshot_date_key, seller_key, orders_created_cnt, items_sold_cnt,
    total_revenue, delivered_orders_cnt, cancelled_orders_cnt,
    avg_review_score, distinct_products_sold
)
SELECT snapshot_date_key, seller_key, orders_created_cnt, items_sold_cnt,
       total_revenue, delivered_orders_cnt, cancelled_orders_cnt,
       avg_review_score, distinct_products_sold
FROM daily
ON CONFLICT (snapshot_date_key, seller_key) DO UPDATE
SET orders_created_cnt = EXCLUDED.orders_created_cnt,
    items_sold_cnt = EXCLUDED.items_sold_cnt,
    total_revenue = EXCLUDED.total_revenue,
    delivered_orders_cnt = EXCLUDED.delivered_orders_cnt,
    cancelled_orders_cnt = EXCLUDED.cancelled_orders_cnt,
    avg_review_score = EXCLUDED.avg_review_score,
    distinct_products_sold = EXCLUDED.distinct_products_sold;
