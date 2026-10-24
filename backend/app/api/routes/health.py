"""Health and readiness check endpoints."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.schemas.detection import HealthResponse, ReadinessResponse
from app.services.model_service import ModelService, get_model_service

router = APIRouter(prefix="", tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Liveness Check",
)
def get_health() -> HealthResponse:
    """Return 200 when the web application process is running."""
    return HealthResponse(
        status="ok",
        service=settings.APP_NAME,
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={
        200: {"description": "Model is loaded and ready for inference"},
        503: {"description": "Model is not loaded or currently unavailable"},
    },
    summary="Model Readiness Check",
)
def get_readiness(
    service: ModelService = Depends(get_model_service),
) -> JSONResponse:
    """Return 200 if model and processor are ready for inference; 503 otherwise."""
    if service.is_loaded:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ready",
                "model_loaded": True,
                "model_id": service.model_id,
                "device": service.device,
            },
        )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "unavailable",
            "model_loaded": False,
            "model_id": service.model_id,
            "device": service.device,
        },
    )
