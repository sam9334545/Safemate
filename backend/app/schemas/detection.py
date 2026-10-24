"""Pydantic schemas for detection and health endpoints."""

from typing import List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness check response."""

    status: str = Field("ok", description="Liveness status")
    service: str = Field("ai-image-screening-api", description="Service identifier")


class ReadinessResponse(BaseModel):
    """Model readiness response."""

    status: str = Field(..., description="Readiness status ('ready' or 'unavailable')")
    model_loaded: bool = Field(..., description="True if model is loaded and ready for inference")
    model_id: str = Field(..., description="Active Hugging Face model identifier")
    device: Optional[str] = Field("cpu", description="Inference device")


class ModelInfoResponse(BaseModel):
    """Model metadata and limitations."""

    model_id: str
    task: str = "image-classification"
    description: str
    model_loaded: bool
    inference_available: bool
    labels: List[str]
    architecture: Optional[str] = "SwinForImageClassification"
    limitations_notice: str


class ClassScore(BaseModel):
    """Individual class confidence score."""

    label: str = Field(..., description="Class name from model taxonomy (e.g., 'artificial' or 'human')")
    score: float = Field(..., description="Normalized confidence score [0.0, 1.0]")


class PredictionResult(BaseModel):
    """Leading prediction and all class distribution."""

    label: str = Field(..., description="Leading predicted class")
    score: float = Field(..., description="Confidence score of leading class")
    scores: List[ClassScore] = Field(..., description="Scores for all model classes")


class InterpretationResult(BaseModel):
    """Responsible plain-language interpretation and limitations."""

    category: str = Field("ai_image_screening", description="Interpretation category")
    summary: str = Field(..., description="Carefully worded, non-definitive explanation")
    is_definitive: bool = Field(False, description="Always False; model output is non-definitive")
    limitations: List[str] = Field(..., description="Explicit limitations and responsible use notices")


class DetectResponse(BaseModel):
    """Complete prediction response contract."""

    success: bool = True
    model_id: str
    prediction: PredictionResult
    interpretation: InterpretationResult
    request_id: str
