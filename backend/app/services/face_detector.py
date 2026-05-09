"""
Face detection using MediaPipe (no OpenCV imported in application code).
Bounding-box rendering uses Pillow only.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional

import mediapipe as mp
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Initialise once at import time — MediaPipe models are loaded lazily.
_mp_face = mp.solutions.face_detection
_detector = _mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.5)

ROI_COLOR = "#00FF41"  # matrix green
ROI_WIDTH = 3
LABEL_PADDING = 4


@dataclass
class FaceROI:
    x: int
    y: int
    width: int
    height: int
    confidence: float


def detect_face(image: Image.Image) -> Optional[FaceROI]:
    """Return the ROI for the first (and only assumed) face, or None."""
    rgb = np.array(image.convert("RGB"), dtype=np.uint8)
    results = _detector.process(rgb)

    if not results.detections:
        return None

    detection = results.detections[0]
    bbox = detection.location_data.relative_bounding_box
    w, h = image.size

    x = max(0, int(bbox.xmin * w))
    y = max(0, int(bbox.ymin * h))
    bw = min(int(bbox.width * w), w - x)
    bh = min(int(bbox.height * h), h - y)
    confidence = float(detection.score[0])

    return FaceROI(x=x, y=y, width=bw, height=bh, confidence=confidence)


def draw_roi(image: Image.Image, roi: FaceROI) -> Image.Image:
    """
    Draw an axis-aligned minimal bounding box and confidence label onto the
    image using Pillow only (no OpenCV).
    """
    annotated = image.copy().convert("RGB")
    draw = ImageDraw.Draw(annotated)

    # Axis-aligned bounding rectangle
    draw.rectangle(
        [roi.x, roi.y, roi.x + roi.width, roi.y + roi.height],
        outline=ROI_COLOR,
        width=ROI_WIDTH,
    )

    # Confidence label above the box
    label = f"Face {roi.confidence:.0%}"
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except OSError:
        font = ImageFont.load_default()

    bbox_text = draw.textbbox((0, 0), label, font=font)
    text_w = bbox_text[2] - bbox_text[0]
    text_h = bbox_text[3] - bbox_text[1]

    label_x = roi.x
    label_y = max(0, roi.y - text_h - LABEL_PADDING * 2)

    draw.rectangle(
        [label_x, label_y, label_x + text_w + LABEL_PADDING * 2, label_y + text_h + LABEL_PADDING * 2],
        fill=ROI_COLOR,
    )
    draw.text((label_x + LABEL_PADDING, label_y + LABEL_PADDING), label, fill="#000000", font=font)

    return annotated


def image_to_jpeg_bytes(image: Image.Image, quality: int = 85) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def jpeg_bytes_to_image(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data))
