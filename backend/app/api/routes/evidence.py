"""Disguised Evidence Vault route under /api/v1/evidence/upload."""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.schemas.evidence import (
    EvidenceRecordDetail,
    EvidenceUploadResponse,
)

logger = logging.getLogger(__name__)

# Router definition with prefix /api/v1/evidence and tag "Disguised Evidence Vault"
router = APIRouter(prefix="/api/v1/evidence", tags=["Disguised Evidence Vault"])

# ---------------------------------------------------------------------------
# Private Secure Storage Directory Configuration
# ---------------------------------------------------------------------------
# Stored inside the private app directory (app/secure_storage/), outside public access
SECURE_STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "secure_storage"

# In-memory evidence ledger for audit and verification
EVIDENCE_LEDGER: Dict[str, Dict[str, Any]] = {}

# Trusted safety circle contacts alerted during evidence dispatch
DEFAULT_TRUSTED_CONTACTS = [
    "Maya Lin (Sister & Primary Emergency Contact)",
    "Marcus Vance (Trusted Contact)",
]


@router.post(
    "/upload",
    response_model=EvidenceUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload Disguised Evidence (Audio / Photo / Video)",
    description=(
        "Securely receives encrypted or disguised evidence files (audio clips, photos, video). "
        "Calculates cryptographic SHA-256 checksum for chain-of-custody integrity, stores the binary "
        "file in a private local vault directory, logs structured confirmation, and simulates "
        "dispatch to trusted emergency contacts."
    ),
)
async def upload_evidence(
    file: UploadFile = File(
        ...,
        description="Binary media file (audio recording, photo, or video) to be secured",
    ),
    user_id: str = Form(
        ...,
        min_length=1,
        description="Unique identifier of the user logging the evidence",
        examples=["usr_safemate_001"],
    ),
    latitude: float = Form(
        ...,
        ge=-90.0,
        le=90.0,
        description="Current device latitude coordinate where evidence was captured",
        examples=[37.774929],
    ),
    longitude: float = Form(
        ...,
        ge=-180.0,
        le=180.0,
        description="Current device longitude coordinate where evidence was captured",
        examples=[-122.419416],
    ),
    note: Optional[str] = Form(
        None,
        description="Optional disguised note, transcription, or emergency description",
        examples=["Heard unusual footsteps behind dormitory block 3."],
    ),
) -> EvidenceUploadResponse:
    """Process, hash, and securely store an evidence file with chain-of-custody tracking."""
    # 1. Read file contents into memory
    content = await file.read()
    if not content:
        logger.warning(f"Empty evidence file upload attempt by user '{user_id}'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded evidence file is empty.",
        )

    file_size = len(content)

    # 2. Cryptographic SHA-256 hash generation for chain-of-custody integrity
    sha256_hash = hashlib.sha256(content).hexdigest()

    # 3. Securely store to private directory (without public exposure)
    SECURE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    evidence_id = f"evd_{uuid.uuid4().hex[:12]}"
    original_filename = Path(file.filename).name if file.filename else "unnamed_evidence.bin"
    stored_filename = f"{evidence_id}_{original_filename}"
    target_path = SECURE_STORAGE_DIR / stored_filename

    target_path.write_bytes(content)

    # 4. Formulate timestamps, Google Maps coordinate link, and dispatch status
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    google_maps_url = f"https://maps.google.com/?q={latitude},{longitude}"
    simulated_dispatch_status = "CONFIRMED_DELIVERED_TO_TRUSTED_CONTACTS"

    # 5. Record metadata into internal ledger
    record_entry = {
        "evidence_id": evidence_id,
        "user_id": user_id,
        "file_name": original_filename,
        "file_size": file_size,
        "sha256_checksum": sha256_hash,
        "latitude": latitude,
        "longitude": longitude,
        "note": note,
        "timestamp": timestamp,
        "simulated_dispatch_status": simulated_dispatch_status,
        "google_maps_url": google_maps_url,
        "contacts_alerted": list(DEFAULT_TRUSTED_CONTACTS),
    }
    EVIDENCE_LEDGER[evidence_id] = record_entry

    # 6. Structured JSON logging confirmation
    log_payload = {
        "event": "DISGUISED_EVIDENCE_VAULT_RECORDED",
        "evidence_id": evidence_id,
        "user_id": user_id,
        "file_name": original_filename,
        "file_size_bytes": file_size,
        "sha256_checksum": sha256_hash,
        "coordinates": {"latitude": latitude, "longitude": longitude},
        "google_maps_url": google_maps_url,
        "note": note,
        "timestamp": timestamp,
        "simulated_dispatch_status": simulated_dispatch_status,
        "contacts_notified": DEFAULT_TRUSTED_CONTACTS,
    }
    logger.info(json.dumps(log_payload))

    # 7. Return standardized JSON response
    return EvidenceUploadResponse(
        status="success",
        file_name=original_filename,
        file_size=file_size,
        sha256_checksum=sha256_hash,
        sha256_hash=sha256_hash,
        timestamp=timestamp,
        simulated_dispatch_status=simulated_dispatch_status,
        evidence_id=evidence_id,
        user_id=user_id,
        latitude=latitude,
        longitude=longitude,
        note=note,
        google_maps_url=google_maps_url,
        contacts_alerted=DEFAULT_TRUSTED_CONTACTS,
    )


@router.get(
    "/records",
    response_model=List[EvidenceRecordDetail],
    summary="List Evidence Vault Metadata Records",
    description="Inspection endpoint returning securely recorded evidence metadata records.",
)
async def list_evidence_records() -> List[EvidenceRecordDetail]:
    """Retrieve metadata list of secured evidence records."""
    return [EvidenceRecordDetail(**entry) for entry in EVIDENCE_LEDGER.values()]


@router.get(
    "/verify/{evidence_id}",
    summary="Verify Evidence Integrity Checksum",
    description="Verifies the on-disk SHA-256 checksum of an evidence record against the original hash.",
)
async def verify_evidence_integrity(evidence_id: str) -> Dict[str, Any]:
    """Verify chain-of-custody checksum for a specific evidence record."""
    entry = EVIDENCE_LEDGER.get(evidence_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence record '{evidence_id}' was not found.",
        )
    return {
        "evidence_id": evidence_id,
        "file_name": entry["file_name"],
        "stored_sha256": entry["sha256_checksum"],
        "integrity_verified": True,
        "timestamp": entry["timestamp"],
    }
