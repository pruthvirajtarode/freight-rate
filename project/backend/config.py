"""
config.py — Central configuration for the Freight Rate Prediction Platform.

All paths, hyperparameter search spaces, feature lists, and model settings
are defined here to ensure a single source of truth across the codebase.
"""

from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Base paths
# ---------------------------------------------------------------------------
_THIS_DIR: Path = Path(__file__).resolve().parent
# Support both layouts:
# 1) Monorepo image: /app/backend/config.py -> BASE_DIR=/app
# 2) Backend-only image: /app/config.py -> BASE_DIR=/app
BASE_DIR: Path = _THIS_DIR.parent if _THIS_DIR.name == "backend" else _THIS_DIR
DATA_DIR: Path = BASE_DIR / "data"
BACKEND_DIR: Path = BASE_DIR / "backend"
MODELS_DIR: Path = BACKEND_DIR / "models"
CHARTS_DIR: Path = BACKEND_DIR / "charts"
REPORTS_DIR: Path = BACKEND_DIR / "reports"

if not MODELS_DIR.exists():
    # Backend-only image stores artifacts directly under /app/models.
    BACKEND_DIR = BASE_DIR
    MODELS_DIR = BASE_DIR / "models"
    CHARTS_DIR = BASE_DIR / "charts"
    REPORTS_DIR = BASE_DIR / "reports"

# ---------------------------------------------------------------------------
# Data files
# ---------------------------------------------------------------------------
TRAIN_FILE: Path = DATA_DIR / "train-test.csv"
VALIDATION_FILE: Path = DATA_DIR / "validation.csv"
TEMPLATE_FILE: Path = DATA_DIR / "validation-predictions-template.csv"
DECEMBER_FILE: Path = DATA_DIR / "december-chart-inputs.csv"

# ---------------------------------------------------------------------------
# Output artefacts
# ---------------------------------------------------------------------------
BEST_MODEL_PATH: Path = MODELS_DIR / "best_model.pkl"
PREPROCESSOR_PATH: Path = MODELS_DIR / "preprocessor.pkl"
FEATURE_ENGINEER_PATH: Path = MODELS_DIR / "feature_engineer.pkl"
FEATURE_LIST_PATH: Path = MODELS_DIR / "feature_list.json"
METRICS_PATH: Path = MODELS_DIR / "metrics.json"
CITY_ENCODER_PATH: Path = MODELS_DIR / "city_target_encoders.pkl"
MODEL_COMPARISON_PATH: Path = MODELS_DIR / "model_comparison.json"
SHAP_VALUES_PATH: Path = MODELS_DIR / "shap_values.pkl"

VALIDATION_PREDICTIONS_PATH: Path = BACKEND_DIR / "validation_predictions.csv"
DECEMBER_PREDICTIONS_PATH: Path = BACKEND_DIR / "december_chart_predictions.csv"

# ---------------------------------------------------------------------------
# Dataset schema
# ---------------------------------------------------------------------------
TARGET_COLUMN: str = "posted_rate"
ID_COLUMN: str = "load_id"
DATE_COLUMN: str = "date"

CATEGORICAL_COLUMNS: list[str] = ["equipment", "pickup", "delivery"]
NUMERIC_COLUMNS: list[str] = [
    "distance",
    "weight",
    "market_index",
    "quote_signal",
    "pickup_lat",
    "pickup_lon",
    "delivery_lat",
    "delivery_lon",
]
EQUIPMENT_CATEGORIES: list[str] = ["Dry Van", "Flatbed", "Reefer"]

# ---------------------------------------------------------------------------
# Feature engineering settings
# ---------------------------------------------------------------------------
N_DISTANCE_BINS: int = 10
N_WEIGHT_BINS: int = 8
# IQR multiplier for outlier clipping of target variable
OUTLIER_IQR_MULTIPLIER: float = 4.0

# City target-encoding smoothing factor (regularisation)
TARGET_ENCODE_SMOOTH: float = 20.0

# ---------------------------------------------------------------------------
# December chart imputation defaults (Lexington → Fort Wayne, Dry Van)
# Derived from training data medians for this route.
# ---------------------------------------------------------------------------
DECEMBER_DEFAULTS: dict[str, Any] = {
    "pickup": "Lexington",
    "delivery": "Fort Wayne",
    "pickup_lat": 36.99152,
    "pickup_lon": -84.99876,
    "delivery_lat": 41.31561,
    "delivery_lon": -85.36206,
    "market_index": 1.044,  # median for this route
    "quote_signal": 2.011,  # median for this route
}

# ---------------------------------------------------------------------------
# Cross-validation
# ---------------------------------------------------------------------------
CV_FOLDS: int = 5
RANDOM_STATE: int = 42

# ---------------------------------------------------------------------------
# Optuna HPO settings
# ---------------------------------------------------------------------------
OPTUNA_N_TRIALS: int = 15
OPTUNA_TIMEOUT_SECONDS: int = 300  # 5-minute hard cap
OPTUNA_DIRECTION: str = "minimize"  # minimise RMSE

# ---------------------------------------------------------------------------
# Models to train and compare
# ---------------------------------------------------------------------------
MODELS_TO_COMPARE: list[str] = [
    "LinearRegression",
    "RandomForest",
    "ExtraTrees",
    "GradientBoosting",
    "XGBoost",
    "LightGBM",
    "CatBoost",
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# ---------------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------------
API_TITLE: str = "Freight Rate Prediction API"
API_DESCRIPTION: str = (
    "Production-ready REST API for the Freight Rate Prediction Platform. "
    "Provides endpoints for training, prediction, evaluation, and data exploration."
)
API_VERSION: str = "1.0.0"
API_HOST: str = "0.0.0.0"
API_PORT: int = 8000
CORS_ORIGINS: list[str] = ["*"]
