from typing import Any

from app.agents.base_agent import safe_llm_json


COMMAND_KEYWORDS = [
    # Create / update / delete
    "add",
    "create",
    "remove",
    "delete",
    "update",
    "change",
    "edit",
    "rename",

    # Expense language
    "expense",
    "expenses",
    "category",
    "categories",
    "paid",
    "pay",
    "buy",
    "bought",
    "cost",
    "spent",
    "income",
    "salary",

    # Loan language
    "loan",
    "loans",
    "lent",
    "borrowed",
    "debt",

    # Read/list language
    "show",
    "list",
    "get",
    "display",
    "check",
    "view",
    "see",
]


FINANCIAL_ADVICE_KEYWORDS = [
    "advice",
    "analyze",
    "analysis",
    "summary",
    "financial situation",
    "what should i do with my money",
    "am i spending too much",
]


RECOMMENDATION_KEYWORDS = [
    "recommend",
    "recommendation",
    "suggest",
    "suggestion",
    "how can i save",
    "improve my budget",
]


NOTIFICATION_KEYWORDS = [
    "remind",
    "reminder",
    "notify",
    "notification",
    "warning",
    "alert",
]


def heuristic_intent(message: str | None, has_image: bool) -> dict[str, Any]:
    """
    Deterministic fallback router.

    This is not the main intelligence layer.
    It protects the graph from bad LLM routing on obvious commands like:
    - show my categories
    - show my loans
    - list expenses
    """

    text = (message or "").lower().strip()

    if has_image:
        return {
            "intent": "vision_extraction",
            "reason": "The request contains an image.",
        }

    # Very clear list/read commands
    obvious_list_patterns = [
        "show my categories",
        "show categories",
        "list categories",
        "get categories",
        "display categories",
        "view categories",
        "check categories",

        "show my expenses",
        "show expenses",
        "list expenses",
        "get expenses",
        "display expenses",
        "view expenses",
        "check expenses",

        "show my loans",
        "show loans",
        "list loans",
        "get loans",
        "display loans",
        "view loans",
        "check loans",
    ]

    if any(pattern in text for pattern in obvious_list_patterns):
        return {
            "intent": "command",
            "reason": "The user wants to list existing financial data.",
        }

    if any(keyword in text for keyword in NOTIFICATION_KEYWORDS):
        return {
            "intent": "notification",
            "reason": "The user asks about reminders, alerts, warnings, or notifications.",
        }

    if any(keyword in text for keyword in RECOMMENDATION_KEYWORDS):
        return {
            "intent": "recommendation",
            "reason": "The user asks for recommendations or suggestions.",
        }

    if any(keyword in text for keyword in FINANCIAL_ADVICE_KEYWORDS):
        return {
            "intent": "financial_advice",
            "reason": "The user asks for financial analysis or advice.",
        }

    if any(keyword in text for keyword in COMMAND_KEYWORDS):
        return {
            "intent": "command",
            "reason": "The message looks like a financial command or data request.",
        }

    return {
        "intent": "unknown",
        "reason": "The request is not clear enough.",
    }


def route_intent(message: str | None, has_image: bool) -> dict[str, Any]:
    """
    Supervisor Agent.

    Chooses which specialized agent should handle the request.
    """

    fallback = heuristic_intent(message, has_image)

    prompt = f"""
You are the SupervisorAgent for AMMA, an AI Money Management Assistant.

Classify the user request into exactly one intent.

Intents:
- command:
  User wants to add, update, delete, list, show, check, view, or manage financial data.
  This includes expenses, categories, loans, income, debt, and payments.
  Examples:
  "show my categories" -> command
  "show my loans" -> command
  "list my expenses" -> command
  "add food expense 450" -> command
  "delete coffee expense" -> command
  "rename Food category to Groceries" -> command

- financial_advice:
  User wants financial analysis, explanation, budget analysis, or advice.
  Examples:
  "analyze my spending" -> financial_advice
  "am I spending too much?" -> financial_advice

- recommendation:
  User wants recommendations or suggestions.
  Examples:
  "recommend how I can save money" -> recommendation

- vision_extraction:
  User uploaded an image, receipt, or document.

- notification:
  User wants reminders, alerts, warnings, or notifications.
  Examples:
  "remind me to pay rent" -> notification

- unknown:
  Only use this if the message is not related to AMMA financial tasks.

Return ONLY valid JSON:
{{
  "intent": "command | financial_advice | recommendation | vision_extraction | notification | unknown",
  "reason": "short explanation"
}}

User message:
{message}

Has image:
{has_image}
"""

    result = safe_llm_json(prompt, fallback)

    intent = result.get("intent", fallback["intent"])

    allowed = {
        "command",
        "financial_advice",
        "recommendation",
        "vision_extraction",
        "notification",
        "unknown",
    }

    if intent not in allowed:
        intent = fallback["intent"]

    # Important safety rule:
    # If the LLM says unknown but deterministic routing clearly found a command,
    # use the deterministic result.
    if intent == "unknown" and fallback["intent"] != "unknown":
        intent = fallback["intent"]
        reason = fallback["reason"]
    else:
        reason = result.get("reason", fallback["reason"])

    return {
        "intent": intent,
        "reason": reason,
    }