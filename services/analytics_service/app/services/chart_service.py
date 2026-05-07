class ChartService:
    """Builds chart-like aggregated views from transaction data."""

    @staticmethod
    def category_breakdown(
        expenses: list[dict],
        year: int,
        month: int | None = None,
        transaction_type: str = "outcome",
    ) -> list[dict]:
        result = {}

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

            if item.get("type") != transaction_type:
                continue

            category = item.get("category_name") or item.get("category") or "Unknown"
            amount = float(item.get("amount", 0))

            result[category] = result.get(category, 0) + amount

        return [
            {"category": category, "amount": amount}
            for category, amount in result.items()
        ]