from __future__ import annotations

from typing import Any

from app.graph.state import AgentState
from app.tools.expense_tool import expense_tool
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
# AFTER confirmation: execution helpers
# ============================================================

def _execute_create_expense(
    action: dict[str, Any],
    auth_header: str | None,
) -> dict[str, Any]:
    data = action.get("data") or {}
    category_name = _get_category_name(data)

    categories = expense_tool.list_categories(auth_header)

    matched_category = expense_tool.find_category_by_name(
        categories=categories,
        category_name=category_name,
    )

    if not matched_category:
        raise RuntimeError(f'Category "{category_name}" does not exist.')

    payload = {
        "description": data.get("description"),
        "type": data.get("type", "outcome"),
        "amount": data.get("amount"),
        "transaction_date": data.get("transaction_date"),
        "category_id": matched_category.get("id"),
    }

    created_expense = expense_tool.create_expense(
        payload=payload,
        auth_header=auth_header,
    )

    return {
        "status": "executed",
        "message": "Transaction added successfully.",
        "payload": payload,
        "created_expense": created_expense,
    }


def _execute_create_category(
    action: dict[str, Any],
    auth_header: str | None,
) -> dict[str, Any]:
    data = action.get("data") or {}
    category_name = _get_category_name(data)

    if not category_name:
        raise RuntimeError("Category name is missing.")

    created_category = expense_tool.create_category(
        name=category_name,
        auth_header=auth_header,
    )

    return {
        "status": "executed",
        "message": f'Category "{category_name}" created successfully.',
        "created_category": created_category,
    }


def _execute_delete_category(
    action: dict[str, Any],
    auth_header: str | None,
) -> dict[str, Any]:
    data = action.get("data") or {}
    category_name = _get_category_name(data)

    if not category_name:
        raise RuntimeError("Category name is missing.")

    categories = expense_tool.list_categories(auth_header)

    matched_category = expense_tool.find_category_by_name(
        categories=categories,
        category_name=category_name,
    )

    if not matched_category:
        raise RuntimeError(f'Category "{category_name}" does not exist.')

    deleted_category = expense_tool.delete_category(
        category_id=matched_category.get("id"),
        auth_header=auth_header,
    )

    return {
        "status": "executed",
        "message": f'Category "{category_name}" deleted successfully.',
        "deleted_category": deleted_category,
    }


def _execute_create_missing_category_then_expense(
    confirmation_action: dict[str, Any],
    auth_header: str | None,
) -> dict[str, Any]:
    category_name = confirmation_action.get("category")
    original_action = confirmation_action.get("original_action", {})
    data = original_action.get("data") or {}

    if not category_name:
        category_name = _get_category_name(data)

    if not category_name:
        raise RuntimeError("Category name is missing.")

    categories = expense_tool.list_categories(auth_header)

    matched_category = expense_tool.find_category_by_name(
        categories=categories,
        category_name=category_name,
    )

    if matched_category:
        created_category = matched_category
    else:
        created_category = expense_tool.create_category(
            name=category_name,
            auth_header=auth_header,
        )

    payload = {
        "description": data.get("description"),
        "type": data.get("type", "outcome"),
        "amount": data.get("amount"),
        "transaction_date": data.get("transaction_date"),
        "category_id": created_category.get("id"),
    }

    created_expense = expense_tool.create_expense(
        payload=payload,
        auth_header=auth_header,
    )

    return {
        "status": "executed",
        "message": f'Category "{category_name}" created and transaction added successfully.',
        "created_category": created_category,
        "payload": payload,
        "created_expense": created_expense,
    }


# ============================================================
# AFTER user says yes: execute confirmed action
# ============================================================

def confirmation_execution_node(state: AgentState) -> AgentState:
    """
    Runs after user confirms.

    Reads confirmation_action from unified working memory and executes it.
    """

    working_memory = state.get("loaded_working_memory") or {}
    confirmation_action = working_memory.get("confirmation_action")
    auth_header = state.get("auth_header")

    if not confirmation_action:
        return {
            "execution_result": {
                "status": "failed",
                "message": "There is no saved action to confirm.",
            },
            "trace": append_trace(state, "ConfirmationExecutionNode"),
        }

    try:
        confirmation_type = confirmation_action.get("type")

        # Special case:
        # Category does not exist, user confirmed to create category first.
        if confirmation_type == "create_missing_category_then_expense":
            original_action = confirmation_action.get("original_action", {})

            execution_result = _execute_create_missing_category_then_expense(
                confirmation_action=confirmation_action,
                auth_header=auth_header,
            )

            return {
                "intent": "command",
                "extracted_action": original_action,
                "execution_result": execution_result,
                "trace": append_trace(state, "ConfirmationExecutionNode"),
            }

        # Normal confirmation:
        # confirmation_action is the prepared extracted_action.
        action = confirmation_action.get("action")

        if action == "create_expense":
            execution_result = _execute_create_expense(
                action=confirmation_action,
                auth_header=auth_header,
            )

        elif action == "create_category":
            execution_result = _execute_create_category(
                action=confirmation_action,
                auth_header=auth_header,
            )

        elif action == "delete_category":
            execution_result = _execute_delete_category(
                action=confirmation_action,
                auth_header=auth_header,
            )

        else:
            execution_result = {
                "status": "failed",
                "message": f"Confirmed action is not executable yet: {action}",
                "confirmation_action": confirmation_action,
            }

        return {
            "intent": "command",
            "extracted_action": confirmation_action,
            "execution_result": execution_result,
            "trace": append_trace(state, "ConfirmationExecutionNode"),
        }

    except Exception as exc:
        return {
            "execution_result": {
                "status": "failed",
                "message": f"Failed to execute confirmed action: {exc}",
                "confirmation_action": confirmation_action,
            },
            "errors": [*state.get("errors", []), f"Confirmation failed: {exc}"],
            "trace": append_trace(state, "ConfirmationExecutionNode"),
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