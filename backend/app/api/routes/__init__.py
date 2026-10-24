"""API routes package."""

from app.api.routes import (
    chatbot,
    deepfake,
    detect,
    emergency,
    evidence,
    health,
    model_info,
    safewalk,
)

__all__ = [
    "chatbot",
    "deepfake",
    "detect",
    "emergency",
    "evidence",
    "health",
    "model_info",
    "safewalk",
]
