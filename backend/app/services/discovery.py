"""Source discovery service: Generates search queries per company, searches DuckDuckGo,
scores with LLM, and persists to sources table as suggested.
NO hardcoded competitors or sources.
"""

import logging
import re
import urllib.parse
from typing import Optional
from ddgs import DDGS

from ..config import USER_AGENT
from ..db import query, get_conn
from .llm import ask_json

log = logging.getLogger(__name__)

DISCOVERY_STRATEGY_PROMPT = """You are a senior competitive intelligence strategist.
Analyze the following company profile and founder interview transcript:

Company Name: {name}
Company Website: {website}

Profile Facts:
{profile_facts}

Founder Interview Transcript:
{interview_qa}

Based solely on this specific business, industry, and target market, identify candidates for intelligence monitoring:
1. 8 to 10 actual direct competitors or substitute platforms in their space. For each, give the company name and a concise search term (2-3 words max, e.g. "Leap Scholar", "IDP Education") to find their homepage.
2. 6 to 8 customer hubs (discussion boards, Reddit subreddits, Quora spaces, review sites, student/parent portals) where customers discuss problems, complaints, and alternatives. (Use concise 2-3 word search terms, e.g. "Reddit studyabroad", "Shiksha reviews", "Pagalguy forum").
3. 6 to 8 market/regulatory/policy sources (government policy portals, visa agencies, industry associations, specialized trade journals) that govern or report on their space. (Use concise search terms, e.g. "UK student visa", "India student visa news", "PIE News international education").

Return ONLY a JSON object:
{{
  "competitors": [
    {{"name": "Competitor Name", "search_term": "concise query (2-3 words)", "monitoring_focus": "what to watch e.g. pricing, partnerships, agent commissions"}}
  ],
  "customer_sources": [
    {{"name": "Community / Platform Name", "search_term": "concise query", "monitoring_focus": "what customer complaints or needs to watch"}}
  ],
  "market_sources": [
    {{"name": "Regulator / Media Name", "search_term": "concise query", "monitoring_focus": "what policy or industry trends to watch"}}
  ]
}}
"""

SCORING_PROMPT = """You are a business intelligence analyst evaluating potential intelligence sources for {company_name} ({industry}).

Sources to evaluate:
{sources_json}

For each source, provide:
1. "source_reliability": float between 0.1 and 1.0 (official regulator: 0.9-1.0; major news publication: 0.8-0.9; company website: 0.7-0.85; community forum/Reddit: 0.5-0.7; user review: 0.4-0.6)
2. "relevance_score": float between 0.1 and 1.0 (how directly it impacts {company_name}'s daily operations and strategy)
3. "reason": a clear, 1-2 sentence executive explanation of WHY this specific source is being monitored and what strategic intelligence it provides.

Return ONLY a JSON array of objects with keys: ["url", "source_reliability", "relevance_score", "reason"].
"""


def _clean_search_url(raw_url: str) -> Optional[str]:
    """Extract clean, unquoted URL if it's a redirect or ad link."""
    if not raw_url:
        return None

    # First unquote if URL-encoded
    raw_url = urllib.parse.unquote(raw_url)

    # Unpack Bing/DuckDuckGo redirects if present
    parsed = urllib.parse.urlparse(raw_url)
    if "bing.com" in parsed.netloc and "u=" in parsed.query:
        params = urllib.parse.parse_qs(parsed.query)
        if "u" in params:
            import base64
            encoded = params["u"][0]
            try:
                padded = encoded + "=" * ((4 - len(encoded) % 4) % 4)
                decoded = base64.b64decode(padded).decode("utf-8", errors="ignore")
                if decoded.startswith("http"):
                    return decoded.split("&")[0].split("?utm_")[0]
            except Exception:
                pass

    if raw_url.startswith("http://") or raw_url.startswith("https://"):
        # Strip tracking query params for cleaner URLs
        clean = raw_url.split("?utm_")[0].split("&utm_")[0]
        return clean

    return None


def _find_url_for_query(query_text: str, is_news: bool = False) -> Optional[tuple[str, str]]:
    """Search DuckDuckGo to discover the top relevant URL and title with graceful retry."""
    ddgs = DDGS()
    queries_to_try = [query_text]

    # If query is long, try first 3 words as fallback
    words = query_text.strip().split()
    if len(words) > 3:
        queries_to_try.append(" ".join(words[:3]))

    for q in queries_to_try:
        try:
            if is_news:
                results = list(ddgs.news(q, max_results=3))
                if results:
                    r = results[0]
                    url = _clean_search_url(r.get("url") or r.get("href"))
                    title = r.get("title") or q
                    if url:
                        return url, title

            results = list(ddgs.text(q, max_results=3))
            if results:
                r = results[0]
                url = _clean_search_url(r.get("href") or r.get("url"))
                title = r.get("title") or q
                if url:
                    return url, title
        except Exception as e:
            log.warning("DuckDuckGo search error for '%s': %s", q, e)
            continue

    return None


def discover_sources_for_company(company_id: int) -> list[dict]:
    """Run full source discovery pipeline for a company."""
    company = query("SELECT * FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise ValueError(f"Company {company_id} not found")

    profile_facts = query("SELECT * FROM profile_facts WHERE company_id = %s", (company_id,)) or []
    interview_qa = query("SELECT * FROM interview_qa WHERE company_id = %s ORDER BY seq ASC", (company_id,)) or []

    facts_text = "\n".join(f"- {f['field']}: {f['value']}" for f in profile_facts) or "None recorded"
    qa_text = "\n".join(f"Q{q['seq']}: {q['question']}\nA: {q['answer'] or 'Skipped'}" for q in interview_qa) or "None recorded"

    # Step 1: LLM generates candidate search terms
    strategy = ask_json(
        DISCOVERY_STRATEGY_PROMPT.format(
            name=company["name"],
            website=company["website"],
            profile_facts=facts_text,
            interview_qa=qa_text
        ),
        system="You are an expert market intelligence architect."
    )

    candidates: list[dict] = []
    seen_urls: set[str] = set()

    # Step 2: Search verification via DDGS for Competitors
    for comp in strategy.get("competitors", []):
        search_q = comp.get("search_term") or comp["name"]
        res = _find_url_for_query(search_q)
        if res:
            url, title = res
            if url not in seen_urls and company["website"] not in url:
                seen_urls.add(url)
                candidates.append({
                    "category": "competitors",
                    "name": comp.get("name") or title,
                    "url": url,
                    "competitor_name": comp.get("name"),
                    "monitoring_focus": comp.get("monitoring_focus", "Competitor product and pricing changes")
                })

    # Search verification for Customer Sources
    for cust in strategy.get("customer_sources", []):
        search_q = cust.get("search_term") or cust["name"]
        res = _find_url_for_query(search_q)
        if res:
            url, title = res
            if url not in seen_urls:
                seen_urls.add(url)
                candidates.append({
                    "category": "customers",
                    "name": cust.get("name") or title,
                    "url": url,
                    "competitor_name": None,
                    "monitoring_focus": cust.get("monitoring_focus", "Customer pain points and sentiment")
                })

    # Search verification for Market Sources
    for mkt in strategy.get("market_sources", []):
        search_q = mkt.get("search_term") or mkt["name"]
        res = _find_url_for_query(search_q, is_news=True) or _find_url_for_query(search_q)
        if res:
            url, title = res
            if url not in seen_urls:
                seen_urls.add(url)
                candidates.append({
                    "category": "market",
                    "name": mkt.get("name") or title,
                    "url": url,
                    "competitor_name": None,
                    "monitoring_focus": mkt.get("monitoring_focus", "Regulatory and market developments")
                })

    if not candidates:
        log.warning("No live candidates found via search.")
        return []

    # Step 3: LLM scores and generates concrete business justification
    import json
    sources_payload = json.dumps([
        {"url": c["url"], "name": c["name"], "category": c["category"], "focus": c["monitoring_focus"]}
        for c in candidates
    ], indent=2)

    industry_fact = next((f["value"] for f in profile_facts if f["field"] == "industry"), "general")
    try:
        scored_list = ask_json(
            SCORING_PROMPT.format(
                company_name=company["name"],
                industry=industry_fact,
                sources_json=sources_payload
            )
        )
    except Exception as e:
        log.warning("Scoring failed: %s, using sensible defaults", e)
        scored_list = []

    score_map = {item.get("url"): item for item in scored_list if isinstance(item, dict) and item.get("url")}

    # Step 4: Persist into database
    saved_sources: list[dict] = []
    with get_conn() as conn, conn.cursor() as cur:
        # Add Internal Intelligence source if not already present
        cur.execute(
            """INSERT INTO sources (company_id, category, name, url, reason, status, source_reliability, relevance_score)
               VALUES (%s, 'internal', 'Internal Document & Deal Uploads', 'internal://uploads',
                       'Continuous parsing of uploaded CRM deal logs, sales call transcripts, and customer objection notes.',
                       'approved', 0.95, 0.95)
               ON CONFLICT (company_id, url) DO NOTHING
               RETURNING *""",
            (company_id,)
        )
        internal_row = cur.fetchone()
        if internal_row:
            saved_sources.append(internal_row)

        for c in candidates:
            scoring = score_map.get(c["url"], {})
            reason = scoring.get("reason") or f"Monitors {c['category']} developments: {c['monitoring_focus']}."
            rel = float(scoring.get("source_reliability", 0.75))
            relevance = float(scoring.get("relevance_score", 0.80))

            cur.execute(
                """INSERT INTO sources (
                     company_id, category, name, url, reason, status,
                     competitor_name, source_reliability, relevance_score
                   ) VALUES (%s, %s, %s, %s, %s, 'suggested', %s, %s, %s)
                   ON CONFLICT (company_id, url) DO UPDATE
                   SET reason = EXCLUDED.reason,
                       source_reliability = EXCLUDED.source_reliability,
                       relevance_score = EXCLUDED.relevance_score
                   RETURNING *""",
                (
                    company_id,
                    c["category"],
                    c["name"][:120],
                    c["url"],
                    reason,
                    c["competitor_name"],
                    rel,
                    relevance
                )
            )
            row = cur.fetchone()
            if row:
                saved_sources.append(row)

        conn.commit()

    return saved_sources
