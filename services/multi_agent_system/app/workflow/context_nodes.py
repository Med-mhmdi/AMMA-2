from typing import Any

from app.graph.state import AgentState
from app.tools.expense_tool import expense_tool
from app.tools.loan_tool import loan_tool
from app.workflow.common import append_trace


def tool_context_node(state: AgentState) -> AgentState:
    """
    Loads real backend context before validation/execution.

    This node does not execute mutations.
    It only reads categories, expenses, or loans and prepares matches.
    """

    extracted_action = state.get("extracted_action", {})
    action = extracted_action.get("action")
    data = extracted_action.get("data") or {}
    auth_header = state.get("auth_header")

    context: dict[str, Any] = {
        "action": action,
        "service_context_loaded": False,
    }

    expense_actions = {
        "create_expense",
        "update_expense",
        "delete_expense",
        "list_expenses",
        "create_category",
        "update_category",
        "delete_category",
        "list_categories",
    }

    loan_actions = {
        "create_loan",
        "update_loan",
        "update_loan_status",
        "delete_loan",
        "list_loans",
    }

    if action in expense_actions:
        try:
            categories = expense_tool.list_categories(auth_header)

            context.update(
                {
                    "service": "expense_service",
                    "service_context_loaded": True,
                    "categories": categories,
                }
            )

            if action in ["create_expense", "delete_category"]:
                category_name = data.get("category") or data.get("category_name")
                matched_category = expense_tool.find_category_by_name(
                    categories=categories,
                    category_name=category_name,
                )

                context.update(
                    {
                        "requested_category": category_name,
                        "matched_category": matched_category,
                        "category_exists": matched_category is not None,
                    }
                )

            if action == "create_category":
                category_name = data.get("category") or data.get("category_name")
                matched_category = expense_tool.find_category_by_name(
                    categories=categories,
                    category_name=category_name,
                )

                context.update(
                    {
                        "requested_category": category_name,
                        "matched_category": matched_category,
                        "category_exists": matched_category is not None,
                    }
                )

            if action == "update_category":
                old_category = data.get("old_category") or data.get("category")
                new_category = data.get("new_category") or data.get("new_name")

                matched_category = expense_tool.find_category_by_name(
                    categories=categories,
                    category_name=old_category,
                )

                context.update(
                    {
                        "requested_category": old_category,
                        "new_category": new_category,
                        "matched_category": matched_category,
                        "category_exists": matched_category is not None,
                    }
                )

            if action in ["update_expense", "delete_expense", "list_expenses"]:
                expenses = expense_tool.list_expenses(auth_header)

                expense_id = data.get("expense_id") or data.get("id")
                matched_expense = expense_tool.find_expense_by_id(
                    expenses=expenses,
                    expense_id=expense_id,
                )

                natural_matches = expense_tool.find_expenses_by_natural_match(
                    expenses=expenses,
                    data=data,
                )

                context.update(
                    {
                        "expenses": expenses,
                        "requested_expense_id": expense_id,
                        "matched_expense": matched_expense,
                        "expense_natural_matches": natural_matches,
                        "expense_match_count": len(natural_matches),
                    }
                )

        except Exception as exc:
            context.update(
                {
                    "service": "expense_service",
                    "service_context_loaded": False,
                    "error": str(exc),
                }
            )

    elif action in loan_actions:
        try:
            loans = loan_tool.list_loans(auth_header)

            loan_id = data.get("loan_id") or data.get("id")
            matched_loan = loan_tool.find_loan_by_id(
                loans=loans,
                loan_id=loan_id,
            )

            natural_matches = loan_tool.find_loans_by_natural_match(
                loans=loans,
                data=data,
            )

            context.update(
                {
                    "service": "loan_service",
                    "service_context_loaded": True,
                    "loans": loans,
                    "requested_loan_id": loan_id,
                    "matched_loan": matched_loan,
                    "loan_natural_matches": natural_matches,
                    "loan_match_count": len(natural_matches),
                }
            )

        except Exception as exc:
            context.update(
                {
                    "service": "loan_service",
                    "service_context_loaded": False,
                    "error": str(exc),
                }
            )

    return {
        "tool_context": context,
        "trace": append_trace(state, "ToolContextNode"),
    }