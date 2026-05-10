from typing import Any

from app.providers.llm_provider import ollama_client


def safe_llm_json(prompt: str, fallback: dict[str, Any]) -> dict[str, Any]:
    """
    Safely calls the configured LLM provider and expects JSON output.

    If the LLM fails or returns invalid JSON, the fallback is returned
    with an extra llm_error field.
    """

    try:
        return ollama_client.generate_json(prompt)
    except Exception as exc:
        return {
            **fallback,
            "llm_error": str(exc),
        }