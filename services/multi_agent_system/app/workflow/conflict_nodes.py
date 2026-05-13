from __future__ import annotations

from typing import Any

from app.agents.conflict_decision_agent import classify_conflict_decision
from app.agents.conflict_response_agent import generate_conflict_clarification_message
from app.graph.state import AgentState
from app.workflow.common import append_trace


# ============================================================
# Helpers
# ============================================================

def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _same_number(left: Any, right: Any) -> bool:
    try:
        return float(left) == float(right)
    except (TypeError, ValueError):
        return False


def _get_category_name_from_expense(expense: dict[str, Any]) -> str | None:
    category = expense.get("category")

    if isinstance(category, dict):
        return category.get("name")

    return expense.get("category_name") or expense.get("category")


def _find_duplicate_expense(
    data: dict[str, Any],
    tool_context: dict[str, Any],
) -> dict[str, Any] | None:
    expenses = tool_context.get("expenses") or []

    requested_description = _norm(data.get("description"))
    requested_amount = data.get("amount")
    requested_date = _norm(data.get("transaction_date") or data.get("date"))
    requested_type = _norm(data.get("type") or "outcome")
    requested_category = _norm(
        data.get("category")
        or data.get("category_name")
        or (tool_context.get("matched_category") or {}).get("name")
    )

    if not requested_description or requested_amount in [None, ""]:
        return None

    for expense in expenses:
        same_description = _norm(expense.get("description")) == requested_description
        same_amount = _same_number(expense.get("amount"), requested_amount)
        same_type = _norm(expense.get("type") or "outcome") == requested_type

        expense_date = _norm(expense.get("transaction_date") or expense.get("date"))
        same_date = not requested_date or expense_date == requested_date

        expense_category = _norm(_get_category_name_from_expense(expense))
        same_category = not requested_category or expense_category == requested_category

        if same_description and same_amount and same_type and same_date and same_category:
            return expense

    return None


def _find_duplicate_loan(
    data: dict[str, Any],
    tool_context: dict[str, Any],
) -> dict[str, Any] | None:
    loans = tool_context.get("loans") or []

    requested_person = _norm(
        data.get("person_name")
        or data.get("person")
        or data.get("borrower")
        or data.get("lender")
    )
    requested_type = _norm(data.get("type"))
    requested_amount = data.get("amount")
    requested_date = _norm(data.get("date_created") or data.get("created_at"))

    if not requested_person or requested_amount in [None, ""]:
        return None

    for loan in loans:
        same_person = _norm(
            loan.get("person_name")
            or loan.get("person")
            or loan.get("borrower")
            or loan.get("lender")
        ) == requested_person

        same_amount = _same_number(loan.get("amount"), requested_amount)
        same_type = not requested_type or _norm(loan.get("type")) == requested_type

        loan_date = _norm(loan.get("date_created") or loan.get("created_at"))
        same_date = not requested_date or loan_date == requested_date

        if same_person and same_amount and same_type and same_date:
            return loan

    return None


# ============================================================
# Conflict check node
# ============================================================

def conflict_check_node(state: AgentState) -> AgentState:
    """
    Checks whether a valid action conflicts with an existing backend record.

    Validation checks:
    - Is the action complete?
    - Is the action legal?
    - Does it require confirmation?

    Conflict check checks:
    - Is this action probably a duplicate?
    - Does a similar expense/loan already exist?
    """

    if state.get("skip_conflict_check"):
        return {
            "conflict_check": {
                "has_conflict": False,
                "skipped": True,
                "reason": "skip_conflict_check flag is true.",
            },
            "trace": append_trace(state, "ConflictCheckNode"),
        }

    extracted_action = state.get("extracted_action") or {}
    tool_context = state.get("tool_context") or {}

    action = extracted_action.get("action")
    data = extracted_action.get("data") or {}

    existing_record = None
    conflict_type = None

    if action == "create_expense" and not extracted_action.get("auto_create_missing_category"):
        existing_record = _find_duplicate_expense(data, tool_context)
        conflict_type = "possible_duplicate_expense"

    elif action == "create_loan":
        existing_record = _find_duplicate_loan(data, tool_context)
        conflict_type = "possible_duplicate_loan"

    if not existing_record:
        return {
            "conflict_check": {
                "has_conflict": False,
                "action": action,
            },
            "trace": append_trace(state, "ConflictCheckNode"),
        }

    conflict_action = {
        **extracted_action,
        "conflict_type": conflict_type,
        "existing_record": existing_record,
    }

    return {
        "conflict_check": {
            "has_conflict": True,
            "awaiting_conflict_resolution": True,
            "conflict_type": conflict_type,
            "conflict_action": conflict_action,
            "existing_record": existing_record,
            "options": ["add_anyway", "update_existing", "cancel"],
        },
        "trace": append_trace(state, "ConflictCheckNode"),
    }


# ============================================================
# Conflict resolution prepare node
# ============================================================

def conflict_resolution_prepare_node(state: AgentState) -> AgentState:
    """
    Prepares a conflict-resolution question and saves the conflict state
    through memory_update_node.
    """

    conflict_check = state.get("conflict_check") or {}

    conflict_action = conflict_check.get("conflict_action") or {}
    existing_record = conflict_check.get("existing_record") or {}
    options = conflict_check.get("options") or ["add_anyway", "update_existing", "cancel"]

    question = generate_conflict_clarification_message(
        user_message=state.get("message") or "",
        conflict_action=conflict_action,
        existing_record=existing_record,
        options=options,
    )

    return {
        "validation": {
            "is_valid": False,
            "needs_user_clarification": True,
            "awaiting_conflict_resolution": True,
            "question": question,
            "conflict_action": conflict_action,
            "conflict_options": options,
            "existing_record": existing_record,
        },
        "conflict_resolution": {
            "awaiting_conflict_resolution": True,
            "question": question,
            "conflict_action": conflict_action,
            "existing_record": existing_record,
            "options": options,
        },
        "trace": append_trace(state, "ConflictResolutionPrepareNode"),
    }


# ============================================================
# Conflict resolution handler node
# ============================================================

def conflict_resolution_handler_node(state: AgentState) -> AgentState:
    """
    Handles the user's answer after conflict_resolution_prepare_node.

    The user's decision is classified by the LLM into:
    - add_anyway
    - update_existing
    - cancel
    - unclear

    Safety rule:
    The LLM only classifies the user's decision.
    This node still controls the actual execution path.
    """

    working_memory = state.get("loaded_working_memory") or {}

    conflict_action = working_memory.get("conflict_action")
    existing_record = working_memory.get("conflict_existing_record")

    message = state.get("message")

    if not conflict_action:
        return {
            "execution_result": {
                "status": "failed",
                "message": "There is no saved conflict to resolve.",
            },
            "trace": append_trace(state, "ConflictResolutionHandlerNode"),
        }

    existing_record = existing_record or conflict_action.get("existing_record") or {}
    options = working_memory.get("conflict_options") or ["add_anyway", "update_existing", "cancel"]

    decision_result = classify_conflict_decision(
        user_message=message or "",
        conflict_action=conflict_action,
        existing_record=existing_record,
    )

    decision = decision_result.get("decision", "unclear")

    if decision == "cancel":
        return {
            "execution_result": {
                "status": "cancelled",
                "message": "Okay, I cancelled the duplicated action.",
            },
            "conflict_resolution": {
                "decision": "cancel",
                "decision_source": "llm",
                "decision_result": decision_result,
            },
            "trace": append_trace(state, "ConflictResolutionHandlerNode"),
        }

    if decision == "unclear":
        question = generate_conflict_clarification_message(
            user_message=message or "",
            conflict_action=conflict_action,
            existing_record=existing_record,
            options=options,
        )

        return {
            "validation": {
                "is_valid": False,
                "needs_user_clarification": True,
                "awaiting_conflict_resolution": True,
                "question": question,
            },
            "conflict_resolution": {
                "awaiting_conflict_resolution": True,
                "decision": "unclear",
                "decision_source": "llm",
                "decision_result": decision_result,
                "question": question,
                "conflict_action": conflict_action,
                "existing_record": existing_record,
                "options": options,
            },
            "trace": append_trace(state, "ConflictResolutionHandlerNode"),
        }

    if decision == "add_anyway":
        prepared_action = {
            **conflict_action,
            "confirmed": True,
        }

        prepared_action.pop("existing_record", None)
        prepared_action.pop("conflict_type", None)

        return {
            "intent": "command",
            "extracted_action": prepared_action,
            "confirmation_approved": True,
            "skip_confirmation": True,
            "skip_conflict_check": True,
            "conflict_resolution": {
                "decision": "add_anyway",
                "decision_source": "llm",
                "decision_result": decision_result,
            },
            "trace": append_trace(state, "ConflictResolutionHandlerNode"),
        }

    if decision == "update_existing":
        action = conflict_action.get("action")
        data = conflict_action.get("data") or {}

        if not existing_record.get("id"):
            return {
                "execution_result": {
                    "status": "failed",
                    "message": "I found the conflict, but I could not identify the existing record ID.",
                },
                "trace": append_trace(state, "ConflictResolutionHandlerNode"),
            }

        if action == "create_expense":
            updated_data = {
                **data,
                "expense_id": existing_record.get("id"),
                "id": existing_record.get("id"),
            }

            prepared_action = {
                "action": "update_expense",
                "data": updated_data,
                "confirmed": True,
            }

        elif action == "create_loan":
            updated_data = {
                **data,
                "loan_id": existing_record.get("id"),
                "id": existing_record.get("id"),
            }

            prepared_action = {
                "action": "update_loan",
                "data": updated_data,
                "confirmed": True,
            }

        else:
            return {
                "execution_result": {
                    "status": "failed",
                    "message": f"Update existing is not supported for action: {action}",
                },
                "trace": append_trace(state, "ConflictResolutionHandlerNode"),
            }

        return {
            "intent": "command",
            "extracted_action": prepared_action,
            "confirmation_approved": True,
            "skip_confirmation": True,
            "skip_conflict_check": True,
            "conflict_resolution": {
                "decision": "update_existing",
                "decision_source": "llm",
                "decision_result": decision_result,
                "existing_record": existing_record,
            },
            "trace": append_trace(state, "ConflictResolutionHandlerNode"),
        }

    return {
        "execution_result": {
            "status": "failed",
            "message": "Unsupported conflict resolution decision.",
        },
        "conflict_resolution": {
            "decision": decision,
            "decision_source": "llm",
            "decision_result": decision_result,
        },
        "trace": append_trace(state, "ConflictResolutionHandlerNode"),
    }