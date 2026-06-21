import os
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
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
    df = pd.read_sql("SELECT * FROM storage.mart_order_bad_review_features", engine)

    # loại bỏ id và cột review_score vì label được tạo từ review_score
    X = df.drop(columns=["order_id", "review_score", "bad_review"], errors="ignore")
    y = df["bad_review"].astype(int)

    # chỉ dùng numeric feature để đơn giản
    X = X.select_dtypes(include=["number"]).fillna(0)

    if y.nunique() < 2:
        raise ValueError("Target bad_review chỉ có 1 lớp, không thể train classifier.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    report = classification_report(y_test, y_pred, output_dict=True)
    pd.DataFrame(report).T.to_csv(OUTPUT_DIR / "classification_bad_review_report.csv")

    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.imshow(cm)
    ax.set_title("Confusion Matrix - Bad Review Classification")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, cm[i, j], ha="center", va="center")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "classification_bad_review_confusion_matrix.png")
    plt.close(fig)

    joblib.dump(model, OUTPUT_DIR / "classification_bad_review_model.pkl")
    print("Done. Outputs saved to ml/outputs/")


if __name__ == "__main__":
    main()
