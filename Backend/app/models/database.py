"""
DocFlow SaaS — Database Models R9
Generic 7-field Document table.
Fields: doc_number, date, subject, from_field, to_field, ccwl_no, notes
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Organization(Base):
    __tablename__ = "organizations"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    name          = Column(String(200), nullable=False)
    slug          = Column(String(100), unique=True, nullable=False)
    plan          = Column(String(50), default="free")
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    logo_url      = Column(Text)
    primary_color = Column(String(20), default="#4f6ef7")
    footer_text   = Column(String(300), default="Powered by DocFlow")


class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    org_id        = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    username      = Column(String(60), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role          = Column(String(60), nullable=False)
    display_name  = Column(String(120))
    token         = Column(String(255), unique=True)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)


class UploadRecord(Base):
    __tablename__ = "upload_records"
    id                = Column(Integer, primary_key=True, autoincrement=True)
    org_id            = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id           = Column(Integer, ForeignKey("users.id"), nullable=True)
    file_path         = Column(String(500))
    original_filename = Column(String(255))
    document_kind     = Column(String(60))
    direction         = Column(String(60))
    role              = Column(String(60))
    status            = Column(Enum("pending", "processing", "completed", "failed"), default="pending")
    confidence_score  = Column(Float)
    ocr_raw_text      = Column(Text)
    created_at        = Column(DateTime, default=datetime.utcnow)
    updated_at        = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    org_id        = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    upload_id     = Column(Integer, ForeignKey("upload_records.id"))
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=True)
    role          = Column(String(60))
    document_kind = Column(String(60))
    direction     = Column(String(60))
    # ── 7 generic fields (all optional) ──────
    doc_number    = Column(String(200))   # Ref No, Letter No, Invoice No, etc.
    date          = Column(String(50))    # any date found
    subject       = Column(String(500))   # Subject / title line
    from_field    = Column(String(300))   # Sender / issuing party
    to_field      = Column(Text)          # Recipient / addressee
    ccwl_no       = Column(String(300))   # CCWL / copy forwarded
    notes         = Column(Text)          # free text / user notes
    # ─────────────────────────────────────────
    is_verified   = Column(Boolean, default=False)
    created_at    = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id        = Column(Integer, primary_key=True, autoincrement=True)
    org_id    = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    upload_id = Column(Integer, ForeignKey("upload_records.id"), nullable=True)
    user_id   = Column(Integer, ForeignKey("users.id"), nullable=True)
    action    = Column(String(100))
    role      = Column(String(60))
    filename  = Column(String(255))
    timestamp = Column(DateTime, default=datetime.utcnow)


class SystemSetting(Base):
    __tablename__ = "system_settings"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    org_id     = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    key        = Column(String(100), nullable=False)
    value      = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)