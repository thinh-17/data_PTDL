-- SCD Type 1: location chỉ cần ghi đè/insert giá trị hiện tại.

INSERT INTO storage.dim_location(city, state)
SELECT DISTINCT customer_city, customer_state
FROM staging.customers
WHERE customer_city IS NOT NULL AND customer_state IS NOT NULL
ON CONFLICT (city, state) DO NOTHING;

INSERT INTO storage.dim_location(city, state)
SELECT DISTINCT seller_city, seller_state
FROM staging.sellers
WHERE seller_city IS NOT NULL AND seller_state IS NOT NULL
ON CONFLICT (city, state) DO NOTHING;
