"""Machine learning pipeline construction and model training module.

Constructs an end-to-end scikit-learn Pipeline incorporating:
- Numerical feature scaling via `StandardScaler`.
- Categorical one-hot encoding via `OneHotEncoder(handle_unknown='ignore')`.
- Regressor algorithms (`RandomForestRegressor` and `XGBRegressor`).
- Cross-validation and model serialization.
"""

from typing import Tuple, Dict, Any
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

from src.data.cleaning import clean_laptop_data, load_raw_data
from src.data.feature_engineering import engineer_features, get_feature_columns
from src.models.evaluate import evaluate_model


def build_preprocessor() -> ColumnTransformer:
    """Build scikit-learn ColumnTransformer for unified feature preprocessing.

    Returns:
        ColumnTransformer: Preprocessor mapping numerical and categorical transforms.
    """
    feature_spec = get_feature_columns()
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), feature_spec["numeric"]),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                feature_spec["categorical"],
            ),
        ],
        remainder="drop",
    )


def build_pipeline(model_type: str = "random_forest") -> Pipeline:
    """Instantiate a complete training pipeline with preprocessor and regressor.

    Args:
        model_type: Model algorithm identifier ('random_forest' or 'xgboost').

    Returns:
        Pipeline: Assembled scikit-learn Pipeline ready for `.fit()`.
    """
    preprocessor = build_preprocessor()

    if model_type.lower() == "xgboost" and HAS_XGBOOST:
        regressor = XGBRegressor(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
        )
    else:
        regressor = RandomForestRegressor(
            n_estimators=300,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        )

    return Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", regressor),
    ])


def prepare_data(data_path: str) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """Ingest, clean, engineer, and split laptop dataset into train/test partitions.

    Args:
        data_path: Path to raw dataset CSV file.

    Returns:
        Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
            (X_train, y_train, X_test, y_test)
    """
    raw_df = load_raw_data(data_path)
    cleaned_df = clean_laptop_data(raw_df)
    engineered_df = engineer_features(cleaned_df)

    feature_spec = get_feature_columns()
    all_features = feature_spec["numeric"] + feature_spec["categorical"]

    X = engineered_df[all_features]
    y = engineered_df["price"]

    return train_test_split(X, y, test_size=0.20, random_state=42)


def train_and_save(
    data_path: str = "data/raw/laptop_price - dataset.csv",
    model_dir: str = "models",
    model_type: str = "random_forest",
) -> Dict[str, Any]:
    """Execute end-to-end training, evaluate across candidates, and export artifact.

    Args:
        data_path: Filepath to raw CSV data.
        model_dir: Directory where the serialized model artifact will be saved.
        model_type: Default regressor architecture ('random_forest' or 'xgboost').

    Returns:
        Dict[str, Any]: Dictionary detailing evaluation metrics for trained models.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Dataset not found at {data_path}. Place dataset in data/raw/ before training."
        )

    print(f"Loading and processing dataset from {data_path}...")
    X_train, y_train, X_test, y_test = prepare_data(data_path)
    print(f"Partition summary: {len(X_train)} training instances, {len(X_test)} evaluation instances.")

    candidates = ["random_forest"]
    if HAS_XGBOOST:
        candidates.append("xgboost")

    evaluation_results: Dict[str, Any] = {}
    best_estimator = None
    best_score = -np.inf
    best_name = ""

    for candidate_name in candidates:
        print(f"Fitting pipeline candidate: {candidate_name}...")
        pipeline = build_pipeline(candidate_name)
        pipeline.fit(X_train, y_train)

        metrics = evaluate_model(pipeline, X_test, y_test)
        cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring="r2")
        metrics["cv_r2_mean"] = float(cv_scores.mean())
        metrics["cv_r2_std"] = float(cv_scores.std())
        evaluation_results[candidate_name] = metrics

        print(f"  Holdout R2: {metrics['r2']:.4f} | MAE: {metrics['mae']:.2f} | 5-Fold CV R2: {metrics['cv_r2_mean']:.4f}")

        if metrics["r2"] > best_score:
            best_score = metrics["r2"]
            best_estimator = pipeline
            best_name = candidate_name

    os.makedirs(model_dir, exist_ok=True)
    destination_file = os.path.join(model_dir, "best_model.pkl")
    joblib.dump(best_estimator, destination_file)
    print(f"Best model candidate ({best_name}) successfully exported to {destination_file}")

    evaluation_results["best_model"] = best_name
    return evaluation_results


if __name__ == "__main__":
    train_and_save()
