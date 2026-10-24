"""Pydantic schemas for the video deepfake detection endpoint."""

from typing import List, Optional
from pydantic import BaseModel, Field


STANDARD_VIDEO_LIMITATIONS: List[str] = [
    "This is an automated video deepfake screening estimate, not definitive proof that a video is authentic, manipulated, or legally admissible evidence.",
    "Detection accuracy is dependent on visible facial clarity, lighting, compression, frame rate, and head movement.",
    "This screening tool does not verify individual identity, consent, intent, or whether video content is non-consensual or abusive.",
    "Do not use this automated screening score as the sole basis for moderation, legal, or protective actions."
]


class VideoDeepfakeResponse(BaseModel):
    """Structured response schema for POST /api/v1/deepfake/detect."""

    success: bool = Field(True, description="Whether the request was processed successfully")
    status: str = Field(..., description="Processing outcome: 'success', 'no_face_detected', or 'inconclusive'")
    prediction: Optional[str] = Field(
        None,
        description="Screening judgment: 'potential_manipulation_detected', 'no_manipulation_detected_by_model', or 'inconclusive'",
    )
    score: Optional[float] = Field(
        None,
        description="Model confidence score for synthetic manipulation [0.0, 1.0], or null if no face detected",
    )
    score_type: str = Field(
        "confidence_score",
        description="Type of metric; raw confidence score, not calibrated statistical probability",
    )
    model_name: str = Field(..., description="Pretrained model identifier")
    frames_sampled: int = Field(..., description="Total number of video frames sampled for inspection")
    faces_detected: int = Field(..., description="Number of sampled frames with detectable facial regions")
    message: str = Field(..., description="Neutral, plain-language explanation of findings")
    limitations: List[str] = Field(
        default_factory=lambda: list(STANDARD_VIDEO_LIMITATIONS),
        description="Responsible usage disclaimers and operational limitations",
    )
    request_id: str = Field(..., description="Traceable correlation ID without personal data")


class DeepfakeReadinessResponse(BaseModel):
    """Schema for GET /api/v1/deepfake/ready."""

    status: str = Field(..., description="'ready' or 'unavailable'")
    model_loaded: bool = Field(..., description="Whether MS-EffGCViT model is loaded")
    detector_loaded: bool = Field(..., description="Whether YOLO face detector is loaded")
    model_id: str = Field(..., description="Video model identifier")
    device: str = Field(..., description="Execution compute device (e.g. cpu)")


class DeepfakeModelInfoResponse(BaseModel):
    """Schema for GET /api/v1/deepfake/model-info."""

    model_id: str = Field(..., description="Model identifier on Hugging Face Hub")
    task: str = Field("video-deepfake-screening", description="Machine learning task name")
    architecture: str = Field("MS-EffGCViT-B0", description="Underlying neural network architecture")
    face_detector: str = Field("YOLOv8n-Face", description="Face localization model")
    description: str = Field(..., description="Plain-language description of capabilities")
    model_loaded: bool = Field(..., description="Whether model weights are loaded in memory")
    inference_available: bool = Field(..., description="Whether inference is operational")
    labels: List[str] = Field(
        default_factory=lambda: [
            "potential_manipulation_detected",
            "no_manipulation_detected_by_model",
            "inconclusive",
            "no_face_detected",
        ],
        description="Possible screening classifications",
    )
    limitations_notice: str = Field(..., description="Safemate responsible screening notice")

