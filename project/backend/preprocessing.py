"""
preprocessing.py — Data cleaning and preprocessing pipeline.

Handles missing values, data type casting, date parsing, anomaly fixing
(e.g., negative weights), and ordinal/target encoding.
"""

import pandas as pd
from config import (
    CATEGORICAL_COLUMNS,
    DATE_COLUMN,
    DECEMBER_DEFAULTS,
    EQUIPMENT_CATEGORIES,
    ID_COLUMN,
    NUMERIC_COLUMNS,
    TARGET_COLUMN,
    TARGET_ENCODE_SMOOTH,
)
from sklearn.base import BaseEstimator, TransformerMixin
from utils import get_logger, timeit

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Core Preprocessing Transformer
# ---------------------------------------------------------------------------


class FreightDataPreprocessor(BaseEstimator, TransformerMixin):
    """
    Scikit-learn compatible transformer for end-to-end data cleaning.
    Learns imputation medians and target encodings during fit().
    Applies them consistently during transform().
    """

    def __init__(self, is_training: bool = True):
        self.is_training = is_training

        # State learned during fit()
        self.route_weight_medians_: dict[str, float] = {}
        self.global_weight_median_: float = 30000.0

        self.month_market_medians_: dict[int, float] = {}
        self.global_market_median_: float = 1.0

        # Target encoders map: column_name -> {category: encoded_value}
        self.target_encoders_: dict[str, dict[str, float]] = {}
        self.global_target_mean_: float = 0.0

    @timeit
    def fit(
        self, X: pd.DataFrame, y: pd.Series | None = None
    ) -> "FreightDataPreprocessor":
        """
        Learn imputation statistics and target encodings from training data.
        """
        logger.info(f"Fitting preprocessor on {len(X)} rows...")
        X = X.copy()

        # 1. Parse dates to extract month for market_index imputation
        if DATE_COLUMN in X.columns and not pd.api.types.is_datetime64_any_dtype(
            X[DATE_COLUMN]
        ):
            dates = pd.to_datetime(X[DATE_COLUMN])
            months = dates.dt.month
        elif DATE_COLUMN in X.columns:
            months = X[DATE_COLUMN].dt.month
        else:
            months = pd.Series([1] * len(X), index=X.index)

        # 2. Fix negative weights before calculating medians
        if "weight" in X.columns:
            X["weight"] = X["weight"].abs()

            # Learn weight medians per route (pickup -> delivery)
            if "pickup" in X.columns and "delivery" in X.columns:
                X["route"] = X["pickup"] + "->" + X["delivery"]
                self.route_weight_medians_ = (
                    X.groupby("route")["weight"].median().to_dict()
                )

            self.global_weight_median_ = X["weight"].median()

        # 3. Learn market_index medians per month
        if "market_index" in X.columns:
            X["month_tmp"] = months
            self.month_market_medians_ = (
                X.groupby("month_tmp")["market_index"].median().to_dict()
            )
            self.global_market_median_ = X["market_index"].median()
            X.drop(columns=["month_tmp"], inplace=True)

        # 4. Target Encoding for high-cardinality categoricals (pickup, delivery, route)
        if y is not None and self.is_training:
            self.global_target_mean_ = y.mean()

            X["route"] = X["pickup"] + "->" + X["delivery"]
            cols_to_encode = ["pickup", "delivery", "route"]

            for col in cols_to_encode:
                if col in X.columns:
                    self.target_encoders_[col] = self._compute_target_encoding(
                        X[col], y, self.global_target_mean_, TARGET_ENCODE_SMOOTH
                    )
            X.drop(columns=["route"], inplace=True, errors="ignore")

        return self

    @timeit
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Apply cleaning, imputation, and encoding to new data.
        """
        logger.info(f"Transforming data ({len(X)} rows)...")
        X = X.copy()

        # --- A. Anomaly Fixing ---
        if "weight" in X.columns:
            # Fix negative weights
            X["weight"] = X["weight"].abs()

        # --- B. December Chart Special Handling ---
        # If this is the december chart file, it lacks some columns. We inject defaults.
        self._inject_missing_december_columns(X)

        # --- C. Date Parsing & Extraction ---
        if DATE_COLUMN in X.columns:
            # Convert to datetime
            X[DATE_COLUMN] = pd.to_datetime(X[DATE_COLUMN])

            # Extract basic components
            X["month"] = X[DATE_COLUMN].dt.month
            X["day"] = X[DATE_COLUMN].dt.day
            X["dayofweek"] = X[DATE_COLUMN].dt.dayofweek
            X["week"] = X[DATE_COLUMN].dt.isocalendar().week.astype(int)
            X["is_weekend"] = (X["dayofweek"] >= 5).astype(int)
            X["quarter"] = X[DATE_COLUMN].dt.quarter

        # --- D. Imputation ---
        # 1. Weight: Route median -> Global median
        if "weight" in X.columns and X["weight"].isnull().any():
            if "pickup" in X.columns and "delivery" in X.columns:
                X["route"] = X["pickup"] + "->" + X["delivery"]
                # Map from route medians
                imputed_weights = X["route"].map(self.route_weight_medians_)
                # Fallback to global
                imputed_weights = imputed_weights.fillna(self.global_weight_median_)
                X["weight"] = X["weight"].fillna(imputed_weights)
                X.drop(columns=["route"], inplace=True)
            else:
                X["weight"] = X["weight"].fillna(self.global_weight_median_)

        # 2. Market Index: Month median -> Global median
        if "market_index" in X.columns and X["market_index"].isnull().any():
            if "month" in X.columns:
                imputed_market = X["month"].map(self.month_market_medians_)
                imputed_market = imputed_market.fillna(self.global_market_median_)
                X["market_index"] = X["market_index"].fillna(imputed_market)
            else:
                X["market_index"] = X["market_index"].fillna(self.global_market_median_)

        # 3. Any remaining numerics get a simple median fill (safety net)
        for col in NUMERIC_COLUMNS:
            if col in X.columns and X[col].isnull().any():
                logger.warning(f"Unexpected NaNs in {col}. Filling with 0.")
                X[col] = X[col].fillna(0.0)

        # --- E. Categorical Encoding ---
        # 1. Ordinal Encode Equipment
        if "equipment" in X.columns:
            # Dry Van=0, Flatbed=1, Reefer=2
            eq_map = {eq: idx for idx, eq in enumerate(EQUIPMENT_CATEGORIES)}
            X["equipment_encoded"] = X["equipment"].map(eq_map).fillna(0).astype(int)

        # 2. Target Encode Cities & Route
        if "pickup" in X.columns and "delivery" in X.columns:
            X["route"] = X["pickup"] + "->" + X["delivery"]

            for col in ["pickup", "delivery", "route"]:
                if col in self.target_encoders_:
                    mapping = self.target_encoders_[col]
                    new_col_name = f"{col}_encoded"
                    # Map, fallback to global mean for unseen categories
                    X[new_col_name] = (
                        X[col].map(mapping).fillna(self.global_target_mean_)
                    )

            X.drop(columns=["route"], inplace=True)

        # Drop original categoricals (except ID/Date if needed later, but we usually drop them before modelling)
        cols_to_drop = [c for c in CATEGORICAL_COLUMNS if c in X.columns]

        # Also drop ID and Date columns since models cannot process strings/datetimes directly
        if ID_COLUMN in X.columns:
            cols_to_drop.append(ID_COLUMN)
        if DATE_COLUMN in X.columns:
            cols_to_drop.append(DATE_COLUMN)

        X.drop(columns=cols_to_drop, inplace=True, errors="ignore")

        return X

    def _compute_target_encoding(
        self, series: pd.Series, target: pd.Series, global_mean: float, smooth: float
    ) -> dict[str, float]:
        """
        Compute smoothed target encoding to prevent overfitting on rare categories.
        formula: (count * cat_mean + smooth * global_mean) / (count + smooth)
        """
        stats = target.groupby(series).agg(["count", "mean"])
        smoothed = (stats["count"] * stats["mean"] + smooth * global_mean) / (
            stats["count"] + smooth
        )
        return smoothed.to_dict()

    def _inject_missing_december_columns(self, X: pd.DataFrame) -> None:
        """
        The december chart inputs lack lat/lon, market_index, and quote_signal.
        Inject them from defaults if missing.
        """
        cols_needed = [
            "pickup_lat",
            "pickup_lon",
            "delivery_lat",
            "delivery_lon",
            "market_index",
            "quote_signal",
        ]
        for col in cols_needed:
            if col not in X.columns:
                logger.debug(f"Injecting missing column {col} for December inference.")
                X[col] = DECEMBER_DEFAULTS.get(col, 0.0)


# ---------------------------------------------------------------------------
# Outlier Removal (Training only)
# ---------------------------------------------------------------------------


def remove_target_outliers(
    X: pd.DataFrame, y: pd.Series, iqr_multiplier: float = 4.0
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Remove extreme outliers in the target variable using IQR method.
    Only applied to training data.
    """
    logger.info(f"Original shape before outlier removal: {X.shape}")

    q1 = y.quantile(0.25)
    q3 = y.quantile(0.75)
    iqr = q3 - q1

    lower_bound = max(0, q1 - (iqr_multiplier * iqr))  # Rates can't be negative
    upper_bound = q3 + (iqr_multiplier * iqr)

    mask = (y >= lower_bound) & (y <= upper_bound)

    X_clean = X[mask].copy()
    y_clean = y[mask].copy()

    removed = len(X) - len(X_clean)
    logger.info(
        f"Removed {removed} rows ({removed / len(X) * 100:.2f}%) outside bounds [{lower_bound:.1f}, {upper_bound:.1f}]"
    )

    return X_clean, y_clean


# ---------------------------------------------------------------------------
# Pipeline Entry Point
# ---------------------------------------------------------------------------


def preprocess_data(
    df: pd.DataFrame,
    is_training: bool = True,
    preprocessor: FreightDataPreprocessor | None = None,
) -> tuple[pd.DataFrame, pd.Series | None, FreightDataPreprocessor]:
    """
    Main entry point for data preprocessing.
    """
    df = df.copy()

    # Extract target
    y = None
    if TARGET_COLUMN in df.columns:
        y = df.pop(TARGET_COLUMN)

    # Remove outliers if training
    if is_training and y is not None:
        from config import OUTLIER_IQR_MULTIPLIER

        df, y = remove_target_outliers(df, y, iqr_multiplier=OUTLIER_IQR_MULTIPLIER)

    # Fit/Transform preprocessor
    if is_training:
        preprocessor = FreightDataPreprocessor(is_training=True)
        preprocessor.fit(df, y)
    elif preprocessor is None:
        raise ValueError("Preprocessor must be provided if is_training is False")

    df_processed = preprocessor.transform(df)

    return df_processed, y, preprocessor
