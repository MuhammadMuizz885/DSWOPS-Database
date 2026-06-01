"""
DocFlow SaaS — recreate_db.py
Drops and recreates all tables. Seeds super admin + demo org.
"""
import os, sys, hashlib, secrets
sys.path.insert(0, os.path.dirname(__file__))

os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR"
try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
except Exception:
    pass

from app.database import engine
from app.models.database import Base, Organization, User, UploadRecord, Document, AuditLog, SystemSetting

print("⚙  Dropping all tables…")
Base.metadata.drop_all(bind=engine)
print("⚙  Recreating all tables…")
Base.metadata.create_all(bind=engine)

from sqlalchemy.orm import Session
db = Session(bind=engine)

# ── Super admin (no org — platform owner = you) ──
super_admin = User(
    org_id=None,
    username="superadmin",
    password_hash=hashlib.sha256("superadmin1234".encode()).hexdigest(),
    role="superadmin",
    display_name="Platform Owner",
    token=secrets.token_hex(32),
    is_active=True,
)
db.add(super_admin)

# ── Demo org (so you can test immediately) ───────
demo_org = Organization(
    name="Demo Office",
    slug="demo",
    plan="pro",
    is_active=True,
    footer_text="Powered by DocFlow",
)
db.add(demo_org)
db.flush()  # get demo_org.id

# ── Demo org admin ───────────────────────────────
demo_admin = User(
    org_id=demo_org.id,
    username="admin",
    password_hash=hashlib.sha256("admin1234".encode()).hexdigest(),
    role="admin",
    display_name="Demo Administrator",
    token=secrets.token_hex(32),
    is_active=True,
)
db.add(demo_admin)

db.commit()
db.close()

print()
print("✅  Database ready.")
print("    Super admin  → superadmin / superadmin1234")
print("    Demo org     → admin / admin1234  (org: demo)")