from fastapi import HTTPException

from app.events.publishers import LoanEventPublisher
from app.repositories.loan_repository import LoanRepository
from app.schemas.loan import LoanCreate, LoanUpdate


class LoanService:
    def __init__(self, loan_repository: LoanRepository):
        self.loan_repository = loan_repository
        self.publisher = LoanEventPublisher()

    def create_loan(self, user_id: int, payload: LoanCreate):
        loan = self.loan_repository.create(
            user_id=user_id,
            person_name=payload.person_name,
            person_phone_number=payload.person_phone_number,
            amount=payload.amount,
            status="unpaid",
            type_=payload.type,
            date_created=payload.date_created,
            date_return=payload.date_return,
            paid_amount=0,
            last_payment_date=None,
            parent_loan_id=None,
        )

        self.publisher.publish_loan_created(
            {
                "event_type": "loan.created",
                "loan_id": loan.id,
                "user_id": loan.user_id,
                "person_name": loan.person_name,
                "amount": float(loan.amount),
                "status": loan.status,
                "type": loan.type,
                "date_created": str(loan.date_created),
                "date_return": str(loan.date_return) if loan.date_return else None,
            }
        )

        return loan

    def list_loans(self, user_id: int):
        return self.loan_repository.list_by_user(user_id)

    def update_loan(self, loan_id: int, user_id: int, payload: LoanUpdate):
        loan = self.loan_repository.get_by_id(loan_id, user_id)

        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")

        if payload.person_name is not None:
            loan.person_name = payload.person_name

        if payload.person_phone_number is not None:
            loan.person_phone_number = payload.person_phone_number

        if payload.amount is not None:
            loan.amount = payload.amount

        if payload.type is not None:
            loan.type = payload.type

        if payload.status is not None:
            loan.status = payload.status

            if payload.status == "unpaid":
                loan.date_return = None
                loan.paid_amount = 0
                loan.last_payment_date = None

            elif payload.status == "partially_paid":
                if payload.paid_amount is None or payload.paid_amount <= 0:
                    raise HTTPException(
                        status_code=400,
                        detail="paid_amount is required for partially_paid loans",
                    )

                if payload.paid_amount >= float(loan.amount):
                    raise HTTPException(
                        status_code=400,
                        detail="paid_amount must be less than total amount for partially_paid loans",
                    )

                if payload.last_payment_date is None:
                    raise HTTPException(
                        status_code=400,
                        detail="last_payment_date is required for partially_paid loans",
                    )

                loan.paid_amount = payload.paid_amount
                loan.last_payment_date = payload.last_payment_date
                loan.date_return = None

            elif payload.status == "paid":
                if payload.date_return is None:
                    raise HTTPException(
                        status_code=400,
                        detail="date_return is required when loan is paid",
                    )

                loan.date_return = payload.date_return
                loan.paid_amount = float(loan.amount)
                loan.last_payment_date = payload.date_return

        return self.loan_repository.save(loan)

    def delete_loan(self, loan_id: int, user_id: int):
        loan = self.loan_repository.get_by_id(loan_id, user_id)

        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")

        self.loan_repository.delete(loan)
        return {"message": "Loan deleted successfully"}