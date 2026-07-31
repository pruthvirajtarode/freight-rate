"""
utils.py — Shared utility functions for the Freight Rate Prediction Platform.

Provides: logging setup, timing decorators, JSON serialisation helpers,
file I/O helpers, and metric computation utilities.
"""

import functools
import json
import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from config import LOG_DATE_FORMAT, LOG_FORMAT, LOG_LEVEL

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def get_logger(name: str, level: str = LOG_LEVEL) -> logging.Logger:
    """
    Return a configured logger for the given module name.

    Args:
        name: Usually ``__name__`` of the calling module.
        level: Logging level string (e.g. "INFO", "DEBUG").

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


# ---------------------------------------------------------------------------
# Timing decorator
# ---------------------------------------------------------------------------


def timeit(func: Callable) -> Callable:
    """
    Decorator that logs the execution time of a function.

    Args:
        func: Function to wrap.

    Returns:
        Wrapped function that logs its duration.
    """
    logger = get_logger(func.__module__)

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"{func.__qualname__} completed in {elapsed:.3f}s")
        return result

    return wrapper


# ---------------------------------------------------------------------------
# JSON serialisation (handles numpy / pandas types)
# ---------------------------------------------------------------------------


class NumpyEncoder(json.JSONEncoder):
    """
    JSON encoder that transparently handles NumPy and Pandas scalar types.
    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        return super().default(obj)


def save_json(data: Any, path: str | Path, indent: int = 2) -> None:
    """
    Persist *data* as a JSON file at *path*.

    Args:
        data: JSON-serialisable object (numpy-safe via :class:`NumpyEncoder`).
        path: Destination file path.
        indent: JSON indentation level.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, cls=NumpyEncoder, indent=indent)


def load_json(path: str | Path) -> Any:
    """
    Load and return JSON data from *path*.

    Args:
        path: Source file path.

    Returns:
        Deserialised Python object.

    Raises:
        FileNotFoundError: If *path* does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    prefix: str = "",
) -> dict[str, float]:
    """
    Compute regression evaluation metrics.

    Args:
        y_true: Ground-truth values.
        y_pred: Predicted values.
        prefix: Optional prefix for metric keys (e.g. ``"val_"``).

    Returns:
        Dictionary with keys: mae, rmse, r2, mape.
    """
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))

    # MAPE — guard against zero targets
    mask = y_true != 0
    mape = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)

    return {
        f"{prefix}mae": round(mae, 4),
        f"{prefix}rmse": round(rmse, 4),
        f"{prefix}r2": round(r2, 6),
        f"{prefix}mape": round(mape, 4),
    }


# ---------------------------------------------------------------------------
# DataFrame helpers
# ---------------------------------------------------------------------------


def safe_read_csv(path: str | Path, **kwargs: Any) -> pd.DataFrame:
    """
    Read a CSV file with error handling and basic validation.

    Args:
        path: Path to the CSV file.
        **kwargs: Additional keyword arguments passed to :func:`pd.read_csv`.

    Returns:
        Loaded :class:`pd.DataFrame`.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If the resulting DataFrame is empty.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    df = pd.read_csv(path, **kwargs)
    if df.empty:
        raise ValueError(f"CSV file is empty: {path}")
    return df


def ensure_directory(path: str | Path) -> Path:
    """
    Create *path* (and any missing parents) if it does not already exist.

    Args:
        path: Directory path to ensure.

    Returns:
        Resolved :class:`Path` object.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Pretty-print helpers
# ---------------------------------------------------------------------------


def print_section(title: str, width: int = 70) -> None:
    """Print a formatted section header to stdout."""
    border = "=" * width
    print(f"\n{border}")
    print(f"  {title}")
    print(border)


def format_metric_table(metrics: dict[str, float]) -> str:
    """
    Format a metrics dictionary as a readable table string.

    Args:
        metrics: Dict of metric_name → value.

    Returns:
        Formatted multi-line string.
    """
    lines = [f"{'Metric':<20} {'Value':>12}", "-" * 34]
    for k, v in metrics.items():
        lines.append(f"{k:<20} {v:>12.4f}")
    return "\n".join(lines)
