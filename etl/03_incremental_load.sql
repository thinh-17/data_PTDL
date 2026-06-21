-- Incremental Load từ raw sang staging.
-- Chỉ INSERT/UPDATE dữ liệu thuộc batch hiện tại nếu business key mới hoặc row_hash thay đổi.

-- CUSTOMERS
WITH src AS (
    SELECT DISTINCT ON (customer_id)
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        LOWER(TRIM(customer_city)) AS customer_city,
        UPPER(TRIM(customer_state)) AS customer_state,
        row_hash,
        batch_id
    FROM raw.olist_customers
    WHERE batch_id = {{BATCH_ID}}
    ORDER BY customer_id, loaded_at DESC
),
changed AS (
    SELECT
        'customers' AS table_name,
        src.customer_id AS business_key,
        CASE WHEN tgt.customer_id IS NULL THEN 'INSERT' ELSE 'UPDATE' END AS operation_type,
        tgt.row_hash AS old_row_hash,
        src.row_hash AS new_row_hash,
        src.batch_id
    FROM src
    LEFT JOIN staging.customers tgt ON src.customer_id = tgt.customer_id
    WHERE tgt.customer_id IS NULL OR src.row_hash IS DISTINCT FROM tgt.row_hash
)
INSERT INTO staging.cdc_log(table_name, business_key, operation_type, old_row_hash, new_row_hash, batch_id)
SELECT table_name, business_key, operation_type, old_row_hash, new_row_hash, batch_id
FROM changed;

WITH src AS (
    SELECT DISTINCT ON (customer_id)
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        LOWER(TRIM(customer_city)) AS customer_city,
        UPPER(TRIM(customer_state)) AS customer_state,
        row_hash,
        batch_id
    FROM raw.olist_customers
    WHERE batch_id = {{BATCH_ID}}
    ORDER BY customer_id, loaded_at DESC
)
INSERT INTO staging.customers(
    customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state,
    row_hash, last_batch_id, updated_at
)
SELECT customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state,
       row_hash, batch_id, CURRENT_TIMESTAMP
FROM src
ON CONFLICT (customer_id) DO UPDATE
SET customer_unique_id = EXCLUDED.customer_unique_id,
    customer_zip_code_prefix = EXCLUDED.customer_zip_code_prefix,
    customer_city = EXCLUDED.customer_city,
    customer_state = EXCLUDED.customer_state,
    row_hash = EXCLUDED.row_hash,
    last_batch_id = EXCLUDED.last_batch_id,
    updated_at = CURRENT_TIMESTAMP
WHERE staging.customers.row_hash IS DISTINCT FROM EXCLUDED.row_hash;

-- ORDERS
WITH src AS (
    SELECT DISTINCT ON (order_id)
        order_id,
        customer_id,
        LOWER(TRIM(order_status)) AS order_status,
        NULLIF(order_purchase_timestamp, '')::timestamp AS order_purchase_timestamp,
        NULLIF(order_approved_at, '')::timestamp AS order_approved_at,
        NULLIF(order_delivered_carrier_date, '')::timestamp AS order_delivered_carrier_date,
        NULLIF(order_delivered_customer_date, '')::timestamp AS order_delivered_customer_date,
        NULLIF(order_estimated_delivery_date, '')::date AS order_estimated_delivery_date,
        row_hash,
        batch_id
    FROM raw.olist_orders
    WHERE batch_id = {{BATCH_ID}}
    ORDER BY order_id, loaded_at DESC
),
changed AS (
    SELECT
        'orders' AS table_name,
        src.order_id AS business_key,
        CASE WHEN tgt.order_id IS NULL THEN 'INSERT' ELSE 'UPDATE' END AS operation_type,
        tgt.row_hash AS old_row_hash,
        src.row_hash AS new_row_hash,
        src.batch_id
    FROM src
    LEFT JOIN staging.orders tgt ON src.order_id = tgt.order_id
    WHERE tgt.order_id IS NULL OR src.row_hash IS DISTINCT FROM tgt.row_hash
)
INSERT INTO staging.cdc_log(table_name, business_key, operation_type, old_row_hash, new_row_hash, batch_id)
SELECT table_name, business_key, operation_type, old_row_hash, new_row_hash, batch_id
FROM changed;

WITH src AS (
    SELECT DISTINCT ON (order_id)
        order_id,
        customer_id,
        LOWER(TRIM(order_status)) AS order_status,
        NULLIF(order_purchase_timestamp, '')::timestamp AS order_purchase_timestamp,
        NULLIF(order_approved_at, '')::timestamp AS order_approved_at,
        NULLIF(order_delivered_carrier_date, '')::timestamp AS order_delivered_carrier_date,
        NULLIF(order_delivered_customer_date, '')::timestamp AS order_delivered_customer_date,
        NULLIF(order_estimated_delivery_date, '')::date AS order_estimated_delivery_date,
        row_hash,
        batch_id
    FROM raw.olist_orders
    WHERE batch_id = {{BATCH_ID}}
    ORDER BY order_id, loaded_at DESC
)
INSERT INTO staging.orders(
    order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at,
    order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date,
    row_hash, last_batch_id, updated_at
)
SELECT order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at,
       order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date,
       row_hash, batch_id, CURRENT_TIMESTAMP
FROM src
ON CONFLICT (order_id) DO UPDATE
SET customer_id = EXCLUDED.customer_id,
    order_status = EXCLUDED.order_status,
    order_purchase_timestamp = EXCLUDED.order_purchase_timestamp,
    order_approved_at = EXCLUDED.order_approved_at,
    order_delivered_carrier_date = EXCLUDED.order_delivered_carrier_date,
    order_delivered_customer_date = EXCLUDED.order_delivered_customer_date,
    order_estimated_delivery_date = EXCLUDED.order_estimated_delivery_date,
    row_hash = EXCLUDED.row_hash,
    last_batch_id = EXCLUDED.last_batch_id,
    updated_at = CURRENT_TIMESTAMP
WHERE staging.orders.row_hash IS DISTINCT FROM EXCLUDED.row_hash;

-- ORDER ITEMS
WITH src AS (
    SELECT DISTINCT ON (order_id, order_item_id)
        order_id,
        NULLIF(order_item_id, '')::int AS order_item_id,
        product_id,
        seller_id,
        NULLIF(shipping_limit_date, '')::timestamp AS shipping_limit_date,
        NULLIF(price, '')::numeric(12,2) AS price,
        NULLIF(freight_value, '')::numeric(12,2) AS freight_value,
        row_hash,
        batch_id
    FROM raw.olist_order_items
    WHERE batch_id = {{BATCH_ID}}
    ORDER BY order_id, order_item_id, loaded_at DESC
),
changed AS (
    SELECT
        'order_items' AS table_name,
        src.order_id || '-' || src.order_item_id AS business_key,
        CASE WHEN tgt.order_id IS NULL THEN 'INSERT' ELSE 'UPDATE' END AS operation_type,
        tgt.row_hash AS old_row_hash,
        src.row_hash AS new_row_hash,
        src.batch_id
    FROM src
    LEFT JOIN staging.order_items tgt
        ON src.order_id = tgt.order_id AND src.order_item_id = tgt.order_item_id
    WHERE tgt.order_id IS NULL OR src.row_hash IS DISTINCT FROM tgt.row_hash
)
INSERT INTO staging.cdc_log(table_name, business_key, operation_type, old_row_hash, new_row_hash, batch_id)
SELECT table_name, business_key, operation_type, old_row_hash, new_row_hash, batch_id
FROM changed;

WITH src AS (
    SELECT DISTINCT ON (order_id, order_item_id)
        order_id,
        NULLIF(order_item_id, '')::int AS order_item_id,
        product_id,
        seller_id,
        NULLIF(shipping_limit_date, '')::timestamp AS shipping_limit_date,
        NULLIF(price, '')::numeric(12,2) AS price,
        NULLIF(freight_value, '')::numeric(12,2) AS freight_value,
        row_hash,
        batch_id
    FROM raw.olist_order_items
    WHERE batch_id = {{BATCH_ID}}
    ORDER BY order_id, order_item_id, loaded_at DESC
)
INSERT INTO staging.order_items(
    order_id, order_item_id, product_id, seller_id, shipping_limit_date,
    price, freight_value, row_hash, last_batch_id, updated_at
)
SELECT order_id, order_item_id, product_id, seller_id, shipping_limit_date,
       price, freight_value, row_hash, batch_id, CURRENT_TIMESTAMP
FROM src
ON CONFLICT (order_id, order_item_id) DO UPDATE
SET product_id = EXCLUDED.product_id,
    seller_id = EXCLUDED.seller_id,
    shipping_limit_date = EXCLUDED.shipping_limit_date,
    price = EXCLUDED.price,
    freight_value = EXCLUDED.freight_value,
    row_hash = EXCLUDED.row_hash,
    last_batch_id = EXCLUDED.last_batch_id,
    updated_at = CURRENT_TIMESTAMP
WHERE staging.order_items.row_hash IS DISTINCT FROM EXCLUDED.row_hash;

-- PAYMENTS
WITH src AS (
    SELECT DISTINCT ON (order_id, payment_sequential)
        order_id,
        NULLIF(payment_sequential, '')::int AS payment_sequential,
        LOWER(TRIM(payment_type)) AS payment_type,
        NULLIF(payment_installments, '')::int AS payment_installments,
        NULLIF(payment_value, '')::numeric(12,2) AS payment_value,
        row_hash,
        batch_id
    FROM raw.olist_order_payments
    WHERE batch_id = {{BATCH_ID}}
    ORDER BY order_id, payment_sequential, loaded_at DESC
)
INSERT INTO staging.order_payments(
    order_id, payment_sequential, payment_type, payment_installments, payment_value,
    row_hash, last_batch_id, updated_at
)
SELECT order_id, payment_sequential, payment_type, payment_installments, payment_value,
       row_hash, batch_id, CURRENT_TIMESTAMP
FROM src
ON CONFLICT (order_id, payment_sequential) DO UPDATE
SET payment_type = EXCLUDED.payment_type,
    payment_installments = EXCLUDED.payment_installments,
    payment_value = EXCLUDED.payment_value,
    row_hash = EXCLUDED.row_hash,
    last_batch_id = EXCLUDED.last_batch_id,
    updated_at = CURRENT_TIMESTAMP
WHERE staging.order_payments.row_hash IS DISTINCT FROM EXCLUDED.row_hash;

-- REVIEWS
WITH src AS (
    SELECT DISTINCT ON (review_id)
        review_id,
        order_id,
        NULLIF(review_score, '')::int AS review_score,
        review_comment_title,
        review_comment_message,
        NULLIF(review_creation_date, '')::timestamp AS review_creation_date,
        NULLIF(review_answer_timestamp, '')::timestamp AS review_answer_timestamp,
        row_hash,
        batch_id
    FROM raw.olist_order_reviews
    WHERE batch_id = {{BATCH_ID}}
    ORDER BY review_id, loaded_at DESC
)
INSERT INTO staging.order_reviews(
    review_id, order_id, review_score, review_comment_title, review_comment_message,
    review_creation_date, review_answer_timestamp, row_hash, last_batch_id, updated_at
)
SELECT review_id, order_id, review_score, review_comment_title, review_comment_message,
       review_creation_date, review_answer_timestamp, row_hash, batch_id, CURRENT_TIMESTAMP
FROM src
ON CONFLICT (review_id) DO UPDATE
SET order_id = EXCLUDED.order_id,
    review_score = EXCLUDED.review_score,
    review_comment_title = EXCLUDED.review_comment_title,
    review_comment_message = EXCLUDED.review_comment_message,
    review_creation_date = EXCLUDED.review_creation_date,
    review_answer_timestamp = EXCLUDED.review_answer_timestamp,
    row_hash = EXCLUDED.row_hash,
    last_batch_id = EXCLUDED.last_batch_id,
    updated_at = CURRENT_TIMESTAMP
WHERE staging.order_reviews.row_hash IS DISTINCT FROM EXCLUDED.row_hash;

-- SELLERS
WITH src AS (
    SELECT DISTINCT ON (seller_id)
        seller_id,
        seller_zip_code_prefix,
        LOWER(TRIM(seller_city)) AS seller_city,
        UPPER(TRIM(seller_state)) AS seller_state,
        row_hash,
        batch_id
    FROM raw.olist_sellers
    WHERE batch_id = {{BATCH_ID}}
    ORDER BY seller_id, loaded_at DESC
)
INSERT INTO staging.sellers(
    seller_id, seller_zip_code_prefix, seller_city, seller_state,
    row_hash, last_batch_id, updated_at
)
SELECT seller_id, seller_zip_code_prefix, seller_city, seller_state,
       row_hash, batch_id, CURRENT_TIMESTAMP
FROM src
ON CONFLICT (seller_id) DO UPDATE
SET seller_zip_code_prefix = EXCLUDED.seller_zip_code_prefix,
    seller_city = EXCLUDED.seller_city,
    seller_state = EXCLUDED.seller_state,
    row_hash = EXCLUDED.row_hash,
    last_batch_id = EXCLUDED.last_batch_id,
    updated_at = CURRENT_TIMESTAMP
WHERE staging.sellers.row_hash IS DISTINCT FROM EXCLUDED.row_hash;

-- PRODUCTS
WITH product_price AS (
    SELECT product_id, AVG(NULLIF(price, '')::numeric(12,2)) AS product_price
    FROM raw.olist_order_items
    GROUP BY product_id
),
src AS (
    SELECT DISTINCT ON (p.product_id)
        p.product_id,
        LOWER(TRIM(p.product_category_name)) AS product_category_name,
        COALESCE(t.product_category_name_english, p.product_category_name) AS product_category_name_english,
        NULLIF(p.product_name_lenght, '')::int AS product_name_length,
        NULLIF(p.product_description_lenght, '')::int AS product_description_length,
        NULLIF(p.product_photos_qty, '')::int AS product_photos_qty,
        NULLIF(p.product_weight_g, '')::int AS product_weight_g,
        NULLIF(p.product_length_cm, '')::int AS product_length_cm,
        NULLIF(p.product_height_cm, '')::int AS product_height_cm,
        NULLIF(p.product_width_cm, '')::int AS product_width_cm,
        pp.product_price,
        p.row_hash,
        p.batch_id
    FROM raw.olist_products p
    LEFT JOIN raw.product_category_name_translation t
        ON p.product_category_name = t.product_category_name
    LEFT JOIN product_price pp
        ON p.product_id = pp.product_id
    WHERE p.batch_id = {{BATCH_ID}}
    ORDER BY p.product_id, p.loaded_at DESC
)
INSERT INTO staging.products(
    product_id, product_category_name, product_category_name_english,
    product_name_length, product_description_length, product_photos_qty,
    product_weight_g, product_length_cm, product_height_cm, product_width_cm,
    product_price, row_hash, last_batch_id, updated_at
)
SELECT product_id, product_category_name, product_category_name_english,
       product_name_length, product_description_length, product_photos_qty,
       product_weight_g, product_length_cm, product_height_cm, product_width_cm,
       product_price, row_hash, batch_id, CURRENT_TIMESTAMP
FROM src
ON CONFLICT (product_id) DO UPDATE
SET product_category_name = EXCLUDED.product_category_name,
    product_category_name_english = EXCLUDED.product_category_name_english,
    product_name_length = EXCLUDED.product_name_length,
    product_description_length = EXCLUDED.product_description_length,
    product_photos_qty = EXCLUDED.product_photos_qty,
    product_weight_g = EXCLUDED.product_weight_g,
    product_length_cm = EXCLUDED.product_length_cm,
    product_height_cm = EXCLUDED.product_height_cm,
    product_width_cm = EXCLUDED.product_width_cm,
    product_price = EXCLUDED.product_price,
    row_hash = EXCLUDED.row_hash,
    last_batch_id = EXCLUDED.last_batch_id,
    updated_at = CURRENT_TIMESTAMP
WHERE staging.products.row_hash IS DISTINCT FROM EXCLUDED.row_hash;
