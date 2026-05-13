from typing import Any

from app.agents.base_agent import safe_llm_json


def _fallback_route(
    message: str | None,
    has_image: bool,
    working_memory: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Minimal safe fallback if the LLM router fails.

    Critical pending-memory routing is handled in app/workflow/agent_nodes.py.
    This fallback only handles normal non-pending routing.
    """

    text = (message or "").lower().strip()

    if has_image:
        return {
            "next_node": "vision_agent",
            "intent": "vision_extraction",
            "reason": "The request contains an image.",
        }

    command_keywords = [
        "add",
        "create",
        "delete",
        "remove",
        "update",
        "change",
        "rename",
        "list",
        "show",
        "check",
        "view",
        "expense",
        "expenses",
        "category",
        "categories",
        "loan",
        "loans",
        "income",
        "transaction",
        "transactions",
    ]

    if any(keyword in text for keyword in command_keywords):
        return {
            "next_node": "command_agent",
            "intent": "command",
            "reason": "Fallback detected a financial command keyword.",
        }

    advice_keywords = [
        "analyze",
        "analysis",
        "advice",
        "budget",
        "spending",
        "save money",
        "too much",
    ]

    if any(keyword in text for keyword in advice_keywords):
        return {
            "next_node": "financial_advisor",
            "intent": "financial_advice",
            "reason": "Fallback detected a financial advice request.",
        }

    return {
        "next_node": "clarification_agent",
        "intent": "unknown",
        "reason": "Fallback route because intent was unclear.",
    }


def route_next_node(
    message: str | None,
    has_image: bool,
    working_memory: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    SupervisorRouterAgent.

    This LLM router is used only when no critical pending memory state
    is active. Pending confirmation and conflict resolution are handled
    deterministically in workflow/agent_nodes.py.
    """

    fallback = _fallback_route(
        message=message,
        has_image=has_image,
        working_memory=working_memory,
    )

    prompt = f"""
You are the SupervisorRouterAgent for AMMA, an AI Money Management Assistant.

Your job is to choose the next LangGraph node.

Available next_node values:
- command_agent
- financial_advisor
- recommendation_agent
- notification_agent
- vision_agent
- clarification_agent

Available intent values:
- command
- financial_advice
- recommendation
- notification
- vision_extraction
- unknown

Routing rules:

1. Financial commands or data requests:
If the user wants to add, update, delete, list, show, check, view, or manage expenses, categories, loans, income, debt, payments, or transactions:
next_node = command_agent
intent = command

Examples:
- "show my categories"
- "show my loans"
- "list expenses"
- "add food expense 450"
- "delete coffee expense"
- "rename Food to Groceries"
- "I got 2000 from work"
- "I lent Ahmed 500"

2. Financial advice:
If the user asks for financial analysis, budget advice, or spending explanation:
next_node = financial_advisor
intent = financial_advice

Examples:
- "analyze my spending"
- "am I spending too much?"
- "what should I do with my money?"

3. Recommendation:
If the user asks for suggestions or recommendations:
next_node = recommendation_agent
intent = recommendation

Examples:
- "recommend how I can save money"
- "suggest a better budget"

4. Notification:
If the user asks for reminders, alerts, warnings, or notifications:
next_node = notification_agent
intent = notification

Examples:
- "remind me to pay rent"
- "notify me when budget is high"

5. Vision:
If the request contains an image:
next_node = vision_agent
intent = vision_extraction

6. Clarification:
If the message is unrelated, vague, or unclear:
next_node = clarification_agent
intent = unknown

Important:
- Return ONLY valid JSON.
- Do not include markdown.
- Do not explain outside JSON.

Current user message:
{message}

Has image:
{has_image}

Working memory:
{working_memory}

Return JSON:
{{
  "next_node": "command_agent | financial_advisor | recommendation_agent | notification_agent | vision_agent | clarification_agent",
  "intent": "command | financial_advice | recommendation | notification | vision_extraction | unknown",
  "reason": "short reason explaining the route"
}}
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
    reason = result.get("reason", fallback["reason"])

    if next_node not in allowed_next_nodes:
        next_node = fallback["next_node"]

    if intent not in allowed_intents:
        intent = fallback["intent"]

    return {
        "next_node": next_node,
        "intent": intent,
        "reason": reason,
    }