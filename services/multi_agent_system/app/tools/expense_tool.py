from typing import Any

import httpx

from app.config import settings


class ExpenseTool:
    """
    Tool used by multi_agent_system to communicate with expense_service.

    It does not access the database directly.
    It calls the real expense_service API, so the microservice remains
    the source of truth.
    """

    CATEGORIES_PATH = "/categories"
    EXPENSES_PATH = "/expenses"

    def __init__(self) -> None:
        self.base_url = settings.EXPENSE_SERVICE_URL.rstrip("/")

    def _headers(self, auth_header: str | None = None) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }

        if auth_header:
            headers["Authorization"] = auth_header

        return headers

    def _normalize_list_response(self, data: Any) -> list[dict[str, Any]]:
        """
        Handles different possible API response formats.

        Examples:
        - [...]
        - {"items": [...]}
        - {"data": [...]}
        - {"results": [...]}
        - {"categories": [...]}
        - {"expenses": [...]}
        """

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            for key in ["items", "data", "results", "categories", "expenses"]:
                value = data.get(key)
                if isinstance(value, list):
                    return value

        return []

    def _raise_clean_error(self, response: httpx.Response) -> None:
        """
        Convert service errors into readable messages for the agent.
        """

        try:
            detail = response.json().get("detail")
        except Exception:
            detail = response.text

        raise RuntimeError(f"{response.status_code}: {detail}")

    # =========================================================
    # Category tools
    # =========================================================

    def list_categories(self, auth_header: str | None = None) -> list[dict[str, Any]]:
        url = f"{self.base_url}{self.CATEGORIES_PATH}"

        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self._headers(auth_header))

            if not response.is_success:
                self._raise_clean_error(response)

            data = response.json()

        return self._normalize_list_response(data)

    def find_category_by_name(
        self,
        categories: list[dict[str, Any]],
        category_name: str | None,
    ) -> dict[str, Any] | None:
        if not category_name:
            return None

        wanted = category_name.strip().lower()

        for category in categories:
            name = str(category.get("name", "")).strip().lower()

            if name == wanted:
                return category

        return None

    def create_category(
        self,
        name: str,
        auth_header: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{self.CATEGORIES_PATH}"

        payload = {
            "name": name,
        }

        with httpx.Client(timeout=30) as client:
            response = client.post(
                url,
                json=payload,
                headers=self._headers(auth_header),
            )

            if not response.is_success:
                self._raise_clean_error(response)

            return response.json()

    def update_category(
        self,
        category_id: int,
        name: str,
        auth_header: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{self.CATEGORIES_PATH}/{category_id}"

        payload = {
            "name": name,
        }

        with httpx.Client(timeout=30) as client:
            response = client.put(
                url,
                json=payload,
                headers=self._headers(auth_header),
            )

            if not response.is_success:
                self._raise_clean_error(response)

            return response.json()

    def delete_category(
        self,
        category_id: int,
        auth_header: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{self.CATEGORIES_PATH}/{category_id}"

        with httpx.Client(timeout=30) as client:
            response = client.delete(
                url,
                headers=self._headers(auth_header),
            )

            if not response.is_success:
                self._raise_clean_error(response)

            if response.content:
                try:
                    return response.json()
                except Exception:
                    return {
                        "status": "deleted",
                        "category_id": category_id,
                    }

            return {
                "status": "deleted",
                "category_id": category_id,
            }

    # =========================================================
    # Expense tools
    # =========================================================

    def list_expenses(self, auth_header: str | None = None) -> list[dict[str, Any]]:
        url = f"{self.base_url}{self.EXPENSES_PATH}"

        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self._headers(auth_header))

            if not response.is_success:
                self._raise_clean_error(response)

            data = response.json()

        return self._normalize_list_response(data)

    def find_expense_by_id(
        self,
        expenses: list[dict[str, Any]],
        expense_id: int | None,
    ) -> dict[str, Any] | None:
        if expense_id is None:
            return None

        for expense in expenses:
            try:
                current_id = int(expense.get("id"))
            except (TypeError, ValueError):
                continue

            if current_id == int(expense_id):
                return expense

        return None

    def find_expenses_by_natural_match(
        self,
        expenses: list[dict[str, Any]],
        data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Finds possible expense matches using natural fields.

        Used for commands like:
        - delete coffee expense
        - delete expense 100
        - update food expense to 500

        This does not decide alone if deletion is safe.
        The validation/execution layer can use match count:
        - 0 matches: ask clarification
        - 1 match: safe to execute
        - multiple matches: ask user to choose
        """

        description = str(data.get("description") or "").strip().lower()
        category = str(data.get("category") or "").strip().lower()
        amount = data.get("amount")
        transaction_date = data.get("transaction_date")

        matches: list[dict[str, Any]] = []

        for expense in expenses:
            score = 0

            expense_description = str(expense.get("description") or "").strip().lower()
            expense_category = str(
                expense.get("category_name")
                or expense.get("category")
                or ""
            ).strip().lower()
            expense_date = expense.get("transaction_date")

            try:
                expense_amount = float(expense.get("amount"))
            except (TypeError, ValueError):
                expense_amount = None

            if description and description in expense_description:
                score += 2

            if category and category == expense_category:
                score += 2

            if amount is not None and expense_amount is not None:
                try:
                    if float(amount) == expense_amount:
                        score += 2
                except (TypeError, ValueError):
                    pass

            if transaction_date and transaction_date == expense_date:
                score += 1

            # Loose keyword match for phrases like "coffee expense"
            if description and expense_category and description in expense_category:
                score += 2

            if score > 0:
                matches.append(
                    {
                        **expense,
                        "_match_score": score,
                    }
                )

        matches.sort(
            key=lambda item: item.get("_match_score", 0),
            reverse=True,
        )

        return matches

    def create_expense(
        self,
        payload: dict[str, Any],
        auth_header: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{self.EXPENSES_PATH}"

        with httpx.Client(timeout=30) as client:
            response = client.post(
                url,
                json=payload,
                headers=self._headers(auth_header),
            )

            if not response.is_success:
                self._raise_clean_error(response)

            return response.json()

    def update_expense(
        self,
        expense_id: int,
        payload: dict[str, Any],
        auth_header: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{self.EXPENSES_PATH}/{expense_id}"

        with httpx.Client(timeout=30) as client:
            response = client.put(
                url,
                json=payload,
                headers=self._headers(auth_header),
            )

            if not response.is_success:
                self._raise_clean_error(response)

            return response.json()

    def delete_expense(
        self,
        expense_id: int,
        auth_header: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{self.EXPENSES_PATH}/{expense_id}"

        with httpx.Client(timeout=30) as client:
            response = client.delete(
                url,
                headers=self._headers(auth_header),
            )

            if not response.is_success:
                self._raise_clean_error(response)

            if response.content:
                try:
                    return response.json()
                except Exception:
                    return {
                        "status": "deleted",
                        "expense_id": expense_id,
                    }

            return {
                "status": "deleted",
                "expense_id": expense_id,
            }


expense_tool = ExpenseTool()