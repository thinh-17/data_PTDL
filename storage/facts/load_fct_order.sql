WITH item_agg AS (
    SELECT
        order_id,
        COUNT(*) AS item_count,
        SUM(price) AS order_value,
        SUM(freight_value) AS freight_value
    FROM staging.order_items
    GROUP BY order_id
),
payment_agg AS (
    SELECT
        order_id,
        SUM(payment_value) AS payment_value,
        MAX(payment_installments) AS payment_installments
    FROM staging.order_payments
    GROUP BY order_id
),
src AS (
    SELECT
        o.order_id,
        dc.customer_key,
        dod.order_detail_key,
        CASE
            WHEN o.order_delivered_customer_date IS NOT NULL
            THEN (o.order_delivered_customer_date::date - o.order_purchase_timestamp::date)
            ELSE NULL
        END AS waiting_day,
        ia.item_count,
        ia.order_value,
        ia.freight_value,
        pa.payment_value,
        pa.payment_installments
    FROM staging.orders o
    LEFT JOIN storage.dim_customer dc
        ON o.customer_id = dc.customer_id
       AND dc.is_current = TRUE
    LEFT JOIN storage.dim_order_detail dod
        ON o.order_id = dod.order_id
    LEFT JOIN item_agg ia
        ON o.order_id = ia.order_id
    LEFT JOIN payment_agg pa
        ON o.order_id = pa.order_id
)
INSERT INTO storage.fct_order(
    order_id, customer_key, order_detail_key, waiting_day, item_count,
    order_value, freight_value, payment_value, payment_installments
)
SELECT
    order_id, customer_key, order_detail_key, waiting_day, item_count,
    order_value, freight_value, payment_value, payment_installments
FROM src
ON CONFLICT (order_id) DO UPDATE
SET customer_key = EXCLUDED.customer_key,
    order_detail_key = EXCLUDED.order_detail_key,
    waiting_day = EXCLUDED.waiting_day,
    item_count = EXCLUDED.item_count,
    order_value = EXCLUDED.order_value,
    freight_value = EXCLUDED.freight_value,
    payment_value = EXCLUDED.payment_value,
    payment_installments = EXCLUDED.payment_installments;
