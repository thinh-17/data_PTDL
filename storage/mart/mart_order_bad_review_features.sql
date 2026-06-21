CREATE OR REPLACE VIEW storage.mart_order_bad_review_features AS
SELECT
    f.order_id,
    COALESCE(f.order_value, 0) AS order_value,
    COALESCE(f.freight_value, 0) AS freight_value,
    COALESCE(f.freight_value, 0) / NULLIF(COALESCE(f.order_value, 0), 0) AS freight_ratio,
    COALESCE(f.item_count, 0) AS item_count,
    COALESCE(f.waiting_day, 0) AS waiting_day,
    CASE
        WHEN dod.delivered_date_key IS NOT NULL
         AND dod.delivered_date_key > (
             SELECT date_key
             FROM storage.dim_date
             WHERE full_date = (
                 SELECT order_estimated_delivery_date
                 FROM staging.orders so
                 WHERE so.order_id = f.order_id
                 LIMIT 1
             )
         )
        THEN 1 ELSE 0
    END AS is_late,
    COALESCE(f.payment_installments, 0) AS payment_installments,
    COALESCE(forv.review_score, 0) AS review_score,
    CASE WHEN COALESCE(forv.review_score, 0) <= 2 THEN 1 ELSE 0 END AS bad_review
FROM storage.fct_order f
JOIN storage.dim_order_detail dod
    ON f.order_detail_key = dod.order_detail_key
LEFT JOIN storage.fct_order_review forv
    ON f.order_id = forv.order_id
WHERE forv.review_score IS NOT NULL;
