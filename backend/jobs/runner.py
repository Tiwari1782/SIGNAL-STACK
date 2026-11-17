"""Wraps every job so success/failure is always logged to job_runs (shown in dashboard)."""
import json
import logging
import traceback
from ..app.db import query

log = logging.getLogger(__name__)


def run_logged(job_name: str, fn, company_id=None, raise_on_error: bool = True):
    run = query(
        "INSERT INTO job_runs (job_name, company_id, status) VALUES (%s, %s, 'running') RETURNING id",
        (job_name, company_id),
        one=True
    )
    run_id = run["id"]
    try:
        summary = fn()
        query(
            "UPDATE job_runs SET status='success', finished_at=now(), summary=%s WHERE id=%s",
            (json.dumps(summary or {}, default=str), run_id)
        )
        return {"id": run_id, "status": "success", "summary": summary}
    except Exception as e:
        err = traceback.format_exc()[-4000:]
        log.error("Job %s (%s) failed: %s", job_name, run_id, e)
        query(
            "UPDATE job_runs SET status='failed', finished_at=now(), error=%s WHERE id=%s",
            (err, run_id)
        )
        if raise_on_error:
            raise
        return {"id": run_id, "status": "failed", "error": err}
