from typing import Any

from app.agents.base_agent import safe_llm_json


def _fallback_route(
    message: str | None,
    has_image: bool,
    working_memory: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Minimal safe fallback only if the LLM fails.

    The main routing intelligence is the LLM.
    This fallback avoids crashes and keeps the graph moving.
    """

    if has_image:
        return {
            "next_node": "vision_agent",
            "intent": "vision_extraction",
            "reason": "The request contains an image.",
        }

    if working_memory and working_memory.get("awaiting_confirmation"):
        return {
            "next_node": "command_agent",
            "intent": "command",
            "reason": "There is a saved action waiting for confirmation or correction.",
        }

    if working_memory and working_memory.get("current_action"):
        return {
            "next_node": "command_agent",
            "intent": "command",
            "reason": "There is an unfinished command in memory.",
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

    Uses the LLM to decide the next graph node based on:
    - current user message
    - whether an image exists
    - unified working memory
    - confirmation state
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
- confirmation_execution
- cancel_working_memory
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

General routing rules:

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

Special rules when working_memory.awaiting_confirmation is true:

The assistant previously showed an action and asked the user to confirm or correct it.

Classify the new user message carefully:

A. Confirmation:
If the user clearly confirms the saved action:
Examples:
- "yes"
- "ok"
- "okay"
- "confirm"
- "do it"
- "add it"
- "create it"
- "looks good"
- "correct"
- "yes add it"
Then:
next_node = confirmation_execution
intent = command

B. Cancellation:
If the user clearly cancels the saved action without giving corrections:
Examples:
- "cancel"
- "stop"
- "forget it"
- "do not add it"
- "no" when it only means no/cancel
Then:
next_node = cancel_working_memory
intent = command

C. Correction / clarification:
If the user gives corrected data, replacement values, or extra details:
Examples:
- "no, it cost 92 total"
- "actually category is Food"
- "use 250 instead"
- "change the amount to 92"
- "it is food"
- "not Transport, it is Food"
- "description should be university bus round trip"
- "the amount is 92"
Then:
next_node = command_agent
intent = command

Important:
- Do NOT treat every message containing "no" as cancellation.
- If "no" is followed by corrected data, route to command_agent.
- If there is an unfinished current_action in memory, the current message may complete or correct it, so usually route to command_agent.
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
  "next_node": "command_agent | confirmation_execution | cancel_working_memory | financial_advisor | recommendation_agent | notification_agent | vision_agent | clarification_agent",
  "intent": "command | financial_advice | recommendation | notification | vision_extraction | unknown",
  "reason": "short reason explaining the route"
}}
"""

    result = safe_llm_json(prompt, fallback)

    allowed_next_nodes = {
        "command_agent",
        "confirmation_execution",
        "cancel_working_memory",
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