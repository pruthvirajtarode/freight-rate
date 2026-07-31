"""
model_selection.py — Model comparison and selection.

Trains multiple regression models using Cross-Validation, evaluates them
on key metrics (RMSE, MAE, R2, MAPE), and selects the best model.
"""

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    RandomForestRegressor,
)

# Scikit-learn models
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, cross_validate

# Advanced models
XGBRegressor: Any = None
try:
    from xgboost import XGBRegressor as _XGBRegressor

    XGBRegressor = _XGBRegressor
except ImportError:
    pass

LGBMRegressor: Any = None
try:
    from lightgbm import LGBMRegressor as _LGBMRegressor

    LGBMRegressor = _LGBMRegressor
except ImportError:
    pass

CatBoostRegressor: Any = None
try:
    from catboost import CatBoostRegressor as _CatBoostRegressor

    CatBoostRegressor = _CatBoostRegressor
except ImportError:
    pass

from config import CV_FOLDS, MODELS_TO_COMPARE, RANDOM_STATE
from utils import get_logger, timeit

logger = get_logger(__name__)


def get_model_instances() -> dict[str, Any]:
    """
    Instantiate and return dictionary of models to compare.
    Only includes models that are successfully imported and listed in config.
    """
    models = {}

    if "LinearRegression" in MODELS_TO_COMPARE:
        models["LinearRegression"] = LinearRegression()

    if "RandomForest" in MODELS_TO_COMPARE:
        models["RandomForest"] = RandomForestRegressor(
            n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1
        )

    if "ExtraTrees" in MODELS_TO_COMPARE:
        models["ExtraTrees"] = ExtraTreesRegressor(
            n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1
        )

    if "GradientBoosting" in MODELS_TO_COMPARE:
        models["GradientBoosting"] = GradientBoostingRegressor(
            n_estimators=100, random_state=RANDOM_STATE
        )

    if "XGBoost" in MODELS_TO_COMPARE and XGBRegressor is not None:
        models["XGBoost"] = XGBRegressor(
            n_estimators=100,
            random_state=RANDOM_STATE,
            n_jobs=-1,
            objective="reg:squarederror",
        )

    if "LightGBM" in MODELS_TO_COMPARE and LGBMRegressor is not None:
        models["LightGBM"] = LGBMRegressor(
            n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1
        )

    if "CatBoost" in MODELS_TO_COMPARE and CatBoostRegressor is not None:
        models["CatBoost"] = CatBoostRegressor(
            iterations=100, random_seed=RANDOM_STATE, thread_count=-1, verbose=0
        )

    return models


@timeit
def compare_models(
    X: pd.DataFrame, y: pd.Series
) -> tuple[str, dict[str, dict[str, float]]]:
    """
    Compare multiple models using K-Fold cross-validation.

    Args:
        X: Feature matrix.
        y: Target variable.

    Returns:
        Tuple of (best_model_name, dictionary_of_all_model_metrics).
    """
    models = get_model_instances()
    if not models:
        raise ValueError("No models available to train. Check imports and config.")

    logger.info(f"Comparing {len(models)} models using {CV_FOLDS}-fold CV...")

    # We will compute RMSE, MAE, R2.
    # scikit-learn cross_validate uses negative scoring for metrics where lower is better.
    scoring = {
        "rmse": "neg_root_mean_squared_error",
        "mae": "neg_mean_absolute_error",
        "r2": "r2",
    }

    kf = KFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    results = {}
    best_model_name = ""
    best_rmse = float("inf")

    for name, model in models.items():
        logger.info(f"Evaluating {name}...")

        cv_res = cross_validate(
            model, X, y, cv=kf, scoring=scoring, n_jobs=1, return_train_score=False
        )

        # Calculate means over folds
        mean_rmse = -np.mean(cv_res["test_rmse"])
        mean_mae = -np.mean(cv_res["test_mae"])
        mean_r2 = np.mean(cv_res["test_r2"])
        mean_fit_time = np.mean(cv_res["fit_time"])

        # Approximate MAPE (cannot be done perfectly in cross_validate without custom scorer)
        # We will log what we have.
        results[name] = {
            "rmse": round(float(mean_rmse), 4),
            "mae": round(float(mean_mae), 4),
            "r2": round(float(mean_r2), 6),
            "fit_time_seconds": round(float(mean_fit_time), 2),
        }

        logger.info(f"  {name} -> RMSE: {mean_rmse:.2f} | R2: {mean_r2:.4f}")

        if mean_rmse < best_rmse:
            best_rmse = mean_rmse
            best_model_name = name

    logger.info(f"Best model selected: {best_model_name} (RMSE: {best_rmse:.2f})")

    return best_model_name, results


def train_final_model(
    model_name: str,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    best_params: dict[str, Any] | None = None,
) -> Any:
    """
    Train the chosen model on the full training dataset.

    Args:
        model_name: Name of the model to instantiate.
        X_train: Full training features.
        y_train: Full training targets.
        best_params: Optional dict of hyperparameters to apply.

    Returns:
        Trained model instance.
    """
    models = get_model_instances()
    if model_name not in models:
        raise ValueError(f"Model {model_name} not found in available models.")

    model = models[model_name]

    # Apply hyperparameters if provided
    if best_params:
        logger.info(f"Applying hyperparameters to {model_name}: {best_params}")
        if hasattr(model, "set_params"):
            model.set_params(**best_params)

    logger.info(f"Training final {model_name} on {len(X_train)} rows...")
    model.fit(X_train, y_train)
    logger.info("Final model training complete.")

    return model
