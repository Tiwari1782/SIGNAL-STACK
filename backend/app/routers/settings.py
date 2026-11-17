"""Router for Company Settings & Schedule Preferences."""

import json
import logging
from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..db import query

router = APIRouter(tags=["settings"])
log = logging.getLogger(__name__)

DEFAULT_SETTINGS = {
    "briefing_day": "Monday",
    "briefing_time": "08:00",
    "timezone": "UTC",
    "monitor_frequency": "daily",
    "refresh_frequency": "weekly",
    "monthly_audit_enabled": True,
    "email_notifications": False,
    "recipient_email": "",
    "auto_approve_discovered_sources": False,
}


class SettingsUpdate(BaseModel):
    briefing_day: Optional[str] = None
    briefing_time: Optional[str] = None
    timezone: Optional[str] = None
    monitor_frequency: Optional[str] = None
    refresh_frequency: Optional[str] = None
    monthly_audit_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    recipient_email: Optional[str] = None
    auto_approve_discovered_sources: Optional[bool] = None


@router.get("/api/companies/{company_id}/settings")
def get_company_settings(company_id: int):
    """Retrieve settings for a company merged with default preferences."""
    company = query("SELECT id, settings FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, f"Company {company_id} not found")

    saved_settings = company.get("settings") or {}
    if isinstance(saved_settings, str):
        try:
            saved_settings = json.loads(saved_settings)
        except Exception:
            saved_settings = {}

    merged = {**DEFAULT_SETTINGS, **saved_settings}
    return {"company_id": company_id, "settings": merged}


@router.put("/api/companies/{company_id}/settings")
def update_company_settings(company_id: int, payload: dict[str, Any]):
    """Update settings for a company."""
    company = query("SELECT id, settings FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, f"Company {company_id} not found")

    current_settings = company.get("settings") or {}
    if isinstance(current_settings, str):
        try:
            current_settings = json.loads(current_settings)
        except Exception:
            current_settings = {}

    # Merge updates
    updated = {**DEFAULT_SETTINGS, **current_settings, **payload}

    query(
        "UPDATE companies SET settings = %s WHERE id = %s",
        (json.dumps(updated), company_id)
    )

    log.info("Updated settings for company %s", company_id)
    return {"ok": True, "company_id": company_id, "settings": updated}
