-- SCD được áp dụng khi load dimension trong thư mục storage/dimensions:
-- - load_dim_customer.sql  : SCD Type 2
-- - load_dim_seller.sql    : SCD Type 2
-- - load_dim_product.sql   : SCD Type 2
-- - load_dim_location.sql  : SCD Type 1
-- - load_dim_order_detail.sql : SCD Type 1
SELECT 'SCD scripts are executed in storage_layer/dimensions' AS note;
