"""Pydantic schemas for the Safemate / Aegis Emergency SOS & Trusted Contacts feature."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Trusted Contacts Schemas
# ---------------------------------------------------------------------------
class ContactCreate(BaseModel):
    """Payload to register a new trusted emergency contact."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Full name of the trusted emergency contact",
        examples=["Maya Lin"],
    )
    phone_number: str = Field(
        ...,
        min_length=3,
        max_length=64,
        description="Phone number configured for emergency SMS/call dispatch",
        examples=["+1-555-0192"],
    )
    email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional email address for emergency notifications",
        examples=["maya.lin@safemail.org"],
    )
    relationship: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Relationship to user (e.g. Sister, Roommate, Campus Security)",
        examples=["Sister & Primary Emergency Contact"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Maya Lin",
                "phone_number": "+1-555-0192",
                "email": "maya.lin@safemail.org",
                "relationship": "Sister & Primary Emergency Contact",
            }
        }
    }


class ContactResponse(BaseModel):
    """Public representation of a registered trusted contact."""

    id: int = Field(..., description="Unique database identifier for the contact")
    user_id: str = Field(..., description="ID or email of the user who registered this contact")
    name: str = Field(..., description="Full name of the contact")
    phone_number: str = Field(..., description="Contact phone number")
    email: Optional[str] = Field(default=None, description="Contact email address")
    relationship: Optional[str] = Field(default=None, description="Relationship to user")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")

    model_config = {"from_attributes": True}


class ContactDeleteResponse(BaseModel):
    """Confirmation payload returned when a trusted contact is deleted."""

    status: str = Field(default="success", description="Status confirmation")
    message: str = Field(..., description="Human-readable success message")
    contact_id: int = Field(..., description="ID of the removed contact")


# ---------------------------------------------------------------------------
# Emergency SOS Panic Trigger Schemas
# ---------------------------------------------------------------------------
class SOSRequest(BaseModel):
    """Request payload submitted when the emergency SOS panic button is pressed."""

    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Current latitude coordinate of the device at the moment of distress",
        examples=[37.774929],
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Current longitude coordinate of the device at the moment of distress",
        examples=[-122.419416],
    )
    message: Optional[str] = Field(
        default=None,
        description="Optional custom emergency message or situation note",
        examples=["I am feeling unsafe, please track my location immediately."],
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Optional identifier of the user (auto-resolved when authenticated)",
        examples=["usr_safemate_001"],
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="Optional client timestamp recorded when the panic button was activated",
        examples=["2026-10-24T16:27:38Z"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "latitude": 37.774929,
                "longitude": -122.419416,
                "message": "I am feeling unsafe, please track my location immediately.",
                "user_id": "usr_safemate_001",
                "timestamp": "2026-10-24T16:27:38Z",
            }
        }
    }


class EmergencyContact(BaseModel):
    """Schema representing an individual trusted emergency contact."""

    name: str = Field(..., description="Full name of the trusted emergency contact")
    phone: str = Field(..., description="Phone number configured for emergency alerts")
    relationship: str = Field(..., description="Relationship to user (e.g., Sister, Roommate)")
    email: Optional[str] = Field(default=None, description="Optional email address")


class DispatchedAlertInfo(BaseModel):
    """Audit record of a dispatched alert notification to an individual contact."""

    name: str = Field(..., description="Name of the contact alerted")
    phone: str = Field(..., description="Phone number alerted")
    relationship: Optional[str] = Field(default=None, description="Relationship of the contact to the user")
    status: str = Field(default="DELIVERED", description="Dispatch transmission status")


class SOSResponse(BaseModel):
    """Response returned upon successful processing of an emergency SOS alert."""

    status: str = Field(default="success", description="Status confirmation of the dispatch")
    timestamp: str = Field(..., description="Timestamp of the alert dispatch")
    count: int = Field(..., description="Count of contacts successfully alerted")
    contacts_alerted: int = Field(
        ..., description="Count of contacts successfully alerted (semantic alias)"
    )
    alert_id: str = Field(..., description="Unique emergency dispatch incident identifier")
    user_id: str = Field(..., description="User ID associated with the SOS alert")
    google_maps_url: str = Field(..., description="Live Google Maps coordinates link")
    distress_message: str = Field(..., description="High-priority distress message broadcasted")
    contacts: List[DispatchedAlertInfo] = Field(
        default_factory=list,
        description="List of trusted contacts who received the emergency dispatch",
    )
