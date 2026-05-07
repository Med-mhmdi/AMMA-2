from pydantic import BaseModel, Field


class BudgetUpsert(BaseModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    amount: int = Field(ge=0)


class BudgetOut(BaseModel):
    id: int
    user_id: int
    year: int
    month: int
    amount: int

    class Config:
        from_attributes = True