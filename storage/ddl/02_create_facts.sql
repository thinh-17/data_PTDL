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
