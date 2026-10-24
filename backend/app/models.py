"""SQLAlchemy database models for SafeWalk, Evidence Vault, and Emergency systems."""

from __future__ import annotations

from sqlalchemy import Boolean, Column, Float, Integer, String, Text
from app.database import Base


class UserModel(Base):
    """Persistent database model for authenticated users."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(String(64), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<UserModel(id={self.id}, email='{self.email}', is_active={self.is_active})>"


# Semantic alias
User = UserModel


class SafeWalkTrip(Base):
    """Persistent database model for SafeWalk trip tokens and live escort sessions."""

    __tablename__ = "safewalk_trips"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    trip_token = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(String(128), index=True, nullable=False)
    destination = Column(String(512), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(String(32), default="active", nullable=False)
    created_at = Column(String(64), nullable=False)
    expected_arrival = Column(String(64), nullable=False)
    last_updated_at = Column(String(64), nullable=True)
    shareable_link = Column(String(256), nullable=False)

    def __repr__(self) -> str:
        return f"<SafeWalkTrip(token='{self.trip_token}', user_id='{self.user_id}', status='{self.status}')>"


class EvidenceRecord(Base):
    """Persistent database model for encrypted/disguised evidence files and chain of custody."""

    __tablename__ = "evidence_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    evidence_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(String(128), index=True, nullable=False)
    file_name = Column(String(512), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, nullable=False)
    sha256_checksum = Column(String(64), index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    note = Column(Text, nullable=True)
    timestamp = Column(String(64), nullable=False)
    simulated_dispatch_status = Column(
        String(128),
        default="CONFIRMED_DELIVERED_TO_TRUSTED_CONTACTS",
        nullable=False,
    )
    google_maps_url = Column(String(512), nullable=False)
    contacts_alerted = Column(Text, default="[]", nullable=False)

    def __repr__(self) -> str:
        return f"<EvidenceRecord(id='{self.evidence_id}', user_id='{self.user_id}', hash='{self.sha256_checksum[:8]}...')>"


class EmergencySOSAlert(Base):
    """Persistent database model for Emergency SOS panic alerts."""

    __tablename__ = "emergency_sos_alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(String(128), index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(String(64), nullable=False)
    status = Column(String(32), default="success", nullable=False)
    contacts_alerted_count = Column(Integer, default=0, nullable=False)
    google_maps_url = Column(String(512), nullable=False)
    distress_message = Column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"<EmergencySOSAlert(alert_id='{self.alert_id}', user_id='{self.user_id}', status='{self.status}')>"
