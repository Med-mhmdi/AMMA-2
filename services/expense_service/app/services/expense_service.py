from fastapi import HTTPException

from app.events.publishers import ExpenseEventPublisher
from app.repositories.category_repository import CategoryRepository
from app.repositories.expense_repository import ExpenseRepository
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


class ExpenseService:
    def __init__(
        self,
        expense_repository: ExpenseRepository,
        category_repository: CategoryRepository,
    ):
        self.expense_repository = expense_repository
        self.category_repository = category_repository
        self.publisher = ExpenseEventPublisher()

    def to_out(self, expense):
        return {
            "id": expense.id,
            "user_id": expense.user_id,
            "description": expense.description,
            "category_id": expense.category_id,
            "category_name": expense.category_rel.name if expense.category_rel else "",
            "type": expense.type,
            "amount": float(expense.amount),
            "transaction_date": expense.transaction_date,
        }

    def create_expense(self, user_id: int, payload: ExpenseCreate):
        category = self.category_repository.get_by_id(payload.category_id, user_id)
        if not category:
            raise HTTPException(status_code=400, detail="Invalid category")

        expense = self.expense_repository.create(
            user_id=user_id,
            amount=payload.amount,
            category_id=payload.category_id,
            type_=payload.type,
            description=payload.description,
            transaction_date=payload.transaction_date,
        )

        expense = self.expense_repository.get_by_id(expense.id, user_id)

        self.publisher.publish_expense_created(
            {
                "event_type": "expense.created",
                "expense_id": expense.id,
                "user_id": expense.user_id,
                "amount": float(expense.amount),
                "category": expense.category_rel.name if expense.category_rel else "",
                "type": expense.type,
                "description": expense.description,
                "transaction_date": str(expense.transaction_date),
            }
        )

        return self.to_out(expense)

    def list_expenses(self, user_id: int):
        expenses = self.expense_repository.list_by_user(user_id)
        return [self.to_out(expense) for expense in expenses]

    def update_expense(self, expense_id: int, user_id: int, payload: ExpenseUpdate):
        expense = self.expense_repository.get_by_id(expense_id, user_id)
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")

        if payload.category_id is not None:
            category = self.category_repository.get_by_id(payload.category_id, user_id)
            if not category:
                raise HTTPException(status_code=400, detail="Invalid category")
            expense.category_id = payload.category_id

        if payload.description is not None:
            expense.description = payload.description

        if payload.type is not None:
            expense.type = payload.type

        if payload.amount is not None:
            expense.amount = payload.amount

        if payload.transaction_date is not None:
            expense.transaction_date = payload.transaction_date

        expense = self.expense_repository.save(expense)
        expense = self.expense_repository.get_by_id(expense.id, user_id)
        return self.to_out(expense)

    def delete_expense(self, expense_id: int, user_id: int):
        expense = self.expense_repository.get_by_id(expense_id, user_id)
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")

        self.expense_repository.delete(expense)
        return {"message": "Expense deleted successfully"}

    def get_monthly_summary(self, user_id: int):
        return self.expense_repository.monthly_summary(user_id)