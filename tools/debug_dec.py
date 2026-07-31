import pandas as pd
import joblib, json
import numpy as np
import sys
sys.path.insert(0, 'project/backend')
from config import BEST_MODEL_PATH, PREPROCESSOR_PATH, FEATURE_ENGINEER_PATH, FEATURE_LIST_PATH
from preprocessing import preprocess_data

df = pd.read_csv('project/data/december-chart-inputs.csv')
preprocessor = joblib.load(PREPROCESSOR_PATH)
engineer = joblib.load(FEATURE_ENGINEER_PATH)
model = joblib.load(BEST_MODEL_PATH)
with open(FEATURE_LIST_PATH) as f:
    feature_names = json.load(f)

df_clean, _, _ = preprocess_data(df, is_training=False, preprocessor=preprocessor)
df_eng = engineer.transform(df_clean)

for col in feature_names:
    if col not in df_eng.columns:
        df_eng[col] = 0.0
df_eng = df_eng[feature_names]

preds = model.predict(df_eng)
print('All 31 December predictions:')
for i, p in enumerate(preds):
    print('  Dec {:02d}: ${:.4f}'.format(i+1, p))
print()
print('Min: ${:.2f}, Max: ${:.2f}, Spread: ${:.2f}'.format(preds.min(), preds.max(), preds.max()-preds.min()))

print('\nFeatures that VARY (non-zero std):')
for col in feature_names:
    std = df_eng[col].std()
    if std > 0:
        print('  {:30s} min={:.4f}  max={:.4f}  std={:.4f}'.format(
            col, df_eng[col].min(), df_eng[col].max(), std))
