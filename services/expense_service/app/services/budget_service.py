from app.repositories.budget_repository import BudgetRepository
from app.schemas.budget import BudgetUpsert


class BudgetService:
    def __init__(self, budget_repository: BudgetRepository):
        self.budget_repository = budget_repository

    def get_budget(self, user_id: int, year: int, month: int):
        budget = self.budget_repository.get_by_month(user_id, year, month)

        if not budget:
            return {
                "id": 0,
                "user_id": user_id,
                "year": year,
                "month": month,
                "amount": 0,
            }

        return budget

    def upsert_budget(self, user_id: int, payload: BudgetUpsert):
        return self.budget_repository.upsert(
            user_id=user_id,
            year=payload.year,
            month=payload.month,
            amount=payload.amount,
        )