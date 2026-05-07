from sqlalchemy.orm import Session

from app.models.budget import Budget


class BudgetRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_month(self, user_id: int, year: int, month: int) -> Budget | None:
        return (
            self.db.query(Budget)
            .filter(
                Budget.user_id == user_id,
                Budget.year == year,
                Budget.month == month,
            )
            .first()
        )

    def upsert(self, user_id: int, year: int, month: int, amount: int) -> Budget:
        budget = self.get_by_month(user_id, year, month)

        if budget:
            budget.amount = amount
        else:
            budget = Budget(
                user_id=user_id,
                year=year,
                month=month,
                amount=amount,
            )
            self.db.add(budget)

        self.db.commit()
        self.db.refresh(budget)
        return budget