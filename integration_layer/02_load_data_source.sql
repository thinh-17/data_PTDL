-- File này mô tả bước load data source.
-- Việc load CSV được thực hiện trong etl/run_etl.py bằng pandas + SQLAlchemy
-- để chạy được trên Windows/macOS/Linux mà không phụ thuộc đường dẫn COPY của PostgreSQL.

SELECT 'CSV files are loaded by integration_layer/run_etl.py into raw schema' AS note;
