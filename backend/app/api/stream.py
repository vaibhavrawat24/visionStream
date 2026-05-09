"""
MJPEG streaming endpoint — serves the latest processed frame as a live feed.
Allows <img src="/stream/feed"> to display the annotated video in real time.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter
from fastapi.responses import Response, StreamingResponse

from app.services.frame_store import frame_store

log = logging.getLogger(__name__)
router = APIRouter()

_BOUNDARY = "visionframe"
_NO_FEED_JPEG: bytes | None = None  # lazy-loaded placeholder


def _make_placeholder() -> bytes:
    """Generate a small grey JPEG as a 'no feed' placeholder."""
    from PIL import Image, ImageDraw
    import io

    img = Image.new("RGB", (640, 480), color="#1a1a2e")
    draw = ImageDraw.Draw(img)
    draw.text((220, 230), "Waiting for stream…", fill="#00FF41")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75)
    return buf.getvalue()


async def _mjpeg_generator():
    global _NO_FEED_JPEG
    if _NO_FEED_JPEG is None:
        _NO_FEED_JPEG = _make_placeholder()

    while True:
        try:
            frame = await asyncio.wait_for(frame_store.wait_for_frame(), timeout=2.0)
        except asyncio.TimeoutError:
            frame = _NO_FEED_JPEG

        yield (
            f"--{_BOUNDARY}\r\n"
            f"Content-Type: image/jpeg\r\n"
            f"Content-Length: {len(frame)}\r\n\r\n"
        ).encode() + frame + b"\r\n"


@router.get("/feed")
async def mjpeg_feed():
    """Serve a live MJPEG stream of the annotated video feed."""
    return StreamingResponse(
        _mjpeg_generator(),
        media_type=f"multipart/x-mixed-replace; boundary={_BOUNDARY}",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/snapshot")
async def snapshot():
    """Return the latest processed frame as a single JPEG."""
    frame = frame_store.latest
    if frame is None:
        return Response(status_code=204)
    return Response(content=frame, media_type="image/jpeg")
