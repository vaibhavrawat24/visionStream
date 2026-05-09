from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ROIBase(BaseModel):
    x: int
    y: int
    width: int
    height: int
    confidence: float
    frame_width: int
    frame_height: int
    session_id: str


class ROICreate(ROIBase):
    pass


class ROIResponse(ROIBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    detected_at: datetime


class ROIListResponse(BaseModel):
    total: int
    items: list[ROIResponse]
