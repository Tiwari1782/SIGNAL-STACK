"""LLM wrapper: Groq primary (per user preference), Gemini fallback. Use ask_json() for structured output."""
import json
import logging
import os
import re
from ..config import GEMINI_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL

log = logging.getLogger(__name__)

def _groq(prompt: str, system: str) -> str:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set")
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    r = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        temperature=0.2
    )
    return r.choices[0].message.content

def _gemini(prompt: str, system: str) -> str:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set")
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)
    r = client.models.generate_content(model=GEMINI_MODEL, contents=f"{system}\n\n{prompt}")
    return r.text

def ask(prompt: str, system: str = "You are a precise business intelligence analyst.",
        prefer: str = "groq") -> str:
    order = [_groq, _gemini] if prefer == "groq" else [_gemini, _groq]
    last = None
    for fn in order:
        try:
            return fn(prompt, system)
        except Exception as e:
            log.warning("LLM provider %s failed: %s", fn.__name__, e)
            last = e
    raise RuntimeError(f"All LLM providers failed: {last}")

def ask_json(prompt: str, **kw):
    raw = ask(prompt + "\n\nReturn ONLY a valid JSON. No commentary, no introductory text, no markdown fences.", **kw)
    # Strip markdown code blocks if present
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if match:
        cleaned = match.group(1).strip()
    else:
        # Or look for [ ... ] or { ... }
        bracket_match = re.search(r"(\[[\s\S]*\]|\{[\s\S]*\})", raw)
        cleaned = bracket_match.group(1).strip() if bracket_match else raw.strip()
    return json.loads(cleaned)
