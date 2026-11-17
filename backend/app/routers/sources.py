"""Sources and Signal Stack management endpoints."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..db import query
from ..services.discovery import discover_sources_for_company

router = APIRouter(tags=["sources"])
log = logging.getLogger(__name__)


class SourceCreateRequest(BaseModel):
    category: str
    name: str
    url: str
    reason: str
    competitor_name: Optional[str] = None
    source_reliability: Optional[float] = 0.8
    relevance_score: Optional[float] = 0.8


@router.post("/api/companies/{company_id}/signal-stack/build")
def build_signal_stack(company_id: int):
    """Trigger dynamic source discovery across Customers, Competitors, Market, and Internal."""
    company = query("SELECT * FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, "Company not found")

    try:
        discovered = discover_sources_for_company(company_id)
    except Exception as e:
        log.error("Failed to discover sources: %s", e)
        raise HTTPException(500, f"Source discovery failed: {str(e)}")

    return get_signal_stack(company_id)


@router.get("/api/companies/{company_id}/signal-stack")
def get_signal_stack(company_id: int):
    """Get the complete Signal Stack grouped by the 4 categories."""
    company = query("SELECT * FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, "Company not found")

    all_sources = query(
        """SELECT * FROM sources
           WHERE company_id = %s AND status != 'removed'
           ORDER BY relevance_score DESC, discovered_at DESC""",
        (company_id,)
    ) or []

    categories = {
        "customers": [],
        "competitors": [],
        "market": [],
        "internal": []
    }

    for s in all_sources:
        cat = s.get("category")
        if cat in categories:
            categories[cat].append(s)

    approved_count = len([s for s in all_sources if s["status"] == "approved"])
    suggested_count = len([s for s in all_sources if s["status"] == "suggested"])
    competitors = set(s["competitor_name"] for s in categories["competitors"] if s.get("competitor_name"))

    return {
        "company": company,
        "categories": categories,
        "stats": {
            "total_sources": len(all_sources),
            "approved_count": approved_count,
            "suggested_count": suggested_count,
            "competitor_count": len(competitors)
        }
    }


@router.get("/api/companies/{company_id}/sources")
def list_sources(
    company_id: int,
    category: Optional[str] = None,
    status: Optional[str] = None
):
    """List sources with optional category and status filters."""
    company = query("SELECT id FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, "Company not found")

    sql = "SELECT * FROM sources WHERE company_id = %s"
    params = [company_id]

    if category:
        sql += " AND category = %s"
        params.append(category)
    if status:
        sql += " AND status = %s"
        params.append(status)
    else:
        sql += " AND status != 'removed'"

    sql += " ORDER BY relevance_score DESC, discovered_at DESC"
    sources = query(sql, tuple(params))
    return sources


@router.post("/api/companies/{company_id}/sources")
def create_custom_source(company_id: int, body: SourceCreateRequest):
    """Manually add an intelligence source."""
    company = query("SELECT id FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, "Company not found")

    if body.category not in ("customers", "competitors", "market", "internal"):
        raise HTTPException(400, "Invalid category")

    source = query(
        """INSERT INTO sources (
             company_id, category, name, url, reason, status,
             competitor_name, source_reliability, relevance_score
           ) VALUES (%s, %s, %s, %s, %s, 'approved', %s, %s, %s)
           ON CONFLICT (company_id, url) DO UPDATE
           SET name = EXCLUDED.name,
               reason = EXCLUDED.reason,
               status = 'approved'
           RETURNING *""",
        (
            company_id,
            body.category,
            body.name,
            body.url,
            body.reason,
            body.competitor_name,
            body.source_reliability or 0.8,
            body.relevance_score or 0.8
        ),
        one=True
    )
    return source


@router.post("/api/sources/{source_id}/approve")
def approve_source(source_id: int):
    """Approve a suggested source for active crawling."""
    source = query("SELECT * FROM sources WHERE id = %s", (source_id,), one=True)
    if not source:
        raise HTTPException(404, "Source not found")

    updated = query(
        "UPDATE sources SET status = 'approved' WHERE id = %s RETURNING *",
        (source_id,),
        one=True
    )
    return updated


@router.post("/api/companies/{company_id}/sources/approve-all")
def approve_all_sources(company_id: int):
    """Approve all suggested sources for a company."""
    company = query("SELECT id FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, "Company not found")

    query(
        "UPDATE sources SET status = 'approved' WHERE company_id = %s AND status = 'suggested'",
        (company_id,)
    )
    return {"message": "All suggested sources approved"}


@router.delete("/api/sources/{source_id}")
def remove_source(source_id: int):
    """Remove a source (soft-delete to 'removed')."""
    source = query("SELECT * FROM sources WHERE id = %s", (source_id,), one=True)
    if not source:
        raise HTTPException(404, "Source not found")

    updated = query(
        "UPDATE sources SET status = 'removed' WHERE id = %s RETURNING *",
        (source_id,),
        one=True
    )
    return updated


@router.get("/api/sources/{source_id}/history")
def get_source_history(source_id: int):
    """View crawl and document history for a source."""
    source = query("SELECT * FROM sources WHERE id = %s", (source_id,), one=True)
    if not source:
        raise HTTPException(404, "Source not found")

    crawl_history = query(
        "SELECT * FROM crawl_runs WHERE source_id = %s ORDER BY started_at DESC LIMIT 20",
        (source_id,)
    ) or []

    documents = query(
        "SELECT id, url, title, content_hash, published_at, discovered_at FROM documents WHERE source_id = %s ORDER BY discovered_at DESC LIMIT 20",
        (source_id,)
    ) or []

    return {
        "source": source,
        "crawl_runs": crawl_history,
        "documents": documents
    }
