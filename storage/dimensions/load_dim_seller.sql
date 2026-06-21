-- SCD Type 2 cho dim_seller.

WITH src AS (
    SELECT
        s.seller_id,
        l.location_key AS seller_location_key,
        s.row_hash
    FROM staging.sellers s
    LEFT JOIN storage.dim_location l
        ON s.seller_city = l.city AND s.seller_state = l.state
),
changed AS (
    SELECT cur.seller_key, src.seller_id
    FROM src
    JOIN storage.dim_seller cur
        ON src.seller_id = cur.seller_id
       AND cur.is_current = TRUE
    WHERE src.row_hash IS DISTINCT FROM cur.row_hash
)
UPDATE storage.dim_seller cur
SET is_current = FALSE,
    effective_to = CURRENT_DATE - INTERVAL '1 day'
FROM changed
WHERE cur.seller_key = changed.seller_key;

WITH src AS (
    SELECT
        s.seller_id,
        l.location_key AS seller_location_key,
        s.row_hash
    FROM staging.sellers s
    LEFT JOIN storage.dim_location l
        ON s.seller_city = l.city AND s.seller_state = l.state
),
to_insert AS (
    SELECT
        src.*,
        COALESCE(MAX(old.version), 0) + 1 AS next_version
    FROM src
    LEFT JOIN storage.dim_seller old
        ON src.seller_id = old.seller_id
    LEFT JOIN storage.dim_seller cur
        ON src.seller_id = cur.seller_id
       AND cur.is_current = TRUE
    WHERE cur.seller_id IS NULL
       OR src.row_hash IS DISTINCT FROM cur.row_hash
    GROUP BY src.seller_id, src.seller_location_key, src.row_hash
)
INSERT INTO storage.dim_seller(
    seller_id, seller_location_key, version, effective_from, effective_to, is_current, row_hash
)
SELECT seller_id, seller_location_key, next_version, CURRENT_DATE, NULL, TRUE, row_hash
FROM to_insert
ON CONFLICT DO NOTHING;
