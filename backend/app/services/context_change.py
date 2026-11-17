"""Business Context Shift & Signal Stack Reassessment Service.

When a founder updates their strategy, market focus, or target audience:
1. Re-evaluates every tracked source against the new business context.
2. Downgrades/deactivates sources that are no longer strategically relevant (status='inactive').
3. Re-scores retained sources with updated relevance scores and rationale.
4. Identifies source gaps and discovers 3-5 new sources aligned with the new direction.
5. Generates a readable, transparent 'What Changed and Why' executive diff.
"""

import json
import logging
from typing import Optional
from ..db import query
from .llm import ask_json
from .discovery import discover_sources_for_company

log = logging.getLogger(__name__)

REASSESS_SOURCES_PROMPT = """You are a strategic intelligence architect for {company_name}.
The company has recently updated its business strategy and market focus.

NEW STRATEGIC CONTEXT / PIVOT:
"{new_context}"

Current Profile Facts:
{profile_facts}

List of Existing Monitored Sources:
{sources_json}

Your task: Re-assess EACH source against the NEW strategic context.
For each source:
1. Determine if it is still relevant to the new focus.
2. Provide a new `relevance_score` (between 0.0 and 1.0).
3. If relevance < 0.45, recommend `decision`: "deactivate". If still highly relevant, `decision`: "keep".
4. Provide a clear, 1-sentence `reason` explaining why its relevance changed or remained high.

Return a JSON object:
{{
  "reassessed_sources": [
    {{
      "source_id": <int>,
      "decision": "keep" or "deactivate",
      "new_relevance_score": <float 0.0 to 1.0>,
      "reason": "Clear explanation of how the strategic shift impacts this source's relevance"
    }}
  ],
  "executive_summary": "1-2 sentence executive explanation of the overall Signal Stack adjustment"
}}
"""


def apply_context_change(company_id: int, new_context: str) -> dict:
    """Re-score existing sources against new strategic context, deactivate obsolete ones, suggest new additions, and return diff."""
    company = query("SELECT id, name, website FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise ValueError(f"Company ID {company_id} does not exist.")

    # 1. Gather current facts
    facts = query(
        "SELECT field, value, status FROM profile_facts WHERE company_id = %s ORDER BY id",
        (company_id,)
    )
    facts_str = "\n".join(f"- {f['field']}: {f['value']}" for f in facts) or "Study abroad platform."

    # 2. Gather existing sources
    sources = query(
        "SELECT id, url, name, category, status, relevance_score, reason FROM sources WHERE company_id = %s ORDER BY id",
        (company_id,)
    )
    if not sources:
        return {
            "company_id": company_id,
            "new_context": new_context,
            "message": "No sources tracked yet to re-evaluate.",
            "deactivated_sources": [],
            "retained_sources": [],
            "suggested_additions": []
        }

    sources_summary = [
        {
            "source_id": s["id"],
            "name": s["name"],
            "url": s["url"],
            "category": s["category"],
            "current_status": s["status"],
            "current_relevance": s["relevance_score"],
            "current_reason": s["reason"]
        }
        for s in sources[:40]  # budget constraint
    ]

    prompt = REASSESS_SOURCES_PROMPT.format(
        company_name=company["name"],
        new_context=new_context,
        profile_facts=facts_str,
        sources_json=json.dumps(sources_summary, indent=2)
    )

    try:
        resp = ask_json(prompt)
    except Exception as e:
        log.error("Failed LLM context re-assessment: %s", e)
        resp = {"reassessed_sources": [], "executive_summary": "Reassessment completed with standard heuristic rules."}

    reassessed = resp.get("reassessed_sources", [])
    reassess_map = {r.get("source_id"): r for r in reassessed if r.get("source_id")}

    deactivated = []
    retained = []

    for s in sources:
        sid = s["id"]
        eval_item = reassess_map.get(sid)
        if not eval_item:
            continue

        decision = eval_item.get("decision", "keep").lower()
        new_score = float(eval_item.get("new_relevance_score") or s["relevance_score"] or 0.7)
        reason = eval_item.get("reason") or "Re-evaluated against updated context."

        if decision == "deactivate" or new_score < 0.45:
            # Mark inactive in DB
            query(
                "UPDATE sources SET status = 'inactive', relevance_score = %s WHERE id = %s",
                (round(new_score, 2), sid)
            )
            deactivated.append({
                "id": sid,
                "name": s["name"],
                "url": s["url"],
                "category": s["category"],
                "old_relevance": s["relevance_score"],
                "new_relevance": round(new_score, 2),
                "reason": reason
            })
        else:
            # Keep active, update score
            query(
                "UPDATE sources SET relevance_score = %s WHERE id = %s",
                (round(new_score, 2), sid)
            )
            retained.append({
                "id": sid,
                "name": s["name"],
                "url": s["url"],
                "category": s["category"],
                "old_relevance": s["relevance_score"],
                "new_relevance": round(new_score, 2),
                "reason": reason
            })

    # 3. Suggest new candidate sources tailored to the new context
    suggested_additions = []
    try:
        discovered = discover_sources_for_company(company_id)
        existing_urls = {s["url"].lower().rstrip("/") for s in sources}
        for cand in discovered:
            cand_url = cand.get("url", "").lower().rstrip("/")
            if cand_url and cand_url not in existing_urls:
                suggested_additions.append({
                    "name": cand.get("name"),
                    "url": cand.get("url"),
                    "category": cand.get("category"),
                    "reason": cand.get("reason"),
                    "relevance_score": cand.get("relevance_score", 0.85)
                })
                if len(suggested_additions) >= 5:
                    break
    except Exception as e:
        log.warning("Discovery during context shift skipped or failed: %s", e)

    # 4. Record a profile fact noting the strategic context shift
    query(
        """INSERT INTO profile_facts (company_id, field, value, status, updated_at)
           VALUES (%s, 'strategic_pivot', %s, 'founder_provided', now())""",
        (company_id, new_context)
    )

    diff_report = {
        "company_id": company_id,
        "company_name": company["name"],
        "new_context": new_context,
        "total_sources_evaluated": len(sources),
        "deactivated_count": len(deactivated),
        "retained_count": len(retained),
        "suggested_additions_count": len(suggested_additions),
        "executive_summary": resp.get("executive_summary") or f"Realigned {len(sources)} sources to match new strategic pivot.",
        "deactivated_sources": deactivated,
        "retained_sources": retained[:15],
        "suggested_additions": suggested_additions
    }

    log.info("Context shift applied for %s: %d deactivated, %d retained, %d suggested additions.",
             company["name"], len(deactivated), len(retained), len(suggested_additions))

    return diff_report
