"""
DocFlow SaaS — DataExtractor (R9)
Generic 7-field extraction for any office document type.
Fields: doc_number, date, subject, from_field, to_field, ccwl_no, notes
All fields optional — user can fill/edit manually.
"""

import re
from typing import Any, Dict


def _extract_doc_number(text: str) -> str:
    """Ref No, No., Invoice No, Order No, Letter No etc."""
    m = re.search(
        r'(?:Ref(?:erence)?\.?\s*No\.?|No\.?|Letter\s*No\.?|Invoice\s*No\.?|Order\s*No\.?|File\s*No\.?)\s*[:\-]?\s*([A-Z0-9\/\-]+)',
        text, re.IGNORECASE
    )
    return m.group(1).strip() if m else ""


def _extract_date(text: str) -> str:
    """Find first date-like pattern in document."""
    m = re.search(
        r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},?\s+\d{4})\b',
        text
    )
    if not m:
        return ""
    raw = m.group(1).strip()
    # Normalise dd/mm/yyyy → yyyy-mm-dd
    nm = re.match(r'^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})$', raw)
    if nm:
        d, mo, y = nm.group(1), nm.group(2), nm.group(3)
        if len(y) == 2:
            y = '20' + y
        return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
    return raw


def _extract_subject(text: str) -> str:
    """Subject: / Sub: / Re: line."""
    m = re.search(r'(?:Subject|Sub|Re)\s*[:\-]\s*(.+)', text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _extract_from(text: str) -> str:
    """From: / Issued by: / Sender line."""
    m = re.search(r'(?:From|Issued\s*by|Sender)\s*[:\-]\s*(.+)', text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _extract_to(text: str) -> str:
    """To: addressee block — grabs lines until a stop keyword."""
    STOP = re.compile(
        r'^\s*(Subject|Sub|CC|C\.C\.|Dated|No\.|From|Ref|Through|Sir|Madam|Dear)',
        re.IGNORECASE
    )
    lines = text.splitlines()
    capturing = False
    collected = []
    for line in lines:
        stripped = line.strip()
        if re.match(r'^To[,:\s]', stripped, re.IGNORECASE) and not capturing:
            capturing = True
            after = re.sub(r'^To[,:\s]*', '', stripped, flags=re.IGNORECASE).strip()
            if after:
                collected.append(after)
            continue
        if capturing:
            if not stripped or STOP.match(stripped):
                break
            collected.append(stripped)
    return ', '.join(collected).strip(', ')


def _extract_ccwl(text: str) -> str:
    """CCWL / Copy forwarded block."""
    m = re.search(
        r'\bCCWL[,:\s]*\n?([\s\S]+?)(?=\n\s*(?:No\.|$|\Z))',
        text, re.IGNORECASE
    )
    if m:
        return re.sub(r'\s*\n\s*', '; ', m.group(1).strip()).strip('; ')
    m2 = re.search(
        r'Copy\s+(?:forwarded|to)\s*[:\-]?\s*([\s\S]+?)(?=\n\s*\n|\Z)',
        text, re.IGNORECASE
    )
    if m2:
        return re.sub(r'\s*\n\s*', '; ', m2.group(1).strip()).strip('; ')
    return ""


def _confidence(value: str, high_len: int = 15) -> float:
    if not value or len(value) < 3:
        return 0.0
    return 0.80 if len(value) >= high_len else 0.55


class DataExtractor:

    @staticmethod
    def extract(ocr_text: str, document_kind: str = None, direction: str = None) -> Dict[str, Any]:
        """
        Extract 7 generic fields from any document type.
        All fields optional — empty string means user fills manually.
        """
        doc_number = _extract_doc_number(ocr_text)
        date       = _extract_date(ocr_text)
        subject    = _extract_subject(ocr_text)
        from_field = _extract_from(ocr_text)
        to_field   = _extract_to(ocr_text)
        ccwl_no    = _extract_ccwl(ocr_text)

        # Overall confidence based on how many fields were extracted
        filled = sum(1 for v in [doc_number, date, subject, from_field, to_field, ccwl_no] if v)
        overall_confidence = round(filled / 6, 3)

        return {
            "doc_number": doc_number,
            "date":       date,
            "subject":    subject,
            "from_field": from_field,
            "to_field":   to_field,
            "ccwl_no":    ccwl_no,
            "notes":      "",          # always blank — user fills
            "_confidence": overall_confidence,
        }


def average_confidence(fields: Dict[str, Any]) -> float:
    if "_confidence" in fields:
        return fields["_confidence"]
    vals = [v for v in fields.values() if isinstance(v, (int, float))]
    return round(sum(vals) / len(vals), 3) if vals else 0.0