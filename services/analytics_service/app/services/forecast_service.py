from calendar import monthrange
from datetime import datetime


class ForecastService:
    @staticmethod
    def build_month_forecast(
        expenses: list[dict],
        year: int,
        month: int,
        budget: float,
    ) -> dict:
        today = datetime.now()
        days_in_month = monthrange(year, month)[1]

        is_current_month = year == today.year and month == today.month

        spent_so_far = 0
        income_so_far = 0

        for item in expenses:
            date_value = item.get("transaction_date")
            if not date_value:
                continue

            transaction_date = datetime.fromisoformat(date_value)

            if transaction_date.year != year or transaction_date.month != month:
                continue

            amount = float(item.get("amount", 0))

            if item.get("type") == "income":
                income_so_far += amount
            else:
                spent_so_far += amount

        if is_current_month:
            elapsed_days = today.day
        else:
            elapsed_days = days_in_month

        daily_average_spending = spent_so_far / elapsed_days if elapsed_days > 0 else 0
        forecast_spending = daily_average_spending * days_in_month

        forecast_balance = income_so_far - forecast_spending
        expected_over_budget = forecast_spending - budget

        if budget <= 0:
            risk_level = "unknown"
            message = "No budget is set for this month."
        elif forecast_spending > budget:
            risk_level = "high"
            message = "You are expected to exceed your monthly budget."
        elif forecast_spending >= budget * 0.9:
            risk_level = "medium"
            message = "You are close to your monthly budget limit."
        else:
            risk_level = "low"
            message = "Your spending forecast is within the monthly budget."

        return {
            "year": year,
            "month": month,
            "days_in_month": days_in_month,
            "elapsed_days": elapsed_days,
            "spent_so_far": spent_so_far,
            "income_so_far": income_so_far,
            "daily_average_spending": round(daily_average_spending, 2),
            "forecast_spending": round(forecast_spending, 2),
            "forecast_balance": round(forecast_balance, 2),
            "budget": budget,
            "expected_over_budget": round(expected_over_budget, 2),
            "risk_level": risk_level,
            "message": message,
        }