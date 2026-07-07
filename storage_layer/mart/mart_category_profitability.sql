DROP TABLE IF EXISTS storage.mart_category_profitability;

CREATE TABLE storage.mart_category_profitability AS
SELECT
    COALESCE(dp.product_category_name_english) AS category,

    SUM(COALESCE(fp.total_revenue, 0)) AS gmv,
    SUM(COALESCE(fp.items_sold_cnt, 0)) AS items_sold,

    SUM(COALESCE(fp.estimated_cogs, 0)) AS estimated_cogs,
    SUM(COALESCE(fp.estimated_tax, 0)) AS estimated_tax,

    SUM(COALESCE(fp.gross_profit, 0)) AS gross_profit,

    SUM(COALESCE(fp.net_revenue_after_tax, 0)) AS net_revenue_after_tax,

    SUM(COALESCE(fp.gross_profit, 0))
        / NULLIF(SUM(COALESCE(fp.total_revenue, 0)), 0) * 100 AS gross_margin,

    SUM(COALESCE(fp.net_revenue_after_tax, 0))
        / NULLIF(SUM(COALESCE(fp.total_revenue, 0)), 0) * 100 AS net_revenue_after_tax_ratio,

    SUM(COALESCE(fp.total_revenue, 0))
        / NULLIF(SUM(COALESCE(fp.items_sold_cnt, 0)), 0) AS revenue_per_item

FROM storage.fct_daily_product_snapshot fp
JOIN storage.dim_product dp
    ON fp.product_key = dp.product_key
GROUP BY 1
ORDER BY gmv DESC;