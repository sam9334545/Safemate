"""Unit and integration tests for Email & Password JWT Authentication."""

import io
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import UserModel
from app.utils.auth import verify_password


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_user(client):
    """Fixture providing a registered user credentials and token."""
    email = "auth_tester@safemate.org"
    password = "StrongPassword123!"

    # Ensure clean slate for test user
    with SessionLocal() as db:
        existing = db.query(UserModel).filter(UserModel.email == email).first()
        if existing:
            db.delete(existing)
            db.commit()

    # Register user
    reg_res = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert reg_res.status_code in (201, 200)

    # Login to get token
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    return {
        "email": email,
        "password": password,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


def test_auth_routes_in_openapi(client):
    """Verify auth endpoints are registered in OpenAPI under tag 'Authentication'."""
    openapi = app.openapi()
    paths = openapi["paths"]
    assert "/api/v1/auth/register" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/me" in paths
    assert "Authentication" in paths["/api/v1/auth/register"]["post"]["tags"]


def test_register_user_success(client):
    """Test successful user registration stores hashed password in database."""
    email = "new_user_reg@safemate.org"
    password = "MySecurePassword!456"

    with SessionLocal() as db:
        existing = db.query(UserModel).filter(UserModel.email == email).first()
        if existing:
            db.delete(existing)
            db.commit()

    response = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == email
    assert data["is_active"] is True
    assert "id" in data
    assert "password" not in data  # Never expose password in response

    # Verify password was hashed in database
    with SessionLocal() as db:
        user = db.query(UserModel).filter(UserModel.email == email).first()
        assert user is not None
        assert user.hashed_password != password
        assert verify_password(password, user.hashed_password)


def test_register_duplicate_email_fails(client, test_user):
    """Test attempting to register with an existing email returns HTTP 400."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": test_user["email"], "password": "AnotherPassword999"},
    )
    assert response.status_code == 400
    assert "already registered" in response.json().get("detail", "").lower()


def test_login_success(client, test_user):
    """Test login with correct credentials via OAuth2 form data returns valid JWT token."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user["email"], "password": test_user["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_incorrect_password(client, test_user):
    """Test login with wrong password returns HTTP 401."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user["email"], "password": "WrongPassword999!"},
    )
    assert response.status_code == 401
    assert "incorrect" in response.json().get("detail", "").lower()


def test_login_nonexistent_email(client):
    """Test login with unregistered email returns HTTP 401."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent_ghost@safemate.org", "password": "SomePassword123!"},
    )
    assert response.status_code == 401


def test_oauth2_form_login(client, test_user):
    """Test OAuth2 form-data login endpoint for Swagger UI."""
    response = client.post(
        "/api/v1/auth/token",
        data={"username": test_user["email"], "password": test_user["password"]},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_get_current_user_me_endpoint(client, test_user):
    """Test /me endpoint returns authenticated user profile."""
    # With valid Bearer token
    response = client.get("/api/v1/auth/me", headers=test_user["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["is_active"] is True

    # Without token -> 401 Unauthorized
    unauth_response = client.get("/api/v1/auth/me")
    assert unauth_response.status_code == 401


def test_safewalk_create_trip_requires_auth(client, test_user):
    """Test SafeWalk trip creation is protected by authentication."""
    trip_payload = {
        "user_id": test_user["email"],
        "destination": "Student Union Building",
        "duration_minutes": 25,
    }

    # 1. Unauthenticated request must fail with 401
    unauth_res = client.post("/api/v1/safewalk/create-trip", json=trip_payload)
    assert unauth_res.status_code == 401

    # 2. Authenticated request succeeds
    auth_res = client.post(
        "/api/v1/safewalk/create-trip",
        json=trip_payload,
        headers=test_user["headers"],
    )
    assert auth_res.status_code == 200
    assert auth_res.json()["status"] == "success"


def test_evidence_upload_requires_auth(client, test_user):
    """Test Evidence Vault upload is protected by authentication."""
    form_data = {
        "user_id": test_user["email"],
        "latitude": "37.774929",
        "longitude": "-122.419416",
        "note": "Secure note",
    }
    files = {
        "file": ("evidence_auth_test.png", io.BytesIO(b"mock_bytes_auth"), "image/png"),
    }

    # 1. Unauthenticated request must fail with 401
    unauth_res = client.post("/api/v1/evidence/upload", data=form_data, files=files)
    assert unauth_res.status_code == 401

    # 2. Authenticated request succeeds
    files_auth = {
        "file": ("evidence_auth_test.png", io.BytesIO(b"mock_bytes_auth"), "image/png"),
    }
    auth_res = client.post(
        "/api/v1/evidence/upload",
        data=form_data,
        files=files_auth,
        headers=test_user["headers"],
    )
    assert auth_res.status_code == 200
    res_data = auth_res.json()
    assert res_data["status"] == "success"

    # Clean up test artifact
    from app.api.routes.evidence import SECURE_STORAGE_DIR
    stored_path = SECURE_STORAGE_DIR / f"{res_data['evidence_id']}_evidence_auth_test.png"
    if stored_path.exists():
        stored_path.unlink()
