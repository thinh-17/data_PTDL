WITH order_review AS (
    SELECT order_id, AVG(review_score)::numeric(5,2) AS avg_review_score
    FROM staging.order_reviews
    GROUP BY order_id
),
daily AS (
    SELECT
        TO_CHAR(o.order_purchase_timestamp::date, 'YYYYMMDD')::int AS snapshot_date_key,
        dp.product_key,
        COUNT(oi.order_item_id) AS items_sold_cnt,
        SUM(oi.price) AS total_revenue,
        AVG(orv.avg_review_score)::numeric(5,2) AS avg_review_score
    FROM staging.orders o
    JOIN staging.order_items oi ON o.order_id = oi.order_id
    JOIN storage.dim_product dp
        ON oi.product_id = dp.product_id
       AND dp.is_current = TRUE
    LEFT JOIN order_review orv
        ON o.order_id = orv.order_id
    WHERE o.order_purchase_timestamp IS NOT NULL
    GROUP BY TO_CHAR(o.order_purchase_timestamp::date, 'YYYYMMDD')::int, dp.product_key
)
INSERT INTO storage.fct_daily_product_snapshot(
    snapshot_date_key, product_key, items_sold_cnt, total_revenue, avg_review_score
)
SELECT snapshot_date_key, product_key, items_sold_cnt, total_revenue, avg_review_score
FROM daily
ON CONFLICT (snapshot_date_key, product_key) DO UPDATE
SET items_sold_cnt = EXCLUDED.items_sold_cnt,
    total_revenue = EXCLUDED.total_revenue,
    avg_review_score = EXCLUDED.avg_review_score;
