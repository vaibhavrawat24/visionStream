"""
Unit tests for the face detector service (no OpenCV used).
These tests use synthetic images so they run without a webcam.
"""
import io
import pytest
from PIL import Image

from app.services.face_detector import (
    FaceROI,
    draw_roi,
    image_to_jpeg_bytes,
    jpeg_bytes_to_image,
)


def _solid_image(w=320, h=240, color="grey") -> Image.Image:
    return Image.new("RGB", (w, h), color=color)


def test_draw_roi_returns_same_size():
    img = _solid_image()
    roi = FaceROI(x=10, y=10, width=80, height=100, confidence=0.9)
    result = draw_roi(img, roi)
    assert result.size == img.size


def test_draw_roi_does_not_mutate_original():
    img = _solid_image(color="blue")
    roi = FaceROI(x=0, y=0, width=50, height=50, confidence=0.8)
    _ = draw_roi(img, roi)
    # Original pixel should still be blue
    assert img.getpixel((25, 25)) == (0, 0, 255)


def test_draw_roi_clamps_to_image_bounds():
    img = _solid_image(320, 240)
    # ROI larger than image — should not raise
    roi = FaceROI(x=0, y=0, width=640, height=480, confidence=0.99)
    result = draw_roi(img, roi)
    assert result.size == (320, 240)


def test_jpeg_roundtrip():
    img = _solid_image(color="red")
    jpeg = image_to_jpeg_bytes(img)
    assert isinstance(jpeg, bytes)
    assert len(jpeg) > 0

    restored = jpeg_bytes_to_image(jpeg)
    assert restored.size == img.size
    assert restored.mode == "RGB"


def test_jpeg_bytes_to_image_valid():
    img = _solid_image()
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    result = jpeg_bytes_to_image(buf.getvalue())
    assert result.size == img.size
