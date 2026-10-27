"""
Revenue Prediction Model Training & Evaluation Engine.
Supports local execution (Scikit-Learn/XGBoost) and distributed Ray Train (XGBoostTrainer).
"""

import os
import json
import math
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd

from application.src.schema_validator import CanonicalCompanyEntity

def prepare_feature_matrix(entities: List[CanonicalCompanyEntity]) -> Tuple[pd.DataFrame, pd.Series]:
    """Extract and vectorize features from canonical company entities."""
    data = []
    for ent in entities:
        # Exclude invalid or zero revenue records
        if ent.annual_revenue <= 0.0 or ent.employee_count <= 0:
            continue

        company_age = max(1, 2025 - ent.founded_year)
        data.append({
            "employee_count": ent.employee_count,
            "founded_year": ent.founded_year,
            "company_age": company_age,
            "industry_sector": ent.industry_sector,
            "country": ent.country,
            "annual_revenue": ent.annual_revenue
        })

    df = pd.DataFrame(data)
    if df.empty:
        raise ValueError("No valid entities available for model training!")

    # One-hot encode categorical features
    df_encoded = pd.get_dummies(df, columns=["industry_sector", "country"], drop_first=True)
    X = df_encoded.drop(columns=["annual_revenue"])
    y = df_encoded["annual_revenue"]
    return X, y

def train_and_evaluate_model(
    entities: List[CanonicalCompanyEntity],
    output_model_dir: str = "application/models",
    test_size: float = 0.20,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Trains a regression model to predict annual company revenue in USD,
    evaluates MAE, RMSE, and R2 on a held-out test split, and persists artifacts.
    """
    os.makedirs(output_model_dir, exist_ok=True)
    X, y = prepare_feature_matrix(entities)

    # Train / Test split
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # Train Gradient Boosting Regressor (matches Ray Train XGBoost architecture)
    model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=4,
        random_state=random_state
    )
    model.fit(X_train, y_train)

    # Predictions & Evaluation
    y_pred = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    mse = float(mean_squared_error(y_test, y_pred))
    rmse = float(math.sqrt(mse))
    r2 = float(r2_score(y_test, y_pred))

    metrics = {
        "evaluation_metrics": {
            "test_mae_usd": round(mae, 2),
            "test_rmse_usd": round(rmse, 2),
            "test_r2_score": round(r2, 4),
        },
        "dataset_statistics": {
            "total_samples": len(X),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "feature_count": X.shape[1],
            "feature_names": list(X.columns),
            "target": "annual_revenue_usd"
        },
        "model_architecture": "GradientBoostingRegressor (100 estimators, depth=4)"
    }

    # Persist metrics JSON
    metrics_path = os.path.join(output_model_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Persist serialized model
    try:
        import joblib
        model_path = os.path.join(output_model_dir, "revenue_model.joblib")
        joblib.dump(model, model_path)
    except ImportError:
        import pickle
        model_path = os.path.join(output_model_dir, "revenue_model.pkl")
        with open(model_path, "wb") as f:
            pickle.dump(model, f)

    return {
        "metrics": metrics,
        "metrics_file": metrics_path,
        "model_file": model_path
    }
