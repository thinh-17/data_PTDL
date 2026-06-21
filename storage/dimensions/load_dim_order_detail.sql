-- SCD Type 1 cho dim_order_detail: order_status được cập nhật giá trị mới nhất.

WITH src AS (
    SELECT
        o.order_id,
        o.order_status,
        TO_CHAR(o.order_purchase_timestamp::date, 'YYYYMMDD')::int AS purchase_date_key,
        CASE
            WHEN o.order_delivered_customer_date IS NOT NULL
            THEN TO_CHAR(o.order_delivered_customer_date::date, 'YYYYMMDD')::int
            ELSE NULL
        END AS delivered_date_key,
        dc.customer_key,
        MD5(CONCAT_WS('|',
            o.order_id,
            o.order_status,
            COALESCE(o.order_purchase_timestamp::text, ''),
            COALESCE(o.order_delivered_customer_date::text, ''),
            COALESCE(dc.customer_key::text, '')
        )) AS row_hash
    FROM staging.orders o
    LEFT JOIN storage.dim_customer dc
        ON o.customer_id = dc.customer_id
       AND dc.is_current = TRUE
)
INSERT INTO storage.dim_order_detail(
    order_id, order_status, purchase_date_key, delivered_date_key, customer_key, row_hash
)
SELECT order_id, order_status, purchase_date_key, delivered_date_key, customer_key, row_hash
FROM src
ON CONFLICT (order_id) DO UPDATE
SET order_status = EXCLUDED.order_status,
    purchase_date_key = EXCLUDED.purchase_date_key,
    delivered_date_key = EXCLUDED.delivered_date_key,
    customer_key = EXCLUDED.customer_key,
    row_hash = EXCLUDED.row_hash
WHERE storage.dim_order_detail.row_hash IS DISTINCT FROM EXCLUDED.row_hash;
