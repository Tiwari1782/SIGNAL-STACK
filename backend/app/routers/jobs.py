"""Router for Job Runs, Scheduled Trigger Endpoints, and Audit Reports."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from ..db import query
from ...jobs.runner import run_logged
from ...jobs.weekly_brief import generate_for_company
from ...jobs.monthly_audit import audit_company

router = APIRouter(tags=["jobs"])
log = logging.getLogger(__name__)


class RunJobRequest(BaseModel):
    company_id: Optional[int] = None


@router.get("/api/job-runs")
def list_all_job_runs(limit: int = 50):
    """List recent job executions across all tasks."""
    return query(
        """SELECT j.*, c.name as company_name
           FROM job_runs j
           LEFT JOIN companies c ON c.id = j.company_id
           ORDER BY j.started_at DESC
           LIMIT %s""",
        (limit,)
    )


@router.get("/api/companies/{company_id}/job-runs")
def list_company_job_runs(company_id: int, limit: int = 30):
    """List job runs for a specific company."""
    return query(
        """SELECT j.*, c.name as company_name
           FROM job_runs j
           LEFT JOIN companies c ON c.id = j.company_id
           WHERE j.company_id = %s OR j.company_id IS NULL
           ORDER BY j.started_at DESC
           LIMIT %s""",
        (company_id, limit)
    )


@router.post("/api/jobs/weekly_brief/run")
def trigger_weekly_brief(body: RunJobRequest):
    """Manually trigger the full weekly brief pipeline."""
    company_id = body.company_id
    if not company_id:
        c = query("SELECT id FROM companies ORDER BY id LIMIT 1", one=True)
        if not c:
            raise HTTPException(400, "No company exists to run brief for")
        company_id = c["id"]

    try:
        run_res = run_logged(
            "weekly_brief",
            lambda: generate_for_company(company_id),
            company_id=company_id,
            raise_on_error=False
        )
        return run_res
    except Exception as e:
        log.error("Failed executing weekly brief trigger: %s", e)
        raise HTTPException(500, f"Weekly brief failed: {str(e)}")


@router.post("/api/jobs/monthly_audit/run")
def trigger_monthly_audit(body: RunJobRequest):
    """Manually trigger the Signal Stack monthly health audit."""
    company_id = body.company_id
    if not company_id:
        c = query("SELECT id FROM companies ORDER BY id LIMIT 1", one=True)
        if not c:
            raise HTTPException(400, "No company exists to run audit for")
        company_id = c["id"]

    try:
        run_res = run_logged(
            "monthly_audit",
            lambda: audit_company(company_id),
            company_id=company_id,
            raise_on_error=False
        )
        return run_res
    except Exception as e:
        log.error("Failed executing monthly audit trigger: %s", e)
        raise HTTPException(500, f"Monthly audit failed: {str(e)}")


@router.get("/api/companies/{company_id}/audit-reports")
def list_audit_reports(company_id: int, limit: int = 20):
    """List historical monthly audit reports for a company."""
    return query(
        """SELECT id, company_id, created_at,
                  (content->>'health_score')::int as health_score,
                  (content->>'total_sources_audited')::int as total_sources_audited,
                  content->>'summary' as summary,
                  content
           FROM audit_reports
           WHERE company_id = %s
           ORDER BY created_at DESC
           LIMIT %s""",
        (company_id, limit)
    )


@router.get("/api/audit-reports/{report_id}")
def get_audit_report(report_id: int):
    """Get a specific full audit report."""
    report = query(
        """SELECT a.*, c.name as company_name
           FROM audit_reports a
           JOIN companies c ON c.id = a.company_id
           WHERE a.id = %s""",
        (report_id,),
        one=True
    )
    if not report:
        raise HTTPException(404, "Audit report not found")
    return report
