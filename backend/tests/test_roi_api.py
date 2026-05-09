import pytest
from datetime import datetime, timezone
from app.models.roi import ROIDetection


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_roi_empty(client):
    r = await client.get("/api/roi")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_latest_roi_404_when_empty(client):
    r = await client.get("/api/roi/latest")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_and_get_roi(client, db_session):
    record = ROIDetection(
        x=10, y=20, width=100, height=120,
        confidence=0.95,
        frame_width=640, frame_height=480,
        session_id="test-session",
        detected_at=datetime.now(timezone.utc),
    )
    db_session.add(record)
    await db_session.commit()
    await db_session.refresh(record)

    r = await client.get("/api/roi")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1

    r2 = await client.get(f"/api/roi/{record.id}")
    assert r2.status_code == 200
    item = r2.json()
    assert item["x"] == 10
    assert item["confidence"] == 0.95

    r3 = await client.get("/api/roi/latest")
    assert r3.status_code == 200


@pytest.mark.asyncio
async def test_list_roi_pagination(client, db_session):
    r = await client.get("/api/roi?skip=0&limit=1")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_get_roi_not_found(client):
    r = await client.get("/api/roi/999999")
    assert r.status_code == 404
