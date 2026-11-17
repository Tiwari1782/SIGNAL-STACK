"""Adaptive AI Interview router: 10 dynamic questions per company, one at a time."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..db import query
from ..services.llm import ask_json

router = APIRouter(tags=["interview"])
log = logging.getLogger(__name__)

TOPICS_GUIDANCE = """
1. Primary business lines and revenue streams
2. Highest-value customer segments and ideal buyer profiles
3. Critical customer pain points and unmet needs
4. Key differentiators vs alternatives (why customers pick them)
5. Direct competitors and unexpected substitutes
6. Major regulatory, policy, or market shifts affecting their space
7. Emerging risks or macro developments that could harm the business
8. Top strategic and growth priorities for the next 6-12 months
9. Internal data signals (objections, CRM patterns, churn reasons)
10. Key executive decisions this intelligence system must support
"""

class AnswerRequest(BaseModel):
    seq: int
    answer: Optional[str] = None
    skip: Optional[bool] = False

class UpdateAnswerRequest(BaseModel):
    answer: str

def _generate_next_question(company: dict, profile_facts: list[dict], qa_history: list[dict], seq: int) -> dict:
    """Ask LLM to generate the next tailored interview question."""
    facts_str = "\n".join(f"- {f['field']}: {f['value']} ({f['status']})" for f in profile_facts) or "None recorded yet."

    qa_str = ""
    if qa_history:
        for item in qa_history:
            status = "SKIPPED" if item.get("skipped") else (item.get("answer") or "No answer provided")
            qa_str += f"Q{item['seq']}: {item['question']}\nA: {status}\n\n"
    else:
        qa_str = "No questions asked yet."

    prompt = f"""You are conducting an adaptive executive interview for the founder/leadership of {company['name']} ({company['website']}).
Your goal is to build deep strategic context for their automated intelligence monitoring system.

Company Facts:
{facts_str}

Interview Transcript So Far:
{qa_str}

Interview Guidance Topics (aim to explore uncovered areas or ask a sharp follow-up if the previous answer warrants deeper clarification):
{TOPICS_GUIDANCE}

Rules for Question #{seq} (Total 10):
1. Ask ONE concise, specific, thought-provoking question tailored to {company['name']}'s exact business.
2. Do NOT ask generic business questions. Refer to their actual industry and previously stated facts.
3. If the previous answer introduced a critical nuance or mystery, ask an insightful follow-up question.
4. If previous topics are well covered, pivot to an untouched guidance topic.
5. Return ONLY a JSON object:
{{
  "question": "your question text here",
  "is_followup": true or false,
  "topic": "topic name"
}}
"""
    try:
        data = ask_json(prompt, system="You are a sharp, senior venture strategist conducting an executive briefing interview.")
        if isinstance(data, dict) and "question" in data:
            return data
    except Exception as e:
        log.warning("LLM question generation failed: %s", e)

    # Fallback default if LLM fails
    fallbacks = [
        "What are your core revenue streams and primary products today?",
        "Who is your highest-value customer segment, and who makes the buying decision?",
        "What are the top 2-3 reasons customers choose you over direct competitors?",
        "Who are your 3 most threatening competitors or emerging substitutes?",
        "What recent market or regulatory changes could impact your business model?",
        "What are your top 1-2 growth priorities over the next 6 to 12 months?",
        "What recurring objections or deal-breakers do you hear most often from prospects?",
        "What early-warning signals would you want to know about before anyone else?",
        "Which internal metrics or data sources reveal the most about customer satisfaction?",
        "What is the single most critical strategic decision you need intelligence for this quarter?"
    ]
    fb_text = fallbacks[(seq - 1) % len(fallbacks)]
    return {"question": fb_text, "is_followup": False, "topic": "General Context"}


@router.get("/api/companies/{company_id}/interview/next")
def get_next_question(company_id: int):
    """Retrieve the current pending question, or generate the next question up to 10."""
    company = query("SELECT * FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, "Company not found")

    history = query(
        "SELECT * FROM interview_qa WHERE company_id = %s ORDER BY seq ASC",
        (company_id,)
    ) or []

    # Check if there is an existing unanswered question
    for q in history:
        if q["answer"] is None and not q["skipped"]:
            return {
                "completed": False,
                "current_question": q,
                "total_completed": len([x for x in history if x["answer"] is not None or x["skipped"]]),
                "total_target": 10,
                "history": history
            }

    completed_count = len([x for x in history if x["answer"] is not None or x["skipped"]])
    if completed_count >= 10:
        return {
            "completed": True,
            "current_question": None,
            "total_completed": completed_count,
            "total_target": 10,
            "history": history
        }

    next_seq = completed_count + 1
    profile_facts = query("SELECT * FROM profile_facts WHERE company_id = %s", (company_id,)) or []

    gen = _generate_next_question(company, profile_facts, history, next_seq)

    row = query(
        """INSERT INTO interview_qa (company_id, seq, question, is_followup)
           VALUES (%s, %s, %s, %s)
           RETURNING *""",
        (company_id, next_seq, gen["question"], gen.get("is_followup", False)),
        one=True
    )

    history.append(row)
    return {
        "completed": False,
        "current_question": row,
        "total_completed": completed_count,
        "total_target": 10,
        "history": history
    }


@router.post("/api/companies/{company_id}/interview/answer")
def submit_answer(company_id: int, body: AnswerRequest):
    """Submit an answer or skip for a specific question seq."""
    company = query("SELECT id FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, "Company not found")

    existing = query(
        "SELECT * FROM interview_qa WHERE company_id = %s AND seq = %s",
        (company_id, body.seq),
        one=True
    )
    if not existing:
        raise HTTPException(404, f"Question seq {body.seq} not found")

    if body.skip:
        updated = query(
            """UPDATE interview_qa
               SET skipped = true, answer = NULL, updated_at = now()
               WHERE id = %s RETURNING *""",
            (existing["id"],),
            one=True
        )
    else:
        if not body.answer or not body.answer.strip():
            raise HTTPException(400, "Answer cannot be empty if not skipping")
        updated = query(
            """UPDATE interview_qa
               SET answer = %s, skipped = false, updated_at = now()
               WHERE id = %s RETURNING *""",
            (body.answer.strip(), existing["id"]),
            one=True
        )

    return updated


@router.get("/api/companies/{company_id}/interview")
def get_interview_history(company_id: int):
    """Get all interview questions and answers for a company."""
    company = query("SELECT id FROM companies WHERE id = %s", (company_id,), one=True)
    if not company:
        raise HTTPException(404, "Company not found")

    items = query(
        "SELECT * FROM interview_qa WHERE company_id = %s ORDER BY seq ASC",
        (company_id,)
    )
    return items


@router.patch("/api/interview/{qa_id}")
def update_answer(qa_id: int, body: UpdateAnswerRequest):
    """Edit an existing answer later."""
    existing = query("SELECT * FROM interview_qa WHERE id = %s", (qa_id,), one=True)
    if not existing:
        raise HTTPException(404, "Interview QA item not found")

    if not body.answer or not body.answer.strip():
        raise HTTPException(400, "Answer text is required")

    updated = query(
        """UPDATE interview_qa
           SET answer = %s, skipped = false, updated_at = now()
           WHERE id = %s RETURNING *""",
        (body.answer.strip(), qa_id),
        one=True
    )
    return updated
