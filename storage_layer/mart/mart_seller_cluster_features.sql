CREATE OR REPLACE VIEW storage.mart_seller_cluster_features AS
SELECT
    ds.seller_key,
    ds.seller_id,
    SUM(f.total_revenue) AS total_revenue,
    SUM(f.orders_created_cnt) AS orders_count,
    SUM(f.items_sold_cnt) AS items_sold,
    SUM(f.total_revenue) / NULLIF(SUM(f.orders_created_cnt), 0) AS avg_order_value,
    AVG(f.avg_review_score) AS avg_review_score,
    SUM(f.cancelled_orders_cnt)::numeric / NULLIF(SUM(f.orders_created_cnt), 0) AS cancelled_orders_rate,
    SUM(f.distinct_products_sold) AS distinct_products_sold
FROM storage.fct_daily_seller_snapshot f
JOIN storage.dim_seller ds
    ON f.seller_key = ds.seller_key
WHERE ds.is_current = TRUE
GROUP BY ds.seller_key, ds.seller_id;
