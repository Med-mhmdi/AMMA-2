from app.graph.state import AgentState
from app.tools.tool_specs import EXPENSE_TOOL_SPECS, LOAN_TOOL_SPECS
from app.workflow.common import append_trace


def validation_node(state: AgentState) -> AgentState:
    extracted_action = state.get("extracted_action", {})
    vision_result = state.get("vision_result", {})
    tool_context = state.get("tool_context", {})

    if vision_result.get("needs_user_clarification"):
        return {
            "validation": {
                "is_valid": False,
                "needs_user_clarification": True,
                "question": vision_result.get("question"),
            },
            "trace": append_trace(state, "ValidationNode"),
        }

    action = extracted_action.get("action")
    data = extracted_action.get("data") or {}
    confirmed = bool(state.get("confirmation_approved") or extracted_action.get("confirmed"))

    if not action or action == "unknown":
        return {
            "validation": {
                "is_valid": False,
                "needs_user_clarification": True,
                "question": (
                    "I could not understand the financial action clearly. "
                    "Please give me more details."
                ),
            },
            "trace": append_trace(state, "ValidationNode"),
        }

    if data.get("date") and not data.get("transaction_date"):
        data["transaction_date"] = data.get("date")

    if action == "create_expense":
        data.setdefault("type", "outcome")

    all_specs = {
        **EXPENSE_TOOL_SPECS,
        **LOAN_TOOL_SPECS,
    }

    spec = all_specs.get(action)

    if spec:
        missing_fields = []

        for field in spec["required_fields"]:
            if data.get(field) in [None, "", []]:
                missing_fields.append(field)

        if action in ["create_expense", "create_loan"]:
            if data.get("amount") in [0, 0.0]:
                if "amount" not in missing_fields:
                    missing_fields.append("amount")

        if missing_fields:
            return {
                "extracted_action": {
                    **extracted_action,
                    "data": data,
                    "missing_fields": missing_fields,
                },
                "validation": {
                    "is_valid": False,
                    "needs_user_clarification": True,
                    "question": f"I need more information: {', '.join(missing_fields)}.",
                    "missing_fields": missing_fields,
                },
                "trace": append_trace(state, "ValidationNode"),
            }

    expense_service_actions = {
        "create_expense",
        "update_expense",
        "delete_expense",
        "list_expenses",
        "create_category",
        "update_category",
        "delete_category",
        "list_categories",
    }

    loan_service_actions = {
        "create_loan",
        "update_loan",
        "update_loan_status",
        "delete_loan",
        "list_loans",
    }

    if action in expense_service_actions or action in loan_service_actions:
        if not tool_context.get("service_context_loaded"):
            return {
                "validation": {
                    "is_valid": False,
                    "needs_user_clarification": True,
                    "question": (
                        f"I could not check the real backend service. "
                        f"Error: {tool_context.get('error')}"
                    ),
                },
                "trace": append_trace(state, "ValidationNode"),
            }

    if action == "create_category":
        if tool_context.get("category_exists"):
            return {
                "validation": {
                    "is_valid": False,
                    "needs_user_clarification": True,
                    "question": f'The category "{tool_context.get("requested_category")}" already exists.',
                },
                "trace": append_trace(state, "ValidationNode"),
            }

    if action == "delete_category":
        requested_category = tool_context.get("requested_category")

        if not tool_context.get("category_exists"):
            return {
                "validation": {
                    "is_valid": False,
                    "needs_user_clarification": True,
                    "question": f'The category "{requested_category}" does not exist, so I cannot delete it.',
                },
                "trace": append_trace(state, "ValidationNode"),
            }

    if action == "update_category":
        old_category = tool_context.get("requested_category")
        new_category = tool_context.get("new_category")

        if not old_category or not new_category:
            return {
                "validation": {
                    "is_valid": False,
                    "needs_user_clarification": True,
                    "question": "I need the old category name and the new category name.",
                },
                "trace": append_trace(state, "ValidationNode"),
            }

        if not tool_context.get("category_exists"):
            return {
                "validation": {
                    "is_valid": False,
                    "needs_user_clarification": True,
                    "question": f'The category "{old_category}" does not exist.',
                },
                "trace": append_trace(state, "ValidationNode"),
            }

    if action == "create_expense":
        requested_category = tool_context.get("requested_category")

        if extracted_action.get("auto_create_missing_category"):
            data["auto_create_missing_category"] = True
            data["missing_category_name"] = extracted_action.get("missing_category_name") or requested_category

        elif not tool_context.get("category_exists"):
            confirmation_action = {
                "type": "create_missing_category_then_expense",
                "category": requested_category,
                "original_action": {
                    **extracted_action,
                    "data": data,
                },
            }

            return {
                "extracted_action": {
                    **extracted_action,
                    "data": data,
                },
                "validation": {
                    "is_valid": False,
                    "needs_user_clarification": True,
                    "awaiting_confirmation": True,
                    "question": (
                        f'The category "{requested_category}" does not exist. '
                        f"Do you want me to create it first and then add the transaction?"
                    ),
                    "confirmation_action": confirmation_action,
                },
                "trace": append_trace(state, "ValidationNode"),
            }

    if action in ["update_expense", "delete_expense"]:
        matched_expense = tool_context.get("matched_expense")
        natural_matches = tool_context.get("expense_natural_matches", [])

        if not matched_expense and len(natural_matches) == 0:
            return {
                "validation": {
                    "is_valid": False,
                    "needs_user_clarification": True,
                    "question": "I could not find a matching expense. Please provide the expense ID or more details.",
                },
                "trace": append_trace(state, "ValidationNode"),
            }

        if not matched_expense and len(natural_matches) > 1:
            return {
                "validation": {
                    "is_valid": False,
                    "needs_user_clarification": True,
                    "question": "I found multiple matching expenses. Please provide the exact expense ID.",
                    "matches": natural_matches[:5],
                },
                "trace": append_trace(state, "ValidationNode"),
            }

    if action in ["update_loan", "update_loan_status", "delete_loan"]:
        matched_loan = tool_context.get("matched_loan")
        natural_matches = tool_context.get("loan_natural_matches", [])

        if not matched_loan and len(natural_matches) == 0:
            return {
                "validation": {
                    "is_valid": False,
                    "needs_user_clarification": True,
                    "question": "I could not find a matching loan. Please provide the loan ID or more details.",
                },
                "trace": append_trace(state, "ValidationNode"),
            }

        if not matched_loan and len(natural_matches) > 1:
            return {
                "validation": {
                    "is_valid": False,
                    "needs_user_clarification": True,
                    "question": "I found multiple matching loans. Please provide the exact loan ID.",
                    "matches": natural_matches[:5],
                },
                "trace": append_trace(state, "ValidationNode"),
            }

    return {
        "extracted_action": {
            **extracted_action,
            "data": data,
        },
        "validation": {
            "is_valid": True,
            "needs_user_clarification": False,
            "confirmed": confirmed,
            "question": None,
        },
        "trace": append_trace(state, "ValidationNode"),
    }