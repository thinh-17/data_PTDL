-- Fact tables theo star schema.

CREATE TABLE IF NOT EXISTS storage.fct_order (
    order_fact_key BIGSERIAL PRIMARY KEY,
    order_id TEXT UNIQUE,
    customer_key BIGINT REFERENCES storage.dim_customer(customer_key),
    order_detail_key BIGINT REFERENCES storage.dim_order_detail(order_detail_key),
    waiting_day INT,
    item_count INT,
    order_value NUMERIC(14,2),
    freight_value NUMERIC(14,2),
    payment_value NUMERIC(14,2),
    payment_installments INT
);

CREATE TABLE IF NOT EXISTS storage.fct_order_review (
    order_review_fact_key BIGSERIAL PRIMARY KEY,
    review_id TEXT UNIQUE,
    order_id TEXT,
    customer_key BIGINT REFERENCES storage.dim_customer(customer_key),
    review_score_key BIGINT REFERENCES storage.dim_review_score(review_score_key),
    review_creation_date_key INT REFERENCES storage.dim_date(date_key),
    review_answer_date_key INT REFERENCES storage.dim_date(date_key),
    review_count INT,
    review_score INT,
    has_comment_message BOOLEAN
);

CREATE TABLE IF NOT EXISTS storage.fct_daily_order_snapshot (
    snapshot_date_key INT PRIMARY KEY REFERENCES storage.dim_date(date_key),
    total_orders_created INT,
    total_orders_approved INT,
    total_orders_delivered INT,
    total_orders_cancelled INT,
    total_revenue NUMERIC(14,2)
);

CREATE TABLE IF NOT EXISTS storage.fct_daily_seller_snapshot (
    snapshot_date_key INT REFERENCES storage.dim_date(date_key),
    seller_key BIGINT REFERENCES storage.dim_seller(seller_key),
    orders_created_cnt INT,
    items_sold_cnt INT,
    total_revenue NUMERIC(14,2),
    delivered_orders_cnt INT,
    cancelled_orders_cnt INT,
    avg_review_score NUMERIC(5,2),
    distinct_products_sold INT,
    PRIMARY KEY(snapshot_date_key, seller_key)
);

CREATE TABLE IF NOT EXISTS storage.fct_daily_product_snapshot (
    snapshot_date_key INT REFERENCES storage.dim_date(date_key),
    product_key BIGINT REFERENCES storage.dim_product(product_key),
    items_sold_cnt INT,
    total_revenue NUMERIC(14,2),
    avg_review_score NUMERIC(5,2),
    PRIMARY KEY(snapshot_date_key, product_key)
);

CREATE TABLE IF NOT EXISTS storage.fct_customer_behavior_snapshot (
    customer_key BIGINT PRIMARY KEY REFERENCES storage.dim_customer(customer_key),
    avg_score_review NUMERIC(5,2),
    total_spend NUMERIC(14,2),
    order_cnt INT,
    order_cancelled_cnt INT,
    avg_day_return_to_buy NUMERIC(10,2)
);


ALTER TABLE storage.fct_daily_product_snapshot
ADD COLUMN IF NOT EXISTS estimated_cogs NUMERIC(18,2),
ADD COLUMN IF NOT EXISTS estimated_tax NUMERIC(18,2),
ADD COLUMN IF NOT EXISTS gross_profit NUMERIC(18,2),
ADD COLUMN IF NOT EXISTS gross_margin NUMERIC(10,4),
ADD COLUMN IF NOT EXISTS net_revenue_after_tax NUMERIC(18,2);
UPDATE storage.fct_daily_product_snapshot fp
SET
    estimated_cogs = COALESCE(fp.total_revenue, 0) * COALESCE(a.estimated_cogs_rate, 0.7000),

    estimated_tax = COALESCE(fp.total_revenue, 0) * COALESCE(a.estimated_tax_rate, 0.0800),

    gross_profit = COALESCE(fp.total_revenue, 0)
                   - COALESCE(fp.total_revenue, 0) * COALESCE(a.estimated_cogs_rate, 0.7000),

    gross_margin = (
        COALESCE(fp.total_revenue, 0)
        - COALESCE(fp.total_revenue, 0) * COALESCE(a.estimated_cogs_rate, 0.7000)
    ) / NULLIF(COALESCE(fp.total_revenue, 0), 0) * 100,

    net_revenue_after_tax = COALESCE(fp.total_revenue, 0)
                            - COALESCE(fp.total_revenue, 0) * COALESCE(a.estimated_tax_rate, 0.0800)

FROM storage.dim_product dp
LEFT JOIN storage.dim_category_financial_assumption a
    ON COALESCE(dp.product_category_name_english) = a.product_category_name_english
WHERE fp.product_key = dp.product_key;