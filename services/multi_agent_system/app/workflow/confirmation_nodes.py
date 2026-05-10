from app.graph.state import AgentState
from app.tools.expense_tool import expense_tool
from app.workflow.common import append_trace


def confirmation_execution_node(state: AgentState) -> AgentState:
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

    pending_type = confirmation_action.get("type")

    if pending_type != "create_missing_category_then_expense":
        return {
            "execution_result": {
                "status": "failed",
                "message": f"Unsupported confirmation action type: {pending_type}",
                "confirmation_action": confirmation_action,
            },
            "trace": append_trace(state, "ConfirmationExecutionNode"),
        }

    category_name = confirmation_action.get("category")
    original_action = confirmation_action.get("original_action", {})
    data = original_action.get("data") or {}

    try:
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
            "intent": "command",
            "extracted_action": original_action,
            "execution_result": {
                "status": "executed",
                "message": f'Category "{category_name}" created and transaction added successfully.',
                "created_category": created_category,
                "payload": payload,
                "created_expense": created_expense,
            },
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


def cancel_working_memory_node(state: AgentState) -> AgentState:
    return {
        "execution_result": {
            "status": "cancelled",
            "message": "Okay, I cancelled the unfinished action.",
        },
        "trace": append_trace(state, "CancelWorkingMemoryNode"),
    }