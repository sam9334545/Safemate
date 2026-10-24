"""Model information endpoint providing public architecture and metadata."""

from fastapi import APIRouter, Depends, status

from app.schemas.detection import ModelInfoResponse
from app.services.model_service import ModelService, get_model_service

router = APIRouter(prefix="", tags=["Model Info"])


@router.get(
    "/model-info",
    response_model=ModelInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Model Information and Limitations",
)
def get_model_info(
    service: ModelService = Depends(get_model_service),
) -> ModelInfoResponse:
    """Return public metadata, supported classes, and limitations for the screening model."""
    return ModelInfoResponse(
        model_id=service.model_id,
        task="image-classification",
        description=(
            "Pretrained Swin Transformer classifier for screening AI-generated artistic images vs. human-created images. "
            "Trained with AutoTrain on 2022 image data."
        ),
        model_loaded=service.is_loaded,
        inference_available=service.is_loaded,
        labels=service.labels,
        architecture="SwinForImageClassification",
        limitations_notice=(
            "This model is an AI-generated-image screening tool developed in October 2022. "
            "It is not a definitive deepfake detector, does not prove manipulation or authenticity, "
            "and does not evaluate personal identity or consent. Newer diffusion models and general photos may yield false results."
        ),
    )
