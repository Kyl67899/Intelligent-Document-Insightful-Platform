"""
services/llm_service.py
-------------------------
Wraps all calls to the LLM (Anthropic Claude). Two responsibilities:

1. analyze_document(text)   -> structured JSON: summary, key_insights, category
2. answer_question(question, context_chunks) -> grounded natural-language answer

Both functions ask the model to return strict JSON so the rest of the app
can parse the response deterministically instead of scraping prose.
"""

import json
import logging
import os

from anthropic import Anthropic

logger = logging.getLogger(__name__)

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to your backend .env file."
            )
        _client = Anthropic(api_key=api_key)
    return _client

def _model_name() -> str:
    return os.getenv("LLM_MODEL", "claude-sonnet-4-6")

def _extract_json(raw_text: str) -> dict:
    """Best-effort extraction of a JSON object from a model response,
    tolerating stray markdown code fences."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in LLM response.")
    return json.loads(cleaned[start : end + 1])

def analyze_document(text: str) -> dict:
    """
    Ask the LLM to produce a document analysis:
      - summary: <= 200 words
      - key_insights: 3-5 bullet-point strings
      - category: a short topic/category label

    `text` is truncated defensively so very long documents stay within a
    reasonable prompt size (the vector DB, not this call, is what handles
    full-document semantic search).
    """
    truncated = text[:20000]

    system_prompt = (
        "You are a precise document analyst. You read raw extracted PDF "
        "text (which may contain OCR noise) and produce a structured "
        "analysis. Always respond with ONLY a valid JSON object - no "
        "markdown fences, no commentary before or after it."
    )

    user_prompt = f"""Analyze the following document text and return a JSON object with
exactly these keys:

- "summary": a concise summary of the document in 200 words or fewer.
- "key_insights": an array of 3 to 5 short strings, each a distinct key
  insight, finding, or takeaway from the document.
- "category": a short label (1-4 words) for the document's main topic or
  category, e.g. "Legal Contract", "Financial Report", "Newsletter".

Document text:
\"\"\"
{truncated}
\"\"\"

Respond with only the JSON object."""

    client = _get_client()
    response = client.messages.create(
        model=_model_name(),
        max_tokens=1200,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw = "".join(block.text for block in response.content if block.type == "text")

    try:
        parsed = _extract_json(raw)
    except (ValueError, json.JSONDecodeError) as exc:
        logger.error("Failed to parse LLM analysis response: %s\nRaw: %s", exc, raw)
        parsed = {
            "summary": raw[:800],
            "key_insights": [],
            "category": "Uncategorized",
        }

    return {
        "summary": str(parsed.get("summary", "")).strip(),
        "key_insights": list(parsed.get("key_insights", []))[:5],
        "category": str(parsed.get("category", "Uncategorized")).strip(),
    }

def answer_question(question: str, context_chunks: list[str]) -> str:
    """
    Generate a natural-language answer to `question`, grounded only in
    `context_chunks` (the top-k semantically relevant chunks retrieved
    from the vector DB for the selected document).
    """
    context = "\n\n---\n\n".join(context_chunks) if context_chunks else "(no context retrieved)"

    system_prompt = (
        "You are a helpful assistant answering questions about a specific "
        "document. Answer using ONLY the provided context. If the answer "
        "isn't contained in the context, say you don't have enough "
        "information in the document to answer, rather than guessing."
    )

    user_prompt = f"""Context from the document:
\"\"\"
{context}
\"\"\"

Question: {question}

Give a clear, direct answer based only on the context above."""

    client = _get_client()
    response = client.messages.create(
        model=_model_name(),
        max_tokens=700,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()
