"""Tests for health and readiness endpoints."""

from fastapi.testclient import TestClient
from tests.conftest import FakeModelService
from app.services.model_service import get_model_service


def test_health_liveness(client: TestClient):
    """Test GET /api/v1/health returns 200 and expected liveness contract."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ai-image-screening-api"
    assert "X-Request-ID" in response.headers


def test_health_ready_when_loaded(client: TestClient):
    """Test GET /api/v1/health/ready returns 200 when model service is initialized."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["model_loaded"] is True
    assert data["model_id"] == "umm-maybe/AI-image-detector"
    assert "device" in data


def test_health_ready_when_unavailable(app_with_mock):
    """Test GET /api/v1/health/ready returns 503 when model is not loaded."""
    unready_service = FakeModelService(is_loaded=False)
    app_with_mock.dependency_overrides[get_model_service] = lambda: unready_service

    with TestClient(app_with_mock) as client:
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unavailable"
        assert data["model_loaded"] is False
        assert data["model_id"] == "umm-maybe/AI-image-detector"


def test_root_endpoint(client: TestClient):
    """Test GET / returns service information and docs links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "ai-image-screening-api"
    assert data["docs"] == "/docs"
