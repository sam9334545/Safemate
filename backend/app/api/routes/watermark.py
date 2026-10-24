"""Forensic Leak Tracer API routes for embedding and extracting invisible watermarks."""

from __future__ import annotations

import json
import logging
from typing import List, Optional
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status

from app.schemas.watermark import WatermarkExtractResponse
from app.services.watermark_service import watermark_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/watermark", tags=["Forensic Leak Tracer"])


@router.post(
    "/embed",
    summary="Embed Invisible Recipient Watermark",
    description="Embeds a visually imperceptible, cryptographically signed watermark identifying a specific recipient.",
)
async def embed_watermark(
    file: UploadFile = File(..., description="Target image file (JPEG, PNG, WEBP)"),
    recipient_name: str = Form(..., description="Name of the person who will receive this copy"),
    recipient_id: Optional[str] = Form(None, description="Optional unique identifier for recipient"),
    owner_id: Optional[str] = Form("usr_safemate", description="SafeMate user ID of the sender"),
    notes: Optional[str] = Form(None, description="Optional sharing terms or notes"),
):
    """Embed an invisible watermark into an image and return the protected PNG file."""
    image_bytes = await file.read()
    output_bytes, media_type, meta = watermark_service.embed(
        image_bytes=image_bytes,
        recipient_name=recipient_name,
        recipient_id=recipient_id,
        owner_id=owner_id,
        notes=notes,
    )

    clean_name = "".join(c for c in recipient_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    filename = f"safemate_copy_{clean_name}.png"

    return Response(
        content=output_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Watermark-Recipient": recipient_name,
            "X-Watermark-ID": meta["recipient_id"],
            "X-Watermark-Fingerprint": meta["fingerprint"],
        },
    )


@router.post(
    "/batch-embed",
    summary="Batch Generate Watermarked Copies for Multiple Recipients",
    description="Generates a downloadable ZIP containing individually watermarked copies for each recipient plus an audit manifest.",
)
async def batch_embed_watermarks(
    file: UploadFile = File(..., description="Image to share with multiple people"),
    recipients: str = Form(..., description="Comma-separated or JSON list of recipient names (e.g. 'Liam, Jake, Sarah')"),
    owner_id: Optional[str] = Form("usr_safemate", description="SafeMate user ID"),
    notes: Optional[str] = Form(None, description="Optional sharing context"),
):
    """Batch embed watermarks for multiple recipients and return a ZIP file."""
    # Parse comma-separated or JSON array of names
    recipient_list: List[str] = []
    recipients_trimmed = recipients.strip()
    if recipients_trimmed.startswith("["):
        try:
            parsed = json.loads(recipients_trimmed)
            if isinstance(parsed, list):
                recipient_list = [str(item) for item in parsed]
        except Exception:
            pass

    if not recipient_list:
        recipient_list = [item.strip() for item in recipients.split(",") if item.strip()]

    if not recipient_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide at least one recipient name.",
        )

    image_bytes = await file.read()
    zip_bytes, media_type = watermark_service.batch_embed(
        image_bytes=image_bytes,
        recipients=recipient_list,
        owner_id=owner_id,
        notes=notes,
    )

    return Response(
        content=zip_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": 'attachment; filename="safemate_protected_bundle.zip"',
            "X-Recipient-Count": str(len(recipient_list)),
        },
    )


@router.post(
    "/extract",
    response_model=WatermarkExtractResponse,
    summary="Extract Watermark from Suspected Leaked Media",
    description="Decodes hidden forensic watermarks from uploaded image to trace which recipient leaked the content.",
)
async def extract_watermark(
    file: UploadFile = File(..., description="Suspected leaked screenshot or photograph"),
) -> WatermarkExtractResponse:
    """Inspect image and return forensic analysis report identifying the leaker."""
    image_bytes = await file.read()
    return watermark_service.extract(image_bytes)


@router.get("/health")
async def watermark_health():
    """Health status probe for forensic watermark engine."""
    return {
        "status": "healthy",
        "service": "forensic_leak_tracer",
        "algorithm": "spatial_lsb_redundant_hmac_sha256",
    }
