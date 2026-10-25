"""Integration tests verifying cross-account authorization and data isolation.

Ensures User A cannot access, download, modify, or delete User B's private resources:
- Evidence Vault files, records, and checksums
- Trusted Contacts
- Emergency SOS alerts and resolution
- Private SafeWalk trips and escalation
- User-bound Chatbot conversation histories
- Guest session scoping vs registered accounts
"""

import io
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import EvidenceRecord, SafeWalkTrip, TrustedContactModel, UserModel
from app.utils.auth import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def user_a(client):
    """Fixture providing registered User A."""
    email = "user_a_security@safemate.org"
    password = "UserAPassword123!"
    with SessionLocal() as db:
        existing = db.query(UserModel).filter(UserModel.email == email).first()
        if existing:
            db.delete(existing)
            db.commit()

    reg_res = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert reg_res.status_code == 201
    user_id = reg_res.json()["id"]

    login_res = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    token = login_res.json()["access_token"]
    return {
        "id": user_id,
        "email": email,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest.fixture
def user_b(client):
    """Fixture providing registered User B."""
    email = "user_b_security@safemate.org"
    password = "UserBPassword456!"
    with SessionLocal() as db:
        existing = db.query(UserModel).filter(UserModel.email == email).first()
        if existing:
            db.delete(existing)
            db.commit()

    reg_res = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert reg_res.status_code == 201
    user_id = reg_res.json()["id"]

    login_res = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    token = login_res.json()["access_token"]
    return {
        "id": user_id,
        "email": email,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest.fixture
def guest_user(client):
    """Fixture providing an anonymous guest user."""
    res = client.post("/api/v1/auth/guest-session")
    assert res.status_code == 200
    token = res.json()["access_token"]
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    return {
        "id": me_res.json()["id"],
        "email": me_res.json()["email"],
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


def test_user_a_cannot_download_or_view_user_b_evidence(client, user_a, user_b):
    """Verify that User B cannot view, download, or verify User A's private evidence."""
    # 1. User A uploads private evidence
    file_bytes = b"CONFIDENTIAL_USER_A_EVIDENCE_AUDIO_OR_PHOTO"
    files = {"file": ("secret_recording.png", io.BytesIO(file_bytes), "image/png")}
    form_data = {
        "user_id": str(user_a["id"]),
        "latitude": "37.7749",
        "longitude": "-122.4194",
        "note": "Secret notes strictly belonging to User A",
    }
    upload_res = client.post("/api/v1/evidence/upload", data=form_data, files=files, headers=user_a["headers"])
    assert upload_res.status_code == 200
    evidence_id = upload_res.json()["evidence_id"]

    # 2. User A can inspect and download their own evidence
    owner_get = client.get(f"/api/v1/evidence/record/{evidence_id}", headers=user_a["headers"])
    assert owner_get.status_code == 200
    owner_down = client.get(f"/api/v1/evidence/download/{evidence_id}", headers=user_a["headers"])
    assert owner_down.status_code == 200

    # 3. User B tries to view User A's evidence record -> 403 FORBIDDEN
    attacker_get = client.get(f"/api/v1/evidence/record/{evidence_id}", headers=user_b["headers"])
    assert attacker_get.status_code == 403
    assert "not authorized" in attacker_get.json()["detail"].lower()

    # 4. User B tries to download User A's evidence file -> 403 FORBIDDEN
    attacker_down = client.get(f"/api/v1/evidence/download/{evidence_id}", headers=user_b["headers"])
    assert attacker_down.status_code == 403
    assert "not authorized" in attacker_down.json()["detail"].lower()

    # 5. User B tries to delete User A's evidence -> 403 FORBIDDEN
    attacker_del = client.delete(f"/api/v1/evidence/record/{evidence_id}", headers=user_b["headers"])
    assert attacker_del.status_code == 403

    # 6. User B lists records -> User A's evidence is strictly omitted
    list_b = client.get("/api/v1/evidence/records", headers=user_b["headers"])
    assert list_b.status_code == 200
    evidence_ids_b = [r["evidence_id"] for r in list_b.json()]
    assert evidence_id not in evidence_ids_b

    # Cleanup by rightful owner
    del_res = client.delete(f"/api/v1/evidence/record/{evidence_id}", headers=user_a["headers"])
    assert del_res.status_code == 200


def test_user_a_cannot_modify_or_delete_user_b_trusted_contacts(client, user_a, user_b):
    """Verify cross-account contact protection: User B cannot modify or delete User A's contacts."""
    # 1. User A adds a contact
    contact_res = client.post(
        "/api/v1/emergency/contacts",
        json={
            "name": "Sister Maya",
            "phone_number": "+1-555-0999",
            "email": "maya@family.org",
            "relationship": "Sister",
        },
        headers=user_a["headers"],
    )
    assert contact_res.status_code in (200, 201)
    contact_id = contact_res.json()["id"]

    # 2. User B tries to update User A's contact -> 404 / 403 (scoped to user)
    upd_res = client.put(
        f"/api/v1/emergency/contacts/{contact_id}",
        json={"name": "Hacked Contact", "phone_number": "+1-555-0000"},
        headers=user_b["headers"],
    )
    assert upd_res.status_code in (403, 404)

    # 3. User B tries to delete User A's contact -> 404 / 403
    del_res = client.delete(f"/api/v1/emergency/contacts/{contact_id}", headers=user_b["headers"])
    assert del_res.status_code in (403, 404)

    # 4. User B lists contacts -> User A's contact is NOT returned
    list_b = client.get("/api/v1/emergency/contacts", headers=user_b["headers"])
    assert list_b.status_code == 200
    assert not any(c["id"] == contact_id for c in list_b.json())

    # Cleanup by rightful owner
    clean_del = client.delete(f"/api/v1/emergency/contacts/{contact_id}", headers=user_a["headers"])
    assert clean_del.status_code == 200


def test_user_a_cannot_resolve_user_b_emergency_alert(client, user_a, user_b):
    """Verify that User B cannot resolve or tamper with User A's emergency distress alerts."""
    # 1. User A triggers SOS
    sos_res = client.post(
        "/api/v1/emergency/sos",
        json={"latitude": 37.7749, "longitude": -122.4194, "note": "Emergency assistance requested"},
        headers=user_a["headers"],
    )
    assert sos_res.status_code == 200
    alert_id = sos_res.json()["alert_id"]

    # 2. User B attempts to resolve User A's alert -> 403 FORBIDDEN
    res_b = client.post(
        f"/api/v1/emergency/sos/{alert_id}/resolve",
        json={"resolution_notes": "Attempting unauthorized de-escalation"},
        headers=user_b["headers"],
    )
    assert res_b.status_code == 403
    assert "not authorized" in res_b.json()["detail"].lower()

    # 3. Rightful owner User A resolves alert -> 200 OK
    res_a = client.post(
        f"/api/v1/emergency/sos/{alert_id}/resolve",
        json={"resolution_notes": "Situation secured safely by owner"},
        headers=user_a["headers"],
    )
    assert res_a.status_code == 200
    assert res_a.json()["status"] == "resolved"


def test_user_a_cannot_read_or_wipe_user_b_chat_history(client, user_a, user_b):
    """Verify that User B cannot read or clear User A's user-bound chat sessions."""
    user_a_session = f"user_{user_a['id']}"

    # 1. User A sends message in their user session
    msg_res = client.post(
        "/api/v1/chatbot/message",
        json={"session_id": user_a_session, "text": "I need help with a protective order"},
        headers=user_a["headers"],
    )
    assert msg_res.status_code == 200

    # 2. User B tries to read User A's chat history -> 403 FORBIDDEN
    hist_b = client.get(f"/api/v1/chatbot/history/{user_a_session}", headers=user_b["headers"])
    assert hist_b.status_code == 403
    assert "not authorized" in hist_b.json()["detail"].lower()

    # 3. User B tries to export User A's consultation report -> 403 FORBIDDEN
    exp_b = client.get(f"/api/v1/chatbot/export/{user_a_session}", headers=user_b["headers"])
    assert exp_b.status_code == 403

    # 4. User B tries to wipe User A's session -> 403 FORBIDDEN
    wipe_b = client.delete(f"/api/v1/chatbot/history/{user_a_session}", headers=user_b["headers"])
    assert wipe_b.status_code == 403

    # 5. User A can access their own history
    hist_a = client.get(f"/api/v1/chatbot/history/{user_a_session}", headers=user_a["headers"])
    assert hist_a.status_code == 200


def test_guest_session_cannot_access_registered_user_evidence(client, user_a, guest_user):
    """Verify that a temporary guest session token cannot read registered users' private evidence."""
    # User A uploads evidence
    files = {"file": ("vault_secret.png", io.BytesIO(b"vault_secret_bytes"), "image/png")}
    form_data = {"user_id": str(user_a["id"]), "latitude": "37.7749", "longitude": "-122.4194"}
    up_res = client.post("/api/v1/evidence/upload", data=form_data, files=files, headers=user_a["headers"])
    assert up_res.status_code == 200
    ev_id = up_res.json()["evidence_id"]

    # Guest token tries to access User A's record -> 403 FORBIDDEN
    guest_get = client.get(f"/api/v1/evidence/record/{ev_id}", headers=guest_user["headers"])
    assert guest_get.status_code == 403

    guest_down = client.get(f"/api/v1/evidence/download/{ev_id}", headers=guest_user["headers"])
    assert guest_down.status_code == 403

    # Cleanup
    client.delete(f"/api/v1/evidence/record/{ev_id}", headers=user_a["headers"])


def test_safewalk_my_trips_isolation(client, user_a, user_b):
    """Verify that /api/v1/safewalk/my-trips returns only the caller's trips."""
    # User A creates a trip
    trip_a = client.post(
        "/api/v1/safewalk/create-trip",
        json={"user_id": str(user_a["id"]), "destination": "User A Dormitory", "duration_minutes": 20},
        headers=user_a["headers"],
    )
    assert trip_a.status_code == 200
    token_a = trip_a.json()["trip_token"]

    # User B creates a trip
    trip_b = client.post(
        "/api/v1/safewalk/create-trip",
        json={"user_id": str(user_b["id"]), "destination": "User B Apartment", "duration_minutes": 15},
        headers=user_b["headers"],
    )
    assert trip_b.status_code == 200
    token_b = trip_b.json()["trip_token"]

    # User A lists their trips
    my_trips_a = client.get("/api/v1/safewalk/my-trips", headers=user_a["headers"])
    assert my_trips_a.status_code == 200
    tokens_a = [t["trip_token"] for t in my_trips_a.json()]
    assert token_a in tokens_a
    assert token_b not in tokens_a

    # User B lists their trips
    my_trips_b = client.get("/api/v1/safewalk/my-trips", headers=user_b["headers"])
    assert my_trips_b.status_code == 200
    tokens_b = [t["trip_token"] for t in my_trips_b.json()]
    assert token_b in tokens_b
    assert token_a not in tokens_b
