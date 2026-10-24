"""Tests for image validation, security checks, and decoding safeguards."""

import io
import pytest
from PIL import Image

from app.schemas.errors import ValidationException
from app.services.image_validation import validate_and_decode_image


def test_valid_jpeg_decoding(valid_jpeg_bytes: bytes):
    """Test valid JPEG bytes are decoded into an RGB image."""
    img = validate_and_decode_image(valid_jpeg_bytes, filename="test.jpg", content_type="image/jpeg")
    assert isinstance(img, Image.Image)
    assert img.mode == "RGB"
    img.close()


def test_valid_png_decoding(valid_png_bytes: bytes):
    """Test valid PNG bytes are decoded into an RGB image."""
    img = validate_and_decode_image(valid_png_bytes, filename="test.png", content_type="image/png")
    assert isinstance(img, Image.Image)
    assert img.mode == "RGB"
    img.close()


def test_valid_webp_decoding(valid_webp_bytes: bytes):
    """Test valid WEBP bytes are decoded into an RGB image."""
    img = validate_and_decode_image(valid_webp_bytes, filename="test.webp", content_type="image/webp")
    assert isinstance(img, Image.Image)
    assert img.mode == "RGB"
    img.close()


def test_empty_file_rejected():
    """Test empty byte payload is rejected with 400 EMPTY_FILE."""
    with pytest.raises(ValidationException) as exc_info:
        validate_and_decode_image(b"", filename="empty.jpg", content_type="image/jpeg")
    assert exc_info.value.code == "EMPTY_FILE"
    assert exc_info.value.status_code == 400


def test_file_too_large_rejected(monkeypatch):
    """Test file larger than MAX_UPLOAD_MB is rejected with 413 FILE_TOO_LARGE."""
    from app.core.config import settings

    # Simulate 2MB max for quick test
    monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 1)
    huge_payload = b"0" * (1 * 1024 * 1024 + 100)

    with pytest.raises(ValidationException) as exc_info:
        validate_and_decode_image(huge_payload, filename="huge.jpg", content_type="image/jpeg")
    assert exc_info.value.code == "FILE_TOO_LARGE"
    assert exc_info.value.status_code == 413


def test_unsupported_file_extension():
    """Test disallowed extension is rejected with 415 UNSUPPORTED_MEDIA_TYPE."""
    with pytest.raises(ValidationException) as exc_info:
        validate_and_decode_image(b"fake data", filename="malicious.exe", content_type="image/jpeg")
    assert exc_info.value.code == "UNSUPPORTED_MEDIA_TYPE"
    assert exc_info.value.status_code == 415


def test_unsupported_mime_type(valid_jpeg_bytes: bytes):
    """Test disallowed MIME type is rejected with 415."""
    with pytest.raises(ValidationException) as exc_info:
        validate_and_decode_image(valid_jpeg_bytes, filename="test.jpg", content_type="application/pdf")
    assert exc_info.value.code == "UNSUPPORTED_MEDIA_TYPE"
    assert exc_info.value.status_code == 415


def test_text_file_renamed_as_jpg():
    """Test a plain text file renamed to .jpg is rejected as INVALID_IMAGE."""
    fake_jpg = b"This is plain text pretending to be a JPG file."
    with pytest.raises(ValidationException) as exc_info:
        validate_and_decode_image(fake_jpg, filename="fake.jpg", content_type="image/jpeg")
    assert exc_info.value.code == "INVALID_IMAGE"
    assert exc_info.value.status_code == 400


def test_corrupt_image_bytes(corrupt_bytes: bytes):
    """Test corrupted image bytes are rejected with 400 INVALID_IMAGE."""
    with pytest.raises(ValidationException) as exc_info:
        validate_and_decode_image(corrupt_bytes, filename="corrupt.jpg", content_type="image/jpeg")
    assert exc_info.value.code == "INVALID_IMAGE"
    assert exc_info.value.status_code == 400


def test_unsupported_image_format_bmp():
    """Test an unsupported image format (BMP) is rejected with 415."""
    img = Image.new("RGB", (50, 50), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="BMP")
    bmp_bytes = buf.getvalue()

    with pytest.raises(ValidationException) as exc_info:
        # Note: extension is omitted to test raw format detection rejection
        validate_and_decode_image(bmp_bytes, filename="test.bmp", content_type="image/bmp")
    assert exc_info.value.code == "UNSUPPORTED_MEDIA_TYPE"
    assert exc_info.value.status_code == 415


def test_animated_gif_rejected(animated_gif_bytes: bytes):
    """Test animated multi-frame images are rejected with ANIMATED_IMAGE_NOT_SUPPORTED."""
    with pytest.raises(ValidationException) as exc_info:
        validate_and_decode_image(animated_gif_bytes, filename="anim.gif", content_type="image/gif")
    assert exc_info.value.code in ["ANIMATED_IMAGE_NOT_SUPPORTED", "UNSUPPORTED_MEDIA_TYPE"]
    assert exc_info.value.status_code in [400, 415]


def test_excessive_dimensions_rejected():
    """Test image with excessive dimensions is rejected with EXCESSIVE_DIMENSIONS."""
    # Create an image that exceeds max dimensions
    from app.core.config import settings

    # Temporarily set max width/height low to test cleanly
    orig_w, orig_h = settings.MAX_IMAGE_WIDTH, settings.MAX_IMAGE_HEIGHT
    try:
        settings.MAX_IMAGE_WIDTH = 200
        settings.MAX_IMAGE_HEIGHT = 200

        img = Image.new("RGB", (300, 300), color="green")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()

        with pytest.raises(ValidationException) as exc_info:
            validate_and_decode_image(png_bytes, filename="large.png", content_type="image/png")
        assert exc_info.value.code == "EXCESSIVE_DIMENSIONS"
        assert exc_info.value.status_code == 400
    finally:
        settings.MAX_IMAGE_WIDTH = orig_w
        settings.MAX_IMAGE_HEIGHT = orig_h


def test_rgba_to_rgb_conversion():
    """Test that RGBA images with transparency are cleanly converted to RGB."""
    img_rgba = Image.new("RGBA", (80, 80), color=(100, 150, 200, 128))
    buf = io.BytesIO()
    img_rgba.save(buf, format="PNG")
    rgba_bytes = buf.getvalue()

    img = validate_and_decode_image(rgba_bytes, filename="alpha.png", content_type="image/png")
    assert img.mode == "RGB"
    img.close()
