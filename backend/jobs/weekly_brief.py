"""Weekly Brief Scheduled Job.

Pipeline:
1) Crawl all approved sources for the company (polite delay, robots.txt, sha256 deduplication).
2) Detect new documents and unanalyzed documents -> LLM analysis into signals.
3) Multi-factor ranking (relevance, impact, urgency, credibility, recency, novelty).
4) Generate full 10-section Monday Morning Intelligence Brief (with anti-fabrication).
5) Save brief + extract Action Items to 'actions' table.
6) Send email if recipient configured in company settings.
7) Record complete execution details in 'job_runs'.
"""

import argparse
import logging
import os
import sys
try:
    from .runner import run_logged
    from backend.app.db import query
    from backend.app.services.crawler import crawl_source
    from backend.app.services.analysis import analyze_document
    from backend.app.services.brief_generator import generate_brief_for_company
    from backend.app.services.email import send_brief
except (ImportError, ModuleNotFoundError, ValueError):
    from runner import run_logged
    from app.db import query
    from app.services.crawler import crawl_source
    from app.services.analysis import analyze_document
    from app.services.brief_generator import generate_brief_for_company
    from app.services.email import send_brief

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("weekly_brief_job")


def generate_for_company(company_id: int) -> dict:
    company = query("SELECT id, name, settings FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise ValueError(f"Company ID {company_id} does not exist.")

    settings = company.get("settings") or {}
    log.info("Starting weekly brief pipeline for %s (ID %s)...", company["name"], company_id)

    # 1. Crawl all approved sources
    approved_sources = query(
        "SELECT id, url, name, category FROM sources WHERE company_id = %s AND status = 'approved'",
        (company_id,)
    )
    total_new_docs = 0
    crawl_errors = 0

    log.info("Crawling %d approved sources...", len(approved_sources))
    for src in approved_sources:
        try:
            res = crawl_source(src["id"])
            total_new_docs += res.get("new_docs", 0)
        except Exception as e:
            crawl_errors += 1
            log.warning("Failed crawling source %s (%s): %s", src["id"], src["url"], e)

    # 2. Analyze unanalyzed documents for this company
    unanalyzed = query(
        """SELECT d.id
           FROM documents d
           JOIN sources s ON s.id = d.source_id
           LEFT JOIN signals sig ON sig.document_id = d.id
           WHERE s.company_id = %s AND sig.id IS NULL
           ORDER BY d.discovered_at DESC
           LIMIT 25""",
        (company_id,)
    )
    log.info("Found %d unanalyzed documents to process into signals...", len(unanalyzed))
    total_signals = 0
    analysis_errors = 0

    for doc in unanalyzed:
        try:
            sig = analyze_document(doc["id"])
            if sig:
                total_signals += 1
        except Exception as e:
            analysis_errors += 1
            log.warning("Failed analyzing document %s: %s", doc["id"], e)

    # 3. Generate 10-section brief
    log.info("Generating Monday Morning Intelligence Brief...")
    brief_res = generate_brief_for_company(company_id, trigger="scheduled")

    # 4. Email delivery if enabled
    email_sent = False
    recipient = settings.get("recipient_email")
    email_enabled = settings.get("email_notifications", False) or settings.get("email_delivery", False)

    if email_enabled and recipient and os.getenv("GMAIL_USER") and os.getenv("GMAIL_APP_PASSWORD"):
        subject = f"Monday Morning Intelligence Brief: {company['name']} ({brief_res.get('period_start')} to {brief_res.get('period_end')})"
        try:
            send_brief(recipient, subject, brief_res["html"])
            email_sent = True
            log.info("Brief emailed successfully to %s", recipient)
        except Exception as e:
            log.error("Failed to email brief to %s: %s", recipient, e)

    return {
        "company_id": company_id,
        "company_name": company["name"],
        "sources_crawled": len(approved_sources),
        "crawl_errors": crawl_errors,
        "new_documents_crawled": total_new_docs,
        "unanalyzed_docs_processed": len(unanalyzed),
        "signals_created": total_signals,
        "analysis_errors": analysis_errors,
        "brief_id": brief_res.get("id") or brief_res.get("brief_id"),
        "period_start": str(brief_res.get("period_start")) if brief_res.get("period_start") else None,
        "period_end": str(brief_res.get("period_end")) if brief_res.get("period_end") else None,
        "email_sent": email_sent,
        "recipient": recipient if email_sent else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Signal Stack Weekly Brief Job")
    parser.add_argument("--company", "-c", type=int, help="Optional company ID to run for")
    args = parser.parse_args()

    if args.company:
        companies = [{"id": args.company}]
    else:
        companies = query("SELECT id FROM companies ORDER BY id")

    if not companies:
        log.info("No companies found in database.")
        return

    for c in companies:
        cid = c["id"]
        log.info("Running weekly brief job for company %s", cid)
        run_logged("weekly_brief", lambda target_id=cid: generate_for_company(target_id), company_id=cid)


if __name__ == "__main__":
    main()
