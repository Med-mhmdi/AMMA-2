from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    description = Column(String, nullable=True)
    type = Column(String, nullable=False)  # income | outcome
    amount = Column(Float, nullable=False)
    transaction_date = Column(Date, nullable=False)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    category_rel = relationship("Category", back_populates="expenses")