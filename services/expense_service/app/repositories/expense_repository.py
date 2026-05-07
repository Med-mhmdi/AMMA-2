from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.expense import Expense


class ExpenseRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        amount: float,
        category_id: int,
        type_: str,
        description: str | None,
        transaction_date,
    ) -> Expense:
        expense = Expense(
            user_id=user_id,
            amount=amount,
            category_id=category_id,
            type=type_,
            description=description,
            transaction_date=transaction_date,
        )
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def list_by_user(self, user_id: int) -> list[Expense]:
        return (
            self.db.query(Expense)
            .options(joinedload(Expense.category_rel))
            .filter(Expense.user_id == user_id)
            .order_by(Expense.transaction_date.desc(), Expense.id.desc())
            .all()
        )

    def get_by_id(self, expense_id: int, user_id: int) -> Expense | None:
        return (
            self.db.query(Expense)
            .options(joinedload(Expense.category_rel))
            .filter(Expense.id == expense_id, Expense.user_id == user_id)
            .first()
        )

    def save(self, expense: Expense) -> Expense:
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def delete(self, expense: Expense) -> None:
        self.db.delete(expense)
        self.db.commit()

    def count_by_category(self, category_id: int, user_id: int) -> int:
        return (
            self.db.query(func.count(Expense.id))
            .filter(Expense.category_id == category_id, Expense.user_id == user_id)
            .scalar()
        )

    def monthly_summary(self, user_id: int) -> dict:
        income = self.db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.user_id == user_id,
            Expense.type == "income",
        ).scalar()

        outcome = self.db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.user_id == user_id,
            Expense.type == "outcome",
        ).scalar()

        return {
            "income": float(income),
            "outcome": float(outcome),
            "balance": float(income) - float(outcome),
        }