from typing import Any

from app.graph.state import AgentState
from app.tools.expense_tool import expense_tool
from app.tools.loan_tool import loan_tool
from app.workflow.common import append_trace


def _get_single_expense_match(tool_context: dict[str, Any]) -> dict[str, Any] | None:
    matched_expense = tool_context.get("matched_expense")

    if matched_expense:
        return matched_expense

    natural_matches = tool_context.get("expense_natural_matches", [])

    if len(natural_matches) == 1:
        return natural_matches[0]

    return None


def _get_single_loan_match(tool_context: dict[str, Any]) -> dict[str, Any] | None:
    matched_loan = tool_context.get("matched_loan")

    if matched_loan:
        return matched_loan

    natural_matches = tool_context.get("loan_natural_matches", [])

    if len(natural_matches) == 1:
        return natural_matches[0]

    return None


def tool_execution_node(state: AgentState) -> AgentState:
    extracted_action = state.get("extracted_action", {})
    tool_context = state.get("tool_context", {})
    auth_header = state.get("auth_header")

    action = extracted_action.get("action")
    data = extracted_action.get("data") or {}

    # =========================
    # List actions
    # =========================

    if action == "list_categories":
        return {
            "execution_result": {
                "status": "executed",
                "message": "Categories loaded successfully.",
                "categories": tool_context.get("categories", []),
            },
            "trace": append_trace(state, "ToolExecutionNode"),
        }

    if action == "list_expenses":
        return {
            "execution_result": {
                "status": "executed",
                "message": "Expenses loaded successfully.",
                "expenses": tool_context.get("expenses", []),
            },
            "trace": append_trace(state, "ToolExecutionNode"),
        }

    if action == "list_loans":
        return {
            "execution_result": {
                "status": "executed",
                "message": "Loans loaded successfully.",
                "loans": tool_context.get("loans", []),
            },
            "trace": append_trace(state, "ToolExecutionNode"),
        }

    # =========================
    # Category execution
    # =========================

    if action == "create_category":
        category_name = data.get("category") or data.get("category_name")

        try:
            created_category = expense_tool.create_category(
                name=category_name,
                auth_header=auth_header,
            )

            return {
                "execution_result": {
                    "status": "executed",
                    "message": f'Category "{category_name}" created successfully.',
                    "created_category": created_category,
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

        except Exception as exc:
            return {
                "execution_result": {
                    "status": "failed",
                    "message": f"Failed to create category: {exc}",
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

    if action == "update_category":
        matched_category = tool_context.get("matched_category")
        new_category = tool_context.get("new_category")

        try:
            updated_category = expense_tool.update_category(
                category_id=matched_category.get("id"),
                name=new_category,
                auth_header=auth_header,
            )

            return {
                "execution_result": {
                    "status": "executed",
                    "message": f'Category renamed to "{new_category}" successfully.',
                    "updated_category": updated_category,
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

        except Exception as exc:
            return {
                "execution_result": {
                    "status": "failed",
                    "message": f"Failed to update category: {exc}",
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

    if action == "delete_category":
        matched_category = tool_context.get("matched_category")

        try:
            deleted_category = expense_tool.delete_category(
                category_id=matched_category.get("id"),
                auth_header=auth_header,
            )

            return {
                "execution_result": {
                    "status": "executed",
                    "message": f'Category "{matched_category.get("name")}" deleted successfully.',
                    "deleted_category": deleted_category,
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

        except Exception as exc:
            return {
                "execution_result": {
                    "status": "failed",
                    "message": f"Failed to delete category: {exc}",
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

    # =========================
    # Expense execution
    # =========================

    if action == "create_expense":
        matched_category = tool_context.get("matched_category")

        if not matched_category and extracted_action.get("auto_create_missing_category"):
            category_name = (
                extracted_action.get("missing_category_name")
                or data.get("missing_category_name")
                or data.get("category")
                or data.get("category_name")
            )

            if not category_name:
                return {
                    "execution_result": {
                        "status": "blocked",
                        "message": "Cannot create missing category because category name is missing.",
                    },
                    "trace": append_trace(state, "ToolExecutionNode"),
                }

            try:
                matched_category = expense_tool.create_category(
                    name=category_name,
                    auth_header=auth_header,
                )
            except Exception as exc:
                return {
                    "execution_result": {
                        "status": "failed",
                        "message": f"Failed to create missing category before expense: {exc}",
                    },
                    "trace": append_trace(state, "ToolExecutionNode"),
                }

        if not matched_category:
            return {
                "execution_result": {
                    "status": "blocked",
                    "message": "Cannot create expense because category was not matched.",
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

        payload = {
            "description": data.get("description"),
            "type": data.get("type", "outcome"),
            "amount": data.get("amount"),
            "transaction_date": data.get("transaction_date"),
            "category_id": matched_category.get("id"),
        }

        try:
            created_expense = expense_tool.create_expense(
                payload=payload,
                auth_header=auth_header,
            )

            return {
                "execution_result": {
                    "status": "executed",
                    "message": "Expense created successfully.",
                    "payload": payload,
                    "created_expense": created_expense,
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

        except Exception as exc:
            return {
                "execution_result": {
                    "status": "failed",
                    "message": f"Failed to create expense: {exc}",
                    "payload": payload,
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

    if action == "update_expense":
        matched_expense = _get_single_expense_match(tool_context)

        payload = {}

        for field in ["description", "type", "amount", "transaction_date"]:
            if data.get(field) is not None:
                payload[field] = data.get(field)

        if data.get("category"):
            matched_category = expense_tool.find_category_by_name(
                categories=tool_context.get("categories", []),
                category_name=data.get("category"),
            )

            if matched_category:
                payload["category_id"] = matched_category.get("id")

        try:
            updated_expense = expense_tool.update_expense(
                expense_id=matched_expense.get("id"),
                payload=payload,
                auth_header=auth_header,
            )

            return {
                "execution_result": {
                    "status": "executed",
                    "message": "Expense updated successfully.",
                    "payload": payload,
                    "updated_expense": updated_expense,
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

        except Exception as exc:
            return {
                "execution_result": {
                    "status": "failed",
                    "message": f"Failed to update expense: {exc}",
                    "payload": payload,
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

    if action == "delete_expense":
        matched_expense = _get_single_expense_match(tool_context)

        try:
            deleted_expense = expense_tool.delete_expense(
                expense_id=matched_expense.get("id"),
                auth_header=auth_header,
            )

            return {
                "execution_result": {
                    "status": "executed",
                    "message": "Expense deleted successfully.",
                    "deleted_expense": deleted_expense,
                    "matched_expense": matched_expense,
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

        except Exception as exc:
            return {
                "execution_result": {
                    "status": "failed",
                    "message": f"Failed to delete expense: {exc}",
                    "matched_expense": matched_expense,
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

    # =========================
    # Loan execution
    # =========================

    if action == "create_loan":
        payload = {
            "person_name": data.get("person_name"),
            "type": data.get("type"),
            "amount": data.get("amount"),
            "date_created": data.get("date_created"),
            "return_date": data.get("return_date"),
            "status": data.get("status", "unpaid"),
            "notes": data.get("notes"),
        }

        payload = {
            key: value
            for key, value in payload.items()
            if value is not None
        }

        try:
            created_loan = loan_tool.create_loan(
                payload=payload,
                auth_header=auth_header,
            )

            return {
                "execution_result": {
                    "status": "executed",
                    "message": "Loan created successfully.",
                    "payload": payload,
                    "created_loan": created_loan,
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

        except Exception as exc:
            return {
                "execution_result": {
                    "status": "failed",
                    "message": f"Failed to create loan: {exc}",
                    "payload": payload,
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

    if action == "update_loan":
        matched_loan = _get_single_loan_match(tool_context)

        payload = {}

        for field in [
            "person_name",
            "type",
            "amount",
            "date_created",
            "return_date",
            "status",
            "paid_amount",
            "last_payment_date",
            "notes",
        ]:
            if data.get(field) is not None:
                payload[field] = data.get(field)

        try:
            updated_loan = loan_tool.update_loan(
                loan_id=matched_loan.get("id"),
                payload=payload,
                auth_header=auth_header,
            )

            return {
                "execution_result": {
                    "status": "executed",
                    "message": "Loan updated successfully.",
                    "payload": payload,
                    "updated_loan": updated_loan,
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

        except Exception as exc:
            return {
                "execution_result": {
                    "status": "failed",
                    "message": f"Failed to update loan: {exc}",
                    "payload": payload,
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

    if action == "update_loan_status":
        matched_loan = _get_single_loan_match(tool_context)

        try:
            updated_loan = loan_tool.update_loan_status(
                loan_id=matched_loan.get("id"),
                status=data.get("status"),
                paid_amount=data.get("paid_amount"),
                last_payment_date=data.get("last_payment_date"),
                auth_header=auth_header,
            )

            return {
                "execution_result": {
                    "status": "executed",
                    "message": "Loan status updated successfully.",
                    "updated_loan": updated_loan,
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

        except Exception as exc:
            return {
                "execution_result": {
                    "status": "failed",
                    "message": f"Failed to update loan status: {exc}",
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

    if action == "delete_loan":
        matched_loan = _get_single_loan_match(tool_context)

        try:
            deleted_loan = loan_tool.delete_loan(
                loan_id=matched_loan.get("id"),
                auth_header=auth_header,
            )

            return {
                "execution_result": {
                    "status": "executed",
                    "message": "Loan deleted successfully.",
                    "deleted_loan": deleted_loan,
                    "matched_loan": matched_loan,
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

        except Exception as exc:
            return {
                "execution_result": {
                    "status": "failed",
                    "message": f"Failed to delete loan: {exc}",
                    "matched_loan": matched_loan,
                },
                "trace": append_trace(state, "ToolExecutionNode"),
            }

    return {
        "execution_result": {
            "status": "dry_run",
            "message": "This action is understood but real execution is not connected yet.",
            "planned_action": extracted_action,
        },
        "trace": append_trace(state, "ToolExecutionNode"),
    }