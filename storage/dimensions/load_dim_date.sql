INSERT INTO storage.dim_date (
    date_key, full_date, day_of_month, month_num, month_name, quarter_num, year_num
)
SELECT
    TO_CHAR(d::date, 'YYYYMMDD')::int AS date_key,
    d::date AS full_date,
    EXTRACT(DAY FROM d)::int AS day_of_month,
    EXTRACT(MONTH FROM d)::int AS month_num,
    TO_CHAR(d, 'Month') AS month_name,
    EXTRACT(QUARTER FROM d)::int AS quarter_num,
    EXTRACT(YEAR FROM d)::int AS year_num
FROM generate_series(
    COALESCE((SELECT MIN(order_purchase_timestamp)::date FROM staging.orders), '2016-01-01'::date),
    COALESCE((SELECT MAX(order_estimated_delivery_date)::date FROM staging.orders), '2019-12-31'::date),
    interval '1 day'
) d
ON CONFLICT (date_key) DO NOTHING;
