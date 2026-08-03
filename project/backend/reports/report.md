# FreightAI Assessment Report

## Project Summary
FreightAI is a freight rate prediction assessment project with data preprocessing, feature engineering, model benchmarking, hyperparameter tuning, evaluation, forecasting, an API backend, and a frontend dashboard.

## Model Performance
- Best model: GradientBoosting
- Validation MAE: 128.98
- Validation RMSE: 575.13
- Validation R2: 0.8507
- Validation MAPE: 6.7607

## Model Comparison
The benchmark compared 7 models: LinearRegression, RandomForest, ExtraTrees, GradientBoosting, XGBoost, LightGBM, and CatBoost.

## Deliverables Produced
- Trained model artifacts in backend/models
- Validation predictions in backend/validation_predictions.csv and deliverables/exports/validation_predictions.csv
- December forecast predictions in backend/december_chart_predictions.csv and deliverables/exports/december_chart_predictions.csv
- Charts saved in backend/charts and deliverables/plots
- FastAPI backend and static frontend implemented

## Notes
The project includes automated tests in backend/tests, and the prediction pipeline was executed successfully in the local environment.
