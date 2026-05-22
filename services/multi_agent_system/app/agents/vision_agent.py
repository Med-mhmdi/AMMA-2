from __future__ import annotations

import base64
import re
from typing import Any

import httpx

from app.agents.command_agent import (
    normalize_action_result,
    normalize_data_fields,
    recalculate_missing_fields,
)
from app.providers.llm_provider import ollama_client
from app.workflow.date_utils import get_today_iso


def _clean_base64(image_base64: str | None) -> str | None:
    """
    Accepts either pure base64 or a browser data URL:
    data:image/png;base64,xxxx
    """

    if not image_base64:
        return None

    image_base64 = image_base64.strip()

    if "," in image_base64 and image_base64.startswith("data:image"):
        return image_base64.split(",", 1)[1].strip()

    return image_base64


def _image_url_to_base64(image_url: str) -> str:
    """
    Downloads an image URL and converts it to base64.

    The main frontend flow should use image_base64 attachments,
    but image_url support is kept for testing.
    """

    with httpx.Client(timeout=60) as client:
        response = client.get(image_url)
        response.raise_for_status()

    return base64.b64encode(response.content).decode("utf-8")


def _normalize_date(value: Any) -> Any:
    """
    Convert simple dates like 15/05/2026 or 15-05-2026 to YYYY-MM-DD.
    If the value is already correct or unknown, return it unchanged.
    """

    if not value or not isinstance(value, str):
        return value

    value = value.strip()

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value

    match = re.fullmatch(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", value)
    if match:
        day, month, year = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    return value


def _fallback_no_image(message: str | None = None) -> dict[str, Any]:
    user_text = (message or "").strip()

    return {
        "status": "no_image",
        "needs_user_clarification": True,
        "question": (
            "I did not receive an image. "
            "Please upload a receipt image, or type the amount, category, and date."
        ),
        "extracted_action": {
            "action": "unknown",
            "requires_confirmation": True,
            "missing_fields": ["image"],
            "data": {
                "user_message": user_text,
            },
            "explanation": "No image was provided.",
        },
        "raw_extraction": {},
    }


def _fallback_vision_failed(error: str, message: str | None = None) -> dict[str, Any]:
    user_text = (message or "").strip()

    return {
        "status": "vision_failed",
        "needs_user_clarification": True,
        "question": (
            "I could not read the image clearly. "
            "You can type the missing details, for example: amount, category, date, and whether it is an expense or loan."
        ),
        "extracted_action": {
            "action": "unknown",
            "requires_confirmation": True,
            "missing_fields": ["amount", "category"],
            "data": {
                "user_message": user_text,
            },
            "explanation": f"Vision extraction failed: {error}",
        },
        "raw_extraction": {},
    }


def _infer_category_from_text(text: str) -> str | None:
    lower = text.lower()

    transport_words = ["bus", "taxi", "train", "metro", "fuel", "car", "parking", "transport"]
    food_words = ["food", "restaurant", "cafe", "coffee", "tea", "pizza", "burger", "meal"]
    shopping_words = ["shop", "shopping", "store", "market", "clothes"]
    bills_words = ["rent", "electricity", "water", "internet", "phone", "bill"]

    if any(word in lower for word in transport_words):
        return "Transport"

    if any(word in lower for word in food_words):
        return "Food"

    if any(word in lower for word in shopping_words):
        return "Shopping"

    if any(word in lower for word in bills_words):
        return "Bills"

    return None


def _build_friendly_missing_question(action: str, data: dict[str, Any], missing_fields: list[str]) -> str:
    """
    Build a user-friendly response when Vision extracted partial information.
    """

    known_parts = []

    description = data.get("description") or data.get("person_name") or data.get("merchant")
    amount = data.get("amount")
    category = data.get("category")
    date = data.get("transaction_date") or data.get("date") or data.get("return_date")
    loan_type = data.get("type")

    if description:
        known_parts.append(f"description/person: {description}")

    if amount is not None:
        known_parts.append(f"amount: {amount}")

    if category:
        known_parts.append(f"category: {category}")

    if date:
        known_parts.append(f"date: {date}")

    if action in {"create_loan", "update_loan", "update_loan_status"} and loan_type:
        known_parts.append(f"loan type: {loan_type}")

    known_text = ", ".join(known_parts) if known_parts else "some information"

    missing_text = ", ".join(missing_fields) if missing_fields else "the missing required details"

    if action == "create_loan":
        return (
            f"I can prepare a loan from the image. I extracted {known_text}, "
            f"but I still need: {missing_text}."
        )

    if action == "create_expense":
        return (
            f"I can add this expense. I extracted {known_text}, "
            f"but I still need: {missing_text}."
        )

    return (
        f"I extracted {known_text}, but I still need: {missing_text}."
    )


def normalize_vision_action(result: dict[str, Any], message: str | None = None) -> dict[str, Any]:
    """
    Converts the vision result into the same structure as CommandAgent.
    Supports create_expense and create_loan.
    """

    user_text = (message or "").strip()
    action = result.get("action") or "create_expense"
    data = result.get("data") or {}

    if not isinstance(data, dict):
        data = {}

    combined_text = " ".join(
        str(value)
        for value in [
            user_text,
            data.get("description"),
            data.get("merchant"),
            data.get("store_name"),
            data.get("vendor"),
            data.get("category"),
            data.get("person_name"),
        ]
        if value
    )

    # Common aliases produced by vision models
    if data.get("merchant") and not data.get("description"):
        data["description"] = data.get("merchant")

    if data.get("store_name") and not data.get("description"):
        data["description"] = data.get("store_name")

    if data.get("vendor") and not data.get("description"):
        data["description"] = data.get("vendor")

    if data.get("total") is not None and data.get("amount") is None:
        data["amount"] = data.get("total")

    if data.get("final_total") is not None and data.get("amount") is None:
        data["amount"] = data.get("final_total")

    if data.get("grand_total") is not None and data.get("amount") is None:
        data["amount"] = data.get("grand_total")

    if data.get("date") and not data.get("transaction_date"):
        data["transaction_date"] = data.get("date")

    if data.get("transaction_date"):
        data["transaction_date"] = _normalize_date(data.get("transaction_date"))

    if data.get("return_date"):
        data["return_date"] = _normalize_date(data.get("return_date"))

    # Infer category from image text + user message
    if not data.get("category"):
        inferred_category = _infer_category_from_text(combined_text)
        if inferred_category:
            data["category"] = inferred_category

    # Loan detection from user message or extracted text
    lower_text = combined_text.lower()
    loan_words = ["loan", "borrowed", "lent", "debt", "owe", "return money", "pay back"]
    if action == "unknown" and any(word in lower_text for word in loan_words):
        action = "create_loan"

    if action == "create_loan":
        # Loan module usually needs person_name, amount, type.
        if data.get("person") and not data.get("person_name"):
            data["person_name"] = data.get("person")

        if not data.get("status"):
            data["status"] = "unpaid"

        # For loan, type usually means gave/received depending on your backend.
        # If unclear, leave it missing so the user clarifies.
        if data.get("loan_type") and not data.get("type"):
            data["type"] = data.get("loan_type")

    else:
        # Default to expense if money amount exists and no loan intent is detected.
        action = "create_expense"

        if not data.get("transaction_date"):
            data["transaction_date"] = get_today_iso()

        if not data.get("type"):
            data["type"] = "outcome"

        if not data.get("description"):
            data["description"] = "Receipt purchase"

        if not data.get("category"):
            data["category"] = "Other"

    normalized = {
        "action": action,
        "requires_confirmation": result.get("requires_confirmation", True),
        "missing_fields": result.get("missing_fields", []),
        "data": data,
        "explanation": result.get("explanation", "Extracted financial action from image."),
    }

    normalized = normalize_action_result(normalized)
    normalized = normalize_data_fields(normalized)
    normalized = recalculate_missing_fields(normalized)

    # If LLM gave unknown but there is enough money data, force create_expense.
    normalized_data = normalized.get("data") or {}
    if normalized.get("action") == "unknown" and normalized_data.get("amount") is not None:
        normalized["action"] = "create_expense"
        normalized = recalculate_missing_fields(normalized)

    return normalized


def extract_from_image(
    image_base64: str | None,
    image_url: str | None,
    message: str | None = None,
) -> dict[str, Any]:
    """
    Vision Agent.

    Reads an image + optional user message and returns an extracted_action
    compatible with the Command Agent pipeline.
    """

    clean_image = _clean_base64(image_base64)

    if not clean_image and image_url:
        try:
            clean_image = _image_url_to_base64(image_url)
        except Exception as exc:
            return _fallback_vision_failed(str(exc), message=message)

    if not clean_image:
        return _fallback_no_image(message=message)

    user_instruction = (message or "").strip() or "No text instruction provided."

    prompt = f"""
You are the VisionAgent for AMMA, an AI Money Management Assistant.

You receive:
1. An uploaded image.
2. The user's text instruction.

User instruction:
{user_instruction}

Your job:
Read the uploaded image and combine it with the user instruction.
Extract exactly one structured financial action.

Supported actions:
1. create_expense
2. create_loan
3. unknown

The image may be:
- a formal receipt
- a shop bill
- a food bill
- a taxi/bus/train ticket
- a bank payment screenshot
- a handwritten/simple expense note
- a screenshot containing expense or loan text

Return ONLY valid JSON.
Do not include markdown.
Do not explain outside JSON.

Expense rules:
- If the image contains a product/service name and a money amount, return action = create_expense.
- Do NOT require a formal receipt layout.
- If the image says "bus : 46 ruble", extract description = "bus", amount = 46, category = "Transport".
- If the user says "add this expense", prefer create_expense.
- If the image contains transport words such as bus, taxi, train, metro, fuel, car, parking, category = "Transport".
- If the image contains food, cafe, restaurant, coffee, tea, pizza, burger, category = "Food".
- If the image contains market, store, clothes, shopping, category = "Shopping".
- If the image contains rent, electricity, water, internet, phone, category = "Bills".
- If category is unclear, use "Other".
- Extract the final total amount if multiple amounts exist.
- If there is only one amount, use it as the amount.
- Use transaction_date from the image if visible.
- Convert dates to YYYY-MM-DD.
- If date is not visible, use today's date: {get_today_iso()}.
- For normal purchases/payments, type = "outcome".
- If the image clearly shows received salary/payment/income, type = "income".

Loan rules:
- If the user instruction or image mentions loan, borrowed, lent, debt, owe, or pay back, return action = create_loan.
- For create_loan, extract amount, person_name, type, status, and return_date if visible.
- type should be "given" if the user gave/lent money to someone.
- type should be "taken" if the user borrowed/took money from someone.
- status should default to "unpaid" if not visible.
- If person_name is not visible, put it in missing_fields.
- If loan type is not clear, put "type" in missing_fields.

Missing field rules:
- If you can extract some information, still return create_expense or create_loan.
- Do NOT return unknown just because some fields are missing.
- Use missing_fields to list missing required fields.
- Only return unknown if there is no readable financial amount and no clear financial action.

Return JSON exactly in this format:
{{
  "action": "create_expense | create_loan | unknown",
  "requires_confirmation": true,
  "missing_fields": [],
  "data": {{
    "description": "short description for expense",
    "person_name": "person name for loan if visible",
    "type": "outcome | income | given | taken",
    "status": "unpaid | paid | partially_paid",
    "amount": 0,
    "transaction_date": "YYYY-MM-DD",
    "return_date": "YYYY-MM-DD or null",
    "category": "Food | Transport | Shopping | Health | Education | Coffee | Work | Bills | Other",
    "merchant": "optional merchant/store name",
    "currency": "optional currency"
  }},
  "explanation": "short explanation"
}}
"""

    try:
        raw_result = ollama_client.generate_vision_json(
            prompt=prompt,
            image_base64=clean_image,
        )
    except Exception as exc:
        return _fallback_vision_failed(str(exc), message=message)

    extracted_action = normalize_vision_action(raw_result, message=message)

    missing_fields = extracted_action.get("missing_fields") or []
    needs_user_clarification = (
        extracted_action.get("action") == "unknown"
        or bool(missing_fields)
    )

    question = None

    if needs_user_clarification:
        question = _build_friendly_missing_question(
            action=extracted_action.get("action", "unknown"),
            data=extracted_action.get("data") or {},
            missing_fields=missing_fields,
        )

    return {
        "status": "ok" if not needs_user_clarification else "incomplete",
        "needs_user_clarification": needs_user_clarification,
        "question": question,
        "extracted_action": extracted_action,
        "raw_extraction": raw_result,
    }