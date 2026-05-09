"""
In-memory pub/sub store for the latest processed frame.
MJPEG streaming subscribers wait on an asyncio.Condition.
"""
from __future__ import annotations

import asyncio
from typing import Optional


class FrameStore:
    def __init__(self) -> None:
        self._frame: Optional[bytes] = None
        self._condition = asyncio.Condition()

    async def publish(self, frame_jpeg: bytes) -> None:
        async with self._condition:
            self._frame = frame_jpeg
            self._condition.notify_all()

    async def wait_for_frame(self) -> bytes:
        """Block until a new frame is available, then return it."""
        async with self._condition:
            await self._condition.wait()
            return self._frame  # type: ignore[return-value]

    @property
    def latest(self) -> Optional[bytes]:
        return self._frame


# Module-level singleton shared across the application
frame_store = FrameStore()
