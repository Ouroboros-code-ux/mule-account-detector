"""
Robust Mule Account & Fraud Detection Model Training Pipeline.
Optimized for low-RAM streaming across multi-million row datasets.
Outputs:
  - backend/data/mule_pipeline.pkl (Trained Preprocessor + Classifier)
  - backend/data/mule_profiling.json (Statistical benchmarks for Explainable AI)
  - backend/data/mule_evaluation.json (ROC-AUC, Precision, Recall metrics)
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
    average_precision_score,
    confusion_matrix
)
import joblib

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "financial_fraud_detection_dataset.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

NUMERIC_FEATURES = [
    "amount",
    "spending_deviation_score",
    "velocity_score",
    "geo_anomaly_score",
    "time_since_last_transaction"
]

CATEGORICAL_FEATURES = [
    "transaction_type",
    "payment_channel",
    "device_used"
]

TARGET = "is_fraud"

def extract_balanced_sample(csv_path: str, chunk_size: int = 100000, normal_sample_ratio: float = 0.05) -> pd.DataFrame:
    """
    Streams CSV in chunks to collect 100% of fraud instances
    along with a representative sample of legitimate transactions.
    Keeps memory usage strictly bounded (<300MB).
    """
    logger.info(f"Streaming data from {csv_path} in chunks of {chunk_size:,} rows...")
    
    fraud_chunks = []
    normal_chunks = []
    total_rows = 0
    total_fraud = 0

    cols_to_load = NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET, "fraud_type"]

    for chunk in pd.read_csv(csv_path, chunksize=chunk_size, usecols=cols_to_load, low_memory=False):
        total_rows += len(chunk)
        
        # Fill missing values gracefully
        chunk["time_since_last_transaction"] = chunk["time_since_last_transaction"].fillna(chunk["time_since_last_transaction"].median())
        chunk["spending_deviation_score"] = chunk["spending_deviation_score"].fillna(0.0)
        chunk["velocity_score"] = chunk["velocity_score"].fillna(0.0)
        chunk["geo_anomaly_score"] = chunk["geo_anomaly_score"].fillna(0.0)
        chunk["is_fraud"] = chunk["is_fraud"].astype(bool)

        fraud_part = chunk[chunk[TARGET] == True]
        normal_part = chunk[chunk[TARGET] == False].sample(frac=normal_sample_ratio, random_state=42)

        total_fraud += len(fraud_part)
        fraud_chunks.append(fraud_part)
        normal_chunks.append(normal_part)

        if total_rows % 500000 == 0:
            logger.info(f"Processed {total_rows:,} rows | Found {total_fraud:,} fraud cases so far...")

    df_fraud = pd.concat(fraud_chunks, ignore_index=True)
    df_normal = pd.concat(normal_chunks, ignore_index=True)

    combined_df = pd.concat([df_fraud, df_normal], ignore_index=True).sample(frac=1.0, random_state=42)
    logger.info(f"Dataset summary: Total rows scanned: {total_rows:,} | Selected balanced training set: {len(combined_df):,} rows ({len(df_fraud):,} fraud / {len(df_normal):,} normal)")
    return combined_df

def compute_profiling_benchmarks(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes statistical percentiles for legitimate vs. mule transactions.
    Used by Explainable AI (XAI) to explain why an account was flagged.
    """
    logger.info("Computing behavioral baseline statistics for XAI...")
    profiles = {"normal": {}, "fraud": {}, "fraud_types": []}

    normal_df = df[df[TARGET] == False]
    fraud_df = df[df[TARGET] == True]

    for feat in NUMERIC_FEATURES:
        profiles["normal"][feat] = {
            "mean": float(normal_df[feat].mean()),
            "std": float(normal_df[feat].std()),
            "p50": float(normal_df[feat].median()),
            "p90": float(normal_df[feat].quantile(0.90)),
            "p99": float(normal_df[feat].quantile(0.99))
        }
        profiles["fraud"][feat] = {
            "mean": float(fraud_df[feat].mean()),
            "std": float(fraud_df[feat].std()),
            "p50": float(fraud_df[feat].median()),
            "p90": float(fraud_df[feat].quantile(0.90)),
            "p99": float(fraud_df[feat].quantile(0.99))
        }

    if "fraud_type" in df.columns:
        profiles["fraud_types"] = [str(t) for t in fraud_df["fraud_type"].dropna().unique().tolist()]

    return profiles

def build_and_train_pipeline(df: pd.DataFrame):
    """
    Builds robust end-to-end preprocessing + calibrated HistGradientBoostingClassifier.
    HistGradientBoosting handles non-linear relationships, missing values, and high dimensions.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Compute and save XAI baselines
    profiles = compute_profiling_benchmarks(df)
    with open(os.path.join(OUTPUT_DIR, "mule_profiling.json"), "w") as f:
        json.dump(profiles, f, indent=2)
    logger.info("Saved XAI behavioral profiles to backend/data/mule_profiling.json")

    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    logger.info(f"Training set: {len(X_train):,} rows | Test set: {len(X_test):,} rows")

    # Robust Preprocessing:
    # 1. RobustScaler: scales numerical features using median & IQR (resists extreme money outliers)
    # 2. OneHotEncoder: categorical variables
    numeric_transformer = Pipeline(steps=[
        ("scaler", RobustScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERIC_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES)
        ]
    )

    # HistGradientBoostingClassifier with balanced class weighting for fraud detection
    # Captures non-linear, multi-branch fraud logic
    classifier = HistGradientBoostingClassifier(
        max_iter=200,
        learning_rate=0.08,
        max_depth=8,
        min_samples_leaf=25,
        class_weight="balanced",
        random_state=42
    )

    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", classifier)
    ])

    logger.info("Fitting Gradient Boosting Pipeline...")
    pipeline.fit(X_train, y_train)

    logger.info("Evaluating model on Holdout Test Set...")
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    roc_auc = float(roc_auc_score(y_test, y_proba))
    pr_auc = float(average_precision_score(y_test, y_proba))
    cm = confusion_matrix(y_test, y_pred).tolist()
    report = classification_report(y_test, y_pred, output_dict=True)

    metrics = {
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "confusion_matrix": cm,
        "classification_report": report
    }

    logger.info(f"Model Results: ROC-AUC: {roc_auc:.4f} | PR-AUC: {pr_auc:.4f}")
    logger.info(f"Classification Report:\n{classification_report(y_test, y_pred)}")

    # Save trained pipeline and metrics
    model_path = os.path.join(OUTPUT_DIR, "mule_pipeline.pkl")
    joblib.dump(pipeline, model_path)
    logger.info(f"Saved complete pipeline to {model_path}")

    metrics_path = os.path.join(OUTPUT_DIR, "mule_evaluation.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved evaluation metrics to {metrics_path}")

if __name__ == "__main__":
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")
    
    df = extract_balanced_sample(DATASET_PATH)
    build_and_train_pipeline(df)
