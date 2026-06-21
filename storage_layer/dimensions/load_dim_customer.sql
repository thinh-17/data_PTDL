-- SCD Type 2 cho dim_customer.
-- Nếu customer_id mới -> insert version 1.
-- Nếu customer_id đã có nhưng row_hash thay đổi -> đóng version cũ và insert version mới.

WITH src AS (
    SELECT
        c.customer_id,
        c.customer_unique_id,
        l.location_key AS customer_location_key,
        c.row_hash
    FROM staging.customers c
    LEFT JOIN storage.dim_location l
        ON c.customer_city = l.city AND c.customer_state = l.state
),
changed AS (
    SELECT
        cur.customer_key,
        src.customer_id
    FROM src
    JOIN storage.dim_customer cur
        ON src.customer_id = cur.customer_id
       AND cur.is_current = TRUE
    WHERE src.row_hash IS DISTINCT FROM cur.row_hash
)
UPDATE storage.dim_customer cur
SET is_current = FALSE,
    effective_to = CURRENT_DATE - INTERVAL '1 day'
FROM changed
WHERE cur.customer_key = changed.customer_key;

WITH src AS (
    SELECT
        c.customer_id,
        c.customer_unique_id,
        l.location_key AS customer_location_key,
        c.row_hash
    FROM staging.customers c
    LEFT JOIN storage.dim_location l
        ON c.customer_city = l.city AND c.customer_state = l.state
),
to_insert AS (
    SELECT
        src.*,
        COALESCE(MAX(old.version), 0) + 1 AS next_version
    FROM src
    LEFT JOIN storage.dim_customer old
        ON src.customer_id = old.customer_id
    LEFT JOIN storage.dim_customer cur
        ON src.customer_id = cur.customer_id
       AND cur.is_current = TRUE
    WHERE cur.customer_id IS NULL
       OR src.row_hash IS DISTINCT FROM cur.row_hash
    GROUP BY src.customer_id, src.customer_unique_id, src.customer_location_key, src.row_hash
)
INSERT INTO storage.dim_customer(
    customer_id, customer_unique_id, customer_location_key,
    version, effective_from, effective_to, is_current, row_hash
)
SELECT
    customer_id, customer_unique_id, customer_location_key,
    next_version, CURRENT_DATE, NULL, TRUE, row_hash
FROM to_insert
ON CONFLICT DO NOTHING;
