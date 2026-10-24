"""Optional live integration test with real Hugging Face model weights."""

import pytest
from PIL import Image

from app.services.model_service import ModelService


@pytest.mark.integration
def test_real_huggingface_model_inference():
    """Live verification using real umm-maybe/AI-image-detector model from Hugging Face."""
    pytest.importorskip("torch")
    service = ModelService("umm-maybe/AI-image-detector")
    success = service.load()
    assert success is True, f"Failed to load real model: {service.initialization_error}"
    assert service.is_loaded is True
    assert "artificial" in service.labels
    assert "human" in service.labels

    # Run inference on a generated RGB PIL image
    test_image = Image.new("RGB", (224, 224), color=(140, 80, 200))
    result = service.predict(test_image)

    assert "prediction" in result
    assert "interpretation" in result

    pred = result["prediction"]
    assert pred.label in ["artificial", "human"]
    assert 0.0 <= pred.score <= 1.0
    assert len(pred.scores) == 2

    # Clean up memory
    del service.model
    del service.processor
    service.model = None
    service.processor = None
