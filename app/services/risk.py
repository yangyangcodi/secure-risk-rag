"""
Risk service — generates a risk-assessed answer from retrieved context.

Supports four providers controlled by MODEL_PROVIDER in .env:
  - "mock"      : keyword-based risk scoring, no LLM needed (local dev/testing)
  - "ollama"    : local LLM via Ollama (free, runs on your machine)
  - "anthropic" : Claude via Anthropic SDK with streaming + prompt caching
  - "vertex"    : Gemini via Vertex AI (GCP production)

Returns: (answer, risk_level, risk_summary, confidence)
"""

import json
import re
from typing import Tuple

from app.core.config import settings

_VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}

# ---------------------------------------------------------------------------
# Mock provider
# ---------------------------------------------------------------------------

_HIGH_RISK_KEYWORDS = {
    "fraud", "breach", "default", "collapse", "laundering", "critical",
    "loss", "bankrupt", "insolvent", "violation", "penalty", "sanction",
}
_MEDIUM_RISK_KEYWORDS = {
    "late", "overdue", "delinquent", "spike", "surge", "exposure",
    "concentration", "volatility", "downgrade", "warning", "concern",
}


def _mock_response(question: str, context: str) -> Tuple[str, str, str, float]:
    combined = (question + " " + context).lower()
    words = set(combined.split())

    high_hits = words & _HIGH_RISK_KEYWORDS
    medium_hits = words & _MEDIUM_RISK_KEYWORDS

    if high_hits:
        risk_level = "high"
        confidence = 0.82
        risk_summary = (
            f"High-risk indicators detected: {', '.join(sorted(high_hits))}. "
            "Immediate review recommended."
        )
    elif medium_hits:
        risk_level = "medium"
        confidence = 0.70
        risk_summary = (
            f"Moderate risk signals present: {', '.join(sorted(medium_hits))}. "
            "Continued monitoring advised."
        )
    else:
        risk_level = "low"
        confidence = 0.90
        risk_summary = "No significant risk indicators found in the provided context."

    context_preview = context[:600].strip() if context else "No context retrieved."
    answer = (
        f"Based on the retrieved documents:\n\n{context_preview}"
    )

    return answer, risk_level, risk_summary, confidence


# ---------------------------------------------------------------------------
# Vertex AI provider
# ---------------------------------------------------------------------------

_RISK_PROMPT = """You are a financial risk analyst. Using ONLY the context below, answer the question and assess the risk level.

Context:
{context}

Question: {question}

Respond with a JSON object using this exact structure:
{{
  "answer": "<factual answer based strictly on the context>",
  "risk_level": "<one of: low, medium, high, critical>",
  "risk_summary": "<1-2 sentence explanation of the risk finding>",
  "confidence": <float between 0.0 and 1.0>
}}

Risk level guidelines:
- low: routine activity, no material concern
- medium: warrants monitoring, potential exposure
- high: action required, significant exposure identified
- critical: immediate escalation needed, severe risk

If context is insufficient, say so clearly and set risk_level to "medium"."""

_vertex_model = None


def _get_vertex_model():
    global _vertex_model
    if _vertex_model is None:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        vertexai.init(
            project=settings.vertex_project_id,
            location=settings.vertex_location,
        )
        _vertex_model = GenerativeModel(settings.gen_model)
    return _vertex_model


def _vertex_response(question: str, context: str) -> Tuple[str, str, str, float]:
    model = _get_vertex_model()
    prompt = _RISK_PROMPT.format(context=context, question=question)
    response = model.generate_content(prompt)
    text = response.text.strip()

    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return (
                data.get("answer") or "Unable to generate answer.",
                _normalise(data.get("risk_level") or "medium"),
                data.get("risk_summary") or "",
                float(data.get("confidence") or 0.5),
            )
        except (json.JSONDecodeError, ValueError):
            pass

    return text, "medium", "Unable to parse structured risk response.", 0.3


# ---------------------------------------------------------------------------
# Ollama provider
# ---------------------------------------------------------------------------

_OLLAMA_BASE_URL = "http://localhost:11434"

_OLLAMA_PROMPT = """You are a financial risk analyst. Using ONLY the context below, answer the question and assess the risk level.

Context:
{context}

Question: {question}

Respond with a JSON object using this exact structure:
{{
  "answer": "<factual answer based strictly on the context>",
  "risk_level": "<one of: low, medium, high, critical>",
  "risk_summary": "<1-2 sentence explanation of the risk finding>",
  "confidence": <float between 0.0 and 1.0>
}}

Risk level guidelines:
- low: routine activity, no material concern
- medium: warrants monitoring, potential exposure
- high: action required, significant exposure identified
- critical: immediate escalation needed, severe risk

If context is insufficient, say so and set risk_level to "medium".
Respond with JSON only — no extra text before or after."""


def _ollama_response(question: str, context: str) -> Tuple[str, str, str, float]:
    import requests

    prompt = _OLLAMA_PROMPT.format(context=context, question=question)
    try:
        resp = requests.post(
            f"{_OLLAMA_BASE_URL}/api/generate",
            json={"model": settings.gen_model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Cannot connect to Ollama. Make sure it is running: `ollama serve`"
        )

    text = resp.json().get("response", "").strip()

    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return (
                data.get("answer") or "Unable to generate answer.",
                _normalise(data.get("risk_level") or "medium"),
                data.get("risk_summary") or "",
                float(data.get("confidence") or 0.5),
            )
        except (json.JSONDecodeError, ValueError):
            pass

    return text, "medium", "Unable to parse structured risk response.", 0.3


# ---------------------------------------------------------------------------
# Anthropic provider
# ---------------------------------------------------------------------------

# System prompt is stable — good candidate for prompt caching.
_ANTHROPIC_SYSTEM = """You are a financial risk analyst assistant. Your job is to:
1. Answer questions using ONLY the provided context documents.
2. Assess the risk level based on what you find.
3. Always respond with valid JSON matching the required schema.

Risk level definitions:
- low: routine activity, no material concern
- medium: warrants monitoring, potential exposure
- high: action required, significant exposure identified
- critical: immediate escalation needed, severe risk

If the context is insufficient to answer confidently, say so and set risk_level to "medium"."""

_ANTHROPIC_USER_TEMPLATE = """Context documents:
{context}

Question: {question}

Respond with a JSON object using this exact structure:
{{
  "answer": "<factual answer based strictly on the context>",
  "risk_level": "<one of: low, medium, high, critical>",
  "risk_summary": "<1-2 sentence explanation of the risk finding>",
  "confidence": <float between 0.0 and 1.0>
}}"""

_anthropic_client = None


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


def _anthropic_response(question: str, context: str) -> Tuple[str, str, str, float]:
    client = _get_anthropic_client()
    user_content = _ANTHROPIC_USER_TEMPLATE.format(context=context, question=question)

    with client.messages.stream(
        model=settings.gen_model,
        max_tokens=1024,
        thinking={"type": "adaptive"},
        system=[
            {
                "type": "text",
                "text": _ANTHROPIC_SYSTEM,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_content}],
    ) as stream:
        message = stream.get_final_message()

    # Extract the text content block (thinking blocks are separate)
    text = ""
    for block in message.content:
        if block.type == "text":
            text = block.text.strip()
            break

    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return (
                data.get("answer") or "Unable to generate answer.",
                _normalise(data.get("risk_level") or "medium"),
                data.get("risk_summary") or "",
                float(data.get("confidence") or 0.5),
            )
        except (json.JSONDecodeError, ValueError):
            pass

    return text, "medium", "Unable to parse structured risk response.", 0.3


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_risk_response(question: str, context: str) -> Tuple[str, str, str, float]:
    """Generate a risk-assessed answer from retrieved context.

    Args:
        question: The user's question.
        context:  Retrieved document chunks joined as a single string.

    Returns:
        Tuple of (answer, risk_level, risk_summary, confidence)
    """
    if settings.model_provider == "mock":
        return _mock_response(question, context)
    if settings.model_provider == "ollama":
        return _ollama_response(question, context)
    if settings.model_provider == "anthropic":
        return _anthropic_response(question, context)
    return _vertex_response(question, context)


def _normalise(level: str) -> str:
    n = level.lower().strip()
    return n if n in _VALID_RISK_LEVELS else "medium"
