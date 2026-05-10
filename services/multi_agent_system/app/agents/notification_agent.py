from typing import Any

from app.agents.base_agent import safe_llm_json


def decide_notification(
    message: str,
    financial_advice: dict[str, Any],
    recommendation: dict[str, Any],
) -> dict[str, Any]:
    """
    Notification Agent.

    Decides whether AMMA should create or suggest a notification.
    """

    prompt = f"""
You are the NotificationAgent for AMMA.

Decide if the user needs a notification, reminder, or warning.

Return ONLY valid JSON:
{{
  "should_notify": true,
  "priority": "low | medium | high",
  "message": "notification message or empty string",
  "reason": "short reason"
}}

User message:
{message}

Financial advice:
{financial_advice}

Recommendation:
{recommendation}
"""

    fallback = {
        "should_notify": False,
        "priority": "low",
        "message": "",
        "reason": "No notification rule triggered.",
    }

    return safe_llm_json(prompt, fallback)