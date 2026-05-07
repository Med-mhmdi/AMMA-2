from sqlalchemy import Column, Integer, UniqueConstraint

from app.database import Base


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("user_id", "year", "month", name="uq_user_budget_month"),
    )