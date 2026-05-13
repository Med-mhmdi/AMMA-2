from __future__ import annotations

from typing import Any

from app.agents.base_agent import safe_llm_json


def classify_conflict_decision(
    user_message: str,
    conflict_action: dict[str, Any],
    existing_record: dict[str, Any],
) -> dict[str, Any]:
    """
    Uses the LLM to understand the user's decision during conflict resolution.

    Important:
    This agent only classifies intent.
    It does not execute anything.
    It does not modify data.
    """

    fallback = {
        "decision": "unclear",
        "confidence": 0.0,
        "reason": "Fallback used because the LLM did not return a valid decision.",
    }

    prompt = f"""
You are AMMA's ConflictDecisionAgent.

The system found a possible duplicate/conflict and asked the user to choose what to do.

Allowed decisions:
- add_anyway
- update_existing
- cancel
- unclear

Meaning:
- add_anyway: The user wants to create/save/add the new record even if it duplicates an existing one.
- update_existing: The user wants to modify/update/replace/use the existing saved record instead of creating a new one.
- cancel: The user wants to stop/cancel/ignore the pending action.
- unclear: The user's message does not clearly choose one of the above.

User message:
{user_message}

Pending action:
{conflict_action}

Existing similar record:
{existing_record}

Rules:
- Return ONLY valid JSON.
- Do not execute anything.
- Do not ask a question.
- Do not invent data.
- If the user says something like "yes add it again", "add another one", "keep both", "save it too", classify as add_anyway.
- If the user says something like "update it", "replace it", "use the existing one", classify as update_existing.
- If the user says something like "cancel", "stop", "no don't add", classify as cancel.
- If the user sends the same original command again while conflict is pending, classify as unclear because they did not choose one of the options clearly.

Return JSON exactly like this:
{{
  "decision": "add_anyway | update_existing | cancel | unclear",
  "confidence": 0.0,
  "reason": "short reason"
}}
"""

    result = safe_llm_json(prompt, fallback)

    decision = result.get("decision", "unclear")
    confidence = result.get("confidence", 0.0)
    reason = result.get("reason", "")

    allowed = {"add_anyway", "update_existing", "cancel", "unclear"}

    if decision not in allowed:
        decision = "unclear"

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    # Safety threshold:
    # If the LLM is not confident, ask again instead of writing to DB.
    if confidence < 0.65 and decision in {"add_anyway", "update_existing"}:
        decision = "unclear"

    return {
        "decision": decision,
        "confidence": confidence,
        "reason": reason,
    }