"""Pytest fixtures and mocked dependencies for isolated, fast test execution."""

import io
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app
from app.schemas.detection import ClassScore, InterpretationResult, PredictionResult
from app.schemas.errors import InferenceException, ModelNotReadyException
from app.services.model_service import ModelService, get_model_service


class FakeModelService(ModelService):
    """Deterministic mock model service for unit testing without downloading HF weights."""

    def __init__(
        self,
        is_loaded: bool = True,
        fail_inference: bool = False,
        artificial_score: float = 0.9421,
        human_score: float = 0.0579,
    ) -> None:
        super().__init__(model_id="umm-maybe/AI-image-detector")
        self.is_loaded = is_loaded
        self.fail_inference = fail_inference
        self.device = "cpu"
        self.labels = ["artificial", "human"]
        self.artificial_score = artificial_score
        self.human_score = human_score

    def load(self) -> bool:
        return self.is_loaded

    def predict(self, image: Image.Image):
        if not self.is_loaded:
            raise ModelNotReadyException("Model service is currently unavailable.")
        if self.fail_inference:
            raise InferenceException("Mocked inference failure occurred.")

        scores = [
            ClassScore(label="artificial", score=self.artificial_score),
            ClassScore(label="human", score=self.human_score),
        ]
        scores.sort(key=lambda s: s.score, reverse=True)
        top = scores[0]

        prediction_result = PredictionResult(
            label=top.label,
            score=top.score,
            scores=scores,
        )

        interpretation_result = InterpretationResult(
            category="ai_image_screening",
            summary=f"The screening model identified visual characteristics frequently associated with AI-generated imagery (score: {top.score * 100:.1f}%).",
            is_definitive=False,
            limitations=[
                "This is an AI-generated-image screening result, not proof that an image is authentic, manipulated, or harmful.",
                "Model was trained on 2022 image distributions; newer generative models, edited photos, camera photos, or screenshots may yield inaccurate classifications.",
                "This screening does not establish personal identity, consent, intent, or whether content is intimate or abusive.",
                "Do not use this automated score as the sole basis for legal, protective, or moderation decisions.",
            ],
        )

        return {
            "prediction": prediction_result,
            "interpretation": interpretation_result,
        }


@pytest.fixture(autouse=True)
def mock_startup_load(monkeypatch):
    """Ensure startup lifespan never downloads the real model during automated tests."""
    monkeypatch.setattr("app.main.model_service.load", lambda: True)
    monkeypatch.setattr("app.services.model_service.model_service.load", lambda: True)


@pytest.fixture
def fake_model_service() -> FakeModelService:
    """Provide a default ready fake model service."""
    return FakeModelService(is_loaded=True)


@pytest.fixture
def app_with_mock(fake_model_service: FakeModelService):
    """FastAPI application with injected fake model service."""
    app = create_app()
    app.dependency_overrides[get_model_service] = lambda: fake_model_service
    return app


@pytest.fixture
def client(app_with_mock) -> Generator[TestClient, None, None]:
    """TestClient configured with dependency overrides."""
    with TestClient(app_with_mock) as test_client:
        yield test_client


@pytest.fixture
def valid_jpeg_bytes() -> bytes:
    """Generate a valid small RGB JPEG in memory."""
    img = Image.new("RGB", (120, 120), color=(180, 50, 70))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def valid_png_bytes() -> bytes:
    """Generate a valid small RGB PNG in memory."""
    img = Image.new("RGB", (100, 100), color=(50, 120, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def valid_webp_bytes() -> bytes:
    """Generate a valid small RGB WEBP in memory."""
    img = Image.new("RGB", (80, 80), color=(80, 180, 80))
    buf = io.BytesIO()
    img.save(buf, format="WEBP")
    return buf.getvalue()


@pytest.fixture
def animated_gif_bytes() -> bytes:
    """Generate an animated multi-frame GIF in memory."""
    frame1 = Image.new("RGB", (50, 50), color="red")
    frame2 = Image.new("RGB", (50, 50), color="blue")
    buf = io.BytesIO()
    frame1.save(
        buf,
        format="GIF",
        save_all=True,
        append_images=[frame2],
        duration=100,
        loop=0,
    )
    return buf.getvalue()


@pytest.fixture
def corrupt_bytes() -> bytes:
    """Corrupt byte sequence pretending to be an image."""
    return b"\xff\xd8\xff\xe0" + b"corrupted_garbage_bytes" * 20
