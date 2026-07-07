-- Dimension tables theo star schema.

CREATE TABLE IF NOT EXISTS storage.dim_date (
    date_key INT PRIMARY KEY,
    full_date DATE NOT NULL,
    day_of_month INT,
    month_num INT,
    month_name TEXT,
    quarter_num INT,
    year_num INT
);

CREATE TABLE IF NOT EXISTS storage.dim_location (
    location_key BIGSERIAL PRIMARY KEY,
    city TEXT,
    state TEXT,
    UNIQUE(city, state)
);

CREATE TABLE IF NOT EXISTS storage.dim_customer (
    customer_key BIGSERIAL PRIMARY KEY,
    customer_id TEXT NOT NULL,
    customer_unique_id TEXT,
    customer_location_key BIGINT REFERENCES storage.dim_location(location_key),
    version INT NOT NULL DEFAULT 1,
    effective_from DATE NOT NULL DEFAULT CURRENT_DATE,
    effective_to DATE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    row_hash TEXT
);

CREATE TABLE IF NOT EXISTS storage.dim_seller (
    seller_key BIGSERIAL PRIMARY KEY,
    seller_id TEXT NOT NULL,
    seller_location_key BIGINT REFERENCES storage.dim_location(location_key),
    version INT NOT NULL DEFAULT 1,
    effective_from DATE NOT NULL DEFAULT CURRENT_DATE,
    effective_to DATE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    row_hash TEXT
);

CREATE TABLE IF NOT EXISTS storage.dim_product (
    product_key BIGSERIAL PRIMARY KEY,
    product_id TEXT NOT NULL,
    product_category_name_english TEXT,
    product_description_length INT,
    product_price NUMERIC(12,2),
    version INT NOT NULL DEFAULT 1,
    effective_from DATE NOT NULL DEFAULT CURRENT_DATE,
    effective_to DATE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    row_hash TEXT
);

CREATE TABLE IF NOT EXISTS storage.dim_order_detail (
    order_detail_key BIGSERIAL PRIMARY KEY,
    order_id TEXT NOT NULL UNIQUE,
    order_status TEXT,
    purchase_date_key INT REFERENCES storage.dim_date(date_key),
    delivered_date_key INT REFERENCES storage.dim_date(date_key),
    customer_key BIGINT REFERENCES storage.dim_customer(customer_key),
    row_hash TEXT
);

CREATE TABLE IF NOT EXISTS storage.dim_review_score (
    review_score_key BIGSERIAL PRIMARY KEY,
    review_score INT UNIQUE,
    score_label TEXT
);


DROP TABLE IF EXISTS storage.dim_category_financial_assumption CASCADE;

CREATE TABLE storage.dim_category_financial_assumption (
    category_financial_key SERIAL PRIMARY KEY,
    product_category_name_english TEXT NOT NULL UNIQUE,
    estimated_cogs_rate NUMERIC(6,4) NOT NULL,
    estimated_tax_rate NUMERIC(6,4) NOT NULL,
    version INT DEFAULT 1,
    is_current BOOLEAN DEFAULT TRUE
);

INSERT INTO storage.dim_category_financial_assumption
(
    product_category_name_english,
    estimated_cogs_rate,
    estimated_tax_rate
)
SELECT
    category_list.product_category_name_english,

    COALESCE(r.estimated_cogs_rate, 0.6500) AS estimated_cogs_rate,
    COALESCE(r.estimated_tax_rate, 0.0800) AS estimated_tax_rate

FROM (
    SELECT DISTINCT
        COALESCE(product_category_name_english) AS product_category_name_english
    FROM storage.dim_product
) category_list
LEFT JOIN raw.category_financial_assumption r
    ON category_list.product_category_name_english = r.product_category_name_english;