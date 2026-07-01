# Olist Data Warehouse

## 1. Cấu trúc chính

```text
olist-data-warehouse/
├── data_source/
│   ├── raw/                  # dữ liệu gốc Olist
│   └── incremental/          # dữ liệu mô phỏng load tăng dần
├── etl/                      # load raw, incremental load, transform, SCD
├── storage/                  # star schema: dimension, fact, mart
├── analysis/                 # query phân tích KPI tài chính vận hành
└── ml/                       # classification và clustering
```

## 2. Cách chạy

### Bước 1: bật PostgreSQL bằng Docker

```bash
docker compose up -d
```

### Bước 2: cài thư viện Python

```bash
pip install -r requirements.txt
```

### Bước 3: chạy ETL full load

```bash
python integration_layer/run_etl.py full
```

Sau bước này, database sẽ có 3 schema:

```text
raw      : dữ liệu gốc đã load từ CSV
staging  : dữ liệu đã làm sạch, chuẩn hóa, phát hiện thay đổi
storage  : star schema, fact, mart dùng để phân tích và ML
```

### Bước 4: kiểm tra bảng trong PostgreSQL

```sql
SELECT COUNT(*) FROM storage.fct_order;
SELECT COUNT(*) FROM storage.fct_order_review;
SELECT * FROM storage.mart_financial_kpi LIMIT 10;
```

### Bước 5: chạy thử incremental load

Batch `batch_002` có dữ liệu mô phỏng thay đổi location của customer để chứng minh SCD Type 2.

```bash
python etl/run_etl.py incremental batch_002
```

Batch `batch_003` có dữ liệu mô phỏng cập nhật trạng thái đơn hàng.

```bash
python etl/run_etl.py incremental batch_003
```

## 3. Slowly Changing Dimension

Dự án áp dụng SCD như sau:

| Dimension | Loại SCD | Ý nghĩa |
|---|---:|---|
| dim_location | Type 1 | city/state sửa thì ghi đè |
| dim_order_detail | Type 1 | order_status cập nhật trạng thái mới |
| dim_customer | Type 2 | lưu lịch sử khi khách hàng đổi location |
| dim_seller | Type 2 | lưu lịch sử khi seller đổi location |
| dim_product | Type 2 | lưu lịch sử khi product đổi category/mô tả/giá tham chiếu |

Các bảng Type 2 có cột:

```text
effective_from, effective_to, is_current, version, row_hash
```

## 4. Incremental Load

Mỗi dòng dữ liệu khi load vào raw có thêm:

```text
batch_id, source_file, loaded_at, row_hash
```

ETL chỉ cập nhật vào staging khi:

```text
- business key chưa tồn tại -> INSERT
- business key đã tồn tại nhưng row_hash khác -> UPDATE
```

Kết quả detect change được ghi vào:

```text
staging.cdc_log
```

## 5. Analysis

Các query trong thư mục `analysis/` lấy dữ liệu từ storage/mart:

```text
financial_kpi_analysis.sql
revenue_growth_analysis.sql
seller_analysis.sql
product_analysis.sql
customer_analysis.sql
```

## 6. Machine Learning

ML lấy feature trực tiếp từ các mart trong storage:

```text
storage.mart_order_bad_review_features
storage.mart_customer_cluster_features
storage.mart_seller_cluster_features
```

Chạy:

```bash
python ml/classification_bad_review.py
python ml/clustering_customer.py
python ml/clustering_seller.py
```

Kết quả lưu trong:

```text
ml/outputs/
```
