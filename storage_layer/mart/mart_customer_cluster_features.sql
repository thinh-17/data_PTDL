CREATE OR REPLACE VIEW storage.mart_customer_cluster_features AS
SELECT
    dc.customer_key,
    dc.customer_unique_id,
    COALESCE(f.total_spend, 0) AS total_spend,
    COALESCE(f.order_cnt, 0) AS order_cnt,
    COALESCE(f.total_spend, 0) / NULLIF(COALESCE(f.order_cnt, 0), 0) AS avg_order_value,
    COALESCE(f.avg_score_review, 0) AS avg_review_score,
    COALESCE(f.order_cancelled_cnt, 0) AS order_cancelled_cnt,
    COALESCE(f.avg_day_return_to_buy, 0) AS avg_day_return_to_buy
FROM storage.fct_customer_behavior_snapshot f
JOIN storage.dim_customer dc
    ON f.customer_key = dc.customer_key
WHERE dc.is_current = TRUE;
