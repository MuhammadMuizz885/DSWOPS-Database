"""
DocFlow SaaS — main.py R8
CRITICAL: StaticFiles mount must be LAST.
CRITICAL: CORS middleware must be added before routers.
"""

import os
import pytesseract
from contextlib import asynccontextmanager

os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.api import routes
from app.api import auth as auth_router

# ── Lifespan ───────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

# ── App (single instance) ──────────────────────
app = FastAPI(
    title="DocFlow SaaS",
    description="Multi-tenant Document Scanning SaaS — R8",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS (must be before routers) ─────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*", "X-Auth-Token"],
    expose_headers=["X-Auth-Token"],
)

# ── Routers ────────────────────────────────────
app.include_router(auth_router.router, prefix="/api")
app.include_router(routes.router, prefix="/api")

# ── Health ─────────────────────────────────────
@app.get("/health")
def health():
    from app.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}

# ── Exception handlers ─────────────────────────
@app.exception_handler(500)
def server_error(request: Request, exc):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# ── StaticFiles (must be LAST) ─────────────────
app.mount("/uploads", StaticFiles(directory="app/static/uploads"), name="uploads")