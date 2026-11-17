"""Intelligence Feed & Signal Analysis router."""

from datetime import datetime
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..db import query
from ..services.analysis import analyze_unprocessed_documents, analyze_document

router = APIRouter(tags=["feed"])
log = logging.getLogger(__name__)


@router.post("/api/companies/{company_id}/analyze")
def trigger_analysis(company_id: int):
    """Run analysis engine over all unanalyzed documents for a company."""
    company = query("SELECT id FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, "Company not found")

    try:
        res = analyze_unprocessed_documents(company_id)
        return res
    except Exception as e:
        log.error("Analysis execution failed: %s", e)
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@router.get("/api/companies/{company_id}/feed")
def get_intelligence_feed(
    company_id: int,
    category: Optional[str] = None,
    competitor: Optional[str] = None,
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    min_relevance: Optional[float] = None,
    impact: Optional[str] = None,
    verification: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Retrieve filtered, ranked signals for a company."""
    company = query("SELECT id FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, "Company not found")

    sql = "SELECT * FROM signals WHERE company_id = %s"
    params = [company_id]

    if category and category != "all":
        sql += " AND category = %s"
        params.append(category)

    if competitor and competitor != "all":
        sql += " AND competitor_name = %s"
        params.append(competitor)

    if impact and impact != "all":
        sql += " AND impact_type = %s"
        params.append(impact)

    if verification and verification != "all":
        sql += " AND verification_status = %s"
        params.append(verification)

    if min_relevance is not None:
        sql += " AND strategic_relevance >= %s"
        params.append(min_relevance)

    if from_date:
        sql += " AND discovered_at >= %s"
        params.append(from_date)

    if to_date:
        sql += " AND discovered_at <= %s"
        params.append(to_date)

    sql += " ORDER BY rank_score DESC, discovered_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    signals = query(sql, tuple(params)) or []

    # Get competitors list for filter dropdown
    competitors_rows = query(
        """SELECT DISTINCT competitor_name FROM signals
           WHERE company_id = %s AND competitor_name IS NOT NULL AND competitor_name != ''""",
        (company_id,)
    ) or []
    competitor_list = [r["competitor_name"] for r in competitors_rows]

    # Metrics count
    stats = {
        "total_signals": len(signals),
        "opportunities": len([s for s in signals if s.get("impact_type") == "opportunity"]),
        "threats": len([s for s in signals if s.get("impact_type") == "threat"]),
        "verified_count": len([s for s in signals if s.get("verification_status") == "verified"]),
    }

    return {
        "company_id": company_id,
        "stats": stats,
        "competitors": competitor_list,
        "signals": signals
    }


@router.get("/api/signals/{signal_id}")
def get_signal_detail(signal_id: int):
    """Get single signal with full trace evidence."""
    sig = query("SELECT * FROM signals WHERE id = %s", (signal_id,), one=True)
    if not sig:
        raise HTTPException(404, "Signal not found")
    return sig
