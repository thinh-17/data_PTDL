WITH src AS (
    SELECT
        r.review_id,
        r.order_id,
        dc.customer_key,
        drs.review_score_key,
        CASE WHEN r.review_creation_date IS NOT NULL
             THEN TO_CHAR(r.review_creation_date::date, 'YYYYMMDD')::int
             ELSE NULL END AS review_creation_date_key,
        CASE WHEN r.review_answer_timestamp IS NOT NULL
             THEN TO_CHAR(r.review_answer_timestamp::date, 'YYYYMMDD')::int
             ELSE NULL END AS review_answer_date_key,
        1 AS review_count,
        r.review_score,
        CASE
            WHEN r.review_comment_message IS NOT NULL AND TRIM(r.review_comment_message) <> ''
            THEN TRUE ELSE FALSE
        END AS has_comment_message
    FROM staging.order_reviews r
    LEFT JOIN staging.orders o
        ON r.order_id = o.order_id
    LEFT JOIN storage.dim_customer dc
        ON o.customer_id = dc.customer_id
       AND dc.is_current = TRUE
    LEFT JOIN storage.dim_review_score drs
        ON r.review_score = drs.review_score
)
INSERT INTO storage.fct_order_review(
    review_id, order_id, customer_key, review_score_key,
    review_creation_date_key, review_answer_date_key,
    review_count, review_score, has_comment_message
)
SELECT
    review_id, order_id, customer_key, review_score_key,
    review_creation_date_key, review_answer_date_key,
    review_count, review_score, has_comment_message
FROM src
ON CONFLICT (review_id) DO UPDATE
SET order_id = EXCLUDED.order_id,
    customer_key = EXCLUDED.customer_key,
    review_score_key = EXCLUDED.review_score_key,
    review_creation_date_key = EXCLUDED.review_creation_date_key,
    review_answer_date_key = EXCLUDED.review_answer_date_key,
    review_count = EXCLUDED.review_count,
    review_score = EXCLUDED.review_score,
    has_comment_message = EXCLUDED.has_comment_message;
