"""Image screening detection endpoint."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, File, Header, UploadFile, status
from fastapi.responses import JSONResponse

from app.schemas.detection import DetectResponse
from app.schemas.errors import ValidationException
from app.services.image_validation import validate_and_decode_image
from app.services.model_service import ModelService, get_model_service
from app.utils.request_id import get_request_id, set_request_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Detection"])


@router.post(
    "/detect",
    response_model=DetectResponse,
    status_code=status.HTTP_200_OK,
    summary="Screen Image for AI-Generated Characteristics",
    responses={
        200: {"description": "Inference succeeded and returned prediction"},
        400: {"description": "Malformed image, empty file, animated image, or excessive dimensions"},
        413: {"description": "Uploaded image exceeds size limit"},
        415: {"description": "Unsupported media type or format"},
        503: {"description": "Screening model is not loaded or initializing"},
        500: {"description": "Inference or processing failure"},
    },
)
async def detect_image(
    file: Optional[UploadFile] = File(None, description="Image file to analyze (JPEG, PNG, WEBP)"),
    service: ModelService = Depends(get_model_service),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
) -> JSONResponse:
    req_id = x_request_id or get_request_id()

    # 1. Validate file presence
    if file is None:
        raise ValidationException(
            message="No file was received. Please provide an image file in the 'file' multipart field.",
            code="MISSING_FILE",
            status_code=400,
            request_id=req_id,
        )

    # 2. Read bytes into memory safely
    try:
        file_bytes = await file.read()
    except Exception as exc:
        logger.error(f"Failed to read uploaded file stream: {type(exc).__name__}")
        raise ValidationException(
            message="Could not read the uploaded file stream.",
            code="INVALID_IMAGE",
            status_code=400,
            request_id=req_id,
        )
    finally:
        await file.close()

    # 3. Validate and decode into RGB PIL image in memory
    img = None
    try:
        img = validate_and_decode_image(
            file_bytes=file_bytes,
            filename=file.filename,
            content_type=file.content_type,
        )

        # 4. Perform model inference
        prediction_output = service.predict(img)

        # 5. Format response adhering to API contract
        response_data = {
            "success": True,
            "model_id": service.model_id,
            "prediction": prediction_output["prediction"].model_dump(),
            "interpretation": prediction_output["interpretation"].model_dump(),
            "request_id": req_id,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
            headers={"X-Request-ID": req_id},
        )

    finally:
        # Guarantee memory release of Pillow image
        if img is not None:
            try:
                img.close()
            except Exception:
                pass
        # Clear raw file_bytes reference
        del file_bytes
