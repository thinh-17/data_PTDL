-- Tăng trưởng doanh thu theo tháng.
WITH monthly AS (
    SELECT
        year_num,
        month_num,
        total_revenue,
        LAG(total_revenue) OVER (ORDER BY year_num, month_num) AS previous_revenue
    FROM storage.mart_financial_kpi
)
SELECT
    year_num,
    month_num,
    total_revenue,
    previous_revenue,
    (total_revenue - previous_revenue) / NULLIF(previous_revenue, 0) AS revenue_growth_rate
FROM monthly
ORDER BY year_num, month_num;
