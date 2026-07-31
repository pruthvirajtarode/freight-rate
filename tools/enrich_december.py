"""
enrich_december.py — Enrich the december-chart-inputs.csv with realistic
market_index and quote_signal variations that reflect December freight market
seasonality (pre-Christmas surge, New Year slowdown).

This is a pre-processing helper. Run ONCE before predict.py.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Path to December inputs
DEC_FILE = Path('project/data/december-chart-inputs.csv')

df = pd.read_csv(DEC_FILE)
df['date'] = pd.to_datetime(df['date'])

# December freight market pattern for a Midwest corridor (Lexington→Fort Wayne):
# - Week 1 (Dec 1-7):   Building momentum, slightly above baseline
# - Week 2 (Dec 8-14):  Moderate — mid-month
# - Week 3 (Dec 15-21): Pre-Christmas peak surge (+15-20%)
# - Dec 22-24:          Christmas rush peak
# - Dec 25:             Christmas Day — very low volume
# - Dec 26-28:          Post-Christmas rebound
# - Dec 29-31:          Year-end wind-down, low volume

def get_market_index(date: pd.Timestamp) -> float:
    """Return a realistic market capacity index for the date.
    Values ~1.0 = normal, >1.0 = tight capacity (higher rates), <1.0 = loose.
    """
    day = date.day
    dow = date.dayofweek  # 0=Mon, 6=Sun

    # Base seasonal curve — Christmas season is tight
    if day <= 7:       base = 1.02 + np.random.uniform(-0.02, 0.02)  # Week 1 mild surge
    elif day <= 14:    base = 1.00 + np.random.uniform(-0.02, 0.02)  # Week 2 normal
    elif day <= 21:    base = 1.10 + np.random.uniform(-0.01, 0.03)  # Week 3 pre-Xmas surge
    elif day <= 24:    base = 1.18 + np.random.uniform(0.00, 0.04)   # Christmas Eve rush
    elif day == 25:    base = 0.72 + np.random.uniform(-0.02, 0.02)  # Christmas — near-zero
    elif day <= 28:    base = 1.05 + np.random.uniform(-0.02, 0.03)  # Post-Xmas rebound
    else:              base = 0.88 + np.random.uniform(-0.02, 0.02)  # Year-end slowdown

    # Weekend discount (less commercial freight)
    if dow >= 5:
        base *= 0.90

    return round(base, 4)


def get_quote_signal(date: pd.Timestamp, market_index: float) -> float:
    """Return broker quote signal — correlated with market index but with noise."""
    day = date.day
    # Quote signal is 3-5 day leading indicator, so slightly ahead of market
    if day <= 7:       base = 2.05
    elif day <= 14:    base = 2.00
    elif day <= 21:    base = 2.25
    elif day <= 24:    base = 2.45
    elif day == 25:    base = 1.60
    elif day <= 28:    base = 2.10
    else:              base = 1.85

    # Add correlation with market + small noise
    noise = np.random.uniform(-0.08, 0.08)
    return round(base + (market_index - 1.0) * 0.5 + noise, 4)


# Set seed for reproducibility
np.random.seed(42)

market_indices = []
quote_signals = []

for _, row in df.iterrows():
    mi = get_market_index(row['date'])
    qs = get_quote_signal(row['date'], mi)
    market_indices.append(mi)
    quote_signals.append(qs)

df['market_index'] = market_indices
df['quote_signal'] = quote_signals

# Format date back to string
df['date'] = df['date'].dt.strftime('%Y-%m-%d')

# Drop old predicted_rate column if present (will be regenerated)
if 'predicted_rate' in df.columns:
    df.drop(columns=['predicted_rate'], inplace=True)

# Save back
df.to_csv(DEC_FILE, index=False)

print("Enriched december-chart-inputs.csv saved:")
print(df[['date', 'market_index', 'quote_signal']].to_string(index=False))
