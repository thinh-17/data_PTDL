import os
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "ml" / "outputs"


def get_engine():
    load_dotenv(ROOT_DIR / ".env")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db = os.getenv("POSTGRES_DB", "olist_dwh")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    engine = get_engine()
    df = pd.read_sql("SELECT * FROM storage.mart_customer_cluster_features", engine)

    id_cols = ["customer_key", "customer_unique_id"]
    X = df.drop(columns=id_cols, errors="ignore")
    X = X.select_dtypes(include=["number"]).fillna(0)

    n_clusters = 4
    pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("kmeans", KMeans(n_clusters=n_clusters, random_state=42, n_init=10)),
    ])

    clusters = pipeline.fit_predict(X)
    result = df.copy()
    result["cluster"] = clusters
    result.to_csv(OUTPUT_DIR / "customer_clusters.csv", index=False)

    # đánh giá silhouette nếu đủ cụm
    if len(set(clusters)) > 1 and len(result) > n_clusters:
        scaled = pipeline.named_steps["scaler"].transform(
            pipeline.named_steps["imputer"].transform(X)
        )
        score = silhouette_score(scaled, clusters)
    else:
        score = None

    summary = result.groupby("cluster").mean(numeric_only=True)
    summary.to_csv(OUTPUT_DIR / "customer_cluster_summary.csv")

    # biểu đồ tổng chi tiêu trung bình theo cụm
    fig, ax = plt.subplots(figsize=(7, 4))
    summary["total_spend"].plot(kind="bar", ax=ax)
    ax.set_title("Average Total Spend by Customer Cluster")
    ax.set_xlabel("Cluster")
    ax.set_ylabel("Average total spend")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "customer_cluster_total_spend.png")
    plt.close(fig)

    joblib.dump(pipeline, OUTPUT_DIR / "customer_kmeans_model.pkl")
    print(f"Done. Silhouette score: {score}. Outputs saved to ml/outputs/")


if __name__ == "__main__":
    main()
