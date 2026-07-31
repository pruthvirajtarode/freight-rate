"""
feature_engineering.py — Feature engineering pipeline.

Constructs derived features, interaction terms, geographical distances,
and cyclical time encodings.
"""

import numpy as np
import pandas as pd
from config import N_DISTANCE_BINS, N_WEIGHT_BINS
from sklearn.base import BaseEstimator, TransformerMixin
from utils import get_logger, timeit

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Geographical Utilities
# ---------------------------------------------------------------------------


def haversine_distance(
    lat1: pd.Series, lon1: pd.Series, lat2: pd.Series, lon2: pd.Series
) -> pd.Series:
    """
    Calculate the great circle distance between two points on the earth (in miles).
    Expects coordinates in decimal degrees.
    """
    # Earth radius in miles
    R = 3958.8

    # Convert to radians
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)

    a = (
        np.sin(dphi / 2.0) ** 2
        + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    )
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    return R * c


# ---------------------------------------------------------------------------
# Feature Engineering Transformer
# ---------------------------------------------------------------------------


class FeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Scikit-learn compatible transformer for feature engineering.
    Stateless transformer (does not need to learn from training data,
    only applies logic), except for binning where we could save boundaries,
    but we use simple quantiles or fixed logic if required.
    """

    def __init__(self):
        # We will store quantile bins during fit so they apply identically to validation
        self.distance_bins_: pd.IntervalIndex = None
        self.weight_bins_: pd.IntervalIndex = None

    @timeit
    def fit(self, X: pd.DataFrame, y=None) -> "FeatureEngineer":
        """Learn bin boundaries from training data."""
        logger.info("Fitting FeatureEngineer (learning bins)...")
        if "distance" in X.columns:
            # Drop duplicates to avoid ValueError with qcut if many identical values
            _, bins = pd.qcut(
                X["distance"], q=N_DISTANCE_BINS, retbins=True, duplicates="drop"
            )
            # Widen the outer boundaries slightly to catch unseen test data
            bins[0] = -np.inf
            bins[-1] = np.inf
            self.distance_bins_ = bins

        if "weight" in X.columns:
            _, bins = pd.qcut(
                X["weight"], q=N_WEIGHT_BINS, retbins=True, duplicates="drop"
            )
            bins[0] = -np.inf
            bins[-1] = np.inf
            self.weight_bins_ = bins

        return self

    @timeit
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Create engineered features."""
        logger.info("Applying feature engineering...")
        X = X.copy()

        # 1. Cyclical Time Encodings
        if "month" in X.columns:
            # Month is 1-12
            X["month_sin"] = np.sin(2 * np.pi * X["month"] / 12.0)
            X["month_cos"] = np.cos(2 * np.pi * X["month"] / 12.0)

        if "dayofweek" in X.columns:
            # Day of week is 0-6
            X["dayofweek_sin"] = np.sin(2 * np.pi * X["dayofweek"] / 7.0)
            X["dayofweek_cos"] = np.cos(2 * np.pi * X["dayofweek"] / 7.0)

        # 2. Distance and Geography
        if all(
            c in X.columns
            for c in ["pickup_lat", "pickup_lon", "delivery_lat", "delivery_lon"]
        ):
            X["haversine_dist"] = haversine_distance(
                X["pickup_lat"], X["pickup_lon"], X["delivery_lat"], X["delivery_lon"]
            )

            if "distance" in X.columns:
                # Ratio of reported distance to straight-line distance
                # Guard against div by zero
                X["dist_ratio"] = X["distance"] / (X["haversine_dist"] + 1.0)

        # 3. Binning
        if "distance" in X.columns and self.distance_bins_ is not None:
            X["distance_bin"] = pd.cut(
                X["distance"], bins=self.distance_bins_, labels=False
            )

        if "weight" in X.columns and self.weight_bins_ is not None:
            X["weight_bin"] = pd.cut(X["weight"], bins=self.weight_bins_, labels=False)

        # 4. Interaction Terms
        if "distance" in X.columns:
            if "market_index" in X.columns:
                X["distance_x_market"] = X["distance"] * X["market_index"]
            if "quote_signal" in X.columns:
                X["distance_x_quote"] = X["distance"] * X["quote_signal"]

        if "market_index" in X.columns and "quote_signal" in X.columns:
            X["market_quote_ratio"] = X["market_index"] / (X["quote_signal"] + 1e-5)

        # 5. Drop redundant columns that models shouldn't use directly
        # E.g., raw coordinates (mostly captured by distance and city encodings)
        cols_to_drop = ["pickup_lat", "pickup_lon", "delivery_lat", "delivery_lon"]
        cols_to_drop = [c for c in cols_to_drop if c in X.columns]
        X.drop(columns=cols_to_drop, inplace=True)

        return X


# ---------------------------------------------------------------------------
# Pipeline helper
# ---------------------------------------------------------------------------


def extract_features(
    X_train: pd.DataFrame, X_val: pd.DataFrame = None, X_test: pd.DataFrame = None
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, FeatureEngineer]:
    """
    Apply feature engineering to train, validation, and test sets consistently.
    """
    engineer = FeatureEngineer()

    # Fit and transform train
    X_train_eng = engineer.fit_transform(X_train)

    # Transform others if provided
    X_val_eng = engineer.transform(X_val) if X_val is not None else None
    X_test_eng = engineer.transform(X_test) if X_test is not None else None

    return X_train_eng, X_val_eng, X_test_eng, engineer
