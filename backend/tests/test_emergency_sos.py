"""Unit and integration tests for the Aegis Emergency SOS service."""

import pytest
from fastapi.testclient import TestClient

from emergency_sos import app, EMERGENCY_CONTACTS_DB, DEFAULT_EMERGENCY_CONTACTS


@pytest.fixture
def client():
    return TestClient(app)


def test_sos_successful_dispatch_known_user(client):
    """Test successful SOS alert for a user with pre-configured contacts including Maya Lin."""
    payload = {
        "user_id": "usr_aegis_001",
        "latitude": 37.774929,
        "longitude": -122.419416,
        "timestamp": "2026-10-24T16:27:38Z",
    }
    response = client.post("/api/emergency/sos", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert "timestamp" in data
    assert data["count"] == 3
    assert data["contacts_alerted"] == 3
    assert data["user_id"] == "usr_aegis_001"
    assert data["google_maps_url"] == "https://maps.google.com/?q=37.774929,-122.419416"
    assert "https://maps.google.com/?q=37.774929,-122.419416" in data["distress_message"]

    # Verify Maya Lin is in the alerted contacts
    notified_names = [record["name"] for record in data["dispatched_alerts"]]
    assert "Maya Lin" in notified_names


def test_sos_successful_dispatch_fallback_user(client):
    """Test that an unmapped user safely falls back to default contacts including Maya Lin."""
    payload = {
        "user_id": "unregistered_student_42",
        "latitude": 34.052235,
        "longitude": -118.243683,
        "timestamp": "2026-10-24T16:27:38Z",
    }
    response = client.post("/api/emergency/sos", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["count"] >= 1
    assert any(a["name"] == "Maya Lin" for a in data["dispatched_alerts"])
    assert "https://maps.google.com/?q=34.052235,-118.243683" in data["google_maps_url"]


def test_sos_validation_missing_latitude(client):
    """Test request validation fails when latitude is omitted."""
    payload = {
        "user_id": "usr_aegis_001",
        "longitude": -122.419416,
        "timestamp": "2026-10-24T16:27:38Z",
    }
    response = client.post("/api/emergency/sos", json=payload)
    assert response.status_code == 422


def test_sos_validation_invalid_latitude_range(client):
    """Test request validation fails when latitude is out of [-90, 90]."""
    payload = {
        "user_id": "usr_aegis_001",
        "latitude": 91.5,
        "longitude": -122.419416,
        "timestamp": "2026-10-24T16:27:38Z",
    }
    response = client.post("/api/emergency/sos", json=payload)
    assert response.status_code == 422


def test_sos_validation_invalid_longitude_range(client):
    """Test request validation fails when longitude is out of [-180, 180]."""
    payload = {
        "user_id": "usr_aegis_001",
        "latitude": 37.774929,
        "longitude": 185.0,
        "timestamp": "2026-10-24T16:27:38Z",
    }
    response = client.post("/api/emergency/sos", json=payload)
    assert response.status_code == 422


def test_sos_validation_empty_user_id(client):
    """Test request validation fails when user_id is empty."""
    payload = {
        "user_id": "",
        "latitude": 37.774929,
        "longitude": -122.419416,
        "timestamp": "2026-10-24T16:27:38Z",
    }
    response = client.post("/api/emergency/sos", json=payload)
    assert response.status_code == 422


def test_emergency_health_check(client):
    """Test emergency subsystem health check endpoint."""
    response = client.get("/api/emergency/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_contacts_endpoint(client):
    """Test viewing contacts configured for a user."""
    response = client.get("/api/emergency/contacts/usr_aegis_001")
    assert response.status_code == 200
    contacts = response.json()
    assert any(c["name"] == "Maya Lin" for c in contacts)
