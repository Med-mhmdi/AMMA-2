from __future__ import annotations

import json
from typing import Any

from app.agents.base_agent import safe_llm_json


def _fallback_conflict_message(
    conflict_action: dict[str, Any],
    existing_record: dict[str, Any],
) -> str:
    action = conflict_action.get("action")
    data = conflict_action.get("data") or {}

    if action == "create_expense":
        return (
            "I found a possible duplicate expense already saved.\n\n"
            "Existing expense:\n"
            f"- ID: {existing_record.get('id')}\n"
            f"- Description: {existing_record.get('description') or data.get('description')}\n"
            f"- Amount: {existing_record.get('amount') or data.get('amount')}\n"
            f"- Category: {existing_record.get('category_name') or data.get('category')}\n"
            f"- Date: {existing_record.get('transaction_date') or data.get('transaction_date')}\n\n"
            "Your new request looks similar to this saved expense.\n"
            "Please choose one option: add anyway, update existing, or cancel."
        )

    if action == "create_loan":
        return (
            "I found a possible duplicate loan already saved.\n\n"
            "Existing loan:\n"
            f"- ID: {existing_record.get('id')}\n"
            f"- Person: {existing_record.get('person_name') or data.get('person_name')}\n"
            f"- Amount: {existing_record.get('amount') or data.get('amount')}\n"
            f"- Date: {existing_record.get('date_created') or data.get('date_created')}\n\n"
            "Your new request looks similar to this saved loan.\n"
            "Please choose one option: add anyway, update existing, or cancel."
        )

    return (
        "I found a possible duplicate record already saved.\n\n"
        "Your new request looks similar to an existing record.\n"
        "Please choose one option: add anyway, update existing, or cancel."
    )


def generate_conflict_clarification_message(
    user_message: str,
    conflict_action: dict[str, Any],
    existing_record: dict[str, Any],
    options: list[str] | None = None,
) -> str:
    """
    Generates a user-friendly conflict clarification message.

    Safety rule:
    This function only generates text. It must never decide, execute,
    or modify the action.
    """

    options = options or ["add_anyway", "update_existing", "cancel"]

    fallback_message = _fallback_conflict_message(
        conflict_action=conflict_action,
        existing_record=existing_record,
    )

    fallback = {
        "message": fallback_message,
    }

    prompt = f"""
You are AMMA, an AI Money Management Assistant.

The system is waiting for the user to resolve a possible duplicate/conflict.

User's latest message:
{user_message}

Pending action:
{json.dumps(conflict_action, ensure_ascii=False, indent=2)}

Existing similar record:
{json.dumps(existing_record, ensure_ascii=False, indent=2)}

Available user choices:
{json.dumps(options, ensure_ascii=False)}

Your job:
Generate a short, clear message telling the user that their new request may duplicate an existing saved record.

Rules:
- Return ONLY valid JSON.
- Do not execute anything.
- Do not say the action is completed.
- Mention the existing record details.
- Ask the user to choose one of these exact options in natural language:
  1. add anyway
  2. update existing
  3. cancel
- Keep the message friendly and concise.

Return JSON with exactly this shape:
{{
  "message": "your message here"
}}
"""

    result = safe_llm_json(prompt, fallback)
    message = result.get("message")

    if not message or not isinstance(message, str):
        return fallback_message

    return message.strip()