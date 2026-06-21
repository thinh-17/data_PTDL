-- Doanh thu theo category sản phẩm.
SELECT
    dp.product_category_name_english,
    SUM(f.total_revenue) AS total_revenue,
    SUM(f.items_sold_cnt) AS items_sold_cnt,
    AVG(f.avg_review_score) AS avg_review_score
FROM storage.fct_daily_product_snapshot f
JOIN storage.dim_product dp
    ON f.product_key = dp.product_key
WHERE dp.is_current = TRUE
GROUP BY dp.product_category_name_english
ORDER BY total_revenue DESC
LIMIT 20;
