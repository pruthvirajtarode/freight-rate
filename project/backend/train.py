"""
train.py — Main training orchestration script.

Executes the full machine learning pipeline:
1. Load data
2. EDA & visualisations
3. Preprocessing & Feature Engineering
4. Model Comparison
5. Hyperparameter Tuning
6. Final Model Training
7. Evaluation & Chart Generation
8. Artefact Saving
"""

import joblib
from config import (
    BEST_MODEL_PATH,
    FEATURE_ENGINEER_PATH,
    FEATURE_LIST_PATH,
    METRICS_PATH,
    MODEL_COMPARISON_PATH,
    MODELS_DIR,
    PREPROCESSOR_PATH,
    TRAIN_FILE,
)
from evaluate import evaluate_predictions
from feature_engineering import extract_features
from hyperparameter_tuning import tune_hyperparameters
from model_selection import compare_models, train_final_model
from preprocessing import preprocess_data
from sklearn.model_selection import train_test_split
from utils import (
    ensure_directory,
    get_logger,
    print_section,
    safe_read_csv,
    save_json,
    timeit,
)
from visualization import (
    generate_eda_charts,
    plot_feature_importance,
    plot_prediction_scatter,
    plot_residuals,
    plot_shap_summary,
)

logger = get_logger(__name__)


@timeit
def run_training_pipeline() -> None:
    """Run the complete end-to-end training pipeline."""
    ensure_directory(MODELS_DIR)

    # -----------------------------------------------------------------------
    # 1. Load Data
    # -----------------------------------------------------------------------
    print_section("1. Loading Data")
    df = safe_read_csv(TRAIN_FILE)
    logger.info(f"Loaded training data: {df.shape}")

    # Generate EDA charts on raw data
    generate_eda_charts(df)

    # Split into train/validation for final holdout evaluation
    # We do model comparison using CV on train_set, then evaluate final on val_set
    train_df, val_df = train_test_split(df, test_size=0.15, random_state=42)
    logger.info(f"Train split: {train_df.shape}, Val split: {val_df.shape}")

    # -----------------------------------------------------------------------
    # 2. Preprocessing
    # -----------------------------------------------------------------------
    print_section("2. Preprocessing")
    X_train_clean, y_train, preprocessor = preprocess_data(train_df, is_training=True)
    X_val_clean, y_val, _ = preprocess_data(
        val_df, is_training=False, preprocessor=preprocessor
    )

    # Save preprocessor
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    logger.info(f"Saved preprocessor to {PREPROCESSOR_PATH}")

    # -----------------------------------------------------------------------
    # 3. Feature Engineering
    # -----------------------------------------------------------------------
    print_section("3. Feature Engineering")
    X_train_eng, X_val_eng, _, engineer = extract_features(X_train_clean, X_val_clean)

    # Save engineer
    joblib.dump(engineer, FEATURE_ENGINEER_PATH)
    logger.info(f"Saved feature engineer to {FEATURE_ENGINEER_PATH}")

    feature_names = list(X_train_eng.columns)
    save_json(feature_names, FEATURE_LIST_PATH)
    logger.info(f"Generated {len(feature_names)} features.")

    # -----------------------------------------------------------------------
    # 4. Model Comparison
    # -----------------------------------------------------------------------
    print_section("4. Model Comparison")
    best_model_name, comparison_results = compare_models(X_train_eng, y_train)
    save_json(comparison_results, MODEL_COMPARISON_PATH)

    # -----------------------------------------------------------------------
    # 5. Hyperparameter Tuning
    # -----------------------------------------------------------------------
    print_section(f"5. Hyperparameter Tuning ({best_model_name})")
    best_params = tune_hyperparameters(best_model_name, X_train_eng, y_train)

    # -----------------------------------------------------------------------
    # 6. Final Model Training
    # -----------------------------------------------------------------------
    print_section("6. Final Model Training")
    # For the final model, we train on the full training set (X_train_eng, y_train)
    # The holdout (X_val_eng) is purely for plotting and final metric logging.
    final_model = train_final_model(best_model_name, X_train_eng, y_train, best_params)

    joblib.dump(final_model, BEST_MODEL_PATH)
    logger.info(f"Saved final model to {BEST_MODEL_PATH}")

    # -----------------------------------------------------------------------
    # 7. Evaluation & Charts
    # -----------------------------------------------------------------------
    print_section("7. Evaluation & Visualization")
    # Predict on holdout validation set
    y_pred_val = final_model.predict(X_val_eng)

    assert y_val is not None, "Validation target y_val is missing!"
    metrics = evaluate_predictions(y_val, y_pred_val, prefix="val_")

    # Add model metadata
    metrics["best_model"] = best_model_name
    save_json(metrics, METRICS_PATH)

    # Generate Charts
    plot_feature_importance(final_model, feature_names)
    plot_residuals(y_val.values, y_pred_val)
    plot_prediction_scatter(y_val.values, y_pred_val)

    # SHAP takes a while, so we sample
    X_sample = X_val_eng.sample(n=min(500, len(X_val_eng)), random_state=42)
    plot_shap_summary(final_model, X_sample)

    logger.info("Training pipeline completed successfully.")


if __name__ == "__main__":
    run_training_pipeline()
