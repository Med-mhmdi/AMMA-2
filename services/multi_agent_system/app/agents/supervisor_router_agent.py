from typing import Any

from app.agents.base_agent import safe_llm_json


CONFIRM_WORDS = [
    "yes",
    "yeah",
    "yep",
    "ok",
    "okay",
    "sure",
    "confirm",
    "do it",
    "create it",
    "add it",
    "yes add it",
    "yes create it",
    "oui",
    "saha",
]

DECLINE_WORDS = [
    "no",
    "nope",
    "cancel",
    "don't",
    "do not",
    "stop",
    "ignore",
    "لا",
]

COMMAND_KEYWORDS = [
    "add",
    "create",
    "remove",
    "delete",
    "update",
    "change",
    "edit",
    "rename",
    "show",
    "list",
    "get",
    "display",
    "check",
    "view",
    "see",
    "expense",
    "expenses",
    "category",
    "categories",
    "loan",
    "loans",
    "paid",
    "pay",
    "buy",
    "bought",
    "spent",
    "cost",
    "income",
    "salary",
    "lent",
    "borrowed",
    "debt",
]

FINANCIAL_ADVICE_KEYWORDS = [
    "advice",
    "analyze",
    "analysis",
    "budget",
    "spending",
    "financial situation",
]

RECOMMENDATION_KEYWORDS = [
    "recommend",
    "recommendation",
    "suggest",
    "suggestion",
    "how can i save",
]

NOTIFICATION_KEYWORDS = [
    "remind",
    "reminder",
    "notify",
    "notification",
    "warning",
    "alert",
]


def _contains_any(text: str, words: list[str]) -> bool:
    return any(word == text or word in text for word in words)


def _heuristic_route(
    message: str | None,
    has_image: bool,
    working_memory: dict[str, Any] | None,
) -> dict[str, Any]:
    text = (message or "").lower().strip()

    if working_memory and working_memory.get("awaiting_confirmation"):
        if _contains_any(text, CONFIRM_WORDS):
            return {
                "next_node": "confirmation_execution",
                "intent": "command",
                "reason": "User confirmed the saved working action.",
            }

        if _contains_any(text, DECLINE_WORDS):
            return {
                "next_node": "cancel_working_memory",
                "intent": "command",
                "reason": "User cancelled the saved working action.",
            }

        return {
            "next_node": "command_agent",
            "intent": "command",
            "reason": "User corrected or clarified an action waiting for confirmation.",
        }

    if working_memory and working_memory.get("current_action"):
        return {
            "next_node": "command_agent",
            "intent": "command",
            "reason": "There is an unfinished command, so the new message may complete it.",
        }

    if has_image:
        return {
            "next_node": "vision_agent",
            "intent": "vision_extraction",
            "reason": "The request contains an image.",
        }

    if _contains_any(text, COMMAND_KEYWORDS):
        return {
            "next_node": "command_agent",
            "intent": "command",
            "reason": "The message looks like a financial command or data request.",
        }

    if _contains_any(text, NOTIFICATION_KEYWORDS):
        return {
            "next_node": "notification_agent",
            "intent": "notification",
            "reason": "The user asks for reminders, alerts, or notifications.",
        }

    if _contains_any(text, RECOMMENDATION_KEYWORDS):
        return {
            "next_node": "recommendation_agent",
            "intent": "recommendation",
            "reason": "The user asks for recommendations.",
        }

    if _contains_any(text, FINANCIAL_ADVICE_KEYWORDS):
        return {
            "next_node": "financial_advisor",
            "intent": "financial_advice",
            "reason": "The user asks for financial advice or analysis.",
        }

    return {
        "next_node": "clarification_agent",
        "intent": "unknown",
        "reason": "The request is not clear enough.",
    }


def route_next_node(
    message: str | None,
    has_image: bool,
    working_memory: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Main supervisor router.

    It decides the next graph node after memory has been loaded.
    """

    fallback = _heuristic_route(
        message=message,
        has_image=has_image,
        working_memory=working_memory,
    )

    # Deterministic routes should not waste LLM calls.
    if fallback["next_node"] in [
        "confirmation_execution",
        "cancel_working_memory",
        "command_agent",
        "vision_agent",
        "clarification_agent",
    ]:
        return fallback

    prompt = f"""
You are the SupervisorRouterAgent for AMMA, an AI Money Management Assistant.

Choose the next node in the LangGraph workflow.

Possible next_node values:
- command_agent
- financial_advisor
- recommendation_agent
- notification_agent
- vision_agent
- clarification_agent

Intent meanings:
- command: add/update/delete/list/show/check/manage expenses, categories, loans, income, debt, or payments
- financial_advice: analysis, budget advice, spending explanation
- recommendation: suggestions or recommendations
- notification: reminders, alerts, warnings
- vision_extraction: image/receipt/document extraction
- unknown: unrelated or unclear

Return ONLY valid JSON:
{{
  "next_node": "command_agent | financial_advisor | recommendation_agent | notification_agent | vision_agent | clarification_agent",
  "intent": "command | financial_advice | recommendation | notification | vision_extraction | unknown",
  "reason": "short reason"
}}

User message:
{message}

Has image:
{has_image}

Working memory:
{working_memory}
"""

    result = safe_llm_json(prompt, fallback)

    allowed_next_nodes = {
        "command_agent",
        "financial_advisor",
        "recommendation_agent",
        "notification_agent",
        "vision_agent",
        "clarification_agent",
    }

    allowed_intents = {
        "command",
        "financial_advice",
        "recommendation",
        "notification",
        "vision_extraction",
        "unknown",
    }

    next_node = result.get("next_node", fallback["next_node"])
    intent = result.get("intent", fallback["intent"])

    if next_node not in allowed_next_nodes:
        next_node = fallback["next_node"]

    if intent not in allowed_intents:
        intent = fallback["intent"]

    return {
        "next_node": next_node,
        "intent": intent,
        "reason": result.get("reason", fallback["reason"]),
    }