"""Pydantic schemas for the Disguised Evidence Vault service."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class EvidenceUploadResponse(BaseModel):
    """Response returned upon successful cryptographic archiving of disguised evidence."""

    status: str = Field(
        default="success",
        description="Status confirmation of the evidence storage and simulated dispatch",
    )
    file_name: str = Field(
        ...,
        description="Original name of the uploaded evidence file",
    )
    file_size: int = Field(
        ...,
        description="Total size of the uploaded evidence file in bytes",
    )
    sha256_checksum: str = Field(
        ...,
        description="Cryptographic SHA-256 hash of the file bytes for chain-of-custody verification",
    )
    sha256_hash: str = Field(
        ...,
        description="Semantic alias for sha256_checksum",
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp when evidence was received and recorded",
    )
    simulated_dispatch_status: str = Field(
        ...,
        description="Confirmation status of simulated evidence dispatch to trusted contacts",
    )
    evidence_id: str = Field(
        ...,
        description="Unique evidence tracking identifier",
    )
    user_id: str = Field(
        ...,
        description="Identifier of the user who recorded the evidence",
    )
    latitude: float = Field(
        ...,
        description="GPS latitude where evidence was captured",
    )
    longitude: float = Field(
        ...,
        description="GPS longitude where evidence was captured",
    )
    note: Optional[str] = Field(
        default=None,
        description="Optional contextual note or incident description",
    )
    google_maps_url: str = Field(
        ...,
        description="Google Maps coordinates link corresponding to the capture location",
    )
    contacts_alerted: List[str] = Field(
        default_factory=list,
        description="List of trusted safety contacts who received the simulated evidence alert",
    )


class EvidenceRecordDetail(BaseModel):
    """Metadata record of an archived piece of evidence."""

    evidence_id: str
    user_id: str
    file_name: str
    file_size: int
    sha256_checksum: str
    latitude: float
    longitude: float
    note: Optional[str] = None
    timestamp: str
    simulated_dispatch_status: str
    google_maps_url: str


class EvidenceDeleteResponse(BaseModel):
    """Response returned upon securely shredding and deleting an evidence record."""

    status: str = Field(default="success", description="Status confirmation")
    message: str = Field(..., description="Confirmation explanation message")
    evidence_id: str = Field(..., description="Unique identifier of the deleted evidence record")

