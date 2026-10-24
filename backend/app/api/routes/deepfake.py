"""Video deepfake screening route under /api/v1/deepfake/detect."""

import logging
import os
from typing import Optional
from fastapi import APIRouter, Depends, File, Header, Query, UploadFile, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.schemas.deepfake import VideoDeepfakeResponse
from app.schemas.errors import ValidationException
from app.services.video_deepfake_service import VideoDeepfakeService, get_video_deepfake_service
from app.utils.request_id import get_request_id, set_request_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deepfake", tags=["Video Deepfake Screening"])


@router.post(
    "/detect",
    response_model=VideoDeepfakeResponse,
    status_code=status.HTTP_200_OK,
    summary="Screen Video for Face Manipulation & Deepfakes",
    responses={
        200: {"description": "Video screening succeeded"},
        400: {"description": "Empty, corrupted, or invalid video file"},
        413: {"description": "Video file exceeds upload size limit"},
        415: {"description": "Unsupported video media type"},
        503: {"description": "Video deepfake screening model is not ready"},
        500: {"description": "Processing or inference error"},
    },
)
async def detect_video_deepfake(
    file: Optional[UploadFile] = File(None, description="Video file to inspect (.mp4, .mov, .avi, .webm, .mkv)"),
    num_frames: Optional[int] = Query(20, ge=5, le=30, description="Number of frames to sample evenly across video"),
    service: VideoDeepfakeService = Depends(get_video_deepfake_service),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
) -> JSONResponse:
    """Screen an uploaded video file to detect facial manipulation and deepfakes."""
    req_id = x_request_id or get_request_id()

    # 1. Validate file presence
    if file is None:
        raise ValidationException(
            message="No video file was received. Please provide a video in the 'file' multipart field.",
            code="MISSING_FILE",
            status_code=400,
            request_id=req_id,
        )

    # 2. Check extension
    if file.filename:
        _, ext = os.path.splitext(file.filename.lower())
        if ext and ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
            raise ValidationException(
                message=f"Video extension '{ext}' is not supported. Supported extensions: {', '.join(settings.ALLOWED_VIDEO_EXTENSIONS)}.",
                code="UNSUPPORTED_MEDIA_TYPE",
                status_code=415,
                request_id=req_id,
            )

    # 3. Read video bytes
    try:
        video_bytes = await file.read()
    except Exception as exc:
        logger.error(f"Failed to read uploaded video stream: {type(exc).__name__}")
        raise ValidationException(
            message="Could not read the uploaded video stream.",
            code="INVALID_VIDEO",
            status_code=400,
            request_id=req_id,
        )
    finally:
        await file.close()

    # 4. Check for empty payload
    if not video_bytes or len(video_bytes) == 0:
        raise ValidationException(
            message="Uploaded video file is empty. Please select a valid video.",
            code="EMPTY_FILE",
            status_code=400,
            request_id=req_id,
        )

    # 5. Check size limit
    if len(video_bytes) > settings.max_video_upload_bytes:
        raise ValidationException(
            message=f"Video size ({len(video_bytes) / (1024 * 1024):.1f}MB) exceeds the maximum allowed limit of {settings.MAX_VIDEO_UPLOAD_MB}MB.",
            code="FILE_TOO_LARGE",
            status_code=413,
            request_id=req_id,
        )

    try:
        # 6. Execute video deepfake screening
        result = service.predict_video(
            video_bytes=video_bytes,
            filename=file.filename,
            num_frames=num_frames,
        )

        result["success"] = True
        result["request_id"] = req_id

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result,
            headers={"X-Request-ID": req_id},
        )
    finally:
        del video_bytes
