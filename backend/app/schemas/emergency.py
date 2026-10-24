"""Pydantic schemas for the Safemate Emergency SOS panic button service."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class SOSRequest(BaseModel):
    """Request payload submitted when the emergency SOS panic button is pressed."""

    user_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier of the user triggering the SOS panic button",
        examples=["usr_safemate_001"],
    )
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
    timestamp: Optional[str] = Field(
        default=None,
        description="Optional client timestamp recorded when the panic button was activated",
        examples=["2026-10-24T16:27:38Z"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "usr_safemate_001",
                "latitude": 37.774929,
                "longitude": -122.419416,
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
    relationship: str = Field(..., description="Relationship of the contact to the user")
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
