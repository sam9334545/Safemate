"""Emergency SOS panic button route under /api/v1/emergency/sos."""

from __future__ import annotations

import datetime
import json
import logging
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.schemas.emergency import (
    DispatchedAlertInfo,
    EmergencyContact,
    SOSRequest,
    SOSResponse,
)

logger = logging.getLogger(__name__)

# Router with explicit prefix /api/v1/emergency and tag "Emergency SOS"
router = APIRouter(prefix="/api/v1/emergency", tags=["Emergency SOS"])

# ---------------------------------------------------------------------------
# Mock Emergency Trusted Contacts Database
# ---------------------------------------------------------------------------
MOCK_EMERGENCY_CONTACTS: Dict[str, List[Dict[str, str]]] = {
    "usr_safemate_001": [
        {
            "name": "Maya Lin",
            "phone": "+1-555-0192",
            "relationship": "Sister & Primary Emergency Contact",
            "email": "maya.lin@safemail.org",
        },
        {
            "name": "Marcus Vance",
            "phone": "+1-555-0144",
            "relationship": "Trusted Friend / Roommate",
            "email": "m.vance@safemail.org",
        },
        {
            "name": "Safemate Campus Response Unit",
            "phone": "+1-800-555-SAFE",
            "relationship": "Campus Safety Operations",
            "email": "dispatch@campus-safety.org",
        },
    ],
    "usr_maya": [
        {
            "name": "Maya Lin",
            "phone": "+1-555-0192",
            "relationship": "Primary Emergency Contact",
            "email": "maya.lin@safemail.org",
        },
    ],
}

DEFAULT_TRUSTED_CONTACTS: List[Dict[str, str]] = [
    {
        "name": "Maya Lin",
        "phone": "+1-555-0192",
        "relationship": "Primary Emergency Contact",
        "email": "maya.lin@safemail.org",
    },
    {
        "name": "Marcus Vance",
        "phone": "+1-555-0144",
        "relationship": "Trusted Emergency Contact",
        "email": "m.vance@safemail.org",
    },
    {
        "name": "Safemate Emergency Response Dispatch",
        "phone": "+1-800-555-SAFE",
        "relationship": "Emergency Dispatch Center",
        "email": "dispatch@safemate.org",
    },
]


def get_emergency_contacts(user_id: str) -> List[Dict[str, str]]:
    """Retrieve saved emergency contacts for the user or default safety circle."""
    contacts = MOCK_EMERGENCY_CONTACTS.get(user_id)
    if contacts:
        return contacts
    logger.info(
        f"User '{user_id}' not explicitly mapped in database; "
        "defaulting to trusted safety circle contacts (including Maya Lin)."
    )
    return DEFAULT_TRUSTED_CONTACTS


@router.post(
    "/sos",
    response_model=SOSResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger Emergency SOS Panic Button",
    description=(
        "Processes an urgent SOS panic trigger from the Safemate emergency button. "
        "Validates coordinates, retrieves trusted contacts (such as Maya Lin), "
        "formats a distress message with live Google Maps coordinates, "
        "logs structured JSON confirmation of dispatch, and returns dispatch status."
    ),
)
async def trigger_sos(payload: SOSRequest) -> SOSResponse:
    """Handle incoming SOS panic button activation."""
    alert_id = f"sos_{uuid.uuid4().hex[:12]}"
    dispatch_timestamp = (
        payload.timestamp
        if payload.timestamp
        else datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

    # 1. Retrieve user's mock emergency trusted contacts
    contacts = get_emergency_contacts(payload.user_id)
    if not contacts:
        logger.error(f"No emergency contacts registered for user '{payload.user_id}'")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No emergency contacts found for user '{payload.user_id}'.",
        )

    # 2. Format Google Maps coordinates string
    google_maps_url = f"https://maps.google.com/?q={payload.latitude},{payload.longitude}"
    distress_message = (
        f"🚨 EMERGENCY SOS [SAFEMATE ALERT] 🚨\n"
        f"User '{payload.user_id}' activated the emergency panic button!\n"
        f"Timestamp: {dispatch_timestamp}\n"
        f"Live GPS Location: {payload.latitude}, {payload.longitude}\n"
        f"Google Maps Link: {google_maps_url}\n"
        f"PRIORITY: IMMEDIATE ASSISTANCE REQUIRED. Please check in or dispatch emergency response."
    )

    # 3. Log structured JSON dispatch confirmation
    dispatched_alert_records: List[DispatchedAlertInfo] = []
    for contact in contacts:
        structured_log = {
            "event": "EMERGENCY_SOS_DISPATCH_CONFIRMED",
            "alert_id": alert_id,
            "user_id": payload.user_id,
            "recipient_name": contact["name"],
            "relationship": contact["relationship"],
            "recipient_phone": contact["phone"],
            "recipient_email": contact.get("email"),
            "google_maps_url": google_maps_url,
            "distress_message": distress_message,
            "dispatch_timestamp": dispatch_timestamp,
            "status": "DELIVERED",
        }
        # Standard logging with structured JSON data
        logger.info(json.dumps(structured_log))

        dispatched_alert_records.append(
            DispatchedAlertInfo(
                name=contact["name"],
                phone=contact["phone"],
                relationship=contact["relationship"],
                status="DELIVERED",
            )
        )

    # 4. Return JSON response confirming status 'success', timestamp, and contact count
    return SOSResponse(
        status="success",
        timestamp=dispatch_timestamp,
        count=len(contacts),
        contacts_alerted=len(contacts),
        alert_id=alert_id,
        user_id=payload.user_id,
        google_maps_url=google_maps_url,
        distress_message=distress_message,
        contacts=dispatched_alert_records,
    )
