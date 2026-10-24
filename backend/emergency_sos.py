"""Aegis Emergency SOS Panic Button Backend Module.

This standalone FastAPI service module handles high-priority distress alerts
triggered from the "Aegis" emergency SOS panic button.

Features:
- Pydantic models for strict request payload validation (user_id, latitude, longitude, timestamp).
- In-memory contact storage with preloaded mock trusted contacts (e.g., Maya Lin).
- Dynamic high-priority distress message generator with live Google Maps coordinate link.
- Simulated multi-channel dispatch mechanism with structured JSON audit logging.
- Standalone execution support via Uvicorn as well as modular APIRouter export.
"""

from __future__ import annotations

import datetime
import json
import logging
import sys
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("aegis.emergency")


# ---------------------------------------------------------------------------
# Pydantic Schemas / Request & Response Validation
# ---------------------------------------------------------------------------
class SOSRequest(BaseModel):
    """Incoming emergency SOS payload from the Aegis panic button."""

    user_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier of the user triggering the SOS alert",
        examples=["usr_aegis_001"],
    )
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Current latitude coordinate of the device at dispatch",
        examples=[37.774929],
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Current longitude coordinate of the device at dispatch",
        examples=[-122.419416],
    )
    timestamp: str = Field(
        ...,
        min_length=1,
        description="ISO 8601 or formatted timestamp string recorded when the panic button was triggered",
        examples=["2026-10-24T16:27:38Z"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "usr_aegis_001",
                "latitude": 37.774929,
                "longitude": -122.419416,
                "timestamp": "2026-10-24T16:27:38Z",
            }
        }
    }


class EmergencyContact(BaseModel):
    """Schema representing a user's trusted emergency contact."""

    contact_id: str
    name: str
    relationship: str
    phone: str
    email: Optional[str] = None
    notification_channels: List[str] = Field(default_factory=lambda: ["sms", "push"])


class DispatchedAlertRecord(BaseModel):
    """Audit record confirming an alert sent to an individual contact."""

    contact_id: str
    name: str
    phone: str
    relationship: str
    channel: str
    status: str = "DELIVERED"
    dispatched_at: str


class SOSResponse(BaseModel):
    """Standardized response schema returned to the client upon SOS trigger."""

    status: str = Field("success", description="Status of the SOS operation")
    timestamp: str = Field(..., description="Timestamp when alerts were dispatched")
    count: int = Field(..., description="Count of contacts successfully alerted")
    contacts_alerted: int = Field(
        ..., description="Count of contacts successfully alerted (semantic alias)"
    )
    alert_id: str = Field(..., description="Unique emergency dispatch incident ID")
    user_id: str = Field(..., description="ID of the user who triggered the SOS")
    google_maps_url: str = Field(..., description="Live Google Maps coordinates URL")
    distress_message: str = Field(..., description="The distress message broadcast to contacts")
    dispatched_alerts: List[DispatchedAlertRecord] = Field(
        default_factory=list,
        description="Audit breakdown of individual contact notifications",
    )


# ---------------------------------------------------------------------------
# In-Memory Emergency Contacts Repository
# ---------------------------------------------------------------------------
# Pre-populated mock repository including primary contact Maya Lin
EMERGENCY_CONTACTS_DB: Dict[str, List[EmergencyContact]] = {
    "usr_aegis_001": [
        EmergencyContact(
            contact_id="cnt_maya_01",
            name="Maya Lin",
            relationship="Sister & Primary Emergency Contact",
            phone="+1-555-0192",
            email="maya.lin@safemail.org",
            notification_channels=["sms", "push", "voice_alert"],
        ),
        EmergencyContact(
            contact_id="cnt_marcus_02",
            name="Marcus Vance",
            relationship="Trusted Friend / Roommate",
            phone="+1-555-0144",
            email="m.vance@safemail.org",
            notification_channels=["sms", "push"],
        ),
        EmergencyContact(
            contact_id="cnt_campus_sec_03",
            name="Aegis Campus Security Response Unit",
            relationship="Campus Safety Operations Center",
            phone="+1-800-555-SAFE",
            email="dispatch@campus-safety.org",
            notification_channels=["sms", "voice_alert"],
        ),
    ],
    "maya_user": [
        EmergencyContact(
            contact_id="cnt_maya_01",
            name="Maya Lin",
            relationship="Primary Emergency Contact",
            phone="+1-555-0192",
            email="maya.lin@safemail.org",
            notification_channels=["sms", "push"],
        ),
    ],
}

# Fallback contacts list used when a user_id does not have a custom profile
DEFAULT_EMERGENCY_CONTACTS: List[EmergencyContact] = [
    EmergencyContact(
        contact_id="cnt_maya_01",
        name="Maya Lin",
        relationship="Primary Emergency Contact",
        phone="+1-555-0192",
        email="maya.lin@safemail.org",
        notification_channels=["sms", "push", "voice_alert"],
    ),
    EmergencyContact(
        contact_id="cnt_marcus_02",
        name="Marcus Vance",
        relationship="Trusted Emergency Contact",
        phone="+1-555-0144",
        email="m.vance@safemail.org",
        notification_channels=["sms", "push"],
    ),
]

# In-memory incident dispatch audit trail
SOS_DISPATCH_AUDIT_LOG: List[Dict[str, Any]] = []


# ---------------------------------------------------------------------------
# Emergency Dispatch Service Logic
# ---------------------------------------------------------------------------
def get_user_emergency_contacts(user_id: str) -> List[EmergencyContact]:
    """Retrieve saved emergency contacts for a given user.

    Falls back to default emergency contacts (including Maya Lin) if user
    has not yet customized their personal contact list.
    """
    contacts = EMERGENCY_CONTACTS_DB.get(user_id)
    if contacts:
        return contacts
    # Return default contact list ensuring Maya Lin is always available
    logger.info(
        f"User '{user_id}' not explicitly mapped in database; "
        "defaulting to trusted safety circle contacts (including Maya Lin)."
    )
    return DEFAULT_EMERGENCY_CONTACTS


def build_distress_message(
    user_id: str, latitude: float, longitude: float, timestamp: str
) -> tuple[str, str]:
    """Format a high-priority distress message with live Google Maps coordinates.

    Returns:
        tuple[str, str]: (distress_message, google_maps_url)
    """
    google_maps_url = f"https://maps.google.com/?q={latitude},{longitude}"
    distress_message = (
        f"🚨 EMERGENCY SOS [AEGIS DISTRESS SIGNAL] 🚨\n"
        f"User ID: {user_id} triggered the emergency panic button!\n"
        f"Timestamp: {timestamp}\n"
        f"Live GPS Location: {latitude}, {longitude}\n"
        f"Google Maps Link: {google_maps_url}\n"
        f"PRIORITY: IMMEDIATE ASSISTANCE REQUIRED. Please check in immediately or contact emergency services."
    )
    return distress_message, google_maps_url


def simulate_emergency_dispatch(
    alert_id: str,
    user_id: str,
    contacts: List[EmergencyContact],
    distress_message: str,
    google_maps_url: str,
    dispatch_timestamp: str,
) -> List[DispatchedAlertRecord]:
    """Simulate alert dispatch mechanism with structured JSON logging per contact.

    Logs a structured JSON message for each alerted trusted contact to guarantee
    compliance with safety auditing standards.
    """
    dispatched_records: List[DispatchedAlertRecord] = []

    for contact in contacts:
        for channel in contact.notification_channels:
            # Structured JSON payload for safety audit log
            dispatch_log_entry = {
                "event": "AEGIS_SOS_ALERT_DISPATCHED",
                "alert_id": alert_id,
                "user_id": user_id,
                "contact_id": contact.contact_id,
                "contact_name": contact.name,
                "relationship": contact.relationship,
                "recipient_phone": contact.phone,
                "recipient_email": contact.email,
                "delivery_channel": channel,
                "status": "DELIVERED",
                "google_maps_url": google_maps_url,
                "distress_message": distress_message,
                "dispatched_at": dispatch_timestamp,
            }

            # Emit structured JSON log as a high-priority critical event
            logger.critical(json.dumps(dispatch_log_entry, indent=None))

        # Record contact-level audit entry
        dispatched_records.append(
            DispatchedAlertRecord(
                contact_id=contact.contact_id,
                name=contact.name,
                phone=contact.phone,
                relationship=contact.relationship,
                channel=",".join(contact.notification_channels),
                status="DELIVERED",
                dispatched_at=dispatch_timestamp,
            )
        )

    return dispatched_records


# ---------------------------------------------------------------------------
# Router Definition
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/api/emergency", tags=["Aegis Emergency SOS"])


@router.post(
    "/sos",
    response_model=SOSResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger Aegis Emergency SOS Panic Button",
    description=(
        "Processes an urgent SOS distress trigger from the Aegis panic button. "
        "Validates coordinates, retrieves user emergency contacts (such as Maya Lin), "
        "formats a high-priority distress message with live Google Maps coordinates, "
        "and logs structured JSON alert confirmation for every dispatched contact."
    ),
)
async def trigger_emergency_sos(payload: SOSRequest) -> SOSResponse:
    """Handle incoming SOS panic button activation."""
    # 1. Generate unique alert ID and dispatch timestamp
    alert_id = f"sos_{uuid.uuid4().hex[:12]}"
    dispatch_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 2. Retrieve user's saved emergency contacts
    contacts = get_user_emergency_contacts(payload.user_id)
    if not contacts:
        logger.error(f"No emergency contacts found for user {payload.user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No emergency contacts registered for user '{payload.user_id}'.",
        )

    # 3. Format high-priority distress message with live Google Maps link
    distress_message, google_maps_url = build_distress_message(
        user_id=payload.user_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        timestamp=payload.timestamp,
    )

    # 4. Simulate dispatch mechanism with structured JSON logging
    dispatched_records = simulate_emergency_dispatch(
        alert_id=alert_id,
        user_id=payload.user_id,
        contacts=contacts,
        distress_message=distress_message,
        google_maps_url=google_maps_url,
        dispatch_timestamp=dispatch_timestamp,
    )

    # 5. Append to in-memory audit log
    audit_entry = {
        "alert_id": alert_id,
        "user_id": payload.user_id,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "client_timestamp": payload.timestamp,
        "dispatch_timestamp": dispatch_timestamp,
        "contacts_count": len(contacts),
        "dispatched_to": [c.name for c in contacts],
    }
    SOS_DISPATCH_AUDIT_LOG.append(audit_entry)

    # 6. Return response with status 'success', dispatch timestamp, and contact count
    return SOSResponse(
        status="success",
        timestamp=dispatch_timestamp,
        count=len(contacts),
        contacts_alerted=len(contacts),
        alert_id=alert_id,
        user_id=payload.user_id,
        google_maps_url=google_maps_url,
        distress_message=distress_message,
        dispatched_alerts=dispatched_records,
    )


@router.get(
    "/contacts/{user_id}",
    response_model=List[EmergencyContact],
    summary="Retrieve Emergency Contacts for a User",
    description="Returns the trusted safety circle contacts configured for a user (e.g., Maya Lin).",
)
async def get_contacts(user_id: str) -> List[EmergencyContact]:
    """Retrieve trusted emergency contacts for inspection."""
    return get_user_emergency_contacts(user_id)


@router.get(
    "/health",
    summary="Aegis Emergency Subsystem Health Check",
    description="Returns health status of the emergency SOS dispatch service.",
)
async def emergency_health_check() -> Dict[str, Any]:
    """Health probe for the emergency subsystem."""
    return {
        "service": "Aegis Emergency SOS Panic System",
        "status": "healthy",
        "dispatches_recorded": len(SOS_DISPATCH_AUDIT_LOG),
    }


# ---------------------------------------------------------------------------
# Standalone Application Factory & Server
# ---------------------------------------------------------------------------
def create_emergency_app() -> FastAPI:
    """Create and configure the standalone Aegis Emergency SOS FastAPI application."""
    app_instance = FastAPI(
        title="Aegis Emergency SOS Service",
        description=(
            "Standalone backend service for the Aegis Emergency SOS Panic Button. "
            "Validates distress payloads, queries trusted contacts, and dispatches "
            "instant priority alerts with live Google Maps coordinate links."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Allow CORS for development / frontend panic button integration
    app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include the emergency router
    app_instance.include_router(router)

    # Root endpoint for service discovery
    @app_instance.get("/", tags=["Root"])
    async def root():
        return {
            "name": "Aegis Emergency SOS Panic Service",
            "version": "1.0.0",
            "sos_endpoint": "POST /api/emergency/sos",
            "docs": "/docs",
            "health": "/api/emergency/health",
        }

    return app_instance


# Standalone application instance
app = create_emergency_app()

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Aegis Emergency SOS Backend Service on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
