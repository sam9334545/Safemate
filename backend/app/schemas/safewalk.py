"""Pydantic schemas for the Aegis SafeWalk trip escort and live-tracking service."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class TripCreateRequest(BaseModel):
    """Request payload for generating a SafeWalk trip token and tracking session."""

    user_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier of the user initiating the SafeWalk session",
        examples=["usr_aegis_001"],
    )
    destination: str = Field(
        ...,
        min_length=1,
        description="Target destination or arrival point for the walk",
        examples=["North Campus Library", "Student Union Dorm 4"],
    )
    duration_minutes: int = Field(
        ...,
        gt=0,
        le=1440,
        description="Estimated walking trip duration in minutes (1 to 1440)",
        examples=[25],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "usr_aegis_001",
                "destination": "North Campus Library",
                "duration_minutes": 25,
            }
        }
    }


class TripCreateResponse(BaseModel):
    """Response returned upon successful creation of a SafeWalk trip session."""

    status: str = Field(default="success", description="Status confirmation of trip token generation")
    trip_token: str = Field(..., description="Unique, temporary trip token for live tracking")
    token: str = Field(..., description="Semantic alias for trip token")
    shareable_link: str = Field(..., description="Live tracking shareable URL for trusted guardians")
    expected_arrival: str = Field(..., description="Expected arrival timestamp in ISO 8601 format")
    expected_arrival_time: str = Field(
        ..., description="Semantic alias representing expected arrival timestamp"
    )
    user_id: str = Field(..., description="User ID of the traveler")
    destination: str = Field(..., description="Target destination")
    duration_minutes: int = Field(..., description="Trip duration in minutes")
    created_at: str = Field(..., description="Timestamp when the trip was initiated")


class TripSessionDetail(BaseModel):
    """Detailed view of an ongoing or completed SafeWalk trip session."""

    trip_token: str = Field(..., description="Unique trip token identifier")
    token: str = Field(..., description="Trip token alias")
    user_id: str = Field(..., description="Unique identifier of the traveler")
    destination: str = Field(..., description="Target arrival destination")
    latitude: Optional[float] = Field(
        default=None, description="Current live latitude coordinate"
    )
    longitude: Optional[float] = Field(
        default=None, description="Current live longitude coordinate"
    )
    status: str = Field(
        default="active",
        description="Current trip status ('active', 'overdue', 'completed')",
    )
    expected_arrival: str = Field(..., description="Expected arrival timestamp in ISO 8601 format")
    expected_arrival_time: Optional[str] = Field(
        default=None, description="Expected arrival timestamp alias"
    )
    duration_minutes: int = Field(..., description="Trip duration in minutes")
    created_at: str = Field(..., description="Timestamp when the trip was created")
    last_updated_at: Optional[str] = Field(
        default=None, description="Timestamp of the most recent coordinate update"
    )
    shareable_link: str = Field(..., description="Shareable live-tracking web URL")


class LocationUpdateRequest(BaseModel):
    """Request payload for updating device GPS coordinates during an active walk."""

    token: str = Field(
        ...,
        min_length=1,
        description="Unique SafeWalk trip token",
        examples=["tk_94821x"],
    )
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Current live latitude coordinate",
        examples=[37.774929],
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Current live longitude coordinate",
        examples=[-122.419416],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "tk_94821x",
                "latitude": 37.774929,
                "longitude": -122.419416,
            }
        }
    }


class LocationUpdateResponse(BaseModel):
    """Response confirming successful update of live GPS coordinates."""

    status: str = Field(default="success", description="Status confirmation of the update")
    token: str = Field(..., description="Trip token updated")
    latitude: float = Field(..., description="Updated latitude")
    longitude: float = Field(..., description="Updated longitude")
    trip_status: str = Field(..., description="Current status of the trip ('active' or 'overdue')")
    expected_arrival: str = Field(..., description="Expected arrival timestamp")
    trip: TripSessionDetail = Field(..., description="Current trip metadata")
