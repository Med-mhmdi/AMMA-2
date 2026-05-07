from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.repositories.loan_repository import LoanRepository
from app.schemas.loan import LoanCreate, LoanOut, LoanUpdate
from app.services.loan_service import LoanService


router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "loan_service"}


@router.post("/loans", response_model=LoanOut, status_code=201)
def create_loan(
    payload: LoanCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = LoanRepository(db)
    service = LoanService(repository)
    return service.create_loan(current_user["user_id"], payload)


@router.get("/loans", response_model=list[LoanOut])
def list_loans(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = LoanRepository(db)
    service = LoanService(repository)
    return service.list_loans(current_user["user_id"])


@router.put("/loans/{loan_id}", response_model=LoanOut)
def update_loan(
    loan_id: int,
    payload: LoanUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = LoanRepository(db)
    service = LoanService(repository)
    return service.update_loan(loan_id, current_user["user_id"], payload)


@router.delete("/loans/{loan_id}")
def delete_loan(
    loan_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = LoanRepository(db)
    service = LoanService(repository)
    return service.delete_loan(loan_id, current_user["user_id"])