"""Error schemas and standardized application exceptions."""

from typing import Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detailed error payload."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable safe explanation")


class ErrorResponse(BaseModel):
    """Standardized API error response format."""

    success: bool = False
    error: ErrorDetail
    request_id: str


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.request_id = request_id


class ValidationException(AppException):
    """Exception raised when input validation fails."""

    def __init__(
        self,
        message: str,
        code: str = "VALIDATION_ERROR",
        status_code: int = 400,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=status_code, request_id=request_id)


class ModelNotReadyException(AppException):
    """Exception raised when inference model is not initialized."""

    def __init__(
        self,
        message: str = "Model service is currently initializing or unavailable.",
        code: str = "MODEL_NOT_READY",
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=503, request_id=request_id)


class InferenceException(AppException):
    """Exception raised during prediction execution."""

    def __init__(
        self,
        message: str = "An error occurred during image screening inference.",
        code: str = "INFERENCE_FAILURE",
        status_code: int = 500,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message=message, code=code, status_code=status_code, request_id=request_id)
