"""Tests for the video deepfake detection endpoint POST /api/v1/deepfake/detect."""

import os
import tempfile
from typing import Generator
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app
from app.services.model_service import get_model_service
from app.services.video_deepfake_service import (
    VideoDeepfakeService,
    get_video_deepfake_service,
)
from tests.conftest import FakeModelService, FakeVideoDeepfakeService


def test_deepfake_detect_success(client: TestClient, valid_mp4_bytes: bytes):
    """Test successful video deepfake screening with valid video upload."""
    response = client.post(
        "/api/v1/deepfake/detect",
        files={"file": ("test_clip.mp4", valid_mp4_bytes, "video/mp4")},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["status"] == "success"
    assert data["prediction"] == "potential_manipulation_detected"
    assert data["score"] == 0.88
    assert data["score_type"] == "confidence_score"
    assert data["model_name"] == "KoreaPeter/ms-eff-gcvit-deepfake-b0-ff-plus-plus"
    assert data["frames_sampled"] == 20
    assert data["faces_detected"] > 0
    assert "visual patterns" in data["message"]
    assert len(data["limitations"]) > 0
    assert "request_id" in data
    assert response.headers.get("x-request-id") == data["request_id"]


def test_deepfake_custom_request_id(client: TestClient, valid_mp4_bytes: bytes):
    """Test propagation of client-supplied X-Request-ID."""
    custom_id = "safemate-audit-req-9999"
    response = client.post(
        "/api/v1/deepfake/detect",
        files={"file": ("clip.mp4", valid_mp4_bytes, "video/mp4")},
        headers={"X-Request-ID": custom_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] == custom_id
    assert response.headers.get("x-request-id") == custom_id


def test_deepfake_missing_file(client: TestClient):
    """Test 400 rejection when no file is supplied in the request."""
    response = client.post("/api/v1/deepfake/detect")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "MISSING_FILE"


def test_deepfake_empty_file_rejected(client: TestClient):
    """Test 400 rejection when uploaded video file is 0 bytes."""
    response = client.post(
        "/api/v1/deepfake/detect",
        files={"file": ("empty.mp4", b"", "video/mp4")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "EMPTY_FILE"


def test_deepfake_unsupported_file_extension(client: TestClient, valid_mp4_bytes: bytes):
    """Test 415 rejection when file extension is not an allowed video format."""
    response = client.post(
        "/api/v1/deepfake/detect",
        files={"file": ("payload.exe", valid_mp4_bytes, "application/octet-stream")},
    )
    assert response.status_code == 415
    data = response.json()
    assert data["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_deepfake_corrupt_video(client: TestClient, corrupt_bytes: bytes):
    """Test 400 handling when video decoding fails."""
    response = client.post(
        "/api/v1/deepfake/detect",
        files={"file": ("broken.mp4", corrupt_bytes, "video/mp4")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_VIDEO"


def test_deepfake_oversized_file_rejected(client: TestClient, monkeypatch):
    """Test 413 rejection when file exceeds MAX_VIDEO_UPLOAD_MB."""
    monkeypatch.setattr(settings, "MAX_VIDEO_UPLOAD_MB", 1)  # 1 MB threshold for test
    oversized = b"\x00" * (1024 * 1024 + 100)
    response = client.post(
        "/api/v1/deepfake/detect",
        files={"file": ("huge.mp4", oversized, "video/mp4")},
    )
    assert response.status_code == 413
    data = response.json()
    assert data["error"]["code"] == "FILE_TOO_LARGE"


def test_deepfake_no_face_detected(valid_mp4_bytes: bytes):
    """Test graceful handling when no face is present in video frames."""
    app = create_app()
    fake_video = FakeVideoDeepfakeService(is_loaded=True, no_face=True)
    app.dependency_overrides[get_model_service] = lambda: FakeModelService(is_loaded=True)
    app.dependency_overrides[get_video_deepfake_service] = lambda: fake_video

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/deepfake/detect",
            files={"file": ("landscape.mp4", valid_mp4_bytes, "video/mp4")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "no_face_detected"
        assert data["prediction"] is None
        assert data["score"] is None
        assert data["faces_detected"] == 0
        assert "No human face was detected" in data["message"]


def test_deepfake_custom_frame_count(client: TestClient, valid_mp4_bytes: bytes):
    """Test query parameter num_frames bounding and sampling."""
    response = client.post(
        "/api/v1/deepfake/detect?num_frames=12",
        files={"file": ("test.mp4", valid_mp4_bytes, "video/mp4")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["frames_sampled"] == 12


def test_deepfake_model_not_ready_returns_503(valid_mp4_bytes: bytes):
    """Test 503 response when video deepfake model service is unavailable."""
    app = create_app()
    unready_service = FakeVideoDeepfakeService(is_loaded=False)
    app.dependency_overrides[get_model_service] = lambda: FakeModelService(is_loaded=True)
    app.dependency_overrides[get_video_deepfake_service] = lambda: unready_service

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/deepfake/detect",
            files={"file": ("test.mp4", valid_mp4_bytes, "video/mp4")},
        )
        assert response.status_code == 503
        data = response.json()
        assert data["error"]["code"] == "MODEL_NOT_READY"


def test_deepfake_inference_failure_returns_500(valid_mp4_bytes: bytes):
    """Test controlled 500 response when inference throws an exception without fabricated results."""
    app = create_app()
    failing_service = FakeVideoDeepfakeService(is_loaded=True, fail_inference=True)
    app.dependency_overrides[get_model_service] = lambda: FakeModelService(is_loaded=True)
    app.dependency_overrides[get_video_deepfake_service] = lambda: failing_service

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/deepfake/detect",
            files={"file": ("test.mp4", valid_mp4_bytes, "video/mp4")},
        )
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "INFERENCE_FAILURE"
        assert "inference" in data["error"]["message"].lower()


def test_deepfake_temporary_file_cleanup_on_success(valid_mp4_bytes: bytes):
    """Verify temporary video files are cleaned up after successful execution."""
    real_service = VideoDeepfakeService()
    # Mock model and detector to return synthetic face
    real_service.is_loaded = True
    real_service.model = lambda batch: [0.1]
    real_service.detector = None  # Will result in no_face_detected

    temp_dir = tempfile.gettempdir()
    initial_files = set(os.listdir(temp_dir))

    real_service.predict_video(valid_mp4_bytes, filename="test.mp4", num_frames=5)

    post_files = set(os.listdir(temp_dir))
    new_files = post_files - initial_files
    # Verify no persistent .mp4 temporary file remains
    assert not any(f.endswith(".mp4") for f in new_files)


def test_deepfake_temporary_file_cleanup_on_exception(valid_mp4_bytes: bytes):
    """Verify temporary files are purged even if an unhandled exception occurs."""
    real_service = VideoDeepfakeService()
    real_service.is_loaded = True
    real_service.model = None

    temp_dir = tempfile.gettempdir()
    initial_files = set(os.listdir(temp_dir))

    # Trigger exception inside frame sampling or processing
    try:
        real_service.predict_video(b"corrupt_video_data", filename="test.mp4")
    except Exception:
        pass

    post_files = set(os.listdir(temp_dir))
    new_files = post_files - initial_files
    assert not any(f.endswith(".mp4") for f in new_files)


def test_backward_compatibility_existing_endpoints(client: TestClient, valid_jpeg_bytes: bytes):
    """Verify that existing health, readiness, model-info, and image detection endpoints remain 100% operational."""
    # 1. Health liveness
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    # 2. Health readiness
    res = client.get("/api/v1/health/ready")
    assert res.status_code == 200
    assert res.json()["status"] == "ready"

    # 3. Model Info
    res = client.get("/api/v1/model-info")
    assert res.status_code == 200
    assert res.json()["model_id"] == "umm-maybe/AI-image-detector"

    # 4. Image detection (POST /api/v1/detect)
    res = client.post(
        "/api/v1/detect",
        files={"file": ("sample.jpg", valid_jpeg_bytes, "image/jpeg")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["prediction"]["label"] == "artificial"


def test_deepfake_ready_endpoint_loaded(client: TestClient):
    """Test GET /api/v1/deepfake/ready returns 200 when service is initialized."""
    res = client.get("/api/v1/deepfake/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["model_loaded"] is True
    assert data["detector_loaded"] is True
    assert data["model_id"] == "KoreaPeter/ms-eff-gcvit-deepfake-b0-ff-plus-plus"
    assert data["device"] == "cpu"


def test_deepfake_ready_endpoint_unready():
    """Test GET /api/v1/deepfake/ready returns 503 when service is unavailable."""
    app = create_app()
    unready = FakeVideoDeepfakeService(is_loaded=False)
    app.dependency_overrides[get_model_service] = lambda: FakeModelService(is_loaded=True)
    app.dependency_overrides[get_video_deepfake_service] = lambda: unready

    with TestClient(app) as test_client:
        res = test_client.get("/api/v1/deepfake/ready")
        assert res.status_code == 503
        data = res.json()
        assert data["status"] == "unavailable"
        assert data["model_loaded"] is False


def test_deepfake_model_info_endpoint(client: TestClient):
    """Test GET /api/v1/deepfake/model-info returns metadata and disclaimers."""
    res = client.get("/api/v1/deepfake/model-info")
    assert res.status_code == 200
    data = res.json()
    assert data["architecture"] == "MS-EffGCViT-B0"
    assert data["face_detector"] == "YOLOv8n-Face"
    assert data["task"] == "video-deepfake-screening"
    assert "potential_manipulation_detected" in data["labels"]
    assert len(data["limitations_notice"]) > 20


def test_deepfake_service_aggregate_predictions():
    """Test confidence, mean, and vote prediction aggregation methods."""
    import numpy as np

    # Empty array
    assert VideoDeepfakeService._aggregate_predictions(np.array([])) == 0.0

    # Mean mode
    preds = np.array([0.2, 0.4, 0.6, 0.8])
    assert round(VideoDeepfakeService._aggregate_predictions(preds, agg_mode="mean"), 2) == 0.50

    # Vote mode
    assert VideoDeepfakeService._aggregate_predictions(preds, agg_mode="vote") == 0.50

    # High fake confidence
    high_fakes = np.array([0.9, 0.95, 0.85, 0.92, 0.1, 0.2])
    score = VideoDeepfakeService._aggregate_predictions(high_fakes, agg_mode="conf")
    assert score > 0.85


def test_deepfake_service_normalize_face():
    """Test face normalization generates correctly shaped and typed ImageNet tensors."""
    import numpy as np
    import torch

    dummy_face = np.full((120, 120, 3), 128, dtype=np.uint8)
    tensor = VideoDeepfakeService._normalize_face(dummy_face, target_size=224)
    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == (3, 224, 224)
    assert tensor.dtype == torch.float32


def test_root_discovery_includes_deepfake_endpoints(client: TestClient):
    """Verify GET / exposes deepfake screening, readiness, and metadata endpoints."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "video_deepfake_screening" in data
    assert "video_deepfake_ready" in data
    assert "video_deepfake_model_info" in data

