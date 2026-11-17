"""Briefs & Action Tracking router."""

import json
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ..db import query
from ..services.brief_generator import generate_brief_for_company
from ..services.email import send_brief

router = APIRouter(tags=["briefs"])
log = logging.getLogger(__name__)


class ActionUpdateRequest(BaseModel):
    status: str  # 'open', 'in_progress', 'done'


class EmailBriefRequest(BaseModel):
    recipient_email: str


@router.post("/api/companies/{company_id}/briefs/generate")
def create_brief(company_id: int):
    """Generate a full 10-section Monday Morning Intelligence Brief."""
    company = query("SELECT id FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, "Company not found")

    try:
        brief = generate_brief_for_company(company_id, trigger="manual")
        return brief
    except Exception as e:
        log.error("Failed to generate brief: %s", e)
        raise HTTPException(500, f"Brief generation failed: {str(e)}")


@router.get("/api/companies/{company_id}/briefs")
def list_company_briefs(company_id: int):
    """List historical briefs for a company."""
    company = query("SELECT id FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, "Company not found")

    briefs = query(
        """SELECT id, company_id, period_start, period_end, trigger, created_at,
                  content->>'title' as title,
                  jsonb_array_length(content->'executive_summary') as summary_points_count
           FROM briefs
           WHERE company_id = %s
           ORDER BY created_at DESC""",
        (company_id,)
    ) or []

    return briefs


@router.get("/api/briefs/{brief_id}")
def get_brief(brief_id: int):
    """Retrieve full brief JSON content, HTML, and associated actions."""
    brief = query("SELECT * FROM briefs WHERE id = %s", (brief_id,), one=True)
    if not brief:
        raise HTTPException(404, "Brief not found")

    actions = query(
        "SELECT * FROM actions WHERE brief_id = %s ORDER BY id ASC",
        (brief_id,)
    ) or []
    brief["actions"] = actions
    return brief


@router.get("/api/briefs/{brief_id}/html", response_class=HTMLResponse)
def get_brief_html(brief_id: int):
    """View the clean executive HTML version of the brief directly in browser."""
    brief = query("SELECT html FROM briefs WHERE id = %s", (brief_id,), one=True)
    if not brief or not brief.get("html"):
        raise HTTPException(404, "Brief HTML not found")
    return HTMLResponse(content=brief["html"])


@router.patch("/api/actions/{action_id}")
def update_action_status(action_id: int, body: ActionUpdateRequest):
    """Update action status (open, in_progress, done)."""
    existing = query("SELECT * FROM actions WHERE id = %s", (action_id,), one=True)
    if not existing:
        raise HTTPException(404, "Action item not found")

    if body.status not in ("open", "in_progress", "done"):
        raise HTTPException(400, "Invalid status. Must be 'open', 'in_progress', or 'done'")

    updated = query(
        """UPDATE actions
           SET status = %s, updated_at = now()
           WHERE id = %s
           RETURNING *""",
        (body.status, action_id),
        one=True
    )
    return updated


@router.post("/api/briefs/{brief_id}/email")
def email_brief(brief_id: int, body: EmailBriefRequest):
    """Email the brief via Gmail SMTP."""
    brief = query(
        """SELECT b.*, c.name as company_name
           FROM briefs b
           JOIN companies c ON c.id = b.company_id
           WHERE b.id = %s""",
        (brief_id,),
        one=True
    )
    if not brief:
        raise HTTPException(404, "Brief not found")

    subject = f"Monday Morning Intelligence Brief: {brief['company_name']}"
    html = brief.get("html", "")
    if not html:
        raise HTTPException(400, "Brief has no HTML content to send")

    try:
        send_brief(body.recipient_email, subject, html)
        return {"ok": True, "message": f"Brief successfully sent to {body.recipient_email}"}
    except Exception as e:
        log.error("Failed to email brief: %s", e)
        raise HTTPException(500, f"Email delivery failed: {str(e)}")
