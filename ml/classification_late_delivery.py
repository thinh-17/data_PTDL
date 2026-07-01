import os
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "ml" / "outputs"


def get_engine():
    load_dotenv(ROOT_DIR / ".env")

    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db = os.getenv("POSTGRES_DB", "olist_dwh")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")

    return create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    )


def make_one_hot_encoder():
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    engine = get_engine()
    df = pd.read_sql("SELECT * FROM storage.mart_late_delivery_features", engine)

    # Lưu phân bố target để đưa vào báo cáo
    target_dist = (
        df["late_delivery"]
        .value_counts(normalize=False)
        .rename_axis("late_delivery")
        .reset_index(name="count")
    )
    target_dist["pct"] = target_dist["count"] * 100 / target_dist["count"].sum()
    target_dist.to_csv(
        OUTPUT_DIR / "late_delivery_target_distribution.csv",
        index=False,
    )

    y = df["late_delivery"].astype(int)

    # Không đưa leakage columns vào feature
    X = df.drop(
        columns=[
            "order_id",
            "late_delivery",
            "delay_days",
        ],
        errors="ignore",
    )

    numeric_features = X.select_dtypes(include=["number"]).columns.tolist()
    categorical_features = X.select_dtypes(include=["object"]).columns.tolist()

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", make_one_hot_encoder()),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=12,
                    min_samples_leaf=10,
                    random_state=42,
                    class_weight="balanced",
                    n_jobs=-1,
                ),
            ),
        ]
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_score = model.predict_proba(X_test)[:, 1]

    report = classification_report(y_test, y_pred, output_dict=True)
    report_df = pd.DataFrame(report).T

    roc_auc = roc_auc_score(y_test, y_score)
    pr_auc = average_precision_score(y_test, y_score)

    report_df.loc["roc_auc", "score"] = roc_auc
    report_df.loc["pr_auc", "score"] = pr_auc

    report_df.to_csv(OUTPUT_DIR / "classification_late_delivery_report.csv")

    cm = confusion_matrix(y_test, y_pred)

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.imshow(cm)
    ax.set_title("Confusion Matrix - Late Delivery Classification")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, cm[i, j], ha="center", va="center")

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "classification_late_delivery_confusion_matrix.png")
    plt.close(fig)

    joblib.dump(model, OUTPUT_DIR / "classification_late_delivery_model.pkl")

    print("Done. Outputs saved to ml/outputs/")
    print(f"ROC-AUC: {roc_auc:.4f}")
    print(f"PR-AUC : {pr_auc:.4f}")
    print(classification_report(y_test, y_pred))


if __name__ == "__main__":
    main()