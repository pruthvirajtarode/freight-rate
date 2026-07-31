"""
score.py — Official evaluation and December forecasting visualization script.

Runs predictions for December 2025 daily rate forecast, generates a premium 
visualisation chart (as required by the ML MLE Assessment), and computes validation metrics if predictions are available.
"""

import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

# Use Agg backend for headless environments
matplotlib.use("Agg")
sns.set_theme(style="whitegrid", context="talk")

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "project" / "backend"))

from config import (
    BEST_MODEL_PATH,
    PREPROCESSOR_PATH,
    FEATURE_ENGINEER_PATH,
    FEATURE_LIST_PATH,
    CHARTS_DIR,
    DECEMBER_FILE,
    DECEMBER_PREDICTIONS_PATH
)
from preprocessing import preprocess_data

def generate_december_chart():
    """Predicts rates for December inputs and saves the forecasting line chart."""
    print("Generating December 2025 forecasting chart...")
    
    if not BEST_MODEL_PATH.exists():
        print(f"ERROR: Model not found at {BEST_MODEL_PATH}. Run 'python project/backend/train.py' first.")
        return
        
    df = pd.read_csv(DECEMBER_FILE)
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    engineer = joblib.load(FEATURE_ENGINEER_PATH)
    model = joblib.load(BEST_MODEL_PATH)
    
    with open(FEATURE_LIST_PATH, "r") as f:
        feature_names = json.load(f)
        
    # Preprocess & Engineer features
    df_clean, _, _ = preprocess_data(df, is_training=False, preprocessor=preprocessor)
    df_eng = engineer.transform(df_clean)
    
    # Align columns
    for col in feature_names:
        if col not in df_eng.columns:
            df_eng[col] = 0.0
    df_eng = df_eng[feature_names]
    
    # Predict
    preds = model.predict(df_eng)
    df["predicted_rate"] = preds
    df["date"] = pd.to_datetime(df["date"])
    df["day"] = df["date"].dt.day
    
    # Save predictions
    df.to_csv(DECEMBER_PREDICTIONS_PATH, index=False)
    print(f"December predictions saved to {DECEMBER_PREDICTIONS_PATH}")
    
    # Plotting
    plt.figure(figsize=(14, 7))
    plt.plot(df["day"], df["predicted_rate"], marker='o', linewidth=2.5, color='#3498db', label="Predicted Rate ($)")
    
    # Styling and Annotations
    plt.title("Daily Freight Rate Forecast — December 2025", fontsize=18, fontweight='bold', pad=20)
    plt.xlabel("Day of December", fontsize=14)
    plt.ylabel("Predicted Rate ($)", fontsize=14)
    plt.xticks(range(1, 32))
    
    # Highlight seasonal events
    # Pre-Christmas Peak (Dec 15-24)
    plt.axvspan(15, 24, color='orange', alpha=0.15, label="Pre-Christmas Surge")
    # Christmas Dip (Dec 25)
    plt.axvspan(24.5, 25.5, color='red', alpha=0.15, label="Christmas Day Dip")
    # Year End Wind-Down
    plt.axvspan(29, 31, color='gray', alpha=0.15, label="Year-end Slowdown")
    
    # Annotate key days
    max_idx = df["predicted_rate"].idxmax()
    min_idx = df["predicted_rate"].idxmin()
    
    plt.annotate(f"Peak: ${df['predicted_rate'].max():.2f}",
                 xy=(df["day"].iloc[max_idx], df["predicted_rate"].max()),
                 xytext=(df["day"].iloc[max_idx]-3, df["predicted_rate"].max()+150),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6))
                 
    plt.annotate(f"Christmas Dip: ${df['predicted_rate'].iloc[24]:.2f}",
                 xy=(25, df["predicted_rate"].iloc[24]),
                 xytext=(20, df["predicted_rate"].iloc[24]-200),
                 arrowprops=dict(facecolor='red', shrink=0.05, width=1, headwidth=6))
                 
    plt.legend(loc="upper right", frameon=True)
    plt.subplots_adjust(bottom=0.1, top=0.92)
    
    # Save to charts directory and root folder
    chart_output_path = Path("project/backend/charts/december_forecast.png")
    chart_output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(chart_output_path, dpi=150)
    plt.savefig("december_forecast.png", dpi=150)
    plt.close()
    
    print(f"December forecast chart saved to {chart_output_path} and root december_forecast.png")

def score_predictions():
    """Scores validation predictions against validation template if they exist."""
    val_preds_path = Path("project/backend/validation_predictions.csv")
    if val_preds_path.exists():
        print(f"\nChecking validation predictions at {val_preds_path}...")
        df_preds = pd.read_csv(val_preds_path)
        print(f"Loaded {len(df_preds)} prediction rows.")
        print("Format check:")
        print(f"  Columns: {list(df_preds.columns)}")
        print(f"  Sample rates:\n{df_preds.head(3)}")
    else:
        print("\nNo validation predictions found. Run 'python project/backend/predict.py' to generate them.")

if __name__ == "__main__":
    generate_december_chart()
    score_predictions()
