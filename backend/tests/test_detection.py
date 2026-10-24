"""Tests for POST /api/v1/detect endpoint, error shapes, CORS, and privacy protections."""

import os
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from tests.conftest import FakeModelService
from app.services.model_service import get_model_service


def test_detect_success(client: TestClient, valid_jpeg_bytes: bytes):
    """Test successful detection with valid JPEG image."""
    files = {"file": ("sample.jpg", valid_jpeg_bytes, "image/jpeg")}
    response = client.post("/api/v1/detect", files=files)

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["model_id"] == "umm-maybe/AI-image-detector"
    assert "prediction" in data
    assert data["prediction"]["label"] == "artificial"
    assert isinstance(data["prediction"]["score"], float)

    # Validate all class scores are returned
    scores = data["prediction"]["scores"]
    assert len(scores) == 2
    labels = {s["label"] for s in scores}
    assert labels == {"artificial", "human"}

    # Validate interpretation and limitations
    interpretation = data["interpretation"]
    assert interpretation["category"] == "ai_image_screening"
    assert interpretation["is_definitive"] is False
    assert len(interpretation["limitations"]) >= 2
    assert "not proof" in interpretation["limitations"][0].lower()

    # Validate request_id presence
    assert "request_id" in data
    assert data["request_id"].startswith("req_")
    assert response.headers.get("X-Request-ID") == data["request_id"]

    # Privacy verification: ensure response doesn't leak image data
    resp_text = response.text
    assert "data:image" not in resp_text
    assert "base64" not in resp_text.lower()


def test_custom_request_id_header(client: TestClient, valid_png_bytes: bytes):
    """Test custom X-Request-ID header is propagated into the response."""
    custom_rid = "custom-test-req-999"
    files = {"file": ("test.png", valid_png_bytes, "image/png")}
    response = client.post("/api/v1/detect", files=files, headers={"X-Request-ID": custom_rid})

    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] == custom_rid
    assert response.headers.get("X-Request-ID") == custom_rid


def test_missing_file_handling(client: TestClient):
    """Test request without a file payload returns structured 400 or 422 error."""
    response = client.post("/api/v1/detect", data={})
    assert response.status_code in [400, 422]
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert "code" in data["error"]
    assert "request_id" in data


def test_empty_file_rejected(client: TestClient):
    """Test empty file upload returns 400 EMPTY_FILE."""
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    response = client.post("/api/v1/detect", files=files)

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "EMPTY_FILE"
    assert "request_id" in data


def test_text_file_renamed_as_jpg_rejected(client: TestClient):
    """Test text disguised as a JPG is rejected with 400 INVALID_IMAGE."""
    files = {"file": ("fake.jpg", b"hello world this is text", "image/jpeg")}
    response = client.post("/api/v1/detect", files=files)

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_IMAGE"
    assert "request_id" in data


def test_corrupt_image_rejected(client: TestClient, corrupt_bytes: bytes):
    """Test corrupt image bytes return 400 INVALID_IMAGE."""
    files = {"file": ("bad.jpg", corrupt_bytes, "image/jpeg")}
    response = client.post("/api/v1/detect", files=files)

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_IMAGE"
    assert "request_id" in data


def test_unsupported_format_rejected(client: TestClient):
    """Test unsupported format (e.g. BMP) returns 415."""
    import io
    img = Image.new("RGB", (30, 30), color="yellow")
    buf = io.BytesIO()
    img.save(buf, format="BMP")

    files = {"file": ("test.bmp", buf.getvalue(), "image/bmp")}
    response = client.post("/api/v1/detect", files=files)

    assert response.status_code == 415
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_oversized_file_rejected(client: TestClient, monkeypatch):
    """Test upload exceeding MAX_UPLOAD_MB returns 413 FILE_TOO_LARGE."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 1)

    big_bytes = b"0" * (1 * 1024 * 1024 + 500)
    files = {"file": ("big.jpg", big_bytes, "image/jpeg")}
    response = client.post("/api/v1/detect", files=files)

    assert response.status_code == 413
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "FILE_TOO_LARGE"


def test_model_not_ready_returns_503(app_with_mock, valid_jpeg_bytes: bytes):
    """Test detection returns 503 when model service is unready."""
    unready_service = FakeModelService(is_loaded=False)
    app_with_mock.dependency_overrides[get_model_service] = lambda: unready_service

    with TestClient(app_with_mock) as client:
        files = {"file": ("test.jpg", valid_jpeg_bytes, "image/jpeg")}
        response = client.post("/api/v1/detect", files=files)

        assert response.status_code == 503
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "MODEL_NOT_READY"
        assert "request_id" in data


def test_inference_failure_returns_500(app_with_mock, valid_jpeg_bytes: bytes):
    """Test that unexpected inference error returns safe 500 INFERENCE_FAILURE."""
    failing_service = FakeModelService(is_loaded=True, fail_inference=True)
    app_with_mock.dependency_overrides[get_model_service] = lambda: failing_service

    with TestClient(app_with_mock) as client:
        files = {"file": ("test.jpg", valid_jpeg_bytes, "image/jpeg")}
        response = client.post("/api/v1/detect", files=files)

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INFERENCE_FAILURE"
        # Verify no traceback is leaked in client response
        assert "Traceback" not in response.text
        assert "FakeModelService" not in response.text


def test_no_disk_persistence_of_images(client: TestClient, valid_png_bytes: bytes):
    """Verify that uploaded images are processed entirely in memory and not persisted to disk."""
    # Record existing files before upload
    workspace_files_before = set(os.listdir("."))

    files = {"file": ("persist_test.png", valid_png_bytes, "image/png")}
    response = client.post("/api/v1/detect", files=files)
    assert response.status_code == 200

    # Ensure no new image files were created on disk
    workspace_files_after = set(os.listdir("."))
    new_files = workspace_files_after - workspace_files_before

    for f in new_files:
        assert not f.endswith((".png", ".jpg", ".jpeg", ".webp")), f"Unexpected file written: {f}"


def test_cors_preflight(client: TestClient):
    """Test CORS preflight response matches configured origins."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    response = client.options("/api/v1/detect", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "POST" in response.headers.get("access-control-allow-methods", "")
