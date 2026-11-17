"""Company setup, profile, and site research endpoints."""

import logging
from typing import Optional
from urllib.parse import urljoin

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..db import get_conn, query
from ..services.crawler import fetch
from ..services.llm import ask_json

router = APIRouter(prefix="/api/companies", tags=["companies"])
log = logging.getLogger(__name__)

# ── Pydantic schemas ────────────────────────────────────────────────

class CompanyCreate(BaseModel):
    name: str
    website: str


class ProfileFactUpdate(BaseModel):
    fact_id: int
    value: Optional[str] = None
    status: Optional[str] = None


class ContextChangeRequest(BaseModel):
    new_context: str


# ── Helpers ──────────────────────────────────────────────────────────

SUBPAGES = ["/about", "/products", "/services", "/pricing", "/team"]


def _crawl_site(website: str) -> tuple[str, list[dict]]:
    """Crawl the homepage + common subpages, return (combined_text, page_results)."""
    pages: list[dict] = []

    # Ensure base URL has a trailing slash for urljoin
    base = website if website.endswith("/") else website + "/"

    # Always try homepage first
    urls_to_try = [website] + [urljoin(base, p.lstrip("/")) for p in SUBPAGES]

    for url in urls_to_try:
        try:
            result = fetch(url)
            pages.append({"url": url, "ok": result["ok"], "text": result.get("text", "")})
        except Exception as exc:
            log.warning("Failed to crawl %s: %s", url, exc)
            pages.append({"url": url, "ok": False, "text": ""})

    combined = "\n\n".join(p["text"] for p in pages if p["ok"] and p["text"])
    return combined, pages


EXTRACTION_PROMPT = """You are a business analyst. Given the following text scraped from a company's website,
extract as many factual profile fields as you can. Return a JSON array of objects.

Each object MUST have:
- "field": one of: industry, products_services, target_customers, business_model,
  pricing_model, company_size, founding_year, headquarters, key_differentiators,
  market_position, value_proposition, technology_used, revenue_model
- "value": the extracted fact (string)
- "status": "verified" if you found direct evidence on the page, "assumed" if inferred
- "evidence_url": the URL where you found the evidence, or null if assumed

Only include fields where you found meaningful information. Do NOT fabricate or guess values
that have no basis in the provided text. If you cannot determine a field, omit it entirely.

Company name: {name}
Company website: {website}

--- SCRAPED TEXT ---
{text}
"""


def _extract_facts(
    company_name: str, website: str, text: str, pages: list[dict]
) -> list[dict]:
    """Ask LLM to extract profile facts from crawled text."""
    if not text.strip():
        return []

    # Build a URL lookup so the LLM has real evidence URLs
    evidence_urls = [p["url"] for p in pages if p["ok"] and p["text"]]

    prompt = EXTRACTION_PROMPT.format(name=company_name, website=website, text=text[:15000])
    prompt += f"\n\nAvailable evidence URLs: {evidence_urls}"

    try:
        facts: list[dict] = ask_json(prompt)
    except Exception as exc:
        log.error("LLM extraction failed: %s", exc)
        return []

    if not isinstance(facts, list):
        log.error("LLM returned non-list: %s", type(facts))
        return []

    return facts


# ── Routes ───────────────────────────────────────────────────────────

@router.post("", status_code=201)
def create_company(body: CompanyCreate) -> dict:
    """Create a new company."""
    row = query(
        "INSERT INTO companies (name, website) VALUES (%s, %s) RETURNING *",
        (body.name, body.website),
        one=True,
    )
    return row


@router.get("")
def list_companies() -> list[dict]:
    """List all companies."""
    return query("SELECT * FROM companies ORDER BY created_at DESC")


@router.get("/{company_id}")
def get_company(company_id: int) -> dict:
    """Get a single company with its profile facts."""
    company = query("SELECT * FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, "Company not found")
    facts = query(
        "SELECT * FROM profile_facts WHERE company_id = %s ORDER BY id",
        (company_id,),
    )
    company["profile_facts"] = facts
    return company


@router.get("/{company_id}/profile")
def get_profile(company_id: int) -> list[dict]:
    """Get profile facts for a company."""
    company = query("SELECT id FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, "Company not found")
    return query(
        "SELECT * FROM profile_facts WHERE company_id = %s ORDER BY id",
        (company_id,),
    )


@router.patch("/{company_id}/profile")
def update_profile_fact(company_id: int, body: ProfileFactUpdate) -> dict:
    """Update a profile fact's value and/or status."""
    existing = query(
        "SELECT * FROM profile_facts WHERE id = %s AND company_id = %s",
        (body.fact_id, company_id),
        one=True,
    )
    if not existing:
        raise HTTPException(404, "Profile fact not found")

    new_value = body.value if body.value is not None else existing["value"]
    new_status = body.status if body.status is not None else existing["status"]

    if new_status not in ("verified", "assumed", "founder_provided"):
        raise HTTPException(400, f"Invalid status: {new_status}")

    row = query(
        """UPDATE profile_facts
           SET value = %s, status = %s, updated_at = now()
           WHERE id = %s RETURNING *""",
        (new_value, new_status, body.fact_id),
        one=True,
    )
    return row


@router.post("/{company_id}/research")
def research_company(company_id: int) -> list[dict]:
    """Crawl company site + extract profile facts via LLM."""
    company = query(
        "SELECT * FROM companies WHERE id = %s", (company_id,), one=True
    )
    if not company:
        raise HTTPException(404, "Company not found")

    # 1. Crawl
    combined_text, page_results = _crawl_site(company["website"])

    if not combined_text.strip():
        raise HTTPException(
            422,
            "Could not extract any text from the company website. "
            "All pages either failed to load or returned no content.",
        )

    # 2. LLM extraction
    facts = _extract_facts(
        company["name"], company["website"], combined_text, page_results
    )

    if not facts:
        return []

    # 3. Persist facts
    saved: list[dict] = []
    with get_conn() as conn, conn.cursor() as cur:
        for f in facts:
            field = f.get("field", "")
            value = f.get("value", "")
            status = f.get("status", "assumed")
            evidence_url = f.get("evidence_url")

            if not field or not value:
                continue

            if status not in ("verified", "assumed"):
                status = "assumed"

            try:
                cur.execute("SAVEPOINT fact_insert")
                cur.execute(
                    """INSERT INTO profile_facts (company_id, field, value, status, evidence_url)
                       VALUES (%s, %s, %s, %s, %s) RETURNING *""",
                    (company_id, field, value, status, evidence_url),
                )
                row = cur.fetchone()
                if row:
                    saved.append(row)
                cur.execute("RELEASE SAVEPOINT fact_insert")
            except Exception as exc:
                log.warning("Failed to insert fact %s: %s", field, exc)
                cur.execute("ROLLBACK TO SAVEPOINT fact_insert")

        conn.commit()

    return saved


@router.post("/{company_id}/context-change")
def trigger_context_change(company_id: int, body: ContextChangeRequest) -> dict:
    """Re-score Signal Stack against a strategic context shift, deactivate irrelevant sources, and suggest additions."""
    company = query("SELECT id FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, "Company not found")

    if not body.new_context or len(body.new_context.strip()) < 10:
        raise HTTPException(400, "Please provide a detailed context statement (at least 10 characters).")

    try:
        from ..services.context_change import apply_context_change
        return apply_context_change(company_id, body.new_context.strip())
    except Exception as e:
        log.error("Failed to execute context change: %s", e)
        raise HTTPException(500, f"Context reassessment failed: {str(e)}")
