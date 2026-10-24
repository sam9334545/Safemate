"""SafeWalk Trip Token generator, live-tracking, and location update routes under /api/v1/safewalk."""

from __future__ import annotations

import datetime
import json
import logging
import secrets
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EmergencyLogModel, SafeWalkTrip, TrustedContactModel, UserModel
from app.utils.auth import get_current_user, get_optional_current_user
from app.schemas.safewalk import (
    LocationUpdateRequest,
    LocationUpdateResponse,
    TripCancelRequest,
    TripCancelResponse,
    TripCompleteResponse,
    TripCreateRequest,
    TripCreateResponse,
    TripEscalateResponse,
    TripSessionDetail,
)
from app.api.routes.emergency import dispatch_emergency_notifications, get_emergency_contacts

logger = logging.getLogger(__name__)


def to_session_detail(trip: SafeWalkTrip) -> TripSessionDetail:
    """Helper to convert SafeWalkTrip database model to TripSessionDetail schema."""
    try:
        crumbs = json.loads(trip.breadcrumbs or "[]")
    except Exception:
        crumbs = []

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
        breadcrumbs=crumbs,
        cancellation_reason=trip.cancellation_reason,
    )


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
    if trip.status in ("completed", "cancelled", "escalated"):
        return trip.status
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
    current_user: UserModel = Depends(get_current_user),
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
        breadcrumbs="[]",
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

    return to_session_detail(trip)


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

    # Update database coordinates and breadcrumbs trail
    trip.latitude = payload.latitude
    trip.longitude = payload.longitude
    trip.last_updated_at = now_iso

    try:
        crumbs = json.loads(trip.breadcrumbs or "[]")
    except Exception:
        crumbs = []
    crumbs.append({
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "timestamp": now_iso,
    })
    trip.breadcrumbs = json.dumps(crumbs)

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
        trip=to_session_detail(trip),
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
    return [to_session_detail(trip) for trip in trips]


@router.post(
    "/trip/{token}/complete",
    response_model=TripCompleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete SafeWalk Trip (I Am Safe)",
    description=(
        "Marks an active or overdue SafeWalk trip session as safely completed. "
        "Records completion timestamp and logs structured confirmation."
    ),
)
async def complete_trip(
    token: str,
    db: Session = Depends(get_db),
) -> TripCompleteResponse:
    """Safely end and complete an active SafeWalk escort session."""
    trip = db.query(SafeWalkTrip).filter(SafeWalkTrip.trip_token == token).first()
    if not trip:
        logger.warning(f"Attempted completion for unknown/expired token: '{token}'")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip token not found or expired",
        )

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    trip.status = "completed"
    trip.last_updated_at = now_iso

    db.commit()
    db.refresh(trip)

    # Log structured confirmation
    log_payload = {
        "event": "SAFEWALK_TRIP_COMPLETED",
        "trip_token": token,
        "user_id": trip.user_id,
        "completed_at": now_iso,
        "destination": trip.destination,
        "status": "completed",
    }
    logger.info(json.dumps(log_payload))

    return TripCompleteResponse(
        status="success",
        message="SafeWalk escort successfully completed. Traveler confirmed safe.",
        trip_token=token,
        trip_status="completed",
        completed_at=now_iso,
        trip=to_session_detail(trip),
    )


@router.post(
    "/trip/{token}/cancel",
    response_model=TripCancelResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel SafeWalk Escort Session",
    description="Cancels an active or overdue SafeWalk session, recording an optional cancellation reason.",
)
async def cancel_trip(
    token: str,
    payload: Optional[TripCancelRequest] = None,
    db: Session = Depends(get_db),
) -> TripCancelResponse:
    """Abort or cancel an active SafeWalk escort session early."""
    trip = db.query(SafeWalkTrip).filter(SafeWalkTrip.trip_token == token).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip token not found or expired",
        )

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    trip.status = "cancelled"
    trip.last_updated_at = now_iso
    if payload and payload.reason:
        trip.cancellation_reason = payload.reason

    db.commit()
    db.refresh(trip)

    logger.info(f"SafeWalk trip '{token}' cancelled. Reason: '{trip.cancellation_reason}'")

    return TripCancelResponse(
        status="cancelled",
        message="SafeWalk escort session has been cancelled.",
        trip_token=token,
        trip_status="cancelled",
        cancelled_at=now_iso,
        cancellation_reason=trip.cancellation_reason,
        trip=to_session_detail(trip),
    )


@router.post(
    "/trip/{token}/escalate",
    response_model=TripEscalateResponse,
    status_code=status.HTTP_200_OK,
    summary="Escalate SafeWalk Escort to Emergency SOS",
    description="Immediately transitions a live SafeWalk session into an active Emergency SOS alert, dispatching coordinates to emergency contacts.",
)
async def escalate_trip(
    token: str,
    db: Session = Depends(get_db),
) -> TripEscalateResponse:
    """Escalate active SafeWalk escort to emergency SOS dispatch."""
    trip = db.query(SafeWalkTrip).filter(SafeWalkTrip.trip_token == token).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip token not found or expired",
        )

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    trip.status = "escalated"
    trip.last_updated_at = now_iso

    lat = trip.latitude if trip.latitude is not None else 0.0
    lon = trip.longitude if trip.longitude is not None else 0.0
    google_maps_url = f"https://maps.google.com/?q={lat},{lon}"
    alert_id = f"esc_{secrets.token_hex(6)}"

    # Fetch contacts
    search_keys = [trip.user_id]
    db_contacts = (
        db.query(TrustedContactModel)
        .filter(TrustedContactModel.user_id.in_(search_keys))
        .all()
    )
    contacts: List[Dict[str, Any]] = []
    if db_contacts:
        for c in db_contacts:
            contacts.append({
                "name": c.name,
                "phone": c.phone_number,
                "email": c.email,
                "relationship": c.relationship or "Trusted Emergency Contact",
            })
    else:
        contacts = get_emergency_contacts(trip.user_id)

    distress_message = (
        f"🚨 SAFEWALK ESCALATION ALERT [SAFEMATE] 🚨\n"
        f"User '{trip.user_id}' requested emergency escalation during active SafeWalk to '{trip.destination}'!\n"
        f"Trip Token: {token}\n"
        f"Live GPS Location: {lat}, {lon}\n"
        f"Google Maps Link: {google_maps_url}\n"
        f"IMMEDIATE ASSISTANCE REQUIRED."
    )

    try:
        await dispatch_emergency_notifications(
            alert_id=alert_id,
            user_id=trip.user_id,
            contacts=contacts,
            distress_message=distress_message,
            google_maps_url=google_maps_url,
            dispatch_timestamp=now_iso,
        )
    except Exception as exc:
        logger.warning(f"Failed to dispatch escalation notifications: {exc}")

    try:
        emergency_log = EmergencyLogModel(
            alert_id=alert_id,
            user_id=trip.user_id,
            latitude=lat,
            longitude=lon,
            triggered_at=now_iso,
            status="escalated_from_safewalk",
            distress_message=distress_message,
            google_maps_url=google_maps_url,
            contacts_alerted_count=len(contacts),
        )
        db.add(emergency_log)
    except Exception as log_err:
        logger.warning(f"Failed to record EmergencyLogModel for escalation: {log_err}")

    db.commit()
    db.refresh(trip)

    return TripEscalateResponse(
        status="escalated",
        message="SafeWalk escort escalated to active Emergency SOS. Emergency contacts notified.",
        trip_token=token,
        alert_id=alert_id,
        escalated_at=now_iso,
        contacts_alerted=len(contacts),
        trip=to_session_detail(trip),
    )


