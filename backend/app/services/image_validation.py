"""Input validation service for uploaded images with security and privacy safeguards."""

import io
import logging
import os
import warnings
from typing import Optional
from PIL import Image, ImageOps

from app.core.config import settings
from app.schemas.errors import ValidationException

logger = logging.getLogger(__name__)

# Configure Pillow decompression bomb protection
Image.MAX_IMAGE_PIXELS = settings.MAX_IMAGE_PIXELS


def validate_and_decode_image(
    file_bytes: bytes,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
) -> Image.Image:
    """Safely validate, decode, and normalize an uploaded image completely in memory.

    Args:
        file_bytes: Raw bytes received from the multipart upload.
        filename: Optional client-provided filename.
        content_type: Optional client-provided MIME content type.

    Returns:
        A validated, non-animated, RGB PIL Image object.

    Raises:
        ValidationException: On any validation, security, or decoding error.
    """
    # 1. Check for empty file
    if not file_bytes or len(file_bytes) == 0:
        raise ValidationException(
            message="Uploaded file is empty. Please select a valid image.",
            code="EMPTY_FILE",
            status_code=400,
        )

    # 2. Enforce upload size limit
    if len(file_bytes) > settings.max_upload_bytes:
        raise ValidationException(
            message=f"File size ({len(file_bytes) / (1024 * 1024):.1f}MB) exceeds the maximum allowed upload limit of {settings.MAX_UPLOAD_MB}MB.",
            code="FILE_TOO_LARGE",
            status_code=413,
        )

    # 3. Check filename extension if provided
    if filename:
        _, ext = os.path.splitext(filename.lower())
        allowed_exts = {".jpg", ".jpeg", ".png", ".webp"}
        if ext and ext not in allowed_exts:
            raise ValidationException(
                message=f"File extension '{ext}' is not supported. Allowed extensions: {', '.join(sorted(allowed_exts))}.",
                code="UNSUPPORTED_MEDIA_TYPE",
                status_code=415,
            )

    # 4. Check client content_type if provided (do not rely on it alone)
    if content_type:
        clean_content_type = content_type.split(";")[0].strip().lower()
        if clean_content_type not in settings.ALLOWED_MIME_TYPES:
            raise ValidationException(
                message=f"MIME type '{content_type}' is not supported. Allowed types: {', '.join(settings.ALLOWED_MIME_TYPES)}.",
                code="UNSUPPORTED_MEDIA_TYPE",
                status_code=415,
            )

    # 5. Decode with Pillow inside a protected context
    byte_stream = io.BytesIO(file_bytes)
    try:
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("error", Image.DecompressionBombWarning)

            try:
                # First pass: open and verify image integrity and header
                with Image.open(byte_stream) as raw_img:
                    raw_img.verify()
            except (Image.DecompressionBombError, Image.DecompressionBombWarning):
                raise ValidationException(
                    message="Image dimensions exceed safe processing limits (potential decompression bomb).",
                    code="EXCESSIVE_DIMENSIONS",
                    status_code=400,
                )
            except Exception as e:
                logger.debug(f"Image verification failed: {type(e).__name__}")
                raise ValidationException(
                    message="The uploaded file is corrupt or not a recognized image format.",
                    code="INVALID_IMAGE",
                    status_code=400,
                )

        # Reset stream for decoding after verify()
        byte_stream.seek(0)
        img = Image.open(byte_stream)

        # Check decoded format against whitelist
        if img.format not in settings.ALLOWED_IMAGE_FORMATS:
            img.close()
            raise ValidationException(
                message=f"Image format '{img.format}' is not supported. Allowed formats: {', '.join(settings.ALLOWED_IMAGE_FORMATS)}.",
                code="UNSUPPORTED_MEDIA_TYPE",
                status_code=415,
            )

        # 6. Reject animated or multi-frame images
        is_animated = getattr(img, "is_animated", False)
        n_frames = getattr(img, "n_frames", 1)
        if is_animated or n_frames > 1:
            img.close()
            raise ValidationException(
                message="Animated or multi-frame images are not supported for image screening. Please upload a static image.",
                code="ANIMATED_IMAGE_NOT_SUPPORTED",
                status_code=400,
            )

        # 7. Check image dimensions and pixel count
        width, height = img.size
        pixel_count = width * height

        if (
            width > settings.MAX_IMAGE_WIDTH
            or height > settings.MAX_IMAGE_HEIGHT
            or pixel_count > settings.MAX_IMAGE_PIXELS
        ):
            img.close()
            raise ValidationException(
                message=(
                    f"Image dimensions ({width}x{height}) exceed maximum allowed limits "
                    f"({settings.MAX_IMAGE_WIDTH}x{settings.MAX_IMAGE_HEIGHT} or {settings.MAX_IMAGE_PIXELS} total pixels)."
                ),
                code="EXCESSIVE_DIMENSIONS",
                status_code=400,
            )

        # 8. Load image data into memory and normalize to RGB
        # Handle EXIF orientation if present (stripping other EXIF to safeguard privacy)
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Convert to RGB mode
        if img.mode != "RGB":
            converted_img = img.convert("RGB")
            img.close()
            img = converted_img
        else:
            # Load pixels into memory so byte_stream can be released
            img.load()

        return img

    except ValidationException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected image decoding error: {type(exc).__name__}")
        raise ValidationException(
            message="Failed to process image data safely.",
            code="INVALID_IMAGE",
            status_code=400,
        )
    finally:
        byte_stream.close()
