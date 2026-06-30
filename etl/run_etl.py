import argparse
import hashlib
import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ROOT_DIR = Path(__file__).resolve().parents[1]


FILE_TABLE_MAP = {
    "olist_customers_dataset.csv": "olist_customers",
    "olist_geolocation_dataset.csv": "olist_geolocation",
    "olist_order_items_dataset.csv": "olist_order_items",
    "olist_order_payments_dataset.csv": "olist_order_payments",
    "olist_order_reviews_dataset.csv": "olist_order_reviews",
    "olist_orders_dataset.csv": "olist_orders",
    "olist_products_dataset.csv": "olist_products",
    "olist_sellers_dataset.csv": "olist_sellers",
    "product_category_name_translation.csv": "product_category_name_translation",
}


def load_env():
    load_dotenv(ROOT_DIR / ".env")
    return {
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "database": os.getenv("POSTGRES_DB", "olist_dwh"),
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
    }


def get_conn():
    cfg = load_env()
    return psycopg2.connect(
        dbname=cfg["database"],
        user=cfg["user"],
        password=cfg["password"],
        host=cfg["host"],
        port=cfg["port"],
    )


def get_engine():
    cfg = load_env()
    return create_engine(
        f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}@"
        f"{cfg['host']}:{cfg['port']}/{cfg['database']}"
    )


def execute_sql_file(path: Path, batch_id: int | None = None):
    sql = path.read_text(encoding="utf-8")
    if batch_id is not None:
        sql = sql.replace("{{BATCH_ID}}", str(batch_id))

    print(f"Running SQL: {path.relative_to(ROOT_DIR)}")
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_many(paths, batch_id: int | None = None):
    for p in paths:
        execute_sql_file(ROOT_DIR / p, batch_id=batch_id)


def start_batch(batch_name: str, load_type: str) -> int:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO staging.etl_batch(batch_name, load_type, status)
                VALUES (%s, %s, 'RUNNING')
                RETURNING batch_id;
                """,
                (batch_name, load_type),
            )
            batch_id = cur.fetchone()[0]
        conn.commit()
        return batch_id
    finally:
        conn.close()


def finish_batch(batch_id: int, status: str = "SUCCESS"):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE staging.etl_batch
                SET status = %s,
                    finished_at = CURRENT_TIMESTAMP
                WHERE batch_id = %s;
                """,
                (status, batch_id),
            )
        conn.commit()
    finally:
        conn.close()


def row_hash_dataframe(df: pd.DataFrame) -> pd.Series:
    source_cols = [c for c in df.columns if c not in {"source_file", "batch_id", "row_hash"}]

    def make_hash(row):
        values = ["" if pd.isna(row[c]) else str(row[c]) for c in source_cols]
        return hashlib.md5("||".join(values).encode("utf-8")).hexdigest()

    return df.apply(make_hash, axis=1)


def load_csv_folder_to_raw(folder: Path, batch_id: int):
    engine = get_engine()

    csv_files = sorted(folder.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in {folder}")
        return

    for csv_file in csv_files:
        table_name = FILE_TABLE_MAP.get(csv_file.name)
        if table_name is None:
            print(f"Skip unknown file: {csv_file.name}")
            continue

        print(f"Loading {csv_file.name} -> raw.{table_name}")
        df = pd.read_csv(csv_file, dtype=str, keep_default_na=False)
        df["source_file"] = csv_file.name
        df["batch_id"] = batch_id
        df["row_hash"] = row_hash_dataframe(df)

        # append raw data; incremental logic is handled in SQL after this step
        df.to_sql(
            table_name,
            engine,
            schema="raw",
            if_exists="append",
            index=False,
            chunksize=5000,
            method="multi",
        )
        print(f"Loaded {len(df):,} rows into raw.{table_name}")


def get_data_folder(mode: str, batch_name: str | None) -> Path:
    if mode == "full":
        return ROOT_DIR / "data_source" / "raw"

    if not batch_name:
        raise ValueError("Incremental mode requires batch name, for example: batch_002")

    return ROOT_DIR / "data_source" / "incremental" / batch_name


def run_pipeline(mode: str, batch_name: str | None):
    # 1. create schemas + raw/staging tables
    execute_many([
        "etl/00_create_schemas.sql",
        "etl/01_create_raw_tables.sql",
    ])

    # 2. create batch
    actual_batch_name = "full_load" if mode == "full" else batch_name
    batch_id = start_batch(actual_batch_name, mode)
    print(f"Batch ID: {batch_id}")

    try:
        # 3. load CSV to raw
        data_folder = get_data_folder(mode, batch_name)
        load_csv_folder_to_raw(data_folder, batch_id)

        # 4. incremental load raw -> staging
        execute_sql_file(ROOT_DIR / "etl/02_load_data_source.sql", batch_id=batch_id)
        execute_sql_file(ROOT_DIR / "etl/03_incremental_load.sql", batch_id=batch_id)
        execute_sql_file(ROOT_DIR / "etl/04_transform_clean_data.sql", batch_id=batch_id)

        # 5. create star schema
        execute_many([
            "storage/ddl/01_create_dimensions.sql",
            "storage/ddl/02_create_facts.sql",
            "storage/ddl/03_create_indexes.sql",
        ])

        # 6. load dimensions, including SCD
        execute_sql_file(ROOT_DIR / "etl/05_apply_scd.sql", batch_id=batch_id)
        execute_many([
            "storage/dimensions/load_dim_date.sql",
            "storage/dimensions/load_dim_location.sql",
            "storage/dimensions/load_dim_review_score.sql",
            "storage/dimensions/load_dim_customer.sql",
            "storage/dimensions/load_dim_seller.sql",
            "storage/dimensions/load_dim_product.sql",
            "storage/dimensions/load_dim_order_detail.sql",
        ])

        # 7. load facts and snapshots
        execute_many([
            "storage/facts/load_fct_order.sql",
            "storage/facts/load_fct_order_review.sql",
            "storage/facts/load_fct_daily_order_snapshot.sql",
            "storage/facts/load_fct_daily_seller_snapshot.sql",
            "storage/facts/load_fct_daily_product_snapshot.sql",
            "storage/facts/load_fct_customer_behavior_snapshot.sql",
        ])

        # 8. create analysis and ML marts
        execute_many([
            "storage/mart/mart_financial_kpi.sql",
            "storage/mart/mart_order_bad_review_features.sql",
            "storage/mart/mart_customer_cluster_features.sql",
            "storage/mart/mart_seller_cluster_features.sql",
            "storage/mart/mart_late_delivery_features.sql",
        ])

        finish_batch(batch_id, "SUCCESS")
        print("ETL completed successfully.")
    except Exception as exc:
        finish_batch(batch_id, "FAILED")
        print(f"ETL failed: {exc}")
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=["full", "incremental"],
        help="full: load data_source/raw; incremental: load data_source/incremental/<batch_name>",
    )
    parser.add_argument(
        "batch_name",
        nargs="?",
        help="batch folder name for incremental mode, e.g. batch_002",
    )
    args = parser.parse_args()
    run_pipeline(args.mode, args.batch_name)


if __name__ == "__main__":
    main()
