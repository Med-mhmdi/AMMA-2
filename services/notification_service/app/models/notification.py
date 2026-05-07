from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    type = Column(String, nullable=False)   # budget_alert | loan_reminder | bill_reminder | subscription_reminder | ai_insight | system_message
    status = Column(String, nullable=False, default="pending")  # pending | sent | read | dismissed | failed
    related_entity_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)