from typing import Any

import httpx

from app.config import settings


class LoanTool:
    """
    Tool used by multi_agent_system to communicate with loan_service.

    It does not access the database directly.
    It calls the real loan_service API, so the microservice remains
    the source of truth.
    """

    LOANS_PATH = "/loans"

    def __init__(self) -> None:
        self.base_url = settings.LOAN_SERVICE_URL.rstrip("/")

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
        - {"loans": [...]}
        """

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            for key in ["items", "data", "results", "loans"]:
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
    # Loan tools
    # =========================================================

    def list_loans(self, auth_header: str | None = None) -> list[dict[str, Any]]:
        url = f"{self.base_url}{self.LOANS_PATH}"

        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self._headers(auth_header))

            if not response.is_success:
                self._raise_clean_error(response)

            data = response.json()

        return self._normalize_list_response(data)

    def find_loan_by_id(
        self,
        loans: list[dict[str, Any]],
        loan_id: int | None,
    ) -> dict[str, Any] | None:
        if loan_id is None:
            return None

        for loan in loans:
            try:
                current_id = int(loan.get("id"))
            except (TypeError, ValueError):
                continue

            if current_id == int(loan_id):
                return loan

        return None

    def find_loans_by_person_name(
        self,
        loans: list[dict[str, Any]],
        person_name: str | None,
    ) -> list[dict[str, Any]]:
        """
        Finds loan matches by person name.

        Used for commands like:
        - delete Ahmed loan
        - Ahmed paid me back
        - change Ahmed loan amount to 600
        """

        if not person_name:
            return []

        wanted = person_name.strip().lower()
        matches: list[dict[str, Any]] = []

        for loan in loans:
            current_name = str(
                loan.get("person_name")
                or loan.get("name")
                or loan.get("person")
                or ""
            ).strip().lower()

            if current_name == wanted or wanted in current_name:
                matches.append(loan)

        return matches

    def find_loans_by_natural_match(
        self,
        loans: list[dict[str, Any]],
        data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Finds possible loan matches using natural fields.

        Used for commands like:
        - delete Ahmed loan
        - mark Ahmed loan as paid
        - update Ahmed borrowed loan to 800

        This does not decide alone if execution is safe.
        The validation/execution layer can use match count:
        - 0 matches: ask clarification
        - 1 match: safe to execute
        - multiple matches: ask user to choose
        """

        person_name = str(data.get("person_name") or "").strip().lower()
        loan_type = str(data.get("type") or "").strip().lower()
        status = str(data.get("status") or "").strip().lower()
        amount = data.get("amount")
        date_created = data.get("date_created")
        return_date = data.get("return_date")

        matches: list[dict[str, Any]] = []

        for loan in loans:
            score = 0

            current_person = str(
                loan.get("person_name")
                or loan.get("name")
                or loan.get("person")
                or ""
            ).strip().lower()

            current_type = str(loan.get("type") or "").strip().lower()
            current_status = str(loan.get("status") or "").strip().lower()
            current_date_created = loan.get("date_created")
            current_return_date = loan.get("return_date") or loan.get("date_return")

            try:
                current_amount = float(loan.get("amount"))
            except (TypeError, ValueError):
                current_amount = None

            if person_name and current_person:
                if person_name == current_person:
                    score += 4
                elif person_name in current_person or current_person in person_name:
                    score += 2

            if loan_type and current_type and loan_type == current_type:
                score += 2

            if status and current_status and status == current_status:
                score += 1

            if amount is not None and current_amount is not None:
                try:
                    if float(amount) == current_amount:
                        score += 2
                except (TypeError, ValueError):
                    pass

            if date_created and date_created == current_date_created:
                score += 1

            if return_date and return_date == current_return_date:
                score += 1

            if score > 0:
                matches.append(
                    {
                        **loan,
                        "_match_score": score,
                    }
                )

        matches.sort(
            key=lambda item: item.get("_match_score", 0),
            reverse=True,
        )

        return matches

    def create_loan(
        self,
        payload: dict[str, Any],
        auth_header: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{self.LOANS_PATH}"

        with httpx.Client(timeout=30) as client:
            response = client.post(
                url,
                json=payload,
                headers=self._headers(auth_header),
            )

            if not response.is_success:
                self._raise_clean_error(response)

            return response.json()

    def update_loan(
        self,
        loan_id: int,
        payload: dict[str, Any],
        auth_header: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{self.LOANS_PATH}/{loan_id}"

        with httpx.Client(timeout=30) as client:
            response = client.put(
                url,
                json=payload,
                headers=self._headers(auth_header),
            )

            if not response.is_success:
                self._raise_clean_error(response)

            return response.json()

    def update_loan_status(
        self,
        loan_id: int,
        status: str,
        paid_amount: float | int | None = None,
        last_payment_date: str | None = None,
        auth_header: str | None = None,
    ) -> dict[str, Any]:
        """
        Updates loan status.

        This uses a general PUT /loans/{id} payload because we do not know yet
        if your loan_service has a dedicated status endpoint.
        If your loan_service has /loans/{id}/status, we can change this later.
        """

        payload: dict[str, Any] = {
            "status": status,
        }

        if paid_amount is not None:
            payload["paid_amount"] = paid_amount

        if last_payment_date is not None:
            payload["last_payment_date"] = last_payment_date

        return self.update_loan(
            loan_id=loan_id,
            payload=payload,
            auth_header=auth_header,
        )

    def delete_loan(
        self,
        loan_id: int,
        auth_header: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{self.LOANS_PATH}/{loan_id}"

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
                        "loan_id": loan_id,
                    }

            return {
                "status": "deleted",
                "loan_id": loan_id,
            }


loan_tool = LoanTool()