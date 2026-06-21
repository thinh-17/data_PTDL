-- SCD Type 2 cho dim_product.

WITH src AS (
    SELECT
        product_id,
        product_category_name_english,
        product_description_length,
        product_price,
        MD5(CONCAT_WS('|',
            product_id,
            product_category_name_english,
            product_description_length::text,
            COALESCE(product_price::text, '')
        )) AS row_hash
    FROM staging.products
),
changed AS (
    SELECT cur.product_key, src.product_id
    FROM src
    JOIN storage.dim_product cur
        ON src.product_id = cur.product_id
       AND cur.is_current = TRUE
    WHERE src.row_hash IS DISTINCT FROM cur.row_hash
)
UPDATE storage.dim_product cur
SET is_current = FALSE,
    effective_to = CURRENT_DATE - INTERVAL '1 day'
FROM changed
WHERE cur.product_key = changed.product_key;

WITH src AS (
    SELECT
        product_id,
        product_category_name_english,
        product_description_length,
        product_price,
        MD5(CONCAT_WS('|',
            product_id,
            product_category_name_english,
            product_description_length::text,
            COALESCE(product_price::text, '')
        )) AS row_hash
    FROM staging.products
),
to_insert AS (
    SELECT
        src.*,
        COALESCE(MAX(old.version), 0) + 1 AS next_version
    FROM src
    LEFT JOIN storage.dim_product old
        ON src.product_id = old.product_id
    LEFT JOIN storage.dim_product cur
        ON src.product_id = cur.product_id
       AND cur.is_current = TRUE
    WHERE cur.product_id IS NULL
       OR src.row_hash IS DISTINCT FROM cur.row_hash
    GROUP BY src.product_id, src.product_category_name_english,
             src.product_description_length, src.product_price, src.row_hash
)
INSERT INTO storage.dim_product(
    product_id, product_category_name_english, product_description_length,
    product_price, version, effective_from, effective_to, is_current, row_hash
)
SELECT
    product_id, product_category_name_english, product_description_length,
    product_price, next_version, CURRENT_DATE, NULL, TRUE, row_hash
FROM to_insert
ON CONFLICT DO NOTHING;
