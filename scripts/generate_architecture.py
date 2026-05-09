"""
Generates the system architecture diagram as architecture.png.
Run from the repo root: python scripts/generate_architecture.py
Requires: pip install Pillow
"""
from __future__ import annotations
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1400, 860
BG = "#0d1117"
BORDER = "#30363d"
ACCENT = "#00ff41"
BLUE = "#58a6ff"
ORANGE = "#f0883e"
PURPLE = "#bc8cff"
TEXT = "#e6edf3"
DIM = "#8b949e"
RED = "#f85149"

def load_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def rect(draw: ImageDraw.ImageDraw, box, fill=None, outline=BORDER, width=2, radius=12):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(draw: ImageDraw.ImageDraw, x1, y1, x2, y2, color=DIM, label: str = "", font=None):
    draw.line([(x1, y1), (x2, y2)], fill=color, width=2)
    # arrowhead
    dx, dy = x2 - x1, y2 - y1
    length = (dx**2 + dy**2) ** 0.5
    if length == 0:
        return
    ux, uy = dx / length, dy / length
    size = 10
    p1 = (x2 - size * ux + size * 0.4 * uy, y2 - size * uy - size * 0.4 * ux)
    p2 = (x2 - size * ux - size * 0.4 * uy, y2 - size * uy + size * 0.4 * ux)
    draw.polygon([(x2, y2), p1, p2], fill=color)
    if label and font:
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        draw.text((mx + 4, my - 14), label, fill=color, font=font)


def box_center(box):
    return ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2)


img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

title_font  = load_font(24, bold=True)
label_font  = load_font(15, bold=True)
small_font  = load_font(12)
tag_font    = load_font(11)

# Title
draw.text((W // 2, 32), "VisionStream — System Architecture", fill=TEXT, font=title_font, anchor="mm")
draw.text((W // 2, 58), "Real-Time Face Detection & Video Streaming", fill=DIM, font=small_font, anchor="mm")

# ── Zones ──────────────────────────────────────────────────────────────────
# [Browser] ── Nginx ── [FastAPI] ── [PostgreSQL]
#                              └── [MediaPipe + Pillow]

# Docker boundary
rect(draw, [40, 90, W - 40, H - 40], fill="#111823", outline="#30363d", width=1, radius=16)
draw.text((60, 102), "Docker Compose", fill=DIM, font=tag_font)

# ── Component boxes ─────────────────────────────────────────────────────────

# Browser / Client
browser_box = [70, 160, 310, 480]
rect(draw, browser_box, fill="#161b22", outline=BLUE, width=2)
draw.text((box_center(browser_box)[0], 183), "Browser", fill=BLUE, font=label_font, anchor="mm")
draw.text((box_center(browser_box)[0], 205), "(React + Vite)", fill=DIM, font=small_font, anchor="mm")
for i, line in enumerate([
    "VideoFeed.jsx",
    "  getUserMedia()",
    "  Canvas capture",
    "ROIPanel.jsx",
    "  ROI history table",
    "StatusBar.jsx",
]):
    draw.text((90, 230 + i * 22), line, fill=TEXT if not line.startswith(" ") else DIM, font=small_font)
draw.text((90, 445), "Port: browser", fill=DIM, font=tag_font)

# Nginx
nginx_box = [390, 240, 570, 400]
rect(draw, nginx_box, fill="#161b22", outline=ORANGE, width=2)
draw.text((box_center(nginx_box)[0], 263), "Nginx", fill=ORANGE, font=label_font, anchor="mm")
draw.text((box_center(nginx_box)[0], 284), "Reverse Proxy", fill=DIM, font=small_font, anchor="mm")
for i, line in enumerate(["/ → Frontend", "/api/* → Backend", "/ws/* → Backend", "/stream/* → Backend"]):
    draw.text((405, 308 + i * 18), line, fill=TEXT, font=tag_font)
draw.text((405, 385), "Port: 80", fill=DIM, font=tag_font)

# FastAPI Backend
backend_box = [640, 130, 940, 610]
rect(draw, backend_box, fill="#161b22", outline=ACCENT, width=2)
draw.text((box_center(backend_box)[0], 155), "FastAPI Backend", fill=ACCENT, font=label_font, anchor="mm")
draw.text((box_center(backend_box)[0], 177), "Port: 8000", fill=DIM, font=small_font, anchor="mm")

# Endpoint sub-boxes
ep_boxes = [
    ([660, 200, 920, 260], PURPLE, "WS /ws/stream", "WebSocket frame ingestion"),
    ([660, 275, 920, 335], BLUE,   "GET /stream/feed", "MJPEG multipart stream"),
    ([660, 350, 920, 410], ORANGE, "GET /api/roi", "ROI records (paginated)"),
    ([660, 425, 920, 485], ORANGE, "GET /api/roi/latest", "Most recent detection"),
    ([660, 500, 920, 560], RED,    "GET /health", "Liveness probe"),
]
for box, color, title, sub in ep_boxes:
    rect(draw, box, fill="#0d1117", outline=color, width=1, radius=6)
    draw.text((box[0] + 10, box[1] + 10), title, fill=color, font=small_font)
    draw.text((box[0] + 10, box[1] + 28), sub, fill=DIM, font=tag_font)

# Services
svc_box = [660, 580, 920, 630]
rect(draw, svc_box, fill="#0d1117", outline=DIM, width=1, radius=6)
draw.text((box_center(svc_box)[0], box_center(svc_box)[1]), "face_detector · frame_store · SQLAlchemy ORM", fill=DIM, font=tag_font, anchor="mm")

# MediaPipe + Pillow
ml_box = [970, 200, 1200, 400]
rect(draw, ml_box, fill="#161b22", outline=PURPLE, width=2)
draw.text((box_center(ml_box)[0], 223), "Inference Layer", fill=PURPLE, font=label_font, anchor="mm")
for i, (name, detail) in enumerate([
    ("MediaPipe", "Face detection"),
    ("", "model_selection=0"),
    ("", "confidence ≥ 0.5"),
    ("Pillow", "ROI bounding box"),
    ("", "draw.rectangle()"),
    ("", "ImageFont label"),
    ("NumPy", "Frame array bridge"),
]):
    color = TEXT if name else DIM
    draw.text((990, 250 + i * 20), (name or "  ") + ("  " + detail if detail else ""), fill=color if name else DIM, font=small_font)
draw.text((990, 385), "No OpenCV (cv2) in app code", fill=ACCENT, font=tag_font)

# PostgreSQL
pg_box = [970, 450, 1200, 620]
rect(draw, pg_box, fill="#161b22", outline=BLUE, width=2)
draw.text((box_center(pg_box)[0], 473), "PostgreSQL 16", fill=BLUE, font=label_font, anchor="mm")
draw.text((box_center(pg_box)[0], 495), "Port: 5432", fill=DIM, font=small_font, anchor="mm")
for i, line in enumerate([
    "Table: roi_detections",
    "  id         PK",
    "  x, y       INT",
    "  width, height INT",
    "  confidence  FLOAT",
    "  session_id  VARCHAR",
    "  detected_at TIMESTAMPTZ",
]):
    draw.text((990, 518 + i * 16), line, fill=TEXT if not line.startswith(" ") else DIM, font=tag_font)
draw.text((990, 606), "Alembic migrations", fill=DIM, font=tag_font)

# Alembic
alembic_box = [1240, 450, 1350, 520]
rect(draw, alembic_box, fill="#161b22", outline=DIM, width=1, radius=6)
draw.text((box_center(alembic_box)[0], box_center(alembic_box)[1] - 8), "Alembic", fill=DIM, font=tag_font, anchor="mm")
draw.text((box_center(alembic_box)[0], box_center(alembic_box)[1] + 8), "migrations", fill=DIM, font=tag_font, anchor="mm")

# ── Arrows ──────────────────────────────────────────────────────────────────
lf = tag_font
# Browser → Nginx (WebSocket)
arrow(draw, browser_box[2], 300, nginx_box[0], 310, PURPLE, "WS frames\n(base64 JPEG)", lf)
# Browser → Nginx (HTTP)
arrow(draw, browser_box[2], 360, nginx_box[0], 360, BLUE, "HTTP /api/roi", lf)

# Nginx → Backend (WebSocket)
arrow(draw, nginx_box[2], 310, backend_box[0], 230, PURPLE, "", lf)
# Nginx → Backend (HTTP)
arrow(draw, nginx_box[2], 360, backend_box[0], 380, BLUE, "", lf)

# Backend → Nginx → Browser (annotated frames back)
arrow(draw, backend_box[0], 290, nginx_box[2], 290, ACCENT, "annotated JPEG", lf)

# Backend ↔ ML
arrow(draw, backend_box[2], 300, ml_box[0], 300, PURPLE, "PIL Image", lf)
arrow(draw, ml_box[0], 340, backend_box[2], 340, ACCENT, "FaceROI", lf)

# Backend → DB
arrow(draw, backend_box[2], 500, pg_box[0], 530, BLUE, "async INSERT", lf)
arrow(draw, pg_box[0], 560, backend_box[2], 540, ORANGE, "SELECT rows", lf)

# Alembic → DB
arrow(draw, alembic_box[0], 485, pg_box[2], 500, DIM, "", lf)

# ── Legend ────────────────────────────────────────────────────────────────
legend_box = [70, H - 120, 550, H - 50]
rect(draw, legend_box, fill="#161b22", outline=BORDER, width=1, radius=8)
draw.text((90, H - 110), "Legend:", fill=DIM, font=tag_font)
legend_items = [
    (PURPLE, "WebSocket / ML"),
    (BLUE,   "HTTP / DB read"),
    (ACCENT, "Processed frames / DB write"),
    (ORANGE, "REST response"),
    (DIM,    "Internal tooling"),
]
for i, (color, label) in enumerate(legend_items):
    x = 90 + i * 92
    draw.rectangle([x, H - 88, x + 14, H - 74], fill=color)
    draw.text((x + 18, H - 90), label, fill=DIM, font=tag_font)

# Save
out = os.path.join(os.path.dirname(__file__), "..", "architecture.png")
img.save(out, format="PNG")
print(f"Saved → {os.path.abspath(out)}")
