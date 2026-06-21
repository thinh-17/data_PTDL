-- Phân tích hiệu quả seller.
SELECT
    ds.seller_id,
    SUM(f.total_revenue) AS total_revenue,
    SUM(f.orders_created_cnt) AS order_cnt,
    SUM(f.items_sold_cnt) AS items_sold_cnt,
    AVG(f.avg_review_score) AS avg_review_score,
    SUM(f.cancelled_orders_cnt)::numeric / NULLIF(SUM(f.orders_created_cnt), 0) AS cancellation_rate
FROM storage.fct_daily_seller_snapshot f
JOIN storage.dim_seller ds
    ON f.seller_key = ds.seller_key
GROUP BY ds.seller_id
ORDER BY total_revenue DESC
LIMIT 20;
