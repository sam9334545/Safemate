"""Unit and integration tests for the SafeWalk Trip Token and live-tracking service."""

import datetime
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import SafeWalkTrip, UserModel
from app.utils.auth import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Fixture ensuring an authenticated user exists and returns Bearer token headers."""
    email = "test_safewalk_user@safemate.org"
    with SessionLocal() as db:
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            user = UserModel(
                email=email,
                hashed_password="hashed_test_password",
                created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
    token = create_access_token(data={"sub": email, "user_id": user.id})
    return {"Authorization": f"Bearer {token}"}


def test_safewalk_routes_in_openapi(client):
    """Verify all SafeWalk endpoints are registered in OpenAPI under tag 'SafeWalk Escort'."""
    openapi = app.openapi()
    paths = openapi["paths"]
    assert "/api/v1/safewalk/create-trip" in paths
    assert "/api/v1/safewalk/trip/{token}" in paths
    assert "/api/v1/safewalk/update-location" in paths

    for path, method in [
        ("/api/v1/safewalk/create-trip", "post"),
        ("/api/v1/safewalk/trip/{token}", "get"),
        ("/api/v1/safewalk/update-location", "post"),
    ]:
        assert method in paths[path]
        assert "SafeWalk Escort" in paths[path][method]["tags"]


def test_create_trip_successful(client, auth_headers):
    """Test successful trip session creation with valid user, destination, and duration."""
    payload = {
        "user_id": "usr_aegis_001",
        "destination": "North Campus Science Library",
        "duration_minutes": 30,
    }
    response = client.post("/api/v1/safewalk/create-trip", json=payload, headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["trip_token"].startswith("tk_")
    assert data["shareable_link"] == f"https://aegis.app/trip/{data['trip_token']}"
    assert data["user_id"] == "usr_aegis_001"
    assert data["destination"] == "North Campus Science Library"
    assert data["duration_minutes"] == 30
    assert "expected_arrival" in data
    assert "created_at" in data

    token = data["trip_token"]
    with SessionLocal() as db:
        trip = db.query(SafeWalkTrip).filter(SafeWalkTrip.trip_token == token).first()
        assert trip is not None
        assert trip.destination == "North Campus Science Library"


def test_get_trip_session(client, auth_headers):
    """Test retrieving an active trip by its token path parameter."""
    create_res = client.post("/api/v1/safewalk/create-trip", json={
        "user_id": "usr_test_walker",
        "destination": "South Hall Dorm",
        "duration_minutes": 15,
    }, headers=auth_headers)
    token = create_res.json()["trip_token"]

    # Retrieve via GET /api/v1/safewalk/trip/{token} (public/guardian access)
    get_res = client.get(f"/api/v1/safewalk/trip/{token}")
    assert get_res.status_code == 200
    trip_data = get_res.json()
    assert trip_data["user_id"] == "usr_test_walker"
    assert trip_data["destination"] == "South Hall Dorm"
    assert trip_data["status"] == "active"
    assert trip_data["latitude"] is None
    assert trip_data["longitude"] is None
    assert "expected_arrival" in trip_data


def test_get_nonexistent_trip_returns_404(client):
    """Test requesting an unknown or expired trip token returns 404 with exact detail."""
    response = client.get("/api/v1/safewalk/trip/tk_invalid_token_999")
    assert response.status_code == 404
    assert "Trip token not found or expired" in response.json().get("detail", "")


def test_update_location_success(client, auth_headers):
    """Test updating live GPS coordinates during an active walk."""
    # 1. Create a trip
    create_res = client.post("/api/v1/safewalk/create-trip", json={
        "user_id": "usr_live_walker",
        "destination": "East Gate Plaza",
        "duration_minutes": 20,
    }, headers=auth_headers)
    token = create_res.json()["trip_token"]

    # 2. Update location
    loc_payload = {
        "token": token,
        "latitude": 37.774929,
        "longitude": -122.419416,
    }
    update_res = client.post("/api/v1/safewalk/update-location", json=loc_payload)
    assert update_res.status_code == 200
    update_data = update_res.json()
    assert update_data["status"] == "success"
    assert update_data["token"] == token
    assert update_data["latitude"] == 37.774929
    assert update_data["longitude"] == -122.419416
    assert update_data["trip_status"] == "active"

    # 3. Verify get_trip reflects updated coordinates
    get_res = client.get(f"/api/v1/safewalk/trip/{token}")
    assert get_res.status_code == 200
    trip_data = get_res.json()
    assert trip_data["latitude"] == 37.774929
    assert trip_data["longitude"] == -122.419416
    assert trip_data["last_updated_at"] is not None


def test_update_location_overdue_flagging(client, auth_headers):
    """Test that a trip exceeding expected duration is flagged as 'overdue'."""
    create_res = client.post("/api/v1/safewalk/create-trip", json={
        "user_id": "usr_late_walker",
        "destination": "West Pavilion",
        "duration_minutes": 5,
    }, headers=auth_headers)
    token = create_res.json()["trip_token"]

    # Simulate past arrival timestamp in database
    past_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=10)).isoformat()
    with SessionLocal() as db:
        trip = db.query(SafeWalkTrip).filter(SafeWalkTrip.trip_token == token).first()
        trip.expected_arrival = past_time
        db.commit()

    # Update location
    update_res = client.post("/api/v1/safewalk/update-location", json={
        "token": token,
        "latitude": 37.775000,
        "longitude": -122.419500,
    })
    assert update_res.status_code == 200
    assert update_res.json()["trip_status"] == "overdue"

    # Verify get_trip also reflects 'overdue'
    get_res = client.get(f"/api/v1/safewalk/trip/{token}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "overdue"


def test_update_location_invalid_token_returns_404(client):
    """Test location update with non-existent token returns 404."""
    response = client.post("/api/v1/safewalk/update-location", json={
        "token": "tk_ghost_token_404",
        "latitude": 37.774929,
        "longitude": -122.419416,
    })
    assert response.status_code == 404
    assert "Trip token not found or expired" in response.json().get("detail", "")


def test_update_location_validation_error(client):
    """Test validation errors on invalid coordinates."""
    # Invalid latitude > 90
    response = client.post("/api/v1/safewalk/update-location", json={
        "token": "tk_any",
        "latitude": 105.0,
        "longitude": -122.419416,
    })
    assert response.status_code == 422


def test_create_trip_validation_zero_or_negative_duration(client, auth_headers):
    """Test duration_minutes must be positive integer."""
    res_zero = client.post("/api/v1/safewalk/create-trip", json={
        "user_id": "usr_aegis_001",
        "destination": "Library",
        "duration_minutes": 0,
    }, headers=auth_headers)
    assert res_zero.status_code == 422


def test_root_lists_safewalk_endpoints(client):
    """Verify root endpoint includes SafeWalk endpoint links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["safewalk_create_trip"] == "/api/v1/safewalk/create-trip"
    assert data["safewalk_trip"] == "/api/v1/safewalk/trip/{token}"
    assert data["safewalk_update_location"] == "/api/v1/safewalk/update-location"
