import os
from pathlib import Path
from typing import Optional, Sequence

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Olist Intelligence Dashboard",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    /* Ẩn header mặc định của Streamlit */
    [data-testid="stHeader"] {
        display: none;
    }

    [data-testid="stToolbar"] {
        display: none;
    }

    [data-testid="stDecoration"] {
        display: none;
    }

    [data-testid="stStatusWidget"] {
        display: none;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    /* Đẩy nội dung lên đúng vị trí sau khi ẩn header */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }

    /* Tab không bị dính sát mép trên */
    .stTabs [data-baseweb="tab-list"] {
        margin-top: 0.5rem;
        gap: 1.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
if not (ROOT_DIR / ".env").exists():
    ROOT_DIR = Path.cwd()


# =========================
# STYLE
# =========================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {font-family: 'Manrope', sans-serif;}
    .stApp {
        background: radial-gradient(circle at 15% 0,#261b4c66 0,transparent 27%), #080a12;
        color: #f6f7fb;
    }
    section[data-testid="stSidebar"] {
        background: #090b13;
        border-right: 1px solid #23283a;
    }
    .main-title {
        font-size: 30px;
        font-weight: 800;
        letter-spacing: -0.05em;
        margin-bottom: 2px;
    }
    .sub-title {
        color: #8e96ab;
        font-size: 13px;
        margin-bottom: 18px;
    }
    .kpi-card {
        min-height: 118px;
        padding: 18px 18px;
        border-radius: 16px;
        background: linear-gradient(145deg,#171a28,#10131e);
        border: 1px solid #23283a;
        box-shadow: 0 8px 26px rgba(0,0,0,.25);
    }
    .kpi-label {
        color: #8c94aa;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .09em;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.055em;
        margin-top: 10px;
        color: #f6f7fb;
    }
    .kpi-note {
        font-size: 11px;
        color: #7f879e;
        margin-top: 4px;
    }
    .insight {
        border: 1px solid #503ca0;
        background: linear-gradient(90deg,#2b1f58aa,#131622);
        padding: 13px 16px;
        border-radius: 14px;
        font-size: 13px;
        color: #c9bfff;
        margin: 8px 0 18px 0;
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg,#171a28,#10131e);
        border: 1px solid #23283a;
        padding: 16px;
        border-radius: 16px;
    }
    div[data-testid="stMetricLabel"] {color: #8c94aa;}
    div[data-testid="stMetricValue"] {color: #f6f7fb; font-weight: 800;}
    .block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1600px;}
    h1, h2, h3 {letter-spacing: -0.03em;}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# DB CONNECTION
# =========================
@st.cache_resource
def get_engine():
    load_dotenv(ROOT_DIR / ".env")

    user = os.getenv("POSTGRES_USER", "olist_user")
    password = os.getenv("POSTGRES_PASSWORD", "olist_pass")
    db = os.getenv("POSTGRES_DB", "olist_db")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")

    return create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}",
        pool_pre_ping=True,
    )


@st.cache_data(ttl=600, show_spinner=False)
def read_sql(sql: str, params: Optional[dict] = None) -> pd.DataFrame:
    engine = get_engine()
    return pd.read_sql(text(sql), engine, params=params)


def read_sql_safe(sql: str, params: Optional[dict] = None) -> pd.DataFrame:
    try:
        return read_sql(sql, params=params)
    except Exception as exc:
        st.warning(f"Không đọc được dữ liệu từ PostgreSQL: {exc}")
        return pd.DataFrame()


def table_exists(schema: str, table: str) -> bool:
    sql = """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = :schema
              AND table_name = :table
        ) AS exists_flag
    """
    try:
        df = read_sql(sql, {"schema": schema, "table": table})
        return bool(df.loc[0, "exists_flag"])
    except Exception:
        return False


# =========================
# FORMAT HELPERS
# =========================
def money(value: float) -> str:
    if pd.isna(value):
        return "R$0"
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"R${value/1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"R${value/1_000:.1f}K"
    return f"R${value:,.0f}"


def pct(value: float) -> str:
    if pd.isna(value):
        return "0.00%"
    return f"{float(value):.2f}%"


def safe_sum(df: pd.DataFrame, col: str) -> float:
    return float(df[col].sum()) if not df.empty and col in df.columns else 0.0


def safe_mean(df: pd.DataFrame, col: str) -> float:
    return float(df[col].mean()) if not df.empty and col in df.columns else 0.0


# =========================
# DATA QUERIES
# =========================
def seller_risk_level(row):
    review = row.get("review", row.get("avg_review_score", 5))
    cancel = row.get("cancel_rate", 0)
    share = row.get("share", 0)

    review = 5 if pd.isna(review) else float(review)
    cancel = 0 if pd.isna(cancel) else float(cancel)
    share = 0 if pd.isna(share) else float(share)

    # Lưu ý: cancel_rate trong SQL đã là phần trăm rồi,
    # ví dụ 0.6 nghĩa là 0.6%, KHÔNG nhân thêm 100.

    if review < 3.5 or cancel >= 3 or (share >= 1 and review < 4):
        return "High"

    if review < 4 or cancel >= 1.5:
        return "Medium"

    return "Low"

def get_monthly_kpi() -> pd.DataFrame:
    """Monthly KPI from daily snapshot. Fallback to fct_order if snapshot is unavailable."""
    if table_exists("storage", "fct_daily_order_snapshot"):
        sql = """
            SELECT
                date_trunc('month', d.full_date)::date AS month_date,
                to_char(date_trunc('month', d.full_date), 'Mon YYYY') AS month_label,
                SUM(COALESCE(s.total_revenue, 0))::numeric AS revenue,
                SUM(COALESCE(s.total_orders_created, 0))::numeric AS orders,
                SUM(COALESCE(s.total_orders_delivered, 0))::numeric AS delivered_orders,
                SUM(COALESCE(s.total_orders_cancelled, 0))::numeric AS cancelled_orders
            FROM storage.fct_daily_order_snapshot s
            JOIN storage.dim_date d
              ON s.snapshot_date_key = d.date_key
            GROUP BY 1, 2
            ORDER BY 1
        """
        df = read_sql_safe(sql)
    else:
        sql = """
            SELECT
                date_trunc('month', d.full_date)::date AS month_date,
                to_char(date_trunc('month', d.full_date), 'Mon YYYY') AS month_label,
                SUM(COALESCE(f.order_value, 0))::numeric AS revenue,
                COUNT(DISTINCT f.order_id)::numeric AS orders,
                SUM(CASE WHEN od.order_status = 'delivered' THEN 1 ELSE 0 END)::numeric AS delivered_orders,
                SUM(CASE WHEN od.order_status = 'cancelled' THEN 1 ELSE 0 END)::numeric AS cancelled_orders
            FROM storage.fct_order f
            JOIN storage.dim_order_detail od
              ON f.order_detail_key = od.order_detail_key
            JOIN storage.dim_date d
              ON od.purchase_date_key = d.date_key
            GROUP BY 1, 2
            ORDER BY 1
        """
        df = read_sql_safe(sql)

    if not df.empty:
        df["aov"] = df["revenue"] / df["orders"].replace(0, pd.NA)
        df["cancellation_rate"] = df["cancelled_orders"] * 100 / df["orders"].replace(0, pd.NA)
        df["delivery_rate"] = df["delivered_orders"] * 100 / df["orders"].replace(0, pd.NA)
        df["growth_rate"] = df["revenue"].pct_change() * 100
    return df


def get_order_status() -> pd.DataFrame:
    sql = """
        SELECT
            COALESCE(od.order_status, 'unknown') AS order_status,
            COUNT(DISTINCT f.order_id)::numeric AS order_count,
            SUM(COALESCE(f.order_value, 0))::numeric AS revenue
        FROM storage.fct_order f
        JOIN storage.dim_order_detail od
          ON f.order_detail_key = od.order_detail_key
        GROUP BY 1
        ORDER BY order_count DESC
    """
    return read_sql_safe(sql)


def get_freight_monthly() -> pd.DataFrame:
    """Read monthly freight KPI from mart_financial_kpi and normalize column names."""
    if table_exists("storage", "mart_financial_kpi"):
        sql = """
            SELECT *
            FROM storage.mart_financial_kpi
            ORDER BY 1
        """
        df = read_sql_safe(sql)

        for c in list(df.columns):
            lc = c.lower()
            if lc in ["month_date", "month", "year_month", "full_date"]:
                df = df.rename(columns={c: "month_date"})
            elif lc in ["freight_ratio", "freight_gmv_ratio", "freight_to_revenue_ratio"]:
                df = df.rename(columns={c: "freight_ratio"})
            elif lc in ["total_revenue", "revenue", "gmv"]:
                df = df.rename(columns={c: "revenue"})
            elif lc in ["total_freight", "freight_value"]:
                df = df.rename(columns={c: "freight_value"})

        if "month_date" not in df.columns and {"year_num", "month_num"}.issubset(df.columns):
            df["month_date"] = pd.to_datetime(
                dict(
                    year=df["year_num"].astype(int),
                    month=df["month_num"].astype(int),
                    day=1,
                )
            )

        if "freight_ratio" not in df.columns and {"freight_value", "revenue"}.issubset(df.columns):
            df["freight_ratio"] = df["freight_value"] * 100 / df["revenue"].replace(0, pd.NA)

        if {"month_date", "freight_ratio"}.issubset(df.columns):
            df = df.sort_values("month_date")
            return df

    return pd.DataFrame()

def get_seller_top(limit: int = 10) -> pd.DataFrame:
    limit = int(limit)

    sql = f"""
        WITH seller_perf AS (
            SELECT
                ds.seller_id,
                SUM(COALESCE(fs.total_revenue, 0)) AS gmv,
                SUM(COALESCE(fs.orders_created_cnt, 0)) AS order_cnt,
                SUM(COALESCE(fs.items_sold_cnt, 0)) AS items_sold,
                SUM(COALESCE(fs.cancelled_orders_cnt, 0)) AS cancelled_cnt,
                AVG(NULLIF(fs.avg_review_score, 0)) AS review
            FROM storage.fct_daily_seller_snapshot fs
            JOIN storage.dim_seller ds
                ON fs.seller_key = ds.seller_key
            GROUP BY ds.seller_id
        ),
        total AS (
            SELECT SUM(gmv) AS total_gmv
            FROM seller_perf
        )
        SELECT
            seller_id AS seller,
            gmv,
            order_cnt,
            items_sold,
            cancelled_cnt,
            gmv * 100.0 / NULLIF(total.total_gmv, 0) AS share,
            cancelled_cnt * 100.0 / NULLIF(order_cnt, 0) AS cancel_rate,
            review
        FROM seller_perf, total
        ORDER BY gmv DESC
        LIMIT {limit};
    """

    df = read_sql_safe(sql)

    if not df.empty:
        df["gmv"] = df["gmv"].fillna(0)
        df["order_cnt"] = df["order_cnt"].fillna(0)
        df["items_sold"] = df["items_sold"].fillna(0)
        df["cancelled_cnt"] = df["cancelled_cnt"].fillna(0)
        df["share"] = df["share"].fillna(0)
        df["cancel_rate"] = df["cancel_rate"].fillna(0)
        df["review"] = df["review"].fillna(0)

        # Cột dùng cho biểu đồ và bảng cũ
        df["revenue"] = df["gmv"]
        df["seller_id"] = df["seller"]
        df["orders_count"] = df["order_cnt"]
        df["avg_review_score"] = df["review"]

        # Cột hiển thị
        df["seller_short"] = df["seller"].astype(str).str.slice(0, 8) + "..."

        # Risk
        df["risk"] = df.apply(seller_risk_level, axis=1)

        total_top_gmv = safe_sum(df, "gmv")
        df["share_in_top"] = df["gmv"] * 100 / total_top_gmv if total_top_gmv else 0

    return df

def render_seller_leaderboard(df: pd.DataFrame):
    if df.empty:
        st.info("Chưa có dữ liệu seller leaderboard.")
        return

    rows = ""

    for i, row in df.reset_index(drop=True).iterrows():
        seller = row.get("seller_short", row.get("seller", row.get("seller_id", "")))
        gmv = row.get("gmv", row.get("revenue", 0))
        share = row.get("share", 0)
        cancel_rate = row.get("cancel_rate", 0)
        review = row.get("review", row.get("avg_review_score", 0))
        risk = row.get("risk", "Low")

        gmv = 0 if pd.isna(gmv) else float(gmv)
        share = 0 if pd.isna(share) else float(share)
        cancel_rate = 0 if pd.isna(cancel_rate) else float(cancel_rate)
        review = 0 if pd.isna(review) else float(review)

        risk_class = {
            "Low": "risk-low",
            "Medium": "risk-medium",
            "High": "risk-high",
        }.get(str(risk), "risk-low")

        rows += f"""
        <tr>
            <td class="rank">{i + 1:02d}</td>
            <td>{seller}</td>
            <td class="money">{money(gmv)}</td>
            <td>{share:.2f}%</td>
            <td>{cancel_rate:.1f}%</td>
            <td>{review:.1f}</td>
            <td><span class="risk-badge {risk_class}">{risk}</span></td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            background: transparent;
            color: #dbe2f1;
            font-family: Manrope, Arial, sans-serif;
        }}

        .seller-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            background: transparent;
        }}

        .seller-table th {{
            text-align: left;
            color: #7f879e;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            padding: 12px 10px;
            border-bottom: 1px solid #23283a;
        }}

        .seller-table td {{
            padding: 13px 10px;
            border-bottom: 1px solid #1d2130;
            color: #dbe2f1;
        }}

        .seller-table tr:last-child td {{
            border-bottom: none;
        }}

        .rank {{
            color: #7f879e !important;
        }}

        .money {{
            color: #a98bff !important;
            font-weight: 800;
        }}

        .risk-badge {{
            padding: 5px 12px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 800;
            display: inline-block;
        }}

        .risk-low {{
            background: #16352f;
            color: #55e7c8;
        }}

        .risk-medium {{
            background: #3a2c17;
            color: #ffd174;
        }}

        .risk-high {{
            background: #401f29;
            color: #ff8da0;
        }}
    </style>
    </head>

    <body>
        <table class="seller-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Seller</th>
                    <th>GMV</th>
                    <th>Share</th>
                    <th>Cancel</th>
                    <th>Review</th>
                    <th>Risk</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </body>
    </html>
    """

    table_height = 70 + len(df) * 48
    components.html(html, height=table_height, scrolling=False)

def render_sales_velocity(df: pd.DataFrame):
    if df.empty:
        st.info("Chưa có dữ liệu sales velocity.")
        return

    view = df.copy().head(8)

    max_units = view["items_sold"].max()
    if pd.isna(max_units) or max_units == 0:
        max_units = 1

    rows = ""

    for _, row in view.iterrows():
        category = str(row.get("category", "unknown")).replace("_", " ")
        units = 0 if pd.isna(row.get("items_sold", 0)) else int(row.get("items_sold", 0))
        width = units * 100 / max_units

        rows += f"""
        <tr>
            <td>{category}</td>
            <td class="money">{units:,}</td>
            <td>
                <div class="progress">
                    <div class="progress-fill" style="width:{width:.1f}%"></div>
                </div>
            </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            background: transparent;
            font-family: Manrope, Arial, sans-serif;
            color: #dbe2f1;
        }}

        .velocity-card {{
            width: 100%;
            background: transparent;
            color: #dbe2f1;
        }}

        .velocity-title {{
            font-size: 18px;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 6px;
        }}

        .velocity-subtitle {{
            color: #7f879e;
            font-size: 12px;
            margin-bottom: 22px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}

        th {{
            text-align: left;
            color: #7f879e;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            padding: 12px 10px;
            border-bottom: 1px solid #23283a;
        }}

        td {{
            padding: 14px 10px;
            border-bottom: 1px solid #1d2130;
            color: #dbe2f1;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        .money {{
            color: #b9a6ff;
            font-weight: 800;
        }}

        .progress {{
            width: 100%;
            height: 7px;
            background: #202536;
            border-radius: 999px;
            overflow: hidden;
        }}

        .progress-fill {{
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #9677ff, #c2b2ff);
        }}
    </style>
    </head>

    <body>
        <div class="velocity-card">
            <div class="velocity-title">Sales velocity</div>
            <div class="velocity-subtitle">Items sold by top category</div>

            <table>
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Units</th>
                        <th>Relative velocity</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    components.html(html, height=460, scrolling=False)

def get_seller_total_revenue() -> float:
    sql = "SELECT SUM(COALESCE(total_revenue, 0))::numeric AS revenue FROM storage.fct_daily_seller_snapshot"
    df = read_sql_safe(sql)
    return float(df.loc[0, "revenue"]) if not df.empty else 0.0


def get_category_top(limit: int = 10) -> pd.DataFrame:
    sql = """
        SELECT
            COALESCE(dp.product_category_name_english, 'unknown') AS category,
            SUM(COALESCE(fp.total_revenue, 0))::numeric AS revenue,
            SUM(COALESCE(fp.items_sold_cnt, 0))::numeric AS items_sold,
            AVG(NULLIF(fp.avg_review_score, 0))::numeric AS avg_review_score
        FROM storage.fct_daily_product_snapshot fp
        LEFT JOIN storage.dim_product dp
          ON fp.product_key = dp.product_key
        GROUP BY 1
        ORDER BY revenue DESC
        LIMIT :limit
    """
    df = read_sql_safe(sql, {"limit": limit})
    if not df.empty:
        df["aov_proxy"] = df["revenue"] / df["items_sold"].replace(0, pd.NA)
    return df


def get_customer_features() -> pd.DataFrame:
    if table_exists("storage", "mart_customer_cluster_features"):
        sql = "SELECT * FROM storage.mart_customer_cluster_features"
    else:
        sql = """
            SELECT
                c.customer_key,
                COALESCE(c.total_spend, 0)::numeric AS total_spend,
                COALESCE(c.order_cnt, 0)::numeric AS order_cnt,
                CASE WHEN COALESCE(c.order_cnt, 0) > 0
                     THEN COALESCE(c.total_spend, 0) / c.order_cnt
                     ELSE 0 END::numeric AS avg_order_value,
                COALESCE(c.avg_score_review, 0)::numeric AS avg_review_score,
                COALESCE(c.order_cancelled_cnt, 0)::numeric AS cancelled_order_cnt,
                COALESCE(c.avg_day_return_to_buy, 0)::numeric AS avg_day_return_to_buy
            FROM storage.fct_customer_behavior_snapshot c
        """
    return read_sql_safe(sql)


def add_customer_cluster(df: pd.DataFrame, n_clusters: int = 4) -> pd.DataFrame:
    if df.empty:
        return df
    if "cluster" in df.columns:
        return df
    if "customer_cluster" in df.columns:
        return df.rename(columns={"customer_cluster": "cluster"})

    from sklearn.cluster import KMeans
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    candidate_features = [
        "total_spend",
        "order_cnt",
        "avg_order_value",
        "avg_review_score",
        "cancelled_order_cnt",
        "avg_day_return_to_buy",
    ]
    features = [c for c in candidate_features if c in df.columns]
    if len(features) < 2 or len(df) < n_clusters:
        df["cluster"] = 0
        return df

    X = df[features]
    pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("kmeans", KMeans(n_clusters=n_clusters, random_state=42, n_init=10)),
        ]
    )
    df = df.copy()
    df["cluster"] = pipe.fit_predict(X)
    return df


def get_review_distribution() -> pd.DataFrame:
    sql = """
        SELECT
            review_score::int AS review_score,
            COUNT(*)::numeric AS review_count
        FROM storage.fct_order_review
        GROUP BY 1
        ORDER BY 1
    """
    return read_sql_safe(sql)


def get_bad_review_rate() -> float:
    sql = """
        SELECT
            SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END)::numeric * 100
            / NULLIF(COUNT(*), 0) AS bad_review_rate
        FROM storage.fct_order_review
    """
    df = read_sql_safe(sql)
    return float(df.loc[0, "bad_review_rate"]) if not df.empty and pd.notna(df.loc[0, "bad_review_rate"]) else 0.0


def get_model_metrics() -> pd.DataFrame:
    """Optional table. Create it if you want model metrics to appear in the dashboard."""
    if not table_exists("storage", "ml_model_metrics"):
        return pd.DataFrame()
    sql = """
        SELECT model_name, metric_name, metric_value
        FROM storage.ml_model_metrics
        ORDER BY model_name, metric_name
    """
    return read_sql_safe(sql)


# =========================
# UI HELPERS
# =========================
def header(title: str, subtitle: str):
    st.markdown(f"<div class='main-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-title'>{subtitle}</div>", unsafe_allow_html=True)


def kpi_card(label: str, value: str, note: str = ""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(message: str):
    st.info(message)

def prepare_customer_cluster_summary(customer_df: pd.DataFrame) -> pd.DataFrame:
    df = customer_df.copy()

    if "avg_review_score" not in df.columns and "avg_score_review" in df.columns:
        df["avg_review_score"] = df["avg_score_review"]

    if "cancelled_order_cnt" not in df.columns and "order_cancelled_cnt" in df.columns:
        df["cancelled_order_cnt"] = df["order_cancelled_cnt"]

    if "avg_order_value" not in df.columns and {"total_spend", "order_cnt"}.issubset(df.columns):
        df["avg_order_value"] = df["total_spend"] / df["order_cnt"].replace(0, pd.NA)

    for col in [
        "total_spend",
        "order_cnt",
        "avg_order_value",
        "avg_review_score",
        "cancelled_order_cnt",
        "avg_day_return_to_buy",
    ]:
        if col not in df.columns:
            df[col] = 0

    summary = (
        df.groupby("cluster", as_index=False)
        .agg(
            total_spend=("total_spend", "mean"),
            order_cnt=("order_cnt", "mean"),
            avg_order_value=("avg_order_value", "mean"),
            avg_review_score=("avg_review_score", "mean"),
            cancelled_order_cnt=("cancelled_order_cnt", "mean"),
            avg_day_return_to_buy=("avg_day_return_to_buy", "mean"),
            customer_count=("cluster", "count"),
        )
    )

    summary["segment"] = "Cluster " + summary["cluster"].astype(str)

    if len(summary) >= 4:
        used = set()

        premium_idx = summary["total_spend"].idxmax()
        summary.loc[premium_idx, "segment"] = "Premium"
        used.add(premium_idx)

        remain = summary.drop(index=list(used))
        loyal_idx = remain["order_cnt"].idxmax()
        summary.loc[loyal_idx, "segment"] = "Loyal"
        used.add(loyal_idx)

        remain = summary.drop(index=list(used))
        risk_score = (
            remain["cancelled_order_cnt"].fillna(0)
            + (5 - remain["avg_review_score"].fillna(5))
        )
        atrisk_idx = risk_score.idxmax()
        summary.loc[atrisk_idx, "segment"] = "At-risk"
        used.add(atrisk_idx)

        remain = summary.drop(index=list(used))
        if not remain.empty:
            onetime_idx = remain["order_cnt"].idxmin()
            summary.loc[onetime_idx, "segment"] = "One-time"

    order = ["One-time", "Loyal", "Premium", "At-risk"]
    summary["segment_order"] = summary["segment"].apply(
        lambda x: order.index(x) if x in order else 99
    )

    return summary.sort_values("segment_order")


def render_customer_segment_cards(summary: pd.DataFrame):
    if summary.empty:
        return

    color_map = {
        "Premium": "#9677ff",
        "Loyal": "#34d9c5",
        "One-time": "#ffbd59",
        "At-risk": "#ff6b81",
    }

    order = ["Premium", "Loyal", "One-time", "At-risk"]
    view = summary.copy()
    view["segment_order"] = view["segment"].apply(lambda x: order.index(x) if x in order else 99)
    view = view.sort_values("segment_order").head(4)

    cols = st.columns(4)

    for col, (_, row) in zip(cols, view.iterrows()):
        segment = row["segment"]
        color = color_map.get(segment, "#9677ff")

        if segment == "Premium":
            desc = f"Avg spend {money(row['total_spend'])} · high AOV"
        elif segment == "Loyal":
            desc = f"{row['order_cnt']:.2f} orders · {row['avg_day_return_to_buy']:.0f} days return"
        elif segment == "One-time":
            desc = f"{row['order_cnt']:.2f} orders · {money(row['total_spend'])} spend"
        elif segment == "At-risk":
            desc = f"Review {row['avg_review_score']:.1f}★ · cancellations"
        else:
            desc = f"{int(row['customer_count']):,} customers"

        with col:
            st.markdown(
                f"""
                <div style="
                    padding: 20px;
                    border: 1px solid #23283a;
                    border-top: 2px solid {color};
                    border-radius: 16px;
                    background: #121521;
                    min-height: 96px;
                ">
                    <div style="font-size:18px;font-weight:800;color:#fff;margin-bottom:10px;">
                        {segment}
                    </div>
                    <div style="font-size:12px;color:#8e96ab;">
                        {desc}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# =========================
# LOAD DATA
# =========================
monthly = get_monthly_kpi()
status_df = get_order_status()
freight_df = get_freight_monthly()
seller_top = get_seller_top(10)
seller_total_revenue = get_seller_total_revenue()
category_top = get_category_top(10)
customer_df = add_customer_cluster(get_customer_features())
review_df = get_review_distribution()
bad_review_rate = get_bad_review_rate()
model_metrics = get_model_metrics()


# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.markdown("# ◈ Olist Intelligence")
st.sidebar.caption("Commerce command center · đọc trực tiếp từ PostgreSQL")

if not monthly.empty:
    min_month = pd.to_datetime(monthly["month_date"]).min().date()
    max_month = pd.to_datetime(monthly["month_date"]).max().date()
    selected_range = st.sidebar.date_input(
        "Khoảng thời gian",
        value=(min_month, max_month),
        min_value=min_month,
        max_value=max_month,
    )
    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start_date, end_date = selected_range
        monthly_view = monthly[
            (pd.to_datetime(monthly["month_date"]).dt.date >= start_date)
            & (pd.to_datetime(monthly["month_date"]).dt.date <= end_date)
        ].copy()
    else:
        monthly_view = monthly.copy()
else:
    monthly_view = monthly.copy()

st.sidebar.markdown("---")
st.sidebar.caption("Bảng chính được dùng: fact/dim/snapshot/mart trong schema storage.")


# =========================
# TABS
# =========================
tabs = st.tabs(["Executive", "Revenue", "Sellers", "Products", "Customers", "Quality & ML"])


# =========================
# EXECUTIVE
# =========================
with tabs[0]:
    header("Business overview", "Bức tranh tổng quan về tăng trưởng và hiệu quả vận hành")

    total_revenue = safe_sum(monthly_view, "revenue")
    total_orders = safe_sum(monthly_view, "orders")
    delivered_orders = safe_sum(monthly_view, "delivered_orders")
    cancelled_orders = safe_sum(monthly_view, "cancelled_orders")
    aov = total_revenue / total_orders if total_orders else 0
    delivery_rate = delivered_orders * 100 / total_orders if total_orders else 0
    cancel_rate = cancelled_orders * 100 / total_orders if total_orders else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("Gross GMV", money(total_revenue), "Tổng doanh thu theo khoảng lọc")
    with c2:
        kpi_card("Orders", f"{int(total_orders):,}", "Số đơn đã tạo")
    with c3:
        kpi_card("Average order", money(aov), "AOV = Revenue / Orders")
    with c4:
        kpi_card("Delivery rate", pct(delivery_rate), f"{int(delivered_orders):,} delivered")
    with c5:
        kpi_card("Cancel rate", pct(cancel_rate), f"{int(cancelled_orders):,} cancelled")

    st.markdown(
        "<div class='insight'>◈ <b>Ý nghĩa:</b> Trang Executive cho biết quy mô doanh thu, số đơn, AOV và rủi ro hủy đơn ở cấp tổng quan.</div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1.65, 1])
    with col1:
        st.subheader("GMV performance")
        if not monthly_view.empty:
            fig = px.line(
                monthly_view,
                x="month_date",
                y="revenue",
                markers=True,
                labels={"month_date": "Tháng", "revenue": "GMV"},
            )
            fig.update_layout(template="plotly_dark", height=360, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_state("Chưa có dữ liệu monthly KPI.")

    with col2:
        st.subheader("Order fulfillment")
        if not status_df.empty:
            fig = px.pie(status_df, names="order_status", values="order_count", hole=0.62)
            fig.update_layout(template="plotly_dark", height=360, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_state("Chưa có dữ liệu trạng thái đơn hàng.")

    col3, col4 = st.columns([1, 1])
    with col3:
        st.subheader("Cancellation rate")
        if not monthly_view.empty:
            fig = px.line(
                monthly_view,
                x="month_date",
                y="cancellation_rate",
                markers=True,
                labels={"month_date": "Tháng", "cancellation_rate": "Cancellation rate (%)"},
            )
            fig.update_layout(template="plotly_dark", height=280, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
    with col4:
        st.subheader("Freight pressure")
        if not freight_df.empty and "freight_ratio" in freight_df.columns:
            fig = px.line(freight_df, x="month_date", y="freight_ratio", markers=True)
            fig.update_layout(template="plotly_dark", height=280, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_state("Chưa tìm thấy cột freight_ratio trong storage.mart_financial_kpi. Có thể thêm mart này sau.")


# =========================
# REVENUE
# =========================
with tabs[1]:
    header("Revenue intelligence", "Xu hướng, động lực tăng trưởng và chênh lệch mục tiêu")

    if monthly_view.empty:
        empty_state("Chưa có dữ liệu doanh thu theo tháng.")
    else:
        revenue_view = monthly_view.copy().sort_values("month_date")
        peak = revenue_view.loc[revenue_view["revenue"].idxmax()]

        # Target chỉ dùng để minh họa quản trị.
        # Nếu sau này có bảng target thật trong DW thì thay phần này bằng query từ PostgreSQL.
        target_factors = [0.90, 0.91, 0.92, 0.93]
        revenue_view["target_revenue"] = [
            float(v) * target_factors[i % len(target_factors)]
            for i, v in enumerate(revenue_view["revenue"].fillna(0))
        ]

        total_target = safe_sum(revenue_view, "target_revenue")
        target_attainment = total_revenue * 100 / total_target if total_target else 0
        target_gap = total_revenue - total_target

        # Lost GMV proxy: ưu tiên lấy doanh thu cancelled nếu status_df có cột revenue.
        # Nếu không có thì ước tính theo tỷ lệ cancelled_orders.
        lost_gmv_proxy = 0.0

        if not status_df.empty and {"order_status", "revenue"}.issubset(status_df.columns):
            cancelled_mask = status_df["order_status"].astype(str).str.lower().eq("cancelled")
            lost_gmv_proxy = safe_sum(status_df.loc[cancelled_mask], "revenue")

        if lost_gmv_proxy == 0 and total_orders:
            lost_gmv_proxy = total_revenue * cancelled_orders / total_orders

        st.markdown(
            f"""
            <div class='insight'>
                ✦ Đỉnh doanh thu trong khoảng lọc là 
                <b>{money(peak['revenue'])}</b> vào 
                <b>{peak['month_label']}</b>. 
                Target trong trang này là mức minh họa để so sánh actual vs target.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 4 KPI card giống layout HTML preview
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            kpi_card(
                "Selected GMV",
                money(total_revenue),
                f"{len(revenue_view)} tháng được chọn",
            )

        with c2:
            gap_note = f"{money(abs(target_gap))} {'above plan' if target_gap >= 0 else 'below plan'}"
            kpi_card(
                "Target attainment",
                pct(target_attainment),
                gap_note,
            )

        with c3:
            kpi_card(
                "Lost GMV proxy",
                money(lost_gmv_proxy),
                "Ước tính từ đơn cancelled",
            )

        with c4:
            kpi_card(
                "Peak month",
                str(peak["month_label"]),
                money(peak["revenue"]),
            )

        # Chỉ giữ 2 biểu đồ
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Actual vs target")

            actual_target_df = revenue_view[
                ["month_date", "revenue", "target_revenue"]
            ].melt(
                id_vars="month_date",
                value_vars=["revenue", "target_revenue"],
                var_name="series",
                value_name="gmv",
            )

            actual_target_df["series"] = actual_target_df["series"].replace(
                {
                    "revenue": "Actual",
                    "target_revenue": "Target",
                }
            )

            fig = px.line(
                actual_target_df,
                x="month_date",
                y="gmv",
                color="series",
                markers=True,
                labels={
                    "month_date": "Tháng",
                    "gmv": "GMV",
                    "series": "",
                },
            )

            fig.update_layout(
                template="plotly_dark",
                height=390,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5,
                ),
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Growth decomposition")

            driver_df = revenue_view.copy()

            driver_df["order_growth_abs"] = (
                driver_df["orders"].pct_change().abs().fillna(0)
            )

            driver_df["aov_growth_abs"] = (
                driver_df["aov"].pct_change().abs().fillna(0)
            )

            denom = (
                driver_df["order_growth_abs"] + driver_df["aov_growth_abs"]
            ).replace(0, pd.NA)

            driver_df["Order volume"] = (
                driver_df["order_growth_abs"] * 100 / denom
            ).fillna(50)

            driver_df["AOV"] = 100 - driver_df["Order volume"]

            # Lấy 10 tháng cuối để biểu đồ gọn giống dashboard preview
            driver_df = driver_df.tail(10)

            driver_long = driver_df[
                ["month_date", "Order volume", "AOV"]
            ].melt(
                id_vars="month_date",
                value_vars=["Order volume", "AOV"],
                var_name="driver",
                value_name="contribution",
            )

            fig = px.bar(
                driver_long,
                x="month_date",
                y="contribution",
                color="driver",
                labels={
                    "month_date": "Tháng",
                    "contribution": "Contribution (%)",
                    "driver": "",
                },
            )

            fig.update_layout(
                template="plotly_dark",
                height=390,
                barmode="stack",
                yaxis_range=[0, 100],
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5,
                ),
            )

            st.plotly_chart(fig, use_container_width=True)


# =========================
# SELLERS
# =========================
with tabs[2]:
    header("Seller performance", "Đóng góp doanh thu, chất lượng và rủi ro tập trung")

    if seller_top.empty:
        empty_state("Chưa có dữ liệu seller snapshot.")
    else:
        top10_revenue = safe_sum(seller_top, "revenue")
        top10_share_total = top10_revenue * 100 / seller_total_revenue if seller_total_revenue else 0
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            kpi_card("Top 10 GMV", money(top10_revenue), "Doanh thu top seller")
        with c2:
            kpi_card("Top 10 share", pct(top10_share_total), "Tỷ trọng trên tổng seller revenue")
        with c3:
            kpi_card("Avg review", f"{safe_mean(seller_top, 'avg_review_score'):.2f}★", "Top seller")
        with c4:
            kpi_card("Avg cancel rate", pct(safe_mean(seller_top, "cancel_rate")), "Top seller")

        col1, col2 = st.columns([1.3, 1])
        with col1:
            st.subheader("Top sellers by GMV")
            fig = px.bar(
                seller_top.sort_values("revenue"),
                x="revenue",
                y="seller_short",
                orientation="h",
                labels={"revenue": "GMV", "seller_short": "Seller"},
            )
            fig.update_layout(template="plotly_dark", height=420, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Seller concentration")
            share_df = pd.DataFrame(
                {
                    "group": ["Top 10 sellers", "Other sellers"],
                    "revenue": [top10_revenue, max(seller_total_revenue - top10_revenue, 0)],
                }
            )
            fig = px.pie(share_df, names="group", values="revenue", hole=0.62)
            fig.update_layout(template="plotly_dark", height=420, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Seller leaderboard")
        st.caption("Ranked by gross GMV")

        render_seller_leaderboard(seller_top)
        # display_cols = [
        #     "seller_short",
        #     "revenue",
        #     "share",
        #     "orders_count",
        #     "items_sold",
        #     "cancel_rate",
        #     "avg_review_score",
        #     "risk",
        # ]

        # leaderboard_df = seller_top[display_cols].rename(
        #     columns={
        #         "seller_short": "Seller",
        #         "revenue": "GMV",
        #         "share": "Share (%)",
        #         "orders_count": "Orders",
        #         "items_sold": "Items sold",
        #         "cancel_rate": "Cancel (%)",
        #         "avg_review_score": "Review",
        #         "risk": "Risk",
        #     }
        # )

        # leaderboard_df["GMV"] = leaderboard_df["GMV"].apply(money)
        # leaderboard_df["Share (%)"] = leaderboard_df["Share (%)"].map(lambda x: f"{x:.2f}%")
        # leaderboard_df["Cancel (%)"] = leaderboard_df["Cancel (%)"].map(lambda x: f"{x:.2f}%")
        # leaderboard_df["Review"] = leaderboard_df["Review"].map(lambda x: f"{x:.2f}")

# =========================
# PRODUCTS
# =========================
with tabs[3]:
    header("Product & category", "Danh mục chủ lực và tốc độ bán sản phẩm")

    if category_top.empty:
        empty_state("Chưa có dữ liệu product/category snapshot.")
    else:
        product_view = category_top.copy()

        product_view["category_label"] = (
            product_view["category"]
            .astype(str)
            .str.replace("_", " ", regex=False)
            .str.title()
        )

        product_view = product_view.sort_values("revenue", ascending=False).head(8)

        col1, col2 = st.columns([1.65, 1])

        with col1:
            st.subheader("Category gross GMV")
            st.caption("Top eight · R$ thousand")

            colors = [
                "#9677ff",
                "#34d9c5",
                "#ffbd59",
                "#58a6ff",
                "#ef7fc3",
                "#ff6b81",
                "#68d391",
                "#9f7aea",
            ]

            fig = px.bar(
                product_view.sort_values("revenue", ascending=True),
                x="revenue",
                y="category_label",
                orientation="h",
                text=None,
                labels={
                    "revenue": "GMV",
                    "category_label": "",
                },
                color="category_label",
                color_discrete_sequence=colors,
            )

            fig.update_traces(
                marker_line_width=0,
                hovertemplate="<b>%{y}</b><br>GMV: R$%{x:,.0f}<extra></extra>",
            )

            fig.update_layout(
                template="plotly_dark",
                height=460,
                showlegend=False,
                margin=dict(l=10, r=20, t=10, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    gridcolor="#23283a",
                    tickprefix="R$",
                    tickformat="~s",
                    title=None,
                ),
                yaxis=dict(
                    title=None,
                    gridcolor="rgba(0,0,0,0)",
                ),
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            render_sales_velocity(product_view)

# =========================
# CUSTOMERS
# =========================
with tabs[4]:
    header("Customer value", "Phân khúc hành vi và cơ hội giữ chân khách hàng")

    if customer_df.empty:
        empty_state("Chưa có dữ liệu customer behavior hoặc mart_customer_cluster_features.")
    else:
        customer_view = customer_df.copy()

        if "avg_review_score" not in customer_view.columns and "avg_score_review" in customer_view.columns:
            customer_view["avg_review_score"] = customer_view["avg_score_review"]

        if "avg_order_value" not in customer_view.columns and {"total_spend", "order_cnt"}.issubset(customer_view.columns):
            customer_view["avg_order_value"] = (
                customer_view["total_spend"] / customer_view["order_cnt"].replace(0, pd.NA)
            )

        repeat_rate = (
            (customer_view["order_cnt"] >= 2).mean() * 100
            if "order_cnt" in customer_view.columns
            else 0
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            kpi_card("Customers", f"{len(customer_view):,}", "Tổng số khách hàng")

        with c2:
            kpi_card("Avg spend", money(safe_mean(customer_view, "total_spend")), "Chi tiêu trung bình")

        with c3:
            kpi_card("Repeat buyers", pct(repeat_rate), "Retention opportunity")

        with c4:
            kpi_card("Avg review", f"{safe_mean(customer_view, 'avg_review_score'):.2f}★", "Điểm review TB")

        st.markdown(
            """
            <div class='insight'>
                ◈ Tệp khách hàng chủ yếu mua một lần. Ưu tiên chiến dịch tái kích hoạt cho nhóm 
                <b>returning customers</b> và nhóm có AOV cao.
            </div>
            """,
            unsafe_allow_html=True,
        )

        cluster_summary = prepare_customer_cluster_summary(customer_view)

        render_customer_segment_cards(cluster_summary)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # =========================
        # FILTER CUSTOMER SEGMENT
        # =========================
        filter_col1, filter_col2 = st.columns([3, 1])

        with filter_col2:
            segment_options = ["All clusters"] + cluster_summary["segment"].tolist()

            selected_segment = st.selectbox(
                "Lọc nhóm khách hàng",
                segment_options,
                index=0,
                key="customer_segment_filter",
            )

        if selected_segment == "All clusters":
            chart_summary = cluster_summary.copy()

            if "Premium" in cluster_summary["segment"].values:
                profile_row = cluster_summary[
                    cluster_summary["segment"] == "Premium"
                ].iloc[0]
            else:
                profile_row = cluster_summary.sort_values(
                    "total_spend",
                    ascending=False,
                ).iloc[0]

            profile_title = "Premium / highest value cluster"
        else:
            chart_summary = cluster_summary[
                cluster_summary["segment"] == selected_segment
            ].copy()

            profile_row = chart_summary.iloc[0]
            profile_title = selected_segment

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        color_map = {
            "Premium": "#9677ff",
            "Loyal": "#34d9c5",
            "One-time": "#ffbd59",
            "At-risk": "#ff6b81",
        }

        # =========================
        # LEFT CHART: AVG SPEND
        # =========================
        with col1:
            st.subheader("Average spend by cluster")
            st.caption("K-means · 4 clusters")

            spend_df = chart_summary.copy()

            fig = px.bar(
                spend_df,
                x="segment",
                y="total_spend",
                color="segment",
                color_discrete_map=color_map,
                category_orders={
                    "segment": ["One-time", "Loyal", "Premium", "At-risk"]
                },
                labels={
                    "segment": "",
                    "total_spend": "Avg spend",
                },
            )

            fig.update_traces(
                marker_line_width=0,
                hovertemplate="<b>%{x}</b><br>Avg spend: R$%{y:,.0f}<extra></extra>",
            )

            fig.update_layout(
                template="plotly_dark",
                height=390,
                showlegend=False,
                margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(
                    tickprefix="R$",
                    gridcolor="#23283a",
                    title=None,
                ),
                xaxis=dict(
                    title=None,
                    gridcolor="rgba(0,0,0,0)",
                ),
            )

            st.plotly_chart(fig, use_container_width=True)

        # =========================
        # RIGHT CHART: RADAR PROFILE
        # =========================
        with col2:
            st.subheader("Cluster profile")
            st.caption(f"Behavioral comparison · {profile_title}")

            radar_cols = {
                "Spend": "total_spend",
                "Orders": "order_cnt",
                "AOV": "avg_order_value",
                "Review": "avg_review_score",
                "Return": "avg_day_return_to_buy",
            }

            values = []

            for label, col in radar_cols.items():
                max_val = cluster_summary[col].max()
                val = profile_row[col]

                if pd.isna(max_val) or max_val == 0:
                    values.append(0)
                else:
                    values.append(float(val) * 100 / float(max_val))

            labels = list(radar_cols.keys())

            selected_color = color_map.get(str(profile_row["segment"]), "#9677ff")

            fig = go.Figure()

            fig.add_trace(
                go.Scatterpolar(
                    r=values + [values[0]],
                    theta=labels + [labels[0]],
                    fill="toself",
                    name=str(profile_row["segment"]),
                    line=dict(color=selected_color, width=3),
                    fillcolor="rgba(150,119,255,0.25)",
                )
            )

            fig.update_layout(
                template="plotly_dark",
                height=390,
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(
                        visible=False,
                        range=[0, 100],
                    ),
                    angularaxis=dict(
                        color="#7f879e",
                    ),
                ),
            )

            st.plotly_chart(fig, use_container_width=True)


# =========================
# QUALITY & ML
# =========================
with tabs[5]:
    header("Service quality & ML", "Review health và khả năng nhận diện đơn có nguy cơ đánh giá xấu")

    total_reviews = safe_sum(review_df, "review_count")
    avg_review = 0.0
    if not review_df.empty:
        avg_review = (review_df["review_score"] * review_df["review_count"]).sum() / total_reviews

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Avg review", f"{avg_review:.2f}★", "Điểm review trung bình")
    with c2:
        kpi_card("Bad review rate", pct(bad_review_rate), "Review ≤ 2★")
    with c3:
        if not model_metrics.empty:
            acc = model_metrics[(model_metrics["metric_name"].str.lower() == "accuracy")]["metric_value"].head(1)
            kpi_card("Model accuracy", pct(float(acc.iloc[0]) * 100 if not acc.empty and float(acc.iloc[0]) <= 1 else float(acc.iloc[0]) if not acc.empty else 0), "Từ storage.ml_model_metrics")
        else:
            kpi_card("Model metrics", "N/A", "Chưa có bảng storage.ml_model_metrics")
    with c4:
        kpi_card("Reviews", f"{int(total_reviews):,}", "Số bản ghi review")

    col1, col2 = st.columns([1.1, 1])
    with col1:
        st.subheader("Review distribution")
        if not review_df.empty:
            fig = px.bar(review_df, x="review_score", y="review_count")
            fig.update_layout(template="plotly_dark", height=380, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_state("Chưa có dữ liệu review.")
    with col2:
        st.subheader("Risk drivers")
        st.dataframe(
            pd.DataFrame(
                [
                    ["Waiting days", "Thời gian xử lý/giao hàng dài", "High"],
                    ["Late delivery", "Giao sau ngày dự kiến", "High"],
                    ["Freight ratio", "Áp lực phí vận chuyển", "Medium"],
                    ["Item count", "Độ phức tạp đơn hàng", "Medium"],
                    ["Installments", "Hành vi thanh toán", "Low"],
                ],
                columns=["Feature", "Business meaning", "Priority"],
            ),
            hide_index=True,
            use_container_width=True,
        )

    if not model_metrics.empty:
        st.subheader("ML model metrics")
        st.dataframe(model_metrics, use_container_width=True, hide_index=True)
    else:
        st.info(
            "Nếu muốn hiển thị Accuracy/Precision/Recall/F1 trực tiếp từ PostgreSQL, hãy tạo bảng storage.ml_model_metrics "
            "hoặc lưu kết quả model vào một mart riêng."
        )
