"""OpenAI wrapper: generate two responses for the same prompt (same model/params)."""

from openai import OpenAI
from typing import Any


DEFAULT_MODEL = "gpt-5.2"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1024


def generate_two_responses(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    client: OpenAI | None = None,
) -> tuple[str, str, dict[str, Any]]:
    """
    Call the OpenAI Responses API twice with the same prompt and params.
    Returns (response_a, response_b, metadata).
    """
    if client is None:
        client = OpenAI()
    metadata = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timestamp": None,  # set by caller with datetime
    }
    kwargs = {
        "model": model,
        "input": prompt,
        "temperature": temperature,
        "max_output_tokens": max_tokens,
    }
    r1 = client.responses.create(**kwargs)
    r2 = client.responses.create(**kwargs)

    def _text(r) -> str:
        return (r.output_text or "").strip()

    text_a = _text(r1)
    text_b = _text(r2)
    return text_a, text_b, metadata
