from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    category_id: int
    type: str = Field(pattern="^(income|outcome)$")
    amount: float = Field(gt=0)
    transaction_date: date


class ExpenseUpdate(BaseModel):
    description: Optional[str] = Field(default=None, min_length=1, max_length=255)
    category_id: Optional[int] = None
    type: Optional[str] = Field(default=None, pattern="^(income|outcome)$")
    amount: Optional[float] = Field(default=None, gt=0)
    transaction_date: Optional[date] = None


class ExpenseOut(BaseModel):
    id: int
    user_id: int
    description: Optional[str] = None
    category_id: int
    category_name: str
    type: str
    amount: float
    transaction_date: date

    class Config:
        from_attributes = True