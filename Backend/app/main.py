import subprocess
import sys
import os

def ensure_tesseract():
    import shutil
    if shutil.which("tesseract") is None:
        print("Tesseract not found — installing via apt...")
        subprocess.run(["apt-get", "update", "-y"], check=True)
        subprocess.run(
            ["apt-get", "install", "-y", "tesseract-ocr", "tesseract-ocr-eng"],
            check=True
        )
        print("Tesseract installed successfully.")
    else:
        print("Tesseract already available.")

ensure_tesseract()


"""
DocFlow SaaS — main.py R8
CRITICAL: StaticFiles mount must be LAST.
CRITICAL: CORS middleware must be added before routers.
"""
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from sqlalchemy import text
import os
import pytesseract
from contextlib import asynccontextmanager

# --------------------------------------------------------------
# os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR"
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


import sys

# ── Dynamic Tesseract Configuration ───────────────────
# If running on Windows (your local machine)
if sys.platform.startswith("win"):
    os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR"
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# If running on Linux (Railway production server)
else:
    # Linux automatically adds tesseract to the global PATH, 
    # so we just point directly to the binary command.
    pytesseract.pytesseract.tesseract_cmd = "tesseract"

# ---------------------------------------------------------------

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
    allow_origins=[
    "https://dswops.vercel.app",
    "http://localhost:3000"
    ],
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
def health_check(db: Session = Depends(get_db)):
    import subprocess
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    try:
        result = subprocess.run(
            ["tesseract", "--version"],
            capture_output=True, text=True, timeout=5
        )
        tess_status = result.stdout.strip().split("\n")[0] if result.returncode == 0 else f"error: {result.stderr}"
    except FileNotFoundError:
        tess_status = "NOT FOUND in PATH"
    except Exception as e:
        tess_status = f"error: {str(e)}"

    return {"status": "ok", "db": db_status, "tesseract": tess_status}

# debug tessearact -------------------------------------------

@app.get("/debug-tesseract")
def debug_tesseract():
    import subprocess
    import shutil
    import os

    results = {}

    # 1. Is the binary findable?
    results["which_tesseract"] = shutil.which("tesseract")

    # 2. What does pytesseract think the cmd is?
    import pytesseract
    results["pytesseract_cmd"] = pytesseract.pytesseract.tesseract_cmd

    # 3. Try running it directly
    try:
        r = subprocess.run(["tesseract", "--version"], capture_output=True, text=True, timeout=5)
        results["tesseract_version"] = r.stdout + r.stderr
        results["returncode"] = r.returncode
    except FileNotFoundError:
        results["tesseract_version"] = "FileNotFoundError — not in PATH"
    except Exception as e:
        results["tesseract_version"] = str(e)

    # 4. What is the PATH?
    results["PATH"] = os.environ.get("PATH", "not set")

    # 5. Is tessdata present?
    try:
        r2 = subprocess.run(["find", "/usr", "-name", "eng.traineddata"], capture_output=True, text=True, timeout=5)
        results["eng_traineddata"] = r2.stdout.strip() or "NOT FOUND"
    except Exception as e:
        results["eng_traineddata"] = str(e)

    # 6. TESSDATA_PREFIX
    results["TESSDATA_PREFIX"] = os.environ.get("TESSDATA_PREFIX", "not set")

    return results

# ── Exception handlers ─────────────────────────
@app.exception_handler(500)
def server_error(request: Request, exc):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# ── StaticFiles (must be LAST) ─────────────────
app.mount("/uploads", StaticFiles(directory="app/static/uploads"), name="uploads")