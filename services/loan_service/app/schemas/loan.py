from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class LoanCreate(BaseModel):
    person_name: str = Field(min_length=1, max_length=100)
    person_phone_number: Optional[str] = None
    amount: float = Field(gt=0)
    type: str = Field(pattern="^(borrowed|lent)$")
    date_created: date
    date_return: Optional[date] = None


class LoanUpdate(BaseModel):
    person_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    person_phone_number: Optional[str] = None
    amount: Optional[float] = Field(default=None, gt=0)
    status: Optional[str] = Field(default=None, pattern="^(unpaid|paid|partially_paid|overdue)$")
    type: Optional[str] = Field(default=None, pattern="^(borrowed|lent)$")
    date_return: Optional[date] = None
    paid_amount: Optional[float] = Field(default=None, ge=0)
    last_payment_date: Optional[date] = None


class LoanOut(BaseModel):
    id: int
    user_id: int
    person_name: str
    person_phone_number: Optional[str] = None
    amount: float
    status: str
    type: str
    date_created: date
    date_return: Optional[date] = None
    paid_amount: float
    last_payment_date: Optional[date] = None
    parent_loan_id: Optional[int] = None

    class Config:
        from_attributes = True