"""
WebSocket endpoint — bidirectional frame streaming.

Client → Server : JSON { "frame": "<base64-jpeg>" }
Server → Client : JSON { "frame": "<base64-jpeg>", "roi": <ROI|null>, "timestamp": "..." }
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.roi import ROIDetection
from app.services import face_detector as fd
from app.services.frame_store import frame_store

log = logging.getLogger(__name__)
router = APIRouter()

# Throttle DB writes: persist at most one ROI per N seconds per session
_DB_WRITE_INTERVAL = 0.25


@router.websocket("/stream")
async def ws_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    session_id = str(uuid.uuid4())
    last_db_write = 0.0
    log.info("WebSocket connected — session %s", session_id)

    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)

            if payload.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue

            frame_b64: str = payload["frame"]
            # Strip data-URL prefix if present
            if "," in frame_b64:
                frame_b64 = frame_b64.split(",", 1)[1]

            frame_bytes = base64.b64decode(frame_b64)
            image = fd.jpeg_bytes_to_image(frame_bytes)

            # Run face detection in a thread so the event loop stays free
            roi = await asyncio.get_running_loop().run_in_executor(
                None, fd.detect_face, image
            )

            if roi:
                annotated = await asyncio.get_running_loop().run_in_executor(
                    None, fd.draw_roi, image, roi
                )
                out_bytes = await asyncio.get_running_loop().run_in_executor(
                    None, fd.image_to_jpeg_bytes, annotated
                )

                # Throttled persistence
                now = asyncio.get_event_loop().time()
                if now - last_db_write >= _DB_WRITE_INTERVAL:
                    last_db_write = now
                    asyncio.create_task(
                        _persist_roi(roi, image.size, session_id)
                    )

                roi_data = {
                    "x": roi.x,
                    "y": roi.y,
                    "width": roi.width,
                    "height": roi.height,
                    "confidence": round(roi.confidence, 4),
                }
            else:
                out_bytes = frame_bytes
                roi_data = None

            await frame_store.publish(out_bytes)

            response = {
                "frame": "data:image/jpeg;base64," + base64.b64encode(out_bytes).decode(),
                "roi": roi_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": session_id,
            }
            await websocket.send_text(json.dumps(response))

    except WebSocketDisconnect:
        log.info("WebSocket disconnected — session %s", session_id)
    except Exception as exc:
        log.exception("WebSocket error in session %s: %s", session_id, exc)
        try:
            await websocket.send_text(json.dumps({"error": str(exc)}))
        except Exception:
            pass


async def _persist_roi(roi: fd.FaceROI, frame_size: tuple[int, int], session_id: str) -> None:
    try:
        async with AsyncSessionLocal() as db:
            record = ROIDetection(
                x=roi.x,
                y=roi.y,
                width=roi.width,
                height=roi.height,
                confidence=roi.confidence,
                frame_width=frame_size[0],
                frame_height=frame_size[1],
                session_id=session_id,
            )
            db.add(record)
            await db.commit()
    except Exception:
        log.exception("Failed to persist ROI for session %s", session_id)
