"""Tests for the integrated Safemate Emergency SOS route under /api/v1/emergency/sos."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_emergency_sos_route_registered(client):
    """Verify route is registered in FastAPI app OpenAPI schema."""
    openapi = app.openapi()
    assert "/api/v1/emergency/sos" in openapi["paths"]
    post_op = openapi["paths"]["/api/v1/emergency/sos"]["post"]
    assert "Emergency SOS" in post_op["tags"]


def test_emergency_sos_trigger_success_with_timestamp(client):
    """Verify triggering SOS with timestamp alerts contacts including Maya Lin."""
    payload = {
        "user_id": "usr_safemate_001",
        "latitude": 37.774929,
        "longitude": -122.419416,
        "timestamp": "2026-10-24T17:01:00Z",
    }
    response = client.post("/api/v1/emergency/sos", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["timestamp"] == "2026-10-24T17:01:00Z"
    assert data["count"] >= 1
    assert data["contacts_alerted"] == data["count"]
    assert "https://maps.google.com/?q=37.774929,-122.419416" in data["google_maps_url"]
    assert any(c["name"] == "Maya Lin" for c in data["contacts"])


def test_emergency_sos_trigger_optional_timestamp(client):
    """Verify triggering SOS without timestamp auto-populates timestamp."""
    payload = {
        "user_id": "usr_safemate_999",
        "latitude": 40.712776,
        "longitude": -74.005974,
    }
    response = client.post("/api/v1/emergency/sos", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["timestamp"] is not None
    assert any(c["name"] == "Maya Lin" for c in data["contacts"])


def test_emergency_sos_validation_failure(client):
    """Verify invalid coordinates produce validation errors (HTTP 422)."""
    # Missing longitude
    response = client.post("/api/v1/emergency/sos", json={
        "user_id": "usr_safemate_001",
        "latitude": 37.774929,
    })
    assert response.status_code == 422

    # Out-of-bounds latitude
    response = client.post("/api/v1/emergency/sos", json={
        "user_id": "usr_safemate_001",
        "latitude": 100.0,
        "longitude": -122.419416,
    })
    assert response.status_code == 422


def test_root_lists_emergency_sos(client):
    """Verify root endpoint advertises emergency_sos link."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["emergency_sos"] == "/api/v1/emergency/sos"
