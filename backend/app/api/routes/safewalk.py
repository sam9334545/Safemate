"""SafeWalk Trip Token generator, live-tracking, and location update routes under /api/v1/safewalk."""

from __future__ import annotations

import datetime
import json
import logging
import secrets
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status

from app.schemas.safewalk import (
    LocationUpdateRequest,
    LocationUpdateResponse,
    TripCreateRequest,
    TripCreateResponse,
    TripSessionDetail,
)

logger = logging.getLogger(__name__)

# Router definition with project prefix /api/v1/safewalk and tag "SafeWalk Escort"
router = APIRouter(prefix="/api/v1/safewalk", tags=["SafeWalk Escort"])

# ---------------------------------------------------------------------------
# In-Memory Active Trip Sessions Database
# ---------------------------------------------------------------------------
ACTIVE_TRIPS_DB: Dict[str, Dict[str, Any]] = {}


def generate_unique_trip_token() -> str:
    """Generate a secure, unique temporary trip token prefixed with 'tk_'."""
    while True:
        token = f"tk_{secrets.token_hex(4)}"
        if token not in ACTIVE_TRIPS_DB:
            return token


def check_and_update_overdue(session: Dict[str, Any]) -> str:
    """Check if trip duration has elapsed and update status to 'overdue' if necessary."""
    try:
        expected_arrival_dt = datetime.datetime.fromisoformat(session["expected_arrival"])
        now = datetime.datetime.now(datetime.timezone.utc)
        if now > expected_arrival_dt:
            session["status"] = "overdue"
        elif session.get("status") != "overdue":
            session["status"] = "active"
    except Exception as exc:
        logger.warning(f"Error parsing expected_arrival for token {session.get('trip_token')}: {exc}")
    return session["status"]


@router.post(
    "/create-trip",
    response_model=TripCreateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate SafeWalk Trip Token and Live Tracking Session",
    description=(
        "Initiates an active SafeWalk escort session. Generates a unique temporary trip token, "
        "computes a shareable live-tracking URL (https://aegis.app/trip/{trip_token}), calculates "
        "expected arrival time, and logs structured session registration data."
    ),
)
async def create_trip(payload: TripCreateRequest) -> TripCreateResponse:
    """Generate a SafeWalk trip token and store the active tracking session."""
    # 1. Generate unique temporary trip token
    trip_token = generate_unique_trip_token()

    # 2. Calculate creation and expected arrival timestamps
    now = datetime.datetime.now(datetime.timezone.utc)
    created_at = now.isoformat()
    arrival_dt = now + datetime.timedelta(minutes=payload.duration_minutes)
    expected_arrival = arrival_dt.isoformat()

    # 3. Construct shareable live-tracking link
    shareable_link = f"https://aegis.app/trip/{trip_token}"

    # 4. Store active trip session in temporary in-memory dictionary
    session_data = {
        "trip_token": trip_token,
        "token": trip_token,
        "user_id": payload.user_id,
        "destination": payload.destination,
        "latitude": None,
        "longitude": None,
        "duration_minutes": payload.duration_minutes,
        "created_at": created_at,
        "expected_arrival": expected_arrival,
        "expected_arrival_time": expected_arrival,
        "last_updated_at": None,
        "shareable_link": shareable_link,
        "status": "active",
    }
    ACTIVE_TRIPS_DB[trip_token] = session_data

    # 5. Log structured JSON confirmation
    log_payload = {
        "event": "SAFEWALK_TRIP_CREATED",
        "trip_token": trip_token,
        "user_id": payload.user_id,
        "destination": payload.destination,
        "duration_minutes": payload.duration_minutes,
        "created_at": created_at,
        "expected_arrival": expected_arrival,
        "shareable_link": shareable_link,
    }
    logger.info(json.dumps(log_payload))

    # 6. Return response conforming to requirements
    return TripCreateResponse(
        status="success",
        trip_token=trip_token,
        token=trip_token,
        shareable_link=shareable_link,
        expected_arrival=expected_arrival,
        expected_arrival_time=expected_arrival,
        user_id=payload.user_id,
        destination=payload.destination,
        duration_minutes=payload.duration_minutes,
        created_at=created_at,
    )


@router.get(
    "/trip/{token}",
    response_model=TripSessionDetail,
    status_code=status.HTTP_200_OK,
    summary="Retrieve SafeWalk Live Trip Details by Token",
    description=(
        "Fetches live escort session information using a shareable trip token. "
        "Returns traveler user_id, destination, current latitude, current longitude, "
        "status (active/overdue), and expected arrival. "
        "Raises 404 if the token is invalid or expired."
    ),
)
async def get_trip(token: str) -> TripSessionDetail:
    """Retrieve session details for an active SafeWalk trip by token."""
    session = ACTIVE_TRIPS_DB.get(token)
    if not session:
        logger.warning(f"Trip token '{token}' not found or session expired.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip token not found or expired",
        )

    # Check if trip time has exceeded the expected duration
    check_and_update_overdue(session)

    return TripSessionDetail(**session)


@router.post(
    "/update-location",
    response_model=LocationUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Live GPS Location During SafeWalk Escort",
    description=(
        "Updates device latitude and longitude coordinates for an active trip session in memory. "
        "Checks if trip time has exceeded expected arrival and flags status as 'overdue' if necessary. "
        "Raises 404 if the token is invalid or expired."
    ),
)
async def update_location(payload: LocationUpdateRequest) -> LocationUpdateResponse:
    """Update live GPS coordinates for an active trip token."""
    session = ACTIVE_TRIPS_DB.get(payload.token)
    if not session:
        logger.warning(f"Attempted location update for unknown/expired token: '{payload.token}'")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip token not found or expired",
        )

    now = datetime.datetime.now(datetime.timezone.utc)
    now_iso = now.isoformat()

    # Update in-memory coordinates
    session["latitude"] = payload.latitude
    session["longitude"] = payload.longitude
    session["last_updated_at"] = now_iso

    # Check if trip time has exceeded expected duration
    current_status = check_and_update_overdue(session)

    # Structured JSON log
    log_payload = {
        "event": "SAFEWALK_LOCATION_UPDATED",
        "trip_token": payload.token,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "status": current_status,
        "updated_at": now_iso,
    }
    logger.info(json.dumps(log_payload))

    # Return response with status and current trip metadata
    return LocationUpdateResponse(
        status="success",
        token=payload.token,
        latitude=payload.latitude,
        longitude=payload.longitude,
        trip_status=current_status,
        expected_arrival=session["expected_arrival"],
        trip=TripSessionDetail(**session),
    )


@router.get(
    "/active-trips",
    response_model=List[TripSessionDetail],
    summary="List All Active SafeWalk Escort Sessions",
    description="Inspection endpoint returning all currently registered in-memory trip sessions.",
)
async def list_active_trips() -> List[TripSessionDetail]:
    """List all registered active SafeWalk sessions."""
    for session in ACTIVE_TRIPS_DB.values():
        check_and_update_overdue(session)
    return [TripSessionDetail(**session) for session in ACTIVE_TRIPS_DB.values()]
