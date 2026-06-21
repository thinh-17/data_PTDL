CREATE UNIQUE INDEX IF NOT EXISTS ux_dim_customer_current
ON storage.dim_customer(customer_id)
WHERE is_current = TRUE;

CREATE UNIQUE INDEX IF NOT EXISTS ux_dim_seller_current
ON storage.dim_seller(seller_id)
WHERE is_current = TRUE;

CREATE UNIQUE INDEX IF NOT EXISTS ux_dim_product_current
ON storage.dim_product(product_id)
WHERE is_current = TRUE;

CREATE INDEX IF NOT EXISTS ix_fct_order_customer ON storage.fct_order(customer_key);
CREATE INDEX IF NOT EXISTS ix_fct_order_order_detail ON storage.fct_order(order_detail_key);
CREATE INDEX IF NOT EXISTS ix_snapshot_date ON storage.fct_daily_order_snapshot(snapshot_date_key);
