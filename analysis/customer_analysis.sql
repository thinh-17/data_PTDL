-- Phân tích giá trị khách hàng.
SELECT
    dc.customer_unique_id,
    f.total_spend,
    f.order_cnt,
    f.avg_score_review,
    f.order_cancelled_cnt,
    f.avg_day_return_to_buy
FROM storage.fct_customer_behavior_snapshot f
JOIN storage.dim_customer dc
    ON f.customer_key = dc.customer_key
WHERE dc.is_current = TRUE
ORDER BY f.total_spend DESC
LIMIT 20;
