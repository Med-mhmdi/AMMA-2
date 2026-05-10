import re
from datetime import date
from typing import Any

from app.agents.base_agent import safe_llm_json


SUPPORTED_ACTIONS = {
    "create_expense",
    "update_expense",
    "delete_expense",
    "list_expenses",
    "create_category",
    "update_category",
    "delete_category",
    "list_categories",
    "create_loan",
    "update_loan",
    "update_loan_status",
    "delete_loan",
    "list_loans",
    "unknown",
}


REQUIRED_FIELDS_BY_ACTION = {
    "create_expense": ["description", "type", "amount", "transaction_date", "category"],
    "update_expense": [],
    "delete_expense": [],
    "list_expenses": [],
    "create_category": ["category"],
    "update_category": [],
    "delete_category": ["category"],
    "list_categories": [],
    "create_loan": ["person_name", "type", "amount", "date_created"],
    "update_loan": [],
    "update_loan_status": ["person_name", "status"],
    "delete_loan": [],
    "list_loans": [],
}


READ_ONLY_ACTIONS = {
    "list_expenses",
    "list_categories",
    "list_loans",
}


def fallback_command_from_message(message: str) -> dict[str, Any]:
    text = message.lower()
    numbers = re.findall(r"\d+(?:\.\d+)?", text)
    amount = float(numbers[-1]) if numbers else None

    if amount is not None and amount.is_integer():
        amount = int(amount)

    data = {
        "raw_message": message,
    }

    if amount is not None:
        data["amount"] = amount

    return {
        "action": "unknown",
        "requires_confirmation": True,
        "missing_fields": ["action"],
        "data": data,
        "explanation": "The LLM could not extract a complete financial action.",
    }


def normalize_action_result(result: dict[str, Any]) -> dict[str, Any]:
    action = result.get("action", "unknown")

    if action not in SUPPORTED_ACTIONS:
        action = "unknown"

    requires_confirmation = result.get("requires_confirmation", True)

    if not isinstance(requires_confirmation, bool):
        requires_confirmation = True

    data = result.get("data") or {}

    if not isinstance(data, dict):
        data = {}

    missing_fields = result.get("missing_fields", [])

    if not isinstance(missing_fields, list):
        missing_fields = []

    explanation = result.get("explanation", "")

    return {
        "action": action,
        "requires_confirmation": requires_confirmation,
        "missing_fields": missing_fields,
        "data": data,
        "explanation": str(explanation),
    }


def normalize_data_fields(result: dict[str, Any]) -> dict[str, Any]:
    data = result.get("data") or {}

    if data.get("category_name") and not data.get("category"):
        data["category"] = data.get("category_name")

    if data.get("old_category_name") and not data.get("old_category"):
        data["old_category"] = data.get("old_category_name")

    if data.get("new_category_name") and not data.get("new_category"):
        data["new_category"] = data.get("new_category_name")

    if data.get("date") and not data.get("transaction_date"):
        data["transaction_date"] = data.get("date")

    if data.get("loan_date") and not data.get("date_created"):
        data["date_created"] = data.get("loan_date")

    if data.get("expense_description") and not data.get("description"):
        data["description"] = data.get("expense_description")

    if data.get("loan_person") and not data.get("person_name"):
        data["person_name"] = data.get("loan_person")

    if data.get("person") and not data.get("person_name"):
        data["person_name"] = data.get("person")

    if data.get("amount") is not None:
        try:
            amount = float(data["amount"])
            data["amount"] = int(amount) if amount.is_integer() else amount
        except (TypeError, ValueError):
            pass

    result["data"] = data
    return result


def recalculate_missing_fields(result: dict[str, Any]) -> dict[str, Any]:
    action = result.get("action", "unknown")
    data = result.get("data") or {}

    required_fields = REQUIRED_FIELDS_BY_ACTION.get(action, [])

    missing_fields = [
        field
        for field in required_fields
        if data.get(field) in [None, "", []]
    ]

    # Amount 0 should count as missing for create_expense/create_loan.
    if action in ["create_expense", "create_loan"]:
        if data.get("amount") in [0, 0.0]:
            if "amount" not in missing_fields:
                missing_fields.append("amount")

    result["missing_fields"] = missing_fields
    result["data"] = data

    if action in READ_ONLY_ACTIONS:
        result["requires_confirmation"] = False

    return result


def _build_memory_context(working_memory: dict[str, Any] | None) -> str:
    if not working_memory:
        return "No previous working memory."

    messages = working_memory.get("messages", [])
    current_action = working_memory.get("current_action")
    confirmation_action = working_memory.get("confirmation_action")
    awaiting_confirmation = working_memory.get("awaiting_confirmation")

    return f"""
Previous unresolved conversation messages:
{messages}

Current unfinished action:
{current_action}

Saved confirmation action:
{confirmation_action}

Awaiting confirmation:
{awaiting_confirmation}

Last question:
{working_memory.get("last_question")}
"""


def repair_command_with_llm(
    message: str,
    current_result: dict[str, Any],
    working_memory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    memory_context = _build_memory_context(working_memory)

    prompt = f"""
    You are the CommandRepairAgent for AMMA.

    Your job:
    Repair or complete an existing command JSON using:
    1. previous working memory
    2. current user message
    3. current incomplete JSON

    Rules:
    - Return ONLY valid JSON.
    - Do NOT execute anything.
    - Use previous unfinished action when the user provides missing information.
    - Keep previous description/date/category/amount unless user clearly changes them.
    - If user says something is food, category is Food.
    - If user says something is work/job/presentation income, category is Work.
    - If normal purchase/payment, type is outcome.
    - If user received/got money, type is income.
    - If required field is truly unavailable, keep it in missing_fields.

    CRITICAL RULE FOR CONFIRMATION CORRECTION:
    If Working memory says "Awaiting confirmation: True", the assistant has already prepared an action and is waiting for the user to confirm or correct it.

    In that case:
    - If the user gives corrected information, modify the saved confirmation action.
    - Do NOT change create_expense into update_expense.
    - Do NOT treat the correction as editing an existing database record.
    - Return the SAME original action type from the saved confirmation action.

    Examples of correction messages:
    - "no, it cost 92"
    - "no the cost is 92"
    - "the amount is 92"
    - "actually category is Food"
    - "not Transport, it is Food"
    - "change it to 250"
    - "description should be university bus round trip"

    Example:

    Saved confirmation action:
    {{
      "action": "create_expense",
      "data": {{
        "description": "Bus fare to university",
        "type": "outcome",
        "amount": 46,
        "transaction_date": "2026-05-10",
        "category": "Transport"
      }}
    }}

    User message:
    "no, it cost 92 total"

    Correct output:
    {{
      "action": "create_expense",
      "requires_confirmation": true,
      "missing_fields": [],
      "data": {{
        "description": "Bus fare to university",
        "type": "outcome",
        "amount": 92,
        "transaction_date": "2026-05-10",
        "category": "Transport"
      }},
      "explanation": "Updated the prepared expense amount before confirmation."
    }}

    Wrong output:
    {{
      "action": "update_expense",
      "data": {{
        "amount": 92
      }}
    }}

    Only use update_expense when the user clearly wants to edit an expense that already exists in the database, for example:
    - "update expense id 14"
    - "edit my previous transaction"
    - "change the old expense from yesterday"
    - "modify existing expense"

    Today:
    {date.today().isoformat()}

    Working memory:
    {memory_context}

    Current user message:
    {message}

    Current incomplete JSON:
    {current_result}

    Return JSON:
    {{
      "action": "create_expense | update_expense | delete_expense | list_expenses | create_category | update_category | delete_category | list_categories | create_loan | update_loan | update_loan_status | delete_loan | list_loans | unknown",
      "requires_confirmation": true,
      "missing_fields": [],
      "data": {{}},
      "explanation": "short explanation"
    }}
    """

    repaired = safe_llm_json(prompt, current_result)
    repaired = normalize_action_result(repaired)
    repaired = normalize_data_fields(repaired)
    repaired = recalculate_missing_fields(repaired)

    return repaired


def extract_command(
    message: str,
    working_memory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    memory_context = _build_memory_context(working_memory)

    prompt = f"""
    You are the CommandAgent for AMMA, an AI Money Management Assistant.

    Your job:
    Convert the user's natural language message into exactly one structured financial action.

    Important:
    - Use working memory if the current user message completes a previous unfinished action.
    - Use saved confirmation action if the user is correcting an action that AMMA already prepared.
    - Return ONLY valid JSON.
    - Do not execute anything.

    CRITICAL RULE FOR CONFIRMATION CORRECTION:
    If Working memory says "Awaiting confirmation: True", the assistant has already prepared an action and is waiting for the user to confirm or correct it.

    In that case:
    - If the user gives corrected information, modify the saved confirmation action.
    - Do NOT change create_expense into update_expense.
    - Do NOT treat the correction as editing an existing database record.
    - Return the SAME original action type from the saved confirmation action.
    - Keep all previous saved fields unless the user clearly changes them.

    Correction examples:
    - "no, it cost 92"
    - "no the cost is 92"
    - "the amount is 92"
    - "actually category is Food"
    - "not Transport, it is Food"
    - "change it to 250"
    - "description should be university bus round trip"

    Example:

    Saved confirmation action:
    {{
      "action": "create_expense",
      "data": {{
        "description": "Bus fare to university",
        "type": "outcome",
        "amount": 46,
        "transaction_date": "2026-05-10",
        "category": "Transport"
      }}
    }}

    User message:
    "no, it cost 92 total"

    Correct output:
    {{
      "action": "create_expense",
      "requires_confirmation": true,
      "missing_fields": [],
      "data": {{
        "description": "Bus fare to university",
        "type": "outcome",
        "amount": 92,
        "transaction_date": "2026-05-10",
        "category": "Transport"
      }},
      "explanation": "Updated the prepared expense amount before confirmation."
    }}

    Wrong output:
    {{
      "action": "update_expense",
      "data": {{
        "amount": 92
      }}
    }}

    Only use update_expense when the user clearly wants to edit an expense that already exists in the database, for example:
    - "update expense id 14"
    - "edit my previous transaction"
    - "change the old expense from yesterday"
    - "modify existing expense"

    Normal incomplete-action example:
    If the user previously said "add blabla to expense" and now says "it is food and cost 250",
    create a complete create_expense action using:
    - description = blabla
    - category = Food
    - amount = 250

    Supported actions:
    1. create_expense
    2. update_expense
    3. delete_expense
    4. list_expenses
    5. create_category
    6. update_category
    7. delete_category
    8. list_categories
    9. create_loan
    10. update_loan
    11. update_loan_status
    12. delete_loan
    13. list_loans
    14. unknown

    Rules for expenses:
    - Expense module stores both income and outcome transactions.
    - For normal purchase/payment, type is outcome.
    - For salary, received money, earnings, got money, type is income.
    - Use transaction_date.
    - If no date is mentioned, use today's date.
    - If user says food, category is Food.
    - If user says coffee, category is Coffee.
    - If user says bus/taxi/metro/transport, category is Transport.
    - If user says work/job/presentation income, category is Work.
    - Description must be short and clean.
    - If the user says "went and came back", "round trip", "both ways", or "each way", calculate the total amount if possible.
      Example: "it cost 46 each, I went and came back" means amount = 92.

    Rules for categories:
    - "create category Books" -> create_category with category Books.
    - "rename Food to Groceries" -> update_category with old_category and new_category.

    Rules for loans:
    - "I lent Ahmed 500" -> create_loan type lent, person_name Ahmed.
    - "I borrowed 500 from Ahmed" -> create_loan type borrowed, person_name Ahmed.
    - "Ahmed paid me back" -> update_loan_status status paid.

    Required fields:
    create_expense: description, type, amount, transaction_date, category
    create_category: category
    delete_category: category
    create_loan: person_name, type, amount, date_created
    update_loan_status: person_name, status

    Working memory:
    {memory_context}

    Today:
    {date.today().isoformat()}

    Current user message:
    {message}

    Return JSON:
    {{
      "action": "create_expense | update_expense | delete_expense | list_expenses | create_category | update_category | delete_category | list_categories | create_loan | update_loan | update_loan_status | delete_loan | list_loans | unknown",
      "requires_confirmation": true,
      "missing_fields": [],
      "data": {{
        "expense_id": 0,
        "description": "short description",
        "type": "income | outcome | lent | borrowed",
        "amount": 0,
        "transaction_date": "YYYY-MM-DD",
        "category": "category name",
        "old_category": "old category name",
        "new_category": "new category name",
        "category_id": 0,
        "loan_id": 0,
        "person_name": "person name",
        "date_created": "YYYY-MM-DD",
        "return_date": "YYYY-MM-DD",
        "status": "unpaid | partially_paid | paid | overdue",
        "notes": "optional notes"
      }},
      "explanation": "short explanation"
    }}
    """

    fallback = {
        "action": "unknown",
        "requires_confirmation": True,
        "missing_fields": ["action"],
        "data": {},
        "explanation": "Could not understand the command.",
    }

    result = safe_llm_json(prompt, fallback)
    result = normalize_action_result(result)
    result = normalize_data_fields(result)

    if result.get("action") == "unknown":
        result = fallback_command_from_message(message)
        result = normalize_action_result(result)
        result = normalize_data_fields(result)

    result = recalculate_missing_fields(result)

    if result.get("action") != "unknown" and result.get("missing_fields"):
        result = repair_command_with_llm(
            message=message,
            current_result=result,
            working_memory=working_memory,
        )

    if result.get("action") in READ_ONLY_ACTIONS:
        result["requires_confirmation"] = False

    return result