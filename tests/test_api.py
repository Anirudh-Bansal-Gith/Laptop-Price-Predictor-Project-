"""Integration tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestDiagnosticsEndpoints:
    def test_health_check_returns_success(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert "model_loaded" in payload

    def test_root_index_returns_metadata(self, client):
        response = client.get("/")
        assert response.status_code == 200
        payload = response.json()
        assert "docs" in payload
        assert "predict_endpoint" in payload


class TestPredictionEndpointValidation:
    def test_missing_required_fields_raises_422(self, client):
        response = client.post("/api/v1/predict", json={"brand": "Dell"})
        assert response.status_code == 422

    def test_out_of_bounds_ram_raises_422(self, client):
        response = client.post("/api/v1/predict", json={
            "brand": "Dell",
            "processor_brand": "Intel",
            "processor_name": "Core i7",
            "ram_gb": 1,  # Minimum boundary is 2
            "storage_gb": 512,
            "storage_type": "SSD",
            "gpu_brand": "Nvidia",
            "screen_size": 15.6,
        })
        assert response.status_code == 422
