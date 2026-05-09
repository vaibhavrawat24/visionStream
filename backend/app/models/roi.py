from datetime import datetime, timezone
from sqlalchemy import Integer, Float, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ROIDetection(Base):
    __tablename__ = "roi_detections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Axis-aligned minimal bounding box (pixel coordinates)
    x: Mapped[int] = mapped_column(Integer, nullable=False)
    y: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    # Detection metadata
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    frame_width: Mapped[int] = mapped_column(Integer, nullable=False)
    frame_height: Mapped[int] = mapped_column(Integer, nullable=False)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
