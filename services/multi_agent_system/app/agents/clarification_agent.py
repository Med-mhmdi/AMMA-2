from typing import Any

from app.agents.base_agent import safe_llm_json


def generate_clarification(
    message: str,
    working_memory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Generates a friendly clarification response for unclear or unsupported messages.
    """

    prompt = f"""
You are AMMA, an AI Money Management Assistant.

The user's message is unclear or unrelated to money management.
Respond politely and briefly.

Rules:
- If the user asks about non-financial topics like weather, explain that you focus on money management.
- If the user says sorry or something casual, answer naturally and ask how you can help with finances.
- Mention examples: expenses, income, categories, loans, budgets, financial advice.
- Return ONLY valid JSON.

User message:
{message}

Working memory:
{working_memory}

Return JSON:
{{
  "type": "clarification",
  "message": "friendly clarification message",
  "should_save_memory": true
}}
"""

    fallback = {
        "type": "clarification",
        "message": (
            "I could not understand the request clearly. "
            "You can ask me to add an expense, record income, manage loans, create categories, or give financial advice."
        ),
        "should_save_memory": True,
    }

    result = safe_llm_json(prompt, fallback)

    return {
        "type": "clarification",
        "message": result.get("message", fallback["message"]),
        "should_save_memory": bool(result.get("should_save_memory", True)),
    }