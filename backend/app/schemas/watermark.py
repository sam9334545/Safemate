"""Pydantic schemas for the Forensic Leak Tracer invisible watermarking service."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WatermarkPayload(BaseModel):
    """Decoded internal payload embedded inside the media."""

    recipient_name: str = Field(..., description="Name of the person who received this specific copy")
    recipient_id: str = Field(..., description="Unique ID for recipient tracking")
    owner_id: str = Field(..., description="SafeMate user ID of the original media owner")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp when watermark was generated")
    notes: Optional[str] = Field(default=None, description="Optional context or sharing restriction notes")


class WatermarkAuditReport(BaseModel):
    """Forensic investigation audit report for court or cyber legal proceedings."""

    case_reference_id: str = Field(..., description="Unique forensic case reference token")
    identified_leaker: Optional[str] = Field(None, description="Name of the recipient who leaked the media")
    recipient_id: Optional[str] = Field(None, description="Identifier of the leaker")
    original_owner: Optional[str] = Field(None, description="Owner who distributed the copy")
    sharing_timestamp: Optional[str] = Field(None, description="When the specific copy was generated")
    cryptographic_integrity: str = Field(..., description="VERIFIED_AUTHENTIC, SIGNATURE_TAMPERED, or NO_WATERMARK")
    evidence_affidavit: str = Field(..., description="Digital sworn declaration text for cyber legal casework")
    actionable_remedies: List[str] = Field(default_factory=list, description="Prescribed legal steps under cyber safety laws")


class WatermarkExtractResponse(BaseModel):
    """Response returned after inspecting a suspected leaked image."""

    status: str = Field(..., description="'match_found', 'no_watermark_detected', or 'signature_tampered'")
    detected: bool = Field(..., description="True if a valid Safemate forensic watermark was located")
    recipient_name: Optional[str] = Field(None, description="Name of the recipient identified")
    recipient_id: Optional[str] = Field(None, description="Unique identifier of the recipient")
    owner_id: Optional[str] = Field(None, description="Owner ID of the original sender")
    timestamp: Optional[str] = Field(None, description="ISO timestamp of copy issuance")
    tamper_detected: bool = Field(default=False, description="True if cryptographic HMAC signature was modified")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence rating (0.0 to 1.0)")
    watermark_fingerprint: Optional[str] = Field(None, description="Cryptographic SHA-256 fingerprint of the watermark payload")
    audit_report: WatermarkAuditReport = Field(..., description="Comprehensive forensic casework report")


class BatchWatermarkItem(BaseModel):
    """Metadata summary of an individual watermarked copy in a batch."""

    recipient_name: str
    recipient_id: str
    file_name: str
    fingerprint: str
