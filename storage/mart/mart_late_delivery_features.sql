CREATE OR REPLACE VIEW storage.mart_late_delivery_features AS
WITH item_agg AS (
    SELECT
        oi.order_id,
        COUNT(*) AS item_count,
        SUM(oi.price) AS order_value,
        SUM(oi.freight_value) AS freight_value,
        COUNT(DISTINCT oi.seller_id) AS seller_count,
        MIN(s.seller_state) AS seller_state,
        MAX(oi.shipping_limit_date) AS max_shipping_limit_date,
        AVG(p.product_weight_g) AS avg_product_weight_g,
        AVG(
            COALESCE(p.product_length_cm, 0)
            * COALESCE(p.product_height_cm, 0)
            * COALESCE(p.product_width_cm, 0)
        ) AS avg_product_volume_cm3
    FROM staging.order_items oi
    LEFT JOIN staging.sellers s
        ON oi.seller_id = s.seller_id
    LEFT JOIN staging.products p
        ON oi.product_id = p.product_id
    GROUP BY oi.order_id
),
payment_agg AS (
    SELECT
        order_id,
        SUM(payment_value) AS payment_value,
        MAX(payment_installments) AS payment_installments
    FROM staging.order_payments
    GROUP BY order_id
)
SELECT
    o.order_id,

    COALESCE(ia.order_value, 0) AS order_value,
    COALESCE(ia.freight_value, 0) AS freight_value,
    COALESCE(ia.freight_value, 0) / NULLIF(COALESCE(ia.order_value, 0), 0) AS freight_ratio,
    COALESCE(ia.item_count, 0) AS item_count,
    COALESCE(pa.payment_value, 0) AS payment_value,
    COALESCE(pa.payment_installments, 0) AS payment_installments,

    EXTRACT(EPOCH FROM (o.order_approved_at - o.order_purchase_timestamp)) / 3600.0
        AS approval_waiting_hours,

    (o.order_estimated_delivery_date - o.order_purchase_timestamp::date)
        AS estimated_delivery_days,

    CASE
        WHEN ia.max_shipping_limit_date IS NOT NULL
        THEN EXTRACT(EPOCH FROM (ia.max_shipping_limit_date - o.order_purchase_timestamp)) / 86400.0
        ELSE NULL
    END AS shipping_limit_days,

    COALESCE(ia.avg_product_weight_g, 0) AS avg_product_weight_g,
    COALESCE(ia.avg_product_volume_cm3, 0) AS avg_product_volume_cm3,
    COALESCE(ia.seller_count, 0) AS seller_count,

    c.customer_state,
    ia.seller_state,

    CASE
        WHEN c.customer_state IS NOT NULL
         AND ia.seller_state IS NOT NULL
         AND c.customer_state = ia.seller_state
        THEN 1 ELSE 0
    END AS same_state_flag,

    -- Chỉ dùng để kiểm tra/report, không đưa vào X
    (o.order_delivered_customer_date::date - o.order_estimated_delivery_date) AS delay_days,

    CASE
        WHEN o.order_delivered_customer_date::date > o.order_estimated_delivery_date
        THEN 1 ELSE 0
    END AS late_delivery

FROM staging.orders o
JOIN staging.customers c
    ON o.customer_id = c.customer_id
LEFT JOIN item_agg ia
    ON o.order_id = ia.order_id
LEFT JOIN payment_agg pa
    ON o.order_id = pa.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp IS NOT NULL
  AND o.order_estimated_delivery_date IS NOT NULL
  AND o.order_delivered_customer_date IS NOT NULL;