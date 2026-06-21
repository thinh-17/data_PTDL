WITH customer_base AS (
    SELECT
        customer_unique_id,
        MIN(customer_key) AS customer_key
    FROM storage.dim_customer
    WHERE is_current = TRUE
    GROUP BY customer_unique_id
),
order_level AS (
    SELECT
        c.customer_unique_id,
        cb.customer_key,
        o.order_id,
        o.order_purchase_timestamp,
        o.order_status,
        COALESCE(SUM(oi.price),0) AS order_value,
        AVG(r.review_score)::numeric(5,2) AS avg_review_score
    FROM staging.orders o
    JOIN staging.customers c
        ON o.customer_id = c.customer_id
    JOIN customer_base cb
        ON c.customer_unique_id = cb.customer_unique_id
    LEFT JOIN staging.order_items oi
        ON o.order_id = oi.order_id
    LEFT JOIN staging.order_reviews r
        ON o.order_id = r.order_id
    GROUP BY c.customer_unique_id, cb.customer_key, o.order_id, o.order_purchase_timestamp, o.order_status
),
customer_agg AS (
    SELECT
        customer_key,
        AVG(avg_review_score)::numeric(5,2) AS avg_score_review,
        SUM(order_value) AS total_spend,
        COUNT(*) AS order_cnt,
        COUNT(*) FILTER (WHERE order_status = 'canceled') AS order_cancelled_cnt,
        CASE
            WHEN COUNT(*) > 1 THEN
                (MAX(order_purchase_timestamp::date) - MIN(order_purchase_timestamp::date))::numeric
                / NULLIF(COUNT(*) - 1, 0)
            ELSE NULL
        END AS avg_day_return_to_buy
    FROM order_level
    GROUP BY customer_key
)
INSERT INTO storage.fct_customer_behavior_snapshot(
    customer_key, avg_score_review, total_spend, order_cnt,
    order_cancelled_cnt, avg_day_return_to_buy
)
SELECT customer_key, avg_score_review, total_spend, order_cnt,
       order_cancelled_cnt, avg_day_return_to_buy
FROM customer_agg
ON CONFLICT (customer_key) DO UPDATE
SET avg_score_review = EXCLUDED.avg_score_review,
    total_spend = EXCLUDED.total_spend,
    order_cnt = EXCLUDED.order_cnt,
    order_cancelled_cnt = EXCLUDED.order_cancelled_cnt,
    avg_day_return_to_buy = EXCLUDED.avg_day_return_to_buy;
