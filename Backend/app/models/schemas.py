"""
DSWOPS — Pydantic Schemas (R5)
Updated for role-based letter/office-order structure.
"""

from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


# ─── Upload request ───────────────────────────────────────────────────────────

LETTER_ROLES = Literal[
    "director",
    "deputy_director",
    "admin",
    "educational_officer",
    "veterinary_officer",
    "chief_conservator",
]

OFFICE_ORDER_ROLES = Literal[
    "director",
    "chief_conservator",
]

class UploadMeta(BaseModel):
    """
    Sent alongside the file on upload (as form fields).
    Frontend sets these BEFORE the user picks the file.
    """
    document_kind: Literal["letter", "office_order"]
    # direction: dispatch | dairy.
    # For office_order, frontend forces "dispatch" automatically.
    direction: Literal["dispatch", "dairy"]
    role: str  # validated server-side against allowed roles for the doc kind


# ─── Extracted field value ────────────────────────────────────────────────────

class ExtractedField(BaseModel):
    value:      Optional[str] = None
    confidence: float = 0.0
    editable:   bool  = True


# ─── Extraction results per doc kind ─────────────────────────────────────────

class LetterExtraction(BaseModel):
    letter_no:  ExtractedField
    date:       ExtractedField
    to_field:   ExtractedField
    cc_field:   ExtractedField
    doc_kind:   str = "letter"


class OfficeOrderExtraction(BaseModel):
    office_order_no: ExtractedField
    date:            ExtractedField
    ccwl:            ExtractedField
    doc_kind:        str = "office_order"


# ─── Upload response ──────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    upload_id:      int
    document_kind:  str
    direction:      str
    role:           str
    status:         str
    file_path:      str
    message:        str


# ─── Extract response ─────────────────────────────────────────────────────────

class ExtractResponse(BaseModel):
    upload_id:       int
    document_kind:   str
    role:            str
    confidence_score: float
    fields:          dict   # LetterExtraction or OfficeOrderExtraction as dict
    status:          str


# ─── Save (confirm) request ───────────────────────────────────────────────────

class SaveLetterRequest(BaseModel):
    letter_no:  Optional[str] = None
    date:       Optional[str] = None
    to_field:   Optional[str] = None
    cc_field:   Optional[str] = None
    notes:      Optional[str] = None


class SaveOfficeOrderRequest(BaseModel):
    office_order_no: Optional[str] = None
    date:            Optional[str] = None
    ccwl:            Optional[str] = None
    notes:           Optional[str] = None


# ─── Record response (after save) ────────────────────────────────────────────

class RecordResponse(BaseModel):
    record_id:     int
    upload_id:     int
    document_kind: str
    role:          str
    direction:     str
    created_at:    Optional[datetime] = None
    message:       str


# ─── List / stats ─────────────────────────────────────────────────────────────

class UploadListItem(BaseModel):
    id:             int
    document_kind:  str
    direction:      str
    role:           str
    status:         str
    original_filename: Optional[str]
    confidence_score:  float
    created_at:     Optional[datetime]

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_uploads:        int
    completed:            int
    failed:               int
    pending:              int
    total_letters:        int
    total_office_orders:  int
    success_rate:         float
