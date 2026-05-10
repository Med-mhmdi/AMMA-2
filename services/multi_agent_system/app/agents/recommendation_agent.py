from typing import Any

from app.agents.base_agent import safe_llm_json


def generate_recommendations(
    message: str,
    financial_advice: dict[str, Any],
) -> dict[str, Any]:
    """
    Recommendation Agent.

    Converts financial advice into clear user actions.
    """

    prompt = f"""
You are the RecommendationAgent for AMMA.

Your job is to convert financial analysis into practical recommendations.

Return ONLY valid JSON:
{{
  "recommendation_type": "saving | spending_control | debt_management | budgeting | general",
  "recommendations": ["recommendation 1", "recommendation 2"],
  "reason": "short reason",
  "needs_notification": false
}}

User message:
{message}

Financial advice:
{financial_advice}
"""

    fallback = {
        "recommendation_type": "general",
        "recommendations": financial_advice.get(
            "recommendations",
            ["Check your monthly expenses and compare them with your income."]
        ),
        "reason": "Generated from available financial advice.",
        "needs_notification": False,
    }

    return safe_llm_json(prompt, fallback)