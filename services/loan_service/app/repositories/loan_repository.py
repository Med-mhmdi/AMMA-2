from sqlalchemy.orm import Session

from app.models.loan import Loan


class LoanRepository:
    """Repository layer for loan database operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        person_name: str,
        person_phone_number: str | None,
        amount: float,
        status: str,
        type_: str,
        date_created,
        date_return,
        paid_amount: float,
        last_payment_date,
        parent_loan_id: int | None,
    ) -> Loan:
        loan = Loan(
            user_id=user_id,
            person_name=person_name,
            person_phone_number=person_phone_number,
            amount=amount,
            status=status,
            type=type_,
            date_created=date_created,
            date_return=date_return,
            paid_amount=paid_amount,
            last_payment_date=last_payment_date,
            parent_loan_id=parent_loan_id,
        )
        self.db.add(loan)
        self.db.commit()
        self.db.refresh(loan)
        return loan

    def list_by_user(self, user_id: int) -> list[Loan]:
        return self.db.query(Loan).filter(Loan.user_id == user_id).all()

    def get_by_id(self, loan_id: int, user_id: int) -> Loan | None:
        return (
            self.db.query(Loan)
            .filter(Loan.id == loan_id, Loan.user_id == user_id)
            .first()
        )

    def save(self, loan: Loan) -> Loan:
        self.db.commit()
        self.db.refresh(loan)
        return loan

    def delete(self, loan: Loan) -> None:
        self.db.delete(loan)
        self.db.commit()