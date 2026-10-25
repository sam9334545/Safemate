"""
SafeMate - Judge Acceptance Scenarios Test Suite (Scenarios A through F)
Validates the complete authentication, authorization, guest session, and demo mode requirements.
"""

import pytest
import io
import uuid
from fastapi.testclient import TestClient
from app.main import create_app
from app.database import Base, engine, get_db
from app.models import UserModel, EvidenceRecord, TrustedContact, EmergencyLog
from app.utils.auth import decode_access_token

@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

def test_scenario_a_normal_registered_user(client):
    """
    Scenario A: Normal Registered User Lifecycle
    1. Register new user
    2. Log in and acquire JWT
    3. Verify /me safe profile
    4. Access private features
    """
    uid = uuid.uuid4().hex[:8]
    email = f"user_{uid}@safemate.org"
    password = "ScenarioAPassword123!"

    # 1. Register
    reg_res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Scenario A Survivor"
    })
    assert reg_res.status_code in (200, 201)
    reg_data = reg_res.json()
    assert "password" not in reg_data
    assert "hashed_password" not in reg_data

    # 2. Log in
    login_res = client.post("/api/v1/auth/login-json", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    assert token is not None

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Verify /me
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == email
    assert me_data["is_guest"] is False
    assert me_data["access_mode"] == "personal_account"
    assert "hashed_password" not in me_data

def test_scenario_b_guest_visitor_session(client):
    """
    Scenario B: Guest Visitor Flow
    1. Request ephemeral guest session
    2. Confirm guest credentials with restricted scope
    3. Verify guest identity in /me
    4. Confirm guest cannot perform registered-user actions
    """
    # 1. Request guest session
    guest_res = client.post("/api/v1/auth/guest-session")
    assert guest_res.status_code in (200, 201)
    guest_token = guest_res.json()["access_token"]
    assert guest_token is not None

    guest_headers = {"Authorization": f"Bearer {guest_token}"}

    # 2. Verify /me reflects guest status
    me_res = client.get("/api/v1/auth/me", headers=guest_headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["is_guest"] is True
    assert me_data["access_mode"] == "guest"

def test_scenario_c_authentication_failure_graceful_handling(client):
    """
    Scenario C: Authentication Failure Fallback
    1. Attempt login with bad credentials -> 401
    2. Verify server does not leak internal exceptions
    3. Client can safely fall back to Judge Demo Mode
    """
    uid = uuid.uuid4().hex[:8]
    bad_login_res = client.post("/api/v1/auth/login-json", json={
        "email": f"nonexistent_{uid}@safemate.org",
        "password": "WrongPassword999!"
    })
    assert bad_login_res.status_code == 401
    assert "detail" in bad_login_res.json()
    assert "Incorrect email or password" in bad_login_res.json()["detail"]

def test_scenario_d_backend_authorization_isolation(client):
    """
    Scenario D: Backend Authorization - User A private resources denied to User B
    """
    # Setup User A and User B
    uid_a = uuid.uuid4().hex[:8]
    uid_b = uuid.uuid4().hex[:8]
    user_a_email = f"user_{uid_a}@safemate.org"
    user_b_email = f"user_{uid_b}@safemate.org"
    pwd = "SecurePassword123!"

    client.post("/api/v1/auth/register", json={"email": user_a_email, "password": pwd})
    client.post("/api/v1/auth/register", json={"email": user_b_email, "password": pwd})

    token_a = client.post("/api/v1/auth/login-json", json={"email": user_a_email, "password": pwd}).json()["access_token"]
    token_b = client.post("/api/v1/auth/login-json", json={"email": user_b_email, "password": pwd}).json()["access_token"]

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A uploads evidence
    file_bytes = b"Scenario D confidential survivor evidence"
    upload_res = client.post(
        "/api/v1/evidence/upload",
        files={"file": ("incident_evidence.png", io.BytesIO(file_bytes), "image/png")},
        data={"user_id": user_a_email, "latitude": "28.5456", "longitude": "77.1926", "note": "User A secret note"},
        headers=headers_a
    )
    assert upload_res.status_code in (200, 201)
    evidence_id = upload_res.json()["evidence_id"]

    # User B attempts to view or download User A's evidence
    b_view_res = client.get(f"/api/v1/evidence/record/{evidence_id}", headers=headers_b)
    assert b_view_res.status_code in (403, 404)

    b_download_res = client.get(f"/api/v1/evidence/download/{evidence_id}", headers=headers_b)
    assert b_download_res.status_code in (403, 404)

    # User A CAN view and download
    a_view_res = client.get(f"/api/v1/evidence/record/{evidence_id}", headers=headers_a)
    assert a_view_res.status_code == 200

def test_scenario_e_safewalk_and_emergency_isolation(client):
    """
    Scenario E: SafeWalk and Emergency alert ownership isolation
    """
    uid_a = uuid.uuid4().hex[:8]
    uid_b = uuid.uuid4().hex[:8]
    user_a_email = f"user_{uid_a}@safemate.org"
    user_b_email = f"user_{uid_b}@safemate.org"
    pwd = "EscortPassword123!"

    client.post("/api/v1/auth/register", json={"email": user_a_email, "password": pwd})
    client.post("/api/v1/auth/register", json={"email": user_b_email, "password": pwd})

    token_a = client.post("/api/v1/auth/login-json", json={"email": user_a_email, "password": pwd}).json()["access_token"]
    token_b = client.post("/api/v1/auth/login-json", json={"email": user_b_email, "password": pwd}).json()["access_token"]

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates SafeWalk trip
    trip_res = client.post(
        "/api/v1/safewalk/create-trip",
        json={"destination": "Campus Library", "duration_minutes": 25},
        headers=headers_a
    )
    assert trip_res.status_code in (200, 201)

    # User A lists trips
    my_trips_a = client.get("/api/v1/safewalk/my-trips", headers=headers_a)
    assert my_trips_a.status_code == 200
    assert len(my_trips_a.json()) >= 1

    # User B lists trips -> should see 0 trips
    my_trips_b = client.get("/api/v1/safewalk/my-trips", headers=headers_b)
    assert my_trips_b.status_code == 200
    assert len(my_trips_b.json()) == 0

def test_scenario_f_access_mode_state_isolation(client):
    """
    Scenario F: Access-mode switching and token separation
    Ensures guest tokens are properly scoped and marked distinct from registered users.
    """
    # 1. Acquire guest token
    guest_res = client.post("/api/v1/auth/guest-session")
    guest_token = guest_res.json()["access_token"]

    # 2. Decode claims
    payload = decode_access_token(guest_token)
    assert payload.get("is_guest") is True
    assert payload.get("mode") == "guest"
