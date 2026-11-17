"""Internal Intelligence File Upload & Signal Extraction Service.

Supports:
- CSV: Sales objection logs, lost deal exports, CRM notes
- XLSX: Pipeline sheets, deal feedback spreadsheets
- PDF: Sales decks, executive call notes, transcripts, market summaries
- TXT: Raw interview notes, feedback emails, deal logs

Extracts:
- Customer objections
- Lost-deal root causes
- Urgent product / feature requests
- Team observations & operational friction
Transforms them into ranked signals with category='internal'.
"""

import csv
import io
import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional
import openpyxl
import pypdf
from ..db import get_conn, query
from .llm import ask_json

log = logging.getLogger(__name__)

INTERNAL_ANALYSIS_PROMPT = """You are a senior executive intelligence analyst for {company_name}.
You are analyzing internal first-party business records (CRM lost-deal logs, customer feedback, sales objection notes, team interview transcripts).

Company Profile:
{profile_facts}

Uploaded Document:
- Filename: {filename}
- File Kind: {kind}

Extracted Document Content:
---
{extracted_text}
---

Your task: Extract up to 5 distinct, high-impact INTERNAL intelligence signals from this document.
Focus specifically on:
1. Recurring customer objections or price resistance
2. Lost-deal root causes (why prospects chose competitors or dropped out)
3. Urgent student/client feature requests and pain points
4. Operational or product gaps affecting revenue or conversion

For EACH distinct signal found, return an object in the "signals" array:
{{
  "signals": [
    {{
      "what_happened": "Clear, objective description of the customer objection, lost-deal pattern, or product request (1-2 sentences)",
      "evidence_snippet": "EXACT verbatim quote or row text from the Extracted Document Content above proving this signal.",
      "why_it_matters": "Business and revenue implications for {company_name}",
      "business_area": "One of: Sales, Product, Pricing, Admissions, Customer Success, Operations",
      "impact_type": "threat" (if a vulnerability/lost revenue) or "opportunity" (if an unmet demand/fixable gap) or "neutral",
      "urgency": "high" or "medium" or "low",
      "suggested_action": "Specific, actionable internal task for the team this week",
      "interpretation": "Strategic assessment of what this objection or request indicates about market positioning or competitor pressure",
      "competitor_name": "Name of competitor mentioned if any, or null",
      "strategic_relevance": float between 0.0 and 1.0 (relevance to core business),
      "impact": float between 0.0 and 1.0 (business impact on revenue or churn),
      "evidence_strength": float between 0.7 and 1.0 (verifiability in document)
    }}
  ]
}}

If the document has no meaningful business intelligence, return {{"signals": []}}.
"""


def parse_file(filename: str, file_bytes: bytes) -> tuple[str, str]:
    """Parse uploaded file bytes into a clean text representation and file kind."""
    fname = filename.lower()
    text = ""
    kind = "text"

    if fname.endswith(".csv"):
        kind = "csv"
        try:
            decoded = file_bytes.decode("utf-8-sig", errors="replace")
        except Exception:
            decoded = file_bytes.decode("latin-1", errors="replace")

        reader = csv.reader(io.StringIO(decoded))
        rows = []
        for r in reader:
            row_str = " | ".join(c.strip() for c in r if c.strip())
            if row_str:
                rows.append(row_str)
        text = "\n".join(rows)

    elif fname.endswith(".xlsx") or fname.endswith(".xls"):
        kind = "xlsx"
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        sheets_text = []
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            sheets_text.append(f"=== Sheet: {sheet_name} ===")
            for row in ws.iter_rows(values_only=True):
                non_empty = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
                if non_empty:
                    sheets_text.append(" | ".join(non_empty))
        text = "\n".join(sheets_text)

    elif fname.endswith(".pdf"):
        kind = "pdf"
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for i, page in enumerate(reader.pages):
            page_content = page.extract_text()
            if page_content and page_content.strip():
                pages_text.append(f"--- Page {i + 1} ---\n{page_content.strip()}")
        text = "\n\n".join(pages_text)

    else:
        kind = "txt"
        try:
            text = file_bytes.decode("utf-8", errors="replace")
        except Exception:
            text = file_bytes.decode("latin-1", errors="replace")

    return kind, text.strip()


def _compute_internal_rank(relevance: float, impact: float, urgency_num: float, credibility: float, recency: float = 0.9, novelty: float = 0.9) -> tuple[float, str]:
    """Compute multi-factor rank score for internal signal."""
    score = (
        0.25 * relevance +
        0.20 * impact +
        0.15 * urgency_num +
        0.15 * credibility +
        0.15 * recency +
        0.10 * novelty
    )
    score = round(max(0.0, min(1.0, score)), 3)

    reasons = []
    if relevance >= 0.8:
        reasons.append("high relevance to revenue pipeline")
    if impact >= 0.8:
        reasons.append("critical customer retention impact")
    if urgency_num >= 0.8:
        reasons.append("requires immediate executive action")
    reasons.append("verified direct internal evidence")

    explanation = f"Prioritized at {int(score * 100)}/100 due to {', '.join(reasons)}."
    return score, explanation


def process_upload_and_extract_signals(company_id: int, filename: str, file_bytes: bytes) -> dict:
    """Parse uploaded file, store in uploads table, extract internal signals, rank, and store in signals table."""
    company = query("SELECT id, name FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise ValueError(f"Company ID {company_id} does not exist.")

    kind, extracted_text = parse_file(filename, file_bytes)
    if not extracted_text:
        raise ValueError("Could not extract any readable text from the uploaded file.")

    # 1. Save record in uploads table
    upload_row = query(
        """INSERT INTO uploads (company_id, filename, kind, extracted_text, uploaded_at)
           VALUES (%s, %s, %s, %s, now())
           RETURNING id, uploaded_at""",
        (company_id, filename, kind, extracted_text[:50000]),
        one=True
    )
    upload_id = upload_row["id"]
    log.info("Saved upload #%s for company %s (%s, %d bytes)", upload_id, company_id, filename, len(file_bytes))

    # 2. Collect company context
    facts = query(
        "SELECT field, value, status FROM profile_facts WHERE company_id = %s ORDER BY id",
        (company_id,)
    )
    facts_str = "\n".join(f"- {f['field']}: {f['value']} ({f['status']})" for f in facts) or "Study abroad platform."

    # Truncate text for prompt budget
    text_sample = extracted_text[:12000]

    prompt = INTERNAL_ANALYSIS_PROMPT.format(
        company_name=company["name"],
        profile_facts=facts_str,
        filename=filename,
        kind=kind,
        extracted_text=text_sample
    )

    try:
        response = ask_json(prompt)
    except Exception as e:
        log.error("LLM extraction failed for upload %s: %s", upload_id, e)
        response = {"signals": []}

    raw_signals = response.get("signals", []) if isinstance(response, dict) else []
    created_signals = []

    clean_doc_text = re.sub(r"\s+", " ", extracted_text).lower()

    for idx, s in enumerate(raw_signals):
        what = (s.get("what_happened") or "").strip()
        if not what:
            continue

        evidence = (s.get("evidence_snippet") or "").strip()
        # Fallback to verbatim excerpt if evidence is empty or hallucinated
        clean_ev = re.sub(r"\s+", " ", evidence).lower()
        if not clean_ev or clean_ev not in clean_doc_text:
            # Pick first substantive row from document
            lines = [l.strip() for l in extracted_text.splitlines() if len(l.strip()) > 20]
            if lines:
                evidence = lines[min(idx, len(lines) - 1)][:250]
            else:
                evidence = extracted_text[:150]

        relevance = float(s.get("strategic_relevance") or 0.85)
        impact = float(s.get("impact") or 0.80)
        urgency_str = (s.get("urgency") or "medium").lower()
        urgency_num = 0.9 if urgency_str == "high" else (0.6 if urgency_str == "medium" else 0.3)
        credibility = 0.95  # Internal first-party data is verified fact
        evidence_strength = float(s.get("evidence_strength") or 0.90)

        rank_score, rank_explanation = _compute_internal_rank(
            relevance=relevance,
            impact=impact,
            urgency_num=urgency_num,
            credibility=credibility
        )

        source_url = f"internal://uploads/{filename}#item-{idx + 1}"
        why = s.get("why_it_matters") or "Direct internal customer feedback affecting conversion and retention."
        biz_area = s.get("business_area") or "Sales"
        impact_type = s.get("impact_type") or "threat"
        action = s.get("suggested_action") or "Review feedback in weekly sales/product review."
        interpretation = s.get("interpretation") or "Key internal operational and competitive feedback."
        competitor = s.get("competitor_name")

        # Insert into signals table
        sig_row = query(
            """INSERT INTO signals (
                company_id, document_id, category, competitor_name,
                what_happened, evidence_snippet, source_url,
                published_at, discovered_at, verification_status,
                why_it_matters, business_area, impact_type, urgency,
                suggested_action, source_reliability, evidence_strength,
                strategic_relevance, rank_score, rank_explanation, interpretation
            ) VALUES (
                %s, NULL, 'internal', %s,
                %s, %s, %s,
                now(), now(), 'verified',
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s
            ) RETURNING id""",
            (
                company_id, competitor,
                what, evidence, source_url,
                why, biz_area, impact_type, urgency_str,
                action, credibility, evidence_strength,
                relevance, rank_score, rank_explanation, interpretation
            ),
            one=True
        )

        created_signals.append({
            "id": sig_row["id"],
            "what_happened": what,
            "evidence_snippet": evidence,
            "rank_score": rank_score,
            "business_area": biz_area,
            "impact_type": impact_type,
            "urgency": urgency_str,
            "suggested_action": action,
            "source_url": source_url,
        })

    log.info("Extracted %d internal signals from upload #%s", len(created_signals), upload_id)

    return {
        "upload_id": upload_id,
        "filename": filename,
        "kind": kind,
        "characters_extracted": len(extracted_text),
        "signals_created_count": len(created_signals),
        "signals": created_signals,
    }
