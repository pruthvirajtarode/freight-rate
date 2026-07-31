import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from preprocessing import preprocess_data


def test_negative_weight_fixing():
    # Test that negative weights are automatically converted to positive
    data = pd.DataFrame({
        "pickup": ["Chicago", "New York"],
        "delivery": ["Dallas", "Miami"],
        "equipment": ["Dry Van", "Reefer"],
        "distance": [1000.0, 1500.0],
        "weight": [-45000.0, -12000.0],
        "market_index": [1.1, 0.9],
        "quote_signal": [2.0, 1.8],
        "pickup_lat": [41.8781, 40.7128],
        "pickup_lon": [-87.6298, -74.0060],
        "delivery_lat": [32.7767, 25.7617],
        "delivery_lon": [-96.7970, -80.1918],
        "date": ["2025-12-01", "2025-12-02"],
        "posted_rate": [3200.0, 4100.0]
    })
    
    _df_clean, _y, preprocessor = preprocess_data(data, is_training=True)
    
    # Preprocessing drops original columns (like weight) and ordinal encodes/target encodes them
    # But let's check that the preprocessor fitted global_weight_median correctly as a positive value
    assert preprocessor.global_weight_median_ > 0
    assert preprocessor.global_weight_median_ == 28500.0 # Median of 45000 and 12000 is 28500

def test_missing_value_imputation():
    # Test that NaN weights are imputed
    data = pd.DataFrame({
        "pickup": ["Chicago", "Chicago", "New York"],
        "delivery": ["Dallas", "Dallas", "Miami"],
        "equipment": ["Dry Van", "Dry Van", "Reefer"],
        "distance": [1000.0, 1000.0, 1500.0],
        "weight": [40000.0, np.nan, 12000.0],
        "market_index": [1.1, 1.1, 0.9],
        "quote_signal": [2.0, 2.0, 1.8],
        "pickup_lat": [41.8781, 41.8781, 40.7128],
        "pickup_lon": [-87.6298, -87.6298, -74.0060],
        "delivery_lat": [32.7767, 32.7767, 25.7617],
        "delivery_lon": [-96.7970, -96.7970, -80.1918],
        "date": ["2025-12-01", "2025-12-02", "2025-12-03"],
        "posted_rate": [3000.0, 3200.0, 4000.0]
    })
    
    _df_clean, _y, preprocessor = preprocess_data(data, is_training=True)
    
    # Check that route weight median was populated
    route_key = "Chicago->Dallas"
    assert route_key in preprocessor.route_weight_medians_
    assert preprocessor.route_weight_medians_[route_key] == 40000.0
