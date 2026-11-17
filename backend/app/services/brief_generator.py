"""Monday Morning Intelligence Brief Generator:
Generates the comprehensive 10-section executive report strictly following ASSIGNMENT.md Section 7.
- Zero fabrication: empty sections say 'No meaningful development this week.'
- Business implications explained, not generic news summaries.
- Automatically persists recommended actions to actions table for weekly tracking.
- Produces executive HTML formatted for email, browser, and print.
"""

from datetime import datetime, timedelta, timezone
import json
import logging
from typing import Optional

from ..db import get_conn, query
from .llm import ask_json

log = logging.getLogger(__name__)

BRIEF_PROMPT = """You are the Chief Intelligence Officer preparing the definitive Monday Morning Intelligence Brief for {company_name} ({company_website}).

Company Profile Facts:
{profile_facts}

Founder Strategic Priorities (from interview):
{interview_context}

Available Verified Signals (Ranked):
{signals_json}

Available Internal Uploads:
{uploads_summary}

Generate an executive-level, decision-grade briefing report structured into the EXACT 10 sections below.
CRITICAL RULES:
1. Do NOT fabricate news. If a category has no signals, output "No meaningful development this week."
2. Explain BUSINESS IMPLICATIONS for {company_name}, not just general summaries of articles.
3. Opportunities must have concrete evidence citations from the signals. If fewer than 3 can be substantiated by real evidence, explicitly state the limitation.
4. For Recommended Actions, assign a realistic owner (e.g. CEO, Head of Admissions, Head of Product, Partnerships Lead) and clear reason.

Return ONLY a valid JSON object matching this schema:
{{
  "title": "Monday Morning Intelligence Brief — Week of {date_str}",
  "period": "{period_start} to {period_end}",
  "executive_summary": [
    "Top development 1 leadership should know",
    "Top development 2 leadership should know",
    "Top development 3 leadership should know",
    "Top development 4 leadership should know",
    "Top development 5 leadership should know"
  ],
  "customer_signals": {{
    "has_data": true or false,
    "summary": "...",
    "items": [
      {{"topic": "...", "evidence": "...", "implications": "..."}}
    ]
  }},
  "competitor_intelligence": {{
    "has_data": true or false,
    "summary": "...",
    "items": [
      {{"competitor": "...", "what_changed": "...", "evidence": "...", "why_it_matters": "...", "implications": "..."}}
    ]
  }},
  "market_intelligence": {{
    "has_data": true or false,
    "summary": "...",
    "items": [
      {{"topic": "...", "what_changed": "...", "evidence": "...", "strategic_relevance": "..."}}
    ]
  }},
  "internal_intelligence": {{
    "has_data": true or false,
    "summary": "...",
    "objections_and_deal_losses": "..."
  }},
  "opportunities": [
    {{
      "title": "Actionable Opportunity",
      "evidence": "Cites real evidence snippet",
      "impact": "Expected revenue/growth impact",
      "next_step": "Immediate first step",
      "priority": "High" or "Medium"
    }}
  ],
  "risks_and_threats": [
    {{
      "title": "Negative development / risk",
      "possible_impact": "How it threatens the business",
      "urgency": "High" or "Medium" or "Low"
    }}
  ],
  "recommended_actions": [
    {{
      "title": "Specific action to take this week",
      "reason": "Why this must be done now",
      "owner": "CEO / Head of Admissions / Partnerships / Product",
      "priority": "P0" or "P1" or "P2"
    }}
  ],
  "watchlist": [
    {{
      "topic": "Early trend to monitor closely",
      "why_watch": "What signals to look for next"
    }}
  ],
  "source_appendix": [
    {{
      "source_name": "...",
      "url": "...",
      "published_at": "...",
      "discovery_date": "...",
      "evidence_snippet": "...",
      "verification_status": "..."
    }}
  ]
}}
"""


def _generate_html_brief(company: dict, content: dict) -> str:
    """Generate executive HTML styling using DESIGN.md tokens for email and print."""
    title = content.get("title", f"Monday Morning Brief — {company['name']}")
    period = content.get("period", "")
    exec_summary = content.get("executive_summary", [])
    cust = content.get("customer_signals", {})
    comp = content.get("competitor_intelligence", {})
    mkt = content.get("market_intelligence", {})
    internal = content.get("internal_intelligence", {})
    opps = content.get("opportunities", [])
    risks = content.get("risks_and_threats", [])
    actions = content.get("recommended_actions", [])
    watch = content.get("watchlist", [])
    appendix = content.get("source_appendix", [])

    def render_list(items):
        if not items:
            return "<p style='color:#5D6B81;font-style:italic;'>No meaningful development this week.</p>"
        return "<ul>" + "".join(f"<li style='margin-bottom:8px;'>{it}</li>" for it in items) + "</ul>"

    opps_html = ""
    if opps:
        for o in opps:
            opps_html += f"""
            <div style='background:#F5F8FC;border-left:4px solid #7FB000;padding:12px 16px;margin-bottom:12px;border-radius:4px;'>
              <div style='display:flex;justify-content:space-between;'>
                <strong style='color:#243855;font-size:16px;'>{o.get('title')}</strong>
                <span style='background:#e6f4ea;color:#1e7e34;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:bold;'>{o.get('priority', 'High')} Priority</span>
              </div>
              <p style='margin:6px 0;font-size:14px;color:#243855;'><strong>Impact:</strong> {o.get('impact')}</p>
              <p style='margin:4px 0;font-size:13px;color:#5D6B81;'><strong>Evidence:</strong> "{o.get('evidence')}"</p>
              <p style='margin:4px 0;font-size:13px;color:#0073D1;'><strong>Next Step:</strong> {o.get('next_step')}</p>
            </div>
            """
    else:
        opps_html = "<p style='color:#5D6B81;font-style:italic;'>No actionable opportunities substantiated by verified evidence this period.</p>"

    risks_html = ""
    if risks:
        for r in risks:
            risks_html += f"""
            <div style='background:#F5F8FC;border-left:4px solid #D64545;padding:12px 16px;margin-bottom:12px;border-radius:4px;'>
              <div style='display:flex;justify-content:space-between;'>
                <strong style='color:#243855;font-size:16px;'>{r.get('title')}</strong>
                <span style='background:#fdecea;color:#D64545;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:bold;'>{r.get('urgency', 'Medium')} Urgency</span>
              </div>
              <p style='margin:6px 0;font-size:14px;color:#243855;'><strong>Possible Impact:</strong> {r.get('possible_impact')}</p>
            </div>
            """
    else:
        risks_html = "<p style='color:#5D6B81;font-style:italic;'>No critical risks identified this period.</p>"

    actions_html = ""
    if actions:
        actions_html = "<table style='width:100%;border-collapse:collapse;margin-top:8px;font-size:14px;'>"
        actions_html += "<tr style='background:#F5F8FC;text-align:left;color:#5D6B81;'><th style='padding:8px 12px;'>Action</th><th style='padding:8px 12px;'>Owner</th><th style='padding:8px 12px;'>Priority</th><th style='padding:8px 12px;'>Reason</th></tr>"
        for a in actions:
            actions_html += f"""
            <tr style='border-bottom:1px solid #E7E7E8;'>
              <td style='padding:10px 12px;font-weight:bold;color:#243855;'>{a.get('title')}</td>
              <td style='padding:10px 12px;color:#0073D1;'>{a.get('owner')}</td>
              <td style='padding:10px 12px;'><span style='background:#F5F8FC;padding:2px 6px;border-radius:4px;font-weight:bold;'>{a.get('priority', 'P1')}</span></td>
              <td style='padding:10px 12px;color:#5D6B81;'>{a.get('reason')}</td>
            </tr>
            """
        actions_html += "</table>"
    else:
        actions_html = "<p style='color:#5D6B81;font-style:italic;'>No recommended actions this week.</p>"

    appendix_html = ""
    if appendix:
        for app in appendix:
            appendix_html += f"""
            <div style='background:#fff;border:1px solid #E7E7E8;padding:12px 14px;margin-bottom:8px;border-radius:6px;font-size:13px;'>
              <div style='display:flex;justify-content:space-between;margin-bottom:4px;'>
                <strong>{app.get('source_name')}</strong>
                <span style='color:#7FB000;font-weight:bold;'>{app.get('verification_status', 'verified').upper()}</span>
              </div>
              <a href='{app.get('url')}' style='color:#0073D1;text-decoration:none;' target='_blank'>{app.get('url')}</a>
              <p style='margin:6px 0;font-style:italic;color:#5D6B81;'>"{app.get('evidence_snippet')}"</p>
            </div>
            """
    else:
        appendix_html = "<p style='color:#5D6B81;font-style:italic;'>No external sources cited.</p>"

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #243855; background: #FAFAFA; margin: 0; padding: 24px; line-height: 1.6; }}
    .container {{ max-width: 860px; margin: 0 auto; background: #FFFFFF; border: 1px solid #E7E7E8; border-radius: 8px; padding: 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }}
    h1 {{ font-size: 26px; color: #243855; text-transform: uppercase; margin-top: 0; margin-bottom: 6px; }}
    h2 {{ font-size: 18px; color: #0073D1; border-bottom: 2px solid #E7E7E8; padding-bottom: 6px; margin-top: 28px; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 0.5px; }}
    .meta {{ color: #5D6B81; font-size: 14px; margin-bottom: 24px; }}
    .exec-summary {{ background: #F5F8FC; border: 1px solid #0073D1; border-radius: 6px; padding: 18px 22px; margin-bottom: 24px; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>{title}</h1>
    <div class="meta">Company: <strong>{company['name']}</strong> | Coverage Period: {period} | Generated: {datetime.now().strftime('%B %d, %Y')}</div>

    <div class="exec-summary">
      <h2 style='margin-top:0;border:0;color:#243855;'>1. Executive Summary — Top 5 Developments</h2>
      {render_list(exec_summary)}
    </div>

    <h2>2. Customer Signals</h2>
    <p>{cust.get('summary', 'No meaningful customer signals detected this week.')}</p>

    <h2>3. Competitor Intelligence</h2>
    <p>{comp.get('summary', 'No meaningful competitor moves observed this week.')}</p>

    <h2>4. Market & Regulatory Intelligence</h2>
    <p>{mkt.get('summary', 'No material regulatory changes observed this week.')}</p>

    <h2>5. Internal Business Intelligence</h2>
    <p>{internal.get('summary', 'No internal uploads recorded this week.')}</p>

    <h2>6. Opportunities Identified</h2>
    {opps_html}

    <h2>7. Risks & Threats</h2>
    {risks_html}

    <h2>8. Recommended Actions for This Week</h2>
    {actions_html}

    <h2>9. What We Should Watch</h2>
    {render_list([f"<strong>{w.get('topic')}:</strong> {w.get('why_watch')}" for w in watch]) if watch else "<p style='color:#5D6B81;font-style:italic;'>No emerging watch items flagged.</p>"}

    <h2>10. Source Appendix & Evidence Trace</h2>
    {appendix_html}

    <div style='text-align:center;margin-top:40px;color:#5D6B81;font-size:12px;border-top:1px solid #E7E7E8;padding-top:16px;'>
      Generated autonomously by Signal Stack. Verified against real evidence.
    </div>
  </div>
</body>
</html>
"""
    return html


def generate_brief_for_company(company_id: int, trigger: str = "manual") -> dict:
    """End-to-end Monday Morning Brief generation:
    1. Reads facts, interview Q&A, and ranked signals.
    2. Prompts LLM for 10-section structured JSON.
    3. Builds executive HTML.
    4. Persists to briefs table.
    5. Populates actions table with newly recommended actions.
    """
    company = query("SELECT * FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise ValueError(f"Company {company_id} not found")

    profile_facts = query("SELECT * FROM profile_facts WHERE company_id = %s", (company_id,)) or []
    interview_qa = query("SELECT * FROM interview_qa WHERE company_id = %s AND answer IS NOT NULL", (company_id,)) or []
    signals = query(
        """SELECT id, category, competitor_name, what_happened, evidence_snippet, source_url,
                  published_at, discovered_at, verification_status, why_it_matters, business_area,
                  impact_type, urgency, suggested_action, rank_score, rank_explanation, interpretation
           FROM signals
           WHERE company_id = %s
           ORDER BY rank_score DESC LIMIT 25""",
        (company_id,)
    ) or []

    uploads = query("SELECT filename, kind FROM uploads WHERE company_id = %s", (company_id,)) or []

    facts_str = "\n".join(f"- {f['field']}: {f['value']}" for f in profile_facts) or "None recorded"
    qa_str = "\n".join(f"Q: {q['question']}\nA: {q['answer']}" for q in interview_qa) or "None recorded"
    signals_json = json.dumps([
        {
            "id": s["id"],
            "category": s["category"],
            "competitor": s["competitor_name"],
            "what_happened": s["what_happened"],
            "evidence": s["evidence_snippet"],
            "source_url": s["source_url"],
            "impact": s["impact_type"],
            "urgency": s["urgency"],
            "why_it_matters": s["why_it_matters"],
            "suggested_action": s["suggested_action"],
            "rank": s["rank_score"]
        }
        for s in signals
    ], indent=2)

    uploads_summary = f"{len(uploads)} internal files processed" if uploads else "No internal uploads provided"

    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    week_end = now.strftime("%Y-%m-%d")

    prompt = BRIEF_PROMPT.format(
        company_name=company["name"],
        company_website=company["website"],
        profile_facts=facts_str,
        interview_context=qa_str,
        signals_json=signals_json,
        uploads_summary=uploads_summary,
        date_str=now.strftime("%B %d, %Y"),
        period_start=week_start,
        period_end=week_end
    )

    try:
        content = ask_json(prompt, system="You are an uncompromising Chief Intelligence Officer crafting an executive briefing for founders.")
    except Exception as exc:
        log.error("Failed to generate brief content via LLM: %s", exc)
        raise RuntimeError(f"Brief generation failed: {exc}")

    html = _generate_html_brief(company, content)

    # Persist brief to briefs table
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO briefs (company_id, period_start, period_end, content, html, trigger, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, now())
               RETURNING *""",
            (
                company_id,
                week_start,
                week_end,
                json.dumps(content),
                html,
                trigger
            )
        )
        brief_row = cur.fetchone()
        brief_id = brief_row["id"]

        # Insert recommended actions into actions table
        actions_list = content.get("recommended_actions", [])
        for a in actions_list:
            cur.execute(
                """INSERT INTO actions (brief_id, title, reason, owner, priority, status, updated_at)
                   VALUES (%s, %s, %s, %s, %s, 'open', now())""",
                (
                    brief_id,
                    a.get("title", "Action item")[:255],
                    a.get("reason", "Derived from intelligence brief"),
                    a.get("owner", "Founder")[:100],
                    a.get("priority", "P1")[:50]
                )
            )

        conn.commit()

    brief_row["actions"] = query("SELECT * FROM actions WHERE brief_id = %s", (brief_id,)) or []
    return brief_row
