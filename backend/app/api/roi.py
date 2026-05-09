"""
REST endpoints for querying stored ROI detection records.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.roi import ROIDetection
from app.schemas.roi import ROIListResponse, ROIResponse

router = APIRouter()


@router.get("", response_model=ROIListResponse)
async def list_rois(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    session_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return paginated ROI detection records, newest first."""
    query = select(ROIDetection)
    count_query = select(func.count()).select_from(ROIDetection)

    if session_id:
        query = query.where(ROIDetection.session_id == session_id)
        count_query = count_query.where(ROIDetection.session_id == session_id)

    total = (await db.execute(count_query)).scalar_one()
    rows = (
        await db.execute(query.order_by(ROIDetection.detected_at.desc()).offset(skip).limit(limit))
    ).scalars().all()

    return ROIListResponse(total=total, items=[ROIResponse.model_validate(r) for r in rows])


@router.get("/latest", response_model=ROIResponse)
async def latest_roi(db: AsyncSession = Depends(get_db)):
    """Return the most recently detected ROI."""
    row = (
        await db.execute(select(ROIDetection).order_by(ROIDetection.detected_at.desc()).limit(1))
    ).scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="No ROI detections recorded yet")

    return ROIResponse.model_validate(row)


@router.get("/{roi_id}", response_model=ROIResponse)
async def get_roi(roi_id: int, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(ROIDetection).where(ROIDetection.id == roi_id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="ROI not found")
    return ROIResponse.model_validate(row)
