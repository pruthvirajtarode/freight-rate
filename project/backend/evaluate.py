"""
evaluate.py — Evaluation pipeline.

Calculates metrics and prepares data structures for visualization.
"""

import numpy as np
import pandas as pd
from utils import compute_metrics, get_logger

logger = get_logger(__name__)


def evaluate_predictions(
    y_true: pd.Series, y_pred: np.ndarray, prefix: str = ""
) -> dict[str, float]:
    """
    Wrapper around compute_metrics that logs the result.
    """
    logger.info(f"Evaluating predictions ({len(y_true)} samples)...")
    metrics = compute_metrics(y_true.values, y_pred, prefix=prefix)

    logger.info("Evaluation Results:")
    for k, v in metrics.items():
        logger.info(f"  {k}: {v:.4f}")

    return metrics


def calculate_residuals(y_true: pd.Series, y_pred: np.ndarray) -> pd.DataFrame:
    """
    Calculate residuals for plotting.
    Returns a DataFrame with true, predicted, and residual values.
    """
    df = pd.DataFrame(
        {"true": y_true.values, "predicted": y_pred, "residual": y_true.values - y_pred}
    )
    return df
