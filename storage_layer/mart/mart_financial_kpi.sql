CREATE OR REPLACE VIEW storage.mart_financial_kpi AS
SELECT
    d.year_num,
    d.month_num,
    COUNT(f.order_id) AS order_cnt,
    SUM(f.order_value) AS total_revenue,
    AVG(f.order_value) AS avg_order_value,
    SUM(f.freight_value) AS total_freight,
    SUM(f.freight_value) / NULLIF(SUM(f.order_value), 0) AS freight_ratio,
    SUM(CASE WHEN dod.order_status = 'canceled' THEN 1 ELSE 0 END)::numeric
        / NULLIF(COUNT(f.order_id), 0) AS cancellation_rate
FROM storage.fct_order f
JOIN storage.dim_order_detail dod
    ON f.order_detail_key = dod.order_detail_key
JOIN storage.dim_date d
    ON dod.purchase_date_key = d.date_key
GROUP BY d.year_num, d.month_num
ORDER BY d.year_num, d.month_num;
