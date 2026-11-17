"""Crawler router: Triggers polite crawling, change detection, and document ingestion."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..db import query
from ..services.crawler import crawl_company_sources, crawl_source

router = APIRouter(tags=["crawler"])
log = logging.getLogger(__name__)


@router.post("/api/companies/{company_id}/crawl")
def trigger_company_crawl(company_id: int):
    """Crawl all approved sources for a company, extract documents, and detect changes."""
    company = query("SELECT id FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, "Company not found")

    try:
        summary = crawl_company_sources(company_id)
        return summary
    except Exception as e:
        log.error("Company crawl failed: %s", e)
        raise HTTPException(500, f"Crawl failed: {str(e)}")


@router.post("/api/sources/{source_id}/crawl")
def trigger_single_source_crawl(source_id: int):
    """Crawl a single source on demand."""
    source = query("SELECT id FROM sources WHERE id = %s", (source_id,), one=True)
    if not source:
        raise HTTPException(404, "Source not found")

    try:
        res = crawl_source(source_id)
        return res
    except Exception as e:
        log.error("Single source crawl failed: %s", e)
        raise HTTPException(500, f"Source crawl failed: {str(e)}")


@router.get("/api/companies/{company_id}/documents")
def list_company_documents(company_id: int, limit: int = 50):
    """List documents collected from sources for this company."""
    company = query("SELECT id FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, "Company not found")

    docs = query(
        """SELECT d.id, d.source_id, d.url, d.title, d.content_hash, d.published_at, d.discovered_at,
                  s.name as source_name, s.category as source_category, s.competitor_name
           FROM documents d
           JOIN sources s ON s.id = d.source_id
           WHERE s.company_id = %s
           ORDER BY d.discovered_at DESC
           LIMIT %s""",
        (company_id, limit)
    ) or []

    return docs
