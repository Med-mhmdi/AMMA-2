from __future__ import annotations

from typing import Any

from app.graph.state import AgentState
from app.workflow.common import append_trace


# ============================================================
# Action groups
# ============================================================

READ_ONLY_ACTIONS = {
    "list_expenses",
    "list_categories",
    "list_loans",
}

MUTATING_ACTIONS = {
    "create_expense",
    "update_expense",
    "delete_expense",
    "create_category",
    "update_category",
    "delete_category",
    "create_loan",
    "update_loan",
    "update_loan_status",
    "delete_loan",
}


# ============================================================
# Shared helpers
# ============================================================

def is_read_only_action(action: str | None) -> bool:
    return action in READ_ONLY_ACTIONS


def is_mutating_action(action: str | None) -> bool:
    return action in MUTATING_ACTIONS


def _format_value(value: Any) -> str:
    if value in [None, "", []]:
        return "not provided"

    return str(value)


def _get_category_name(action_data: dict[str, Any]) -> str | None:
    return (
        action_data.get("category")
        or action_data.get("category_name")
        or action_data.get("name")
    )


# ============================================================
# Confirmation message builders
# ============================================================

def _build_expense_confirmation(action_data: dict[str, Any]) -> str:
    transaction_type = action_data.get("type", "outcome")

    if transaction_type == "income":
        title = "I will add this income transaction:"
    else:
        title = "I will add this expense transaction:"

    return (
        f"{title}\n"
        f"- Description: {_format_value(action_data.get('description'))}\n"
        f"- Type: {_format_value(transaction_type)}\n"
        f"- Amount: {_format_value(action_data.get('amount'))} rubles\n"
        f"- Category: {_format_value(_get_category_name(action_data))}\n"
        f"- Date: {_format_value(action_data.get('transaction_date'))}\n\n"
        f"Please confirm, or correct anything."
    )


def _build_category_confirmation(action: str, action_data: dict[str, Any]) -> str:
    if action == "create_category":
        return (
            f'I will create the category "{_format_value(_get_category_name(action_data))}".\n\n'
            f"Please confirm, or correct anything."
        )

    if action == "delete_category":
        return (
            f'I will delete the category "{_format_value(_get_category_name(action_data))}".\n\n'
            f"Please confirm, or correct anything."
        )

    if action == "update_category":
        return (
            f"I will rename this category:\n"
            f"- From: {_format_value(action_data.get('old_category'))}\n"
            f"- To: {_format_value(action_data.get('new_category'))}\n\n"
            f"Please confirm, or correct anything."
        )

    return "Please confirm this category action, or correct anything."


def _build_loan_confirmation(action: str, action_data: dict[str, Any]) -> str:
    if action == "create_loan":
        return (
            f"I will create this loan record:\n"
            f"- Person: {_format_value(action_data.get('person_name'))}\n"
            f"- Type: {_format_value(action_data.get('type'))}\n"
            f"- Amount: {_format_value(action_data.get('amount'))} rubles\n"
            f"- Date: {_format_value(action_data.get('date_created'))}\n"
            f"- Return date: {_format_value(action_data.get('return_date'))}\n\n"
            f"Please confirm, or correct anything."
        )

    if action in ["update_loan", "update_loan_status"]:
        return (
            f"I will update this loan:\n"
            f"- Person: {_format_value(action_data.get('person_name'))}\n"
            f"- Status: {_format_value(action_data.get('status'))}\n"
            f"- Amount: {_format_value(action_data.get('amount'))}\n"
            f"- Paid amount: {_format_value(action_data.get('paid_amount'))}\n\n"
            f"Please confirm, or correct anything."
        )

    if action == "delete_loan":
        return (
            f"I will delete this loan:\n"
            f"- Loan ID: {_format_value(action_data.get('loan_id'))}\n"
            f"- Person: {_format_value(action_data.get('person_name'))}\n\n"
            f"Please confirm, or correct anything."
        )

    return "Please confirm this loan action, or correct anything."


def _build_confirmation_message(extracted_action: dict[str, Any]) -> str:
    action = extracted_action.get("action")
    data = extracted_action.get("data") or {}

    if action == "create_expense":
        return _build_expense_confirmation(data)

    if action in ["create_category", "update_category", "delete_category"]:
        return _build_category_confirmation(action, data)

    if action in ["create_loan", "update_loan", "update_loan_status", "delete_loan"]:
        return _build_loan_confirmation(action, data)

    return (
        f"I understood this action:\n"
        f"- Action: {_format_value(action)}\n"
        f"- Data: {data}\n\n"
        f"Please confirm, or correct anything."
    )


# ============================================================
# BEFORE execution: prepare confirmation
# ============================================================

def confirmation_prepare_node(state: AgentState) -> AgentState:
    """
    Runs before tool execution.

    Mutating actions are not executed immediately.
    Instead, the action is saved in working memory and the user is asked
    to confirm or correct it.
    """

    extracted_action = state.get("extracted_action") or {}
    action = extracted_action.get("action")

    if not is_mutating_action(action):
        return {
            "validation": {
                "is_valid": True,
                "needs_user_clarification": False,
                "question": None,
            },
            "trace": append_trace(state, "ConfirmationPrepareNode"),
        }

    confirmation_message = _build_confirmation_message(extracted_action)

    return {
        "validation": {
            "is_valid": False,
            "needs_user_clarification": True,
            "awaiting_confirmation": True,
            "question": confirmation_message,
            "confirmation_action": extracted_action,
        },
        "trace": append_trace(state, "ConfirmationPrepareNode"),
    }


# ============================================================
# AFTER user says yes: approve saved action, do not execute yet
# ============================================================

def confirmation_handler_node(state: AgentState) -> AgentState:
    """
    Runs after the user confirms a saved action.

    Important:
    This node does NOT execute the backend tool.
    It only loads the saved confirmation_action from working memory and marks it
    as approved. The graph will then reload tool context, validate again,
    run conflict_check, and only then execute.
    """

    working_memory = state.get("loaded_working_memory") or {}
    confirmation_action = working_memory.get("confirmation_action")

    if not confirmation_action:
        return {
            "execution_result": {
                "status": "failed",
                "message": "There is no saved action to confirm.",
            },
            "trace": append_trace(state, "ConfirmationHandlerNode"),
        }

    # Special case saved by validation_node:
    # category missing, user approved creating it before adding the expense.
    if confirmation_action.get("type") == "create_missing_category_then_expense":
        original_action = confirmation_action.get("original_action") or {}
        prepared_action = {
            **original_action,
            "confirmed": True,
            "auto_create_missing_category": True,
            "missing_category_name": confirmation_action.get("category"),
        }
    else:
        prepared_action = {
            **confirmation_action,
            "confirmed": True,
        }

    return {
        "intent": "command",
        "extracted_action": prepared_action,
        "confirmation_approved": True,
        "validation": {
            "is_valid": True,
            "needs_user_clarification": False,
            "awaiting_confirmation": False,
            "confirmed": True,
            "question": None,
        },
        "trace": append_trace(state, "ConfirmationHandlerNode"),
    }


# ============================================================
# AFTER user says no/cancel: cancel memory
# ============================================================

def cancel_working_memory_node(state: AgentState) -> AgentState:
    return {
        "execution_result": {
            "status": "cancelled",
            "message": "Okay, I cancelled the unfinished action.",
        },
        "trace": append_trace(state, "CancelWorkingMemoryNode"),
    }
