"""SafeWalk Trip Token generator, live-tracking, and location update routes under /api/v1/safewalk."""

from __future__ import annotations

import datetime
import json
import logging
import secrets
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SafeWalkTrip
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


def generate_unique_trip_token(db: Session) -> str:
    """Generate a collision-free temporary trip token prefixed with 'tk_'."""
    while True:
        token = f"tk_{secrets.token_hex(4)}"
        existing = db.query(SafeWalkTrip).filter(SafeWalkTrip.trip_token == token).first()
        if not existing:
            return token


def check_and_update_overdue(trip: SafeWalkTrip, db: Session) -> str:
    """Check if trip duration has elapsed and update status to 'overdue' if necessary."""
    try:
        expected_arrival_dt = datetime.datetime.fromisoformat(trip.expected_arrival)
        now = datetime.datetime.now(datetime.timezone.utc)
        if now > expected_arrival_dt:
            if trip.status != "overdue":
                trip.status = "overdue"
                db.commit()
                db.refresh(trip)
        elif trip.status != "overdue":
            trip.status = "active"
    except Exception as exc:
        logger.warning(f"Error parsing expected_arrival for token {trip.trip_token}: {exc}")
    return trip.status


@router.post(
    "/create-trip",
    response_model=TripCreateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate SafeWalk Trip Token and Live Tracking Session",
    description=(
        "Initiates an active SafeWalk escort session. Generates a unique temporary trip token, "
        "computes a shareable live-tracking URL (https://aegis.app/trip/{trip_token}), calculates "
        "expected arrival time, and persists session to the database."
    ),
)
async def create_trip(
    payload: TripCreateRequest,
    db: Session = Depends(get_db),
) -> TripCreateResponse:
    """Generate a SafeWalk trip token and store the active tracking session in database."""
    # 1. Generate unique temporary trip token verified against database
    trip_token = generate_unique_trip_token(db)

    # 2. Calculate creation and expected arrival timestamps
    now = datetime.datetime.now(datetime.timezone.utc)
    created_at = now.isoformat()
    arrival_dt = now + datetime.timedelta(minutes=payload.duration_minutes)
    expected_arrival = arrival_dt.isoformat()

    # 3. Construct shareable live-tracking link
    shareable_link = f"https://aegis.app/trip/{trip_token}"

    # 4. Persist active trip session to PostgreSQL/SQLAlchemy database
    new_trip = SafeWalkTrip(
        trip_token=trip_token,
        user_id=payload.user_id,
        destination=payload.destination,
        duration_minutes=payload.duration_minutes,
        latitude=None,
        longitude=None,
        created_at=created_at,
        expected_arrival=expected_arrival,
        last_updated_at=None,
        shareable_link=shareable_link,
        status="active",
    )
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)

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
        "Fetches live escort session information from database using a shareable trip token. "
        "Returns traveler user_id, destination, current latitude, current longitude, "
        "status (active/overdue), and expected arrival. "
        "Raises 404 if the token is invalid or expired."
    ),
)
async def get_trip(
    token: str,
    db: Session = Depends(get_db),
) -> TripSessionDetail:
    """Retrieve session details for an active SafeWalk trip from database."""
    trip = db.query(SafeWalkTrip).filter(SafeWalkTrip.trip_token == token).first()
    if not trip:
        logger.warning(f"Trip token '{token}' not found or session expired in database.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip token not found or expired",
        )

    # Check if trip time has exceeded expected duration
    check_and_update_overdue(trip, db)

    return TripSessionDetail(
        trip_token=trip.trip_token,
        token=trip.trip_token,
        user_id=trip.user_id,
        destination=trip.destination,
        latitude=trip.latitude,
        longitude=trip.longitude,
        status=trip.status,
        expected_arrival=trip.expected_arrival,
        expected_arrival_time=trip.expected_arrival,
        duration_minutes=trip.duration_minutes,
        created_at=trip.created_at,
        last_updated_at=trip.last_updated_at,
        shareable_link=trip.shareable_link,
    )


@router.post(
    "/update-location",
    response_model=LocationUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Live GPS Location During SafeWalk Escort",
    description=(
        "Updates device latitude and longitude coordinates for an active trip session in the database. "
        "Checks if trip time has exceeded expected arrival and flags status as 'overdue' if necessary. "
        "Raises 404 if the token is invalid or expired."
    ),
)
async def update_location(
    payload: LocationUpdateRequest,
    db: Session = Depends(get_db),
) -> LocationUpdateResponse:
    """Update live GPS coordinates for an active trip token in database."""
    trip = db.query(SafeWalkTrip).filter(SafeWalkTrip.trip_token == payload.token).first()
    if not trip:
        logger.warning(f"Attempted location update for unknown/expired token: '{payload.token}'")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip token not found or expired",
        )

    now = datetime.datetime.now(datetime.timezone.utc)
    now_iso = now.isoformat()

    # Update database coordinates
    trip.latitude = payload.latitude
    trip.longitude = payload.longitude
    trip.last_updated_at = now_iso

    # Check and update overdue status
    current_status = check_and_update_overdue(trip, db)

    db.commit()
    db.refresh(trip)

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
        expected_arrival=trip.expected_arrival,
        trip=TripSessionDetail(
            trip_token=trip.trip_token,
            token=trip.trip_token,
            user_id=trip.user_id,
            destination=trip.destination,
            latitude=trip.latitude,
            longitude=trip.longitude,
            status=trip.status,
            expected_arrival=trip.expected_arrival,
            expected_arrival_time=trip.expected_arrival,
            duration_minutes=trip.duration_minutes,
            created_at=trip.created_at,
            last_updated_at=trip.last_updated_at,
            shareable_link=trip.shareable_link,
        ),
    )


@router.get(
    "/active-trips",
    response_model=List[TripSessionDetail],
    summary="List All Active SafeWalk Escort Sessions",
    description="Inspection endpoint returning all currently registered database trip sessions.",
)
async def list_active_trips(db: Session = Depends(get_db)) -> List[TripSessionDetail]:
    """List all registered active SafeWalk sessions from database."""
    trips = db.query(SafeWalkTrip).all()
    for trip in trips:
        check_and_update_overdue(trip, db)
    return [
        TripSessionDetail(
            trip_token=trip.trip_token,
            token=trip.trip_token,
            user_id=trip.user_id,
            destination=trip.destination,
            latitude=trip.latitude,
            longitude=trip.longitude,
            status=trip.status,
            expected_arrival=trip.expected_arrival,
            expected_arrival_time=trip.expected_arrival,
            duration_minutes=trip.duration_minutes,
            created_at=trip.created_at,
            last_updated_at=trip.last_updated_at,
            shareable_link=trip.shareable_link,
        )
        for trip in trips
    ]
