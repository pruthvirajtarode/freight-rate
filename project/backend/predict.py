"""
predict.py — Prediction orchestrator.

Loads saved models and preprocessors, runs inference on validation.csv
and december-chart-inputs.csv, and generates the required output files.
"""

from pathlib import Path

import joblib
import pandas as pd
from config import (
    BEST_MODEL_PATH,
    DECEMBER_FILE,
    DECEMBER_PREDICTIONS_PATH,
    FEATURE_ENGINEER_PATH,
    FEATURE_LIST_PATH,
    ID_COLUMN,
    PREPROCESSOR_PATH,
    VALIDATION_FILE,
    VALIDATION_PREDICTIONS_PATH,
)
from preprocessing import preprocess_data
from utils import get_logger, safe_read_csv, timeit

logger = get_logger(__name__)


@timeit
def load_artefacts():
    """Load model, preprocessor, engineer, and feature list."""
    if not BEST_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found at {BEST_MODEL_PATH}. Run train.py first."
        )

    model = joblib.load(BEST_MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    engineer = joblib.load(FEATURE_ENGINEER_PATH)

    import json

    with open(FEATURE_LIST_PATH, "r") as f:
        feature_names = json.load(f)

    return model, preprocessor, engineer, feature_names


@timeit
def predict_file(
    input_path: Path,
    output_path: Path,
    model,
    preprocessor,
    engineer,
    feature_names,
    id_col: str | None = None,
) -> pd.DataFrame:
    """
    Run prediction on a CSV file and save results.
    """
    logger.info(f"Predicting on {input_path.name}...")

    df = safe_read_csv(input_path)

    # Keep IDs for output if specified
    ids = df[id_col].copy() if id_col and id_col in df.columns else None

    # 1. Preprocess
    df_clean, _, _ = preprocess_data(df, is_training=False, preprocessor=preprocessor)

    # 2. Feature Engineering
    df_eng = engineer.transform(df_clean)

    # Ensure column order matches training exactly
    missing_cols = set(feature_names) - set(df_eng.columns)
    if missing_cols:
        logger.warning(f"Missing columns in input: {missing_cols}. Filling with 0.")
        for col in missing_cols:
            df_eng[col] = 0.0

    df_eng = df_eng[feature_names]

    # 3. Predict
    predictions = model.predict(df_eng)

    # 4. Format Output
    if ids is not None:
        out_df = pd.DataFrame({id_col: ids, "predicted_rate": predictions.round(2)})
    else:
        out_df = df.copy()
        if "date" in out_df.columns:
            out_df["date"] = pd.to_datetime(out_df["date"]).dt.strftime('%d-%b-%Y')
        out_df["predicted_rate"] = predictions.round(2)

    # Save
    out_df.to_csv(output_path, index=False)
    logger.info(f"Saved predictions to {output_path}")

    return out_df


@timeit
def run_predictions() -> None:
    """Run required predictions for the assessment."""
    model, preprocessor, engineer, feature_names = load_artefacts()

    # 1. Predict validation.csv
    logger.info("Generating validation predictions...")
    predict_file(
        input_path=VALIDATION_FILE,
        output_path=VALIDATION_PREDICTIONS_PATH,
        model=model,
        preprocessor=preprocessor,
        engineer=engineer,
        feature_names=feature_names,
        id_col=ID_COLUMN,
    )

    # 2. Predict december-chart-inputs.csv
    logger.info("Generating December chart predictions...")
    predict_file(
        input_path=DECEMBER_FILE,
        output_path=DECEMBER_PREDICTIONS_PATH,
        model=model,
        preprocessor=preprocessor,
        engineer=engineer,
        feature_names=feature_names,
        id_col=None,  # Keep all columns for the chart
    )

    # Copy to root folder for submission compliance
    import shutil

    from config import BASE_DIR
    try:
        shutil.copy2(VALIDATION_PREDICTIONS_PATH, BASE_DIR.parent / "validation_predictions.csv")
        shutil.copy2(DECEMBER_PREDICTIONS_PATH, BASE_DIR.parent / "december_chart_predictions.csv")
        logger.info("Copied predictions to root folder for submission.")
    except Exception as e:
        logger.warning(f"Could not copy predictions to root folder: {e}")

    logger.info("All predictions completed successfully.")


if __name__ == "__main__":
    run_predictions()
