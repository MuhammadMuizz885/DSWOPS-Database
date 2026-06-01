"""
DocFlow SaaS — Routes R9
Generic 7-field document model.
Fields: doc_number, date, subject, from_field, to_field, ccwl_no, notes
All scoped by org_id (multi-tenant).
"""

import os, shutil
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.database import AuditLog, UploadRecord, Document, User, Organization
from app.services.data_extractor import DataExtractor
from app.services.ocr_service import OCRService

router = APIRouter()
ocr_service = OCRService()
data_extractor = DataExtractor()

UPLOAD_DIR = "./app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

VIEWER_ROLES = ["admin", "manager", "officer", "viewer"]
UPLOAD_ROLES = ["admin", "manager", "officer"]


# ─────────────────────────────────────────────
# UPLOAD
# ─────────────────────────────────────────────
@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in UPLOAD_ROLES:
        raise HTTPException(status_code=403, detail="Your role cannot upload documents")

    document_kind = request.headers.get("X-Document-Kind", "letter")
    direction     = request.headers.get("X-Direction", "incoming")
    role          = request.headers.get("X-Role", current_user.role)

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{timestamp}_{role}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        from app.services.compressor import compress_file
        file_path = compress_file(file_path)
    except Exception:
        pass

    final_filename = os.path.basename(file_path)

    record = UploadRecord(
        org_id=current_user.org_id,
        user_id=current_user.id,
        file_path=file_path,
        original_filename=final_filename,
        document_kind=document_kind,
        direction=direction,
        role=role,
        status="pending",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    _log(db, record.id, current_user.org_id, current_user.id, "upload", role, final_filename)
    return {"upload_id": record.id, "filename": final_filename, "status": "pending"}


# ─────────────────────────────────────────────
# OCR EXTRACT
# ─────────────────────────────────────────────
@router.post("/extract/{upload_id}")
def extract_document(
    upload_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = _get_record(upload_id, current_user.org_id, db)
    _check_ownership(record, current_user)

    record.status = "processing"
    db.commit()

    try:
        ocr_result = ocr_service.extract_text(record.file_path)
        ocr_text   = ocr_result[0] if isinstance(ocr_result, tuple) else ocr_result
        confidence = ocr_result[1] if isinstance(ocr_result, tuple) and len(ocr_result) > 1 else 0.85

        extracted = data_extractor.extract(ocr_text, record.document_kind, record.direction)

        record.ocr_raw_text     = ocr_text
        record.confidence_score = confidence
        record.status           = "completed"
        db.commit()

        # Remove internal key before sending to frontend
        fields_out = {k: v for k, v in extracted.items() if not k.startswith("_")}

        _log(db, record.id, current_user.org_id, current_user.id, "extract", record.role, record.original_filename)
        return {
            "upload_id":        upload_id,
            "extracted_fields": fields_out,
            "confidence_score": round(confidence * 100),
        }
    except Exception as e:
        record.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"OCR extraction failed: {str(e)}")


# ─────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────
@router.post("/save/{upload_id}")
def save_document(
    upload_id: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = _get_record(upload_id, current_user.org_id, db)
    _check_ownership(record, current_user)

    # Remove existing saved doc if re-saving
    db.query(Document).filter(Document.upload_id == upload_id).delete()

    doc = Document(
        org_id        = current_user.org_id,
        upload_id     = upload_id,
        user_id       = current_user.id,
        role          = record.role,
        document_kind = record.document_kind,
        direction     = record.direction,
        doc_number    = data.get("doc_number", ""),
        date          = data.get("date", ""),
        subject       = data.get("subject", ""),
        from_field    = data.get("from_field", ""),
        to_field      = data.get("to_field", ""),
        ccwl_no       = data.get("ccwl_no", ""),
        notes         = data.get("notes", ""),
    )
    db.add(doc)
    record.status = "completed"
    db.commit()

    _log(db, upload_id, current_user.org_id, current_user.id, "save", record.role, record.original_filename)
    return {"message": "Saved successfully", "upload_id": upload_id}


# ─────────────────────────────────────────────
# RECORDS LIST
# ─────────────────────────────────────────────
@router.get("/documents")
def list_documents(
    page:        int = Query(1, ge=1),
    limit:       int = Query(20, ge=1, le=100),
    search:      str = Query(""),
    kind_filter: str = Query(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(UploadRecord).filter(UploadRecord.org_id == current_user.org_id)

    if current_user.role not in ("admin", "manager"):
        query = query.filter(UploadRecord.user_id == current_user.id)

    if search:      query = query.filter(UploadRecord.original_filename.ilike(f"%{search}%"))
    if kind_filter: query = query.filter(UploadRecord.document_kind == kind_filter)

    total   = query.count()
    records = query.order_by(UploadRecord.created_at.desc()).offset((page-1)*limit).limit(limit).all()

    return {
        "total":   total,
        "page":    page,
        "pages":   max(1, (total + limit - 1) // limit),
        "records": [_fmt_record(r) for r in records],
    }


# ─────────────────────────────────────────────
# RECORD DETAIL
# ─────────────────────────────────────────────
@router.get("/document/{upload_id}")
def get_document(
    upload_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = _get_record(upload_id, current_user.org_id, db)
    if current_user.role not in ("admin", "manager"):
        _check_ownership(record, current_user)

    doc = db.query(Document).filter(Document.upload_id == upload_id).first()
    fields = {}
    if doc:
        fields = {
            "doc_number": doc.doc_number,
            "date":       doc.date,
            "subject":    doc.subject,
            "from_field": doc.from_field,
            "to_field":   doc.to_field,
            "ccwl_no":    doc.ccwl_no,
            "notes":      doc.notes,
        }

    return {
        **_fmt_record(record),
        "file_url": f"/uploads/{os.path.basename(record.file_path)}" if record.file_path else None,
        "fields": fields,
    }


# ─────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────
@router.delete("/document/{upload_id}")
def delete_document(
    upload_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = _get_record(upload_id, current_user.org_id, db)
    if current_user.role not in ("admin", "manager"):
        _check_ownership(record, current_user)

    _log(db, upload_id, current_user.org_id, current_user.id, "delete", record.role, record.original_filename)
    db.query(Document).filter(Document.upload_id == upload_id).delete()
    db.query(AuditLog).filter(AuditLog.upload_id == upload_id).delete()
    if record.file_path and os.path.exists(record.file_path):
        os.remove(record.file_path)
    db.delete(record)
    db.commit()
    return {"message": "Deleted"}


# ─────────────────────────────────────────────
# BULK DELETE
# ─────────────────────────────────────────────
@router.delete("/documents/bulk")
def bulk_delete(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ids = data.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="No IDs provided")
    deleted = 0
    for uid in ids:
        record = db.query(UploadRecord).filter(
            UploadRecord.id == uid, UploadRecord.org_id == current_user.org_id).first()
        if not record:
            continue
        if current_user.role not in ("admin", "manager") and record.user_id != current_user.id:
            continue
        db.query(Document).filter(Document.upload_id == uid).delete()
        db.query(AuditLog).filter(AuditLog.upload_id == uid).delete()
        if record.file_path and os.path.exists(record.file_path):
            os.remove(record.file_path)
        db.delete(record)
        _log(db, None, current_user.org_id, current_user.id, "delete", record.role, record.original_filename)
        deleted += 1
    db.commit()
    return {"message": f"{deleted} record(s) deleted", "deleted": deleted}


# ─────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────
@router.get("/stats")
def get_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(UploadRecord).filter(UploadRecord.org_id == current_user.org_id)
    if current_user.role not in ("admin", "manager"):
        q = q.filter(UploadRecord.user_id == current_user.id)
    total     = q.count()
    completed = q.filter(UploadRecord.status == "completed").count()
    failed    = q.filter(UploadRecord.status == "failed").count()
    letters   = q.filter(UploadRecord.document_kind == "letter").count()
    orders    = q.filter(UploadRecord.document_kind == "office_order").count()
    return {
        "total": total, "completed": completed, "failed": failed,
        "letters": letters, "office_orders": orders,
        "success_rate": round(completed / total * 100, 1) if total else 0,
    }


# ─────────────────────────────────────────────
# AUDIT LOG
# ─────────────────────────────────────────────
@router.get("/audit-logs")
def get_audit_logs(
    page:  int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(AuditLog).filter(AuditLog.org_id == current_user.org_id)
    if current_user.role not in ("admin", "manager"):
        q = q.filter(AuditLog.user_id == current_user.id)
    total = q.count()
    logs  = q.order_by(AuditLog.timestamp.desc()).offset((page-1)*limit).limit(limit).all()
    return {
        "total": total,
        "logs": [{"id": l.id, "action": l.action, "role": l.role,
                  "filename": l.filename,
                  "timestamp": l.timestamp.isoformat() if l.timestamp else None}
                 for l in logs],
    }


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def _get_record(upload_id: int, org_id: int, db: Session) -> UploadRecord:
    record = db.query(UploadRecord).filter(
        UploadRecord.id == upload_id, UploadRecord.org_id == org_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

def _check_ownership(record: UploadRecord, user: User):
    if record.user_id != user.id and user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="Access denied")

def _fmt_record(r: UploadRecord) -> dict:
    return {
        "id": r.id, "filename": r.original_filename,
        "document_kind": r.document_kind, "direction": r.direction,
        "role": r.role, "status": r.status,
        "confidence_score": r.confidence_score,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }

def _log(db, upload_id, org_id, user_id, action, role, filename):
    try:
        db.add(AuditLog(upload_id=upload_id, org_id=org_id, user_id=user_id,
                        action=action, role=role, filename=filename))
        db.commit()
    except Exception:
        pass