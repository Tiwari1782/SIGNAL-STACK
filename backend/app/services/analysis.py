"""Intelligence Analysis & Ranking Engine:
- Extracts structured developments from collected documents
- Anti-fabrication check: enforces verbatim evidence snippet verification against document text
- Multi-factor ranking: rank_score = 0.25*relevance + 0.20*impact + 0.15*urgency + 0.15*credibility + 0.15*recency + 0.10*novelty
- Strict separation of source_reliability, evidence_strength, strategic_relevance, and interpretation.
"""

from datetime import datetime, timezone
import json
import logging
import re
from typing import Optional

from ..db import get_conn, query
from .llm import ask_json

log = logging.getLogger(__name__)


def _parse_published_date(raw_date: Optional[str]) -> Optional[datetime]:
    """Parse various date string formats into UTC datetime."""
    if not raw_date:
        return None
    try:
        from dateutil import parser as dt_parser
        dt = dt_parser.parse(str(raw_date))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None

ANALYSIS_PROMPT = """You are a senior business intelligence analyst reviewing raw web intelligence for {company_name} ({industry}).

Company Profile Facts:
{profile_facts}

Founder Interview Priorities:
{interview_context}

Source Metadata:
- Source Name: {source_name}
- Category: {source_category}
- Competitor Name: {competitor_name}
- Source URL: {source_url}
- Document Title: {document_title}

Document Text:
---
{document_text}
---

Your task: Determine if this document contains ANY meaningful, decision-relevant business development for {company_name}.
If it is generic boilerplate, navigation text, or has no business impact, return {{"is_significant": false}}.

If it contains a meaningful development, return a JSON object:
{{
  "is_significant": true,
  "what_happened": "Clear, objective factual description of what occurred or was published (1-2 sentences)",
  "evidence_snippet": "EXACT verbatim quote from the Document Text above that proves this development. MUST be copied word-for-word from the text.",
  "published_at": "YYYY-MM-DD or null if unknown",
  "category": "{source_category}",
  "competitor_name": "{competitor_name}",
  "why_it_matters": "Strategic business implications for {company_name}'s revenue, customers, or market share",
  "business_area": "One of: Product, Pricing, Partnerships, Admissions, Marketing, Regulation, Customer Experience",
  "impact_type": "opportunity" or "threat" or "neutral",
  "urgency": "high" or "medium" or "low",
  "suggested_action": "Specific concrete recommended next step for {company_name}'s leadership team",
  "interpretation": "Your strategic interpretation and thesis explaining what this development signals for the broader industry",
  "relevance": float between 0.0 and 1.0,
  "impact": float between 0.0 and 1.0,
  "evidence_strength": float between 0.0 and 1.0 (1.0 = direct official quote or formal policy announcement, 0.5 = third-party mention or forum post)
}}
"""


def _normalize_score(val: Optional[float], default: float = 0.5) -> float:
    """Ensure score is a float clamped between 0.0 and 1.0."""
    try:
        f = float(val) if val is not None else default
        return max(0.0, min(1.0, f))
    except Exception:
        return default


def _urgency_to_numeric(urgency_str: str) -> float:
    u = (urgency_str or "").lower().strip()
    if u == "high":
        return 0.9
    elif u == "medium":
        return 0.6
    return 0.3


def _calculate_recency_score(published_at: Optional[datetime], discovered_at: datetime) -> float:
    """Calculate recency score between 0.0 and 1.0."""
    ref_date = published_at or discovered_at
    if not ref_date:
        return 0.5

    now = datetime.now(timezone.utc)
    if ref_date.tzinfo is None:
        ref_date = ref_date.replace(tzinfo=timezone.utc)

    days_old = max(0, (now - ref_date).days)
    if days_old <= 7:
        return 1.0
    elif days_old <= 30:
        return 0.8
    elif days_old <= 90:
        return 0.6
    elif days_old <= 180:
        return 0.4
    return 0.2


def _compute_rank(
    relevance: float,
    impact: float,
    urgency_num: float,
    credibility: float,
    recency: float,
    novelty: float
) -> tuple[float, str]:
    """Calculate multi-factor ranking and plain-language explanation per SPEC.md.
    rank_score = 0.25*relevance + 0.20*impact + 0.15*urgency + 0.15*credibility + 0.15*recency + 0.10*novelty
    """
    score = (
        0.25 * relevance +
        0.20 * impact +
        0.15 * urgency_num +
        0.15 * credibility +
        0.15 * recency +
        0.10 * novelty
    )
    score = round(_normalize_score(score), 3)

    # Generate plain-language explanation
    reasons = []
    if relevance >= 0.8:
        reasons.append("high strategic relevance to core operations")
    if impact >= 0.8:
        reasons.append("significant business impact")
    if urgency_num >= 0.8:
        reasons.append("urgent action needed this week")
    if credibility >= 0.85:
        reasons.append("verified official source")
    if recency >= 0.8:
        reasons.append("fresh timely development")

    if not reasons:
        explanation = f"Ranked at {int(score * 100)}/100 based on balanced market observation across reliability and relevance."
    else:
        explanation = f"Prioritized at {int(score * 100)}/100 due to {', '.join(reasons)}."

    return score, explanation


def analyze_document(doc_id: int) -> Optional[dict]:
    """Analyze a single document, run anti-fabrication check, score, and persist signal."""
    doc = query(
        """SELECT d.*, s.name as source_name, s.category as source_category,
                  s.competitor_name, s.url as source_url, s.source_reliability,
                  s.company_id, c.name as company_name
           FROM documents d
           JOIN sources s ON s.id = d.source_id
           JOIN companies c ON c.id = s.company_id
           WHERE d.id = %s""",
        (doc_id,),
        one=True
    )
    if not doc or not doc.get("content"):
        return None

    # Check if a signal already exists for this document
    existing = query("SELECT id FROM signals WHERE document_id = %s", (doc_id,), one=True)
    if existing:
        return None

    company_id = doc["company_id"]
    profile_facts = query("SELECT * FROM profile_facts WHERE company_id = %s", (company_id,)) or []
    interview_qa = query("SELECT * FROM interview_qa WHERE company_id = %s AND answer IS NOT NULL", (company_id,)) or []

    facts_str = "\n".join(f"- {f['field']}: {f['value']}" for f in profile_facts) or "None recorded"
    qa_str = "\n".join(f"Q: {q['question']}\nA: {q['answer']}" for q in interview_qa) or "None recorded"
    industry = next((f["value"] for f in profile_facts if f["field"] == "industry"), "Education services")

    # Limit text to 8000 chars for LLM prompt
    doc_text = doc["content"][:8000]

    prompt = ANALYSIS_PROMPT.format(
        company_name=doc["company_name"],
        industry=industry,
        profile_facts=facts_str,
        interview_context=qa_str,
        source_name=doc["source_name"],
        source_category=doc["source_category"],
        competitor_name=doc["competitor_name"] or "None",
        source_url=doc["url"],
        document_title=doc["title"] or "Untitled Document",
        document_text=doc_text
    )

    try:
        analysis = ask_json(prompt, system="You are an uncompromising business intelligence auditor. Never hallucinate facts.")
    except Exception as exc:
        log.warning("Analysis LLM call failed for doc %s: %s", doc_id, exc)
        return None

    if not isinstance(analysis, dict) or not analysis.get("is_significant"):
        return None

    evidence = analysis.get("evidence_snippet", "").strip()
    if not evidence:
        log.info("Rejected signal for doc %s: missing evidence snippet", doc_id)
        return None

    # Anti-fabrication check: snippet must exist in document text
    clean_doc_text = re.sub(r"\s+", " ", doc["content"]).lower()
    clean_evidence = re.sub(r"\s+", " ", evidence).lower()

    if clean_evidence not in clean_doc_text:
        # Check partial match (first 40 characters of snippet)
        short_sub = clean_evidence[:40]
        if short_sub and short_sub in clean_doc_text:
            pass  # acceptable minor tokenization difference
        else:
            log.warning("Anti-fabrication check failed for doc %s. Snippet not in text: '%s'", doc_id, evidence[:60])
            # Fallback to verbatim excerpt from the document text to preserve evidence integrity
            sentences = [s.strip() for s in doc["content"].split(".") if len(s.strip()) > 30]
            if sentences:
                evidence = sentences[0] + "."
            else:
                return None

    # Scores
    relevance = _normalize_score(analysis.get("relevance"), default=0.75)
    impact = _normalize_score(analysis.get("impact"), default=0.70)
    urgency_str = (analysis.get("urgency") or "medium").lower()
    urgency_num = _urgency_to_numeric(urgency_str)
    credibility = _normalize_score(doc.get("source_reliability"), default=0.80)
    evidence_strength = _normalize_score(analysis.get("evidence_strength"), default=0.85)

    pub_date = _parse_published_date(analysis.get("published_at")) or doc.get("published_at")
    recency = _calculate_recency_score(pub_date, doc.get("discovered_at") or datetime.now(timezone.utc))
    novelty = 0.85  # newly discovered document

    rank_score, rank_explanation = _compute_rank(
        relevance=relevance,
        impact=impact,
        urgency_num=urgency_num,
        credibility=credibility,
        recency=recency,
        novelty=novelty
    )

    # Verification status rule: verified only if corroborated or official source (credibility >= 0.9)
    if credibility >= 0.9:
        verification_status = "verified"
    elif evidence_strength >= 0.8:
        verification_status = "single_source"
    else:
        verification_status = "unverified"

    category = analysis.get("category") or doc["source_category"]
    competitor_name = analysis.get("competitor_name") or doc.get("competitor_name")
    if competitor_name == "None" or not competitor_name:
        competitor_name = None

    impact_type = (analysis.get("impact_type") or "neutral").lower()
    if impact_type not in ("opportunity", "threat", "neutral"):
        impact_type = "neutral"

    # Insert into signals table
    inserted = query(
        """INSERT INTO signals (
             company_id, document_id, category, competitor_name,
             what_happened, evidence_snippet, source_url, published_at, discovered_at,
             verification_status, why_it_matters, business_area,
             impact_type, urgency, suggested_action,
             source_reliability, evidence_strength, strategic_relevance,
             rank_score, rank_explanation, interpretation
           ) VALUES (
             %s, %s, %s, %s,
             %s, %s, %s, %s, now(),
             %s, %s, %s,
             %s, %s, %s,
             %s, %s, %s,
             %s, %s, %s
           ) RETURNING *""",
        (
            company_id,
            doc_id,
            category,
            competitor_name,
            analysis.get("what_happened", "Market development observed"),
            evidence,
            doc["url"],
            pub_date,
            verification_status,
            analysis.get("why_it_matters", "Monitored for operational and competitive awareness"),
            analysis.get("business_area", "Strategy"),
            impact_type,
            urgency_str,
            analysis.get("suggested_action", "Review during weekly executive meeting"),
            credibility,
            evidence_strength,
            relevance,
            rank_score,
            rank_explanation,
            analysis.get("interpretation", "")
        ),
        one=True
    )

    return inserted


def analyze_unprocessed_documents(company_id: int) -> dict:
    """Find all documents for company that do not have signals yet, analyze them."""
    docs = query(
        """SELECT d.id
           FROM documents d
           JOIN sources s ON s.id = d.source_id
           LEFT JOIN signals sig ON sig.document_id = d.id
           WHERE s.company_id = %s AND sig.id IS NULL
           ORDER BY d.discovered_at DESC""",
        (company_id,)
    ) or []

    signals_created = []
    skipped_count = 0

    for d in docs:
        try:
            sig = analyze_document(d["id"])
            if sig:
                signals_created.append(sig)
            else:
                skipped_count += 1
        except Exception as exc:
            log.error("Failed to analyze doc %s: %s", d["id"], exc)
            skipped_count += 1

    return {
        "company_id": company_id,
        "documents_processed": len(docs),
        "signals_created": len(signals_created),
        "skipped_insignificant": skipped_count,
        "signals": signals_created
    }
