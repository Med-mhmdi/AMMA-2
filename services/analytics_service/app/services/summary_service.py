from calendar import monthrange
from datetime import datetime

import httpx

from app.config import settings
from app.services.cache_service import CacheService


class SummaryService:
    def __init__(self):
        self.cache_service = CacheService()

    @staticmethod
    async def get_expense_list(token: str) -> list[dict]:
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{settings.EXPENSE_SERVICE_URL}/expenses",
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_loan_list(token: str) -> list[dict]:
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{settings.LOAN_SERVICE_URL}/loans",
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    def filter_expenses(
        expenses: list[dict],
        year: int,
        month: int | None = None,
    ) -> list[dict]:
        filtered = []

        for item in expenses:
            date_value = item.get("transaction_date")
            if not date_value:
                continue

            item_year = int(date_value.split("-")[0])
            item_month = int(date_value.split("-")[1])

            if item_year != year:
                continue

            if month is not None and item_month != month:
                continue

            filtered.append(item)

        return filtered

    @staticmethod
    def build_summary(expenses: list[dict]) -> dict:
        income = 0
        expense = 0

        for item in expenses:
            amount = float(item.get("amount", 0))

            if item.get("type") == "income":
                income += amount
            else:
                expense += amount

        return {
            "total_income": income,
            "total_expense": expense,
            "balance": income - expense,
        }

    @staticmethod
    def build_monthly_data(expenses: list[dict], year: int) -> list[dict]:
        months = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]

        result = {
            i: {
                "month": months[i - 1],
                "income": 0,
                "expense": 0,
                "balance": 0,
            }
            for i in range(1, 13)
        }

        for item in expenses:
            date_value = item.get("transaction_date")
            if not date_value:
                continue

            item_year = int(date_value.split("-")[0])
            item_month = int(date_value.split("-")[1])

            if item_year != year:
                continue

            amount = float(item.get("amount", 0))

            if item.get("type") == "income":
                result[item_month]["income"] += amount
            else:
                result[item_month]["expense"] += amount

            result[item_month]["balance"] = (
                result[item_month]["income"] - result[item_month]["expense"]
            )

        return list(result.values())

    @staticmethod
    def build_daily_data(expenses: list[dict], year: int, month: int) -> list[dict]:
        days_in_month = monthrange(year, month)[1]

        result = {
            day: {
                "day": day,
                "income": 0,
                "expense": 0,
                "balance": 0,
            }
            for day in range(1, days_in_month + 1)
        }

        for item in expenses:
            date_value = item.get("transaction_date")
            if not date_value:
                continue

            transaction_date = datetime.fromisoformat(date_value)

            if transaction_date.year != year or transaction_date.month != month:
                continue

            day = transaction_date.day
            amount = float(item.get("amount", 0))

            if item.get("type") == "income":
                result[day]["income"] += amount
            else:
                result[day]["expense"] += amount

            result[day]["balance"] = result[day]["income"] - result[day]["expense"]

        return [result[day] for day in range(1, days_in_month + 1)]

    @staticmethod
    def build_budget_status(year: int, month: int, spent: float, budget: float) -> dict:
        from calendar import monthrange
        from datetime import datetime

        raw_percent = (spent / budget) * 100 if budget > 0 else 0
        bar_percent = min(raw_percent, 100)

        budget_left = budget - spent

        today = datetime.now()
        is_current_month = year == today.year and month == today.month

        days_in_month = monthrange(year, month)[1]

        month_progress_percent = (
            (today.day / days_in_month) * 100
            if is_current_month
            else 100
        )

        status = "safe"
        severity = 0

        if raw_percent > 100:
            status = "over"
            severity = 4

        elif raw_percent == 100:
            status = "full"
            severity = 3

        elif raw_percent >= 90:
            status = "warning"
            severity = 2

        elif is_current_month and raw_percent > month_progress_percent:
            status = "fast"
            severity = 1

        message = ""

        if status == "warning":
            message = "⚠ You are close to exceeding your monthly budget"

        elif status == "full":
            message = "⚠ You have used exactly all your monthly budget"

        elif status == "over":
            message = "🚨 You exceeded your monthly budget"

        return {
            "spent": spent,
            "budget": budget,
            "percent_used": raw_percent,
            "bar_percent": bar_percent,
            "budget_left": budget_left,
            "month_progress_percent": month_progress_percent,
            "is_current_month": is_current_month,
            "status": status,
            "severity": severity,
            "message": message,
        }

    @staticmethod
    async def get_budget(token: str, year: int, month: int) -> dict:
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{settings.EXPENSE_SERVICE_URL}/budgets?year={year}&month={month}",
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    def build_loan_summary(
            loans: list[dict],
            year: int,
            month: int | None,
            period: str,
    ) -> dict:
        active_statuses = ["unpaid", "partially_paid", "overdue"]

        filtered_loans = []

        for loan in loans:
            date_value = loan.get("date_created")
            if not date_value:
                continue

            loan_year = int(date_value.split("-")[0])
            loan_month = int(date_value.split("-")[1])

            if loan_year != year:
                continue

            if period == "monthly" and month is not None and loan_month != month:
                continue

            filtered_loans.append(loan)

        active_loans = [
            loan for loan in filtered_loans
            if loan.get("status") in active_statuses
        ]

        borrowed_total = 0
        lent_total = 0
        active_borrowed = 0
        active_lent = 0
        active_people = []

        for loan in filtered_loans:
            amount = float(loan.get("amount", 0))
            paid_amount = float(loan.get("paid_amount", 0) or 0)
            remaining = max(amount - paid_amount, 0)

            if loan.get("type") == "borrowed":
                borrowed_total += amount
            elif loan.get("type") == "lent":
                lent_total += amount

            if loan.get("status") in active_statuses:
                if loan.get("type") == "borrowed":
                    active_borrowed += remaining
                elif loan.get("type") == "lent":
                    active_lent += remaining

                active_people.append(
                    {
                        "person_name": loan.get("person_name", "Unknown"),
                        "type": loan.get("type"),
                        "status": loan.get("status"),
                        "amount": amount,
                        "paid_amount": paid_amount,
                        "remaining_amount": remaining,
                    }
                )

        loan_balance = active_lent - active_borrowed

        return {
            "borrowed_total": borrowed_total,
            "lent_total": lent_total,
            "loan_count": len(filtered_loans),
            "active_loan_count": len(active_loans),
            "active_borrowed": active_borrowed,
            "active_lent": active_lent,
            "loan_balance": loan_balance,
            "active_people": active_people,
            "loan_status": (
                "You are in debt"
                if loan_balance < 0
                else "People owe you money"
                if loan_balance > 0
                else "Balanced"
            ),
        }

    async def build_dashboard_summary(
        self,
        user_id: int,
        token: str,
        year: int,
        month: int | None,
        period: str,
    ) -> dict:

        expenses = await self.get_expense_list(token)
        loans = await self.get_loan_list(token)

        selected_month = month if period == "monthly" else None
        filtered_expenses = self.filter_expenses(expenses, year, selected_month)

        summary = self.build_summary(filtered_expenses)
        loan_summary = self.build_loan_summary(
            loans=loans,
            year=year,
            month=month,
            period=period,
        )

        budget_data = await self.get_budget(token, year, month or datetime.now().month)
        budget_amount = float(budget_data.get("amount", 0))

        monthly_data = self.build_monthly_data(expenses, year)
        selected_month_data = monthly_data[(month or datetime.now().month) - 1]
        selected_month_spent = float(selected_month_data.get("expense", 0))

        budget_status = self.build_budget_status(
            year=year,
            month=month or datetime.now().month,
            spent=selected_month_spent,
            budget=budget_amount,
        )

        result = {
            **summary,
            **loan_summary,
            "year": year,
            "month": month,
            "period": period,
            "monthly": monthly_data,
            "budget_status": budget_status,
        }

        return result

    async def build_category_breakdown(
        self,
        user_id: int,
        token: str,
        year: int,
        month: int | None,
        period: str,
        transaction_type: str,
        chart_service,
    ) -> list[dict]:
        cache_key = self.cache_service.get_cache_key(
            user_id,
            f"categories:{year}:{month}:{period}:{transaction_type}",
        )
        cached_value = self.cache_service.get(cache_key)

        if cached_value is not None:
            return cached_value

        expenses = await self.get_expense_list(token)

        selected_month = month if period == "monthly" else None

        result = chart_service.category_breakdown(
            expenses=expenses,
            year=year,
            month=selected_month,
            transaction_type=transaction_type,
        )

        self.cache_service.set(cache_key, result, ttl_seconds=120)
        return result

    async def build_daily_summary(
        self,
        user_id: int,
        token: str,
        year: int,
        month: int,
    ) -> list[dict]:
        cache_key = self.cache_service.get_cache_key(user_id, f"daily:{year}:{month}")
        cached_value = self.cache_service.get(cache_key)

        if cached_value is not None:
            return cached_value

        expenses = await self.get_expense_list(token)
        result = self.build_daily_data(expenses, year, month)

        self.cache_service.set(cache_key, result, ttl_seconds=120)
        return result

    def invalidate_user_cache(self, user_id: int):
        deleted = self.cache_service.invalidate_user_cache(user_id)
        return {"deleted_keys": deleted}