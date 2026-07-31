import sys
from pathlib import Path

# Add backend to path so we can import app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data

def test_metrics_not_found_initially():
    # If the model has not been trained in this test run, it should either return metrics or 404
    response = client.get("/api/v1/metrics")
    assert response.status_code in [200, 404]

def test_models_compare_not_found_initially():
    response = client.get("/api/v1/models/compare")
    assert response.status_code in [200, 404]
