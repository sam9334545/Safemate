"""Tests for model metadata and public information endpoint."""

from fastapi.testclient import TestClient
from tests.conftest import FakeModelService
from app.services.model_service import get_model_service


def test_model_info_success(client: TestClient):
    """Test GET /api/v1/model-info returns required public schema."""
    response = client.get("/api/v1/model-info")
    assert response.status_code == 200
    data = response.json()

    assert data["model_id"] == "umm-maybe/AI-image-detector"
    assert data["task"] == "image-classification"
    assert "description" in data
    assert data["model_loaded"] is True
    assert data["inference_available"] is True
    assert "artificial" in data["labels"]
    assert "human" in data["labels"]
    assert "limitations_notice" in data
    assert "SwinForImageClassification" in data.get("architecture", "")

    # Security check: ensure no internal filesystem paths or tokens leak
    payload_str = str(data)
    assert "C:\\" not in payload_str
    assert "/home/" not in payload_str
    assert "token" not in payload_str.lower()


def test_model_info_when_unready(app_with_mock):
    """Test model-info properly reflects unready state."""
    unready_service = FakeModelService(is_loaded=False)
    app_with_mock.dependency_overrides[get_model_service] = lambda: unready_service

    with TestClient(app_with_mock) as client:
        response = client.get("/api/v1/model-info")
        assert response.status_code == 200
        data = response.json()
        assert data["model_loaded"] is False
        assert data["inference_available"] is False
