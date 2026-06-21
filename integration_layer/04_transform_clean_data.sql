-- Bước transform đã được tích hợp trong 03_incremental_load.sql:
-- - chuẩn hóa city/state
-- - cast kiểu dữ liệu ngày tháng, numeric
-- - join category tiếng Anh cho product
-- - upsert vào staging current tables
SELECT 'Transform clean data completed in staging tables' AS note;
