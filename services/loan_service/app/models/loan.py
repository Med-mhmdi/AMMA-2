from sqlalchemy import Column, Date, DateTime, Integer, Numeric, String
from sqlalchemy.sql import func

from app.database import Base


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    person_name = Column(String, nullable=False)
    person_phone_number = Column(String, nullable=True)

    amount = Column(Numeric(10, 2), nullable=False)

    # unpaid | partially_paid | paid | overdue
    status = Column(String, nullable=False, default="unpaid")

    # borrowed | lent
    type = Column(String, nullable=False)

    date_created = Column(Date, nullable=False)
    date_return = Column(Date, nullable=True)

    # New fields for repayment tracking
    paid_amount = Column(Numeric(10, 2), nullable=False, default=0)
    last_payment_date = Column(Date, nullable=True)

    parent_loan_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )