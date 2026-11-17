"""Router for Internal Intelligence Document Uploads."""

import logging
from fastapi import APIRouter, File, HTTPException, UploadFile
from ..db import query
from ..services.uploads import process_upload_and_extract_signals

router = APIRouter(tags=["uploads"])
log = logging.getLogger(__name__)


@router.get("/api/companies/{company_id}/uploads")
def list_company_uploads(company_id: int):
    """List historical internal file uploads for a company."""
    company = query("SELECT id FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, f"Company {company_id} not found")

    return query(
        """SELECT id, company_id, filename, kind, length(extracted_text) as char_count, uploaded_at
           FROM uploads
           WHERE company_id = %s
           ORDER BY uploaded_at DESC""",
        (company_id,)
    )


@router.post("/api/companies/{company_id}/uploads")
async def upload_internal_document(company_id: int, file: UploadFile = File(...)):
    """Upload a CSV, XLSX, PDF, or TXT internal intelligence file to extract objections, lost deals, and requests."""
    company = query("SELECT id, name FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, f"Company {company_id} not found")

    filename = file.filename or "upload.txt"
    fname_lower = filename.lower()
    allowed_exts = (".csv", ".xlsx", ".xls", ".pdf", ".txt", ".md")
    if not any(fname_lower.endswith(ext) for ext in allowed_exts):
        raise HTTPException(400, f"Unsupported file type. Allowed formats: {', '.join(allowed_exts)}")

    try:
        content_bytes = await file.read()
        if not content_bytes:
            raise HTTPException(400, "Uploaded file is empty.")

        result = process_upload_and_extract_signals(
            company_id=company_id,
            filename=filename,
            file_bytes=content_bytes
        )
        return {
            "ok": True,
            "message": f"Successfully processed '{filename}' and created {result['signals_created_count']} internal signals.",
            **result
        }
    except ValueError as ve:
        raise HTTPException(400, str(ve))
    except Exception as e:
        log.error("Internal document upload error for company %s: %s", company_id, e)
        raise HTTPException(500, f"Upload processing failed: {str(e)}")
