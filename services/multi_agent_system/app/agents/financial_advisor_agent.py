from typing import Any

from app.agents.base_agent import safe_llm_json


def generate_financial_advice(message: str) -> dict[str, Any]:
    """
    Financial Advisor Agent.

    Produces financial analysis/advice.
    Later this should call analytics_tool for real dashboard data.
    """

    prompt = f"""
You are the FinancialAdvisorAgent for AMMA.

You give practical financial advice.

For this version:
- Be honest that real analytics data may be needed.
- Do not invent exact numbers.
- Give practical and safe advice.

Return ONLY valid JSON:
{{
  "risk_level": "low | medium | high | unknown",
  "summary": "short financial summary",
  "recommendations": ["recommendation 1", "recommendation 2"],
  "needs_real_analytics_data": true
}}

User message:
{message}
"""

    fallback = {
        "risk_level": "unknown",
        "summary": "I need analytics data to provide accurate advice.",
        "recommendations": [
            "Check income, expenses, budget usage, and active loans before making a decision."
        ],
        "needs_real_analytics_data": True,
    }

    return safe_llm_json(prompt, fallback)