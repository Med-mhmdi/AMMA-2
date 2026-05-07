from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.repositories.category_repository import CategoryRepository
from app.repositories.expense_repository import ExpenseRepository
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.schemas.expense import ExpenseCreate, ExpenseOut, ExpenseUpdate
from app.services.category_service import CategoryService
from app.services.expense_service import ExpenseService
from app.repositories.budget_repository import BudgetRepository
from app.schemas.budget import BudgetOut, BudgetUpsert
from app.services.budget_service import BudgetService


router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "expense_service"}


@router.post("/expenses", response_model=ExpenseOut, status_code=201)
def create_expense(
    payload: ExpenseCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expense_repository = ExpenseRepository(db)
    category_repository = CategoryRepository(db)
    service = ExpenseService(expense_repository, category_repository)
    return service.create_expense(current_user["user_id"], payload)


@router.get("/expenses", response_model=list[ExpenseOut])
def list_expenses(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expense_repository = ExpenseRepository(db)
    category_repository = CategoryRepository(db)
    service = ExpenseService(expense_repository, category_repository)
    return service.list_expenses(current_user["user_id"])


@router.put("/expenses/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expense_repository = ExpenseRepository(db)
    category_repository = CategoryRepository(db)
    service = ExpenseService(expense_repository, category_repository)
    return service.update_expense(expense_id, current_user["user_id"], payload)


@router.delete("/expenses/{expense_id}")
def delete_expense(
    expense_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expense_repository = ExpenseRepository(db)
    category_repository = CategoryRepository(db)
    service = ExpenseService(expense_repository, category_repository)
    return service.delete_expense(expense_id, current_user["user_id"])


@router.get("/expenses/summary")
def get_summary(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expense_repository = ExpenseRepository(db)
    category_repository = CategoryRepository(db)
    service = ExpenseService(expense_repository, category_repository)
    return service.get_monthly_summary(current_user["user_id"])


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(
    payload: CategoryCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category_repository = CategoryRepository(db)
    expense_repository = ExpenseRepository(db)
    service = CategoryService(category_repository, expense_repository)
    return service.create_category(current_user["user_id"], payload)


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category_repository = CategoryRepository(db)
    expense_repository = ExpenseRepository(db)
    service = CategoryService(category_repository, expense_repository)
    return service.list_categories(current_user["user_id"])


@router.put("/categories/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category_repository = CategoryRepository(db)
    expense_repository = ExpenseRepository(db)
    service = CategoryService(category_repository, expense_repository)
    return service.update_category(category_id, current_user["user_id"], payload)


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category_repository = CategoryRepository(db)
    expense_repository = ExpenseRepository(db)
    service = CategoryService(category_repository, expense_repository)
    return service.delete_category(category_id, current_user["user_id"])

@router.get("/budgets", response_model=BudgetOut)
def get_budget(
    year: int,
    month: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = BudgetRepository(db)
    service = BudgetService(repository)

    return service.get_budget(current_user["user_id"], year, month)


@router.put("/budgets", response_model=BudgetOut)
def upsert_budget(
    payload: BudgetUpsert,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = BudgetRepository(db)
    service = BudgetService(repository)

    return service.upsert_budget(current_user["user_id"], payload)