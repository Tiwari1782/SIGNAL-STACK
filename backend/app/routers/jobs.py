"""Router for Job Runs, Scheduled Trigger Endpoints, and Audit Reports."""

import logging
import os
import sys
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from ..db import query

try:
    from backend.jobs.runner import run_logged
    from backend.jobs.weekly_brief import generate_for_company
    from backend.jobs.monthly_audit import audit_company
except (ImportError, ModuleNotFoundError, ValueError):
    try:
        from jobs.runner import run_logged
        from jobs.weekly_brief import generate_for_company
        from jobs.monthly_audit import audit_company
    except (ImportError, ModuleNotFoundError, ValueError):
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from jobs.runner import run_logged
        from jobs.weekly_brief import generate_for_company
        from jobs.monthly_audit import audit_company

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
def list_company_job_runs(company_id: int, limit: int = 25):
    """List job runs for a specific company."""
    return query(
        """SELECT * FROM job_runs
           WHERE company_id = %s
           ORDER BY started_at DESC
           LIMIT %s""",
        (company_id, limit)
    )


@router.get("/api/companies/{company_id}/audit-reports")
def list_audit_reports(company_id: int, limit: int = 10):
    """List monthly Signal Stack audit reports for a company."""
    return query(
        """SELECT * FROM audit_reports
           WHERE company_id = %s
           ORDER BY created_at DESC
           LIMIT %s""",
        (company_id, limit)
    )


@router.post("/api/jobs/weekly_brief/run")
def trigger_weekly_brief(body: RunJobRequest, background_tasks: BackgroundTasks):
    """Trigger the Monday Morning Brief generation pipeline on demand."""
    if not body.company_id:
        raise HTTPException(400, "company_id is required to run weekly brief")

    # Run the weekly brief synchronously or via background task
    try:
        res = run_logged(
            job_name="weekly_brief",
            company_id=body.company_id,
            fn=lambda: generate_for_company(body.company_id)
        )
        return {
            "status": "success" if res.get("brief_id") or res.get("id") else "partial",
            "message": "Weekly brief execution completed",
            "summary": res
        }
    except Exception as e:
        log.error("Error triggering weekly brief: %s", e)
        raise HTTPException(500, f"Weekly brief failed: {str(e)}")


@router.post("/api/jobs/monthly_audit/run")
def trigger_monthly_audit(body: RunJobRequest):
    """Trigger the Monthly Signal Stack Audit on demand."""
    if not body.company_id:
        raise HTTPException(400, "company_id is required to run monthly audit")

    try:
        res = run_logged(
            job_name="monthly_audit",
            company_id=body.company_id,
            fn=lambda: audit_company(body.company_id)
        )
        return {
            "status": "success",
            "message": "Monthly audit completed",
            "summary": res
        }
    except Exception as e:
        log.error("Error triggering monthly audit: %s", e)
        raise HTTPException(500, f"Monthly audit failed: {str(e)}")
