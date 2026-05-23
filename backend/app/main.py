from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import roi, stream, websocket
from app.core.config import settings
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if they don't exist (Alembic handles migrations in prod)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="VisionStream API",
    description="Real-time face detection video streaming backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(websocket.router, prefix="/ws", tags=["stream-ws"])
app.include_router(stream.router, prefix="/stream", tags=["stream-mjpeg"])
app.include_router(roi.router, prefix="/api/roi", tags=["roi"])


@app.get("/health", tags=["ops"])
async def health():
    return {"status": "ok", "service": "visionstream-backend"}
