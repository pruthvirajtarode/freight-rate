"""
routes.py — FastAPI routes for the Freight Rate Prediction Platform.

Defines endpoints for prediction, training triggers, downloading files,
and fetching metrics.
"""

import json
from io import StringIO

import joblib
import numpy as np
import pandas as pd
from config import (
    BEST_MODEL_PATH,
    DECEMBER_PREDICTIONS_PATH,
    FEATURE_ENGINEER_PATH,
    FEATURE_LIST_PATH,
    METRICS_PATH,
    MODEL_COMPARISON_PATH,
    PREPROCESSOR_PATH,
    VALIDATION_PREDICTIONS_PATH,
)
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from preprocessing import preprocess_data
from pydantic import BaseModel
from utils import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Module-level cached artifacts to avoid reloading on every request
_MODEL = None
_PREPROCESSOR = None
_ENGINEER = None
_FEATURE_NAMES = None


def _ensure_artifacts_loaded():
    """Load model artifacts into module-level variables if available."""
    global _MODEL, _PREPROCESSOR, _ENGINEER, _FEATURE_NAMES
    if _MODEL is not None:
        return
    try:
        if BEST_MODEL_PATH.exists():
            _MODEL = joblib.load(BEST_MODEL_PATH)
        if PREPROCESSOR_PATH.exists():
            _PREPROCESSOR = joblib.load(PREPROCESSOR_PATH)
        if FEATURE_ENGINEER_PATH.exists():
            _ENGINEER = joblib.load(FEATURE_ENGINEER_PATH)
        if FEATURE_LIST_PATH.exists():
            with open(FEATURE_LIST_PATH, "r") as f:
                _FEATURE_NAMES = json.load(f)
        logger.info("Model artifacts loaded into memory.")
    except Exception as e:
        logger.warning(f"Failed to load some artifacts at startup: {e}")

# ---------------------------------------------------------------------------
# Pydantic Models for Validation
# ---------------------------------------------------------------------------


class SinglePredictionRequest(BaseModel):
    pickup: str
    delivery: str
    distance: float
    equipment: str
    weight: float
    date: str
    pickup_lat: float = 0.0
    pickup_lon: float = 0.0
    delivery_lat: float = 0.0
    delivery_lon: float = 0.0
    market_index: float | None = None
    quote_signal: float | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/health")
def health_check():
    """Check API status and model availability."""
    # Try to use cached model state when possible
    try:
        _ensure_artifacts_loaded()
    except Exception:
        pass
    model_ready = _MODEL is not None or BEST_MODEL_PATH.exists()
    return {"status": "online", "model_loaded": model_ready}


@router.get("/metrics")
def get_metrics():
    """Return model performance metrics."""
    if not METRICS_PATH.exists():
        raise HTTPException(
            status_code=404, detail="Metrics not found. Train model first."
        )
    with open(METRICS_PATH, "r") as f:
        metrics = json.load(f)
    return metrics


@router.get("/models/compare")
def get_model_comparison():
    """Return model comparison results."""
    if not MODEL_COMPARISON_PATH.exists():
        raise HTTPException(status_code=404, detail="Comparison data not found.")
    with open(MODEL_COMPARISON_PATH, "r") as f:
        data = json.load(f)
    return data


@router.post("/predict/single")
def predict_single(req: SinglePredictionRequest):
    """Predict freight rate for a single load."""
    # Ensure artifacts are loaded (cached) to reduce overhead
    if _MODEL is None and not BEST_MODEL_PATH.exists():
        raise HTTPException(status_code=503, detail="Model not trained yet.")
    try:
        _ensure_artifacts_loaded()
        model = _MODEL
        preprocessor = _PREPROCESSOR
        engineer = _ENGINEER
        feature_names = _FEATURE_NAMES

        # Convert request to DataFrame
        df = pd.DataFrame([req.dict()])

        # Preprocess & Feature Engineer
        df_clean, _, _ = preprocess_data(
            df, is_training=False, preprocessor=preprocessor
        )
        df_eng = engineer.transform(df_clean)

        # Align columns
        for col in feature_names:
            if col not in df_eng.columns:
                df_eng[col] = 0.0
        df_eng = df_eng[feature_names]

        # Predict
        prediction = model.predict(df_eng)[0]

        return {"predicted_rate": round(float(prediction), 2)}

    except Exception as e:
        logger.error(f"Prediction error: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/batch")
async def predict_batch(file: UploadFile = File(...)):
    """Upload a CSV file and get predictions back."""
    if not BEST_MODEL_PATH.exists():
        raise HTTPException(status_code=503, detail="Model not trained yet.")

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))

        _ensure_artifacts_loaded()
        model = _MODEL
        preprocessor = _PREPROCESSOR
        engineer = _ENGINEER
        feature_names = _FEATURE_NAMES

        # Preprocess & Feature Engineer
        df_clean, _, _ = preprocess_data(
            df, is_training=False, preprocessor=preprocessor
        )
        df_eng = engineer.transform(df_clean)

        for col in feature_names:
            if col not in df_eng.columns:
                df_eng[col] = 0.0
        df_eng = df_eng[feature_names]

        predictions = model.predict(df_eng)
        df["predicted_rate"] = np.round(predictions, 2)

        # Return as JSON for frontend table rendering
        return {"data": df.to_dict(orient="records")}

    except Exception as e:
        logger.error(f"Batch prediction error: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train")
def trigger_training(background_tasks: BackgroundTasks):
    """Trigger the training pipeline in the background."""
    from train import run_training_pipeline

    background_tasks.add_task(run_training_pipeline)
    return {"message": "Training started in background."}


@router.get("/download/validation")
def download_validation_predictions():
    """Download the validation_predictions.csv"""
    if not VALIDATION_PREDICTIONS_PATH.exists():
        raise HTTPException(
            status_code=404, detail="Validation predictions not generated."
        )
    return FileResponse(
        VALIDATION_PREDICTIONS_PATH,
        media_type="text/csv",
        filename="validation_predictions.csv",
    )


@router.get("/download/december")
def download_december_predictions():
    """Download the december_chart_predictions.csv"""
    if not DECEMBER_PREDICTIONS_PATH.exists():
        raise HTTPException(
            status_code=404, detail="December predictions not generated."
        )
    return FileResponse(
        DECEMBER_PREDICTIONS_PATH,
        media_type="text/csv",
        filename="december_chart_predictions.csv",
    )
