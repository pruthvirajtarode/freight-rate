"""
hyperparameter_tuning.py — Optuna-based Hyperparameter Optimization.

Given a selected best model, this module runs an Optuna study to find
the optimal hyperparameters to minimize RMSE.
"""

from typing import Any

import numpy as np
import optuna
import pandas as pd
from config import (
    CV_FOLDS,
    OPTUNA_DIRECTION,
    OPTUNA_N_TRIALS,
    OPTUNA_TIMEOUT_SECONDS,
    RANDOM_STATE,
)
from sklearn.model_selection import KFold, cross_val_score
from utils import get_logger, timeit

logger = get_logger(__name__)

# Suppress verbose Optuna logging
optuna.logging.set_verbosity(optuna.logging.WARNING)


def get_search_space(model_name: str, trial: optuna.Trial) -> dict[str, Any]:
    """
    Define the hyperparameter search space for each supported model.
    """
    params = {}

    if model_name == "RandomForest":
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 300),
            "max_depth": trial.suggest_int("max_depth", 5, 30),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
            "max_features": trial.suggest_categorical(
                "max_features", ["sqrt", "log2", None]
            ),
        }

    elif model_name == "ExtraTrees":
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 300),
            "max_depth": trial.suggest_int("max_depth", 5, 30),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
        }

    elif model_name == "GradientBoosting":
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 300),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "max_depth": trial.suggest_int("max_depth", 3, 10),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        }

    elif model_name == "XGBoost":
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 300),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "max_depth": trial.suggest_int("max_depth", 3, 12),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        }

    elif model_name == "LightGBM":
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 300),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 20, 100),
            "max_depth": trial.suggest_int("max_depth", 3, 15),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "verbose": -1,
        }

    elif model_name == "CatBoost":
        params = {
            "iterations": trial.suggest_int("iterations", 50, 300),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "depth": trial.suggest_int("depth", 4, 10),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1e-3, 10.0, log=True),
            "verbose": 0,
        }

    return params


@timeit
def tune_hyperparameters(
    model_name: str, X: pd.DataFrame, y: pd.Series
) -> dict[str, Any]:
    """
    Run Optuna study to find best hyperparameters for the given model.
    """
    logger.info(f"Starting hyperparameter tuning for {model_name}...")

    # If the model doesn't support tuning or is LinearRegression, skip
    if model_name == "LinearRegression":
        logger.info("LinearRegression requires no tuning. Skipping.")
        return {}

    # Get the uninstantiated model class/factory from model_selection
    from model_selection import get_model_instances

    def objective(trial: optuna.Trial) -> float:
        # 1. Get params for this trial
        params = get_search_space(model_name, trial)

        # 2. Instantiate model with params
        base_models = get_model_instances()
        model = base_models[model_name]
        if hasattr(model, "set_params"):
            model.set_params(**params)

        # 3. Cross-validate
        kf = KFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

        # Scikit-learn returns negative MSE
        scores = cross_val_score(
            model, X, y, cv=kf, scoring="neg_root_mean_squared_error", n_jobs=1
        )

        # 4. Return RMSE to minimize
        rmse = -np.mean(scores)
        return rmse

    study = optuna.create_study(
        direction=OPTUNA_DIRECTION,
        sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE),
    )

    study.optimize(
        objective,
        n_trials=OPTUNA_N_TRIALS,
        timeout=OPTUNA_TIMEOUT_SECONDS,
        show_progress_bar=False,
    )

    logger.info(f"Tuning complete. Best RMSE: {study.best_value:.4f}")
    logger.info(f"Best params: {study.best_params}")

    return study.best_params
