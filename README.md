# VisionStream

Real-time face detection video streaming system.  
Webcam frames are processed server-side (MediaPipe + Pillow — no OpenCV in application code), ROI bounding boxes are persisted in PostgreSQL, and the annotated feed is returned to the browser over WebSocket.

---

## Architecture

```
Browser (React)
  │  WebSocket /ws/stream  (base64 JPEG frames → annotated JPEG back)
  │  HTTP GET /stream/feed  (MJPEG alternative consumer)
  │  HTTP GET /api/roi      (ROI history)
  ▼
Nginx :80  (reverse proxy)
  ├─ /ws/*      → FastAPI :8000  (WebSocket upgrade)
  ├─ /stream/*  → FastAPI :8000  (MJPEG, no buffering)
  ├─ /api/*     → FastAPI :8000  (REST)
  └─ /*         → React   :3000

FastAPI
  ├─ WS /ws/stream         ← frame in → detect → draw → frame out
  ├─ GET /stream/feed       MJPEG multipart stream
  ├─ GET /api/roi           paginated ROI records
  ├─ GET /api/roi/latest    most recent detection
  └─ GET /health

Inference (no cv2 imported in app code)
  MediaPipe FaceDetection → FaceROI(x, y, width, height, confidence)
  Pillow ImageDraw.rectangle() → annotated JPEG

PostgreSQL :5432
  table: roi_detections
  (id, x, y, width, height, confidence, frame_width, frame_height, session_id, detected_at)
```

See `architecture.png` for the full diagram.

---

## Project Structure

```
visionStream/
├── backend/
│   ├── app/
│   │   ├── api/          # websocket.py · stream.py · roi.py
│   │   ├── core/         # config.py · database.py
│   │   ├── models/       # roi.py (SQLAlchemy)
│   │   ├── schemas/      # roi.py (Pydantic)
│   │   ├── services/     # face_detector.py · frame_store.py
│   │   └── main.py
│   ├── alembic/          # DB migrations
│   ├── tests/            # pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # VideoFeed · ROIPanel · StatusBar
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile
│   └── package.json
├── nginx/nginx.conf
├── docker-compose.yml
├── architecture.png
└── scripts/generate_architecture.py
```

---

## Quick Start (Docker — 5 minutes)

**Prerequisites:** Docker Desktop installed and running, a browser with camera access.

### macOS

If `docker` command is not found after installing Docker Desktop:

```bash
export PATH="$PATH:/Applications/Docker.app/Contents/Resources/bin"
# Make it permanent
echo 'export PATH="$PATH:/Applications/Docker.app/Contents/Resources/bin"' >> ~/.zshrc
source ~/.zshrc
```

```bash
git clone <repo-url> visionStream
cd visionStream

# First run (~5-10 min — downloads MediaPipe and Node packages)
docker compose up --build

# Subsequent runs (seconds)
docker compose up
```

Open **http://localhost**, click **Start Stream**, allow camera access.

```bash
# Stop
docker compose down
```

---

### Windows

1. Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) — enable WSL 2 backend when prompted
2. Open **PowerShell** or **Command Prompt** (Docker Desktop adds `docker` to PATH automatically)

```powershell
git clone <repo-url> visionStream
cd visionStream

# First run
docker compose up --build

# Subsequent runs
docker compose up
```

Open **http://localhost** in your browser, click **Start Stream**, allow camera access.

```powershell
# Stop
docker compose down
```

> **Windows note:** If you get a WSL 2 error, open Docker Desktop → Settings → General → enable "Use the WSL 2 based engine" and restart Docker Desktop.

---

### Linux

```bash
# Install Docker Engine + Compose plugin
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin

# Allow running docker without sudo (re-login after this)
sudo usermod -aG docker $USER

git clone <repo-url> visionStream
cd visionStream

docker compose up --build
```

Open **http://localhost**, click **Start Stream**, allow camera access.

```bash
docker compose down
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `WS` | `/ws/stream` | Bidirectional frame streaming |
| `GET` | `/stream/feed` | MJPEG multipart live feed |
| `GET` | `/stream/snapshot` | Latest processed frame (JPEG) |
| `GET` | `/api/roi` | List ROI records (`?skip=0&limit=50&session_id=…`) |
| `GET` | `/api/roi/latest` | Most recent detection |
| `GET` | `/api/roi/{id}` | Single record |
| `GET` | `/health` | Liveness probe |

### WebSocket protocol

**Client → Server**
```json
{ "frame": "data:image/jpeg;base64,<...>" }
```

**Server → Client**
```json
{
  "frame": "data:image/jpeg;base64,<annotated>",
  "roi": { "x": 120, "y": 45, "width": 180, "height": 200, "confidence": 0.97 },
  "timestamp": "2024-01-01T12:00:00.000Z",
  "session_id": "uuid"
}
```
`roi` is `null` when no face is detected.

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

---

## Generating the Architecture Diagram

```bash
pip install Pillow
python scripts/generate_architecture.py
# → architecture.png
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite |
| Backend | Python 3.11, FastAPI, Uvicorn |
| Face detection | MediaPipe (no OpenCV in app code) |
| ROI rendering | Pillow (`ImageDraw.rectangle`) |
| Database | PostgreSQL 16, SQLAlchemy 2 (async), Alembic |
| Streaming | WebSocket (bidirectional), MJPEG (output) |
| Proxy | Nginx |
| Container | Docker, Docker Compose |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `docker: command not found` | `export PATH="$PATH:/Applications/Docker.app/Contents/Resources/bin"` |
| Port 80 already in use | Change `"80:80"` → `"8080:80"` in `docker-compose.yml`, visit `http://localhost:8080` |
| Camera not working | Browser requires `localhost` or HTTPS for camera — don't use IP address |
| No face detected | Ensure good lighting and face the camera directly |
| Backend crash on startup | Run `docker compose logs backend` to see the error |

---

## Design Decisions

- **MediaPipe over OpenCV** — satisfies the no-cv2 constraint; pip-installable, no compilation needed.
- **WebSocket for frames** — bidirectional so the server can push annotated frames back to the same client instantly.
- **MJPEG `/stream/feed`** — secondary consumer path that lets any HTTP client (e.g. `<img>` tag) display the stream without JavaScript.
- **Throttled DB writes** — ROI is persisted at most 4×/sec per session to avoid write pressure from 10+ fps detection.
- **asyncio.Condition for MJPEG** — multiple MJPEG subscribers share a single condition variable; no polling.
- **Alembic** — versioned schema migrations so the database can evolve without destructive resets.
