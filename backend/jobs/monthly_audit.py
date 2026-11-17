"""Monthly Signal Stack Audit Job.

Audits every source in a company's Signal Stack:
1) Dead URLs: HTTP HEAD/GET health check with timeout (flags 404, 410, DNS/network failures as 'dead').
2) Duplicate detection: Identifies duplicate domains or identical URLs.
3) Inactive sources: Sources with no documents gathered in 60+ days (or aged > 30 days with 0 docs).
4) Declining relevance: Sources with relevance_score < 0.50.
5) Discovery Diff: Re-scans for new competitor/market candidates not currently tracked.
6) Health Score: Quantifies overall signal health (0-100).
7) Stores comprehensive audit report in 'audit_reports' table and logs execution to 'job_runs'.
"""

import argparse
from datetime import datetime, timezone
import logging
from urllib.parse import urlparse
import requests
try:
    from .runner import run_logged
    from backend.app.db import query
    from backend.app.services.discovery import discover_sources_for_company
except (ImportError, ModuleNotFoundError, ValueError):
    from runner import run_logged
    from app.db import query
    from app.services.discovery import discover_sources_for_company

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("monthly_audit_job")

USER_AGENT = "SignalStackBot/1.0 (+https://github.com/signalstack; polite audit crawler)"


def _check_url_health(url: str) -> tuple[int, str]:
    """Test URL reachability via HEAD (fallback GET). Returns (status_code, error_message)."""
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        if resp.status_code in (405, 501):  # Method not allowed for HEAD, try fast GET
            resp = requests.get(url, headers=headers, timeout=10, stream=True)
        return resp.status_code, ""
    except requests.exceptions.RequestException as e:
        return 0, str(e)


def audit_company(company_id: int) -> dict:
    company = query("SELECT id, name, website FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise ValueError(f"Company ID {company_id} does not exist.")

    log.info("Starting monthly audit for %s (ID %s)...", company["name"], company_id)

    sources = query(
        "SELECT id, url, name, category, status, relevance_score, source_reliability, discovered_at FROM sources WHERE company_id = %s ORDER BY id",
        (company_id,)
    )
    total_sources = len(sources)
    log.info("Auditing %d sources for %s...", total_sources, company["name"])

    dead_sources = []
    duplicate_sources = []
    inactive_sources = []
    low_relevance_sources = []
    domain_map = {}

    for s in sources:
        url = s["url"]
        sid = s["id"]
        parsed = urlparse(url)
        domain = (parsed.netloc or "").lower().replace("www.", "")

        # 1. Duplicate Domain / URL check
        if domain in domain_map:
            duplicate_sources.append({
                "source_id": sid,
                "name": s["name"] or url,
                "url": url,
                "domain": domain,
                "conflicts_with_id": domain_map[domain]["id"],
                "category": s["category"]
            })
        else:
            domain_map[domain] = s

        # 2. Dead URL check
        status_code, err = _check_url_health(url)
        if status_code in (404, 410) or (status_code == 0 and err):
            # Mark dead in sources table
            query(
                "UPDATE sources SET status = 'dead', last_status_code = %s, last_checked = now() WHERE id = %s",
                (status_code if status_code != 0 else 0, sid)
            )
            dead_sources.append({
                "source_id": sid,
                "name": s["name"] or url,
                "url": url,
                "status_code": status_code,
                "error": err or f"HTTP {status_code} Not Found/Gone"
            })
        else:
            query(
                "UPDATE sources SET last_status_code = %s, last_checked = now() WHERE id = %s",
                (status_code, sid)
            )

        # 3. Inactive source check (no docs in 60 days)
        doc_stat = query(
            "SELECT max(discovered_at) as last_doc, count(*) as count FROM documents WHERE source_id = %s",
            (sid,),
            one=True
        )
        last_doc_time = doc_stat["last_doc"] if doc_stat else None
        doc_count = doc_stat["count"] if doc_stat else 0

        # Check if no documents or older than 60 days
        now = datetime.now(timezone.utc)
        is_inactive = False
        if last_doc_time:
            days_since_doc = (now - last_doc_time).days
            if days_since_doc >= 60:
                is_inactive = True
        elif s["discovered_at"]:
            days_since_discovery = (now - s["discovered_at"]).days
            if days_since_discovery >= 30 and doc_count == 0:
                is_inactive = True

        if is_inactive:
            inactive_sources.append({
                "source_id": sid,
                "name": s["name"] or url,
                "url": url,
                "last_document_date": last_doc_time.isoformat() if last_doc_time else None,
                "total_documents": doc_count,
            })

        # 4. Low relevance check
        if s["relevance_score"] is not None and s["relevance_score"] < 0.50:
            low_relevance_sources.append({
                "source_id": sid,
                "name": s["name"] or url,
                "url": url,
                "relevance_score": s["relevance_score"],
                "reason": "Relevance score is below 0.50 threshold."
            })

    # 5. Discovery diff / recommended additions
    recommended_additions = []
    try:
        log.info("Running discovery diff to find new candidate sources...")
        discovered = discover_sources_for_company(company_id)
        existing_urls = {s["url"].lower().rstrip("/") for s in sources}
        for cand in discovered:
            cand_url = cand.get("url", "").lower().rstrip("/")
            if cand_url and cand_url not in existing_urls:
                recommended_additions.append({
                    "name": cand.get("name"),
                    "url": cand.get("url"),
                    "category": cand.get("category"),
                    "reason": cand.get("reason"),
                    "relevance_score": cand.get("relevance_score", 0.7),
                    "source_reliability": cand.get("source_reliability", 0.7),
                })
                if len(recommended_additions) >= 5:
                    break
    except Exception as e:
        log.warning("Discovery diff skipped or encountered error: %s", e)

    # 6. Health Score (0-100)
    active_count = len([s for s in sources if s.get("status") in ("approved", "suggested") and s["id"] not in [d["source_id"] for d in dead_sources]])
    penalties = (len(dead_sources) * 15) + (len(duplicate_sources) * 5) + (len(inactive_sources) * 10) + (len(low_relevance_sources) * 5)
    base_score = 100 - penalties
    if total_sources == 0:
        health_score = 50
    else:
        health_score = max(10, min(100, base_score))

    report_content = {
        "audit_date": datetime.now(timezone.utc).isoformat(),
        "company_id": company_id,
        "company_name": company["name"],
        "total_sources_audited": total_sources,
        "active_sources_count": active_count,
        "health_score": health_score,
        "summary": (
            f"Signal Stack Audit for {company['name']}: {total_sources} sources audited. "
            f"{len(dead_sources)} dead URLs, {len(duplicate_sources)} duplicate domains, "
            f"{len(inactive_sources)} inactive sources, {len(recommended_additions)} new candidate sources recommended. "
            f"Stack Health Score: {health_score}/100."
        ),
        "dead_sources": dead_sources,
        "duplicate_sources": duplicate_sources,
        "inactive_sources": inactive_sources,
        "low_relevance_sources": low_relevance_sources,
        "recommended_additions": recommended_additions,
    }

    # Save to audit_reports
    report_row = query(
        "INSERT INTO audit_reports (company_id, content) VALUES (%s, %s) RETURNING id, created_at",
        (company_id, requests.compat.json.dumps(report_content)),
        one=True
    )

    log.info("Audit completed. Report ID: %s, Health Score: %d/100", report_row["id"], health_score)

    return {
        "company_id": company_id,
        "company_name": company["name"],
        "audit_report_id": report_row["id"],
        "health_score": health_score,
        "total_sources_audited": total_sources,
        "dead_count": len(dead_sources),
        "duplicate_count": len(duplicate_sources),
        "inactive_count": len(inactive_sources),
        "low_relevance_count": len(low_relevance_sources),
        "recommended_additions_count": len(recommended_additions),
    }


def main():
    parser = argparse.ArgumentParser(description="Signal Stack Monthly Audit Job")
    parser.add_argument("--company", "-c", type=int, help="Optional company ID to audit")
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
        log.info("Running monthly audit job for company %s", cid)
        run_logged("monthly_audit", lambda target_id=cid: audit_company(target_id), company_id=cid)


if __name__ == "__main__":
    main()
