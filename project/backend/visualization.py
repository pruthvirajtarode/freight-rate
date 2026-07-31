"""
visualization.py — Data visualization generation.

Creates static PNG charts for EDA and model evaluation, which are
served by the FastAPI backend to the frontend.
"""

from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

# Use Agg backend for headless server environment
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import shap
from config import CHARTS_DIR
from utils import ensure_directory, get_logger, timeit

logger = get_logger(__name__)

# Set style
sns.set_theme(style="whitegrid", context="talk")


@timeit
def plot_feature_importance(
    model: Any,
    feature_names: list[str],
    top_n: int = 15,
    filename: str = "feature_importance.png",
) -> Path:
    """
    Plot feature importance from a tree-based model.
    """
    out_path = ensure_directory(CHARTS_DIR) / filename

    if not hasattr(model, "feature_importances_"):
        logger.warning(
            f"Model {type(model).__name__} lacks feature_importances_. Cannot plot."
        )
        return out_path

    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:top_n]

    plt.figure(figsize=(10, 8))
    feature_labels = [feature_names[i] for i in indices]
    sns.barplot(
        x=importances[indices],
        y=feature_labels,
        hue=feature_labels,
        palette="viridis",
        legend=False,
    )
    plt.title("Top Feature Importances", pad=20)
    plt.xlabel("Relative Importance")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()

    logger.info(f"Saved feature importance plot to {out_path}")
    return out_path


@timeit
def plot_shap_summary(
    model: Any, X_sample: pd.DataFrame, filename: str = "shap_summary.png"
) -> Path:
    """
    Generate SHAP summary plot.
    """
    out_path = ensure_directory(CHARTS_DIR) / filename

    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample)

        plt.figure(figsize=(12, 8))
        shap.summary_plot(shap_values, X_sample, show=False)
        plt.tight_layout()
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close()
        logger.info(f"Saved SHAP summary to {out_path}")

    except Exception as e:
        logger.error(f"Failed to generate SHAP plot: {e}")

    return out_path


@timeit
def plot_residuals(
    y_true: np.ndarray, y_pred: np.ndarray, filename: str = "residuals.png"
) -> Path:
    """
    Plot residuals (prediction error).
    """
    out_path = ensure_directory(CHARTS_DIR) / filename
    residuals = y_true - y_pred

    _fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Scatter plot
    ax1.scatter(y_pred, residuals, alpha=0.3, color="#3498db")
    ax1.axhline(y=0, color="r", linestyle="--")
    ax1.set_xlabel("Predicted Rate ($)")
    ax1.set_ylabel("Residual Error ($)")
    ax1.set_title("Residuals vs Predicted")

    # Histogram
    sns.histplot(residuals, bins=50, kde=True, ax=ax2, color="#2ecc71")
    ax2.set_xlabel("Residual Error ($)")
    ax2.set_title("Residual Distribution")

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()

    logger.info(f"Saved residuals plot to {out_path}")
    return out_path


@timeit
def plot_prediction_scatter(
    y_true: np.ndarray, y_pred: np.ndarray, filename: str = "prediction_scatter.png"
) -> Path:
    """
    Plot actual vs predicted scatter plot.
    """
    out_path = ensure_directory(CHARTS_DIR) / filename

    plt.figure(figsize=(8, 8))
    plt.scatter(y_true, y_pred, alpha=0.3, color="#9b59b6")

    # Ideal line
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    plt.plot([min_val, max_val], [min_val, max_val], "r--", lw=2)

    plt.xlabel("Actual Rate ($)")
    plt.ylabel("Predicted Rate ($)")
    plt.title("Actual vs Predicted Freight Rates")

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()

    logger.info(f"Saved prediction scatter to {out_path}")
    return out_path


@timeit
def generate_eda_charts(df: pd.DataFrame) -> None:
    """
    Generate standard EDA charts from the raw training dataframe.
    """
    ensure_directory(CHARTS_DIR)

    # 1. Target Distribution
    if "posted_rate" in df.columns:
        plt.figure(figsize=(10, 6))
        sns.histplot(df["posted_rate"], bins=50, kde=True, color="#e74c3c")
        plt.title("Distribution of Posted Rates")
        plt.xlabel("Rate ($)")
        plt.savefig(
            CHARTS_DIR / "target_distribution.png", dpi=150, bbox_inches="tight"
        )
        plt.close()

    # 2. Correlation Heatmap
    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty:
        plt.figure(figsize=(12, 10))
        corr = numeric_df.corr()
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(
            corr,
            mask=mask,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            vmin=-1,
            vmax=1,
            center=0,
            square=True,
            linewidths=0.5,
        )
        plt.title("Feature Correlation Matrix")
        plt.savefig(
            CHARTS_DIR / "correlation_heatmap.png", dpi=150, bbox_inches="tight"
        )
        plt.close()

    logger.info("EDA charts generated.")
